from datetime import timedelta

from fastapi import Depends, APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.authnz.models import User
from app.authnz.schemas import (
    UserLogin,
    UserLoginResponse,
    UserProfileResponse,
    UserRegister,
    UserProfile,
)
from app.utils.schema import SuccessResponse
from app.authnz import utils as authnz_utils
from app.utils.exceptions import CustomException
from app.utils.i18n import trans


router = APIRouter()


@router.post("/user/register")
def user_register(user: UserRegister, db: Session = Depends(get_db)) -> SuccessResponse:
    """
    User Register
    """
    db_user = User.get_user_by_username(db, username=user.username)
    if db_user:
        raise CustomException(
            detail=trans("Username already registered"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return SuccessResponse(
        data=UserProfileResponse.from_orm(User.create_user(db, user=user)),
        status_code=status.HTTP_201_CREATED,
    )


# MARK: Login
@router.post("/user/login")
def user_login(user: UserLogin, db: Session = Depends(get_db)) -> SuccessResponse:
    """
    User Login
    """
    user = authnz_utils.authenticate_user(db, user.username, user.password)
    if not user:
        raise CustomException(
            detail=trans("Incorrect username or password"),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = authnz_utils.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return SuccessResponse(
        data=UserLoginResponse(access_token=access_token),
        status_code=status.HTTP_200_OK,
    )


# Login method just used for swagger (for easier login)
# it only functions as debug feature
@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> UserLoginResponse:
    """
    Just used for swagger login
    """
    user = authnz_utils.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise CustomException(
            detail=trans("Incorrect username or password"),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = authnz_utils.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return UserLoginResponse(access_token=access_token)


@router.delete("/user/delete")
async def user_delete(
    db: Session = Depends(get_db),
    current_user: User = Depends(authnz_utils.get_active_user),
) -> SuccessResponse:
    """
    User Delete
    """
    current_user.delete(db)
    return SuccessResponse(
        status_code=status.HTTP_200_OK,
    )


# Mark: Profile
@router.get("/user/profile")
async def user_profile(
    current_user: User = Depends(authnz_utils.get_active_user),
) -> SuccessResponse:
    """
    User Profile
    """
    return SuccessResponse(
        data=UserProfileResponse.from_orm(current_user), status_code=status.HTTP_200_OK
    )


@router.put("/user/profile")
async def user_update_profile(
    user_data: UserProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(authnz_utils.get_active_user),
) -> SuccessResponse:
    """
    User Profile update
    """
    return SuccessResponse(
        data=UserProfileResponse.from_orm(
            current_user.update_user(db=db, user_data=user_data)
        ),
        status_code=status.HTTP_200_OK,
    )
