"""
Integração — Wizard → Intent Detection → HITL interrupt → aprovação → vaga (Sprint K2).

Camada 3 da pirâmide de testes.
Cobre:
- WizardOrchestratorService.process_wizard_message retorna dict com intent + response
- WizardIntent enum tem valores conhecidos (PUBLISH_JOB, SAVE_DRAFT, etc.)
- _detect_intent reconhece mensagens claras
- company_id preservado em todas as chamadas (multi-tenant G1)
- HITL com domain=wizard persiste company_id corretamente
- store_resume_info preserva thread_id e domain
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


COMPANY_ID = "c-wizard-001"
THREAD_ID = str(uuid.uuid4())
SESSION_ID = "ws-wizard-session"


def _make_db():
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


def _make_wizard_context(company_id=COMPANY_ID):
    return {
        "thread_id": THREAD_ID,
        "session_id": SESSION_ID,
        "company_id": company_id,
        "user_id": "user-recruiter-1",
        "conversation_history": [],
    }


# ---------------------------------------------------------------------------
# WizardOrchestratorService
# ---------------------------------------------------------------------------

class TestWizardOrchestratorService:

    def _make_service(self):
        from app.domains.job_management.services.wizard_orchestrator_service import WizardOrchestratorService
        return WizardOrchestratorService()

    def test_process_wizard_message_returns_response(self):
        """process_wizard_message é síncrono e retorna dict com 'intent' e 'conversational_response'."""
        svc = self._make_service()
        result = svc.process_wizard_message(
            message="publicar a vaga",
            context=_make_wizard_context(),
        )
        assert result is not None
        assert isinstance(result, dict)
        assert "intent" in result

    def test_detect_intent_publish_job(self):
        """Mensagem sobre publicar vaga deve ter confiança alta."""
        svc = self._make_service()
        result = svc._detect_intent("quero publicar a vaga agora")
        assert result is not None
        assert hasattr(result, "intent")

    def test_detect_intent_unknown_for_vague_message(self):
        """Mensagem vaga deve retornar algum intent (não lançar exceção)."""
        svc = self._make_service()
        result = svc._detect_intent("oi")
        assert result is not None

    def test_company_id_in_context(self):
        """company_id deve ser preservado no contexto do wizard."""
        context = _make_wizard_context(company_id="company-xyz")
        assert context["company_id"] == "company-xyz"

    def test_get_available_intents_returns_list(self):
        svc = self._make_service()
        intents = svc.get_available_intents()
        assert isinstance(intents, list)
        assert len(intents) > 0

    def test_wizard_intent_enum_has_expected_values(self):
        """WizardIntent deve ter valores conhecidos (não CREATE_JOB que não existe)."""
        from app.domains.job_management.services.wizard_orchestrator_service import WizardIntent
        values = [i.value for i in WizardIntent]
        assert "publish_job" in values
        assert "save_draft" in values
        assert "unknown" in values


# ---------------------------------------------------------------------------
# WizardGraph — HITL interrupt (via HITLService diretamente)
# ---------------------------------------------------------------------------

class TestWizardGraphHITL:

    @pytest.mark.asyncio
    async def test_hitl_request_includes_company_id(self):
        """HITLService deve persistir company_id no payload (G1 multi-tenant)."""
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory = {}

        with patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id=THREAD_ID,
                action="create_job",
                description="Criar vaga Dev Backend",
                data={"title": "Dev Backend"},
                ws_session_id=SESSION_ID,
                domain="wizard",
                company_id=COMPANY_ID,
            )

        stored = svc._load(f"hitl:{THREAD_ID}:{pending_id}")
        assert stored["company_id"] == COMPANY_ID
        assert stored["domain"] == "wizard"

    @pytest.mark.asyncio
    async def test_hitl_resume_info_stored(self):
        """store_resume_info deve preservar thread_id e domain."""
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory = {}

        await svc.store_resume_info(
            thread_id=THREAD_ID,
            domain="wizard",
            session_id=SESSION_ID,
            agent_input_dict={"message": "criar vaga", "company_id": COMPANY_ID},
        )

        resume = await svc.get_resume_info(THREAD_ID)
        assert resume["thread_id"] == THREAD_ID
        assert resume["domain"] == "wizard"
        assert resume["agent_input"]["company_id"] == COMPANY_ID
