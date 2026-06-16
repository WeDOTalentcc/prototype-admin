import type { Metadata } from "next"
import PrivacidadeClient from "./PrivacidadeClient"

export const metadata: Metadata = {
  title: "Portal de Privacidade | WeDoTalent",
  description: "Exercite seus direitos de privacidade conforme a LGPD. Solicite revisão de decisão automatizada (Art. 20), acesso, correção ou exclusão dos seus dados pessoais.",
}

export default function PrivacidadePage() {
  return <PrivacidadeClient />
}
