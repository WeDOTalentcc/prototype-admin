"""
Pandapé ATS Client Implementation

Pandapé is a Brazilian ATS platform commonly used in Latin America.
API Docs: https://api-ats.pandape.com/index.html
"""
import logging
from datetime import datetime
from typing import Any

import httpx

from app.domains.ats_integration.services.ats_clients.ats_pii_filter import filter_inbound_text, filter_outbound
from app.shared.resilience.circuit_breaker import PANDAPE_CIRCUIT, circuit_breaker_decorator

from .base import ATSCandidate, ATSClient, ATSJob

logger = logging.getLogger(__name__)


class PandapeClient(ATSClient):
    """
    Pandapé ATS API Client.
    
    Implements bidirectional sync with Pandapé platform.
    Supports CRUD operations for candidates and jobs.
    """
    
    DEFAULT_BASE_URL = "https://api-ats.pandape.com/api/v2"
    
    @property
    def name(self) -> str:
        return "pandape"
    
    def _validate_config(self) -> None:
        if not self.config.api_key:
            raise ValueError("Pandapé API key is required")
        if not self.config.base_url:
            self.config.base_url = self.DEFAULT_BASE_URL
    
    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.config.company_id:
            headers["X-Company-Id"] = self.config.company_id
        return headers
    
    @circuit_breaker_decorator(PANDAPE_CIRCUIT)
    async def test_connection(self) -> bool:
        """Test Pandapé API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/jobs",
                    headers=self._get_headers(),
                    params={"limit": 1},
                    timeout=self.config.timeout
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Pandapé connection test failed: {e}")
            return False
    
    def _parse_datetime(self, value: Any) -> datetime | None:
        """Safely parse datetime from various formats."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            if "T" in str(value):
                return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return datetime.strptime(str(value), "%Y-%m-%d")
        except (ValueError, TypeError):
            return None
    
    def _parse_candidate(self, data: dict[str, Any]) -> ATSCandidate:
        """Parse Pandapé candidate response to normalized format."""
        # Sanitizar campos de texto livre antes de armazenar (LGPD Art. 46)
        data = filter_inbound_text(data, "pandape")
        name = data.get("nome_completo") or data.get("name") or data.get("fullName") or ""
        email = data.get("email_principal") or data.get("email") or ""
        
        return ATSCandidate(
            ats_id=str(data.get("id", "") or data.get("candidato_id", "")),
            name=name,
            email=email,
            phone=data.get("telefone_celular") or data.get("phone") or data.get("phoneNumber"),
            status=data.get("situacao") or data.get("status"),
            stage=data.get("etapa") or data.get("stage"),
            cv_url=data.get("cv_anexo") or data.get("resumeUrl"),
            linkedin_url=data.get("linkedin_url") or data.get("linkedin"),
            location=data.get("cidade") or data.get("city") or data.get("location"),
            notes=data.get("parecer_rh") or data.get("notes"),
            custom_fields=data.get("campos_adicionais") or data.get("customFields"),
            created_at=self._parse_datetime(data.get("data_cadastro") or data.get("createdAt")),
            updated_at=self._parse_datetime(data.get("data_atualizacao") or data.get("updatedAt")),
            raw_data=data
        )
    
    @circuit_breaker_decorator(PANDAPE_CIRCUIT)
    async def get_candidate(self, candidate_id: str) -> ATSCandidate | None:
        """Get candidate from Pandapé."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/candidates/{candidate_id}",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
                if response.status_code == 404:
                    logger.warning(f"Candidate {candidate_id} not found in Pandapé")
                    return None
                response.raise_for_status()
                return self._parse_candidate(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Failed to get Pandapé candidate {candidate_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get Pandapé candidate {candidate_id}: {e}")
            raise
    
    @circuit_breaker_decorator(PANDAPE_CIRCUIT)
    async def list_candidates(
        self,
        job_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[ATSCandidate]:
        """List candidates from Pandapé."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if job_id:
            params["vaga_id"] = job_id
        if status:
            params["situacao"] = status
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/candidates",
                    headers=self._get_headers(),
                    params=params,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                data = response.json()
                candidates_data = data.get("data", data) if isinstance(data, dict) else data
                if not isinstance(candidates_data, list):
                    candidates_data = [candidates_data] if candidates_data else []
                logger.info(f"✅ Fetched {len(candidates_data)} candidates from Pandapé")
                return [self._parse_candidate(c) for c in candidates_data]
        except Exception as e:
            logger.error(f"Failed to list Pandapé candidates: {e}")
            raise
    
    @circuit_breaker_decorator(PANDAPE_CIRCUIT)
    async def create_candidate(self, data: dict[str, Any], has_consent: bool = True) -> ATSCandidate:
        """Create candidate in Pandapé."""
        # Filtrar campos sensíveis se sem consentimento (LGPD Art. 6)
        data = filter_outbound(data, "pandape", has_consent=has_consent)
        pandape_data = {
            "nome_completo": data.get("name"),
            "email_principal": data.get("email"),
            "telefone_celular": data.get("phone"),
            "linkedin_url": data.get("linkedin_url"),
            "cidade": data.get("location"),
            "vaga_id": data.get("job_id"),
            "pretensao_salarial": data.get("salary_expectation"),
        }
        pandape_data = {k: v for k, v in pandape_data.items() if v is not None}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/candidates",
                    headers=self._get_headers(),
                    json=pandape_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                result = self._parse_candidate(response.json())
                logger.info(f"✅ Created candidate {result.ats_id} in Pandapé")
                return result
        except Exception as e:
            logger.error(f"Failed to create Pandapé candidate: {e}")
            raise
    
    @circuit_breaker_decorator(PANDAPE_CIRCUIT)
    async def update_candidate(
        self,
        candidate_id: str,
        data: dict[str, Any],
        has_consent: bool = True,
    ) -> ATSCandidate:
        """Update candidate in Pandapé."""
        # Filtrar campos sensíveis se sem consentimento (LGPD Art. 6)
        data = filter_outbound(data, "pandape", has_consent=has_consent)
        pandape_data: dict[str, Any] = {}
        
        field_mapping = {
            "status": "situacao",
            "stage": "etapa",
            "notes": "parecer_rh",
            "rejection_reason": "motivo_rejeicao",
            "phone": "telefone_celular",
            "location": "cidade",
            "linkedin_url": "linkedin_url",
            "salary_expectation": "pretensao_salarial",
            "wsi_score": "nota_avaliacao",
        }
        
        for wedo_field, pandape_field in field_mapping.items():
            if wedo_field in data:
                pandape_data[pandape_field] = data[wedo_field]
        
        if not pandape_data:
            current = await self.get_candidate(candidate_id)
            if current:
                return current
            raise ValueError(f"Candidate {candidate_id} not found and no data to update")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.config.base_url}/candidates/{candidate_id}",
                    headers=self._get_headers(),
                    json=pandape_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                result = self._parse_candidate(response.json())
                logger.info(f"✅ Updated candidate {candidate_id} in Pandapé: {list(pandape_data.keys())}")
                return result
        except Exception as e:
            logger.error(f"Failed to update Pandapé candidate {candidate_id}: {e}")
            raise
    
    async def update_candidate_status(
        self,
        candidate_id: str,
        new_status: str,
        reason: str | None = None
    ) -> bool:
        """Update candidate status in Pandapé."""
        data: dict[str, Any] = {"status": new_status}
        if reason:
            data["rejection_reason"] = reason
        
        try:
            await self.update_candidate(candidate_id, data)
            logger.info(f"✅ Updated status of candidate {candidate_id} to {new_status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update Pandapé candidate status: {e}")
            return False
    
    @circuit_breaker_decorator(PANDAPE_CIRCUIT)
    async def add_note(
        self,
        candidate_id: str,
        note: str,
        author: str | None = None
    ) -> bool:
        """Add note to candidate in Pandapé."""
        note_data = {
            "texto": note,
            "autor": author or "LIA System",
            "data": datetime.utcnow().isoformat()
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/candidates/{candidate_id}/observacoes",
                    headers=self._get_headers(),
                    json=note_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                logger.info(f"✅ Added note to candidate {candidate_id} in Pandapé")
                return True
        except Exception as e:
            logger.error(f"Failed to add note to Pandapé candidate {candidate_id}: {e}")
            return False
    
    def _parse_job(self, data: dict[str, Any]) -> ATSJob:
        """Parse Pandapé job response."""
        return ATSJob(
            ats_id=str(data.get("id", "") or data.get("vaga_id", "")),
            title=data.get("titulo") or data.get("title") or data.get("name") or "",
            description=data.get("descricao") or data.get("description"),
            department=data.get("area") or data.get("departamento") or data.get("department"),
            location=data.get("cidade") or data.get("city") or data.get("location"),
            status=data.get("status") or data.get("situacao"),
            requirements=data.get("requisitos") or data.get("requirements"),
            employment_type=data.get("tipo_contrato") or data.get("employmentType") or data.get("type"),
            salary_range=data.get("faixa_salarial") or data.get("salaryRange"),
            created_at=self._parse_datetime(data.get("data_abertura") or data.get("createdAt")),
            updated_at=self._parse_datetime(data.get("data_atualizacao") or data.get("updatedAt")),
            raw_data=data
        )
    
    @circuit_breaker_decorator(PANDAPE_CIRCUIT)
    async def get_job(self, job_id: str) -> ATSJob | None:
        """Get job from Pandapé."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/jobs/{job_id}",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return self._parse_job(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Failed to get Pandapé job {job_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get Pandapé job {job_id}: {e}")
            raise
    
    @circuit_breaker_decorator(PANDAPE_CIRCUIT)
    async def list_jobs(
        self,
        status: str | None = None,
        limit: int = 100
    ) -> list[ATSJob]:
        """List jobs from Pandapé."""
        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/jobs",
                    headers=self._get_headers(),
                    params=params,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                data = response.json()
                jobs_data = data.get("data", data) if isinstance(data, dict) else data
                if not isinstance(jobs_data, list):
                    jobs_data = [jobs_data] if jobs_data else []
                logger.info(f"✅ Fetched {len(jobs_data)} jobs from Pandapé")
                return [self._parse_job(j) for j in jobs_data]
        except Exception as e:
            logger.error(f"Failed to list Pandapé jobs: {e}")
            raise
