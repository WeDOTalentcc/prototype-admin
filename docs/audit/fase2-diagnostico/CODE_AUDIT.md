# CODE_AUDIT.md — Auditoria de Código e Padrões
**Protocolo:** P05
**Data:** 2026-04-13
**Sistema:** LIA Agent System
**Auditor:** Senior Tech Lead (automatizado via SSH probes + análise estática)

---

## RESUMO EXECUTIVO

| Métrica | Valor |
|---|---|
| Total de arquivos Python | 2.513 |
| Arquivos de teste | 437 (17,4% do total) |
| Migrations Alembic | 76 |
| Domínios de negócio | 55+ |
| Routers FastAPI | 236 |
| Agentes ReAct/LangGraph | 35 |
| Findings críticos (ALTA) | 8 |
| Findings moderados (MÉDIA) | 14 |
| Findings informativos (BAIXA) | 12 |
| **Score de Saúde** | **62/100** |

**Contexto:** O sistema é uma plataforma multi-agente de recrutamento com 2.513 arquivos Python, 76 migrations, 35 agentes especializados e 17+ integrações externas. A arquitetura base (LangGraph ReAct, tenant isolation, compliance layer) é sólida. Os principais riscos concentram-se em: (1) SQL injection via f-string em tool registries LLM-acessíveis, (2) duplicação extrema de implementações de e-mail/WhatsApp, (3) 406 testes para 2.513 arquivos (~16% cobertura estimada), e (4) feature flag `LIA_DISABLE_C3B=1` que desativa toda a camada de compliance.

---

## DOMÍNIO 1 — ORGANIZAÇÃO E ESTRUTURA

### Findings

| Severidade | Descrição | Arquivo(s) | Impacto | Fix |
|---|---|---|---|---|
| **ALTA** | 15 implementações de `send_email()` em 3 camadas distintas sem interface canônica unificada. Tools LLM usam `communication_tools.py` (silently simulated), API usa `api/v1/communication.py`, e `libs/messaging/lia_messaging/email.py` é o terceiro caminho | `app/api/v1/communication.py:94`, `app/api/v1/email_templates.py:459`, `app/api/v1/communications.py:285`, `app/services/email_providers/resend_provider.py:65`, `app/domains/communication/services/email_service.py:149,781`, `app/domains/communication/tools/communication_tools.py:19`, `libs/messaging/lia_messaging/email.py:33` | Emails enviados via agente passam por `communication_tools.py` que tem `simulated=True` no fallback — possível perda silenciosa de comunicações em produção | Definir `CommunicationPort` (interface abstrata) e converter todos os 3 caminhos para chamá-la. Eliminar duplicatas em `app/services/email_providers/` (duplicam `app/domains/communication/services/email_providers/`) |
| **ALTA** | 3 registries de agentes coexistindo: `AgentRegistry`, `ReactAgentRegistry`, `DomainRegistry` — sem documento oficial de qual é canônico para cada operação | `app/shared/agents/agent_registry.py`, `libs/agents-core/lia_agents_core/react_agent_registry.py`, `app/domains/registry.py` | Divergência pode fazer agente registrado em apenas um registry não ser roteado corretamente em determinado contexto | Designar `AgentRegistry` como canônico. Fazer `ReactAgentRegistry` ser adaptador sobre `AgentRegistry`. Escrever ADR. |
| **MÉDIA** | 24 instâncias de `send_whatsapp`/`send_message` espalhadas em 3 APIs (`communication.py`, `communications.py`, `whatsapp.py`) + `libs/messaging` + 6 serviços de domínio | `app/api/v1/communication.py:213`, `app/api/v1/communications.py:449,502,549`, `app/api/v1/whatsapp.py:380`, `app/domains/communication/services/whatsapp_service.py:204`, `libs/messaging/lia_messaging/whatsapp.py:33` | Comportamento inconsistente por canal; risco de mensagem duplicada | Consolidar em `MultiChannelService` como único ponto de envio |
| **MÉDIA** | `PolicySetupAgent` legado importável via shim com `DeprecationWarning` ignorado em produção (`warnings.simplefilter("ignore")`) | `app/agents/policy_setup_agent.py:8-12`, `app/orchestrator/action_handlers/communication_actions.py:757` | Warning é ativamente suprimido — nenhum alerta chega a logs nem a clientes | Remover shim; redirecionar todos os callers para `domains/hiring_policy/agents/policy_react_agent.py` |
| **MÉDIA** | 55+ domínios sem `DOMAIN_CATALOG.md` individual; único catálogo em `app/domains/DOMAIN_CATALOG.md`. Endpoints como `api/v1/lia_assistant/` têm 4 submodules sem estrutura de domínio | `app/api/v1/lia_assistant/`, `app/api/v1/candidate_search/`, `app/api/v1/automation/` | Dificulta onboarding de novos devs e estabelecimento de ownership | Mapear cada subdiretório de `api/v1/` para um domínio; criar `OWNERS.md` por domínio |
| **BAIXA** | 278 arquivos `__init__.py` com estrutura inconsistente (alguns vazios, alguns com re-exports, alguns com lógica de bootstrap) | Padrão em `/app/domains/*/`, `/app/shared/` | Importações circulares latentes | Padronizar: `__init__.py` apenas com re-exports explícitos |
| **BAIXA** | `LegacyChatPage` presente no routing mas não usado (`chat-page.tsx:44`) — confirmado no PLATFORM_MAP | Frontend (`plataforma-lia/`) | Dead code aumenta bundle e confunde devs | Remover componente e rota |

---

## DOMÍNIO 2 — QUALIDADE DO CÓDIGO DE IA

### Findings

| Severidade | Descrição | Arquivo(s) | Impacto | Fix |
|---|---|---|---|---|
| **ALTA** | `MultimodalService` (LLM Factory) bypassa a factory via raw httpx direto — sem PII strip, sem audit trail, sem tenant routing | `app/domains/ai/services/llm.py:163` (e classes relacionadas) | Chamadas Gemini via `generate_with_gemini()` saem sem compliance layer — viola LGPD Art. 20 e audit trail | Refatorar `MultimodalService` para obrigatoriamente passar por `get_provider_for_tenant()` |
| **ALTA** | `LLM_DEFAULT_TEMPERATURE=0.7` definido em settings, mas OpenAI hardcoded em `llm.py:163` com `temperature=0.7` sem ler settings; providers Claude e Gemini também usam `0.7` como default sem respeitar `LLM_AGENT_TEMPERATURE=0.3` para agentes | `app/domains/ai/services/llm.py:163`, `app/shared/providers/llm_claude.py:58,87`, `app/shared/providers/llm_gemini.py:52`, `app/domains/cv_screening/services/wsi_service/question_generator.py:575,633,701` | Agentes recebem temperatura 0.7 (criatividade) em vez de 0.3 (precisão) — saídas menos determinísticas; inconsistência com ADR | Passar `temperature=settings.LLM_AGENT_TEMPERATURE` nos providers; eliminar magic numbers |
| **ALTA** | 6 arquivos com prompts inline como f-strings (`system_prompt = f"..."`) — não externalizados em `app/prompts/` | 6 arquivos (probe: 6 hits de `system_prompt\s*=\s*f"`) | Impossível versionar, auditar ou A/B testar prompts sem deploy; contaminação de lógica com template | Mover para `app/prompts/<domain>/` como `.txt` ou `.yaml` com slot typing |
| **MÉDIA** | Modelos hardcoded diretamente no código: `"claude-sonnet-4-6"` em 8+ lugares, `"gemini-2.5-flash"` em 4+, `"gpt-4o"` em 3+, `"gemini-2.0-flash-exp"` em `gemini_voice.py:380` sem env override | `app/api/v1/wsi/evaluation.py:350`, `app/api/v1/wsi/questions.py:198`, `app/api/v1/rubric_evaluation.py:187,205,224,325,336`, `app/api/v1/gemini_voice.py:380`, `app/api/v1/experience_highlights.py:37` | Upgrade de modelo requer localização manual de todos os hardcodes; `gemini-2.0-flash-exp` é alias instável (preview) | Centralizar em `app/core/agent_model_config.py` e referenciar via constante |
| **MÉDIA** | RAGAS evaluation (faithfulness, answer_relevancy, context_precision, context_recall) é apenas observabilidade — scores abaixo de 0.70 geram apenas WARNING log, sem ação automática sobre seleção de modelo, prompts ou RAG | `app/domains/ai/services/ragas_evaluation_service.py` | Loop de qualidade incompleto — plataforma não auto-corrige quando qualidade de resposta cai | Implementar ação mínima: se `overall_score < 0.70` por N avaliações consecutivas, acionar alert + criar Jira ticket via webhook |
| **MÉDIA** | Whisper local (`whisper.load_model("base")`) usado como fallback em 2 pontos críticos — modelo não bundled em produção (nenhum `.pkl`/`.pt` encontrado no disco) | `app/services/voice_interview_state_machine.py:270`, `app/services/twin_knowledge_indexer.py:221` | Em produção, fallback para Whisper local falhará silenciosamente se model não instalado | Substituir fallback local por chamada Whisper API (`whisper-1`) com circuit breaker; documentar como requisito de deployment se local for necessário |
| **BAIXA** | Token tracking (`usage_metadata`, `increment_usage`) em apenas 11 arquivos — muitos caminhos de LLM sem contabilização de tokens | `app/domains/credits/services/token_budget_service.py`, `app/api/v1/agent_chat_ws.py` | Billing e budget enforcement incompletos para caminhos que bypassa o WS principal | Adicionar callback de token counting em todos os providers via LangChain `callbacks` |

