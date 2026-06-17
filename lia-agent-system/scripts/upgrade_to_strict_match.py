"""Upgrade plain require_company_id gates to require_company_id_strict_match
whenever a sibling parameter accepts company_id from path/query/body/form
and a JWT-vs-payload mismatch could otherwise slip through.

Detects these patterns on the same endpoint function:
- A gate param: ``X: ... = Depends(require_company_id)`` where X is
  ``company_id`` or ``_company_gate``.
- A sibling param named ``company_id`` whose source is one of:
  * Explicit:  ``Path(...)`` / ``Query(...)`` / ``Body(...)`` / ``Form(...)``.
  * Implicit path: ``company_id: str`` AND the function decorator route
    string contains ``{company_id}``.
  * Implicit query: ``company_id: str`` AND route string does NOT contain
    ``{company_id}`` (FastAPI infers a query param for scalar types).

Rewrites the gate's default to
``Depends(require_company_id_strict_match("path.company_id" | ...))``.

Pydantic-model body params with a ``company_id`` field are NOT auto-
detected here (would require model introspection); add explicit
``Body(...)`` accessor on the field or invoke the helper manually.

Idempotent.
"""
from __future__ import annotations

import sys
from pathlib import Path

import libcst as cst

ROOT = Path(__file__).resolve().parent.parent
HELPER = "require_company_id"
STRICT = "require_company_id_strict_match"
SOURCE_MAP = {"Path": "path", "Query": "query", "Body": "body", "Form": "form"}


def _is_plain_gate(default) -> bool:
    if not isinstance(default, cst.Call):
        return False
    if not (isinstance(default.func, cst.Name) and default.func.value == "Depends"):
        return False
    for a in default.args:
        if isinstance(a.value, cst.Name) and a.value.value == HELPER:
            return True
    return False


def _detect_source(p: cst.Param, route_path: str | None) -> str | None:
    d = p.default
    if isinstance(d, cst.Call) and isinstance(d.func, cst.Name):
        kind = SOURCE_MAP.get(d.func.value)
        if kind:
            return f"{kind}.company_id"
    # Implicit path/query inference for scalar params with no FastAPI source.
    # FastAPI: scalar type + name in route template → path; else → query.
    if d is None and route_path is not None:
        ann = p.annotation
        is_scalar = False
        if ann is not None and isinstance(ann.annotation, cst.Name) \
                and ann.annotation.value in ("str", "int", "UUID", "float"):
            is_scalar = True
        if is_scalar:
            if "{company_id}" in route_path:
                return "path.company_id"
            return "query.company_id"
    return None


def _extract_route_path(decorators) -> str | None:
    """Find the literal path passed to @router.get/post/put/.../delete()."""
    for dec in decorators:
        call = dec.decorator
        if not isinstance(call, cst.Call):
            continue
        # Only @router.<method>(...) style.
        if not (isinstance(call.func, cst.Attribute)
                and call.func.attr.value in ("get", "post", "put", "patch", "delete")):
            continue
        for a in call.args:
            if isinstance(a.value, cst.SimpleString):
                return a.value.evaluated_value
    return None


class Upgrader(cst.CSTTransformer):
    def __init__(self) -> None:
        self.upgraded = 0

    def leave_FunctionDef(self, original, updated):
        params = list(updated.params.params) + list(updated.params.kwonly_params)
        route_path = _extract_route_path(updated.decorators)

        # Find sibling explicit-source company_id (or implicit path/query).
        source = None
        for p in params:
            if isinstance(p.name, cst.Name) and p.name.value == "company_id":
                s = _detect_source(p, route_path)
                if s is not None:
                    source = s
                    break
        if source is None:
            return updated

        # Find plain gate param.
        new_regular = []
        changed = False
        for p in updated.params.params:
            if isinstance(p.name, cst.Name) and p.name.value in ("company_id", "_company_gate") \
                    and _is_plain_gate(p.default):
                if p.name.value == "company_id":
                    # Don't shadow the explicit-source param: rename gate.
                    new_name = cst.Name("_company_gate")
                else:
                    new_name = p.name
                new_default = cst.Call(
                    func=cst.Name("Depends"),
                    args=[cst.Arg(value=cst.Call(
                        func=cst.Name(STRICT),
                        args=[cst.Arg(value=cst.SimpleString(f'"{source}"'))],
                    ))],
                )
                new_regular.append(p.with_changes(name=new_name, default=new_default))
                changed = True
                self.upgraded += 1
            else:
                new_regular.append(p)
        if not changed:
            return updated
        return updated.with_changes(
            params=updated.params.with_changes(params=tuple(new_regular))
        )


def process(path: Path, apply: bool) -> int:
    src = path.read_text(encoding="utf-8")
    if HELPER not in src:
        return 0
    try:
        tree = cst.parse_module(src)
    except cst.ParserSyntaxError:
        return 0
    up = Upgrader()
    new_tree = tree.visit(up)
    if up.upgraded == 0:
        return 0
    new_src = new_tree.code
    # Ensure strict import.
    if STRICT not in new_src.splitlines()[0] and f"import {STRICT}" not in new_src \
            and f"{STRICT}," not in new_src and f", {STRICT}" not in new_src:
        import re
        m = re.search(r"from\s+app\.shared\.security\.require_company_id\s+import\s+([^\n]+)", new_src)
        if m and STRICT not in m.group(1):
            new_src = new_src.replace(m.group(0), m.group(0).rstrip() + f", {STRICT}")
    try:
        compile(new_src, str(path), "exec")
    except SyntaxError:
        return 0
    if apply:
        path.write_text(new_src, encoding="utf-8")
    return up.upgraded


def main() -> int:
    apply = "--apply" in sys.argv
    total_files = 0
    total_upgrades = 0
    for p in sorted((ROOT / "app" / "api").rglob("*.py")):
        n = process(p, apply)
        if n > 0:
            total_files += 1
            total_upgrades += n
    print(f"[upgrade_to_strict_match] mode={'APPLY' if apply else 'DRY-RUN'} "
          f"files={total_files} upgrades={total_upgrades}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
