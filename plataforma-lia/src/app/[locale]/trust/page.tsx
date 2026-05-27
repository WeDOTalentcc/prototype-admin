import type { Metadata } from "next"
import TrustClient from "./TrustClient"

export const metadata: Metadata = {
  title: "Trust Center | WeDoTalent",
  description: "Central de confiança e segurança da Plataforma LIA WeDoTalent. Saiba sobre nossas certificações, conformidade LGPD e práticas de proteção de dados.",
}

export default function PublicTrustCenterPage() {
  return <TrustClient />
}
