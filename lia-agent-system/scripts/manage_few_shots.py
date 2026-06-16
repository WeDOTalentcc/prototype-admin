#!/usr/bin/env python3
"""W4-038 · CLI canonical para gerenciar few_shot_examples em prompt YAMLs.

Uso:
    python scripts/manage_few_shots.py list --domain automation
    python scripts/manage_few_shots.py validate
    python scripts/manage_few_shots.py validate --domain communication
    python scripts/manage_few_shots.py add --domain automation \\
        --id automation-ex-99 --category happy_path \\
        --scenario "Test scenario" --user-input "Test input" \\
        --expected-response "Test response" --demonstrates tag1,tag2
    python scripts/manage_few_shots.py prune --domain automation --keep-recent 10

Subcommands:
- list      — lista exemplos de um domain
- validate  — roda schema sensor (igual scripts/check_few_shot_yaml_schema.py)
- add       — adiciona exemplo manual (ID slug auto se omitted)
- prune     — remove auto_evolved entries antigas (FIFO)

Atomic edits via backup *.yaml.bak (rollback se YAML write falha).
NÃO faz commit git — usuário decide quando commitar.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DOMAINS = REPO_ROOT / "app" / "prompts" / "domains"


def _load_yaml(path: Path) -> dict | None:
    try:
        import yaml
    except ImportError:
        print("ERROR: pyyaml not installed", file=sys.stderr)
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _save_yaml(path: Path, data: dict) -> None:
    import yaml
    # Backup
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)
    try:
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
        )
    except Exception:
        # Rollback
        shutil.copy2(backup, path)
        raise


def _resolve_domain(domain: str) -> Path:
    p = PROMPTS_DOMAINS / f"{domain}.yaml"
    if not p.exists():
        raise SystemExit(f"Domain YAML não encontrado: {p}")
    return p


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> int:
    path = _resolve_domain(args.domain)
    data = _load_yaml(path) or {}
    examples = data.get("few_shot_examples") or []
    print(f"\n[{args.domain}] {len(examples)} examples:\n")
    for ex in examples:
        if not isinstance(ex, dict):
            print(f"  ⚠  non-dict entry: {ex!r}")
            continue
        eid = ex.get("id", "?")
        cat = ex.get("category", "?")
        scen = (ex.get("scenario") or "")[:60]
        print(f"  - {eid:20s} [{cat:20s}] {scen}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    # Delegate ao sensor canonical
    import subprocess
    sensor = REPO_ROOT / "scripts" / "check_few_shot_yaml_schema.py"
    cmd = [sys.executable, str(sensor)]
    if args.blocking:
        cmd.append("--blocking")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def cmd_add(args: argparse.Namespace) -> int:
    path = _resolve_domain(args.domain)
    data = _load_yaml(path) or {}
    examples = data.setdefault("few_shot_examples", [])

    # Resolve id slug
    eid = args.id
    if not eid:
        existing_ids = {e.get("id") for e in examples if isinstance(e, dict)}
        for n in range(1, 100):
            candidate = f"{args.domain}-ex-{n:02d}"
            if candidate not in existing_ids:
                eid = candidate
                break

    # Sanity: dup check
    for e in examples:
        if isinstance(e, dict) and e.get("id") == eid:
            raise SystemExit(f"ERROR: id={eid!r} já existe em {path}")

    new_entry = {
        "id": eid,
        "category": args.category,
        "scenario": args.scenario,
        "user_input": args.user_input,
        "expected_response": args.expected_response,
    }
    if args.demonstrates:
        new_entry["demonstrates"] = [t.strip() for t in args.demonstrates.split(",") if t.strip()]

    examples.append(new_entry)
    _save_yaml(path, data)
    print(f"✅ Added {eid} to {args.domain} (total: {len(examples)} examples)")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    path = _resolve_domain(args.domain)
    data = _load_yaml(path) or {}
    examples = data.get("few_shot_examples") or []
    if not examples:
        print(f"No examples in {args.domain}")
        return 0

    # Separa auto_evolved (FIFO candidates) vs manual
    auto = [e for e in examples if isinstance(e, dict) and e.get("category") == "auto_evolved"]
    manual = [e for e in examples if isinstance(e, dict) and e.get("category") != "auto_evolved"]

    keep_auto = args.keep_recent
    if len(auto) <= keep_auto:
        print(f"No prune needed (auto_evolved={len(auto)} <= keep_recent={keep_auto})")
        return 0

    # FIFO: drop oldest from start
    to_drop = auto[: len(auto) - keep_auto]
    survivors = auto[len(auto) - keep_auto :]
    data["few_shot_examples"] = manual + survivors

    print(f"⚠  Pruning {len(to_drop)} auto_evolved entries from {args.domain}:")
    for e in to_drop:
        print(f"  - {e.get('id')} [{e.get('scenario', '')[:50]}]")

    _save_yaml(path, data)
    print(f"✅ Pruned. Remaining: {len(data['few_shot_examples'])} examples")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="W4-038 · few_shot_examples management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subs = parser.add_subparsers(dest="cmd", required=True)

    p_list = subs.add_parser("list", help="lista exemplos de um domain")
    p_list.add_argument("--domain", required=True)
    p_list.set_defaults(func=cmd_list)

    p_val = subs.add_parser("validate", help="roda schema sensor")
    p_val.add_argument("--blocking", action="store_true")
    p_val.set_defaults(func=cmd_validate)

    p_add = subs.add_parser("add", help="adiciona exemplo manual")
    p_add.add_argument("--domain", required=True)
    p_add.add_argument("--id", help="slug único (auto se omitted)")
    p_add.add_argument("--category", required=True)
    p_add.add_argument("--scenario", required=True)
    p_add.add_argument("--user-input", required=True)
    p_add.add_argument("--expected-response", required=True)
    p_add.add_argument("--demonstrates", help="comma-separated tags")
    p_add.set_defaults(func=cmd_add)

    p_prune = subs.add_parser("prune", help="FIFO remove auto_evolved antigos")
    p_prune.add_argument("--domain", required=True)
    p_prune.add_argument("--keep-recent", type=int, default=10)
    p_prune.set_defaults(func=cmd_prune)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
