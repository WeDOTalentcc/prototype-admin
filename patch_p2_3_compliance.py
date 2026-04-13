#!/usr/bin/env python3
"""
P2.3: Compliance Dashboard for Studio

Backend:
  1. New endpoint GET /admin/studio/compliance-summary
     Returns: total executions, blocks (security/injection/fairness),
     PII strips, top blocked agents, trend over time.

Frontend:
  2. Add "studio" subsection to fairness-compliance section in settings
  3. Extend FairnessComplianceHub with branching logic:
     - default (no branching) → existing fairness view
     - 'studio' → new StudioComplianceView component
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
# 1. Backend: /admin/studio/compliance-summary endpoint
# ============================================================
print("\n=== 1. Backend endpoint ===")
patch_file(
    BASE_BE,
    "app/api/v1/custom_agents.py",
    '''@router.get("/studio/metrics/summary", summary="Aggregated Studio metrics for dashboard/chat")''',
    '''@router.get("/studio/compliance-summary", summary="Aggregated compliance metrics for Studio")
async def get_studio_compliance_summary(
    period_days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated compliance metrics across all Studio agents in the period.

    Returns:
      - Total executions and breakdown by compliance_status (pass/blocked)
      - Top agents by blocked execution count (highest risk)
      - Daily trend (executions per day)
      - Active agents count
      - Block rate percentage

    Used by Settings > Fairness & Compliance > Studio dashboard.
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select, and_, func, desc, cast, Date
    from lia_models.custom_agent import CustomAgent
    from lia_models.agent_execution_log import AgentExecutionLog

    since = datetime.now(timezone.utc) - timedelta(days=period_days)
    base_filter = and_(
        AgentExecutionLog.company_id == current_user.company_id,
        AgentExecutionLog.created_at >= since,
    )

    # Totals
    totals = await db.execute(
        select(
            func.count(AgentExecutionLog.id).label("total"),
            func.coalesce(
                func.sum(
                    func.case((AgentExecutionLog.compliance_status != "pass", 1), else_=0)
                ),
                0,
            ).label("blocked"),
            func.coalesce(func.avg(AgentExecutionLog.confidence), 0.0).label("avg_confidence"),
        ).where(base_filter)
    )
    t = totals.one()
    total_exec = t.total or 0
    blocked = t.blocked or 0
    block_rate = round((blocked / total_exec * 100), 2) if total_exec > 0 else 0.0

    # Breakdown by compliance_status
    status_breakdown = await db.execute(
        select(
            AgentExecutionLog.compliance_status,
            func.count(AgentExecutionLog.id).label("count"),
        )
        .where(base_filter)
        .group_by(AgentExecutionLog.compliance_status)
    )
    by_status = {row.compliance_status or "unknown": row.count for row in status_breakdown.all()}

    # Top blocked agents (highest risk)
    top_blocked_q = await db.execute(
        select(
            AgentExecutionLog.agent_id,
            func.count(AgentExecutionLog.id).label("blocks"),
        )
        .where(
            and_(
                base_filter,
                AgentExecutionLog.compliance_status != "pass",
            )
        )
        .group_by(AgentExecutionLog.agent_id)
        .order_by(desc("blocks"))
        .limit(5)
    )
    top_blocked_rows = list(top_blocked_q.all())

    top_blocked_agents = []
    for row in top_blocked_rows:
        agent_res = await db.execute(
            select(CustomAgent).where(CustomAgent.id == row.agent_id)
        )
        agent = agent_res.scalar_one_or_none()
        top_blocked_agents.append({
            "agent_id": str(row.agent_id),
            "agent_name": agent.name if agent else "(deleted)",
            "blocked_count": row.blocks,
        })

    # Daily trend (executions per day)
    trend_q = await db.execute(
        select(
            cast(AgentExecutionLog.created_at, Date).label("day"),
            func.count(AgentExecutionLog.id).label("count"),
            func.coalesce(
                func.sum(
                    func.case((AgentExecutionLog.compliance_status != "pass", 1), else_=0)
                ),
                0,
            ).label("blocked"),
        )
        .where(base_filter)
        .group_by("day")
        .order_by("day")
    )
    trend = [
        {
            "day": row.day.isoformat() if row.day else None,
            "executions": row.count,
            "blocked": row.blocked or 0,
        }
        for row in trend_q.all()
    ]

    # Active agents
    active_count = await db.scalar(
        select(func.count(CustomAgent.id)).where(
            and_(
                CustomAgent.company_id == current_user.company_id,
                CustomAgent.status == "active",
            )
        )
    ) or 0

    return {
        "period_days": period_days,
        "total_executions": total_exec,
        "blocked_executions": blocked,
        "block_rate_pct": block_rate,
        "avg_confidence": round(float(t.avg_confidence or 0), 3),
        "active_agents": active_count,
        "by_status": by_status,
        "top_blocked_agents": top_blocked_agents,
        "trend": trend,
    }


@router.get("/studio/metrics/summary", summary="Aggregated Studio metrics for dashboard/chat")''',
    "compliance-summary endpoint",
)


# ============================================================
# 2. Frontend: add "Studio" subsection to settings
# ============================================================
print("\n=== 2. Add Studio subsection ===")
patch_file(
    BASE_FE,
    "components/pages/settings-page-enhanced.tsx",
    '''      { id: 'dashboard', title: 'Dashboard', description: 'Visão geral de fairness', fields: ['fairness_summary'] },
      { id: 'audit-log', title: 'Auditoria', description: 'Log de eventos de compliance', fields: ['audit_log'] },
      { id: 'export', title: 'Exportar', description: 'Relatórios para auditores', fields: ['export_reports'] },''',
    '''      { id: 'dashboard', title: 'Dashboard', description: 'Visão geral de fairness', fields: ['fairness_summary'] },
      { id: 'audit-log', title: 'Auditoria', description: 'Log de eventos de compliance', fields: ['audit_log'] },
      { id: 'studio', title: 'Studio', description: 'Compliance dos agentes Studio', fields: ['studio_compliance'] },
      { id: 'export', title: 'Exportar', description: 'Relatórios para auditores', fields: ['export_reports'] },''',
    "add studio subsection",
)


# ============================================================
# 3. Frontend: Proxy route
# ============================================================
print("\n=== 3. Proxy route ===")
write_file(BASE_FE, "app/api/backend-proxy/custom-agents/studio-compliance-summary/route.ts", '''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const qs = searchParams.toString()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/custom-agents/studio/compliance-summary${qs ? `?${qs}` : ""}`,
      { headers: getAuthHeaders(req) },
    )
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')


# ============================================================
# 4. Frontend: StudioComplianceView component
# ============================================================
print("\n=== 4. StudioComplianceView ===")
write_file(BASE_FE, "components/settings/StudioComplianceView.tsx", '''"use client"

import React, { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Bot, ShieldCheck, AlertTriangle, Activity, TrendingDown, Loader2 } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { textStyles, cardStyles } from "@/lib/design-tokens"

interface StudioComplianceData {
  period_days: number
  total_executions: number
  blocked_executions: number
  block_rate_pct: number
  avg_confidence: number
  active_agents: number
  by_status: Record<string, number>
  top_blocked_agents: Array<{ agent_id: string; agent_name: string; blocked_count: number }>
  trend: Array<{ day: string; executions: number; blocked: number }>
}

export function StudioComplianceView() {
  const [period, setPeriod] = useState("30")
  const [data, setData] = useState<StudioComplianceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
        const res = await fetch(
          `/api/backend-proxy/custom-agents/studio-compliance-summary?period_days=${period}`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        )
        if (!res.ok) throw new Error("Erro ao carregar dados")
        const json = await res.json()
        setData(json)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Erro ao carregar")
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [period])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 gap-2 text-sm text-lia-text-secondary">
        <Loader2 className="w-4 h-4 animate-spin" /> Carregando metricas do Studio...
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-10 h-10 text-status-error mx-auto mb-3" />
        <p className={textStyles.subtitle}>{error}</p>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-4">
      {/* Header with period selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-wedo-cyan-dark" />
          <h2 className={textStyles.title}>Compliance do Agent Studio</h2>
        </div>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Ultimos 7 dias</SelectItem>
            <SelectItem value="30">Ultimos 30 dias</SelectItem>
            <SelectItem value="90">Ultimos 90 dias</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-lia-text-secondary" />
              <span className="text-xs text-lia-text-secondary">Execucoes</span>
            </div>
            <p className="text-2xl font-bold font-inter text-lia-text-primary">{data.total_executions}</p>
          </CardContent>
        </Card>

        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              <span className="text-xs text-lia-text-secondary">Aprovadas</span>
            </div>
            <p className="text-2xl font-bold font-inter text-emerald-600">
              {data.total_executions - data.blocked_executions}
            </p>
          </CardContent>
        </Card>

        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="w-4 h-4 text-status-warning" />
              <span className="text-xs text-lia-text-secondary">Bloqueadas</span>
            </div>
            <p className="text-2xl font-bold font-inter text-status-warning">{data.blocked_executions}</p>
            <p className="text-[10px] text-lia-text-disabled mt-0.5">{data.block_rate_pct}% do total</p>
          </CardContent>
        </Card>

        <Card className={cardStyles.default}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-1">
              <Bot className="w-4 h-4 text-wedo-cyan-dark" />
              <span className="text-xs text-lia-text-secondary">Agents ativos</span>
            </div>
            <p className="text-2xl font-bold font-inter text-lia-text-primary">{data.active_agents}</p>
            <p className="text-[10px] text-lia-text-disabled mt-0.5">
              Confianca media: {(data.avg_confidence * 100).toFixed(0)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Trend chart */}
      {data.trend.length > 0 && (
        <Card className={cardStyles.default}>
          <CardHeader>
            <CardTitle className="text-sm">Execucoes por dia</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={data.trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="executions" stroke="#60BED1" strokeWidth={2} name="Total" />
                <Line type="monotone" dataKey="blocked" stroke="#DC2626" strokeWidth={2} name="Bloqueadas" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Top blocked agents */}
      {data.top_blocked_agents.length > 0 && (
        <Card className={cardStyles.default}>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-status-warning" />
              Agents com mais bloqueios
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.top_blocked_agents.map((a, i) => (
                <div key={a.agent_id} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-lia-text-disabled font-inter">{i + 1}.</span>
                    <span className="text-lia-text-primary">{a.agent_name}</span>
                  </div>
                  <Badge className="bg-status-warning/15 text-status-warning text-xs">
                    {a.blocked_count} bloqueio{a.blocked_count !== 1 ? "s" : ""}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {data.total_executions === 0 && (
        <Card className={cardStyles.default}>
          <CardContent className="py-8 text-center">
            <Bot className="w-10 h-10 text-lia-text-disabled mx-auto mb-3" />
            <p className={textStyles.subtitle}>Sem execucoes no periodo</p>
            <p className="text-xs text-lia-text-disabled mt-1">
              Crie agents no Studio e vincule a vagas para ver metricas aqui
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
''')


# ============================================================
# 5. Wire StudioComplianceView into FairnessComplianceHub
# ============================================================
print("\n=== 5. Wire into FairnessComplianceHub ===")
patch_file(
    BASE_FE,
    "components/settings/FairnessComplianceHub.tsx",
    '''import { textStyles, cardStyles } from"@/lib/design-tokens"''',
    '''import { textStyles, cardStyles } from"@/lib/design-tokens"
import { StudioComplianceView } from"./StudioComplianceView"''',
    "import StudioComplianceView",
)

# Add early-return branching for "studio" subsection
patch_file(
    BASE_FE,
    "components/settings/FairnessComplianceHub.tsx",
    '''export function FairnessComplianceHub({ activeSubsection }: FairnessComplianceHubProps) {
  const [period, setPeriod] = useState("30")''',
    '''export function FairnessComplianceHub({ activeSubsection }: FairnessComplianceHubProps) {
  // P2.3: Studio subsection has its own dedicated view
  if (activeSubsection === "studio") {
    return <StudioComplianceView />
  }

  const [period, setPeriod] = useState("30")''',
    "branch on studio subsection",
)


# ============================================================
# VERIFY
# ============================================================
import ast
print("\n=== Verify backend ===")
try:
    ast.parse(read_file(BASE_BE, "app/api/v1/custom_agents.py"))
    print("  OK: custom_agents.py")
except SyntaxError as e:
    print(f"  ERROR: {e}")

print("\nP2.3 Compliance Dashboard complete!")
