import uuid
from datetime import datetime
from typing import Annotated

from mireacrm_common.errors import ConflictError
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


UuidPk = Annotated[
    uuid.UUID, mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
]
CreatedAt = Annotated[
    datetime, mapped_column(DateTime(timezone=True), server_default=func.now())
]


class Consumable(Base):
    """Материал: что расходуется при оказании услуги.

    Каталог владеет справочником — что за материал и в чём измеряется.
    Остатками владеет inventory-service.
    """

    __tablename__ = "consumables"
    __table_args__ = (UniqueConstraint("name", name="consumables_name_unique"),)

    id: Mapped[UuidPk]
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[CreatedAt]


class Service(Base):
    """Услуга из прайса филиала."""

    __tablename__ = "services"

    id: Mapped[UuidPk]
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    name: Mapped[str] = mapped_column(String(200))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price_kopecks: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[CreatedAt]

    norms: Mapped[list["ConsumptionNorm"]] = relationship(
        back_populates="service", cascade="all, delete-orphan", lazy="selectin"
    )

    def set_norms(self, norms: list["ConsumptionNorm"]) -> None:
        seen: set[uuid.UUID] = set()
        for norm in norms:
            if norm.consumable_id in seen:
                raise ConflictError("материал указан в нормативе дважды")
            seen.add(norm.consumable_id)
        self.norms = norms


class ConsumptionNorm(Base):
    """Сколько материала уходит на одну процедуру."""

    __tablename__ = "consumption_norms"
    __table_args__ = (
        UniqueConstraint("service_id", "consumable_id", name="consumption_norms_unique"),
    )

    id: Mapped[UuidPk]
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    consumable_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("consumables.id", ondelete="RESTRICT")
    )
    amount: Mapped[float] = mapped_column(Float)

    service: Mapped[Service] = relationship(back_populates="norms")
    consumable: Mapped[Consumable] = relationship(lazy="selectin")
