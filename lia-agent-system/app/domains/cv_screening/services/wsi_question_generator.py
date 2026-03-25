"""
WSI-based Screening Question Generator Service.

Generates scientific interview questions based on:
1. Big Five personality model
2. Bloom's Taxonomy
3. Dreyfus Model of skill acquisition
4. CBI (Competency-Based Interviewing)
"""
from typing import List, Dict, Optional, Literal, Any
import uuid
import logging

from app.schemas.screening import (
    ScreeningQuestionRequest,
    ScreeningQuestion,
    ScreeningQuestionResponse,
    BigFiveProfile
)
from app.services.seniority_context_calibrator import (
    calibrate_or_fallback,
    CalibrationContext,
    CalibrationResult,
    WSI_CONTEXTUAL_CALIBRATION_ENABLED,
)
from app.services.seniority_utils import normalize_seniority

logger = logging.getLogger(__name__)

BLOOM_LEVELS = {
    1: "Lembrar",
    2: "Compreender",
    3: "Aplicar",
    4: "Analisar",
    5: "Avaliar",
    6: "Criar"
}

DREYFUS_STAGES = {
    1: "Novato",
    2: "Iniciante Avançado",
    3: "Competente",
    4: "Proficiente",
    5: "Especialista"
}

SENIORITY_TO_DREYFUS = {
    "junior": 2,
    "pleno": 3,
    "senior": 4,
    "lead": 5,
    "executive": 5
}

SENIORITY_TO_BLOOM = {
    "junior": [1, 2, 3],
    "pleno": [3, 4],
    "senior": [4, 5],
    "lead": [5, 6],
    "executive": [5, 6]
}

BIG_FIVE_QUESTIONS = {
    "openness": [
        {
            "text": "Descreva uma situação onde você propôs uma solução inovadora para um problema no trabalho. O que motivou sua ideia e qual foi o resultado?",
            "expected_signals": ["Criatividade", "Iniciativa", "Abertura a novas ideias"],
            "threshold": 60
        },
        {
            "text": "Conte sobre uma vez em que você precisou aprender uma tecnologia ou metodologia completamente nova. Como você abordou esse aprendizado?",
            "expected_signals": ["Curiosidade intelectual", "Adaptabilidade", "Proatividade no aprendizado"],
            "threshold": 50
        },
        {
            "text": "Você já questionou um processo estabelecido e sugeriu uma mudança? Como foi essa experiência?",
            "expected_signals": ["Pensamento crítico", "Coragem para inovar", "Capacidade de argumentação"],
            "threshold": 70
        }
    ],
    "conscientiousness": [
        {
            "text": "Como você organiza e prioriza múltiplas tarefas quando tem vários projetos simultâneos? Dê um exemplo concreto.",
            "expected_signals": ["Organização", "Planejamento", "Gestão de tempo"],
            "threshold": 60
        },
        {
            "text": "Descreva uma situação onde você precisou entregar um projeto com alta qualidade sob pressão de prazo. Como garantiu a qualidade?",
            "expected_signals": ["Atenção a detalhes", "Comprometimento", "Resiliência"],
            "threshold": 50
        },
        {
            "text": "Conte sobre um projeto de longo prazo que você gerenciou do início ao fim. Como manteve o foco e a consistência?",
            "expected_signals": ["Persistência", "Disciplina", "Foco em resultados"],
            "threshold": 70
        }
    ],
    "extraversion": [
        {
            "text": "Conte sobre uma experiência liderando uma equipe ou conduzindo uma reunião importante. Como você engajou os participantes?",
            "expected_signals": ["Liderança", "Comunicação", "Energia social"],
            "threshold": 60
        },
        {
            "text": "Descreva uma situação onde você precisou influenciar ou convencer colegas sobre uma ideia. Qual foi sua abordagem?",
            "expected_signals": ["Persuasão", "Assertividade", "Habilidades interpessoais"],
            "threshold": 50
        },
        {
            "text": "Como você contribui para manter o moral e a motivação da equipe em momentos desafiadores?",
            "expected_signals": ["Energia positiva", "Colaboração", "Empatia ativa"],
            "threshold": 70
        }
    ],
    "agreeableness": [
        {
            "text": "Descreva como você lidou com um conflito na equipe. Qual foi seu papel na resolução?",
            "expected_signals": ["Mediação", "Empatia", "Colaboração"],
            "threshold": 60
        },
        {
            "text": "Conte sobre uma vez em que você ajudou um colega a superar uma dificuldade profissional. O que você fez?",
            "expected_signals": ["Suporte", "Altruísmo", "Trabalho em equipe"],
            "threshold": 50
        },
        {
            "text": "Como você reage quando recebe feedback crítico sobre seu trabalho? Dê um exemplo.",
            "expected_signals": ["Receptividade", "Humildade", "Abertura para crescimento"],
            "threshold": 40
        }
    ],
    "stability": [
        {
            "text": "Como você lida com situações de alta pressão e prazos curtos? Descreva uma experiência específica.",
            "expected_signals": ["Calma sob pressão", "Resiliência", "Autocontrole"],
            "threshold": 60
        },
        {
            "text": "Conte sobre uma situação onde um projeto não saiu como planejado. Como você reagiu e se recuperou?",
            "expected_signals": ["Adaptabilidade", "Equilíbrio emocional", "Foco em soluções"],
            "threshold": 50
        },
        {
            "text": "Descreva como você mantém o equilíbrio emocional em situações de incerteza ou mudanças constantes.",
            "expected_signals": ["Estabilidade", "Maturidade", "Gestão de estresse"],
            "threshold": 70
        }
    ]
}

