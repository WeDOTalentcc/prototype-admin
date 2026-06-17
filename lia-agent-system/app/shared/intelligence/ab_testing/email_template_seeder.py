"""
A/B Testing Seeder — Email Template Variants (Fase 5 / A5).

Seeds initial A/B test experiments for email templates:
- E6 invite (screening invitation)
- Follow-up (screening reminder)
- Feedback (rejection/passed feedback)

Each test has a control + treatment variant with 50/50 traffic split.
Uses the persistent ABTestingService (PromptVariant model).
"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.learning.ab_testing_service import ABTestingService

logger = logging.getLogger(__name__)

EMAIL_AB_TESTS: list[dict[str, Any]] = [
    {
        "test_name": "email_screening_invite",
        "variants": [
            {
                "variant_name": "control",
                "prompt_template": (
                    "Olá {{candidate_name}},\n\n"
                    "Você foi selecionado(a) para participar do processo seletivo para a vaga de "
                    "{{job_title}} na {{company_name}}.\n\n"
                    "Para iniciar sua triagem, acesse o link abaixo:\n"
                    "{{screening_link}}\n\n"
                    "Atenciosamente,\n{{company_name}}"
                ),
                "traffic_percentage": 50.0,
            },
            {
                "variant_name": "treatment_personalized",
                "prompt_template": (
                    "{{candidate_name}}, temos boas notícias!\n\n"
                    "Seu perfil chamou nossa atenção e gostaríamos de convidá-lo(a) "
                    "para a próxima etapa do processo seletivo de {{job_title}}.\n\n"
                    "A triagem é rápida (cerca de 10 minutos) e pode ser feita pelo link:\n"
                    "{{screening_link}}\n\n"
                    "Estamos ansiosos para conhecê-lo(a) melhor!\n"
                    "Equipe {{company_name}}"
                ),
                "traffic_percentage": 50.0,
            },
        ],
    },
    {
        "test_name": "email_follow_up_reminder",
        "variants": [
            {
                "variant_name": "control",
                "prompt_template": (
                    "Olá {{candidate_name}},\n\n"
                    "Notamos que você ainda não completou a triagem para a vaga de {{job_title}}.\n\n"
                    "O prazo para conclusão é {{deadline}}. Acesse:\n"
                    "{{screening_link}}\n\n"
                    "Atenciosamente,\n{{company_name}}"
                ),
                "traffic_percentage": 50.0,
            },
            {
                "variant_name": "treatment_urgency",
                "prompt_template": (
                    "{{candidate_name}}, não perca esta oportunidade!\n\n"
                    "Restam apenas {{days_remaining}} dias para completar sua triagem "
                    "para {{job_title}}. Outros candidatos já avançaram no processo.\n\n"
                    "Complete agora (leva ~10 min):\n"
                    "{{screening_link}}\n\n"
                    "Conte conosco,\n{{company_name}}"
                ),
                "traffic_percentage": 50.0,
            },
        ],
    },
    {
        "test_name": "email_feedback_rejection",
        "variants": [
            {
                "variant_name": "control",
                "prompt_template": (
                    "Olá {{candidate_name}},\n\n"
                    "Agradecemos seu interesse e participação no processo seletivo para {{job_title}}.\n\n"
                    "Após análise cuidadosa, seguiremos com outros candidatos nesta etapa. "
                    "Seu perfil ficará em nosso banco de talentos para futuras oportunidades.\n\n"
                    "Desejamos sucesso em sua carreira.\n{{company_name}}"
                ),
                "traffic_percentage": 50.0,
            },
            {
                "variant_name": "treatment_constructive",
                "prompt_template": (
                    "{{candidate_name}},\n\n"
                    "Obrigado por dedicar seu tempo ao processo de {{job_title}}.\n\n"
                    "Embora tenhamos seguido com outros perfis para esta vaga, "
                    "valorizamos suas competências{{strengths_note}}.\n\n"
                    "Manteremos seu perfil ativo e entraremos em contato quando surgir "
                    "uma oportunidade mais alinhada.\n\n"
                    "Sucesso!\n{{company_name}}"
                ),
                "traffic_percentage": 50.0,
            },
        ],
    },
]


async def seed_email_ab_tests(db: AsyncSession) -> dict[str, Any]:
    """Seed A/B test variants for email templates if not already present."""
    service = ABTestingService()
    results = {"created": [], "skipped": [], "errors": []}

    for test_config in EMAIL_AB_TESTS:
        test_name = test_config["test_name"]
        try:
            existing = await service.list_active_tests(db)
            already_exists = any(t["test_name"] == test_name for t in existing)

            if already_exists:
                results["skipped"].append(test_name)
                logger.debug("[ABSeeder] Test '%s' already exists, skipping", test_name)
                continue

            result = await service.create_test(
                test_name=test_name,
                variants=test_config["variants"],
                db=db,
            )

            if "error" in result:
                results["errors"].append({"test": test_name, "error": result["error"]})
                logger.warning("[ABSeeder] Failed to create '%s': %s", test_name, result["error"])
            else:
                results["created"].append(test_name)
                logger.info(
                    "[ABSeeder] Created test '%s' with %d variants",
                    test_name, len(test_config["variants"]),
                )

        except Exception as exc:
            results["errors"].append({"test": test_name, "error": str(exc)})
            logger.error("[ABSeeder] Error seeding '%s': %s", test_name, exc)

    await db.commit()
    logger.info(
        "[ABSeeder] Seeding complete: created=%d skipped=%d errors=%d",
        len(results["created"]), len(results["skipped"]), len(results["errors"]),
    )
    return results
