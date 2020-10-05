.PHONY: test run-prod run-dev stop

test:
	docker-compose build komidabot-test && \
	docker-compose run komidabot-test

run-prod:
	docker-compose up --build komidabot-prod

run-dev:
	docker-compose up --build komidabot-dev

stop:
	docker-compose stop
