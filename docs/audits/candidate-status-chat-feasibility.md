# Auditoria técnica — chat candidato pós-aplicação (LIA)

> Documento de viabilidade técnica. **Não decide produto, não escreve código.**
> Base de evidência para o plano de construção subsequente.
>
> Escopo da feature alvo (apenas para contexto):
> Candidato cadastrado pela LIA recebe um canal contínuo (WhatsApp e/ou link web)
> para perguntar sobre o status dele em uma vaga. Escopo extremamente limitado:
> status atual, última movimentação, próximos passos, feedback estruturado de
> rejeição, informações parametrizáveis pelo tenant. Isolamento total das outras
> capacidades da LIA.

---

## TL;DR — Recomendação

**Viável, com refatoração bem delimitada antes do MVP.** A maior parte da
infraestrutura existe (modelo de candidato com `company_id`, `CandidateStageHistory`,
`AuditService`, `FairnessGuard`, dois webhooks WhatsApp em produção, padrão de
token assinado em `gemini_voice.py`, portal LGPD com OTP). O que **não existe e
precisa nascer**:

1. Identidade "candidato falando da própria aplicação" (token + OTP curto, análogo
   ao que o portal LGPD já faz, mas reutilizável).
2. Domínio isolado `candidate_self_service` no orquestrador, com whitelist
   explícita de tools (3-5 tools no máximo).
3. Rate limit por `candidate_id` (hoje só existe por tenant/usuário).
4. Guard de **faithfulness** outbound (FairnessGuard cobre viés, mas não cobre
   fabricação de justificativa de rejeição).
5. Consent purpose `ongoing_communication` no `ConsentCheckerService`
   (hoje só `ai_screening` família).

Caminho de menor risco: **agente isolado novo**, ingestão pelo webhook
WhatsApp existente (`app/api/v1/whatsapp.py`) com um novo branch de roteamento
que detecta "candidato com aplicação ativa fazendo pergunta de status" antes
do `ConversationManager` da Phase 1/2 de inscrição assumir.

---

## 1. Mapa do canal WhatsApp

### 1.1 Webhooks existentes
Há **dois roteadores WhatsApp** registrados em produção, com finalidades distintas:

| Finalidade | Arquivo | Endpoints | Orquestrador |
|---|---|---|---|
| Mensagens de candidato (inscrição/triagem) | `lia-agent-system/app/api/v1/whatsapp.py` | `GET /api/v1/whatsapp/webhook` (L113, verificação Meta), `POST /api/v1/whatsapp/webhook` (L155, Meta), `POST /api/v1/whatsapp/twilio-webhook` (L260, Twilio) | `ConversationManager` (`app/domains/recruiter_assistant/services/conversation_manager.py`) |
| Onboarding de **recrutador** via WhatsApp | `lia-agent-system/app/api/v1/whatsapp_webhook.py` | `POST /api/v1/whatsapp/webhook` (L119, Twilio), `POST /api/v1/whatsapp/flow-webhook` (L199), `POST /api/v1/whatsapp/status-callback` (L260) | `services/onboarding_orchestrator.py` |

> **Atenção para colisão de paths**: ambos declaram `POST /api/v1/whatsapp/webhook`.
> A ordem de `include_router` em `main.py` decide quem responde. Isso é um risco
> latente independente desta feature (vale alertar no follow-up), mas não bloqueia.

### 1.2 Identificação do remetente
- **Meta:** `phone_number_id` → `company_id` via `PhoneNumberMapping` ou `WhatsappRepository` (`whatsapp.py:33-68`).
- **Twilio:** número "To" (número da LIA) → `company_id` via `_get_company_from_twilio_number` (`whatsapp.py:347`).
- **Sessão de candidato:** tabela `whatsapp_conversations` (model `WhatsAppConversation`), lookup por `(phone_number, company_id)` em `ConversationManager.get_or_create_conversation` (`conversation_manager.py:254`). Pode expirar (`EXPIRED`, L276) e ressurgir como nova inscrição.
- **Sessão de onboarding:** join `onboarding_agent_state` × `whatsapp_sessions` por `phone_number` (`whatsapp_webhook.py:57-91`).

