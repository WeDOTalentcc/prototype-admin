# CODE_AUDIT.md — Auditoria de Código: WeDOTalent Platform
> P05 · Fase 2 · Data: 2026-04-14

---

## Sumário Executivo

A plataforma WeDOTalent é composta por três camadas de código auditadas neste documento: a camada de IA em Python (FastAPI + LangGraph), o frontend em Next.js 15 e o backend Rails 7.1 em transição para CRUD canônico. A camada Python demonstra a arquitetura mais madura, com circuit breakers, YAML de prompts, multi-tenancy e orquestração LangGraph bem implementados, mas carrega riscos operacionais sérios como bypass silencioso de compliance e falsa confirmação de email para recrutadores. O frontend Next.js tem boas abstrações de proxy e sistema de autenticação robusto, mas sofre de dívida de vibe coding expressiva — dual chat system coexistente, cobertura de testes de ~7% e um bypass de autenticação de staging crítico. O Rails é a camada de maior risco imediato: quatro achados críticos de produção (acesso cross-tenant de candidatos com violação LGPD, nova conexão TCP RabbitMQ por request, CORS hardcoded em localhost, e JWT triplicado com lógica divergente) bloqueiam qualquer deploy em ambiente multi-tenant real. Com média ponderada de **66/100**, a plataforma tem fundações arquiteturais válidas, mas requer remediação urgente nos P0 antes de escalar a produção.

---

## Índice de Saúde do Codebase

| Camada | Score | Status |
|--------|-------|--------|
| Python AI Layer | 70/100 | 🟡 |
| Next.js Frontend | 68.5/100 | 🟡 |
| Rails Backend | 56/100 | 🔴 |
| **MÉDIA PONDERADA** | **66/100** | |

**Cálculo da média ponderada:** A camada de IA Python é o produto central e diferencial competitivo (peso 40%), o Frontend é a superfície crítica com o usuário (peso 35%), e o Rails é uma camada transitória de CRUD em migração (peso 25%).

- Python AI Layer: 70 × 0,40 = **28,0**
- Next.js Frontend: 68,5 × 0,35 = **23,975**
- Rails Backend: 56 × 0,25 = **14,0**
- **Total ponderado: 65,975 → 66/100**

**Interpretação geral:** As três camadas operam com bases arquiteturais razoáveis — a separação de domínios Python, as abstrações de proxy do Next.js e o namespacing REST do Rails são escolhas corretas. O problema está na execução: riscos de segurança e confiabilidade identificados em todas as camadas, com o Rails apresentando falhas de produção imediatas (CORS em localhost, acesso cross-tenant) e o Python com riscos de compliance e confiabilidade do produto (falsa confirmação de email). Com 4 semanas de remediação focada nos P0 e P1 listados neste documento, o score pode atingir 80+.

---

## Achados Críticos — Cross-Layer (BLOQUEIAM PRODUÇÃO)

Os seguintes achados, combinados, impedem um deploy seguro em ambiente multi-tenant de produção:

1. **[RAILS — CRÍTICO] S1 — Candidatos sem `account_id`: acesso cross-tenant de dados pessoais**
   Arquivo: `db/schema.rb` + `app/controllers/v1/users/candidates_controller.rb`
   A tabela `candidates` não possui `account_id`. Um recrutador da Empresa A pode acessar os dados pessoais (CPF, data de nascimento, salário) de candidatos da Empresa B via `GET /v1/users/candidates/:id`. Violação direta da LGPD.

2. **[RAILS — CRÍTICO] S2 — Nova conexão TCP RabbitMQ por mensagem publicada**
   Arquivo: `app/services/message_service/event_publisher.rb:4`
   Cada chamada `publish` abre uma nova conexão TCP com o RabbitMQ (latência 50-200ms), cria canal, publica e fecha. Sob carga, esgota file descriptors e pode derrubar o broker. Ocorre dentro de request HTTP síncrono de magic link, bloqueando o login do usuário.

3. **[RAILS — CRÍTICO] S3 — CORS hardcoded `localhost:3000`: API inacessível em produção**
   Arquivo: `config/initializers/cors.rb:3`
   A única origem CORS aceita é `http://localhost:3000`. Qualquer requisição do frontend de produção (ex: `app.wedotalent.com`) é bloqueada. A API Rails está essencialmente inoperante para o frontend real.

4. **[RAILS — CRÍTICO] S4 — JWT implementado em 3 locais com lógicas divergentes e API deprecada**
   Arquivos: `app/lib/json_web_token.rb`, `app/controllers/application_controller.rb:22`, `app/controllers/v1/sessions_controller.rb:44`, `app/controllers/v1/users/application_controller.rb:50`
   Três implementações de `jwt_decode`. Uma usa `secrets.secret_key_base` (deprecado no Rails 7.1). Uma tem `rescue` bare sem tipo (engole qualquer exceção). Mudança de lógica JWT exige atualizar 3 arquivos.

5. **[PYTHON — CRÍTICO] D5-01 — `LIA_DISABLE_C3B=1` bypassa silenciosamente toda a camada de compliance**
   Arquivo: `app/shared/compliance/c3b_layer.py:15`
   Uma variável de ambiente não auditada desabilita completamente o FairnessGuard em todos os tenants simultaneamente, sem log de auditoria. Risco de LGPD/GDPR e reputacional para plataforma B2B de RH.

6. **[PYTHON — CRÍTICO] D6-01 — Email "simulado" confirmado como enviado ao recrutador**
   Arquivo: `app/domains/communication/tools/communication_tools.py`
   Quando a query ao modelo Candidate falha, a tool `send_email` retorna `{"success": True, "data": {"simulated": True}}`. O agent confirma envio, o recrutador vê confirmação — nenhum email chegou. Falsa confirmação de dado crítico do produto.

7. **[FRONTEND — CRÍTICO] DEV_AUTO_LOGIN habilitado por padrão em ambientes não-produção**
   Arquivo: `src/middleware.ts:10`
   `DEV_AUTO_LOGIN = process.env.NODE_ENV !== 'production'` — em staging (Replit), qualquer pessoa acessa a plataforma completa sem credenciais, com conta demo. Exposição pública de staging.

8. **[FRONTEND — ALTO] `dangerouslySetInnerHTML` sem sanitização no layout raiz**
   Arquivo: `src/app/[locale]/layout.tsx:120,126`
   Dois usos de `dangerouslySetInnerHTML` no layout raiz sem `DOMPurify`/`sanitizeHtml`. XSS persistente se qualquer dado dinâmico atingir esses pontos.

9. **[FRONTEND — ALTO] 5 rotas `bulk/*` sem auth cookie fallback**
   Arquivos: `candidates/bulk/update-status/route.ts`, `bulk/assign-job/route.ts`, `bulk/send-email/route.ts`, `bulk/start-screening/route.ts`, `bulk/delete/route.ts`
   Padrão manual ad-hoc sem fallback para cookie `lia_access_token`. Se o header Authorization não vier, a chamada vai sem autenticação.

---

## D1 — Organização & Estrutura

### Python AI Layer

**Métricas**
- Diretórios: 60 mapeados (domains, api, orchestrator, services, shared, agents, middleware, etc.)
- Arquivos Python: >450 | Linhas: >152.000
- TODO/FIXME/HACK: **59 ocorrências**
- `send_email` implementações distintas: **11 funções**

**Achados**

#### [CRÍTICO] D1-01 — Duplicação Massiva de Funções de Comunicação
**Arquivos afetados (seleção):**
- `app/api/v1/communication.py:94` — `async def send_email`
- `app/api/v1/communications.py:285` — `async def send_email` (arquivo diferente, função idêntica)
- `app/api/v1/email_templates.py:459` — `async def send_email`
- `app/domains/communication/tools/communication_tools.py:19` — `async def send_email`
- `app/domains/communication/services/email_service.py:149` e `:781` — dois `send_email` no mesmo arquivo
- `app/services/email_providers/resend_provider.py:65` e `app/domains/communication/services/email_providers/resend_provider.py:65` — dois providers Resend idênticos

**Impact:** Qualquer bug em lógica de envio precisa ser corrigido em 6+ lugares. O domínio `communication` tem dois stacks paralelos (`app/services/email_providers/` e `app/domains/communication/services/email_providers/`) — apenas o segundo é importado pela produção, o primeiro é código morto mas mantido no repo. Risco de regressão alto.

**Fix:** Unificar sob `app/domains/communication/services/`. Remover `app/services/email_providers/` e `app/api/v1/communication.py` (há `communications.py` canônico). Consolidar as duas implementações de `EmailService`.

---

#### [ALTO] D1-02 — 59 TODOs de "extract to repository" não resolvidos
**Padrão:** `# TODO(phase2): extract to repository` em 30+ arquivos de rota.

**Exemplos:**
- `app/api/v1/suggestion_feedback.py:72`
- `app/api/v1/wsi/sessions.py:32`
- `app/api/v1/audit_timeline.py:77`
- `app/api/v1/automation/event_handlers/handlers_lifecycle.py:934, :1179`

**Impact:** Lógica de negócio diretamente em route handlers (routes com >1.000 linhas: `billing.py:1713`, `teams.py:1557`, `interview_notes.py:1203`, `data_request.py:1169`). Dificulta reuso, teste unitário e separação de responsabilidades. Alinhado com "TODO(phase2)" que aparentemente nunca veio.

