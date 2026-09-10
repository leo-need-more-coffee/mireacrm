from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.events import EventPublisher
from app.infra.lifespan import AppContext


def get_context(request: Request) -> AppContext:
    return request.app.state.context


async def get_session(context: AppContext = Depends(get_context)) -> AsyncIterator[AsyncSession]:
    async with context.session() as session:
        yield session


def get_publisher(context: AppContext = Depends(get_context)) -> EventPublisher:
    return context.publisher
