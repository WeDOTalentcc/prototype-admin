# ROUTES_ENDPOINTS_AUDIT.md
## Protocolo PX02 — Inventário Completo de Rotas e Endpoints WeDOTalent/LIA
**Data:** 2026-04-14  
**Executado por:** Claude Code (claude-sonnet-4-6)

---

## CABEÇALHO — CONTAGENS

| Fonte | Quantidade |
|---|---|
| Rotas Rails (`ats-api-copia`) | ~65 rotas explícitas + resources |
| Módulos Python registrados em `routes.py` | ~200+ módulos → ~362 endpoints declarados |
| Proxy routes no frontend (`backend-proxy`) | **478 route.ts files** |
| Serviços de API no frontend (`lia-api/`) | 9 arquivos de cliente API |
| Webhooks de entrada (Python) | 6 endpoints de webhook |
| Integrações externas confirmadas | Merge.dev (ATS), Mailgun, Twilio, OpenMic.ai, WhatsApp, WorkOS, Microsoft Graph |

---

## SEÇÃO 1 — INVENTÁRIO RAILS (`ats-api-copia`)

### Arquitetura de Auth Rails
- JWT simples via `secret_key_base` (não WorkOS)
- `before_action :authorize_request` em todos os controllers `v1/users/`
- **Sem tenant scope explícito nas queries** — usa `account_id` apenas no momento de criação, não filtra leituras

### Tabela de Rotas Rails

| Método | Rota | Controller#Action | Arquivo controller existe? | Tenant Scoped? |
|--------|------|-------------------|--------------------|----------------|
| POST | `/cable` (WS) | ActionCable server | Sim (ActionCable) | N/A |
| GET | `/up` | rails/health#show | Sim (interno Rails) | Não |
| GET | `/service-worker` | rails/pwa#service_worker | Sim (interno Rails) | Não |
| GET | `/manifest` | rails/pwa#manifest | Sim (interno Rails) | Não |
| POST | `/v1/sessions` | v1/sessions#create | Sim | Não (login público) |
| GET | `/v1/me` | v1/sessions#me | Sim | Sim (requires auth) |
| POST | `/v1/logout` | v1/sessions#logout | Sim | Sim (requires auth) |
| GET | `/v1/users/applies` | v1/users/applies#index | Sim | PARCIAL — filtra por `account_id` só no create |
| GET | `/v1/users/applies/:id` | v1/users/applies#show | Sim | NAO — sem scope por account |
| POST | `/v1/users/applies` | v1/users/applies#create | Sim | PARCIAL — `account_id` adicionado no merge |
| PUT | `/v1/users/applies/:id` | v1/users/applies#update | Sim | Não |
| DELETE | `/v1/users/applies/:id` | v1/users/applies#destroy | Sim | Não |
| GET | `/v1/users/jobs` | v1/users/jobs#index | Sim | PARCIAL |
| GET | `/v1/users/jobs/:id` | v1/users/jobs#show | Sim | Não |
| POST | `/v1/users/jobs` | v1/users/jobs#create | Sim | PARCIAL |
| PUT | `/v1/users/jobs/:id` | v1/users/jobs#update | Sim | Sim (ensure_owner) |
| DELETE | `/v1/users/jobs/:id` | v1/users/jobs#destroy | Sim | Sim (ensure_owner) |
| GET | `/v1/users/selective_processes` | v1/users/selective_processes#index | Sim | PARCIAL |
| GET | `/v1/users/selective_processes/:id` | v1/users/selective_processes#show | Sim | Não |
| POST | `/v1/users/selective_processes` | v1/users/selective_processes#create | Sim | PARCIAL |
| PUT | `/v1/users/selective_processes/:id` | v1/users/selective_processes#update | Sim | Não |
| DELETE | `/v1/users/selective_processes/:id` | v1/users/selective_processes#destroy | Sim | Não |
| GET | `/v1/users/candidates` | v1/users/candidates#index | Sim | PARCIAL |
| GET | `/v1/users/candidates/:id` | v1/users/candidates#show | Sim | Não |
| POST | `/v1/users/candidates` | v1/users/candidates#create | Sim | PARCIAL |
| PUT | `/v1/users/candidates/:id` | v1/users/candidates#update | Sim | Não |
| DELETE | `/v1/users/candidates/:id` | v1/users/candidates#destroy | Sim | Não |
| GET | `/v1/users/search` | v1/users/users#index | Sim | Não |
| GET | `/v1/users/search/:id` | v1/users/users#show | Sim | Não |
| POST | `/v1/users/create` | v1/users/users#create | Sim | Não |
| PUT | `/v1/users/edit/:id` | v1/users/users#update | Sim | Não |
| DELETE | `/v1/users/delete/:id` | v1/users/users#destroy | Sim | Não |
| GET | `/v1/users/messages` | v1/users/messages#index | Sim | PARCIAL |
| GET | `/v1/users/messages/:id` | v1/users/messages#show | Sim | Não |
| POST | `/v1/users/messages` | v1/users/messages#create | Sim | PARCIAL |
| PUT | `/v1/users/messages/:id` | v1/users/messages#update | Sim | Não |
| DELETE | `/v1/users/messages/:id` | v1/users/messages#destroy | Sim | Não |
| GET/POST/PUT/DELETE | `/v1/users/client_accounts(/:id)` | v1/users/client_accounts#* | Sim | Sim (account_id merge no create, before_action) |
| GET/POST/PUT/DELETE | `/v1/users/client_users(/:id)` | v1/users/client_users#* | Sim | Sim |
| GET/POST/PUT/DELETE | `/v1/users/company_profiles(/:id)` | v1/users/company_profiles#* | Sim | Sim |
| GET/POST/PUT/DELETE | `/v1/users/departments(/:id)` | v1/users/departments#* | Sim | Sim |
| GET/POST/PUT/DELETE | `/v1/users/email_templates(/:id)` | v1/users/email_templates#* | Sim | Sim |
| GET/POST/PUT/DELETE | `/v1/users/interviews(/:id)` | v1/users/interviews#* | Sim | Sim |
| GET/POST/PUT/DELETE | `/v1/users/notifications(/:id)` | v1/users/notifications#* | Sim | Não confirmado |
| GET/POST/PUT/DELETE | `/v1/users/talent_pools(/:id)` | v1/users/talent_pools#* | Sim | PARCIAL |
| GET | `/v1/users/talent_pools/:id/candidates` | v1/users/talent_pools#candidates | Sim | PARCIAL |
| POST | `/v1/users/talent_pools/:id/add_candidates` | v1/users/talent_pools#add_candidates | Sim | PARCIAL |
| POST | `/v1/users/talent_pools/:id/move_to_job` | v1/users/talent_pools#move_to_job | Sim | PARCIAL |
| POST | `/v1/users/talent_pools/:id/create_job_from_pool` | v1/users/talent_pools#create_job_from_pool | Sim | PARCIAL |
| GET/POST/PUT/DELETE | `/v1/users/recruitment_campaigns(/:id)` | v1/users/recruitment_campaigns#* | Sim | Não confirmado |
| POST | `/v1/users/recruitment_campaigns/:id/advance_stage` | v1/users/recruitment_campaigns#advance_stage | Sim | Não confirmado |
| POST | `/v1/users/recruitment_campaigns/:id/complete_stage` | v1/users/recruitment_campaigns#complete_stage | Sim | Não confirmado |
| POST | `/v1/users/recruitment_campaigns/:id/add_checkpoint` | v1/users/recruitment_campaigns#add_checkpoint | Sim | Não confirmado |

