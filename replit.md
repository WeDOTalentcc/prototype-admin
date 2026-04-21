# Recent Changes

- **Task #714 — FLUXO Alpha1 ganha CT-ML (11 camadas) + CT-CHANGELOG Q1–Q2/2026**: `plataforma-lia/docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md` (2500→2689 linhas) recebeu duas seções transversais novas, inseridas entre `CT — Chat Unified` e a `TABELA CONSOLIDADA`. **CT-ML** consolida a auditoria honesta das 11 camadas de inteligência (Learning Loop ●, A/B Testing ●, Semantic Search ●, Embedding Service ●, RAG ◑, Calibration ●, Predictive Analytics ●, Score Normalization ●, Conversation Memory ●, Template Learning ●, Routing Adaptativo ● + Voice Analysis ◑ e Long-Term Memory ● como complementares), com localização canônica do código (corrigindo 3 caminhos errados na Task brief — `predictive_analytics`, `conversation_memory`, `score_normalization` ficam em `app/domains/`, não em `app/shared/services/`), endpoints expostos, etapas ativas, marcação explícita dos 6 shims retro-compat em `app/shared/services/*` (⌬), diagrama ASCII do **ciclo virtuoso** (turno → observação pós-ação → monitoramento Model Drift 24/7) e tabela de gaps/dívidas técnicas (RAG insight parcial em E15, Voice generalização gated, shims pendentes de ADR-018, score_normalization sem API/dashboard, routing adaptativo sem métrica de qualidade exposta). **CT-CHANGELOG** categoriza as melhorias entregues mar/abr 2026 em 7 grupos: A) Production Readiness (refactor < 1000 L em 39→5 arquivos, 38→50+ test files, Vue-readiness 55→59/70), B) Tenant Isolation (Task #673 + #306 IDOR + #334 WSI + tool registries fail-closed), C) Routing Canônico (P0/P1 fixes + Task #672 capabilities CI gate + Task #552 echo specialist + Task #623 cleanup tools), D) Compliance (Task #712 PII real, FairnessGuard v5 #84, identity hardening, Bell #82, XSS sanitize), E) ML/IA (eval 62→70/73 + 15 fixes, semantic signals layer, calibration_dashboard_v2, agent quality dashboard, billing E2E #558), F) Integrações (Teams #706, WhatsApp/Teams reminders #626/#625, Candidate Portal Rails, voice pipeline, JWT blacklist), G) Doc/Glossário (FLUXO v2.0 + E0 + E0.5 + E10–E16 + CT, glossário 281 actions/94 tools #692, MAPA 18 domínios, ADR-018/019/020). Inclui timeline ondas mar→abr/2026. Apenas documentação — zero mudança de código.

- **Task #713 — FLUXO Alpha1 ganha E10–E16 + macro-etapa CT (Chat Unified) + tabela consolidada**: `plataforma-lia/docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md` agora cobre o ciclo completo *atrair → triar → decidir → contratar → analisar* com 7 novos capítulos pós-decisão (**E10 Proposta & Negociação** ✗ STUB, **E11 Hire & Pré-Onboarding** ✗ STUB sem conector HRIS, **E12 Arquivamento & Talent Pool** ◐ usa `talent_pool` domain + `silver_medalist_service`, **E13 Pós-decisão Analítico** ◐ Bias Audit/Four-Fifths ● mas NPS/QoH ✗ STUB, **E14 Closing da Vaga** ✗ majoritariamente STUB, **E15 Reporting & Dashboards** ◐ endpoints `reports.py`/`saas_metrics.py`/`wsi/reports.py` ● + BI export ✗ STUB, **E16 Feedback Loop** ◐ `lia_feedback.py`/`golden_drift_monitor`/`fewshot_evolution` ● + NPS processo ✗ STUB), uma macro-etapa transversal **CT — Chat Unified como Entrada MVP** mapeando todos os 26 componentes de `unified-chat/` (UnifiedChat 3 render modes, slash commands, mentions, smart upload, transport SSE→WS→polling, event bus `lia:settings-action`/`lia:settings-success`/`lia:settings-updated`/`lia:onboarding-progress`, integração com OnboardingChatPage, status de cobertura por hub) e uma **TABELA CONSOLIDADA DE STATUS DAS 16 ETAPAS + CT** (14 ●, 4 ◐, 3 ✗) com conclusão técnica explícita de que o gap pós-MVP está em E10/E11/E14 + ML para QoH (E13) + NPS estruturado (E13/E16). STUB explicitamente marcado em cada step sem código real. Apenas documentação — zero mudança de código.

