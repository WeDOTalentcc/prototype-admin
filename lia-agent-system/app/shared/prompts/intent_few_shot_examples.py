"""
Few-Shot Examples para Tier 3 do Orchestrator (LLM Router) — Sprint J2

Exemplos co-criados para cobrir os 7 domínios de agentes da LIA.
Formato estruturado para validação por profissional sênior de RH.

Cobertura:
- 10 casos CLAROS (confiança esperada ≥ 0.85 → roteamento direto)
- 10 casos AMBÍGUOS (confiança esperada ≤ 0.55 → deve pedir esclarecimento)
- 7 domínios: wizard, cv_screening, kanban, sourcing, job_management, communication, policy

Referência: docs/analises/PLANO_IMPLEMENTACAO_GAPS_IA.md → Sprint J2
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FewShotExample:
    message: str
    intent: str
    domain: str | None
    confidence: float           # Score esperado pelo avaliador humano
    notes: str = ""             # Anotações do especialista de RH


# ---------------------------------------------------------------------------
# Casos CLAROS — confiança esperada ≥ 0.85
# ---------------------------------------------------------------------------

CLEAR_EXAMPLES: list[FewShotExample] = [
    FewShotExample(
        message="preciso criar uma nova vaga de desenvolvedor backend sênior para o time de plataforma",
        intent="job_wizard",
        domain="job_management",
        confidence=0.95,
        notes="cargo específico + senioridade + contexto claro → wizard",
    ),
    FewShotExample(
        message="analisa o currículo do João Silva para a vaga de analista de dados",
        intent="cv_screening",
        domain="cv_screening",
        confidence=0.95,
        notes="candidato específico + vaga específica + verbo 'analisar' → triagem",
    ),
    FewShotExample(
        message="busca desenvolvedores fullstack no mercado com experiência em React e Node",
        intent="sourcing",
        domain="sourcing",
        confidence=0.92,
        notes="busca externa de candidatos com stack explícito → sourcing",
    ),
    FewShotExample(
        message="quais candidatos estão parados há mais de 7 dias no pipeline da vaga de gerente",
        intent="kanban_analysis",
        domain="pipeline",
        confidence=0.90,
        notes="análise de pipeline com critério temporal → kanban/pipeline",
    ),
    FewShotExample(
        message="qual o status de todas as vagas abertas do departamento de engenharia",
        intent="jobs_status",
        domain="job_management",
        confidence=0.90,
        notes="consulta de status de vagas → job management",
    ),
    FewShotExample(
        message="manda um email de feedback para os candidatos reprovados na triagem da vaga 123",
        intent="send_feedback_email",
        domain="communication",
        confidence=0.93,
        notes="ação de comunicação específica com candidatos reprovados → communication",
    ),
    FewShotExample(
        message="quais são as regras de compliance para movimentação de candidatos no pipeline",
        intent="policy_query",
        domain="policy",
        confidence=0.88,
        notes="consulta de regras/política → policy agent",
    ),
    FewShotExample(
        message="agendar entrevista técnica com a Maria Souza para quinta-feira às 14h",
        intent="schedule_interview",
        domain="scheduling",
        confidence=0.94,
        notes="agendamento com nome, tipo e horário específico → scheduling",
    ),
    FewShotExample(
        message="disparar triagem automática WSI para os 15 novos candidatos da vaga de vendas",
        intent="disparar_triagem",
        domain="cv_screening",
        confidence=0.91,
        notes="ação específica de triagem em lote → cv_screening",
    ),
    FewShotExample(
        message="como está o funil de conversão da vaga de product manager? quantos chegaram em cada etapa",
        intent="analise_funil",
        domain="pipeline",
        confidence=0.89,
        notes="análise de funil com métricas → kanban/pipeline analytics",
    ),
]


# ---------------------------------------------------------------------------
# Casos AMBÍGUOS — confiança esperada ≤ 0.55 → deve pedir esclarecimento
# ---------------------------------------------------------------------------

AMBIGUOUS_EXAMPLES: list[FewShotExample] = [
    FewShotExample(
        message="vou precisar contratar alguém",
        intent="clarification_needed",
        domain=None,
        confidence=0.35,
        notes="sem cargo, sem contexto — pode ser wizard ou sourcing. Deve pedir esclarecimento",
    ),
    FewShotExample(
        message="o que você acha desse candidato",
        intent="clarification_needed",
        domain=None,
        confidence=0.40,
        notes="sem candidato específico, sem vaga. Pode ser screening ou kanban. Ambíguo",
    ),
    FewShotExample(
        message="como estão as vagas",
        intent="clarification_needed",
        domain=None,
        confidence=0.45,
        notes="pode ser job_management (status) ou kanban (pipeline). Contexto insuficiente",
    ),
    FewShotExample(
        message="preciso de candidatos",
        intent="clarification_needed",
        domain=None,
        confidence=0.40,
        notes="pode ser sourcing (buscar novos) ou kanban (ver os atuais). Ambíguo",
    ),
    FewShotExample(
        message="avisa o candidato",
        intent="clarification_needed",
        domain=None,
        confidence=0.35,
        notes="sem candidato, sem assunto. Pode ser email, WhatsApp ou Teams. Muito ambíguo",
    ),
    FewShotExample(
        message="como funciona nossa seleção",
        intent="clarification_needed",
        domain=None,
        confidence=0.50,
        notes="pode ser policy (regras) ou onboarding (entender processo). Contexto duplo",
    ),
    FewShotExample(
        message="ajuda com a vaga",
        intent="clarification_needed",
        domain=None,
        confidence=0.30,
        notes="completamente vago. Qual vaga? Que tipo de ajuda? Deve pedir esclarecimento",
    ),
    FewShotExample(
        message="analisa isso",
        intent="clarification_needed",
        domain=None,
        confidence=0.25,
        notes="sem referente. 'Isso' pode ser um CV, pipeline, vaga ou relatório. Mínimo contexto",
    ),
    FewShotExample(
        message="quero saber mais sobre os candidatos",
        intent="clarification_needed",
        domain=None,
        confidence=0.45,
        notes="pode ser sourcing (busca), kanban (pipeline) ou cv_screening. Ambíguo sem vaga",
    ),
    FewShotExample(
        message="preciso fechar essa vaga logo",
        intent="clarification_needed",
        domain=None,
        confidence=0.50,
        notes="urgência clara, mas sem ação definida. Pipeline aceleration? Sourcing? Triagem rápida?",
    ),
]


# ---------------------------------------------------------------------------
# Export consolidado
# ---------------------------------------------------------------------------

FEW_SHOT_EXAMPLES: list[FewShotExample] = CLEAR_EXAMPLES + AMBIGUOUS_EXAMPLES

CLEAR_INTENTS = {e.intent for e in CLEAR_EXAMPLES if e.intent != "clarification_needed"}
COVERED_DOMAINS = {e.domain for e in FEW_SHOT_EXAMPLES if e.domain is not None}

REQUIRED_DOMAINS = {
    "job_management",
    "cv_screening",
    "sourcing",
    "pipeline",
    "communication",
    "policy",
    "scheduling",
}
