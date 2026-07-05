from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import DateTime, String

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="developer")
    status: Mapped[str] = mapped_column(String(20), default="active")
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color: Mapped[str] = mapped_column(String(20), default="#6366f1")
    initials: Mapped[str] = mapped_column(String(5), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    # Nullable rather than backfilled with a server default: existing rows
    # simply have no preferences yet, and the service layer falls back to
    # DEFAULT_NOTIFICATION_PREFERENCES / DEFAULT_APPEARANCE_PREFERENCES when
    # reading a user whose column is still None.
    notification_preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    appearance_preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)