# ARCHITECTURE_FITNESS_BASELINE.md — Architecture Fitness Functions (Baseline)
**Protocolo:** P27  
**Data:** 2026-04-14  
**Engenheiro:** Claude Opus 4.6  
**Baseado em:** P13 (DUPLICATION), P22 (CANONICAL_SOURCES), P23 (CONVERGENCE)  
**Executado contra:** `lia-agent-system/` (1822 .py files, 61 dominios)

**Depende de:** P13, P22, P23  
**Alimenta:** P32, P35

---

## RESULTADOS DO BASELINE

### Sumario

| Metrica | Valor |
|---------|-------|
| **Total de testes** | 12 |
| **Passando** | 8 (67%) |
| **Falhando** | 4 (33%) |

### Por Categoria

| Categoria | Testes | Pass | Fail | % Pass |
|-----------|--------|------|------|--------|
| **Cat 1: SSOT (Single Source of Truth)** | 3 | 2 | 1 | 67% |
| **Cat 2: Estrutura de Agentes** | 4 | 2 | 2 | 50% |
| **Cat 3: Cross-cutting Enforcement** | 5 | 4 | 1 | 80% |

---

## CAT 1: SINGLE SOURCE OF TRUTH

### T1.1 LLM Instantiation Only Via Factory — FAIL (1 violation)

| Status | Violations | Detalhes |
|--------|-----------|----------|
| FAIL | 1 | `app/domains/ai/services/llm.py` instancia `ChatAnthropic`, `genai.Client`, `ChatOpenAI` diretamente |

**Arquivo violador:** `app/domains/ai/services/llm.py`
- Este arquivo e o proprio LLM service — cria clientes como parte de sua funcao
- **Veredicto:** FALSE POSITIVE parcial — este e um provider interno, nao um bypass. Mas deveria delegar para LLMProviderFactory/ProviderContainer em vez de instanciar diretamente.

**Acao:** Migrar `llm.py` para usar `ProviderContainer` internamente. Esforco: S.

### T1.2 Compliance Domain Prompt Enforcement — PASS (0 violations)

| Status | Detalhes |
|--------|----------|
| PASS | 100% dos domain.py que existem herdam de ComplianceDomainPrompt |

**LIA-C01 blocking funciona.** Nenhum dominio registrado sem compliance.

### T1.3 FairnessGuard in Decision Agents — PASS (0 violations)

| Status | Detalhes |
|--------|----------|
| PASS | Todos os 5 dominios de decisao (sourcing, cv_screening, pipeline, recruiter_assistant, analytics) importam FairnessGuard |

---

## CAT 2: ESTRUTURA DE AGENTES

### T2.1 Every Domain Has domain.py — FAIL (44 of 61 domains)

| Status | Total Dominios | Com domain.py | Sem domain.py |
|--------|---------------|---------------|---------------|
| FAIL | 61 | 17 | 44 |

**Dominios sem domain.py (amostra):**
admin, admin_settings, agent_memory, ai, approvals, auth, autonomous, billing, bulk_actions, candidate_lists, candidates, chat, client_users, clients, company, company_culture, company_settings, compliance, consent, credits, data_subject, digital_twin, email_templates, goals, health_check, integrations_hub, interview_intelligence, job_creation, job_vacancies_analytics, journey_mapping, lgpd, modules, notifications, observability, opinions, policy, recruitment, recruitment_campaign, recruitment_journey, saas_metrics, shared_searches, talent_intelligence, talent_pool, tasks, technical_tests, triagem, trust_center, voice, workforce

**Analise:** A maioria destes 44 dominios sao "dominios leves" (4 files cada, tipicamente `__init__.py` + `actions.py` + `services/` + `repositories/`). Eles operam como sub-modulos chamados por dominios maiores, nao como dominios autonomos com routing proprio.

**Veredicto:** NAO e necessariamente um problema — nem todo modulo precisa de `domain.py` se nao e roteavel diretamente. Mas a estrutura deveria ser consistente.

**Acao:** Para os 44 dominios sem domain.py, classificar como:
- **Roteavel** (precisa domain.py): autonomous, digital_twin, voice, billing — estimar 5-7 que realmente precisam
- **Sub-modulo** (nao precisa domain.py): admin, health_check, lgpd — funcoes de suporte

