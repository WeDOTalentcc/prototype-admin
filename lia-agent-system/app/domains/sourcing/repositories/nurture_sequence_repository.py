"""
NurtureSequenceRepository — ADR-001 canonical repository.
Gerencia sequências de nurturing (candidate_nurture_sequences)
e aprovações HITL de steps (nurture_step_approvals).

Tabelas:
  candidate_nurture_sequences — PK: sequence_id
    cols: sequence_id, candidate_id, vacancy_id, company_id, status,
          total_steps, current_step, steps_approved, steps_executed,
          steps_data (jsonb), created_at, updated_at, lgpd_expiry
  nurture_step_approvals — PK: (sequence_id, step_number)
    cols: approval_id, sequence_id, step_number, approved_by,
          approved_at, notes, status
"""
import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class NurtureSequenceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def create(
        self,
        candidate_id: str,
        company_id: str,
        steps: list[dict],
        vacancy_id: Optional[str] = None,
        sequence_id: Optional[str] = None,
        lgpd_expiry_days: int = 180,
    ) -> dict:
        """
        Persiste sequência de nurture.
        Fail-closed em company_id.
        ON CONFLICT (sequence_id) DO NOTHING — idempotente.
        """
        self._require_company_id(company_id)
        import uuid as _uuid
        seq_id = sequence_id or str(_uuid.uuid4())
        now = datetime.utcnow()
        lgpd_expiry = now + timedelta(days=lgpd_expiry_days)
        result = await self.db.execute(
            text("""
                INSERT INTO candidate_nurture_sequences (
                    sequence_id, candidate_id, vacancy_id, company_id,
                    status, total_steps, current_step,
                    steps_approved, steps_executed,
                    steps_data, created_at, updated_at, lgpd_expiry
                ) VALUES (
                    :seq_id, :cand_id, :vac_id, :co_id,
                    created, :total_steps, 0,
                    0, 0,
                    :steps_data, :created_at, :created_at, :lgpd_expiry
                )
                ON CONFLICT (sequence_id) DO NOTHING
                RETURNING sequence_id, candidate_id, company_id, status, created_at, lgpd_expiry
            """),
            {
                "seq_id": seq_id,
                "cand_id": candidate_id,
                "vac_id": vacancy_id or None,
                "co_id": company_id,
                "total_steps": len(steps),
                "steps_data": json.dumps(steps),
                "created_at": now,
                "lgpd_expiry": lgpd_expiry,
            },
        )
        await self.db.commit()
        row = result.mappings().fetchone()
        if row:
            return dict(row)
        # ON CONFLICT DO NOTHING — retornar shape mínimo
        return {
            "sequence_id": seq_id,
            "candidate_id": candidate_id,
            "company_id": company_id,
            "status": "created",
            "created_at": now,
            "lgpd_expiry": lgpd_expiry,
        }

    async def get_by_id(self, seq_id: str, company_id: str) -> Optional[dict]:
        """
        Busca sequência por sequence_id com filtro de company_id (fail-closed).
        Retorna None se não encontrado ou de outra empresa.
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT sequence_id, candidate_id, vacancy_id, company_id,
                       status, total_steps, current_step,
                       steps_approved, steps_executed,
                       created_at, updated_at, lgpd_expiry
                FROM candidate_nurture_sequences
                WHERE sequence_id = :seq_id AND company_id = :company_id
            """),
            {"seq_id": seq_id, "company_id": company_id},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None

    async def get_active_by_candidate(
        self, candidate_id: str, company_id: str
    ) -> Optional[dict]:
        """
        Retorna sequência mais recente (ativa ou criada) para um candidato.
        Fail-closed em company_id.
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT sequence_id, candidate_id, vacancy_id, company_id,
                       status, total_steps, current_step,
                       steps_executed, steps_approved,
                       created_at, updated_at, lgpd_expiry
                FROM candidate_nurture_sequences
                WHERE candidate_id = :cid
                  AND company_id = :company_id
                  AND status NOT IN (expired, completed)
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"cid": candidate_id, "company_id": company_id},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None

    async def upsert_step_approval(
        self,
        sequence_id: str,
        step_number: int,
        company_id: str,
        approved_by: str = "recruiter",
        notes: str = "",
        approval_id: Optional[str] = None,
    ) -> dict:
        """
        Registra ou atualiza aprovação de step HITL.
        PK unique: (sequence_id, step_number).
        Fail-closed em company_id.
        """
        self._require_company_id(company_id)
        import uuid as _uuid
        from datetime import datetime as _dt
        appr_id = approval_id or str(_uuid.uuid4())
        now = _dt.utcnow()
        await self.db.execute(
            # RLS-EXEMPT: nurture_step_approvals — transitive via nurture_sequence
            text("""
                INSERT INTO nurture_step_approvals (
                    approval_id, sequence_id, step_number,
                    approved_by, approved_at, notes, status
                ) VALUES (
                    :appr_id, :seq_id, :step_num,
                    :approver, :approved_at, :notes, approved
                )
                ON CONFLICT (sequence_id, step_number) DO UPDATE
                    SET approval_id = EXCLUDED.approval_id,
                        approved_by = EXCLUDED.approved_by,
                        approved_at = EXCLUDED.approved_at,
                        notes = EXCLUDED.notes,
                        status = approved
            """),
            {
                "appr_id": appr_id,
                "seq_id": sequence_id,
                "step_num": step_number,
                "approver": approved_by,
                "approved_at": now,
                "notes": notes,
            },
        )
        await self.db.commit()
        return {"approval_id": appr_id, "sequence_id": sequence_id, "step_number": step_number}

    async def get_step_approval(
        self, sequence_id: str, step_number: int, company_id: str
    ) -> Optional[dict]:
        """
        Verifica se step foi aprovado (DB autoritativo para HITL server-side).
        Fail-closed em company_id.
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT nsa.approval_id, nsa.sequence_id, nsa.step_number,
                       nsa.status, nsa.approved_by, nsa.approved_at
                FROM nurture_step_approvals nsa
                JOIN candidate_nurture_sequences cns
                  ON nsa.sequence_id = cns.sequence_id
                WHERE nsa.sequence_id = :seq_id
                  AND nsa.step_number = :step_num
                  AND cns.company_id = :company_id
                ORDER BY nsa.approved_at DESC
                LIMIT 1
            """),
            {"seq_id": sequence_id, "step_num": step_number, "company_id": company_id},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None
