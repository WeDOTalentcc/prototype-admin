# ADR-001-EXEMPT: JSON path workaround for non-JSONB column
# (`additional_data->>'external_id'`). Rails-mirrored table where Python is
# read-only; query stays inline because moving requires schema migration to
# JSONB which is owned by Rails (out of scope for this repo).
"""
JD Import Service - Parses and normalizes job descriptions from ATS/HRIS.

Phase 1B of Learning Loop: Extract structured data from imported JDs.

Features:
- Parse JD text into structured fields (title, skills, responsibilities)
- Normalize job titles for matching
- Extract and categorize skills (technical vs behavioral)
- Detect seniority levels
- Build company-specific catalogs
"""
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.imported_job_description import (
    ClientSkillCatalog,
    ImportBatch,
    ImportedJobDescription,
    ImportSource,
    ImportStatus,
    ProcessingStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class ParsedJD:
    """Result of parsing a job description."""
    title_normalized: str
    seniority: str | None
    seniority_confidence: float
    department: str | None
    employment_type: str | None
    work_model: str | None
    responsibilities: list[str]
    technical_skills: list[dict[str, Any]]
    behavioral_competencies: list[dict[str, Any]]
    salary_min: float | None
    salary_max: float | None
    benefits: list[str]
    parsing_confidence: float



def _normalize_location(raw) -> str | None:
    """Format location: JSON string {"city":...,"state":...} -> "City, ST".
    Handles plain strings, dicts, and null values transparently.
    """
    if not raw:
        return None
    if isinstance(raw, dict):
        parts = [p for p in [raw.get("city"), raw.get("state")] if p]
        return ", ".join(parts) or None
    if isinstance(raw, str) and raw.startswith("{"):
        import json as _json
        try:
            loc = _json.loads(raw)
            parts = [p for p in [loc.get("city"), loc.get("state")] if p]
            return ", ".join(parts) or None
        except Exception:
            pass
    return raw or None


class JDImportService:
    """
    Service for importing and parsing job descriptions from external sources.
    
    Handles:
    - Batch import from ATS/HRIS
    - Text parsing and field extraction
    - Skill normalization and categorization
    - Building company-specific catalogs
    """
    
    SENIORITY_PATTERNS = {
        "estagio": ["estágio", "estagio", "intern", "internship", "estagi"],
        "trainee": ["trainee", "jovem aprendiz", "aprendiz"],
        "junior": ["júnior", "junior", "jr", "jr.", "nivel i", "nível i", "entry level", "iniciante"],
        "pleno": ["pleno", "pl", "pl.", "nivel ii", "nível ii", "mid-level", "mid level", "intermediário"],
        "senior": ["sênior", "senior", "sr", "sr.", "nivel iii", "nível iii", "experienced"],
        "especialista": ["especialista", "specialist", "expert", "principal", "staff"],
        "coordenador": ["coordenador", "coordinator", "coord", "coord.", "lead", "líder técnico"],
        "gerente": ["gerente", "manager", "gestor", "head of", "head de"],
        "diretor": ["diretor", "director", "vp", "vice-presidente", "c-level", "cto", "cfo", "ceo"],
    }
    
    SKILL_CATEGORIES = {
        "programming": ["python", "java", "javascript", "typescript", "c#", "c++", "ruby", "go", "rust", "php", "swift", "kotlin"],
        "frameworks": ["react", "angular", "vue", "django", "flask", "spring", "rails", "express", "nextjs", "nest"],
        "databases": ["sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "oracle", "dynamodb"],
        "cloud": ["aws", "azure", "gcp", "google cloud", "kubernetes", "docker", "terraform", "cloudformation"],
        "data": ["spark", "hadoop", "airflow", "databricks", "snowflake", "bigquery", "pandas", "numpy", "dbt"],
        "devops": ["ci/cd", "jenkins", "gitlab", "github actions", "ansible", "puppet", "chef"],
        "agile": ["scrum", "kanban", "agile", "jira", "confluence"],
    }
    
    BEHAVIORAL_KEYWORDS = [
        "comunicação", "comunicacao", "communication",
        "liderança", "lideranca", "leadership",
        "trabalho em equipe", "teamwork", "colaboração", "colaboracao",
        "proatividade", "proativo", "proactive",
        "resolução de problemas", "problem solving",
        "adaptabilidade", "flexibilidade", "flexibility",
        "pensamento crítico", "critical thinking", "analítico",
        "organização", "organizacao", "organization",
        "gestão do tempo", "time management",
        "criatividade", "creativity", "inovação", "innovation",
        "empatia", "empathy",
        "negociação", "negociacao", "negotiation",
        "resiliência", "resilience",
        "autonomia", "autonomy", "independência",
    ]
    
    BENEFIT_KEYWORDS = [
        "vale refeição", "vr", "vale alimentação", "va", "vale transporte", "vt",
        "plano de saúde", "plano de saude", "assistência médica", "convênio médico",
        "plano odontológico", "plano dental", "odonto",
        "seguro de vida", "seguro vida",
        "gympass", "totalpass", "academia",
        "home office", "trabalho remoto", "remoto",
        "plr", "ppr", "bônus", "bonus", "participação nos lucros",
        "day off", "folga aniversário", "folga de aniversário",
        "auxílio creche", "auxilio creche", "auxílio educação",
        "previdência privada", "previdencia privada",
        "stock options", "ações", "equity",
        "horário flexível", "flexibilidade de horário",
    ]

    async def create_import_batch(
        self,
        db: AsyncSession,
        company_id: UUID,
        source: str,
        total_records: int,
        created_by: str | None = None,
        config: dict | None = None
    ) -> ImportBatch:
        """Create a new import batch for tracking."""
        batch = ImportBatch(
            company_id=company_id,
            source=source,
            total_records=total_records,
            created_by=created_by,
            import_config=config or {},
            started_at=datetime.utcnow()
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        return batch

    async def import_jd(
        self,
        db: AsyncSession,
        company_id: UUID,
        jd_data: dict[str, Any],
        source: str = ImportSource.MANUAL_UPLOAD.value,
        batch_id: UUID | None = None,
        parse_immediately: bool = True
    ) -> ImportedJobDescription:
        """
        Import a single job description.
        
        Args:
            db: Database session
            company_id: Company identifier
            jd_data: Raw JD data with at least 'title' and optionally 'description'
            source: Import source (ats_gupy, manual_upload, etc.)
            batch_id: Optional batch ID for tracking
            parse_immediately: Whether to parse the JD immediately
        """
        imported_jd = ImportedJobDescription(
            company_id=company_id,
            external_id=jd_data.get("external_id"),
            source=source,
            import_batch_id=batch_id,
            job_title_original=jd_data.get("title", ""),
            department=jd_data.get("department"),
            area=jd_data.get("area"),
            team=jd_data.get("team"),
            seniority=jd_data.get("seniority"),
            employment_type=jd_data.get("employment_type"),
            work_model=jd_data.get("work_model"),
            location=_normalize_location(jd_data.get("location")),
            description_raw=jd_data.get("description"),
            responsibilities_raw=jd_data.get("responsibilities_text"),
            salary_min=jd_data.get("salary_min"),
            salary_max=jd_data.get("salary_max"),
            salary_currency=jd_data.get("salary_currency", "BRL"),
            benefits=jd_data.get("benefits", []),
            hiring_manager=jd_data.get("hiring_manager"),
            hiring_manager_email=jd_data.get("hiring_manager_email"),
            recruiter=jd_data.get("recruiter"),
            headcount=jd_data.get("headcount", 1),
            job_status=jd_data.get("status"),
            was_filled=jd_data.get("was_filled"),
            candidates_count=jd_data.get("candidates_count"),
            time_to_fill_days=jd_data.get("time_to_fill_days"),
            hired_candidate_id=jd_data.get("hired_candidate_id"),
            created_date_original=jd_data.get("created_date"),
            closed_date_original=jd_data.get("closed_date"),
            metadata_raw=jd_data.get("metadata", {}),
        )
        
        quality_score = self._compute_quality_score(jd_data)
        imported_jd.is_used_for_learning = quality_score >= 0.65

        # ── FairnessGuard — fail-closed: blocked JDs never feed the learning loop ──
        # Hard block (is_blocked=True): is_used_for_learning=False + raises ValueError
        #   → import_batch_jds catches it → item counted as failed in batch.errors
        # Soft warnings: is_used_for_learning=False + continues (item saved, not learned from)
        # Guard exception: fail-open for guard regression (log warning, keep existing flag)
        if imported_jd.is_used_for_learning:
            _fg_text = " ".join(filter(None, [
                jd_data.get("title", ""),
                jd_data.get("description", ""),
                jd_data.get("responsibilities_text", ""),
                " ".join(jd_data.get("required_skills") or jd_data.get("skills") or []),
            ])).strip()
            if _fg_text:
                try:
                    from app.shared.compliance.fairness_guard import FairnessGuard
                    _fg_result = FairnessGuard().check(_fg_text)
                    if _fg_result.is_blocked:
                        imported_jd.is_used_for_learning = False
                        logger.warning(
                            "[JDImport] FairnessGuard HARD BLOCK: JD '%s' excluded from learning "
                            "(category=%s, terms=%s) company_id=%s",
                            jd_data.get("title", "?"), _fg_result.category,
                            _fg_result.blocked_terms, company_id,
                        )
                        raise ValueError(
                            f"fairness_blocked category={_fg_result.category} "
                            f"terms={','.join(_fg_result.blocked_terms or [])}"
                        )
                    elif _fg_result.soft_warnings:
                        imported_jd.is_used_for_learning = False
                        logger.warning(
                            "[JDImport] FairnessGuard soft warnings: JD '%s' excluded from "
                            "learning (warnings=%s) company_id=%s",
                            jd_data.get("title", "?"), _fg_result.soft_warnings, company_id,
                        )
                except ValueError:
                    raise
                except Exception as _fg_exc:  # noqa: BLE001 — guard regression must not break import
                    logger.warning(
                        "[JDImport] FairnessGuard check failed — fail-open (guard regression): %s",
                        _fg_exc,
                    )

        if parse_immediately:
            parsed = self.parse_jd(imported_jd)
            self._apply_parsed_data(imported_jd, parsed)

        db.add(imported_jd)
        await db.commit()
        await db.refresh(imported_jd)

        # ── Phase 4H — create JobVacancy mirror for the rail filter ──
        # User-facing rail "ATS" reads from job_vacancies WHERE source='ats_import'.
        # Without this mirror, imported JDs only live in imported_job_descriptions
        # and never surface as cards in the Vagas page.
        # Fail-open: any error logs warning + continues (imported_jd already persisted).
        try:
            await self._mirror_to_job_vacancy(db, company_id, imported_jd, source)
        except Exception as exc:
            logger.warning(
                "[JDImport] _mirror_to_job_vacancy failed (fail-open) for jd=%s: %s",
                imported_jd.id, exc,
            )

        return imported_jd

    @staticmethod
    def _map_source_to_vacancy(import_source: str) -> str:
        """Map ImportSource enum value to JobVacancy.source canonical value.

        Live ATS sync (Gupy, Greenhouse, Lever) -> 'ats_external'.
        One-time imports (spreadsheet, manual upload, API) -> 'ats_import'.
        Anything else (defensive) -> 'ats_import'.
        """
        live_sync = {"ats_gupy", "ats_pandape", "ats_greenhouse", "ats_lever", "ats_other"}
        return "ats_external" if import_source in live_sync else "ats_import"

    @staticmethod
    def _map_source_to_system_slug(import_source: str) -> str:
        """Map ImportSource enum value to source_system slug (Task #435).

        Used by analytics.py:_classify_job_lifecycle_stage to land the
        vacancy in the 'ats_importada' lifecycle stage on the Recrutar page.

        ATS-specific imports map to their canonical slug (gupy, pandape,
        greenhouse). Generic imports (spreadsheet, manual_upload, api_import,
        hris_*) fall through to 'ats_other' (catch-all).
        """
        slug_map = {
            "ats_gupy": "gupy",
            "ats_pandape": "pandape",
            "ats_greenhouse": "greenhouse",
            # ats_lever, ats_other -> 'ats_other'
        }
        return slug_map.get(import_source, "ats_other")

    async def _mirror_to_job_vacancy(
        self,
        db: AsyncSession,
        company_id: UUID,
        imported_jd: ImportedJobDescription,
        import_source: str,
    ) -> None:
        """Create JobVacancy row mirroring an ImportedJobDescription.

        Phase 4H: ATS-imported vagas must appear in job_vacancies so the
        Vagas page rail can filter by source='ats_import'. Idempotent:
        skips if JobVacancy with same (company_id, external_id, source) exists.

        FAIL-CLOSED on missing company_id (multi-tenancy enforcement).
        Caller wraps in try/except for fail-open behavior.
        """
        if not company_id:
            raise ValueError(
                "company_id required for JobVacancy mirror (multi-tenancy enforcement)"
            )

        from lia_models.job_vacancy import JobVacancy
        from sqlalchemy import text as sa_text

        vacancy_source = self._map_source_to_vacancy(import_source)

        # Idempotency: skip if external_id already mirrored for this source.
        # Uses raw SQL with `additional_data->>'external_id'` since the column
        # is JSON (not JSONB) — `.astext` only works on JSONB.
        if imported_jd.external_id:
            existing_check = await db.execute(
                sa_text(
                    "SELECT 1 FROM job_vacancies "
                    "WHERE company_id = :cid "
                    "AND source = :src "
                    "AND additional_data->>'external_id' = :ext_id "
                    "LIMIT 1"
                ),
                {
                    "cid": str(company_id),
                    "src": vacancy_source,
                    "ext_id": imported_jd.external_id,
                },
            )
            if existing_check.scalar_one_or_none() is not None:
                logger.info(
                    "[JDImport] JobVacancy mirror exists (external_id=%s) — skip",
                    imported_jd.external_id,
                )
                return

        else:
            # Dedup by title for imports without external_id (manual uploads)
            # ADR-001-EXEMPT: cross-repo query; no canonical repository covers
            # job_vacancies title-dedup without an external_id anchor.
            title_check = await db.execute(
                sa_text(
                    "SELECT 1 FROM job_vacancies "
                    "WHERE company_id = :cid "
                    "AND title = :title "
                    "AND status = 'Rascunho' "
                    "AND created_at > NOW() - INTERVAL '24 hours' "
                    "LIMIT 1"
                ),
                {"cid": str(company_id), "title": imported_jd.title},
            )
            if title_check.scalar_one_or_none() is not None:
                logger.info(
                    "[JDImport] Duplicate title (no external_id) \u2014 skip: %s",
                    imported_jd.title,
                )
                return

        salary_range = None
        if imported_jd.salary_min is not None or imported_jd.salary_max is not None:
            salary_range = {
                "min": float(imported_jd.salary_min) if imported_jd.salary_min else None,
                "max": float(imported_jd.salary_max) if imported_jd.salary_max else None,
                "currency": imported_jd.salary_currency or "BRL",
            }

        # Phase 4J — populate fields for analytics.py lifecycle classifier:
        # _classify_job_lifecycle_stage returns 'ats_importada' when:
        #   _job_is_imported_from_ats(job) AND status=='Rascunho'
        # Triggers via source_system slug OR additional_data["imported_from_ats"].
        # We set BOTH for defense-in-depth.
        source_system_slug = self._map_source_to_system_slug(import_source)

        # T-1166 — separate responsibilities from requirements at mirror time.
        # `imported_job_descriptions` already keeps them in distinct columns
        # (`responsibilities` ARRAY vs `requirements_mandatory` ARRAY); the old
        # mirror dropped both on the floor, which (combined with the missing
        # `job_vacancies.responsibilities` column, now fixed in migration 132)
        # is why the JD edit panel showed tech skills under "RESPONSABILIDADES".
        responsibilities_list = list(imported_jd.responsibilities or [])
        requirements_list = list(imported_jd.requirements_mandatory or [])

        vacancy = JobVacancy(
            company_id=str(company_id),
            title=imported_jd.job_title_original or "Vaga importada",
            department=imported_jd.department,
            location=imported_jd.location,
            work_model=imported_jd.work_model,
            employment_type=imported_jd.employment_type,
            seniority_level=imported_jd.seniority,
            description=imported_jd.description_raw,
            responsibilities=responsibilities_list,
            requirements=requirements_list,
            salary_range=salary_range,
            benefits=imported_jd.benefits or [],
            manager=imported_jd.hiring_manager,
            manager_email=imported_jd.hiring_manager_email,
            recruiter=imported_jd.recruiter,
            # Status MUST be 'Rascunho' for classifier to assign 'ats_importada'.
            # imported_jd.job_status from external ATS may be 'Active'/'Open'/etc;
            # we override to start fresh in our lifecycle (recruiter then advances).
            status="Rascunho",
            stage="Planejamento",
            source=vacancy_source,                # Phase 4H: 'ats_import' | 'ats_external'
            source_system=source_system_slug,     # Phase 4J: Task #435 lifecycle slug
            wizard_stage=None,                    # only wizard-source vagas have this
            additional_data={
                "external_id": imported_jd.external_id,
                "import_source": import_source,
                "imported_jd_id": str(imported_jd.id),
                "import_batch_id": str(imported_jd.import_batch_id) if imported_jd.import_batch_id else None,
                # Phase 4J — flag for _job_is_imported_from_ats heuristic.
                # Defense-in-depth: even if source_system column read fails,
                # this flag guarantees classifier returns 'ats_importada'.
                "imported_from_ats": True,
                # Original status from ATS preserved for debugging / future restore
                "original_external_status": imported_jd.job_status,
            },
        )
        db.add(vacancy)
        await db.commit()
        await db.refresh(vacancy)
        logger.info(
            "[JDImport] JobVacancy mirror created id=%s source=%s jd=%s",
            vacancy.id, vacancy_source, imported_jd.id,
        )

    async def import_batch_jds(
        self,
        db: AsyncSession,
        company_id: UUID,
        jds_data: list[dict[str, Any]],
        source: str = ImportSource.MANUAL_UPLOAD.value,
        created_by: str | None = None
    ) -> ImportBatch:
        """
        Import multiple job descriptions in a batch.
        
        Returns batch with progress tracking.
        """
        batch = await self.create_import_batch(
            db=db,
            company_id=company_id,
            source=source,
            total_records=len(jds_data),
            created_by=created_by
        )
        
        batch.status = ImportStatus.PROCESSING.value
        
        for jd_data in jds_data:
            try:
                await self.import_jd(
                    db=db,
                    company_id=company_id,
                    jd_data=jd_data,
                    source=source,
                    batch_id=batch.id,
                    parse_immediately=True
                )
                batch.successful_records += 1
            except Exception as e:
                batch.failed_records += 1
                batch.errors = (batch.errors or []) + [{
                    "jd_title": jd_data.get("title", "unknown"),
                    "error": str(e)
                }]
                logger.error(f"Failed to import JD: {e}")
            
            batch.processed_records += 1
        
        batch.status = (
            ImportStatus.COMPLETED.value 
            if batch.failed_records == 0 
            else ImportStatus.PARTIALLY_COMPLETED.value
        )
        batch.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(batch)
        
        await self._update_skill_catalog(db, company_id, batch.id)
        
        return batch


    def _compute_quality_score(self, jd_data: dict) -> float:
        """Score 0-1. Only jobs with score >= 0.65 feed the salary benchmark.

        Weights: title (0.25) + salary_min (0.30) + department (0.15) + seniority (0.15) + skills (0.15)
        """
        score = 0.0
        if jd_data.get("title"):        score += 0.25
        if jd_data.get("salary_min"):   score += 0.30
        if jd_data.get("department"):   score += 0.15
        if jd_data.get("seniority"):    score += 0.15
        if jd_data.get("skills") or jd_data.get("required_skills"):  score += 0.15
        return round(score, 2)

    def parse_jd(self, jd: ImportedJobDescription) -> ParsedJD:
        """
        Parse a job description and extract structured data.
        
        Uses NLU patterns to extract:
        - Normalized title
        - Seniority level
        - Skills (technical and behavioral)
        - Responsibilities
        - Benefits
        """
        title = jd.job_title_original or ""
        description = jd.description_raw or ""
        responsibilities_text = jd.responsibilities_raw or ""
        full_text = f"{title} {description} {responsibilities_text}".lower()
        
        title_normalized = self._normalize_title(title)
        
        seniority, seniority_confidence = self._detect_seniority(title, description)
        
        technical_skills = self._extract_technical_skills(full_text)
        
        behavioral = self._extract_behavioral_competencies(full_text)
        
        responsibilities = self._extract_responsibilities(responsibilities_text or description)
        
        benefits = self._extract_benefits(description)
        
        parsing_confidence = self._calculate_parsing_confidence(
            has_title=bool(title),
            has_seniority=seniority is not None,
            skills_count=len(technical_skills),
            responsibilities_count=len(responsibilities),
        )
        
        return ParsedJD(
            title_normalized=title_normalized,
            seniority=seniority or jd.seniority,
            seniority_confidence=seniority_confidence,
            department=jd.department,
            employment_type=jd.employment_type,
            work_model=jd.work_model,
            responsibilities=responsibilities,
            technical_skills=technical_skills,
            behavioral_competencies=behavioral,
            salary_min=jd.salary_min,
            salary_max=jd.salary_max,
            benefits=benefits or jd.benefits or [],
            parsing_confidence=parsing_confidence
        )

    def _normalize_title(self, title: str) -> str:
        """Normalize job title for matching."""
        normalized = title.lower().strip()
        
        for seniority_terms in self.SENIORITY_PATTERNS.values():
            for term in seniority_terms:
                normalized = re.sub(rf'\b{re.escape(term)}\b', '', normalized, flags=re.IGNORECASE)
        
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        normalized = re.sub(r'^[\s\-\|]+|[\s\-\|]+$', '', normalized)
        
        return normalized.title()

    def _detect_seniority(self, title: str, description: str) -> tuple[str | None, float]:
        """Detect seniority level from title and description."""
        text = f"{title} {description}".lower()
        
        for seniority, patterns in self.SENIORITY_PATTERNS.items():
            for pattern in patterns:
                if pattern in title.lower():
                    return seniority, 0.95
        
        for seniority, patterns in self.SENIORITY_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    return seniority, 0.7
        
        return None, 0.0

    def _extract_technical_skills(self, text: str) -> list[dict[str, Any]]:
        """Extract technical skills from text."""
        skills = []
        seen = set()
        
        for category, category_skills in self.SKILL_CATEGORIES.items():
            for skill in category_skills:
                if skill.lower() in text and skill.lower() not in seen:
                    level = self._infer_skill_level(text, skill)
                    skills.append({
                        "name": skill,
                        "category": category,
                        "level": level,
                        "required": "obrigatório" in text or "required" in text,
                    })
                    seen.add(skill.lower())
        
        skill_pattern = r'(?:conhecimento|experiência|habilidade)s?\s+(?:em|com|de)\s+([A-Za-z0-9\s,/]+)'
        matches = re.findall(skill_pattern, text, re.IGNORECASE)
        for match in matches:
            for skill in re.split(r'[,/]', match):
                skill = skill.strip()
                if len(skill) > 2 and skill.lower() not in seen:
                    skills.append({
                        "name": skill,
                        "category": "other",
                        "level": "intermediate",
                        "required": False,
                    })
                    seen.add(skill.lower())
        
        return skills[:20]

    def _infer_skill_level(self, text: str, skill: str) -> str:
        """Infer skill level from context."""
        context_window = 100
        skill_lower = skill.lower()
        pos = text.find(skill_lower)
        if pos == -1:
            return "intermediate"
        
        context = text[max(0, pos-context_window):min(len(text), pos+context_window)]
        
        if any(term in context for term in ["avançado", "advanced", "expert", "profundo", "sólido"]):
            return "advanced"
        elif any(term in context for term in ["básico", "basic", "noções", "desejável"]):
            return "basic"
        else:
            return "intermediate"

    def _extract_behavioral_competencies(self, text: str) -> list[dict[str, Any]]:
        """Extract behavioral competencies from text."""
        competencies = []
        seen = set()
        
        for keyword in self.BEHAVIORAL_KEYWORDS:
            if keyword in text.lower() and keyword not in seen:
                name = keyword.title().replace("ção", "ção").replace("cão", "ção")
                competencies.append({
                    "name": name,
                    "justification": "Identificado na descrição da vaga"
                })
                seen.add(keyword)
        
        return competencies[:10]

    def _extract_responsibilities(self, text: str) -> list[str]:
        """Extract responsibilities from text."""
        if not text:
            return []
        
        bullet_pattern = r'(?:^|\n)\s*(?:[-•*]|\d+[.\)])\s*(.+?)(?=\n|$)'
        matches = re.findall(bullet_pattern, text, re.MULTILINE)
        
        if matches:
            responsibilities = [m.strip() for m in matches if len(m.strip()) > 10]
        else:
            sentences = re.split(r'[.;]\s+', text)
            responsibilities = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return responsibilities[:15]

    def _extract_benefits(self, text: str) -> list[str]:
        """Extract benefits from text."""
        benefits = []
        text_lower = text.lower()
        
        for keyword in self.BENEFIT_KEYWORDS:
            if keyword in text_lower and keyword not in [b.lower() for b in benefits]:
                benefits.append(keyword.title())
        
        return benefits[:15]

    def _calculate_parsing_confidence(
        self,
        has_title: bool,
        has_seniority: bool,
        skills_count: int,
        responsibilities_count: int
    ) -> float:
        """Calculate overall parsing confidence."""
        confidence = 0.3
        
        if has_title:
            confidence += 0.2
        if has_seniority:
            confidence += 0.1
        if skills_count >= 3:
            confidence += 0.2
        elif skills_count >= 1:
            confidence += 0.1
        if responsibilities_count >= 3:
            confidence += 0.2
        elif responsibilities_count >= 1:
            confidence += 0.1
        
        return min(confidence, 0.95)

    def _apply_parsed_data(self, jd: ImportedJobDescription, parsed: ParsedJD) -> None:
        """Apply parsed data to the imported JD."""
        jd.job_title_normalized = parsed.title_normalized
        jd.seniority = parsed.seniority
        jd.seniority_confidence = parsed.seniority_confidence
        jd.responsibilities = parsed.responsibilities
        jd.technical_skills = parsed.technical_skills
        jd.behavioral_competencies = parsed.behavioral_competencies
        jd.benefits = parsed.benefits or jd.benefits
        jd.parsing_confidence = parsed.parsing_confidence
        jd.processing_status = ProcessingStatus.PARSED.value
        jd.processed_at = datetime.utcnow()

    async def _update_skill_catalog(
        self,
        db: AsyncSession,
        company_id: UUID,
        batch_id: UUID
    ) -> None:
        """Update company skill catalog from imported JDs."""
        stmt = select(ImportedJobDescription).where(
            and_(
                ImportedJobDescription.company_id == company_id,
                ImportedJobDescription.import_batch_id == batch_id,
                ImportedJobDescription.processing_status == ProcessingStatus.PARSED.value,
                ImportedJobDescription.is_used_for_learning.is_(True),  # FairnessGuard gate
            )
        )
        result = await db.execute(stmt)
        jds = result.scalars().all()
        
        skill_freq: dict[str, dict] = {}
        
        for jd in jds:
            for skill_data in (jd.technical_skills or []):
                skill_name = skill_data.get("name", "").lower()
                if not skill_name:
                    continue
                
                if skill_name not in skill_freq:
                    skill_freq[skill_name] = {
                        "original_name": skill_data.get("name"),
                        "type": "technical",
                        "count": 0,
                        "titles": set(),
                        "departments": set(),
                        "seniorities": set(),
                        "jd_ids": set(),
                    }
                
                skill_freq[skill_name]["count"] += 1
                if jd.job_title_normalized:
                    skill_freq[skill_name]["titles"].add(jd.job_title_normalized)
                if jd.department:
                    skill_freq[skill_name]["departments"].add(jd.department)
                if jd.seniority:
                    skill_freq[skill_name]["seniorities"].add(jd.seniority)
                skill_freq[skill_name]["jd_ids"].add(str(jd.id))
        
        for skill_name, data in skill_freq.items():
            existing = await db.execute(
                select(ClientSkillCatalog).where(
                    and_(
                        ClientSkillCatalog.company_id == company_id,
                        ClientSkillCatalog.skill_name_normalized == skill_name
                    )
                )
            )
            catalog_skill = existing.scalar_one_or_none()
            
            if catalog_skill:
                catalog_skill.frequency += data["count"]
                catalog_skill.associated_titles = list(
                    set(catalog_skill.associated_titles or []) | data["titles"]
                )
                catalog_skill.associated_departments = list(
                    set(catalog_skill.associated_departments or []) | data["departments"]
                )
                catalog_skill.source_jds = list(
                    set(catalog_skill.source_jds or []) | data["jd_ids"]
                )
            else:
                new_skill = ClientSkillCatalog(
                    company_id=company_id,
                    skill_name=data["original_name"],
                    skill_name_normalized=skill_name,
                    skill_type=data["type"],
                    frequency=data["count"],
                    associated_titles=list(data["titles"]),
                    associated_departments=list(data["departments"]),
                    associated_seniorities=list(data["seniorities"]),
                    source_jds=list(data["jd_ids"]),
                )
                db.add(new_skill)
        
        await db.commit()

    async def get_import_stats(
        self,
        db: AsyncSession,
        company_id: UUID
    ) -> dict[str, Any]:
        """Get import statistics for a company."""
        jd_count = await db.execute(
            select(func.count()).select_from(ImportedJobDescription).where(
                ImportedJobDescription.company_id == company_id
            )
        )
        
        skill_count = await db.execute(
            select(func.count()).select_from(ClientSkillCatalog).where(
                ClientSkillCatalog.company_id == company_id
            )
        )
        
        batch_result = await db.execute(
            select(ImportBatch).where(
                ImportBatch.company_id == company_id
            ).order_by(ImportBatch.created_at.desc()).limit(5)
        )
        recent_batches = batch_result.scalars().all()
        
        return {
            "total_jds_imported": jd_count.scalar() or 0,
            "skills_in_catalog": skill_count.scalar() or 0,
            "recent_imports": [b.to_dict() for b in recent_batches],
        }


jd_import_service = JDImportService()


def get_jd_import_service() -> "JDImportService":
    return jd_import_service


def _strip_meta(p: dict) -> dict:
    return {k: v for k, v in p.items() if not k.startswith("_")}


async def import_job_description(**params):
    """Wrapper para o chat. Delega para JDImportService.import_jd."""
    return await jd_import_service.import_jd(**_strip_meta(params))