---

## DOMÍNIO 3 — PADRÕES DE INTEGRAÇÃO

### Findings

| Severidade | Descrição | Arquivo(s) | Impacto | Fix |
|---|---|---|---|---|
| **ALTA** | `OPENMIC_WEBHOOK_SECRET` não configurado permite bypass completo de validação HMAC em webhook de voz — com log WARNING mas sem bloqueio | `app/api/v1/openmic_webhook.py:159` | Webhook de triagem de voz pode ser invocado por qualquer ator externo sem autenticação | Tornar `OPENMIC_WEBHOOK_SECRET` obrigatório em produção (falhar no startup se ausente); bloquear request se secret ausente, não só logar |
| **ALTA** | `LIA_DISABLE_C3B=1` desativa **toda** a camada de compliance pré/pós LLM — passthrough completo. Feature flag sem controle de acesso, auditoria ou expiração | `app/shared/compliance/c3b_layer.py:7,15` | Um env var mal configurado desativa LGPD Art. 20, FairnessGuard, PII strip, AuditCallback — risco regulatório severo | Remover flag ou restringir a `APP_ENV=development`; exigir aprovação multi-pessoa para habilitação em staging; adicionar alerta em startup quando ativado |
| **MÉDIA** | `httpx.AsyncClient` instanciado sem `timeout` consistente e sem pool compartilhado em 15+ arquivos — cada request cria nova conexão TCP | `app/api/v1/workos.py:755`, `app/api/v1/ats.py:235`, `app/api/v1/calendar.py:652`, `app/api/v1/teams.py:1428,1445`, `app/api/v1/company.py:853`, `app/services/email_providers/mailgun_provider.py:135` | Sem connection pooling, alto volume de requests pode esgotar file descriptors; sem timeout padrão, algumas chamadas sem timeout podem travar workers | Criar `shared/http_client.py` com `AsyncClient` singleton (ou `async_generator` de sessão) com timeout padrão e `limits` configuráveis |
| **MÉDIA** | Twilio webhook usa HMAC-SHA1 para assinatura — SHA1 considerado fraco criptograficamente; nenhum plano de migração para SHA-256 identificado | `app/api/v1/whatsapp_webhook.py:45` | SHA1 vulnerável a colisões teóricas; Twilio suporta migração para SHA-256 via header header | Migrar para HMAC-SHA256 assim que Twilio liberar migration path; documentar no backlog |
| **MÉDIA** | Rate limiting (Redis sliding window) tem fallback para in-memory dict em instância única — sem sincronização entre workers. APScheduler usa `MemoryJobStore` (single-instance) | `app/middleware/rate_limiter.py`, `app/domains/automation/services/automation_scheduler.py` | Em deploys multi-worker/multi-container, rate limits e jobs schedulados não são coordenados | Garantir Redis disponível em produção; migrar APScheduler para `RedisJobStore` (bug de pickle com ZoneInfo documentado — criar issue para fix) |
| **BAIXA** | Sem `idempotency_key` em requests de mutação HTTP para APIs externas (Resend, Mailgun, Twilio) — apenas operações internas têm idempotency tracking | `app/shared/robustness/context_management.py:123-196` (interno apenas) | Retry em falha transiente pode causar duplicação de email/SMS para candidato | Adicionar `Idempotency-Key: sha256(tenant+candidate+template+timestamp_day)` no header de todas as chamadas de envio |
| **BAIXA** | Deepgram referenciado em allowlist do OpenMic sem serviço dedicado verificável | `app/services/voice/deepgram_service.py` (apenas httpx client) | Dependência externa não documentada formalmente — sem circuit breaker próprio | Confirmar se Deepgram está em uso; se sim, registrar circuit breaker |

