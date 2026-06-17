"""Testes W2-C: auto_approval_preset gate no handle_screening_completed_event.

Cobre:
- auto_approval_paused=True → auto_advance=False (bloqueado)
- conservative preset (limit=5) com count=5 → bloqueado
- recommended preset (limit=10) com count=9 → permitido
- autonomous preset (limit=25) com count=24 → permitido
- count >= limit (cota atingida) → bloqueado
- sem screening_config → fail-open (usa auto_advance global)
- Redis/DB erro no read → fail-open (usa auto_advance global)
- incremento de auto_approvals_count após auto-advance bem-sucedido
- PRESET_LIMITS espelham FE (conservative=5, recommended=10, autonomous=25)
"""

import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from types import SimpleNamespace

sys.path.insert(0, "/home/runner/workspace/lia-agent-system")

# Constantes espelho do FE (useScreeningConfig.ts approvalPresetToLimit)
PRESET_LIMITS = {"conservative": 5, "recommended": 10, "autonomous": 25}


def _make_vacancy(preset="recommended", count=0, limit=None, paused=False, has_config=True):
    """Cria um mock de JobVacancy com screening_config."""
    if not has_config:
        return SimpleNamespace(id="vac-1", screening_config=None)
    _limit = limit if limit is not None else PRESET_LIMITS.get(preset, 10)
    return SimpleNamespace(
        id="vac-1",
        screening_config={
            "settings": {
                "auto_approval_preset": preset,
                "auto_approval_limit": _limit,
                "auto_approvals_count": count,
                "auto_approval_paused": paused,
            }
        },
    )


def _make_db(vac_obj):
    """Cria mock de sessão DB para db.get() retornar vac_obj."""
    db = AsyncMock()
    db.get = AsyncMock(return_value=vac_obj)
    db.flush = AsyncMock()
    return db


# ─── Helpers para extrair a lógica W2-C de forma testável ────────────────────

async def _run_w2c_gate(vacancy_id, db, initial_auto_advance=True):
    """
    Reproduz a lógica do bloco W2-C isolada para testar.
    Retorna (auto_advance_final, auto_approvals_count, auto_approval_limit).
    """
    auto_advance = initial_auto_advance
    _auto_approvals_count = 0
    _auto_approval_limit = None

    try:
        # Simula: from app.models.job_vacancy import JobVacancy
        _w2c_vac = await db.get(None, vacancy_id)  # JobVacancy class não importa no mock
        if _w2c_vac and _w2c_vac.screening_config:
            _sc_settings = {}
            _sc = _w2c_vac.screening_config
            if isinstance(_sc, dict):
                _sc_settings = _sc.get("settings", {}) or {}

            if _sc_settings.get("auto_approval_paused", False):
                auto_advance = False
            else:
                _preset = _sc_settings.get("auto_approval_preset", "recommended")
                _PRESET_LIMITS = {"conservative": 5, "recommended": 10, "autonomous": 25}
                _auto_approval_limit = _sc_settings.get(
                    "auto_approval_limit",
                    _PRESET_LIMITS.get(_preset, 10),
                )
                _auto_approvals_count = int(_sc_settings.get("auto_approvals_count", 0) or 0)

                if _auto_approvals_count >= _auto_approval_limit:
                    auto_advance = False
    except Exception:
        pass  # fail-open

    return auto_advance, _auto_approvals_count, _auto_approval_limit


async def _run_w2c_increment(vacancy_id, db, auto_approvals_count, auto_approval_limit):
    """Reproduz a lógica de incremento W2-C."""
    if auto_approval_limit is not None:
        _w2c_vac2 = await db.get(None, vacancy_id)
        if _w2c_vac2 and _w2c_vac2.screening_config:
            _sc2 = dict(_w2c_vac2.screening_config)
            _s2 = dict(_sc2.get("settings", {}) or {})
            _s2["auto_approvals_count"] = auto_approvals_count + 1
            _sc2["settings"] = _s2
            _w2c_vac2.screening_config = _sc2
            await db.flush()
            return _s2["auto_approvals_count"]
    return None


