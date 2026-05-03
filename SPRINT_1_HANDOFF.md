# SPRINT 1 HANDOFF — Remediation Wave 0 Quick Wins

**Branch:** `fix/sprint-1-quick-wins`
**Base:** `origin/main` (HEAD `0e962156d`)
**Worktree:** `/home/runner/sprint-1-quick-wins/` (separado de `feat/benefits-prv-canonical` em `/home/runner/workspace/`)
**Período:** 2026-04-30
**Owner:** Paulo (founder/produto) + Claude Opus 4.7 (execução)
**Documento mestre:** `REMEDIATION_BRIEF v1.0` em `/Users/paulomoraes/.claude/plans/deixe-isso-regisrado-e-starry-ullman.md`

---

## Status: 9/9 cards Wave 0 + BRANCH_MAP — COMPLETO

### Commits ordenados por dependência

| # | Hash | Card | Achado | Severidade | Files |
|---|---|---|---|---|---|
| 1 | `a6bafc7c9` | R-009 | F-325 | Alta | 2 |
| 2 | `5eb36f886` | R-001 | F-001 | Crítica | 3 |
| 3 | `dd0644d75` | R-002 | F-205 | Crítica | 3 |
| 4 | `98d7dc3b9` | R-003 | F-209 | Crítica | 2 |
| 5 | `d81287102` | R-004 | F-212 | Crítica | 3 |
| 6 | `7697743dc` | R-005 | F-201 | Alta | 1 |
| 7 | `a5e649ba1` | R-006 | F-309 | Alta | 2 |
| 8 | `6ec3584eb` | R-007 | F-318 | Alta | 3 |
| 9 | `1e4de3106` | R-008 | F-323 | Alta | 2 |
| 10 | `6b6f55464` | BRANCH_MAP | — | docs | 1 |

**Total:** 10 commits, ~22 arquivos alterados, ~1.4k linhas de código + testes + docs.

### Disciplinas aplicadas

- ✅ **TDD obrigatório (P0/P1):** RED → GREEN → REFACTOR para todos os 9 cards.
- ✅ **harness-engineering format:** GUIDE / SENSOR / DÉBITO em cada commit message.
- ✅ **production-quality modules:** `ai-architecture` (R-001/2), `compliance-risk` (R-003/8), `backend-quality` (R-005/6/7), `canonical-standards` (R-008).
- ✅ **CLAUDE.md global + projeto:** non-negotiables (multi-tenant, LGPD, fairness, secrets) preservados; sensors G1-G7 verdes.
- ✅ **Branch convention:** worktree separado de `feat/benefits-prv-canonical` (sem cross-contamination).
- ✅ **Pre-commit:** ruff + ruff-format + mypy + G1/G2/G4 passam em todos os commits.
- ✅ **No --no-verify, no --all-files:** apenas `pre-commit run --files <especificos>`.
- ✅ **No git push:** Paulo faz manualmente via Replit IDE → `replit-sync` → `WeDOTalentcc/wedotalent02202026`.

### Critérios de aceite por card (resumo)

#### R-001 — Eliminar bypass BYOK em skills_ontology_engine
- ✅ `import google.generativeai` removido do skills_ontology_engine.py
- ✅ Substituído por `EmbeddingProviderFactory.get_default()` + `provider.embed_batch()`
- ✅ `os.environ.get("GEMINI_API_KEY")` e `GOOGLE_API_KEY` removidos
- ✅ `scripts/check_llm_factory_enforcement.py` passa com 0 violações
- ✅ Linter estendido para detectar `genai.{configure,embed_content,GenerativeModel,embedding_model}`
- ✅ 5/5 testes em `tests/integration/test_skills_ontology_byok.py` PASSED

#### R-002 — track_llm_usage_start helper canonical (parcial — 1 caller exemplar)
- ✅ Helper `track_llm_usage_start(company_id, *, model, domain, operation)` em `token_budget_service`
- ✅ Wire exemplar em `wsi/_shared.get_anthropic_client`
- ✅ 6/6 testes em `tests/integration/test_llm_usage_tracking.py` PASSED
- ⏳ Sprint 2: wire nos 8+ callers remanescentes (lista no commit msg)

