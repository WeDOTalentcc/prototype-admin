"use client"

import type React from "react"
import type { Candidate } from "../types"
import { toast } from "sonner"
import type { ChatMessage } from "./candidates-core"
import { getInitialDisplayedResultsCount } from '@/stores/candidates-store'

export interface CandidatesCVHandlersContext {
  setCandidates: (v: Candidate[]) => void
  setIsDroppingCV: (v: boolean) => void
  setCvUploadLoading: (v: boolean) => void
  setHasSearchResults: (v: boolean) => void
  setSearchResultsCount: (v: number) => void
  setShowSearchResults: (v: boolean) => void
  setDisplayedResultsCount: (v: number) => void
  setChatMessages: (v: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void
}

export function useCandidatesCVHandlers(ctx: CandidatesCVHandlersContext) {
  const {
    setCandidates,
    setIsDroppingCV,
    setCvUploadLoading,
    setHasSearchResults,
    setSearchResultsCount,
    setShowSearchResults,
    setDisplayedResultsCount,
    setChatMessages,
  } = ctx

  const handleCVDrop = async (e: DragEvent) => {
    e.preventDefault()
    setIsDroppingCV(false)

    const files = e.dataTransfer?.files
    if (!files) return
    if (files.length === 0) return

    const file = files[0]
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']

    if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|doc|docx|txt)$/i)) {
      toast.error("Formato inválido", { description: "Por favor, envie um arquivo PDF, DOC, DOCX ou TXT" })
      return
    }

    setCvUploadLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/backend-proxy/search/candidates/from-cv?limit=20&search_pearch=false', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Erro ao processar CV')
      }

      const data = await response.json()

      // Add LIA message with results (only show local results - user can opt-in to global)
      const liaMessage = {
        id: `lia-cv-${Date.now()}`,
        type: 'lia' as const,
        content: `📄 Analisei o CV **${file.name}** e encontrei:\n\n` +
          `**Perfil extraído:**\n` +
          `• Título: ${data.extracted_title || 'Não identificado'}\n` +
          `• Skills: ${data.extracted_skills?.slice(0, 5).join(', ') || 'Não identificadas'}\n\n` +
          `**Busca na base local:**\n` +
          `• Query gerada: "${data.query_generated}"\n` +
          `• ${data.local_count || data.total_count} candidato${(data.local_count || data.total_count) > 1 ? 's' : ''} encontrado${(data.local_count || data.total_count) > 1 ? 's' : ''}`,
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, liaMessage])

      // Update candidates with results if available
      if (data.candidates && data.candidates.length > 0) {
        const mappedCandidates: Candidate[] = data.candidates.map((c: Record<string, unknown>) => ({
          id: c.id || `cv-${Date.now()}-${Math.random()}`,
          candidateId: c.id || '',
          name: c.name || `${c.first_name || ''} ${c.last_name || ''}`.trim(),
          email: '',
          phone: '',
          current_title: c.current_title || c.headline,
          current_company: c.current_company,
          linkedin_url: c.linkedin_url,
          technical_skills: (c.skills as string[]) || [],
          location_city: (c.location as string)?.split(',')[0]?.trim(),
          avatar_url: c.picture_url,
          years_of_experience: c.total_experience_years,
          status: 'new',
          source: c.source || 'local',
          position: c.current_title || 'Não especificado',
          location: c.location || 'Não especificado',
          workModel: 'remoto' as 'remoto' | 'híbrido' | 'presencial',
          score: typeof c.score === 'number' ? c.score : 0,  // P1-2: sem 75 fabricado
          skills: c.skills || [],
          experience: c.total_experience_years || 0,
          education: 'Não informado',
          contractType: 'CLT' as 'CLT' | 'PJ' | 'Freelancer',
          linkedin: c.linkedin_url || '',
          monthlySalary: 0,
          avatar: c.picture_url
        }))

        setCandidates(mappedCandidates)
        setHasSearchResults(true)
        setSearchResultsCount(mappedCandidates.length)
        setShowSearchResults(true)
        setDisplayedResultsCount(getInitialDisplayedResultsCount())

        toast.info("CV analisado", { description: `Encontrados ${mappedCandidates.length} candidatos similares` })
      }
    } catch (error) {
      toast.error("Erro ao processar CV", { description: error instanceof Error ? error.message : 'Erro desconhecido' })
    } finally {
      setCvUploadLoading(false)
    }
  }

  const handleCVDragOver = (e: DragEvent) => {
    e.preventDefault()
    setIsDroppingCV(true)
  }

  const handleCVDragLeave = (e: DragEvent) => {
    e.preventDefault()
    setIsDroppingCV(false)
  }

  return { handleCVDrop, handleCVDragOver, handleCVDragLeave }
}
