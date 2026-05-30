"""
Unit tests — HITL Persistence (Sprint F1).

Cobre:
- HITLService.request_approval() — Redis + DB best-effort
- HITLService.receive_approval() — atualiza Redis + insere audit trail
- HITLService.get_pending() — Redis first, DB fallback
- HITLService.is_approved() — consulta por pending_id
- Modelos HITLPendingAction + HITLAuditTrail — to_dict(), campos obrigatórios
- Migration 032 — estrutura SQL correta
- DB fallback quando Redis indisponível
"""
import pytest

pytestmark = pytest.mark.hard

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# HITLService — request_approval com DB best-effort
# ---------------------------------------------------------------------------

class TestHITLServiceRequestApproval:

    @pytest.mark.asyncio
    async def test_request_approval_returns_pending_id(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        with patch("app.domains.cv_screening.services.hitl_service._db_save_pending", new_callable=AsyncMock), \
             patch("app.api.v1.ws_manager.ws_manager") as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            pending_id = await svc.request_approval(
                thread_id="t-001",
                action="create_job",
                description="Confirmar criação da vaga",
                data={"job_title": "Engenheiro"},
                ws_session_id="s-001",
                domain="wizard",
            )
        assert isinstance(pending_id, str)
        assert len(pending_id) == 36  # UUID

    @pytest.mark.asyncio
    async def test_request_approval_calls_db_save(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        with patch("app.domains.cv_screening.services.hitl_service._db_save_pending", new_callable=AsyncMock) as mock_db, \
             patch("app.api.v1.ws_manager.ws_manager") as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            await svc.request_approval(
                thread_id="t-002",
                action="move_candidate",
                description="Mover candidato",
                data={},
                ws_session_id="s-002",
                domain="pipeline_transition",
                company_id="acme",
            )
        mock_db.assert_called_once()
        call_kwargs = mock_db.call_args[1]
        assert call_kwargs["thread_id"] == "t-002"
        assert call_kwargs["domain"] == "pipeline_transition"
        assert call_kwargs["company_id"] == "acme"

    @pytest.mark.asyncio
    async def test_request_approval_stores_in_memory_when_redis_unavailable(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_save_pending", new_callable=AsyncMock), \
             patch("app.api.v1.ws_manager.ws_manager") as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            pending_id = await svc.request_approval(
                thread_id="t-003",
                action="finalize_wsi",
                description="Finalizar WSI",
                data={},
                ws_session_id="s-003",
            )
        key = f"hitl:t-003:{pending_id}"
        assert key in svc._memory
        assert svc._memory[key]["pending_id"] == pending_id

    @pytest.mark.asyncio
    async def test_request_approval_db_failure_does_not_raise(self):
        """DB falha silenciosamente — não bloqueia o fluxo do agente."""
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        with patch("app.domains.cv_screening.services.hitl_service._db_save_pending", side_effect=Exception("DB down")), \
             patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.api.v1.ws_manager.ws_manager") as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            # Não deve levantar exceção mesmo com DB falhando
            pending_id = await svc.request_approval(
                thread_id="t-fail",
                action="test",
                description="",
                data={},
                ws_session_id="s-fail",
            )
        assert pending_id  # ainda retorna um pending_id válido

    @pytest.mark.asyncio
    async def test_request_approval_ws_failure_does_not_raise(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        with patch("app.domains.cv_screening.services.hitl_service._db_save_pending", new_callable=AsyncMock), \
             patch("app.api.v1.ws_manager.ws_manager") as mock_ws:
            mock_ws.send_to_session = AsyncMock(side_effect=Exception("WS down"))
            pending_id = await svc.request_approval(
                thread_id="t-ws-fail",
                action="test",
                description="",
                data={},
                ws_session_id="s-ws-fail",
            )
        assert pending_id


# ---------------------------------------------------------------------------
# HITLService — receive_approval com DB audit trail
# ---------------------------------------------------------------------------

class TestHITLServiceReceiveApproval:

    @pytest.mark.asyncio
    async def test_receive_approval_updates_approved_flag(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_resolve", new_callable=AsyncMock):
            svc._memory["hitl:t-r1:p-001"] = {
                "pending_id": "p-001",
                "thread_id": "t-r1",
                "domain": "wizard",
                "action": "create_job",
            }
            result = await svc.receive_approval(
                thread_id="t-r1",
                pending_id="p-001",
                approved=True,
                comment="OK",
            )
        assert result["approved"] is True
        assert result["comment"] == "OK"
        assert "resolved_at" in result

    @pytest.mark.asyncio
    async def test_receive_approval_calls_db_resolve(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_resolve", new_callable=AsyncMock) as mock_resolve:
            await svc.receive_approval(
                thread_id="t-r2",
                pending_id="p-002",
                approved=False,
                comment="Rejeitado",
                resolved_by="manager@acme.com",
                company_id="acme",
            )
        mock_resolve.assert_called_once()
        kwargs = mock_resolve.call_args[1]
        assert kwargs["approved"] is False
        assert kwargs["resolved_by"] == "manager@acme.com"
        assert kwargs["company_id"] == "acme"

    @pytest.mark.asyncio
    async def test_receive_approval_creates_record_if_missing(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_resolve", new_callable=AsyncMock):
            result = await svc.receive_approval(
                thread_id="t-new",
                pending_id="p-new",
                approved=True,
            )
        assert result["thread_id"] == "t-new"
        assert result["approved"] is True

    @pytest.mark.asyncio
    async def test_receive_approval_db_failure_does_not_raise(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_resolve", side_effect=Exception("DB down")):
            result = await svc.receive_approval(
                thread_id="t-dbfail",
                pending_id="p-dbfail",
                approved=True,
            )
        assert result["approved"] is True  # resultado ainda correto


# ---------------------------------------------------------------------------
# HITLService — get_pending com DB fallback
# ---------------------------------------------------------------------------

class TestHITLServiceGetPending:

    @pytest.mark.asyncio
    async def test_get_pending_returns_from_memory(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory["hitl:t-gp1:p-A"] = {
            "pending_id": "p-A",
            "thread_id": "t-gp1",
            "approved": None,
            "requested_at": "2026-03-08T10:00:00+00:00",
        }
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_get_pending", new_callable=AsyncMock) as mock_db:
            result = await svc.get_pending("t-gp1")
        assert result is not None
        assert result["pending_id"] == "p-A"
        mock_db.assert_not_called()  # Redis/memory hit — DB não consultado

    @pytest.mark.asyncio
    async def test_get_pending_falls_back_to_db(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        # Sem nada em Redis/memory
        db_result = {"pending_id": "p-db", "thread_id": "t-gp2", "approved": None}
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_get_pending", new_callable=AsyncMock, return_value=db_result):
            result = await svc.get_pending("t-gp2")
        assert result["pending_id"] == "p-db"

    @pytest.mark.asyncio
    async def test_get_pending_returns_none_when_resolved(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory["hitl:t-gp3:p-B"] = {
            "pending_id": "p-B",
            "thread_id": "t-gp3",
            "approved": True,  # já resolvido
        }
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_get_pending", new_callable=AsyncMock, return_value=None):
            result = await svc.get_pending("t-gp3")
        assert result is None


# ---------------------------------------------------------------------------
# Modelos HITLPendingAction + HITLAuditTrail
# ---------------------------------------------------------------------------

class TestHITLModels:

    def test_hitl_pending_action_importable(self):
        from app.models.hitl import HITLPendingAction
        assert HITLPendingAction.__tablename__ == "hitl_pending_actions"

    def test_hitl_audit_trail_importable(self):
        from app.models.hitl import HITLAuditTrail
        assert HITLAuditTrail.__tablename__ == "hitl_audit_trail"

    def test_hitl_pending_action_to_dict(self):
        from app.models.hitl import HITLPendingAction
        import uuid
        now = datetime.now(timezone.utc)
        record = HITLPendingAction(
            pending_id="p-test",
            thread_id="t-test",
            company_id="acme",
            domain="wizard",
            action="create_job",
            description="Confirmar vaga",
            data={"job_title": "Dev"},
            agent_input={"message": "confirmar"},
            ws_session_id="s-test",
            status="pending",
            expires_at=now + timedelta(hours=24),
            created_at=now,
        )
        d = record.to_dict()
        assert d["pending_id"] == "p-test"
        assert d["domain"] == "wizard"
        assert d["action"] == "create_job"
        assert d["status"] == "pending"
        assert d["approved"] is None

    def test_hitl_audit_trail_to_dict(self):
        from app.models.hitl import HITLAuditTrail
        now = datetime.now(timezone.utc)
        trail = HITLAuditTrail(
            company_id="acme",
            thread_id="t-audit",
            pending_id="p-audit",
            domain="pipeline_transition",
            action="move_candidate",
            approved=True,
            comment="Aprovado",
            resolved_by="manager@acme.com",
            resolved_at=now,
        )
        d = trail.to_dict()
        assert d["approved"] is True
        assert d["domain"] == "pipeline_transition"
        assert d["resolved_by"] == "manager@acme.com"

    def test_hitl_pending_action_has_required_columns(self):
        from app.models.hitl import HITLPendingAction
        cols = {c.name for c in HITLPendingAction.__table__.columns}
        required = {"id", "thread_id", "pending_id", "domain", "action",
                    "status", "created_at", "expires_at"}
        assert required <= cols

    def test_hitl_audit_trail_has_required_columns(self):
        from app.models.hitl import HITLAuditTrail
        cols = {c.name for c in HITLAuditTrail.__table__.columns}
        required = {"id", "thread_id", "pending_id", "domain", "action",
                    "approved", "resolved_at"}
        assert required <= cols


# ---------------------------------------------------------------------------
# Migration 032 — estrutura SQL
# ---------------------------------------------------------------------------

class TestHITLMigration032:

    def test_migration_file_exists(self):
        import pathlib
        p = pathlib.Path("alembic/versions/032_add_hitl_tables.py")
        assert p.exists()

    def test_migration_revision_correct(self):
        import pathlib
        content = pathlib.Path("alembic/versions/032_add_hitl_tables.py").read_text()
        assert 'revision = "032_add_hitl_tables"' in content

    def test_migration_down_revision_correct(self):
        import pathlib
        content = pathlib.Path("alembic/versions/032_add_hitl_tables.py").read_text()
        assert 'down_revision = "031_add_pending_actions_table"' in content

    def test_migration_creates_hitl_pending_actions(self):
        import pathlib
        content = pathlib.Path("alembic/versions/032_add_hitl_tables.py").read_text()
        assert "hitl_pending_actions" in content

    def test_migration_creates_hitl_audit_trail(self):
        import pathlib
        content = pathlib.Path("alembic/versions/032_add_hitl_tables.py").read_text()
        assert "hitl_audit_trail" in content

    def test_migration_031_fixes_orphan(self):
        """031 deve seguir 030, não 026 (branch orfã resolvida)."""
        import pathlib
        content = pathlib.Path("alembic/versions/031_add_pending_actions_table.py").read_text()
        assert 'down_revision = "030_add_prompt_version"' in content

    def test_migration_chain_complete(self):
        """Verificar que a cadeia 030 → 031 → 032 está correta."""
        import pathlib
        m031 = pathlib.Path("alembic/versions/031_add_pending_actions_table.py").read_text()
        m032 = pathlib.Path("alembic/versions/032_add_hitl_tables.py").read_text()
        assert "030_add_prompt_version" in m031
        assert "031_add_pending_actions_table" in m032
