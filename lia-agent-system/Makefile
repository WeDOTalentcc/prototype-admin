# WeDoTalent lia-agent-system — Developer tooling canonical
#
# Registrado 2026-05-20 (Sprint 0 pós-audit E2E).
# Reduz TTHW dos sensors de ~30min pra <5min:
#   - Dev novo: `make help` mostra todos os comandos
#   - Sensors: `make check-all` roda os 2 canonical em sequência
#   - Pré-commit local: `make check-pydantic` (<1s)
#   - Antes de push: `make check-all` (~35s)

.PHONY: help check-pydantic smoke check-all sensors smoke-quick lint check-imports check-benefit-taxonomy

help:   ## Lista todos os targets disponíveis
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check-pydantic: ## AST checker R1+R2+R3+R4 conventions (rápido, ~1s)
	@echo "▶ Pydantic Conventions (R1+R2+R3+R4) — CLAUDE.md 2026-05-20"
	python3 scripts/check_pydantic_conventions.py app/

smoke:  ## Contract smoke test em 1798 endpoints (~34s, requires uvicorn:8001)
	@echo "▶ Contract smoke test — 1798 endpoints"
	@echo "  (requires uvicorn rodando em localhost:8001)"
	python3 -m pytest tests/contract/test_endpoint_smoke.py --no-header -q --tb=line

smoke-quick:    ## Smoke test em subset GETs apenas (~10s, faster iteration)
	python3 -m pytest tests/contract/test_endpoint_smoke.py --no-header -q --tb=line -k "GET"

check-all: check-pydantic check-imports check-benefit-taxonomy check-domain-conformance smoke   ## Roda todos os sensors canonical em sequência (~35s total)
	@echo "✅ All sensors passed"

sensors: check-all      ## Alias para check-all

lint:   ## Roda ruff + ruff-format check (pre-commit equivalent)
	ruff check app/ scripts/ tests/
	ruff format --check app/ scripts/ tests/


check-imports:  ## Sensor canonical import paths (no libs.models.lia_models drift)
	@echo "▶ Canonical Import Paths sensor — auditoria 2026-05-24"
	python3 scripts/check_canonical_import_paths.py --blocking

check-benefit-taxonomy: ## AST sensor taxonomia canonical benefícios (baseline 0 — 2026-05-24)
	@echo "▶ Benefit Taxonomy drift sensor — BLOCKING (baseline=0)"
	python3 scripts/check_no_duplicate_benefit_taxonomy.py --blocking

check-domain-conformance:       ## Domain structure conformance (BLOCKING, ~2s)
	@echo "▶ Domain structure conformance — canonical directory layout"
	python3 -m pytest tests/contract/test_domain_structure_conformance.py -v --tb=short --no-header --no-cov

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

# ─── LIA Field Toggles sensors (audit 2026-05-21) ─────────────────────────────

check-lia-sync: ## Schema-sync TS↔Python — 34 canonical fields (~50ms)
	@echo "▶ LIA field definitions sync TS↔Python (P2-10)"
	python3 scripts/check_lia_field_definitions_sync.py

check-lia-agents:       ## Agentes respeitam lia_field_toggles (anti-regressão P0-1, ~200ms)
	@echo "▶ Agent respeita helper canonical (P0-1 anti-regressão)"
	python3 scripts/check_agent_respects_lia_toggles.py

check-policy-gates:     ## Contract tests dos 4 policy gates (24 testes, ~6s)
	@echo "▶ Policy gates contract tests (P0-2 + P1-4 + P1-7 + P1-8 + P1-9)"
	python3 -m pytest \
		tests/contract/test_offer_approval_gate.py \
		tests/contract/test_wsi_effectiveness_gate.py \
		tests/contract/test_self_scheduling_gate.py \
		tests/contract/test_lia_field_config_service_canonical.py \
		--no-header --no-cov -q

check-lia: check-lia-sync check-lia-agents check-policy-gates   ## Roda os 3 lia-toggles sensors em sequência (~7s)
	@echo "✅ All lia field toggles sensors passed"

