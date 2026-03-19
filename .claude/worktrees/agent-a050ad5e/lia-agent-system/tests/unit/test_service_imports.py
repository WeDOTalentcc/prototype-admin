"""Import coverage for stub service re-export modules."""
import importlib


class TestServiceStubImports:
    def test_email_providers_importable(self):
        m = importlib.import_module("app.services.email_providers")
        assert m is not None

    def test_evaluation_criteria_service_importable(self):
        m = importlib.import_module("app.services.evaluation_criteria_service")
        assert m is not None

    def test_jd_template_service_importable(self):
        m = importlib.import_module("app.services.jd_template_service")
        assert m is not None

    def test_job_audit_service_importable(self):
        m = importlib.import_module("app.services.job_audit_service")
        assert m is not None

    def test_job_clone_service_importable(self):
        m = importlib.import_module("app.services.job_clone_service")
        assert m is not None

    def test_merge_ats_service_importable(self):
        m = importlib.import_module("app.services.merge_ats_service")
        assert m is not None

    def test_score_normalization_service_importable(self):
        m = importlib.import_module("app.services.score_normalization_service")
        assert m is not None

    def test_stage_automation_engine_importable(self):
        m = importlib.import_module("app.services.stage_automation_engine")
        assert m is not None

    def test_template_learning_service_importable(self):
        m = importlib.import_module("app.services.template_learning_service")
        assert m is not None

    def test_wsi_question_service_importable(self):
        m = importlib.import_module("app.services.wsi_question_service")
        assert m is not None

    def test_seniority_jd_analyzer_importable(self):
        m = importlib.import_module("app.services.seniority_jd_analyzer")
        assert m is not None

    def test_proactive_service_importable(self):
        m = importlib.import_module("app.services.proactive_service")
        assert m is not None

    def test_proactive_alert_service_importable(self):
        m = importlib.import_module("app.services.proactive_alert_service")
        assert m is not None

    def test_teams_bot_importable_or_skipped(self):
        """teams_bot may fail due to missing botbuilder.core symbols."""
        try:
            m = importlib.import_module("app.services.teams_bot")
            assert m is not None
        except ImportError:
            import pytest
            pytest.skip("teams_bot requires botbuilder extras not installed")

    def test_modules_have_file_attribute(self):
        modules = [
            "app.services.email_providers",
            "app.services.score_normalization_service",
            "app.services.stage_automation_engine",
        ]
        for mod_name in modules:
            m = importlib.import_module(mod_name)
            assert hasattr(m, "__file__") or hasattr(m, "__spec__")