### 1.3 Roteamento ao orquestrador
**Hoje, nenhum dos dois webhooks chega ao `MainOrchestrator`.** Eles são
máquinas de estado dedicadas. Um candidato falando "qual o status da minha
vaga?" é interpretado dentro do `ConversationManager` como mensagem da fase
atual de inscrição/triagem, não como query de status.

### 1.4 Templates, botões, Flows (Twilio + Meta)
- Templates aprovados existentes (referenciados em `test_whatsapp_native_buttons.py:68-79`): `triagem`, `entrevista`, `feedback`. **Não há template "status update".**
- `WhatsAppClient` (`app/services/whatsapp_client.py`) tem `send_template`, `send_message`, `send_buttons`, `send_cta`, `trigger_flow`. **Pronto** para conversa contínua dentro da janela de 24h; fora dela exige template aprovado pela Meta (gap regulatório, não técnico).
- Único Flow definido: `app/services/whatsapp_flows/onboarding_flow_v1.json` (4 telas: hiring_focus, volume, pain, **consent LGPD obrigatório**). Bom padrão para reusar em consentimento de comunicação contínua.
- Verificação de assinatura Twilio existe e é fail-closed em prod/staging (`whatsapp_webhook.py:23-54`, LIA-SEC-03).

### 1.5 Gaps para "candidato pergunta status"
1. Detecção de intent "status" antes do `ConversationManager` capturar a mensagem dentro da máquina de estado de inscrição.
2. Reabertura de conversa após `EXPIRED` (24h Meta) — exige template aprovado tipo `lia_status_disponivel`.
3. Nenhum template "status update" / "feedback de rejeição" estruturado pré-aprovado.
4. Nenhum mapeamento `phone → candidate_id` (o que existe é `phone → conversa ativa de inscrição`). Para múltiplas vagas no mesmo tenant, o mesmo telefone tem N `VacancyCandidate` — precisa de desambiguação por vaga.

---

## 2. Identidade e autenticação do candidato

### 2.1 O que já existe
- **Modelo `Candidate`** (`libs/models/lia_models/candidate.py:95`): vinculado a `company_id` (L128, **mandatório**), com `email`/`cpf` criptografados (Fernet), `phone`, `mobile_phone`, `secondary_phone`. **Mesmo telefone pode existir em múltiplos tenants** — cada `Candidate` é único por `(company_id, ...)`.
- **`VacancyCandidate`** (mesmo arquivo, L409): chave `(vacancy_id, candidate_id)` dentro de `company_id`.
- **Portal LGPD com OTP** (`plataforma-lia/src/app/[locale]/portal/data-request/[token]` + `lia-agent-system/app/api/public/candidate_portal.py:45,408`): padrão "token na URL + OTP 6 dígitos via email/WhatsApp" já implementado e em produção. **É o padrão a reutilizar.**
- **WS token HMAC** (`app/api/v1/gemini_voice.py:62-73`): `hmac_sha256(SECRET, "session_id:company_id:candidate_id")`. Padrão a reutilizar para tokens curtos de sessão.
- **Magic links** (`plataforma-lia/src/app/api/auth/magic-link/route.ts`): mas hoje proxia para Rails e emite `auth_token` cookie de **recrutador**, não candidato.

### 2.2 Auth middleware
`lia-agent-system/app/middleware/auth_enforcement.py:138`:
- Bearer JWT obrigatório, exceto **public paths** (`L41`): `/api/v1/data-request`, `/api/public/`, `/ws/`.
- Sem token → 401. Mismatch de `X-Company-ID` × JWT → 403.
- Webhooks WhatsApp protegidos por assinatura Twilio/Meta, não por JWT.

### 2.3 Opções viáveis para autenticar "candidato falando da própria aplicação"
| Opção | Descrição | Pró | Contra |
|---|---|---|---|
| **A. WhatsApp opt-in + posse do número** | Após aplicação, candidato confirma opt-in via Flow (com consent LGPD); número validado pelo próprio handshake do WhatsApp | UX zero-friction; reutiliza Flow v1 existente | Dependência total da Meta; não resolve canal web |
| **B. Token assinado por candidate_id+vacancy_id** (recomendado) | Backend gera `hmac(SECRET, candidate_id:vacancy_id:expiry)` enviado por email/WhatsApp ao concluir aplicação. URL `/portal/status/{token}` + OTP curto se token >7 dias | Reutiliza padrão `gemini_voice` e portal LGPD; funciona web e WhatsApp; offline-tolerable | Requer rotina de envio do link; OTP adiciona fricção |
| **C. JWT curto pós-OTP** | Após verificar OTP, emite JWT 30min com `sub: candidate_id`, `tenant: company_id`, `scope: ["status_inquiry"]` | Stateless; auditável; integra com middleware existente | Precisa novo claim `actor_type=candidate` e novo path público |
| **D. Reuso do `data_requests` token** | Estender o token do portal LGPD para também responder status | Zero infra nova | Mistura propósitos legais distintos (Art. 18 LGPD vs comms gerais) → **risco** |

