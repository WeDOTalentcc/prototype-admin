# ONBOARDING.md — Guia de Entrada na Plataforma LIA

**Versão:** 1.0
**Última atualização:** 2026-03-26

---

## 1. O que é a Plataforma LIA

A Plataforma LIA é um sistema de recrutamento e seleção com IA da WeDOTalent. O nome "LIA" refere-se à assistente de IA (Letícia Inteligência Artificial) que ajuda recrutadores em todo o ciclo: criação de vagas, triagem de CVs, entrevistas WSI (Work Sample Interview), agendamento, pipeline management e comunicação com candidatos.

**Stack principal:**
- **Backend:** Python 3.11 + FastAPI + LangChain/LangGraph + PostgreSQL + Redis
- **Frontend:** React 18 + Next.js + Tailwind CSS + Radix UI + shadcn/ui
- **Agentes IA:** 9 domínios especializados com ReAct loop + tools
- **LLMs:** Claude (Anthropic), GPT-4o (OpenAI), Gemini (Google) via factory pattern

---

## 2. Ordem de Leitura dos Specs

### Dia 1 — Contexto e Arquitetura

| # | Documento | Caminho | Tempo | O que você vai aprender |
|---|-----------|---------|-------|------------------------|
| 1 | **PLATFORM_MAP** | `docs/PLATFORM_MAP.md` | 30 min | Mapa geral: repositórios, fluxo entre sistemas, rotas, integrações |
| 2 | **AI_ARCHITECTURE** | `docs/specs/ai/AI_ARCHITECTURE.md` | 45 min | Como os agentes funcionam: ReAct loop, LLM factory, tool system, observability |
| 3 | **DATA_MODELS** | `docs/specs/backend/DATA_MODELS.md` | 30 min | Modelos de dados: candidatos, vagas, pipeline, WSI, notificações |

### Dia 2 — Agentes e Backend

| # | Documento | Caminho | Tempo | O que você vai aprender |
|---|-----------|---------|-------|------------------------|
| 4 | **AGENT_SPECS** | `docs/specs/ai/AGENT_SPECS.md` | 45 min | Os 9 domínios de agentes, tools, routing, state machines |
| 5 | **LLM_DECISIONS** | `docs/specs/ai/LLM_DECISIONS.md` | 20 min | Por que Claude/GPT/Gemini, quando usar cada, custos, fallbacks |
| 6 | **API_CONTRACTS** | `docs/specs/backend/API_CONTRACTS.md` | 30 min | Endpoints REST, schemas, auth, error codes |

### Dia 3 — Prompts e Qualidade IA

| # | Documento | Caminho | Tempo | O que você vai aprender |
|---|-----------|---------|-------|------------------------|
| 7 | **PROMPT_STANDARDS** | `docs/specs/ai/PROMPT_STANDARDS.md` | 30 min | Padrões de system prompts, few-shot, anti-sycophancy, idioma |
| 8 | **AI_FAILURE_MODES** | `docs/specs/ai/AI_FAILURE_MODES.md` | 25 min | O que pode dar errado: hallucination, bias, timeout, drift |
| 9 | **AI_QA_PROTOCOL** | `docs/specs/qa/AI_QA_PROTOCOL.md` | 30 min | Como testar agentes: DeepEval, RAGAS, fairness, red team |

### Dia 4 — Frontend e Design

| # | Documento | Caminho | Tempo | O que você vai aprender |
|---|-----------|---------|-------|------------------------|
| 10 | **FRONTEND_STANDARDS** | `docs/specs/frontend/FRONTEND_STANDARDS.md` | 20 min | Padrões React/Next.js, proxy routes, state management |
| 11 | **DESIGN_SYSTEM** | `docs/specs/frontend/DESIGN_SYSTEM.md` | 30 min | Tokens, componentes, tipografia 85/10/5, dark mode |
| 12 | **UX_PATTERNS** | `docs/specs/frontend/UX_PATTERNS.md` | 30 min | Navegação, loading, modais, kanban, chat, keyboard shortcuts |

### Dia 5 — QA e Processo

| # | Documento | Caminho | Tempo | O que você vai aprender |
|---|-----------|---------|-------|------------------------|
| 13 | **QA_PROTOCOL** | `docs/specs/qa/QA_PROTOCOL.md` | 25 min | Pirâmide de testes, ferramentas, coverage, load testing |
| 14 | **GOLDEN_DATASET** | `docs/specs/qa/GOLDEN_DATASET.md` | 15 min | Datasets de referência para validar IA |
| 15 | **CONTRIBUTING** | `docs/specs/process/CONTRIBUTING.md` | 20 min | Como contribuir: branches, commits, PRs, review |
| 16 | **SPEC_TEMPLATE** | `docs/specs/process/SPEC_TEMPLATE.md` | 10 min | Template para novas features |

---

## 3. Mapa de Navegação Visual

```
                    ┌─────────────────┐
                    │  PLATFORM_MAP   │ ◀── Comece aqui
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ AI            │ │ Backend       │ │ Frontend      │
    │ ARCHITECTURE  │ │ DATA_MODELS   │ │ FRONTEND      │
    │ AGENT_SPECS   │ │ API_CONTRACTS │ │ _STANDARDS    │
    │ LLM_DECISIONS │ │               │ │ DESIGN_SYSTEM │
    │ PROMPT_STDS   │ │               │ │ UX_PATTERNS   │
    │ AI_FAILURES   │ │               │ │               │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                 │                 │
            └────────────────┼────────────────┘
                             ▼
                    ┌─────────────────┐
                    │  QA             │
                    │  QA_PROTOCOL    │
                    │  AI_QA_PROTOCOL │
                    │  GOLDEN_DATASET │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  PROCESS        │
                    │  CONTRIBUTING   │
                    │  SPEC_TEMPLATE  │
                    └─────────────────┘
```

