# Auditoria Sobreposta sobre Cartografia v1.0
*Versão 1.0 | Data: 2026-04-30 | Baseada em: CARTOGRAFIA_ARQUITETURAL.md v1.0*

> **Convenções:** IDs de achado no formato `F-NNN`. Cada achado referencia ID cartográfico (`V7-A12`, `V12.5-AL3`, etc.). Marcadores `[FATO]` (path:linha lido via SSH) / `[HIPÓTESE]` (inferido). Severidade: **Crítica** (bloqueia produção enterprise — segurança/compliance), **Alta** (confiabilidade ou multiplicador de dívida), **Média** (velocidade de evolução), **Baixa** (higiene). Esforço: **P** 1-2d, **M** 3-10d, **G** >10d.

---

## Sumário Executivo da Auditoria

**Estado em uma frase:** A plataforma WeDOTalent é arquiteturalmente madura (RLS no DB, BYOK com linter CI, eval framework rico com 552 testes em 29 dirs, DSR LGPD completo, retenção SOX/LGPD documentada) mas tem **gaps críticos de isolamento de tenant em 17 modelos sensíveis sem `company_id`**, **streaming endpoints (SSE/WS) sem post-compliance em chunks**, **AuditService.log_decision sub-utilizado em decisões críticas**, **22 dos 63 domínios sem qualquer teste unit** e **3 orquestradores em paralelo** que precisam consolidação.

**Cinco achados de maior severidade (Crítica, top 5):**

1. **[F-302] `audit_logs` (V12.5-AL1) sem `company_id`** — SOX audit logs globais; queries sem filter de tenant retornam logs cross-tenant. **Evidência:** [libs/models/lia_models/audit_logs.py](libs/models/lia_models/audit_logs.py) modelo SOXAuditLog não declara `company_id`.
2. **[F-306] Repositories com raw SQL e tenant context indeterminado (V12.11-RLS1)** — Vários repos usam `db.execute(text(...))`; se chamados via `Depends(get_db)` (legacy) em vez de `get_tenant_db()`, RLS não dispara. **Evidência:** [wsi_repository.py:45-297](app/domains/voice/repositories/wsi_repository.py:45) com 15+ raw queries.
3. **[F-001] Bypass real de BYOK em `skills_ontology_engine.py:535`** — Importa `google.generativeai` direto e usa `os.environ.get("GEMINI_API_KEY")` sem passar por `get_provider_for_tenant()`. **Evidência:** [V10-SC NÃO se aplica; V12.10-LLM1 falhou para este path].
4. **[F-315/F-316] Streaming SSE/WS sem post-compliance em chunks (V12.2-PII1, V12.7-OG)** — `pre_compliance` é chamado no início, mas chunks individuais do stream não são filtrados — PII pode vazar em tempo real.
5. **[F-209] AuditService.criteria_used vazio em maioria das decisões (V12.5-AL3)** — `log_decision()` aceita `criteria_used: list` mas grep mostra 3 paths com payload rico vs 8+ chamadas com `criteria_used=[]`. Audit trail impotente para explainability.

**Três pontos fortes confirmados:**

1. **RLS PostgreSQL com defesa em profundidade.** 3 migrations (040+068+102) implementam `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` + 4 policies (SELECT/INSERT/UPDATE/DELETE) por tabela, com helper [database.py](app/core/database.py) `set_tenant_context()` e `get_tenant_db()` (`SET ROLE lia_app`). Quando bem invocado, é robusto.

2. **Eval framework rico (V12.12 ML + tests).** 29 test dirs incluindo `tests/deepeval/` (agent quality), `tests/llm_eval/` (reasoning), `tests/ragas/` (RAG), `tests/golden/` (scenarios), `tests/fairness/` (4/5 disparate impact + bias detector), `tests/security/` (16 arquivos com injection harness, tenant isolation, red-team PII/fairness/circuit). 552 arquivos no total.

3. **BYOK + LLM Factory com linter CI.** `scripts/check_llm_factory_enforcement.py` define ALLOWLIST com 11 paths autorizados + BLOCKED_NAMES (AsyncAnthropic, ChatAnthropic, ChatOpenAI, ChatGoogleGenerativeAI, genai.Client). Encryption Fernet em `tenant_llm_config.provider_api_keys`. Tier1/Tier2 enforcement via `TASK_MINIMUM_TIER`.

**Magnitude: total de achados por severidade**

| Severidade | Count | % |
|---|---|---|
| 🔴 Crítica | 11 | 13% |
| 🟠 Alta | 23 | 27% |
| 🟡 Média | 38 | 45% |
| 🟢 Baixa | 13 | 15% |
| **Total** | **85** | **100%** |

---

## Tabela Mestre de Achados (T-Audit)

