"use client"

import { useState } from "react"
import type { Candidate } from "@/components/pages/candidates/types"
import { toast } from "sonner"

export function useRevealContact({
  setCreditsRemaining,
}: {
  setCreditsRemaining: (fn: (prev: number) => number) => void
}) {
  const [showRevealModal, setShowRevealModal] = useState(false)
  const [revealCandidate, setRevealCandidate] = useState<Candidate | null>(null)
  const [revealType, setRevealType] = useState<"email" | "phone">("email")
  const [revealedContacts, setRevealedContacts] = useState<Record<string, { email?: string; phone?: string }>>({})
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

  // Reuses the single-candidate reveal endpoint per candidate/type. The backend
  // only charges for contacts that actually exist, so unavailable ones are free.
  const handleBulkReveal = async (types: Array<"email" | "phone">) => {
    if (!bulkRevealCandidates.length || !types.length) return
    setIsBulkRevealing(true)
    let revealed = 0
    let unavailable = 0
    try {
      for (const cand of bulkRevealCandidates) {
        for (const type of types) {
          if (revealedContacts[cand.id]?.[type]) continue
          try {
            const response = await fetch('/api/backend-proxy/search/reveal/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                candidate_id: cand.id,
                candidate_name: cand.name,
                reveal_type: type,
                linkedin_slug: cand.linkedin_url?.split('/in/')?.[1]?.replace('/', '') || null,
              }),
            })
            const data = await response.json()
            if (data.success) {
              const value = type === 'email' ? data.email : data.phone
              setRevealedContacts(prev => ({
                ...prev,
                [cand.id]: { ...prev[cand.id], [type]: value },
              }))
              if (data.credits_remaining !== undefined && data.credits_remaining !== null) {
                setCreditsRemaining(() => data.credits_remaining)
              }
              revealed++
            } else {
              unavailable++
            }
          } catch {
            unavailable++
          }
        }
      }
      setShowBulkRevealModal(false)
      if (revealed > 0) {
        toast.success(`${revealed} contato(s) revelado(s)`, {
          description: unavailable ? `${unavailable} indisponível(is) - sem cobrança.` : undefined,
          duration: 5000,
        })
      } else {
        toast.error("Nenhum contato disponível", {
          description: "Os candidatos selecionados não tinham os contatos escolhidos.",
          duration: 5000,
        })
      }
    } finally {
      setIsBulkRevealing(false)
    }
  }

  return {
    state: { showRevealModal, revealCandidate, revealType, revealedContacts, isRevealing, showBulkRevealModal, bulkRevealCandidates, isBulkRevealing },
    actions: { setShowRevealModal, setRevealCandidate, setRevealType, setRevealedContacts, openRevealModal, handleRevealContact, openBulkRevealModal, handleBulkReveal, setShowBulkRevealModal },
  }
}

export type RevealContactState = ReturnType<typeof useRevealContact>
