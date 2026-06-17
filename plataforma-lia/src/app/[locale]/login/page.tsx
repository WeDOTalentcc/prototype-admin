import type { Metadata } from "next"
import LoginClient from "./LoginClient"

export const metadata: Metadata = {
  title: "Entrar | WeDoTalent",
  description: "Acesse a WeDoTalent com suas credenciais. Faça login para gerenciar vagas, candidatos e pipelines de recrutamento.",
}

export default function LoginPage() {
  return <LoginClient />
}
