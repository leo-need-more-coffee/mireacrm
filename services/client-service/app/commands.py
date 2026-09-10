"""Входные команды предметной области."""

import uuid

from pydantic import BaseModel, Field

from app.models import PreferredChannel


class ClientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    # Телефон — основной идентификатор клиента на ресепшене.
    phone: str = Field(pattern=r"^\+?\d{10,15}$")
    branch_id: uuid.UUID
    email: str = Field(default="", max_length=200)
    telegram: str = Field(default="", max_length=64)
    preferred: PreferredChannel = PreferredChannel.SMS


class LoyaltyAccrual(BaseModel):
    invoice_id: uuid.UUID
    paid_kopecks: int = Field(ge=0)
