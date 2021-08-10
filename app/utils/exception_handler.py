from fastapi import status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as starHTTPException

from app.utils.schema import ErrorResponse
from app.utils.exceptions import CustomException
from app.utils.i18n import trans


def add_exception_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        content = ErrorResponse(
            message=trans("Validation error"),
            errors=str(exc),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
        return JSONResponse(status_code=content.status_code, content=content.dict())

    @app.exception_handler(CustomException)
    async def custom_exception_handler(request, exc):
        content = ErrorResponse(
            message=exc.detail, errors=exc.errors, status_code=exc.status_code
        )
        return JSONResponse(status_code=content.status_code, content=content.dict())

    @app.exception_handler(HTTPException)
    async def custom_exception_handler(request, exc):
        content = ErrorResponse(message=exc.detail, status_code=exc.status_code)
        return JSONResponse(status_code=content.status_code, content=content.dict())

    @app.exception_handler(starHTTPException)
    async def custom_exception_handler(request, exc):
        content = ErrorResponse(message=exc.detail, status_code=exc.status_code)
        return JSONResponse(status_code=content.status_code, content=content.dict())
