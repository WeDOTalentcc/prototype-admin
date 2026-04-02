"use client"

import { useState, useEffect, useCallback } from "react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { Copy, Check, ArrowRight, Brain, X } from "lucide-react"
import { toast } from "sonner"
type AnalysisType = 'bullet_points' | 'short_paragraph' | 'detailed_bullets'

interface LiaAnalysis {
  type: AnalysisType
  content: string
  generated_at: string
  candidate_id: string
}

interface LiaAnalysisModalProps {
  isOpen: boolean
  onClose: () => void
  onOpen?: () => void
  candidate: Record<string, unknown>
  onTransportToOpinions?: (analysis: LiaAnalysis) => void
  children?: React.ReactNode
}

const ANALYSIS_TABS = [
  { id: 'bullet_points' as AnalysisType, label: 'Pontos-chave' },
  { id: 'short_paragraph' as AnalysisType, label: 'Resumo' },
  { id: 'detailed_bullets' as AnalysisType, label: 'Análise Detalhada' },
]

export function LiaAnalysisModal({
  isOpen,
  onClose,
  onOpen,
  candidate,
  onTransportToOpinions,
  children,
}: LiaAnalysisModalProps) {
  const [activeTab, setActiveTab] = useState<AnalysisType>('bullet_points')
  const [analyses, setAnalyses] = useState<Record<AnalysisType, LiaAnalysis | null>>({
    bullet_points: null,
    short_paragraph: null,
    detailed_bullets: null,
  })
  const [loadingAnalysis, setLoadingAnalysis] = useState<AnalysisType | null>(null)
  const [copiedTab, setCopiedTab] = useState<AnalysisType | null>(null)
  const [savedMessage, setSavedMessage] = useState<string | null>(null)
const generateAnalysis = useCallback(async (type: AnalysisType) => {
    if (!candidate?.id) return
    
    setLoadingAnalysis(type)
    
    try {
      const response = await fetch('/api/backend-proxy/lia/profile-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidate.id,
          analysis_type: type,
          candidate_data: {
            name: candidate.name || candidate.nome,
            current_role: candidate.currentRole || candidate.cargo_atual,
            current_company: candidate.currentCompany || candidate.empresa_atual,
            location: candidate.location || candidate.localizacao,
            experience_years: candidate.yearsOfExperience || candidate.anos_experiencia,
            skills: candidate.skills || [],
            education: candidate.education || candidate.formacao || [],
            experiences: candidate.experiences || candidate.experiencias || [],
            summary: candidate.summary || candidate.resumo,
          }
        })
      })

      if (!response.ok) {
        throw new Error('Falha ao gerar análise')
      }

      const data = await response.json()
      
      setAnalyses(prev => ({
        ...prev,
        [type]: {
          type,
          content: data.analysis,
          generated_at: new Date().toISOString(),
          candidate_id: candidate.id,
        }
      }))
    } catch (error) {
      toast.error("Erro ao gerar análise", { description: "Não foi possível gerar a análise. Tente novamente." })
    } finally {
      setLoadingAnalysis(null)
    }
  }, [candidate, toast])

  useEffect(() => {
    if (isOpen && candidate?.id && !analyses[activeTab] && loadingAnalysis !== activeTab) {
      generateAnalysis(activeTab)
    }
  }, [isOpen, activeTab, candidate?.id, analyses, loadingAnalysis, generateAnalysis])

  const handleCopy = async (type: AnalysisType) => {
    const analysis = analyses[type]
    if (!analysis?.content) return

    try {
      await navigator.clipboard.writeText(analysis.content)
      setCopiedTab(type)
      setTimeout(() => setCopiedTab(null), 2000)
      toast.success("Copiado!", { description: "Análise copiada para a área de transferência" })
    } catch (error) {
      toast.error("Erro ao copiar", { description: "Não foi possível copiar o texto" })
    }
  }

  const handleTransport = async () => {
    const analysis = analyses[activeTab]
    if (!analysis || !candidate?.id) return

    try {
      const response = await fetch('/api/backend-proxy/lia/profile-analysis/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidate.id,
          analysis_type: activeTab,
          content: analysis.content,
          user_id: 'default_user'
        })
      })

      if (!response.ok) {
        throw new Error('Falha ao salvar análise')
      }

      onTransportToOpinions?.(analysis)
      
      // Show inline message instead of toast, don't close modal
      const tabLabel = ANALYSIS_TABS.find(t => t.id === activeTab)?.label || 'Análise'
      setSavedMessage(`${tabLabel} salvo com sucesso`)
      setTimeout(() => setSavedMessage(null), 3000)
    } catch (error) {
      setSavedMessage('Erro ao salvar')
      setTimeout(() => setSavedMessage(null), 3000)
    }
  }

  const renderAnalysisContent = (type: AnalysisType) => {
    const analysis = analyses[type]
    const isLoading = loadingAnalysis === type

    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center py-6 space-y-2">
          <div className="relative">
            <Brain className="w-6 h-6 text-wedo-cyan animate-pulse motion-reduce:animate-none" />
            <div className="absolute inset-0 w-6 h-6 border-2 border-gray-900 dark:border-lia-border-medium border-t-transparent rounded-full animate-spin motion-reduce:animate-none" />
          </div>
          <p className="text-micro text-lia-text-secondary">
            LIA está gerando a análise...
          </p>
        </div>
      )
    }

    if (!analysis?.content) {
      return (
        <div className="flex flex-col items-center justify-center py-6 space-y-2">
          <Brain className="w-6 h-6 text-wedo-cyan" />
          <p className="text-micro text-lia-text-secondary">
            Clique na aba para gerar a análise
          </p>
        </div>
      )
    }

    // Format content with proper paragraphs and spacing
    const formatContent = (content: string) => {
      // Split by double newlines or single newlines
      const paragraphs = content.split(/\n\n|\n/).filter(p => p.trim())
      
      return paragraphs.map((paragraph, index) => {
        // Check if it's a bullet point
        if (paragraph.trim().startsWith('•') || paragraph.trim().startsWith('-') || paragraph.trim().startsWith('*')) {
          return (
            <p key={`bullet-${index}`} className="pl-2 mb-1.5">
              {paragraph.trim()}
            </p>
          )
        }
        return (
          <p key={`para-${index}`} className="mb-2 text-justify">
            {paragraph.trim()}
          </p>
        )
      })
    }

    return (
      // @ts-ignore TODO: fix type
      <div className="text-xs text-lia-text-primary leading-relaxed">
        <p className="font-semibold text-lia-text-primary mb-2 text-xs">{String(candidate?.name || candidate?.nome || "")}</p>
        <div className="space-y-0">
          {formatContent(analysis.content)}
        </div>
      </div>
    )
  }

  return (
    <Popover open={isOpen} onOpenChange={(open: boolean) => {
      if (open) {
        onOpen?.()
      } else {
        onClose()
      }
    }}>
      <PopoverTrigger asChild onClick={() => onOpen?.()}>
        {children}
      </PopoverTrigger>
      <PopoverContent 
        className="w-[420px] p-0 border border-lia-border-subtle rounded-md"
        side="left"
        align="start"
        sideOffset={8}
      >
        <div className="flex flex-col">
          <div className="flex items-center justify-between px-3 py-2.5 border-b border-lia-border-subtle bg-gray-50/50 rounded-t-lg">
            <div className="flex items-center gap-1.5">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              <span className="text-xs font-semibold text-lia-text-primary">Resumo do Perfil</span>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-200 rounded-md transition-colors motion-reduce:transition-none"
            >
              <X className="w-4 h-4 text-lia-text-secondary" />
            </button>
          </div>

          <div className="flex gap-1 px-3 py-2 border-b border-lia-border-subtle bg-lia-bg-primary">
            {ANALYSIS_TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none ${
                  activeTab === tab.id
                    ? 'bg-gray-800 text-white'
                    : 'text-lia-text-primary hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="min-h-chart-sm max-h-[320px] overflow-y-auto p-4 bg-lia-bg-primary">
            {renderAnalysisContent(activeTab)}
          </div>

          <div className="px-4 py-3 border-t border-lia-border-subtle bg-gray-50/50 rounded-b-lg space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-micro text-lia-text-secondary">Análise gerada pela LIA. Confirme informações.</p>
              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopy(activeTab)}
                  disabled={!analyses[activeTab]?.content}
                  className="h-7 px-2.5 gap-1 text-xs border-lia-border-subtle"
                >
                  {copiedTab === activeTab ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      Copiado
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Copiar
                    </>
                  )}
                </Button>
                <Button
                  size="sm"
                  onClick={onClose}
                  className="h-7 px-3 text-xs text-white bg-gray-800 hover:bg-gray-900"
                >
                  Concluído
                </Button>
              </div>
            </div>
            {onTransportToOpinions && analyses[activeTab]?.content && (
              <div className="space-y-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleTransport}
                  className="w-full h-7 gap-1.5 text-xs border-gray-900 dark:border-lia-border-medium text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-gray-100 dark:bg-lia-bg-secondary"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                  Transportar "{ANALYSIS_TABS.find(t => t.id === activeTab)?.label}" para Pareceres
                </Button>
                {savedMessage && (
                  <p className={`text-micro text-center ${savedMessage.includes('Erro') ? 'text-status-error' : 'text-status-success'}`}>
                    {savedMessage.includes('Erro') ? '⚠ ' : '✓ '}{savedMessage}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
