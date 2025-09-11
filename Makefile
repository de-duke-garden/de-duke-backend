# Development Targets
dev-start:
	@echo "Starting development containers"
	docker compose -f compose.dev.yaml up -d

dev-stop:
	@echo "Stopping development containers"
	docker compose -f compose.dev.yaml down

dev-restart:
	@echo "Restarting development containers"
	docker compose -f compose.dev.yaml down && docker compose -f compose.dev.yaml up -d

dev-build:
	@echo "Building development containers"
	docker compose -f compose.dev.yaml up --build -d

dev-logs:
	@echo "Viewing development logs"
	docker compose -f compose.dev.yaml logs -f

dev-exec-backend:
	@echo "Executing shell in development backend service"
	docker compose -f compose.dev.yaml exec backend sh

dev-exec-db:
	@echo "Executing shell in development db service"
	docker compose -f compose.dev.yaml exec db sh

dev-ps:
	@echo "Listing running development containers"
	docker compose -f compose.dev.yaml ps

dev-prune:
	@echo "Cleaning up unused development containers, networks, images, and volumes"
	docker system prune -f && docker volume prune -f

# Staging Targets
staging-start:
	@echo "Starting staging containers"
	docker compose -f compose.staging.yaml up -d

staging-stop:
	@echo "Stopping staging containers"
	docker compose -f compose.staging.yaml down

staging-restart:
	@echo "Restarting staging containers"
	docker compose -f compose.staging.yaml down && docker compose -f compose.staging.yaml up -d

staging-build:
	@echo "Building staging containers"
	docker compose -f compose.staging.yaml up --build -d

staging-logs:
	@echo "Viewing staging logs"
	docker compose -f compose.staging.yaml logs -f

staging-exec-backend:
	@echo "Executing shell in staging backend service"
	docker compose -f compose.staging.yaml exec backend sh

staging-exec-db:
	@echo "Executing shell in staging db service"
	docker compose -f compose.staging.yaml exec db sh

staging-ps:
	@echo "Listing running staging containers"
	docker compose -f compose.staging.yaml ps

staging-prune:
	@echo "Cleaning up unused staging containers, networks, images, and volumes"
	docker system prune -f && docker volume prune -f

# Production Targets
prod-start:
	@echo "Starting production containers"
	docker compose -f compose.prod.yaml up -d

prod-stop:
	@echo "Stopping production containers"
	docker compose -f compose.prod.yaml down

prod-restart:
	@echo "Restarting production containers"
	docker compose -f compose.prod.yaml down && docker compose -f compose.prod.yaml up -d

prod-build:
	@echo "Building production containers"
	docker compose -f compose.prod.yaml up --build -d

prod-logs:
	@echo "Viewing production logs"
	docker compose -f compose.prod.yaml logs -f

prod-exec-backend:
	@echo "Executing shell in production backend service"
	docker compose -f compose.prod.yaml exec backend sh

prod-exec-db:
	@echo "Executing shell in production db service"
	docker compose -f compose.prod.yaml exec db sh

prod-ps:
	@echo "Listing running production containers"
	docker compose -f compose.prod.yaml ps

prod-prune:
	@echo "Cleaning up unused production containers, networks, images, and volumes"
	docker system prune -f && docker volume prune -f
