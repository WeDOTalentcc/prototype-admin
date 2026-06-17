"""TDD EntityResolver class — FIX-P0-01.

Cobertura: 25 test cases para todos os branches da UX de disambiguação,
tipos de entidade, estratégias de match (exato/email/prefixo/fuzzy/acento).

RED FLAGS detectados (ver CLAUDE.md):
  - Assumes first match is correct → corrigido: disambiguation UX
  - Tries to use LLM to pick entity → proibido: resolver é 100% determinístico
"""
import pytest

from app.shared.entity_resolver import (
    EntityResolver,
    EntityResolverFactory,
    ResolvedEntity,
    ResolutionResult,
)
from app.shared.entities.registry import ENTITY_REGISTRY, EntityTypeDefinition, get_entity_type


# ── Entity Type Registry ──────────────────────────────────────────────────────

def test_all_four_entity_types_registered():
    for key in ("candidate", "job", "company", "user"):
        assert key in ENTITY_REGISTRY, f"Missing entity type: {key}"


def test_candidate_definition_has_required_fields():
    defn = ENTITY_REGISTRY["candidate"]
    assert defn.unique_id_field == "candidate_id"
    assert "email" in defn.searchable_fields
    assert "name" in defn.searchable_fields
    assert defn.table_name == "candidates"


def test_job_definition_has_required_fields():
    defn = ENTITY_REGISTRY["job"]
    assert defn.unique_id_field == "job_id"
    assert "title" in defn.searchable_fields
    assert defn.table_name == "job_vacancies"


def test_get_entity_type_raises_for_unknown():
    with pytest.raises(ValueError, match="Unknown entity type"):
        get_entity_type("dragon")


def test_get_entity_type_case_insensitive():
    defn = get_entity_type("CANDIDATE")
    assert defn.name == "Candidate"


# ── Fixtures ─────────────────────────────────────────────────────────────────

CANDIDATES = [
    {"candidate_id": "c1", "name": "João Silva",   "first_name": "João",   "last_name": "Silva",    "email": "joao@empresa.com"},
    {"candidate_id": "c2", "name": "Maria Souza",  "first_name": "Maria",  "last_name": "Souza",    "email": "maria@empresa.com"},
    {"candidate_id": "c3", "name": "Carlos Mendes","first_name": "Carlos", "last_name": "Mendes",   "email": "carlos@empresa.com"},
    {"candidate_id": "c4", "name": "Ana Lima",     "first_name": "Ana",    "last_name": "Lima",     "email": "ana@empresa.com"},
    {"candidate_id": "c5", "name": "Pedro Costa",  "first_name": "Pedro",  "last_name": "Costa",    "email": "pedro@empresa.com"},
    {"candidate_id": "c6", "name": "Lucas Ferreira","first_name": "Lucas", "last_name": "Ferreira", "email": "lucas@empresa.com"},
]

JOBS = [
    {"job_id": "j1", "title": "Engenheiro de Software", "department": "Tecnologia"},
    {"job_id": "j2", "title": "Engenheiro de Dados",    "department": "Tecnologia"},
    {"job_id": "j3", "title": "Designer UX",            "department": "Produto"},
]


# ── Exact match ───────────────────────────────────────────────────────────────

def test_exact_email_match_auto_selects():
    """Spec: Exact match (email given) → selected with confidence=1.0"""
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "joao@empresa.com", CANDIDATES)
    assert result.selected is not None
    assert result.selected.entity_id == "c1"
    assert result.selected.confidence == 1.0


def test_exact_name_match_auto_selects():
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "Maria Souza", CANDIDATES)
    assert result.selected is not None
    assert result.selected.entity_id == "c2"


def test_no_false_positive_email_same_domain():
    """Other emails on same domain must NOT match a different user's email."""
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "maria@empresa.com", CANDIDATES)
    assert result.selected is not None
    assert result.selected.entity_id == "c2"   # not c1/c3/c4/c5/c6


# ── Case insensitive ──────────────────────────────────────────────────────────

def test_case_insensitive_name_match():
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "maria souza", CANDIDATES)
    assert result.selected is not None
    assert result.selected.entity_id == "c2"


def test_uppercase_email_match():
    """Spec: Case insensitive"""
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "JOAO@EMPRESA.COM", CANDIDATES)
    assert result.selected is not None
    assert result.selected.entity_id == "c1"


# ── Accent insensitive (João vs Joao) ─────────────────────────────────────────

def test_accent_insensitive_joao_vs_joao():
    """Spec: João vs Joao — must match despite missing tilde."""
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "Joao", CANDIDATES)
    assert result.selected is not None
    assert result.selected.entity_id == "c1"


def test_accent_insensitive_jose_vs_jose():
    candidates = [{"candidate_id": "cx", "name": "José Barros",
                   "first_name": "José", "last_name": "Barros", "email": "jose@x.com"}]
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "Jose Barros", candidates)
    assert result.selected is not None
    assert result.selected.entity_id == "cx"


# ── Partial / prefix match ────────────────────────────────────────────────────

