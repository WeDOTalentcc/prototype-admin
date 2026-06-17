/**
 * Task #1180 — Helper para injetar a proposta do site dentro do chat.
 * Renderizado por `WebsiteProposalCard` em `UnifiedMessageList.tsx`
 * quando `message.metadata.type === "website_proposal"`.
 */
import type { LiaChatMessage } from "@/hooks/chat/lia-chat-connection-types"
import type { ProposedSaves } from "@/lib/website-proposal-mapper"

export const WEBSITE_PROPOSAL_MESSAGE_TYPE = "website_proposal" as const

export const WEBSITE_PROPOSAL_INTRO =
  "Aqui está o que eu extraí do site. Revise, edite o que quiser e me diga o que salvar."

export function buildWebsiteProposalMessage(
  proposed: ProposedSaves,
  companyId: string,
): LiaChatMessage {
  return {
    id: `website-proposal-${Date.now()}`,
    sender: "lia",
    content: WEBSITE_PROPOSAL_INTRO,
    timestamp: new Date().toISOString(),
    metadata: {
      type: WEBSITE_PROPOSAL_MESSAGE_TYPE,
      websiteProposal: { proposed, companyId },
    },
  }
}
