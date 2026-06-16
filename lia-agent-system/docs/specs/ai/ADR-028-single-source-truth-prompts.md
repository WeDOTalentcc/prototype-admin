# ADR-028 — Single Source of Truth para System Prompts (PromptComposer)

**Status**: Accepted (Sprint 2 implementation pending — see Q2 Canonical Refactor)
**Data**: 2026-05-06
**Contexto**: Wizard "ID empresa" bug audit (sessão Sprint B+) revelou 18 sources of truth para mesma regra
**Autor**: Claude Opus 4.7 com decisão Paulo
**Sprint**: Q2 Canonical Refactor (Sprint 0 — Governance)

---

## Contexto

Auditoria 2026-05-06 (origem: bug LIA pedindo "ID da empresa") revelou **18 sources of truth** para mesma instrução de tenant isolation:

1. `app/prompts/shared/guardrails_block.yaml` — multi_tenancy block
2. `app/shared/prompts/system_prompt_builder.py` — TENANT_ISOLATION_HARD_RULE
3. `app/shared/prompts/interaction_patterns.py` — TENANT_ISOLATION_BLOCK
4-18. **15 ReAct agent classes** com `DOMAIN_INSTRUCTIONS` class-attr

Cada novo agent precisaria adicionar manualmente em N lugares. Esta sessão precisou de **10+ commits** para corrigir o bug porque cada commit pegava 1-3 dos 18 lugares. Drift garantido.

### Inventário (verificado)

```
$ find app -name "*.yaml" | grep prompt | wc -l
32 YAML prompt files

$ find app -name "*prompt*.py" | wc -l
37 Python prompt files

$ grep -rln "system_prompt\|SYSTEM_PROMPT" app/ | wc -l
127 files mention system_prompt

$ grep -rln "DOMAIN_INSTRUCTIONS\s*=" app/ | wc -l
15 ReAct agents with class-level DOMAIN_INSTRUCTIONS
```

**Comparação com enterprise patterns:**
- Anthropic Claude Code: ~5-8 templates totais
- OpenAI Assistants: 1 system prompt por assistant + thread metadata
- Cursor / Replit Agent: tools com runtime env, prompt centralizado

---

## Decisão

**Adotar PromptComposer factory pattern** como **único caminho** de construção de system prompts para agents.

### 1. Arquitetura proposta

```python
# app/shared/prompts/composer.py (NOVO)

@dataclass
class PromptContext:
    """Runtime context — populated por middleware antes de chamar LLM."""
    company_id: str            # do JWT
    user_id: str               # do JWT
    user_name: str
    user_role: str
    conversation_summary: str = ""
    stage: str = ""

class PromptComposer:
    """Single composition point para system prompts de agents."""

    @classmethod
    def compose(
        cls,
        *,
        agent_type: str,             # "jobs_mgmt", "wizard", etc.
        domain_specific: str,        # texto específico do domínio
        few_shot_examples: str = "",
        domain_reasoning: str = "",
        ctx: PromptContext,
    ) -> str:
        """Compõe system prompt seguindo padrão canonical:

        ORDER (estrito):
          1. Persona base (lia_persona.yaml)
          2. Domain-specific identity
          3. Few-shot examples (opcional)
          4. UNIVERSAL BLOCKS (auto-injetados — NÃO PODE SER ESQUECIDO):
             - TENANT_ISOLATION_BLOCK
             - NEGATION_DETECTION_BLOCK
             - ANTI_SYCOPHANCY_BLOCK
          5. Domain reasoning (ReAct protocol)
          6. Runtime context (ctx)
        """
        ...
```

### 2. Migration plan

Migrar 15 agents para o factory pattern. Cada agent perde sua `DOMAIN_INSTRUCTIONS` class-attr; em vez disso, herda de `LangGraphReActBase` que chama `PromptComposer.compose(...)` em `_get_system_prompt(ctx)`.

```python
# AFTER refactor
class WizardReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    AGENT_TYPE = "wizard"
    DOMAIN_SPECIFIC = WIZARD_DOMAIN_SPECIFIC
    FEW_SHOTS = WIZARD_FEW_SHOT_EXAMPLES
    DOMAIN_REASONING = WIZARD_REASONING_PROMPT

    # NO MORE: DOMAIN_INSTRUCTIONS = ...  ← eliminated

    # Base class auto-composes via PromptComposer.compose(...)
```

### 3. Universal blocks são INVIOLÁVEIS

```python
UNIVERSAL_BLOCKS = (
    TENANT_ISOLATION_BLOCK,
    NEGATION_DETECTION_BLOCK,
    ANTI_SYCOPHANCY_BLOCK,
)
```

PromptComposer **SEMPRE** injeta esses 3 blocks. Não pode ser desabilitado por agent. Adicionar novo block universal = mudança aqui (1 lugar).

### 4. Sensor harness

Sensor `check_agent_has_universal_blocks` verifica:
- Cada classe que herda `LangGraphReActBase` NÃO tem `DOMAIN_INSTRUCTIONS` class-attr (deprecated)
- Cada classe define `AGENT_TYPE`, `DOMAIN_SPECIFIC`, e usa factory
- Output rendered (via fixture) contém os 3 universal blocks

Inicialmente warn-only durante migration. Blocking após Sprint 2 completo.

---

## Consequências

### Positivas
- ✅ **18 → 1** source of truth para universal rules
- ✅ Adicionar novo agent = automatic guardrails
- ✅ Adicionar novo universal rule = 1 commit, não 18
- ✅ Sensor catches drift em PR-time
- ✅ Alinha com Anthropic / OpenAI / LangGraph patterns
- ✅ Testabilidade (PromptComposer pode ser mockado)

### Negativas
- ⚠️ Refator de 15 agents (~20-30h Sprint 2)
- ⚠️ Risco de regressão (mitigado por TDD red-phase + smoke tests)
- ⚠️ Backward compat tests obrigatórios

### Reversibilidade
ADR é reversível durante migration: cada agent pode reverter para DOMAIN_INSTRUCTIONS via git revert. Após Sprint 2 completo + sensor blocking, reverter custa muito.

---

## Implementação (Sprint 2)

| Task | Esforço | Skill |
|---|---|---|
| Criar `PromptComposer` + tests | 4h | `/tdd-workflow` + `/design-patterns` |
| Refator `LangGraphReActBase` | 3h | `/canonical-fix` |
| Migrate 15 agents (1.5h cada) | 22h | `/create-canonical-agent` + REGRA 6 |
| Backward compat tests | 4h | `/tdd-workflow` |
| Sensor blocking ratchet | 2h | `/harness-engineering` |
| Documentação + ADR final | 1h | docs |
| **Total Sprint 2** | **~36h** | |

---

## Métricas de sucesso

- Antes: 18 sources, 15 DOMAIN_INSTRUCTIONS class-attr, sensor warn-only
- Depois: 1 source (PromptComposer), 0 DOMAIN_INSTRUCTIONS, sensor blocking
- Tests: 100% TDD coverage on PromptComposer
- Regression: 0 (smoke tests E2E em 5 agents críticos)
- LLM behavior: equivalent (output prompt diff < 50 chars vs current)

---

## Referências

- Bug origem: sessão Sprint B+ wizard "ID empresa"
- ADR-001 (Repository Pattern) — padrão similar para SQL
- ADR-026 (screening_questions canonical) — padrão similar para data
- CLAUDE.md REGRA 1 (multi-tenancy)
- Skill `/canonical-fix`, `/harness-engineering`, `/tdd-workflow`
