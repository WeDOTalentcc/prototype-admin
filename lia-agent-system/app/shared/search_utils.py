"""
Shared utilities for search query handling.

Post-mortem 2026-04-29 wizard UAT — Bug 5: a user query like
"candidatos?" was passed verbatim to the candidate search service. The
search index tokenizer treated "candidatos?" as a literal token (not
matching "candidatos") and returned zero results.

This module provides a single canonical normalization function so all
search call-sites converge on the same behavior. Centralizing here also
gives us one place to extend (Portuguese stopwords, accent folding,
synonym expansion) without touching every call-site.

Skill canônica: harness-engineering [guide computacional] —
single source of truth for query preprocessing.
"""
from __future__ import annotations

import re

# Trailing/leading punctuation we strip. Hyphens are preserved (back-end)
# and apostrophes/quotes are preserved (search phrases).
_TRAILING_PUNCT_RE = re.compile(r"[?.;:,!]+$")
_LEADING_PUNCT_RE = re.compile(r"^[?.;:,!]+")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_search_query(query: str | None) -> str:
    """Normalize a free-text search query for downstream tokenization.

    Operations (in order):
      1. Trim leading/trailing whitespace.
      2. Remove trailing punctuation (e.g. "candidatos?" → "candidatos").
      3. Remove leading punctuation (e.g. "? candidatos" → "candidatos").
      4. Collapse runs of whitespace to a single space.
      5. Final strip.

    Operations explicitly NOT performed (preserve user intent):
      - Lowercase: search backends often handle case themselves; lowercasing
        here would surprise users searching for proper nouns.
      - Accent folding: Portuguese accents are part of meaningful tokens.
      - Stopword removal: would drop short queries entirely.

    Returns the empty string for None / empty / whitespace-only input.

    Examples:
        >>> normalize_search_query("candidatos?")
        'candidatos'
        >>> normalize_search_query("   Python   sênior   ")
        'Python sênior'
        >>> normalize_search_query("? candidatos ?")
        'candidatos'
        >>> normalize_search_query("back-end developer")
        'back-end developer'
        >>> normalize_search_query(None)
        ''
        >>> normalize_search_query("")
        ''
    """
    if not query:
        return ""
    q = query.strip()
    if not q:
        return ""
    q = _TRAILING_PUNCT_RE.sub("", q)
    q = _LEADING_PUNCT_RE.sub("", q)
    q = _WHITESPACE_RE.sub(" ", q)
    return q.strip()
