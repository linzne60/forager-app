from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.safety_agent import run_safety_static
from app.agents.weather_agent import run_weather_agent
from app.config import settings
from app.services.classifier import get_classifier
from app.services.nutrition_data import get_nutrition

logger = logging.getLogger(__name__)


@dataclass
class ForageInput:
    image: Image.Image
    photo_url: str
    latitude: float | None
    longitude: float | None
    state_abbr: str | None
    db: AsyncSession


@dataclass
class ForageEvent:
    event: str
    data: dict


async def _run_weather(latitude: float | None, longitude: float | None) -> ForageEvent | None:
    if latitude is None or longitude is None:
        return None

    weather_data = await run_weather_agent(latitude, longitude)
    return ForageEvent(event="weather", data={"weather_context": weather_data})


async def run_orchestrator_stream(input: ForageInput) -> AsyncGenerator[ForageEvent, None]:

    classifier = get_classifier()
    predictions = await asyncio.to_thread(classifier.predict, input.image)

    heatmap_bytes = await asyncio.to_thread(classifier.explain, input.image)

    heatmap_filename = f"{uuid.uuid4()}.jpg"
    heatmap_path = settings.media_dir / "heatmaps" / heatmap_filename
    heatmap_path.write_bytes(heatmap_bytes)
    heatmap_url = f"/media/heatmaps/{heatmap_filename}"

    top = predictions[0]
   
    yield ForageEvent(event="classify", data={
        "predictions": [{"species": p.species, "confidence": p.confidence} for p in predictions],
        "heatmap_url": heatmap_url,
    })

    # safety determins tier
    static_result = run_safety_static(                                                                                                             
        species_class_name=top.species,                                                                                                            
        predictions=predictions,                                                                                                                   
        state_abbr=input.state_abbr,                                                                                                               
    )

    yield ForageEvent(event="safety_static", data={
        "confidence_tier": static_result.confidence_tier,                                    
        "candidates": [                                                                      
            {                                                                                
                "species": c.species,                                                        
                "confidence": c.confidence,                                                  
                "safety_verdict": c.safety_verdict,
                "warning_message": c.warning_message,
            }                                                                                
            for c in static_result.candidates
        ],
        "lookalike_findings": static_result.lookalike_findings,
        "protection_findings": static_result.protection_findings,
        "safety_info": static_result.safety_info,
        "safety_verdict": static_result.safety_verdict,
        "warning_message": static_result.warning_message,
    })

    # nutrition only for strong match
    if static_result.confidence_tier == "strong_match":
        nutrition_data = get_nutrition(top.species)
        yield ForageEvent(event="nutrition", data={"nutrition_info": nutrition_data})

    # weather 
    weather_event = await _run_weather(input.latitude, input.longitude)
    if weather_event:
        yield weather_event

    yield ForageEvent(event="complete", data={})
