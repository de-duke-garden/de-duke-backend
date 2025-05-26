# De-Duke Documentation

## Overview
This is the overview for the De-Duke application, built using Django, DRF and more and containerized with Docker.

## Prerequisites
- Docker
- Docker Compose
- Make (optional, for using Makefile commands)

## Project Structure
```
De-Duke/
├── backend/
├── .env_file/
|   └── dev.env
├── .secrets/
|   └── db/
|        └── password.txt
├── compose.<mode>.yml
├── Makefile
└── README.md
```

## Quick Start
1. Clone the repository
2. Copy `.env.example` to `.env` and configure environment variables
3. Build and run the containers:
```bash
make build-dev
make build # production
```

## Available Make Commands
- `make build` - Build Docker containers
- `make up` - Start the services
- `make down` - Stop the services
- `make logs` - View container logs
- `make migrate` - Run database migrations
- `make shell` - Access Django shell

## Development
More details about development setup and processes will be added as the project evolves.

## Additional Services
Additional services and their brief will be included here as they are added to the project.

## Detailed Documentation
Detailed documentation on the services will be in README.md of each services