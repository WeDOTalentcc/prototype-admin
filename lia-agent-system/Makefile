# WeDoTalent lia-agent-system — Developer tooling canonical
#
# Registrado 2026-05-20 (Sprint 0 pós-audit E2E).
# Reduz TTHW dos sensors de ~30min pra <5min:
#   - Dev novo: `make help` mostra todos os comandos
#   - Sensors: `make check-all` roda os 2 canonical em sequência
#   - Pré-commit local: `make check-pydantic` (<1s)
#   - Antes de push: `make check-all` (~35s)

.PHONY: help check-pydantic smoke check-all sensors smoke-quick lint

help:	## Lista todos os targets disponíveis
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check-pydantic:	## AST checker R1+R2+R3+R4 conventions (rápido, ~1s)
	@echo "▶ Pydantic Conventions (R1+R2+R3+R4) — CLAUDE.md 2026-05-20"
	python3 scripts/check_pydantic_conventions.py app/

smoke:	## Contract smoke test em 1798 endpoints (~34s, requires uvicorn:8001)
	@echo "▶ Contract smoke test — 1798 endpoints"
	@echo "  (requires uvicorn rodando em localhost:8001)"
	python3 -m pytest tests/contract/test_endpoint_smoke.py --no-header -q --tb=line

smoke-quick:	## Smoke test em subset GETs apenas (~10s, faster iteration)
	python3 -m pytest tests/contract/test_endpoint_smoke.py --no-header -q --tb=line -k "GET"

check-all: check-pydantic smoke	## Roda todos os sensors canonical em sequência (~35s total)
	@echo "✅ All sensors passed"

sensors: check-all	## Alias para check-all

lint:	## Roda ruff + ruff-format check (pre-commit equivalent)
	ruff check app/ scripts/ tests/
	ruff format --check app/ scripts/ tests/

# ─── Quick reference ──────────────────────────────────────────────────────────
# Pre-commit hook (auto-roda em git commit):
#   .pre-commit-config.yaml já tem pydantic-conventions-warn
#
# CI (auto-roda em PR):
#   .github/workflows/pydantic-conventions-sensors.yml roda check-all
#
# Manual local:
#   make check-pydantic   # rápido, < 1s
#   make smoke            # médio, ~34s
#   make check-all        # tudo, ~35s
# ──────────────────────────────────────────────────────────────────────────────
