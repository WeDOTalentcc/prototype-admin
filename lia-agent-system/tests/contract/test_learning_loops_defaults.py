"""Contract tests — Learning Loops defaults canonical (F2.1 + F2.2 fix 2026-05-24).

Pins three contracts:

1. AUTOMATION_RULES_DEFAULTS["learning_loops"] contém todas as 5 chaves
   esperadas e o default LGPD-aligned (bigfive_department_history=False).
2. Helper canonical load_learning_loops_toggles devolve defaults canonical
   quando company não tem CompanyHiringPolicy (fail-soft).
3. Consumers em job_creation/services/*.py usam o helper canonical (não
   queries SQL inline) e não dependem de defaults literal `.get(key, default)`.

Background F2.1: audit 2026-05-24 descobriu 4 fontes paralelas divergindo
do default `bigfive_department_history` — backend constant=True, helper
docstring documenta False, frontend UI mostra False+requiresDisclosure,
consumer inline em bigfive_service.py:208 usa False. Conservative defaults
ganharam (ADR-LGPD-001 opt-in via disclosure modal canonical).

Background F2.2: jd_similar_service.record_jd_if_enabled mantinha lookup
inline de CompanyHiringPolicy (~30 linhas) em vez de delegar ao helper
canonical `load_learning_loops_toggles` (production-quality DRY violation).
"""
from __future__ import annotations

import inspect
import re
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def _restore_hiring_policy_repo():
    """Cleanup fixture — preserva module-level HiringPolicyRepository.

    Padrão necessário porque alguns testes deste helper precisam
    rebindar repo_mod.HiringPolicyRepository = MagicMock(...) para
    controlar o que o helper canonical chama. Sem este fixture, o
    rebind vaza para outros testes que mockam o repo no caminho canonical
    (e.g. tests/unit/test_handle_job_published_record_jd.py).
    """
    import app.domains.hiring_policy.repositories.hiring_policy_repository as repo_mod
    original = repo_mod.HiringPolicyRepository
    try:
        yield repo_mod
    finally:
        repo_mod.HiringPolicyRepository = original


# ── Contract 1: canonical defaults shape + LGPD-aligned values ──────────────


def test_canonical_defaults_bigfive_department_history_is_false_for_lgpd():
    """F2.1 fix 2026-05-24: aligned com UI requiresDisclosure + ADR-LGPD-001.

    ADR-LGPD-001 (CLAUDE.md) + ANPD Art. 12 §1 Guia de Anonimização: agregados
    com N >= 10 podem qualificar como anonimização, MAS o opt-in canonical
    via UI disclosure modal continua sendo o caminho seguro. Empresa nova
    (sem CompanyHiringPolicy) começa OFF, ativa explicitamente.
    """
    from app.models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS

    loops = AUTOMATION_RULES_DEFAULTS["learning_loops"]
    assert loops["bigfive_department_history"] is False, (
        "F2.1 fix: bigfive_department_history default DEVE ser False "
        "(ADR-LGPD-001 conservative + opt-in via UI canonical disclosure). "
        "Editar lia-agent-system/libs/models/lia_models/company_hiring_policy.py "
        "AUTOMATION_RULES_DEFAULTS['learning_loops']['bigfive_department_history']."
    )


def test_canonical_defaults_all_keys_present():
    """Schema canonical: AUTOMATION_RULES_DEFAULTS['learning_loops'] tem
    exatamente as 5 chaves esperadas com tipo bool. Helper canonical
    confia que TODAS estão presentes — consumers chamam toggles.get(key)
    sem default literal.
    """
    from app.models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS

    loops = AUTOMATION_RULES_DEFAULTS["learning_loops"]
    expected_keys = {
        "enabled",
        "bigfive_company_culture",
        "bigfive_department_history",
        "wsi_question_effectiveness",
        "jd_similar_suggestion",
    }
    assert set(loops.keys()) == expected_keys, (
        f"learning_loops keys drift: esperado={expected_keys}, "
        f"actual={set(loops.keys())}. Schema canonical em AUTOMATION_RULES_DEFAULTS."
    )
    for key, value in loops.items():
        assert isinstance(value, bool), (
            f"learning_loops[{key!r}]={value!r} não é bool. "
            f"Schema canonical requer bool para todos os toggles."
        )


