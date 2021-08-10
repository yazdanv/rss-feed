from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.utils.i18n import active_translation


def add_middlewares(app):
    @app.middleware("http")
    async def get_accept_language(request: Request, call_next):
        active_translation(request.headers.get("accept-language", None))
        response = await call_next(request)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
