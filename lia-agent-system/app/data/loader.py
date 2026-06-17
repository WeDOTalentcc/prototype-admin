"""
app/data/loader.py — Fixture loader for job template data.

All job template data lives in app/data/fixtures/*.json.
This module provides the same public API that the old Python data files exposed,
so all existing imports continue to work unchanged.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@lru_cache(maxsize=64)
def _load_fixture(name: str) -> Any:
    """Load a JSON fixture file by name (cached)."""
    path = FIXTURES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# ─── Public constants (same names as old Python modules) ─────────────────────

@lru_cache(maxsize=1)
def _get_tech_templates() -> list:
    return _load_fixture("curated_templates_tech")

@lru_cache(maxsize=1)
def _get_vendas_templates() -> list:
    return _load_fixture("curated_templates_vendas")

@lru_cache(maxsize=1)
def _get_rh_templates() -> list:
    return _load_fixture("curated_templates_rh")

@lru_cache(maxsize=1)
def _get_financas_templates() -> list:
    return _load_fixture("curated_templates_financas")

@lru_cache(maxsize=1)
def _get_marketing_templates() -> list:
    return _load_fixture("curated_templates_marketing")

@lru_cache(maxsize=1)
def _get_operacoes_data() -> dict:
    return _load_fixture("curated_templates_operacoes")

@lru_cache(maxsize=1)
def _get_customer_success_templates() -> list:
    return _load_fixture("curated_templates_customer_success")

@lru_cache(maxsize=1)
def _get_administrativo_templates() -> list:
    return _load_fixture("curated_templates_administrativo")

@lru_cache(maxsize=1)
def _get_cs_templates() -> list:
    return _load_fixture("curated_templates_cs")

@lru_cache(maxsize=1)
def _get_saude_templates() -> list:
    return _load_fixture("curated_templates_saude")

@lru_cache(maxsize=1)
def _get_categories_data() -> dict:
    return _load_fixture("template_categories")


# ─── Properties matching old module-level variables ──────────────────────────

def get_tech_templates() -> list:
    return _get_tech_templates()

def get_vendas_templates() -> list:
    return _get_vendas_templates()

def get_rh_templates() -> list:
    return _get_rh_templates()

def get_financas_templates() -> list:
    return _get_financas_templates()

def get_marketing_templates() -> list:
    return _get_marketing_templates()

def get_operacoes_templates() -> list:
    return _get_operacoes_data().get("OPERACOES_TEMPLATES", [])

def get_juridico_templates() -> list:
    return _get_operacoes_data().get("JURIDICO_TEMPLATES", [])

def get_engenharia_templates() -> list:
    return _get_operacoes_data().get("ENGENHARIA_TEMPLATES", [])

def get_customer_success_templates() -> list:
    return _get_customer_success_templates()

def get_administrativo_templates() -> list:
    return _get_administrativo_templates()

def get_cs_templates() -> list:
    return _get_cs_templates()

def get_saude_templates() -> list:
    return _get_saude_templates()

def get_brazilian_templates() -> list:
    return _load_fixture("brazilian_job_templates")


# ─── Category metadata ────────────────────────────────────────────────────────

def get_template_categories() -> dict:
    return _get_categories_data()["categories"]

def get_category_aliases() -> dict:
    return _get_categories_data()["category_aliases"]

def get_subcategory_aliases() -> dict:
    return _get_categories_data()["subcategory_aliases"]