### Observações Rails
- **JWT isolado:** Rails usa seu próprio JWT (HS256 com `secret_key_base`), enquanto Python usa WorkOS. Esses sistemas são **incompatíveis** — um token Rails não funciona no Python e vice-versa.
- **Sem concern `TenantScoped`:** Nenhum concern de tenant foi encontrado. O scope é feito manualmente pelo `account_id` no momento de criação, mas **leituras e updates não filtram por tenant**.
- **Sem CSRF para JSON:** `protect_from_forgery with: :null_session` usado na sessions_controller — adequado para APIs JSON.

---

## SEÇÃO 2 — INVENTÁRIO PYTHON AI (`lia-agent-system`)

### Arquitetura
- FastAPI com ~200 módulos registrados via `register_all_routes(app)` em `app/api/routes.py`
- Todos prefixados com `/api/v1/` (salvo exceções)
- Auth via `AuthEnforcementMiddleware` (WorkOS JWT + `company_id` multi-tenant)
- Orquestrador em `/api/orchestrator/` (sem `/v1/`)
- Proxy do frontend: `/api/backend-proxy/*` → aponta para `BACKEND_URL` (Python, porta 8001)

### Agrupamento por Domínio

#### HEALTH / INFRA
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `system_health` | `/api/v1` | GET `/health`, GET `/health/detailed` |
| `health_check` | `/api/v1` | GET `/health-check` |
| `health_langgraph` | `/api/v1` | GET `/health/langgraph` |
| `rails_health` | `/api/v1/rails` | GET `/health`, GET `/status` |
| `rails_sync` | `/api/v1` | (sync routes) |

