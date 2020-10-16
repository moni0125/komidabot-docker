.PHONY: test run-prod run-dev stop

test:
	docker-compose build komidabot-dev && \
	docker-compose run --rm --entrypoint=./wait-postgres.sh komidabot-dev && \
	docker-compose run --rm --entrypoint=python komidabot-dev -W default manage.py test

run-prod:
	docker-compose up --build komidabot-prod

run-dev:
	docker-compose up --build komidabot-dev

stop:
	docker-compose stop
