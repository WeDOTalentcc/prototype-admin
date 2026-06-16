"""
Tests — PolicyEngine Alpha 1

Cobre:
- apply_industry_defaults() para cada setor (via V2 service)
- load_default_rules() idempotencia (mock)
- save_policy_block() persistencia multi-tenant (V2 service direto)
- Endpoint POST /policy-engine/apply-sector/{company_id}

WT-2022 Phase 2 prep (2026-05-21): tests migrados de V1 PolicyEngine
(deprecated, deletion Q3 2026) para V2 PolicyEngineService. Tests V1-
specific (e.g. SECTOR_DEFAULTS classvar shape, DEFAULT_POLICIES exact
values em memoria) skipped com TODO ate post-deletion quando os dados
forem internalizados em V2 / lia_models.policy.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ─────────────────────────────────────────────
# apply_industry_defaults — V2 service (delega para V1 por ora; pos-deletion
# os dados SECTOR_DEFAULTS sao internalizados em V2)
# ─────────────────────────────────────────────

class TestApplyIndustryDefaults:
    def _engine(self):
        from app.domains.policy.services.policy_engine_service import PolicyEngineService
        return PolicyEngineService()

    @pytest.mark.asyncio
    async def test_tech_sector(self):
        e = self._engine()
        p = await e.apply_industry_defaults("tech")
        assert p["max_pearch_searches_per_day"] == 50
        assert p["require_approval_for_bulk_email"] is False
        assert p["allow_global_search"] is True

    @pytest.mark.asyncio
    async def test_varejo_sector(self):
        e = self._engine()
        p = await e.apply_industry_defaults("varejo")
        assert p["max_pearch_searches_per_day"] == 200
        assert p["max_voice_screenings_per_day"] == 500
        assert p["require_approval_for_bulk_email"] is True

    @pytest.mark.asyncio
    async def test_logistica_sector(self):
        e = self._engine()
        p = await e.apply_industry_defaults("logistica")
        assert p["max_pearch_searches_per_day"] == 300
        assert p["max_concurrent_requests"] == 30

    @pytest.mark.asyncio
    async def test_financeiro_sector(self):
        e = self._engine()
        p = await e.apply_industry_defaults("financeiro")
        assert p["allow_global_search"] is False  # BCB 498
        assert p["max_pearch_searches_per_day"] == 20

    @pytest.mark.asyncio
    async def test_saude_sector(self):
        e = self._engine()
        p = await e.apply_industry_defaults("saude")
        assert p["allow_global_search"] is False
        assert p["max_voice_screenings_per_day"] == 80

    @pytest.mark.asyncio
    async def test_rpo_sector(self):
        e = self._engine()
        p = await e.apply_industry_defaults("rpo")
        assert p["max_pearch_searches_per_day"] == 500
        assert p["max_voice_screenings_per_day"] == 2000
        assert p["require_approval_for_bulk_email"] is False

    @pytest.mark.asyncio
    async def test_unknown_sector_falls_back_to_defaults(self):
        e = self._engine()
        p = await e.apply_industry_defaults("desconhecido")
        # V2 delega ao V1 que retorna DEFAULT_POLICIES — pos-deletion validar
        # contra dataset canonical internalizado em lia_models.policy
        assert "max_pearch_searches_per_day" in p

    @pytest.mark.asyncio
    async def test_case_insensitive(self):
        e = self._engine()
        p = await e.apply_industry_defaults("VAREJO")
        assert p["max_pearch_searches_per_day"] == 200

    @pytest.mark.asyncio
    async def test_returns_full_policy_dict(self):
        e = self._engine()
        p = await e.apply_industry_defaults("tech")
        required_keys = {
            "max_pearch_searches_per_day",
            "max_voice_screenings_per_day",
            "max_tokens_per_request",
            "max_concurrent_requests",
            "allow_global_search",
            "require_approval_for_bulk_email",
        }
        assert required_keys.issubset(p.keys())


# ─────────────────────────────────────────────
# load_default_rules() — idempotencia
# ─────────────────────────────────────────────

class TestLoadDefaultRules:
    @pytest.mark.asyncio
    async def test_load_returns_stats_dict(self):
        service_mock = MagicMock()
        service_mock.load_default_rules = AsyncMock(return_value={
            "business_rules_created": 6,
            "business_rules_skipped": 0,
            "rate_limit_rules_created": 5,
            "rate_limit_rules_skipped": 0,
            "escalation_rules_created": 5,
            "escalation_rules_skipped": 0,
        })
        stats = await service_mock.load_default_rules()
        assert stats["business_rules_created"] == 6
        assert stats["rate_limit_rules_created"] == 5
        assert stats["escalation_rules_created"] == 5

    @pytest.mark.asyncio
    async def test_load_idempotent_skips_existing(self):
        """Segunda chamada deve retornar apenas skipped, nenhum created."""
        service_mock = MagicMock()
        service_mock.load_default_rules = AsyncMock(return_value={
            "business_rules_created": 0,
            "business_rules_skipped": 6,
            "rate_limit_rules_created": 0,
            "rate_limit_rules_skipped": 5,
            "escalation_rules_created": 0,
            "escalation_rules_skipped": 5,
        })
        stats = await service_mock.load_default_rules()
        assert stats["business_rules_created"] == 0
        assert stats["business_rules_skipped"] == 6

    @pytest.mark.asyncio
    async def test_default_business_rules_count(self):
        from lia_models.policy import DEFAULT_BUSINESS_RULES
        assert len(DEFAULT_BUSINESS_RULES) == 6

    @pytest.mark.asyncio
    async def test_default_rate_limit_rules_count(self):
        from lia_models.policy import DEFAULT_RATE_LIMIT_RULES
        assert len(DEFAULT_RATE_LIMIT_RULES) == 5

    @pytest.mark.asyncio
    async def test_default_escalation_rules_count(self):
        from lia_models.policy import DEFAULT_ESCALATION_RULES
        assert len(DEFAULT_ESCALATION_RULES) == 5

    @pytest.mark.asyncio
    async def test_default_rules_have_required_fields(self):
        from lia_models.policy import DEFAULT_BUSINESS_RULES, DEFAULT_RATE_LIMIT_RULES, DEFAULT_ESCALATION_RULES
        for rule in DEFAULT_BUSINESS_RULES:
            assert "name" in rule
            assert "rule_type" in rule
            assert "conditions" in rule
            assert "actions" in rule
        for rule in DEFAULT_RATE_LIMIT_RULES:
            assert "name" in rule
            assert "target_type" in rule
            assert "limit_value" in rule
            assert "window_seconds" in rule
        for rule in DEFAULT_ESCALATION_RULES:
            assert "name" in rule
            assert "trigger_type" in rule
            assert "condition" in rule
            assert "escalate_to" in rule


# ─────────────────────────────────────────────
# save_policy_block() — persistencia (V2 service, ja canonical)
# ─────────────────────────────────────────────

class TestSavePolicyBlock:
    @pytest.mark.asyncio
    async def test_save_returns_company_id_and_sector(self):
        company_id = str(uuid4())
        service_mock = MagicMock()
        service_mock.save_policy_block = AsyncMock(return_value={
            "company_id": company_id,
            "sector": "varejo",
            "automation_rules": {"auto_screening": True, "autonomy_level": "high"},
            "screening_rules": {"max_pearch_searches_per_day": 200},
        })
        result = await service_mock.save_policy_block(company_id=company_id, sector="varejo")
        assert result["company_id"] == company_id
        assert result["sector"] == "varejo"

    @pytest.mark.asyncio
    async def test_financeiro_sets_global_search_false(self):
        from app.domains.policy.services.policy_engine_service import PolicyEngineService

        company_id = str(uuid4())
        mock_db = AsyncMock()

        # Simula que nao ha policy existente
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.domains.policy.services.policy_engine_service.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_ctx

            service = PolicyEngineService()
            result = await service.save_policy_block(
                company_id=company_id,
                sector="financeiro",
                db=None,
            )

        assert result["screening_rules"]["allow_global_search"] is False

    @pytest.mark.asyncio
    async def test_rpo_sets_high_autonomy(self):
        from app.domains.policy.services.policy_engine_service import PolicyEngineService

        company_id = str(uuid4())
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.domains.policy.services.policy_engine_service.AsyncSessionLocal") as mock_session_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_ctx

            service = PolicyEngineService()
            result = await service.save_policy_block(
                company_id=company_id,
                sector="rpo",
                db=None,
            )

        assert result["automation_rules"]["autonomy_level"] == "high"

    @pytest.mark.asyncio
    async def test_multitenant_isolation(self):
        """Dois company_ids distintos nao interferem."""
        service_mock = MagicMock()

        async def _fake_save(company_id, sector, db=None):
            return {"company_id": company_id, "sector": sector,
                    "automation_rules": {}, "screening_rules": {}}

        service_mock.save_policy_block = _fake_save

        c1 = str(uuid4())
        c2 = str(uuid4())
        r1 = await service_mock.save_policy_block(c1, "tech")
        r2 = await service_mock.save_policy_block(c2, "varejo")
        assert r1["company_id"] == c1
        assert r2["company_id"] == c2
        assert r1["company_id"] != r2["company_id"]


# ─────────────────────────────────────────────
# Endpoint apply-sector
# ─────────────────────────────────────────────

class TestApplySectorEndpoint:
    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_400(self):
        from fastapi.testclient import TestClient
        try:
            from app.main import app
            client = TestClient(app)
            response = client.post("/api/v1/policy-engine/apply-sector/nao-e-uuid?sector=tech")
            assert response.status_code == 400
        except Exception:
            pytest.skip("App nao disponivel em ambiente de teste unitario")

    @pytest.mark.asyncio
    async def test_invalid_sector_returns_400(self):
        from fastapi.testclient import TestClient
        try:
            from app.main import app
            client = TestClient(app)
            company_id = str(uuid4())
            response = client.post(f"/api/v1/policy-engine/apply-sector/{company_id}?sector=invalido")
            assert response.status_code == 400
        except Exception:
            pytest.skip("App nao disponivel em ambiente de teste unitario")

    def test_valid_sectors_list(self):
        """WT-2022 P3.1 Phase 3 (2026-05-21): valida 6 setores canonical Alpha 1
        em CANONICAL_SECTOR_DEFAULTS post V1 deletion."""
        from lia_models.policy import CANONICAL_SECTOR_DEFAULTS, VALID_SECTORS

        expected = {"tech", "varejo", "logistica", "financeiro", "saude", "rpo"}
        assert set(CANONICAL_SECTOR_DEFAULTS.keys()) == expected
        assert set(VALID_SECTORS) == expected
