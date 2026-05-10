"""JdSimilarService — Sprint B Phase 1.

Orchestration layer entre repositório de JD History e o EmbeddingService.

Responsabilidades:
- Consultar histórico de JDs similares quando recruiter inicia wizard
- Persistir JDs no histórico ao publicar vaga (record_jd)
- Atualizar outcome quando vaga preenche (mark_filled)

Multi-tenancy: company_id sempre obrigatório.
PII: embedding gerado APENAS de title + responsibilities — nunca candidate data.
Fail-open: erros em EmbeddingService não bloqueiam o wizard.
ADR-006: nenhum log inclui PII (apenas IDs).
"""
from __future__ import annotations

import logging
import re
from typing import Any
from uuid import UUID

from app.domains.job_creation.repositories.jd_similar_history_repository import (
    JD_SIMILAR_MIN_HISTORY,
    JdSimilarHistoryRepository,
)

logger = logging.getLogger(__name__)


# Embedding dim válida (consistente com OpenAI text-embedding-3-small)
JD_EMBEDDING_DIM = 1536


# ── PII Redactor (Sprint B Phase 1, gap C4) ────────────────────────────────
#
# Defense-in-depth: even though _build_embedding_text only pulls from JD
# fields (title, responsibilities, requirements), recruiters routinely paste
# free-text content that contains candidate PII (CPF/CNPJ/email/phone). This
# redactor runs computational regex BEFORE the embedding API call so PII
# never leaves the platform via OpenAI text-embedding-3-small.
#
# CLAUDE.md non-negotiable rule #2 (LGPD) + harness sensor (computational).

