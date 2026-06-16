# Infrastructure — Canonical YAMLs Bundle (2026-04-24)

> Bundle dedicado com **verbatim dos 21 YAMLs canônicos de Infrastructure**
> (tool permissions + domain routing + agents_registry + tool_registry_metadata + 17 capabilities). Lido direto de `lia-agent-system/` no Replit em 2026-04-24. Tamanho total: 98.9 KB.
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
Busque pelo nome do YAML (ex.: `cv_screening.yaml`). Cada YAML tem header com path canônico + linhas + bloco ```yaml verbatim.

---

## Índice (21 YAMLs)

| # | YAML | Grupo | Path canônico | Linhas | Versão | Updated |
|---|---|---|---|---|---|---|
| 1 | `tool_permissions.yaml` | technical_config | `app/tools/tool_permissions.yaml` | 251 | 1.0 | — |
| 2 | `domain_routing.yaml` | technical_config | `app/orchestrator/config/domain_routing.yaml` | 397 | 1.0 | — |
| 3 | `agents_registry.yaml` | technical_config | `app/agents_registry.yaml` | 117 | — | — |
| 4 | `tool_registry_metadata.yaml` | technical_config | `app/tools/tool_registry_metadata.yaml` | 1026 | — | — |
| 5 | `capabilities.yaml (agent_studio)` | capabilities | `app/domains/agent_studio/config/capabilities.yaml` | 43 | — | — |
| 6 | `capabilities.yaml (analytics)` | capabilities | `app/domains/analytics/config/capabilities.yaml` | 100 | — | — |
| 7 | `capabilities.yaml (ats_integration)` | capabilities | `app/domains/ats_integration/config/capabilities.yaml` | 97 | — | — |
| 8 | `capabilities.yaml (automation)` | capabilities | `app/domains/automation/config/capabilities.yaml` | 102 | — | — |
| 9 | `capabilities.yaml (candidate_self_service)` | capabilities | `app/domains/candidate_self_service/config/capabilities.yaml` | 33 | — | — |
| 10 | `capabilities.yaml (communication)` | capabilities | `app/domains/communication/config/capabilities.yaml` | 84 | — | — |
| 11 | `capabilities.yaml (company_settings)` | capabilities | `app/domains/company_settings/config/capabilities.yaml` | 80 | 1.0 | — |
| 12 | `capabilities.yaml (cv_screening)` | capabilities | `app/domains/cv_screening/config/capabilities.yaml` | 90 | — | — |
| 13 | `capabilities.yaml (digital_twin)` | capabilities | `app/domains/digital_twin/config/capabilities.yaml` | 14 | — | — |
| 14 | `capabilities.yaml (hiring_policy)` | capabilities | `app/domains/hiring_policy/config/capabilities.yaml` | 41 | — | — |
| 15 | `capabilities.yaml (interview_scheduling)` | capabilities | `app/domains/interview_scheduling/config/capabilities.yaml` | 96 | — | — |
| 16 | `capabilities.yaml (job_management)` | capabilities | `app/domains/job_management/config/capabilities.yaml` | 140 | — | — |
| 17 | `capabilities.yaml (pipeline)` | capabilities | `app/domains/pipeline/config/capabilities.yaml` | 22 | — | — |
| 18 | `capabilities.yaml (recruiter_assistant)` | capabilities | `app/domains/recruiter_assistant/config/capabilities.yaml` | 140 | — | — |
| 19 | `capabilities.yaml (recruitment_campaign)` | capabilities | `app/domains/recruitment_campaign/config/capabilities.yaml` | 15 | — | — |
| 20 | `capabilities.yaml (sourcing)` | capabilities | `app/domains/sourcing/config/capabilities.yaml` | 72 | — | — |
| 21 | `capabilities.yaml (talent_pool)` | capabilities | `app/domains/talent_pool/config/capabilities.yaml` | 20 | — | — |

---

## Princípios de fidelidade

- Todo byte de YAML foi lido direto de `lia-agent-system/` (Replit) em 2026-04-24. Zero paráfrase, zero invenção.
- **Código é fonte de verdade.** Se divergir do bundle, abrir issue para atualizar o bundle.
- Atualização: triggered por mudança em YAML canônico + revisão trimestral.

## Cross-references com outros bundles

- **Persona + Agent prompts + Platform manifest + Agent templates + Intelligence floor** → `LIA_YAMLS_CANONICAL_BUNDLE.md`
- **Compliance técnico** (protected_attributes, fairness_post_check) → `COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md`
- **Infraestrutura** (tool_permissions, domain_routing, agents_registry, tool_registry_metadata, 17 capabilities) → `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md`

---

## Parte 1 — Technical config (4 YAMLs)

Consumido por ToolRegistry, @tool_handler, CascadedRouter, AgentRegistryWatcher.

### Arquivo canônico: `app/tools/tool_permissions.yaml`

**Linhas:** 251  |  **Bytes:** 8046

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

**Linhas:** 397  |  **Bytes:** 13904

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

### Arquivo canônico: `app/agents_registry.yaml`

**Linhas:** 117  |  **Bytes:** 4384

```yaml
# Agent Registry — LIA Platform
# Source of truth for dynamic agent declarations.
# Hot-reload supported via AgentRegistryWatcher (app/core/agent_registry_watcher.py).
#
# Format per agent:
#   name: string (unique identifier, matches domain key in ReactAgentRegistry)
#   domain: string (domain label)
#   class_path: string (fully-qualified Python class path)
#   model_id: string (LLM model identifier)
#   system_prompt_path: string | null (path to system_prompt.py module)
#   enabled: bool (set false to disable without removing entry)

agents:
  - name: pipeline
    domain: pipeline
    class_path: app.domains.pipeline.agents.pipeline_transition_agent.PipelineTransitionAgent
    model_id: claude-sonnet-4-6
    system_prompt_path: app/domains/pipeline/agents/system_prompt.py
    enabled: true

  - name: sourcing
    domain: sourcing
    class_path: app.domains.sourcing.agents.sourcing_react_agent.SourcingReActAgent
    model_id: claude-sonnet-4-6
    system_prompt_path: app/domains/sourcing/agents/system_prompt.py
    enabled: true

  - name: wizard
    domain: wizard
    class_path: app.domains.job_management.agents.job_wizard_graph.JobWizardGraph
    model_id: claude-sonnet-4-6
    system_prompt_path: app/domains/job_management/agents/system_prompt.py
    enabled: true

  - name: talent
    domain: talent
    class_path: app.domains.talent.agents.talent_agent.TalentAgent
    model_id: claude-haiku-4-5-20251001
    system_prompt_path: null
    enabled: true

  - name: kanban
    domain: kanban
    class_path: app.domains.kanban.agents.kanban_agent.KanbanAgent
    model_id: claude-haiku-4-5-20251001
    system_prompt_path: null
    enabled: true

  - name: policy
    domain: policy
    class_path: app.domains.policy.agents.agent.PolicySetupAgent
    model_id: claude-haiku-4-5-20251001
    system_prompt_path: null
    enabled: true

  - name: jobs_management
    domain: jobs_management
    class_path: app.domains.job_management.agents.jobs_management_agent.JobsManagementReActAgent
    model_id: claude-sonnet-4-6
    system_prompt_path: null
    enabled: true

  - name: analytics
    domain: analytics
    class_path: app.domains.analytics.agents.analytics_react_agent.AnalyticsReActAgent
    model_id: claude-sonnet-4-6
    system_prompt_path: app/domains/analytics/agents/analytics_system_prompt.py
    enabled: true

  - name: ats_integration
    domain: ats_integration
    class_path: app.domains.ats_integration.agents.ats_integration_react_agent.ATSIntegrationReActAgent
    model_id: claude-haiku-4-5-20251001
    system_prompt_path: app/domains/ats_integration/agents/ats_integration_system_prompt.py
    enabled: true

  - name: automation
    domain: automation
    class_path: app.domains.automation.agents.automation_react_agent.AutomationReActAgent
    model_id: claude-haiku-4-5-20251001
    system_prompt_path: app/domains/automation/agents/automation_system_prompt.py
    enabled: true

  - name: communication
    domain: communication
    class_path: app.domains.communication.agents.communication_react_agent.CommunicationReActAgent
    model_id: claude-haiku-4-5-20251001
    system_prompt_path: app/domains/communication/agents/communication_system_prompt.py
    enabled: true

  - name: autonomous
    domain: autonomous
    class_path: app.domains.autonomous.agents.autonomous_react_agent.AutonomousReActAgent
    model_id: claude-sonnet-4-6
    system_prompt_path: null
    enabled: true

  # A3 — InterviewGraph (entrevistas / agendamento conversacional).
  # Composição com tenant_llm_context (provider escolhido via contextvar
  # por tenant) + AuditCallback + FairnessGuard + pii_masking já presentes.
  - name: interview_scheduling
    domain: interview_scheduling
    class_path: app.domains.interview_scheduling.agents.interview_graph.InterviewGraph
    model_id: claude-sonnet-4-6
    system_prompt_path: app/prompts/domains/interview_scheduling.yaml
    enabled: true

  # A4 — WSIInterviewGraph (entrevistas WSI síncronas).
  # Composição com tenant_llm_context para WSIScreeningPipeline +
  # AuditCallback + FairnessGuard + pii_masking já presentes.
  - name: wsi_interview
    domain: wsi_interview
    class_path: app.domains.cv_screening.agents.wsi_interview_graph.WSIInterviewGraph
    model_id: claude-sonnet-4-6
    system_prompt_path: app/prompts/domains/wsi_interview.yaml
    enabled: true
