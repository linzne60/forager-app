import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import ForageInput, run_orchestrator_stream
from app.api.routes.utilities import load_photo
from app.auth.dependencies import get_optional_user
from app.db.session import get_db
from app.models.users import User
from app.rate_limit import limiter
from app.services.discovery import create_discovery_from_classify, update_discovery_enrichment
from app.services.geocoding import geocode_location, geocode_zip, reverse_geocode

logger = logging.getLogger(__name__)
router = APIRouter()


def _sse_encode(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/forage/stream", tags=["identification"])
@limiter.limit("10/hour")
async def forage_stream(
    request: Request,
    photo: UploadFile = File(...),
    session_id: uuid.UUID | None = Form(None),
    discovered_at: datetime | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    city: str | None = Form(None),
    state: str | None = Form(None),
    zip_code: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    _, image, photo_url = await load_photo(photo)

    # geocodes location
    if latitude is None and longitude is None:
        if city and state:
            coords = await geocode_location(city, state)
            if coords:
                latitude, longitude = coords
        elif zip_code:
            coords = await geocode_zip(zip_code)
            if coords:
                latitude, longitude = coords
    elif latitude is not None and longitude is not None and not city and not state:
        result = await reverse_geocode(latitude, longitude)
        if result:
            city, state = result

    location = None
    if any([latitude, longitude, city, state, zip_code]):
        location = {"latitude": latitude, "longitude": longitude, "city": city, "state": state, "zip_code": zip_code}

    # creates input for stream
    forage_input = ForageInput(
        image=image,
        photo_url=photo_url,
        latitude=latitude,
        longitude=longitude,
        state_abbr=state,
        db=db,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        discovery_id = None

        try:
            async for event in run_orchestrator_stream(forage_input):
                if event.event == "classify":
                    discovery = await create_discovery_from_classify(
                        db,
                        user_id=current_user.id if current_user else None,
                        session_id=session_id,
                        photo_url=photo_url,
                        heatmap_url=event.data.get("heatmap_url", ""),
                        location=location,
                        discovered_at=discovered_at,
                        predictions=event.data.get("predictions", []),
                    )
                    discovery_id = discovery.id
                    yield _sse_encode("classify", {**event.data, "discovery_id": str(discovery_id)})

                elif event.event == "safety_static":
                    safety_details = {
                        "confidence_tier": event.data["confidence_tier"],
                        "candidates": event.data["candidates"], 
                        "safety_info": event.data["safety_info"],
                        "lookalike_findings": event.data["lookalike_findings"],
                        "protection_findings": event.data["protection_findings"],
                    }
                    await update_discovery_enrichment(
                        db, discovery_id,
                        safety_verdict=event.data["safety_verdict"],
                        safety_details={**safety_details, "warning_message": event.data["warning_message"]},
                    )
                    yield _sse_encode("safety_static", event.data)

                elif event.event == "nutrition":
                    if event.data.get("nutrition_info"):
                        await update_discovery_enrichment(db, discovery_id, nutrition_info=event.data["nutrition_info"])
                    yield _sse_encode("nutrition", event.data)

                elif event.event == "weather":
                    if event.data.get("weather_context"):
                        await update_discovery_enrichment(db, discovery_id, weather_context=event.data["weather_context"])
                    yield _sse_encode("weather", event.data)

                elif event.event == "complete":
                    await update_discovery_enrichment(db, discovery_id, enrichment_status="complete")
                    yield _sse_encode("complete", {"discovery_id": str(discovery_id)})

        except Exception as e:
            logger.error("Forage stream error: %s: %s", type(e).__name__, e)
            yield _sse_encode("error", {"message": "An unexpected error occurred."})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
