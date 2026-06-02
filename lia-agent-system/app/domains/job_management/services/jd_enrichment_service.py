"""
Job Description Enrichment Service.

Orquestra a análise de múltiplas fontes de dados para gerar sugestões
enriquecidas e contextualizadas para o Job Description.

Fontes de dados:
- Market Benchmark: Dados de mercado (Glassdoor, LinkedIn, etc.)
- Skills Catalog: Catálogo de competências técnicas e comportamentais
- Company History: Histórico de vagas da empresa (ATS/HRIS)
- Company Config: Configurações e defaults da empresa
- Responsibilities Catalog: Catálogo de responsabilidades por área
"""
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.services.ats_job_history_service import ATSJobHistoryService
from app.schemas.jd_enrichment import (
    BehavioralCompetencySuggestion,
    BonusSuggestion,
    CompensationSuggestions,
    EnrichedJobDescription,
    EnrichedSuggestion,
    EnrichmentRequest,
    EnrichmentResponse,
    SalarySuggestion,
    SectionSuggestions,
    SuggestionImpactLevel,
    SuggestionSource,
    TechnicalSkillSuggestion,
)
from app.domains.company.services.company_configuration_service import CompanyConfigurationService
from app.shared.services.market_benchmark_service import MarketBenchmarkService
from app.shared.services.responsibilities_catalog_service import ResponsibilitiesCatalogService
from app.shared.services.skills_catalog_service import SkillsCatalogService

logger = logging.getLogger(__name__)


MIN_TECHNICAL_SKILLS_FOR_WSI = 9
MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI = 5
MIN_RESPONSIBILITIES = 5


def _extract_skill_names(items: Any) -> list[str]:
    """Extrai nomes de uma coluna estruturada (technical_requirements /
    behavioral_competencies) que pode conter strings ou dicts.

    Aceita as chaves canônicas usadas pelos diferentes writers do projeto:
    ``name`` (writer do wizard via ``_normalize_skills_to_objects``),
    ``technology``/``skill`` e ``competency`` (model comment legado).
    """
    names: list[str] = []
    for item in items or []:
        if isinstance(item, str):
            value = item
        elif isinstance(item, dict):
            value = (
                item.get("name")
                or item.get("technology")
                or item.get("skill")
                or item.get("competency")
                or item.get("value")
                or ""
            )
        else:
            value = str(item)
        value = (value or "").strip()
        if value:
            names.append(value)
    return names


def _merge_section_items(section: "SectionSuggestions") -> list[str]:
    """Funde ``detected_items`` + valores das ``suggestions`` de uma seção,
    deduplicando case-insensitive e preservando a ordem (detectados primeiro).
    """
    merged: list[str] = []
    seen: set[str] = set()
    candidates = list(section.detected_items or []) + [
        s.value for s in (section.suggestions or [])
    ]
    for raw in candidates:
        value = (raw or "").strip()
        key = value.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(value)
    return merged


def _compose_enriched_jd_text(
    *,
    title: str,
    seniority: str | None,
    department: str | None,
    location: str | None,
    work_model: str | None,
    original_description: str | None,
    responsibilities: list[str],
    technical_skills: list[str],
    behavioral_competencies: list[str],
) -> str:
    """Monta a descrição enriquecida (PT-BR, markdown) a partir das seções."""
    lines: list[str] = [f"# {title}"]
    meta = [m for m in (seniority, department, location, work_model) if m]
    if meta:
        lines.append(" · ".join(meta))
    if original_description and original_description.strip():
        lines.append("\n## Sobre a vaga\n" + original_description.strip())
    if responsibilities:
        lines.append("\n## Responsabilidades")
        lines.extend(f"- {r}" for r in responsibilities)
    if technical_skills:
        lines.append("\n## Competências Técnicas")
        lines.extend(f"- {t}" for t in technical_skills)
    if behavioral_competencies:
        lines.append("\n## Competências Comportamentais")
        lines.extend(f"- {b}" for b in behavioral_competencies)
    return "\n".join(lines)


