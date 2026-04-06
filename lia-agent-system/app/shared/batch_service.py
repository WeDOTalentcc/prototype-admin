# LIA-T06 — BatchService genérico com asyncio.gather + Semaphore
# Padrão de mercado: Eightfold AI, Findem, HireEZ usam processamento em lote
# para triagem de CVs, scoring de candidatos e matching de vagas.
# LGPD Art. 7: processamento em lote deve ser minimizado e auditável.
"""Generic async batch processor with concurrency control, progress tracking,
and error handling. Central component for cv_screening and other LIA domains.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Input type
R = TypeVar("R")  # Result type


@dataclass
class BatchItem(Generic[T]):
    item_id: str
    payload: T

@dataclass
class BatchResult(Generic[R]):
    item_id: str
    result: R | None = None
    error: str | None = None
    success: bool = True
    processing_time_ms: float = 0.0

@dataclass
class BatchReport(Generic[R]):
    batch_id: str
    total: int
    successful: int
    failed: int
    results: list[BatchResult[R]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    total_time_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        return self.successful / self.total if self.total > 0 else 0.0


class BatchService(Generic[T, R]):
    """Generic async batch processor.

    Usage:
        service = BatchService(max_concurrency=10, fail_fast=False)
        items = [BatchItem(item_id="1", payload=cv_text), ...]
        report = await service.process(items, process_single_cv)

    LIA-T06: Centraliza processamento em lote para cv_screening, análise de
    candidatos e qualquer outro domínio que precise de batch async.
    """

    def __init__(
        self,
        max_concurrency: int = 10,
        fail_fast: bool = False,
        timeout_per_item_seconds: float = 30.0,
    ):
        self.max_concurrency = max_concurrency
        self.fail_fast = fail_fast
        self.timeout_per_item_seconds = timeout_per_item_seconds
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def process(
        self,
        items: list[BatchItem[T]],
        processor: Callable[[T], Coroutine[Any, Any, R]],
        batch_id: str | None = None,
    ) -> BatchReport[R]:
        """Process a batch of items concurrently with semaphore control.

        Args:
            items: List of BatchItem to process
            processor: Async callable that takes item payload and returns result
            batch_id: Optional batch identifier for tracking

        Returns:
            BatchReport with all results and statistics
        """
        import time
        import uuid

        batch_id = batch_id or f"batch-{str(uuid.uuid4())[:8]}"
        logger.info("[BatchService] Starting batch %s with %d items (concurrency=%d)",
                    batch_id, len(items), self.max_concurrency)

        t_start = time.monotonic()
        results: list[BatchResult[R]] = []

        async def _process_one(item: BatchItem[T]) -> BatchResult[R]:
            async with self._semaphore:
                t0 = time.monotonic()
                try:
                    result = await asyncio.wait_for(
                        processor(item.payload),
                        timeout=self.timeout_per_item_seconds,
                    )
                    elapsed = (time.monotonic() - t0) * 1000
                    return BatchResult(
                        item_id=item.item_id,
                        result=result,
                        success=True,
                        processing_time_ms=elapsed,
                    )
                except TimeoutError:
                    elapsed = (time.monotonic() - t0) * 1000
                    logger.warning("[BatchService] Timeout on item %s after %.0fms",
                                   item.item_id, elapsed)
                    return BatchResult(
                        item_id=item.item_id,
                        error=f"Timeout after {self.timeout_per_item_seconds}s",
                        success=False,
                        processing_time_ms=elapsed,
                    )
                except Exception as exc:
                    elapsed = (time.monotonic() - t0) * 1000
                    logger.error("[BatchService] Error on item %s: %s", item.item_id, exc)
                    if self.fail_fast:
                        raise
                    return BatchResult(
                        item_id=item.item_id,
                        error=str(exc),
                        success=False,
                        processing_time_ms=elapsed,
                    )

        tasks = [_process_one(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=not self.fail_fast)

        # Normalize exceptions to BatchResult if gather swallowed them
        normalized: list[BatchResult[R]] = []
        for r in results:
            if isinstance(r, Exception):
                normalized.append(BatchResult(item_id="unknown", error=str(r), success=False))
            else:
                normalized.append(r)

        total_time = (time.monotonic() - t_start) * 1000
        successful = sum(1 for r in normalized if r.success)
        failed = len(normalized) - successful

        report = BatchReport(
            batch_id=batch_id,
            total=len(items),
            successful=successful,
            failed=failed,
            results=normalized,
            errors=[r.error for r in normalized if r.error],
            completed_at=datetime.now(UTC),
            total_time_ms=total_time,
        )

        logger.info(
            "[BatchService] Batch %s done: %d/%d success in %.0fms",
            batch_id, successful, len(items), total_time,
        )
        return report
