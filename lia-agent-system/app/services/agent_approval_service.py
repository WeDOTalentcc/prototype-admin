"""
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