**Recomendação:** combinar B (token na URL após apply) + C (JWT 30min após OTP)
+ A (opt-in para WhatsApp). D é tentador mas legalmente confuso.

### 2.4 Risco: ambiguidade de telefone entre tenants
O mesmo telefone pode estar em N tenants. Resolução por phone APENAS é insuficiente
e pode vazar dados entre empresas. **Sempre exigir `vacancy_id` ou `candidate_id` no
token** — nunca resolver puramente por phone no canal candidato.

---

## 3. Modelo de dados de status / timeline

### 3.1 Onde está o status "agora"
- `VacancyCandidate.status` (sourced/approved/rejected/...) e `VacancyCandidate.stage`, com `previous_status`, `stage_entered_at` (L439), `added_by`, `rejected_by_human` (L436), `human_reviewer_id` (L437).
- `Candidate.is_active`, `is_hired`, `is_blacklisted`, `last_activity_at`, `last_contacted_at`.

### 3.2 Onde está a história "o que aconteceu"
- **`CandidateStageHistory`** (`libs/models/lia_models/recruitment_stages.py:309`): `from_stage_id/name`, `to_stage_id/name`, `transition_type`, `triggered_by`, `triggered_by_user_id`, `created_at`, `source_agent`, `reason`, `notes`. Tem repositório dedicado (`app/domains/recruitment/repositories/stage_history_repository.py`, método `list_for_candidate`). **Esta tabela já responde "última coisa que aconteceu".**
- **`AuditLog`** via `AuditService.get_candidate_decisions(candidate_id, vacancy_id)` (`audit_service.py:154`): traz decisões de IA com `reasoning`, `criteria_used`, `score`, `confidence`. Retenção 5 anos (`RETENTION_PERIODS`, L56-61).

### 3.3 Feedback estruturado de rejeição
- **`CandidateFeedback`** (`libs/models/lia_models/candidate_feedback.py:17`): `adherence_score`, `improvement_tips`, `missing_skills`, `matched_skills`, `feedback_type` enum com `REJECTION` (L124).
- **`RecruiterDecisionFeedback`**: rastro de decisões humanas (override etc).
- **DISC vs Big Five:** o sistema **não usa DISC**, usa **Big Five** (`BigFiveProfile` em `ClientAccount.settings["big_five_profiles"]`, `app/api/v1/big_five.py:129`) e `Archetype` (`libs/models/lia_models/archetype.py`). Comunicação de feedback ao candidato precisa traduzir de Big Five/Archetype para linguagem que ele entenda — **não chamar de DISC**, evitar score numérico (regra da skill `lia-compliance`, ver §6).

### 3.4 Construção do payload "status + última movimentação + próximos passos + feedback"
| Campo | Fonte | Status |
|---|---|---|
| Status atual | `VacancyCandidate.status/stage` | **OK** |
| Última movimentação + autor + timestamp | `CandidateStageHistory.list_for_candidate(...)` ordenada DESC | **OK** |
| Última decisão de IA (com reasoning) | `AuditService.get_candidate_decisions(...)` | **OK** |
| Próximos passos | `RecruitmentStage.allowed_transitions` / `auto_advance_rules` | **GAP**: não há campo `next_steps` parametrizável por tenant; precisa ser inferido ou novo campo |
| Feedback estruturado de rejeição | `CandidateFeedback` (latest, type=REJECTION) | **OK** (mas pode ser ausente se rejeição manual sem feedback gerado) |
| Mensagens parametrizáveis pelo tenant | — | **GAP**: nenhuma tabela de mensagens-template por estágio configuráveis pelo tenant para o candidato |

