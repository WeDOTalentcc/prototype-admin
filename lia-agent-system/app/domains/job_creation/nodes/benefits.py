"""benefits_node canonical -- inferencia + confirmacao de beneficios (2026-06-18).

Posicao no grafo: apos salary, antes de variable_comp_node.

Fluxo:
1. Le seniority + department + contract_type do estado.
2. Chama CompanyBenefitRepository.list_matching() -- matching AND por 3 dimensoes.
3. Separa em "suggested" (matches=True, pre-marcados) e "catalog" (restante).
4. Emite ws_stage_payload{stage="benefits"} para o painel do frontend.
5. Na proxima invocacao (recruiter confirmou via right_panel_form),
   confirmed_benefits ja esta no estado -- o no passa direto para o proximo.

Scoring semantico:
  matched all 3 dims  → confidence 0.95 (auto-suggested)
  matched 2 dims      → confidence 0.80 (suggested)
  matched 1 dim       → confidence 0.60 (listed, recruiter decides)
  universal (sem restr) → confidence 0.50 (always listed)
  nao compativel      → nao mostrado
"""

import logging
import time
from typing import Any, Dict, List

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.helpers.ws_payload_builder import build_ws_stage_payload
from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

logger = logging.getLogger(__name__)

_TIMEOUT_S = 12.0



def _benefits_toggle_active(state) -> bool:
    """Respeita o toggle 'benefits' das Instruções da LIA (Configurações).

    Mesmo padrão de salary.py: is_active=False => skip painel de benefícios,
    wizard passa direto com confirmed_benefits=[]. Ausente (sem row) ou True
    => ativo. Fail-open para não bloquear em caso de erro de DB.
    """
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id or company_id in ("default", "unknown"):
        return True

    async def _read():
        import uuid as _uuid
        from sqlalchemy import select as _select
        from app.core.database import AsyncSessionLocal
        from app.models.lia_field_toggles import LiaFieldToggle
        try:
            _cid = _uuid.UUID(company_id)
        except ValueError:
            return True
        async with AsyncSessionLocal() as _db:
            val = (
                await _db.execute(
                    _select(LiaFieldToggle.is_active).where(
                        LiaFieldToggle.company_id == _cid,
                        LiaFieldToggle.field_key == "benefits",
                    )
                )
            ).scalar_one_or_none()
        return val is not False  # None (sem row) ou True => ativo

    try:
        return run_coro_in_threadpool(_read, timeout=_TIMEOUT_S)
    except Exception:
        return True  # fail-open


def _fetch_benefits_matching(
    company_id: str,
    seniority: str | None,
    department: str | None,
    contract_type: str | None,
    subsidiary: str | None = None,
    subsidiary_cnpj: str | None = None,
) -> List[Dict[str, Any]]:
    """Chama CompanyBenefitRepository.list_matching em threadpool.

    Retorna lista de dicts com campos canonicos + confidence score.
    """
    async def _do():
        from app.core.database import AsyncSessionLocal
        from app.domains.company.repositories.company_benefit_repository import (
            CompanyBenefitRepository,
        )
        async with AsyncSessionLocal() as db:
            repo = CompanyBenefitRepository(db)
            pairs = await repo.list_matching(
                company_id,
                seniority_level=seniority,
                department=department,
                contract_type=contract_type,
                subsidiary=subsidiary,
                subsidiary_cnpj=subsidiary_cnpj,
            )
            result = []
            for benefit, matches in pairs:
                # Confidence baseada em quantas restricoes o benefit tem que casam
                dims_set = (
                    bool(benefit.seniority_levels),
                    bool(benefit.departments),
                    bool(benefit.contract_types),
                )
                num_restrictions = sum(dims_set)

                if not matches:
                    continue  # nao mostrar o que claramente nao se aplica

                if num_restrictions == 3:
                    confidence = 0.95
                elif num_restrictions == 2:
                    confidence = 0.80
                elif num_restrictions == 1:
                    confidence = 0.60
                else:
                    confidence = 0.50  # universal (sem restricao = aplica a todos)

                result.append({
                    "id": str(benefit.id),
                    "name": benefit.name,
                    "category": benefit.category,
                    "description": benefit.description or "",
                    "value": benefit.value,
                    "value_type": benefit.value_type or "fixed",
                    "currency": benefit.currency or "BRL",
                    "frequency": benefit.frequency or "monthly",
                    "provider": benefit.provider or "",
                    "notes": benefit.notes or "",
                    "confidence": confidence,
                    "source": "catalog",
                    "benefit_id": str(benefit.id),
                })
            # Sort: maior confidence primeiro
            result.sort(key=lambda x: x["confidence"], reverse=True)
            return result

    try:
        return run_coro_in_threadpool(_do, timeout=_TIMEOUT_S) or []
    except Exception as exc:
        logger.warning("[BenefitsNode] list_matching failed (fail-open): %s", exc)
        return []


