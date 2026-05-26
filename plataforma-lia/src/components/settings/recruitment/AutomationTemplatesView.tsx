"use client"

/**
 * AutomationTemplatesView — Sprint B canonical impeccable.
 *
 * Lista de templates canonical. Click → 1-click import:
 * - Hidratam SentenceBuilder com state pré-preenchido
 * - User pode editar ANTES de salvar
 *
 * Voice "Quiet Operator": templates são SUGESTÕES, não imposições.
 *
 * Audit ref: AUTOMATIONS_SPRINT_PLAN_ADR.md Sprint B + IMPECCABLE_CRITIQUE
 */

import { Card, CardContent } from "@/components/ui/card"
import {
  ArrowRight,
  Calendar,
  Filter,
  Mail,
  MessageCircle,
  Sparkles,
  Workflow,
  type LucideIcon,
} from "lucide-react"

// Map canonical category → icon
const CATEGORY_ICON: Record<string, LucideIcon> = {
  communication: Mail,
  pipeline: Sparkles,
  scheduling: Calendar,
  screening: Filter,
  workflow: Workflow,
}

// SentenceBuilder state shape (mirrored from canonical YAML)
export interface AutomationTemplateState {
  trigger: { type: string; params: Record<string, unknown> }
  conditions: Array<{ field: string; operator: string; value: unknown }>
  actions: Array<{ type: string; params: Record<string, unknown> }>
  name: string
}

export interface AutomationTemplate {
  id: string
  name: string
  category: keyof typeof CATEGORY_ICON | string
  description: string
  impact: string
  state: AutomationTemplateState
}

// Templates hardcoded canonical — mesmas keys do YAML backend
// (TODO Sprint B.3: fetch via /api/backend-proxy/automation-templates GET)
export const AUTOMATION_TEMPLATES: AutomationTemplate[] = [
  {
    id: "welcome_email_on_apply",
    name: "Email de boas-vindas pós-aplicação",
    category: "communication",
    description:
      "Quando candidato se aplica a uma vaga, envie email de boas-vindas confirmando recebimento e próximos passos.",
    impact: "Recrutador economiza ~5 min por aplicação. Candidato sai com clareza.",
    state: {
      trigger: { type: "candidate_applied", params: {} },
      conditions: [],
      actions: [
        {
          type: "send_email",
          params: { template_id: "welcome_application_received" },
        },
      ],
      name: "Boas-vindas após aplicação",
    },
  },
  {
    id: "auto_advance_high_wsi",
    name: "Auto-avanço quando WSI > 80",
    category: "pipeline",
    description:
      "Quando candidato recebe score WSI > 80 na triagem, move automaticamente para etapa Entrevista (skip de revisão manual em high-confidence).",
    impact:
      "Reduz tempo médio até entrevista em 2-3 dias. Use apenas se autonomy_level >= medium nas políticas.",
    state: {
      trigger: { type: "wsi_score_received", params: {} },
      conditions: [
        { field: "candidate.wsi_score", operator: "gt", value: 80 },
      ],
      actions: [
        { type: "move_stage", params: { stage_id: "interview" } },
      ],
      name: "Avanço automático WSI alto",
    },
  },
  {
    id: "rejection_feedback_24h",
    name: "Feedback de recusa em até 24h",
    category: "communication",
    description:
      "Quando candidato é movido para etapa Rejeitado, envia automaticamente feedback personalizado em até 24h (LGPD tempestividade).",
    impact: "Compliance LGPD + experiência candidato melhor.",
    state: {
      trigger: { type: "stage_changed", params: { stage_id: "rejected" } },
      conditions: [],
      actions: [
        {
          type: "send_email",
          params: { template_id: "rejection_with_feedback" },
        },
      ],
      name: "Feedback automático após rejeição",
    },
  },
  {
    id: "interview_invite_whatsapp",
    name: "Convite de entrevista por WhatsApp",
    category: "scheduling",
    description:
      "Quando candidato chega na etapa Entrevista, envia link de agendamento por WhatsApp (canal preferido per candidate research).",
    impact: "Taxa de resposta WhatsApp ~80% vs ~40% email. Reduz no-show.",
    state: {
      trigger: { type: "stage_changed", params: { stage_id: "interview" } },
      conditions: [],
      actions: [
        {
          type: "send_whatsapp",
          params: { template_id: "interview_invite" },
        },
      ],
      name: "Convite entrevista WhatsApp",
    },
  },
  {
    id: "salary_filter",
    name: "Filtro de pretensão salarial fora da faixa",
    category: "screening",
    description:
      "Quando candidato declara pretensão fora da tolerância salarial da vaga, move para Rejeitado automaticamente com feedback transparente.",
    impact:
      "Recrutador foca tempo em candidatos viáveis. Candidato sai com clareza imediata.",
    state: {
      trigger: { type: "candidate_applied", params: {} },
      conditions: [
        {
          field: "candidate.salary_outside_range",
          operator: "eq",
          value: true,
        },
      ],
      actions: [
        { type: "move_stage", params: { stage_id: "rejected" } },
        {
          type: "send_email",
          params: { template_id: "salary_mismatch" },
        },
      ],
      name: "Filtro salarial automático",
    },
  },
  {
    id: "manager_approval_alert",
    name: "Alerta de aprovação pendente do gestor",
    category: "workflow",
    description:
      "Quando oferta aguarda aprovação do gestor há mais de 48h, alerta o gestor (e CC recrutador) por email.",
    impact: "Evita ofertas presas no pipeline. SLA visível.",
    state: {
      trigger: {
        type: "offer_pending_approval",
        params: { hours_threshold: 48 },
      },
      conditions: [],
      actions: [
        {
          type: "send_email",
          params: {
            template_id: "manager_approval_reminder",
            cc_recruiter: true,
          },
        },
      ],
      name: "Alerta aprovação pendente",
    },
  },
  {
    id: "stale_pipeline_nudge",
    name: "Cutucada de pipeline parado",
    category: "workflow",
    description:
      "Quando candidato fica > 7 dias na mesma etapa, notifica recrutador pra mover ou rejeitar (anti-pipeline-stale).",
    impact: "Mantém pipeline saudável. Candidato não 'morre' esperando.",
    state: {
      trigger: {
        type: "candidate_stale_in_stage",
        params: { days_threshold: 7 },
      },
      conditions: [],
      actions: [
        {
          type: "notify_recruiter",
          params: { message_template: "stale_candidate_nudge" },
        },
      ],
      name: "Pipeline parado há 7 dias",
    },
  },
  {
    id: "post_offer_celebration",
    name: "Mensagem de celebração pós-aceite",
    category: "communication",
    description:
      "Quando candidato aceita oferta, envia WhatsApp celebrando + email com próximos passos pra onboarding.",
    impact: "Reduz arrependimento pós-aceite. Inicia onboarding com energia.",
    state: {
      trigger: { type: "offer_accepted", params: {} },
      conditions: [],
      actions: [
        {
          type: "send_whatsapp",
          params: { template_id: "offer_celebration" },
        },
        {
          type: "send_email",
          params: { template_id: "pre_onboarding_steps" },
        },
      ],
      name: "Celebração aceite oferta",
    },
  },
]

