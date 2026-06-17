"""
WSI Interview Graph - State machine para entrevistas WSI síncronas.

Implementa fluxo previsível e auditável para sessões de entrevista
comportamental/técnica baseadas na metodologia WSI da WeDOTalent.

Por que Graph (não ReAct)?
- Fluxo sequencial determinístico: pergunta 1 → 2 → N → resultado
- Cada etapa deve ser rastreável individualmente (compliance BCB 498, SOX)
- Sem decisão autônoma — transições baseadas em regras explícitas
- Auditável: log completo de cada nó para FairnessGuard e Bias Audit

Conforme recomendação arquitetural: fluxos previsíveis = Graph,
fluxos com raciocínio autônomo = ReAct.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import uuid4

try:
    from langsmith import traceable as _traceable
except ImportError:
    def _traceable(**kwargs):  # type: ignore[misc]
        def decorator(fn):
            return fn
        return decorator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class WSIInterviewStage(StrEnum):
    INIT = "init"
    LOAD_CONTEXT = "load_context"
    GENERATE_QUESTION = "generate_question"
    AWAIT_RESPONSE = "await_response"
    VALIDATE_RESPONSE = "validate_response"
    SCORE_RESPONSE = "score_response"
    ADVANCE = "advance"
    GENERATE_FEEDBACK = "generate_feedback"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class WSIQuestionBlock:
    block_id: str
    block_type: str  # "technical" | "behavioral" | "situational"
    question: str
    competency: str
    bloom_level: int  # 1-6
    dreyfus_level: int  # 1-5
    big_five_trait: str | None = None
    max_score: float = 10.0
    # F9-1 — peso normalizado do trait F3 (score_final / soma_scores_traits).
    # Padrão 1.0 = pesos uniformes quando dados F3 indisponíveis (perguntas do DB sem ranking OCEAN).
    trait_weight: float = 1.0


@dataclass
class WSIResponseRecord:
    question_block: WSIQuestionBlock
    candidate_response: str
    score: float = 0.0
    bloom_achieved: int = 0
    dreyfus_achieved: int = 0
    reasoning: str = ""
    scored_at: datetime | None = None


@dataclass
class WSIInterviewState:
    session_id: str
    company_id: str
    candidate_id: str
    job_id: str
    interview_level: str = "standard"  # "quick" | "standard" | "full"

    # Contexto carregado no LOAD_CONTEXT
    job_requirements: dict[str, Any] = field(default_factory=dict)
    candidate_profile: dict[str, Any] = field(default_factory=dict)

    # Banco de perguntas para esta sessão
    question_blocks: list[WSIQuestionBlock] = field(default_factory=list)
    current_question_index: int = 0

    # Respostas coletadas
    responses: list[WSIResponseRecord] = field(default_factory=list)

    # Pergunta atual em exibição
    current_question: WSIQuestionBlock | None = None
    awaiting_response: bool = False

    # Scores parciais por dimensão
    technical_score: float = 0.0
    behavioral_score: float = 0.0
    situational_score: float = 0.0
    eligibility_score: float = 0.0
    # Contadores para acumulação ponderada correta (spec F8 — média simples por bloco)
    technical_score_count: int = 0
    behavioral_score_count: int = 0

    # Score final
    wsi_final_score: float | None = None
    recommendation: str = ""  # "aprovado" | "aguardando" | "reprovado"

    # Auditoria
    stage: WSIInterviewStage = WSIInterviewStage.INIT
    execution_log: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    error: str | None = None

    def log_step(self, node: str, details: dict[str, Any]) -> None:
        self.execution_log.append({
            "node": node,
            "timestamp": datetime.utcnow().isoformat(),
            "question_index": self.current_question_index,
            **details,
        })

    @property
    def is_complete(self) -> bool:
        return self.stage in (WSIInterviewStage.COMPLETE, WSIInterviewStage.ERROR)

    @property
    def questions_remaining(self) -> int:
        return max(0, len(self.question_blocks) - self.current_question_index)

    @property
    def progress_pct(self) -> float:
        if not self.question_blocks:
            return 0.0
        return (self.current_question_index / len(self.question_blocks)) * 100


# ---------------------------------------------------------------------------
# LangGraph TypedDict envelope (PostgresSaver requires JSON-serializable state)
# ---------------------------------------------------------------------------

try:
    from typing import TypedDict as _WSITDBase

    class _WSILangGraphState(_WSITDBase, total=False):
        wsi_data: dict        # serialized WSIInterviewState
        pending_response: str  # candidate's latest response (set before submit)
        operation: str        # "start" | "submit"

    _HAS_WSI_TYPED_DICT = True
except Exception:
    _HAS_WSI_TYPED_DICT = False
    _WSILangGraphState = dict  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Serialization helpers (WSIInterviewState ↔ JSON-compatible dict)
# ---------------------------------------------------------------------------

def _wsi_state_to_dict(state: "WSIInterviewState") -> dict:
    """Serializa WSIInterviewState → dict JSON-compatível para PostgresSaver."""
    def _block_d(b: "WSIQuestionBlock") -> dict:
        return {
            "block_id": b.block_id,
            "block_type": b.block_type,
            "question": b.question,
            "competency": b.competency,
            "bloom_level": b.bloom_level,
            "dreyfus_level": b.dreyfus_level,
            "big_five_trait": b.big_five_trait,
            "max_score": b.max_score,
            "trait_weight": b.trait_weight,
        }

    return {
        "session_id": state.session_id,
        "company_id": state.company_id,
        "candidate_id": state.candidate_id,
        "job_id": state.job_id,
        "interview_level": state.interview_level,
        "job_requirements": state.job_requirements,
        "candidate_profile": state.candidate_profile,
        "question_blocks": [_block_d(q) for q in state.question_blocks],
        "current_question_index": state.current_question_index,
        "responses": [
            {
                "question_block": _block_d(r.question_block),
                "candidate_response": r.candidate_response,
                "score": r.score,
                "bloom_achieved": r.bloom_achieved,
                "dreyfus_achieved": r.dreyfus_achieved,
                "reasoning": r.reasoning,
                "scored_at": r.scored_at.isoformat() if r.scored_at else None,
            }
            for r in state.responses
        ],
        "current_question": _block_d(state.current_question) if state.current_question else None,
        "awaiting_response": state.awaiting_response,
        "technical_score": state.technical_score,
        "behavioral_score": state.behavioral_score,
        "situational_score": state.situational_score,
        "eligibility_score": state.eligibility_score,
        "technical_score_count": state.technical_score_count,
        "behavioral_score_count": state.behavioral_score_count,
        "wsi_final_score": state.wsi_final_score,
        "recommendation": state.recommendation,
        "stage": state.stage.value,
        "execution_log": state.execution_log,
        "started_at": state.started_at.isoformat(),
        "completed_at": state.completed_at.isoformat() if state.completed_at else None,
        "error": state.error,
    }


def _wsi_state_from_dict(d: dict) -> "WSIInterviewState":
    """Desserializa dict → WSIInterviewState."""
    def _block(b: dict) -> "WSIQuestionBlock":
        return WSIQuestionBlock(
            block_id=b["block_id"],
            block_type=b["block_type"],
            question=b["question"],
            competency=b["competency"],
            bloom_level=b["bloom_level"],
            dreyfus_level=b["dreyfus_level"],
            big_five_trait=b.get("big_five_trait"),
            max_score=b.get("max_score", 10.0),
            trait_weight=float(b.get("trait_weight", 1.0)),
        )

    state = WSIInterviewState(
        session_id=d["session_id"],
        company_id=d["company_id"],
        candidate_id=d["candidate_id"],
        job_id=d["job_id"],
        interview_level=d.get("interview_level", "standard"),
        job_requirements=d.get("job_requirements", {}),
        candidate_profile=d.get("candidate_profile", {}),
        question_blocks=[_block(q) for q in d.get("question_blocks", [])],
        current_question_index=d.get("current_question_index", 0),
        awaiting_response=d.get("awaiting_response", False),
        technical_score=d.get("technical_score", 0.0),
        behavioral_score=d.get("behavioral_score", 0.0),
        situational_score=d.get("situational_score", 0.0),
        eligibility_score=d.get("eligibility_score", 0.0),
        technical_score_count=d.get("technical_score_count", 0),
        behavioral_score_count=d.get("behavioral_score_count", 0),
        wsi_final_score=d.get("wsi_final_score"),
        recommendation=d.get("recommendation", ""),
        stage=WSIInterviewStage(d.get("stage", "init")),
        execution_log=d.get("execution_log", []),
        error=d.get("error"),
    )
    if d.get("started_at"):
        try:
            state.started_at = datetime.fromisoformat(d["started_at"])
        except Exception:
            pass
    if d.get("completed_at"):
        try:
            state.completed_at = datetime.fromisoformat(d["completed_at"])
        except Exception:
            pass
    state.current_question = _block(d["current_question"]) if d.get("current_question") else None
    state.responses = [
        WSIResponseRecord(
            question_block=_block(r["question_block"]),
            candidate_response=r["candidate_response"],
            score=r.get("score", 0.0),
            bloom_achieved=r.get("bloom_achieved", 0),
            dreyfus_achieved=r.get("dreyfus_achieved", 0),
            reasoning=r.get("reasoning", ""),
            scored_at=datetime.fromisoformat(r["scored_at"]) if r.get("scored_at") else None,
        )
        for r in d.get("responses", [])
    ]
    return state


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

class WSIInterviewNodes:
    """Nós de processamento do grafo de entrevista WSI."""

    async def load_context(self, state: WSIInterviewState) -> WSIInterviewState:
        """Carrega banco de perguntas WSI para a sessão.

        Tenta gerar perguntas via WSIScreeningPipeline usando `job_requirements`
        e `candidate_profile` pré-carregados pelo endpoint (que tem acesso ao DB).
        Se não houver dados pré-carregados, usa perguntas de fallback.

        Padrão de design: o grafo recebe contexto do endpoint (camada com DB),
        não acessa o DB diretamente — mantém desacoplamento e testabilidade.
        """
        state.stage = WSIInterviewStage.LOAD_CONTEXT

        # SEG-4: Gate 1 — verificação de consentimento LGPD antes de iniciar entrevista WSI
        if state.candidate_id and state.company_id:
            try:
                from app.core.database import AsyncSessionLocal
                from app.services.consent_checker_service import ConsentCheckerService
                async with AsyncSessionLocal() as _db:
                    _consent_svc = ConsentCheckerService(_db)
                    _consent = await _consent_svc.check_candidate_consent(
                        candidate_id=state.candidate_id,
                        company_id=state.company_id,
                        purpose="ai_screening",
                    )
                if not _consent.allowed:
                    logger.warning(
                        "[WSIInterviewGraph][SEG-4] Consentimento revogado — abortando WSI "
                        "candidate=%s reason=%s",
                        state.candidate_id, _consent.reason,
                    )
                    state.error = "LGPD_CONSENT_REVOKED"
                    state.stage = WSIInterviewStage.ERROR
                    state.log_step("load_context", {
                        "status": "consent_revoked",
                        "reason": _consent.reason,
                    })
                    return state
                if getattr(_consent, "soft_warning", False):
                    logger.info(
                        "[WSIInterviewGraph][SEG-4] Consentimento ausente (soft warning) — "
                        "prosseguindo candidate=%s",
                        state.candidate_id,
                    )
            except Exception as _consent_exc:
                logger.warning(
                    "[WSIInterviewGraph][SEG-4] Consent check falhou — prosseguindo: %s",
                    _consent_exc,
                )

        try:
            question_source = "unknown"

            # FONTE ÚNICA DE VERDADE: perguntas salvas pelo recrutador em Configurações da Vaga.
            # Lê de job_screening_questions antes de qualquer geração on-the-fly.
            if state.job_id:
                try:
                    from sqlalchemy import text as _sql_text

                    from app.core.database import AsyncSessionLocal
                    async with AsyncSessionLocal() as _db:
                        rows = (await _db.execute(
                            _sql_text(
                                "SELECT id, question_text, category, question_type, weight, "
                                "skill_targeted, block_id "
                                "FROM job_screening_questions "
                                "WHERE job_vacancy_id = :job_id AND is_active = true "
                                "ORDER BY created_at ASC"
                            ),
                            {"job_id": state.job_id},
                        )).fetchall()

                    if rows:
                        state.question_blocks = [
                            WSIQuestionBlock(
                                block_id=str(row[0]),
                                block_type=(
                                    "technical"
                                    if (row[3] or row[2] or "").lower() in ("technical", "tecnico", "tech")
                                    else "behavioral"
                                ),
                                question=row[1],
                                competency=row[5] or "",
                                bloom_level=3,
                                dreyfus_level=3,
                                big_five_trait=None,
                                max_score=float(row[4] or 1.0) * 10 if float(row[4] or 1.0) <= 1.0 else float(row[4] or 10.0),
                            )
                            for row in rows
                        ]
                        question_source = "saved_db"
                        logger.info(
                            "[WSIInterviewGraph] Loaded %d saved questions from DB for job_id=%s",
                            len(state.question_blocks), state.job_id,
                        )
                except Exception as db_exc:
                    logger.warning(
                        "[WSIInterviewGraph] Could not load saved questions from DB: %s — will attempt pipeline fallback",
                        db_exc,
                    )

            # FALLBACK: recrutador ainda não configurou perguntas — gera via pipeline com aviso.
            if not state.question_blocks:
                logger.warning(
                    "[WSIInterviewGraph] AVISO: nenhuma pergunta salva encontrada para job_id=%s. "
                    "Usando pipeline como fallback — o recrutador deve configurar perguntas em "
                    "Configurações da Vaga > Perguntas de Triagem.",
                    state.job_id,
                )
                if state.job_requirements and state.candidate_profile:
                    from app.domains.cv_screening.services.wsi_screening_pipeline import (
                        WSIScreeningPipeline,
                        WSIScreeningPipelineRequest,
                    )
                    req = WSIScreeningPipelineRequest(
                        job_title=state.job_requirements.get("title", ""),
                        job_description=state.job_requirements.get("description", ""),
                        seniority=state.job_requirements.get("seniority"),
                        company_id=state.company_id,
                        include_company_questions=False,
                    )
                    pipeline = WSIScreeningPipeline()
                    result = await pipeline.build_pipeline(req, [])
                    state.question_blocks = [
                        WSIQuestionBlock(
                            block_id=q.get("id", str(uuid4())),
                            block_type=q.get("block_type", "technical"),
                            question=q["question"],
                            competency=q.get("competency", ""),
                            bloom_level=q.get("bloom_level", 3),
                            dreyfus_level=q.get("dreyfus_level", 3),
                            big_five_trait=q.get("big_five_trait"),
                            max_score=q.get("max_score", 10.0),
                        )
                        for q in (result.questions if hasattr(result, "questions") else [])
                    ]
                    question_source = "fallback_pipeline"

            if not state.question_blocks:
                state.question_blocks = self._build_fallback_questions()
                question_source = "hardcoded_fallback"

            state.log_step("load_context", {
                "status": "success",
                "questions_loaded": len(state.question_blocks),
                "interview_level": state.interview_level,
                "source": question_source,
            })
            logger.info(
                "[WSIInterviewGraph] Context loaded: session=%s questions=%d source=%s",
                state.session_id, len(state.question_blocks), question_source,
            )

        except Exception as exc:
            logger.error(f"[WSIInterviewGraph] load_context failed: {exc}", exc_info=True)
            state.log_step("load_context", {"status": "error", "error": str(exc)})
            state.question_blocks = self._build_fallback_questions()

        return state

    async def generate_question(self, state: WSIInterviewState) -> WSIInterviewState:
        """Apresenta a próxima pergunta ao candidato."""
        state.stage = WSIInterviewStage.GENERATE_QUESTION

        if state.current_question_index >= len(state.question_blocks):
            # Todas as perguntas respondidas — vai para feedback
            state.stage = WSIInterviewStage.GENERATE_FEEDBACK
            state.log_step("generate_question", {"status": "all_questions_done"})
            return state

        block = state.question_blocks[state.current_question_index]
        state.current_question = block
        state.awaiting_response = True

        state.log_step("generate_question", {
            "status": "question_presented",
            "block_id": block.block_id,
            "block_type": block.block_type,
            "bloom_level": block.bloom_level,
            "dreyfus_level": block.dreyfus_level,
        })

        return state

    async def validate_response(
        self, state: WSIInterviewState, candidate_response: str
    ) -> WSIInterviewState:
        """Valida se a resposta é válida (não vazia, não timeout, não skip)."""
        state.stage = WSIInterviewStage.VALIDATE_RESPONSE
        state.awaiting_response = False

        response_clean = (candidate_response or "").strip()
        is_skip = response_clean.lower() in ("skip", "pular", "próxima", "proxima", "")
        is_valid = bool(response_clean) and not is_skip

        state.log_step("validate_response", {
            "status": "valid" if is_valid else "skipped",
            "response_length": len(response_clean),
            "is_skip": is_skip,
        })

        if not is_valid:
            # Resposta inválida/skip: registra com score 0 e avança
            if state.current_question:
                state.responses.append(WSIResponseRecord(
                    question_block=state.current_question,
                    candidate_response="[sem resposta]",
                    score=0.0,
                    reasoning="Candidato não respondeu ou pulou a pergunta.",
                    scored_at=datetime.utcnow(),
                ))
            state.current_question_index += 1
            state.stage = WSIInterviewStage.ADVANCE
        else:
            # SEG-1: verificação de injeção de prompt na resposta do candidato
            try:
                from app.shared.prompt_injection import PromptInjectionGuard
                _inj_guard = PromptInjectionGuard()
                _inj_result = _inj_guard.check(response_clean)
                if _inj_result.risk_level == "high":
                    logger.warning(
                        "[WSIInterviewGraph][SEG-1] Injeção de prompt bloqueada session=%s "
                        "patterns=%s",
                        state.session_id, _inj_result.matched_patterns,
                    )
                    state.log_step("validate_response", {
                        "status": "injection_blocked",
                        "patterns": _inj_result.matched_patterns,
                    })
                    # Trata como resposta inválida para não comprometer o scoring
                    if state.current_question:
                        state.responses.append(WSIResponseRecord(
                            question_block=state.current_question,
                            candidate_response="[resposta bloqueada por segurança]",
                            score=0.0,
                            reasoning="Resposta bloqueada pelo PromptInjectionGuard.",
                            scored_at=datetime.utcnow(),
                        ))
                    state.current_question_index += 1
                    state.stage = WSIInterviewStage.ADVANCE
                    return state
            except Exception as _inj_exc:
                logger.debug("[WSIInterviewGraph] PromptInjectionGuard check skipped: %s", _inj_exc)

            # A3/G1: FairnessGuard — mask protected info from candidate responses before scoring
            masked_response = response_clean
            try:
                from app.shared.pii_masking import strip_pii_for_llm_prompt
                masked_response = strip_pii_for_llm_prompt(response_clean)
            except Exception as _pii_exc:
                logger.debug("[WSIInterviewGraph][A3] PII masking skipped: %s", _pii_exc)

            try:
                from app.shared.compliance.fairness_guard_middleware import check_fairness
                _fg_resp = check_fairness(
                    {"candidate_response": masked_response},
                    context="wsi_candidate_response",
                    company_id=str(state.candidate_profile.get("company_id", "")),
                    affirmative_criterion=(
                        state.job_requirements.get("affirmative_criteria_primary")
                        if state.job_requirements.get("is_affirmative") else None
                    ),
                )
                if _fg_resp.has_warnings:
                    state.log_step("validate_response", {
                        "status": "fairness_warnings",
                        "warnings_count": len(_fg_resp.warnings),
                    })
                    logger.info(
                        "[WSIInterviewGraph][A3] FairnessGuard L2 warnings on candidate response "
                        "session=%s warnings=%d",
                        state.session_id, len(_fg_resp.warnings),
                    )
            except Exception as _fg_exc:
                logger.debug("[WSIInterviewGraph][A3] FairnessGuard check skipped: %s", _fg_exc)

            # Válida: vai para scoring
            # Armazena temporariamente para score_response
            state.candidate_profile["_pending_response"] = {
                "text": masked_response,
                "question_block": state.current_question,
            }
            state.stage = WSIInterviewStage.SCORE_RESPONSE

        return state

    async def score_response(self, state: WSIInterviewState) -> WSIInterviewState:
        """Pontua a resposta usando deterministic scorer + LLM assessment."""
        state.stage = WSIInterviewStage.SCORE_RESPONSE

        pending = state.candidate_profile.pop("_pending_response", {})
        response_text = pending.get("text", "")
        block = state.current_question

        if not block or not response_text:
            state.current_question_index += 1
            state.stage = WSIInterviewStage.ADVANCE
            return state

        try:
            from app.domains.cv_screening.services.wsi_deterministic_scorer import calculate_wsi_deterministic

            score_result = calculate_wsi_deterministic(
                response_text=response_text,
                competency_name=block.competency,
                question_framework=getattr(block, "framework", "CBI"),
            )

            record = WSIResponseRecord(
                question_block=block,
                candidate_response=response_text,
                score=score_result.final_score,
                bloom_achieved=score_result.bloom_level,
                dreyfus_achieved=score_result.dreyfus_level,
                reasoning=score_result.justification,
                scored_at=datetime.utcnow(),
            )
            state.responses.append(record)

            # Acumula score na dimensão correta
            self._accumulate_score(state, block.block_type, record.score, block.max_score)

            state.log_step("score_response", {
                "status": "scored",
                "block_id": block.block_id,
                "score": record.score,
                "bloom_achieved": record.bloom_achieved,
                "dreyfus_achieved": record.dreyfus_achieved,
            })

            # AUD: Audit trail para cada bloco avaliado (BCB 498 / SOX)
            try:
                from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
                await audit_service.log_decision(
                    company_id=str(state.company_id) if state.company_id else None,
                    agent_name="wsi_interview_graph",
                    decision_type="score_candidate",
                    action="wsi_block_scored",
                    decision=f"block_{block.block_id}_scored",
                    reasoning=[
                        f"WSI block {block.block_id} scored via BARS",
                        f"Block type: {block.block_type}",
                        f"Score: {record.score}",
                        f"Bloom achieved: {record.bloom_achieved}",
                        f"Dreyfus achieved: {record.dreyfus_achieved}",
                        f"Competency: {block.competency}",
                    ],
                    criteria_used=["bloom_taxonomy", "dreyfus_model", "competency_scoring"],
                    candidate_id=str(state.candidate_id) if state.candidate_id else None,
                    job_vacancy_id=str(state.job_id) if state.job_id else None,
                    score=float(record.score) if record.score else None,
                    human_review_required=False,
                    criteria_ignored=list(PROTECTED_CRITERIA),
                )
            except Exception as _audit_exc:
                logger.debug("[WSIInterviewGraph] audit_service skipped in score_response: %s", _audit_exc)

        except Exception as exc:
            logger.warning(f"[WSIInterviewGraph] score_response error: {exc}")
            state.log_step("score_response", {"status": "error", "error": str(exc)})

        state.current_question_index += 1
        state.stage = WSIInterviewStage.ADVANCE
        return state

    async def advance(self, state: WSIInterviewState) -> WSIInterviewState:
        """Decide o próximo estado: próxima pergunta ou encerramento."""
        if state.current_question_index >= len(state.question_blocks):
            state.stage = WSIInterviewStage.GENERATE_FEEDBACK
        else:
            state.stage = WSIInterviewStage.GENERATE_QUESTION

        state.log_step("advance", {
            "next_stage": state.stage.value,
            "progress_pct": round(state.progress_pct, 1),
            "questions_remaining": state.questions_remaining,
        })
        return state

    async def generate_feedback(self, state: WSIInterviewState) -> WSIInterviewState:
        """Calcula score final WSI e gera parecer."""
        state.stage = WSIInterviewStage.GENERATE_FEEDBACK
        try:
            from app.domains.cv_screening.services.wsi_deterministic_scorer import (
                calculate_final_wsi_score as deterministic_final,
            )

            # Usa SENIORITY_WEIGHTS da spec F8 (não hardcoded 70%/30%)
            _seniority = state.job_requirements.get("seniority")

            # F9-1 — WSI_técnico: média simples por pergunta técnica
            _tech_scores = [
                (r.question_block.competency, r.score, 1.0)
                for r in state.responses
                if r.question_block.block_type == "technical"
            ] or [("technical", state.technical_score, 1.0)]

            # F9-1 — WSI_comportamental: ponderado pelo trait_weight do ranking F3
            # trait_weight = score_final_trait / soma_scores_traits (padrão 1.0 = uniforme)
            _behav_scores = [
                (r.question_block.competency, r.score, r.question_block.trait_weight)
                for r in state.responses
                if r.question_block.block_type in ("behavioral", "situational")
            ] or [("behavioral", state.behavioral_score, 1.0)]

            _final_result = deterministic_final(
                technical_scores=_tech_scores,
                behavioral_scores=_behav_scores,
                seniority=_seniority,
            )
            state.wsi_final_score = _final_result.get("final_score", 0.0)

            _decision = _final_result.get("decision", "rejected")
            if _decision == "approved":
                state.recommendation = "aprovado"
            elif _decision == "needs_review":
                state.recommendation = "aguardando"
            else:
                state.recommendation = "reprovado"

            state.stage = WSIInterviewStage.COMPLETE
            state.completed_at = datetime.utcnow()

            state.log_step("generate_feedback", {
                "status": "complete",
                "wsi_final_score": state.wsi_final_score,
                "recommendation": state.recommendation,
                "total_responses": len(state.responses),
                "duration_s": (state.completed_at - state.started_at).total_seconds(),
            })

            # AUD: Audit trail para avaliação final WSI (BCB 498 / SOX)
            try:
                from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
                _passed = state.recommendation == "aprovado"
                await audit_service.log_decision(
                    company_id=str(state.company_id) if state.company_id else None,
                    agent_name="wsi_interview_graph",
                    decision_type="approved" if _passed else "rejected",
                    action="wsi_final_evaluation",
                    decision="approved" if _passed else "rejected",
                    reasoning=[
                        "WSI final evaluation completed",
                        f"Final score: {state.wsi_final_score}",
                        f"Recommendation: {state.recommendation}",
                        f"Total responses: {len(state.responses)}",
                        f"Passed: {_passed}",
                    ],
                    criteria_used=["wsi_score", "bloom_taxonomy", "dreyfus_model", "competency_evaluation"],
                    candidate_id=str(state.candidate_id) if state.candidate_id else None,
                    job_vacancy_id=str(state.job_id) if state.job_id else None,
                    score=float(state.wsi_final_score) if state.wsi_final_score else None,
                    human_review_required=True,
                    criteria_ignored=list(PROTECTED_CRITERIA),
                )
            except Exception as _audit_exc:
                logger.debug("[WSIInterviewGraph] audit_service skipped in generate_feedback: %s", _audit_exc)

            # ── Gate 1 feedback ao candidato (fail-safe — Gap 16.1) ─────────
            # Envia email de resultado apenas quando há email no perfil do candidato.
            if state.recommendation == "reprovado":
                try:
                    from app.domains.candidates.services.candidate_feedback_service import (
                        candidate_feedback_service as _cfs,
                    )
                    _email = state.candidate_profile.get("email")
                    if _email:
                        import asyncio as _asyncio
                        _asyncio.ensure_future(
                            _cfs.send_gate_feedback(
                                gate_level="gate1_rejected",
                                candidate_email=_email,
                                candidate_name=state.candidate_profile.get("name", "Candidato"),
                                vacancy_title=state.job_requirements.get("title", "Vaga"),
                                company_name=state.job_requirements.get("company_name", "WeDOTalent"),
                            )
                        )
                except Exception as _fe:
                    logger.debug("[WSI] gate1 feedback failed (non-blocking): %s", _fe)
            # ────────────────────────────────────────────────────────────────

        except Exception as exc:
            logger.error(f"[WSIInterviewGraph] generate_feedback failed: {exc}", exc_info=True)
            state.error = str(exc)
            state.stage = WSIInterviewStage.ERROR
            state.log_step("generate_feedback", {"status": "error", "error": str(exc)})

        return state

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _accumulate_score(
        self, state: WSIInterviewState, block_type: str, score: float, max_score: float
    ) -> None:
        # score comes from DeterministicWSIResult.final_score — already in [1.0, 5.0].
        # Spec F8: média simples por bloco (cada resposta tem peso igual dentro do bloco).
        # Fórmula: new_avg = (old_avg * n + new_score) / (n + 1)
        clamped = max(1.0, min(5.0, score))
        if block_type == "technical":
            n = state.technical_score_count
            state.technical_score = (state.technical_score * n + clamped) / (n + 1)
            state.technical_score_count = n + 1
        elif block_type in ("behavioral", "situational"):
            n = state.behavioral_score_count
            state.behavioral_score = (state.behavioral_score * n + clamped) / (n + 1)
            state.behavioral_score_count = n + 1

    def _build_fallback_questions(self) -> list[WSIQuestionBlock]:
        """Perguntas de fallback quando o pipeline não consegue gerar questões."""
        return [
            WSIQuestionBlock(
                block_id="fallback-1",
                block_type="behavioral",
                question="Descreva uma situação em que você precisou solucionar um problema complexo no trabalho.",
                competency="problem_solving",
                bloom_level=4,
                dreyfus_level=3,
            ),
            WSIQuestionBlock(
                block_id="fallback-2",
                block_type="situational",
                question="Como você lidaria com um prazo apertado e recursos limitados?",
                competency="adaptability",
                bloom_level=3,
                dreyfus_level=3,
            ),
        ]


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class WSIInterviewGraph:
    """
    Grafo de estado para condução de entrevistas WSI síncronas.

    Fluxo:
        load_context
            → generate_question  (loop: apresenta cada pergunta)
                → validate_response  (candidato responde)
                    → score_response  (se resposta válida)
                        → advance  (próxima pergunta ou encerramento)
                    → advance  (se skip/vazio)
            → generate_feedback  (todas perguntas respondidas)
                → COMPLETE

    Uso:
        graph = WSIInterviewGraph()
        state = graph.create_session(candidate_id=..., job_id=..., company_id=...)
        state = await graph.start(state)                    # load_context + 1ª pergunta
        state = await graph.submit_response(state, "...")   # responde e avança
        if state.is_complete:
            logger.debug("WSI complete: score=%s recommendation=%s", state.wsi_final_score, state.recommendation)
    """

    def __init__(self, nodes: WSIInterviewNodes | None = None):
        self.nodes = nodes or WSIInterviewNodes()
        self._compiled_lg: Any | None = None  # LangGraph compiled graph (lazy init)
        logger.info("[WSIInterviewGraph] Initialized")


    def create_session(
        self,
        candidate_id: str,
        job_id: str,
        company_id: str,
        interview_level: str = "standard",
    ) -> WSIInterviewState:
        """Cria uma nova sessão de entrevista WSI."""
        return WSIInterviewState(
            session_id=f"system:{uuid4()}",
            company_id=company_id,
            candidate_id=candidate_id,
            job_id=job_id,
            interview_level=interview_level,
        )

    # ------------------------------------------------------------------
    # LangGraph nativo — StateGraph com operação start/submit
    # ------------------------------------------------------------------

    def _build_langgraph(self) -> Any:
        """Constrói StateGraph com nós wrapper (dict ↔ WSIInterviewState)."""
        from langgraph.graph import END as LEND
        from langgraph.graph import StateGraph
        from lia_agents_core.checkpointer import get_checkpointer

        nodes_ref = self.nodes

        # ---- Node wrappers ----

        async def lg_load_context(s: dict) -> dict:
            wsi = _wsi_state_from_dict(s["wsi_data"])
            wsi = await nodes_ref.load_context(wsi)
            return {"wsi_data": _wsi_state_to_dict(wsi)}

        async def lg_generate_question(s: dict) -> dict:
            wsi = _wsi_state_from_dict(s["wsi_data"])
            wsi = await nodes_ref.generate_question(wsi)
            return {"wsi_data": _wsi_state_to_dict(wsi)}

        async def lg_validate_response(s: dict) -> dict:
            wsi = _wsi_state_from_dict(s["wsi_data"])
            wsi = await nodes_ref.validate_response(wsi, s.get("pending_response", ""))
            return {"wsi_data": _wsi_state_to_dict(wsi), "pending_response": ""}

        async def lg_score_response(s: dict) -> dict:
            wsi = _wsi_state_from_dict(s["wsi_data"])
            wsi = await nodes_ref.score_response(wsi)
            return {"wsi_data": _wsi_state_to_dict(wsi)}

        async def lg_advance(s: dict) -> dict:
            wsi = _wsi_state_from_dict(s["wsi_data"])
            wsi = await nodes_ref.advance(wsi)
            return {"wsi_data": _wsi_state_to_dict(wsi)}

        async def lg_generate_feedback(s: dict) -> dict:
            wsi = _wsi_state_from_dict(s["wsi_data"])
            wsi = await nodes_ref.generate_feedback(wsi)
            return {"wsi_data": _wsi_state_to_dict(wsi)}

        # ---- Routing functions ----

        def route_dispatcher(s: dict) -> str:
            return "lg_load_context" if s.get("operation") == "start" else "lg_validate_response"

        def route_after_load(s: dict) -> str:
            stage = s.get("wsi_data", {}).get("stage", "")
            if stage == WSIInterviewStage.ERROR.value:
                return "error"
            if stage == WSIInterviewStage.COMPLETE.value:
                return "complete"
            return "ok"

        def route_after_gen_question(s: dict) -> str:
            stage = s.get("wsi_data", {}).get("stage", "")
            return "feedback" if stage == WSIInterviewStage.GENERATE_FEEDBACK.value else "end"

        def route_after_validate(s: dict) -> str:
            stage = s.get("wsi_data", {}).get("stage", "")
            return "score" if stage == WSIInterviewStage.SCORE_RESPONSE.value else "advance"

        def route_after_advance(s: dict) -> str:
            stage = s.get("wsi_data", {}).get("stage", "")
            return "feedback" if stage == WSIInterviewStage.GENERATE_FEEDBACK.value else "question"

        # ---- Build graph ----

        schema = _WSILangGraphState if _HAS_WSI_TYPED_DICT else dict
        builder = StateGraph(schema)

        builder.add_node("lg_dispatcher", lambda s: s)
        builder.add_node("lg_load_context", lg_load_context)
        builder.add_node("lg_generate_question", lg_generate_question)
        builder.add_node("lg_validate_response", lg_validate_response)
        builder.add_node("lg_score_response", lg_score_response)
        builder.add_node("lg_advance", lg_advance)
        builder.add_node("lg_generate_feedback", lg_generate_feedback)

        builder.set_entry_point("lg_dispatcher")
        builder.add_conditional_edges("lg_dispatcher", route_dispatcher, {
            "lg_load_context": "lg_load_context",
            "lg_validate_response": "lg_validate_response",
        })
        builder.add_conditional_edges("lg_load_context", route_after_load, {
            "error": LEND,
            "complete": LEND,
            "ok": "lg_generate_question",
        })
        builder.add_conditional_edges("lg_generate_question", route_after_gen_question, {
            "end": LEND,
            "feedback": "lg_generate_feedback",
        })
        builder.add_conditional_edges("lg_validate_response", route_after_validate, {
            "score": "lg_score_response",
            "advance": "lg_advance",
        })
        builder.add_edge("lg_score_response", "lg_advance")
        builder.add_conditional_edges("lg_advance", route_after_advance, {
            "question": "lg_generate_question",
            "feedback": "lg_generate_feedback",
        })
        builder.add_edge("lg_generate_feedback", LEND)

        # interrupt_before lg_generate_feedback: permite HITL antes de finalizar avaliação WSI
        return builder.compile(
            checkpointer=get_checkpointer(),
            interrupt_before=["lg_generate_feedback"],
        )

    async def _start_langgraph(
        self, state: WSIInterviewState, audit_callback=None
    ) -> WSIInterviewState:
        """Inicia sessão via StateGraph nativo (operation='start').

        P36 Full: injects 3-layer intelligence before graph execution.
        """
        if self._compiled_lg is None:
            self._compiled_lg = self._build_langgraph()

        # --- P36: Camada 3 — Global screening insights ---
        screening_insights_snippet = ""
        try:
            from app.shared.services.global_insights_service import get_global_insights
            insights_svc = get_global_insights()
            insights = await insights_svc.get_screening_insights()
            screening_insights_snippet = insights_svc.format_screening_for_prompt(insights)
        except Exception as exc:
            logger.debug("[WSIInterviewGraph] GlobalInsights skipped: %s", exc)

        # --- P36: Camada 2 — Recruiter personalization ---
        recruiter_snippet = ""
        try:
            from app.domains.analytics.services.recruiter_personalization_service import get_recruiter_prompt_context
            recruiter_snippet = await get_recruiter_prompt_context(
                recruiter_id="system",
                company_id=str(state.company_id),
            )
        except Exception as exc:
            logger.debug("[WSIInterviewGraph] RecruiterPersonalization skipped: %s", exc)

        # Inject into wsi_data metadata (available to scoring/question generation nodes)
        wsi_dict = _wsi_state_to_dict(state)
        if screening_insights_snippet or recruiter_snippet:
            meta = wsi_dict.get("metadata") or {}
            if screening_insights_snippet:
                meta["screening_insights"] = screening_insights_snippet
            if recruiter_snippet:
                meta["recruiter_context"] = recruiter_snippet
            wsi_dict["metadata"] = meta

        lg_input = {
            "wsi_data": wsi_dict,
            "pending_response": "",
            "operation": "start",
        }
        try:
            result = await self._compiled_lg.ainvoke(
                lg_input,
                config={"configurable": {"thread_id": state.session_id}},
            )
            wsi_data = result.get("wsi_data") if isinstance(result, dict) else None
            return _wsi_state_from_dict(wsi_data) if wsi_data else state
        except Exception as exc:
            logger.error(f"[WSIInterviewGraph] LangGraph start failed: {exc}", exc_info=True)
            state.error = str(exc)
            state.stage = WSIInterviewStage.ERROR
            return state

    async def _submit_response_langgraph(
        self,
        state: WSIInterviewState,
        candidate_response: str,
        audit_callback=None,
    ) -> WSIInterviewState:
        """Processa resposta via StateGraph nativo (operation='submit')."""
        if self._compiled_lg is None:
            self._compiled_lg = self._build_langgraph()

        lg_input = {
            "wsi_data": _wsi_state_to_dict(state),
            "pending_response": candidate_response,
            "operation": "submit",
        }
        config = {"configurable": {"thread_id": state.session_id}}
        try:
            result = await self._compiled_lg.ainvoke(lg_input, config=config)

            # ── HITL: detectar interrupt_before lg_generate_feedback ─────────
            if isinstance(result, dict) and result.get("__interrupt__"):
                if not getattr(state, "hitl_approved", False):
                    try:
                        from app.domains.cv_screening.services.hitl_service import hitl_service
                        wsi_dict = result.get("wsi_data", {})
                        await hitl_service.request_approval(
                            thread_id=state.session_id,
                            action="finalize_wsi_score",
                            description=(
                                f"Aprovar avaliação WSI finalizada. "
                                f"Score final: {wsi_dict.get('wsi_final_score', 'calculando')}"
                            ),
                            data={
                                "session_id": state.session_id,
                                "wsi_final_score": wsi_dict.get("wsi_final_score"),
                                "technical_score": wsi_dict.get("technical_score"),
                                "behavioral_score": wsi_dict.get("behavioral_score"),
                            },
                            ws_session_id=state.session_id,
                            domain="cv_screening",
                            company_id=state.company_id if hasattr(state, "company_id") else "",
                        )
                        await hitl_service.store_resume_info(
                            thread_id=state.session_id,
                            domain="cv_screening",
                            session_id=state.session_id,
                            agent_input_dict={
                                "message": candidate_response,
                                "context": {
                                    "company_id": getattr(state, "company_id", ""),
                                    "hitl_approved": True,
                                    "wsi_session_id": state.session_id,
                                },
                                "session_id": state.session_id,
                                "company_id": getattr(state, "company_id", ""),
                                "user_id": "",
                            },
                            hitl_context="wsi_finalize_score",
                        )
                        logger.info("[WSIInterviewGraph] HITL aprovação solicitada session=%s", state.session_id)
                        # Retorna estado atual (sem feedback gerado ainda)
                        wsi_data = result.get("wsi_data")
                        return _wsi_state_from_dict(wsi_data) if wsi_data else state
                    except Exception as _hitl_exc:
                        logger.warning("[WSIInterviewGraph] HITL request_approval falhou: %s", _hitl_exc)
                else:
                    # hitl_approved=True: resume imediatamente para gerar feedback
                    result = await self._compiled_lg.ainvoke(None, config=config)

            wsi_data = result.get("wsi_data") if isinstance(result, dict) else None
            return _wsi_state_from_dict(wsi_data) if wsi_data else state
        except Exception as exc:
            logger.error(f"[WSIInterviewGraph] LangGraph submit failed: {exc}", exc_info=True)
            state.error = str(exc)
            state.stage = WSIInterviewStage.ERROR
            return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start(
        self, state: WSIInterviewState, audit_callback=None
    ) -> WSIInterviewState:
        """Inicia sessão via LangGraph nativo."""
        return await self._start_langgraph(state, audit_callback)

    async def submit_response(
        self, state: WSIInterviewState, candidate_response: str, audit_callback=None
    ) -> WSIInterviewState:
        """Submete resposta do candidato via LangGraph nativo."""
        return await self._submit_response_langgraph(state, candidate_response, audit_callback)

    def get_session_summary(self, state: WSIInterviewState) -> dict[str, Any]:
        """Retorna resumo auditável da sessão (para compliance e relatórios)."""
        return {
            "session_id": state.session_id,
            "candidate_id": state.candidate_id,
            "job_id": state.job_id,
            "company_id": state.company_id,
            "interview_level": state.interview_level,
            "stage": state.stage.value,
            "is_complete": state.is_complete,
            "progress_pct": round(state.progress_pct, 1),
            "questions_total": len(state.question_blocks),
            "questions_answered": len(state.responses),
            "scores": {
                "technical": round(state.technical_score, 2),
                "behavioral": round(state.behavioral_score, 2),
                "situational": round(state.situational_score, 2),
                "final": state.wsi_final_score,
            },
            "recommendation": state.recommendation,
            "started_at": state.started_at.isoformat(),
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "execution_log": state.execution_log,
        }


# Singleton para uso compartilhado (cada sessão cria um WSIInterviewState próprio)
wsi_interview_graph = WSIInterviewGraph()
