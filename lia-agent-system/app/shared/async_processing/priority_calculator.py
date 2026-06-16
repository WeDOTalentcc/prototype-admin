"""
Priority Calculator — E11 (Priority Queue)

Calcula prioridade de tasks para asyncio.PriorityQueue baseado em urgência.
Menor número = maior prioridade.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class PriorityCalculator:
    """
    Calcula prioridade de execução de tasks assíncronas.

    Escala de prioridade:
    1 = URGENTE (SLA em risco)
    2 = ALTA (backlog crítico)
    3 = NORMAL
    5 = BAIXA (padrão)
    """

    # Task type → base priority
    _BASE_PRIORITIES: dict[str, int] = {
        "cv_screening": 2,
        "sourcing": 2,
        "followup": 3,
        "wsi_abandoned": 3,
        "notification": 3,
        "report": 5,
        "analytics": 5,
    }

    def compute(
        self,
        task_type: str,
        metadata: dict | None = None,
    ) -> int:
        """
        Retorna prioridade numérica para a task (1=mais urgente, 5=mais baixa).

        Regras de escalação:
        - `sourcing` com deadline_days < 7 → prioridade 1
        - `cv_screening` com backlog > 50 → prioridade 2
        - `followup` ou `wsi_abandoned` → prioridade 3
        - padrão → prioridade 5
        """
        metadata = metadata or {}
        base = self._BASE_PRIORITIES.get(task_type, 5)

        try:
            # Escalação: sourcing com deadline urgente
            if task_type == "sourcing":
                deadline_days = metadata.get("deadline_days")
                if deadline_days is not None and int(deadline_days) < 7:
                    logger.debug(
                        "[PriorityCalculator] sourcing deadline_days=%d → prioridade 1",
                        deadline_days,
                    )
                    return 1

            # Escalação: cv_screening com backlog alto
            if task_type == "cv_screening":
                backlog = metadata.get("backlog_size", 0)
                if int(backlog) > 50:
                    logger.debug(
                        "[PriorityCalculator] cv_screening backlog=%d > 50 → prioridade 2",
                        backlog,
                    )
                    return 2

        except (ValueError, TypeError) as exc:
            logger.warning("[PriorityCalculator] Metadata parse error: %s", exc)

        return base


priority_calculator = PriorityCalculator()
