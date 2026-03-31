// @ts-nocheck
"use client"

import React, { useState, useEffect, useRef, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  Save, 
  RefreshCw, 
  Workflow, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Brain,
  Info,
  Pencil,
  X,
  Plus
} from "lucide-react"
import { 
  RecruitmentJourneyConfig, 
  RecruitmentStage, 
  DEFAULT_STAGES 
} from "@/components/settings/RecruitmentJourneyConfig"

export default function JornadaRecrutamentoPage() {
  const [stages, setStages] = useState<RecruitmentStage[]>(DEFAULT_STAGES)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [originalStages, setOriginalStages] = useState<RecruitmentStage[]>(DEFAULT_STAGES)
  const [isEditMode, setIsEditMode] = useState(false)
  const [stagesBeforeEdit, setStagesBeforeEdit] = useState<RecruitmentStage[]>([])
  const [companyId, setCompanyId] = useState<string | null>(null)
  const isMountedRef = useRef(true)
  const abortControllerRef = useRef<AbortController | null>(null)

  const loadStages = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()
    const signal = abortControllerRef.current.signal

    try {
      const companyRes = await fetch('/api/backend-proxy/company/profile/', { signal })
      if (!isMountedRef.current) return
      
      let fetchedCompanyId: string | null = null
      if (companyRes.ok) {
        const company = await companyRes.json()
        if (company && company.id) {
          fetchedCompanyId = company.id
          if (isMountedRef.current) setCompanyId(fetchedCompanyId)
        }
      }
      
      if (!fetchedCompanyId) {
        if (isMountedRef.current) {
          setStages(DEFAULT_STAGES)
          setOriginalStages(DEFAULT_STAGES)
          setIsLoading(false)
        }
        return
      }
      
      const url = `/api/backend-proxy/recruitment-journey/templates/?company_id=${fetchedCompanyId}`
      const response = await fetch(url, { signal })
      if (!isMountedRef.current) return
      
      if (response.ok) {
        const data = await response.json()
        if (data.templates && data.templates.length > 0) {
          const template = data.templates[0]
          const stagesData = template.stages_config || template.stages
          if (stagesData && stagesData.length > 0) {
            if (isMountedRef.current) {
              setStages(stagesData)
              setOriginalStages(stagesData)
            }
          }
        }
      }
    } catch (error: unknown) {
      if (error.name === 'AbortError') return
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    loadStages()
    
    return () => {
      isMountedRef.current = false
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [loadStages])

  const handleStagesChange = (newStages: RecruitmentStage[]) => {
    setStages(newStages)
    setHasChanges(JSON.stringify(newStages) !== JSON.stringify(originalStages))
    setSaveStatus('idle')
  }

  const handleStartEdit = () => {
    setStagesBeforeEdit([...stages])
    setIsEditMode(true)
  }

  const handleCancelEdit = () => {
    setStages(stagesBeforeEdit)
    setHasChanges(false)
    setIsEditMode(false)
    setSaveStatus('idle')
  }

  const handleSave = async () => {
    setIsSaving(true)
    setSaveStatus('idle')
    
    try {
      let currentCompanyId = companyId
      if (!currentCompanyId) {
        const companyRes = await fetch('/api/backend-proxy/company/profile/')
        if (companyRes.ok) {
          const company = await companyRes.json()
          if (company && company.id) {
            currentCompanyId = company.id
            setCompanyId(currentCompanyId)
          }
        }
      }
      
      const url = currentCompanyId 
        ? `/api/backend-proxy/recruitment-journey/templates/?company_id=${currentCompanyId}`
        : '/api/backend-proxy/recruitment-journey/templates/'
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Pipeline Principal',
          description: 'Jornada de recrutamento padrão da empresa',
          stages_config: stages,
          is_default: true,
          company_id: currentCompanyId
        })
      })

      if (response.ok) {
        setSaveStatus('success')
        setOriginalStages(stages)
        setHasChanges(false)
        setIsEditMode(false)
        setTimeout(() => setSaveStatus('idle'), 3000)
      } else {
        setSaveStatus('error')
      }
    } catch (error) {
      setSaveStatus('error')
    } finally {
      setIsSaving(false)
    }
  }

  const handleResetToDefault = () => {
    setStages(DEFAULT_STAGES)
    setHasChanges(JSON.stringify(DEFAULT_STAGES) !== JSON.stringify(originalStages))
    setSaveStatus('idle')
  }

  const activeStages = stages.filter(s => s.isActive).length
  const automatedStages = stages.filter(s => (s as { automations?: { emailFeedback?: boolean; whatsappNotification?: boolean } }).automations?.emailFeedback || (s as { automations?: { emailFeedback?: boolean; whatsappNotification?: boolean } }).automations?.whatsappNotification).length

  if (isLoading) {
    return (
      <div aria-live="polite" aria-busy={isLoading} className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary mx-auto mb-4" />
          <p className="text-sm lia-text-500">Carregando jornada de recrutamento...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Workflow className="w-7 h-7 lia-text-600 dark:text-lia-text-tertiary" />
            <h1
              className="text-2xl font-semibold lia-text-800 dark:text-lia-text-primary"
              
            >
              Jornada de Recrutamento
            </h1>
            {isEditMode && hasChanges && (
              <Badge variant="outline" className="bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30">
                Alterações não salvas
              </Badge>
            )}
          </div>
          <p className="text-sm lia-text-500">
            {isEditMode 
              ? "Arraste para reordenar, ative automações e personalize cada etapa."
              : "Visualize as etapas configuradas do seu processo seletivo."
            }
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {isEditMode ? (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleResetToDefault}
                className="lia-text-600"
                disabled={isSaving}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Resetar padrão
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancelEdit}
                className="lia-text-600"
                disabled={isSaving}
              >
                <X className="w-4 h-4 mr-2" />
                Cancelar
              </Button>
              
              <Button
                size="sm"
                onClick={handleSave}
                disabled={!hasChanges || isSaving}
                className="text-white"
                style={{backgroundColor: hasChanges ? 'var(--gray-950)' : 'var(--gray-200)'}}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                    Salvando...
                  </>
                ) : saveStatus === 'success' ? (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Salvo!
                  </>
                ) : saveStatus === 'error' ? (
                  <>
                    <AlertCircle className="w-4 h-4 mr-2" />
                    Erro ao salvar
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Salvar
                  </>
                )}
              </Button>
            </>
          ) : (
            <Button
              size="sm"
              onClick={handleStartEdit}
              className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
            >
              <Pencil className="w-4 h-4 mr-2" />
              Editar
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <Card className="border border-lia-border-subtle">
            <CardContent className="p-6">
              <RecruitmentJourneyConfig
                stages={stages}
                onChange={handleStagesChange}
                isEditMode={isEditMode}
                hideHeader={true}
              />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="border border-lia-border-subtle">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium lia-text-800 dark:text-lia-text-primary flex items-center gap-2">
                <Info className="w-4 h-4" />
                Resumo do Pipeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-xs lia-text-500">Total de etapas</span>
                <span className="text-sm font-semibold lia-text-800">{stages.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs lia-text-500">Etapas ativas</span>
                <span className="text-sm font-semibold text-status-success">{activeStages}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs lia-text-500">Com automação</span>
                <span className="text-sm font-semibold lia-text-900 dark:lia-text-50">{automatedStages}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border border-lia-border-default dark:border-lia-border-default bg-gray-50 dark:bg-lia-bg-secondary/50">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Brain className="w-5 h-5 text-wedo-cyan mt-0.5" />
                <div>
                  <p className="text-sm font-medium lia-text-800 mb-1">
                    Dica LIA
                  </p>
                  <p className="text-xs lia-text-600">
                    {isEditMode 
                      ? "Arraste as etapas para reordená-las. Ative Email e WhatsApp para manter candidatos engajados."
                      : "Clique em 'Editar' para personalizar as etapas do seu processo seletivo."
                    }
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border border-lia-border-subtle">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                Automações Disponíveis
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 text-xs lia-text-600">
                <div className="w-2 h-2 rounded-full bg-gray-700 dark:lia-bg-300" />
                Email de feedback automático
              </div>
              <div className="flex items-center gap-2 text-xs lia-text-600">
                <div className="w-2 h-2 rounded-full bg-status-success" />
                Notificação WhatsApp
              </div>
              <p className="text-micro lia-text-400 pt-2 border-t">
                Mais automações em breve: SMS, agendamento, testes automáticos
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
