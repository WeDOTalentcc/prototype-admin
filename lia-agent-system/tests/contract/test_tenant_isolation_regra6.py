"""
Contract tests: REGRA 6 -- x_company_id Header nao deve sobrescrever JWT.

P0-W1-05: communication_settings.py
P1-W1-01: candidates_consent.py
Audit ref: P0-W1-05 + P1-W1-01 (2026-05-24)
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path("/home/runner/workspace/lia-agent-system")
COMM_SETTINGS = ROOT / "app/api/v1/communication_settings.py"
CANDIDATES_CONSENT = ROOT / "app/api/v1/candidates/candidates_consent.py"


def _parse_ast(filepath: Path) -> ast.Module:
    return ast.parse(filepath.read_text())


def _get_function_args(tree: ast.Module, func_name: str) -> list[str]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            return [arg.arg for arg in node.args.args]
    return []


def _has_header_orphan_import(filepath: Path) -> bool:
    source = filepath.read_text()
    tree = ast.parse(source)
    has_header_import = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "fastapi" in node.module:
                for alias in node.names:
                    if alias.name == "Header":
                        has_header_import = True
    if not has_header_import:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = (node.args.defaults or []) + [d for d in (node.args.kw_defaults or []) if d is not None]
            for default in defaults:
                for sub in ast.walk(default):
                    if isinstance(sub, ast.Name) and sub.id == "Header":
                        return False
                    if isinstance(sub, ast.Attribute) and sub.attr == "Header":
                        return False
    return True


class TestCommunicationSettingsRegra6:
    def test_file_exists(self):
        assert COMM_SETTINGS.exists()

    def test_no_x_company_id_in_get_handler(self):
        tree = _parse_ast(COMM_SETTINGS)
        args = _get_function_args(tree, "get_communication_settings")
        assert "x_company_id" not in args, "P0-W1-05: get_communication_settings ainda tem x_company_id"

    def test_no_x_company_id_in_put_handler(self):
        tree = _parse_ast(COMM_SETTINGS)
        args = _get_function_args(tree, "update_communication_settings")
        assert "x_company_id" not in args, "P0-W1-05: update_communication_settings ainda tem x_company_id"

    def test_no_x_company_id_assignment_in_body(self):
        source = COMM_SETTINGS.read_text()
        assert "x_company_id or" not in source, "P0-W1-05: anti-pattern R4b x_company_id or encontrado"

    def test_canonical_require_company_id_imported(self):
        source = COMM_SETTINGS.read_text()
        assert "from app.shared.security.require_company_id import require_company_id" in source

    def test_wedo_base_model_used_for_update_schema(self):
        source = COMM_SETTINGS.read_text()
        assert "class CommunicationSettingsUpdate(WeDoBaseModel)" in source

    def test_no_header_orphan_import(self):
        assert not _has_header_orphan_import(COMM_SETTINGS), (
            "P0-W1-05: Header importado de fastapi mas nao usado em nenhum arg de funcao (import orfao)"
        )

    def test_no_get_company_id_wrapper(self):
        source = COMM_SETTINGS.read_text()
        assert "def get_company_id(" not in source, (
            "P0-W1-05: wrapper get_company_id desnecessaria ainda presente -- "
            "remover e usar Depends(require_company_id) direto nos handlers"
        )


class TestCandidatesConsentRegra6:
    def test_file_exists(self):
        assert CANDIDATES_CONSENT.exists()

    def test_no_x_company_id_in_get_consents(self):
        tree = _parse_ast(CANDIDATES_CONSENT)
        args = _get_function_args(tree, "get_candidate_consents")
        assert "x_company_id" not in args, "P1-W1-01: get_candidate_consents ainda tem x_company_id"

    def test_no_x_company_id_in_create_consent(self):
        tree = _parse_ast(CANDIDATES_CONSENT)
        args = _get_function_args(tree, "create_or_update_candidate_consent")
        assert "x_company_id" not in args, "P1-W1-01: create_or_update_candidate_consent ainda tem x_company_id"

    def test_no_x_company_id_in_revoke_consent(self):
        tree = _parse_ast(CANDIDATES_CONSENT)
        args = _get_function_args(tree, "revoke_candidate_consent")
        assert "x_company_id" not in args, "P1-W1-01: revoke_candidate_consent ainda tem x_company_id"

    def test_no_admin_company_fallback(self):
        source = CANDIDATES_CONSENT.read_text()
        assert "admin_company" not in source, (
            "P1-W1-01: fallback admin_company encontrado -- permite cross-tenant LGPD"
        )

    def test_require_company_id_in_consent_endpoints(self):
        source = CANDIDATES_CONSENT.read_text()
        assert "from app.shared.security.require_company_id import require_company_id" in source
        count = source.count("Depends(require_company_id)")
        assert count >= 3, f"P1-W1-01: esperado >= 3 Depends(require_company_id), encontrado {count}"

    def test_wedo_base_model_for_consent_schemas(self):
        source = CANDIDATES_CONSENT.read_text()
        assert "class ConsentCreateRequest(WeDoBaseModel)" in source

    def test_no_header_orphan_import(self):
        assert not _has_header_orphan_import(CANDIDATES_CONSENT), (
            "P1-W1-01: Header importado de fastapi mas nao usado em nenhum arg (import orfao)"
        )
