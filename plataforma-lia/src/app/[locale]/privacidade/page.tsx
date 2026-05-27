import type { Metadata } from "next"
import PrivacidadeClient from "./PrivacidadeClient"

export const metadata: Metadata = {
  title: "Política de Privacidade | WeDoTalent",
  description: "Política de privacidade e proteção de dados da Plataforma LIA WeDoTalent. Saiba como seus dados são coletados, usados e protegidos conforme a LGPD.",
}

export default function PrivacidadePage() {
  return <PrivacidadeClient />
}
