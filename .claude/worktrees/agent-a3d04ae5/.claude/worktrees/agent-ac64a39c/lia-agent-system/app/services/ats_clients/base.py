"""
Base ATS Client Interface

Defines the abstract interface that all ATS clients must implement
for bidirectional synchronization between WedoTalent and external ATS platforms.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ATSClientConfig:
    """Configuration for ATS client."""
    api_key: str
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    company_id: Optional[str] = None
    webhook_url: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class ATSCandidate:
    """Normalized candidate data from ATS."""
    ats_id: str
    name: str
    email: str
    phone: Optional[str] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    cv_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
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
    description: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    requirements: Optional[str] = None
    salary_range: Optional[str] = None
    employment_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
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
    ats_id: Optional[str] = None
    wedotalent_id: Optional[str] = None
    changes: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
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
        """Return ATS name (gupy, pandape, stackone)."""
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
    async def get_candidate(self, candidate_id: str) -> Optional[ATSCandidate]:
        """Get a single candidate by ID."""
        pass
    
    @abstractmethod
    async def list_candidates(
        self,
        job_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ATSCandidate]:
        """List candidates with optional filters."""
        pass
    
    @abstractmethod
    async def create_candidate(self, data: Dict[str, Any]) -> ATSCandidate:
        """Create a new candidate in ATS."""
        pass
    
    @abstractmethod
    async def update_candidate(
        self,
        candidate_id: str,
        data: Dict[str, Any]
    ) -> ATSCandidate:
        """Update an existing candidate."""
        pass
    
    @abstractmethod
    async def update_candidate_status(
        self,
        candidate_id: str,
        new_status: str,
        reason: Optional[str] = None
    ) -> bool:
        """Update candidate status/stage."""
        pass
    
    @abstractmethod
    async def add_note(
        self,
        candidate_id: str,
        note: str,
        author: Optional[str] = None
    ) -> bool:
        """Add a note/observation to candidate."""
        pass
    
    # ============== JOB OPERATIONS ==============
    
    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[ATSJob]:
        """Get a single job by ID."""
        pass
    
    @abstractmethod
    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ATSJob]:
        """List jobs with optional filters."""
        pass
    
    # ============== BIDIRECTIONAL SYNC OPERATIONS ==============
    
    async def sync_candidate_to_ats(
        self,
        wedotalent_id: str,
        data: Dict[str, Any],
        ats_id: Optional[str] = None
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
    ) -> Optional[ATSCandidate]:
        """
        Pull candidate data from ATS to WedoTalent.
        
        Args:
            ats_id: ATS candidate ID
            
        Returns:
            Normalized ATSCandidate or None if not found
        """
        logger.info(f"📥 Pulling candidate {ats_id} from {self.name}")
        return await self.get_candidate(ats_id)
    
    async def sync_candidates_from_ats(
        self,
        job_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ATSCandidate]:
        """
        Pull multiple candidates from ATS (bulk sync).
        
        Args:
            job_id: Optional job filter
            since: Optional datetime to get only recent updates
            limit: Maximum candidates to fetch
            
        Returns:
            List of normalized ATSCandidate objects
        """
        logger.info(f"📥 Bulk pulling candidates from {self.name} (job={job_id}, limit={limit})")
        candidates = await self.list_candidates(job_id=job_id, limit=limit)
        
        if since:
            candidates = [
                c for c in candidates
                if c.updated_at and c.updated_at >= since
            ]
        
        return candidates
    
    async def sync_job_from_ats(self, ats_id: str) -> Optional[ATSJob]:
        """
        Pull job data from ATS.
        
        Args:
            ats_id: ATS job ID
            
        Returns:
            Normalized ATSJob or None if not found
        """
        logger.info(f"📥 Pulling job {ats_id} from {self.name}")
        return await self.get_job(ats_id)
    
    async def sync_jobs_from_ats(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ATSJob]:
        """
        Pull all jobs from ATS.
        
        Args:
            status: Optional status filter
            limit: Maximum jobs to fetch
            
        Returns:
            List of normalized ATSJob objects
        """
        logger.info(f"📥 Bulk pulling jobs from {self.name} (status={status}, limit={limit})")
        return await self.list_jobs(status=status, limit=limit)
