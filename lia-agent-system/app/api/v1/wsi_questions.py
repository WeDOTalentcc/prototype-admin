"""
WSI Questions API - Endpoints for WSI question generation and regeneration.

Provides:
- Generate WSI questions based on competencies using Gemini LLM
- Regenerate questions when competencies change
- Validate question quality with WSI minimums (3+ technical, 2+ behavioral)
- Template fallback if LLM is unavailable
- A2/G1: FairnessGuard check on generated question texts
"""
import logging
import json
import os
from typing import List, Optional, Set
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

from app.shared.compliance.fairness_guard_middleware import check_fairness

router = APIRouter(prefix="/wsi", tags=["WSI Questions"])
logger = logging.getLogger(__name__)

MIN_TECHNICAL_QUESTIONS = 4
MIN_BEHAVIORAL_QUESTIONS = 2
MIN_ELIGIBILITY_QUESTIONS = 2
DEFAULT_MAX_QUESTIONS = 12

_gemini_model = None


def _get_gemini_model():
    global _gemini_model
    if _gemini_model is None:
        import google.generativeai as genai
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not configured")
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
    return _gemini_model


def _clean_llm_json(response_text: str) -> str:
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    if text.startswith("json"):
        text = text[4:]
    return text.strip()


class WSIQuestion(BaseModel):
    """WSI question structure."""
    id: str
    question: str
    type: str = "open"
    required: bool = True
    options: Optional[List[str]] = None
    expected_answer: Optional[str] = None
    competency_validated: Optional[str] = None
    skill_type: Optional[str] = None
    block_id: Optional[int] = None


class GenerateQuestionsRequest(BaseModel):
    """Request to generate WSI questions."""
    company_id: str
    job_title: str
    technical_skills: List[str] = Field(default_factory=list)
    behavioral_competencies: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None
    department: Optional[str] = None
    max_questions: int = DEFAULT_MAX_QUESTIONS

    @validator('technical_skills', 'behavioral_competencies', pre=True, always=True)
    def filter_empty_strings(cls, v):
        if v is None:
            return []
        return [s.strip() for s in v if s and s.strip()]


class RegenerateQuestionsRequest(BaseModel):
    """Request to regenerate WSI questions based on full competency lists."""
    company_id: str
    job_title: str
    current_questions: List[WSIQuestion] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    behavioral_competencies: List[str] = Field(default_factory=list)
    seniority: Optional[str] = None
    max_questions: int = DEFAULT_MAX_QUESTIONS

    @validator('technical_skills', 'behavioral_competencies', pre=True, always=True)
    def filter_empty_strings(cls, v):
        if v is None:
            return []
        return [s.strip() for s in v if s and s.strip()]


class QuestionsResponse(BaseModel):
    """Response with generated questions."""
    success: bool
    questions: List[WSIQuestion]
    changes_summary: Optional[str] = None
    questions_added: int = 0
    questions_removed: int = 0
    quality_warnings: List[str] = Field(default_factory=list)
    block_distribution: Optional[dict] = None


ELIGIBILITY_TEMPLATES = [
    WSIQuestion(
        id="wsi-elig-availability",
        question="Qual sua disponibilidade para início? Existe algum período de aviso prévio ou compromisso atual que precisemos considerar?",
        type="eliminatory",
        required=True,
        competency_validated="Disponibilidade",
        skill_type="eligibility",
        block_id=2
    ),
    WSIQuestion(
        id="wsi-elig-work-model",
        question="Esta posição requer [modelo de trabalho]. Isso é compatível com sua situação atual? Há alguma restrição de localização?",
        type="eliminatory",
        required=True,
        competency_validated="Modelo de Trabalho",
        skill_type="eligibility",
        block_id=2
    )
]

