# Infrastructure — Canonical YAMLs Bundle (2026-04-24)

> Bundle dedicado com **verbatim dos 2 YAMLs canônicos de Infrastructure**
> (tool permissions + domain routing). Lido direto de `lia-agent-system/` no Replit em 2026-04-24. Tamanho total: 21.4 KB.
>
> **Fonte única de verdade:** o código em `lia-agent-system/`.
> **Guia de navegação:** `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md`.
> **Handoff dev:** `INFRASTRUCTURE_DEV_HANDOFF_2026-04-23.md` (Card 3 — Infrastructure).

---

## Como usar este bundle com AI assistants

### Claude Code (CLI)
Adicionar em `CLAUDE.md` do repo novo:
```
## Referência canônica — YAMLs de Infrastructure
Consulte `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md` para verbatim de qualquer YAML
da camada de infrastructure antes de replicar.
```
Claude Code lerá `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md` automaticamente quando for replicar ou editar qualquer YAML listado.

### Cursor
Salvar em `.cursor/rules/infrastructure-yamls.mdc`:
```
---
description: Verbatim canônico dos YAMLs da camada de Infrastructure
alwaysApply: false
---
Este arquivo é a fonte verbatim dos YAMLs de Infrastructure. Quando usuário pedir
para replicar, editar ou consultar qualquer YAML listado aqui, use o
conteúdo exato deste bundle.
```
Invocar na chat via: `@infrastructure-yamls replica o <nome>.yaml`

