"use client"

import { useParams } from "next/navigation"
import { Loader2 } from "lucide-react"
import { useCandidateForPage } from "@/hooks/candidates/use-candidate-for-page"
import { CandidatePage } from "@/components/candidate-page"

/**
 * Standalone route wrapper for /funil-de-talentos/candidato/[id].
 * Loads candidate via URL id and renders <CandidatePage> in 'page' mode.
 *
 * For drawer/kanban context, callers pass candidate prop directly to
 * <CandidatePage mode="modal" />.
 */
export default function CandidateRoutePage() {
  const params = useParams()
  const id = params?.id as string | undefined
  const { candidate, loading, error } = useCandidateForPage(id)

  if (loading) {
    return (
      <div
        className="flex items-center justify-center min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary"
        role="status"
        aria-live="polite"
      >
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary mx-auto mb-3" aria-hidden="true" />
          <p className="text-sm text-lia-text-secondary">Carregando perfil...</p>
        </div>
      </div>
    )
  }

  if (error || !candidate) {
    return (
      <div
        className="flex items-center justify-center min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary"
        role="alert"
        aria-live="assertive"
      >
        <p className="text-sm text-status-error">{error || "Candidato não encontrado"}</p>
      </div>
    )
  }

  return (
    <CandidatePage
      candidate={candidate as unknown as Record<string, unknown>}
      mode="page"
    />
  )
}
