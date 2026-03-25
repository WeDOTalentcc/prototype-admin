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
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
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

class WSIInterviewStage(str, Enum):
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
    big_five_trait: Optional[str] = None
    max_score: float = 10.0


@dataclass
class WSIResponseRecord:
    question_block: WSIQuestionBlock
    candidate_response: str
    score: float = 0.0
    bloom_achieved: int = 0
    dreyfus_achieved: int = 0
    reasoning: str = ""
    scored_at: Optional[datetime] = None


@dataclass
class WSIInterviewState:
    session_id: str
    company_id: str
    candidate_id: str
    job_id: str
    interview_level: str = "standard"  # "quick" | "standard" | "full"

    # Contexto carregado no LOAD_CONTEXT
    job_requirements: Dict[str, Any] = field(default_factory=dict)
    candidate_profile: Dict[str, Any] = field(default_factory=dict)

    # Banco de perguntas para esta sessão
    question_blocks: List[WSIQuestionBlock] = field(default_factory=list)
    current_question_index: int = 0

    # Respostas coletadas
    responses: List[WSIResponseRecord] = field(default_factory=list)

    # Pergunta atual em exibição
    current_question: Optional[WSIQuestionBlock] = None
    awaiting_response: bool = False

    # Scores parciais por dimensão
    technical_score: float = 0.0
    behavioral_score: float = 0.0
    situational_score: float = 0.0

    # Score final
    wsi_final_score: Optional[float] = None
    recommendation: str = ""  # "aprovado" | "aguardando" | "reprovado"

    # Auditoria
    stage: WSIInterviewStage = WSIInterviewStage.INIT
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def log_step(self, node: str, details: Dict[str, Any]) -> None:
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
                    from app.core.database import AsyncSessionLocal
                    from sqlalchemy import text as _sql_text
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
                    result = pipeline.build_pipeline(req, [])
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

            # Válida: vai para scoring
            # Armazena temporariamente para score_response
            state.candidate_profile["_pending_response"] = {
                "text": response_clean,
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
            from app.services.wsi_deterministic_scorer import calculate_wsi_deterministic

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
                from app.shared.compliance.audit_service import audit_service, PROTECTED_CRITERIA
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as _audit_db:
                    await audit_service.log_decision(
                        db=_audit_db,
                        company_id=state.company_id,
                        domain="cv_screening",
                        agent_name="wsi_interview_graph",
                        decision_type="wsi_score",
                        decision=f"block_{block.block_id}_scored",
                        candidate_id=state.candidate_id,
                        job_id=state.job_id,
                        metadata={
                            "block": block.block_id,
                            "block_type": block.block_type,
                            "score": record.score,
                            "bloom_achieved": record.bloom_achieved,
                            "dreyfus_achieved": record.dreyfus_achieved,
                            "competency": block.competency,
                        },
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
            from app.services.wsi_deterministic_scorer import calculate_final_wsi_score as deterministic_final

            _final_result = deterministic_final(
                technical_scores=[("technical", state.technical_score, 1.0)],
                behavioral_scores=[
                    ("behavioral", state.behavioral_score, 0.6),
                    ("situational", state.situational_score, 0.4),
                ],
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
                from app.shared.compliance.audit_service import audit_service
                from app.core.database import AsyncSessionLocal
                _passed = state.recommendation == "aprovado"
                async with AsyncSessionLocal() as _audit_db:
                    await audit_service.log_decision(
                        db=_audit_db,
                        company_id=state.company_id,
                        domain="cv_screening",
                        agent_name="wsi_interview_graph",
                        decision_type="wsi_final_evaluation",
                        decision="approved" if _passed else "rejected",
                        candidate_id=state.candidate_id,
                        job_id=state.job_id,
                        metadata={
                            "final_score": state.wsi_final_score,
                            "passed": _passed,
                            "recommendation": state.recommendation,
                            "total_responses": len(state.responses),
                        },
                        criteria_ignored=[],
                    )
            except Exception as _audit_exc:
                logger.debug("[WSIInterviewGraph] audit_service skipped in generate_feedback: %s", _audit_exc)

            # D2 — Confidence calibration: emite métrica Prometheus para cv_screening
            try:
                from app.shared.observability.agent_metrics import record_confidence
                record_confidence(
                    domain="cv_screening",
                    confidence=min(1.0, (state.wsi_final_score or 0.0) / 5.0),
                    has_tools=False,
                )
            except Exception:
                pass  # fail-safe: nunca bloquear avaliação por métrica

            # ── Gate 1 feedback ao candidato (fail-safe — Gap 16.1) ─────────
            # Envia email de resultado apenas quando há email no perfil do candidato.
            if state.recommendation == "reprovado":
                try:
                    from app.services.candidate_feedback_service import (
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
        # Feed directly to calculate_final_wsi_score which expects /5 scale.
        clamped = max(1.0, min(5.0, score))
        if block_type == "technical":
            state.technical_score = (state.technical_score + clamped) / 2
        elif block_type in ("behavioral", "situational"):
            state.behavioral_score = (state.behavioral_score + clamped) / 2

    def _build_fallback_questions(self) -> List[WSIQuestionBlock]:
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

    def __init__(self, nodes: Optional[WSIInterviewNodes] = None):
        self.nodes = nodes or WSIInterviewNodes()
        self._compiled_lg: Optional[Any] = None  # LangGraph compiled graph (lazy init)
        logger.info("[WSIInterviewGraph] Initialized")

    async def _run_node(
        self,
        node_name: str,
        node_fn,
        state: WSIInterviewState,
        *args,
        audit_callback=None,
    ) -> WSIInterviewState:
        """Executa um nó com logging auditável (BCB 498 / SOX)."""
        t0 = time.perf_counter()
        try:
            logger.info(
                f"[WSIInterviewGraph] node_start node={node_name}",
                extra={"session_id": state.session_id, "node": node_name, "graph": "WSIInterviewGraph"},
            )
            result = await node_fn(state, *args)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(
                f"[WSIInterviewGraph] node_end node={node_name} elapsed_ms={elapsed_ms}",
                extra={
                    "session_id": state.session_id,
                    "node": node_name,
                    "elapsed_ms": elapsed_ms,
                    "graph": "WSIInterviewGraph",
                },
            )
            if audit_callback:
                audit_callback.on_tool_call(
                    tool_name=node_name,
                    input_preview=f"stage={state.stage.value}",
                    output_preview=f"result_stage={result.stage.value}",
                    latency_ms=float(elapsed_ms),
                    success=True,
                )
            return result
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            logger.error(
                f"[WSIInterviewGraph] node_error node={node_name} elapsed_ms={elapsed_ms}: {exc}",
                extra={
                    "session_id": state.session_id,
                    "node": node_name,
                    "elapsed_ms": elapsed_ms,
                    "error": str(exc),
                    "graph": "WSIInterviewGraph",
                },
                exc_info=True,
            )
            if audit_callback:
                audit_callback.on_tool_call(
                    tool_name=node_name,
                    input_preview=f"stage={state.stage.value}",
                    output_preview="error",
                    latency_ms=float(elapsed_ms),
                    success=False,
                    error=str(exc),
                )
            state.error = str(exc)
            state.stage = WSIInterviewStage.ERROR
            return state

    def create_session(
        self,
        candidate_id: str,
        job_id: str,
        company_id: str,
        interview_level: str = "standard",
    ) -> WSIInterviewState:
        """Cria uma nova sessão de entrevista WSI."""
        return WSIInterviewState(
            session_id=str(uuid4()),
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
        from langgraph.graph import StateGraph, END as LEND
        from app.shared.agents.checkpointer import get_checkpointer

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
        """Inicia sessão via StateGraph nativo (operation='start')."""
        if self._compiled_lg is None:
            try:
                self._compiled_lg = self._build_langgraph()
            except Exception as exc:
                logger.warning(f"[WSIInterviewGraph] LangGraph build failed: {exc}")
                return await self._start_legacy(state, audit_callback)

        lg_input = {
            "wsi_data": _wsi_state_to_dict(state),
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
            return await self._start_legacy(state, audit_callback)

    async def _submit_response_langgraph(
        self,
        state: WSIInterviewState,
        candidate_response: str,
        audit_callback=None,
    ) -> WSIInterviewState:
        """Processa resposta via StateGraph nativo (operation='submit')."""
        if self._compiled_lg is None:
            try:
                self._compiled_lg = self._build_langgraph()
            except Exception as exc:
                logger.warning(f"[WSIInterviewGraph] LangGraph build failed: {exc}")
                return await self._submit_response_legacy(state, candidate_response, audit_callback)

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
                        from app.services.hitl_service import hitl_service
                        wsi_dict = result.get("wsi_data", {})
                        pending_id = await hitl_service.request_approval(
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
            return await self._submit_response_legacy(state, candidate_response, audit_callback)

    # ------------------------------------------------------------------
    # Dual-path public API
    # ------------------------------------------------------------------

    async def start(
        self, state: WSIInterviewState, audit_callback=None
    ) -> WSIInterviewState:
        """Dual-path: LangGraph nativo (USE_LANGGRAPH_NATIVE=True) ou legado."""
        from app.core.config import settings
        if settings.USE_LANGGRAPH_NATIVE:
            return await self._start_langgraph(state, audit_callback)
        return await self._start_legacy(state, audit_callback)

    async def submit_response(
        self, state: WSIInterviewState, candidate_response: str, audit_callback=None
    ) -> WSIInterviewState:
        """Dual-path: LangGraph nativo (USE_LANGGRAPH_NATIVE=True) ou legado."""
        from app.core.config import settings
        if settings.USE_LANGGRAPH_NATIVE:
            return await self._submit_response_langgraph(state, candidate_response, audit_callback)
        return await self._submit_response_legacy(state, candidate_response, audit_callback)

    @_traceable(name="WSIInterviewGraph._start_legacy", run_type="chain")
    async def _start_legacy(
        self, state: WSIInterviewState, audit_callback=None
    ) -> WSIInterviewState:
        """Inicia a sessão: carrega contexto e apresenta a primeira pergunta."""
        if audit_callback:
            audit_callback.on_chain_start_manual()
        state = await self._run_node("load_context", self.nodes.load_context, state, audit_callback=audit_callback)
        if not state.is_complete:
            state = await self._run_node("generate_question", self.nodes.generate_question, state, audit_callback=audit_callback)
        if audit_callback and state.is_complete:
            await audit_callback.on_chain_end_manual(
                confidence=0.9, success=not bool(state.error), error=state.error
            )
        return state

    @_traceable(name="WSIInterviewGraph._submit_response_legacy", run_type="chain")
    async def _submit_response_legacy(
        self, state: WSIInterviewState, candidate_response: str, audit_callback=None
    ) -> WSIInterviewState:
        """Processa a resposta do candidato e avança para o próximo estado (legado).

        Retorna o estado atualizado. Se `state.awaiting_response` for True após
        o retorno, apresenta `state.current_question.question` para o candidato.
        Se `state.is_complete`, a entrevista foi encerrada.
        """
        if state.is_complete:
            return state

        if not state.awaiting_response:
            logger.warning(
                f"[WSIInterviewGraph] submit_response called but not awaiting_response "
                f"(session={state.session_id})"
            )
            return state

        # validate → score (ou skip) → advance → generate_question (ou feedback)
        state = await self._run_node(
            "validate_response", self.nodes.validate_response, state, candidate_response, audit_callback=audit_callback
        )

        if state.stage == WSIInterviewStage.SCORE_RESPONSE:
            state = await self._run_node("score_response", self.nodes.score_response, state, audit_callback=audit_callback)

        if state.stage == WSIInterviewStage.ADVANCE:
            state = await self._run_node("advance", self.nodes.advance, state, audit_callback=audit_callback)

        if state.stage == WSIInterviewStage.GENERATE_QUESTION:
            state = await self._run_node("generate_question", self.nodes.generate_question, state, audit_callback=audit_callback)
        elif state.stage == WSIInterviewStage.GENERATE_FEEDBACK:
            state = await self._run_node("generate_feedback", self.nodes.generate_feedback, state, audit_callback=audit_callback)

        if audit_callback and state.is_complete:
            await audit_callback.on_chain_end_manual(
                confidence=0.9 if not state.error else 0.3,
                success=not bool(state.error),
                error=state.error,
            )
        return state

    def get_session_summary(self, state: WSIInterviewState) -> Dict[str, Any]:
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