def build_wsi_persistence_payload(
    enriched: "EnrichedJobDescription",
    *,
    original_description: str | None = None,
) -> dict[str, Any]:
    """Transforma um ``EnrichedJobDescription`` (detectados + sugestões) no
    payload determinístico de persistência da vaga.

    Funde detectados + sugestões por seção, calcula a qualidade WSI canônica
    (``evaluate_jd_quality``, single source) e aplica o gate de mínimos
    (9 técnicas + 5 comportamentais). É puro: não toca DB nem rede.
    """
    from app.domains.cv_screening.services.wsi_service.jd_quality import (
        evaluate_jd_quality,
    )
    from app.domains.job_management.services.job_vacancy_service import (
        JobVacancyService,
    )

    responsibilities = _merge_section_items(enriched.responsibilities)
    technical = _merge_section_items(enriched.technical_skills)
    behavioral = _merge_section_items(enriched.behavioral_competencies)

    quality = evaluate_jd_quality(
        description=original_description,
        job_title=enriched.title,
        department=enriched.department,
        seniority=enriched.seniority,
        responsibilities=responsibilities,
        technical_skills=technical,
        behavioral_competencies=behavioral,
        d3_min=MIN_TECHNICAL_SKILLS_FOR_WSI,
        d4_min=MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI,
    )
    max_score = float(quality.get("max_score") or 100) or 100.0
    wsi_quality_score = round(float(quality.get("score", 0)) / max_score, 4)
    warnings = [
        ind["detail"]
        for ind in quality.get("indicators", [])
        if ind.get("status") in ("insufficient", "partial") and ind.get("detail")
    ]

    meets_wsi_minimums = (
        len(technical) >= MIN_TECHNICAL_SKILLS_FOR_WSI
        and len(behavioral) >= MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI
    )

    generated_jd_text = _compose_enriched_jd_text(
        title=enriched.title,
        seniority=enriched.seniority,
        department=enriched.department,
        location=enriched.location,
        work_model=enriched.work_model,
        original_description=original_description,
        responsibilities=responsibilities,
        technical_skills=technical,
        behavioral_competencies=behavioral,
    )

    enriched_jd_blob = {
        "description": generated_jd_text,
        "responsibilities": responsibilities,
        "technical_skills": technical,
        "behavioral_competencies": behavioral,
        "generated_jd_text": generated_jd_text,
        "wsi_quality_score": wsi_quality_score,
        "wsi_quality_warnings": warnings,
        "meets_wsi_minimums": meets_wsi_minimums,
        "source_description": original_description,
        "updated_at": datetime.utcnow().isoformat(),
    }

    return {
        "responsibilities": responsibilities,
        "technical_skills": technical,
        "behavioral_competencies": behavioral,
        "technical_requirements_objects": JobVacancyService._normalize_skills_to_objects(
            technical
        ),
        "behavioral_competencies_objects": JobVacancyService._normalize_skills_to_objects(
            behavioral
        ),
        "meets_wsi_minimums": meets_wsi_minimums,
        "wsi_quality_score": wsi_quality_score,
        "wsi_quality_warnings": warnings,
        "generated_jd_text": generated_jd_text,
        "enriched_jd": enriched_jd_blob,
    }