### Manual (ctrl+F)
Busque pelo nome do YAML (ex.: `cv_screening.yaml`). Cada YAML tem header com:
- Path canônico no Replit
- Linhas / bytes / versão / data de atualização
- Formato estrutural (A/B/C/D/E) para domain YAMLs
- Bloco ```yaml com verbatim completo

---

## Índice (2 YAMLs)

| # | YAML | Path canônico | Linhas | Versão | Updated |
|---|---|---|---|---|---|
| 1 | `tool_permissions.yaml` | `app/tools/tool_permissions.yaml` | 251 | 1.0 | — |
| 2 | `domain_routing.yaml` | `app/orchestrator/config/domain_routing.yaml` | 397 | 1.0 | — |

---

## Princípios de fidelidade

- Todo byte de YAML foi lido direto de `lia-agent-system/` (Replit) em 2026-04-24. Zero paráfrase, zero invenção.
- **Código é fonte de verdade.** Se divergir do bundle, abrir issue para atualizar o bundle (bug de staleness).
- Atualização: triggered por mudança em YAML canônico + revisão trimestral.
- Cross-reference para outros bundles: ver sessão inicial.

## Cross-references com outros bundles

- **Persona + Agent prompts** (lia_persona, compliance_block, guardrails_block, agent_prompts, defensive + 24 domain prompts + intelligence_floor) → `LIA_YAMLS_CANONICAL_BUNDLE.md`
- **Compliance técnico** (protected_attributes, fairness_post_check) → `COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md`
- **Infraestrutura** (tool_permissions, domain_routing) → `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md`

---

## YAMLs canônicos de Infrastructure

Technical config consumido pelo ToolRegistry, tool_handler decorator e CascadedRouter. Não é injetado em prompt — é lido por código Python.

### Arquivo canônico: `app/tools/tool_permissions.yaml`

**Linhas:** 251  |  **Bytes:** 8046  |  **Versão:** 1.0

```yaml
version: '1.0'
global:
  scopes:
    talent_funnel:
      query:
      - search_candidates
      - get_candidate_details
      - get_candidate_stats
      - compare_candidates
      - get_talent_quality
      - get_talent_engagement
      - get_talent_availability
      - get_diversity_metrics
      - get_candidate_history
      - get_ml_predictions
      - get_conversion_patterns
      - analyze_skill_gaps
      - map_candidate_skills_to_ontology
      - match_internal_candidates
      - get_engagement_metrics
      action:
      - add_candidate_to_vacancy
      - reject_candidate
      - shortlist_candidate
      - add_to_list
      - hide_candidate
      - send_email
      - send_whatsapp
      - send_bulk_email
      - export_candidates
      - create_nurture_sequence
      - suggest_reengagement
    job_table:
      query:
      - search_jobs
      - get_job_details
      - get_pipeline_stats
      - get_recruiter_metrics
      - get_velocity_metrics
      - get_efficiency_metrics
      - get_comparative_metrics
      - get_workload_distribution
      - get_hiring_quality
      - get_cost_metrics
      - get_trends
      - get_market_benchmarks
      action:
      - create_job
      - update_job
      - pause_job
      - close_job
      - publish_job
      - export_job_analytics
      - generate_report
    in_job:
      query:
      - get_job_details
      - get_vacancy_funnel
      - get_candidate_details
      - get_activity_summary
      - get_pending_actions
      - compare_candidates
      - get_candidate_stats
      - get_bottleneck_analysis
      - get_job_velocity
      - get_job_quality_metrics
      - get_stakeholder_metrics
      - get_prediction_metrics
      - get_job_benchmark
      - get_smart_alerts
      - analyze_interview_recording
      action:
      - update_candidate_stage
      - bulk_update_candidates_stage
      - reject_candidate
      - shortlist_candidate
      - add_to_list
      - hide_candidate
      - wsi_screening
      - send_email
      - send_whatsapp
      - schedule_interview
      - send_feedback
    global:
      query:
      - infer_related_skills
      - get_skill_adjacencies
      - forecast_hiring_needs
      - get_market_intelligence
      action:
      - generate_report
      - schedule_report
      - analyze_cv_match
      - create_and_screen_candidate
      - parse_and_create_candidate
      - add_to_vacancy
    universal:
      query:
      - search_candidates
      - get_candidate_details
      - get_candidate_stats
      - compare_candidates
      - get_talent_quality
      - get_talent_engagement
      - get_talent_availability
      - get_diversity_metrics
      - get_candidate_history
      - get_ml_predictions
      - get_conversion_patterns
      - search_jobs
      - get_job_details
      - get_pipeline_stats
      - get_recruiter_metrics
      - get_velocity_metrics
      - get_efficiency_metrics
      - get_comparative_metrics
      - get_workload_distribution
      - get_hiring_quality
      - get_cost_metrics
      - get_trends
      - get_market_benchmarks
      - get_vacancy_funnel
      - get_activity_summary
      - get_pending_actions
      - get_bottleneck_analysis
      - get_job_velocity
      - get_job_quality_metrics
      - get_stakeholder_metrics
      - get_prediction_metrics
      - get_job_benchmark
      - get_smart_alerts
      - infer_related_skills
      - get_skill_adjacencies
      - analyze_skill_gaps
      - map_candidate_skills_to_ontology
      - match_internal_candidates
      - forecast_hiring_needs
      - analyze_interview_recording
      - get_engagement_metrics
      - get_market_intelligence
      - suggest_reengagement
      action:
      - add_candidate_to_vacancy
      - add_to_list
      - add_to_vacancy
      - analyze_cv_match
      - bulk_update_candidates_stage
      - close_job
      - create_and_screen_candidate
      - create_job
      - create_sourcing_agent
      - export_candidates
      - export_job_analytics
      - generate_report
      - hide_candidate
      - parse_and_create_candidate
      - pause_job
      - publish_job
      - reject_candidate
      - schedule_interview
      - schedule_report
      - send_bulk_email
      - send_email
      - send_feedback
      - send_whatsapp
      - shortlist_candidate
      - update_candidate_stage
      - update_job
      - wsi_screening
      - create_nurture_sequence
      - suggest_reengagement
    company_settings:
      query:
      - get_company_profile
      - get_company_completion
      action:
      - save_company_field
      - save_company_section
      - analyze_company_website
      - process_uploaded_document
      - import_workforce_plan
  llm_provider: gemini
  llm_fallback_order:
  - gemini
  - claude
  - openai

