import type { Metadata } from "next"
import ResetPasswordClient from "./ResetPasswordClient"

export const metadata: Metadata = {
  title: "Redefinir Senha | WeDoTalent",
  description: "Redefina sua senha da WeDoTalent. Escolha uma nova senha segura para proteger sua conta.",
}

export default function ResetPasswordPage() {
  return <ResetPasswordClient />
}