---

## DOMÍNIO 4 — PERSISTÊNCIA E DADOS

### Findings

| Severidade | Descrição | Arquivo(s) | Impacto | Fix |
|---|---|---|---|---|
| **ALTA** | SQL f-strings com `{where_clause}` montado dinamicamente em tool registries diretamente acessíveis por agentes LLM — embora condições individuais usem parâmetros `:param`, o `where_clause` é um join de strings | `app/domains/sourcing/agents/sourcing_tool_registry.py:133,251`, `app/domains/sourcing/agents/diversity_tool_registry.py:153`, `app/domains/sourcing/agents/passive_pipeline_tool_registry.py:99`, `app/domains/hiring_policy/agents/policy_tool_registry.py:112,952`, `app/domains/lgpd/services/lgpd_cleanup_service.py:111,127`, `app/orchestrator/context_adapter.py:296`, `app/jobs/tasks/compliance.py:190,206` | Se um agente injetar valor inesperado como nome de tabela/coluna via argumento de tool, o where_clause resultante pode ser manipulado. Risco amplificado porque esses tools são invocados autonomamente pelo LLM | Extrair construção de queries para repository classes com ORM (SQLAlchemy `select()` + `where()`); eliminar f-strings em queries |
| **MÉDIA** | `generate_offer` tool é read-only — lê dados e retorna texto, sem persistir registro em tabela `offers`; operação critica de auditoria (LGPD, trabalhista) sem rastreabilidade | Identificado no PLATFORM_MAP §9.4 | Ofertas geradas por agente não ficam auditáveis; em litígio trabalhista, não há prova da proposta feita | Criar tabela `generated_offers` com FK para `vacancy_candidates`; tool deve fazer INSERT antes de retornar texto |
| **MÉDIA** | `schedule_interview` tool tem dois caminhos paralelos: stub em `scheduling_tools.py` (retorna URL falsa sem DB write) e implementação real em `communication_tools.py` — não unificados | `app/domains/pipeline/agents/scheduling_tools.py:59`, `app/domains/communication/tools/communication_tools.py:208` | Agente pode chamar stub e criar entrevista fantasma — sem registro em `interviews` table | Remover stub; garantir tool registry aponta para `communication_tools.py:208` |
| **MÉDIA** | 41 arquivos usam `is_deleted`/`deleted_at`/`soft_delete` sem garantia de filtro em todas as queries — se query não inclui `WHERE is_deleted = false`, dado deletado reaparece | 41 arquivos com soft delete (probe) | Candidatos LGPD-deletados podem reaparecer em resultados de busca | Implementar SQLAlchemy event listener global que injeta filtro `is_deleted=false` para modelos com soft delete (padrão Django-style) |
| **BAIXA** | Vários endpoints com `# TODO(phase2): extract to repository` têm queries SQLAlchemy diretas no route handler — viola separação de camadas | `app/api/v1/suggestion_feedback.py:72`, `app/api/v1/learning_patterns.py:23`, `app/api/v1/wsi/sessions.py:32`, `app/api/v1/wsi/evaluation.py:48`, `app/api/v1/audit_timeline.py:77` + 20 outros | Dificuldade de teste unitário; acoplamento forte entre HTTP layer e persistência | Sistematizar extração de repos; criar `BaseRepository` genérico |
| **BAIXA** | `_load_model_weights()` em predictive analytics retorna dict hardcoded — pesos não persistidos em tabela, não versionados, não auditáveis | `app/domains/analytics/services/predictive_analytics_service.py` | Mudança de pesos requer deploy; impossível A/B testar; sem auditoria de mudanças | Mover pesos para tabela `ml_model_weights` com versionamento e timestamp |