```

### Arquivo canônico: `app/tools/tool_registry_metadata.yaml`

**Linhas:** 1026  |  **Bytes:** 35798

```yaml
# Tool Registry Metadata — Sprint G5
# Source of truth for tool declarations (descriptions, allowed_agents, scope).
# Handlers remain in Python. This file is validated at startup via ToolRegistry.validate_yaml().
#
# Format per tool:
#   name: string (unique identifier)
#   description: string (sent to LLM)
#   allowed_agents: list of agent type strings
#   scope: TALENT_FUNNEL | JOB_TABLE | IN_JOB | GLOBAL
#   version: semver string
#   parameters: JSON Schema object

tools:

  # ── Job Wizard Tools ───────────────────────────────────────────────────────

  - name: search_salary_benchmark
    description: Search for salary benchmark data for a given job role, seniority, and location.
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [job_title]
      properties:
        job_title: {type: string}
        seniority: {type: string}
        location: {type: string}
        industry: {type: string}

  - name: validate_job_fields
    description: Validate job creation fields and check for missing required information.
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [fields]
      properties:
        fields: {type: object}

  - name: get_job_suggestions
    description: Get AI-powered suggestions to improve a job description or requirements.
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [job_title]
      properties:
        job_title: {type: string}
        current_description: {type: string}
        industry: {type: string}

  - name: save_job_draft
    description: Save the current job vacancy as a draft to the database.
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [fields]
      properties:
        fields: {type: object}
        draft_id: {type: string}

  - name: get_company_config
    description: Get company configuration including hiring workflow and approval settings.
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      properties:
        config_type: {type: string}

  - name: get_intelligent_salary
    description: Get intelligent salary suggestions based on market data and company budget.
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [job_title]
      properties:
        job_title: {type: string}
        seniority: {type: string}
        location: {type: string}

  - name: get_intelligent_skills
    description: Get intelligent skill suggestions for a given job title and seniority.
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [job_title]
      properties:
        job_title: {type: string}
        seniority: {type: string}
        industry: {type: string}

  - name: capture_wizard_feedback
    description: Capture user feedback about the job creation wizard experience.
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [feedback_type, rating]
      properties:
        feedback_type: {type: string}
        rating: {type: integer}
        comment: {type: string}

  - name: generate_enriched_jd
    description: Generate an enriched job description based on collected fields and market data.
    allowed_agents: [job_planner, job_intake, orchestrator, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [fields]
      properties:
        fields: {type: object}
        tone: {type: string}

  # ── Candidate Tools ────────────────────────────────────────────────────────

  - name: update_candidate_stage
    description: Move a candidate to a different pipeline stage within a vacancy.
    allowed_agents: [orchestrator, recruiter_assistant, screening, analyst_feedback]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id, target_stage]
      properties:
        candidate_id: {type: string}
        target_stage: {type: string}
        job_id: {type: string}
        notes: {type: string}
        notify_candidate: {type: boolean}

  - name: add_candidate_to_vacancy
    description: Add a candidate from the talent pool to a specific vacancy.
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id, vacancy_id]
      properties:
        candidate_id: {type: string}
        vacancy_id: {type: string}
        stage: {type: string}
        notes: {type: string}

  - name: reject_candidate
    description: Reject a candidate from a vacancy with an optional reason.
    allowed_agents: [orchestrator, recruiter_assistant, screening, analyst_feedback]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id]
      properties:
        candidate_id: {type: string}
        vacancy_id: {type: string}
        reason: {type: string}
        notify: {type: boolean}

  - name: shortlist_candidate
    description: Add a candidate to a shortlist for a specific vacancy.
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id, vacancy_id]
      properties:
        candidate_id: {type: string}
        vacancy_id: {type: string}
        notes: {type: string}

  - name: bulk_update_candidates_stage
    description: Move multiple candidates to a new pipeline stage in bulk.
    allowed_agents: [orchestrator, recruiter_assistant, screening, analyst_feedback]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [candidate_ids, target_stage]
      properties:
        candidate_ids:
          type: array
          items: {type: string}
        target_stage: {type: string}
        job_id: {type: string}

  - name: add_to_list
    description: Add a candidate to a named candidate list (talent pool management).
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id, list_name]
      properties:
        candidate_id: {type: string}
        list_name: {type: string}
        notes: {type: string}

  - name: wsi_screening
    description: Initiate a WSI (Workforce Screening Interview) for a candidate.
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id, job_id]
      properties:
        candidate_id: {type: string}
        job_id: {type: string}
        screening_type: {type: string, enum: [voice, text, video]}

  - name: hide_candidate
    description: Hide a candidate from the active pipeline view (soft remove).
    allowed_agents: [orchestrator, recruiter_assistant, screening, analyst_feedback]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id]
      properties:
        candidate_id: {type: string}
        vacancy_id: {type: string}
        reason: {type: string}

  # ── Query / Analytics Tools ────────────────────────────────────────────────

  - name: search_candidates
    description: Search the talent pool for candidates matching specified criteria.
    allowed_agents: [orchestrator, recruiter_assistant, sourcing, analytics]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      properties:
        query: {type: string}
        filters: {type: object}
        limit: {type: integer}
        offset: {type: integer}

  - name: get_candidate_details
    description: Get full profile details for a specific candidate.
    allowed_agents: [orchestrator, recruiter_assistant, screening, analytics]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id]
      properties:
        candidate_id: {type: string}
        include_history: {type: boolean}

  - name: get_candidate_stats
    description: Get aggregate statistics about candidates in the talent pool.
    allowed_agents: [orchestrator, recruiter_assistant, analytics]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      properties:
        filters: {type: object}
        group_by: {type: string}

  - name: search_jobs
    description: Search job vacancies by title, status, department, or other criteria.
    allowed_agents: [orchestrator, recruiter_assistant, analytics, job_planner]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      properties:
        query: {type: string}
        status: {type: string}
        department: {type: string}
        limit: {type: integer}

  - name: get_job_details
    description: Get full details of a specific job vacancy including requirements and pipeline.
    allowed_agents: [orchestrator, recruiter_assistant, analytics, job_planner]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [job_id]
      properties:
        job_id: {type: string}
        include_candidates: {type: boolean}

  - name: get_pipeline_stats
    description: Get pipeline statistics for a specific vacancy or all vacancies.
    allowed_agents: [orchestrator, recruiter_assistant, analytics]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      properties:
        job_id: {type: string}
        date_range: {type: string}

  - name: get_vacancy_funnel
    description: Get funnel data for a specific vacancy showing candidates at each stage.
    allowed_agents: [orchestrator, recruiter_assistant, analytics]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [job_id]
      properties:
        job_id: {type: string}
        include_rejected: {type: boolean}

  # ── Export Tools ──────────────────────────────────────────────────────────

  - name: export_candidates
    description: Export candidate data to CSV or Excel format.
    allowed_agents: [orchestrator, recruiter_assistant, analytics]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      properties:
        candidate_ids:
          type: array
          items: {type: string}
        format: {type: string, enum: [csv, xlsx]}
        fields: {type: array, items: {type: string}}

  # ── Communication Tools ───────────────────────────────────────────────────

  - name: send_email
    description: Send an email to one or more candidates or recruiters.
    allowed_agents: [orchestrator, recruiter_assistant, communication]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [to, subject, body]
      properties:
        to:
          type: array
          items: {type: string}
        subject: {type: string}
        body: {type: string}
        template_id: {type: string}

  - name: send_whatsapp
    description: Send a WhatsApp message to a candidate phone number.
    allowed_agents: [orchestrator, recruiter_assistant, communication]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [phone, message]
      properties:
        phone: {type: string}
        message: {type: string}
        template_name: {type: string}

  # ── Job Management Tools ──────────────────────────────────────────────────

  - name: create_job
    description: Create a new job vacancy with the specified requirements and settings.
    allowed_agents: [orchestrator, job_planner, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [title, description]
      properties:
        title: {type: string}
        description: {type: string}
        department: {type: string}
        location: {type: string}
        salary_range: {type: object}
        requirements: {type: array, items: {type: string}}

  - name: update_job
    description: Update fields of an existing job vacancy.
    allowed_agents: [orchestrator, job_planner, job_wizard]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [job_id]
      properties:
        job_id: {type: string}
        fields: {type: object}

  - name: publish_job
    description: Publish a job vacancy to make it visible to candidates and job boards.
    allowed_agents: [orchestrator, job_planner]
    scope: JOB_TABLE
    version: "1.0"
    parameters:
      type: object
      required: [job_id]
      properties:
        job_id: {type: string}
        channels:
          type: array
          items: {type: string}

  # ── Global Tools ──────────────────────────────────────────────────────────

  - name: generate_report
    description: Generate a recruitment analytics report for a given date range and scope.
    allowed_agents: [orchestrator, analytics]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [report_type]
      properties:
        report_type: {type: string}
        date_from: {type: string}
        date_to: {type: string}
        format: {type: string, enum: [pdf, csv, json]}

  - name: schedule_report
    description: Schedule a recurring analytics report to be sent automatically.
    allowed_agents: [orchestrator, analytics]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [report_type, schedule, recipients]
      properties:
        report_type: {type: string}
        schedule: {type: string, description: "Cron expression"}
        recipients:
          type: array
          items: {type: string}

  # === Phase 6/8: New tools ===

  # Talent Pool (5)
  - name: create_talent_pool
    description: Create a new live talent pool with optional archetype
    allowed_agents: [talent_pool, recruiter_assistant, orchestrator]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [name]
      properties:
        name: {type: string}
        archetype_id: {type: string}
        description: {type: string}

  - name: list_talent_pools
    description: List active talent pools for the current company
    allowed_agents: [talent_pool, recruiter_assistant, orchestrator]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      properties:
        status: {type: string, enum: [active, paused, archived]}

  - name: add_to_talent_pool
    description: Add candidates to a talent pool
    allowed_agents: [talent_pool, sourcing, orchestrator]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [pool_id, candidate_ids]
      properties:
        pool_id: {type: string}
        candidate_ids: {type: array, items: {type: string}}

  - name: move_pool_to_job
    description: Move candidates from talent pool to a job vacancy
    allowed_agents: [talent_pool, orchestrator]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [pool_id, job_id, candidate_ids, target_stage]
      properties:
        pool_id: {type: string}
        job_id: {type: string}
        candidate_ids: {type: array, items: {type: string}}
        target_stage: {type: string}

  - name: get_pool_candidates
    description: List candidates in a talent pool with stage filtering
    allowed_agents: [talent_pool, recruiter_assistant, orchestrator]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [pool_id]
      properties:
        pool_id: {type: string}
        stage: {type: string, enum: [discovered, contacted, screening, screened, ready]}

  # Agent Studio (4)
  - name: create_sourcing_agent
    description: Create a persistent sourcing agent for a job or talent pool
    allowed_agents: [agent_studio, orchestrator]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [agent_name]
      properties:
        agent_name: {type: string}
        sector_template: {type: string}
        job_id: {type: string}
        talent_pool_id: {type: string}

  - name: calibrate_sourcing_agent
    description: Start calibration for a sourcing agent (trigger Big Card modal)
    allowed_agents: [agent_studio, orchestrator]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [agent_id]
      properties:
        agent_id: {type: string}

  - name: get_agent_status
    description: Get status, strategy, and metrics of a sourcing agent
    allowed_agents: [agent_studio, recruiter_assistant, orchestrator]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [agent_id]
      properties:
        agent_id: {type: string}

  - name: run_multi_strategy_search
    description: Execute 4 parallel search strategies (direct, adjacent, silver medalists, reengagement)
    allowed_agents: [agent_studio, sourcing, orchestrator]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [job_title]
      properties:
        job_title: {type: string}
        skills: {type: array, items: {type: string}}
        location: {type: string}
        seniority: {type: string}

  # Digital Twins (3)
  - name: create_digital_twin
    description: Create a Digital Twin from a Subject Matter Expert
    allowed_agents: [digital_twin, orchestrator]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [twin_name]
      properties:
        twin_name: {type: string}
        sme_user_id: {type: string}
        specialties: {type: array, items: {type: string}}

  - name: evaluate_with_twin
    description: Evaluate a candidate using a Digital Twin's reasoning (RAG few-shot)
    allowed_agents: [digital_twin, cv_screening, orchestrator]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [twin_id, candidate_id]
      properties:
        twin_id: {type: string}
        candidate_id: {type: string}
        job_id: {type: string}

  - name: list_digital_twins
    description: List available Digital Twins for the current company
    allowed_agents: [digital_twin, recruiter_assistant, orchestrator]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      properties: {}

  # Campaigns (3)
  - name: create_recruitment_campaign
    description: Create an end-to-end recruitment campaign for a job or pool
    allowed_agents: [recruitment_campaign, orchestrator]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [name]
      properties:
        name: {type: string}
        job_id: {type: string}
        talent_pool_id: {type: string}
        automation_level: {type: string, enum: [auto, semi, assisted]}

  - name: get_campaign_progress
    description: Get current stage and progress of a recruitment campaign
    allowed_agents: [recruitment_campaign, recruiter_assistant, orchestrator]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [campaign_id]
      properties:
        campaign_id: {type: string}

  - name: advance_campaign_stage
    description: Advance a recruitment campaign to the next stage
    allowed_agents: [recruitment_campaign, orchestrator]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [campaign_id]
      properties:
        campaign_id: {type: string}

  # Job Flow Completion (4)
  - name: create_offer_letter
    description: Generate an offer letter for a selected candidate
    allowed_agents: [pipeline_action, orchestrator]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id, job_id]
      properties:
        candidate_id: {type: string}
        job_id: {type: string}
        salary: {type: number}
        start_date: {type: string}

  - name: confirm_placement
    description: Confirm a candidate has been hired and close the position
    allowed_agents: [pipeline_action, orchestrator]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [candidate_id, job_id]
      properties:
        candidate_id: {type: string}
        job_id: {type: string}
        start_date: {type: string}

  - name: cancel_vacancy
    description: Cancel a job vacancy with a structured reason
    allowed_agents: [job_planner, orchestrator]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [job_id, reason]
      properties:
        job_id: {type: string}
        reason: {type: string, enum: [budget_cut, position_eliminated, internal_hire, other]}

  - name: pause_vacancy
    description: Pause a job vacancy with reason and expected resume date
    allowed_agents: [job_planner, orchestrator]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [job_id, reason]
      properties:
        job_id: {type: string}
        reason: {type: string}
        resume_date: {type: string}

  # Marketplace (3)
  - name: publish_to_job_board
    description: Publish a job vacancy to external job boards (LinkedIn, Indeed)
    allowed_agents: [job_planner, communication, orchestrator]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [job_id, board]
      properties:
        job_id: {type: string}
        board: {type: string, enum: [linkedin, indeed, gupy, glassdoor]}

  - name: get_external_applications
    description: Import applications from external job boards
    allowed_agents: [sourcing, orchestrator]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [job_id]
      properties:
        job_id: {type: string}
        board: {type: string}

  - name: search_candidates_pearch
    description: Search candidates using Pearch AI (800M+ profiles, consumes credits)
    allowed_agents: [sourcing, sourcing_search, agent_studio, orchestrator]
    scope: TALENT_FUNNEL
    version: "1.0"
    parameters:
      type: object
      required: [query]
      properties:
        query: {type: string}
        search_type: {type: string, enum: [fast, pro]}
        limit: {type: integer, maximum: 50}
        show_emails: {type: boolean}

  # ── Talent Intelligence: Skills Ontology ─────────────────────────────────

  - name: infer_related_skills
    description: Infer related skills from a set of input skills using the ontology graph with adjacency traversal and semantic proximity scoring
    allowed_agents: [orchestrator, recruiter_assistant, sourcing, analytics, job_planner, job_wizard]
    scope: GLOBAL
    version: "1.0"
    module: talent_intelligence_pro
    parameters:
      type: object
      required: [skills]
      properties:
        skills: {type: array, items: {type: string}}
        depth: {type: integer, minimum: 1, maximum: 3}
        limit: {type: integer, minimum: 1, maximum: 30}

  - name: get_skill_adjacencies
    description: Get adjacent skills for a given skill with proximity weights, domain classification, and relationship type from the skills ontology graph
    allowed_agents: [orchestrator, recruiter_assistant, sourcing, analytics, job_planner, job_wizard]
    scope: GLOBAL
    version: "1.0"
    module: talent_intelligence_pro
    parameters:
      type: object
      required: [skill]
      properties:
        skill: {type: string}
        min_weight: {type: number, minimum: 0, maximum: 1}

  - name: analyze_skill_gaps
    description: Analyze skill gaps between candidate and job requirements using ontology adjacencies, identifying matched, missing, and transferable skills with development suggestions
    allowed_agents: [orchestrator, recruiter_assistant, sourcing, analytics, screening]
    scope: TALENT_FUNNEL
    version: "1.0"
    module: talent_intelligence_pro
    parameters:
      type: object
      properties:
        candidate_skills: {type: array, items: {type: string}}
        required_skills: {type: array, items: {type: string}}
        candidate_id: {type: string}
        job_id: {type: string}

  - name: map_candidate_skills_to_ontology
    description: Map raw skill strings from a candidate profile to canonical ontology nodes with domain and specialization classification
    allowed_agents: [orchestrator, recruiter_assistant, sourcing, analytics, screening]
    scope: TALENT_FUNNEL
    version: "1.0"
    module: talent_intelligence_pro
    parameters:
      type: object
      properties:
        skills: {type: array, items: {type: string}}
        candidate_id: {type: string}

  # ── Talent Intelligence: Internal Mobility ───────────────────────────────

  - name: match_internal_candidates
    description: Match internal employees to an open position considering direct skill matches, adjacent/transferable skills via ontology, and development potential
    allowed_agents: [orchestrator, recruiter_assistant, analytics]
    scope: TALENT_FUNNEL
    version: "1.0"
    module: internal_mobility
    parameters:
      type: object
      properties:
        job_id: {type: string}
        required_skills: {type: array, items: {type: string}}
        job_title: {type: string}
        seniority: {type: string}
        department: {type: string}
        limit: {type: integer, minimum: 1, maximum: 50}

  # ── Talent Intelligence: Workforce Planning ──────────────────────────────

  - name: forecast_hiring_needs
    description: Forecast hiring needs based on historical turnover data, pipeline velocity, growth targets, and seasonality for a given time period
    allowed_agents: [orchestrator, recruiter_assistant, analytics]
    scope: GLOBAL
    version: "1.0"
    module: workforce_planning
    parameters:
      type: object
      properties:
        period: {type: string, enum: [month, quarter, half_year, year]}
        department: {type: string}
        growth_rate: {type: number}
        include_backfills: {type: boolean}

  # ── Talent Intelligence: Interview Intelligence ──────────────────────────

  - name: analyze_interview_recording
    description: "Análise completa de entrevista: WSI (Bloom, Dreyfus, CBI, Big Five) + detecção de viés + análise comparativa + parecer estratégico + feedback ao candidato."
    allowed_agents: [orchestrator, recruiter_assistant, screening, analytics]
    scope: IN_JOB
    version: "2.0"
    module: interview_intelligence
    parameters:
      type: object
      properties:
        interview_id: {type: string, description: "UUID da entrevista (busca do banco)"}
        transcript: {type: string, description: "Transcrição inline (fallback)"}
        candidate_id: {type: string}
        job_id: {type: string}
        interviewer_name: {type: string}
        interview_type: {type: string, enum: [behavioral, technical, cultural, final]}
        include_bias: {type: boolean, default: true}
        include_comparative: {type: boolean, default: true}
        include_opinion: {type: boolean, default: true}
        include_feedback: {type: boolean, default: true}

  - name: detect_interview_bias
    description: "Detectar viés em entrevista: padrões linguísticos + análise LLM. Identifica viés de idade, gênero, aparência, afinidade e perguntas ilegais."
    allowed_agents: [orchestrator, recruiter_assistant, screening, analytics]
    scope: IN_JOB
    version: "1.0"
    module: interview_intelligence
    parameters:
      type: object
      required: [interview_id]
      properties:
        interview_id: {type: string}
        use_llm: {type: boolean, default: true}

  - name: generate_interview_opinion
    description: "Gerar parecer estratégico de contratação: CONTRATAR / NÃO CONTRATAR / AVALIAR MAIS com evidências da transcrição."
    allowed_agents: [orchestrator, recruiter_assistant, screening, analytics]
    scope: IN_JOB
    version: "1.0"
    module: interview_intelligence
    parameters:
      type: object
      required: [interview_id]
      properties:
        interview_id: {type: string}

  - name: generate_candidate_feedback
    description: "Gerar feedback estruturado e construtivo para devolver ao candidato após entrevista."
    allowed_agents: [orchestrator, recruiter_assistant, screening, analytics]
    scope: IN_JOB
    version: "1.0"
    module: interview_intelligence
    parameters:
      type: object
      required: [interview_id]
      properties:
        interview_id: {type: string}

  - name: compare_interview_performance
    description: "Comparar performance do candidato vs. outros da mesma vaga com ranking, benchmarks e insights."
    allowed_agents: [orchestrator, recruiter_assistant, screening, analytics]
    scope: IN_JOB
    version: "1.0"
    module: interview_intelligence
    parameters:
      type: object
      required: [interview_id]
      properties:
        interview_id: {type: string}

  # ── Talent Intelligence: Passive Candidate Nurture ───────────────────────

  - name: create_nurture_sequence
    description: Create an automated nurture sequence to engage passive candidates over time with multi-channel touchpoints
    allowed_agents: [orchestrator, recruiter_assistant, communication, recruitment_campaign]
    scope: TALENT_FUNNEL
    version: "1.0"
    module: candidate_nurture
    parameters:
      type: object
      required: [candidate_ids]
      properties:
        candidate_ids: {type: array, items: {type: string}}
        template: {type: string, enum: [tech_talent, leadership, silver_medalist, general]}
        custom_name: {type: string}
        tags: {type: array, items: {type: string}}

  - name: get_engagement_metrics
    description: Get engagement metrics for nurture sequences including open rates, click rates, and conversion to applicant/hire
    allowed_agents: [orchestrator, recruiter_assistant, analytics, recruitment_campaign]
    scope: TALENT_FUNNEL
    version: "1.0"
    module: candidate_nurture
    parameters:
      type: object
      properties:
        sequence_id: {type: string}
        period: {type: string, enum: [week, month, quarter]}

  - name: suggest_reengagement
    description: Suggest inactive candidates for re-engagement based on inactivity period, past scores, and engagement signals
    allowed_agents: [orchestrator, recruiter_assistant, sourcing, recruitment_campaign]
    scope: TALENT_FUNNEL
    version: "1.0"
    module: candidate_nurture
    parameters:
      type: object
      properties:
        days_inactive: {type: integer, minimum: 7}
        limit: {type: integer, minimum: 1, maximum: 50}

  - name: get_market_intelligence
    description: Get real-time market intelligence for a role — salary benchmarks from external sources (web search + LLM parsing), demand trends, in-demand skills, and competitive analysis
    allowed_agents: [orchestrator, recruiter_assistant, sourcing, analyst_feedback, wsi_evaluator]
    scope: GLOBAL
    version: "1.0"
    module: talent_intelligence_pro
    parameters:
      type: object
      properties:
        job_title: {type: string, description: "Job title to research"}
        seniority: {type: string, description: "Seniority level (Junior, Pleno, Senior)"}
        location: {type: string, description: "Location for regional adjustment"}
        industry: {type: string, description: "Industry sector"}
        include_trends: {type: boolean, default: true}
      required: [job_title]

  # ── Proactive Intelligence Tools ────────────────────────────────────────────

  - name: get_proactive_alerts
    description: Get proactive pipeline alerts (stale candidates, SLA risks, bottlenecks, empty pipelines, high rejection rates)
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      properties:
        severity: {type: string, enum: [low, medium, high, critical]}
        category: {type: string}

  - name: get_autonomous_actions
    description: List autonomous actions executed or pending confirmation by LIA
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      properties:
        status: {type: string, enum: [pending, executed, all]}

  - name: confirm_autonomous_action
    description: Confirm a pending autonomous action for execution
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [action_id]
      properties:
        action_id: {type: string}

  - name: reject_autonomous_action
    description: Reject a pending autonomous action
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      required: [action_id]
      properties:
        action_id: {type: string}
        reason: {type: string}

  - name: detect_pending_decisions
    description: Detect pending hiring manager decisions and send escalation notifications
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      properties:
        send_notifications: {type: boolean, default: false}

  - name: get_learning_insights
    description: Get insights from hiring outcome learning (successful patterns, ranking adjustments)
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: GLOBAL
    version: "1.0"
    parameters:
      type: object
      properties:
        role: {type: string}
        seniority: {type: string}

  - name: record_hiring_outcome
    description: Record a hiring outcome for learning (filled, cancelled, turnover)
    allowed_agents: [orchestrator, recruiter_assistant]
    scope: IN_JOB
    version: "1.0"
    parameters:
      type: object
      required: [job_id, candidate_id, outcome]
      properties:
        job_id: {type: string}
        candidate_id: {type: string}
        outcome: {type: string, enum: [filled, cancelled, expired, turnover]}
        satisfaction_score: {type: number, minimum: 1, maximum: 5}
        retention_days: {type: integer}
