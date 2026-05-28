import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import api_router
from app.config import settings
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.rate_limit import limiter
from app.services.classifier import load_classifier
from app.services.nutrition_data import load_nutrition_data
from app.services.safety_data import load_safety_data

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s...", settings.app_name)

    load_classifier(settings)
    load_safety_data(settings)
    load_nutrition_data(settings)
    
    yield
    logger.info("Shutting down %s...", settings.app_name)

app = FastAPI(
    title=settings.app_name,
    description="Ecological Foraging Intelligence Agent",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    openapi_tags=[
        {"name": "health", "description": "System health and readiness endpoints"},                                                                          
        {"name": "auth", "description": "Authentication and user management"},                                                                               
        {"name": "discoveries", "description": "Plant discovery journal"},
        {"name": "identification", "description": "Plant classification & safety agents"},
    ]
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router)

settings.media_dir.mkdir(parents=True, exist_ok=True)

(settings.media_dir / "uploads").mkdir(exist_ok=True)
(settings.media_dir / "heatmaps").mkdir(exist_ok=True)

app.mount("/media", StaticFiles(directory=str(settings.media_dir)), name="media")

@app.get("/")
async def read_root():
    return {"message": "welcome to forager!"}
