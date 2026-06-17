from app.domains.base import DomainAction

TALENT_INTELLIGENCE_ACTIONS: list[DomainAction] = [
    DomainAction(name="infer_related_skills", description="Inferir skills relacionadas via grafo de ontologia", requires_confirmation=False),
    DomainAction(name="get_skill_adjacencies", description="Obter skills adjacentes com pesos de proximidade", requires_confirmation=False),
    DomainAction(name="analyze_skill_gaps", description="Analisar gaps de skills entre candidato e vaga", requires_confirmation=False),
    DomainAction(name="map_candidate_skills_to_ontology", description="Mapear skills brutas para nós canônicos da ontologia", requires_confirmation=False),
    DomainAction(name="match_internal_candidates", description="Buscar candidatos internos para mobilidade interna", requires_confirmation=False),
    DomainAction(name="forecast_hiring_needs", description="Prever necessidades de contratação por período/departamento", requires_confirmation=False),
]
