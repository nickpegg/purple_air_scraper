all: lint test

bootstrap:
	pipenv install -d

lint:
	pipenv run black *py

test:
	pipenv run mypy *py
	pipenv run pytest

build:
	docker build -t nickpegg/purple_air_scraper .

push:
	docker push nickpegg/purple_air_scraper
