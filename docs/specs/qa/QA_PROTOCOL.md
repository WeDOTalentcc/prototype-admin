# QA_PROTOCOL.md — Protocolo de Qualidade da Plataforma LIA

**Versão:** 1.0
**Última atualização:** 2026-03-26
**Repositórios cobertos:** `lia-agent-system` (backend Python), `plataforma-lia` (frontend React/Next.js)

---

## 1. Pirâmide de Testes

```
                    ┌──────────┐
                    │  Load    │  ← Locust (stress, SLA)
                   ┌┤  Tests   ├┐
                  ┌┤└──────────┘├┐
                 ┌┤  Security   ├┐
                ┌┤ Red Teaming  ├┐
               ┌┤└─────────────┘├┐
              ┌┤   E2E Tests     ├┐
             ┌┤ (Playwright/pytest)├┐
            ┌┤└──────────────────┘ ├┐
           ┌┤  Integration Tests    ├┐
          ┌┤  (FastAPI TestClient)   ├┐
         ┌┤└─────────────────────── ┘├┐
        ┌┤   Contract + Fairness      ├┐
       ┌┤ (agent interface + 4/5 rule) ├┐
      ┌┤└──────────────────────────── ┘├┐
     ┌┤        Unit Tests               ├┐
    ┌┤   (pytest, 170 arquivos, ~40k LOC) ├┐
    └─────────────────────────────────────┘
```

| Camada | Ferramenta | Arquivos | LOC aprox. | Quando roda |
|--------|-----------|----------|-----------|-------------|
| Unit | pytest + pytest-asyncio | 170 | ~40.000 | Pre-commit (easy), CI push (medium), CI nightly (hard) |
| Contract | pytest | 16 | ~4.000 | CI push |
| Fairness | pytest + golden_dataset | 2 | ~400 | CI push |
| Integration | pytest + TestClient | 21 | ~5.000 | CI push |
| E2E (backend) | pytest + httpx | 9 | ~2.500 | CI nightly |
| E2E (frontend) | Playwright | 13 specs | ~3.000 | CI nightly |
| Security | pytest (red team) | 6 | ~700 | CI nightly |
| DeepEval | pytest + deepeval | 1 | ~100 | Release (non-blocking) |
| RAGAS | pytest + ragas | 1 | ~100 | Release (non-blocking) |
| Load | Locust | 1 + config | ~400 | Release |
| Visual | Vitest + modals tests | 1 | ~200 | CI push |

---

## 2. Configuração do Test Runner

### 2.1 Backend (pytest)

**Arquivo:** `lia-agent-system/pytest.ini`

```ini
[pytest]
asyncio_mode = auto
testpaths = app/tests tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --cov=app --cov-report=term-missing --cov-fail-under=30
         --ignore=app/tests/test_multi_tenancy_security.py
         --ignore=app/tests/test_policy_gaps_fixes.py
         --ignore=app/tests/test_sync_canonical_endpoint.py
asyncio_default_fixture_loop_scope = session
asyncio_default_test_loop_scope = session
markers =
    easy: <5ms, pre-commit
    medium: <50ms, CI push
    hard: ~100ms, CI nightly
    very_hard: LLM real, release only
filterwarnings =
    ignore::DeprecationWarning
    ignore::pytest.PytestUnraisableExceptionWarning
```

**Markers de complexidade:**

| Marker | SLA por teste | Quando rodar |
|--------|--------------|-------------|
| `@pytest.mark.easy` | < 5ms | Pre-commit |
| `@pytest.mark.medium` | < 50ms | CI push |
| `@pytest.mark.hard` | ~ 100ms | CI nightly |
| `@pytest.mark.very_hard` | Ilimitado (LLM real) | Release only |

**Coverage gate:** `--cov-fail-under=30` (atual ~32%, target 80%)

**Progressão histórica:** 10% → 12% → 25% → 29% → 32% → 27% (realinhamento) → 30% → 34% → 40% → 50% → 80% (meta)

### 2.2 Frontend (Playwright)

**Diretório:** `plataforma-lia/e2e/`

