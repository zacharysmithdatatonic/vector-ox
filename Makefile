.PHONY: setup install dev test lint format clean help

# Default board size for setup
BOARD_SIZE ?= 3

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup the project with specified board size (default: 3)
	@echo "Setting up vector-ox project with board size $(BOARD_SIZE)..."
	poetry install
	poetry run python -m vector_ox.setup --board-size $(BOARD_SIZE)

install: ## Install dependencies
	poetry install

dev: ## Install development dependencies
	poetry install --with dev

test: ## Run tests
	poetry run pytest

lint: ## Run linting
	poetry run flake8 vector_ox/
	poetry run black --check vector_ox/
	poetry run isort --check-only vector_ox/

format: ## Format code
	poetry run black vector_ox/
	poetry run isort vector_ox/

clean: ## Clean up generated files
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf vector_ox/__pycache__/
	rm -rf vector_ox/*/__pycache__/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

play-random: ## Play the game with random bot
	poetry run python -m vector_ox.game --board-size 3 --bot-type random

play-algorithm: ## Play the game with algorithm bot
	poetry run python -m vector_ox.game --board-size 3 --bot-type algorithm

play-vector: ## Play the game with vector bot
	poetry run python -m vector_ox.game --board-size 3 --bot-type vector


generate-data: ## Generate training data for vector database
	poetry run python -m vector_ox.data_generator

build-vectors: ## Build vector database from generated data
	poetry run python -m vector_ox.vector_builder

play-test: ## Run bot tournament and display performance charts
	poetry run python -m vector_ox.bot_tester --games-per-matchup 50

play-test-extensive: ## Run extensive bot tournament (200 games per matchup)
	poetry run python -m vector_ox.bot_tester --games-per-matchup 200

play-test-save: ## Run bot tournament and save results to file
	poetry run python -m vector_ox.bot_tester --games-per-matchup 100 --output-file bot_results.json 