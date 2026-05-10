"""Coverage tests for company_scraper_service.py — pure helper methods."""
import pytest

from app.domains.company.services.company_scraper_service import CompanyScraperService


@pytest.fixture
def svc():
    return CompanyScraperService()


class TestCategorizePageUrl:
    def test_career_url(self, svc):
        assert svc._categorize_page("https://acme.com/careers") == "careers"

    def test_vagas_url(self, svc):
        assert svc._categorize_page("https://empresa.com.br/vagas") == "careers"

    def test_culture_url(self, svc):
        assert svc._categorize_page("https://acme.com/our-culture") == "culture"

    def test_values_url(self, svc):
        assert svc._categorize_page("https://acme.com/our-values") == "values"

    def test_about_url(self, svc):
        assert svc._categorize_page("https://acme.com/about-us") == "about"

    def test_team_url(self, svc):
        assert svc._categorize_page("https://acme.com/team") == "team"

    def test_mission_url(self, svc):
        assert svc._categorize_page("https://acme.com/mission") == "mission"

    def test_generic_url(self, svc):
        assert svc._categorize_page("https://acme.com/products") == "general"

    def test_link_text_overrides(self, svc):
        # URL generic but link text contains "trabalhe" (a career keyword)
        result = svc._categorize_page("https://acme.com/page", link_text="trabalhe conosco")
        assert result == "careers"

    def test_cultura_keyword(self, svc):
        assert svc._categorize_page("https://empresa.com.br/cultura") == "culture"


class TestNormalizeUrl:
    def test_adds_https_scheme(self, svc):
        result = svc._normalize_url("acme.com")
        assert result.startswith("https://")

    def test_keeps_existing_https(self, svc):
        result = svc._normalize_url("https://acme.com")
        assert result.startswith("https://")

    def test_keeps_existing_http(self, svc):
        result = svc._normalize_url("http://acme.com")
        assert result.startswith("http://")

    def test_adds_trailing_slash_to_root(self, svc):
        result = svc._normalize_url("https://acme.com")
        assert result.endswith("/")

    def test_path_not_modified(self, svc):
        result = svc._normalize_url("https://acme.com/about")
        assert "/about" in result


class TestExtractTextContent:
    def test_extracts_text_from_html(self, svc):
        html = "<html><body><main><p>Hello World</p></main></body></html>"
        result = svc._extract_text_content(html)
        assert "Hello World" in result

    def test_removes_script_tags(self, svc):
        html = "<html><body><script>alert('x')</script><p>Content</p></body></html>"
        result = svc._extract_text_content(html)
        assert "alert" not in result
        assert "Content" in result

    def test_removes_nav_tags(self, svc):
        html = "<html><body><nav>Navigation</nav><p>Main content</p></body></html>"
        result = svc._extract_text_content(html)
        assert "Navigation" not in result

    def test_empty_html(self, svc):
        result = svc._extract_text_content("<html><body></body></html>")
        assert result == ""

    def test_collapses_multiple_newlines(self, svc):
        html = "<html><body><p>A</p><p>B</p></body></html>"
        result = svc._extract_text_content(html)
        assert "\n\n\n" not in result


class TestFindLinkedinUrl:
    def test_finds_linkedin_in_href(self, svc):
        html = '''<html><body>
            <a href="https://linkedin.com/company/acme">LinkedIn</a>
        </body></html>'''
        result = svc._find_linkedin_url(html, "https://acme.com")
        assert result == "https://linkedin.com/company/acme"

    def test_returns_none_when_not_found(self, svc):
        html = "<html><body><p>No social links</p></body></html>"
        result = svc._find_linkedin_url(html, "https://acme.com")
        assert result is None

    def test_finds_linkedin_with_path(self, svc):
        html = '''<html><body>
            <a href="https://www.linkedin.com/company/wedotalent">Follow</a>
        </body></html>'''
        result = svc._find_linkedin_url(html, "https://wedotalent.cc")
        assert "linkedin.com" in result
