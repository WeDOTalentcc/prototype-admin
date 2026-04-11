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
                "dev_fusion/linkedin-profile-scraper"
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
                "dev_fusion/linkedin-profile-scraper"
            )
            
            assert "error" in result
            assert "Connection timeout" in result["error"]
