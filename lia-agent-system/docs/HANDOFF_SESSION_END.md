# LIA Maturity Program — Session Handoff (2026-04-21)

> **Como usar este doc:** na nova sessão, abrir Claude Code, peça "leia `lia-agent-system/docs/HANDOFF_SESSION_END.md` no Replit e continue Onda 4 de onde parou (4.3 em diante)". Este doc é auto-contido — não precisa ler outros docs pra retomar.

---

## 🎯 Estado final da sessão

**422/422 tests green** no Replit branch `fix/kanban-e2e-bugs`. Uvicorn funcional (sem restart desde Onda 3 audit).

### 17 items shippados nesta sessão

| Bloco | Items | Commits |
|-------|-------|---------|
| **Track 1 (FIX 20-34)** | 14 FIXes canonical-fix (pagination, templates, enum normalizer, persona cleanup, SystemPromptBuilder slots, resolver wiring, DB schema drift, test isolation) | `182dec756` a `ab3216ccd` |
| **Onda 1 (5 items)** | FIX 34 (test isolation), Init I.B (persona renders cards), Init VI Fase 0 (eval_judge factory), G2 (obs markers), G6 (multi-tenant toggle) | `ab3216ccd` a `cee507b2f` |
| **Onda 2 (5 items)** | G5 light (PII redact), Init VI Fase 1 (golden set 129 + CI), Init IV (briefing formatter), Init V (citations backend), Init II.D (workflow_context) | `a45875997` a `f7b8ec3a6` |
| **Onda 3 (5 items)** | G4 (cost tracker), G3 (HITL checkpoint), Init VII (error policies), Init VIII (persona consistency), Init III MVP (episodic memory) | `d2e5bb376` a `ddf7c9769` |
| **Onda 4.1 + 4.2** | Pre-existing fix (_build_tool_schema_for_intent), G4.B (cost_tracker wired) | `e1bd6997b`, `7bb4dd716` |
| **Polish/chores** | Init IV plural fix, marker counter sync | `ba2f32436`, `ac536e90e` |

### Producer layers 100% shipped
Todos os módulos existem, testados, runtime-verified:
- `app/prompts/catalog/capability_cards.yaml` (16 cards)
- `app/orchestrator/citation_processor.py` (V)
- `app/orchestrator/hitl.py` (G3)
- `app/orchestrator/error_policies.py` + `.yaml` (VII)
- `app/orchestrator/workflow_registry.py` (II.D)
- `app/shared/observability/cost_tracker.py` (G4) + WIRED em ClaudeLLMProvider (G4.B)
- `app/shared/observability/marker_catalog.yaml` (G2, 30 markers)
- `app/shared/memory/recruiter_preferences.py` (III MVP)
- `app/shared/quality/persona_validator.py` + `tests/persona_scenarios.yaml` (VIII)
- `app/domains/recruiter_assistant/services/lia_briefing_formatter.py` (IV)
- `app/shared/pii_masking.py` extended with `redact_response_with_audit` (G5)
- `app/orchestrator/chat_adapter.py` has `_apply_pii_redaction` (G5 integrated)
- `app/shared/prompts/system_prompt_builder.py` renders: persona cards (I.B), active_filters + pending_action (II.A), workflow_context (II.D), tenant toggle (G6)
- `app/orchestrator/memory_resolver.py` quantifier gate (FIX 26) + resolve enrichment (FIX 30)
- `app/orchestrator/main_orchestrator.py` FIX 31 resolver wired no process()
- `app/shared/providers/llm_claude.py` G4.B cost tracking active

---

## 🟡 Pendente — Onda 4.3 a 4.9 (7 items)

### Contexto: producer ready, falta wiring caller → producer

Cada item abaixo tem **producer shipped** + **integration point identificado** + **patch sketch completo**. Trabalho restante = wire it + TDD + commit.

### 4.3 — III.B — ConversationState hydrate from user_preferences

**Risk: LOW.** Additive read enrichment.

**Target file:** `app/orchestrator/main_orchestrator.py` após linha 296-299 (`_setup_conversation_memory`).

