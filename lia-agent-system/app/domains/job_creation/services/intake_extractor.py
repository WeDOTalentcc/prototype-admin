"""IntakeExtractor — canonical Pre-F1 intake extraction service.

Single source of truth for parsing the recruiter's free-text intake into
a structured `JobIntakePayload`. Used exclusively by `intake_node`
(`graph.py`) — no other module should perform intake extraction.

Responsibilities:
- Mask PII before sending text to the LLM (Compliance L1).
- Run FairnessGuard pre-check on the raw input (Compliance L2).
- Call the configured LLM (provider chosen via tenant context) to produce
  a structured `JobIntakePayload` with per-field confidence + source.
- Decide which downstream stages can be marked as pre-completed because
  the recruiter already provided enough information up-front. HITL 1
  (`jd_enrichment`) and HITL 2 (`wsi_questions`) are NEVER pre-completed.

The extractor degrades gracefully: if the LLM is unavailable or returns
malformed JSON, it falls back to a deterministic regex-based parse so the
wizard can still progress. Confidence values reflect the source.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError

from app.domains.job_creation.compliance import (
    check_input_fairness,
    mask_pii_for_llm,
)
from app.shared.types import WeDoBaseModel
from app.shared.llm_models import CANONICAL_HAIKU_MODEL

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# F-100 telemetry (PR-13 / Opção C) — medir uso real de `right_panel_form`.
#
# Decisão Paulo 2026-05-26 (Opção C): `right_panel_form` é feature half-shipped
# — backend extrai/funde 14 fields desse dict (extract_from_sources abaixo),
# MAS o frontend NUNCA shipped a UI lateral que populava esse dict no chat-
# initiated wizard. Zero matches em plataforma-lia.
#
# Plano: 48h de telemetria em prod → revisar contagem → decidir:
#   Opção A — implementar UI lateral (~2-3 dias FE) se counter > 0 e crescendo.
#   Opção B — remover backend órfão (~4h cleanup) se counter = 0 ou estagnado.
#
# Pattern canonical: app/services/voice/wsi_pipeline.py:30-55 (try/except +
# REGISTRY lookup pra hot-reload race em dev / multi-import).
# ---------------------------------------------------------------------------
try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter

    _RIGHT_PANEL_METRIC_NAME = "lia_right_panel_form_received_total"
    _existing_right_panel = getattr(
        _PROM_REGISTRY, "_names_to_collectors", {}
    ).get(_RIGHT_PANEL_METRIC_NAME)
    if _existing_right_panel is not None:
        lia_right_panel_form_received_total = _existing_right_panel
    else:
        lia_right_panel_form_received_total = _PromCounter(
            _RIGHT_PANEL_METRIC_NAME,
            (
                "Total intake_extractor.extract_from_sources calls observed "
                "with the optional right_panel_form dict. Label populated=true "
                "iff dict is non-empty AND has at least one non-empty value. "
                "Used to decide between Opção A (ship UI) vs Opção B (remove "
                "backend) — see PR-13 F-100 telemetry."
            ),
            labelnames=("populated", "stage"),
        )
    _RIGHT_PANEL_METRICS_AVAILABLE = True
except (ImportError, ValueError):  # pragma: no cover
    lia_right_panel_form_received_total = None
    _RIGHT_PANEL_METRICS_AVAILABLE = False


# Provenance enum — kept backward compatible.
#   * `user_text`         — extracted from the recruiter's free-text turn
#   * `right_panel_form`  — supplied via the right-side draft form
#   * `attached_file`     — extracted from a JD/PDF attachment
#   * `llm`/`regex`/`default`/`user` — legacy values used by older callers
FieldSource = Literal[
    "user_text",
    "right_panel_form",
    "attached_file",
    "llm",
    "regex",
    "default",
    "user",
]
ConfidenceLabel = Literal["high", "medium", "low"]
WorkModel = Literal["remoto", "hibrido", "presencial", ""]
ContractType = Literal["clt", "pj", "estagio", "temporario", "freelancer", ""]


def _label_for(score: float) -> ConfidenceLabel:
    """Map a numeric confidence to the categorical contract label."""
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


class IntakeField(BaseModel):
    """A single extracted field with provenance.

    Carries both a numeric `confidence` (0..1) used for downstream
    routing math AND a categorical `confidence_label` (`high`/`medium`/
    `low`) which is the public contract surfaced to other domains.
    """

    value: Any = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: FieldSource = "default"

    @property
    def confidence_label(self) -> ConfidenceLabel:
        return _label_for(self.confidence)


class LocationField(BaseModel):
    """Structured location — used as the `value` of `location: IntakeField`."""

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "Brasil"


# DUPLICATE_OF_INTENT: app/schemas/job_vacancy_state.py — extractor internal subset of canonical salary range (Sprint Q.1 triagem I bucket)
class SalaryRange(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    currency: str = "BRL"


class JobIntakePayload(WeDoBaseModel):
    """Canonical structured payload extracted from the recruiter's intake.

    Each field carries the extracted value, a per-field confidence
    (numeric + categorical label) and the provenance (`user_text`,
    `right_panel_form`, `attached_file`, ...). Downstream stages decide
    whether to skip themselves based on whether the confidence is high
    enough (>= 0.7) and the field is non-empty.
    """

    # --- Pre-F1 minimal identification ---
    title: IntakeField = Field(default_factory=IntakeField)
    department: IntakeField = Field(default_factory=IntakeField)
    location: IntakeField = Field(default_factory=IntakeField)  # value: LocationField
    work_model: IntakeField = Field(default_factory=IntakeField)  # remoto/hibrido/presencial
    seniority: IntakeField = Field(default_factory=IntakeField)
    # Hiring-manager identity is split per spec — name and email travel
    # independently because they often arrive from different sources
    # (form vs. email signature in attached file).
    manager_name: IntakeField = Field(default_factory=IntakeField)
    manager_email: IntakeField = Field(default_factory=IntakeField)
    contract_type: IntakeField = Field(default_factory=IntakeField)  # CLT/PJ/...

    # --- Body (responsibilities + requirements) ---
    responsibilities: IntakeField = Field(default_factory=IntakeField)  # value: list[str]
    technical_skills: IntakeField = Field(default_factory=IntakeField)  # value: list[str]
    behavioral_skills: IntakeField = Field(default_factory=IntakeField)  # value: list[str]
    languages: IntakeField = Field(default_factory=IntakeField)  # value: list[str]

    # --- Compensation ---
    salary: IntakeField = Field(default_factory=IntakeField)  # value: SalaryRange
    benefits: IntakeField = Field(default_factory=IntakeField)  # value: list[str]

    # --- Aggregate signals ---
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    raw_input: str = ""
    fairness_blocked: bool = False
    fairness_message: Optional[str] = None

    @property
    def overall_confidence_label(self) -> ConfidenceLabel:
        return _label_for(self.overall_confidence)

    def field_is_filled(self, field_name: str, min_confidence: float = 0.7) -> bool:
        """Return True if the named field is filled with sufficient confidence."""
        f = getattr(self, field_name, None)
        if not isinstance(f, IntakeField):
            return False
        if f.confidence < min_confidence:
            return False
        v = f.value
        if v is None:
            return False
        if isinstance(v, str) and not v.strip():
            return False
        if isinstance(v, list) and not v:
            return False
        if isinstance(v, dict) and not any(v.values()):
            return False
        return True


# ---------------------------------------------------------------------------
# Stage-precompletion mapping
# ---------------------------------------------------------------------------

# HITL stages that can NEVER be skipped via precompletion. These
# correspond to recruiter approval points required by methodology:
#   HITL 1 — jd_enrichment (recruiter approves the enriched JD)
#   HITL 2 — wsi_questions (recruiter approves screening questions)
NEVER_PRECOMPLETED: frozenset[str] = frozenset({"jd_enrichment", "wsi_questions"})

# Mapping: which stage can be marked pre-completed if which JobIntakePayload
# fields are filled. Stages absent from this map are never pre-completed.
#
# `intake` is precompleted when the bare minimum identification block is
# present so the wizard never re-asks for what the recruiter already
# typed. `bigfive` (behavioral profile) is precompleted only when the
# recruiter described enough behavioral signals to score it.
_STAGE_REQUIREMENTS: Dict[str, List[str]] = {
    "intake": ["title", "seniority", "work_model"],
    "salary": ["salary"],
    # `competency` is only pre-completed when the recruiter described
    # both technical and behavioral skills — otherwise the wizard still
    # needs to compose them via WSI methodology.
    "competency": ["technical_skills", "behavioral_skills"],
    # `bigfive` (behavioral inference) is skippable only when behavioral
    # skills + responsibilities are detailed enough to ground the trait
    # inference. We do NOT precomplete on technical skills alone.
    "bigfive": ["behavioral_skills", "responsibilities"],
}


def compute_precompleted_stages(payload: JobIntakePayload) -> set[str]:
    """Return the set of stage names that can be skipped because the
    recruiter already provided sufficient data up-front.

    Never includes HITL 1 (`jd_enrichment`) or HITL 2 (`wsi_questions`).
    """
    out: set[str] = set()
    for stage, required_fields in _STAGE_REQUIREMENTS.items():
        if stage in NEVER_PRECOMPLETED:
            continue
        if all(payload.field_is_filled(f) for f in required_fields):
            out.add(stage)
    return out


# ---------------------------------------------------------------------------
# Regex fallback parser (used when LLM is unavailable)
# ---------------------------------------------------------------------------

_TITLE_RE = re.compile(
    r"(?:vaga|posi[cç][aã]o|cargo)\s+(?:de\s+|para\s+)?([A-Za-zÀ-ÿ0-9 .\-/]{2,60})",
    re.IGNORECASE,
)
_SENIORITY_RE = re.compile(
    r"\b(est[áa]gio|estagi[áa]rio|j[úu]nior|junior|pleno|s[êe]nior|senior|lead|principal|staff|diretor)\b",
    re.IGNORECASE,
)
_MODEL_RE = re.compile(r"\b(remoto|h[íi]brido|presencial)\b", re.IGNORECASE)
_LOCATION_RE = re.compile(
    r"\b(?:em|no|na)\s+([A-ZÀ-Ý][A-Za-zÀ-ÿ ]{2,40})(?=[,.\n]|\s+(?:com|de|para|e|ou)\b|$)",
)
_DEPARTMENT_RE = re.compile(
    r"\b(?:do|para o|no)\s+(?:time|departamento|setor|squad)\s+(?:de\s+)?([A-Za-zÀ-ÿ ]{2,40})",
    re.IGNORECASE,
)
_SALARY_RE = re.compile(
    r"R\$\s*([\d.]+(?:,\d{2})?)\s*(?:a|até|-)\s*R\$\s*([\d.]+(?:,\d{2})?)",
    re.IGNORECASE,
)


def _normalize_seniority(raw: str) -> str:
    s = raw.lower().strip()
    if s.startswith("est"):
        return "estagiario"
    if "jun" in s:
        return "junior"
    if "sen" in s:
        return "senior"
    return s


def _normalize_model(raw: str) -> WorkModel:
    s = raw.lower().strip()
    if s.startswith("rem"):
        return "remoto"
    if s.startswith("h"):
        return "hibrido"
    if s.startswith("pres"):
        return "presencial"
    return ""  # type: ignore[return-value]


def _regex_extract(raw: str) -> JobIntakePayload:
    """Best-effort regex extraction. Used as fallback when LLM fails."""
    payload = JobIntakePayload(raw_input=raw)

    if m := _TITLE_RE.search(raw):
        payload.title = IntakeField(value=m.group(1).strip(), confidence=0.45, source="regex")

    if m := _SENIORITY_RE.search(raw):
        payload.seniority = IntakeField(
            value=_normalize_seniority(m.group(1)),
            confidence=0.55,
            source="regex",
        )

    if m := _MODEL_RE.search(raw):
        payload.work_model = IntakeField(
            value=_normalize_model(m.group(1)),
            confidence=0.6,
            source="regex",
        )

    if m := _LOCATION_RE.search(raw):
        payload.location = IntakeField(
            value=LocationField(city=m.group(1).strip()).model_dump(),
            confidence=0.4,
            source="regex",
        )

    if m := _DEPARTMENT_RE.search(raw):
        payload.department = IntakeField(value=m.group(1).strip(), confidence=0.4, source="regex")

    if m := _SALARY_RE.search(raw):
        def _to_int(s: str) -> Optional[int]:
            try:
                return int(s.replace(".", "").split(",")[0])
            except Exception:
                return None
        payload.salary = IntakeField(
            value=SalaryRange(min=_to_int(m.group(1)), max=_to_int(m.group(2))).model_dump(),
            confidence=0.5,
            source="regex",
        )

    # Aggregate confidence = mean of filled fields.
    filled = [
        getattr(payload, f).confidence
        for f in (
            "title",
            "seniority",
            "work_model",
            "location",
            "department",
            "salary",
        )
        if getattr(payload, f).confidence > 0
    ]
    payload.overall_confidence = round(sum(filled) / len(filled), 2) if filled else 0.0
    return payload


# ---------------------------------------------------------------------------
# IntakeExtractor — main entrypoint
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Você é um extrator estruturado de dados de vaga para a LIA.
Receba o texto livre do recrutador e devolva APENAS JSON válido com a forma:

{
  "title": {"value": str, "confidence": 0..1},
  "department": {"value": str, "confidence": 0..1},
  "location": {"value": {"city": str|null, "state": str|null, "country": str|null}, "confidence": 0..1},
  "work_model": {"value": "remoto"|"hibrido"|"presencial"|"", "confidence": 0..1},
  "seniority": {"value": str, "confidence": 0..1},
  "manager_name": {"value": str, "confidence": 0..1},
  "manager_email": {"value": str, "confidence": 0..1},
  "contract_type": {"value": "clt"|"pj"|"estagio"|"temporario"|"freelancer"|"", "confidence": 0..1},
  "responsibilities": {"value": [str, ...], "confidence": 0..1},
  "technical_skills": {"value": [str, ...], "confidence": 0..1},
  "behavioral_skills": {"value": [str, ...], "confidence": 0..1},
  "languages": {"value": [str, ...], "confidence": 0..1},
  "salary": {"value": {"min": int|null, "max": int|null, "currency": "BRL"}, "confidence": 0..1},
  "benefits": {"value": [str, ...], "confidence": 0..1}
}

Regras:
- Use confidence ALTO (>=0.85) só quando o campo está LITERALMENTE no texto.
- Use confidence MÉDIO (0.6-0.84) quando inferiu razoavelmente.
- Use confidence BAIXO (<0.6) quando chutou — prefira deixar value vazio.
- Nunca invente nome de gestor, salário ou localização.
- NUNCA inclua dados pessoais identificáveis (CPF, email, telefone) — eles foram mascarados antes.
- Responda APENAS o JSON, sem markdown, sem explicação.
"""