```

## Parte 2 — Intent capabilities por domínio (17 YAMLs)

Consumidos por `KeywordIntentMatcher` em cada `domain.py` para mapear keyword → intent antes de invocar agente.

### Arquivo canônico: `app/domains/agent_studio/config/capabilities.yaml`

**Linhas:** 43  |  **Bytes:** 1496

```yaml
domain: agent_studio

intent_keywords:
  criar agente: create_sourcing_agent
  novo agente: create_sourcing_agent
  ativar agente: create_sourcing_agent
  agente sourcing: create_sourcing_agent
  agent studio: list_agents
  studio agentes: list_agents
  calibrar: calibrate_agent
  calibração: calibrate_agent
  recalibrar: recalibrate_agent
  status agente: get_agent_status
  como está o agente: get_agent_status
  pausar agente: pause_agent
  parar agente: pause_agent
  templates setor: list_sector_templates
  templates disponíveis: list_sector_templates
  busca inteligente: run_multi_strategy
  multi estratégia: run_multi_strategy
  busca multi: run_multi_strategy
  4 estratégias: run_multi_strategy
  agente custom: create_custom_agent
  agente customizado: create_custom_agent
  criar custom: create_custom_agent
  novo custom: create_custom_agent
  listar custom: list_custom_agents
  meus agentes custom: list_custom_agents
  testar agente: test_custom_agent
  testar custom: test_custom_agent
  executar agente: execute_custom_agent
  executar custom: execute_custom_agent
  marketplace: browse_marketplace
  explorar marketplace: browse_marketplace
  publicar marketplace: publish_to_marketplace
  publicar agente: publish_to_marketplace
  instalar agente: install_from_marketplace
  instalar marketplace: install_from_marketplace
  atribuir crew: assign_to_crew
  adicionar crew: assign_to_crew
  consumo studio: get_studio_consumption
  uso agentes: get_studio_consumption
