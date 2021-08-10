from fastapi import APIRouter

import app.authnz.views as authnz

api_router = APIRouter()
api_router.include_router(authnz.router, tags=["authnz"])