**What to wire:**
```python
# After memory setup, before Phase 0:
try:
    from app.shared.memory.recruiter_preferences import get_preference
    # Fetch latest conversation_summaries row for this user (query)
    from sqlalchemy import select
    from lia_models.conversation import ConversationSummary
    _stmt = (
        select(ConversationSummary)
        .join(ConversationSummary.conversation)
        .where(ConversationSummary.conversation.has(user_id=ctx.user_id))
        .order_by(ConversationSummary.created_at.desc())
        .limit(1)
    )
    _res = await db.execute(_stmt)
    _last_summary = _res.scalar_one_or_none()
    _prefs = (_last_summary.user_preferences if _last_summary else {}) or {}
    ctx.extra["recruiter_prefs"] = {
        "preferred_top_n": get_preference(_prefs, "preferred_top_n", default=5),
        "briefing_style": get_preference(_prefs, "briefing_style", default="short"),
        "communication_channel": get_preference(_prefs, "communication_channel", default="email"),
    }
except Exception as _hydrate_exc:
    logger.debug("[III.B] hydrate skipped: %s", _hydrate_exc)
```

**Tests:**
- Mock DB to return ConversationSummary with user_preferences → verify ctx.extra populated
- Mock DB to raise → verify fail-safe (empty ctx.extra, no crash)

**Produto que consome:** futuro Init III.C (prompt injection do context recruiter_prefs).

### 4.4 — IV.B — Briefing greeting wire

**Risk: LOW.** Additive.

**Target file:** `app/orchestrator/main_orchestrator.py` dentro de `process()`, logo antes de Phase 0 handler (após III.B hydrate).

**What to wire:**
```python
# In process() after III.B hydrate, before Phase 0:
_msg_lower = (ctx.message or "").lower().strip()
_greeting_patterns = {"oi", "olá", "ola", "hello", "hi", "bom dia", "boa tarde", "boa noite"}
if _msg_lower in _greeting_patterns or (len(_msg_lower) <= 10 and any(g in _msg_lower for g in _greeting_patterns)):
    try:
        from app.domains.recruiter_assistant.services.lia_briefing_formatter import (
            get_cached_briefing, format_briefing_for_greeting,
        )
        _briefing = await get_cached_briefing(ctx.user_id, str(ctx.company_id), db=db)
        _summary = format_briefing_for_greeting(_briefing)
        if _summary:
            ctx.extra["briefing_context"] = _summary
            # Inject into persona via extra_instructions
            _existing_instr = ctx.extra.get("extra_instructions", "") or ""
            ctx.extra["extra_instructions"] = (
                f"{_existing_instr}\n\nNa saudação inclua: {_summary}"
            ).strip()
    except Exception as _briefing_exc:
        logger.debug("[IV.B] briefing skipped: %s", _briefing_exc)
```

**Tests:** mock briefing service + verify greeting injection; non-greeting message → no injection.

### 4.5 — V.B — Citations populate em ChatResponse

**Risk: HIGH.** ChatResponse schema change; frontend may consume.

**Target file:** `app/orchestrator/main_orchestrator.py` linhas 353-391 (agentic_loop result handling).

**What to wire:**
```python
# In agentic_loop result processing, before constructing ChatResponse:
from app.orchestrator.citation_processor import build_citations_from_tool_calls

_tool_calls_made = _agentic_result.get("tool_calls_made", []) or []
_citations = build_citations_from_tool_calls(
    _tool_calls_made,
    response_text=_agentic_result.get("response", ""),
)

# In the ChatResponse(...) kwargs:
ChatResponse(
    ...,
    citations=_citations,
    has_citations=bool(_citations),
)
```

**Tests:** mock agentic_loop returning tool_calls_made → verify citations populated.

**Backward compat:** field defaults to `[]`, `has_citations=False`. Frontend ignoring new fields = unchanged behavior.

### 4.6 — G3.B — HITL dispatch executor→ChatResponse

**Risk: MEDIUM.**

**Target files:**
- `app/tools/executor.py` linha 283 (HITL detection existe)
- `app/orchestrator/agentic_loop.py` (consume executor result)
- `app/orchestrator/main_orchestrator.py` (construct ChatResponse)

**What to wire:**
```python
# In agentic_loop, when executor returns requires_hitl=True:
if isinstance(result, dict) and result.get("requires_hitl"):
    from app.orchestrator.hitl import build_hitl_checkpoint
    _checkpoint = build_hitl_checkpoint(
        tool_name=result.get("tool_name", ""),
        tool_params=result.get("attempted_params", {}) or result.get("parameters", {}),
        governance_tags=result.get("governance_tags", []),
        reason=result.get("reason"),
    )
    return {
        "response": "Essa ação requer aprovação. Confirme para prosseguir.",
        "hitl_checkpoint": _checkpoint,
        "short_circuited_by": "hitl",
    }

# In main_orchestrator ChatResponse construction:
ChatResponse(
    ...,
    hitl_checkpoint=_agentic_result.get("hitl_checkpoint"),
)
```

