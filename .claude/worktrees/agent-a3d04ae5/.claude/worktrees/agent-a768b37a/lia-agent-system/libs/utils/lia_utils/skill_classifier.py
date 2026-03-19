"""
Skill classification utility for separating technical and soft skills.
"""
from typing import List, Tuple

SOFT_SKILLS = {
    "comunicação", "communication", "oratória", "public speaking", "apresentação",
    "negociação", "negotiation", "persuasão", "storytelling", "escuta ativa",
    "liderança", "leadership", "gestão de equipe", "team management", "mentoria",
    "mentoring", "coaching", "delegação", "tomada de decisão", "decision making",
    "trabalho em equipe", "teamwork", "colaboração", "collaboration", "empatia",
    "empathy", "relacionamento interpessoal", "networking", "influência",
    "resolução de problemas", "problem solving", "pensamento crítico",
    "critical thinking", "pensamento analítico", "analytical thinking",
    "criatividade", "creativity", "inovação", "innovation",
    "organização", "organization", "gestão de tempo", "time management",
    "planejamento", "planning", "priorização", "multitarefa", "multitasking",
    "adaptabilidade", "adaptability", "flexibilidade", "flexibility",
    "resiliência", "resilience", "aprendizado contínuo", "proatividade",
    "proactive", "iniciativa", "initiative", "autonomia",
    "inteligência emocional", "emotional intelligence", "autoconhecimento",
    "self-awareness", "autogestão", "controle emocional", "motivação",
    "ética", "ethics", "profissionalismo", "responsabilidade", "comprometimento",
    "commitment", "pontualidade", "atenção a detalhes", "attention to detail",
    "orientação a resultados", "result-oriented", "foco em resultados"
}


def normalize_skill(skill: str) -> str:
    """Normalize skill name for comparison."""
    return skill.lower().strip()


def classify_skills(skills: List[str]) -> Tuple[List[str], List[str]]:
    """
    Classify skills into technical and soft skills.
    Uses EXACT matching (case-insensitive) to avoid false positives.

    Args:
        skills: List of skill names

    Returns:
        Tuple of (technical_skills, soft_skills)
    """
    technical = []
    soft = []

    soft_skills_normalized = {s.lower().strip() for s in SOFT_SKILLS}

    for skill in skills:
        normalized = skill.lower().strip()
        if normalized in soft_skills_normalized:
            soft.append(skill)
        else:
            technical.append(skill)

    return technical, soft
