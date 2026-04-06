"""
Route service facade for candidate search and sourcing.
Encapsulates business logic from API routes (app/api/v1/candidate_search.py) for portability.
"""
import hashlib
import logging
import re
import unicodedata
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    normalized = unicodedata.normalize('NFKD', name.lower())
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    normalized = re.sub(r'[^a-z\s]', '', normalized)
    normalized = ' '.join(normalized.split())
    return normalized


def _generate_fingerprint(name: str, linkedin_url: str | None = None, email: str | None = None) -> str:
    parts = [_normalize_name(name)]
    if linkedin_url:
        linkedin_id = linkedin_url.rstrip('/').split('/')[-1].lower()
        parts.append(f"li:{linkedin_id}")
    if email:
        parts.append(f"email:{email.lower()}")
    fingerprint_str = "|".join(sorted(parts))
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]


def _get_match_label(score: float) -> str:
    if score >= 85:
        return "Exceeds"
    elif score >= 60:
        return "Meets"
    elif score >= 35:
        return "Partial"
    return "Missing"


class CandidateSearchRouteService:
    """Encapsulates business logic from candidate search API routes."""

    async def search_candidates_unified(
        self,
        db: AsyncSession,
        query: str,
        thread_id: str | None = None,
        search_spec: dict[str, Any] | None = None,
        search_local: bool = True,
        search_pearch: bool = False,
        pearch_type: str = "fast",
        local_limit: int = 50,
        pearch_limit: int = 20,
        show_emails: bool = False,
        show_phone_numbers: bool = False,
        job_vacancy_id: str | None = None,
        job_id: str | None = None,
        exclude_candidate_ids: list[str] | None = None,
        include_discovered: bool = False,
    ) -> dict[str, Any]:
        """Search candidates using hybrid strategy (local DB + Pearch AI).

        Extracted from POST /candidates (lines 569-669).
        NOTE: Delegates to pearch_service.hybrid_search() for the actual search execution.
        This facade adds rubric evaluation, expansion recommendations, and scoring logic.

        Returns:
            Dict with keys: query, thread_id, candidates, local_count, pearch_count,
            total_count, credits_remaining, search_time_seconds, warning_message,
            can_load_more, should_expand_to_global, expansion_message, high_adherence_count
        """
        from app.domains.sourcing.services.pearch_service import HybridSearchRequest, SearchType, pearch_service

        hybrid_request = HybridSearchRequest(
            query=query,
            thread_id=thread_id,
            search_spec=search_spec,
            search_local_first=search_local,
            include_pearch=search_pearch,
            pearch_type=SearchType(pearch_type) if pearch_type in ["fast", "pro"] else SearchType.FAST,
            local_limit=local_limit,
            pearch_limit=pearch_limit,
            show_emails=show_emails,
            show_phone_numbers=show_phone_numbers,
            job_vacancy_id=job_vacancy_id,
            exclude_candidate_ids=exclude_candidate_ids,
            include_discovered=include_discovered,
        )

        result = await pearch_service.hybrid_search(db, hybrid_request)

        candidates: list[dict[str, Any]] = []
        for profile in result.local_candidates:
            candidates.append({"profile": profile, "source": "local"})
        for profile in result.pearch_candidates:
            candidates.append({"profile": profile, "source": "pearch"})

        if job_id and candidates:
            requirements = await self._get_job_requirements(db, job_id)
            if requirements:
                logger.info(f"Evaluating {len(candidates)} candidates with rubrics for job_id={job_id}")
                candidates = await self._evaluate_candidates_with_rubrics(candidates, requirements)

        scored_candidates = []
        for c in candidates:
            c.get("rubric_score")
            scored_candidates.append(c)

        high_adherence_count = sum(
            1 for c in scored_candidates
            if c.get("source") == "local" and c.get("rubric_score") is not None and c.get("rubric_score", 0) >= 60.0
        )

        local_only_count = sum(1 for c in scored_candidates if c.get("source") == "local")
        should_expand = (
            local_only_count < 25
            and high_adherence_count < int(local_only_count * 0.6)
            and not search_pearch
        )

        expansion_message = None
        if should_expand:
            if local_only_count == 0:
                expansion_message = "Nenhum candidato encontrado no banco local. Recomendamos expandir para busca global (Pearch)."
            elif high_adherence_count < 10:
                expansion_message = f"Encontrados apenas {high_adherence_count} candidatos com aderência >= 60%. Considere expandir para busca global."
            else:
                expansion_message = f"Pool local limitado ({local_only_count} candidatos). Busca global pode encontrar mais perfis adequados."

        return {
            "query": result.query,
            "thread_id": result.thread_id,
            "candidates": scored_candidates,
            "local_count": result.local_count,
            "pearch_count": result.pearch_count,
            "total_count": result.total_count,
            "credits_remaining": result.pearch_credits_remaining,
            "search_time_seconds": (result.local_search_time or 0) + (result.pearch_search_time or 0),
            "warning_message": result.warning_message,
            "can_load_more": result.pearch_count >= pearch_limit,
            "should_expand_to_global": should_expand,
            "expansion_message": expansion_message,
            "high_adherence_count": high_adherence_count,
        }

    async def get_candidate_scoring(
        self,
        db: AsyncSession,
        candidate_id: str,
        job_id: str,
    ) -> dict[str, Any]:
        """Evaluate a single candidate against job requirements using rubric scoring.

        Extracted from POST /evaluate-for-job (lines 672-813) — single candidate path.
        Looks up candidate in main table or staging table, then evaluates with rubrics.

        Returns:
            Dict with keys: candidate_id, rubric_score, rubric_match_label,
            rubric_evaluated, error
        """
        from app.domains.cv_screening.services.rubric_evaluation_service import rubric_evaluation_service

        requirements = await self._get_job_requirements(db, job_id)
        if not requirements:
            return {
                "candidate_id": candidate_id,
                "rubric_evaluated": False,
                "error": "Nenhum requisito cadastrado para esta vaga",
            }

        candidate_data = await self._load_candidate_data(db, candidate_id)
        if not candidate_data:
            return {
                "candidate_id": candidate_id,
                "rubric_evaluated": False,
                "error": "Candidato não encontrado",
            }

        try:
            eval_result = await rubric_evaluation_service.evaluate_candidate(
                candidate_data=candidate_data,
                requirements=requirements,
            )
            return {
                "candidate_id": candidate_id,
                "rubric_score": eval_result.score,
                "rubric_match_label": _get_match_label(eval_result.score),
                "rubric_evaluated": True,
            }
        except Exception as e:
            logger.warning(f"Failed to evaluate candidate {candidate_id}: {e}")
            return {
                "candidate_id": candidate_id,
                "rubric_evaluated": False,
                "error": str(e),
            }

    async def evaluate_candidates_batch(
        self,
        db: AsyncSession,
        candidate_ids: list[str],
        job_id: str,
    ) -> dict[str, Any]:
        """Evaluate multiple candidates against job requirements in batch.

        Extracted from POST /evaluate-for-job (lines 672-813).

        Returns:
            Dict with keys: job_id, total_candidates, evaluated_count,
            failed_count, results
        """
        requirements = await self._get_job_requirements(db, job_id)
        if not requirements:
            return {
                "job_id": job_id,
                "total_candidates": len(candidate_ids),
                "evaluated_count": 0,
                "failed_count": len(candidate_ids),
                "results": [
                    {"candidate_id": cid, "rubric_evaluated": False, "error": "Nenhum requisito cadastrado para esta vaga"}
                    for cid in candidate_ids
                ],
            }

        results: list[dict[str, Any]] = []
        evaluated_count = 0
        failed_count = 0

        for candidate_id in candidate_ids:
            scoring = await self.get_candidate_scoring(db, candidate_id, job_id)
            results.append(scoring)
            if scoring.get("rubric_evaluated"):
                evaluated_count += 1
            else:
                failed_count += 1

        return {
            "job_id": job_id,
            "total_candidates": len(candidate_ids),
            "evaluated_count": evaluated_count,
            "failed_count": failed_count,
            "results": results,
        }

    async def import_pearch_candidates(
        self,
        db: AsyncSession,
        candidates_data: list[dict[str, Any]],
        source_search_query: str | None,
        company_id: UUID,
    ) -> dict[str, Any]:
        """Import candidates from Pearch search into staging table.

        Extracted from POST /candidates/import (lines 844-1038).
        Imports to external_candidate_profiles (staging), NOT the main candidates table.
        Handles deduplication via fingerprint hashing.

        Returns:
            Dict with keys: imported_count, skipped_count, updated_count,
            imported_ids, skipped_ids, mapping, message
        """
        import uuid as uuid_lib

        from app.models.candidate import Candidate, ExternalCandidateProfile

        imported_ids: list[str] = []
        skipped_ids: list[str] = []
        updated_ids: list[str] = []
        id_mappings: list[dict[str, str]] = []

        for candidate_dto in candidates_data:
            pearch_id = candidate_dto.get("pearch_id")
            name = candidate_dto.get("name", "")
            linkedin_url = candidate_dto.get("linkedin_url")
            email = candidate_dto.get("email")
            phone = candidate_dto.get("phone")

            fingerprint = _generate_fingerprint(name, linkedin_url, email)

            existing_in_main = await db.execute(
                select(Candidate).where(
                    or_(
                        Candidate.pearch_profile_id == pearch_id,
                        Candidate.linkedin_url == linkedin_url,
                    )
                ).limit(1)
            )
            existing_candidate = existing_in_main.scalars().first()
            if existing_candidate:
                skipped_ids.append(pearch_id)
                id_mappings.append({"pearch_id": pearch_id, "local_id": str(existing_candidate.id)})
                continue

            staging_filters = [ExternalCandidateProfile.source_profile_id == pearch_id]
            if linkedin_url:
                staging_filters.append(ExternalCandidateProfile.linkedin_url == linkedin_url)
            staging_filters.append(ExternalCandidateProfile.fingerprint_hash == fingerprint)

            existing_in_staging = await db.execute(
                select(ExternalCandidateProfile).where(
                    ExternalCandidateProfile.company_id == company_id,
                    or_(*staging_filters),
                ).limit(1)
            )
            existing_profile = existing_in_staging.scalars().first()

            if existing_profile:
                updated = False
                if email and not existing_profile.email:
                    existing_profile.email = email
                    existing_profile.has_email = True
                    existing_profile.contact_revealed = True
                    updated = True
                if phone and not existing_profile.phone:
                    existing_profile.phone = phone
                    existing_profile.has_phone = True
                    existing_profile.contact_revealed = True
                    updated = True
                if updated:
                    updated_ids.append(pearch_id)
                else:
                    skipped_ids.append(pearch_id)
                id_mappings.append({"pearch_id": pearch_id, "local_id": str(existing_profile.id)})
                continue

            location_city, location_state, location_country = None, None, None
            location = candidate_dto.get("location")
            if location:
                parts = [p.strip() for p in location.split(",")]
                if len(parts) >= 1:
                    location_city = parts[0]
                if len(parts) >= 2:
                    location_state = parts[1]
                if len(parts) >= 3:
                    location_country = parts[2]

            name_parts = name.split(' ', 1)
            first_name = candidate_dto.get("first_name") or (name_parts[0] if name_parts else None)
            last_name = candidate_dto.get("last_name") or (name_parts[1] if len(name_parts) > 1 else None)

            experiences_snapshot = []
            for exp in candidate_dto.get("experiences", []):
                exp_dict = exp if isinstance(exp, dict) else {}
                experiences_snapshot.append({
                    "company_name": exp_dict.get("company_name"),
                    "company_linkedin_url": exp_dict.get("company_linkedin_url"),
                    "company_domain": exp_dict.get("company_domain"),
                    "title": exp_dict.get("title"),
                    "start_date": exp_dict.get("start_date"),
                    "end_date": exp_dict.get("end_date"),
                    "duration_years": exp_dict.get("duration_years"),
                    "is_current": exp_dict.get("is_current"),
                    "description": exp_dict.get("description"),
                    "location": exp_dict.get("location"),
                    "industries": exp_dict.get("industries", []),
                    "company_size": exp_dict.get("company_size"),
                    "company_size_range": exp_dict.get("company_size_range"),
                    "technologies": exp_dict.get("technologies", []),
                    "is_startup": exp_dict.get("is_startup"),
                    "company_founded_year": exp_dict.get("company_founded_year"),
                    "company_annual_revenue": exp_dict.get("company_annual_revenue"),
                    "company_followers_count": exp_dict.get("company_followers_count"),
                    "company_keywords": exp_dict.get("company_keywords", []),
                })

            new_id = uuid_lib.uuid4()
            skills = candidate_dto.get("skills", [])
            expertise = candidate_dto.get("expertise", [])
            languages = candidate_dto.get("languages")
            yoe = candidate_dto.get("years_of_experience")

            profile = ExternalCandidateProfile(
                id=new_id,
                company_id=company_id,
                source="pearch",
                source_profile_id=pearch_id,
                linkedin_url=linkedin_url,
                raw_payload={"original_dto": candidate_dto, "source_search_query": source_search_query},
                name=name,
                normalized_name=_normalize_name(name),
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                avatar_url=candidate_dto.get("avatar_url"),
                headline=candidate_dto.get("headline"),
                summary=candidate_dto.get("summary"),
                current_title=candidate_dto.get("current_title"),
                current_company=candidate_dto.get("current_company"),
                location_city=location_city,
                location_state=location_state,
                location_country=location_country,
                location_raw=location,
                years_of_experience=int(yoe) if yoe else None,
                skills=skills[:50] if skills else [],
                expertise=expertise[:20] if expertise else [],
                languages={"items": languages} if languages else {},
                experiences_snapshot=experiences_snapshot,
                education_snapshot=candidate_dto.get("education"),
                is_open_to_work=candidate_dto.get("is_open_to_work"),
                is_decision_maker=candidate_dto.get("is_decision_maker"),
                is_top_universities=candidate_dto.get("is_top_universities"),
                has_email=bool(email),
                has_phone=bool(phone),
                contact_revealed=bool(email or phone),
                fingerprint_hash=fingerprint,
                status="discovered",
                search_query=source_search_query,
            )
            db.add(profile)

            imported_ids.append(str(new_id))
            id_mappings.append({"pearch_id": pearch_id, "local_id": str(new_id)})

        await db.commit()

        return {
            "imported_count": len(imported_ids),
            "skipped_count": len(skipped_ids),
            "updated_count": len(updated_ids),
            "imported_ids": imported_ids,
            "skipped_ids": skipped_ids,
            "mapping": id_mappings,
            "message": f"Salvos {len(imported_ids)} candidatos descobertos em staging. {len(updated_ids)} atualizados. {len(skipped_ids)} já existiam.",
        }

    async def promote_candidate(
        self,
        db: AsyncSession,
        profile_id: str,
        company_id: UUID,
    ) -> dict[str, Any]:
        """Promote a discovered candidate from staging to main candidates table.

        Extracted from POST /candidates/promote/{profile_id} (lines 1051-1464).
        Handles merge with existing candidates or creation of new ones,
        including experience and education records.

        Returns:
            Dict with keys: success, message, candidate_id, profile_id,
            was_merged, merged_with_id
        """
        import uuid as uuid_lib

        from app.models.candidate import (
            Candidate,
            CandidateEducation,
            CandidateExperience,
            CandidateSource,
            ExternalCandidateProfile,
        )

        profile_result = await db.execute(
            select(ExternalCandidateProfile).where(ExternalCandidateProfile.id == profile_id)
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            return {"success": False, "error": "Perfil não encontrado na staging"}

        if str(profile.company_id) != str(company_id):
            return {"success": False, "error": "Acesso negado: perfil pertence a outra empresa"}

        if profile.promoted_to_candidate_id:
            return {
                "success": True,
                "message": "Candidato já foi promovido anteriormente",
                "candidate_id": str(profile.promoted_to_candidate_id),
                "profile_id": profile_id,
                "was_merged": False,
            }

        existing_candidate = None
        if profile.linkedin_url:
            existing_result = await db.execute(
                select(Candidate).where(Candidate.linkedin_url == profile.linkedin_url)
            )
            existing_candidate = existing_result.scalar_one_or_none()

        if not existing_candidate and profile.source_profile_id:
            existing_result = await db.execute(
                select(Candidate).where(Candidate.pearch_profile_id == profile.source_profile_id)
            )
            existing_candidate = existing_result.scalar_one_or_none()

        if existing_candidate:
            updated_fields = self._merge_candidate_fields(existing_candidate, profile)

            existing_source = await db.execute(
                select(CandidateSource).where(
                    CandidateSource.candidate_id == existing_candidate.id,
                    CandidateSource.source == profile.source,
                )
            )
            if not existing_source.scalar_one_or_none():
                source = CandidateSource(
                    candidate_id=existing_candidate.id,
                    source=profile.source,
                    source_profile_id=profile.source_profile_id,
                    linkedin_url=profile.linkedin_url,
                    fingerprint_hash=profile.fingerprint_hash,
                    is_primary=False,
                    external_profile_id=profile.id,
                )
                db.add(source)

            profile.promoted_to_candidate_id = existing_candidate.id
            profile.promoted_at = datetime.utcnow()
            profile.status = "promoted_merged"

            await db.commit()

            return {
                "success": True,
                "message": f"Candidato mesclado com existente. Campos atualizados: {', '.join(updated_fields) if updated_fields else 'nenhum (dados já completos)'}",
                "candidate_id": str(existing_candidate.id),
                "profile_id": profile_id,
                "was_merged": True,
                "merged_with_id": str(existing_candidate.id),
            }

        new_candidate_id = uuid_lib.uuid4()
        raw_payload_raw = profile.raw_payload or {}
        raw_payload = raw_payload_raw.get("original_dto", raw_payload_raw)

        pearch_insights_data = {}
        if raw_payload.get("insights"):
            pearch_insights_data = {
                "overall_summary": raw_payload.get("insights", {}).get("overall_summary"),
                "query_insights": raw_payload.get("insights", {}).get("query_insights", []),
                "match_reasoning": raw_payload.get("match_reasoning"),
            }

        company_followers_count = None
        company_keywords = None
        experiences_data = raw_payload.get("experiences", [])
        if experiences_data:
            first_exp = experiences_data[0] if isinstance(experiences_data[0], dict) else {}
            company_info = first_exp.get("company_info", {})
            if company_info:
                company_followers_count = company_info.get("followers_count")
                company_keywords = company_info.get("keywords", [])
            if company_followers_count is None:
                company_followers_count = first_exp.get("company_followers_count")
            if not company_keywords:
                company_keywords = first_exp.get("company_keywords", [])

        candidate = Candidate(
            id=new_candidate_id,
            name=profile.name,
            email=profile.email,
            phone=profile.phone,
            linkedin_url=profile.linkedin_url,
            avatar_url=profile.avatar_url,
            current_title=profile.current_title,
            current_company=profile.current_company,
            seniority_level=profile.seniority_level,
            self_introduction=profile.summary,
            headline=profile.headline,
            location_city=profile.location_city,
            location_state=profile.location_state,
            location_country=profile.location_country,
            years_of_experience=profile.years_of_experience,
            technical_skills=profile.skills or [],
            expertise=profile.expertise or [],
            languages=profile.languages or {},
            source="pearch",
            pearch_profile_id=profile.source_profile_id,
            is_open_to_work=profile.is_open_to_work,
            is_decision_maker=profile.is_decision_maker,
            is_top_universities=profile.is_top_universities,
            is_hiring=raw_payload.get("is_hiring"),
            linkedin_followers_count=raw_payload.get("followers_count"),
            linkedin_connections_count=raw_payload.get("connections_count"),
            pearch_insights=pearch_insights_data,
            outreach_message=raw_payload.get("outreach_message") or getattr(profile, 'outreach_message', None),
            best_personal_email=getattr(profile, 'best_personal_email', None) or raw_payload.get("best_personal_email"),
            phone_types=getattr(profile, 'phone_types', None) or raw_payload.get("phone_types", {}),
            estimated_age=getattr(profile, 'estimated_age', None) or raw_payload.get("estimated_age"),
            middle_name=raw_payload.get("middle_name"),
            best_business_email=raw_payload.get("best_business_email"),
            personal_emails=raw_payload.get("personal_emails", []),
            business_emails=raw_payload.get("business_emails", []),
            company_followers_count=company_followers_count,
            company_keywords=company_keywords,
            status="new",
            is_active=True,
            additional_data={
                "promoted_from_staging": True,
                "original_profile_id": str(profile.id),
            },
        )
        db.add(candidate)

        source = CandidateSource(
            candidate_id=new_candidate_id,
            source=profile.source,
            source_profile_id=profile.source_profile_id,
            linkedin_url=profile.linkedin_url,
            fingerprint_hash=profile.fingerprint_hash,
            is_primary=True,
            external_profile_id=profile.id,
        )
        db.add(source)

        for idx, exp_data in enumerate(profile.experiences_snapshot or []):
            experience = CandidateExperience(
                candidate_id=new_candidate_id,
                company_name=exp_data.get("company_name", "Unknown"),
                company_linkedin_url=exp_data.get("company_linkedin_url"),
                company_domain=exp_data.get("company_domain"),
                title=exp_data.get("title"),
                start_date=exp_data.get("start_date"),
                end_date=exp_data.get("end_date"),
                duration_years=exp_data.get("duration_years"),
                is_current=exp_data.get("is_current", False),
                description=exp_data.get("description"),
                location=exp_data.get("location"),
                industries=exp_data.get("industries", []),
                company_size=exp_data.get("company_size"),
                company_size_range=exp_data.get("company_size_range"),
                technologies=exp_data.get("technologies", []),
                is_startup=exp_data.get("is_startup"),
                company_founded_year=exp_data.get("company_founded_year"),
                company_annual_revenue=exp_data.get("company_annual_revenue"),
                sequence_order=idx,
            )
            db.add(experience)

        for idx, edu_data in enumerate(profile.education_snapshot or []):
            education = CandidateEducation(
                candidate_id=new_candidate_id,
                institution=edu_data.get("school") or edu_data.get("institution"),
                degree=edu_data.get("degree"),
                field_of_study=edu_data.get("field_of_study") or edu_data.get("field"),
                start_date=edu_data.get("start_date"),
                end_date=edu_data.get("end_date"),
                is_completed=True if edu_data.get("end_date") else False,
                sequence_order=idx,
            )
            db.add(education)

        profile.promoted_to_candidate_id = new_candidate_id
        profile.promoted_at = datetime.utcnow()
        profile.status = "promoted"

        await db.commit()

        return {
            "success": True,
            "message": "Candidato promovido para a base principal com sucesso",
            "candidate_id": str(new_candidate_id),
            "profile_id": profile_id,
            "was_merged": False,
        }

    async def persist_revealed_contact(
        self,
        db: AsyncSession,
        pearch_id: str,
        candidate_name: str,
        email: str | None = None,
        phone: str | None = None,
        linkedin_url: str | None = None,
        current_title: str | None = None,
        current_company: str | None = None,
        avatar_url: str | None = None,
    ) -> dict[str, Any]:
        """Persist revealed contact data for a Pearch candidate.

        Extracted from POST /candidates/persist-revealed (lines 1487-1580).

        Returns:
            Dict with keys: success, message, candidate_id, is_new
        """
        import uuid as uuid_lib

        from app.models.candidate import Candidate

        existing = await db.execute(
            select(Candidate).where(Candidate.pearch_profile_id == pearch_id)
        )
        candidate = existing.scalar_one_or_none()

        if candidate:
            updated = False
            if email and not candidate.email:
                candidate.email = email
                updated = True
            if phone and not candidate.phone:
                candidate.phone = phone
                updated = True

            if updated:
                await db.commit()
                return {
                    "success": True,
                    "message": "Dados de contato atualizados no cadastro existente",
                    "candidate_id": str(candidate.id),
                    "is_new": False,
                }
            return {
                "success": True,
                "message": "Candidato já possui os dados de contato",
                "candidate_id": str(candidate.id),
                "is_new": False,
            }

        name_parts = candidate_name.split(' ', 1)
        name_parts[0] if name_parts else None
        new_candidate = Candidate(
            id=uuid_lib.uuid4(),
            name=candidate_name,
            email=email,
            phone=phone,
            linkedin_url=linkedin_url,
            current_title=current_title,
            current_company=current_company,
            avatar_url=avatar_url,
            pearch_profile_id=pearch_id,
            source="pearch",
            status="new",
            is_active=True,
        )
        db.add(new_candidate)
        await db.commit()

        return {
            "success": True,
            "message": "Novo candidato criado com dados de contato revelados",
            "candidate_id": str(new_candidate.id),
            "is_new": True,
        }

    async def get_search_suggestions(
        self,
        db: AsyncSession,
        query: str,
        company_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Get auto-complete suggestions based on query prefix.

        Provides suggestions from job titles, skills, and recent searches.

        Returns:
            Dict with keys: suggestions, source
        """
        from app.models.candidate import Candidate

        suggestions: list[str] = []

        if len(query) < 2:
            return {"suggestions": [], "source": "none"}

        search_term = f"%{query}%"
        titles_result = await db.execute(
            select(Candidate.current_title)
            .where(Candidate.current_title.ilike(search_term))
            .distinct()
            .limit(5)
        )
        for row in titles_result.scalars().all():
            if row and row not in suggestions:
                suggestions.append(row)

        skills_result = await db.execute(
            select(Candidate.technical_skills)
            .where(Candidate.technical_skills.isnot(None))
            .limit(100)
        )
        for skills_list in skills_result.scalars().all():
            if isinstance(skills_list, list):
                for skill in skills_list:
                    if isinstance(skill, str) and query.lower() in skill.lower() and skill not in suggestions:
                        suggestions.append(skill)
                        if len(suggestions) >= 10:
                            break
            if len(suggestions) >= 10:
                break

        return {"suggestions": suggestions[:10], "source": "database"}

    async def get_search_statistics(
        self,
        db: AsyncSession,
        company_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Get statistics and facets for the candidate search interface.

        Returns:
            Dict with keys: total_candidates, total_discovered,
            top_skills, top_titles, source_breakdown
        """
        from sqlalchemy import func as sqla_func

        from app.models.candidate import Candidate, ExternalCandidateProfile

        total_result = await db.execute(
            select(sqla_func.count(Candidate.id)).where(Candidate.is_active == True)
        )
        total_candidates = total_result.scalar() or 0

        discovered_query = select(sqla_func.count(ExternalCandidateProfile.id))
        if company_id:
            discovered_query = discovered_query.where(ExternalCandidateProfile.company_id == company_id)
        discovered_result = await db.execute(discovered_query)
        total_discovered = discovered_result.scalar() or 0

        source_result = await db.execute(
            select(
                Candidate.source,
                sqla_func.count(Candidate.id).label("count"),
            )
            .where(Candidate.is_active == True)
            .group_by(Candidate.source)
        )
        source_breakdown = {row.source: row.count for row in source_result.all()}

        return {
            "total_candidates": total_candidates,
            "total_discovered": total_discovered,
            "source_breakdown": source_breakdown,
        }

    def _merge_candidate_fields(self, existing_candidate: Any, profile: Any) -> list[str]:
        """Merge staging profile fields into existing candidate (only fills gaps).

        Returns list of updated field names.
        """
        updated_fields: list[str] = []
        if profile.email and not existing_candidate.email:
            existing_candidate.email = profile.email
            updated_fields.append("email")
        if profile.phone and not existing_candidate.phone:
            existing_candidate.phone = profile.phone
            updated_fields.append("phone")
        if profile.avatar_url and not existing_candidate.avatar_url:
            existing_candidate.avatar_url = profile.avatar_url
            updated_fields.append("avatar_url")
        if profile.summary and not existing_candidate.self_introduction:
            existing_candidate.self_introduction = profile.summary
            updated_fields.append("self_introduction")
        if profile.skills and not existing_candidate.technical_skills:
            existing_candidate.technical_skills = profile.skills
            updated_fields.append("technical_skills")

        raw_payload_raw = profile.raw_payload or {}
        raw_payload = raw_payload_raw.get("original_dto", raw_payload_raw)

        bool_fields = [
            ("is_open_to_work", ["is_open_to_work", "is_opentowork"]),
            ("is_decision_maker", ["is_decision_maker"]),
            ("is_top_universities", ["is_top_universities"]),
            ("is_hiring", ["is_hiring"]),
        ]
        for attr_name, payload_keys in bool_fields:
            for key in payload_keys:
                if key in raw_payload:
                    setattr(existing_candidate, attr_name, raw_payload[key])
                    updated_fields.append(attr_name)
                    break

        text_fields = [
            ("headline", "headline"),
            ("expertise", "expertise"),
            ("seniority_level", "seniority_level"),
            ("best_personal_email", "best_personal_email"),
            ("estimated_age", "estimated_age"),
            ("outreach_message", "outreach_message"),
            ("middle_name", "middle_name"),
            ("best_business_email", "best_business_email"),
        ]
        for attr_name, payload_key in text_fields:
            if payload_key in raw_payload:
                setattr(existing_candidate, attr_name, raw_payload.get(payload_key))
                updated_fields.append(attr_name)
            elif getattr(profile, attr_name, None) is not None:
                setattr(existing_candidate, attr_name, getattr(profile, attr_name))
                updated_fields.append(attr_name)

        if "personal_emails" in raw_payload:
            existing_candidate.personal_emails = raw_payload.get("personal_emails", [])
            updated_fields.append("personal_emails")
        if "business_emails" in raw_payload:
            existing_candidate.business_emails = raw_payload.get("business_emails", [])
            updated_fields.append("business_emails")

        if "insights" in raw_payload or getattr(profile, 'pearch_insights', None) is not None:
            raw_insights = raw_payload.get("insights", {})
            if raw_insights:
                existing_candidate.pearch_insights = {
                    "overall_summary": raw_insights.get("overall_summary"),
                    "query_insights": raw_insights.get("query_insights", []),
                    "match_reasoning": raw_payload.get("match_reasoning"),
                }
            elif getattr(profile, 'pearch_insights', None) is not None:
                existing_candidate.pearch_insights = profile.pearch_insights
            updated_fields.append("pearch_insights")

        return updated_fields

    async def _get_job_requirements(self, db: AsyncSession, job_id: str) -> list[Any] | None:
        """Fetch job requirements for rubric evaluation."""
        try:
            from app.domains.cv_screening.services.rubric_evaluation_service import JobRequirementCreate
            from app.models.job_vacancy import JobRequirement

            def _normalize_priority(priority: str | None) -> str:
                if not priority:
                    return "medium"
                p = priority.lower().strip()
                mapping = {
                    "alta": "high", "high": "high", "obrigatório": "high", "mandatory": "high",
                    "média": "medium", "medium": "medium", "importante": "medium",
                    "baixa": "low", "low": "low", "desejável": "low", "nice_to_have": "low",
                }
                return mapping.get(p, "medium")

            result = await db.execute(
                select(JobRequirement).where(JobRequirement.job_vacancy_id == UUID(job_id))
            )
            db_requirements = result.scalars().all()

            if not db_requirements:
                return None

            return [
                JobRequirementCreate(
                    requirement=req.requirement,
                    description=req.description,
                    priority=_normalize_priority(req.priority),
                    category=req.category,
                )
                for req in db_requirements
            ]
        except Exception as e:
            logger.warning(f"Failed to fetch job requirements for job_id={job_id}: {e}")
            return None

    async def _evaluate_candidates_with_rubrics(
        self, candidates: list[dict[str, Any]], requirements: list[Any]
    ) -> list[dict[str, Any]]:
        """Evaluate candidates using rubric service and update dicts in-place."""
        from app.domains.cv_screening.services.rubric_evaluation_service import rubric_evaluation_service

        for candidate in candidates:
            try:
                profile = candidate.get("profile")
                if not profile:
                    continue
                candidate_data = {
                    "id": getattr(profile, "id", None),
                    "name": getattr(profile, "name", None),
                    "current_title": getattr(profile, "current_title", None),
                    "current_company": getattr(profile, "current_company", None),
                    "years_of_experience": getattr(profile, "years_of_experience", None),
                    "skills": getattr(profile, "skills", []) or getattr(profile, "technical_skills", []),
                    "technical_skills": getattr(profile, "technical_skills", []) or getattr(profile, "skills", []),
                    "expertise": getattr(profile, "expertise", []),
                    "work_history": getattr(profile, "work_history", []),
                    "education": getattr(profile, "education", []),
                    "self_introduction": getattr(profile, "summary", None) or getattr(profile, "self_introduction", None),
                }
                eval_result = await rubric_evaluation_service.evaluate_candidate(
                    candidate_data=candidate_data,
                    requirements=requirements,
                )
                candidate["rubric_score"] = eval_result.score
                candidate["rubric_match_label"] = _get_match_label(eval_result.score)
                candidate["rubric_evaluated"] = True
            except Exception as e:
                logger.warning(f"Rubric evaluation failed for candidate: {e}")
                candidate["rubric_evaluated"] = False
        return candidates

    async def _load_candidate_data(self, db: AsyncSession, candidate_id: str) -> dict[str, Any] | None:
        """Load candidate data from main table or staging table."""
        from app.models.candidate import Candidate, ExternalCandidateProfile

        result = await db.execute(
            select(Candidate).where(Candidate.id == UUID(candidate_id))
        )
        candidate = result.scalar_one_or_none()

        if candidate:
            return {
                "id": str(candidate.id),
                "name": candidate.name,
                "current_title": candidate.current_title,
                "current_company": candidate.current_company,
                "years_of_experience": candidate.years_of_experience,
                "seniority_level": candidate.seniority_level,
                "technical_skills": candidate.technical_skills or [],
                "skills": candidate.technical_skills or [],
                "soft_skills": candidate.soft_skills or [],
                "certifications": candidate.certifications or [],
                "languages": candidate.languages or {},
                "work_history": candidate.work_history or [],
                "education": candidate.education or [],
                "resume_text": candidate.resume_text,
                "self_introduction": candidate.self_introduction,
                "expertise": candidate.expertise or [],
            }

        staging_result = await db.execute(
            select(ExternalCandidateProfile).where(ExternalCandidateProfile.id == UUID(candidate_id))
        )
        staging_candidate = staging_result.scalar_one_or_none()

        if staging_candidate:
            return {
                "id": str(staging_candidate.id),
                "name": staging_candidate.name,
                "current_title": staging_candidate.current_title,
                "current_company": staging_candidate.current_company,
                "years_of_experience": staging_candidate.years_of_experience,
                "seniority_level": staging_candidate.seniority_level,
                "skills": staging_candidate.skills or [],
                "technical_skills": staging_candidate.skills or [],
                "expertise": staging_candidate.expertise or [],
                "work_history": staging_candidate.experiences_snapshot or [],
                "education": staging_candidate.education_snapshot or [],
                "self_introduction": staging_candidate.summary,
            }

        return None


candidate_search_route_service = CandidateSearchRouteService()
