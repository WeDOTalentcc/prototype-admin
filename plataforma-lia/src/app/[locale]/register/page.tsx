import type { Metadata } from "next"
import RegisterClient from "./RegisterClient"

export const metadata: Metadata = {
  title: "Criar Conta | WeDoTalent",
  description: "Crie sua conta na WeDoTalent e comece a recrutar com inteligência artificial. Cadastro rápido e seguro.",
}

export default function RegisterPage() {
  return <RegisterClient />
}