```

### Arquivo canônico: `app/domains/analytics/config/capabilities.yaml`

**Linhas:** 100  |  **Bytes:** 3814

```yaml
# capabilities.yaml — analytics domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: analytics

intent_keywords:
  relatório kpi: generate_kpi_report
  relatório de kpi: generate_kpi_report
  kpi report: generate_kpi_report
  gerar kpi: generate_kpi_report
  indicadores kpi: generate_kpi_report
  funil conversão: analyze_funnel
  funil de conversão: analyze_funnel
  analyze funnel: analyze_funnel
  métricas funil: analyze_funnel
  métricas do funil: analyze_funnel
  saúde vaga: job_health_check
  saúde da vaga: job_health_check
  job health: job_health_check
  health check: job_health_check
  verificar saúde: job_health_check
  detectar anomalia: detect_anomalies
  anomalia: detect_anomalies
  detect anomalies: detect_anomalies
  alerta anomalia: detect_anomalies
  comparar período: compare_periods
  comparar períodos: compare_periods
  compare periods: compare_periods
  comparação mensal: compare_periods
  comparação de períodos: compare_periods
  previsão: forecast
  previsão de métricas: forecast
  forecast: forecast
  projeção: forecast
  tendência: forecast
  sugerir estratégia: suggest_strategy
  estratégia recrutamento: suggest_strategy
  estratégia de recrutamento: suggest_strategy
  sugestão estratégica: suggest_strategy
  recomendação: suggest_strategy
  pergunta dados: answer_data_question
  pergunta sobre dados: answer_data_question
  data question: answer_data_question
  consulta dados: answer_data_question
  consulta de dados: answer_data_question
  insights vaga: get_job_insights
  insights da vaga: get_job_insights
  job insights: get_job_insights
  benchmark salarial: get_job_insights
  benchmark: get_job_insights
  salário médio: get_job_insights
  faixa salarial: get_job_insights
  faixa de mercado: get_job_insights
  faixa de remuneração: get_job_insights
  remuneração de mercado: get_job_insights
  salário de mercado: get_job_insights
  mercado paga: get_job_insights
  quanto paga o mercado: get_job_insights
  quanto o mercado paga: get_job_insights
  remuneração média: get_job_insights
  relatório vaga: generate_job_report
  relatório da vaga: generate_job_report
  job report: generate_job_report
  gerar relatório: generate_job_report
  relatório candidato: generate_candidate_report
  relatório de candidato: generate_candidate_report
  relatório comparativo: generate_candidate_report
  comparar candidatos: generate_candidate_report
  analytics busca: get_search_analytics
  analytics de busca: get_search_analytics
  search analytics: get_search_analytics
  desempenho busca: get_search_analytics
  desempenho de busca: get_search_analytics
  analytics wizard: get_wizard_analytics
  analytics do wizard: get_wizard_analytics
  wizard analytics: get_wizard_analytics
  uso do wizard: get_wizard_analytics
  probabilidade contratação: predict_hiring_probability
  probabilidade de contratação: predict_hiring_probability
  hiring probability: predict_hiring_probability
  chance de contratar: predict_hiring_probability
  tempo preenchimento: predict_time_to_fill
  tempo de preenchimento: predict_time_to_fill
  time to fill: predict_time_to_fill
  prazo da vaga: predict_time_to_fill
  risco desistência: predict_dropout_risk
  risco de desistência: predict_dropout_risk
  dropout risk: predict_dropout_risk
  candidato desistir: predict_dropout_risk
  dashboard: get_dashboard_data
  dados dashboard: get_dashboard_data
  dados do dashboard: get_dashboard_data
  painel indicadores: get_dashboard_data
  painel de indicadores: get_dashboard_data
  monitoramento agentes: get_agent_monitoring
  monitoramento de agentes: get_agent_monitoring
  agent monitoring: get_agent_monitoring
  performance agentes: get_agent_monitoring
  performance dos agentes: get_agent_monitoring
