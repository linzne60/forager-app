import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import String, cast, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.discoveries import Discovery
from app.models.users import User
from app.schemas.discoveries import DiscoveryListItem, DiscoveryResponse, DiscoveryUpdate

router = APIRouter()


@router.get("", response_model=list[DiscoveryListItem])
async def list_discoveries(
    limit: int = 20,
    cursor: datetime | None = None,
    q: str | None = None,
    safety: str | None = Query(None, description="Comma-separated: safe,caution,danger"),
    confidence_min: float | None = None,
    confidence_max: float | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Discovery)
        .where(Discovery.user_id == user.id)
        .order_by(Discovery.discovered_at.desc())
        .limit(limit)
    )

    # Cursor pagination: get items older than the cursor
    if cursor is not None:
        query = query.where(Discovery.discovered_at < cursor)

    # Text search across species name, location, and notes
    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(
                cast(Discovery.species_prediction["common_name"].astext, String).ilike(pattern),
                cast(Discovery.location["city"].astext, String).ilike(pattern),
                cast(Discovery.location["state"].astext, String).ilike(pattern),
                Discovery.user_notes.ilike(pattern),
            )
        )

    # Safety verdict filter
    if safety:
        verdicts = [v.strip() for v in safety.split(",")]
        query = query.where(Discovery.safety_verdict.in_(verdicts))

    # Confidence range filter
    if confidence_min is not None:
        query = query.where(Discovery.confidence_score >= confidence_min)
    if confidence_max is not None:
        query = query.where(Discovery.confidence_score <= confidence_max)

    # Date range filter
    if date_from is not None:
        query = query.where(Discovery.discovered_at >= date_from)
    if date_to is not None:
        query = query.where(Discovery.discovered_at <= date_to)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{discovery_id}", response_model=DiscoveryResponse)
async def get_discovery(
    discovery_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Discovery).where(Discovery.id == discovery_id)
    )
    discovery = result.scalar_one_or_none()
    if discovery is None:
        raise HTTPException(status_code=404, detail="Discovery not found")
    return discovery


@router.patch("/{discovery_id}", response_model=DiscoveryResponse)
async def update_discovery(
    discovery_id: uuid.UUID,
    body: DiscoveryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Discovery).where(
            Discovery.id == discovery_id,
            Discovery.user_id == user.id,
        )
    )
    discovery = result.scalar_one_or_none()
    if discovery is None:
        raise HTTPException(status_code=404, detail="Discovery not found")

    discovery.user_notes = body.user_notes
    await db.commit()
    await db.refresh(discovery)
    return discovery


@router.delete("/{discovery_id}", status_code=204)
async def delete_discovery(
    discovery_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Discovery).where(
            Discovery.id == discovery_id,
            Discovery.user_id == user.id,
        )
    )
    discovery = result.scalar_one_or_none()
    if discovery is None:
        raise HTTPException(status_code=404, detail="Discovery not found")

    await db.delete(discovery)
    await db.commit()