### 3.5 Gaps de dados
1. **Próximos passos parametrizáveis**: criar `RecruitmentStage.candidate_facing_next_step_template` (texto curto i18n) ou tabela `tenant_candidate_messages(stage_id, message_pt, message_en)`.
2. **Feedback estruturado garantido**: hoje rejeição manual pode ocorrer sem `CandidateFeedback`. Precisa hook que crie um placeholder ou política "se não há feedback, LIA responde apenas status, não inventa motivo".
3. **Timeline unificada**: `CandidateStageHistory` (movimentações) e `AuditLog` (decisões de IA) são fontes paralelas. Para o candidato, é melhor uma view única (`vw_candidate_timeline`) ou um serviço que faça merge — evita o agente ter de cruzar duas fontes.

---

## 4. Arquitetura de agentes — onde encaixa o `candidate_self_service`

### 4.1 Estado atual
- `MainOrchestrator.process` (`app/orchestrator/main_orchestrator.py:187`) é o entry point único, com fases:
  - **Phase 0** PendingAction (L324)
  - **Phase 1** ActionExecutor (L340)
  - **Phase 1.5** AgenticLoop / function-calling (L355) — feature flag `LIA_AGENTIC_LOOP`
  - **Phase 2** Orchestrator → `CascadedRouter` → DomainWorkflow → ReAct
- `CascadedRouter` (`cascaded_router.py`): 8 tiers (memory, redis, vector, fast, LLM cascade, autonomous ReAct, studio, clarification).
- Domínios são auto-registrados via `@register_domain` em `app/domains/registry.py:25-63`, herdando de `ComplianceDomainPrompt` (`app/domains/compliance_base.py`).
- Mapeamento intent→domain em `app/orchestrator/domain_mappings.py:8-43` (`AGENT_TYPE_TO_DOMAIN`).
- Suporte a "skip generic phases" via `_DOMAIN_SPECIFIC_CONTEXTS = {"company_settings", "settings_config", "hiring_policy"}` (`main_orchestrator.py:338`) — **padrão ideal para isolar o domínio candidato**.

### 4.2 Duas opções
| Opção | Pró | Contra |
|---|---|---|
| **A. Domínio isolado `candidate_self_service`** (recomendada) | Whitelist de tools natural; system prompt dedicado; adiciona-se a `_DOMAIN_SPECIFIC_CONTEXTS` para pular fases genéricas; auditoria fica clara | Requer registrar domínio + mapping + tool registry filtrado |
| **B. Modo restrito do orquestrador atual** (`context_type="candidate_chat"`) | Reuso máximo | **Alto risco de vazamento de tools** (qualquer tool sem `allowed_agents` setado fica visível); contamina pipeline com lógica condicional por persona; difícil auditar |

### 4.3 Plano de encaixe (apenas para informar o plano)
1. Criar `app/domains/candidate_self_service/` com `domain.py` herdando `ComplianceDomainPrompt`, `domain_id="candidate_self_service"`, `actor_type="candidate"` (novo atributo).
2. Adicionar a `_DOMAIN_SPECIFIC_CONTEXTS` em `main_orchestrator.py:338` o `context_type="candidate_chat"`.
3. Inserir um pre-router antes da Phase 1.5 que, quando `ctx.actor_type == "candidate"`, **força** `domain_id="candidate_self_service"` e ignora os outros tiers do `CascadedRouter`.
4. Definir `allowed_agents=["candidate_self_service"]` nos handlers das 3-5 tools desejadas (ver §5).

---

## 5. Whitelist de tools

### 5.1 Estado atual
- `app/tools/registry.py`: cerca de 120+ tools registradas via `register_tool`. `get_tools_for_agent(agent_type)` (L89-103) já implementa visibilidade: se `tool.allowed_agents` está populado, só esses agentes veem.
- **Problema**: a maioria das tools **não declara `allowed_agents`**, então elas ficam visíveis a qualquer agente que pedir o catálogo. Em modo restrito (Opção B do §4) isso é fatal.
- `agentic_loop.py:98-115` checa `company_id` no contexto e emite warning se ausente — mas não bloqueia. **Tarefas #329 e #330** (já no backlog) endereçam isto:
  - **#329** — automated check que previne tools novas de pular tenant isolation;
  - **#330** — testar que tools recusam chamadas sem `company_id`.