# ── RESTRICTED TOOLS ─────────────────────────────────────────────────────────
# Tools that require explicit user confirmation before execution (OWASP LLM06).
# Any tool matching dangerous keywords (delete/remove/purge/bulk/export/config/
# permission/close/cancel/reject/hide) MUST be listed here.
# The ActionExecutor and orchestrator check this list to enforce HITL guardrails.
restricted_tools:
  # Destructive / removal actions
  - reject_candidate          # permanently reject from pipeline
  - hide_candidate            # soft-delete from view
  - cancel_vacancy            # cancel entire job opening
  - close_job                 # close job permanently
  - pause_job                 # pause job (reversible but impactful)
  - pause_vacancy             # pause vacancy with reason
  # Bulk / batch operations
  - bulk_update_candidates_stage  # move many candidates at once
  - send_bulk_email           # mass email to candidates
  # Export / data extraction
  - export_candidates         # export candidate PII data
  - export_job_analytics      # export analytics data
  # Configuration / settings
  - get_company_config        # read company configuration
  # Communication (irreversible sends)
  - send_email                # send individual email
  - send_whatsapp             # send WhatsApp message
  - send_feedback             # send feedback to candidate
  # Pipeline stage changes
  - update_candidate_stage    # move candidate between stages
  # Job publishing (external visibility)
  - publish_job               # make job publicly visible
  - publish_to_job_board      # publish to external boards
  # Autonomous actions
  - confirm_autonomous_action # confirm AI-initiated action
  # Hiring decisions
  - confirm_placement         # confirm hire decision
  - create_offer_letter       # generate offer letter
  - record_hiring_outcome     # record hiring result

  # Job creation/modification (structural changes)
  - create_job                # create new job vacancy
  - update_job                # modify existing job
  # Report scheduling
  - schedule_report           # schedule automated report delivery
  # Pool operations
  - move_pool_to_job          # move talent pool candidates to job
  # Agent management
  - create_sourcing_agent     # create AI sourcing agent
  - calibrate_sourcing_agent  # recalibrate agent parameters
  # Campaign operations
  - advance_campaign_stage    # advance recruitment campaign stage
  # Autonomous action rejection
  - reject_autonomous_action  # reject AI-initiated autonomous action
  # Company settings (write operations)
  - save_company_field         # modify company profile data
  - save_company_section       # bulk modify company section
  - analyze_company_website    # external HTTP call to scrape website
  - import_workforce_plan      # import workforce planning data

# Per-tenant LLM provider config (`llm_provider` / `llm_fallback_order`)
# is intentionally NOT supported here — that data lives in the
# `tenant_llm_configs` database table (see ADR-016 / Task #353).
# Only per-tenant scope `overrides` are honoured under `tenants:` going
# forward.
tenants: {}
```

### Arquivo canônico: `app/orchestrator/config/domain_routing.yaml`

**Linhas:** 397  |  **Bytes:** 13904  |  **Versão:** 1.0

**Descrição:** Domain-level keyword/regex routing (LIA-I05 / Fase 5 cutover). Loaded by fast_router.py at startup. Each domain has a list of regex patterns. First-match wins (with confidence scoring in matcher). Whe

```yaml
version: "1.0"

description: |
  Domain-level keyword/regex routing (LIA-I05 / Fase 5 cutover).
  Loaded by fast_router.py at startup. Each domain has a list of regex patterns.
  First-match wins (with confidence scoring in matcher).
  When adding a new domain or pattern, restart the worker to pick up changes.
  No code change needed — config-as-data.

