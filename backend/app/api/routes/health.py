import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    # liveness probe
    return {"status": "ok", "app": settings.app_name}

@router.get("/ready")
async def ready_check():
    # readiness probe
    return {"status": "ready"}

@router.get("/health/db")
async def health_db_check(db: AsyncSession = Depends(get_db)):
    try:
        # select 1 standard ping for sql databases
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "reachable"}
    except Exception as e:
        logger.error(f"Database health check failed:{e}", exc_info=True)
        return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": "database unreachable"}
        )