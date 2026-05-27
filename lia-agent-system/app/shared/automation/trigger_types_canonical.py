"""trigger_types_canonical.py — Sprint Z.4 canonical single source.

Antes (audit findings): 4 enums divergentes em 5 arquivos com 10/10/14/17/9 valores.
Agora: 1 enum canonical (TriggerType) + 1 lista de metadata (TRIGGER_TYPE_CATALOG)
+ helpers (get_trigger_metadata, list_all_triggers, to_api_response).

Convergencia:
- app/api/v1/automations.py.get_trigger_types() devolve este catalog (Z.4)
- app/domains/automation/services/stage_automation_engine.py (TriggerType local — DEPRECATED, sera removido Sprint Z.5)
- app/domains/automation/services/automation_trigger_service.py (TriggerType local — DEPRECATED, sera removido Sprint Z.6)
- libs/models/lia_models/automation.py (TriggerType — DEPRECATED para uso novo; backward compat preservado para coluna DB)
- frontend useTriggerTypes() consome via endpoint
- SentenceBuilder hidratado com este shape

Backward-compat: TODOS os values aqui sao strings ja em uso em DB rows existentes
e codigo. Nenhum value foi renomeado. Sprint Z.4 NAO migra dados; consolida API/enum surface.

Audit ref: AUTOMATIONS_BACKEND_AUDIT.md (P1: 4 enums) +
AUTOMATIONS_SPRINT_PLAN_ADR.md Sprint Z.4
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TriggerType(str, Enum):
    """Canonical trigger types — single source of truth.

    Convencao: snake_case. Ordem por categoria.

    Cobre a UNIAO dos 4 enums concorrentes pre-Sprint-Z.4:
    - libs/models/lia_models/automation.py (10 vals, DB-bound)
    - app/domains/automation/services/stage_automation_engine.py (17 vals)
    - app/domains/automation/services/automation_trigger_service.py (9 vals, time-based)
    - app/api/v1/automations.py (10 vals expostos, subset de lib)
    """
    # ── Lifecycle de aplicacao ──
    CANDIDATE_APPLIED = "candidate_applied"

    # ── Movimentacao no pipeline ──
    # NOTE: 'candidate_stage_changed' é o canonical value (lib DB enum legacy);
    # stage_automation_engine usa 'stage_changed' como alias local que sera deprecado em Z.5.
    CANDIDATE_STAGE_CHANGED = "candidate_stage_changed"
    CANDIDATE_INACTIVE = "candidate_inactive"
    CANDIDATE_NO_SHOW = "candidate_no_show"

    # ── IA scoring / triagem ──
    SCREENING_COMPLETED = "screening_completed"

    # ── Entrevista ──
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    INTERVIEW_REMINDER_24H = "interview_reminder_24h"

    # ── Comunicacao / engajamento ──
    NO_RESPONSE_48H = "no_response_48h"
    CANDIDATE_NO_CONTACT_48H = "candidate_no_contact_48h"
    FEEDBACK_RECEIVED = "feedback_received"
    FEEDBACK_PENDING_48H = "feedback_pending_48h"
    SCORECARD_PENDING_24H = "scorecard_pending_24h"
    CANDIDATE_LINKEDIN_UPDATE = "candidate_linkedin_update"
    CANDIDATE_BIRTHDAY = "candidate_birthday"

    # ── Outcome do candidato ──
    CANDIDATE_REJECTED = "candidate_rejected"
    CANDIDATE_HIRED = "candidate_hired"

    # ── Oferta ──
    OFFER_SENT = "offer_sent"
    OFFER_ACCEPTED = "offer_accepted"

    # ── Vaga ──
    JOB_PUBLISHED = "job_published"
    JOB_NO_MOVEMENT_5D = "job_no_movement_5d"
    DEADLINE_APPROACHING = "deadline_approaching"
    JOB_DEADLINE_APPROACHING = "job_deadline_approaching"
    CANDIDATES_SOURCED = "candidates_sourced"
    SLOT_OPENED = "slot_opened"

    # ── Externo / sistema ──
    ATS_SYNC = "ats_sync"


# ─────────────────────────────────────────────────────────────────────────────
# Metadata catalog
# ─────────────────────────────────────────────────────────────────────────────

CANONICAL_CATEGORIES = frozenset({
    "lifecycle",
    "pipeline",
    "scoring",
    "interview",
    "communication",
    "outcome",
    "offer",
    "job",
    "external",
})


@dataclass(frozen=True)
class ParamDef:
    name: str
    label: str
    type: str  # "string" | "number" | "select" | "stage_id"
    required: bool = True
    options: tuple[tuple[str, str], ...] | None = None  # immutable; pra type="select"


@dataclass(frozen=True)
class TriggerMetadata:
    value: TriggerType
    label_pt: str  # PT-BR label canonical (UI consumer)
    label_en: str
    description: str
    category: str  # ver CANONICAL_CATEGORIES
    params: tuple[ParamDef, ...] = field(default_factory=tuple)


TRIGGER_TYPE_CATALOG: tuple[TriggerMetadata, ...] = (
    # ── Lifecycle ──
    TriggerMetadata(
        value=TriggerType.CANDIDATE_APPLIED,
        label_pt="Candidato se candidatou",
        label_en="Candidate applied",
        description="Dispara quando um candidato se candidata a uma vaga.",
        category="lifecycle",
    ),

    # ── Pipeline ──
    TriggerMetadata(
        value=TriggerType.CANDIDATE_STAGE_CHANGED,
        label_pt="Candidato mudou de etapa",
        label_en="Candidate stage changed",
        description="Dispara quando um candidato muda de etapa no processo seletivo.",
        category="pipeline",
        params=(
            ParamDef(name="stage_id", label="Etapa destino", type="stage_id", required=False),
        ),
    ),
    TriggerMetadata(
        value=TriggerType.CANDIDATE_INACTIVE,
        label_pt="Candidato inativo",
        label_en="Candidate inactive",
        description="Candidato sem movimentacao no pipeline.",
        category="pipeline",
        params=(
            ParamDef(name="days_threshold", label="Dias", type="number", required=False),
        ),
    ),
    TriggerMetadata(
        value=TriggerType.CANDIDATE_NO_SHOW,
        label_pt="Candidato nao compareceu",
        label_en="Candidate no-show",
        description="Candidato faltou a etapa marcada (entrevista, dinamica, etc).",
        category="pipeline",
    ),

    # ── Scoring ──
    TriggerMetadata(
        value=TriggerType.SCREENING_COMPLETED,
        label_pt="Triagem concluida",
        label_en="Screening completed",
        description="Dispara quando a triagem do candidato (WSI/BigFive) é concluida.",
        category="scoring",
    ),

    # ── Interview ──
    TriggerMetadata(
        value=TriggerType.INTERVIEW_SCHEDULED,
        label_pt="Entrevista agendada",
        label_en="Interview scheduled",
        description="Dispara quando uma entrevista é agendada.",
        category="interview",
    ),
    TriggerMetadata(
        value=TriggerType.INTERVIEW_COMPLETED,
        label_pt="Entrevista concluida",
        label_en="Interview completed",
        description="Dispara apos entrevista realizada.",
        category="interview",
    ),
    TriggerMetadata(
        value=TriggerType.INTERVIEW_REMINDER_24H,
        label_pt="Lembrete de entrevista 24h antes",
        label_en="Interview reminder 24h",
        description="Lembrete proativo 24h antes da entrevista marcada.",
        category="interview",
    ),

    # ── Communication ──
    TriggerMetadata(
        value=TriggerType.NO_RESPONSE_48H,
        label_pt="Sem resposta há 48h",
        label_en="No response in 48h",
        description="Candidato sem resposta a contato por 48h.",
        category="communication",
    ),
    TriggerMetadata(
        value=TriggerType.CANDIDATE_NO_CONTACT_48H,
        label_pt="Candidato sem contato há 48h",
        label_en="Candidate no contact 48h",
        description="Proativo: recrutador nao tentou contato em 48h.",
        category="communication",
    ),
    TriggerMetadata(
        value=TriggerType.FEEDBACK_RECEIVED,
        label_pt="Feedback recebido",
        label_en="Feedback received",
        description="Feedback de entrevista/gestor foi registrado.",
        category="communication",
    ),
    TriggerMetadata(
        value=TriggerType.FEEDBACK_PENDING_48H,
        label_pt="Feedback pendente há 48h",
        label_en="Feedback pending 48h",
        description="Gestor/entrevistador ainda nao deu feedback ha 48h.",
        category="communication",
    ),
    TriggerMetadata(
        value=TriggerType.SCORECARD_PENDING_24H,
        label_pt="Scorecard pendente há 24h",
        label_en="Scorecard pending 24h",
        description="Scorecard de entrevista nao preenchido em 24h.",
        category="communication",
    ),
    TriggerMetadata(
        value=TriggerType.CANDIDATE_LINKEDIN_UPDATE,
        label_pt="Candidato atualizou LinkedIn",
        label_en="Candidate updated LinkedIn",
        description="Sinal de engajamento: candidato modificou perfil publico.",
        category="communication",
    ),
    TriggerMetadata(
        value=TriggerType.CANDIDATE_BIRTHDAY,
        label_pt="Aniversario do candidato",
        label_en="Candidate birthday",
        description="Trigger de relacionamento (talent pool).",
        category="communication",
    ),

    # ── Outcome ──
    TriggerMetadata(
        value=TriggerType.CANDIDATE_REJECTED,
        label_pt="Candidato rejeitado",
        label_en="Candidate rejected",
        description="Dispara quando um candidato é rejeitado.",
        category="outcome",
    ),
    TriggerMetadata(
        value=TriggerType.CANDIDATE_HIRED,
        label_pt="Candidato contratado",
        label_en="Candidate hired",
        description="Dispara quando um candidato é contratado.",
        category="outcome",
    ),

    # ── Offer ──
    TriggerMetadata(
        value=TriggerType.OFFER_SENT,
        label_pt="Proposta enviada",
        label_en="Offer sent",
        description="Dispara quando uma proposta é enviada ao candidato.",
        category="offer",
    ),
    TriggerMetadata(
        value=TriggerType.OFFER_ACCEPTED,
        label_pt="Proposta aceita",
        label_en="Offer accepted",
        description="Candidato confirmou aceite da proposta.",
        category="offer",
    ),

    # ── Job ──
    TriggerMetadata(
        value=TriggerType.JOB_PUBLISHED,
        label_pt="Vaga publicada",
        label_en="Job published",
        description="Dispara quando uma vaga vai ao ar.",
        category="job",
    ),
    TriggerMetadata(
        value=TriggerType.JOB_NO_MOVEMENT_5D,
        label_pt="Vaga sem movimentacao há 5 dias",
        label_en="Job no movement 5d",
        description="Vaga sem candidatos novos ou movimentacao em 5 dias.",
        category="job",
    ),
    TriggerMetadata(
        value=TriggerType.DEADLINE_APPROACHING,
        label_pt="Prazo se aproximando",
        label_en="Deadline approaching",
        description="Dispara quando o prazo de uma vaga está se aproximando.",
        category="job",
    ),
    TriggerMetadata(
        value=TriggerType.JOB_DEADLINE_APPROACHING,
        label_pt="Prazo da vaga proximo (proativo)",
        label_en="Job deadline approaching (proactive)",
        description="Versao proativa do alerta de prazo (cron-driven).",
        category="job",
    ),
    TriggerMetadata(
        value=TriggerType.CANDIDATES_SOURCED,
        label_pt="Candidatos prospectados",
        label_en="Candidates sourced",
        description="Apos lote de sourcing automatico/manual entregar candidatos.",
        category="job",
    ),
    TriggerMetadata(
        value=TriggerType.SLOT_OPENED,
        label_pt="Slot de entrevista aberto",
        label_en="Interview slot opened",
        description="Quando agenda disponibiliza horario novo de entrevista.",
        category="job",
    ),

    # ── External ──
    TriggerMetadata(
        value=TriggerType.ATS_SYNC,
        label_pt="Sincronizacao com ATS",
        label_en="ATS sync",
        description="Evento externo de sincronizacao com ATS.",
        category="external",
    ),
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers (public API)
# ─────────────────────────────────────────────────────────────────────────────


def get_trigger_metadata(value: str | TriggerType) -> TriggerMetadata | None:
    """Lookup canonical por value. Fail-CLOSED (returns None se desconhecido).

    Aceita string OU enum.
    """
    target = value.value if isinstance(value, TriggerType) else value
    for meta in TRIGGER_TYPE_CATALOG:
        if meta.value.value == target:
            return meta
    return None


def list_all_triggers() -> list[TriggerMetadata]:
    """Returns canonical catalog (defensive copy, tuple internals immutable)."""
    return list(TRIGGER_TYPE_CATALOG)


def to_api_response() -> list[dict]:
    """Shape canonical pra endpoint GET /trigger-types/available.

    Format: {value, name (label_pt), label_pt, label_en, description, category, params}.
    Aligns com backend automations.py:get_trigger_types existente (campos value/name/description preservados).
    """
    out: list[dict] = []
    for meta in TRIGGER_TYPE_CATALOG:
        params_list = []
        for p in meta.params:
            params_list.append({
                "name": p.name,
                "label": p.label,
                "type": p.type,
                "required": p.required,
                "options": (
                    [{"value": v, "label": lbl} for v, lbl in p.options]
                    if p.options
                    else None
                ),
            })
        out.append({
            "value": meta.value.value,
            "name": meta.label_pt,  # backward-compat: API "name" = label_pt
            "label_pt": meta.label_pt,
            "label_en": meta.label_en,
            "description": meta.description,
            "category": meta.category,
            "params": params_list,
        })
    return out
