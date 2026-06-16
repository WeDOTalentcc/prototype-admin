"""
Evaluation Criteria Service for André's methodology - Phase 3.

Seeds evaluation criteria from existing catalogs, provides fuzzy lookup
for job requirements, and updates effectiveness based on recruiter feedback.
"""
import logging
from difflib import SequenceMatcher
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.cv_screening.repositories.evaluation_criteria_repository import EvaluationCriteriaRepository

from lia_models.evaluation_criteria import CriterionCategory, EvaluationCriteria
from app.shared.services.responsibilities_catalog_service import RESPONSIBILITIES_CATALOG
from app.shared.services.skills_catalog_service import (
    BEHAVIORAL_COMPETENCIES_CATALOG,
    TECH_SKILLS_CATALOG,
)

logger = logging.getLogger(__name__)
from app.shared.compliance import scoring_safeguards as _ss
from app.shared.compliance.scoring_safeguards import FairnessBlockedError


EVIDENCE_PATTERNS: dict[str, dict[str, Any]] = {
    "technical_skill": {
        "positive_templates": [
            "{years}+ anos de experiência com {skill} em produção",
            "Projetos com {skill} listados com detalhes técnicos e resultados",
            "Certificações reconhecidas em {skill}",
            "Contribuições open source ou publicações técnicas sobre {skill}",
            "Uso de {skill} em contexto de alta escala ou missão crítica",
        ],
        "negative_templates": [
            "{skill} mencionado apenas em lista de skills sem contexto",
            "Apenas cursos online ou tutoriais de {skill}",
            "{skill} como skill secundária sem evidência de uso profissional",
            "Experiência com {skill} limitada a projetos acadêmicos",
            "Menção vaga a {skill} sem período ou contexto de uso",
        ],
        "guideline_template": (
            "Avaliar evidências concretas de uso profissional de {skill}. "
            "Priorizar experiência em produção, contribuições mensuráveis e certificações. "
            "Descontar menções sem contexto ou apenas formação sem prática."
        ),
        "years": "3",
    },
    "behavioral_competency": {
        "positive_templates": [
            "Exemplos concretos de {skill} com métricas e resultados",
            "Gestão direta de equipe ou projeto demonstrando {skill}",
            "Resultados mensuráveis atribuídos a {skill}",
            "Promoções ou reconhecimentos por demonstrar {skill}",
            "Histórico consistente de {skill} em múltiplas posições",
        ],
        "negative_templates": [
            "Apenas menciona {skill} sem exemplos concretos",
            "Auto-declaração de {skill} sem evidências ou contexto",
            "{skill} mencionado de forma genérica sem resultados",
            "Apenas referência informal a {skill} sem cargo ou papel formal",
            "Descrição vaga de {skill} sem situação, ação ou resultado",
        ],
        "guideline_template": (
            "Avaliar {skill} com base no método STAR (Situação, Tarefa, Ação, Resultado). "
            "Valorizar exemplos com métricas concretas e impacto mensurável. "
            "Descontar auto-declarações sem evidência comportamental."
        ),
    },
    "responsibility": {
        "positive_templates": [
            "Responsabilidade exercida com resultados quantificados",
            "Papel claro com duração e escopo definidos na área de {skill}",
            "Progressão de responsabilidades demonstrando crescimento em {skill}",
            "Entregas mensuráveis associadas à responsabilidade de {skill}",
            "Feedback positivo ou reconhecimento pela atuação em {skill}",
        ],
        "negative_templates": [
            "Descrição genérica de {skill} sem detalhes de atuação",
            "Responsabilidade de {skill} sem período ou contexto definido",
            "{skill} listado sem resultados ou entregas mensuráveis",
            "Menção superficial a {skill} sem evidência de execução",
            "Apenas título de cargo sem descrição de atividades em {skill}",
        ],
        "guideline_template": (
            "Avaliar se o candidato exerceu {skill} com autonomia e resultados. "
            "Priorizar evidências com escopo, duração e entregas concretas. "
            "Descontar descrições genéricas sem contexto de execução."
        ),
    },
}

