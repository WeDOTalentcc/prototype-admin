"""E11 — Priority Queue por Urgência"""
import pytest


class TestPriorityCalculator:

    def test_sourcing_with_deadline_lt_7_returns_priority_1(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("sourcing", {"deadline_days": 3})
        assert priority == 1

    def test_sourcing_with_deadline_gt_7_returns_base(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("sourcing", {"deadline_days": 14})
        assert priority == 2  # base for sourcing

    def test_cv_screening_with_large_backlog_returns_2(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("cv_screening", {"backlog_size": 75})
        assert priority == 2

    def test_cv_screening_small_backlog_returns_2(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("cv_screening", {"backlog_size": 10})
        assert priority == 2  # base for cv_screening

    def test_followup_returns_3(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("followup", {})
        assert priority == 3

    def test_wsi_abandoned_returns_3(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("wsi_abandoned", {})
        assert priority == 3

    def test_unknown_task_type_returns_5(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("some_unknown_task", {})
        assert priority == 5

    def test_no_metadata_uses_defaults(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("sourcing")  # no metadata
        assert priority == 2  # base, no escalation without metadata

    def test_sourcing_deadline_exactly_7_returns_base(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("sourcing", {"deadline_days": 7})
        assert priority == 2  # 7 is NOT < 7

    def test_cv_screening_backlog_exactly_50_returns_base(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        priority = calc.compute("cv_screening", {"backlog_size": 50})
        assert priority == 2  # 50 is NOT > 50

    def test_singleton_module_level(self):
        from app.shared.async_processing.priority_calculator import priority_calculator, PriorityCalculator
        assert isinstance(priority_calculator, PriorityCalculator)

    def test_report_returns_5(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        assert calc.compute("report") == 5

    def test_analytics_returns_5(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        assert calc.compute("analytics") == 5

    def test_notification_returns_3(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        assert calc.compute("notification") == 3

    def test_invalid_metadata_value_falls_back_to_base(self):
        from app.shared.async_processing.priority_calculator import PriorityCalculator
        calc = PriorityCalculator()
        # Non-numeric deadline_days — should log warning and return base
        priority = calc.compute("sourcing", {"deadline_days": "not_a_number"})
        assert priority == 2  # base for sourcing
