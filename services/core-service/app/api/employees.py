import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import commands, domain
from app.api import schemas
from app.api.deps import get_publisher, get_session
from app.infra.events import EventPublisher
from app.models import EmployeeRole

router = APIRouter(tags=["employees"])


@router.post(
    "/branches/{branch_id}/employees",
    response_model=schemas.EmployeeOut,
    status_code=status.HTTP_201_CREATED,
)
async def hire_employee(
    branch_id: uuid.UUID,
    payload: commands.EmployeeCreate,
    session: AsyncSession = Depends(get_session),
    publisher: EventPublisher = Depends(get_publisher),
):
    return await domain.hire_employee(session, branch_id, payload, publisher)


@router.get("/branches/{branch_id}/employees", response_model=list[schemas.EmployeeOut])
async def list_employees(
    branch_id: uuid.UUID,
    role: EmployeeRole | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    employees, _ = await domain.list_employees(session, branch_id, role, limit)
    return employees


@router.get("/employees/{employee_id}/schedule", response_model=schemas.ScheduleOut)
async def get_schedule(
    employee_id: uuid.UUID,
    start_at: datetime = Query(alias="from"),
    end_at: datetime = Query(alias="to"),
    session: AsyncSession = Depends(get_session),
):
    employee, shifts = await domain.get_schedule(session, employee_id, start_at, end_at)
    return schemas.ScheduleOut(employee=employee, shifts=shifts)