#### AUTH
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `auth` | `/api/v1` | POST `/auth/login`, GET `/auth/me`, POST `/auth/logout` |
| `workos` | `/api/v1` | GET `/workos/auth-url`, POST `/workos/callback` |
| `workos.scim_router` | `/api/v1` | SCIM 2.0 provisioning |
| `workos.webhook_router` | `/api/v1` | POST `/workos/webhook` |
| `workos.public_auth_router` | `/api/v1` | Public auth endpoints |

#### CANDIDATOS
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `candidates` | `/api/v1/candidates` | CRUD completo, `/search`, `/bulk/*`, `/toon`, `/stage`, `/files` |
| `candidate_search` | `/api/v1` | GET `/candidates/search` |
| `candidate_lists` | `/api/v1/candidate-lists` | CRUD de listas de candidatos |
| `toon_router` | `/api/v1` | GET `/candidates/{id}/toon` |
| `rag_search_router` | `/api/v1` | POST `/rag-search/candidates` |
| `candidate_compare` | `/api/v1` | POST `/candidates/compare` |

#### VAGAS (JOBS)
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `job_vacancies` | `/api/v1` | CRUD vagas, `/publish`, `/status`, `/metrics`, `/duplicate`, `/sourcing-status`, `/generate-public-link` |
| `job_vacancies.router_public` | `/api/v1/public-vacancies` | GET `p/{slug}`, POST `p/{slug}/apply` |
| `job_drafts` | `/api/v1` | CRUD rascunhos |
| `jd_generation` | `/api/v1` | POST `/jd/generate` |
| `jd_import` | `/api/v1/learning` | POST (upload JD) |
| `job_board` | `/api/v1` | POST `/job-boards/linkedin/publish/{id}`, POST `/job-boards/indeed/publish/{id}`, GET `/job-boards/status/{id}` |
| `job_analytics` | `/api/v1` | GET `/job-analytics` |
| `job_templates` | `/api/v1` | CRUD templates de vaga |
| `job_qualification` | `/api/v1` | GET/POST `/jobs/qualification` |
| `job_embeddings` | `/api/v1` | POST `/job-embeddings/fast-track/record-usage`, POST `/job-embeddings/outcome` |

#### PIPELINE / KANBAN
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `pipeline` | `/api/v1/pipeline` | GET overview, transitions |
| `applications` | `/api/v1` | CRUD candidaturas |
| `recruitment_stages` | `/api/v1/recruitment-stages` | CRUD stages, reorder, sub-statuses |
| `stage_transition_automation` | `/api/v1/stage-automation` | GET/POST automações |
| `kanban_assistant` | `/api/v1` | POST `/lia/kanban-assistant` |
| `pipeline_templates` | `/api/v1` | CRUD templates de pipeline |
| `pipeline_orchestrator_router` | `/api/v1` | Orchestrated pipeline |
| `pipeline_policy_router` | `/api/v1` | Políticas de pipeline |
| `pipeline_velocity` | `/api/v1` | GET `/pipeline-velocity`, `/bottlenecks` |
| `pipeline_prediction` | `/api/v1` | Previsões ML |

#### SOURCING / TALENT POOLS
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `sourcing` | `/api/v1` | Boolean search, sourcing results |
| `sourcing_pipeline` | `/api/v1` | GET `/config`, POST `/run/{job_id}`, POST `/run-all` |
| `sourcing_orchestrator_router` | `/api/v1` | Orchestrated sourcing |
| `sourcing_agents_router` | `/api/v1` | CRUD sourcing agents |
| `talent_funnel` | `/api/v1` | GET `/talent-funnel` |
| `talent_pools` | `/api/v1` | CRUD talent pools + actions |
| `multi_strategy_router` | `/api/v1` | POST `/sourcing/multi-strategy` |

#### ENTREVISTAS / AGENDAMENTO
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `interviews` | `/api/v1` | CRUD entrevistas |
| `scheduling` | `/api/v1` | `/scheduling/link`, confirmar slots |
| `interview_notes` | `/api/v1` | CRUD notas de entrevista |
| `interview_analysis` | `/api/v1` | Análise pós-entrevista |
| `calendar` | `/api/v1` | Google Calendar auth, reschedule |
| `self_scheduling_public` | `/api/v1` | Página pública de autoagendamento |
| `calibration` | `/api/v1` | Start/feedback calibração |
| `rubric_evaluation` | `/api/v1/rubrics` | Avaliação por rubrica |
| `technical_tests` | `/api/v1` | Testes técnicos |