SKILL_SPECIFIC_EVIDENCE: dict[str, dict[str, list[str]]] = {
    "Python": {
        "positive": [
            "5+ anos de experiência com Python em produção",
            "Contribuições open source em Python",
            "Projetos Python listados com detalhes técnicos",
            "Uso de frameworks Python (Django, FastAPI, Flask) em produção",
            "Arquitetura de sistemas Python de alta escala",
        ],
        "negative": [
            "Python mencionado apenas em lista de skills sem contexto",
            "Apenas cursos online de Python",
            "Python como skill secundária sem evidência de uso",
            "Somente scripts simples em Python sem projetos reais",
        ],
    },
    "Java": {
        "positive": [
            "Experiência sólida com Java em aplicações enterprise",
            "Domínio de ecossistema Spring Boot/Spring Cloud",
            "Projetos Java com alta concorrência e performance",
            "Certificação Oracle Java ou equivalente",
        ],
        "negative": [
            "Java mencionado sem projetos ou contexto profissional",
            "Apenas formação acadêmica em Java",
            "Java listado sem versão ou framework específico",
        ],
    },
    "React": {
        "positive": [
            "Projetos React em produção com detalhes de complexidade",
            "Experiência com ecossistema React (Redux, Next.js, hooks)",
            "Contribuições em componentes reutilizáveis e design systems",
            "Performance optimization em aplicações React",
        ],
        "negative": [
            "React mencionado sem projetos concretos",
            "Apenas tutoriais ou projetos pessoais em React",
            "React como skill secundária sem evidência de profundidade",
        ],
    },
    "AWS": {
        "positive": [
            "Arquitetura de soluções em AWS com múltiplos serviços",
            "Certificação AWS (Solutions Architect, DevOps Engineer)",
            "Gestão de infraestrutura AWS em produção",
            "Otimização de custos e alta disponibilidade na AWS",
        ],
        "negative": [
            "AWS mencionado sem serviços específicos",
            "Apenas uso básico de EC2/S3 sem arquitetura",
            "AWS listado sem contexto de escala ou complexidade",
        ],
    },
    "SQL": {
        "positive": [
            "Modelagem de dados e queries complexas em produção",
            "Otimização de performance de banco de dados",
            "Experiência com múltiplos SGBDs (PostgreSQL, MySQL, Oracle)",
            "Administração de bancos de dados em escala",
        ],
        "negative": [
            "SQL mencionado apenas como skill básica",
            "Somente queries simples sem modelagem",
            "SQL sem contexto de volume de dados ou complexidade",
        ],
    },
    "Docker": {
        "positive": [
            "Containerização de aplicações em produção com Docker",
            "Criação de imagens otimizadas e multi-stage builds",
            "Docker Compose para ambientes de desenvolvimento e CI/CD",
            "Integração de Docker com orquestração (Kubernetes, ECS)",
        ],
        "negative": [
            "Docker mencionado sem contexto de uso profissional",
            "Apenas uso básico de containers sem otimização",
            "Docker listado sem pipeline ou orquestração",
        ],
    },
    "Kubernetes": {
        "positive": [
            "Gestão de clusters Kubernetes em produção",
            "Implementação de deployments, services e ingress",
            "Certificação CKA/CKAD ou equivalente",
            "Automação de infraestrutura com Helm e operators",
        ],
        "negative": [
            "Kubernetes mencionado sem experiência prática",
            "Apenas Minikube ou ambientes de teste",
            "Kubernetes listado sem detalhes de escala ou gestão",
        ],
    },
    "Machine Learning": {
        "positive": [
            "Modelos de ML em produção com métricas de performance",
            "Pipeline completo: coleta, treinamento, deploy e monitoramento",
            "Publicações ou contribuições em ML/AI",
            "Experiência com MLOps e versionamento de modelos",
        ],
        "negative": [
            "ML mencionado sem projetos concretos",
            "Apenas certificados ou cursos de ML",
            "ML como interesse sem aplicação profissional",
        ],
    },
    "Liderança": {
        "positive": [
            "Gestão direta de equipe com número de reports",
            "Resultados mensuráveis de liderança (turnover, engajamento)",
            "Promoções por competência de liderança",
            "Desenvolvimento de pessoas com cases de sucesso",
        ],
        "negative": [
            "Apenas menciona liderança sem exemplos concretos",
            "Liderança informal sem cargo de gestão",
            "Auto-declaração de liderança sem evidências",
        ],
    },
    "Comunicação": {
        "positive": [
            "Apresentações para stakeholders seniores ou clientes",
            "Produção de documentação técnica ou relatórios",
            "Mediação de conflitos com resultados positivos",
            "Comunicação cross-funcional com múltiplas áreas",
        ],
        "negative": [
            "Comunicação mencionada de forma genérica",
            "Sem exemplos concretos de comunicação efetiva",
            "Apenas auto-avaliação positiva sem contexto",
        ],
    },
}


