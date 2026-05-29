"""
Contract sensor — wsi/reports.py must keep get_wsi_audit_trail endpoint registered.

WHY THIS SENSOR EXISTS
======================
Audit Recovery #3 (2026-05-23) restaurou ``get_wsi_audit_trail`` (endpoint
``GET /api/v1/wsi/reports/audit/{session_id}``) que foi silenciosamente
removido pelo merge commit 02361f41c em 2026-05-01.

O endpoint é COMPLIANCE-CRÍTICO:
- EU AI Act Art. 12 — record-keeping obrigatório pra IA de alto risco
  (recruitment é high-risk Annex III)
- LGPD Art. 20 — direito de explicação de decisão automatizada
- Único path canonical pra extrair trilha imutável WSI (responses + hashes
  SHA-256 + análise correlata) para auditoria regulatória ANPD ou EU.

Pattern: BLOCKING — endpoint compliance NUNCA pode regredir silenciosamente.
Se um refactor futuro precisar remover (raríssimo), atualizar este sensor
em PR explícito + ADR + flag de feature deprecation.
"""
from __future__ import annotations

from app.api.v1.wsi import reports as wsi_reports_module


def test_get_wsi_audit_trail_function_exists():
    """
    Função handler `get_wsi_audit_trail` deve estar definida no módulo
    `app.api.v1.wsi.reports`.

    Specific regression guard contra Recovery #3 incident — back then o
    handler foi totalmente removido pelo merge 02361f41c. Test falha
    imediato se estado recorrer.
    """
    assert hasattr(wsi_reports_module, "get_wsi_audit_trail"), (
        "wsi.reports.get_wsi_audit_trail handler missing. "
        "Recovery #3 (2026-05-23) restaurou esse endpoint compliance "
        "(EU AI Act Art. 12 / LGPD Art. 20). Se foi removido em refactor "
        "posterior, atualizar sensor + ADR + documentar substituto."
    )


def test_get_wsi_audit_trail_route_registered():
    """
    Endpoint GET /reports/audit/{session_id} deve estar no `router.routes`.
    """
    routes = {
        route.path for route in wsi_reports_module.router.routes  # type: ignore[attr-defined]
    }
    assert "/reports/audit/{session_id}" in routes, (
        f"Route '/reports/audit/{{session_id}}' missing from wsi.reports router. "
        f"Routes registered: {sorted(routes)}\n"
        "Path final esperado em runtime: /api/v1/wsi/reports/audit/{session_id}."
    )


def test_get_wsi_audit_trail_has_role_gate():
    """
    Endpoint compliance NÃO pode estar acessível publicamente. Deve ter
    gate de role (admin OR dpo) via FastAPI Depends.

    Garante que recovery não esqueceu de propagar o `require_role` original.
    """
    for route in wsi_reports_module.router.routes:  # type: ignore[attr-defined]
        if getattr(route, "path", None) == "/reports/audit/{session_id}":
            # Route.dependant.dependencies inclui top-level Depends(require_role(...))
            # + Depends(get_current_user_strict) + Depends(get_db). FastAPI cria
            # objetos Dependant transitivos por dependência.
            dependant = getattr(route, "dependant", None)
            assert dependant is not None, "Route lost dependant info"
            deps_count = len(dependant.dependencies)
            assert deps_count >= 2, (
                f"Route /reports/audit has only {deps_count} top-level dependencies. "
                "Expected role gate (require_role([admin, wedotalent_admin])) "
                "+ auth (get_current_user_strict) + db. Compliance endpoint NUNCA "
                "pode estar público."
            )
            return
    raise AssertionError("Route /reports/audit/{session_id} not found in router.routes")


def test_get_wsi_audit_trail_is_tenant_scoped():
    """Multi-tenancy fail-closed (Task #511 r3 + Fase 2.5 triagem 2026-05-29).

    O handler DEVE chamar ``validate_company_access`` (escopa tenant admin a
    propria company) e manter o deny-by-default quando a sessao nao resolve
    company (job_vacancy orfao). Cross-tenant SO e permitido a
    ``wedotalent_admin`` — staff WeDOTalent que responde regulador EU/ANPD
    (EU AI Act Art. 12). Sem isso, IDOR cross-tenant vaza audit trail de
    outro tenant.

    O sensor company_id flagga este handler como false positive porque o gate
    e ``validate_company_access`` (nao ``require_company_id``); este teste
    pina o gate real pra impedir regressao silenciosa do isolamento.
    """
    import inspect

    src = inspect.getsource(wsi_reports_module.get_wsi_audit_trail)
    assert "validate_company_access" in src, (
        "get_wsi_audit_trail perdeu validate_company_access — isolamento "
        "tenant quebrado (IDOR cross-tenant). Restaurar Task #511 r3."
    )
    assert "cross_tenant_roles" in src and "status_code=403" in src, (
        "get_wsi_audit_trail perdeu o deny-by-default (403 quando company "
        "nao resolve). Sem company resolvivel, so roles cross-tenant acessam."
    )
    assert "wedotalent_admin" in src, (
        "get_wsi_audit_trail deve reconhecer wedotalent_admin como o unico "
        "role com acesso cross-tenant (compliance EU AI Act Art. 12)."
    )


def test_get_wsi_audit_trail_has_multi_tenancy_marker():
    """O marker ``# multi-tenancy:`` documenta o false-positive do sensor
    company_id e mantem o baseline limpo. Regressao = re-aparece como
    offender e empurra o ratchet acima do baseline."""
    import inspect

    src = inspect.getsource(wsi_reports_module.get_wsi_audit_trail)
    assert "# multi-tenancy:" in src, (
        "Marker # multi-tenancy: removido de get_wsi_audit_trail — sensor "
        "check_company_id_in_routes volta a flaggar como offender."
    )
