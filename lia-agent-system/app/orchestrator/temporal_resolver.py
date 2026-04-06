# LIA-R01 — TemporalResolver: resolução de expressões temporais em PT-BR
# Suporte a: "ontem", "amanhã", "semana que vem", "mês passado", etc.
# Referência: Tezi AI usa NLP temporal para agendamentos; LIA precisa de equivalente PT-BR.

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum


class TemporalGranularity(str, Enum):
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
    confidence: float  # 0.0 to 1.0
    
    def as_iso_range(self) -> str:
        return f"{self.resolved_start.isoformat()}/{self.resolved_end.isoformat()}"


_PT_BR_PATTERNS: list[tuple[str, callable]] = []  # populated by _build_patterns()


def _build_patterns(today: date) -> list[tuple[re.Pattern, TemporalResult]]:
    """Build regex → TemporalResult mappings for PT-BR temporal expressions."""
    
    def week_start(d: date) -> date:
        return d - timedelta(days=d.weekday())
    
    def month_start(d: date) -> date:
        return d.replace(day=1)
    
    def month_end(d: date) -> date:
        # First day of next month minus 1
        if d.month == 12:
            return d.replace(year=d.year + 1, month=1, day=1) - timedelta(days=1)
        return d.replace(month=d.month + 1, day=1) - timedelta(days=1)
    
    w_start = week_start(today)
    m_start = month_start(today)
    
    patterns = [
        # Today
        (r"\b(hoje|today)\b", TemporalResult(
            original="hoje", resolved_start=today, resolved_end=today,
            granularity=TemporalGranularity.DAY, confidence=1.0)),
        # Yesterday
        (r"\b(ontem|yesterday)\b", TemporalResult(
            original="ontem",
            resolved_start=today - timedelta(days=1),
            resolved_end=today - timedelta(days=1),
            granularity=TemporalGranularity.DAY, confidence=1.0)),
        # Tomorrow
        (r"\b(amanh[ãa]|tomorrow)\b", TemporalResult(
            original="amanhã",
            resolved_start=today + timedelta(days=1),
            resolved_end=today + timedelta(days=1),
            granularity=TemporalGranularity.DAY, confidence=1.0)),
        # This week
        (r"\b(esta semana|essa semana|this week)\b", TemporalResult(
            original="esta semana",
            resolved_start=w_start,
            resolved_end=w_start + timedelta(days=6),
            granularity=TemporalGranularity.WEEK, confidence=1.0)),
        # Last week
        (r"\b(semana passada|last week)\b", TemporalResult(
            original="semana passada",
            resolved_start=w_start - timedelta(weeks=1),
            resolved_end=w_start - timedelta(days=1),
            granularity=TemporalGranularity.WEEK, confidence=1.0)),
        # Next week
        (r"\b(semana que vem|pr[oó]xima semana|next week)\b", TemporalResult(
            original="semana que vem",
            resolved_start=w_start + timedelta(weeks=1),
            resolved_end=w_start + timedelta(weeks=1, days=6),
            granularity=TemporalGranularity.WEEK, confidence=1.0)),
        # This month
        (r"\b(este m[eê]s|esse m[eê]s|this month)\b", TemporalResult(
            original="este mês",
            resolved_start=m_start,
            resolved_end=month_end(today),
            granularity=TemporalGranularity.MONTH, confidence=1.0)),
        # Last month
        (r"\b(m[eê]s passado|last month)\b", TemporalResult(
            original="mês passado",
            resolved_start=month_start(today.replace(day=1) - timedelta(days=1)),
            resolved_end=today.replace(day=1) - timedelta(days=1),
            granularity=TemporalGranularity.MONTH, confidence=1.0)),
        # Next month
        (r"\b(m[eê]s que vem|pr[oó]ximo m[eê]s|next month)\b", TemporalResult(
            original="mês que vem",
            resolved_start=month_start(month_end(today) + timedelta(days=1)),
            resolved_end=month_end(month_end(today) + timedelta(days=1)),
            granularity=TemporalGranularity.MONTH, confidence=1.0)),
        # Last 7 days
        (r"\b([uú]ltimos?\s+7\s+dias?|last\s+7\s+days?)\b", TemporalResult(
            original="últimos 7 dias",
            resolved_start=today - timedelta(days=7),
            resolved_end=today,
            granularity=TemporalGranularity.WEEK, confidence=0.95)),
        # Last 30 days
        (r"\b([uú]ltimos?\s+30\s+dias?|last\s+30\s+days?)\b", TemporalResult(
            original="últimos 30 dias",
            resolved_start=today - timedelta(days=30),
            resolved_end=today,
            granularity=TemporalGranularity.MONTH, confidence=0.95)),
        # Last N days (generic)
        (r"\b[uú]ltimos?\s+(\d+)\s+dias?\b", None),  # handled specially below
    ]
    
    compiled = []
    for pattern_str, result in patterns:
        if result is not None:
            compiled.append((re.compile(pattern_str, re.IGNORECASE), result))
    
    return compiled


