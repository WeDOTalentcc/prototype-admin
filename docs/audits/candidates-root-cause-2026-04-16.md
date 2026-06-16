# Auditoria de causa raiz — Funil de Talentos

**Data:** 2026-04-16
**Autor:** Task #287 (auditoria puramente investigativa — nenhuma mudança de código)
**Sintomas investigados:** “Erro ao carregar candidatos. Tente novamente.” e “Failed to fetch” na página
`/[locale]/funil-de-talentos`, mesmo após tasks #267, #268, #274, #275, #276, #282, #283, #284, #285.

---

## 1. Escopo e metodologia

A auditoria cobre o caminho que o Funil de Talentos exercita quando é aberto pelo usuário demo,
partindo do componente React até o banco, passando por Pearch/Apify/RAG/LLM factory/embeddings.
Para cada camada listamos um veredito (**OK / risco / quebrado**) com evidências em código
(caminho + linha) e observações do ambiente de dev (workflows `dev-server` e `lia-backend` em
execução em 2026-04-16 21:43 UTC).

Evidência empírica principal (probe direta no ambiente):

| Alvo | Comando | Resultado |
|---|---|---|
| Backend FastAPI direto | `curl http://127.0.0.1:8001/api/v1/candidates?limit=3` (sem token) | **HTTP 401** `{"detail":"Authentication required"}` em 14 ms |
| Proxy Next.js | `curl http://127.0.0.1:5000/api/backend-proxy/candidates?limit=5` (sem cookie) | **HTTP 401** `{"error":"Authentication required"}` em 50 ms |
| `dev-server` logs | `/api/auth/ws-token 503` repetidos | Renovação de token WS está falhando em loop |

---

## 2. Fluxo ponta a ponta

```
FunilDeTalentosPage
  └─ useCandidatesList()                               (src/hooks/candidates/use-candidates-list.ts)
      └─ liaApi.getCandidates({limit, offset, ...})    (src/services/lia-api/candidates-api.ts:340)
          └─ fetchWithRetry  (attempts=3, timeout=20 s, retry em 5xx/network)
              └─ GET /api/backend-proxy/candidates?...    [Next.js App Router]
                  └─ createProxyHandlers → fetch(BACKEND_URL + /api/v1/candidates, auth, signal=30 s)
                      └─ AuthEnforcementMiddleware       (app/middleware/auth_enforcement.py:138)
                          ├─ valida Bearer ou rejeita 401 "Authentication required"
                          └─ (DEV_MODE) injeta state.company_id="demo_company"
                      └─ enforce_candidates_deprecation  (deprecation.py:133) — só 410 se STRICT_RAILS_ONLY
                      └─ list_candidates                 (candidates/candidates_crud.py:156)
                          └─ CandidateRepository.list_candidates(...)   # sem tenant filter
                                                                         # 7 s p95 (task #282)
                          └─ except Exception: 500 str(e)
```

A busca híbrida (Pearch/Apify/RAG/LLM) **só é acionada via POST `/search/candidates`** (aba de busca
com query digitada). O carregamento inicial do Funil **não exercita** essa cadeia — ela é
relevante apenas para o segundo sintoma (“LIA está buscando…” travado).

---

## 3. Veredito por camada

### 3.1 Frontend — página e hook  → **RISCO**
- `FunilDeTalentosClient.tsx:94-106` consome `useCandidatesList()` no mount. Não chama
  Pearch/Apify. ✅
- `useCandidatesList` trata erro com *string genérica* em pt-BR (`"Erro ao carregar candidatos.
  Tente novamente."`) independente do status HTTP (linhas 79-85). Ou seja, 401, 403, 503 e 500 do
  backend aparecem ao usuário exatamente igual. Não há CTA de relogin. **Coberto por #276.**
- `liaApi.getCandidates` anexa `err.status = response.status` (candidates-api.ts:359-363) — mas o
  hook descarta esse campo. Isso é o que permite o sintoma: sessão expirada ⇒ 401 do proxy ⇒
  banner vermelho de erro genérico ⇒ usuário acha que o backend caiu. **Lacuna: o hook precisa
  ler `err.status` e renderizar um estado específico para 401/403.**
- `fetchWithRetry` (services/lia-api/base.ts:23-58) usa `AbortSignal.timeout(20000)` e 3
  tentativas com backoff 0/1/3 s. Correto — task #274 cobre; nenhum bug novo. ✅
- `useCandidatesQuery` existe paralelamente (componentes antigos) e é mais permissivo (não
  anexa status, transforma em `Error("Search failed")`). Não é exercido pelo Funil de Talentos
  atual, mas é uma armadilha pro futuro.

### 3.2 Proxy Next.js `/api/backend-proxy/candidates`  → **OK**
- `src/app/api/backend-proxy/candidates/route.ts` usa `createProxyHandlers` canônico com
  `signal: AbortSignal.timeout(30000)` (proxy-handler.ts:178), unwrap de envelope FastAPI,
  erros passam status e corpo (proxy-handler.ts:186-189). ✅
- `getAuthHeaders` (auth-headers.ts:4-22) resolve Authorization → cookie `lia_access_token` →
  `workos_session`. Se **nenhum** está presente, envia sem header → backend devolve 401. Esse é o
  caminho exato que reproduz a evidência do §1 (`HTTP 401 Authentication required`).

### 3.3 Proxy Next.js `/api/backend-proxy/search/candidates`  → **RISCO**
- Hand-roll (`route.ts:1-82`) duplica lógica do `createProxyHandlers` **sem**:
  - `AbortSignal.timeout(...)` no `fetch` interno (linha 28). Se o backend trava, a rota pendura
    por quantos segundos a plataforma aguentar.
  - Propagação do corpo/details originais no bloco `except` (linhas 44-49) — tudo vira
    `{"error":"Erro ao conectar com o backend"}` 500 opaco. O usuário do Funil de Talentos
    vê exatamente esta mensagem quando o backend devolve 503 da Pearch, 502 transitório, ou
    exceção no rubric/embeddings.
  - Forward de form-data/custom headers (task #249 já aponta essa gap para outras rotas).
- Unwrap envelope só checa `"ok" in json && "data" in json` e assume `data` como objeto —
  não cobre respostas em que `data` é uma lista.

### 3.4 Auth e tenant  → **QUEBRADO em DEV_MODE, RISCO no caminho padrão**
- `AuthEnforcementMiddleware` (middleware/auth_enforcement.py:138) **roda antes** do
  `get_current_user_or_demo`. Se não houver `Authorization: Bearer …`, o request morre com 401
  (linhas 234-238). Ou seja: o fallback demo em `dependencies.py:get_current_user_or_demo`
  **nunca é exercido quando vem via middleware global**. A página confia em cookie
  `lia_access_token`/`workos_session`; se o cookie expirou ou nunca foi emitido (fluxo demo
  direto), 100 % dos requests do Funil batem em 401. **Esta é a causa raiz #1 do sintoma.**
- Quando `LIA_DEV_MODE=true` **e** `X-Dev-Api-Key` confere, o middleware injeta um usuário
  sintético com `company_id="demo_company"` (linhas 227-230 e 249-253) — a **string legada**,
  não o `DEMO_COMPANY_UUID` canônico. Isso:
  - reintroduz “demo_company” em `request.state.company_id` depois das correções de #283/#284;
  - quebra rotas que chamam `resolve_tenant_id(...)` (tenant.py:61-67), pois “demo_company”
    está em `_INVALID_TENANT_VALUES`;
  - cria divergência entre `request.state.company_id` ("demo_company") e `user.company_id`
    (DEMO_COMPANY_UUID após `ensure_demo_user`).
- `ensure_demo_user` (dependencies.py:36-95) já seta `DEMO_COMPANY_UUID` e faz migração
  in-place de rows legados com `"demo_company"`. ✅ (coberto por #283, complementa #285)
- Endpoint `/api/v1/candidates` **não** declara `Depends(get_current_user_or_demo)` nem filtra
  por tenant (candidates_crud.py:156-229). Só o middleware global defende — e só para fora
  de produção, nada filtra a query por company_id.

### 3.5 Backend `/api/v1/candidates` (listagem)  → **RISCO**
- Sem tenant filter: `candidate_repo.list_candidates(search, status, source, seniority, ids,
  skip, limit, sort_by, sort_order)` não recebe `company_id`. Em ambiente multi-tenant real,
  retorna candidatos de todas as empresas. Task #282 foca em latência, não em tenancy.
- Broad `except Exception as e: raise HTTPException(500, detail=str(e))` (linhas 227-229):
  qualquer erro de DB (ex.: tipo inválido para coluna `company_id`, timeout do pool,
  constraint) vaza como 500 com mensagem Python crua. No proxy isso vira o banner genérico.
- Dep. `enforce_candidates_deprecation` (linha 44) adiciona `Deprecation: true`/`Sunset`
  mesmo quando `STRICT_RAILS_ONLY=false`. Se o operador virar a flag, a rota devolve **410
  Gone** — kill-switch que o frontend trata como erro genérico também.

### 3.6 Backend `/api/v1/search/candidates` (busca híbrida)  → **RISCO**
- `search_candidates` (candidate_search/search.py:99-325) captura `Exception` e devolve 500
  com `detail=f"Search failed: {str(e)}"`. LLM/embeddings/RAG errors chegam assim.
- Se `PEARCH_CIRCUIT` e `APIFY_SEARCH_CIRCUIT` estiverem ambos abertos e `search_pearch=True`,
  devolve **503** (linhas 145-149). O proxy hand-roll mapeia como 500/503 com body genérico,
  frontend mostra “Erro ao carregar candidatos”.
- Tracking de créditos (`CreditService.consume_action`, linha 288) ocorre depois da resposta já
  montada — se falhar, é só `logger.warning` (não afeta o sintoma, mas indica que saldo pode
  sair dessincronizado).

### 3.7 Sourcing externo  → **RISCO**
- **Pearch** (`pearch_service.py`): depende de `PEARCH_API_KEY`. `.env` do `lia-agent-system`
  tem `PEARCH_API_KEY=` em branco; no processo em execução, `PEARCH_API_KEY` **não aparece no
  `env | grep`** (§8). Health check em `/api/v1/candidates/health` retornaria
  `api_key_set=false`. Todo `include_pearch=true` cairá em circuit open ou 503.
- Circuit-breaker fallback em `_pearch_search_fallback` (pearch_service.py:40-95) tenta RAG
  interno (pgvector) — só ajuda se `company_id` for canônico e o pgvector estiver populado.
- **Apify fallback** (`apify_search_service.py:26-28`): ligado por
  `APIFY_SEARCH_FALLBACK_ENABLED=true`. Variável **não está setada** no ambiente atual. Mesmo
  com `APIFY_API_KEY` presente, o fallback está desligado por default, então abrir o Pearch
  circuit = 503 imediato.
- `APIFY_TOKEN` não aparece no env — só vemos `APIFY_API_KEY`. `ApifyService` aceita ambos,
  mas é risco de configuração se um componente diferente espera `APIFY_TOKEN`.
- **RAGPipelineService**: usa embeddings (próximo item) + pgvector. Fail-safe devolve vazio.
- **RubricEvaluationService**: chamado somente quando `request.job_id` é passado; falhas ficam
  em `logger.warning`, não quebram a resposta.

### 3.8 LLM factory / embeddings  → **RISCO**
- `app/shared/providers/llm_factory.py` é a fábrica canônica (referenciada em
  `scripts/check_llm_factory_enforcement.py`). Providers configurados: OpenAI, Anthropic,
  Gemini (`shared/providers/llm_*.py`) + embeddings análogos
  (`embedding_openai`, `embedding_gemini`).
- Ambiente atual tem `ANTHROPIC_API_KEY`, `AI_INTEGRATIONS_ANTHROPIC_API_KEY`,
  `AI_INTEGRATIONS_GEMINI_API_KEY`. **`OPENAI_API_KEY` não está visível** via `env`. Qualquer
  provider que escolha OpenAI por padrão (embeddings antigos, rubric model default) vai falhar
  no startup do serviço.
- `/api/v1/candidates` (listagem) **não** invoca LLM/embeddings. Logo, LLM quebrado não
  explica o erro do carregamento inicial, mas explica falhas em rubric/enriquecimento durante
  busca.

### 3.9 Variáveis de ambiente  → **risco de configuração**

Legenda: ✅ presente · ⚠ ausente/em branco · ❓ não verificado.

| Variável | Status atual (Replit) | Observação |
|---|---|---|
| `BACKEND_URL` | ✅ | `http://127.0.0.1:8001` — confere com o processo |
| `LIA_BACKEND_URL` / `NEXT_PUBLIC_BACKEND_URL` | ✅ | Legadas, mantidas |
| `PEARCH_API_KEY` | ⚠ em branco em `.env`, ausente em `env` | Global search quebra |
| `APIFY_API_KEY` | ✅ | |
| `APIFY_TOKEN` | ⚠ | Alguns caminhos podem esperar esta chave |
| `APIFY_SEARCH_FALLBACK_ENABLED` | ⚠ (default=false) | Fallback desligado |
| `OPENAI_API_KEY` | ⚠ em branco em `.env`, ausente em `env` | Pode derrubar embeddings/rubric |
| `GEMINI_API_KEY` | ✅ via `AI_INTEGRATIONS_GEMINI_API_KEY` | |
| `ANTHROPIC_API_KEY` | ✅ | |
| `APP_ENV` | ❓ não visível | Afeta `_dev_environment()` |
| `LIA_DEV_MODE` / `LIA_DEV_API_KEY` | ❓ | Controla fallback dev do middleware |
| `STRICT_RAILS_ONLY` | default false | Se true, `/candidates` devolve 410 |
| `RAILS_API_URL` | ❓ | Se setado, list_candidates tenta Rails primeiro |
| Secret JWT / WorkOS | ❓ | `dev-server` reporta `/api/auth/ws-token` 503 em loop |
| Postgres (`DATABASE_URL`) | ✅ (logs SQL confirmam pool ativo) | |

---

## 4. Causas raiz

### 4.1 Confirmadas (evidência reproduzível neste Repl)

1. **Middleware global rejeita requisições sem Bearer com 401, antes do fallback demo.**
   Evidência: `curl /api/v1/candidates?limit=3` devolve `401 Authentication required` em
   14 ms. Código: `app/middleware/auth_enforcement.py:234-238`. O `get_current_user_or_demo`
   de `app/auth/dependencies.py:234` nunca é executado. Sintoma: banner “Erro ao carregar
   candidatos” em qualquer sessão sem cookie válido.

2. **UI não diferencia 401/403 de 5xx.** `use-candidates-list.ts:79-85` escreve a mesma
   string pt-BR para todo erro. Sessão expirada aparece idêntica a backend fora do ar.

3. **Proxy de busca hand-roll achata todo erro em 500 opaco.**
   `src/app/api/backend-proxy/search/candidates/route.ts:18-49` — corpo de erro do backend é
   descartado; UI perde o motivo real (503 Pearch, 400 validation, etc.).

4. **Endpoint `/api/v1/candidates` não filtra por tenant nem exige `current_user`.**
   `candidates_crud.py:156-229`. Em produção multi-tenant, vaza dados entre empresas;
   em dev, o broad `except` esconde erros de driver como 500 opaco.

### 4.2 Suspeitas (faltam evidências diretas mas o código deixa explícito)

5. **DEV_MODE do middleware reintroduz `"demo_company"` (string legada)**
   (`auth_enforcement.py:227-230, 249-253`). Qualquer rota que usa `resolve_tenant_id` falha
   com `ValueError`, virando 500 genérico no proxy.

6. **Pearch e Apify sem chaves/flag no Repl atual.** Busca global cai em 503 imediato; sem
   diferenciação, UI exibe erro genérico. Evidência: `PEARCH_API_KEY` em branco,
   `APIFY_SEARCH_FALLBACK_ENABLED` não setado.

7. **`OPENAI_API_KEY` ausente pode derrubar embeddings/RAG/rubric.** Não impacta a listagem
   (GET /candidates), mas contribui para o segundo sintoma (“LIA está buscando…” travado).

8. **`/api/auth/ws-token` devolvendo 503 em loop** nos logs do `dev-server` — indica que o
   serviço de emissão de token WebSocket está com problema. Embora seja rota distinta, se o
   usuário depender desse endpoint para manter a sessão/identificar-se no SSO, o cookie
   `lia_access_token` pode estar expirando e alimentando #1.

9. **`enforce_candidates_deprecation` (Sunset 2026-07-31)** é kill-switch: se alguém ligar
   `STRICT_RAILS_ONLY=true` sem rails_adapter pronto, o Funil fica 410 Gone.

10. **Proxy de search não usa `AbortSignal.timeout()`**: se o backend pendura em
    LLM/Pearch, a rota Next.js fica esperando indefinidamente até o timeout global
    (≈ minutos), e o `fetchWithRetry` do cliente aborta em 30 s, mostrando “Failed to fetch”.

---

## 5. Mapa causa → task

| # | Causa | Task existente | Cobertura |
|---|---|---|---|
| 1 | Middleware 401 antes do fallback demo; fluxo demo quebra sem cookie | **nenhuma direta** | ❌ Gap — precisa task nova |
| 2 | UI não distingue 401 de 5xx (sem CTA relogin) | #276 “Mostrar tela de relogin…” | ✅ Cobre o sintoma de UX; ainda precisa que o hook leia `err.status` |
| 3 | Proxy `/search/candidates` hand-roll opaco, sem timeout, sem details | parcialmente #249 (form-data/headers) e #274 (retry/timeout) | ⚠ Falta converter a rota para `createProxyHandlers` e propagar corpo de erro |
| 4 | `/api/v1/candidates` sem tenant filter e broad `except` → 500 `str(e)` | #282 (latência <1 s) | ⚠ Latência coberta; tenancy + sanitização de erro **não** |
| 5 | DEV_MODE injeta `"demo_company"` legado em request.state | #283/#284/#285 (migração UUID) | ⚠ Código em produção migrou, mas o middleware ficou para trás — gap |
| 6 | Pearch/Apify sem chaves/flag | nenhuma | ❌ Gap de configuração/runbook |
| 7 | `OPENAI_API_KEY` ausente → embeddings/rubric quebram | nenhuma | ❌ Gap |
| 8 | `/api/auth/ws-token` 503 em loop | nenhuma | ❌ Gap |
| 9 | `STRICT_RAILS_ONLY` kill-switch vira 410 | nenhuma | Baixa prioridade (flag off hoje) |
| 10 | Proxy de search sem AbortSignal | #274 | ⚠ Parcial — rota hand-roll está fora do padrão |
| — | #267 (campo `company_id`) | cobre normalização no Kanban; não afeta listagem do Funil |
| — | #268 (SWR assumindo array) | cobre outras páginas; não afeta `useCandidatesList` |
| — | #275 (watchdog candidate-profile) | correlato; não afeta listagem |

---

## 6. Recomendações priorizadas

### P0 — Desbloquear o sintoma principal
- **P0.1** Auditar e corrigir o `AuthEnforcementMiddleware` para, fora de produção,
  permitir fallback explícito ao usuário demo (`ensure_demo_user`) **com `DEMO_COMPANY_UUID`
  canônico**, não com a string “demo_company”. Alternativa: garantir que o fluxo Replit
  emite `lia_access_token` válido antes da primeira navegação. (Causa #1 + #5)
- **P0.2** Fazer `useCandidatesList` ler `err.status` e, para 401/403, emitir um estado
  “relogin”/“sessão expirada” com CTA, em vez do banner genérico. Conecta com #276 e é
  pré-requisito para a task #276 funcionar.
- **P0.3** Converter `src/app/api/backend-proxy/search/candidates/route.ts` para
  `createProxyHandlers` (ou pelo menos: adicionar `AbortSignal.timeout(30_000)` e propagar
  body + status original ao cliente).

### P1 — Robustez do backend
- **P1.1** Adicionar `Depends(get_current_user_or_demo)` + filtro por
  `company_id = user.company_id` em `list_candidates` (candidates_crud.py:156). Evita vazamento
  cross-tenant e força o caminho de auth. Substituir `str(e)` por mensagem sanitizada; logar
  full stack no servidor.
- **P1.2** Diferenciar 503 (Pearch/Apify ambos open) de 500 no `search.py:320-325` —
  devolver `warning_message` estruturado em vez de derrubar tudo como 500 genérico.
- **P1.3** Documentar e preencher no Replit: `PEARCH_API_KEY`, `OPENAI_API_KEY`,
  `APIFY_SEARCH_FALLBACK_ENABLED`, `APIFY_TOKEN` (se algum componente espera), `APP_ENV`.
  Publicar um *healthcheck* no boot que falhe ruidoso se faltar.

### P2 — Higiene
- **P2.1** Investigar o loop de `/api/auth/ws-token 503` — provavelmente dependência
  tangencial mas alimenta expiração de `lia_access_token`.
- **P2.2** Remover ou gatekeep o `enforce_candidates_deprecation` assim que Rails estiver
  pronto, para eliminar o kill-switch latente.
- **P2.3** Unificar `useCandidatesQuery` e `useCandidatesList` — código morto ou duplicado
  gera regressões como a atual.

---

## 7. Resumo executivo (para o comentário da task)

As três a cinco causas mais prováveis, em ordem:

1. **Middleware global devolve 401 antes do demo-fallback** — qualquer request sem cookie
   válido quebra a página. É o mais provável pro sintoma dominante.
2. **UI colapsa 401/403/5xx em uma única mensagem** — mesmo que o backend esteja OK, o usuário
   vê “Erro ao carregar candidatos” em cenários tratáveis (sessão expirada).
3. **Proxy `/search/candidates` hand-roll esconde o motivo real** (sem timeout, sem body) —
   transforma qualquer 4xx/5xx útil em 500 opaco.
4. **`/api/v1/candidates` sem tenant filter + `except Exception: 500 str(e)`** — segurança e
   mensagens de erro crús.
5. **Config de sourcing incompleta no Repl** (`PEARCH_API_KEY`, `APIFY_SEARCH_FALLBACK_ENABLED`,
   `OPENAI_API_KEY`) — deriva pro segundo sintoma (“LIA está buscando…” travado).

**Primeiros passos:** atacar (1) + (2) juntos — é o ciclo que o usuário sente. Em seguida
(3) e (4) em paralelo. Só depois mexer em configuração de Pearch/Apify/LLM.
