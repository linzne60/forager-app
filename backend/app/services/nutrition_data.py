import json
import logging

from app.config import Settings

logger = logging.getLogger(__name__)

CONFIDENCE_LEVELS = {
    "high": "Data sourced from USDA SR Legacy or Foundation Foods (laboratory verified). USDA FDC ID cited where available.",
    "medium": "Data sourced from published ethnobotanical or foraging literature (e.g. Thayer, Kallas, peer-reviewed studies).",
    "low": "Limited data available. Values are general estimates and should not be relied upon for precision.",
}

_nutrition: dict[str, dict] = {}


def load_nutrition_data(settings: Settings) -> None:
    global _nutrition

    with open(settings.nutrition_data_path) as f:
        entries = json.load(f)
    _nutrition = {entry["species"]: entry for entry in entries}

    logger.info("Nutrition data loaded: %d entries", len(_nutrition))


def get_nutrition(species_class_name: str) -> dict | None:
    return _nutrition.get(species_class_name)
