.PHONY: help install lint test run clean docker-build docker-run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

lint: ## Run linting tools
	black src/ tests/ --check
	flake8 src/ tests/
	mypy src/

test: ## Run tests
	pytest tests/ -v

run: ## Run the full pipeline
	python main.py

clean: ## Clean generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf data/interim/*
	rm -rf data/processed/*

docker-build: ## Build Docker image
	docker build -t dili-risk-score .

docker-run: ## Run pipeline in Docker
	docker run --rm -v $(PWD)/data:/app/data dili-risk-score 