"""
Round-trip oracle — Fase 7 Camada 0 (eligibility_questions).

Garante que os shapes do wizard (4 shapes históricos) sobrevivem ao normalizer
do consumidor real e chegam na triagem com is_eliminatory correto.

Seam coberto:
    state dict snapshot → EligibilityQuestionItem normalizer
    → get_eligibility_questions_from_job
    → filtro is_eliminatory (replica conversation_manager.py:1143-1155)
"""
import pytest
from app.schemas.eligibility_question_item import EligibilityQuestionItem
from app.domains.cv_screening.services.eligibility_verification_service import (
    eligibility_service,
)


# ─── snapshots realistas (incluindo sentinel keys de produção) ────────────
# Shape 1: Wizard — {question, required_answer: "yes"|"no"} + sentinels
WIZARD_SNAPSHOT = {
    "question": "Você possui CNH categoria B ou superior?",
    "required_answer": "yes",
    "_template_id": "tmpl-abc123",
    "_is_master_origin": True,
}

# Shape 2: Job-edit — {question, type, disqualify_on_fail, expected_answer, order}
JOB_EDIT_SNAPSHOT = {
    "question": "Disponibilidade para trabalho presencial em São Paulo?",
    "type": "yes_no",
    "disqualify_on_fail": True,
    "expected_answer": "Sim",
    "order": 2,
}

# Shape 3: Catálogo Settings — {eliminatory, eliminatoryAnswer} + SENTINEL KEYS
# Este é o shape crítico: _template_id e _is_master_origin devem ser descartados
# pelo model_validator(before) SEM levantar ValidationError (extra='forbid').
CATALOG_SNAPSHOT = {
    "question": "Você é PcD (Pessoa com Deficiência)?",
    "type": "yes_no",
    "category": "legal",
    "eliminatory": True,
    "eliminatoryAnswer": "Nao",
    "_template_id": "tmpl-pcd-master-001",
    "_is_master_origin": False,
}

# Shape 4: Legado — {question_text, is_eliminatory, category, expected_answer}
LEGACY_SNAPSHOT = {
    "question_text": "Inglês avançado ou fluente é requisito da vaga?",
    "is_eliminatory": True,
    "category": "legal",
    "expected_answer": "Sim",
}

# Shape não-eliminatório — deve ser FILTRADO pelo consumer
NON_ELIMINATORY_SNAPSHOT = {
    "question": "Você tem experiência com metodologias ágeis?",
    "type": "yes_no",
    "disqualify_on_fail": False,
    "eliminatory": False,
    "expected_answer": "Sim",
}


# ─── helper de consumer ────────────────────────────────────────────────────
def _run_consumer(snapshots: list[dict]) -> list[dict]:
    """Replica lógica exata de conversation_manager.py:1143-1155."""
    job_data = {"eligibility_questions": snapshots}
    out = []
    for _q in eligibility_service.get_eligibility_questions_from_job(job_data):
        if not _q.is_eliminatory:
            continue
        out.append({
            "question": _q.question_text,
            "is_eliminatory": True,
            "expected_answer": _q.expected_answer,
            "category": _q.category,
        })
    return out


# ─── Grupo 1: normalizer unit (EligibilityQuestionItem) ───────────────────