### T2.2 No Inline System Prompts — FAIL (12 violations)

| Status | Violations | Detalhes |
|--------|-----------|----------|
| FAIL | 12 | 12 arquivos `*_system_prompt.py` com `DOMAIN_SPECIFIC` inline |

**Arquivos violadores:**
1. `sourcing/agents/sourcing_system_prompt.py`
2. `job_management/agents/wizard_system_prompt.py`
3. `cv_screening/agents/pipeline_system_prompt.py`
4. `communication/agents/communication_system_prompt.py`
5. `analytics/agents/analytics_system_prompt.py`
6. `ats_integration/agents/ats_integration_system_prompt.py`
7. `automation/agents/automation_system_prompt.py`
8. `recruiter_assistant/agents/jobs_mgmt_system_prompt.py`
9. `recruiter_assistant/agents/kanban_system_prompt.py`
10. `recruiter_assistant/agents/talent_system_prompt.py`
11. `hiring_policy/agents/policy_system_prompt.py`
12. `company_settings/agents/company_system_prompt.py`

**Acao:** Migrar para `config/prompts.yaml` por dominio (P25). Esforco: M (3-5 dias para 12 migracoes).

### T2.3 Every ReAct Agent Has EnhancedAgentMixin — PASS (0 violations)

| Status | Total ReAct | Com Mixin | Sem Mixin |
|--------|------------|-----------|-----------|
| PASS | 13 | 13 | 0 |

**100% dos ReAct agents herdam EnhancedAgentMixin.** Memory e learning automaticos.

### T2.4 Tool Registry Per Domain — PASS (0 violations)

| Status | Dominios com Agents | Dominios com Tools | Missing |
|--------|--------------------|--------------------|---------|
| PASS | 11 | 13 | 0 |

**Todos os dominios com agentes tem tool registry correspondente.** Ate dominios sem agentes tem tools (ex: talent_intelligence).

---

## CAT 3: CROSS-CUTTING ENFORCEMENT

### T3.1 Audit in ReAct Agents — PASS

| Status | Total | Com Audit |
|--------|-------|-----------|
| PASS | 13/13 | Via LangGraphReActBase (AuditCallback auto-injetado) |

### T3.2 PII Strip in ReAct Agents — PASS

| Status | Total | Com PII Strip |
|--------|-------|---------------|
| PASS | 13/13 | Via LangGraphReActBase (LIA-C04 auto) |

### T3.3 No Hardcoded API Keys — PASS

| Status | Violations |
|--------|-----------|
| PASS | 0 — nenhuma API key hardcoded encontrada em app/ |

### T3.4 No Swallowed Errors (except: pass) — PASS

| Status | Violations |
|--------|-----------|
| PASS | 0 — nenhum `except: pass` ou `except Exception: pass` encontrado |

**Nota positiva:** O codebase nao engole erros silenciosamente.

### T3.5 No PII in Log Statements — FAIL (377 potential violations)

| Status | Violations |
|--------|-----------|
| FAIL | 377 log statements que referenciam campos PII (email, phone, cpf, full_name) |

**Analise:** Muitas dessas sao false positives — o codebase usa PIIMaskingFilter no handler, que mascara ANTES de emitir. Mas 377 referencias diretas a campos PII em statements de log e um risco: se o filter falhar, PII vaza.

**Acao:** Revisar as 377 ocorrencias. Estimativa: ~80% sao masked pelo filter, ~20% (~75) sao riscos reais. Esforco: M.

---

## RESUMO DA BASELINE

### Tabela Consolidada

| # | Teste | Cat | Status | Violations | Severidade |
|---|-------|-----|--------|-----------|-----------|
| T1.1 | LLM instantiation via factory | SSOT | FAIL | 1 | BAIXA (false positive parcial) |
| T1.2 | Compliance domain enforcement | SSOT | PASS | 0 | — |
| T1.3 | FairnessGuard in decision agents | SSOT | PASS | 0 | — |
| T2.1 | Every domain has domain.py | Structure | FAIL | 44 | MEDIA (maioria sao sub-modulos) |
| T2.2 | No inline system prompts | Structure | FAIL | 12 | MEDIA (migracao planejada) |
| T2.3 | ReAct agents have EnhancedMixin | Structure | PASS | 0 | — |
| T2.4 | Tool registry per domain | Structure | PASS | 0 | — |
| T3.1 | Audit in ReAct agents | Cross-cut | PASS | 0 | — |
| T3.2 | PII strip in ReAct agents | Cross-cut | PASS | 0 | — |
| T3.3 | No hardcoded API keys | Cross-cut | PASS | 0 | — |
| T3.4 | No swallowed errors | Cross-cut | PASS | 0 | — |
| T3.5 | No PII in log statements | Cross-cut | FAIL | 377 | ALTA (risco LGPD) |

