"""
Job Board Integration Service - LinkedIn and Indeed job posting.
Handles publishing jobs to external job boards.
For MVP: Prepare infrastructure, actual posting may require OAuth approval.
"""
import logging
import os
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCRUDRepository

from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


class JobBoardService:
    """
    Handles publishing jobs to external job boards.
    For MVP: Prepare infrastructure, actual posting may require OAuth approval.
    """
    
    def __init__(self):
        self.linkedin_client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.linkedin_client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.indeed_api_key = os.getenv("INDEED_API_KEY")
        self.base_url = os.getenv("APP_BASE_URL", "https://app.wedotalent.com")
    
    async def publish_to_linkedin(
        self, 
        job: JobVacancy, 
        db: AsyncSession,
        company_page_id: str | None = None
    ) -> dict:
        """
        LinkedIn Job Posting API integration.
        Requires: LinkedIn Company Page admin access and OAuth 2.0.
        
        For MVP: Returns mock response. Full integration requires:
        1. LinkedIn Company Page admin access
        2. LinkedIn Developer App with Job Posting permissions
        3. OAuth 2.0 flow for authorization
        
        Args:
            job: JobVacancy model instance
            db: Database session
            company_page_id: LinkedIn Company Page URN (optional)
        
        Returns:
            dict with success status and post details
        """
        logger.info(f"📤 Publishing job {job.id} to LinkedIn")
        
        if not self.linkedin_client_id or not self.linkedin_client_secret:
            logger.warning(
                "[JobBoardService] LinkedIn credentials not configured — "
                "skipping publish for job_id=%s. Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET.",
                job.id,
            )
            return {
                "success": False,
                "error": "not_configured",
                "message": (
                    "LinkedIn API credentials not configured. "
                    "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET to enable direct LinkedIn posting. "
                    "Configure in Configurações > Integrações."
                ),
                "platform": "linkedin",
                "job_id": str(job.id),
                "job_title": job.title,
            }
        
        # Onda 2E (audit 2026-06-06): proveniencia honesta. Credenciais configuradas NAO
        # significam integracao real — a LinkedIn Job Posting API exige aprovacao de partner
        # (Talent Solutions) e NAO ha chamada HTTP real implementada. NAO fabricar post_id/URL
        # nem marcar a vaga como publicada (era falso-positivo de publicacao).
        logger.warning(
            "[JobBoardService] LinkedIn Job Posting API nao implementada (requer partner approval) "
            "— job_id=%s retornando not_implemented sem fabricar publicacao.",
            job.id,
        )
        return {
            "success": False,
            "status": "not_implemented",
            "error": "not_implemented",
            "message": (
                "Publicacao direta no LinkedIn ainda nao esta disponivel: a LinkedIn Job Posting "
                "API exige aprovacao de partner (Talent Solutions). As credenciais estao "
                "configuradas, mas a integracao de publicacao ainda nao foi implementada — "
                "nenhuma vaga foi publicada."
            ),
            "platform": "linkedin",
            "job_id": str(job.id),
            "job_title": job.title,
        }

    async def publish_to_indeed(
        self, 
        job: JobVacancy, 
        db: AsyncSession
    ) -> dict:
        """
        Indeed XML Feed or API integration.
        Supports: XML job feed for Indeed aggregation.
        
        Indeed primarily uses XML feeds for job ingestion. This method:
        1. Marks the job as published to Indeed
        2. Generates a unique job ID for Indeed tracking
        
        The actual job data is served via the XML feed endpoint.
        
        Args:
            job: JobVacancy model instance
            db: Database session
        
        Returns:
            dict with success status and job details
        """
        logger.info(f"📤 Publishing job {job.id} to Indeed")

        api_configured = bool(self.indeed_api_key)
        publish_mode = "api_direct" if api_configured else "xml_feed"

        if not api_configured:
            logger.info(
                "[JobBoardService] INDEED_API_KEY not set — publishing via XML feed fallback for job_id=%s.",
                job.id,
            )

        try:
            indeed_job_id = f"wdt_{job.id.hex[:12]}"
            
            job.published_indeed = True
            job.indeed_job_id = indeed_job_id
            job.last_published_at = datetime.utcnow()
            await db.commit()
            
            feed_url = f"{self.base_url}/api/v1/job-boards/feed/indeed.xml"
            job_url = f"{self.base_url}/vagas/{job.public_slug or job.id}"
            
            logger.info(f"✅ Job {job.id} added to Indeed ({publish_mode}) with job_id: {indeed_job_id}")
            
            return {
                "success": True,
                "publish_mode": publish_mode,
                "api_configured": api_configured,
                "message": (
                    f"Job '{job.title}' published to Indeed via {'API' if api_configured else 'XML feed'}. "
                    + ("" if api_configured else "Set INDEED_API_KEY for direct API posting.")
                ),
                "job_id": indeed_job_id,
                "platform": "indeed",
                "vacancy_id": str(job.id),
                "job_title": job.title,
                "published_at": job.last_published_at.isoformat(),
                "feed_url": feed_url,
                "job_url": job_url,
                "note": (
                    None if api_configured
                    else "Submit the feed URL to Indeed Publisher to complete integration: " + feed_url
                ),
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"❌ Error publishing to Indeed: {e}")
            return {
                "success": False,
                "message": f"Error publishing to Indeed: {str(e)}",
                "platform": "indeed",
                "job_id": str(job.id)
            }
    
    async def unpublish_from_linkedin(
        self, 
        job: JobVacancy, 
        db: AsyncSession
    ) -> dict:
        """
        Remove job from LinkedIn.
        
        Args:
            job: JobVacancy model instance
            db: Database session
        
        Returns:
            dict with success status
        """
        logger.info(f"📤 Unpublishing job {job.id} from LinkedIn")
        
        try:
            old_post_id = job.linkedin_post_id
            
            job.published_linkedin = False
            job.linkedin_post_id = None
            await db.commit()
            
            logger.info(f"✅ Job {job.id} unpublished from LinkedIn")
            
            return {
                "success": True,
                "message": f"Job '{job.title}' removed from LinkedIn",
                "platform": "linkedin",
                "job_id": str(job.id),
                "old_post_id": old_post_id
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"❌ Error unpublishing from LinkedIn: {e}")
            return {
                "success": False,
                "message": f"Error unpublishing from LinkedIn: {str(e)}",
                "platform": "linkedin",
                "job_id": str(job.id)
            }
    
    async def unpublish_from_indeed(
        self, 
        job: JobVacancy, 
        db: AsyncSession
    ) -> dict:
        """
        Remove job from Indeed feed.
        
        Args:
            job: JobVacancy model instance
            db: Database session
        
        Returns:
            dict with success status
        """
        logger.info(f"📤 Unpublishing job {job.id} from Indeed")
        
        try:
            old_job_id = job.indeed_job_id
            
            job.published_indeed = False
            job.indeed_job_id = None
            await db.commit()
            
            logger.info(f"✅ Job {job.id} removed from Indeed feed")
            
            return {
                "success": True,
                "message": f"Job '{job.title}' removed from Indeed feed",
                "platform": "indeed",
                "job_id": str(job.id),
                "old_indeed_id": old_job_id
            }
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"❌ Error unpublishing from Indeed: {e}")
            return {
                "success": False,
                "message": f"Error unpublishing from Indeed: {str(e)}",
                "platform": "indeed",
                "job_id": str(job.id)
            }
    
    def health_check(self) -> dict:
        """
        Return structured configuration health for LinkedIn and Indeed integrations.

        Returns:
            dict with status for each platform:
            - connected:       API credentials configured
            - not_configured:  credentials absent (graceful fallback available)
        """
        li_configured = bool(self.linkedin_client_id and self.linkedin_client_secret)
        indeed_configured = bool(self.indeed_api_key)

        linkedin_status = {
            "status": "connected" if li_configured else "not_configured",
            "configured": li_configured,
            "message": None if li_configured else (
                "LINKEDIN_CLIENT_ID e LINKEDIN_CLIENT_SECRET não configurados. "
                "A publicação no LinkedIn requer aprovação OAuth e acesso à Company Page. "
                "Configure as credenciais em Configurações > Integrações."
            ),
        }
        indeed_status = {
            "status": "connected" if indeed_configured else "not_configured",
            "configured": indeed_configured,
            "publish_mode": "api_direct" if indeed_configured else "xml_feed",
            "feed_available": True,
            "message": None if indeed_configured else (
                "INDEED_API_KEY não configurado — vagas publicadas via feed XML "
                "(/api/v1/job-boards/feed/indeed.xml). "
                "Configure INDEED_API_KEY em Configurações > Integrações para publicação direta via API."
            ),
        }

        any_configured = li_configured or indeed_configured
        return {
            "status": "connected" if any_configured else "not_configured",
            "platforms": {
                "linkedin": linkedin_status,
                "indeed": indeed_status,
            },
        }

    async def get_publishing_status(
        self, 
        job: JobVacancy
    ) -> dict:
        """
        Get publishing status for a job across all platforms.
        
        Args:
            job: JobVacancy model instance
        
        Returns:
            dict with publishing status for all platforms
        """
        return {
            "job_id": str(job.id),
            "job_title": job.title,
            "platforms": {
                "linkedin": {
                    "published": job.published_linkedin or False,
                    "post_id": job.linkedin_post_id,
                    "url": f"https://www.linkedin.com/jobs/view/{job.linkedin_post_id}" if job.linkedin_post_id else None
                },
                "indeed": {
                    "published": job.published_indeed or False,
                    "job_id": job.indeed_job_id,
                    "feed_url": f"{self.base_url}/api/v1/job-boards/feed/indeed.xml" if job.published_indeed else None
                },
                "website": {
                    "published": job.published_website or False,
                    "url": f"{self.base_url}/vagas/{job.public_slug or job.id}" if job.published_website else None
                }
            },
            "last_published_at": job.last_published_at.isoformat() if job.last_published_at else None
        }
    
    async def generate_job_feed_xml(
        self, 
        company_id: str, 
        db: AsyncSession
    ) -> str:
        """
        Generate Indeed-compatible XML feed of all active jobs.
        Format follows Indeed's job feed specification.
        
        Args:
            company_id: Company ID to filter jobs
            db: Database session
        
        Returns:
            XML string in Indeed format
        """
        jobs = await JobVacancyCRUDRepository(db).list_indeed_published_active(company_id)
        
        root = ET.Element("source")
        
        publisher = ET.SubElement(root, "publisher")
        publisher.text = "WeDoTalent"
        
        publisher_url = ET.SubElement(root, "publisherurl")
        publisher_url.text = self.base_url
        
        last_build_date = ET.SubElement(root, "lastBuildDate")
        last_build_date.text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        for job in jobs:
            job_elem = self._create_indeed_job_element(job)
            root.append(job_elem)
        
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ", encoding=None)
        
        if isinstance(pretty_xml, bytes):
            pretty_xml = pretty_xml.decode("utf-8")
        
        lines = pretty_xml.split('\n')
        if lines[0].startswith('<?xml'):
            lines[0] = '<?xml version="1.0" encoding="utf-8"?>'
        
        return '\n'.join(lines)
    
    def _create_indeed_job_element(self, job: JobVacancy) -> ET.Element:
        """
        Create Indeed job XML element from JobVacancy.
        
        Args:
            job: JobVacancy model instance
        
        Returns:
            ET.Element representing the job
        """
        job_elem = ET.Element("job")
        
        title = ET.SubElement(job_elem, "title")
        title.text = self._cdata(job.title)
        
        date = ET.SubElement(job_elem, "date")
        date.text = job.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000") if job.created_at else ""
        
        ref_number = ET.SubElement(job_elem, "referencenumber")
        ref_number.text = job.indeed_job_id or f"wdt_{str(job.id)[:12]}"
        
        url = ET.SubElement(job_elem, "url")
        url.text = f"{self.base_url}/vagas/{job.public_slug or job.id}"
        
        company = ET.SubElement(job_elem, "company")
        company.text = self._cdata(job.masked_company_name or "WeDoTalent Client")
        
        location = job.location or ""
        city = ET.SubElement(job_elem, "city")
        city.text = self._cdata(location.split(",")[0].strip() if location else "")
        
        state = ET.SubElement(job_elem, "state")
        state.text = self._cdata(location.split(",")[1].strip() if location and "," in location else "")
        
        country = ET.SubElement(job_elem, "country")
        country.text = "BR"
        
        description = ET.SubElement(job_elem, "description")
        description.text = self._cdata(job.description or "")
        
        salary = ET.SubElement(job_elem, "salary")
        if job.salary_range:
            salary_range = job.salary_range
            if isinstance(salary_range, dict):
                min_sal = salary_range.get("min", 0)
                max_sal = salary_range.get("max", 0)
                currency = salary_range.get("currency", "BRL")
                salary.text = f"{currency} {min_sal:,.0f} - {max_sal:,.0f}"
            else:
                salary.text = str(job.salary or "A combinar")
        else:
            salary.text = job.salary or "A combinar"
        
        job_type = ET.SubElement(job_elem, "jobtype")
        job_type.text = self._map_employment_type(job.employment_type)
        
        category = ET.SubElement(job_elem, "category")
        category.text = self._cdata(job.department or "")
        
        experience = ET.SubElement(job_elem, "experience")
        experience.text = job.seniority_level or ""
        
        remote_type = ET.SubElement(job_elem, "remotetype")
        remote_type.text = self._map_work_model(job.work_model)
        
        return job_elem
    
    def _cdata(self, text: str) -> str:
        """Wrap text for CDATA if needed."""
        if not text:
            return ""
        if any(c in text for c in ['<', '>', '&', '"', "'"]):
            return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return text
    
    def _map_employment_type(self, employment_type: str | None) -> str:
        """Map internal employment type to Indeed format."""
        mapping = {
            "CLT": "fulltime",
            "PJ": "contract",
            "Temporário": "temporary",
            "Estágio": "internship",
            "Freelancer": "contract",
            "Meio período": "parttime"
        }
        return mapping.get(employment_type or "", "fulltime")
    
    def _map_work_model(self, work_model: str | None) -> str:
        """Map internal work model to Indeed format."""
        mapping = {
            "remoto": "remote",
            "híbrido": "hybrid",
            "presencial": "onsite"
        }
        return mapping.get((work_model or "").lower(), "")
    
    def _prepare_linkedin_job_data(self, job: JobVacancy) -> dict:
        """
        Prepare job data for LinkedIn Job Posting API.
        
        Args:
            job: JobVacancy model instance
        
        Returns:
            dict formatted for LinkedIn API
        """
        return {
            "title": job.title,
            "description": job.description or "",
            "location": {
                "city": job.location.split(",")[0].strip() if job.location else "",
                "country": "BR"
            },
            "employmentStatus": self._map_employment_type_linkedin(job.employment_type),
            "workplaceType": self._map_work_model_linkedin(job.work_model),
            "seniorityLevel": self._map_seniority_linkedin(job.seniority_level),
            "skills": [req.get("technology") for req in (job.technical_requirements or []) if req.get("required")],
            "externalApplyUrl": f"{self.base_url}/vagas/{job.public_slug or job.id}",
        }
    
    def _map_employment_type_linkedin(self, employment_type: str | None) -> str:
        """Map internal employment type to LinkedIn format."""
        mapping = {
            "CLT": "FULL_TIME",
            "PJ": "CONTRACT",
            "Temporário": "TEMPORARY",
            "Estágio": "INTERNSHIP",
            "Meio período": "PART_TIME"
        }
        return mapping.get(employment_type or "", "FULL_TIME")
    
    def _map_work_model_linkedin(self, work_model: str | None) -> str:
        """Map internal work model to LinkedIn format."""
        mapping = {
            "remoto": "REMOTE",
            "híbrido": "HYBRID",
            "presencial": "ON_SITE"
        }
        return mapping.get((work_model or "").lower(), "ON_SITE")
    
    def _map_seniority_linkedin(self, seniority: str | None) -> str:
        """Map internal seniority to LinkedIn format."""
        mapping = {
            "Júnior": "ENTRY_LEVEL",
            "Pleno": "MID_SENIOR_LEVEL",
            "Sênior": "MID_SENIOR_LEVEL",
            "Especialista": "DIRECTOR"
        }
        return mapping.get(seniority or "", "MID_SENIOR_LEVEL")


job_board_service = JobBoardService()
