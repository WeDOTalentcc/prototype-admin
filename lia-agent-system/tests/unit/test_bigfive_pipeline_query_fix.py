"""Test that pipeline overview BigFive query reads from lia_opinions, not test_results."""
import inspect
import pytest


def test_pipeline_overview_bigfive_reads_from_lia_opinions():
    """The SQL for BigFive in pipeline overview must JOIN lia_opinions.behavioral_analysis."""
    from app.repositories.job_vacancies_analytics_repository import JobVacanciesAnalyticsRepository

    source = inspect.getsource(JobVacanciesAnalyticsRepository.get_pipeline_overview_enriched)

    # Must NOT join test_results for personality/big_five
    assert not (
        "personality" in source and "big_five" in source and "test_results" in source
    ), (
        "BigFive query must NOT read from test_results (WSI never writes there). "
        "It must read from lia_opinions.behavioral_analysis->>ocean_traits"
    )


def test_pipeline_overview_bigfive_select_references_ocean_traits():
    """The SELECT clause must use ocean_traits from lia_opinions for big_five_data."""
    from app.repositories.job_vacancies_analytics_repository import JobVacanciesAnalyticsRepository

    source = inspect.getsource(JobVacanciesAnalyticsRepository.get_pipeline_overview_enriched)

    # Must reference ocean_traits from lia_opinions
    assert "ocean_traits" in source, (
        "BigFive SQL must select behavioral_analysis->ocean_traits from lia_opinions"
    )
    assert "lia_opinions" in source, (
        "BigFive SQL must join lia_opinions to get ocean_traits"
    )
