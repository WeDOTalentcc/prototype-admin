# QA Fix Report — 2026-04-15

> **Input:** `QA_REPORT_2026-04-15.md` (16 bugs detectados via Claude Preview contra Replit)
> **Plano:** `.claude/plans/delightful-sniffing-gosling.md`
> **Branch:** `fix/qa-2026-04-15`
> **Repos impactados:** apenas `WeDOTalentcc/wedotalent02202026` (FastAPI + Next.js).
> **`ats-api-copia` (Rails):** não tocado — nenhum bug estava lá.

---

## Resumo

| Status | Qtd | Bugs |
|---|---:|---|
| ✅ Corrigido | 13 | BUG-01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 12, 13, 14¹ |
| 📋 Fora de escopo (plano separado) | 1 | BUG-11 (bottom-dock + página Minha Empresa) |
| 📝 Nota sem código | 2 | BUG-15 (dados de teste), BUG-16 (Replit dev mode) |

¹ BUG-14 (cards de template silenciosos no overflow de quota) é resolvido **transitivamente** por BUG-02 + BUG-03 — agora mostra mensagem clara de quota em vez de cliques silenciosos.

**Commits:**
1. `d55a7299` — fix(backend): BUGs 01/04/05/06/07
2. `7383d639` — fix(frontend): BUGs 02/03/08/09/10/12/13
3. `4d254e2c` — test: cobertura dos fixes (pytest + Vitest + Playwright)

---

## Fixes detalhados

### 🔴 BUG-01 — Chat LIA retorna `{"content": ""}` silenciosamente
**Arquivo:** `lia-agent-system/app/api/v1/chat.py`

Causa: orquestrador retorna `response=""` sem tratamento. O handler seguia e devolvia `ChatResponse(content="")` com status 200.

Fix: lê `orch_result.get("response") or ""` (defesa), e se vazio, loga `chat.empty_response` com contexto e levanta `HTTPException(502, "LIA não conseguiu gerar resposta...")`. **Bug silencioso → erro observável.**

### 🔴 BUG-04 — `GET /sourcing-agents` → 500
**Arquivo:** `lia-agent-system/app/api/v1/sourcing_agents.py`

Adicionou:
- `logger = logging.getLogger(__name__)`
- Tipagem `current_user: User`
- Guard `if not company_id: raise 400` (evita query com company_id vazio/None)
- `try/except` envolvendo a query, logando stacktrace em erro e levantando 500 com `detail=f"Falha ao listar agentes: {exc.__class__.__name__}"`

### 🔴 BUG-06 — `GET /agent-templates/sectors` → 404
**Arquivo:** `lia-agent-system/app/api/routes.py`

Causa raiz: `agent_templates_router` tem `GET /agent-templates/{template_id}` e era registrado **antes** de `sector_templates_router`. FastAPI casava `sectors` como `template_id="sectors"` → 404.

Fix: invertida ordem de registro + comentário explicando porquê.

### 🟠 BUG-05 — `GET /hitl/pending` → 500 intermitente
**Arquivos:** `lia-agent-system/app/api/v1/hitl.py`, `app/domains/cv_screening/services/hitl_service.py`

Causa: `hitl_service.get_all_pending_by_company` abria `AsyncSessionLocal()` própria em vez de usar a sessão do request → esgotava pool em concorrência.

Fix:
- `hitl.py`: handler ganhou `db: AsyncSession = Depends(get_db)` + remoção do `try/except` que engolia exceptions em `pending_list = []`.
- `hitl_service.py`: `get_all_pending_by_company(company_id, db=None)` — usa `db` do request se fornecido; mantém fallback `AsyncSessionLocal` (backward compat).

### 🟠 BUG-07 — Briefing diário: "Não foi possível carregar"
**Arquivo:** `lia-agent-system/app/api/v1/briefing.py`

Causa: endpoint recebia `user_id="default_user"` (fallback do proxy FE) e o service falhava com user inexistente no DB.

Fix: early-return com `_EMPTY_BRIEFING` para `user_id` vazio ou `"default_user"`. Logging estruturado no catch do fluxo real.

### 🔴 BUG-03 — "Error 403" genérico na UI
**Arquivos:** `plataforma-lia/src/lib/api/extract-error-message.ts` (novo), `plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx`

Causa: a UI fazia `errData?.detail` mas o proxy envia `{error, details: {message}}` — daí caía em `` `Error ${res.status}` `` mesmo com mensagem detalhada disponível.

Fix: novo helper `extractErrorMessage(body, status)` cobre todos os formatos do backend (details.message, detail string, detail objeto, message, error) com fallback. Usado em `AgentStudioPage.handleToggleStatus` e criação de agente.

### 🔴 BUG-02 — Empty state silencioso quando GET /sourcing-agents falha
**Arquivo:** `plataforma-lia/src/components/pages-agent-studio/AgentsTab.tsx`

Causa: `loadAgents` lia `data.agents || []` sem checar `res.ok`. Em 500, `data` era `{error: ...}` → `agents=[]` → empty state, mesmo com agentes existentes.

Fix: novo state `loadError` + branch de render com `<AlertCircle/> + "Tentar novamente"`. Distingue lista vazia legítima de erro.

### 🟡 BUG-13 — Chat sem indicador "LIA digitando"
**Arquivos:** `plataforma-lia/src/hooks/chat/useChatSocket.ts`, `useChatMessages.ts`, `use-lia-chat-connection.ts`

Causa: `isThinking` só era setado ao receber evento `thinking` do WebSocket. No caminho REST/SSE nunca ligava.

Fix: `useChatSocket` expõe `setIsThinking`; `useChatMessages` aceita como prop e chama `setIsThinking(true)` ao enviar + `finally { setIsThinking(false) }` no caminho REST. Propagado pelo facade.

### 🟡 BUG-12 — ConversationalCreator sem CTA
**Arquivo:** `plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx`

Causa: componente existia mas estava sem botão visível (só na aba "Custom Agents", sem chamar atenção).

Fix: novo botão **"Criar com IA"** (variant outline, ícone `Wand2`) no toolbar ao lado de `"+ Criar Agente"`. Troca para aba "custom" e faz scroll suave até o `<div id="agent-studio-conversational-creator">`.

### 🟠 BUG-09 — Modo "Lateral" do chat navega para Tarefas
**Arquivo:** `plataforma-lia/src/components/dashboard-app.tsx`

Causa: handler de `lia:leave-fullscreen-chat` fazia `setCurrentPage("Tarefas")` hardcoded.

Fix: `previousPageBeforeChatRef` guarda a última página não-"Chat LIA". Handler restaura essa página (fallback "Tarefas" mantido só se nada foi salvo).

### 🟡 BUG-10 — Layout Agent Studio quebra com chat lateral
**Arquivo:** `plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx`

Causa: `grid-cols-1 md:grid-cols-4` ativa 4 colunas em viewport de 768px — mas com chat lateral (~360px) sobra só ~920px úteis, truncando "PASSO" em "PASS".

Fix: `grid-cols-1 sm:grid-cols-2 xl:grid-cols-4` + `min-w-0` + `break-words` nos cards. Para a outra grid horizontal (agents.length > 0), migrado para `xl:flex` com colunas em telas menores. Setas escondidas em telas sem espaço.

### 🟠 BUG-08 — `user_id=default_user` em requests pré-auth
**Novos arquivos:** `plataforma-lia/src/hooks/shared/use-authenticated-user-id.ts`

**Arquivos alterados:**
- `src/components/sidebar.tsx` — gate de render do `NotificationSystem` com `isAuthReady`
- `src/components/top-bar.tsx` — idem
- `src/components/daily-briefing-card.tsx` — `userId` agora é `null` até auth hidratar; fetch gated
- `src/app/api/backend-proxy/briefing/route.ts` — proxy server-side recusa `user_id=default_user` com 400
- `src/app/api/backend-proxy/notifications/read-all/route.ts` — idem

Contrato novo: `useAuthenticatedUserId()` retorna `{ userId: string | null, isReady: boolean }`. `null` enquanto carrega → caller decide gate. **Nunca retorna `"default_user"`.**

---

## Cobertura de testes

### Backend (pytest) — `lia-agent-system/tests/unit/test_qa_fixes_2026_04_15.py`

- `TestHitlServiceAcceptsExternalDb::test_uses_external_db_when_provided`
- `TestHitlServiceAcceptsExternalDb::test_empty_company_id_returns_empty_list`
- `TestRouteRegistrationOrder::test_sector_templates_router_registered_before_agent_templates`
- `TestBriefingEmptyForDefaultUser::test_default_user_returns_empty_briefing`
- `TestBriefingEmptyForDefaultUser::test_empty_user_id_returns_empty_briefing`
- `TestSourcingAgentsDefensiveList::test_missing_company_id_raises_400`
- `TestChatEmptyResponseGuard::test_chat_py_has_empty_response_guard`

