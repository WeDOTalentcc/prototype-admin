import type { Metadata } from "next"
import LoginClient from "./LoginClient"

export const metadata: Metadata = {
  title: "Entrar | LIA — WeDo Talent",
  description: "Acesse a Plataforma LIA WeDoTalent com suas credenciais. Faça login para gerenciar vagas, candidatos e pipelines de recrutamento.",
}

export default function LoginPage() {
  return <LoginClient />
}
