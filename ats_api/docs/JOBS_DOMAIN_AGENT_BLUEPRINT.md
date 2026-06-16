# Blueprint: Domain Agent para Vagas (Jobs) — v2

## Decisoes de Design

### Licoes do Sourcing

O dominio `sourced_profile_sourcing` tem 33 actions e ja sofre com classificacao errada de intent (doc `ANALISE_SOURCED_PROFILE_SOURCING.md`). Cada action a mais e mais um ponto de confusao pro LLM no `process_intent`. O design deste dominio aplica as licoes aprendidas:

1. **Actions consolidadas (~22)** — abaixo do threshold de 25 que funciona no sourcing
2. **Parametros no lugar de actions separadas** — `distribution(by: "status")` ao inves de 7 actions separadas
3. **Escopo claro por action** — sem sobreposicao semantica entre `job_stats` e `job_analytics`
4. **Write actions com confirmacao rigida** — contagem exata antes de executar
5. **Fairness guard** — obrigatorio em matching e pipeline (implicacao legal)
6. **Conversation memory desde o dia 1** — Rails persiste e reenvia, evitando o gap do sourcing
7. **Context tiered** — carrega o essencial sempre, pesado sob demanda

---

## Arquitetura

```
Rails ATS API (envia domain="jobs" + context_data)
    │
    ▼
MessageRouter.route()
    ├─ domain: "jobs"  → DomainOrchestrator.process_query()
    │
    ▼
DomainOrchestrator
    ├─ DomainRegistry.get_instance("jobs") → JobsDomain
    ├─ Monta DomainContext (job_id, user_id, account_id, auth_token)
    ├─ Carrega context_for_ai TIER 1 (job + pipeline_summary)
    │
    ▼
DomainWorkflow.process() — LangGraph 3 nodes
    │
    ├─ Node 1: DomainIntentAgent
    │     → domain.process_intent(query, context)
    │     → LLM → {action_id, params, confidence}
    │
    ├─ Node 2: DomainExecutorAgent
    │     → domain.execute_action(action_id, params, context, stats)
    │     → Se action precisa TIER 2, carrega sob demanda
    │     → FairnessGuard.check() em actions sensiveis
    │     → HTTP request a API Rails
    │
    └─ Node 3: DomainResponseBuilder
          → Formata resposta via TemplateFormatter
    │
    ▼
DomainOrchestrator cria mensagem via API (POST /v1/users/messages)
    ▼
Resposta aparece no workspace do usuario
```

---

## Modelo de Dados: Job

### Campos Principais (tabela `jobs`)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `id` | bigint | ID unico |
| `title` | string | Titulo da vaga |
| `description` | text | Descricao completa |
| `user_id` | bigint | Recrutador responsavel |
| `account_id` | bigint | Conta (tenant) |
| `company_id` | bigint | Empresa da vaga |
| `job_status_id` | bigint | Status atual (FK → job_statuses) |
| `published_date` | datetime | Data de publicacao |
| `application_deadline` | datetime | Prazo para candidaturas |
| `is_remote` | boolean | Se e remoto |
| `city`, `state`, `country` | string | Localizacao |
| `workplace_type` | string | 1=Remoto, 2=Hibrido, 3=Presencial |
| `seniority` | integer | Enum: 0=Junior, 1=Pleno, 2=Senior, 3=Especialista, 4=Estagio, 5=Lead, 6=Gerente, 7=Diretor |
| `employment_type` | integer | Enum: 0=CLT, 1=PJ, 2=Estagio, 3=Temporario, 4=Freelancer, 5=Aprendiz |
| `priority` | integer | Enum: 1=Alta, 2=Media, 3=Baixa |
| `urgency_level` | integer | Enum: 1=Baixa, 2=Moderada, 3=Media, 4=Alta, 5=Critica |
| `is_active` | boolean | Se esta ativa |
| `is_archived` | boolean | Se esta arquivada |
| `is_deleted` | boolean | Soft delete |
| `is_urgent` | boolean | Flag de urgencia |
| `reason_for_pause` | string | Motivo de pausa |
| `department_id` | bigint | Departamento |
| `team_id` | bigint | Time |
| `hiring_manager_id` | bigint | Gestor da vaga |
| `workflow_template_id` | bigint | Template de workflow |
| `screening_deadline` | date | Prazo para triagem |
| `shortlist_deadline` | date | Prazo para shortlist |
| `closing_deadline` | date | Prazo para fechamento |
| `disabilities` | boolean | Vaga PCD |
| `main_pcd_category` | integer | Categoria PCD principal |
| `confidential_type` | integer | 1=Publica, 2=Interna, 3=Confidencial |
| `sector`, `segment`, `target_audience` | string | Classificacao |
| `is_screening_active` | boolean | Se triagem automatica esta ativa |
| `minimum_screening_score` | float | Score minimo para aprovacao |
| `has_automatic_interview` | boolean | Se entrevista automatica esta habilitada |
| `interview_minimum_score` | float | Score minimo para entrevista |
| `responsibilities` | string[] | Lista de responsabilidades |
| `missing_fields` | jsonb | Campos obrigatorios nao preenchidos |
| `field_requirements` | jsonb | Template de campos obrigatorios |

### Relacionamentos

| Relacionamento | Tipo | Tabela | Descricao |
|----------------|------|--------|-----------|
| `selective_processes` | has_many | `selective_processes` | Etapas do processo seletivo (Kanban) |
| `applies` | has_many | `applies` | Candidaturas a vaga |
| `evaluations` | has_many | `evaluations` | Avaliacoes da vaga |
| `skills` | has_many :through | `skill_relationships` → `skills` | Skills exigidas |
| `benefits` | has_many :through | `benefit_relationships` → `benefits` | Beneficios oferecidos |
| `remunerations` | has_many :through | `remuneration_relationships` → `remunerations` | Remuneracao (salario, comissao, bonus) |
| `languages` | has_many :through | `language_relationships` → `languages` | Idiomas exigidos |
| `behavioral_skills` | has_many :through | `behavioral_skill_relationships` | Skills comportamentais |
| `user` | belongs_to | `users` | Recrutador responsavel |
| `company` | belongs_to | `companies` | Empresa |
| `job_status` | belongs_to | `job_statuses` | Status (Rascunho, Ativa, etc.) |
| `department` | belongs_to | `departments` | Departamento |
| `team` | belongs_to | `teams` | Time |
| `hiring_manager` | belongs_to | `users` | Gestor da contratacao |
| `job_journeys` | has_many | `job_journeys` | Jornada da vaga (checklist) |
| `embedding_record` | has_one | `embeddings` | Embedding para matching |
| `analytics_snapshot` | has_one | `job_analytics_snapshots` | Cache de analytics |
| `dispatches` | has_many | `dispatches` | Envios (email, WhatsApp, etc.) |
| `candidate_feedbacks` | has_many | `candidate_feedbacks` | Feedbacks de candidatos |

### Maquina de Estados (job_statuses)

```
Rascunho → Ativa | Aguardando aprovacao
Aguardando aprovacao → Aprovada | Rascunho
Aprovada → Ativa | Rascunho
Ativa → Paralisada | Fechada (preenchida) | Fechada (expirada) | Cancelada | Concluida
Paralisada → Ativa | Reaberta | Cancelada
Reaberta → Ativa | Paralisada | Cancelada
Interna → Ativa | Paralisada | Cancelada
Fechada (preenchida) → Reaberta | Arquivada
Fechada (expirada) → Reaberta | Arquivada
Cancelada → Reaberta | Arquivada
Concluida → Reaberta | Arquivada
Arquivada → Reaberta
```

---

