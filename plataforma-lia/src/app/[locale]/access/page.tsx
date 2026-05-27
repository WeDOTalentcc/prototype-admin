import type { Metadata } from "next"
import AccessClient from "./AccessClient"

export const metadata: Metadata = {
  title: "Acesso | WeDoTalent",
  description: "Selecione sua área de acesso na WeDoTalent. Escolha entre o portal do cliente ou o painel administrativo.",
}

export default function AccessPage() {
  return <AccessClient />
}
