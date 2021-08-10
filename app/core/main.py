from fastapi import APIRouter

import app.authnz.views as authnz
import app.reader.views as reader


api_router = APIRouter()
api_router.include_router(authnz.router, tags=["authnz"])
api_router.include_router(reader.feed_admin_router, tags=["Feed Admin"])
api_router.include_router(reader.feed_user_router, tags=["Feed User"])