class TestEligibilityQuestionItemNormalizer:

    def test_wizard_shape_is_eliminatory_and_expected_answer(self):
        """required_answer='yes' → is_eliminatory=True (default), expected_answer='Sim'."""
        item = EligibilityQuestionItem(**WIZARD_SNAPSHOT)
        assert item.is_eliminatory is True
        assert item.expected_answer == "Sim"
        assert "CNH" in item.question

    def test_job_edit_shape_disqualify_on_fail_maps_to_is_eliminatory(self):
        """disqualify_on_fail=True → is_eliminatory=True."""
        item = EligibilityQuestionItem(**JOB_EDIT_SNAPSHOT)
        assert item.is_eliminatory is True
        assert item.expected_answer == "Sim"
        assert item.order == 2

    def test_catalog_shape_sentinel_keys_stripped_no_validation_error(self):
        """
        Catálogo com _template_id + _is_master_origin NÃO levanta ValidationError.
        model_validator(before) consome os keys legados e devolve só campos
        canônicos; extra='forbid' não vê as sentinels.
        Resultado: is_eliminatory=True, expected_answer='Nao'.
        """
        # Este é o teste que prova — não apenas traça — que extra='forbid' não barra
        # sentinels de produção. Se levantar, o commit quebra runtime.
        item = EligibilityQuestionItem(**CATALOG_SNAPSHOT)
        assert item.is_eliminatory is True
        assert item.expected_answer == "Nao"
        assert item.category == "legal"
        assert item.question == "Você é PcD (Pessoa com Deficiência)?"

    def test_legacy_shape_question_text_normalizes(self):
        """question_text (shape legado) → question, is_eliminatory=True."""
        item = EligibilityQuestionItem(**LEGACY_SNAPSHOT)
        assert item.question == "Inglês avançado ou fluente é requisito da vaga?"
        assert item.is_eliminatory is True
        assert item.expected_answer == "Sim"

    def test_non_eliminatory_shape_flag_is_false(self):
        """disqualify_on_fail=False + eliminatory=False → is_eliminatory=False."""
        item = EligibilityQuestionItem(**NON_ELIMINATORY_SNAPSHOT)
        assert item.is_eliminatory is False

    def test_wizard_sentinel_keys_stripped_no_validation_error(self):
        """_template_id + _is_master_origin no wizard snapshot também NÃO levantam."""
        item = EligibilityQuestionItem(**WIZARD_SNAPSHOT)
        assert not hasattr(item, "_template_id")
        assert not hasattr(item, "_is_master_origin")


# ─── Grupo 2: round-trip consumer (replica conversation_manager) ──────────

class TestEligibilityRoundTrip:

    def test_wizard_snapshot_reaches_triagem_pipeline(self):
        result = _run_consumer([WIZARD_SNAPSHOT])
        assert len(result) == 1
        assert "CNH" in result[0]["question"]
        assert result[0]["is_eliminatory"] is True
        assert result[0]["expected_answer"] == "Sim"

    def test_catalog_snapshot_with_sentinels_reaches_triagem(self):
        """Catalog snapshot com _template_id/_is_master_origin chega na triagem."""
        result = _run_consumer([CATALOG_SNAPSHOT])
        assert len(result) == 1
        assert "PcD" in result[0]["question"]
        assert result[0]["is_eliminatory"] is True
        assert result[0]["expected_answer"] == "Nao"

    def test_non_eliminatory_snapshot_filtered_out(self):
        """non-eliminatory é filtrado — zero chega na triagem."""
        result = _run_consumer([NON_ELIMINATORY_SNAPSHOT])
        assert result == []

    def test_mixed_only_eliminatory_pass_filter(self):
        """
        2 eliminatórias + 1 não-eliminatória → count=2.
        Se is_eliminatory cair no normalizer, count errado revela o bug.
        """
        result = _run_consumer([
            WIZARD_SNAPSHOT,
            NON_ELIMINATORY_SNAPSHOT,
            CATALOG_SNAPSHOT,
        ])
        assert len(result) == 2, (
            f"Esperava 2 eliminatórias, got {len(result)}: "
            f"{[r['question'][:40] for r in result]}"
        )

    def test_empty_eligibility_returns_empty(self):
        """state[] (FastAPI path sem fix) → triagem não recebe elegibilidade."""
        assert _run_consumer([]) == []

    def test_all_four_shapes_all_reach_triagem(self):
        """
        Oráculo máximo: todos os 4 shapes eliminatórios chegam na triagem.
        Um count < 4 revela qual shape normalizou errado.
        """
        result = _run_consumer([
            WIZARD_SNAPSHOT,
            JOB_EDIT_SNAPSHOT,
            CATALOG_SNAPSHOT,
            LEGACY_SNAPSHOT,
        ])
        assert len(result) == 4, (
            f"Esperava 4 (1/shape), got {len(result)}: "
            f"{[r['question'][:35] for r in result]}"
        )
