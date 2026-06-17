"use client"

import React from "react"
import { Calendar, Zap, Mail, Users, MessageCircle, BarChart3, LucideIcon } from "lucide-react"
import { Button } from "./button"

export interface QuickAction {
  id: string
  label: string
  icon: LucideIcon
  onClick: () => void
  variant?: "default" | "primary" | "success" | "warning"
}

interface QuickActionChipsProps {
  actions: QuickAction[]
  className?: string
}

export const QuickActionChips = React.memo(function QuickActionChips({ actions, className = "" }: QuickActionChipsProps) {
  const getVariantStyles = (variant: QuickAction["variant"] = "default") => {
    switch (variant) {
      case "primary":
        return "text-lia-text-secondary border-lia-border-default hover:bg-lia-interactive-hover"
      case "success":
        return "bg-status-success/10 text-status-success border-status-success/30 hover:bg-status-success/20"
      case "warning":
        return "bg-status-warning/10 text-status-warning border-status-warning/30 hover:bg-status-warning/20"
      default:
        return "hover:bg-lia-interactive-hover"
    }
  }

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {actions.map((action) => {
        const Icon = action.icon
        return (
          <Button
            key={action.id}
            variant="outline"
            size="sm"
            onClick={action.onClick}
            className={`inline-flex items-center gap-2 px-3 py-1.5 h-auto rounded-md text-base-ui font-medium transition-colors motion-reduce:transition-none duration-200 border-lia-border-default ${getVariantStyles(action.variant)}`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{action.label}</span>
          </Button>
        )
      })}
    </div>
  )
})
QuickActionChips.displayName = "QuickActionChips"

export const defaultCandidateActions: Omit<QuickAction, "onClick">[] = [
  {
    id: "schedule",
    label: "Agendar Entrevista",
    icon: Calendar,
    variant: "primary"
  },
  {
    id: "evaluate",
    label: "Avaliar Fit Técnico",
    icon: Zap,
    variant: "default"
  },
  {
    id: "email",
    label: "Gerar Email",
    icon: Mail,
    variant: "default"
  },
  {
    id: "whatsapp",
    label: "Enviar WhatsApp",
    icon: MessageCircle,
    variant: "default"
  },
  {
    id: "compare",
    label: "Comparar Perfis",
    icon: Users,
    variant: "default"
  },
  {
    id: "analytics",
    label: "Ver Analytics",
    icon: BarChart3,
    variant: "default"
  }
]