# Brazilian CNPJ: 14 digits, optionally formatted XX.XXX.XXX/XXXX-XX
_CNPJ_RE = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/\d{4}-?\d{2}\b")
# Brazilian CPF formatted: XXX.XXX.XXX-XX
_CPF_FORMATTED_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
# Email: standard, conservative
_EMAIL_RE = re.compile(r"\b[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
# Brazilian phones formatted: (DD) 9XXXX-XXXX, +55 DD 9XXXX-XXXX, DD 9XXXX-XXXX
_PHONE_FORMATTED_RE = re.compile(
    r"(?:\+?55\s?)?"           # optional +55 country code
    r"\(?\d{2}\)?\s?"           # 2-digit DDD, optional parens
    r"9?\d{4}[-\s]\d{4}"        # 8 or 9 digits with required separator
)

# Context-aware unformatted patterns. Bare 11-digit sequences are ambiguous
# (could be CPF or 9-digit cellphone with DDD), so we look at preceding
# keywords to disambiguate. Non-greedy keyword + optional separator + digits.
_CPF_CONTEXTUAL_RE = re.compile(
    r"(?:cpf|documento|doc\.|rg)[\s:.\-]+(\d{11})\b",
    flags=re.IGNORECASE,
)
_PHONE_CONTEXTUAL_RE = re.compile(
    r"(?:telefone|tel\.?|cel(?:ular)?\.?|whatsapp|whats|fone|contato)[\s:.\-]+"
    r"(\+?\d{10,13})\b",
    flags=re.IGNORECASE,
)
# Bare 11-digit sequences without context default to CPF (more sensitive
# data class — fail-safe: redact as CPF rather than expose).
_CPF_BARE_RE = re.compile(r"(?<!\d)\d{11}(?!\d)")
# 10-digit sequences default to phone (BR landline format).
_PHONE_BARE_RE = re.compile(r"(?<!\d)\d{10}(?!\d)")


def _redact_pii(text: str) -> str:
    """Replace CPF/CNPJ/email/phone in text with placeholder tokens.

    Strategy (Sprint B Phase 1, gap C4):
    1. Formatted patterns first (CNPJ → CPF → email → phone) — unambiguous.
    2. Contextual unformatted: keyword-prefixed digits ("Telefone 11999991234"
       → [TEL]; "CPF 11122233344" → [CPF]).
    3. Bare 11-digit defaults to [CPF] (fail-safe: most sensitive class).
    4. Bare 10-digit defaults to [TEL] (BR landline pattern).

    Non-PII numeric content (years 2024, version 3.11, "5+ anos", team sizes)
    is preserved — patterns require specific digit counts (≥10 for phone,
    exactly 11 for unformatted CPF).
    """
    if not text:
        return text
    out = _CNPJ_RE.sub("[CNPJ]", text)
    out = _CPF_FORMATTED_RE.sub("[CPF]", out)
    out = _EMAIL_RE.sub("[EMAIL]", out)
    out = _PHONE_FORMATTED_RE.sub("[TEL]", out)
    # Context-aware before bare-default fallback
    out = _PHONE_CONTEXTUAL_RE.sub("[TEL]", out)
    out = _CPF_CONTEXTUAL_RE.sub("[CPF]", out)
    # Bare numeric defaults
    out = _CPF_BARE_RE.sub("[CPF]", out)
    out = _PHONE_BARE_RE.sub("[TEL]", out)
    return out


def _build_embedding_text(title: str, jd_enriched: dict[str, Any] | None = None) -> str:
    """Constrói o texto que será embedado.

    Inclui: title + responsibilities + requirements (concat).
    EXCLUI: salário, dados de candidatos, info confidencial.
    Mantém ADR-006 (sem PII via field-level filter + regex redactor).
    """
    parts: list[str] = [title.strip()] if title else []
    if jd_enriched:
        responsibilities = jd_enriched.get("responsibilities") or []
        if isinstance(responsibilities, list):
            parts.extend(str(r) for r in responsibilities if r)
        requirements = jd_enriched.get("requirements") or []
        if isinstance(requirements, list):
            parts.extend(str(r) for r in requirements if r)
    # Apply PII redactor to every part before joining (gap C4).
    redacted = [_redact_pii(p) for p in parts if p]
    return " | ".join(redacted)


def _normalize_title(title: str) -> str:
    """Normaliza título pra busca consistente."""
    if not title:
        return ""
    return " ".join(title.lower().strip().split())


class JdSimilarService:
    """Wraps JdSimilarHistoryRepository + EmbeddingService.

    Construtor recebe instances injetadas (testável).
    """

    def __init__(
        self,
        repository: JdSimilarHistoryRepository,
        embedding_service: Any,
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service

    # ── Read ────────────────────────────────────────────────────────────────

    async def find_similar(
        self,
        company_id: str,
        title: str,
        department: str | None = None,
        toggle_enabled: bool = True,
        min_similarity: float = 0.7,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Returns top-N JDs similares se toggle ON e thresh atendido. Fail-open."""
        if not toggle_enabled:
            return []
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy)")

        # Skip embedding cost se threshold não bate
        try:
            count = await self.repository.count_for_company(company_id)
        except Exception as exc:
            logger.warning(
                "[JdSimilar] count_for_company failed (fail-open): %s",
                str(exc)[:200],
            )
            return []
        if count < JD_SIMILAR_MIN_HISTORY:
            return []

        # Generate embedding (fail-open if EmbeddingService crashes)
        embedding_text = _build_embedding_text(
            title=title,
            jd_enriched={"responsibilities": [department]} if department else None,
        )
        try:
            embedding = await self.embedding_service.generate_embedding(
                embedding_text,
            )
        except Exception as exc:
            logger.warning(
                "[JdSimilar] embedding generation failed (fail-open): %s",
                str(exc)[:200],
            )
            return []
        if not embedding or len(embedding) != JD_EMBEDDING_DIM:
            logger.warning(
                "[JdSimilar] invalid embedding dim (got %s, expected %d) — fail-open",
                len(embedding) if embedding else "None",
                JD_EMBEDDING_DIM,
            )
            return []

        try:
            return await self.repository.find_similar_jds(
                company_id=company_id,
                embedding=embedding,
                min_similarity=min_similarity,
                limit=limit,
                department=department,
            )
        except Exception as exc:
            logger.warning(
                "[JdSimilar] find_similar_jds query failed (fail-open): %s",
                str(exc)[:200],
            )
            return []

    # ── Write ───────────────────────────────────────────────────────────────

    async def record_jd(
        self,
        company_id: str,
        job_id: str,
        title: str,
        jd_enriched: dict[str, Any],
        seniority_level: str | None = None,
        department: str | None = None,
    ) -> None:
        """Persiste JD no histórico ao publicar vaga.

        Multi-tenancy: company_id obrigatório.
        PII: embedding gerado de title + responsibilities apenas.
        Fail-soft: se embedding falhar, persiste sem embedding (similarity desabilitada).
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy)")

        embedding_text = _build_embedding_text(title, jd_enriched)
        embedding: list[float] | None = None
        try:
            embedding = await self.embedding_service.generate_embedding(embedding_text)
            if embedding and len(embedding) != JD_EMBEDDING_DIM:
                logger.warning(
                    "[JdSimilar.record_jd] invalid embedding dim (job_id=%s)",
                    job_id,
                )
                embedding = None
        except Exception as exc:
            logger.warning(
                "[JdSimilar.record_jd] embedding failed (job_id=%s, fail-soft): %s",
                job_id, str(exc)[:200],
            )
            embedding = None

        if embedding is None:
            # Skip persistence quando embedding falha — sem embedding,
            # JD não é útil pra similarity search depois
            logger.info(
                "[JdSimilar.record_jd] skipping record (no embedding) job_id=%s",
                job_id,
            )
            return

        try:
            await self.repository.record_jd(
                company_id=company_id,
                job_id=job_id,
                title_normalized=_normalize_title(title),
                jd_enriched=jd_enriched,
                embedding=embedding,
                seniority_level=seniority_level,
                department=department,
            )
            logger.info(
                "[JdSimilar.record_jd] persisted job_id=%s company_id=%s",
                job_id, company_id,
            )
        except Exception as exc:
            logger.error(
                "[JdSimilar.record_jd] persist failed (job_id=%s): %s",
                job_id, str(exc)[:200],
            )
            # Re-raise — caller decide se vaga publica mesmo com falha de record
            raise

    async def mark_filled(
        self,
        company_id: str,
        job_id: str,
        time_to_fill_days: int,
        candidates_count: int,
    ) -> None:
        """Marca outcome quando vaga preenche."""
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy)")
        try:
            record_id = await self.repository.find_id_by_job(
                company_id=company_id,
                job_id=job_id,
            )
        except Exception as exc:
            logger.warning(
                "[JdSimilar.mark_filled] lookup failed (job_id=%s): %s",
                job_id, str(exc)[:200],
            )
            return
        if record_id is None:
            logger.debug(
                "[JdSimilar.mark_filled] no record for job_id=%s (skip)",
                job_id,
            )
            return

        await self.repository.mark_filled(
            record_id=record_id,
            company_id=company_id,
            time_to_fill_days=time_to_fill_days,
            candidates_count=candidates_count,
        )
        logger.info(
            "[JdSimilar.mark_filled] job_id=%s filled in %dd, %d candidates",
            job_id, time_to_fill_days, candidates_count,
        )

    async def increment_reuse(
        self,
        company_id: str,
        record_id: str | UUID,
    ) -> None:
        """Incrementa contador quando recruiter reaproveita JD do histórico."""
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy)")
        rec_uuid = record_id if isinstance(record_id, UUID) else UUID(str(record_id))
        await self.repository.increment_reuse(rec_uuid, company_id=company_id)


