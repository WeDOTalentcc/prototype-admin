"""
WSI Screening Pipeline Service - Unified orchestrator for all WSI screening blocks.

Orchestrates:
- Block 2: Company default screening questions + eligibility (from database)
- Block 3: Technical assessment (Bloom/Dreyfus via WSIService)
- Block 4: Behavioral/Situational (Big Five/CBI via WSIService)
"""
import logging
from difflib import SequenceMatcher
from typing import Any

from app.domains.cv_screening.constants.wsi_constants import (
    BLOOM_LEVEL_LABELS as BLOOM_LEVELS,
)
from app.domains.cv_screening.constants.wsi_constants import (
    DREYFUS_STAGE_LABELS as DREYFUS_STAGES,
)
from app.domains.cv_screening.constants.wsi_constants import (
    SENIORITY_DISTRIBUTIONS,
    SENIORITY_TO_BLOOM,
    SENIORITY_TO_DREYFUS,
    WSI_BLOCK_NAMES,
)
from app.domains.cv_screening.services.seniority_context_calibrator import (
    WSI_CONTEXTUAL_CALIBRATION_ENABLED,
    CalibrationContext,
    calibrate_or_fallback,
)
from app.domains.cv_screening.services.seniority_resolver import SENIORITY_RESOLVER_ENABLED, resolve_seniority_full
from app.domains.cv_screening.services.seniority_utils import normalize_seniority
from app.schemas.screening import (
    UnifiedScreeningQuestion,
    WSIBlockSummary,
    WSIScreeningPipelineRequest,
    WSIScreeningPipelineResponse,
)
from app.domains.voice.schemas.wsi_types import ScreeningPolicyConfig, ScreeningPolicyResult
from app.shared.policy_middleware import get_policy_for_company

logger = logging.getLogger(__name__)


def _build_pipeline_calibration_context(request, seniority: str) -> CalibrationContext:
    """Build calibration context from screening pipeline request."""
    skills = []
    if hasattr(request, 'skills') and request.skills:
        skills = request.skills if isinstance(request.skills, list) else [request.skills]
    elif hasattr(request, 'competencies') and request.competencies:
        skills = [c if isinstance(c, str) else getattr(c, 'name', str(c)) for c in request.competencies]

    return CalibrationContext(
        seniority=seniority,
        job_title=getattr(request, 'title', '') or getattr(request, 'job_title', '') or '',
        department=getattr(request, 'department', None),
        industry=getattr(request, 'industry', None),
        country=getattr(request, 'country', None),
        location=getattr(request, 'location', None),
        required_skills=skills,
        salary_min=getattr(request, 'salary_min', None),
        salary_max=getattr(request, 'salary_max', None),
        company_size=getattr(request, 'company_size', None),
    )

BLOCK_NAMES = {k: WSI_BLOCK_NAMES[k] for k in (2, 3, 4)}

MODEL_DISTRIBUTIONS = {
    "compact": {"technical": 4, "behavioral": 3, "total": 7},
    "full": {"technical": 7, "behavioral": 5, "total": 12},
}

AFFIRMATIVE_QUESTIONS = {
    "pcd": "Legal ter você aqui! 😊 Essa vaga faz parte do nosso programa de inclusão para Pessoas com Deficiência (PCD). Você se identifica com esse perfil? Fique tranquilo(a), sua resposta não elimina você do processo — queremos apenas entender melhor como adaptar as próximas etapas pra você.",
    "racial": "Que bom te ter aqui! 😊 Essa vaga faz parte do nosso programa de ação afirmativa para pessoas negras (pretas e pardas), por autodeclaração. Você se identifica com esse perfil? Independente da resposta, você segue no processo — mas é importante pra gente entender seu perfil.",
    "gender": "Que bom te ter aqui! 😊 Essa vaga faz parte do nosso programa de ação afirmativa para mulheres. Você se identifica com esse perfil? Sua resposta não elimina você do processo, mas nos ajuda a entender melhor a composição dos candidatos.",
    "age": "Legal ter você aqui! 😊 Essa vaga faz parte do nosso programa de inclusão para profissionais 50+. Você se enquadra nessa faixa etária? Fique tranquilo(a), sua resposta não elimina você do processo — queremos apenas garantir diversidade geracional.",
    "lgbtqia+": "Que bom te ter aqui! 😊 Essa vaga faz parte do nosso programa de diversidade para pessoas LGBTQIA+. Você se identifica com esse grupo? Sua resposta não elimina você do processo, é apenas para nos ajudar a promover um ambiente mais inclusivo.",
    "refugee": "Que bom te ter aqui! 😊 Essa vaga faz parte do nosso programa de inclusão para pessoas refugiadas e imigrantes. Você se identifica com esse perfil? Sua resposta não elimina você do processo — é apenas para nos ajudar a promover diversidade e inclusão.",
    "indigenous": "Que bom te ter aqui! 😊 Essa vaga faz parte do nosso programa de ação afirmativa para pessoas indígenas, por autodeclaração. Você se identifica com esse perfil? Independente da resposta, você segue no processo — queremos apenas entender melhor seu perfil.",
}