**Tests:** mock executor returning requires_hitl → verify checkpoint built + propagated.

### 4.7 — VII.B — error_policies wire em try/except críticos

**Risk: MEDIUM.** Changes error response text user-facing.

**Target files (3 locations):**
- `app/orchestrator/main_orchestrator.py` linhas ~412-427 (catch-all in process())
- `app/orchestrator/agentic_loop.py` (top-level exception)
- `app/tools/executor.py` (tool execution errors)

**Pattern:**
```python
from app.orchestrator.error_policies import apply_policy

try:
    # existing
except Exception as exc:
    _policy = apply_policy(exc)
    return ChatResponse(
        success=False,
        content=_policy["response"],
        intent_detected="error_recovery",
        structured_data={
            "policy_id": _policy["policy_id"],
            "retry_hint": _policy["retry_hint"],
            "severity": _policy["severity"],
        },
    )
```

**Tests:** trigger each of the 5 policy triggers (timeout, empty_result, enum_error, permission_denied, tenant_mismatch) → verify apply_policy invoked + policy_id in response.

### 4.8 — FIX 35 — G1 conversational polish (persona footnotes + options + filters)

**Risk: LOW.** YAML-only.

**Depends on:** V.B shipped (citations data flows to LIA).

**Target file:** `app/prompts/shared/lia_persona.yaml` — nova seção dentro de `prompts.lia_persona`.

**Content to append** (as markdown section inside prompts.lia_persona):
```
## Estrutura de Respostas Ricas (FIX 35 / G1 conversational)

Quando sua resposta usa dados de tools, siga estes padrões:

### Citations (footnotes markdown)
Formato: `Encontrei 30 vagas ativas¹.\n\n¹ Fonte: search_jobs(status=Ativa) às 14:32`
Use superscript + rodapé quando houver ≥1 tool_call. Liste todas as fontes.

### Opções numeradas (action chips em texto)
Quando ofereces ≥2 next actions, numere:
  "Posso te ajudar com:
  1) Rankear top 5 candidatos
  2) Ver detalhes da vaga
  3) Buscar perfis similares
  Qual você quer?"
User responde "1" ou descreve.

### Filtros ativos (state em texto)
Em buscas contínuas, cite o estado:
  "Filtros ativos: status=Ativa, departamento=Tecnologia. Remover algum?"
Para remover: "remover status" ou "limpar filtros".

### Progress multi-step
Em operações com ≥2 tool calls, emite deltas via streaming:
  "1/4 buscando candidatos..."
  "2/4 ranqueando por fit..."
  "3/4 aplicando filtros de diversidade..."
  "4/4 formatando resultado."

### Error recovery (offers em texto)
Em falhas, ofereça próxima ação:
  "Deu timeout na busca. Posso tentar de novo, ajustar filtros ou abrir ticket. Qual prefere?"
```

**Tests:** YAML parses, persona contains footnote example + numbered option example + filter example.

**Wiring:** usa FIX 29 migration pattern (append como markdown section inside `prompts.lia_persona`).

### 4.9 — VIII.B — persona validator CI

**Risk: LOW.** CI only.

**Target file:** `.github/workflows/lia-eval.yml` — add new step.

**Requires:** `tests/persona_recordings.yaml` (placeholder stub OK — real recordings ship later).

**Patch:**
```yaml
      - name: Init VIII — persona consistency check
        working-directory: lia-agent-system
        env:
          LIA_SKIP_DB: "1"
        run: |
          python3 <<'PY'
          import pathlib
          import yaml
          from app.shared.quality.persona_validator import validate_response

          rec_file = pathlib.Path('tests/persona_recordings.yaml')
          if not rec_file.exists():
              print('no recordings — skipping (VIII.B ready, populate after real LIA calls)')
              exit(0)
          recordings = yaml.safe_load(rec_file.read_text()) or {}
          failed = []
          for sid, text in recordings.items():
              v = validate_response(sid, text)
              if v and not v.passed:
                  failed.append((sid, v.failures))
          if failed:
              for sid, fs in failed:
                  print(f'FAIL {sid}: {fs}')
              exit(1)
          print(f'✓ {len(recordings)} persona scenarios passed')
          PY
```

**Tests:** workflow YAML parses + step present + references validate_response.

---

## 📋 Execução nova sessão — checklist

