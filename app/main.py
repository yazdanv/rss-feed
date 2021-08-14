from app.core.celery_utils import celery_app
from fastapi import FastAPI

from app.core.main import app

app.celery_app = celery_app
celery = app.celery_app
