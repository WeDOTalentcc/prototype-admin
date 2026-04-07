"""
Tests — LGPD & Compliance Gap Closure (Task #63)

Covers:
  1. TTL cleanup: 'messages' table (primary) + interview_notes, screening_tasks, fairness_audit_log
  2. EncryptedFieldMixin: PII encryption via @validates with plaintext nulling
     - New writes: plaintext column is NULL; encrypted column + hash are populated
     - Fail-closed in production; dev-mode raw-bytes fallback
  3. Fairness Report endpoint: JSON/CSV/PDF, period params, 403 for non-admin, 503 for missing PDF lib
  4. Four-Fifths Rule computation per protected group (AIR logic)
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# 1. TTL Cleanup Tests
# ---------------------------------------------------------------------------

class TestConversationTTLCleanup:
    """Tests for TTL-based cleanup of time-bounded data tables."""

    @pytest.mark.asyncio
    async def test_run_cleanup_includes_new_ttl_keys(self):
        """run_cleanup() summary includes chat/interview/screening/AI keys."""
        from unittest.mock import patch
        from app.shared.services.lgpd_cleanup_service import run_cleanup

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.scalar = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        with patch(
            "app.shared.services.lgpd_cleanup_service.AsyncSessionLocal",
            return_value=mock_session,
        ):
            result = await run_cleanup(dry_run=True)

        assert "chat_messages_deleted" in result
        assert "interview_notes_deleted" in result
        assert "screening_logs_deleted" in result
        assert "ai_decision_logs_deleted" in result

    @pytest.mark.asyncio
    async def test_retention_days_mapping(self):
        """RETENTION_DAYS contains all required data types with correct TTLs."""
        from app.shared.services.lgpd_cleanup_service import RETENTION_DAYS

        assert RETENTION_DAYS["chat_messages"] == 90
        assert RETENTION_DAYS["interview_data"] == 180
        assert RETENTION_DAYS["screening_logs"] == 365
        assert RETENTION_DAYS["ai_decision_logs"] == 365
        assert RETENTION_DAYS["rejected"] == 90
        assert RETENTION_DAYS["withdrawn"] == 90

    @pytest.mark.asyncio
    async def test_cleanup_by_created_at_dry_run_does_not_delete(self):
        """_cleanup_by_created_at with dry_run=True must not execute DELETE."""
        from app.shared.services.lgpd_cleanup_service import _cleanup_by_created_at

        mock_db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 5
        mock_db.execute = AsyncMock(return_value=count_result)

        count = await _cleanup_by_created_at(mock_db, "interview_notes", 180, dry_run=True)

        assert count == 5
        for call in mock_db.execute.call_args_list:
            query_str = str(call)
            assert "DELETE" not in query_str.upper()

    @pytest.mark.asyncio
    async def test_cleanup_by_created_at_real_run_executes_delete(self):
        """_cleanup_by_created_at with dry_run=False must execute DELETE."""
        from app.shared.services.lgpd_cleanup_service import _cleanup_by_created_at

        mock_db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 3
        mock_db.execute = AsyncMock(return_value=count_result)
        mock_db.commit = AsyncMock()

        count = await _cleanup_by_created_at(mock_db, "chat_messages", 90, dry_run=False)

        assert count == 3
        delete_calls = [
            c for c in mock_db.execute.call_args_list
            if "DELETE" in str(c).upper()
        ]
        assert len(delete_calls) >= 1
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_conversation_ttl_cleanup_returns_per_table_summary(self):
        """run_conversation_ttl_cleanup() returns per-table breakdown."""
        from unittest.mock import patch
        from app.shared.services.lgpd_cleanup_service import run_conversation_ttl_cleanup

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        mock_session.execute = AsyncMock(return_value=count_result)
        mock_session.commit = AsyncMock()

        with patch(
            "app.shared.services.lgpd_cleanup_service.AsyncSessionLocal",
            return_value=mock_session,
        ):
            result = await run_conversation_ttl_cleanup(dry_run=True)

        assert "tables" in result
        assert "total_deleted" in result
        assert result["dry_run"] is True

    def test_ttl_config_contains_messages_table(self):
        """
        run_conversation_ttl_cleanup must include the 'messages' table.
        Message.__tablename__ = 'messages' in lia_models/conversation.py —
        this is the primary production chat message table.
        """
        import inspect
        from app.shared.services import lgpd_cleanup_service as svc
        source = inspect.getsource(svc.run_conversation_ttl_cleanup)
        assert '"messages"' in source or "'messages'" in source, (
            "run_conversation_ttl_cleanup MUST include the 'messages' table "
            "(Message.__tablename__ = 'messages' in lia_models/conversation.py)"
        )

    def test_run_cleanup_source_contains_messages_table(self):
        """run_cleanup() must also include the 'messages' table."""
        import inspect
        from app.shared.services import lgpd_cleanup_service as svc
        source = inspect.getsource(svc.run_cleanup)
        assert '"messages"' in source or "'messages'" in source, (
            "run_cleanup MUST include the 'messages' table"
        )


# ---------------------------------------------------------------------------
# 2. Encryption Tests
# ---------------------------------------------------------------------------

class TestEncryptedFieldMixin:
    """
    Tests for Fernet at-rest encryption of CPF/email fields.

    Key design: EncryptedFieldMixin uses @validates to intercept writes to
    plaintext columns. The validator:
    - Populates encrypted backing column
    - Populates hash column
    - NULLS the plaintext column (return None)
    """

    def setup_method(self):
        from cryptography.fernet import Fernet
        self._test_key = Fernet.generate_key().decode()
        os.environ["FIELD_ENCRYPTION_KEY"] = self._test_key

    def teardown_method(self):
        os.environ.pop("FIELD_ENCRYPTION_KEY", None)
        os.environ.pop("IS_DEVELOPMENT", None)

    def test_encrypt_returns_bytes(self):
        from app.shared.encryption.encrypted_field_mixin import _encrypt
        result = _encrypt("test@example.com")
        assert isinstance(result, bytes)
        assert b"test@example.com" not in result

    def test_decrypt_roundtrip(self):
        from app.shared.encryption.encrypted_field_mixin import _encrypt, _decrypt
        plaintext = "123.456.789-09"
        encrypted = _encrypt(plaintext)
        decrypted = _decrypt(encrypted)
        assert decrypted == plaintext

    def test_plaintext_does_not_persist_in_encrypted_bytes(self):
        """Encrypted bytes must not contain plaintext CPF/email."""
        from app.shared.encryption.encrypted_field_mixin import _encrypt
        cpf = "123.456.789-09"
        email = "candidate@empresa.com.br"
        assert cpf.encode() not in _encrypt(cpf)
        assert email.encode() not in _encrypt(email)

    def test_encrypt_none_returns_none(self):
        from app.shared.encryption.encrypted_field_mixin import _encrypt, _decrypt
        assert _encrypt(None) is None
        assert _decrypt(None) is None

    def test_email_hash_is_deterministic(self):
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        h1 = _sha256_hash("user@example.com")
        h2 = _sha256_hash("USER@EXAMPLE.COM")
        assert h1 == h2
        assert len(h1) == 64

    def test_email_hash_different_values(self):
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        h1 = _sha256_hash("user1@example.com")
        h2 = _sha256_hash("user2@example.com")
        assert h1 != h2

    def test_hybrid_property_write_encrypts_and_nulls_raw(self):
        """
        Setting email via hybrid_property MUST:
        1. Set _email_encrypted with Fernet bytes (not containing plaintext)
        2. Set email_hash with SHA-256 hex
        3. Set _email_raw = None (DB column NULL — PII not persisted in plaintext)
        4. Reading obj.email returns decrypted string (transparent access)
        """
        from sqlalchemy import Column, LargeBinary, String, Integer
        from sqlalchemy.orm import DeclarativeBase
        from app.shared.encryption.encrypted_field_mixin import (
            EncryptedFieldMixin, _sha256_hash, _decrypt,
        )

        class _TestBase(DeclarativeBase):
            pass

        class _PiiModel(EncryptedFieldMixin, _TestBase):
            __tablename__ = "_pii_hybrid_test_001"
            # "_email_raw" → hybrid_property "email"
            _pii_encrypt_fields = [("_email_raw", "_email_encrypted", "email_hash")]
            id = Column(Integer, primary_key=True)
            _email_raw = Column("email", String(255), nullable=True)
            _email_encrypted = Column("email_encrypted", LargeBinary, nullable=True)
            email_hash = Column(String(64), nullable=True)

        obj = _PiiModel(id=1)
        obj._email_encrypted = None
        obj.email_hash = None
        obj._email_raw = None

        # Write via the public hybrid property
        obj.email = "test@example.com"

        # _email_raw (DB column) must be NULL — no plaintext at rest
        assert obj._email_raw is None, (
            "_email_raw DB column must be NULL after write — PII not stored in plaintext"
        )
        # Encrypted bytes must be populated
        assert obj._email_encrypted is not None
        assert isinstance(obj._email_encrypted, bytes)
        assert b"test@example.com" not in obj._email_encrypted
        # Decryption must round-trip
        assert _decrypt(obj._email_encrypted) == "test@example.com"
        # Hash must be correct
        assert obj.email_hash == _sha256_hash("test@example.com")
        # Transparent read: obj.email returns decrypted plaintext (from encrypted col)
        assert obj.email == "test@example.com", (
            "obj.email must return plaintext transparently (auth/JWT/email services)"
        )

    def test_hybrid_property_encrypts_cpf_and_nulls_raw(self):
        """Setting cpf via hybrid must populate _cpf_encrypted AND null _cpf_raw."""
        from sqlalchemy import Column, LargeBinary, String, Integer
        from sqlalchemy.orm import DeclarativeBase
        from app.shared.encryption.encrypted_field_mixin import (
            EncryptedFieldMixin, _decrypt,
        )

        class _TestBase2(DeclarativeBase):
            pass

        class _CpfModel(EncryptedFieldMixin, _TestBase2):
            __tablename__ = "_cpf_hybrid_test_002"
            _pii_encrypt_fields = [("_cpf_raw", "_cpf_encrypted", None)]
            id = Column(Integer, primary_key=True)
            _cpf_raw = Column("cpf", String(14), nullable=True)
            _cpf_encrypted = Column("cpf_encrypted", LargeBinary, nullable=True)

        obj = _CpfModel(id=1)
        obj._cpf_encrypted = None
        obj._cpf_raw = None

        obj.cpf = "123.456.789-09"

        # _cpf_raw DB column must be NULL
        assert obj._cpf_raw is None, "_cpf_raw must be NULL — no CPF stored in plaintext"
        # CPF must be recoverable from encrypted column
        assert obj._cpf_encrypted is not None
        assert _decrypt(obj._cpf_encrypted) == "123.456.789-09"
        # Transparent read
        assert obj.cpf == "123.456.789-09"

    def test_none_value_clears_encrypted_columns(self):
        """Setting None via hybrid must also clear encrypted/hash columns."""
        from sqlalchemy import Column, LargeBinary, String, Integer
        from sqlalchemy.orm import DeclarativeBase
        from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin

        class _TestBase3(DeclarativeBase):
            pass

        class _NullModel(EncryptedFieldMixin, _TestBase3):
            __tablename__ = "_null_hybrid_test_003"
            _pii_encrypt_fields = [("_email_raw", "_email_encrypted", "email_hash")]
            id = Column(Integer, primary_key=True)
            _email_raw = Column("email", String(255), nullable=True)
            _email_encrypted = Column("email_encrypted", LargeBinary, nullable=True)
            email_hash = Column(String(64), nullable=True)

        obj = _NullModel(id=1)
        obj._email_encrypted = b"previous_encrypted"
        obj.email_hash = "prevhash"

        obj.email = None

        assert obj._email_encrypted is None
        assert obj.email_hash is None

    def test_encrypted_field_mixin_email_hash_helper(self):
        from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin
        h = EncryptedFieldMixin.email_hash_for("hello@world.com")
        assert len(h) == 64

    def test_no_key_raises_in_production_mode(self):
        """Without FIELD_ENCRYPTION_KEY and IS_DEVELOPMENT != 'true', raises EncryptionKeyMissingError."""
        os.environ.pop("FIELD_ENCRYPTION_KEY", None)
        os.environ.pop("IS_DEVELOPMENT", None)
        import importlib
        import app.shared.encryption.encrypted_field_mixin as efm
        importlib.reload(efm)
        with pytest.raises(efm.EncryptionKeyMissingError):
            efm._encrypt("hello")
        os.environ["FIELD_ENCRYPTION_KEY"] = self._test_key

    def test_no_key_dev_mode_uses_raw_bytes(self):
        """IS_DEVELOPMENT=true allows fallback to raw-bytes for local dev."""
        os.environ.pop("FIELD_ENCRYPTION_KEY", None)
        os.environ["IS_DEVELOPMENT"] = "true"
        import importlib
        import app.shared.encryption.encrypted_field_mixin as efm
        importlib.reload(efm)
        result = efm._encrypt("hello")
        assert result == b"hello"
        os.environ.pop("IS_DEVELOPMENT", None)
        os.environ["FIELD_ENCRYPTION_KEY"] = self._test_key


# ---------------------------------------------------------------------------
# 3. Fairness Report Endpoint Tests
# ---------------------------------------------------------------------------

class TestFairnessReportEndpoint:
    """Tests for GET /api/v1/admin/compliance/fairness/report."""

    def _make_app_with_overrides(self, admin_user=None, db=None):
        """Create FastAPI app with dependency overrides for testing."""
        from fastapi import FastAPI
        from fastapi import HTTPException
        from app.api.v1.admin_compliance_fairness import router
        from app.auth.dependencies import require_admin
        from app.core.database import get_db

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        if admin_user is not None:
            app.dependency_overrides[require_admin] = lambda: admin_user
        else:
            async def _deny():
                raise HTTPException(status_code=403, detail="Admin required")
            app.dependency_overrides[require_admin] = _deny

        if db is not None:
            app.dependency_overrides[get_db] = lambda: db

        return app

    def _make_mock_db(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        return mock_db

    @pytest.mark.asyncio
    async def test_json_report_200_with_admin(self):
        """Admin user receives 200 with JSON fairness report."""
        mock_user = MagicMock()
        mock_user.role = "admin"
        app = self._make_app_with_overrides(admin_user=mock_user, db=self._make_mock_db())

        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/admin/compliance/fairness/report",
                params={"period": "30d", "format": "json"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "total_candidates_evaluated" in data
        assert "four_fifths_by_dimension" in data
        assert "overall_pass" in data

    @pytest.mark.asyncio
    async def test_non_admin_receives_403(self):
        """Non-admin user must receive 403 Forbidden."""
        app = self._make_app_with_overrides(admin_user=None, db=self._make_mock_db())

        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/admin/compliance/fairness/report",
                params={"period": "30d"},
            )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_csv_report_returns_csv_content(self):
        """CSV format returns proper CSV content-type."""
        mock_user = MagicMock()
        app = self._make_app_with_overrides(admin_user=mock_user, db=self._make_mock_db())

        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/admin/compliance/fairness/report",
                params={"period": "7d", "format": "csv"},
            )

        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_pdf_without_weasyprint_returns_503(self):
        """PDF format returns 503 when WeasyPrint is not installed."""
        from unittest.mock import patch
        mock_user = MagicMock()
        app = self._make_app_with_overrides(admin_user=mock_user, db=self._make_mock_db())

        with patch(
            "app.api.v1.admin_compliance_fairness._report_to_pdf_bytes",
            side_effect=ImportError("No module named 'weasyprint'"),
        ):
            from httpx import AsyncClient, ASGITransport
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/api/v1/admin/compliance/fairness/report",
                    params={"period": "90d", "format": "pdf"},
                )

        assert resp.status_code == 503
        assert "WeasyPrint" in resp.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_custom_period_requires_dates(self):
        """period=custom without start_date/end_date returns 422."""
        mock_user = MagicMock()
        app = self._make_app_with_overrides(admin_user=mock_user, db=self._make_mock_db())

        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/admin/compliance/fairness/report",
                params={"period": "custom"},
            )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_report_contains_required_fields(self):
        """JSON report includes all required compliance fields."""
        mock_user = MagicMock()
        app = self._make_app_with_overrides(admin_user=mock_user, db=self._make_mock_db())

        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/admin/compliance/fairness/report",
                params={"period": "30d", "format": "json"},
            )

        data = resp.json()
        required_keys = [
            "period", "start_date", "end_date", "generated_at",
            "total_candidates_evaluated", "four_fifths_by_dimension", "overall_pass",
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_parse_period_valid_values(self):
        """_parse_period correctly parses standard periods."""
        from app.api.v1.admin_compliance_fairness import _parse_period

        for period in ("7d", "30d", "90d"):
            start, end = _parse_period(period, None, None)
            delta = end - start
            expected_days = int(period[:-1])
            assert abs(delta.days - expected_days) <= 1

    @pytest.mark.asyncio
    async def test_parse_period_custom(self):
        """_parse_period handles custom date range."""
        from app.api.v1.admin_compliance_fairness import _parse_period

        start, end = _parse_period("custom", "2025-01-01", "2025-03-31")
        assert start.year == 2025
        assert end.month == 3

    @pytest.mark.asyncio
    async def test_four_fifths_threshold_is_80_percent(self):
        """Four-Fifths Rule threshold must be 0.80."""
        from app.api.v1.admin_compliance_fairness import FOUR_FIFTHS_THRESHOLD
        assert FOUR_FIFTHS_THRESHOLD == 0.80

    @pytest.mark.asyncio
    async def test_json_report_includes_signature_field(self):
        """JSON report must include report_signature field for tamper-evidence."""
        mock_user = MagicMock()
        app = self._make_app_with_overrides(admin_user=mock_user, db=self._make_mock_db())

        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/admin/compliance/fairness/report",
                params={"period": "30d", "format": "json"},
            )

        data = resp.json()
        assert "report_signature" in data, "report_signature field required for NYC LL 144 / EU AI Act auditability"

    @pytest.mark.asyncio
    async def test_json_report_signed_with_key(self):
        """With REPORT_SIGNING_KEY set, report_signature must not be 'unsigned'."""
        import os
        os.environ["REPORT_SIGNING_KEY"] = "test-signing-key-for-compliance"
        try:
            mock_user = MagicMock()
            app = self._make_app_with_overrides(admin_user=mock_user, db=self._make_mock_db())

            from httpx import AsyncClient, ASGITransport
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/api/v1/admin/compliance/fairness/report",
                    params={"period": "30d", "format": "json"},
                )

            data = resp.json()
            assert data["report_signature"] != "unsigned"
            assert len(data["report_signature"]) == 64  # SHA-256 hex digest
        finally:
            os.environ.pop("REPORT_SIGNING_KEY", None)


# ---------------------------------------------------------------------------
# 4. Four-Fifths Rule Computation Tests
# ---------------------------------------------------------------------------

class TestFourFifthsComputation:
    """Unit tests for _compute_four_fifths per-group AIR logic."""

    def test_passes_when_all_groups_above_threshold(self):
        """All groups above 0.80 AIR → passes."""
        from app.api.v1.admin_compliance_fairness import _compute_four_fifths

        groups = [
            {"group": "male", "total": 100, "approved": 80},
            {"group": "female", "total": 100, "approved": 72},
        ]
        result = _compute_four_fifths("gender", groups)
        assert result.reference_group == "male"
        assert abs(result.reference_rate - 0.80) < 0.001
        assert abs(result.min_adverse_impact_ratio - 0.90) < 0.01
        assert result.passes_four_fifths_rule is True

    def test_fails_when_group_below_threshold(self):
        """Group with AIR < 0.80 → fails."""
        from app.api.v1.admin_compliance_fairness import _compute_four_fifths

        groups = [
            {"group": "white", "total": 200, "approved": 160},
            {"group": "black", "total": 100, "approved": 60},
        ]
        result = _compute_four_fifths("race", groups)
        assert result.reference_group == "white"
        air_black = (60 / 100) / (160 / 200)
        assert abs(result.min_adverse_impact_ratio - air_black) < 0.01
        assert result.passes_four_fifths_rule is False

    def test_single_group_passes(self):
        """Single group with no comparator → AIR=1.0 → passes."""
        from app.api.v1.admin_compliance_fairness import _compute_four_fifths

        groups = [{"group": "male", "total": 50, "approved": 40}]
        result = _compute_four_fifths("gender", groups)
        assert result.passes_four_fifths_rule is True
        assert result.min_adverse_impact_ratio == 1.0

    def test_empty_groups_passes(self):
        """Empty group list → no data → passes by default."""
        from app.api.v1.admin_compliance_fairness import _compute_four_fifths

        result = _compute_four_fifths("disability", [])
        assert result.passes_four_fifths_rule is True
        assert result.min_adverse_impact_ratio == 1.0

    def test_reference_group_is_highest_approval_rate(self):
        """Reference group is the one with the highest approval rate."""
        from app.api.v1.admin_compliance_fairness import _compute_four_fifths

        groups = [
            {"group": "under_40", "total": 100, "approved": 90},
            {"group": "over_40", "total": 100, "approved": 60},
        ]
        result = _compute_four_fifths("age_group", groups)
        assert result.reference_group == "under_40"
        assert abs(result.reference_rate - 0.90) < 0.001

    def test_air_computed_against_reference_not_average(self):
        """AIR = minority_rate / reference_rate (not against average)."""
        from app.api.v1.admin_compliance_fairness import _compute_four_fifths

        groups = [
            {"group": "A", "total": 100, "approved": 50},
            {"group": "B", "total": 100, "approved": 100},
            {"group": "C", "total": 100, "approved": 40},
        ]
        result = _compute_four_fifths("region", groups)
        assert result.reference_group == "B"
        expected_min_air = 40 / 100
        assert abs(result.min_adverse_impact_ratio - expected_min_air) < 0.01
