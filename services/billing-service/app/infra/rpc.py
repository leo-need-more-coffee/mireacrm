"""Каркас gRPC-сервера: перехват ошибок, разбор аргументов, сборка сервера."""

import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from grpc_reflection.v1alpha import reflection
from sqlalchemy.exc import IntegrityError

from app.infra import identity, tracing
from app.infra.errors import (
    ConflictError,
    InvalidArgumentError,
    NotFoundError,
    UnavailableError,
)


class ServerInterceptor(grpc.aio.ServerInterceptor):
    """Подхватывает контекст трассировки и маппит доменные ошибки в коды gRPC."""

    _CODES: ClassVar[dict[type[Exception], grpc.StatusCode]] = {
        NotFoundError: grpc.StatusCode.NOT_FOUND,
        InvalidArgumentError: grpc.StatusCode.INVALID_ARGUMENT,
        ConflictError: grpc.StatusCode.ABORTED,
        UnavailableError: grpc.StatusCode.UNAVAILABLE,
    }

    async def intercept_service(self, continuation, handler_call_details):
        handler = await continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        inner: Callable[..., Awaitable] = handler.unary_unary
        metadata = dict(handler_call_details.invocation_metadata or ())

        async def wrapper(request, context):
            tracing.set_current(tracing.parse(metadata.get(tracing.HEADER)))
            identity.set_current(identity.parse(metadata))
            try:
                return await inner(request, context)
            except IntegrityError:
                await context.abort(grpc.StatusCode.ABORTED, "конфликт при записи в базу")
            except tuple(self._CODES) as exc:
                await context.abort(self._CODES[type(exc)], str(exc))

        return grpc.unary_unary_rpc_method_handler(
            wrapper,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )


@dataclass(frozen=True, slots=True)
class Registration:
    """Как подключить сервисер к серверу и под каким именем показать в рефлексии."""

    register: Callable[[grpc.aio.Server], None]
    full_name: str


def parse_uuid(value: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise InvalidArgumentError(f"{field}: невалидный UUID") from exc


def to_timestamp(value: datetime) -> Timestamp:
    out = Timestamp()
    out.FromDatetime(value)
    return out


async def build_server(port: int, registrations: Sequence[Registration]) -> grpc.aio.Server:
    server = grpc.aio.server(interceptors=[ServerInterceptor()])
    for item in registrations:
        item.register(server)

    # Рефлексия нужна, чтобы grpcurl работал без .proto под рукой.
    reflection.enable_server_reflection(
        (*(item.full_name for item in registrations), reflection.SERVICE_NAME), server
    )
    server.add_insecure_port(f"0.0.0.0:{port}")
    return server
