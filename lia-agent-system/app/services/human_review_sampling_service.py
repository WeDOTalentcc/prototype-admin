"""
Human Review Sampling Service — Fase 7 (LGPD + EU AI Act)

Implementa sampling determinístico de 5% de decisões de IA para revisão humana.
Conforme EU AI Act Art. 14 (Human Oversight) e LGPD Art. 20 (Revisão de Decisões Automatizadas).

O sampling é determinístico por decision_id (via hash MD5):
- Mesma decision_id sempre retorna o mesmo resultado (idempotente)
- Não depende de estado externo ou banco de dados
- 5% = 1 em cada 20 decisões é marcada para revisão
"""
import hashlib
import logging

logger = logging.getLogger(__name__)


class HumanReviewSamplingService:
    """
    Serviço de sampling para revisão humana de decisões de IA.

    Garante que ~5% de todas as decisões automáticas sejam revisadas por humano,
    atendendo aos requisitos de supervisão humana do EU AI Act e LGPD Art. 20.
    """

    # 5% de todas as decisões de IA
    SAMPLE_RATE: float = 0.05

    # Tipos de decisão que SEMPRE requerem revisão humana (independente do sampling)
    ALWAYS_REVIEW_DECISIONS = {
        "finalize_hiring",   # Contratação definitiva
        "mass_rejection",    # Rejeição em lote
        "fairness_flagged",  # Decisão sinalizada pelo FairnessGuard
    }

    def should_flag_for_review(self, decision_id: str) -> bool:
        """
        Determina deterministicamente se uma decisão deve ser revisada por humano.

        Usa hash MD5 do decision_id para garantir idempotência:
        - Mesma decision_id sempre retorna o mesmo resultado
        - ~5% das decisions retornam True

        Args:
            decision_id: ID único da decisão de IA (UUID ou string)

        Returns:
            True se a decisão deve ser revisada por humano
        """
        hash_val = int(hashlib.md5(str(decision_id).encode()).hexdigest(), 16)
        threshold = int(self.SAMPLE_RATE * 100)  # 5 → threshold de 0-99
        return (hash_val % 100) < threshold

    def should_always_review(self, decision_type: str) -> bool:
        """
        Verifica se o tipo de decisão sempre requer revisão humana.

        Args:
            decision_type: Tipo da decisão (ex: "finalize_hiring")

        Returns:
            True se sempre deve ser revisado
        """
        return decision_type in self.ALWAYS_REVIEW_DECISIONS

    async def flag_for_review(
        self,
        db,
        *,
        decision_id: str,
        decision_type: str,
        agent_name: str,
        company_id: str,
        candidate_id: str | None = None,
        job_id: str | None = None,
        summary: str = "",
        confidence: float = 0.0,
        reason: str = "5pct_sampling",
    ) -> bool:
        """
        Cria registro de revisão humana para uma decisão de IA.

        Args:
            db: AsyncSession do banco de dados
            decision_id: ID único da decisão
            decision_type: Tipo da decisão (ex: "cv_screening", "pipeline_transition")
            agent_name: Nome do agente que tomou a decisão
            company_id: ID da empresa
            candidate_id: ID do candidato (opcional)
            job_id: ID da vaga (opcional)
            summary: Resumo da decisão
            confidence: Confiança do agente (0-1)
            reason: Razão para revisão ("5pct_sampling", "always_required", "low_confidence")

        Returns:
            True se o registro foi criado com sucesso
        """
        try:
            # Tentar usar o audit_service para registrar a decisão para revisão
            from app.services.audit_service import audit_service
            await audit_service.log_decision(
                company_id=company_id,
                agent_name=agent_name,
                decision_type=decision_type,
                action="flag_for_human_review",
                decision=f"human_review_required:{reason}",
                reasoning=[summary],
                criteria_used=[],
                candidate_id=candidate_id,
                job_vacancy_id=job_id,
                confidence=confidence,
                human_review_required=True,
            )
            logger.info(
                "Decisão %s marcada para revisão humana (reason=%s, agent=%s)",
                decision_id, reason, agent_name,
            )
            return True
        except Exception as exc:
            logger.warning("Falha ao registrar revisão humana para %s: %s", decision_id, exc)
            return False

    async def evaluate_and_flag(
        self,
        db,
        *,
        decision_id: str,
        decision_type: str,
        agent_name: str,
        company_id: str,
        confidence: float = 0.9,
        candidate_id: str | None = None,
        job_id: str | None = None,
        summary: str = "",
    ) -> bool:
        """
        Avalia se a decisão deve ser revisada e, se sim, cria o registro.

        Combina sampling de 5% com verificação de tipos always-review e
        confiança baixa (< 0.7 também aciona revisão).

        Returns:
            True se a decisão foi marcada para revisão
        """
        reason = None

        if self.should_always_review(decision_type):
            reason = "always_required"
        elif confidence < 0.7:
            reason = "low_confidence"
        elif self.should_flag_for_review(decision_id):
            reason = "5pct_sampling"

        if reason:
            return await self.flag_for_review(
                db,
                decision_id=decision_id,
                decision_type=decision_type,
                agent_name=agent_name,
                company_id=company_id,
                candidate_id=candidate_id,
                job_id=job_id,
                summary=summary,
                confidence=confidence,
                reason=reason,
            )

        return False


# Instância singleton
human_review_sampling_service = HumanReviewSamplingService()
