/**
 * Proactive hints → chat message bridge. Mirrors `website-proposal-injector`:
 * builds a LIA chat message that `UnifiedMessageList` renders as
 * `<ProactiveSuggestionCard />` when `metadata.type === "proactive_hints"`.
 *
 * Substitui o dropdown da lâmpada (`ProactiveHintsBadge`) — as sugestões
 * proativas scheduler-driven agora chegam como mensagem conversacional + cards
 * dentro do chat unificado (chat-first).
 */
import {
  type LiaChatMessage,
  createMessageId,
  formatMessageTime,
} from "@/hooks/chat/lia-chat-connection-types"
import type { ProactiveHint } from "@/hooks/proactive/use-proactive-hints"

export const PROACTIVE_HINTS_MESSAGE_TYPE = "proactive_hints" as const

export const PROACTIVE_HINTS_INTRO =
  "Notei algumas coisas que talvez precisem da sua atenção:"

export function buildProactiveHintsMessage(
  hints: ProactiveHint[],
): LiaChatMessage {
  return {
    id: createMessageId("proactive-hints"),
    sender: "lia",
    content: PROACTIVE_HINTS_INTRO,
    timestamp: formatMessageTime(),
    metadata: {
      type: PROACTIVE_HINTS_MESSAGE_TYPE,
      proactiveHints: hints,
    },
  }
}
