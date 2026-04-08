"use client"

import React from "react"
import { CheckCircle, Circle, Loader2, ArrowRight } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

/**
 * FlowStepMessage — renders as a special LIA chat message showing workflow progress.
 *
 * Inspired by Claude Code's step-by-step execution flow.
 * Renders inline in the chat alongside regular LiaChatMessage components.
 *
 * Usage in chat message list:
 *   {msg.type === 'flow' ? (
 *     <FlowStepMessage steps={msg.flowSteps} question={msg.flowQuestion} />
 *   ) : (
 *     <LiaChatMessage type={msg.role} content={msg.content} timestamp={msg.timestamp} />
 *   )}
 */

export interface FlowStep {
  id: string
  label: string
  icon?: string           // emoji icon for the step
  status: "completed" | "in_progress" | "pending"
  detail?: string         // e.g. "47 candidatos encontrados"
}

interface FlowStepMessageProps {
  steps: FlowStep[]
  question?: string       // e.g. "Quer o fluxo completo ou parar em algum ponto?"
  onSelectScope?: (stepId: string | "all") => void  // called when user picks scope
  compact?: boolean       // inline mode (inside message) vs standalone
}

export default function FlowStepMessage({
  steps, question, onSelectScope, compact = false,
}: FlowStepMessageProps) {
  return (
    <div className={`${compact ? "" : "bg-gray-50 rounded-lg p-4 my-2"}`}>
      {/* Flow steps */}
      <div className="flex items-center gap-1 flex-wrap">
        {steps.map((step, i) => (
          <React.Fragment key={step.id}>
            <FlowStepChip step={step} />
            {i < steps.length - 1 && (
              <ArrowRight className={`w-3 h-3 flex-shrink-0 ${
                step.status === "completed" ? "text-gray-700" : "text-gray-300"
              }`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Active step detail */}
      {steps.filter(s => s.status === "in_progress" && s.detail).map(s => (
        <p key={s.id} className={`${textStyles.caption} mt-2 text-gray-600`}>
          {s.detail}
        </p>
      ))}

      {/* Scope question */}
      {question && onSelectScope && (
        <div className="mt-3 pt-2 border-t border-gray-200">
          <p className={`${textStyles.bodySmall} mb-2`}>{question}</p>
          <div className="flex gap-2">
            <button
              onClick={() => onSelectScope("all")}
              className="px-3 py-1.5 text-xs rounded-md bg-gray-900 text-white hover:bg-gray-800 transition-colors"
            >
              Fluxo completo
            </button>
            {steps.filter(s => s.status === "pending").map(s => (
              <button
                key={s.id}
                onClick={() => onSelectScope(s.id)}
                className="px-3 py-1.5 text-xs rounded-md border border-gray-300 text-gray-600 hover:bg-gray-100 transition-colors"
              >
                Até {s.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ---------- Flow Step Chip ----------

function FlowStepChip({ step }: { step: FlowStep }) {
  const statusConfig = {
    completed: {
      bg: "bg-gray-900",
      text: "text-white",
      icon: <CheckCircle className="w-3 h-3" />,
    },
    in_progress: {
      bg: "bg-yellow-100",
      text: "text-yellow-800",
      icon: <Loader2 className="w-3 h-3 animate-spin" />,
    },
    pending: {
      bg: "bg-gray-100",
      text: "text-gray-400",
      icon: <Circle className="w-3 h-3" />,
    },
  }
  const config = statusConfig[step.status]

  return (
    <div
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs ${config.bg} ${config.text}`}
      title={step.detail || step.label}
    >
      {step.icon ? <span>{step.icon}</span> : config.icon}
      <span className="font-medium">{step.label}</span>
    </div>
  )
}

// ---------- Prebuilt Flow Templates ----------

/**
 * Predefined flow templates for common actions.
 * Use these to quickly construct FlowStepMessage data.
 */
export const FLOW_TEMPLATES = {
  createJobWithSourcing: (currentStep: string = "definition"): FlowStep[] => {
    const steps = [
      { id: "search", label: "Busca", icon: "🔍" },
      { id: "definition", label: "Vaga", icon: "📋" },
      { id: "agent", label: "Agente", icon: "🤖" },
      { id: "calibration", label: "Calibrar", icon: "✅" },
      { id: "wait", label: "Aguardar", icon: "⏳" },
    ]
    return assignStatuses(steps, currentStep)
  },

  searchToAction: (count: number): FlowStep[] => [
    { id: "search", label: "Busca", icon: "🔍", status: "completed", detail: `${count} encontrados` },
    { id: "action", label: "Ação", icon: "📋", status: "pending" },
  ],

  poolSourcing: (currentStep: string = "config"): FlowStep[] => {
    const steps = [
      { id: "config", label: "Config", icon: "⚙️" },
      { id: "calibration", label: "Calibrar", icon: "✅" },
      { id: "sourcing", label: "Sourcing", icon: "🤖" },
    ]
    return assignStatuses(steps, currentStep)
  },

  screening: (currentStep: string = "screening"): FlowStep[] => {
    const steps = [
      { id: "screening", label: "Triagem", icon: "📋" },
      { id: "wsi", label: "WSI", icon: "📊" },
      { id: "interview", label: "Entrevista", icon: "🗓" },
    ]
    return assignStatuses(steps, currentStep)
  },

  fullCampaign: (currentStep: string = "definition"): FlowStep[] => {
    const steps = [
      { id: "definition", label: "Vaga", icon: "📋" },
      { id: "sourcing", label: "Sourcing", icon: "🔍" },
      { id: "screening", label: "Triagem", icon: "🔄" },
      { id: "wsi", label: "WSI", icon: "📊" },
      { id: "interview", label: "Entrevista", icon: "🗓" },
      { id: "offer", label: "Oferta", icon: "💼" },
    ]
    return assignStatuses(steps, currentStep)
  },
}

function assignStatuses(
  steps: Array<Omit<FlowStep, "status">>,
  currentStep: string
): FlowStep[] {
  const currentIdx = steps.findIndex(s => s.id === currentStep)
  return steps.map((s, i) => ({
    ...s,
    status: i < currentIdx ? "completed" as const
          : i === currentIdx ? "in_progress" as const
          : "pending" as const,
  }))
}
