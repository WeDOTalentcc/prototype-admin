"""
email_templates_data.py — Compatibility stub.

DEFAULT_TEMPLATES is now loaded from app/data/fixtures/email_default_templates.json.
"""
import json
from functools import lru_cache
from pathlib import Path

_FIXTURES = Path(__file__).parent.parent.parent.parent / "data/fixtures"


@lru_cache(maxsize=1)
def _load() -> list:
    return json.loads((_FIXTURES / "email_default_templates.json").read_text(encoding="utf-8"))


DEFAULT_TEMPLATES = _load()
