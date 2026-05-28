from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlantKnowledge(Base):
    __tablename__ = "plant_knowledge"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    species_class_name: Mapped[str | None] = mapped_column(String, index=True)
    content: Mapped[str] = mapped_column(String)
    embedding: Mapped[list] = mapped_column(Vector(384))       # 384 dims for all-MiniLM-L6-v2
    source: Mapped[str | None] = mapped_column(String)         # e.g. "safety_guide", "lookalike_notes" 

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )