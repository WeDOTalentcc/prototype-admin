from app.domains.base import DomainAction

INTERVIEW_INTELLIGENCE_ACTIONS: list[DomainAction] = [
    DomainAction(name="analyze_interview_recording", description="Análise completa de entrevista (WSI, Dreyfus, CBI, Big Five, viés)", requires_confirmation=False),
    DomainAction(name="detect_interview_bias", description="Detectar viés na condução da entrevista", requires_confirmation=False),
    DomainAction(name="compare_interview_performance", description="Comparar performance entre candidatos entrevistados", requires_confirmation=False),
    DomainAction(name="generate_interview_opinion", description="Gerar parecer estratégico de entrevista", requires_confirmation=False),
    DomainAction(name="generate_candidate_feedback", description="Gerar feedback construtivo ao candidato", requires_confirmation=False),
]
