import type { Metadata } from "next"
import ForgotPasswordClient from "./ForgotPasswordClient"

export const metadata: Metadata = {
  title: "Recuperar Senha | WeDoTalent",
  description: "Recupere o acesso à sua conta LIA WeDoTalent. Insira seu e-mail para receber as instruções de redefinição de senha.",
}

export default function ForgotPasswordPage() {
  return <ForgotPasswordClient />
}
