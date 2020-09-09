FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

ENV PAS_PROM_PORT 9101
ENV PAS_LOGGING info
EXPOSE ${PAS_PROM_PORT}

WORKDIR /app

RUN pip install --no-cache-dir pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system

COPY . .

CMD python /app/purple_air_scraper.py
