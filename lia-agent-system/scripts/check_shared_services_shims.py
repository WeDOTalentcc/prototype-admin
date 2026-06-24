"""
CI lint — shim/real service consolidation guard (Task #1283).

Contexto: vários serviços vivem em duas árvores — a implementação real em
`app/domains/<domain>/services/<name>.py` (a **fonte-da-verdade**) e um *shim*
em `app/shared/services/<name>.py` que apenas reexporta a implementação real.
O risco documentado (handoff de busca §19) é a **divergência**: alguém edita o
shim achando que é a lógica, ou copia a implementação real para o shim,
recriando uma cópia duplicada que sai de sincronia.

Política canônica:
    - A fonte-da-verdade é SEMPRE `app/domains/*/services`.
    - Qualquer arquivo em `app/shared/services/<name>.py` cujo basename colida
      com um `app/domains/*/services/<name>.py` DEVE ser um shim puro: só
      docstring + imports (incl. `from app.domains... import *` e reexport de
      símbolos privados para testes). NÃO pode conter `def` / `async def` /
      `class` (= lógica de negócio).
    - O shim DEVE de fato delegar: precisa ter pelo menos um
      `from app.domains.* import ...` apontando para o módulo twin.

Integração com CI:
    - Coberto pelo job de fitness `tests/fitness/test_audit_2026_04_finals.py`
      (`TestShimServiceConsolidationGuard`), que executa este script como
      subprocess e valida exit-code 0 contra a árvore real do repositório.
    - Coberto pelo unit guard `tests/test_shared_services_shims_guard.py`, que
      valida exit-code para árvores sintéticas limpa vs. violadora (tmp).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SHARED_SERVICES = _ROOT / "app" / "shared" / "services"
_DOMAINS = _ROOT / "app" / "domains"


def _domain_service_index(domains_root: Path) -> dict[str, list[Path]]:
    """Map basename -> [paths] for every app/domains/*/services/*.py module."""
    index: dict[str, list[Path]] = {}
    if not domains_root.exists():
        return index
    for path in domains_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if path.name == "__init__.py":
            continue
        # Only files whose parent (or an ancestor) directory is named "services".
        if "services" not in path.parts:
            continue
        index.setdefault(path.name, []).append(path)
    return index


def _is_pure_shim(tree: ast.Module) -> tuple[bool, list[str]]:
    """A pure shim contains only a docstring + imports (no def/async def/class).

    Try/except wrapping imports (used to optionally reexport private symbols) is
    allowed as long as it contains no business logic.
    """
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            offenders.append(f"function `{node.name}` (linha {node.lineno})")
        elif isinstance(node, ast.ClassDef):
            offenders.append(f"class `{node.name}` (linha {node.lineno})")
    return (not offenders, offenders)


def _delegates_to_domain(tree: ast.Module, basename: str) -> bool:
    """True if the file imports from app.domains.*.services.<module>."""
    module_stem = basename[:-3]  # strip ".py"
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            if mod.startswith("app.domains.") and mod.endswith(
                f".services.{module_stem}"
            ):
                return True
    return False


def _scan(
    shared_dir: Path = _SHARED_SERVICES, domains_root: Path = _DOMAINS
) -> list[tuple[str, str]]:
    """Return list of (relative_path, reason) violations."""
    violations: list[tuple[str, str]] = []
    if not shared_dir.exists():
        return violations
    domain_index = _domain_service_index(domains_root)

    for path in sorted(shared_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        if path.name not in domain_index:
            # No domain twin → this is a genuine shared-only service. Skip.
            continue
        rel = path.relative_to(_ROOT) if _ROOT in path.parents else path
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception as exc:  # pragma: no cover - parse failure is a violation
            violations.append((str(rel), f"falha ao parsear: {exc}"))
            continue

        is_pure, offenders = _is_pure_shim(tree)
        if not is_pure:
            twin = domain_index[path.name][0]
            twin_rel = twin.relative_to(_ROOT) if _ROOT in twin.parents else twin
            violations.append(
                (
                    str(rel),
                    "contém lógica de negócio "
                    + ", ".join(offenders)
                    + f" — a fonte-da-verdade é `{twin_rel}`. "
                    "Mova a lógica para o domínio e deixe este arquivo só "
                    "reexportando.",
                )
            )
            continue

        if not _delegates_to_domain(tree, path.name):
            twin = domain_index[path.name][0]
            twin_rel = twin.relative_to(_ROOT) if _ROOT in twin.parents else twin
            violations.append(
                (
                    str(rel),
                    "não delega para o domínio: falta "
                    f"`from app.domains.*.services.{path.name[:-3]} import *` "
                    f"apontando para `{twin_rel}`.",
                )
            )
    return violations


def main() -> int:
    violations = _scan()
    if not violations:
        print(
            "[shim-guard] OK — todos os arquivos de app/shared/services com "
            "twin em app/domains/*/services são shims puros que delegam."
        )
        return 0
    print(
        f"[shim-guard] FAIL — {len(violations)} violação(ões) de consolidação "
        "shim/real detectada(s):",
        file=sys.stderr,
    )
    for rel, reason in violations:
        print(f"  {rel}  ->  {reason}", file=sys.stderr)
    print(
        "\nFonte-da-verdade = app/domains/*/services. Shims em "
        "app/shared/services devem APENAS reexportar (sem def/class).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