# Onda 2C.1 (audit 2026-06-06): ponte entre o vocabulário do critério gravado na vaga
# (affirmative_criteria_primary) e as chaves de AFFIRMATIVE_QUESTIONS. A VAGA é a fonte
# da verdade — o endpoint resolve o tipo server-side, sem confiar na flag do FE.
_CRITERION_TO_TYPE = {
    "gender": "gender",
    "race_ethnicity": "racial",
    "disability": "pcd",
    "lgbtqia": "lgbtqia+",
    "age": "age",
    "refugee": "refugee",
    "indigenous": "indigenous",
    "other": None,
}


def criterion_to_affirmative_type(criterion):
    """Mapeia affirmative_criteria_primary da vaga -> chave de AFFIRMATIVE_QUESTIONS.

    Retorna None para 'other'/desconhecido (injection usa o texto fallback genérico,
    nunca uma pergunta ausente).
    """
    if not criterion:
        return None
    return _CRITERION_TO_TYPE.get(str(criterion).strip().lower())



def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _is_duplicate(question_text: str, existing_texts: list[str], threshold: float = 0.65) -> bool:
    for existing in existing_texts:
        if _text_similarity(question_text, existing) >= threshold:
            return True
    return False


class WSIScreeningPipeline:
    """Unified orchestrator for WSI screening question generation."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def build_pipeline(
        self,
        request: WSIScreeningPipelineRequest,
        company_questions_raw: list[dict[str, Any]],
    ) -> WSIScreeningPipelineResponse:
        seniority_resolution_meta = None
        if SENIORITY_RESOLVER_ENABLED:
            resolution = resolve_seniority_full(
                explicit_seniority=request.seniority,
                job_title=request.job_title,
                job_description=request.job_description,
                salary_min=getattr(request, "salary_min", None),
                salary_max=getattr(request, "salary_max", None),
                technical_skills=request.technical_skills or None,
            )
            if request.seniority is not None:
                effective_seniority = normalize_seniority(request.seniority)
            else:
                effective_seniority = resolution.level
            seniority_resolution_meta = {
                "resolved": request.seniority is None,
                "source": "multi_signal" if request.seniority is None else "explicit_with_cross_validation",
                "effective_level": effective_seniority,
                "explicit_input": request.seniority,
                "resolver_level": resolution.level,
                "confidence": resolution.confidence,
                "agreement": resolution.agreement,
                "signals": [
                    {
                        "source": s.source,
                        "level": s.level,
                        "confidence": s.confidence,
                        "weight": s.weight,
                        "evidence": s.evidence,
                    }
                    for s in resolution.signals
                ],
                "warnings": resolution.validation_warnings,
                "confirmation_message": resolution.confirmation_message,
                "requires_confirmation": resolution.requires_confirmation,
            }
            if resolution.validation_warnings:
                self.logger.warning(f"Seniority resolution warnings: {resolution.validation_warnings}")
            self.logger.info(
                f"Seniority resolved: {effective_seniority} "
                f"(agreement={resolution.agreement}, confidence={resolution.confidence:.2f})"
            )
        elif request.seniority is not None:
            effective_seniority = normalize_seniority(request.seniority)
            seniority_resolution_meta = {
                "resolved": False,
                "source": "explicit",
                "effective_level": effective_seniority,
                "explicit_input": request.seniority,
            }
            self.logger.info(f"Seniority from explicit input: {effective_seniority}")
        else:
            effective_seniority = "pleno"
            seniority_resolution_meta = {
                "resolved": False,
                "source": "default",
                "effective_level": effective_seniority,
                "explicit_input": None,
            }
            self.logger.info(f"Seniority defaulted to: {effective_seniority}")

        all_questions: list[UnifiedScreeningQuestion] = []
        quality_warnings: list[str] = []

        seniority_dist = SENIORITY_DISTRIBUTIONS.get(request.format, SENIORITY_DISTRIBUTIONS["full"])
        model = seniority_dist.get(effective_seniority, MODEL_DISTRIBUTIONS.get(request.format, MODEL_DISTRIBUTIONS["full"]))
        model_total = model["total"]
        total_target = request.question_count if request.question_count is not None else model_total

        company_target = 0

        if total_target == model_total:
            tech_target = model["technical"]
            behav_target = model["behavioral"]
        else:
            ratio = total_target / model_total
            tech_target = max(1, round(model["technical"] * ratio))
            behav_target = max(1, round(model["behavioral"] * ratio))
            distributed = tech_target + behav_target
            if distributed < total_target:
                tech_target += total_target - distributed
            elif distributed > total_target:
                diff = distributed - total_target
                while diff > 0 and behav_target > 1:
                    behav_target -= 1
                    diff -= 1
                while diff > 0 and tech_target > 1:
                    tech_target -= 1
                    diff -= 1
        self.logger.info(
            f"Distribution for {effective_seniority}/{request.format}: "
            f"tech={tech_target}, behav={behav_target}, total_target={total_target}"
        )

        # --- Block 2: Company Questions (includes eligibility configured by recruiter) ---
        if request.include_company_questions and company_questions_raw:
            block_2_company = self._build_company_block(
                company_questions_raw,
                request.company_question_categories,
            )
            company_target = len(block_2_company)
            all_questions.extend(block_2_company)
            self.logger.info(f"Block 2: {len(block_2_company)} company questions")

        if request.is_affirmative:
            affirmative_text = AFFIRMATIVE_QUESTIONS.get(
                request.affirmative_type,
                "Que bom te ter aqui! Essa é uma vaga com ação afirmativa. Você se identifica com o perfil da ação afirmativa desta posição? Sua resposta não elimina você do processo — é apenas para nos ajudar a promover diversidade."
            )
            affirmative_q = UnifiedScreeningQuestion(
                id=f"wsi-affirmative-{request.affirmative_type or 'general'}",
                text=affirmative_text,
                category="company",
                block_id=2,
                source="company",
                bloom_level=1,
                bloom_label=BLOOM_LEVELS.get(1, "Lembrar"),
                dreyfus_stage=1,
                dreyfus_label=DREYFUS_STAGES.get(1, "Novato"),
                framework="WSI",
                weight=1.0,
                is_eliminatory=False,
                question_type="yes_no",
                expected_signals=["Autodeclaração", "Enquadramento no critério"],
                scoring_criteria={},
                is_selected=True,
                order=0,
            )
            all_questions.append(affirmative_q)
            self.logger.info(f"Injected affirmative action question into Block 2: {request.affirmative_type or 'general'}")

        # --- Block 3: Technical ---
        block_3 = await self._build_technical_block(request, tech_target, effective_seniority)
        all_questions.extend(block_3)
        if len(block_3) < 2:
            quality_warnings.append(
                f"Apenas {len(block_3)} perguntas técnicas. Recomendado: 3+"
            )
        self.logger.info(f"Block 3: {len(block_3)} technical questions")

        # --- Block 4: Behavioral / Situational ---
        block_4 = await self._build_behavioral_block(request, behav_target, effective_seniority)
        all_questions.extend(block_4)
        if len(block_4) < 2:
            quality_warnings.append(
                f"Apenas {len(block_4)} perguntas comportamentais. Recomendado: 2+"
            )
        self.logger.info(f"Block 4: {len(block_4)} behavioral questions")

        wsi_count = len(block_3) + len(block_4)
        wsi_target = total_target - company_target
        if wsi_count < wsi_target:
            deficit = wsi_target - wsi_count
            self.logger.info(f"Rebalancing: {deficit} questions short of target {wsi_target}")
            existing_ids = {q.id for q in all_questions}

            extra_behav = await self._build_behavioral_block(request, behav_target + deficit + 2, effective_seniority)
            for q in extra_behav:
                if deficit <= 0:
                    break
                if q.id not in existing_ids:
                    all_questions.append(q)
                    existing_ids.add(q.id)
                    deficit -= 1

            if deficit > 0:
                extra_tech = await self._build_technical_block(request, tech_target + deficit + 2, effective_seniority)
                for q in extra_tech:
                    if deficit <= 0:
                        break
                    if q.id not in existing_ids:
                        all_questions.append(q)
                        existing_ids.add(q.id)
                        deficit -= 1

            final_wsi = len(all_questions) - company_target
            if final_wsi < wsi_target:
                quality_warnings.append(
                    f"Pipeline gerou {final_wsi} perguntas WSI de {wsi_target} solicitadas. "
                    f"Adicione mais skills técnicas ou competências comportamentais para maior cobertura."
                )

        for idx, q in enumerate(all_questions):
            q.order = idx

        blocks = self._group_into_blocks(all_questions)

        block_dist = {}
        for b in blocks:
            block_dist[str(b.block_id)] = b.question_count

        if WSI_CONTEXTUAL_CALIBRATION_ENABLED:
            _cal_ctx = _build_pipeline_calibration_context(request, effective_seniority)
            _cal_result = calibrate_or_fallback(_cal_ctx)
            dreyfus_stage = _cal_result.dreyfus_target
            bloom_levels = _cal_result.bloom_levels
        else:
            _cal_result = None
            dreyfus_stage = SENIORITY_TO_DREYFUS.get(effective_seniority, 3)
            bloom_levels = SENIORITY_TO_BLOOM.get(effective_seniority, [3, 4])

        metadata = {
            "seniority": effective_seniority,
            "dreyfus_stage": dreyfus_stage,
            "bloom_levels": bloom_levels,
            "skills_count": len(request.technical_skills),
            "title": request.job_title,
            "department": request.department,
            "format": request.format,
            "company_questions_count": company_target,
        }
        if _cal_result is not None:
            metadata["calibration"] = {
                "enabled": True,
                "confidence": _cal_result.confidence,
                "area_profile_id": _cal_result.area_profile_id,
                "area_maturity": _cal_result.area_maturity,
                "years_reference": _cal_result.years_reference,
                "rationale": _cal_result.rationale,
                "calibration_offsets": _cal_result.calibration_offsets,
            }

        return WSIScreeningPipelineResponse(
            success=True,
            questions=all_questions,
            blocks=blocks,
            total_count=len(all_questions),
            block_distribution=block_dist,
            metadata=metadata,
            seniority_resolution=seniority_resolution_meta,
            quality_warnings=quality_warnings,
        )

    def _build_company_block(
        self,
        raw_questions: list[dict[str, Any]],
        category_filter: list[str] | None,
    ) -> list[UnifiedScreeningQuestion]:
        questions: list[UnifiedScreeningQuestion] = []
        for q in raw_questions:
            if not q.get("is_active", True):
                continue
            cat = q.get("category", "general")
            if category_filter and cat not in category_filter:
                continue

            q_type_map = {
                "yes_no": "yes_no",
                "text": "open",
                "single_choice": "single_choice",
                "multiple_choice": "multiple_choice",
                "scale": "scale",
            }

            questions.append(
                UnifiedScreeningQuestion(
                    id=str(q.get("id", "")),
                    text=q.get("question_text", ""),
                    category="company",
                    block_id=2,
                    source="company",
                    bloom_level=2,
                    bloom_label=BLOOM_LEVELS.get(2, "Compreender"),
                    dreyfus_stage=2,
                    dreyfus_label=DREYFUS_STAGES.get(2, "Iniciante Avançado"),
                    framework="Company",
                    weight=0.9 if q.get("is_eliminatory") else 0.7,
                    is_eliminatory=q.get("is_eliminatory", False),
                    question_type=q_type_map.get(q.get("question_type", "text"), "open"),
                    options=q.get("options"),
                    expected_answer=q.get("expected_answer"),
                    expected_signals=[],
                    scoring_criteria={},
                    is_selected=True,
                    order=q.get("order", 0),
                )
            )
        return questions

    async def _build_technical_block(
        self,
        request: WSIScreeningPipelineRequest,
        target_count: int,
        effective_seniority: str = "pleno",
    ) -> list[UnifiedScreeningQuestion]:
        # WSI-AUDIT-EXEMPT: helper interno do pipeline, sem company_id no scope.
        # Audit log unificado e gravado uma vez no endpoint /api/v1/wsi/screening-pipeline
        # (wsi_screening_pipeline_endpoint.py) para cobrir technical + behavioral + Block 1.5 + Block 2.
        # Granularidade per-block nao agrega valor (mesma decisao IA).
        available_skills = request.technical_skills or []

        if not available_skills:
            logger.warning("No technical skills provided — cannot generate technical questions")
            return []

        from app.domains.cv_screening.services.wsi_service import WSIService
        wsi_svc = WSIService()
        wsi_questions = await wsi_svc.generate_from_simple_inputs(
            skills=available_skills,
            seniority=effective_seniority,
            job_description=request.job_description,
            mode="compact",
        )

        tech_questions = [q for q in wsi_questions if q.question_type != "situational"]

        questions: list[UnifiedScreeningQuestion] = []
        dreyfus_stage = SENIORITY_TO_DREYFUS.get(effective_seniority, 3)
        dreyfus_label = DREYFUS_STAGES.get(dreyfus_stage, "Competente")
        for wq in tech_questions[:target_count]:
            bloom_level = wq.scoring_criteria.get("bloom_level", 3) if isinstance(wq.scoring_criteria, dict) else 3
            if not isinstance(bloom_level, int):
                try:
                    bloom_level = int(bloom_level)
                except (ValueError, TypeError):
                    bloom_level = 3
            questions.append(
                UnifiedScreeningQuestion(
                    id=wq.id,
                    text=wq.question_text,
                    category="technical",
                    block_id=3,
                    source="wsi_generated",
                    trait=wq.scoring_criteria.get("ocean_trait") if isinstance(wq.scoring_criteria, dict) else None,
                    skill=wq.competency,
                    bloom_level=bloom_level,
                    bloom_label=BLOOM_LEVELS.get(bloom_level, "Aplicar"),
                    dreyfus_stage=dreyfus_stage,
                    dreyfus_label=dreyfus_label,
                    framework=wq.framework,
                    weight=wq.weight,
                    expected_signals=wq.expected_signals,
                    scoring_criteria=wq.scoring_criteria if isinstance(wq.scoring_criteria, dict) else {},
                    is_selected=True,
                    question_type="open",
                    order=0,
                )
            )
        return questions

    async def _build_behavioral_block(
        self,
        request: WSIScreeningPipelineRequest,
        target_count: int,
        effective_seniority: str = "pleno",
    ) -> list[UnifiedScreeningQuestion]:
        # WSI-AUDIT-EXEMPT: helper interno do pipeline, sem company_id no scope.
        # Audit log unificado e gravado uma vez no endpoint /api/v1/wsi/screening-pipeline
        # (wsi_screening_pipeline_endpoint.py) para cobrir technical + behavioral + Block 1.5 + Block 2.
        # Granularidade per-block nao agrega valor (mesma decisao IA).
        BIG_FIVE_TRAITS = [
            "Abertura a mudanças",
            "Organização e disciplina",
            "Sociabilidade",
            "Cooperação",
            "Estabilidade emocional",
        ]

        behavioral_skills = request.behavioral_competencies
        if not behavioral_skills or len(behavioral_skills) == 0:
            behavioral_skills = BIG_FIVE_TRAITS[:target_count]
            logger.info(
                f"No behavioral competencies provided — using Big Five traits as base ({len(behavioral_skills)} traits)"
            )

        from app.domains.cv_screening.services.wsi_service import WSIService
        wsi_svc = WSIService()
        wsi_questions = await wsi_svc.generate_from_simple_inputs(
            skills=[],
            behavioral=behavioral_skills,
            seniority=effective_seniority,
            job_description=request.job_description,
            mode="compact",
        )

        behav_questions = [q for q in wsi_questions if q.framework == "BigFive" or q.question_type == "situational"]
        if not behav_questions:
            behav_questions = wsi_questions

        dreyfus_stage = SENIORITY_TO_DREYFUS.get(effective_seniority, 3)
        dreyfus_label = DREYFUS_STAGES.get(dreyfus_stage, "Competente")
        questions: list[UnifiedScreeningQuestion] = []
        selected = behav_questions[:target_count]
        for idx, wq in enumerate(selected):
            bloom_level = wq.scoring_criteria.get("bloom_level", 3) if isinstance(wq.scoring_criteria, dict) else 3
            if not isinstance(bloom_level, int):
                try:
                    bloom_level = int(bloom_level)
                except (ValueError, TypeError):
                    bloom_level = 3
            questions.append(
                UnifiedScreeningQuestion(
                    id=wq.id,
                    text=wq.question_text,
                    category="behavioral",
                    block_id=4,
                    source="wsi_generated",
                    trait=wq.scoring_criteria.get("ocean_trait") if isinstance(wq.scoring_criteria, dict) else None,
                    skill=wq.competency,
                    bloom_level=bloom_level,
                    bloom_label=BLOOM_LEVELS.get(bloom_level, "Aplicar"),
                    dreyfus_stage=dreyfus_stage,
                    dreyfus_label=dreyfus_label,
                    framework=wq.framework,
                    weight=wq.weight,
                    expected_signals=wq.expected_signals,
                    scoring_criteria=wq.scoring_criteria if isinstance(wq.scoring_criteria, dict) else {},
                    is_selected=True,
                    question_type="open",
                    order=0,
                )
            )
        return questions

    def _group_into_blocks(
        self, questions: list[UnifiedScreeningQuestion]
    ) -> list[WSIBlockSummary]:
        block_map: dict[int, list[UnifiedScreeningQuestion]] = {}
        for q in questions:
            block_map.setdefault(q.block_id, []).append(q)

        blocks: list[WSIBlockSummary] = []
        for bid in sorted(block_map.keys()):
            qs = block_map[bid]
            blocks.append(
                WSIBlockSummary(
                    block_id=bid,
                    block_name=BLOCK_NAMES.get(bid, f"Bloco {bid}"),
                    question_count=len(qs),
                    questions=qs,
                )
            )
        return blocks

    async def apply_screening_policy(
        self,
        company_id: str,
        questions: list[UnifiedScreeningQuestion],
        db=None,
    ) -> ScreeningPolicyResult:
        """
        Apply company screening_rules to screening results.
        
        Returns dict with:
        - questions: Original + company default questions
        - policy_applied: Whether a policy was found
        """
        result = {
            "questions": list(questions),
            "policy_applied": False,
        }
        
        if not company_id or not db:
            return result
        
        try:
            policy = await get_policy_for_company(company_id, db)
            screening = policy.get("screening_rules", {})
            result["policy_applied"] = True
            
            default_questions = screening.get("default_screening_questions", [])
            if default_questions:
                existing_texts = {q.text.lower().strip() for q in questions if hasattr(q, 'text')}
                for idx, dq in enumerate(default_questions):
                    if isinstance(dq, str) and dq.lower().strip() not in existing_texts:
                        result["questions"].append(
                            UnifiedScreeningQuestion(
                                id=f"company-policy-{idx}",
                                text=dq,
                                category="company",
                                block_id=2,
                                source="company",
                                bloom_level=2,
                                bloom_label=BLOOM_LEVELS.get(2, "Compreender"),
                                dreyfus_stage=2,
                                dreyfus_label=DREYFUS_STAGES.get(2, "Iniciante Avançado"),
                                framework="Company",
                                weight=0.7,
                                trait=None,
                                skill=None,
                                options=None,
                                expected_answer=None,
                                question_type="open",
                                is_eliminatory=False,
                                expected_signals=[],
                                scoring_criteria={},
                                is_selected=True,
                                order=len(result["questions"]) + 1,
                            )
                        )
        except Exception as e:
            logger.warning(f"Failed to apply screening policy for {company_id}: {e}")
        
        return result
    
    async def get_screening_policy(
        self,
        company_id: str,
        db=None,
    ) -> ScreeningPolicyConfig:
        """Get effective screening configuration for a company."""
        try:
            if db:
                policy = await get_policy_for_company(company_id, db)
                screening = policy.get("screening_rules", {})
                return {
                    "experience_policy": screening.get("experience_policy", "per_job"),
                    "default_screening_questions": screening.get("default_screening_questions", []),
                    "salary_expectation_filter": screening.get("salary_expectation_filter", False),
                    "salary_tolerance_percent": screening.get("salary_tolerance_percent", 15),
                }
        except Exception as e:
            logger.warning(f"Failed to load screening policy: {e}")

        return {
            "experience_policy": "per_job",
            "default_screening_questions": [],
            "salary_expectation_filter": False,
            "salary_tolerance_percent": 15,
        }


wsi_screening_pipeline = WSIScreeningPipeline()
