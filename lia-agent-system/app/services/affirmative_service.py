"""
Affirmative Action Service for managing diversity criteria in job vacancies.
"""
from fastapi import status
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.affirmative_audit import AffirmativeAuditLog, CandidateAffirmativeDocument
from app.models.candidate import Candidate
from app.models.job_vacancy import JobVacancy

AFFIRMATIVE_CRITERIA = {
    "gender": {
        "label": "Gênero",
        "options": ["Mulheres", "Mulheres Negras", "Mulheres Trans"],
        "document_types": ["autodeclaracao"]
    },
    "race_ethnicity": {
        "label": "Raça/Etnia",
        "options": ["Pessoas Negras", "Pessoas Pardas", "Pessoas Pretas"],
        "document_types": ["autodeclaracao_racial"]
    },
    "disability": {
        "label": "Pessoa com Deficiência (PcD)",
        "options": ["PcD - Física", "PcD - Visual", "PcD - Auditiva", "PcD - Intelectual", "PcD - Múltipla"],
        "document_types": ["laudo_pcd", "certificado_reabilitacao"]
    },
    "age": {
        "label": "Idade 50+",
        "options": ["50+ anos"],
        "document_types": ["documento_identidade"]
    },
    "lgbtqia": {
        "label": "LGBTQIA+",
        "options": ["LGBTQIA+"],
        "document_types": ["autodeclaracao"]
    },
    "refugee": {
        "label": "Pessoa Refugiada",
        "options": ["Refugiados", "Solicitantes de Refúgio"],
        "document_types": ["documento_refugio", "protocolo_conare"]
    },
    "indigenous": {
        "label": "Pessoa Indígena",
        "options": ["Indígenas"],
        "document_types": ["autodeclaracao_indigena", "rani"]
    },
    "other": {
        "label": "Outro",
        "options": ["Outro grupo minorizado"],
        "document_types": ["autodeclaracao"]
    }
}

DOCUMENT_UPLOAD_DEADLINE_HOURS = 24


