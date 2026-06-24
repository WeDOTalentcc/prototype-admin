"""
Agent Quality Evaluator — Sprint J1

Avalia qualidade de respostas de agentes via LLM-as-judge (Claude Haiku).
Executa em shadow mode (background Celery) — não bloqueia produção.

Arquitetura:
- 5 métricas: task_completion, factual_accuracy, fairness, coherence, actionability
- Sampling: QUALITY_EVAL_SAMPLING_RATE (default 10%)
- Persistência: tabela agent_quality_evaluations
- LangSmith: envia feedback para avaliação contínua em staging

Referências:
- Plano: docs/analises/PLANO_IMPLEMENTACAO_GAPS_IA.md → Sprint J1
- Crença #11 (Anti-sycophancy) — benchmarks setoriais injetados no prompt
"""
from __future__ import annotations
from app.shared.llm_models import CANONICAL_HAIKU_MODEL

import logging
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

QUALITY_EVAL_SAMPLING_RATE: float = float(
    os.environ.get("QUALITY_EVAL_SAMPLING_RATE", "0.10")
)

EVAL_METRICS: dict[str, str] = {
    "task_completion": (
        "A tarefa solicitada pelo usuário foi completamente executada pelo agente?"
    ),
    "factual_accuracy": (
        "A resposta contém afirmações verificáveis e corretas? Não há alucinações?"
    ),
    "fairness": (
        "A resposta é livre de viés discriminatório (gênero, raça, idade, etc.)?"
    ),
    "coherence": (
        "A resposta é coerente com o contexto da conversa e com o pedido do usuário?"
    ),
    "actionability": (
        "A resposta oferece próximos passos claros e acionáveis para o recrutador?"
    ),
}


@dataclass
class EvaluationResult:
    agent_id: str
    company_id: str
    session_id: str | None
    scores: dict[str, float]
    overall_score: float
    evaluated_at: datetime = field(default_factory=datetime.utcnow)


class AgentQualityEvaluator:
    """
    Avalia qualidade de respostas de agentes via LLM-as-judge.

    Uso típico (shadow mode — não aguardar resultado):
        await agent_quality_evaluator.evaluate_if_sampled(
            agent_id="wizard",
            user_message="crie uma vaga de dev sênior",
            agent_response="...",
            context={"company_id": "...", "session_id": "..."},
            company_id="...",
        )
    """

    async def evaluate_if_sampled(
        self,
        *,
        agent_id: str,
        user_message: str,
        agent_response: str,
        context: dict[str, Any],
        company_id: str,
        session_id: str | None = None,
        db: Any = None,
    ) -> EvaluationResult | None:
        """
        Avalia a resposta se dentro do sampling rate configurado.
        Retorna None se não amostrado ou se avaliação falhar (shadow mode).
        """
        if random.random() > QUALITY_EVAL_SAMPLING_RATE:
            return None

        try:
            return await self.evaluate_response(
                agent_id=agent_id,
                user_message=user_message,
                agent_response=agent_response,
                context=context,
                company_id=company_id,
                session_id=session_id,
                db=db,
            )
        except Exception as exc:
            logger.debug(
                "[AgentQualityEvaluator] Avaliação falhou (shadow mode): %s", exc
            )
            return None

    async def evaluate_response(
        self,
        *,
        agent_id: str,
        user_message: str,
        agent_response: str,
        context: dict[str, Any],
        company_id: str,
        session_id: str | None = None,
        db: Any = None,
    ) -> EvaluationResult:
        """
        Avalia resposta com LLM-as-judge (5 métricas).
        Persiste resultado e envia para LangSmith (se configurado).
        """
        scores: dict[str, float] = {}

        for metric, question in EVAL_METRICS.items():
            score = await self._judge(
                question=question,
                user_message=user_message,
                agent_response=agent_response,
            )
            scores[metric] = score

        overall = sum(scores.values()) / len(scores)

        result = EvaluationResult(
            agent_id=agent_id,
            company_id=company_id,
            session_id=session_id,
            scores=scores,
            overall_score=overall,
        )

        if db is not None:
            await self._persist(result, db)

        await self._send_to_langsmith(result, user_message, agent_response)

        logger.info(
            "[AgentQualityEvaluator] agent=%s company=%s overall=%.2f scores=%s",
            agent_id, company_id, overall, scores,
        )
        return result

    async def _judge(
        self,
        question: str,
        user_message: str,
        agent_response: str,
    ) -> float:
        """
        LLM-as-judge via anthropic.AsyncAnthropic.
        Retorna score 0.0–1.0. Retorna 0.5 em caso de falha (neutral fallback).
        """
        try:
            import anthropic  # allows test mocking via patch("anthropic.AsyncAnthropic")

            prompt = (
                f"Você é um avaliador de qualidade de sistemas de IA para recrutamento.\n\n"
                f"Pergunta de avaliação: {question}\n\n"
                f"Mensagem do usuário: {user_message[:500]}\n"
                f"Resposta do agente: {agent_response[:1000]}\n\n"
                f"Responda APENAS com um número de 0.0 a 1.0.\n"
                f"0.0 = não satisfaz | 0.5 = parcialmente | 1.0 = totalmente satisfaz"
            )

            client = anthropic.AsyncAnthropic()
            response = await client.messages.create(
                model=CANONICAL_HAIKU_MODEL,  # was claude-haiku-20240307 (deprecated)
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            score = float(raw.strip())
            return max(0.0, min(1.0, score))

        except Exception as exc:
            logger.debug("[AgentQualityEvaluator] _judge fallback: %s", exc)
            return 0.5  # neutral fallback — não penaliza nem recompensa

    async def _persist(self, result: EvaluationResult, db: Any) -> None:
        """Persiste EvaluationResult na tabela agent_quality_evaluations."""
        try:
            from lia_models.agent_quality_evaluation import AgentQualityEvaluation
            record = AgentQualityEvaluation(
                agent_id=result.agent_id,
                company_id=result.company_id,
                session_id=result.session_id,
                overall_score=result.overall_score,
                scores=result.scores,
                evaluated_at=result.evaluated_at,
            )
            db.add(record)
            await db.commit()
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning("[AgentQualityEvaluator] Persistência falhou: %s", exc)

    async def _send_to_langsmith(
        self, result: EvaluationResult, user_message: str, agent_response: str
    ) -> None:
        """
        Envia resultado como feedback para LangSmith (staging/CI).
        Silencioso se LANGSMITH_API_KEY não configurado.
        """
        api_key = os.environ.get("LANGSMITH_API_KEY")
        if not api_key:
            return
        try:
            from langsmith import Client
            client = Client(api_key=api_key)
            run_id = f"{result.agent_id}_{result.evaluated_at.isoformat()}"
            client.create_feedback(
                run_id=run_id,
                key="agent_quality_overall",
                score=result.overall_score,
                comment=str(result.scores),
            )
        except Exception as exc:
            logger.debug("[AgentQualityEvaluator] LangSmith feedback falhou: %s", exc)


agent_quality_evaluator = AgentQualityEvaluator()
