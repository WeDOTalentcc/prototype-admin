#!/usr/bin/env python3
"""SENSOR (harness-engineering: B.1 cross-tenant query filter coverage).

Registrado 2026-05-21 — HARDENING_PLAN.md Bloco B.1.

AST checker que detecta queries ORM `select/update/delete(<Model>)` em
arquivos `*service*.py` (qualquer pasta) e `app/api/**/*.py` quando o
Model tem coluna `company_id` definida em `libs/models/lia_models/`,
mas a expressão NÃO contém `.where(<Model>.company_id == ...)` na mesma
expressão encadeada, e tampouco há comentário marker
`# TENANT-EXEMPT: <reason>` em janela próxima.

Por quê:
  Audit 2026-05-21 (P1.x cross-tenant) descobriu que mesmo após
  ADR-001 + check_no_select_in_services, ainda há sites onde queries
  são montadas SEM filter de company_id explícito (assume-se que vem
  via repository, mas em api/* às vezes não vem). Sensor B.1 fecha
  esse gap com cobertura cross-cutting (services + api).

Distinção dos outros sensores:
  - check_no_cross_tenant_query.py — raw `text(...)` SQL em tool_registry
  - check_no_select_in_services.py — banimento total de select em services
  - **check_query_has_tenant_filter.py (este)** — quando select EXISTE,
    obriga company_id filter explícito.

Pattern referência: scripts/check_pydantic_conventions.py (CLAUDE.md REGRA 1-6).

Modo:
  warn-only (default) — baseline alta esperada (~50+), promoção a blocking
  quando baseline atinge 0 ou via ratchet via --baseline-file.

Output:
  PATH:LINE  [Model.operation]  message
  FIX: instrução em PT-BR otimizada pra consumo LLM.

Uso:
    python3 scripts/check_query_has_tenant_filter.py [--warn-only]
                                                     [--baseline-file scripts/baselines/tenant_filter.txt]
                                                     [--update-baseline]
    Exit 0 = clean, ou warn-only mode
    Exit 1 = blocking mode + count > baseline
"""
from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "libs" / "models" / "lia_models"

# Operações ORM cobertas pelo sensor
ORM_OPERATIONS = frozenset({"select", "update", "delete"})

# Diretórios a escanear
SCAN_DIRS = [
    ROOT / "app" / "api",
    ROOT / "app" / "domains",
    ROOT / "app" / "services",
    ROOT / "app" / "shared",
]

# Skip patterns
SKIP_DIR_PARTS = frozenset({
    "tests", "test", "__pycache__", "migrations", "alembic",
    "scripts", ".venv", "venv", "node_modules", ".git",
})

# Skip file patterns
SKIP_FILE_PATTERNS = frozenset({
    "__init__.py",  # geralmente só re-export
    "conftest.py",
})

# Skip arquivos que não são services nem api (utilities, types, etc)
# Inclui arquivos com sufixo service/api/repository/handler/router/endpoint
def is_scan_target(path: Path) -> bool:
    """True se o arquivo deve ser escaneado."""
    name = path.name
    if name in SKIP_FILE_PATTERNS:
        return False
    if not name.endswith(".py"):
        return False
    parts = path.parts
    for skip in SKIP_DIR_PARTS:
        if skip in parts:
            return False
    # Aceita: service files (qualquer pasta), api files, repository files
    return (
        "service" in name
        or "/api/" in str(path)
        or "/services/" in str(path)
        or "repository" in name
        or "handler" in name
        or "router" in name
        or "endpoint" in name
        or "/domains/" in str(path)
    )


EXEMPT_MARKERS = ("TENANT-EXEMPT", "CROSS-TENANT-EXEMPT", "ADR-001-EXEMPT")


@dataclass
class Hit:
    path: Path
    line: int
    model: str
    operation: str
    snippet: str


