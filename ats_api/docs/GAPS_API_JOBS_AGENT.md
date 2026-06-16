# Gaps da API para o Agente de Jobs

Análise das APIs faltantes para suportar todas as perguntas mapeadas no dominio Jobs.

---

## Contexto: O que o Searchkick ja indexa no Job

O `GET /jobs` (index) usa Searchkick com `where` flexivel. O agente pode filtrar por qualquer campo indexado e receber `total_count` na resposta. Os agregadores (`agg_search_array`) retornam distribuicoes automaticamente.

**Campos ja indexados e filtraveis:**

| Dimensao | Campos no search_data | Agregador (aggs) |
|----------|----------------------|-------------------|
| Status | `job_status_id`, `job_status_name` | Sim |
| Localizacao | `city`, `state`, `country`, `location_full` | Sim (`city`, `state`, `country`) |
| Modelo trabalho | `workplace_type`, `workplace_type_text`, `is_remote` | Sim |
| Senioridade | `seniority`, `seniority_text` | **Nao** (campo indexado mas sem agregador) |
| Salario | `salary_from`, `salary_to`, `salary_range`, `salary_value` | Sim (`salary_range`) |
| Empresa/Cliente | `company_id`, `company_name` | Sim |
| Recrutador/Owner | `user_id`, `user_name`, `user_email` | Sim |
| Hiring Manager | `hiring_manager_id`, `hiring_manager_name` | **Nao** (campo indexado mas sem agregador) |
| Departamento | `department_id`, `department_name` | **Nao** (campo indexado mas sem agregador) |
| Prioridade | `priority`, `priority_text` | **Nao** (campo indexado mas sem agregador) |
| Urgencia | `urgency_level`, `urgency_level_text`, `is_urgent` | Sim (`is_urgent`) |
| Deadline | `closing_deadline`, `application_deadline`, `is_deadline_expired`, `days_until_deadline` | Sim (`has_deadline`, `is_deadline_expired`) |
| Skills | `skills`, `skills_text` | Sim |
| Applies | `total_applies`, `applies_count`, `applies_by_status_count` | **Nao** |
| Datas | `created_at`, `updated_at`, `published_date` | **Nao** |
| Emprego | `employment_type`, `employment_type_text` | **Nao** |
| PCD | `is_pcd`, `main_pcd_category` | Sim |

**O que o `StatsService` ja retorna:**
- `by_status`, `open_vs_closed`, `avg_days_to_close`, `created_per_week`
- `by_department`, `by_priority`, `by_urgency`, `by_workplace_type`
- `top_hiring_managers` (top 10 por qtd), `totals`

**O que o `AnalyticsService` retorna (por vaga):**
- `overview` (total_applies, days_since_published, days_until_deadline)
- `funnel` (stages com current_count, conversion_rate, avg_time_in_stage, bottleneck)
- `velocity` (time_to_first_action, time_to_screening, applies_per_day, trend)
- `quality` (avg_cv_match, score_distribution, evaluation_stats)
- `sources` (by_source, by_career_page)
- `engagement` (dispatches, messages, feedback)
- `scheduling` (interviews scheduled/completed/cancelled)
- `team_activity` (actions_by_user, inactive_applies_7d)

---

## Status por Secao

| # | Secao | Status | Como responder |
|---|-------|--------|----------------|
| 1 | Contagens e Visao Geral | ✅ | `GET /jobs` com `where` + `total_count` / `GET /jobs/stats` |
| 2 | Detalhes de uma Vaga | ✅ | `GET /jobs/:id` |
| 3 | Pipeline / Funil | ✅ | `GET /jobs/:id/analytics` (funnel) + `GET /jobs/:id/kanban` |
| 4 | Tempo e Performance | ⚠️ | Analytics cobre por vaga. Falta visao cross-vagas |
| 5 | SLA e Alertas | ⚠️ | Filtros de deadline existem no Searchkick. Falta alertas combinados |
| 6 | Distribuicoes e Estatisticas | ✅ | Searchkick aggs + `where` + `total_count` cobrem todas as dimensoes |
| 7 | Busca e Filtros | ✅ | Searchkick full-text + where combinado |
| 8 | Comparacoes e Rankings | ⚠️ | Parcial — ordering por total_applies funciona, mas ranking por conversao/velocidade nao |
| 9 | Relatorios | ✅ | Combinacao de stats + analytics + export |
| 10 | Analise e Sugestoes (LLM) | ✅ | Dados brutos disponiveis, LLM processa |
| 11 | Conversacional | ✅ | N/A (conversation_memory no Python) |
| 12 | Cross-Domain (Hub) | ⚠️ | Match existe. Integracao sourcing via Hub futuro |