**Fix:** Sprint dedicado de extração de repositórios. Priorizar os 5 arquivos com >1.000 linhas.

---

#### [MÉDIO] D1-03 — Dois `job_wizard.py` de prompts duplicados
**Arquivos:**
- `app/shared/prompts/job_wizard.py` (451 linhas)
- `app/domains/job_management/prompts/job_wizard.py` (410 linhas)

**Nota positiva:** `app/prompts/job_wizard.py` faz `from app.shared.prompts.job_wizard import *` (proxy), e produção importa `shared/prompts`. O arquivo de `domains/job_management/prompts/` é código morto/legado mas com 410 linhas quase idênticas. Risco de drift.

**Fix:** Remover `app/domains/job_management/prompts/job_wizard.py` após verificar que nada o importa diretamente.

---

**Código afetado estimado:** ~15% dos arquivos de rota têm duplicação ou acoplamento direto.
**Score D1: 62/100**

---

### Next.js Frontend

**Métricas**
- 1.037 arquivos `.tsx`
- 506 rotas de API em `/src/app/api/`
- Estrutura top-level: `app/`, `components/`, `stores/`, `hooks/`, `lib/`, `services/`, `contexts/`, `types/`, `utils/`

**Achados**

#### ALTO — Dual Chat System Coexistente
**Severidade:** Alto
**Arquivos:**
- `src/components/pages/chat-page.tsx` (727 linhas) — contém `ChatPage` (wrapper) E `LegacyChatPage` (implementação completa com 80+ imports)
- `src/components/unified-chat/UnifiedChat.tsx` (352 linhas) — sistema novo
- `src/components/pages/chat-page/` — diretório com implementação paralela (`useChatPageCore.tsx`, `useChatPageHandlers.tsx`, etc.)
- `src/components/unified-chat/ChatPageFullscreen` — terceiro entry point

**Impacto:** `ChatPage` hoje é apenas `return <ChatPageFullscreen />`, mas `LegacyChatPage` permanece no mesmo arquivo com 700+ linhas de dead code ativo. Duas implementações completas de mensagens, hooks de streaming e HITL coexistem. Qualquer bug fix pode ser aplicado no lugar errado.

**Fix:** Remover `LegacyChatPage` e todo o código legado do `chat-page.tsx`. Manter apenas o re-export para `ChatPageFullscreen`. Limpeza estimada: ~650 linhas.

#### MÉDIO — ChatContextPanel Fragmentado em 3 Arquivos sem Justificativa
**Severidade:** Médio
**Arquivos:**
- `src/components/chat/ChatContextPanel.tsx`
- `src/components/chat/ChatContextPanelPart1.tsx`
- `src/components/chat/ChatContextPanelPart2.tsx`
- `src/components/chat/ChatContextPanelPart3.tsx`

**Impacto:** Refatoração mecânica que cria 3 ficheiros sem abstração semântica (Part1, Part2, Part3). Dificulta navegação e compreensão.

**Fix:** Consolidar em sub-componentes com nomes descritivos (`CandidateContextHeader`, `CandidateMetadata`, `PipelineActions`) ou usar seções dentro de um único arquivo.

#### MÉDIO — Convenção de Nomenclatura Inconsistente
**Arquivos:**
- `src/components/pages/chat-page/` — pasta kebab-case
- `src/components/pages-agent-studio/` — pasta com hífen inconsistente
- `src/components/pages-talent-pools/` — idem
- Mistura de `PascalCase.tsx` e `kebab-case.tsx` dentro de `/components/`

**Impacto:** Descoberta de arquivos prejudicada. IDEs com file-system sensitive podem quebrar imports em Linux.

**Fix:** Padronizar: pastas em `kebab-case`, componentes em `PascalCase.tsx`.

#### BAIXO — Sem Dead Code Detection Automatizado
**Impacto:** Com 1.037 arquivos TSX e sistema legado visível (`LegacyChatPage`), não há evidência de ferramentas como `ts-prune` ou `knip` no pipeline CI.

**Fix:** Adicionar `knip` ou `ts-prune` ao script de lint.

**Score D1: 68/100**

---

### Rails Backend

**Inventário**
- **160 arquivos Ruby** organizados em: controllers, models, services, serializers, workers, jobs, channels, concerns
- **Estrutura de pastas:** `app/controllers/v1/users/` + `v1/auth/` — bem namespaceado para API versionada
- **85 migrações** com schema em 217 linhas — tamanho coerente
- **Models:** 80+ models — rico domínio de negócio (consent, audit_log, LGPD, ATS completo)

**Achados**

#### [Médio] Rota de usuários não-RESTful
**Arquivo:** `config/routes.rb:45-51`
**Detalhe:** As rotas de usuários usam paths customizados (`GET search`, `POST create`, `PUT edit/:id`, `DELETE delete/:id`) em vez do helper `resources :users`. Inconsistente com o padrão REST adotado para todos os outros recursos.
**Fix:** Substituir por `resources :users, path: ''`.

#### [Médio] Dead code: `OnboardingEventPublisher` nunca chamado
**Arquivo:** `app/services/onboarding_event_publisher.rb`
**Detalhe:** A classe `OnboardingEventPublisher` existe com interface própria (`ROUTING_KEY = "onboarding_events"`) mas **nunca é instanciada no código**. Todos os controllers chamam `MessageService::EventPublisher.publish` diretamente. Código morto que confunde manutenção.
**Fix:** Eliminar `onboarding_event_publisher.rb` ou consolidar como o publisher padrão.

#### [Baixo] Pasta `app/lib/` não-convencional
**Arquivo:** `app/lib/json_web_token.rb`
**Detalhe:** Convenção Rails coloca utilitários em `lib/` (raiz), não `app/lib/`. Além disso, o módulo `JsonWebToken` duplica lógica JWT que já existe em 3 lugares.
**Fix:** Mover para `app/lib/` é aceitável em Rails 7+, mas consolidar a lógica JWT primeiro.

#### [Baixo] Schema.rb com version 2025_07_14 (data futura relativa ao projeto)
**Arquivo:** `db/schema.rb:13`
**Detalhe:** `version: 2025_07_14_142059` — migrações criadas com datas futuras (provavelmente geradas por scripts batch). Não afeta runtime mas dificulta rastreio de ordem cronológica real.

**Score Domínio 1: 72/100** — Estrutura sólida, namespacing correto, concerns bem definidos. Penalização por rotas inconsistentes e dead code.

---

## D2 — Qualidade de Código AI

### Python AI Layer

**Métricas**
- Prompts inline (`system_prompt = """` ou f-string): **19+ ocorrências**
- YAML de prompts externos: **20 arquivos** em `app/prompts/domains/`
- Model strings hardcoded: **12 ocorrências** (fora de settings)
- Temperature hardcoded: **15+ ocorrências** (esperadas — maioria justificadas)
- Token tracking: **presente** (`TenantBudget`, `increment_usage`, `usage_metadata`)
- Streaming: **suportado** (SSE + WS)
- Structured output: **manual JSON parsing** (sem `with_structured_output`)
- Error handling LLM: **genérico** — `except Exception` em 4 locais no provider Claude

**Achados**

#### [ALTO] D2-01 — Model Strings Hardcoded Fora do Settings
**Arquivos:**
- `app/api/v1/wsi/evaluation.py:350` — `model="claude-sonnet-4-6"` direto
- `app/api/v1/wsi/questions.py:198` — `model="claude-sonnet-4-6"` direto
- `app/api/v1/lia_assistant/wizard.py:460` — `model="gemini-2.5-flash"` direto
- `app/api/v1/rubric_evaluation.py:187, 224, 325, 336` — 4 ocorrências
- `app/api/v1/llm_config.py:257, 264, 274` — fallbacks hardcoded
- `app/services/studio_metering_service.py:40` — `"gemini-1.5-flash"` default

**Nota positiva:** `app/core/agent_model_config.py:14` define `DEFAULT_MODEL = os.getenv("CLAUDE_DEFAULT_MODEL", "claude-sonnet-4-6")` — o padrão existe, mas não é usado de forma consistente.

**Impact:** Troca de modelo (ex: migração para Claude 4 ou Gemini 2.5 Pro) requer grep manual de 12+ arquivos. Risco de inconsistência entre agents.

**Fix:** Centralizar em `agent_model_config.py`. Todos os `model=` devem referenciar `DEFAULT_MODEL`, `DEFAULT_GEMINI_MODEL`, etc. Validar via linter customizado ou test.

---

#### [ALTO] D2-02 — LLM Error Handling Genérico no Provider Principal
**Arquivo:** `app/shared/providers/llm_claude.py:77, 107, 150, 179`

O provider Claude captura `except Exception` sem distinguir:
- `anthropic.RateLimitError` (429) → deveria aplicar backoff exponencial antes de repassar
- `anthropic.APITimeoutError` → deveria ter retry policy diferente
- `anthropic.AuthenticationError` → deveria alertar ops imediatamente
- `anthropic.OverloadedError` → deveria redirecionar para cascade LLM

O circuit breaker (`ANTHROPIC_CIRCUIT`) está presente e é positivo. Mas a ausência de tratamento granular de erros significa que rate limits e timeouts são tratados identicamente — o circuit pode abrir prematuramente por timeouts transitórios.

