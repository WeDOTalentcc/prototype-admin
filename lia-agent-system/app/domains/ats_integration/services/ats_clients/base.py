"""
Base ATS Client Interface

Defines the abstract interface that all ATS clients must implement
for bidirectional synchronization between WedoTalent and external ATS platforms.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class ATSClientConfig:
    """Configuration for ATS client."""
    api_key: str
    api_secret: str | None = None
    base_url: str | None = None
    company_id: str | None = None
    webhook_url: str | None = None
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class ATSCandidate:
    """Normalized candidate data from ATS."""
    ats_id: str
    name: str
    email: str
    phone: str | None = None
    status: str | None = None
    stage: str | None = None
    cv_url: str | None = None
    linkedin_url: str | None = None
    location: str | None = None
    notes: str | None = None
    custom_fields: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    raw_data: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ats_id": self.ats_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "stage": self.stage,
            "cv_url": self.cv_url,
            "linkedin_url": self.linkedin_url,
            "location": self.location,
            "notes": self.notes,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class ATSJob:
    """Normalized job data from ATS."""
    ats_id: str
    title: str
    description: str | None = None
    department: str | None = None
    location: str | None = None
    status: str | None = None
    requirements: str | None = None
    salary_range: str | None = None
    employment_type: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    raw_data: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ats_id": self.ats_id,
            "title": self.title,
            "description": self.description,
            "department": self.department,
            "location": self.location,
            "status": self.status,
            "requirements": self.requirements,
            "salary_range": self.salary_range,
            "employment_type": self.employment_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    action: str  # created, updated, deleted
    ats_id: str | None = None
    wedotalent_id: str | None = None
    changes: list[str] = field(default_factory=list)
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action,
            "ats_id": self.ats_id,
            "wedotalent_id": self.wedotalent_id,
            "changes": self.changes,
            "error": self.error,
        }


class ATSClient(ABC):
    """
    Abstract base class for ATS API clients.
    
    Implements the Template Method pattern - concrete clients implement
    the abstract methods while inheriting common sync logic.
    """
    
    def __init__(self, config: ATSClientConfig):
        self.config = config
        self._validate_config()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return ATS name (gupy, pandape, merge)."""
        pass
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate configuration has required fields."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the API connection is working."""
        pass
    
    # ============== CANDIDATE OPERATIONS ==============
    
    @abstractmethod
    async def get_candidate(self, candidate_id: str) -> ATSCandidate | None:
        """Get a single candidate by ID."""
        pass
    
    @abstractmethod
    async def list_candidates(
        self,
        job_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[ATSCandidate]:
        """List candidates with optional filters."""
        pass
    
    @abstractmethod
    async def create_candidate(self, data: dict[str, Any]) -> ATSCandidate:
        """Create a new candidate in ATS."""
        pass
    
    @abstractmethod
    async def update_candidate(
        self,
        candidate_id: str,
        data: dict[str, Any]
    ) -> ATSCandidate:
        """Update an existing candidate."""
        pass
    
    @abstractmethod
    async def update_candidate_status(
        self,
        candidate_id: str,
        new_status: str,
        reason: str | None = None
    ) -> bool:
        """Update candidate status/stage."""
        pass
    
    @abstractmethod
    async def add_note(
        self,
        candidate_id: str,
        note: str,
        author: str | None = None
    ) -> bool:
        """Add a note/observation to candidate."""
        pass
    
    # ============== JOB OPERATIONS ==============
    
    @abstractmethod
    async def get_job(self, job_id: str) -> ATSJob | None:
        """Get a single job by ID."""
        pass
    
    @abstractmethod
    async def list_jobs(
        self,
        status: str | None = None,
        limit: int = 100
    ) -> list[ATSJob]:
        """List jobs with optional filters."""
        pass
    
    # ============== BIDIRECTIONAL SYNC OPERATIONS ==============
    
    async def sync_candidate_to_ats(
        self,
        wedotalent_id: str,
        data: dict[str, Any],
        ats_id: str | None = None
    ) -> SyncResult:
        """
        Push candidate data from WedoTalent to ATS.
        
        If ats_id provided, updates existing. Otherwise creates new.
        
        Args:
            wedotalent_id: WedoTalent internal candidate ID
            data: Candidate data to sync
            ats_id: Optional existing ATS ID for updates
            
        Returns:
            SyncResult with operation details
        """
        try:
            if ats_id:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"📤 Updating candidate {ats_id} in {self.name}")
                result = await self.update_candidate(ats_id, data)
                return SyncResult(
                    success=True,
                    action="updated",
                    ats_id=result.ats_id,
                    wedotalent_id=wedotalent_id,
                    changes=list(data.keys())
                )
            else:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"📤 Creating new candidate in {self.name}")
                result = await self.create_candidate(data)
                return SyncResult(
                    success=True,
                    action="created",
                    ats_id=result.ats_id,
                    wedotalent_id=wedotalent_id,
                    changes=list(data.keys())
                )
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"❌ Failed to sync candidate to {self.name}: {e}")
            return SyncResult(
                success=False,
                action="error",
                wedotalent_id=wedotalent_id,
                error=str(e)
            )
    
    async def sync_candidate_from_ats(
        self,
        ats_id: str
    ) -> ATSCandidate | None:
        """
        Pull candidate data from ATS to WedoTalent.
        
        Args:
            ats_id: ATS candidate ID
            
        Returns:
            Normalized ATSCandidate or None if not found
        """
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"📥 Pulling candidate {ats_id} from {self.name}")
        return await self.get_candidate(ats_id)
    
    async def sync_candidates_from_ats(
        self,
        job_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100
    ) -> list[ATSCandidate]:
        """
        Pull multiple candidates from ATS (bulk sync).
        
        Args:
            job_id: Optional job filter
            since: Optional datetime to get only recent updates
            limit: Maximum candidates to fetch
            
        Returns:
            List of normalized ATSCandidate objects
        """
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"📥 Bulk pulling candidates from {self.name} (job={job_id}, limit={limit})")
        candidates = await self.list_candidates(job_id=job_id, limit=limit)
        
        if since:
            candidates = [
                c for c in candidates
                if c.updated_at and c.updated_at >= since
            ]
        
        return candidates
    
    async def sync_job_from_ats(self, ats_id: str) -> ATSJob | None:
        """
        Pull job data from ATS.
        
        Args:
            ats_id: ATS job ID
            
        Returns:
            Normalized ATSJob or None if not found
        """
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"📥 Pulling job {ats_id} from {self.name}")
        return await self.get_job(ats_id)
    
    async def sync_jobs_from_ats(
        self,
        status: str | None = None,
        limit: int = 100
    ) -> list[ATSJob]:
        """
        Pull all jobs from ATS.
        
        Args:
            status: Optional status filter
            limit: Maximum jobs to fetch
            
        Returns:
            List of normalized ATSJob objects
        """
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"📥 Bulk pulling jobs from {self.name} (status={status}, limit={limit})")
        return await self.list_jobs(status=status, limit=limit)