```

### Arquivo canônico: `app/domains/ats_integration/config/capabilities.yaml`

**Linhas:** 97  |  **Bytes:** 3445

```yaml
# capabilities.yaml — ats_integration domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: ats_integration

intent_keywords:
  sincronizar candidato: sync_candidate
  sync candidato: sync_candidate
  sync candidate: sync_candidate
  enviar candidato para ats: sync_candidate
  enviar candidato para o ats: sync_candidate
  sincronizar com ats: sync_candidate
  sincronizar vaga: sync_job
  sync vaga: sync_job
  sync job: sync_job
  enviar vaga para ats: sync_job
  enviar vaga para o ats: sync_job
  sincronização em massa: bulk_sync
  sync em massa: bulk_sync
  bulk sync: bulk_sync
  sincronizar tudo: bulk_sync
  sincronizar todos: bulk_sync
  importar candidatos: pull_candidates
  pull candidates: pull_candidates
  puxar candidatos: pull_candidates
  importar candidatos do ats: pull_candidates
  buscar candidatos no ats: pull_candidates
  importar vagas: pull_jobs
  pull jobs: pull_jobs
  puxar vagas: pull_jobs
  importar vagas do ats: pull_jobs
  status sincronização: check_sync_status
  status da sincronização: check_sync_status
  verificar sincronização: check_sync_status
  sync status: check_sync_status
  status do sync: check_sync_status
  configurar ats: configure_ats
  config ats: configure_ats
  setup ats: configure_ats
  conectar ats: configure_ats
  configurar integração ats: configure_ats
  listar conexões: list_connections
  conexões ats: list_connections
  list connections: list_connections
  ver conexões: list_connections
  quais ats conectados: list_connections
  testar conexão: test_connection
  test connection: test_connection
  verificar conexão: test_connection
  conexão ats: test_connection
  testar integração: test_connection
  mapear campos: map_fields
  mapeamento de campos: map_fields
  field mapping: map_fields
  configurar campos: map_fields
  map fields: map_fields
  log sincronização: view_sync_log
  log de sincronização: view_sync_log
  histórico sync: view_sync_log
  sync log: view_sync_log
  auditoria ats: view_sync_log
  auditoria do ats: view_sync_log
  conflito dados: resolve_conflict
  conflito de dados: resolve_conflict
  resolver conflito ats: resolve_conflict
  data conflict: resolve_conflict
  conflito sincronização: resolve_conflict
  conflito de sincronização: resolve_conflict
  atualizar status ats: update_status_ats
  atualizar status no ats: update_status_ats
  update status ats: update_status_ats
  enviar status para ats: update_status_ats
  push status: update_status_ats
  enviar score ats: send_score_ats
  enviar score para ats: send_score_ats
  enviar score para o ats: send_score_ats
  send score ats: send_score_ats
  enviar parecer ats: send_score_ats
  enviar parecer para ats: send_score_ats
  enviar parecer para o ats: send_score_ats
  sincronizar resultado entrevista: sync_interview_result
  sincronizar resultado da entrevista: sync_interview_result
  sync interview result: sync_interview_result
  enviar resultado entrevista ats: sync_interview_result
  ativar webhook: enable_webhook
  enable webhook: enable_webhook
  webhook ats: enable_webhook
  configurar webhook: enable_webhook
  desativar webhook: disable_webhook
  disable webhook: disable_webhook
  remover webhook: disable_webhook
  desabilitar webhook: disable_webhook
  ver mapeamento: view_field_mapping
  ver mapeamento de campos: view_field_mapping
  view field mapping: view_field_mapping
  campos mapeados: view_field_mapping
```

### Arquivo canônico: `app/domains/automation/config/capabilities.yaml`

**Linhas:** 102  |  **Bytes:** 3818

```yaml
# capabilities.yaml — automation domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: automation

intent_keywords:
  criar tarefa: create_task
  nova tarefa: create_task
  create task: create_task
  adicionar tarefa: create_task
  listar tarefas: list_tasks
  minhas tarefas: list_tasks
  list tasks: list_tasks
  tarefas pendentes: list_tasks
  ver tarefas: list_tasks
  concluir tarefa: complete_task
  completar tarefa: complete_task
  tarefa concluída: complete_task
  complete task: complete_task
  finalizar tarefa: complete_task
  cancelar tarefa: cancel_task
  cancel task: cancel_task
  remover tarefa: cancel_task
  decompor tarefa: decompose_task
  quebrar tarefa: decompose_task
  decompose task: decompose_task
  dividir tarefa: decompose_task
  subtarefas: decompose_task
  planejar execução: plan_execution
  plano de execução: plan_execution
  plan execution: plan_execution
  criar plano: plan_execution
  planejamento: plan_execution
  próximas tarefas: get_next_tasks
  próxima tarefa: get_next_tasks
  next tasks: get_next_tasks
  o que fazer agora: get_next_tasks
  tarefas prioritárias: get_next_tasks
  criar automação: create_automation
  nova automação: create_automation
  create automation: create_automation
  configurar automação: create_automation
  adicionar automação: create_automation
  listar automações: list_automations
  ver automações: list_automations
  list automations: list_automations
  automações configuradas: list_automations
  automações ativas: list_automations
  ativar automação: enable_automation
  enable automation: enable_automation
  habilitar automação: enable_automation
  ligar automação: enable_automation
  desativar automação: disable_automation
  disable automation: disable_automation
  desabilitar automação: disable_automation
  pausar automação: disable_automation
  desligar automação: disable_automation
  disparar automação: trigger_automation
  trigger automation: trigger_automation
  executar automação: trigger_automation
  rodar automação: trigger_automation
  log automação: view_automation_log
  log de automação: view_automation_log
  histórico automação: view_automation_log
  histórico de automação: view_automation_log
  automation log: view_automation_log
  automação de etapa: configure_stage_automation
  automação de estágio: configure_stage_automation
  stage automation: configure_stage_automation
  transição automática: configure_stage_automation
  automatizar etapa: configure_stage_automation
  automatizar transição: configure_stage_automation
  prever sub-status: predict_substatus
  prever substatus: predict_substatus
  predict substatus: predict_substatus
  próximo status: predict_substatus
  previsão de status: predict_substatus
  alertas proativos: check_proactive_alerts
  verificar alertas: check_proactive_alerts
  proactive alerts: check_proactive_alerts
  alertas pendentes: check_proactive_alerts
  meus alertas: check_proactive_alerts
  configurar alerta: configure_alert
  criar alerta: configure_alert
  configure alert: configure_alert
  novo alerta: configure_alert
  tarefa recorrente: schedule_recurring
  agendar recorrente: schedule_recurring
  recurring task: schedule_recurring
  automação periódica: schedule_recurring
  tarefa programada: schedule_recurring
  dependências tarefa: view_task_dependencies
  dependências de tarefa: view_task_dependencies
  ver dependências: view_task_dependencies
  task dependencies: view_task_dependencies
  grafo de tarefas: view_task_dependencies
  verificação autônoma: run_autonomous_check
  autonomous check: run_autonomous_check
  verificação automática: run_autonomous_check
  background check: run_autonomous_check
  agente autônomo: run_autonomous_check