**Fix:** Adicionar `from anthropic import RateLimitError, APITimeoutError, OverloadedError`. Tratar cada tipo com estratégia de retry/escalation distinta antes de propagar ao circuit breaker.

---

#### [ALTO] D2-03 — Structured Output via Parse Manual (sem `with_structured_output`)
**Arquivos:**
- `app/api/v1/wsi/_shared.py:264` — `parse_json_response()` custom
- `app/domains/job_management/services/jd_generator_service.py:162` — `_parse_json_response()` custom
- `app/domains/recruiter_assistant/services/jobs_management_assistant_service.py:95` — custom
- `app/domains/ai/services/structured_output.py:269` — `parse_json_from_text()` custom

Ao menos **4 implementações distintas** de parser JSON de LLM output. Nenhuma usa `with_structured_output` do LangChain ou `response_format={"type": "json_object"}` da Anthropic.

**Impact:** Qualquer mudança no formato de output do LLM quebra parsers silenciosamente. Sem schema validation, erros chegam ao usuário como dados parciais. Manutenção em 4 lugares.

**Fix:** Unificar em `app/domains/ai/services/structured_output.py`. Adotar Pydantic schemas + `llm.with_structured_output(MyModel)` onde o modelo suporta. Para Anthropic direto, usar `response_format={"type": "json_object"}` com `pydantic.TypeAdapter`.

---

#### [MÉDIO] D2-04 — Prompts Inline (19 ocorrências) vs YAML Registry (20 arquivos)
**Exemplos de prompts inline:**
- `app/api/v1/lia_assistant/_shared.py:1047, 1083, 1117` — 3 system prompts embutidos em funções
- `app/domains/cv_screening/services/wsi_question_adjuster.py:65` — prompt f-string em service
- `app/api/v1/lia_assistant/wizard.py:209` — prompt f-string em route handler

**Contexto positivo:** Existe `app/prompts/domains/` com 20 YAMLs e um registry bem estruturado. O problema é que 19+ prompts "escaparam" do registry e ficaram inline.

**Fix:** Migrar prompts inline para YAMLs correspondentes. Adicionar teste de cobertura: `assert all prompts use PromptVersionRegistry`.

---

**Score D2: 70/100**

---

### Next.js Frontend

**Achados**

#### ALTO — `backgroundTasks` em Estado Local, Não em Store Global
**Severidade:** Alto
**Arquivo:** `src/hooks/chat/useChatSocket.ts` (linhas 76-77)

`backgroundTasks` é gerenciado via `useState` dentro de `useChatSocket` e exposto no return object. Quando o componente remonta (troca de rota, modo chat), todas as tarefas de background são perdidas. Outras partes da UI que precisam do estado de tasks (notificações, navbar) não têm acesso sem prop drilling.

**Fix:** Mover `backgroundTasks` para `chat-state-store.ts` (já existe em `/src/stores/chat-state-store.ts`).

#### MÉDIO — Casting `as unknown as Record<string, unknown>` Frequente em useChatSocket
**Severidade:** Médio
**Arquivo:** `src/hooks/chat/useChatSocket.ts` (linhas 104, 140, 148, 161)

O tipo `StreamingEvent` tem `[key: string]: unknown` index signature, então os casts são evitáveis. Indica que o tipo do evento não é preciso o suficiente.

**Fix:** Criar discriminated union types para cada `event.type` (ex: `PlanProgressEvent`, `BackgroundTaskUpdateEvent`, `PanelUpdateEvent`) usando `StreamingEventType` já definido.

#### MÉDIO — Re-conexão WS Tem Race Condition Potencial
**Severidade:** Médio
**Arquivo:** `src/hooks/chat/useChatSocket.ts` (linhas ~220-225)

O `setTimeout(() => connect(), 50)` com delay hardcoded é frágil. Se o `disconnect()` demorar mais de 50ms (ex: rede lenta), o `connect()` pode tentar abrir nova WS enquanto a anterior ainda fecha.

**Fix:** Usar `useCallback` com lógica de `wsRef.current?.readyState === WebSocket.CLOSED` antes de reconectar, ou usar `useEffect` cleanup adequadamente.

#### MÉDIO — Token de WS Buscado via `fetch` Client-Side (Sem Cache)
**Severidade:** Médio
**Arquivo:** `src/hooks/chat/useChatSocket.ts` (linhas 83-90)

Toda vez que `useChatSocket` monta, faz um fetch para `/api/auth/ws-token`. Em páginas com múltiplos componentes usando chat (ex: KanbanSuperChatSection, LIASearchSidebarChat, InlineChatPanel), isso multiplica as requisições.

**Fix:** Mover o token WS para o `auth-store` com TTL, ou usar `SWR` com `dedupingInterval`.

#### BAIXO — `thinkingSteps` Cresce Indefinidamente
**Arquivo:** `src/hooks/chat/useChatSocket.ts`

Array cresce a cada mensagem sem limpeza no `token_done`/`message` event.

**Fix:** Resetar `thinkingSteps` quando `case "message"` é recebido.

**Score D2: 72/100**

---

### Rails Backend

**Como Rails interage com Python/FastAPI**

O Rails NÃO faz chamadas HTTP diretas ao Python. A integração é exclusivamente via **RabbitMQ** (gem `bunny`), o que é uma escolha arquitetural correta para desacoplamento.

**Achados**

#### [CRÍTICO] RabbitMQ: nova conexão TCP por mensagem publicada
**Arquivos:**
- `app/services/message_service/event_publisher.rb:3-18`
- `app/services/onboarding_event_publisher.rb:14-33`
- `app/controllers/v1/users/onboarding_controller.rb:182`
- `app/controllers/v1/auth/magic_links_controller.rb:46`

**Detalhe:** Cada chamada a `MessageService::EventPublisher.publish` abre uma conexão TCP nova com o RabbitMQ (`Bunny.new(...).start`), cria um canal, publica, fecha o canal, fecha a conexão. Isso é **extremamente custoso**: latência de 50-200ms por publish, esgota file descriptors sob carga, e falha silenciosamente sob pico. Em `magic_links_controller`, isso acontece **dentro de um request HTTP síncrono**.

**Impacto:** Under load, magic link verify pode timeout. Um burst de invites simultâneos pode derrubar o RabbitMQ connection pool.

**Fix imediato:**
```ruby
# config/initializers/rabbitmq.rb
RABBITMQ_CONNECTION = Bunny.new(ENV["RABBITMQ_URL"]).tap(&:start)

# MessageService::EventPublisher
def self.publish(payload)
  channel = RABBITMQ_CONNECTION.create_channel
  exchange = channel.direct("messages_exchange", durable: true)
  exchange.publish(payload.to_json, routing_key: "messages_created", persistent: true)
  channel.close
end
```
**Fix ideal:** Mover todo publish de eventos para Sidekiq job (assíncrono, fora do request lifecycle).

#### [Alto] Método `publish_onboarding_event` duplicado em 2 controllers
**Arquivos:**
- `app/controllers/v1/auth/magic_links_controller.rb:45-53`
- `app/controllers/v1/users/onboarding_controller.rb:181-189`

**Detalhe:** Código idêntico copiado. Violação de DRY crítica — se a interface do publisher mudar, há 2 lugares para atualizar.
**Fix:** Extrair para `app/controllers/concerns/onboarding_publishable.rb`.

#### [Alto] Publish síncrono dentro de request HTTP (magic link verify)
**Arquivo:** `app/controllers/v1/auth/magic_links_controller.rb:27-31`
**Detalhe:** O `verify` da magic link publica um evento RabbitMQ **antes** de retornar o JWT para o frontend. Se o RabbitMQ estiver lento/indisponível, o login do usuário trava.
**Fix:** Envolver em `PublishOnboardingEventJob.perform_later(...)`.

#### [Médio] ActionCable broadcast diretamente no model
**Arquivo:** `app/models/recruitment_campaign.rb:85-89`
**Detalhe:** Models não devem ter dependência de infraestrutura de transport (ActionCable). Viola Single Responsibility Principle. Dificulta testes unitários do model.
**Fix:** Mover para callback no controller ou job.

**Score Domínio 2: 45/100** — O padrão RabbitMQ é correto arquiteturalmente, mas a implementação é naive e perigosa em produção.

---

## D3 — Padrões de Integração

### Python AI Layer

**Métricas**
- `httpx.AsyncClient` (raw HTTP): **14 ocorrências em prod** (excluindo testes)
- SDK Anthropic oficial (`import anthropic`): usado em 4 arquivos ✓
- SDK Google genai: usado em 1 arquivo (import lazy) ✓
- API keys hardcoded: **0** (apenas em testes com valores de teste) ✓
- Rate limiting: `app/middleware/rate_limiter.py` presente ✓
- Circuit breakers: `app/shared/resilience/circuit_breaker.py` (1060 linhas) ✓

**Achados**

#### [ALTO] D3-01 — httpx.AsyncClient Sem Pool (Objetos Temporários em Hot Paths)
**Arquivos:**
- `app/services/whatsapp_client.py:50, 82, 126, 187` — 4 clientes criados/destruídos por request
- `app/api/v1/teams.py:1428, 1445` — clientes temporários em chamadas MS Teams
- `app/api/v1/company.py:853` — cliente temporário para integração externa
- `app/services/onboarding_orchestrator.py:608` — cliente temporário em orchestration