## APIs Rails Disponiveis

### 1. CRUD de Vagas

| Metodo | Endpoint | Descricao | Params Principais |
|--------|----------|-----------|-------------------|
| GET | `/v1/users/jobs` | Lista vagas (busca, filtros, paginacao) | `term`, `page`, `per_page`, `compact`, filtros ES |
| GET | `/v1/users/jobs/:id` | Detalhes de uma vaga | `includes` (selective_processes, skills, benefits, remunerations, languages) |
| POST | `/v1/users/jobs` | Cria vaga | `job[title, description, ...]`, `skills[]`, `benefits[]` |
| PUT | `/v1/users/jobs/:id` | Atualiza vaga | Mesmos params do create |
| DELETE | `/v1/users/jobs/:id` | Remove vaga (soft delete) | — |

### 2. Acoes sobre Vagas

| Metodo | Endpoint | Descricao | Params |
|--------|----------|-----------|--------|
| POST | `/v1/users/jobs/:id/change_status` | Muda status | `job_status_id`, `reason` |
| POST | `/v1/users/jobs/:id/publish` | Publica vaga | — (valida campos obrigatorios) |
| POST | `/v1/users/jobs/:id/unpublish` | Despublica | — |
| POST | `/v1/users/jobs/:id/copy` | Duplica vaga | `job[user_id, entities[]]` |
| GET | `/v1/users/jobs/:id/export` | Exporta dados | `format` (csv/pdf) |

### 3. Analytics e Estatisticas

| Metodo | Endpoint | Descricao | Params |
|--------|----------|-----------|--------|
| GET | `/v1/users/jobs/stats` | Estatisticas da conta (global) | `start_date`, `end_date` |
| GET | `/v1/users/jobs/:id/analytics` | Analytics de uma vaga especifica | `force_refresh` |

**Stats retorna:** `by_status`, `open_vs_closed`, `avg_days_to_close`, `created_per_week`, `by_department`, `by_priority`, `by_urgency`, `by_workplace_type`, `top_hiring_managers`, `totals`

**Analytics retorna:** `overview`, `funnel`, `velocity`, `quality`, `sources`, `engagement`, `scheduling`, `team_activity`

### 4. Matching Semantico

| Metodo | Endpoint | Descricao | Params |
|--------|----------|-----------|--------|
| GET | `/v1/users/jobs/matches/candidates` | Candidatos compativeis via embedding | `job_id`, `top_k`, `page`, `per_page`, `min_score`, `max_score`, `filters{}` |

### 5. Sugestoes com IA

| Metodo | Endpoint | Descricao | Params |
|--------|----------|-----------|--------|
| POST | `/v1/users/jobs/:job_id/suggestion` | Gera sugestoes de titulo/descricao/skills | `suggestion[type, job[...]]` |
| POST | `/v1/users/jobs/:id/suggestion/questions` | Gera perguntas de avaliacao | `type`, `evaluation_id`, `query` |
| POST | `/v1/users/jobs/boolean_search` | Gera busca booleana (Google/LinkedIn) | `job_id` |

### 6. Kanban (Pipeline)

| Metodo | Endpoint | Descricao | Params |
|--------|----------|-----------|--------|
| GET | `/v1/users/jobs/:job_id/kanban` | Dados do Kanban | `selective_process_id`, `term`, `page` |
| POST | `/v1/users/jobs/:id/applies/approve_collection` | Aprova em lote | `select_all_params` |
| POST | `/v1/users/jobs/:id/applies/reject_collection` | Rejeita em lote | `select_all_params` |

### 7. Estrutura Organizacional e Jornada

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/v1/users/jobs/:id/organizational_structure` | Estrutura organizacional |
| GET | `/v1/users/job_journeys?job_id=X` | Jornada da vaga (checklist) |

---

## Actions Consolidadas (22 actions)

### Principio: menos actions = melhor classificacao do LLM

O sourcing tem 33 actions e erros de classificacao documentados. Consolidamos para 22 usando parametros ao inves de actions separadas.

### Consolidacoes aplicadas

| Antes (v1 — 40+ actions) | Depois (v2 — 22 actions) | Racional |
|---------------------------|--------------------------|----------|
| `distribution_by_status`, `distribution_by_department`, `distribution_by_workplace`, `distribution_by_priority`, `distribution_by_urgency`, `top_hiring_managers`, `open_vs_closed` | `distribution(by: "status\|department\|workplace\|priority\|urgency\|hiring_manager\|open_closed")` | Mesmo endpoint `/stats`, mesmo formato de resposta. O param `by` resolve |
| `funnel_analysis`, `velocity_metrics`, `quality_metrics`, `engagement_metrics`, `scheduling_metrics`, `team_activity`, `source_analysis` | `job_analytics(section: "funnel\|velocity\|quality\|engagement\|scheduling\|team\|sources\|all")` | Tudo vem de `/analytics`. Param `section` filtra ou retorna tudo |
| `pause_job`, `archive_job`, `activate_job`, `publish_job`, `unpublish_job` | `change_status(target: "Paralisada\|Arquivada\|Ativa\|publish\|unpublish")` | Um unico handler resolve status. `publish`/`unpublish` sao cases especiais dentro do mesmo fluxo |
| `approve_applies`, `reject_applies` | `bulk_apply_action(action: "approve\|reject")` | Mesma logica com guard de confirmacao |
| `list_jobs`, `search_jobs` | `list_jobs(term: "python")` | `term` presente = search, ausente = list |
| `job_stats` + `avg_time_to_close` + `weekly_trend` + `count_jobs` | `account_stats(metric: "all\|time_to_close\|trend\|totals")` | Tudo vem de `/stats`. Um handler, param seleciona |

### Tabela Final de Actions (22)

| # | action_id | Tipo | Descricao | Params | API |
|---|-----------|------|-----------|--------|-----|
| 1 | `show_job_details` | QUERY | Detalhes da vaga atual | — | `GET /jobs/:id` |
| 2 | `list_jobs` | QUERY | Lista/busca vagas da conta | `term`, `filters` | `GET /jobs` |
| 3 | `pipeline_status` | QUERY | Status do Kanban com contagens | `stage_filter` | `GET /jobs/:id/kanban` |
| 4 | `matching_candidates` | QUERY | Candidatos compativeis via embedding | `top_k`, `min_score` | `GET /jobs/matches/candidates` |
| 5 | `missing_fields` | QUERY | Campos faltantes para publicacao | — | `GET /jobs/:id` (missing_fields) |
| 6 | `job_journeys` | QUERY | Checklist da jornada da vaga | — | `GET /job_journeys?job_id=X` |
| 7 | `organizational_structure` | QUERY | Estrutura do time e gestor | — | `GET /jobs/:id/organizational_structure` |
| 8 | `account_stats` | AGGREGATE | Estatisticas globais da conta | `metric`, `start_date`, `end_date` | `GET /jobs/stats` |
| 9 | `distribution` | AGGREGATE | Distribuicao por dimensao | `by` | `GET /jobs/stats` |
| 10 | `job_analytics` | ANALYZE | Analytics da vaga (funil, velocidade, etc.) | `section` | `GET /jobs/:id/analytics` |
| 11 | `change_status` | ACTION | Muda status / publica / despublica / arquiva / pausa / ativa | `target`, `reason` | `POST /jobs/:id/change_status` ou `publish`/`unpublish` |
| 12 | `copy_job` | ACTION | Duplica a vaga | — | `POST /jobs/:id/copy` |
| 13 | `generate_suggestion` | ACTION | Gera descricao/titulo/skills via IA | `type` | `POST /jobs/:id/suggestion` |
| 14 | `generate_questions` | ACTION | Gera perguntas de avaliacao | `type`, `query` | `POST /jobs/:id/suggestion/questions` |
| 15 | `generate_boolean_search` | ACTION | Gera string booleana para sourcing | — | `POST /jobs/boolean_search` |
| 16 | `bulk_apply_action` | ACTION | Aprova/rejeita candidaturas em lote | `action`, `stage_filter` | `POST /jobs/:id/applies/approve\|reject_collection` |
| 17 | `export_job` | ACTION | Exporta dados da vaga | `format` | `GET /jobs/:id/export` |
| 18 | `conversational_response` | CONV | Resposta generica (saudacao, agradecimento) | — | — |
| 19 | `help` | CONV | Lista capacidades do agent | — | — |
| 20 | `summarize_job` | ANALYZE | Resumo executivo da vaga (LLM) | — | TIER 1 context |
| 21 | `compare_with_market` | ANALYZE | Compara vaga com benchmark | — | TIER 1 + LLM |
| 22 | `readiness_check` | QUERY | Checa se vaga esta pronta (campos + status + timeline) | — | TIER 1 context |

---

## Desambiguacao: account_stats vs job_analytics

Este e o ponto mais critico de classificacao. "Estatisticas dessa vaga" vs "Estatisticas das vagas" — uma palavra de diferenca.

### Regra no System Prompt

```
REGRA CRITICA — STATS vs ANALYTICS:

