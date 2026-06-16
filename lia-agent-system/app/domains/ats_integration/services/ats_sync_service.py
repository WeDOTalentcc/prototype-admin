"""
ATS Sync Service - Centralized ATS synchronization engine.

This service manages bidirectional synchronization between WedoTalent and client ATSs:
- Push: Receives triggers from agents when data changes, syncs to ATS
- Pull: Fetches data from ATS to keep WedoTalent in sync
- Validates if fields exist in client ATS
- Executes sync for supported fields only
- Stores unsupported data in WedoTalent extended area
- Maintains audit log for all operations

Design Principle:
- WedoTalent is the source of truth for all data
- Bidirectional sync keeps both systems updated
- Data without ATS field mapping stays in WedoTalent only
- NO field creation in client ATS (not authorized)
"""
import logging
import os
import uuid
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any


from app.domains.ats_integration.services.ats_clients.base import ATSClient, ATSClientConfig
from app.domains.ats_integration.services.ats_clients.gupy import GupyClient
from app.domains.ats_integration.services.ats_clients.merge import MergeClient
from app.domains.ats_integration.services.ats_clients.pandape import PandapeClient

logger = logging.getLogger(__name__)




class ATSClientNotConfiguredError(Exception):
    """Raised when trigger_sync is called but no ATS client is configured.

    Distinct from ATSSyncResult.ATS_ERROR (real client failure).
    Callers that catch this must NOT log ats_synced=True -- the sync was skipped.
    """
    def __init__(self, ats_type: str) -> None:
        super().__init__(
            f"ATS client not configured for type={ats_type!r}. "
            "Sync skipped -- configure the integration in Settings."
        )
        self.ats_type = ats_type

class ATSSyncTrigger(StrEnum):
    """Events that trigger ATS synchronization."""
    STATUS_CHANGE = "status_change"
    CANDIDATE_CREATED = "candidate_created"
    CANDIDATE_UPDATED = "candidate_updated"
    SCORE_UPDATED = "score_updated"
    PARECER_GENERATED = "parecer_generated"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_SENT = "offer_sent"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_REJECTED = "offer_rejected"
    CANDIDATE_HIRED = "candidate_hired"
    CANDIDATE_REJECTED = "candidate_rejected"
    PULL_FROM_ATS = "pull_from_ats"
    BULK_SYNC = "bulk_sync"