---

## O que NAO precisa criar (Searchkick ja resolve)

### Distribuicoes (Secao 6) — Todas cobertas via `GET /jobs`

O agente Python pode usar `GET /jobs` com filtros e agregadores para responder:

| Pergunta | Como resolver |
|----------|--------------|
| "Quantas vagas em SP?" | `where[city]=sao paulo` → `total_count` |
| "Distribuicao por cidade" | `aggs` com `city` |
| "Quantas vagas senior?" | `where[seniority]=2` → `total_count` |
| "Distribuicao por senioridade" | `where` por cada valor OU adicionar agregador (ver Gap 1) |
| "Media salarial das vagas" | `aggs` com `salary_range` |
| "Vagas do cliente X" | `where[company_name]=x` → `total_count` |
| "Quantas vagas cada recrutador tem?" | `aggs` com `user_name` |
| "Vagas remotas vs presenciais" | `aggs` com `workplace_type` |
| "Vagas por departamento" | `where[department_name]=x` OU stats `by_department` |

### Filtros de SLA/Deadline (Secao 5.1) — Ja indexados

| Pergunta | Como resolver |
|----------|--------------|
| "Vagas que vencem essa semana" | `where[closing_deadline][lte]=2026-03-12` + `where[closing_deadline][gte]=2026-03-05` |
| "Vagas com deadline expirado" | `where[is_deadline_expired]=true` |
| "Vagas abertas ha mais de 60 dias" | `where[created_at][lte]=2026-01-04` + `where[is_active]=true` |

### Contagens com filtro (Secao 1.3)

| Pergunta | Como resolver |
|----------|--------------|
| "Vagas de tecnologia abertas" | `where[department_name]=tecnologia` + `where[is_active]=true` → `total_count` |
| "Vagas remotas" | `where[workplace_type]=1` → `total_count` |
| "Vagas do gerente Joao" | `where[hiring_manager_name]=joao` → `total_count` |
| "Vagas com salario acima de 10k" | `where[salary_from][gte]=10000` → `total_count` |

---

## Gaps Reais — O que precisa criar

### Gap 1 — Agregadores faltantes no `agg_search_array` (Baixo esforco)

**Arquivo:** `app/models/job.rb` metodo `self.agg_search_array`

O Searchkick ja indexa esses campos, mas nao tem agregadores definidos. Sem o agregador, o agente consegue filtrar (`where`) mas nao consegue pedir a distribuicao completa em uma unica chamada.

**Adicionar:**

```ruby
def self.agg_search_array(_params = {})
  {
    # ... existentes ...
    seniority_text: { field: "seniority_text", limit: 10 },
    employment_type_text: { field: "employment_type_text", limit: 10 },
    department_name: { field: "department_name", limit: 20 },
    hiring_manager_name: { field: "hiring_manager_name", limit: 20 },
    priority_text: { field: "priority_text", limit: 5 },
    urgency_level_text: { field: "urgency_level_text", limit: 10 }
  }
end
```

**Impacto:** O agente podera pedir `GET /jobs?include_aggregators=true` e receber distribuicoes por senioridade, tipo de emprego, departamento, hiring manager, prioridade e urgencia sem precisar iterar.

---

### Gap 2 — Vagas paradas / sem movimentacao (Medio esforco)

**Problema:** Nao ha como identificar vagas "travadas" de forma eficiente. O campo `updated_at` do Job nao reflete movimentacao de candidatos (applies/apply_statuses). Para saber "ultima movimentacao" teria que chamar analytics de cada vaga.

**Perguntas afetadas:**
- "Quais vagas estao paradas ha mais de 30 dias?"
- "Quais vagas nao receberam candidatos novos na ultima semana?"
- "Tem vaga sem movimentacao?"
- "Quais vagas estao travadas?"

**Proposta A — Indexar `last_activity_at` no Searchkick:**

