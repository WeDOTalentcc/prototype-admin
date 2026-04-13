import json
import logging
import os
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger("lia.billing.consumption_audit")

CONSUMPTION_LOG_RETENTION_DAYS = int(os.environ.get("CONSUMPTION_LOG_RETENTION_DAYS", "730"))

APIFY_USD_TO_BRL_RATE = float(os.environ.get("APIFY_USD_TO_BRL_RATE", "5.50"))

_PII_PATTERNS = [
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b\d{3}[\.\-]?\d{3}[\.\-]?\d{3}[\-]?\d{2}\b"), "[CPF_REDACTED]"),
    (re.compile(r"\b\d{10,11}\b"), "[PHONE_REDACTED]"),
]


def _redact_pii(text: str | None) -> str | None:
    if not text:
        return text
    result = text
    for pattern, replacement in _PII_PATTERNS:
        result = pattern.sub(replacement, result)
    if len(result) > 200:
        result = result[:200] + "...[TRUNCATED]"
    return result


class ConsumptionAuditLogger:

    @staticmethod
    def log_operation(
        company_id: str,
        user_id: str | None,
        operation: str,
        provider: str,
        cost_usd: float,
        success: bool,
        duration_ms: int = 0,
        pipeline_id: str | None = None,
        actor_id: str | None = None,
        model_name: str | None = None,
        tokens_input: int | None = None,
        tokens_output: int | None = None,
        error_message: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cost_brl = round(cost_usd * APIFY_USD_TO_BRL_RATE, 4)
        record = {
            "event": "consumption_operation",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "company_id": company_id,
            "user_id": user_id,
            "operation": operation,
            "provider": provider,
            "cost_usd": round(cost_usd, 6),
            "cost_brl": cost_brl,
            "success": success,
            "duration_ms": duration_ms,
            "pipeline_id": pipeline_id,
            "actor_id": actor_id,
            "model_name": model_name,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "error_message": _redact_pii(error_message),
            "retention_days": CONSUMPTION_LOG_RETENTION_DAYS,
        }
        if extra:
            record["extra"] = extra

        logger.info(json.dumps(record, ensure_ascii=False))
        return record

    @staticmethod
    def log_budget_alert(
        company_id: str,
        category: str,
        current_spend_usd: float,
        budget_usd: float,
        usage_percentage: float,
    ) -> dict[str, Any]:
        record = {
            "event": "budget_alert",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "company_id": company_id,
            "category": category,
            "current_spend_usd": round(current_spend_usd, 4),
            "budget_usd": round(budget_usd, 2),
            "usage_percentage": round(usage_percentage, 1),
            "retention_days": CONSUMPTION_LOG_RETENTION_DAYS,
        }
        logger.warning(json.dumps(record, ensure_ascii=False))
        return record

    @staticmethod
    def log_invoice_generated(
        company_id: str,
        year: int,
        month: int,
        total_usd: float,
        total_brl: float,
        line_count: int,
    ) -> dict[str, Any]:
        record = {
            "event": "invoice_generated",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "company_id": company_id,
            "period": f"{year}-{month:02d}",
            "total_usd": round(total_usd, 4),
            "total_brl": round(total_brl, 2),
            "line_count": line_count,
            "retention_days": CONSUMPTION_LOG_RETENTION_DAYS,
        }
        logger.info(json.dumps(record, ensure_ascii=False))
        return record
