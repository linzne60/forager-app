import json
import logging

from app.config import Settings

logger = logging.getLogger(__name__)

_lookalikes: dict[str, dict] = {}
_protected: dict[str, dict] = {}


def load_safety_data(settings: Settings) -> None:
    global _lookalikes, _protected

    with open(settings.safety_lookalikes_path) as f:
        entries = json.load(f)
    _lookalikes = {entry["species"]: entry for entry in entries}

    with open(settings.safety_protected_path) as f:
        entries = json.load(f)
    _protected = {entry["species"]: entry for entry in entries}

    logger.info("Safety data loaded: %d lookalike entries, %d protected species entries", len(_lookalikes), len(_protected))


def get_lookalike(species: str) -> dict | None:
    return _lookalikes.get(species)


def get_protection(species: str) -> dict | None:
    return _protected.get(species)
