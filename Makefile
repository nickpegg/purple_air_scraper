all: lint test

develop:
	pip install --upgrade poetry
	poetry install

lint:
	poetry run black *py

test:
	poetry run mypy *py
	poetry run pytest

build:
	docker build -t nickpegg/purple_air_scraper .

push:
	docker push nickpegg/purple_air_scraper