---

## 4. Primeiros Passos — Setup Local

### 4.1 Backend

```bash
cd lia-agent-system

# Instalar dependências
pip install -e ".[dev]"

# Configurar variáveis
cp .env.example .env
# Editar .env com suas chaves (ANTHROPIC_API_KEY, OPENAI_API_KEY, DATABASE_URL)

# Migrations
alembic upgrade head

# Rodar servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2 Frontend

```bash
cd plataforma-lia

# Instalar dependências
npm install

# Rodar dev server
npm run dev
# Acessar em http://localhost:3000
```

### 4.3 Rodar testes

```bash
# Backend — unit tests rápidos
cd lia-agent-system
python -m pytest tests/unit/ -m easy -v

# Frontend — Vitest
cd plataforma-lia
npx vitest run

# Frontend — Playwright e2e
npx playwright test
```

---

## 5. Conceitos-Chave

### 5.1 ReAct Loop

O padrão central de todos os agentes. O agente raciocina (Reason), age (Act) chamando uma tool, e observa (Observe) o resultado:

```
Usuário → Router → Agente do domínio → ReAct Loop:
  1. Reason: "Preciso buscar candidatos para esta vaga"
  2. Act: Chama tool `search_candidates(query, filters)`
  3. Observe: Recebe lista de candidatos
  4. Reason: "Encontrei 5 candidatos, preciso calcular score"
  5. Act: Chama tool `score_wsi_response(candidate, rubric)`
  6. Observe: Recebe scores
  7. Final: Formata resposta para o recrutador
```

**Arquivo:** `app/shared/agents/react_loop.py`

### 5.2 Domínios de Agentes

| Domínio | Responsabilidade | Arquivo base |
|---------|-----------------|-------------|
| `recruiter_assistant` | Coordenação, routing, chat geral | `app/domains/recruiter_assistant/` |
| `talent_management` | Busca, triagem, matching | `app/domains/talent_management/` |
| `pipeline` | Kanban, transições, automações | `app/domains/pipeline/` |
| `interview` | WSI, scheduling, notas | `app/domains/interview/` |
| `communication` | Email, WhatsApp, Teams, notificações | `app/domains/communication/` |
| `analytics` | KPIs, dashboards, funil | `app/domains/analytics/` |
| `sourcing` | Busca proativa, boolean queries | `app/domains/sourcing/` |
| `policy` | Regras de automação, governance | `app/domains/policy/` |
| `job_management` | CRUD de vagas, wizard | `app/domains/job_management/` |

### 5.3 LLM Factory

```python
from app.shared.providers.llm_factory import create_tracked_llm

llm = create_tracked_llm(
    domain="talent_management",
    model_provider="claude",  # ou "openai", "gemini"
    temperature=0.3,
)
response: DomainResponse = await llm.ainvoke(messages)
```

### 5.4 Multi-Tenancy

Toda query DEVE filtrar por `company_id`. Nunca retornar dados de outro tenant:

```python
query = select(Candidate).where(Candidate.company_id == company_id)
```

### 5.5 FairnessGuard

Qualquer output que impacta candidatos DEVE passar pelo FairnessGuard:

```python
from app.shared.compliance.fairness_guard import FairnessGuard
result = FairnessGuard().check(output_text)
if result.blocked:
    output_text = "Esta avaliação requer revisão humana."
```

---

## 6. Documentos de Análise (Referência)

Além dos specs, estes documentos contêm análises detalhadas:

| Documento | Caminho | Conteúdo |
|-----------|---------|----------|
| PRODUCT_DESIGN_INVENTORY | `docs/PRODUCT_DESIGN_INVENTORY.md` | 70 componentes, 35 modais, inventário completo |
| QA Report Sprint | `docs/QA_REPORT_SPRINT_2026-02-28.md` | Auditoria 32 itens, bugs corrigidos |
| QA Vacancy Review | `docs/analises/QA_VACANCY_SYSTEM_REVIEW.md` | Fluxo completo de vagas, triggers, status |
| GUIA_TESTES_ONDA1 | `docs/analises/GUIA_TESTES_ONDA1.md` | Testes manuais Ondas 1-3 (1575 linhas) |
| JIRA_CARD_CHAT_FIX | `docs/JIRA_CARD_CHAT_DESIGN_FIX.md` | Design debt do chat LIA |

---

## 7. Glossário

| Termo | Significado |
|-------|-----------|
| **LIA** | Letícia Inteligência Artificial — assistente de IA da plataforma |
| **WSI** | Work Sample Interview — entrevista baseada em simulação de trabalho real |
| **BARS** | Behaviorally Anchored Rating Scale — escala de avaliação comportamental |
| **AIR** | Adverse Impact Ratio — métrica de disparate impact (≥ 0.80 é justo) |
| **TOON** | Card visual compacto do candidato com dados-chave |
| **ReAct** | Reason-Act-Observe — padrão de loop de agentes IA |
| **SDD** | Spec-Driven Development — desenvolvimento guiado por especificação |
| **HITL** | Human-in-the-Loop — decisão delegada para humano |
| **PII** | Personally Identifiable Information — dados pessoais identificáveis |
| **Four-Fifths Rule** | Regra dos 4/5 — se taxa de seleção de um grupo < 80% do grupo mais selecionado, há disparate impact |
| **Silver Medalist** | Candidato que chegou a etapas avançadas mas não foi contratado — potencial para reaproveitamento |
| **Zero-Touch Scheduling** | Auto-agendamento de entrevista pelo candidato via link público |
| **Pipeline Velocity** | Tempo que candidatos ficam em cada etapa do processo seletivo |
