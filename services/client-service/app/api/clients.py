import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import commands, domain
from app.api import schemas
from app.api.deps import get_context, get_publisher, get_session
from app.infra.events import EventPublisher
from app.infra.lifespan import AppContext

router = APIRouter(tags=["clients"])


@router.post("/clients", response_model=schemas.ClientOut, status_code=status.HTTP_201_CREATED)
async def register_client(
    payload: commands.ClientCreate,
    session: AsyncSession = Depends(get_session),
    publisher: EventPublisher = Depends(get_publisher),
):
    return await domain.register_client(session, payload, publisher)


@router.get("/clients", response_model=schemas.ClientOut)
async def find_by_phone(
    phone: str = Query(min_length=10, max_length=20),
    session: AsyncSession = Depends(get_session),
):
    """Поиск по телефону — основной сценарий на ресепшене."""
    return await domain.find_by_phone(session, phone)


@router.get("/clients/{client_id}", response_model=schemas.ClientCardOut)
async def get_client_card(
    client_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    context: AppContext = Depends(get_context),
):
    """Карточка клиента: своё состояние плюс история записей из booking."""
    client = await domain.get_client(session, client_id)
    appointments = await context.clients.appointments(client_id)

    return schemas.ClientCardOut(
        **schemas.ClientOut.model_validate(client).model_dump(),
        appointments=[schemas.appointment_out(item) for item in appointments],
    )


@router.get("/clients/{client_id}/loyalty", response_model=schemas.LoyaltyOut)
async def get_loyalty(client_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    client = await domain.get_client(session, client_id)
    return schemas.LoyaltyOut(
        client_id=client.id,
        points_balance=client.points_balance,
        entries=sorted(client.entries, key=lambda entry: entry.created_at, reverse=True),
    )