```

### Arquivo canônico: `app/domains/candidate_self_service/config/capabilities.yaml`

**Linhas:** 33  |  **Bytes:** 842

```yaml
# capabilities.yaml — candidate_self_service domain intent keywords
domain: candidate_self_service

intent_keywords:
  status: get_status
  candidatura: get_status
  processo: get_status
  vaga: get_status
  etapa: get_status
  fase: get_status
  aprovado: get_status
  reprovado: get_status
  resultado: get_status
  andamento: get_status
  entrevista: get_interview_info
  reunião: get_interview_info
  reuniao: get_interview_info
  agendamento: get_interview_info
  horário: get_interview_info
  horario: get_interview_info
  data: get_interview_info
  feedback: get_feedback
  avaliação: get_feedback
  avaliacao: get_feedback
  retorno: get_feedback
  comentário: get_feedback
  comentario: get_feedback
  nota: get_feedback
  explicação: get_lgpd_info
  explicacao: get_lgpd_info
  lgpd: get_lgpd_info
  direito: get_lgpd_info
```

### Arquivo canônico: `app/domains/communication/config/capabilities.yaml`

**Linhas:** 84  |  **Bytes:** 3047

```yaml
# capabilities.yaml — communication domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: communication

intent_keywords:
  enviar email: send_email
  send email: send_email
  disparar email: send_email
  email candidato: send_email
  email em massa: send_bulk_email
  bulk email: send_bulk_email
  envio massa: send_bulk_email
  envio em lote: send_bulk_email
  enviar parecer: send_candidate_report
  parecer gestor: send_candidate_report
  relatório candidato: send_candidate_report
  report gestor: send_candidate_report
  relatório progresso: send_progress_report
  relatório de progresso: send_progress_report
  progress report: send_progress_report
  andamento da vaga: send_progress_report
  progresso da vaga: send_progress_report
  relatório kpi: send_kpi_report
  relatório de kpi: send_kpi_report
  kpi report: send_kpi_report
  relatório consolidado: send_kpi_report
  indicadores: send_kpi_report
  feedback candidato: send_feedback
  enviar feedback: send_feedback
  devolutiva candidato: send_feedback
  retorno candidato: send_feedback
  criar template: create_template
  template email: create_template
  novo template: create_template
  editar template: edit_template
  atualizar template: edit_template
  listar template: list_templates
  templates disponíveis: list_templates
  visualizar template: preview_template
  preview template: preview_template
  preview do template: preview_template
  notificar stakeholder: notify_stakeholders
  notificação: notify_stakeholders
  avisar gestor: notify_stakeholders
  alertar equipe: notify_stakeholders
  enviar whatsapp: send_whatsapp
  whatsapp candidato: send_whatsapp
  mensagem whatsapp: send_whatsapp
  whatsapp: send_whatsapp
  enviar teams: send_teams_message
  mensagem teams: send_teams_message
  teams: send_teams_message
  notificar teams: send_teams_message
  enviar sms: send_sms
  sms candidato: send_sms
  sms: send_sms
  histórico comunicação: get_communication_history
  histórico de comunicação: get_communication_history
  communication history: get_communication_history
  histórico email: get_communication_history
  histórico mensagem: get_communication_history
  convite triagem: send_screening_invite
  convite de triagem: send_screening_invite
  convidar triagem: send_screening_invite
  screening invite: send_screening_invite
  convite entrevista: send_interview_invite
  convite de entrevista: send_interview_invite
  convidar entrevista: send_interview_invite
  interview invite: send_interview_invite
  preferência comunicação: update_preferences
  preferências de comunicação: update_preferences
  opt-out: update_preferences
  preferências candidato: update_preferences
  canal preferido: update_preferences
  webhook: manage_webhook
  configurar webhook: manage_webhook
  registrar webhook: manage_webhook
  solicitação dados: handle_data_request
  solicitação de dados: handle_data_request
  data request: handle_data_request
  lgpd solicitação: handle_data_request
  lgpd: handle_data_request
```

### Arquivo canônico: `app/domains/company_settings/config/capabilities.yaml`

**Linhas:** 80  |  **Bytes:** 1568

**Descrição:** Capabilities and intent-keyword mapping for the company_settings domain. Used by KeywordIntentMatcher (domain.py) for fast intent routing.

```yaml
version: "1.0"
description: |
  Capabilities and intent-keyword mapping for the company_settings domain.
  Used by KeywordIntentMatcher (domain.py) for fast intent routing.

intent_keywords:
  configure_profile:
    - "perfil"
    - "dados"
    - "nome"
    - "cnpj"
    - "website"
    - "email"
    - "telefone"
    - "endereço"
    - "setor"
    - "indústria"
    - "porte"
    - "funcionários"
    - "linkedin"
    - "logo"
    - "fundação"
  configure_culture:
    - "cultura"
    - "missão"
    - "visão"
    - "valores"
    - "evp"
    - "proposta de valor"
    - "employer branding"
    - "modelo de trabalho"
    - "híbrido"
    - "remoto"
    - "presencial"
    - "diversidade"
    - "dei"
    - "inclusão"
    - "sustentabilidade"
    - "liderança"
    - "dinâmica"
    - "crescimento"
  configure_tech_stack:
    - "tech stack"
    - "stack"
    - "tecnologia"
    - "engenharia"
    - "linguagens"
    - "ferramentas"
    - "infraestrutura"
  configure_benefits:
    - "benefícios"
    - "plano de saúde"
    - "vale"
    - "auxílio"
    - "bônus"
    - "PLR"
    - "stock options"
    - "gympass"
    - "home office"
  configure_workforce:
    - "planejamento"
    - "contratações"
    - "workforce"
    - "headcount"
    - "vagas planejadas"
    - "meta de contratação"
  analyze_website:
    - "analisar website"
    - "analisar site"
    - "extrair do site"
    - "importar do website"
    - "scraping"
  process_document:
    - "documento"
    - "handbook"
    - "manual"
    - "organograma"
    - "plano de cargos"
    - "upload"
```

### Arquivo canônico: `app/domains/cv_screening/config/capabilities.yaml`

**Linhas:** 90  |  **Bytes:** 2766

```yaml
# capabilities.yaml — cv_screening domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: cv_screening

intent_keywords:
  analisar cv: parse_cv
  parse cv: parse_cv
  extrair cv: parse_cv
  currículo: parse_cv
  curriculo: parse_cv
  triagem automática: auto_screen
  triar candidato: auto_screen
  screening: auto_screen
  triagem: auto_screen
  triagem lote: batch_screen
  batch screening: batch_screen
  triagem em massa: batch_screen
  score wsi: calculate_wsi_score
  calcular wsi: calculate_wsi_score
  wsi score: calculate_wsi_score
  pontuação wsi: calculate_wsi_score
  rankear: rank_candidates
  ranking: rank_candidates
  rank candidato: rank_candidates
  ordenar candidatos: rank_candidates
  corte dinâmico: dynamic_cutoff
  top 25: dynamic_cutoff
  dynamic cut: dynamic_cutoff
  red flag: detect_red_flags
  red flags: detect_red_flags
  detectar red flag: detect_red_flags
  risco cv: detect_red_flags
  flag: detect_red_flags
  saturação: check_saturation
  pipeline saturado: check_saturation
  saturation: check_saturation
  bloom: classify_bloom
  taxonomia bloom: classify_bloom
  bloom taxonomy: classify_bloom
  dreyfus: classify_dreyfus
  proficiência: classify_dreyfus
  dreyfus level: classify_dreyfus
  big five: map_big_five
  big5: map_big_five
  personalidade: map_big_five
  comportamental: map_big_five
  cbi: validate_cbi
  competency based: validate_cbi
  competência: validate_cbi
  parecer: generate_report
  relatório candidato: generate_report
  parecer candidato: generate_report
  comparar candidato: compare_candidates
  comparação: compare_candidates
  compare: compare_candidates
  calibrar: calibrate_model
  calibração: calibrate_model
  calibrate: calibrate_model
  feedback modelo: calibrate_model
  explicar score: explain_score
  explainability: explain_score
  como calculou: explain_score
  rubrica: evaluate_rubric
  avaliação rubrica: evaluate_rubric
  rubric evaluation: evaluate_rubric
  pergunta triagem: generate_questions
  screening question: generate_questions
  gerar pergunta: generate_questions
  ajustar pergunta: adjust_questions
  refinar pergunta: adjust_questions
  adjust question: adjust_questions
  voz: voice_screening
  voice screening: voice_screening
  triagem por voz: voice_screening
  normalizar score: normalize_scores
  normalize: normalize_scores
  normalização: normalize_scores
  senioridade: assess_seniority
  seniority: assess_seniority
  nível experiência: assess_seniority
  feedback candidato: send_feedback
  feedback triagem: send_feedback
  enviar feedback: send_feedback
  devolutiva: send_feedback
  feedback ao candidato: send_feedback
  pré-qualificação: pre_qualify
  pre qualify: pre_qualify
  pré-qualificar: pre_qualify
```

### Arquivo canônico: `app/domains/digital_twin/config/capabilities.yaml`

**Linhas:** 14  |  **Bytes:** 378

```yaml
domain: digital_twin

intent_keywords:
  digital twin: list_twins
  gêmeo digital: list_twins
  criar twin: create_twin
  novo twin: create_twin
  avaliar com twin: evaluate_with_twin
  avaliação twin: evaluate_with_twin
  segunda opinião: evaluate_with_twin
  opinião do especialista: evaluate_with_twin
  treinar twin: index_twin_audio
  indexar áudio: index_twin_audio
