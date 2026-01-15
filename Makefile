.PHONY: help install install-python install-js dev clean generate build test

# Default target
help:
	@echo "Fussel - Static Photo Gallery Generator"
	@echo ""
	@echo "Available targets:"
	@echo "  make install        - Install all dependencies (Python + JS)"
	@echo "  make install-python - Install Python dependencies only"
	@echo "  make install-js     - Install JavaScript dependencies only"
	@echo "  make generate       - Generate the gallery site"
	@echo "  make dev            - Run in development mode (watch web app)"
	@echo "  make clean          - Clean build artifacts and dependencies"
	@echo "  make test           - Run tests (if available)"
	@echo ""
	@echo "First time setup:"
	@echo "  1. Copy sample_config.yml to config.yml"
	@echo "  2. Edit config.yml with your settings"
	@echo "  3. Run 'make install'"
	@echo "  4. Run 'make generate'"

# Install all dependencies
install: install-python install-js

# Install Python dependencies
install-python:
	@echo "Setting up Python virtual environment..."
	python3 -m venv .venv || python -m venv .venv
	.venv/bin/pip install --upgrade pip setuptools wheel
	.venv/bin/pip install -e .

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
	.venv/bin/python -m fussel.fussel

# Development mode - run web app in watch mode
dev:
	@if ! command -v yarn >/dev/null 2>&1; then \
		echo "Error: yarn is required but not found. Please install yarn first."; \
		echo "Visit https://yarnpkg.com/getting-started/install for installation instructions."; \
		exit 1; \
	fi
	cd fussel/web && yarn start

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

# Run tests (placeholder for future test suite)
test:
	@echo "Running tests..."
	@echo "Test suite not yet implemented"