```
e2e/
├── fixtures/
│   ├── auth.fixture.ts
│   └── wizard-conversation.fixture.ts
└── tests/
    ├── auth/
    │   └── login.spec.ts
    ├── chat/
    │   ├── conversation-memory.spec.ts
    │   └── tool-calling.spec.ts
    ├── kanban/
    │   └── move-candidate.spec.ts
    └── wizard/
        ├── complete-flow.spec.ts
        ├── step1-info-basica.spec.ts
        ├── step2-requisitos.spec.ts
        ├── step3-competencias.spec.ts
        ├── step4-beneficios.spec.ts
        ├── step5-wsi.spec.ts
        ├── step6-descricao.spec.ts
        ├── step7-revisao.spec.ts
        └── test_job_creation_lia.spec.ts
```

### 2.3 Frontend (Vitest)

**Diretório:** `plataforma-lia/src/components/modals/__tests__/`

- `bulk-action-modal-rejection-reasons.test.ts` — testa lógica de rejeição em lote

---

## 3. Estrutura de Diretórios de Teste (Backend)

```
lia-agent-system/tests/
├── conftest.py                    # Fixtures globais (mock_tool, mock_memory_service, base_react_loop)
├── unit/                          # 170 arquivos — testes isolados com mocking
│   ├── test_ach020_api_docs.py
│   ├── test_admin_guardrails_api.py
│   ├── test_agent_health_alert_service.py
│   ├── test_anti_sycophancy_prompts.py
│   ├── test_audit_trail_gates.py
│   ├── test_c1_ats_lgpd_fields.py
│   ├── test_disparate_impact_wsi.py
│   ├── test_pipeline_velocity_service.py
│   ├── test_rubric_evaluation_service.py
│   ├── test_silver_medalist_service.py
│   ├── test_stage_entered_at.py
│   └── ... (170 total)
├── contract/                      # 16 arquivos — contratos agent-to-agent
│   ├── test_agent_interface_contract.py
│   ├── test_hitl_contracts.py
│   ├── test_multi_tenant_isolation_contract.py
│   ├── test_prompt_version_contracts.py
│   ├── test_wizard_pipeline_contract.py
│   └── ... (16 total)
├── fairness/                      # 2 arquivos — bias audit
│   ├── test_four_fifths_rule.py   # Regra dos 4/5 (EEOC)
│   └── test_red_teaming.py        # Red teaming adversarial
├── integration/                   # 21 arquivos — endpoints reais
│   ├── test_api_candidates_coverage.py
│   ├── test_ciclo_fechado_flow.py
│   ├── test_guardrails_flow.py
│   ├── test_hitl_flow.py
│   ├── test_pipeline_transition_flow.py
│   └── ... (21 total)
├── e2e/                           # 9 arquivos — cenários end-to-end
│   ├── test_cascaded_router_e2e.py
│   ├── test_job_wizard_graph_e2e.py
│   ├── test_langgraph_agents_e2e.py
│   ├── test_wsi_interview_graph_e2e.py
│   └── ... (9 total)
├── security/                      # 6 arquivos — red team
│   ├── test_red_team_circuit_breakers.py
│   ├── test_red_team_fairness.py
│   ├── test_red_team_lgpd.py
│   ├── test_red_team_multi_tenant.py
│   ├── test_red_team_pii.py
│   └── test_red_team_prompt_injection.py
├── deepeval/                      # 1 arquivo — qualidade LLM
│   └── test_agent_quality.py      # Hallucination, Faithfulness, Bias
├── ragas/                         # 1 arquivo + golden queries
│   ├── golden_queries.py          # 5 fluxos críticos
│   └── test_ragas_evaluation.py
├── load/                          # Load testing
│   ├── locustfile.py              # 4 cenários (search, toon, wsi_batch, wizard)
│   ├── load_test_config.py        # Samples e SLAs
│   └── README.md
└── fixtures/
    └── golden_dataset.py          # 60 candidatos sintéticos para fairness
```

---

## 4. Critérios de Cobertura por Camada

### 4.1 Unit Tests (obrigatório)

| Domínio | Cobertura mínima | Foco |
|---------|-----------------|------|
| Services (`app/services/`) | 80% | Lógica de negócio, cálculos de score, validações |
| Agents (`app/domains/*/agents/`) | 60% | Tool registry, routing, state machine |
| API endpoints (`app/api/`) | 70% | Request/response schemas, auth, error codes |
| Models (`app/models/`) | 50% | Validação de campos, defaults, constraints |
| Shared (`app/shared/`) | 80% | ReAct loop, LLM factory, observability |

### 4.2 Contract Tests (obrigatório)

Cada agente que expõe uma interface pública deve ter contract test verificando:
- Input schema aceito
- Output schema retornado
- Campos obrigatórios presentes
- Multi-tenant isolation (company_id filtering)

