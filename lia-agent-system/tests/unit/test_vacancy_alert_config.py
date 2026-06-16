"""Testes do model VacancyAlertConfig."""
import pytest
from libs.models.lia_models.vacancy_alert_config import VacancyAlertConfig


def test_vacancy_alert_config_fields():
    """Model deve ter todos os campos canônicos."""
    config = VacancyAlertConfig(
        company_id="co-1",
        vacancy_id="vac-1",
        recruiter_id="rec-1",
        alert_type="new_candidate",
        frequency="daily",
    )
    assert config.company_id == "co-1"
    assert config.frequency == "daily"
    assert config.alert_type == "new_candidate"


def test_frequency_values():
    """Frequências válidas são aceitas."""
    valid = {"daily", "twice_daily", "weekly", "monthly", "off"}
    for freq in valid:
        c = VacancyAlertConfig(
            company_id="co", vacancy_id="v", recruiter_id="r",
            alert_type="t", frequency=freq,
        )
        assert c.frequency == freq


def test_column_default_is_daily():
    """Coluna frequency tem default=daily no nível do DB/column."""
    col = VacancyAlertConfig.__table__.columns["frequency"]
    assert col.default.arg == "daily"


def test_table_name():
    """Tabela tem nome canônico."""
    assert VacancyAlertConfig.__tablename__ == "vacancy_alert_configs"


def test_unique_constraint_present():
    """UniqueConstraint vacancy_id+recruiter_id+alert_type existe."""
    constraints = {c.name for c in VacancyAlertConfig.__table__.constraints}
    assert "uq_vacancy_alert" in constraints