Se a query contem QUALQUER referencia a vaga especifica ("dessa vaga", "essa vaga",
"da vaga X", "nessa posicao", "dessa posicao"), use → job_analytics

Se a query fala de TODAS as vagas / da empresa / da conta / do time / geral
("nossas vagas", "todas as vagas", "da empresa", "geral", "dashboard"),
use → account_stats

Se a query fala de DISTRIBUICAO ou AGRUPAMENTO
("por status", "por departamento", "quantas de cada"), use → distribution

Exemplos resolvidos:
- "Estatisticas dessa vaga" → job_analytics (section: "all")
- "Estatisticas das vagas" → account_stats (metric: "all")
- "Como esta o funil?" → job_analytics (section: "funnel")
- "Quantas vagas ativas?" → account_stats (metric: "totals")
- "Vagas por departamento" → distribution (by: "department")
- "Quanto tempo pra fechar?" → account_stats (metric: "time_to_close")
- "De onde vem os candidatos?" → job_analytics (section: "sources")
```

### Triggers Calibrados

```python
INTENT_TRIGGERS = {
    "account_stats": {
        "keywords": ["estatisticas gerais", "nossas vagas", "todas as vagas",
                      "quantas vagas", "dashboard", "da empresa", "da conta",
                      "visao geral das vagas", "overview das vagas"],
        "negative": ["dessa vaga", "essa vaga", "nessa vaga", "da vaga"]
    },
    "job_analytics": {
        "keywords": ["dessa vaga", "essa vaga", "nessa vaga", "funil",
                      "pipeline", "gargalo", "velocidade", "qualidade",
                      "entrevistas", "time da vaga", "fontes", "engajamento",
                      "como esta essa", "analytics"],
        "requires_job_id": True
    },
    "distribution": {
        "keywords": ["por status", "por departamento", "por prioridade",
                      "por urgencia", "por modelo de trabalho", "quantas de cada",
                      "distribuicao", "agrupadas", "abertas vs fechadas",
                      "quem tem mais vagas"]
    }
}
```

---

## Context Tiered (Carregamento por Tiers)

O `context_for_ai` do sourcing carrega tudo de uma vez, incluindo aggregated_stats que pode ser pesado. Para jobs, carregamento em tiers:

### TIER 1 — Sempre carregado (low-cost, essencial)

Carregado na entrada do DomainOrchestrator para TODA query.

```
GET /v1/users/jobs/:id/context_for_ai?tier=1

{
  job: {
    id, title, description, city, state, country,
    workplace_type_text, seniority_text, employment_type_text,
    priority_text, urgency_level_text,
    is_active, is_archived, is_urgent,
    published_date, application_deadline, closing_deadline,
    job_status_name, job_status_color,
    user_name, company_name, department_name,
    hiring_manager_name,
    skills: [...], benefits: [...], languages: [...],
    salary_from, salary_to, salary_currency,
    responsibilities: [...],
    missing_fields_count, completeness_percentage,
    is_ready_for_publication
  },
  pipeline_summary: {
    total_participants,
    stages: [
      { name, position, status, count, percentage, color }
    ]
  }
}
```

**Custo:** 1 query SQL com JOINs + 1 query de selective_processes. Rapido.

### TIER 2 — Sob demanda (carregado pelo action handler)

Carregado APENAS quando a action precisa. O handler chama `api_client.get_job_analytics()` ou `api_client.get_job_stats()` diretamente.

```python
TIER_2_ACTIONS = frozenset({
    "job_analytics",
    "account_stats",
    "distribution",
    "matching_candidates",
    "bulk_apply_action",
})
```

```python
@require_job_id
def job_analytics(self, params, context, tier1_stats=None):
    section = params.get("section", "all")
    analytics = self.get_api_client(context).get_job_analytics(
        context.metadata["job_id"],
        section=section
    )
    # formata e retorna
```

### TIER 3 — Raramente usado (chamadas individuais)

```python
TIER_3_ACTIONS = frozenset({
    "matching_candidates",
    "export_job",
    "generate_suggestion",
    "generate_questions",
})
```

Estas actions fazem chamadas especificas que podem ser lentas (embedding search, LLM generation) e nunca sao pre-carregadas.

### Beneficio

- TIER 1 custa ~50ms → toda query tem contexto basico instantaneo
- Somente ~30% das queries precisam de TIER 2 (analytics/stats pesados)
- TIER 3 e sob demanda explicito, nunca pre-carregado

---

## Fairness Guard

### Por que e critico em vagas

No contexto de vagas, filtrar candidatos por genero, idade, PCD, raca tem implicacao legal direta (LGPD, EEO, legislacao trabalhista). O sourcing ja tem `fairness.py` — vagas precisa ser mais rigido.

### Actions que passam pelo FairnessGuard

```python
FAIRNESS_GUARDED_ACTIONS = frozenset({
    "matching_candidates",
    "pipeline_status",
    "bulk_apply_action",
    "job_analytics",     # section: "quality" pode expor dados sensiveis
    "summarize_job",
})
```

### Implementacao

```python
class JobFairnessGuard:

    BLOCKED_FILTERS = frozenset({
        "gender", "genero", "sexo",
        "age", "idade", "birth_date", "data_nascimento",
        "race", "raca", "ethnicity", "etnia",
        "religion", "religiao",
        "marital", "estado_civil",
    })

    PCD_CONTEXT_REQUIRED = frozenset({
        "pcd", "disability", "deficiencia",
    })

    DISCLAIMER_MATCHING = (
        "⚠️ Este ranking e baseado em fit tecnico (skills, experiencia, embedding). "
        "Fatores como fit cultural, potencial de crescimento e diversidade "
        "devem ser considerados na decisao final."
    )

    DISCLAIMER_BULK_ACTION = (
        "⚠️ Acoes em lote afetam multiplos candidatos. "
        "Certifique-se de que os criterios nao discriminam por atributos protegidos."
    )

    @classmethod
    def check_params(cls, params: dict) -> tuple[bool, str | None]:
        for key, value in params.items():
            if key.lower() in cls.BLOCKED_FILTERS and value is not None:
                return False, (
                    f"❌ Filtro por '{key}' bloqueado. "
                    f"Filtrar candidatos por {key} pode violar legislacao trabalhista (LGPD/EEO). "
                    f"Consulte seu departamento juridico."
                )
            if key.lower() in cls.PCD_CONTEXT_REQUIRED and value is not None:
                if not params.get("_pcd_job_context"):
                    return False, (
                        f"⚠️ Filtro por '{key}' requer que a vaga seja marcada como PCD. "
                        f"Verifique se a vaga tem 'disabilities: true' antes de filtrar por PCD."
                    )
        return True, None

    @classmethod
    def add_matching_disclaimer(cls, message: str) -> str:
        return f"{message}\n\n---\n{cls.DISCLAIMER_MATCHING}"

    @classmethod
    def add_bulk_disclaimer(cls, message: str) -> str:
        return f"{message}\n\n---\n{cls.DISCLAIMER_BULK_ACTION}"

    @classmethod
    def anonymize_for_llm(cls, candidates: list[dict]) -> tuple[list[dict], dict[str, str]]:
        safe_fields = {
            "id", "score", "cv_match", "total_experience_years",
            "skills", "city", "current_position", "education_level"
        }
        anonymized = []
        id_mapping = {}
        for i, c in enumerate(candidates, 1):
            code = f"C{i:03d}"
            anon = {"candidate_code": code}
            if cid := c.get("id"):
                id_mapping[code] = str(cid)
            for field in safe_fields:
                if field in c:
                    anon[field] = c[field]
            anonymized.append(anon)
        return anonymized, id_mapping
