
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from lia_models.billing import (
    CompanyModule,
    ModuleStatus,
    ModuleTier,
    AVAILABLE_MODULES,
)


def _make_module(
    company_id="comp-1",
    module_name="talent_intelligence_pro",
    status="beta",
    tier="free",
    expires_at=None,
):
    mod = CompanyModule()
    mod.id = "00000000-0000-0000-0000-000000000001"
    mod.company_id = company_id
    mod.module_name = module_name
    mod.status = status
    mod.tier = tier
    mod.activated_at = datetime.utcnow()
    mod.expires_at = expires_at
    mod.metadata_json = "{}"
    mod.created_at = datetime.utcnow()
    mod.updated_at = datetime.utcnow()
    return mod


class TestCompanyModuleModel:
    def test_to_dict_basic(self):
        mod = _make_module()
        d = mod.to_dict()
        assert d["module_name"] == "talent_intelligence_pro"
        assert d["status"] == "beta"
        assert d["tier"] == "free"
        assert d["label"] == "Talent Intelligence Pro"
        assert d["company_id"] == "comp-1"

    def test_to_dict_with_metadata(self):
        mod = _make_module()
        mod.metadata_json = {"trial_days": 30}
        d = mod.to_dict()
        assert d["metadata"]["trial_days"] == 30

    def test_to_dict_bad_metadata(self):
        mod = _make_module()
        mod.metadata_json = None
        d = mod.to_dict()
        assert d["metadata"] == {}

    def test_is_accessible_beta(self):
        mod = _make_module(status="beta")
        assert mod.is_accessible is True

    def test_is_accessible_active(self):
        mod = _make_module(status="active")
        assert mod.is_accessible is True

    def test_is_accessible_trial(self):
        mod = _make_module(status="trial")
        assert mod.is_accessible is True

    def test_is_accessible_disabled(self):
        mod = _make_module(status="disabled")
        assert mod.is_accessible is False

    def test_is_accessible_expired_status(self):
        mod = _make_module(status="expired")
        assert mod.is_accessible is False

    def test_is_accessible_coming_soon(self):
        mod = _make_module(status="coming_soon")
        assert mod.is_accessible is False

    def test_is_accessible_trial_expired_date(self):
        mod = _make_module(status="trial", expires_at=datetime.utcnow() - timedelta(days=1))
        assert mod.is_accessible is False

    def test_is_accessible_trial_not_expired(self):
        mod = _make_module(status="trial", expires_at=datetime.utcnow() + timedelta(days=30))
        assert mod.is_accessible is True


class TestModuleEnums:
    def test_module_status_values(self):
        assert ModuleStatus.BETA.value == "beta"
        assert ModuleStatus.TRIAL.value == "trial"
        assert ModuleStatus.ACTIVE.value == "active"
        assert ModuleStatus.EXPIRED.value == "expired"
        assert ModuleStatus.DISABLED.value == "disabled"
        assert ModuleStatus.COMING_SOON.value == "coming_soon"

    def test_module_tier_values(self):
        assert ModuleTier.FREE.value == "free"
        assert ModuleTier.BASIC.value == "basic"
        assert ModuleTier.PRO.value == "pro"
        assert ModuleTier.ENTERPRISE.value == "enterprise"


class TestAvailableModules:
    def test_beta_modules_exist(self):
        beta = [k for k, v in AVAILABLE_MODULES.items() if v["initial_status"] == "beta"]
        assert "talent_intelligence_pro" in beta
        assert "internal_mobility" in beta
        assert "interview_intelligence" in beta
        assert "workforce_planning" in beta
        assert "candidate_nurture" in beta
        assert len(beta) == 5

    def test_coming_soon_modules_exist(self):
        coming = [k for k, v in AVAILABLE_MODULES.items() if v["initial_status"] == "coming_soon"]
        assert "onboarding_suite" in coming
        assert "predictive_analytics" in coming
        assert len(coming) == 2

    def test_all_modules_have_required_fields(self):
        for name, info in AVAILABLE_MODULES.items():
            assert "label" in info, f"{name} missing label"
            assert "description" in info, f"{name} missing description"
            assert "initial_status" in info, f"{name} missing initial_status"


class TestModuleServiceUnit:
    @pytest.fixture
    def svc(self):
        from app.domains.modules.services.module_service import ModuleService
        return ModuleService()

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        return db

    def _mock_scalar_result(self, value):
        result = MagicMock()
        result.scalar_one_or_none.return_value = value
        return result

    def _mock_scalars_result(self, values):
        result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = values
        result.scalars.return_value = scalars
        return result

    @pytest.mark.asyncio
    async def test_is_module_active_found_beta(self, svc, mock_db):
        mod = _make_module(status="beta")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        assert await svc.is_module_active(mock_db, "comp-1", "talent_intelligence_pro") is True

    @pytest.mark.asyncio
    async def test_is_module_active_disabled_no_fallback(self, svc, mock_db):
        mod = _make_module(status="disabled")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        result = await svc.is_module_active(mock_db, "comp-1", "talent_intelligence_pro")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_module_active_expired_no_fallback(self, svc, mock_db):
        mod = _make_module(status="expired")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        result = await svc.is_module_active(mock_db, "comp-1", "talent_intelligence_pro")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_module_active_disabled_ignores_feature_flag(self, svc, mock_db):
        mod = _make_module(status="disabled")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        ff_mock = MagicMock()
        ff_mock.is_enabled = AsyncMock(return_value=True)
        with patch("app.shared.governance.feature_flag_service.feature_flag_service", ff_mock):
            result = await svc.is_module_active(mock_db, "comp-1", "talent_intelligence_pro")
            assert result is False
            ff_mock.is_enabled.assert_not_called()

    @pytest.mark.asyncio
    async def test_is_module_active_not_found_falls_back_to_feature_flag(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)

        ff_mock = MagicMock()
        ff_mock.is_enabled = AsyncMock(return_value=True)
        with patch("app.shared.governance.feature_flag_service.feature_flag_service", ff_mock):
            result = await svc.is_module_active(mock_db, "comp-1", "talent_intelligence_pro")
            assert result is True

    @pytest.mark.asyncio
    async def test_get_module_status(self, svc, mock_db):
        mod = _make_module(status="active")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        status = await svc.get_module_status(mock_db, "comp-1", "talent_intelligence_pro")
        assert status == "active"

    @pytest.mark.asyncio
    async def test_get_module_status_expired_by_date(self, svc, mock_db):
        mod = _make_module(status="trial", expires_at=datetime.utcnow() - timedelta(days=1))
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        status = await svc.get_module_status(mock_db, "comp-1", "talent_intelligence_pro")
        assert status == "expired"

    @pytest.mark.asyncio
    async def test_get_module_status_not_found(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)
        status = await svc.get_module_status(mock_db, "comp-1", "unknown_module")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_company_modules(self, svc, mock_db):
        mod1 = _make_module(module_name="talent_intelligence_pro")
        mod2 = _make_module(module_name="internal_mobility")
        mock_db.execute.return_value = self._mock_scalars_result([mod1, mod2])
        modules = await svc.get_company_modules(mock_db, "comp-1")
        assert len(modules) == 2

    @pytest.mark.asyncio
    async def test_get_company_modules_with_catalog(self, svc, mock_db):
        mod1 = _make_module(module_name="talent_intelligence_pro")
        mock_db.execute.return_value = self._mock_scalars_result([mod1])
        modules = await svc.get_company_modules(mock_db, "comp-1", include_catalog=True)
        names = [m["module_name"] for m in modules]
        assert "talent_intelligence_pro" in names
        assert "onboarding_suite" in names
        assert len(modules) == len(AVAILABLE_MODULES)

    @pytest.mark.asyncio
    async def test_activate_module_new(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)
        result = await svc.activate_module(mock_db, "comp-1", "talent_intelligence_pro")
        assert result["success"] is True
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_module_unknown(self, svc, mock_db):
        result = await svc.activate_module(mock_db, "comp-1", "nonexistent_module")
        assert result["success"] is False
        assert "Unknown module" in result["error"]

    @pytest.mark.asyncio
    async def test_activate_module_existing(self, svc, mock_db):
        mod = _make_module(status="disabled")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        result = await svc.activate_module(mock_db, "comp-1", "talent_intelligence_pro", status="active", tier="pro")
        assert result["success"] is True
        assert mod.status == "active"
        assert mod.tier == "pro"

    @pytest.mark.asyncio
    async def test_deactivate_module(self, svc, mock_db):
        mod = _make_module(status="beta")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        result = await svc.deactivate_module(mock_db, "comp-1", "talent_intelligence_pro")
        assert result["success"] is True
        assert mod.status == "disabled"

    @pytest.mark.asyncio
    async def test_deactivate_module_not_found(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)
        result = await svc.deactivate_module(mock_db, "comp-1", "talent_intelligence_pro")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_module_tier(self, svc, mock_db):
        mod = _make_module(tier="pro")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        tier = await svc.get_module_tier(mock_db, "comp-1", "talent_intelligence_pro")
        assert tier == "pro"

    @pytest.mark.asyncio
    async def test_get_module_tier_not_found(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)
        tier = await svc.get_module_tier(mock_db, "comp-1", "talent_intelligence_pro")
        assert tier is None

    @pytest.mark.asyncio
    async def test_seed_beta_modules(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)
        created = await svc.seed_beta_modules(mock_db, "comp-new")
        assert len(created) == len(AVAILABLE_MODULES)
        assert "talent_intelligence_pro" in created
        assert "onboarding_suite" in created

    @pytest.mark.asyncio
    async def test_seed_beta_modules_skips_existing(self, svc, mock_db):
        existing = _make_module(module_name="talent_intelligence_pro")
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = existing
            else:
                result.scalar_one_or_none.return_value = None
            return result

        mock_db.execute.side_effect = side_effect
        created = await svc.seed_beta_modules(mock_db, "comp-1")
        assert "talent_intelligence_pro" not in created

    @pytest.mark.asyncio
    async def test_update_module_partial_status(self, svc, mock_db):
        mod = _make_module(status="beta", tier="free")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        result = await svc.update_module(mock_db, "comp-1", "talent_intelligence_pro", status="active")
        assert result["success"] is True
        assert mod.status == "active"
        assert mod.tier == "free"

    @pytest.mark.asyncio
    async def test_update_module_partial_tier(self, svc, mock_db):
        mod = _make_module(status="active", tier="free")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        result = await svc.update_module(mock_db, "comp-1", "talent_intelligence_pro", tier="pro")
        assert result["success"] is True
        assert mod.status == "active"
        assert mod.tier == "pro"

    @pytest.mark.asyncio
    async def test_update_module_not_found(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)
        result = await svc.update_module(mock_db, "comp-1", "talent_intelligence_pro", status="active")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_update_module_unknown(self, svc, mock_db):
        result = await svc.update_module(mock_db, "comp-1", "nonexistent_module", status="active")
        assert result["success"] is False
        assert "Unknown module" in result["error"]

    @pytest.mark.asyncio
    async def test_get_module_by_id(self, svc, mock_db):
        mod = _make_module()
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        result = await svc.get_module_by_id(mock_db, str(mod.id))
        assert result is mod

    @pytest.mark.asyncio
    async def test_get_module_by_id_invalid_uuid(self, svc, mock_db):
        result = await svc.get_module_by_id(mock_db, "not-a-uuid")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_module_by_id_not_found(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)
        import uuid
        result = await svc.get_module_by_id(mock_db, str(uuid.uuid4()))
        assert result is None

    @pytest.mark.asyncio
    async def test_update_module_by_id(self, svc, mock_db):
        mod = _make_module(status="beta", tier="free")
        mock_db.execute.return_value = self._mock_scalar_result(mod)
        result = await svc.update_module_by_id(mock_db, str(mod.id), status="active")
        assert result["success"] is True
        assert mod.status == "active"
        assert mod.tier == "free"

    @pytest.mark.asyncio
    async def test_update_module_by_id_not_found(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)
        import uuid
        result = await svc.update_module_by_id(mock_db, str(uuid.uuid4()), status="active")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_billing_context(self, svc, mock_db):
        mod = _make_module(status="active", tier="pro")
        acct = MagicMock()
        acct.to_dict.return_value = {"company_id": "comp-1", "balance": 100}

        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = mod
            else:
                result.scalar_one_or_none.return_value = acct
            return result

        mock_db.execute.side_effect = side_effect
        ctx = await svc.get_billing_context(mock_db, "comp-1", "talent_intelligence_pro")
        assert ctx is not None
        assert ctx["is_billable"] is True
        assert ctx["credit_account"]["balance"] == 100

    @pytest.mark.asyncio
    async def test_get_billing_context_not_found(self, svc, mock_db):
        mock_db.execute.return_value = self._mock_scalar_result(None)
        ctx = await svc.get_billing_context(mock_db, "comp-1", "talent_intelligence_pro")
        assert ctx is None