```

### Arquivo canônico: `app/domains/hiring_policy/config/capabilities.yaml`

**Linhas:** 41  |  **Bytes:** 1320

```yaml
# capabilities.yaml — hiring_policy domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: hiring_policy

intent_keywords:
  política: configure_policy
  politica: configure_policy
  policy: configure_policy
  regra: configure_policy
  configurar: configure_policy
  setup: configure_policy
  pipeline: configure_pipeline
  etapa: configure_pipeline
  stage: configure_pipeline
  agendamento: configure_scheduling
  scheduling: configure_scheduling
  agendar: configure_scheduling
  comunicação: configure_communication
  comunicacao: configure_communication
  communication: configure_communication
  email: configure_communication
  whatsapp: configure_communication
  triagem: configure_screening
  screening: configure_screening
  automação: configure_automation
  automacao: configure_automation
  automation: configure_automation
  autonomia: configure_automation
  compliance: validate_compliance
  conformidade: validate_compliance
  validar: validate_compliance
  progresso: get_progress
  progress: get_progress
  portal: configure_candidate_portal
  portal candidato: configure_candidate_portal
  candidato portal: configure_candidate_portal
  ativar portal: configure_candidate_portal
  desativar portal: configure_candidate_portal
  portal do candidato: configure_candidate_portal
```

### Arquivo canônico: `app/domains/interview_scheduling/config/capabilities.yaml`

**Linhas:** 96  |  **Bytes:** 3714

```yaml
# capabilities.yaml — interview_scheduling domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: interview_scheduling

intent_keywords:
  agendar entrevista: schedule_interview
  marcar entrevista: schedule_interview
  schedule interview: schedule_interview
  agendar reunião: schedule_interview
  reagendar entrevista: reschedule_interview
  reagendar: reschedule_interview
  remarcar entrevista: reschedule_interview
  reschedule: reschedule_interview
  mudar horário entrevista: reschedule_interview
  mudar horário da entrevista: reschedule_interview
  cancelar entrevista: cancel_interview
  cancel interview: cancel_interview
  desmarcar entrevista: cancel_interview
  verificar disponibilidade: check_availability
  checar disponibilidade: check_availability
  check availability: check_availability
  disponibilidade calendário: check_availability
  disponibilidade do calendário: check_availability
  horários disponíveis: check_availability
  horários livres: check_availability
  link agendamento: generate_self_scheduling_link
  link de agendamento: generate_self_scheduling_link
  auto-agendamento: generate_self_scheduling_link
  self scheduling: generate_self_scheduling_link
  link para candidato agendar: generate_self_scheduling_link
  horários comuns: find_common_slots
  slots comuns: find_common_slots
  encontrar horários: find_common_slots
  common slots: find_common_slots
  enviar lembrete: send_reminder
  lembrete entrevista: send_reminder
  lembrete de entrevista: send_reminder
  reminder: send_reminder
  agendar lembretes: schedule_reminders
  programar lembretes: schedule_reminders
  lembretes automáticos: schedule_reminders
  entrevistas hoje: list_today_interviews
  entrevistas de hoje: list_today_interviews
  agenda hoje: list_today_interviews
  agenda de hoje: list_today_interviews
  today interviews: list_today_interviews
  entrevistas do dia: list_today_interviews
  conflito agenda: resolve_conflict
  conflito de agenda: resolve_conflict
  resolver conflito: resolve_conflict
  scheduling conflict: resolve_conflict
  entrevista wsi: start_wsi_interview
  iniciar entrevista wsi: start_wsi_interview
  wsi interview: start_wsi_interview
  entrevista completa: start_wsi_interview
  enviar pergunta: send_question
  fazer pergunta: send_question
  próxima pergunta: send_question
  send question: send_question
  analisar resposta: analyze_response
  avaliar resposta: analyze_response
  analyze response: analyze_response
  análise de resposta: analyze_response
  transcrever áudio: transcribe_audio
  transcrição: transcribe_audio
  transcribe: transcribe_audio
  transcrever entrevista: transcribe_audio
  analisar voz: analyze_voice
  análise de voz: analyze_voice
  análise vocal: analyze_voice
  voice analysis: analyze_voice
  resposta evasiva: detect_evasive
  detectar evasiva: detect_evasive
  candidato evadindo: detect_evasive
  evasive answer: detect_evasive
  pergunta follow-up: generate_followup
  pergunta de follow-up: generate_followup
  follow-up: generate_followup
  gerar follow-up: generate_followup
  aprofundar resposta: generate_followup
  finalizar entrevista: complete_interview
  encerrar entrevista: complete_interview
  complete interview: complete_interview
  concluir entrevista: complete_interview
  resumo da entrevista: complete_interview
  dúvida entrevista: interview_qa
  dúvida sobre entrevista: interview_qa
  pergunta sobre entrevista: interview_qa
  interview qa: interview_qa
  triagem rápida: start_quick_screening
  quick screening: start_quick_screening
  triagem inicial: start_quick_screening
  screening rápido: start_quick_screening
  iniciar triagem: start_quick_screening
```

### Arquivo canônico: `app/domains/job_management/config/capabilities.yaml`

**Linhas:** 140  |  **Bytes:** 4113

```yaml
# capabilities.yaml — job_management domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: job_management

intent_keywords:
  criar vaga: create_job
  nova vaga: create_job
  create job: create_job
  abrir vaga: create_job
  wizard: guided_wizard
  guiado: guided_wizard
  passo a passo: guided_wizard
  step: guided_wizard
  extrair requisito: extract_requirements
  extract: extract_requirements
  requisitos: extract_requirements
  rubrica: generate_rubrics
  rubric: generate_rubrics
  atualizar vaga: update_job
  editar vaga: update_job
  update: update_job
  alterar vaga: update_job
  saúde: health_check
  health: health_check
  diagnóstico: health_check
  estratégia: suggest_strategy
  strategy: suggest_strategy
  duplicar: duplicate_job
  duplicate: duplicate_job
  template: create_from_template
  modelo: create_from_template
  clonar: clone_job
  clone: clone_job
  fechar vaga: close_job
  close: close_job
  arquivar: close_job
  encerrar: close_job
  pausar vaga: pause_job
  pausar: pause_job
  pause: pause_job
  pausa: pause_job
  suspender: pause_job
  suspende: pause_job
  benefício: get_benefits
  benefit: get_benefits
  melhorar jd: suggest_jd_improvements
  improve: suggest_jd_improvements
  sugerir melhoria: suggest_jd_improvements
  detectar critério: detect_criteria
  detect: detect_criteria
  auto detect: detect_criteria
  pergunta wsi: generate_wsi_questions
  wsi question: generate_wsi_questions
  triagem: generate_wsi_questions
  avançar etapa: advance_wizard_step
  avançar para próxima: advance_wizard_step
  próxima etapa: advance_wizard_step
  next step: advance_wizard_step
  advance: advance_wizard_step
  dados etapa: get_wizard_step_data
  step data: get_wizard_step_data
  etapa atual: get_wizard_step_data
  enriquecer jd: enrich_jd
  enriquecer a job: enrich_jd
  enriquecer: enrich_jd
  enrich: enrich_jd
  enriquecimento: enrich_jd
  importar jd: import_jd
  import jd: import_jd
  gerar jd: generate_jd
  generate jd: generate_jd
  gerar job description: generate_jd
  analytics: job_analytics
  métricas: job_analytics
  relatório: job_analytics
  qualificação: qualify_job
  qualify: qualify_job
  publicar: publish_job
  publish: publish_job
  job board: publish_job
  webhook: job_status_webhook
  status: job_status_webhook
  buscar template: search_templates
  pesquisar template: search_templates
  search template: search_templates
  aplicar template: apply_template
  usar template: apply_template
  apply template: apply_template
  analisar jd: analyze_jd
  avaliar jd: analyze_jd
  qualidade jd: analyze_jd
  analyze jd: analyze_jd
  compensação: suggest_compensation
  faixa salarial: suggest_compensation
  salary range: suggest_compensation
  sugerir salário: suggest_compensation
  remuneração: suggest_compensation
  # EX-007: English + PT list jobs resilience
  list jobs: list_jobs
  show jobs: list_jobs
  active jobs: list_jobs
  show me jobs: list_jobs
  show me the jobs: list_jobs
  show me the active jobs: list_jobs
  listar vagas: list_jobs
  ver vagas: list_jobs
  vagas ativas: list_jobs
  vagas abertas: list_jobs
  minhas vagas: list_jobs
  mostra vagas: list_jobs
  # JD generation keyword substrings
  descrição de vaga: generate_jd
  gerar descrição: generate_jd
  generate job description: generate_jd
  job desc: generate_jd
  # Salary suggestion keyword substrings
  salário sugerir: suggest_compensation
  qual salário: suggest_compensation
  suggest salary: suggest_compensation
  salary for: suggest_compensation
  # `duplicar` is already mapped above; this covers the `duplica` variant.
  duplica: duplicate_job
  # JM-005: urgency/risk queries — eval fix
  vagas urgentes: list_jobs
  urgentes: list_jobs
  em risco: list_jobs
  risco: list_jobs
  vaga urgente: list_jobs
  urgência: list_jobs
  quais vagas estão: list_jobs
  quais vagas: list_jobs
  # JM-008: count by status — eval fix
  quantas vagas: count_jobs
  quantas vagas tenho: count_jobs
  contar vagas: count_jobs
  vagas pausadas: list_jobs
  vagas concluídas: list_jobs
  vagas abertas: list_jobs
```

### Arquivo canônico: `app/domains/pipeline/config/capabilities.yaml`

**Linhas:** 22  |  **Bytes:** 683

```yaml
# capabilities.yaml — pipeline domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: pipeline