#### COMUNICAÇÃO / VOZ
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `communications` | `/api/v1` | Email, WhatsApp, Teams para candidatos |
| `communication` | `/api/v1` | POST `/communication/send-email`, `/send-whatsapp`, `/send-screening-invite` |
| `email` | `/api/v1` | Email endpoints |
| `email_templates` | `/api/v1` | CRUD email templates |
| `whatsapp` | `/api/v1` | WhatsApp outbound |
| `voice` | `/api/v1` | GET `/voice/health`, POST `/voice/transcribe`, `/analyze`, `/interview` |
| `twilio_voice` | `/api/v1` | Twilio voice callbacks |
| `gemini_voice` | `/api/v1` | Gemini voice screening |
| `voice_stream` | `/api/v1` | POST `/voice-stream/start-session` |
| `openmic_webhook` | `/api/v1/openmic` | POST `/webhook`, GET `/webhook/health` |
| `teams` | `/api/v1` | Microsoft Teams integration |
| `notifications` | `/api/v1` | CRUD notificações, unread-count |
| `digest` | `/api/v1` | Weekly digest |

#### WSI (ENTREVISTA ESTRUTURADA)
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `wsi_endpoints` | (sem prefix) | WSI umbrella router |
| `wsi_router` | (sem prefix `/api/v1`) | GET/POST `/wsi/*` |
| `wsi_async_v1` | `/api/v1` | POST `/wsi-async/invite`, GET/POST `/wsi-async/{token}` |
| `wsi_questions` | `/api/v1` | GET/POST `/wsi/questions/{jobId}` |
| `wsi_screening_pipeline_endpoint` | `/api/v1` | POST `/wsi/screening-pipeline` |
| `wsi_question_adjust` | `/api/v1` | POST `/wsi/questions/adjust` |
| `wsi_observability` | `/api/v1` | Observabilidade WSI |
| `triagem` | `/api/v1` | POST `/triagem/*` |
| `screening` | `/api/v1` | CV screening |

#### COMPLIANCE / LGPD
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `lgpd_compliance` | `/api/v1` | LGPD endpoints |
| `compliance_controls` | `/api/v1` | Controles de compliance |
| `bias_audit` | `/api/v1` | POST `/bias-audit` |
| `admin_bias_audit` | `/api/v1` | Admin bias audit |
| `guardrails` | `/api/v1` | CRUD guardrails de agentes |
| `trust_center` | `/api/v1` | Trust Center |
| `audit_logs` | `/api/v1` | GET `/audit-logs`, export |
| `data_subject_requests` | `/api/v1` | DSR CRUD + ações |
| `consent_management` | `/api/v1` | Consentimento LGPD |
| `granular_consent_router` | `/api/v1` | Consentimento granular |
| `admin_lgpd_router` | `/api/v1` | Admin LGPD |

#### AGENTES / AI
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `orchestrator_routes` | `/api/orchestrator` | POST `/process`, WebSocket |
| `hitl_router` | `/api/v1` | GET `/hitl/pending`, POST approve/reject |
| `agent_chat_ws_router` | (sem prefix) | WebSocket `/ws/agent-chat/{session_id}` |
| `agent_chat_sse_router` | `/api/v1` | SSE `/agent-chat/stream` |
| `agent_memory_router` | `/api/v1` | GET/POST `/agent-memory/*` |
| `custom_agents_router` | `/api/v1` | CRUD custom agents |
| `agent_deployments_router` | `/api/v1` | Deployments de agentes |
| `agent_templates_router` | `/api/v1` | Templates de agentes |
| `sourcing_agents_router` | `/api/v1` | Sourcing agents |
| `digital_twins_router` | `/api/v1` | Digital twins |
| `lia_assistant` | `/api/v1` | GET/POST `/lia/*` |
| `wizard_smart_orchestrator` | `/api/v1/wizard` | POST `/smart-orchestrate` |

#### ADMIN / OBSERVABILIDADE
| Módulo | Prefix | Endpoints Principais |
|--------|--------|----------------------|
| `admin` | `/api/v1` | Admin geral |
| `admin_platform` | `/api/v1` | Admin plataforma |
| `admin_token_budget` | `/api/v1` | Token budget por empresa |
| `admin_prompts` | `/api/v1` | CRUD prompts |
| `admin_cb_router` | `/api/v1` | Circuit breakers |
| `admin_dlq_router` | `/api/v1` | Dead letter queue |
| `admin_lgpd_router` | `/api/v1` | LGPD admin |
| `observability` | `/api/v1` | GET `/observability` |
| `traces_router` | `/api/v1` | Traces LangSmith |
| `drift` | `/api/v1` | Model drift detection |
| `ab_testing` | `/api/v1` | A/B testing |
| `cache` | `/api/v1` | Cache management |

