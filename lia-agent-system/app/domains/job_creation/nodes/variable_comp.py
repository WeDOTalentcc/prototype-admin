"""variable_comp_node canonical -- inferencia + confirmacao de remuneracao variavel (2026-06-18).

Posicao no grafo: apos benefits_node, antes de competency.

Fluxo:
1. Le seniority + department + contract_type + extracted JD variable comp do estado.
2. Chama CompensationComponentRepository.list_matching() -- AND por 3-5 dimensoes
   (seniority, department, contract_type, subsidiary, subsidiary_cnpj).
3. Separa em "suggested" (matches=True) e "catalog" (restante).
4. Emite ws_stage_payload{stage="variable_comp"} para o painel do frontend.
5. Na proxima invocacao (recruiter confirmou via right_panel_form),
   confirmed_variable_compensation ja esta no estado -- o no passa direto.

O node tambem consome "variable_comp_extracted" do estado (caso o intake
tenha conseguido extrair dados de remuneracao variavel do JD de origem).
Se extraido do JD, o confidence inicial e maior (0.90) pois veio de dados
explicitamente informados pelo recrutador.
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


def _fetch_comp_matching(
    company_id: str,
    seniority: str | None,
    department: str | None,
    contract_type: str | None,
    subsidiary: str | None = None,
    subsidiary_cnpj: str | None = None,
) -> List[Dict[str, Any]]:
    """Chama CompensationComponentRepository.list_matching em threadpool."""
    async def _do():
        from app.core.database import AsyncSessionLocal
        from app.domains.company.repositories.compensation_component_repository import (
            CompensationComponentRepository,
        )
        async with AsyncSessionLocal() as db:
            repo = CompensationComponentRepository(db)
            pairs = await repo.list_matching(
                company_id,
                seniority_level=seniority,
                department=department,
                contract_type=contract_type,
                subsidiary=subsidiary,
                subsidiary_cnpj=subsidiary_cnpj,
            )
            result = []
            for comp, matches in pairs:
                if not matches:
                    continue

                dims_set = (
                    bool(comp.seniority_levels),
                    bool(comp.departments),
                    bool(comp.contract_types),
                    bool(comp.subsidiaries),
                )
                num_restrictions = sum(dims_set)

                if num_restrictions >= 3:
                    confidence = 0.95
                elif num_restrictions == 2:
                    confidence = 0.80
                elif num_restrictions == 1:
                    confidence = 0.65
                else:
                    confidence = 0.55  # universal

                result.append({
                    "id": str(comp.id),
                    "name": comp.name,
                    "kind": comp.kind,
                    "description": comp.description or "",
                    "target_pct": comp.target_pct,
                    "frequency": comp.frequency or "annual",
                    "currency": comp.currency or "BRL",
                    "notes": comp.notes or "",
                    "confidence": confidence,
                    "source": "catalog",
                    "component_id": str(comp.id),
                })

            result.sort(key=lambda x: x["confidence"], reverse=True)
            return result

    try:
        return run_coro_in_threadpool(_do, timeout=_TIMEOUT_S) or []
    except Exception as exc:
        logger.warning("[VariableCompNode] list_matching failed (fail-open): %s", exc)
        return []


def variable_comp_node(state: JobCreationState) -> JobCreationState:
    """No de confirmacao de remuneracao variavel.

    - Se variable_comp_suggested ja True E confirmed_variable_compensation preenchido: pass-through.
    - Caso contrario: fetch catalogo + matching, emite panel, seta variable_comp_suggested.
    """
    t0 = time.time()

    # Pass-through se ja confirmado
    if state.get("variable_comp_suggested") and state.get("confirmed_variable_compensation") is not None:
        logger.info("[VariableCompNode] already confirmed, pass-through")
        return state

    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id or company_id in ("default", "unknown"):
        logger.warning("[VariableCompNode] no company_id -- skip variable comp")
        updates: Dict[str, Any] = {
            "variable_comp_suggested": True,
            "confirmed_variable_compensation": [],
        }
        return {**state, **updates}

    seniority = state.get("seniority_resolved") or state.get("parsed_seniority") or None
    department = state.get("parsed_department") or None
    contract_type = state.get("parsed_employment_type") or None
    # Fase 2 (2026-06-18): subsidiary propagado via intake.py -> dept.subsidiary_cnpj
    subsidiary = state.get("parsed_subsidiary") or None
    subsidiary_cnpj = state.get("parsed_subsidiary_cnpj") or None

    matched_comps = _fetch_comp_matching(
        company_id, seniority, department, contract_type, subsidiary, subsidiary_cnpj,
    )

    # Dados extraidos do JD (caso o intake tenha extraido)
    jd_extracted = state.get("variable_comp_extracted") or []

    # Se JD extraiu dados, elevar confidence deles para 0.90 e mesclar
    jd_ids = set()
    for jd_item in jd_extracted:
        if isinstance(jd_item, dict) and jd_item.get("component_id"):
            jd_ids.add(jd_item["component_id"])

    for comp in matched_comps:
        if comp["component_id"] in jd_ids:
            comp["confidence"] = 0.90
            comp["source"] = "jd_extracted"

    suggested = [c for c in matched_comps if c["confidence"] >= 0.80]
    catalog = [c for c in matched_comps if c["confidence"] < 0.80]

    context_label = ""
    if seniority:
        context_label += f"nivel {seniority}"
    if department:
        sep = " / " if context_label else ""
        context_label += f"{sep}dept. {department}"

    has_any = bool(suggested or catalog)

    logger.info(
        "[VariableCompNode] company=%s suggested=%d catalog=%d jd_extracted=%d context=%r %.0fms",
        company_id, len(suggested), len(catalog), len(jd_extracted),
        context_label, (time.time() - t0) * 1000,
    )

    if not has_any:
        # Nenhum componente no catalogo -- perguntar diretamente
        msg_text = (
            "Esta vaga possui remuneracao variavel?\n\n"
            "Informe o tipo (PLR, bonus por meta, comissao, equity, spot bonus) "
            "e os parametros (percentual alvo, frequencia).\n\n"
            "Se nao houver remuneracao variavel, responda 'nao'."
        )
    else:
        msg_text = (
            "Esta vaga possui remuneracao variavel?\n\n"
            + (
                f"Para o perfil ({context_label}), encontrei {len(suggested)} componente(s) "
                f"compativel(is) no catalogo da empresa.\n\n"
                if suggested
                else ""
            )
            + "Confirme, ajuste valores ou adicione componentes de remuneracao variavel."
        )

    updates = {
        "current_stage": "variable_comp",
        "stage_history": (state.get("stage_history") or []) + ["variable_comp"],
        "completeness": calculate_completeness("variable_comp"),
        "requires_approval": False,
        "variable_comp_suggested": True,
        "ws_stage_payload": build_ws_stage_payload(
            stage="variable_comp",
            completeness=calculate_completeness("variable_comp"),
            requires_approval=False,
            data={
                "message": msg_text,
                "suggested": suggested,
                "catalog": catalog,
                "jd_extracted": jd_extracted,
                "context": {
                    "seniority": seniority,
                    "department": department,
                    "contract_type": contract_type,
                },
            },
        ),
    }

    return {**state, **updates}