- **Task #712 — Onboarding proativo + Configurações 100% conectadas (7 actions canônicas)**: o domínio `company_settings` agora delega WRITE 100% para as tools já existentes em `app/domains/company_settings/agents/company_tool_registry.py` (`_wrap_save_company_section`, `_wrap_import_workforce_plan`, `_wrap_process_uploaded_document`), em vez de retornar "configuração indisponível". `domain.py` ganhou `_delegate_section_write` + `_SECTION_FIELD_HINTS` que filtram payload por seção (profile/culture) e respondem `clarification_response` quando faltam campos — zero duplicação de lógica de gravação, FairnessGuard L1+L2+L3 + PII Masking + AuditTrail + tier validation aplicados de forma idêntica em chat e UI. `_handle_process_document` ganhou pipeline real: aceita `document_text` ou `document_b64`+`document_format` (pdf via pypdf, docx via python-docx, txt UTF-8) e devolve `requires_human_approval=True` com `expected_fields` para revisão humana antes da gravação (LGPD Art. 8). Frontend: novo hook `use-settings-conversational.ts` (`triggerAction(actionId, opts)`) emitindo `lia:settings-action` (consumido por novo listener em `settings-page-enhanced.tsx` que abre tab + scrolla até `[data-field=...]` + highlight 3s) + `settings-open-tab` (compat reversa); novo componente `SetupProgressBanner` (LIA DS v4.2.1 — `role="status"`, `aria-live="polite"`, dark/light tokens, dismiss 24h em `localStorage`, threshold 80%) montado em `dashboard-app.tsx` para todas as páginas exceto Chat LIA e Configurações; CTA "Analisar nosso site" adicionado ao topo de `MinhaEmpresaHub.tsx` disparando `analyze_website`; `onboarding-controller.handleStartWizard` agora redireciona pra `/onboarding` (renderizando `OnboardingChatPage`) em vez de fechar o modal silenciosamente. Doc canônico ganhou capítulo **E0.5 — ONBOARDING PROATIVO + CONFIGURAÇÕES 100% CONECTADAS** em `FLUXO_TECNICO_COMPLETO_ALPHA1.md` cobrindo: catálogo das 7 actions × tier × tool delegada, pipeline conversacional chat→action→painel, hook `use-settings-conversational`, banner persistente, CTA analyze_website, pipeline `process_document`, 5 inegociáveis anti-regressão (delegar/nunca duplicar; sem fallback silencioso; clarification-first; TIER 1 pós-setup `confirmed=true`; AuditTrail obrigatório). Testes unitários `tests/unit/test_company_settings_actions.py` cobrem clarification (4 actions sem dados), error (6 actions sem `company_id`) e success com mock das tools delegadas (configure_profile → save_company_section, configure_workforce → import_workforce_plan, process_document → process_uploaded_document).

- **Task #711 — FLUXO Alpha1 ganha capítulo E0 (Arquitetura de IA)**: `plataforma-lia/docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md` agora abre com um capítulo E0 que documenta a camada cognitiva como base de todas as etapas E1–E9: 4 grandes camadas (Roteamento → Domínios → Agentes → Tools), CascadedRouter de **8 tiers** (Tier 0 MemoryResolver, Tier 1 LRU, Tier 2 Redis hash, Tier 3 pgvector, Tier 4 FastRouter regex, Tier 5 LLM Cascade Haiku→Sonnet→Opus com A/B, Tier 6 AutonomousReActAgent, Fallback Clarification — corrige a referência antiga de "6 tiers" no doc), tabela de 19 domínios canônicos com status real (incluindo `company_settings` com 5/7 actions stub — alvo da Task #712), tabela de 27 agentes (`@register_agent` + aliases), Tool Registry + `tool_permissions.yaml` por tenant (ADR-015), ContextAggregatorService + Memory subsystem (`ConversationState`, `WorkingMemory`, `reference_resolver`), 6 escudos de compliance (FairnessGuard 3L, PII Masking 4L, FactChecker, BiasAudit Four-Fifths, AuditTrail SOX, Policy Engine) + PromptInjectionGuard + C3B Layer + Scoring Safeguards, Persona LIA + Anti-Sycophancy + Defensive Prompts (com A/B `cascade_router_system_prompt`), camada de observabilidade (OTel tracing, structured logging, agent monitoring, model drift, AI consumption outbox, silent-fallback counter ADR-019), diagrama ASCII end-to-end "1 mensagem do recrutador → resposta" e mapa cruzado componente × etapa E1–E9. Cross-references explícitos para `ARCHITECTURE.md` (ADRs 001–020), `cascaded_router.py`, `domain_routing.yaml`, `domain_mappings.py`, `tool_permissions.yaml` e `RELATORIO_CAPACIDADES_PROMPTS_LIA.md` (vence em conflito). Apenas documentação — zero mudança de código.