def discover_tenant_scoped_models() -> set[str]:
    """Retorna nomes de classes ORM (CamelCase) que têm coluna company_id.

    Heurística AST simples: classe que define `company_id = Column(...)`
    em corpo (top-level attrs).
    """
    tenant_models: set[str] = set()
    if not MODELS_DIR.exists():
        return tenant_models

    for model_file in MODELS_DIR.glob("*.py"):
        if model_file.name in SKIP_FILE_PATTERNS:
            continue
        try:
            src = model_file.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(model_file))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            # Procurar atributo company_id em corpo da classe
            for stmt in node.body:
                target_names: list[str] = []
                if isinstance(stmt, ast.Assign):
                    for tgt in stmt.targets:
                        if isinstance(tgt, ast.Name):
                            target_names.append(tgt.id)
                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    target_names.append(stmt.target.id)
                if "company_id" in target_names:
                    tenant_models.add(node.name)
                    break
    return tenant_models


def has_exempt_in_window(src_lines: list[str], lineno: int, window: int = 5) -> bool:
    """Verifica se há marker TENANT-EXEMPT nas N linhas acima do hit."""
    start = max(0, lineno - 1 - window)
    end = min(len(src_lines), lineno + 1)
    chunk = "\n".join(src_lines[start:end])
    return any(marker in chunk for marker in EXEMPT_MARKERS)


def extract_chained_call(node: ast.AST) -> list[ast.Call]:
    """Dado um ast.Call (resultado de select(Model)), retorna a lista de
    todos os ast.Call ancestor-encadeados via .where().method() etc.

    Implementação: percorre AST tree do enclosing module e procura a
    expression statement / assignment que contém o select call, então
    coleta toda a chain.
    """
    return []  # not used directly — handled by extract_call_chain


def collect_chain_method_names(call_node: ast.Call, root_tree: ast.AST) -> set[str]:
    """Encontra a expression que ENVOLVE call_node e retorna os nomes
    de método chained (.where, .filter, etc.).
    """
    method_names: set[str] = set()

    # Estratégia: subir até achar um Expr ou Assign ancestor que contenha
    # call_node, então descer coletando .attr names.
    # Como ast não tem parent links, fazemos walk e procuramos por
    # any Call/Attribute que tenha esse call_node como descendant.
    target_id = id(call_node)

    def collect_methods_under(node):
        """Coleta nomes de método attribute em todo subtree."""
        names = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Attribute):
                names.add(n.attr)
        return names

    # Encontra o ancestor mais alto que ainda CONTÉM o call_node (statement-level)
    enclosing_stmt = None
    for n in ast.walk(root_tree):
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Return, ast.Await)):
            for descendant in ast.walk(n):
                if id(descendant) == target_id:
                    enclosing_stmt = n
                    break
            if enclosing_stmt is not None:
                break

    if enclosing_stmt is not None:
        method_names.update(collect_methods_under(enclosing_stmt))

    return method_names


def collect_chain_source(call_node: ast.Call, src: str) -> str:
    """Extrai o texto-fonte da chain envolvendo call_node, do início da
    statement enclosing até o fim da chain. Heurística: usa
    end_lineno/end_col_offset (Python 3.8+).
    """
    return ""  # legacy stub, replaced by simpler approach


def get_line_text_with_continuations(src_lines: list[str], start_line: int) -> str:
    """Junta linhas a partir de start_line até balancear parênteses/colchetes.

    Útil pra reconstruir chamadas multi-linha tipo:
        result = await db.execute(
            select(Model)
            .where(Model.id == foo)
            .where(Model.company_id == bar)
        )
    """
    if start_line < 1 or start_line > len(src_lines):
        return ""

    idx = start_line - 1  # 0-based
    # Walk backwards to find statement start (no leading whitespace +
    # not a continuation of previous line via open paren).
    # Simple heuristic: walk back until line ends with non-comma/non-open.
    while idx > 0:
        prev = src_lines[idx - 1].rstrip()
        if prev.endswith("(") or prev.endswith(",") or prev.endswith("\\"):
            idx -= 1
        else:
            break

    buf: list[str] = []
    depth = 0
    started = False
    for i in range(idx, len(src_lines)):
        line = src_lines[i]
        buf.append(line)
        for ch in line:
            if ch in "([{":
                depth += 1
                started = True
            elif ch in ")]}":
                depth -= 1
        if started and depth <= 0:
            break
    return "\n".join(buf)


