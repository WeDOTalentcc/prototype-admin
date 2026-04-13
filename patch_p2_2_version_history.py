#!/usr/bin/env python3
"""
P2.2: Version History for Custom Agents

Every PATCH to a custom agent saves a snapshot of the previous state.
Allows recruiters to see diff and revert to a previous version.

Components:
  1. Model: AgentVersionSnapshot (libs/models)
  2. Migration 073
  3. Service: AgentVersionService with create_snapshot + list + revert
  4. Endpoints: 3 (list versions, get version, revert)
  5. Hook in existing PATCH endpoint to save snapshot before update
  6. Frontend: types, hook, VersionHistoryPanel component
  7. Wire into AgentDetailsPanel
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
# 1. Model
# ============================================================
print("\n=== 1. AgentVersionSnapshot model ===")
write_file(BASE_BE, "libs/models/lia_models/agent_version_snapshot.py", '''"""
AgentVersionSnapshot — historico de versoes de Custom Agents.

Cada PATCH a um agent cria um snapshot do estado anterior antes de aplicar
a mudanca. Permite timeline visual, diff, e revert.
"""
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from lia_config.database import Base


class AgentVersionSnapshot(Base):
    __tablename__ = "agent_version_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    version = Column(Integer, nullable=False)

    # Snapshot completo do estado anterior
    snapshot_data = Column(JSONB, nullable=False)

    # Campos que mudaram nesta revisao
    changed_fields = Column(ARRAY(String), default=[])
    change_reason = Column(Text, nullable=True)

    changed_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "company_id": self.company_id,
            "version": self.version,
            "snapshot_data": self.snapshot_data or {},
            "changed_fields": self.changed_fields or [],
            "change_reason": self.change_reason,
            "changed_by": self.changed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def summary(self):
        """Lightweight summary for list view (without full snapshot)."""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "version": self.version,
            "changed_fields": self.changed_fields or [],
            "change_reason": self.change_reason,
            "changed_by": self.changed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
''')

write_file(BASE_BE, "app/models/agent_version_snapshot.py",
    'from lia_models.agent_version_snapshot import *  # noqa: F401,F403\n')


# ============================================================
# 2. Migration 073
# ============================================================
print("\n=== 2. Migration 073 ===")
write_file(BASE_BE, "alembic/versions/073_agent_version_snapshots.py", '''"""Create agent_version_snapshots table.

