"""intake_node canonical — PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantém comportamento byte-identical via tests de regressão.

Pre-F1: Parse user input via IntakeExtractor (LLM + regex fallback).
"""

import logging
import re
import time
import unicodedata
from difflib import SequenceMatcher
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
from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool
from app.domains.job_creation.services.seniority_resolver import (
    _infer_from_title,
    SENIORITY_DISPLAY_NAMES,
)

logger = logging.getLogger(__name__)


# Audit 2026-06-03 (#2 + #8): derivacao deterministica no intake. Principio:
# derivar de SINAL REAL (titulo digitado, prefixo do email), pre-preencher como
# SUGESTAO e sinalizar proveniencia -- nunca alucinar (vide bug "Carlos Mendes").
# O recrutador confirma/corrige; estes campos sao sugestoes, nao fatos.
_GENERIC_MAILBOX_PREFIXES = {
    "rh", "contato", "vagas", "noreply", "no-reply", "jobs", "recrutamento",
    "talent", "talentos", "recruiting", "hr", "careers", "carreiras", "admin",
    "info", "atendimento", "suporte", "comercial",
}


def _derive_name_from_email(email: str | None) -> str | None:
    """Delega ao helper canonical (helpers.manager_identity). Antes havia copia
    local -- unificado no audit 2026-06-05 (uma fonte da verdade)."""
    from app.domains.job_creation.helpers.manager_identity import (
        derive_name_from_email,
    )
    return derive_name_from_email(email)


# Audit 2026-06-03 (#8 departamento tenant-aware): casar o título contra os
# departamentos REAIS do cliente (nunca inventar um que ele não tem). Tokens de
# senioridade são removidos do título antes do match — assim "Diretor
# Financeiro" casa com "Finanças", não com um eventual departamento "Diretoria".
_SENIORITY_TOKENS = {
    "diretor", "diretora", "diretoria", "gerente", "coordenador", "coordenadora",
    "analista", "assistente", "estagiario", "estagiaria", "junior", "pleno",
    "senior", "especialista", "head", "lead", "supervisor", "supervisora",
    "chefe", "presidente", "tecnico", "tecnica", "auxiliar", "trainee",
    "vp", "ceo", "cto", "cfo", "coo", "cmo",
}
_DEPT_STOPWORDS = {"de", "da", "do", "e", "das", "dos"}