def chain_has_company_id_filter(chain_text: str, model_name: str) -> bool:
    """Heurística: chain text contém `.where(` (ou .filter) E
    referência a `company_id`. Aceita variações:
      .where(Model.company_id == ...)
      .where(and_(..., Model.company_id == ...))
      .filter(Model.company_id == ...)
      .filter_by(company_id=...)
    """
    has_where_or_filter = (
        ".where(" in chain_text
        or ".filter(" in chain_text
        or ".filter_by(" in chain_text
    )
    if not has_where_or_filter:
        return False
    # company_id deve aparecer DENTRO de uma das chamadas where/filter
    return "company_id" in chain_text


@dataclass
class FoundCall:
    node: ast.Call
    model: str
    operation: str


def find_orm_calls(tree: ast.AST) -> list[FoundCall]:
    """Encontra todas as chamadas a select/update/delete(Model) onde
    Model começa com letra maiúscula (heurística para classe)."""
    found: list[FoundCall] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in ORM_OPERATIONS:
            op = func.id
        elif isinstance(func, ast.Attribute) and func.attr in ORM_OPERATIONS:
            op = func.attr
        else:
            continue
        if not node.args:
            continue
        first_arg = node.args[0]
        # Aceitar Name(SomeModel)
        if isinstance(first_arg, ast.Name) and first_arg.id[:1].isupper():
            found.append(FoundCall(node=node, model=first_arg.id, operation=op))
        # ignorar select(func.count()), select(some_subq), select(*) — não-class
    return found


def scan_file(path: Path, tenant_models: set[str]) -> list[Hit]:
    """Scaneia um arquivo Python e retorna hits."""
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    src_lines = src.splitlines()
    hits: list[Hit] = []

    for found in find_orm_calls(tree):
        if found.model not in tenant_models:
            continue

        lineno = found.node.lineno

        # Skip se há marker EXEMPT acima
        if has_exempt_in_window(src_lines, lineno):
            continue

        # Reconstroi a chain (multi-line aware)
        chain_text = get_line_text_with_continuations(src_lines, lineno)

        # Se a chain inclui company_id num .where/.filter, está OK
        if chain_has_company_id_filter(chain_text, found.model):
            continue

        snippet = src_lines[lineno - 1].strip()[:120] if lineno <= len(src_lines) else ""
        hits.append(
            Hit(
                path=path,
                line=lineno,
                model=found.model,
                operation=found.operation,
                snippet=snippet,
            )
        )

    return hits


def find_scan_files() -> list[Path]:
    files: list[Path] = []
    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for p in scan_dir.rglob("*.py"):
            if is_scan_target(p):
                files.append(p)
    return sorted(set(files))


def format_hit(hit: Hit) -> str:
    try:
        rel = hit.path.relative_to(ROOT)
    except ValueError:
        rel = hit.path
    return f"{rel}:{hit.line}  [{hit.model}.{hit.operation}]  {hit.snippet}"


FIX_INSTRUCTION = """
FIX (PT-BR, otimizado pra consumo LLM):

Adicionar filtro company_id explicito na expressao encadeada:

  # ANTES (anti-pattern):
  stmt = select(Candidate).where(Candidate.id == cid)

  # DEPOIS (canonical):
  stmt = (
      select(Candidate)
      .where(Candidate.id == cid)
      .where(Candidate.company_id == company_id)  # tenant gate canonical
  )

Alternativa (legitimo cross-tenant analytics / migration / model staging):
adicionar comentario marker na linha imediatamente acima da expressao:

  # TENANT-EXEMPT: cross-tenant analytics aggregate (audit Anderson 2026-05-21)
  stmt = select(Candidate).where(Candidate.created_at >= cutoff)

CLAUDE.md REGRA ZERO + Pydantic R2: company_id NUNCA vem do payload.
Sempre via Depends(require_company_id) -> JWT canonical -> arg do metodo.
""".strip()


