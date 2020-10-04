.PHONY: test

test:
	docker-compose exec komidabot-dev python manage.py test

run-prod:
	docker-compose up --build komidabot-prod

run-dev:
	docker-compose up --build komidabot-dev

stop:
	docker-compose stop
