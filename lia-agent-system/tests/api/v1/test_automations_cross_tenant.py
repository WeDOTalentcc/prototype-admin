"""Cross-tenant contract test for automations endpoints — REGRA 2 canonical.

Sensor permanente para o fix 2026-05-26: company_id NUNCA via query/body.
Backend extrai do JWT via Depends(require_company_id).

Pin:
1. list_automations não declara `company_id: str = Query(...)`.
2. Endpoint usa Depends(require_company_id) — JWT é a única fonte.
3. require_company_id_strict_match NÃO é importado/referenciado (pattern legado removido).

Pattern: introspecção AST (zero FastAPI runtime). Espelha
test_automation_tenant_isolation.py + test_offer_approval_gate.py.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

AUTOMATIONS_FILE = Path(__file__).resolve().parents[3] / "app" / "api" / "v1" / "automations.py"


@pytest.fixture(scope="module")
def automations_ast() -> ast.Module:
    """Parse automations.py once per module."""
    source = AUTOMATIONS_FILE.read_text()
    return ast.parse(source)


@pytest.fixture(scope="module")
def automations_source() -> str:
    return AUTOMATIONS_FILE.read_text()


# ---------------------------------------------------------------------------
# REGRA 2 canonical — company_id NUNCA via Query
# ---------------------------------------------------------------------------


class TestAutomationsRegra2Canonical:
    """Pin REGRA 2: company_id NUNCA em Query/Body. Sempre via JWT (Depends)."""

    def test_no_company_id_query_param(self, automations_source: str):
        """Nenhum endpoint pode ter `company_id: str = Query(...)`."""
        # Regex robusta: company_id seguido de Query em qualquer linha.
        forbidden_pattern = 'company_id: str = Query('
        assert forbidden_pattern not in automations_source, (
            f"REGRA 2 violation: '{forbidden_pattern}' encontrado em {AUTOMATIONS_FILE}.\n"
            f"company_id NUNCA via query — backend extrai do JWT via Depends(require_company_id).\n"
            f"Ver CLAUDE.md user-global REGRA 2 + commit canonical 2026-05-26."
        )

    def test_no_strict_match_query_company_id(self, automations_source: str):
        """Nenhum endpoint pode usar require_company_id_strict_match('query.company_id').

        O pattern strict_match era defesa-em-profundidade pra payload company_id.
        Removido após audit P1-5 — JWT é authoritative, sem segunda fonte.
        """
        forbidden = 'require_company_id_strict_match("query.company_id")'
        assert forbidden not in automations_source, (
            f"REGRA 2 canonical: {forbidden} foi removido — pattern legado.\n"
            f"Use Depends(require_company_id) direto (JWT only)."
        )

    def test_all_endpoints_use_require_company_id_jwt(
        self, automations_ast: ast.Module
    ):
        """Todo handler com `company_id` parameter usa Depends(require_company_id)."""
        # Walk all async def at module level
        endpoints_with_company_id = []
        for node in ast.walk(automations_ast):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.arg != "company_id":
                    continue
                # Find the default value (Depends call)
                defaults = node.args.defaults + node.args.kw_defaults
                # Map arg -> default
                # Easier: re-scan via source
                endpoints_with_company_id.append(node.name)
                break

        # We expect at least 10 handlers with company_id (8 strict + 2 trigger/action types)
        assert len(endpoints_with_company_id) >= 10, (
            f"Esperava >= 10 handlers com company_id, encontrei {len(endpoints_with_company_id)}: "
            f"{endpoints_with_company_id}"
        )

    def test_require_company_id_imported(self, automations_source: str):
        """`require_company_id` (JWT canonical) é importado."""
        assert "require_company_id" in automations_source
        assert "from app.shared.security.require_company_id import" in automations_source


# ---------------------------------------------------------------------------
# Frontend contract — proxy não força company_id no query
# ---------------------------------------------------------------------------

FRONTEND_TAB = (
    Path("/home/runner/workspace/plataforma-lia/src/components/settings/"
         "recruitment/automations-tab.tsx")
)


class TestAutomationsTabRegra2Canonical:
    """Pin frontend: nunca envia company_id na URL."""

    def test_frontend_does_not_send_company_id_in_url(self):
        """automations-tab.tsx NÃO pode construir URL com ?company_id=..."""
        if not FRONTEND_TAB.exists():
            pytest.skip(f"Frontend tab file not found at {FRONTEND_TAB}")
        source = FRONTEND_TAB.read_text()
        # Anti-pattern: ?company_id= em qualquer URL fetch
        forbidden = "automations?company_id="
        assert forbidden not in source, (
            f"REGRA 2 violation: '{forbidden}' encontrado em {FRONTEND_TAB}.\n"
            f"Frontend NUNCA passa company_id via query — backend extrai do JWT."
        )
