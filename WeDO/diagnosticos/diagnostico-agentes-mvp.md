# Diagnóstico Completo — Agentes IA para Alpha 1 MVP
## Cruzamento: Roadmap Alpha 1 × Codebase V5 (GitHub) × Referência LIA

**Data:** 13 de Março de 2026
**Versão:** 5.0 (Análise investigativa profunda — cruzamento codebase real × `relatorio_capacidades_prompts_lia.md`)
**Método:** Leitura direta do codebase V5 via GitHub API + filesystem LIA + roadmap Alpha 1 v2 + auditoria de capacidades de prompts e chats

> **Changelog v5.0 (13/03/2026):** Análise investigativa profunda do codebase com cruzamento do `relatorio_capacidades_prompts_lia.md` (1394 linhas, 10 seções). Principais adições: **Nova Seção 13G** — Arquitetura dos 3 Níveis de Chat (Float/Kanban/Full) com escopos `scope_config.py` (TALENT_FUNNEL 20 tools, IN_JOB 25 tools, JOB_TABLE 19 tools, GLOBAL 2 tools), fluxo de decisão frontend (`isGenericQuestion()`, `analysisCommands[]`, `detect_command_type()`), endpoints `orchestrated_talent_chat.py` e `orchestrated_job_chat.py`. **Nova Seção 13H** — ActionExecutor closed-loop + PendingActionStore (HITL via chat). **Nova Seção 13I** — Templates de Resposta (18 Kanban + 8 Analytics + Float commands). **Nova Seção 13J** — Sistema Preditivo e Insights (6 ferramentas preditivas, 8 serviços de inteligência operacional, Response Cache). **Nova Seção 13K** — Quick Actions e Ações Bulk (12 quick actions + 9 bulk actions + 8 contextuais). **Seção 14 atualizada** — Jobs Management Agent adicionado como 12º agente; contagens de tools corrigidas por scope_config.py real. **Seção 16 ampliada** — 17+ capacidades ausentes identificadas (LIA Score clicável, WSI assíncrono, ML adaptativo, fit cultural, auto-routing aprendiz, etc.). **Seção 22 ampliada** — Dívidas técnicas e limitações incorporadas do relatório (fallbacks hardcoded, detecção por keywords, cache não-distribuído, arquivos monolíticos). Conflitos de merge resolvidos no `relatorio_capacidades_prompts_lia.md`. Contagem total: 15 agentes (11 ReAct + 2 LangGraph + 1 interview_graph + 1 Orchestrator), ~497 arquivos Python na camada de IA, ~130 endpoints API. Jobs Management Agent reconhecido como 12º agente ReAct (já contido nos 11 ReAct originais; total da tabela seção 8 = 15 linhas incluindo Orchestrator).
>
> **Changelog v3.0 (11/03/2026):** Sprints de Segurança e Governança SEG-1 a SEG-5 implementados e testados. Wiring completo: PromptInjectionGuard (SEG-1) em `wsi_interview_graph.py` + `agent_chat_ws.py`; FairnessGuard (SEG-2) em `sourcing_react_agent.py` + `pipeline_transition_agent.py`; PII Masking Celery workers (SEG-3A) via `worker_process_init` signal; strip_pii_for_llm_prompt (SEG-3B) em 4 callers LLM (rubric, analysis, voice, comparison); ConsentCheckerService (SEG-4) no Gate 1 do WSI (`load_context`); AuditService (SEG-5) nos gates de decisão — pipeline HITL/transition/LangGraph, sourcing ReAct/LangGraph, HITL rejected. 34 testes unitários adicionados (6 arquivos). Auditoria de governança completa: 8/8 Inegociáveis ✅, 12/13 Crenças ✅. **Atenção:** SEG-1 a SEG-5 fecham os 5 gaps críticos de WIRING. Permanecem como pendentes os 6 gaps de CONFIGURAÇÃO/BASELINE (BiasAudit, PolicyEngine, FRIA, Circuit breakers, Data Retention, DSR e2e) — estes requerem configuração antes do go-live, não implementação de código.

> **Changelog v2.0:** Documento consolidado — catálogo completo de capacidades (agentes, tools, graphs, automações, serviços, API endpoints, gaps V5) integrado diretamente neste diagnóstico como seções 13-21. Corrigido Tier 5 Router (Haiku→Sonnet→Opus), path PII Masking, adicionado PromptInjectionGuard como infra existente, adicionado job cleanup_stale_reminders (10 jobs), corrigido gap V5 Security Guard.
**Repositório V5:** `github.com/talensestg/recruiter_agent_v5`
**Referência LIA:** `lia-agent-system/` (filesystem local)

---

> ## ⚠️ ESCOPO DESTE DOCUMENTO
>
> Este diagnóstico cobre **exclusivamente o Alpha 1 MVP** — o pipeline automatizado de recrutamento: ATS import → Gate 1 → WSI triagem → Gate 2 → agendamento.
>
> ### Interfaces de conversa com LIA que estão FORA deste roadmap
>
> Os seguintes pontos de contato da LIA com o usuário **não estão mapeados nos cards** deste documento e precisam de roadmap próprio:
>
> | Interface | Onde aparece | O que faz |
> |-----------|-------------|-----------|
> | **Prompt Tabela de Vagas** | Página Gestão de Vagas (`jobs-page.tsx`) | LIA integrada na toolbar — busca inteligente de vagas, sugestões proativas, ações em lote assistidas |
> | **Prompt Página de Vaga** | Página individual de vaga | LIA contextualizada para uma vaga específica — análise pipeline, candidatos, JD |
> | **Prompt Flutuante Geral (LIA Float)** | Global — qualquer página da plataforma | Assistente flutuante sempre disponível — `LiaChatPanel` com WebSocket, HITL cards, streaming |
> | **Prompt Políticas de Recrutamento** | Página de configuração de políticas | Interface conversacional para configurar `CompanyHiringPolicy` — 19 perguntas do PolicySetupAgent |
> | **Prompt Funil de Talentos** | Kanban / Talent Funnel | LIA no funil de candidatos — movimentações, insights, scoring, ações em massa |
> | **Interface Teams** | Microsoft Teams (bot) | Bot Teams para recrutadores — notificações, aprovações HITL via Teams, queries via chat |
>
> ### Itens de implementação fora deste roadmap
>
> Consulte a **Seção 22** deste documento para a lista completa de itens recomendados por André (análise comparativa V5 vs LIA) que **não estão nos cards do Alpha 1**, incluindo os 7 cards AUD (WT-1506 a WT-1512), gaps técnicos pendentes e oportunidades de produto.

---

## 0. GLOSSÁRIO — Termos Essenciais

> **Leia antes de qualquer outra seção.** Um dev novo precisa entender estes termos para trabalhar em qualquer card.

| Termo | Definição |
|-------|-----------|
| **Alpha 1** | Versão mínima do produto com o fluxo completo: Login → Editar Vaga → WSI → Busca → Gate 1 → Contato → Follow-up → Triagem → Gate 2 → Agendamento |
| **V5** | Codebase do produto em desenvolvimento pelo time (`github.com/talensestg/recruiter_agent_v5`) |
| **LIA** | Codebase de referência da plataforma WeDOTalent (`lia-agent-system/`) — usar como modelo a copiar |
| **ReAct Agent** | Padrão de agente IA: Reasoning (pensar) + Acting (chamar ferramenta) em loop. Implementado via LangGraph prebuilt `create_react_agent` |
| **LangGraph** | Framework de grafos stateful para fluxos multi-etapa. Usado para WSI Interview, Job Wizard e Interview Scheduling |
| **4-file pattern** | Padrão obrigatório de todo agente: `*_react_agent.py` + `*_system_prompt.py` + `*_tool_registry.py` + `*_stage_context.py` |
| **WSI** | Work Simulation Interview — metodologia proprietária de triagem baseada em Bloom Taxonomy + Dreyfus Model + Big Five + CBI |
| **WRF** | Weighted Rank Fusion — algoritmo de fusão de resultados de busca (ES + PGVector) com pesos configuráveis |
| **HITL** | Human-in-the-Loop — mecanismo que pausa o agente e aguarda aprovação humana antes de prosseguir (`interrupt_before` no LangGraph) |
| **Gate 1** | Ponto de aprovação/rejeição após triagem curricular — consultor decide quem avança para a triagem WSI |
| **Gate 2** | Ponto de aprovação/rejeição após triagem WSI — consultor decide finalistas para entrevista presencial |
| **FairnessGuard** | Módulo de 3 camadas que detecta viés discriminatório em queries, JDs e respostas de agentes. Arquivo: `app/shared/compliance/fairness_guard.py` |
| **PII Masking** | Mascaramento de dados pessoais (CPF, email, telefone) nos logs para conformidade LGPD. Arquivo: `app/shared/pii_masking.py` |
| **AuditCallback** | Callback LangGraph que registra cada decisão dos agentes para auditoria SOX/BCB-498. Arquivo: `app/shared/compliance/audit_callback.py` |
| **PolicyEngine** | Motor de políticas do orquestrador — aplica guardrails antes/depois de cada execução. Arquivo: `app/orchestrator/policy_engine.py` |
| **CascadedRouter** | Router em 6 tiers: Memory Cache → Redis → VectorSemantic → FastRouter (regex) → LLM Cascade (Haiku→Sonnet→Opus) → Clarification |
| **EnhancedAgentMixin** | Mixin que adiciona memória working/LTM + guardrails + learning a qualquer agente. Arquivo: `app/shared/agents/enhanced_agent_mixin.py` |
| **PostgresSaver** | Checkpointer persistente do LangGraph (vs MemorySaver em memória). Necessário para sessões WSI entre turnos |
| **Company ID** | Identificador do tenant (empresa cliente). **OBRIGATÓRIO** em todos os modelos, queries e endpoints — nunca omitir |
| **Thread ID** | Identificador de sessão de uma conversa ou entrevista. Compartilhado entre WSI Graph e HITL Service |
| **DLQ** | Dead Letter Queue — fila de mensagens que falharam, para reprocessamento. Implementado via RabbitMQ |
| **FRIA** | Fundamental Rights Impact Assessment — avaliação obrigatória pelo EU AI Act para sistemas de triagem (Art. 6 Annex III) |
| **Four-Fifths Rule** | Regra 4/5 (NYC LL144 + EU AI Act): `adverse_impact_ratio = menor_grupo / maior_grupo >= 0.80`. Abaixo disso = discriminação estatística |
| **DSR** | Data Subject Request — solicitação de titular de dados (LGPD Art. 18): acesso, correção, exclusão, portabilidade, objeção |
| **Sprints Alpha 1** | S0 (infra base) → S1 (busca + comunicação) → S2 (WSI + triagem) → S3 (Gates + agendamento) |

---

## 0B. SETUP INICIAL — Pré-Requisitos Antes do Sprint 0

> **Execute tudo nesta seção ANTES de escrever qualquer linha de código.** Sem isso, os agentes não vão funcionar.

### 0B.1 Variáveis de Ambiente Obrigatórias

```env
# === LLM (obrigatório desde Sprint 0) ===
ANTHROPIC_API_KEY=sk-ant-...        # Claude Sonnet — LLM primário
OPENAI_API_KEY=sk-...               # GPT-4 — fallback
GOOGLE_API_KEY=...                  # Gemini — fallback + embeddings

# === Banco de Dados ===
DATABASE_URL=postgresql+asyncpg://user:pass@host/db   # PostgreSQL (Neon ou local)
REDIS_URL=redis://localhost:6379/0                    # Redis (cache + sessão)

# === Email (obrigatório desde Sprint 1) ===
RESEND_API_KEY=re_...               # Provider primário de email
SENDGRID_API_KEY=SG....             # Provider secundário (fallback)
EMAIL_FROM=noreply@wedotalent.com

# === WhatsApp (Sprint 1 — secundário) ===
WHATSAPP_META_TOKEN=...             # Meta/Graph API token
WHATSAPP_PHONE_NUMBER_ID=...        # ID do número WhatsApp Business

# === Busca (Sprint 1) ===
ELASTICSEARCH_URL=http://localhost:9200  # ES para busca fulltext
PEARCH_API_KEY=...                       # Pearch AI — 190M+ perfis

# === ATS Integration (Sprint 0 — premissa) ===
GUPY_API_KEY=...                    # Gupy ATS
PANDAPE_API_KEY=...                 # Pandapé ATS (opcional)
MERGE_API_KEY=...                   # Merge ATS connector

# === Calendário/Scheduling (Sprint 3) ===
MICROSOFT_GRAPH_CLIENT_ID=...
MICROSOFT_GRAPH_CLIENT_SECRET=...
MICROSOFT_GRAPH_TENANT_ID=...

# === Observabilidade ===
LANGSMITH_API_KEY=ls__...           # LangSmith tracing
LANGSMITH_PROJECT=alpha-1

# === Feature Flags ===
FAIRNESS_LAYER3_ENABLED=false       # LLM fairness check (opt-in — caro)
REACT_MAX_ITERATIONS_DEFAULT=5      # Max iterações por agente
REACT_MAX_TOOL_CALLS=3              # Max tool calls por request
REACT_OBSERVATION_MAX_CHARS=5000    # Trunca outputs grandes
```

### 0B.2 Migrations Alembic — Ordem Obrigatória

Execute TODAS antes de iniciar qualquer sprint:

```bash
cd lia-agent-system/
alembic upgrade head
```

**Migrations críticas para Alpha 1 (mínimo):**

| Migration | O que cria | Sprint |
|-----------|-----------|--------|
| `001` – `019` | Modelos base (candidates, jobs, pipeline, users) | Pré-requisito |
| `020_add_guardrails_table` | Tabela `guardrails` — regras de agentes por tenant | S0 |
| `032_add_hitl_tables` | `hitl_pending_actions` + `hitl_audit_trail` | S0 |
| `034_add_agent_quality_evaluations` | `agent_quality_evaluations` | S0 |
| `035_add_user_agent_preferences` | `user_agent_preferences` | S0 |

### 0B.3 Seeds Iniciais (executar na ordem)

```bash
# 1. Guardrails globais (13 regras — LGPD + Fairness + domínios)
python -c "
from app.core.seeds.guardrails_seed import run_seed
import asyncio
from app.core.database import get_db
asyncio.run(run_seed())
"

# 2. Taxonomia (skills, áreas, senioridades)
python -c "from app.core.taxonomy import seed_taxonomy; seed_taxonomy()"

# 3. Política padrão do tenant (via HiringPolicyService)
# Executar via API: POST /api/v1/policy/onboarding/start
# OU usar o PolicySetupAgent (19 perguntas)
```

### 0B.4 LangGraph PostgresSaver — Configuração

O WSIInterviewGraph e o JobWizardGraph precisam de checkpointing persistente. Configure antes do Sprint 2:

```python
# app/core/database.py (verificar se já existe)
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def get_checkpointer():
    return AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL)
```

### 0B.5 Celery Worker + Beat Schedule

O AutomationScheduler (10 jobs) roda via Celery. Configure antes do Sprint 1:

```bash
# Worker (processar tarefas)
celery -A app.core.celery_app worker --loglevel=info

# Beat scheduler (disparar jobs agendados)
celery -A app.core.celery_app beat --loglevel=info
```

**Jobs que rodam automaticamente (configurados na LIA):**
- `check_inactive_candidates` — a cada 1h
- `send_interview_reminders` — a cada 15min
- `auto_complete_screenings` — a cada 1h
- `run_lgpd_cleanup` — diário 02:00
- `drift-run-batch-daily` — diário 06:00 (Brasília)

### 0B.6 Verificação de Saúde Pré-Sprint

```bash
# Checar se tudo está up
curl http://localhost:8000/health

# Checar conectividade dos serviços
python -c "
from app.core.config import settings
print('DB:', settings.DATABASE_URL[:20])
print('Redis:', settings.REDIS_URL)
print('LLM:', 'ok' if settings.ANTHROPIC_API_KEY else 'MISSING')
"
```

---

## 1. RESUMO EXECUTIVO

O roadmap Alpha 1 define 10 passos (Login → Editar Vaga → Roteiro WSI → Buscar Candidatos → Gate 1 → Contato Email → Follow-up → Triagem WSI → Gate 2 → Agendamento/Feedback) que requerem **9 agentes/serviços de IA** referenciados explicitamente no fluxo (Ag.0→Ag.8). Este diagnóstico cruza cada agente com o que já existe no V5 e na LIA, identificando gaps, dependências e infraestrutura necessária.

### Diferenças Críticas Alpha 1 vs MVP Original

| Aspecto | MVP Original (Jan/2026) | Alpha 1 (Mar/2026) |
|---------|------------------------|---------------------|
| Criação de vaga | Wizard conversacional (criar do zero) | Editar vaga importada do ATS |
| Canal de contato | WhatsApp primário | **Email primário** (WhatsApp secundário) |
| Canal de triagem | WhatsApp WSI | **Chat Web** (primário) + WhatsApp (secundário) |
| Follow-up | Não especificado | **7 dias automático** (24h entre re-envios) |
| Triagem abandonada | Não especificado | **Timeout 48h** + 2 lembretes + alerta consultor |
| Feedback pós-triagem | Implícito | **Ag.4 EntrevistadorWSI** agradece + feedback + próximos passos |
| Integração ATS | Desejável, não bloqueante | **Premissa** (vagas importadas, Ag.8 sync) |
| Inscrição web | Via link WhatsApp | **Bypass Gate 1** → triagem automática |

---

## 2. FLUXO ALPHA 1 — VISÃO GERAL E DEPENDÊNCIAS ENTRE AGENTES

> **Por que esta seção está no início:** O fluxo é a "planta da casa" — mostra o que acontece em cada passo e quais agentes participam. Leia isto primeiro para entender o contexto dos agentes detalhados depois.
>
> **Convenção:** Cada linha mostra o componente LIA e, entre parênteses, o equivalente V5 quando existe. Itens marcados com ⚠️ foram reclassificados durante o diagnóstico (ver seção 4 para detalhes).

### 2.1 Fluxo Passo-a-Passo com Agentes e Dependências

```
Passo 1 (Login)
    └→ Sem agente IA

Passo 2 (Editar Vaga)
    └→ Ag.8 IntegradorATS ⚠️ SERVIÇO REST no Alpha 1
    │   LIA: ats_integration_react_agent.py | V5: SourcingAPIClient + 67 YAMLs
    │   ──→ importa vaga do ATS externo
    └→ Ag.1 JD Generator
        LIA: wizard_react_agent.py + job_wizard_graph.py | V5: wizard_react_agent.py + jd_generator_service.py
        ──→ gera/ajusta JD com LLM + FairnessGuard

Passo 3 (Configurar Roteiro WSI)
    └→ Ag.4+5 WSI Interview Graph (Ag.5 são nós do mesmo grafo, não agente separado)
        LIA: wsi_interview_graph.py | V5: InterviewGraph (4 nós, sem WSI)
        ──→ gera perguntas WSI baseadas na JD

Passo 4 (Buscar Candidatos)
    └→ Ag.2 SourcingAgent
    │   LIA: sourcing_react_agent.py (14 tools) | V5: MultiAgentOrchestrator (6 sub-agents)
    │   ──→ busca em ES + PGVector + WRF + Pearch
    └→ Ag.3 TriagemCurricular
    │   LIA: pipeline_react_agent.py (13 tools) | V5: ❌ sem agente dedicado (scoring parcial em evaluation/evaluate_response_node — rubrica simples, sem matching CV×JD)
    │   ──→ score de matching CV × JD
    └→ Ag.4+5 WSI
        LIA: wsi_interview_graph.py | V5: evaluation domain (scoring rubrica)
        ──→ ranking preliminar

Passo 5 (Gate 1 — Aprovação/Rejeição)
    └→ Ag.9 PipelineTransition
    │   LIA: pipeline_transition_agent.py (20 tools + HITL) | V5: pipeline_transition_agent.py
    │   ──→ HITL: consultor aprova/rejeita candidatos
    └→ Ag.7 Communication ⚠️ RECLASSIFICADO (era "AnalistaFeedback" no roadmap — é serviço)
    │   LIA: communication_react_agent.py (5 tools) | V5: communication_react_agent.py + email_service.py
    │   ──→ feedback para reprovados via PersonalizedFeedbackService
    └→ Ag.8 IntegradorATS ⚠️ SERVIÇO REST
        LIA: ats_sync_service.py | V5: SourcingAPIClient
        ──→ sync status para ATS

Passo 6 (Contato Email)
    └→ Ag.0 Orchestrator
    │   LIA: main_orchestrator.py + cascaded_router.py | V5: DomainOrchestrator (2 domínios)
    │   ──→ dispara contato via Communication
    └→ Ag.7 Communication
        LIA: communication_react_agent.py + email_service.py | V5: email_service.py
        ──→ envia email com link para triagem

Passo 6B (Follow-up 7 dias)
    └→ Automation infra
    │   LIA: automation_scheduler.py (10 jobs) | V5: ❌ sem scheduler (follow-up seria manual ou via cron externo)
    │   ──→ re-envio a cada 24h por 7 dias
    └→ Ag.7 Communication
        LIA: teams_service.py | V5: ❌ sem Teams (V5 só tem email_service.py — notificação interna não coberta)
        ──→ notificação Teams se sem resposta

Passo 7 (Triagem WSI — Chat Web)
    └→ Ag.0 Orchestrator
    │   LIA: main_orchestrator.py | V5: DomainOrchestrator
    │   ──→ roteia candidato para WSI graph
    └→ Ag.4+5 WSI Interview Graph
        LIA: wsi_interview_graph.py (~9 nós) | V5: InterviewGraph (4 nós)
        ──→ conduz entrevista + calcula score

Passo 7A (Triagem Abandonada)
    └→ Automation infra
        LIA: automation_scheduler.py + stage_automation_engine.py | V5: ❌ sem scheduler nem engine de automação (timeout/lembretes seriam manuais)
        ──→ timeout 48h + 2 lembretes + alerta Teams

Passo 7B (Feedback pós-triagem)
    └→ Ag.4+5 WSI
        LIA: wsi_interview_graph.py (nó generate_feedback) | V5: ⚠️ craft_message_node gera mensagem genérica (sem feedback estruturado WSI, sem próximos passos)
        ──→ agradece + feedback + próximos passos

Passo 8 (Gate 2 — Aprovação Final)
    └→ Ag.9 PipelineTransition
    │   LIA: pipeline_transition_agent.py | V5: pipeline_transition_agent.py
    │   ──→ HITL: consultor decide finalistas
    └→ Ag.7 Communication
    │   LIA: communication_react_agent.py | V5: communication_react_agent.py
    │   ──→ feedback para reprovados
    └→ Ag.8 IntegradorATS ⚠️ SERVIÇO REST
        LIA: ats_sync_service.py | V5: SourcingAPIClient
        ──→ sync final para ATS

Passo 9A (Agendar Entrevista)
    └→ Ag.6 SchedulingAgent
        LIA: interview_graph.py (6 nós) | V5: ❌ sem agendamento (V5 não tem scheduling — seria manual ou via ATS externo)
        ──→ calendário + Zoom/Teams/Meet + convites

Passo 9B (Enviar Feedback Final)
    └→ Ag.7 Communication ⚠️ era "AnalistaFeedback" no roadmap
        LIA: communication_react_agent.py + personalized_feedback_service.py | V5: ⚠️ email_service.py envia email básico (sem personalização LLM, sem diferenciação por Gate)
        ──→ feedback construtivo para não-finalistas
```

### 2.2 Mapa Visual de Dependências

> **Legenda:** ⚡ = agente ReAct/Graph real | 🔧 = serviço (reclassificado do roadmap)
> Cada nó mostra: Nome (LIA) | V5 equivalente

```
    🔧 Ag.8 (ATS Service)              ⚡ Ag.1 (JD Generator)           ⚡ Ag.4+5 (WSI Graph)
    LIA: ats_sync_service.py            LIA: wizard_react_agent.py       LIA: wsi_interview_graph.py
    V5:  SourcingAPIClient + 67 YAMLs   V5:  wizard_react_agent.py       V5:  InterviewGraph (4 nós)
         │                                   │                                │
         │                                   ▼                                ▼
         │                              ⚡ Ag.2 (Sourcing)           ──→ ⚡ Ag.3 (Triagem CV)
         │                              LIA: sourcing_react_agent.py     LIA: pipeline_react_agent.py
         │                              V5:  MultiAgentOrchestrator      V5:  ❌ não existe
         │                                                                    │
         ▼                                                                    ▼
    ⚡ Ag.9 (Pipeline)         ◄──── Gate 1 ◄────                   ⚡ Ag.0 (Orchestrator)
    LIA: pipeline_transition_agent.py                                LIA: main_orchestrator.py
    V5:  pipeline_transition_agent.py                                V5:  DomainOrchestrator (2 dom.)
         │                                                                    │
         ▼                                                                    ▼
    ⚡ Ag.7 (Communication)         ──→ ⚡ Ag.4+5 (WSI entrevista)      ──→ Gate 2
    LIA: communication_react_agent.py   LIA: wsi_interview_graph.py
    V5:  communication_react_agent.py   V5:  InterviewGraph (4 nós)
    ⚠️ absorve "AnalistaFeedback"                                              │
         │                                                                    ▼
         ▼                                                              ⚡ Ag.0 (Orchestrator)
    ⚡ Ag.6 (Scheduling)        ◄──── Ag.9 (Pipeline) ◄────
    LIA: interview_graph.py (6 nós)
    V5:  ❌ não existe
```

---

## 3. MAPEAMENTO DOS AGENTES — ALPHA 1 vs LIA vs V5

### 3.1 Agentes Alpha 1 com Referência Cruzada LIA ↔ V5

> **Nota:**
> - **Agente Roadmap (Ag.X)** = referência do nosso roadmap Alpha 1
> - **Agente LIA** = arquivo no nosso codebase (`lia-agent-system/app/domains/...`)
> - **V5 Correspondente** = arquivo no codebase V5 (`src/domains/...`)
> - **Gap V5** = o que o V5 NÃO tem que a LIA tem (e que precisamos para Alpha 1)

| # | Agente Roadmap | Agente LIA | V5 Correspondente | Gap V5 (o que V5 não tem) | Passos | Catálogo |
|---|----------------|------------|-------------------|--------------------------|:------:|:--------:|
| Ag.0 | **Orchestrator** | `main_orchestrator.py` + `cascaded_router.py` | `orchestrator/main_orchestrator.py` + `cascaded_router.py` | V5 tem base. Gap: CascadedRouter Tier 5 (Haiku→Sonnet→Opus), PolicyEngine, TaskPlanner multi-step | 5, 6, 7 | 14.1 |
| Ag.1 | **JD Generator** | `wizard_react_agent.py` + `job_wizard_graph.py` | `job_management/wizard_react_agent.py` + `jd_generator_service.py` | V5 tem base. Gap: FairnessGuard no JD, modo "editar vaga importada" (V5 só cria do zero) | 3 | 14.2 |
| Ag.2 | **SourcingAgent** | `sourcing_react_agent.py` (14 tools) | `sourcing/sourcing_react_agent.py` + `wrf_service.py` | V5 tem 6 sub-agents. Gap: WRF completo, LearningLoop (like/dislike), busca por JD, boolean search | 4 | 14.3 |
| Ag.3 | **TriagemCurricular** | `pipeline_react_agent.py` (13 tools) | `cv_screening/pipeline_react_agent.py` + `cv_scoring_service.py` | V5 tem scoring básico. Gap: rubric dinâmica, eligibility rules engine, PII masking no CV | 4 | 14.4 |
| Ag.4+5 | **WSI Interview** ⚠️ Ag.5 reclassificado: são nós do grafo, não agente separado | `wsi_interview_graph.py` (6 nós) | `cv_screening/wsi_interview_graph.py` + `wsi_service.py` | V5 tem graph base. Gap: voice orchestrator, 7-block WSI scoring, PromptInjectionGuard, feedback diferenciado | 3, 7 | 14.5 |
| Ag.6 | **Scheduling** | `interview_graph.py` (6 nós) | `interview_scheduling/interview_graph.py` + `calendar_service.py` | V5 tem graph. Gap: zero-touch scheduling, integração Zoom/Teams/Meet, conflito de agenda | 9A | 14.6 |
| Ag.7 | **Communication** ⚠️ reclassificado: era "AnalistaFeedback" no roadmap — feedback é serviço deste agente | `communication_react_agent.py` (5 tools) | `communication/communication_react_agent.py` + `email_service.py` | V5 tem agent. Gap: WhatsApp adapter, Teams notifications, email tracking pixel, template engine | 5-9B | 14.7 |
| Ag.8 | **IntegradorATS** ⚠️ serviço REST no Alpha 1 (agente ReAct pós-Alpha) | `ats_integration_react_agent.py` (5 tools) | `ats_integration/ats_integration_react_agent.py` + `ats_sync_service.py` | V5 tem agent + 5 clientes ATS. Gap: sync bidirecional real-time, webhook listeners, field mapping config | 2, 5, 8 | 14.8 |
| **Ag.9** | **PipelineTransition** | `pipeline_transition_agent.py` (20 tools + HITL) | `pipeline/pipeline_transition_agent.py` | V5 tem agent. Gap: StageAutomationEngine, HITL approval flow, bypass Gate 1 (inscrição web) | 5, 8 | 14.9 |
| **Ag.10** | **HiringPolicy** ⚠️ reclassificado: entra como serviço de políticas (4 tools), não como agente conversacional | `policy_react_agent.py` (4 de 13 tools) | `hiring_policy/policy_react_agent.py` | V5 tem agent. Gap: compliance rules engine, diversity scoring, industry defaults | config | 14.10 |

### 3.2 Agentes LIA que NÃO entram no Alpha 1

| Agente LIA | V5 Correspondente | Gap V5 | Por que não entra | Prioridade | Catálogo |
|------------|-------------------|--------|-------------------|:----------:|:--------:|
| **Kanban Agent** (22 tools) | `recruiter_assistant/kanban_react_agent.py` | V5 tem. Gap: drag-drop pipeline, batch operations | Alpha 1 foca no fluxo, não no dashboard | P2 | 14.11 |
| **Talent Agent** (12 tools) | `recruiter_assistant/talent_react_agent.py` | V5 tem. Gap: proactive recommendations, market insights | Recomendações consultivas — nice-to-have | P2 | 14.12 |
| **Analytics Agent** (19 tools) | `analytics/analytics_react_agent.py` | V5 tem. Gap: real-time dashboards, funnel metrics | Dashboards de performance — pós-Alpha 1 | P2 | 14.13 |
| **Automation Agent** (6 tools + 10 jobs) | `automation/automation_react_agent.py` | V5 tem. Gap: visual rule builder, DLQ management | Agente conversacional não entra; infra roda | P1 | 14.14 |
| **Jobs Management Agent** (—) | `jobs_mgmt/jobs_mgmt_react_agent.py` | V5 tem. Gap: portfólio de vagas inteligente | Gerencia listagem/filtros/status de vagas | P2 | 14.15 |

> **Atualizado v5.0:** Analytics corrigido de 6→19 tools. Jobs Management Agent adicionado (ver seção 14.15).
>
> **Importante:**
> - O **Hiring Policy** entra no Alpha 1 como **serviço de políticas** (4 tools), não como agente conversacional (ver seção 14.10). O agente conversacional completo (13 tools + WebSocket) é pós-Alpha.
> - O **Automation Agent** como agente conversacional não entra no Alpha 1, mas seus **10 jobs agendados** e **8 triggers de evento** rodam como infraestrutura em todos os cenários (ver seção 14.14).

---

## 4. DIAGNÓSTICO POR AGENTE — CRUZAMENTO V5 × LIA × ALPHA 1

> **⚠️ RECLASSIFICAÇÕES:** A numeração Ag.0 a Ag.10 vem do roadmap Alpha 1 original. Durante o diagnóstico, 4 itens foram reclassificados:
>
> | Roadmap Original | Reclassificação | Motivo |
> |-----------------|-----------------|--------|
> | Ag.5 — AvaliadorWSI | **Nós do WSIInterviewGraph (Ag.4)** | São nós `score_response` + `generate_feedback` do mesmo LangGraph, não agente separado. Não existe como agente em nenhum codebase. |
> | Ag.7 — AnalistaFeedback | **Serviço do CommunicationReActAgent** | Não existe como agente em nenhum codebase. É funcionalidade coberta por `PersonalizedFeedbackService` + templates, acionada pelo CommunicationReActAgent (14.7). |
> | Ag.8 — IntegradorATS | **Serviço REST no Alpha 1** | Existe como ReActAgent na LIA, mas CRUD bidirecional não precisa de raciocínio autônomo. Alpha 1 usa como serviço REST. |
> | Ag.10 — HiringPolicy | **Serviço de políticas no Alpha 1 (4 tools)** | Agente conversacional completo (13 tools) é pós-Alpha. Alpha 1 usa 4 tools como serviço: `get_current_policy`, `save_policy_block`, `apply_industry_defaults`, `validate_policy_compliance`. Triagem (Ag.3) e Gates (Ag.9) dependem de políticas configuradas — hardcodar defaults é frágil e não escala. |
>
> Os blocos abaixo mantêm a numeração original para rastreabilidade, mas com avisos de reclassificação onde aplicável.

---

### 4.1 Ag.0 — ORCHESTRATOR

**Função Alpha 1:** Coordenação geral do fluxo, disparo de contato (passo 6), coordenação da triagem WSI (passo 7).

#### Estado no V5 (GitHub)
- **Existe:** `src/domains/orchestrator.py` — `DomainOrchestrator`
- **Padrão:** Orquestrador simples com `DomainRegistry` + `DomainWorkflow`
- **Limitações V5:**
  - Só orquestra 2 domínios: `sourced_profile_sourcing` e `evaluation`
  - Sem cascata de roteamento (sem tiers)
  - Sem suporte a pending actions (multi-turn)
  - Sem HITL (Human-in-the-Loop)
  - Sem integração com canais (email/WhatsApp/chat web)
  - Sem memória cross-sessão

#### Estado na LIA (Referência)
- **Existe:** `app/orchestrator/main_orchestrator.py` — `MainOrchestrator`
- **Padrão:** 3-Tier CascadedRouter (T1: Cache → T2: FastRouter regex → T3: LLM Few-shot)
- **Capacidades LIA:**
  - Fase 0: PendingActions (multi-turn confirmations)
  - Fase 1: ActionExecutor (intents fechados)
  - Fase 2: Roteamento para 11 agentes via registry
  - Memória de sessão + cross-sessão + long-term
  - DomainWorkflows com transições inteligentes

#### Gap Analysis
| Capacidade | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| Roteamento para múltiplos agentes | ⚠️ 2 domínios | ✅ 11+ domínios | ✅ 9 agentes | 🔴 CRÍTICO |
| Cascata de roteamento (Tiers) | ❌ | ✅ 6 tiers (memory→redis→vector→fast→LLM→clarification) | ✅ | 🔴 CRÍTICO |
| PendingActions (multi-turn) | ❌ | ✅ | ✅ Gates 1/2 | 🔴 CRÍTICO |
| HITL (Human-in-the-Loop) | ❌ | ✅ interrupt_before | ✅ Gates | 🔴 CRÍTICO |
| Disparo de contato (email) | ❌ | ⚠️ via CommunicationAgent | ✅ | 🟡 ALTO |
| Coordenação multi-agente WSI | ❌ | ✅ Graph + ReAct | ✅ Ag.4+Ag.5 | 🟡 ALTO |
| Token Budget | ❌ | ✅ REACT_TOKEN_BUDGET | ⚠️ Desejável | 🟢 BAIXO |

**Veredicto:** O Orchestrator V5 é insuficiente. Precisa ser reconstruído seguindo padrão LIA com CascadedRouter.

---

### 4.2 Ag.2 — SOURCING AGENT

**Função Alpha 1:** Busca de candidatos no Funil de Talentos (banco interno + Pearch). 5 modos de busca, filtros avançados MAP-003.

#### Estado no V5 (GitHub)
- **Existe:** `src/domains/sourced_profile_sourcing/` — domínio completo e mais maduro do V5
- **Padrão:** Multi-Agent interno (6 sub-agentes: SearchAgent, DetailAgent, ComparisonAgent, AnalyticsAgent, ReportAgent, ActionAgent)
- **Orquestrador:** `MultiAgentOrchestrator` com `RouterAgent` + `PlannerAgent`
- **Capacidades V5:**
  - ✅ SmartExtractor (extrai skills, companies, locations via LLM)
  - ✅ FairnessGuard (validação de viés em buscas)
  - ✅ FactChecker (verificação de respostas)
  - ✅ Cache (StatsManager)
  - ✅ Prompt Builder dinâmico
  - ⚠️ Busca via API REST para ATS externo (sourcing domain)
  - ✅ PGVector (busca semântica via `embedding_service.py` + pgvector dep)
  - ✅ RAG Service híbrido (pgvector cosine + pg_trgm fulltext) — 391 linhas
  - ❌ Sem Elasticsearch (usa pg_trgm como fulltext)
  - ❌ Sem WRF (Weighted Rank Fusion) — fusão ad-hoc no RAG
  - ❌ Sem integração Pearch AI
  - ❌ Sem Like/Dislike feedback loop

#### Estado na LIA (Referência)
- **Existe:** `app/domains/sourcing/agents/sourcing_react_agent.py` — SourcingReActAgent
- **Padrão:** ReAct (4 arquivos) + 14 tools
- **Capacidades LIA:**
  - ✅ Busca semântica (PGVector + embeddings Gemini)
  - ✅ Elasticsearch integrado
  - ✅ WRF (Weighted Rank Fusion)
  - ✅ SemanticSearch service
  - ✅ EmbeddingService
  - ✅ LearningLoop (preferências aprendidas)
  - ✅ Integração Pearch AI (planejada)
  - ✅ FairnessGuard 3 camadas
  - ✅ Like/Dislike via LearningLoop

#### Gap Analysis
| Capacidade | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| Busca por skills/filtros | ✅ via API | ✅ local + API | ✅ | 🟢 V5 tem |
| SmartExtractor (LLM → params) | ✅ | ✅ | ✅ | 🟢 V5 tem |
| FairnessGuard | ✅ básico | ✅ 3 camadas | ✅ | 🟡 V5 básico |
| Busca semântica PGVector | ✅ `embedding_service.py` + pgvector dep | ✅ `embedding_service.py` + `pgv_analyzer.py` | ✅ MAP-002 | 🟡 ALTO (ambos têm, unificar) |
| Busca fulltext | ✅ pg_trgm (no RAG) | ✅ tsvector + SearchBackend abstração | ✅ | 🟡 ALTO (LIA mais maduro) |
| Elasticsearch | ❌ (usa pg_trgm) | ✅ SearchBackend com seletor ES/PG via env | ✅ para >500k docs | 🟡 ALTO (LIA tem, integrar) |
| Busca Híbrida (semantic+text) | ✅ `rag_service.py` (cosine + pg_trgm + reranking) | ✅ `hybrid_search_service.py` (tsvector + pgvector, alpha blend) | ✅ | 🟡 ALTO (ambos têm, LIA mais completo) |
| WRF (Weighted Rank Fusion) | ❌ (fusão ad-hoc no RAG) | ✅ `wrf_service.py` + `wrf_dynamic_k_service.py` | ✅ | 🟡 ALTO (LIA tem) |
| ES Score Drop + PGV Gap Analyzer | ❌ | ✅ `es_score_drop_analyzer.py` + `pgv_gap_analyzer.py` | ✅ | 🟡 ALTO (LIA tem) |
| Pre-WRF Filter Orchestrator | ❌ | ✅ `pre_wrf_filter_service.py` (orquestra ES+PGV→WRF) | ✅ | 🟡 ALTO (LIA tem) |
| RAG Pipeline | ✅ `rag_service.py` (391 linhas, híbrido) | ✅ `rag_pipeline_service.py` (pgvector + BM25 + FairnessGuard) | ✅ | 🟡 ALTO (ambos têm) |
| Modos busca (5: IA/Boolean/Similar/JD/Archetypes) | ⚠️ 1-2 modos (search + semantic) | ⚠️ 2-3 modos | ✅ 5 modos | 🟡 ALTO |
| Pearch AI integração | ❌ | ✅ `pearch_service.py` | ✅ | 🟡 ALTO (integrar) |
| Apify (emails + enriquecimento) | ❌ | ✅ `apify_service.py` + `apify_mcp_client.py` | ✅ | 🟡 ALTO (integrar) |
| Like/Dislike feedback loop | ❌ | ✅ `learning_loop_service.py` + `feedback_learning_service.py` | ✅ MAP-012 | 🟡 ALTO |
| Perfil Similar (busca por referência) | ❌ | ⚠️ via job_embedding semantic search | ✅ | 🟡 ALTO |

**Veredicto (REVISADO):** Tanto V5 quanto LIA têm busca semântica PGVector + busca híbrida. V5 tem RAG service funcional (391 linhas, pgvector cosine + pg_trgm). LIA tem arquitetura mais madura (WRF formal, analyzers, SearchBackend com abstração ES/PG, 221 serviços totais). O gap real é de **unificação e integração**, não de construção do zero. A camada de busca semântica **existe em ambos os codebases**.

---

### 4.3 Ag.3 — TRIAGEM CURRICULAR (CV Screening)

**Função Alpha 1:** Triagem de CV, análise pré-WSI, aparece no prompt expandido da LIA no Funil de Talentos (passo 4).

#### Estado no V5 (GitHub)
- **Não existe como agente separado.** A avaliação no V5 está no domínio `evaluation` mas focada em respostas de entrevista, não em análise de CV.

#### Estado na LIA (Referência)
- **Existe:** `app/domains/cv_screening/agents/pipeline_react_agent.py` — PipelineReActAgent
- **Padrão:** ReAct (4 arquivos) + 14 tools
- **Capacidades LIA:**
  - ✅ Triagem curricular com scoring
  - ✅ Matching candidato × vaga
  - ✅ Análise de gaps
  - ✅ Comparação de perfis
  - ✅ FairnessGuard na avaliação

#### Gap Analysis
| Capacidade | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| Análise de CV (scoring) | ❌ | ✅ PipelineReAct | ✅ | 🔴 CRÍTICO |
| Matching candidato × vaga | ❌ | ✅ | ✅ MAP-005 | 🔴 CRÍTICO |
| Comparação entre candidatos | ⚠️ ComparisonAgent | ✅ | ✅ | 🟡 V5 parcial |
| Análise de gaps | ❌ | ✅ | ✅ | 🟡 ALTO |

**Veredicto:** Precisa ser construído no V5. A LIA tem o PipelineReActAgent como referência completa.

---

### 4.4 Ag.4 — ENTREVISTADOR WSI

**Função Alpha 1:** (1) Gerar perguntas WSI a partir do JD (passo 3), (2) Conduzir triagem WSI via chat web/WhatsApp (passo 7), (3) Dar feedback pós-triagem (passo 7B).

#### Estado no V5 (GitHub)
- **Existe parcialmente:** `src/domains/evaluation/` — `EvaluationDomain` + `InterviewGraph`
- **LangGraph V5:** StateGraph com 4 nós: `classify_input` → `evaluate` → `decide_flow` → `craft_message`
- **Capacidades V5:**
  - ✅ Classificação de respostas (answer/question/off_topic/unclear/not_interested)
  - ✅ Scoring por rubrica (relevance, depth, clarity, examples)
  - ✅ Geração de mensagem ao candidato (acknowledgment + transition + next_content)
  - ✅ Decisão de fluxo (followup/next_question/end_interview/handle_question)
  - ✅ Checkpointing com MemorySaver
  - ⚠️ Usa Gemini (Google) como LLM, não Claude
  - ❌ Sem geração de perguntas WSI (recebe perguntas prontas)
  - ❌ Sem metodologia WSI formal (Bloom, Dreyfus, Big Five, CBI)
  - ❌ Sem scoring WSI (7 blocos)
  - ❌ Sem canal chat web ou WhatsApp (é API REST pura)
  - ❌ Sem feedback pós-triagem estruturado
  - ❌ Sem AuditCallback (SOX/BCB 498)
  - ❌ Sem FairnessGuard na avaliação
  - ❌ Sem timeout/abandono de triagem

#### Estado na LIA (Referência)
- **Existe:** `app/domains/cv_screening/agents/wsi_interview_graph.py` — WSIInterviewGraph
- **LangGraph LIA:** StateGraph com ~9 nós: `load_context` → `generate_question` → `validate_response` → `score_response` → `advance` → `generate_feedback`
- **Capacidades LIA:**
  - ✅ Geração de perguntas WSI (7 blocos)
  - ✅ Metodologia WSI (Bloom + Dreyfus + Big Five + CBI)
  - ✅ Scoring por resposta + score final composto
  - ✅ HITL: `interrupt_before=["lg_generate_feedback"]`
  - ✅ AuditCallback (SOX/BCB 498 compliance)
  - ✅ FairnessGuard na avaliação de respostas
  - ✅ FactChecker (valida respostas contra dados conhecidos)
  - ✅ PostgresSaver (checkpointing persistente)
  - ✅ Feedback pós-triagem com próximos passos

#### Gap Analysis
| Capacidade | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| LangGraph base (classificar/avaliar) | ✅ 4 nós | ✅ ~9 nós | ✅ | 🟢 V5 tem base |
| Geração de perguntas WSI (Blocos 2-5) | ❌ | ✅ | ✅ passo 3 | 🔴 CRÍTICO |
| Metodologia WSI (Bloom/Dreyfus/CBI) | ❌ | ✅ | ✅ | 🔴 CRÍTICO |
| Scoring WSI (7 blocos) | ❌ rubrica simples | ✅ WSI Score | ✅ | 🔴 CRÍTICO |
| Canal chat web | ❌ API REST | ⚠️ WebSocket | ✅ primário | 🔴 CRÍTICO |
| Canal WhatsApp | ❌ | ⚠️ adapter | ✅ secundário | 🟡 ALTO |
| Feedback pós-triagem (7B) | ❌ | ✅ | ✅ | 🟡 ALTO |
| Triagem abandonada (timeout 48h) | ❌ | ❌ | ✅ passo 7A | 🟡 ALTO (novo) |
| HITL (interrupt_before) | ❌ | ✅ | ✅ | 🟡 ALTO |
| AuditCallback | ❌ | ✅ | ✅ | 🟡 ALTO |
| FairnessGuard na avaliação | ❌ | ✅ | ✅ | 🟡 ALTO |
| PostgresSaver (checkpointing) | ⚠️ MemorySaver | ✅ PostgresSaver | ✅ | 🟡 ALTO |

**Veredicto:** V5 tem a base do LangGraph de avaliação, mas falta a camada WSI completa. Precisa ser enriquecido com a metodologia da LIA, geração de perguntas, e canais web/WhatsApp.

---

### 4.5 Ag.5 — AVALIADOR WSI ⚠️ RECLASSIFICADO → nós do WSIInterviewGraph (Ag.4)

> **⚠️ RECLASSIFICAÇÃO:** O roadmap Alpha 1 listou "AvaliadorWSI" como agente separado (Ag.5), mas isto NÃO é um agente — são **nós do mesmo LangGraph** que o Ag.4 (WSIInterviewGraph). Especificamente, os nós `score_response` e `generate_feedback` do grafo. Não existe como agente separado em nenhum codebase (LIA nem V5). A gap analysis abaixo documenta o que esses nós de scoring precisam para funcionar.

**Função real:** Nós de avaliação dentro do WSIInterviewGraph — calcula score WSI e gera parecer.

#### Estado no V5 (GitHub)
- **Parcialmente no evaluation:** O `evaluate_response_node` faz scoring por rubrica (relevance, depth, clarity, examples), mas sem metodologia WSI.
- **Não é agente separado** — é nó do InterviewGraph.

#### Estado na LIA (Referência)
- **Integrado no WSIInterviewGraph:** Nós `score_response` e `generate_feedback` do grafo.
- **Scoring WSI:** Fórmula composta com pesos por bloco (técnico, comportamental, cultural).
- **Não é agente separado** — nunca foi implementado assim.

#### Gap Analysis (capacidades dos nós de scoring)
| Capacidade | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| Scoring por rubrica (básico) | ✅ | ✅ | ✅ base | 🟢 V5 tem |
| Score WSI (7 blocos + pesos) | ❌ | ✅ | ✅ | 🔴 CRÍTICO |
| Parecer textual para recrutador | ⚠️ feedback_for_recruiter | ✅ | ✅ | 🟡 ALTO |
| Análise comparativa de candidatos | ⚠️ ComparisonAgent | ✅ | ✅ passo 4 | 🟡 V5 parcial |
| Ranking de candidatos por score | ⚠️ AnalyticsAgent | ✅ | ✅ passo 4 | 🟡 V5 parcial |
| BiasAudit (Four-Fifths Rule) | ❌ | ✅ | ✅ | 🟡 ALTO |

**Veredicto:** NÃO é agente separado. São nós do WSIInterviewGraph (Ag.4). V5 tem scoring básico por rubrica que precisa ser estendido com a metodologia WSI de 7 blocos da LIA. Ver bloco **14.5** para o componente técnico real.

---

### 4.6 Ag.6 — SCHEDULING AGENT

**Função Alpha 1:** Agendamento de entrevista para aprovados no Gate 2 (passo 9A). Email + WhatsApp ao candidato com link de reunião.

#### Estado no V5 (GitHub)
- **Não existe.** Nenhum código de agendamento encontrado.

#### Estado na LIA (Referência)
- **Existe:** `app/domains/interview_scheduling/agents/interview_graph.py` — InterviewGraph
- **LangGraph LIA:** StateGraph com 6 nós: `loader` → `collector` → `router` → `validator` → `executor` → `response`
- **Capacidades LIA:**
  - ✅ Coleta conversacional de dados (data, hora, tipo)
  - ✅ Validação de disponibilidade
  - ✅ Integração com calendário (Microsoft Graph / Google Calendar)
  - ✅ Geração de link de reunião (Zoom/Teams/Meet)

#### Gap Analysis
| Capacidade | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| LangGraph de agendamento | ❌ | ✅ 6 nós | ✅ | 🔴 CRÍTICO |
| Integração calendário | ❌ | ✅ Microsoft Graph | ✅ | 🔴 CRÍTICO |
| Link de reunião | ❌ | ✅ Zoom/Teams/Meet | ✅ | 🔴 CRÍTICO |
| Notificação email + WhatsApp | ❌ | ⚠️ via Communication | ✅ | 🟡 ALTO |
| Alerta consultor se sem horário | ❌ | ❌ | ✅ Alpha 1 | 🟡 ALTO (novo) |

**Veredicto:** Precisa ser construído do zero no V5. LIA tem a referência completa.

---

### 4.7 Ag.7 — ANALISTA FEEDBACK ⚠️ RECLASSIFICADO → serviço do CommunicationReActAgent

> **⚠️ RECLASSIFICAÇÃO:** O roadmap Alpha 1 listou "AnalistaFeedback" como agente autônomo (Ag.7), mas isto **nunca foi e nunca deveria ser um agente**. Não existe como agente em nenhum codebase (LIA nem V5). A funcionalidade de feedback é coberta por:
> - **CommunicationReActAgent** (14.7) — orquestra o envio (email, WhatsApp, Teams)
> - **`personalized_feedback_service.py`** — gera o conteúdo do feedback personalizado
> - **Templates configuráveis** — templates de comunicação por Gate/estágio
>
> O roadmap incorretamente promoveu um **serviço** a **agente**. Feedback não precisa de raciocínio autônomo (ReAct) — é geração de template + envio, acionado pelo Orchestrator.

**Função real:** Serviço de feedback acionado pelo CommunicationReActAgent — gera e envia feedback para candidatos reprovados em Gate 1, Gate 2 e decisão final.

#### Estado no V5 (GitHub)
- **Não existe como agente.** O V5 tem `email_service.py` como base de envio.

#### Estado na LIA (Referência)
- **Não existe como agente.** A funcionalidade está distribuída em:
  - `communication_react_agent.py` — tool `send_feedback` aciona o serviço
  - `personalized_feedback_service.py` — gera feedback personalizado por LLM
  - Templates de comunicação — diferenciados por Gate/estágio

#### Gap Analysis (capacidades do serviço de feedback)
| Capacidade | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| Geração de feedback personalizado | ❌ | ✅ `personalized_feedback_service.py` | ✅ | 🟡 ALTO (wiring) |
| Envio email feedback | ❌ | ✅ `email_service.py` + adapters | ✅ | 🟡 ALTO (wiring) |
| Envio WhatsApp feedback | ❌ | ⚠️ whatsapp_adapter | ⚠️ secundário | 🟢 BAIXO |
| Feedback diferenciado por Gate | ❌ | ⚠️ templates existem, lógica de Gate a conectar | ✅ (G1 vs G2) | 🟡 ALTO (wiring) |
| Integração com ATS (sync status) | ❌ | ✅ `ats_sync_service.py` | ✅ via Ag.8 | 🟡 ALTO (wiring) |

**Veredicto:** NÃO é agente. É serviço de feedback orquestrado pelo CommunicationReActAgent (14.7). A LIA já tem os componentes (`personalized_feedback_service.py`, templates, adapters) — o gap é de **wiring**, não de construção. Ver bloco **14.7** para o agente real que opera esta funcionalidade.

---

### 4.8 Ag.8 — INTEGRADOR ATS ⚠️ NOTA: serviço REST no Alpha 1

> **⚠️ RECLASSIFICAÇÃO PARCIAL:** Na LIA, existe como `ATSIntegrationReActAgent` (agente ReAct com 5 tools). Porém, para o Alpha 1, a integração ATS é **CRUD bidirecional** (importar vagas, exportar status/scores) que NÃO precisa de raciocínio autônomo ReAct. O Alpha 1 usa como **serviço REST** — `ats_sync_service.py` + clientes ATS (Gupy, Pandapé, Merge, StackOne). O agente conversacional fica para pós-Alpha.

**Função Alpha 1:** Sync bidirecional com ATS externo via serviço REST. Premissa do Alpha 1 (vagas importadas). Passos 2, 5, 8.

#### Estado no V5 (GitHub)
- **Parcialmente:** O V5 já se comunica com o ATS via `SourcingAPIClient` (REST), mas como consumidor, não como agente de integração bidirecional.
- `documentation/` contém YAMLs de 67+ endpoints da API do ATS.

#### Estado na LIA (Referência)
- **Existe como agente:** `app/domains/ats_integration/agents/ats_integration_react_agent.py` — ATSIntegrationReActAgent
- **Existe como serviço:** `app/services/ats_sync_service.py` + 5 clientes ATS
- **Alpha 1 usa o serviço**, não o agente conversacional

#### Gap Analysis
| Capacidade | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| Leitura de API ATS (GET) | ✅ SourcingAPIClient | ✅ | ✅ | 🟢 V5 tem |
| Documentação de endpoints YAML | ✅ 67+ endpoints | ✅ | ✅ | 🟢 V5 tem |
| Sync bidirecional (write back) | ⚠️ parcial | ✅ `ats_sync_service.py` + `update_candidate_status` | ✅ | 🟡 ALTO (integrar) |
| Importar vagas do ATS | ⚠️ parcial | ✅ | ✅ premissa | 🟡 ALTO (integrar) |
| Exportar status/scores para ATS | ❌ | ✅ `ats_sync_service.py` | ✅ passos 5,8 | 🟡 ALTO (integrar) |
| Mapeamento de campos ATS ↔ WeDo | ⚠️ | ✅ clientes Gupy/Pandapé/Merge | ✅ | 🟡 ALTO |
| Agente ReAct conversacional | ❌ | ✅ ATSIntegrationReAct | ❌ pós-Alpha | 🟢 pós-Alpha |

**Veredicto:** V5 tem boa base de consumo de API ATS (67+ docs YAML). Alpha 1 usa como **serviço REST** (`ats_sync_service.py` + clientes ATS) — não precisa de agente ReAct conversacional. O gap é de **wiring**: conectar write-back (exportar status/scores) e importação estruturada de vagas. Ver bloco **14.8** para o componente técnico.

---

### 4.9 JD GENERATOR SERVICE (não numerado como agente)

**Função Alpha 1:** Geração/ajuste de Job Description a partir de dados da vaga (passo 3). Serviço LLM, não agente autônomo.

#### Estado no V5 (GitHub)
- **Não existe.** Nenhum serviço de geração de JD encontrado.

#### Estado na LIA (Referência)
- **Existe:** Tool `generate_enriched_jd` no WizardAgent
- **Capacidades LIA:**
  - ✅ Geração de JD enriquecida com dados de mercado
  - ✅ Sugestões inteligentes (salary benchmark, skills)
  - ✅ FairnessGuard (JD sem viés)

#### Gap Analysis
| Capacidade | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| Geração de JD por LLM | ❌ | ✅ tool | ✅ | 🟡 ALTO |
| Ajuste de JD existente (ATS) | ❌ | ⚠️ | ✅ | 🟡 ALTO |
| FairnessGuard em JD | ❌ | ✅ | ✅ | 🟡 ALTO |
| Salary benchmark | ❌ | ✅ tool | ⚠️ desejável | 🟢 BAIXO |

**Veredicto:** Serviço LLM simples. Pode ser tool do Orchestrator ou endpoint dedicado.

---

## 5. INFRAESTRUTURA COMPARTILHADA — DIAGNÓSTICO

### 5.1 Camada de Compliance/Fairness

| Componente | V5 | LIA | Necessário Alpha 1 | Gap | Status Wiring |
|-----------|:--:|:---:|:------------------:|:---:|:-------------:|
| FairnessGuard (padrões discriminatórios) | ✅ básico (1 camada) | ✅ 3 camadas (Regex→Léxico→LLM) `fairness_guard.py` | ✅ screening + sourcing | 🟢 RESOLVIDO | ✅ **Wired (SEG-2)** — `sourcing_react_agent.py` + `pipeline_transition_agent.py` |
| FactChecker | ✅ básico (sourcing only) | ✅ granular `fact_checker.py` | ✅ WSI + sourcing | 🟡 ALTO | ⚠️ Parcial |
| BiasAudit (Four-Fifths Rule / NYC LL144) | ❌ | ✅ `bias_audit.py` + `bias_audit_snapshot.py` | ✅ baseline pré-go-live | 🟡 ALTO | ❌ Baseline não rodado |
| AuditCallback / Audit Service (SOX/BCB 498) | ❌ | ✅ `audit_service.py` + `audit_writer.py` + `audit_callback.py` | ✅ decisões Gate 1/2 | 🟢 RESOLVIDO | ✅ **Wired (SEG-5)** — pipeline HITL/transition/LangGraph + sourcing ReAct/LangGraph + HITL rejected |
| Guardrails em DB (por tenant) | ❌ | ✅ migration 020 + `guardrail_repository.py` | ✅ multi-tenant | 🟡 ALTO | ⚠️ DB ok, config parcial |
| PII Masking (LGPD Art. 46) | ❌ | ✅ `pii_masking.py` (global log filter) | ✅ todos logs | 🟢 RESOLVIDO | ✅ **Ativo (SEG-3A/3B)** — global log filter + Celery workers + strip antes do LLM em 4 callers |
| Prompt Injection Guard | ❌ | ✅ `prompt_injection.py` (177 linhas) | ✅ WSI + chat | 🟢 RESOLVIDO | ✅ **Wired (SEG-1)** — `wsi_interview_graph.validate_response` + `agent_chat_ws.py` |
| Consent Management (LGPD Art. 7) | ❌ | ✅ `consent_management.py` + modelos | ✅ antes de Gate 1 | 🟢 RESOLVIDO | ✅ **Validado (SEG-4)** — `ConsentCheckerService` em `wsi_interview_graph.load_context` (Gate 1 WSI) |
| DSR — Data Subject Requests (LGPD Art. 18) | ❌ | ✅ `data_subject_requests.py` (5 tipos) | ✅ workflow completo | 🟡 ALTO | ❌ NÃO testado e2e |
| LGPD Cleanup / Data Retention (Art. 16) | ❌ | ✅ `LgpdCleanupService` (90/180/365d) | ✅ retenção configurada | 🟡 ALTO | ❌ NÃO configurado p/ Alpha 1 |
| EU AI Act — FRIA (Art. 6 Annex III) | ❌ | ⚠️ Template existe | ✅ screening é high-risk | 🟡 ALTO | ❌ NÃO preenchido |
| PolicyEngine (governança de agentes) | ❌ | ✅ `policy_engine.py` | ✅ regras Alpha 1 | 🟡 ALTO | ❌ Sem policies Alpha 1 |
| Agent Monitoring (governance) | ❌ | ✅ `agent_monitoring_service.py` | ⚠️ desejável | 🟢 BAIXO | ⚠️ Parcial |

### 5.2 Camada de Inteligência/Aprendizado

| Componente | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| SmartExtractor (NL → params) | ✅ | ✅ | ✅ | 🟢 V5 tem |
| EmbeddingService | ✅ básico | ✅ Gemini text-embedding-004 | ✅ | 🟡 V5 básico |
| SemanticSearch | ❌ | ✅ | ✅ busca avançada | 🔴 CRÍTICO |
| RAG Service | ✅ busca híbrida (docs) | ✅ 3 fontes paralelas | ✅ | 🟢 V5 tem |
| LearningLoop (feedback implícito) | ❌ | ✅ captura silenciosa | ✅ Like/Dislike | 🟡 ALTO |
| AB Testing (prompts) | ❌ | ✅ | ⚠️ desejável | 🟢 BAIXO |
| RecruiterPersonalization | ❌ | ✅ após 10+ vagas | ⚠️ desejável | 🟢 BAIXO |
| FinetuningExport | ❌ | ✅ | ❌ não para Alpha 1 | — |

### 5.3 Camada de Comunicação/Canais

| Componente | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| Multi-channel service | ❌ | ✅ orchestrated | ✅ email+WhatsApp+web | 🔴 CRÍTICO |
| Email adapter | ❌ | ✅ | ✅ canal primário | 🔴 CRÍTICO |
| WhatsApp adapter | ❌ | ✅ | ✅ canal secundário | 🟡 ALTO |
| Chat Web (canal de triagem) | ❌ | ⚠️ WebSocket agent_chat_ws | ✅ canal primário triagem | 🔴 CRÍTICO |
| Follow-up automático (7 dias) | ❌ | ❌ | ✅ passo 6B | 🔴 CRÍTICO (novo) |
| Template management | ❌ | ⚠️ parcial | ✅ | 🟡 ALTO |
| Tracking de abertura/clique | ❌ | ❌ | ✅ passo 6B | 🟡 ALTO (novo) |
| Notificação Teams (consultor) | ❌ | ⚠️ teams_adapter | ✅ passos 7A, 9A | 🟡 ALTO |

### 5.4 Camada de Infraestrutura de Agentes

| Componente | V5 | LIA | Necessário Alpha 1 | Gap |
|-----------|:--:|:---:|:------------------:|:---:|
| BaseAgent interface | ⚠️ DomainPrompt | ✅ BaseAgent + AgentInput/Output | ✅ | 🟡 ALTO |
| EnhancedAgentMixin | ❌ | ✅ memory+autonomy+learning | ✅ | 🟡 ALTO |
| ReactAgentRegistry | ❌ | ✅ singleton 11 agentes | ✅ | 🟡 ALTO |
| LangGraphBase + checkpointer | ⚠️ MemorySaver | ✅ PostgresSaver | ✅ | 🟡 ALTO |
| 4-file pattern (agent scaffold) | ❌ | ✅ obrigatório | ✅ padronização | 🟡 ALTO |
| Tool Registry (YAML + runtime) | ✅ YAML per-endpoint | ✅ metadata.yaml + scope | ✅ | 🟢 V5 tem base |
| Scope Config (tool access control) | ❌ | ✅ 4 scopes | ✅ | 🟡 ALTO |
| Working Memory | ✅ MemoryService | ✅ 3 níveis | ✅ | 🟡 V5 básico |
| Long-term Memory | ❌ | ✅ agent_long_term_memory | ⚠️ desejável | 🟢 BAIXO |
| Circuit Breaker | ❌ | ✅ | ✅ APIs externas | 🟡 ALTO |
| Token Budget | ❌ | ✅ feature flag | ⚠️ desejável | 🟢 BAIXO |
| Observabilidade (LangSmith/Prometheus) | ❌ | ✅ 13+ métricas | ✅ | 🟡 ALTO |

---

## 6. ARQUITETURA RECOMENDADA — AGENTES ALPHA 1 (LIA vs V5)

Com base no diagnóstico, a arquitetura recomendada consolida os agentes referenciados no roadmap em **9 componentes técnicos** (alguns agentes são melhor implementados como nós de um mesmo grafo, e 2 serviços transversais foram identificados na revisão arquitetural):

| # | Componente Técnico | Tipo | Agentes/Função Alpha 1 | LIA Ref | Prioridade |
|---|-------------------|------|------------------------|---------|------------|
| 1 | **MainOrchestrator** | Orchestrator (3-Tier) | Ag.0 — coordenação geral | `main_orchestrator.py` + `cascaded_router.py` | P0 — Sprint 0 |
| 2 | **SourcingReActAgent** | ReAct (4 arquivos) | Ag.2 — busca candidatos | `sourcing_react_agent.py` | P0 — Sprint 1 |
| 3 | **CVScreeningReActAgent** | ReAct (4 arquivos) | Ag.3 — triagem CV + scoring | `pipeline_react_agent.py` | P1 — Sprint 1-2 |
| 4 | **WSIInterviewGraph** | LangGraph StateGraph | Ag.4+5 — entrevista + avaliação WSI | `wsi_interview_graph.py` | P0 — Sprint 2 |
| 5 | **SchedulingGraph** | LangGraph StateGraph | Ag.6 — agendamento de entrevista | `interview_graph.py` | P1 — Sprint 3 |
| 6 | **CommunicationService** | Serviço + Adapters | Ag.7 — email, WhatsApp, Teams, feedback | `communication_react_agent.py` | P0 — Sprint 1 |
| 7 | **ATSIntegrationService** | Serviço REST | Ag.8 — sync bidirecional com ATS | `ats_integration_react_agent.py` | P0 — Sprint 0 |
| 8 | **PipelineGateService** | Serviço | Ag.9 — estado Gate1/Gate2 + regras transição + auditoria + bypass web | `pipeline_transition_agent.py` + `stage_automation_engine.py` | P0 — Sprint 2 |
| 9 | **EventRetryOrchestrator** | Serviço | Infra — scheduler + idempotência + DLQ para follow-up/timeout/lembretes | `automation_scheduler.py` + `planned_task_service.py` | P1 — Sprint 1 |

**Justificativas de consolidação:**
- **Ag.4 + Ag.5 unificados:** Na LIA, o EntrevistadorWSI e AvaliadorWSI são nós do mesmo LangGraph (`wsi_interview_graph.py`). Separá-los em agentes distintos cria overhead desnecessário de coordenação. O grafo mantém ambas as funções em nós diferentes.
- **Ag.7 como serviço:** AnalistaFeedback não precisa de raciocínio autônomo (ReAct). É geração de templates + envio. Melhor como serviço consumido pelo Orchestrator/CommunicationService.
- **Ag.8 como serviço:** IntegradorATS é CRUD bidirecional. Não precisa de ReAct. O V5 já tem `SourcingAPIClient` como base.
- **JD Generator:** Absorvido como tool/serviço dentro do fluxo de edição de vaga.

### 6.2 Comparação Arquitetural LIA vs V5 — Diferenças Estruturais

| Dimensão | V5 (GitHub) | LIA (Referência) | Impacto Alpha 1 |
|----------|-------------|-------------------|------------------|
| **Padrão de Agente** | Misto (some ReAct, some API-first) | 4-file pattern obrigatório: `agent.py` + `tool_registry.py` + `system_prompt.py` + `domain.py` | Alpha 1 usa padrão LIA — V5 precisa ser adaptado |
| **Router/Orchestrator** | IntentAnalyzer + APIPlan + Execute (3 agents) | CascadedRouter Tier 5 (Haiku→Sonnet→Opus) + PolicyEngine + TaskPlanner | LIA é mais sofisticado — usar LIA |
| **Tool Registry** | YAML per-endpoint (`tools/*.yaml`) | `metadata.yaml` + runtime scope config (4 scopes: `recruiter`, `candidate`, `admin`, `system`) | LIA tem controle de acesso por scope — V5 não |
| **LangGraph** | `MemorySaver` (in-memory) | `PostgresSaver` (persistente) + checkpointer por tenant | Alpha 1 precisa PostgresSaver para sessões WSI |
| **Memory** | `MemoryService` (1 nível, Redis) | 3 níveis: working + episodic + long-term | LIA é mais completa |
| **Sourcing** | 6 sub-agents (search, detail, comparison, analytics, report, action) | 1 ReAct agent com 14 tools + WRF + LearningLoop | V5 fragmenta demais; LIA é mais coeso |
| **WSI** | Graph base com scoring por rubrica | Graph com 7-block WSI scoring + voice orchestrator + feedback diferenciado | LIA tem mais profundidade |
| **Communication** | Agent base com email | Agent com 5 tools + WhatsApp + Teams + template engine | V5 só tem email básico |
| **ATS** | Agent + 5 clientes (Gupy, PandaPé, Merge, StackOne, base) | Agent + mesmos 5 clientes + sync bidirecional + webhooks | Mesma base, LIA adiciona sync real-time |
| **Segurança** | Sem PII masking, sem PromptInjectionGuard | `pii_masking.py` + `prompt_injection.py` — **totalmente wired (SEG-1/SEG-3)** | ✅ **Resolvido:** PromptInjectionGuard em WSI+chat, PII masking global + Celery + strip antes do LLM |
| **Observabilidade** | Sem métricas dedicadas | 13+ métricas Prometheus + LangSmith tracing | V5 é cego; LIA tem infra |
| **Automação** | Sem scheduler dedicado | 10 jobs agendados + 8 triggers de evento + `StageAutomationEngine` | V5 não tem; LIA tem toda a infra |
| **Governança** | Sem FairnessGuard | FairnessGuard 3 camadas + Bias Audit + RedTeam | LIA tem, V5 não |

> **Conclusão:** A LIA é uma **evolução significativa do V5** com a mesma base de domínios mas infraestrutura de governança, segurança e automação muito mais madura. O V5 serve como **referência de domínio** (quais serviços existem) mas a arquitetura a seguir é a da LIA.

---

## 7. SERVIÇOS DE SUPORTE — GAPS OPERACIONAIS (INFRA LIA PARCIAL / V5 AUSENTE)

O Alpha 1 introduz funcionalidades que requerem integração operacional. Alguns têm infraestrutura na LIA (código existe, não está integrado no fluxo Alpha 1):

| Serviço | Referência Alpha 1 | Status V5 | Status LIA | Prioridade |
|---------|-------------------|:---------:|:----------:|:----------:|
| **Follow-up Scheduler** | Passo 6B (re-envio 24h × 7 dias) | ❌ | ⚠️ `automation_scheduler.py` (infra existe, regra de 7 dias não) | P1 |
| **Email Tracking** | Passo 6B (abertura/clique de email) | ❌ | ❌ | P1 |
| **Triagem Abandonada Monitor** | Passo 7A (timeout 48h + 2 lembretes) | ❌ | ⚠️ trigger `triagem_abandonada` existe em `communication_matrix.py` | P1 |
| **Chat Web Canal** | Passo 7 (link no email → chat web para triagem) | ❌ | ⚠️ WebSocket `agent_chat_ws.py` base | P0 |
| **Teams Notification** | Passos 7A, 9A (alertas ao consultor) | ❌ | ⚠️ `teams_adapter.py` + `teams.py` modelo | P1 |
| **Inscrição Web → Bypass Gate 1** | Passo 5 (inscritos via web pulam Gate 1) | ❌ | ❌ | P1 |

> **Nota de maturidade (revisão pós-architect review):** Vários componentes marcados acima como ⚠️ na LIA existem como código implementado mas não integrado operacionalmente no produto. O esforço principal é de **integração e configuração**, não de reconstrução.

---

## 8. TOOLS — RESUMO DE CONTAGEM POR AGENTE

> **Detalhe completo das tools** (nome, função, serviço que chama) está dentro de cada bloco de agente na **seção 14**. Esta seção é apenas um resumo de contagem.

| Agente (LIA) | Tools | Tipo | Seção 14 |
|-------------|:-----:|------|:--------:|
| MainOrchestrator (Ag.0) | 9 | Orchestrator | 14.1 |
| Job Wizard (Ag.1) | 9 | ReAct + Graph | 14.2 |
| Sourcing (Ag.2) | 14 | ReAct | 14.3 |
| CV Screening (Ag.3) | 13 | ReAct | 14.4 |
| WSI Interview (Ag.4+5) | 6 nós | StateGraph | 14.5 |
| Scheduling (Ag.6) | 6 nós | StateGraph | 14.6 |
| Communication (Ag.7) | 5 | ReAct | 14.7 |
| ATS Integration (Ag.8) | 5 | ReAct | 14.8 |
| Pipeline Transition (Ag.9) | 20 | ReAct + HITL | 14.9 |
| Hiring Policy (Ag.10) ⚠️ modo serviço | 4 (de 13) | ReAct (4 tools como serviço) | 14.10 |
| **Total Alpha 1** | **91** | | |
| Kanban | 22 | ReAct | 14.11 |
| Talent | 12 | ReAct | 14.12 |
| Analytics | 19 | ReAct | 14.13 |
| Automation | 6 | ReAct | 14.14 |
| Jobs Management | 14 | ReAct | 14.15 |
| **Total Geral (15 agentes)** | **164** (Alpha 1 usa 91) | | |

> **Atualizado v5.0:** Analytics corrigido de 6→19 tools (conforme `analytics_tool_registry.py`). Jobs Management Agent (`jobs_mgmt_react_agent.py`) adicionado como 15º agente — gerencia portfólio de vagas (listagem, filtros, status, duplicação). Escopos por chat: TALENT_FUNNEL filtra 20 tools, IN_JOB filtra 25 tools, GLOBAL filtra 2 tools (ver seção 13G).

---

## 9. LIBS E DEPENDÊNCIAS

### 9.1 Stack V5 Atual (requirements.txt)
```
langchain-core==0.3.29, langchain-google-genai==2.0.8, langgraph==0.2.58
google-generativeai==0.8.3, psycopg2-binary, pgvector, pika (RabbitMQ)
celery[redis], flask, gunicorn, streamlit
```

### 9.2 Stack LIA (referência)
```
libs/agents-core (monorepo UV): BaseAgent, LangGraphBase, ReactAgentRegistry, EnhancedAgentMixin
libs/audit: AuditCallback, AuditWriter, AuditStorage
libs/contexts: system prompts por domínio
libs/services: repositories compartilhados
libs/models: guardrails, modelos compartilhados
libs/config: settings, database, Redis
```

### 9.3 Libs Adicionais Necessárias para Alpha 1
| Lib/Pacote | Propósito | V5 tem | LIA tem |
|-----------|-----------|:------:|:-------:|
| `langchain-anthropic` | Claude como LLM primário | ❌ | ✅ |
| `langgraph-checkpoint-postgres` | Checkpointing persistente | ❌ | ✅ |
| `elasticsearch` | Busca full-text | ❌ | ✅ |
| `sendgrid` ou `boto3` (SES) | Email transacional | ❌ | ⚠️ |
| `twilio` ou `360dialog` | WhatsApp Business API | ❌ | ⚠️ |
| `msgraph-sdk` | Microsoft Graph (calendário) | ❌ | ✅ |
| `apify-client` | Web scraping/enriquecimento | ❌ | ❌ |
| `langsmith` | Observabilidade de agentes | ❌ | ✅ |
| `prometheus-client` | Métricas | ❌ | ✅ |

---

## 10. CONTAGEM DE GAPS

### Matriz de Maturidade por Componente (revisão completa pós-varredura expandida)

> **Nota:** Varredura expandida identificou que LIA tem **221 serviços** em `app/services/` e V5 tem **PGVector + RAG híbrido funcional** (391 linhas). Muitos gaps do diagnóstico inicial eram falsos positivos.
> 
> Níveis: **Absent** (não existe) → **Stub** (interface sem impl) → **Partial** (código existe, incompleto) → **Implemented** (funcional, não integrado no fluxo Alpha 1) → **Ready** (pronto para uso)

| Componente | V5 | LIA | Nível Real |
|-----------|:--:|:---:|:----------:|
| PGVector + Embeddings | ✅ Implemented (`embedding_service.py`, pgvector dep) | ✅ Implemented (`embedding_service.py`, `pgv_gap_analyzer.py`, migration 028) | **Ambos têm — unificar** |
| Busca Híbrida (semantic + text) | ✅ Implemented (`rag_service.py` 391 linhas, cosine + pg_trgm) | ✅ Implemented (`hybrid_search_service.py`, `rag_pipeline_service.py`, alpha blend) | **Ambos têm — LIA mais maduro** |
| Elasticsearch | ❌ Absent (usa pg_trgm) | ✅ Implemented (`search_service.py` SearchBackend abstração, seletor via env) | **LIA tem** |
| WRF + Dynamic K | ❌ Absent | ✅ Implemented (`wrf_service.py`, `wrf_dynamic_k_service.py`, `pre_wrf_filter_service.py`) | **LIA tem** |
| ES Score Drop + PGV Gap | ❌ Absent | ✅ Implemented (`es_score_drop_analyzer.py`, `pgv_gap_analyzer.py`) | **LIA tem** |
| WSI Question Service | ❌ Absent | ✅ Implemented (`wsi_question_service.py`, `wsi_question_generator.py`, `wsi_question_adjuster.py`, `wsi_deterministic_scorer.py`, `wsi_screening_pipeline.py`, `wsi_service.py`, `wsi_voice_orchestrator.py`) — **7 serviços** | **LIA tem (extenso)** |
| CV Parser + Scoring | ❌ Absent | ✅ Implemented (`cv_parser.py`, `cv_scoring_service.py`) | **LIA tem** |
| Pipeline State Machine | ❌ Absent | ✅ Implemented (`pipeline_service.py`, `pipeline_stage_service.py`, `pipeline_prediction_service.py`, `pipeline_velocity_service.py`) — **4 serviços** | **LIA tem** |
| HITL Service | ❌ Absent | ✅ Implemented (`hitl_service.py` — interrupt via LangGraph, Redis cache, DB persist, WS protocol) | **LIA tem** |
| Calendar/Scheduling | ❌ Absent | ✅ Implemented (`calendar_service.py`, `google_calendar_client.py`, `zero_touch_scheduling_service.py`) | **LIA tem** |
| Email Service | ❌ Absent | ✅ Implemented (`email_service.py`, `email_providers/` com Resend + SendGrid, `recruitment_email_templates.py`) | **LIA tem** |
| Teams Integration | ❌ Absent | ✅ Implemented (`teams_service.py`, `teams_bot.py`, `teams_auth.py`, `teams_simple.py`, `teams_recording_service.py`) — **5 serviços** | **LIA tem** |
| WhatsApp | ❌ Absent | ✅ Implemented (`whatsapp_service.py`, `whatsapp_meta_service.py`, `whatsapp_twilio_service.py`, `whatsapp_factory.py`) — **4 serviços** | **LIA tem** |
| ATS Integration | ⚠️ Partial (67 YAML docs, API client) | ✅ Implemented (`ats_sync_service.py`, `gupy_service.py`, `pandape_service.py`, `merge_ats_service.py`, `ats_clients/`) | **LIA tem** |
| Communication Matrix | ❌ Absent | ✅ Implemented (`communication_service.py`, `communication_dispatcher.py`, `communication_history_service.py`) | **LIA tem** |
| Token Budget | ❌ Absent | ✅ Implemented (`token_budget_service.py` — multi-tenant, Redis, planos starter/pro/business/enterprise) | **LIA tem** |
| Audit/Compliance | ❌ Absent | ✅ Implemented (`audit_service.py` → `shared/compliance/audit_service.py`) | **LIA tem** |
| Automation Scheduler | ❌ Absent | ✅ Implemented (`automation_scheduler.py`, `automation_service.py`, `automation_trigger_service.py`, `planned_task_service.py`, `stage_automation_engine.py`) — **5 serviços** | **LIA tem** |
| Pearch AI | ❌ Absent | ✅ Implemented (`pearch_service.py`) | **LIA tem** |
| Apify | ❌ Absent | ✅ Implemented (`apify_service.py`, `apify_mcp_client.py`) | **LIA tem** |
| RAG/SmartExtractor | ✅ Implemented (`rag_service.py`, `smart_extractor.py`) | ✅ Implemented (`rag_pipeline_service.py`, `semantic_search_service.py`) | **Ambos têm** |
| FairnessGuard | ✅ Partial (1 camada) | ✅ Implemented (3 camadas + `bias_audit_service.py`) | **LIA mais maduro** |
| Learning/Feedback | ❌ Absent | ✅ Implemented (`learning_loop_service.py`, `feedback_learning_service.py`, `learning_analytics_service.py`) | **LIA tem** |

### Por Severidade (revisão final — inclui governança, compliance e segurança)

> **Atualizado v3.0 (11/03/2026):** 5 gaps críticos de governança/compliance resolvidos pelos Sprints SEG-1 a SEG-5. Contagem ajustada de 55→50 gaps totais.

| Severidade | Qtd | Categoria | Gaps |
|-----------|:---:|-----------|------|
| 🔴 CRÍTICO | **3** | Funcionalidade | Email tracking pixel/clique, Inscrição web bypass Gate 1, Feedback diferenciado por Gate |
| ~~🔴 CRÍTICO~~ | ~~5~~ | ~~Segurança/LGPD/Governança~~ | ✅ **Resolvidos (SEG-1 a SEG-5):** PromptInjectionGuard wired; PII Masking global+Celery+LLM strip; FairnessGuard wired sourcing+pipeline; AuditService wired Gates; ConsentCheckerService Gate 1 WSI |
| 🟡 ALTO | **39** | Integração | Unificar PGVector V5+LIA, configurar WRF para Alpha 1, wiring WSI graph→chat web, follow-up 7 dias, adaptar scheduling graph, configurar pipeline state machine para Gates |
| | | Governança | Bias Audit baseline não estabelecido (infra `bias_audit.py` existe — precisa rodar baseline antes de go-live) |
| | | Governança | PolicyEngine não configurado para regras Alpha 1 (módulo `policy_engine.py` existe — configurar via HiringPolicyService Ag.10 modo serviço) |
| | | Legal | EU AI Act FRIA (Fundamental Rights Impact Assessment) não documentado para screening WSI (template existe — precisa ser preenchido) |
| | | Compliance | Circuit breakers não configurados para todos os LLM providers (infra existe — precisa wiring) |
| | | LGPD | Data retention policies (90/180/365 dias) não configuradas para Alpha 1 (`LgpdCleanupService` existe) |
| | | LGPD | DSR (Data Subject Requests) — workflow existe mas não testado end-to-end |
| 🟢 BAIXO | **8** | Desejável | AB Testing, RecruiterPersonalization, FinetuningExport, Long-term Memory refinement |
| **TOTAL** | **50** | | (revisado de 55→50 após resolução de 5 gaps críticos por SEG-1 a SEG-5) |

### Conclusão da Varredura Expandida (atualizado v5.0)
**O gap real do Alpha 1 é de ORQUESTRAÇÃO e WIRING — não de construção de serviços. Os gaps críticos de governança/compliance foram resolvidos nos Sprints SEG-1 a SEG-5.**

- A LIA tem ~497 arquivos Python na camada de IA e ~130 endpoints API
- **Governança/Compliance (atualizado v3.0):** Os 5 gaps críticos de wiring foram resolvidos — FairnessGuard ativo em sourcing + pipeline, PromptInjectionGuard ativo em WSI + chat, PII Masking ativo globalmente + Celery + strip antes do LLM, ConsentCheckerService no Gate 1 WSI, AuditService em todas as decisões de Gate
- Os gaps remanescentes são de **configuração do fluxo Alpha 1** (não de código ausente)
- **Atualizado v5.0:** Análise profunda identificou 20+ capacidades ausentes/parciais (ver seção 16.6), incluindo: LIA Score clicável, WSI assíncrono, ML adaptativo, fit cultural, auto-routing aprendiz, JobReportModal com dados reais, análise comparativa visual, e 8 dívidas técnicas
- O trabalho principal é: **(1)** wiring dos agentes existentes, **(2)** configuração do fluxo Alpha 1, **(3)** baseline de fairness antes do go-live, **(4)** resolver capacidades parciais de alto impacto

### 10.1 Gaps de Funcionalidade (absent em ambos)
1. **Email tracking pixel** (abertura) + link redirect (clique) — **Absent em ambos**
2. **Inscrição web bypass Gate 1** (flag source=web_inscription) — **Absent em ambos**
3. **Feedback diferenciado por Gate** (Gate 1 construtivo vs Gate 2 final) — **Absent em ambos**

### 10.2 Gaps de Governança e Compliance

> **Nota:** Tabela atualizada v3.0 (11/03/2026). Os 5 gaps críticos (SEG-1 a SEG-5) foram implementados e testados. Gaps remanescentes são de configuração/baseline, não de wiring de código.

| Gap | Módulo LIA | V5 Equivalente | Status | Criticidade Alpha 1 |
|-----|------------|----------------|:------:|:-------------------:|
| ~~**FairnessGuard não wired no screening**~~ | `app/shared/compliance/fairness_guard.py` (3 camadas) | ⚠️ V5 tem 1 camada, sem wiring em CV screening | ✅ **Resolvido SEG-2** — `sourcing_react_agent.py` + `pipeline_transition_agent.py` | 🟢 FECHADO |
| ~~**PromptInjectionGuard não wired**~~ | `app/shared/prompt_injection.py` | ❌ V5 não tem | ✅ **Resolvido SEG-1** — `wsi_interview_graph.validate_response` + `agent_chat_ws.py` | 🟢 FECHADO |
| ~~**Consent não validado no pipeline**~~ | `app/services/consent_checker_service.py` | ❌ V5 não tem | ✅ **Resolvido SEG-4** — `ConsentCheckerService` em `wsi_interview_graph.load_context` (Gate 1) | 🟢 FECHADO |
| ~~**PII Masking não ativo em logs**~~ | `app/shared/pii_masking.py` | ❌ V5 não tem | ✅ **Resolvido SEG-3A/3B** — global log filter + Celery workers + `strip_pii_for_llm_prompt()` em 4 callers | 🟢 FECHADO |
| ~~**Audit trail não ativo nos Gates**~~ | `app/shared/compliance/audit_service.py` | ❌ V5 não tem | ✅ **Resolvido SEG-5** — pipeline (HITL + transition + LangGraph) + sourcing (ReAct + LangGraph) + HITL rejected | 🟢 FECHADO |
| **Bias Audit baseline não rodado** | `app/api/v1/bias_audit.py` | ❌ V5 não tem Bias Audit | ❌ Pendente — rodar antes do go-live Alpha 1 | 🟡 ALTO — NYC LL144 + EU AI Act |
| **PolicyEngine sem regras Alpha 1** | `app/orchestrator/policy_engine.py` | ❌ V5 não tem PolicyEngine | ❌ Pendente — configurar via HiringPolicyService (`apply_industry_defaults` + `save_policy_block`) | 🟡 ALTO — governança de agentes |
| **FRIA não documentado** | Template existe nos docs compliance | ❌ V5 não tem FRIA | ❌ Pendente — preencher para screening WSI | 🟡 ALTO — EU AI Act Art. 6 Annex III |
| **Circuit breakers sem config** | Infra existe | ⚠️ V5 tem retry básico, sem circuit breaker formal | ❌ Pendente — configurar para Anthropic/OpenAI/Gemini | 🟡 ALTO — resiliência |
| **Data retention não configurado** | `LgpdCleanupService` | ❌ V5 não tem cleanup/retention | ❌ Pendente — configurar 90/180/365 dias para Alpha 1 | 🟡 ALTO — LGPD Art. 16 |
| **DSR workflow não testado** | `app/api/v1/data_subject_requests.py` | ❌ V5 não tem DSR workflow | ❌ Pendente — testar fluxo completo e2e | 🟡 ALTO — LGPD Art. 18 |

**Gaps resolvidos pelos Sprints SEG (resumo técnico):**
- **SEG-1** `PromptInjectionGuard`: singleton `_injection_guard` em `agent_chat_ws.py`; `validate_response()` em `wsi_interview_graph.py`. High→block, medium→log+continue.
- **SEG-2** `FairnessGuard`: `check()` + `check_implicit_bias()` no início de `process()` em sourcing e pipeline. Blocked→retorna `educational_message`.
- **SEG-3A** `PII Masking Celery`: `@signals.worker_process_init.connect` em `libs/config/lia_config/celery_app.py` instala o filter em cada worker child process (modelo prefork).
- **SEG-3B** `strip_pii_for_llm_prompt()`: aplicado antes de qualquer montagem de prompt em `rubric_evaluation_service.py`, `analysis_service.py`, `voice_screening_analysis.py`, `candidate_comparison_service.py`. Feature flag `LLM_PROMPT_PII_STRIPPING_ENABLED`.
- **SEG-4** `ConsentCheckerService`: em `wsi_interview_graph.load_context()` com `AsyncSessionLocal`. Revogado→`state.error="LGPD_CONSENT_REVOKED"`. Fail-safe: exceção no check não bloqueia (warning log).
- **SEG-5** `AuditService`: `log_decision()` com `PROTECTED_CRITERIA` sempre em `criteria_ignored`. Fail-safe: exceção no audit não bloqueia o agente.

### 10.3 Gaps de Integração/Wiring (infra funcional existe, precisa configurar para Alpha 1)
1. **Follow-up 7 dias** — LIA tem `automation_scheduler.py` (criar regra Alpha 1)
2. **Triagem abandonada 48h** — LIA tem trigger `triagem_abandonada` (configurar timings)
3. **Chat Web → WSI** — LIA tem WebSocket `agent_chat_ws.py` + WSI services (wiring)
4. **Alerta consultor via Teams** — LIA tem 5 serviços Teams (configurar eventos)

---

## 11. RECOMENDAÇÃO — ORDEM DE CONSTRUÇÃO
→ **Movido para seção 17** (após toda a documentação técnica e catálogo de agentes)

---

## 12. RESUMO PARA CRIAÇÃO DE CARDS JIRA
→ **Movido para seção 18** (após toda a documentação técnica e catálogo de agentes)

---

## 13. ARQUITETURA E PADRÕES GERAIS

### Padrão de Agentes
```
LangGraphReActBase (libs/agents-core/lia_agents_core/langgraph_react_base.py)
├── create_react_agent (LangGraph prebuilt)
├── State: MessagesState
├── Checkpointer: PostgresSaver
├── Nodes: agent (LLM) ↔ tools (executor)
└── Cicla até LLM dar resposta final
```

### Padrão 4-File por Agente
```
domains/{domain}/agents/
├── {domain}_react_agent.py       ← Agente ReAct (ou Graph)
├── {domain}_tool_registry.py     ← Tools registradas
├── {domain}_system_prompt.py     ← System prompt
└── {domain}_stage_context.py     ← Contexto por estágio
```

### Orquestração (CascadedRouter 6 Tiers)
```
Usuário → MainOrchestrator → CascadedRouter (6 tiers) → Agente de Domínio
         ├── Tier 1: Memory Cache (in-memory)
         ├── Tier 2: Redis Cache
         ├── Tier 3: VectorSemanticCache (pgvector cosine)
         ├── Tier 4: FastRouter (regex/keyword)
         ├── Tier 5: LLM Cascade (Haiku→Sonnet→Opus)
         └── Tier 6: Clarification (pedir ao usuário)
```

### Infraestrutura Compartilhada (usada por todos os agentes)
| Componente | Arquivo | Função |
|-----------|--------|--------|
| BaseAgent | `libs/agents-core/lia_agents_core/langgraph_react_base.py` | Base ReAct com lifecycle hooks |
| FairnessGuard | `app/shared/agents/fairness_guard.py` | 3 camadas (pre-prompt, post-response, aggregate) |
| AuditCallback | `app/shared/compliance/audit_service.py` | Log estruturado de decisões IA |
| PII Masking | `app/shared/pii_masking.py` | Masking LGPD (CPF, email, tel) |
| PromptInjectionGuard | `app/shared/prompt_injection.py` | Detecção de prompt injection (177 linhas) |
| Token Budget | `app/services/token_budget_service.py` | Rate limiting por tenant/plano |
| HITL Service | `app/services/hitl_service.py` | Human-in-the-Loop via LangGraph interrupt |
| EmbeddingService | `app/shared/intelligence/embedding_service.py` | Gemini text-embedding-004 (768 dim) |
| WorkingMemoryService | `app/shared/agents/working_memory.py` | Memória de trabalho persistente por sessão |

### Shared Tools (disponíveis para todos os agentes)
**Arquivos:** `app/shared/tools/insight_tools.py`, `proactive_tools.py`, `predictive_tools.py`, `export_tools.py`

| Tool | O que faz | Frequência |
|------|----------|-----------|
| `get_pipeline_health` | Detecta gargalos e estagnação | On-demand |
| `get_conversion_rates` | Taxas de conversão entre estágios | On-demand |
| `get_time_to_fill` | Duração média de preenchimento | On-demand |
| `get_candidate_quality_distribution` | Distribuição de scores | On-demand |
| `check_stagnant_candidates` | Candidatos parados >7 dias | Periódico (1h) |
| `check_pending_offers` | Ofertas aguardando resposta | Periódico (30m) |
| `check_overdue_tasks` | Tarefas atrasadas do recrutador | Periódico (1h) |
| `check_pipeline_risks` | Scan holístico de saúde | Periódico (30m) |
| `predict_dropout_risk` | Probabilidade de desistência | On-demand |
| `predict_time_to_fill` | Estimativa de tempo | On-demand |
| `get_pipeline_forecast` | Projeção 4 semanas | On-demand |
| `get_strategic_recommendations` | Conselho consultivo IA | On-demand |
| `export_candidates` | Exporta lista CSV/XLSX/JSON | On-demand |
| `generate_report` | Relatórios PDF de recrutamento | On-demand |
| `export_job_analytics` | Deep dive por vaga | On-demand |
| `schedule_report` | Agenda relatórios recorrentes | On-demand |

---

## 13B. SHELL PADRÃO DO AGENTE LIA — BLUEPRINT PARA REPLICAÇÃO

> **Fonte:** `docs/GUIA_ARQUITETURA_IA_v1.0.md` — Seções 14, 15, 32, 33, Apêndice B
>
> **Este shell é o CONTRATO que todos os 15 agentes devem seguir.** Um agente está "pronto" quando implementa 100% deste shell. Qualquer desvio deve ser documentado como decisão arquitetural (ADR).

### 13B.1 Padrão 4-File — Estrutura Obrigatória

```
app/domains/{domain}/agents/
├── {domain}_react_agent.py       ← Agente principal (herda EnhancedAgentMixin + BaseAgent)
├── {domain}_tool_registry.py     ← Tools registradas com scope + metadata
├── {domain}_system_prompt.py     ← Prompt canônico (função get_{domain}_system_prompt)
└── {domain}_stage_context.py     ← Definição de stages + campos + transições
```

**Exceções documentadas:**
- LangGraph Graphs (`wsi_interview_graph.py`, `interview_graph.py`, `job_wizard_graph.py`) — substituem `_react_agent.py`
- PolicySetupAgent (`agent.py`) — LLM direto, não ReAct
- PipelineTransitionAgent — invocação direta via API, não via registry

### 13B.2 Anatomia do System Prompt — 10 Seções Obrigatórias

Todo agente ReAct DEVE ter system prompt com estas seções na ordem:

```
[1] === IDENTIDADE ===           → Nome LIA, personalidade, tom, idioma (PT-BR)
[2] === FILOSOFIA CENTRAL ===    → Chat como interface principal do produto
[3] === INSTRUCOES REACT ===     → Como raciocinar (Thought/Action/Observe) em JSON
[4] === ESTAGIOS ===             → Estágios do domínio com campos obrigatórios de cada um
[5] === COMPLIANCE E ETICA ===   → LGPD, FairnessGuard, regras de bloqueio discriminatório
[6] === EXEMPLOS ===             → Few-shot: entrada → raciocínio → resposta (2-3 exemplos)
[7] === CONTRA-ARGUMENTACAO ===  → Quando e como discordar do recrutador com dados
[8] === CALIBRACAO ===           → Adaptar ao porte (startup <50 / PME 50-500 / corporação >500)
[9] === CONFIRMACOES ===         → Palavras de confirmação/negação em PT-BR
[10] === REGRAS CRITICAS ===     → Lista de NUNCA/SEMPRE (guardrails hard-coded)
```

**Tamanho ideal:** 800-1500 tokens. Acima de 2000 tokens = custo desnecessário e perda de atenção do LLM.

### 13B.3 Template de Identidade LIA (fixo, compartilhado)

**Arquivo:** `app/prompts/shared/lia_persona.yaml`

```
Você é a LIA (Learning Intelligence Assistant), assistente de IA especialista em
[função específica do agente] da plataforma WeDOTalent.

Seu papel: [descrever o que este agente faz em 1-2 frases]
Seu estilo: consultivo, direto, baseado em dados — nunca vago ou evasivo

PRINCÍPIOS INEGOCIÁVEIS:
- Nunca discriminar candidatos por gênero, raça, idade, religião, orientação sexual,
  estado civil ou deficiência
- Sempre citar a base legal quando bloquear solicitação discriminatória
- Nunca inventar dados ou confirmar informações que não foram fornecidas
- Identificar-se como IA quando perguntado diretamente
- Responder em português brasileiro
- Proibido linguagem informal (sem "vc", "tmj", "blz")
```

### 13B.4 Protocolo ReAct — Instruções de Output (JSON obrigatório)

```json
PROTOCOLO DE RACIOCÍNIO — IMPORTANTE:

Para cada mensagem, analise o contexto e responda com JSON:
{
  "thought": "raciocínio estratégico PROFUNDO — analise o que sabe, o que falta,
              riscos, trade-offs. Não seja superficial aqui.",
  "action": "call_tool" | "respond" | "ask_clarification",
  "tool_name": "nome da ferramenta (null se action != call_tool)",
  "tool_args": { ... parâmetros da ferramenta ... },
  "response": "sua resposta ao usuário (null se chamando ferramenta)"
}

Regras de decisão:
- call_tool   → quando precisa de dados externos para responder bem
- respond     → quando tem informação suficiente para uma resposta útil
- ask_clarification → quando a pergunta é ambígua e precisa de mais contexto
```

### 13B.5 YAML de Domínio — Estrutura Obrigatória

**Localização:** `app/prompts/domains/{domain}.yaml`

```yaml
persona:
  name: "LIA"
  role: "[papel específico do agente neste domínio]"
  tone: "consultivo, direto, baseado em dados"

scope_in:
  - "O que o agente DEVE fazer"

scope_out:
  - "O que o agente NÃO DEVE fazer"

behavioral_rules:
  - "Regras comportamentais hard-coded"

system_prompt: |
  [Prompt completo seguindo as 10 seções obrigatórias]

intent_examples:
  - input: "exemplo de mensagem do usuário"
    intent: "nome_da_intenção"
    domain: "nome_do_domínio"
```

**YAMLs existentes na LIA (9 domínios):**
`sourcing.yaml`, `job_management.yaml`, `cv_screening.yaml`, `communication.yaml`, `interview_scheduling.yaml`, `analytics.yaml`, `ats_integration.yaml`, `automation.yaml`, `recruiter_assistant.yaml`

### 13B.6 EnhancedAgentMixin — Capacidades Obrigatórias

**Arquivo:** `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py`

Todo agente que herda `EnhancedAgentMixin` ganha automaticamente:

| Capacidade | Método | O que faz |
|-----------|--------|----------|
| Memória Working | `_get_memory_context()` | Carrega contexto da sessão atual |
| Memória Long-Term | `_get_ltm_context()` | Insights de sessões anteriores do mesmo recrutador |
| Guardrails | `_resolve_guardrails()` | Verifica policies da empresa (autonomia, HITL) |
| Learning | `_post_loop_learning()` | Extrai aprendizados da interação e salva no LTM |
| Insight Tools | `_get_all_enhanced_tools()` | Tools compartilhadas (analytics, proactive, predictive) |

### 13B.7 Lifecycle do Agente ReAct — 6 Passos (Exemplo Canônico)

> **CONTRATO:** Todo agente ReAct (Ag.1, Ag.2, Ag.3, Ag.7, Ag.8, Ag.9, Ag.10) **deve** seguir este padrão de 6 passos. A classe concreta muda, mas a sequência é obrigatória.

**Exemplo:** `SourcingReActAgent` — `app/domains/sourcing/agents/sourcing_react_agent.py`

```python
class SourcingReActAgent(EnhancedAgentMixin, BaseAgent):
    """Herda de EnhancedAgentMixin e BaseAgent."""

    def __init__(self) -> None:
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_sourcing_tools()]
        self._setup_enhanced(domain="sourcing")  # ← ativa memória + autonomia + learning

    async def process(self, input: AgentInput, db: AsyncSession) -> AgentOutput:
        # 1. MEMÓRIA — carrega working memory + long-term memory + context summary
        memory_context = await self._get_memory_context(input.session_id, input.company_id)

        # 2. GUARDRAILS — resolve policies da empresa via DB (3-tier: global → tenant → domínio)
        guardrails = await self._resolve_guardrails(input.company_id)

        # 3. TOOLS — monta lista de tools por estágio do pipeline + enhanced tools
        tools = get_stage_tools(input.pipeline_stage) + self._get_all_enhanced_tools()

        # 4. CONFIG — cria ReActConfig com observer (telemetria)
        config = ReActConfig(
            max_iterations=settings.REACT_MAX_ITERATIONS_DEFAULT,  # 5
            max_tool_calls=settings.REACT_MAX_TOOL_CALLS,          # 3
            domain="sourcing",
            observer=ReActObserver(
                session_id=input.session_id,
                domain="sourcing",
                agent_class="SourcingReActAgent",
                company_id=input.company_id,
                user_id=input.user_id,
            )
        )

        # 5. EXECUÇÃO — roda ReActLoop com system prompt que inclui guardrails + memória
        state = await ReActLoop(config).run(
            system_prompt=get_sourcing_system_prompt(guardrails, memory_context),
            user_message=input.message,
            tools=tools,
            history=await self._memory_service.get_history(input.session_id),
        )

        # 6. PÓS-LOOP — learning + save memory + build output
        await self._post_loop_learning(state, input.company_id, input.session_id)

        return AgentOutput.from_state(state)
```

**Para reproduzir qualquer agente ReAct, substituir:**
| O que muda | Sourcing (exemplo) | Outro agente |
|-----------|-------------------|-------------|
| Classe | `SourcingReActAgent` | `{Domain}ReActAgent` |
| Domain | `"sourcing"` | `"{domain}"` |
| Tools | `get_sourcing_tools()` | `get_{domain}_tools()` |
| System prompt | `get_sourcing_system_prompt()` | `get_{domain}_system_prompt()` |
| Stage tools | `get_stage_tools(stage)` | Mesma função (tools filtradas por pipeline_stage) |

**Proteções do Loop:**
- `REACT_MAX_ITERATIONS_DEFAULT = 5` (evita loops infinitos)
- `REACT_DUPLICATE_THRESHOLD = 2` (mesma ação 2x → para)
- `REACT_OBSERVATION_MAX_CHARS = 5000` (trunca outputs grandes)
- `REACT_MAX_TOOL_CALLS = 3` (limita chamadas de tool por request)
- `conversation_history[-5:]` (apenas últimas 5 mensagens)

### 13B.8 Few-Shot Examples — Padrão

Cada agente deve ter 2-3 exemplos de reasoning correto no system prompt:

```
EXEMPLOS:

[Usuário]: "[mensagem típica do domínio]"
[Resposta]:
{
  "thought": "[raciocínio profundo mostrando análise de contexto, dados faltantes, trade-offs]",
  "action": "call_tool",
  "tool_name": "[tool_name]",
  "tool_args": { ... },
  "response": null
}

[Usuário]: "[mensagem que viola compliance]"
[Resposta]:
{
  "thought": "[raciocínio mostrando detecção de violação e base legal]",
  "action": "respond",
  "tool_name": null,
  "tool_args": {},
  "response": "[bloqueio educativo com citação da lei]"
}
```

**Regra (recomendação André):** 10 exemplos claros + 10 ambíguos por domínio, co-criados com profissional sênior de RH.

### 13B.9 Checklist de Conformidade do Agente

Para cada agente, verificar:

| # | Item | Verificação | Obrigatório |
|---|------|------------|:-----------:|
| 1 | 4-file pattern completo | `ls app/domains/{domain}/agents/` | ✅ |
| 2 | System prompt com 10 seções | Inspecionar `_system_prompt.py` | ✅ |
| 3 | Template de identidade LIA | Seção IDENTIDADE no prompt | ✅ |
| 4 | Protocolo ReAct (JSON) | Seção INSTRUCOES REACT no prompt | ✅ |
| 5 | Few-shot examples (2-3) | Seção EXEMPLOS no prompt | ✅ |
| 6 | YAML de domínio | `app/prompts/domains/{domain}.yaml` | ✅ |
| 7 | EnhancedAgentMixin herdado | Classe do agente | ✅ |
| 8 | ReActObserver (telemetria) | No método `process()` | ✅ |
| 9 | Guardrails por empresa | `_resolve_guardrails()` chamado | ✅ |
| 10 | Memória (working + LTM) | `_get_memory_context()` chamado | ✅ |
| 11 | Post-loop learning | `_post_loop_learning()` chamado | ✅ |
| 12 | Compliance no prompt | Seção COMPLIANCE E ETICA | ✅ |
| 13 | Calibração por porte | Seção CALIBRACAO | ✅ |
| 14 | FairnessGuard wired | Intercepta queries discriminatórias | ✅ |
| 15 | PII Masking nos logs | Nenhum CPF/email/tel nos logs | ✅ |
| 16 | Multi-tenancy (company_id) | Em todas as queries DB | ✅ |
| 17 | Testes unitários | `tests/domains/{domain}/` | ✅ |
| 18 | Testes de integração | Endpoint → agente → tool → DB | ✅ |

### 13B.10 WSI — Validação dos 15 Serviços na LIA

> Os 15 arquivos WSI listados no roadmap **todos existem** na LIA com implementação completa:

| # | Arquivo | Linhas | Conceito WSI Implementado | Status |
|---|---------|:------:|---------------------------|:------:|
| 1 | `wsi_screening_pipeline.py` | 676 | Pipeline principal — orquestra Blocks 2-5 (empresa, elegibilidade, técnico, comportamental) | ✅ Completo |
| 2 | `wsi_deterministic_scorer.py` | 558 | Scoring 100% determinístico: `Score = (0.6×Autodec) + (0.4×Context) - Penalty + Bonus` | ✅ Completo |
| 3 | `wsi_question_generator.py` | 600 | Geração de perguntas por taxonomia de Bloom (6 níveis) + Dreyfus (5 estágios) | ✅ Completo |
| 4 | `wsi_question_adjuster.py` | 297 | Ajuste dinâmico de dificuldade mantendo integridade WSI (pesos, blocos, sequência) | ✅ Completo |
| 5 | `wsi_question_service.py` | 879 | Classificação de skills em categorias + mapeamento para blocos WSI | ✅ Completo |
| 6 | `wsi_service.py` | 1295 | Fachada geral — coordena JD→competências→perguntas→análise→relatório→feedback | ✅ Completo |
| 7 | `wsi_voice_orchestrator.py` | 780 | Triagem por voz via OpenMic.ai — converte perguntas WSI→prompts de agente→scores | ✅ Completo |
| 8 | `rubric_evaluation_service.py` | 1350 | Avaliação por rubrica com exclusões essenciais + evidências + red flags + calibração | ✅ Completo |
| 9 | `evaluation_criteria_service.py` | 465 | Biblioteca de critérios + seeding de catálogos + tracking de efetividade | ✅ Completo |
| 10 | `calibration_profiles.py` | 948 | Perfis de maturidade de área + offsets Bloom/Dreyfus + ajustes geográficos + salary ranges | ✅ Completo |
| 11 | `seniority_context_calibrator.py` | 599 | Calibração por contexto (tech emergente vs madura, geografia, salário) | ✅ Completo |
| 12 | `score_normalization_service.py` | 176 | Normalização cross-versão para comparabilidade justa | ✅ Completo |
| 13 | `personalized_feedback_service.py` | 1020 | Feedback construtivo com pontos fortes + oportunidades + tom configurável | ✅ Completo |
| 14 | `pre_qualification_service.py` | 354 | Fast-path de elegibilidade (Block 3) antes dos blocos complexos | ✅ Completo |
| 15 | `eligibility_verification_service.py` | 374 | Elegibilidade interativa + reconsideração de respostas "não" | ✅ Completo |
| 16 | `seniority_resolver.py` | ~120 | Resolução de senioridade a partir do perfil do candidato | ✅ Completo |
| 17 | `seniority_utils.py` | ~80 | Utilitários de senioridade (mapeamentos, helpers) | ✅ Completo |
| 18 | `app/services/wsi_screening_pipeline.py` | ~50 | Wrapper legacy no nível de serviço (redireciona para domain) | ✅ Legacy |
| | **TOTAL** | **~9.621** | | |

**Metodologia WSI fundamentada em:**
- **Bloom Taxonomy** (6 níveis: Remember → Create) — define profundidade das perguntas técnicas
- **Dreyfus Model** (5 estágios: Novice → Expert) — mapeia experiência e contexto
- **Big Five (OCEAN)** — perguntas comportamentais e fit cultural
- **CBI (Competency-Based Interviewing)** — estrutura de perguntas por competência
- **Calibração contextual** — ajusta expectativas por maturidade da área, geografia e salário

---

## 13C. CAMADA DE INTELIGÊNCIA LIA — INVENTÁRIO COMPLETO (~165 ARQUIVOS)

> **Fonte:** `docs/mapa_inteligencia_lia_completo.md` — 20 seções, ~165 arquivos
>
> **Propósito:** Este inventário lista TODOS os arquivos da camada de inteligência organizados por camada funcional. Para cada camada, indica quais arquivos são Alpha 1 (obrigatórios) e quais são pós-Alpha. Os **roteiros de reprodução** no final dizem a ORDEM EXATA para replicar cada subsistema.

### 13C.1 Orquestrador Central (9 arquivos) [ALPHA 1]

O "cérebro" que recebe inputs, classifica a intenção e decide qual agente invocar.

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/orchestrator/orchestrator.py` | Ponto de entrada — recebe requisição, coordena agentes, retorna resposta | ✅ |
| `app/orchestrator/intent_router.py` | Classificação de intenção (NLU) — decide qual domínio atende | ✅ |
| `app/orchestrator/fast_router.py` | Router rápido para comandos simples sem LLM | ✅ |
| `app/orchestrator/cascaded_router.py` | Router em cascata — tenta fast_router, depois LLM (6 tiers) | ✅ |
| `app/orchestrator/task_planner.py` | Decompõe tarefas complexas em subtarefas sequenciais | ✅ |
| `app/orchestrator/policy_engine.py` | Aplica políticas de negócio e guardrails antes/depois da execução | ✅ |
| `app/orchestrator/action_executor.py` | Executa ações decididas pelo orquestrador | ✅ |
| `app/orchestrator/pending_action.py` | Gerencia ações pendentes que aguardam confirmação humana | ✅ |
| `app/orchestrator/state_manager.py` | Gerencia estado da conversa entre turnos | ✅ |

**Arquivos adicionais do orquestrador (encontrados na verificação do codebase):**

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/orchestrator/main_orchestrator.py` | MainOrchestrator — ponto de entrada de alto nível | ✅ |
| `app/orchestrator/context_adapter.py` | Adaptação de contexto entre componentes do orquestrador | ✅ |
| `app/orchestrator/memory_resolver.py` | Resolução de memória — carrega contexto relevante para o agente | ✅ |
| `app/orchestrator/navigation_intent.py` | Grupos de intent de navegação — Configurações, Indicadores, WSI (Sprint J) | ✅ |
| `app/orchestrator/llm_cascade.py` | Implementação da cascata LLM (Haiku→Sonnet→Opus) | ✅ |
| `app/orchestrator/semantic_cache.py` | Cache semântico de intents (alias para vector_semantic_cache) | ✅ |
| `app/orchestrator/vector_semantic_cache.py` | Cache semântico via pgvector cosine similarity | ✅ |
| `app/orchestrator/tenant_budget.py` | Controle de budget de tokens por tenant | ✅ |

### 13C.2 Provedores LLM e Infraestrutura de IA (13 arquivos) [ALPHA 1]

Interface com modelos de linguagem, embeddings e busca semântica — toda IA depende desta camada.

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/services/llm.py` | Serviço LLM de alto nível — 955 linhas, abstração principal usada por agentes | ✅ |
| `app/shared/providers/llm_factory.py` | Factory — instancia o provider correto (Claude, OpenAI, Gemini) | ✅ |
| `app/shared/providers/llm_provider.py` | Interface base de provider LLM | ✅ |
| `app/shared/providers/llm_client.py` | Cliente HTTP para chamadas LLM | ✅ |
| `app/shared/providers/llm_claude.py` | Provider Anthropic Claude (primário) | ✅ |
| `app/shared/providers/llm_openai.py` | Provider OpenAI GPT-4 (fallback) | ✅ |
| `app/shared/providers/llm_gemini.py` | Provider Google Gemini (fallback + embeddings) | ✅ |
| `app/shared/providers/ats_factory.py` | Factory de integração com sistemas ATS | ✅ |
| `app/shared/providers/voice_provider.py` | Provider de voz (speech-to-text, text-to-speech) | ⚠️ |
| `app/shared/intelligence/embedding_service.py` | Serviço de embeddings — Gemini text-embedding-004 (768 dim) | ✅ |
| `app/shared/intelligence/semantic_search_service.py` | Busca semântica sobre embeddings (pgvector cosine) | ✅ |
| `app/shared/intelligence/smart_extractor.py` | Extrator inteligente — NL → dados estruturados via LLM | ✅ |
| `app/shared/intelligence/param_patterns.py` | Padrões de parâmetros para extração | ✅ |

### 13C.3 Robustez e Guardrails (11 arquivos) [ALPHA 1 — wiring pendente]

Camadas de proteção para segurança e confiabilidade das respostas da IA. **Módulos existem, mas a maioria NÃO está wired nos fluxos de agente (ver seção 16.2).**

| Arquivo | Papel | Alpha 1 | Wired? |
|---------|-------|:-------:|:------:|
| `app/shared/robustness/input_validation.py` | Validação de inputs — sanitização e limites | ✅ | ❌ |
| `app/shared/robustness/response_filter.py` | Filtro de respostas — remove conteúdo inadequado, PII, alucinações | ✅ | ❌ |
| `app/shared/robustness/defensive_prompts.py` | Prompts defensivos — proteção contra jailbreak e manipulação | ✅ | ❌ |
| `app/shared/robustness/error_handling.py` | Tratamento de erros — fallbacks e recuperação | ✅ | ⚠️ |
| `app/shared/robustness/context_management.py` | Gestão de contexto — controle de tamanho e relevância | ✅ | ⚠️ |
| `app/shared/robustness/enhanced_base.py` | Base aprimorada para agentes com guardrails | ✅ | ⚠️ |
| `app/shared/robustness/enhanced_registry.py` | Registry aprimorado com validações | ✅ | ⚠️ |
| `app/shared/robustness/intent_schemas.py` | Schemas de intenção para validação estruturada | ✅ | ⚠️ |
| `app/models/guardrail.py` | Guardrail SQLAlchemy model — editáveis por company_id, domain, node | ✅ | ✅ |
| `app/api/v1/guardrails.py` | API de guardrails — CRUD admin para ativar/desativar regras sem deploy | ✅ | ✅ |
| `alembic/versions/020_add_guardrails_table.py` | Migration: tabela `guardrails` | ✅ | ✅ |

### 13C.4 Tools Centrais e Registries (13 arquivos) [ALPHA 1]

Sistema de tools que os agentes invocam para acessar dados e executar ações.

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/tools/registry.py` | Registry global de ferramentas | ✅ |
| `app/tools/scope_config.py` | Configuração de escopo — define quais tools cada agente pode acessar (4 scopes) | ✅ |
| `app/tools/executor.py` | Executor de ferramentas — invoca a tool e retorna resultado | ✅ |
| `app/tools/candidate_tools.py` | Tools de candidatos: buscar, filtrar, atualizar | ✅ |
| `app/tools/job_tools.py` | Tools de vagas: criar, editar, listar | ✅ |
| `app/tools/job_wizard_tools.py` | Tools específicas do wizard de vagas | ✅ |
| `app/tools/communication_tools.py` | Tools de comunicação: enviar email, WhatsApp, gerar mensagem | ✅ |
| `app/tools/query_tools.py` | Tools de consulta: queries ao banco e APIs | ✅ |
| `app/tools/export_tools.py` | Tools de exportação: relatórios, CSVs | ⚠️ |
| `app/shared/tools/insight_tools.py` | Tools de insights: análise de dados, tendências | ✅ |
| `app/shared/tools/predictive_tools.py` | Tools preditivas: previsão de sucesso, tempo de contratação | ⚠️ |
| `app/shared/tools/proactive_tools.py` | Tools proativas: sugestões automáticas, alertas | ⚠️ |
| `app/shared/tools/export_tools.py` | Tools de exportação compartilhadas | ⚠️ |

### 13C.5 Comunicação Inteligente (23 arquivos) [ALPHA 1 — CRÍTICO]

Sistema completo de comunicação multi-canal. Alpha 1 precisa de email + WhatsApp funcionando.

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/domains/communication/services/communication_service.py` | Serviço principal — orquestra envio e geração | ✅ |
| `app/domains/communication/services/interpret_context_llm_service.py` | Interpretação de contexto via LLM — gera mensagem adequada | ✅ |
| `app/domains/communication/services/infer_behavior_service.py` | Inferência de comportamento do candidato — ajusta tom e conteúdo | ✅ |
| `app/domains/communication/services/email_templates_data.py` | Banco de templates de email com variáveis | ✅ |
| `app/domains/communication/services/communication_dispatcher.py` | Dispatcher — decide e executa envio por canal (email, WhatsApp, ambos) | ✅ |
| `app/domains/communication/services/communication_history_service.py` | Histórico de comunicações por candidato | ✅ |
| `app/domains/communication/services/transition_dispatch_service.py` | Dispatch automático de comunicação em transições de pipeline | ✅ |
| `app/domains/communication/services/email_service.py` | Serviço de envio de email | ✅ |
| `app/domains/communication/services/email_providers/base.py` | Interface base do provider de email | ✅ |
| `app/domains/communication/services/email_providers/resend_provider.py` | Provider Resend | ✅ |
| `app/domains/communication/services/email_providers/sendgrid_provider.py` | Provider SendGrid | ✅ |
| `app/domains/communication/services/whatsapp_service.py` | Serviço de WhatsApp (modo simulado) | ✅ |
| `app/domains/communication/services/whatsapp_factory.py` | Factory de provedores WhatsApp | ✅ |
| `app/domains/communication/services/whatsapp_provider.py` | Provider base de WhatsApp | ✅ |
| `app/domains/communication/services/whatsapp_meta_service.py` | Provider WhatsApp via Meta/Graph API | ✅ |
| `app/domains/communication/services/whatsapp_twilio_service.py` | Provider WhatsApp via Twilio | ✅ |
| `app/domains/communication/services/data_request_service.py` | Solicitação de dados ao candidato | ✅ |
| `app/domains/communication/services/data_request_whatsapp_service.py` | Solicitação de dados via WhatsApp | ⚠️ |
| `app/domains/communication/services/webhook_service.py` | Webhooks de comunicação | ⚠️ |
| `app/domains/communication/services/return_event_service.py` | Serviço de eventos de retorno | ⚠️ |
| `app/services/email_service.py` | Serviço de email (nível serviço — legacy) | ✅ |
| `app/services/email_providers.py` | Provedores de email (nível serviço — legacy) | ✅ |
| `app/services/recruitment_email_templates.py` | Templates de email de recrutamento | ✅ |

### 13C.6 Sourcing Inteligente (13 arquivos) [ALPHA 1]

Busca e avaliação de candidatos com múltiplas fontes (local + externa).

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/domains/sourcing/services/sourcing_pipeline.py` | Pipeline principal de sourcing | ✅ |
| `app/domains/sourcing/services/candidate_search_route_service.py` | Roteamento de busca de candidatos | ✅ |
| `app/domains/sourcing/services/vacancy_search.py` | Busca por vagas | ✅ |
| `app/domains/sourcing/services/query_builders.py` | Construtores de queries de busca | ✅ |
| `app/domains/sourcing/services/search_analytics.py` | Analytics de buscas de sourcing | ⚠️ |
| `app/domains/sourcing/services/wrf_service.py` | Serviço WRF (Work Requirements Framework) | ✅ |
| `app/domains/sourcing/services/pre_wrf_filter.py` | Filtro pré-WRF | ✅ |
| `app/domains/sourcing/services/evaluation_criteria.py` | Critérios de avaliação de candidatos | ✅ |
| `app/domains/sourcing/services/es_analyzer.py` | Análise via Elasticsearch | ✅ |
| `app/domains/sourcing/services/pgv_analyzer.py` | Análise via pgvector (busca semântica) | ✅ |
| `app/domains/sourcing/services/pearch_service.py` | Serviço de busca Pearch AI (190M+ perfis) | ⚠️ |
| `app/domains/sourcing/services/apify_service.py` | Integração com Apify (web scraping LinkedIn/Glassdoor) | ⚠️ |
| `app/domains/sourcing/services/apify_mcp_client.py` | Cliente MCP para Apify | ⚠️ |

### 13C.7 CV Screening (5 arquivos) [ALPHA 1]

Triagem de currículos — complementa os 18 serviços WSI da seção 13B.10.

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/domains/cv_screening/services/cv_parser.py` | Parser de currículos — extrai dados estruturados de CVs | ✅ |
| `app/domains/cv_screening/services/cv_scoring_service.py` | Scoring de CV — pontua currículo vs. requisitos da vaga | ✅ |
| `app/domains/cv_screening/services/cv_screening_batch_service.py` | Triagem em lote — processa múltiplos CVs de uma vez | ✅ |
| `app/domains/cv_screening/services/screening_question_set_service.py` | Gerenciamento de conjuntos de perguntas de triagem | ✅ |
| `app/services/screening_question_set_service.py` | Serviço de perguntas de triagem (nível serviço — legacy) | ✅ |

### 13C.8 HITL — Human-in-the-Loop Persistence (7 arquivos) [ALPHA 1 — CRÍTICO]

Sistema de aprovação humana para ações de alto risco, com persistência para auditoria SOX/BCB-498.

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/services/hitl_service.py` | HITLService — Redis fast-path + PostgreSQL source-of-truth | ✅ |
| `app/models/hitl.py` | HITLPendingAction + HITLAuditTrail — modelos SQLAlchemy | ✅ |
| `app/api/v1/hitl.py` | `POST /api/v1/hitl/{thread_id}/approve` — endpoint de aprovação | ✅ |
| `alembic/versions/032_add_hitl_tables.py` | Migration: tabelas `hitl_pending_actions` + `hitl_audit_trail` | ✅ |
| `tests/unit/test_hitl_persistence.py` | 25 testes de persistência HITL | ✅ |
| `plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx` | Componente FE — card de aprovação no float chat | ✅ |
| `plataforma-lia/src/hooks/use-float-streaming.ts` | Hook FE — streaming WebSocket + HITL interception | ✅ |

**Agentes que usam HITL:**
- `job_wizard_graph.py` — `interrupt_before=["stage_transition"]`
- `wsi_interview_graph.py` — `interrupt_before=["lg_generate_feedback"]`
- `pipeline_transition_agent.py` — pre-check HITL antes de `_process_langgraph()`

### 13C.9 Avaliação de Qualidade de Agentes (3 arquivos) [ALPHA 1 — ALTO]

Avaliação automática de qualidade das respostas, drift detection e alertas.

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/services/agent_quality_evaluator.py` | AgentQualityEvaluator — avalia task_completion, fairness, response_quality, latência | ✅ |
| `app/services/agent_health_alert_service.py` | AgentHealthAlertService — alertas Bell+Teams | ✅ | ❌ NÃO EXISTE — implementar |
| `alembic/versions/034_add_agent_quality_evaluations.py` | Migration: tabela `agent_quality_evaluations` | ✅ |

### 13C.10 Preferências de Agente por Usuário (3 arquivos) [PÓS-ALPHA]

Auto-confirm que elimina confirmações repetitivas após a primeira aprovação.

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/services/user_agent_preference_service.py` | `should_auto_confirm()` — verifica se já aprovou ação similar | ⚠️ |
| `app/models/user_agent_preference.py` | UserAgentPreference — modelo SQLAlchemy | ⚠️ |
| `alembic/versions/035_add_user_agent_preferences.py` | Migration: tabela `user_agent_preferences` | ⚠️ |

### 13C.11 Observabilidade e Governança de IA (10 arquivos)

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/shared/governance/agent_monitoring_service.py` | Monitoramento de agentes — latência, erros, throughput | ✅ |
| `app/shared/governance/feature_flag_service.py` | Feature flags para controle de funcionalidades de IA | ✅ |
| `app/services/token_tracking_service.py` | Tracking de tokens — contabiliza uso por agente, modelo e tenant | ✅ |
| `app/services/explainability_service.py` | Explicabilidade — justificativas legíveis para decisões IA | ⚠️ |
| `app/services/agent_monitoring_service.py` | Monitoramento de agentes (nível serviço) | ✅ |
| `app/services/ai_cache_service.py` | Cache de respostas de IA — evita chamadas repetidas | ✅ |
| `app/services/autonomous_agent_service.py` | Serviço de agentes autônomos — execução sem supervisão | ⚠️ |
| `app/services/training_data_service.py` | Serviço de dados de treinamento — coleta para fine-tuning | ⚠️ |
| `app/services/voice_screening_analysis.py` | Análise de screening por voz | ⚠️ |
| `app/domains/analytics/services/wsi_observability.py` | Observabilidade específica do WSI | ✅ |

### 13C.12 Analytics e Insights com IA (9 arquivos) [PÓS-ALPHA — serviços do AnalyticsReAct]

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/domains/analytics/services/job_analytics_prompt_service.py` | Prompts para analytics de vagas via LLM | ⚠️ |
| `app/domains/analytics/services/job_insights_service.py` | Insights inteligentes sobre vagas | ⚠️ |
| `app/domains/analytics/services/predictive_analytics_service.py` | Analytics preditivo — previsões de tempo e sucesso | ⚠️ |
| `app/domains/analytics/services/job_report_service.py` | Geração de relatórios de vagas | ⚠️ |
| `app/domains/analytics/services/candidate_report_service.py` | Geração de relatórios de candidatos | ⚠️ |
| `app/domains/analytics/services/report_service.py` | Serviço geral de relatórios | ⚠️ |
| `app/domains/analytics/services/search_analytics_service.py` | Analytics de buscas | ⚠️ |
| `app/domains/analytics/services/wizard_analytics_service.py` | Analytics do wizard de criação | ⚠️ |
| `app/domains/analytics/services/agent_monitoring_service.py` | Monitoramento de agentes (nível analytics) | ⚠️ |

### 13C.13 Intelligence Layer e Machine Learning (5 arquivos) [PÓS-ALPHA]

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/services/intelligence_layer_service.py` | Serviço central da camada de inteligência — readiness checks, predições | ⚠️ |
| `app/services/ml/feature_engineering.py` | Engenharia de features — extrai variáveis para modelos preditivos | ⚠️ |
| `app/services/ml/outcome_predictor.py` | Preditor de resultados — prevê sucesso de contratação | ⚠️ |
| `app/services/ml/model_registry.py` | Registry de modelos ML — versionamento e seleção | ⚠️ |
| `app/shared/agents/proactive_worker.py` | Worker proativo — verificações automáticas sem intervenção | ⚠️ |

**Arquivos adicionais em `app/shared/agents/` (verificados no codebase):**

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/shared/agents/enhanced_agent_mixin.py` | EnhancedAgentMixin — adiciona memória+guardrails+learning a agentes | ✅ |
| `app/shared/agents/langgraph_react_base.py` | LangGraphReActBase — base para agentes ReAct com LangGraph | ✅ |
| `app/shared/agents/langgraph_base.py` | LangGraphBase — base genérica para grafos LangGraph | ✅ |
| `app/shared/agents/checkpointer.py` | Checkpointer — wrapper do PostgresSaver por tenant | ✅ |
| `app/shared/agents/agent_scaffold.py` | Scaffold para criação de novos agentes (template) | ✅ |
| `app/shared/agents/autonomy_engine.py` | Engine de autonomia — decide quando agir proativamente | ⚠️ |
| `app/shared/agents/confidence.py` | Estimativa de confiança das respostas do agente | ⚠️ |
| `app/shared/agents/execution_log_store.py` | Store de logs de execução para debugging e auditoria | ✅ |
| `app/shared/agents/learning_extractor.py` | Extrai aprendizados da interação para salvar no LTM | ✅ |
| `app/shared/agents/long_term_memory.py` | Memória de longo prazo — insights de sessões anteriores | ⚠️ |
| `app/shared/agents/memory_integration.py` | Integração entre working memory e long-term memory | ✅ |
| `app/shared/agents/nodes.py` | Nós compartilhados entre múltiplos grafos | ✅ |
| `app/shared/agents/observability.py` | Observabilidade dos agentes (métricas, traces) | ✅ |
| `app/shared/agents/base_state_machine.py` | State machine base para agentes com estados | ✅ |
| `app/shared/agents/state_machine.py` | State machine implementada para fluxos de agentes | ✅ |
| `app/shared/agents/streaming_callback.py` | Callback de streaming (respostas token-a-token) | ✅ |
| `app/shared/agents/timed_tool_node.py` | Nó de tool com timeout configurável | ✅ |
| `app/shared/agents/agent_types.py` | Tipos e enums de agentes | ✅ |
| `app/shared/agents/sourcing_engagement_nodes.py` | Nós de engajamento específicos do sourcing | ✅ |

### 13C.14 Configuração e Infraestrutura Base (8 arquivos) [ALPHA 1]

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/core/config.py` | Configuração central — chaves API, modelos padrão, limites, feature flags | ✅ |
| `app/core/database.py` | Conexão com banco de dados PostgreSQL | ✅ |
| `app/core/logging_config.py` | Configuração de logs com PII masking | ✅ |
| `app/core/taxonomy.py` | Taxonomia de categorias (skills, áreas, senioridades) | ✅ |
| `app/core/template_channels.py` | Mapeamento de canais de comunicação por template | ✅ |
| `app/services/email_service.py` | Serviço de email (nível serviço) | ✅ |
| `app/services/email_providers.py` | Provedores de email (nível serviço) | ✅ |
| `app/services/recruitment_email_templates.py` | Templates de email de recrutamento | ✅ |

### 13C.15 Testes de Carga (2 arquivos) [ALPHA 1 — pré-go-live]

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `tests/load/locustfile.py` | Locust — WizardUser, PipelineUser, HealthCheckUser com p50/p95/p99 | ✅ |
| `tests/load/load_test_config.py` | Configuração de carga — targets, thresholds, cenários | ✅ |

### 13C.16 Resumo Quantitativo

| Camada | Arquivos | Alpha 1 | Pós-Alpha |
|--------|:--------:|:-------:|:---------:|
| Orquestrador Central | 9 | 9 | 0 |
| Provedores LLM | 13 | 12 | 1 |
| Robustez/Guardrails | 11 | 11 | 0 |
| Tools Centrais | 13 | 8 | 5 |
| Comunicação | 23 | 20 | 3 |
| Sourcing | 13 | 9 | 4 |
| CV Screening | 5 | 5 | 0 |
| WSI (seção 13B.10) | 18 | 18 | 0 |
| HITL | 7 | 7 | 0 |
| Quality Evaluator | 3 | 3 | 0 |
| Preferências Usuário | 3 | 0 | 3 |
| Observabilidade | 10 | 5 | 5 |
| Analytics/Insights | 9 | 0 | 9 |
| ML/Intelligence | 5 | 0 | 5 |
| Config/Infra Base | 8 | 8 | 0 |
| Testes de Carga | 2 | 2 | 0 |
| **TOTAL** | **~152** | **~117** | **~35** |

> **Atualização Sprint J (11/03/2026):** Números atualizados após verificação do codebase real:
> - Agentes ReAct: **13** (11 via registry + PipelineTransitionAgent direto + PolicySetupAgent LLM direto)
> - Domínios DDD: **12** (inclui domínio `policy` adicionado no Sprint I3c)
> - YAMLs de prompt: **13 arquivos** em `app/prompts/domains/` + `app/prompts/shared/`
> - Migrations Alembic: **35** (última: 035_add_user_agent_preferences)
> - Testes BE: **3.712+** | Coverage: **32,66%** (gate CI: 32%)
> - Sprints concluídos: A–F + G1–G7 + H + I + J

### 13C.17 Roteiros de Reprodução — Ordem Exata por Subsistema

> **REGRA:** Estes roteiros indicam a ORDEM DE LEITURA para entender e replicar cada subsistema. O dev deve ler os arquivos nesta sequência para construir um modelo mental correto antes de implementar.

#### Para reproduzir um agente ReAct (qualquer domínio):
```
1. app/shared/agents/react_agent_registry.py    ← como o agente é registrado
2. app/domains/{domain}/agents/{domain}_react_agent.py  ← lógica principal (herda EnhancedAgentMixin)
3. app/domains/{domain}/agents/{domain}_system_prompt.py ← prompt canônico (10 seções, ver 13B.2)
4. app/domains/{domain}/agents/{domain}_tool_registry.py ← tools disponíveis
5. app/domains/{domain}/agents/{domain}_stage_context.py ← estágios e transições
6. app/prompts/domains/{domain}.yaml             ← persona, scope_in, scope_out, behavioral_rules
7. app/prompts/shared/lia_persona.yaml           ← identidade LIA compartilhada
```

#### Para reproduzir o WSI (entrevista + scoring):
```
1. app/domains/cv_screening/services/wsi_screening_pipeline.py  ← pipeline principal (orquestra Blocks 2-5)
2. app/domains/cv_screening/agents/wsi_interview_graph.py       ← LangGraph StateGraph (entrevista)
3. app/domains/cv_screening/services/wsi_deterministic_scorer.py ← scoring 100% determinístico
4. app/domains/cv_screening/services/wsi_question_generator.py  ← geração por Bloom + Dreyfus
5. app/domains/cv_screening/services/calibration_profiles.py    ← perfis de calibração por área
6. app/domains/cv_screening/services/seniority_context_calibrator.py ← ajustes por contexto
7. app/domains/cv_screening/services/personalized_feedback_service.py ← feedback ao candidato
8. app/domains/cv_screening/services/rubric_evaluation_service.py ← avaliação por rubrica
```

#### Para reproduzir a comunicação inteligente:
```
1. app/domains/communication/services/communication_service.py     ← serviço principal
2. app/domains/communication/services/interpret_context_llm_service.py ← entende situação via LLM
3. app/domains/communication/services/infer_behavior_service.py    ← infere comportamento do candidato
4. app/domains/communication/services/communication_dispatcher.py  ← decide canal (email/WA/ambos)
5. app/domains/communication/services/email_service.py             ← envio de email
6. app/domains/communication/services/email_providers/resend_provider.py ← provider Resend
7. app/domains/communication/services/whatsapp_service.py          ← envio WhatsApp
8. app/domains/communication/services/whatsapp_meta_service.py     ← provider Meta API
9. app/domains/communication/services/email_templates_data.py      ← templates
10. app/domains/communication/services/transition_dispatch_service.py ← dispatch em transições
```

#### Para reproduzir o orquestrador:
```
1. app/orchestrator/orchestrator.py       ← ponto de entrada
2. app/orchestrator/intent_router.py      ← NLU — classifica intenção
3. app/orchestrator/fast_router.py        ← tentativa rápida sem LLM
4. app/orchestrator/cascaded_router.py    ← cascata: fast → cache → LLM (Haiku→Sonnet→Opus)
5. app/orchestrator/task_planner.py       ← decomposição de tarefas complexas
6. app/orchestrator/policy_engine.py      ← políticas de negócio (guardrails)
7. app/orchestrator/action_executor.py    ← execução de ações
8. app/orchestrator/pending_action.py     ← ações pendentes (HITL)
9. app/orchestrator/state_manager.py      ← estado entre turnos
```

#### Para reproduzir o sourcing inteligente:
```
1. app/domains/sourcing/agents/sourcing_react_agent.py  ← agente ReAct (14 tools)
2. app/domains/sourcing/services/sourcing_pipeline.py   ← pipeline principal
3. app/domains/sourcing/services/wrf_service.py         ← Work Requirements Framework
4. app/domains/sourcing/services/pre_wrf_filter.py      ← filtro pré-WRF
5. app/domains/sourcing/services/es_analyzer.py          ← Elasticsearch
6. app/domains/sourcing/services/pgv_analyzer.py         ← pgvector (busca semântica)
7. app/domains/sourcing/services/query_builders.py       ← construtores de query
8. app/domains/sourcing/services/pearch_service.py       ← Pearch AI (190M+ perfis)
```

#### Para reproduzir o HITL:
```
1. app/services/hitl_service.py                  ← HITLService (Redis + PostgreSQL)
2. app/models/hitl.py                            ← modelos (PendingAction + AuditTrail)
3. app/api/v1/hitl.py                            ← endpoint de aprovação
4. plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx ← card FE
5. plataforma-lia/src/hooks/use-float-streaming.ts ← streaming + HITL interception
```

#### Para entender os prompts:
```
1. app/prompts/shared/lia_persona.yaml           ← persona base LIA (tom, restrições)
2. app/prompts/shared/defensive.yaml             ← proteção contra jailbreak
3. app/prompts/shared/agent_prompts.yaml         ← prompts compartilhados entre agentes
4. app/prompts/domains/{domain}.yaml             ← prompts específicos por domínio
   Domínios disponíveis: cv_screening, job_management, sourcing, communication,
   automation, interview_scheduling, pipeline_transition, recruiter_assistant,
   analytics, ats_integration
5. app/shared/prompts/loader.py                  ← PromptLoader (carrega YAMLs com cache)
6. app/shared/prompts/templates.py               ← PromptTemplate + PromptLibrary
7. app/shared/prompts/cot.py                     ← ChainOfThoughtBuilder, CoTStrategy
8. app/shared/prompts/few_shot_examples.py       ← exemplos few-shot gerais
9. app/shared/prompts/intent_few_shot_examples.py ← exemplos few-shot do orquestrador
10. app/shared/prompts/prompt_registry.py        ← registry com busca por domínio/versão
11. app/shared/prompts/agent_prompts.py          ← system prompts compartilhados dos agentes
12. app/shared/prompts/examples/                 ← exemplos por domínio:
    - orchestrator_examples.py
    - job_planner_examples.py
    - sourcing_examples.py
    - pipeline_examples.py
13. app/domains/{domain}/agents/{domain}_system_prompt.py ← prompt canônico do agente

IMPORTANTE: app/prompts/ contém APENAS arquivos YAML.
           Implementações Python estão em app/shared/prompts/.
```

#### Para reproduzir provedores LLM:
```
1. app/services/llm.py                           ← serviço LLM de alto nível (955 linhas)
2. app/shared/providers/llm_factory.py           ← factory (Claude, OpenAI, Gemini)
3. app/shared/providers/llm_claude.py            ← provider Anthropic (primário)
4. app/shared/providers/llm_openai.py            ← provider OpenAI (fallback)
5. app/shared/providers/llm_gemini.py            ← provider Gemini (fallback + embeddings)
6. app/shared/intelligence/embedding_service.py  ← embeddings Gemini text-embedding-004
7. app/shared/intelligence/semantic_search_service.py ← busca semântica pgvector
```

---

## 13D. COMPLIANCE E FAIRNESS — REFERÊNCIA TÉCNICA PARA REPRODUÇÃO

> **Fonte:** `docs/GUIA_ARQUITETURA_IA_v1.0.md` — Seção 27 + Apêndice A
>
> Esta seção detalha a API, padrões e configuração dos módulos de compliance e fairness que devem ser wired nos fluxos Alpha 1 (ver gaps 10.2). Sem isso, os agentes funcionam mas **não cumprem os Inegociáveis do Guia v3.3**.

### 13D.1 FairnessGuard — 3 Camadas

**Arquivo:** `app/shared/compliance/fairness_guard.py`

| Camada | Mecanismo | Latência | Ativação |
|--------|-----------|:--------:|----------|
| **1 — Regex** | 40+ padrões (gênero, raça, idade, religião, estado civil, maternidade/paternidade, deficiência) | ~0ms | Sempre ativa |
| **2 — Léxico implícito** | Detecta linguagem indiretamente discriminatória (ex: "jovem e dinâmico" → flag idade) | ~0ms | Sempre ativa |
| **3 — LLM (opt-in)** | Análise contextual de casos ambíguos via LLM | ~2s | `FAIRNESS_LAYER3_ENABLED=True` |

**Padrão regex faixa etária (exemplo):** `r"\bde\s+\d+\s+(a|até|ate)\s+\d+\s+anos\b"`

**API de uso:**
```python
result = await fairness_guard.check(text, context)
result = await fairness_guard.check_explicit_bias(text)  # alias

result.is_biased          # bool
result.categories         # list de categorias detectadas
result.flagged_patterns   # patterns específicos
result.recommendation     # sugestão de correção
```

**Onde deve ser wired (Alpha 1):**
- `pipeline_react_agent.py` — antes de scoring/triagem (Ag.3)
- `sourcing_react_agent.py` — na validação de queries de busca (Ag.2)
- `wizard_react_agent.py` — na geração/edição de JD (Ag.1)
- `validate_policy_compliance` — tool do HiringPolicyService (Ag.10)

### 13D.2 Bias Audit API

**Arquivo:** `app/services/bias_audit_service.py`

**Método:** Four-Fifths Rule em 4 dimensões:

| Dimensão | Métrica |
|----------|---------|
| `gender` | adverse_impact_ratio = menor_grupo / maior_grupo |
| `age_group` | adverse_impact_ratio |
| `disability` | adverse_impact_ratio |
| `region` | adverse_impact_ratio |

**Flag:** ratio < 0.80 (regra 4/5 — NYC LL144 + EU AI Act)

**Endpoints:**
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| GET | `/api/v1/bias-audit/job/{job_id}` | Auditoria atual |
| GET | `/api/v1/bias-audit/job/{job_id}/history` | Histórico de snapshots |

**Snapshots auditáveis:**
- Modelo: `app/models/bias_audit_snapshot.py` (BiasAuditSnapshot)
- Migration: `018_add_bias_audit_snapshot.py`
- Compliance: SOX / ISO 27001 (histórico imutável)

**Admin UI:** `plataforma-lia/src/app/admin/compliance/auditoria/bias/page.tsx`

### 13D.3 LGPD — Implementações Ativas

#### Footer de IA em emails
**Arquivo:** `app/shared/channels/adapters/email_adapter.py`
```python
AI_GENERATED_FOOTER = "Esta comunicação foi gerada por IA..."
# Aplicado automaticamente quando message.ai_generated=True
```

#### Campos de consentimento granular
**Arquivo:** `app/models/communication_settings.py`

| Campo | Finalidade |
|-------|-----------|
| `DATA_SHARING_EMAIL_PROVIDERS` | Consentimento para SendGrid/Mailgun/Resend |
| `DATA_SHARING_SMS_PROVIDERS` | Consentimento para Twilio |
| `AI_GENERATED_COMMUNICATIONS` | Consentimento para comunicações de IA |

#### Human Review Sampling (5%)
**Arquivo:** `app/services/human_review_sampling_service.py`
- Determinístico por MD5 hash — mesma decisão sempre cai na mesma categoria
- **ALWAYS_REVIEW (100%):** `finalize_hiring`, `mass_rejection`, `fairness_flagged`
- **Sampling (5%):** demais decisões de IA

#### Data Request / Consent
| Arquivo | Função |
|---------|--------|
| `app/api/v1/data_request.py` | Pedidos de dados (LGPD Art. 18) |
| `app/api/v1/consent_management.py` | Gestão de consentimento (LGPD Art. 7) |

### 13D.4 Compliance Enterprise (BCB-498 / SOX / ISO 27001)

| Arquivo | Função | Framework |
|---------|--------|-----------|
| `app/api/v1/compliance_controls.py` | Controles SOX/ISO | SOX + ISO 27001 |
| `app/api/v1/audit_logs.py` | Logs de auditoria imutáveis | SOX + ISO 27001 |
| `app/api/v1/trust_center.py` | Portal trust center | Todos |
| `app/models/bias_audit_snapshot.py` | Snapshots auditáveis | SOX + ISO 27001 |
| `app/shared/compliance/audit_service.py` | Serviço de auditoria | Todos |

> **Para Alpha 1:** Compliance enterprise (BCB-498/SOX/ISO) é desejável mas não bloqueante. Os módulos críticos são: FairnessGuard (wiring), Consent (validação), PII Masking (ativação), Audit Trail (wiring nos Gates) e Human Review Sampling (ativação). Ver seção 10.2 para gaps e prioridades.

**Arquivos adicionais em `app/shared/compliance/` (verificados no codebase):**

| Arquivo | Papel | Alpha 1 |
|---------|-------|:-------:|
| `app/shared/compliance/audit_callback.py` | AuditCallback — callback LangGraph que registra cada decisão | ✅ |
| `app/shared/compliance/audit_writer.py` | AuditWriter — persiste logs de auditoria no banco | ✅ |
| `app/shared/compliance/audit_storage.py` | AuditStorage — interface de armazenamento de audits | ✅ |
| `app/shared/compliance/audit_models.py` | Modelos de dados dos eventos de auditoria | ✅ |
| `app/shared/compliance/fact_checker.py` | FactChecker — verifica consistência de claims do agente | ✅ |

### 13D.5 Guardrails em Banco de Dados — Modelo, Repositório e Seed

> Estes 13 guardrails são os **Inegociáveis do Guia v3.3 codificados em DB**. O seed deve rodar no setup de todo novo tenant. Os guardrails são carregados pelo `GuardrailRepository` com prioridade 3-tier (global → tenant → domínio) e validados em runtime por cada agente via `BaseAgent.check_guardrails()`.

#### Modelo
**Arquivo:** `app/models/guardrail.py`

```python
class Guardrail(Base):
    __tablename__ = "guardrails"
    id              = Column(UUID, primary_key=True)
    level           = Column(String(20))     # "primary" | "secondary"
    domain          = Column(String(50))     # NULL = todos os domínios
    node            = Column(String(50))     # NULL = todos os nós
    tool            = Column(String(50))     # NULL = todas as tools
    rule            = Column(Text)           # A regra em linguagem natural
    blocking_message = Column(Text)          # Mensagem se bloqueado
    is_active       = Column(Boolean)
    company_id      = Column(UUID)           # NULL = global
    updated_by      = Column(String)
    updated_at      = Column(TIMESTAMP)
```

#### Repositório — Prioridade 3-Tier
**Arquivo:** `app/shared/compliance/guardrail_repository.py`

| Prioridade | Filtro | Escopo |
|:----------:|--------|--------|
| 1 | `level=primary`, `domain=None`, `company_id=None` | Guardrails primários globais (LGPD/fairness) |
| 2 | `level=primary`, `domain=None`, `company_id=X` | Guardrails primários do tenant |
| 3 | `level=secondary`, `domain=Y`, `company_id=None` | Guardrails secundários globais do domínio |
| 4 | `level=secondary`, `domain=Y`, `company_id=X` | Guardrails secundários do tenant para o domínio |

```python
guardrails = await GuardrailRepository.get_active(
    db=db,
    domain="sourcing",      # domínio do agente
    company_id=company_id   # tenant atual
)
```

#### Seed Inicial (13 guardrails)
**Arquivo:** `app/core/seeds/guardrails_seed.py`

#### Guardrails Globais (6) — LGPD + Fairness

| # | Guardrail | Escopo | Compliance |
|:-:|-----------|--------|-----------|
| 1 | Nunca revelar informações pessoais de candidatos não compartilhadas explicitamente | Todos os agentes | LGPD Art. 46 |
| 2 | Nunca discriminar por gênero, raça, idade, religião ou estado civil | Todos os agentes | FairnessGuard + EU AI Act |
| 3 | Sempre identificar comunicação gerada por IA quando solicitado | Communication (Ag.7) | LGPD Art. 6 + EU AI Act Art. 52 |
| 4 | Nunca criar perguntas que impliquem questões familiares, filhos ou vida pessoal | WSI Interview (Ag.4+5) | CLT Art. 373-A + FairnessGuard |
| 5 | Não tomar decisões finais de rejeição sem revisão humana habilitada | Pipeline (Ag.9) | EU AI Act Art. 14 (HITL) |
| 6 | Registrar auditoria completa de todas as avaliações automatizadas | Todos os agentes | SOX + ISO 27001 + LGPD Art. 37 |

#### Guardrails por Domínio (7) — Regras Específicas

| # | Domínio | Guardrail | Agente |
|:-:|---------|-----------|--------|
| 7 | `wsi_interviewer` | Perguntas exclusivamente sobre competências profissionais | Ag.4+5 (WSI) |
| 8 | `wsi_interviewer` | Não interromper candidato durante resposta | Ag.4+5 (WSI) |
| 9 | `communication` | Todo email deve incluir identificação de IA no rodapé | Ag.7 (Communication) |
| 10 | `sourcing` | Não contatar candidatos já recusados nos últimos 6 meses | Ag.2 (Sourcing) |
| 11 | `pipeline` | Gate humano obrigatório antes de rejeição em massa | Ag.9 (Pipeline) |
| 12 | `analytics` | Nunca expor dados individuais em relatórios agregados | Ag.13 (Analytics) |
| 13 | `policy` | Alterações em políticas requerem confirmação explícita do usuário | Ag.10 (HiringPolicy) |

**Para rodar o seed:**
```bash
python -c "from app.core.seeds.guardrails_seed import run_seed; import asyncio; asyncio.run(run_seed(db))"
```

**Dependências Alpha 1:**
- Os 6 guardrails globais devem estar ativos desde o Sprint 0 (infra compartilhada)
- Os guardrails de domínio (#7-#13) devem ser ativados quando o respectivo agente entrar em operação
- O `PolicyEngine` carrega guardrails ativos do DB e os injeta no contexto de cada execução de agente

---

## 13E. DOCUMENTAÇÃO DISPONÍVEL NO CODEBASE LIA (verificada)

| Documento | Path | Tamanho | Conteúdo |
|-----------|------|---------|----------|
| Guia Arquitetura IA v1.0 | `docs/GUIA_ARQUITETURA_IA_v1.0.md` | — | Fonte citada nas seções 13B e 13D |
| AI Architecture Audit | `docs/ai-architecture-audit.md` | 516 KB | Auditoria completa da arquitetura de IA |
| Mapa Camada Inteligência | `docs/MAPA_CAMADA_INTELIGENCIA.md` | 329 KB | Mapa detalhado da camada de inteligência |
| Conceitos IA WeDOTalent | `docs/CONCEITOS_IA_WEDOTALENT.md` | 180 KB | Conceitos e fundamentos da IA da plataforma |
| Plano Ciclo Fechado LIA | `docs/PLANO_CICLO_FECHADO_LIA.md` | — | Plano de ciclo fechado da LIA |
| Domain Verification Report | `docs/fase2c_domain_verification_report.md` | — | Relatório de verificação dos domínios |
| Metodologia WSI | `docs/WSI_METHODOLOGY_REFERENCE.md` | — | Referência da metodologia WSI |

---

## 13F. FRONTEIRA IA vs. DETERMINÍSTICO — GUIA DE DECISÃO

> **Quando usar LLM e quando usar código?** Esta seção define o mapa de decisões para o time de desenvolvimento. Toda feature nova deve ser classificada antes de implementar.

### Mapa de Decisões: O que é IA vs Determinístico

```
┌──────────────────────────────────────────────────────────────────┐
│              IA vs DETERMINÍSTICO — MAPA COMPLETO                │
│                                                                  │
│  DECISÕES 100% LLM:                                              │
│  ├─ Intent classification (o que o recrutador quer fazer)       │
│  ├─ Geração de Job Description (a partir de dados da vaga)      │
│  ├─ Análise de CV e extração de dados não estruturados          │
│  ├─ WSI scoring qualitativo (blocos comportamentais, STAR)      │
│  ├─ Geração de perguntas de triagem personalizadas              │
│  ├─ Sugestões de competências e skills complementares           │
│  ├─ Análise de fit cultural                                     │
│  ├─ Geração de comunicações personalizadas (email, feedback)    │
│  ├─ Análise multimodal (vídeo, imagem, transcrição de voz)      │
│  └─ Predição de sub-status de pipeline (probabilidade)          │
│                                                                  │
│  DECISÕES HÍBRIDAS (IA + Regras determinísticas):               │
│  ├─ Roteamento: Memory Cache → Regex → LLM (cascata 6 tiers)   │
│  ├─ WSI scoring quantitativo: LLM extrai dados + Algoritmo soma │
│  ├─ Busca de candidatos: WRF (pesos determinísticos) + embedds  │
│  ├─ Personalização: histórico estatístico + LLM ajusta tom      │
│  ├─ Automação pipeline: triggers determinísticos + LLM prediz   │
│  └─ Cache semântico: cosine similarity (math) + LLM (fallback)  │
│                                                                  │
│  DECISÕES 100% DETERMINÍSTICAS (sem LLM):                       │
│  ├─ Autenticação e autorização (JWT + RBAC)                     │
│  ├─ FairnessGuard Camada 1 (regex pattern matching)             │
│  ├─ FactChecker (validação numérica com ranges fixos)           │
│  ├─ Rate limiting e PolicyEngine (contadores + limites)         │
│  ├─ Retenção LGPD (dias fixos por tipo de dado)                 │
│  ├─ Pipeline state machine (transições válidas hardcoded)       │
│  ├─ Multi-tenancy isolation (company_id filter em toda query)   │
│  ├─ Token tracking e billing (contagem exata)                   │
│  └─ Feature flags (boolean per tenant)                          │
└──────────────────────────────────────────────────────────────────┘
```

### Regra de Ouro por Nível de Garantia

| Nível | Onde fica | Como funciona | Confiabilidade | Usar para |
|-------|-----------|---------------|---------------|-----------|
| **Soft** | System Prompt | Instrução textual ao LLM | Baixa — LLM pode ignorar | Tom, formato, sugestões |
| **Médio** | Stage Context | Contexto injetado por estágio | Média — orienta o LLM | Foco da conversa, contexto |
| **Hard** | Tool Code (Python) | Código executado, não depende do LLM | Alta — garantido | Compliance, autenticação, billing |

> **Regra:** Para qualquer regra crítica de negócio (compliance, segurança, multi-tenancy), use nível **Hard** (código na tool). Prompts orientam — código garante.

### Critério de Decisão: Usar LLM ou não?

```
Para uma nova feature, pergunte:

1. A saída precisa ser DETERMINÍSTICA e AUDITÁVEL? → Código puro
   (ex: calcular score, validar CPF, filtrar por company_id)

2. A saída envolve LINGUAGEM NATURAL ou RACIOCÍNIO? → LLM
   (ex: gerar JD, analisar CV, responder candidato)

3. A saída mistura dados estruturados + interpretação? → Híbrido
   (ex: WSI score = LLM analisa resposta + algoritmo calcula nota)

4. A regra é de COMPLIANCE ou SEGURANÇA? → SEMPRE código (Hard)
   (ex: FairnessGuard, PII Masking, rate limiting)
```

### Human-in-the-Loop Checkpoints — Quando Confirmar

| Ação | Requer HITL? | Motivo | Quem aprova |
|------|:----------:|--------|-------------|
| Envio de email em massa | ✅ SIM | Comunicação irreversível | Recrutador |
| Rejeição de candidato | ✅ SIM | Decisão final negativa | Recrutador |
| Publicação de vaga | ✅ SIM | Exposição pública | Recrutador |
| Movimentação de pipeline | ✅ SIM | Mudança de etapa | Recrutador |
| Agendamento de entrevista | ✅ SIM | Compromisso com candidato | Recrutador |
| Envio via WhatsApp | ✅ SIM | Comunicação direta | Recrutador |
| Geração de JD | ❌ NÃO | Preview antes de publicar | — |
| Scoring WSI | ❌ NÃO | Informativo, não é ação | — |
| Busca de candidatos | ❌ NÃO | Apenas listagem | — |
| Sugestões de skills | ❌ NÃO | Sugestão editável pelo usuário | — |

> **Princípio:** Toda ação que causa efeito externo (envia, publica, rejeita, agenda) requer confirmação humana. Ações informativas (score, busca, sugestão) são automáticas.

---

## 13G. ARQUITETURA DOS 3 NÍVEIS DE CHAT — ESCOPOS, DECISÃO E ENDPOINTS

> **Fonte:** `relatorio_capacidades_prompts_lia.md` seção 1 + investigação direta de `scope_config.py`, `orchestrated_talent_chat.py`, `orchestrated_job_chat.py`
>
> **Por que esta seção existe:** O diagnóstico v3.0 não documentava como os 3 pontos de contato do chat (Float, Kanban, Full) se conectam ao backend, quais ferramentas cada um tem acesso, e como a decisão "processar localmente vs delegar ao orquestrador" é tomada no frontend. Esta informação é crítica para entender o escopo real de cada agente.

### 13G.1 Os 3 Níveis de Chat

| Chat | Localização Frontend | Escopo (`scope_config.py`) | Endpoint Backend | Backend File |
|------|---------------------|---------------------------|-----------------|-------------|
| **Float Chat** | `candidates-page.tsx` | `TALENT_FUNNEL` (20 tools) | `POST /orchestrator/talent-chat` | `orchestrated_talent_chat.py` |
| **Kanban Chat** | `job-kanban-page.tsx` | `IN_JOB` (25 tools) | `POST /orchestrator/job-chat` | `orchestrated_job_chat.py` |
| **Chat Full** | `chat-page.tsx` | `GLOBAL` (2 tools) | `POST /orchestrator/process` + WebSocket | `orchestrator.py` |

### 13G.2 Escopos Detalhados (`app/tools/scope_config.py`)

**TALENT_FUNNEL (20 tools):**
- Query (11): `search_candidates`, `get_candidate_details`, `get_candidate_stats`, `compare_candidates`, `get_talent_quality`, `get_talent_engagement`, `get_talent_availability`, `get_diversity_metrics`, `get_candidate_history`, `get_ml_predictions`, `get_conversion_patterns`
- Action (9): `add_candidate_to_vacancy`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `send_email`, `send_whatsapp`, `send_bulk_email`, `export_candidates`

**IN_JOB (25 tools):**
- Query (14): `get_job_details`, `get_vacancy_funnel`, `get_candidate_details`, `get_activity_summary`, `get_pending_actions`, `compare_candidates`, `get_candidate_stats`, `get_bottleneck_analysis`, `get_job_velocity`, `get_job_quality_metrics`, `get_stakeholder_metrics`, `get_prediction_metrics`, `get_job_benchmark`, `get_smart_alerts`
- Action (11): `update_candidate_stage`, `bulk_update_candidates_stage`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `wsi_screening`, `send_email`, `send_whatsapp`, `schedule_interview`, `send_feedback`

**GLOBAL (2 tools):**
- `generate_report`, `schedule_report`
- Todas as mensagens vão ao Orchestrator.process_request() com escopo completo (o scope GLOBAL no config limita tools, mas o orchestrator roteia para o agente correto que tem suas próprias tools)

### 13G.3 Fluxo de Decisão Frontend — Float Chat

```
1. Mensagem recebida → normalizar
2. Verificar se é COMANDO DE ANÁLISE (analysisCommands[]):
   - "analisar potencial", "resumo executivo", "top 5", "comparar", etc.
   → Se sim: handleAICommand(message) [processamento IA via backend]
3. Verificar se é PERGUNTA GENÉRICA (isGenericQuestion()):
   - Regex: /^(o que|como|por que|quando|onde|quem|quanto)/, /?$/
   - EXCETO se contém searchKeywords (46 termos): "desenvolvedor", "python", "react", etc.
   → Se é pergunta genérica SEM keywords: handleOrchestratedTalentMessage() → backend
4. Senão: executar como BUSCA DE CANDIDATOS via executeSearch()
```

**`isGenericQuestion()` (candidates-page.tsx, ~linha 5617):**
- Input: texto do usuário
- Processing: regex de padrões interrogativos + ausência de 46 keywords de busca
- Output: boolean — true se é pergunta genérica (vai para orquestrador), false se é busca
- Keywords: cargos (desenvolvedor, gerente, analista...), tecnologias (python, react, node...), localidades (são paulo, remoto...), senioridades (junior, pleno, senior...)

### 13G.4 Fluxo de Decisão Backend — Kanban Chat

```
1. Request recebida com job_context + candidates + message
2. Backend detecta command_type via detect_command_type(message) → KanbanCommandType
3. Se command_type ∈ _ANALYTICAL_COMMAND_TYPES (12 tipos): análise IA
4. Se command_type ∈ ACTIONABLE_INTENTS: executa ação via ActionExecutor
5. Se é confirmação/rejeição de ação pendente: resolve via PendingActionStore
6. Senão: roteia para Orchestrator.process_request() com contexto enriquecido
```

### 13G.5 Diagrama de Interação Consolidado

```
┌─────────────────────────────────────────────────────────┐
│  Float Chat (candidates-page)                           │
│  Escopo: TALENT_FUNNEL (20 tools)                       │
│  Decisão: isGenericQuestion() → orquestrador            │
│           analysisCommands → handleAICommand             │
│           default → executeSearch (busca candidatos)     │
│  → callOrchestratedTalentChat() → /orchestrator/talent-chat │
├─────────────────────────────────────────────────────────┤
│  Kanban Chat (job-kanban-page)                          │
│  Escopo: IN_JOB (25 tools)                              │
│  Decisão: detect_command_type() → KanbanCommandType     │
│           analytical → análise IA                        │
│           actionable → ActionExecutor                    │
│  → callOrchestratedJobChat() → /orchestrator/job-chat    │
├─────────────────────────────────────────────────────────┤
│  Chat Full (chat-page)                                  │
│  Escopo: GLOBAL (2 tools, mas orchestrator completo)    │
│  → liaApi.orchestratorProcess() → /orchestrator/process  │
│  (+ WebSocket wsSendMessage)                            │
└──────────────────────────┬──────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Orchestrator │
                    │ + CascadedR. │
                    └──────┬──────┘
                           │ domain dispatch
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        [11 Agentes ReAct via LangGraph]
```

### 13G.6 Estado do Float / Super Prompt

Gerenciado via `LiaFloatContext` (`src/contexts/lia-float-context.tsx`):
- `isOpen` / `isExpanded` — Float mini vs. Super Prompt expandido
- `expand()` / `collapse()` — Transição entre modos
- `sharedMessages` — Mensagens compartilhadas entre mini e expandido

---

## 13H. ACTIONEXECUTOR CLOSED-LOOP + PENDINGACTIONSTORE (HITL VIA CHAT)

> **Fonte:** `relatorio_capacidades_prompts_lia.md` seção 7.4 + investigação de `app/orchestrator/action_executor.py` e `app/orchestrator/pending_action.py`

### 13H.1 Conceito

O `ActionExecutor` implementa um loop fechado de execução de ações pelo chat, sem necessidade de modais ou interfaces separadas. Quando o usuário pede uma ação (mover candidato, enviar email, etc.), a LIA propõe a ação com `needs_confirmation: true` e aguarda confirmação.

### 13H.2 Ações Suportadas

| Ação | Método | Descrição |
|------|--------|-----------|
| `move_candidate` | `ActionExecutor.move_candidate()` | Move candidato entre etapas do pipeline |
| `send_email` | `ActionExecutor.send_email()` | Envia email individual |
| `start_screening` | `ActionExecutor.start_screening()` | Inicia triagem WSI comportamental |
| `schedule_interview` | `ActionExecutor.schedule_interview()` | Agenda entrevista |
| `request_data` | `ActionExecutor.request_data()` | Solicita dados adicionais ao candidato |
| `analyze_profile` | `ActionExecutor.analyze_profile()` | Executa análise aprofundada do perfil |
| `approve_candidate` | `ActionExecutor.approve_candidate()` | Aprova candidato para próxima etapa |

### 13H.3 Fluxo HITL via Chat

```
1. Usuário pede ação: "Mova o João Silva para Entrevista Técnica"
2. LIA detecta intent → ActionExecutor identifica ação
3. LIA responde com needs_confirmation: true + detalhes da ação
4. Resposta ao usuário: "📋 Confirmação necessária: Mover João Silva de Triagem para Entrevista Técnica. Confirma?"
5. Usuário confirma → PendingActionStore resolve ação
6. ActionExecutor executa ação real no backend
7. LIA responde: "✅ João Silva movido para Entrevista Técnica! Próximo passo sugerido: Agendar entrevista."
```

### 13H.4 Arquivos

| Arquivo | Papel |
|---------|-------|
| `app/orchestrator/action_executor.py` | Execução das 7 ações com validação e feedback |
| `app/orchestrator/pending_action.py` | Store de ações pendentes (in-memory por sessão) |
| `app/api/v1/orchestrated_job_chat.py` | Integração com ActionExecutor no endpoint Kanban |
| `app/api/v1/orchestrated_talent_chat.py` | Integração com ActionExecutor no endpoint Float (v3.0) |

---

## 13I. TEMPLATES DE RESPOSTA — KANBAN (18) + ANALYTICS (8) + FLOAT

> **Fonte:** `relatorio_capacidades_prompts_lia.md` seções 4.1, 4.2, 4.3

### 13I.1 Kanban — 18 Command Templates

**Arquivo:** `app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`

| # | Comando | Tipo | Descrição |
|---|---------|------|-----------|
| 1 | `rankear_candidatos` | Análise IA | Ranking com score_fit, forças, gaps, justificativa |
| 2 | `performance_funil` | Análise IA | Métricas do pipeline: total, por etapa, conversão, benchmark |
| 3 | `gargalos_processo` | Análise IA | Gargalos com tipo, impacto, recomendação, prioridades |
| 4 | `comparar_candidatos` | Análise IA | Comparativo detalhado multi-dimensional |
| 5 | `resumir_perfil` | Análise IA | Resumo executivo completo do candidato |
| 6 | `candidatos_ativos` | Query local | Lista candidatos ativos na vaga |
| 7 | `taxa_conversao` | Query local | Taxa de conversão por etapa |
| 8 | `tempo_medio` | Query local | Tempo médio por etapa do pipeline |
| 9 | `candidatos_parados` | Query local | Candidatos sem movimentação recente |
| 10 | `top_candidatos` | Análise IA | Top candidatos por score/fit |
| 11 | `mover_candidato` | Ação | Via ActionExecutor.move_candidate() |
| 12 | `enviar_email` | Ação | Via ActionExecutor.send_email() |
| 13 | `disparar_triagem` | Ação | Via ActionExecutor.start_screening() |
| 14 | `agendar_entrevista` | Ação | Via ActionExecutor.schedule_interview() |
| 15 | `solicitar_dados` | Ação | Via ActionExecutor.request_data() |
| 16 | `analisar_perfil` | Análise IA | Análise aprofundada com recomendações |
| 17 | `aprovar_candidato` | Ação | Via ActionExecutor.approve_candidate() |
| 18 | `analise_geral` | Análise IA | Análise geral do pipeline (fallback default) |

Cada template inclui: `keywords[]`, `prompt_template` (com placeholders `{job_context}`, `{candidates_context}`, `{pipeline_context}`), `response_sections[]`, `follow_up_prompts[]`.

Fallback offline: Templates de análise retornam dados do banco local quando LLM falha. Templates de ação retornam: "Desculpe, ocorreu um erro ao processar sua requisição."

### 13I.2 Job Analytics — 8 Command Templates

**Arquivo:** `app/domains/analytics/services/job_analytics_prompt_service.py`

| # | Comando | Agente Executor | Descrição |
|---|---------|-----------------|-----------|
| 1 | `funnel_analysis` | Analytics | Análise do funil: candidatos por etapa, conversão, gargalos, tempo médio |
| 2 | `comparative_analysis` | Analytics | Comparação entre vagas: tempo, conversão, qualidade |
| 3 | `bottleneck_detection` | Analytics | Gargalos: tempo de espera, candidatos parados, ações pendentes |
| 4 | `time_to_fill_prediction` | Analytics | Previsão de tempo para preencher a vaga |
| 5 | `candidate_quality_score` | Pipeline | Qualidade dos candidatos: fit técnico, cultural, diversidade |
| 6 | `sourcing_effectiveness` | Sourcing | Efetividade do sourcing: melhores canais, custo por candidato |
| 7 | `weekly_summary` | Analytics | Resumo semanal: novos candidatos, movimentações, entrevistas |
| 8 | `salary_benchmark` | Wizard | Benchmark salarial: competitividade, ajustes |

Fallback offline: Se agente IA falha, retorna `{"success": false, "error": str(e)}` — sem template offline alternativo.

### 13I.3 Float Chat — Comandos de Análise

**Detecção via `analysisCommands[]` (candidates-page.tsx):**

| Comando | Ação |
|---------|------|
| "analisar potencial" | Análise de potencial de crescimento via IA |
| "resumo executivo" | Resumo executivo dos resultados de busca |
| "resumir busca" | Resumo consolidado da busca |
| "top 5" / "top5" | Top 5 melhores candidatos |
| "comparar" | Comparação entre candidatos selecionados |
| "pontos a desenvolver" | Pontos de desenvolvimento |
| "vagas ideais" | Tipos de vagas adequadas |
| "definir tipo" | Classificação de tipo de perfil |

---

## 13J. SISTEMA PREDITIVO E INSIGHTS — INVENTÁRIO COMPLETO

> **Fonte:** `relatorio_capacidades_prompts_lia.md` seção 6 + investigação de `app/services/predictive_analytics_service.py`

### 13J.1 Ferramentas Preditivas (Analytics Agent)

| Ferramenta | Input | Processing | Output | Surfacing UI |
|------------|-------|------------|--------|-------------|
| `get_prediction_metrics` | `job_id`, `time_range` | Query histórico + modelo de regressão | Previsões de hiring (prazo, prob.) | Analytics dashboard, Chat |
| `get_ml_predictions` | `job_id`, `model_type` | Modelo ML treinado em dados da empresa | Previsões com confidence intervals | Analytics dashboard |
| `get_conversion_patterns` | `job_id`/`company_id` | Análise de padrões no funil | Taxas de conversão por etapa/fonte | JobReportModal, Chat |
| `get_smart_alerts` | `company_id`, `threshold` | Detecção de anomalias e tendências | Lista de alertas com severidade | Dashboard, SaturationBadge |
| `get_trends` | `metric`, `time_range` | Séries temporais de métricas | Tendências com visualização | Analytics dashboard |
| `get_bottleneck_analysis` | `job_id` | Análise de tempos por etapa | Gargalos + recomendações | Kanban Chat, Dashboard |

### 13J.2 Predições Específicas

| Predição | Dados Utilizados | Endpoint/Serviço | Surfacing UI |
|----------|------------------|-------------------|-------------|
| Probabilidade de contratação | Histórico vagas similares, pool atual | `predictive_analytics_service.py` | Chat, Analytics |
| Time-to-Fill (TTF) | Tempos por etapa, velocidade pipeline | `time_to_fill_prediction` command | Chat, JobReportModal |
| Risco de dropout | Tempo parado, engajamento, mercado | `get_smart_alerts` + `EWS` | SaturationBadge, Alertas |
| Previsão de pipeline | Conversão histórica, volume atual | `get_ml_predictions` | Analytics dashboard |
| Predição salarial | Mercado, cargo, localização, senioridade | `get_intelligent_salary` / `salary_benchmark` | Wizard, Chat |

### 13J.3 Serviços de Inteligência Operacional (8 serviços)

| # | Serviço | Tipo | Dados Utilizados | Surfacing UI |
|---|---------|------|------------------|-------------|
| 1 | Pipeline Velocity Engine | Local (query) | Timestamps de movimentação por etapa | Kanban page, Analytics dashboard |
| 2 | Zero-Touch Scheduling | IA + Local | Disponibilidade, preferências, SLAs | Communication Agent, Calendar API |
| 3 | Silver Medalists | IA (matching) | Histórico de candidatos rejeitados | Sourcing Agent, ProactiveInsightCard |
| 4 | Recruiter Intelligence | Local (metrics) | Volume, velocidade, qualidade | Analytics dashboard |
| 5 | Early Warning Score (EWS) | IA (anomaly) | Pipeline metrics, tempos, saturação | SaturationBadge, SmartAlerts |
| 6 | Journey Intelligence | Local + IA | Touchpoints do candidato | Kanban page |
| 7 | Recruiter Perf. Benchmark | Local (metrics) | KPIs comparativos entre recrutadores | Analytics dashboard |
| 8 | Pipeline Prediction | IA (ML model) | Dados históricos vagas similares | JobReportModal, Analytics |

### 13J.4 Response Cache Service

- Cache de respostas para intents analíticas recorrentes
- `generate_cache_key()`: intent + contexto + mensagem + company_id
- Invalidação por entidade: `invalidate_for_job()`, `invalidate_for_candidate()`, `invalidate_for_company()`
- Invalidação por padrão regex: `invalidate_by_pattern()`
- **Arquivo:** `app/services/response_cache_service.py`

---

## 13K. QUICK ACTIONS E AÇÕES BULK — INVENTÁRIO COMPLETO

> **Fonte:** `relatorio_capacidades_prompts_lia.md` seção 7

### 13K.1 Quick Actions do Chat Full (chat-page.tsx)

| Quick Action | Mensagem Enviada |
|-------------|-----------------|
| Criar nova vaga | `"Criar uma nova vaga"` |
| Solicitar aprovação | `"Solicite aprovação de nova vaga"` |
| Compartilhar com gestor | `"Compartilhe candidatos com gestor"` |
| Solicitar feedback | `"Solicite feedback de entrevista"` |
| Consultar candidato | `"Consulte informações sobre candidato"` |
| Adicionar candidato | `"Adicione novo candidato"` |
| Reagendar entrevista | `"Reagende uma entrevista"` |
| Agendar entrevista (contextual) | `"agendar entrevista"` |
| Avaliar fit técnico | `"avaliar fit técnico do candidato"` |
| Gerar email follow-up | `"gerar email de follow-up"` |
| Enviar WhatsApp | `"enviar mensagem whatsapp"` |
| Comparar perfis | `"comparar perfis de candidatos"` |

### 13K.2 Ações Bulk — Funil de Talentos (UnifiedBulkActionsBar)

**Arquivo:** `plataforma-lia/src/components/ui/unified-bulk-actions-bar.tsx`

| # | Ação | Prop | Disponível em Funil | Disponível em Kanban |
|---|------|------|---------------------|----------------------|
| 1 | Mover etapa | `onMoveStage` | Sim | Sim |
| 2 | Rejeitar | `onReject` | Sim | Sim |
| 3 | Enviar email | `onEmail` | Sim | Sim |
| 4 | Agendar entrevista | `onSchedule` | Sim | Sim |
| 5 | Adicionar a vaga | `onAddToVacancy` | Sim | Sim |
| 6 | Mover para lista | `onMoveToList` | Sim | Sim |
| 7 | Exportar | `onExport` | Sim | Sim |
| 8 | Esconder | `onHide` | Sim | Sim |
| 9 | Triagem WSI | `onWSIScreening` | Sim | Sim |

### 13K.3 Ações Contextuais — ContextualActionsBanner

**Arquivo:** `plataforma-lia/src/components/contextual-actions-banner.tsx`

| # | Ação |
|---|------|
| 1 | Mover etapa |
| 2 | Rejeitar |
| 3 | Enviar email |
| 4 | Agendar entrevista |
| 5 | Adicionar a vaga |
| 6 | Mover para lista |
| 7 | Esconder |
| 8 | Triagem WSI |

---

## 14. CATÁLOGO POR AGENTE — BLOCO COMPLETO

Cada bloco contém TUDO que o agente precisa para funcionar: tipo, arquivos, tools, serviços, endpoints, automações, graphs, gaps V5 aplicáveis, conformidade com o shell padrão (seção 13B), roteiro de reprodução (seção 13C.17), e o que fazer para Alpha 1.

> **Legenda de tags:**
> - **[ALPHA 1]** = entra no escopo do Alpha 1 MVP
> - **[PÓS-ALPHA]** = não entra no Alpha 1, implementar depois
> - **Agente LIA** = arquivo de referência no nosso codebase (`lia-agent-system/`)
> - **V5 Correspondente** = arquivo correspondente no codebase V5 (`talensestg/recruiter_agent_v5`)
> - **Shell Padrão** = conformidade com o blueprint da seção 13B
> - **Roteiro de Reprodução** = ordem de leitura para replicar (seção 13C.17)

---

### 14.1 MainOrchestrator (Ag.0) [ALPHA 1]
**Tipo:** Orchestrator (não é ReAct nem Graph — routing + task planning)
**Padrão Arquitetural:**
- **NEM ReAct NEM LangGraph** — é orquestrador central com `CascadedRouter` (6 tiers)
- Recebe mensagem → classifica intent (T1:Cache → T2:FastRouter regex → T3:LLM few-shot) → roteia para agente do domínio
- `TaskPlanner` decompõe intents complexos em multi-step
- `PendingActions` gerencia confirmações multi-turn (HITL inline)
- V5: `DomainOrchestrator` (2 domínios, sem tiers) — precisa ser reconstruído seguindo padrão LIA

**Prioridade Alpha 1:** P0 (Sprint 0)
**Agente LIA:** `app/orchestrator/main_orchestrator.py`
**V5 Correspondente:** `src/orchestrator/main_orchestrator.py` + `cascaded_router.py` (mesma arquitetura)

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/orchestrator/main_orchestrator.py` | Orquestrador principal |
| `app/orchestrator/orchestrator.py` | Core logic |
| `app/orchestrator/cascaded_router.py` | Router 6 tiers (Haiku→Sonnet→Opus) |
| `app/orchestrator/intent_router.py` | Classificador de intents |
| `app/orchestrator/pending_actions.py` | Ações pendentes (multi-turn) |
| `app/orchestrator/vector_semantic_cache.py` | Cache semântico (pgvector) |
| `app/orchestrator/task_planner.py` | Planejador de tarefas |

#### Serviços Chamados
- `CascadedRouter` (6 tiers)
- `IntentRouter` (classifica intent → domínio)
- `TaskPlanner` (decomposição multi-step)
- `PolicyEngine` (políticas de execução)
- `VectorSemanticCache` (pgvector cosine)

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| WS | `/ws/chat/{session_id}` | WebSocket principal — roteia para agentes por `domain` param |

#### Domínios Roteados
| Domain Param | Agente Destino |
|-------------|---------------|
| `wizard` | WizardReActAgent |
| `pipeline`, `cv_screening` | PipelineReActAgent |
| `sourcing` | SourcingReActAgent |
| `talent` (default) | TalentReActAgent |
| `kanban` | KanbanReActAgent |
| `jobs_management` | JobsManagementReActAgent |
| `policy` | PolicyReActAgent |
| `pipeline_transition` | PipelineTransitionAgent |
| `analytics` | AnalyticsReActAgent |
| `communication` | CommunicationReActAgent |
| `ats_integration` | ATSIntegrationReActAgent |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir o orquestrador** (9 arquivos na ordem)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos |
|--------|-------|:--------:|
| Provedores LLM | 13C.2 | 13 (cascade Haiku→Sonnet→Opus) |
| Config/Infra Base | 13C.14 | 8 (config.py, database.py, logging) |
| Robustez | 13C.3 | 11 (input_validation, defensive_prompts) |

#### Gaps V5 Aplicáveis
- V5 usa `DomainOrchestrator` com apenas 2 domínios vs LIA com 11 domínios
- LIA é mais avançada neste ponto

#### Para Alpha 1
- Configurar routing para domínios Alpha 1 (wizard, pipeline, sourcing, communication, wsi, scheduling)
- Garantir que `pending_actions` funciona para fluxos multi-turn (wizard, scheduling)
- Validar cache semântico com intents Alpha 1

---

### 14.2 Job Wizard Agent (Ag.1 — JD Generator) [ALPHA 1]
**Tipo:** ReAct Agent + LangGraph StateGraph (dual mode)
**Padrão Arquitetural:**
- **ReAct (4-file pattern):** `wizard_react_agent.py` + `wizard_tool_registry.py` + `wizard_system_prompt.py` + `wizard_domain.yaml` — modo conversacional com consultor (criar/editar vaga)
- **LangGraph StateGraph:** `job_wizard_graph.py` — modo determinístico com nós `collect_info` → `generate_jd` → `validate_jd` → `review` para fluxo guiado de criação de vaga
- **Quando usa qual:** ReAct para interação livre (perguntas do consultor), Graph para fluxo estruturado (wizard passo-a-passo)
- **Ciclo ReAct:** Recebe mensagem → pensa (LLM) → escolhe tool → executa → observa resultado → repete até resposta final
- V5: Mesma arquitetura dual (wizard_react_agent + jd_generator_service)

**Prioridade Alpha 1:** P0 (Sprint 1)
**Agente LIA:** `app/domains/job_management/agents/wizard_react_agent.py`
**V5 Correspondente:** `src/domains/job_management/wizard_react_agent.py` + `jd_generator_service.py` (mesma arquitetura)

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/job_management/agents/wizard_react_agent.py` | Agente ReAct conversacional |
| `app/domains/job_management/agents/wizard_tool_registry.py` | 9 tools registradas |
| `app/domains/job_management/agents/wizard_system_prompt.py` | System prompt (persona LIA) |
| `app/domains/job_management/agents/job_wizard_graph.py` | StateGraph com HITL |
| `app/domains/job_management/tools/job_wizard_tools.py` | Tools adicionais do wizard |

#### Tools (9)
| Tool | O que faz | Serviço |
|------|----------|---------|
| `validate_job_requirements` | Valida requisitos da vaga | FairnessGuard |
| `get_salary_benchmarks` | Benchmarks salariais do mercado | DB Analytics |
| `search_salary_benchmark` | Busca benchmark salarial específico | DB Analytics |
| `validate_job_fields` | Valida campos obrigatórios | Validation rules |
| `get_job_suggestions` | Sugestões IA para campos | LLM |
| `save_job_draft` | Salva rascunho da vaga | DB: job_vacancies |
| `get_company_config` | Configuração da empresa | DB: companies |
| `generate_enriched_jd` | Gera JD enriquecida com IA | JDGeneratorService + JDEnrichmentService |
| `check_job_draft_health` | Verifica completude do draft | Validation rules |

#### LangGraph — Job Wizard Graph
```
Nós: intent_classifier → field_extractor → tool_router → tool_executor → response_generator → stage_transition → END
State: JobWizardState { intent, fields{}, current_stage, tool_calls[] }
Checkpointer: PostgresSaver
HITL: interrupt_before=["stage_transition"]
```

#### Serviços
| Serviço | Arquivo | Função |
|---------|--------|--------|
| JDGeneratorService | `app/services/jd_generator_service.py` | Geração de JD com LLM |
| JDEnrichmentService | `app/services/jd_enrichment_service.py` | Enriquecimento de JD |
| JDParserService | `app/services/jd_parser_service.py` | Parser de JD existente |
| JDImportService | `app/services/jd_import_service.py` | Importação de JD |
| JDTemplateService | `app/services/jd_template_service.py` | Templates de JD |
| JobVacancyService | `app/services/job_vacancy_service.py` | CRUD de vagas |
| JobRequirementsService | `app/services/job_requirements_service.py` | Requisitos de vagas |
| WizardOrchestratorService | `app/domains/job_management/services/wizard_orchestrator_service.py` | Orquestração do wizard |
| WizardDataPriorityService | `app/domains/job_management/services/wizard_data_priority_service.py` | Priorização de dados |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| POST | `/wizard/start` | Inicia wizard de vaga |
| POST | `/wizard/message` | Envia mensagem ao wizard |
| WS | `/ws/chat/{session_id}` (domain=`wizard`) | WebSocket conversacional |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (7 arquivos na ordem, domínio=`job_management`)
→ Ver seção **13C.17 — Para reproduzir o HITL** (5 arquivos — Graph usa HITL)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| Provedores LLM | 13C.2 | `llm.py`, `llm_factory.py`, `llm_claude.py` |
| HITL | 13C.8 | `hitl_service.py`, `HITLConfirmCard.tsx` |
| Prompts | 13C.17 | `job_management.yaml`, `lia_persona.yaml` |

#### Implementação — Padrão ReAct 13B.7
| Parâmetro | Valor |
|-----------|-------|
| Classe | `WizardReActAgent(EnhancedAgentMixin, BaseAgent)` |
| Domain | `"job_management"` |
| Tools | `get_job_management_tools()` (10 tools) |
| System prompt | `get_job_management_system_prompt(guardrails, memory_context)` |
| Guardrails | 13D.5 — #1-#6 globais (FairnessGuard no JD é crítico) |
| Particularidade | Dual ReAct+Graph — `job_wizard_graph.py` orquestra os nós, ReAct escolhe tools dentro de cada nó |

#### Para Alpha 1
- Adaptar para modo "editar vaga importada do ATS" (não criar do zero)
- `JDImportService` precisa receber dados do ATS e popular o wizard
- HITL no `stage_transition` para aprovação de JD

---

### 14.3 Sourcing Agent (Ag.2) [ALPHA 1]
**Tipo:** ReAct Agent (4-file pattern)
**Padrão Arquitetural:**
- **ReAct puro (4-file pattern):** `sourcing_react_agent.py` + `sourcing_tool_registry.py` + `sourcing_system_prompt.py` + `sourcing_domain.yaml`
- **Sem LangGraph** — usa ciclo ReAct iterativo: mensagem → raciocínio LLM → escolha de tool (14 disponíveis) → execução → observação → próximo passo
- **14 tools** incluem: busca semântica (PGVector), busca texto (ES/pg_trgm), WRF fusion, Pearch AI, Apify, like/dislike feedback
- V5: Usa `MultiAgentOrchestrator` com 6 sub-agents (search, detail, comparison, analytics, report, action) — padrão diferente, LIA é mais coeso

**Prioridade Alpha 1:** P0 (Sprint 1)
**Agente LIA:** `app/domains/sourcing/agents/sourcing_react_agent.py`
**V5 Correspondente:** `src/domains/sourcing/sourcing_react_agent.py` + `sourcing_pipeline.py` + `wrf_service.py`

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/sourcing/agents/sourcing_react_agent.py` | Agente ReAct |
| `app/domains/sourcing/agents/sourcing_tool_registry.py` | 14 tools |
| `app/domains/sourcing/agents/sourcing_system_prompt.py` | System prompt ("Consultora Estratégica") |

#### Tools (14)
| Tool | O que faz | Serviço |
|------|----------|---------|
| `set_search_criteria` | Define critérios de busca | Search Context |
| `suggest_skills` | Sugestões IA de skills para cargo | LLM / Skill Taxonomy |
| `search_candidates` | Busca candidatos (ES+PGV+WRF) | CandidateSearchService |
| `filter_results` | Filtra resultados por critério | In-memory filter |
| `view_candidate` | Visualiza perfil do candidato | DB: candidates |
| `analyze_profile` | Análise IA do perfil | Profile Analysis Service |
| `compare_candidates` | Comparação lado a lado | ComparisonService |
| `score_candidate` | Scoring WSI do candidato | WSI Scoring Service |
| `add_to_shortlist` | Adiciona à shortlist | DB: vacancy_candidates |
| `remove_from_shortlist` | Remove da shortlist | DB: vacancy_candidates |
| `rank_candidates` | Rankeia shortlist por score IA | Scoring Engine |
| `send_outreach` | Envia mensagem de contato (omnichannel) | CommunicationService |
| `generate_message` | Gera mensagem personalizada com IA | LLM |
| `track_response` | Rastreia resposta do candidato | DB: communication_history |

#### Serviços
| Serviço | Arquivo | Função |
|---------|--------|--------|
| HybridSearchService | `app/services/hybrid_search_service.py` | Busca híbrida tsvector + pgvector |
| WRFDynamicKService | `app/services/wrf_dynamic_k_service.py` | WRF Dynamic K por qualificação |
| PreWRFFilterService | `app/services/pre_wrf_filter_service.py` | Orquestra ES+PGV antes de WRF |
| RAGPipelineService | `app/services/rag_pipeline_service.py` | RAG: pgvector + BM25 + FairnessGuard |
| PearchService | `app/services/pearch_service.py` | Busca Pearch AI (190M+ perfis) |
| ApifyService | `app/services/apify_service.py` | Scraping LinkedIn/Glassdoor |
| CandidateEnrichmentService | `app/services/candidate_enrichment_service.py` | Enriquecimento de perfis |
| SourcingPipelineService | `app/services/sourcing_pipeline_service.py` | Pipeline completo de sourcing |
| SemanticSearchService | `app/shared/intelligence/semantic_search_service.py` | Expansão semântica |
| EmbeddingService | `app/shared/intelligence/embedding_service.py` | Gemini text-embedding-004 |
| WorkingMemoryService | `app/shared/agents/working_memory.py` | Memória de trabalho |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| POST | `/sourcing/search` | Busca booleana |
| POST | `/sourcing/match-candidates` | Matching candidato×vaga |
| GET | `/sourcing/suggestions/{job_id}` | Sugestões por vaga |
| POST | `/candidates/search/local` | Busca local (PostgreSQL) |
| POST | `/candidates/search` | Busca externa (Pearch AI 190M+) |
| POST | `/candidates/{id}/enrich` | Enriquecimento (Apify) |
| GET | `/candidates/rag-search` | Busca RAG híbrida |
| WS | `/ws/chat/{session_id}` (domain=`sourcing`) | WebSocket conversacional |

#### Gaps V5 Aplicáveis
| Gap V5 | Impacto |
|--------|---------|
| ParamExtractor (492 linhas, extração detalhada skills/location/score) | 🟡 V5 mais detalhado na extração |
| FactChecker domain-specific (313 linhas, verifica claims) | 🟡 LIA tem genérico em shared/compliance |
| Template Formatter (256 linhas, formatação por tipo de resultado) | 🟢 Nice-to-have |
| Validators (367 linhas, validação de dados de sourcing) | 🟢 LIA valida inline |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (7 arquivos na ordem, domínio=`sourcing`)
→ Ver seção **13C.17 — Para reproduzir o sourcing inteligente** (8 arquivos na ordem)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| Sourcing Services | 13C.6 | 13 arquivos (pipeline, WRF, Pearch, ES, pgvector) |
| Provedores LLM | 13C.2 | `llm.py`, `embedding_service.py`, `semantic_search_service.py` |
| Prompts | 13C.17 | `sourcing.yaml`, `lia_persona.yaml` |

#### Implementação — Padrão ReAct 13B.7
| Parâmetro | Valor |
|-----------|-------|
| Classe | `SourcingReActAgent(EnhancedAgentMixin, BaseAgent)` |
| Domain | `"sourcing"` |
| Tools | `get_sourcing_tools()` (14 tools) |
| System prompt | `get_sourcing_system_prompt(guardrails, memory_context)` |
| Guardrails | 13D.5 — #1-#6 globais + #10 (`sourcing`: não contatar recusados <6 meses) |
| Particularidade | ReAct puro — exemplo canônico da seção 13B.7 |

#### Para Alpha 1
- Integrar busca com dados importados do ATS (candidatos da vaga)
- Validar que WRF+PGV+ES funciona em produção
- Configurar Pearch/Apify para busca externa (se no scope Alpha 1)

---

### 14.4 CV Screening Agent (Ag.3 — Pipeline) [ALPHA 1]
**Tipo:** ReAct Agent (4-file pattern)
**Padrão Arquitetural:**
- **ReAct puro (4-file pattern):** `pipeline_react_agent.py` + `pipeline_tool_registry.py` + `pipeline_system_prompt.py` + `pipeline_domain.yaml`
- **Sem LangGraph** — ciclo ReAct iterativo com 13 tools (triagem CV, scoring, matching, comparação, gaps)
- **Diferença do WSI:** Este agente faz triagem de CV (análise documental); o WSI Graph (14.5) faz entrevista conversacional
- V5: Não existe como agente separado — scoring básico em `evaluation` domain

**Prioridade Alpha 1:** P1 (Sprint 2)
**Agente LIA:** `app/domains/cv_screening/agents/pipeline_react_agent.py`
**V5 Correspondente:** `src/domains/cv_screening/pipeline_react_agent.py` + `cv_scoring_service.py` + `rubric_evaluation_service.py`

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/cv_screening/agents/pipeline_react_agent.py` | Agente ReAct |
| `app/domains/cv_screening/agents/pipeline_tool_registry.py` | 13 tools |
| `app/domains/cv_screening/agents/pipeline_system_prompt.py` | System prompt (FAIRNESS_RULES + COMMUNICATION_TRANSPARENCY_RULES) |

#### Tools (13)
| Tool | O que faz | Serviço |
|------|----------|---------|
| `view_candidate_profile` | Perfil completo do candidato | DB: candidates |
| `move_candidate` | Muda estágio no pipeline | DB + HITLService |
| `analyze_cv` | Extrai skills/score do CV | CVParser + AI Analysis |
| `run_wsi_screening` | Triagem comportamental WSI | WSIService |
| `schedule_interview` | Agenda entrevista | CalendarService |
| `send_communication` | Envia comunicação ao candidato | CommunicationService |
| `add_notes` | Adiciona notas ao perfil | DB: candidate_notes |
| `batch_move` | Move múltiplos candidatos | DB batch |
| `add_to_shortlist` | Adiciona à shortlist | DB: vacancy_candidates |
| `view_screening_results` | Visualiza resultados de triagem | DB: screening_results |
| `view_interview_notes` | Notas da entrevista | DB: interview_notes |
| `generate_offer` | Cria proposta de contratação | Offer Generation Service |
| `finalize_hiring` | Registra admissão | Core Recruitment |

#### Serviços
| Serviço | Arquivo | Função |
|---------|--------|--------|
| CVParser | `app/services/cv_parser.py` | Extrai dados estruturados do CV |
| CVScoringService | `app/services/cv_scoring_service.py` | Score matching CV vs vaga |
| RubricEvaluationService | `app/services/rubric_evaluation_service.py` | Avaliação por rubrica BARS |
| EvaluationCriteriaService | `app/services/evaluation_criteria_service.py` | Critérios de avaliação por vaga |
| WSIScreeningPipeline | `app/domains/cv_screening/services/wsi_screening_pipeline.py` | Pipeline completo de screening |
| HITLService | `app/services/hitl_service.py` | Human-in-the-Loop |
| FairnessGuard | `app/shared/agents/fairness_guard.py` | Verificação de viés |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| POST | `/automation/screen-candidate` | Triagem curricular (CVScoringService Rubric/BARS) |
| POST | `/automation/handle-trigger/screening-completed` | Pós-triagem (Bloom+Dreyfus+Big5) |
| WS | `/ws/chat/{session_id}` (domain=`pipeline`) | WebSocket conversacional |
| REST | `/orchestrator/*` | PipelineReActAgent endpoints |

#### Gaps V5 Aplicáveis
| Gap V5 | Impacto |
|--------|---------|
| Multi-Stage Eval Graph (4 nós: classify→evaluate→decide→craft) | 🟡 V5 tem graph de avaliação mais sofisticado |
| Security Guard (detecção prompt injection em inputs de candidatos) | 🟡 LIA tem PromptInjectionGuard mas não integrado aqui |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (7 arquivos na ordem, domínio=`cv_screening`)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| CV Screening Services | 13C.7 | 5 arquivos (cv_parser, scoring, batch, questions) |
| WSI Services | 13B.10 | 18 arquivos (pipeline WSI completo) |
| Robustez | 13C.3 | `input_validation.py`, `response_filter.py` (PromptInjection!) |
| HITL | 13C.8 | `hitl_service.py` (Gate 1/2 precisam aprovação humana) |

#### Implementação — Padrão ReAct 13B.7
| Parâmetro | Valor |
|-----------|-------|
| Classe | `PipelineReActAgent(EnhancedAgentMixin, BaseAgent)` |
| Domain | `"cv_screening"` |
| Tools | `get_pipeline_tools()` (13 tools) |
| System prompt | `get_pipeline_system_prompt(guardrails, memory_context)` |
| Guardrails | 13D.5 — #1-#6 globais + #11 (`pipeline`: gate humano antes de rejeição em massa) |
| Particularidade | FairnessGuard wiring crítico (13D.1) + PromptInjectionGuard (13D) + HITL para Gates |

#### Para Alpha 1
- Integrar PromptInjectionGuard no fluxo de screening (antes de processar input do candidato)
- Configurar para fluxo Alpha 1: triagem CV → score → Gate 1 (HITL)
- Garantir que `move_candidate` aciona triggers automáticos (StageAutomationEngine)

---

### 14.5 WSI Interview Agent (Ag.4 + Ag.5 — Entrevistador + Avaliador) [ALPHA 1]

> **Absorve do roadmap:** Este componente unifica **Ag.4 (Entrevistador WSI)** e **Ag.5 (Avaliador WSI)** — são nós do mesmo LangGraph (`score_response`, `generate_feedback`), não agentes separados. O roadmap original listou Ag.5 como agente autônomo, mas isso foi **reclassificado** (ver seção 4.5).

**Tipo:** LangGraph StateGraph (determinístico — sem ReAct)
**Padrão Arquitetural:**
- **LangGraph StateGraph puro** — NÃO usa ReAct (não tem 4-file pattern)
- **Grafo determinístico:** `load_context` → `generate_question` → `validate_response` → `score_response` → `advance` → `generate_feedback`
- **Loop por bloco:** O nó `advance` volta para `generate_question` até completar todos os blocos WSI (7 blocos)
- **HITL:** `interrupt_before=["lg_generate_feedback"]` — pausa antes de gerar feedback para aprovação do consultor
- **State:** `WSIInterviewState` com question_blocks[], current_block, responses[], scores[], final_score
- **Diferença do ReAct:** Não há ciclo "pensar → escolher tool" — cada nó faz exatamente uma coisa, fluxo é fixo
- **PostgresSaver:** Checkpointing persistente (sessões podem durar dias)
- V5: `InterviewGraph` com 4 nós simples (classify → evaluate → decide → craft_message), sem WSI

**Prioridade Alpha 1:** P0 (Sprint 2)
**Agente LIA:** `app/domains/cv_screening/agents/wsi_interview_graph.py` (unifica Ag.4 e Ag.5 em 1 graph)
**V5 Correspondente:** `src/domains/cv_screening/wsi_interview_graph.py` + `wsi_service.py` + `wsi_question_generator.py`

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/cv_screening/agents/wsi_interview_graph.py` | StateGraph completo (entrevista + avaliação) |

#### LangGraph — WSI Interview Graph
```
Nós:
  load_context → generate_question → validate_response → score_response → advance → generate_feedback
                        ↑                                                    |
                        └────────────────── (loop por bloco) ────────────────┘

State: WSIInterviewState
  - question_blocks[]     — blocos de perguntas WSI
  - responses[]           — respostas do candidato
  - technical_score       — score técnico
  - behavioral_score      — score comportamental
  - recommendation        — aprovado/reprovado
  - wsi_final_score       — score composto final

Checkpointer: PostgresSaver (persistência entre turnos)
```

#### Serviços
| Serviço | Arquivo | Função |
|---------|--------|--------|
| WSIService | `app/services/wsi_service.py` | Serviço principal WSI (orquestração) |
| WSIQuestionService | `app/services/wsi_question_service.py` | Geração e gestão de perguntas |
| WSIQuestionGenerator | `app/services/wsi_question_generator.py` | Geração IA de perguntas |
| WSIQuestionAdjuster | `app/services/wsi_question_adjuster.py` | Ajuste de dificuldade/foco |
| WSIDeterministicScorer | `app/services/wsi_deterministic_scorer.py` | Scoring determinístico (Bloom+Dreyfus+Big5) |
| WSIScreeningPipeline | `app/services/wsi_screening_pipeline.py` | Pipeline completo de screening |
| WSIVoiceOrchestrator | `app/services/wsi_voice_orchestrator.py` | Orquestração para triagem por voz |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| POST | `/api/v1/wsi/generate-questions` | Gera perguntas WSI via Claude-Sonnet |
| POST | `/api/v1/wsi/analyze-response` | Analisa resposta do candidato |
| POST | `/api/v1/wsi/complete-screening` | Completa triagem WSI |
| POST | `/screening/questions` | Gera perguntas WSI |
| POST | `/screening/questions/regenerate` | Regenera perguntas |

#### Scoring
- **Bloom's Taxonomy:** Nível cognitivo da resposta (Remember→Create)
- **Dreyfus Model:** Nível de expertise (Novice→Expert)
- **Big Five Personality:** Traços comportamentais
- **Função:** `calculate_wsi_deterministic` → score 0-100 por competência

#### Gaps V5 Aplicáveis
| Gap V5 | Impacto |
|--------|---------|
| Security Guard / PromptInjectionGuard | 🔴 CRÍTICO — candidatos podem injetar prompts. Integrar `app/shared/prompt_injection.py` ANTES de processar respostas |
| Final Analysis (análise final agregada pós-entrevista) | 🟡 Útil para Gate 2 — gera parecer consolidado |
| OTT Service (one-time-token para sessão) | 🟡 Segurança de sessão de triagem web |

#### Automações Relacionadas
| Automação | Frequência | Ação |
|----------|-----------|------|
| `auto_complete_expired_screenings` | A cada 1h | Finaliza triagens expiradas |
| `triagem_abandonada` | 24h após início | Email lembrete ao candidato |
| `SCREENING_COMPLETED` (evento) | Imediato | Log atividade + email feedback |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir o WSI** (8 arquivos na ordem)
→ Ver seção **13C.17 — Para reproduzir o HITL** (5 arquivos — Graph usa `interrupt_before`)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| WSI Services | 13B.10 | 18 arquivos (scoring, questions, calibration, feedback) |
| HITL | 13C.8 | `hitl_service.py` (interrupt_before=["lg_generate_feedback"]) |
| Robustez | 13C.3 | PromptInjectionGuard (candidatos podem injetar prompts!) |
| Comunicação | 13C.5 | `personalized_feedback_service.py` (feedback ao candidato) |

#### Para Alpha 1
- **CRÍTICO:** Integrar PromptInjectionGuard no nó `validate_response` antes de scoring
- Adaptar para entrega via Chat Web (WebSocket `agent_chat_ws.py`)
- Configurar timeout de 48h para triagem abandonada
- Gerar feedback diferenciado (construtivo para Gate 1, final para Gate 2)

---

### 14.6 Scheduling Agent (Ag.6) [ALPHA 1]
**Tipo:** LangGraph StateGraph (determinístico — sem ReAct)
**Padrão Arquitetural:**
- **LangGraph StateGraph puro** — NÃO usa ReAct (não tem 4-file pattern)
- **Grafo determinístico:** `loader` → `collector` → `router` → `validator` → `executor` → `response`
- **Coleta conversacional:** `collector` interage com candidato para obter data/hora/tipo de entrevista
- **Integração calendário:** `executor` chama Microsoft Graph / Google Calendar + gera link Zoom/Teams/Meet
- **Diferença do ReAct:** Fluxo fixo — cada nó faz exatamente uma coisa, sem ciclo de raciocínio
- V5: Não existe — precisa ser construído do zero

**Prioridade Alpha 1:** P1 (Sprint 3)
**Agente LIA:** `app/domains/interview_scheduling/agents/interview_graph.py`
**V5 Correspondente:** `src/domains/interview_scheduling/interview_graph.py` + `calendar_service.py` + `zero_touch_scheduling_service.py`

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/interview_scheduling/agents/interview_graph.py` | StateGraph de agendamento |
| `app/domains/interview_scheduling/agents/interview_scheduling_nodes.py` | Nós do graph |

#### LangGraph — Interview Scheduling Graph
```
Nós:
  interview_state_loader → interview_details_collector → interview_router → interview_validator → interview_scheduler_executor → interview_response_planner
                                     ↑                         |
                                     └──── (campos faltando) ──┘

State: _InterviewStateDict { workflow_data, session_id }
Checkpointer: PostgresSaver
```

#### Serviços
| Serviço | Arquivo | Função |
|---------|--------|--------|
| CalendarService | `app/services/calendar_service.py` | Gestão de calendário |
| GoogleCalendarClient | `app/services/google_calendar_client.py` | Cliente Google Calendar |
| ZeroTouchSchedulingService | `app/services/zero_touch_scheduling_service.py` | Agendamento automático |
| TeamsService | `app/services/teams_service.py` | Integração Microsoft Teams |
| TeamsAuth | `app/services/teams_auth.py` | Autenticação Teams |
| TeamsRecordingService | `app/services/teams_recording_service.py` | Gravação de reuniões |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| POST | `/scheduling/interviews` | Agenda entrevista |
| POST | `/scheduling/interviews/with-teams` | Agenda com Teams (Microsoft Graph API) |

#### Automações Relacionadas
| Automação | Frequência | Ação |
|----------|-----------|------|
| `send_interview_reminders` | A cada 15m | Lembretes 24h (Email+WA) e 1h (WA) |
| `check_interview_no_shows` | A cada 30m | Detecta no-shows |
| `entrevista_nao_confirmada` | 6h antes | Alerta ao recrutador |
| `INTERVIEW_SCHEDULED` (evento) | Imediato | Confirmação + evento no calendário |
| `INTERVIEW_COMPLETED` (evento) | Imediato | Gera parecer IA |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`interview_scheduling`, mas é LangGraph Graph)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| Comunicação | 13C.5 | Email + WhatsApp para lembretes/confirmações |
| HITL | 13C.8 | Aprovação de agendamento |

#### Para Alpha 1
- Configurar com Google Calendar ou Teams (conforme cliente)
- Integrar com Pipeline Transition Agent para trigger pós-Gate 2
- Garantir que lembretes 24h/1h funcionam

---

### 14.7 Communication Agent (Ag.7) [ALPHA 1]

> **Absorve do roadmap:** Este agente absorve o **Ag.7 (AnalistaFeedback)** do roadmap original. O roadmap listou "AnalistaFeedback" como agente autônomo, mas feedback é funcionalidade deste agente — acionada via `PersonalizedFeedbackService` + templates configuráveis por Gate/estágio. Não existe "agente de feedback" separado (ver seção 4.7 para a reclassificação completa).

**Tipo:** ReAct Agent (4-file pattern)
**Padrão Arquitetural:**
- **ReAct puro (4-file pattern):** `communication_react_agent.py` + `communication_tool_registry.py` + `communication_system_prompt.py` + `communication_domain.yaml`
- **Sem LangGraph** — ciclo ReAct iterativo com 5 tools (send_email, send_whatsapp, get_history, schedule_message, send_feedback)
- **23 arquivos de suporte:** Adapters (Resend, SendGrid, Meta, Twilio), dispatcher, templates, history — ver camada 13C.5
- **Diferença:** Usa ReAct para decidir qual canal enviar (email vs WhatsApp vs Teams), com que template, em que momento
- V5: Mesma arquitetura (communication_react_agent.py), mas só email básico

**Prioridade Alpha 1:** P0 (Sprint 1)
**Agente LIA:** `app/domains/communication/agents/communication_react_agent.py`
**V5 Correspondente:** `src/domains/communication/communication_react_agent.py` + `email_service.py` + `whatsapp_service.py`

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/communication/agents/communication_react_agent.py` | Agente ReAct |
| `app/domains/communication/agents/communication_tool_registry.py` | 5 tools |
| `app/domains/communication/agents/communication_system_prompt.py` | System prompt |
| `app/domains/communication/models/communication_matrix.py` | Matriz de comunicação (6 triggers) |

#### Tools (5)
| Tool | O que faz | Serviço |
|------|----------|---------|
| `send_email` | Envia email (Resend ou SendGrid) | EmailService |
| `send_whatsapp` | Envia WhatsApp (Meta ou Twilio) | WhatsAppService |
| `get_communication_history` | Histórico de comunicações | CommunicationHistoryService |
| `schedule_message` | Agenda envio futuro | AutomationScheduler |
| `check_rate_limit` | Verifica rate limit por canal | TokenBudgetService |

#### Serviços
| Serviço | Arquivo | Função |
|---------|--------|--------|
| CommunicationService | `app/domains/communication/services/communication_service.py` | Serviço principal |
| CommunicationDispatcher | `app/services/communication_dispatcher.py` | Despacho multi-canal |
| EmailService | `app/services/email_service.py` | Envio de emails |
| EmailProviders | `app/services/email_providers/` | Resend + SendGrid |
| RecruitmentEmailTemplates | `app/services/recruitment_email_templates.py` | Templates de email |
| WhatsAppService | `app/domains/communication/services/whatsapp_service.py` | WhatsApp (Meta Business API) |
| WhatsAppTwilioService | `app/services/whatsapp_twilio_service.py` | WhatsApp via Twilio |
| WhatsAppMetaService | `app/services/whatsapp_meta_service.py` | WhatsApp via Meta |
| WhatsAppFactory | `app/services/whatsapp_factory.py` | Factory para selecionar provider |
| CommunicationHistoryService | `app/domains/communication/services/communication_history_service.py` | Histórico |
| TeamsService | `app/domains/communication/services/teams_service.py` | Microsoft Teams |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| POST | `/communication/send-email` | Envia email |
| POST | `/communication/send-whatsapp` | Envia WhatsApp |
| POST | `/communication/send-screening-invite` | Convite de triagem |
| WS | `/ws/chat/{session_id}` (domain=`communication`) | WebSocket |

#### Communication Matrix Triggers
| Trigger | Canal | Timing | Ação |
|---------|-------|--------|------|
| `match_alto_detectado` | Bell + Email | Imediato | Notifica match >80% |
| `triagem_abandonada` | Email | 24h após início | Lembrete ao candidato |
| `entrevista_nao_confirmada` | Alerta | 6h antes | Alerta ao recrutador |
| `briefing_2x_dia` | Dashboard | 08:00 e 14:00 | Briefing ao recrutador |
| `sla_em_risco` | Alerta | Quando ultrapassado | Alerta SLA |
| `sla_violado` | Alerta + Email | Quando violado | Escalação SLA |

#### Automações Relacionadas
| Automação | Frequência | Ação |
|----------|-----------|------|
| `CANDIDATE_NO_CONTACT_48H` | 48h | Email follow-up + tarefa |
| `CANDIDATE_REJECTED` (evento) | Imediato | Email rejeição + talent pool |
| `STAGE_CHANGED` (evento) | Imediato | Comunicação automática por estágio |

#### Gaps — Funcionalidades Faltantes
| Gap | Status | Impacto |
|-----|:------:|---------|
| Email tracking pixel (abertura/clique) | ❌ Absent | 🔴 Implementar do zero |
| Feedback diferenciado por Gate (construtivo vs final) | ❌ Absent | 🟡 Template novo |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir a comunicação inteligente** (10 arquivos na ordem)
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`communication`)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| Comunicação Services | 13C.5 | **23 arquivos** (serviço principal, dispatcher, email providers, WhatsApp providers, templates, histórico) |
| Provedores LLM | 13C.2 | `interpret_context_llm_service.py` usa LLM para gerar mensagens |
| Config/Infra | 13C.14 | `email_service.py`, `recruitment_email_templates.py` |

#### Implementação — Padrão ReAct 13B.7
| Parâmetro | Valor |
|-----------|-------|
| Classe | `CommunicationReActAgent(EnhancedAgentMixin, BaseAgent)` |
| Domain | `"communication"` |
| Tools | `get_communication_tools()` (5 tools) |
| System prompt | `get_communication_system_prompt(guardrails, memory_context)` |
| Guardrails | 13D.5 — #1-#6 globais + #3 (IA identificada) + #9 (`communication`: footer IA obrigatório) |
| Particularidade | Absorve AnalistaFeedback (Ag.7 reclassificado) — `PersonalizedFeedbackService` é serviço interno, não agente |

#### Para Alpha 1
- Email é canal primário — configurar EmailService com provider real (Resend ou SendGrid)
- Criar templates Alpha 1: convite triagem, follow-up 7 dias, feedback Gate 1 (construtivo), feedback Gate 2 (final)
- Implementar tracking pixel para métricas de abertura/clique
- Configurar follow-up automático em 7 dias (trigger `CANDIDATE_NO_CONTACT_48H` → ajustar para 7 dias)

---

### 14.8 ATS Integration Agent (Ag.8) [ALPHA 1]
**Tipo:** ReAct Agent (4-file pattern) — ⚠️ Alpha 1 usa como serviço REST, não como agente conversacional
**Padrão Arquitetural:**
- **Na LIA: ReAct (4-file pattern)** — `ats_integration_react_agent.py` + `ats_tool_registry.py` + `ats_system_prompt.py` + `ats_domain.yaml`
- **No Alpha 1: Serviço REST** — usa `ats_sync_service.py` + 5 clientes ATS (Gupy, PandaPé, Merge, StackOne, base) diretamente, sem ciclo ReAct
- **Por que serviço no Alpha 1:** CRUD bidirecional (importar vagas, exportar status/scores) é determinístico — não precisa de raciocínio autônomo ReAct
- V5: `SourcingAPIClient` (consumidor REST) + 67 YAMLs de endpoints

**Prioridade Alpha 1:** P0 (Sprint 0)
**Agente LIA:** `app/domains/ats_integration/agents/ats_integration_react_agent.py`
**V5 Correspondente:** `src/domains/ats_integration/ats_integration_react_agent.py` + `ats_sync_service.py` + clientes Gupy/PandaPé/Merge/StackOne

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/ats_integration/agents/ats_integration_react_agent.py` | Agente ReAct |
| `app/domains/ats_integration/agents/ats_integration_tool_registry.py` | 5 tools |
| `app/domains/ats_integration/agents/ats_integration_system_prompt.py` | System prompt |

#### Tools (5)
| Tool | O que faz | Serviço |
|------|----------|---------|
| `sync_candidate_to_ats` | Sync candidato para ATS externo | ATSSyncService |
| `fetch_candidate_from_ats` | Importa candidato do ATS | ATSSyncService |
| `validate_ats_fields` | Valida campos ATS | Validation rules |
| `bulk_sync_candidates` | Sync em lote | ATSSyncService |
| `get_sync_status` | Status do sync | ATSSyncService |

#### Serviços
| Serviço | Arquivo | Função |
|---------|--------|--------|
| ATSSyncService | `app/domains/ats_integration/services/ats_sync_service.py` | Sync bidirecional com ATS |
| GupyService | `app/services/gupy_service.py` | Cliente Gupy API |
| PandapeService | `app/services/pandape_service.py` | Cliente Pandapé API |
| MergeATSService | `app/services/merge_ats_service.py` | Cliente Merge.dev (multi-ATS) |
| ATSJobHistoryService | `app/services/ats_job_history_service.py` | Histórico de vagas no ATS |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| POST | `/ats/connections` | Cria conexão ATS (Gupy/Pandapé) |
| POST | `/ats/connections/{id}/sync` | Dispara sync bidirecional |
| WS | `/ws/chat/{session_id}` (domain=`ats_integration`) | WebSocket |

#### Automações Relacionadas
| Automação | Frequência | Ação |
|----------|-----------|------|
| `ATS_SYNC` (evento) | Imediato | Sincroniza mudanças com ATS externo |
| `CANDIDATE_HIRED` (evento) | Imediato | Sync final com ATS |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`ats_integration`)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| Provedores LLM | 13C.2 | `ats_factory.py` (factory de providers ATS) |
| Config/Infra | 13C.14 | `config.py` (chaves API dos ATS) |

#### Implementação — Padrão ReAct 13B.7
| Parâmetro | Valor |
|-----------|-------|
| Classe | `ATSIntegrationReActAgent(EnhancedAgentMixin, BaseAgent)` |
| Domain | `"ats_integration"` |
| Tools | `get_ats_tools()` (5 tools) |
| System prompt | `get_ats_system_prompt(guardrails, memory_context)` |
| Guardrails | 13D.5 — #1-#6 globais |
| Particularidade | **Alpha 1 usa como serviço REST** — não instancia o ReAct loop. Chama `ats_sync_service.py` diretamente. O padrão 13B.7 aplica-se ao pós-Alpha quando o agente conversacional for ativado. |

#### Para Alpha 1
- Alpha 1 assume "premissa = vaga importada do ATS"
- Validar `fetch_candidate_from_ats` com pelo menos 1 provedor real (Gupy ou Merge)
- Garantir que importação popula dados suficientes para o wizard editar

---

### 14.9 Pipeline Transition Agent (NÃO ESTAVA NO ROADMAP — P0) [ALPHA 1]
**Tipo:** ReAct Agent (4-file pattern) + HITL inline
**Padrão Arquitetural:**
- **ReAct com HITL (4-file pattern):** `pipeline_transition_agent.py` + `pipeline_tool_registry.py` + `pipeline_system_prompt.py` + `pipeline_domain.yaml`
- **Sem LangGraph** — ciclo ReAct iterativo com **20 tools** + HITL de confirmação
- **HITL inline:** Tools como `approve_candidate`, `reject_candidate`, `move_to_gate` pausam para confirmação do consultor via `PendingActions` do Orchestrator
- **20 tools** incluem: move_candidate, approve, reject, batch_approve, check_rejection_fairness, get_pipeline_status, gate_bypass (inscrição web)
- **Diferença:** É o agente com mais tools (20) e o único ReAct que integra HITL no ciclo de execução (não no grafo)
- V5: Mesma arquitetura (pipeline_transition_agent.py), mas sem HITL e sem StageAutomationEngine

**Prioridade Alpha 1:** P0 (Sprint 2-3) — essencial para Gates 1/2
**Agente LIA:** `app/domains/pipeline/agents/pipeline_transition_agent.py`
**V5 Correspondente:** `src/domains/pipeline/pipeline_transition_agent.py` + `kanban_assistant_service.py` (mesma arquitetura)

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/pipeline/agents/pipeline_transition_agent.py` | ReAct com HITL |
| `app/domains/pipeline/agents/pipeline_tool_registry.py` | 20 tools |

#### Tools (20)
| Tool | O que faz | Serviço |
|------|----------|---------|
| `get_candidate_profile` | Perfil completo | DB: candidates |
| `get_candidate_wsi_scores` | Scores WSI | DB: wsi_scores |
| `get_candidate_screening_results` | Resultados de triagem | DB: screening_results |
| `get_candidate_salary_info` | Info salarial | DB: candidate_salary |
| `update_candidate_field` | Atualiza campo do candidato | DB: candidates |
| `request_data_collection` | Solicita coleta de dados | DataCollectionService |
| `get_stage_sub_statuses` | Sub-status do estágio | DB: pipeline_stages |
| `suggest_sub_status` | Sugere sub-status | LLM |
| `extract_preferences` | Extrai preferências do recrutador | NLP |
| `validate_transition` | Valida transição de estágio | PolicyEngine + FairnessGuard |
| `get_job_context` | Contexto da vaga | DB: job_vacancies |
| `schedule_secondary_task` | Agenda tarefa secundária | PlannedTaskService |
| `personalize_communication` | Personaliza comunicação | LLM |
| `check_rejection_fairness` | Verifica viés na rejeição | **FairnessGuard** (SOX compliance) |
| `check_candidate_availability` | Disponibilidade do candidato | CalendarService |
| `get_recruiter_preferences` | Preferências do recrutador | DB: recruiter_preferences |
| `save_recruiter_preference` | Salva preferência | DB: recruiter_preferences |
| `get_interview_details` | Detalhes da entrevista | CalendarService |
| `cancel_interview` | Cancela entrevista | CalendarService |
| `reschedule_interview` | Reagenda entrevista | CalendarService |

#### Serviços
| Serviço | Arquivo | Função |
|---------|--------|--------|
| PipelineService | `app/services/pipeline_service.py` | Gestão do pipeline |
| PipelineStageService | `app/services/pipeline_stage_service.py` | Configuração de estágios |
| CommunicationDispatcher | `app/services/communication_dispatcher.py` | Despacho multi-canal |
| CalendarService | `app/domains/interview_scheduling/services/calendar_service.py` | Calendário |
| FairnessGuard | `app/shared/agents/fairness_guard.py` | Verificação de viés |
| HITLService | `app/services/hitl_service.py` | Human-in-the-Loop |

#### HITL Behavior
- **Ações que requerem aprovação humana:** move (para estágios avançados), reject, offer
- **Endpoint HITL:** `POST /hitl/{thread_id}/approve`, `GET /hitl/{thread_id}/pending`
- **Fluxo:** Agent propõe ação → HITL cria pending approval → Recrutador aprova/rejeita → Agent executa

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| POST | `/recruitment-stages/*` | Pipeline transition endpoints |
| POST | `/hitl/{thread_id}/approve` | Aprova ação pendente |
| GET | `/hitl/{thread_id}/pending` | Lista ações pendentes |
| WS | `/ws/chat/{session_id}` (domain=`pipeline_transition`) | WebSocket |

#### Automações Relacionadas
| Automação | Frequência | Ação |
|----------|-----------|------|
| `STAGE_CHANGED` (evento) | Imediato | Log transição + auto-agenda se Interview |
| `CANDIDATE_REJECTED` (evento) | Imediato | Email rejeição + talent pool |
| `CANDIDATE_HIRED` (evento) | Imediato | Sync ATS + onboarding |
| `OFFER_SENT` (evento) | Imediato | Monitora resposta |
| `JOB_NO_MOVEMENT_5D` | 5 dias | Alerta vaga estagnada |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`pipeline`)
→ Ver seção **13C.17 — Para reproduzir o HITL** (5 arquivos — HITL é core deste agente)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| HITL | 13C.8 | **7 arquivos** (BE + FE — core deste agente) |
| Robustez | 13C.3 | FairnessGuard (`check_rejection_fairness`), Audit Trail |
| Comunicação | 13C.5 | Dispatch automático em transições de pipeline |
| Qualidade | 13C.9 | AgentQualityEvaluator (decisões de Gate auditoráveis) |

#### Implementação — Padrão ReAct 13B.7
| Parâmetro | Valor |
|-----------|-------|
| Classe | `PipelineTransitionAgent(EnhancedAgentMixin, BaseAgent)` |
| Domain | `"pipeline"` |
| Tools | `get_pipeline_transition_tools()` (20 tools) |
| System prompt | `get_pipeline_system_prompt(guardrails, memory_context)` |
| Guardrails | 13D.5 — #1-#6 globais + #5 (rejeição sem HITL proibida) + #11 (`pipeline`: gate humano antes de rejeição em massa) |
| Particularidade | ReAct + HITL — `validate_transition` chama PolicyEngine + FairnessGuard. HITL interrupt obrigatório em Gate 1/2. Maior contagem de tools Alpha 1 (20). |

#### Para Alpha 1
- Configurar para Gate 1 (pós-triagem CV) e Gate 2 (pós-WSI)
- Gate 1: HITL obrigatório antes de aprovar/rejeitar
- Gate 2: HITL obrigatório + fairness check antes de rejeitar
- Garantir que `check_rejection_fairness` funciona com FairnessGuard

---

### 14.10 Hiring Policy Agent ⚠️ [ALPHA 1 — P1 Sprint 1, modo serviço]
**Tipo:** ReAct Agent (4-file pattern) — **Alpha 1 usa 4 tools como serviço, sem agente conversacional**
**Padrão Arquitetural:**
- **ReAct puro (4-file pattern):** `policy_react_agent.py` + `policy_tool_registry.py` + `policy_system_prompt.py` + `policy_domain.yaml`
- **Sem LangGraph** — ciclo ReAct iterativo com 13 tools (políticas de contratação, compliance, diversity scoring)
- **Alpha 1:** Não instancia o agente conversacional. As 4 tools essenciais são chamadas diretamente pelo Orchestrator/PipelineTransition/CVScreening como serviço de políticas
- V5: Mesma arquitetura (policy_react_agent.py)

> **⚠️ RECLASSIFICAÇÃO:** Originalmente marcado como "PÓS-ALPHA P1". Reclassificado para **Alpha 1 P1 Sprint 1 (modo serviço)** porque:
> 1. `get_current_policy` + `apply_industry_defaults` definem os defaults que seriam hardcoded — é mais limpo e escalável usar o serviço
> 2. `validate_policy_compliance` chama o FairnessGuard — compliance é Inegociável (Guia v3.3)
> 3. `save_policy_block` permite configurar regras por cliente (pesos de scoring, SLAs, critérios de elegibilidade) sem SQL manual
> 4. Triagem (Ag.3) e Gates (Ag.9) **dependem** de políticas configuradas para funcionar corretamente

**Prioridade:** P1 (Sprint 1 Alpha 1 — modo serviço)
**Agente LIA:** `app/domains/policy/agents/agent.py`
**V5 Correspondente:** `src/domains/hiring_policy/policy_react_agent.py` (mesma arquitetura)

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/policy/agents/agent.py` | PolicySetupAgent — 19 perguntas, 5 blocos |
| `app/domains/policy/agents/system_prompt.py` | EXTRACTION_PROMPT + REPLY_PROMPT |
| `app/domains/policy/agents/tool_registry.py` | POLICY_TOOLS = [] (LLM direto, sem tools) |
| `app/domains/policy/agents/stage_context.py` | QUESTIONS (19), BLOCK_NAMES (5 blocos), PolicySetupSession |
| `app/agents/policy_setup_agent.py` | Shim de retrocompatibilidade (re-exporta do novo path) |

#### Tools — Alpha 1 (4 tools como serviço)
| Tool | O que faz | Serviço | Consumidor Alpha 1 |
|------|----------|---------|-------------------|
| `get_current_policy` | Carrega políticas da empresa | DB: company_hiring_policies | Orchestrator, CVScreening, PipelineTransition |
| `save_policy_block` | Salva bloco inteiro de política | DB | Setup inicial do cliente (onboarding) |
| `apply_industry_defaults` | Aplica padrões do setor em lote | DB | Setup inicial do cliente (onboarding) |
| `validate_policy_compliance` | Verifica viés/violações | **FairnessGuard** | CVScreening (pré-triagem), PipelineTransition (pré-Gate) |

#### Tools — Pós-Alpha (9 tools restantes)
| Tool | O que faz | Serviço | Por que pós-Alpha |
|------|----------|---------|-------------------|
| `save_policy_field` | Salva campo individual de política | DB | Granularidade de edição — Alpha 1 usa `save_policy_block` |
| `get_policy_summary` | Resumo das políticas ativas | DB | Interface conversacional |
| `get_company_context` | Dados contextuais da empresa | DB | Enriquecimento conversacional |
| `get_industry_benchmarks` | SLAs e práticas de mercado | INDUSTRY_BENCHMARKS | Consultoria — nice-to-have |
| `explain_policy_impact` | Explica impacto de uma política | LLM | Análise consultiva |
| `get_setup_progress` | Progresso do setup | DB | UX conversacional |
| `get_platform_benchmarks` | Performance real da plataforma | DB Analytics | Analytics pós-Alpha |
| `detect_policy_impact_anomalies` | Detecta anomalias | Analytics | Analytics pós-Alpha |
| `get_policy_effectiveness_report` | Impacto das políticas | DB Analytics | Analytics pós-Alpha |

#### API Endpoints
| Método | Endpoint | Fase | Descrição |
|--------|---------|:----:|-----------|
| REST | `/hiring-policy/current` | Alpha 1 | GET política atual (chamado internamente) |
| REST | `/hiring-policy/apply-defaults` | Alpha 1 | POST aplicar defaults do setor |
| REST | `/hiring-policy/save-block` | Alpha 1 | POST salvar bloco de política |
| REST | `/hiring-policy/validate` | Alpha 1 | POST validar compliance (FairnessGuard) |
| REST | `/hiring-policy/*` | Pós-Alpha | Demais endpoints do PolicyReActAgent |
| WS | `/ws/chat/{session_id}` (domain=`policy`) | Pós-Alpha | WebSocket conversacional |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`policy`)

#### Implementação — Padrão ReAct 13B.7
| Parâmetro | Valor |
|-----------|-------|
| Classe | `PolicyReActAgent(EnhancedAgentMixin, BaseAgent)` |
| Domain | `"policy"` |
| Tools | `get_policy_tools()` (13 tools — Alpha 1: 4 como serviço) |
| System prompt | `get_policy_system_prompt(guardrails, memory_context)` |
| Guardrails | 13D.5 — #1-#6 globais + #13 (`policy`: alterações requerem confirmação explícita) |
| Particularidade | **Alpha 1 usa 4 tools como serviço** — não instancia o ReAct loop. `validate_policy_compliance` chama FairnessGuard (13D.1). Pós-Alpha ativa o agente conversacional completo. |

#### Para Alpha 1 (modo serviço)
1. **Sprint 1:** Expor as 4 tools como endpoints REST internos (sem agente conversacional)
2. **Sprint 1:** Integrar `get_current_policy` no Orchestrator (carrega políticas no contexto de cada execução)
3. **Sprint 1:** Integrar `validate_policy_compliance` no CVScreening (antes de triagem) e PipelineTransition (antes de Gate 1/2)
4. **Sprint 1:** Criar script de onboarding que chama `apply_industry_defaults` + `save_policy_block` para cada novo cliente
5. **Pós-Alpha:** Habilitar agente conversacional completo (13 tools + WebSocket) para consultor configurar políticas via chat

---

### 14.11 Kanban Agent [PÓS-ALPHA — P2]
**Tipo:** ReAct Agent (4-file pattern)
**Padrão Arquitetural:**
- **ReAct puro (4-file pattern):** `kanban_react_agent.py` + `kanban_tool_registry.py` + `kanban_system_prompt.py` + `kanban_domain.yaml`
- **Sem LangGraph** — ciclo ReAct iterativo com 22 tools (pipeline ops, drag-drop, batch, filtros)
- **Maior contagem de tools pós-Alpha** (22 tools)
- V5: Mesma arquitetura (kanban_react_agent.py)

**Prioridade:** P2
**Agente LIA:** `app/domains/recruiter_assistant/agents/kanban_react_agent.py`
**V5 Correspondente:** `src/domains/recruiter_assistant/kanban_react_agent.py` (mesma arquitetura)

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/recruiter_assistant/agents/kanban_react_agent.py` | Agente ReAct |
| `app/domains/recruiter_assistant/agents/kanban_tool_registry.py` | 22 tools |
| `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` | System prompt |

#### Tools (22)
| Tool | O que faz | Serviço |
|------|----------|---------|
| `view_candidate_full_profile` | Perfil completo | DB |
| `get_pipeline_benchmarks` | Benchmarks do pipeline | DB Analytics |
| `get_pipeline_summary` | Resumo do pipeline | DB |
| `get_stage_metrics` | Métricas por estágio | DB |
| `list_stage_candidates` | Lista candidatos por estágio | DB |
| `analyze_stage` | Análise de estágio | Analytics |
| `identify_bottlenecks` | Identifica gargalos | Analytics |
| `get_candidate_aging` | Aging de candidatos | DB |
| `compare_stages` | Compara estágios | Analytics |
| `suggest_movements` | Sugere movimentações | LLM |
| `batch_move_candidates` | Move em lote | DB batch |
| `send_batch_communication` | Comunicação em lote | CommunicationService |
| `start_screening_batch` | Inicia triagem em lote | ScreeningService |
| `generate_pipeline_report` | Relatório do pipeline | Report Generator |
| `check_rejection_fairness` | Verifica viés | FairnessGuard |
| `find_silver_medalists` | Encontra silver medalists | SilverMedalistService |
| `get_recruiter_backlog` | Backlog do recrutador | DB |
| `get_recruiter_benchmark` | Benchmark do recrutador | RecruiterMetricsService |
| `get_journey_metrics` | Métricas de jornada | JourneyIntelligenceService |
| `get_at_risk_candidates` | Candidatos em risco | EarlyWarningService |
| `get_pipeline_prediction` | Previsão de pipeline | PipelinePredictionService |
| `get_pipeline_velocity` | Velocidade do pipeline | PipelineVelocityService |

#### Serviços Exclusivos
| Serviço | Arquivo | Função |
|---------|--------|--------|
| RecruiterMetricsService | `app/services/recruiter_metrics_service.py` | Métricas do recrutador |
| JourneyIntelligenceService | `app/services/journey_intelligence_service.py` | Inteligência de jornada |
| PipelinePredictionService | `app/services/pipeline_prediction_service.py` | Previsão de outcomes |
| EarlyWarningService | `app/services/early_warning_service.py` | Alertas antecipados |
| SilverMedalistService | `app/services/silver_medalist_service.py` | Silver medalists |
| PipelineVelocityService | `app/services/pipeline_velocity_service.py` | Velocidade de movimentação |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| REST | `/orchestrator/job-chat/*` | KanbanReActAgent endpoints |
| WS | `/ws/chat/{session_id}` (domain=`kanban`) | WebSocket |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`recruiter_assistant`, agente=`kanban`)

#### Para Alpha 1
- Útil para visualização do pipeline pelo consultor
- Prioridade P2 — implementar se houver tempo no Sprint 3

---

### 14.12 Talent Agent [PÓS-ALPHA — P2]
**Tipo:** ReAct Agent (4-file pattern)
**Padrão Arquitetural:**
- **ReAct puro (4-file pattern):** `talent_react_agent.py` + `talent_tool_registry.py` + `talent_system_prompt.py` + `talent_domain.yaml`
- **Sem LangGraph** — ciclo ReAct iterativo com 12 tools (recomendações proativas, market insights, comparação)
- **Agente default do Orchestrator** — quando `domain` param não é especificado, vai para este agente
- V5: Mesma arquitetura (talent_react_agent.py)

**Prioridade:** P2
**Agente LIA:** `app/domains/recruiter_assistant/agents/talent_react_agent.py`
**V5 Correspondente:** `src/domains/recruiter_assistant/talent_react_agent.py` (mesma arquitetura)

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/recruiter_assistant/agents/talent_react_agent.py` | Agente ReAct |
| `app/domains/recruiter_assistant/agents/talent_tool_registry.py` | 12 tools |

#### Tools (12)
| Tool | O que faz |
|------|----------|
| `search_candidates` | Busca candidatos |
| `list_candidates` | Lista candidatos |
| `view_candidate_profile` | Perfil do candidato |
| `compare_candidates` | Comparação lado a lado |
| `rank_candidates` | Ranking por score |
| `analyze_skills` | Análise de skills |
| `recommend_actions` | Recomendações IA |
| `create_shortlist` | Cria shortlist |
| `export_report` | Exporta relatório |
| `check_search_fairness` | Verifica viés na busca |
| `get_talent_pool_benchmarks` | Benchmarks do talent pool |
| `check_pool_health` | Saúde do talent pool |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| REST | `/orchestrator/talent-chat/*` | TalentReActAgent endpoints |
| WS | `/ws/chat/{session_id}` (domain=`talent`, default) | WebSocket (agente default) |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`recruiter_assistant`, agente=`talent`)

---

### 14.13 Analytics Agent [PÓS-ALPHA — P2]
**Tipo:** ReAct Agent (4-file pattern)
**Padrão Arquitetural:**
- **ReAct puro (4-file pattern):** `analytics_react_agent.py` + `analytics_tool_registry.py` + `analytics_system_prompt.py` + `analytics_domain.yaml`
- **Sem LangGraph** — ciclo ReAct iterativo com 6 tools (insights, reports, funnel metrics, predictive analytics)
- **9 serviços de suporte:** job_analytics, insights, predictive, reports, search_analytics — ver camada 13C.12
- V5: Mesma arquitetura (analytics_react_agent.py)

**Prioridade:** P2
**Agente LIA:** `app/domains/analytics/agents/analytics_react_agent.py`
**V5 Correspondente:** `src/domains/analytics/analytics_react_agent.py` (mesma arquitetura)

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/analytics/agents/analytics_react_agent.py` | Agente ReAct |
| `app/domains/analytics/agents/analytics_tool_registry.py` | 6 tools |

#### Tools (6)
| Tool | O que faz | Serviço |
|------|----------|---------|
| `get_job_insights` | Insights por vaga | JobInsightsService |
| `predict_hiring_metrics` | Previsão de métricas | PredictiveAnalyticsService |
| `generate_job_report` | Relatório por vaga | JobReportService |
| `generate_candidate_report` | Relatório por candidato | CandidateReportService |
| `get_search_analytics` | Analytics de busca | SearchAnalyticsService |
| `get_agent_performance` | Performance dos agentes | AgentMonitoringService |

#### Serviços
| Serviço | Arquivo |
|---------|--------|
| JobInsightsService | `app/domains/analytics/services/job_insights_service.py` |
| PredictiveAnalyticsService | `app/domains/analytics/services/predictive_analytics_service.py` |
| JobReportService | `app/domains/analytics/services/job_report_service.py` |
| CandidateReportService | `app/domains/analytics/services/candidate_report_service.py` |
| SearchAnalyticsService | `app/domains/analytics/services/search_analytics_service.py` |
| AgentMonitoringService | `app/shared/governance/agent_monitoring_service.py` |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| REST | `/wsi-observability/*` | Observabilidade WSI |
| REST | `/agent-monitoring/*` | Monitoramento de agentes |
| WS | `/ws/chat/{session_id}` (domain=`analytics`) | WebSocket |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`analytics`)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| Analytics Services | 13C.12 | 9 arquivos (insights, predictive, reports, search analytics) |
| Observabilidade | 13C.11 | `agent_monitoring_service.py`, `wsi_observability.py` |

---

### 14.14 Automation Agent [PÓS-ALPHA — P1 (infra roda)]
**Tipo:** ReAct Agent (4-file pattern) + Scheduler infra (roda sem agente conversacional)
**Padrão Arquitetural:**
- **ReAct puro (4-file pattern):** `automation_react_agent.py` + `automation_tool_registry.py` + `automation_system_prompt.py` + `automation_domain.yaml`
- **Sem LangGraph** — ciclo ReAct iterativo com 6 tools (gerenciar regras, triggers, jobs)
- **Dual mode no Alpha 1:**
  - ❌ Agente conversacional NÃO entra no Alpha 1
  - ✅ `AutomationScheduler` (10 jobs) + `StageAutomationEngine` (8 triggers) RODAM como infra
- **Infra que roda sem agente:** Os 10 jobs agendados e 8 triggers de evento rodam via scheduler background — não precisa do agente ReAct conversacional
- V5: Mesma arquitetura (automation_react_agent.py + automation_scheduler.py)

**Prioridade:** P1 (agente conversacional não entra no Alpha 1, mas 10 jobs + 8 triggers rodam como infra)
**Agente LIA:** `app/domains/automation/agents/automation_react_agent.py`
**V5 Correspondente:** `src/domains/automation/automation_react_agent.py` + `automation_scheduler.py` (mesma arquitetura)

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/automation/agents/automation_react_agent.py` | Agente ReAct |
| `app/domains/automation/agents/automation_tool_registry.py` | 6 tools |
| `app/domains/automation/services/automation_scheduler.py` | Scheduler (10 jobs) |
| `app/domains/automation/services/stage_automation_engine.py` | Engine de automação por estágio |
| `app/domains/automation/services/automation_trigger_service.py` | Triggers proativos |
| `app/domains/automation/services/automation_handlers.py` | Handlers de eventos |

#### Tools (6)
| Tool | O que faz |
|------|----------|
| `decompose_task` | Decompõe tarefa complexa em subtarefas |
| `prioritize_tasks` | Prioriza lista de tarefas |
| `get_execution_plan` | Plano de execução |
| `build_dag` | Constrói DAG de dependências |
| `check_dependencies` | Verifica dependências |
| `get_next_tasks` | Próximas tarefas a executar |

#### Jobs Agendados (10)
| Job | Frequência | O que faz |
|-----|-----------|----------|
| `check_inactive_candidates` | A cada 1h | Candidatos sem atividade 7+ dias |
| `check_interview_no_shows` | A cada 30m | Detecta no-shows |
| `send_interview_reminders` | A cada 15m | Lembretes 24h/1h |
| `check_expiring_vacancies` | Diário 09:00 | Vagas próximas do deadline |
| `cleanup_stale_reminders` | Diário 00:00 | Limpa flags obsoletos |
| `auto_complete_screenings` | A cada 1h | Triagens expiradas |
| `pipeline_monitor` | A cada 30m | Saúde do pipeline |
| `learning_automation` | A cada 6h | Padrões e promoção de skills |
| `expire_trials` | Diário 01:00 | Trials expirados |
| `run_lgpd_cleanup` | Diário 02:00 | Cleanup LGPD |

#### Triggers por Evento (8)
| Evento | Ação |
|--------|------|
| `SCREENING_COMPLETED` | Log + email feedback |
| `STAGE_CHANGED` | Log transição + auto-agenda se Interview |
| `CANDIDATE_REJECTED` | Email rejeição + talent pool |
| `INTERVIEW_SCHEDULED` | Confirmação + evento calendário |
| `INTERVIEW_COMPLETED` | Parecer IA |
| `CANDIDATE_HIRED` | Sync ATS + onboarding |
| `OFFER_SENT` | Monitora resposta |
| `ATS_SYNC` | Sincroniza com ATS externo |

#### Triggers Proativos por Tempo (5)
| Trigger | Threshold | Ação |
|---------|----------|------|
| `CANDIDATE_NO_CONTACT_48H` | 48h | Follow-up + tarefa |
| `SCORECARD_PENDING_24H` | 24h | Notifica entrevistador |
| `JOB_NO_MOVEMENT_5D` | 5 dias | Alerta vaga estagnada |
| `FEEDBACK_PENDING_48H` | 48h | Escalação prioridade alta |
| `JOB_DEADLINE_APPROACHING` | 3 dias | Alerta severidade alta |

#### API Endpoints
| Método | Endpoint | Descrição |
|--------|---------|-----------|
| POST | `/automation/trigger-event` | Dispara evento |
| REST | `/tasks/*` | AutomationReActAgent |
| REST | `/proactive-actions/*` | AutonomousAgentService |
| REST | `/transition/*` | Stage transition |

#### Roteiro de Reprodução
→ Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`automation`)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| Comunicação | 13C.5 | Dispatch automático em transições |
| Observabilidade | 13C.11 | Monitoring + alerts para jobs agendados |
| Config/Infra | 13C.14 | `config.py` (thresholds, feature flags) |

#### Para Alpha 1
- Garantir que AutomationScheduler está rodando com os 10 jobs
- Configurar thresholds Alpha 1: follow-up 7 dias (não 48h), timeout triagem 48h
- Validar que StageAutomationEngine dispara corretamente em transições

---

### 14.15 Jobs Management Agent [PÓS-ALPHA — P2]
**Tipo:** ReAct Agent (4-file pattern)
**Padrão Arquitetural:**
- **ReAct puro (4-file pattern):** `jobs_mgmt_react_agent.py` + `jobs_mgmt_tool_registry.py` + `jobs_mgmt_system_prompt.py` + `jobs_mgmt_stage_context.py`
- **Sem LangGraph** — ciclo ReAct iterativo com 14 tools (gerenciar portfólio de vagas)
- **Localização:** `app/domains/recruiter_assistant/agents/` (mesmo domínio que Kanban e Talent)
- **Escopo:** Visão macro do portfólio de vagas — métricas, SLA, bottlenecks, ações estratégicas
- V5: Mesma arquitetura (`recruiter_assistant/jobs_mgmt_react_agent.py`)

**Prioridade:** P2 (gerenciamento de portfólio de vagas — pós-Alpha 1)
**Agente LIA:** `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` (635 linhas)
**V5 Correspondente:** `src/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py`

> **Adicionado v5.0:** Agente identificado na análise investigativa do codebase. Segue padrão 4-file idêntico ao Kanban/Talent. FairnessGuard integrado (`validate_job_action_fairness`).

#### Arquivos
| Arquivo | Função |
|---------|--------|
| `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | Agente ReAct (635 linhas) |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py` | 14 tools (911 linhas) |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` | System prompt PT-BR (186 linhas) |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_stage_context.py` | Contexto de estágio + predições |

#### Tools (14)
| Tool | O que faz |
|------|----------|
| `list_jobs` | Lista vagas com filtros (status, prioridade, recrutador) |
| `view_job_details` | Detalhes completos de uma vaga |
| `get_portfolio_metrics` | Métricas do portfólio (TTF, fill rate, ativas, etc.) |
| `compare_jobs` | Compara vagas lado a lado |
| `check_sla` | Verifica compliance SLA das vagas |
| `analyze_bottlenecks` | Identifica gargalos no processo |
| `get_recruitment_benchmarks` | Benchmarks de recrutamento por período |
| `pause_job` | Pausa uma vaga |
| `reopen_job` | Reabre uma vaga pausada/fechada |
| `close_job` | Fecha uma vaga |
| `update_priority` | Atualiza prioridade de uma vaga |
| `generate_report` | Gera relatório do portfólio |
| `get_pipeline_prediction` | Predição de pipeline por vaga |
| `validate_job_action_fairness` | FairnessGuard — valida ações sem bias |

#### Roteiro de Reprodução
> Ver seção **13C.17 — Para reproduzir um agente ReAct** (domínio=`recruiter_assistant`, agente=`jobs_mgmt`)

#### Camadas de Suporte Obrigatórias
| Camada | Seção | Arquivos Relevantes |
|--------|-------|---------------------|
| FairnessGuard | 13D.1 | `validate_job_action_fairness` integrado |
| Observabilidade | 13C.11 | Monitoring para ações de portfólio |
| Config/Infra | 13C.14 | `config.py` (SLA thresholds, feature flags) |

---

## 15. CAPACIDADES EXCLUSIVAS V5 — RESUMO CONSOLIDADO

| # | Capacidade V5 | Arquivo V5 | Agente LIA Afetado | Status LIA | Impacto |
|---|-------------|-----------|-------------------|:----------:|---------|
| 1 | Multi-Stage Eval Graph | `evaluation/graph.py` | CV Screening (14.4) | LIA tem WSI Graph diferente | 🟡 |
| 2 | Tool Execution Hooks | `tools/hooks.py` | Todos (infra) | ❌ Ausente | 🟡 |
| 3 | Tool Contracts | `tools/contracts.py` | Todos (infra) | ⚠️ Pydantic/YAML | 🟢 |
| 4 | YAML-to-Tool Factory | `utils/yaml_to_tools.py` | ATS Integration (14.8) | ⚠️ Diferente | 🟡 |
| 5 | Prompt Builder Dinâmico | `prompt_builder/` | Sourcing (14.3) | ⚠️ YAML registry | 🟢 |
| 6 | FactChecker domain-specific | `fact_checker.py` | Sourcing (14.3) | ⚠️ Genérico | 🟡 |
| 7 | PromptInjectionGuard integrado | `security.py` | WSI (14.5) + CV Screening (14.4) | ✅ **Wired SEG-1** — `wsi_interview_graph.validate_response` + `agent_chat_ws.py` | 🟢 |
| 8 | Confirmation Builder | `confirmation_builder.py` | Pipeline Transition (14.9) | ⚠️ HITL genérico | 🟢 |
| 9 | RabbitMQ modular | `rabbitmq_service.py` | Automation (14.14) | ⚠️ LIA tem consumer | 🟡 |
| 10 | OTT Service | `ott_service.py` | WSI (14.5) | ❌ Ausente | 🟡 |
| 11 | ParamExtractor | `param_extractor.py` | Sourcing (14.3) | ❌ Ausente | 🟡 |
| 12 | Template Formatter | `template_formatter.py` | Sourcing (14.3) | ⚠️ Genérico | 🟢 |
| 13 | Final Analysis | `final_analysis.py` | Pipeline Transition (14.9) — Gate 2 | ❌ Ausente | 🟡 |
| 14 | Validators domain-specific | `validators.py` | Sourcing (14.3) | ⚠️ Inline | 🟢 |

---

## 16. GAPS VERDADEIROS E ESTIMATIVA FINAL

### 16.1 Gaps que requerem implementação nova (absent em ambos)
1. **Email tracking pixel** (abertura/clique) — afeta Communication Agent (14.7) — implementar do zero
2. **Inscrição web bypass Gate 1** (flag source) — afeta Pipeline Transition (14.9) — regra de negócio nova
3. **Feedback diferenciado por Gate** (construtivo vs final) — afeta Communication Agent (14.7) — template novo

### 16.2 Gaps de Segurança e Governança — ✅ TODOS RESOLVIDOS (Sprints SEG-1 a SEG-5)

> **Atualizado v3.0:** Os 5 gaps críticos de segurança/governança foram implementados e testados em 11/03/2026. 34 testes unitários adicionados, 0 regressões. Auditoria de governança: 8/8 Inegociáveis ✅.

4. ~~**PromptInjectionGuard**~~ → ✅ **Resolvido SEG-1:** `wsi_interview_graph.validate_response()` + singleton `_injection_guard` em `agent_chat_ws.py`. 6 categorias de injection, high→block, medium→log.
5. ~~**FairnessGuard no screening**~~ → ✅ **Resolvido SEG-2:** `sourcing_react_agent.process()` + `pipeline_transition_agent.process()`. `check()` + `check_implicit_bias()` com fail-safe.
6. ~~**Consent antes do pipeline**~~ → ✅ **Resolvido SEG-4:** `ConsentCheckerService.check_candidate_consent(purpose="ai_screening")` em `wsi_interview_graph.load_context()`. Revogado→`LGPD_CONSENT_REVOKED`. Fail-safe.
7. ~~**PII Masking nos logs**~~ → ✅ **Resolvido SEG-3A/3B:** Celery workers via `worker_process_init` signal. `strip_pii_for_llm_prompt()` em `rubric_evaluation_service.py`, `analysis_service.py`, `voice_screening_analysis.py`, `candidate_comparison_service.py`.
8. ~~**Audit trail nos Gates**~~ → ✅ **Resolvido SEG-5:** `audit_service.log_decision()` com `PROTECTED_CRITERIA` em `criteria_ignored`. Pipeline (HITL pending + transition completed + LangGraph path + HITL rejected) + Sourcing (ReAct loop + LangGraph path). Fail-safe.

### 16.3 Gaps de Compliance (módulos LIA existem, requerem configuração — ALTO)
9. **Bias Audit baseline** — `app/api/v1/bias_audit.py` → rodar disparity ratios antes do go-live (NYC LL144 + EU AI Act)
10. **PolicyEngine sem regras Alpha 1** — `app/orchestrator/policy_engine.py` → configurar via HiringPolicyService (Ag.10 modo serviço: `apply_industry_defaults` + `save_policy_block`)
11. **FRIA não documentado** — template compliance existe → preencher para screening WSI (EU AI Act Art. 6 Annex III)
12. **Circuit breakers sem config** — infra existe → configurar para Anthropic/OpenAI/Gemini
13. **Data retention não configurado** — `LgpdCleanupService` → definir 90/180/365 dias para dados Alpha 1 (LGPD Art. 16)
14. **DSR workflow não testado** — `app/api/v1/data_subject_requests.py` → testar 5 tipos: acesso, correção, exclusão, portabilidade, objeção (LGPD Art. 18)

### 16.4 Conclusão
O trabalho do Alpha 1 NÃO é construir agentes — **todos os 15 agentes existem**. O trabalho é:
1. **Wiring de Agentes:** Conectar agentes existentes no fluxo Alpha 1
2. ~~**Wiring de Governança:**~~ ✅ **Concluído (SEG-1 a SEG-5)** — FairnessGuard, PromptInjectionGuard, PII Masking, Consent e Audit estão todos wired
3. **Configuração:** Parametrizar automações, policies e retention para regras Alpha 1
4. **Integração:** ATS sync com pelo menos 1 provedor real
5. **Compliance:** Rodar bias audit baseline, preencher FRIA, testar DSR workflow
6. **Templates:** Email Alpha 1 + feedback diferenciado
7. **Testing:** Testes end-to-end do fluxo completo + validação de compliance

### 16.5 Estimativa Revisada
| Categoria | Story Points |
|----------|:-----------:|
| Wiring/Configuração de agentes existentes | ~30 SP |
| ~~**Wiring de Governança/Compliance**~~ | ~~**~15 SP**~~ → **✅ CONCLUÍDO (SEG-1 a SEG-5)** |
| Novas funcionalidades (tracking, bypass, feedback diferenciado) | ~15 SP |
| Templates de email + feedback diferenciado | ~8 SP |
| Chat Web (adaptar WebSocket) | ~8 SP |
| ATS Integration (validar com provedor real) | ~8 SP |
| **Compliance pre-go-live** (bias baseline, FRIA, DSR test, retention config) | **~10 SP** |
| Testes end-to-end | ~15 SP |
| **TOTAL REVISADO** | **~109 SP** |

### 16.6 Capacidades Ausentes Identificadas (v5.0 — Análise Profunda)

> **Fonte:** Cruzamento do `relatorio_capacidades_prompts_lia.md` seção 9 com investigação direta do codebase

#### 16.6.1 Ausentes — Sem implementação

| # | Capacidade | Status | Descrição | Complexidade | Impacto | Arquivos Relevantes |
|---|-----------|--------|-----------|-------------|---------|---------------------|
| 1 | **LIA Score clicável no funil** | Ausente | Recrutador clica no score e vê breakdown (rubricas, WSI, prereq, recency) com explicação | Média | Alto | `lia_score_service.py`, `candidates-page.tsx` |
| 2 | **Fit cultural com dados de entrevista** | Ausente | Avaliar fit cultural cruzando dados de entrevistas reais (notas, sentimento, valores) | Alta | Alto | `lia_score_service.py`, `pipeline_react_agent.py` |
| 3 | **WSI assíncrono** | Ausente | Enviar triagem WSI e processar respostas quando o candidato responder (fluxo offline) | Alta | Alto | `wsi_screening` tool, `pipeline_react_agent.py` |
| 4 | **Relatório cross-vagas** | Ausente | Dashboard consolidado comparando métricas entre TODAS as vagas (TTF, qualidade, custo, fontes) | Média | Médio | `job_analytics_prompt_service.py`, `job-report-modal.tsx` |
| 5 | **WSI Voice (voz)** | Ausente | Triagem WSI por voz (speech-to-text + text-to-speech) — atualmente text-only | Alta | Médio | `voice_provider.py`, `wsi_interview_graph.py` |
| 6 | **Notificação WhatsApp em Job Created** | Ausente | `JobCreatedNotificationRequest` suporta email + Teams mas não WhatsApp | Baixa | Baixo | `communication_service.py` |

#### 16.6.2 Parcialmente implementados — Requerem completar

| # | Capacidade | Status | Gap | Complexidade | Impacto | Arquivos Relevantes |
|---|-----------|--------|-----|-------------|---------|---------------------|
| 7 | **Análise comparativa visual** | Parcial | `compare_candidates` tool existe mas resultado só aparece como texto no chat; falta componente UI lado-a-lado | Média | Alto | `analytics_query_tools.py`, `kanban_assistant_prompts.py` |
| 8 | **Auto-routing aprendiz** | Parcial | CascadedRouter usa cache (velocidade) mas não faz aprendizado; peso dos tiers é estático | Alta | Alto | `cascaded_router.py`, `llm_cascade.py` |
| 9 | **Insights proativos no Kanban** | Parcial | SaturationBadge existe mas é reativo (badge estático); falta ProactiveAgentWorker no kanban UI | Média | Médio | `SaturationBadge.tsx`, `proactive_agent_worker.py` |
| 10 | **ML adaptativo** | Parcial | `Calibration_Adjustment` na fórmula do LIA Score é sempre = 0; falta loop de feedback de contratações reais | Alta | Alto | `lia_score_service.py`, `learning_analytics_service.py` |
| 11 | **Benchmark salarial real** | Parcial | Benchmark usa IA para estimar; não há integração com fontes reais (Glassdoor, Levels.fyi) | Média | Médio | `job_wizard_tools.py` |
| 12 | **JobReportModal** | Parcial | Dados hardcoded no frontend (funnelMetrics, channelPerformance, timeline, budget); sem integração backend | Média | Alto | `job-report-modal.tsx` |

#### 16.6.3 Dívidas técnicas e fragilidades

| # | Dívida | Descrição | Impacto |
|---|--------|-----------|---------|
| 13 | **Detecção por keywords frágil** | `isGenericQuestion()` (5 regex + 46 keywords), `analysisCommands[]` (8 strings fixas), `detect_command_type()` (keywords) — falham para variações de linguagem | Alto |
| 14 | **Arquivos monolíticos** | `candidates-page.tsx` (10.398 linhas), `lia-api.ts` (4.943 linhas) — dificultam manutenção | Médio |
| 15 | **IntentRouter legado** | Coexiste com LLM Cascade como fallback; duplicação de lógica de roteamento | Baixo |
| 16 | **AgentFactory vs get_agent** | Dois padrões coexistem; `get_agent()` NÃO é session-safe mas é usado em código legado | Médio |
| 17 | **Cache Tier 1 não-distribuído** | LRU in-process, não compartilhado entre workers; eviction FIFO | Baixo |
| 18 | **Escopo GLOBAL incoerente** | `scope_config.py` limita a 2 tools, mas chat-page envia tudo ao Orchestrator que ignora scope na execução | Médio |
| 19 | **handleOpenRubricAnalysis orphaned** | Função em `candidates-page.tsx` (~linha 6424) sem call sites; modal renderiza mas não é acessível via botão | Baixo |
| 20 | **PolicyEngine nullable** | DB service pode ser `None`; validação pode falhar silenciosamente | Médio |

#### 16.6.4 Fallbacks hardcoded

| Componente | Comportamento de Fallback |
|-----------|--------------------------|
| Orchestrator | Se LLM falha, retorna: "Olá! Sou a LIA..." com 3 sugestões fixas |
| CascadedRouter | Se nenhum tier resolve, retorna clarificação com 6 opções fixas |
| VectorSemanticCache | Se pgvector indisponível, pula silenciosamente (graceful) |
| PlanDetector | Falha silenciosa via try/except (non-blocking) |
| Kanban análise | Templates retornam dados do banco local quando LLM falha |
| Kanban ações | Retorna: "Desculpe, ocorreu um erro ao processar sua requisição." |
| Analytics | Retorna `{"success": false, "error": str(e)}` — sem template offline alternativo |

### 16.7 Processamento Local vs IA — Mapa de Referência

> **Fonte:** `relatorio_capacidades_prompts_lia.md` seção 8.1

| Funcionalidade | Execução | Tipo |
|---------------|----------|------|
| LIA Score | Local (sem LLM) — fórmula ponderada | Determinístico |
| Busca de candidatos | Local (PostgreSQL) + API externa (Pearch AI) | Híbrido |
| Distribuições/Analytics | Local — contagens e agrupamentos | Determinístico |
| SaturationBadge | Local — threshold vs contagem | Determinístico |
| JobReportModal | Local — dados hardcoded no frontend (mock) | Mock |
| Avaliação por rubrica | IA real (Claude via Pipeline Agent) | IA |
| WSI Screening | IA real (Claude via Pipeline Agent) | IA |
| Comparação candidatos | IA real (Claude via Kanban/Analytics Agent) | IA |
| Ranking candidatos | IA real (Claude via Kanban Agent) | IA |
| JD Enriquecida | IA real (Claude via Wizard Agent) | IA |
| Benchmark salarial | IA real (Claude) + dados de mercado | IA + dados |

## APÊNDICE A — ARQUIVOS DE REFERÊNCIA

### V5 (GitHub: talensestg/recruiter_agent_v5)
```
src/
├── agents/                          ← 6 agentes genéricos do workflow LangGraph
│   ├── intent_analyzer.py
│   ├── api_planner.py
│   ├── api_executor.py
│   ├── plan_validator.py
│   ├── data_processor.py
│   └── answer_formatter.py
├── domains/
│   ├── orchestrator.py              ← DomainOrchestrator (2 domínios)
│   ├── registry.py                  ← DomainRegistry (singleton)
│   ├── workflow.py                  ← DomainWorkflow
│   ├── evaluation/                  ← Domínio de avaliação WSI (LangGraph 4 nós)
│   │   ├── graph.py                 ← InterviewGraph (classify→evaluate→decide→craft)
│   │   ├── nodes.py                 ← classify_input, evaluate_response, decide_flow, craft_message
│   │   ├── state.py                 ← InterviewState (TypedDict)
│   │   ├── models.py                ← InputClassification, RubricEvaluation, FlowDecision
│   │   ├── prompts.py               ← CLASSIFY_INPUT_PROMPT, EVALUATE_RESPONSE_PROMPT
│   │   └── ...
│   └── sourced_profile_sourcing/    ← Domínio de sourcing (multi-agent interno)
│       ├── agents/                   ← 6 sub-agentes (search, detail, comparison, analytics, report, action)
│       ├── fairness.py              ← FairnessGuard (básico)
│       ├── fact_checker.py          ← FactChecker
│       ├── smart_extractor.py       ← SmartExtractor (NL→params)
│       ├── memory.py                ← Memória de sessão
│       └── ...
├── tools/
│   ├── registry.py                  ← ToolRegistry (YAML-based)
│   ├── contracts.py                 ← ToolConfig, ToolCategory
│   └── hooks.py                     ← Pre/post hooks
├── services/
│   ├── rag_service.py               ← RAGService (busca híbrida docs)
│   ├── embedding_service.py         ← EmbeddingService (pgvector)
│   ├── memory_service.py            ← MemoryService (PostgreSQL)
│   └── ...
├── workflow/
│   └── graph.py                     ← WorkflowOrchestrator (LangGraph 6 nós genéricos)
└── documentation/                   ← 67+ YAMLs de endpoints API ATS
```

### LIA (Referência — filesystem local)
```
lia-agent-system/
├── app/
│   ├── orchestrator/
│   │   ├── main_orchestrator.py             ← MainOrchestrator 3-Tier
│   │   ├── orchestrator.py                  ← Core logic
│   │   ├── cascaded_router.py               ← Router 6 tiers (Haiku→Sonnet→Opus)
│   │   ├── intent_router.py                 ← Classificador de intents
│   │   ├── pending_actions.py               ← Ações pendentes (multi-turn)
│   │   ├── vector_semantic_cache.py         ← Cache semântico (pgvector)
│   │   └── task_planner.py                  ← Planejador de tarefas
│   ├── domains/
│   │   ├── analytics/agents/                ← AnalyticsReActAgent (6 tools)
│   │   ├── ats_integration/agents/          ← ATSIntegrationReActAgent
│   │   ├── automation/agents/               ← AutomationReActAgent
│   │   │   └── services/                    ← AutomationScheduler (10 jobs)
│   │   ├── communication/agents/            ← CommunicationReActAgent
│   │   │   └── models/communication_matrix.py ← 6 triggers automáticos
│   │   ├── cv_screening/agents/             ← PipelineReAct + WSIInterviewGraph
│   │   ├── hiring_policy/agents/            ← PolicyReActAgent (13 tools)
│   │   ├── interview_scheduling/agents/     ← InterviewGraph (6 nós)
│   │   ├── job_management/agents/           ← WizardReAct + JobWizardGraph
│   │   ├── pipeline/agents/                 ← PipelineTransitionAgent (17+ tools, HITL)
│   │   ├── recruiter_assistant/agents/      ← TalentReActAgent + KanbanReActAgent
│   │   └── sourcing/agents/                 ← SourcingReActAgent (14 tools)
│   ├── shared/
│   │   ├── compliance/                      ← FairnessGuard, FactChecker, AuditService
│   │   ├── intelligence/                    ← SmartExtractor, EmbeddingService, SemanticSearch
│   │   ├── prompt_injection.py              ← PromptInjectionGuard (177 linhas)
│   │   ├── pii_masking.py                   ← PII Masking LGPD
│   │   ├── learning/                        ← LearningLoop, ABTesting, Personalization
│   │   ├── robustness/                      ← InputValidation, ErrorHandling, DefensivePrompts
│   │   ├── channels/                        ← MultiChannel, adapters (email, WA, Teams, SMS)
│   │   └── agents/                          ← shims → libs/agents-core
│   ├── services/                            ← 221 serviços (ver seção 18)
│   └── tools/
│       ├── tool_registry_metadata.yaml      ← 32 tools declaradas
│       ├── scope_config.py                  ← 4 scopes de acesso
│       └── registry.py                      ← Runtime registry
├── libs/
│   ├── agents-core/                         ← BaseAgent, LangGraphBase, EnhancedAgentMixin
│   ├── audit/                               ← AuditCallback, AuditWriter
│   ├── contexts/                            ← System prompts por domínio
│   └── services/                            ← Repositories compartilhados
└── langgraph.json                           ← 3 graphs declarados
```

---

## 17. RECOMENDAÇÃO — ORDEM DE CONSTRUÇÃO

> **Legenda:** 🟢 MVP CRÍTICO — bloqueia demo funcional | 🟡 MVP SUPORTE — necessário Alpha 1 completo | 🔵 PÓS-MVP — Alpha 1.1

### Sprint 0 — Infra Base (pré-requisito de tudo)
0. 🟢 **AGT-000** — Padronização & Setup Base (4-file pattern, env, Docker, checklist 18 itens)
1. 🟢 **AGT-002** — Infraestrutura Compartilhada (BaseAgent, FairnessGuard, PII Masking, AuditCallback)
2. 🟢 **AGT-003** — ATSIntegrationService (importar vagas — premissa Alpha 1)
3. 🟢 **AGT-001** — MainOrchestrator (CascadedRouter 6-Tier, HITL, roteamento)

### Sprint 1 — Busca + Comunicação + Gates (paralelo pós-S0)
4. 🟡 **AGT-004** — SourcingReActAgent (ES + PGVector + WRF + Pearch)
5. 🟢 **AGT-005** — CommunicationService + Adapters (Email + WhatsApp + Teams)
6. 🟡 **AGT-006** — JD Generator Service
7. 🟡 **AGT-017** — HiringPolicyService (4 tools como serviço)
8. 🟢 **AGT-015** — PipelineGateService (Gate 1 / Gate 2 + HITL trigger)

### Sprint 2 — Core WSI + Chat + Scheduler (paralelo pós-S1)
9.  🟢 **AGT-007** — WSIInterviewGraph (geração perguntas + triagem + scoring + feedback)
10. 🟡 **AGT-008** — CVScreeningReActAgent (triagem curricular + matching)
11. 🟢 **AGT-009** — Chat Web Canal (WebSocket candidato)
12. 🟡 **AGT-016** — EventRetryOrchestrator (Celery scheduler + DLQ)
13. 🟡 **AGT-010** — Follow-up 7 dias + Email Tracking

### Sprint 2 FE — Interface Candidato (paralelo com S2 backend)
14. 🟢 **AGT-FE-001** — Chat Web UI (interface candidato mobile-first)
15. 🟢 **AGT-FE-002** — HITLConfirmCard (aprovação consultor via chat)

### Sprint 3 — Gates HITL + Scheduling + Monitores
16. 🟢 **AGT-011** — Gate HITL Wiring (interrupt → card → approve → resume)
17. 🔵 **AGT-012** — SchedulingGraph (calendário + link reunião)
18. 🔵 **AGT-013** — Triagem Abandonada Monitor (timeout 48h)
19. 🔵 **AGT-014** — Teams/Slack Notifications (alertas consultor)

### Sprint 3 FE
20. 🔵 **AGT-FE-003** — Pipeline Status UI (dashboard consultor)

---

## 18. CARDS JIRA — ALPHA 1 (COMPLETOS)

> **Escopo:** Estes cards cobrem o pipeline automatizado de recrutamento Alpha 1. As interfaces conversacionais da LIA com o recrutador (Tabela de Vagas, Página de Vaga, Prompt Flutuante, Teams, Políticas, Funil de Talentos) e os itens de melhoria técnica recomendados por André (AUD-001 a AUD-007 + gaps técnicos) **não estão neste roadmap** — ver **Seção 22**.

### Tabela de Resumo

| Card ID | Componente | Tipo | Classificação | Prioridade | Sprint | Story Points |
|---------|-----------|------|:-------------:|:----------:|:------:|:------------:|
| AGT-000 | Padronização & Setup Base | Infra/Dev | 🟢 MVP CRÍTICO | P0 | S0 | 5 |
| AGT-001 | MainOrchestrator (3-Tier + HITL) | Orchestrator | 🟢 MVP CRÍTICO | P0 | S0 | 13 |
| AGT-002 | Infraestrutura Compartilhada | Infra | 🟢 MVP CRÍTICO | P0 | S0 | 21 |
| AGT-003 | ATSIntegrationService | Serviço | 🟢 MVP CRÍTICO | P0 | S0 | 8 |
| AGT-004 | SourcingReActAgent | ReAct | 🟡 MVP SUPORTE | P0 | S1 | 13 |
| AGT-005 | CommunicationService + Adapters | Serviço | 🟢 MVP CRÍTICO | P0 | S1 | 13 |
| AGT-006 | JD Generator Service | Serviço LLM | 🟡 MVP SUPORTE | P1 | S1 | 5 |
| AGT-017 | HiringPolicyService (modo serviço) | Serviço | 🟡 MVP SUPORTE | P1 | S1 | 5 |
| AGT-015 | PipelineGateService (Gate1/Gate2) | Serviço+HITL | 🟢 MVP CRÍTICO | P0 | S1 | 8 |
| AGT-007 | WSIInterviewGraph (Ag.4+Ag.5) | LangGraph | 🟢 MVP CRÍTICO | P0 | S2 | 21 |
| AGT-008 | CVScreeningReActAgent (Ag.3) | ReAct | 🟡 MVP SUPORTE | P1 | S2 | 8 |
| AGT-009 | Chat Web Canal (triagem candidato) | Infra | 🟢 MVP CRÍTICO | P0 | S2 | 8 |
| AGT-016 | EventRetryOrchestrator (scheduler+DLQ) | Serviço | 🟡 MVP SUPORTE | P1 | S2 | 8 |
| AGT-010 | Follow-up 7d + Email Tracking | Serviço | 🟡 MVP SUPORTE | P1 | S2 | 8 |
| AGT-011 | Gate HITL Wiring | Serviço+HITL | 🟢 MVP CRÍTICO | P0 | S3 | 8 |
| AGT-012 | SchedulingGraph (Ag.6) | LangGraph | 🔵 PÓS-MVP | P1 | S3 | 13 |
| AGT-013 | Triagem Abandonada Monitor (48h) | Serviço | 🔵 PÓS-MVP | P1 | S3 | 5 |
| AGT-014 | Teams/Slack Notifications | Serviço | 🔵 PÓS-MVP | P2 | S3 | 3 |
| AGT-FE-001 | Chat Web UI | Frontend | 🟢 MVP CRÍTICO | P0 | S2 | 8 |
| AGT-FE-002 | HITLConfirmCard | Frontend | 🟢 MVP CRÍTICO | P0 | S2 | 5 |
| AGT-FE-003 | Pipeline Status UI | Frontend | 🔵 PÓS-MVP | P1 | S3 | 5 |
| **TOTAL** | | | | | | **~188 SP** |

> **Reestimativa:** O trabalho real é de integração/wiring/configuração de serviços existentes, não construção do zero. Estimativa revisada: **~109 SP** (ver seção 16.5).

---

### AGT-000 — Padronização & Setup Base (4-File Pattern + Dev Environment)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S0 | **Prioridade:** P0 | **Story Points:** 5
**Dependências:** nenhuma — este card deve ser concluído ANTES de qualquer outro
**Seções de Referência:** 13B (blueprint completo), 13D (compliance ref), 13F (IA vs Determinístico)

**Descrição:** Card de infraestrutura de desenvolvimento. Define o padrão obrigatório para todos os agentes, a estrutura de diretórios do projeto V5, configuração do ambiente (env vars, Docker, serviços externos) e o checklist de 18 itens de produção que TODOS os agentes devem passar antes de marcar como "Done". Nenhum outro card pode ser iniciado sem este estar concluído.

**Estrutura de Diretórios V5 (a criar):**
```
src/
├── api/
│   ├── routes/          ← Endpoints FastAPI
│   └── ws/              ← WebSocket handlers
├── core/
│   ├── config.py        ← Settings Pydantic BaseSettings
│   ├── database.py      ← Async SQLAlchemy engine
│   ├── celery_app.py    ← Celery instance
│   └── seeds/           ← Seeds (guardrails, defaults)
├── domains/             ← DDD: um subdir por domínio
│   └── {domain}/
│       ├── agents/      ← 4 arquivos por agente (padrão obrigatório)
│       │   ├── {domain}_react_agent.py
│       │   ├── {domain}_system_prompt.py
│       │   ├── {domain}_tool_registry.py
│       │   └── {domain}_stage_context.py
│       └── services/    ← Serviços de negócio do domínio
├── models/              ← SQLAlchemy models
├── prompts/
│   ├── domains/         ← YAMLs por domínio ({domain}.yaml)
│   └── shared/          ← YAMLs compartilhados (lia_persona.yaml)
├── services/            ← Serviços transversais (cross-domain)
├── shared/
│   ├── agents/          ← Infra de agentes (EnhancedAgentMixin, etc.)
│   ├── compliance/      ← FairnessGuard, AuditCallback, FactChecker
│   ├── channels/        ← Adapters de comunicação (email, WhatsApp, Teams)
│   └── providers/       ← LLM providers (LLMFactory)
├── jobs/                ← Celery tasks e beat jobs
└── alembic/
    └── versions/        ← Migrations numeradas (001, 002, ...)
```

**Padrão 4-File Obrigatório por Agente:**
```
{domain}_react_agent.py    ← Classe principal (herda EnhancedAgentMixin)
{domain}_system_prompt.py  ← build_system_prompt() → str (10 seções obrigatórias)
{domain}_tool_registry.py  ← TOOL_DEFINITIONS, STAGE_TOOLS, funções wrapper async
{domain}_stage_context.py  ← get_stage_context(stage: str) → str
```

**10 Seções Obrigatórias do System Prompt:**
```
=== IDENTIDADE E PAPEL ===
=== CONTEXTO DA EMPRESA ===        ← injetado via stage_context (dinâmico)
=== FERRAMENTAS DISPONÍVEIS ===
=== REGRAS DE USO DAS FERRAMENTAS ===
=== CONTEXTO DO ESTÁGIO ATUAL ===   ← dinâmico por stage
=== GUARDRAILS E LIMITAÇÕES ===
=== COMPLIANCE E ÉTICA ===
=== EXEMPLOS DE USO (FEW-SHOT) ===  ← mínimo 2-3 exemplos
=== TRATAMENTO DE ERROS ===
=== FORMATO DE RESPOSTA ===
```

**Variáveis de Ambiente Obrigatórias (`.env.example`):**
```bash
# LLM
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/lia_v5
REDIS_URL=redis://localhost:6379

# Message Broker
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Celery
CELERY_BROKER_URL=${RABBITMQ_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Auth
WORKOS_API_KEY=
JWT_SECRET_KEY=

# Integrações Alpha 1
RESEND_API_KEY=         # Email transacional
GUPY_API_KEY=           # ATS Gupy
PEARCH_API_KEY=         # Busca candidatos externos

# Observabilidade
LANGSMITH_API_KEY=
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=lia-v5-alpha1

# Feature Flags
FAIRNESS_LAYER3_ENABLED=false   # Camada 3 LLM do FairnessGuard (opt-in)
```

**Checklist de Produção — 18 Itens (obrigatório para TODO agente antes de marcar "Done"):**

| # | Critério | Verificação |
|---|---------|------------|
| 1 | Padrão 4-file completo | `agent.py`, `system_prompt.py`, `tool_registry.py`, `stage_context.py` presentes |
| 2 | EnhancedAgentMixin herdado | `process()` implementado e funcional |
| 3 | FairnessGuard wired | Chamado em TODAS as entradas de texto do usuário |
| 4 | PromptInjectionGuard wired | Sanitiza input antes de passar ao LLM |
| 5 | AuditCallback registrado | Toda execução trackeada no DB com `company_id` |
| 6 | `company_id` propagado | Em TODAS as queries, registros e logs |
| 7 | PII Masking ativo | Loggers não expõem CPF, email, telefone |
| 8 | PolicyEngine consultado | Antes de cada execução de agente |
| 9 | Circuit breaker em uso | Em TODAS as chamadas LLM e APIs externas |
| 10 | System prompt 10 seções | Incluindo mínimo 2 few-shot examples |
| 11 | STAGE_TOOLS correto | Tools disponíveis por estágio definidas |
| 12 | Testes unitários | Mínimo 5 por tool registrada |
| 13 | Testes fairness | 5+ queries discriminatórias bloqueadas pelo FairnessGuard |
| 14 | Testes integração | Fluxo completo com mocks |
| 15 | Sem dados hardcoded | Sem CPF, email, telefone em código |
| 16 | Sem secrets em código | Todas credenciais via env vars |
| 17 | Logs sem PII | Verificado com PIIMaskingTest |
| 18 | FRIA documentada | Se agente toma decisões sobre candidatos (EU AI Act) |

**Arquivos a criar/configurar (V5):**
- Criar: `docker-compose.yml` (PostgreSQL 15 + Redis 7 + RabbitMQ 3)
- Criar: `.env.example` (todas vars obrigatórias documentadas)
- Criar: `alembic.ini` + `alembic/env.py` (suporte async SQLAlchemy)
- Criar: `src/core/config.py` (Settings com Pydantic BaseSettings, env vars validadas)
- Criar: `src/shared/agents/agent_scaffold.py` (`AgentScaffold.generate(domain="X")` → 4 arquivos)
- Verificar: `requirements.txt` inclui: `langchain-anthropic`, `langgraph`, `celery`, `aio-pika`, `pgvector`, `alembic`, `asyncpg`

**Acceptance Criteria:**
- [ ] `docker-compose up` sobe PostgreSQL + Redis + RabbitMQ sem erros
- [ ] `alembic upgrade head` roda sem erros
- [ ] `AgentScaffold.generate(domain="test")` cria 4 arquivos com estrutura correta
- [ ] `.env.example` documentado e revisado pelo tech lead
- [ ] Checklist 18 itens publicado internamente (Confluence / README)
- [ ] README de setup: passos 1–10 para subir o projeto do zero em máquina nova

**Riscos/Gotchas:**
- V5 pode ter estrutura de diretórios diferente — mapear e decidir migrar ou adaptar
- `agent_scaffold.py` gera templates — devs devem implementar o conteúdo real
- Env vars de integrações externas (Gupy, Pearch) podem não estar disponíveis no início — usar mocks

**Definition of Done:**
- [ ] Docker Compose funcional — todos serviços healthy (`docker-compose ps`)
- [ ] Checklist 18 itens revisado e aprovado pelo tech lead
- [ ] `AgentScaffold.generate()` testado gerando 4 arquivos corretos
- [ ] README atualizado com setup completo

---

### AGT-001 — MainOrchestrator (3-Tier CascadedRouter + HITL)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S0 | **Prioridade:** P0 | **Story Points:** 13
**Dependências:** AGT-002 (bloqueante — infra compartilhada primeiro)
**Seções de Referência:** 14.1, 13C.1, 13B.7, 13C.17 (roteiro orquestrador)

**Descrição:**
Orquestrador central que recebe mensagens do frontend via WebSocket, classifica a intenção com CascadedRouter (6 tiers) e roteia para o agente correto. Cobre os passos 5, 6 e 7 do fluxo Alpha 1. Sem ele, nenhum outro agente funciona.

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Adaptar | `src/domains/orchestrator.py` | `app/orchestrator/orchestrator.py` |
| Criar | `src/orchestrator/cascaded_router.py` | `app/orchestrator/cascaded_router.py` |
| Criar | `src/orchestrator/intent_router.py` | `app/orchestrator/intent_router.py` |
| Criar | `src/orchestrator/fast_router.py` | `app/orchestrator/fast_router.py` |
| Criar | `src/orchestrator/pending_action.py` | `app/orchestrator/pending_action.py` |
| Criar | `src/orchestrator/task_planner.py` | `app/orchestrator/task_planner.py` |
| Criar | `src/orchestrator/state_manager.py` | `app/orchestrator/state_manager.py` |
| Criar | `src/orchestrator/llm_cascade.py` | `app/orchestrator/llm_cascade.py` |
| Criar | `src/orchestrator/navigation_intent.py` | `app/orchestrator/navigation_intent.py` |

**Acceptance Criteria:**
- [ ] WebSocket `/ws/chat/{session_id}` roteia para agente correto por `domain` param
- [ ] CascadedRouter T4 (FastRouter regex) cobre pelo menos os intents Alpha 1 (wizard, sourcing, pipeline, wsi, communication)
- [ ] PendingActions suporta fluxos multi-turn (wizard e scheduling)
- [ ] Roteamento para todos os 9 agentes Alpha 1 funcionando
- [ ] HITL inline: quando agente emite `interrupt`, mensagem chega ao frontend como `type: hitl_request`
- [ ] Logs sem PII (PII Masking ativo)

**Requisitos de Compliance:**
- [ ] PolicyEngine carrega guardrails do DB antes de cada execução (`app/orchestrator/policy_engine.py`)
- [ ] `company_id` extraído do JWT e propagado para todos os agentes

**Testes obrigatórios:**
- Unit: testar CascadedRouter com intents Alpha 1 (wizard/sourcing/pipeline)
- Unit: testar PendingActions (criar, recuperar, resolver)
- Integration: WebSocket → Orchestrator → SourcingAgent → resposta
- Integration: HITL flow — interrupt → approve → resume

**Riscos / Gotchas:**
- V5 tem `DomainOrchestrator` com apenas 2 domínios — NÃO reusar diretamente
- `navigation_intent.py` foi adicionado no Sprint J com 4 grupos de intenção — verificar se V5 tem algo similar antes de criar do zero
- O `llm_cascade.py` implementa a lógica Haiku→Sonnet→Opus — começar com Sonnet diretamente se quiser simplificar no MVP

**Definition of Done:**
- [ ] 4-file pattern do orquestrador completo
- [ ] Todos os agentes Alpha 1 registrados no registry
- [ ] Testes unitários cobrindo os 6 tiers do router
- [ ] Compliance check 13B.9 (18 itens) passando

---

### AGT-002 — Infraestrutura Compartilhada (BaseAgent + Compliance + Prompts)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S0 | **Prioridade:** P0 | **Story Points:** 21
**Dependências:** nenhuma (é o pré-requisito de todos)
**Seções de Referência:** 13B, 13C.2, 13C.3, 13C.14, 13D

**Descrição:**
Setup da infraestrutura base que todos os agentes dependem: BaseAgent/EnhancedAgentMixin, provedores LLM, sistema de prompts, robustez/guardrails, compliance (FairnessGuard, PII Masking, AuditCallback, PromptInjectionGuard) e configuração base. Este card é o pré-requisito de TODOS os outros.

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Criar | `src/shared/agents/enhanced_agent_mixin.py` | `app/shared/agents/enhanced_agent_mixin.py` |
| Criar | `src/shared/agents/langgraph_react_base.py` | `app/shared/agents/langgraph_react_base.py` |
| Criar | `src/shared/providers/llm_factory.py` | `app/shared/providers/llm_factory.py` |
| Criar | `src/shared/providers/llm_claude.py` | `app/shared/providers/llm_claude.py` |
| Criar | `src/shared/compliance/fairness_guard.py` | `app/shared/compliance/fairness_guard.py` |
| Criar | `src/shared/compliance/audit_callback.py` | `app/shared/compliance/audit_callback.py` |
| Criar | `src/shared/compliance/audit_service.py` | `app/shared/compliance/audit_service.py` |
| Criar | `src/shared/pii_masking.py` | `app/shared/pii_masking.py` |
| Criar | `src/shared/prompt_injection.py` | `app/shared/prompt_injection.py` |
| Criar | `src/shared/prompts/loader.py` | `app/shared/prompts/loader.py` |
| Criar | `src/prompts/shared/lia_persona.yaml` | `app/prompts/shared/lia_persona.yaml` |
| Criar | `src/core/seeds/guardrails_seed.py` | `app/core/seeds/guardrails_seed.py` |
| Adaptar | `src/core/config.py` | `app/core/config.py` |
| Executar | Migrations 020, 032, 034, 035 | ver 0B.2 |
| Executar | `guardrails_seed.py` | ver 0B.3 |

**Acceptance Criteria:**
- [ ] `EnhancedAgentMixin.process()` funciona com 6 passos (ver 13B.7)
- [ ] FairnessGuard.check() detecta padrões discriminatórios (Camadas 1+2 ativas)
- [ ] PII Masking ativo nos loggers (CPF, email, tel mascarados nos logs)
- [ ] AuditCallback registra todas as execuções de agente no DB
- [ ] PromptInjectionGuard bloqueia tentativas de injection
- [ ] 13 guardrails do seed carregados no DB
- [ ] Providers LLM: Claude primário, OpenAI e Gemini como fallback funcionando

**Requisitos de Compliance:**
- [ ] 6 guardrails globais do seed ativos (seção 13D.5)
- [ ] Todos os loggers configurados com PII Masking (LGPD Art. 46)

**Testes obrigatórios:**
- Unit: FairnessGuard com 10+ casos discriminatórios conhecidos
- Unit: PII Masking — log com CPF/email/tel deve ser mascarado
- Unit: PromptInjectionGuard — casos de jailbreak comuns

**Riscos / Gotchas:**
- `EnhancedAgentMixin` depende de `WorkingMemoryService` e `LTMService` — criar stubs se não quiser implementar LTM no Sprint 0
- O provider Claude usa `langchain-anthropic` (não `anthropic` direto) — verificar dependência no `requirements.txt` do V5
- `guardrails_seed.py` depende de `AsyncSession` do SQLAlchemy — adaptar para o padrão de DB do V5

**Definition of Done:**
- [ ] Todos os 13 guardrails seedados e carregáveis via `GuardrailRepository`
- [ ] Testes de compliance (Fairness + PII + Injection) passando
- [ ] Nenhum dado pessoal visível nos logs

---

### AGT-003 — ATSIntegrationService (Premissa do Alpha 1)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S0 | **Prioridade:** P0 | **Story Points:** 8
**Dependências:** AGT-002
**Seções de Referência:** 14.8, 4.8

**Descrição:**
Serviço REST de integração bidirecional com ATS externo. É a **premissa** do Alpha 1: as vagas precisam ser importadas do ATS antes de tudo mais. O Alpha 1 usa como serviço REST simples (não agente ReAct). Cobre passos 2, 5 e 8.

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Adaptar | `src/domains/ats_integration/` | `app/domains/ats_integration/` |
| Criar | `src/services/ats_sync_service.py` | `app/services/ats_sync_service.py` |
| Reusar | `src/domains/sourced_profile_sourcing/` (API client) | `app/domains/ats_integration/agents/ats_integration_tool_registry.py` |

**Acceptance Criteria:**
- [ ] `GET /api/v1/ats/jobs` importa vagas do ATS externo (pelo menos Gupy)
- [ ] Vagas importadas salvas como `job_vacancies` no DB com `company_id`
- [ ] `POST /api/v1/ats/sync-status` exporta status/score do candidato de volta ao ATS
- [ ] Mapeamento de campos ATS ↔ WeDo funcional para Gupy (campo a campo)
- [ ] Tratamento de erro se ATS estiver indisponível (circuit breaker ou retry)

**Requisitos de Compliance:**
- [ ] `company_id` em todas as queries de vaga
- [ ] Audit log para cada sync bidirecional

**Testes obrigatórios:**
- Unit: mock do cliente ATS — importar vaga, verificar mapeamento de campos
- Integration: importar vaga do ATS → verificar persistência no DB

**Riscos / Gotchas:**
- V5 tem 67+ YAMLs de endpoints do ATS em `documentation/` — usar como referência de campo
- Começar com Gupy apenas; Pandapé e Merge ficam para pós-Alpha
- `SourcingAPIClient` do V5 é só leitura — adicionar write-back separadamente

**Definition of Done:**
- [ ] Importação de vagas funcionando com pelo menos 1 ATS real
- [ ] Sync de status/scores voltando para o ATS
- [ ] Testes com mock do ATS passando

---

### AGT-004 — SourcingReActAgent (Busca de Candidatos)
**Classificação:** `🟡 MVP SUPORTE` | **Sprint:** S1 | **Prioridade:** P0 | **Story Points:** 13
**Dependências:** AGT-002 (infra), AGT-003 (vagas importadas)
**Seções de Referência:** 14.3, 4.2, 13B.7, 13C.6, 13C.17 (roteiro sourcing)

**Descrição:**
Agente ReAct de busca de candidatos. Cobre passo 4 do fluxo Alpha 1. Usa 14 tools: busca semântica (PGVector), fulltext (ES/pg_trgm), WRF fusion, Pearch AI, Like/Dislike feedback loop. A LIA tem implementação completa como referência.

**14 Tools do SourcingReActAgent (todas registradas em `sourcing_tool_registry.py`):**

| # | Tool | Descrição |
|---|------|-----------|
| 1 | `extract_search_params` | SmartExtractor: NL query → estruturado (skills, localização, experiência) |
| 2 | `semantic_search` | Busca PGVector cosine similarity (embeddings 768d) |
| 3 | `fulltext_search` | Busca ES BM25 / pg_trgm (texto exato e fuzzy) |
| 4 | `wrf_fusion` | Weighted Rank Fusion: combina resultados ES + PGVector com pesos |
| 5 | `pearch_search` | Busca externa Pearch AI (190M+ perfis — quota: 10/dia/tenant) |
| 6 | `get_candidate_profile` | Perfil completo candidato (CV, scores, histórico, contatos) |
| 7 | `add_to_shortlist` | Adiciona candidato à shortlist (persiste com `company_id` + `job_id`) |
| 8 | `remove_from_shortlist` | Remove candidato da shortlist |
| 9 | `like_candidate` | Feedback positivo — ajusta ranking de candidatos similares |
| 10 | `dislike_candidate` | Feedback negativo — reduz recomendações de candidatos similares |
| 11 | `filter_by_location` | Filtro geográfico (cidade, estado, remoto/híbrido/presencial) |
| 12 | `filter_by_experience` | Filtro por anos de experiência mínima |
| 13 | `get_similar_candidates` | Candidatos similares ao perfil de um candidato de referência |
| 14 | `check_policy_compliance` | Valida query/resultado contra HiringPolicy do tenant |

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Adaptar | `src/domains/sourcing/sourcing_react_agent.py` | `app/domains/sourcing/agents/sourcing_react_agent.py` |
| Criar | `src/domains/sourcing/sourcing_system_prompt.py` | `app/domains/sourcing/agents/sourcing_system_prompt.py` |
| Criar | `src/domains/sourcing/sourcing_tool_registry.py` | `app/domains/sourcing/agents/sourcing_tool_registry.py` |
| Criar | `src/domains/sourcing/sourcing_stage_context.py` | `app/domains/sourcing/agents/sourcing_stage_context.py` |
| Criar | `src/domains/sourcing/services/wrf_service.py` | `app/domains/sourcing/services/wrf_service.py` |
| Adaptar | `src/services/rag_service.py` | `app/services/rag_pipeline_service.py` |
| Criar | `src/prompts/domains/sourcing.yaml` | `app/prompts/domains/sourcing.yaml` |

**Acceptance Criteria:**
- [ ] Padrão 4-file completo (react_agent + system_prompt + tool_registry + stage_context)
- [ ] SmartExtractor extrai skills/location/experience de queries em português
- [ ] Busca semântica PGVector funcionando com embeddings reais
- [ ] WRF fusion combinando resultados de ES + PGVector
- [ ] FairnessGuard wired — queries discriminatórias bloqueadas com explicação
- [ ] Tool `add_to_shortlist` persiste candidatos com `company_id` e `job_id`
- [ ] Sistema de prompt com 10 seções (ver 13B.2) + 2-3 few-shot examples
- [ ] Integração com MultiAgentOrchestrator do V5 (via Registry)

**Requisitos de Compliance:**
- [ ] FairnessGuard na validação de queries (seção 13D.1)
- [ ] Guardrail #10: não contatar candidatos recusados <6 meses
- [ ] PII Masking ativo nos logs do agente

**Testes obrigatórios:**
- Unit: SmartExtractor — extrair skills de 5 queries diferentes em PT-BR
- Unit: FairnessGuard — detectar query discriminatória ("candidato jovem")
- Integration: query NL → SmartExtractor → PGVector → WRF → lista candidatos
- Fairness: 10 queries discriminatórias devem ser bloqueadas

**Riscos / Gotchas:**
- V5 tem `MultiAgentOrchestrator` com 6 sub-agents — NÃO reusar essa arquitetura; substituir por ReAct único com 14 tools
- V5 já tem PGVector + RAG funcional (`rag_service.py` 391 linhas) — avaliar reuso antes de recriar
- `ParamExtractor` do V5 (492 linhas) pode ser mais detalhado que o LIA — comparar antes de decidir qual usar

**Definition of Done:**
- [ ] Checklist 13B.9 (18 itens) passando
- [ ] FairnessGuard wired e testado
- [ ] Pelo menos 5 testes unitários + 2 de integração

---

### AGT-005 — CommunicationService + Adapters (Email + WhatsApp + Teams)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S1 | **Prioridade:** P0 | **Story Points:** 13
**Dependências:** AGT-002
**Seções de Referência:** 14.7, 4.7, 13C.5, 13C.17 (roteiro comunicação)

**Descrição:**
Serviço multi-canal de comunicação. Cobre passos 5-9B do fluxo Alpha 1. Email é canal primário. WhatsApp é secundário. Teams para notificações ao consultor. A LIA tem 23 arquivos de comunicação como referência.

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Adaptar | `src/domains/communication/` | `app/domains/communication/agents/` + `services/` |
| Criar | `src/services/email_service.py` | `app/domains/communication/services/email_service.py` |
| Criar | `src/services/email_providers/resend_provider.py` | `app/domains/communication/services/email_providers/resend_provider.py` |
| Criar | `src/services/whatsapp_service.py` | `app/domains/communication/services/whatsapp_service.py` |
| Criar | `src/services/personalized_feedback_service.py` | `app/domains/cv_screening/services/personalized_feedback_service.py` |
| Criar | `src/services/communication_dispatcher.py` | `app/domains/communication/services/communication_dispatcher.py` |

**Acceptance Criteria:**
- [ ] Email transacional enviado via Resend (provider primário)
- [ ] Template de email com link para triagem WSI (chat web)
- [ ] Footer de IA obrigatório em emails gerados por IA (`AI_GENERATED_FOOTER`)
- [ ] Feedback personalizado por LLM para reprovados em Gate 1 e Gate 2 (diferenciados)
- [ ] WhatsApp adapter funcional (modo simulado para Alpha 1, real pós-Alpha)
- [ ] Notificação Teams ao consultor (alerta de candidato sem resposta)
- [ ] Histórico de comunicações persistido por candidato + `company_id`

**Requisitos de Compliance:**
- [ ] `ai_generated=True` → footer LGPD obrigatório em todos os emails
- [ ] Consentimento do candidato validado antes de envio (LGPD Art. 7)
- [ ] Guardrail #9: todo email deve incluir identificação de IA

**Testes obrigatórios:**
- Unit: template engine — variáveis substituídas corretamente
- Unit: feedback diferenciado — Gate 1 (construtivo) ≠ Gate 2 (final)
- Integration: envio real de email via Resend (sandbox)

**Riscos / Gotchas:**
- V5 tem apenas `email_service.py` básico — a maior parte precisa ser criada
- Feedback diferenciado por Gate (Gate1=construtivo vs Gate2=final) é funcionalidade nova — não existe em nenhum codebase
- Email tracking pixel (abertura/clique) é funcionalidade nova — não existe em nenhum codebase (ver AGT-010)

**Definition of Done:**
- [ ] Email end-to-end: gerar → enviar → histórico registrado
- [ ] Footer de IA presente em todos os emails gerados por IA
- [ ] Testes com mock do provider passando

---

### AGT-006 — JD Generator Service
**Classificação:** `🟡 MVP SUPORTE` | **Sprint:** S1 | **Prioridade:** P1 | **Story Points:** 5
**Dependências:** AGT-002, AGT-003
**Seções de Referência:** 14.2 (parte do Wizard), 4.9

**Descrição:**
Serviço LLM que gera/ajusta Job Description a partir dos dados importados do ATS. Não é agente autônomo — é uma tool do WizardAgent. Cobre passo 2 (editar vaga importada). FairnessGuard obrigatório no JD gerado.

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Criar | `src/services/jd_generator_service.py` | `app/services/jd_generator_service.py` |
| Criar | `src/services/jd_enrichment_service.py` | `app/services/jd_enrichment_service.py` |
| Criar | `src/services/jd_import_service.py` | `app/services/jd_import_service.py` |

**Acceptance Criteria:**
- [ ] `generate_enriched_jd(job_data)` gera JD em PT-BR a partir dos dados do ATS
- [ ] Modo "editar vaga importada" — ajustar JD existente, não criar do zero
- [ ] FairnessGuard wired — JD sem linguagem discriminatória
- [ ] Sugestões de salary benchmark opcionais (desejável no Alpha 1)

**Requisitos de Compliance:**
- [ ] FairnessGuard na geração de JD (seção 13D.1)

**Definition of Done:**
- [ ] JD gerada passa pelo FairnessGuard sem flags
- [ ] Teste unitário com JD discriminatória → bloqueio

---

### AGT-017 — HiringPolicyService (modo serviço — 4 tools)
**Classificação:** `🟡 MVP SUPORTE` | **Sprint:** S1 | **Prioridade:** P1 | **Story Points:** 5
**Dependências:** AGT-002
**Seções de Referência:** 14.10, 4.10, 13D.5

**Descrição:**
No Alpha 1, o HiringPolicy entra como **serviço** (4 tools), não como agente conversacional completo. Fornece políticas de contratação para os agentes de triagem e pipeline. O PolicySetupAgent (onboarding de 19 perguntas) é opcional no Alpha 1.

**ATENÇÃO — Path correto (pós Sprint I3c):**
`app/domains/policy/agents/` (NÃO `app/domains/hiring_policy/` — este diretório não existe mais)

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Criar | `src/domains/policy/agents/agent.py` | `app/domains/policy/agents/agent.py` |
| Criar | `src/domains/policy/agents/system_prompt.py` | `app/domains/policy/agents/system_prompt.py` |
| Criar | `src/domains/policy/agents/stage_context.py` | `app/domains/policy/agents/stage_context.py` |
| Criar | `src/services/hiring_policy_service.py` | Serviço que expõe as 4 tools como funções Python |

**4 tools disponíveis no modo serviço:**
1. `get_current_policy(company_id)` — retorna política atual do tenant
2. `save_policy_block(company_id, block_name, data)` — salva bloco de política
3. `apply_industry_defaults(company_id, industry)` — aplica defaults do setor
4. `validate_policy_compliance(text, company_id)` — valida texto contra a política

**Acceptance Criteria:**
- [ ] `get_current_policy()` retorna política do tenant (ou defaults se não configurada)
- [ ] `apply_industry_defaults()` popula política com valores razoáveis para o setor
- [ ] `validate_policy_compliance()` usa FairnessGuard + regras da política
- [ ] PolicyEngine do Orchestrator carrega políticas via `get_current_policy()`
- [ ] PolicySetupAgent (19 perguntas) como opcional — pode ser ativado pós-Alpha

**Riscos / Gotchas:**
- O PolicySetupAgent usa LLM direto (sem tools) com `EXTRACTION_PROMPT` + `REPLY_PROMPT` — padrão diferente do 4-file pattern
- `POLICY_TOOLS = []` — confirmar que o agente realmente não usa tools externas
- Guardrail #13: alterações de política requerem confirmação explícita do usuário

**Definition of Done:**
- [ ] 4 tools testadas unitariamente
- [ ] PolicyEngine do Orchestrator usando `get_current_policy()` em runtime

---

### AGT-007 — WSIInterviewGraph (Entrevista + Scoring)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S2 | **Prioridade:** P0 | **Story Points:** 21
**Dependências:** AGT-002, AGT-005 (para enviar link de triagem), AGT-009 (Chat Web)
**Seções de Referência:** 14.5, 4.4, 13B.10 (15 serviços WSI), 13C.17 (roteiro WSI)

**Descrição:**
LangGraph StateGraph que conduz a entrevista WSI completa. Cobre passos 3 (gerar perguntas), 7 (triagem), 7A (abandono) e 7B (feedback). É o componente mais complexo do Alpha 1. A LIA tem 18 serviços WSI (~9.621 linhas) como referência completa.

**7 Blocos WSI — Sequência de Execução:**

| Bloco | Nome | Conteúdo | Tipo de Scoring |
|-------|------|----------|----------------|
| 1 | Apresentação | Contexto empresa, vaga, próximos passos | Informativo (sem score) |
| 2 | Elegibilidade | Requisitos CLT, PCD, localização, disponibilidade | Eliminatório |
| 3 | Técnico básico | Hard skills essenciais da vaga | `0.6×Autodec` |
| 4 | Comportamental CBI | Perguntas situacionais (método STAR) | `0.6×Autodec + 0.4×Context` |
| 5 | Simulação / caso prático | Resolução de problema real do cargo | `0.6×Autodec + 0.4×Context + Bonus` |
| 6 | Fit cultural | Valores, estilo de trabalho, ambiente | `0.4×Context` |
| 7 | Encerramento | Perguntas candidato, próximos passos | Informativo (sem score) |

**Fórmula de scoring determinístico:** `Score = (0.6 × Autodeclarado) + (0.4 × Contextual) − Penalty + Bonus`

**15 Serviços WSI do LIA a copiar/adaptar (13B.10 — ~9.621 linhas total):**

| Serviço | Arquivo LIA | Responsabilidade |
|---------|------------|-----------------|
| WSI Screening Pipeline | `wsi_screening_pipeline.py` | Orquestrador geral — coordena todos os serviços |
| WSI Deterministic Scorer | `wsi_deterministic_scorer.py` | Fórmula scoring (558L — crítico, copiar direto) |
| WSI Question Generator | `wsi_question_generator.py` | Gera perguntas por bloco via LLM + calibração |
| WSI Feedback Generator | `wsi_feedback_generator.py` | Feedback personalizado pós-triagem |
| Calibration Profiles | `calibration_profiles.py` | Perfis calibração por cargo / nível / setor |
| Bloom Taxonomy Mapper | `bloom_taxonomy_mapper.py` | Mapeia perguntas a nível cognitivo Bloom |
| Dreyfus Level Assessor | `dreyfus_level_assessor.py` | Avalia nível Dreyfus (novato → especialista) |
| Big Five Analyzer | `big_five_analyzer.py` | Analisa traços Big Five nas respostas CBI |
| CBI Question Bank | `cbi_question_bank.py` | Banco 200+ perguntas CBI por categoria |
| WSI Session Manager | `wsi_session_manager.py` | Gestão de sessão multi-turno com PostgresSaver |
| WSI State Machine | `wsi_state_machine.py` | Máquina de estados: bloco atual, perguntas feitas |
| WSI Block Navigator | `wsi_block_navigator.py` | Navegação entre blocos (avançar, saltar elegibilidade) |
| WSI Response Validator | `wsi_response_validator.py` | Valida adequação da resposta (comprimento, relevância) |
| WSI Report Generator | `wsi_report_generator.py` | Relatório completo PDF + JSON por candidato |
| Personalized Feedback Service | `personalized_feedback_service.py` | Feedback diferenciado Gate 1 ≠ Gate 2 |

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Adaptar | `src/domains/cv_screening/wsi_interview_graph.py` | `app/domains/cv_screening/agents/wsi_interview_graph.py` |
| Criar | `src/domains/cv_screening/services/wsi_screening_pipeline.py` | `app/domains/cv_screening/services/wsi_screening_pipeline.py` |
| Criar | `src/domains/cv_screening/services/wsi_deterministic_scorer.py` | `app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| Criar | `src/domains/cv_screening/services/wsi_question_generator.py` | `app/domains/cv_screening/services/wsi_question_generator.py` |
| Criar | `src/domains/cv_screening/services/calibration_profiles.py` | `app/domains/cv_screening/services/calibration_profiles.py` |
| Criar | `src/domains/cv_screening/services/personalized_feedback_service.py` | `app/domains/cv_screening/services/personalized_feedback_service.py` |
| Adaptar | `src/domains/evaluation/graph.py` (4 nós existentes) | Estender para 9 nós da LIA |

**LangGraph — Estrutura do WSIInterviewGraph:**
```
State: WSIState { session_id, job_id, company_id, candidate_id, current_block,
                  questions[], answers[], scores{}, status }
Nós: load_context → generate_question → deliver_question →
     validate_response → score_response → advance_block →
     generate_feedback → END
Checkpointer: PostgresSaver (obrigatório para sessões multi-turno)
HITL: interrupt_before=["generate_feedback"]
```

**Acceptance Criteria:**
- [ ] Gera perguntas WSI a partir do JD (Blocos 2-5: empresa, elegibilidade, técnico, comportamental)
- [ ] Conduz entrevista conversacional via Chat Web (WebSocket)
- [ ] Scoring determinístico: `Score = (0.6×Autodec) + (0.4×Context) - Penalty + Bonus`
- [ ] Feedback personalizado pós-triagem com pontos fortes + oportunidades
- [ ] HITL: consultor aprova/revisa antes de enviar feedback ao candidato
- [ ] Timeout 48h: triagem abandonada → 2 lembretes → alerta consultor
- [ ] PostgresSaver: sessão persistida entre turnos (candidato pode retomar)
- [ ] FairnessGuard: nenhuma pergunta discriminatória (CLT 373-A)
- [ ] PromptInjectionGuard: respostas do candidato sanitizadas
- [ ] AuditCallback: cada resposta e score registrados

**Requisitos de Compliance:**
- [ ] FairnessGuard wired em `generate_question` e `validate_response`
- [ ] PromptInjectionGuard em `validate_response` (candidato controla input)
- [ ] Guardrail #4: sem perguntas sobre filhos/família/vida pessoal
- [ ] Guardrail #7: perguntas exclusivamente sobre competências profissionais
- [ ] AuditCallback em todos os nós de scoring
- [ ] Consentimento do candidato validado antes de iniciar WSI (LGPD Art. 7)

**Testes obrigatórios:**
- Unit: WSIDeterministicScorer com 10 respostas simuladas
- Unit: FairnessGuard — perguntas discriminatórias bloqueadas
- Unit: PromptInjectionGuard — tentativas de injection em respostas
- Integration: fluxo completo WSI (start → 5 perguntas → score → feedback)
- Fairness: auditoria Four-Fifths Rule antes do go-live (bias audit baseline)

**Riscos / Gotchas:**
- V5 tem `InterviewGraph` com 4 nós e scoring por rubrica simples — NÃO é o WSI. Usar como base estrutural mas reescrever os nós
- V5 usa Gemini como LLM — migrar para Claude (Sonnet) como primário
- O `wsi_deterministic_scorer.py` (558 linhas) é a peça mais crítica — copiar diretamente da LIA
- Timeout 48h + lembretes é funcionalidade nova (não existe em nenhum codebase) — implementar via AutomationScheduler (AGT-016)

**Definition of Done:**
- [ ] Fluxo WSI completo end-to-end testado
- [ ] FairnessGuard + PromptInjectionGuard + AuditCallback wired e testados
- [ ] Bias audit baseline rodado (seção 13D.2)
- [ ] FRIA documentado para screening WSI (EU AI Act)
- [ ] Checklist 13B.9 passando

---

### AGT-008 — CVScreeningReActAgent (Triagem Curricular)
**Classificação:** `🟡 MVP SUPORTE` | **Sprint:** S2 | **Prioridade:** P1 | **Story Points:** 8
**Dependências:** AGT-002, AGT-007 (WSI como serviço chamado pela tool `run_wsi_screening`)
**Seções de Referência:** 14.4, 4.3, 13C.7, 13B.7

**Descrição:**
Agente ReAct de triagem de CV. Análise documental (não conversacional). Scoring de matching CV × JD. Cobre passo 4. A LIA tem `PipelineReActAgent` como referência completa.

**8 Tools do CVScreeningReActAgent (todas registradas em `pipeline_tool_registry.py`):**

| # | Tool | Descrição |
|---|------|-----------|
| 1 | `parse_cv` | Extrai estrutura de CV (PDF/DOCX) — skills, experiência, formação, idiomas |
| 2 | `score_cv_match` | Score matching CV × JD (0–100) via LLM + regras determinísticas |
| 3 | `extract_skills` | Extrai habilidades técnicas e comportamentais do texto do CV |
| 4 | `check_experience` | Valida se candidato atende experiência mínima da vaga |
| 5 | `run_wsi_screening` | Dispara fluxo WSI completo (AGT-007) para candidato aprovado na triagem documental |
| 6 | `move_to_stage` | Move candidato para próximo estágio do pipeline (com HITL se configurado) |
| 7 | `add_screening_note` | Adiciona nota de triagem ao histórico do candidato (`company_id` obrigatório) |
| 8 | `get_job_requirements` | Recupera requisitos completos da vaga (JD + HiringPolicy do tenant) |

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Criar | `src/domains/cv_screening/pipeline_react_agent.py` | `app/domains/cv_screening/agents/pipeline_react_agent.py` |
| Criar | `src/domains/cv_screening/pipeline_tool_registry.py` | `app/domains/cv_screening/agents/pipeline_tool_registry.py` |
| Criar | `src/domains/cv_screening/services/cv_parser.py` | `app/domains/cv_screening/services/cv_parser.py` |
| Criar | `src/domains/cv_screening/services/cv_scoring_service.py` | `app/domains/cv_screening/services/cv_scoring_service.py` |
| Criar | `src/prompts/domains/cv_screening.yaml` | `app/prompts/domains/cv_screening.yaml` |

**Acceptance Criteria:**
- [ ] 4-file pattern completo
- [ ] `analyze_cv` extrai skills, experiência, formação do CV
- [ ] `score_candidate` gera score de matching CV × JD
- [ ] FairnessGuard wired antes de scoring
- [ ] `move_candidate` muda estágio no pipeline com HITL se necessário
- [ ] System prompt com `FAIRNESS_RULES` + `COMMUNICATION_TRANSPARENCY_RULES`

**Requisitos de Compliance:**
- [ ] FairnessGuard wired — scoring não pode usar atributos protegidos
- [ ] Audit trail para cada decisão de triagem

**Definition of Done:**
- [ ] Checklist 13B.9 passando
- [ ] FairnessGuard testado com candidatos de grupos minoritários

---

### AGT-009 — Chat Web Canal (Interface de Triagem para Candidato)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S2 | **Prioridade:** P0 | **Story Points:** 8
**Dependências:** AGT-007 (WSI Graph), AGT-002 (PromptInjectionGuard)
**Seções de Referência:** 5.3, 7 (serviços de suporte)

**Descrição:**
Canal de triagem primário do Alpha 1. O candidato recebe um link no email e acessa uma interface web de chat para fazer a triagem WSI. A LIA tem `agent_chat_ws.py` (WebSocket) como base.

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Criar | `src/api/ws/candidate_chat.py` | `app/api/v1/agent_chat_ws.py` |
| Criar | `src/api/routes/candidate_session.py` | Link único por candidato/vaga |

**Acceptance Criteria:**
- [ ] Link único por candidato+vaga (formato: `/triagem/{token}`)
- [ ] WebSocket estável para conversas de 10-30 minutos
- [ ] PromptInjectionGuard ativo antes de cada mensagem do candidato
- [ ] Sessão persistida via PostgresSaver (candidato pode retomar)
- [ ] Mensagem de boas-vindas + explicação do processo antes de iniciar
- [ ] Timeout: sessão expira após 48h sem atividade

**Requisitos de Compliance:**
- [ ] Banner de consentimento antes de iniciar a triagem (LGPD Art. 7)
- [ ] Identificação de IA na interface ("Você está interagindo com uma IA")

**Definition of Done:**
- [ ] Candidato consegue completar triagem WSI do início ao fim via Chat Web
- [ ] PromptInjectionGuard testado com tentativas reais de injection

---

### AGT-010 — Follow-up 7 dias + Email Tracking
**Classificação:** `🟡 MVP SUPORTE` | **Sprint:** S2 | **Prioridade:** P1 | **Story Points:** 8
**Dependências:** AGT-005, AGT-016 (EventRetryOrchestrator)
**Seções de Referência:** 7 (serviços de suporte), 5.3

**Descrição:**
Funcionalidade nova (não existe em nenhum codebase). Candidatos que não responderam ao email de triagem recebem re-envios a cada 24h por 7 dias. Email tracking detecta abertura/clique.

**Arquivos a criar (V5 e LIA — novo em ambos):**

| Ação | Arquivo | Descrição |
|------|---------|-----------|
| Criar | `src/services/followup_scheduler.py` | Regra de follow-up: re-envio a cada 24h × 7 dias |
| Criar | `src/services/email_tracking_service.py` | Pixel de abertura + redirect de clique |
| Criar | `src/api/routes/email_events.py` | Webhook: GET `/track/open/{token}`, GET `/track/click/{token}` |

**Acceptance Criteria:**
- [ ] Email inicial enviado após Gate 1 (aprovação do consultor)
- [ ] Se não aberto em 24h: re-envio automático (máximo 7 re-envios)
- [ ] Se candidato abre/clica: parar follow-up automático
- [ ] Pixel de rastreamento 1×1 GIF no email detecta abertura
- [ ] Link de triagem é redirect que registra clique antes de redirecionar
- [ ] Notificação ao consultor após 7 dias sem resposta

**Riscos / Gotchas:**
- Email tracking (pixel) é funcionalidade nova — sem referência no LIA
- Alguns clientes de email bloqueiam pixels — a ausência de abertura não significa que não foi lido
- Follow-up agressivo pode violar LGPD — limitar re-envios e sempre incluir opt-out

**Definition of Done:**
- [ ] Follow-up automático funcionando com 3+ cenários testados
- [ ] Pixel de rastreamento registrando aberturas

---

### AGT-015 — PipelineGateService (Gate 1 / Gate 2)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S1 | **Prioridade:** P0 | **Story Points:** 8
**Dependências:** AGT-002, AGT-003
**Seções de Referência:** 14.9, 4.9, 6 (arquitetura recomendada)

**Descrição:**
Serviço que gerencia o estado dos Gates (1 e 2), as regras de transição de pipeline e a integração HITL. Cobre passos 5 e 8. O `PipelineTransitionAgent` da LIA é a referência (20 tools + HITL).

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Adaptar | `src/domains/pipeline/pipeline_transition_agent.py` | `app/domains/pipeline/agents/pipeline_transition_agent.py` |
| Criar | `src/services/pipeline_gate_service.py` | Lógica de Gate 1/Gate 2 |
| Criar | `src/services/stage_automation_engine.py` | `app/domains/automation/services/stage_automation_engine.py` |

**Acceptance Criteria:**
- [ ] Gate 1: consultor aprova/rejeita candidatos via interface HITL
- [ ] Gate 2: consultor decide finalistas com score WSI visível
- [ ] Reprovados Gate 1: trigger para envio de feedback (via AGT-005)
- [ ] Aprovados Gate 1: trigger para envio de link de triagem WSI (via AGT-005)
- [ ] Candidatos inscritos via web: `source=web_inscription` bypassa Gate 1 → triagem automática
- [ ] Sync de status para ATS após cada Gate (via AGT-003)
- [ ] Audit trail para cada decisão de Gate (compliance)

**Requisitos de Compliance:**
- [ ] Guardrail #5: nunca rejeitar em massa sem gate humano
- [ ] Guardrail #11: gate humano obrigatório antes de rejeição em massa
- [ ] AuditCallback em cada transição de Gate
- [ ] Consentimento validado antes de Gate 1 (LGPD)

**Definition of Done:**
- [ ] Gate 1 e Gate 2 funcionando end-to-end
- [ ] Bypass de inscrição web implementado

---

### AGT-016 — EventRetryOrchestrator (Scheduler + DLQ)
**Classificação:** `🟡 MVP SUPORTE` | **Sprint:** S2 | **Prioridade:** P1 | **Story Points:** 8
**Dependências:** AGT-002
**Seções de Referência:** 14.14 (Automation Agent infra), 7 (serviços de suporte)

**Descrição:**
Infraestrutura de automação que roda em background: 10 jobs agendados + 8 triggers de evento + Dead Letter Queue. O Automation Agent conversacional não entra no Alpha 1, mas esta infra precisa rodar. Cobre passos 6B (follow-up) e 7A (triagem abandonada).

**Arquivos a criar/modificar (V5):**

| Ação | Arquivo V5 | Referência LIA |
|------|-----------|----------------|
| Criar | `src/services/automation_scheduler.py` | `app/domains/automation/services/automation_scheduler.py` |
| Criar | `src/services/stage_automation_engine.py` | `app/domains/automation/services/stage_automation_engine.py` |
| Criar | `src/services/planned_task_service.py` | `app/services/planned_task_service.py` |

**Jobs prioritários para Alpha 1:**
- `follow_up_7d` — re-envio email a cada 24h × 7 dias (novo)
- `triagem_timeout_48h` — timeout de triagem + 2 lembretes + alerta consultor (novo)
- `check_interview_no_shows` — a cada 30min
- `send_interview_reminders` — a cada 15min
- `run_lgpd_cleanup` — diário 02:00

**Definition of Done:**
- [ ] Scheduler rodando via Celery Beat
- [ ] Follow-up 7d e timeout triagem 48h configurados
- [ ] DLQ para eventos que falharam

---

### AGT-011 — Gate HITL Wiring (Aprovação via Chat)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S3 | **Prioridade:** P0 | **Story Points:** 8
**Dependências:** AGT-015 (PipelineGate), AGT-FE-002 (HITLConfirmCard UI)
**Seções de Referência:** 13C.8, CLAUDE.md (Sprint J), 13B.9

**Descrição:** Wiring completo do fluxo HITL: agente emite `interrupt` via LangGraph → frontend recebe `{"type": "hitl_request"}` → consultor vê HITLConfirmCard no chat → aprova ou rejeita → agente resume do ponto de interrupção. Já existe implementação de referência na LIA (Sprint J). Inclui persistência Redis (fast-path) + PostgreSQL (source of truth) nas tabelas `hitl_pending_actions` e `hitl_audit_trail`.

**Arquivos a criar/modificar (V5):**
- Criar: `src/services/hitl_service.py` — `store_resume_info()`, `get_resume_info()`, `request_approval()`, `receive_approval()`
- Criar: `src/api/routes/hitl.py` — `POST /api/v1/hitl/{thread_id}/approve`
- Adaptar: `src/api/ws/agent_chat_ws.py` — 3 casos de resume: WSI (`ainvoke None`), Wizard (`ainvoke None`), genérico (`agent.process`)
- Executar: Migration `alembic/versions/032_add_hitl_tables.py`

**Tabelas HITL (migration 032):**
- `hitl_pending_actions`: `(id, company_id, thread_id, domain, action, description, data JSON, agent_input JSON, status, ws_session_id, created_at, expires_at, resolved_at, resolved_by, comment)`
- `hitl_audit_trail`: `(id, company_id, thread_id, pending_id, action, approved, comment, resolved_by, resolved_at)`

**Acceptance Criteria:**
- [ ] Agente emite `interrupt` LangGraph → WebSocket envia `{"type": "hitl_request", "action": "...", "description": "..."}` ao frontend
- [ ] `HITLService.request_approval()` persiste no Redis (TTL 24h) + PostgreSQL simultaneamente
- [ ] `POST /api/v1/hitl/{thread_id}/approve` com `{approved: true/false, comment}` resolve e retorna ao agente
- [ ] Agente resume do checkpoint via `ainvoke(None)` com estado preservado (PostgresSaver obrigatório)
- [ ] `domain` e `company_id` registrados em todos os records HITL (multi-tenant)
- [ ] HITL expirado (>24h) retorna erro gracioso ao recrutador
- [ ] Audit trail completo: quem aprovou, quando, comentário

**Requisitos de Compliance:**
- [ ] `company_id` + `domain` obrigatórios em `hitl_pending_actions` (multi-tenant)
- [ ] Audit trail imutável em `hitl_audit_trail` (SOX compliance)
- [ ] Ações HITL registradas via `AuditCallback`

**Testes obrigatórios:**
- Unit: `HITLService` — store/retrieve Redis, store/retrieve PostgreSQL, expiração TTL
- Unit: `receive_approval()` — aprovação e rejeição com comment
- Integration: fluxo completo interrupt → approve → resume (mock WebSocket)
- Integration: expiração — aprovação após 24h retorna erro gracioso

**Riscos/Gotchas:**
- PostgresSaver obrigatório para resume funcionar — MemorySaver não suporta cross-request
- Redis TTL e PostgreSQL devem ser sincronizados — Redis é fast-path, DB é source of truth
- Risco de race condition: aprovação chega antes de interrupt ser registrado — retry com backoff
- V5 provavelmente não tem tabelas HITL — rodar migration antes de testar

**Definition of Done:**
- [ ] Fluxo completo: interrupt → HITLConfirmCard → approve/reject → resume agente funcionando end-to-end
- [ ] `company_id` e `domain` em todos registros HITL
- [ ] Testes unitários HITLService passando
- [ ] Migration 032 executada com sucesso

---

### AGT-012 — SchedulingGraph (Agendamento de Entrevista)
**Classificação:** `🔵 PÓS-MVP (Alpha 1.1)` | **Sprint:** S3 | **Prioridade:** P1 | **Story Points:** 13
**Dependências:** AGT-002, AGT-005 (Communication — enviar convites)
**Seções de Referência:** 14.6, 4.6

**Descrição:** LangGraph StateGraph de 6 nós que automatiza o agendamento de entrevista pós-Gate 2. Integra com Microsoft Graph (Outlook Calendar) para verificar disponibilidade e criar evento. Gera link de videoconferência (Teams como padrão Alpha 1). Envia convites ao candidato e entrevistador. NÃO existe no V5 — implementar do zero usando LIA como referência.

**Arquivos a criar (zero no V5, copiar/adaptar do LIA):**
- Criar: `src/domains/scheduling/interview_graph.py` — StateGraph 6 nós + PostgresSaver
- Criar: `src/domains/scheduling/interview_scheduling_nodes.py` — funções de cada nó
- Criar: `src/services/calendar_service.py` — MS Graph calendar API wrapper (MSAL auth)
- Criar: `src/services/zero_touch_scheduling_service.py` — orquestrador agendamento automático
- Criar: `src/prompts/domains/scheduling.yaml` — prompts agendamento em PT-BR

**LangGraph — Estrutura SchedulingGraph:**
```
State: SchedulingState { session_id, job_id, company_id, candidate_id,
                          interviewer_id, proposed_slots[], confirmed_slot,
                          meeting_link, status }
Nós: get_interviewer_slots → propose_times → confirm_slot →
     create_calendar_event → send_invitations → END
Integração: Microsoft Graph SDK (calendário) + Bot Builder (Teams link)
Checkpointer: PostgresSaver (candidato pode confirmar slot depois)
```

**Acceptance Criteria:**
- [ ] Consultar disponibilidade do entrevistador via MS Graph Calendar
- [ ] Propor 3 slots ao candidato via chat/email
- [ ] Candidato confirma slot preferido (resposta email/chat)
- [ ] Criar evento no Calendar com detalhes vaga + candidato
- [ ] Gerar link videoconferência Teams (padrão Alpha 1)
- [ ] Enviar convite calendar ao candidato + entrevistador + CC recrutador
- [ ] Fallback: se MS Graph indisponível, proposta de slots manual

**Requisitos de Compliance:**
- [ ] Dados de disponibilidade não armazenados após agendamento (LGPD minimização)
- [ ] `company_id` em todos registros de agendamento
- [ ] Consentimento candidato para compartilhamento de dados com entrevistador

**Testes obrigatórios:**
- Unit: mock MS Graph — propor slots, criar evento
- Unit: timezone handling (Brasília vs UTC)
- Integration: fluxo completo Gate 2 aprovado → agendar → convites enviados (mocks)
- Mock: MS Graph indisponível → fallback funciona sem quebrar

**Riscos/Gotchas:**
- MS Graph auth (MSAL) requer configuração Azure AD — verificar credentials V5
- Timezone: candidatos em fusos diferentes — sempre armazenar UTC, exibir local
- Candidatos sem resposta de slot — timeout 48h + notificação consultor (usar AGT-016)
- V5 pode ter `calendar_service.py` básico — avaliar reuso vs reescrever

**Definition of Done:**
- [ ] Agendamento end-to-end: Gate 2 aprovado → proposta slots → confirmação → evento criado → convites enviados
- [ ] Mock MS Graph passando nos testes
- [ ] Timezone testado (Brasília, São Paulo, Manaus)

---

### AGT-013 — Triagem Abandonada Monitor (Timeout 48h)
**Classificação:** `🔵 PÓS-MVP (Alpha 1.1)` | **Sprint:** S3 | **Prioridade:** P1 | **Story Points:** 5
**Dependências:** AGT-016 (EventRetryOrchestrator — Celery scheduler), AGT-005 (Communication)
**Seções de Referência:** 5.3, 7, 14.14

**Descrição:** Monitor periódico (Celery Beat) que detecta triagens WSI iniciadas mas não concluídas após 48h. Envia 2 lembretes ao candidato + alerta ao consultor via Teams se ainda abandonada. Candidato pode retomar a qualquer momento (PostgresSaver preserva estado). Funcionalidade nova — não existe em V5 nem LIA como componente isolado.

**Arquivos a criar (V5):**
- Criar: `src/jobs/triagem_timeout_job.py` — job Celery: detecta sessions com `status=in_progress` e `last_activity_at < now - 48h`
- Criar: `src/services/abandonment_monitor_service.py` — lógica: 1º lembrete (48h) → 2º lembrete (+24h) → alerta consultor (+24h) → marcar `abandoned`
- Adaptar: `src/core/celery_tasks.py` — registrar task `triagem.timeout_check` no beat schedule (a cada hora)

**Acceptance Criteria:**
- [ ] Job Celery roda a cada hora via Beat schedule (idempotente)
- [ ] 48h sem atividade → 1º lembrete email/WhatsApp ao candidato: "Sua triagem ainda está disponível"
- [ ] +24h sem resposta → 2º lembrete com senso de urgência
- [ ] +24h sem resposta → alerta Teams ao consultor: "Candidato X abandonou triagem de Vaga Y" + link direto
- [ ] Candidato acessa link e retoma triagem normalmente (PostgresSaver preserva estado)
- [ ] Status `abandoned` após 3 tentativas — não enviar mais alertas
- [ ] `company_id` em todos registros de abandono

**Requisitos de Compliance:**
- [ ] Máximo 3 contatos (2 lembretes + 1 final) — não spam (LGPD Art. 7)
- [ ] Opt-out: candidato pode recusar continuar (link "Não tenho interesse")
- [ ] Audit log de cada tentativa de contato

**Testes obrigatórios:**
- Unit: `AbandonmentMonitorService` — cenários 48h, 72h, 96h, status=abandoned
- Unit: não re-alertar candidato já marcado `abandoned`
- Integration: mock Celery Beat → job roda → lembrete enviado (mock Communication)

**Riscos/Gotchas:**
- PostgresSaver deve estar configurado para retomada funcionar (depende AGT-011)
- Job deve ser idempotente — rodar 2x não envia 2 emails
- Timezone: "48h" em fuso do candidato vs UTC do servidor

**Definition of Done:**
- [ ] Job Celery registrado e rodando no Beat schedule
- [ ] Fluxo 48h → lembrete → 72h → lembrete → 96h → abandono testado
- [ ] Opt-out implementado e testado

---

### AGT-014 — Teams/Slack Notifications (Alertas ao Consultor)
**Classificação:** `🔵 PÓS-MVP (Alpha 1.1)` | **Sprint:** S3 | **Prioridade:** P2 | **Story Points:** 3
**Dependências:** AGT-005 (CommunicationService — Teams adapter já implementado)
**Seções de Referência:** 5.3

**Descrição:** Notificações proativas ao consultor via Microsoft Teams quando candidato não responde (passo 6B), triagem abandonada (passo 7A) ou candidato sem horário disponível (passo 9A). Reutiliza o Teams adapter do AGT-005. Mensagens Adaptive Cards com link direto ao candidato/vaga na plataforma.

**Arquivos a criar/modificar (V5):**
- Criar: `src/services/teams_notification_service.py` — formatação e envio de Adaptive Cards Teams
- Adaptar: `src/services/communication_dispatcher.py` — adicionar rota `TEAMS_ALERT` (AGT-005 já tem Teams adapter)
- Criar: `src/templates/teams/` — templates Adaptive Cards para cada tipo de alerta

**Tipos de alerta Teams (Alpha 1):**

| Tipo | Trigger | Mensagem exemplo |
|------|---------|-----------------|
| `CANDIDATE_NO_RESPONSE` | 24h sem abrir email | "João Silva não abriu o convite de triagem para Dev Senior" |
| `SCREENING_ABANDONED` | 48h sem completar triagem | "Maria Costa abandonou a triagem de UX Designer (48h)" |
| `SCHEDULING_NO_AVAILABILITY` | Candidato sem slots | "Carlos Souza não confirmou horário para Dev Senior" |

**Acceptance Criteria:**
- [ ] Adaptive Card enviado com nome candidato + nome vaga + link direto à plataforma
- [ ] 3 tipos de alerta funcionando: no-response, abandoned, no-availability
- [ ] Card Teams inclui botões de ação: "Ver Candidato", "Enviar Email"
- [ ] `company_id` no routing — Teams correto por tenant
- [ ] Fallback: se Teams indisponível → envia email ao consultor

**Testes obrigatórios:**
- Unit: `TeamsNotificationService` — cada tipo gera payload Adaptive Card correto
- Integration: mock Teams API — envio bem-sucedido + erro → fallback email

**Definition of Done:**
- [ ] 3 tipos de alerta funcionando end-to-end
- [ ] Fallback para email se Teams indisponível
- [ ] Mock Teams API passando nos testes

---

### AGT-FE-001 — Chat Web UI (Interface do Candidato para Triagem)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S2 | **Prioridade:** P0 | **Story Points:** 8
**Dependências:** AGT-009 (WebSocket backend), AGT-007 (WSI Graph)
**Seções de Referência:** Design System v4.2.1, 13F (AI vs Non-AI — UI deve identificar IA)

**Descrição:** Interface web acessada pelo candidato via link único enviado por email. Conduz a triagem WSI de forma conversacional. Design simples, mobile-first, sem necessidade de login. Banner de consentimento LGPD obrigatório antes de iniciar. Identificação clara de IA em destaque.

**Arquivos a criar (V5):**
- Criar: `src/app/triagem/[token]/page.tsx` — página principal SSR, valida token único
- Criar: `src/components/chat/CandidateChat.tsx` — interface chat com streaming token a token
- Criar: `src/components/chat/ConsentBanner.tsx` — banner LGPD (checkbox aceite obrigatório)
- Criar: `src/components/chat/ProgressIndicator.tsx` — "Bloco 2/5 • Pergunta 3/6"
- Criar: `src/hooks/use-candidate-chat.ts` — WebSocket hook com reconnect automático
- Criar: `src/lib/session-token.ts` — validação e decode do token único

**Acceptance Criteria:**
- [ ] Página carrega em <2s via link único `/triagem/{token}` — sem login
- [ ] Banner consentimento LGPD exibido antes de qualquer pergunta — checkbox obrigatório; sem aceite não avança
- [ ] Identificação IA visível: "Você está interagindo com a LIA, assistente de IA da WeDOTalent"
- [ ] Streaming token a token (UX suave — evitar telas em branco)
- [ ] Indicador de progresso em tempo real: "Bloco 2/5 • Pergunta 3/6"
- [ ] Design mobile-first: funciona em smartphone 375px sem scroll horizontal
- [ ] Token inválido/expirado: página amigável de erro (não 404 genérico)
- [ ] Sessão cai: reconecta automaticamente e retoma do ponto salvo (PostgresSaver)

**Requisitos de Compliance:**
- [ ] Banner LGPD obrigatório antes de qualquer dado ser coletado (Art. 7 LGPD)
- [ ] Identificação clara de IA em destaque (EU AI Act, LGPD)
- [ ] Token único — candidato não pode acessar triagem de outro
- [ ] Sem analytics de terceiros na página de triagem (minimização LGPD)

**Testes obrigatórios:**
- E2E Playwright: fluxo completo — abrir link → banner consent → triagem → completion
- Unit: `use-candidate-chat.ts` — WebSocket connect, receive message, reconnect
- Unit: token inválido → redirect para página de erro amigável
- Acessibilidade: contraste WCAG AA, navegação teclado funcional

**Riscos/Gotchas:**
- WebSocket em mobile pode cair — reconnect automático crítico (exponential backoff)
- Token expira após 7 dias — candidato que demora recebe link expirado (mensagem clara)
- Streaming pode ter latência alta — indicador "IA digitando..." durante geração
- Manter UI simples (peso baixo) — evitar shadcn/ui components pesados

**Definition of Done:**
- [ ] Candidato completa triagem WSI do início ao fim via mobile
- [ ] Banner LGPD testado (sem aceite → não avança — testado E2E)
- [ ] Playwright E2E passando
- [ ] Lighthouse: Performance >80, Accessibility >90

---

### AGT-FE-002 — HITLConfirmCard (Aprovação do Consultor)
**Classificação:** `🟢 MVP CRÍTICO` | **Sprint:** S2 | **Prioridade:** P0 | **Story Points:** 5
**Dependências:** AGT-011 (HITL Wiring backend), AGT-001 (WebSocket Orchestrator)
**Seções de Referência:** 13C.8, CLAUDE.md (Sprint J)

**Descrição:** Componente React que aparece no chat do consultor quando um agente precisa de aprovação humana (HITL). Exibe ação pendente, contexto resumido e botões Aprovar/Rejeitar. Já existe implementação de referência na LIA (Sprint J — `HITLConfirmCard.tsx`) — adaptar para V5.

**Arquivos a criar/adaptar (V5):**
- Adaptar: `src/components/HITLConfirmCard.tsx` — ref: `plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx`
- Adaptar: `src/hooks/use-hitl-streaming.ts` — ref: `plataforma-lia/src/hooks/use-float-streaming.ts`
- Criar: `src/components/HITLConfirmCard.stories.tsx` — Storybook stories para os 5 estados

**Acceptance Criteria:**
- [ ] Card aparece no chat quando WebSocket recebe `{"type": "hitl_request"}`
- [ ] Exibe: título da ação, descrição legível ("Aprovar envio de email para 47 candidatos"), contexto resumido
- [ ] Botão "Aprovar" (estilo primário) envia `{approved: true}` ao backend
- [ ] Botão "Rejeitar" abre campo de texto para comentário → envia `{approved: false, comment: "..."}`
- [ ] Estado loading durante envio: botões desabilitados + spinner
- [ ] Card desaparece após resolução; mensagem de confirmação inline no chat
- [ ] Múltiplos HITL pendentes: stack de cards em ordem cronológica
- [ ] Card expirado (>24h): badge "Expirado" sem botões de ação

**Testes obrigatórios:**
- Unit: render — card exibe descrição + botões corretamente
- Unit: aprovar → `use-hitl-streaming` envia payload `{approved: true}`
- Unit: rejeitar com comentário → payload `{approved: false, comment: "..."}`
- Unit: estado loading — botões desabilitados durante envio
- Unit: card expirado — sem botões, badge "Expirado"

**Definition of Done:**
- [ ] Card funcional com approve/reject testados manualmente + integração AGT-011
- [ ] 5 estados implementados: pending, loading, approved, rejected, expired
- [ ] Unit tests passando
- [ ] Storybook stories para cada estado

---

### AGT-FE-003 — Pipeline Status UI (Visão do Consultor)
**Classificação:** `🔵 PÓS-MVP (Alpha 1.1)` | **Sprint:** S3 | **Prioridade:** P1 | **Story Points:** 5
**Dependências:** AGT-015 (PipelineGateService), AGT-007 (WSI scores via API)
**Seções de Referência:** Design System v4.2.1

**Descrição:** Dashboard para o consultor monitorar o pipeline de candidatos por vaga: estágio atual, scores WSI, ações pendentes (Gates 1 e 2). Permite aprovar/rejeitar Gate 1 e Gate 2 diretamente pela UI (complementar ao chat HITL). Atualização automática de status.

**Arquivos a criar (V5):**
- Criar: `src/app/pipeline/[jobId]/page.tsx` — página dashboard pipeline por vaga
- Criar: `src/components/pipeline/PipelineStatusBoard.tsx` — colunas por estágio
- Criar: `src/components/pipeline/CandidateStageCard.tsx` — card candidato: score + ações
- Criar: `src/hooks/use-pipeline-status.ts` — polling 30s ou WebSocket para status real-time

**Acceptance Criteria:**
- [ ] Lista candidatos agrupados por estágio: Inscritos | Em Triagem | Aguardando Gate 1 | Aprovados Gate 1 | Triagem Concluída | Aguardando Gate 2 | Finalistas
- [ ] Score WSI (0–100) visível para candidatos com triagem concluída
- [ ] Ações por candidato: [Aprovar Gate 1] [Rejeitar Gate 1] nos estágios corretos
- [ ] Filtros básicos: por vaga (URL param `[jobId]`), por status (dropdown)
- [ ] Atualização automática a cada 30s (polling) ou WebSocket se disponível
- [ ] Responsivo: funciona em desktop 1280px+ (uso by recruiter)

**Testes obrigatórios:**
- Unit: `use-pipeline-status` — fetch, parse resposta API, polling interval
- Unit: `PipelineStatusBoard` — renderiza candidatos nos estágios corretos
- E2E: consultor acessa pipeline → vê candidatos → aprova Gate 1 → candidato muda de estágio

**Definition of Done:**
- [ ] Dashboard funcional com dados reais da API
- [ ] Gate 1 e Gate 2 podem ser resolvidos pela UI (além do chat HITL)
- [ ] Testes unitários passando

---

## 19. MAPA DE DEPENDÊNCIAS ENTRE CARDS

### Grafo de Bloqueios (quem bloqueia quem)

```
AGT-002 (Infra)
  ├── bloqueia AGT-001 (Orchestrator)
  ├── bloqueia AGT-003 (ATS)
  ├── bloqueia AGT-004 (Sourcing)
  ├── bloqueia AGT-005 (Communication)
  ├── bloqueia AGT-006 (JD Generator)
  ├── bloqueia AGT-017 (Policy Service)
  ├── bloqueia AGT-015 (Pipeline Gate)
  ├── bloqueia AGT-016 (Scheduler)
  └── bloqueia AGT-009 (Chat Web)

AGT-003 (ATS)
  └── bloqueia AGT-004 (Sourcing — precisa de vagas importadas)
  └── bloqueia AGT-006 (JD Generator — precisa de dados da vaga)

AGT-005 (Communication)
  ├── bloqueia AGT-010 (Follow-up 7d)
  └── bloqueia AGT-013 (Abandono 48h)

AGT-007 (WSI Graph)
  └── bloqueia AGT-008 (CV Screening usa WSI como tool)

AGT-009 (Chat Web backend)
  └── bloqueia AGT-FE-001 (Chat Web UI)

AGT-011 (HITL Wiring)
  └── bloqueia AGT-FE-002 (HITL Card)

AGT-015 (Pipeline Gate)
  └── bloqueia AGT-011 (HITL Wiring — Gate usa HITL)
  └── bloqueia AGT-FE-003 (Pipeline UI)

AGT-016 (Scheduler)
  ├── bloqueia AGT-010 (Follow-up — usa scheduler)
  └── bloqueia AGT-013 (Abandono — usa scheduler)
```

### Cards que podem rodar em PARALELO (sem dependências entre si)

| Sprint | Cards Paralelos |
|--------|----------------|
| S0 | AGT-002 (sempre primeiro) |
| S0→S1 | AGT-001, AGT-003 em paralelo (ambos dependem só de AGT-002) |
| S1 | AGT-004, AGT-005, AGT-006, AGT-017, AGT-015, AGT-016 em paralelo (dependem de AGT-002) |
| S2 | AGT-007, AGT-008, AGT-009, AGT-010 em paralelo (AGT-007 e AGT-008 independentes) |
| S2 FE | AGT-FE-001 (após AGT-009) em paralelo com backend S2 |
| S3 | AGT-011, AGT-012, AGT-013, AGT-014 em paralelo (AGT-011 depende de AGT-015) |
| S3 FE | AGT-FE-002 (após AGT-011), AGT-FE-003 (após AGT-015) |

### Critical Path (caminho mais longo)

```
AGT-002 → AGT-015 → AGT-011 → AGT-FE-002
               ↑
AGT-003 → AGT-007 → AGT-009 → AGT-FE-001
```

---

## 20. NON-FUNCTIONAL REQUIREMENTS (NFRs) POR COMPONENTE

### Latência

| Componente | P50 | P95 | Limite Máximo | Notas |
|-----------|:---:|:---:|:-------------:|-------|
| WebSocket handshake | <100ms | <300ms | 1s | Crítico para UX do candidato |
| WSI — resposta por turno | <2s | <4s | 8s | Inclui LLM + scoring |
| Sourcing — query inicial | <1s | <3s | 5s | Com cache: <500ms |
| Sourcing — WRF fusion | <500ms | <1s | 2s | ES + PGVector + WRF |
| Email send | <2s | <5s | 10s | Async — não bloquear resposta |
| Gate HITL — approve | <500ms | <1s | 2s | Operação crítica de aprovação |
| ATS sync (write-back) | <3s | <8s | 30s | Pode ser async |
| CV parsing | <3s | <8s | 15s | Upload de arquivo |

### Disponibilidade e Resiliência

| Componente | Uptime Alvo | Fallback | Circuit Breaker |
|-----------|:-----------:|---------|:---------------:|
| Claude (LLM primário) | 99,5% | → OpenAI → Gemini | ✅ Obrigatório |
| PostgreSQL | 99,9% | Neon auto-failover | ✅ |
| Redis | 99,5% | Degradar graciosamente sem cache | ✅ |
| Email (Resend) | 99% | → SendGrid | ✅ |
| ATS API | 95% | Enfileirar + retry | ✅ |
| WebSocket | 99% | Reconexão automática no client | ✅ |

### Rate Limits por Tenant

| Recurso | Starter | Pro | Business | Enterprise |
|---------|:-------:|:---:|:--------:|:----------:|
| Requisições LLM/hora | 100 | 500 | 2.000 | Ilimitado |
| Candidatos/busca | 50 | 200 | 1.000 | Ilimitado |
| Emails/dia | 200 | 1.000 | 5.000 | Ilimitado |
| Sessões WSI simultâneas | 5 | 20 | 100 | Ilimitado |

> **Implementação:** `app/orchestrator/tenant_budget.py` + `app/services/token_budget_service.py`

### Tamanhos Máximos de Payload

| Endpoint | Tamanho Máximo | Formato |
|---------|:--------------:|---------|
| Upload de CV | 5 MB | PDF, DOCX, TXT |
| Mensagem de chat | 4.000 chars | Texto |
| JD gerada | 10.000 chars | Markdown |
| Batch de candidatos (Gate) | 100 por vez | — |
| Export CSV | 10.000 registros | CSV/XLSX |

### Segurança

| Requisito | Implementação |
|-----------|--------------|
| Autenticação | JWT (WorkOS SSO) — header `Authorization: Bearer {token}` |
| `company_id` | Extraído do JWT claims — nunca confiar no body |
| WebSocket auth | Token no query param (`?token=`) na conexão inicial |
| HTTPS obrigatório | TLS 1.2+ em todos os endpoints |
| Rate limiting | Por IP + por tenant |
| CORS | Whitelist de domínios por tenant |

---

## 21. GUIA PRÁTICO: ONDE MEXER — 16 CENÁRIOS DE DESENVOLVIMENTO

> Referência rápida para o time de desenvolvimento. Para cada situação comum, indica exatamente quais arquivos alterar e como. Extraído do MAPA_CAMADA_INTELIGENCIA.md §11 e verificado contra o codebase LIA.

### 21.1 Tabela de Cenários (16 situações)

| # | Preciso de... | Mexo em... | Arquivo(s) |
|---|--------------|-----------|-----------|
| 1 | Nova legislação/compliance | `shared/compliance/` | `fairness_guard.py` (padrões), `audit_service.py` (log) |
| 2 | Mudar triagem de candidatos | `cv_screening/services/` | `wsi_service.py`, `evaluation_criteria_service.py` |
| 3 | Adicionar tool a um agente | `domains/*/agents/` | `*_tool_registry.py` (função + registro + STAGE_TOOLS) |
| 4 | Mudar tom/formato de resposta | `domains/*/agents/` | `*_system_prompt.py` |
| 5 | Criar novo agente/domínio | `shared/agents/` | `agent_scaffold.py` → gera 4 arquivos automaticamente |
| 6 | Mudar roteamento de intenções | `orchestrator/` | `fast_router.py` (regex), `intent_router.py` (LLM) |
| 7 | Ajustar memória/personalização | `shared/agents/` | `working_memory.py`, `long_term_memory.py` |
| 8 | Adicionar validação de viés | `shared/compliance/` | `fairness_guard.py` (novos padrões regex) |
| 9 | Mudar regra do pipeline | `cv_screening/agents/` | `pipeline_tool_registry.py`, `pipeline_system_prompt.py` |
| 10 | Adicionar canal de comunicação | `shared/channels/adapters/` | Criar novo adapter + registrar em `channel_router.py` |
| 11 | Trocar provedor de LLM | `shared/providers/` | `llm_factory.py` + criar novo `llm_*.py` |
| 12 | Adicionar benchmarks | `domains/*/agents/` | `*_tool_registry.py` (dados + fontes na tool) |
| 13 | Config por empresa (multi-tenant) | Banco de dados | `CompanyHiringPolicy` — NUNCA hardcodar em código |
| 14 | Mascarar dados pessoais (LGPD) | `shared/` | `pii_masking.py` (novos padrões PII) |
| 15 | Mudar pesos/blocos do WSI | `cv_screening/services/` | `wsi_service.py`, `wsi_deterministic_scorer.py` |
| 16 | Adicionar feature flag | `shared/governance/` | `feature_flag_service.py` |

### 21.2 Cenário Detalhado: Adicionar Nova Legislação/Compliance

```
Passo 1: shared/compliance/fairness_guard.py
   → Adicionar novos padrões regex em BLOCKED_PATTERNS
   → Adicionar novas categorias se necessário

Passo 2: fairness_guard.py (método check_semantic)
   → Atualizar instruções do LLM para incluir a nova norma

Passo 3: domains/*/agents/*_system_prompt.py (todos os agentes afetados)
   → Adicionar referência à nova norma na seção === COMPLIANCE E ÉTICA ===

Passo 4: Testar
   → Enviar texto que viola a nova norma
   → Verificar que FairnessGuard bloqueia nas 2 camadas (check + check_semantic)
   → Verificar que agente explica educacionalmente sem discriminar
```

### 21.3 Cenário Detalhado: Adicionar Tool a Agente Existente

```
Passo 1: domains/{domain}/agents/{domain}_tool_registry.py
   → Criar função async wrapper:
     async def _wrap_nova_tool(param1: str, param2: int, **kwargs) -> dict:
         try:
             resultado = await nova_tool_service.executar(param1, param2)
             return {"status": "success", "data": resultado}
         except Exception as e:
             logger.error(f"Erro nova_tool: {e}")
             return {"status": "error", "message": str(e)}

Passo 2: Mesmo arquivo — adicionar ToolDefinition em TOOL_DEFINITIONS:
   ToolDefinition(
       name="nova_tool",
       description="Descrição clara do que a tool faz e quando usar",
       parameters={"param1": {"type": "string"}, "param2": {"type": "integer"}},
       function=_wrap_nova_tool
   )

Passo 3: Mesmo arquivo — adicionar nos estágios corretos em STAGE_TOOLS:
   STAGE_TOOLS = {
       "stage_inicial": ["tool_existente", "nova_tool"],  # adicionar aqui
       "stage_avancado": ["outra_tool"],
   }

Passo 4: {domain}_system_prompt.py (opcional)
   → Adicionar instrução de quando usar a nova tool nos exemplos few-shot

Passo 5: Testar
   → Enviar mensagem que deveria triggar a nova tool
   → Verificar no LangSmith que o agente chamou a tool corretamente
   → Verificar tratamento de erro (simular falha da tool)
```

### 21.4 Cenário Detalhado: Criar Novo Domínio do Zero

```
Passo 1: Usar AgentScaffold
   from src.shared.agents.agent_scaffold import AgentScaffold
   AgentScaffold.generate(domain="novo_dominio")
   → Cria 4 arquivos com estrutura base:
     novo_dominio_react_agent.py
     novo_dominio_system_prompt.py
     novo_dominio_tool_registry.py
     novo_dominio_stage_context.py

Passo 2: Implementar tools
   → Criar funções wrapper async no tool_registry
   → Definir TOOL_DEFINITIONS e STAGE_TOOLS

Passo 3: Escrever system prompt
   → Seguir padrão 10 seções obrigatórias (ver AGT-000)

Passo 4: Registrar no ReactAgentRegistry
   → shared/agents/react_agent_registry.py

Passo 5: Adicionar roteamento
   → orchestrator/fast_router.py (padrões regex para o domínio)
   → orchestrator/intent_router.py (exemplos LLM de quando rotear)

Passo 6: Testar end-to-end
   → Enviar mensagem que deveria rotear para o novo domínio
   → Verificar: roteamento → agente → tools → resposta final
```

---

### 21.5 Anti-Patterns — NUNCA Faça Isso

| Anti-Pattern | Consequência | Alternativa Correta |
|-------------|-------------|-------------------|
| Hardcodar regras por empresa | Impossível escalar para N clientes | Use `CompanyHiringPolicy` no banco |
| Colocar dados sensíveis em logs | Violação LGPD (Art. 46) | Use `PIIMasking` antes de logar |
| Criar tool sem `try/except` | Erro não tratado crasha o ReActLoop | Sempre envolva em try/except com log |
| Mudar tool sem atualizar `STAGE_TOOLS` | Tool existe mas agente não consegue usar | Atualizar STAGE_TOOLS junto com a tool |
| Lógica crítica apenas no prompt | LLM pode ignorar a regra | Implemente em código (tool ou guard) |
| Chamar LLM sem circuit breaker | Falha do provider derruba o sistema | Use `CircuitBreaker` para chamadas externas |
| Ignorar FairnessGuard no input do usuário | Viés discriminatório passa sem detecção | Sempre valide texto com `check()` |
| Retornar traceback ao usuário | UX ruim + expõe internals do sistema | Retorne mensagem amigável no catch |

---

### 21.6 Human-in-the-Loop — Mapa de Confirmações por Ação

| Ação | Confirmação? | Risco | Domínio |
|------|:-----------:|-------|---------|
| `analisar_perfil` | NÃO | Baixo | cv_screening |
| `disparar_triagem` | NÃO | Baixo | cv_screening |
| `scoring_wsi` | NÃO | Baixo | cv_screening |
| `buscar_candidatos` | NÃO | Baixo | sourcing |
| `gerar_jd` | NÃO | Baixo | job_management |
| `mover_candidato` | SIM | Médio | pipeline |
| `aprovar_candidato` | SIM | Médio | pipeline |
| `agendar_entrevista` | SIM | Médio | scheduling |
| `enviar_email` | SIM | Alto | communication |
| `reprovar_candidato` | SIM | Alto | pipeline |
| `publicar_vaga` | SIM | Alto | job_management |
| `enviar_whatsapp_massa` | SIM | Alto | communication |

> **Ao criar nova tool:** se ela causa efeito externo (envia, publica, move, agenda, rejeita), adicione `requires_confirmation=True` no `ToolDefinition` e no `ActionExecutorService`.

---

### 21.7 Limites Operacionais — Referência Rápida

| Recurso | Limite | Configuração |
|---------|--------|-------------|
| LLM timeout (Claude/OpenAI) | 120 segundos | `shared/providers/llm_*.py` |
| LLM timeout (Gemini) | Default SDK | `shared/providers/llm_gemini.py` |
| Max tool calls por request | 3 | `MAX_TOOL_CALLS_PER_REQUEST` |
| Max iterações ReActLoop | 5 (configurável) | `ReActConfig.max_iterations` |
| Rate limit por minuto | 200 req/min por tenant | Rate limiter middleware |
| Rate limit por hora | 2.000 req/hr por tenant | Rate limiter middleware |
| Cache hot (Tier 1) | TTL 5 minutos | `cache_manager_service.py` |
| Cache warm (Tier 2) | TTL 1 hora | idem |
| Cache cold (Tier 3) | TTL 24 horas | idem |
| DB pool recycle | 3.600 segundos | Pool settings |
| Pearch searches/dia | 10 por tenant | PolicyEngine |
| Voice screenings/dia | 20 por tenant | PolicyEngine |
| Max tokens/request | 50.000 | PolicyEngine |
| Max concurrent requests | 5 por tenant | PolicyEngine |

> **Ao criar nova tool que chama LLM ou API externa:** verifique limites acima. Use `CircuitBreaker` para chamadas externas e `PolicyEngine` para limites por tenant.

---

## 22. FORA DO ROADMAP ALPHA 1 — ITENS PENDENTES E RECOMENDAÇÕES

> Esta seção consolida tudo que é relevante para a plataforma mas **não está nos cards do Alpha 1**. Fonte: `docs/analise-comparativa-v5-vs-lia.md` + recomendações de André + análise de gaps do codebase LIA.

---

### 22.1 Interfaces Conversacionais da LIA não mapeadas

Estes são os pontos de contato da LIA com o usuário (recrutador e candidato) que precisam de roadmap e design próprios. Nenhum deles tem card neste documento.

| Interface | Arquivo(s) de Referência (LIA) | Status |
|-----------|-------------------------------|--------|
| **Prompt Tabela de Vagas** | `plataforma-lia/src/app/(main)/jobs/jobs-page.tsx` — `AISearchToggle`, `useLiaSuggestions`, `callOrchestratedJobsManagement` | ❌ Sem card |
| **Prompt Página de Vaga** | `plataforma-lia/src/app/(main)/jobs/[jobId]/` — LIA contextualizada por vaga | ❌ Sem card |
| **Prompt Flutuante Geral (LIA Float)** | `plataforma-lia/src/components/lia-float/LiaChatPanel.tsx`, `use-float-streaming.ts` — WebSocket, HITL cards, streaming | ❌ Sem card |
| **Prompt Políticas de Recrutamento** | `app/domains/policy/agents/agent.py` — PolicySetupAgent 19Q conversacional | ❌ Sem card (AGT-017 cobre só o modo serviço) |
| **Prompt Funil de Talentos** | `plataforma-lia/src/app/(main)/candidates/` — KanbanAgent + TalentAgent | ❌ Sem card |
| **Interface Teams (Bot)** | `app/services/teams_notification_service.py`, MS Bot Builder — bot bidirecional | ❌ Sem card (AGT-014 cobre só alertas unidirecionais) |

**Próximo passo sugerido:** criar epic separado "Alpha 2 — Interfaces LIA" com cards para cada interface acima.

---

### 22.2 Cards AUD — Recomendações de André (Auditoria Agente Python V5)

Fonte: `docs/analise-comparativa-v5-vs-lia.md` §12 + Epic [WT-1505](https://wedotalent.atlassian.net/browse/WT-1505)

| Card | Jira | Título | Sprint | SP | Prioridade | Status |
|------|------|--------|--------|----|------------|--------|
| AUD-001 | [WT-1506](https://wedotalent.atlassian.net/browse/WT-1506) | Propagar `AuditCallback` para ReAct Agents (execução trackeada no DB) | 1 | 2 | P0 | ⏳ Pendente no V5 |
| AUD-002 | [WT-1507](https://wedotalent.atlassian.net/browse/WT-1507) | Rastrear Tools chamadas por nome (observabilidade de tools) | 1 | 1 | P1 | ⏳ Pendente no V5 |
| AUD-003 | [WT-1508](https://wedotalent.atlassian.net/browse/WT-1508) | Circuit Breaker no Autonomous Agent (`circuit_breaker.py`) | 1 | 2 | P1 | ⏳ Pendente no V5 |
| AUD-004 | [WT-1509](https://wedotalent.atlassian.net/browse/WT-1509) | Retention/Cleanup de `agent_executions` (LGPD data minimization) | 2 | 1 | P2 | ⏳ Pendente no V5 |
| AUD-005 | [WT-1510](https://wedotalent.atlassian.net/browse/WT-1510) | Storage externo para logs pesados (S3/GCS — logs >90d) | 3 | 3 | P3 | ⏳ Pendente no V5 |
| AUD-006 | [WT-1511](https://wedotalent.atlassian.net/browse/WT-1511) | Endpoints REST de Timeline de execução de agente | 3 | 3 | P3 | ⏳ Pendente no V5 |
| AUD-007 | [WT-1512](https://wedotalent.atlassian.net/browse/WT-1512) | Métricas Prometheus (8 métricas estratégicas + `/metrics` endpoint) | 3 | 3 | P3 | ⏳ Pendente no V5 |

**Total AUD:** 7 cards | 15 story points | Estimado ~19h

> **Nota:** Os cards AUD existem no Jira mas não estão integrados ao roadmap Alpha 1 deste documento. Devem ser tratados como epic paralelo de qualidade/observabilidade.

---

### 22.3 Gaps Técnicos Pendentes na LIA (não resolvidos nos Sprints A–J)

Fonte: `docs/analise-comparativa-v5-vs-lia.md` §6.2

| # | Gap | Impacto | Esforço | Prioridade |
|---|-----|---------|---------|------------|
| 1 | **IaC declarativo (Terraform/Pulumi)** | Portabilidade cloud, reproducibilidade infra | Média (2-3 semanas) | P2 |
| 2 | **Test categorization `very_hard`** | Pirâmide de testes incompleta na categoria mais crítica | Baixa (1-2 dias) | P3 |
| 3 | **Fine-tuning pipeline contínuo** | LIA aprende padrões específicos por empresa — maior acurácia | Alta (6-8 semanas) | P2 |
| 4 | **AutomationReActAgent registrado no WebSocket dispatcher** | `automation_react_agent.py` existe em `domains/automation/agents/` mas não está wired no `agent_chat_ws.py` | Baixa (1-2 dias) | P1 |

---

### 22.4 Recomendações de Portabilidade V5 → LIA (Priorizadas por Impacto × Esforço)

Fonte: `docs/analise-comparativa-v5-vs-lia.md` §9

#### P0 — Crítico (implementar antes ou junto com Alpha 1)

| # | Item | Arquivo LIA de Referência | Esforço |
|---|------|--------------------------|---------|
| 1 | Limpeza estrutural do repo V5 | — | 1-2 dias |
| 2 | Prompt injection global | `app/shared/prompt_injection.py` | 3-5 dias |
| 3 | Multi-provider LLM (LLMFactory) | `app/shared/providers/llm_factory.py` | 2-3 semanas |
| 4 | Circuit Breaker | `app/shared/resilience/circuit_breaker.py` | 3-5 dias |
| 5 | Rate Limiting (sliding window Redis) | `app/shared/resilience/rate_limiter.py` | 3-5 dias |
| 6 | PII Masking global (logger) | `app/shared/pii_masking.py` | 2-3 dias |

#### P1 — Alto (1-2 meses pós Alpha 1)

| # | Item | Arquivo LIA de Referência | Esforço |
|---|------|--------------------------|---------|
| 7 | Token Tracking + alertas 80%/100% | `app/services/token_tracking_service.py` | 1-2 semanas |
| 8 | Policy Middleware FastAPI | `app/orchestrator/policy_middleware.py` | 1-2 semanas |
| 9 | Structured Logging (JSON + PII) | `app/core/structured_logging.py` | 2-3 dias |
| 10 | Audit Trail persistente (DB) | `app/shared/compliance/audit_service.py` | 1-2 semanas |
| 11 | Confidence Policies por domínio | `app/services/confidence_policy_service.py` | 1-2 semanas |
| 12 | CI/CD Pipeline (GitHub Actions) | `.github/workflows/ci.yml` LIA | 1-2 dias |

#### P2 — Médio (2-4 meses)

| # | Item | Arquivo LIA de Referência | Esforço |
|---|------|--------------------------|---------|
| 13 | Learning Loop (DPO feedback export) | `app/services/learning_loop_service.py` | 3-4 semanas |
| 14 | A/B Testing de prompts | `app/services/ab_testing_service.py` | 1-2 semanas |
| 15 | Output Validation (OWASP LLM02) | validação estruturada de outputs LLM | 1-2 semanas |

---

### 22.5 Oportunidades de Produto (Novas Features — Pós Alpha 1)

Fonte: `docs/analise-comparativa-v5-vs-lia.md` §11.2

| # | Feature | Benefício | Complexidade |
|---|---------|-----------|-------------|
| 1 | **Wizard-to-Pipeline handoff automático** | Ao criar vaga via wizard, abre kanban automaticamente em split-view | Média |
| 2 | **Dashboard Analytics em tempo real via chat** | Insights de recrutamento conversacionais com gráficos gerados in-chat | Alta |
| 3 | **Communication agent com templates inteligentes** | Sugere template de email por estágio do candidato — reduz 80% do tempo | Média |
| 4 | **ATS sync bidirecional em tempo real** | Mudanças no Gupy/Pandapé refletem no kanban via PlatformEvents | Alta |
| 5 | **LIA como copiloto contextual em páginas** | Ao navegar para qualquer página, LIA assume contexto automaticamente | Alta |
| 6 | **Fine-tuning contínuo por empresa** | Exportar feedback DPO para fine-tuning — LIA aprende padrões da empresa | Muito alta |
| 7 | **Multi-tenant split-view config** | Cada empresa com config independente de split-view (domínios habilitados, threshold de confiança) por tier de plano | Média |

---

### 22.6 Oportunidades Técnicas Adicionais (v5.0)

> **Fonte:** `relatorio_capacidades_prompts_lia.md` seção 9.10 + investigação do codebase

| # | Oportunidade | Complexidade | Impacto |
|---|-------------|-------------|---------|
| 1 | Registro dinâmico de agentes via YAML (sem restart) | Alta | Alto |
| 2 | Multi-model por agente (GPT para tasks rápidas, Claude para análise, Gemini para embeddings) | Média | Alto |
| 3 | RAG por domínio com embeddings dedicados | Alta | Alto |
| 4 | Circuit breaker para Pearch AI (já existe infra, falta config) | Baixa | Médio |
| 5 | Validar escopo de tools no backend (não apenas no config) | Baixa | Alto |
| 6 | Ativar FairnessGuard em TODOS os agentes (atualmente só 4 de 11) | Baixa | Alto |
| 7 | Remover IntentRouter legado (duplicação com LLM Cascade) | Baixa | Médio |
| 8 | Streaming de pensamentos ReAct via WebSocket (transparência para o usuário) | Média | Médio |

---

## Pendências Futuras — Análise Comparativa v5 vs LIA

> Fonte: `docs/analise-comparativa-v5-vs-lia.md` v9.1 (10/03/2026). Itens não cobertos nas Seções 22.1–22.5 acima. Organizados por tema.

---

### Scorecard Comparativo — 14 Dimensões (v9.0 — 10/03/2026)

> ↑ = melhoria no V9.0 vs v8.0. Scores de 1-10 baseados em leitura direta do código-fonte + benchmark de mercado.

| Dimensão | V5 | LIA v9.0 | Delta | Vantagem |
|----------|-----|----------|-------|----------|
| D1. Arquitetura de Agentes | 7.0 | 9.3 ↑ | +2.3 | LIA |
| D2. Qualidade de Código | 6.5 | 7.6 ↑ | +1.1 | LIA |
| D3. **Organização/Estrutura** | **3.5** | **7.9** | **+4.4** | **LIA** |
| D4. Eficiência LLM | 7.5 | 8.0 | +0.5 | LIA |
| D5. Governança IA | 5.0 | 9.6 | +4.6 | LIA |
| D6. Segurança | 5.5 | 9.0 | +3.5 | LIA |
| D7. Human-in-the-Loop | 5.5 | 9.4 ↑ | +3.9 | LIA |
| D8. Sistema de Aprendizado | 3.0 | 7.5 | +4.5 | LIA |
| D9. **Tool System** | **8.5** | **7.5** | **-1.0** | **V5** |
| D10. Observability | 5.0 | 9.7 | +4.7 | LIA |
| D11. Testes | 7.0 | 9.2 ↑ | +2.2 | LIA |
| D12. Infraestrutura | 7.5 | 9.8 | +2.3 | LIA |
| D13. Multi-provider LLM | 1.0 | 8.5 | +7.5 | LIA |
| D14. Resiliência | 3.0 | 9.5 | +6.5 | LIA |
| **Média** | **5.4** | **9.0 ↑** | **+3.6** | **LIA** |

> **Único ponto de vantagem V5 (D9 — Tool System):** V5 possui 70 tools YAML declarativas vs 32 da LIA. A LIA usa abordagem híbrida (YAML + code-driven) que é mais flexível mas menos inspecionável. Ver PF-1 item 6 (function calling nativo) e G5 (YAML Tool Registry já implementado).

---

### Métricas Quantitativas Comparadas (v9.0 — filesystem verificado)

| Métrica | V5 | LIA |
|---------|-----|-----|
| Arquivos Python (app/) | ~196 | **1.180+** |
| LOC estimado | ~49K | ~465K+ |
| Domínios DDD | 2 | **12** |
| Agentes ReAct (padrão 4-file) | 0 | **13 ReAct** + 3 StateGraph (16 total) |
| Tools YAML declarativos | **70** | 32 YAML + code-driven |
| Routers REST registrados | 0 (CLI) | **204** |
| Serviços (app/services/) | ~15 | **215** |
| Modelos SQLAlchemy | — | **99** |
| Migrations Alembic | — | **36** (inc. compliance: HITL, fairness, bias, guardrails) |
| Providers LLM | 1 (Gemini) | **3** (Claude primário + OpenAI + Gemini) + Factory |
| Canais de comunicação | 1 (callback REST) | **5** (email, WhatsApp, SMS, Teams, in-app Bell) |
| Testes BE coletados | 53 arquivos | **3.712+** coletados · 0 falhas · 208 arquivos |
| Cobertura BE | — | **32.66%** (gate CI: 32%) |
| Testes FE | — | Vitest + **60+** unitários |
| Testes de carga | — | Locust (WizardUser + PipelineUser + HealthCheckUser) |
| Libs UV Monorepo | — | **10** libs |
| Serviços Docker Compose | 2 workers | **14** serviços (incl. Prometheus, Grafana, Celery multi-fila) |
| Métricas Prometheus | — | **13+** |
| Páginas Next.js | — | **89** |
| Hooks FE (src/hooks/) | — | **85** (76 hooks + 9 test files) |
| Componentes FE (src/components/) | — | **47 diretórios** (~450 arquivos .tsx) |

---

### O que V5 tem que LIA ainda não tem (gaps a fechar)

| Item | V5 | LIA | Ação necessária |
|------|----|-----|-----------------|
| Tool System YAML — qtde | **70 tools** | 32 tools | Expandir YAML registry (G5 base já existe) |
| TOON format nativo para tools | `documentation_toon/` 30+ YAMLs | `toon_service.py` para candidatos | Aplicar TOON compacto para tools também |
| RAG com reranking explícito | pgvector + full-text + reranking | pgvector + BM25 alpha blend | Adicionar reranking cross-encoder ao RAG |
| Test categorization `very_hard` | Sim (testes difíceis categorizados) | Markers registrados, sem testes | Criar 10+ testes `very_hard` (WSI/HITL/multi-tenant) |
| Pipeline linear plan-execute | `WorkflowOrchestrator` | ReAct loop (mais flexível) | — (LIA já é mais avançada aqui) |
| AuditCallback propagado a todos agentes | ❌ gap identificado (AUD-001) | `AuditCallback` existe em `shared/compliance/` | Propagar para todos ReAct agents (card WT-1506) |
| Tool tracking por nome na auditoria | ❌ gap (AUD-002) | Tool registry existe | Rastrear nome da tool chamada por execução (WT-1507) |
| Circuit Breaker no agente autônomo | ❌ gap (AUD-003) | `@circuit_breaker` em providers | Aplicar no `AutonomousAgentService` (WT-1508) |
| Retention/Cleanup de agent_executions | ❌ gap (AUD-004) | Scheduler LGPD existe | Adicionar job de cleanup para agent_executions (WT-1509) |
| Storage externo para logs pesados | ❌ gap (AUD-005) | S3 lifecycle SOX implementado | Ativar política em produção para agent logs (WT-1510) |
| Endpoints REST de timeline de execução | ❌ gap (AUD-006) | `ExecutionLogStore` existe | Criar endpoints públicos de timeline (WT-1511) |
| Métricas Prometheus por agente | ❌ gap (AUD-007) | 13+ métricas gerais | Adicionar métricas granulares por agente/tool (WT-1512) |

> Os 7 cards AUD (WT-1506 → WT-1512) estão no Epic **WT-1505** e representam o roadmap de remediação de auditabilidade, resiliência e observabilidade — tanto para o V5 quanto para gaps que a LIA deve fechar por simetria.

---

### PF-1 Agentes e Arquitetura

| # | Item | Detalhe | Prioridade |
|---|------|---------|------------|
| 1 | **Smoke tests por domínio WS com dados reais** | Todos os 10 domínios registrados no WS dispatcher precisam de suite de regressão com dados reais — `USE_LANGGRAPH_NATIVE=True` ativo mas sem cobertura de smoke tests end-to-end por domínio | P1 |
| 2 | **AutomationReActAgent wired no WS dispatcher** | `automation_react_agent.py` existe em `app/domains/automation/agents/` com padrão 4-file completo mas não está registrado em `agent_chat_ws.py`. Correção estimada: 1-2 dias, 1 linha no dispatcher | P1 |
| 3 | **PolicyReActAgent (legado) substituído pelo PolicySetupAgent** | `policy_react_agent.py` (item 9 no inventário de agentes) marcado como "legado" — não registrado no WS. Avaliar deprecação formal ou migração completa para `domains/policy/agents/agent.py` | P2 |
| 4 | **Conversão do pipeline linear V5 para ReAct pattern** | V5 usa pipeline plan-execute hardcoded (`WorkflowOrchestrator`). Para o time V5, converter para ReAct loop com tool selection dinâmica (padrão LIA). Esforço estimado: 3-4 semanas | P2 (V5) |
| 5 | **Delegation pattern entre agentes** | LIA não implementa delegation (CrewAI pattern) — agente A delegar subtask ao agente B dinamicamente. Relevante para fluxos complexos multi-domínio | P3 |
| 6 | **Function calling nativo via API** | Tools do V5 mapeiam para endpoints REST (não function calling nativo da API Anthropic/OpenAI). LIA usa ToolNode LangGraph, mas avaliar migração para function calling API nativo para performance | P3 |
| 7 | **Subgraphs LangGraph** | Usar subgraphs para composição de workflows complexos (sourcing, evaluation, scheduling como subgraphs de um fluxo maior) — padrão LangGraph canônico não utilizado ainda | P3 |

---

### PF-2 Frontend (God Object e Qualidade FE)

| # | Item | Detalhe | Prioridade |
|---|------|---------|------------|
| 1 | **Extração de `useCandidatesModals`** | `candidates-page.tsx` em ~10.592 linhas. Sprint dedicado para extrair hook de modais — principal bloqueio para reduzir abaixo de 8.000 linhas | P0 |
| 2 | **Extração de `CandidatesFilterPanel` como componente autônomo** | Painel de filtros ainda embutido no god object. Extração permite testes unitários independentes | P1 |
| 3 | **Extração de `CandidatesTable` como componente autônomo** | Tabela principal ainda no god object. Componente crítico para testes de renderização | P1 |
| 4 | **`use-candidates-search.ts` e `use-candidates-pagination.ts`** | Dois hooks faltantes para completar a decomposição de `candidates-page.tsx`: busca avançada e paginação como hooks independentes | P1 |
| 5 | **Testes unitários FE para componentes extraídos** | `CandidateSearchBar`, `CandidateTabs`, `SearchResultsHeader` foram extraídos mas carecem de suíte de testes Vitest equivalente aos 9 testes do Sprint J | P1 |

---

### PF-3 Backend e Cobertura de Testes

| # | Item | Detalhe | Prioridade |
|---|------|---------|------------|
| 1 | **Coverage incremental: 32.66% → 40% → 60% → 80%** | Gate CI atual: 32% (achieved 32.66%). Alvos: `candidate_search.py` (2299 stmts), `company.py` (1815 stmts), `job_vacancies.py` (1821 stmts). Requer mocks de DB pesados. Meta aspiracional 80% | P1 |
| 2 | **Test categorization `very_hard`** | Marker registrado em `pytest.ini` mas sem nenhum teste classificado nessa categoria. V5 tem testes `very_hard` (ex: `test_difficult_cases.py`). Adicionar 10+ testes WSI/HITL/multi-tenant nessa categoria | P2 |
| 3 | **Property-based testing (Hypothesis)** | Testes de propriedade para schemas Pydantic e serviços críticos — padrão não adotado na LIA. Benefício: descoberta de edge cases não cobertos por testes manuais | P3 |
| 4 | **Mutation testing** | Verificar qualidade dos testes existentes via mutation testing (Mutmut) — testes que não capturam mutations são candidatos a revisão | P3 |
| 5 | **God object BE: `candidate_search.py`** | Arquivo com 2299 statements — maior arquivo de serviço do backend. Candidato a decomposição seguindo padrão SRP | P2 |

---

### PF-4 Infraestrutura e Deploy

| # | Item | Detalhe | Prioridade |
|---|------|---------|------------|
| 1 | **IaC declarativo (Terraform/Pulumi)** | Scripts bash `deploy/gcp_setup.sh` e `deploy/aws_setup.sh` existem. Deploy declarativo via Terraform ou Pulumi ausente. Necessário para reproducibilidade e portabilidade cloud | P2 |
| 2 | **Secrets Management (Vault/KMS)** | Variáveis de ambiente em `.env` plaintext. Migração para HashiCorp Vault ou AWS KMS necessária para production readiness enterprise (SOC 2 requisito) | P2 |
| 3 | **Auto-scaling (Kubernetes/ECS)** | Deploy atual é Docker Compose em VM. Para escala enterprise: Kubernetes (GKE/EKS) ou ECS com auto-scaling horizontal baseado em carga | P3 |
| 4 | **Staging environment** | Sem ambiente de staging separado do produção. Requisito para CI/CD enterprise-grade — deployments validados antes de ir para prod | P2 |
| 5 | **Rollback strategy** | Sem estratégia de rollback automático documentada. Necessário para `deploy.yml` — deploy → health check → rollback automático se falhar | P2 |
| 6 | **Dependency scanning automático** | `pip-audit` e `npm audit` existem no CI mas sem Dependabot para PRs automáticos de updates. Requisito OWASP LLM05 | P2 |
| 7 | **Runbook operacional** | Sem documentação de runbook (operações de rotina, troubleshooting, escalation) — requisito para on-call e compliance SOC 2 | P2 |

---

### PF-5 Compliance, Governança e Segurança

| # | Item | Detalhe | Prioridade |
|---|------|---------|------------|
| 1 | **Explainability (EU AI Act Art. 13)** | Logging do reasoning chain completo de cada decisão do agente. LIA tem `AuditCallback` mas sem endpoint público de explicabilidade por decisão | P1 |
| 2 | **Bias monitoring dashboard** | Dashboard visual com métricas de fairness ao longo do tempo (trend de `adverse_impact_ratio` por vaga/empresa). `bias_audit_service.py` e `BiasAuditSnapshot` existem — falta UI | P2 |
| 3 | **FRIA (Fundamental Rights Impact Assessment)** | EU AI Act Art. 6 Annex III exige avaliação de impacto em direitos fundamentais para sistemas de triagem. LIA não tem template/processo formal de FRIA | P2 |
| 4 | **Output Validation (OWASP LLM02)** | Validação estruturada de outputs LLM contra schema esperado antes de retornar ao usuário. LIA tem `FactChecker` mas sem validação de schema de output genérica | P1 |
| 5 | **Risk classification por tipo de output** | Classificar outputs por nível de risco: hire/reject = alto risco; list/search = baixo risco. Permite aplicar salvaguardas proporcionais ao risco | P2 |
| 6 | **Human oversight por confidence threshold** | Escalation automática para humano quando LLM está com baixa confiança. `confidence_policy_service.py` existe mas sem integração com HITL automático | P2 |
| 7 | **LGPD Art. 7 — consentimento para todos os canais** | Verificar se canal WhatsApp e Teams têm verificação de consentimento equivalente ao email. `LGPD_consent` implementado mas cobertura de canais precisa de auditoria | P1 |

---

### PF-6 Observabilidade e Monitoramento

| # | Item | Detalhe | Prioridade |
|---|------|---------|------------|
| 1 | **Dashboard Grafana integrado** | Prometheus já coleta 13+ métricas. Docker Compose prod tem Prometheus+Grafana mas dashboards/alertas Grafana não estão configurados com queries prontas | P2 |
| 2 | **Alerting rules Prometheus** | `alertmanager` não configurado. Regras de alerta para: latência P95 > threshold, error rate > 5%, circuit breaker aberto, agent quality score abaixo de threshold | P2 |
| 3 | **Distributed tracing (OpenTelemetry completo)** | `app/shared/tracing.py` existe mas cobertura de instrumentação não verificada para todos os domínios. V5 usa apenas LangSmith | P2 |
| 4 | **Error aggregation Sentry — configuração por ambiente** | Sentry integrado no BE e FE. Verificar configuração de `environment` (dev/staging/prod) e `release` para rastreabilidade entre deploys | P1 |
| 5 | **LangGraph Studio integrado** | `langgraph.json` existe para LangGraph Studio. Documentar fluxo de uso para debugging de graphs em desenvolvimento | P3 |
| 6 | **S3/GCS lifecycle para logs pesados** | Fase G3 implementou `celery task audit.apply_lifecycle_policy` mensal. Verificar se política está ativa em produção: Standard→Glacier IR→Deep Archive→delete (7 anos SOX) | P1 |

---

### PF-7 Aprendizado e IA Adaptativa

| # | Item | Detalhe | Prioridade |
|---|------|---------|------------|
| 1 | **Fine-tuning pipeline contínuo** | `lia_feedback.py` exporta dados DPO mas pipeline de fine-tuning automático ausente. Requer: (a) coleta de feedback estruturado, (b) curadoria do dataset, (c) job de fine-tuning periódico, (d) A/B testing do modelo fine-tuned vs base | P2 |
| 2 | **Personalização por empresa (model-per-tenant)** | LIA aprende padrões globais mas não tem isolamento de aprendizado por tenant. Cada empresa poderia ter pesos calibrados por seus padrões históricos de contratação | P3 |
| 3 | **A/B testing de modelos LLM** | `ab_testing_service.py` existe para prompts. Estender para A/B de modelos LLM (ex: Claude Sonnet vs Claude Haiku em determinado domínio) — útil para otimização de custo × qualidade | P2 |
| 4 | **Few-shot examples de RH sênior validados** | System prompts com exemplos few-shot existem mas sem exemplos validados por especialistas sêniores de RH. Benchmark de qualidade das respostas dos agentes contra gold standard | P2 |
| 5 | **Model drift detection para todos os agentes** | `model_drift_service.py` com 4 triggers existe. Verificar cobertura: quais agentes têm drift detection ativo vs quais ainda não têm métricas de baseline | P1 |

---

### PF-8 Roadmap Sugerido (Sprints K-M — Pós Sprint J)

> Fonte: `docs/analise-comparativa-v5-vs-lia.md` §11.4. Itens não cobertos nos cards Alpha 1.

```
Sprint K (Semana 1-2): Produto — Features de Alta Demanda
├── Wizard→Pipeline handoff automático no split-view (PF-1 § oportunidade)
├── AutomationReActAgent wired no WS dispatcher (PF-1 item 2 — 1 linha em agent_chat_ws.py)
├── Smoke tests por domínio WS com dados reais (PF-1 item 1)
└── candidates-page.tsx: extração useCandidatesModals hook (PF-2 item 1)

Sprint L (Semana 3-4): Qualidade + Cobertura
├── Coverage: 32.66% → 40% (candidate_search.py, company.py, job_vacancies.py)
├── Test categorization very_hard: 10+ testes WSI/HITL/multi-tenant
├── Fine-tuning: pipeline DPO training contínuo (lia_feedback.py já exporta)
└── IaC básico: Terraform para GCP/AWS (PF-4 item 1)

Sprint M (Semana 5-6): Features Avançadas
├── Dashboard Analytics real-time: gráficos via AnalyticsReActAgent WS
├── Communication agent: templates inteligentes por stage do candidato
├── ATS sync bidirecional via PlatformEvents
└── Multi-tenant split-view config (por plano Starter/Pro/Enterprise)
```

---

### PF-9 Riscos Identificados na Análise Comparativa

> Fonte: `docs/analise-comparativa-v5-vs-lia.md` §10.1.

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **God object FE regression** — mudança em `candidates-page.tsx` quebra features escondidas | Alta | Alto | Extrair componentes + testes unitários por componente (PF-2) |
| **Coverage regression** — novos endpoints sem cobertura rebaixam gate CI | Média | Médio | Gate incremental: 32% → 40% → 60% (PF-3 item 1) |
| **ReAct loop depth ilimitado** — agente em loop infinito sem circuit breaker no loop | Média | Alto | `MAX_TOOL_CALLS_PER_REQUEST=3` + `MAX_ITERATIONS=5` já configurados — verificar enforcement |
| **Smoke test ausente** — agente wired mas com bug de integração descoberto só em prod | Alta | Alto | Suite de smoke tests por domínio WS (PF-1 item 1) |
| **Fine-tuning dataset enviesado** — feedback capturado sem curadoria pode amplificar bias existente | Média | Crítico | Curadoria com FairnessGuard antes de incluir no dataset DPO |
| **IaC ausente** — infra recriada manualmente em caso de disaster recovery | Alta | Alto | Terraform/Pulumi (PF-4 item 1) |
