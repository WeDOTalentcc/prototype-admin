> ## ⚠️ CANONICAL DE PRODUÇÃO
>
> **Replit `lia-agent-system/` é canonical de produção** (decisão Paulo 2026-05-23). NÃO é legacy.
>
> - Edits aqui = produção viva
> - Fonte de verdade para 7 agentes ReAct (Wizard, Pipeline, Sourcing, Talent, JobsManagement, Kanban, Policy) + voice channels (Twilio PSTN/VoIP/Gemini Live) + triagem candidato público (`/api/v1/triagem/{token}`) + WhatsApp (Meta + Twilio)
> - `recruiter_agent_v5` NÃO substitui este sistema no contexto UI/candidato-facing
> - Statements legacy em outros CLAUDE.md são outdated — ignorar
>
> Ver `/workspace/CLAUDE.md` para racional completo.

---

# CLAUDE.md — lia-agent-system

> Regras canônicas para agentes IA trabalhando neste repo.
> Não é doc humano — é **harness layer**: guides que reduzem P(erro) na geração de código.
> Princípio: **Agent = Model + Harness** (Hashimoto 2026). Erros recorrentes viram regras aqui.

## Não-negociáveis (multi-tenant + LGPD + fairness + secrets)

Estas regras vêm do CLAUDE.md global do usuário. **Aplicam a 100% do código.**

1. **Multi-tenant — `company_id`**: todo modelo que persiste dado de cliente DEVE ter coluna `company_id`. Toda query DEVE filtrar por `company_id`. **`company_id` vem do JWT/sessão/User-lookup, NUNCA do payload da request.** Sem exceção.
2. **LGPD**: dados sensíveis (raça, religião, gênero, etnia, estado civil, saúde) NÃO podem ser coletados nem usados em decisões de IA. Logs NÃO podem conter PII (CPF, RG, telefone, email crus) — sensor `G4: no-pii-in-logs` enforce.
3. **Fairness**: prompts que rankam/filtram candidatos DEVEM passar por `FairnessGuard`. Pattern canônico em `app/domains/communication/agents/communication_react_agent.py` (FAR-2, ACH-026).
4. **Secrets**: zero hardcoded. Tudo via env vars + Pydantic Settings.

## Anti-patterns proibidos (sensores existentes detectam)

| Anti-pattern | Por quê | Sensor |
|---|---|---|
| `getattr(model_row, "column_name", None)` | Mascara schema bug silently — fix P0-1 (auditoria 2026-04-26: `_resolve_company_id` retornava `None` pra todo Teams message) | `G6: no-getattr-on-models` (`scripts/check_no_getattr_on_models.py`) |
| Raw SQL em controllers `app/api/v1/*.py` | Mistura camada — repository é canônico | `G1: no-sql-in-controllers` |
| PII em log statements | LGPD violation | `G4: no-pii-in-logs` |
| Endpoint sem `response_model=` | Type contract quebrado | `G2: response-model-required` |
| Import de path proibido (ADR-012) | Camadas violadas | `G5: no-forbidden-imports` |
| `require_company=False` sem justificativa documentada | Bypass multi-tenant não rastreável | `F8: require-company-exemptions` |
| `try: ... except Exception: pass` | Silent failure destrói sensor — falhar alto > capturar e descartar | `G7: no-silent-swallow` (`scripts/check_no_silent_swallow.py` — warn-only). Ver seção "Exception handling discipline (R-003)" abaixo. |

## Regras canonical-fix

- **Fix sempre no produtor, nunca no consumidor.** Se múltiplos callers passam dado errado, fix está no schema/contrato — não em cada caller.
- **Schema é fonte de verdade.** Modelo SQLAlchemy + Pydantic types > comentários > docstrings.
- **Não duplicar.** Antes de criar função/serviço novo, `grep` por nome similar. Reuso > NIH.
- **Não inventar tipos.** `String(255), nullable=True, indexed` em `User.company_id`? Replicar exato em outras colunas tenant.

## Exception handling discipline (R-003)

`except Exception:` silencioso (`pass` ou `return` sem `logger.*`) é proibido em:
- `app/orchestrator/**`
- `app/shared/{llm,compliance,providers}/**`
- `app/middleware/**`
- `libs/agents-core/**`

**Pattern hot path (debug — não polui mas registra):**
```python
except Exception as exc:
    logger.debug("[component] operation failed: %s", exc, exc_info=True)
    return None  # mantém comportamento existente
```

**Pattern compliance/fairness (warning — nunca silenciar):**
```python
except Exception as exc:
    logger.warning("[component] failed (compliance): %s", exc, exc_info=True)
    # ainda fail-open por design, mas registrado
```

**Aceitáveis (excluir do gate):**
- `except ImportError:` para optional deps
- `except asyncio.CancelledError:` cancelamento legítimo
- `except ValueError:` em loop com `continue` (skip-on-invalid)

Sensor: `scripts/check_no_silent_swallow.py` (warn-only). Promote para CI gate em R-003.2 (Wave 3) quando 25 sites adiados forem fixados.

## Regras de organização de branch e BRANCH_MAP

### Guide 1 — Branch por tema (feedforward, computacional)

Todo novo tema/feature/épico abre branch própria a partir de `main`:
- Padrão: `feat/<tema>-<descricao-curta>` ou `fix/<tema>-<descricao-curta>`
- **Proibido acumular temas distintos** em uma única branch de sprint
- Exceção: bug fix dentro do tema atual da branch ativa
- Após merge: branch de feature pode ser deletada; tag `milestone/<descricao>` preserva o ponto

Exemplos válidos: `feat/teams-integration`, `feat/pr-a-rail-a-metadata`, `fix/wsi-scoring-cast`

Exemplo proibido: commitar Teams + LIA Maturity + Rail features na mesma branch de sprint (caso histórico de `feat/orch-migration-sprint-I` — não repetir).

### Guide 2 — `docs/BRANCH_MAP.md` é canônico (feedforward, computacional)

`docs/BRANCH_MAP.md` é o **mapa canônico do repositório**. Toda mudança que adiciona tema novo OU milestone significativo OBRIGA atualização do mapa antes do commit final do tema.

Para cada nova entrega:
1. Adicionar nova seção §N em `docs/BRANCH_MAP.md` (se for tema novo)
2. Criar tag `milestone/<descricao>` se a entrega fechar um marco
3. Atualizar tabela de Cross-references se um doc canônico novo foi criado em `docs/`
4. Commit message do mapa: `docs(nav): BRANCH_MAP — <descrição>`

Antes de propor qualquer mudança não-trivial, agentes IA DEVEM ler `docs/BRANCH_MAP.md` para identificar tema, milestones e docs canônicos cruzados (templates de prompt no Apêndice A do mapa).

### Sensor — branch-map-theme-check (ativo, computacional)

Implementado como hook commit-msg via pre-commit framework. Bloqueia commits
em branches genéricas (sprint accumulators) cujo tema declarado no commit
prefix não aparece em `docs/BRANCH_MAP.md`.

- **Script:** `scripts/check_branch_map.py`
- **Config:** `.pre-commit-config.yaml`
- **Doc:** `scripts/README_HOOKS.md`
- **Instalação (1x por dev):** `pip install pre-commit && pre-commit install --hook-type commit-msg`

Bypass intencional (apenas em urgência): `git commit --no-verify`.


## TDD obrigatório para fixes de P0/P1

Padrão: red → green → refactor. Toda fix de P0/P1 da auditoria DEVE incluir teste que falha antes da fix e passa depois. Sem teste = fix não foi feita.

**Pattern de test paths:**
- Schema check: `tests/integration/test_<feature>_<area>.py` com classe `Test<Model>Schema`
- Red team: `tests/security/test_red_team_<eixo>.py` — adicionar classe `Test<Canal>Boundary` quando expandir cobertura

## Componentes de harness deste repo

1. **Planning loop**: ReAct via `lia_agents_core` (cap iterations, condition stop)
2. **Tool layer**: `app/tools/registry.py` + `app/tools/executor.py`. Tools tipadas via `ToolDefinition`.
3. **Context management**: `app/orchestrator/registry.py` (V1/V2 — orchestrator-migration sprint III)
4. **Memory**: `app/services/conversation_memory_service.py`
5. **Sandbox**: subprocess isolation em `app/tools/executor.py`
6. **Guides**: este arquivo + módulos production-quality em `~/.claude/commands/production-quality/`
7. **Sensors**: 10 hooks em `.pre-commit-config.yaml` + suite pytest com red-team em `tests/security/`
8. **Permission gating**: `Depends(get_current_user)` + `require_company` (F8 enforce)
9. **Error handling**: 4-tier — `app/shared/errors.py` (LIAIntegrationError etc.)
10. **Observability**: OTEL `@trace_span` (orchestrator-migration sprint III.C aplicou em V1/V2)
11. **Serving layer**: FastAPI + WebSocket + RabbitMQ consumer (`MessageWorker` se aplicável)

## Auditoria pendente (referência viva)

Auditoria deep mais recente: **AUDITORIA_TEAMS_2026-04-26.md** (em `/Users/paulomoraes/Documents/Python/`).

Wave 1 (em progresso):
- ✅ **W1.1** P0-1 multi-tenant `company_id` em `TeamsConversation` — commit `f7f972882` + auto-commit `2adac0f2c`
- ⏳ **W1.2** P0-2 remover `company_id` de `TeamsWebhookPayload`
- ⏳ **W1.3** P0-3 tenant filter em `/webhook/audit-logs`
- ⏳ **W1.4** P0-4 8 testes red team Teams (PII, fairness, LGPD, prompt-injection, signature, etc.)
- ⏳ **W1.5** decorator `@require_tenant_filter` reusável

## Quando esta regra atualiza

Toda nova regra adicionada aqui DEVE:
1. Vir de erro observado (não regra preventiva genérica)
2. Ter sensor computacional correspondente (linter, teste, hook)
3. Ter mensagem de erro otimizada para LLM (não só humano)
4. Princípio Hashimoto: nunca mais aquele erro específico


## Débito harness conhecido (G6 — 24 matches detectados em 2026-04-26)

O sensor `G6: no-getattr-on-models` descobriu 24 ocorrências do anti-pattern
`getattr(<model_row>, "<column>", <default>)` em produção. Cada uma é potencialmente
um bug do tipo P0-1 (mascara coluna ausente / quebrada). Hook está em **warn-only**
até cleanup. Ordem sugerida (alta → baixa criticidade):

| Path | Ocorrências | Wave alvo |
|---|---|---|
| `app/api/v1/auth.py` | 3× user.company_id | W1.6 (multi-tenant auth) |
| `app/api/v1/teams.py:1499` | 1× user.company_id | W1.2 (Teams) |
| `app/api/v1/rails_sync.py` | 3× | W1.7 (rails sync) |
| `app/api/v1/bulk_actions.py` | 1× | W1.7 |
| `app/api/v1/candidates/candidates_crud.py` | 1× candidate.company_id | W1.6 |
| `app/jobs/tasks/communication.py` | 1× user.company_id | W1.6 |
| `app/domains/sourcing/services/sourcing_pipeline_service.py` | 2× job.company_id | W1.6 |
| `app/domains/sourcing/tools/query_tools.py` | 1× | W1.6 |
| `app/domains/job_management/tools/job_tools.py` | 1× | W1.6 |
| `app/domains/cv_screening/services/personalized_feedback_service.py` | 2× | W1.6 |
| `app/domains/cv_screening/tools/candidate_tools.py` | 2× candidate.company_id | W1.6 |
| `app/domains/communication/services/teams_sso_service.py` | 2× conv.* | W1.2 (Teams) |
| `app/domains/analytics/services/predictive_analytics_service.py` | 1× | W1.6 |
| `app/domains/recruiter_assistant/services/conversation_memory.py` | 1× | W1.6 |
| `app/shared/channels/adapters/email_adapter.py` | 2× message.company_id | W1.6 |

Quando o cleanup completar (cada wave fixa o seu subset), promover G6 para
**block-only** removendo `|| true` do `entry:` em `.pre-commit-config.yaml`.

Princípio Hashimoto: nunca mais P0-1 em modelo nenhum.


## Anatomy of a canonical agent / tool / domain

> **Decisão (auditoria 2026-04-27):** todo novo agent / tool / domain DEVE seguir este pattern.
> Modelos novos (Claude, agentes IA, devs) leem este checklist + snippets e replicam idêntico.
> Sensor G7 (`scripts/check_agent_compliance.py`) valida automaticamente em pre-commit.
> Skill `create-canonical-agent` orquestra a criação seguindo este pattern.

### 1. Anatomy of a canonical agent

**Localização canônica:** `app/domains/<domain>/agents/<domain>_react_agent.py`

**Checklist:**

1. ✅ Herda de `LangGraphReActBase` + `EnhancedAgentMixin`
2. ✅ Decorado com `@register_agent("<domain>", aliases=[...])`
3. ✅ Define `DOMAIN_INSTRUCTIONS` apontando para `app/prompts/domains/<domain>.yaml`
4. ✅ Em `process(input)` — sequência canon:
   - **FairnessGuard.check** antes de qualquer LLM call (FAR-2)
   - **HITL gate** para mensagens sensíveis (AUD-4)
   - **audit_service.log_decision** ao concluir (ACH-026)
   - **company_id** sempre de `input.company_id` (NUNCA payload externo)
5. ✅ Tools via `tool_registry` com `@tool_handler("domain")` — NÃO langchain `@tool` decorator
6. ✅ LLM via `get_provider_for_tenant(tenant_id)` — NÃO singleton global
7. ✅ `@trace_span` em hot-path (OTEL)
8. ✅ Tests em `tests/domains/<domain>/test_<domain>_react_agent.py` cobrindo: schema, FairnessGuard, PII, audit

**Snippet canon — esqueleto da classe:**

```python
"""<Domain> ReAct Agent — <descrição curta>.

Domain: <domain>
"""
import logging

from lia_agents_core.agent_interface import AgentAction, AgentInput, AgentOutput
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.<domain>.agents.<domain>_system_prompt import <DOMAIN>_DOMAIN_SPECIFIC
from app.domains.<domain>.agents.<domain>_tool_registry import get_<domain>_tools
from app.shared.agents.agent_registry import register_agent

logger = logging.getLogger(__name__)


@register_agent("<domain>", aliases=[...])
class <Domain>ReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    DOMAIN_INSTRUCTIONS = <DOMAIN>_DOMAIN_SPECIFIC

    # Mensagens que exigem aprovação humana antes de enviar (LGPD + EU AI Act Art.14)
    _HITL_MESSAGE_TYPES = frozenset({...})

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = [t.name for t in get_<domain>_tools()]
        self._setup_enhanced(domain="<domain>")
        logger.info("[<Domain>ReActAgent] Initialized")

    @property
    def domain_name(self) -> str:
        return "<domain>"
```

**Snippet canon — FairnessGuard (FAR-2) — extraído de [communication_react_agent.py:175-200](app/domains/communication/agents/communication_react_agent.py):**

```python
async def process(self, input: AgentInput) -> AgentOutput:
    # FAR-2: FairnessGuard — bloquear mensagens com linguagem discriminatória
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        _fg_result = _fg.check(input.message)
        if _fg_result.is_blocked:
            logger.warning(
                "[<Domain>ReActAgent][FAR-2] FairnessGuard bloqueou mensagem: "
                "category=%s terms=%s",
                _fg_result.category, _fg_result.blocked_terms,
            )
            try:
                await _fg.log_check(
                    result=_fg_result,
                    context="<domain>",
                    company_id=str(input.company_id or ""),
                )
            except Exception:
                pass
            return AgentOutput(
                message=_fg_result.educational_message,
                confidence=1.0,
                metadata={"fairness_blocked": True, "fairness_category": _fg_result.category},
            )
    except Exception as _fg_exc:
        logger.debug("[<Domain>ReActAgent] FairnessGuard check skipped: %s", _fg_exc)
    # ... continuação do process
```

**Snippet canon — audit_service.log_decision (ACH-026) — extraído de [communication_react_agent.py:240-260](app/domains/communication/agents/communication_react_agent.py):**

```python
from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service

await audit_service.log_decision(
    company_id=str(input.company_id or ""),
    agent_name="<domain>_react_agent",
    decision_type="<action_type>",
    action=f"<action_label>",
    decision="<approved|rejected|pending_review>",
    reasoning=["<porquê desta decisão>"],
    criteria_used=[...],
    candidate_id=str(candidate_id) if candidate_id else None,
    human_review_required=False,
    criteria_ignored=list(PROTECTED_CRITERIA),  # ALWAYS pass for LGPD
)
```

**Snippet canon — HITL gate (AUD-4) — para mensagens sensíveis:**

```python
_hitl_approved = input.context.get("hitl_approved", False)
_msg_type = input.context.get("message_type", "")
if not _hitl_approved and _msg_type in self._HITL_MESSAGE_TYPES:
    from app.domains.cv_screening.services.hitl_service import hitl_service
    pending_id = await hitl_service.request_approval(
        thread_id=str(input.session_id),
        action="<action_name>",
        description="...",
        data={"company_id": str(input.company_id or ""), ...},
        ws_session_id=str(input.session_id),
        domain="<domain>",
        company_id=str(input.company_id or ""),
    )
    return AgentOutput(message="Aguardando aprovação...", ...)
```

**Snippet canon — PII redaction (LGPD) antes de LLM:**

```python
from app.shared.pii_masking import strip_pii_for_llm_prompt

# ANTES de enviar texto ao LLM (orchestrator, tool, etc.):
clean_message = strip_pii_for_llm_prompt(input.message)
# Use clean_message em prompts; manter input.message original apenas para audit
```

**Snippet canon — LLM Factory (BYOK / Choose Your AI):**

```python
from app.shared.providers.llm_factory import get_provider_for_tenant

# NÃO usar singleton global. Sempre per-tenant:
provider = get_provider_for_tenant(tenant_id=str(input.company_id or "default"))
response = await provider.chat(messages=[...])
```

**Snippet canon — OTEL @trace_span:**

```python
from app.shared.observability.tracing import trace_span

@trace_span("<domain>.process")
async def process(self, input: AgentInput) -> AgentOutput:
    ...
```

### 2. Anatomy of a canonical tool

**Localização canônica:** `app/domains/<domain>/tools/<domain>_<verb>_tool.py` (ou junto em `<domain>_tools.py`)

**Checklist:**

1. ✅ Decorado com `@tool_handler("<domain>")` — NÃO `@tool` legacy do langchain
2. ✅ Async function, type hints estritos em parâmetros
3. ✅ Retorna `dict[str, Any]` com `{"success": bool, "message": str, ...}`
4. ✅ Validação de args obrigatórios no início (early return com `success=False`)
5. ✅ `company_id` recebido de `kwargs` mas DEVE ser cruzado com session do orchestrator (não confiar)
6. ✅ Side-effects (DB write, API external) DEVEM gerar audit_log
7. ✅ Idempotência quando aplicável (idempotency_key em kwargs)

**Snippet canon — extraído de [communication_tool_registry.py:1-50](app/domains/communication/agents/communication_tool_registry.py):**

```python
"""<Domain> Tool Registry — wraps services em ToolDefinition format."""
import logging
from typing import Any
from lia_agents_core.react_loop import ToolDefinition
from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)


@tool_handler("<domain>")
async def _wrap_<verb>_<noun>(**kwargs: Any) -> dict[str, Any]:
    """<Descrição clara da ação>."""
    from app.domains.<domain>.services.<service> import <Service>

    candidate_id = kwargs.get("candidate_id")
    company_id = kwargs.get("company_id")

    if not candidate_id:
        return {"success": False, "message": "candidate_id é obrigatório"}
    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}

    svc = <Service>()
    result = await svc.do_thing(candidate_id=candidate_id, company_id=company_id, **kwargs)
    return {"success": True, "message": "...", "result_id": result.id}


def get_<domain>_tools() -> list[ToolDefinition]:
    """Return list of tools available to the <Domain> agent."""
    return [
        ToolDefinition(
            name="<verb>_<noun>",
            description="<o que faz, when_to_use, when_not_to_use>",
            parameters={
                "candidate_id": {"type": "string", "required": True},
                "company_id": {"type": "string", "required": True},
                # ...
            },
            function=_wrap_<verb>_<noun>,
        ),
        # ...
    ]
```

### 3. Anatomy of a canonical domain

**Localização canônica:** `app/domains/<domain>/`

**Estrutura mínima:**

```
app/domains/<domain>/
├── __init__.py
├── agents/
│   ├── __init__.py
│   ├── <domain>_react_agent.py      # ⭐ CANONICAL
│   ├── <domain>_tool_registry.py    # ⭐ CANONICAL
│   ├── <domain>_system_prompt.py    # ⭐ CANONICAL (reads from prompts/<domain>.yaml)
│   └── <domain>_stage_context.py    # ⭐ CANONICAL
├── services/
│   └── ...
├── tools/                            # opcional — tools de baixo nível
│   └── ...
└── repositories/
    └── ...
```

**Adicionalmente, fora do diretório do domain (pontos de extensão canônicos):**

| Localização | O que adicionar |
|---|---|
| `app/prompts/domains/<domain>.yaml` | System prompt em YAML estruturado |
| `app/orchestrator/config/domain_routing.yaml` | Entry para roteamento de intent → domain |
| `tests/domains/<domain>/test_<domain>_react_agent.py` | Testes canon (ver checklist abaixo) |
| `tests/security/test_red_team_*.py` | Adicionar Teams* class (multi_tenant, PII, fairness, LGPD) |

**Checklist de testes canon para domain novo:**

```python
class Test<Domain>RedTeamPII:
    @pytest.mark.xfail(reason="GAP até impl real", strict=False)
    def test_<domain>_strips_pii_before_llm(self):
        src = inspect.getsource(<Domain>ReActAgent)
        assert "strip_pii_for_llm_prompt" in src or "PIIRedactor" in src

class Test<Domain>RedTeamFairness:
    def test_<domain>_invokes_fairness_guard(self):
        src = inspect.getsource(<Domain>ReActAgent)
        assert "FairnessGuard" in src

class Test<Domain>RedTeamMultiTenant:
    def test_<domain>_uses_input_company_id(self):
        src = inspect.getsource(<Domain>ReActAgent.process)
        assert "input.company_id" in src
        # NUNCA payload.company_id externo

class Test<Domain>RedTeamAudit:
    def test_<domain>_logs_decision(self):
        src = inspect.getsource(<Domain>ReActAgent)
        assert "audit_service.log_decision" in src
```

### 4. Hooks pre-commit que validam isto automaticamente

| Hook | O que valida | Script |
|---|---|---|
| G1 | No SQL em controllers | `check_no_sql_in_controllers.py` |
| G2 | `response_model=` em endpoints | `check_response_models.py` |
| G4 | Sem PII em logs | `check_no_pii_in_logs.py` |
| G5 | Imports proibidos (ADR-012) | `check_forbidden_imports.py` |
| G6 | No `getattr(model, "X", None)` | `check_no_getattr_on_models.py` |
| **G7 (W3.2)** | **Agent compliance: FairnessGuard, audit, PII, llm_factory** | **`check_agent_compliance.py`** |
| F8 | `require_company=False` justificada | `check_require_company_exemptions.py` |
| LLM | LLM Factory enforcement | `check_llm_factory_enforcement.py` |

### 5. Skill orquestradora `create-canonical-agent` (W3.4)

Quando você (ou outro Claude) precisar criar agente novo, invoque:

```
/create-canonical-agent <domain>
```

A skill:
1. Pergunta domain name, descrição, tools necessárias
2. Roda `AgentScaffold.generate(...)` (já existente em `libs/agents-core`)
3. Injeta automaticamente os snippets canon acima
4. Cria `app/prompts/domains/<domain>.yaml` (template)
5. Adiciona linha em `app/orchestrator/config/domain_routing.yaml`
6. Cria `tests/domains/<domain>/test_<domain>_react_agent.py` com testes RED
7. Roda G7 para validar — bloqueia se faltar cross-cutting

Nunca crie agent à mão. Sempre via skill (ou siga este checklist manualmente E rode G7 antes de commit).

### 6. Audit retroativo (W3.3)

Para auditar agents EXISTENTES contra esta anatomy:

```bash
python scripts/audit_agent_compliance.py
# Output: AGENT_COMPLIANCE_MATRIX_<date>.md
# Linhas: cada agent | Colunas: cada cross-cutting | ✅/⚠️/❌
```


## Teams send paths — when to use which (W5.5 canonical doc)

A plataforma tem **4 paths complementares** para enviar mensagens ao Microsoft Teams, com nichos distintos. **NÃO são drift** — cada um resolve um caso de uso específico. Use o correto:

### Decision tree

```
Você precisa enviar algo ao Teams?
│
├─ É resposta a um webhook /messages do Bot Framework?
│   → use simple_teams_bot (teams_simple.py)
│
├─ É proativo (sem ter recebido webhook), mas você TEM ConversationReference armazenada?
│   → use teams_bot (teams_bot.py) — usa BotFrameworkAdapter.continue_conversation
│
├─ É broadcast / notificação para um channel sem bot (via Incoming Webhook URL)?
│   → use TeamsService (teams_service.py) — MessageCard format
│
└─ É integração baixo-nível em domain.py / actions.py / capabilities.yaml?
    → use lia_messaging.teams.send_teams_message (libs/messaging) — helper canon
```

### Detalhamento por path

| Path | Localização | Tecnologia | Quando usar | Auth |
|---|---|---|---|---|
| **`simple_teams_bot`** ⭐ canonical de resposta a webhook | `app/domains/communication/services/teams_simple.py` | httpx + Bot Framework REST | Resposta a `/messages` webhook (chat 1:1) | App credentials (MICROSOFT_APP_ID/PASSWORD) |
| **`teams_bot`** ⭐ canonical de proativo via ConversationReference | `app/domains/communication/services/teams_bot.py` | botbuilder.core SDK (`continue_conversation`) | Notificação proativa em conversa existente armazenada (wsi_abandoned, scheduling_service, triagem_completion) | Idem |
| **`TeamsService`** ⭐ canonical de broadcast Incoming Webhook | `app/domains/communication/services/teams_service.py` | httpx + Incoming Webhook URL | Broadcasts em channels sem bot (jobs/integrations/notifications/weekly_digest). MessageCard format. | TEAMS_WEBHOOK_URL |
| **`lia_messaging.teams`** ⭐ helper baixo nível | `libs/messaging/lia_messaging/teams.py` | httpx wrapper | Usado por `TeamsService` e domain abstractions canonical (capabilities.yaml, domain.py, actions.py) | TEAMS_WEBHOOK_URL |

### Anti-patterns

- ❌ **Não importe `simple_teams_bot` em service de domain (não-API)** — use `teams_bot` ou `TeamsService` conforme caso
- ❌ **Não use `teams_service`/Incoming Webhook para chat 1:1 com bot** — Incoming Webhook é só channel-broadcast
- ❌ **Não use `BotFrameworkAdapter` (teams_bot) sem ter ConversationReference** — ele depende disso
- ❌ **Não criar quinto path** — se aparecer caso novo, valide aqui antes de criar nova abstração

### Convergência futura (não obrigatória, mas opção)

Se time decidir consolidar, pattern alternativo seria:
- Único `MSTeamsChannelAdapter` em `app/shared/channels/adapters/teams_adapter.py` (já existe!) que internamente escolhe o path correto via feature detection (webhook vs ConversationReference vs Incoming Webhook URL).
- Nesse caso, todos os 4 viram implementations privadas atrás do adapter.
- Decisão arquitetural pendente — não fazer agora.

## Convenção shared/observability/ vs shared/services/ (R-005)

Padrão canônico para módulos em `app/shared/`:

- `observability/` — telemetria, alertas, métricas, drift detection, budget tracking, health alerts
- `services/`      — regra de negócio compartilhada cross-domain (não-observability)

**Proibido**: mesmo basename de arquivo em ambos diretórios. Sensor `scripts/check_no_observability_services_dup.py` valida em CI.

Histórico: drift bidirecional acumulado em 6 arquivos (R-005.2 cobre os 5 restantes em Wave 2).


## Required env vars guard (R-006 / ADR-AUTH-001)

Catches the class of bug we hit in 2026-05-20: `FIELD_ENCRYPTION_KEY` missing
in the uvicorn process env → `get_current_user_or_demo` instantiates a `User`
SQLAlchemy model with PII columns → Fernet `_get_fernet()` raises
`EncryptionKeyMissingError` → HTTP 500 on the first request hitting auth fallback.

**Princípio:** app MUST fail at startup, not at first request that needs the var.

**Guide (feedforward):**
- Required: `DATABASE_URL`, `SECRET_KEY` (≥32 chars RFC 7518), `FIELD_ENCRYPTION_KEY` (valid Fernet 44-char base64).
- Optional but recommended dev: `IS_DEVELOPMENT=true`, `REDIS_URL`.
- **Anti-pattern proibido:** `os.getenv("FIELD_ENCRYPTION_KEY", "")` ou `or "default"` — silent fallback destrói o sensor.

**Sensor:** `scripts/check_required_env.py`
- Roda em CI + startup entrypoint.
- `--strict`: valida min_length + parseabilidade Fernet.
- `--dotenv .env`: carrega .env antes de checar (Replit Secrets passam direto).
- Mensagem de erro nomeia o var, o motivo, e o comando exato pra gerar valor válido.
- **Achados ativos 2026-05-20**: `SECRET_KEY` tem 25 chars no .env (precisa ≥32). Tracked como follow-up (rotação requer re-login).

## Schema drift detection (R-007 / ADR-MIGRATIONS-001)

Catches the class of bug `calibration_weights.company_id does not exist`: model
declara coluna, mas migration alembic nunca rodou ou nunca foi criada → query
retorna `asyncpg.exceptions.UndefinedColumnError` em runtime.

**Princípio:** parity model ↔ DB é verificada no boot/deploy, nunca lazy.

**Guide (feedforward):**
- Toda migration que adiciona coluna em tabela tenant-aware DEVE incluir `company_id` simultaneamente.
- Deploy pipeline roda `alembic upgrade head` **antes** de `uvicorn`, com `--sql` dry-run em log para audit trail.
- Multi-tenancy especial: coluna `company_id` em model SEM migration correspondente bloqueia deploy.

**Sensor:** `scripts/check_schema_drift.py`
- Compara `Base.metadata.tables` (lia_config.database) vs `inspect(engine)` da DB live.
- Separa em "in_model_not_in_db" (missing migration) vs "in_db_not_in_model" (stale model).
- Output JSON via `--json` para integração CI.
- **Achados ativos 2026-05-20**: 196 drifts no codebase (116 missing migrations em 21 tables, 80 stale models em 18 tables). Sprint dedicado em follow-up.

## Pydantic schemas single-source (R-008 / ADR-SCHEMAS-001)

Cada feature tem **um** módulo canonical de schemas (ex:
`app/api/v1/<feature>/calibration.py`). Duplicar nome de classe `BaseModel`
entre arquivos é violação — causa silent contract bugs (divergem) ou dead
code (idênticos).

**Guide (feedforward):**
- Antes de criar `class FooRequest(BaseModel)`, `grep -rn "class FooRequest" app/` — se existir, importe ou nomeie diferente (`FooRequestV2`, `FooContext`, etc).
- Nome canônico espelha contrato Rails quando aplicável (`job_vacancy_id` > `vacancy_id`).
- **Anti-pattern proibido:** classe `BaseModel` declarada em ≥2 arquivos com mesmos OU diferentes fields.

**Sensor:** `scripts/check_duplicate_pydantic_schemas.py`
- AST lint, <2s em codebase 181k LOC.
- Distingue identical (= dead code, cleanup mecânico) de divergent (= silent contract bug grave).
- Output otimizado pra LLM: path:line dos 2 sites, diff fields, ação corretiva (`rm class X from Y`).
- **Achados ativos 2026-05-20**: 192 duplicates restantes (122 dead code + 75 divergent). Onda 1 limpou 5 Calibration* dead em `misc_search.py`. Follow-up prioriza 75 divergent (silent contract bugs em produção).

## Wizard canonical endpoint (R-009 / ADR-WIZARD-001)

Único path canônico de criação de vaga conversacional via REST:
**`POST /api/v1/wizard/smart-orchestrate`** (`app/api/v1/wizard_smart_orchestrator.py:152`).

**Mirrors the WS pattern** em `agent_chat_ws.py:1108` (canonical wizard via WebSocket). Mesmo `WizardSessionService.process_message()` + mesmo `JobCreationGraph` (12 stages: intake → jd_enrichment → bigfive → salary → competency → wsi_questions → eligibility → review → publish → calibration → handoff → done).

**Dois modos** no SmartOrchestrateRequest, mutuamente exclusivos:

1. **Normal turn** (default): `message` livre, handler chama `WizardSessionService.process_message(...)` → drives graph forward.

2. **HITL gate resume**: `approval_decision: Literal["approved","rejected"]` + `pending_id: str` set juntos → handler chama `wizard_gate_service.resume_gate(...)` (mesma idempotência CAS + audit row do WS). `message` é ignorado neste modo.

**Guide (feedforward):**
- Pydantic validator pair guard: `approval_decision` e `pending_id` DEVEM ser ambos presentes ou ambos ausentes. Validation message nomeia ambos os fields + as 2 ações válidas para self-correction LLM-readable.
- Frontend `plataforma-lia/src/services/chat-api.ts:188` (`orchestrateWizardMessage`) envia os 3 fields HITL (`approval_decision`, `pending_id`, `approval_comment`) quando user clica Aprovar/Rejeitar no painel.
- **Anti-pattern proibido:** chamar `JobWizardGraph` em `app/domains/job_management/agents/job_wizard_graph.py` (motor legacy, Task #1085 remove a classe inteira). Canonical é `JobCreationGraph` em `app/domains/job_creation/graph.py`.

**Sensor:** `tests/integration/test_wizard_hitl_approval_rest.py`
- 3 cenários: HITL invoca `resume_gate` (not `process_message`), Pydantic guard 422, ValueError → HTTP 200 estruturado (never 500).
- TestClient + AsyncMock têm flakiness ocasional por event-loop cleanup; follow-up migrar pra `httpx.AsyncClient`.

**Endpoint legacy deprecado:** `POST /chat/message` com `domain="wizard"` retornava `internal_error` por NameErrors em helpers nunca implementados. Aposentado pelo refactor 2026-05-20. Frontend nunca chamou esse path.

### Bateria 9 — Wizard canonical E2E sensors (Sprint H/I)

Sensores permanentes em `tests/wizard/test_canonical_e2e_sensors.py`.

Cobertura:
- Initial stage advances past 'initial'
- HITL gate (jd-enrichment) sets `awaiting_confirmation=True`
- `company_id` invariant (multi-tenancy)
- Full 6-turn conversation reaches `complete` / `done` + `job_vacancy_id` populado

Run manualmente:

```bash
LIA_E2E_SENSORS_ENABLED=true \
  python3 -m pytest tests/wizard/test_canonical_e2e_sensors.py -v -s
```

Default: skipped (slow + requires live wizard em `localhost:8001`). Run pre-deploy.

### Sprint R.4 — CI bateria 9 wizard sensors nightly

`.github/workflows/wizard-nightly.yml` runs the canonical wizard E2E sensors
at 06:00 UTC daily (~03:00 BRT). 4 tests (~6 min total) covering:
- intake stage advancement
- HITL gate awaiting_confirmation invariant
- multi-tenancy `company_id` invariant
- full 6-turn conversation → publish → `job_vacancy_id` populated

Manual trigger: GitHub UI → Actions → "Wizard E2E Sensors (Nightly)" → Run workflow.

Failure indicates wizard regression — **block deploy** until the bateria 9
goes green again. Scheduled 30 min after `wizard-e2e-cenario-a.yml` (05:30 UTC)
to escalate LLM load and isolate failure context.

**Secrets required in the GitHub repo settings** (Anderson/team configures
when merging to canonical):
- `AI_PROXY_URL` — Anthropic gateway base URL
- `AI_PROXY_KEY` — Anthropic API key (or proxy key)
- `FIELD_ENCRYPTION_KEY` — Fernet key for encrypted DB fields
- `JWT_SECRET_KEY` — secret used by `app.auth.security.create_access_token`

**Meta-sensor:** `tests/sensors/test_ci_wizard_nightly_workflow.py` pins the
workflow shape — cron schedule, `LIA_E2E_SENSORS_ENABLED="true"` env var,
pytest invocation of `test_canonical_e2e_sensors.py`, `workflow_dispatch`
trigger. If any of those drift, the meta-sensor fails locally before the
nightly silently becomes a green no-op.


### ADR-WIZARD-002 — Documento canonical do wizard agêntico (2026-05-21)

> A arquitetura completa do wizard de criação de vaga (agentic conversational
> end-to-end pipeline) está documentada em `/tmp/WIZARD_ARCHITECTURE_CANONICAL.md`
> (Replit) + `/Users/paulomoraes/Documents/Python/WIZARD_ARCHITECTURE_CANONICAL.md`
> (Mac local), 2200+ linhas com:
>
> - 19 seções (Executive Summary, ASCII Architecture Diagram, Frontend Layer,
>   REST API Layer, WizardSessionService, LangGraph 15-node State Machine,
>   JobCreationState TypedDict, Persistence Layer, Schemas & Data Contracts,
>   Auth & Multi-tenancy, LLM Provider Chain, Audit Trail & Compliance,
>   Checkpointer AsyncPostgresSaver, 140+ Sensors, CI/CD, Workflow Replit,
>   Known Issues, Glossary com Sprint codenames mapping, Verification Recipes)
> - **Cita file:line para cada claim** — code is source of truth
> - WSI methodology distribution table inline (de `WSI_METHODOLOGY_COMPLETE_v2.md`
>   §5.4 + §5.5, referenced em `app/domains/job_creation/graph.py:4579`
>   `_get_question_distribution`) — compact 7q + full 12q por senioridade,
>   alocação intra-framework (CBI_tech/Dreyfus/Bloom/CBI_behav/BigFive)
> - Sprint codenames F→R mapping completo (commit hashes + themes), do estado
>   broken (pré-F) ao wizard E2E publish + nightly CI sensor green
>   (`042926e76` Sprint R Wave 4)
>
> **Regra de uso**: qualquer mudança arquitetural no wizard (`graph.py`,
> `wizard_session_service.py`, `state.py`, `wizard_smart_orchestrator.py`,
> `api_client.py`) DEVE incluir update no doc canonical no mesmo commit ou
> issue de follow-up explícita. Sensor:
> `tests/sensors/test_wizard_doc_freshness.py` — checa que o doc existe + foi
> modificado nos últimos 30 dias (warn-only por enquanto, BLOCKING quando
> baseline estiver verde + Anderson/time consciente do contrato).
>
> Entry point: leia o doc do início (Section 1 Executive Summary + Section 2
> ASCII Architecture) antes de mudar qualquer node do graph. WSI distribution
> table (Section 6 Node 8) é canonical — drift entre essa tabela, `graph.py:4579`
> e `WSI_METHODOLOGY_COMPLETE_v2.md §5.4-5.5` quebra silenciosamente o
> alinhamento F5 entre proporção de perguntas e scoring weights.
>
> ADR origem: canonical fix definitivo do wizard agêntico (commits Sprint F
> rolled-into → `0627531c9` Sprint H+I+J+K+L → `98082cef8` Sprint M+N →
> `9cb528561` Sprint O.1/O.3 → `014d77a60` Sprint P → `aa77f6c6a` Sprint Q →
> `042926e76` Sprint R Wave 4 final). Ver "Sprint Codenames Mapping" na
> Section 18 Glossary do doc canonical para tabela completa.


## Resolved Deprecations

- **2026-05-21 Sprint S:** removed `react_orchestrate` deprecated alias from
  `app/api/v1/wizard_smart_orchestrator.py` (was lines 374-385, function
  `async def react_orchestrate` + route `POST /api/v1/wizard/react-orchestrate`).
  Zero callers verified across `lia-agent-system/` (Python) and
  `plataforma-lia/` (TS, only auto-generated `api.generated.ts` types — no
  hand-written caller). Canonical replacement: `POST /api/v1/wizard/smart-orchestrate`.
  Sibling routes `/api/v1/pipeline/react-orchestrate` and
  `/api/v1/sourcing/react-orchestrate` (different routers, different domains)
  remain untouched. Sensor `tests/sensors/test_react_orchestrate_removed.py`
  enforces both source-level and FastAPI-route-level absence.



## Harness guard — verificar git log antes/depois de commit (registrado 2026-05-23)

Quando trabalhar em workspace com multiplos agentes paralelos (Replit
sandbox), commits podem ser absorvidos por outros agentes simultaneos
quando dois agentes tocam arquivos do mesmo diff window.

**Historico:** Sprint 3.3 (WSIVoicePlugin absorvido em commit
react-keys), T4 (TemplateClonePanel absorvido em Sprint X.A batch 6),
C5/D1 (HEAD avancou de ff7b2ee1b para 22ea094b4 entre o inicio da
sessao e o primeiro commit local).

**Pattern obrigatorio** para qualquer commit no Replit:

1. ANTES de `git commit`:
   ```bash
   git log --oneline -1
   ```
   Memorize o hash de HEAD atual.

2. Faca o commit normal:
   ```bash
   git add <files-explicit>
   git commit -m "..."
   ```

3. APOS commit:
   ```bash
   git log --oneline -1
   ```
   Verifique que o novo HEAD eh seu commit (mensagem + hash batem).

4. Se HEAD novo NAO eh seu commit OU sua mensagem foi capturada por
   outro agente: NAO faca rebase/reset/amend (REGRA ZERO). Reporte
   como ticket de harness pro Paulo e siga adiante com novo commit
   suplementar se necessario.

**Regra:** confirmar HEAD movimento eh disciplina barata (~1s). Garante
que o trabalho assinado foi de fato registrado no historico do Replit.

---

## Race-condition harness — commits multi-agent (registrado 2026-05-23)

**Problema observado (3x em sessao 2026-05-22+23):** multiplos agents
Claude rodando em paralelo no Replit absorvem files uns dos outros via
`git add .` ou commit timing race.

**Casos historicos:**
- Sprint 3.3 (WSI plugin absorvido em commit "react-keys")
- T4 (TemplateClonePanel absorvido em "Sprint X.A batch 6")
- Workstream A T5 commit absorption

### Pattern obrigatorio

Use `scripts/safe_commit.sh` em vez de `git commit -m` direto:

```bash
./scripts/safe_commit.sh \
    --message "feat(xxx): subject

body com contexto..." \
    --files "app/foo.py tests/test_foo.py"
```

O script:
- Verifica HEAD antes/depois (detect absorption)
- Stage SO files declarados (no `git add .`)
- Detecta pre-existing rogue staging (outro agent staged antes) → exit 3
- Verifica staged = declared apos staging (detect rogue mid-flight) → exit 3
- Verifica commit message bate com input (detect message capture) → exit 6
- Verifica commit contem files declarados (detect drop) → exit 7
- Exit non-zero em qualquer guard fail

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | OK — commit registrado e validado |
| 2 | Args invalidos OU empty staging sem --allow-empty |
| 3 | Stage mismatch — rogue file detectado (pre ou pos staging) |
| 4 | `git commit` falhou (hook rejeitou, etc.) |
| 5 | HEAD nao avancou apos commit (no-op ou absorvido) |
| 6 | Commit message diverge (capture por outro agent) |
| 7 | File declarado sumiu do commit final |

### Sub-agents (SSH ao Replit)

Sub-agents que rodam SSH ao Replit **DEVEM** usar `safe_commit.sh` — nao
`git commit -m` direto. Briefings devem mencionar explicitamente:

> "Para qualquer commit no workspace, use ./scripts/safe_commit.sh
>  --message ... --files ... — NUNCA git commit -m direto."

### Testes

`tests/contract/test_safe_commit_guard.sh` — 7 cases (happy path, stage
mismatch, empty staging, missing args, dry run, multi-file). Rodar quando
modificar `scripts/safe_commit.sh`.

### Quando NAO usar

- Merge commits (precisam de `--no-edit` ou interativo)
- Amends (manual + REGRA ZERO)
- Commits criados pelo Replit IDE (Paulo via UI) — esses sao manuais e
  proprios do workflow Replit

### Refs

- `scripts/safe_commit.sh` — implementacao
- `tests/contract/test_safe_commit_guard.sh` — testes
- `~/.claude/CLAUDE.md` "REGRA ZERO" — nao push, nao remoto
- Section anterior "Replit canonical produção" — workflow geral
