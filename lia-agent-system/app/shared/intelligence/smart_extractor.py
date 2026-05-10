import hashlib
import logging
import re
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.shared.intelligence.param_patterns import (
    UNIVERSAL_PATTERNS,
    ExtractionResult,
    get_patterns_for_domain,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedParams:
    params: dict[str, Any] = field(default_factory=dict)
    source: str = "none"
    confidence: float = 0.0
    cached: bool = False
    extraction_time_ms: float = 0.0
    extraction_details: list[ExtractionResult] = field(default_factory=list)

    @property
    def has_params(self) -> bool:
        return len(self.params) > 0


class ExtractionCache:
    def __init__(self, ttl_seconds: int = 300, max_entries: int = 200):
        self._cache: dict[str, tuple] = {}
        self._ttl = ttl_seconds
        self._max_entries = max_entries

    def _make_key(self, query: str, domain_id: str) -> str:
        normalized = self._normalize(query)
        return hashlib.md5(f"{domain_id}:{normalized}".encode()).hexdigest()

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = unicodedata.normalize("NFKD", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def get(self, query: str, domain_id: str) -> ExtractedParams | None:
        key = self._make_key(query, domain_id)
        if key in self._cache:
            result, expires_at = self._cache[key]
            if datetime.utcnow().timestamp() < expires_at:
                cached_result = ExtractedParams(
                    params=dict(result.params),
                    source="cached",
                    confidence=result.confidence,
                    cached=True,
                    extraction_time_ms=0.0,
                    extraction_details=list(result.extraction_details),
                )
                return cached_result
            else:
                del self._cache[key]
        return None

    def set(self, query: str, domain_id: str, result: ExtractedParams) -> None:
        if len(self._cache) >= self._max_entries:
            self._evict_oldest()
        key = self._make_key(query, domain_id)
        expires_at = datetime.utcnow().timestamp() + self._ttl
        self._cache[key] = (result, expires_at)

    def _evict_oldest(self) -> None:
        if not self._cache:
            return
        oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]

    def clear(self) -> None:
        self._cache.clear()

    def size(self) -> int:
        return len(self._cache)


class ParamExtractor:
    def extract(self, query: str, domain_id: str | None = None) -> ExtractedParams:
        start = time.monotonic()
        patterns = get_patterns_for_domain(domain_id) if domain_id else UNIVERSAL_PATTERNS

        results: list[ExtractionResult] = []
        params: dict[str, Any] = {}

        for pattern in patterns:
            for regex in pattern.patterns:
                try:
                    matches = re.finditer(regex, query, re.IGNORECASE)
                    for match in matches:
                        raw = match.group(0)
                        try:
                            value_group = match.group(pattern.group_index)
                        except (IndexError, AttributeError):
                            value_group = raw

                        if pattern.transform_fn:
                            try:
                                value = pattern.transform_fn(match)
                            except Exception:
                                value = value_group
                        else:
                            value = value_group

                        result = ExtractionResult(
                            name=pattern.name,
                            value=value,
                            raw_match=raw,
                            confidence=0.9,
                            source="regex",
                        )
                        results.append(result)

                        if pattern.name in params:
                            existing = params[pattern.name]
                            if isinstance(existing, list):
                                if value not in existing:
                                    existing.append(value)
                            else:
                                if existing != value:
                                    params[pattern.name] = [existing, value]
                        else:
                            params[pattern.name] = value
                except re.error as e:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.warning(f"Regex error for pattern '{pattern.name}': {e}")

        elapsed = (time.monotonic() - start) * 1000
        confidence = min(0.95, 0.3 + (len(results) * 0.15)) if results else 0.0

        return ExtractedParams(
            params=params,
            source="regex" if results else "none",
            confidence=confidence,
            cached=False,
            extraction_time_ms=elapsed,
            extraction_details=results,
        )


class SmartExtractor:
    def __init__(
        self,
        confidence_threshold: float = 0.8,
        cache_ttl: int = 300,
        cache_max_entries: int = 200,
    ):
        self._param_extractor = ParamExtractor()
        self._cache = ExtractionCache(ttl_seconds=cache_ttl, max_entries=cache_max_entries)
        self._confidence_threshold = confidence_threshold
        self._extraction_count = 0
        self._regex_only_count = 0
        self._llm_fallback_count = 0
        self._cache_hit_count = 0

    def extract(
        self,
        query: str,
        domain_id: str | None = None,
        available_actions: list[str] | None = None,
    ) -> ExtractedParams:
        self._extraction_count += 1

        cached = self._cache.get(query, domain_id or "universal")
        if cached:
            self._cache_hit_count += 1
            logger.debug(f"SmartExtractor cache hit for domain={domain_id}")
            return cached

        result = self._param_extractor.extract(query, domain_id)

        if result.confidence >= self._confidence_threshold:
            self._regex_only_count += 1
            self._cache.set(query, domain_id or "universal", result)
            logger.debug(
                f"SmartExtractor regex-only: {len(result.params)} params, "
                f"confidence={result.confidence:.2f}, time={result.extraction_time_ms:.1f}ms"
            )
            return result

        if result.has_params:
            result.source = "hybrid"
            self._llm_fallback_count += 1
        else:
            result.source = "none"

        self._cache.set(query, domain_id or "universal", result)
        logger.debug(
            f"SmartExtractor {result.source}: {len(result.params)} params, "
            f"confidence={result.confidence:.2f}"
        )
        return result

    def get_stats(self) -> dict[str, Any]:
        total = self._extraction_count or 1
        return {
            "total_extractions": self._extraction_count,
            "regex_only_count": self._regex_only_count,
            "llm_fallback_count": self._llm_fallback_count,
            "cache_hit_count": self._cache_hit_count,
            "regex_only_rate": self._regex_only_count / total,
            "cache_hit_rate": self._cache_hit_count / total,
            "cache_size": self._cache.size(),
        }

    def clear_cache(self) -> None:
        self._cache.clear()