---

## DOMÍNIO 5 — SEGURANÇA

### Findings

| Severidade | Descrição | Arquivo(s) | Impacto | Fix |
|---|---|---|---|---|
| **CRÍTICA** | `LIA_DISABLE_C3B=1` desabilita pré-compliance (PII auto-sanitize LIA-C04, FairnessGuard LIA-C05, AuditCallback, ComplianceDomainPrompt LIA-C01) sem qualquer controle de acesso | `app/shared/compliance/c3b_layer.py:7,15` | Desabilitação acidental ou intencional viola LGPD, pode expor PII de candidatos em logs, bypassa fairness checks — risco legal direto | Restringir a `APP_ENV=development` (bloquear em `staging` e `production`); adicionar log CRITICAL no startup se ativado; adicionar alerta Sentry |
| **ALTA** | CORS default `allow_methods=["*"]` e `allow_headers=["*"]` com `allow_credentials=True` — combinação perigosa em lista de origins não wildcard mas potencialmente ampla | `app/main.py:385-390` | Se `CORS_ORIGINS` for mal configurado em produção (e.g., `["*"]`), combinado com credentials=True, ativa CORS misconfiguration | Restringir `allow_methods` a lista explícita; `allow_headers` a lista mínima necessária; validar que `CORS_ORIGINS` não inclui `*` no startup |
| **ALTA** | Webhook OPENMIC sem secret configurado é aceito sem autenticação (só warning log) | `app/api/v1/openmic_webhook.py:159` | Qualquer ator pode acionar scoring de triagem de voz | Tornar secret obrigatório; retornar 403 se ausente |
| **MÉDIA** | `SECRET_KEY = "change-this-in-production"` como default, com validação apenas quando `APP_ENV=production` — staging pode rodar com chave fraca | `libs/config/lia_config/config.py:146,349` | JWT forjável em staging se key não alterada; staging geralmente tem dados reais de teste | Validar também para `APP_ENV=staging`; adicionar mínimo de 32 chars |
| **MÉDIA** | 53 comments de TODO técnico pendentes em routes de API — alguns incluem funcionalidades críticas não implementadas: `admin_platform.py` tem TODO para provisioning WorkOS + email de boas-vindas substituídos por no-ops | `app/api/v1/admin_platform.py:91,129,134,138` | Admin cria cliente sem provisionar WorkOS e sem enviar email de boas-vindas — fluxo quebrado silenciosamente | Implementar ou criar tickets rastreáveis; nunca deixar TODO em path de produção sem fallback |
| **MÉDIA** | Endpoints protegidos por `get_db` (sem RLS no Postgres) — isolamento multi-tenant depende inteiramente de app-level. Se bug bypass autenticação, dados de outro tenant são acessíveis | Confirmado no PLATFORM_MAP §7 | Tenant isolation fault = data breach | Avaliar Row Level Security (RLS) no Postgres como defense-in-depth |
| **BAIXA** | Token parcial logado em `client_users.py:113` (`token[:10]...`) e token WhatsApp em `whatsapp.py:127` (`token[:10]...`) — mesmo truncado, pode ser suficiente para ataques de prefixo em tokens curtos | `app/api/v1/client_users.py:113`, `app/api/v1/whatsapp.py:127` | Em tokens de 20-32 chars, 10 caracteres é 31-50% do espaço — reduz entropia de busca | Usar hash SHA-256 do token para logging; nunca logar prefix |

