"use client"

/**
 * ComplianceOverviewPanel — P2-4 (audit 2026-05-26):
 *
 * Dashboard read-only que agrega sinais de compliance espalhados em outros
 * hubs/subsections do menu Configurações. Renderizado como default
 * landing do hub "Compliance & LGPD" quando o admin/compliance officer
 * abre a página sem selecionar subsection.
 *
 * Sinais agregados (5 cards):
 *  1. Taxa de consent (consent records ativos / total candidatos)
 *  2. DSR Art. 20 backlog (pedidos pendentes, dias úteis até SLA 15d)
 *  3. Audit access coverage (tenant audit logs Art. 9 LGPD)
 *  4. Fairness threshold (4/5-rule via FairnessGuard)
 *  5. Cross-tenant violations (target: 0; alerta se > 0)
 *
 * MVP: valores estáticos com TODO comments — wire-up de API real fica
 * como follow-up P3 (cada hub tem seu próprio endpoint).
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/CONFIGURACOES_MENU_COHERENCE_AUDIT.md
 * P2-4 + §3.consent-vs-lgpd (LGPD distribuído mas coeso, falta hub unificador).
 *
 * RBAC (P2-3): visível para admin/manager/recruiter/viewer (todos veem o hub
 * fairness-compliance, mas editing está gated em sub-páginas individuais).
 */

import { ShieldCheck, AlertTriangle, FileWarning, BarChart3, Lock, ArrowRight } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { textStyles } from "@/lib/design-tokens"

type Status = "ok" | "attention" | "error"

interface ComplianceMetric {
  id: string
  title: string
  value: string
  context: string
  status: Status
  icon: typeof ShieldCheck
  subsectionLink?: string
}

// TODO(P3): substituir mock por hooks reais (useConsentSummary, useDSRBacklog, etc.)
// Endpoints candidatos:
// - GET /api/backend-proxy/lgpd/consent-summary
// - GET /api/backend-proxy/lgpd/dsr-requests?status=pending
// - GET /api/backend-proxy/lgpd/audit-coverage
// - GET /api/backend-proxy/fairness-report/summary?days=30
// - GET /api/backend-proxy/lgpd/cross-tenant-violations (deve sempre retornar 0)
const STATIC_METRICS: ComplianceMetric[] = [
  {
    id: "consent",
    title: "Taxa de consentimento (90d)",
    value: "—",
    context: "Candidatos com consent LGPD ativo",
    status: "ok",
    icon: ShieldCheck,
    subsectionLink: "consent",
  },
  {
    id: "dsr",
    title: "Pedidos LGPD Art. 20",
    value: "—",
    context: "Pendentes (SLA 15 dias úteis)",
    status: "ok",
    icon: FileWarning,
    subsectionLink: "lgpd-candidatos",
  },
  {
    id: "audit",
    title: "Audit coverage (30d)",
    value: "—",
    context: "Tenant audit logs LGPD Art. 9 — direito titular acesso",
    status: "ok",
    icon: BarChart3,
    subsectionLink: "audit-summary",
  },
  {
    id: "fairness",
    title: "FairnessGuard",
    value: "—",
    context: "4/5-rule status nas decisões de IA",
    status: "ok",
    icon: ShieldCheck,
    subsectionLink: "studio",
  },
  {
    id: "cross-tenant",
    title: "Cross-tenant violations",
    value: "0",
    context: "Tentativas bloqueadas de acesso entre tenants (target: 0)",
    status: "ok",
    icon: Lock,
  },
]

const STATUS_STYLES: Record<Status, { badge: string; iconColor: string; label: string }> = {
  ok: {
    badge: "bg-status-success/10 text-status-success border-status-success/20",
    iconColor: "text-status-success",
    label: "OK",
  },
  attention: {
    badge: "bg-status-warning/10 text-status-warning border-status-warning/20",
    iconColor: "text-status-warning",
    label: "Atenção",
  },
  error: {
    badge: "bg-status-error/10 text-status-error border-status-error/20",
    iconColor: "text-status-error",
    label: "Crítico",
  },
}

interface Props {
  onNavigateToSubsection?: (subsection: string) => void
}

export function ComplianceOverviewPanel({ onNavigateToSubsection }: Props = {}) {
  return (
    <div className="space-y-4" data-testid="compliance-overview-panel">
      <div className="p-4 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary/50">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-wedo-cyan shrink-0 mt-0.5" aria-hidden="true" />
          <div className="space-y-1">
            <h3 className={textStyles.h3}>Visão geral de Compliance</h3>
            <p className="text-sm text-lia-text-secondary">
              Status agregado de LGPD, fairness e audit. Cada card abre o detalhe completo na sub-página correspondente.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {STATIC_METRICS.map((metric) => {
          const Icon = metric.icon
          const statusStyle = STATUS_STYLES[metric.status]
          return (
            <Card
              key={metric.id}
              className="border border-lia-border-subtle hover:border-lia-border-default transition-colors motion-reduce:transition-none"
              data-testid={`compliance-card-${metric.id}`}
            >
              <CardContent className="p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <Icon className={`w-5 h-5 ${statusStyle.iconColor}`} aria-hidden="true" />
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full border ${statusStyle.badge}`}
                  >
                    {statusStyle.label}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-lia-text-secondary">{metric.title}</p>
                  <p className={textStyles.kpi}>{metric.value}</p>
                </div>
                <p className="text-xs text-lia-text-secondary leading-snug">{metric.context}</p>
                {metric.subsectionLink && onNavigateToSubsection && (
                  <button
                    type="button"
                    onClick={() => onNavigateToSubsection(metric.subsectionLink!)}
                    className="flex items-center gap-1 text-xs text-wedo-cyan-text hover:underline mt-1"
                    data-testid={`compliance-card-link-${metric.id}`}
                  >
                    Ver detalhes <ArrowRight className="w-3 h-3" aria-hidden="true" />
                  </button>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      <p className="text-xs text-lia-text-secondary border-t border-lia-border-subtle pt-3">
        <AlertTriangle className="w-3 h-3 inline mr-1 text-status-warning" aria-hidden="true" />
        Valores agregados em tempo real serão wired no follow-up P3. Por ora, painel mostra a estrutura canonical.
      </p>
    </div>
  )
}
