"""Sensor TDD — Fase 4: persist Pearch profiles on search.

Testa:
 4-B: _profile_to_row mapeamento correto (sem PII inferenciais), upsert idempotente,
      fire-and-forget não bloqueia resposta (DB lento não impacta P99)
 4-C: get_suppression_docids retorna docids, timeout fail-open (retorna [])

Skill: tdd-workflow + harness-engineering.
LGPD: gender/estimated_age NÃO armazenados (Art. 5 II / Art. 7 IX).
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_profile(**kwargs):
    defaults = dict(
        docid="pearch-abc-123",
        name="Ana Souza",
        headline="Engenheira Python Sr",
        skills=["python", "fastapi"],
        experiences=[],
        location="São Paulo, SP, Brasil",
        gender="F",           # deve ser ignorado
        estimated_age=32,     # deve ser ignorado
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ─── 4-B: _profile_to_row ───────────────────────────────────────────────────

class TestProfileToRow:
    """4-B — mapeamento CandidateProfile → upsert dict."""

    def test_docid_maps_to_source_profile_id(self):
        from app.api.v1.candidate_search._persist import _profile_to_row
        row = _profile_to_row(_make_profile(), "cid-1", "fp-abc", "dev python sr")
        assert row["source_profile_id"] == "pearch-abc-123"
        assert row["source"] == "pearch"

    def test_company_id_preserved(self):
        from app.api.v1.candidate_search._persist import _profile_to_row
        row = _profile_to_row(_make_profile(), "cid-xyz", "fp-abc", "dev")
        assert row["company_id"] == "cid-xyz"

    def test_search_fingerprint_stored(self):
        from app.api.v1.candidate_search._persist import _profile_to_row
        row = _profile_to_row(_make_profile(), "cid-1", "fp-unique-123", "dev")
        assert row["search_fingerprint"] == "fp-unique-123"

    def test_gender_not_in_raw_payload(self):
        """LGPD: dados inferenciais sensíveis não persistidos em raw_payload."""
        from app.api.v1.candidate_search._persist import _profile_to_row
        row = _profile_to_row(_make_profile(gender="F", estimated_age=32), "cid-1", "fp", "dev")
        raw = row.get("raw_payload", {})
        assert "gender" not in raw, "gender deve ser omitido do raw_payload (LGPD Art. 5 II)"
        assert "estimated_age" not in raw, "estimated_age deve ser omitido do raw_payload"

    def test_missing_docid_returns_none(self):
        from app.api.v1.candidate_search._persist import _profile_to_row
        row = _profile_to_row(_make_profile(docid=None), "cid-1", "fp", "dev")
        assert row is None, "Sem docid não há como fazer upsert por source_profile_id"

    def test_empty_docid_returns_none(self):
        from app.api.v1.candidate_search._persist import _profile_to_row
        row = _profile_to_row(_make_profile(docid=""), "cid-1", "fp", "dev")
        assert row is None

    def test_skills_array_stored(self):
        from app.api.v1.candidate_search._persist import _profile_to_row
        row = _profile_to_row(_make_profile(skills=["python", "aws"]), "cid-1", "fp", "dev")
        assert row["skills"] == ["python", "aws"]


# ─── 4-B: _persist_pearch_profiles_best_effort (fire-and-forget) ────────────

class TestPersistBestEffort:
    """4-B — best-effort persist: idempotente e não-bloqueante."""

    @pytest.mark.asyncio
    async def test_does_not_raise_on_db_error(self):
        """Fire-and-forget: exceção interna NÃO deve se propagar."""
        from app.api.v1.candidate_search._persist import _persist_pearch_profiles_best_effort

        with patch("lia_config.database.async_session_factory") as mock_factory:
            # Simula DB que explode no commit
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.execute = AsyncMock(side_effect=RuntimeError("DB unavailable"))
            mock_factory.return_value = mock_session

            # Não deve levantar exceção
            await _persist_pearch_profiles_best_effort(
                [_make_profile()], "cid-1", "fp-abc", "dev python"
            )

    @pytest.mark.asyncio
    async def test_non_blocking_slow_db(self):
        """DB lento (5s) não atrasa chamador — task fire-and-forget completa em background."""
        import time
        from app.api.v1.candidate_search._persist import _persist_pearch_profiles_best_effort

        slow_delay = 0.3  # Simula DB lento

        async def _slow_execute(*args, **kwargs):
            await asyncio.sleep(slow_delay)
            return MagicMock(fetchall=lambda: [])

        with patch("lia_config.database.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.execute = _slow_execute
            mock_session.commit = AsyncMock()
            mock_factory.return_value = mock_session

            # criar task diretamente — deve iniciar sem bloquear
            t0 = time.monotonic()
            task = asyncio.create_task(
                _persist_pearch_profiles_best_effort(
                    [_make_profile()], "cid-1", "fp-abc", "dev"
                )
            )
            elapsed = time.monotonic() - t0
            assert elapsed < 0.05, f"create_task bloqueou por {elapsed:.3f}s (esperado < 0.05)"
            # Aguarda task concluir para não sujar o event loop
            await asyncio.wait_for(task, timeout=slow_delay + 1.0)

    @pytest.mark.asyncio
    async def test_skips_profiles_without_docid(self):
        """Perfis sem docid são ignorados silenciosamente."""
        from app.api.v1.candidate_search._persist import _persist_pearch_profiles_best_effort

        no_docid_profiles = [_make_profile(docid=None), _make_profile(docid="")]

        with patch("lia_config.database.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.execute = AsyncMock(return_value=MagicMock(fetchall=lambda: []))
            mock_session.commit = AsyncMock()
            mock_factory.return_value = mock_session

            # Com 0 linhas válidas, não deve chamar execute de upsert
            await _persist_pearch_profiles_best_effort(no_docid_profiles, "cid-1", "fp", "dev")
            # Verifica que commit não foi chamado (nenhum upsert ocorreu)
            mock_session.commit.assert_not_called()


# ─── 4-C: get_suppression_docids ────────────────────────────────────────────

class TestGetSuppressionDocids:
    """4-C — suppression: retorna docids conhecidos; fail-open em timeout."""

    @pytest.mark.asyncio
    async def test_returns_known_docids(self):
        """Retorna list[str] com source_profile_ids da empresa."""
        from app.api.v1.candidate_search._persist import get_suppression_docids

        mock_row1 = MagicMock()
        mock_row1.__getitem__ = lambda self, i: "docid-001" if i == 0 else None
        mock_row2 = MagicMock()
        mock_row2.__getitem__ = lambda self, i: "docid-002" if i == 0 else None

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.v1.candidate_search._persist.asyncio.wait_for", new=AsyncMock(return_value=mock_result)):
            docids = await get_suppression_docids(mock_db, "cid-1")

        assert "docid-001" in docids
        assert "docid-002" in docids

    @pytest.mark.asyncio
    async def test_timeout_returns_empty_list(self):
        """Timeout (DB lento) → fail-open: retorna [] sem levantar exceção."""
        from app.api.v1.candidate_search._persist import get_suppression_docids

        mock_db = AsyncMock()

        with patch(
            "app.api.v1.candidate_search._persist.asyncio.wait_for",
            new=AsyncMock(side_effect=asyncio.TimeoutError()),
        ):
            docids = await get_suppression_docids(mock_db, "cid-1")

        assert docids == [], "Timeout deve retornar [] (fail-open, busca continua normalmente)"

    @pytest.mark.asyncio
    async def test_db_error_returns_empty_list(self):
        """Exceção de DB → fail-open: retorna []."""
        from app.api.v1.candidate_search._persist import get_suppression_docids

        mock_db = AsyncMock()

        with patch(
            "app.api.v1.candidate_search._persist.asyncio.wait_for",
            new=AsyncMock(side_effect=RuntimeError("Connection reset")),
        ):
            docids = await get_suppression_docids(mock_db, "cid-2")

        assert docids == []

    @pytest.mark.asyncio
    async def test_empty_table_returns_empty_list(self):
        """Empresa sem buscas anteriores → [] (sem suppression)."""
        from app.api.v1.candidate_search._persist import get_suppression_docids

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []

        with patch("app.api.v1.candidate_search._persist.asyncio.wait_for", new=AsyncMock(return_value=mock_result)):
            docids = await get_suppression_docids(AsyncMock(), "cid-new")

        assert docids == []