```

### Integracao nos action handlers

```python
@require_job_id
def matching_candidates(self, params, context, tier1_stats=None):
    allowed, reason = JobFairnessGuard.check_params(params)
    if not allowed:
        return DomainResponse(success=False, message=reason, error="fairness_blocked")

    results = self.get_api_client(context).get_matching_candidates(...)

    message = self._format_matching_results(results)
    message = JobFairnessGuard.add_matching_disclaimer(message)

    return DomainResponse(success=True, message=message, data=results)
```

---

## Conversation Memory

### Problema conhecido do sourcing

O sourcing tem suporte a `ConversationMemory` no Python (restaura via `from_dict()`), mas o Rails NAO popula nem persiste o campo `conversation_memory` no `context_data`. Resultado: "essa vaga aqui", "exatamente isso", "desses" — o agent nao sabe a que se refere.

### Solucao para Jobs (implementar desde o dia 1)

#### Rails: persistir e reenviar

```ruby
class Workspace < ApplicationRecord
  # campo jsonb: conversation_memory (ja existe no schema)

  def update_conversation_memory(memory_dict)
    update_column(:conversation_memory, memory_dict)
  end

  def get_conversation_context
    {
      conversation_memory: conversation_memory || {},
      recent_messages: messages
        .where(is_deleted: false)
        .order(created_at: :desc)
        .limit(5)
        .map { |m| { role: m.entity == 0 ? "assistant" : "user", content: m.content } }
        .reverse
    }
  end
end
```

Quando o agent retorna a resposta, o metadata inclui `conversation_memory` atualizado:

```ruby
# No controller que recebe a resposta do agent:
if metadata["conversation_memory"].present?
  workspace.update_conversation_memory(metadata["conversation_memory"])
end
```

Na proxima mensagem do usuario, o Rails envia:

```json
{
  "domain": "jobs",
  "user_query": "E os top 5?",
  "context_data": {
    "job_id": 456,
    "conversation_memory": {
      "last_action": "pipeline_status",
      "last_job_detailed": 456,
      "mentioned_stages": {"Triagem": 30, "Entrevista": 12},
      "active_filters": {}
    },
    "recent_messages": [
      {"role": "user", "content": "Como esta o pipeline?"},
      {"role": "assistant", "content": "📊 Pipeline: Triagem 30, Entrevista 12..."}
    ]
  }
}
```

#### Python: JobConversationMemory

```python
@dataclass
class JobConversationMemory:
    last_action: str | None = None
    last_job_detailed: int | None = None
    last_analytics_section: str | None = None
    mentioned_stages: dict[str, int] = field(default_factory=dict)
    mentioned_candidates: dict[str, int] = field(default_factory=dict)
    active_filters: dict[str, Any] = field(default_factory=dict)
    last_interaction: datetime | None = None

    def resolve_reference(self, query: str, context: DomainContext) -> dict:
        if any(w in query.lower() for w in ["essa vaga", "essa posicao", "nessa vaga"]):
            return {"job_id": context.metadata.get("job_id")}
        if any(w in query.lower() for w in ["desses", "deles", "esses"]):
            return {"continuation": True, "keep_filters": True}
        return {}

    def to_dict(self) -> dict: ...

    @classmethod
    def from_dict(cls, data: dict) -> "JobConversationMemory": ...
```

---

## Write Actions: Confirmacao Rigida

### Problema

"Aprove todos" pode afetar 200 candidatos. `needs_confirmation=True` generico nao e suficiente.

### Protocolo de confirmacao

```python
WRITE_ACTION_CONFIRMATION = {
    "change_status": {
        "message_template": (
            "⚠️ Tem certeza que deseja alterar o status da vaga "
            "**{job_title}** de **{current_status}** para **{target_status}**?"
        ),
        "requires_counts": False
    },
    "bulk_apply_action": {
        "message_template": (
            "⚠️ **Acao em lote**: Tem certeza que deseja **{action}** "
            "**{count} candidato(s)** da etapa **{stage}** da vaga **{job_title}**?\n\n"
            "Esta acao NAO pode ser desfeita."
        ),
        "requires_counts": True,
        "fairness_disclaimer": True
    },
    "copy_job": {
        "message_template": "Deseja duplicar a vaga **{job_title}**?",
        "requires_counts": False
    },
}
```

### Fluxo

```
1. Usuario: "Rejeite todos os candidatos da triagem"
2. Agent detecta: bulk_apply_action(action="reject", stage_filter="Triagem")
3. Handler consulta pipeline: 47 candidatos na etapa Triagem
4. Handler retorna:
   DomainResponse(
       success=True,
       needs_confirmation=True,
       message="⚠️ Tem certeza que deseja REJEITAR 47 candidato(s) da etapa Triagem da vaga Dev Python?\n\nEsta acao NAO pode ser desfeita.\n\n---\n⚠️ Acoes em lote afetam multiplos candidatos...",
       metadata={
           "pending_action": "bulk_apply_action",
           "pending_params": {"action": "reject", "stage_filter": "Triagem", "count": 47}
       }
   )