**Arquivo de referência:** `tests/contract/test_agent_interface_contract.py`

### 4.3 Integration Tests (obrigatório)

Endpoints REST devem ter cobertura para:
- Happy path (200/201)
- Validação de input (422)
- Autenticação ausente (401)
- Autorização insuficiente (403)
- Recurso não encontrado (404)
- Limite de plano (402)

### 4.4 Fairness Tests (obrigatório)

- **Four-Fifths Rule:** adverse_impact_ratio ≥ 0.80 para todas as dimensões (gênero, idade, PCD, região)
- **Golden dataset:** 60 candidatos sintéticos com scores independentes de dados demográficos
- **Red teaming:** prompts adversariais não devem alterar scores com base em atributos protegidos

---

## 5. Fixtures Globais

### 5.1 Backend (`tests/conftest.py`)

| Fixture | Tipo | Uso |
|---------|------|-----|
| `mock_tool` | `AsyncMock` | ToolDefinition genérica para testes de ReAct loop |
| `mock_memory_service` | `MagicMock` | Working memory com métodos stub |
| `base_react_config` | `ReActConfig` | Config base com system_prompt, tools, max_iterations |
| `base_react_loop` | `ReActLoop` | Loop pronto para teste com config + memory |
| `observer` | `ReActObserver` | Observer com session_id/domain/agent_class de teste |

### 5.2 Frontend (`e2e/fixtures/`)

| Fixture | Arquivo | Uso |
|---------|---------|-----|
| `auth.fixture.ts` | `e2e/fixtures/` | Login, session management, auth state |
| `wizard-conversation.fixture.ts` | `e2e/fixtures/` | Conversa wizard pré-configurada |

---

## 6. Load Testing

**Ferramenta:** Locust (`tests/load/locustfile.py`)

| Cenário | Endpoint | SLA | Descrição |
|---------|----------|-----|-----------|
| `candidate_search` | `GET /api/v1/candidates/rag-search` | P95 < 3s | RAG híbrido BM25 + semantic |
| `toon_card` | `GET /api/v1/candidates/{id}/toon` | P95 < 2s | TOON card com cache Redis |
| `wsi_screening_batch` | `POST /api/v1/wsi/sessions` | P95 < 5s | Inicializar entrevistas WSI em lote |
| `wizard_interaction` | `POST /api/v1/chat` | P95 < 10s | Fluxo wizard com LLM |

**Execução:**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --users=50 --spawn-rate=5 --run-time=5m --headless
```

**Variáveis:**
- `LIA_AUTH_TOKEN` — Bearer token (obrigatório em prod)
- `LIA_COMPANY_ID` — company_id de testes (default: `c-load-001`)

---

## 7. Security Testing (Red Team)

**Diretório:** `tests/security/` (6 arquivos)

| Arquivo | Categoria | Verificações |
|---------|-----------|-------------|
| `test_red_team_prompt_injection.py` | Prompt Injection | 3 payloads detectados, 5 gaps xfail (DAN, HTML, jailbreak) |
| `test_red_team_pii.py` | PII Leakage | PIIMaskingFilter mascara CPF, email, telefone, nomes |
| `test_red_team_lgpd.py` | LGPD Compliance | Consent check, scheduled deletion, data anonymization |
| `test_red_team_multi_tenant.py` | Tenant Isolation | company_id filtering em todas as queries |
| `test_red_team_fairness.py` | Bias Adversarial | Prompts tentando alterar scores por atributos protegidos |
| `test_red_team_circuit_breakers.py` | Resiliência | Circuit breaker + retry em serviços externos |

**PromptInjectionGuard:**
- **Módulo:** `app/shared/prompt_injection`
- **Resultado:** `is_suspicious: bool`, `risk_level: str`, `confidence: float`
- **Detectados:** "Ignore all previous instructions", "###SYSTEM###", "IGNORE PREVIOUS"
- **Gaps conhecidos (xfail):** HTML injection, DAN, jailbreak, language model attacks

---

## 8. Comandos de Execução

### 8.1 Backend

```bash
cd lia-agent-system

# Suite completa
python -m pytest tests/ -v

# Apenas unit
python -m pytest tests/unit/ -v

# Por marker
python -m pytest tests/ -m easy -v        # < 5ms cada
python -m pytest tests/ -m medium -v      # < 50ms cada

