.PHONY: test run-prod run-dev stop

test:
	docker-compose build komidabot-dev && \
	docker-compose run --rm komidabot-dev python -W default manage.py test

run-prod:
	docker-compose up --build komidabot-prod

run-dev:
	docker-compose up --build komidabot-dev

stop:
	docker-compose stop
