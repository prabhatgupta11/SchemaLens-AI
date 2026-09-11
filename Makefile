.PHONY: setup up down test clean logs

setup:
	@echo "Create .env file if it doesn't exist..."
	@if [ ! -f .env ]; then echo "OPENAI_API_KEY=" > .env; echo "Created .env, please add your OPENAI_API_KEY"; fi

up: setup
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose exec api pytest tests/

clean:
	docker compose down -v
	rm -rf data/*
