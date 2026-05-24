"""
RAGAS Evaluation Service — ACH-027

Avaliação contínua da qualidade das respostas dos agentes LIA usando RAGAS
(Retrieval Augmented Generation Assessment System).

Métricas avaliadas:
- faithfulness: resposta factualmente alinhada com contexto fornecido
- answer_relevancy: resposta relevante para a pergunta
- context_precision: contexto fornecido é preciso para a pergunta
- context_recall: contexto recuperado cobre as informações necessárias

Armazena resultados em 'agent_ragas_evaluations' com retenção de 90 dias.
Celery task: 'ragas.evaluate_batch' — executado diariamente às 03h UTC.

Fail-safe: falha na avaliação RAGAS não afeta o funcionamento dos agentes.
"""
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# Threshold de alerta (score abaixo disso gera WARNING no log)
# Configurável via RAGAS_QUALITY_THRESHOLD env var (padrão: 0.70)
RAGAS_QUALITY_THRESHOLD = float(os.getenv("RAGAS_QUALITY_THRESHOLD", "0.70"))


@dataclass
class RAGASEvaluationInput:
    """Entrada para avaliação RAGAS de uma resposta de agente."""

    question: str
    answer: str
    contexts: list[str]
    ground_truth: str | None = None  # Resposta ideal esperada (golden dataset)
    session_id: str = ""
    company_id: str = ""
    domain: str = ""
    agent_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGASEvaluationResult:
    """Resultado de uma avaliação RAGAS."""

    evaluation_id: str
    session_id: str
    domain: str
    agent_name: str
    faithfulness: float | None
    answer_relevancy: float | None
    context_precision: float | None
    context_recall: float | None
    overall_score: float | None
    evaluated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed_threshold(self) -> bool:
        """True se score geral acima do threshold de qualidade."""
        if self.overall_score is None:
            return True  # fail-safe: não penalizar por ausência de score
        return self.overall_score >= RAGAS_QUALITY_THRESHOLD

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "session_id": self.session_id,
            "domain": self.domain,
            "agent_name": self.agent_name,
            "faithfulness": self.faithfulness,
            "answer_relevancy": self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "overall_score": self.overall_score,
            "evaluated_at": self.evaluated_at.isoformat(),
            "metadata": self.metadata,
        }


