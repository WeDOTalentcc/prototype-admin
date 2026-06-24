"""
Fix D — session_id em FairnessAuditLog + correlation_id em FairnessPolicyViolation.

TDD Red-Green-Refactor:
1. FairnessAuditLog model tem coluna session_id
2. log_check() aceita session_id kwarg e persiste no registro
3. FairnessPolicyViolation.correlation_id é populado com session_id
4. SSE threadar session_id para log_check (Fix A enriquecido)
5. _fairness_pre_check aceita session_id e passa para log_check (Fix B enriquecido)
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _blocked():
    from app.shared.compliance.fairness_guard import FairnessCheckResult
    return FairnessCheckResult(
        is_blocked=True,
        blocked_terms=["homens"],
        category="genero",
        educational_message="Mensagem educacional.",
        original_query="somente homens",
        confidence=0.95,
    )


# ─── Fix D.1: FairnessAuditLog tem coluna session_id ─────────────────────────

class TestFairnessAuditLogModel:

    def test_modelo_tem_coluna_session_id(self):
        """FairnessAuditLog deve ter atributo session_id mapeado para coluna."""
        from lia_models.fairness_audit import FairnessAuditLog
        cols = {c.name for c in FairnessAuditLog.__table__.columns}
        assert "session_id" in cols, (
            "Fix D.1 ausente: coluna session_id não existe em fairness_audit_log. "
            "Adicionar Column(String(100), nullable=True) ao modelo e rodar migration."
        )

    def test_coluna_session_id_e_nullable(self):
        """session_id deve ser nullable (retrocompatibilidade)."""
        from lia_models.fairness_audit import FairnessAuditLog
        col = FairnessAuditLog.__table__.columns["session_id"]
        assert col.nullable is True, "session_id deve ser nullable"

    def test_coluna_session_id_tipo_string(self):
        """session_id deve ser String."""
        from sqlalchemy import String
        from lia_models.fairness_audit import FairnessAuditLog
        col = FairnessAuditLog.__table__.columns["session_id"]
        assert isinstance(col.type, String), f"Tipo esperado String, recebeu {col.type}"


# ─── Fix D.2: log_check() aceita e persiste session_id ───────────────────────

class TestLogCheckSessionId:

    def test_log_check_aceita_session_id_kwarg(self):
        """log_check deve aceitar session_id como parâmetro opcional."""
        import inspect
        from app.shared.compliance.fairness_guard import FairnessGuard
        sig = inspect.signature(FairnessGuard.log_check)
        assert "session_id" in sig.parameters, (
            "Fix D.2 ausente: log_check() não tem parâmetro session_id. "
            "Adicionar session_id: str | None = None na assinatura."
        )

    @pytest.mark.asyncio
    async def test_log_check_persiste_session_id_no_registro(self):
        """Quando session_id passado, deve ser salvo no FairnessAuditLog.
        
        Passamos db= diretamente para evitar dependência do AsyncSessionLocal.
        """
        from app.shared.compliance.fairness_guard import FairnessGuard

        added_objects = []
        mock_db = AsyncMock()
        mock_db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
        mock_db.flush = AsyncMock()

        guard = FairnessGuard()
        result = _blocked()

        await guard.log_check(
            result=result,
            db=mock_db,
            context="chat_sse",
            company_id="00000000-0000-0000-0000-000000000001",
            session_id="sess-abc-123",
        )

        from lia_models.fairness_audit import FairnessAuditLog
        audit_records = [o for o in added_objects if isinstance(o, FairnessAuditLog)]
        assert len(audit_records) == 1, (
            f"Esperava 1 FairnessAuditLog, encontrou {len(audit_records)}"
        )
        assert audit_records[0].session_id == "sess-abc-123", (
            f"Fix D.2 ausente: session_id não foi persistido no FairnessAuditLog. "
            f"Recebeu: {audit_records[0].session_id!r}"
        )

    @pytest.mark.asyncio
    async def test_log_check_sem_session_id_nao_quebra(self):
        """Backward compat: log_check sem session_id não deve levantar exceção."""
        from app.shared.compliance.fairness_guard import FairnessGuard

        added_objects = []
        mock_db = AsyncMock()
        mock_db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
        mock_db.flush = AsyncMock()

        guard = FairnessGuard()
        result = _blocked()

        # não deve levantar exceção
        await guard.log_check(
            result=result,
            db=mock_db,
            context="chat_sse",
            company_id="00000000-0000-0000-0000-000000000001",
        )

        from lia_models.fairness_audit import FairnessAuditLog
        audit_records = [o for o in added_objects if isinstance(o, FairnessAuditLog)]
        assert len(audit_records) == 1


# ─── Fix D.3: FairnessPolicyViolation.correlation_id populado ────────────────

class TestCorrelationIdPopulado:

    @pytest.mark.asyncio
    async def test_correlation_id_preenchido_com_session_id(self):
        """
        Quando log_check recebe session_id e is_blocked=True,
        FairnessPolicyViolation.correlation_id deve ser igual ao session_id.
        """
        from app.shared.compliance.fairness_guard import FairnessGuard

        added_objects = []
        mock_db = AsyncMock()
        mock_db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
        mock_db.flush = AsyncMock()

        guard = FairnessGuard()
        result = _blocked()

        await guard.log_check(
            result=result,
            db=mock_db,
            context="chat_sse",
            company_id="00000000-0000-0000-0000-000000000001",
            session_id="sess-xyz-456",
        )

        from lia_models.fairness_policies import FairnessPolicyViolation
        violations = [o for o in added_objects if isinstance(o, FairnessPolicyViolation)]
        assert len(violations) == 1, (
            f"Esperava 1 FairnessPolicyViolation, encontrou {len(violations)}"
        )
        assert violations[0].correlation_id == "sess-xyz-456", (
            f"Fix D.3 ausente: correlation_id deveria ser 'sess-xyz-456', "
            f"mas está '{violations[0].correlation_id!r}'"
        )

    @pytest.mark.asyncio
    async def test_correlation_id_none_sem_session_id(self):
        """Sem session_id, correlation_id deve permanecer None (backward compat)."""
        from app.shared.compliance.fairness_guard import FairnessGuard

        added_objects = []
        mock_db = AsyncMock()
        mock_db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
        mock_db.flush = AsyncMock()

        guard = FairnessGuard()
        result = _blocked()

        await guard.log_check(
            result=result,
            db=mock_db,
            context="chat_sse",
            company_id="00000000-0000-0000-0000-000000000001",
        )

        from lia_models.fairness_policies import FairnessPolicyViolation
        violations = [o for o in added_objects if isinstance(o, FairnessPolicyViolation)]
        assert violations[0].correlation_id is None


# ─── Fix D.4+D.5: session_id threaded no SSE e no mixin ──────────────────────

class TestSessionIdThreaded:

    def test_mixin_aceita_session_id_kwarg(self):
        """_fairness_pre_check deve aceitar session_id= kwarg."""
        import inspect
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        sig = inspect.signature(EnhancedAgentMixin._fairness_pre_check)
        assert "session_id" in sig.parameters, (
            "Fix D.5 ausente: _fairness_pre_check não tem parâmetro session_id. "
            "Adicionar session_id: Optional[str] = None na assinatura."
        )

    @pytest.mark.asyncio
    async def test_mixin_passa_session_id_ao_log_check(self):
        """Quando session_id passado ao mixin, deve chegar ao log_check."""
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        from app.shared.compliance.fairness_guard import FairnessCheckResult

        class _Agent(EnhancedAgentMixin):
            _enhanced_domain = "test"

        agent = _Agent()
        blocked = FairnessCheckResult(
            is_blocked=True, blocked_terms=[], category="genero",
            educational_message="X", original_query="y", confidence=0.9,
        )
        log_check_mock = AsyncMock()

        with patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.check",
            return_value=blocked,
        ), patch(
            "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
            log_check_mock,
        ):
            await agent._fairness_pre_check(
                "somente homens",
                company_id="co-1",
                session_id="sess-001",
            )

        await asyncio.sleep(0.05)
        log_check_mock.assert_called_once()
        kw = log_check_mock.call_args.kwargs
        assert kw.get("session_id") == "sess-001", (
            f"session_id não chegou ao log_check. kwargs recebidos: {kw}"
        )

    def test_sse_passa_session_id_no_log_check(self):
        """Verifica que agent_chat_sse.py passa session_id ao log_check (inspeção estática)."""
        with open("app/api/v1/agent_chat_sse.py") as f:
            source = f.read()
        lia_p03_idx = source.find("LIA-P03")
        block = source[lia_p03_idx : lia_p03_idx + 1000]
        assert "session_id" in block, (
            "Fix D.4 ausente: agent_chat_sse.py não passa session_id ao log_check. "
            "Adicionar session_id=session_id no create_task do LIA-P03."
        )
