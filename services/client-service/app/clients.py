"""gRPC-клиенты к соседям."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from mirea.booking.v1 import booking_pb2, booking_pb2_grpc
from mirea.common.v1 import common_pb2
from mireacrm_common import grpc_client


@dataclass(frozen=True, slots=True)
class Appointment:
    id: uuid.UUID
    branch_id: uuid.UUID
    service_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: str
    price_kopecks: int


class BookingClient:
    """История записей клиента. Владеет ею booking, мы только спрашиваем."""

    def __init__(self, address: str) -> None:
        self._channel = grpc_client.channel(address)
        self._stub = booking_pb2_grpc.BookingServiceStub(self._channel)

    async def close(self) -> None:
        await self._channel.close()

    async def appointments(self, client_id: uuid.UUID, limit: int = 20) -> list[Appointment]:
        request = booking_pb2.ListClientAppointmentsRequest(
            client_id=str(client_id), page=common_pb2.PageRequest(limit=limit)
        )

        async with grpc_client.call("booking", "client", client_id) as metadata:
            response = await self._stub.ListClientAppointments(request, metadata=metadata)

        return [
            Appointment(
                id=uuid.UUID(item.id),
                branch_id=uuid.UUID(item.branch_id),
                service_id=uuid.UUID(item.service_id),
                starts_at=item.period.start_at.ToDatetime(),
                ends_at=item.period.end_at.ToDatetime(),
                status=booking_pb2.AppointmentStatus.Name(item.status)
                .removeprefix("APPOINTMENT_STATUS_")
                .lower(),
                price_kopecks=item.price.amount_kopecks,
            )
            for item in response.appointments
        ]
