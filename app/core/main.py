from fastapi import APIRouter, FastAPI

from app.core.database import setup_db
from app.utils.exception_handler import add_exception_handlers
from app.utils.middlewares import add_middlewares
import app.authnz.views as authnz
import app.reader.views as reader


api_router = APIRouter()
api_router.include_router(authnz.router, tags=["authnz"])
api_router.include_router(reader.feed_admin_router, tags=["Feed Admin"])
api_router.include_router(reader.feed_user_router, tags=["Feed User"])
api_router.include_router(
    reader.feedentry_admin_router, tags=["FeedEntry Admin"])
api_router.include_router(
    reader.feedentry_user_router, tags=["FeedEntry User"])


app = FastAPI()

add_exception_handlers(app)
add_middlewares(app)

setup_db()

app.include_router(api_router)