#### WEBHOOKS (ENTRADA)
| Módulo | Prefix Final | Endpoints |
|--------|-------------|-----------|
| `external_webhooks` | `/api/v1/external-webhooks` | POST `/ats/{platform}`, POST `/interview/{provider}`, POST `/document/{provider}`, GET `/event-log`, GET `/health` |
| `merge_webhooks` | `/api/v1/webhooks/merge` | POST `/` |
| `mailgun_webhooks` | `/api/v1/webhooks/mailgun` | POST `` |
| `openmic_webhook` | `/api/v1/openmic` | POST `/webhook`, GET `/webhook/health` |
| `whatsapp_webhook` | `/api/v1/whatsapp` | POST `/webhook`, POST `/flow-webhook`, POST `/status-callback` |
| `job_status_webhooks` | `/api/v1/job-status-webhooks` | POST `/register`, GET `/`, GET `/{id}`, PATCH `/{id}`, DELETE `/{id}`, POST `/{id}/test`, GET `/{id}/logs`, GET `/events/available` |
| `workos.webhook_router` | `/api/v1` | POST `/workos/webhook` |
| `email_tracking` | `/api/v1` | Email tracking callbacks |

---

## SEÇÃO 3 — INVENTÁRIO FRONTEND (Next.js `plataforma-lia`)

### Arquitetura do Frontend
- **Proxy universal:** Frontend (Next.js) usa `BACKEND_URL = '/api/backend-proxy'` como base
- **`/api/backend-proxy`** são Next.js API Routes que fazem proxy para `BACKEND_URL` = `http://127.0.0.1:8001` (Python FastAPI)
- **478 route.ts files** mapeando endpoints Python
- **NÃO existe integração direta do frontend com o Rails** — todo tráfego passa pelo Python
- **LIA proxy especial:** `/api/lia/[...path]` → catch-all para Python em `/api/v1/*`

### Frontend → Python: Chamadas Confirmadas por Módulo

| Domínio Frontend | URLs Chamadas | Backend Python existe? |
|-----------------|---------------|------------------------|
| `jobs-api.ts` | `/job-vacancies`, `/job-vacancies/{id}`, `/job-vacancies/{id}/publish`, `/job-vacancies/{id}/status`, `/job-vacancies/{id}/metrics`, `/job-vacancies/{id}/duplicate`, `/job-vacancies/{id}/confirm-global-search`, `/job-vacancies/{id}/sourcing-status`, `/job-vacancies/{id}/generate-public-link`, `/job-boards/linkedin/publish/{id}`, `/job-boards/indeed/publish/{id}`, `/job-boards/status/{id}`, `/job-boards/unpublish/{id}/{platform}`, `/job-boards/publish-batch`, `/job-vacancies/stats/overview`, `/job-vacancies/search`, `/notifications/recruiter-action`, `/communications/transfer`, `/job-embeddings/fast-track/record-usage`, `/job-embeddings/outcome` | Sim (todos no Python) |
| `candidates-api.ts` | `/candidates/search`, `/candidates/search/local/`, `/candidates/search/by-job-description`, `/candidates/health`, `/credits/balance`, `/candidates/`, `/candidates/{id}`, `/lia/job-wizard/salary-benchmark` | Sim (todos no Python) |
| `chat-api.ts` | `/chat`, `/chat/with-attachments`, `/chat/`, `/orchestrator/process`, `/lia/job-wizard/interpret`, `/lia/conversational`, `/lia/active-draft`, `/wizard/smart-orchestrate/` | Sim (todos no Python) |
| `wsi-api.ts` | `/wsi/*` | Sim |
| `voice-api.ts` | `/voice/health`, `/voice/transcribe`, `/voice/interview` | Sim |
| `email-api.ts` | `/email-templates/*`, `/communication/send-email` | Sim |
| `notifications-api.ts` | `/notifications/*`, `/notifications/unread-count` | Sim |
| `bulk-api.ts` | `/candidates/bulk/*`, `/jobs/bulk/*` | Sim |
| `misc-api.ts` | `/health`, variados | Sim |

### Frontend → Rails: Nenhuma chamada direta encontrada
O frontend **não chama o Rails diretamente**. Todo o tráfego passa pelo Python via proxy.

---

## SEÇÃO 4 — INVENTÁRIO AGENT TOOLS (Ferramentas dos Agentes)

### Rails Adapter (Python → Rails)
O `RailsAdapter` em `app/domains/integrations_hub/services/rails_adapter.py` é a ponte principal:
- Usa `RAILS_API_URL` + `RAILS_API_TOKEN` para chamadas service-to-service
- Mapeia: candidates, jobs, applies, selective_processes, messages
- **Circuit breaker** `RAILS_CIRCUIT` protege todas as chamadas
- Fallback para DB local Python quando Rails não disponível

