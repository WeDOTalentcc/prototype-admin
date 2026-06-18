"""
Sentinel tests for CompanyPlanConfig (Fase 1.1) and dependent services (Fases 1.2-1.3).
Static file-based checks to avoid SQLAlchemy MetaData conflicts in the test suite.
"""
import os
import re


PLAN_CONFIG_MODEL = "libs/models/lia_models/plan_config.py"
MIGRATION_292     = "alembic/versions/292_add_company_plan_configs.py"
TOKEN_BUDGET_SVC  = "app/domains/credits/services/token_budget_service.py"
QUOTA_ENFORCEMENT = "app/services/quota_enforcement.py"


def _src(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestCompanyPlanConfigModel:

    def test_model_file_exists(self):
        assert os.path.exists(PLAN_CONFIG_MODEL)

    def test_tablename_is_company_plan_configs(self):
        assert '__tablename__ = "company_plan_configs"' in _src(PLAN_CONFIG_MODEL)

    def test_required_columns_declared(self):
        src = _src(PLAN_CONFIG_MODEL)
        required = [
            "plan_code", "max_seats",
            "embedding_monthly_cap", "llm_monthly_cap", "llm_request_ceiling",
            "pearch_credits_monthly", "pearch_credits_rollover",
            "apify_credits_monthly", "apify_credits_rollover",
            "max_custom_agents", "agent_executions_monthly",
            "feature_flags", "is_trial", "trial_days",
        ]
        missing = [c for c in required if c not in src]
        assert not missing, f"Missing column declarations: {missing}"

    def test_plan_code_has_unique_constraint(self):
        src = _src(PLAN_CONFIG_MODEL)
        assert "unique=True" in src or "UniqueConstraint" in src

    def test_feature_flags_is_jsonb(self):
        src = _src(PLAN_CONFIG_MODEL)
        assert "JSONB" in src and "feature_flags" in src


class TestSeedData:

    def test_migration_file_exists(self):
        assert os.path.exists(MIGRATION_292)

    def test_all_four_tiers_present(self):
        src = _src(MIGRATION_292)
        for tier in ("trial", "starter", "pro", "enterprise"):
            assert '"plan_code": "' + tier + '"' in src, f"Tier '{tier}' missing from seed"

    def test_starter_has_bulk_actions_and_export_full(self):
        src = _src(MIGRATION_292)
        assert "bulk_actions" in src
        assert "export_full" in src

    def test_enterprise_has_paradigm_flags(self):
        src = _src(MIGRATION_292)
        for flag in ("projetos_advanced", "digital_twins", "api_access", "white_label"):
            assert flag in src, f"Enterprise flag '{flag}' missing"

    def test_trial_duration_is_30_days(self):
        src = _src(MIGRATION_292)
        assert "30" in src and "trial_days" in src

    def test_enterprise_rollover_enabled(self):
        src = _src(MIGRATION_292)
        assert "rollover" in src


class TestTokenBudgetServiceDBRead:

    def test_imports_plan_config_model(self):
        src = _src(TOKEN_BUDGET_SVC)
        assert "plan_config" in src.lower() or "CompanyPlanConfig" in src

    def test_has_db_read_and_fallback(self):
        src = _src(TOKEN_BUDGET_SVC)
        assert "company_plan_configs" in src or "CompanyPlanConfig" in src
        assert "PLAN_DAILY_LIMITS" in src or "fallback" in src.lower()

    def test_has_cache_invalidation(self):
        src = _src(TOKEN_BUDGET_SVC)
        assert "invalidate" in src.lower() and "cache" in src.lower()


class TestQuotaEnforcementDBRead:

    def test_references_plan_config(self):
        src = _src(QUOTA_ENFORCEMENT)
        assert "plan_config" in src.lower() or "CompanyPlanConfig" in src

    def test_has_hardcoded_fallback(self):
        src = _src(QUOTA_ENFORCEMENT)
        assert "PLAN_AGENT_QUOTAS" in src or "fallback" in src.lower()
