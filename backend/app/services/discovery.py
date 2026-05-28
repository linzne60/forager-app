import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discoveries import Discovery


async def create_discovery_from_classify(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    session_id: uuid.UUID | None,
    photo_url: str,
    heatmap_url: str,
    location: dict[str, Any] | None,
    discovered_at: datetime | None,
    predictions: list[dict],
) -> Discovery:

    top = predictions[0]
    species_prediction = {"common_name": top["species"], "confidence": top["confidence"]}
    confidence_score = top["confidence"]
    all_predictions = [{"common_name": p["species"], "confidence": p["confidence"]} for p in predictions]


    discovery = Discovery(
        user_id=user_id,
        session_id=session_id,
        photo_url=photo_url,
        heatmap_url=heatmap_url,
        location=location,
        discovered_at=discovered_at,
        species_prediction=species_prediction,
        confidence_score=confidence_score,
        all_predictions=all_predictions,
        safety_verdict="pending",
        safety_details={},
        nutrition_info=None,
        weather_context=None,
    )

    db.add(discovery)
    await db.commit()
    await db.refresh(discovery)

    return discovery


async def update_discovery_enrichment(
    db: AsyncSession,
    discovery_id: uuid.UUID,
    **fields: Any,
) -> None:

    await db.execute(
        update(Discovery)
        .where(Discovery.id == discovery_id)
        .values(**fields)
    )
    await db.commit()


async def claim_discoveries(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID
) -> int:
    """
    Links anonymous discoveries to a newly registered user.
    Returns the number of rows updated.
    """
    query = (
        update(Discovery)
        .where(Discovery.session_id == session_id)
        .where(Discovery.user_id.is_(None))  # only claim 'orphan' records
        .values(user_id=user_id)
    )

    result = await db.execute(query)

    return result.rowcount