QUESTION_TEMPLATES = {
    "technical": {
        "Python": "Descreva um projeto onde você utilizou Python para resolver um problema complexo. Quais bibliotecas você usou?",
        "JavaScript": "Como você organiza o código JavaScript em projetos grandes? Cite padrões que utiliza.",
        "React": "Explique como você gerencia estado em aplicações React. Já usou Redux, Context API ou outras soluções?",
        "Node.js": "Descreva sua experiência com Node.js em aplicações de produção. Como lida com escalabilidade?",
        "SQL": "Dê um exemplo de uma query SQL complexa que você escreveu. Como otimizou a performance?",
        "Docker": "Como você utiliza Docker no seu fluxo de trabalho? Tem experiência com orquestração?",
        "AWS": "Quais serviços AWS você já utilizou? Descreva um projeto onde aplicou arquitetura cloud.",
        "TypeScript": "Quais benefícios você vê no uso de TypeScript? Como aplica tipagem avançada?",
        "Kubernetes": "Descreva sua experiência com Kubernetes. Já configurou clusters em produção?",
        "Git": "Como você organiza branches e commits? Qual estratégia de git flow prefere?",
        "Java": "Descreva sua experiência com Java. Quais frameworks já utilizou em produção?",
        "C#": "Como você estrutura projetos em C#? Tem experiência com .NET Core?",
        "Go": "Quais são os benefícios que você vê no uso de Go? Em quais projetos aplicou?",
        "Ruby": "Descreva sua experiência com Ruby on Rails. Como lida com performance?",
        "PHP": "Como você organiza código em PHP? Quais frameworks conhece?",
    },
    "behavioral": {
        "Comunicação": "Conte sobre uma situação onde precisou explicar algo técnico para uma pessoa não-técnica.",
        "Liderança": "Descreva um momento onde liderou uma equipe ou projeto. Quais desafios enfrentou?",
        "Resolução de Problemas": "Fale sobre um problema complexo que resolveu. Qual foi sua abordagem?",
        "Trabalho em Equipe": "Como você lida com conflitos em equipe? Dê um exemplo concreto.",
        "Adaptabilidade": "Conte sobre uma mudança significativa no trabalho. Como se adaptou?",
        "Proatividade": "Descreva uma iniciativa que você tomou sem ser solicitado. Qual foi o resultado?",
        "Organização": "Como você gerencia múltiplas tarefas com prazos conflitantes?",
        "Empatia": "Conte sobre uma situação onde precisou entender o ponto de vista do outro.",
        "Resiliência": "Fale sobre um fracasso ou obstáculo significativo. Como superou?",
        "Pensamento Analítico": "Descreva uma decisão importante que tomou baseada em dados.",
        "Criatividade": "Conte sobre uma solução criativa que você propôs para um problema.",
        "Foco no Cliente": "Descreva uma situação onde foi além para atender às necessidades de um cliente.",
    }
}


def normalize_competency(comp: str) -> str:
    return comp.strip().lower()


def generate_question_for_skill(skill: str, skill_type: str = "technical") -> Optional[WSIQuestion]:
    templates = QUESTION_TEMPLATES.get(skill_type, {})
    skill_normalized = skill.strip()

    for template_skill, question in templates.items():
        if template_skill.lower() in skill_normalized.lower() or skill_normalized.lower() in template_skill.lower():
            return WSIQuestion(
                id=f"wsi-{skill_type}-{skill_normalized.lower().replace(' ', '-').replace('/', '-')}",
                question=question,
                type="open",
                required=True,
                competency_validated=skill_normalized,
                skill_type=skill_type
            )

    if skill_type == "technical":
        return WSIQuestion(
            id=f"wsi-tech-{skill_normalized.lower().replace(' ', '-').replace('/', '-')}",
            question=f"Descreva sua experiência com {skill_normalized}. Em quais projetos aplicou essa tecnologia?",
            type="open",
            required=True,
            competency_validated=skill_normalized,
            skill_type=skill_type
        )
    else:
        return WSIQuestion(
            id=f"wsi-behav-{skill_normalized.lower().replace(' ', '-').replace('/', '-')}",
            question=f"Conte sobre uma situação onde demonstrou {skill_normalized.lower()} no ambiente de trabalho.",
            type="open",
            required=True,
            competency_validated=skill_normalized,
            skill_type=skill_type
        )