class AffirmativeService:
    """Service for managing affirmative action criteria and verification."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_criteria_options(self) -> dict[str, Any]:
        """Return all available affirmative action criteria."""
        return AFFIRMATIVE_CRITERIA
    
    def check_candidate_eligibility(
        self,
        candidate: Candidate,
        vacancy: JobVacancy
    ) -> dict[str, Any]:
        """Check if candidate meets affirmative action criteria for vacancy."""
        if not vacancy.is_affirmative:
            return {"eligible": True, "reason": "Vaga não é afirmativa"}
        
        criteria_primary = vacancy.affirmative_criteria_primary
        criteria_secondary = vacancy.affirmative_criteria_secondary
        
        eligibility_checks = []
        
        if criteria_primary:
            check = self._check_single_criterion(candidate, criteria_primary)
            eligibility_checks.append(check)
        
        if criteria_secondary:
            check = self._check_single_criterion(candidate, criteria_secondary)
            eligibility_checks.append(check)
        
        is_eligible = any(check["meets_criteria"] for check in eligibility_checks)
        
        return {
            "eligible": is_eligible,
            "checks": eligibility_checks,
            "requires_document": is_eligible,
            "document_types": self._get_required_document_types(criteria_primary, criteria_secondary)
        }
    
    def _check_single_criterion(self, candidate: Candidate, criterion: str) -> dict[str, Any]:
        """Check if candidate meets a single criterion."""
        check_map = {
            "gender": lambda c: c.gender and c.gender.lower() in ["feminino", "mulher", "female", "trans"],
            "race_ethnicity": lambda c: c.diversity_race_ethnicity in ["black", "brown", "preta", "parda", "negra"],
            "disability": lambda c: c.diversity_disability == True,
            "age": lambda c: c.diversity_age_50_plus == True,
            "lgbtqia": lambda c: c.diversity_lgbtqia == True,
            "refugee": lambda c: c.diversity_refugee == True,
            "indigenous": lambda c: c.diversity_indigenous == True,
            "other": lambda c: True
        }
        
        check_fn = check_map.get(criterion, lambda c: False)
        meets = check_fn(candidate)
        
        return {
            "criterion": criterion,
            "label": AFFIRMATIVE_CRITERIA.get(criterion, {}).get("label", criterion),
            "meets_criteria": meets,
            "self_declared": meets
        }
    
    def _get_required_document_types(self, primary: str, secondary: str = None) -> list[str]:
        """Get required document types for criteria."""
        doc_types = []
        if primary and primary in AFFIRMATIVE_CRITERIA:
            doc_types.extend(AFFIRMATIVE_CRITERIA[primary]["document_types"])
        if secondary and secondary in AFFIRMATIVE_CRITERIA:
            doc_types.extend(AFFIRMATIVE_CRITERIA[secondary]["document_types"])
        return list(set(doc_types))
    
    def create_document_request(
        self,
        candidate_id: UUID,
        vacancy_id: UUID,
        company_id: str,
        criteria_type: str
    ) -> CandidateAffirmativeDocument:
        """Create a document upload request with 24h deadline."""
        deadline = datetime.utcnow() + timedelta(hours=DOCUMENT_UPLOAD_DEADLINE_HOURS)
        
        document = CandidateAffirmativeDocument(
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            company_id=company_id,
            document_type="pending_upload",
            document_url="",
            criteria_type=criteria_type,
            status="pending_upload",
            upload_deadline=deadline
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        self._log_action(
            company_id=company_id,
            vacancy_id=vacancy_id,
            candidate_id=candidate_id,
            action="document_request_created",
            metadata={"deadline": deadline.isoformat(), "criteria_type": criteria_type}
        )
        
        return document
    
    def upload_document(
        self,
        document_id: UUID,
        document_url: str,
        original_filename: str,
        document_type: str
    ) -> CandidateAffirmativeDocument:
        """Process document upload."""
        document = self.db.query(CandidateAffirmativeDocument).filter(
            CandidateAffirmativeDocument.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document request not found")
        
        if document.upload_deadline and datetime.utcnow() > document.upload_deadline:
            document.is_expired = True
            document.status = "expired"
            self.db.commit()
            raise ValueError("Upload deadline has expired")
        
        document.document_url = document_url
        document.original_filename = original_filename
        document.document_type = document_type
        document.status = "pending_verification"
        document.uploaded_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        self._log_action(
            company_id=document.company_id,
            vacancy_id=document.vacancy_id,
            candidate_id=document.candidate_id,
            action="document_uploaded",
            metadata={"document_type": document_type, "filename": original_filename}
        )
        
        return document
    
    def verify_document_lia(
        self,
        document_id: UUID,
        verification_result: dict[str, Any]
    ) -> CandidateAffirmativeDocument:
        """LIA automated verification of document."""
        document = self.db.query(CandidateAffirmativeDocument).filter(
            CandidateAffirmativeDocument.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document not found")
        
        document.verified_by_lia = True
        document.lia_verification_result = verification_result
        document.lia_verified_at = datetime.utcnow()
        document.status = "lia_verified" if verification_result.get("valid") else "lia_rejected"
        
        self.db.commit()
        self.db.refresh(document)
        
        self._log_action(
            company_id=document.company_id,
            vacancy_id=document.vacancy_id,
            candidate_id=document.candidate_id,
            action="document_verified_lia",
            result=verification_result.get("valid"),
            metadata=verification_result
        )
        
        return document
    
    def verify_document_recruiter(
        self,
        document_id: UUID,
        recruiter_email: str,
        approved: bool,
        notes: str = None
    ) -> CandidateAffirmativeDocument:
        """Recruiter manual verification of document."""
        document = self.db.query(CandidateAffirmativeDocument).filter(
            CandidateAffirmativeDocument.id == document_id
        ).first()
        
        if not document:
            raise ValueError("Document not found")
        
        document.verified_by_recruiter = True
        document.recruiter_email = recruiter_email
        document.recruiter_verified_at = datetime.utcnow()
        document.recruiter_notes = notes
        document.status = "approved" if approved else "rejected"
        
        self.db.commit()
        self.db.refresh(document)
        
        self._log_action(
            company_id=document.company_id,
            vacancy_id=document.vacancy_id,
            candidate_id=document.candidate_id,
            action="document_verified_recruiter",
            result=approved,
            performed_by=recruiter_email,
            performed_by_type="recruiter",
            metadata={"notes": notes}
        )
        
        return document
    
    def get_pending_documents(
        self,
        company_id: str,
        vacancy_id: UUID = None
    ) -> list[dict[str, Any]]:
        """Get all pending document uploads for a company/vacancy."""
        query = self.db.query(CandidateAffirmativeDocument).filter(
            CandidateAffirmativeDocument.company_id == company_id,
            CandidateAffirmativeDocument.status.in_(["pending_upload", "pending_verification", "lia_verified"])
        )
        
        if vacancy_id:
            query = query.filter(CandidateAffirmativeDocument.vacancy_id == vacancy_id)
        
        documents = query.all()
        
        result = []
        for doc in documents:
            candidate = self.db.query(Candidate).filter(Candidate.id == doc.candidate_id).first()
            hours_remaining = None
            if doc.upload_deadline:
                remaining = doc.upload_deadline - datetime.utcnow()
                hours_remaining = max(0, remaining.total_seconds() / 3600)
            
            result.append({
                "id": str(doc.id),
                "candidate_id": str(doc.candidate_id),
                "candidate_name": candidate.name if candidate else "Unknown",
                "vacancy_id": str(doc.vacancy_id) if doc.vacancy_id else None,
                "status": doc.status,
                "document_type": doc.document_type,
                "criteria_type": doc.criteria_type,
                "hours_remaining": round(hours_remaining, 1) if hours_remaining else None,
                "is_expired": doc.is_expired,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "verified_by_lia": doc.verified_by_lia,
                "verified_by_recruiter": doc.verified_by_recruiter
            })
        
        return result
    
    def check_expired_documents(self, company_id: str) -> int:
        """Check and mark expired documents."""
        now = datetime.utcnow()
        
        expired = self.db.query(CandidateAffirmativeDocument).filter(
            CandidateAffirmativeDocument.company_id == company_id,
            CandidateAffirmativeDocument.status == "pending_upload",
            CandidateAffirmativeDocument.upload_deadline < now,
            CandidateAffirmativeDocument.is_expired == False
        ).all()
        
        for doc in expired:
            doc.is_expired = True
            doc.status = "expired"
            self._log_action(
                company_id=doc.company_id,
                vacancy_id=doc.vacancy_id,
                candidate_id=doc.candidate_id,
                action="document_expired",
                metadata={"deadline": doc.upload_deadline.isoformat()}
            )
        
        self.db.commit()
        return len(expired)
    
    def _log_action(
        self,
        company_id: str,
        action: str,
        vacancy_id: UUID = None,
        candidate_id: UUID = None,
        result: bool = None,
        reason: str = None,
        performed_by: str = None,
        performed_by_type: str = "system",
        metadata: dict[str, Any] = None
    ):
        """Log an affirmative action event."""
        log = AffirmativeAuditLog(
            company_id=company_id,
            vacancy_id=vacancy_id,
            candidate_id=candidate_id,
            action=action,
            result=result,
            reason=reason,
            performed_by=performed_by,
            performed_by_type=performed_by_type,
            action_metadata=metadata or {}
        )
        self.db.add(log)
