import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import auth, meta
from app.infra import tracing
from app.infra.config import Settings, get_settings
from app.infra.errors import (
    ForbiddenError,
    MethodNotAllowedError,
    UnauthenticatedError,
    UnknownRouteError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from app.infra.health import check_readiness
from app.infra.lifespan import AppContext, build_context

log = logging.getLogger("gateway")

_PROXIED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

_HTTP_CODES: dict[type[Exception], int] = {
    UnauthenticatedError: 401,
    ForbiddenError: 403,
    UnknownRouteError: 404,
    MethodNotAllowedError: 405,
    UpstreamUnavailableError: 503,
    UpstreamTimeoutError: 504,
}


def create_app(context: AppContext) -> FastAPI:
    app = FastAPI(title="Mirea CRM Gateway", version="0.1.0")
    app.state.context = context

    app.include_router(auth.router)
    app.include_router(meta.router)

    for exc_type, status_code in _HTTP_CODES.items():
        app.add_exception_handler(exc_type, _make_handler(status_code))

    @app.middleware("http")
    async def trace_context(request: Request, call_next):
        traceparent = tracing.parse(request.headers.get(tracing.HEADER))
        tracing.set_current(traceparent)
        response = await call_next(request)
        response.headers[tracing.HEADER] = traceparent
        return response

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", include_in_schema=False)
    async def readyz() -> JSONResponse:
        report = await check_readiness(context)
        return JSONResponse(
            status_code=200 if report.ready else 503,
            content={"status": "ok" if report.ready else "degraded", "checks": report.checks},
        )

    # Объявлен последним: FastAPI выбирает первый подошедший маршрут, и любой
    # объявленный ниже собственный путь шлюза был бы им перехвачен.
    @app.api_route("/{path:path}", methods=_PROXIED_METHODS, include_in_schema=False)
    async def dispatch(path: str, request: Request):
        route = context.router.resolve(request.method, f"/{path}")
        principal = await context.verifier.verify(request.headers.get("authorization"))
        if not principal.has_any(route.roles):
            raise ForbiddenError(route.roles, principal.roles)

        response = await context.proxy.forward(route.upstream, request, principal)
        log.info(
            "%s /%s -> %s %s",
            request.method, path, route.upstream, response.status_code,
            extra={"user": principal.username, "trace_id": tracing.trace_id()},
        )
        return response

    return app


def _make_handler(status_code: int):
    async def handler(_: Request, exc: Exception) -> JSONResponse:
        headers: dict[str, str] = {}
        if isinstance(exc, UnauthenticatedError):
            headers["WWW-Authenticate"] = "Bearer"
        if isinstance(exc, MethodNotAllowedError):
            headers["Allow"] = ", ".join(exc.allowed)
        return JSONResponse(status_code=status_code, content={"detail": str(exc)}, headers=headers)

    return handler


async def serve(settings: Settings | None = None) -> None:
    import uvicorn

    settings = settings or get_settings()
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(levelname)-8s %(name)s: %(message)s",
    )

    async with build_context(settings) as context:
        server = uvicorn.Server(
            uvicorn.Config(
                create_app(context), host="0.0.0.0", port=settings.http_port, log_level="info"
            )
        )
        log.info("шлюз слушает :%s, realm %s", settings.http_port, settings.oidc_issuer)
        await server.serve()


def run() -> None:
    asyncio.run(serve())