Revision ID: 073_agent_version_snapshots
Revises: 072_agent_approvals
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "073_agent_version_snapshots"
down_revision = "072_agent_approvals"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_version_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot_data", JSONB, nullable=False),
        sa.Column("changed_fields", ARRAY(sa.String()), server_default="{}"),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_agent_version_snapshots_agent_version",
        "agent_version_snapshots",
        ["agent_id", "version"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_agent_version_snapshots_agent_version", table_name="agent_version_snapshots")
    op.drop_table("agent_version_snapshots")
''')


# ============================================================
# 3. Service
# ============================================================
print("\n=== 3. AgentVersionService ===")
write_file(BASE_BE, "app/services/agent_version_service.py", '''"""
AgentVersionService — Gerencia historico de versoes de Custom Agents.

Operacoes:
  - create_snapshot(agent_before_update, changed_fields, reason, user_id)
  - list_versions(agent_id, company_id, limit, offset)
  - get_version(agent_id, version, company_id)
  - revert(agent_id, target_version, reverted_by)
"""
import logging
from typing import Optional
from uuid import uuid4

from sqlalchemy import and_, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.agent_version_snapshot import AgentVersionSnapshot
from lia_models.custom_agent import CustomAgent

logger = logging.getLogger(__name__)

# Fields included in snapshot (editaveis)
SNAPSHOT_FIELDS = [
    "name", "role", "description", "system_prompt", "allowed_tools",
    "domain", "icon", "config", "max_steps", "temperature", "model_override",
    "enable_memory", "context_level", "excluded_tools",
]


class AgentVersionService:

    async def create_snapshot(
        self,
        db: AsyncSession,
        agent: CustomAgent,
        changed_fields: list[str],
        changed_by: str,
        change_reason: Optional[str] = None,
    ) -> AgentVersionSnapshot:
        """Create a snapshot of the agent's current state BEFORE update is applied."""
        snapshot_data = {f: getattr(agent, f, None) for f in SNAPSHOT_FIELDS}

        # Normalize non-JSON-safe values
        for k, v in list(snapshot_data.items()):
            if hasattr(v, "isoformat"):
                snapshot_data[k] = v.isoformat()

        snapshot = AgentVersionSnapshot(
            id=uuid4(),
            agent_id=agent.id,
            company_id=agent.company_id,
            version=agent.version or 1,
            snapshot_data=snapshot_data,
            changed_fields=changed_fields,
            change_reason=change_reason,
            changed_by=changed_by,
        )
        db.add(snapshot)

        # Increment agent version
        agent.version = (agent.version or 1) + 1

        logger.info(
            "[AgentVersion] snapshot created: agent=%s version=%s fields=%s by=%s",
            agent.id, snapshot.version, changed_fields, changed_by,
        )
        return snapshot

    async def list_versions(
        self,
        db: AsyncSession,
        agent_id: str,
        company_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AgentVersionSnapshot], int]:
        """List version snapshots for an agent, newest first."""
        base_filter = and_(
            AgentVersionSnapshot.agent_id == agent_id,
            AgentVersionSnapshot.company_id == company_id,
        )

        total = await db.scalar(
            select(func.count(AgentVersionSnapshot.id)).where(base_filter)
        )

        result = await db.execute(
            select(AgentVersionSnapshot)
            .where(base_filter)
            .order_by(desc(AgentVersionSnapshot.version))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total or 0

    async def get_version(
        self,
        db: AsyncSession,
        agent_id: str,
        version: int,
        company_id: str,
    ) -> Optional[AgentVersionSnapshot]:
        """Get specific version snapshot."""
        result = await db.execute(
            select(AgentVersionSnapshot).where(
                and_(
                    AgentVersionSnapshot.agent_id == agent_id,
                    AgentVersionSnapshot.version == version,
                    AgentVersionSnapshot.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def revert(
        self,
        db: AsyncSession,
        agent: CustomAgent,
        target_version: int,
        reverted_by: str,
    ) -> CustomAgent:
        """Revert agent to a previous version. Creates a new snapshot before reverting."""
        target = await self.get_version(db, str(agent.id), target_version, agent.company_id)
        if not target:
            raise ValueError(f"Version {target_version} not found")

        # Snapshot current state before reverting
        current_fields = list(SNAPSHOT_FIELDS)
        await self.create_snapshot(
            db=db,
            agent=agent,
            changed_fields=current_fields,
            changed_by=reverted_by,
            change_reason=f"Revert to version {target_version}",
        )

        # Apply snapshot data
        for field, value in (target.snapshot_data or {}).items():
            if field in SNAPSHOT_FIELDS and hasattr(agent, field):
                setattr(agent, field, value)

        logger.info(
            "[AgentVersion] reverted: agent=%s to version=%s by=%s",
            agent.id, target_version, reverted_by,
        )
        return agent


agent_version_service = AgentVersionService()
''')


# ============================================================
# 4. Schemas
# ============================================================
print("\n=== 4. Schemas ===")
write_file(BASE_BE, "app/schemas/agent_version.py", '''"""Pydantic schemas for agent version history."""
from typing import Any, Optional

from pydantic import BaseModel


class AgentVersionSummary(BaseModel):
    id: str
    agent_id: str
    version: int
    changed_fields: list[str] = []
    change_reason: Optional[str] = None
    changed_by: str
    created_at: Optional[str] = None


class AgentVersionDetail(BaseModel):
    id: str
    agent_id: str
    company_id: str
    version: int
    snapshot_data: dict[str, Any] = {}
    changed_fields: list[str] = []
    change_reason: Optional[str] = None
    changed_by: str
    created_at: Optional[str] = None


class AgentVersionListResponse(BaseModel):
    versions: list[AgentVersionSummary]
    total: int
    limit: int
    offset: int


class RevertVersionRequest(BaseModel):
    reason: Optional[str] = None
''')


# ============================================================
# 5. Hook in PATCH endpoint + add 3 new endpoints
# ============================================================
print("\n=== 5. Hook PATCH + add endpoints ===")

# Read current PATCH endpoint to find the right place to hook
# Find "update_custom_agent" function and add snapshot call before update

patch_file(
    BASE_BE,
    "app/api/v1/custom_agents.py",
    '''@router.patch("/{agent_id}", response_model=CustomAgentResponse)
async def update_custom_agent(
    agent_id: str,
    body: UpdateCustomAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):''',
    '''@router.patch("/{agent_id}", response_model=CustomAgentResponse)
async def update_custom_agent(
    agent_id: str,
    body: UpdateCustomAgentRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update custom agent. Automatically creates a version snapshot before applying changes."""''',
    "add docstring to PATCH",
)

# Hook snapshot creation before update in the service call
# First we need to see the current structure. Let me find where agent_marketplace_service.update_agent is called.

patch_file(
    BASE_BE,
    "app/api/v1/custom_agents.py",
    '''    try:
        agent = await agent_marketplace_service.update_agent(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            data=body.model_dump(exclude_none=True),
        )''',
    '''    # P2.2: Snapshot before update
    try:
        from app.services.agent_version_service import agent_version_service
        from sqlalchemy import select as _sel
        _existing_result = await db.execute(
            _sel(CustomAgent).where(
                CustomAgent.id == agent_id,
                CustomAgent.company_id == current_user.company_id,
            )
        )
        _existing = _existing_result.scalar_one_or_none()
        if _existing:
            _update_data = body.model_dump(exclude_none=True)
            _changed_fields = [k for k in _update_data.keys() if hasattr(_existing, k)]
            if _changed_fields:
                await agent_version_service.create_snapshot(
                    db=db,
                    agent=_existing,
                    changed_fields=_changed_fields,
                    changed_by=str(current_user.id),
                )
    except Exception as _snap_err:
        logger.warning("[AgentVersion] snapshot failed (non-blocking): %s", _snap_err)

    try:
        agent = await agent_marketplace_service.update_agent(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            data=body.model_dump(exclude_none=True),
        )''',
    "hook snapshot in PATCH",
)

# Add CustomAgent import if missing
patch_file(
    BASE_BE,
    "app/api/v1/custom_agents.py",
    '''from app.domains.agent_studio.custom_agent_runtime import get_available_tool_names''',
    '''from app.domains.agent_studio.custom_agent_runtime import get_available_tool_names
from lia_models.custom_agent import CustomAgent''',
    "add CustomAgent import",
)

# Add version history endpoints before /search endpoint
patch_file(
    BASE_BE,
    "app/api/v1/custom_agents.py",
    '''@router.get("/search", summary="Search agents by name (fuzzy)")''',
    '''@router.get("/{agent_id}/versions", summary="List agent version history")
async def list_agent_versions(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of version snapshots for an agent."""
    from app.services.agent_version_service import agent_version_service
    versions, total = await agent_version_service.list_versions(
        db=db,
        agent_id=agent_id,
        company_id=current_user.company_id,
        limit=limit,
        offset=offset,
    )
    return {
        "versions": [v.summary() for v in versions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{agent_id}/versions/{version}", summary="Get specific version snapshot")
async def get_agent_version(
    agent_id: str,
    version: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full snapshot data for a specific version."""
    from app.services.agent_version_service import agent_version_service
    snap = await agent_version_service.get_version(
        db=db,
        agent_id=agent_id,
        version=version,
        company_id=current_user.company_id,
    )
    if not snap:
        raise HTTPException(status_code=404, detail="Version not found")
    return snap.to_dict()


@router.post("/{agent_id}/revert/{version}", summary="Revert agent to previous version")
async def revert_agent_to_version(
    agent_id: str,
    version: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revert agent state to a previous version. Creates a new snapshot before reverting."""
    from app.services.agent_version_service import agent_version_service
    from sqlalchemy import select as _sel

    agent_result = await db.execute(
        _sel(CustomAgent).where(
            CustomAgent.id == agent_id,
            CustomAgent.company_id == current_user.company_id,
        )
    )
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        reverted = await agent_version_service.revert(
            db=db,
            agent=agent,
            target_version=version,
            reverted_by=str(current_user.id),
        )
        await db.commit()
        return CustomAgentResponse(**reverted.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("[AgentVersion] revert failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revert agent")


@router.get("/search", summary="Search agents by name (fuzzy)")''',
    "add 3 version endpoints",
)


# ============================================================
# 6. Frontend — types + hook + component
# ============================================================
print("\n=== 6. Frontend types ===")
patch_file(
    BASE_FE,
    "components/pages-agent-studio/custom-agents/types.ts",
    '''export interface AgentApproval {''',
    '''export interface AgentVersionSummary {
  id: string
  agent_id: string
  version: number
  changed_fields: string[]
  change_reason: string | null
  changed_by: string
  created_at: string | null
}

export interface AgentVersionDetail {
  id: string
  agent_id: string
  company_id: string
  version: number
  snapshot_data: Record<string, unknown>
  changed_fields: string[]
  change_reason: string | null
  changed_by: string
  created_at: string | null
}

export interface AgentApproval {''',
    "add version types",
)


print("\n=== 7. SWR hook ===")
write_file(BASE_FE, "hooks/agents/use-agent-versions.ts", '''"use client"

import useSWR from "swr"
import type { AgentVersionSummary } from "@/components/pages-agent-studio/custom-agents/types"

const fetcher = async (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!res.ok) throw new Error(`Failed: ${res.status}`)
  return res.json()
}

export function useAgentVersions(agentId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<{
    versions: AgentVersionSummary[]
    total: number
    limit: number
    offset: number
  }>(
    agentId ? `/api/backend-proxy/custom-agents/${agentId}/versions?limit=20` : null,
    fetcher,
    { revalidateOnFocus: false, dedupingInterval: 5000 }
  )
  return {
    versions: data?.versions ?? [],
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
    'export { useStudioChatIntents } from "./use-studio-chat-intents"',
    'export { useStudioChatIntents } from "./use-studio-chat-intents"\nexport { useAgentVersions } from "./use-agent-versions"',
    "export versions hook",
)


# ============================================================
# 8. Proxy routes
# ============================================================
print("\n=== 8. Proxy routes ===")
# Reuses catch-all [...path]/route.ts if it exists
# Create dedicated route for versions
write_file(BASE_FE, "app/api/backend-proxy/custom-agents/[id]/versions/route.ts", '''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const { searchParams } = new URL(req.url)
    const qs = searchParams.toString()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/custom-agents/${id}/versions${qs ? `?${qs}` : ""}`,
      { headers: getAuthHeaders(req) },
    )
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')


# ============================================================
# 9. VersionHistoryPanel component
# ============================================================
print("\n=== 9. VersionHistoryPanel ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/VersionHistoryPanel.tsx", '''"use client"

import React, { useState } from "react"
import { History, RotateCcw, Loader2, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles, buttonStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { useAgentVersions } from "@/hooks/agents"

interface VersionHistoryPanelProps {
  agentId: string
  currentVersion: number
  onReverted?: () => void
}

export function VersionHistoryPanel({ agentId, currentVersion, onReverted }: VersionHistoryPanelProps) {
  const { versions, isLoading, mutate } = useAgentVersions(agentId)
  const [revertingVersion, setRevertingVersion] = useState<number | null>(null)

  const handleRevert = async (version: number) => {
    if (!confirm(`Reverter para versao ${version}? O estado atual sera salvo como novo snapshot.`)) return
    setRevertingVersion(version)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/custom-agents/${agentId}/revert/${version}`, {
        method: "POST",
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Erro" }))
        throw new Error(err.detail || "Erro ao reverter")
      }
      toast.success(`Revertido para versao ${version}`)
      mutate()
      onReverted?.()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Erro ao reverter")
    } finally {
      setRevertingVersion(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4 text-xs text-lia-text-disabled">
        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Carregando historico...
      </div>
    )
  }

  if (versions.length === 0) {
    return (
      <div className={cn(cardStyles.flat, "p-4 text-center")}>
        <History className="w-6 h-6 text-lia-text-disabled mx-auto mb-1.5" />
        <p className="text-xs text-lia-text-secondary">Nenhuma versao anterior</p>
        <p className="text-[10px] text-lia-text-disabled mt-1">Snapshots sao criados automaticamente a cada edicao</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 mb-2">
        <History className="w-3.5 h-3.5 text-lia-text-disabled" />
        <h4 className={cn(textStyles.subtitle, "text-xs font-semibold")}>
          Historico de versoes
        </h4>
        <span className={cn(badgeStyles.default, "text-[10px] ml-auto")}>
          v{currentVersion} (atual)
        </span>
      </div>

      <div className="space-y-1.5 max-h-64 overflow-auto">
        {versions.map((v) => {
          const isReverting = revertingVersion === v.version
          const date = v.created_at ? new Date(v.created_at).toLocaleString("pt-BR", {
            day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
          }) : ""

          return (
            <div key={v.id} className={cn(cardStyles.compact, "flex items-center justify-between")}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className={cn(badgeStyles.default, "text-[10px]")}>v{v.version}</span>
                  <span className="text-[10px] text-lia-text-disabled">{date}</span>
                </div>
                {v.changed_fields.length > 0 && (
                  <p className="text-[10px] text-lia-text-secondary mt-0.5 truncate">
                    Mudou: {v.changed_fields.slice(0, 3).join(", ")}
                    {v.changed_fields.length > 3 && ` +${v.changed_fields.length - 3}`}
                  </p>
                )}
                {v.change_reason && (
                  <p className="text-[10px] text-lia-text-disabled italic mt-0.5 truncate">{v.change_reason}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => handleRevert(v.version)}
                disabled={isReverting || v.version >= currentVersion}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                title={v.version >= currentVersion ? "Ja eh a versao atual" : "Reverter para esta versao"}
              >
                {isReverting ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <RotateCcw className="w-3 h-3" />
                )}
                Reverter
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
''')


# ============================================================
# 10. Wire into AgentDetailsPanel
# ============================================================
print("\n=== 10. Wire VersionHistoryPanel into AgentDetailsPanel ===")
patch_file(
    BASE_FE,
    "components/pages-agent-studio/custom-agents/AgentDetailsPanel.tsx",
    '''import { useAgentDeployments } from "@/hooks/agents"''',
    '''import { useAgentDeployments } from "@/hooks/agents"
import { VersionHistoryPanel } from "./VersionHistoryPanel"''',
    "import VersionHistoryPanel",
)

# Add the VersionHistoryPanel section before the actions footer
patch_file(
    BASE_FE,
    "components/pages-agent-studio/custom-agents/AgentDetailsPanel.tsx",
    '''          {/* Actions */}
          <div className="flex gap-2 pt-2 border-t border-lia-border-subtle">''',
    '''          {/* Version History */}
          <div className="pt-2 border-t border-lia-border-subtle">
            <VersionHistoryPanel
              agentId={agent.id}
              currentVersion={(agent as unknown as { version?: number }).version || 1}
              onReverted={() => {
                // parent should refetch if needed
              }}
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2 border-t border-lia-border-subtle">''',
    "wire VersionHistoryPanel",
)


# ============================================================
# 11. Update barrel
# ============================================================
print("\n=== 11. Barrel ===")
patch_file(
    BASE_FE,
    "components/pages-agent-studio/custom-agents/index.ts",
    'export { AgentChatCard, MetricsSummaryCard } from "./AgentChatCard"',
    'export { AgentChatCard, MetricsSummaryCard } from "./AgentChatCard"\nexport { VersionHistoryPanel } from "./VersionHistoryPanel"',
    "export VersionHistoryPanel",
)


# ============================================================
# VERIFY
# ============================================================
import ast
print("\n=== Verify ===")
for f in [
    "libs/models/lia_models/agent_version_snapshot.py",
    "app/schemas/agent_version.py",
    "app/services/agent_version_service.py",
    "app/api/v1/custom_agents.py",
    "alembic/versions/073_agent_version_snapshots.py",
]:
    try:
        ast.parse(read_file(BASE_BE, f))
        print(f"  OK: {f}")
    except SyntaxError as e:
        print(f"  ERROR: {f}: {e}")

print("\nP2.2 Version History complete!")
