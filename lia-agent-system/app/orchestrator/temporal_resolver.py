"""
TemporalResolver — LIA-R01

Parses natural-language temporal expressions from recruiting queries (PT-BR + EN)
and resolves them to concrete date ranges. Used by Analytics and RecruitmentAssistant
to translate "últimos 30 dias", "esta semana", etc. into ISO date pairs.

harness-engineering guide: computacional/determinístico — sem LLM call.
"""
from __future__ import annotations

import re
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import StrEnum
from typing import List, Optional


class TemporalGranularity(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    EXACT = "exact"


@dataclass
class TemporalResult:
    original: str
    resolved_start: date
    resolved_end: date
    granularity: TemporalGranularity
    confidence: float = 1.0
    warnings: List[str] = field(default_factory=list)

    def as_iso_range(self) -> str:
        return f"{self.resolved_start.isoformat()}/{self.resolved_end.isoformat()}"


# ---------------------------------------------------------------------------
# Pattern table — matched in order (more specific first)
# ---------------------------------------------------------------------------

def _week_start(ref: date) -> date:
    """Monday of the week containing ref."""
    return ref - timedelta(days=ref.weekday())


def _month_start(ref: date) -> date:
    return ref.replace(day=1)


def _month_end(ref: date) -> date:
    _, last = monthrange(ref.year, ref.month)
    return ref.replace(day=last)


def _prev_month_start(ref: date) -> date:
    first = ref.replace(day=1)
    prev = first - timedelta(days=1)
    return prev.replace(day=1)


def _prev_month_end(ref: date) -> date:
    first = ref.replace(day=1)
    prev = first - timedelta(days=1)
    return prev


def _next_week_start(ref: date) -> date:
    ws = _week_start(ref)
    return ws + timedelta(weeks=1)


def _next_week_end(ref: date) -> date:
    return _next_week_start(ref) + timedelta(days=6)


class TemporalResolver:
    """
    Resolves natural-language temporal expressions to TemporalResult.

    Usage:
        resolver = TemporalResolver()
        result = resolver.resolve("candidatos dos últimos 30 dias")
        print(result.as_iso_range())  # "2026-03-10/2026-04-09"
    """

    def __init__(self, reference_date: Optional[date] = None):
        self._ref = reference_date or date.today()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, text: str) -> Optional[TemporalResult]:
        """Return the first temporal expression found in text, or None."""
        if not text:
            return None
        results = self._match_all(text)
        return results[0] if results else None

    def resolve_all(self, text: str) -> List[TemporalResult]:
        """Return all temporal expressions found in text."""
        if not text:
            return []
        return self._match_all(text)

    def inject_date_context(self, text: str) -> str:
        """Append resolved date ranges inline after matched expressions.

        Example:
            "candidatos de hoje" → "candidatos de hoje [2026-04-04/2026-04-04]"
        """
        results = self._match_all(text)
        if not results:
            return text
        # Append the first match's range to the original text
        out = text
        for r in results:
            out = out + f" [{r.as_iso_range()}]"
        return out

    # ------------------------------------------------------------------
    # Internal — pattern dispatch
    # ------------------------------------------------------------------

    def _match_all(self, text: str) -> List[TemporalResult]:
        ref = self._ref
        t = text.lower()
        results: List[TemporalResult] = []

        # ----------------------------------------------------------------
        # ISO date range: "2026-01-01 a 2026-01-31" / "2026-01-01/2026-01-31"
        # ----------------------------------------------------------------
        m = re.search(
            r"(\d{4}-\d{2}-\d{2})\s*(?:a|to|/)\s*(\d{4}-\d{2}-\d{2})", t
        )
        if m:
            try:
                start = date.fromisoformat(m.group(1))
                end = date.fromisoformat(m.group(2))
                results.append(TemporalResult(
                    original=m.group(0),
                    resolved_start=start,
                    resolved_end=end,
                    granularity=TemporalGranularity.EXACT,
                    confidence=1.0,
                ))
                return results
            except ValueError:
                # T-04 Tipo D: ISO date range parse failure (e.g. "2026-13-45")
                # is a non-match, not an error — fall through to try other
                # patterns (single date, "last N days", etc).
                pass

        # ----------------------------------------------------------------
        # Single ISO date: "2026-03-15"
        # ----------------------------------------------------------------
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", t)
        if m:
            try:
                d = date.fromisoformat(m.group(1))
                results.append(TemporalResult(
                    original=m.group(0),
                    resolved_start=d,
                    resolved_end=d,
                    granularity=TemporalGranularity.EXACT,
                    confidence=1.0,
                ))
                return results
            except ValueError:
                # T-04 Tipo D: single ISO date parse failure (e.g. "2026-02-30")
                # is a non-match, not an error — fall through to try other
                # patterns ("last N days", relative offsets, etc).
                pass

        # ----------------------------------------------------------------
        # Exact N days: "últimos N dias" / "last N days"
        # ----------------------------------------------------------------
        m = re.search(
            r"[uú]ltimos?\s+(\d+)\s+dias?|last\s+(\d+)\s+days?", t
        )
        if m:
            n = int(m.group(1) or m.group(2))
            results.append(TemporalResult(
                original=m.group(0),
                resolved_start=ref - timedelta(days=n),
                resolved_end=ref,
                granularity=TemporalGranularity.DAY,
                confidence=0.9,
            ))
            return results

        # ----------------------------------------------------------------
        # Today / ontem / amanhã
        # ----------------------------------------------------------------
        if re.search(r"\bhoje\b|today", t):
            results.append(TemporalResult(
                original="hoje",
                resolved_start=ref,
                resolved_end=ref,
                granularity=TemporalGranularity.DAY,
                confidence=1.0,
            ))
            return results

        if re.search(r"\bontem\b|yesterday", t):
            yesterday = ref - timedelta(days=1)
            results.append(TemporalResult(
                original="ontem",
                resolved_start=yesterday,
                resolved_end=yesterday,
                granularity=TemporalGranularity.DAY,
                confidence=1.0,
            ))
            return results

        if re.search(r"\bamanha\b|\bamanhã\b|tomorrow", t):
            tomorrow = ref + timedelta(days=1)
            results.append(TemporalResult(
                original="amanhã",
                resolved_start=tomorrow,
                resolved_end=tomorrow,
                granularity=TemporalGranularity.DAY,
                confidence=1.0,
            ))
            return results

        # ----------------------------------------------------------------
        # Semana passada / last week
        # ----------------------------------------------------------------
        if re.search(r"semana\s+passada|last\s+week", t):
            ws = _week_start(ref) - timedelta(weeks=1)
            we = ws + timedelta(days=6)
            results.append(TemporalResult(
                original="semana passada",
                resolved_start=ws,
                resolved_end=we,
                granularity=TemporalGranularity.WEEK,
                confidence=1.0,
            ))
            return results

        # ----------------------------------------------------------------
        # Semana que vem / next week
        # ----------------------------------------------------------------
        if re.search(r"semana\s+que\s+vem|next\s+week", t):
            ws = _next_week_start(ref)
            we = _next_week_end(ref)
            results.append(TemporalResult(
                original="semana que vem",
                resolved_start=ws,
                resolved_end=we,
                granularity=TemporalGranularity.WEEK,
                confidence=1.0,
            ))
            return results

        # ----------------------------------------------------------------
        # Esta semana / this week
        # ----------------------------------------------------------------
        if re.search(r"esta\s+semana|esse\s+semana|this\s+week", t):
            ws = _week_start(ref)
            we = ws + timedelta(days=6)
            results.append(TemporalResult(
                original="esta semana",
                resolved_start=ws,
                resolved_end=we,
                granularity=TemporalGranularity.WEEK,
                confidence=1.0,
            ))
            return results

        # ----------------------------------------------------------------
        # Mês passado / last month
        # ----------------------------------------------------------------
        if re.search(r"m[eê]s\s+passado|last\s+month", t):
            ms = _prev_month_start(ref)
            me = _prev_month_end(ref)
            results.append(TemporalResult(
                original="mês passado",
                resolved_start=ms,
                resolved_end=me,
                granularity=TemporalGranularity.MONTH,
                confidence=1.0,
            ))
            return results

        # ----------------------------------------------------------------
        # Este mês / esse mês / this month
        # ----------------------------------------------------------------
        if re.search(r"este\s+m[eê]s|esse\s+m[eê]s|this\s+month", t):
            ms = _month_start(ref)
            me = _month_end(ref)
            results.append(TemporalResult(
                original="este mês",
                resolved_start=ms,
                resolved_end=me,
                granularity=TemporalGranularity.MONTH,
                confidence=1.0,
            ))
            return results

        return results
