"""
Gupy ATS Client Implementation

Gupy is a popular Brazilian ATS platform.
API Docs: https://developers.gupy.io/
"""
import logging
from datetime import datetime
from typing import Any

import httpx

from app.domains.ats_integration.services.ats_clients.ats_pii_filter import filter_inbound_text, filter_outbound
from app.shared.resilience.circuit_breaker import GUPY_CIRCUIT, circuit_breaker_decorator

from .base import ATSCandidate, ATSClient, ATSJob

logger = logging.getLogger(__name__)


class GupyClient(ATSClient):
    """
    Gupy ATS API Client.
    
    Implements bidirectional sync with Gupy platform.
    Supports CRUD operations for candidates and jobs.
    """
    
    DEFAULT_BASE_URL = "https://api.gupy.io/api/v1"
    
    @property
    def name(self) -> str:
        return "gupy"
    
    def _validate_config(self) -> None:
        if not self.config.api_key:
            raise ValueError("Gupy API key is required")
        if not self.config.base_url:
            self.config.base_url = self.DEFAULT_BASE_URL
    
    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @circuit_breaker_decorator(GUPY_CIRCUIT)
    async def test_connection(self) -> bool:
        """Test Gupy API connection."""
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
            logger.error(f"Gupy connection test failed: {e}")
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
        """Parse Gupy candidate response to normalized format."""
        # Sanitizar campos de texto livre antes de armazenar (LGPD Art. 46)
        data = filter_inbound_text(data, "gupy")
        name = data.get("nome") or data.get("name") or ""
        email = data.get("email") or ""

        return ATSCandidate(
            ats_id=str(data.get("id", "")),
            name=name,
            email=email,
            phone=data.get("telefone") or data.get("phone"),
            status=data.get("fase") or data.get("status"),
            stage=data.get("etapa") or data.get("step"),
            cv_url=data.get("curriculo_url") or data.get("resumeUrl"),
            linkedin_url=data.get("linkedin") or data.get("linkedinUrl"),
            location=data.get("cidade") or data.get("city"),
            notes=data.get("observacoes") or data.get("notes"),
            custom_fields=data.get("campos_customizados") or data.get("customFields"),
            created_at=self._parse_datetime(data.get("created_at") or data.get("createdAt")),
            updated_at=self._parse_datetime(data.get("updated_at") or data.get("updatedAt")),
            raw_data=data
        )
    
    @circuit_breaker_decorator(GUPY_CIRCUIT)
    async def get_candidate(self, candidate_id: str) -> ATSCandidate | None:
        """Get candidate from Gupy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/applications/{candidate_id}",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
                if response.status_code == 404:
                    logger.warning(f"Candidate {candidate_id} not found in Gupy")
                    return None
                response.raise_for_status()
                return self._parse_candidate(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Failed to get Gupy candidate {candidate_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get Gupy candidate {candidate_id}: {e}")
            raise
    
    @circuit_breaker_decorator(GUPY_CIRCUIT)
    async def list_candidates(
        self,
        job_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[ATSCandidate]:
        """List candidates from Gupy."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if job_id:
            params["vaga_id"] = job_id
        if status:
            params["fase"] = status
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/applications",
                    headers=self._get_headers(),
                    params=params,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                data = response.json()
                candidates_data = data.get("data", []) if isinstance(data, dict) else data
                logger.info(f"✅ Fetched {len(candidates_data)} candidates from Gupy")
                return [self._parse_candidate(c) for c in candidates_data]
        except Exception as e:
            logger.error(f"Failed to list Gupy candidates: {e}")
            raise
    
    @circuit_breaker_decorator(GUPY_CIRCUIT)
    async def create_candidate(self, data: dict[str, Any], has_consent: bool = True) -> ATSCandidate:
        """Create candidate in Gupy."""
        # Filtrar campos sensíveis se sem consentimento (LGPD Art. 6)
        data = filter_outbound(data, "gupy", has_consent=has_consent)
        gupy_data = {
            "nome": data.get("name"),
            "email": data.get("email"),
            "telefone": data.get("phone"),
            "linkedin": data.get("linkedin_url"),
            "cidade": data.get("location"),
            "vaga_id": data.get("job_id"),
        }
        gupy_data = {k: v for k, v in gupy_data.items() if v is not None}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/applications",
                    headers=self._get_headers(),
                    json=gupy_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                result = self._parse_candidate(response.json())
                logger.info(f"✅ Created candidate {result.ats_id} in Gupy")
                return result
        except Exception as e:
            logger.error(f"Failed to create Gupy candidate: {e}")
            raise
    
    @circuit_breaker_decorator(GUPY_CIRCUIT)
    async def update_candidate(
        self,
        candidate_id: str,
        data: dict[str, Any],
        has_consent: bool = True,
    ) -> ATSCandidate:
        """Update candidate in Gupy."""
        # Filtrar campos sensíveis se sem consentimento (LGPD Art. 6)
        data = filter_outbound(data, "gupy", has_consent=has_consent)
        gupy_data: dict[str, Any] = {}

        field_mapping = {
            "status": "fase",
            "stage": "etapa",
            "notes": "observacoes",
            "rejection_reason": "motivo_reprovacao",
            "phone": "telefone",
            "location": "cidade",
            "linkedin_url": "linkedin",
        }
        
        for wedo_field, gupy_field in field_mapping.items():
            if wedo_field in data:
                gupy_data[gupy_field] = data[wedo_field]
        
        if not gupy_data:
            current = await self.get_candidate(candidate_id)
            if current:
                return current
            raise ValueError(f"Candidate {candidate_id} not found and no data to update")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.config.base_url}/applications/{candidate_id}",
                    headers=self._get_headers(),
                    json=gupy_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                result = self._parse_candidate(response.json())
                logger.info(f"✅ Updated candidate {candidate_id} in Gupy: {list(gupy_data.keys())}")
                return result
        except Exception as e:
            logger.error(f"Failed to update Gupy candidate {candidate_id}: {e}")
            raise
    
    async def update_candidate_status(
        self,
        candidate_id: str,
        new_status: str,
        reason: str | None = None
    ) -> bool:
        """Update candidate status in Gupy."""
        data: dict[str, Any] = {"status": new_status}
        if reason:
            data["rejection_reason"] = reason
        
        try:
            await self.update_candidate(candidate_id, data)
            logger.info(f"✅ Updated status of candidate {candidate_id} to {new_status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update Gupy candidate status: {e}")
            return False
    
    @circuit_breaker_decorator(GUPY_CIRCUIT)
    async def add_note(
        self,
        candidate_id: str,
        note: str,
        author: str | None = None
    ) -> bool:
        """Add note to candidate in Gupy."""
        note_data = {
            "texto": note,
            "autor": author or "LIA System"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/applications/{candidate_id}/observacoes",
                    headers=self._get_headers(),
                    json=note_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                logger.info(f"✅ Added note to candidate {candidate_id} in Gupy")
                return True
        except Exception as e:
            logger.error(f"Failed to add note to Gupy candidate {candidate_id}: {e}")
            return False
    
    def _parse_job(self, data: dict[str, Any]) -> ATSJob:
        """Parse Gupy job response."""
        return ATSJob(
            ats_id=str(data.get("id", "")),
            title=data.get("titulo") or data.get("name") or "",
            description=data.get("descricao") or data.get("description"),
            department=data.get("departamento") or data.get("department"),
            location=data.get("cidade") or data.get("city"),
            status=data.get("status"),
            requirements=data.get("requisitos") or data.get("requirements"),
            employment_type=data.get("tipo_contrato") or data.get("employmentType"),
            created_at=self._parse_datetime(data.get("created_at") or data.get("createdAt")),
            updated_at=self._parse_datetime(data.get("updated_at") or data.get("updatedAt")),
            raw_data=data
        )
    
    @circuit_breaker_decorator(GUPY_CIRCUIT)
    async def get_job(self, job_id: str) -> ATSJob | None:
        """Get job from Gupy."""
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
            logger.error(f"Failed to get Gupy job {job_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get Gupy job {job_id}: {e}")
            raise
    
    @circuit_breaker_decorator(GUPY_CIRCUIT)
    async def list_jobs(
        self,
        status: str | None = None,
        limit: int = 100
    ) -> list[ATSJob]:
        """List jobs from Gupy."""
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
                jobs_data = data.get("data", []) if isinstance(data, dict) else data
                logger.info(f"✅ Fetched {len(jobs_data)} jobs from Gupy")
                return [self._parse_job(j) for j in jobs_data]
        except Exception as e:
            logger.error(f"Failed to list Gupy jobs: {e}")
            raise