5. Usuario: "Sim, pode rejeitar"
6. ConversationMemory detecta pending_action → executa sem re-perguntar
```

---

## Estrutura de Arquivos

```
recruiter_agent_v5/src/domains/jobs/
├── __init__.py
├── domain.py                 # JobsDomain (@register_domain, 22 actions)
├── api_client.py             # JobsAPIClient (HTTP client para Rails API)
├── cache.py                  # TieredContextManager (TIER 1 cache, TIER 2 sob demanda)
├── fairness.py               # JobFairnessGuard
├── memory.py                 # JobConversationMemory
├── prompts.py                # System prompt + ACTIONS_USING_TIER1
├── prompt_builder/
│   ├── __init__.py
│   ├── actions.py            # 22 actions com triggers e exemplos
│   └── dynamic_builder.py    # Geracao dinamica de prompts
├── actions/
│   ├── __init__.py           # JobsActions (composicao)
│   ├── base.py               # BaseJobAction + require_job_id + require_confirmation
│   ├── query.py              # show_job_details, list_jobs, pipeline_status, missing_fields, job_journeys, org_structure, readiness_check
│   ├── analytics.py          # job_analytics(section), account_stats(metric), distribution(by), summarize_job, compare_with_market
│   ├── matching.py           # matching_candidates (com FairnessGuard)
│   ├── mutations.py          # change_status, copy_job, bulk_apply_action, export_job (com confirmacao)
│   ├── suggestions.py        # generate_suggestion, generate_questions, generate_boolean_search
│   └── conversational.py     # conversational_response, help
├── template_formatter.py     # Formatacao de respostas em markdown
├── dispatcher.py             # Consumer RabbitMQ
└── tasks.py                  # Celery tasks
```

### Composicao (DRY — sem heranca multipla)

A v1 usava heranca multipla (mixin) como o sourcing. Problema: 12 classes base herdadas = debug dificil, MRO imprevisivel.

```python
class JobsActions:
    def __init__(self):
        self._query = QueryActions()
        self._analytics = AnalyticsActions()
        self._matching = MatchingActions()
        self._mutations = MutationActions()
        self._suggestions = SuggestionActions()
        self._conversational = ConversationalActions()

    def __getattr__(self, name):
        for group in (self._query, self._analytics, self._matching,
                      self._mutations, self._suggestions, self._conversational):
            if hasattr(group, name):
                return getattr(group, name)
        raise AttributeError(f"Action '{name}' not found")
```

Cada grupo herda apenas de `BaseJobAction`. Sem diamond inheritance, sem MRO surprises.

---

## Mapeamento action_id → handler (domain.py)

```python
ACTION_HANDLERS = {
    "show_job_details":        self._actions.show_job_details,
    "list_jobs":               self._actions.list_jobs,
    "pipeline_status":         self._actions.pipeline_status,
    "missing_fields":          self._actions.missing_fields,
    "job_journeys":            self._actions.job_journeys,
    "organizational_structure":self._actions.organizational_structure,
    "readiness_check":         self._actions.readiness_check,

    "account_stats":           self._actions.account_stats,
    "distribution":            self._actions.distribution,
    "job_analytics":           self._actions.job_analytics,
    "summarize_job":           self._actions.summarize_job,
    "compare_with_market":     self._actions.compare_with_market,

    "matching_candidates":     self._actions.matching_candidates,

    "change_status":           self._actions.change_status,
    "copy_job":                self._actions.copy_job,
    "bulk_apply_action":       self._actions.bulk_apply_action,
    "export_job":              self._actions.export_job,

    "generate_suggestion":     self._actions.generate_suggestion,
    "generate_questions":      self._actions.generate_questions,
    "generate_boolean_search": self._actions.generate_boolean_search,

    "conversational_response": self._actions.conversational_response,
    "help":                    self._actions.help,
}
```

22 handlers. Cada um com responsabilidade unica. O LLM escolhe entre 22 opcoes ao inves de 40+.

---

## Actions que usam TIER 1 (cache do context_for_ai)

Essas actions resolvem com dados ja carregados, sem chamada extra:

```python
ACTIONS_USING_TIER1 = frozenset({
    "show_job_details",
    "pipeline_status",
    "missing_fields",
    "readiness_check",
    "summarize_job",
    "conversational_response",
    "help",
})
```

---

## Context Data Esperado do Rails

```json
{
  "domain": "jobs",
  "user_query": "Como esta o pipeline dessa vaga?",
  "context_data": {
    "user_id": 42,
    "account_id": 1,
    "workspace_id": 123,
    "job_id": 456,
    "auth_token": "Bearer xxx",
    "conversation_memory": {
      "last_action": "show_job_details",
      "last_job_detailed": 456,
      "active_filters": {}
    },
    "recent_messages": [
      {"role": "user", "content": "Detalhes dessa vaga"},
      {"role": "assistant", "content": "📋 Vaga: Dev Python Senior..."}
    ]
  }
}
```

### Workspace Integration

- `domain: "job"` + `domain_reference_id: <job_id>` → workspace da vaga
- `Workspace.find_or_create_for_domain(user:, account:, domain: "job", domain_reference_id: job.id)`
- Canal ActionCable: `domain_messages_user_{user_id}_job_{job_id}`

---

## System Prompt — Core Rules

```
Voce e Lia, assistente de recrutamento, operando no contexto de VAGAS.

CORE_RULES:

1. CONTEXTO: O usuario esta em um workspace vinculado a uma VAGA (job_id={job_id}).
   "Essa vaga", "essa posicao", "nessa vaga" = vaga atual.
   NUNCA peca clarificacao sobre qual vaga.

2. STATS vs ANALYTICS (CRITICO):
   - "dessa/essa/nessa vaga" + metricas → job_analytics
   - "das vagas / geral / empresa / conta" → account_stats
   - "por status / por departamento / quantas de cada" → distribution
   Na DUVIDA com job_id no contexto → job_analytics

3. WRITE ACTIONS: Qualquer acao que MODIFICA dados (change_status, bulk_apply_action, copy_job)
   DEVE retornar needs_confirmation=True com contagens exatas antes de executar.

4. FAIRNESS: Filtros por genero, idade, raca, religiao sao BLOQUEADOS.
   Filtros por PCD so sao permitidos se a vaga tem disabilities=true.

5. RESOLUCAO DE REFERENCIAS: Use conversation_memory para resolver
   pronomes e referencias ("desses", "os mesmos", "sim").

6. MAPEAMENTOS DIRETOS:
   - "Publique" / "Coloque no ar" → change_status(target: "publish")
   - "Pause" / "Suspenda" → change_status(target: "Paralisada")
   - "Feche" / "Encerre" → change_status(target: "Fechada (preenchida)")
   - "Reabra" → change_status(target: "Reaberta")
   - "Arquive" → change_status(target: "Arquivada")
   - "Pipeline" / "Kanban" / "Etapas" → pipeline_status
   - "Quem combina?" / "Match" → matching_candidates
   - "O que falta?" / "Esta pronta?" → readiness_check
   - "Gere descricao" / "Melhore a descricao" → generate_suggestion
   - "Perguntas para entrevista" → generate_questions
   - "Busca booleana" → generate_boolean_search
   - "Como esta o funil?" / "Gargalo?" → job_analytics(section: "funnel")
   - "Velocidade" → job_analytics(section: "velocity")
   - "Entrevistas agendadas" → job_analytics(section: "scheduling")
   - "De onde vem os candidatos?" → job_analytics(section: "sources")
   - "Vagas por departamento" → distribution(by: "department")
   - "Abertas vs fechadas" → distribution(by: "open_closed")
```

---

## Exemplos de Interacao

### Queries basicas
```
User: "Quantos candidatos tem nessa vaga?"
→ pipeline_status
→ "📊 A vaga Dev Python Senior tem 45 candidatos no pipeline:
   Triagem: 30 | Entrevista: 12 | Contratado: 3"

User: "O que falta para publicar?"
→ readiness_check
→ "⚠️ A vaga esta 72% completa. Faltam:
   - Salario (critico)
   - Beneficios (critico)
   - Idiomas (opcional)
   Status: Rascunho → precisa mudar para Ativa"
```

### Analytics (section param)
```
User: "Como esta o funil?"
→ job_analytics(section: "funnel")
→ "📊 Funil: Triagem 30 → Entrevista 12 (conv. 40%) → Contratado 3 (conv. 25%)
   Gargalo: Triagem (conv. 40%, media 3.2 dias)"

User: "Velocidade do pipeline"
→ job_analytics(section: "velocity")
→ "⏱️ Primeira acao: 4.5h | Triagem: 2.3 dias | 5.1 candidatos/dia"

