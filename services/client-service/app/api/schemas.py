"""Представления домена в HTTP-ответах. Аналог `rpc/mapping.py` для gRPC."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app import clients as booking_clients
from app import models


class AppointmentOut(BaseModel):
    id: uuid.UUID
    branch_id: uuid.UUID
    service_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: str
    price_kopecks: int


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    phone: str
    email: str
    telegram: str
    preferred: models.PreferredChannel
    branch_id: uuid.UUID
    points_balance: int


class ClientCardOut(ClientOut):
    """Карточка клиента: своё состояние плюс история записей из booking."""

    appointments: list[AppointmentOut] = []


class LoyaltyEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: uuid.UUID
    paid_kopecks: int
    points: int
    created_at: datetime


class LoyaltyOut(BaseModel):
    client_id: uuid.UUID
    points_balance: int
    entries: list[LoyaltyEntryOut]


def appointment_out(item: booking_clients.Appointment) -> AppointmentOut:
    return AppointmentOut(
        id=item.id,
        branch_id=item.branch_id,
        service_id=item.service_id,
        starts_at=item.starts_at,
        ends_at=item.ends_at,
        status=item.status,
        price_kopecks=item.price_kopecks,
    )
