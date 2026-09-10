import uuid

from fastapi import APIRouter, Depends, status
from mireacrm_common.deps import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from app import commands, domain
from app.api import schemas

router = APIRouter(tags=["catalog"])


@router.post("/services", response_model=schemas.ServiceOut, status_code=status.HTTP_201_CREATED)
async def create_service(
    payload: commands.ServiceCreate, session: AsyncSession = Depends(get_session)
):
    return schemas.service_out(await domain.create_service(session, payload))


@router.get("/services/{service_id}", response_model=schemas.ServiceOut)
async def get_service(service_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    return schemas.service_out(await domain.get_service(session, service_id))


@router.get("/branches/{branch_id}/services", response_model=list[schemas.ServiceOut])
async def list_branch_services(
    branch_id: uuid.UUID,
    only_active: bool = True,
    session: AsyncSession = Depends(get_session),
):
    services = await domain.list_branch_services(session, branch_id, only_active)
    return [schemas.service_out(service) for service in services]


@router.put("/services/{service_id}/price", response_model=schemas.ServiceOut)
async def update_price(
    service_id: uuid.UUID,
    payload: commands.PriceUpdate,
    session: AsyncSession = Depends(get_session),
):
    return schemas.service_out(await domain.update_price(session, service_id, payload))
