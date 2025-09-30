.PHONY: help install test coverage lint format clean run qa verify ci-verify pre-commit-install trend-analysis sbom build build-docker test-docker verify-docker

# Docker image name
DOCKER_IMAGE := termnet:dev

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make build      - Build Docker development image"
	@echo "  make test       - Run all tests"
	@echo "  make test-docker - Run tests in Docker"
	@echo "  make coverage   - Run tests with coverage report"
	@echo "  make lint       - Run linters (ruff, mypy)"
	@echo "  make format     - Format code with black and isort"
	@echo "  make clean      - Remove build artifacts and cache"
	@echo "  make run        - Run TermNet"
	@echo "  make qa         - Run full QA suite (format, lint, test, coverage)"
	@echo "  make verify     - Run TermNet quality gates"
	@echo "  make verify-docker - Run verify in Docker"
	@echo "  make ci-verify  - Run CI verification with artifacts"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make trend-analysis     - Add metrics to trend history"
	@echo "  make sbom              - Generate Software Bill of Materials"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	playwright install chromium

build: build-docker

build-docker:
	@echo "Building Docker development image..."
	docker build -f Dockerfile.dev -t $(DOCKER_IMAGE) .
	@echo "✅ Docker image built: $(DOCKER_IMAGE)"

test:
	pytest tests/ -v

test-docker:
	@echo "Running tests in Docker..."
	docker run --rm -v $(PWD):/workspace $(DOCKER_IMAGE) pytest tests/ -v

test-unit:
	pytest tests/ -v -m "not integration"

test-integration:
	pytest tests/ -v -m integration

coverage:
	pytest tests/ --cov=termnet --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	ruff check termnet/ tests/ scripts/
	mypy termnet/ --config-file mypy.ini

format:
	black termnet/ tests/
	isort termnet/ tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf .mypy_cache/

run:
	python -m termnet.main

qa: format lint test coverage
	@echo "✅ QA Suite Complete!"

verify:
	@PYTHONPATH=.bmad-core:. VERIFY_MAX_SECONDS=40 VERIFY_ART_DIR=artifacts python3 scripts/verify_quality_gates.py
	@echo "Recording claim receipt..."
	@bash -lc 'test -x scripts/record_claim.sh && ./scripts/record_claim.sh "agentic_rag_e2e_gate" "validator" "artifacts/rag_reason.json,artifacts/rag_processor.json,artifacts/code_analyze.json,artifacts/orchestrator_plan.json,artifacts/verify_summary.json" "OK" || true'

verify-docker:
	@echo "Running verify in Docker..."
	docker run --rm -v $(PWD):/workspace -e PYTHONPATH=.bmad-core:. -e VERIFY_MAX_SECONDS=40 -e VERIFY_ART_DIR=artifacts $(DOCKER_IMAGE) python3 scripts/verify_quality_gates.py

ci-verify:
	@PYTHONPATH=.bmad-core:. VERIFY_MAX_SECONDS=40 VERIFY_ART_DIR=artifacts python3 scripts/verify_quality_gates.py
	@test -f artifacts/verify_summary.json && echo "✅ Artifacts generated" || exit 1
	@echo "CI verification complete"

pre-commit-install:
	pip install pre-commit
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

trend-analysis:
	@echo "Running trend analysis system..."
	@python -m termnet.trend_analysis
	@echo ""
	@echo "Running trend visualizer..."
	@python -m termnet.trend_visualizer
sbom:
	@echo "Generating Software Bill of Materials..."
	@mkdir -p artifacts
	@echo "Generating Python dependency list..."
	@pip freeze > artifacts/requirements-freeze.txt
	@echo "Generating SBOM with syft (if available)..."
	@command -v syft >/dev/null 2>&1 && syft . -o json --file artifacts/sbom.json || echo "syft not found - install with: brew install syft"
	@echo "Generating vulnerability scan with grype (if available)..."
	@command -v grype >/dev/null 2>&1 && grype . -o json --file artifacts/vulnerabilities.json || echo "grype not found - install with: brew install grype"
	@echo "✅ SBOM artifacts saved to artifacts/"
