"""
Tests for CandidateEnrichmentService.

Tests cover:
- LinkedIn profile data extraction
- Field mapping and application
- Experience and education record creation
- URL normalization
- Error handling
"""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.domains.candidates.services.candidate_enrichment_service import CandidateEnrichmentService


class TestCandidateEnrichmentServiceHelpers:
    """Tests for helper methods."""
    
    def test_normalize_linkedin_url_standard(self):
        """Test normalizing standard LinkedIn URL."""
        service = CandidateEnrichmentService()
        
        url = "https://www.linkedin.com/in/johndoe"
        normalized = service._normalize_linkedin_url(url)
        
        assert normalized == "https://www.linkedin.com/in/johndoe"
    
    def test_normalize_linkedin_url_with_trailing_slash(self):
        """Test normalizing URL with trailing slash."""
        service = CandidateEnrichmentService()
        
        url = "https://www.linkedin.com/in/johndoe/"
        normalized = service._normalize_linkedin_url(url)
        
        assert not normalized.endswith("/") or normalized == url.rstrip("/")
    
    def test_normalize_linkedin_url_without_https(self):
        """Test normalizing URL without https."""
        service = CandidateEnrichmentService()
        
        url = "linkedin.com/in/johndoe"
        normalized = service._normalize_linkedin_url(url)
        
        assert "linkedin.com/in/johndoe" in normalized
    
    def test_parse_date_string(self):
        """Test parsing string date."""
        service = CandidateEnrichmentService()
        
        result = service._parse_date("2023")
        
        assert result == "2023"
    
    def test_parse_date_dict(self):
        """Test parsing dict date format."""
        service = CandidateEnrichmentService()
        
        result = service._parse_date({"year": 2023, "month": 6})
        
        assert result == "6/2023"
    
    def test_parse_date_dict_year_only(self):
        """Test parsing dict date with year only."""
        service = CandidateEnrichmentService()
        
        result = service._parse_date({"year": 2023})
        
        assert result == "2023"
    
    def test_parse_date_none(self):
        """Test parsing None date."""
        service = CandidateEnrichmentService()
        
        result = service._parse_date(None)
        
        assert result is None


