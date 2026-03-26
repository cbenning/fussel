.PHONY: help install install-python install-js dev clean generate build test serve fmt lint

UV      := uv
PYTHON  := $(UV) run python
PYTEST  := $(UV) run pytest
RUFF    := $(UV) run ruff

# Default target
help:
	@echo "Fussel - Static Photo Gallery Generator"
	@echo ""
	@echo "Available targets:"
	@echo "  make install        - Install all dependencies (Python + JS)"
	@echo "  make install-python - Install Python dependencies only"
	@echo "  make install-js     - Install JavaScript dependencies only"
	@echo "  make generate       - Generate the gallery site"
	@echo "  make serve          - Start HTTP server to preview generated site"
	@echo "  make dev            - Run in development mode (watch web app)"
	@echo "  make test           - Run all tests (Python + JS)"
	@echo "  make fmt            - Format Python source with ruff"
	@echo "  make lint           - Lint Python source with ruff (no changes)"
	@echo "  make clean          - Clean build artifacts and dependencies"
	@echo ""
	@echo "First time setup:"
	@echo "  1. Copy sample_config.yml to config.yml"
	@echo "  2. Edit config.yml with your settings"
	@echo "  3. Run 'make install'"
	@echo "  4. Run 'make generate'"

# Install all dependencies
install: install-python install-js

# Install Python dependencies via uv
install-python:
	@echo "Installing Python dependencies with uv..."
	$(UV) sync --extra dev

# Install JavaScript dependencies
install-js:
	@echo "Installing JavaScript dependencies..."
	@if ! command -v yarn >/dev/null 2>&1; then \
		echo "Error: yarn is required but not found. Please install yarn first."; \
		echo "Visit https://yarnpkg.com/getting-started/install for installation instructions."; \
		exit 1; \
	fi
	cd fussel/web && yarn install

# Generate the gallery site
generate:
	@echo "Generating gallery site..."
	$(PYTHON) -m fussel.fussel

# Development mode - run web app in watch mode
dev:
	@if ! command -v yarn >/dev/null 2>&1; then \
		echo "Error: yarn is required but not found. Please install yarn first."; \
		echo "Visit https://yarnpkg.com/getting-started/install for installation instructions."; \
		exit 1; \
	fi
	cd fussel/web && yarn start

# Run tests
test:
	@echo "Running Python tests..."
	$(PYTEST) tests/ -v --cov=fussel --cov-report=html --cov-report=term
	@echo "Running JS tests..."
	cd fussel/web && yarn test

# Format Python source
fmt:
	@echo "Formatting Python source..."
	$(RUFF) format .
	$(RUFF) check --fix .

# Lint Python source (check only, no changes)
lint:
	@echo "Linting Python source..."
	$(RUFF) format --check .
	$(RUFF) check .

# Serve the generated site
serve:
	@echo "Starting HTTP server..."
	$(PYTHON) serve.py

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf fussel/web/build
	rm -rf fussel/web/node_modules
	rm -rf .venv
	rm -rf fussel/web/.pnp.*
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
