from app.utils.schema import BaseOrmModel
from typing import Optional
from pydantic import BaseModel, AnyHttpUrl


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    name: Optional[str] = None
    profile_picture: Optional[AnyHttpUrl] = None


class UserProfileResponse(UserProfile):
    id: int
    username: str

    class Config:
        orm_mode = True


class UserPublicProfile(BaseOrmModel):
    name: Optional[str] = None
    profile_picture: Optional[AnyHttpUrl] = None