#### R-003 — Enriquecer criteria_used no AuditService
- ✅ 4 sites em `audit_service.py` substituídos por payload estruturado "key:value"
- ✅ `grep "criteria_used=\[\]" audit_service.py` retorna 0
- ✅ 5/5 testes em `tests/integration/test_audit_criteria_enriched.py` PASSED
- ⏳ Sprint 2: 2 sites remanescentes em `crew_audit.py:152` e `human_review_sampling_service.py:113`

#### R-004 — output_schema em ToolDefinition (parcial — 1 caller exemplar)
- ✅ Campo `output_schema: Optional[Type[BaseModel]]` em `ToolDefinition`
- ✅ `ToolOutput` Pydantic canonical em `tool_adapter.py`
- ✅ Wire exemplar em `communication_tool_registry.send_email`
- ✅ 6/6 testes em `tests/integration/test_tool_output_schema.py` PASSED
- ⏳ Sprint 2: 31 outros tool registries + extender `ToolExecutor` para `model_validate`

#### R-005 — response_model nos routers WSI/pipeline/sourcing
- ✅ Achado: G2 sensor já reporta 0 violações nesses paths em `origin/main`
- ✅ Pin de regressão via teste em `tests/integration/test_response_model_wsi_pipeline_sourcing.py`
- ✅ 2/2 testes PASSED
- ⏳ Sprint 2/3: 60+ endpoints sem `response_model` em paths fora do brief

#### R-006 — DEV_MODE gateado por ENVIRONMENT
- ✅ `_DEV_MODE = LIA_DEV_MODE AND ENVIRONMENT in (test/development/local/dev)`
- ✅ Drift detection log ERROR quando bloqueado
- ✅ 6/6 testes em `tests/security/test_dev_mode_env_gate.py` PASSED
- ⏳ Sprint 2: pre-commit hook que bloqueia `LIA_DEV_MODE=true` em `.env.staging|production`

#### R-007 — JWT exp/aud/iss validation
- ✅ `settings.JWT_AUDIENCE` + `JWT_ISSUER` (Optional, default None — backward compat)
- ✅ `decode_token` passa `audience`/`issuer` para `jwt.decode` quando configurados
- ✅ `create_access_token` inclui `aud`/`iss` em tokens emitidos quando configurados
- ✅ 8/8 testes em `tests/security/test_jwt_validation.py` PASSED
- ⏳ Sprint 2: documentar migration plan em `CONFIGURATION.md`; estender Rails JWT fallback

#### R-008 — Hardening ContextVar company_id (anti JWT forgery)
- ✅ 2 helpers canonicos: `_set_company_id_from_jwt(verified_payload)` e `_set_company_id_synthetic_dev_only()`
- ✅ 4 sites em `auth_enforcement.py` migrados para usar os helpers
- ✅ Synthetic helper raise RuntimeError fora de DEV_MODE (defesa em profundidade)
- ✅ Source-level audit (regex) impede regressão futura
- ✅ 7/7 testes em `tests/security/test_red_team_jwt_forgery.py` PASSED
- ⏳ Sprint 2: linter `scripts/check_no_direct_contextvar_set.py` repo-wide

#### R-009 — Wire BYOK linter no CI workflow
- ✅ Step "G-LLM: BYOK enforcement (LLM Factory)" adicionado ao job `lint`
- ✅ Sem `|| true` nem `continue-on-error: true` (bloqueante)
- ✅ Workflow já roda em `pull_request` (defesa pre-merge)
- ✅ 3/3 testes em `tests/integration/test_ci_byok_linter_wired.py` PASSED

### Arquivos novos criados

- `tests/integration/test_ci_byok_linter_wired.py` (R-009)
- `tests/integration/test_skills_ontology_byok.py` (R-001)
- `tests/integration/test_llm_usage_tracking.py` (R-002)
- `tests/integration/test_audit_criteria_enriched.py` (R-003)
- `tests/integration/test_tool_output_schema.py` (R-004)
- `tests/integration/test_response_model_wsi_pipeline_sourcing.py` (R-005)
- `tests/security/test_dev_mode_env_gate.py` (R-006)
- `tests/security/test_jwt_validation.py` (R-007)
- `tests/security/test_red_team_jwt_forgery.py` (R-008)
- `docs/BRANCH_MAP.md` (commit 10)

