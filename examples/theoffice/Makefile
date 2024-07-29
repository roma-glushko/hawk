SOURCE?=src
TESTS?=tests

.PHONY: help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	@pdm install

dev: ## Run a dev server
	@PYTHONTRACEMALLOC=1 pdm run fastapi dev $(PWD)/src/theoffice/main.py

run: ## Run a dev server
	@PYTHONTRACEMALLOC=1 pdm run fastapi run $(PWD)/src/theoffice/main.py

clean: ## Clean temporary files
	@echo "🧹 Cleaning temporary files.."
	@rm -rf dist
	@rm -rf .mypy_cache .pytest_cache .ruff_cache
	@rm -rf .coverage htmlcov coverage.xml
	@rm -rf .mutmut-cache
	@rm -rf site

lint-check: ## Lint source code without modifying it
	@echo "🧹 Ruff"
	@pdm run ruff check $(SOURCE) $(TESTS)
	@pdm "🧽 MyPy"
	@poetry run mypy --pretty $(SOURCE) $(TESTS)

lint: ## Lint source code
	@echo "🧹 Ruff"
	@pdm run ruff check --fix $(SOURCE) $(TESTS)
	@echo "🧽 MyPy"
	@pdm run mypy --pretty $(SOURCE) $(TESTS)
