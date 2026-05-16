"""T-1157 — Audit obrigatório nos services dos 3 domínios:
``interview_scheduling``, ``interview_intelligence``, ``offer``.

Padrão sentinela espelha T-1149 (T-1129 sealing):

* Visita AST nos services dos 3 domínios.
* Para cada ``async def`` PÚBLICO (nome sem ``_`` inicial e fora do
  prefixo getter) que faz mutação (``db.commit``, ``session.commit``,
  ``_repo.create``, ``_repo.update``, ``_repo.delete``, ``db.add``,
  ``session.add``), exige uma chamada a ``log_decision`` ou
  ``log_decision_in_session`` no corpo (direto ou via método chamado
  no mesmo objeto, ex.: ``await self._audit(...)``).
* Débito legado tracked em ``tests/.baseline_audit_missing_interview_offer.txt``.
* Regressão (método NOVO sem audit) quebra o build.

Por que isso importa
--------------------

Os 3 domínios fazem mutações de alto valor para SOX, LGPD e WSI:

* ``offer_service`` — proposta formal de remuneração ao candidato
  (SOX 7-year retention, hiring decision).
* ``scheduling_service`` — entrevista marcada (LGPD; aciona evento
  ``on_interview_scheduled`` no pipeline).
* ``transcription_service`` — transcrição de áudio é PII sensível
  (LGPD Art.46, mascaramento via ``PIIMaskingFilter``).

Sem audit, não conseguimos reconstruir "por que essa entrevista foi
marcada" / "quem cancelou esta offer" — falha de SOX e EU AI Act.

Origem: Task #1157 (T-1149 follow-up).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
APP_DIR = REPO_ROOT / "app"
SERVICE_DIRS = (
    APP_DIR / "domains" / "interview_scheduling" / "services",
    APP_DIR / "domains" / "interview_intelligence" / "services",
    APP_DIR / "domains" / "offer" / "services",
)
BASELINE_FILE = REPO_ROOT / "tests" / ".baseline_audit_missing_interview_offer.txt"

# Métodos que indicam mutação no DB (basta UM para o método ser
# considerado "mutating").
_MUTATION_METHOD_NAMES = {
    "commit", "add", "delete", "merge",
    "create", "update", "upsert", "save",
    "bulk_save", "bulk_save_objects",
    "create_or_get_draft",  # OfferRepository.create
}
# Receivers válidos para considerar mutação (evita falsos positivos
# em ``list.append``, ``set.add`` etc.).
_MUTATION_RECEIVERS = {
    "db", "session", "self._db", "self._session",
    "_repo", "self._repo", "repo", "self.repo",
    "_db",
}
# Audit symbols — qualquer chamada cujo nome ou attr final esteja aqui
# satisfaz o requisito.
_AUDIT_SYMBOLS = {
    "log_decision",
    "log_decision_in_session",
    "log_action",  # legacy AuditService.log_action
    "audit_company_change",  # wrapper canônico do company_settings
}
# Prefixos de nome que indicam read-only (não exigem audit).
_READONLY_PREFIXES = (
    "get_", "find_", "list_", "query_", "fetch_", "load_", "read_",
    "compute_", "calc_", "render_", "format_", "serialize_", "build_",
    "is_", "has_", "can_", "resolve_", "check_", "validate_",
    "search_", "count_", "exists_", "summarize_",
    "generate_ics", "generate_token",  # helpers puros
)
# Nomes inteiros explicitamente isentos (fora dos prefixos).
_EXEMPT_NAMES = {
    "to_dict",
    "from_dict",
    "as_dict",
    "send_interview_confirmation",  # comunicação, não mutation de domínio
    "send_message",
}


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


def _iter_python_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        p for p in root.rglob("*.py")
        if "__pycache__" not in p.parts and p.name != "__init__.py"
    )


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return None


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _violation_key(rel: str, lineno: int, name: str) -> str:
    return f"{rel}:{lineno}:{name}"


def _method_is_exempt(name: str) -> bool:
    if name.startswith("_"):
        return True
    if name in _EXEMPT_NAMES:
        return True
    return any(name.startswith(p) for p in _READONLY_PREFIXES)


def _receiver_token(expr: ast.expr) -> str | None:
    """Compress receiver to a comparable token (e.g., ``self._db`` →
    ``"self._db"``; ``db`` → ``"db"``).
    """
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        inner = _receiver_token(expr.value)
        return f"{inner}.{expr.attr}" if inner else None
    return None


class _MutationVisitor(ast.NodeVisitor):
    """Detecta mutation calls e audit calls dentro de UM método."""

    def __init__(self) -> None:
        self.has_mutation = False
        self.has_audit = False

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        # Audit detection (qualquer chamada com .attr ou .id em
        # _AUDIT_SYMBOLS satisfaz, independente do receiver).
        f = node.func
        called_name = (
            f.id if isinstance(f, ast.Name)
            else f.attr if isinstance(f, ast.Attribute)
            else None
        )
        if called_name in _AUDIT_SYMBOLS:
            self.has_audit = True

        # Mutation detection: ``<recv>.<method>(...)`` onde método está
        # em _MUTATION_METHOD_NAMES e receiver token está em
        # _MUTATION_RECEIVERS (ou termina em ``_repo``).
        if (
            isinstance(f, ast.Attribute)
            and f.attr in _MUTATION_METHOD_NAMES
        ):
            recv = _receiver_token(f.value)
            if recv and (
                recv in _MUTATION_RECEIVERS
                or recv.endswith("_repo")
                or recv.endswith(".db")
                or recv.endswith(".session")
            ):
                self.has_mutation = True

        self.generic_visit(node)


def _collect_violations(path: Path) -> list[str]:
    tree = _parse(path)
    if tree is None:
        return []
    rel = _rel(path)
    out: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for member in node.body:
            if not isinstance(member, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            if _method_is_exempt(member.name):
                continue
            visitor = _MutationVisitor()
            for stmt in member.body:
                visitor.visit(stmt)
            if visitor.has_mutation and not visitor.has_audit:
                out.append(_violation_key(rel, member.lineno, member.name))
    return out


def _scan_all_violations() -> set[str]:
    out: set[str] = set()
    for d in SERVICE_DIRS:
        for f in _iter_python_files(d):
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
            + (f"\n  ... (+{len(new) - 30} more)" if len(new) > 30 else "")
            + f"\n\n{remediation}"
        )
        raise AssertionError(msg)
    if fixed:
        print(
            f"[T-1157 ratchet] {label}: baseline shrank by {len(fixed)}. "
            "Remove fixed entries from `tests/.baseline_audit_missing_interview_offer.txt` "
            "to lock in the gain."
        )


def test_no_service_mutation_without_audit() -> None:
    """Todo método mutating em service de interview/offer chama
    ``AuditService.log_decision[_in_session]``.

    Sentinela do padrão T-1149. Débito legado vive em
    ``tests/.baseline_audit_missing_interview_offer.txt``; regressões
    novas quebram a build.
    """
    current = _scan_all_violations()
    baseline = _load_lines(BASELINE_FILE)
    _assert_no_new_violations(
        current=current,
        baseline=baseline,
        label="service mutation without audit",
        remediation=(
            "Adicione `await AuditService().log_decision_in_session(...)` "
            "no método (decision_type apropriado: schedule_interview / "
            "approve_hiring / generate_feedback). Ver "
            "`docs/runbooks/audit-interview-offer.md`."
        ),
    )


def test_audit_baseline_not_stale() -> None:
    """Baseline não pode listar entradas que já foram corrigidas."""
    current = _scan_all_violations()
    baseline = _load_lines(BASELINE_FILE)
    stale = sorted(baseline - current)
    assert not stale, (
        f"T-1157 — baseline tem {len(stale)} entrada(s) obsoleta(s); "
        "remova do arquivo:\n  " + "\n  ".join(stale[:30])
    )


def test_sentinel_covers_three_domains() -> None:
    """Meta-asserção: a sentinela está olhando os 3 domínios alvo."""
    found_files = []
    for d in SERVICE_DIRS:
        found_files.extend(_iter_python_files(d))
    found_names = {f.parent.parent.name for f in found_files}
    assert "interview_scheduling" in found_names, found_names
    assert "interview_intelligence" in found_names, found_names
    assert "offer" in found_names, found_names
