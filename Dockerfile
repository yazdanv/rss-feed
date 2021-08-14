FROM python:3.8.11-buster

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev


COPY requirements.txt ./
RUN pip install -r ./requirements.txt

COPY ./app /app

EXPOSE 8081

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]