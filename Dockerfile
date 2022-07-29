FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

ENV PAS_PROM_PORT 9101
ENV PAS_LOGGING info
EXPOSE ${PAS_PROM_PORT}

WORKDIR /app

RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY . .

CMD python /app/purple_air_scraper.py
