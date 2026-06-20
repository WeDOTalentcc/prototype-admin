"""Task #1223 — enrich + persist primitive (JD enriquecida WSI persistida na vaga).

Cobre:
  * o helper puro ``build_wsi_persistence_payload`` (merge detectados+sugestões,
    shapes estruturados, gate de mínimos 9 técnicas + 5 comportamentais);
  * o método ``JdEnrichmentService.enrich_and_persist_vacancy`` (fail-alto,
    persistência quando atinge mínimos, NÃO persiste "no vácuo" quando não atinge).

Hermético: sem DB real nem rede. ``enrich_job_description`` e o repositório são
mockados; o gate/merge/quality rodam de verdade (não são mockados).
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.domains.job_management.services.jd_enrichment_service import (
    MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI,
    MIN_TECHNICAL_SKILLS_FOR_WSI,
    JobManagementJdEnrichmentService as JdEnrichmentService,
    build_wsi_persistence_payload,
)
from app.schemas.jd_enrichment import (
    EnrichedJobDescription,
    EnrichedSuggestion,
    EnrichmentResponse,
    SectionSuggestions,
    SuggestionSource,
)


def _suggestion(value: str) -> EnrichedSuggestion:
    return EnrichedSuggestion(
        id=f"s-{value.lower().replace(' ', '-')}",
        value=value,
        source=SuggestionSource.SKILLS_CATALOG,
        justification="teste",
    )


def _section(name: str, title: str, detected: list[str], suggestions: list[str]) -> SectionSuggestions:
    return SectionSuggestions(
        section_name=name,
        section_title=title,
        detected_items=list(detected),
        suggestions=[_suggestion(s) for s in suggestions],
    )


def _enriched(
    *,
    title: str = "Desenvolvedor Python Sênior",
    technical_detected: list[str],
    technical_sugg: list[str],
    behavioral_detected: list[str],
    behavioral_sugg: list[str],
    responsibilities_detected: list[str] | None = None,
    responsibilities_sugg: list[str] | None = None,
) -> EnrichedJobDescription:
    return EnrichedJobDescription(
        company_id="company-1",
        title=title,
        seniority="Sênior",
        responsibilities=_section(
            "responsibilities",
            "Responsabilidades",
            responsibilities_detected or [],
            responsibilities_sugg or [],
        ),
        technical_skills=_section(
            "technical_skills", "Competências Técnicas", technical_detected, technical_sugg
        ),
        behavioral_competencies=_section(
            "behavioral_competencies",
            "Competências Comportamentais",
            behavioral_detected,
            behavioral_sugg,
        ),
    )


# ───────────────────────── helper puro: merge + gate ─────────────────────────


def test_payload_merges_detected_and_suggestions_dedup_order():
    enriched = _enriched(
        technical_detected=["Python", "Django"],
        technical_sugg=["python", "Docker", "Kubernetes"],  # 'python' dup case-insensitive
        behavioral_detected=["Liderança"],
        behavioral_sugg=["Comunicação"],
    )
    payload = build_wsi_persistence_payload(enriched, original_description="vaga x")

    # dedup case-insensitive, ordem preservada (detectados primeiro)
    assert payload["technical_skills"] == ["Python", "Django", "Docker", "Kubernetes"]
    assert payload["behavioral_competencies"] == ["Liderança", "Comunicação"]


def test_payload_structured_objects_use_canonical_normalizer_shape():
    enriched = _enriched(
        technical_detected=["Python"],
        technical_sugg=[],
        behavioral_detected=["Liderança"],
        behavioral_sugg=[],
    )
    payload = build_wsi_persistence_payload(enriched)

    tech_obj = payload["technical_requirements_objects"][0]
    assert tech_obj["name"] == "Python"
    assert tech_obj["required"] is True
    assert "level" in tech_obj and "years_experience" in tech_obj

    behav_obj = payload["behavioral_competencies_objects"][0]
    assert behav_obj["name"] == "Liderança"


def test_gate_met_when_nine_technical_and_five_behavioral():
    enriched = _enriched(
        technical_detected=[f"Tech{i}" for i in range(MIN_TECHNICAL_SKILLS_FOR_WSI)],
        technical_sugg=[],
        behavioral_detected=[f"Behav{i}" for i in range(MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI)],
        behavioral_sugg=[],
    )
    payload = build_wsi_persistence_payload(enriched)
    assert payload["meets_wsi_minimums"] is True


def test_gate_not_met_when_below_minimums():
    enriched = _enriched(
        technical_detected=["Python", "Django"],
        technical_sugg=[],
        behavioral_detected=["Liderança"],
        behavioral_sugg=[],
    )
    payload = build_wsi_persistence_payload(enriched)
    assert payload["meets_wsi_minimums"] is False


def test_enriched_jd_blob_has_string_lists_for_frontend():
    enriched = _enriched(
        technical_detected=["Python"],
        technical_sugg=[],
        behavioral_detected=["Liderança"],
        behavioral_sugg=[],
    )
    blob = build_wsi_persistence_payload(enriched)["enriched_jd"]
    assert all(isinstance(x, str) for x in blob["technical_skills"])
    assert all(isinstance(x, str) for x in blob["behavioral_competencies"])
    assert isinstance(blob["generated_jd_text"], str)
    assert "updated_at" in blob


# ───────────────────────── método: enrich_and_persist ─────────────────────────


def _vacancy():
    import uuid

    return SimpleNamespace(
        id=uuid.UUID("00000000-0000-4000-a000-000000000abc"),
        company_id="company-1",
        title="Desenvolvedor Python Sênior",
        department="Engenharia",
        seniority_level="Sênior",
        location="São Paulo",
        work_model="Remoto",
        responsibilities=["Desenvolver features"],
        technical_requirements=[{"name": "Python", "required": True}],
        behavioral_competencies=[{"name": "Liderança"}],
        salary_range=None,
        description="Descrição original",
        enriched_jd=None,
        updated_at=None,
    )


def _mock_response(enriched: EnrichedJobDescription) -> EnrichmentResponse:
    return EnrichmentResponse(success=True, enriched_jd=enriched, summary_message="ok")


@pytest.mark.asyncio
async def test_persists_structured_fields_when_minimums_met():
    vacancy = _vacancy()
    enriched = _enriched(
        technical_detected=[f"Tech{i}" for i in range(MIN_TECHNICAL_SKILLS_FOR_WSI)],
        technical_sugg=[],
        behavioral_detected=[f"Behav{i}" for i in range(MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI)],
        behavioral_sugg=[],
        responsibilities_detected=["Resp A", "Resp B"],
    )
    db = AsyncMock()
    svc = JdEnrichmentService()

    with patch.object(
        svc, "enrich_job_description", AsyncMock(return_value=_mock_response(enriched))
    ), patch(
        "app.domains.job_management.repositories.job_vacancy_crud_repository.JobVacancyCRUDRepository.get_vacancy_by_id_and_company",
        AsyncMock(return_value=vacancy),
    ), patch(
        "app.domains.job_management.repositories.job_vacancy_crud_repository.JobVacancyCRUDRepository.flush_and_refresh",
        AsyncMock(side_effect=lambda obj: obj),
    ):
        result = await svc.enrich_and_persist_vacancy(str(vacancy.id), "company-1", db)

    assert result.persisted is True
    assert result.meets_wsi_minimums is True
    assert result.technical_count == MIN_TECHNICAL_SKILLS_FOR_WSI
    assert result.behavioral_count == MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI
    # colunas estruturadas gravadas no ORM
    assert isinstance(vacancy.technical_requirements, list)
    assert vacancy.technical_requirements[0]["name"] == "Tech0"
    assert vacancy.behavioral_competencies[0]["name"] == "Behav0"
    assert vacancy.responsibilities == ["Resp A", "Resp B"]
    assert vacancy.enriched_jd is not None
    assert vacancy.enriched_jd["meets_wsi_minimums"] is True
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_does_not_persist_in_vacuum_when_minimums_missing():
    vacancy = _vacancy()
    enriched = _enriched(
        technical_detected=["Python", "Django"],
        technical_sugg=[],
        behavioral_detected=["Liderança"],
        behavioral_sugg=[],
    )
    db = AsyncMock()
    svc = JdEnrichmentService()

    with patch.object(
        svc, "enrich_job_description", AsyncMock(return_value=_mock_response(enriched))
    ), patch(
        "app.domains.job_management.repositories.job_vacancy_crud_repository.JobVacancyCRUDRepository.get_vacancy_by_id_and_company",
        AsyncMock(return_value=vacancy),
    ):
        result = await svc.enrich_and_persist_vacancy(str(vacancy.id), "company-1", db)

    assert result.success is True
    assert result.persisted is False
    assert result.meets_wsi_minimums is False
    assert "faltam" in result.message.lower()
    # vaga NÃO mutada / sem commit
    assert vacancy.enriched_jd is None
    assert vacancy.description == "Descrição original"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_enrichment_failure_returns_unsuccess_no_commit():
    vacancy = _vacancy()
    db = AsyncMock()
    svc = JdEnrichmentService()
    failed = EnrichmentResponse(
        success=False, enriched_jd=None, error="LLM indisponível", summary_message="falhou"
    )

    with patch.object(
        svc, "enrich_job_description", AsyncMock(return_value=failed)
    ), patch(
        "app.domains.job_management.repositories.job_vacancy_crud_repository.JobVacancyCRUDRepository.get_vacancy_by_id_and_company",
        AsyncMock(return_value=vacancy),
    ):
        result = await svc.enrich_and_persist_vacancy(str(vacancy.id), "company-1", db)

    # sem fake success: enriquecimento falhou → success=False, nada persistido
    assert result.success is False
    assert result.persisted is False
    assert result.error == "LLM indisponível"
    assert vacancy.enriched_jd is None
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_fail_high_when_vacancy_missing():
    db = AsyncMock()
    svc = JdEnrichmentService()
    with patch(
        "app.domains.job_management.repositories.job_vacancy_crud_repository.JobVacancyCRUDRepository.get_vacancy_by_id_and_company",
        AsyncMock(return_value=None),
    ):
        with pytest.raises(ValueError, match="não encontrada"):
            await svc.enrich_and_persist_vacancy(
                "00000000-0000-4000-a000-000000000abc", "company-1", db
            )


@pytest.mark.asyncio
async def test_fail_high_on_empty_company_id():
    db = AsyncMock()
    svc = JdEnrichmentService()
    with pytest.raises(ValueError, match="company_id"):
        await svc.enrich_and_persist_vacancy("00000000-0000-4000-a000-000000000abc", "", db)


@pytest.mark.asyncio
async def test_fail_high_on_invalid_uuid():
    db = AsyncMock()
    svc = JdEnrichmentService()
    with pytest.raises(ValueError, match="UUID"):
        await svc.enrich_and_persist_vacancy("not-a-uuid", "company-1", db)