TECHNICAL_QUESTION_TEMPLATES = {
    "junior": [
        {
            "template": "Você já utilizou {skill} em algum projeto ou estudo? Descreva sua experiência e o que aprendeu.",
            "bloom_level": 2,
            "framework": "CBI"
        },
        {
            "template": "Qual foi o maior desafio que você enfrentou ao aprender {skill}? Como você superou?",
            "bloom_level": 3,
            "framework": "CBI"
        }
    ],
    "pleno": [
        {
            "template": "Descreva um projeto onde você utilizou {skill} de forma significativa. Qual foi o contexto, sua ação e o resultado?",
            "bloom_level": 4,
            "framework": "CBI"
        },
        {
            "template": "Qual foi o maior desafio técnico que você enfrentou com {skill}? Como você diagnosticou e resolveu o problema?",
            "bloom_level": 4,
            "framework": "CBI"
        },
        {
            "template": "Compare diferentes abordagens ou ferramentas relacionadas a {skill}. Em que situações você usaria cada uma?",
            "bloom_level": 5,
            "framework": "Bloom"
        }
    ],
    "senior": [
        {
            "template": "Descreva uma arquitetura ou solução complexa que você projetou usando {skill}. Quais trade-offs você considerou?",
            "bloom_level": 5,
            "framework": "CBI"
        },
        {
            "template": "Como você avalia e decide a melhor abordagem técnica ao usar {skill}? Dê um exemplo de uma decisão difícil.",
            "bloom_level": 5,
            "framework": "Bloom"
        },
        {
            "template": "Conte sobre uma vez em que você mentorou alguém em {skill}. Como você estruturou o ensino?",
            "bloom_level": 6,
            "framework": "Dreyfus"
        }
    ],
    "lead": [
        {
            "template": "Descreva como você definiu padrões ou diretrizes técnicas relacionadas a {skill} para sua equipe ou empresa.",
            "bloom_level": 6,
            "framework": "CBI"
        },
        {
            "template": "Qual foi a decisão arquitetural mais impactante que você tomou envolvendo {skill}? Quais foram os resultados a longo prazo?",
            "bloom_level": 6,
            "framework": "Bloom"
        }
    ],
    "executive": [
        {
            "template": "Como você avalia a adoção de novas tecnologias como {skill} em uma organização? Quais fatores você considera?",
            "bloom_level": 6,
            "framework": "Bloom"
        },
        {
            "template": "Descreva uma estratégia técnica que você liderou envolvendo {skill}. Qual foi o impacto no negócio?",
            "bloom_level": 6,
            "framework": "CBI"
        }
    ]
}


