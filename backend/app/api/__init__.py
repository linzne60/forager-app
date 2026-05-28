from fastapi import APIRouter

from app.api.routes import auth, discoveries, forage_stream, health, locations, weather

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(discoveries.router, prefix="/discoveries", tags=["discoveries"])
api_router.include_router(forage_stream.router, tags=["forage"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])