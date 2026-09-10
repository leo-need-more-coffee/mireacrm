"""Входные команды предметной области.

Домен принимает их и от REST, и от gRPC. Представления наружу у каждого
транспорта свои: `api/schemas.py` для HTTP, `rpc/mapping.py` для gRPC.
"""

import uuid

from pydantic import BaseModel, Field


class NormIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    unit: str = Field(min_length=1, max_length=16)
    amount: float = Field(gt=0)


class ServiceCreate(BaseModel):
    branch_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    duration_minutes: int = Field(gt=0, le=8 * 60)
    price_kopecks: int = Field(ge=0)
    norms: list[NormIn] = Field(default_factory=list)


class PriceUpdate(BaseModel):
    price_kopecks: int = Field(ge=0)
