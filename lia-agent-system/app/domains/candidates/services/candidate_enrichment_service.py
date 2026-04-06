"""
Candidate Enrichment Service.
Enriches candidate data using Apify LinkedIn scrapers.
Supports MCP (Model Context Protocol) for simplified actor calls.
"""
import logging
import re
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.sourcing.services.apify_mcp_client import ApifyMCPClient
from app.models.candidate import Candidate, CandidateEducation, CandidateExperience

logger = logging.getLogger(__name__)

LINKEDIN_PROFILE_ACTOR = "dev_fusion/linkedin-profile-scraper"
LINKEDIN_PROFILE_ACTOR_ALT = "curious_coder/linkedin-profile-scraper"


class CandidateEnrichmentService:
    """
    Service for enriching candidate data from LinkedIn profiles using Apify.
    
    Supports two main actors:
    - dev_fusion/linkedin-profile-scraper: Includes email discovery (no cookies required)
    - curious_coder/linkedin-profile-scraper: Basic profile scraper
    
    Fields that can be enriched:
    - Basic: name, avatar_url, headline, current_title, current_company
    - Location: location_city, location_state, location_country
    - Skills: technical_skills, languages, certifications
    - Social: linkedin_followers_count, linkedin_connections_count, is_open_to_work
    - Contact: email, secondary_email, best_personal_email, best_business_email
    - Bio: self_introduction (summary)
    - Experience: CandidateExperience records
    - Education: CandidateEducation records
    """
    
    def __init__(self):
        self.mcp_client = ApifyMCPClient()
        self.use_email_discovery = True
    
    async def enrich_candidate(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        linkedin_url: str | None = None,
        include_experiences: bool = True,
        include_education: bool = True,
        include_email_discovery: bool = True
    ) -> dict[str, Any]:
        """
        Enrich a candidate's data from their LinkedIn profile.
        
        Args:
            db: Database session
            candidate_id: UUID of the candidate to enrich
            linkedin_url: LinkedIn profile URL (optional, uses candidate's if not provided)
            include_experiences: Whether to import work experience records
            include_education: Whether to import education records
            include_email_discovery: Whether to attempt email discovery
            
        Returns:
            Dict with enrichment results including updated fields and any errors
        """
        result = await db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            return {
                "success": False,
                "error": f"Candidate {candidate_id} not found",
                "fields_updated": []
            }
        
        profile_url = linkedin_url or candidate.linkedin_url
        
        if not profile_url:
            return {
                "success": False,
                "error": "No LinkedIn URL provided or found for candidate",
                "fields_updated": []
            }
        
        profile_url = self._normalize_linkedin_url(profile_url)
        
        logger.info(f"Starting LinkedIn enrichment for candidate {candidate_id} using URL: {profile_url}")
        
        try:
            actor_id = LINKEDIN_PROFILE_ACTOR if include_email_discovery else LINKEDIN_PROFILE_ACTOR_ALT
            
            profile_data = await self._scrape_linkedin_profile(profile_url, actor_id)
            
            if not profile_data or profile_data.get("error"):
                if actor_id == LINKEDIN_PROFILE_ACTOR:
                    logger.warning(f"Primary scraper failed, trying alternative: {profile_data.get('error')}")
                    profile_data = await self._scrape_linkedin_profile(profile_url, LINKEDIN_PROFILE_ACTOR_ALT)
                
                if not profile_data or profile_data.get("error"):
                    return {
                        "success": False,
                        "error": f"Failed to scrape LinkedIn profile: {profile_data.get('error', 'Unknown error')}",
                        "fields_updated": []
                    }
            
            updated_fields = await self._apply_enrichment(
                db, candidate, profile_data,
                include_experiences, include_education
            )
            
            await db.commit()
            
            logger.info(f"Enrichment completed for candidate {candidate_id}: {len(updated_fields)} fields updated")
            
            return {
                "success": True,
                "fields_updated": updated_fields,
                "experiences_added": profile_data.get("_experiences_added", 0),
                "education_added": profile_data.get("_education_added", 0),
                "source": actor_id
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Enrichment error for candidate {candidate_id}: {type(e).__name__}: {e}")
            return {
                "success": False,
                "error": str(e),
                "fields_updated": []
            }
    
    async def _scrape_linkedin_profile(self, linkedin_url: str, actor_id: str) -> dict[str, Any]:
        """
        Scrape a LinkedIn profile using Apify actor.
        
        Args:
            linkedin_url: LinkedIn profile URL
            actor_id: Apify actor ID to use
            
        Returns:
            Parsed profile data
        """
        try:
            input_data = {
                "urls": [linkedin_url],
                "minDelay": 2,
                "maxDelay": 5
            }
            
            if "dev_fusion" in actor_id:
                input_data["includeEmailDiscovery"] = True
            
            result = await self.mcp_client.call_actor(
                actor_id,
                input_data,
                wait_for_finish=True,
                timeout_secs=180
            )
            
            if isinstance(result, dict) and result.get("error"):
                return result
            
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            elif isinstance(result, dict):
                return result
            
            return {"error": "Empty result from LinkedIn scraper"}
            
        except Exception as e:
            logger.error(f"LinkedIn scrape error: {type(e).__name__}: {e}")
            return {"error": str(e)}
    
    async def _apply_enrichment(
        self,
        db: AsyncSession,
        candidate: Candidate,
        profile_data: dict[str, Any],
        include_experiences: bool,
        include_education: bool
    ) -> list[str]:
        """
        Apply enrichment data to candidate record.
        
        Args:
            db: Database session
            candidate: Candidate model instance
            profile_data: Data from LinkedIn scraper
            include_experiences: Whether to add experience records
            include_education: Whether to add education records
            
        Returns:
            List of field names that were updated
        """
        updated_fields = []
        
        field_mappings = {
            "name": ["firstName", "lastName"],
            "avatar_url": ["profilePicture", "profilePic", "picture", "avatar"],
            "headline": ["headline", "title"],
            "current_title": ["currentTitle", "title", "headline"],
            "current_company": ["currentCompany", "company"],
            "self_introduction": ["summary", "about", "bio"],
            "linkedin_url": ["linkedinUrl", "profileUrl", "url"],
        }
        
        if profile_data.get("firstName") and profile_data.get("lastName"):
            full_name = f"{profile_data['firstName']} {profile_data['lastName']}".strip()
            if full_name and (not candidate.name or candidate.name == ""):
                candidate.name = full_name
                updated_fields.append("name")
        
        for candidate_field, source_fields in field_mappings.items():
            if candidate_field == "name":
                continue
            
            current_value = getattr(candidate, candidate_field, None)
            if current_value:
                continue
            
            for source_field in source_fields:
                value = profile_data.get(source_field)
                if value:
                    setattr(candidate, candidate_field, value)
                    updated_fields.append(candidate_field)
                    break
        
        self._apply_location(candidate, profile_data, updated_fields)
        
        self._apply_skills(candidate, profile_data, updated_fields)
        
        self._apply_languages(candidate, profile_data, updated_fields)
        
        self._apply_certifications(candidate, profile_data, updated_fields)
        
        self._apply_social_metrics(candidate, profile_data, updated_fields)
        
        self._apply_contact_info(candidate, profile_data, updated_fields)
        
        if include_experiences:
            experiences_added = await self._add_experiences(db, candidate, profile_data)
            profile_data["_experiences_added"] = experiences_added
        
        if include_education:
            education_added = await self._add_education(db, candidate, profile_data)
            profile_data["_education_added"] = education_added
        
        candidate.updated_at = datetime.utcnow()
        
        if "enrichment" not in (candidate.additional_data or {}):
            if candidate.additional_data is None:
                candidate.additional_data = {}
            candidate.additional_data["enrichment"] = {
                "last_enriched_at": datetime.utcnow().isoformat(),
                "source": "linkedin",
                "fields_updated": updated_fields
            }
        
        return updated_fields
    
    def _apply_location(
        self,
        candidate: Candidate,
        profile_data: dict[str, Any],
        updated_fields: list[str]
    ) -> bool:
        """Parse and apply location data."""
        location = profile_data.get("location") or profile_data.get("locationName") or ""
        
        if not location:
            return False
        
        parts = [p.strip() for p in location.split(",")]
        
        if len(parts) >= 1 and not candidate.location_city:
            candidate.location_city = parts[0]
            updated_fields.append("location_city")
        
        if len(parts) >= 2 and not candidate.location_state:
            candidate.location_state = parts[1]
            updated_fields.append("location_state")
        
        if len(parts) >= 3 and not candidate.location_country:
            candidate.location_country = parts[-1]
            updated_fields.append("location_country")
        elif len(parts) == 2 and not candidate.location_country:
            candidate.location_country = parts[1]
            if "location_state" in updated_fields:
                candidate.location_state = None
                updated_fields.remove("location_state")
        
        return True
    
    def _apply_skills(
        self,
        candidate: Candidate,
        profile_data: dict[str, Any],
        updated_fields: list[str]
    ):
        """Apply skills data."""
        skills = profile_data.get("skills") or []
        
        if isinstance(skills, list) and skills:
            skill_names = []
            for skill in skills:
                if isinstance(skill, str):
                    skill_names.append(skill)
                elif isinstance(skill, dict):
                    name = skill.get("name") or skill.get("skill") or ""
                    if name:
                        skill_names.append(name)
            
            if skill_names:
                existing = set(candidate.technical_skills or [])
                new_skills = [s for s in skill_names if s not in existing]
                
                if new_skills:
                    candidate.technical_skills = list(existing) + new_skills
                    updated_fields.append("technical_skills")
    
    def _apply_languages(
        self,
        candidate: Candidate,
        profile_data: dict[str, Any],
        updated_fields: list[str]
    ):
        """Apply language data."""
        languages = profile_data.get("languages") or []
        
        if isinstance(languages, list) and languages:
            lang_dict = candidate.languages or {}
            
            for lang in languages:
                if isinstance(lang, str):
                    if lang not in lang_dict:
                        lang_dict[lang] = "conversational"
                elif isinstance(lang, dict):
                    name = lang.get("name") or lang.get("language") or ""
                    level = lang.get("proficiency") or lang.get("level") or "conversational"
                    if name and name not in lang_dict:
                        lang_dict[name] = level
            
            if lang_dict != (candidate.languages or {}):
                candidate.languages = lang_dict
                updated_fields.append("languages")
    
    def _apply_certifications(
        self,
        candidate: Candidate,
        profile_data: dict[str, Any],
        updated_fields: list[str]
    ):
        """Apply certification data."""
        certifications = profile_data.get("certifications") or []
        
        if isinstance(certifications, list) and certifications:
            cert_names = []
            for cert in certifications:
                if isinstance(cert, str):
                    cert_names.append(cert)
                elif isinstance(cert, dict):
                    name = cert.get("name") or cert.get("title") or ""
                    authority = cert.get("authority") or cert.get("issuer") or ""
                    if name:
                        full_cert = f"{name}" + (f" ({authority})" if authority else "")
                        cert_names.append(full_cert)
            
            if cert_names:
                existing = set(candidate.certifications or [])
                new_certs = [c for c in cert_names if c not in existing]
                
                if new_certs:
                    candidate.certifications = list(existing) + new_certs
                    updated_fields.append("certifications")
    
    def _apply_social_metrics(
        self,
        candidate: Candidate,
        profile_data: dict[str, Any],
        updated_fields: list[str]
    ):
        """Apply social metrics (followers, connections, etc.)."""
        followers = profile_data.get("followersCount") or profile_data.get("followers")
        if followers and not candidate.linkedin_followers_count:
            try:
                candidate.linkedin_followers_count = int(followers)
                updated_fields.append("linkedin_followers_count")
            except (ValueError, TypeError):
                pass
        
        connections = profile_data.get("connectionsCount") or profile_data.get("connections")
        if connections and not candidate.linkedin_connections_count:
            try:
                if isinstance(connections, str) and "+" in connections:
                    connections = connections.replace("+", "").replace(",", "")
                candidate.linkedin_connections_count = int(connections)
                updated_fields.append("linkedin_connections_count")
            except (ValueError, TypeError):
                pass
        
        open_to_work = profile_data.get("isOpenToWork") or profile_data.get("openToWork")
        if open_to_work is not None and candidate.is_open_to_work is None:
            candidate.is_open_to_work = bool(open_to_work)
            updated_fields.append("is_open_to_work")
    
    def _apply_contact_info(
        self,
        candidate: Candidate,
        profile_data: dict[str, Any],
        updated_fields: list[str]
    ):
        """Apply contact information (emails, phones)."""
        email = profile_data.get("email") or profile_data.get("emailAddress")
        if email and not candidate.email:
            candidate.email = email
            updated_fields.append("email")
        
        personal_email = profile_data.get("personalEmail") or profile_data.get("bestPersonalEmail")
        if personal_email and not candidate.best_personal_email:
            candidate.best_personal_email = personal_email
            updated_fields.append("best_personal_email")
        
        business_email = profile_data.get("businessEmail") or profile_data.get("bestBusinessEmail")
        if business_email and not candidate.best_business_email:
            candidate.best_business_email = business_email
            updated_fields.append("best_business_email")
        
        personal_emails = profile_data.get("personalEmails") or []
        if personal_emails and not candidate.personal_emails:
            candidate.personal_emails = personal_emails
            updated_fields.append("personal_emails")
        
        business_emails = profile_data.get("businessEmails") or []
        if business_emails and not candidate.business_emails:
            candidate.business_emails = business_emails
            updated_fields.append("business_emails")
        
        if not candidate.email:
            if candidate.best_personal_email:
                candidate.email = candidate.best_personal_email
                if "email" not in updated_fields:
                    updated_fields.append("email")
            elif candidate.best_business_email:
                candidate.email = candidate.best_business_email
                if "email" not in updated_fields:
                    updated_fields.append("email")
    
    async def _add_experiences(
        self,
        db: AsyncSession,
        candidate: Candidate,
        profile_data: dict[str, Any]
    ) -> int:
        """Add work experience records from profile data."""
        experiences = profile_data.get("experience") or profile_data.get("positions") or []
        
        if not isinstance(experiences, list):
            return 0
        
        added = 0
        for i, exp in enumerate(experiences):
            if not isinstance(exp, dict):
                continue
            
            company_name = exp.get("companyName") or exp.get("company") or ""
            if not company_name:
                continue
            
            existing = await db.execute(
                select(CandidateExperience).where(
                    CandidateExperience.candidate_id == candidate.id,
                    CandidateExperience.company_name == company_name,
                    CandidateExperience.title == (exp.get("title") or exp.get("position") or "")
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            experience = CandidateExperience(
                candidate_id=candidate.id,
                company_name=company_name,
                company_linkedin_url=exp.get("companyUrl") or exp.get("companyLinkedInUrl"),
                title=exp.get("title") or exp.get("position"),
                start_date=self._parse_date(exp.get("startDate") or exp.get("start")),
                end_date=self._parse_date(exp.get("endDate") or exp.get("end")),
                is_current=exp.get("isCurrent") or exp.get("current") or False,
                description=exp.get("description") or exp.get("summary"),
                location=exp.get("location") or exp.get("locationName"),
                sequence_order=i
            )
            
            if exp.get("duration"):
                try:
                    duration_str = exp.get("duration", "")
                    years = 0
                    if "year" in duration_str.lower():
                        years_match = re.search(r"(\d+)\s*year", duration_str.lower())
                        if years_match:
                            years = int(years_match.group(1))
                    if "month" in duration_str.lower():
                        months_match = re.search(r"(\d+)\s*month", duration_str.lower())
                        if months_match:
                            years += int(months_match.group(1)) / 12
                    experience.duration_years = round(years, 1)
                except Exception:
                    pass
            
            db.add(experience)
            added += 1
        
        return added
    
    async def _add_education(
        self,
        db: AsyncSession,
        candidate: Candidate,
        profile_data: dict[str, Any]
    ) -> int:
        """Add education records from profile data."""
        education_list = profile_data.get("education") or profile_data.get("educations") or []
        
        if not isinstance(education_list, list):
            return 0
        
        added = 0
        for i, edu in enumerate(education_list):
            if not isinstance(edu, dict):
                continue
            
            institution = edu.get("schoolName") or edu.get("school") or edu.get("institution") or ""
            if not institution:
                continue
            
            existing = await db.execute(
                select(CandidateEducation).where(
                    CandidateEducation.candidate_id == candidate.id,
                    CandidateEducation.institution == institution
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            education = CandidateEducation(
                candidate_id=candidate.id,
                institution=institution,
                degree=edu.get("degree") or edu.get("degreeName"),
                field_of_study=edu.get("fieldOfStudy") or edu.get("field"),
                start_date=self._parse_date(edu.get("startDate") or edu.get("start")),
                end_date=self._parse_date(edu.get("endDate") or edu.get("end")),
                description=edu.get("description") or edu.get("activities"),
                sequence_order=i
            )
            
            db.add(education)
            added += 1
        
        return added
    
    def _parse_date(self, date_value: Any) -> str | None:
        """Parse various date formats into string."""
        if not date_value:
            return None
        
        if isinstance(date_value, str):
            return date_value
        
        if isinstance(date_value, dict):
            year = date_value.get("year")
            month = date_value.get("month")
            if year:
                if month:
                    return f"{month}/{year}"
                return str(year)
        
        return str(date_value) if date_value else None
    
    def _normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL to standard format."""
        url = url.strip()
        
        url = url.split("?")[0].rstrip("/")
        
        if not url.startswith("http"):
            url = "https://" + url
        
        url = re.sub(r"https?://(www\.)?", "https://www.", url)
        
        return url
    
    async def enrich_from_cv_text(
        self,
        db: AsyncSession,
        candidate_id: UUID,
        cv_text: str
    ) -> dict[str, Any]:
        """
        Extract LinkedIn URL from CV text and enrich candidate.
        
        Args:
            db: Database session
            candidate_id: UUID of the candidate
            cv_text: Raw CV text content
            
        Returns:
            Enrichment result
        """
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+'
        match = re.search(linkedin_pattern, cv_text)
        
        if match:
            linkedin_url = match.group(0)
            return await self.enrich_candidate(db, candidate_id, linkedin_url)
        
        return {
            "success": False,
            "error": "No LinkedIn URL found in CV text",
            "fields_updated": []
        }


candidate_enrichment_service = CandidateEnrichmentService()
