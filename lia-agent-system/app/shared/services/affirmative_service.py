"""
Affirmative Action Service — gestão de critérios de diversidade + workflow de
documento (autodeclaração / laudo) em vagas afirmativas.

Onda 2C.3 (audit 2026-06-06): revivido + portado para AsyncSession (antes usava
sqlalchemy.orm.Session síncrona com AsyncSession injetada → quebrava em runtime).
As tabelas affirmative_audit_logs + candidate_affirmative_documents são LOCAIS
(criadas via Base.metadata.create_all), NÃO Rails — o banner RAILS-DEPRECATED estava
errado e foi removido. Multi-tenancy via company_id em todas as queries.

Compliance (LGPD/CLT 373-A/Lei 12.711 ADP):
- A autodeclaração de raça/PCD/etc é dado SENSÍVEL → upload exige consent granular
  (purpose=affirmative_verification) fail-closed.
- Verificação humana (recrutador) é o ponto de decisão (HITL) + audit canônico.
- check_can_advance: hard-gate que bloqueia avanço no pipeline até o recrutador verificar.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.affirmative_audit import AffirmativeAuditLog, CandidateAffirmativeDocument
from lia_models.candidate import Candidate
from lia_models.job_vacancy import JobVacancy

AFFIRMATIVE_CRITERIA = {
    "gender": {
        "label": "Gênero",
        "options": ["Mulheres", "Mulheres Negras", "Mulheres Trans"],
        "document_types": ["autodeclaracao"],
    },
    "race_ethnicity": {
        "label": "Raça/Etnia",
        "options": ["Pessoas Negras", "Pessoas Pardas", "Pessoas Pretas"],
        "document_types": ["autodeclaracao_racial"],
    },
    "disability": {
        "label": "Pessoa com Deficiência (PcD)",
        "options": ["PcD - Física", "PcD - Visual", "PcD - Auditiva", "PcD - Intelectual", "PcD - Múltipla"],
        "document_types": ["laudo_pcd", "certificado_reabilitacao"],
    },
    "age": {
        "label": "Idade 50+",
        "options": ["50+ anos"],
        "document_types": ["documento_identidade"],
    },
    "lgbtqia": {
        "label": "LGBTQIA+",
        "options": ["LGBTQIA+"],
        "document_types": ["autodeclaracao"],
    },
    "refugee": {
        "label": "Pessoa Refugiada",
        "options": ["Refugiados", "Solicitantes de Refúgio"],
        "document_types": ["documento_refugio", "protocolo_conare"],
    },
    "indigenous": {
        "label": "Pessoa Indígena",
        "options": ["Indígenas"],
        "document_types": ["autodeclaracao_indigena", "rani"],
    },
    "other": {
        "label": "Outro",
        "options": ["Outro grupo minorizado"],
        "document_types": ["autodeclaracao"],
    },
}

DOCUMENT_UPLOAD_DEADLINE_HOURS = 24

# Consent purpose canônico para dados sensíveis de ação afirmativa (LGPD).
AFFIRMATIVE_CONSENT_PURPOSE = "affirmative_verification"


# ── Hard-gate (espelha OfferService.check_can_send) ──────────────────────────
class AffirmativeGateError(PermissionError):
    """Base de bloqueio de avanço no pipeline por documento afirmativo. Cada
    subclasse tem um `reason` único (1:1 com ui_action na camada de chat)."""
    reason: str = "affirmative_gate"


class AffirmativeDocumentUnverifiedError(AffirmativeGateError):
    reason = "affirmative_document_unverified"


class AffirmativeDocumentRejectedError(AffirmativeGateError):
    reason = "affirmative_document_rejected"


class AffirmativeDocumentExpiredError(AffirmativeGateError):
    reason = "affirmative_document_expired"


class AffirmativeConsentRequiredError(PermissionError):
    """Upload de documento sensível sem consent granular (LGPD fail-closed)."""
    reason = "affirmative_consent_required"


def affirmative_advancement_verdict(status: str | None, verified_by_recruiter: bool, is_expired: bool) -> str:
    """Decisão PURA do hard-gate dado o estado do documento.

    Retorna: 'permit' | 'unverified' | 'rejected' | 'expired'.
    """
    if is_expired or status == "expired":
        return "expired"
    if status == "rejected":
        return "rejected"
    if status == "approved" and verified_by_recruiter:
        return "permit"
    return "unverified"


class AffirmativeService:
    """Service for managing affirmative action criteria and verification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_criteria_options(self) -> dict[str, Any]:
        """Return all available affirmative action criteria."""
        return AFFIRMATIVE_CRITERIA

    def check_candidate_eligibility(self, candidate: Candidate, vacancy: JobVacancy) -> dict[str, Any]:
        """Check if candidate meets affirmative action criteria for vacancy (in-memory)."""
        if not vacancy.is_affirmative:
            return {"eligible": True, "reason": "Vaga não é afirmativa"}

        criteria_primary = vacancy.affirmative_criteria_primary
        criteria_secondary = vacancy.affirmative_criteria_secondary

        eligibility_checks = []
        if criteria_primary:
            eligibility_checks.append(self._check_single_criterion(candidate, criteria_primary))
        if criteria_secondary:
            eligibility_checks.append(self._check_single_criterion(candidate, criteria_secondary))

        is_eligible = any(check["meets_criteria"] for check in eligibility_checks)
        return {
            "eligible": is_eligible,
            "checks": eligibility_checks,
            "requires_document": is_eligible,
            "document_types": self._get_required_document_types(criteria_primary, criteria_secondary),
        }

    def _check_single_criterion(self, candidate: Candidate, criterion: str) -> dict[str, Any]:
        """Check if candidate meets a single criterion (self-declared signals)."""
        check_map = {
            "gender": lambda c: bool(c.gender) and c.gender.lower() in ["feminino", "mulher", "female", "trans"],
            "race_ethnicity": lambda c: c.diversity_race_ethnicity in ["black", "brown", "preta", "parda", "negra"],
            "disability": lambda c: c.diversity_disability,
            "age": lambda c: c.diversity_age_50_plus,
            "lgbtqia": lambda c: c.diversity_lgbtqia,
            "refugee": lambda c: c.diversity_refugee,
            "indigenous": lambda c: c.diversity_indigenous,
            "other": lambda c: True,
        }
        check_fn = check_map.get(criterion, lambda c: False)
        meets = bool(check_fn(candidate))
        return {
            "criterion": criterion,
            "label": AFFIRMATIVE_CRITERIA.get(criterion, {}).get("label", criterion),
            "meets_criteria": meets,
            "self_declared": meets,
        }

    def _get_required_document_types(self, primary: str, secondary: str = None) -> list[str]:
        """Get required document types for criteria."""
        doc_types = []
        if primary and primary in AFFIRMATIVE_CRITERIA:
            doc_types.extend(AFFIRMATIVE_CRITERIA[primary]["document_types"])
        if secondary and secondary in AFFIRMATIVE_CRITERIA:
            doc_types.extend(AFFIRMATIVE_CRITERIA[secondary]["document_types"])
        return sorted(set(doc_types))

    async def create_document_request(
        self, candidate_id: UUID, vacancy_id: UUID, company_id: str, criteria_type: str
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
            upload_deadline=deadline,
        )
        self.db.add(document)
        self._log_action(
            company_id=company_id,
            vacancy_id=vacancy_id,
            candidate_id=candidate_id,
            action="document_request_created",
            metadata={"deadline": deadline.isoformat(), "criteria_type": criteria_type},
        )
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def upload_document(
        self, document_id: UUID, document_url: str, original_filename: str, document_type: str
    ) -> CandidateAffirmativeDocument:
        """Process document upload (candidato submete dado sensível → exige consent LGPD)."""
        document = (await self.db.execute(  # ADR-001-EXEMPT: revival afirmativo Onda 2C.3 — repo extraction follow-up
            select(CandidateAffirmativeDocument).where(CandidateAffirmativeDocument.id == document_id)
        )).scalar_one_or_none()
        if not document:
            raise ValueError("Document request not found")

        # LGPD: autodeclaração de atributo sensível exige consent granular fail-closed.
        await self._require_affirmative_consent(document.candidate_id, document.company_id)

        if document.upload_deadline and datetime.utcnow() > document.upload_deadline:
            document.is_expired = True
            document.status = "expired"
            await self.db.commit()
            raise ValueError("Upload deadline has expired")

        document.document_url = document_url
        document.original_filename = original_filename
        document.document_type = document_type
        document.status = "pending_verification"
        document.uploaded_at = datetime.utcnow()
        self._log_action(
            company_id=document.company_id,
            vacancy_id=document.vacancy_id,
            candidate_id=document.candidate_id,
            action="document_uploaded",
            metadata={"document_type": document_type, "filename": original_filename},
        )
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def verify_document_lia(
        self, document_id: UUID, verification_result: dict[str, Any]
    ) -> CandidateAffirmativeDocument:
        """LIA automated verification of document."""
        document = (await self.db.execute(  # ADR-001-EXEMPT: revival afirmativo Onda 2C.3
            select(CandidateAffirmativeDocument).where(CandidateAffirmativeDocument.id == document_id)
        )).scalar_one_or_none()
        if not document:
            raise ValueError("Document not found")

        document.verified_by_lia = True
        document.lia_verification_result = verification_result
        document.lia_verified_at = datetime.utcnow()
        document.status = "lia_verified" if verification_result.get("valid") else "lia_rejected"
        self._log_action(
            company_id=document.company_id,
            vacancy_id=document.vacancy_id,
            candidate_id=document.candidate_id,
            action="document_verified_lia",
            result=verification_result.get("valid"),
            metadata=verification_result,
        )
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def verify_document_recruiter(
        self, document_id: UUID, recruiter_email: str, approved: bool, notes: str = None
    ) -> CandidateAffirmativeDocument:
        """Recruiter manual verification (HITL — ponto de decisão humano + audit canônico)."""
        document = (await self.db.execute(  # ADR-001-EXEMPT: revival afirmativo Onda 2C.3
            select(CandidateAffirmativeDocument).where(CandidateAffirmativeDocument.id == document_id)
        )).scalar_one_or_none()
        if not document:
            raise ValueError("Document not found")

        document.verified_by_recruiter = True
        document.recruiter_email = recruiter_email
        document.recruiter_verified_at = datetime.utcnow()
        document.recruiter_notes = notes
        document.status = "approved" if approved else "rejected"
        self._log_action(
            company_id=document.company_id,
            vacancy_id=document.vacancy_id,
            candidate_id=document.candidate_id,
            action="document_verified_recruiter",
            result=approved,
            performed_by=recruiter_email,
            performed_by_type="recruiter",
            metadata={"notes": notes},
        )
        await self.db.commit()
        await self.db.refresh(document)

        # Audit canônico (LGPD Art. 20 / EU AI Act) além do log de domínio.
        await self._log_canonical_decision(document, recruiter_email, approved)
        return document

    async def get_pending_documents(self, company_id: str, vacancy_id: UUID = None) -> list[dict[str, Any]]:
        """Get all pending document uploads for a company/vacancy."""
        stmt = select(CandidateAffirmativeDocument).where(  # ADR-001-EXEMPT: revival afirmativo Onda 2C.3
            CandidateAffirmativeDocument.company_id == company_id,
            CandidateAffirmativeDocument.status.in_(["pending_upload", "pending_verification", "lia_verified"]),
        )
        if vacancy_id:
            stmt = stmt.where(CandidateAffirmativeDocument.vacancy_id == vacancy_id)
        documents = (await self.db.execute(stmt)).scalars().all()

        # Resolve nomes em batch (evita N+1).
        cand_ids = [d.candidate_id for d in documents if d.candidate_id]
        names: dict[Any, str] = {}
        if cand_ids:
            rows = (await self.db.execute(  # ADR-001-EXEMPT: revival afirmativo Onda 2C.3
                select(Candidate.id, Candidate.name).where(Candidate.id.in_(cand_ids))
            )).all()
            names = {r[0]: r[1] for r in rows}

        result = []
        for doc in documents:
            hours_remaining = None
            if doc.upload_deadline:
                remaining = doc.upload_deadline - datetime.utcnow()
                hours_remaining = max(0, remaining.total_seconds() / 3600)
            result.append({
                "id": str(doc.id),
                "candidate_id": str(doc.candidate_id),
                "candidate_name": names.get(doc.candidate_id, "Unknown"),
                "vacancy_id": str(doc.vacancy_id) if doc.vacancy_id else None,
                "status": doc.status,
                "document_type": doc.document_type,
                "criteria_type": doc.criteria_type,
                "hours_remaining": round(hours_remaining, 1) if hours_remaining else None,
                "is_expired": doc.is_expired,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "verified_by_lia": doc.verified_by_lia,
                "verified_by_recruiter": doc.verified_by_recruiter,
            })
        return result

    async def check_expired_documents(self, company_id: str) -> int:
        """Check and mark expired documents."""
        now = datetime.utcnow()
        expired = (await self.db.execute(  # ADR-001-EXEMPT: revival afirmativo Onda 2C.3
            select(CandidateAffirmativeDocument).where(
                CandidateAffirmativeDocument.company_id == company_id,
                CandidateAffirmativeDocument.status == "pending_upload",
                CandidateAffirmativeDocument.upload_deadline < now,
                CandidateAffirmativeDocument.is_expired.is_(False),  # bug fix: era `not <column>`
            )
        )).scalars().all()

        for doc in expired:
            doc.is_expired = True
            doc.status = "expired"
            self._log_action(
                company_id=doc.company_id,
                vacancy_id=doc.vacancy_id,
                candidate_id=doc.candidate_id,
                action="document_expired",
                metadata={"deadline": doc.upload_deadline.isoformat()},
            )
        await self.db.commit()
        return len(expired)

    async def check_can_advance(self, candidate_id: UUID, vacancy_id: UUID, company_id: str) -> None:
        """Pre-flight hard-gate: bloqueia avanço no pipeline numa vaga afirmativa até o
        recrutador verificar o documento. Idempotente, sem side-effects. Raise
        AffirmativeGateError subclass no bloqueio; None se permitido (ou se não há documento)."""
        doc = (await self.db.execute(  # ADR-001-EXEMPT: revival afirmativo Onda 2C.3
            select(CandidateAffirmativeDocument)
            .where(
                CandidateAffirmativeDocument.candidate_id == candidate_id,
                CandidateAffirmativeDocument.company_id == company_id,
            )
            .order_by(CandidateAffirmativeDocument.created_at.desc())
        )).scalars().first()
        # Filtra por vaga quando informado (vacancy_id pode ser nullable na coluna).
        if doc is None:
            return  # nenhum documento afirmativo → não bloqueia
        verdict = affirmative_advancement_verdict(doc.status, doc.verified_by_recruiter, doc.is_expired)
        if verdict == "permit":
            return
        if verdict == "rejected":
            raise AffirmativeDocumentRejectedError("Documento afirmativo rejeitado pelo recrutador.")
        if verdict == "expired":
            raise AffirmativeDocumentExpiredError("Prazo de upload do documento afirmativo expirou.")
        raise AffirmativeDocumentUnverifiedError("Documento afirmativo aguardando verificação do recrutador.")

    async def _require_affirmative_consent(self, candidate_id, company_id: str) -> None:
        """Fail-closed: exige consent granular para dado sensível de ação afirmativa (LGPD)."""
        try:
            from app.domains.lgpd.services.consent_checker_service import ConsentCheckerService
        except Exception:
            return  # ambiente sem LGPD service — não bloqueia (best-effort)
        checker = ConsentCheckerService(self.db)
        res = await checker.check_candidate_consent(
            candidate_id=str(candidate_id), company_id=company_id, purpose=AFFIRMATIVE_CONSENT_PURPOSE
        )
        if not getattr(res, "allowed", True):
            raise AffirmativeConsentRequiredError(
                getattr(res, "reason", None) or "Consentimento de dados sensíveis (ação afirmativa) ausente."
            )

    async def _log_canonical_decision(self, document, recruiter_email: str, approved: bool) -> None:
        """Audit canônico (best-effort) da decisão humana de verificação."""
        try:
            from app.shared.compliance.audit_service import audit_service
            await audit_service.log_decision(
                company_id=document.company_id,
                agent_name="affirmative_verification",
                decision_type="affirmative_document_verification",
                action="document_verified_recruiter",
                decision="approved" if approved else "rejected",
                reasoning=[
                    f"Documento afirmativo {document.document_type} (criterio={document.criteria_type})",
                    "Verificacao humana (HITL) pelo recrutador",
                ],
                criteria_used=["affirmative_action", "document_verification"],
                candidate_id=str(document.candidate_id) if document.candidate_id else None,
                job_vacancy_id=str(document.vacancy_id) if document.vacancy_id else None,
                human_review_required=True,
                actor_user_id=recruiter_email,
            )
        except Exception:
            pass  # audit canônico é best-effort; o log de domínio (_log_action) já persistiu

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
        metadata: dict[str, Any] = None,
    ):
        """Log an affirmative action event (add only; o caller faz o commit)."""
        log = AffirmativeAuditLog(
            company_id=company_id,
            vacancy_id=vacancy_id,
            candidate_id=candidate_id,
            action=action,
            result=result,
            reason=reason,
            performed_by=performed_by,
            performed_by_type=performed_by_type,
            action_metadata=metadata or {},
        )
        self.db.add(log)
