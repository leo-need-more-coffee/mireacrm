import enum
import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, func
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


class PreferredChannel(enum.StrEnum):
    SMS = "sms"
    EMAIL = "email"
    TELEGRAM = "telegram"


class Client(Base):
    """Карточка клиента.

    Историей записей владеет booking-service — она запрашивается по gRPC,
    а не дублируется здесь.
    """

    __tablename__ = "clients"

    id: Mapped[UuidPk]
    full_name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(200), default="")
    telegram: Mapped[str] = mapped_column(String(64), default="")
    preferred: Mapped[PreferredChannel] = mapped_column(
        Enum(PreferredChannel, name="preferred_channel"), default=PreferredChannel.SMS
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    points_balance: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[CreatedAt]

    entries: Mapped[list["LoyaltyEntry"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", lazy="selectin"
    )


class LoyaltyEntry(Base):
    """Одно начисление баллов.

    invoice_id уникален: биллинг может повторить вызов при ретрае, но баллы
    начисляются один раз.
    """

    __tablename__ = "loyalty_entries"

    id: Mapped[UuidPk]
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"))
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    paid_kopecks: Mapped[int] = mapped_column(BigInteger)
    points: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[CreatedAt]

    client: Mapped[Client] = relationship(back_populates="entries")
