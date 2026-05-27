import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { TasksPage } from "@/components/pages/tasks-page"

export const metadata: Metadata = {
  title: "Decidir | WeDoTalent",
  description: "Painel diário com tarefas pendentes, alertas ativos e vagas para acompanhar com a LIA.",
}

export default function DecidirRoute() {
  return (
    <ErrorBoundarySection>
      <TasksPage />
    </ErrorBoundarySection>
  )
}
