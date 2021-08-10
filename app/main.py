from fastapi import FastAPI

from app.core.main import api_router
from app.core.database import setup_db
from app.utils.exception_handler import add_exception_handlers
from app.utils.middlewares import add_middlewares

app = FastAPI()
add_exception_handlers(app)
add_middlewares(app)

setup_db()

app.include_router(api_router)