`async with httpx.AsyncClient()` cria uma nova connection pool por request. Em paths de alta frequência (WhatsApp, Teams), isso resulta em TCP handshakes repetidos e pressão no file descriptor limit.

**Fix:** Criar `app/shared/http/client_pool.py` com um singleton `httpx.AsyncClient` por serviço externo (configurado com `limits`, `timeout` e `keepalive`). Injetar via FastAPI lifespan.

---

#### [MÉDIO] D3-02 — Ausência de Retry Policy Uniforme para HTTP Externo
**Arquivo:** `app/services/whatsapp_client.py`, `app/api/v1/ats.py:235`

Chamadas HTTP externas (WhatsApp API, ATS, etc.) não têm `tenacity` ou `httpx` transport com retry. O circuit breaker cobre LLM calls mas não HTTP genérico. Um 503 transiente da Meta/WhatsApp falha imediatamente.

**Fix:** Adicionar `httpx_retries` ou `tenacity.retry` decorator para HTTP externo com backoff exponencial (3 tentativas, jitter). Usar o mesmo `CircuitBreaker` pattern já existente.

---

#### [BAIXO] D3-03 — Import Lazy do SDK Google (`google.generativeai`)
**Arquivo:** `app/domains/talent_intelligence/services/skills_ontology_engine.py:535`

`import google.generativeai as genai` é feito dentro de um bloco `if` em runtime. Dificulta type checking e torna erros de configuração silenciosos até o momento de uso.

---

**Score D3: 78/100**

---

### Next.js Frontend

**Achados**

#### ALTO — 506 Rotas de API com Padrões Heterogêneos de Auth
**Severidade:** Alto

Existem **3 padrões diferentes** de proxy coexistindo:

**Padrão A — `createProxyHandlers()` (correto, padronizado):**
```typescript
// activities/route.ts, candidates/route.ts
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/activities",
  auth: true, // default
})
```
Auth via `getAuthHeaders()` centralizado. OK.

**Padrão B — `proxyFetchWithRetry()` (correto, com retry):**
```typescript
// chat/route.ts
const response = await proxyFetchWithRetry(request, '/api/v1/chat', {...})
```
Auth via `getAuthHeaders()` interno. OK, mas inconsistente.

**Padrão C — Manual ad-hoc (problemático):**
```typescript
// candidates/bulk/update-status/route.ts
...(request.headers.get('Authorization') ? { 'Authorization': request.headers.get('Authorization')! } : {}),
```
Lógica de auth duplicada, sem fallback para cookie `lia_access_token` ou sessão WorkOS. Se o header não vier, a chamada vai sem auth.

**Arquivos com Padrão C (risco):**
- `candidates/bulk/update-status/route.ts`
- `candidates/bulk/assign-job/route.ts`
- `candidates/bulk/send-email/route.ts`
- `candidates/bulk/start-screening/route.ts`
- `candidates/bulk/delete/route.ts`

**Fix:** Migrar todos os Padrão C para `createProxyHandlers()` ou `proxyFetchWithRetry()`.

#### MÉDIO — `BACKEND_URL` com Fallback Hardcoded em 30+ Arquivos
**Severidade:** Médio
**Padrão encontrado em 30+ arquivos:**
```typescript
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'
```

**Fix:** Centralizar em `src/lib/config.ts`:
```typescript
export const BACKEND_URL = process.env.BACKEND_URL ?? 'http://127.0.0.1:8001'
```

#### MÉDIO — `NEXT_PUBLIC_API_URL` Indefinido em `.env.example`
**Severidade:** Médio
**Arquivo:** `src/hooks/chat/useChatTransport.ts` (linha ~13)
`NEXT_PUBLIC_API_URL` não está definido em `.env.example`. Em produção, `window.location.origin` pode diferir do backend real.

**Fix:** Adicionar `NEXT_PUBLIC_API_URL` ao `.env.example` e documentar quando usar vs `NEXT_PUBLIC_WS_URL`.

#### BAIXO — Timeout Fixo em Proxy (15s) sem Configuração por Rota
Rotas de análise de candidatos ou bulk operations podem legitimamente demorar mais. Rotas simples deveriam ter timeout menor.

**Fix:** Adicionar `timeoutMs?: number` ao `ProxyConfig`.

**Score D3: 75/100**

---

### Rails Backend

**Achados**

#### [CRÍTICO] CORS hardcoded para `localhost:3000` em produção
**Arquivo:** `config/initializers/cors.rb:3`
```ruby
origins 'http://localhost:3000'
```
**Detalhe:** A única configuração CORS aceita é `localhost:3000`. Isso significa que em **produção**, todas as requisições cross-origin do frontend real (ex: `app.wedotalent.com`) serão bloqueadas. O arquivo de produção (`production.rb`) tem `allowed_request_origins` comentado. A API está essencialmente inacessível para qualquer frontend de produção real.

**Fix:**
```ruby
origins Rails.env.production? ? ENV.fetch("FRONTEND_URL") : 'http://localhost:3000'
```

#### [Alto] Sem rate limiting no endpoint de login e magic link
**Arquivo:** `config/routes.rb`, `app/controllers/v1/sessions_controller.rb`, `app/controllers/v1/auth/magic_links_controller.rb`
**Detalhe:** A gem `rack-attack` **não está instalada** (ausente do Gemfile). Os endpoints `/v1/sessions` (login) e `/v1/auth/magic-link/verify` não têm throttling. Exposição a brute-force e credential stuffing. Existe uma tabela `rate_limit_rules` no banco mas ela **não está conectada a nenhum middleware**.

**Fix:** Adicionar `gem 'rack-attack'` + initializer com throttle de 5 req/minuto para login por IP.

#### [Alto] Sem secrets via `Rails.application.credentials` — tudo via ENV raw
**Arquivos:** `app/services/message_service/event_publisher.rb:4`, `app/services/onboarding_event_publisher.rb:14`, `app/controllers/v1/users/onboarding_controller.rb:55`
**Detalhe:** `ENV["RABBITMQ_URL"]`, `ENV["LIA_WHATSAPP_NUMBER"]` — acesso direto sem fallback ou validação. Se a var não existir em produção, `Bunny.new(nil)` lança exceção não tratada. Não há uso de `Rails.application.credentials` em lugar algum.

**Fix:** Encapsular em módulo de config com validação na inicialização:
```ruby
raise "RABBITMQ_URL não configurado" if ENV["RABBITMQ_URL"].blank? && Rails.env.production?
```

#### [Médio] Sem idempotência em `Apply.find_or_create_by!` sob condição de corrida
**Arquivo:** `app/controllers/v1/users/talent_pools_controller.rb:102-106`
**Detalhe:** `find_or_create_by!` não é atômico sem índice único no banco. Duas requisições simultâneas podem criar applies duplicados.
**Fix:** Adicionar migration com `add_index :applies, [:candidate_id, :job_id, :selective_process_id], unique: true`.

#### [Médio] ActionCable sem autenticação configurada para produção
**Arquivo:** `config/environments/production.rb:45` (comentado)
**Detalhe:** `config.action_cable.allowed_request_origins` está comentado em produção. O canal WebSocket aceita conexões de qualquer origem.

**Score Domínio 3: 55/100** — RabbitMQ como transport é correto; execução (CORS, rate limit, idempotência) é deficiente.

---

## D4 — Persistência & Dados

### Python AI Layer

**Métricas**
- Migrações Alembic: **76** ✓
- Arquivos com soft delete (`is_deleted`, `deleted_at`): **41** ✓
- Index declarations: bem cobertos em `auth/models.py`, `auth/workos_models.py` ✓
- Raw SQL via `text()` com f-string: **10+ ocorrências**
- Transações (`rollback()`): presentes em `candidate_lists.py`, `compliance_controls.py`, etc. ✓

**Achados**

#### [ALTO] D4-01 — Raw SQL com f-string em Tool Registries de Agents
**Arquivos:**
- `app/domains/sourcing/agents/sourcing_tool_registry.py:133` — `f"SELECT COUNT(*) as total FROM candidates WHERE {where_clause}"`
- `app/domains/sourcing/agents/diversity_tool_registry.py:153` — idem
- `app/domains/sourcing/agents/passive_pipeline_tool_registry.py:99` — idem
- `app/domains/pipeline/agents/pipeline_tool_registry.py:187` — `text(f"UPDATE candidates SET {field_name} = :val...")`
- `app/domains/hiring_policy/agents/policy_tool_registry.py:112` — `text(f"SELECT id, {block} FROM company_hiring_policies...")`

**Análise de risco:** `where_clause` é construído via `" AND ".join(conditions)` onde `conditions` são strings literais adicionadas condicionalmente — os valores usam bind params (`:role_pattern`), então o risco de SQL injection clássico é **baixo**. No entanto, o padrão é frágil: um refactor que passa `where_clause` de input externo cria vulnerabilidade. O `field_name` em `pipeline_tool_registry.py:187` e `block` em `policy_tool_registry.py:112` merecem auditoria adicional (não foram confirmados como whitelisted).

**Impact:** Fragilidade estrutural. Não é SQLAlchemy ORM — ausência de type safety, sem composição de queries, sem eager loading.

**Fix:** Substituir raw SQL em tool registries por SQLAlchemy `select()` statements com `filter()` dinâmico. Para `hiring_policy` e `pipeline`, confirmar whitelist de `block` e `field_name` ou converter para ORM.