# ── Contract 2: helper fail-soft devolve canonical defaults ─────────────────


@pytest.mark.asyncio
async def test_load_learning_loops_toggles_missing_policy_returns_canonical_defaults(
    _restore_hiring_policy_repo,
):
    """Helper fail-soft: company sem policy → returns canonical defaults
    (não raise, não dict vazio). Garante que callers podem chamar
    toggles.get('key') sem proteção adicional.
    """
    from app.shared.services.learning_loops_toggles import (
        load_learning_loops_toggles,
    )
    from app.models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS

    # Repo retorna None (sem policy salva) → helper devolve defaults canonical
    repo = MagicMock()
    repo.get_by_company = AsyncMock(return_value=None)
    _restore_hiring_policy_repo.HiringPolicyRepository = MagicMock(return_value=repo)

    out = await load_learning_loops_toggles("co-1", MagicMock())
    assert out == AUTOMATION_RULES_DEFAULTS["learning_loops"], (
        "Helper canonical deve devolver AUTOMATION_RULES_DEFAULTS['learning_loops'] "
        "quando company não tem policy salva (fail-soft canonical)."
    )
    # Sanity: F2.1 fix means bigfive_department_history is False here
    assert out["bigfive_department_history"] is False


# ── Contract 3: jd_similar_service consome via canonical helper (F2.2) ──────


def test_jd_similar_service_uses_canonical_helper():
    """F2.2 fix: record_jd_if_enabled DEVE usar load_learning_loops_toggles
    (não query inline). Helper foi criado 2026-05-21 como single source
    of truth; jd_similar_service migrou 2026-05-24.

    Source-level pin: se alguém reintroduz lookup inline (~30 linhas que
    foram removidas), este sentinel falha.
    """
    from app.domains.job_creation.services import jd_similar_service

    src = inspect.getsource(jd_similar_service.JdSimilarService.record_jd_if_enabled)
    assert "load_learning_loops_toggles" in src, (
        "JdSimilarService.record_jd_if_enabled não usa mais o helper canonical. "
        "Reintroduzir query inline de CompanyHiringPolicy é exatamente a "
        "duplicação que F2.2 fix 2026-05-24 removeu. Re-migrar ao helper em "
        "app/shared/services/learning_loops_toggles.py."
    )


def test_bigfive_service_consumers_dont_use_literal_defaults():
    """F2.1 production-quality DRY: consumers do helper NÃO devem usar
    defaults literais em toggles.get(key, literal). Helper já garante
    presença de TODAS as chaves canonical com tipo bool.

    Padrão proibido: `toggles.get("bigfive_department_history", False)`
    Padrão canonical: `toggles.get("bigfive_department_history")`

    Sem essa regra, default literal pode divergir de AUTOMATION_RULES_DEFAULTS
    (foi exatamente o que causou F2.1: 4 fontes paralelas com defaults
    diferentes).
    """
    import app.domains.job_creation.services.bigfive_service as bigfive_mod

    src = inspect.getsource(bigfive_mod)
    # Pattern: toggles.get("learning_loops_key", <bool literal>)
    canonical_keys = (
        "enabled",
        "bigfive_company_culture",
        "bigfive_department_history",
        "wsi_question_effectiveness",
        "jd_similar_suggestion",
    )
    bad_patterns = []
    for key in canonical_keys:
        pat = re.compile(
            rf'toggles\.get\(\s*["\']{re.escape(key)}["\']\s*,\s*(True|False)\s*\)'
        )
        for m in pat.finditer(src):
            bad_patterns.append((key, m.group(0)))

    assert not bad_patterns, (
        "F2.1 DRY violation: bigfive_service tem default literal em toggles.get(): "
        f"{bad_patterns}. Helper canonical já garante presença das 5 chaves; "
        "use toggles.get('key') sem default literal. Sensor: "
        "scripts/check_learning_loops_canonical_helper.py."
    )