def test_prefix_match_single_first_name():
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "Carlos", CANDIDATES)
    assert result.selected is not None
    assert result.selected.entity_id == "c3"


def test_job_title_partial_match():
    resolver = EntityResolver()
    result = resolver.resolve("job", "Designer UX", JOBS)
    assert result.selected is not None
    assert result.selected.entity_id == "j3"


# ── Fuzzy matching ────────────────────────────────────────────────────────────

def test_fuzzy_typo_yasmim_vs_yasmin():
    """Spec: Partial match (first name given) with typo tolerance."""
    candidates = [
        {"candidate_id": "c99", "name": "Yasmin Reis", "first_name": "Yasmin",
         "last_name": "Reis", "email": "yasmin@x.com"},
    ]
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "Yasmim Reis", candidates)
    assert result.selected is not None
    assert result.selected.entity_id == "c99"


# ── Disambiguation: 2-5 matches ───────────────────────────────────────────────

def test_two_to_five_matches_requires_disambiguation():
    """Spec: 2-5 matches → show list, ask user."""
    resolver = EntityResolver()
    result = resolver.resolve("job", "Engenheiro", JOBS)
    assert result.selected is None
    assert result.ambiguous is True
    assert result.requires_disambiguation is True
    assert 2 <= len(result.matches) <= 5
    assert result.error is None


def test_disambiguation_list_includes_both_matches():
    resolver = EntityResolver()
    result = resolver.resolve("job", "Engenheiro", JOBS)
    ids = [m.entity_id for m in result.matches]
    assert "j1" in ids
    assert "j2" in ids


# ── Disambiguation: >5 matches ────────────────────────────────────────────────

def test_more_than_five_matches_returns_error():
    """Spec: >5 matches → too ambiguous, ask for more context."""
    many_candidates = [
        {"candidate_id": f"c{i}", "name": f"Silva Pessoa {i}",
         "first_name": "Silva", "last_name": f"Pessoa {i}", "email": f"silva{i}@x.com"}
        for i in range(10)
    ]
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "Silva", many_candidates)
    assert result.selected is None
    assert result.ambiguous is True
    assert result.requires_disambiguation is False
    assert "please be more specific" in (result.error or "")
    assert len(result.matches) == 5  # truncated to top 5


# ── No match ──────────────────────────────────────────────────────────────────

def test_no_match_returns_error_message():
    """Spec: No match case."""
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "Zumbi das Flores", CANDIDATES)
    assert result.selected is None
    assert result.ambiguous is False
    assert result.error is not None
    assert "No match" in result.error


def test_empty_input_returns_error():
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "", CANDIDATES)
    assert result.selected is None
    assert result.error is not None


# ── All entity types ──────────────────────────────────────────────────────────

def test_job_entity_type():
    resolver = EntityResolver()
    result = resolver.resolve("job", "Designer UX", JOBS)
    assert result.selected is not None
    assert result.selected.entity_id == "j3"


def test_company_entity_type():
    companies = [
        {"company_id": "co1", "name": "WeDOTalent", "trade_name": "WeDO"},
        {"company_id": "co2", "name": "TechCorp",   "trade_name": "Tech"},
    ]
    resolver = EntityResolver()
    result = resolver.resolve("company", "WeDOTalent", companies)
    assert result.selected is not None
    assert result.selected.entity_id == "co1"


def test_user_entity_type():
    users = [
        {"user_id": "u1", "name": "Paulo Moraes", "first_name": "Paulo",
         "last_name": "Moraes", "email": "paulo@wedotalent.cc"},
    ]
    resolver = EntityResolver()
    result = resolver.resolve("user", "Paulo Moraes", users)
    assert result.selected is not None
    assert result.selected.entity_id == "u1"


# ── Confidence ordering ────────────────────────────────────────────────────────

def test_matches_sorted_by_confidence_descending():
    resolver = EntityResolver()
    result = resolver.resolve("job", "Engenheiro", JOBS)
    confs = [m.confidence for m in result.matches]
    assert confs == sorted(confs, reverse=True)


def test_exact_match_confidence_is_1_0():
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "João Silva", CANDIDATES)
    assert result.selected is not None
    assert result.selected.confidence == 1.0


# ── Factory ────────────────────────────────────────────────────────────────────

def test_factory_creates_resolver_for_valid_type():
    resolver = EntityResolverFactory.create("candidate")
    assert isinstance(resolver, EntityResolver)


def test_factory_raises_for_unknown_type():
    with pytest.raises(ValueError, match="Unknown entity type"):
        EntityResolverFactory.create("unknown_type")


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_candidates_list_returns_no_match():
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "João", [])
    assert result.selected is None
    assert result.error is not None


def test_row_missing_id_field_falls_back_to_id_key():
    """Rows may use 'id' instead of 'candidate_id'."""
    rows = [{"id": "fallback-id", "name": "Teste Fallback",
             "first_name": "Teste", "last_name": "Fallback", "email": "t@x.com"}]
    resolver = EntityResolver()
    result = resolver.resolve("candidate", "Teste Fallback", rows)
    assert result.selected is not None
    assert result.selected.entity_id == "fallback-id"