class TestFieldMapping:
    """Tests for field mapping and application."""
    
    def test_apply_location_full(self):
        """Test applying full location data."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.location_city = None
        candidate.location_state = None
        candidate.location_country = None
        
        profile_data = {"location": "São Paulo, SP, Brazil"}
        updated_fields = []
        
        result = service._apply_location(candidate, profile_data, updated_fields)
        
        assert result is True
        assert "location_city" in updated_fields
        assert candidate.location_city == "São Paulo"
    
    def test_apply_location_partial(self):
        """Test applying partial location data."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.location_city = None
        candidate.location_state = None
        candidate.location_country = None
        
        profile_data = {"location": "New York, USA"}
        updated_fields = []
        
        result = service._apply_location(candidate, profile_data, updated_fields)
        
        assert result is True
        assert "location_city" in updated_fields
    
    def test_apply_location_empty(self):
        """Test applying empty location data."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        
        profile_data = {"location": ""}
        updated_fields = []
        
        result = service._apply_location(candidate, profile_data, updated_fields)
        
        assert result is False
    
    def test_apply_skills_list_of_strings(self):
        """Test applying skills as list of strings."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.technical_skills = None
        
        profile_data = {"skills": ["Python", "JavaScript", "React"]}
        updated_fields = []
        
        service._apply_skills(candidate, profile_data, updated_fields)
        
        assert "technical_skills" in updated_fields
        assert candidate.technical_skills == ["Python", "JavaScript", "React"]
    
    def test_apply_skills_list_of_dicts(self):
        """Test applying skills as list of dicts."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.technical_skills = None
        
        profile_data = {
            "skills": [
                {"name": "Python", "endorsements": 50},
                {"name": "JavaScript", "endorsements": 30}
            ]
        }
        updated_fields = []
        
        service._apply_skills(candidate, profile_data, updated_fields)
        
        assert "technical_skills" in updated_fields
        assert "Python" in candidate.technical_skills  # type: ignore[operator]
        assert "JavaScript" in candidate.technical_skills  # type: ignore[operator]
    
    def test_apply_skills_merge_existing(self):
        """Test merging skills with existing ones."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.technical_skills = ["Python"]
        
        profile_data = {"skills": ["Python", "JavaScript"]}
        updated_fields = []
        
        service._apply_skills(candidate, profile_data, updated_fields)
        
        assert "technical_skills" in updated_fields
        assert "Python" in candidate.technical_skills
        assert "JavaScript" in candidate.technical_skills
    
    def test_apply_languages_list_of_strings(self):
        """Test applying languages as list of strings."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.languages = None
        
        profile_data = {"languages": ["English", "Portuguese"]}
        updated_fields = []
        
        service._apply_languages(candidate, profile_data, updated_fields)
        
        assert "languages" in updated_fields
        assert candidate.languages["English"] == "conversational"  # type: ignore[index]
    
    def test_apply_languages_list_of_dicts(self):
        """Test applying languages as list of dicts."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.languages = None
        
        profile_data = {
            "languages": [
                {"name": "English", "proficiency": "native"},
                {"name": "Portuguese", "level": "fluent"}
            ]
        }
        updated_fields = []
        
        service._apply_languages(candidate, profile_data, updated_fields)
        
        assert "languages" in updated_fields
        assert candidate.languages["English"] == "native"  # type: ignore[index]
        assert candidate.languages["Portuguese"] == "fluent"  # type: ignore[index]
    
    def test_apply_certifications(self):
        """Test applying certification data."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.certifications = None
        
        profile_data = {
            "certifications": [
                {"name": "AWS Solutions Architect", "authority": "Amazon"},
                {"name": "PMP"}
            ]
        }
        updated_fields = []
        
        service._apply_certifications(candidate, profile_data, updated_fields)
        
        assert "certifications" in updated_fields
        assert any("AWS" in c for c in candidate.certifications)  # type: ignore[union-attr]
    
    def test_apply_social_metrics_followers(self):
        """Test applying followers count."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.linkedin_followers_count = None
        candidate.linkedin_connections_count = None
        candidate.is_open_to_work = None
        
        profile_data = {"followersCount": 1500}
        updated_fields = []
        
        service._apply_social_metrics(candidate, profile_data, updated_fields)
        
        assert "linkedin_followers_count" in updated_fields
        assert candidate.linkedin_followers_count == 1500
    
    def test_apply_social_metrics_connections_with_plus(self):
        """Test applying connections count with + sign."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.linkedin_followers_count = None
        candidate.linkedin_connections_count = None
        candidate.is_open_to_work = None
        
        profile_data = {"connectionsCount": "500+"}
        updated_fields = []
        
        service._apply_social_metrics(candidate, profile_data, updated_fields)
        
        assert "linkedin_connections_count" in updated_fields
        assert candidate.linkedin_connections_count == 500
    
    def test_apply_contact_info_primary_email(self):
        """Test applying primary email."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.email = None
        candidate.best_personal_email = None
        candidate.best_business_email = None
        candidate.personal_emails = None
        candidate.business_emails = None
        
        profile_data = {"email": "john@example.com"}
        updated_fields = []
        
        service._apply_contact_info(candidate, profile_data, updated_fields)
        
        assert "email" in updated_fields
        assert candidate.email == "john@example.com"
    
    def test_apply_contact_info_fallback_to_personal(self):
        """Test email fallback to personal email."""
        service = CandidateEnrichmentService()
        candidate = MagicMock(spec=Candidate)
        candidate.email = None
        candidate.best_personal_email = None
        candidate.best_business_email = None
        candidate.personal_emails = None
        candidate.business_emails = None
        
        profile_data = {"bestPersonalEmail": "john.personal@gmail.com"}
        updated_fields = []
        
        service._apply_contact_info(candidate, profile_data, updated_fields)
        
        assert candidate.email == "john.personal@gmail.com"


