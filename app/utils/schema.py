from app.core.config import ShowMessageType
from enum import Enum
import time
from typing import Optional
from pydantic import BaseModel


class BaseOrmModel(BaseModel):
    class Config:
        orm_mode = True


class BaseIdModel(BaseOrmModel):
    id: Optional[int] = None
    is_active: Optional[bool] = True
    is_deleted: Optional[bool] = False

    class Config:
        orm_mode = True


class BaseResponse(BaseOrmModel):
    current_time: int = round(time.time())
    message: str = None
    success: bool
    status_code: int = 200
    show_type: Enum = ShowMessageType.NONE


class ErrorResponse(BaseResponse):
    errors: Optional[str] = None
    success: bool = False


class SuccessResponse(BaseResponse):
    index: Optional[int] = None
    total: Optional[int] = None
    data: Optional[BaseModel] = None
    success: bool = True