def _build_calibration_context(context, seniority: str) -> CalibrationContext:
    """Build calibration context from question generation context."""
    skills = []
    if hasattr(context, 'competencies') and context.competencies:
        skills = [c.name for c in context.competencies if hasattr(c, 'name')]
    elif hasattr(context, 'skills') and context.skills:
        skills = context.skills

    return CalibrationContext(
        seniority=seniority,
        job_title=getattr(context, 'title', '') or '',
        department=getattr(context, 'department', None),
        industry=getattr(context, 'industry', None),
        country=getattr(context, 'country', None),
        location=getattr(context, 'location', None),
        required_skills=skills,
        salary_min=getattr(context, 'salary_min', None),
        salary_max=getattr(context, 'salary_max', None),
        company_size=getattr(context, 'company_size', None),
    )


class WSIScreeningQuestionGenerator:
    """
    Generates WSI-based screening questions using scientific frameworks.
    """
    
    def __init__(self):
        pass
    
    def generate_questions(self, context: ScreeningQuestionRequest) -> ScreeningQuestionResponse:
        """
        Generate screening questions based on job context.
        
        Args:
            context: Job context including title, seniority, skills, and Big Five profile
            
        Returns:
            ScreeningQuestionResponse with categorized questions
        """
        behavioral_questions = self._generate_behavioral_questions(context)
        technical_questions = self._generate_technical_questions(context)
        cultural_questions = self._generate_cultural_questions(context)
        
        all_questions = behavioral_questions + technical_questions + cultural_questions
        
        for i, q in enumerate(all_questions):
            q.order = i
        
        target_count = context.question_count
        if len(all_questions) > target_count:
            behavioral_count = max(2, target_count // 3)
            technical_count = max(2, (target_count - behavioral_count) * 2 // 3)
            cultural_count = target_count - behavioral_count - technical_count
            
            all_questions = (
                behavioral_questions[:behavioral_count] +
                technical_questions[:technical_count] +
                cultural_questions[:cultural_count]
            )
        
        _cal_result: Optional[CalibrationResult] = None
        if WSI_CONTEXTUAL_CALIBRATION_ENABLED:
            _cal_ctx = _build_calibration_context(context, context.seniority)
            _cal_result = calibrate_or_fallback(_cal_ctx)
            dreyfus_stage = _cal_result.dreyfus_target
            bloom_levels = _cal_result.bloom_levels
        else:
            dreyfus_stage = SENIORITY_TO_DREYFUS.get(context.seniority, 3)
            bloom_levels = SENIORITY_TO_BLOOM.get(context.seniority, [3, 4])

        metadata: Dict[str, Any] = {
            "seniority": context.seniority,
            "dreyfus_stage": dreyfus_stage,
            "bloom_levels": bloom_levels,
            "skills_count": len(context.skills),
            "title": context.title,
            "department": context.department
        }
        if _cal_result is not None:
            metadata["calibration"] = {
                "area_maturity": _cal_result.area_maturity,
                "dreyfus_target": _cal_result.dreyfus_target,
                "bloom_levels": _cal_result.bloom_levels,
                "years_reference": _cal_result.years_reference,
                "confidence": _cal_result.confidence,
                "area_profile_id": _cal_result.area_profile_id,
            }

        return ScreeningQuestionResponse(
            questions=all_questions,
            behavioral_questions=behavioral_questions,
            technical_questions=technical_questions,
            cultural_questions=cultural_questions,
            total_count=len(all_questions),
            metadata=metadata
        )
    
    def _generate_behavioral_questions(
        self,
        context: ScreeningQuestionRequest
    ) -> List[ScreeningQuestion]:
        """Generate Big Five based behavioral questions."""
        questions = []
        profile = context.big_five_profile or BigFiveProfile()
        if WSI_CONTEXTUAL_CALIBRATION_ENABLED:
            _cal_ctx = _build_calibration_context(context, context.seniority)
            _cal_result = calibrate_or_fallback(_cal_ctx)
            dreyfus_stage = _cal_result.dreyfus_target
            bloom_levels = _cal_result.bloom_levels
        else:
            dreyfus_stage = SENIORITY_TO_DREYFUS.get(context.seniority, 3)
            bloom_levels = SENIORITY_TO_BLOOM.get(context.seniority, [3, 4])
        
        trait_scores = {
            "openness": profile.openness,
            "conscientiousness": profile.conscientiousness,
            "extraversion": profile.extraversion,
            "agreeableness": profile.agreeableness,
            "stability": profile.stability
        }
        
        sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)
        
        target_behavioral = context.question_count or 3
        top_n = min(max(3, target_behavioral), 5)
        for trait, score in sorted_traits[:top_n]:
            trait_questions = BIG_FIVE_QUESTIONS.get(trait, [])
            
            for q_data in trait_questions:
                if score >= q_data.get("threshold", 50):
                    bloom_level = bloom_levels[0] if bloom_levels else 3
                    
                    question = ScreeningQuestion(
                        id=str(uuid.uuid4()),
                        text=q_data["text"],
                        category="behavioral",
                        trait=trait,
                        skill=None,
                        bloom_level=bloom_level,
                        bloom_label=BLOOM_LEVELS.get(bloom_level, "Aplicar"),
                        dreyfus_stage=dreyfus_stage,
                        dreyfus_label=DREYFUS_STAGES.get(dreyfus_stage, "Competente"),
                        framework="BigFive",
                        weight=0.8 if score >= 70 else 0.6,
                        expected_signals=q_data.get("expected_signals", []),
                        scoring_criteria={
                            "5": "Exemplo detalhado com impacto mensurável e reflexão profunda",
                            "4": "Exemplo claro com ação específica e resultado visível",
                            "3": "Exemplo básico com contexto e ação identificáveis",
                            "2": "Exemplo vago ou genérico sem detalhes concretos",
                            "1": "Sem exemplo ou resposta irrelevante"
                        },
                        is_selected=True,
                        order=0
                    )
                    questions.append(question)
                    break
        
        return questions
    
    def _generate_technical_questions(
        self,
        context: ScreeningQuestionRequest
    ) -> List[ScreeningQuestion]:
        """Generate CBI-style technical questions based on skills."""
        questions = []
        seniority = context.seniority or "pleno"
        templates = TECHNICAL_QUESTION_TEMPLATES.get(seniority, TECHNICAL_QUESTION_TEMPLATES["pleno"])
        if WSI_CONTEXTUAL_CALIBRATION_ENABLED:
            _cal_ctx = _build_calibration_context(context, seniority)
            _cal_result = calibrate_or_fallback(_cal_ctx)
            dreyfus_stage = _cal_result.dreyfus_target
        else:
            dreyfus_stage = SENIORITY_TO_DREYFUS.get(seniority, 3)
        
        skills = context.skills if context.skills else []
        target_count = context.question_count or len(skills) or 5

        skill_queue = []
        if skills:
            if len(skills) >= target_count:
                skill_queue = [(s, 0) for s in skills[:target_count]]
            else:
                base_per_skill = target_count // len(skills)
                remainder = target_count % len(skills)
                for idx, skill in enumerate(skills):
                    reps = base_per_skill + (1 if idx < remainder else 0)
                    for r in range(reps):
                        skill_queue.append((skill, r))

        for i, (skill, variation) in enumerate(skill_queue):
            template_data = templates[(i + variation) % len(templates)]
            bloom_level = template_data.get("bloom_level", 3)
            if variation > 0:
                bloom_offset = variation % 3
                bloom_level = max(1, min(6, bloom_level + bloom_offset))

            question = ScreeningQuestion(
                id=str(uuid.uuid4()),
                text=template_data["template"].format(skill=skill),
                category="technical",
                trait=None,
                skill=skill,
                bloom_level=bloom_level,
                bloom_label=BLOOM_LEVELS.get(bloom_level, "Aplicar"),
                dreyfus_stage=dreyfus_stage,
                dreyfus_label=DREYFUS_STAGES.get(dreyfus_stage, "Competente"),
                framework=template_data.get("framework", "CBI"),
                weight=0.9,
                expected_signals=[
                    f"Conhecimento técnico em {skill}",
                    "Experiência prática",
                    "Capacidade de resolução de problemas"
                ],
                scoring_criteria={
                    "5": f"Projeto complexo com decisões avançadas em {skill}",
                    "4": f"Projeto real com aplicação significativa de {skill}",
                    "3": f"Experiência básica com {skill} em contexto prático",
                    "2": f"Conhecimento teórico de {skill} sem aplicação clara",
                    "1": f"Sem experiência relevante com {skill}"
                },
                is_selected=True,
                order=0
            )
            questions.append(question)

        return questions
    
    def _generate_cultural_questions(
        self,
        context: ScreeningQuestionRequest
    ) -> List[ScreeningQuestion]:
        """Generate cultural fit questions based on department and role."""
        questions = []
        if WSI_CONTEXTUAL_CALIBRATION_ENABLED:
            _cal_ctx = _build_calibration_context(context, context.seniority)
            _cal_result = calibrate_or_fallback(_cal_ctx)
            dreyfus_stage = _cal_result.dreyfus_target
            bloom_levels = _cal_result.bloom_levels
        else:
            dreyfus_stage = SENIORITY_TO_DREYFUS.get(context.seniority, 3)
            bloom_levels = SENIORITY_TO_BLOOM.get(context.seniority, [3, 4])
        
        cultural_templates = [
            {
                "text": "O que você busca em uma cultura de empresa? Quais valores são importantes para você?",
                "signals": ["Alinhamento de valores", "Autoconhecimento", "Clareza de expectativas"]
            },
            {
                "text": "Descreva o ambiente de trabalho ideal para você. Como você contribui para criar esse ambiente?",
                "signals": ["Colaboração", "Proatividade", "Adaptabilidade"]
            },
            {
                "text": f"Por que você se interessou pela posição de {context.title}? O que te atraiu nessa oportunidade?",
                "signals": ["Motivação genuína", "Conhecimento da vaga", "Alinhamento de objetivos"]
            }
        ]
        
        for i, template in enumerate(cultural_templates[:2]):
            bloom_level = bloom_levels[0] if bloom_levels else 3
            
            question = ScreeningQuestion(
                id=str(uuid.uuid4()),
                text=template["text"],
                category="cultural",
                trait=None,
                skill=None,
                bloom_level=bloom_level,
                bloom_label=BLOOM_LEVELS.get(bloom_level, "Aplicar"),
                dreyfus_stage=dreyfus_stage,
                dreyfus_label=DREYFUS_STAGES.get(dreyfus_stage, "Competente"),
                framework="CBI",
                weight=0.7,
                expected_signals=template.get("signals", []),
                scoring_criteria={
                    "5": "Resposta autêntica com exemplos e reflexão profunda",
                    "4": "Resposta clara com autoconhecimento evidente",
                    "3": "Resposta básica com pontos relevantes",
                    "2": "Resposta genérica sem profundidade",
                    "1": "Resposta evasiva ou desalinhada"
                },
                is_selected=True,
                order=0
            )
            questions.append(question)
        
        return questions
    
    def regenerate_category(
        self,
        context: ScreeningQuestionRequest,
        category: str,
        exclude_ids: List[str] = []
    ) -> List[ScreeningQuestion]:
        """
        Regenerate questions for a specific category.
        
        Args:
            context: Job context
            category: Category to regenerate (behavioral, technical, cultural)
            exclude_ids: Question IDs to exclude from regeneration
            
        Returns:
            New list of questions for the category
        """
        if category == "behavioral":
            questions = self._generate_behavioral_questions(context)
        elif category == "technical":
            questions = self._generate_technical_questions(context)
        elif category == "cultural":
            questions = self._generate_cultural_questions(context)
        else:
            questions = []
        
        filtered = [q for q in questions if q.id not in exclude_ids]
        
        return filtered


wsi_screening_generator = WSIScreeningQuestionGenerator()
