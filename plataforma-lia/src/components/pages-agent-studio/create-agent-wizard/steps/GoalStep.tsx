"use client"

import { Sparkles, Search, Heart, Phone, Settings2 } from "lucide-react"
import { useTranslations } from "next-intl"

import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

import type { AgentGoal } from "../types"

const GOALS: Array<{
  id: AgentGoal
  icon: typeof Sparkles
  label: string
  desc: string
}> = [
  {
    id: "triagem_inicial",
    icon: Sparkles,
    label: "Triagem inicial automatizada",
    desc: "Analisar CV, ranquear candidatos e gerar Big Five/WSI scores",
  },
  {
    id: "sourcing_ativo",
    icon: Search,
    label: "Sourcing ativo",
    desc: "Encontrar candidatos no LinkedIn ou no talent pool da empresa",
  },
  {
    id: "screening_cultural",
    icon: Heart,
    label: "Screening cultural / fit",
    desc: "Avaliar match com cultura e valores da empresa",
  },
  {
    id: "voz_whatsapp",
    icon: Phone,
    label: "Triagem por voz ou WhatsApp",
    desc: "Conversar com candidato via canal de mensagem",
  },
  {
    id: "outro",
    icon: Settings2,
    label: "Outro / criar do zero",
    desc: "Quero configurar tudo manualmente ou explorar opcoes",
  },
]

interface GoalStepProps {
  goal: AgentGoal | null
  onSelect: (goal: AgentGoal) => void
}

export function GoalStep({ goal, onSelect }: GoalStepProps) {
  const t = useTranslations("agents.studio.wizard")
  return (
    <div className="space-y-3" role="radiogroup" aria-label={t("goalAriaLabel")}>
      <p className="text-sm text-lia-text-secondary">
        Escolha o que voce quer que o agente faca. Vamos sugerir o melhor caminho no proximo passo.
      </p>
      {GOALS.map(({ id, icon: Icon, label, desc }) => (
        <Card
          key={id}
          role="radio"
          aria-checked={goal === id}
          tabIndex={0}
          data-testid={`goal-option-${id}`}
          onClick={() => onSelect(id)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault()
              onSelect(id)
            }
          }}
          className={cn(
            "cursor-pointer transition-shadow duration-200 hover:shadow-lia-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30",
            goal === id && "border-pebble ring-2 ring-graphite/20",
          )}
        >
          <CardContent className="flex items-start gap-3 p-4">
            <div
              className={cn(
                "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                goal === id ? "bg-powder text-graphite" : "bg-lia-bg-tertiary text-lia-text-secondary",
              )}
              aria-hidden="true"
            >
              <Icon className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold text-lia-text-primary">{label}</div>
              <div className="text-xs text-lia-text-secondary mt-0.5">{desc}</div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