---

## DOMÍNIO 6 — DÉBITO TÉCNICO DE VIBE CODING

### Findings

| Severidade | Descrição | Arquivo(s) | Impacto | Fix |
|---|---|---|---|---|
| **ALTA** | Cobertura de testes estimada ~16% (406 test files para 2.513 arquivos Python) — 0 testes para os 35 agentes em produção (apenas 6 test files em `tests/test_agents/` que testam graphs LangGraph, não tools individuais) | `app/tests/` (18 files), `tests/test_agents/` (6 files para LangGraph), resto sem tests | Regressões em tool registries e agent behaviors vão diretamente para produção sem detecção | Estabelecer threshold mínimo de 60% cobertura em `app/domains/*/tools/` e `app/domains/*/agents/`; CI deve falhar abaixo do threshold |
| **ALTA** | `main_orchestrator.py` tem 1.188 linhas e `agent_chat_ws.py` tem 1.101 linhas — ambos combinam responsabilidades de routing, compliance, memory, serialization, streaming e error handling | `app/orchestrator/main_orchestrator.py`, `app/api/v1/agent_chat_ws.py` | Funções de 100+ linhas são impossíveis de testar unitariamente; bug em qualquer parte afeta o fluxo inteiro | Quebrar em classes focadas: `ComplianceLayer`, `MemoryManager`, `StreamingHandler`, `ChatRouter` |
| **ALTA** | `sourcing_tool_registry.py` tem 1.423 linhas em um único arquivo — mistura tools de search, query building, filtering, ranking, pearch integration, e DB access | `app/domains/sourcing/agents/sourcing_tool_registry.py` | Arquivo inmantenível; qualquer mudança de schema de candidatos requer editar 1.400 linhas | Decompor em módulos por responsabilidade: `query_builder.py`, `ranking.py`, `enrichment.py` |
| **MÉDIA** | 3.545 ocorrências de variáveis genéricas (`result`, `data`, `response`, `temp`) — média de 1.4 por arquivo Python | Codebase inteiro | Dificulta rastreamento de bugs; code review automatizado não consegue identificar tipo/semântica | Executar linting com `ruff` + regra `N806/N803`; nomear por semântica: `candidate_rows`, `llm_response`, etc. |
| **MÉDIA** | 53 comentários `# TODO` ativos no código de produção — 31 deles referenciando "phase2" sem data de entrega ou ticket | `app/api/v1/` (40+ arquivos) | TODOs são dívida sem SLA — ficam no código indefinidamente | Converter todos os TODOs em GitHub Issues; deletar comentário do código quando issue criado |
| **MÉDIA** | `saas_metrics.py` (963 linhas), `observability.py` (934 linhas), `compliance_controls.py` (748 linhas), `technical_tests.py` (704 linhas) — router files com business logic embutida | `app/api/v1/saas_metrics.py`, `app/api/v1/observability.py`, `app/api/v1/compliance_controls.py` | Business logic em router impossibilita reutilização e teste | Extrair lógica para service layer conforme padrão já estabelecido em `app/domains/` |
| **BAIXA** | `app/orchestrator/policy_engine.py:118` usa `%s` (psycopg2-style) em vez de `:param` (SQLAlchemy-style) — inconsistência de parameter binding | `app/orchestrator/policy_engine.py:118` | Risco de falha silenciosa se driver mudar; inconsistência dificulta revisão de segurança | Uniformizar para `:param` em todo o codebase |
| **BAIXA** | `app/api/v1/lia_assistant/conversational.py` contém string de prompt inline com instruções de formato monetário em português hardcoded no route handler | `app/api/v1/lia_assistant/conversational.py:136-141` | Prompt embutido em route não é versionado nem testável isoladamente | Mover para `app/prompts/lia_assistant/conversational_format.txt` |