# Com coverage report
python -m pytest tests/ --cov=app --cov-report=html

# Apenas fairness
python -m pytest tests/fairness/ -v

# Apenas contract
python -m pytest tests/contract/ -v

# Apenas security (red team)
python -m pytest tests/security/ -v

# DeepEval (requer OPENAI_API_KEY, non-blocking no CI)
python -m pytest tests/deepeval/ -v

# RAGAS (requer OPENAI_API_KEY, non-blocking no CI)
python -m pytest tests/ragas/ -v
```

### 8.2 Frontend

```bash
cd plataforma-lia

# Vitest (unit/component)
npx vitest run

# Playwright (e2e)
npx playwright test

# Playwright — suite específica
npx playwright test e2e/tests/wizard/
npx playwright test e2e/tests/chat/
npx playwright test e2e/tests/kanban/
```

---

## 9. QA Report — Referência Histórica

O relatório `docs/QA_REPORT_SPRINT_2026-02-28.md` documenta uma auditoria completa:

| Camada | Itens verificados | Resultado |
|--------|------------------|-----------|
| L — Legal/LGPD | 5 | 5/5 OK (L1, L8 corrigidos) |
| B — Bias/Fairness | 4 | 4/4 OK (B1, B2 corrigidos) |
| A — Arquitetura | 5 | 5/5 OK (A2 corrigido) |
| M — Monetização | 4 | 4/4 OK |
| N — Notificações | 4 | 4/4 OK |
| T — Testes | 4 | 4/4 OK (T1, T2 corrigidos) |

**Bugs corrigidos nesse sprint:**
- B1: Nome do candidato removido do contexto LLM (blind evaluation)
- B2: GEOGRAPHIC_ADJUSTMENTS discriminatório esvaziado
- L1: LANGCHAIN_TRACING_V2 default = False
- L8: WhatsApp verify token sem fallback hardcoded
- A2: Retry com tenacity no Gemini provider
- T1: Campo `priority` adicionado nos testes BARS
- T2: `question_count` max corrigido de 15 → 25

---

## 10. Critérios de Aprovação de PR

| Critério | Obrigatório | Bloqueante |
|----------|-------------|-----------|
| Testes unitários passando | Sim | Sim |
| Coverage ≥ 30% | Sim | Sim |
| Contract tests passando | Sim | Sim |
| Fairness tests passando | Sim | Sim |
| Zero warnings de segurança (secrets hardcoded) | Sim | Sim |
| Integration tests passando | Sim | Não (warning) |
| E2E tests passando | Não (nightly) | Não |
| DeepEval/RAGAS passando | Não | Não (continue-on-error) |
| Load test SLAs atendidos | Não (release) | Não |

---

## 11. Verificação Rápida — Onda 1

**Arquivo de referência:** `docs/analises/GUIA_TESTES_ONDA1.md`

Cobre os sprints 1A–1E + 2A–2D + 3A com testes manuais e automatizados para:
- `stage_entered_at` (1A) — coluna, index, regra de negócio
- Pipeline Velocity Engine (1B) — endpoints, alertas, chat LIA
- Zero-Touch Scheduling (1C) — fluxo completo com token público
- Silver Medalists (1E) — scoring, reaproveitamento, alertas
- Recruiter Intelligence (2A) — daily briefing, backlog, urgency score

---

## 12. Arquivos de Referência

| Arquivo | Caminho | Conteúdo |
|---------|---------|----------|
| pytest.ini | `lia-agent-system/pytest.ini` | Config do runner, markers, coverage gate |
| conftest.py | `lia-agent-system/tests/conftest.py` | Fixtures globais |
| golden_dataset.py | `lia-agent-system/tests/fixtures/golden_dataset.py` | 60 candidatos sintéticos |
| golden_queries.py | `lia-agent-system/tests/ragas/golden_queries.py` | 5 golden queries RAGAS |
| locustfile.py | `lia-agent-system/tests/load/locustfile.py` | 4 cenários de carga |
| GUIA_TESTES_ONDA1.md | `docs/analises/GUIA_TESTES_ONDA1.md` | Testes manuais Onda 1-3 |
| QA_REPORT_SPRINT.md | `docs/QA_REPORT_SPRINT_2026-02-28.md` | Auditoria completa 32 itens |
| QA_VACANCY_REVIEW.md | `docs/analises/QA_VACANCY_SYSTEM_REVIEW.md` | Review do sistema de vagas |