### Score: 8/12 (67%) PASS

### Top 4 Falhas por Prioridade

| # | Teste | Violations | Fix | Esforco |
|---|-------|-----------|-----|---------|
| 1 | **T3.5 PII in logs** | 377 | Revisar + adicionar masking explicito | M (3-5d) |
| 2 | **T2.2 Inline prompts** | 12 | Migrar para YAML (P25) | M (3-5d) |
| 3 | **T2.1 domain.py missing** | 44 | Classificar roteaveis vs sub-modulos | S (1-2d analise) |
| 4 | **T1.1 LLM bypass** | 1 | Migrar llm.py para ProviderContainer | S (1d) |

---

## TESTES ADICIONAIS PROPOSTOS (para CI futuro)

| # | Teste | Cat | O que verifica |
|---|-------|-----|---------------|
| T4.1 | No functions > 100 lines | Quality | Complexidade de funcoes |
| T4.2 | No TODO without issue ref | Quality | Debito nao rastreado |
| T4.3 | Consistent error hierarchy | Quality | Todos erros herdam de LIAError |
| T4.4 | Protected attributes only in YAML | SSOT | Nenhuma lista inline de atributos protegidos |
| T4.5 | Every agent has tests | Coverage | Cobertura minima por agente |
| T4.6 | CalibrationWeight consumed | Cross-cut | Agentes de scoring carregam weights |
| T4.7 | FairnessGuard post-check | Cross-cut | Todos dominios fazem post-check |
| T4.8 | No CORS wildcard | Security | CORS nao permite * |

---

## PLANO DE INTEGRACAO NO CI

```yaml
# .github/workflows/fitness.yml
name: Architecture Fitness Functions

on:
  pull_request:
    paths:
      - 'app/**'
      - 'libs/**'

jobs:
  fitness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python tests/fitness/run_fitness.py
      - run: python tests/fitness/check_baseline.py --min-pass 8
    # BLOCKING: PR nao merge se score < baseline (8/12)
    # Meta: aumentar baseline a cada sprint
```

### Evolucao da Baseline

| Sprint | Meta | De | Para |
|--------|------|-----|------|
| Sprint 1 | Fix T3.5 (PII logs) + T1.1 (LLM) | 8/12 | 10/12 |
| Sprint 2 | Fix T2.2 (inline prompts) | 10/12 | 11/12 |
| Sprint 3 | Classificar T2.1 + adicionar T4.1-T4.8 | 11/12 | 11/20 (55% de 20) |
| Sprint 4+ | Fix novos testes gradualmente | 11/20 | 18/20 (90%) |

---

## RESUMO EXECUTIVO

### O que o baseline revela

O codebase esta **surpreendentemente saudavel** para vibe coding:
- **Zero API keys hardcoded**
- **Zero erros engolidos** (except: pass)
- **100% compliance enforcement** (LIA-C01 blocking funciona)
- **100% ReAct agents com audit + PII strip + enhanced mixin**
- **100% decision agents com FairnessGuard**

### Os 4 gaps reais
1. **PII em log statements** (377 refs) — risco LGPD, masking existe no handler mas e fragil
2. **12 prompts inline** — devem migrar para YAML
3. **44 dominios sem domain.py** — maioria sao sub-modulos (classificar)
4. **1 LLM bypass** — llm.py deve usar ProviderContainer

### Metafora
O fitness baseline e como um exame de saude: os orgaos vitais (compliance, audit, security) estao saudaveis. Os problemas sao colesterol (PII em logs), habitos alimentares (prompts inline) e peso (dominios sem estrutura). Nada e emergencia cirurgica — sao melhorias de habitos.