### 5.2 Tools mínimas necessárias para o candidato (proposta para o plano)
| Tool | Output |
|---|---|
| `get_candidate_application_status(candidate_id, vacancy_id)` | status, stage, stage_entered_at |
| `get_last_pipeline_event(candidate_id, vacancy_id)` | última transição (data, stage origem→destino, autor genérico) |
| `get_next_steps(vacancy_id, current_stage)` | template parametrizado pelo tenant |
| `get_candidate_rejection_feedback(candidate_id, vacancy_id)` | só retorna se `feedback_type=REJECTION` existir; senão null |
| `get_tenant_candidate_message(company_id, message_key)` | textos custom (boas-vindas, despedida, FAQ) |

Todas devem declarar `allowed_agents=["candidate_self_service"]` **e** validar
que `candidate_id` recebido bate com o `candidate_id` do `ToolExecutionContext`
(zero-trust mesmo dentro do agente).

### 5.3 Apoio nas tarefas #329/#330
Esta feature **antecipa a urgência** de #329/#330 — sem elas, o domínio
candidato é seguro só por convenção, não por enforcement. Recomendação:
**#329 e #330 viram pré-requisitos hard do MVP**.

---

## 6. Guardrails, FairnessGuard e tom de resposta

### 6.1 FairnessGuard (`app/shared/compliance/fairness_guard.py`)
- 3 camadas: regex hard-block (L134-386, 10+ categorias: gênero, raça, idade, religião, orientação, deficiência, maternidade, etc), lexicon implícito (L30-67, "boa aparência", "faculdade de ponta"), LLM semantic (Layer 3).
- **Já é aplicado a outputs de "Parecer candidato" e "Feedback rejeição" (L170-171)** — bom precedente. Falta confirmar que será chamado também no path candidato e **antes do envio**, não só no log.
- Bloqueia entrada e saída separadamente; em `MainOrchestrator` o pre-check só roda no input (L232-264). Para output candidato precisa ser explicitamente invocado pós-LLM.

### 6.2 Skill `lia-compliance` — obrigações relevantes
- **Crença #03 / Inegociável #1**: candidato não pode ser ranqueado sem WSI explicável; feedback ao candidato deve ser "warm", focar em pontos fortes e **nunca revelar score numérico** (linhas ~142-144 da SKILL.md).
- **Inegociável #2**: rejeição automática exige human review gate.
- **Inegociável #5**: consent antes de qualquer processamento.
- **EU AI Act**: recrutamento é "High Risk" Art. 6; `ConfidencePolicyService` define níveis (APPLY_SILENT ≥0.85, APPLY_NOTIFY 0.70-0.84, ASK_USER <0.70).

### 6.3 Riscos específicos do canal candidato
| Risco | Mitigação proposta |
|---|---|
| Fabricação de motivo de rejeição (alucinação) | **Faithfulness guard novo** — se a tool `get_candidate_rejection_feedback` retorna null, LIA é proibida de gerar motivo; resposta é "ainda não há feedback estruturado disponível". Não é coberto pelo FairnessGuard atual. |
| Viés em explicação ("você não foi aprovado porque é jovem demais") | FairnessGuard já cobre — apenas garantir invocação outbound |
| Vazamento de critérios internos da empresa | System prompt explícito + whitelist de tools (§5) — sem `get_job_score_breakdown`, sem `get_recruiter_notes` |
| Vazamento de outros candidatos | Validação `candidate_id` em todas as tools + JWT scope (§2) |
| Tom inadequado (frio, jurídico, defensivo) | Persona prompt warm + i18n PT/EN; testar via golden dataset (skill `lia-testing`) |

### 6.4 HITL outbound
`HITLService` (`app/domains/cv_screening/services/hitl_service.py`) tem gates para
`create_job`, `PipelineTransition`, finalização WSI — **nada para outbound chat**.
Para candidato: avaliar se mensagens contendo decisão de rejeição devem passar
por gate humano (caso a caso por tenant) — bandeira de configuração por
`ClientAccount.settings`.

---

## 7. LGPD, consentimento e direito de explicação

