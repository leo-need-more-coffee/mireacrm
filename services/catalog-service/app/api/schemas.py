"""Представления домена в HTTP-ответах. Аналог `rpc/mapping.py` для gRPC."""

import uuid

from pydantic import BaseModel, ConfigDict

from app import models


class NormOut(BaseModel):
    consumable_id: uuid.UUID
    name: str
    unit: str
    amount: float


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    branch_id: uuid.UUID
    name: str
    duration_minutes: int
    price_kopecks: int
    is_active: bool
    norms: list[NormOut] = []


def service_out(service: models.Service) -> ServiceOut:
    return ServiceOut(
        id=service.id,
        branch_id=service.branch_id,
        name=service.name,
        duration_minutes=service.duration_minutes,
        price_kopecks=service.price_kopecks,
        is_active=service.is_active,
        norms=[
            NormOut(
                consumable_id=norm.consumable_id,
                name=norm.consumable.name,
                unit=norm.consumable.unit,
                amount=norm.amount,
            )
            for norm in sorted(service.norms, key=lambda n: n.consumable.name)
        ],
    )