---

#### [ALTO] D4-02 — policy_engine.py usa psycopg2 Síncrono Paralelo ao asyncpg
**Arquivo:** `app/orchestrator/policy_engine.py:106-128`

`_get_db_connection()` usa uma connection psycopg2 síncrona (não a pool asyncpg da aplicação). Isso cria uma segunda connection pool síncrona, fora do lifecycle do FastAPI, sem circuit breaker, sem pool management.

**Impact:** Conexões órfãs sob carga, incompatibilidade com o event loop async, comportamento imprevisível em failover.

**Fix:** Substituir por `AsyncSessionLocal` (já usado em todo o resto da aplicação). A lógica de `_get_daily_usage` deve ser `async`.

---

#### [MÉDIO] D4-03 — `text(f"""...""")` em audit_timeline para query dinâmica de filtros
**Arquivo:** `app/api/v1/audit_timeline.py:185-196`

Query construída com `where_sql = " AND ".join(where_clauses)` inserida em `text(f"""SELECT * FROM ... WHERE {where_sql}""")`. O padrão `SELECT *` sem projeção explícita é um smell.

**Fix:** Projetar colunas explicitamente. Usar `sqlalchemy.select(AuditModel).where()` com filtros compostos.

---

**Score D4: 72/100**

---

### Next.js Frontend

**Achados**

#### ALTO — Estado Chat Fragmentado Entre Store e Hook Local
**Severidade:** Alto

Existe `src/stores/chat-state-store.ts` mas o hook `useChatSocket` mantém estado crítico localmente:
- `hitlPending` — estado local (deveria ser global: HITL pode afetar navbar, notificações)
- `backgroundTasks` — estado local (idem)
- `planProgressSteps` — estado local
- `conversationIdFromWs` — estado local

O store `chat-state-store.ts` existe mas aparentemente não é usado para esses estados críticos.

**Impacto:** Múltiplas instâncias de chat (float + inline + fullscreen) podem ter estados HITL desincronizados.

**Fix:** Consolidar `hitlPending`, `backgroundTasks`, `planProgressSteps` em `chat-state-store.ts`. Usar apenas o store como fonte de verdade.

#### MÉDIO — 14+ Stores com `persist()`, Sem Estratégia de Versioning
**Severidade:** Médio
**Stores com persist:** `onboarding-store`, `job-ui-store`, `job-filters-store`, `talent-funnel-store`, `wizard-store`, `template-store`, `triagem-store`, `recent-items-store`, `table-features-store`, `navigation-store`, `ui-preferences-store`

Sem evidência de `version` ou `migrate` nas configurações de `persist()`. Mudanças no shape dos dados quebram o localStorage sem migração silenciosa.

**Fix:**
```typescript
persist(set => ({ ... }), {
  name: 'job-filters-store',
  version: 2,
  migrate: (persisted, version) => { ... }
})
```

#### MÉDIO — `useState` Extensivo em Componentes Grandes
**Severidade:** Médio
**Componentes afetados:**
- `sidebar.tsx` (1.071 linhas) — múltiplos `useState`
- `pipeline-overview-page.tsx` (967 linhas) — idem
- `AgentStudioPage.tsx` (962 linhas) — idem

Estado de UI que deveria estar em stores (ex: filtros de pipeline, configurações de visualização) permanece local, impedindo persistência e deep-linking.

**Fix:** Extrair estado relevante para stores existentes (`job-ui-store`, `job-filters-store`).

#### BAIXO — `localStorage` Acessado Diretamente em Componentes
**Arquivo:** `src/components/unified-chat/UnifiedChat.tsx` (linhas 25-41)

Acesso direto ao `localStorage` sem abstração. Zustand `persist` com `storage: createJSONStorage(() => localStorage)` é o padrão correto aqui.

**Fix:** Mover `mode` e `sidebarWidthPx` para `ui-preferences-store` com persist.

**Score D4: 70/100**

---

### Rails Backend

**Achados**

#### [CRÍTICO] `candidates` table sem `account_id` — dados cross-tenant acessíveis
**Arquivo:** `db/schema.rb` (tabela `candidates`)
**Detalhe:** A tabela `candidates` **não possui coluna `account_id`**. Ao contrário de `jobs` e `messages` que têm `account_id` indexado, candidatos são globais no banco. Isso significa que um recruiter da Empresa A pode acessar candidatos cadastrados pela Empresa B via `GET /v1/users/candidates`. O `CandidatesController` usa `ResourceLoader` que faz `Candidate.find_by(id: params[:id])` **sem qualquer filtro de tenant**.

**Impacto:** CRÍTICO — vazamento de dados pessoais (CPF, data de nascimento, salário, etc.) entre tenants. Violação direta da LGPD.

**Fix:** Migration para adicionar `account_id` à tabela `candidates` + backfill + atualizar `TenantScoped`.

#### [Alto] N+1 em `add_candidates` — loop + query por iteração
**Arquivo:** `app/controllers/v1/users/talent_pools_controller.rb:67-75`
**Detalhe:** Para cada `candidate_id` no array, dispara 1 SELECT + possivelmente 1 INSERT. Para um bulk de 100 candidatos = 200 queries.

**Fix:**
```ruby
existing_ids = @talent_pool.talent_pool_candidates.pluck(:candidate_id)
new_ids = candidate_ids.map(&:to_i) - existing_ids
TalentPoolCandidate.insert_all(new_ids.map { |id| { talent_pool_id: @talent_pool.id, candidate_id: id, origin: origin, stage: "discovered" } })
```

#### [Alto] N+1 similar em `move_to_job`
**Arquivo:** `app/controllers/v1/users/talent_pools_controller.rb:90-110`
**Detalhe:** Loop sobre `candidate_ids` com `find_by` + `move_to_job!` + `Apply.find_or_create_by!` por iteração. 3 queries por candidato.
**Fix:** Carregar todos os `talent_pool_candidates` de uma vez antes do loop.

#### [Alto] `SchemaCloneService` executa SQL raw com interpolação de string sem sanitização total
**Arquivo:** `app/services/schema_clone_service.rb:83-87`
```ruby
drop_cmd = "DROP SCHEMA IF EXISTS \"#{target_schema}\" CASCADE;"
ActiveRecord::Base.connection.execute(drop_cmd)
```
**Detalhe:** `target_schema` vem de `account.staging_tenant`. Embora haja validação `end_with?("_staging")`, a string não é sanitizada pelo ActiveRecord. Um nome de schema com aspas duplas poderia injetar SQL.
**Fix:** Usar `ActiveRecord::Base.connection.quote_table_name(target_schema)` ou parametrizar.

#### [Médio] Sem transações nas operações compostas de onboarding
**Arquivo:** `app/controllers/v1/users/onboarding_controller.rb:14-79`
**Detalhe:** O `invite` cria `User`, `MagicLink`, `OnboardingSession` e envia email em sequência sem `ApplicationRecord.transaction`. Se `OnboardingSession.create!` falhar após `user.save!`, o usuário existe no banco sem sessão.
**Fix:** Envolver em `ApplicationRecord.transaction do ... end`.

#### [Médio] Schema 217 linhas para 85 migrações — schema incompleto
**Arquivo:** `db/schema.rb`
**Detalhe:** Com 80+ models mas apenas os models mais simples no schema, a maioria dos models complexos (audit_log, consent_record, ai_consumption, etc.) não aparece no schema. Isso sugere que o `schema.rb` pode não refletir o estado real do banco em produção.

**Score Domínio 4: 60/100** — Indexação razoável (412 indexes nas migrations), mas o gap de `account_id` em candidates é uma falha de design grave.

---

## D5 — Segurança

### Python AI Layer

**Métricas**
- Arquivos de API com Pydantic validation: **192** (cobertura excelente) ✓
- API keys hardcoded: **0** em produção ✓
- Secrets manager: `app/core/secrets_provider.py` (Doppler) ✓
- CORS: configurado via `settings.CORS_ORIGINS` (não wildcard hardcoded) ✓
- Circuit breaker LLM: **presente** (`app/shared/resilience/circuit_breaker.py`) ✓
- Prompt injection guard: presente em 10 arquivos (sanitize) ✓
- OPENMIC webhook: HMAC-SHA256 validado, raise em produção se bypass ativo ✓

**Achados**

#### [CRÍTICO] D5-01 — `LIA_DISABLE_C3B=1` Bypassa Camada de Compliance Inteira
**Arquivo:** `app/shared/compliance/c3b_layer.py:7, 15, 55, 102`

```python
_C3B_DISABLED = os.environ.get("LIA_DISABLE_C3B", "0") == "1"
# ...
if _C3B_DISABLED:
    return  # passthrough — sem bias check, sem fairness guard
```

C3B é a camada de fairness/compliance que bloqueia respostas com bias. Uma variável de ambiente não auditada desabilita completamente esse controle em todos os tenants simultaneamente.

**Impact:** Se um atacante ou operador mal-intencionado ativar `LIA_DISABLE_C3B=1` em produção, toda a proteção anti-bias cai sem log de auditoria. Risco de LGPD/GDPR e reputacional para plataforma B2B de RH.

