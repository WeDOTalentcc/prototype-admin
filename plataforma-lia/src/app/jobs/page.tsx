import type { Metadata } from "next"
import { Suspense } from "react"
import { JobsPage } from "@/components/pages/jobs-page"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export const metadata: Metadata = {
  title: "Vagas | LIA — WeDo Talent",
  description: "Gerencie todas as vagas de emprego da sua empresa. Crie, edite e acompanhe processos seletivos com triagem inteligente por IA.",
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary p-6">
      <div className="animate-pulse motion-reduce:animate-none">
        <div className="h-8 w-48 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-xl mb-4" />
        <div className="h-4 w-96 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-xl mb-8" />
        <div className="space-y-4">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="h-16 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function JobsListPage() {
  return (
    <ErrorBoundarySection>
      <Suspense fallback={<LoadingSkeleton />}>
        <JobsPage />
      </Suspense>
    </ErrorBoundarySection>
  )
}
