"""Testes W2-E: CalibrationFeedback Redis persistence.

Cobertura:
- persistence: feedback gravado em Redis (hset key + expire)
- read-through: get_calibration_adjustment lê Redis se in-memory vazio (simula restart)
- warm cache: após leitura Redis, in-memory é populado
- fail-open write: Redis unavailable → in-memory funciona normalmente, sem raise
- fail-open read: Redis unavailable → fallback in-memory sem raise
- version persistence: get_calibration_version lê Redis
- TTL: expire chamado com _CALIBRATION_REDIS_TTL
"""

import sys, os, unittest
from unittest.mock import MagicMock, patch, call
from io import StringIO

sys.path.insert(0, "/home/runner/workspace/lia-agent-system")

from app.domains.cv_screening.services.rubric_evaluation_service import (
    CalibrationFeedback,
    _CALIBRATION_REDIS_TTL,
)


def _make_feedback():
    """Instância limpa de CalibrationFeedback para cada teste."""
    fb = CalibrationFeedback()
    fb._redis_client = None
    fb._calibration_adjustments = {}
    fb._feedback_log = []
    return fb


class TestCalibrationRedisW2E(unittest.TestCase):
    # ── 1. TTL constant ─────────────────────────────────────────────────────

    def test_calibration_redis_ttl_is_30_days(self):
        self.assertEqual(_CALIBRATION_REDIS_TTL, 30 * 24 * 3600)

    # ── 2. Persistência na escrita ───────────────────────────────────────────

    def test_update_writes_to_redis(self):
        fb = _make_feedback()
        mock_r = MagicMock()
        with patch.object(fb, "_get_redis", return_value=mock_r):
            fb._update_calibration_adjustments("job-001", 3.0, 4.0)

        mock_r.hset.assert_called_once()
        key_used = mock_r.hset.call_args[0][0]
        self.assertEqual(key_used, "calibration_adjustment:job-001")
        mapping = mock_r.hset.call_args[1]["mapping"]
        self.assertIn("avg", mapping)
        self.assertAlmostEqual(float(mapping["avg"]), 1.0)

    def test_update_sets_expire_with_correct_ttl(self):
        fb = _make_feedback()
        mock_r = MagicMock()
        with patch.object(fb, "_get_redis", return_value=mock_r):
            fb._update_calibration_adjustments("job-002", 2.0, 3.5)

        mock_r.expire.assert_called_once_with(
            "calibration_adjustment:job-002", _CALIBRATION_REDIS_TTL
        )

    # ── 3. Leitura Redis-first após "restart" ────────────────────────────────

    def test_get_adjustment_reads_redis_when_in_memory_empty(self):
        fb = _make_feedback()
        mock_r = MagicMock()
        mock_r.hgetall.return_value = {"avg": "0.8", "sum": "1.6", "count": "2", "version": "2"}
        with patch.object(fb, "_get_redis", return_value=mock_r):
            result = fb.get_calibration_adjustment("job-003")
        self.assertAlmostEqual(result, 0.8)
        mock_r.hgetall.assert_called_once_with("calibration_adjustment:job-003")

    def test_get_adjustment_warms_in_memory_cache_from_redis(self):
        fb = _make_feedback()
        mock_r = MagicMock()
        mock_r.hgetall.return_value = {"avg": "1.5", "sum": "3.0", "count": "2", "version": "2"}
        with patch.object(fb, "_get_redis", return_value=mock_r):
            fb.get_calibration_adjustment("job-004")
        # in-memory deve estar populado agora
        self.assertIn("job:job-004", fb._calibration_adjustments)
        self.assertAlmostEqual(fb._calibration_adjustments["job:job-004"]["avg"], 1.5)

    # ── 4. Version lê Redis ──────────────────────────────────────────────────

    def test_get_version_reads_redis(self):
        fb = _make_feedback()
        mock_r = MagicMock()
        mock_r.hget.return_value = "5"
        with patch.object(fb, "_get_redis", return_value=mock_r):
            v = fb.get_calibration_version("job-005")
        self.assertEqual(v, 5)
        mock_r.hget.assert_called_once_with("calibration_adjustment:job-005", "version")

    def test_get_version_fallback_in_memory(self):
        fb = _make_feedback()
        fb._calibration_adjustments["job:job-006"] = {"sum": 1.0, "count": 1, "avg": 1.0, "version": 3}
        with patch.object(fb, "_get_redis", return_value=None):
            v = fb.get_calibration_version("job-006")
        self.assertEqual(v, 3)

    # ── 5. Fail-open escrita (Redis fora) ────────────────────────────────────

    def test_update_fail_open_when_redis_unavailable(self):
        fb = _make_feedback()
        mock_r = MagicMock()
        mock_r.hset.side_effect = Exception("connection refused")
        with patch.object(fb, "_get_redis", return_value=mock_r):
            # Não deve levantar exceção
            fb._update_calibration_adjustments("job-007", 2.0, 3.0)
        # in-memory deve estar atualizado mesmo com Redis falhando
        self.assertAlmostEqual(
            fb._calibration_adjustments["job:job-007"]["avg"], 1.0
        )

    def test_update_fail_open_when_redis_is_none(self):
        fb = _make_feedback()
        with patch.object(fb, "_get_redis", return_value=None):
            fb._update_calibration_adjustments("job-008", 3.0, 4.5)
        self.assertAlmostEqual(
            fb._calibration_adjustments["job:job-008"]["avg"], 1.5
        )

    # ── 6. Fail-open leitura (Redis fora) ────────────────────────────────────

    def test_get_adjustment_fail_open_redis_exception(self):
        fb = _make_feedback()
        fb._calibration_adjustments["job:job-009"] = {"sum": 2.0, "count": 2, "avg": 1.0, "version": 2}
        mock_r = MagicMock()
        mock_r.hgetall.side_effect = Exception("timeout")
        with patch.object(fb, "_get_redis", return_value=mock_r):
            result = fb.get_calibration_adjustment("job-009")
        # deve retornar o valor in-memory mesmo com Redis falhando
        self.assertAlmostEqual(result, 1.0)

    def test_get_adjustment_returns_zero_when_no_data(self):
        fb = _make_feedback()
        mock_r = MagicMock()
        mock_r.hgetall.return_value = {}  # chave ausente no Redis
        with patch.object(fb, "_get_redis", return_value=mock_r):
            result = fb.get_calibration_adjustment("job-010-no-data")
        self.assertEqual(result, 0.0)

    # ── 7. Acumulação correta de ajustes via record_feedback (integração) ─────

    def test_record_feedback_persists_running_average(self):
        fb = _make_feedback()
        mock_r = MagicMock()
        with patch.object(fb, "_get_redis", return_value=mock_r):
            fb.record_feedback("ev1", "cand1", "job-int", 3.0, 4.0, "approved")
            fb.record_feedback("ev2", "cand2", "job-int", 3.0, 3.5, "approved")
        # Redis chamado 2 vezes (uma por record)
        self.assertEqual(mock_r.hset.call_count, 2)
        # avg deve ser (1.0 + 0.5) / 2 = 0.75
        last_mapping = mock_r.hset.call_args[1]["mapping"]
        self.assertAlmostEqual(float(last_mapping["avg"]), 0.75, places=5)
        self.assertEqual(int(float(last_mapping["count"])), 2)
        self.assertEqual(int(float(last_mapping["version"])), 2)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.TestLoader().loadTestsFromTestCase(TestCalibrationRedisW2E))
    sys.exit(0 if result.wasSuccessful() else 1)