**Fix:**
1. Remover o bypass ou convertê-lo em feature flag por-tenant com auditoria obrigatória.
2. Se necessário para testes, exigir que só funcione em `APP_ENV=development`.
3. Adicionar log de auditoria imutável quando o bypass é ativado.
4. Alertar via Sentry quando `_C3B_DISABLED=True` em qualquer ambiente não-local.

---

#### [ALTO] D5-02 — `allow_methods=["*"]` e `allow_headers=["*"]` no CORS
**Arquivo:** `app/main.py:388-389`

```python
allow_methods=["*"],
allow_headers=["*"],
```

Junto com `allow_credentials=True`, esse padrão permite qualquer origem enviar qualquer header com cookies. O valor real de `CORS_ORIGINS` não foi confirmado.

**Fix:** Especificar `allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]` e `allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Tenant-ID"]`. Confirmar que `CORS_ORIGINS` nunca é `*` em produção.

---

#### [ALTO] D5-03 — Falha Silenciosa na Política de Segurança (fail-open)
**Arquivo:** `app/orchestrator/policy_engine.py:98-103`

```python
except Exception as e:
    logger.error(f"❌ Policy validation failed: {e}")
    # Fail-safe: allow on error but log
    return {"allowed": True, ...}
```

Qualquer exceção no policy engine (incluindo erros de DB) resulta em `allowed: True`. Em sistemas de RH com regras de compliance, um erro de DB permite acesso irrestrito.

**Fix:** Para regras de compliance/billing, fail-closed (`allowed: False`) com mensagem de erro genérica para o usuário. Fail-open só é aceitável para regras de experiência (ex: sugestões de UI).

---

#### [MÉDIO] D5-04 — Logger expõe detalhes de exceção em produção
**Arquivo:** `app/main.py:468-471` (handler global de exceções)

O handler global retorna `"Internal server error"` para o cliente (correto), mas `logger.error(f"Unhandled exception: {exc}")` pode incluir stack traces com dados de candidatos se o `exc` contiver objetos de domínio em seu `__str__`.

**Fix:** Adicionar `extra={"sensitive": True}` e configurar filtro de log para mascarar emails/CPFs em mensagens de erro.

---

**Score D5: 75/100**

---

### Next.js Frontend

**Achados**

#### CRITICO — DEV_AUTO_LOGIN Habilitado por Padrão em Não-Produção
**Severidade:** Crítico
**Arquivo:** `src/middleware.ts` (linha 10)

```typescript
const DEV_AUTO_LOGIN = process.env.NODE_ENV !== 'production'
```

Em staging e qualquer ambiente não-`production`, qualquer usuário pode acessar a plataforma sem credenciais. O middleware faz auto-login com credenciais padrão (`demo@wedotalent.com` / `demo123`).

**Impacto:** Se staging for acessível publicamente (comum em Replit), qualquer pessoa tem acesso completo à plataforma com conta demo.

**Fix:**
```typescript
const DEV_AUTO_LOGIN = process.env.DEV_AUTO_LOGIN === 'true'
```
Exigir opt-in explícito via variável de ambiente, não opt-out.

#### ALTO — `dangerouslySetInnerHTML` em Layout Principal Sem Sanitização
**Severidade:** Alto
**Arquivo:** `src/app/[locale]/layout.tsx` (linhas 120, 126)

Dois usos de `dangerouslySetInnerHTML` no layout raiz da aplicação, sem evidência de `sanitizeHtml()` neste contexto (ao contrário dos modais, que usam `sanitizeHtml`).

**Impacto:** XSS persistente se qualquer dado dinâmico atingir esse ponto.

**Fix:** Auditar o que é inserido no layout. Se for conteúdo estático (scripts analytics), usar `<Script>` do Next.js. Se dinâmico, adicionar `DOMPurify`.

#### ALTO — Ausência de Content-Security-Policy
**Severidade:** Alto
**Arquivo:** `next.config.js`

Headers configurados:
- `Cache-Control` — presente
- `X-Frame-Options` — **ausente**
- `Content-Security-Policy` — **ausente**
- `X-Content-Type-Options` — **ausente**
- `Strict-Transport-Security` — **ausente**
- `Referrer-Policy` — **ausente**

**Fix:** Adicionar ao `next.config.js`:
```javascript
{
  key: 'X-Frame-Options',
  value: 'SAMEORIGIN',
},
{
  key: 'X-Content-Type-Options',
  value: 'nosniff',
},
{
  key: 'Referrer-Policy',
  value: 'strict-origin-when-cross-origin',
},
{
  key: 'Content-Security-Policy',
  value: "default-src 'self'; connect-src 'self' wss: ws:; img-src 'self' data: https:;",
},
```

#### MÉDIO — `dangerouslySetInnerHTML` em 16 Locais, Maioria Sanitizada
**Severidade:** Médio

14 dos 16 usos usam `sanitizeHtml()`:
- `email-templates-manager.tsx:486` — OK
- `send-email-modal.tsx:282` — OK
- `unified-communication-preview.tsx:71,81` — OK
- `wsi-triagem-invite-modal.tsx:638,649,681` — OK

Exceções não sanitizadas:
- `src/app/[locale]/layout.tsx:120,126` — Ver finding Crítico acima

**Fix:** Garantir que TODOS os usos passem por `sanitizeHtml()`. Considerar ESLint plugin `no-danger`.

#### MÉDIO — Auth Cookie com `SameSite: 'none'` em Produção
**Arquivo:** `src/middleware.ts`
```typescript
const COOKIE_SAMESITE: 'lax' | 'none' = IS_PRODUCTION ? 'none' : 'lax'
```
`SameSite: none` permite envio cross-origin, necessário para SSO WorkOS, mas aumenta superfície de ataque CSRF.

**Fix:** Verificar se WorkOS realmente exige `none`. Se sim, garantir que todos os endpoints críticos validam o token JWT e não apenas o cookie.

#### BAIXO — Credenciais Default no Código
**Arquivo:** `src/middleware.ts` (linhas 95-96)
```typescript
const demoEmail = process.env.DEV_AUTO_LOGIN_EMAIL || 'demo@wedotalent.com'
const demoPassword = process.env.DEV_AUTO_LOGIN_PASSWORD || 'demo123'
```
Credenciais hardcoded como fallback. Se alguém criar um usuário `demo@wedotalent.com` / `demo123` em prod acidentalmente, há risco.

**Fix:** Remover defaults hardcoded. Falhar explicitamente se variáveis não definidas quando DEV_AUTO_LOGIN=true.

**Score D5: 62/100**

---

### Rails Backend

**Achados**

#### [CRÍTICO] `CandidatesController` sem isolamento de tenant — qualquer usuário acessa qualquer candidato
**Arquivo:** `app/controllers/v1/users/candidates_controller.rb` + `app/controllers/concerns/resource_loader.rb`
**Detalhe:** O `ResourceLoader.set_resource` faz:
```ruby
klass = controller_name.classify.constantize  # => Candidate
resource = klass.find_by(id: params[:id])     # ZERO filtro de tenant
```
Endpoint: `GET /v1/users/candidates/:id` retorna o candidato **de qualquer empresa**. Com CPF, data de nascimento, documentos de diversidade — isso é violação da LGPD.

**Fix:** `ResourceLoader` deve checar `account_id` ou `CandidatesController` deve override `set_resource` com `scope_to_tenant`.

#### [CRÍTICO] JWT duplicado em 3 locais com implementação ligeiramente diferente cada vez
**Arquivos:**
- `app/lib/json_web_token.rb` (usa `Rails.application.secrets.secret_key_base` — deprecated Rails 7.1)
- `app/controllers/application_controller.rb:22`
- `app/controllers/v1/sessions_controller.rb:44`
- `app/controllers/v1/users/application_controller.rb:50`

**Detalhe:** Três implementações de `jwt_decode`. O `JsonWebToken` usa `secrets.secret_key_base` (API deprecada no Rails 7+). Uma dessas implementações tem `rescue` genérico que engole **qualquer** exceção:
```ruby
rescue  # JsonWebToken — sem tipo! Engole até erros de syntax
  nil
```
**Fix:** Centralizar em `app/lib/json_web_token.rb` com `rescue JWT::DecodeError` explícito, remover as implementações duplicadas nos controllers.

#### [Alto] `OnboardingController.settings` mistura GET e PATCH na mesma action
**Arquivo:** `app/controllers/v1/users/onboarding_controller.rb:128-139`
**Detalhe:** A autorização `authorize_admin!` é chamada **condicionalmente dentro da action**, não como `before_action`. Se um bug de routing direcionar um GET para o branch PATCH, o admin check pode ser bypassado.
**Fix:** Separar em `settings_show` e `settings_update` com `before_action :authorize_admin!, only: [:settings_update]`.

#### [Alto] `JSON.parse(params[:where])` sem validação de schema
**Arquivo:** `app/controllers/v1/users/application_controller.rb:95-104`
```ruby
where.merge!(JSON.parse(params[:where])) if params[:where]
filter = JSON.parse(params[:filter]) if params[:filter]
```
**Detalhe:** Qualquer cliente pode injetar cláusulas where arbitrárias na pesquisa. Sem whitelist das chaves permitidas.
**Fix:** Validar as chaves do hash contra uma whitelist de campos permitidos por model.

