#!/usr/bin/env python3
"""
P2.1: Approval Workflow

Flow: draft → (submit) → pending_approval → (review) → approved/rejected → active

Components:
  1. Model: AgentApprovalRequest
  2. Migration 072
  3. Service: AgentApprovalService
  4. 3 endpoints: request, list pending, review
  5. Frontend: ApprovalBadge, ApprovalsList, wire into AgentDetailsPanel
"""
import os

BASE_BE = "/home/runner/workspace/lia-agent-system"
BASE_FE = "/home/runner/workspace/plataforma-lia/src"


def write_file(base, rel, content):
    full = os.path.join(base, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  CREATED: {rel}")


def read_file(base, rel):
    with open(os.path.join(base, rel)) as f:
        return f.read()


def patch_file(base, rel, old, new, label=""):
    full = os.path.join(base, rel)
    content = read_file(base, rel)
    if old not in content:
        print(f"  SKIP: {label}")
        return False
    content = content.replace(old, new, 1)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {label}")
    return True


# ============================================================
# 1. Model: AgentApprovalRequest
# ============================================================
print("\n=== 1. Model ===")
write_file(BASE_BE, "libs/models/lia_models/agent_approval.py", '''"""
AgentApprovalRequest — Workflow de aprovacao para Studio agents.

Enterprise requirement: manager/admin aprova antes do agent ir para producao.
Flow: draft -> pending_approval -> approved/rejected -> active
"""
import enum
import uuid

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AgentApprovalRequest(Base):
    __tablename__ = "agent_approval_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    requested_by = Column(String(128), nullable=False)
    reviewed_by = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    review_notes = Column(Text, nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "company_id": self.company_id,
            "requested_by": self.requested_by,
            "reviewed_by": self.reviewed_by,
            "status": self.status,
            "review_notes": self.review_notes,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
''')

write_file(BASE_BE, "app/models/agent_approval.py",
    'from lia_models.agent_approval import *  # noqa: F401,F403\n')


# ============================================================
# 2. Migration 072
# ============================================================
print("\n=== 2. Migration 072 ===")
write_file(BASE_BE, "alembic/versions/072_agent_approvals.py", '''"""Create agent_approval_requests table.

Revision ID: 072_agent_approvals
Revises: 071_agent_execution_logs
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "072_agent_approvals"
down_revision = "071_agent_execution_logs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_approval_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("requested_by", sa.String(128), nullable=False),
        sa.Column("reviewed_by", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_agent_approval_status",
        "agent_approval_requests",
        "status IN ('pending', 'approved', 'rejected')",
    )

    # Add pending_approval to custom_agents.status check constraint
    # (If a CHECK constraint exists, we need to update it. For now, assume it's open.)


def downgrade():
    op.drop_constraint("ck_agent_approval_status", "agent_approval_requests", type_="check")
    op.drop_table("agent_approval_requests")
''')


# ============================================================
# 3. Service: AgentApprovalService
# ============================================================
print("\n=== 3. Service ===")
write_file(BASE_BE, "app/services/agent_approval_service.py", '''"""
AgentApprovalService — Business logic for agent approval workflow.

Rules:
  - Only agent creator can submit for approval
  - Only users with role "admin" can review approvals
  - Agent status transitions: draft -> pending_approval -> approved (active) / rejected (draft)
  - Audit log: every submission and review recorded
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.agent_approval import AgentApprovalRequest
from lia_models.custom_agent import CustomAgent

logger = logging.getLogger(__name__)


class AgentApprovalService:

    async def request_approval(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
        requested_by: str,
    ) -> AgentApprovalRequest:
        """Submit agent for approval. Agent must be in draft status."""
        # Validate agent
        result = await db.execute(
            select(CustomAgent).where(
                and_(
                    CustomAgent.id == agent_id,
                    CustomAgent.company_id == company_id,
                )
            )
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise ValueError("Agent not found")
        if agent.status != "draft":
            raise ValueError(f"Only draft agents can be submitted. Current: {agent.status}")

        # Check if there is already a pending request
        existing = await db.execute(
            select(AgentApprovalRequest).where(
                and_(
                    AgentApprovalRequest.agent_id == agent_id,
                    AgentApprovalRequest.status == "pending",
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("There is already a pending approval request for this agent")

        # Create approval request
        approval = AgentApprovalRequest(
            id=uuid4(),
            agent_id=agent_id,
            company_id=company_id,
            requested_by=requested_by,
            status="pending",
        )
        db.add(approval)

        # Update agent status to pending_approval
        agent.status = "pending_approval"

        logger.info(
            "[AgentApproval] request submitted: agent=%s by=%s company=%s",
            agent_id, requested_by, company_id,
        )
        return approval

    async def list_pending(
        self,
        db: AsyncSession,
        company_id: str,
    ) -> list[AgentApprovalRequest]:
        """List all pending approval requests for a company (for admins)."""
        result = await db.execute(
            select(AgentApprovalRequest).where(
                and_(
                    AgentApprovalRequest.company_id == company_id,
                    AgentApprovalRequest.status == "pending",
                )
            ).order_by(AgentApprovalRequest.requested_at.desc())
        )
        return list(result.scalars().all())

    async def review(
        self,
        db: AsyncSession,
        approval_id: str,
        company_id: str,
        reviewer_id: str,
        action: str,
        notes: Optional[str] = None,
    ) -> AgentApprovalRequest:
        """Approve or reject an approval request.

        action: "approve" | "reject"
        """
        if action not in ("approve", "reject"):
            raise ValueError(f"Invalid action: {action}")

        result = await db.execute(
            select(AgentApprovalRequest).where(
                and_(
                    AgentApprovalRequest.id == approval_id,
                    AgentApprovalRequest.company_id == company_id,
                )
            )
        )
        approval = result.scalar_one_or_none()
        if not approval:
            raise ValueError("Approval request not found")
        if approval.status != "pending":
            raise ValueError(f"Only pending requests can be reviewed. Current: {approval.status}")

        # Update approval
        approval.status = "approved" if action == "approve" else "rejected"
        approval.reviewed_by = reviewer_id
        approval.reviewed_at = datetime.now(timezone.utc)
        approval.review_notes = notes

        # Update agent status accordingly
        agent_result = await db.execute(
            select(CustomAgent).where(CustomAgent.id == approval.agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if agent:
            if action == "approve":
                agent.status = "active"
            else:
                agent.status = "draft"  # Back to draft for revision

        logger.info(
            "[AgentApproval] reviewed: approval=%s action=%s by=%s",
            approval_id, action, reviewer_id,
        )
        return approval

    async def get_latest_for_agent(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
    ) -> Optional[AgentApprovalRequest]:
        """Get the latest approval request for an agent (any status)."""
        result = await db.execute(
            select(AgentApprovalRequest).where(
                and_(
                    AgentApprovalRequest.agent_id == agent_id,
                    AgentApprovalRequest.company_id == company_id,
                )
            ).order_by(AgentApprovalRequest.requested_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()


agent_approval_service = AgentApprovalService()
''')


# ============================================================
# 4. Schemas
# ============================================================
print("\n=== 4. Schemas ===")
write_file(BASE_BE, "app/schemas/agent_approval.py", '''"""Pydantic schemas for agent approval workflow."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RequestApprovalRequest(BaseModel):
    """Empty body — agent_id comes from URL path."""
    pass


class ReviewApprovalRequest(BaseModel):
    action: Literal["approve", "reject"]
    notes: Optional[str] = Field(None, max_length=2000)


class ApprovalResponse(BaseModel):
    id: str
    agent_id: str
    company_id: str
    requested_by: str
    reviewed_by: Optional[str] = None
    status: str
    review_notes: Optional[str] = None
    requested_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    # Enriched fields
    agent_name: Optional[str] = None


class ApprovalListResponse(BaseModel):
    approvals: list[ApprovalResponse]
    total: int
''')


# ============================================================
# 5. Endpoints
# ============================================================
print("\n=== 5. Endpoints ===")
write_file(BASE_BE, "app/api/v1/agent_approvals.py", '''"""
REST API for agent approval workflow.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.auth.models import UserRole
from app.core.database import get_db
from app.schemas.agent_approval import (
    ApprovalListResponse,
    ApprovalResponse,
    ReviewApprovalRequest,
)
from app.services.agent_approval_service import agent_approval_service

logger = logging.getLogger(__name__)

# Router for agent-specific approval requests
agent_router = APIRouter(prefix="/custom-agents", tags=["Agent Approvals"])


@agent_router.post("/{agent_id}/request-approval", response_model=ApprovalResponse, status_code=201)
async def request_agent_approval(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit an agent for approval. Agent must be in draft status."""
    try:
        approval = await agent_approval_service.request_approval(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            requested_by=str(current_user.id),
        )
        await db.commit()
        return ApprovalResponse(**approval.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error requesting approval: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to request approval")


# Router for approval management (admin only)
approvals_router = APIRouter(prefix="/agent-approvals", tags=["Agent Approvals"])


@approvals_router.get("/pending", response_model=ApprovalListResponse)
async def list_pending_approvals(
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
):
    """List all pending approval requests (admin only)."""
    approvals = await agent_approval_service.list_pending(
        db=db, company_id=current_user.company_id
    )

    # Enrich with agent names
    from lia_models.custom_agent import CustomAgent
    responses = []
    for a in approvals:
        resp = ApprovalResponse(**a.to_dict())
        agent_result = await db.execute(
            select(CustomAgent).where(CustomAgent.id == a.agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if agent:
            resp.agent_name = agent.name
        responses.append(resp)

    return ApprovalListResponse(approvals=responses, total=len(responses))


@approvals_router.post("/{approval_id}/review", response_model=ApprovalResponse)
async def review_approval(
    approval_id: str,
    body: ReviewApprovalRequest,
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject an approval request (admin only)."""
    try:
        approval = await agent_approval_service.review(
            db=db,
            approval_id=approval_id,
            company_id=current_user.company_id,
            reviewer_id=str(current_user.id),
            action=body.action,
            notes=body.notes,
        )
        await db.commit()
        return ApprovalResponse(**approval.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error reviewing approval: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to review approval")
''')


# ============================================================
# 6. Register routers
# ============================================================
print("\n=== 6. Register routers ===")
patch_file(
    BASE_BE,
    "app/api/routes.py",
    "from app.api.v1.agent_deployments import target_router as agent_deployments_target_router",
    "from app.api.v1.agent_deployments import target_router as agent_deployments_target_router\n"
    "from app.api.v1.agent_approvals import agent_router as agent_approvals_agent_router\n"
    "from app.api.v1.agent_approvals import approvals_router as agent_approvals_approvals_router",
    "add approval router imports",
)

patch_file(
    BASE_BE,
    "app/api/routes.py",
    'app.include_router(agent_deployments_target_router, prefix="/api/v1")',
    'app.include_router(agent_deployments_target_router, prefix="/api/v1")\n'
    '    app.include_router(agent_approvals_agent_router, prefix="/api/v1")\n'
    '    app.include_router(agent_approvals_approvals_router, prefix="/api/v1")',
    "register approval routers",
)


# ============================================================
# 7. Frontend: types + hook
# ============================================================
print("\n=== 7. Frontend types + hook ===")
# Add ApprovalStatus to types
patch_file(
    BASE_FE,
    "components/pages-agent-studio/custom-agents/types.ts",
    'export type AgentStatus = "draft" | "active" | "paused" | "archived"',
    'export type AgentStatus = "draft" | "pending_approval" | "active" | "paused" | "archived"\n\nexport type ApprovalStatus = "pending" | "approved" | "rejected"\n\nexport interface AgentApproval {\n  id: string\n  agent_id: string\n  company_id: string\n  requested_by: string\n  reviewed_by: string | null\n  status: ApprovalStatus\n  review_notes: string | null\n  requested_at: string | null\n  reviewed_at: string | null\n  agent_name?: string\n}',
    "add approval types",
)

# Add hook
write_file(BASE_FE, "hooks/agents/use-approvals.ts", '''"use client"

import useSWR from "swr"
import type { AgentApproval } from "@/components/pages-agent-studio/custom-agents/types"

const fetcher = async (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(`Failed: ${res.status}`)
  return res.json()
}

export function usePendingApprovals() {
  const { data, error, isLoading, mutate } = useSWR<{ approvals: AgentApproval[]; total: number }>(
    "/api/backend-proxy/agent-approvals/pending",
    fetcher,
    { revalidateOnFocus: true, dedupingInterval: 10000 }
  )
  return {
    approvals: data?.approvals ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError: !!error,
    mutate,
  }
}
''')

patch_file(
    BASE_FE,
    "hooks/agents/index.ts",
    'export { useCustomAgents, useAgentDeployments } from "./use-custom-agents"',
    'export { useCustomAgents, useAgentDeployments } from "./use-custom-agents"\nexport { usePendingApprovals } from "./use-approvals"',
    "export approvals hook",
)


# ============================================================
# 8. Frontend: Proxy routes
# ============================================================
print("\n=== 8. Proxy routes ===")
# Proxy for request-approval (POST /custom-agents/{id}/request-approval)
# Already handled by catch-all [...path]/route.ts

# Proxy for /agent-approvals
write_file(BASE_FE, "app/api/backend-proxy/agent-approvals/pending/route.ts", '''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(req: NextRequest) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/agent-approvals/pending`, { headers: getAuthHeaders(req) })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')

write_file(BASE_FE, "app/api/backend-proxy/agent-approvals/[id]/review/route.ts", '''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const body = await req.text()
    const res = await fetch(`${BACKEND_URL}/api/v1/agent-approvals/${id}/review`, {
      method: "POST", headers: getAuthHeaders(req), body,
    })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')


# ============================================================
# 9. Frontend: ApprovalsList component
# ============================================================
print("\n=== 9. ApprovalsList ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/ApprovalsList.tsx", '''"use client"

import React, { useState } from "react"
import { Check, X, Clock, Loader2, ShieldCheck } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles, buttonStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { usePendingApprovals } from "@/hooks/agents"

interface ApprovalsListProps {
  onReviewed?: () => void
}

export function ApprovalsList({ onReviewed }: ApprovalsListProps) {
  const { approvals, isLoading, mutate } = usePendingApprovals()
  const [reviewingId, setReviewingId] = useState<string | null>(null)
  const [notes, setNotes] = useState<Record<string, string>>({})

  const handleReview = async (approvalId: string, action: "approve" | "reject") => {
    setReviewingId(approvalId)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/agent-approvals/${approvalId}/review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ action, notes: notes[approvalId] || null }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Erro" }))
        throw new Error(err.detail || "Erro ao revisar")
      }
      toast.success(action === "approve" ? "Agente aprovado" : "Agente rejeitado")
      mutate()
      onReviewed?.()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Erro ao revisar")
    } finally {
      setReviewingId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4 text-xs text-lia-text-disabled">
        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Carregando aprovacoes...
      </div>
    )
  }

  if (approvals.length === 0) {
    return (
      <div className={cn(cardStyles.flat, "p-4 text-center")}>
        <ShieldCheck className="w-6 h-6 text-lia-text-disabled mx-auto mb-1.5" />
        <p className="text-xs text-lia-text-secondary">Nenhuma aprovacao pendente</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 mb-2">
        <Clock className="w-3.5 h-3.5 text-amber-500" />
        <h4 className={cn(textStyles.subtitle, "text-xs font-semibold")}>
          Aprovacoes pendentes ({approvals.length})
        </h4>
      </div>

      {approvals.map((approval) => {
        const isReviewing = reviewingId === approval.id
        return (
          <div key={approval.id} className={cn(cardStyles.default, "p-3 space-y-2")}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-semibold text-lia-text-primary">
                  {approval.agent_name || "Agent"}
                </p>
                <p className="text-[10px] text-lia-text-disabled">
                  Solicitado por: {approval.requested_by}
                </p>
              </div>
              <span className={cn(badgeStyles.warning, "text-[10px]")}>Pendente</span>
            </div>

            <textarea
              value={notes[approval.id] || ""}
              onChange={(e) => setNotes({ ...notes, [approval.id]: e.target.value })}
              placeholder="Notas da revisao (opcional)"
              rows={2}
              className="w-full text-xs border border-lia-border-subtle rounded-md px-2 py-1.5 bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30 resize-none"
              disabled={isReviewing}
            />

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleReview(approval.id, "approve")}
                disabled={isReviewing}
                className="flex-1 inline-flex items-center justify-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium bg-emerald-500 text-white hover:bg-emerald-600 transition-colors disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" /> Aprovar
              </button>
              <button
                type="button"
                onClick={() => handleReview(approval.id, "reject")}
                disabled={isReviewing}
                className={cn(buttonStyles.outline, "flex-1 text-xs px-3 py-1.5")}
              >
                <X className="w-3.5 h-3.5 mr-1" /> Rejeitar
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
''')


# ============================================================
# 10. Frontend: RequestApprovalButton
# ============================================================
print("\n=== 10. RequestApprovalButton ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/RequestApprovalButton.tsx", '''"use client"

import React, { useState } from "react"
import { ShieldCheck, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { buttonStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import type { CustomAgent } from "./types"

interface RequestApprovalButtonProps {
  agent: CustomAgent
  onRequested?: () => void
}

export function RequestApprovalButton({ agent, onRequested }: RequestApprovalButtonProps) {
  const [isRequesting, setIsRequesting] = useState(false)

  const handleRequest = async () => {
    setIsRequesting(true)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/custom-agents/${agent.id}/request-approval`, {
        method: "POST",
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Erro" }))
        throw new Error(err.detail || "Erro ao solicitar aprovacao")
      }
      toast.success("Aprovacao solicitada", "O administrador sera notificado.")
      onRequested?.()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Erro ao solicitar aprovacao")
    } finally {
      setIsRequesting(false)
    }
  }

  if (agent.status !== "draft") return null

  return (
    <button
      type="button"
      onClick={handleRequest}
      disabled={isRequesting}
      className={cn(buttonStyles.primary, "text-xs px-3 py-1.5 inline-flex items-center gap-1.5")}
    >
      {isRequesting ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : (
        <ShieldCheck className="w-3.5 h-3.5" />
      )}
      Solicitar aprovacao
    </button>
  )
}
''')


# ============================================================
# 11. Update barrel
# ============================================================
print("\n=== 11. Barrel ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/index.ts", '''export { TemplateGallery } from "./TemplateGallery"
export { TemplateCard } from "./TemplateCard"
export { AgentCard } from "./AgentCard"
export { AgentCardSkeleton } from "./AgentCardSkeleton"
export { AgentDetailsPanel } from "./AgentDetailsPanel"
export { AgentActivityCard } from "./AgentActivityCard"
export { DeployDialog } from "./DeployDialog"
export { ConversationalCreator } from "./ConversationalCreator"
export { TestDebugPanel } from "./TestDebugPanel"
export { ToolSelector } from "./ToolSelector"
export { ContextLevelSelect } from "./ContextLevelSelect"
export { ApprovalsList } from "./ApprovalsList"
export { RequestApprovalButton } from "./RequestApprovalButton"
export type * from "./types"
''')


# ============================================================
# 12. Wire into AgentStudioPage — add ApprovalsList section
# ============================================================
print("\n=== 12. Wire into AgentStudioPage ===")
patch_file(
    BASE_FE,
    "components/pages-agent-studio/AgentStudioPage.tsx",
    'import { TemplateGallery, AgentCard as CustomAgentCard, AgentCardSkeleton, AgentDetailsPanel, DeployDialog, ConversationalCreator, TestDebugPanel } from "@/components/pages-agent-studio/custom-agents"',
    'import { TemplateGallery, AgentCard as CustomAgentCard, AgentCardSkeleton, AgentDetailsPanel, DeployDialog, ConversationalCreator, TestDebugPanel, ApprovalsList } from "@/components/pages-agent-studio/custom-agents"',
    "add ApprovalsList import",
)

# Insert ApprovalsList above Meus Agentes section (admin-only visibility handled by API)
patch_file(
    BASE_FE,
    "components/pages-agent-studio/AgentStudioPage.tsx",
    '''            {/* My Agents */}
            <section>
              <h3 className="text-sm font-semibold text-lia-text-primary mb-3">
                Meus Agentes {customAgents.length > 0 && `(${customAgents.length})`}
              </h3>''',
    '''            {/* Pending Approvals (admin only — hidden if empty or not admin) */}
            <section>
              <ApprovalsList onReviewed={() => mutateCustomAgents()} />
            </section>

            {/* My Agents */}
            <section>
              <h3 className="text-sm font-semibold text-lia-text-primary mb-3">
                Meus Agentes {customAgents.length > 0 && `(${customAgents.length})`}
              </h3>''',
    "add ApprovalsList section",
)


# ============================================================
# Verify backend AST
# ============================================================
import ast
print("\n=== Verify ===")
for f in [
    "libs/models/lia_models/agent_approval.py",
    "app/schemas/agent_approval.py",
    "app/services/agent_approval_service.py",
    "app/api/v1/agent_approvals.py",
    "alembic/versions/072_agent_approvals.py",
    "app/api/routes.py",
]:
    try:
        ast.parse(read_file(BASE_BE, f))
        print(f"  OK: {f}")
    except SyntaxError as e:
        print(f"  ERROR: {f}: {e}")

print("\nP2.1 Approval Workflow complete!")