def _generate_evidence_for_skill(
    skill_name: str,
    category: str,
    subcategory: str | None = None,
) -> dict[str, Any]:
    if skill_name in SKILL_SPECIFIC_EVIDENCE:
        specific = SKILL_SPECIFIC_EVIDENCE[skill_name]
        pattern = EVIDENCE_PATTERNS.get(category, EVIDENCE_PATTERNS["technical_skill"])
        guideline = pattern["guideline_template"].format(skill=skill_name)
        return {
            "positive": specific["positive"],
            "negative": specific["negative"],
            "guideline": guideline,
        }

    pattern = EVIDENCE_PATTERNS.get(category, EVIDENCE_PATTERNS["technical_skill"])
    years = pattern.get("years", "3")

    positive = [
        t.format(skill=skill_name, years=years)
        for t in pattern["positive_templates"]
    ]
    negative = [
        t.format(skill=skill_name, years=years)
        for t in pattern["negative_templates"]
    ]
    guideline = pattern["guideline_template"].format(skill=skill_name)

    return {
        "positive": positive,
        "negative": negative,
        "guideline": guideline,
    }


class EvaluationCriteriaService:

    def __init__(self):
        self._similarity_threshold = 0.55

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    async def seed_from_catalogs(self, db: AsyncSession) -> dict[str, int]:
        repo = EvaluationCriteriaRepository(db)
        existing_count = await repo.count_all()
        if existing_count and existing_count > 0:
            logger.info(
                f"Evaluation criteria already seeded ({existing_count} records). Skipping."
            )
            return {"created": 0, "skipped": existing_count}

        created = 0

        for area, categories in TECH_SKILLS_CATALOG.items():
            for subcategory, skills in categories.items():
                top_skills = skills[:5]
                for skill in top_skills:
                    evidence = _generate_evidence_for_skill(
                        skill, "technical_skill", subcategory
                    )
                    criteria = EvaluationCriteria(
                        name=skill,
                        category=CriterionCategory.TECHNICAL_SKILL.value,
                        subcategory=f"{area}/{subcategory}",
                        positive_evidences=evidence["positive"],
                        negative_evidences=evidence["negative"],
                        evaluation_guidelines=evidence["guideline"],
                        source="seed",
                        is_active=True,
                    )
                    repo.add(criteria)
                    created += 1

        for key, comp_data in BEHAVIORAL_COMPETENCIES_CATALOG.items():
            comp_name = comp_data["name"]
            evidence = _generate_evidence_for_skill(
                comp_name, "behavioral_competency", key
            )
            criteria = EvaluationCriteria(
                name=comp_name,
                category=CriterionCategory.BEHAVIORAL_COMPETENCY.value,
                subcategory=key,
                positive_evidences=evidence["positive"],
                negative_evidences=evidence["negative"],
                evaluation_guidelines=evidence["guideline"],
                source="seed",
                is_active=True,
            )
            db.add(criteria)
            created += 1

            for sub in comp_data.get("subcategories", [])[:3]:
                sub_evidence = _generate_evidence_for_skill(
                    sub, "behavioral_competency", key
                )
                sub_criteria = EvaluationCriteria(
                    name=sub,
                    category=CriterionCategory.BEHAVIORAL_COMPETENCY.value,
                    subcategory=f"{key}/{comp_name}",
                    positive_evidences=sub_evidence["positive"],
                    negative_evidences=sub_evidence["negative"],
                    evaluation_guidelines=sub_evidence["guideline"],
                    source="seed",
                    is_active=True,
                )
                db.add(sub_criteria)
                created += 1

        for area, resp_categories in RESPONSIBILITIES_CATALOG.items():
            for subcategory, responsibilities in resp_categories.items():
                top_resps = responsibilities[:4]
                for resp in top_resps:
                    short_name = resp[:100] if len(resp) > 100 else resp
                    evidence = _generate_evidence_for_skill(
                        short_name, "responsibility", f"{area}/{subcategory}"
                    )
                    criteria = EvaluationCriteria(
                        name=short_name,
                        category=CriterionCategory.RESPONSIBILITY.value,
                        subcategory=f"{area}/{subcategory}",
                        positive_evidences=evidence["positive"],
                        negative_evidences=evidence["negative"],
                        evaluation_guidelines=evidence["guideline"],
                        source="seed",
                        is_active=True,
                    )
                    db.add(criteria)
                    created += 1

        await repo.flush()
        logger.info(f"Seeded {created} evaluation criteria from catalogs")
        return {"created": created, "skipped": 0}

    async def get_criteria_for_requirements(
        self,
        db: AsyncSession,
        requirements: list[str],
        min_score: float = 0.4,
    ) -> list[dict[str, Any]]:
        # C5 — Fairness gate (LGPD Art. 20 / CLAUDE.md #2/#3).
        # Must run BEFORE any DB query — test asserts mock_db.execute.assert_not_called().
        for _ec_req in requirements:
            _ec_fg, _ec_fg_unavail = _ss.run_fairness_check(str(_ec_req) if _ec_req else "")
            if _ec_fg_unavail or (_ec_fg and _ec_fg.is_blocked):
                _ec_fg = _ec_fg or type(
                    "FR", (), {"is_blocked": True, "category": "unavailable",
                               "educational_message": "fairness guard unavailable"}
                )()
                await _ss.log_scoring_decision(
                    company_id="unknown",
                    agent_name="evaluation_criteria_service",
                    decision_type="fairness_block",
                    action="cv_screening.fairness_block",
                    decision="blocked",
                    reasoning=[
                        f"FairnessGuard blocked requirement: category={_ec_fg.category}",
                        _ec_fg.educational_message or "",
                        f"blocked_requirement={str(_ec_req)[:80]}",
                    ],
                    criteria_used=["fairness_guard"],
                    human_review_required=True,
                )
                raise FairnessBlockedError(_ec_fg)

        all_criteria = await EvaluationCriteriaRepository(db).list_active()

        matches: list[dict[str, Any]] = []

        for requirement in requirements:
            req_lower = requirement.lower()
            matched = []

            for criteria in all_criteria:
                name_score = self._similarity(req_lower, criteria.name.lower())

                contains_bonus = 0.0
                if criteria.name.lower() in req_lower or req_lower in criteria.name.lower():
                    contains_bonus = 0.3

                final_score = min(name_score + contains_bonus, 1.0)

                if final_score >= min_score:
                    matched.append({
                        "criteria": criteria,
                        "score": final_score,
                    })

            matched.sort(key=lambda x: x["score"], reverse=True)
            top_matches = matched[:5]

            best_score = top_matches[0]["score"] if top_matches else 0.0
            matches.append({
                "requirement": requirement,
                "matched_criteria": [m["criteria"] for m in top_matches],
                "match_score": best_score,
            })

        logger.info(
            f"Matched {sum(len(m['matched_criteria']) for m in matches)} criteria "
            f"for {len(requirements)} requirements"
        )
        return matches

    async def update_effectiveness(
        self,
        db: AsyncSession,
        criteria_id: UUID,
        was_helpful: bool,
    ) -> EvaluationCriteria | None:
        criteria = await EvaluationCriteriaRepository(db).get_by_id(criteria_id)

        if not criteria:
            logger.warning(f"Criteria {criteria_id} not found for effectiveness update")
            return None

        criteria.feedback_count += 1
        criteria.usage_count += 1

        adjustment = 0.05 if was_helpful else -0.05
        new_score = criteria.effectiveness_score + adjustment
        criteria.effectiveness_score = max(0.0, min(1.0, new_score))

        await db.flush()
        logger.info(
            f"Updated effectiveness for '{criteria.name}': "
            f"score={criteria.effectiveness_score:.2f}, "
            f"helpful={was_helpful}, feedback_count={criteria.feedback_count}"
        )
        return criteria

    async def get_all_active(
        self,
        db: AsyncSession,
        category: str | None = None,
    ) -> list[EvaluationCriteria]:
        return await EvaluationCriteriaRepository(db).list_active_by_category(category=category)

    async def get_by_id(
        self,
        db: AsyncSession,
        criteria_id: UUID,
    ) -> EvaluationCriteria | None:
        return await EvaluationCriteriaRepository(db).get_by_id(criteria_id)


evaluation_criteria_service = EvaluationCriteriaService()