class ATSSyncAction(StrEnum):
    """Types of sync actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ATTACH_DOCUMENT = "attach_document"
    PULL = "pull"
    BULK_PULL = "bulk_pull"


class ATSSyncResult(StrEnum):
    """Result of sync attempt."""
    SUCCESS = "success"
    FIELD_NOT_MAPPED = "field_not_mapped"
    ATS_ERROR = "ats_error"
    NOT_APPLICABLE = "not_applicable"
    QUEUED = "queued"
    NO_CLIENT = "no_client_configured"


class ATSFieldMapping:
    """
    Field mapping between WedoTalent and client ATSs.
    
    Defines which fields can be synced to which ATS.
    Fields not in mapping will be stored only in WedoTalent.
    """
    
    GUPY_MAPPINGS = {
        "candidate_id": {"ats_field": "application_id", "sync": True},
        "name": {"ats_field": "nome", "sync": True},
        "email": {"ats_field": "email", "sync": True},
        "phone": {"ats_field": "telefone", "sync": True},
        "status": {"ats_field": "fase", "sync": True},
        "cv_url": {"ats_field": "curriculo_url", "sync": True},
        "linkedin_url": {"ats_field": "linkedin", "sync": True},
        "location": {"ats_field": "cidade", "sync": True},
        "wsi_score": {"ats_field": None, "sync": False, "note": "Gupy não tem campo para score WSI"},
        "salary_current": {"ats_field": None, "sync": False, "note": "Dado sensível - não sincronizar"},
        "salary_expectation": {"ats_field": None, "sync": False, "note": "Dado sensível - não sincronizar"},
        "behavioral_score": {"ats_field": None, "sync": False},
        "big_five_profile": {"ats_field": None, "sync": False},
        "dreyfus_levels": {"ats_field": None, "sync": False},
        "parecer": {"ats_field": "observacoes", "sync": True, "type": "text_append"},
        "rejection_reason": {"ats_field": "motivo_reprovacao", "sync": True},
    }
    
    PANDAPE_MAPPINGS = {
        "candidate_id": {"ats_field": "candidato_id", "sync": True},
        "name": {"ats_field": "nome_completo", "sync": True},
        "email": {"ats_field": "email_principal", "sync": True},
        "phone": {"ats_field": "telefone_celular", "sync": True},
        "status": {"ats_field": "situacao", "sync": True},
        "cv_url": {"ats_field": "cv_anexo", "sync": True},
        "linkedin_url": {"ats_field": "linkedin_url", "sync": True},
        "location": {"ats_field": "cidade", "sync": True},
        "wsi_score": {"ats_field": "nota_avaliacao", "sync": True, "note": "Pandapé suporta score"},
        "salary_current": {"ats_field": None, "sync": False, "note": "Dado sensível"},
        "salary_expectation": {"ats_field": "pretensao_salarial", "sync": True},
        "parecer": {"ats_field": "parecer_rh", "sync": True},
        "rejection_reason": {"ats_field": "motivo_rejeicao", "sync": True},
    }
    
    MERGE_MAPPINGS = {
        "candidate_id": {"ats_field": "id", "sync": True},
        "name": {"ats_field": "first_name,last_name", "sync": True, "note": "Split into first/last name"},
        "email": {"ats_field": "email_addresses", "sync": True, "type": "array"},
        "phone": {"ats_field": "phone_numbers", "sync": True, "type": "array"},
        "status": {"ats_field": "current_stage", "sync": True},
        "cv_url": {"ats_field": "attachments", "sync": True, "type": "array", "note": "Resume attachment"},
        "linkedin_url": {"ats_field": "urls", "sync": True, "type": "array"},
        "location": {"ats_field": "locations", "sync": True, "type": "array"},
        "wsi_score": {"ats_field": "custom_fields.wsi_score", "sync": True, "note": "Via custom field if supported"},
        "salary_current": {"ats_field": None, "sync": False, "note": "Dado sensível - não sincronizar"},
        "salary_expectation": {"ats_field": None, "sync": False, "note": "Dado sensível - não sincronizar"},
        "behavioral_score": {"ats_field": None, "sync": False},
        "big_five_profile": {"ats_field": None, "sync": False},
        "dreyfus_levels": {"ats_field": None, "sync": False},
        "parecer": {"ats_field": "notes", "sync": True, "type": "note_create"},
        "rejection_reason": {"ats_field": None, "sync": False, "note": "Depends on ATS support"},
    }
    
    @classmethod
    def get_mapping(cls, ats_type: str) -> dict[str, Any]:
        """Get field mappings for a specific ATS."""
        mappings = {
            "gupy": cls.GUPY_MAPPINGS,
            "pandape": cls.PANDAPE_MAPPINGS,
            "merge": cls.MERGE_MAPPINGS,
        }
        return mappings.get(ats_type.lower(), {})
    
    @classmethod
    def can_sync_field(cls, ats_type: str, field_name: str) -> bool:
        """Check if a field can be synced to the specified ATS."""
        mapping = cls.get_mapping(ats_type)
        field_config = mapping.get(field_name, {})
        return field_config.get("sync", False)
    
    @classmethod
    def get_ats_field_name(cls, ats_type: str, field_name: str) -> str | None:
        """Get the corresponding ATS field name."""
        mapping = cls.get_mapping(ats_type)
        field_config = mapping.get(field_name, {})
        return field_config.get("ats_field")


class ATSSyncAuditLog:
    """Audit log entry for sync operations."""
    
    def __init__(
        self,
        sync_id: str,
        trigger: ATSSyncTrigger,
        action: ATSSyncAction,
        source_agent: str,
        ats_type: str,
        candidate_id: str | None,
        job_id: str | None,
        fields_synced: list[str],
        fields_skipped: list[dict[str, str]],
        result: ATSSyncResult,
        ats_response: dict[str, Any] | None,
        error_message: str | None,
        timestamp: datetime,
        direction: str = "push"
    ):
        self.sync_id = sync_id
        self.trigger = trigger
        self.action = action
        self.source_agent = source_agent
        self.ats_type = ats_type
        self.candidate_id = candidate_id
        self.job_id = job_id
        self.fields_synced = fields_synced
        self.fields_skipped = fields_skipped
        self.result = result
        self.ats_response = ats_response
        self.error_message = error_message
        self.timestamp = timestamp
        self.direction = direction
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "sync_id": self.sync_id,
            "trigger": self.trigger.value,
            "action": self.action.value,
            "source_agent": self.source_agent,
            "ats_type": self.ats_type,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "fields_synced": self.fields_synced,
            "fields_skipped": self.fields_skipped,
            "result": self.result.value,
            "ats_response": self.ats_response,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction,
        }


class ATSSyncService:
    """
    Central service for bidirectional ATS synchronization.
    
    Supports:
    - Push: Send data from WedoTalent to ATS
    - Pull: Fetch data from ATS to WedoTalent
    - Bulk sync operations
    - Audit trail for all operations
    """
    
    def __init__(self):
        self.audit_log: list[ATSSyncAuditLog] = []
        self.supported_ats = ["gupy", "pandape", "merge"]
        self._clients: dict[str, ATSClient] = {}
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize ATS clients from environment variables."""
        gupy_key = os.environ.get("GUPY_API_KEY")
        if gupy_key:
            try:
                config = ATSClientConfig(
                    api_key=gupy_key,
                    base_url=os.environ.get("GUPY_BASE_URL"),
                    company_id=os.environ.get("GUPY_COMPANY_ID"),
                )
                self._clients["gupy"] = GupyClient(config)
                logger.info("✅ Gupy client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gupy client: {e}")
        
        pandape_key = os.environ.get("PANDAPE_API_KEY")
        if pandape_key:
            try:
                config = ATSClientConfig(
                    api_key=pandape_key,
                    base_url=os.environ.get("PANDAPE_BASE_URL"),
                    company_id=os.environ.get("PANDAPE_COMPANY_ID"),
                )
                self._clients["pandape"] = PandapeClient(config)
                logger.info("✅ Pandapé client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Pandapé client: {e}")
        
        merge_key = os.environ.get("MERGE_API_KEY")
        if merge_key:
            try:
                config = ATSClientConfig(
                    api_key=merge_key,
                    base_url=os.environ.get("MERGE_API_BASE_URL", "https://api.merge.dev/api/ats/v1"),
                    company_id=os.environ.get("MERGE_ACCOUNT_TOKEN"),
                )
                self._clients["merge"] = MergeClient(config)
                logger.info("✅ Merge.dev client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Merge.dev client: {e}")
    
    def register_client(self, ats_type: str, client: ATSClient) -> None:
        """Register an ATS client manually."""
        self._clients[ats_type.lower()] = client
        logger.info(f"✅ Registered {ats_type} client")
    
    def get_client(self, ats_type: str) -> ATSClient | None:
        """Get an ATS client by type."""
        return self._clients.get(ats_type.lower())
    
    def has_client(self, ats_type: str) -> bool:
        """Check if an ATS client is configured."""
        return ats_type.lower() in self._clients
    
    async def test_connection(self, ats_type: str) -> bool:
        """Test connection to an ATS."""
        client = self.get_client(ats_type)
        if not client:
            return False
        return await client.test_connection()
    
    async def trigger_sync(
        self,
        trigger: ATSSyncTrigger,
        source_agent: str,
        ats_type: str,
        candidate_id: str | None = None,
        job_id: str | None = None,
        data: dict[str, Any] | None = None,
        force_sync: bool = False
    ) -> dict[str, Any]:
        """
        Trigger a push sync operation.
        
        Called by agents when data changes that should be synced to ATS.
        
        Args:
            trigger: Type of event triggering sync
            source_agent: Name of agent triggering sync
            ats_type: Target ATS type (gupy, pandape, merge)
            candidate_id: ID of candidate being synced
            job_id: ID of job vacancy
            data: Data to sync
            force_sync: Force sync even for non-critical fields
            
        Returns:
            Sync result with details of what was synced
        """
        sync_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        logger.info(f"🔄 ATS Sync triggered: {trigger.value} by {source_agent}")
        logger.info(f"   Target ATS: {ats_type}, Candidate: {candidate_id}, Job: {job_id}")
        
        if ats_type.lower() not in self.supported_ats:
            return self._create_result(
                sync_id=sync_id,
                trigger=trigger,
                source_agent=source_agent,
                ats_type=ats_type,
                result=ATSSyncResult.NOT_APPLICABLE,
                message=f"ATS type '{ats_type}' not supported",
                timestamp=timestamp
            )
        
        if not data:
            data = {}
        
        fields_synced = []
        fields_skipped = []
        wedotalent_only = []
        
        for field_name, field_value in data.items():
            if ATSFieldMapping.can_sync_field(ats_type, field_name):
                ats_field = ATSFieldMapping.get_ats_field_name(ats_type, field_name)
                if ats_field:
                    fields_synced.append({
                        "wedotalent_field": field_name,
                        "ats_field": ats_field,
                        "value": field_value
                    })
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.info(f"   ✅ Will sync: {field_name} → {ats_field}")
            else:
                mapping = ATSFieldMapping.get_mapping(ats_type).get(field_name, {})
                reason = mapping.get("note", "Campo não mapeado no ATS")
                fields_skipped.append({
                    "field": field_name,
                    "reason": reason
                })
                wedotalent_only.append(field_name)
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"   ⏭️ Skip ATS (WedoTalent only): {field_name} - {reason}")
        
        action = self._determine_action(trigger)
        
        if fields_synced:
            try:
                ats_response = await self._execute_sync(
                    ats_type=ats_type,
                    action=action,
                    candidate_id=candidate_id,
                    job_id=job_id,
                    fields=fields_synced
                )
                result = ATSSyncResult.SUCCESS
                error_message = None
            except ATSClientNotConfiguredError as e:
                logger.debug(
                    "[ats_sync] Sync skipped -- ATS not configured: %s",
                    e.ats_type,
                )
                result = ATSSyncResult.NO_CLIENT
                error_message = str(e)
                ats_response = None
            except Exception as e:
                logger.error(f"❌ ATS sync failed: {e}")
                result = ATSSyncResult.ATS_ERROR
                error_message = str(e)
                ats_response = None
        else:
            result = ATSSyncResult.FIELD_NOT_MAPPED
            error_message = "Nenhum campo mapeado para sincronização"
            ats_response = None
        
        audit_entry = ATSSyncAuditLog(
            sync_id=sync_id,
            trigger=trigger,
            action=action,
            source_agent=source_agent,
            ats_type=ats_type,
            candidate_id=candidate_id,
            job_id=job_id,
            fields_synced=[f["wedotalent_field"] for f in fields_synced],
            fields_skipped=fields_skipped,
            result=result,
            ats_response=ats_response,
            error_message=error_message,
            timestamp=timestamp,
            direction="push"
        )
        self.audit_log.append(audit_entry)
        
        sync_success = result == ATSSyncResult.SUCCESS
        
        try:
            from app.shared.services.event_dispatcher import event_dispatcher
            await event_dispatcher.on_ats_sync_completed(
                company_id="",
                ats_type=ats_type,
                trigger=trigger.value,
                candidate_id=candidate_id,
                job_id=job_id,
                fields_synced=len(fields_synced),
                success=sync_success
            )
        except Exception as e:
            logger.warning(f"Event dispatch failed for ATS sync: {e}")
        
        return {
            "sync_id": sync_id,
            "success": sync_success,
            "result": result.value,
            "trigger": trigger.value,
            "source_agent": source_agent,
            "ats_type": ats_type,
            "fields_synced": [f["wedotalent_field"] for f in fields_synced],
            "fields_skipped": fields_skipped,
            "wedotalent_only": wedotalent_only,
            "message": self._get_result_message(result, fields_synced, wedotalent_only),
            "skipped": result == ATSSyncResult.NO_CLIENT,
            "timestamp": timestamp.isoformat()
        }
    
    async def pull_candidate(
        self,
        ats_type: str,
        ats_candidate_id: str,
        source_agent: str = "system"
    ) -> dict[str, Any]:
        """
        Pull a single candidate from ATS.
        
        Args:
            ats_type: Type of ATS (gupy, pandape, merge)
            ats_candidate_id: ATS candidate ID
            source_agent: Agent or system triggering pull
            
        Returns:
            Pull result with candidate data
        """
        sync_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        logger.info(f"📥 Pulling candidate {ats_candidate_id} from {ats_type}")
        
        client = self.get_client(ats_type)
        if not client:
            return self._create_result(
                sync_id=sync_id,
                trigger=ATSSyncTrigger.PULL_FROM_ATS,
                source_agent=source_agent,
                ats_type=ats_type,
                result=ATSSyncResult.NO_CLIENT,
                message=f"No {ats_type} client configured",
                timestamp=timestamp
            )
        
        try:
            candidate = await client.sync_candidate_from_ats(ats_candidate_id)
            
            if candidate:
                audit_entry = ATSSyncAuditLog(
                    sync_id=sync_id,
                    trigger=ATSSyncTrigger.PULL_FROM_ATS,
                    action=ATSSyncAction.PULL,
                    source_agent=source_agent,
                    ats_type=ats_type,
                    candidate_id=ats_candidate_id,
                    job_id=None,
                    fields_synced=["name", "email", "phone", "status", "location"],
                    fields_skipped=[],
                    result=ATSSyncResult.SUCCESS,
                    ats_response=candidate.to_dict(),
                    error_message=None,
                    timestamp=timestamp,
                    direction="pull"
                )
                self.audit_log.append(audit_entry)
                
                return {
                    "sync_id": sync_id,
                    "success": True,
                    "result": ATSSyncResult.SUCCESS.value,
                    "ats_type": ats_type,
                    "candidate": candidate.to_dict(),
                    "message": f"✅ Candidato obtido de {ats_type}",
                    "timestamp": timestamp.isoformat()
                }
            else:
                return self._create_result(
                    sync_id=sync_id,
                    trigger=ATSSyncTrigger.PULL_FROM_ATS,
                    source_agent=source_agent,
                    ats_type=ats_type,
                    result=ATSSyncResult.NOT_APPLICABLE,
                    message=f"Candidato {ats_candidate_id} não encontrado em {ats_type}",
                    timestamp=timestamp
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to pull candidate from {ats_type}: {e}")
            return self._create_result(
                sync_id=sync_id,
                trigger=ATSSyncTrigger.PULL_FROM_ATS,
                source_agent=source_agent,
                ats_type=ats_type,
                result=ATSSyncResult.ATS_ERROR,
                message=str(e),
                timestamp=timestamp
            )
    
    async def pull_candidates(
        self,
        ats_type: str,
        job_id: str | None = None,
        limit: int = 100,
        source_agent: str = "system"
    ) -> dict[str, Any]:
        """
        Pull multiple candidates from ATS.
        
        Args:
            ats_type: Type of ATS
            job_id: Optional job filter
            limit: Maximum candidates to pull
            source_agent: Agent or system triggering pull
            
        Returns:
            Pull result with list of candidates
        """
        sync_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        logger.info(f"📥 Bulk pulling candidates from {ats_type} (job={job_id}, limit={limit})")
        
        client = self.get_client(ats_type)
        if not client:
            return self._create_result(
                sync_id=sync_id,
                trigger=ATSSyncTrigger.BULK_SYNC,
                source_agent=source_agent,
                ats_type=ats_type,
                result=ATSSyncResult.NO_CLIENT,
                message=f"No {ats_type} client configured",
                timestamp=timestamp
            )
        
        try:
            candidates = await client.sync_candidates_from_ats(job_id=job_id, limit=limit)
            
            audit_entry = ATSSyncAuditLog(
                sync_id=sync_id,
                trigger=ATSSyncTrigger.BULK_SYNC,
                action=ATSSyncAction.BULK_PULL,
                source_agent=source_agent,
                ats_type=ats_type,
                candidate_id=None,
                job_id=job_id,
                fields_synced=[f"pulled_{len(candidates)}_candidates"],
                fields_skipped=[],
                result=ATSSyncResult.SUCCESS,
                ats_response={"count": len(candidates)},
                error_message=None,
                timestamp=timestamp,
                direction="pull"
            )
            self.audit_log.append(audit_entry)
            
            return {
                "sync_id": sync_id,
                "success": True,
                "result": ATSSyncResult.SUCCESS.value,
                "ats_type": ats_type,
                "candidates": [c.to_dict() for c in candidates],
                "count": len(candidates),
                "message": f"✅ Obtidos {len(candidates)} candidatos de {ats_type}",
                "timestamp": timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to bulk pull candidates from {ats_type}: {e}")
            return self._create_result(
                sync_id=sync_id,
                trigger=ATSSyncTrigger.BULK_SYNC,
                source_agent=source_agent,
                ats_type=ats_type,
                result=ATSSyncResult.ATS_ERROR,
                message=str(e),
                timestamp=timestamp
            )
    
    async def pull_jobs(
        self,
        ats_type: str,
        status: str | None = None,
        limit: int = 100,
        source_agent: str = "system"
    ) -> dict[str, Any]:
        """
        Pull jobs from ATS.
        
        Args:
            ats_type: Type of ATS
            status: Optional status filter
            limit: Maximum jobs to pull
            source_agent: Agent or system triggering pull
            
        Returns:
            Pull result with list of jobs
        """
        sync_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        logger.info(f"📥 Pulling jobs from {ats_type} (status={status}, limit={limit})")
        
        client = self.get_client(ats_type)
        if not client:
            return self._create_result(
                sync_id=sync_id,
                trigger=ATSSyncTrigger.BULK_SYNC,
                source_agent=source_agent,
                ats_type=ats_type,
                result=ATSSyncResult.NO_CLIENT,
                message=f"No {ats_type} client configured",
                timestamp=timestamp
            )
        
        try:
            jobs = await client.sync_jobs_from_ats(status=status, limit=limit)
            
            return {
                "sync_id": sync_id,
                "success": True,
                "result": ATSSyncResult.SUCCESS.value,
                "ats_type": ats_type,
                "jobs": [j.to_dict() for j in jobs],
                "count": len(jobs),
                "message": f"✅ Obtidas {len(jobs)} vagas de {ats_type}",
                "timestamp": timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to pull jobs from {ats_type}: {e}")
            return self._create_result(
                sync_id=sync_id,
                trigger=ATSSyncTrigger.BULK_SYNC,
                source_agent=source_agent,
                ats_type=ats_type,
                result=ATSSyncResult.ATS_ERROR,
                message=str(e),
                timestamp=timestamp
            )
    
    async def trigger_status_change(
        self,
        source_agent: str,
        ats_type: str,
        candidate_id: str,
        job_id: str,
        old_status: str,
        new_status: str,
        reason: str | None = None
    ) -> dict[str, Any]:
        """
        Specialized trigger for status changes (most common sync).
        
        Status changes are always synced immediately as they are critical.
        """
        data: dict[str, Any] = {"status": new_status}
        if reason:
            data["rejection_reason"] = reason
        
        return await self.trigger_sync(
            trigger=ATSSyncTrigger.STATUS_CHANGE,
            source_agent=source_agent,
            ats_type=ats_type,
            candidate_id=candidate_id,
            job_id=job_id,
            data=data,
            force_sync=True
        )
    
    async def trigger_parecer_sync(
        self,
        source_agent: str,
        ats_type: str,
        candidate_id: str,
        job_id: str,
        parecer_text: str,
        wsi_score: float | None = None
    ) -> dict[str, Any]:
        """
        Specialized trigger for parecer/score sync.
        
        Pareceres are synced as notes/observations in ATSs that support it.
        """
        data: dict[str, Any] = {"parecer": parecer_text}
        if wsi_score is not None:
            data["wsi_score"] = wsi_score
        
        return await self.trigger_sync(
            trigger=ATSSyncTrigger.PARECER_GENERATED,
            source_agent=source_agent,
            ats_type=ats_type,
            candidate_id=candidate_id,
            job_id=job_id,
            data=data
        )
    
    def _determine_action(self, trigger: ATSSyncTrigger) -> ATSSyncAction:
        """Determine sync action based on trigger type."""
        create_triggers = [
            ATSSyncTrigger.CANDIDATE_CREATED,
        ]
        pull_triggers = [
            ATSSyncTrigger.PULL_FROM_ATS,
            ATSSyncTrigger.BULK_SYNC,
        ]
        
        if trigger in create_triggers:
            return ATSSyncAction.CREATE
        elif trigger in pull_triggers:
            return ATSSyncAction.PULL
        else:
            return ATSSyncAction.UPDATE
    
    async def _execute_sync(
        self,
        ats_type: str,
        action: ATSSyncAction,
        candidate_id: str | None,
        job_id: str | None,
        fields: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Execute the actual sync with the ATS using real clients.
        
        Falls back to mock if no client is configured.
        """
        client = self.get_client(ats_type)
        
        if client is None:
            logger.warning(
                "[ats_sync] No client configured for ats_type=%s -- raising ATSClientNotConfiguredError",
                ats_type,
            )
            raise ATSClientNotConfiguredError(ats_type)
        
        data = {f["wedotalent_field"]: f["value"] for f in fields}
        
        logger.info(f"📤 Executing real {action.value} sync to {ats_type}")
        logger.info(f"   Fields: {list(data.keys())}")
        
        try:
            if action == ATSSyncAction.UPDATE:
                if not candidate_id:
                    raise ValueError("candidate_id required for UPDATE action")
                result = await client.update_candidate(candidate_id, data)
                return {
                    "status": "success",
                    "action": "updated",
                    "ats_id": result.ats_id,
                    "fields_updated": list(data.keys())
                }
            
            elif action == ATSSyncAction.CREATE:
                if job_id:
                    data["job_id"] = job_id
                result = await client.create_candidate(data)
                return {
                    "status": "success",
                    "action": "created",
                    "ats_id": result.ats_id,
                    "fields_created": list(data.keys())
                }
            
            elif action == ATSSyncAction.PULL:
                if not candidate_id:
                    raise ValueError("candidate_id required for PULL action")
                result = await client.get_candidate(candidate_id)
                if result:
                    return {
                        "status": "success",
                        "action": "pulled",
                        "ats_id": result.ats_id,
                        "candidate": result.to_dict()
                    }
                else:
                    return {
                        "status": "not_found",
                        "action": "pulled",
                        "ats_id": candidate_id
                    }
            
            else:
                return self._mock_sync(ats_type, action, candidate_id, fields)
                
        except Exception as e:
            logger.error(f"❌ Real sync failed: {e}")
            raise
    
    def _mock_sync(
        self,
        ats_type: str,
        action: ATSSyncAction,
        candidate_id: str | None,
        fields: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Mock sync for development/testing when no real client is configured.
        """
        logger.info(f"🔧 Mock {action.value} sync to {ats_type}")
        logger.info(f"   Fields: {[f['wedotalent_field'] for f in fields]}")
        
        return {
            "status": "success",
            "ats_type": ats_type,
            "action": action.value,
            "fields_updated": len(fields),
            "ats_reference_id": f"mock_{ats_type}_{candidate_id}_{datetime.utcnow().timestamp()}",
            "mock": True
        }
    
    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize value for logging (hide sensitive data)."""
        if isinstance(value, str) and len(value) > 100:
            return f"{value[:50]}... ({len(value)} chars)"
        return value
    
    def _get_result_message(
        self,
        result: ATSSyncResult,
        fields_synced: list[dict],
        wedotalent_only: list[str]
    ) -> str:
        """Generate human-readable result message."""
        if result == ATSSyncResult.SUCCESS:
            synced_names = [f["wedotalent_field"] for f in fields_synced]
            msg = f"✅ Sincronizado com ATS: {', '.join(synced_names)}"
            if wedotalent_only:
                msg += f"\n📦 Salvo apenas no WedoTalent: {', '.join(wedotalent_only)}"
            return msg
        elif result == ATSSyncResult.FIELD_NOT_MAPPED:
            return "📦 Dados salvos apenas no WedoTalent (campos não existem no ATS do cliente)"
        elif result == ATSSyncResult.ATS_ERROR:
            return "❌ Erro na sincronização com ATS - dados salvos no WedoTalent"
        elif result == ATSSyncResult.NO_CLIENT:
            return "⚠️ Cliente ATS não configurado - usando modo mock"
        else:
            return "ℹ️ Sincronização não aplicável"
    
    def _create_result(
        self,
        sync_id: str,
        trigger: ATSSyncTrigger,
        source_agent: str,
        ats_type: str,
        result: ATSSyncResult,
        message: str,
        timestamp: datetime
    ) -> dict[str, Any]:
        """Create a result dict for non-sync scenarios."""
        return {
            "sync_id": sync_id,
            "success": False,
            "result": result.value,
            "trigger": trigger.value,
            "source_agent": source_agent,
            "ats_type": ats_type,
            "fields_synced": [],
            "fields_skipped": [],
            "wedotalent_only": [],
            "message": message,
            "timestamp": timestamp.isoformat()
        }
    
    def get_audit_log(
        self,
        candidate_id: str | None = None,
        job_id: str | None = None,
        direction: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get audit log entries, optionally filtered."""
        logs = self.audit_log
        
        if candidate_id:
            logs = [l for l in logs if l.candidate_id == candidate_id]
        if job_id:
            logs = [l for l in logs if l.job_id == job_id]
        if direction:
            logs = [l for l in logs if l.direction == direction]
        
        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)
        return [l.to_dict() for l in logs[:limit]]
    
    def get_sync_stats(self) -> dict[str, Any]:
        """Get synchronization statistics."""
        total = len(self.audit_log)
        success = len([l for l in self.audit_log if l.result == ATSSyncResult.SUCCESS])
        errors = len([l for l in self.audit_log if l.result == ATSSyncResult.ATS_ERROR])
        push_count = len([l for l in self.audit_log if l.direction == "push"])
        pull_count = len([l for l in self.audit_log if l.direction == "pull"])
        
        by_ats = {}
        for log in self.audit_log:
            if log.ats_type not in by_ats:
                by_ats[log.ats_type] = {"total": 0, "success": 0, "errors": 0}
            by_ats[log.ats_type]["total"] += 1
            if log.result == ATSSyncResult.SUCCESS:
                by_ats[log.ats_type]["success"] += 1
            elif log.result == ATSSyncResult.ATS_ERROR:
                by_ats[log.ats_type]["errors"] += 1
        
        return {
            "total_syncs": total,
            "successful": success,
            "errors": errors,
            "push_operations": push_count,
            "pull_operations": pull_count,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "by_ats": by_ats,
            "configured_clients": list(self._clients.keys())
        }


ats_sync_service = ATSSyncService()


def get_ats_sync_service() -> "ATSSyncService":
    return ats_sync_service
