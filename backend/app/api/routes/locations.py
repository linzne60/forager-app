import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.locations import SavedLocation
from app.models.users import User
from app.schemas.locations import LocationCreate, LocationResponse
from app.services.geocoding import geocode_location, geocode_zip

router = APIRouter()


@router.get("", response_model=list[LocationResponse])
async def list_locations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedLocation)
        .where(SavedLocation.user_id == user.id)
        .order_by(SavedLocation.is_pinned.desc(), SavedLocation.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=LocationResponse, status_code=201)
async def create_location(
    body: LocationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    latitude = body.latitude
    longitude = body.longitude

    # Geocode if coordinates not provided
    if latitude is None and longitude is None:
        coords = None
        if body.zip_code:
            coords = await geocode_zip(body.zip_code)
        elif body.city and body.state:
            coords = await geocode_location(body.city, body.state)

        if coords:
            latitude, longitude = coords

    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=422,
            detail="Could not determine coordinates. Provide GPS location, city/state, or zip code.",
        )

    location = SavedLocation(
        user_id=user.id,
        label=body.label,
        city=body.city,
        state=body.state,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location


@router.patch("/{location_id}/pin", response_model=LocationResponse)
async def pin_location(
    location_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch the target location
    result = await db.execute(
        select(SavedLocation).where(
            SavedLocation.id == location_id,
            SavedLocation.user_id == user.id,
        )
    )
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    # Unpin all other locations for this user
    all_result = await db.execute(
        select(SavedLocation).where(
            SavedLocation.user_id == user.id,
            SavedLocation.is_pinned.is_(True),
        )
    )
    for loc in all_result.scalars().all():
        loc.is_pinned = False

    # Pin the target
    location.is_pinned = True
    await db.commit()
    await db.refresh(location)
    return location


@router.delete("/{location_id}", status_code=204)
async def delete_location(
    location_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedLocation).where(
            SavedLocation.id == location_id,
            SavedLocation.user_id == user.id,
        )
    )
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    await db.delete(location)
    await db.commit()
