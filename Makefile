SOURCE?=src
TESTS?=tests

.PHONY: help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	@pdm install

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

build: ## Build the project
	@echo "🏗️ Building the project.."
	@pdm build

publish: ## Publish the project
	@echo "🚀 Publishing the project.."
	@pdm publish

test: ## Run tests
	@pdm run coverage run -m pytest $(TESTS) $(SOURCE)

test-cov-html: ## Generate test coverage
	@pdm run coverage report --show-missing
	@pdm run coverage html

test-cov-xml: ## Run tests
	@pdm run coverage run -m pytest $(TESTS) --cov $(SOURCE) --cov-report=xml

test-cov-open: test-cov-html  ## Open test coverage in browser
	@open htmlcov/index.html