intent_keywords:
  mover candidato: move_candidate
  move candidate: move_candidate
  avançar candidato: move_candidate
  avançar etapa: move_candidate
  mudar etapa: move_candidate
  transição: move_candidate
  interpretar contexto: interpret_context
  interpretar: interpret_context
  prever sub-status: predict_sub_status
  predizer sub-status: predict_sub_status
  sugerir ação: suggest_next_action
  próxima ação: suggest_next_action
  listar etapas: list_pipeline_stages
  etapas do pipeline: list_pipeline_stages
  ver pipeline: list_pipeline_stages
```

### Arquivo canônico: `app/domains/recruiter_assistant/config/capabilities.yaml`

**Linhas:** 140  |  **Bytes:** 4989

```yaml
# capabilities.yaml — recruiter_assistant domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: recruiter_assistant

intent_keywords:
  briefing diário: daily_briefing
  briefing do dia: daily_briefing
  daily briefing: daily_briefing
  bom dia lia: daily_briefing
  resumo matinal: daily_briefing
  como está meu dia: daily_briefing
  resumo do dia: end_of_day_summary
  resumo final: end_of_day_summary
  end of day: end_of_day_summary
  encerrar dia: end_of_day_summary
  fim do dia: end_of_day_summary
  pergunta rápida: quick_question
  dúvida rápida: quick_question
  quick question: quick_question
  me ajuda com: quick_question
  planejar dia: plan_day
  planejar meu dia: plan_day
  plan day: plan_day
  organizar agenda: plan_day
  organizar minha agenda: plan_day
  saúde do pipeline: pipeline_health
  saúde pipeline: pipeline_health
  pipeline health: pipeline_health
  como está o pipeline: pipeline_health
  status do pipeline: pipeline_health
  candidatos parados: kanban_analysis
  candidatos estão parados: stale_candidates
  candidatos inativos: stale_candidates
  stale candidates: stale_candidates
  candidatos sem movimento: stale_candidates
  candidatos esquecidos: stale_candidates
  mover candidato: move_candidate
  mover para etapa: move_candidate
  move candidate: move_candidate
  mudar etapa: move_candidate
  trocar etapa: move_candidate
  avançar candidato: move_candidate
  sugerir ação: suggest_action
  próxima ação: suggest_action
  suggest action: suggest_action
  o que fazer com: suggest_action
  recomendação de ação: suggest_action
  buscar contexto: search_context
  histórico conversa: search_context
  histórico de conversa: search_context
  search context: search_context
  buscar no histórico: search_context
  salvar memória: save_memory
  lembrar disso: save_memory
  save memory: save_memory
  guardar informação: save_memory
  anotar: save_memory
  recuperar memória: recall_memory
  o que eu disse sobre: recall_memory
  recall memory: recall_memory
  lembrar de: recall_memory
  buscar memória: recall_memory
  resumo da conversa: conversation_summary
  resumir conversa: conversation_summary
  conversation summary: conversation_summary
  resumo do chat: conversation_summary
  análise do kanban: kanban_analysis
  análise kanban: kanban_analysis
  kanban analysis: kanban_analysis
  analisar kanban: kanban_analysis
  visão do kanban: kanban_analysis
  ranking: kanban_analysis
  rankear: kanban_analysis
  rankear candidatos: kanban_analysis
  ranking de candidatos: kanban_analysis
  melhores candidatos: kanban_analysis
  quem são os melhores: kanban_analysis
  top candidatos: kanban_analysis
  ordenar candidatos: kanban_analysis
  classificar candidatos: kanban_analysis
  performance do funil: kanban_analysis
  como está o funil: kanban_analysis
  métricas do funil: kanban_analysis
  gargalos: kanban_analysis
  gargalo no processo: kanban_analysis
  taxa de conversão: kanban_analysis
  tempo médio: kanban_analysis
  calibrar perfil: calibrate_profile
  calibrar candidato ideal: calibrate_profile
  calibrate profile: calibrate_profile
  perfil ideal: calibrate_profile
  ajustar perfil: calibrate_profile
  enviar notificação: send_notification
  notificar: send_notification
  send notification: send_notification
  alerta para mim: send_notification
  acompanhar metas: track_goals
  minhas metas: track_goals
  track goals: track_goals
  progresso das metas: track_goals
  metas de recrutamento: track_goals
  gerar insights: generate_insights
  insights de busca: generate_insights
  generate insights: generate_insights
  análise proativa: generate_insights
  sugestões proativas: generate_insights
  alertas: proactive_alerts
  alertas proativos: proactive_alerts
  smart alerts: proactive_alerts
  alertas inteligentes: proactive_alerts
  riscos do pipeline: proactive_alerts
  ações autônomas: autonomous_actions
  ações automáticas: autonomous_actions
  ações pendentes: autonomous_actions
  autonomous actions: autonomous_actions
  notificar gestor: stakeholder_notify
  notificar hiring manager: stakeholder_notify
  decisões pendentes: stakeholder_notify
  pending decisions: stakeholder_notify
  escalar decisão: stakeholder_notify
  aprendizado: learning_insights
  learning insights: learning_insights
  o que a lia aprendeu: learning_insights
  insights de contratação: learning_insights
  comparar candidatos: compare_candidates
  compare candidates: compare_candidates
  comparação de candidatos: compare_candidates
  candidato vs candidato: compare_candidates
  recomendar etapa: stage_recommendation
  qual próxima etapa: stage_recommendation
  stage recommendation: stage_recommendation
  sugerir etapa: stage_recommendation
  recomendação de etapa: stage_recommendation
  ajuda: help_command
  help: help_command
  comandos disponíveis: help_command
  o que você pode fazer: help_command
  funcionalidades: help_command
```

### Arquivo canônico: `app/domains/recruitment_campaign/config/capabilities.yaml`

**Linhas:** 15  |  **Bytes:** 469

```yaml
domain: recruitment_campaign

intent_keywords:
  criar campanha: create_campaign
  nova campanha: create_campaign
  iniciar campanha: create_campaign
  campanha de recrutamento: create_campaign
  progresso campanha: get_campaign_progress
  status campanha: get_campaign_progress
  como está a campanha: get_campaign_progress
  avançar campanha: advance_campaign
  próxima etapa: advance_campaign
  listar campanhas: list_campaigns
  minhas campanhas: list_campaigns
```

### Arquivo canônico: `app/domains/sourcing/config/capabilities.yaml`

**Linhas:** 72  |  **Bytes:** 2051

```yaml
# capabilities.yaml — sourcing domain intent keywords
# Generated by Fase 5 migration (LIA-I05)

domain: sourcing

intent_keywords:
  search: search_candidates
  buscar: search_candidates
  busca: search_candidates
  candidato: search_candidates
  global: global_search
  semantic: semantic_search
  semântic: semantic_search
  boolean: generate_boolean
  booleana: generate_boolean
  cv: parse_cv
  currículo: parse_cv
  curriculo: parse_cv
  analisar cv: parse_cv
  adicionar: add_candidate
  cadastrar: add_candidate
  sugerir: suggest_candidates
  suggest: suggest_candidates
  sugestão: suggest_candidates
  match: match_candidates
  compatibilidade: match_candidates
  enriquecer: enrich_profile
  enrich: enrich_profile
  pipeline: auto_source
  automático: auto_source
  auto_source: auto_source
  volume: check_volume
  proativ: proactive_suggest
  filtrar: filter_candidates
  filtro: filter_candidates
  rankear: rank_candidates
  rank: rank_candidates
  comparar: compare_candidates
  talent pool: talent_pool_search
  pool: talent_pool_search
  pearch: pearch_search
  estratégia: build_search_strategy
  strategy: build_search_strategy
  resultado: analyze_search_results
  feedback: feedback_search
  expandir: expand_search
  ampliar: expand_search
  contatar: contact_candidates
  outreach: contact_candidates
  triagem: screen_candidates
  screening: screen_candidates
  mercado: assess_market
  exportar: export_candidates
  importar: import_candidates
  dedup: dedup_candidates
  duplica: dedup_candidates
  tag: tag_candidates
  taguear: tag_candidates
  engagement: engagement_pipeline
  agendar: schedule_outreach
  mover candidato: update_candidate_stage
  mover etapa: update_candidate_stage
  mudar etapa: update_candidate_stage
  rejeitar: reject_candidate
  reprovar: reject_candidate
  shortlist: shortlist_candidate
  favoritar: shortlist_candidate
  favorito: shortlist_candidate
  adicionar à vaga: add_candidate_to_vacancy
  adicionar a vaga: add_candidate_to_vacancy
  vincular vaga: add_candidate_to_vacancy
```

### Arquivo canônico: `app/domains/talent_pool/config/capabilities.yaml`

**Linhas:** 20  |  **Bytes:** 610

```yaml
domain: talent_pool

intent_keywords:
  criar pool: create_talent_pool
  criar banco: create_talent_pool
  novo banco: create_talent_pool
  novo pool: create_talent_pool
  banco de talentos: list_talent_pools
  listar pool: list_talent_pools
  meus bancos: list_talent_pools
  meus pools: list_talent_pools
  adicionar ao pool: add_to_pool
  adicionar no banco: add_to_pool
  mover para vaga: move_pool_to_job
  migrar para vaga: move_pool_to_job
  candidatos do pool: get_pool_candidates
  ver pool: get_pool_candidates
  criar vaga do pool: create_job_from_pool
  vaga a partir do pool: create_job_from_pool
```

---

*Bundle gerado em 2026-04-24 | Fonte: `lia-agent-system/` no Replit | MD5 sincronizado Mac ↔ Replit*