def load_baseline(baseline_file: Path) -> int:
    if not baseline_file.exists():
        return 0
    try:
        return int(baseline_file.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return 0


def save_baseline(baseline_file: Path, count: int) -> None:
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_file.write_text(f"{count}\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AST checker: tenant filter coverage em ORM queries"
    )
    parser.add_argument(
        "--warn-only", action="store_true",
        help="Modo warn-only (default ja eh warn-only ate baseline 0)"
    )
    parser.add_argument(
        "--blocking", action="store_true",
        help="Forca modo blocking (fail se count > baseline)"
    )
    parser.add_argument(
        "--baseline-file", type=Path,
        default=ROOT / "scripts" / "baselines" / "tenant_filter.txt",
        help="Arquivo de baseline para ratchet"
    )
    parser.add_argument(
        "--update-baseline", action="store_true",
        help="Atualiza arquivo de baseline com count atual e sai 0"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON machine-readable"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suprime output detalhado (apenas summary)"
    )
    args = parser.parse_args(argv)

    tenant_models = discover_tenant_scoped_models()
    if not tenant_models:
        print("[B.1 tenant-filter sensor] WARN: nenhum model com company_id encontrado em libs/models/lia_models/", file=sys.stderr)
        return 0

    files = find_scan_files()
    all_hits: list[Hit] = []
    for f in files:
        all_hits.extend(scan_file(f, tenant_models))

    count = len(all_hits)
    baseline = load_baseline(args.baseline_file)

    if args.update_baseline:
        save_baseline(args.baseline_file, count)
        print(f"[B.1 tenant-filter sensor] Baseline atualizado em {args.baseline_file}: {count} violations")
        return 0

    if args.json:
        import json
        payload = {
            "count": count,
            "baseline": baseline,
            "scanned_files": len(files),
            "tenant_models_count": len(tenant_models),
            "hits": [
                {
                    "path": str(h.path.relative_to(ROOT)) if h.path.is_absolute() else str(h.path),
                    "line": h.line,
                    "model": h.model,
                    "operation": h.operation,
                    "snippet": h.snippet,
                }
                for h in all_hits
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        if not args.quiet:
            for h in all_hits[:100]:
                print(format_hit(h))
            if count > 100:
                print(f"... (+{count - 100} mais hits omitidos do output verboso)")

        print(file=sys.stderr)
        print(
            f"[B.1 tenant-filter sensor] {count} ORM queries sobre models tenant-scoped "
            f"SEM filter company_id (baseline ratchet: {baseline}).",
            file=sys.stderr,
        )
        print(f"  Scanned: {len(files)} arquivos", file=sys.stderr)
        print(f"  Tenant-scoped models detected: {len(tenant_models)}", file=sys.stderr)
        if count > 0:
            print(file=sys.stderr)
            print(FIX_INSTRUCTION, file=sys.stderr)

    # Mode resolution
    blocking_mode = args.blocking and not args.warn_only

    if blocking_mode and count > baseline:
        print(
            f"\n[B.1 tenant-filter sensor] BLOCKING: {count} > baseline {baseline}. "
            "Corrigir ou adicionar TENANT-EXEMPT marker.",
            file=sys.stderr,
        )
        return 1

    if not blocking_mode:
        print(
            "\n[B.1 tenant-filter sensor] WARN-ONLY (default). "
            "Promover a --blocking quando count atingir 0 (ou via baseline ratchet).",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
