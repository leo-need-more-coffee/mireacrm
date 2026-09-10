"""Домен против настоящего Postgres."""

import uuid

import pytest
from mireacrm_common.errors import ConflictError, NotFoundError

from app import commands, domain
from app.models import PreferredChannel

BRANCH = uuid.uuid4()


def client_data(phone: str = "+79001234567", **kwargs) -> commands.ClientCreate:
    payload = {
        "full_name": "Мария Клиентова",
        "phone": phone,
        "branch_id": BRANCH,
        "email": "maria@example.com",
        "preferred": PreferredChannel.TELEGRAM,
        "telegram": "@maria",
    }
    payload.update(kwargs)
    return commands.ClientCreate(**payload)


class TestRegistration:
    async def test_registered_and_event_published(self, session, publisher):
        client = await domain.register_client(session, client_data(), publisher)

        assert client.id is not None
        assert client.points_balance == 0
        assert publisher.routing_keys() == ["client.registered"]

    async def test_duplicate_phone_rejected(self, session, publisher):
        await domain.register_client(session, client_data(), publisher)

        with pytest.raises(ConflictError, match="телефон"):
            await domain.register_client(session, client_data(), publisher)

    async def test_found_by_phone(self, session, publisher):
        created = await domain.register_client(session, client_data(), publisher)

        found = await domain.find_by_phone(session, "+79001234567")

        assert found.id == created.id

    async def test_unknown_phone(self, session, publisher):
        with pytest.raises(NotFoundError):
            await domain.find_by_phone(session, "+70000000000")


class TestLoyalty:
    async def test_points_accrued(self, session, publisher):
        client = await domain.register_client(session, client_data(), publisher)

        accrual = commands.LoyaltyAccrual(invoice_id=uuid.uuid4(), paid_kopecks=520000)

        updated, added = await domain.accrue_points(session, client.id, accrual)

        assert added == 260
        assert updated.points_balance == 260

    async def test_accrual_is_idempotent_by_invoice(self, session, publisher):
        """Биллинг может повторить вызов при ретрае — баллы начисляются раз."""
        client = await domain.register_client(session, client_data(), publisher)
        accrual = commands.LoyaltyAccrual(invoice_id=uuid.uuid4(), paid_kopecks=520000)

        first, added_first = await domain.accrue_points(session, client.id, accrual)
        second, added_second = await domain.accrue_points(session, client.id, accrual)

        assert added_first == 260
        assert added_second == 0
        assert second.points_balance == first.points_balance == 260

    async def test_balance_accumulates_across_invoices(self, session, publisher):
        client = await domain.register_client(session, client_data(), publisher)

        for _ in range(3):
            await domain.accrue_points(
                session,
                client.id,
                commands.LoyaltyAccrual(invoice_id=uuid.uuid4(), paid_kopecks=100_00),
            )

        refreshed = await domain.get_client(session, client.id)
        assert refreshed.points_balance == 15
        assert len(refreshed.entries) == 3

    async def test_unknown_client(self, session, publisher):
        with pytest.raises(NotFoundError):
            await domain.accrue_points(
                session,
                uuid.uuid4(),
                commands.LoyaltyAccrual(invoice_id=uuid.uuid4(), paid_kopecks=100),
            )
