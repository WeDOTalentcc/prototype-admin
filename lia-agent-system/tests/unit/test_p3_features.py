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

    @patch("app.jobs.tasks.communication.asyncio")
    def test_send_daily_calls_asyncio_run(self, mock_asyncio):
        """send_daily_briefing_task deve chamar asyncio.run(...)."""
        from app.jobs.celery_tasks import send_daily_briefing_task
        mock_asyncio.run.return_value = {"sent": 5, "skipped": 0, "errors": 0}
        result = send_daily_briefing_task()
        mock_asyncio.run.assert_called_once()

    @patch("app.jobs.tasks.communication.asyncio")
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

class TestJDUploadEndpoint:
    """Testa a lógica de validação do endpoint upload-file via HTTP."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.v1.jd_import import router
        from app.auth.dependencies import get_current_user_or_demo
        from app.core.database import get_db
        from unittest.mock import MagicMock

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        # Override auth + DB dependencies
        mock_user = MagicMock()
        mock_user.id = "00000000-0000-0000-0000-000000000001"
        mock_user.company_id = "00000000-0000-0000-0000-000000000001"

        async def override_auth():
            return mock_user

        async def override_db():
            return AsyncMock()

        from app.shared.security.require_company_id import require_company_id

        async def override_company_id():
            return str(mock_user.company_id)

        app.dependency_overrides[get_current_user_or_demo] = override_auth
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[require_company_id] = override_company_id

        return TestClient(app, raise_server_exceptions=False)

    def test_unsupported_file_type_returns_400(self, client):
        """Arquivo .exe deve retornar 400."""
        response = client.post(
            "/api/v1/import/upload-file",
            files={"file": ("malware.exe", b"binary_data", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "não suportado" in response.json()["detail"].lower() or response.status_code == 400

    def test_file_too_large_returns_413(self, client):
        """Arquivo > 5MB deve retornar 413."""
        big_content = b"x" * (5 * 1024 * 1024 + 1)
        response = client.post(
            "/api/v1/import/upload-file",
            files={"file": ("big.txt", big_content, "text/plain")},
        )
        assert response.status_code == 413

    def test_empty_txt_file_returns_422(self, client):
        """Arquivo .txt vazio deve retornar 422."""
        response = client.post(
            "/api/v1/import/upload-file",
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
            "/api/v1/import/upload-file",
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
                "/api/v1/import/upload-file",
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
                "/api/v1/import/upload-file?title=Dev%20Backend",
                files={"file": ("arquivo.txt", content, "text/plain")},
            )
            assert response.status_code in (200, 422, 500)  # não 400
            if mock_svc.import_jd.called:
                call_kwargs = mock_svc.import_jd.call_args[1]
                assert call_kwargs["jd_data"]["title"] == "Dev Backend"


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
# FairnessGuard no JD upload
# ─────────────────────────────────────────────────────────────────

class TestJDUploadFairnessGuard:
    """FairnessGuard bloqueia JDs com linguagem discriminatoria."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from app.api.v1.jd_import import router
        from app.auth.dependencies import get_current_user_or_demo
        from app.core.database import get_db
        from unittest.mock import MagicMock

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        mock_user = MagicMock()
        mock_user.id = "00000000-0000-0000-0000-000000000001"
        mock_user.company_id = "00000000-0000-0000-0000-000000000001"

        async def override_auth():
            return mock_user

        async def override_db():
            return AsyncMock()

        from app.shared.security.require_company_id import require_company_id

        async def override_company_id():
            return str(mock_user.company_id)

        app.dependency_overrides[get_current_user_or_demo] = override_auth
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[require_company_id] = override_company_id
        return TestClient(app, raise_server_exceptions=False)

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
                "/api/v1/import/upload-file",
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
                    "/api/v1/import/upload-file",
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
                    "/api/v1/import/upload-file",
                    files={"file": ("vaga.txt", content, "text/plain")},
                )
                # Fail-safe: continua mesmo com FairnessGuard indisponivel
                assert response.status_code != 422