- **Task #513 (parcial) — Fix senioridade fallback silencioso + Zod enrichedJd + SQL schemas**:
  - **Fallback silencioso removido** em `wsi_screening_pipeline.py`: quando o resolver multi-sinal está desabilitado E `request.seniority` não é informada, o pipeline ainda usa "pleno" como default mas agora marca `seniority_resolution.requires_confirmation=True`, expõe `warning` no metadata e adiciona o aviso em `quality_warnings` (antes era `logger.info` silencioso). Logging promovido a `WARNING`.
  - **Zod `jobCreateSchema` enriquecido** em `plataforma-lia/src/lib/schemas/job.schema.ts`: adicionado campo `enriched_jd: z.record(z.unknown()).nullable().optional()` (alinhado ao backend `JobVacancyCreate.enriched_jd`); `seniority` ganhou enum canônico (junior/pleno/senior/lead/executive/specialist); `manager_email` valida formato; `salary_min/max` checados como não-negativos e `salary_min ≤ salary_max` via `.refine()`; `currency` exige 3 letras.
  - **SQL schemas de referência atualizados** (`database/wsi_schema.sql` + `wsi_schema_corrected.sql`): todos os CHECKs de score migrados de `BETWEEN 1 AND 5` para `BETWEEN 0 AND 10` (alinhado à migration 090); `bloom_level` corrigido para `BETWEEN 1 AND 6`; `dreyfus_level` para `BETWEEN 1 AND 5`; comentários SQL refletem escala 0-10.
  - **Tests:** 2 novos testes em `test_screening_pipeline_integration.py` — `test_seniority_silent_fallback_emits_warning` (patcha `SENIORITY_RESOLVER_ENABLED=False` e valida warning + `requires_confirmation=True`) e `test_explicit_seniority_does_not_emit_fallback_warning`. Suite total 30 PASSED.
  - **Pendente para futuro PR (deferido):** reescrita dos prompt templates RAG (caminho `app/shared/agents/prompts/wsi/` da spec original não existe — investigar se virou Python strings em outro lugar), suite E2E `tests/e2e/test_wsi_pipeline_e2e.py` com 4 cenários, architect review consolidado de PR1+PR2+PR3+PR4, e fechamento do audit doc rev. 14.

- **Task #510 — Correções metodológicas WSI scorer (M02 Bloom + M07 Dreyfus + M08 Gates)**:
  - **M02 Bloom keyword overlap (FIXED):** `BLOOM_LEVELS[3]` removeu `"projeto"` (substantivo ambíguo); `BLOOM_LEVELS[6]` agora usa expressões compostas (`"do zero"`, `"arquitetei"`, `"fundei"`, `"concebi"`, `"inovei"`, `"criei do zero"`, `"projetei do zero"`). `calculate_bloom_level` reescrito com **regex word-boundary `\b`** — elimina falsos matches de substring (ex: `"uso"` em `"abuso"`).
  - **M07 Dreyfus behavioral vs technical (FIXED):** novo `DREYFUS_LEVELS_BEHAVIORAL` com ranges distintos (Iniciante 0–0.5a, Básico 0.5–1.5a, Intermediário 1.5–3a, Avançado 3–6a, Especialista 6+a) — promove cedo em soft skills. `calculate_dreyfus_level(skill_type="technical"|"behavioral")` parametrizado; `WSIResponseAnalyzer` deriva `question_type` do framework e propaga até o scorer.
  - **M08 Gates absolute precedence (FIXED):** `_compute_decision_confidence` em `reports.py` eliminou `ambiguous_gates = {G2, G5, G6}` que rebaixava confidence/ativava review. Qualquer gate falhado ⇒ `("alta", False)` (rejeição clara). `human_review_required` permanece como flag separada acionada apenas por `llm_fallback_count >= 2` ou `score_variance > 2.0`. Prompt RAG do `report_generator.py` ganhou regra explícita de "PRECEDÊNCIA ABSOLUTA DOS GATES".
  - **Tests:** 3 classes novas em `test_wsi1_scoring_engine.py` — `TestBloomAlignmentRegression` (4/4 PASSED), `TestDreyfusBehavioral` (4/4 PASSED), `TestGatesAbsolutePrecedence` (6 testes; importação validada via boot). Backend HTTP 200 com 1531 endpoints pós-edição. Audit doc atualizado para revisão 12.

