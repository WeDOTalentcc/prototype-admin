# Mapeamento de Capacidades dos Prompts da LIA × v5

**Versão:** 1.0 | **Data:** Março/2026 | **Autoria:** Análise de código LIA + recruiter_agent_v5 (GitHub WeDOTalent)

---

## Índice

1. [Como ler este documento](#como-ler)
2. [Visão geral: os 4 contextos de prompt](#visao-geral)
3. [Prompt 1 — Flutuante / Global](#prompt-1)
   - 3.1 [Capacidades IN](#p1-in)
   - 3.2 [Restrições OUT e Delegação](#p1-out)
   - 3.3 [Dados coletados e gerados](#p1-dados)
   - 3.4 [Arquitetura técnica — LIA](#p1-lia)
   - 3.5 [Arquitetura técnica — v5](#p1-v5)
   - 3.6 [Diagrama de delegação e migração de contexto](#p1-diagrama)
   - 3.7 [Comparativo LIA × v5](#p1-comparativo)
4. [Prompt 2 — Expandido: Tabela de Vagas](#prompt-2)
   - 4.1 [Capacidades IN](#p2-in)
   - 4.2 [Restrições OUT](#p2-out)
   - 4.3 [Dados coletados e gerados](#p2-dados)
   - 4.4 [Arquitetura técnica — LIA](#p2-lia)
   - 4.5 [Arquitetura técnica — v5](#p2-v5)
   - 4.6 [Comparativo LIA × v5](#p2-comparativo)
5. [Prompt 3 — Expandido: Dentro da Vaga (Kanban)](#prompt-3)
   - 5.1 [Capacidades IN](#p3-in)
   - 5.2 [Restrições OUT](#p3-out)
   - 5.3 [Dados coletados e gerados](#p3-dados)
   - 5.4 [Arquitetura técnica — LIA](#p3-lia)
   - 5.5 [Arquitetura técnica — v5](#p3-v5)
   - 5.6 [Comparativo LIA × v5](#p3-comparativo)
6. [Prompt 4 — Expandido: Funil de Talentos](#prompt-4)
   - 6.1 [Capacidades IN](#p4-in)
   - 6.2 [Restrições OUT](#p4-out)
   - 6.3 [Dados coletados e gerados](#p4-dados)
   - 6.4 [Arquitetura técnica — LIA](#p4-lia)
   - 6.5 [Arquitetura técnica — v5](#p4-v5)
   - 6.6 [Comparativo LIA × v5](#p4-comparativo)
7. [Tabela-resumo global: 4 prompts × 10 dimensões](#tabela-resumo)
8. [Glossário técnico](#glossario)

---

## 1. Como ler este documento {#como-ler}

Este documento compara **dois sistemas de agentes de IA** que alimentam a mesma interface de usuário (ATS WeDOTalent):

- **LIA** (`lia-agent-system/`) — backend FastAPI em Python, arquitetura baseada em domínios YAML + orquestrador Python. Código local no repositório.
- **v5** (`recruiter_agent_v5`) — backend LangGraph em Python, arquitetura baseada em domínios Python + hub de roteamento. Código em GitHub (WeDOTalent/recruiter_agent_v5).

Cada "prompt" corresponde a um **contexto de interface**: o frontend envia `context_page` junto com a mensagem, e o backend carrega o(s) domínio(s) correto(s) para aquela tela.

**Convenções utilizadas:**
- ✅ Capacidade implementada e funcional
- ⚠️ Implementada mas com limitação conhecida
- ❌ Não existe / fora do escopo
- `[ESCRITA]` — ação que modifica dados, sempre requer confirmação do usuário
- `[LOTE]` — ação em massa sobre múltiplos registros

---

## 2. Visão geral: os 4 contextos de prompt {#visao-geral}

A tabela abaixo mostra como o frontend mapeia páginas para contextos de agente em cada sistema:

| UI / Página | context_page (LIA) | context_type (LIA) | domain payload (v5) | Domínio v5 |
|---|---|---|---|---|
| Chat flutuante (toda página) | `general` | `general` | `null` + `hub_mode: true` | `autonomous` |
| Tabela de vagas `/jobs` | `job`, `jobs`, `vacancies`, `wizard` | `job_management` | `"jobs"` | `jobs` |
| Dentro da vaga `/jobs/{id}` | `pipeline`, `kanban` | `pipeline` | `"applies"` | `applies` |
| Funil de talentos `/candidates`, `/sourcing/{id}` | `sourcing`, `talent` | `talent_funnel` | `"sourced_profile_sourcing"` | `sourced_profile_sourcing` |

**Fontes do código:**
- LIA: `lia-agent-system/app/orchestrator/context_adapter.py` → `PAGE_TO_CONTEXT_TYPE`
- v5: `src/hub/catalog.py` → `NAVIGATION_ROUTES`, `src/api.py` → `ChatRequest.domain`

---

## 3. Prompt 1 — Flutuante / Global {#prompt-1}

### O que é e onde aparece

O **Prompt Flutuante** é o assistente que aparece em **todas as páginas** da plataforma como um ícone de chat. O usuário pode abri-lo a qualquer momento, independentemente de estar na tela de vagas, kanban ou sourcing. É o modo mais genérico da LIA — um copiloto de recrutamento com visão 360° do ATS.

**Quando usar:** briefing do dia, perguntas gerais, navegação, análises cross-vagas, comparação de finalistas, priorização de agenda, insights sobre o processo.

**Quando NÃO usar:** criar uma vaga (→ Prompt 2), triar CVs de uma vaga específica (→ Prompt 3), buscar candidatos no pool de sourcing (→ Prompt 4).

---

### 3.1 Capacidades IN {#p1-in}

#### Briefing e Agenda
- **Briefing diário** — resumo de pendências, candidatos para revisar, entrevistas do dia, alertas urgentes, vagas com deadline próximo
- **Priorização de agenda** — organiza tarefas por urgência e impacto, sugere o que fazer primeiro
- **Alertas de SLA** — vagas paradas há mais de N dias, candidatos sem follow-up, entrevistas sem feedback registrado
- **Notificações não lidas** — quantidade e detalhe de alertas e aprovações pendentes

#### Análise de Pipeline (visão cross-vagas)
- **Overview do pipeline** — visão consolidada de candidatos em todas as vagas abertas
- **Identificação de candidatos em risco** — detecta quem está parado há mais tempo em uma etapa
- **Comparação de finalistas** — tabela comparativa lado a lado de múltiplos candidatos
- **Diagnóstico completo de vaga** — coleta em paralelo: dados + kanban + analytics + atividade recente
- **Saúde do pipeline de múltiplas vagas** — score, gargalos, candidatos parados por vaga

#### Ações sobre Vagas
- **Busca de vagas** — por título, status, departamento, localidade
- **Detalhes de vaga** — dados completos incluindo pipeline de candidatos
- **Alterar status de vaga** — publicar, pausar, fechar, reabrir, arquivar `[ESCRITA]`
- **Copiar/duplicar vaga** `[ESCRITA]`
- **Iniciar sourcing automático** — dispara busca de candidatos para uma vaga
- **Estatísticas agregadas de vagas** — total, ativas, pausadas, arquivadas, urgentes

#### Ações sobre Candidatos e Candidaturas
- **Buscar candidatos** — por nome, skill, localidade, experiência
- **Detalhes de candidato** — perfil completo, histórico de processos
- **Mover candidatura de etapa** `[ESCRITA]`
- **Aprovar/rejeitar candidato** `[ESCRITA]`
- **Candidatos parados em etapas** — detecta por vaga e por severidade (attention/warning/critical)
- **Analytics de uma candidatura** — funil, taxa de conversão, tempo em cada etapa

#### Comunicação e Notificações
- **Enviar feedback de rejeição** — mensagem respeitosa sem dados protegidos `[ESCRITA]`
- **Notificações e mensagens** — busca e exibe mensagens do usuário
- **Aprovações pendentes** — lista solicitações aguardando aprovação do recrutador

#### Agendamento
- **Agenda de entrevistas do dia** — eventos com `has_feedback` para detectar sem retorno
- **Criar evento no calendário** `[ESCRITA]`
- **Horários disponíveis** — verifica disponibilidade para agendamento
- **Gerar link de self-scheduling** — candidato escolhe horário `[ESCRITA]`
- **Buscar reuniões por vaga** — filtra entrevistas agendadas por `job_id`
- **Entrevistas sem feedback** — bulk endpoint que retorna eventos passados sem feedback

#### Avaliações
- **Listar avaliações/testes** — por vaga, com status e score
- **Candidatos em avaliações** — status (pending/completed/expired), score, data
- **Enviar avaliação para candidato** `[ESCRITA]`

#### Organização e Listas
- **Departamentos** — árvore hierárquica da empresa
- **Listas de candidatos/vagas** — busca e criação de listas organizadas
- **Adicionar a lista** — single ou bulk (async) `[ESCRITA]`
- **Métricas de produtividade** — ações realizadas, candidatos movimentados, tempo de resposta

#### Planejamento e Controle (exclusivo v5)
- **write_plan** — cria e atualiza plano de execução visível em tempo real (etapas: ⬜→🔄→✅)
- **think** — raciocínio estruturado antes de agir em passos complexos
- **File system virtual** — salva/lê resultados grandes (>5K chars) em arquivos temporários
- **Tool discovery** — descobre endpoints disponíveis da API (como SHOW TABLES do SQL)
- **Fallback genérico** — chama qualquer endpoint da API Rails não coberto pelas tools específicas

---

### 3.2 Restrições OUT e Delegação {#p1-out}

| O que NÃO faz | Por quê | Onde fazer |
|---|---|---|
| Triagem detalhada de CVs com score WSI | Requer contexto de vaga específica carregado | Prompt 3 (Kanban) |
| Criação de vaga com wizard conversacional completo | Requer domínio `job_management` com tools JOB_TABLE | Prompt 2 (Tabela de Vagas) |
| Busca avançada no banco de talentos com scoring de compatibilidade | Requer contexto de sourcing carregado (`sourcing_id`) | Prompt 4 (Funil de Talentos) |
| Condução de entrevista WSI estruturada (CBI) | Requer domínio `interview_scheduling` | Prompt 3 (Kanban) |
| Configuração de integrações ATS | Fora do escopo de todos os prompts de chat | Painel de configurações |

---

### 3.3 Dados coletados e gerados {#p1-dados}

**Dados de entrada (inputs):**
- `message` — pergunta/instrução do usuário
- `user_id` + `company_id` — identidade e contexto multi-tenant
- `conversation_id` — histórico da sessão para memória
- `viewing_entities` (v5) — entidades visíveis na tela (job_id, candidate_id atual)
- `current_path` (v5) — URL atual para resolução de contexto implícito
- `session_id` — isolamento de sessão

**Dados gerados (outputs):**
- Briefing formatado (bullets: urgentes → importantes → informativos)
- Tabela comparativa de finalistas (markdown)
- Diagnóstico completo de vaga (pipeline + analytics + alertas)
- Plano de execução com status em tempo real (v5: `write_plan`)
- Resultados intermediários em arquivo virtual (v5: offloading >5K chars)
- Confirmação de ações com preview antes de executar

---

### 3.4 Arquitetura técnica — LIA {#p1-lia}

```
Frontend (context_page: "general")
    ↓
ContextAdapter.from_rest()
    → context_type = "general"
    ↓
MainOrchestrator
    → carrega domínio: recruiter_assistant.yaml
    → tools disponíveis (scope: GLOBAL):
        - get_company_config
        - capture_wizard_feedback
        - generate_report
        - schedule_report
    ↓
Agentes disponíveis: orchestrator, recruiter_assistant
    ↓
Canal: REST /api/v1/chat | WebSocket | RabbitMQ
```

**System prompt:** `lia-agent-system/app/prompts/domains/recruiter_assistant.yaml`

**Persona:** "Assistente pessoal do recrutador: proativo, conciso, focado em ações práticas e planejamento inteligente do dia de trabalho."

**Padrões de comportamento aplicados** (`interaction_patterns.py`):
- `NEGATION_DETECTION_BLOCK` — cancela ação imediatamente se mensagem contém negação explícita
- `CHAIN_OF_THOUGHT_BLOCK` — raciocina dentro de `<thought>` antes de responder
- `ANTI_SYCOPHANCY_BLOCK` — nunca concorda para evitar conflito; apresenta dados antes de validar

**Formato de resposta:**
- Briefing: bullet list urgentes → importantes → informativos
- Comparação: tabela markdown lado a lado
- Insights: `[Insight]` contexto + ação recomendada
- Encerramento sempre com: "Próximas ações sugeridas: [1] [2] [3]"

**Segurança:**
- `ContextAdapter.validate_entity_ownership()` — IDOR prevention: valida que `entity_id` pertence a `company_id`
- Validação em tabelas: `sourcing_sessions`, `job_vacancies`, `candidates`

---

### 3.5 Arquitetura técnica — v5 {#p1-v5}

```
Frontend (domain: null, hub_mode: true)
    ↓
POST /chat ou /chat/stream (SSE)
    ↓
MessageRouter.route()
    ↓
HubPlanner (LLM-based)
    → analisa query com PLANNER_SYSTEM_PROMPT
    → detecta padrões regex:
        - FAST_NAV_PATTERNS → navegação direta (sem LLM)
        - _JOB_ID_PATTERN → abre vaga específica
        - _CANDIDATE_ID_PATTERN → abre candidato específico
        - MULTI_INTENT_RE → detecta multi-intenção → HubTask[] paralelo
    → gera HubExecutionPlan { tasks[], strategy, navigation_actions[] }
    ↓
AutonomousDomain
    → AUTONOMOUS_SYSTEM_PROMPT (100+ linhas de regras)
    → 73+ tools organizadas por módulo:

    VAGAS (tools/jobs.py):
      search_jobs | get_job | create_job | update_job | get_job_kanban
      get_job_analytics | get_matching_candidates | update_job_status
      get_all_jobs_stats | duplicate_job | get_job_selective_processes
      get_pipeline_health | get_multi_job_analytics | get_job_context_rich
      get_job_org_structure | get_job_ai_suggestion | get_job_questions
      start_auto_sourcing | send_reject_feedback | bulk_add_list_to_job
      get_job_alerts | bulk_archive_jobs | bulk_pause_jobs | bulk_activate_jobs

    CANDIDATOS (tools/candidates.py):
      search_candidates | search_candidates_hybrid | get_candidate
      create_candidate | update_candidate | get_candidates_stats
      full_candidate_search (pipeline multi-estratégia: 3 buscas paralelas)

    CANDIDATURAS (tools/applies.py):
      search_applies | get_apply_details | create_apply | bulk_create_applies
      update_apply | move_apply_stage | get_apply_history
      get_selective_processes | get_apply_stats | get_stalled_applies
      bulk_approve_applies | bulk_reject_applies | bulk_move_applies
      send_apply_reject_feedback | diagnose_applies

    SOURCING (tools/sourcing.py):
      search_sourcings | start_sourcing | get_sourcing_details
      get_sourcing_stats | find_similar_candidates | get_sourced_profiles
      update_sourced_profile | import_sourced_profile | search_archetypes
      get_multi_sourcing_stats

    AGENDAMENTO (tools/scheduling.py):
      get_calendar_agenda | create_calendar_event | get_available_slots
      generate_self_scheduling_link | search_meetings | create_internal_meeting
      get_interview_sessions | get_events_without_feedback

    AVALIAÇÕES (tools/evaluations.py):
      search_evaluations | get_evaluation | create_evaluation
      list_evaluation_questions | create_evaluation_question
      get_candidates_in_evaluations | send_evaluation

    ORGANIZAÇÃO (tools/organization.py):
      search_departments | get_department_tree | search_teams
      search_lists | create_list | add_to_list | bulk_add_to_list
      get_pending_approvals | approve_request | reject_request
      daily_briefing_complete | get_recruiter_productivity_metrics
      get_notifications | get_unread_notifications_count | get_messages

    MACROS (tools/macros.py):
      diagnose_job_complete | get_full_candidate_profile | get_daily_briefing

    PLANEJAMENTO (tools/planning.py):
      write_plan | read_plan

    FILE SYSTEM (tools/file_system.py):
      save_file | read_file | list_files

    GENÉRICO (tools/generic.py):
      think | discover_api | call_api (fallback) | ask_user | get_instructions

    FORMATAÇÃO (tools/formatting.py):
      [formatação de respostas]

    TOOL SEARCH (tools/tool_search.py):
      [busca de tools disponíveis]
```

**Regras de execução (AUTONOMOUS_SYSTEM_PROMPT):**
- Queries simples (1 tool): vai direto, sem `write_plan`
- Queries com 2+ tools: SEMPRE `write_plan` antes + atualiza após cada tool
- Budget: max 40 chamadas de API por sessão (planning/file system não contam)
- Offloading: resultados >5 itens ou >5K chars → salvos em arquivo virtual automaticamente
- Resolução de contexto: `viewing_entities` → sessão → URL atual → `ask_user`
- `ask_user` apenas para: múltiplos candidatos com mesmo nome, query vaga demais, ou escrita bloqueada

---

### 3.6 Diagrama de delegação e migração de contexto {#p1-diagrama}

#### LIA — Migração por `context_page`

```
                    USUÁRIO ENVIA MENSAGEM
                            │
                     context_page enviado
                            │
            ┌───────────────┼───────────────────┐
            ▼               ▼                   ▼
       "general"    "job"|"jobs"|"vagas"|     "pipeline"|
       "global"     "wizard"                 "kanban"
            │               │                   │
            ▼               ▼                   ▼
        context_type:  context_type:       context_type:
         "general"    "job_management"      "pipeline"
            │               │                   │
            ▼               ▼                   ▼
      recruiter_     job_management.yaml    cv_screening +
      assistant.yaml    (Prompt 2)          pipeline_transition +
      (Prompt 1)                            interview_scheduling +
            │                               communication
            │                               (Prompt 3)
            │
            │    TAMBÉM PODE SER:
            │        "sourcing"|"talent"
            │              │
            ▼              ▼
     Contexto geral   context_type:
     recebe GLOBAL     "talent_funnel"
     tools apenas     sourcing + analytics
                      (Prompt 4)
```

**Gatilhos de migração (sempre controlados pelo frontend):**
- Usuário navega para `/jobs` → frontend seta `context_page: "job"` → Prompt 2 ativado
- Usuário abre uma vaga específica `/jobs/{id}` → frontend seta `context_page: "pipeline"` → Prompt 3 ativado
- Usuário vai para `/candidates` ou `/sourcing/{id}` → frontend seta `context_page: "sourcing"` → Prompt 4 ativado
- Usuário volta para página genérica → frontend seta `context_page: "general"` → Prompt 1 retoma

**Não existe roteamento inteligente no backend LIA**: o contexto é sempre determinado pelo frontend.

#### v5 — Roteamento inteligente pelo HubPlanner

```
         USUÁRIO ENVIA MENSAGEM (hub_mode: true)
                        │
               HubPlanner analisa
                        │
        ┌───────────────┼──────────────────────────┐
        ▼               ▼                          ▼
   FAST_NAV_PATTERNS  ID explícito         Análise LLM do planner
   (regex sem LLM)    na mensagem          (PLANNER_SYSTEM_PROMPT)
        │               │                          │
        ▼               ▼              ┌───────────┼────────────┐
   NavigationAction  Open direto       ▼           ▼            ▼
   (navega a page)   (job ou        jobs        applies    sourced_
                      candidate)   domain       domain     profile_
                                     │           │         sourcing
                                     ▼           ▼         domain
                              "vagas"/"job"  "kanban"/   "candidatos"/
                               queries     "pipeline"    "sourcing"
                                          queries        queries

        MULTI_INTENT_RE detectado?
        → HubExecutionPlan com múltiplas HubTask em paralelo
        → Ex: "estatísticas de vagas E candidatos" → 2 domains em paralelo
```

**Diferença crítica**: o v5 faz roteamento inteligente por LLM (HubPlanner) — o usuário pode perguntar "mostra o kanban da vaga 42" estando em qualquer página e o v5 roteia para o domínio `applies` automaticamente. Na LIA, isso só funciona se o frontend enviar `context_page: "pipeline"`.

---

### 3.7 Comparativo LIA × v5 {#p1-comparativo}

| Dimensão | LIA (recruiter_assistant) | v5 (autonomous) |
|---|---|---|
| **Arquivo principal** | `recruiter_assistant.yaml` | `autonomous/prompts.py` → `AUTONOMOUS_SYSTEM_PROMPT` |
| **Quantidade de tools** | 4 (scope GLOBAL) | 73+ tools em 13 módulos |
| **Roteamento** | Determinístico (frontend define context_page) | Inteligente via HubPlanner (LLM + regex) |
| **Multi-intenção** | ❌ Não suporta nativamente | ✅ `MULTI_INTENT_RE` + HubTask[] paralelo |
| **Visibilidade de execução** | ❌ Sem feedback de progresso | ✅ write_plan com ⬜→🔄→✅ em tempo real |
| **Budget de tools** | ⚠️ Não documentado/controlado | ✅ Max 40 API calls por sessão |
| **Memória cross-session** | ✅ Preferências por conta (sessão e persistente) | ✅ `conversation_memory` no DomainContext |
| **Resolução de contexto implícito** | ❌ Sem `viewing_entities` | ✅ `viewing_entities` → sessão → URL → ask_user |
| **Offloading de resultados grandes** | ❌ Não implementado | ✅ File system virtual (>5K chars) |
| **Navegação programática** | ❌ Apenas descreve onde ir | ✅ `NavigationAction(NAVIGATE, target)` |
| **Streaming SSE** | ⚠️ Via WebSocket | ✅ `/chat/stream` com SSE nativo |
| **Fallback de API** | ❌ Sem fallback genérico | ✅ `call_api` chama qualquer endpoint Rails |
| **Anti-sycophancy** | ✅ `ANTI_SYCOPHANCY_BLOCK` explícito | ✅ Implícito no system prompt |
| **Confirmação de escrita** | ✅ NEGATION_DETECTION_BLOCK | ✅ `ask_user` para escrita bloqueada |

---

## 4. Prompt 2 — Expandido: Tabela de Vagas {#prompt-2}

### O que é e onde aparece

O **Prompt Expandido da Tabela de Vagas** aparece quando o usuário abre o chat enquanto está na página `/user/jobs`. É o prompt especializado para **criar, configurar, editar e gerir vagas**. Quando ativado, a interface expande o painel de chat ao lado da tabela de vagas.

**Contexto carregado:** detalhes de vagas existentes + benchmark salarial de mercado.

**Quando usar:** criar nova vaga, gerar job description, configurar etapas do processo seletivo, editar requisitos, definir critérios de triagem, verificar benchmark salarial, publicar ou encerrar vagas.

**Quando NÃO usar:** buscar candidatos (→ Prompt 4), triar CVs (→ Prompt 3), agendar entrevistas (→ Prompt 3).

---

### 4.1 Capacidades IN {#p2-in}

#### Wizard Conversacional de Criação de Vagas
- **Condução de wizard passo a passo** — coleta título, área, senioridade, requisitos, competências WSI, tipo de contrato, faixa salarial, localidade, modelo de trabalho, etapas do processo seletivo; uma pergunta por vez
- **Validação de campos** — verifica campos obrigatórios e inconsistências antes de salvar
- **Confirmação por seção** — confirma cada bloco antes de avançar
- **Salvamento como rascunho** — persiste o estado do wizard para retomada `[ESCRITA]`
- **Criação final de vaga** — salva a vaga completa no banco `[ESCRITA]`

#### Job Description (JD)
- **Geração de JD enriquecida** — cria descrição profissional a partir dos requisitos coletados, com tom configurável (formal, criativo, técnico)
- **Sugestões de melhoria de JD** — IA aponta lacunas e melhorias na descrição atual
- **Linguagem inclusiva** — LIA garante linguagem neutra de gênero e sem discriminação
- **Estrutura padrão** — seções: Sobre a empresa | Responsabilidades | Requisitos | Benefícios

#### Benchmark Salarial e Competências
- **Benchmark salarial inteligente** — sugere faixa salarial baseada em cargo + senioridade + localidade + mercado
- **Sugestão inteligente de skills** — IA recomenda competências técnicas e comportamentais por cargo e nível
- **Competências WSI por cargo** — sugere quais dos 7 blocos WSI são mais relevantes para o perfil

#### Edição e Gestão de Vagas
- **Busca de vagas** — por título, status, departamento, filtros avançados, com abas: todas | ativas | urgentes | pausadas | arquivadas
- **Detalhes de vaga** — dados completos + candidatos `[ESCRITA]`
- **Atualização de campos** — edita qualquer atributo de vaga existente `[ESCRITA]`
- **Publicação de vaga** — torna vaga visível para candidatos e job boards `[ESCRITA]`
- **Alteração de status** — publicar, pausar, fechar, reabrir, arquivar `[ESCRITA]`
- **Duplicar vaga** — cria cópia com todos os campos `[ESCRITA]`
- **Ações em lote** — arquivar/pausar/ativar múltiplas vagas de uma vez `[LOTE][ESCRITA]`

#### Analytics e Relatórios de Vagas
- **Estatísticas do pipeline** — candidatos por etapa, taxa de conversão, tempo médio
- **Analytics de múltiplas vagas** — comparação agregada em uma chamada (v5: `get_multi_job_analytics`)
- **Saúde do pipeline** — score de saúde, gargalos, candidatos parados por vaga
- **Alertas de vagas** — prazo vencido, urgentes sem finalistas, vagas paradas, sem candidatos
- **Resumo executivo** — combina dados + analytics em relatório estruturado
- **Exportar vaga** — dados em CSV
- **Estatísticas globais** — total de vagas, ativas, pausadas, arquivadas, urgentes (v5: `get_all_jobs_stats`)

#### Matching e Sourcing
- **Candidatos compatíveis** — busca no banco candidatos com alta compatibilidade por embedding similarity (v5: `get_matching_candidates`)
- **Iniciar sourcing automático** — dispara busca de candidatos do banco local e/ou global para a vaga `[ESCRITA]`
- **Adicionar lista a vaga** — adiciona todos os candidatos de uma lista ao processo seletivo da vaga `[LOTE][ESCRITA]`

#### Configuração de Processo Seletivo
- **Configuração de etapas** — define as etapas do funil (ex: Web Response → Triagem → Entrevista → Proposta)
- **Critérios de triagem** — define nota de corte e questões eliminatórias
- **Cutoff dinâmico** — configura saturation e cutoff automático para triagem em lote (LIA: `automation.yaml`)

---

### 4.2 Restrições OUT {#p2-out}

| O que NÃO faz | Por quê | Onde fazer |
|---|---|---|
| Busca ativa de candidatos | Requer contexto de sourcing | Prompt 4 (Funil) |
| Triagem de CVs específicos | Requer contexto de candidatos carregados na vaga | Prompt 3 (Kanban) |
| Agendamento de entrevistas | Requer domínio `interview_scheduling` | Prompt 3 (Kanban) |
| Movimentação de candidatos no pipeline | Requer domínio `pipeline_transition` | Prompt 3 (Kanban) |
| Comunicação com candidatos | Requer domínio `communication` | Prompt 3 (Kanban) |

---

### 4.3 Dados coletados e gerados {#p2-dados}

**Inputs:**
- `context_page: "job"/"jobs"/"vacancies"/"wizard"` — ativa o contexto
- `entity_id` — ID da vaga em foco (se alguma estiver selecionada)
- `job_context` — dados ricos da vaga atual (título, requisitos, pipeline, candidatos)
- Campos coletados no wizard: título, área, senioridade, tipo de contrato, faixa salarial, localidade, modelo de trabalho, skills, competências WSI, etapas do processo

**Outputs:**
- Job Description completa (texto Markdown estruturado)
- Rascunho salvo no banco (`save_job_draft`)
- Vaga criada/publicada no ATS
- Benchmark salarial (min/max por mercado, cargo, localidade)
- Lista de skills sugeridas com justificativa
- Relatórios de pipeline em formato texto + dados para gráficos no frontend

---

### 4.4 Arquitetura técnica — LIA {#p2-lia}

```
Frontend (context_page: "job"|"jobs"|"vacancies"|"wizard")
    ↓
ContextAdapter.from_rest() OU from_job_chat()
    → context_type = "job_management"
    → entity_id = job_id (se disponível)
    → job_context = dados ricos da vaga
    ↓
MainOrchestrator
    → carrega domínio: job_management.yaml
    ↓
Tools disponíveis (scope: JOB_TABLE):
    ├── search_salary_benchmark(job_title, seniority, location, industry)
    ├── validate_job_fields(fields)
    ├── get_job_suggestions(job_title, current_description, industry)
    ├── save_job_draft(fields, draft_id)
    ├── get_intelligent_salary(job_title, seniority, location)
    ├── get_intelligent_skills(job_title, seniority, industry)
    ├── generate_enriched_jd(fields, tone)
    ├── search_jobs(query, status, department, limit)
    ├── get_job_details(job_id, include_candidates)
    ├── get_pipeline_stats(job_id, date_range)
    ├── create_job(title, description, department, location, salary_range, requirements)
    ├── update_job(job_id, fields)
    └── publish_job(job_id, channels[])

Tools compartilhadas (scope: GLOBAL):
    ├── get_company_config(config_type)
    ├── generate_report(report_type, date_from, date_to, format)
    └── schedule_report(report_type, schedule, recipients)

Agentes: orchestrator, job_planner, job_intake, job_wizard
```

**Regras de comportamento (job_management.yaml):**
- Nunca incluir critérios discriminatórios na JD (idade, estado civil, gênero)
- Confirmar título + senioridade + tipo de contrato antes de salvar
- Alertar se requisitos forem excessivamente restritivos (pipeline escasso)
- Sugerir benchmark salarial sempre que disponível
- Formato wizard: uma pergunta por vez, confirmação por seção

---

### 4.5 Arquitetura técnica — v5 {#p2-v5}

```
Frontend (domain: "jobs") OU
HubPlanner detecta query sobre vagas
    ↓
JobsDomain (domain_id: "jobs")
    → domain_name: "Gestao de Vagas"
    → description: "Gestao completa de vagas: listagem, analytics, pipeline, status, matching, sugestoes"
    ↓
JobsPrompts → JobDynamicPromptBuilder
    → PromptConfig(max_actions_in_prompt=8, max_examples_per_action=2)
    → Dois modos:
        • has_job_context=True: prompt enriquecido com detalhes da vaga específica
        • has_job_context=False: prompt genérico para listagem de vagas
    ↓
TieredContextManager (cache por tier):
    • ACTIONS_USING_TIER1: dados básicos (dados+pipeline)
    • ACTIONS_USING_TIER2: dados completos (+analytics +atividade recente)
    ↓
JobsActions (src/domains/jobs/actions/):
    analytics.py:
        ├── job_analytics (funil, taxas de conversão, candidatos por etapa)
        ├── account_stats (estatísticas globais de todas as vagas)
        └── pipeline_health (saúde de múltiplas vagas)
    base.py:
        └── show_job_details (detalhes completos)
    conversational.py:
        └── [interações conversacionais e clarificação]
    matching.py:
        └── matching_candidates (embedding similarity para candidatos)
    mutations.py:
        ├── change_status (publicar/pausar/fechar/reabrir/arquivar)
        ├── copy_job (duplicar vaga)
        ├── bulk_apply_action (ações em lote no pipeline)
        └── export_job (CSV)
    query.py:
        ├── list_jobs (com filtros e abas: active/urgent/paused/archived)
        ├── pipeline_status (kanban visual da vaga)
        ├── alerts (prazo vencido, urgentes, paradas, sem candidatos)
        └── summarize_job (resumo executivo combinando dados+analytics)
    suggestions.py:
        ├── generate_suggestion (IA sugere melhorias para a JD)
        ├── generate_interview_questions (IA gera perguntas por competência)
        └── auto_source (inicia sourcing automático)

_CONTEXT_ACTION_PATTERNS (detecção rápida por regex):
    "pipeline|kanban" → pipeline_status
    "analytics|funil|gargalo" → job_analytics
    "report|relatório|resumo" → summarize_job
    "detalhes|info" → show_job_details
    "alertas" → alerts
    "estatísticas|stats" → account_stats
    "exportar" → export_job
    "auto-source|sourcing automático" → auto_source
    "feedback rejeição" → send_reject_feedback
    "saúde do pipeline" → pipeline_health
```

**Diferenças arquiteturais v5 vs LIA neste contexto:**
- v5 tem **cache tiered**: tier1 (dados básicos, rápido) vs tier2 (completo + analytics, mais pesado) por ação
- v5 tem **detecção rápida por regex** (`_CONTEXT_ACTION_PATTERNS`) antes de chamar o LLM para classificar intenção
- v5 tem `auto_source` que inicia sourcing automático de candidatos para a vaga
- LIA tem **wizard conversacional** mais estruturado (save_job_draft + validate_job_fields + generate_enriched_jd)

---

### 4.6 Comparativo LIA × v5 {#p2-comparativo}

| Dimensão | LIA (job_management) | v5 (jobs domain) |
|---|---|---|
| **Arquivo principal** | `job_management.yaml` | `jobs/domain.py` + `actions/*.py` + `prompts/*.py` |
| **Wizard conversacional** | ✅ Com save_job_draft por seção | ⚠️ Sem wizard estruturado — cria direto via API |
| **JD gerada por IA** | ✅ `generate_enriched_jd` com tom configurável | ✅ `get_job_ai_suggestion` via API |
| **Benchmark salarial** | ✅ `search_salary_benchmark` | ⚠️ Não documentado como tool separada |
| **Skills sugeridas por IA** | ✅ `get_intelligent_skills` | ✅ `get_job_questions` (perguntas de entrevista) |
| **Validação de campos** | ✅ `validate_job_fields` | ⚠️ Sem validação explícita pré-save |
| **Cache tiered** | ❌ Não implementado | ✅ Tier1 vs Tier2 por ação |
| **Detecção de intenção** | Via LLM geral | ✅ Regex rápido + LLM fallback |
| **Sourcing automático** | ⚠️ Delegado ao domínio `sourcing` | ✅ `auto_source` direto no domínio jobs |
| **Analytics multi-vagas** | ✅ `get_pipeline_stats` | ✅ `get_multi_job_analytics` (1 chamada) |
| **Exportação** | ✅ `generate_report(format: csv/pdf/json)` | ✅ `export_job` (CSV) |
| **Ações em lote** | ✅ Via `automation.yaml` | ✅ `bulk_archive/pause/activate_jobs` |
| **Perguntas de entrevista** | ❌ Não implementado no domínio | ✅ `generate_interview_questions` por vaga |
| **Diagnóstico completo** | ❌ Não implementado | ✅ `diagnose_job_complete` (macro) |

---

## 5. Prompt 3 — Expandido: Dentro da Vaga (Kanban) {#prompt-3}

### O que é e onde aparece

O **Prompt Expandido Dentro da Vaga** aparece quando o usuário está na tela de uma vaga específica (`/user/jobs/{id}`), visualizando o kanban de candidatos ou a tabela de candidaturas. É o prompt mais operacional: age diretamente sobre candidatos de **uma vaga específica**.

**Contexto carregado:** dados da vaga + lista de candidatos + pipeline com etapas.

**Quando usar:** triar CVs, mover candidatos no pipeline, agendar entrevistas, conduzir entrevistas WSI, enviar comunicações, ver funil da vaga, análise de candidaturas, ações em lote sobre candidatos.

**Quando NÃO usar:** criar nova vaga (→ Prompt 2), buscar candidatos no pool externo (→ Prompt 4).

---

### 5.1 Capacidades IN {#p3-in}

#### Triagem Curricular e Score WSI
- **Triagem automática de CV** — analisa currículo contra rubrica da vaga com critérios objetivos
- **Cálculo de score WSI** — 7 blocos de avaliação:
  1. Hard Skills Técnicas — competências específicas do cargo
  2. Soft Skills / Comportamentais — evidências comportamentais via CBI
  3. Experiência Profissional — anos, empresas, setor, progressão
  4. Liderança — evidências de gestão de pessoas, projetos, equipes
  5. Comunicação — clareza, persuasão, escrita, oratória
  6. Alinhamento Cultural — fit com valores e cultura da empresa
  7. Potencial — capacidade de crescimento e aprendizado
- **Recomendação automática:** Avançar (≥75%) | Revisão (60-74%) | Rejeitar (<60%)
- **Detecção de red flags** — gaps de emprego, job hopping, inconsistências de datas, contradições no CV
- **Triagem em lote** — múltiplos candidatos avaliados em paralelo com ranking
- **Verificação de elegibilidade** — questões eliminatórias verificadas antes de qualquer avaliação
- **FairnessGuard** — verifica viés involuntário antes de qualquer rejeição; ignora: nome, foto, localização, estado civil, idade, etnia

#### Pipeline e Movimentação de Candidatos
- **Ver kanban da vaga** — visualiza etapas com candidatos em cada uma
- **Mover candidato para etapa** — com confirmação obrigatória `[ESCRITA]`
- **Aprovação de candidato** — avança para próxima etapa `[ESCRITA]`
- **Rejeição de candidato** — com motivo e opção de notificar `[ESCRITA]`
- **Mover candidatos em lote** — toda uma etapa de uma vez `[LOTE][ESCRITA]`
- **Aprovar em massa** — move toda uma etapa para próxima `[LOTE][ESCRITA]`
- **Rejeitar em massa** — rejeita toda uma etapa `[LOTE][ESCRITA]`
- **Ocultar candidato** — remove da visualização ativa (soft remove) `[ESCRITA]`
- **Funil de conversão** — candidatos em cada etapa + taxa de conversão
- **Distribuição por etapa** — percentual e barra visual por etapa
- **Candidatos parados** — detecta por severidade: attention (7d) / warning (14d) / critical (30d+)

#### Entrevistas (Agendamento e Condução WSI)
- **Agendar entrevista** — verifica disponibilidade em calendários e propõe horários
- **Reagendar / cancelar entrevista** `[ESCRITA]`
- **Confirmação automática** — envia detalhes para candidato e entrevistador
- **Auto-agendamento** — gera link para candidato escolher horário `[ESCRITA]`
- **Condução de entrevista WSI** — perguntas comportamentais estruturadas (CBI), uma por vez
- **Triagem inicial por voz/texto** — ligação ou WhatsApp
- **Transcrição e análise de áudio** — com consentimento explícito do candidato
- **Detecção de respostas evasivas** — identifica inconsistências durante a entrevista
- **Análise pós-entrevista** — competências avaliadas + evidências coletadas + score parcial
- **Entrevistas sem feedback** — lista eventos passados sem feedback para follow-up

#### Avaliação Formal (Testes e Questionários)
- **Listar avaliações da vaga** — testes disponíveis, status (pending/completed/expired), score
- **Enviar avaliação para candidato** `[ESCRITA]`
- **Ver resultados de avaliação** — score e respostas

#### Análise e Ranking de Candidatos
- **Buscar candidatos na vaga** — por nome, etapa, score, status, data
- **Detalhes completos** — perfil, score WSI, experiências, skills, avaliações, histórico
- **Filtrar por score** — candidatos com score acima de X
- **Top N candidatos** — ranking dos melhores por compatibilidade
- **Comparar candidatos** — análise lado a lado de múltiplos perfis
- **Timeline da candidatura** — histórico de eventos: mudanças de etapa, avaliações, entrevistas
- **Ranking global da vaga** — todos os candidatos ordenados por compatibilidade
- **Analytics de candidaturas** — analytics completo: funil, taxas, tempo médio por etapa
- **Diagnóstico de candidaturas** — diagnóstico completo com recomendações de IA

#### Comunicação com Candidatos (domínio `communication`)
- **Enviar email individual** — com preview e confirmação `[ESCRITA]`
- **Enviar email em massa** — para grupo de candidatos (>10: confirmação obrigatória) `[LOTE][ESCRITA]`
- **Mensagem WhatsApp** — via Meta API + Twilio `[ESCRITA]`
- **Notificação Teams** — para stakeholders internos `[ESCRITA]`
- **Templates de mensagem** — criação e aplicação de templates por vaga e etapa
- **Feedback de rejeição** — mensagem respeitosa, padronizada e sem dados protegidos `[ESCRITA]`
- **Convite de entrevista** — com dados de calendário e link de acesso `[ESCRITA]`
- **Histórico de comunicações** — log completo por candidato
- **Relatório de entrega** — confirmação de envio em massa com quantidade de destinatários

---

### 5.2 Restrições OUT {#p3-out}

| O que NÃO faz | Por quê | Onde fazer |
|---|---|---|
| Buscar candidatos no pool externo | Requer domínio `sourcing` | Prompt 4 (Funil) |
| Criar ou editar vaga | Requer domínio `job_management` | Prompt 2 (Tabela de Vagas) |
| Briefing geral do dia / overview cross-vagas | Contexto limitado a uma vaga | Prompt 1 (Flutuante) |
| Decisão final de contratação | Requer validação humana obrigatória | Recrutador |

---

### 5.3 Dados coletados e gerados {#p3-dados}

**Inputs:**
- `context_page: "pipeline"/"kanban"` — ativa o contexto
- `entity_id` — job_id da vaga aberta
- `job_context` — dados da vaga (título, requisitos, etapas, competências WSI)
- `candidates` — lista de candidatos carregados na tela
- `selected_candidate_ids` — candidatos selecionados pelo recrutador para ação em lote

**Outputs:**
- Score WSI (0-100) por candidato com justificativa para cada bloco
- Recomendação de avanço, revisão ou rejeição
- Ranking de candidatos por compatibilidade
- Relatório de análise pós-entrevista (competências + evidências + score parcial)
- Transcrição de áudio (com consentimento)
- Templates de comunicação gerados por IA
- Log de auditoria de todas as avaliações e movimentações (compliance LGPD/SOX)

---

### 5.4 Arquitetura técnica — LIA {#p3-lia}

```
Frontend (context_page: "pipeline" | "kanban")
    ↓
ContextAdapter
    → context_type = "pipeline"
    → entity_id = job_id
    → candidates = lista de candidatos da tela
    → selected_candidate_ids = selecionados pelo usuário
    ↓
MainOrchestrator
    → carrega MÚLTIPLOS domínios em paralelo:
        ├── cv_screening.yaml        ← triagem e score WSI
        ├── pipeline_transition.yaml ← movimentação no funil
        ├── interview_scheduling.yaml ← agendamento e condução WSI
        └── communication.yaml       ← comunicações multi-canal
    ↓
Tools disponíveis (scope: IN_JOB):
    ├── update_candidate_stage(candidate_id, target_stage, job_id, notes, notify_candidate)
    ├── reject_candidate(candidate_id, vacancy_id, reason, notify)
    ├── bulk_update_candidates_stage(candidate_ids[], target_stage, job_id)
    ├── wsi_screening(candidate_id, job_id, screening_type: voice|text|video)
    ├── hide_candidate(candidate_id, vacancy_id, reason)
    └── get_vacancy_funnel(job_id, include_rejected)

Agentes: orchestrator, recruiter_assistant, screening, analyst_feedback, communication
```

**Arquitetura multi-domínio:** A LIA usa múltiplos YAMLs para este contexto, cada um com seu system prompt especializado. O orquestrador decide qual domínio está mais adequado para cada intenção detectada.

**Regras de comportamento críticas:**
- `cv_screening.yaml`: NUNCA avalia por nome, foto, localização, estado civil, idade, etnia
- `cv_screening.yaml`: Sempre consulta FairnessGuard antes de rejeitar
- `interview_scheduling.yaml`: Perguntas APENAS sobre competências profissionais (nunca família, filhos, estado civil)
- `communication.yaml`: Todo email gerado inclui rodapé "Mensagem gerada com assistência de IA pela LIA (WeDOTalent)"
- `pipeline_transition.yaml`: Confirma ações destrutivas ou irreversíveis antes de executar

---

### 5.5 Arquitetura técnica — v5 {#p3-v5}

```
Frontend (domain: "applies") OU
HubPlanner detecta query sobre candidaturas/kanban
    ↓
AppliesDomain (domain_id: "applies")
    → domain_name: "Gestao de Candidaturas"
    → description: "Gestao completa de candidaturas: busca, detalhes, pipeline/kanban,
       aprovacao/reprovacao, ranking, comparacao, analytics, acoes em lote.
       Opera no contexto de uma vaga (job_id)."
    ↓
AppliesPrompts → AppliesDynamicPromptBuilder
    → PromptConfig(max_actions_in_prompt=8, max_examples_per_action=2)
    → Dois modos:
        • has_job_context=True: inclui job_id no prompt
        • has_job_context=False: modo genérico
    ↓
AppliesActions (src/domains/applies/actions/):
    analytics.py:
        ├── apply_analytics (analytics completo da vaga)
        └── stage_distribution (distribuição por etapa com barra visual)
    base.py:
        └── [ações base compartilhadas]
    bulk.py:
        ├── bulk_approve_applies (massa → próxima etapa)
        ├── bulk_reject_applies (massa → rejeição)
        ├── bulk_move_applies (massa → etapa específica, async)
        └── send_apply_reject_feedback (feedback de rejeição em lote)
    comparison.py:
        └── compare_candidates (comparação lado a lado com IA)
    conversational.py:
        └── [clarificação e interação conversacional]
    details.py:
        ├── show_apply_details (perfil completo + score + experiências + avaliações)
        └── apply_timeline (histórico completo de eventos)
    pipeline.py:
        ├── get_kanban (pipeline visual com candidatos por etapa)
        ├── move_stage (mover candidato com confirmação)
        ├── approve_apply (aprovar com confirmação)
        └── reject_apply (rejeitar com confirmação)
    scoring.py:
        ├── filter_by_score (filtra acima de threshold)
        ├── top_candidates (top N por compatibilidade)
        └── full_ranking (ranking completo da vaga)
    search.py:
        ├── search_applies (busca com filtros: nome, etapa, score, status, data)
        ├── search_by_name (busca por nome do candidato)
        ├── list_applies_by_stage (candidatos de uma etapa específica)
        ├── recent_applies (mais recentes)
        └── count_applies (total com filtros)
    sourcing.py:
        ├── stalled_applies (candidatos parados por severidade: attention/warning/critical)
        └── diagnose_applies (diagnóstico completo com recomendações IA)
```

**Diferença v5 vs LIA neste contexto:**
- v5 usa **um domínio unificado** (`applies`) em vez de 4 domínios separados (LIA)
- v5 não tem entrevista WSI como capacidade separada — ela fica no `autonomous` (chat global)
- v5 não tem `communication` como subdomínio — comunicações ficam no `autonomous`
- v5 tem `diagnose_applies` — diagnóstico automatizado com recomendações de IA
- v5 tem `stalled_applies` com classificação por severidade (attention/warning/critical com SLAs)
- v5 tem `bulk_move_applies` assíncrono para operações pesadas

---

### 5.6 Comparativo LIA × v5 {#p3-comparativo}

| Dimensão | LIA (pipeline context) | v5 (applies domain) |
|---|---|---|
| **Arquivos principais** | `cv_screening.yaml` + `pipeline_transition.yaml` + `interview_scheduling.yaml` + `communication.yaml` | `applies/domain.py` + `actions/*.py` |
| **Arquitetura** | Multi-domínio (4 YAMLs simultâneos) | Domínio único unificado |
| **Score WSI (7 blocos)** | ✅ Com FairnessGuard explícito | ⚠️ Score gerado via API (não explicitamente documentado como WSI) |
| **FairnessGuard** | ✅ Verificado antes de toda rejeição | ⚠️ Implícito nas regras do autonomous |
| **Entrevista WSI (CBI)** | ✅ Domínio dedicado com perguntas estruturadas | ⚠️ Via autonomous (sem domínio dedicado) |
| **Triagem por voz** | ✅ `wsi_screening(type: voice)` | ✅ Via `get_interview_sessions` |
| **Transcrição de áudio** | ✅ Com consentimento explícito | ⚠️ Não documentado como feature explícita |
| **Ações em lote** | ✅ `bulk_update_candidates_stage` | ✅ `bulk_approve/reject/move_applies` (async) |
| **Diagnóstico completo** | ❌ Não implementado no domínio | ✅ `diagnose_applies` com recomendações IA |
| **Candidatos parados** | ⚠️ Via analytics global | ✅ `stalled_applies` por severidade (SLA) |
| **Comunicação multi-canal** | ✅ Email + WhatsApp + Teams (domínio próprio) | ✅ Via autonomous (`send_apply_reject_feedback`) |
| **Templates de mensagem** | ✅ Criação e gestão de templates | ⚠️ Feedback padronizado mas sem gestão de templates |
| **Histórico de comunicações** | ✅ Log completo por candidato | ✅ `apply_timeline` + `get_apply_history` |
| **LGPD/SOX audit log** | ✅ Registrado para cada avaliação | ✅ Via `apply_timeline` |
| **Comparação de candidatos** | ✅ Tabela comparativa | ✅ `compare_candidates` com análise IA |
| **Self-scheduling para candidato** | ✅ Link gerado via `interview_scheduling` | ✅ `generate_self_scheduling_link` |

---

## 6. Prompt 4 — Expandido: Funil de Talentos {#prompt-4}

### O que é e onde aparece

O **Prompt Expandido do Funil de Talentos** aparece na tela de candidatos (`/user/candidates`) ou na sessão de sourcing (`/user/sourcing/{id}/chat`). É o prompt especializado em **busca e análise de candidatos** no banco de talentos — tanto candidatos internos do ATS quanto perfis externos buscados via Pearch AI.

**Contexto carregado:** lista de candidatos do resultado de busca + dados da sessão de sourcing (`sourcing_id`) + vaga-alvo (se houver).

**Quando usar:** buscar candidatos no banco interno, buscar perfis externos (Pearch AI), construir queries booleanas, analisar compatibilidade, gerar relatórios do pool, exportar candidatos, adicionar candidatos a vagas ou listas.

**Quando NÃO usar:** criar vaga (→ Prompt 2), triar CVs de candidatos já em uma vaga (→ Prompt 3), tarefas do dia / briefing (→ Prompt 1).

---

### 6.1 Capacidades IN {#p4-in}

#### Busca de Candidatos

##### Banco Interno LIA
- **Busca full-text** — por nome, skill, cargo, empresa anterior, localidade
- **Busca híbrida** — Elasticsearch (70%) + embeddings semânticos (30%) para maior precisão
- **Busca multi-estratégia** — pipeline com 3 buscas paralelas integradas (v5: `full_candidate_search`)
- **Filtros avançados** — experiência, formação, idiomas, modelo de trabalho, faixa salarial, disponibilidade
- **Candidatos favoritos** — `/user/candidates?tab=favoritos`
- **Arquetipos** — templates de perfil ideal cadastrados no sistema para busca padronizada

##### Banco Externo via Pearch AI
- **Busca com 190M+ perfis globais** — integração Pearch AI com query semântica
- **Refinamento de query** — ajuste iterativo de critérios até resultado satisfatório
- **Candidatos similares** — busca por embedding similarity a partir de um perfil existente

##### Busca Booleana
- **Construção de queries** — ex: `Java AND AWS AND (senior OR pleno) NOT júnior`
- **Refinamento guiado** — LIA sugere ajustes quando resultado < 5 ou > 50 candidatos
- **Busca de archaetipos** — localiza templates de perfil ideal no sistema

#### Análise e Scoring de Candidatos
- **Score de compatibilidade** — 0-100% com justificativa por candidato para a vaga alvo
- **Score médio do pool** — com mediana, faixa min-max, quantidade acima de 80, acima de 90
- **Top N candidatos** — ranking dos melhores por score de compatibilidade
- **Distribuição de scores** — histograma e percentis
- **Candidatos para descartar** — identifica perfis claramente fora do critério
- **Candidatos que precisam de triagem** — identifica perfis na zona de dúvida
- **Ranking por prioridade** — ordenação por urgência + fit + disponibilidade
- **Melhores por experiência** — top candidatos por anos e qualidade de experiência

#### Análise Demográfica e de Diversidade
- **Distribuição por gênero** — percentuais com nota de privacidade
- **Distribuição de idiomas** — nível por idioma (fluente, intermediário, básico)
- **Distribuição de formação** — universidades, cursos, nível (graduação, pós, mestrado, doutorado)
- **Distribuição geográfica** — por cidade, estado, região
- **Distribuição por modelo de trabalho** — remoto, híbrido, presencial
- **Análise de diversidade** — Four-Fifths Rule por dimensão (gênero, idade, PCD, região)
- **Bias audit** — verificação de equidade na seleção por múltiplas dimensões

#### Análise Técnica do Pool
- **Skills mais comuns** — frequência e profundidade por skill
- **Lacunas de skills** — skills requisitadas pela vaga que o pool não cobre
- **Análise de skills** — distribuição e profundidade de competências técnicas
- **Experiência média** — anos de experiência médio do pool
- **Experiência com empresa destaque** — candidatos de empresas específicas

#### Relatórios e Analytics
- **Resumo executivo do sourcing** — visão completa: distribuição demográfica, scores, localização, skills, contatos, diversidade, formação
- **Relatório de top candidatos** — detalhado dos melhores perfis com análise IA
- **Análise de melhoria de busca** — identifica por que o pool está fraco e sugere como melhorar
- **Comparação de sourcings** — compara múltiplos sourcings em uma chamada (v5: `get_multi_sourcing_stats`)
- **Exportação de candidatos** — CSV/XLSX com campos selecionáveis

#### Ações sobre Candidatos do Pool
- **Adicionar candidato a vaga** — vincula candidato ao processo seletivo de uma vaga `[ESCRITA]`
- **Shortlist** — adiciona candidato à lista de pré-selecionados para uma vaga `[ESCRITA]`
- **Adicionar a lista** — inclui candidato em lista nomeada de talentos `[ESCRITA]`
- **Criar lista** — cria nova lista de candidatos com nome inferido do contexto `[ESCRITA]`
- **Bulk add to list** — adiciona múltiplos candidatos de uma vez (async) `[LOTE][ESCRITA]`
- **Aprovar perfil sourced** — marca como aprovado no sourcing `[ESCRITA]`
- **Rejeitar perfil sourced** — exclui do pool de consideração `[ESCRITA]`
- **Importar como candidato** — converte perfil sourced em candidato formal no ATS `[ESCRITA]`
- **Adicionar rating/nota** — avalia e anota perfil sourced `[ESCRITA]`

#### Comunicação (via TALENT_FUNNEL)
- **Enviar email** — para um ou múltiplos candidatos do pool `[ESCRITA]`
- **Enviar WhatsApp** — para candidato com template configurável `[ESCRITA]`

#### Sourcing Analytics
- **Estatísticas do sourcing** — total de perfis, taxa de aprovação, ROI, distribuição de scores
- **Import stats** — candidatos importados com e sem apply
- **Histórico de buscas** — sourcings anteriores realizados

---

### 6.2 Restrições OUT {#p4-out}

| O que NÃO faz | Por quê | Onde fazer |
|---|---|---|
| Triagem detalhada de CV com score WSI | Requer contexto de candidatos na vaga | Prompt 3 (Kanban) |
| Agendamento de entrevistas | Requer domínio `interview_scheduling` | Prompt 3 (Kanban) |
| Movimentação no pipeline de uma vaga | Requer domínio `pipeline_transition` | Prompt 3 (Kanban) |
| Criação de vagas | Requer domínio `job_management` | Prompt 2 (Tabela de Vagas) |
| Briefing geral / agenda do dia | Contexto focado no pool de talentos | Prompt 1 (Flutuante) |

---

### 6.3 Dados coletados e gerados {#p4-dados}

**Inputs:**
- `context_page: "sourcing"/"talent"` — ativa o contexto
- `entity_id` = `sourcing_id` — ID da sessão de sourcing ativa
- `entity_type: "sourcing"` — tipo da entidade em foco
- `candidates` — lista de candidatos do resultado de busca atual (carregada na tela)
- `selected_candidate_ids` — candidatos selecionados pelo recrutador
- `search_context` — configurações da busca (query, filtros aplicados)
- `target_job` — vaga-alvo para cálculo de score de compatibilidade

**Outputs:**
- Lista de candidatos com score de compatibilidade e justificativa
- Relatório executivo de sourcing (Markdown estruturado)
- Análise de diversidade com métricas Four-Fifths Rule
- Dados para gráficos: distribuições demográficas, de skills, de scores
- Lista de candidatos exportada (CSV/XLSX)
- Candidatos adicionados a vaga / lista / shortlist
- Sugestões de refinamento de busca quando pool < 5 ou > 50

---

### 6.4 Arquitetura técnica — LIA {#p4-lia}

```
Frontend (context_page: "sourcing" | "talent")
    ↓
ContextAdapter.from_talent_chat() OU from_rest()
    → context_type = "talent_funnel"
    → entity_id = sourcing_id
    → entity_type = "sourcing"
    → candidates = candidatos da tela
    → search_context = configuração da busca
    → target_job = vaga alvo (se existir)
    ↓
MainOrchestrator
    → carrega domínios:
        ├── sourcing.yaml   ← busca e análise de talentos
        └── analytics.yaml  ← KPIs, relatórios, bias audit
    ↓
Tools disponíveis (scope: TALENT_FUNNEL):
    ├── search_candidates(query, filters, limit, offset)
    ├── get_candidate_details(candidate_id, include_history)
    ├── get_candidate_stats(filters, group_by)
    ├── add_candidate_to_vacancy(candidate_id, vacancy_id, stage, notes)
    ├── shortlist_candidate(candidate_id, vacancy_id, notes)
    ├── add_to_list(candidate_id, list_name, notes)
    ├── export_candidates(candidate_ids[], format: csv|xlsx, fields[])
    ├── send_email(to[], subject, body, template_id)
    └── send_whatsapp(phone, message, template_name)

Tools compartilhadas (scope: GLOBAL):
    ├── generate_report(report_type, date_from, date_to, format)
    └── schedule_report(report_type, schedule, recipients)

Agentes: orchestrator, recruiter_assistant, sourcing, analytics
```

**Regras de comportamento (sourcing.yaml):**
- Score de compatibilidade sempre apresentado com justificativa
- Nunca inferir gênero, etnia, idade a partir de nome ou localização
- Se < 5 resultados: propõe automaticamente critérios menos restritivos
- Se > 50 resultados: pergunta se deseja filtro adicional
- Sempre cita a fonte: banco interno vs. Pearch vs. externo

**Regras de comportamento (analytics.yaml):**
- Dados sempre agregados (LGPD-safe) — sem identificação individual em relatórios
- Destaca anomalias com contexto + recomendação de ação
- Quando amostra < 30 registros: indica baixa confiabilidade estatística
- Compara com benchmark setorial quando disponível

---

### 6.5 Arquitetura técnica — v5 {#p4-v5}

```
Frontend (domain: "sourced_profile_sourcing") OU
HubPlanner detecta query sobre candidatos/sourcing
    ↓
SourcedProfileSourcingDomain (domain_id: "sourced_profile_sourcing")
    → domain_name: "Análise de Perfis em Sourcing"
    → description: "Análise e ações sobre perfis de candidatos vinculados a um sourcing específico.
       Sempre requer sourcing_id no contexto."
    ↓
SourcedProfileSourcingPrompts → DynamicPromptBuilder
    → USE_DYNAMIC_BUILDER = env var (padrão: true)
    → PromptConfig(max_actions_in_prompt=6, max_examples_per_action=2, enable_cache=True)
    → Modo dinâmico: injeta total_candidates + aggregated_stats no prompt
    ↓
StatsManager — pré-computa e cacheia estatísticas agregadas:
    ACTIONS_USING_AGGREGATED = frozenset({
        count_candidates, count_by_filter, average_score, score_distribution,
        list_candidates, average_experience, average_salary_expectation,
        language_distribution, education_distribution, gender_distribution,
        work_model_distribution, diversity_analysis, location_distribution,
        analyze_skills, generate_executive_report, generate_top_candidates_report,
        summarize_search, analyze_search_improvement, score_above, common_strengths,
        skill_gaps, candidates_to_discard, needs_screening, priority_ranking,
        work_model_specific, top_by_experience
    })
    ↓
SourcedProfileSourcingActions (src/domains/sourced_profile_sourcing/actions/):
    analysis.py:
        ├── common_strengths (pontos fortes comuns do pool)
        ├── skill_gaps (lacunas de skills do pool vs. vaga)
        └── diversity_analysis (Four-Fifths Rule por dimensão)
    comparison.py:
        └── compare_candidates (comparação lado a lado com IA)
    conversational.py:
        └── [clarificação e interação]
    count.py:
        ├── count_candidates (total)
        └── count_by_filter (total por filtro)
    details.py:
        └── show_candidate_details (detalhes + análise IA + experiências + skills)
    distribution.py:
        ├── language_distribution (nível por idioma)
        ├── education_distribution (universidades, cursos, nível)
        ├── gender_distribution (percentuais por gênero)
        ├── location_distribution (por cidade, estado, região)
        └── work_model_distribution (remoto/híbrido/presencial)
    feedback.py:
        ├── approve_candidate (aprovar no sourcing)
        ├── reject_candidate (rejeitar do pool)
        └── add_rating (rating + nota)
    insights.py:
        ├── analyze_skills (distribuição e profundidade de skills)
        ├── top_by_experience (top por anos/qualidade)
        └── work_model_specific (candidatos por modelo de trabalho)
    report.py:
        ├── generate_executive_report (com planejamento + coleta + análise + formatação)
        ├── generate_top_candidates_report (detalhado dos melhores)
        └── summarize_search (resumo geral com todas as dimensões)
    score.py:
        ├── average_score (média + mediana + faixa + acima de 80/90)
        ├── score_distribution (histograma)
        ├── score_above (candidatos acima de threshold)
        ├── top_candidates (top N por score)
        └── priority_ranking (urgência + fit + disponibilidade)
    search.py:
        ├── search_candidates (busca por termo, skill, critério)
        ├── filter_by_skill (skill específica)
        ├── filter_by_score (acima de mínimo)
        ├── list_candidates (todos, com paginação)
        └── recent_candidates (mais recentes)
    search_improvement.py:
        └── analyze_search_improvement (por que pool está fraco + como melhorar)
```

**SLA de relatório (`report.py`):**
O `generate_executive_report` usa pipeline de 4 etapas com timer:
1. `report_planning` — define estrutura e métricas a coletar
2. `report_data_collection` — coleta dados da API
3. `report_analysis` — análise IA dos dados coletados
4. `report_formatting` — formata relatório final com dados de gráficos

---

### 6.6 Comparativo LIA × v5 {#p4-comparativo}

| Dimensão | LIA (talent_funnel) | v5 (sourced_profile_sourcing) |
|---|---|---|
| **Arquivos principais** | `sourcing.yaml` + `analytics.yaml` | `sourced_profile_sourcing/domain.py` + `actions/*.py` |
| **Busca no banco interno** | ✅ `search_candidates` | ✅ `search_candidates` + `filter_by_skill` + `filter_by_score` |
| **Busca híbrida (ES + embeddings)** | ⚠️ Não documentada como separada | ✅ `search_candidates_hybrid` (70% ES + 30% embeddings) |
| **Pearch AI (190M+ perfis)** | ✅ Documentado no system prompt | ⚠️ Não documentado como tool explícita no domínio |
| **Queries booleanas** | ✅ Documentado no system prompt | ⚠️ Suportado via busca mas sem tool dedicada |
| **Candidatos similares** | ✅ `find_similar_candidates` | ✅ Via scoring por embedding |
| **Score de compatibilidade** | ✅ 0-100% com justificativa | ✅ Score calculado pela API + distribuição |
| **Análise demográfica** | ✅ Via `analytics.yaml` | ✅ `distribution/*.py` (5 dimensões) |
| **Bias audit (Four-Fifths Rule)** | ✅ Documentado no analytics.yaml | ✅ `diversity_analysis` + `gender_distribution` |
| **Relatório executivo** | ✅ Via `generate_report` (GLOBAL) | ✅ `generate_executive_report` (4-step pipeline) |
| **Cache de stats agregadas** | ❌ Não implementado | ✅ `StatsManager` + `ACTIONS_USING_AGGREGATED` |
| **Análise de melhoria de busca** | ⚠️ Sugerida no system prompt | ✅ `analyze_search_improvement` (ação dedicada) |
| **Adicionar candidato a vaga** | ✅ `add_candidate_to_vacancy` | ✅ `create_apply` via autonomous |
| **Shortlist** | ✅ `shortlist_candidate` | ✅ Via `add_to_list` + `create_list` |
| **Exportação de candidatos** | ✅ `export_candidates(csv/xlsx)` | ✅ Via autonomous tools |
| **Arquetipos de busca** | ❌ Não implementado | ✅ `search_archetypes` |
| **Comparação de sourcings** | ❌ Um por vez | ✅ `get_multi_sourcing_stats` (bulk) |
| **LLM para relatório** | ✅ Gemini/Claude via GLOBAL tools | ✅ `create_tracked_llm` (temperature=0.3) |

---

## 7. Tabela-resumo global: 4 prompts × 10 dimensões {#tabela-resumo}

| Dimensão | Prompt 1 — Flutuante | Prompt 2 — Tabela Vagas | Prompt 3 — Kanban | Prompt 4 — Funil Talentos |
|---|---|---|---|---|
| **Contexto de ativação** | Todas as páginas | `/user/jobs` | `/user/jobs/{id}` | `/user/candidates`, `/user/sourcing/{id}` |
| **context_page (LIA)** | `general` | `job`, `jobs`, `vacancies`, `wizard` | `pipeline`, `kanban` | `sourcing`, `talent` |
| **domain payload (v5)** | `null` + hub_mode | `"jobs"` | `"applies"` | `"sourced_profile_sourcing"` |
| **Domínios LIA** | `recruiter_assistant` | `job_management` | `cv_screening` + `pipeline_transition` + `interview_scheduling` + `communication` | `sourcing` + `analytics` |
| **Domínio v5** | `autonomous` | `jobs` | `applies` | `sourced_profile_sourcing` |
| **N° de tools LIA** | 4 (GLOBAL) | 13 (JOB_TABLE) | 6 (IN_JOB) | 9 (TALENT_FUNNEL) |
| **N° de tools v5** | 73+ (13 módulos) | 7 action files | 10 action files | 14 action files |
| **Escrita de dados** | ✅ Com confirmação | ✅ Com confirmação | ✅ Com confirmação | ✅ Com confirmação |
| **Operações em lote** | ✅ v5 | ✅ v5 | ✅ Ambos | ✅ Ambos |
| **Score WSI / IA** | ❌ | ⚠️ Sugestão de skills | ✅ Score WSI 7 blocos | ✅ Score de compatibilidade |
| **Bias audit / Fairness** | ⚠️ Via analytics global | ✅ LIA usa linguagem inclusiva | ✅ FairnessGuard antes de rejeitar | ✅ Four-Fifths Rule |
| **Entrevista WSI (CBI)** | ❌ | ❌ | ✅ LIA | ❌ |
| **Comunicação multi-canal** | ✅ v5 | ❌ | ✅ Ambos | ✅ Ambos |
| **Relatórios exportáveis** | ✅ Ambos | ✅ Ambos | ⚠️ LIA via global | ✅ Ambos |
| **Streaming em tempo real** | ✅ v5 (SSE) | ✅ v5 | ✅ v5 | ✅ v5 |
| **Progressão visível (write_plan)** | ✅ v5 apenas | ✅ v5 | ✅ v5 | ✅ v5 |
| **Cache otimizado** | ❌ LIA | ✅ v5 (Tier1/Tier2) | ✅ v5 (AppliesCacheManager) | ✅ v5 (StatsManager) |
| **LGPD compliance** | ✅ Ambos | ✅ Ambos | ✅ Ambos (audit log) | ✅ Ambos (dados agregados) |

---

## 8. Glossário técnico {#glossario}

| Termo | Definição |
|---|---|
| **context_page** | Campo enviado pelo frontend junto com a mensagem indicando qual página o usuário está. Determina qual prompt/domínio será ativado na LIA. |
| **context_type** | Tipo normalizado de contexto, mapeado a partir do `context_page` pelo `ContextAdapter`. Ex: `"job"` → `"job_management"`. |
| **domain payload** | Campo `domain` no payload da API do v5 (`POST /chat`). Determina qual domínio v5 processar a requisição. |
| **hub_mode** | Flag do v5 (`hub_mode: true`) que ativa o HubPlanner para roteamento inteligente baseado em LLM + regex. |
| **HubPlanner** | Componente v5 responsável por analisar a query e criar um `HubExecutionPlan` — decide qual(is) domínio(s) usar, em paralelo ou sequencial. |
| **HubExecutionPlan** | Plano de execução do v5 contendo: lista de `HubTask[]`, `TaskStrategy` (sequential/parallel), `NavigationAction[]` e `reasoning`. |
| **DomainContext** | Objeto de contexto compartilhado no v5: contém `workspace_id`, `sourcing_id`, `selected_ids`, `conversation_memory`, `auth_token`, `api_calls_history`. |
| **DomainAction** | Ação definida em cada domínio v5 com: `id`, `name`, `description`, `ActionType`, `examples[]`, `requires_confirmation`. |
| **ActionType** | Enum v5 que classifica ações: `QUERY` (consulta), `AGGREGATE` (agrega), `ANALYZE` (analisa com IA), `ACTION` (modifica dados). |
| **GLOBAL scope** | Escopo de tools da LIA disponíveis em todos os contextos de prompt. |
| **JOB_TABLE scope** | Escopo de tools da LIA disponíveis apenas no contexto de tabela de vagas. |
| **IN_JOB scope** | Escopo de tools da LIA disponíveis apenas dentro de uma vaga específica (kanban). |
| **TALENT_FUNNEL scope** | Escopo de tools da LIA disponíveis no contexto de funil de talentos/sourcing. |
| **WSI** | Workforce Screening Interview — sistema de avaliação em 7 blocos: Hard Skills, Soft Skills, Experiência, Liderança, Comunicação, Alinhamento Cultural, Potencial. |
| **FairnessGuard** | Camada de verificação de viés involuntário da LIA executada antes de qualquer rejeição. Impede discriminação por nome, foto, localização, estado civil, idade, etnia. |
| **Four-Fifths Rule** | Regra de equidade estatística: se taxa de aprovação de um grupo for menor que 80% da taxa do grupo mais aprovado, existe evidência de disparidade sistemática. |
| **Pearch AI** | Plataforma de sourcing externo integrada à LIA, com acesso a 190M+ perfis globais. |
| **write_plan** | Tool do v5 autonomous que cria/atualiza um plano de execução visível ao usuário em tempo real (⬜ pendente → 🔄 em andamento → ✅ concluído). |
| **StatsManager** | Componente v5 que pré-computa e cacheia estatísticas agregadas do sourcing para ações que dependem de dados do pool inteiro. |
| **TieredContextManager** | Componente v5 do domínio `jobs` com cache em dois níveis: Tier1 (dados básicos, rápido) e Tier2 (dados completos + analytics, mais pesado). |
| **IDOR** | Insecure Direct Object Reference — tipo de vulnerabilidade que permite acessar dados de outras empresas via IDs. Prevenido pelo `ContextAdapter.validate_entity_ownership()` na LIA. |
| **CBI** | Competency-Based Interview — metodologia de entrevista estruturada por competências e evidências comportamentais. Usada nas entrevistas WSI. |
| **MULTI_INTENT_RE** | Regex do v5 que detecta queries com múltiplas intenções distintas, gerando `HubTask[]` executados em paralelo. |
| **viewing_entities** | Campo do v5 enviado pelo frontend indicando quais entidades o usuário está vendo na tela atual (ex: `{job_id: 42, candidate_id: 123}`). Permite resolução de referências implícitas. |
| **NavigationAction** | Ação de navegação do v5 que instrui o frontend a navegar para uma URL específica sem recarregar (ex: `NAVIGATE → /user/jobs/42`). |
| **DomainCatalog** | Classe v5 que centraliza: mapeamento de domínios disponíveis (`DomainRegistry`), rotas de navegação do frontend (`NAVIGATION_ROUTES`) e catálogo legível por LLM. |
| **UniversalContext** | Objeto de contexto normalizado da LIA que o `MainOrchestrator` consome — abstraindo REST, WebSocket e RabbitMQ. |
| **RabbitMQ** | Protocolo de mensageria assíncrono suportado pela LIA via `ContextAdapter.from_rabbitmq()` — compatível com o formato de payload do v5. |
| **SSE** | Server-Sent Events — protocolo de streaming unidirecional servidor→cliente. O v5 expõe `/chat/stream` com SSE nativo para progresso em tempo real. |
| **SLA** | Service Level Agreement — prazo acordado para execução de uma etapa. Candidatos parados além do SLA são sinalizados com severidade: attention (7d) / warning (14d) / critical (30d+). |

---

*Documento gerado a partir da leitura do código `lia-agent-system/` (local) e `WeDOTalent/recruiter_agent_v5` (GitHub) em Março/2026.*
*Para atualizar: reler `context_adapter.py`, `tool_registry_metadata.yaml`, YAMLs de domínios, e os `domain.py` + `actions/*.py` do v5.*
