.PHONY: help dev calibrate bench test verify docker-build docker-run docker-stop

.DEFAULT_GOAL := help

help:
	@echo "Sibyl Makefile"
	@echo "Available commands:"
	@echo "  dev            - Run the local development server (uvicorn)"
	@echo "  calibrate      - Train the Platt scaling calibration model"
	@echo "  bench          - Run benchmark evaluation for Brier score"
	@echo "  test           - Run pytest with coverage"
	@echo "  verify         - Run full verification suite for judges (< 30 seconds)"
	@echo "  docker-build   - Build the Docker image"
	@echo "  docker-run     - Run the Docker container on port 8001"
	@echo "  docker-stop    - Stop the Docker container"

dev:
	bash scripts/run_server.sh

calibrate:
	python scripts/calibrate.py

bench:
	python scripts/bench.py

test:
	pytest --cov=sibyl

verify: ## Run full verification suite for judges (< 30 seconds)
	@echo "🔮 Sibyl Verification Suite"
	@echo "═══════════════════════════════════════════════════"
	@echo ""
	@echo "1/2 — Unit Tests"
	pytest --cov=sibyl --tb=short -q
	@echo ""
	@echo "2/2 — Syntax Check (bench.py)"
	python -c "import scripts.bench; print('   ✅ bench.py importable')" 2>/dev/null || python -c "exec(open('scripts/bench.py').read().replace('asyncio.run(main())', ''))" && echo "   ✅ bench.py syntax OK"
	@echo ""
	@echo "═══════════════════════════════════════════════════"
	@echo "✅ All verification checks passed"

docker-build:
	docker build -t sibyl:latest .

docker-run:
	docker run -d --name sibyl-agent -p 8001:8001 --env-file .env sibyl:latest

docker-stop:
	docker stop sibyl-agent || true
	docker rm sibyl-agent || true