- **Task #497 PR2 — Flip atômico escala WSI 0-5 → 0-10 (engine + DB + Pydantic)**:
  - `wsi_scale.py` flipado integralmente: `SCALE_MAX 5→10`, `WSI_CUTOFFS 7.5/6.0`, `GATE_G3 4.0`, `CLASSIFY_*` ×2, indicadores de inflação ×2, todas as constantes Dreyfus/STAR/justificação ×2. Mantidas chaves `AUTODECLARATION_LEVEL_KEYWORDS` em 1.0–5.0 (input do candidato; engine reescala via fator `legacy_to_engine = SCALE_MAX/5.0`).
  - **M04 endereçado** — penalidades alinhadas à spec §8.2: `−1.5/−1.0/−2.5` (não double linear). Bonuses ×2 (`1.0/0.6/2.0`).
  - **Bug fix do scorer** (linha 253): keyword lookup em `extract_autodeclaracao_score` agora aplica `legacy_to_engine` (antes vazava valor /5 cru no engine /10).
  - **Pydantic `le=5 → le=10`** em 5 schemas: `_shared.py`, `wsi_service/models.py`, `personalized_feedback_service.py`, `lia_opinion.py`, `input_validation.py`.
  - **Alembic 090** (`090_widen_wsi_score_scale_to_10.py`) — reversível: `UPDATE wsi_results/wsi_response_analyses *2` + `DROP/ADD CHECK BETWEEN 0 AND 10`. Ordinalidade preservada (transformação linear monotônica). Downgrade `/2` + restaura CHECK 1-5.
  - **17 services satélites auditados** (T4): `evaluation.py` (gates/decision_confidence /10), `reports.py` (severity 1.5/3.0, strengths ≥7.0, gaps <6.0), `report_generator.py` (RAG prompts /10.0, behavioral 1.0–10.0), `personalized_feedback_service.py` (templates /10.0, thresholds 9.0/7.0/5.0/8.0, removido `*2` espurio em score_10/score_comp).
  - **Conversões `*2` órfãs removidas** (T5): `reports.py:755`, `evaluation.py:421`, `personalized_feedback_service.py:521+555`.
  - **Architect review:** APPROVED_WITH_NITS (zero SEVERE/MAJOR). 2 nits aplicados antes do fechamento. Smoke test pós-flip: classify(9.5)=excepcional, classify(7.6)=alto, classify(4.5)=abaixo_da_media; backend HTTP 200 em /api/v1/health (1531 endpoints, 1654 schemas) sem regressão de imports.
  - **Deferido:** PR3 (60 telas frontend `/5 → /10`) e PR4 (templates RAG + E2E + atualização de `database/wsi_schema*.sql`).

- **Task #497 PR1 — Constantes canônicas WSI (refator puro, zero behavior change)**:
  - Novo `lia-agent-system/app/domains/cv_screening/constants/wsi_scale.py` consolida TODAS as magic numbers da escala WSI (cutoffs, gate G3, normalizações STAR/Bloom, thresholds de classificação 6 níveis, penalidades/bônus, indicadores de inflação/contexto).
  - `wsi_deterministic_scorer.py` refatorado para importar do `wsi_scale` — removidas duplicações inline de `WSI_CUTOFFS` e `GATE_G3_THRESHOLD` (que sombreavam o import e quebravam a futura troca de escala).
  - Patterns de `extract_autodeclaracao_score` ("X de 5", "X/5", "nota X", "nível X") agora multiplicam por `SCALE_MAX/5.0` — em escala 0-5 isso é identidade (×1.0); na escala 0-10 do PR2 vira ×2.0 automaticamente sem editar o engine.
  - PR1 isolado: nenhum valor numérico mudou. Smoke test confirma classify(4.6/3.8/2.0) e final WSI idênticos ao pré-refator. Habilita o PR2 (flip atômico engine ×2 + DB migration) editando apenas `wsi_scale.py`.
- **Task #429 — Job Readiness Hub (MVP)**: Pipeline visual de 7 estágios para preparar vagas importadas do ATS antes da triagem.
  - Backend: novas colunas em `job_vacancies` (migration 086), `JobReadinessService` com classificador puro + HITL approval, REST API em `/api/v1/job-readiness/*`.
  - Frontend: cliente `readiness-api.ts`, página Hub em `/[locale]/jobs/readiness` (alias PT `/vagas/prontidao`) com kanban + drawer + ações em lote, banner CTA + botão "Prontidão" na página de Vagas.
  - Tests: 16 unit tests do classifier + integration test de isolamento multi-tenant.

# Overview
Plataforma LIA (Learning Intelligence Assistant) is an AI-powered recruitment and selection system designed to optimize hiring processes. It leverages a multi-agent AI architecture and the WSI (WeDoTalent Skill Index) methodology to provide comprehensive candidate assessment (technical, behavioral, cultural fit). LIA aims to revolutionize recruitment by offering advanced AI capabilities, robust authentication, candidate comparison, specialized testing, KPI dashboards, real-time notifications, and predictive analytics, ensuring an efficient, compliant, and intelligent solution that improves hiring quality and reduces time-to-hire.

