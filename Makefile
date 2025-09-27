.PHONY: help install test coverage lint format clean run qa verify ci-verify pre-commit-install pre-commit-run trend-analysis sbom

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run all tests"
	@echo "  make coverage   - Run tests with coverage report"
	@echo "  make lint       - Run linters (ruff, mypy)"
	@echo "  make format     - Format code with black and isort"
	@echo "  make clean      - Remove build artifacts and cache"
	@echo "  make run        - Run TermNet"
	@echo "  make qa         - Run full QA suite (format, lint, test, coverage)"
	@echo "  make verify     - Run TermNet quality gates"
	@echo "  make ci-verify  - Run CI verification with artifacts"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run     - Run pre-commit on all files"
	@echo "  make trend-analysis     - Add metrics to trend history"
	@echo "  make sbom              - Generate Software Bill of Materials"
	@echo "  make service       - Run TermNet FastAPI service"
	@echo "  make redis         - Start Redis server"
	@echo "  make test-service  - Test TermNet service endpoints"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	playwright install chromium

test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m "not integration"

test-integration:
	pytest tests/ -v -m integration

coverage:
	pytest tests/ --cov=termnet --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	ruff check termnet/ tests/
	mypy termnet/ --ignore-missing-imports

format:
	black termnet/ tests/ --line-length=88
	isort termnet/ tests/ --profile black --line-length 88
	ruff format termnet/ tests/

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

ci-verify:
	@PYTHONPATH=.bmad-core:. VERIFY_MAX_SECONDS=40 VERIFY_ART_DIR=artifacts python3 scripts/verify_quality_gates.py
	@test -f artifacts/verify_summary.json && echo "✅ Artifacts generated" || exit 1
	@echo "CI verification complete"

pre-commit-install:
	pip install pre-commit
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

pre-commit-run:
	pre-commit run --all-files

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

# TermNet service commands
service-install:
	@echo "Installing TermNet service dependencies..."
	pip install fastapi uvicorn redis sqlalchemy faiss-cpu prometheus-client \
		opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi \
		opentelemetry-exporter-otlp pyyaml

service-run:
	@echo "Starting TermNet service..."
	uvicorn termnet_service:app --reload --host 0.0.0.0 --port 8000

service-test:
	@echo "Testing TermNet service..."
	pytest test_termnet_service.py -v

redis-start:
	@echo "Starting Redis (Docker required)..."
	docker run -d --name termnet-redis -p 6379:6379 redis:latest || docker start termnet-redis

otel-start:
	@echo "Starting OpenTelemetry collector (Docker required)..."
	docker run -d --name otel-collector -p 4317:4317 -p 4318:4318 \
		otel/opentelemetry-collector-contrib:latest || docker start otel-collector

service-deps: redis-start otel-start
	@echo "✅ Service dependencies started"

service-stop:
	@echo "Stopping service dependencies..."
	-docker stop termnet-redis otel-collector
	-docker rm termnet-redis otel-collector