def _norm_txt(value: str) -> str:
    return (
        unicodedata.normalize("NFKD", value or "")
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def _dept_tokens(value: str, *, drop_seniority: bool = False) -> list:
    toks = [
        t for t in re.split(r"[^a-z0-9]+", _norm_txt(value))
        if len(t) >= 3 and t not in _DEPT_STOPWORDS
    ]
    if drop_seniority:
        toks = [t for t in toks if t not in _SENIORITY_TOKENS]
    return toks


def _tok_sim(a: str, b: str) -> float:
    if a == b:
        return 1.0
    n = min(len(a), len(b))
    if n >= 4:
        cp = 0
        for x, y in zip(a, b):
            if x == y:
                cp += 1
            else:
                break
        if cp >= 4:
            return 0.85
    return SequenceMatcher(None, a, b).ratio()


def _match_department(title, dept_names, threshold: float = 0.8):
    """Delegate to canonical helper (Fase 8 A1)."""
    from app.domains.job_creation.helpers.department_match import match_department
    return match_department(title, dept_names, threshold)


_AFFIRMATIVE_PATTERNS: list[tuple[str, str]] = [
    (r"\bpcd\b|pessoa[s]?\s+com\s+defici\u00eancia|defici\u00eancia\s+f\u00edsica|defici\u00eancia\s+visual|defici\u00eancia\s+auditiva", "disability"),
    (r"\bmulhere[s]?\b|\bfeminino\b|\bfeminina\b|g\u00eanero\s+feminino|exclusiv[ao]\s+para\s+mulher", "gender"),
    (r"\bnegr[ao]s?\b|\bpretos?\b|afrodescendente[s]?|afro-descendent", "race_ethnicity"),
    (r"\blgbtqia?\+?\b|\blgbtq\b|transgên|transsexual|\btrans\b|n\u00e3o-bin\u00e1ri|nao[\\s-]binari", "lgbtqia"),
    (r"\bind\u00edgen[ao]s?\b|indigena[s]?\b|povos\s+origin\u00e1ri", "indigenous"),
    (r"\brefugiad[ao]s?\b|\bimigrante[s]?\b", "refugee"),
    (r"\bafirmativ[ao]\b|a\u00e7\u00e3o\s+afirmativa|vaga\s+afirmativa", "other"),
]


def _detect_affirmative_intent(query: str) -> tuple[bool, str | None, str | None]:
    """Detecta vaga afirmativa no texto do recrutador via regex.
    Retorna (is_affirmative, criteria_primary, description_hint).
    Proveniencia declarada -- nunca alucina.
    """
    if not query:
        return False, None, None
    text = unicodedata.normalize("NFKD", query.lower())
    # Remove combining chars (acentos) para match uniforme
    text = "".join(c for c in text if not unicodedata.combining(c))
    for pattern, criteria in _AFFIRMATIVE_PATTERNS:
        if re.search(pattern, text):
            desc = query.strip()[:120] if query else None
            return True, criteria, desc
    return False, None, None

def _derive_intake_suggestions(
    *,
    parsed_title: str | None,
    parsed_seniority: str | None,
    parsed_manager_name: str | None,
    parsed_manager_email: str | None,
):
    """Pre-preenche senioridade (do titulo) e nome do gestor (do email) quando
    ausentes, a partir de sinais determinísticos. Nao sobrescreve valor explicito.

    Retorna (seniority, seniority_inferred, manager_name, name_suggested).
    """
    seniority = parsed_seniority
    seniority_inferred = False
    if not seniority and parsed_title:
        level, conf = _infer_from_title(parsed_title)
        if level and conf >= 0.8:
            seniority = SENIORITY_DISPLAY_NAMES.get(level, level)
            seniority_inferred = True

    manager_name = parsed_manager_name
    name_suggested = False
    if not manager_name and parsed_manager_email:
        derived = _derive_name_from_email(parsed_manager_email)
        if derived:
            manager_name = derived
            name_suggested = True

    return seniority, seniority_inferred, manager_name, name_suggested

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
    # Frente 2 (2026-05-29): short-circuit adicional quando intake_gate já foi visitado.
    # Evita re-rodar IntakeExtractor nos turnos após intake_gate emitir sugestão/clarify.
    if state.get("parsed_title") and (
        state.get("gate_resume_message")
        or state.get("jd_enriched")
        or state.get("intake_salary_suggested")
        or state.get("intake_approved") is True
    ):
        return {**state, "current_stage": "intake"}

    # ── F3-1: IntakeExtractor (LLM + regex fallback) ──
    parsed_title = state.get("parsed_title")
    parsed_seniority = state.get("parsed_seniority")
    parsed_department = state.get("parsed_department")
    parsed_location = state.get("parsed_location")
    parsed_model = state.get("parsed_model")
    parsed_employment_type = state.get("parsed_employment_type")  # P0-A
    parsed_manager_name = state.get("parsed_manager_name")  # FASE 5
    parsed_manager_email = state.get("parsed_manager_email")  # FASE 5
    parsed_languages = state.get("parsed_languages") or []  # D1
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
        # P0-A: regime de contratação (CLT/PJ/...) — schema field contract_type.
        parsed_employment_type = parsed_employment_type or _val("contract_type")
        # FASE 5 - gestor + email (schema fields manager_name/manager_email).
        parsed_manager_name = parsed_manager_name or _val("manager_name")
        parsed_manager_email = parsed_manager_email or _val("manager_email")
        parsed_languages = parsed_languages or _val("languages") or []  # D1
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

    # Audit 2026-06-03 (#2 + #8): derivacao deterministica (senioridade do titulo,
    # nome do gestor do email). Roda fora do try para valer mesmo se a extracao
    # LLM falhou. Pre-preenche como SUGESTAO + flags de proveniencia (a LIA avisa
    # que deduziu, e o recrutador confirma/corrige).
    (
        parsed_seniority,
        seniority_inferred_from_title,
        parsed_manager_name,
        manager_name_suggested_from_email,
    ) = _derive_intake_suggestions(
        parsed_title=parsed_title,
        parsed_seniority=parsed_seniority,
        parsed_manager_name=parsed_manager_name,
        parsed_manager_email=parsed_manager_email,
    )

    # Audit 2026-06-03 (#8 departamento tenant-aware): quando o departamento não
    # veio, casa o título contra os departamentos REAIS do cliente (DB, guardado
    # por timeout + fail-open). Nunca inventa um depto que o cliente não tem.
    department_inferred_from_title = False
    _dept_names: list = []  # [FIX P2] inicializado antes do try para dept-suggestion
    if not parsed_department and parsed_title:
        _company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if _company_id:
            try:
                async def _load_company_departments():
                    from uuid import UUID
                    from app.core.database import AsyncSessionLocal
                    from app.domains.company.repositories.department_repository import (
                        DepartmentRepository,
                    )
                    async with AsyncSessionLocal() as _db:
                        rows = await DepartmentRepository(_db).list_active_for_company(
                            UUID(_company_id)
                        )
                        # Retorna (name, subsidiary_name, subsidiary_cnpj) para
                        # propagacao da dimensao de filial ao estado da vaga
                        # (Fase 2 matching 2026-06-18).
                        return [
                            (
                                r.name,
                                getattr(r, "subsidiary_name", None),
                                getattr(r, "subsidiary_cnpj", None),
                            )
                            for r in rows if getattr(r, "name", None)
                        ]

                _dept_data = run_coro_in_threadpool(
                    _load_company_departments, timeout=2.0
                ) or []
                _dept_names = [d[0] for d in _dept_data]
                _dept_subsidiary_map = {d[0]: (d[1], d[2]) for d in _dept_data}
                _matched_dept = _match_department(parsed_title, _dept_names)
                if _matched_dept:
                    parsed_department = _matched_dept
                    department_inferred_from_title = True
                    # Propaga filial/CNPJ do departamento para o estado
                    _sub_name, _sub_cnpj = _dept_subsidiary_map.get(_matched_dept, (None, None))
                    if _sub_name or _sub_cnpj:
                        state = dict(state)
                        state["parsed_subsidiary"] = _sub_name
                        state["parsed_subsidiary_cnpj"] = _sub_cnpj
                    logger.info(
                        "[JobCreation:intake] departamento deduzido do titulo "
                        "%s -> %s (match tenant-aware, subsidiary=%s)", parsed_title, _matched_dept, _sub_name,
                    )
            except Exception as _dept_exc:
                logger.warning(
                    "[JobCreation:intake] dept inference fail-open: %s", _dept_exc,
                )

    # [FIX P2 dept-suggestion] Quando nao ha match, surfacar candidato do titulo
    # para o wizard oferecer sugestao de criacao ou escolha de dept existente.
    _department_candidate_from_title: str | None = None
    _existing_departments_for_state: list = []
    if not parsed_department and parsed_title:
        _candidate_dept_names = _dept_names  # set by DB lookup above, or [] if not reached
        if _candidate_dept_names:
            _existing_departments_for_state = list(_candidate_dept_names[:10])
            _title_toks = _dept_tokens(parsed_title, drop_seniority=True)
            if _title_toks:
                _department_candidate_from_title = " ".join(
                    t.capitalize() for t in _title_toks[:3]
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

    # Audit 2026-06-03: transparencia -- quando algo foi deduzido, a LIA avisa
    # explicitamente na mensagem (chega ao chat via stage_data.message).
    # W1-B (2026-06-12): inicializa flags de vaga afirmativa.
    is_affirmative_detected = False
    affirmative_criteria_detected: str | None = None
    affirmative_description_detected: str | None = None

    _base_intake_msg = (
        msg("intake.captured", parsed_title=parsed_title)
        if parsed_title
        else msg("intake.ask_for_title")
    )
    _deduction_notes = []
    if seniority_inferred_from_title and parsed_seniority:
        _deduction_notes.append(
            f"Deduzi a senioridade **{parsed_seniority}** pela nomenclatura do "
            f"titulo -- ajuste se nao for o caso."
        )
    if manager_name_suggested_from_email and parsed_manager_name:
        _deduction_notes.append(
            f"Pelo email, o gestor parece ser **{parsed_manager_name}** -- "
            f"confirme ou corrija."
        )
    if department_inferred_from_title and parsed_department:
        _deduction_notes.append(
            f"Pela area do titulo, deduzi o departamento **{parsed_department}** -- "
            f"confirme ou ajuste."
        )
    # W1-B (2026-06-12): deteccao de vaga afirmativa -- antes de montar mensagem.
    if not state.get("is_affirmative") and query:
        _aff, _crit, _desc = _detect_affirmative_intent(query)
        if _aff:
            is_affirmative_detected = True
            affirmative_criteria_detected = _crit
            affirmative_description_detected = _desc
            _deduction_notes.append(
                f"Detectei que esta pode ser uma **vaga afirmativa** "
                f"({'para PCD' if _crit == 'disability' else 'grupo prioritario: ' + (_crit or 'outro')}) "
                f"-- confirme se e isso ou corrija."
            )

    intake_message = _base_intake_msg
    if _deduction_notes:
        intake_message = _base_intake_msg + " " + " ".join(_deduction_notes)

    updates: Dict[str, Any] = {
        "current_stage": "intake",
        "raw_input": query,
        "parsed_title": parsed_title,
        "parsed_seniority": parsed_seniority,
        "parsed_department": parsed_department,
        "parsed_location": parsed_location,
        "parsed_model": parsed_model,
        "parsed_employment_type": parsed_employment_type,
        "parsed_manager_name": parsed_manager_name,
        "parsed_manager_email": parsed_manager_email,
        "parsed_languages": parsed_languages,
        "intake_confidence": intake_confidence,
        "seniority_inferred_from_title": seniority_inferred_from_title,
        "manager_name_suggested_from_email": manager_name_suggested_from_email,
        "department_inferred_from_title": department_inferred_from_title,
        "department_candidate_from_title": _department_candidate_from_title,
        "existing_departments": _existing_departments_for_state,
        "parsed_subsidiary": state.get("parsed_subsidiary"),
        "parsed_subsidiary_cnpj": state.get("parsed_subsidiary_cnpj"),
        "is_affirmative": is_affirmative_detected or state.get("is_affirmative", False),
        "affirmative_criteria_primary": affirmative_criteria_detected or state.get("affirmative_criteria_primary"),
        "affirmative_description": affirmative_description_detected or state.get("affirmative_description"),
        "stage_history": (state.get("stage_history") or []) + ["intake"],
        "completeness": calculate_completeness("intake"),
        "requires_approval": False,
        "ws_stage_payload": build_ws_stage_payload(
            stage="intake",
            completeness=calculate_completeness("intake"),
            requires_approval=False,
            data={
                # Task #1099 — invariant: data.message obrigatório.
                "message": intake_message,
                "raw_input": query,
                "parsed_title": parsed_title,
                "parsed_seniority": parsed_seniority,
                "parsed_department": parsed_department,
                "parsed_location": parsed_location,
                "parsed_model": parsed_model,
                "parsed_employment_type": parsed_employment_type,
                "parsed_manager_name": parsed_manager_name,
                "parsed_manager_email": parsed_manager_email,
                "intake_confidence": intake_confidence,
                "intake_source": intake_source,
                "seniority_inferred_from_title": seniority_inferred_from_title,
                "manager_name_suggested_from_email": manager_name_suggested_from_email,
                "department_inferred_from_title": department_inferred_from_title,
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
