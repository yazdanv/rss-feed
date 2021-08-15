# RssFeed Backend
A backend server for rss feeds with python, FastAPI
it uses two celery services (worker and beat) for fetching
feeds priodically, and stores them onto the database
using the docker-compose method it would spin up
postgres and redis images and also start all the required
services used by this backend (celery_worker, celery_beat, rssfeed)

## Run Using Docker
    docker-compose up -d

## Test Using pytest
    pytest -v

## Run server manually
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8081
you also need to run the celery worker
    celery -A app.main.celery worker -l info -c 100
and the celery beat
    celery -A app.main.celery beat -l info


## Update Requirements

1.  pip freeze > requirements.txt


## Formatting tools BLACK

Try black project before every commit use it like:

black path-to-dir-or-file for example => black .
