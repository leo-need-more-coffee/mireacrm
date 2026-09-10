"""Домен против настоящего Postgres."""

import uuid

import pytest

from app import commands, domain
from app.infra.errors import NotFoundError

BRANCH = uuid.uuid4()


def service_data(name: str = "Окрашивание", **kwargs) -> commands.ServiceCreate:
    payload = {
        "branch_id": BRANCH,
        "name": name,
        "duration_minutes": 90,
        "price_kopecks": 450000,
        "norms": [
            commands.NormIn(name="Краска 6.0", unit="г", amount=60),
            commands.NormIn(name="Окислитель 6%", unit="мл", amount=90),
        ],
    }
    payload.update(kwargs)
    return commands.ServiceCreate(**payload)


class TestCreate:
    async def test_service_with_norms(self, session):
        service = await domain.create_service(session, service_data())

        assert service.id is not None
        assert len(service.norms) == 2
        assert {norm.consumable.name for norm in service.norms} == {"Краска 6.0", "Окислитель 6%"}

    async def test_consumables_are_reused_across_services(self, session):
        """Материал с тем же названием не заводится второй раз."""
        first = await domain.create_service(session, service_data("Окрашивание"))
        second = await domain.create_service(session, service_data("Тонирование"))

        first_ids = {norm.consumable_id for norm in first.norms}
        second_ids = {norm.consumable_id for norm in second.norms}
        assert first_ids == second_ids

    async def test_service_without_norms(self, session):
        service = await domain.create_service(session, service_data("Консультация", norms=[]))

        assert service.norms == []


class TestRead:
    async def test_unknown_service(self, session):
        with pytest.raises(NotFoundError):
            await domain.get_service(session, uuid.uuid4())

    async def test_foreign_branch_hidden(self, session):
        """Услугу нельзя запросить от имени чужого филиала."""
        service = await domain.create_service(session, service_data())

        with pytest.raises(NotFoundError):
            await domain.get_service(session, service.id, branch_id=uuid.uuid4())

    async def test_branch_price_list(self, session):
        await domain.create_service(session, service_data("Стрижка"))
        await domain.create_service(session, service_data("Окрашивание"))

        services = await domain.list_branch_services(session, BRANCH)

        assert [s.name for s in services] == ["Окрашивание", "Стрижка"]

    async def test_other_branch_sees_nothing(self, session):
        await domain.create_service(session, service_data())

        assert await domain.list_branch_services(session, uuid.uuid4()) == []

    async def test_norms_sorted_by_name(self, session):
        service = await domain.create_service(session, service_data())

        norms = await domain.consumption_norms(session, service.id)

        assert [norm.consumable.name for norm in norms] == ["Краска 6.0", "Окислитель 6%"]


class TestPrice:
    async def test_updated(self, session):
        service = await domain.create_service(session, service_data())

        updated = await domain.update_price(
            session, service.id, commands.PriceUpdate(price_kopecks=520000)
        )

        assert updated.price_kopecks == 520000
        assert len(updated.norms) == 2

    async def test_unknown_service(self, session):
        with pytest.raises(NotFoundError):
            await domain.update_price(
                session, uuid.uuid4(), commands.PriceUpdate(price_kopecks=1)
            )
