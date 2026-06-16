"""
GAP-11-007 — LIAError adoption ratchet.

Prevents regression: HTTPException(500) count in app/api/v1/ must
stay at or below the current baseline. Each sprint: fix a batch,
lower RATCHET_MAX.

Ratchet history:
  2026-06-16: 835 (initial baseline recorded by 0e59dccac)
  2026-06-16: 163 (GAP-11-007 bulk-fix: 672 common patterns replaced)
"""
import ast
import os

RATCHET_MAX = 163  # GREEN: 2026-06-16 bulk-fix 672 common patterns → 163 remaining


class _HTTPException500Finder(ast.NodeVisitor):
    def __init__(self):
        self.count = 0

    def visit_Raise(self, node: ast.Raise):
        call = node.exc
        if not isinstance(call, ast.Call):
            self.generic_visit(node)
            return
        func = call.func
        if isinstance(func, ast.Name):
            fname = func.id
        elif isinstance(func, ast.Attribute):
            fname = func.attr
        else:
            self.generic_visit(node)
            return
        if fname != "HTTPException":
            self.generic_visit(node)
            return
        for kw in call.keywords:
            if kw.arg == "status_code" and isinstance(kw.value, ast.Constant) and kw.value.value == 500:
                self.count += 1
                return
        if call.args and isinstance(call.args[0], ast.Constant) and call.args[0].value == 500:
            self.count += 1
        self.generic_visit(node)


def _count_violations(base: str) -> int:
    total = 0
    for root, _, files in os.walk(base):
        if "__pycache__" in root:
            continue
        for fname in files:
            if not fname.endswith(".py") or fname.startswith("test_"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    tree = ast.parse(f.read(), filename=fpath)
                finder = _HTTPException500Finder()
                finder.visit(tree)
                total += finder.count
            except SyntaxError:
                pass
    return total


def test_lia_error_ratchet_no_regression():
    """GAP-11-007: HTTPException(500) count must stay at or below RATCHET_MAX."""
    api_dir = "app/api/v1"
    assert os.path.isdir(api_dir), f"Run from lia-agent-system root; missing {api_dir}"
    count = _count_violations(api_dir)
    assert count <= RATCHET_MAX, (
        f"LIAError adoption regressed: {count} HTTPException(500) violations "
        f"(max allowed: {RATCHET_MAX}). "
        f"Fix by replacing 'raise HTTPException(status_code=500, ...)' with "
        f"'raise LIAError(...)' from app.shared.errors. "
        f"See GAP-11-007 in audit_gaps_consolidado_2026-06-16.md."
    )
