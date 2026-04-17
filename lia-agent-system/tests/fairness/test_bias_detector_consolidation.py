"""
Regression test for task #321: ensure FairnessGuard.detect_interview_indicators
covers every keyword captured by the 3 ex-bias-detectors that have been
consolidated into it.

If any string below stops being detected, the consolidation has regressed
and the legacy detectors would have caught a case the unified guard misses.
"""
from __future__ import annotations

from app.shared.compliance.fairness_guard import (
    FairnessGuard,
    INCLUSIVE_LANGUAGE_REPLACEMENTS_EN,
    INCLUSIVE_LANGUAGE_REPLACEMENTS_PT,
)


# Corpus de strings que cada um dos 3 detectors antigos pegava.
# (bias_type_esperado, frase)
LEGACY_BIAS_DETECTOR_CORPUS: list[tuple[str, str]] = [
    # bias_detector_service.BIAS_PATTERNS
    ("age_bias", "ele tem idade demais para o cargo"),
    ("age_bias", "candidato muito velho para a equipe"),
    ("age_bias", "preciso de alguém jovem"),
    ("age_bias", "novo demais, sem maturidade"),
    ("age_bias", "experiência demais para essa função"),
    ("age_bias", "praticamente aposentada"),
    ("appearance_bias", "achei a candidata bonita"),
    ("appearance_bias", "achei o candidato atraente"),
    ("appearance_bias", "boa aparência é importante"),
    ("appearance_bias", "ele é meio feio"),
    ("appearance_bias", "muito magra para o cargo"),
    ("appearance_bias", "ele é apresentável"),
    ("family_status_bias", "ela é casada"),
    ("family_status_bias", "candidata solteira"),
    ("family_status_bias", "tem filhos pequenos"),
    ("family_status_bias", "está grávida"),
    ("family_status_bias", "gestante no momento"),
    ("family_status_bias", "planejando maternidade"),
    ("family_status_bias", "vai tirar paternidade"),
    ("socioeconomic_bias", "ela tem sotaque do nordeste"),
    ("socioeconomic_bias", "vive na periferia"),
    ("socioeconomic_bias", "mora em uma favela"),
    ("socioeconomic_bias", "vem de bairro nobre"),
    ("socioeconomic_bias", "outra classe social"),
    ("disability_bias", "candidato deficiente físico"),
    ("disability_bias", "tem deficiência visual"),
    ("disability_bias", "candidato cadeirante"),
    ("disability_bias", "é cego"),
    ("disability_bias", "marcado como pcd"),
    ("racial_bias", "questão de raça"),
    ("racial_bias", "ele é negro"),
    ("racial_bias", "candidato branco"),
    ("racial_bias", "candidato pardo"),
    ("racial_bias", "indígena com formação"),
    ("racial_bias", "asiático no time"),
    ("racial_bias", "candidato preto"),
    ("religious_bias", "questão de religião"),
    ("religious_bias", "muito religioso"),
    ("religious_bias", "vai à igreja toda semana"),
    ("religious_bias", "acredita em deus"),
    ("religious_bias", "candidato ateu"),
    ("religious_bias", "evangélica praticante"),
    ("religious_bias", "católico devoto"),
    ("sexual_orientation_bias", "tema de orientação sexual"),
    ("sexual_orientation_bias", "ele é gay"),
    ("sexual_orientation_bias", "candidata lésbica"),
    ("sexual_orientation_bias", "pessoa trans"),
    ("sexual_orientation_bias", "totalmente heterossexual"),
    ("sexual_orientation_bias", "candidato homossexual"),
    ("sexual_orientation_bias", "do movimento lgbtq"),
    ("affinity_bias", "ele parece comigo"),
    ("affinity_bias", "fizemos a mesma faculdade"),
    ("affinity_bias", "somos da mesma cidade"),
    ("affinity_bias", "é meu conterrâneo"),
    ("affinity_bias", "fui colega de trabalho dele"),
    ("cultural_proxy_bias", "tem cultural fit com o time"),
    ("cultural_proxy_bias", "achamos que não combina"),
    ("cultural_proxy_bias", "não é a cara da empresa"),
    ("cultural_proxy_bias", "fora do nosso perfil"),
    ("cultural_proxy_bias", "não tem a cara da empresa"),
    # interview_intelligence_tools.BIAS_INDICATORS extras already covered above.
]


def test_fairness_guard_covers_legacy_bias_detector_patterns():
    fg = FairnessGuard()
    misses: list[tuple[str, str, list[str]]] = []
    for expected_type, phrase in LEGACY_BIAS_DETECTOR_CORPUS:
        alerts = fg.detect_interview_indicators(phrase)
        types = [a["type"] for a in alerts]
        if expected_type not in types:
            misses.append((expected_type, phrase, types))
    assert not misses, (
        "FairnessGuard.detect_interview_indicators perdeu cobertura em relação "
        f"aos detectors legados: {misses}"
    )


def test_apply_inclusive_language_covers_jd_enrichment_replacements():
    """Every PT/EN replacement key must round-trip through the canonical helper."""
    fg = FairnessGuard()
    for term in list(INCLUSIVE_LANGUAGE_REPLACEMENTS_PT.keys()) + list(
        INCLUSIVE_LANGUAGE_REPLACEMENTS_EN.keys()
    ):
        text = f"prefixo {term} sufixo"
        corrected, corrections = fg.apply_inclusive_language(text)
        assert corrections, f"FairnessGuard não detectou '{term}'"
        assert term.lower() not in corrected.lower(), (
            f"Termo '{term}' persiste em '{corrected}' após apply_inclusive_language"
        )


def test_jd_enrichment_check_fairness_delegates_to_fairness_guard():
    from app.domains.job_creation.services.jd_enrichment import check_fairness

    text = "Procuramos jovem e dinâmico com boa aparência"
    corrected, corrections = check_fairness(text)
    # Replacements applied
    assert "jovem e dinâmico" not in corrected.lower()
    assert "boa aparência" not in corrected.lower()
    assert any("jovem e dinâmico" in c for c in corrections)


