import type { Metadata } from "next"
import { DashboardApp } from "@/components/dashboard-app"

export const metadata: Metadata = {
  title: "Tarefas | LIA — WeDo Talent",
  description: "Gerencie e acompanhe tarefas de recrutamento, entrevistas agendadas e atividades pendentes da sua equipe.",
}

export default function Tasks() {
  return <DashboardApp initialPage="Painel de Controle" />
}