def _generate_questions_from_templates(
    technical_skills: List[str],
    behavioral_competencies: List[str],
    max_questions: int
) -> List[WSIQuestion]:
    questions: List[WSIQuestion] = []

    for tmpl in ELIGIBILITY_TEMPLATES:
        questions.append(tmpl.model_copy())

    tech_target = min(max(MIN_TECHNICAL_QUESTIONS, len(technical_skills)), 5)
    for skill in technical_skills[:tech_target]:
        question = generate_question_for_skill(skill, "technical")
        if question:
            question.block_id = 3
            questions.append(question)

    behav_target = min(max(MIN_BEHAVIORAL_QUESTIONS, len(behavioral_competencies)), 3)
    for comp in behavioral_competencies[:behav_target]:
        question = generate_question_for_skill(comp, "behavioral")
        if question:
            question.block_id = 4
            questions.append(question)

    return questions[:max_questions]


async def _generate_questions_with_llm(
    job_title: str,
    technical_skills: List[str],
    behavioral_competencies: List[str],
    responsibilities: List[str],
    seniority: Optional[str],
    department: Optional[str],
    max_questions: int
) -> List[WSIQuestion]:
    elig_count = MIN_ELIGIBILITY_QUESTIONS
    tech_count = min(max(MIN_TECHNICAL_QUESTIONS, len(technical_skills)), max_questions - MIN_BEHAVIORAL_QUESTIONS - elig_count)
    behav_count = min(max(MIN_BEHAVIORAL_QUESTIONS, len(behavioral_competencies)), max_questions - tech_count - elig_count)
    total = elig_count + tech_count + behav_count

    system_prompt = f"""Você é especialista em metodologia WSI (WeDoTalent Skill Index) para triagem de candidatos.
Gere perguntas de triagem organizadas por blocos WSI para a vaga descrita.

METODOLOGIA WSI - BLOCOS DE TRIAGEM:

Bloco 2 - Elegibilidade WSI ({elig_count} perguntas):
- Perguntas eliminatórias e de fit básico
- Verificam disponibilidade, modelo de trabalho, pretensão salarial, localização
- Type: "eliminatory", category: "eligibility"
- Exemplo: "Qual sua disponibilidade para início? Existe algum período de aviso prévio?"
- Exemplo: "Esta posição é [remoto/híbrido/presencial] em [localização]. Isso é compatível com sua situação atual?"

Bloco 3 - Avaliação Técnica ({tech_count} perguntas):
- Perguntas abertas avaliando competências técnicas específicas
- Cada pergunta deve validar UMA skill técnica listada
- Type: "open", category: "technical"
- Calibrar complexidade pela senioridade

Bloco 4 - Análise Situacional e Fit ({behav_count} perguntas):
- Perguntas situacionais e comportamentais
- Testam competências comportamentais em cenários reais
- Type: "open", category: "behavioral" ou "situational"
- Incluir follow-ups implícitos (ex: "Qual foi o resultado?")

REGRAS OBRIGATÓRIAS:
1. Gere exatamente {elig_count} perguntas de elegibilidade (block_id: 2), {tech_count} perguntas técnicas (block_id: 3) e {behav_count} perguntas comportamentais (block_id: 4) ({total} total)
2. Perguntas de elegibilidade devem ser eliminatórias (type: "eliminatory")
3. Perguntas técnicas e comportamentais devem ser abertas (type: "open"), permitindo avaliação rica
4. As perguntas devem ser contextuais ao título, skills, responsabilidades e senioridade da vaga
5. Calibrar complexidade conforme senioridade: junior = conceitos básicos, senior = arquitetura e decisões
6. Cada pergunta técnica deve validar uma skill específica listada
7. Cada pergunta comportamental deve validar uma competência comportamental específica
8. Perguntas devem ser em português do Brasil

FORMATO DE SAÍDA (JSON array):
[
  {{
    "id": "wsi-block{{N}}-nome",
    "question": "texto da pergunta",
    "type": "open|eliminatory",
    "required": true,
    "competency_validated": "nome da skill/competência alvo",
    "skill_type": "technical|behavioral|eligibility",
    "block_id": 2|3|4
  }}
]"""

    context_parts = [f"Título da vaga: {job_title}"]
    if seniority:
        context_parts.append(f"Senioridade: {seniority}")
    if department:
        context_parts.append(f"Departamento: {department}")
    if responsibilities:
        context_parts.append(f"Responsabilidades: {', '.join(responsibilities[:10])}")
    if technical_skills:
        context_parts.append(f"Competências Técnicas ({len(technical_skills)}): {', '.join(technical_skills)}")
    if behavioral_competencies:
        context_parts.append(f"Competências Comportamentais ({len(behavioral_competencies)}): {', '.join(behavioral_competencies)}")

    user_prompt = f"""Gere as perguntas de triagem WSI para esta vaga:

{chr(10).join(context_parts)}

Gere {elig_count} perguntas de elegibilidade (bloco 2), {tech_count} perguntas técnicas (bloco 3) cobrindo as skills listadas e {behav_count} perguntas comportamentais (bloco 4) cobrindo as competências listadas.
Cada pergunta DEVE incluir o campo "block_id" correspondente ao seu bloco (2, 3 ou 4).
Responda APENAS com JSON array válido, sem markdown."""

    model = _get_gemini_model()
    response = model.generate_content(
        [{"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 4096,
        }
    )

    response_text = _clean_llm_json(response.text)
    raw_questions = json.loads(response_text)

    questions: List[WSIQuestion] = []
    for q in raw_questions:
        skill_type = q.get("skill_type", "technical")
        comp = q.get("competency_validated", "general")
        safe_id = comp.lower().replace(" ", "-").replace("/", "-")
        block_id = q.get("block_id")
        if block_id is None:
            if skill_type == "eligibility":
                block_id = 2
            elif skill_type == "technical":
                block_id = 3
            else:
                block_id = 4
        questions.append(WSIQuestion(
            id=q.get("id", f"wsi-{skill_type}-{safe_id}"),
            question=q.get("question", ""),
            type=q.get("type", "open"),
            required=q.get("required", True),
            competency_validated=comp,
            skill_type=skill_type,
            block_id=block_id
        ))

    return questions[:max_questions]


async def _generate_new_questions_with_llm(
    skills: List[str],
    skill_type: str,
    job_title: str,
    seniority: Optional[str]
) -> List[WSIQuestion]:
    if not skills:
        return []

    system_prompt = f"""Você é especialista em metodologia WSI para triagem de candidatos.
Gere perguntas de triagem abertas e contextuais para as competências listadas.

REGRAS:
1. Gere exatamente 1 pergunta por competência fornecida
2. Perguntas abertas, em português do Brasil
3. Tipo: {"técnica" if skill_type == "technical" else "comportamental"}
4. Calibrar para senioridade: {seniority or "não definida"}
5. Contextualizar para a vaga: {job_title}

FORMATO (JSON array):
[
  {{
    "id": "wsi-{skill_type}-nome",
    "question": "texto",
    "type": "open",
    "required": true,
    "competency_validated": "competência",
    "skill_type": "{skill_type}"
  }}
]"""

    user_prompt = f"""Competências para gerar perguntas: {', '.join(skills)}
Responda APENAS com JSON array válido, sem markdown."""

    model = _get_gemini_model()
    response = model.generate_content(
        [{"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 2048,
        }
    )

    response_text = _clean_llm_json(response.text)
    raw_questions = json.loads(response_text)

    questions: List[WSIQuestion] = []
    for q in raw_questions:
        comp = q.get("competency_validated", "general")
        safe_id = comp.lower().replace(" ", "-").replace("/", "-")
        questions.append(WSIQuestion(
            id=q.get("id", f"wsi-{skill_type}-{safe_id}"),
            question=q.get("question", ""),
            type=q.get("type", "open"),
            required=q.get("required", True),
            competency_validated=comp,
            skill_type=skill_type
        ))

    return questions


def validate_question_coverage(
    questions: List[WSIQuestion],
    technical_skills: List[str],
    behavioral_competencies: List[str]
) -> List[str]:
    warnings = []
    tech_questions = [q for q in questions if q.skill_type == "technical"]
    behav_questions = [q for q in questions if q.skill_type == "behavioral"]
    elig_questions = [q for q in questions if q.block_id == 2 or q.skill_type == "eligibility"]

    if len(elig_questions) < MIN_ELIGIBILITY_QUESTIONS:
        warnings.append(f"Apenas {len(elig_questions)} perguntas de elegibilidade. Recomendado: {MIN_ELIGIBILITY_QUESTIONS}+")

    if len(tech_questions) < MIN_TECHNICAL_QUESTIONS and len(technical_skills) >= MIN_TECHNICAL_QUESTIONS:
        warnings.append(f"Apenas {len(tech_questions)} perguntas técnicas geradas. Recomendado: {MIN_TECHNICAL_QUESTIONS}+")

    if len(behav_questions) < MIN_BEHAVIORAL_QUESTIONS and len(behavioral_competencies) >= MIN_BEHAVIORAL_QUESTIONS:
        warnings.append(f"Apenas {len(behav_questions)} perguntas comportamentais geradas. Recomendado: {MIN_BEHAVIORAL_QUESTIONS}+")

    return warnings


@router.post("/generate-questions", response_model=QuestionsResponse)
async def generate_wsi_questions(request: GenerateQuestionsRequest):
    """
    Generate WSI questions based on job competencies using Gemini LLM.
    Falls back to template-based generation if LLM is unavailable.
    """
    try:
        try:
            questions = await _generate_questions_with_llm(
                job_title=request.job_title,
                technical_skills=request.technical_skills,
                behavioral_competencies=request.behavioral_competencies,
                responsibilities=request.responsibilities,
                seniority=request.seniority,
                department=request.department,
                max_questions=request.max_questions
            )
            logger.info(f"Generated {len(questions)} WSI questions via Gemini LLM for '{request.job_title}'")
        except Exception as llm_error:
            logger.warning(f"LLM generation failed, falling back to templates: {llm_error}")
            questions = _generate_questions_from_templates(
                technical_skills=request.technical_skills,
                behavioral_competencies=request.behavioral_competencies,
                max_questions=request.max_questions
            )

        # A2/G1: FairnessGuard check on generated question texts
        filtered_questions: List[WSIQuestion] = []
        fg_removed = 0
        for q in questions:
            fg_result = check_fairness(
                {"question": q.question},
                context="wsi_question_generation",
                company_id=request.company_id,
            )
            if fg_result.is_blocked:
                logger.warning(
                    "[WSI][A2] FairnessGuard blocked question id=%s category=%s",
                    q.id, fg_result.blocked_result.category if fg_result.blocked_result else "unknown",
                )
                fg_removed += 1
            else:
                filtered_questions.append(q)

        if fg_removed:
            logger.info("[WSI][A2] %d question(s) removed by FairnessGuard", fg_removed)

        warnings = validate_question_coverage(
            filtered_questions,
            request.technical_skills,
            request.behavioral_competencies
        )
        if fg_removed:
            warnings.append(f"{fg_removed} pergunta(s) removida(s) pelo FairnessGuard por conterem viés discriminatório.")

        block_distribution = {}
        for q in filtered_questions:
            bid = q.block_id or (3 if q.skill_type == "technical" else 4)
            block_distribution[bid] = block_distribution.get(bid, 0) + 1

        return QuestionsResponse(
            success=True,
            questions=filtered_questions,
            questions_added=len(filtered_questions),
            questions_removed=fg_removed,
            quality_warnings=warnings,
            block_distribution=block_distribution
        )

    except Exception as e:
        logger.error(f"Error generating WSI questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate-questions", response_model=QuestionsResponse)
async def regenerate_wsi_questions(request: RegenerateQuestionsRequest):
    """
    Regenerate WSI questions when competencies change.

    Accepts full competency lists and computes diffs server-side:
    - Keeps questions for competencies still in the list
    - Removes questions for competencies no longer in the list
    - Generates new questions for new competencies via LLM
    - Ensures minimum WSI quality thresholds
    """
    try:
        current_questions = request.current_questions

        current_tech_set: Set[str] = {normalize_competency(c) for c in request.technical_skills}
        current_behav_set: Set[str] = {normalize_competency(c) for c in request.behavioral_competencies}
        all_current_competencies = current_tech_set | current_behav_set

        retained_questions: List[WSIQuestion] = []
        covered_competencies: Set[str] = set()
        removed_count = 0

        for q in current_questions:
            if q.competency_validated:
                comp_normalized = normalize_competency(q.competency_validated)
                if comp_normalized in all_current_competencies:
                    retained_questions.append(q)
                    covered_competencies.add(comp_normalized)
                else:
                    removed_count += 1
            else:
                retained_questions.append(q)

        new_tech = [s for s in request.technical_skills if normalize_competency(s) not in covered_competencies]
        new_behav = [s for s in request.behavioral_competencies if normalize_competency(s) not in covered_competencies]

        added_count = 0
        tech_count = sum(1 for q in retained_questions if q.skill_type == "technical")
        behav_count = sum(1 for q in retained_questions if q.skill_type == "behavioral")

        tech_needed = max(0, MIN_TECHNICAL_QUESTIONS - tech_count)
        tech_to_generate = new_tech[:max(tech_needed, 2)]
        behav_needed = max(0, MIN_BEHAVIORAL_QUESTIONS - behav_count)
        behav_to_generate = new_behav[:max(behav_needed, 1)]

        try:
            if tech_to_generate:
                new_tech_questions = await _generate_new_questions_with_llm(
                    skills=tech_to_generate,
                    skill_type="technical",
                    job_title=request.job_title,
                    seniority=request.seniority
                )
                for q in new_tech_questions:
                    if len(retained_questions) < request.max_questions:
                        retained_questions.append(q)
                        covered_competencies.add(normalize_competency(q.competency_validated or ""))
                        added_count += 1

            if behav_to_generate:
                new_behav_questions = await _generate_new_questions_with_llm(
                    skills=behav_to_generate,
                    skill_type="behavioral",
                    job_title=request.job_title,
                    seniority=request.seniority
                )
                for q in new_behav_questions:
                    if len(retained_questions) < request.max_questions:
                        retained_questions.append(q)
                        covered_competencies.add(normalize_competency(q.competency_validated or ""))
                        added_count += 1

        except Exception as llm_error:
            logger.warning(f"LLM regeneration failed, falling back to templates: {llm_error}")
            for skill in tech_to_generate:
                if len(retained_questions) < request.max_questions:
                    question = generate_question_for_skill(skill, "technical")
                    if question:
                        retained_questions.append(question)
                        covered_competencies.add(normalize_competency(skill))
                        added_count += 1

            for comp in behav_to_generate:
                if len(retained_questions) < request.max_questions:
                    question = generate_question_for_skill(comp, "behavioral")
                    if question:
                        retained_questions.append(question)
                        covered_competencies.add(normalize_competency(comp))
                        added_count += 1

        changes = []
        if added_count > 0:
            changes.append(f"Adicionadas {added_count} novas perguntas")
        if removed_count > 0:
            changes.append(f"Removidas {removed_count} perguntas de competências não mais selecionadas")

        warnings = validate_question_coverage(
            retained_questions,
            request.technical_skills,
            request.behavioral_competencies
        )

        return QuestionsResponse(
            success=True,
            questions=retained_questions,
            changes_summary=". ".join(changes) if changes else "Nenhuma alteração necessária",
            questions_added=added_count,
            questions_removed=removed_count,
            quality_warnings=warnings
        )

    except Exception as e:
        logger.error(f"Error regenerating WSI questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/question-templates")
async def get_question_templates():
    """
    Get available question templates for reference.
    """
    return {
        "success": True,
        "templates": QUESTION_TEMPLATES,
        "supported_technical": list(QUESTION_TEMPLATES.get("technical", {}).keys()),
        "supported_behavioral": list(QUESTION_TEMPLATES.get("behavioral", {}).keys()),
        "minimums": {
            "technical": MIN_TECHNICAL_QUESTIONS,
            "behavioral": MIN_BEHAVIORAL_QUESTIONS
        }
    }
