# Agent Compliance Matrix — 2026-04-27

Gap matrix de cobertura cross-cutting nos agents canonical da plataforma.
Gerado por `scripts/audit_agent_compliance.py` (W3.3, auditoria 2026-04-27).

## Sumário por dimensão

| Dimensão | Cobertura | Descrição |
|---|---|---|
| Inheritance | 🟢 13/13 (100%) | Class extends LangGraphReActBase |
| EnhancedMixin | 🟢 13/13 (100%) | Class extends EnhancedAgentMixin |
| @register_agent | 🟢 11/13 (84%) | Decorator @register_agent applied |
| FairnessGuard | 🔴 6/13 (46%) | FAR-2 — discriminatory language guard |
| AuditService | 🔴 4/13 (30%) | ACH-026 — decision audit trail |
| PII strip | 🔴 0/13 (0%) | LGPD — PII redaction before LLM |
| LLM Factory | 🔴 0/13 (0%) | BYOK — per-tenant LLM provider |
| OTEL | 🔴 0/13 (0%) | Observability — distributed tracing |
| HITL gate | 🔴 4/13 (30%) | AUD-4 — human-in-the-loop gate |
| System YAML | 🟡 8/13 (61%) | app/prompts/domains/<domain>.yaml exists |
| Tool registry | 🟢 12/13 (92%) | <domain>_tool_registry.py exists |

## Matriz por agent

| Agent (domain) | Inheritance | EnhancedMixin | @register_agent | FairnessGuard | AuditService | PII strip | LLM Factory | OTEL | HITL gate | System YAML | Tool registry |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `analytics` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `ats_integration` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `automation` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `autonomous` | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `candidate_self_service` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| `communication` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| `company_settings` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `pipeline` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `policy` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| `jobs_management` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `kanban` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `talent` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `sourcing` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |

## Top gaps (priorizar)

- **PII strip** — 13 agents sem cobertura (100% gap)
- **LLM Factory** — 13 agents sem cobertura (100% gap)
- **OTEL** — 13 agents sem cobertura (100% gap)
- **AuditService** — 9 agents sem cobertura (70% gap)
- **HITL gate** — 9 agents sem cobertura (70% gap)

## Próximos passos

1. Para cada agent com ❌ em FairnessGuard / AuditService / PII strip, abrir issue no formato W2.x.
2. Promover hook G7 para block-only (`.pre-commit-config.yaml`) quando cobertura ≥ 90%.
3. Skill `create-canonical-agent` (W3.4) garante que NOVOS agents nascem em 100%.
4. Re-rodar este audit periodicamente (CI semanal recomendado).