### Frontend (Vitest)

- `src/lib/api/extract-error-message.test.ts` — 8 testes cobrindo todos os formatos de erro
- `src/hooks/__tests__/use-authenticated-user-id.test.ts` — 7 testes (resolveUserId + hook) incluindo `"nunca retorna default_user"`

### Smoke E2E Playwright — `plataforma-lia/e2e/tests/qa-smoke-2026-04-15.spec.ts`

1. **BUG-01** — Chat LIA responde com texto não vazio
2. **BUG-13** — Indicador "digitando" aparece durante espera
3. **BUG-02** — Agent Studio lista agentes sem card de erro em 200 OK
4. **BUG-03** — Quota excedida mostra mensagem detalhada (não "Error 403")
5. **BUG-09** — Troca Fullscreen → Sidebar preserva página (Vagas, não Tarefas)
6. **Contexto** — Chip muda entre Tarefas/Vagas/Estúdio/Módulos
7. **BUG-07** — Briefing diário carrega sem card de erro
8. **BUG-08** — Zero requests com `user_id=default_user`

**Rodar contra Replit:**
```bash
PLAYWRIGHT_BASE_URL=http://localhost:3333 \
  npx playwright test qa-smoke-2026-04-15
```
(O proxy local `.claude/replit-proxy.js` já existe e aponta para a instância Replit.)

---

## Fora de escopo

### BUG-11 — Modo "bottom-dock" + página "Minha Empresa"
É feature nova (não bug). Precisa:
- Estender `ChatMode` type com `"bottom-dock"`
- Nova branch de layout em `UnifiedChat.tsx`
- Criar rota `/[locale]/minha-empresa` ou mapear para menu existente

**A criar em plano separado.** Paulo confirmou essa segregação ao aprovar o plano.

### BUG-15 — Vagas duplicadas (V0001–V0006 "Desenvolvedor Python Senior")
Dados de seed/teste. Sem código para mudar — nota para ops reverem o dataset de demo.

### BUG-16 — Hot-reloads do webpack
Replit rodando em dev mode. Para produção definitiva, `NODE_ENV=production` elimina `_next/static/webpack/*.hot-update.*`. Sem código neste PR.

---

## Próximos passos (ainda nesta branch)

1. **Rodar os testes locais** (ambiente do usuário):
   ```bash
   cd lia-agent-system && pytest tests/unit/test_qa_fixes_2026_04_15.py -v
   cd plataforma-lia && npx vitest run
   cd plataforma-lia && npx next build
   ```
2. **Push da branch:**
   ```bash
   git push -u origin fix/qa-2026-04-15
   ```
3. **Abrir PR** em `WeDOTalentcc/wedotalent02202026` apontando para `main` com o corpo linkando para `QA_REPORT_2026-04-15.md` + este relatório.
4. **Smoke E2E contra Replit atualizado** (depois do deploy do Replit puxar a branch) — os 8 cenários devem passar.
5. Depois do merge, iniciar plano separado para **BUG-11** (bottom-dock + Minha Empresa).

---

## Como o fix respeita a arquitetura canônica

- **`CLAUDE.md` (raiz):** Regra de Ouro "Planejamento → aprovação → código" seguida (plano aprovado antes dos commits).
- **ADR-005 (response_model):** nenhum handler novo; alterações em handlers existentes mantiveram ou não regrediram.
- **ADR multi-tenancy:** `company_id` obrigatório em `sourcing_agents.list` reforçado — 400 explícito quando ausente.
- **ADR-002 (lia_models):** imports `from libs.models.lia_models...` preservados; `_convert_response()` no `ChatAdapter` não tocado.
- **Design System v4.2.1:** Fixes de layout usam apenas tokens `lia-*`/`wedo-*` + classes Tailwind semânticas. Zero hex hardcoded.
- **Portabilidade Vue:** hook `useAuthenticatedUserId` com interface `{ userId, isReady }` (padrão Composition API / Pinia); helper `resolveUserId` pura sem React. Helper `extractErrorMessage` também agnóstico de framework.
- **LGPD / PII:** nenhum log novo contém PII (só `user_id` não-sensível e `company_id`).
- **Teams (não tocar):** `PUBLIC_PREFIXES` em `auth_enforcement.py` intocado.

---

_Relatório gerado automaticamente como parte do plano `.claude/plans/delightful-sniffing-gosling.md`._
