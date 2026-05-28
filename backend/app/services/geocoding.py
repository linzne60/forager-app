import logging

import httpx

logger = logging.getLogger(__name__)


async def geocode_location(city: str, state: str) -> tuple[float, float] | None:
    """
    Converts a city + state string to (latitude, longitude) using OpenStreetMap Nominatim.
    Returns None if the location cannot be resolved.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"{city}, {state}", "format": "json", "limit": 1},
                headers={"User-Agent": "ForagerApp/1.0"},
            )
            response.raise_for_status()
            results = response.json()

            if not results:
                return None

            return float(results[0]["lat"]), float(results[0]["lon"])

    except Exception as e:
        logger.warning("Geocoding failed for (%s, %s): %s: %s", city, state, type(e).__name__, e)
        return None


async def reverse_geocode(latitude: float, longitude: float) -> tuple[str, str] | None:
    """
    Converts (latitude, longitude) to (city, state) using OpenStreetMap Nominatim.
    Returns None if the location cannot be resolved.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": latitude, "lon": longitude, "format": "json", "zoom": 10},
                headers={"User-Agent": "ForagerApp/1.0"},
            )
            response.raise_for_status()
            result = response.json()

            address = result.get("address", {})
            city = address.get("city") or address.get("town") or address.get("village") or ""
            state = address.get("state", "")

            if city or state:
                return city, state
            return None

    except Exception as e:
        logger.warning("Reverse geocoding failed for (%s, %s): %s: %s", latitude, longitude, type(e).__name__, e)
        return None


async def geocode_zip(zip_code: str) -> tuple[float, float] | None:
    """
    Converts a US zip code to (latitude, longitude) using OpenStreetMap Nominatim.
    Returns None if the zip code cannot be resolved.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "postalcode": zip_code,
                    "country": "US",
                    "format": "json",
                    "limit": 1,
                },
                headers={"User-Agent": "ForagerApp/1.0"},
            )
            response.raise_for_status()
            results = response.json()

            if not results:
                return None

            return float(results[0]["lat"]), float(results[0]["lon"])

    except Exception as e:
        logger.warning("Geocoding failed for zip %s: %s: %s", zip_code, type(e).__name__, e)
        return None