# ─── Cross-Tenant hardening sensors (HARDENING_PLAN.md B.1 + B.2, 2026-05-21) ──

check-tenant-filter:    ## B.1: ORM select/update/delete tem .where(.company_id) (warn-only)
	@echo "▶ B.1 tenant-filter coverage — HARDENING_PLAN 2026-05-21"
	python3 scripts/check_query_has_tenant_filter.py --quiet

check-client-id-bypass: ## B.2: sentinela "platform" bypass em app/api (BLOCKING)
	@echo "▶ B.2 client_id sentinel bypass — HARDENING_PLAN 2026-05-21"
	python3 scripts/check_no_client_id_query_bypass.py

check-cross-tenant: check-tenant-filter check-client-id-bypass  ## Roda B.1 + B.2 em sequência (~10s)
	@echo "✅ Cross-tenant hardening sensors completed"

# ─── Recovery sensors (Audit 2026-05-23 — merge incident 02361f41c) ──────────
# Sensores BLOCKING criados durante recovery dos 10 arquivos Tipo A afetados
# pelo merge commit 02361f41c (1/mai/2026, 994 files, -34328 LOC silenciosas).
# Cada sensor bloqueia regressão futura do trabalho recuperado em Recovery
# #1 a #10. Detalhes: ~/Documents/Python/AUDIT_DEEP_2026-05-23.md.

check-recoveries:       ## Recovery sensors (Audit 2026-05-23) — 40+ tests BLOCKING (~120s)
	@echo "▶ Recovery sensors (merge incident 02361f41c anti-regression)"
	python3 -m pytest \
		tests/contract/test_lia_feedback_contract.py \
		tests/contract/test_no_collection_errors.py \
		tests/contract/test_wsi_audit_trail_contract.py \
		tests/contract/test_analytics_actions_contract.py \
		tests/contract/test_job_actions_contract.py \
		tests/contract/test_candidate_actions_migration.py \
		tests/contract/test_teams_bridge_contract.py \
		tests/contract/test_interview_graph_fairness_contract.py \
		tests/contract/test_rails_client_canonical_home.py \
		tests/contract/test_wedotalent_rails_client_contract.py \
		tests/contract/test_policy_migration.py \
		tests/api/test_lia_feedback_hardening.py \
		--no-header --no-cov -q --tb=short

check-recoveries-fast:  ## Recovery sensors EXCETO no_collection (que demora ~90s, ~10s sem ele)
	@echo "▶ Recovery sensors fast (skip no_collection_errors)"
	python3 -m pytest \
		tests/contract/test_lia_feedback_contract.py \
		tests/contract/test_wsi_audit_trail_contract.py \
		tests/contract/test_analytics_actions_contract.py \
		tests/contract/test_job_actions_contract.py \
		tests/contract/test_candidate_actions_migration.py \
		tests/contract/test_teams_bridge_contract.py \
		tests/contract/test_interview_graph_fairness_contract.py \
		tests/contract/test_rails_client_canonical_home.py \
		tests/contract/test_wedotalent_rails_client_contract.py \
		tests/contract/test_policy_migration.py \
		tests/api/test_lia_feedback_hardening.py \
		--no-header --no-cov -q --tb=short

check-lia-toggles: ## P2-5: Verify all lia_field_toggles have real consumers
	python3 scripts/check_lia_field_toggle_consumers.py

check-lia-toggles-blocking:
	python3 scripts/check_lia_field_toggle_consumers.py --blocking

# ─── Architecture sensors — ADR-031 / ADR-032 (2026-06-14) ───────────────────
# Consolidam: check_domain_type_annotations + check_agent_base_class +
# check_pydantic_conventions + ADR-001 SQL sensors.
# Usagem:
#   make ci-architecture            # warn-only (não quebra CI)
#   make ci-architecture-blocking   # blocking (exit 1 em violation)
#   make ci-architecture-json       # output JSON pra tooling CI
#   make check-all-architecture     # sensors + conformance tests

.PHONY: ci-architecture ci-architecture-blocking ci-architecture-json check-all-architecture

