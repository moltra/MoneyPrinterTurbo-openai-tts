.PHONY: help install install-dev format lint test clean

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

format:  ## Format code with black and isort
	@echo "Formatting code..."
	black app/ webui/ tests/
	isort app/ webui/ tests/
	@echo "✓ Code formatted!"

lint:  ## Lint code with ruff
	@echo "Linting code..."
	ruff check app/ webui/ tests/
	@echo "✓ Linting complete!"

lint-fix:  ## Lint and auto-fix issues
	@echo "Linting and fixing..."
	ruff check --fix app/ webui/ tests/
	@echo "✓ Auto-fixes applied!"

format-check:  ## Check if code is formatted
	@echo "Checking formatting..."
	black --check app/ webui/ tests/
	isort --check-only app/ webui/ tests/

test:  ## Run tests
	@echo "Running tests..."
	pytest tests/ -v

test-cov:  ## Run tests with coverage
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=app --cov=webui --cov-report=html --cov-report=term

clean:  ## Clean up cache and build files
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "✓ Cleaned!"

all: format lint test  ## Format, lint, and test
	@echo "✓ All checks passed!"
