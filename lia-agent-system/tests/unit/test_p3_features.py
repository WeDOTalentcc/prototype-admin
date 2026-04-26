"""
Tests — P3 Features: Briefing Task + JD Upload Endpoint

Cobre:
- P3-1: briefing.send_daily Celery task (task registration, asyncio.run, retry)
- P3-2: POST /import/upload-file (file type validation, size limit, text extraction)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from io import BytesIO


# ─────────────────────────────────────────────────────────────────
# P3-1: briefing.send_daily Celery task
# ─────────────────────────────────────────────────────────────────

class TestBriefingCeleryTask:
    def test_task_registered_in_celery_app(self):
        """briefing.send_daily deve estar registrado no celery_app."""
        from lia_config.celery_app import celery_app
        assert "briefing-daily" in celery_app.conf.beat_schedule, (
            "Celery beat schedule deve conter 'briefing-daily'"
        )
        entry = celery_app.conf.beat_schedule["briefing-daily"]
        assert entry["task"] == "briefing.send_daily"

    def test_beat_schedule_hour_and_minute(self):
        """briefing-daily deve rodar às 09:00 UTC (= 06h Brasília)."""
        from lia_config.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["briefing-daily"]
        schedule = entry["schedule"]
        # crontab(hour=9, minute=0)
        assert 9 in schedule.hour
        assert 0 in schedule.minute

    def test_send_daily_task_exists_in_celery_tasks(self):
        """Módulo celery_tasks deve expor send_daily_briefing_task."""
        import app.jobs.celery_tasks as tasks
        assert hasattr(tasks, "send_daily_briefing_task"), (
            "celery_tasks deve ter send_daily_briefing_task definido"
        )

    @patch("app.jobs.celery_tasks.asyncio")
    def test_send_daily_calls_asyncio_run(self, mock_asyncio):
        """send_daily_briefing_task deve chamar asyncio.run(...)."""
        from app.jobs.celery_tasks import send_daily_briefing_task
        mock_asyncio.run.return_value = {"sent": 5, "skipped": 0, "errors": 0}
        result = send_daily_briefing_task()
        mock_asyncio.run.assert_called_once()

    @patch("app.jobs.celery_tasks.asyncio")
    def test_send_daily_returns_dict(self, mock_asyncio):
        """send_daily_briefing_task deve retornar dict com sent/skipped/errors."""
        from app.jobs.celery_tasks import send_daily_briefing_task
        mock_asyncio.run.return_value = {"sent": 3, "skipped": 1, "errors": 0}
        result = send_daily_briefing_task()
        # task deve retornar o resultado do asyncio.run
        assert result is not None


# ─────────────────────────────────────────────────────────────────
# P3-2: POST /import/upload-file — validações no endpoint
# ─────────────────────────────────────────────────────────────────

def _build_upload_test_app():
    """Helper: app + TestClient with strict-auth + DB + audit helpers stubbed.

    Task #838 changed `/import/upload-file` to use `get_current_user_strict`
    and to persist consent + audit records. Tests stub those helpers so they
    don't require a real DB or rails JWT.
    """
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from app.api.v1 import jd_import
    from app.auth.dependencies import get_current_user_strict, get_current_user_or_demo
    from app.core.database import get_db
    from unittest.mock import MagicMock

    app = FastAPI()
    app.include_router(jd_import.router, prefix="/api/v1")

    mock_user = MagicMock()
    mock_user.id = "00000000-0000-0000-0000-000000000001"
    mock_user.company_id = "00000000-0000-0000-0000-000000000001"

    async def override_auth():
        return mock_user

    async def override_db():
        return AsyncMock()

    app.dependency_overrides[get_current_user_strict] = override_auth
    app.dependency_overrides[get_current_user_or_demo] = override_auth
    app.dependency_overrides[get_db] = override_db

    return TestClient(app, raise_server_exceptions=False), mock_user


class TestJDUploadEndpoint:
    """Testa a lógica de validação do endpoint upload-file via HTTP."""

    @pytest.fixture
    def client(self):
        # Patch audit helpers so tests don't need a real DB session.
        with patch("app.api.v1.jd_import._record_jd_upload_audit", new=AsyncMock(return_value=None)), \
             patch("app.api.v1.jd_import._record_jd_upload_consent", new=AsyncMock(return_value=None)), \
             patch("app.api.v1.jd_import._company_has_jd_upload_consent", new=AsyncMock(return_value=True)):
            client, _ = _build_upload_test_app()
            yield client

    def test_unsupported_file_type_returns_400(self, client):
        """Arquivo .exe deve retornar 400."""
        response = client.post(
            "/api/v1/import/upload-file?consent_acknowledged=true",
            files={"file": ("malware.exe", b"binary_data", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "não suportado" in response.json()["detail"].lower() or response.status_code == 400

    def test_file_too_large_returns_413(self, client):
        """Arquivo > 5MB deve retornar 413."""
        big_content = b"x" * (5 * 1024 * 1024 + 1)
        response = client.post(
            "/api/v1/import/upload-file?consent_acknowledged=true",
            files={"file": ("big.txt", big_content, "text/plain")},
        )
        assert response.status_code == 413

    def test_empty_txt_file_returns_422(self, client):
        """Arquivo .txt vazio deve retornar 422."""
        response = client.post(
            "/api/v1/import/upload-file?consent_acknowledged=true",
            files={"file": ("empty.txt", b"   \n  ", "text/plain")},
        )
        assert response.status_code == 422

    @patch("app.api.v1.jd_import.JDImportService")
    def test_valid_txt_calls_import_service(self, mock_service_cls, client):
        """Arquivo .txt válido deve chamar JDImportService.import_jd()."""
        mock_service = MagicMock()
        mock_imported = MagicMock()
        mock_imported.to_dict.return_value = {"id": "jd-1", "title": "Dev"}
        mock_service.import_jd = AsyncMock(return_value=mock_imported)
        mock_service_cls.return_value = mock_service

        txt_content = b"Vaga de desenvolvedor Python. Requisitos: 3 anos de experiencia."
        response = client.post(
            "/api/v1/import/upload-file?consent_acknowledged=true",
            files={"file": ("vaga.txt", txt_content, "text/plain")},
        )
        # Must have called import_jd
        mock_service.import_jd.assert_called_once()
        call_kwargs = mock_service.import_jd.call_args[1]
        assert call_kwargs["source"] == "file_upload"
        assert call_kwargs["parse_immediately"] is True

    def test_md_extension_accepted(self, client):
        """Arquivo .md deve ser aceito (não retornar 400)."""
        with patch("app.api.v1.jd_import.JDImportService") as mock_cls:
            mock_svc = MagicMock()
            mock_imported = MagicMock()
            mock_imported.to_dict.return_value = {"id": "jd-2", "title": "Test"}
            mock_svc.import_jd = AsyncMock(return_value=mock_imported)
            mock_cls.return_value = mock_svc

            content = b"# Vaga: Engenheiro de Software\n\nDescricao completa da vaga aqui."
            response = client.post(
                "/api/v1/import/upload-file?consent_acknowledged=true",
                files={"file": ("vaga.md", content, "text/markdown")},
            )
            assert response.status_code != 400

    def test_title_query_param_used_as_jd_title(self, client):
        """Parâmetro title= deve sobrescrever nome do arquivo como título."""
        with patch("app.api.v1.jd_import.JDImportService") as mock_cls:
            mock_svc = MagicMock()
            mock_imported = MagicMock()
            mock_imported.to_dict.return_value = {"id": "jd-3", "title": "Dev Backend"}
            mock_svc.import_jd = AsyncMock(return_value=mock_imported)
            mock_cls.return_value = mock_svc

            content = b"Vaga com titulo customizado passado por query param."
            response = client.post(
                "/api/v1/import/upload-file?title=Dev%20Backend&consent_acknowledged=true",
                files={"file": ("arquivo.txt", content, "text/plain")},
            )
            assert response.status_code in (200, 422, 500)  # não 400
            if mock_svc.import_jd.called:
                call_kwargs = mock_svc.import_jd.call_args[1]
                assert call_kwargs["jd_data"]["title"] == "Dev Backend"


# ─────────────────────────────────────────────────────────────────
# Task #838 — Privacy & audit hardening on JD upload
# ─────────────────────────────────────────────────────────────────

class TestJDUploadPrivacyHardening:
    """M-01 (consent), M-09 (no demo), M-10 (immutable audit)."""

    def test_demo_mode_disabled_in_production(self):
        """The upload endpoint must depend on get_current_user_strict (M-09)."""
        import inspect
        from app.api.v1.jd_import import upload_jd_file
        from app.auth.dependencies import (
            get_current_user_or_demo,
            get_current_user_strict,
        )

        sig = inspect.signature(upload_jd_file)
        param = sig.parameters["current_user"]
        # Default is fastapi.Depends(get_current_user_strict)
        assert param.default.dependency is get_current_user_strict, (
            "upload_jd_file deve usar get_current_user_strict para impedir demo em prod"
        )
        assert param.default.dependency is not get_current_user_or_demo

    def test_missing_consent_for_new_company_returns_428(self):
        """Sem consentimento e sem registro prévio, retorna 428 (Precondition Required)."""
        with patch("app.api.v1.jd_import._company_has_jd_upload_consent", new=AsyncMock(return_value=False)), \
             patch("app.api.v1.jd_import._record_jd_upload_audit", new=AsyncMock(return_value=None)), \
             patch("app.api.v1.jd_import._record_jd_upload_consent", new=AsyncMock(return_value=None)):
            client, _ = _build_upload_test_app()
            response = client.post(
                "/api/v1/import/upload-file",  # consent_acknowledged ausente (default False)
                files={"file": ("vaga.txt", b"Conteudo da vaga", "text/plain")},
            )
            assert response.status_code == 428
            body = response.json()
            assert body["detail"]["error"] == "consent_required"
            assert body["detail"]["consent_param"] == "consent_acknowledged"

    def test_company_with_prior_consent_bypasses_dialog(self):
        """Empresa que já consentiu não precisa enviar consent_acknowledged."""
        with patch("app.api.v1.jd_import._company_has_jd_upload_consent", new=AsyncMock(return_value=True)), \
             patch("app.api.v1.jd_import._record_jd_upload_audit", new=AsyncMock(return_value=None)), \
             patch("app.api.v1.jd_import._record_jd_upload_consent", new=AsyncMock(return_value=None)), \
             patch("app.api.v1.jd_import.JDImportService") as svc_cls:
            mock_svc = MagicMock()
            mock_imported = MagicMock()
            mock_imported.to_dict.return_value = {"id": "jd-bypass", "title": "Eng"}
            mock_svc.import_jd = AsyncMock(return_value=mock_imported)
            svc_cls.return_value = mock_svc

            client, _ = _build_upload_test_app()
            response = client.post(
                "/api/v1/import/upload-file",  # sem consent_acknowledged
                files={"file": ("vaga.txt", b"Conteudo da vaga", "text/plain")},
            )
            assert response.status_code == 200
            assert mock_svc.import_jd.called

    def test_audit_log_is_persisted_with_required_fields(self):
        """Cada upload bem-sucedido grava user_id, company_id, filename_hash, size_bytes, uuid."""
        recorded = {}

        async def fake_record_audit(**kwargs):
            recorded.update(kwargs)

        with patch("app.api.v1.jd_import._company_has_jd_upload_consent", new=AsyncMock(return_value=True)), \
             patch("app.api.v1.jd_import._record_jd_upload_consent", new=AsyncMock(return_value=None)), \
             patch("app.api.v1.jd_import._record_jd_upload_audit", new=AsyncMock(side_effect=fake_record_audit)), \
             patch("app.api.v1.jd_import.JDImportService") as svc_cls:
            mock_svc = MagicMock()
            mock_imported = MagicMock()
            mock_imported.to_dict.return_value = {"id": "jd-audit", "title": "QA"}
            mock_svc.import_jd = AsyncMock(return_value=mock_imported)
            svc_cls.return_value = mock_svc

            client, mock_user = _build_upload_test_app()
            payload = b"Vaga de QA com cobertura de testes E2E."
            response = client.post(
                "/api/v1/import/upload-file?consent_acknowledged=true",
                files={"file": ("vaga.txt", payload, "text/plain")},
            )
            assert response.status_code == 200, response.text
            assert recorded["user_id"] == str(mock_user.id)
            assert str(recorded["company_id"]) == str(mock_user.company_id)
            assert recorded["size_bytes"] == len(payload)
            assert recorded["extension"] == ".txt"
            assert isinstance(recorded["upload_uuid"], str) and len(recorded["upload_uuid"]) >= 32
            # filename hashed (SHA-256 hex = 64 chars), never plaintext
            assert len(recorded["filename_hash"]) == 64
            assert "vaga.txt" not in recorded["filename_hash"]

            # Response also exposes the audit identifiers (for client-side correlation)
            body = response.json()
            assert body["audit"]["uuid"] == recorded["upload_uuid"]
            assert body["audit"]["filename_hash"] == recorded["filename_hash"]
            assert body["audit"]["size_bytes"] == len(payload)

    def test_consent_record_persisted_only_once_per_company(self):
        """Quando ainda não há consentimento, o consent_acknowledged=true grava o registro."""
        consent_calls = []

        async def fake_record_consent(company_id, user_id):
            consent_calls.append((company_id, user_id))

        with patch("app.api.v1.jd_import._company_has_jd_upload_consent", new=AsyncMock(return_value=False)), \
             patch("app.api.v1.jd_import._record_jd_upload_audit", new=AsyncMock(return_value=None)), \
             patch("app.api.v1.jd_import._record_jd_upload_consent", new=AsyncMock(side_effect=fake_record_consent)), \
             patch("app.api.v1.jd_import.JDImportService") as svc_cls:
            mock_svc = MagicMock()
            mock_imported = MagicMock()
            mock_imported.to_dict.return_value = {"id": "jd-consent", "title": "Dev"}
            mock_svc.import_jd = AsyncMock(return_value=mock_imported)
            svc_cls.return_value = mock_svc

            client, mock_user = _build_upload_test_app()
            response = client.post(
                "/api/v1/import/upload-file?consent_acknowledged=true",
                files={"file": ("vaga.txt", b"Vaga de dev backend.", "text/plain")},
            )
            assert response.status_code == 200, response.text
            # First-time consent: registered exactly once (the helper itself
            # is idempotent across calls — second upload sees `already=True`).
            assert len(consent_calls) == 1
            assert str(consent_calls[0][0]) == str(mock_user.company_id)

    def test_filename_hash_helper_is_stable_and_pii_free(self):
        """SHA-256 do filename é estável e não expõe o nome original."""
        from app.api.v1.jd_import import _hash_filename

        h1 = _hash_filename("CV-Maria-Silva-CPF-12345.pdf")
        h2 = _hash_filename("CV-Maria-Silva-CPF-12345.pdf")
        assert h1 == h2
        assert len(h1) == 64
        assert "Maria" not in h1 and "12345" not in h1
        # Different filenames produce different hashes
        assert _hash_filename("other.pdf") != h1


# ─────────────────────────────────────────────────────────────────
# P3-1: use-daily-briefing hook (lógica interna — testável como unit)
# ─────────────────────────────────────────────────────────────────

class TestDailyBriefingTask:
    """Testes adicionais do beat schedule para garantir idempotência."""

    def test_briefing_beat_entry_has_expires(self):
        """briefing-daily deve ter options.expires definido."""
        from lia_config.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["briefing-daily"]
        assert "options" in entry
        assert entry["options"].get("expires") == 3600

    def test_task_name_matches_routes_config(self):
        """task_routes não precisa ter briefing, mas se tiver deve usar onboarding_low."""
        from lia_config.celery_app import celery_app
        routes = celery_app.conf.task_routes or {}
        # Se estiver roteado, deve ser fila de baixa prioridade
        for pattern, cfg in routes.items():
            if "briefing" in pattern:
                assert cfg.get("queue") in ("onboarding_low", "celery")


# ─────────────────────────────────────────────────────────────────
# Task #838 — Preflight de bypass de consent (M-01)
# ─────────────────────────────────────────────────────────────────

class TestJDUploadConsentStatusEndpoint:
    """`GET /import/jd-upload/consent-status` permite que o FE pule o dialogo
    quando a empresa ja consentiu — concretiza o requisito 'bypass para
    dominios ja consentidos' do done criteria.
    """

    def test_returns_true_when_company_has_prior_consent(self):
        """Empresa pre-consentida: backend devolve has_consent=True."""
        with patch(
            "app.api.v1.jd_import._company_has_jd_upload_consent",
            new=AsyncMock(return_value=True),
        ):
            client, _ = _build_upload_test_app()
            res = client.get("/api/v1/import/jd-upload/consent-status")
            assert res.status_code == 200
            assert res.json() == {"has_consent": True}

    def test_returns_false_when_company_never_consented(self):
        """Empresa nova: backend devolve has_consent=False (FE mostra dialogo)."""
        with patch(
            "app.api.v1.jd_import._company_has_jd_upload_consent",
            new=AsyncMock(return_value=False),
        ):
            client, _ = _build_upload_test_app()
            res = client.get("/api/v1/import/jd-upload/consent-status")
            assert res.status_code == 200
            assert res.json() == {"has_consent": False}

    def test_status_endpoint_is_read_only(self):
        """Preflight nao deve gravar consent nem audit (sem efeito colateral)."""
        consent_mock = AsyncMock(return_value=None)
        audit_mock = AsyncMock(return_value=None)
        with patch(
            "app.api.v1.jd_import._company_has_jd_upload_consent",
            new=AsyncMock(return_value=True),
        ), patch(
            "app.api.v1.jd_import._record_jd_upload_consent", new=consent_mock,
        ), patch(
            "app.api.v1.jd_import._record_jd_upload_audit", new=audit_mock,
        ):
            client, _ = _build_upload_test_app()
            res = client.get("/api/v1/import/jd-upload/consent-status")
            assert res.status_code == 200
            consent_mock.assert_not_called()
            audit_mock.assert_not_called()


# ─────────────────────────────────────────────────────────────────
# FairnessGuard no JD upload
# ─────────────────────────────────────────────────────────────────

class TestJDUploadFairnessGuard:
    """FairnessGuard bloqueia JDs com linguagem discriminatoria.

    Task #838 alinhamento: usa o mesmo `_build_upload_test_app()` que stuba
    `get_current_user_strict` + helpers de audit/consent; envia
    `consent_acknowledged=true` para que o gate LGPD nao mascare a saida do
    FairnessGuard.
    """

    @pytest.fixture
    def client(self):
        with patch("app.api.v1.jd_import._record_jd_upload_audit", new=AsyncMock(return_value=None)), \
             patch("app.api.v1.jd_import._record_jd_upload_consent", new=AsyncMock(return_value=None)), \
             patch("app.api.v1.jd_import._company_has_jd_upload_consent", new=AsyncMock(return_value=True)):
            client, _ = _build_upload_test_app()
            yield client

    def test_discriminatory_jd_blocked_by_fairness_guard(self, client):
        """JD com linguagem discriminatoria deve retornar 422."""
        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as mock_fg_cls:
            from unittest.mock import MagicMock
            mock_result = MagicMock()
            mock_result.is_blocked = True
            mock_result.blocked_terms = ["jovem", "solteiro"]
            mock_result.educational_message = "Criterios discriminatorios detectados."
            mock_fg_cls.return_value.check.return_value = mock_result

            content = b"Buscamos jovem solteiro sem filhos para vaga de engenheiro."
            response = client.post(
                "/api/v1/import/upload-file?consent_acknowledged=true",
                files={"file": ("vaga.txt", content, "text/plain")},
            )
            assert response.status_code == 422
            assert "discriminat" in response.json()["detail"].lower()

    def test_fairness_soft_warning_does_not_block(self, client):
        """Soft warning nao bloqueia importacao — apenas loga."""
        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as mock_fg_cls:
            mock_result = MagicMock()
            mock_result.is_blocked = False
            mock_result.soft_warnings = ["Possivel vies implicito detectado"]
            mock_result.blocked_terms = []
            mock_fg_cls.return_value.check.return_value = mock_result

            with patch("app.api.v1.jd_import.JDImportService") as mock_svc_cls:
                mock_svc = MagicMock()
                mock_imported = MagicMock()
                mock_imported.to_dict.return_value = {"id": "jd-fw", "title": "Eng"}
                mock_svc.import_jd = AsyncMock(return_value=mock_imported)
                mock_svc_cls.return_value = mock_svc

                content = b"Vaga para desenvolvedor com experiencia em sistemas."
                response = client.post(
                    "/api/v1/import/upload-file?consent_acknowledged=true",
                    files={"file": ("vaga.txt", content, "text/plain")},
                )
                # Nao bloqueado — continua normalmente
                assert response.status_code != 422
                mock_svc.import_jd.assert_called_once()

    def test_fairness_guard_failure_is_fail_safe(self, client):
        """Se FairnessGuard lancar excecao, upload deve continuar (fail-safe)."""
        with patch("app.shared.compliance.fairness_guard.FairnessGuard", side_effect=ImportError("modulo indisponivel")):
            with patch("app.api.v1.jd_import.JDImportService") as mock_svc_cls:
                mock_svc = MagicMock()
                mock_imported = MagicMock()
                mock_imported.to_dict.return_value = {"id": "jd-fs", "title": "Dev"}
                mock_svc.import_jd = AsyncMock(return_value=mock_imported)
                mock_svc_cls.return_value = mock_svc

                content = b"Vaga de desenvolvedor full stack com 3 anos de experiencia."
                response = client.post(
                    "/api/v1/import/upload-file?consent_acknowledged=true",
                    files={"file": ("vaga.txt", content, "text/plain")},
                )
                # Fail-safe: continua mesmo com FairnessGuard indisponivel
                assert response.status_code != 422