User: "Entrevistas agendadas?"
→ job_analytics(section: "scheduling")
→ "📅 12 agendadas | 8 completadas | 2 canceladas | 1 no-show"
```

### Distributions (by param)
```
User: "Vagas por departamento"
→ distribution(by: "department")
→ "📊 Engenharia: 15 | Produto: 8 | Comercial: 5 | RH: 3"

User: "Abertas vs fechadas"
→ distribution(by: "open_closed")
→ "📊 Abertas: 23 | Fechadas: 18 | Total no periodo: 41"
```

### Write actions com confirmacao
```
User: "Rejeite todos da triagem"
→ bulk_apply_action(action: "reject", stage_filter: "Triagem")

Agent (1a resposta — confirmacao):
"⚠️ Tem certeza que deseja REJEITAR 47 candidato(s) da etapa Triagem
da vaga Dev Python Senior?

Esta acao NAO pode ser desfeita.

---
⚠️ Acoes em lote afetam multiplos candidatos. Certifique-se de que
os criterios nao discriminam por atributos protegidos."

User: "Sim"
→ executa → "✅ 47 candidatos rejeitados da etapa Triagem."
```

### Matching com FairnessGuard
```
User: "Quem combina com essa vaga?"
→ matching_candidates(top_k: 10)
→ "🎯 Top 10 candidatos compativeis:
   1. Maria Silva (92%) - 5 anos Python
   2. Joao Santos (87%) - 8 anos backend
   ...
   ---
   ⚠️ Este ranking e baseado em fit tecnico. Fatores como
   fit cultural e diversidade devem ser considerados."

User: "Filtre por genero feminino"
→ matching_candidates(gender: "feminino")
→ "❌ Filtro por 'gender' bloqueado. Filtrar candidatos por genero
   pode violar legislacao trabalhista (LGPD/EEO).
   Consulte seu departamento juridico."
```

---

## Mudancas Necessarias no Rails (ATS API)

### 1. Endpoint `context_for_ai` no JobsController (tiered)

```ruby
# config/routes.rb
resources :jobs do
  member do
    get :context_for_ai
  end
end
```

```ruby
def context_for_ai
  @job = Job.include_base.find(params[:id])
  tier = (params[:tier] || 1).to_i

  response = build_tier1_context(@job)
  response.merge!(build_tier2_context(@job)) if tier >= 2

  render_success(response)
end

private

def build_tier1_context(job)
  {
    job: serialize_job_for_ai(job),
    pipeline_summary: job.selection_process_summary
  }
end

def build_tier2_context(job)
  analytics = Jobs::AnalyticsService.new(job: job).call
  {
    aggregated_stats: build_aggregated_stats(analytics),
    recent_applies: serialize_recent_applies(job)
  }
end
```

### 2. Conversation Memory no Workspace

```ruby
# Rails persiste conversation_memory no workspace
# quando recebe resposta do agent com metadata.conversation_memory
class Api::V1::MessagesController < ApplicationController
  def create
    # ... cria mensagem ...

    if params.dig(:metadata, :conversation_memory).present?
      workspace = Workspace.find_by(id: params[:workspace_id])
      workspace&.update_column(:conversation_memory,
        params[:metadata][:conversation_memory])
    end
  end
end

# Na proxima mensagem do usuario, envia conversation_memory:
def build_context_for_agent(workspace, message)
  {
    domain: workspace.domain,
    user_query: message.content,
    context_data: {
      job_id: workspace.domain_reference_id,
      user_id: current_user.id,
      workspace_id: workspace.id,
      account_id: current_account.id,
      **workspace.get_conversation_context
    }
  }
end
```

---

## Checklist de Implementacao

### Rails (ATS API)
- [ ] Criar `context_for_ai` tiered no JobsController
- [ ] Adicionar rota `GET /v1/users/jobs/:id/context_for_ai`
- [ ] Persistir `conversation_memory` no Workspace ao receber resposta do agent
- [ ] Enviar `conversation_memory` + `recent_messages` em toda mensagem ao agent
- [ ] Criar workspace com `domain: "job"` quando usuario abre chat na vaga

### Python Agent (recruiter_agent_v5)
- [ ] Criar `src/domains/jobs/`
- [ ] `domain.py` com `@register_domain` e 22 actions
- [ ] `api_client.py` com metodos tiered
- [ ] `cache.py` com `TieredContextManager`
- [ ] `fairness.py` com `JobFairnessGuard`
- [ ] `memory.py` com `JobConversationMemory`
- [ ] `prompts.py` com system prompt e triggers calibrados
- [ ] `prompt_builder/` com 22 actions + triggers + negative keywords
- [ ] `actions/` (base, query, analytics, matching, mutations, suggestions, conversational)
- [ ] Composicao via delegacao (nao heranca multipla)
- [ ] `template_formatter.py`
- [ ] `dispatcher.py` + `tasks.py`
- [ ] Registrar domain no `__init__.py`

### Testes
- [ ] Unit: cada action handler isolado (mock API)
- [ ] Unit: FairnessGuard (block, allow, PCD context)
- [ ] Unit: ConversationMemory (resolve references, serialize/deserialize)
- [ ] Unit: intent classification (stats vs analytics vs distribution)
- [ ] Integration: fluxo completo query → intent → execute → response
- [ ] Integration: write action com confirmacao (2 turnos)
- [ ] Integration: conversation memory persistence round-trip


outros endpoints importantes que precisam ser levados em consideracao

# Agente Jobs — Mapeamento Perguntas x Endpoints

Referencia para o agente Python saber qual endpoint chamar, com quais parametros, e o que esperar de retorno.

---

## Endpoints Disponiveis

| # | Endpoint | Metodo | Descricao |
|---|----------|--------|-----------|
| 1 | `/v1/users/jobs` | GET | Listagem com Searchkick (filtros, busca, paginacao, agregadores) |
| 2 | `/v1/users/jobs/:id` | GET | Detalhe completo de uma vaga |
| 3 | `/v1/users/jobs/:id/analytics` | GET | Analytics completo da vaga (funnel, velocity, quality, etc) |
| 4 | `/v1/users/jobs/:id/kanban` | GET | Kanban com candidatos por etapa |
| 5 | `/v1/users/jobs/stats` | GET | Estatisticas agregadas cross-vagas |
| 6 | `/v1/users/jobs/alerts` | GET | Alertas combinados (deadline, urgencia, vagas paradas) |
| 7 | `/v1/users/jobs/:id/activity_log` | GET | Historico de mudancas da vaga |
| 8 | `/v1/users/jobs/:id/export` | GET | Exportacao CSV da vaga |
| 9 | `/v1/users/applies` | GET | Listagem de applies (candidaturas) com filtros |
| 10 | `/v1/users/jobs/:id/evaluations` | GET | Avaliacoes vinculadas a uma vaga |

---

## 1. CONTAGENS E VISAO GERAL

### "Quantas vagas eu tenho?" / "Total de vagas"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[is_deleted]=false`
- **Retorno:** `total_count` no response
- **Campo usado:** `total_count`

### "Quantas vagas abertas/ativas?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[is_active]=true&where[is_archived]=false`
- **Retorno:** `total_count`

### "Me da um resumo das vagas" / "Panorama geral"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Params:** `start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` (opcional, default 30 dias)
- **Retorno:**
  ```json
  {
    "totals": { "total": 150, "active": 80, "archived": 30, "created_in_period": 25 },
    "by_status": [{ "status": "Ativa", "color": "#green", "count": 80 }],
    "open_vs_closed": { "open": 80, "closed": 45, "total": 125 },
    "avg_days_to_close": 32.5,
    "created_per_week": [{ "week": "2026-02-23", "count": 5 }]
  }
  ```