# User Preferences
- Idioma: Português
- Design/Layout: Sempre perguntar antes de fazer mudanças em design ou layouts - o usuário quer avaliar propostas antes da implementação
- Separação Backend/Frontend: Manter estruturas de back e front completamente separadas (API REST/GraphQL no backend, SPA no frontend)
- Componentização: Priorizar componentes reutilizáveis e modulares, evitar código monolítico
- Preparação para Migração: Estruturar código pensando em possível conversão para Vue.js + Nuxt (frontend) e Ruby on Rails (backend)
- Border Radius: Seguir DS v4.2.1 — rounded-md (8px) padrão universal para botões/inputs/cards/modais, rounded-xl (16px) para interfaces imersivas (chat, login), rounded-full (pill) para badges/skills/avatars.
- Chat é a interface principal - O recrutador interage com a LIA através de conversa natural, NÃO através de botões
- LIA pergunta, recrutador responde - Quando uma etapa está completa, a LIA PERGUNTA se quer avançar. O recrutador RESPONDE no chat (ex: "sim", "vamos", "pode avançar")
- Painéis são suporte visual - Os painéis laterais mostram informações e permitem edição, mas a navegação e decisões são feitas via chat
- Sem botões como interface principal - Botões são apenas atalhos opcionais, NUNCA a forma principal de interação
- Transições via confirmação textual - O recrutador confirma avanço de etapa escrevendo no chat, não clicando em botões
- A LIA deve entender variações naturais de confirmação em português

# Regras de Desenvolvimento (OBRIGATÓRIAS)

Estas regras valem para toda sessão de trabalho — humana ou IA — antes de qualquer edição. Violar qualquer uma delas é motivo para reverter o trabalho.

1. **Identifique o arquivo canônico antes de editar.** Antes de qualquer fix ou feature, mapeie a fonte da verdade (qual arquivo/rota/hook/serviço é o dono daquela responsabilidade). Se houver mais de um candidato, pare e consolide primeiro.
   - ❌ Não fazer: editar o primeiro arquivo que apareceu no grep e seguir adiante.
   - ✅ Fazer: rodar busca, listar todos os candidatos, escolher o canônico, marcar os demais para deleção.

2. **Corrija na origem, nunca no consumidor.** Se o bug está num serviço/endpoint/hook usado por N telas, conserte lá — não em cada chamada.
   - ❌ Não fazer: adicionar um `if (!data) return []` na tela X para esconder que o endpoint Y devolve `null`.
   - ✅ Fazer: ajustar o endpoint Y para devolver `[]` (ou tipar/validar a resposta no serviço compartilhado).

3. **Proibido workaround.** Sem `try/except` mascarando erro, sem fallback silencioso, sem cópia de lógica para "ganhar tempo", sem flag improvisada para desviar do bug.
   - ❌ Não fazer: `try: real_call() except: return mock_data` para o build não quebrar.
   - ✅ Fazer: deixar o erro explodir explicitamente, logar com contexto e corrigir a causa raiz.

4. **Arquitetura canônica e unificada.** Uma responsabilidade = um arquivo. Um endpoint = uma rota. Um domínio = um hook/serviço. Sem duplicatas, sem "v2" convivendo com "v1" sem plano de remoção.
   - ❌ Não fazer: manter `useCandidates.ts` e `useCandidatesNew.ts` ativos ao mesmo tempo.
   - ✅ Fazer: migrar consumidores para o canônico e deletar o legado na mesma task.

5. **Clean code enterprise.** Nomes claros, funções pequenas (<50 linhas), sem dead code, contratos tipados (Pydantic no backend, types no frontend), separação real de concerns frontend/backend/IA. Sem `any` gratuito, sem `print()`, sem segredo hardcoded.
   - ❌ Não fazer: função de 300 linhas que faz fetch, transforma, valida, persiste e renderiza.
   - ✅ Fazer: dividir em funções nomeadas por intenção, cada uma testável isoladamente.

6. **Antes de marcar concluído.** Rode a auditoria de 14 dimensões (skill `feature-audit`) e, quando o trabalho envolveu correção de código existente, rode também a checagem da skill `canonical-fix`. Se qualquer dimensão ficar ⚠️ ou ❌, conserte antes de fechar a task.
   - ❌ Não fazer: marcar `completed` porque "compilou e a tela abriu".
   - ✅ Fazer: passar pelas 14 dimensões, anexar o resultado, só então fechar.

