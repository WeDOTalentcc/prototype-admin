import type { Metadata } from "next"
import AjudaClient from "./AjudaClient"

export const metadata: Metadata = {
  title: "Ajuda & Suporte | WeDoTalent",
  description: "Central de ajuda da WeDoTalent. Encontre guias, tutoriais e respostas para as principais dúvidas sobre recrutamento com IA.",
}

export default function AjudaPage() {
  return <AjudaClient />
}
