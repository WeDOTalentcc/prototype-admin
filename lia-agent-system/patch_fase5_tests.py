#!/usr/bin/env python3
"""
FASE 5 — Append 5 tests to test_phase4_fail_loud_red.py

Tests added:
  TestPublishIdentity:
    - test_publish_populates_identity_fields    (H1: recruiter/manager kwargs)
    - test_publish_created_by_valid_uuid        (happy-path: UUID passthrough)
    - test_publish_created_by_anonymous_becomes_none  (anonymous filtered)
    - test_publish_populates_stakeholders       (H3: stakeholders not discarded)
  TestManagerEmailWarning:
    - test_manager_email_domain_warning         (H2: cross-domain logs warning)
"""
import sys

TARGET = "tests/wizard/test_phase4_fail_loud_red.py"

with open(TARGET, encoding="utf-8") as f:
    src = f.read()

# Verify the file already has our existing Phase 4 tests as anchor
ANCHOR = "class TestGenerateWsiScreeningModeGuard:"
if ANCHOR not in src:
    print(f"ERROR: anchor '{ANCHOR}' not found in {TARGET}")
    sys.exit(1)

NEW_TESTS = '''

# ── FASE 5: H1+H3+H4+H2 identity + stakeholders + created_by + domain warning ──


class TestPublishIdentity:
    """H1+H3+H4 — _publish_job_fastapi must populate identity/stakeholders/created_by."""

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _make_state(user_id="", recruiter_name="", recruiter_email="",
                    manager_name="", manager_email="", stakeholders=None):
        return {
            "user_id": user_id,
            "parsed_recruiter_name": recruiter_name,
            "parsed_recruiter_email": recruiter_email,
            "parsed_manager_name": manager_name,
            "parsed_manager_email": manager_email,
            "parsed_stakeholders": stakeholders or [],
            # required by _publish_job_fastapi to build the vacancy
            "job_title": "Engenheiro de Software",
            "job_description": "Descricao",
            "job_responsibilities": ["Responsabilidade"],
            "skills_obrigatorias": ["Python"],
            "job_department": "Engenharia",
            "job_location": "Remoto",
            "seniority_level": "Pleno",
            "work_model": "remoto",
            "salary_range": "10000-15000",
            # no questions_approved → skips question_set branch
        }

    @staticmethod
    def _run_publish(state):
        import asyncio
        import importlib
        import libs.models.lia_models.job_vacancy as _jv_mod
        _tools = importlib.import_module(
            "app.domains.job_creation.orchestrator.wizard_service_tools"
        )
        _db_mod = importlib.import_module("app.core.database")
        _jr_mod = importlib.import_module(
            "app.domains.job_management.repositories.job_vacancy_crud_repository"
        )
        _publish_job_fastapi = _tools._publish_job_fastapi

        captured_kwargs = {}

        class _FakeVacancy:
            id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

        class _FakeRepo:
            async def create_vacancy(self, model):
                return _FakeVacancy()

        # Capture kwargs passed to _JobVacancyModel constructor
        from unittest.mock import MagicMock, AsyncMock, patch

        def _capture_jv(**kwargs):
            captured_kwargs.update(kwargs)
            return MagicMock()

        mock_jv_cls = MagicMock(side_effect=_capture_jv)
        fake_db = MagicMock()
        fake_db.__aenter__ = AsyncMock(return_value=fake_db)
        fake_db.__aexit__ = AsyncMock(return_value=False)
        fake_db.commit = AsyncMock()

        with (
            patch.object(_db_mod, "AsyncSessionLocal", return_value=fake_db),
            patch.object(_jr_mod, "JobVacancyCRUDRepository", return_value=_FakeRepo()),
            patch.object(_jv_mod, "JobVacancy", mock_jv_cls),
        ):
            asyncio.run(_publish_job_fastapi(state, _VALID_UUID))

        return captured_kwargs

    # ------------------------------------------------------------------ tests

    def test_publish_populates_identity_fields(self):
        """H1: vacancy constructor receives recruiter/manager identity kwargs."""
        state = self._make_state(
            user_id="cc1d4a5b-0001-0002-0003-aabbccddeeff",
            recruiter_name="Ana Lima",
            recruiter_email="ana@empresa.com",
            manager_name="Carlos Souza",
            manager_email="carlos@empresa.com",
        )
        kwargs = self._run_publish(state)
        assert kwargs.get("recruiter") == "Ana Lima", f"recruiter={kwargs.get('recruiter')!r}"
        assert kwargs.get("recruiter_email") == "ana@empresa.com"
        assert kwargs.get("manager") == "Carlos Souza"
        assert kwargs.get("manager_email") == "carlos@empresa.com"

    def test_publish_created_by_valid_uuid(self):
        """H1 happy-path: valid UUID in state['user_id'] passes through as created_by."""
        _uuid = "cc1d4a5b-0001-0002-0003-aabbccddeeff"
        state = self._make_state(user_id=_uuid)
        kwargs = self._run_publish(state)
        assert kwargs.get("created_by") == _uuid, (
            f"expected {_uuid!r}, got {kwargs.get('created_by')!r} — "
            "filtro pode estar filtrando demais"
        )

    def test_publish_created_by_anonymous_becomes_none(self):
        """H4: 'anonymous' and '' must become None — not stored as created_by."""
        for bad_uid in ("anonymous", "", None):
            state = self._make_state(user_id=bad_uid or "")
            # For None: state["user_id"] won't exist / will be ""
            if bad_uid is None:
                state.pop("user_id", None)
            kwargs = self._run_publish(state)
            assert kwargs.get("created_by") is None, (
                f"user_id={bad_uid!r} → created_by deve ser None, "
                f"got {kwargs.get('created_by')!r}"
            )

    def test_publish_populates_stakeholders(self):
        """H3: stakeholders defined via set_stakeholders must reach the vacancy model."""
        _stk = [
            {"name": "Maria", "email": "maria@empresa.com", "role": "hiring_manager"},
            {"name": "Pedro", "email": "pedro@empresa.com", "role": "tech_lead"},
        ]
        state = self._make_state(stakeholders=_stk)
        kwargs = self._run_publish(state)
        assert kwargs.get("stakeholders") == _stk, (
            f"stakeholders={kwargs.get('stakeholders')!r} — "
            "dado definido via set_stakeholders esta sendo descartado (H3)"
        )


class TestManagerEmailDomainWarning:
    """H2: manager email com dominio diferente do recrutador deve logar warning."""

    def test_manager_email_domain_warning(self, caplog):
        """Warning logged when manager domain differs from recruiter domain."""
        import logging
        import importlib
        _svc = importlib.import_module(
            "app.domains.job_creation.services.wizard_session_service"
        )
        WizardSessionService = _svc.WizardSessionService

        # Minimal state with recruiter domain @empresa.com, manager @outra.com
        state = {
            "parsed_recruiter_email": "recrutador@empresa.com",
        }
        context = {
            "_raw_user_message": "meu gestor e lider@outra.com",
        }
        thread_id = "test-thread-h2"

        svc = WizardSessionService.__new__(WizardSessionService)

        with caplog.at_level(
            logging.WARNING,
            logger="app.domains.job_creation.services.wizard_session_service",
        ):
            # Call the private method that extracts manager email and applies warning
            # We simulate what _update_manager_identity does when it finds an email
            from unittest.mock import patch, MagicMock
            import re

            # Patch _extract_manager_email to return a controllable cross-domain email
            with patch.object(
                _svc,
                "_extract_manager_email",
                return_value="lider@outra.com",
            ):
                # Invoke the identity-update path directly
                # _update_manager_identity is the internal method at line ~1083
                if hasattr(svc, "_update_manager_identity"):
                    svc._update_manager_identity(state, context, "user_message", thread_id)
                else:
                    # Fallback: call the public method that invokes it
                    # and check the warning appears
                    pass  # will fail explicitly below if method doesn't exist

        # The warning must mention the cross-domain mismatch
        domain_warnings = [
            r for r in caplog.records
            if r.levelno == logging.WARNING and "dominio" in r.message.lower()
        ]
        assert domain_warnings, (
            "Expected a WARNING about manager domain mismatch — none found. "
            f"All log records: {[r.message for r in caplog.records]}"
        )
        assert "outra.com" in domain_warnings[0].message or "empresa.com" in domain_warnings[0].message
'''

# Append before the last line (if it ends cleanly) or just at the end
src = src.rstrip() + "\n" + NEW_TESTS + "\n"

with open(TARGET, "w", encoding="utf-8") as f:
    f.write(src)

print(f"OK: 5 tests appended to {TARGET}")

# Quick syntax check
import py_compile, tempfile, os
tmp = tempfile.mktemp(suffix=".py")
with open(TARGET) as f:
    code = f.read()
with open(tmp, "w") as f:
    f.write(code)
try:
    py_compile.compile(tmp, doraise=True)
    print("OK: syntax check passed")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
finally:
    try:
        os.unlink(tmp)
    except Exception:
        pass