#### [Alto] `class_valid?` executa `constantize` em input do usuário sem sanitização
**Arquivo:** `app/controllers/v1/users/application_controller.rb:272-279`
**Detalhe:** Além de `constantize` em input não confiável (pode acessar classes internas do Rails), o `rescue` chama `params[:class_name].constantize` **novamente** na mensagem de erro — se a primeira falhou, a segunda também vai falhar, lançando outra exceção não tratada.
**Fix:** Usar `safe_constantize` e checar contra uma whitelist de models permitidos.

#### [Médio] `is_admin` usado como booleano direto sem framework de autorização
**Arquivo:** `app/controllers/v1/users/application_controller.rb:59`
**Detalhe:** Sem Pundit/CanCan. Autorização baseada em atributo direto `is_admin` no user. Não há RBAC granular — todos os admins têm acesso a tudo.

#### [Médio] Sem proteção CSRF real (null_session em todos os controllers API)
**Detalhe:** `protect_from_forgery with: :null_session` é correto para APIs stateless com JWT. Verificado, não é um problema — apenas registro.

**Score Domínio 5: 48/100** — Cross-tenant candidate access + JWT triplicado são os pontos mais críticos.

---

## D6 — Vibe Coding Debt

### Python AI Layer

**Métricas**
- Arquivos de teste: **441** (excelente) — mas concentrados em poucos domínios
- Generic vars (`result =`, `data =`, `response =`, `temp =`): **3.545 ocorrências**
- Generic functions (`def process`, `def execute`, `def handle`, `def run`): **35 ocorrências**
- Arquivos de rota >1000 linhas: **8 arquivos**
- Código simulado em produção (`"simulated": True`): **4 ocorrências em communication_tools.py**

**Achados**

#### [ALTO] D6-01 — `communication_tools.py` Retorna Mock em Produção
**Arquivo:** `app/domains/communication/tools/communication_tools.py`

```python
except Exception as e:
    logger.warning(f"Database model access issue: {e}, using mock response")
    return {
        "success": True,
        "data": {"simulated": True, ...}
    }
```

Esta é a tool de `send_email` chamada pelo agent ReAct. Quando a query ao Candidate model falha (por qualquer motivo — conexão, migration, etc.), a tool **silenciosamente retorna sucesso simulado**. O agent considera o email como enviado, o usuário vê confirmação, mas nenhum email foi disparado. **Dado de falsa confirmação para o recrutador.**

**Impact:** Crítico para confiança do produto. Um recrutador envia oferta a candidato — o agent confirma — nenhum email chegou. O candidato nunca recebe.

**Fix:** Remover o bloco `except` que retorna `simulated: True`. Propagar o erro para o agent com `"success": False`. Deixar o agent decidir como tratar falha.

---

#### [ALTO] D6-02 — 8 Arquivos de Rota com >1000 Linhas (Business Logic em Routes)
**Arquivos:**
- `app/api/v1/billing.py` — **1.713 linhas**
- `app/api/v1/teams.py` — **1.557 linhas**
- `app/api/v1/workos.py` — **1.400 linhas**
- `app/shared/services/seed_service.py` — **1.367 linhas**
- `app/api/v1/custom_agents.py` — **1.227 linhas**
- `app/api/v1/interview_notes.py` — **1.203 linhas**
- `app/api/v1/data_request.py` — **1.169 linhas**
- `app/api/v1/agent_chat_ws.py` — **1.101 linhas**

`agent_chat_ws.py` (1.101 linhas) é particularmente problemático: mistura autenticação, WebSocket lifecycle, orchestration, error handling e formatting em um único arquivo de rota.

**Impact:** Impossível fazer TDD isolado. Qualquer mudança de protocolo WS afeta lógica de negócio.

**Fix:** Para `agent_chat_ws.py`: extrair `WebSocketSessionManager`, `MessageProcessor`, `AuthMiddlewareWS` como classes separadas. Para billing/teams: extrair para `BillingService`, `TeamsIntegrationService`.

---

#### [ALTO] D6-03 — 441 Arquivos de Teste mas Cobertura Concentrada
**Diretório:** `app/tests/` (20 arquivos visíveis + `test_voice_api.py` na raiz)

Os testes existentes focam em: autenticação WorkOS, hiring policy, multi-tenancy, LGPD, email providers. **Não há testes unitários visíveis para:**
- `main_orchestrator.py` (ponto central de todo chat)
- `cascaded_router` / `llm_cascade.py`
- Tool registries dos agents (sourcing, pipeline, hiring_policy)
- `c3b_layer.py` (camada de compliance crítica)

**Fix:** Sprint de cobertura: priorizar `main_orchestrator.py`, `llm_cascade.py`, `c3b_layer.py` com mocks de LLM. Meta: 70% de cobertura nos paths críticos de chat.

---

#### [MÉDIO] D6-04 — 3.545 Ocorrências de Generic Variable Names
**Pattern:** `result =`, `data =`, `response =` usados de forma genérica em todo o codebase.

Em contextos de AI/agent code isso é problemático: `result = await llm.generate(...)` seguido de `result = db.execute(...)` no mesmo scope cria confusão semântica sobre o que `result` contém.

**Fix:** Renomear variáveis em funções críticas: `llm_response`, `db_result`, `api_response`. Introduzir como coding standard e aplicar em PRs futuros.

---

#### [BAIXO] D6-05 — `_perf_metrics` em Memória Local sem TTL
**Arquivo:** `app/orchestrator/main_orchestrator.py:47`

```python
_perf_metrics: dict[str, list[float]] = {}
```

Dict global em memória cresce indefinidamente. Em worker Gunicorn com múltiplos processos, cada processo tem métricas isoladas — nunca são agregadas.

**Fix:** Usar Redis para métricas de performance ou exportar via Prometheus/OpenTelemetry.

---

**Score D6: 55/100**

---

### Next.js Frontend

**Métricas**
- **`as any` usages:** ~50-100 ocorrências reais de `as any` confirmadas
- **ESLint suppressions:** 101 comentários `eslint-disable`
- **TODOs/FIXMEs:** 0 detectados (positivo — zero TODO no código)
- **Test coverage:** 29 test hooks + 48 arquivos E2E (77 arquivos de teste total para 1.037 TSX = ~7%)
- **Componentes grandes:** 8 componentes com 700+ linhas

**Achados**

#### ALTO — Componentes Monolíticos (700-1.071 linhas)
**Severidade:** Alto

| Arquivo | Linhas | Problema |
|---|---|---|
| `sidebar.tsx` | 1.071 | God component: navegação + auth + notificações + search |
| `pipeline-overview-page.tsx` | 967 | UI + lógica + filtros + data fetching |
| `AgentStudioPage.tsx` | 962 | Configuração + preview + teste + publicação |
| `chat-workflow-reels.tsx` | 919 | Animações + estado + lógica de reels |
| `TalentPoolPage.tsx` | 842 | CRUD + search + filtros |
| `chat-page.tsx` | 727 | Legado + novo sistema (ver D1) |

**Impacto:** Componentes >500 linhas dificultam code review, aumentam chance de re-renders desnecessários e tornam TDD impossível.

**Fix:** Extrair sub-componentes e custom hooks. Regra: componente > 300 linhas = candidato à divisão. Hook > 150 linhas = candidato à divisão.

#### ALTO — Cobertura de Testes Insuficiente (~7%)
**Severidade:** Alto
- 77 arquivos de teste para 1.037 componentes + hooks
- Hooks críticos com testes: `use-agent-streaming-reconnect.test.ts`, `use-lia-chat-connection.test.ts` — positivo
- Componentes sem testes: `sidebar.tsx`, `AgentStudioPage.tsx`, `UnifiedChat.tsx`, todos os modais
- Stores com testes: 4 (`wizard`, `chat-state`, `kanban`, `auth`) — positivo mas parcial

**Fix:** Meta mínima: 30% de cobertura de componentes críticos. Prioridade: `UnifiedChat`, `useChatSocket`, `useChatTransport`, stores.

#### MÉDIO — `as unknown as Record<string, unknown>` como Antipadrão Recorrente
**Severidade:** Médio
**Ocorrências confirmadas:** `useChatSocket.ts`, `useChatTransport.ts`, `proxy-handler.ts`, `chat/route.ts`

**Fix:** Definir tipos discriminados para todos os eventos de streaming. Usar Zod para validar respostas da API em runtime.

#### MÉDIO — 101 Supressões de ESLint (`react-hooks/exhaustive-deps`)
**Severidade:** Médio

Todas as 101 supressões são de `react-hooks/exhaustive-deps`. Indica uso defensivo de `useEffect` com deps incompletos.

**Impacto:** Stale closures silenciosas, bugs difíceis de reproduzir.

**Fix:** Revisar cada supressão. Migrar casos legítimos para `useCallback` com deps completos. Usar `useEffectEvent` (React 19) quando disponível.

#### MÉDIO — `eslint: { ignoreDuringBuilds: true }` em next.config
**Arquivo:** `next.config.js` (linha 14)
```javascript
eslint: {
  ignoreDuringBuilds: true,
},
```
CI nunca falha por lint. Erros ESLint nunca bloqueiam deploy.

**Fix:** Remover `ignoreDuringBuilds: true`. Corrigir os erros que aparecerão.

#### BAIXO — Storybook Configurado mas Sem Evidência de Uso
**Diretório:** `src/stories/` — existe

**Fix:** Auditar stories existentes. Remover se obsoletas ou comprometer-se com manutenção ativa.

**Score D6: 55/100**

---

### Rails Backend