### Mapeamento Campos Fork ↔ Rails (confirmado no adapter)
| Entidade | Campos mapeados Fork→Rails |
|----------|---------------------------|
| Candidate | ~60 campos (name, email, phone, linkedin, resume_url, diversity_*, skills, etc.) |
| Job | ~35 campos (title, description, status, employment_type, seniority_level, salary_range, etc.) |
| Apply | candidate_id, job_id, selective_process_id, account_id |
| Selective Process | mapeado |
| Message | mapeado |

### Integrações Externas Confirmadas (Python → Terceiros)
| Serviço | URL | Módulo |
|---------|-----|--------|
| Merge.dev (ATS) | `https://api.merge.dev/api/ats/v1` | `app/domains/ats_integration/` |
| OpenMic.ai (Voice) | Inbound webhook | `app/api/v1/openmic_webhook.py` |
| Twilio (Voice/SMS) | Inbound webhook + outbound API | `app/api/v1/twilio_voice.py` |
| Mailgun (Email) | Inbound webhook | `app/api/v1/mailgun_webhooks.py` |
| WhatsApp / Meta | Inbound + outbound | `app/api/v1/whatsapp*.py` |
| WorkOS (SSO) | Inbound webhook + OAuth | `app/api/v1/workos.py` |
| Microsoft Graph | Calendar + Teams | `app/api/v1/microsoft_graph.py` |
| Pearch AI | Candidate search (190M+ profiles) | `app/api/v1/candidates/` |

---

## SEÇÃO 5 — WEBHOOKS (ENTRADA E SAÍDA)

