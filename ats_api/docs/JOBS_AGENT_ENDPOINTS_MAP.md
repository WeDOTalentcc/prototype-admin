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