class IntakeExtractor:
    """Service that converts free-text intake into a `JobIntakePayload`.

    Single canonical extractor — `intake_node` in `graph.py` is the only
    consumer. All compliance gates (PII mask + FairnessGuard pre-check)
    are applied here so callers don't have to repeat them.
    """

    def __init__(self, llm_client: Any = None) -> None:
        self._llm = llm_client

    # ---- LLM client (lazy) -------------------------------------------------
    def _get_llm(self) -> Any:
        """Resolve a Claude chat model for intake extraction.

        Canonical resolution order (canonical-fix Phase 4 — Task wizard
        audit 2026-05):
          1. Tenant-specific Claude key via
             ``app.shared.tenant_llm_context.get_claude_model_for_tenant``.
             (Previous code imported a non-existent
             ``app.shared.services.tenant_llm_context.get_llm_for_current_tenant``
             — the import always raised ``ModuleNotFoundError`` and the
             extractor silently fell back to the regex parser, which
             could not extract from short colloquial inputs like
             "desenvolvedor python senior". That cascaded into the
             input-thin guard always firing — see
             ``docs/architecture/wizard-flow.md`` §"Bugs históricos".)
          2. Global default ``ChatAnthropic`` from ``app.core.config``
             when the tenant has no custom key. This restores the
             original intent: intake LLM always available; regex is the
             final-resort fallback only when even the global model is
             unreachable.
        """
        if self._llm is not None:
            return self._llm
        try:
            from app.shared.tenant_llm_context import get_claude_model_for_tenant
            self._llm = get_claude_model_for_tenant()
        except Exception as exc:  # pragma: no cover — defensive
            logger.info("[IntakeExtractor] tenant LLM lookup failed: %s", exc)
            self._llm = None
        if self._llm is None:
            try:
                from app.core.config import settings
                from app.shared.providers.anthropic_client import get_chat_anthropic

                # Task #1166: route through the centralized helper so
                # the proxy ``base_url`` injection (Task #1164 Bug D) is
                # guaranteed and the AST sentinel can enforce a single
                # construction seam for the wizard domain.
                self._llm = get_chat_anthropic(
                    model=settings.LLM_PRIMARY_MODEL,
                    temperature=settings.LLM_DEFAULT_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                )
                logger.info(
                    "[IntakeExtractor] Using default global Claude model "
                    "(no tenant-specific key configured)"
                )
            except Exception as exc:
                logger.warning(
                    "[IntakeExtractor] Default Claude unavailable, will fall "
                    "back to regex extraction: %s",
                    exc,
                )
                self._llm = None
        return self._llm

    # ---- Public API --------------------------------------------------------
    def extract_from_sources(
        self,
        user_text: str = "",
        right_panel_form: Optional[Dict[str, Any]] = None,
        attached_file_text: str = "",
    ) -> JobIntakePayload:
        """Extract + merge intake from up to three sources.

        The right-panel form is treated as user-confirmed truth and wins
        ties with `source="right_panel_form"` (high confidence). Free
        text and attached-file text are passed through `extract()` and
        merged in priority order: form > user_text > attached_file. The
        returned payload exposes the dominant `source` per field so
        downstream stages can decide what to re-confirm.
        """
        # ----- F-100 telemetry (PR-13) -------------------------------------
        # Conta toda chamada e classifica se o dict opcional `right_panel_form`
        # chegou populado. "Populado" = pelo menos um valor não-vazio (None,
        # "", [], {} contam como vazio). Janela inicial: 48h em prod.
        _rpf_populated = bool(
            right_panel_form
            and any(v not in (None, "", [], {}) for v in right_panel_form.values())
        )
        if lia_right_panel_form_received_total is not None:
            try:
                lia_right_panel_form_received_total.labels(
                    populated="true" if _rpf_populated else "false",
                    stage="intake",
                ).inc()
            except Exception:  # pragma: no cover — telemetria nunca quebra hot path
                logger.debug(
                    "right_panel_form counter inc failed", exc_info=True
                )
        # Log INFO complementar (canary durante a janela 48h).
        logger.info(
            "[right_panel_form] received populated=%s fields=%s",
            _rpf_populated,
            sorted(right_panel_form.keys()) if (right_panel_form and _rpf_populated) else [],
        )
        # -------------------------------------------------------------------

        # 1) Form fields are authoritative — wrap each non-empty entry.
        form_payload = JobIntakePayload(raw_input="")
        if right_panel_form:
            for fname in form_payload.model_fields:
                if fname in {"overall_confidence", "raw_input",
                             "fairness_blocked", "fairness_message"}:
                    continue
                if fname in right_panel_form and right_panel_form[fname] not in (None, "", []):
                    setattr(form_payload, fname, IntakeField(
                        value=right_panel_form[fname],
                        confidence=0.95,
                        source="right_panel_form",
                    ))

        # 2) Run extract on each text source (user_text first → priority).
        text_payload = self.extract(user_text) if user_text and user_text.strip() else None
        file_payload = self.extract(attached_file_text) if attached_file_text and attached_file_text.strip() else None

        # Tag the source for fields populated from each text payload so
        # the merger can preserve provenance instead of squashing to
        # `llm`/`regex`.
        def _retag(p: Optional[JobIntakePayload], src: FieldSource) -> Optional[JobIntakePayload]:
            if p is None:
                return None
            for fname in p.model_fields:
                f = getattr(p, fname, None)
                if isinstance(f, IntakeField) and f.confidence > 0:
                    f.source = src
            return p

        text_payload = _retag(text_payload, "user_text")
        file_payload = _retag(file_payload, "attached_file")

        # 3) Merge in priority order. For each field, the first source
        # with a filled value wins; ties are broken by confidence.
        merged = JobIntakePayload(raw_input=user_text or "")
        for fname in merged.model_fields:
            if fname in {"overall_confidence", "raw_input",
                         "fairness_blocked", "fairness_message"}:
                continue
            for candidate in (form_payload, text_payload, file_payload):
                if candidate is None:
                    continue
                cand_field = getattr(candidate, fname, None)
                if isinstance(cand_field, IntakeField) and candidate.field_is_filled(fname, min_confidence=0.0):
                    cur = getattr(merged, fname)
                    if not isinstance(cur, IntakeField) or cur.confidence < cand_field.confidence:
                        setattr(merged, fname, cand_field)

        # 4) Propagate fairness signal from any source.
        for p in (form_payload, text_payload, file_payload):
            if p is not None and p.fairness_blocked:
                merged.fairness_blocked = True
                merged.fairness_message = p.fairness_message
                break

        # 5) Recompute overall confidence as mean of filled fields.
        confidences = [
            getattr(merged, f).confidence
            for f in merged.model_fields
            if isinstance(getattr(merged, f, None), IntakeField)
            and getattr(merged, f).confidence > 0
        ]
        merged.overall_confidence = (
            round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        )
        return merged

    def extract(self, raw_input: str) -> JobIntakePayload:
        """Extract a structured payload from the recruiter's free text.

        Pipeline:
          1. FairnessGuard pre-check — block early if input is biased.
          2. PII mask — strip CPF/email/phone before any LLM call.
          3. LLM structured extraction (JSON-only).
          4. Regex fallback if the LLM is unavailable or output is invalid.
        """
        if not raw_input or not raw_input.strip():
            return JobIntakePayload(raw_input=raw_input or "", overall_confidence=0.0)

        # 1) FairnessGuard pre-check
        check = check_input_fairness(raw_input)
        if check.is_blocked:
            logger.warning(
                "[IntakeExtractor] FairnessGuard blocked input | category=%s terms=%s",
                check.category, check.blocked_terms,
            )
            return JobIntakePayload(
                raw_input=raw_input,
                fairness_blocked=True,
                fairness_message=(
                    check.educational_message
                    or "Sua descrição contém termos potencialmente discriminatórios."
                ),
                overall_confidence=0.0,
            )

        # 2) PII mask
        masked = mask_pii_for_llm(raw_input)

        # 3) LLM extraction
        payload = self._llm_extract(masked, raw_input)
        if payload is not None:
            return payload

        # 4) Regex fallback
        logger.info("[IntakeExtractor] Falling back to regex extraction")
        return _regex_extract(raw_input)

    # ---- Internals ---------------------------------------------------------
    def _llm_extract(self, masked_input: str, raw_input: str) -> Optional[JobIntakePayload]:
        llm = self._get_llm()
        if llm is None:
            return None

        try:
            response = self._invoke_llm(llm, masked_input)
        except Exception as exc:
            logger.warning("[IntakeExtractor] LLM call failed: %s", exc)
            return None

        if not response:
            return None

        text = response.strip()
        # Strip markdown fences if any
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("[IntakeExtractor] LLM returned non-JSON: %s", exc)
            return None

        # Wrap into IntakeField shape if the LLM returned a flat structure
        for key, val in list(data.items()):
            if isinstance(val, dict) and "value" in val and "confidence" in val:
                val.setdefault("source", "llm")
            else:
                # Flat field — wrap it
                data[key] = {"value": val, "confidence": 0.7, "source": "llm"}

        try:
            payload = JobIntakePayload(raw_input=raw_input, **data)
        except ValidationError as exc:
            logger.warning("[IntakeExtractor] Schema validation failed: %s", exc)
            return None

        # Aggregate confidence dynamically over every `IntakeField` on
        # the payload. Iterating model_fields avoids drifting away from
        # the schema again — adding a new field to JobIntakePayload (e.g.
        # `manager_email`) is automatically picked up here without
        # touching this function.
        confidences = [
            getattr(payload, fname).confidence
            for fname in payload.model_fields
            if isinstance(getattr(payload, fname, None), IntakeField)
            and getattr(payload, fname).confidence > 0
        ]
        payload.overall_confidence = (
            round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        )
        return payload

    def _invoke_llm(self, llm: Any, masked_input: str) -> str:
        """Invoke the LLM. Supports common interfaces (langchain BaseChatModel
        with .invoke, anthropic-style .messages.create, or a callable).
        """
        prompt_user = f"Texto do recrutador:\n{masked_input}"

        # langchain-style ChatModel
        if hasattr(llm, "invoke"):
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                msg = llm.invoke([
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=prompt_user),
                ])
                return getattr(msg, "content", str(msg))
            except Exception:
                pass

        # Anthropic-style client
        if hasattr(llm, "messages") and hasattr(llm.messages, "create"):
            resp = llm.messages.create(
                model=getattr(llm, "model", CANONICAL_HAIKU_MODEL),
                max_tokens=1024,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt_user}],
            )
            blocks = getattr(resp, "content", [])
            return "".join(getattr(b, "text", "") for b in blocks)

        # Plain callable
        if callable(llm):
            return llm(_SYSTEM_PROMPT + "\n\n" + prompt_user)

        raise RuntimeError("Unknown LLM client interface")


# Singleton accessor (matches scheduler/graph patterns)
_singleton: Optional[IntakeExtractor] = None


def get_intake_extractor() -> IntakeExtractor:
    global _singleton
    if _singleton is None:
        _singleton = IntakeExtractor()
    return _singleton
