"""Бизнес-операции. Используются и REST-слоем, и gRPC-сервером."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import commands, models
from app.infra.errors import NotFoundError


async def _resolve_consumable(session: AsyncSession, norm: commands.NormIn) -> models.Consumable:
    """Материалы заводятся по ходу создания услуги.

    Отдельного эндпоинта нет намеренно: администратор филиала мыслит услугой
    («на окрашивание уходит 60 г краски»), а не справочником материалов.
    """
    existing = await session.scalar(
        select(models.Consumable).where(models.Consumable.name == norm.name)
    )
    if existing is not None:
        return existing

    consumable = models.Consumable(name=norm.name, unit=norm.unit)
    session.add(consumable)
    await session.flush()
    return consumable


async def create_service(
    session: AsyncSession, data: commands.ServiceCreate
) -> models.Service:
    service = models.Service(
        branch_id=data.branch_id,
        name=data.name,
        duration_minutes=data.duration_minutes,
        price_kopecks=data.price_kopecks,
    )

    norms = []
    for item in data.norms:
        consumable = await _resolve_consumable(session, item)
        norms.append(models.ConsumptionNorm(consumable_id=consumable.id, amount=item.amount))
    service.set_norms(norms)

    session.add(service)
    await session.commit()
    return await get_service(session, service.id)


async def get_service(
    session: AsyncSession, service_id: uuid.UUID, branch_id: uuid.UUID | None = None
) -> models.Service:
    # populate_existing обязателен: после commit объект остаётся в identity map,
    # и без него вернётся кэшированный экземпляр с незагруженными связями.
    # Обращение к ним вне async-контекста даёт MissingGreenlet.
    query = (
        select(models.Service)
        .where(models.Service.id == service_id)
        .options(
            selectinload(models.Service.norms).selectinload(models.ConsumptionNorm.consumable)
        )
        .execution_options(populate_existing=True)
    )

    service = await session.scalar(query)
    if service is None:
        raise NotFoundError("service", service_id)

    # branch_id в запросе — не фильтр, а проверка: услуга принадлежит своему
    # филиалу, и спрашивать её от имени чужого нельзя.
    if branch_id is not None and service.branch_id != branch_id:
        raise NotFoundError("service", service_id)
    return service


async def list_branch_services(
    session: AsyncSession, branch_id: uuid.UUID, only_active: bool = True
) -> list[models.Service]:
    query = (
        select(models.Service)
        .where(models.Service.branch_id == branch_id)
        .options(
            selectinload(models.Service.norms).selectinload(models.ConsumptionNorm.consumable)
        )
    )
    if only_active:
        query = query.where(models.Service.is_active.is_(True))

    result = await session.scalars(query.order_by(models.Service.name))
    return list(result)


async def update_price(
    session: AsyncSession, service_id: uuid.UUID, data: commands.PriceUpdate
) -> models.Service:
    service = await get_service(session, service_id)
    service.price_kopecks = data.price_kopecks
    await session.commit()
    return await get_service(session, service_id)


async def consumption_norms(
    session: AsyncSession, service_id: uuid.UUID
) -> list[models.ConsumptionNorm]:
    service = await get_service(session, service_id)
    return sorted(service.norms, key=lambda norm: norm.consumable.name)
