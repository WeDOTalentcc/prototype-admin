"""Testa que o scoring da triagem aplica os pesos de senioridade corretos."""
import pytest
import statistics

MOCK_TECH_SCORES = [8.0, 7.5, 8.5, 7.0, 7.8, 9.0, 8.2]
MOCK_BEHAV_SCORES = [8.0, 7.5, 8.5, 7.0, 9.0]


def _expected(tech, behav, tw, bw):
    return round(statistics.mean(tech) * tw + statistics.mean(behav) * bw, 2)


@pytest.mark.parametrize("seniority,tech_w,behav_w", [
    ("diretor",    0.3125,  0.6875),
    ("executive",  0.625,   0.375 ),
    ("pleno",      0.6875,  0.3125),
    ("senior",     0.5625,  0.4375),
    ("lead",       0.4375,  0.5625),
    ("junior",     0.625,   0.375),
    ("estagiario", 0.6875,  0.3125),
])
def test_final_score_uses_seniority_weights(seniority, tech_w, behav_w):
    from app.domains.recruitment.services.triagem_session_service.scoring import (
        calculate_session_final_score,
    )
    result = calculate_session_final_score(
        technical_scores=MOCK_TECH_SCORES,
        behavioral_scores=MOCK_BEHAV_SCORES,
        seniority=seniority,
    )
    expected = _expected(MOCK_TECH_SCORES, MOCK_BEHAV_SCORES, tech_w, behav_w)
    fs = result["final_score"]
    assert abs(fs - expected) < 0.1, (
        f"seniority={seniority!r}: score={fs}, esperado aprox {expected}"
    )


def test_pleno_and_director_differ():
    # Usar scores tecnicos muito maiores que comportamentais para garantir diferenca visivel
    # Com tech=9.0, behav=5.0:
    #   pleno (tech 0.6875, behav 0.3125) -> 9.0*0.6875 + 5.0*0.3125 = 6.1875 + 1.5625 = 7.75
    #   diretor (tech 0.3125, behav 0.6875) -> 9.0*0.3125 + 5.0*0.6875 = 2.8125 + 3.4375 = 6.25
    from app.domains.recruitment.services.triagem_session_service.scoring import (
        calculate_session_final_score,
    )
    high_tech = [9.0, 9.0, 9.0]
    low_behav = [5.0, 5.0, 5.0]
    r_pleno = calculate_session_final_score(high_tech, low_behav, seniority="pleno")
    r_dir   = calculate_session_final_score(high_tech, low_behav, seniority="diretor")
    # pleno pesa mais tecnico -> score maior quando tech > behav
    assert r_pleno["final_score"] > r_dir["final_score"], (
        f"pleno={r_pleno['final_score']}, diretor={r_dir['final_score']}"
    )