def benefits_node(state: JobCreationState) -> JobCreationState:
    """No de confirmacao de beneficios.

    - Se benefits_suggested ja True E confirmed_benefits preenchido: pass-through.
    - Caso contrario: fetch catalogo + matching, emite panel, seta benefits_suggested.
    """
    t0 = time.time()

    # Pass-through se ja confirmado
    if state.get("benefits_suggested") and state.get("confirmed_benefits"):
        logger.info("[BenefitsNode] already confirmed, pass-through")
        return state

    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id or company_id in ("default", "unknown"):
        logger.warning("[BenefitsNode] no company_id -- skip benefits")
        updates: Dict[str, Any] = {
            "benefits_suggested": True,
            "confirmed_benefits": [],
        }
        return {**state, **updates}

    # Toggle gate: 'benefits' OFF => skip painel, wizard passa direto
    if not _benefits_toggle_active(state):
        logger.info("[BenefitsNode] toggle 'benefits' OFF — skip painel")
        return {**state, "benefits_suggested": True, "confirmed_benefits": []}

    seniority = state.get("seniority_resolved") or state.get("parsed_seniority") or None
    department = state.get("parsed_department") or None
    contract_type = state.get("parsed_employment_type") or None

    subsidiary = state.get("parsed_subsidiary") or None
    subsidiary_cnpj = state.get("parsed_subsidiary_cnpj") or None
    matched_benefits = _fetch_benefits_matching(company_id, seniority, department, contract_type, subsidiary, subsidiary_cnpj)

    # Separa sugeridos (alta confianca) de catalogados (media/baixa)
    suggested = [b for b in matched_benefits if b["confidence"] >= 0.80]
    catalog = [b for b in matched_benefits if b["confidence"] < 0.80]

    context_label = ""
    if seniority:
        context_label += f"nivel {seniority}"
    if department:
        sep = " / " if context_label else ""
        context_label += f"{sep}dept. {department}"

    logger.info(
        "[BenefitsNode] company=%s suggested=%d catalog=%d context=%r %.0fms",
        company_id, len(suggested), len(catalog), context_label, (time.time() - t0) * 1000,
    )

    updates = {
        "current_stage": "benefits",
        "stage_history": (state.get("stage_history") or []) + ["benefits"],
        "completeness": calculate_completeness("benefits"),
        "requires_approval": False,
        "benefits_suggested": True,
        "ws_stage_payload": build_ws_stage_payload(
            stage="benefits",
            completeness=calculate_completeness("benefits"),
            requires_approval=False,
            data={
                "message": (
                    f"Quais beneficios esta vaga oferece?\n\n"
                    + (
                        f"Para o perfil ({context_label}), encontrei {len(suggested)} beneficio(s) "
                        f"compativel(is) no catalogo da sua empresa.\n\n"
                        if suggested
                        else "Nao encontrei beneficios especificos para este perfil no catalogo.\n\n"
                    )
                    + "Confirme, ajuste ou adicione beneficios."
                ),
                "suggested": suggested,
                "catalog": catalog,
                "context": {
                    "seniority": seniority,
                    "department": department,
                    "contract_type": contract_type,
                },
            },
        ),
    }

    return {**state, **updates}
