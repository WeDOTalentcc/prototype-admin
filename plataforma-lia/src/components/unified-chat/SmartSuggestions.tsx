"use client"

import React, { useMemo } from "react"
import { cn } from "@/lib/utils"
import {
  Briefcase, Search, BarChart2, Users, FileText, Sparkles,
  Brain, Calendar, MessageCircle, HelpCircle, Zap,
} from "lucide-react"

interface Suggestion {
  icon: React.ElementType
  label: string
  prompt: string
  category: "criar" | "buscar" | "analisar" | "comunicar" | "ajuda"
}

interface Props {
  contextPage?: string
  mode: "sidebar" | "floating" | "fullscreen"
  onSuggestionClick: (prompt: string) => void
}

/**
 * SmartSuggestions — C.2 Feature Discovery.
 *
 * Dynamic suggestions based on context page and time of day.
 * Progressive disclosure: shows most relevant first.
 * Replaces static UnifiedChatEmptyState suggestions.
 */

const ALL_SUGGESTIONS: Suggestion[] = [
  // Criar
  { icon: Briefcase, label: "Criar nova vaga", prompt: "Criar uma vaga de Product Manager Senior", category: "criar" },
  { icon: FileText, label: "Enriquecer JD", prompt: "Tenho um JD que precisa ser melhorado", category: "criar" },
  { icon: Brain, label: "Gerar perguntas WSI", prompt: "Gerar perguntas de triagem para a vaga", category: "criar" },

  // Buscar
  { icon: Search, label: "Buscar candidatos", prompt: "Buscar desenvolvedores Python senior em Sao Paulo", category: "buscar" },
  { icon: Users, label: "Talent pool", prompt: "Mostrar talent pools ativos", category: "buscar" },
  { icon: Zap, label: "Sourcing automatico", prompt: "Iniciar sourcing automatico para vagas abertas", category: "buscar" },

  // Analisar
  { icon: BarChart2, label: "Relatorio semanal", prompt: "Gerar relatorio semanal de recrutamento", category: "analisar" },
  { icon: BarChart2, label: "Saúde do Funil", prompt: "Como esta a saude do funil?", category: "analisar" },
  { icon: Sparkles, label: "Analytics de vagas", prompt: "Analytics das vagas abertas", category: "analisar" },

  // Comunicar
  { icon: MessageCircle, label: "Feedback candidatos", prompt: "Enviar feedback para candidatos rejeitados", category: "comunicar" },
  { icon: Calendar, label: "Agendar entrevista", prompt: "Agendar entrevista tecnica", category: "comunicar" },

  // Ajuda
  { icon: HelpCircle, label: "O que posso fazer?", prompt: "/ajuda", category: "ajuda" },
]

// Page-specific priority
const PAGE_PRIORITIES: Record<string, string[]> = {
  "jobs": ["criar", "analisar"],
  "candidates": ["buscar", "comunicar"],
  "pipeline": ["analisar", "comunicar"],
  "dashboard": ["analisar", "criar"],
  "agent-studio": ["buscar", "criar"],
}

// Time-based greeting
function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return "Bom dia"
  if (hour < 18) return "Boa tarde"
  return "Boa noite"
}

export function SmartSuggestions({ contextPage, mode, onSuggestionClick }: Props) {
  const suggestions = useMemo(() => {
    const priorities = PAGE_PRIORITIES[contextPage || ""] || ["criar", "buscar"]
    const sorted = [...ALL_SUGGESTIONS].sort((a, b) => {
      const aIdx = priorities.indexOf(a.category)
      const bIdx = priorities.indexOf(b.category)
      const aPri = aIdx >= 0 ? aIdx : 99
      const bPri = bIdx >= 0 ? bIdx : 99
      return aPri - bPri
    })
    // Show 4 in compact, 6 in fullscreen
    return sorted.slice(0, mode === "fullscreen" ? 6 : 4)
  }, [contextPage, mode])

  const isCompact = mode === "sidebar" || mode === "floating"

  return (
    <div className="flex flex-col items-center justify-center flex-1 px-4 py-8">
      {/* Greeting */}
      <div className="text-center mb-6">
        <div className="w-10 h-10 rounded-full bg-wedo-cyan/10 flex items-center justify-center mx-auto mb-3">
          <Sparkles className="w-5 h-5 text-wedo-cyan" />
        </div>
        <h3 className={cn(
          "font-semibold text-lia-text-primary",
          isCompact ? "text-sm" : "text-lg",
        )}>
          {getGreeting()}! Sou a LIA.
        </h3>
        <p className="text-xs text-lia-text-secondary mt-1">
          Como posso ajudar você hoje?
        </p>
      </div>

      {/* Suggestion grid */}
      <div className={cn(
        "w-full max-w-md gap-2",
        isCompact ? "flex flex-col" : "grid grid-cols-2",
      )}>
        {suggestions.map((s, i) => {
          const Icon = s.icon
          return (
            <button
              key={i}
              onClick={() => onSuggestionClick(s.prompt)}
              className="flex items-start gap-2.5 px-3 py-2.5 rounded-xl border border-lia-border-subtle bg-lia-bg-primary text-left hover:border-wedo-cyan/40 hover:bg-wedo-cyan/5 transition-colors motion-reduce:transition-none group"
            >
              <Icon className="w-4 h-4 text-lia-text-disabled group-hover:text-wedo-cyan flex-shrink-0 mt-0.5 transition-colors" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-lia-text-primary">
                  {s.label}
                </p>
              </div>
            </button>
          )
        })}
      </div>

      {/* Progressive disclosure hint */}
      <p className="text-[10px] text-lia-text-tertiary mt-4">
        Digite /ajuda para ver todas as funcionalidades
      </p>
    </div>
  )
}

/**
 * /ajuda command response — full capabilities list.
 * Called when user types /ajuda in chat.
 */
export const HELP_RESPONSE = `**O que a LIA pode fazer:**

**Criar vagas**
- Criar vaga com enriquecimento automatico do JD
- Gerar perguntas de triagem WSI (CBI/Bloom/Dreyfus)
- Configurar elegibilidade e publicar

**Buscar candidatos**
- Sourcing automatico (local/global/hibrido)
- Busca por skills, experiencia, localizacao
- Talent pools e listas

**Analisar**
- Pipeline health e gargalos
- Analytics por vaga (funil, velocidade, qualidade)
- Relatorios semanais/mensais

**Comunicar**
- Agendar entrevistas (direto ou self-scheduling)
- Enviar feedback (aprovacao/rejeicao)
- Email e WhatsApp

**Atalhos**
- @nome — mencionar candidato ou vaga
- /criar vaga — iniciar wizard
- /buscar — buscar candidatos
- /pipeline — ver pipeline
- /relatorio — gerar relatorio
- Arrastar PDF — auto-detecta CV ou JD`