```ruby
# Em Job#search_data, adicionar:
last_activity_at: compute_last_activity_at

# Novo metodo:
def compute_last_activity_at
  dates = [updated_at]

  last_apply = Apply.where(job_id: id, is_deleted: false).maximum(:created_at)
  dates << last_apply if last_apply

  last_transition = ApplyStatus
    .joins(:apply)
    .where(applies: { job_id: id, is_deleted: false }, is_deleted: false)
    .maximum(:created_at)
  dates << last_transition if last_transition

  dates.compact.max
end
```

Com isso: `GET /jobs?where[last_activity_at][lte]=2026-02-03&where[is_active]=true` retorna vagas paradas.

**Custo:** Precisa reindexar. O calculo e feito no momento do reindex, entao nao impacta performance de leitura. Mas o campo fica desatualizado ate o proximo reindex. Pode adicionar um callback no Apply e ApplyStatus para reindexar o job pai.

**Proposta B — Query direta no StatsService (sem reindex):**

```ruby
def stale_jobs(days_threshold: 30)
  ActiveRecord::Base.connection.select_all(<<~SQL)
    SELECT j.id, j.title, j.created_at,
      COALESCE(
        (SELECT MAX(ast.created_at) FROM apply_statuses ast
         INNER JOIN applies a ON a.id = ast.apply_id
         WHERE a.job_id = j.id AND a.is_deleted = false AND ast.is_deleted = false),
        j.created_at
      ) AS last_activity_at
    FROM jobs j
    WHERE j.account_id = #{account_id.to_i}
      AND j.is_deleted = false
      AND j.is_active = true
      AND j.is_archived = false
    HAVING COALESCE(
      (SELECT MAX(ast.created_at) FROM apply_statuses ast
       INNER JOIN applies a ON a.id = ast.apply_id
       WHERE a.job_id = j.id AND a.is_deleted = false AND ast.is_deleted = false),
      j.created_at
    ) < NOW() - INTERVAL '#{days_threshold.to_i} days'
    ORDER BY last_activity_at ASC
    LIMIT 20
  SQL
end
```

**Recomendacao:** Proposta B para MVP (funciona sem reindex). Proposta A como melhoria futura.

---

### Gap 3 — Alertas combinados (Medio esforco)

**Problema:** O agente consegue filtrar por deadline, urgencia, etc individualmente. Mas perguntas como "o que priorizar hoje?" ou "vagas em risco" exigem cruzar multiplas regras de negocio. O agente Python poderia fazer multiplas chamadas, mas um endpoint dedicado seria mais eficiente e consistente.

**Perguntas afetadas:**
- "Tem vaga urgente sem candidato em fase final?"
- "Quais vagas precisam de atencao?"
- "O que eu deveria priorizar hoje?"
- "Quais vagas estao em risco?"

**Proposta — `GET /jobs/alerts`:**

**Arquivo:** `app/services/jobs/alerts_service.rb`

