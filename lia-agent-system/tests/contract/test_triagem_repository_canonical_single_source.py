"""
P2 D — TriagemRepository consolidation: single canonical source.

Sintoma: dois repositories coexistiam:
  1. app/domains/triagem/repositories/triagem_repository.py — stub vazio
     (apenas __init__ + self.db, zero métodos)
  2. app/domains/recruitment/repositories/triagem_session_repository.py —
     canonical real (7 métodos + usado pelo P0 fix 497e30429 + services)

Endpoint app/api/v1/triagem.py importava o stub mas só acessava `repo.db`
(nunca chamava métodos). Stub era pure dead-code disfarçado de repository.

Fix: stub deletado; dependency `get_triagem_repo` retorna `TriagemSessionRepository`
canonical. Nome legacy `TriagemRepository` mantido como alias no
`app/domains/triagem/repositories/__init__.py` para backward compat
(prevenir quebra em imports externos enquanto fazemos migração).

Contratos defendidos:
  1. `TriagemSessionRepository` é o único path canonical.
  2. Legacy alias `TriagemRepository` resolve para canonical.
  3. `get_triagem_repo` retorna instância de `TriagemSessionRepository`.
  4. Stub `app/domains/triagem/repositories/triagem_repository.py` não existe mais.
  5. Endpoint endpoints continuam funcionais (`repo.db` acessível).
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
)


class TestSingleCanonicalSource:
    """Contrato 1+4: TriagemSessionRepository é único canonical; stub não existe."""

    def test_canonical_repository_importable(self):
        assert TriagemSessionRepository is not None
        assert hasattr(TriagemSessionRepository, "get_session_by_token")

    def test_stub_file_deleted(self):
        """Stub original em domains/triagem/repositories/triagem_repository.py
        deve ter sido deletado."""
        stub_path = Path(__file__).parent.parent.parent / "app" / "domains" / "triagem" / "repositories" / "triagem_repository.py"
        assert not stub_path.exists(), (
            f"Stub file ainda existe em {stub_path}. "
            "P2 D incompleto — deletar arquivo."
        )


class TestBackwardCompatAlias:
    """Contrato 2: nome legacy `TriagemRepository` resolve para canonical."""

    def test_legacy_alias_points_to_canonical(self):
        """`from app.domains.triagem.repositories import TriagemRepository`
        deve continuar funcionando e retornar a classe canonical."""
        mod = importlib.import_module("app.domains.triagem.repositories")
        assert hasattr(mod, "TriagemRepository"), (
            "Alias `TriagemRepository` removido do __init__.py — quebra "
            "imports externos que ainda usam nome legacy."
        )
        assert mod.TriagemRepository is TriagemSessionRepository, (
            f"Alias `TriagemRepository` deveria ser {TriagemSessionRepository}, "
            f"mas é {mod.TriagemRepository}"
        )


class TestDependencyReturnsCanonical:
    """Contrato 3: `get_triagem_repo` retorna `TriagemSessionRepository`."""

    @pytest.mark.asyncio
    async def test_get_triagem_repo_returns_canonical_instance(self):
        from unittest.mock import AsyncMock

        from app.repositories.dependencies import get_triagem_repo

        mock_db = AsyncMock(spec=AsyncSession)
        repo = get_triagem_repo(db=mock_db)

        assert isinstance(repo, TriagemSessionRepository), (
            f"Esperado TriagemSessionRepository, recebeu {type(repo)}"
        )
        assert repo.db is mock_db, "repo.db deve continuar acessível (endpoint contract)"


class TestEndpointImportContract:
    """Contrato 5: endpoint continua importável (não quebra dependencies)."""

    def test_endpoint_module_imports_cleanly(self):
        # Se import quebrar, ImportError sobe aqui
        mod = importlib.import_module("app.api.v1.triagem")
        assert mod is not None