### Arquivos canonicos modificados

- `.github/workflows/ci.yml` — +1 step bloqueante (R-009)
- `scripts/check_llm_factory_enforcement.py` — BLOCKED_ATTRIBUTES expandido (R-001)
- `app/domains/talent_intelligence/services/skills_ontology_engine.py` — `_load_embeddings` refatorado (R-001)
- `app/domains/credits/services/token_budget_service.py` — novo helper `track_llm_usage_start` (R-002)
- `app/api/v1/wsi/_shared.py` — `get_anthropic_client` wireado (R-002)
- `app/shared/compliance/audit_service.py` — 4 payloads estruturados (R-003)
- `libs/agents-core/lia_agents_core/tool_adapter.py` — `ToolOutput` + `output_schema` (R-004)
- `app/domains/communication/agents/communication_tool_registry.py` — `send_email` declara `output_schema` (R-004)
- `app/middleware/auth_enforcement.py` — DEV_MODE gate (R-006), helpers ContextVar (R-008)
- `app/auth/security.py` — `decode_token` valida aud/iss (R-007)
- `libs/config/lia_config/config.py` — `JWT_AUDIENCE` + `JWT_ISSUER` settings (R-007)

---

## Próximos passos para o Paulo

### 1. Push manual

Branch local: `fix/sprint-1-quick-wins` em `/home/runner/sprint-1-quick-wins/`.
Pode ser pushado via Replit IDE seguindo o workflow padrão:
- Replit IDE → branch `replit-sync` → `WeDOTalentcc/wedotalent02202026`
- OU push direto da branch `fix/sprint-1-quick-wins` se for criar PR.

### 2. Revisar critérios de aceite

Cada commit message tem o bloco `─── GUIDE / SENSOR / DÉBITO ───` com:
- Critérios atingidos por card (✅ checklist)
- Débito explícito Sprint 2 documentado linha-a-linha
- Owner e dependências

### 3. Configurar settings em prod (R-007 migration plan)

Antes de mergear R-007 para prod:
1. Deploy desta fix com `JWT_AUDIENCE=None` e `JWT_ISSUER=None` (no-op).
2. Setar `JWT_AUDIENCE="lia-app"` e `JWT_ISSUER="wedotalent"` em `.env` de prod.
3. Forçar refresh de tokens em todos os clientes (ou aguardar 30min de `ACCESS_TOKEN_EXPIRE_MINUTES`).
4. Tokens legacy sem aud/iss serão rejeitados — todos clientes já terão reissue.

### 4. Verificar staging antes de prod (R-006)

Antes do deploy para staging, confirmar:
- `ENVIRONMENT=staging` está setado em staging .env
- `LIA_DEV_MODE=true` está REMOVIDO de staging .env (se estava lá)
- Caso `LIA_DEV_MODE=true` esteja em staging, R-006 vai logar ERROR ("Config drift detectado") e bloquear DEV_MODE — comportamento correto.

### 5. Sprint 2 backlog (debt explicito Sprint 1)

| Item | Card origem | Esforço estimado |
|---|---|---|
| R-002 wire restante (8+ callers) | F-205 | M (3-5d) |
| R-003 wire restante (2 sites) | F-209 | P (1d) |
| R-004 wire restante (31 tool registries) + sensor G-TOOLS + ToolExecutor.model_validate | F-212/F-200 | G (10-15d) |
| R-005 expansão (60+ endpoints) | F-201 | G (15-20d) ondas |
| Pre-commit hook anti DEV_MODE em prod templates | F-309 | P (1d) |
| `CONFIGURATION.md` migration plan JWT aud/iss | F-318 | P (1d) |
| Linter `check_no_direct_contextvar_set.py` repo-wide | F-323 | M (3-5d) |
| `tenant_llm_context.py:190` BYOK fix (fora de R-001) | F-001 | P (1-2d) |
| Wire `check_llm_imports.py` no CI também | — | P (1d) |
| Wire R-002 token tracking dentro do ProviderContainer (auto) | F-205 | M (3-5d) |

