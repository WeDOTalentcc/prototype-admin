"""
Sprint 3.1 — Unit tests para job_creation domain nodes.

ONDE COLOCAR: lia-agent-system/tests/domains/job_creation/test_nodes.py
Rodar: pytest tests/domains/job_creation/ -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# --- Fixtures ---

@pytest.fixture
def base_state():
    """Base wizard state for testing."""
    return {
        "company_id": 1,
        "auth_token": "test-token",
        "session_id": "sess-123",
        "ws_send": AsyncMock(),
        "api_client": AsyncMock(),
        "jd_enriched": {
            "titulo_padronizado": "Product Manager Senior",
            "senioridade_confirmada": "Senior",
            "about_role": "Responsavel por product strategy",
            "skills_obrigatorias": [
                {"skill": "Product Strategy", "contexto": "B2B SaaS"},
                {"skill": "Data Analysis", "contexto": "SQL + dashboards"},
            ],
            "competencias_comportamentais": [
                {"competencia": "Lideranca", "contexto": "Cross-functional", "trait_big_five": "extraversion"},
            ],
            "fairness_corrections": [],
        },
        "approved_questions": [
            {"question": "Descreva uma experiencia...", "skill": "Product Strategy", "block": "technical", "framework": "CBI", "weight": 0.15},
        ],
        "eligibility_questions": [
            {"question": "Tem experiencia com B2B?", "required_answer": "yes", "eliminatory": True},
        ],
        "seniority": "senior",
        "screening_mode": "compact",
        "platforms": ["linkedin", "website"],
        "auto_screen": True,
        "salary_min": 15000,
        "salary_max": 25000,
        "quality_score": 78,
        "jd_approved": True,
        "questions_approved": True,
    }


# --- Publish Node Tests ---

class TestPublishNode:
    """Tests for publish_node Rails integration."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_publish_creates_job_in_rails(self, mock_client_cls, base_state):
        """publish_node deve criar job no Rails via POST /v1/users/jobs."""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"data": {"id": 42}},
            raise_for_status=MagicMock(),
        )
        mock_client_cls.return_value = mock_client

        from wizard_wsi_patches.sprint_1a import publish_node_rails_integration as mod
        result = await mod.publish_node(base_state, {})

        assert result.get("job_id") == 42
        assert result.get("published") is True

    @pytest.mark.asyncio
    async def test_publish_sends_ws_progress(self, base_state):
        """publish_node deve enviar mensagens WS de progresso."""
        ws_send = base_state["ws_send"]

        # Mock Rails calls
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post.return_value = MagicMock(
                status_code=201,
                json=lambda: {"data": {"id": 1}},
                raise_for_status=MagicMock(),
            )
            mock_cls.return_value = mock_client

            from wizard_wsi_patches.sprint_1a import publish_node_rails_integration as mod
            await mod.publish_node(base_state, {})

        # Should have sent multiple progress messages
        assert ws_send.call_count >= 3
        first_call = ws_send.call_args_list[0][0][0]
        assert first_call["type"] == "wizard_stage"
        assert "Criando vaga" in first_call["data"]["progress"]

    @pytest.mark.asyncio
    async def test_publish_generates_share_link(self, base_state):
        """publish_node deve gerar share_link após publicar."""
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post.return_value = MagicMock(
                status_code=201,
                json=lambda: {"data": {"id": 99}},
                raise_for_status=MagicMock(),
            )
            mock_cls.return_value = mock_client

            from wizard_wsi_patches.sprint_1a import publish_node_rails_integration as mod
            result = await mod.publish_node(base_state, {})

        assert result.get("share_link") is not None
        assert "99" in result["share_link"]

    @pytest.mark.asyncio
    async def test_publish_handles_rails_failure(self, base_state):
        """publish_node deve tratar erro do Rails gracefully."""
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post.side_effect = Exception("Connection refused")
            mock_cls.return_value = mock_client

            from wizard_wsi_patches.sprint_1a import publish_node_rails_integration as mod
            result = await mod.publish_node(base_state, {})

        assert "error" in result
        assert result.get("job_id") is None


# --- Review Node Tests ---

class TestReviewNode:
    """Tests for review_node defaults application."""

    @pytest.mark.asyncio
    async def test_review_applies_defaults(self, base_state):
        """review_node deve aplicar company defaults nos campos."""
        base_state["screening_mode"] = None  # Not set yet
        base_state["platforms"] = None
        base_state["api_client"].get_company_defaults.return_value = {
            "screening_mode": "full",
            "publish_platforms": ["linkedin", "indeed"],
            "auto_screen": True,
        }

        from wizard_wsi_patches.sprint_1a import review_node_apply_defaults as mod
        result = await mod.review_node(base_state, {})

        assert result["screening_mode"] == "full"
        assert result["platforms"] == ["linkedin", "indeed"]
        assert "screening_mode" in result["defaults_applied"]

    @pytest.mark.asyncio
    async def test_review_does_not_override_existing(self, base_state):
        """review_node NAO deve sobrescrever valores já definidos."""
        base_state["screening_mode"] = "compact"
        base_state["api_client"].get_company_defaults.return_value = {
            "screening_mode": "full",
        }

        from wizard_wsi_patches.sprint_1a import review_node_apply_defaults as mod
        result = await mod.review_node(base_state, {})

        assert result["screening_mode"] == "compact"  # Kept original

    @pytest.mark.asyncio
    async def test_review_readiness_checks(self, base_state):
        """review_node deve calcular readiness corretamente."""
        from wizard_wsi_patches.sprint_1a import review_node_apply_defaults as mod
        result = await mod.review_node(base_state, {})

        readiness = result["readiness"]
        assert readiness["checks"]["jd_approved"] is True
        assert readiness["checks"]["has_questions"] is True
        assert readiness["ready"] is True

    @pytest.mark.asyncio
    async def test_review_not_ready_missing_questions(self, base_state):
        """review_node deve marcar not ready se sem perguntas."""
        base_state["approved_questions"] = []

        from wizard_wsi_patches.sprint_1a import review_node_apply_defaults as mod
        result = await mod.review_node(base_state, {})

        assert result["readiness"]["ready"] is False
        assert "has_questions" in result["readiness"]["missing"]


# --- Dedup Tests ---

class TestDeduplication:
    """Tests for skill deduplication."""

    def test_dedup_removes_duplicates(self):
        from wizard_wsi_patches.sprint_2b.dedup_embedding_patch import deduplicate_skills_by_similarity

        skills = [
            {"skill": "Python"},
            {"skill": "python"},  # duplicate (case)
            {"skill": "JavaScript"},
            {"skill": "React"},
        ]
        result = deduplicate_skills_by_similarity(skills, threshold=0.85)
        assert len(result) == 3

    def test_dedup_keeps_unique(self):
        from wizard_wsi_patches.sprint_2b.dedup_embedding_patch import deduplicate_skills_by_similarity

        skills = [
            {"skill": "Python"},
            {"skill": "JavaScript"},
            {"skill": "Go"},
        ]
        result = deduplicate_skills_by_similarity(skills, threshold=0.85)
        assert len(result) == 3

    def test_dedup_empty_list(self):
        from wizard_wsi_patches.sprint_2b.dedup_embedding_patch import deduplicate_skills_by_similarity

        result = deduplicate_skills_by_similarity([], threshold=0.85)
        assert result == []