1. `ssh replit-wedo 'cd /home/runner/workspace && git log --oneline -10'` — confirmar HEAD
2. `ssh replit-wedo 'cd /home/runner/workspace/lia-agent-system && PYTHONPATH=. LIA_SKIP_DB=1 python3 -m pytest tests/unit/ -q --no-cov 2>&1 | tail -5'` — confirmar ≥422 green baseline
3. Ler este doc
4. Começar Onda 4.3 (III.B)
5. Ordem: **III.B → IV.B → V.B → G3.B → VII.B → FIX 35 → VIII.B**
6. Cada um: RED test → GREEN patch → regression full → commit
7. **Restart uvicorn DEPOIS** de todos 7 (padrão Onda 1/2/3 — restart final reduz noise)
8. Smoke real via JWT no chat: verificar cada B-item com log marker apropriado

---

## 🧰 Skills obrigatórias (não-negociáveis, CLAUDE.md)

- **canonical-fix** (Replit Agent): producer-level fix, no workaround, no silent fallback
- **harness-engineering-lia** (~/.claude/skills/harness-engineering-lia): classify cada change (guide/sensor × comp/infer)
- **production-quality** (CLAUDE.md): P0/P1/P2, LGPD/multi-tenancy/fairness, no hardcoded secrets
- **lia-testing** (~/.claude/skills/lia-testing): TDD Red→Green→Refactor patterns

---

## 📁 Docs relacionados (ler se precisar context)

- `lia-agent-system/docs/LIA_MATURITY_ROADMAP.md` — roadmap completo + status tracker
- `lia-agent-system/docs/ONDA2_PLAN.md` — 1704 linhas com specs originais (V/IV/II.D especialmente)
- `lia-agent-system/docs/FINAL_AUDIT.md` — audit executivo 12 items
- `lia-agent-system/docs/INITIATIVES_AUDIT.md` — audit inicial
- `lia-agent-system/docs/PHASE0_AUDIT.md` — discovery + freshness matrix

Plan file na máquina Paulo: `/Users/paulomoraes/.claude/plans/cached-swimming-quail.md` (563+ linhas) contém a Onda 4 com §1-§8 completos.

---

## 🔍 Padrões descobertos nesta sessão (lições aplicar na próxima)

1. **PARTE L pattern** — test-green NÃO implica runtime-active. Sempre smoke real pós-restart (descobriu FIX 15/19/26/30/31 dead code situations).

2. **Replit auto-checkpoint absorbing commits** — replit-agent reescreve mensagens de commit. Aceitar mas logar FIX marker explicitamente pra traceability.

3. **Canonical-fix rigor paga** — 4 FIXes extras (29-32) resolvidos em ~30min cada porque producer + consumer já estavam mapeados.

4. **Progressive disclosure funciona** — checkpoint entre itens evita big-bang regressions. Cada commit separado com smoke = rollback granular.

5. **SSH bash timing** — `nohup ... & disown; sleep 5` é o padrão que funciona pra uvicorn relaunch. Sem `sleep`, disown não toma efeito antes da SSH fechar.

6. **Anchor false-positives em grep-based patches** — cuidado com strings curtas tipo "G6" (match em "G1-G6" pre-existente). Usar anchors mais específicos tipo "G6 (2026-04-21)".

---

## 🎯 Contexto mínimo pra nova sessão abrir e começar

**Quem é o usuário:** Paulo Moraes, fundador WeDOTalent. Prefere explicação simples. Push manual no GitHub via Replit IDE (AI NUNCA faz push). Pattern adversarial de auditoria ("tem certeza? tudo pronto?") pega gaps reais.

**Ambiente:**
- SSH alias: `replit-wedo` → `/home/runner/workspace`
- Repo: `lia-agent-system/` (FastAPI + Python)
- Branch: `fix/kanban-e2e-bugs`
- JWT gen: `python3 -c "from app.auth.security import create_access_token; from app.core.tenant import DEMO_COMPANY_UUID; print(create_access_token(subject='smoke', role='admin', company_id=DEMO_COMPANY_UUID))"`
- Chat endpoint: `POST /api/v1/chat` com Bearer token + JSON `{"content": "...", "conversation_id": "..."}`

**Primeiro comando na nova sessão:**
```bash
ssh replit-wedo 'cd /home/runner/workspace/lia-agent-system && git log --oneline -5 && PYTHONPATH=. LIA_SKIP_DB=1 python3 -m pytest tests/unit/ -q --no-cov 2>&1 | tail -3'
```

Deve mostrar: 422+ passed, HEAD em `7bb4dd716` (G4.B) ou mais recente.

---

**Pronto pra handoff.**
