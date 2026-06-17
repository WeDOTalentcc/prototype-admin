# Runbook — Variáveis de ambiente de sourcing & providers

**Owners:** Plataforma LIA · **Última atualização:** 2026-04-17 (Task #297)

Este runbook lista cada variável de ambiente que o backend `lia-agent-system`
consulta para habilitar **sourcing externo** (Pearch, Apify), **LLMs**
(OpenAI, Anthropic, Gemini), **autenticação** (WorkOS) e o **atalho de DEV**.
Ele é a fonte de verdade que o healthcheck de boot e o endpoint
`GET /api/v1/health/providers` consultam.

> Verificação rápida do estado atual:
>
> ```bash
> curl -s http://127.0.0.1:8001/api/v1/health/providers | jq .
> ```
>
> Cada provider devolve `status` ∈ `ok | warn | fail`, mais `detail`,
> `env_vars` e `impacts`. Status global é o pior dos providers; resposta é
> `200` para `ok`/`warn` e `503` para `fail`.

---

## Como setar / atualizar

- **Replit:** Tools → Secrets → adicione a chave/valor. Ele entra no `env` do
  processo no próximo restart do workflow `lia-backend`.
- **Local (`.env`):** edite `lia-agent-system/.env` e reinicie o uvicorn.
- **Produção:** secret manager (Doppler — `SECRETS_PROVIDER=doppler` +
  `DOPPLER_TOKEN`). Nunca comitar valores reais no repositório.

Após mudar qualquer secret, **reinicie o workflow `lia-backend`** para que o
healthcheck de boot reflita o novo estado nos logs.

---

## Sourcing externo

### `PEARCH_API_KEY`  *(obrigatório p/ busca global)*
- **Função:** autentica chamadas ao serviço Pearch AI (190M+ perfis).
- **Onde é consumida:** `app/domains/sourcing/services/pearch_service.py`.
- **Status quando ausente:** `fail`. `include_pearch=true` em
  `/api/v1/search/candidates` cai imediatamente em circuit-open; busca usa
  fallback RAG local (pgvector) ou Apify (se habilitado).
- **Companion:** `PEARCH_API_URL` (default `https://api.pearch.ai`).

### `APIFY_API_KEY` *(ou `APIFY_TOKEN`)*
- **Função:** autentica chamadas a actors da Apify usados como fallback de
  sourcing (LinkedIn scraping etc.).
- **Onde é consumida:** `app/domains/sourcing/services/apify_search_service.py`,
  `app/domains/sourcing/services/apify_service.py`.
- **Status:** `ok` se presente **e** `APIFY_SEARCH_FALLBACK_ENABLED=true`.
- **Nota:** alguns componentes legados esperam `APIFY_TOKEN`. Se possível,
  setar **as duas** com o mesmo valor.

### `APIFY_SEARCH_FALLBACK_ENABLED`
- **Função:** flag que liga/desliga o fallback do Apify quando o circuit do
  Pearch está aberto.
- **Default:** `false` (fallback **desligado**).
- **Status:** `warn` se a key existe mas a flag é falsa; `fail` se a flag é
  verdadeira mas a key está ausente.

---

## LLM providers

A factory (`app/shared/providers/llm_factory.py`) usa a chain default
`anthropic → gemini → openai`. **Pelo menos uma** chave precisa estar setada
ou o backend recusa subir em produção.

### `ANTHROPIC_API_KEY` *(ou `AI_INTEGRATIONS_ANTHROPIC_API_KEY`)*
- **Função:** Claude (provider primário do orchestrator e da maioria dos
  agentes ReAct).
- **Status quando ausente:** `warn` (fallback Gemini/OpenAI assume).

### `OPENAI_API_KEY` *(ou `AI_INTEGRATIONS_OPENAI_API_KEY`)*
- **Função:** embeddings default (`embedding_openai`), RAGPipelineService,
  RubricEvaluationService quando `provider=openai`.
- **Status quando ausente:** `warn`. Embeddings/rubric podem cair em fallback,
  mas RAG sem embeddings da OpenAI devolve resultados degradados.

### `GEMINI_API_KEY` *(ou `GOOGLE_API_KEY` / `AI_INTEGRATIONS_GEMINI_API_KEY`)*
- **Função:** Google Gemini — fallback intermediário da chain.
- **Status quando ausente:** `warn`.

### `LLM_DEFAULT_PROVIDER`
- **Função:** override do provider primário usado pelo `ProviderContainer`
  (default `gemini`).

---

## Auth & sessão

### `WORKOS_API_KEY` + `WORKOS_CLIENT_ID`
- **Função:** SSO oficial via WorkOS (emissão de `lia_access_token`,
  WebSocket token).
- **Status quando ausentes:** `warn`. SSO indisponível; sessão depende
  exclusivamente do atalho `DEV_MODE` — bom para Replit dev, **inaceitável**
  em produção.

### `LIA_DEV_MODE` + `LIA_DEV_API_KEY`
- **Função:** atalho de auth. Quando `LIA_DEV_MODE=true` **e** o request
  envia `X-Dev-Api-Key: $LIA_DEV_API_KEY`, o `AuthEnforcementMiddleware`
  injeta um usuário sintético com `company_id=DEMO_COMPANY_UUID`.
- **Onde é consumida:** `app/middleware/auth_enforcement.py`.
- **Regras:**
  - `APP_ENV=production` + `LIA_DEV_MODE=true` ⇒ **fail**. Desligue.
  - Dev + flag ligada sem key ⇒ `warn` (middleware vai rejeitar).
  - Dev + flag ligada com key ⇒ `ok`.

### `APP_ENV`
- **Função:** controla `_is_dev_environment()` em vários módulos
  (middleware, scheduler, healthcheck) e ativa o seed do demo user.
- **Valores aceitos:** `development` (default), `dev`, `local`, `staging`,
  `production`, `prod`.

---

## Comportamento agregado

| Cenário | Boot log | `/health/providers` | Impacto no usuário |
|---|---|---|---|
| Tudo OK | `Overall: OK` | `200 {"overall":"ok"}` | Nenhum — busca híbrida total |
| Pearch sem chave, Apify ligado | `Overall: FAIL` (pearch fail) | `503 {"overall":"fail"}` | Busca global sem Pearch; fallback Apify cobre parcialmente |
| OpenAI sem chave | `Overall: WARN` | `200 {"overall":"warn"}` | RAG/embeddings degradados; LLM ainda funciona via Gemini/Claude |
| Nenhum LLM | `llm_chain: FAIL` | `503` | Agentes não respondem; em produção o boot **aborta** |
| WorkOS faltando + DEV_MODE off | `workos: WARN`, `dev_mode: WARN` | `200 {"overall":"warn"}` | Login não emite token; usuário fica em loop de relogin |

---

## Smoke test pós-mudança

1. Reinicie o workflow `lia-backend`.
2. Confira os logs — deve aparecer o bloco `───── Provider healthcheck (boot) ─────`
   listando cada provider com ícone e status.
3. `curl -s http://127.0.0.1:8001/api/v1/health/providers | jq .overall`
   deve coincidir com a linha `Overall:` do log.
4. Se `pearch.status=ok`: `curl -X POST .../api/v1/search/candidates` com
   `include_pearch=true` deve responder sem `degraded_sources` listando
   `pearch_search`.

---

## Causas raiz cobertas

Este runbook + healthcheck endereçam diretamente os itens **#6, #7 e #9** da
auditoria `docs/audits/candidates-root-cause-2026-04-16.md`:

- #6 — Pearch/Apify sem chaves/flag no Repl.
- #7 — `OPENAI_API_KEY` ausente derruba embeddings/rubric.
- #9 — `STRICT_RAILS_ONLY` / `LIA_DEV_MODE` mal configurados em produção.

---

## Apêndice: `/api/auth/ws-token` 503 em dev

**Sintoma**: logs do `dev-server` mostram `GET /api/auth/ws-token 503` em
loop quando a página é aberta.

**Diagnóstico** (Task #298): a rota só devolve 503 com
`code: 'dev_auto_login_failed'` quando o backend FastAPI não responde a
`POST /api/v1/auth/login` para o usuário demo. Causas comuns:

1. **Backend ainda subindo** (cold-start até ~15s após restart). 503 é
   transitório; o cliente faz backoff (`useChatSocket`/`useFloatStreaming`
   tentam 3x com backoff exponencial 1.5s/3s/6s).
2. **Credenciais `DEV_AUTO_LOGIN_EMAIL`/`DEV_AUTO_LOGIN_PASSWORD` inválidas**
   ou usuário demo ausente do banco. Resolvido via seed do `demo_user` no
   `app/auth/dependencies.py:ensure_demo_user`.
3. **Backend fora do ar** (workflow `lia-backend` parado). 503 vira
   permanente até restart. Loop visível = página recarregando.

**Mitigação aplicada**:
- Respostas de erro do `/api/auth/ws-token` agora carregam
  `Cache-Control: no-store`, evitando que browsers/proxies guardem 503
  transitório e contaminem ciclos de relogin.
- `useFloatStreaming` foi alinhado com `useChatSocket` (3 tentativas com
  backoff). Antes era single-shot, deixando o token undefined até unmount.

**Workaround se persistir em dev**:
1. Restart `lia-backend` (`Run` na aba Workflows ou `Shell`:
   `pkill -f uvicorn; ...`).
2. Confirmar que `/api/v1/auth/login` responde 200 com token via
   `curl -X POST http://127.0.0.1:8001/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"demo@wedotalent.com","password":"demo123"}'`.
3. Limpar cookie `lia_access_token` no browser e recarregar — força
   re-emissão via dev-auto-login.

Se mesmo assim continuar, abra task linkada a esta seção: trata-se de
problema novo, não do loop documentado pela auditoria #287.
