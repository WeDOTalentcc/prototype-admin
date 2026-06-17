"use client"

/**
 * AgentConversationPreview — Fase 3 Sprint 2 ("mostrar o agente em ação").
 *
 * Padrão ElevenLabs adaptado ao recrutador: em vez de descrever o que o agente
 * faz, mostramos 2-4 turnos de uma conversa real (Candidato ↔ Agente) que
 * evidencia o VALOR — análise, justificativa, recomendação. Reutilizável em
 * card (compact), modal de detalhe (full) e wizard.
 *
 * DECISÃO DE DESIGN (white-label canonical, memory project_white_label_ai_assistant
 * + sensor check_no_lia_hardcoded_in_studio):
 *   No Agent Studio, o agente é do CLIENTE (white-label), não a assistente da
 *   plataforma. A regra de exclusividade-cyan reserva o acento da marca para a
 *   assistente da plataforma quando ELA age — não para os agentes que o
 *   recrutador cria. Logo o balão do agente usa um acento TONAL NEUTRO
 *   (lia-bg-tertiary + lia-border-medium + avatar graphite), não o acento da
 *   marca. Isso satisfaz o sensor que protege o acento da marca em
 *   pages-agent-studio/ e mantém o produto white-label coerente. O contraste
 *   candidato/agente vem da tonalidade (powder claro vs. tertiary mais firme)
 *   + avatar, não de cor de marca.
 *
 * Flat-by-default (DESIGN.md): sem shadow; hierarquia por tonal layering.
 *
 * Acessibilidade (WCAG 2.1 AA): lista semântica (role="list") com aria-label
 * traduzido; cada turno anuncia o papel (Candidato / Agente) via texto visível
 * + sr-only redundante para leitores de tela.
 */

import { Brain, User } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"

import { cn } from "@/lib/utils"
import {
  getSampleConversation,
  type ConversationTurn,
} from "@/lib/agents/sample-conversations"

export interface AgentConversationPreviewProps {
  /** Turnos explícitos. Quando ausente, derivados de slug/category/locale. */
  turns?: ConversationTurn[]
  /** Slug canonical do template (preferido para lookup de diálogo curado). */
  slug?: string | null
  /** Categoria do agente (fallback de lookup). */
  category?: string | null
  /** Compact: 2 turnos, densidade de card. Full (default): 3-4 turnos. */
  compact?: boolean
  /** Nome do agente exibido no balão (white-label via useAiPersona no consumer). */
  agentName?: string
  className?: string
}

export function AgentConversationPreview({
  turns,
  slug,
  category,
  compact = false,
  agentName,
  className,
}: AgentConversationPreviewProps) {
  const t = useTranslations("agents.studio.conversationPreview")
  const locale = useLocale()

  const resolvedTurns =
    turns ??
    getSampleConversation({ slug, category, locale, compact })

  if (resolvedTurns.length === 0) return null

  const agentLabel = agentName?.trim() || t("agentRole")
  const candidateLabel = t("candidateRole")

  return (
    <ul
      role="list"
      aria-label={t("ariaLabel")}
      data-testid="agent-conversation-preview"
      data-compact={compact ? "true" : "false"}
      className={cn("flex flex-col gap-2", className)}
    >
      {resolvedTurns.map((turn, index) => {
        const isAgent = turn.role === "agent"
        const roleLabel = isAgent ? agentLabel : candidateLabel
        return (
          <li
            key={index}
            data-testid={`conversation-turn-${turn.role}`}
            className={cn(
              "flex w-full gap-2",
              isAgent ? "flex-row" : "flex-row-reverse",
            )}
          >
            {/* Avatar tonal neutro — graphite sobre powder/tertiary. Sem cyan
                (white-label Studio). Brain = o agente respondendo; User =
                candidato. */}
            <span
              aria-hidden="true"
              className={cn(
                "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full",
                isAgent
                  ? "bg-lia-bg-tertiary text-lia-text-secondary"
                  : "bg-powder text-lia-text-disabled dark:bg-lia-bg-secondary",
              )}
            >
              {isAgent ? (
                <Brain className="h-3.5 w-3.5" />
              ) : (
                <User className="h-3.5 w-3.5" />
              )}
            </span>

            <div
              className={cn(
                "min-w-0 max-w-[82%] rounded-xl px-3 py-2",
                isAgent
                  ? "rounded-tl-sm border border-lia-border-medium bg-lia-bg-tertiary"
                  : "rounded-tr-sm bg-powder dark:bg-lia-bg-secondary",
              )}
            >
              <p
                className={cn(
                  "text-[10px] font-semibold uppercase tracking-wider",
                  "text-lia-text-disabled",
                )}
              >
                <span className="sr-only">{t("turnFrom")} </span>
                {roleLabel}
              </p>
              <p
                className={cn(
                  "mt-0.5 leading-relaxed text-lia-text-primary",
                  compact ? "text-xs line-clamp-3" : "text-sm",
                )}
              >
                {turn.text}
              </p>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