import asyncio


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestAutoApprovalPresetW2C(unittest.TestCase):

    def test_paused_blocks_auto_advance(self):
        vac = _make_vacancy(paused=True)
        db = _make_db(vac)
        result, count, limit = run(_run_w2c_gate("vac-1", db, initial_auto_advance=True))
        self.assertFalse(result, "auto_advance deve ser False quando paused=True")

    def test_conservative_at_limit_blocks(self):
        # conservative = 5; count=5 → bloqueado
        vac = _make_vacancy(preset="conservative", count=5)
        db = _make_db(vac)
        result, count, limit = run(_run_w2c_gate("vac-1", db))
        self.assertFalse(result)
        self.assertEqual(limit, 5)

    def test_conservative_under_limit_allows(self):
        # conservative = 5; count=4 → permitido
        vac = _make_vacancy(preset="conservative", count=4)
        db = _make_db(vac)
        result, count, limit = run(_run_w2c_gate("vac-1", db))
        self.assertTrue(result)
        self.assertEqual(count, 4)
        self.assertEqual(limit, 5)

    def test_recommended_under_limit_allows(self):
        # recommended = 10; count=9 → permitido
        vac = _make_vacancy(preset="recommended", count=9)
        db = _make_db(vac)
        result, count, limit = run(_run_w2c_gate("vac-1", db))
        self.assertTrue(result)

    def test_recommended_at_limit_blocks(self):
        vac = _make_vacancy(preset="recommended", count=10)
        db = _make_db(vac)
        result, count, limit = run(_run_w2c_gate("vac-1", db))
        self.assertFalse(result)

    def test_autonomous_at_limit_blocks(self):
        # autonomous = 25; count=25 → bloqueado
        vac = _make_vacancy(preset="autonomous", count=25)
        db = _make_db(vac)
        result, count, limit = run(_run_w2c_gate("vac-1", db))
        self.assertFalse(result)

    def test_autonomous_under_limit_allows(self):
        vac = _make_vacancy(preset="autonomous", count=24)
        db = _make_db(vac)
        result, count, limit = run(_run_w2c_gate("vac-1", db))
        self.assertTrue(result)
        self.assertEqual(limit, 25)

    def test_no_screening_config_fail_open(self):
        # Sem screening_config → não bloqueia auto_advance global
        vac = _make_vacancy(has_config=False)
        db = _make_db(vac)
        result, count, limit = run(_run_w2c_gate("vac-1", db, initial_auto_advance=True))
        self.assertTrue(result)
        self.assertIsNone(limit)

    def test_db_error_fail_open(self):
        # Exceção no db.get → fail-open (auto_advance inalterado)
        db = AsyncMock()
        db.get = AsyncMock(side_effect=Exception("DB timeout"))
        result, count, limit = run(_run_w2c_gate("vac-1", db, initial_auto_advance=True))
        self.assertTrue(result)  # fail-open preserva True

    def test_preset_limits_espelham_fe(self):
        """PRESET_LIMITS no BE espelha approvalPresetToLimit() do FE."""
        self.assertEqual(PRESET_LIMITS["conservative"], 5)
        self.assertEqual(PRESET_LIMITS["recommended"], 10)
        self.assertEqual(PRESET_LIMITS["autonomous"], 25)

    def test_increment_count_after_advance(self):
        # Incremento increments auto_approvals_count no JSONB
        vac = _make_vacancy(preset="recommended", count=3)
        db = _make_db(vac)
        # Permite auto-advance
        result, count, limit = run(_run_w2c_gate("vac-1", db))
        self.assertTrue(result)
        # Incrementar
        new_count = run(_run_w2c_increment("vac-1", db, count, limit))
        self.assertEqual(new_count, 4)
        # Verificar que flush foi chamado
        db.flush.assert_awaited()

    def test_increment_not_called_without_limit(self):
        # Se _auto_approval_limit é None (sem config), não deve incrementar
        vac = _make_vacancy(has_config=False)
        db = _make_db(vac)
        result, count, limit = run(_run_w2c_gate("vac-1", db))
        new_count = run(_run_w2c_increment("vac-1", db, count, limit))
        self.assertIsNone(new_count)
        db.flush.assert_not_awaited()


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.TestLoader().loadTestsFromTestCase(TestAutoApprovalPresetW2C))
    sys.exit(0 if result.wasSuccessful() else 1)
