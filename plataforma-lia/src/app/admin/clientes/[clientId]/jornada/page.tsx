"use client"

import React, { use, useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Workflow,
  ArrowRight,
  CheckCircle2,
  Clock,
  ExternalLink,
  Bell,
  Loader2,
  RefreshCw,
  AlertCircle
} from "lucide-react"
import Link from "next/link"

interface RecruitmentStage {
  id: string
  name: string
  description?: string
  color: string
  isActive: boolean
  order: number
  automations?: {
    emailFeedback?: boolean
    whatsappNotification?: boolean
  }
}

const DEFAULT_STAGES: RecruitmentStage[] = [
  { id: 'applied', name: 'Candidatura', color: 'var(--gray-400)', isActive: true, order: 1 },
  { id: 'screening', name: 'Triagem', isActive: true, order: 2 },
  { id: 'interview', name: 'Entrevista', color: 'var(--status-warning)', isActive: true, order: 3 },
  { id: 'technical', name: 'Avaliação Técnica', color: 'var(--wedo-purple)', isActive: true, order: 4 },
  { id: 'offer', name: 'Proposta', color: 'var(--status-success)', isActive: true, order: 5 },
  { id: 'hired', name: 'Contratado', color: 'var(--status-success)', isActive: true, order: 6 }
]

export default function ClientJornadaPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [stages, setStages] = useState<RecruitmentStage[]>(DEFAULT_STAGES)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadStages = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const url = `/api/backend-proxy/recruitment-journey/templates/?company_id=${clientId}`
      const response = await fetch(url, {
        headers: {
          'X-Company-ID': clientId
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.templates && data.templates.length > 0) {
          const template = data.templates[0]
          const stagesData = template.stages_config || template.stages
          if (stagesData && stagesData.length > 0) {
            setStages(stagesData)
          }
        }
      }
    } catch (err) {
      setError('Erro ao carregar jornada de recrutamento')
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    loadStages()
  }, [loadStages])

  const activeStages = stages.filter(s => s.isActive)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin lia-text-600 dark:text-lia-text-tertiary mx-auto mb-4" />
          <p className="text-sm lia-text-400 dark:lia-text-500">
            Carregando jornada...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Workflow className="w-6 h-6 lia-text-600 dark:text-lia-text-tertiary" />
            <h2 
              className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary"
            >
              Jornada de Recrutamento
            </h2>
          </div>
          <p className="text-sm lia-text-400 dark:lia-text-500">
            Pipeline e etapas do processo seletivo
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadStages}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Atualizar
          </Button>
          <Link href="/admin/jornada-recrutamento" target="_blank">
            <Button variant="outline" size="sm">
              <ExternalLink className="w-4 h-4 mr-2" />
              Abrir Editor Global
            </Button>
          </Link>
        </div>
      </div>

      <Card className="border-status-warning/30 bg-status-warning/10/50 dark:border-status-warning/30 dark:bg-status-warning/20">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Bell className="w-5 h-5 text-status-warning mt-0.5" />
            <div>
              <p className="text-sm font-medium text-status-warning dark:text-status-warning">
                Contexto do Cliente: {clientId}
              </p>
              <p className="text-xs text-status-warning dark:text-status-warning mt-1">
                Esta jornada é específica para este cliente.
                Todas as chamadas de API utilizarão o header X-Company-ID: {clientId}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-status-error/30 bg-status-error/10/50 dark:border-status-error/30 dark:bg-status-error/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-status-error" />
              <p className="text-sm text-status-error dark:text-status-error">{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base lia-text-800 dark:text-lia-text-primary">
              Pipeline de Etapas
            </CardTitle>
            <Badge variant="outline">
              {activeStages.length} etapas ativas
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 overflow-x-auto py-4">
            {stages.map((stage, index) => (
              <React.Fragment key={stage.id}>
                <div 
                  className={`flex flex-col items-center gap-2 px-4 py-3 rounded-md border min-w-[120px] ${
                    stage.isActive
                      ? 'bg-white dark:bg-lia-bg-primary'
                      : 'bg-gray-50 dark:bg-lia-bg-secondary opacity-50 border-lia-border-subtle dark:border-lia-border-subtle'
                  }`}
                  style={{borderColor: stage.isActive ? stage.color : undefined}}
                >
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{backgroundColor: stage.color}}
                  />
                  <span 
                    className="text-sm font-medium text-center lia-text-800 dark:text-lia-text-primary"
                  >
                    {stage.name}
                  </span>
                  {stage.isActive ? (
                    <CheckCircle2 className="w-4 h-4 text-status-success" />
                  ) : (
                    <Clock className="w-4 h-4 lia-text-400" />
                  )}
                </div>
                {index < stages.length - 1 && (
                  <ArrowRight className="w-5 h-5 shrink-0 lia-text-400 dark:lia-text-500" />
                )}
              </React.Fragment>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold lia-text-900 dark:lia-text-50">{activeStages.length}</p>
            <p className="text-sm lia-text-400 dark:lia-text-500">
              Etapas Ativas
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-status-success">
              {stages.filter(s => s.automations?.emailFeedback).length}
            </p>
            <p className="text-sm lia-text-400 dark:lia-text-500">
              Com Email Automático
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-wedo-purple">
              {stages.filter(s => s.automations?.whatsappNotification).length}
            </p>
            <p className="text-sm lia-text-400 dark:lia-text-500">
              Com WhatsApp Automático
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
