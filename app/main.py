from app.core.celery_utils import celery_app
from fastapi import FastAPI

from app.core.main import api_router
from app.core.database import setup_db
from app.utils.exception_handler import add_exception_handlers
from app.utils.middlewares import add_middlewares

app = FastAPI()

app.celery_app = celery_app
celery = app.celery_app

add_exception_handlers(app)
add_middlewares(app)

setup_db()

app.include_router(api_router)


# #################################
# ## Startup and Shutdown Events ##
# #################################

# task_object = dict()


# @app.on_event("startup")
# async def startup_event():
#     task_object["my_task"] = asyncio.ensure_future(parse_feeds())
#     print("task scheduled")


# @app.on_event("shutdown")
# async def shutdown_event():
#     if not task_object["my_task"].cancelled():
#         task_object["my_task"].cancel()


# Include the app router