```ruby
module Jobs
  class AlertsService
    def initialize(account_id:)
      @account_id = account_id
    end

    def call
      {
        deadline_expired: deadline_expired_jobs,
        deadline_soon: deadline_soon_jobs(days: 7),
        urgent_without_finalists: urgent_without_finalists,
        stale: stale_active_jobs(days: 30),
        no_applies: active_jobs_without_applies,
        summary: {
          total_alerts: 0 # calculado apos montar tudo
        }
      }
    end

    private

    def base_scope
      Job.where(account_id: @account_id, is_deleted: false, is_active: true, is_archived: false)
    end

    def deadline_expired_jobs
      base_scope
        .where("closing_deadline < ?", Date.current)
        .select(:id, :title, :closing_deadline, :urgency_level)
        .order(:closing_deadline)
        .limit(20)
        .map { |j| { job_id: j.id, title: j.title, closing_deadline: j.closing_deadline, urgency_level: j.urgency_level } }
    end

    def deadline_soon_jobs(days:)
      base_scope
        .where(closing_deadline: Date.current..days.days.from_now.to_date)
        .select(:id, :title, :closing_deadline, :urgency_level)
        .order(:closing_deadline)
        .limit(20)
        .map { |j| { job_id: j.id, title: j.title, closing_deadline: j.closing_deadline, days_remaining: (j.closing_deadline - Date.current).to_i } }
    end

    def urgent_without_finalists
      final_stages = SelectiveProcess.where(status: [:hired, :interview]).pluck(:id)

      urgent_ids = base_scope.where("is_urgent = true OR urgency_level >= 4").pluck(:id)
      return [] if urgent_ids.empty?

      jobs_with_finalists = Apply
        .where(job_id: urgent_ids, selective_process_id: final_stages, is_deleted: false)
        .distinct
        .pluck(:job_id)

      base_scope
        .where(id: urgent_ids - jobs_with_finalists)
        .select(:id, :title, :urgency_level)
        .limit(20)
        .map { |j| { job_id: j.id, title: j.title, urgency_level: j.urgency_level } }
    end

    def stale_active_jobs(days:)
      rows = ActiveRecord::Base.connection.select_all(<<~SQL)
        SELECT j.id, j.title,
          COALESCE(
            (SELECT MAX(ast.created_at) FROM apply_statuses ast
             INNER JOIN applies a ON a.id = ast.apply_id
             WHERE a.job_id = j.id AND a.is_deleted = false AND ast.is_deleted = false),
            j.created_at
          ) AS last_activity_at
        FROM jobs j
        WHERE j.account_id = #{@account_id.to_i}
          AND j.is_deleted = false
          AND j.is_active = true
          AND j.is_archived = false
          AND COALESCE(
            (SELECT MAX(ast.created_at) FROM apply_statuses ast
             INNER JOIN applies a ON a.id = ast.apply_id
             WHERE a.job_id = j.id AND a.is_deleted = false AND ast.is_deleted = false),
            j.created_at
          ) < NOW() - INTERVAL '#{days.to_i} days'
        ORDER BY last_activity_at ASC
        LIMIT 20
      SQL

      rows.map do |row|
        {
          job_id: row["id"],
          title: row["title"],
          last_activity_at: row["last_activity_at"],
          days_inactive: ((Time.current - row["last_activity_at"].to_time) / 1.day).to_i
        }
      end
    end

    def active_jobs_without_applies
      base_scope
        .left_joins(:applies)
        .where(applies: { id: nil })
        .select(:id, :title, :created_at)
        .order(:created_at)
        .limit(20)
        .map { |j| { job_id: j.id, title: j.title, days_open: ((Time.current - j.created_at) / 1.day).to_i } }
    end
  end
end
```

**Rota:** Adicionar em `config/routes.rb`:

```ruby
collection do
  get :alerts
end
```

**Controller:** Adicionar ao `jobs_controller.rb`:

```ruby
def alerts
  result = ::Jobs::AlertsService.new(account_id: @current_user.account_id).call
  render json: { success: true, data: result }, status: :ok
end
```

---

### Gap 4 — Rankings cross-vagas por performance (Baixo esforco)

**Problema:** O index ordena por `total_applies` (campo indexado), mas nao por metricas como taxa de conversao ou velocidade de fechamento. Para "top 5 vagas mais concorridas" funciona, mas para "vagas com melhor conversao" nao.

**Perguntas afetadas:**
- "Quais vagas fecharam mais rapido?"
- "Quais vagas estao com melhor taxa de conversao?"
- "Ranking de vagas por tempo aberto"
- "Quais vagas estao com pior performance?"

**Proposta — Adicionar ao `StatsService`:**

```ruby
def jobs_ranking(limit: 10)
  {
    most_applies: most_applies_ranking(limit),
    longest_open: longest_open_ranking(limit),
    fastest_closed: fastest_closed_ranking(limit)
  }
end

private

def most_applies_ranking(limit)
  base_scope
    .where(is_active: true)
    .joins("LEFT JOIN applies ON applies.job_id = jobs.id AND applies.is_deleted = false")
    .group("jobs.id", "jobs.title")
    .order("COUNT(applies.id) DESC")
    .limit(limit)
    .pluck("jobs.id", "jobs.title", Arel.sql("COUNT(applies.id)"))
    .map { |id, title, count| { job_id: id, title: title, applies_count: count } }
end

def longest_open_ranking(limit)
  base_scope
    .where(is_active: true, is_archived: false)
    .order(:created_at)
    .limit(limit)
    .map { |j| { job_id: j.id, title: j.title, days_open: ((Time.current - j.created_at) / 1.day).to_i } }
end

def fastest_closed_ranking(limit)
  closed_names = ["Fechada (preenchida)", "Concluida"]

  ActiveRecord::Base.connection.select_all(<<~SQL).map do |row|
    SELECT j.id, j.title,
      EXTRACT(EPOCH FROM (al.created_at - j.created_at)) / 86400.0 AS days_to_close
    FROM jobs j
    INNER JOIN activity_logs al ON al.reference_type = 'Job'
      AND al.reference_id = j.id AND al.action = 'update'
    INNER JOIN job_statuses js ON js.id = (al.changeset->'job_status_id'->>'to')::bigint
    WHERE j.account_id = #{account_id.to_i}
      AND j.is_deleted = false
      AND js.name IN (#{closed_names.map { |n| "'#{n}'" }.join(',')})
      AND j.created_at BETWEEN '#{start_date}' AND '#{end_date.end_of_day.iso8601}'
    ORDER BY days_to_close ASC
    LIMIT #{limit.to_i}
  SQL
    { job_id: row["id"], title: row["title"], days_to_close: row["days_to_close"]&.to_f&.round(1) }
  end
end
```

