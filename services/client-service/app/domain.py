"""Бизнес-операции. Используются и REST-слоем, и gRPC-сервером."""

import uuid

from mirea.events.v1 import events_pb2
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import commands, models
from app.infra.errors import ConflictError, NotFoundError
from app.infra.events import EventPublisher

# Пять процентов от оплаченной суммы, округление вниз до целого балла.
POINTS_RATE = 0.05


def points_for(paid_kopecks: int) -> int:
    return int(paid_kopecks / 100 * POINTS_RATE)


async def register_client(
    session: AsyncSession, data: commands.ClientCreate, publisher: EventPublisher
) -> models.Client:
    exists = await session.scalar(select(models.Client).where(models.Client.phone == data.phone))
    if exists is not None:
        raise ConflictError(f"клиент с телефоном {data.phone} уже заведён")

    client = models.Client(
        full_name=data.full_name,
        phone=data.phone,
        email=data.email,
        telegram=data.telegram,
        preferred=data.preferred,
        branch_id=data.branch_id,
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)

    await publisher.publish(
        "client.registered",
        client_registered=events_pb2.ClientRegistered(
            client_id=str(client.id), branch_id=str(client.branch_id)
        ),
    )
    return client


async def get_client(session: AsyncSession, client_id: uuid.UUID) -> models.Client:
    client = await session.get(models.Client, client_id)
    if client is None:
        raise NotFoundError("client", client_id)
    return client


async def find_by_phone(session: AsyncSession, phone: str) -> models.Client:
    client = await session.scalar(select(models.Client).where(models.Client.phone == phone))
    if client is None:
        raise NotFoundError("client", phone)
    return client


async def accrue_points(
    session: AsyncSession, client_id: uuid.UUID, data: commands.LoyaltyAccrual
) -> tuple[models.Client, int]:
    """Начисляет баллы за оплаченный счёт.

    Идемпотентно по invoice_id: биллинг может повторить вызов при ретрае,
    и повторное начисление вернёт текущий баланс, ничего не изменив.
    """
    client = await get_client(session, client_id)

    duplicate = await session.scalar(
        select(models.LoyaltyEntry).where(models.LoyaltyEntry.invoice_id == data.invoice_id)
    )
    if duplicate is not None:
        return client, 0

    points = points_for(data.paid_kopecks)
    client.entries.append(
        models.LoyaltyEntry(
            invoice_id=data.invoice_id, paid_kopecks=data.paid_kopecks, points=points
        )
    )
    client.points_balance += points

    try:
        await session.commit()
    except IntegrityError:
        # Гонку двух одновременных ретраев разрешает уникальный индекс.
        await session.rollback()
        return await get_client(session, client_id), 0

    await session.refresh(client)
    return client, points