---

## ÍNDICE DE SAÚDE DO CODEBASE

**Score:** 62/100

| Dimensão | Peso | Pontos Obtidos | Score |
|---|---|---|---|
| Organização | 15% | 8/15 | 8/15 |
| IA Code Quality | 20% | 12/20 | 12/20 |
| Integração | 15% | 9/15 | 9/15 |
| Persistência | 15% | 10/15 | 10/15 |
| Segurança | 20% | 12/20 | 12/20 |
| Vibe Coding Debt | 15% | 11/15 | 11/15 |

**Justificativa do score por dimensão:**

**Organização (8/15):** Arquitetura de domínios bem estruturada (55+ domínios) e padrão DDD coerente (+5). Penalizações: 15 implementações de `send_email` sem interface canônica (-3), 3 registries de agentes sem canônico definido (-2), 24 implementações de `send_whatsapp` (-2).

**IA Code Quality (12/20):** Base forte: LangGraph ReAct, compliance pipeline, 3-layer memory, fairness integration (+8). Penalizações: temperatura incorreta para agentes (0.7 em vez de 0.3) em múltiplos providers (-2), 6 arquivos com prompts inline (-2), hardcode de model names em 12+ lugares (-2), RAGAS sem loop de ação (-1), Whisper local sem fallback seguro (-1).

**Integração (9/15):** Rate limiting Redis com fallback in-memory (+3), HMAC para webhooks (+2), circuit breakers documentados (+2). Penalizações: OPENMIC webhook bypassável (-2), sem connection pooling em httpx (-2), Twilio HMAC-SHA1 (-1), sem idempotency em APIs externas (-1).

**Persistência (10/15):** 76 migrations bem mantidas (+3), soft delete em 41 arquivos (+2), pgvector HNSW (+2), transações com rollback (+2). Penalizações: f-string SQL em tool registries (-3), `generate_offer` sem persistência (-1), stub de `schedule_interview` sem DB write (-1).

**Segurança (12/20):** Prompt injection guard (20+ patterns) (+3), JWT + WorkOS SSO (+3), FairnessGuard pré-LLM (+3), PII masking global (+3). Penalizações: `LIA_DISABLE_C3B` bypass crítico (-4), OPENMIC sem secret obrigatório (-2), CORS com `["*"]` methods/headers + credentials (-2), token prefix em logs (-1).

**Vibe Coding Debt (11/15):** Arquitetura bem documentada com PLATFORM_MAP (+3), padrão de repository em evolução (+2), testes de integração para fluxos críticos (+2). Penalizações: 16% cobertura de testes (-2), arquivos de 1.000+ linhas (-2), 3.545 variáveis genéricas (-1), 53 TODOs sem SLA (-1).

---

## TOP 10 PRIORIDADES DE REMEDIAÇÃO

Ordenadas por `severidade × esforço` (alta severidade, baixo esforço primeiro):

