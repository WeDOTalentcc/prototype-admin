import type { Metadata } from "next"
import VerifyEmailClient from "./VerifyEmailClient"

export const metadata: Metadata = {
  title: "Verificar Email | WeDoTalent",
  description: "Confirme seu endereço de email para ativar sua conta na WeDoTalent.",
}

export default function VerifyEmailPage() {
  return <VerifyEmailClient />
}
