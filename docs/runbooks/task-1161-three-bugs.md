# Runbook — Task #1161: Wizard E2E 3 bugs bloqueantes

> Última revisão: 2026-05-17 — Task #1161
>
> Este runbook documenta a causa raiz, fix e sentinelas das 3 regressões
> que travavam pw-cenario-B/C/D simultaneamente. Use-o quando vir:
> - 401 do Anthropic em dev/staging mesmo com tenant key válida no banco
> - `WizardSessionService` respondendo só "Houve um problema, tente novamente"
>   sem traceback no log
> - 500 em `/api/v1/company/culture-*` com body genérico e sem stack server-side

---

## Bug A — Anthropic 401 quando o callsite passa `api_key` explícita

**Sintoma.** Em dev/staging, `ChatAnthropic(api_key=<tenant_key>)` retorna 401
mesmo com `AI_INTEGRATIONS_ANTHROPIC_BASE_URL=https://modelfarm.local/...`
configurada. Em produção (sem a env var) o caminho funciona.

**Causa raiz.** Em `lia-agent-system/app/shared/llm_bootstrap.py`, o patch
do SDK `anthropic.Anthropic.__init__` aninhava a injeção de `base_url` dentro
do mesmo bloco `if "api_key" not in kwargs:` que cuidava da injeção de
api_key. Quando o LangChain (`ChatAnthropic`) passa `api_key=...` explícito
para o SDK, o bloco inteiro era pulado — incluindo `base_url`. O cliente
batia direto na API pública (`https://api.anthropic.com`), que rejeitava a
chave de dev → 401.

**Fix.** Extraído helper `_inject_anthropic_env(kwargs)` com DUAS condições
independentes:
- `api_key` continua gated em `if "api_key" not in kwargs` (não sobrescreve
  intenção do caller).
- `base_url` injeta SEMPRE que `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` está
  setada e o caller não passou `base_url` explícito.

Em produção a env var fica unset → no-op. Em dev/staging todo cliente
Anthropic (sync, async, via LangChain ou direto) passa pelo modelfarm proxy.

**Sentinela.** `tests/integration/llm/test_anthropic_base_url_injection_t_1161.py`
- `test_base_url_injected_when_caller_passes_explicit_api_key` — reproduz o
  callsite real do `ChatAnthropic`.
- `test_base_url_injected_when_caller_passes_nothing` — caminho original.
- `test_base_url_noop_when_env_unset` — produção (sem proxy).
- `test_inject_helper_uses_unconditional_base_url` — AST assertion que o
  bloco `if base_url and "base_url" not in kwargs:` NÃO está aninhado dentro
  de `if "api_key" not in kwargs:`. Garante que ninguém regenere o bug por
  refactor.

### Bug A — Addendum Task #1164 (Bug D, root cause real do "IA degradada")

**Sintoma residual.** Mesmo com a fix de Bug A aplicada, o wizard de criação
de vaga seguia disparando `_fallback_enrichment` ("O serviço de IA está
degradado neste momento, então gerei um enriquecimento mínimo (qualidade
estimada: 20%)") em 100% dos turnos. Logs do `lia-backend` mostravam
`POST https://api.anthropic.com/v1/messages` retornando 401 enquanto os
classifiers (supervisor/gates/intake/meta_helper) continuavam OK via
`localhost:1106/modelfarm/anthropic`.

**Causa raiz.** `langchain_anthropic.ChatAnthropic._client_params` (linha
1617 em `chat_models.py`) SEMPRE faz `"base_url": self.anthropic_api_url`,
com o default vindo de `from_env(["ANTHROPIC_API_URL", "ANTHROPIC_BASE_URL"], default="https://api.anthropic.com")`.
Em dev/staging nenhum desses env vars está setado, então `ChatAnthropic`
construía `anthropic.Client(api_key=..., base_url="https://api.anthropic.com")`.
O guard de Bug A (`if base_url and "base_url" not in kwargs:`) então
PULAVA a injeção porque `base_url` já estava em kwargs (default Anthropic),
e o cliente saía batendo direto na API pública com a wrapper key →
401. Os classifiers escapavam porque criam `anthropic.Anthropic(...)`
direto (sem o wrapper LangChain) e populam `base_url` explicitamente a
partir do env var.

**Fix.** Em `_inject_anthropic_env` o guard ficou:
```python
base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
if base_url:
    current = kwargs.get("base_url")
    if current is None or _is_default_anthropic_base_url(current):
        kwargs["base_url"] = base_url
```
O helper `_is_default_anthropic_base_url` enumera os defaults upstream
(`https://api.anthropic.com` com/sem trailing slash). Qualquer outro
valor passa intocado (respeita override explícito do caller).

**Sentinela.** `tests/integration/llm/test_anthropic_base_url_injection_t_1164.py`
- `test_base_url_overridden_when_kwargs_has_anthropic_default` — reproduz o
  callsite real do `ChatAnthropic._client` (kwargs já com o default).
- `test_base_url_overridden_when_kwargs_has_anthropic_default_with_trailing_slash`
  — variante com trailing slash.
- `test_explicit_non_default_base_url_is_preserved` — override do caller
  com URL não-default é respeitado.
- `test_helper_detects_default_anthropic_base_urls` — coverage runtime do
  helper.
- `test_inject_helper_overrides_default_anthropic_base_url` — AST guard
  exigindo a chamada de `_is_default_anthropic_base_url` no helper.

---

## Bug B — `NotImplementedError` silenciado em `aresume_with_message`

**Sintoma.** No wizard, ao retomar uma sessão pausada em HITL, o usuário
recebe uma resposta de fallback genérica ("Houve um problema, tente
novamente") sem nenhum erro no log do backend. Diagnóstico fica impossível.

**Causa raiz.** Em `WizardSessionService.process_message`, o `try/except`
que envolve `wiz_g.aresume_with_message(...)` capturava `Exception` com
`logger.error(f"... {type(exc).__name__}")` — só o NOME do tipo, sem stack
trace. Exceções como `NotImplementedError` vindas de stubs legados
profundos no graph eram silenciadas, e `_emit_silent_fallback` mascarava
o estado real do checkpoint LangGraph.

**Fix.** No catch em `app/domains/job_creation/services/wizard_session_service.py`
(handler de `aresume_with_message`):
1. Substituído `logger.error(...)` por `logger.exception(...)` — escreve
   o traceback COMPLETO no log do backend.
2. Adicionado `sentry_sdk.capture_exception(inv_exc)` em try/except
   defensivo (Sentry pode não estar configurado em test envs).
3. AMBOS rodam ANTES de `_emit_silent_fallback` — assim o fallback não
   ofusca a causa raiz que ele está mascarando.

**Sentinela.** `tests/integration/agents/test_wizard_resume_traceback_t_1161.py`
- `test_resume_catch_calls_logger_exception` — AST exige `logger.exception(`
  no handler.
- `test_resume_catch_calls_sentry_capture` — AST exige
  `sentry_sdk.capture_exception(`.
- `test_logger_exception_runs_before_silent_fallback` — AST exige que o
  índice de `logger.exception(...)` no body do handler venha ANTES do
  índice de `_emit_silent_fallback(...)`.

**Root cause REAL (addendum 2026-05-17).** Com `logger.exception(...)` o
traceback completo apareceu no stdout do backend e revelou a verdadeira
origem do `NotImplementedError`:

```
File ".../langgraph/checkpoint/base/__init__.py", line 271, in aget_tuple
    raise NotImplementedError
```

A classe sync `langgraph.checkpoint.postgres.PostgresSaver` herda
`aget_tuple` do stub abstrato `BaseCheckpointSaver`. Como
`aresume_with_message` faz `await self._graph.ainvoke(Command(resume=...))`,
o `AsyncPregelLoop.__aenter__` chama `await checkpointer.aget_tuple(...)`
e bate no stub — `NIE` silenciado pelo `_emit_silent_fallback`. Em
produção, `get_checkpointer()` retornava o mesmo `PostgresSaver` sync,
então o bug atinge prod (não só dev).

**Fix.** `libs/agents-core/lia_agents_core/checkpointer.py`:
- Adicionado helper `_supports_async(saver)` que detecta se `aget_tuple`
  foi sobrescrito em algum ancestral antes de bater no
  `BaseCheckpointSaver`.
- `get_checkpointer()` agora aplica esse guard: em DEV, cai para
  `MemorySaver` (= `InMemorySaver`, que implementa async); em
  prod/staging, levanta `RuntimeError` exigindo migração para
  `AsyncPostgresSaver`.

**Sentinela complementar.** `tests/integration/agents/test_checkpointer_async_support_t_1161.py`
- `test_supports_async_helper_is_defined` — AST garante a presença do helper.
- `test_get_checkpointer_calls_supports_async_guard` — AST exige a
  chamada de `_supports_async(...)` dentro de `get_checkpointer()`.
- `test_runtime_checkpointer_supports_aget_tuple` — runtime: o saver
  efetivamente retornado em dev deve sobrescrever `aget_tuple`.

---

## Bug C — `/company/culture-*` retorna 500 vazando `str(e)` (raiz: ResponseValidationError)

**Sintoma duplo:**
1. **Information disclosure** (threat model): 500 com `detail=str(e)`
   vazando paths, queries SQL e stack hints para o cliente.
2. **Root cause real**: `fastapi.exceptions.ResponseValidationError` em
   `GET /api/v1/company/culture-profile/{company_id}`, payload
   `{'type': 'string_type', 'loc': ('response', 'default_languages', 0),
   'input': {'code': 'pt-BR', 'label': 'Português (Brasil)'}}`.

**Causa raiz.** O schema `CompanyCultureProfileBase.default_languages`
tipa `list[str]`, mas o banco contém objetos `[{code, label, level,
required}]` salvos pelo UI antigo (`app/data/ui_actions_data.json`
seed e variantes). Pydantic v2 rejeita a serialização → 500. Os 19
catches em `app/api/v1/company_culture.py` e `company_culture_config.py`
encadeavam `detail=str(e)` e `logger.error(f'... {e}')`, então:
- Cliente recebia o texto do `ResponseValidationError` (interno).
- Backend log NÃO tinha traceback completo (`.error` em vez de `.exception`).

**Fix em 2 camadas:**

1. **HTTP layer (information disclosure)** — Script batch substituiu
   nos 2 arquivos:
   - `detail=str(e)` → `detail="internal error"` + `raise ... from e`
   - `logger.error(f"... {e}")` → `logger.exception("...")`

2. **Schema (root cause da 500)** — Adicionado em
   `app/schemas/company_culture.py`:
   - Helper `_normalize_list_of_strings(v)` que aceita lista mista
     (`str | dict | None`) e devolve `list[str]`. Para dicts, extrai
     `code` → `name` → `label` → `value`. Defesa em profundidade.
   - `@field_validator(..., mode="before")` aplicado em `values`,
     `evp_bullets`, `core_competencies`, `analyzed_pages`, `locations`,
     `tech_stack`, `default_languages` na `CompanyCultureProfileBase`.

**Sentinela.** `tests/integration/security/test_culture_no_internal_leak_t_1161.py`
- `test_no_str_e_in_http_exception_detail[modpath]` — AST proíbe
  `HTTPException(detail=str(e))` e `detail=f"... {e}"` nos dois módulos.
- `test_catch_all_uses_logger_exception[modpath]` — AST exige
  `logger.exception(` em todo `except Exception` que termina em 500.
- `test_culture_profile_schema_normalizes_dict_items` — coverage real
  do validator: payload com mix de `dict`/`str`/`None`/`""` produz
  exatamente `list[str]`.

---

## Comandos CI / Validação local

```bash
# Sentinelas offline (rodam sem DB/Redis):
cd lia-agent-system
python3 -m pytest \
  tests/integration/llm/test_anthropic_base_url_injection_t_1161.py \
  tests/integration/agents/test_wizard_resume_traceback_t_1161.py \
  tests/integration/security/test_culture_no_internal_leak_t_1161.py \
  -v

# E2E (precisa lia-backend + dev-server):
cd plataforma-lia
APP_ENV=development pnpm playwright test \
  e2e/tests/wizard/03-vaga-executiva.spec.ts \
  e2e/tests/wizard/08-hitl-correcao.spec.ts \
  e2e/tests/wizard/09-edge-cases.spec.ts \
  --project=desktop-chrome --reporter=list

# Ou via workflows Replit:
#   pw-cenario-B  → 03-vaga-executiva.spec.ts
#   pw-cenario-C  → 08-hitl-correcao.spec.ts
#   pw-cenario-D  → 09-edge-cases.spec.ts (com LIA_JD_ENRICHMENT_TIMEOUT_S=0.001)
```

## Rollback (emergency only)

| Bug | Rollback | Risco |
|-----|----------|-------|
| A | Reverter `_inject_anthropic_env` p/ aninhamento original | Volta o 401 em dev/staging |
| B | Reverter `logger.exception` p/ `logger.error` | Volta a opacidade do silent fallback |
| C (HTTP) | Reverter `detail="internal error"` p/ `detail=str(e)` | Volta o leak de PII/internals |
| C (schema) | Remover `field_validator` em `CompanyCultureProfileBase` | Volta o 500 no GET culture-profile |

Não há flag de feature: os 3 fixes são corretos por construção e
cobertos por sentinela. Rollback só justificável em incidente onde
um dos fixes prove ter introduzido outra regressão.
