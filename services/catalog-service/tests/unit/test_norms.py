"""Инвариант нормативов внутри агрегата Service."""

import uuid

import pytest

from app.infra.errors import ConflictError
from app.models import ConsumptionNorm, Service


def norm(consumable_id: uuid.UUID, amount: float) -> ConsumptionNorm:
    return ConsumptionNorm(consumable_id=consumable_id, amount=amount)


def test_norms_assigned():
    service = Service(name="Стрижка", duration_minutes=60, price_kopecks=150000)
    service.set_norms([norm(uuid.uuid4(), 10), norm(uuid.uuid4(), 20)])

    assert len(service.norms) == 2


def test_duplicate_consumable_rejected():
    """Один материал дважды в нормативе — это опечатка, а не двойной расход."""
    service = Service(name="Стрижка", duration_minutes=60, price_kopecks=150000)
    consumable = uuid.uuid4()

    with pytest.raises(ConflictError, match="дважды"):
        service.set_norms([norm(consumable, 10), norm(consumable, 20)])


def test_empty_norms_allowed():
    """Услуга без расхода материалов — консультация, например."""
    service = Service(name="Консультация", duration_minutes=30, price_kopecks=0)
    service.set_norms([])

    assert service.norms == []
