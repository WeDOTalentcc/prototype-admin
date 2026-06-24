"""Testes W2-B v2: add_bank_question tool no wizard.
Corrige mock — run_coro_in_threadpool é importado localmente no handler, então
mockamos em app.domains.job_creation.helpers.async_audit."""

import sys, os, uuid, unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

sys.path.insert(0, "/home/runner/workspace/lia-agent-system")

from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_add_bank_question

COMPANY_ID = "c0000000-0000-0000-0000-000000000001"
Q_ID = str(uuid.uuid4())


def _make_bank_question(question_id=None, company_id=COMPANY_ID, question_text="Você tem CNH categoria B?",
                         category="behavioral", is_eliminatory=False, expected_answer=None):
    qid = uuid.UUID(question_id) if question_id else uuid.UUID(Q_ID)
    return SimpleNamespace(
        id=qid,
        company_id=company_id,
        question_text=question_text,
        question_type="yes_no",
        options=None,
        is_required=True,
        is_eliminatory=is_eliminatory,
        expected_answer=expected_answer,
        category=category,
        order=1,
        is_active=True,
    )


def _make_state(questions=None, screening_mode="full", company_id=COMPANY_ID):
    return {
        "company_id": company_id,
        "screening_mode": screening_mode,
        "wsi_questions": questions or [],
        "questions_approved": None,
    }


def _make_ctx(company_id=COMPANY_ID):
    return SimpleNamespace(company_id=company_id)


def _run(state, tool_input, ctx=None, mock_question=None, not_found=False):
    """Executa _handle_add_bank_question com mock do repositório via run_coro_in_threadpool."""
    if ctx is None:
        ctx = _make_ctx()
    with patch(
        "app.domains.job_creation.helpers.async_audit.run_coro_in_threadpool",
        return_value=None if not_found else mock_question,
    ):
        return _handle_add_bank_question(state, tool_input, ctx)


class TestAddBankQuestionW2B(unittest.TestCase):

    def test_happy_path_adds_question_to_state(self):
        q = _make_bank_question()
        state = _make_state()
        result = _run(state, {"question_id": Q_ID}, mock_question=q)
        self.assertFalse(result.error, f"Expected no error but got: {result.llm_message}")
        new_questions = result.state_updates.get("wsi_questions", [])
        self.assertEqual(len(new_questions), 1)
        added = new_questions[0]
        self.assertEqual(added["question"], "Você tem CNH categoria B?")
        self.assertEqual(added["source"], "company_bank")
        self.assertEqual(added["bank_question_id"], Q_ID)

    def test_source_company_bank_tag(self):
        q = _make_bank_question()
        state = _make_state()
        result = _run(state, {"question_id": Q_ID}, mock_question=q)
        self.assertEqual(result.state_updates["wsi_questions"][0]["source"], "company_bank")

    def test_question_not_found_returns_error(self):
        state = _make_state()
        result = _run(state, {"question_id": Q_ID}, not_found=True)
        self.assertTrue(result.error)
        self.assertIn("não encontrada", result.llm_message)

    def test_invalid_uuid_returns_error(self):
        state = _make_state()
        result = _handle_add_bank_question(state, {"question_id": "not-a-uuid"}, _make_ctx())
        self.assertTrue(result.error)
        self.assertIn("inválido", result.llm_message)

    def test_missing_question_id_returns_error(self):
        state = _make_state()
        result = _handle_add_bank_question(state, {}, _make_ctx())
        self.assertTrue(result.error)
        self.assertIn("obrigatório", result.llm_message)

    def test_max_limit_full_mode(self):
        questions = [{"question": f"q{i}", "block": "technical", "approved": False} for i in range(12)]
        state = _make_state(questions=questions, screening_mode="full")
        result = _run(state, {"question_id": Q_ID}, mock_question=_make_bank_question())
        self.assertTrue(result.error)
        self.assertIn("limite", result.llm_message.lower())

    def test_max_limit_compact_mode(self):
        questions = [{"question": f"q{i}", "block": "behavioral", "approved": False} for i in range(7)]
        state = _make_state(questions=questions, screening_mode="compact")
        result = _run(state, {"question_id": Q_ID}, mock_question=_make_bank_question())
        self.assertTrue(result.error)
        self.assertIn("limite", result.llm_message.lower())

    def test_under_limit_succeeds(self):
        # 6/7 compact — should succeed
        questions = [{"question": f"q{i}", "block": "behavioral", "approved": False} for i in range(6)]
        state = _make_state(questions=questions, screening_mode="compact")
        q = _make_bank_question()
        result = _run(state, {"question_id": Q_ID}, mock_question=q)
        self.assertFalse(result.error)
        self.assertEqual(len(result.state_updates["wsi_questions"]), 7)

    def test_eliminatory_flag_preserved(self):
        q = _make_bank_question(is_eliminatory=True)
        state = _make_state()
        result = _run(state, {"question_id": Q_ID}, mock_question=q)
        self.assertTrue(result.state_updates["wsi_questions"][0]["is_eliminatory"])

    def test_questions_approved_reset_to_none(self):
        q = _make_bank_question()
        state = _make_state()
        state["questions_approved"] = True
        result = _run(state, {"question_id": Q_ID}, mock_question=q)
        self.assertIsNone(result.state_updates.get("questions_approved"))

    def test_company_id_required(self):
        state = {"company_id": "", "screening_mode": "full", "wsi_questions": []}
        ctx = _make_ctx(company_id="")
        result = _handle_add_bank_question(state, {"question_id": Q_ID}, ctx)
        self.assertTrue(result.error)
        self.assertIn("empresa", result.llm_message)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.TestLoader().loadTestsFromTestCase(TestAddBankQuestionW2B))
    sys.exit(0 if result.wasSuccessful() else 1)