interface Props {
  onUseTemplate: (templateState: AutomationTemplateState) => void
}

export function AutomationTemplatesView({ onUseTemplate }: Props) {
  return (
    <div className="space-y-4" data-testid="automation-templates-view">
      <div className="space-y-1">
        <h3 className="text-sm font-medium text-lia-text-primary">
          Exemplos prontos pra começar
        </h3>
        <p className="text-xs text-lia-text-secondary">
          Use como ponto de partida. Você ajusta tudo antes de salvar.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {AUTOMATION_TEMPLATES.map((tpl) => {
          const Icon = CATEGORY_ICON[tpl.category] ?? MessageCircle
          return (
            <Card
              key={tpl.id}
              className="border-lia-border-subtle hover:border-wedo-cyan/40 transition-colors motion-reduce:transition-none"
              data-testid={`template-card-${tpl.id}`}
            >
              <CardContent className="p-4 space-y-2">
                <div className="flex items-start gap-2">
                  <Icon
                    className="w-4 h-4 text-wedo-cyan shrink-0 mt-0.5"
                    aria-hidden="true"
                    data-testid={`template-icon-${tpl.id}`}
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-lia-text-primary leading-snug">
                      {tpl.name}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-lia-text-secondary leading-snug">
                  {tpl.description}
                </p>
                <p className="text-xs text-lia-text-tertiary italic">
                  {tpl.impact}
                </p>
                <button
                  type="button"
                  onClick={() => onUseTemplate(tpl.state)}
                  className="text-xs text-wedo-cyan hover:underline inline-flex items-center gap-1 mt-1"
                  data-testid={`template-use-${tpl.id}`}
                >
                  Usar este{" "}
                  <ArrowRight className="w-3 h-3" aria-hidden="true" />
                </button>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
