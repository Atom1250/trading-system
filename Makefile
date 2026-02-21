.PHONY: build up down dev help open-ui clean

# Default target
help:
	@echo "Trading System Management"
	@echo "========================="
	@echo "Usage:"
	@echo "  make help       - Show this help message"
	@echo "  make dev        - Full setup: Build, launch services, and open UI (localhost:3000)"
	@echo "  make up         - Start services in the background"
	@echo "  make build      - Build or rebuild services"
	@echo "  make down       - Stop and remove containers"
	@echo "  make logs       - View service logs"
	@echo "  make open-ui    - Open the browser to http://localhost:3000"
	@echo "  make clean      - Remove orpaned containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

open-ui:
	@echo "Waiting for services to initialize..."
	@sleep 5
	@open http://localhost:3000

dev: build up open-ui
	@echo "System is running. UI should be open in your browser."

clean:
	docker-compose down --remove-orphans -v
