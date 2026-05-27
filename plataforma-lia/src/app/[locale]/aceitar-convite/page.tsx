import type { Metadata } from "next"
import AceitarConviteClient from "./AceitarConviteClient"

export const metadata: Metadata = {
  title: "Aceitar Convite | WeDoTalent",
  description: "Aceite seu convite e crie sua conta na Plataforma LIA WeDoTalent para colaborar no processo de recrutamento da sua empresa.",
}

export default function AceitarConvitePage() {
  return <AceitarConviteClient />
}
