# Makefile for Unpuzzle MVP Backend

.PHONY: help setup dev docker-dev test clean lint format

# Default target
help:
	@echo "Available commands:"
	@echo "  setup      - Set up development environment"
	@echo "  dev        - Run development server"
	@echo "  docker-dev - Run with Docker"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  clean      - Clean up"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	./scripts/dev-setup.sh

# Run development server
dev:
	@echo "Starting development server on port 3001..."
	python manage.py runserver 0.0.0.0:3001

# Run with Docker
docker-dev:
	@echo "Starting Docker development environment..."
	./scripts/docker-dev.sh

# Run tests
test:
	@echo "Running tests..."
	python manage.py test

# Run linting (when tools are installed)
lint:
	@echo "Running linting..."
	@if command -v flake8 >/dev/null 2>&1; then flake8 .; else echo "flake8 not installed"; fi

# Format code (when tools are installed)
format:
	@echo "Formatting code..."
	@if command -v black >/dev/null 2>&1; then black .; else echo "black not installed"; fi
	@if command -v isort >/dev/null 2>&1; then isort .; else echo "isort not installed"; fi

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	docker-compose down --volumes --remove-orphans 2>/dev/null || true

# Create migrations
migrate:
	python manage.py makemigrations
	python manage.py migrate

# Create superuser
superuser:
	python manage.py createsuperuser

# Shell
shell:
	python manage.py shell