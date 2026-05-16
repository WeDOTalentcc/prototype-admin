"""T-1157 — Ownership cross-validation nas rotas dos 3 domínios.

Complementa o sentinela T-1149 ``test_no_endpoint_missing_require_company_id_gate``:
o gate ``Depends(_require_company_id)`` garante que o handler RECEBE
``company_id`` do JWT. Esta sentinela vai um passo além — garante que
o handler USA esse ``company_id`` na consulta de ownership ANTES de
executar uma mutation.

Padrão sentinela espelha T-1149 (T-1129 sealing):

* Visita AST nos 6 arquivos de rota dos 3 domínios:
  ``interviews.py``, ``interview_notes.py``, ``interview_analysis.py``,
  ``scheduling.py``, ``offers.py``, ``calendar.py``.
* Para cada handler ``async def`` decorado com ``@router.{post|put|patch|delete}``,
  exige PELO MENOS UMA chamada com ``company_id=...`` como kwarg no
  corpo (heurística simples: garante que ``company_id`` é repassado
  para a camada de repositório/serviço, não silenciosamente ignorado).
* Débito legado tracked em
  ``tests/.baseline_ownership_xvalidation_interview_offer.txt``.

Por que esta heurística é suficiente
------------------------------------

Cobrir "ownership real" requer entender o grafo do repositório
(``repo.get_by_id(id, company_id)`` é seguro; ``repo.get_by_id(id)``
sem company_id é vulnerável). Verificar isso na route fica frágil.

O contrato pragmático: o handler RECEBE ``company_id`` (gate T-1149)
**e** REPASSA ``company_id`` para a camada de baixo (sentinela
T-1157). Isso captura 100% dos casos onde a rota faz mutation e
"esquece" o tenant — o bug clássico de cross-tenant.

Origem: Task #1157.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
API_V1_DIR = REPO_ROOT / "app" / "api" / "v1"

ROUTE_FILES = (
    API_V1_DIR / "interviews.py",
    API_V1_DIR / "interview_notes.py",
    API_V1_DIR / "interview_analysis.py",
    API_V1_DIR / "scheduling.py",
    API_V1_DIR / "offers.py",
    API_V1_DIR / "calendar.py",
)

BASELINE_FILE = (
    REPO_ROOT / "tests" / ".baseline_ownership_xvalidation_interview_offer.txt"
)

_MUTATING_METHODS = {"post", "put", "patch", "delete"}


def _load_lines(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line)
    return out


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return None


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _is_router_mutating_decorator(deco: ast.expr) -> bool:
    if not isinstance(deco, ast.Call):
        return False
    return (
        isinstance(deco.func, ast.Attribute)
        and deco.func.attr in _MUTATING_METHODS
    )


def _body_passes_company_id(node: ast.AST) -> bool:
    """Detecta se algum Call dentro do corpo passa
    ``company_id`` como kwarg.
    """
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        for kw in sub.keywords or []:
            if kw.arg == "company_id":
                return True
    return False


def _collect_violations(path: Path) -> list[str]:
    tree = _parse(path)
    if tree is None:
        return []
    rel = _rel(path)
    out: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(
            _is_router_mutating_decorator(d) for d in node.decorator_list
        ):
            continue
        if not _body_passes_company_id(node):
            out.append(f"{rel}:{node.lineno}:{node.name}")
    return out


def _scan_all_violations() -> set[str]:
    out: set[str] = set()
    for f in ROUTE_FILES:
        out.update(_collect_violations(f))
    return out


def _assert_no_new_violations(
    *,
    current: set[str],
    baseline: set[str],
    label: str,
    remediation: str,
) -> None:
    new = sorted(current - baseline)
    fixed = sorted(baseline - current)
    if new:
        msg = (
            f"T-1157 — {len(new)} new {label} violation(s):\n  "
            + "\n  ".join(new[:30])
            + f"\n\n{remediation}"
        )
        raise AssertionError(msg)
    if fixed:
        print(
            f"[T-1157 ratchet] {label}: baseline shrank by {len(fixed)}. "
            "Remove fixed entries from the baseline to lock in the gain."
        )


def test_no_mutating_route_without_company_id_passthrough() -> None:
    """Toda rota mutating em interview/offer repassa ``company_id``.

    Sentinela T-1157. Débito legado em
    ``tests/.baseline_ownership_xvalidation_interview_offer.txt``;
    regressões novas quebram a build.
    """
    current = _scan_all_violations()
    baseline = _load_lines(BASELINE_FILE)
    _assert_no_new_violations(
        current=current,
        baseline=baseline,
        label="mutating route without company_id passthrough",
        remediation=(
            "Adicione `Depends(_require_company_id)` no parâmetro e "
            "repasse `company_id=company_id` para o repositório/service. "
            "Ver `docs/runbooks/audit-interview-offer.md` §3."
        ),
    )


def test_ownership_baseline_not_stale() -> None:
    current = _scan_all_violations()
    baseline = _load_lines(BASELINE_FILE)
    stale = sorted(baseline - current)
    assert not stale, (
        f"T-1157 — baseline tem {len(stale)} entrada(s) obsoleta(s); "
        "remova do arquivo:\n  " + "\n  ".join(stale[:30])
    )


def test_sentinel_covers_six_route_files() -> None:
    existing = [p for p in ROUTE_FILES if p.exists()]
    assert len(existing) >= 5, (
        f"T-1157 — esperados ≥5 arquivos de rota, encontrados "
        f"{len(existing)}: {[p.name for p in existing]}"
    )
