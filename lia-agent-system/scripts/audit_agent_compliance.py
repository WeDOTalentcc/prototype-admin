"""
Audit retroativo — canonical agent compliance matrix.

Diferente de check_agent_compliance.py (G7 hook que retorna pass/fail),
este script gera um RELATORIO em markdown com gap matrix por agent x
dimensao cross-cutting. Usado para:
  - Baseline da plataforma (% de cobertura por dimensao)
  - Tracking de progresso wave-a-wave
  - Comparacao pre/pos refactor

Output: AGENT_COMPLIANCE_MATRIX_<YYYY-MM-DD>.md

Uso:
    python scripts/audit_agent_compliance.py
    python scripts/audit_agent_compliance.py --output /tmp/matrix.md

Skills aplicadas:
- harness-engineering: SENSOR de mensuracao retroativo (computacional).
- production-quality: gap matrix expoe risco P0/P1 por agent.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_AGENTS_GLOB = "app/domains/*/agents/*_react_agent.py"
_PROMPTS_DIR = _ROOT / "app" / "prompts" / "domains"


# Each tuple: (column_label, regex_or_substring, description_for_doc)
# (label, regex_or_marker, description, inherited_via)
# `inherited_via`: if not None, the dimension is automatically covered when the
# agent inherits from the named base class — sensor was reporting false negatives
# because it only looked at each agent file, ignoring heritage.
# Investigation 2026-04-27 (Paulo): LangGraphReActBase already invokes
# strip_pii_for_llm_prompt (line 71-79), get_provider_for_tenant (line 297),
# and FairnessGuard pre-check (line 277). Orchestrator wraps every agent
# call with @trace_span (main_orchestrator.py:336) and AuditService.log_output
# (main_orchestrator.py:1585-1605, conditional on entity_id).
_DIMENSIONS = [
    ("Inheritance",      r"LangGraphReActBase",                  "Class extends LangGraphReActBase",                                None),
    ("EnhancedMixin",    r"EnhancedAgentMixin",                  "Class extends EnhancedAgentMixin",                                None),
    ("@register_agent",  r"@register_agent\(",                   "Decorator @register_agent applied",                                None),
    ("FairnessGuard",    r"FairnessGuard",                       "FAR-2 — discriminatory language guard (auto via base + extra explicit)", "EnhancedAgentMixin"),
    ("AuditService",     r"audit_service\.|log_decision",        "ACH-026 — decision audit (orchestrator wraps via log_output)",     "orchestrator"),
    ("PII strip",        r"strip_pii_for_llm_prompt|PIIRedactor","LGPD — PII redaction before LLM (auto via LangGraphReActBase)",    "LangGraphReActBase"),
    ("LLM Factory",      r"get_provider_for_tenant",             "BYOK — per-tenant LLM (auto via LangGraphReActBase)",              "LangGraphReActBase"),
    ("OTEL",             r"@trace_span|trace_span\(",            "Observability — @trace_span (auto via orchestrator parent span)",  "orchestrator"),
    ("HITL gate",        r"hitl_service|request_approval",       "AUD-4 — human-in-the-loop (per-agent, opcional)",                  None),
    ("System YAML",      "__yaml_check__",                       "app/prompts/domains/<domain>.yaml exists",                         None),
    ("Tool registry",    "__tool_registry__",                    "<domain>_tool_registry.py exists",                                 None),
]

_REGISTER_AGENT = re.compile(r"@register_agent\(['\"](\w+)['\"]")


def _check_dimension(dim_key: str | re.Pattern, agent_path: Path, src: str) -> bool:
    """Check whether the dimension is satisfied for this agent file."""
    if isinstance(dim_key, str):
        if dim_key == "__yaml_check__":
            # v4: aceita 4 patterns:
            # 1. agent_id literal
            # 2. agent aliases declarados em @register_agent
            # 3. domain dir name
            # 4. "Content source: app/prompts/domains/X.yaml" comment em _system_prompt.py
            m = _REGISTER_AGENT.search(src)
            if m:
                yaml_path = _PROMPTS_DIR / f"{m.group(1)}.yaml"
                if yaml_path.exists():
                    return True
                # aliases?
                alias_match = re.search(
                    r"@register_agent\([\'\"]\w+[\'\"]\s*,\s*aliases\s*=\s*\[([^\]]*)\]",
                    src,
                )
                if alias_match:
                    for alias in re.findall(r"[\'\"](\w+)[\'\"]", alias_match.group(1)):
                        if (_PROMPTS_DIR / f"{alias}.yaml").exists():
                            return True
            # filename-based
            stem = agent_path.stem.replace("_react_agent", "")
            if (_PROMPTS_DIR / f"{stem}.yaml").exists():
                return True
            # parent domain dir
            domain_dir_name = agent_path.parents[1].name
            if (_PROMPTS_DIR / f"{domain_dir_name}.yaml").exists():
                return True
            # content source comment in adjacent _system_prompt.py
            sysp = agent_path.parent / agent_path.name.replace("_react_agent.py", "_system_prompt.py")
            if sysp.exists():
                sysp_src = sysp.read_text(errors="ignore")
                cs = re.search(r"Content source:\s*app/prompts/domains/(\w+)\.yaml", sysp_src)
                if cs and (_PROMPTS_DIR / f"{cs.group(1)}.yaml").exists():
                    return True
            return False
        if dim_key == "__tool_registry__":
            # v3: accept either same-folder registry OR a cross-domain import
            expected = agent_path.parent / agent_path.name.replace(
                "_react_agent.py", "_tool_registry.py"
            )
            if expected.exists():
                return True
            # cross-domain: import like 
            if re.search(r"from app\.domains\.[\w]+\.agents\.\w+_tool_registry import", src):
                return True
            return False
        # plain substring (treated as regex though)
        return bool(re.search(dim_key, src))
    return bool(dim_key.search(src))


def _row(agent_path: Path) -> dict:
    src = agent_path.read_text(errors="ignore")
    rel = str(agent_path.relative_to(_ROOT))
    domain_match = _REGISTER_AGENT.search(src)
    domain = domain_match.group(1) if domain_match else agent_path.stem.replace("_react_agent", "")
    row = {"agent": rel, "domain": domain, "dims": {}, "dims_source": {}}
    has_base = "LangGraphReActBase" in src
    has_mixin = "EnhancedAgentMixin" in src
    for label, key, _desc, inherited_via in _DIMENSIONS:
        explicit = _check_dimension(key, agent_path, src)
        if explicit:
            row["dims"][label] = True
            row["dims_source"][label] = "explicit"
        elif inherited_via == "LangGraphReActBase" and has_base:
            row["dims"][label] = True
            row["dims_source"][label] = "via LangGraphReActBase"
        elif inherited_via == "EnhancedAgentMixin" and has_mixin:
            row["dims"][label] = True
            row["dims_source"][label] = "via EnhancedAgentMixin"
        elif inherited_via == "orchestrator":
            # Every agent is invoked through the orchestrator wrapper, which
            # provides @trace_span and conditional audit_service.log_output
            row["dims"][label] = True
            row["dims_source"][label] = "via orchestrator wrapper"
        else:
            row["dims"][label] = False
            row["dims_source"][label] = "MISSING"
    return row


def _summary(rows: list[dict]) -> dict[str, dict]:
    """Compute per-dimension % coverage."""
    total = len(rows)
    out: dict[str, dict] = {}
    for label, _, desc, _inh in _DIMENSIONS:
        passing = sum(1 for r in rows if r["dims"][label])
        out[label] = {
            "passing": passing,
            "total": total,
            "pct": (passing * 100 // total) if total else 0,
            "desc": desc,
        }
    return out


def _render_md(rows: list[dict], summary: dict[str, dict]) -> str:
    today = date.today().isoformat()
    lines: list[str] = []
    lines.append(f"# Agent Compliance Matrix — {today}")
    lines.append("")
    lines.append(
        "Gap matrix de cobertura cross-cutting nos agents canonical da plataforma."
    )
    lines.append(
        "Gerado por `scripts/audit_agent_compliance.py` v2 (W3.3 refinado 2026-04-27)."
    )
    lines.append("")
    lines.append(
        "**Heritage-aware (v2):** dimensoes auto-cobertas via `LangGraphReActBase`, "
        "`EnhancedAgentMixin` ou orchestrator wrapper sao marcadas como ✅ (com source). "
        "v1 reportava 0% PII/LLM Factory/OTEL — falsos negativos resolvidos."
    )
    lines.append("")
    lines.append("## Sumário por dimensão")
    lines.append("")
    lines.append("| Dimensão | Cobertura | Descrição |")
    lines.append("|---|---|---|")
    for label, _, _, _inh in _DIMENSIONS:
        s = summary[label]
        bar = "🟢" if s["pct"] >= 80 else ("🟡" if s["pct"] >= 50 else "🔴")
        lines.append(
            f"| {label} | {bar} {s['passing']}/{s['total']} ({s['pct']}%) | {s['desc']} |"
        )
    lines.append("")

    # Detail per agent
    lines.append("## Matriz por agent")
    lines.append("")
    headers = ["Agent (domain)"] + [label for label, _, _, _inh in _DIMENSIONS]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in sorted(rows, key=lambda x: x["agent"]):
        cells = [f"`{r['domain']}`"]
        for label, _, _, _inh in _DIMENSIONS:
            cells.append("✅" if r["dims"][label] else "❌")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    # Top gaps
    lines.append("## Top gaps (priorizar)")
    lines.append("")
    sorted_dims = sorted(summary.items(), key=lambda kv: kv[1]["pct"])
    for label, s in sorted_dims[:5]:
        if s["pct"] < 100:
            lines.append(
                f"- **{label}** — {s['total'] - s['passing']} agents sem cobertura "
                f"({100 - s['pct']}% gap)"
            )
    lines.append("")

    lines.append("## Próximos passos")
    lines.append("")
    lines.append("1. Para cada agent com ❌ em FairnessGuard / AuditService / PII strip, abrir issue no formato W2.x.")
    lines.append("2. Promover hook G7 para block-only (`.pre-commit-config.yaml`) quando cobertura ≥ 90%.")
    lines.append("3. Skill `create-canonical-agent` (W3.4) garante que NOVOS agents nascem em 100%.")
    lines.append("4. Re-rodar este audit periodicamente (CI semanal recomendado).")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit canonical agent compliance.")
    parser.add_argument(
        "--output",
        default=str(_ROOT.parent / f"AGENT_COMPLIANCE_MATRIX_{date.today().isoformat()}.md"),
    )
    args = parser.parse_args()

    agents = sorted(_ROOT.glob(_AGENTS_GLOB))
    if not agents:
        print("No agents found.")
        return 1

    rows = [_row(p) for p in agents]
    summary = _summary(rows)
    md = _render_md(rows, summary)

    out = Path(args.output)
    out.write_text(md)

    # CLI summary
    print(f"Audited {len(rows)} agents → {out}")
    print()
    for label, _, _, _inh in _DIMENSIONS:
        s = summary[label]
        bar = "🟢" if s["pct"] >= 80 else ("🟡" if s["pct"] >= 50 else "🔴")
        print(f"  {bar} {label:<18} {s['passing']:>2}/{s['total']:<2}  ({s['pct']}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
