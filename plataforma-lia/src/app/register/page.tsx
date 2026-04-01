import type { Metadata } from "next"
import RegisterClient from "./RegisterClient"

export const metadata: Metadata = {
  title: "Criar Conta | LIA — WeDo Talent",
  description: "Crie sua conta na Plataforma LIA WeDoTalent e comece a recrutar com inteligência artificial. Cadastro rápido e seguro.",
}

export default function RegisterPage() {
  return <RegisterClient />
}
