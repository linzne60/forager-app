import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Discovery(Base):
    __tablename__ = "discoveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # nullable allows for guest user
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)

    # input data
    photo_url: Mapped[str | None] = mapped_column(String)
    location: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    user_notes: Mapped[str | None] = mapped_column(String)

    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # agent and ML data
    species_prediction: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    all_predictions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    heatmap_url: Mapped[str | None] = mapped_column(String)

    enrichment_status: Mapped[str | None] = mapped_column(String(30), default="pending")
    safety_verdict: Mapped[str | None] = mapped_column(String(50), default="caution")  # "safe", "caution", "danger"
    safety_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    nutrition_info: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    weather_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()")
    )