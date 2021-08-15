from sqlalchemy.orm import session
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, status, Request

from app.core.config import settings
from app.core.database import SessionLocal
from app.authnz.schemas import TokenData
from app.authnz.models import User
from app.utils.exceptions import CustomException
from app.utils.i18n import trans


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = CustomException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=trans("Could not validate credentials"),
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    db = SessionLocal()
    user = User.get_user_by_username(db, username=token_data.username)
    db.close()
    if user is None:
        raise credentials_exception
    return user


async def get_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise CustomException(status_code=400, detail="Inactive user")
    if current_user.is_deleted:
        raise CustomException(status_code=400, detail="Deleted user")
    return current_user


async def get_admin_user(current_user: User = Depends(get_active_user)):
    if not current_user.is_staff:
        raise CustomException(
            detail=trans("You dont have permission for this resource"),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return current_user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def authenticate_user(db, username, password):
    user = User.get_user_by_username(db, username=username)
    if not user:
        return False
    if not user.check_password(password):
        return False
    return user


def get_request_domain(request: Request) -> str:
    return request._headers["origin"]
