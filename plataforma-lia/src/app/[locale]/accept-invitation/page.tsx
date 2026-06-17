import type { Metadata } from "next"
import AcceptInvitationClient from "./AcceptInvitationClient"

export const metadata: Metadata = {
  title: "Aceitar Convite | WeDoTalent",
  description: "Aceite seu convite para ingressar na equipe de recrutamento na WeDoTalent e comece a colaborar.",
}

export default function AcceptInvitationPage() {
  return <AcceptInvitationClient />
}
