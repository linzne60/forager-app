import logging
import secrets
import uuid
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.oauth import PROVIDERS, get_redirect_uri, get_userinfo
from app.auth.passwords import hash_password, verify_password
from app.config import settings
from app.db.session import get_db
from app.models.users import User
from app.rate_limit import limiter
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.services.discovery import claim_discoveries

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("3/minute", key_func=get_remote_address)
async def register(
    request: Request,
    payload: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
    )
    db.add(user)
    await db.flush()

    if payload.session_id:
        claimed = await claim_discoveries(db, payload.session_id, user.id)
        logger.info("Claimed %d discoveries for new user %s", claimed, user.id)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute", key_func=get_remote_address)
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if payload.session_id:
        claimed = await claim_discoveries(db, payload.session_id, user.id)
        logger.info("Claimed %d discoveries for user %s", claimed, user.id)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        token_data = decode_token(refresh_token)
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(status_code=401, detail="Refresh token has expired") from err
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from err

    user_id = token_data.get("sub")
    if not user_id or token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token type")

    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(str(user.id))

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600
    )

    return TokenResponse(
        access_token=new_access_token,
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.display_name is not None:
        current_user.display_name = body.display_name
    if body.default_location is not None:
        current_user.default_location = body.default_location.model_dump()
    if body.dietary_info is not None:
        current_user.dietary_info = body.dietary_info.model_dump()

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)

@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    state = secrets.token_urlsafe(32)

    config = PROVIDERS[provider]
    params = {
        "client_id": config["client_id"],
        "redirect_uri": get_redirect_uri(provider),
        "scope": config["scope"],
        "response_type": "code",
        "state": state
    }
    redirect = RedirectResponse(f"{config['authorize_url']}?{urlencode(params)}")
    redirect.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        path="/",
        max_age=600,
    )
    return redirect

@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str | None = None,
    oauth_state: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not oauth_state or state != oauth_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state. Possible CSRF attack.")
    
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    try:
        userinfo = await get_userinfo(provider, code)
    except Exception as err:
        logger.exception("OAuth userinfo fetch failed for provider %s", provider)
        raise HTTPException(status_code=400, detail="OAuth authentication failed") from err

    oauth_id = userinfo.get("oauth_id")
    email = userinfo.get("email")
    display_name = userinfo.get("display_name", "User")

    if not oauth_id:
        raise HTTPException(status_code=400, detail="OAuth authentication failed")

    result = await db.execute(
        select(User).where(User.oauth_provider == provider, User.oauth_id == oauth_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            oauth_provider=provider,
            oauth_id=oauth_id,
            display_name=display_name,
        )
        db.add(user)
        await db.flush()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    params = urlencode({"token": access_token})
    redirect = RedirectResponse(f"{settings.frontend_url}/auth/callback#{params}")
    redirect.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        path="/",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
    )
    redirect.delete_cookie("oauth_state")
    return redirect

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=not settings.debug,
        samesite="lax"
    )
    return {"detail": "Successfully logged out"}
