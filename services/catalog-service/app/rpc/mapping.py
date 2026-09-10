"""Перевод доменных моделей в сообщения protobuf."""

from mirea.catalog.v1 import catalog_pb2
from mirea.common.v1 import common_pb2

from app import models


def service(value: models.Service) -> catalog_pb2.Service:
    return catalog_pb2.Service(
        id=str(value.id),
        branch_id=str(value.branch_id),
        name=value.name,
        duration_minutes=value.duration_minutes,
        price=common_pb2.Money(amount_kopecks=value.price_kopecks, currency_code="RUB"),
        is_active=value.is_active,
    )


def norm(value: models.ConsumptionNorm) -> catalog_pb2.ConsumptionNorm:
    return catalog_pb2.ConsumptionNorm(
        consumable_id=str(value.consumable_id),
        name=value.consumable.name,
        unit=value.consumable.unit,
        amount=value.amount,
    )