domains:
  job_management:
    # ── Leitura / Listagem (BUG-17 fix: sem esses patterns, "listar vagas" caía no
    # genérico \bvaga\b e era roteado para job_wizard, que não tem list_jobs no
    # tool registry. Padrões específicos primeiro para ancorar leitura antes de criação)
    - "list(a|ar|ando|e|em|ei)?\\s+(\\w+\\s+)*vagas?"
    - "ver\\s+(\\w+\\s+)*vagas?"
    - "mostrar?\\s+(\\w+\\s+)*vagas?"
    - "minhas?\\s+vagas?"
    - "quais\\s+(\\w+\\s+)*vagas?"
    - "quantas\\s+vagas?"
    - "vagas?\\s+(abertas?|ativas?|em\\s+aberto|em\\s+andamento|pendentes?|fechadas?|pausadas?|canceladas?)"
    # English patterns (EX-007 resilience)
    - "show\\s+(me\\s+)?(the\\s+)?(active\\s+)?jobs?"
    - "list\\s+(me\\s+)?(all\\s+)?(active\\s+)?jobs?"
    - "get\\s+(me\\s+)?(the\\s+)?jobs?"
    - "\\bactive\\s+jobs?\\b"
    - "ranking\\s+d[eo]?\\s+vagas?"
    - "\\bfunil\\s+d[ae]\\s+vaga"
    - "detalhes\\s+d[ae]\\s+vaga"
    # ── Criação / Edição
    - "criar?\\s+\\w*\\s*vaga"
    - "nova\\s+vaga"
    - "editar?\\s+\\w*\\s*vaga"
    - "atualizar?\\s+\\w*\\s*vaga"
    - "gerar?\\s+jd"
    - "job\\s+description"
    - "descri[çc][ãa]o\\s+d[aeo]\\s+vaga"
    - "wizard"
    - "requisitos\\s+d[aeo]"
    - "clonar?\\s+\\w*\\s*vaga"
    - "fechar?\\s+\\w*\\s*vaga"
    - "publicar?\\s+\\w*\\s*vaga"
    - "pausar?\\s+\\w*\\s*vaga"
    - "template\\s+d[aeo]\\s+vaga"
    - "\\bvaga\\b"
    - "compet[eê]ncias"
    - "sal[áa]rio"
    - "sal[aá]rio\\s+da\\s+vaga"
    - "atualiz\\w*\\s+\\w+\\s+sal[aá]rio\\s+da\\s+vaga"
    - "benef[ií]cios"
    - "enrichment"
  sourcing:
    - "buscar?\\s+\\w*\\s*candidato"
    - "pesquisar?\\s+\\w*\\s*candidato"
    - "encontrar?\\s+\\w*\\s*candidato"
    - "pearch"
    - "boolean\\s+search"
    - "busca\\s+booleana"
    - "string\\s+booleana"
    - "talent\\s+pool"
    - "sourcing"
    - "atrair?\\s+\\w*\\s*candidato"
    - "ranking\\s+d[eo]"
    - "top\\s+\\d+\\s+candidato"
    - "filtrar?\\s+\\w*\\s*candidato"
    - "melhor\\s+match\\s+para\\s+(?:a\\s+)?vaga"
    - "match.*candidatos.*vaga"
  sourcing_planner:
    - "crit[eé]rios\\s+de\\s+busca"
    - "definir?\\s+\\w*\\s*crit[eé]rios"
    - "par[aâ]metros\\s+de\\s+busca"
    - "configurar?\\s+\\w*\\s*busca"
    - "sugerir?\\s+\\w*\\s*skills?"
    - "sugest[aã]o\\s+de\\s+skills?"
  sourcing_search:
    - "busca\\s+de\\s+talentos"
    - "talent\\s+search"
    - "ver\\s+perfil\\s+d[eo]\\s+candidato"
    - "exibir?\\s+\\w*\\s*candidatos?"
    - "listar?\\s+candidatos?\\s+encontrados?"
  sourcing_enrich:
    - "analisar?\\s+\\w*\\s*perfil"
    - "comparar?\\s+\\w*\\s*candidatos?"
    - "score\\s+d[eo]\\s+candidato"
    - "\\bshortlist\\b"
    - "adicionar?\\s+\\w*\\s*shortlist"
    - "ranking\\s+d[eo]\\s+candidatos?"
    - "avaliar?\\s+\\w*\\s*perfil"
  sourcing_engagement:
    - "abordagem\\s+d[eo]\\s+candidato"
    - "enviar?\\s+\\w*\\s*abordagem"
    - "mensagem\\s+de\\s+abordagem"
    - "contatar?\\s+\\w*\\s*candidato"
    - "rastrear?\\s+\\w*\\s*resposta"
    - "\\boutreach\\b"
    - "gerar?\\s+\\w*\\s*mensagem\\s+d[eo]\\s+contato"
  cv_screening:
    - "triagem"
    - "analisar?\\s+\\w*\\s*cv"
    - "analisar?\\s+\\w*\\s*curr[ií]culo"
    - "red\\s*flags?"
    - "screening"
    - "parsear?\\s+cv"
    - "extrair?\\s+dados?\\s+d[eo]?\\s*cv"
    - "avaliar?\\s+\\w*\\s*curr[ií]culo"
    - "pontua[çc][ãa]o\\s+d[eo]\\s+cv"
  wsi_assessment:
    - "score\\s+wsi"
    - "avaliar?\\s+\\w*\\s*candidato"
    - "avalia[çc][ãa]o\\s+wsi"
    - "\\bwsi\\b"
    - "\\bbloom\\b"
    - "\\bdreyfus\\b"
    - "big\\s*five"
    - "compet[eê]ncia\\s+comportamental"
    - "eligibilidade"
    - "calibra[çc][ãa]o"
    - "senioridade"
    - "perguntas?\\s+wsi"
    - "question[áa]rio"
  interviewing:
    - "entrevistar?"
    - "entrevista\\b"
    - "transcrever?\\s+\\w*\\s*entrevista"
    - "voice\\s+screening"
    - "voice\\s+interview"
    - "gravar?\\s+\\w*\\s*entrevista"
    - "iniciar?\\s+\\w*\\s*entrevista"
  scheduling:
    - "agendar?\\s+\\w*\\s*entrevista"
    - "reagendar?\\s+\\w*\\s*entrevista"
    - "cancelar?\\s+\\w*\\s*entrevista"
    - "hor[áa]rio\\s+dispon[ií]vel"
    - "marcar?\\s+\\w*\\s*entrevista"
    - "agendar?\\s+\\w*\\s*reuni[ãa]o"
    - "calend[áa]rio"
    - "disponibilidade\\s+de\\s+hor[áa]rio"
    - "agendar?\\b"
    - "reagendar?\\b"
  communication:
    - "enviar?\\s+\\w*\\s*email"
    - "enviar?\\s+\\w*\\s*whatsapp"
    - "enviar?\\s+\\w*\\s*mensagem"
    - "template\\s+d[aeo]\\s+email"
    - "notifica[çc][ãa]o"
    - "comunicar?\\s+\\w*\\s*candidato"
    - "feedback\\s+para?\\s+\\w*\\s*candidato"
    - "\\bteams\\b"
    - "mand[ao].*\\bwhatsapp\\b"
    - "mand[ao].*\\b(email|mensagem)\\b"
    - "convid[ao]\\w*.*\\bentrevista\\b"
    - "email\\s+de\\s+rejei[çc][aã]o"
  kanban_search:
    - "pipeline\\s+(da|dessa|desta|do|de)\\s+vaga"
    - "como\\s+est[áa]\\s+(essa|a|o)\\s+vaga"
    - "\\bver\\s+\\w*\\s*candidato"
    - "\\blistar?\\s+\\w*\\s*candidato"
    - "\\bmostrar?\\s+\\w*\\s*candidato"
    - "quem\\s+est[áa]\\s+em"
    - "candidatos?\\s+na\\s+etapa"
    - "resumo\\s+d[eo]\\s+pipeline"
    - "m[ée]tricas?\\s+da\\s+etapa"
    - "benchmarks?\\s+d[eo]\\s+pipeline"
    - "velocidade\\s+d[eo]\\s+pipeline"
    - "pipeline_velocity"
    - "\\bkanban\\b"
    - "etapa\\s+d[eo]"
    - "funil\\s+de\\s+recrutamento"
  kanban_insight:
    - "gargalo[s]?\\s+d[eo]\\s+pipeline"
    - "gargalo[s]?\\b"
    - "bottleneck[s]?"
    - "previs[ãa]o\\s+de\\s+fechamento"
    - "previs[ãa]o\\s+d[eo]\\s+pipeline"
    - "candidatos?\\s+em\\s+risco"
    - "\\bat.?risk\\b"
    - "aging\\s+d[eo]\\s+candidato"
    - "tempo\\s+na\\s+etapa"
    - "analisar?\\s+etapa"
    - "comparar?\\s+etapas?"
    - "sugerir?\\s+movimenta[çc][ãa]o"
    - "jornada\\s+d[eo]\\s+candidato"
    - "pipeline.?prediction"
    - "an[áa]lise\\s+d[eo]\\s+funil"
    - "identify.?bottleneck"
  kanban_action:
    - "mover?\\s+\\w*\\s*candidato"
    - "mover?\\s+em\\s+lote"
    - "aprovar?\\s+\\w*\\s*candidato"
    - "rejeitar?\\s+\\w*\\s*candidato"
    - "reprovar?\\s+\\w*\\s*candidato"
    - "triagem\\s+em\\s+lote"
    - "triagem\\s+batch"
    - "comunicac[ao][ãa]o\\s+em\\s+massa"
    - "mensagem\\s+em\\s+massa"
    - "relat[óo]rio\\s+d[eo]\\s+pipeline"
    - "prata\\s+da\\s+casa"
    - "silver\\s+medalist"
    - "backlog\\s+d[eo]\\s+recrutador"
    - "benchmark\\s+d[eo]\\s+recrutador"
    - "compara[çc][ãa]o\\s+d[eo]\\s+candidato"
  pipeline_context:
    - "perfil\\s+d[eo]\\s+candidato"
    - "scores?\\s+wsi"
    - "resultado\\s+da\\s+triagem"
    - "sal[áa]rio\\s+d[eo]\\s+candidato"
    - "disponibilidade\\s+d[eo]\\s+candidato"
    - "contexto\\s+da\\s+vaga"
    - "sub.?status\\s+dispon"
    - "get_candidate_profile"
    - "get_candidate_wsi"
  pipeline_decision:
    - "validar?\\s+transi[çc][ãa]o"
    - "sub.?status\\s+suger"
    - "prefer[eê]ncias?\\s+d[eo]\\s+recrutador"
    - "coletar?\\s+dados?\\s+d[eo]\\s+candidato"
    - "agendar?\\s+tarefa\\s+secund[áa]ria"
    - "validate.?transition"
    - "suggest.?sub.?status"
    - "recruiter.?preference"
  pipeline_action:
    - "atualizar?\\s+\\w*\\s*candidato"
    - "personalizar?\\s+comunica[çc][ãa]o"
    - "cancelar?\\s+\\w*\\s*entrevista"
    - "reagendar?\\s+\\w*\\s*entrevista"
    - "detalhes?\\s+da\\s+entrevista"
    - "update.?candidate.?field"
    - "personalize.?communication"
    - "reschedule.?interview"
    - "cancel.?interview"
    - "atualiza\\s+o?\\s+(email|telefone|celular|linkedin|cargo|empresa|cidade|estado|modelo\\s+de\\s+trabalho|forma[çc][aã]o|idiomas?|disponibilidade)"
    - "atualizar?\\s+campo"
    - "muda\\s+o?\\s+(email|telefone|celular|linkedin|cargo|empresa|cidade|estado|modelo\\s+de\\s+trabalho|forma[çc][aã]o|idiomas?|disponibilidade)"
    - "troca\\s+o?\\s+(email|telefone|celular|linkedin|cargo|empresa|cidade|estado|modelo\\s+de\\s+trabalho|forma[çc][aã]o|idiomas?|disponibilidade)"
  analytics:
    - "gerar?\\s+relat[óo]rio"
    - "relat[óo]rio\\b"
    - "dashboard"
    - "kpi"
    - "m[ée]trica"
    - "estat[ií]stica"
    - "an[áa]lise\\s+d[aeo]"
    - "exportar?\\s+\\w*\\s*candidato"
    - "exportar?\\s+\\w*\\s*dados"
    - "report"
    - "tempo\\s+m[eé]dio\\s+de\\s+contrata"
    - "[íi]ndice\\s+de\\s+diversidade"
    - "diversidade\\s+das?\\s+contrata"
    - "time.?to.?hire"
    - "taxa\\s+de\\s+convers[aã]o"
  ats_integration:
    - "sync\\s+ats"
    - "sincronizar?\\s+\\w*\\s*ats"
    - "\\bgupy\\b"
    - "pandap[eé]"
    - "merge\\s+ats"
    - "importar?\\s+d[eo]\\s+ats"
    - "integra[çc][ãa]o\\s+ats"
  recruiter_assistant:
    - "briefing"
    - "meu\\s+dia"
    - "resumo\\s+d[eo]\\s+dia"
    - "resumo\\s+di[aá]rio"
    - "sum[aá]rio\\s+d[eo]\\s+dia"
    - "minha\\s+agenda"
    - "agenda\\s+de\\s+hoje"
    - "agenda\\s+de\\s+amanhã"
    - "agenda\\s+dessa?\\s+semana"
    - "compromissos?\\s+de\\s+hoje"
    - "compromissos?\\s+de\\s+amanhã"
    - "entrevistas?\\s+de\\s+hoje"
    - "entrevistas?\\s+de\\s+amanhã"
    - "o\\s+que\\s+tenho\\s+hoje"
    - "o\\s+que\\s+tenho\\s+amanhã"
    - "o\\s+que\\s+preciso\\s+fazer\\s+hoje"
    - "tarefas?\\s+de\\s+hoje"
    - "tarefas?\\s+pendentes?"
    - "sugest[ãõ]es?\\s+proativa"
    - "assist[eê]ncia"
    - "\\bajuda\\b"
    - "como\\s+funciona"
    - "o\\s+que\\s+[eé]\\s+o?\\s+m[oó]dulo"
    - "explica\\s+o\\s+m[oó]dulo"
    - "para\\s+que\\s+serve"
    - "como\\s+us[ao]"
    - "me\\s+explica"
    - "o\\s+que\\s+[eé]\\s+[ao]?\\s*\\blia\\b"
    - "help\\b"
  task_planning:
    - "tarefa"
    - "planejar?\\s+tarefa"
    - "delegar?\\s+tarefa"
    - "criar?\\s+tarefa"
    - "to[\\s-]?do"
    - "lista\\s+de?\\s+tarefas"
    - "pr[óo]ximos?\\s+passos?"
    - "lembrete"
    - "me\\s+lembra"
    - "me\\s+avisa"
    - "cria\\s+um\\s+lembrete"
    - "criar?\\s+lembrete"
    - "anot[ao]"
    - "criar?\\s+nota"
    - "salva\\s+uma?\\s+nota"
    - "nota\\s+sobre"
  interview_scheduling:
    - "criar?\\s+compromisso"
    - "novo\\s+compromisso"
    - "agendar?\\s+reuni[aã]o"
    - "agendar?\\s+call"
    - "agendar?\\s+alinhamento"
    - "criar?\\s+evento"
    - "compromisso\\s+no\\s+calend[aá]rio"
    - "reuni[aã]o\\s+no\\s+calend[aá]rio"
  talent_pool:
    - "talent\\s+pool"
    - "pool\\s+de\\s+talentos?"
    - "banco\\s+de\\s+talentos?"
    - "banco\\s+vivo"
    - "bancos?\\s+vivos?"
    - "criar\\s+\\w*\\s*pool"
    - "mover\\s+\\w*\\s*pool\\s+\\w*\\s*vaga"
    - "candidatos?\\s+do\\s+pool"
  agent_studio:
    - "agent\\s+studio"
    - "studio\\s+de\\s+agentes?"
    - "criar\\s+\\w*\\s*agente"
    - "novo\\s+agente"
    - "ativar\\s+\\w*\\s*agente"
    - "calibra[rç]"
    - "recalibra[rç]"
    - "busca\\s+inteligente"
    - "multi.?estrat[eé]gia"
    - "4\\s+estrat[eé]gias?"
    - "templates?\\s+setor"
  digital_twin:
    - "digital\\s+twin"
    - "g[eê]meo\\s+digital"
    - "twin\\s+\\w*\\s*especialista"
    - "avaliar?\\s+com\\s+twin"
    - "segunda\\s+opini[aã]o"
    - "clon[ae]r?\\s+\\w*\\s*racioc[ií]nio"
    - "criar\\s+\\w*\\s*twin"
  recruitment_campaign:
    - "campanha\\s+\\w*\\s*recrutamento"
    - "criar\\s+\\w*\\s*campanha"
    - "nova\\s+campanha"
    - "fluxo\\s+completo"
    - "avan[cç]ar\\s+\\w*\\s*campanha"
    - "progresso\\s+\\w*\\s*campanha"
    - "workflow\\s+rail"
  # Task #320 — close routing for CompanySettingsReActAgent (W16/W19).
  # Intents that mutate company-level configuration: profile, branding,
  # culture, tech stack, default pipeline stages, corporate domain, policies.
  # Patterns are anchored on "empresa" / "companhia" / "organiza[cç][ãa]o"
  # or unambiguous company-config nouns (logo, logotipo, tech stack) to
  # avoid colliding with job_management ("benef[ií]cios", "compet[eê]ncias")
  # or kanban/pipeline domains.
  company_settings:
    - "configura[çc][ãa]o\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "configurar?\\s+\\w*\\s*(empresa|companhia|organiza[çc][ãa]o)"
    - "ajustes?\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "ajustar?\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "perfil\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "dados\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "pol[ií]tica[s]?\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "alterar?\\s+\\w*\\s*pol[ií]tica"
    - "atualizar?\\s+\\w*\\s*pol[ií]tica"
    - "mudar?\\s+\\w*\\s*pol[ií]tica"
    - "cultura\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "miss[ãa]o\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "valores\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "tech\\s+stack"
    - "stack\\s+t[eé]cnico"
    - "benef[ií]cios\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "etapas?\\s+padr[ãa]o"
    - "etapas?\\s+default"
    - "etapas?\\s+padronizadas?"
    - "atualizar?\\s+\\w*\\s*etapas?\\s+padr"
    - "configurar?\\s+\\w*\\s*etapas?\\s+padr"
    - "dom[ií]nio\\s+d[ae]\\s+(empresa|email|corporativo)"
    - "dom[ií]nio\\s+corporativo"
    - "trocar?\\s+\\w*\\s*dom[ií]nio"
    - "alterar?\\s+\\w*\\s*dom[ií]nio"
    - "mudar?\\s+\\w*\\s*dom[ií]nio"
    - "atualizar?\\s+\\w*\\s*dom[ií]nio"
    - "logo\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "\\blogotipo\\b"
    - "trocar?\\s+\\w*\\s*logo"
    - "mudar?\\s+\\w*\\s*logo"
    - "atualizar?\\s+\\w*\\s*logo"
    - "alterar?\\s+\\w*\\s*logo"
    - "subir\\s+\\w*\\s*logo"
    - "branding\\s+d[ae]\\s+(empresa|companhia|organiza[çc][ãa]o)"
    - "workforce\\s+planning"
    - "planejamento\\s+d[ae]\\s+for[çc]a\\s+de\\s+trabalho"
```

---

*Bundle gerado em 2026-04-24 | Próxima revisão: triggered por mudança em YAML canônico ou trimestral | Fonte: `lia-agent-system/` no Replit*
