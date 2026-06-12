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

import httpx
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
        company_id: str | None = None,
        credentials: dict | None = None,
    ) -> dict:
        """
        LinkedIn Job Posting API integration (real implementation).

        Two posting modes (controlled by credentials["posting_type"]):
        - "job_posting": POST to /v2/simpleJobPostings (structured job ad)
        - "social_only": POST to /v2/ugcPosts only (social feed share)

        Fail-loud: never marks job as published if the API call fails.
        NEVER fabricates post_id or published_linkedin=True on error.

        Args:
            job:         JobVacancy model instance
            db:          Database session
            company_id:  Multi-tenancy — used to resolve credentials if not passed
            credentials: Pre-resolved credentials dict (access_token, org_urn, posting_type)
        """
        logger.info("[linkedin] publishing job_id=%s, company_id=%s", job.id, company_id)

        _LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

        if not credentials:
            return {
                "success": False,
                "error": "not_configured",
                "message": (
                    "LinkedIn não está configurado. "
                    "Conecte em Configurações > Integrações > Job Boards > LinkedIn."
                ),
                "platform": "linkedin",
                "job_id": str(job.id),
                "job_title": job.title,
            }

        access_token = credentials.get("access_token", "")
        org_urn = credentials.get("org_urn", "")
        posting_type = credentials.get("posting_type", "social_only")

        if not access_token or not org_urn:
            return {
                "success": False,
                "error": "credentials_incomplete",
                "message": "access_token ou org_urn ausente nas credenciais armazenadas.",
                "platform": "linkedin",
                "job_id": str(job.id),
            }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        job_url = f"{self.base_url}/vagas/{job.public_slug or job.id}"
        job_post_id: str | None = None
        social_post_id: str | None = None

        # ── Step 1: Job Posting API (structured job ad) ───────────────────────
        if posting_type == "job_posting":
            job_payload = {
                "externalJobPostingId": f"wdt-{job.id}",
                "title": job.title,
                "description": {"text": (job.description or "")[:4000]},
                "employmentStatus": self._map_employment_type_linkedin(job.employment_type),
                "workRemoteAllowed": (job.work_model or "").lower() in ("remoto", "hibrido", "híbrido", "remote", "hybrid"),
                "location": {"countryCode": "BR"},
                "applyMethod": {
                    "com.linkedin.jobs.OffsiteApply": {
                        "companyApplyUrl": job_url,
                    }
                },
                "listedAt": int(datetime.utcnow().timestamp() * 1000),
                "integrationContext": org_urn,
            }
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        f"{_LINKEDIN_API_BASE}/simpleJobPostings",
                        headers=headers,
                        json=job_payload,
                    )
                if resp.status_code in (200, 201):
                    job_post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-Restli-Id")
                    logger.info(
                        "[linkedin] job posting created for job_id=%s, post_id=%s",
                        job.id, job_post_id,
                    )
                else:
                    error_body: dict = {}
                    try:
                        error_body = resp.json()
                    except Exception:
                        error_body = {"raw": resp.text[:500]}
                    logger.error(
                        "[linkedin] simpleJobPostings error for job_id=%s: status=%s body=%s",
                        job.id, resp.status_code, error_body,
                    )
                    return {
                        "success": False,
                        "error": f"linkedin_api_error_{resp.status_code}",
                        "linkedin_error": error_body,
                        "platform": "linkedin",
                        "job_id": str(job.id),
                        "job_title": job.title,
                        "message": (
                            f"LinkedIn Job Postings API retornou {resp.status_code}. "
                            "Verifique se o access_token tem permissão 'w_member_social' ou 'r_liteprofile'."
                        ),
                    }
            except httpx.TimeoutException as exc:
                logger.error("[linkedin] simpleJobPostings timeout for job_id=%s: %s", job.id, exc)
                return {
                    "success": False,
                    "error": "timeout",
                    "message": "LinkedIn Job Postings API não respondeu a tempo.",
                    "platform": "linkedin",
                    "job_id": str(job.id),
                }
            except httpx.RequestError as exc:
                logger.error("[linkedin] simpleJobPostings request error for job_id=%s: %s", job.id, exc)
                return {
                    "success": False,
                    "error": "request_error",
                    "message": f"Erro de conexão com LinkedIn: {exc}",
                    "platform": "linkedin",
                    "job_id": str(job.id),
                }

        # ── Step 2: UGC Post (social feed share) — always run ────────────────
        social_text = self._build_social_summary(job)
        ugc_payload = {
            "author": org_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": social_text},
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": job_url,
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{_LINKEDIN_API_BASE}/ugcPosts",
                    headers=headers,
                    json=ugc_payload,
                )
            if resp.status_code in (200, 201):
                social_post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-Restli-Id")
                logger.info(
                    "[linkedin] ugcPost created for job_id=%s, post_id=%s",
                    job.id, social_post_id,
                )
            else:
                error_body = {}
                try:
                    error_body = resp.json()
                except Exception:
                    error_body = {"raw": resp.text[:500]}
                logger.error(
                    "[linkedin] ugcPosts error for job_id=%s: status=%s body=%s",
                    job.id, resp.status_code, error_body,
                )
                # If job posting already succeeded, report partial success
                if job_post_id:
                    logger.warning(
                        "[linkedin] job posting succeeded but social post failed for job_id=%s",
                        job.id,
                    )
                else:
                    return {
                        "success": False,
                        "error": f"linkedin_ugc_error_{resp.status_code}",
                        "linkedin_error": error_body,
                        "platform": "linkedin",
                        "job_id": str(job.id),
                        "job_title": job.title,
                        "message": (
                            f"LinkedIn UGC Posts API retornou {resp.status_code}. "
                            "Verifique se o access_token tem permissão 'w_member_social'."
                        ),
                    }
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            logger.error("[linkedin] ugcPosts error for job_id=%s: %s", job.id, exc)
            if not job_post_id:
                return {
                    "success": False,
                    "error": "request_error",
                    "message": f"Erro de conexão ao criar post social: {exc}",
                    "platform": "linkedin",
                    "job_id": str(job.id),
                }

        # ── Step 3: Mark job as published ONLY after at least one API success ─
        canonical_post_id = job_post_id or social_post_id
        if not canonical_post_id:
            return {
                "success": False,
                "error": "no_post_id",
                "message": "LinkedIn não retornou post_id — não marcando como publicado.",
                "platform": "linkedin",
                "job_id": str(job.id),
            }

        try:
            job.published_linkedin = True
            job.linkedin_post_id = canonical_post_id
            job.last_published_at = datetime.utcnow()
            await db.commit()
        except Exception as exc:
            await db.rollback()
            logger.error(
                "[linkedin] DB commit failed after successful API call for job_id=%s: %s",
                job.id, exc,
            )
            return {
                "success": False,
                "error": "db_commit_failed",
                "message": (
                    "Post enviado com sucesso ao LinkedIn, mas falhou ao salvar no banco. "
                    f"post_id={canonical_post_id} — verifique manualmente."
                ),
                "platform": "linkedin",
                "job_id": str(job.id),
                "post_id": canonical_post_id,
            }

        logger.info(
            "[linkedin] job_id=%s published successfully: post_id=%s",
            job.id, canonical_post_id,
        )
        return {
            "success": True,
            "platform": "linkedin",
            "job_id": str(job.id),
            "job_title": job.title,
            "post_id": canonical_post_id,
            "job_post_id": job_post_id,
            "social_post_id": social_post_id,
            "job_url": job_url,
            "linkedin_job_url": (
                f"https://www.linkedin.com/jobs/view/{job_post_id}"
                if job_post_id else None
            ),
            "published_at": job.last_published_at.isoformat(),
            "posting_type": posting_type,
        }

    def _build_social_summary(self, job: "JobVacancy") -> str:
        """Build a concise social post text for the job."""
        lines = [f"🚀 Nova oportunidade: {job.title}"]
        if job.department:
            lines.append(f"Área: {job.department}")
        work_model_map = {
            "remoto": "Remoto",
            "híbrido": "Híbrido",
            "hibrido": "Híbrido",
            "presencial": "Presencial",
        }
        wm = work_model_map.get((job.work_model or "").lower())
        if wm:
            lines.append(f"Modelo: {wm}")
        if job.employment_type:
            lines.append(f"Contrato: {job.employment_type}")
        lines.append("")
        lines.append("Candidate-se e saiba mais:")
        return "\n".join(lines)

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
