"""Contract sentinel — sourcing_agents endpoints por {agent_id} são tenant-scoped.

Regressão guard do P0-2 (cross-tenant takeover, audit 2026-05-21): os handlers
legados de /sourcing-agents resolviam CustomAgent por ID SEM filtrar company_id,
permitindo que qualquer usuário autenticado lesse/pausasse/retomasse o agente de
OUTRA empresa. Fix: todo handler por ID resolve via _require_owned_agent(), que
filtra company_id do JWT e devolve 404 em cross-tenant.

Source-level (sem DB) — barato e robusto contra reintrodução do padrão inseguro.
"""
import re
from pathlib import Path

SRC_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "sourcing_agents.py"
)

# Todo handler que recebe {agent_id} no path.
BY_ID_HANDLERS = [
    "get_sourcing_agent",
    "submit_feedback",
    "get_calibration_candidates",
    "get_agent_timeline",
    "pause_agent",
    "resume_agent",
]


def _block(src: str, name: str) -> str:
    """Trecho da `(async )?def {name}(` até o próximo def/handler no nível de módulo."""
    m = re.search(rf"(?:async )?def {re.escape(name)}\(", src)
    assert m, f"função {name} não encontrada em sourcing_agents.py"
    rest = src[m.end():]
    nxt = re.search(r"\n(?:async def |def |@router\.|router = )", rest)
    return src[m.start(): m.end() + (nxt.start() if nxt else len(rest))]


def test_by_id_handlers_resolve_via_tenant_guard():
    src = SRC_PATH.read_text(encoding="utf-8")
    offenders = [h for h in BY_ID_HANDLERS if "_require_owned_agent" not in _block(src, h)]
    assert not offenders, (
        "Handlers {agent_id} sem _require_owned_agent (cross-tenant takeover P0-2): "
        f"{offenders}. Todo handler por ID deve resolver o agente filtrando company_id do JWT."
    )


def test_tenant_guard_filters_company_id_and_404s():
    src = SRC_PATH.read_text(encoding="utf-8")
    guard = _block(src, "_require_owned_agent")
    assert "CustomAgent.company_id == company_id" in guard, (
        "_require_owned_agent não filtra company_id — multi-tenancy quebrada."
    )
    assert "scalar_one_or_none" in guard and "404" in guard, (
        "_require_owned_agent deve devolver 404 quando o agente não pertence ao tenant."
    )


def test_company_id_comes_from_jwt_not_payload():
    """company_id vem do current_user (JWT), nunca do payload (REGRA multi-tenancy)."""
    src = SRC_PATH.read_text(encoding="utf-8")
    guard = _block(src, "_require_company")
    assert 'getattr(current_user, "company_id"' in guard, (
        "_require_company deve derivar company_id do current_user (JWT)."
    )