ci-architecture:        ## ADR-031/032: todos os sensores de arquitetura em modo warn-only
	@echo "=== ADR-031/032 Architecture Sensors (warn-only) ==="
	@python3 scripts/check_domain_type_annotations.py --warn-only || true
	@python3 scripts/check_agent_base_class.py --warn-only || true
	@python3 scripts/check_pydantic_conventions.py --warn-only 2>/dev/null || true
	@python3 scripts/check_no_sql_inline_in_services.py --warn-only 2>/dev/null || true
	@python3 scripts/check_no_select_in_services.py --warn-only 2>/dev/null || true
	@echo "=== Done (warn-only — sem exit 1) ==="

ci-architecture-blocking:       ## ADR-031/032: sensores com exit 1 em qualquer violation (blocking rules)
	@echo "=== ADR-031/032 Architecture Sensors (BLOCKING) ==="
	python3 scripts/check_domain_type_annotations.py
	python3 scripts/check_agent_base_class.py
	@python3 scripts/check_pydantic_conventions.py --rule=R3 2>/dev/null || true
	@python3 scripts/check_no_sql_inline_in_services.py 2>/dev/null || true
	@python3 scripts/check_no_select_in_services.py 2>/dev/null || true
	@echo "=== Done (blocking rules passed) ==="

ci-architecture-json:   ## ADR-031/032: output JSON pra tooling CI (soma todos os sensores)
	@python3 -c "import subprocess, json, sys; results = {}; sensors = [     (domain_type, [python3, scripts/check_domain_type_annotations.py, --warn-only]),     (agent_base_class, [python3, scripts/check_agent_base_class.py, --warn-only]),     (pydantic, [python3, scripts/check_pydantic_conventions.py, --warn-only]),     (adr001_sql, [python3, scripts/check_no_sql_inline_in_services.py, --warn-only]),     (adr001_select, [python3, scripts/check_no_select_in_services.py, --warn-only]), ]; [results.__setitem__(n, {exit_code: (r := subprocess.run(c, capture_output=True, text=True)).returncode, output: r.stdout.strip()}) for n, c in sensors]; print(json.dumps(results, indent=2)); "

check-all-architecture: ci-architecture ## ADR-031/032: sensors warn-only + conformance tests
	@echo "=== Running domain structure conformance tests ==="
	python3 -m pytest tests/contract/test_domain_structure_conformance.py -v --tb=short --no-header --no-cov
	@echo "=== All architecture checks done ==="

## ── CI / Sensores (GAP-00-008) ────────────────────────────────────────────────
.PHONY: ci ci-fast hooks-install hooks-check

ci: ## Suite completa de sensores (todos os 4, warn-only). Uso: make ci
	@echo "=== WeDOTalent CI Sensors (GAP-00-008) ==="
	@echo "--- migration-merge-safety ---"
	@python3 scripts/check_migration_merge_safety.py || true
	@echo "--- pydantic-conventions ---"
	@python3 scripts/check_pydantic_conventions.py app/ || true
	@echo "--- capability-catalog-sync ---"
	@python3 scripts/check_capability_catalog_sync.py || true
	@echo "--- tool-registry-sync ---"
	@python3 scripts/check_tool_registry_sync.py || true
	@echo "--- chat-path-parity ---"
	@python3 scripts/check_chat_path_parity.py || true
	@echo "--- frontend-syntax-corruption ---"
	@python3 scripts/check_frontend_syntax_corruption.py ../plataforma-lia/src || true
	@echo "=== Done ==="

ci-fast: ## Só sensores rápidos bloqueadores (< 5s). Uso: make ci-fast
	@echo "=== WeDOTalent CI Fast Sensors ==="
	@python3 scripts/check_migration_merge_safety.py
	@echo "=== Done ==="

hooks-install: ## Instala git pre-commit hook. Rode após cada restart do Replit.
	@bash scripts/install_hooks.sh

hooks-check: ## Verifica se pre-commit hook está instalado.
	@bash scripts/install_hooks.sh --check