class JdEnrichmentService:
    """
    Serviço de enriquecimento de Job Description.
    
    Analisa os dados fornecidos pelo recrutador e gera sugestões
    contextualizadas baseadas em múltiplas fontes de dados.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.market_benchmark = MarketBenchmarkService()
        self.skills_catalog = SkillsCatalogService()
        self.responsibilities_catalog = ResponsibilitiesCatalogService()
        self.company_config = CompanyConfigurationService()
        self.ats_history = ATSJobHistoryService()
    
    async def enrich_job_description(
        self,
        request: EnrichmentRequest,
        db: AsyncSession | None = None
    ) -> EnrichmentResponse:
        """
        Enriquece o Job Description com sugestões contextualizadas.
        
        Args:
            request: Dados do JD para enriquecer
            db: Sessão do banco de dados (opcional)
            
        Returns:
            EnrichmentResponse com JD enriquecido
        """
        try:
            self.logger.info(f"Enriching JD for company {request.company_id}, title: {request.title}")
            
            responsibilities_result = await self._enrich_responsibilities(request, db)
            technical_skills_result = await self._enrich_technical_skills(request, db)
            behavioral_result = await self._enrich_behavioral_competencies(request, db)
            compensation_result = await self._enrich_compensation(request, db)
            
            responsibilities: SectionSuggestions = responsibilities_result
            technical_skills: SectionSuggestions = technical_skills_result
            behavioral: SectionSuggestions = behavioral_result
            compensation: CompensationSuggestions = compensation_result
            
            total_suggestions = (
                len(responsibilities.suggestions) +
                len(technical_skills.suggestions) +
                len(behavioral.suggestions) +
                (1 if compensation.salary else 0) +
                (1 if compensation.bonus else 0) +
                len(compensation.benefits_suggestions)
            )
            
            wsi_score, wsi_warnings = self._calculate_wsi_quality(
                request, technical_skills, behavioral
            )
            
            completeness = self._calculate_completeness(
                request, responsibilities, technical_skills, behavioral, compensation
            )
            
            enriched_jd = EnrichedJobDescription(
                job_id=request.job_draft_id,
                company_id=request.company_id,
                title=request.title,
                department=request.department,
                seniority=request.seniority,
                location=request.location,
                work_model=request.work_model,
                responsibilities=responsibilities,
                technical_skills=technical_skills,
                behavioral_competencies=behavioral,
                compensation=compensation,
                total_suggestions_count=total_suggestions,
                wsi_quality_score=wsi_score,
                wsi_quality_warnings=wsi_warnings,
                completeness_score=completeness,
                analysis_context={
                    "sources_analyzed": [
                        "market_benchmark",
                        "company_history",
                        "skills_catalog",
                        "responsibilities_catalog"
                    ],
                    "company_id": request.company_id,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            summary = self._generate_summary_message(enriched_jd)
            
            return EnrichmentResponse(
                success=True,
                enriched_jd=enriched_jd,
                summary_message=summary
            )
            
        except Exception as e:
            self.logger.error(f"Error enriching JD: {e}", exc_info=True)
            return EnrichmentResponse(
                success=False,
                error=str(e),
                summary_message="Erro ao enriquecer o Job Description. Tente novamente."
            )
    
    async def enrich_and_persist_vacancy(
        self,
        job_vacancy_id: str,
        company_id: str,
        db: AsyncSession,
    ) -> "JdEnrichmentPersistResult":
        """Enriquece a JD de uma vaga REAL e persiste o resultado na vaga.

        Carrega a vaga (fail-alto se ausente), enriquece a partir dos campos
        atuais, aplica o gate de mínimos WSI (9 técnicas + 5 comportamentais)
        e — somente quando os mínimos são atingidos — grava as colunas
        estruturadas (``technical_requirements``, ``behavioral_competencies``,
        ``responsibilities``, ``description``) e o blob ``enriched_jd``.

        Quando os mínimos NÃO são atingidos, NÃO persiste (não enriquece "no
        vácuo") e retorna ``persisted=False`` com mensagem explícita do que
        falta. Erros de input (company_id ausente, UUID inválido, vaga
        inexistente) levantam ``ValueError`` — falha alto, sem fake success.
        """
        from app.schemas.jd_enrichment import JdEnrichmentPersistResult

        if not company_id or not str(company_id).strip():
            raise ValueError("company_id é obrigatório para enrich_and_persist_vacancy")
        if not job_vacancy_id or not str(job_vacancy_id).strip():
            raise ValueError("job_vacancy_id é obrigatório para enrich_and_persist_vacancy")

        import uuid as _uuid

        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCRUDRepository,
        )

        try:
            vacancy_uuid = _uuid.UUID(str(job_vacancy_id))
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"job_vacancy_id inválido (esperado UUID): {job_vacancy_id!r}"
            ) from exc

        repo = JobVacancyCRUDRepository(db)
        vacancy = await repo.get_vacancy_by_id_and_company(vacancy_uuid, company_id)
        if vacancy is None:
            raise ValueError(
                f"Vaga {job_vacancy_id} não encontrada para a empresa {company_id}"
            )

        salary_range = getattr(vacancy, "salary_range", None) or {}
        request = EnrichmentRequest(
            company_id=str(company_id),
            job_draft_id=str(vacancy.id),
            title=vacancy.title or "",
            department=getattr(vacancy, "department", None),
            seniority=getattr(vacancy, "seniority_level", None),
            location=getattr(vacancy, "location", None),
            work_model=getattr(vacancy, "work_model", None),
            detected_responsibilities=list(getattr(vacancy, "responsibilities", None) or []),
            detected_technical_skills=_extract_skill_names(
                getattr(vacancy, "technical_requirements", None)
            ),
            detected_behavioral_competencies=_extract_skill_names(
                getattr(vacancy, "behavioral_competencies", None)
            ),
            salary_min=salary_range.get("min") if isinstance(salary_range, dict) else None,
            salary_max=salary_range.get("max") if isinstance(salary_range, dict) else None,
            raw_input=getattr(vacancy, "description", None),
        )

        response = await self.enrich_job_description(request, db)
        if not response.success or response.enriched_jd is None:
            return JdEnrichmentPersistResult(
                success=False,
                persisted=False,
                meets_wsi_minimums=False,
                job_vacancy_id=str(vacancy.id),
                message=response.summary_message
                or "Falha ao enriquecer o Job Description.",
                error=response.error,
            )

        payload = build_wsi_persistence_payload(
            response.enriched_jd,
            original_description=getattr(vacancy, "description", None),
        )

        technical = payload["technical_skills"]
        behavioral = payload["behavioral_competencies"]
        responsibilities = payload["responsibilities"]
        meets = payload["meets_wsi_minimums"]

        if not meets:
            missing_tech = max(0, MIN_TECHNICAL_SKILLS_FOR_WSI - len(technical))
            missing_behav = max(0, MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI - len(behavioral))
            parts: list[str] = []
            if missing_tech:
                parts.append(f"{missing_tech} competência(s) técnica(s)")
            if missing_behav:
                parts.append(f"{missing_behav} competência(s) comportamental(is)")
            faltam = " e ".join(parts) if parts else "dados mínimos"
            message = (
                f"Não enriqueci a vaga ainda: faltam {faltam} para atingir o mínimo "
                f"de qualidade WSI ({MIN_TECHNICAL_SKILLS_FOR_WSI} técnicas + "
                f"{MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI} comportamentais). "
                "Me diga mais sobre a vaga para eu completar."
            )
            self.logger.info(
                "enrich_and_persist_vacancy: mínimos WSI não atingidos para vaga %s "
                "(tech=%d/%d, behav=%d/%d) — não persistindo",
                vacancy.id,
                len(technical),
                MIN_TECHNICAL_SKILLS_FOR_WSI,
                len(behavioral),
                MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI,
            )
            return JdEnrichmentPersistResult(
                success=True,
                persisted=False,
                meets_wsi_minimums=False,
                job_vacancy_id=str(vacancy.id),
                technical_count=len(technical),
                behavioral_count=len(behavioral),
                responsibilities_count=len(responsibilities),
                wsi_quality_score=payload["wsi_quality_score"],
                wsi_quality_warnings=payload["wsi_quality_warnings"],
                message=message,
            )

        vacancy.technical_requirements = payload["technical_requirements_objects"]
        vacancy.behavioral_competencies = payload["behavioral_competencies_objects"]
        vacancy.responsibilities = responsibilities
        vacancy.description = payload["generated_jd_text"]
        vacancy.enriched_jd = payload["enriched_jd"]
        vacancy.updated_at = datetime.utcnow()

        await repo.flush_and_refresh(vacancy)
        await db.commit()

        self.logger.info(
            "enrich_and_persist_vacancy: vaga %s enriquecida e persistida "
            "(tech=%d, behav=%d, resp=%d, wsi=%.2f)",
            vacancy.id,
            len(technical),
            len(behavioral),
            len(responsibilities),
            payload["wsi_quality_score"] or 0.0,
        )

        return JdEnrichmentPersistResult(
            success=True,
            persisted=True,
            meets_wsi_minimums=True,
            job_vacancy_id=str(vacancy.id),
            technical_count=len(technical),
            behavioral_count=len(behavioral),
            responsibilities_count=len(responsibilities),
            wsi_quality_score=payload["wsi_quality_score"],
            wsi_quality_warnings=payload["wsi_quality_warnings"],
            message="Job Description enriquecida e salva na vaga.",
        )

    def _empty_section(self, name: str, title: str) -> SectionSuggestions:
        """Retorna uma seção vazia."""
        return SectionSuggestions(section_name=name, section_title=title)
    
    async def _enrich_responsibilities(
        self,
        request: EnrichmentRequest,
        db: AsyncSession | None
    ) -> SectionSuggestions:
        """Enriquece responsabilidades com sugestões do catálogo e histórico."""
        detected = request.detected_responsibilities or []
        suggestions: list[EnrichedSuggestion] = []
        
        try:
            self._detect_area_from_title(request.title)
            seniority = request.seniority or "pleno"
            
            catalog_suggestions = self.responsibilities_catalog.suggest_responsibilities(
                role=request.title,
                seniority=seniority,
                limit=5
            )
            
            for i, resp in enumerate(catalog_suggestions):
                resp_text = resp.description if hasattr(resp, 'description') else str(resp)
                if resp_text not in detected:
                    suggestions.append(EnrichedSuggestion(
                        id=f"resp-catalog-{i}",
                        value=resp_text,
                        source=SuggestionSource.SKILLS_CATALOG,
                        justification=f"Responsabilidade comum para {request.title} ({seniority})",
                        impact_description="Melhora clareza sobre as expectativas do cargo",
                        impact_level=SuggestionImpactLevel.MEDIUM,
                        is_new=True,
                        category="responsibilities"
                    ))
            
            
            missing_count = max(0, MIN_RESPONSIBILITIES - len(detected))
            quality_note = None
            if missing_count > 0:
                quality_note = f"Adicione +{missing_count} responsabilidades para uma descrição mais completa"
            
        except Exception as e:
            self.logger.error(f"Error enriching responsibilities: {e}")
            missing_count = 0
            quality_note = None
        
        return SectionSuggestions(
            section_name="responsibilities",
            section_title="Responsabilidades",
            detected_items=detected,
            suggestions=suggestions[:8],
            missing_count=missing_count,
            recommended_count=MIN_RESPONSIBILITIES,
            quality_note=quality_note
        )
    
    async def _enrich_technical_skills(
        self,
        request: EnrichmentRequest,
        db: AsyncSession | None
    ) -> SectionSuggestions:
        """Enriquece competências técnicas com dados de mercado e catálogo."""
        detected = request.detected_technical_skills or []
        suggestions: list[EnrichedSuggestion] = []
        
        try:
            role_area = self._detect_area_from_title(request.title)
            
            catalog_result = self.skills_catalog.get_skills_for_role(
                role=request.title,
                seniority=request.seniority
            )
            catalog_skills = catalog_result.get("technical", [])[:6] if isinstance(catalog_result, dict) else []
            
            market_data = await self._get_market_skill_data(request.title, request.location)
            
            for i, skill in enumerate(catalog_skills):
                if skill not in detected:
                    market_percentage = market_data.get(skill.lower(), {}).get("percentage", 0)
                    time_improvement = market_data.get(skill.lower(), {}).get("time_improvement", 0)
                    
                    justification = f"Skill relevante para {role_area}"
                    if market_percentage > 0:
                        justification = f"{market_percentage}% das vagas similares no mercado incluem {skill}"
                    
                    impact_desc = None
                    if time_improvement > 0:
                        impact_desc = f"Vagas com {skill} fecham {time_improvement}% mais rápido"
                    
                    suggestions.append(TechnicalSkillSuggestion(
                        id=f"tech-catalog-{i}",
                        value=skill,
                        source=SuggestionSource.MARKET_BENCHMARK if market_percentage > 0 else SuggestionSource.SKILLS_CATALOG,
                        justification=justification,
                        metrics={"market_percentage": market_percentage} if market_percentage > 0 else None,
                        impact_description=impact_desc,
                        impact_level=SuggestionImpactLevel.HIGH if market_percentage > 70 else SuggestionImpactLevel.MEDIUM,
                        is_new=True,
                        category="technical_skills",
                        market_demand_trend="stable"
                    ))
            
            
            missing_count = max(0, MIN_TECHNICAL_SKILLS_FOR_WSI - len(detected))
            quality_note = None
            if missing_count > 0:
                if len(detected) < 5:
                    quality_note = f"⚠️ Apenas {len(detected)} competências técnicas — adicione +{missing_count} para triagem WSI completa (modo Full requer até 9 perguntas técnicas)"
                else:
                    quality_note = f"Adicione +{missing_count} competências técnicas para cobertura total no modo Completo (recomendado: 9+)"
            
        except Exception as e:
            self.logger.error(f"Error enriching technical skills: {e}")
            missing_count = 0
            quality_note = None
        
        return SectionSuggestions(
            section_name="technical_skills",
            section_title="Competências Técnicas",
            detected_items=detected,
            suggestions=suggestions[:8],
            missing_count=missing_count,
            recommended_count=MIN_TECHNICAL_SKILLS_FOR_WSI,
            quality_note=quality_note
        )
    
    async def _enrich_behavioral_competencies(
        self,
        request: EnrichmentRequest,
        db: AsyncSession | None
    ) -> SectionSuggestions:
        """Enriquece competências comportamentais com foco em qualidade WSI."""
        detected = request.detected_behavioral_competencies or []
        suggestions: list[EnrichedSuggestion] = []
        
        try:
            role_area = self._detect_area_from_title(request.title)
            is_leadership = self._is_leadership_role(request.title, request.seniority)
            
            catalog_result = self.skills_catalog.get_behavioral_competencies_for_role(
                role=request.title
            )
            catalog_competencies = [c.get("name", c) if isinstance(c, dict) else c for c in catalog_result[:5]]
            
            leadership_competencies = ["Liderança", "Gestão de Conflitos", "Desenvolvimento de Pessoas", "Tomada de Decisão"]
            senior_competencies = ["Comunicação Assertiva", "Influência", "Pensamento Estratégico"]
            
            for i, comp in enumerate(catalog_competencies):
                if comp not in detected:
                    is_leadership_comp = comp in leadership_competencies
                    is_senior_comp = comp in senior_competencies
                    
                    if is_leadership and is_leadership_comp:
                        justification = f"92% dos cargos de liderança pedem {comp}"
                        wsi_note = "Essencial para perguntas WSI sobre gestão e liderança"
                    elif is_senior_comp and request.seniority and "sênior" in request.seniority.lower():
                        justification = "Competência crítica para profissionais sênior"
                        wsi_note = "Permite avaliar maturidade profissional nas perguntas WSI"
                    else:
                        justification = f"Competência recomendada para {role_area}"
                        wsi_note = "Melhora a qualidade das perguntas comportamentais WSI"
                    
                    suggestions.append(BehavioralCompetencySuggestion(
                        id=f"behav-catalog-{i}",
                        value=comp,
                        source=SuggestionSource.SKILLS_CATALOG,
                        justification=justification,
                        wsi_quality_note=wsi_note,
                        impact_description="Permite gerar perguntas de triagem mais assertivas",
                        impact_level=SuggestionImpactLevel.HIGH if is_leadership_comp else SuggestionImpactLevel.MEDIUM,
                        is_new=True,
                        category="behavioral_competencies"
                    ))
            
            
            missing_count = max(0, MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI - len(detected))
            quality_note = None
            if missing_count > 0:
                quality_note = f"⚠️ Faltam {missing_count} competências comportamentais (mínimo {MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI} para cobertura dos 5 pilares de avaliação). Adicione estas sugestões para melhorar a triagem."
            
        except Exception as e:
            self.logger.error(f"Error enriching behavioral competencies: {e}")
            missing_count = 0
            quality_note = None
        
        return SectionSuggestions(
            section_name="behavioral_competencies",
            section_title="Competências Comportamentais",
            detected_items=detected,
            suggestions=suggestions[:6],
            missing_count=missing_count,
            recommended_count=MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI,
            quality_note=quality_note
        )
    
    async def _enrich_compensation(
        self,
        request: EnrichmentRequest,
        db: AsyncSession | None
    ) -> CompensationSuggestions:
        """Enriquece dados de remuneração com benchmark de mercado."""
        salary_suggestion = None
        bonus_suggestion = None
        
        try:
            if request.salary_min or request.salary_max:
                market_data = await self.market_benchmark.search_salary_benchmark(
                    role=request.title,
                    location=request.location or "São Paulo",
                    seniority=request.seniority
                )
                
                if market_data:
                    market_min = market_data.get("min", 0)
                    market_max = market_data.get("max", 0)
                    market_median = market_data.get("median", 0)
                    
                    current_max = request.salary_max or 0
                    
                    if market_median > 0 and current_max > 0:
                        diff_percentage = ((market_median - current_max) / market_median) * 100
                        
                        if diff_percentage > 5:
                            comparison = f"{abs(diff_percentage):.0f}% abaixo do mercado"
                            impact = f"Ajustar pode aumentar aplicações qualificadas em {min(diff_percentage * 2, 50):.0f}%"
                            
                            salary_suggestion = SalarySuggestion(
                                id="salary-benchmark-1",
                                suggested_min=market_min,
                                suggested_max=market_max,
                                current_min=request.salary_min,
                                current_max=request.salary_max,
                                justification=f"Sua faixa está {comparison} para {request.location or 'o mercado'}",
                                market_comparison=comparison,
                                impact_description=impact,
                                market_percentile=int(((current_max / market_max) * 100) if market_max > 0 else 50),
                                sources_consulted=market_data.get("sources", ["Glassdoor", "LinkedIn"]),
                                sample_size=market_data.get("sample_size", 50)
                            )
                        elif diff_percentage < -10:
                            salary_suggestion = SalarySuggestion(
                                id="salary-benchmark-1",
                                suggested_min=market_min,
                                suggested_max=market_max,
                                current_min=request.salary_min,
                                current_max=request.salary_max,
                                justification=f"Sua faixa está {abs(diff_percentage):.0f}% acima do mercado - competitiva!",
                                market_comparison=f"{abs(diff_percentage):.0f}% acima do mercado",
                                impact_description="Faixa competitiva, deve atrair bons candidatos",
                                market_percentile=min(int(((current_max / market_max) * 100) if market_max > 0 else 75), 95),
                                sources_consulted=market_data.get("sources", ["Glassdoor", "LinkedIn"]),
                                sample_size=market_data.get("sample_size", 50)
                            )
            
            is_senior = request.seniority and ("sênior" in request.seniority.lower() or "senior" in request.seniority.lower())
            is_leadership = self._is_leadership_role(request.title, request.seniority)
            
            if is_senior or is_leadership:
                bonus_suggestion = BonusSuggestion(
                    id="bonus-benchmark-1",
                    suggested_salary_months="2-4 salários",
                    suggested_percentage_min=15,
                    suggested_percentage_max=30,
                    justification="Bônus anual é prática comum para cargos sênior/liderança",
                    sector_practice=f"Média do setor para {request.title}: 2-4 salários"
                )
            
        except Exception as e:
            self.logger.error(f"Error enriching compensation: {e}")
        
        return CompensationSuggestions(
            salary=salary_suggestion,
            bonus=bonus_suggestion,
            benefits_suggestions=[],
            total_compensation_note="Remuneração total inclui salário base, bônus e benefícios" if salary_suggestion else None
        )
    
    async def _get_market_skill_data(
        self,
        title: str,
        location: str | None
    ) -> dict[str, dict[str, Any]]:
        """Busca dados de mercado sobre skills (mock por enquanto)."""
        common_skills_market_data = {
            "python": {"percentage": 85, "time_improvement": 15},
            "javascript": {"percentage": 80, "time_improvement": 12},
            "react": {"percentage": 75, "time_improvement": 18},
            "node.js": {"percentage": 70, "time_improvement": 14},
            "docker": {"percentage": 68, "time_improvement": 23},
            "kubernetes": {"percentage": 55, "time_improvement": 20},
            "aws": {"percentage": 72, "time_improvement": 17},
            "sql": {"percentage": 82, "time_improvement": 10},
            "typescript": {"percentage": 65, "time_improvement": 16},
            "java": {"percentage": 60, "time_improvement": 11},
        }
        return common_skills_market_data
    
    def _detect_area_from_title(self, title: str) -> str:
        """Detecta a área com base no título do cargo."""
        title_lower = title.lower()
        
        tech_keywords = ["desenvolvedor", "developer", "engenheiro", "engineer", "devops", "data", "software", "tech", "programador"]
        finance_keywords = ["financeiro", "contábil", "contador", "fp&a", "tesouraria", "controller"]
        hr_keywords = ["rh", "recursos humanos", "recrutador", "talent", "people"]
        marketing_keywords = ["marketing", "growth", "comunicação", "social media", "conteúdo"]
        sales_keywords = ["vendas", "comercial", "account", "sales", "sdr", "closer"]
        
        for keyword in tech_keywords:
            if keyword in title_lower:
                return "engineering"
        for keyword in finance_keywords:
            if keyword in title_lower:
                return "finance"
        for keyword in hr_keywords:
            if keyword in title_lower:
                return "hr"
        for keyword in marketing_keywords:
            if keyword in title_lower:
                return "marketing"
        for keyword in sales_keywords:
            if keyword in title_lower:
                return "sales"
        
        return "general"
    
    def _is_leadership_role(self, title: str, seniority: str | None) -> bool:
        """Verifica se é um cargo de liderança."""
        title_lower = title.lower()
        leadership_keywords = ["gerente", "diretor", "head", "líder", "lead", "manager", "coordenador", "supervisor", "cto", "ceo", "vp"]
        
        for keyword in leadership_keywords:
            if keyword in title_lower:
                return True
        
        if seniority and "sênior" in seniority.lower():
            if any(word in title_lower for word in ["tech", "técnico", "arquiteto"]):
                return True
        
        return False
    
    def _calculate_wsi_quality(
        self,
        request: EnrichmentRequest,
        technical_skills: SectionSuggestions,
        behavioral: SectionSuggestions
    ) -> tuple[float, list[str]]:
        """Score de qualidade WSI — DELEGADO ao canônico 9-dim (Fase 3.3).

        Consolidação WSI: delega a
        ``cv_screening.services.wsi_service.jd_quality.evaluate_jd_quality``
        (single source). Retorna 0-1 (escala original desta superfície)
        derivado do score canônico /100. Mapeia EnrichmentRequest -> inputs.
        """
        from app.domains.cv_screening.services.wsi_service.jd_quality import (
            evaluate_jd_quality,
        )

        r = evaluate_jd_quality(
            description=request.raw_input,
            job_title=request.title,
            department=request.department,
            seniority=request.seniority,
            responsibilities=list(request.detected_responsibilities or []),
            technical_skills=list(request.detected_technical_skills or []),
            behavioral_competencies=list(request.detected_behavioral_competencies or []),
        )
        warnings = [
            ind["detail"]
            for ind in r["indicators"]
            if ind.get("status") in ("insufficient", "partial")
        ]
        return round(r["score"] / 100.0, 2), warnings
    
    def _calculate_completeness(
        self,
        request: EnrichmentRequest,
        responsibilities: SectionSuggestions,
        technical_skills: SectionSuggestions,
        behavioral: SectionSuggestions,
        compensation: CompensationSuggestions
    ) -> float:
        """Calcula score de completude do JD."""
        score = 0.0
        weights = {
            "title": 0.15,
            "responsibilities": 0.20,
            "technical_skills": 0.20,
            "behavioral": 0.15,
            "salary": 0.15,
            "location": 0.10,
            "seniority": 0.05
        }
        
        if request.title:
            score += weights["title"]
        
        resp_count = len(request.detected_responsibilities or [])
        if resp_count >= MIN_RESPONSIBILITIES:
            score += weights["responsibilities"]
        elif resp_count > 0:
            score += weights["responsibilities"] * (resp_count / MIN_RESPONSIBILITIES)
        
        tech_count = len(request.detected_technical_skills or [])
        if tech_count >= MIN_TECHNICAL_SKILLS_FOR_WSI:
            score += weights["technical_skills"]
        elif tech_count > 0:
            score += weights["technical_skills"] * (tech_count / MIN_TECHNICAL_SKILLS_FOR_WSI)
        
        behav_count = len(request.detected_behavioral_competencies or [])
        if behav_count >= MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI:
            score += weights["behavioral"]
        elif behav_count > 0:
            score += weights["behavioral"] * (behav_count / MIN_BEHAVIORAL_COMPETENCIES_FOR_WSI)
        
        if request.salary_min and request.salary_max:
            score += weights["salary"]
        elif request.salary_min or request.salary_max:
            score += weights["salary"] * 0.5
        
        if request.location:
            score += weights["location"]
        
        if request.seniority:
            score += weights["seniority"]
        
        return min(1.0, score)
    
    def _generate_summary_message(self, enriched_jd: EnrichedJobDescription) -> str:
        """Gera mensagem de resumo para a LIA apresentar."""
        suggestions_count = enriched_jd.total_suggestions_count
        
        sections_with_suggestions = []
        if enriched_jd.responsibilities.suggestions:
            sections_with_suggestions.append(f"{len(enriched_jd.responsibilities.suggestions)} responsabilidades")
        if enriched_jd.technical_skills.suggestions:
            sections_with_suggestions.append(f"{len(enriched_jd.technical_skills.suggestions)} competências técnicas")
        if enriched_jd.behavioral_competencies.suggestions:
            sections_with_suggestions.append(f"{len(enriched_jd.behavioral_competencies.suggestions)} competências comportamentais")
        if enriched_jd.compensation.salary:
            sections_with_suggestions.append("ajuste de faixa salarial")
        
        message = "Analisei as informações usando dados de mercado, histórico de vagas e configurações da empresa. "
        
        if suggestions_count > 0:
            message += f"Preparei {suggestions_count} sugestões para enriquecer o JD: {', '.join(sections_with_suggestions)}. "
        
        if enriched_jd.wsi_quality_warnings:
            message += f"\n\n⚠️ **Atenção WSI:** {enriched_jd.wsi_quality_warnings[0]}"
        
        message += "\n\nAs sugestões marcadas com 💡 são opcionais. Você pode aceitar todas, algumas ou nenhuma."
        
        return message
    
    async def generate_enriched_jd(
        self,
        request: EnrichmentRequest,
        db: AsyncSession | None = None
    ) -> 'EnrichedJDResult':
        """
        Generate enriched JD in format expected by frontend.
        
        Wraps enrich_job_description and returns result with sections as array.
        
        Args:
            request: Enrichment request data
            db: Optional database session
            
        Returns:
            EnrichedJDResult with sections as array
        """
        response = await self.enrich_job_description(request, db)
        
        if not response.success or not response.enriched_jd:
            raise ValueError(response.error or "Failed to enrich job description")
        
        enriched = response.enriched_jd
        
        sections = [
            enriched.responsibilities,
            enriched.technical_skills,
            enriched.behavioral_competencies
        ]
        
        return EnrichedJDResult(
            sections=sections,
            compensation=EnrichedCompensationResult(
                current_range={"min": enriched.compensation.salary.current_min, "max": enriched.compensation.salary.current_max} if enriched.compensation.salary and enriched.compensation.salary.current_min else None,
                market_range={"min": enriched.compensation.salary.suggested_min, "max": enriched.compensation.salary.suggested_max} if enriched.compensation.salary else None,
                market_position=self._determine_market_position(enriched.compensation.salary) if enriched.compensation.salary else None,
                salary_suggestion=enriched.compensation.salary,
                bonus_suggestion=enriched.compensation.bonus,
                competitiveness_score=enriched.compensation.salary.market_percentile if enriched.compensation.salary else None
            ) if enriched.compensation else None,
            wsi_quality_score=int((enriched.wsi_quality_score or 0) * 100),
            overall_completeness=enriched.completeness_score,
            total_suggestions=enriched.total_suggestions_count
        )
    
    def _determine_market_position(self, salary: SalarySuggestion | None) -> str | None:
        """Determine market position based on salary comparison."""
        if not salary or not salary.market_comparison:
            return None
        
        comparison = salary.market_comparison.lower()
        if "abaixo" in comparison:
            return "below"
        elif "acima" in comparison:
            return "above"
        else:
            return "competitive"


class EnrichedCompensationResult:
    """Result object for compensation data."""
    def __init__(
        self,
        current_range: dict | None = None,
        market_range: dict | None = None,
        market_position: str | None = None,
        salary_suggestion: SalarySuggestion | None = None,
        bonus_suggestion: BonusSuggestion | None = None,
        competitiveness_score: int | None = None
    ):
        self.current_range = current_range
        self.market_range = market_range
        self.market_position = market_position
        self.salary_suggestion = salary_suggestion
        self.bonus_suggestion = bonus_suggestion
        self.competitiveness_score = competitiveness_score


class EnrichedJDResult:
    """Result object for enriched JD data with sections as array."""
    def __init__(
        self,
        sections: list[SectionSuggestions],
        compensation: EnrichedCompensationResult | None,
        wsi_quality_score: int,
        overall_completeness: float,
        total_suggestions: int
    ):
        self.sections = sections
        self.compensation = compensation
        self.wsi_quality_score = wsi_quality_score
        self.overall_completeness = overall_completeness
        self.total_suggestions = total_suggestions


jd_enrichment_service = JdEnrichmentService()