**Policies canônicas (consultar antes de tocar tools/shims):**
- `docs/policies/require_company_exemptions.md` — catálogo das 19 exceções `@tool_handler(require_company=False)` autorizadas (uma linha por decorador, com justificativa). Qualquer novo decorador sem entrada nesta lista é bloqueado por `lia-agent-system/tests/test_global_tool_registry_smoke.py`.
- `docs/policies/shim_sla.md` — SLA dos 14 shims `RAILS-DEPRECATED` (data alvo de remoção + responsável). Adicionar shim sem SLA = violar a política.
- `.local/audit/wsi-screening-e2e-report.md` (rev. 3) — auditoria E2E WSI com selo por achado (17 itens). Consultar antes de mexer em rotas de triagem/voz/convite.
- `docs/audits/AUDIT_STATUS_REPORT_2026-04-FINAL.md` §0.1 — reconciliação 2026-04-19 das pendências F4/F5/F8/F10/F11/F12 + #544 + #545.
- `docs/audits/chat-message-actions-and-feedback-loop-audit.md` (Task #569, 2026-04-19) — auditoria das ações por mensagem do chat unificado (copy/thumbs/chips) e do loop de aprendizado. **Achado P0:** endpoints `/api/v1/lia/feedback/{thumbs,rating,correction,metrics}` chamados pelo frontend não existem no backend; `feedback-api.ts` mascara o 404 → loop `interaction_feedback → learning_patterns → prompt` está morto na origem. Hardening na Task #570.

**Skills relacionadas:**
- `feature-audit` — auditoria obrigatória de 14 dimensões antes de marcar qualquer task como concluída.
- `lia-planning` — metodologia de planning unificada (GSD + spec-driven + brainstorming) para qualquer trabalho significativo.
- `canonical-fix` — protocolo de 5 fases para identificar arquivo canônico e corrigir na origem, sem workaround. Aplicada em Task #563 para consolidar `duplicate_job` (4 implementações → 1 canônica em `app.domains.job_management.services.job_clone_service`) e remover stub órfão de `reject_candidate` em `pipeline_tools.py`. Canônico de rejeição: `_reject_candidate` em `app/orchestrator/action_handlers/candidate_actions.py`.
- `vue-migration-prep` — garante que o código novo já nasce preparado para a futura migração Vue/Nuxt.
- `design-standardize` — padronização visual React+Tailwind conforme Design System LIA v4.2.1.

# System Architecture
The platform uses Next.js, React, and TypeScript for the frontend, styled with Radix UI, shadcn/ui, and Tailwind CSS. The backend is built with FastAPI (Python) and PostgreSQL. AI agents are orchestrated with LangGraph and primarily powered by Claude Sonnet.

**Core Architectural Decisions & Features:**
- **Multi-Agent AI System**: Orchestrates specialized AI agents using the WSI methodology for candidate evaluation and supports a custom agent marketplace with metering and billing.
- **Intelligent Conversational Interface (LIA)**: The primary interaction is chat-based, supporting multi-step reasoning, intent classification, and session persistence. It includes a unified chat system with WebSocket and SSE fallback.
- **UI/UX Design**: Adheres to an "ElevenLabs pattern" with a monochromatic palette, cyan accents, a 3-font system, interactive pipeline flows, sortable columns, advanced pagination, and a command palette, all aligned with Design System v4.2.1. Dynamic split-screen panels and a floating Super Prompt enhance user interaction.
- **WSI Screening**: A 6-block AI-powered methodology for comprehensive candidate evaluation, generating detailed reports with STAR analysis, Bloom/Dreyfus levels, gap analysis, and recommendations. Includes a public candidate-facing chat page for WSI screening with text and bidirectional audio support.
- **Compliance (3-Pillar Architecture)**: Designed to comply with LGPD, SOX, and EU AI Act, incorporating FairnessGuard and FactChecker for bias detection. Includes a `BiasAuditService` to calculate adverse impact.
- **Job Creation & Candidate Management**: Supports conversational and manual job creation, with a Kanban candidate movement system featuring AI-powered sub-status prediction and WSI score integration.
- **5-Chat + 2-Channel Architecture**: Comprises dedicated chats for Job Creation, Talent, Jobs Management, Pipeline/Kanban, and Policy, integrated with WhatsApp and MS Teams. Settings pages use the `settings_config` context type via UnifiedChat lateral — no embedded chat. Chat transport: WebSocket first (via `/api/auth/ws-token` JWT), SSE fallback, REST fallback (`POST /api/backend-proxy/chat` → backend `/api/v1/chat`). Backend response format: `{ ok, data: { message: { content }, conversation: { id } } }`. Domain-specific contexts (`company_settings`, `hiring_policy`) skip Phase 1 (ActionExecutor) and Phase 1.5 (Agentic Loop) to route directly to their dedicated agent via context_type_override in Orchestrator.
- **Minha Empresa (Conversational Cards)**: The "Minha Empresa" page in Settings uses collapsible cards (Dados Basicos, Cultura, Tech Stack, Beneficios, Departamentos, Politicas) that update in real-time when the company_settings agent responds via the UnifiedChat lateral. Context auto-switches to `settings_config` on mount.
- **Closed-Loop Action Execution**: Enables full closed-loop actions across chats using `ActionExecutorService` with LLM-powered smart parameter extraction.
- **Talent Funnel Search Optimization**: Leverages Elasticsearch, PG Vector, and WRF for advanced search with LLM job classification and candidate scoring.
- **Progressive Automation & CompanyHiringPolicy**: Implements `CompanyHiringPolicy` to control automation levels with a confidence-based decision engine and conversational onboarding.
- **Multi-Channel Communication Dispatcher**: Sends messages to all available channels (email + WhatsApp) by default.
- **Celery Scheduler & Automations**: Handles background automations for follow-ups, abandoned WSI checks, and feedback sending.
- **Broker Abstraction Layer**: Utilizes a `BrokerInterface` for messaging with `RedisBroker`, `RabbitMQBroker`, and `PubSubBroker` implementations.
- **Voice Analysis Integration**: VoIP browser calls use Gemini Live Audio API with Twilio as PSTN fallback.
- **Security & Production Readiness**: Includes robust authentication with httpOnly cookies, JWT, and WorkOS SSO, API security measures, unified health endpoint, structured logging, and global exception handlers. Per-request cost tracking with budget alerts. RLS (Row Level Security) enforced at PostgreSQL level on 107 VARCHAR company_id tables via migration 068. Deny-by-default policies with `lia_app` non-superuser role. See `docs/RLS_CONTRACT.md` for Rails integration guide.
- **Talent Intelligence Domain**: Implements competitive capabilities such as a Skills Ontology Engine, Internal Mobility matching, Workforce Planning, Interview Intelligence (transcript analysis + Gemini transcription service), and Passive Candidate Nurture. These are part of monetizable modules with module-aware tool gating.
- **Interview Intelligence Infrastructure**: Full interview lifecycle with Microsoft Calendar integration, dedicated transcript/transcript_language/transcript_source columns on Interview model, Gemini-based audio/video transcription service (`app/domains/interview_intelligence/services/transcription_service.py`), background transcription via PATCH `/interviews/{id}/recording`, POST `/interviews/{id}/transcribe`, GET `/interviews/{id}/transcript`. Teams transcription also populates the dedicated columns. Migration 067 adds the new columns.
- **Interview Intelligence Pro (Premium Module)**: 5 services in `app/domains/interview_intelligence/services/`: (1) InterviewWSIService — WSI methodology on transcripts (Bloom/Dreyfus/CBI/Big Five), (2) BiasDetectorService — dual-layer bias detection (regex + LLM), (3) ComparativeAnalysisService — candidate ranking vs vacancy peers, (4) StrategicOpinionService — LLM hiring recommendation with evidence, (5) FeedbackGeneratorService — structured candidate feedback. 5 tools: `analyze_interview_recording` (full suite), `detect_interview_bias`, `generate_interview_opinion`, `generate_candidate_feedback`, `compare_interview_performance`. All gated by `interview_intelligence` module.
- **External API Consumption Tracking (Apify/Pearch)**: Unified ledger for tracking external API costs per tenant. `ExternalApiConsumption` model records every Apify/Pearch call with company_id, cost_usd, cost_brl, exchange_rate, provider, operation, success status. Endpoints: GET `/api/v1/consumption/report` (period report), GET `/api/v1/consumption/invoice-data` (invoice generation data), GET `/api/v1/consumption/budget-status` (Apify budget tracking). Budget alerts via ActivityService when monthly Apify spend exceeds threshold. Env vars: `APIFY_USD_TO_BRL_RATE` (default 5.50), `APIFY_MONTHLY_BUDGET_USD` (default 100.00). `CreditTransactionType` extended with `APIFY_ENRICHMENT` and `PEARCH_SEARCH`. TokenTrackingService extended with `record_apify_usage()` for ai_consumption integration. Migration 075.
- **ATS Integration**: Full integration with Gupy, Pandapé, and Merge.dev.
- **Monetizable Modules Infrastructure**: Provides a framework for managing and gating features as modules with different tiers and statuses (beta, trial, active, expired). Audited in Task #163 — 14-dimension analysis + WeDO governance + LGPD compliance passed. 15 tools mapped to 5 modules (7 PREMIUM_GATED, 8 TASTING). Fail-closed on error. PII masking at LLMService level covers all module tool calls. Tenant isolation via `_enforce_tenant()` on all endpoints. See `docs/audit/AUDIT_MODULES_GOVERNANCE_T163.md`.
- **LLM Configuration**: Allows per-tenant configuration of LLM providers (Gemini, Claude, OpenAI) via settings.
- **Recursive RAG Chunking**: Implements a `RecursiveTextSplitter` strategy for hierarchical document chunking.
- **CrewAI-Style Delegation on AgentBus**: A formal multi-agent delegation system built on AgentBus with `AgentCrew`, `CrewPlan`, and `CrewPlanExecutor` for task orchestration.
- **UI/UX Enhancements**: TopBar eliminated, sidebar now includes user panel and redesigned notification system. TipTap Rich Text Editor integrated for email templates and job descriptions.

# Database Migrations
- **Tool**: Alembic. Versions live in `lia-agent-system/alembic/versions/` (NOT `lia-agent-system/app/db/migrations/`).
- **Apply**: `cd lia-agent-system && python -m alembic upgrade head`. Idempotent — re-runs are no-ops when already at head.
- **Automated**: `scripts/post-merge.sh` runs `alembic upgrade head` after every merge so model changes never leave the running DB out of sync (regression guard for the 2026-04-17 outage where Task #346's migration 082 `add_candidate_company_id` shipped but never ran → all `/candidates` and `/search/candidates` endpoints returned 500 with `UndefinedColumnError: column candidates.company_id does not exist`).
- **Demo tenant**: Canonical UUID is `00000000-0000-4000-a000-000000000001`. Migration 080 retired the legacy string id `'demo_company'` from every string-typed `company_id`/`tenant_id` column and inserted the canonical row into `companies`.

# External Dependencies
- Anthropic (Claude API)
- WorkOS
- Google Gemini (API, Live Audio API)
- Pearch AI
- Microsoft Graph
- Gupy ATS
- Pandapé ATS
- Merge (ATS connector)
- HubSpot
- Stripe
- Apify
- Mailgun (primary email)
- Resend (email fallback)
- PostgreSQL
- Redis
- Elasticsearch
- Sentry (error monitoring)
- OpenAI (Whisper, TTS — PSTN fallback only)
- Twilio (Voice — PSTN fallback only)
- Deepgram (STT/transcrição de voz)
- Celery

# i18n (Internationalization)
- **Library**: next-intl
- **Default locale**: pt (Portuguese), maps to messages/pt-BR.json
- **Supported locales**: pt, en
- **Locale prefix**: always (all routes prefixed with /pt/ or /en/)
- **Root / redirects**: 307 to /pt/
- **Config files**: src/i18n/config.ts, src/i18n/request.ts, src/i18n/routing.ts
- **Message files**: messages/pt-BR.json, messages/en.json
- **Route structure**: src/app/[locale]/ contains all page routes; src/app/api/ stays outside [locale]
- **Localized pathnames**: Not yet implemented. All routes use same path under both locales (e.g., /pt/vagas, /en/vagas). Localized URL rewrites (vagas↔jobs, funil↔pipeline) deferred to future tasks when route structure is consolidated
- **Middleware**: src/middleware.ts chains next-intl locale routing with existing JWT/WorkOS auth
- **Sidebar**: Uses useTranslations('sidebar') — section labels, item labels, user menu, recent items all translated
- **next.config.js**: Uses createNextIntlPlugin wrapping withBundleAnalyzer
- **Locale detection**: Disabled (`localeDetection: false` in routing.ts) — forces Portuguese regardless of browser language
- **Translation status**: All namespaces fully translated (sidebar, chat, jobs, candidates, screening, kanban, agents, settings). ~785 keys translated from English to Portuguese. Remaining ~195 untranslated keys are brand/proper names (WhatsApp, LinkedIn, Score WSI, etc.) intentionally identical in both languages

## WSI Transparency Backfill (task #534)

Legacy `wsi_response_analyses` rows written before task #528 have `transparency_extras` NULL. Run the idempotent backfill once after deploy to populate breakdowns and the degraded-quality banner for historical F11 reports:

```bash
cd lia-agent-system
python scripts/backfill_wsi_transparency_extras.py
# preview only — inspects the first batch and exits (sample, not full count):
BACKFILL_DRY_RUN=1 python scripts/backfill_wsi_transparency_extras.py
```

The select also restricts to completed sessions (`wsi_sessions.status='completed'` or `completed_at IS NOT NULL`) so in-flight sessions are not touched.

The script recomputes the JSONB via `calculate_wsi_deterministic` (Camada 1 only — Camada 2 LLM is not re-run). Backfilled rows are flagged `is_llm_fallback=true`, `degraded_quality=true`, `degraded_reasons=[..., "backfill_recalculated"]` and `layer2_degraded_reason="backfill_legacy_record_layer2_unavailable"` so auditors can tell rebuilt rows from rows produced by the live writer.
