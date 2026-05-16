"""Fix functions with a duplicate ``company_id`` argument.

The enforcer (enforce_require_company_id.py) injects
``company_id: str = Depends(require_company_id)`` as the last parameter.
When the endpoint already had its own ``company_id`` parameter (e.g. a
Path / Query / Body field), this produces an invalid function definition
(``SyntaxError: duplicate argument 'company_id'``).

This pass walks every ``app/api/**/*.py`` file and, for any function
with two ``company_id`` parameters, renames the GATE injection (the one
whose default is ``Depends(require_company_id)`` or
``Depends(require_company_id_strict_match(...))``) to ``_company_gate``.

It also opportunistically upgrades the gate to
``require_company_id_strict_match(...)`` when the source of the
pre-existing ``company_id`` is detectable (Path / Query / Body /
plain — falls back to the unscoped helper).

Idempotent.
"""
from __future__ import annotations

import sys
from pathlib import Path

import libcst as cst

ROOT = Path(__file__).resolve().parent.parent
HELPER_NAME = "require_company_id"
STRICT_NAME = "require_company_id_strict_match"
HELPER_MODULE = "app.shared.security.require_company_id"


def _is_gate_default(default) -> bool:
    if not isinstance(default, cst.Call):
        return False
    if not (isinstance(default.func, cst.Name) and default.func.value == "Depends"):
        return False
    for a in default.args:
        v = a.value
        if isinstance(v, cst.Name) and v.value == HELPER_NAME:
            return True
        if isinstance(v, cst.Call) and isinstance(v.func, cst.Name) \
                and v.func.value == STRICT_NAME:
            return True
    return False


def _detect_source(other_param: cst.Param) -> str | None:
    """Return 'path.company_id' / 'query.company_id' / 'body.company_id'
    based on FastAPI helper in other_param's default."""
    d = other_param.default
    if isinstance(d, cst.Call) and isinstance(d.func, cst.Name):
        n = d.func.value
        if n == "Path":
            return "path.company_id"
        if n == "Query":
            return "query.company_id"
        if n == "Body":
            return "body.company_id"
    # If annotated with Path/Query/Body inside Annotated[...] etc., skip
    # for safety — fall back to plain require_company_id.
    return None


class FixTransformer(cst.CSTTransformer):
    def __init__(self) -> None:
        self.renamed = 0
        self.upgraded_to_strict = 0

    def leave_FunctionDef(self, original, updated):
        params = list(updated.params.params) + list(updated.params.kwonly_params)
        names = [p.name.value for p in params if isinstance(p.name, cst.Name)]
        if names.count("company_id") < 2:
            return updated

        # Find the gate one (injected) and the other (pre-existing).
        gate_idx = -1
        other_param: cst.Param | None = None
        for i, p in enumerate(params):
            if isinstance(p.name, cst.Name) and p.name.value == "company_id":
                if _is_gate_default(p.default):
                    gate_idx = i
                else:
                    other_param = p

        if gate_idx == -1 or other_param is None:
            # Both look like gates (unlikely) — leave alone.
            return updated

        gate_param = params[gate_idx]
        # Detect source and upgrade if possible.
        source = _detect_source(other_param)
        if source is not None:
            new_default = cst.Call(
                func=cst.Name("Depends"),
                args=[cst.Arg(value=cst.Call(
                    func=cst.Name(STRICT_NAME),
                    args=[cst.Arg(value=cst.SimpleString(f'"{source}"'))],
                ))],
            )
            self.upgraded_to_strict += 1
        else:
            new_default = gate_param.default  # keep plain require_company_id

        new_gate = gate_param.with_changes(
            name=cst.Name("_company_gate"),
            default=new_default,
        )
        self.renamed += 1

        # Rebuild params list. The gate is always in updated.params.params
        # because the enforcer injects regular (non-kwonly) params.
        new_regular = []
        regular_params = list(updated.params.params)
        regular_idx = 0
        for p in regular_params:
            if (isinstance(p.name, cst.Name) and p.name.value == "company_id"
                    and _is_gate_default(p.default)):
                new_regular.append(new_gate)
            else:
                new_regular.append(p)
            regular_idx += 1

        return updated.with_changes(
            params=updated.params.with_changes(params=tuple(new_regular))
        )


def process_file(path: Path, apply: bool) -> dict:
    src = path.read_text(encoding="utf-8")
    if "company_id" not in src:
        return {"path": str(path), "skipped": True}
    try:
        tree = cst.parse_module(src)
    except cst.ParserSyntaxError as e:
        return {"path": str(path), "error": f"parse: {e}"}
    transformer = FixTransformer()
    new_tree = tree.visit(transformer)
    if transformer.renamed == 0:
        return {"path": str(path), "renamed": 0}
    new_src = new_tree.code
    # Sanity compile.
    try:
        compile(new_src, str(path), "exec")
    except SyntaxError as e:
        return {"path": str(path), "error": f"post_edit: {e}"}
    if apply:
        path.write_text(new_src, encoding="utf-8")
    return {
        "path": str(path),
        "renamed": transformer.renamed,
        "upgraded_to_strict": transformer.upgraded_to_strict,
    }


def main() -> int:
    apply = "--apply" in sys.argv
    totals = {"files": 0, "renamed": 0, "strict": 0, "errors": 0}
    for p in sorted((ROOT / "app" / "api").rglob("*.py")):
        r = process_file(p, apply)
        if r.get("error"):
            totals["errors"] += 1
            print(f"  ERR {r['path']}: {r['error']}")
        elif r.get("renamed", 0) > 0:
            totals["files"] += 1
            totals["renamed"] += r["renamed"]
            totals["strict"] += r.get("upgraded_to_strict", 0)
    print(f"[fix_duplicate_company_id] mode={'APPLY' if apply else 'DRY-RUN'} "
          f"files={totals['files']} renamed={totals['renamed']} "
          f"upgraded_to_strict={totals['strict']} errors={totals['errors']}")
    return 0 if totals["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