# -- Sync wire helper (sync nodes calling async service) ---------------------


def record_jd_fire_and_forget(
    company_id: str,
    job_id: str,
    title: str,
    jd_enriched: dict[str, Any],
    seniority_level: str | None = None,
    department: str | None = None,
) -> None:
    """Fire-and-forget wrapper for sync callers (e.g., LangGraph publish_node).

    Spawns a daemon thread with its own asyncio event loop and runs record_jd().
    NEVER raises - failures are logged but never bubble up to the caller.

    Multi-tenancy: company_id required.
    Use case: graph.py publish_node (sync) needs to fire async record_jd
    after Rails API publish succeeds. Without blocking the wizard return.
    """
    if not company_id or not job_id or not title:
        logger.debug(
            "[JdSimilar.fire_and_forget] missing required fields (company=%s job=%s)",
            bool(company_id), bool(job_id),
        )
        return

    import threading

    def _runner() -> None:
        import asyncio

        async def _run() -> None:
            try:
                from app.shared.intelligence.embedding_service import EmbeddingService
                from lia_config.database import async_session_factory

                async with async_session_factory() as db:
                    repo = JdSimilarHistoryRepository(db)
                    embed_svc = EmbeddingService()
                    svc = JdSimilarService(
                        repository=repo, embedding_service=embed_svc,
                    )
                    await svc.record_jd(
                        company_id=company_id,
                        job_id=job_id,
                        title=title,
                        jd_enriched=jd_enriched,
                        seniority_level=seniority_level,
                        department=department,
                    )
            except Exception as exc:
                logger.warning(
                    "[JdSimilar.fire_and_forget] record failed (job_id=%s): %s",
                    job_id, str(exc)[:200],
                )

        try:
            asyncio.run(_run())
        except Exception as exc:
            logger.warning(
                "[JdSimilar.fire_and_forget] event loop error (job_id=%s): %s",
                job_id, str(exc)[:200],
            )

    thread = threading.Thread(target=_runner, daemon=True, name=f"jd-record-{job_id[:8]}")
    thread.start()
