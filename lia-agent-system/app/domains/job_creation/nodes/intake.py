"""intake_node canonical — PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantém comportamento byte-identical via tests de regressão.

Pre-F1: Parse user input via IntakeExtractor (LLM + regex fallback).
"""

import logging
import time
from typing import Any, Dict

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.helpers.ws_payload_builder import (
    build_ws_stage_payload,
)
from app.domains.job_creation.helpers.i18n import msg
from app.domains.job_creation.helpers.intake_audit import emit_intake_audit

logger = logging.getLogger(__name__)


def intake_node(state: JobCreationState) -> JobCreationState:
    """Pre-F1: Parse user input via IntakeExtractor (LLM + regex fallback).

    Phase 3 / F3-1 — replaces previous stub pass-through.
    Extracts: parsed_title, parsed_seniority, parsed_department, parsed_location, parsed_model.
    Fail-open: low confidence on extraction failure does NOT block the wizard.
    """
    # Deferred imports to avoid circular dependency with graph.py module-level state.
    from app.domains.job_creation.graph import (
        get_intake_extractor,
        _suggest_pipeline_template,
        _build_pipeline_template_db_suggestion,
    )

    t0 = time.time()
    query = state.get("user_query", "") or state.get("raw_input", "")
    logger.info("[JobCreation:intake] query=%s", query[:80])

    # T2 (Task #1085) — resume short-circuit em DOIS sinais (cobre WS canônico
    # E action-based): (a) gate_resume_message setado pelo path
    # domain.py::_handle_gate_jd; OU (b) jd_enriched já populado
    # vindo do checkpoint (path canônico WS via WizardSessionService).
    # Em ambos os casos, parsed_title já foi extraído em turno anterior
    # e re-rodar IntakeExtractor (~1-3s + tokens) é desperdício puro.
    if state.get("parsed_title") and (
        state.get("gate_resume_message") or state.get("jd_enriched")
    ):
        return {**state, "current_stage": "intake"}

    # ── F3-1: IntakeExtractor (LLM + regex fallback) ──
    parsed_title = state.get("parsed_title")
    parsed_seniority = state.get("parsed_seniority")
    parsed_department = state.get("parsed_department")
    parsed_location = state.get("parsed_location")
    parsed_model = state.get("parsed_model")
    intake_confidence = 0.0
    intake_source = "none"
    try:
        # Use module-level get_intake_extractor() so tests can monkeypatch it.
        extractor = get_intake_extractor()
        right_panel_form = state.get("right_panel_form") or {}
        attached_file_text = state.get("attached_file_text") or ""
        if right_panel_form or attached_file_text:
            extraction = extractor.extract_from_sources(
                user_text=query,
                right_panel_form=right_panel_form,
                attached_file_text=attached_file_text,
            )
        else:
            extraction = extractor.extract(query)
        # Fill ONLY fields that arent already explicit in state.
        # extraction is a JobIntakePayload (canonical schema —
        # ). Each field is an IntakeField with
        # .value and .source. Reading raw attributes (.parsed_title)
        # would AttributeError silently and was the root cause of Task #1096
        # input-thin guard always firing — see audit
        # docs/audits/wizard-job-creation-2026-05.md and
        # docs/architecture/wizard-flow.md.
        def _val(field_name: str):
            f = getattr(extraction, field_name, None)
            if f is None:
                return None
            v = getattr(f, "value", None)
            if v in (None, "", []):
                return None
            return v

        parsed_title = parsed_title or _val("title")
        parsed_seniority = parsed_seniority or _val("seniority")
        parsed_department = parsed_department or _val("department")
        parsed_location = parsed_location or _val("location")
        # NB: schema field is work_model (remoto/hibrido/presencial),
        # exposed downstream as parsed_model for state continuity.
        parsed_model = parsed_model or _val("work_model")
        intake_confidence = extraction.overall_confidence
        _title_field = getattr(extraction, "title", None)
        intake_source = (
            getattr(_title_field, "source", None) or "regex"
        )
        logger.info(
            "[JobCreation:intake] F3-1 extraction: source=%s, conf=%.2f, "
            "title=%s, seniority=%s, location=%s, model=%s",
            intake_source, intake_confidence, parsed_title, parsed_seniority,
            parsed_location, parsed_model,
        )
    except Exception as _ex_exc:
        logger.warning(
            "[JobCreation:intake] F3-1 extraction failed (fail-open): %s", _ex_exc,
        )

    # WT-2022 P0.C: LGPD Art. 20 audit trail para decisao automatizada de
    # intake extraction. Delegado a emit_intake_audit (helper canonical em
    # app/domains/job_creation/helpers/intake_audit.py) — 70 LOC inline
    # extraidas em PR-11 (F-4.3). Fail-safe: gap NUNCA bloqueia wizard.
    emit_intake_audit(
        company_id=str(state.get("workspace_id") or state.get("company_id") or ""),
        job_id=str(state.get("job_id")) if state.get("job_id") else None,
        intake_source=intake_source,
        intake_confidence=intake_confidence,
        parsed_title=parsed_title,
        parsed_seniority=parsed_seniority,
        parsed_location=parsed_location,
        parsed_model=parsed_model,
    )

    updates: Dict[str, Any] = {
        "current_stage": "intake",
        "raw_input": query,
        "parsed_title": parsed_title,
        "parsed_seniority": parsed_seniority,
        "parsed_department": parsed_department,
        "parsed_location": parsed_location,
        "parsed_model": parsed_model,
        "intake_confidence": intake_confidence,
        "stage_history": (state.get("stage_history") or []) + ["intake"],
        "completeness": calculate_completeness("intake"),
        "requires_approval": False,
        "ws_stage_payload": build_ws_stage_payload(
            stage="intake",
            completeness=calculate_completeness("intake"),
            requires_approval=False,
            data={
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    msg("intake.captured", parsed_title=parsed_title)
                    if parsed_title
                    else msg("intake.ask_for_title")
                ),
                "raw_input": query,
                "parsed_title": parsed_title,
                "parsed_seniority": parsed_seniority,
                "parsed_department": parsed_department,
                "parsed_location": parsed_location,
                "parsed_model": parsed_model,
                "intake_confidence": intake_confidence,
                "intake_source": intake_source,
                # Task #1055 — emite o pipeline_template determinístico já no
                # turno de intake para que o WizardPipelineTemplateCard apareça
                # mesmo se a chamada de culture-stack ou Gemini falhar depois.
                "suggestions_data": {
                    "pipeline_template": _suggest_pipeline_template(
                        parsed_title, parsed_seniority,
                    ),
                    # Sprint Pipeline Templates 2026-05-26 — canonical DB-based suggestion
                    # (Phase 1.6). Frontend prefere quando templates != [] e score >= threshold.
                    "pipeline_template_db": _build_pipeline_template_db_suggestion(state),
                },
            },
        ),
    }

    # ── Sprint Pipeline Templates Gap #5 (2026-05-26) — wiring backend↔frontend ──
    # Frontend useWizardFlow lê ui_action no top do ws_stage_payload + data.templates.
    # Quando DB suggestion tem should_suggest=True, eleva templates pro top de data
    # e emite ui_action="suggest_pipeline_template". data.suggestions_data.pipeline_template_db
    # permanece intacto (retrocompat com wizard-plan-card.ts legacy via Task #1055).
    try:
        _db_sugg = (
            (updates.get("ws_stage_payload", {}).get("data", {}) or {})
            .get("suggestions_data", {})
            .get("pipeline_template_db")
        )
        if (
            isinstance(_db_sugg, dict)
            and _db_sugg.get("should_suggest")
            and _db_sugg.get("templates")
        ):
            updates["ws_stage_payload"]["ui_action"] = "suggest_pipeline_template"
            updates["ws_stage_payload"]["data"]["templates"] = _db_sugg["templates"]
    except Exception:  # noqa: BLE001 — fail-open por design (telemetria, não bloqueia fluxo)
        pass

    # NOTE on LL-2 manager preferences:
    # ManagerPreferencesService.apply_to_state() is invoked by
    # WizardSessionService.process_message() BEFORE this graph runs.
    # See app/domains/job_creation/services/wizard_session_service.py:217+.
    # Centralizing it there avoids double DB hits and keeps single source of truth.

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:intake] %0.fms", elapsed)
    return {**state, **updates}
