SOURCE?=src
TESTS?=tests

.PHONY: help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	@uv sync --all-extras

clean: ## Clean temporary files
	@echo "🧹 Cleaning temporary files.."
	@rm -rf dist
	@rm -rf .mypy_cache .pytest_cache .ruff_cache
	@rm -rf .coverage htmlcov coverage.xml
	@rm -rf .mutmut-cache
	@rm -rf site

lint-check: ## Lint source code without modifying it
	@echo "🧹 Ruff"
	@uv run ruff check $(SOURCE) $(TESTS)
	@echo "🧽 MyPy"
	@uv run mypy --pretty $(SOURCE) $(TESTS)

lint: ## Lint source code
	@echo "🧹 Ruff"
	@uv run ruff check --fix $(SOURCE) $(TESTS)
	@echo "🧽 MyPy"
	@uv run mypy --pretty $(SOURCE) $(TESTS)

docs-run: ## Start docs with autoreload
	@uv run mkdocs serve

build-docs: ## Build docs
	@uv run mkdocs build

build: build-docs ## Build the project
	@echo "🏗️ Building the project.."
	@uv build

publish: ## Publish the project
	@echo "🚀 Publishing the project.."
	@uv publish

test: ## Run tests
	@uv run coverage run -m pytest $(TESTS) $(SOURCE) --cov --cov-report=html --cov-report=term --cov-report xml:.coverage.xml

test-cov-html: ## Generate test coverage
	@uv run coverage report --show-missing
	@uv run coverage html

test-cov-xml: ## Run tests
	@uv run coverage run -m pytest $(TESTS) --cov $(SOURCE) --cov-report=xml

test-cov-open: test-cov-html  ## Open test coverage in browser
	@open htmlcov/index.html