import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_user_oauth", "oauth_provider", "oauth_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # authentication is optional as users may authenticate via OAuth or not at all
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String)
    
    oauth_provider: Mapped[str] = mapped_column(String(50), default="local")  # "local", "google", "github"
    oauth_id: Mapped[str | None] = mapped_column(String(255))  # Google sub or GitHub id for OAuth users
    
    display_name: Mapped[str] = mapped_column(String(100), default="User")
    
    default_location: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    dietary_info: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )
