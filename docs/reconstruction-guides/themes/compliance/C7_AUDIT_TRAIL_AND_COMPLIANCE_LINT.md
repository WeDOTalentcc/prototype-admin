# Theme C7 — Audit Trail & Compliance Lint

**Layer:** Compliance  |  **Card Jira:** 2 (Compliance)
**Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/` no Replit

---

## O que é este tema

Duas facetas de rastreabilidade e enforcement:
1. **Audit Trail** — registro imutável de toda decisão automatizada sobre candidato (cria, score, rank, reject, approve, escale). Atende LGPD Art. 37 + EU AI Act Art. 12 (rastreabilidade).
2. **Compliance Lint** — scripts automatizados em CI que validam invariantes não-negociáveis (sem PII em log, company_id validado, FairnessGuard chamado, etc.) antes de merge.

**Boundary com temas irmãos:**
- **C1 Fairness** — produz o registro; C7 armazena e gerencia
- **C5 Multi-tenancy** — garante isolation; C7 enforça via lint
- **I5 Observability** — traces/métricas operacionais; C7 é compliance-specific
- **O1 Testing** — testes funcionais; C7 lint é complementar (invariantes estruturais)

---

## Arquivos conectados (8 Python + 1 YAML + 13 lint scripts + 1 migration)

### Camada Persona (LLM vê — 1 YAML)

| Arquivo | Bundle | Como é injetado |
|---------|--------|-----------------|
| `compliance_block.yaml` (seção `decision.audit`) | LIA_YAMLS §shared | "Toda decisão sobre candidatos deve ser registrada com: critérios utilizados, score/ranking, justificativa, timestamp, identificação do agente. Decisões sem justificativa documentada são não-auditáveis e podem ser contestadas." |

### Camada Código (Python — 8 arquivos)

**Core audit (6 arquivos em app/shared/compliance/):**

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|------------------|
| `audit_service.py` | `app/shared/compliance/audit_service.py` | 659 | **Núcleo.** `AuditService` singleton com `log_decision()`. `get_audit_service()` retorna instance global. Nota: `log_llm_call()` e `log_tool_call()` NÃO existem nesta classe — audit de LLM/tool é feito via `@tool_handler` (I2) |
| `audit_callback.py` | `app/shared/compliance/audit_callback.py` | 313 | `AuditCallback(BaseCallbackHandler)` — integra com LangGraph para capturar LLM calls + tool calls + node transitions automaticamente + custo estimado via `_estimate_cost()` |
| `audit_models.py` | `app/shared/compliance/audit_models.py` | 128 | Dataclasses: `LLMCallRecord`, `ToolCallRecord`, `NodeTransitionRecord`, `RequestCostRecord`, `ExecutionAuditRecord` |
| `audit_storage.py` | `app/shared/compliance/audit_storage.py` | 8 | Thin wrapper — delega para `libs/audit/lia_audit/audit_storage.py` |
| `audit_writer.py` | `app/shared/compliance/audit_writer.py` | 5 | Thin wrapper — delega para `libs/audit/lia_audit/audit_writer.py` |
| `scoring_safeguards.py` | `app/shared/compliance/scoring_safeguards.py` | 163 | **Helpers obrigatórios.** `run_fairness_check()`, `log_scoring_decision()`, `hash_payload()`, `schedule_audit_log()`, `FairnessBlockedError` |

**Shared lib (2 arquivos em libs/audit/lia_audit/):**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|------------------|
| `audit_callback.py` | `libs/audit/lia_audit/audit_callback.py` | Implementação canônica (para reuso por outros projetos) |
| `audit_models.py` | `libs/audit/lia_audit/audit_models.py` | Models canônicos |

**Modelo SQLAlchemy:**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|------------------|
| `audit_log.py` | `libs/models/lia_models/audit_log.py` (real: ~128L) | `AuditLog` table + `DecisionType` enum |
| `audit_models.py` (shim) | `app/shared/compliance/audit_models.py` (7L) | Re-exporta de `libs/audit/lia_audit/audit_models.py` — não implementação |

**Migration canônica:**
- `alembic/versions/015_add_fairness_audit_log.py` — cria tabela `fairness_audit_log`

### 13 Lint Scripts (scripts/check_*.py)

| Script | O que verifica |
|--------|----------------|
| `check_duplicate_indexes.py` | Alembic migrations não criam índices duplicados |
| `check_forbidden_imports.py` | Impede imports proibidos (ex.: langchain_community deprecated) |
| `check_init_completeness.py` | `__init__.py` exporta tudo declarado |
| `check_llm_factory_enforcement.py` | LLM calls via `LLMProviderFactory` (sem import direto de anthropic/openai) |
| `check_llm_imports.py` | Idem ao anterior, complementar |
| `check_no_langchain_tool_decorator.py` | Proíbe `@langchain.tool` (usar `@tool_handler`) |
| `check_no_legacy_tool_decorator.py` | Proíbe decorators de tool antigos |
| `check_no_pii_in_logs.py` | **C2-related**: zero `logging.getLogger` direto (usar `get_masked_logger`) |
| `check_no_sql_in_controllers.py` | Controllers/endpoints não têm SQL direto (usar repositories) |
| `check_require_company_exemptions.py` | **C5-related**: endpoints têm `Depends(get_verified_company_id)` |
| `check_response_models.py` | **I6-related**: todo endpoint declara `response_model` (ADR-005) |
| `check_shim_sla.py` | Shim/deprecated modules respeitam SLA de remoção |
| `check_tool_authoring_surface.py` | Tools seguem padrão canônico |

### Integration points

- **`ComplianceDomainPrompt`** (C1) chama `AuditService.log_decision()` em `pre_process` e `post_process`
- **`AuditCallback`** é registrado no `LangGraphReActBase` — captura TODO call automaticamente
- **`scoring_safeguards.py`** é importado por CV screening, WSI evaluation, ranking services
- **Lint scripts** rodam em GitHub Actions + pre-commit hooks
- **`fairness_audit_log`** table alimenta BiasAuditService (C1 post-deploy audit)

---

## Lógica IN → OUT

### Input de audit

```python
# audit_service.log_decision() aceita:
company_id: str         # SEMPRE do JWT (C5)
subject_id: str         # candidate_id / job_vacancy_id
decision_type: DecisionType  # enum: SCORE_CANDIDATE, APPROVE_CANDIDATE, REJECT_CANDIDATE, MOVE_STAGE, SEND_MESSAGE, SCHEDULE_INTERVIEW, GENERATE_FEEDBACK, JOB_CREATION
criteria_used: list[str]     # ["Python experience", "5+ years"]
criteria_ignored: list[str]  # protected attributes list
score_breakdown: dict        # {"technical": 75, "behavioral": 60}
reasoning: list[str]         # explicações (podem ir)
fairness_flags: list[str]    # se L1/L2/L3 sinalizou
confidence: float            # 0.0-1.0
agent_name: str              # "CVScreeningAgent"
timestamp: datetime          # auto-populated
```

### Processing

**Fluxo completo** (de `scoring_safeguards.py::log_scoring_decision` + `audit_service`):

```
1. Decision agent invoca scoring (ex.: cv_screening)
2. scoring_safeguards.run_fairness_check(payload):
   - Chama FairnessGuard.check() (L1+L2)
   - Retorna (result, is_blocked)
3. Se is_blocked:
   - raise FairnessBlockedError → agente retorna educational_message
   - AINDA ASSIM: log_scoring_decision é chamado (registrar bloqueio)
4. Se não blocked: continua scoring normal
5. log_scoring_decision(company_id, candidate_id, job_id, score, criteria_used, ...):
   - Schedule audit async via asyncio.create_task (não bloqueia scoring)
   - AuditService.log_decision monta ExecutionAuditRecord
   - AuditWriter persiste em fairness_audit_log table
6. LangGraph AuditCallback intercepta:
   - on_llm_start/end → LLMCallRecord
   - on_tool_start/end → ToolCallRecord
   - on_chain_start/end → NodeTransitionRecord
   - Custo estimado via _estimate_cost(model, tokens)
7. RequestCostRecord agregado: soma de todos os LLMCallRecord
8. ExecutionAuditRecord flushes to audit_log + fairness_audit_log tables
```

### Output — AuditLog model

```python
# libs/models/lia_models/audit_log.py
# ATENÇÃO: os valores REAIS do DecisionType (verificados via SSH 2026-04-24):
class DecisionType(str, Enum):
    SCORE_CANDIDATE = "score_candidate"
    APPROVE_CANDIDATE = "approve_candidate"
    REJECT_CANDIDATE = "reject_candidate"
    MOVE_STAGE = "move_stage"
    SEND_MESSAGE = "send_message"
    SCHEDULE_INTERVIEW = "schedule_interview"
    GENERATE_FEEDBACK = "generate_feedback"
    JOB_CREATION = "job_creation"
    # NÃO usar: CV_SCREENING, WSI_EVALUATION, PIPELINE_PROMOTION etc (não existem no código)

class AuditLog(Base):
    id: UUID
    company_id: UUID                # tenant isolation
    candidate_id: UUID              # subject
    job_vacancy_id: UUID
    decision_type: DecisionType
    decision: str                   # "approved" | "rejected" | "shortlisted"
    score: float | None
    action: str | None
    criteria_used: ARRAY[str]
    criteria_ignored: ARRAY[str]
    reasoning: ARRAY[str]
    fairness_flags: ARRAY[str]
    confidence: float | None
    agent_name: str
    human_reviewed_at: datetime | None
    human_override: str | None
    created_at: datetime
```

### Side effects

- **Tabela `audit_log`** (ou `fairness_audit_log` específica) recebe row
- **Métricas**: `audit_decisions_total{decision_type, company_id}`, `audit_llm_calls_total`, `audit_tool_calls_total`, `audit_cost_usd_total{model}`
- **Eventos** publicados via UnifiedEventPublisher (R3) — outros sistemas podem reagir (ex.: send email de contestação)
- **Candidate portal** (C4) lê audit_log para produzir explanation

### Escalation / HITL

| Trigger | Ação |
|---------|------|
| Decisão com `fairness_flags` não vazia | Alerta compliance team |
| Padrão de rejeições discriminatórias (via BiasAuditService) | Abertura automática de revisão |
| Audit log falha de escrita (DB down) | Retry + alert SRE |
| Decisão sem `criteria_used` (bug) | Lint CI previne, mas se escapar: audit preenchido com "(missing)" + alert |
| Custo LLM ultrapassa budget tenant (C5 BYOK) | Throttle + email admin |

---

## Lint Scripts detalhados

### Nota: script check_c3b_compliance.py

> **ATENÇÃO**: `check_c3b_compliance.py` **NÃO EXISTE** no disco (verificado via SSH 2026-04-24). O conceito abaixo é aspiracional — implementar no v5.

```bash
# Procura por decision agents que NÃO chamam pre_process (compliance_base.py)
# Blocks merge if found
```

Rodar manualmente:
```bash
python scripts/check_c3b_compliance.py
# Output: lista de agents problemáticos com nome do arquivo + linha
```

### `check_fairness_consolidation.py`

Verifica que scoring services importam **apenas** de `app.shared.compliance.fairness_guard` (fonte canônica). Proíbe forks ou imports de versões antigas.

### `check_no_pii_in_logs.py`

Grep em todo código Python:
- ❌ `logging.getLogger(__name__)` → bloqueia
- ✅ `get_masked_logger(__name__)` → passa

### `check_require_company_exemptions.py`

Verifica que cada endpoint FastAPI declara `Depends(get_verified_company_id)` ou está em allowlist explícita (health check, public).

### `check_response_models.py`

ADR-005: todo endpoint declara `response_model=<Schema>`. Lint bloqueia endpoints "open" (sem schema).

### Como integrar em CI

```yaml
# .github/workflows/compliance-lint.yml
name: Compliance Lint
on: [pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - name: Run compliance lint
        run: |
          python scripts/check_c3b_compliance.py
          python scripts/check_fairness_consolidation.py
          python scripts/check_no_pii_in_logs.py
          python scripts/check_require_company_exemptions.py
          python scripts/check_response_models.py
          python scripts/check_llm_factory_enforcement.py
          # (... todos os 13)
```

---

## Instruções para Claude Code / Cursor

### "Implementa Audit Trail + Compliance Lint no v5"

```
1. COPIE 8 arquivos Python (audit_service, callback, models, storage, writer, safeguards, + libs/audit/*)

2. CRIE Alembic migration para audit_log table:
   # Baseado em libs/models/lia_models/audit_log.py
   # Inclui: DecisionType enum, campos company_id/subject/criteria_used/reasoning/...

3. REGISTRE AuditCallback no LangGraph setup:
   # em LangGraphReActBase.__init__
   callbacks = [AuditCallback(), ...]

4. INTEGRE scoring_safeguards em TODO scoring service:
   from app.shared.compliance.scoring_safeguards import (
       run_fairness_check, log_scoring_decision, FairnessBlockedError
   )

   result, blocked = run_fairness_check(input_text)
   if blocked:
       raise FairnessBlockedError(result.educational_message)
   # ... calcula score ...
   await log_scoring_decision(
       company_id=company_id,
       candidate_id=candidate_id,
       score=final_score,
       criteria_used=[...],
       criteria_ignored=protected_attrs
   )

5. COPIE 13 lint scripts para scripts/check_*.py

6. CONFIGURE CI (.github/workflows/compliance-lint.yml):
   - Rodar TODOS os 13 scripts
   - Bloquear PR se algum falhar

7. CONFIGURE pre-commit hooks (opcional mas recomendado):
   # .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: compliance-lint
         name: Compliance lint
         entry: bash -c "python scripts/check_c3b_compliance.py && ..."
         language: system

8. VERIFIQUE:
   - pytest tests/unit/test_audit_service.py
   - pytest tests/unit/test_scoring_safeguards.py
   - pytest tests/integration/test_audit_log_flow.py
   - Rodar TODOS os 13 lint scripts localmente (zero violations)
```

### "Adiciona audit a uma feature nova"

```
Se feature produz decisão sobre candidato:
  → import scoring_safeguards
  → Chamar run_fairness_check(input)
  → Chamar log_scoring_decision com criteria_used + criteria_ignored completos
  → NUNCA skipar log mesmo se blocked (registrar bloqueio é auditoria)

Se feature é novo tipo de decisão:
  → Adicionar novo valor em DecisionType enum
  → Atualizar migration para aceitar novo valor

Se feature invoca LLM direto:
  → AuditCallback captura automaticamente (via LangGraph callbacks)
  → Se não usar LangGraph, invocar AuditService.log_llm_call manualmente

Se feature tem invariante novo:
  → Criar scripts/check_<invariant>.py
  → Adicionar ao CI workflow
  → Documentar em C7 doc
```

### Setup em CLAUDE.md

```markdown
## Compliance: Audit Trail + Lint (C7)

- **Toda decisão** sobre candidato passa por `scoring_safeguards.log_scoring_decision`
- **criteria_used + criteria_ignored** SEMPRE preenchidos (nunca vazios)
- **AuditCallback** registrado em LangGraph callbacks — captura LLM + tool calls
- **13 lint scripts** rodando em CI — PR bloqueia se algum falha
- **audit_log table**: imutável, retenção conforme LGPD Art. 16

Lint scripts a rodar localmente antes de PR:
```bash
for s in scripts/check_*.py; do python "$s"; done
```

Consultar `themes/compliance/C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md`.
```

### Setup em `.cursor/rules/audit.mdc`

```
---
description: "C7 Audit Trail + Compliance Lint"
alwaysApply: false
---

Quando o usuário pedir para:
- Criar decision agent
- Adicionar scoring service
- Criar endpoint novo

1. Leia themes/compliance/C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md
2. IMPORT scoring_safeguards + log_scoring_decision
3. SEMPRE registrar criteria_used + criteria_ignored
4. NUNCA logar PII (check_no_pii_in_logs bloqueia)
5. Rodar os 13 lint scripts antes de sugerir commit
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- Backend de storage (PostgreSQL, MySQL, BigQuery)
- Formato de `ExecutionAuditRecord` (pode usar Pydantic)
- Retenção (mandato LGPD mas período varia por deployer)
- Lint framework (ruff, flake8, ast-grep — o importante é enforcement)
- Cost estimation model (usar pricing atualizado Anthropic/OpenAI)

### NÃO pode adaptar

| Invariante | Por quê | Consequência |
|-----------|---------|--------------|
| Audit log imutável (APPEND-ONLY) | LGPD Art. 37 + compliance forense | Adulteração invalida audit |
| Toda decisão logada, mesmo as blocked | Transparência regulatória | Lacunas em auditoria |
| `criteria_used` + `criteria_ignored` obrigatórios | LGPD Art. 20 (critérios utilizados) | Impossível explicar decisão |
| Lint CI bloqueia merge em violations | Prevenção de regressão | Bugs acumulam = dívida técnica |
| `fairness_flags` preservados | Permite re-auditar decisões passadas | Pattern de viés fica invisível |
| Tenant isolation em audit (`company_id` required) | Multi-tenant security | Vazamento cross-tenant |
| Retention conforme LGPD Art. 16 | Obrigação legal | Violação retenção |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `audit_log` table criada via Alembic migration
- [ ] **(P0)** `fairness_audit_log` table criada (migration 015)
- [ ] **(P0)** `DecisionType` enum populado com todos tipos do produto
- [ ] **(P0)** `AuditService` singleton + `get_audit_service()` funcionando
- [ ] **(P0)** `AuditCallback` registrado em LangGraph callbacks
- [ ] **(P0)** `scoring_safeguards` importado em TODO scoring service
- [ ] **(P0)** 13 lint scripts rodando em CI + bloqueando merge em violation
- [ ] **(P1)** Cost estimation via `_estimate_cost()` correto para providers ativos
- [ ] **(P1)** RequestCostRecord agregado por request + telemetria
- [ ] **(P1)** Pre-commit hooks opcional para dev local
- [ ] **(P1)** Retenção automatizada (cleanup job R4) conforme LGPD Art. 16
- [ ] **(P2)** Dashboard audit metrics (decisions/day, block rate, cost)
- [ ] **(P2)** Export para compliance external audit (trimestral)

---

## Gotchas e erros comuns

| Sintoma | Causa | Como evitar |
|---------|-------|-------------|
| Decisão sem audit log | Service não importou scoring_safeguards | Lint `check_c3b_compliance.py` detecta |
| Audit log bloqueia scoring (timeout) | Não usou `schedule_audit_log` (async) | Usar `asyncio.create_task` via helper |
| Lint CI falso positivo | Regex muito genérico | Revisar script + adicionar allowlist específica |
| criteria_used vazio (bug) | Agent não populou lista | Validação no log_scoring_decision: raise se empty |
| Cross-tenant em audit (A vê logs de B) | Endpoint de audit sem get_verified_company_id | Lint `check_require_company_exemptions` |
| Cost estimation errada | Pricing hardcoded desatualizado | Atualizar `_estimate_cost` ao mudar modelo |
| Retention job deletando dados válidos | Política ambígua | Dry run obrigatório + approval manual |

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| AuditService singleton | `tests/unit/test_audit_service.py` | `get_audit_service()` retorna mesma instance |
| Log decision | `tests/unit/test_log_decision.py` | criteria_used + criteria_ignored preservados |
| AuditCallback LLM | `tests/unit/test_audit_callback_llm.py` | on_llm_end registra LLMCallRecord |
| Cost estimation | `tests/unit/test_cost_estimation.py` | Model sonnet-4-5 + tokens → esperado $x |
| Scoring safeguards integration | `tests/integration/test_scoring_safeguards.py` | Fairness block → log ainda registrado |
| FairnessBlockedError | `tests/unit/test_fairness_blocked.py` | Raise propaga + log de bloqueio |
| 13 lint scripts | `tests/integration/test_compliance_lint.py` | Cada script testado com happy + sad path |
| Audit retention | `tests/integration/test_audit_retention.py` | Cleanup job respeita LGPD Art. 16 |

---

## Referências

### Bundles verbatim
- `LIA_YAMLS_CANONICAL_BUNDLE.md` §Parte 1 (compliance_block.yaml — decision.audit)

### Reconstruction guides
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.2 C8 (Audit Trail)
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §11.7 (Lint scripts como gates)

### Regulatório
- **LGPD Art. 12** — operações de tratamento
- **LGPD Art. 16** — retenção
- **LGPD Art. 37** — registro de operações
- **LGPD Art. 38** — relatório de impacto
- **EU AI Act Art. 12** — rastreabilidade
- **`responsible-ai/eu-ai-act-technical-documentation-pt.md`** §5.3 (audit log)

### Cross-references
- **C1 Fairness** — produz fairness_flags que vão ao audit
- **C5 Multi-tenancy** — isola audit por company_id
- **O1 Testing** — 13 lint scripts complementam test suite
- **R4 Background Jobs** — retention cleanup roda em scheduler

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit*