class TestCandidateEnrichmentServiceIntegration:
    """Integration tests with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_enrich_candidate_success(self):
        """Test successful candidate enrichment."""
        service = CandidateEnrichmentService()
        
        mock_profile_data = {
            "firstName": "John",
            "lastName": "Doe",
            "headline": "Senior Software Engineer",
            "location": "San Francisco, CA, USA",
            "skills": ["Python", "JavaScript"],
            "email": "john@example.com"
        }
        
        with patch.object(
            service, '_scrape_linkedin_profile',
            return_value=mock_profile_data
        ):
            mock_db = AsyncMock(spec=AsyncSession)
            
            mock_candidate = MagicMock(spec=Candidate)
            mock_candidate.id = uuid4()
            mock_candidate.name = None
            mock_candidate.linkedin_url = "https://linkedin.com/in/johndoe"
            mock_candidate.avatar_url = None
            mock_candidate.headline = None
            mock_candidate.current_title = None
            mock_candidate.current_company = None
            mock_candidate.self_introduction = None
            mock_candidate.location_city = None
            mock_candidate.location_state = None
            mock_candidate.location_country = None
            mock_candidate.technical_skills = None
            mock_candidate.languages = None
            mock_candidate.certifications = None
            mock_candidate.linkedin_followers_count = None
            mock_candidate.linkedin_connections_count = None
            mock_candidate.is_open_to_work = None
            mock_candidate.email = None
            mock_candidate.best_personal_email = None
            mock_candidate.best_business_email = None
            mock_candidate.personal_emails = None
            mock_candidate.business_emails = None
            mock_candidate.additional_data = None
            mock_candidate.updated_at = None
            
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_candidate
            mock_db.execute.return_value = mock_result
            
            result = await service.enrich_candidate(
                db=mock_db,
                candidate_id=mock_candidate.id,
                include_experiences=False,
                include_education=False
            )
            
            assert result["success"] is True
            assert "fields_updated" in result
            assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_enrich_candidate_not_found(self):
        """Test enrichment when candidate not found."""
        service = CandidateEnrichmentService()
        
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        result = await service.enrich_candidate(
            db=mock_db,
            candidate_id=uuid4()
        )
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_enrich_candidate_no_linkedin_url(self):
        """Test enrichment when no LinkedIn URL available."""
        service = CandidateEnrichmentService()
        
        mock_db = AsyncMock(spec=AsyncSession)
        
        mock_candidate = MagicMock(spec=Candidate)
        mock_candidate.id = uuid4()
        mock_candidate.linkedin_url = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_candidate
        mock_db.execute.return_value = mock_result
        
        result = await service.enrich_candidate(
            db=mock_db,
            candidate_id=mock_candidate.id
        )
        
        assert result["success"] is False
        assert "LinkedIn URL" in result["error"]
    
    @pytest.mark.asyncio
    async def test_enrich_candidate_scrape_failure_fallback(self):
        """Test fallback to alternative scraper on failure."""
        service = CandidateEnrichmentService()
        
        mock_profile_data = {
            "firstName": "John",
            "lastName": "Doe",
            "headline": "Developer"
        }
        
        with patch.object(
            service, '_scrape_linkedin_profile',
            side_effect=[
                {"error": "Primary scraper failed"},
                mock_profile_data
            ]
        ):
            mock_db = AsyncMock(spec=AsyncSession)
            
            mock_candidate = MagicMock(spec=Candidate)
            mock_candidate.id = uuid4()
            mock_candidate.name = None
            mock_candidate.linkedin_url = "https://linkedin.com/in/johndoe"
            mock_candidate.avatar_url = None
            mock_candidate.headline = None
            mock_candidate.current_title = None
            mock_candidate.current_company = None
            mock_candidate.self_introduction = None
            mock_candidate.location_city = None
            mock_candidate.location_state = None
            mock_candidate.location_country = None
            mock_candidate.technical_skills = None
            mock_candidate.languages = None
            mock_candidate.certifications = None
            mock_candidate.linkedin_followers_count = None
            mock_candidate.linkedin_connections_count = None
            mock_candidate.is_open_to_work = None
            mock_candidate.email = None
            mock_candidate.best_personal_email = None
            mock_candidate.best_business_email = None
            mock_candidate.personal_emails = None
            mock_candidate.business_emails = None
            mock_candidate.additional_data = None
            mock_candidate.updated_at = None
            
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_candidate
            mock_db.execute.return_value = mock_result
            
            result = await service.enrich_candidate(
                db=mock_db,
                candidate_id=mock_candidate.id,
                include_experiences=False,
                include_education=False
            )
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_scrape_linkedin_profile_with_email_discovery(self):
        """Test LinkedIn scraping with email discovery."""
        service = CandidateEnrichmentService()
        
        mock_result = [{"firstName": "John", "email": "john@example.com"}]
        
        with patch.object(
            service.mcp_client, 'call_actor',
            return_value=mock_result
        ) as mock_call:
            result = await service._scrape_linkedin_profile(
                "https://linkedin.com/in/johndoe",
                "dev_fusion/Linkedin-Profile-Scraper"
            )
            
            assert result["firstName"] == "John"
            assert result["email"] == "john@example.com"
            
            call_args = mock_call.call_args
            input_data = call_args[0][1] if len(call_args[0]) > 1 else call_args.kwargs.get("input_data", {})
            assert input_data.get("includeEmailDiscovery") is True
    
    @pytest.mark.asyncio
    async def test_scrape_linkedin_profile_error(self):
        """Test LinkedIn scraping error handling."""
        service = CandidateEnrichmentService()
        
        with patch.object(
            service.mcp_client, 'call_actor',
            side_effect=Exception("Connection timeout")
        ):
            result = await service._scrape_linkedin_profile(
                "https://linkedin.com/in/johndoe",
                "dev_fusion/Linkedin-Profile-Scraper"
            )
            
            assert "error" in result
            assert "Connection timeout" in result["error"]


def _make_blank_candidate():
    """Create a MagicMock Candidate with all enrichment-relevant fields set to None."""
    candidate = MagicMock(spec=Candidate)
    for field in [
        "name", "avatar_url", "headline", "current_title", "current_company",
        "self_introduction", "linkedin_url", "github_url", "portfolio_url",
        "middle_name", "gender", "years_of_experience", "estimated_age",
        "seniority_level", "interests", "expertise", "location_city",
        "location_state", "location_country", "technical_skills", "languages",
        "certifications", "linkedin_followers_count", "linkedin_connections_count",
        "is_open_to_work", "email", "best_personal_email", "best_business_email",
        "personal_emails", "business_emails", "secondary_email", "phone",
        "mobile_phone", "phone_types", "additional_data", "updated_at",
    ]:
        setattr(candidate, field, None)
    candidate.id = uuid4()
    return candidate


class TestEnhancedFieldMapping:
    """Tests for enhanced field mapper (~40 fields)."""

    def test_apply_phone_info(self):
        service = CandidateEnrichmentService()
        candidate = _make_blank_candidate()

        profile_data = {
            "phoneNumbers": ["+5511999887766", "+5511888776655"],
            "phoneTypes": {"mobile": True, "work": True},
        }
        updated_fields = []

        service._apply_phone_info(candidate, profile_data, updated_fields)

        assert "phone" in updated_fields
        assert "mobile_phone" in updated_fields
        assert "phone_types" in updated_fields
        assert candidate.phone == "+5511999887766"
        assert candidate.mobile_phone == "+5511888776655"

    def test_apply_phone_single(self):
        service = CandidateEnrichmentService()
        candidate = _make_blank_candidate()

        profile_data = {"phone": "+5511111"}
        updated_fields = []

        service._apply_phone_info(candidate, profile_data, updated_fields)

        assert "phone" in updated_fields
        assert candidate.phone == "+5511111"

    @pytest.mark.asyncio
    async def test_apply_enrichment_full_mapping(self):
        """Test _apply_enrichment with a rich profile covering ~40 fields."""
        service = CandidateEnrichmentService()
        candidate = _make_blank_candidate()

        profile_data = {
            "firstName": "John",
            "middleName": "Robert",
            "lastName": "Doe",
            "headline": "Senior Software Engineer",
            "currentCompany": "TechCorp",
            "summary": "Experienced engineer",
            "githubUrl": "https://github.com/johndoe",
            "portfolioUrl": "https://johndoe.dev",
            "totalExperienceYears": 8.5,
            "estimatedAge": 32,
            "seniorityLevel": "senior",
            "location": "San Francisco, CA, USA",
            "skills": ["Python", "Go"],
            "languages": [{"name": "English", "proficiency": "native"}],
            "certifications": [{"name": "AWS SA", "authority": "Amazon"}],
            "followersCount": 1500,
            "connectionsCount": "500+",
            "isOpenToWork": True,
            "email": "john@example.com",
            "bestPersonalEmail": "john.personal@gmail.com",
            "secondaryEmail": "john2@example.com",
            "phoneNumbers": ["+1234567890"],
            "interests": ["Open Source", "AI"],
            "expertise": ["Backend", "Cloud"],
        }

        db = AsyncMock(spec=AsyncSession)

        updated_fields = await service._apply_enrichment(
            db, candidate, profile_data, False, False
        )

        assert "name" in updated_fields
        assert candidate.name == "John Robert Doe"
        assert "headline" in updated_fields
        assert "github_url" in updated_fields
        assert candidate.github_url == "https://github.com/johndoe"
        assert "years_of_experience" in updated_fields
        assert candidate.years_of_experience == 8
        assert "estimated_age" in updated_fields
        assert candidate.estimated_age == 32
        assert "seniority_level" in updated_fields
        assert candidate.seniority_level == "senior"
        assert "email" in updated_fields
        assert "best_personal_email" in updated_fields
        assert "secondary_email" in updated_fields
        assert "phone" in updated_fields
        assert "interests" in updated_fields
        assert "expertise" in updated_fields
        assert "linkedin_followers_count" in updated_fields
        assert "is_open_to_work" in updated_fields
        assert candidate.additional_data["enrichment"]["source"] == "linkedin"

    def test_apply_contact_info_secondary_email(self):
        service = CandidateEnrichmentService()
        candidate = _make_blank_candidate()
        candidate.email = "primary@email.com"

        profile_data = {"secondaryEmail": "secondary@email.com"}
        updated_fields = []

        service._apply_contact_info(candidate, profile_data, updated_fields)

        assert "secondary_email" in updated_fields
        assert candidate.secondary_email == "secondary@email.com"


class TestExperienceMapperEnhanced:
    """Tests for enhanced experience mapping with company enrichment fields."""

    @pytest.mark.asyncio
    async def test_experience_with_company_info(self):
        service = CandidateEnrichmentService()

        candidate = MagicMock(spec=Candidate)
        candidate.id = uuid4()

        db = AsyncMock(spec=AsyncSession)
        existing_mock = MagicMock()
        existing_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = existing_mock

        profile_data = {
            "experience": [
                {
                    "companyName": "TechCorp",
                    "title": "Senior Dev",
                    "companyInfo": {
                        "industries": ["Technology"],
                        "num_employees_range": "51-200",
                        "technologies": ["Python", "React"],
                        "is_startup": True,
                        "founded_in": 2015,
                        "funding_stage": "series_b",
                        "hq_city": "San Francisco",
                        "hq_state": "CA",
                        "hq_country": "US",
                        "domain": "techcorp.com",
                        "keywords": ["saas", "ai"],
                    },
                    "duration_years": 3.5,
                    "isCurrent": True,
                    "location": "Remote",
                }
            ]
        }

        added = await service._add_experiences(db, candidate, profile_data)

        assert added == 1
        db.add.assert_called_once()

        exp_obj = db.add.call_args[0][0]
        assert exp_obj.company_name == "TechCorp"
        assert exp_obj.industries == ["Technology"]
        assert exp_obj.company_size == "51-200"
        assert exp_obj.technologies == ["Python", "React"]
        assert exp_obj.is_startup is True
        assert exp_obj.company_founded_year == 2015
        assert exp_obj.funding_stage == "series_b"
        assert exp_obj.company_hq_city == "San Francisco"
        assert exp_obj.company_domain == "techcorp.com"
        assert exp_obj.company_tags == ["saas", "ai"]
        assert exp_obj.duration_years == 3.5


class TestEducationMapperEnhanced:
    """Tests for enhanced education mapping."""

    @pytest.mark.asyncio
    async def test_education_with_institution_info(self):
        service = CandidateEnrichmentService()

        candidate = MagicMock(spec=Candidate)
        candidate.id = uuid4()

        db = AsyncMock(spec=AsyncSession)
        existing_mock = MagicMock()
        existing_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = existing_mock

        profile_data = {
            "education": [
                {
                    "schoolName": "MIT",
                    "degree": "BS",
                    "fieldOfStudy": "Computer Science",
                    "startDate": "2010",
                    "endDate": "2014",
                    "gpa": "3.8",
                    "institution_city": "Cambridge",
                    "institution_state": "MA",
                    "institution_country": "US",
                    "institution_ranking": 1,
                    "institution_tier": "tier1",
                }
            ]
        }

        added = await service._add_education(db, candidate, profile_data)

        assert added == 1
        db.add.assert_called_once()

        edu_obj = db.add.call_args[0][0]
        assert edu_obj.institution == "MIT"
        assert edu_obj.gpa == "3.8"
        assert edu_obj.institution_city == "Cambridge"
        assert edu_obj.institution_country == "US"
        assert edu_obj.institution_ranking == 1
        assert edu_obj.institution_tier == "tier1"
        assert edu_obj.is_completed is True

