"use client"

import { useState } from "react"
import type { Candidate } from "@/components/pages/candidates/types"
import { useCandidatesStore } from "@/stores/candidates-store"
import { toast } from "sonner"

export function useRevealContact({
  setCreditsRemaining,
}: {
  setCreditsRemaining: (fn: (prev: number) => number) => void
}) {
  const [showRevealModal, setShowRevealModal] = useState(false)
  const [revealCandidate, setRevealCandidate] = useState<Candidate | null>(null)
  const [revealType, setRevealType] = useState<"email" | "phone">("email")
  // SSOT (P2 #5): revealedContacts vive no candidates-store, espelhando searchFeedbacks.
  // Produtor escreve via updater funcional com merge; consumidores recebem por prop.
  const revealedContacts = useCandidatesStore((s) => s.revealedContacts)
  const setRevealedContacts = useCandidatesStore((s) => s.setRevealedContacts)
  const [isRevealing, setIsRevealing] = useState(false)

  const openRevealModal = (candidate: Candidate, type: "email" | "phone") => {
    setRevealCandidate(candidate)
    setRevealType(type)
    setShowRevealModal(true)
  }

  const handleRevealContact = async () => {
    if (!revealCandidate) return
    setIsRevealing(true)
    try {
      const response = await fetch('/api/backend-proxy/search/reveal/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: revealCandidate.id,
          candidate_name: revealCandidate.name,
          reveal_type: revealType,
          linkedin_slug: revealCandidate.linkedin_url?.split('/in/')?.[1]?.replace('/', '') || null
        })
      })

      const data = await response.json()

      if (data.success) {
        setRevealedContacts(prev => ({
          ...prev,
          [revealCandidate.id]: {
            ...prev[revealCandidate.id],
            [revealType]: revealType === 'email' ? data.email : data.phone
          }
        }))
        setShowRevealModal(false)

        if (data.credits_remaining !== undefined && data.credits_remaining !== null) {
          setCreditsRemaining(() => data.credits_remaining)
        }

        const revealedValue = revealType === 'email' ? data.email : data.phone
        toast.success(revealType === 'email' ? "Email revelado" : "Telefone revelado", { description: revealedValue || "Contato revelado com sucesso", duration: 5000 })

        // Persistir contatos revelados automaticamente para candidatos Pearch
        if (revealCandidate.source === 'pearch') {
          try {
            const pearchId = revealCandidate.pearch_profile_id || revealCandidate.id
            const persistResponse = await fetch('/api/backend-proxy/search/candidates/persist-revealed', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                pearch_id: pearchId,
                candidate_name: revealCandidate.name,
                email: revealType === 'email' ? data.email : null,
                phone: revealType === 'phone' ? data.phone : null,
                linkedin_url: revealCandidate.linkedin_url || null,
                current_title: revealCandidate.current_title || null,
                current_company: revealCandidate.current_company || null,
                avatar_url: revealCandidate.avatar_url || null
              })
            })
            const persistData = await persistResponse.json()
            if (persistData.success) {
              toast.success("LIA salvou o contato", { description: persistData.is_new ? "Candidato adicionado à sua base local" : "Dados atualizados no cadastro existente", duration: 3000 })
            } else {
              toast.warning("Aviso", { description: "Contato revelado mas não foi salvo na base. Use 'Salvar na Base' para persistir.", duration: 4000 })
            }
          } catch {
            toast.warning("Aviso", { description: "Contato revelado mas não foi salvo automaticamente. Use 'Salvar na Base' para persistir.", duration: 4000 })
          }
        }
      } else {
        toast.error("Contato não disponível", { description: data.message || 'Não foi possível revelar o contato', duration: 5000 })
      }
    } catch {
      toast.error("Erro ao revelar contato", { description: "Ocorreu um erro. Tente novamente.", duration: 5000 })
    } finally {
      setIsRevealing(false)
    }
  }

  // ── Bulk reveal (selecionados na barra de ações) ──────────────────────────
  const [showBulkRevealModal, setShowBulkRevealModal] = useState(false)
  const [bulkRevealCandidates, setBulkRevealCandidates] = useState<Candidate[]>([])
  const [isBulkRevealing, setIsBulkRevealing] = useState(false)

  const openBulkRevealModal = (candidatesToReveal: Candidate[]) => {
    setBulkRevealCandidates(candidatesToReveal)
    setShowBulkRevealModal(true)
  }

  // Uses the bulk reveal endpoint (asyncio.gather + Semaphore(3) + timeout 35s per candidate).
  // AbortController: 120s covers 3 batches of 3 candidates × 35s ≈ 105s max real latency.
  const handleBulkReveal = async (types: Array<"email" | "phone">) => {
    if (!bulkRevealCandidates.length || !types.length) return
    setIsBulkRevealing(true)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 120_000)

    try {
      // Build items: skip already-revealed, one entry per candidate×type
      const items = bulkRevealCandidates.flatMap((cand) =>
        types
          .filter((type) => !revealedContacts[cand.id]?.[type])
          .map((type) => ({
            candidate_id: cand.id,
            candidate_name: cand.name,
            reveal_type: type,
            linkedin_slug:
              cand.linkedin_url?.split('/in/')?.[1]?.replace('/', '') || null,
          }))
      )

      if (!items.length) {
        setShowBulkRevealModal(false)
        toast.info('Contatos já revelados', { description: 'Todos os contatos selecionados já foram revelados.', duration: 3000 })
        return
      }

      const response = await fetch('/api/backend-proxy/search/reveal/bulk/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items }),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      const results: Array<{
        success: boolean
        candidate_id: string
        reveal_type: string
        email?: string
        phone?: string
        credits_remaining?: number
      }> = data.results || []

      // Update store with revealed contacts
      if (results.some((r) => r.success)) {
        setRevealedContacts((prev) => {
          const next = { ...prev }
          for (const r of results) {
            if (r.success) {
              const value = r.reveal_type === 'email' ? r.email : r.phone
              next[r.candidate_id] = { ...next[r.candidate_id], [r.reveal_type]: value }
            }
          }
          return next
        })
      }

      // Update credits from last successful result
      const lastWithCredits = [...results].reverse().find((r) => r.credits_remaining != null)
      if (lastWithCredits?.credits_remaining != null) {
        setCreditsRemaining(() => lastWithCredits.credits_remaining!)
      }

      // Fire-and-forget persist for pearch candidates
      for (const r of results) {
        if (!r.success) continue
        const cand = bulkRevealCandidates.find((c) => c.id === r.candidate_id)
        if (cand?.source === 'pearch') {
          const value = r.reveal_type === 'email' ? r.email : r.phone
          fetch('/api/backend-proxy/search/candidates/persist-revealed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              pearch_id: cand.pearch_profile_id || cand.id,
              candidate_name: cand.name,
              email: r.reveal_type === 'email' ? value : null,
              phone: r.reveal_type === 'phone' ? value : null,
              linkedin_url: cand.linkedin_url || null,
              current_title: cand.current_title || null,
              current_company: cand.current_company || null,
              avatar_url: cand.avatar_url || null,
            }),
          }).catch((e: unknown) => { console.warn("[bulk-reveal] persist-revealed failed (non-critical):", e) })
        }
      }

      setShowBulkRevealModal(false)

      const { revealed_count = 0, unavailable_count = 0, timeout_count = 0 } = data
      if (revealed_count > 0) {
        const parts: string[] = []
        if (unavailable_count) parts.push(`${unavailable_count} indisponível(is)`)
        if (timeout_count) parts.push(`${timeout_count} com timeout`)
        toast.success(`${revealed_count} contato(s) revelado(s)`, {
          description: parts.length ? parts.join(', ') + ' — sem cobrança.' : undefined,
          duration: 5000,
        })
      } else {
        toast.error('Nenhum contato disponível', {
          description: 'Os candidatos selecionados não tinham os contatos escolhidos.',
          duration: 5000,
        })
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        toast.error('Tempo esgotado', { description: 'A revelação demorou muito. Tente com menos candidatos.', duration: 5000 })
      } else {
        toast.error('Erro ao revelar contatos', { description: 'Ocorreu um erro. Tente novamente.', duration: 5000 })
      }
    } finally {
      clearTimeout(timeoutId)
      setIsBulkRevealing(false)
    }
  }

  return {
    state: { showRevealModal, revealCandidate, revealType, revealedContacts, isRevealing, showBulkRevealModal, bulkRevealCandidates, isBulkRevealing },
    actions: { setShowRevealModal, setRevealCandidate, setRevealType, setRevealedContacts, openRevealModal, handleRevealContact, openBulkRevealModal, handleBulkReveal, setShowBulkRevealModal },
  }
}

export type RevealContactState = ReturnType<typeof useRevealContact>