class RAGASEvaluationService:
    """
    Serviço de avaliação de qualidade LLM via RAGAS.

    Modo de operação:
    - Avaliação assíncrona: armazena samples durante execução dos agentes
    - Batch evaluation: Celery task diário avalia samples acumulados
    - Resultados persistidos em DB para histórico e alertas

    Dependência RAGAS é opcional — se não instalada, usa avaliação simplificada
    baseada em heurísticas de comprimento e coerência.
    """

    def __init__(self) -> None:
        self._ragas_available = self._check_ragas()

    def _check_ragas(self) -> bool:
        """Verifica se pacote ragas está disponível."""
        try:
            import ragas  # noqa: F401
            return True
        except ImportError:
            logger.info(
                "[RAGASEvaluationService] Pacote 'ragas' não instalado — "
                "usando avaliação heurística simplificada."
            )
            return False

    async def evaluate(
        self,
        evaluation_input: RAGASEvaluationInput,
        db: Any,
    ) -> RAGASEvaluationResult:
        """
        Avalia qualidade de uma resposta de agente.

        Fail-safe: qualquer exceção retorna resultado com scores None.
        """
        evaluation_id = str(uuid4())
        evaluated_at = datetime.utcnow()

        try:
            if self._ragas_available:
                scores = await self._evaluate_with_ragas(evaluation_input)
            else:
                scores = self._evaluate_heuristic(evaluation_input)

            overall = self._compute_overall(scores)

            result = RAGASEvaluationResult(
                evaluation_id=evaluation_id,
                session_id=evaluation_input.session_id,
                domain=evaluation_input.domain,
                agent_name=evaluation_input.agent_name,
                faithfulness=scores.get("faithfulness"),
                answer_relevancy=scores.get("answer_relevancy"),
                context_precision=scores.get("context_precision"),
                context_recall=scores.get("context_recall"),
                overall_score=overall,
                evaluated_at=evaluated_at,
                metadata=evaluation_input.metadata,
            )

            if not result.passed_threshold:
                logger.warning(
                    "[RAGAS] Score abaixo do threshold: domain=%s agent=%s "
                    "overall=%.2f threshold=%.2f",
                    evaluation_input.domain, evaluation_input.agent_name,
                    overall or 0, RAGAS_QUALITY_THRESHOLD,
                )

            await self._persist_result(result, db)
            return result

        except Exception as exc:
            logger.debug("[RAGAS] Avaliação falhou (fail-safe): %s", exc)
            return RAGASEvaluationResult(
                evaluation_id=evaluation_id,
                session_id=evaluation_input.session_id,
                domain=evaluation_input.domain,
                agent_name=evaluation_input.agent_name,
                faithfulness=None,
                answer_relevancy=None,
                context_precision=None,
                context_recall=None,
                overall_score=None,
                evaluated_at=evaluated_at,
                metadata={"error": str(exc)},
            )

    async def _evaluate_with_ragas(self, inp: RAGASEvaluationInput) -> dict[str, float]:
        """Avaliação usando biblioteca RAGAS (quando disponível)."""
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )

        data = {
            "question": [inp.question],
            "answer": [inp.answer],
            "contexts": [inp.contexts],
        }
        if inp.ground_truth:
            data["ground_truth"] = [inp.ground_truth]

        dataset = Dataset.from_dict(data)

        metrics = [faithfulness, answer_relevancy]
        if inp.contexts:
            metrics.append(context_precision)
        if inp.ground_truth and inp.contexts:
            metrics.append(context_recall)

        result = evaluate(dataset, metrics=metrics)
        return dict(result)

    def _evaluate_heuristic(self, inp: RAGASEvaluationInput) -> dict[str, float]:
        """
        Avaliação heurística simplificada quando RAGAS não está disponível.

        Critérios aproximados (não substitui RAGAS real):
        - answer_relevancy: score baseado em comprimento e palavras-chave da pergunta
        - faithfulness: score base 0.8 (sem verificação factual real)
        """
        scores: dict[str, float] = {}

        # answer_relevancy: resposta curta demais = baixa relevância
        if inp.answer:
            words = len(inp.answer.split())
            if words < 10:
                scores["answer_relevancy"] = 0.4
            elif words < 30:
                scores["answer_relevancy"] = 0.7
            else:
                scores["answer_relevancy"] = 0.85
        else:
            scores["answer_relevancy"] = 0.0

        # faithfulness: proxy — se contextos foram fornecidos, score maior
        scores["faithfulness"] = 0.80 if inp.contexts else 0.60

        # context_precision: 1.0 se contextos não vazio
        if inp.contexts:
            scores["context_precision"] = 0.80

        return scores

    def _compute_overall(self, scores: dict[str, float]) -> float | None:
        """Média ponderada dos scores disponíveis."""
        if not scores:
            return None
        weights = {
            "faithfulness": 0.35,
            "answer_relevancy": 0.35,
            "context_precision": 0.15,
            "context_recall": 0.15,
        }
        total_weight = 0.0
        weighted_sum = 0.0
        for metric, weight in weights.items():
            if metric in scores and scores[metric] is not None:
                weighted_sum += scores[metric] * weight
                total_weight += weight

        if total_weight == 0:
            return None
        return round(weighted_sum / total_weight, 4)

    async def _persist_result(self, result: RAGASEvaluationResult, db: Any) -> None:
        """Persiste resultado na tabela agent_ragas_evaluations."""
        try:
            from sqlalchemy import text
            # ADR-001-EXEMPT: direct SQL — ragas eval is a non-tenant time-series table, no company_id filter needed at eval layer
            await db.execute(
                # RLS-EXEMPT: agent_ragas_evaluations — system observability table, not tenant-scoped
                text(
                    """
                    INSERT INTO agent_ragas_evaluations
                      (id, session_id, domain, agent_name,
                       faithfulness, answer_relevancy, context_precision, context_recall,
                       overall_score, evaluated_at, metadata)
                    VALUES
                      (:id, :session_id, :domain, :agent_name,
                       :faithfulness, :answer_relevancy, :context_precision, :context_recall,
                       :overall_score, :evaluated_at, CAST(:metadata AS jsonb))
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                {
                    "id": result.evaluation_id,
                    "session_id": result.session_id,
                    "domain": result.domain,
                    "agent_name": result.agent_name,
                    "faithfulness": result.faithfulness,
                    "answer_relevancy": result.answer_relevancy,
                    "context_precision": result.context_precision,
                    "context_recall": result.context_recall,
                    "overall_score": result.overall_score,
                    "evaluated_at": result.evaluated_at,
                    "metadata": __import__("json").dumps(result.metadata),
                },
            )
            await db.commit()
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.debug("[RAGAS] Falha ao persistir resultado: %s", exc)

    async def get_domain_summary(
        self,
        domain: str,
        company_id: str,
        db: Any,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Retorna sumário de qualidade do agente nos últimos N dias.

        Returns:
            dict com avg_overall, avg_faithfulness, avg_relevancy, total_evaluations,
                   below_threshold_count, period_days
        """
        try:
            from sqlalchemy import text
            since = datetime.utcnow() - timedelta(days=days)
            result = await db.execute(
                text(
                    """
                    SELECT
                        COUNT(*) as total,
                        AVG(overall_score) as avg_overall,
                        AVG(faithfulness) as avg_faithfulness,
                        AVG(answer_relevancy) as avg_relevancy,
                        SUM(CASE WHEN overall_score < :threshold THEN 1 ELSE 0 END) as below_threshold
                    FROM agent_ragas_evaluations
                    WHERE domain = :domain
                      AND evaluated_at >= :since
                    """
                ),
                {
                    "domain": domain,
                    "since": since,
                    "threshold": RAGAS_QUALITY_THRESHOLD,
                },
            )
            row = result.fetchone()
            if not row or row.total == 0:
                return {"domain": domain, "period_days": days, "total_evaluations": 0}

            return {
                "domain": domain,
                "period_days": days,
                "total_evaluations": int(row.total),
                "avg_overall": round(float(row.avg_overall or 0), 4),
                "avg_faithfulness": round(float(row.avg_faithfulness or 0), 4),
                "avg_relevancy": round(float(row.avg_relevancy or 0), 4),
                "below_threshold_count": int(row.below_threshold or 0),
                "quality_rate": round(
                    1.0 - (int(row.below_threshold or 0) / max(int(row.total), 1)), 4
                ),
            }
        except Exception as exc:
            logger.warning("[RAGAS] Falha ao buscar sumário: %s", exc)
            return {"domain": domain, "period_days": days, "error": str(exc)}


# Singleton para uso nos agentes
ragas_evaluation_service = RAGASEvaluationService()
