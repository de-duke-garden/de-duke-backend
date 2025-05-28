# Development Targets
start-dev:
	@echo "Starting development containers"
	docker compose -f compose.dev.yaml up -d

stop-dev:
	@echo "Stopping development containers"
	docker compose -f compose.dev.yaml down

restart-dev:
	@echo "Restarting development containers"
	docker compose -f compose.dev.yaml down && docker compose -f compose.dev.yaml up -d

build-dev:
	@echo "Building development containers"
	docker compose -f compose.dev.yaml up --build -d

logs-dev:
	@echo "Viewing development logs"
	docker compose -f compose.dev.yaml logs -f

exec-dev:
	@echo "Executing shell in development service (replace <service> with your service name)"
	docker compose -f compose.dev.yaml exec <service> sh

ps-dev:
	@echo "Listing running development containers"
	docker compose -f compose.dev.yaml ps

prune-dev:
	@echo "Cleaning up unused development containers, networks, images, and volumes"
	docker system prune -f && docker volume prune -f

collectstatic-dev:
	@echo "Collecting static files on service `backend`"
	docker compose -f compose.dev.yaml exec backend python manage.py collectstatic --noinput

ssl-generate-dev:
	@echo "Generating SSL certificates with Certbot"
	docker compose -f compose.stagging.yaml exec certbot certbot certonly --webroot --webroot-path=/var/lib/letsencrypt -d localhost


# stagging Targets
start-stagging:
	@echo "Starting stagging containers"
	docker compose -f compose.stagging.yaml up -d

stop-stagging:
	@echo "Stopping stagging containers"
	docker compose -f compose.stagging.yaml down

restart-stagging:
	@echo "Restarting stagging containers"
	docker compose -f compose.stagging.yaml down && docker compose -f compose.stagging.yaml up -d

build-stagging:
	@echo "Building stagging containers"
	docker compose -f compose.stagging.yaml up --build -d

logs-stagging:
	@echo "Viewing stagging logs"
	docker compose -f compose.stagging.yaml logs -f

exec-stagging:
	@echo "Executing shell in stagging service (replace <service> with your service name)"
	docker compose -f compose.stagging.yaml exec <service> sh

ps-stagging:
	@echo "Listing running stagging containers"
	docker compose -f compose.stagging.yaml ps

prune-stagging:
	@echo "Cleaning up unused stagging containers, networks, images, and volumes"
	docker system prune -f && docker volume prune -f

collectstatic-stagging:
	@echo "Collecting static files on service `backend`"
	docker compose -f compose.stagging.yaml exec backend python manage.py collectstatic --noinput

ssl-generate-stagging:
	@echo "Generating SSL certificates with Certbot"
	docker compose -f compose.stagging.yaml exec certbot certbot certonly --webroot --webroot-path=/var/lib/letsencrypt -d de-duke.com

# Production Targets
start:
	@echo "Starting production containers"
	docker compose -f compose.yaml up -d

stop:
	@echo "Stopping production containers"
	docker compose -f compose.yaml down

restart:
	@echo "Restarting production containers"
	docker compose -f compose.yaml down && docker compose -f compose.yaml up -d

build:
	@echo "Building production containers"
	docker compose -f compose.yaml up --build -d

logs:
	@echo "Viewing production logs"
	docker compose -f compose.yaml logs -f

exec:
	@echo "Executing shell in production service (replace <service> with your service name)"
	docker compose -f compose.yaml exec <service> sh

ps:
	@echo "Listing running production containers"
	docker compose -f compose.yaml ps

prune:
	@echo "Cleaning up unused production containers, networks, images, and volumes"
	docker system prune -f && docker volume prune -f

collectstatic:
	@echo "Collecting static files on service `backend`"
	docker compose -f compose.yaml exec backend python manage.py collectstatic --noinput


# General Targets
dummy-cert:
	@echo "Generating dummy SSL certificates for local development"
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ./nginx/certs/dummy-key.pem -out ./nginx/certs/dummy-cert.pem -subj "//CN=localhost"