| # | Prioridade | Finding | Severidade | Esforço | Ação Imediata |
|---|---|---|---|---|---|
| 1 | **CRÍTICA** | `LIA_DISABLE_C3B=1` sem restrição de ambiente | CRÍTICA | Baixo (1h) | Adicionar `if _C3B_DISABLED and settings.APP_ENV != "development": raise RuntimeError(...)` no startup |
| 2 | **CRÍTICA** | OPENMIC webhook sem secret obrigatório | ALTA | Baixo (2h) | Adicionar verificação early-return com 403 se `OPENMIC_WEBHOOK_SECRET` não configurado |
| 3 | **ALTA** | SQL f-strings em tool registries LLM-acessíveis | ALTA | Médio (3-5 dias) | Converter queries de `sourcing_tool_registry.py`, `diversity_tool_registry.py`, `passive_pipeline_tool_registry.py` para SQLAlchemy ORM |
| 4 | **ALTA** | Temperatura incorreta em providers de LLM (0.7 vs 0.3) | ALTA | Baixo (4h) | Passar `temperature=settings.LLM_AGENT_TEMPERATURE` nos construtores de `llm_claude.py`, `llm_gemini.py`, `llm.py` |
| 5 | **ALTA** | `send_email` em 15 implementações — path de agente usa `simulated=True` | ALTA | Alto (1 semana) | Criar `CommunicationPort`, wiring imediato do path de tools para implementação real |
| 6 | **ALTA** | `schedule_interview` stub retorna URL falsa sem DB write | ALTA | Médio (1 dia) | Remover stub em `scheduling_tools.py`; apontar tool registry para `communication_tools.py:208` |
| 7 | **ALTA** | `generate_offer` sem persistência para auditoria | ALTA | Médio (1 dia) | Criar tabela `generated_offers`; adicionar INSERT na tool antes de retornar resposta |
| 8 | **ALTA** | Cobertura de testes ~16% — 0 testes para tool registries | ALTA | Alto (contínuo) | Configurar pytest-cov no CI com threshold 40% mínimo; priorizar testes de `sourcing_tool_registry.py` e `candidate_actions.py` |
| 9 | **MÉDIA** | `MultimodalService` bypassa LLM factory (sem PII strip, sem audit) | MÉDIA | Médio (2 dias) | Refatorar para obrigatoriamente passar por `get_provider_for_tenant()` |
| 10 | **MÉDIA** | 1.188 linhas em `main_orchestrator.py` e 1.101 em `agent_chat_ws.py` | MÉDIA | Alto (1-2 semanas) | Extrair `ComplianceLayer`, `MemoryManager`, `StreamingHandler` como classes separadas com testes unitários |

---

## APÊNDICE A — METODOLOGIA DE AUDITORIA

**Ferramentas utilizadas:**
- SSH probes com grep/find sobre 2.513 arquivos Python
- Análise de PLATFORM_MAP.md (reconhecimento fase 1, 150+ items)
- Inspeção manual de arquivos críticos: `main_orchestrator.py`, `agent_chat_ws.py`, `config.py`, `sourcing_tool_registry.py`, `prompt_injection.py`, `c3b_layer.py`
- Contagem de padrões: grep por anti-patterns, hardcodes, TODOs, variáveis genéricas

**Limitações:**
- Cobertura de testes: estimada por file count, não por linha executada (sem pytest-cov executado)
- SQL injection: análise estática conservadora — `where_clause` com condições parametrizadas é menos crítico, mas ainda merece refatoração para ORM
- Secrets em produção: auditoria confirma ausência de secrets hardcoded no código (apenas em testes com `"test-key"`)

## APÊNDICE B — EVIDÊNCIAS NUMÉRICAS

| Métrica | Valor | Fonte |
|---|---|---|
| Total arquivos .py | 2.513 | `find ... -name "*.py" \| wc -l` |
| Arquivos de teste | 406 (`test_*.py`) + 437 em `*/tests/*` | find probes |
| Migrations | 76 (até `076_consumption_observability_fields.py`) | `ls alembic/versions/` |
| Domínios em `app/domains/` | 55+ | `ls app/domains/` |
| `__init__.py` files | 278 | find probe |
| Implementações `send_email` | 15 | grep probe |
| Implementações `send_whatsapp`/`send_message` | 24 | grep probe |
| Arquivos com prompts f-string inline | 6 | grep probe |
| Hardcoded model names (non-test, non-comment) | 14+ instâncias | grep probe |
| Arquivos com rate limiting | 20 | grep probe |
| Arquivos com soft delete | 41 | grep probe |
| TODOs no código de produção | 53 | grep probe |
| Variáveis genéricas (`result`, `data`, etc.) | 3.545 | grep probe |
| Arquivos com SQL f-strings | 8+ | grep probe |
| Arquivos de JWT/auth | 37 | grep probe |
| Pydantic validation em API layer | 192 arquivos | grep probe |

