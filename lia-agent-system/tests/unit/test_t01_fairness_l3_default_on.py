"""T-01: FairnessGuard L3 default ON cross-sector (V3 D1 + ADR-031-v3).

Testes canonical para garantir que L3 LLM semantic check dispara em:
- Setor desconhecido (default safe)
- Varejo (D1: subido de OFF para ON)
- Logistica (D1: subido de OFF para ON)

Compliance: LGPD Art. 6/11 + EU AI Act Annex III item 4 (high-risk recruitment).
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch


class TestT01FairnessL3DefaultOn:
    """Validates L3 LLM semantic check fires for unknown sectors + varejo + logistica."""

    @pytest.mark.asyncio
    async def test_unknown_sector_triggers_l3(self):
        """Setor desconhecido (e.g. construcao, agricultura, governo, ONG) DEVE disparar L3.

        ADR-031-v3: default safe = L3 ON para setor nao mapeado em ALPHA1_SECTOR_RULES.
        """
        from app.shared.compliance.fairness_guard import FairnessGuard

        fg = FairnessGuard()
        with patch.object(fg, "check_with_layer3", new=AsyncMock()) as mock_l3:
            mock_l3.return_value = type(
                "R",
                (),
                {
                    "is_blocked": False,
                    "blocked_terms": [],
                    "category": None,
                    "educational_message": "",
                    "original_query": "test query",
                    "confidence": 0.9,
                    "soft_warnings": [],
                },
            )()
            await fg.check_with_sector(
                text="Buscamos pessoa jovem dinamica para vaga",
                sector="construcao",  # setor desconhecido
                action_type="ranking_output",
            )
            assert mock_l3.called, "L3 LLM semantic check DEVE disparar para setor desconhecido"

    @pytest.mark.asyncio
    async def test_varejo_triggers_l3(self):
        """Varejo DEVE disparar L3 (D1 consistencia compliance cross-sector)."""
        from app.shared.compliance.fairness_guard import FairnessGuard

        fg = FairnessGuard()
        with patch.object(fg, "check_with_layer3", new=AsyncMock()) as mock_l3:
            mock_l3.return_value = type(
                "R",
                (),
                {
                    "is_blocked": False,
                    "blocked_terms": [],
                    "category": None,
                    "educational_message": "",
                    "original_query": "test query",
                    "confidence": 0.9,
                    "soft_warnings": [],
                },
            )()
            await fg.check_with_sector(
                text="Vendedor para loja com habilidade comunicativa",
                sector="varejo",
                action_type="ranking_output",
            )
            assert mock_l3.called, "L3 DEVE disparar em varejo (D1 ADR-031-v3)"

    @pytest.mark.asyncio
    async def test_logistica_triggers_l3(self):
        """Logistica DEVE disparar L3 (D1 consistencia compliance cross-sector)."""
        from app.shared.compliance.fairness_guard import FairnessGuard

        fg = FairnessGuard()
        with patch.object(fg, "check_with_layer3", new=AsyncMock()) as mock_l3:
            mock_l3.return_value = type(
                "R",
                (),
                {
                    "is_blocked": False,
                    "blocked_terms": [],
                    "category": None,
                    "educational_message": "",
                    "original_query": "test query",
                    "confidence": 0.9,
                    "soft_warnings": [],
                },
            )()
            await fg.check_with_sector(
                text="Operador masculino para deposito",
                sector="logistica",
                action_type="ranking_output",
            )
            assert mock_l3.called, "L3 DEVE disparar em logistica (D1 ADR-031-v3)"