### "Quantas vagas fechamos esse mes?"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Params:** `start_date=2026-03-01&end_date=2026-03-31`
- **Campo usado:** `open_vs_closed.closed`

### "Quantas vagas novas abriram essa semana?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[created_at][gte]=2026-03-01&where[is_active]=true`
- **Retorno:** `total_count`

---

## 2. CONTAGENS COM FILTRO

### "Quantas vagas de tecnologia estao abertas?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[department_name]=tecnologia&where[is_active]=true`
- **Retorno:** `total_count`

### "Quantas vagas tenho em Sao Paulo?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[city]=sao paulo`
- **Retorno:** `total_count`

### "Quantas vagas remotas?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[workplace_type]=1`
- **Retorno:** `total_count`

### "Quantas vagas senior abertas?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[seniority]=2&where[is_active]=true`
- **Retorno:** `total_count`
- **Nota:** seniority: 0=Junior, 1=Pleno, 2=Senior, 3=Especialista, 4=Estagio, 5=Lead, 6=Gerente, 7=Diretor

### "Quantas vagas do cliente X?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[company_name]=nome do cliente`
- **Retorno:** `total_count`

### "Quantas vagas o gerente Joao tem?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[hiring_manager_name]=joao`
- **Retorno:** `total_count`

### "Quantas vagas com salario acima de 10k?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[salary_from][gte]=10000`
- **Retorno:** `total_count`

---

## 3. DETALHES DE UMA VAGA

### "Me mostra os detalhes da vaga 123" / "Abre a vaga de Dev Senior"
- **Endpoint:** `GET /v1/users/jobs/:id`
- **Retorno:**
  ```json
  {
    "id": 123,
    "title": "Dev Senior",
    "description": "...",
    "job_status": { "id": 1, "name": "Ativa", "color": "#green" },
    "user_name": "Recrutador",
    "hiring_manager_id": 45,
    "city": "Sao Paulo",
    "workplace_type": "1",
    "seniority": 2,
    "salary_from": 15000,
    "salary_to": 20000,
    "application_deadline": "2026-04-01",
    "closing_deadline": "2026-04-15",
    "priority": 1,
    "urgency_level": 4,
    "is_urgent": true,
    "responsibilities": ["Liderar equipe", "Code review"],
    "applies_count": 42,
    "created_at": "2026-02-01"
  }
  ```

### "Quais skills essa vaga pede?"
- **Endpoint:** `GET /v1/users/jobs/:id` (inclui skills via serializer)
- **Alternativa:** `GET /v1/users/skill_relationships?where[reference_type]=Job&where[reference_id]=:id`

### "Qual a faixa salarial?"
- **Endpoint:** `GET /v1/users/jobs/:id`
- **Campos:** `salary_from`, `salary_to`, `salary_currency`, `salary_period`

### "Faz quanto tempo que essa vaga ta aberta?"
- **Endpoint:** `GET /v1/users/jobs/:id/analytics`
- **Campos:** `overview.days_since_published`, `overview.days_since_created`

### "Essa vaga ta dentro do prazo?"
- **Endpoint:** `GET /v1/users/jobs/:id/analytics`
- **Campos:** `overview.days_until_deadline`, `overview.is_deadline_expired`

---

## 4. PIPELINE / FUNIL

### "Qual o funil da vaga X?" / "Quantos candidatos tem em cada etapa?"
- **Endpoint:** `GET /v1/users/jobs/:id/analytics`
- **Campo:** `funnel.stages`
- **Retorno:**
  ```json
  {
    "funnel": {
      "stages": [
        {
          "selective_process_id": 1,
          "name": "Funil",
          "current_count": 30,
          "total_entered": 50,
          "total_exited": 20,
          "conversion_rate": 40.0,
          "avg_time_in_stage_hours": 72.5
        }
      ],
      "overall_conversion_rate": 8.5,
      "bottleneck_stage": "Entrevista",
      "avg_total_pipeline_days": 15.3
    }
  }
  ```

### "Quem sao os candidatos na fase de entrevista?"
- **Endpoint:** `GET /v1/users/jobs/:id/kanban`
- **Params:** `selective_process_id=:stage_id&page=1`
- **Retorno:**
  ```json
  {
    "columns": [{
      "selective_process_id": 3,
      "selective_process_title": "Entrevista",
      "applies": {
        "records": [{ "id": 1, "name": "Joao", "email": "...", "cv_match": 85 }],
        "total_count": 12
      }
    }]
  }
  ```

### "Qual a taxa de conversao por etapa?"
- **Endpoint:** `GET /v1/users/jobs/:id/analytics`
- **Campo:** `funnel.stages[].conversion_rate`

### "Onde ta o gargalo dessa vaga?"
- **Endpoint:** `GET /v1/users/jobs/:id/analytics`
- **Campo:** `funnel.bottleneck_stage`

### "Tem candidato parado ha muito tempo?"
- **Endpoint:** `GET /v1/users/jobs/:id/analytics`
- **Campo:** `team_activity.inactive_applies_7d`

---

## 5. TEMPO E PERFORMANCE

### "Qual o tempo medio de fechamento das vagas?"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `avg_days_to_close`

### "Quanto tempo em media um candidato fica em cada etapa?"
- **Endpoint:** `GET /v1/users/jobs/:id/analytics`
- **Campo:** `funnel.stages[].avg_time_in_stage_hours`

### "Qual etapa demora mais?"
- **Endpoint:** `GET /v1/users/jobs/:id/analytics`
- **Logica:** ordenar `funnel.stages` por `avg_time_in_stage_hours` DESC

### "Quantas vagas fechamos por mes?"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `created_per_week` (agrupar por mes no Python)

### "Qual recruiter fecha mais rapido?"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `top_recruiters_by_speed`
- **Retorno:**
  ```json
  [{ "user_id": 1, "name": "Maria", "jobs_closed": 8, "avg_days_to_close": 22.3 }]
  ```

### "Quais vagas estao paradas ha mais de 30 dias?"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `stale_jobs`
- **Retorno:**
  ```json
  [{ "job_id": 45, "title": "Dev Pleno", "last_activity_at": "2026-01-15", "days_inactive": 49 }]
  ```

### "Vagas abertas ha mais de 60 dias"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[created_at][lte]=2026-01-04&where[is_active]=true&where[is_archived]=false`
- **Retorno:** lista de vagas + `total_count`

---

## 6. SLA E ALERTAS

### "Quais vagas estao fora do SLA?" / "Tem alguma vaga atrasada?"
- **Endpoint:** `GET /v1/users/jobs/alerts`
- **Campo:** `deadline_expired`
- **Retorno:**
  ```json
  {
    "deadline_expired": [{ "job_id": 10, "title": "QA Senior", "closing_deadline": "2026-02-28", "urgency_level": 4 }],
    "deadline_soon": [{ "job_id": 20, "title": "Dev Jr", "closing_deadline": "2026-03-10", "days_remaining": 5 }],
    "urgent_without_finalists": [{ "job_id": 30, "title": "Tech Lead", "urgency_level": 5 }],
    "stale": [{ "job_id": 45, "title": "Dev Pleno", "days_inactive": 35 }],
    "no_applies": [{ "job_id": 50, "title": "Data Analyst", "days_open": 12 }],
    "summary": { "total_alerts": 15 }
  }
  ```

### "Quais vagas vencem essa semana?"
- **Endpoint:** `GET /v1/users/jobs/alerts`
- **Campo:** `deadline_soon`

### "Tem vaga urgente sem candidato em fase final?"
- **Endpoint:** `GET /v1/users/jobs/alerts`
- **Campo:** `urgent_without_finalists`