### 6. Aviso de segurança (fora de Sprint 1, mas detectado)

Durante setup, verifiquei que `git remote -v` em `lia-agent-system` expõe
GitHub PAT tokens nas URLs:

```
origin  https://ghp_<...>@github.com/WeDOTalentcc/wedotalent02202026.git
github  https://ghp_<...>@github.com/wedotalentcc/wedocc2026.git
ats-api-copia  https://ghp_<...>@github.com/WeDOTalentcc/ats-api-copia.git
```

**Recomendação Sprint 2 ou imediato:** rotacionar os PATs e migrar para SSH
remotes ou GitHub Apps. Tokens em `.git/config` ficam em backups/clones e
podem vazar.

---

## Comandos de verificação end-to-end

```bash
# No Replit, dentro do worktree:
cd /home/runner/sprint-1-quick-wins/lia-agent-system

# 1. Confirmar 10 commits do Sprint 1
git log --oneline | head -10

# 2. Rodar todos os testes do Sprint 1
PYTHONPATH=/home/runner/sprint-1-quick-wins/lia-agent-system/libs/agents-core:/home/runner/sprint-1-quick-wins/lia-agent-system/libs/config:$PYTHONPATH \
  python3 -m pytest \
  tests/integration/test_ci_byok_linter_wired.py \
  tests/integration/test_skills_ontology_byok.py \
  tests/integration/test_llm_usage_tracking.py \
  tests/integration/test_audit_criteria_enriched.py \
  tests/integration/test_tool_output_schema.py \
  tests/integration/test_response_model_wsi_pipeline_sourcing.py \
  tests/security/test_dev_mode_env_gate.py \
  tests/security/test_jwt_validation.py \
  tests/security/test_red_team_jwt_forgery.py \
  -v --no-cov

# 3. Confirmar BYOK linter passa
python3 scripts/check_llm_factory_enforcement.py

# 4. Confirmar G2 sensor para WSI/pipeline/sourcing
python3 scripts/check_response_models.py | grep -E "(wsi|pipeline|sourcing)" | head
# (deve retornar vazio)

# 5. Confirmar AST OK em todos os arquivos modificados
for f in app/domains/talent_intelligence/services/skills_ontology_engine.py \
         app/domains/credits/services/token_budget_service.py \
         app/api/v1/wsi/_shared.py \
         app/shared/compliance/audit_service.py \
         libs/agents-core/lia_agents_core/tool_adapter.py \
         app/domains/communication/agents/communication_tool_registry.py \
         app/middleware/auth_enforcement.py \
         app/auth/security.py \
         libs/config/lia_config/config.py; do
  python3 -c "import ast; ast.parse(open('$f').read()); print('OK', '$f')"
done
```

---

## Referências

- **REMEDIATION_BRIEF v1.0:** `/Users/paulomoraes/.claude/plans/deixe-isso-regisrado-e-starry-ullman.md`
- **AUDITORIA_SOBREPOSTA v1.0:** documento mestre dos 77 achados F-NNN.
- **CLAUDE.md global:** `~/.claude/CLAUDE.md` (multi-tenant + LGPD + fairness + secrets non-negotiables).
- **CLAUDE.md projeto:** `lia-agent-system/CLAUDE.md` (sensors G1-G7, TDD obrigatório P0/P1, anatomy of canonical agent).
- **Skills aplicadas:** `production-quality:modules:{ai-architecture,backend-quality,canonical-standards,compliance-risk}` + `harness-engineering` + referência `create-canonical-agent`.
- **BRANCH_MAP.md:** `lia-agent-system/docs/BRANCH_MAP.md` (criado nesta entrega, §1 = Sprint 1).

---

*SPRINT 1 HANDOFF v1.0 — gerado em 2026-04-30 ao final da execução do Sprint 1
Quick Wins (REMEDIATION_BRIEF Wave 0). Branch `fix/sprint-1-quick-wins` pronta
para review + merge + push manual pelo Paulo.*
