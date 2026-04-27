# Agent Compliance Matrix — 2026-04-27

Gap matrix de cobertura cross-cutting nos agents canonical da plataforma.
Gerado por `scripts/audit_agent_compliance.py` v2 (W3.3 refinado 2026-04-27).

**Heritage-aware (v2):** dimensoes auto-cobertas via `LangGraphReActBase`, `EnhancedAgentMixin` ou orchestrator wrapper sao marcadas como ✅ (com source). v1 reportava 0% PII/LLM Factory/OTEL — falsos negativos resolvidos.

## Sumário por dimensão

| Dimensão | Cobertura | Descrição |
|---|---|---|
| Inheritance | 🟢 13/13 (100%) | Class extends LangGraphReActBase |
| EnhancedMixin | 🟢 13/13 (100%) | Class extends EnhancedAgentMixin |
| @register_agent | 🟢 11/13 (84%) | Decorator @register_agent applied |
| FairnessGuard | 🟢 13/13 (100%) | FAR-2 — discriminatory language guard (auto via base + extra explicit) |
| AuditService | 🟢 13/13 (100%) | ACH-026 — decision audit (orchestrator wraps via log_output) |
| PII strip | 🟢 13/13 (100%) | LGPD — PII redaction before LLM (auto via LangGraphReActBase) |
| LLM Factory | 🟢 13/13 (100%) | BYOK — per-tenant LLM (auto via LangGraphReActBase) |
| OTEL | 🟢 13/13 (100%) | Observability — @trace_span (auto via orchestrator parent span) |
| HITL gate | 🔴 4/13 (30%) | AUD-4 — human-in-the-loop (per-agent, opcional) |
| System YAML | 🟡 8/13 (61%) | app/prompts/domains/<domain>.yaml exists |
| Tool registry | 🟢 12/13 (92%) | <domain>_tool_registry.py exists |

## Matriz por agent

| Agent (domain) | Inheritance | EnhancedMixin | @register_agent | FairnessGuard | AuditService | PII strip | LLM Factory | OTEL | HITL gate | System YAML | Tool registry |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `analytics` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| `ats_integration` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| `automation` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| `autonomous` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| `candidate_self_service` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `communication` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `company_settings` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| `pipeline` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `policy` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `jobs_management` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| `kanban` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| `talent` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| `sourcing` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Top gaps (priorizar)

- **HITL gate** — 9 agents sem cobertura (70% gap)
- **System YAML** — 5 agents sem cobertura (39% gap)
- **@register_agent** — 2 agents sem cobertura (16% gap)
- **Tool registry** — 1 agents sem cobertura (8% gap)

## Próximos passos

1. Para cada agent com ❌ em FairnessGuard / AuditService / PII strip, abrir issue no formato W2.x.
2. Promover hook G7 para block-only (`.pre-commit-config.yaml`) quando cobertura ≥ 90%.
3. Skill `create-canonical-agent` (W3.4) garante que NOVOS agents nascem em 100%.
4. Re-rodar este audit periodicamente (CI semanal recomendado).
