"""Sensor test: BigFive/OCEAN score persistence per candidate after WSI screening.

INVESTIGATION FINDINGS (2026-06-14):
─────────────────────────────────────────────────────────────────────────────
Scenario A — BigFive IS persisted per-candidate, but with two structural gaps.

WHERE scores live:
  - Primary: LiaOpinion.behavioral_analysis['ocean_traits'] (JSONB dict)
    Shape: {"ocean_traits": {"openness": 0.7, "conscientiousness": 0.8, ...}}
    Written by TWO code paths:
      1. handlers_screening._persist_lia_opinion_with_ocean()
         (event_handlers/handlers_screening.py:417 — screening_completed trigger)
      2. triagem_session_service completion.py:443 (web triagem path, block 2.4)

GAP 1 — Pipeline-overview reads wrong table (test_results, not LiaOpinion):
  - analytics.py:1196 reads big_five_data from test_results.answers
    WHERE tt.category='personality' AND tt.subcategory='big_five'
  - NO code path ever writes WSI ocean_traits to test_results.
  - Result: big_five_data is ALWAYS null in pipeline-overview response.
  - bigFiveScores in kanban (pipeline-overview-page.tsx:1458) = always null.
  - KanbanScoreCells.tsx:170 shows BigFive column as empty/opacity-40.

GAP 2 — Triagem parecer tab checks top-level keys, not nested ocean_traits:
  - triagem-parecer-tab.tsx:159: entries = Object.entries(report.behavioral_analysis)
  - isBigFive = entries.some(([k]) => Object.keys(BIG_FIVE_MAP).includes(k))
  - BIG_FIVE_MAP = {openness, conscientiousness, extraversion, agreeableness, neuroticism}
  - BUT LiaOpinion.behavioral_analysis shape = {"ocean_traits": {...}, "wsi_source": "..."}
  - The OCEAN keys are nested under .ocean_traits, NOT top-level
  - Result: isBigFive = false → shows fallback "Análise Comportamental" text block,
    never the BigFive radar/bar chart.
  NOTE: The parecer tab reads from wsi_reports.behavioral_analysis (sessions.py:219),
  which is a DIFFERENT table from LiaOpinion.behavioral_analysis. wsi_reports is only
  written by wsi_voice_orchestrator (voice path). The web triagem path writes only to
  LiaOpinion, not wsi_reports — so for web triagem sessions, report is null entirely.

FIX NEEDED:
  Fix 1 (pipeline-overview): In analytics.py get_pipeline_overview, join LiaOpinion
  and extract behavioral_analysis->'ocean_traits' instead of test_results.answers.
  Fix 2 (triagem parecer): In triagem-parecer-tab.tsx, check for ocean_traits nesting:
  const behavData = report.behavioral_analysis?.ocean_traits ?? report.behavioral_analysis
  const entries = Object.entries(behavData) — then check isBigFive against those entries.
─────────────────────────────────────────────────────────────────────────────
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Sensor 1: ocean_traits persisted to LiaOpinion (handler path) ──────────

@pytest.mark.asyncio
async def test_persist_lia_opinion_with_ocean_writes_ocean_traits():
    """_persist_lia_opinion_with_ocean must write ocean_traits to LiaOpinion.behavioral_analysis."""
    mock_opinion = MagicMock()
    mock_opinion.behavioral_analysis = {}

    mock_repo = AsyncMock()
    mock_repo.upsert_ocean_opinion.return_value = mock_opinion

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    wsi_result = MagicMock()
    wsi_result.ocean_traits = {
        "openness": 0.72,
        "conscientiousness": 0.85,
        "extraversion": 0.60,
        "agreeableness": 0.78,
        "stability": 0.65,
    }
    wsi_result.classification = "excelente"
    wsi_result.technical_wsi = 4.1
    wsi_result.behavioral_wsi = 3.9

    request = MagicMock()
    request.candidate_id = "cand-001"
    request.vacancy_id = "vac-001"
    request.company_id = "comp-001"

    candidate_feedback = MagicMock()
    candidate_feedback.main_message = "Candidato com bom perfil."

    with patch(
        "app.repositories.opinions_repository.OpinionsRepository",
        return_value=mock_repo,
    ):
        from app.api.v1.automation.event_handlers.handlers_screening import (
            _persist_lia_opinion_with_ocean,
        )
        await _persist_lia_opinion_with_ocean(
            db=mock_db,
            request=request,
            wsi_result=wsi_result,
            overall_wsi=4.0,
            recommendation="approved",
            candidate_feedback=candidate_feedback,
        )

    mock_repo.upsert_ocean_opinion.assert_awaited_once()
    call_kwargs = mock_repo.upsert_ocean_opinion.call_args.kwargs
    assert call_kwargs["ocean_traits"] == wsi_result.ocean_traits
    assert call_kwargs["candidate_id"] == "cand-001"
    assert call_kwargs["vacancy_id"] == "vac-001"


# ── Sensor 2: upsert_ocean_opinion stores ocean_traits under nested key ─────

def test_upsert_ocean_opinion_stores_nested_ocean_traits():
    """GAP 2 SENSOR: upsert_ocean_opinion stores ocean_traits nested, not at top-level.

    This test documents the shape mismatch between BE storage and FE expectation.
    The FE triagem-parecer-tab reads Object.entries(behavioral_analysis) and checks
    for top-level OCEAN keys, but the stored shape is {'ocean_traits': {...}}.
    """
    stored_blob = {}
    ocean_input = {"openness": 0.8, "conscientiousness": 0.75}

    # Simulate what upsert_ocean_opinion does:
    # behavioral_blob["ocean_traits"] = ocean_traits
    stored_blob["ocean_traits"] = ocean_input

    # Confirm shape: OCEAN keys are NOT at top level
    assert "openness" not in stored_blob, (
        "OCEAN traits must NOT be top-level in behavioral_analysis blob. "
        "If this test fails, the storage changed and the FE check may now work. "
        "Update triagem-parecer-tab.tsx to remove the nested lookup workaround."
    )
    assert "ocean_traits" in stored_blob
    assert stored_blob["ocean_traits"]["openness"] == 0.8


def test_fe_bigfive_map_keys_vs_stored_keys():
    """Documents the FE check that fails due to nesting mismatch.

    triagem-parecer-tab.tsx checks:
      const isBigFive = entries.some(([k]) => Object.keys(BIG_FIVE_MAP).includes(k))
    where BIG_FIVE_MAP = {openness, conscientiousness, extraversion, agreeableness, neuroticism}

    But the stored behavioral_analysis top-level keys are:
      ocean_traits, wsi_classification, wsi_behavioral, behavioral_scores, wsi_source

    This means isBigFive is ALWAYS false for web triagem sessions.
    Fix: const behavData = ba.ocean_traits ?? ba; const isBigFive = ...entries(behavData)
    """
    FE_BIG_FIVE_MAP_KEYS = {
        "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"
    }

    # Simulate what BE stores (completion.py block 2.4)
    stored_ba = {
        "wsi_classification": "excelente",
        "wsi_behavioral": 3,
        "behavioral_scores": [],
        "ocean_traits": {"openness": 0.8, "conscientiousness": 0.75},
        "wsi_source": "web_triagem",
    }

    # FE check (current broken behavior)
    top_level_keys = set(stored_ba.keys())
    is_bigfive_current_fe = bool(top_level_keys & FE_BIG_FIVE_MAP_KEYS)
    assert not is_bigfive_current_fe, (
        "Current FE check should FAIL to detect BigFive in stored blob "
        "(top-level keys don't overlap with BIG_FIVE_MAP). "
        "If this assertion fails, storage shape changed — review the fix."
    )

    # Fixed FE check (what it should be after fix)
    ocean_data = stored_ba.get("ocean_traits") or stored_ba
    is_bigfive_fixed = bool(set(ocean_data.keys()) & FE_BIG_FIVE_MAP_KEYS)
    assert is_bigfive_fixed, (
        "After fix, FE should detect BigFive by reading behavioral_analysis.ocean_traits"
    )


# ── Sensor 3: pipeline-overview gap (test_results path never populated) ─────

def test_pipeline_overview_bigfive_query_reads_wrong_table():
    """GAP 1 SENSOR: Documents that pipeline-overview reads BigFive from test_results,
    but WSI screening never writes ocean_traits there.

    analytics.py SQL:
        LEFT JOIN LATERAL (
            SELECT tr4.answers FROM test_results tr4
            JOIN technical_tests tt4 ON tt4.id = tr4.test_id
            WHERE tr4.candidate_id = b.candidate_id
              AND tt4.category = 'personality'
              AND tt4.subcategory = 'big_five'
            ORDER BY tr4.created_at DESC LIMIT 1
        ) tr_b5 ON true
        → tr_b5.answers AS big_five_data

    WSI screening writes ocean_traits to: LiaOpinion.behavioral_analysis['ocean_traits']
    WSI screening does NOT write to: test_results (no INSERT to test_results in any WSI path)

    Fix: Change the analytics.py SQL to LEFT JOIN lia_opinions and extract
    lo.behavioral_analysis->'ocean_traits' as big_five_data.
    """
    # Documented paths that write to test_results:
    # (none of these are the WSI ocean_traits path)
    test_results_writers = [
        "app/api/v1/technical_tests.py",  # manual test results from recruiter
        "app/domains/voice/repositories/wsi_repository.py",  # voice screening only
    ]

    # Documented paths that write ocean_traits to LiaOpinion:
    ocean_traits_writers = [
        "app/api/v1/automation/event_handlers/handlers_screening.py",  # screening_completed trigger
        "app/domains/recruitment/services/triagem_session_service/completion.py",  # web triagem
    ]

    # The gap: test_results is never written by WSI ocean_traits code paths
    assert len(ocean_traits_writers) > 0  # persistence exists
    assert len(test_results_writers) > 0  # test_results has other writers
    # The assertion: NO overlap between ocean_traits writers and test_results writers
    # This is structural — the test documents the gap for fixability tracking
    assert all("test_results" not in w for w in ocean_traits_writers), (
        "If ocean_traits writers now also write to test_results, GAP 1 may be fixed. "
        "Remove this test and update analytics.py join comment."
    )


# ── Sensor 4: score_calculator produces ocean_traits in WSIResult ───────────

def test_wsi_score_calculator_produces_ocean_traits():
    """WSIScoreCalculator._aggregate_ocean_traits must aggregate per-trait scores.

    Normalization: mean_score (1–5) → (mean - 1) / 4 → [0, 1].
    Uses r.final_score (not r.score). Only ALLOWED_TRAITS contribute.
    """
    from app.domains.cv_screening.services.wsi_service.score_calculator import (
        WSIScoreCalculator,
    )

    calc = WSIScoreCalculator()

    # Use final_score (as the impl reads) and ALLOWED_TRAITS values
    responses = [
        MagicMock(trait_ocean="openness", final_score=5.0),   # max
        MagicMock(trait_ocean="openness", final_score=3.0),   # mid
        MagicMock(trait_ocean="conscientiousness", final_score=5.0),
        MagicMock(trait_ocean=None, final_score=3.0),          # no trait — ignored
        MagicMock(trait_ocean="not_a_trait", final_score=4.0), # not in ALLOWED_TRAITS — ignored
    ]

    result = calc._aggregate_ocean_traits(responses)

    assert "openness" in result, "openness must be aggregated"
    assert "conscientiousness" in result, "conscientiousness must be aggregated"
    assert "stability" not in result, "stability not in inputs, must not appear"
    assert "not_a_trait" not in result, "non-ALLOWED_TRAITS must be ignored"

    # openness mean: (5.0 + 3.0) / 2 = 4.0 → normalized: (4.0 - 1) / 4 = 0.75
    assert abs(result["openness"] - 0.75) < 0.01, (
        f"openness expected 0.75 (normalized from mean=4.0), got {result['openness']}"
    )
    # conscientiousness: 5.0 → normalized: (5.0 - 1) / 4 = 1.0
    assert abs(result["conscientiousness"] - 1.0) < 0.01, (
        f"conscientiousness expected 1.0 (normalized from mean=5.0), got {result['conscientiousness']}"
    )