### Webhooks de Entrada (inbound) — Python
| Webhook | URL Completa | Autenticado? | Propósito |
|---------|-------------|-------------|-----------|
| OpenMic.ai | `POST /api/v1/openmic/webhook` | Sim (HMAC-SHA256) | Conclusão de entrevista por voz |
| WhatsApp Meta | `POST /api/v1/whatsapp/webhook` | Parcial (verificação token) | Mensagens WhatsApp recebidas |
| WhatsApp Flow | `POST /api/v1/whatsapp/flow-webhook` | Parcial | Fluxos interativos WA |
| WhatsApp Status | `POST /api/v1/whatsapp/status-callback` | Não | Status de entrega |
| Merge.dev ATS | `POST /api/v1/webhooks/merge` | Não confirmado | Sync dados ATS externos |
| Mailgun | `POST /api/v1/webhooks/mailgun` | Não confirmado | Email events (bounces, opens) |
| WorkOS | `POST /api/v1/workos/webhook` | Sim (WorkOS signature) | SSO events (user.created, etc.) |
| Job Status Webhooks | `POST /api/v1/job-status-webhooks/register` | Sim (auth middleware) | Cadastro de webhooks de clientes (renomeado em #234 para evitar colisão com `/api/v1/webhooks/*` da plataforma) |
| Email Tracking | `/api/v1` (tracking) | Parcial | Open/click tracking |

### Webhooks de Saída (outbound) — Python para clientes
| Evento | Mecanismo | Status |
|--------|-----------|--------|
| Job status changes | `job_status_webhooks.py` — delivery para URLs cadastradas | Implementado |
| Stage transitions | Event sourcing via RabbitMQ → consumer | Implementado |
| Screening completed | Notificações + webhooks | Implementado |

### Rails: Sem Webhooks
Nenhum webhook foi encontrado no `ats-api-copia`. O Rails não tem sistema de webhooks.

---

## SEÇÃO 6 — GAPS: ANÁLISE CRUZADA

### A. ROTAS FANTASMA (Backend define, ninguém chama)

**Rails — Rotas sem uso identificado pelo frontend ou Python:**
- `GET /v1/users/search` — duplica funcionalidade de `/v1/users/candidates`
- `GET /v1/users/search/:id` — duplica `/v1/users/candidates/:id`
- `POST /v1/users/create` — rota não-REST (deveria ser POST `/v1/users`)
- `PUT /v1/users/edit/:id` — rota não-REST (deveria ser PUT `/v1/users/:id`)
- `DELETE /v1/users/delete/:id` — rota não-REST

**Python — Módulos registrados de baixa visibilidade:**
- `test_activities` — endpoints de teste que podem estar em produção
- `finetuning_export` — exportação para fine-tuning (operacional interno)
- `experience_highlights` — sem proxy frontend confirmado
- `big_five` — sem proxy frontend confirmado
- `affirmative` — sem proxy frontend confirmado
- `saturation` — sem proxy frontend confirmado
- `wsi_observability` — observabilidade interna

### B. CHAMADAS ORFAS ★★★ (Alguém chama, rota não existe ou pode não existir)

**CRITICO — Frontend chama Python, confirmar existência:**
| URL Chamada (frontend) | Existe no Python? | Risco |
|------------------------|-------------------|-------|
| `/api/backend-proxy/pipeline-overview` | Não encontrado explicitamente (pode estar em `pipeline.py`) | MEDIO |
| `/api/backend-proxy/pipeline-pulse` | Não encontrado explicitamente | ALTO |
| `/api/backend-proxy/enhance-prompt` | Não encontrado em routes.py | ALTO |
| `/api/backend-proxy/interpret-context` | Não encontrado em routes.py | ALTO |
| `/api/backend-proxy/transcribe/audio` | Pode ser `/voice/transcribe` — path diferente | MEDIO |
| `/api/backend-proxy/transition/execute` | Não encontrado — pode ser `stage_transition_automation` | ALTO |
| `/api/backend-proxy/proactive-insights` | `proactive_actions_router` existe mas path pode divergir | MEDIO |
| `/api/backend-proxy/insurance/[...path]` | **NÃO EXISTE no Python** | CRITICO |
| `/api/backend-proxy/stage-catalog` | Não encontrado em routes.py | ALTO |
| `/api/backend-proxy/company-pipeline` | Não encontrado — pode ser `pipeline.router` | MEDIO |
| `/api/backend-proxy/jobs/[id]/pipeline` | Path diferente do `/api/v1/pipeline` | MEDIO |
| `/api/backend-proxy/jobs/[id]/report` | Não confirmado em routes.py | ALTO |
| `/api/backend-proxy/jobs/[id]/screening-config` | Não confirmado | ALTO |
| `/api/backend-proxy/journey` | `journey_mapping` existe mas path pode divergir | MEDIO |
| `/api/backend-proxy/ml/predict/salary` | `salary_benchmark_router` existe mas path pode ser `/salary-benchmark` | MEDIO |
| `/api/backend-proxy/ml/predict/time-to-fill` | `pipeline_prediction` existe mas path a confirmar | MEDIO |
| `/api/backend-proxy/search/reveal` | Não confirmado (busca externa Pearch?) | ALTO |
| `/api/backend-proxy/search/similar/combine-profiles` | Não confirmado | ALTO |

**CRITICO — Frontend chama Rails mas Rails não tem a rota:**
- Frontend → Python → Rails via adapter: para candidates/jobs/applies
- Rails tem apenas 65 rotas; Python tem ~362 endpoints
- **Funcionalidades que o frontend usa mas Rails não tem:** agendamento, WSI, analytics, LGPD, bias audit, AI scoring — tudo está SOMENTE no Python

**CRITICO — `/api/backend-proxy/insurance/[...path]`:**
Este proxy de `insurance` não tem correspondente no Python. Chamadas retornarão 404.

### C. ROTAS SEM TENANT SCOPE

**Rails (CRITICO):**
- Praticamente todos os `index` e `show` do Rails não filtram por `account_id`
- Um usuário autenticado pode chamar `GET /v1/users/candidates` e ver candidatos de outras contas
- Afeta: applies, jobs, selective_processes, candidates, messages, users
- Rotas com tenant parcial (apenas no create): `client_accounts`, `company_profiles`, `departments`, `email_templates`, `interviews`

**Python:**
- `AuthEnforcementMiddleware` injeta `company_id` em todos os requests autenticados
- Porém dependência de cada controller usar corretamente o `company_id` — risco de drift

### D. ROTAS SEM AUTENTICAÇÃO

**Rails — Rotas públicas (intencional):**
- `GET /up` — health check infraestrutura (OK)
- `GET /service-worker`, `GET /manifest` — PWA (OK)
- `POST /v1/sessions` — login (OK)

**Rails — Rotas com possível gap:**
- `GET /v1/me` e `POST /v1/logout` exigem auth via `before_action :authorize_request` na sessions_controller ✓
- Controllers `v1/users/*` têm `before_action :authorize_request` ✓

**Python — Rotas públicas identificadas:**
- `GET /health`, `/health-check` — health checks (OK)
- `/portal/data-request` — portal do candidato (OK, design intencional)
- `/public/shared/*` — buscas compartilhadas (OK, design intencional)
- `/api/v1/public-vacancies/p/{slug}`, `/apply` — candidatura pública (OK)
- `GET /api/v1/self-scheduling/{token}` — autoagendamento (OK)
- `POST /api/v1/openmic/webhook` — webhook externo (protegido por HMAC, não JWT)
- `GET /api/v1/rails/health`, `GET /api/v1/rails/status` — monitoramento infra (OK, documentado)

---

## SUMÁRIO EXECUTIVO

### Score de Saúde das Rotas

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| Cobertura Rails→Frontend | 2/10 | Frontend não usa Rails diretamente; Rails tem ~65 rotas vs ~362 no Python |
| Tenant Scoping Rails | 2/10 | Apenas criação de recursos filtra por tenant; leituras são globais — risco de vazamento de dados |
| Tenant Scoping Python | 7/10 | Middleware garante `company_id`, mas implementação por módulo pode variar |
| Autenticação Rails | 6/10 | JWT próprio (incompatível com WorkOS), before_action presente, mas token nunca expira via logout (stateless) |
| Autenticação Python | 8/10 | WorkOS + AuthEnforcementMiddleware + circuit breakers |
| Cobertura Frontend→Python | 8/10 | 478 proxy routes cobrem bem os ~362 endpoints Python |
| Webhooks | 7/10 | Boa cobertura de entrada, HMAC em openmic, sem validação confirmada em mailgun/merge |
| Integração Rails↔Python | 3/10 | RailsAdapter existe e tem field mapping completo, mas `RAILS_API_URL` pode não estar configurado em produção |
| **Score Geral** | **5/10** | Plataforma funcionalmente rica no Python, Rails subutilizado e com gaps de segurança |

### Achados Críticos (Prioridade de Ação)

**P0 — Segurança Imediata:**
1. **Rails sem tenant scope nas leituras** — qualquer usuário autenticado pode listar dados de outras empresas via `/v1/users/candidates`, `/v1/users/jobs`, etc.
2. **JWT Rails incompatível com WorkOS** — dois sistemas de autenticação paralelos; se o Python assume que o auth é feito pelo WorkOS, tokens Rails não funcionam no Python e vice-versa.

**P1 — Funcionalidade Quebrada:**
3. **`/api/backend-proxy/insurance/[...path]`** — proxy no frontend sem rota correspondente no Python. Retorna 404.
4. **`/api/backend-proxy/pipeline-pulse`** — sem correspondência clara em routes.py.
5. **`/api/backend-proxy/enhance-prompt`** e **`/interpret-context`** — não localizados em routes.py.
6. **`/api/backend-proxy/transition/execute`** — path a confirmar vs `stage_transition_automation`.

**P2 — Gaps de Integração:**
7. **RAILS_API_URL não configurado** = RailsAdapter opera em fallback local. A "migração CRUD para Rails" está incompleta se essa variável não está em produção.
8. **Rotas Rails não-REST** (`/v1/users/create`, `/v1/users/edit/:id`, `/v1/users/delete/:id`) são código legado que pode confundir integrações.

**P3 — Observabilidade:**
9. **Webhooks Mailgun e Merge.dev** sem validação de assinatura confirmada — vulneráveis a replay attacks.
10. **478 proxy routes mas apenas ~65 rotas Rails** — grande parte das funcionalidades listadas como "Rails" na documentação estão realmente no Python.

---

## APÊNDICE — Estrutura de Diretórios

### Rails Controllers
```
ats-api-copia/app/controllers/
├── application_controller.rb
├── concerns/
└── v1/
    ├── sessions_controller.rb
    ├── auth/
    │   └── magic_links_controller.rb
    └── users/
        ├── application_controller.rb
        ├── applies_controller.rb
        ├── candidates_controller.rb
        ├── client_accounts_controller.rb
        ├── client_users_controller.rb
        ├── company_profiles_controller.rb
        ├── departments_controller.rb
        ├── email_templates_controller.rb
        ├── interviews_controller.rb
        ├── jobs_controller.rb
        ├── messages_controller.rb
        ├── notifications_controller.rb
        ├── onboarding_controller.rb
        ├── recruitment_campaigns_controller.rb
        ├── selective_processes_controller.rb
        ├── talent_pools_controller.rb
        └── users_controller.rb
```

### Python API Modules (seleção)
```
lia-agent-system/app/api/
├── routes.py           ← registro de todos os ~200 módulos
├── orchestrator_routes.py
├── wsi_endpoints.py
├── public/
│   ├── candidate_portal.py
│   └── shared_searches.py
└── v1/
    ├── [~180 arquivos de módulo]
    ├── job_vacancies/  ← submodule com crud.py, lifecycle.py
    ├── clients/
    └── recruitment_stages/
```

### Frontend Proxy Routes (478 arquivos)
```
plataforma-lia/src/app/api/
├── backend-proxy/     ← 478 route.ts → proxy para Python :8001
│   ├── candidates/
│   ├── job-vacancies/
│   ├── pipeline*/
│   ├── wsi*/
│   ├── compliance*/
│   ├── admin*/
│   └── [+ 50 outros domínios]
├── lia/
│   ├── [...path]/route.ts   ← catch-all para /api/v1/*
│   └── chat/stream/route.ts ← streaming SSE
└── [auth/workos routes]
```

---

*Relatório gerado pelo protocolo PX02 em 2026-04-14. Baseado em análise estática do código-fonte. Confirmar gaps P1 com smoke tests antes de categorizar como bugs definitivos.*