### 7.1 Consent hoje
`ConsentCheckerService` (`app/domains/lgpd/services/consent_checker_service.py`):
- `PURPOSE_TO_CONSENT_TYPE` (L47-52): apenas `ai_screening`, `ai_scoring`, `ai_video_analysis`, `ai_comparison` — todos mapeiam para categoria `SCREENING`.
- Modelo `LGPDConsent` (em `lia_models`): campos `candidate_id`, `company_id`, `consent_type`, `consent_given`, `consent_date`, `revoked_at` (L77-85, 239-252).
- `WSIInterviewGraph.load_context` (cv_screening agent, L337-372) já gateia processamento por consent.

### 7.2 Gaps
1. **Falta purpose `ongoing_communication` / `whatsapp_chat`**. Comunicação contínua via WhatsApp exige base legal própria (consentimento ou execução contratual, dependendo do tenant) — distinta de "screening".
2. **Direito de explicação (LGPD Art. 20 + EU AI Act Art. 14/86)**: o candidato pode pedir explicação de decisão automatizada. Hoje o canal é o portal LGPD (`data-request`); a feature do chat **passa a ser um canal alternativo de exercício deste direito**, o que aumenta a obrigação de qualidade de resposta e auditoria.
3. **Onboarding Flow LGPD existente** (`onboarding_flow_v1.json` SCREEN_CONSENT) é para recrutador — precisa Flow análogo para candidato com texto específico de "comunicação contínua via LIA".
4. **Revogação**: o canal deve aceitar comando explícito ("parar"/"cancelar"/"revogar") e propagar para `LGPDConsent.revoked_at`. Twilio/Meta também têm STOP/SAIR nativos — interceptar.

### 7.3 Retenção
`AuditService.RETENTION_PERIODS` (audit_service.py:56-61): `send_message` e `conversational_output` retidos **5 anos (1825 dias)**. Suficiente; só validar que conversas com candidato seguem mesmo padrão.

---

## 8. Custo, rate limiting e abuso

### 8.1 Estado atual
- `quota_enforcement.py` (`app/services/`): `PLAN_AGENT_QUOTAS` (L18-43) por plano (Starter/Pro/Business/Enterprise) com `custom_agents`, `sourcing_agents`, `digital_twins`, `campaigns`. **Granularidade: tenant.**
- Skill `lia-compliance` cita HTTP rate limits 600/min/user, 3000/min/company; LLM 60 calls/min — implementação não localizada com profundidade nesta auditoria, mas reside em middleware FastAPI.
- `agent_quota.py` (`libs/models/lia_models/`) é só schema de quotas por tenant.
- **Nenhum limite por `candidate_id` ou por `phone_number`**.

### 8.2 Modelo proposto (input para o plano)
| Dimensão | Limite sugerido (MVP) |
|---|---|
| Mensagens por candidato por hora | 10 |
| Mensagens por candidato por dia | 30 |
| Mensagens por phone por hora (anti-spam de telefone reciclado) | 20 |
| LLM tokens por candidate por dia | 5k |
| Custo por tenant por candidato por mês (cap) | configurável; default 0.50 USD |

Implementação: nova tabela `candidate_chat_quota(candidate_id, company_id,
window_start, message_count, token_count)` ou Redis com TTL. Hook no
`MainOrchestrator` antes da Phase 1.5 quando `ctx.actor_type=="candidate"`.

### 8.3 Loop / spam protection
- Detectar mensagens repetidas idênticas (>3 em 5min) → resposta canned + cooldown.
- Detectar pergunta fora de escopo (não relacionada à própria aplicação) → resposta canned + log.
- Twilio MessageStatus já chega em `whatsapp_webhook.py:260` (`status-callback`); usar para detectar `failed` em loop e suspender.

---

## 9. Observabilidade e auditoria

### 9.1 Estado atual
- **`AuditLog`** (`libs/models/lia_models/audit_log.py:27`) campos: `decision_type`, `reasoning` (JSON), `criteria_used`, `criteria_ignored`, `score`, `confidence`, `actor_user_id`. Retenção 5 anos.
- **`AuditService.log_output`** (`audit_service.py:300`) loga **toda resposta da LIA**: `input_text` (4k), `output_text` (8k), `fairness_flags`, `agent_used`, `action_executed`. Já invocado nos webhooks WhatsApp existentes (ex.: `whatsapp_webhook.py:178-194`).
- **Tracing** (`app/shared/observability/tracing.py`): spans `router.route`, `rag.search`, `hitl.request_approval`, `ws.agent_chat` com `trace_id`, `service.name`, `status`. `CascadedRouter` emite spans por tier (`tier1_lru_cache`...`tier6_autonomous_react`).