### "O que eu deveria priorizar hoje?"
- **Endpoint:** `GET /v1/users/jobs/alerts`
- **Logica:** LLM analisa todos os campos do alerta e prioriza

### "Vagas com prazo ate sexta"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[closing_deadline][lte]=2026-03-07&where[closing_deadline][gte]=2026-03-05&where[is_active]=true`

---

## 7. DISTRIBUICOES E ESTATISTICAS

### "Distribuicao das vagas por area/departamento"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `by_department`

**Alternativa via agregadores:**
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `force_aggregators=true`
- **Campo:** `aggregations.department_name`

### "Distribuicao por cidade"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `force_aggregators=true`
- **Campo:** `aggregations.city`

### "Quantas vagas remotas vs presenciais?"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `by_workplace_type`

### "Distribuicao por senioridade"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `force_aggregators=true`
- **Campo:** `aggregations.seniority_text`

### "Distribuicao por faixa salarial"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `force_aggregators=true`
- **Campo:** `aggregations.salary_range`

### "Quantas vagas cada recrutador tem?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `force_aggregators=true`
- **Campo:** `aggregations.user_name`

### "Quantas vagas por cliente?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `force_aggregators=true`
- **Campo:** `aggregations.company_name`

### "Distribuicao por prioridade"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `by_priority`

### "Distribuicao por urgencia"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `by_urgency`

### "Quem ta com mais vagas?" (hiring managers)
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `top_hiring_managers`

---

## 8. BUSCA E FILTROS

### "Me mostra vagas de Python" / "Busca vagas que pedem React"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `term=python`
- **Retorno:** lista de vagas ranqueadas por relevancia + `total_count`

### "Vagas remotas de tecnologia em SP"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[workplace_type]=1&where[department_name]=tecnologia&where[city]=sao paulo`

### "Vagas senior de marketing com salario acima de 15k"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[seniority]=2&where[department_name]=marketing&where[salary_from][gte]=15000`

### "Vagas criadas nos ultimos 7 dias"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `where[created_at][gte]=2026-02-26`

### "Em quais vagas o Joao da Silva esta?"
- **Endpoint:** `GET /v1/users/applies`
- **Params:** `where[candidate_id]=:candidate_id`
- **Retorno:** lista de applies, cada um com `job_id` e `selective_process_name`
- **Nota:** buscar candidate_id antes via `GET /v1/users/candidates?term=joao da silva`

---

## 9. COMPARACOES E RANKINGS

### "Top 5 vagas mais concorridas"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `jobs_ranking.most_applies`
- **Retorno:**
  ```json
  [{ "job_id": 10, "title": "Dev Senior", "applies_count": 120 }]
  ```

### "Quais vagas fecharam mais rapido?"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `jobs_ranking.fastest_closed`
- **Retorno:**
  ```json
  [{ "job_id": 5, "title": "QA Pleno", "days_to_close": 12.3 }]
  ```

### "Ranking de vagas por tempo aberto"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `jobs_ranking.longest_open`

### "Compara a vaga A com a vaga B"
- **Endpoint:** `GET /v1/users/jobs/:id_a/analytics` + `GET /v1/users/jobs/:id_b/analytics`
- **Logica:** chamar analytics de ambas e comparar no Python/LLM

### "Qual dessas vagas tem mais candidatos?"
- **Endpoint:** `GET /v1/users/jobs/:id_a` + `GET /v1/users/jobs/:id_b`
- **Campo:** `applies_count` de cada

---

## 10. RELATORIOS

### "Gera um relatorio das vagas" / "Resumo executivo"
- **Endpoints combinados:**
  1. `GET /v1/users/jobs/stats` — visao macro
  2. `GET /v1/users/jobs/alerts` — problemas e prioridades
- **Logica:** LLM consolida dados em formato de relatorio

### "Relatorio da vaga X"
- **Endpoints combinados:**
  1. `GET /v1/users/jobs/:id` — dados da vaga
  2. `GET /v1/users/jobs/:id/analytics` — metricas completas
- **Logica:** LLM gera relatorio narrativo

### "Exporta a lista de vagas" / "CSV das vagas abertas"
- **Endpoint:** `GET /v1/users/jobs/:id/export`
- **Params:** `format=csv`
- **Retorno:** arquivo CSV para download

### "Relatorio de vagas por cliente"
- **Endpoints:**
  1. `GET /v1/users/jobs?force_aggregators=true` — aggregations.company_name
  2. Para cada cliente relevante: `GET /v1/users/jobs?where[company_name]=X`

---

## 11. ANALISE E SUGESTOES (LLM)

### "Essa descricao de vaga ta boa?" / "Me sugere melhorias"
- **Endpoint:** `GET /v1/users/jobs/:id`
- **Campos enviados ao LLM:** `description`, `title`, `responsibilities`, skills, seniority, salary
- **Logica:** LLM analisa e sugere melhorias

### "Por que essa vaga ta demorando tanto?"
- **Endpoint:** `GET /v1/users/jobs/:id/analytics`
- **Campos enviados ao LLM:** `funnel` (bottleneck, conversion_rate), `velocity`, `quality` (avg_cv_match)
- **Logica:** LLM diagnostica com base nos dados

### "Quais skills estao sendo mais pedidos nas vagas?"
- **Endpoint:** `GET /v1/users/jobs`
- **Params:** `force_aggregators=true&where[is_active]=true`
- **Campo:** `aggregations.skills`

### "Ta abrindo mais vaga remota ou presencial?"
- **Endpoint:** `GET /v1/users/jobs/stats`
- **Campo:** `by_workplace_type`
- **Complemento:** comparar com periodo anterior passando `start_date`/`end_date` diferentes

---

## 12. CONVERSACIONAL / CONTEXTUAL

### "E essa vaga aqui?" / "Me fala mais sobre ela"
- **Logica:** usar conversation_memory para pegar job_id da ultima vaga mencionada
- **Endpoint:** `GET /v1/users/jobs/:id`

### "E o funil dela?"
- **Logica:** conversation_memory → job_id
- **Endpoint:** `GET /v1/users/jobs/:id/analytics` → `funnel`

### "Agora filtra so as de SP"
- **Logica:** manter filtros anteriores da conversa + adicionar `where[city]=sao paulo`
- **Endpoint:** `GET /v1/users/jobs`

---

## Referencia Rapida — Enums

### Seniority
| ID | Valor |
|----|-------|
| 0 | Junior |
| 1 | Pleno |
| 2 | Senior |
| 3 | Especialista |
| 4 | Estagio |
| 5 | Lead |
| 6 | Gerente |
| 7 | Diretor |

### Workplace Type
| ID | Valor |
|----|-------|
| nil | Nao informado |
| 1 | Remoto |
| 2 | Hibrido |
| 3 | Presencial |

### Priority
| ID | Valor |
|----|-------|
| nil | Nao informado |
| 1 | Alta |
| 2 | Media |
| 3 | Baixa |

### Urgency Level
| ID | Valor |
|----|-------|
| nil | Nao informado |
| 1 | Baixa |
| 2 | Moderada |
| 3 | Media |
| 4 | Alta |
| 5 | Critica |

### Employment Type
| ID | Valor |
|----|-------|
| 0 | CLT |
| 1 | PJ |
| 2 | Estagio |
| 3 | Temporario |
| 4 | Freelancer |
| 5 | Aprendiz |




'e extremamente importante que quando a action/tools for retornar uma colecao vc apresente visualmente bem como tabela ascii ou de uma forma visual agradavel, da mesma forma quando for detalhes de uma vaga #show ou analises deve retornar em formato mais relatorio

voce pode usar como referencia o domain/sourced_profile_sourcing q esta funcionando muito bem

