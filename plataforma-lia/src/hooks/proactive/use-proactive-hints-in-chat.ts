"use client"

import { useEffect, useRef } from "react"

import {
  PROACTIVE_HINTS_MESSAGE_TYPE,
  buildProactiveHintsMessage,
} from "@/components/unified-chat/proactive-suggestion-injector"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import { dedupeAppend } from "@/hooks/chat/lia-chat-connection-types"
import { useProactiveActionRouter } from "@/hooks/chat/use-proactive-action-router"

import { useProactiveHints, type ProactiveHint } from "./use-proactive-hints"

/**
 * useProactiveHintsInChat — traz as sugestões proativas scheduler-driven para
 * o chat unificado como uma mensagem conversacional da LIA + cards, aposentando
 * o dropdown `ProactiveHintsBadge`.
 *
 * Comportamento (UX aprovada em 2026-06-04):
 *  - Quando há hints pendentes, a LIA posta UMA mensagem ("Notei algumas
 *    coisas…") carregando os hints ainda não exibidos em
 *    `metadata.type = "proactive_hints"`.
 *  - Idempotente: a injeção varre o transcript atual e só adiciona hints cujo
 *    id ainda não está presente — zero duplicata no poll de 60s do SWR, em
 *    re-renders ou num remount suave.
 *  - Resiliente ao restore de histórico: re-roda quando `chatIsFetchingHistory`
 *    assenta, então um reload (que substitui `chatMessages` pelo histórico do
 *    servidor) ainda re-exibe hints que continuam pendentes.
 *  - Liga os botões de ação de forma conversacional via
 *    `useProactiveActionRouter`, enviando o follow-up pelo próprio chat.
 */
export function useProactiveHintsInChat(): void {
  const { hints, isLoading } = useProactiveHints()
  const { setChatMessages, sendChatMessage, chatIsFetchingHistory } =
    useLiaChatContext()

  // Único ponto de montagem do roteador de ações proativas no app.
  useProactiveActionRouter({ sendChatMessage })

  const hintsRef = useRef<ProactiveHint[]>(hints)
  hintsRef.current = hints
  // `useProactiveHints` retorna um array novo (slice+sort) a cada render; uma
  // key estável evita re-rodar o efeito sem mudança real de conteúdo.
  const hintIdsKey = hints.map((h) => h.id).join(",")

  useEffect(() => {
    if (isLoading || chatIsFetchingHistory) return
    const current = hintsRef.current
    if (current.length === 0) return

    setChatMessages((prev) => {
      const alreadyShown = new Set<string>()
      for (const m of prev) {
        const md = m.metadata as Record<string, unknown> | undefined
        if (
          md?.type === PROACTIVE_HINTS_MESSAGE_TYPE &&
          Array.isArray(md.proactiveHints)
        ) {
          for (const h of md.proactiveHints as ProactiveHint[]) {
            alreadyShown.add(h.id)
          }
        }
      }
      const toAdd = current.filter((h) => !alreadyShown.has(h.id))
      if (toAdd.length === 0) return prev
      return dedupeAppend(prev, buildProactiveHintsMessage(toAdd))
    })
  }, [hintIdsKey, isLoading, chatIsFetchingHistory, setChatMessages])
}