**Achados**

#### [Alto] `V1::Users::ApplicationController` tem 348 linhas com responsabilidades mistas
**Arquivo:** `app/controllers/v1/users/application_controller.rb`
**Detalhe:** Um único base controller contém: JWT auth, tenant scoping, search params, order params, filter params, pin/confidential logic, activity logging, collection deletion, analytics helpers (`data_applies_days/weeks/months`), AND render helpers. Isso é um **God Object**.

**Fix:** Extrair analytics para `app/services/analytics_service.rb`, search helpers para `SearchRenderer` concern já existente, pin logic para `PinManageable` concern.

#### [Alto] Cobertura de testes: apenas 12 spec files para 160 arquivos Ruby (7.5%)
**Arquivo:** `spec/`
**Detalhe:**
- 6 specs de models (apply, apply_status, job, user, candidate, work_c_models)
- 5 specs de controllers (sessions, selective_processes, applies, jobs, candidates)
- 1 spec de channel
- **Zero specs** para: onboarding_controller, talent_pools_controller, magic_links_controller, todos os services, todos os workers, concerns de segurança

**Impacto:** As áreas mais críticas (magic link auth, onboarding, RabbitMQ, tenant scoping) têm 0% de cobertura de testes.

#### [Médio] `add_candidates` loop com `save!` individual — sem tratamento de falha parcial
**Arquivo:** `app/controllers/v1/users/talent_pools_controller.rb:67-76`
**Detalhe:** Se o 5º `tpc.save!` falhar em um loop de 10, os 4 primeiros já foram commitados. Sem transação envolvendo o loop.

#### [Médio] `order_params` com `JSON.parse` sem rescue
**Arquivo:** `app/controllers/v1/users/application_controller.rb:65`
```ruby
order = JSON.parse(params[:order]) || {}
```
**Detalhe:** Se `params[:order]` for uma string JSON inválida, vai lançar `JSON::ParserError` não tratado → 500.

#### [Médio] 33 ocorrências de lógica condicional nos controllers (`if.*params`)
**Detalhe:** Business logic de filtro/busca misturada diretamente nos controllers ao invés de ser delegada para query objects ou scopes de model.

#### [Baixo] Comentário placeholder em `SessionsController`
**Arquivo:** `app/controllers/v1/sessions_controller.rb:36-39`

Comentário de desenvolvimento deixado no código de produção. O `user_payload` retorna apenas `id` e `email` — `name` certamente é necessário no frontend.

**Score Domínio 6: 58/100** — God Controller é o maior problema; cobertura de testes é alarmantemente baixa nas áreas críticas.

---

## Índice de Saúde do Codebase — Detalhamento

| Domínio | Python AI | Frontend | Rails | Média |
|---------|-----------|----------|-------|-------|
| D1 Estrutura | 62 | 68 | 72 | 67,3 |
| D2 AI Quality | 70 | 72 | 45 | 62,3 |
| D3 Integração | 78 | 75 | 55 | 69,3 |
| D4 Persistência | 72 | 70 | 60 | 67,3 |
| D5 Segurança | 75 | 62 | 48 | 61,7 |
| D6 Debt | 55 | 55 | 58 | 56,0 |
| **Total** | **70** | **68,5** | **56** | **66 (pond.)** |

> **Nota sobre pesos internos por camada:**
> - Python AI: D2 (25%), D5 (20%), D4/D3/D1 (15% cada), D6 (10%)
> - Frontend: D2 (25%), D3 (20%), D4/D1/D5 (15% cada), D6 (10%)
> - Rails: pesos iguais aproximados (16,7% cada domínio)
>
> **Média ponderada cross-layer:** Python × 0,40 + Frontend × 0,35 + Rails × 0,25 = 28,0 + 23,975 + 14,0 = **65,975 → 66/100**

---

## Prioridades de Remediação

### P0 — Corrigir HOJE (Bloqueiam Produção)

| # | Camada | Arquivo | Fix em 1 linha |
|---|--------|---------|----------------|
| 1 | Rails | `config/initializers/cors.rb:3` | Parametrizar `origins` via `ENV.fetch("FRONTEND_URL")` |
| 2 | Rails | `db/schema.rb` + `candidates_controller.rb` | Migration `add_column :candidates, :account_id` + filtro de tenant |
| 3 | Rails | `app/lib/json_web_token.rb` + 2 controllers | Centralizar JWT, corrigir `rescue` bare |
| 4 | Rails | `app/services/message_service/event_publisher.rb` | Connection pool singleton em initializer |
| 5 | Python | `app/shared/compliance/c3b_layer.py:15` | Restringir bypass a `APP_ENV=development` + audit log |
| 6 | Python | `app/domains/communication/tools/communication_tools.py` | Remover `except` com `simulated: True`, propagar erro |
| 7 | Frontend | `src/middleware.ts:10` | Mudar `DEV_AUTO_LOGIN` para opt-in via `process.env.DEV_AUTO_LOGIN === 'true'` |
| 8 | Frontend | `src/app/[locale]/layout.tsx:120,126` | Auditar e sanitizar `dangerouslySetInnerHTML` com DOMPurify |
| 9 | Frontend | `candidates/bulk/*/route.ts` | Migrar 5 rotas bulk para `createProxyHandlers()` |

### P1 — Sprint Atual (Alto Impacto)

- **[Python] D5-03:** Mudar `policy_engine.py` para fail-closed em regras de billing
- **[Python] D5-02:** Especificar `allow_methods` e `allow_headers` explicitamente no CORS
- **[Python] D2-01:** Centralizar model strings em `agent_model_config.py`
- **[Python] D2-02:** Error handling granular em `llm_claude.py` para `RateLimitError`, `APITimeoutError`
- **[Python] D4-02:** Converter `policy_engine._get_daily_usage` para async com `AsyncSessionLocal`
- **[Python] D3-01:** Criar `app/shared/http/client_pool.py` com singletons `httpx.AsyncClient`
- **[Rails] S5:** Adicionar `gem 'rack-attack'` com throttle de login e magic link
- **[Rails] S6+S7:** Mover publish RabbitMQ para Sidekiq job; extrair concern `OnboardingPublishable`
- **[Rails] S10:** Envolver `invite` em `ApplicationRecord.transaction`
- **[Rails] S8:** Refatorar `add_candidates` com `insert_all`
- **[Rails] S12:** Separar actions GET/PATCH em `settings_show` e `settings_update`
- **[Frontend] D3:** Centralizar `BACKEND_URL` em `src/lib/config.ts`
- **[Frontend] D4:** Consolidar `hitlPending`, `backgroundTasks`, `planProgressSteps` em `chat-state-store.ts`
- **[Frontend] D6:** Deletar `LegacyChatPage` de `chat-page.tsx` (~650 linhas de dead code)
- **[Frontend] D5:** Adicionar headers CSP, X-Frame-Options, HSTS ao `next.config.js`

### P2 — Backlog Técnico (Médio Prazo)

- **[Python]** Consolidar stack de comunicação — remover duplicatas de email/whatsapp (D1-01)
- **[Python]** Unificar JSON parsing em `structured_output.py` com Pydantic schemas (D2-03)
- **[Python]** Converter raw SQL de tool registries para SQLAlchemy ORM (D4-01)
- **[Python]** Extrair business logic de routes — priorizar `agent_chat_ws.py` e `billing.py` (D6-02)
- **[Python]** Sprint de cobertura de testes: `main_orchestrator`, `llm_cascade`, `c3b_layer` (D6-03)
- **[Rails]** Extrair analytics, search helpers para concerns/services (God Controller S13)
- **[Rails]** Specs para onboarding, talent pools, magic link (cobertura crítica S14)
- **[Rails]** Sanitizar `schema_clone_service.rb` com `quote_table_name` (S9)
- **[Frontend]** Criar discriminated union types para eventos WebSocket (D2)
- **[Frontend]** Adicionar `version` + `migrate` a todos os stores com `persist()` (D4)
- **[Frontend]** Remover `eslint: { ignoreDuringBuilds: true }` e corrigir erros (D6)
- **[Frontend]** Aumentar cobertura de testes para 30% nos componentes críticos (D6)
- **[Frontend]** Refatorar `sidebar.tsx` em sub-componentes (D6)
- **[Frontend]** Adicionar `timeoutMs` configurável por rota no `proxy-handler` (D3)
- **[Frontend]** Adicionar `knip` para dead code detection (D1)

---

## Apêndice: Métricas de Inventário

| Métrica | Python AI | Frontend | Rails |
|---------|-----------|----------|-------|
| Total de arquivos | >450 arquivos Python | 1.037 arquivos TSX + 506 rotas API | 160 arquivos Ruby |
| Linhas de código (aprox) | 152.139 linhas | 135.519 linhas TSX | ~30.000 linhas estimadas |
| Arquivos de teste | 441 (incl. fixtures) | 77 (29 hooks + 48 E2E) | 12 spec files |
| Cobertura estimada | ~30-40% (concentrada em auth, LGPD) | ~7% | ~7,5% |
| Migrações | 76 Alembic | N/A | 85 Rails migrations |
| Dívida técnica principal | 59 TODOs phase2 + 8 routes >1000 linhas + mock em produção | Dual chat system + 101 eslint-disable + 7% test coverage | 4 críticos de produção: CORS, tenant leak, JWT, RabbitMQ |
