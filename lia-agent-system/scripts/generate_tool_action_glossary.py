#!/usr/bin/env python3
"""
Generate canonical GLOSSARIO_ACTIONS_TOOLS.md from source of truth files.

Sources read:
- app/tools/tool_registry_metadata.yaml   (88+5 tools with descriptions,
                                            when_to_use, when_not_to_use,
                                            governance_tags, related_tools,
                                            side_effects, allowed_agents,
                                            scope, parameters)
- app/domains/*/actions.py                (DomainActions in separate files)
- app/domains/*/domain.py                 (DomainActions inline in 4 domains:
                                            company_settings, hiring_policy,
                                            pipeline, candidate_self_service)
- app/domains/*/domain.py _ACTION_TOOL_MAP (action_id → tool_name mapping)

Output: docs/GLOSSARIO_ACTIONS_TOOLS.md

Usage:
    python scripts/generate_tool_action_glossary.py
    python scripts/generate_tool_action_glossary.py --check  # dry run, exit code 1 if stale

Commit refs for context:
- FIX 1 82009b0c8, FIX 2 4d55b7c40, FIX 3+4 c9ec97385,
- FIX 5+6+7 71a2ec1d1, FIX 8 8e8bfa3bd, FIX 9 896f4ae34,
- FIX 10 c0a3e3b79, FIX 11 cf12c3ec9, FIX 12 3f7245f18
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: PyYAML required. Install with: pip install pyyaml")


# ── Paths ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]  # lia-agent-system/
YAML_PATH = ROOT / "app" / "tools" / "tool_registry_metadata.yaml"
DOMAINS_DIR = ROOT / "app" / "domains"
OUTPUT_PATH = ROOT / "docs" / "GLOSSARIO_ACTIONS_TOOLS.md"


# ── Data extraction ──────────────────────────────────────────────────

def load_tools() -> list[dict]:
    """Load tool entries from YAML, sorted alphabetically by name."""
    data = yaml.safe_load(YAML_PATH.read_text())
    tools = data.get("tools", [])
    return sorted(tools, key=lambda t: t.get("name", ""))


def extract_domain_actions(domain_dir: Path) -> list[dict]:
    """Extract DomainAction entries from a single domain folder.

    Looks for actions in actions.py (if exists) OR inline in domain.py.
    Returns list of dicts with keys: action_id, name, description, examples,
    requires_confirmation, tags, required_params, optional_params.
    """
    results: list[dict] = []
    actions_py = domain_dir / "actions.py"
    domain_py = domain_dir / "domain.py"

    files_to_parse: list[Path] = []
    if actions_py.exists():
        files_to_parse.append(actions_py)
    if domain_py.exists():
        files_to_parse.append(domain_py)

    for fp in files_to_parse:
        try:
            src = fp.read_text()
            tree = ast.parse(src)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fname = ""
            if isinstance(node.func, ast.Name):
                fname = node.func.id
            elif isinstance(node.func, ast.Attribute):
                fname = node.func.attr
            if fname != "DomainAction":
                continue

            entry: dict = {}
            for kw in node.keywords:
                if not isinstance(kw.value, (ast.Constant, ast.Tuple, ast.List)):
                    continue
                if isinstance(kw.value, ast.Constant):
                    entry[kw.arg] = kw.value.value
                elif isinstance(kw.value, (ast.Tuple, ast.List)):
                    items: list = []
                    for elt in kw.value.elts:
                        if isinstance(elt, ast.Constant):
                            items.append(elt.value)
                    entry[kw.arg] = tuple(items)

            # Normalize: id/action_id aliases
            aid = entry.get("action_id") or entry.get("id")
            if not aid:
                continue
            entry["action_id"] = aid
            results.append(entry)

    return results


def extract_action_tool_map(domain_dir: Path) -> dict[str, str]:
    """Extract _ACTION_TOOL_MAP dict from domain.py (if present).

    Returns mapping action_id → tool_id (Tool name in registry).
    """
    domain_py = domain_dir / "domain.py"
    if not domain_py.exists():
        return {}
    try:
        src = domain_py.read_text()
        tree = ast.parse(src)
    except Exception:
        return {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_ACTION_TOOL_MAP":
                    if isinstance(node.value, ast.Dict):
                        mapping = {}
                        for k, v in zip(node.value.keys, node.value.values):
                            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                mapping[str(k.value)] = str(v.value)
                        return mapping
    return {}


def collect_all_domain_data() -> tuple[
    dict[str, list[dict]],    # domain_id → list of actions
    dict[str, dict[str, str]],  # domain_id → action_id_tool_map
    dict[str, list[str]],      # tool_id → list of "domain.action" that invoke it
]:
    """Walk app/domains/*/ and gather all DomainAction data + reverse index."""
    domain_actions: dict[str, list[dict]] = {}
    domain_tool_maps: dict[str, dict[str, str]] = {}
    tool_invocations: dict[str, list[str]] = {}

    for domain_dir in sorted(DOMAINS_DIR.iterdir()):
        if not domain_dir.is_dir():
            continue
        if domain_dir.name.startswith("_") or domain_dir.name == "__pycache__":
            continue
        if domain_dir.name in ("ai",):  # skip non-domain dirs
            continue

        actions = extract_domain_actions(domain_dir)
        if actions:
            domain_actions[domain_dir.name] = actions

        tool_map = extract_action_tool_map(domain_dir)
        if tool_map:
            domain_tool_maps[domain_dir.name] = tool_map
            for aid, tid in tool_map.items():
                tool_invocations.setdefault(tid, []).append(f"{domain_dir.name}.{aid}")

    return domain_actions, domain_tool_maps, tool_invocations


# ── Rendering ─────────────────────────────────────────────────────────

def render_header() -> str:
    today = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return f"""# Glossário de Tools e DomainActions — LIA AI

> **Fonte da verdade visível** para o time de desenvolvimento consumir e reproduzir a camada de IA da plataforma LIA.
>
> Gerado automaticamente a partir de:
> - `app/tools/tool_registry_metadata.yaml` (fonte YAML das ferramentas)
> - `app/domains/*/actions.py` e `app/domains/*/domain.py` (DomainActions)
>
> **Regenerar:** `python scripts/generate_tool_action_glossary.py`
>
> **Manutenção automática:** o workflow `.github/workflows/tool-glossary-check.yml` (Task #733) roda `python scripts/generate_tool_action_glossary.py --check` em todo push/PR que mexe nos fontes de tools/actions, no gerador ou neste documento, e quebra o build se o glossário estiver desatualizado.
>
> **Última atualização:** {today} · **Status pós FIX 1-12:** 100% cobertura

## Changelog referente aos FIXes

| FIX | Commit | Mudou no glossário |
|-----|--------|---------------------|
| 1 | `82009b0c8` | n/a (injeção no LLM) |
| 2 | `4d55b7c40` | +245 examples em DomainActions |
| 3+4 | `c9ec97385` | +governance_tags, +related_tools em Tools |
| 5+6+7 | `71a2ec1d1` | wizard sync + cross-refs em 2 clusters |
| 8 | `8e8bfa3bd` | +side_effects em Tools + FairnessGuard ativa |
| 9 | `896f4ae34` | +25 examples inline (4 domínios novos) + 100% quality |
| 10 | `c0a3e3b79` | +5 wizard tools YAML (extract_job_requirements, create_job_draft, validate_job_requirements, get_salary_benchmarks, check_job_draft_health) |
| 11 | `cf12c3ec9` | cross-ref em `generate_wsi_questions` |
| 12 | `3f7245f18` | n/a (observability module) |

---
"""


def render_governance_glossary() -> str:
    return """## Governance tags — glossário

Valores canônicos de `governance_tags` (campo de `ToolDefinition`) com enforcement atual.

| Tag | Significado | Enforcement | Status |
|-----|-------------|-------------|--------|
| `multi_tenant` | Tool valida `company_id` | `ToolExecutionContext` | ✅ ativo |
| `pii` | Tool trata PII | Logging/audit (parcial) | ⏳ parcial |
| `fairness_guard` | Sujeita à análise de viés | **FIX 8** — Layer 1 regex bloqueia | ✅ **ativo** |
| `requires_hitl` | Precisa confirmação humana | **FIX 3** — `pending_hitl_confirmation` | ✅ **ativo** |
| `audit_trail` | Grava audit log | Hook futuro | ⏳ parcial |
| `credits_consumed` | Custa crédito externo | Validação futura | ⏳ parcial |
| `write_destructive` | Ação destrutiva | Combinada com `requires_hitl` | ✅ via HITL |

---
"""


def render_side_effects_glossary() -> str:
    return """## Side_effects — glossário

Valores observados no YAML (15 distintos).

| Side effect | Significado | Uso downstream |
|-------------|-------------|----------------|
| `none` | Read-only | Retry seguro, idempotent |
| `db_write` | Persiste no banco | Retry cuidadoso, idempotency key |
| `external_api_call` | Chama API externa | Circuit breaker, timeout |
| `credits_consumed` | Gasta créditos pagos | Budget check pré-execução |
| `audit_trail` | Grava audit log | Forward ao audit service |
| `email_sent` | Envio de email | Rate limiting, dedup |
| `webhook_fired` | Dispara webhook | Replay protection |
| `whatsapp_sent` | Envio via WhatsApp | Rate limiting por tenant |
| `mock_only` | Só mock | Skip em produção |
| `write_destructive` | Destrutivo | Sempre com HITL |

---
"""


def render_tool(tool: dict, invocations: list[str]) -> str:
    name = tool.get("name", "?")
    description = (tool.get("description") or "").strip()
    when_to_use = (tool.get("when_to_use") or "").strip()
    when_not_to_use = (tool.get("when_not_to_use") or "").strip()
    governance = tool.get("governance_tags") or []
    related = tool.get("related_tools") or []
    side_effects = tool.get("side_effects") or []
    allowed_agents = tool.get("allowed_agents") or []
    scope = tool.get("scope", "n/a")
    version = tool.get("version", "—")
    parameters = tool.get("parameters", {})

    # Block quote for multi-line descriptions
    def blockquote(text: str) -> str:
        if not text:
            return "_(vazio)_"
        return "\n".join(f"> {line}" for line in text.split("\n"))

    md = f"### `{name}`\n\n"
    md += "**Descrição completa:**\n"
    md += blockquote(description) + "\n\n"

    if when_to_use:
        md += "**USE WHEN:**\n"
        md += blockquote(when_to_use) + "\n\n"
    if when_not_to_use:
        md += "**DO NOT USE WHEN:**\n"
        md += blockquote(when_not_to_use) + "\n\n"

    md += "**Campos técnicos:**\n\n"
    md += "| Campo | Valor |\n|-------|-------|\n"
    md += f"| `governance_tags` | `{governance}` |\n"
    md += f"| `side_effects` | `{side_effects}` |\n"
    md += f"| `related_tools` | `{related}` |\n"
    md += f"| `allowed_agents` | `{allowed_agents}` |\n"
    md += f"| `scope` | `{scope}` |\n"
    md += f"| `version` | `{version}` |\n\n"

    if parameters:
        md += "**Parameters schema:**\n\n```json\n"
        md += json.dumps(parameters, indent=2, ensure_ascii=False)
        md += "\n```\n\n"

    if invocations:
        md += f"**Invocada pelas DomainActions:** `{'`, `'.join(invocations)}`\n\n"

    md += "---\n\n"
    return md


def render_domain_action(domain: str, action: dict, tool_map: dict[str, str]) -> str:
    aid = action.get("action_id", "?")
    name = action.get("name", "")
    description = (action.get("description") or "").strip()
    examples = action.get("examples") or ()
    requires_conf = action.get("requires_confirmation", False)
    tags = action.get("tags") or []
    req_params = action.get("required_params") or []
    opt_params = action.get("optional_params") or []

    md = f"### `{aid}` — {name}\n\n"
    md += "**Descrição completa:**\n"
    md += "\n".join(f"> {line}" for line in description.split("\n")) + "\n\n"

    if examples:
        md += "**Examples (few-shot):**\n"
        for ex in examples:
            md += f"- `\"{ex}\"`\n"
        md += "\n"

    md += "**Campos técnicos:**\n\n"
    md += "| Campo | Valor |\n|-------|-------|\n"
    md += f"| `requires_confirmation` | `{requires_conf}` |\n"
    md += f"| `required_params` | `{req_params}` |\n"
    md += f"| `optional_params` | `{opt_params}` |\n"
    md += f"| `tags` | `{tags}` |\n\n"

    if aid in tool_map:
        md += f"**Tool mapping:** `{aid}` → `{tool_map[aid]}`\n\n"

    md += "---\n\n"
    return md


def render_clusters() -> str:
    return """## Clusters semânticos disambiguados (FIX 7+11)

Três grupos de ações similares foram identificadas como fonte de confusão no LLM. FIX 7 e FIX 11 adicionaram cross-references nas descriptions.

### Cluster 1 — Melhorar Job Description (job_management)

| action_id | Comportamento |
|-----------|---------------|
| `generate_jd` | Cria JD do zero com IA |
| `enrich_jd` | Enriquece JD existente, aplicando melhorias |
| `suggest_jd_improvements` | Só sugere edições, não sobrescreve |

Cada uma referencia as outras no texto de `description` via `Distinto de X (que ...)`.

### Cluster 2 — Buscar candidatos (sourcing)

| action_id | Comportamento |
|-----------|---------------|
| `auto_source` | Sourcing automático com outreach |
| `suggest_candidates` | Sugere perfis para revisão manual |
| `talent_pool_search` | Busca só no pool interno, sem sourcing externo |

### Cluster 3 — Perguntas WSI (job_management vs cv_screening)

| action_id | Domínio | Quando usar |
|-----------|---------|-------------|
| `generate_wsi_questions` | `job_management` | Na configuração da vaga, antes da triagem começar |
| _(dinamicamente)_ | `cv_screening` | Durante a triagem, adaptando por candidato |

`generate_wsi_questions` em `job_management/actions.py` tem cross-ref explícito para o fluxo em `cv_screening`.

---
"""


def render_footer(tool_count: int, action_count: int, domain_count: int) -> str:
    today = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return f"""## Estatísticas

- **{tool_count}** ferramentas (tools) no registry
- **{action_count}** DomainActions em **{domain_count}** domínios
- Geração automática via `scripts/generate_tool_action_glossary.py`

## Regenerar este documento

```bash
# Em lia-agent-system/ root:
python scripts/generate_tool_action_glossary.py

# Ou em CI:
python scripts/generate_tool_action_glossary.py --check  # exit 1 se stale
```

## Ver também

- [`docs/LIA_AI_HANDOFF.md`](./LIA_AI_HANDOFF.md) — Handoff técnico das 12 melhorias
- [`docs/specs/ai/ADR-019-governance-and-observability.md`](./specs/ai/ADR-019-governance-and-observability.md) — Decisões arquiteturais
- [`docs/specs/CANONICAL_SOURCES_SPEC.md`](./specs/CANONICAL_SOURCES_SPEC.md) — Registry canônico
- [`app/tools/tool_registry_metadata.yaml`](../app/tools/tool_registry_metadata.yaml) — fonte YAML

*Última regeneração: {today}*
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Dry run: exit 1 if output differs from current file")
    parser.add_argument("--output", default=None, help="Override output path")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else OUTPUT_PATH

    tools = load_tools()
    domain_actions, domain_tool_maps, tool_invocations = collect_all_domain_data()

    # Build
    parts: list[str] = []
    parts.append(render_header())
    parts.append(render_governance_glossary())
    parts.append(render_side_effects_glossary())

    # Tools section
    parts.append(f"## Tools ({len(tools)} entries)\n\n")
    for tool in tools:
        parts.append(render_tool(tool, sorted(tool_invocations.get(tool.get("name", ""), []))))

    # DomainActions section
    total_actions = sum(len(actions) for actions in domain_actions.values())
    parts.append(f"## DomainActions ({total_actions} entries em {len(domain_actions)} domínios)\n\n")
    for domain, actions in sorted(domain_actions.items()):
        parts.append(f"### Domínio: `{domain}` ({len(actions)} actions)\n\n")
        tool_map = domain_tool_maps.get(domain, {})
        for action in actions:
            parts.append(render_domain_action(domain, action, tool_map))

    # Clusters
    parts.append(render_clusters())

    # Tool → Action reverse index
    parts.append("## Reverse index — Tool → DomainActions que a invocam\n\n")
    parts.append("| Tool | Invocada por |\n|------|---------------|\n")
    for tool_name in sorted(tool_invocations.keys()):
        refs = ", ".join(f"`{r}`" for r in sorted(tool_invocations[tool_name]))
        parts.append(f"| `{tool_name}` | {refs} |\n")
    parts.append("\n---\n\n")

    # Footer
    parts.append(render_footer(len(tools), total_actions, len(domain_actions)))

    new_content = "".join(parts)

    # Check mode
    if args.check:
        if not output_path.exists():
            print(f"FAIL: {output_path} does not exist. Run without --check to generate.")
            return 1
        existing = output_path.read_text()
        # Strip timestamps for comparison
        def strip_ts(text: str) -> str:
            import re
            return re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC", "<TS>", text)
        if strip_ts(new_content) != strip_ts(existing):
            print(f"FAIL: {output_path} is stale. Regenerate with: python scripts/generate_tool_action_glossary.py")
            return 1
        print(f"OK: {output_path} up to date.")
        return 0

    # Write
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(new_content)
    print(f"✓ Generated {output_path}")
    print(f"  {len(tools)} tools · {total_actions} domain actions · {len(domain_actions)} domains")
    print(f"  {len(new_content):,} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
