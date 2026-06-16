"""Contract — Task #1302: detector tenant-filter type matches column type.

Cada detector em ``ProactiveDetectorService.detectors`` escopa sua query por um
identificador de tenant (``company_id`` / ``client_account_id``). Se o valor
Python usado no filtro NÃO bater com o tipo SQL da coluna, o Postgres levanta um
erro de tipo (``varchar = uuid``) que o ``except`` largo do detector engole — a
query devolve ``[]`` e o alerta NUNCA dispara, sem nenhum log de erro visível.

Esse foi o incidente do ``AICreditsLowDetector`` (convertia ``company_id`` para
``UUID`` contra uma coluna ``String(64)``); a mesma armadilha reapareceu no
``PipelineStuckDetector`` contra ``JobVacancy.company_id`` (``String(255)``).
Contexto: ``.agents/memory/detector-tenant-filter-types.md``.

Este sentinela varre, via AST, o ``detect()`` (e helpers) de CADA detector
registrado, encontra cada comparação ``<Model>.<tenant_col> == <rhs>``, resolve
a classe do modelo pelo ``import`` local do método, lê o tipo REAL da coluna em
``__table__`` e exige que o lado direito (string crua vs ``UUID(...)``) seja
compatível com o tipo da coluna. Um detector novo (ou alterado) que reintroduza
o mismatch quebra a build aqui — antes de virar um alerta "fantasma" silencioso.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest
from sqlalchemy import String

try:  # tipo UUID dialeto Postgres (usado pelos modelos)
    from sqlalchemy.dialects.postgresql import UUID as _PGUUID
except Exception:  # pragma: no cover - dialeto sempre disponível
    _PGUUID = None

try:  # tipo UUID genérico SQLAlchemy 2.x (defensivo)
    from sqlalchemy import Uuid as _SAUuid
except Exception:  # pragma: no cover
    _SAUuid = None

_UUID_TYPES = tuple(t for t in (_PGUUID, _SAUuid) if t is not None)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SERVICE_PATH = (
    REPO_ROOT / "app" / "shared" / "services" / "proactive_detector_service.py"
)

# Colunas de escopo de tenant que precisam casar com o tipo do filtro.
TENANT_COLUMNS = {"company_id", "client_account_id"}

# Detectores que NÃO usam comparação ORM `Model.company_id == ...` (raw SQL com
# bind param sempre stringificado, portanto seguro por construção). Precisam
# estar listados aqui senão o guard de cobertura abaixo falha (evita que o
# sentinela passe vazio se a varredura AST quebrar silenciosamente).
RAW_SQL_DETECTORS = {"WorkforcePlanStaleDetector"}


def _column_kind(col_type) -> str:
    """Classifica o tipo SQLAlchemy da coluna em 'uuid' | 'string' | 'other'."""
    if _UUID_TYPES and isinstance(col_type, _UUID_TYPES):
        return "uuid"
    # UUID do Postgres NÃO é subclasse de String, então a ordem acima é segura.
    if isinstance(col_type, String):
        return "string"
    return "other"


def _collect_imports(func_node: ast.AST) -> dict[str, str]:
    """Mapeia nome importado -> módulo dentro de um corpo de função."""
    imports: dict[str, str] = {}
    for node in ast.walk(func_node):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imports[alias.asname or alias.name] = node.module
    return imports


def _collect_uuid_vars(func_node: ast.AST) -> set[str]:
    """Variáveis locais atribuídas a partir de UUID(...) -> tipadas como UUID."""
    uuid_vars: set[str] = set()
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            fn = node.value.func
            if isinstance(fn, ast.Name) and fn.id == "UUID":
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        uuid_vars.add(tgt.id)
    return uuid_vars


def _rhs_kind(rhs: ast.AST, uuid_vars: set[str]) -> str | None:
    """Classifica o lado direito do filtro: 'uuid' | 'string' | None (ignorar)."""
    if isinstance(rhs, ast.Call) and isinstance(rhs.func, ast.Name):
        if rhs.func.id == "UUID":
            return "uuid"
        if rhs.func.id == "str":
            return "string"
    if isinstance(rhs, ast.Name):
        if rhs.id in uuid_vars:
            return "uuid"
        if rhs.id == "company_id":
            return "string"
    return None


def _detector_class_nodes() -> dict[str, ast.ClassDef]:
    tree = ast.parse(SERVICE_PATH.read_text(encoding="utf-8"))
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def _registered_detector_class_names() -> list[str]:
    from app.shared.services.proactive_detector_service import (
        ProactiveDetectorService,
    )

    return [type(d).__name__ for d in ProactiveDetectorService().detectors]


def _resolve_column_type(model_name: str, column: str, imports: dict[str, str]):
    module_path = imports.get(model_name)
    if module_path is None:
        return None, f"sem import para modelo '{model_name}'"
    try:
        module = importlib.import_module(module_path)
        model = getattr(module, model_name)
        col = model.__table__.columns[column]
    except Exception as exc:  # pragma: no cover - falha de import é informativa
        return None, f"falha ao resolver {module_path}.{model_name}.{column}: {exc}"
    return col.type, None


def _scan_detector(class_node: ast.ClassDef) -> list[dict]:
    """Retorna a lista de filtros tenant comparados encontrados no detector."""
    findings: list[dict] = []
    for method in class_node.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        imports = _collect_imports(method)
        uuid_vars = _collect_uuid_vars(method)
        for node in ast.walk(method):
            if not isinstance(node, ast.Compare):
                continue
            if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
                continue
            left = node.left
            if not (
                isinstance(left, ast.Attribute)
                and left.attr in TENANT_COLUMNS
                and isinstance(left.value, ast.Name)
            ):
                continue
            rhs_kind = _rhs_kind(node.comparators[0], uuid_vars)
            if rhs_kind is None:
                continue
            findings.append(
                {
                    "model": left.value.id,
                    "column": left.attr,
                    "rhs_kind": rhs_kind,
                    "imports": imports,
                }
            )
    return findings


def test_detector_company_id_filter_matches_column_type():
    """Para cada detector, o tipo do filtro tenant casa com o tipo da coluna."""
    class_nodes = _detector_class_nodes()
    registered = _registered_detector_class_names()

    covered: set[str] = set()
    problems: list[str] = []

    for cls_name in registered:
        node = class_nodes.get(cls_name)
        assert node is not None, (
            f"detector registrado '{cls_name}' não encontrado no AST de "
            f"{SERVICE_PATH.name}"
        )
        findings = _scan_detector(node)
        if findings:
            covered.add(cls_name)
        for f in findings:
            col_type, err = _resolve_column_type(
                f["model"], f["column"], f["imports"]
            )
            if err:
                problems.append(f"{cls_name}: {err}")
                continue
            col_kind = _column_kind(col_type)
            if col_kind == "other":
                problems.append(
                    f"{cls_name}: coluna {f['model']}.{f['column']} tem tipo "
                    f"inesperado {type(col_type).__name__} (nem String nem UUID)"
                )
                continue
            if col_kind != f["rhs_kind"]:
                problems.append(
                    f"{cls_name}: filtro {f['model']}.{f['column']} usa "
                    f"{f['rhs_kind'].upper()} mas a coluna é "
                    f"{col_kind.upper()} ({type(col_type).__name__}). "
                    "Mismatch silencioso: Postgres levanta erro de tipo, o "
                    "except do detector engole e o alerta nunca dispara."
                )

    assert not problems, (
        "Incompatibilidade(s) tipo-do-filtro × tipo-da-coluna detectada(s):\n"
        + "\n".join(f"  - {p}" for p in problems)
    )

    # Guard anti-vacuidade: todo detector registrado precisa OU ter sido coberto
    # (achou um filtro ORM) OU estar no allowlist de raw-SQL. Sem isto, uma
    # quebra futura na varredura AST faria o teste passar sem checar nada.
    uncovered = set(registered) - covered - RAW_SQL_DETECTORS
    assert not uncovered, (
        "Detectores sem filtro tenant detectado pela varredura AST "
        f"(nem no allowlist raw-SQL): {sorted(uncovered)}. Se for um detector "
        "raw-SQL legítimo, adicione-o a RAW_SQL_DETECTORS; senão a varredura "
        "está cega para o filtro company_id deste detector."
    )


def test_raw_sql_detectors_allowlist_is_minimal():
    """O allowlist de raw-SQL não pode citar detector inexistente (evita que um
    rename mascare um detector que voltou a usar ORM sem cobertura)."""
    registered = set(_registered_detector_class_names())
    stale = RAW_SQL_DETECTORS - registered
    assert not stale, (
        f"RAW_SQL_DETECTORS cita detector(es) não registrado(s): {sorted(stale)}"
    )