### 9.2 O que precisa para o canal candidato
| Necessidade | Status atual | Gap |
|---|---|---|
| Logar entrada do candidato | `log_output` aceita `input_text` | OK, só passar `actor_type=candidate` |
| Logar resposta da LIA com fairness flags | `log_output` faz | OK |
| Logar tools chamadas e dados acessados | AuditLog tem `criteria_used` (JSON) | **Gap parcial**: precisa convenção de gravar `tool_calls=[...]` no `reasoning` |
| Logar `candidate_id`/`vacancy_id` por mensagem | Schema já tem `candidate_id`, `job_vacancy_id` (L189-190 do webhook) | OK |
| Trace span dedicado para o agente candidato | `ws.agent_chat` é genérico | Adicionar `candidate_chat` span com atributo `actor_type` |
| Detecção de PII nos logs | `pii_masking.mask_pii` existe (`app/shared/pii_masking.py`, usado em `gemini_voice.py:212`) | Aplicar consistentemente em `output_text` antes de logar |

---

## 10. Síntese final

### 10.1 Gaps priorizados
**Must-have para MVP:**
1. Identidade candidato: token assinado por aplicação + JWT curto pós-OTP (§2).
2. Domínio isolado `candidate_self_service` + adição a `_DOMAIN_SPECIFIC_CONTEXTS` (§4).
3. Whitelist real de tools (#329 + #330 como **dependências hard**) (§5).
4. Faithfulness guard outbound (não fabricar motivo de rejeição) (§6).
5. Consent purpose `ongoing_communication` no `ConsentCheckerService` + Flow LGPD candidato (§7).
6. Rate limit por `candidate_id` + por `phone_number` (§8).
7. Tabela / mecanismo de "next steps parametrizáveis por estágio + tenant" (§3.4).
8. Pre-router no webhook WhatsApp para detectar candidato com aplicação ativa fazendo pergunta de status, antes do `ConversationManager` consumir (§1.5).
9. Templates Meta/Twilio aprovados: `lia_status_disponivel`, `lia_feedback_estruturado` (§1.4) — **risco de prazo**, aprovação Meta leva dias/semanas.
10. AuditLog `actor_type=candidate` + `tool_calls` em `reasoning` (§9).

**Nice-to-have (pós-MVP):**
- HITL outbound configurável por tenant (§6.4).
- Canal web `/portal/status/{token}` paralelo ao WhatsApp.
- Translation i18n EN/ES.
- Voice (reusar `gemini_voice` para candidato falar com LIA).

### 10.2 Riscos arquiteturais
- **Colisão de paths WhatsApp** (§1.1) — independente, mas vale resolver antes.
- **Tools sem `allowed_agents` (gap #329)** — risco real de vazamento se a feature for shipped antes de #329/#330.
- **Aprovação de templates pela Meta** — fora do controle do time; planejar 2-4 semanas de buffer.
- **Mesmo telefone, múltiplos tenants** — qualquer resolução por phone APENAS é vulnerável (§2.4).
- **Conversas "EXPIRED" da Meta (24h)** — exige template aprovado; sem isso, LIA não consegue iniciar conversa fora da janela.
- **HITLService sem gate outbound de chat** (§6.4) — para tenants regulados (BCB, financeiro, saúde) pode ser bloqueador.

### 10.3 Decisões em aberto (precisam input de produto)
1. Escopo de "próximos passos": livre-texto por tenant, enum fechado, ou geração por LLM com template?
2. Política quando não há `CandidateFeedback`: silenciar? Cair em template genérico? Acionar HITL?
3. Persona da LIA-candidato: mesmo nome ou sub-persona ("LIA-Suporte")? Idioma default?
4. Cap de custo por candidato — quem paga (tenant) e qual o cap default?
5. Canal default: WhatsApp-first, web-first, ou ambos paralelos no MVP?
6. Tenants opt-in vs opt-out na ativação da feature?
7. Política de revogação: comando livre ("não quero mais"), só STOP, ou exige link no portal?

### 10.4 Recomendação final
**Caminho de menor risco para o MVP:**

1. **Antes de codar a feature**, fechar (não esta task) #329 e #330 — sem isso, isolamento de tools é só convenção.
2. **MVP em 3 fases:**
   - **Fase 1 — só leitura, só WhatsApp, sem LLM.** Templates aprovados de status estruturado disparados por gatilho ("/status" ou botão pós-aplicação) — responde via tool determinística sem LLM. Sem alucinação possível.
   - **Fase 2 — LLM dentro do domínio isolado.** Adiciona `candidate_self_service` agent com whitelist de 5 tools, faithfulness guard, rate limit. Mantém WhatsApp.
   - **Fase 3 — canal web + voz** reaproveitando `gemini_voice`.
3. **Reuso máximo** de:
   - Padrão token+OTP do portal LGPD;
   - HMAC do `gemini_voice` para JWT curto;
   - `CandidateStageHistory` + `AuditService` como fontes de verdade para timeline;
   - `WhatsAppClient` e webhook `/api/v1/whatsapp/webhook`;
   - `_DOMAIN_SPECIFIC_CONTEXTS` para isolar pipeline.
4. **Não criar nada novo** que duplique o que já existe (ex.: não inventar nova tabela de timeline — usar `CandidateStageHistory`; não inventar novo middleware de auth — estender o public path existente).

A feature é **viável**, o desenho é **conhecido**, e o risco principal é
**operacional** (aprovação Meta de templates, política de produto sobre
silêncio em rejeições, dependência das tarefas #329/#330) — não técnico.

---

## Anexo — referências de arquivos

- `lia-agent-system/app/api/v1/whatsapp.py` (webhook Meta+Twilio, candidato)
- `lia-agent-system/app/api/v1/whatsapp_webhook.py` (webhook Twilio, onboarding)
- `lia-agent-system/app/services/whatsapp_client.py`
- `lia-agent-system/app/services/whatsapp_flows/onboarding_flow_v1.json`
- `lia-agent-system/app/domains/recruiter_assistant/services/conversation_manager.py`
- `lia-agent-system/app/services/onboarding_orchestrator.py`
- `lia-agent-system/app/orchestrator/main_orchestrator.py`
- `lia-agent-system/app/orchestrator/cascaded_router.py`
- `lia-agent-system/app/orchestrator/agentic_loop.py`
- `lia-agent-system/app/orchestrator/domain_mappings.py`
- `lia-agent-system/app/orchestrator/precondition_checker.py`
- `lia-agent-system/app/domains/registry.py`
- `lia-agent-system/app/domains/compliance_base.py`
- `lia-agent-system/app/tools/registry.py`
- `lia-agent-system/app/middleware/auth_enforcement.py`
- `lia-agent-system/app/api/public/candidate_portal.py`
- `lia-agent-system/app/api/v1/gemini_voice.py`
- `lia-agent-system/app/shared/compliance/fairness_guard.py`
- `lia-agent-system/app/shared/compliance/audit_service.py`
- `lia-agent-system/app/shared/observability/tracing.py`
- `lia-agent-system/app/shared/pii_masking.py`
- `lia-agent-system/app/services/quota_enforcement.py`
- `lia-agent-system/app/domains/lgpd/services/consent_checker_service.py`
- `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`
- `lia-agent-system/app/domains/cv_screening/services/hitl_service.py`
- `lia-agent-system/app/domains/recruitment/repositories/stage_history_repository.py`
- `lia-agent-system/libs/models/lia_models/candidate.py`
- `lia-agent-system/libs/models/lia_models/recruitment_stages.py`
- `lia-agent-system/libs/models/lia_models/candidate_feedback.py`
- `lia-agent-system/libs/models/lia_models/audit_log.py`
- `lia-agent-system/libs/models/lia_models/agent_quota.py`
- `lia-agent-system/libs/models/lia_models/archetype.py`
- `plataforma-lia/src/app/[locale]/portal/data-request/`
- `plataforma-lia/src/app/api/auth/magic-link/route.ts`
- `.agents/skills/lia-compliance/SKILL.md`

Tarefas relacionadas no backlog (já existentes, não duplicar):
- #329 — automated check que previne tools novas de pular tenant isolation
- #330 — testar que tools recusam chamadas sem `company_id`