**Rota:** Ja usa `GET /jobs/stats`, basta incluir `jobs_ranking` no retorno (ou parametrizar para so retornar quando pedido: `GET /jobs/stats?include_ranking=true`).

---

### Gap 5 — Recrutadores por velocidade (Baixo esforco)

**Perguntas afetadas:**
- "Qual recruiter fecha mais rapido?"
- "Qual o ritmo de fechamento do time?"

**Proposta — Adicionar ao `StatsService`:**

```ruby
def top_recruiters_by_speed
  closed_names = ["Fechada (preenchida)", "Concluida"]

  ActiveRecord::Base.connection.select_all(<<~SQL).map do |row|
    SELECT
      ju.user_id, u.name AS user_name,
      COUNT(DISTINCT j.id) AS jobs_closed,
      AVG(EXTRACT(EPOCH FROM (al.created_at - j.created_at)) / 86400.0) AS avg_days_to_close
    FROM job_users ju
    INNER JOIN jobs j ON j.id = ju.job_id
    INNER JOIN users u ON u.id = ju.user_id
    INNER JOIN activity_logs al ON al.reference_type = 'Job'
      AND al.reference_id = j.id AND al.action = 'update'
    INNER JOIN job_statuses js ON js.id = (al.changeset->'job_status_id'->>'to')::bigint
    WHERE j.account_id = #{account_id.to_i}
      AND j.is_deleted = false
      AND js.name IN (#{closed_names.map { |n| "'#{n}'" }.join(',')})
      AND j.created_at BETWEEN '#{start_date}' AND '#{end_date.end_of_day.iso8601}'
    GROUP BY ju.user_id, u.name
    HAVING COUNT(DISTINCT j.id) >= 1
    ORDER BY avg_days_to_close ASC
    LIMIT 10
  SQL
    {
      user_id: row["user_id"],
      name: row["user_name"],
      jobs_closed: row["jobs_closed"],
      avg_days_to_close: row["avg_days_to_close"]&.to_f&.round(1)
    }
  end
end
```

---

## Resumo Final

| # | Gap | O que fazer | Onde | Esforco | Prioridade |
|---|-----|-------------|------|---------|------------|
| 1 | Agregadores | Adicionar 6 agregadores ao `agg_search_array` | `Job model` | Baixo | Alta |
| 2 | Vagas paradas | Query de vagas sem movimentacao | `StatsService` | Medio | Media |
| 3 | Alertas | Novo `AlertsService` + rota `GET /jobs/alerts` | Novo servico | Medio | Alta |
| 4 | Rankings | Rankings cross-vagas (most applies, longest open, fastest closed) | `StatsService` | Baixo | Media |
| 5 | Velocidade recrutador | Ranking de recrutadores por tempo de fechamento | `StatsService` | Baixo | Baixa |

**Total: 3 baixo esforco + 2 medio esforco. Nenhum alto.**

O Searchkick ja cobre ~90% das necessidades. Os gaps reais sao:
- Distribuicoes que faltam agregador (Gap 1) — resolvido com 6 linhas
- Dados que exigem cruzamento de tabelas em tempo real (Gaps 2, 4, 5) — SQL no StatsService
- Regras de negocio combinadas para alertas proativos (Gap 3) — novo servico dedicado
