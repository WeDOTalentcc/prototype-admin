"""F5: AutomationScheduler._is_digest_due respeita briefing_frequency do usuário.

Testa:
- daily/twice_daily → sempre True
- weekly → True só na segunda-feira (weekday==0)
- monthly → True só no dia 1
- frequência desconhecida → True (fail-open)
"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock


# Importa somente o método estático — não instancia o scheduler inteiro
def _is_due(frequency: str, fake_now: datetime) -> bool:
    """Helper: patcha datetime.now(UTC) e chama _is_digest_due."""
    from app.domains.automation.services.automation_scheduler import AutomationScheduler

    with patch(
        "app.domains.automation.services.automation_scheduler.datetime"
    ) as mock_dt:
        mock_dt.now.return_value = fake_now
        # Precisamos que UTC seja resolvível
        mock_dt.now.side_effect = lambda tz=None: fake_now
        return AutomationScheduler._is_digest_due(frequency)


class TestIsDigestDue(unittest.TestCase):
    # Datas de referência (UTC)
    MONDAY = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)    # weekday=0
    TUESDAY = datetime(2026, 6, 16, 8, 0, tzinfo=timezone.utc)   # weekday=1
    WEDNESDAY = datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc) # weekday=2
    DAY_1 = datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc)      # dia 1
    DAY_15 = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)    # dia 15

    # --- daily / twice_daily ---

    def test_daily_always_true_monday(self):
        assert _is_due("daily", self.MONDAY) is True

    def test_daily_always_true_tuesday(self):
        assert _is_due("daily", self.TUESDAY) is True

    def test_twice_daily_always_true(self):
        assert _is_due("twice_daily", self.WEDNESDAY) is True

    # --- weekly ---

    def test_weekly_true_on_monday(self):
        assert _is_due("weekly", self.MONDAY) is True

    def test_weekly_false_on_tuesday(self):
        assert _is_due("weekly", self.TUESDAY) is False

    def test_weekly_false_on_wednesday(self):
        assert _is_due("weekly", self.WEDNESDAY) is False

    # --- monthly ---

    def test_monthly_true_on_day_1(self):
        assert _is_due("monthly", self.DAY_1) is True

    def test_monthly_false_on_day_15(self):
        assert _is_due("monthly", self.DAY_15) is False

    # --- unknown / fallback ---

    def test_unknown_frequency_fail_open(self):
        assert _is_due("biweekly", self.TUESDAY) is True

    def test_empty_frequency_fail_open(self):
        assert _is_due("", self.TUESDAY) is True


if __name__ == "__main__":
    unittest.main()