class TemporalResolver:
    """Resolves PT-BR temporal expressions to concrete date ranges.
    
    LIA-R01: Necessário para o orchestrator interpretar queries como
    "candidatos da semana passada" ou "vagas abertas este mês".
    
    Referência: HireEZ e Tezi AI usam NLP temporal para filtros de busca.
    """
    
    def __init__(self, reference_date: date | None = None):
        self._today = reference_date or date.today()
        self._patterns = _build_patterns(self._today)
        # Generic N-days pattern
        self._n_days_pattern = re.compile(
            r"\b[uú]ltimos?\s+(\d+)\s+dias?\b", re.IGNORECASE
        )
        # ISO date range pattern: YYYY-MM-DD a YYYY-MM-DD
        self._iso_range_pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2})\s+a\s+(\d{4}-\d{2}-\d{2})"
        )
        # ISO single date
        self._iso_date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
    
    def resolve(self, text: str) -> TemporalResult | None:
        """Attempt to resolve a temporal expression in the given text.
        
        Returns the first match found, or None if no temporal expression detected.
        """
        # Try explicit patterns first (highest confidence)
        for pattern, result in self._patterns:
            m = pattern.search(text)
            if m:
                # Return a copy with original set to the matched text
                return TemporalResult(
                    original=m.group(0),
                    resolved_start=result.resolved_start,
                    resolved_end=result.resolved_end,
                    granularity=result.granularity,
                    confidence=result.confidence,
                )
        
        # Generic "últimos N dias"
        m = self._n_days_pattern.search(text)
        if m:
            n = int(m.group(1))
            return TemporalResult(
                original=m.group(0),
                resolved_start=self._today - timedelta(days=n),
                resolved_end=self._today,
                granularity=TemporalGranularity.DAY,
                confidence=0.9,
            )
        
        # ISO range "2024-01-01 a 2024-01-31"
        m = self._iso_range_pattern.search(text)
        if m:
            try:
                start = date.fromisoformat(m.group(1))
                end = date.fromisoformat(m.group(2))
                return TemporalResult(
                    original=m.group(0),
                    resolved_start=start,
                    resolved_end=end,
                    granularity=TemporalGranularity.EXACT,
                    confidence=1.0,
                )
            except ValueError:
                pass
        
        # Single ISO date
        m = self._iso_date_pattern.search(text)
        if m:
            try:
                d = date.fromisoformat(m.group(1))
                return TemporalResult(
                    original=m.group(0),
                    resolved_start=d,
                    resolved_end=d,
                    granularity=TemporalGranularity.EXACT,
                    confidence=1.0,
                )
            except ValueError:
                pass
        
        return None
    
    def resolve_all(self, text: str) -> list[TemporalResult]:
        """Find all temporal expressions in text."""
        results = []
        remaining = text
        while True:
            result = self.resolve(remaining)
            if result is None:
                break
            results.append(result)
            # Remove matched portion to find next
            remaining = remaining.replace(result.original, " ", 1)
        return results
    
    def inject_date_context(self, text: str) -> str:
        """Replace temporal expressions with ISO date ranges for LLM context.
        
        Example: "semana passada" → "semana passada [2024-03-11/2024-03-17]"
        """
        result = self.resolve(text)
        if result:
            replacement = f"{result.original} [{result.as_iso_range()}]"
            return text.replace(result.original, replacement, 1)
        return text
