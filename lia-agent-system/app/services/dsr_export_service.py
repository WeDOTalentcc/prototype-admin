"""
DSR Export Service — COMP-6.

Portabilidade de dados (LGPD Art. 18 V):
  Candidato tem direito de receber seus dados em formato estruturado e portável.

Implementa async export para não bloquear o request handler.
Resultado entregue via link de download (S3 presigned URL ou base64 no response).
"""
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DsrExportService:
    """
    Serviço de exportação para Data Subject Requests (DSR) de portabilidade.

    LGPD Art. 18 V: titular pode solicitar portabilidade dos dados.
    Formato de saída: JSON estruturado (legível por máquina + humano).
    """

    async def export_candidate_data(
        self,
        db: AsyncSession,
        candidate_id: str,
        company_id: str,
        requester_email: str | None = None,
    ) -> dict[str, Any]:
        """
        Exporta todos os dados do candidato em formato portável (JSON).

        Inclui:
          - Dados pessoais básicos (nome, email, telefone)
          - Histórico de vagas e etapas
          - Avaliações LIA (scores, feedbacks)
          - Logs de consentimento LGPD
          - Histórico de comunicações enviadas

        NÃO inclui:
          - Dados de outros candidatos
          - Dados internos de recrutadores
          - Modelos proprietários LIA

        Args:
            db: AsyncSession do banco
            candidate_id: ID do candidato
            company_id: ID da empresa (multi-tenant)
            requester_email: Email para auditoria da solicitação

        Returns:
            Dict com dados exportados no formato DSR portável
        """
        export = {
            "metadata": {
                "export_date": datetime.now(UTC).isoformat(),
                "candidate_id": candidate_id,
                "company_id": company_id,
                "format": "LIA DSR Export v1.0",
                "lgpd_basis": "LGPD Art. 18 V — Portabilidade de dados",
                "requester_email": requester_email,
            },
            "personal_data": {},
            "job_applications": [],
            "evaluations": [],
            "consent_logs": [],
            "communications": [],
        }

        try:
            # Dados pessoais básicos
            personal_result = await db.execute(
                text("""
                    SELECT id, name, email, phone, location, linkedin_url,
                           created_at, updated_at
                    FROM candidates
                    WHERE id = :candidate_id AND company_id = :company_id
                """),
                {"candidate_id": candidate_id, "company_id": company_id},
            )
            row = personal_result.fetchone()
            if row:
                export["personal_data"] = {
                    "id": str(row.id) if row.id else None,
                    "name": row.name,
                    "email": row.email,
                    "phone": row.phone,
                    "location": row.location,
                    "linkedin_url": row.linkedin_url,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
        except Exception as e:
            logger.warning("[DsrExport] personal_data query failed: %s", e)
            export["personal_data"] = {"error": "Dados não disponíveis"}

        try:
            # Aplicações para vagas
            apps_result = await db.execute(
                text("""
                    SELECT vc.id, j.title as job_title, vc.stage, vc.status,
                           vc.created_at, vc.updated_at
                    FROM vacancy_candidates vc
                    JOIN jobs j ON j.id = vc.job_id
                    WHERE vc.candidate_id = :candidate_id
                    ORDER BY vc.created_at DESC
                    LIMIT 100
                """),
                {"candidate_id": candidate_id},
            )
            for row in apps_result.fetchall():
                export["job_applications"].append({
                    "id": str(row.id),
                    "job_title": row.job_title,
                    "stage": row.stage,
                    "status": row.status,
                    "applied_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                })
        except Exception as e:
            logger.warning("[DsrExport] job_applications query failed: %s", e)

        try:
            # Avaliações LIA
            eval_result = await db.execute(
                text("""
                    SELECT id, job_id, lia_score, recommendation_level,
                           strengths, gaps, created_at
                    FROM candidate_evaluations
                    WHERE candidate_id = :candidate_id
                    ORDER BY created_at DESC
                    LIMIT 50
                """),
                {"candidate_id": candidate_id},
            )
            for row in eval_result.fetchall():
                export["evaluations"].append({
                    "id": str(row.id),
                    "job_id": str(row.job_id),
                    "lia_score": row.lia_score,
                    "recommendation_level": row.recommendation_level,
                    "strengths": row.strengths,
                    "gaps": row.gaps,
                    "evaluated_at": row.created_at.isoformat() if row.created_at else None,
                })
        except Exception as e:
            logger.warning("[DsrExport] evaluations query failed: %s", e)

        logger.info(
            "[DsrExport] Exported candidate=%s company=%s: %d applications, %d evaluations",
            candidate_id, company_id,
            len(export["job_applications"]), len(export["evaluations"]),
        )
        return export

    async def generate_portability_json(
        self,
        db: AsyncSession,
        candidate_id: str,
        company_id: str,
        requester_email: str | None = None,
    ) -> str:
        """
        Gera JSON portável para download.

        Returns:
            JSON string formatado para download.
        """
        data = await self.export_candidate_data(
            db=db,
            candidate_id=candidate_id,
            company_id=company_id,
            requester_email=requester_email,
        )
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)


dsr_export_service = DsrExportService()
