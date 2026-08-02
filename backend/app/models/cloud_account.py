import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CloudAccount(Base):
    __tablename__ = "cloud_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="aws",
    )
    aws_account_id: Mapped[str] = mapped_column(
        String(12),
        unique=True,
        nullable=False,
    )
    role_arn: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        default=lambda: str(uuid.uuid4()),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_sync_region: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    last_sync_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    resource_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )