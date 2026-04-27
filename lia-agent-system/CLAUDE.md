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
| `try: ... except Exception: pass` | Silent failure destrói sensor — falhar alto > capturar e descartar | code review humano (TODO: linter) |

## Regras canonical-fix

- **Fix sempre no produtor, nunca no consumidor.** Se múltiplos callers passam dado errado, fix está no schema/contrato — não em cada caller.
- **Schema é fonte de verdade.** Modelo SQLAlchemy + Pydantic types > comentários > docstrings.
- **Não duplicar.** Antes de criar função/serviço novo, `grep` por nome similar. Reuso > NIH.
- **Não inventar tipos.** `String(255), nullable=True, indexed` em `User.company_id`? Replicar exato em outras colunas tenant.

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