| ID | Lente | Vista | Componente (cartografia) | Tipo | Descrição | Localização | Impacto | Severidade | Esforço |
|---|---|---|---|---|---|---|---|---|---|
| **F-001** | L1 | V12.10 | V12.10-LLM4 BYOKSupport | Bypass BYOK | Importa `google.generativeai` direto, lê `GEMINI_API_KEY` global, sem tenant key | [skills_ontology_engine.py:531-541](app/domains/talent_intelligence/services/skills_ontology_engine.py:531) | Embeddings sem tenant, sem audit, sem cost tracking per-tenant | Crítica | P |
| **F-002** | L1 | V6/V7 | V6-D1 sourcing → V6-D21 credits | Cross-domain leak | sourcing importa credit_service direto sem abstração | [sourcing_tool_registry.py:99](app/domains/sourcing/agents/sourcing_tool_registry.py:99) | Acoplamento bilateral; mudança em credits quebra sourcing | Alta | M |
| **F-003** | L1 | V6/V12.9 | V6-D1 sourcing → V12.9 RAG | Cross-domain RAG | sourcing importa RAGPipelineService e Pearch direto | sourcing_tool_registry.py + pearch_service.py | AI services não versionáveis independentemente | Alta | M |
| **F-004** | L1 | V6 | V6-D1 sourcing → V6-D18 candidates | Enrichment coupling | contact_enrichment importa candidate_enrichment direto | contact_enrichment_service.py | Refactor candidates quebra sourcing | Média | M |
| **F-005** | L1 | V6 | V6-D19 job_management → V6-D2 recruiter_assistant | Circular leak | jd_template_service importa pipeline_stage_service | [jd_template_service.py](app/domains/job_management/services/jd_template_service.py) | Domains interdependentes; impossível separar | Alta | M |
| **F-006** | L1 | V12.4 | V12.4-IC1 + V6-D19 | LLM intent coupling | wizard_step_service importa intent_classifier e enhanced_intent_classifier direto | [wizard_step_service/_shared.py](app/domains/job_management/services/wizard_step_service/_shared.py) | job_management bloqueado em classifier AI | Média | M |
| **F-007** | L1 | V10 | V10-OR1 → V6-Dx | Orchestrator-domain coupling | action_handlers importam dominios diretos em 15+ files | [action_handlers/*](app/orchestrator/action_handlers/) | Orchestrator quebra em runtime se domain service muda assinatura | Alta | M |
| **F-008** | L1/L2 | V5 | V5 (HTTP) | HTTP sem abstração | 8+ services em sourcing/ usam httpx.AsyncClient sem factory centralizada | apify_*.py, stackoverflow_service.py, github_service.py, pearch_service.py | Retry/timeout/headers duplicados; sem circuit_breaker global | Média | M |
| **F-009** | L2 | V9 | V9-T pipeline_tools | Duplicação tool homônimo | `pipeline_tools.py` em 2 paths com 50% overlap | [recruiter_assistant/tools/pipeline_tools.py](app/domains/recruiter_assistant/tools/pipeline_tools.py) (244L) E [pipeline/tools/pipeline_tools.py](app/domains/pipeline/tools/pipeline_tools.py) (320L) | Bugs em um não replicam ao outro | Média | M |
| **F-010** | L2 | V9 | V9-T query_tools | Duplicação 3x | `query_tools.py` em sourcing/, job_management/, analytics/ com ~70% overlap | 3 arquivos | Refactor fragmentado | Média | G |
| **F-011** | L2 | V12.8 | V12.8-MEM4 PronounResolver | Duplicação memory | 2 implementações de memory_resolver.py (orchestrator/ vs shared/) | [orchestrator/memory_resolver.py](app/orchestrator/memory_resolver.py) (380L) vs [shared/memory_resolver.py](app/shared/memory_resolver.py) (209L) | Manter dois codebases, divergência crescente | Média | M |
| **F-012** | L2 | V12.4 | V12.4-IC2 | Duplicação intent classifier | `intent_classifier.py` (317L) vs `enhanced_intent_classifier.py` (470L) sem documentação de qual escolher | [intent_classifier.py](app/domains/ai/services/intent_classifier.py) e [enhanced_intent_classifier.py](app/domains/ai/services/enhanced_intent_classifier.py) | Importers confusos; sem factory de roteamento | Baixa | P |
| **F-013** | L2 | V12.5 | V12.5-AL1 | Audit shim duplicado | `app/shared/services/audit_service.py` (re-export) vs canonical `app/shared/compliance/audit_service.py` | dois paths | Importers podem usar caminho errado | Baixa | P |
| **F-014** | L2 | V12.5 | V12.5-AL5 PIIMasking | PII filters paralelos | `app/shared/pii_masking.py` (canonical) vs `app/domains/ats_integration/services/ats_clients/ats_pii_filter.py` (especializado ATS) | dois paths | Avaliar se são complementares ou divergentes | Baixa | P |
| **F-015** | L1 | V6/V12.10 | V6-D5 communication → google.genai | Cross-domain LLM | teams_orchestrator_bridge importa `google.genai` 2x sem tenant context | [teams_orchestrator_bridge.py:261, 375](app/domains/communication/services/teams_orchestrator_bridge.py:261) | Verificar se é via factory ou bypass | Média | P |
| **F-016** | L1 | V6/V12.10 | V6-D16 voice → google.genai | Voice direct | voice_screening_orchestrator importa google.genai direto (mas está na ALLOWLIST do linter? Verificar) | [voice_screening_orchestrator.py:929](app/domains/voice/services/voice_screening_orchestrator.py:929) | Se não na ALLOWLIST = bypass; verificar | Média | P |
| **F-017** | L1 | V12.5 | V12.5 audit duplos | Multi-loggers | `audit_service.py` em `app/shared/compliance/` E `app/shared/services/` (shim) E `libs/audit/lia_audit/` | 3 paths | Confusão sobre canonical | Baixa | P |
| **F-018** | L2 | V5 | V5 (HTTP timeouts) | HTTP timeouts duplicados | Cada domain define timeout próprio em httpx (5s vs 30s) sem policy global | 8+ services | Tuning impossível; retry inconsistente | Baixa | P |
| **F-200** | L3 | V9 | V9-T (todos tool_registries) | Tool returns dict[str,Any] | 20+ tool wrappers retornam dict não tipificado, **kwargs não validado | [diversity_tool_registry.py:42](app/domains/sourcing/agents/diversity_tool_registry.py:42) + 19 outros registries | LLM recebe outputs sem garantia de schema; bugs silenciosos | Crítica | M |
| **F-201** | L3 | A3 (264 routers) | V14-CFG | Endpoints sem response_model | ~717 occurrences de endpoints sem `response_model=` declarado | [wsi/sessions.py:170,222](app/api/v1/wsi/sessions.py:170) + muitos outros | Respostas divergem de contrato; clients não sabem estrutura | Alta | P |
| **F-202** | L3 | V6-D18 | candidate.py schemas | Pydantic Optional excessivo | `CandidateUpdate` tem ~60 campos `Optional[...]`; sem validação required vs optional por operation | [app/schemas/candidate.py:1-150](app/schemas/candidate.py:1) | Permite estados inválidos (candidate sem nome) | Média | P |
| **F-203** | L3 | V10-OR1 | MainOrchestrator.process | Return type implícito | Retorna `ChatResponse` sem `Literal[...]` em campos enum-like | [main_orchestrator.py:346-390](app/orchestrator/main_orchestrator.py:346) | Casting implícito; type checker incompleto | Média | P |
| **F-204** | L3 | V12.8 | V12.8-MEM1 | Raw tuple returns | `wsi_repository.get_session()` retorna tuple raw; callers usam índices mágicos `session[0]` | [wsi/sessions.py:34-40](app/api/v1/wsi/sessions.py:34) | Frágil a schema change | Média | P |
| **F-205** | L4 | V12.10 | V12.10-LLM2 callers | LLM sem token tracking pre-call | 9+ callers de `get_provider_for_tenant()` não logam model + tokens antes de `.complete()` | wsi/_shared.py:271, wsi/reports.py:262, candidate_search/archetypes.py:1141 + 6 outros | Sem visibilidade de spend per domain/user | Crítica | P |
| **F-206** | L4 | V14-CFG | RequestIdMiddleware | Correlation ID não propagado | `request.state.request_id` injetado mas não evidência de propagação a DB/LLM/cache calls | [middleware/request_id.py:1-18](app/middleware/request_id.py:1) | Tracing distribuída quebrada | Média | P |
| **F-207** | L4 | V14-CFG | Sentry init | Profiling desativado | `sentry_sdk.init` sem `profiles_sample_rate` | [app/core/sentry.py:104-125](app/core/sentry.py:104) | Performance regressions invisíveis | Baixa | P |
| **F-208** | L4 | V12 (geral) | OpenTelemetry | Instrumentação esparsa | 16 `@trace_span` decorators vs 1587 imports do tracer; tool_registry wrappers sem spans | cascaded_router.py:173, main_orchestrator.py:345 vs zero em sourcing tools | Blind spots em tool execution | Média | M |
| **F-209** | L4 | V12.5 | V12.5-AL3 CriteriaTracking | Audit criteria_used vazio | Maioria das chamadas `log_decision()` passa `criteria_used=[]` em vez de payload rico | [audit_service.py:339,583,615](app/shared/compliance/audit_service.py:339) com vazios | Audit trail impotente para explainability LGPD/EU AI Act | Crítica | P |
| **F-210** | L4 | V10-SC6 | TenantBudget | Alerts sem metric | `tenant_budget.py:251` emite event="token_budget_alert" mas sem metric increment para dashboard | [tenant_budget.py:251](app/orchestrator/tenant_budget.py:251) | Alertas invisíveis em monitoring | Média | M |
| **F-211** | L4 | V12 obs | LangSmith config | Tracer configurado mas LLM não envolvido | `configure_langsmith()` chamado mas Anthropic/OpenAI clients não têm `wrap_openai`/equivalent | [observability/langsmith.py:18-60](app/shared/observability/langsmith.py:18) | Tracer não emite spans LLM reais | Média | P |
| **F-212** | L3 | V9 | V9-T tool definitions | Output schema missing | ToolDefinitions em registries omitem `output_schema` Pydantic | 20+ registries | LLM consome dict de formato imprevisível | Crítica | P |
| **F-213** | L3 | V10-OR1 | Phases methods | Return type missing | `_handle_pending_action`, `_try_action_executor`, `_process_via_orchestrator` sem `-> ChatResponse` explícito | [main_orchestrator.py:1132,1302,1382,1439](app/orchestrator/main_orchestrator.py:1132) | Type checker não valida | Média | P |
| **F-214** | L4 | V9 | V9-T tool wrappers | Exception silent | `except Exception as e: logger.debug()` em 20+ tool wrappers; sem metric, sem Sentry breadcrumb | [diversity_tool_registry.py:73,161,295](app/domains/sourcing/agents/diversity_tool_registry.py:73) + 17 outros | Tool failures invisíveis | Média | P |
| **F-215** | L3 | V6-D29 | wsi_compact_pipeline | Bare dict returns | `app/services/wsi_compact_pipeline.py:113-150` usa dict returns sem DTOs | wsi_compact_pipeline.py | Callers não typechecked | Média | P |
| **F-216** | L4 | V14-CFG | request_id sync | Sync contexts isolados | request_id pode não fluir para sync LLM factory calls | [middleware/auth_enforcement.py:296](app/middleware/auth_enforcement.py:296) | Tracing perde sync contexts | Baixa | P |
| **F-217** | L3 | A3 | response envelope | Inconsistent envelope | Alguns endpoints retornam dict literal sem ResponseEnvelope | wsi/sessions.py:34-80 | Clients não sabem estrutura esperada | Média | P |
| **F-218** | L4 | V12.5 | V12.5-AL5 RetentionPolicy | Sem alerting expiry | RETENTION_PERIODS define 730-1825 dias mas nenhum job alerta antes de expiry | [audit_service.py:54-60](app/shared/compliance/audit_service.py:54) | Compliance risk silencioso | Baixa | P |
| **F-219** | L3 | V9 | V9-T inputs | Kwargs não tipificados | `**kwargs: Any` aceita typos sem erro; LLM pode passar `rol` em vez de `role` | diversity_tool_registry.py:42-80 + outros | Bugs silenciosos difíceis de debug | Média | P |
| **F-220** | L4 | V10 | V10 spans | Spans sem tags | Spans não têm `tenant_id`, `user_id`, `model` em attributes | [cascaded_router.py:173](app/orchestrator/cascaded_router.py:173) | Tracing não filtrável por tenant | Média | P |
| **F-221** | L3 | V10-OR1 | UniversalContext | Required fields sem validation | `process(ctx)` não documenta quais campos de ctx são obrigatórios | [main_orchestrator.py:346-360](app/orchestrator/main_orchestrator.py:346) | Callers passam contexto incompleto | Baixa | P |
| **F-300** | L5 | V14-CFG | Auth public paths | Health endpoints | `POST /api/v1/health_check/seed`, `/sync-from-library` não em PUBLIC_PATHS explicitamente | [health_check.py](app/api/v1/health_check.py) | DEV_MODE pode permitir acesso sem JWT | Média | P |
| **F-302** | L5 | V12.5/V12.11 | V12.5-AL1 + V12.11-RLS | audit_logs sem company_id | SOXAuditLog não declara `company_id`; queries cross-tenant possíveis | [libs/models/lia_models/audit_logs.py](libs/models/lia_models/audit_logs.py) | Audit trail vaza entre tenants | Crítica | M |
| **F-303** | L5 | V12.11 | V12.11-RLS5 | conversation sem company_id | Conversation só com user_id; context_id pode colidir cross-tenant | [libs/models/lia_models/conversation.py](libs/models/lia_models/conversation.py) | Chat leak entre tenants | Alta | M |
| **F-304** | L5 | V12.11 | V12.11-RLS | technical_tests sem company_id | Testes técnicos shared cross-tenant | [libs/models/lia_models/technical_tests.py](libs/models/lia_models/technical_tests.py) | Templates leakam | Alta | M |
| **F-305** | L5 | V12.11 | V12.11-RLS | activity_feed/agent_activity sem company_id | Activity logs cross-tenant | activity_feed.py + agent_activity.py | Observability breach | Alta | M |
| **F-306** | L5 | V12.11 | V12.11-RLS1 | Repos com raw SQL e tenant unclear | 15+ raw queries em wsi_repository.py; depende de `Depends(get_tenant_db)` ser usado | [wsi_repository.py:45-297](app/domains/voice/repositories/wsi_repository.py:45) | RLS pode não aplicar se Depends errado | Crítica | G |
| **F-307** | L5 | V14-CFG | API keys env | Skills ontology env unsafe | `os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")` sem validação | [skills_ontology_engine.py:531](app/domains/talent_intelligence/services/skills_ontology_engine.py:531) | Env var names em traceback expõem config | Média | P |
| **F-309** | L5 | V14-CFG | DEV_MODE bypass | Synthetic admin user | `LIA_DEV_MODE=true` + `LIA_DEV_API_KEY` válido = admin synthetic | [auth_enforcement.py:72-76](app/middleware/auth_enforcement.py:72) | Staging com vars erradas = admin sem JWT | Alta | P |
| **F-310** | L5 | V14-CFG | Rails JWT fallback | Late company_id binding | Se FastAPI JWT decode fails, fallback para Rails — company_id resolved tarde | [auth_enforcement.py:249-266](app/middleware/auth_enforcement.py:249) | Rails compromise = fake company_id | Média | M |
| **F-312** | L5 | V12.6 | V12.6-LGPD2 | Models PII sem legal_basis | candidate.py, client_user.py armazenam name/email/cpf/phone sem `legal_basis_id` ou `consent_version_id` | [candidate.py:128-170](libs/models/lia_models/candidate.py:128) | LGPD: não rastreia base legal do processamento | Alta | M |
| **F-313** | L5 | V9 | V9-T pipeline mutations | Tool safety category informal | `GUARDRAIL_TOOLS` list sem enum formal | [pipeline_action_tool_registry.py](app/domains/pipeline/agents/pipeline_action_tool_registry.py) | Práctica sim, formalização não | Média | P |
| **F-315** | L5 | V12.2/V12.7 | V12.2-PII1 | SSE sem post_compliance em chunks | `pre_compliance` chamado, mas chunks individuais não filtrados antes de yield | [agent_chat_sse.py:235-250](app/api/v1/agent_chat_sse.py:235) | PII vaza em streaming | Alta | M |
| **F-316** | L5 | V12.2 | V12.2-PII1 | WS streaming sem post-compliance | WebSocket idem SSE | [agent_chat_ws.py](app/api/v1/agent_chat_ws.py) | PII vaza em WS | Alta | M |
| **F-317** | L5 | V14-CFG | CORS config | allow_credentials=True com permissive methods | `allow_methods=["*"], allow_headers=["*"], allow_credentials=True` | [main.py:471](app/main.py:471) | Em prod CORS_ORIGINS é lista — OK; staging precisa validar | Média | P |
| **F-318** | L5 | V14-CFG | JWT validation | Sem exp/aud/iss validation explícita | `decode_token()` em `app.auth.security` não confirma checks | [auth_enforcement.py:247-250](app/middleware/auth_enforcement.py:247) | Token expirado pode ser aceito | Alta | P |
| **F-321** | L5 | V12.2 | V12.2-PII4 | EncryptedFieldMixin parcial | `name`, `phone` provavelmente em plaintext (apenas cpf+email cifrados) | [encrypted_field_mixin.py](app/shared/encryption/encrypted_field_mixin.py) | PII em plaintext | Média | M |
| **F-323** | L5 | V12.11 | V12.11-RLS1 | _current_company_id confiabilidade | Depende de JWT signature verification ser sólida | auth_enforcement.py | Se JWT decode fraco, ContextVar pode ser injetada | Alta | P |
| **F-324** | L5 | V12.5 | V12.5-AL1 | log_decision sub-utilizado | grep `AuditService.log_decision` retorna 0 matches em api/v1/ | (zero locais) | Audit trail incompleto | Alta | M |
| **F-325** | L5 | V12.10 | V12.10-LLM5 CILinter | Linter CI executado? | `check_llm_factory_enforcement.py` existe; não validado se .github/workflows/ci.yml o executa | [.github/workflows/ci.yml](.github/workflows/ci.yml) | Bypasses passam despercebidos | Alta | P |
| **F-400** | L6 | V6 | V6-D17, V6-D32, V6-D33-D63 | 22 domínios sem teste unit | agent_memory, agent_studio, candidate_lists, data_subject, digital_twin, email_templates, goals, health_check, hiring_policy, interview_intelligence, job_management, job_vacancies_analytics, journey_mapping, modules, opinions, recruitment_journey, saas_metrics, talent_intelligence, talent_pool, technical_tests, trust_center, workforce | tests/ | 34% domínios sem cobertura | Alta | G |
| **F-401** | L6 | V6 | V6-D9 hiring_policy vs V6-D ?policy | hiring_policy=0 testes | hiring_policy é canonical mas tests/policy=10 (legacy) | tests/ | Confusão sobre qual domain testar | Alta | M |
| **F-402** | L6 | V12.7 | V12.7 fitness | tests/fitness vazio | Diretório criado mas sem implementação | tests/fitness/ | Gap em LLM-as-judge prompts genéricos | Média | M |
| **F-403** | L6 | V12 | tests/chaos, tests/load, tests/contract, tests/characterization | 4 dirs criados mas conteúdo não verificado | tests/{chaos,load,contract,characterization}/ | Não confirmado se implementados ou stubs | Média | M |
| **F-406** | L6 | V14-CFG | CI coverage | Threshold mínimo não configurado | `.coverage` rodando, mas sem `fail-if-coverage-under` | pyproject.toml | Coverage cai sem alerta | Média | P |
| **F-407** | L6 | V12 ML | mutation testing | mutmut/cosmic-ray ausentes | (não detectados) | Testes podem ter blind spots | Baixa | M |
| **F-408** | L7 | V6 | 14 services @deprecated 2026-04-17 | Refatoração fase 7 incompleta | 14 services em `app/shared/services/*` + `bias_audit_service.py` marcados deprecated mas ainda no codebase | shared/services/ | Imports a deprecated podem persistir | Alta | M |
| **F-409** | L7 | V10 | V10-OR1 vs V10-OR2 | 3 orchestrators paralelos | main_orchestrator.py (1785L) + cascaded_router.py (948L) + orchestrator.py (596L) | app/orchestrator/ | Duplicação clara; orchestrator.py legacy | Alta | G |
| **F-410** | L7 | V6 | V6-D9 hiring_policy vs policy | 2 domínios policy | `app/domains/policy/` (~400L, legacy?) vs `app/domains/hiring_policy/` (canonical, completo) | app/domains/{policy,hiring_policy}/ | Confusão de canonical | Alta | M |
| **F-411** | L7 | V6 | TODOs | 79 TODOs não datados | Maioria phase2 (refatoração agendada); 4 stubs em admin_platform | grep -rn TODO | Trabalho não trackeado | Média | M |
| **F-412** | L7 | V6 | type: ignore | 1540 directives | ~2.5% do código evitando type checker | grep `pyright: ignore`/`type: ignore` | Pydantic v2 narrowing? Auditar | Média | G |
| **F-413** | L7 | V6 | __init__.py star imports | 98 files com `from ... import *` | Implicit re-exports, hard to trace | grep | Antipattern documentado mas amplo | Média | M |
| **F-414** | L7 | V8 | V8-W4 (agents_legacy) | agents_legacy.py orfão | 4 tasks Celery (drift.run_batch, agents.wsi_interview.start, agents.triagem.run, agents.sourcing.search). Importadores: apenas __init__.py | [app/jobs/tasks/agents_legacy.py](app/jobs/tasks/agents_legacy.py) | Candidato a deleção segura | Baixa | P |
| **F-416** | L7 | V6 | V6-D23 recruitment_journey | Stub vazio | repos/dependencies/__init__.py mas zero agents/services/tests | recruitment_journey/ | Merge candidate ou deletar | Baixa | P |
| **F-417** | L7 | V10 | main_orchestrator.py | Comments 8.5% | 151 comment lines / 1785 total = 8.5% (esperado 3-5%) | main_orchestrator.py | Refatoração em progresso | Baixa | P |
| **F-419** | L7 | V6 | * imports | 10 files non-init com star imports | Pattern intencional (plugin) mas frouxa documentação | grep | Symbol collision risk | Baixa | P |
| **F-422** | L7 | V7 | V7-A* legacy | 2 paths execução agente | agents_legacy.py + agents.py em paralelo | app/jobs/tasks/ | Dual paths confundem | Média | M |
| **F-423** | L7 | V14-CFG | feature flags | LIA_V2_* não detectados | Flags via env/config (não hardcoded) — neutro | (não em código) | Documentação ausente | Baixa | P |

---

## Lente L1 — Acoplamento e Violações Arquiteturais

**Sumário:** 11 achados (F-001 a F-007, F-015, F-016, mais F-008 e F-018 compartilhados com L2). Padrões dominantes: cross-domain imports diretos sem abstração (sourcing→credits→ai→candidates), LLM clients diretos fora da factory (1 bypass real confirmado em skills_ontology_engine), HTTP clients sem registry centralizado. **Pontos fortes:** linter LLM Factory bem desenhado com ALLOWLIST de 11 paths; circuit_breaker centralizado em `app/shared/resilience/circuit_breaker.py` (APIFY/GEMINI_LIVE/RAILS).

(Detalhes na tabela mestre.)

---

## Lente L2 — Duplicação Funcional

**Sumário:** 7 achados (F-009 a F-014, F-017, F-018). Padrões: tools homônimos cross-domain (`pipeline_tools.py`, `query_tools.py` em múltiplos paths), 2 implementações de memory_resolver, 2 intent classifiers sem factory de roteamento, audit shim duplicado, PII filters paralelos. **Pontos fortes:** 8 libs/ workspace com separação clara (lia-config, lia-utils, lia-audit, lia-messaging, lia-models, lia-agents-core, lia-services, lia-contexts).

---

## Lente L3 — Contratos Implícitos e Fragilidade Tipológica

**Sumário:** 11 achados (F-200 a F-204, F-212 a F-215, F-217, F-219, F-221). Padrão dominante: tool registries com `**kwargs: Any → dict[str, Any]` (20+ instances), endpoints sem `response_model=` (~717 occurrences), Pydantic com Optional excessivo, raw tuple returns em repositories. **Pontos fortes:** 562 schemas Pydantic globais; 102 alembic migrations versionadas; LIAError hierarquia em `app/shared/errors.py`.

---

## Lente L4 — Dívida de Observabilidade

**Sumário:** 11 achados (F-205 a F-211, F-216, F-218, F-220). Padrão: LLM calls sem token tracking pre-call (9+ callers), correlation_id não propagado, OpenTelemetry instrumentação esparsa (16 spans para 1587 imports do tracer), audit `criteria_used` vazio, exceções engolidas em tool wrappers, Sentry sem profiling, LangSmith configurado mas LLM clients não envolvidos. **Pontos fortes:** Sentry PII scrubbing implementado, OpenTelemetry com fallback lightweight tracer, token budget Redis backend com TTL.

---

## Lente L5 — Dívida de Segurança e Compliance (a mais densa)

**Sumário:** 17 achados (F-300, F-302 a F-307, F-309, F-310, F-312, F-313, F-315 a F-318, F-321, F-323 a F-325). 

**Vetores principais:**
- **RLS bypass risks (F-302 a F-306):** 17 modelos sem `company_id` (audit_logs/conversation/technical_tests/activity_feed/agent_activity como críticos); raw SQL em repos depende de `Depends(get_tenant_db)` ser usado.
- **Streaming sem post-compliance (F-315/F-316):** SSE/WS yield chunks sem PII masking em tempo real.
- **Auth gaps (F-309/F-310/F-318/F-323):** DEV_MODE injeção sintética; Rails JWT fallback com late binding; JWT sem validação explícita de exp/aud/iss.
- **LGPD (F-312):** PII models sem `legal_basis_id` ou `consent_version_id`.
- **Audit incompleto (F-324):** `log_decision` sub-utilizado em handlers de API.
- **BYOK enforcement (F-001/F-307/F-325):** 1 bypass real; CI execução do linter não confirmada.

**Pontos fortes:**
- RLS no DB layer (3 migrations: 040+068+102 com FORCE ROW LEVEL SECURITY).
- 10 endpoints DSR LGPD Art. 18 completos (V12.6-EP1 a EP10).
- LegalBasis enum + retention SOX/LGPD documentada por tipo.
- Fairness HTTP 451 handler global + FairnessGuard em autonomous (Tier 6).
- Twilio webhook signature `hmac.compare_digest()` (timing-safe) + fail-closed em prod.
- Linter LLM Factory com ALLOWLIST + BLOCKED_NAMES.

---

## Lente L6 — Dívida de Testes

**Sumário:** 6 achados (F-400 a F-403, F-406, F-407). Padrão: 22/63 domínios (35%) sem teste unit; tests/fitness vazio; 4 dirs (chaos, load, contract, characterization) sem conteúdo confirmado; coverage CI sem threshold; mutation testing ausente.

**Pontos fortes (excepcionais):**
- 552 test files em 29 dirs.
- Eval framework rico: tests/deepeval (agent quality), tests/llm_eval (reasoning), tests/ragas (RAG), tests/golden (scenarios), tests/fairness (4-fifths rule + bias detector), tests/security (16 arquivos com prompt injection harness, tenant isolation, red-team PII/fairness).
- 102 alembic migrations versionadas, sem orfandade.

---

## Lente L7 — Dead Code e Ortodoxia Frouxa

**Sumário:** 11 achados (F-408 a F-414, F-416, F-417, F-419, F-422, F-423). Padrão: 14 services deprecated 2026-04-17 ainda no codebase; 3 orquestradores em paralelo (main_orchestrator + cascaded_router + orchestrator legacy); policy/ vs hiring_policy/ duplicados; 79 TODOs phase2; 1540 type: ignore; 98 `from ... import *` em __init__.py; agents_legacy.py orfão funcional.

**Pontos fortes:** Phase-2 refactoring documentado via TODOs + @deprecated tags (visibilidade do trabalho em progresso).

---

## Achados por Vista da Cartografia

### V1 (Mapa de Contexto) — 0 achados específicos
*(referente apenas — atores externos não geram achados de código).*

### V2 (Mapa de Propósito) — 0 achados específicos

### V3 (Topologia de Runtime) — 0 achados em código (referente: F-409 sobre orchestrators paralelos não roda em containers separados)

### V4 (Mensageria) — 1 achado relacionado (F-414 agents_legacy.py com 4 tasks Celery)

### V5 (Topologia de Dados) — 5 achados
- F-008 HTTP sem abstração
- F-018 HTTP timeouts duplicados

### V6 (Domínios DDD) — 14 achados
- F-002 a F-007 cross-domain coupling
- F-015, F-016 LLM bypass em domains
- F-400 22 domínios sem testes
- F-401 hiring_policy vs policy duplicados
- F-408 14 services deprecated
- F-410 policy/ legacy
- F-416 recruitment_journey stub
- F-411, F-412, F-413 dead code

### V7 (Catálogo de Agentes) — 1 achado
- F-422 agents_legacy.py paths paralelos

### V8 (Subagentes/Workers) — 1 achado
- F-414 agents_legacy.py orfão

### V9 (Tools e Actions) — 9 achados
- F-009 pipeline_tools.py duplicado 2x
- F-010 query_tools.py 3x
- F-200 tools dict[str,Any]
- F-212 ToolDefinition output_schema missing
- F-214 exception silent em wrappers
- F-219 kwargs não tipificados
- F-313 tool safety category informal

### V10 (Cascade Router e Orquestração) — 7 achados
- F-007 action_handlers acoplados
- F-203, F-213 return types missing
- F-208, F-220 OpenTelemetry esparsa
- F-409 3 orchestrators paralelos
- F-417 main_orchestrator com 8.5% comments

### V11 (Matriz Capacidades) — 0 achados diretos (matriz é descritiva)

### V12 (Cross-cutting) — 25 achados (a vista mais auditada)

| Sub-vista | Achados |
|---|---|
| V12.1 Fairness | (nenhum direto — Fairness está bem implementado) |
| V12.2 PII | F-014 PII filters paralelos; F-315/F-316 streaming sem post-compliance; F-321 encryption parcial |
| V12.3 Prompt Injection | (nenhum direto) |
| V12.4 Intent Classifier | F-006 LLM intent coupling; F-012 duplicação intent_classifier |
| V12.5 Audit Log | F-013 shim duplicado; F-017 multi-loggers; F-209 criteria_used vazio; F-218 sem alerting expiry; F-302 audit_logs sem company_id; F-324 log_decision sub-utilizado |
| V12.6 LGPD | F-312 PII sem legal_basis |
| V12.7 Output Guardrails | F-402 tests/fitness vazio |
| V12.8 Memory | F-011 memory_resolver duplicado; F-204 raw tuple returns |
| V12.9 RAG | F-003 sourcing→RAG coupling |
| V12.10 LLM Factory + BYOK | F-001 bypass real; F-205 sem token tracking; F-211 LangSmith não envolvido; F-325 linter CI não validado |
| V12.11 Multi-tenancy + RLS | F-302 a F-306, F-323 (6 achados de RLS bypass) |
| V12.12 ML Pipelines | (sem achados diretos de auditoria) |

### V13 (Caminhos Canônicos) — 4 achados
- F-205 LLM sem token tracking em F2/F3
- F-206 correlation_id não propagado
- F-315/F-316 streaming sem post-compliance em F2

### V14 (Configuração e Runtime) — 8 achados
- F-201 endpoints sem response_model
- F-207 Sentry sem profiling
- F-216 sync request_id
- F-300 health endpoints PUBLIC_PATHS
- F-309 DEV_MODE bypass
- F-310 Rails JWT fallback
- F-317 CORS config
- F-318 JWT validation
- F-406 CI coverage threshold

---

*Fim da Auditoria Sobreposta v1.0. Todos os achados F-NNN têm IDs cartográficos referenciados — prontos para Plano de Remediação Priorizado (`REMEDIACAO_PRIORIZADA.md`).*
