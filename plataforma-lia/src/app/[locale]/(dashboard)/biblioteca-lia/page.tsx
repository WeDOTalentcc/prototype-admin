import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { BibliotecaLiaRouteClient } from "./BibliotecaLiaRouteClient"

export const metadata: Metadata = {
  title: "Biblioteca LIA | WeDoTalent",
  description: "Conteúdos, prompts e recursos de IA.",
}

export default function BibliotecaLiaRoute() {
  return (
    <ErrorBoundarySection>
      <BibliotecaLiaRouteClient />
    </ErrorBoundarySection>
  )
}
