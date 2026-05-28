import uuid

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_token
from app.db.session import get_db
from app.models.users import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.get(User, uuid.UUID(user_id))

        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(status_code=401, detail="Token has expired") from err

    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=401, detail="Invalid token") from err
    

async def get_optional_user(
    token: str | None = Depends(oauth2_optional),
    db: AsyncSession = Depends(get_db)
):
    
    if token is None:
        return None
    
    return await get_current_user(token=token, db=db)
