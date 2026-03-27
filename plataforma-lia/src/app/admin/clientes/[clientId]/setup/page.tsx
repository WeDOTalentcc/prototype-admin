"use client"

import React, { use, useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Settings,
  Building2,
  Gift,
  Heart,
  Users,
  FileText,
  CheckCircle2,
  Clock,
  ExternalLink,
  Bell,
  Loader2
} from "lucide-react"
import Link from "next/link"

interface SetupSection {
  id: string
  title: string
  description: string
  status: string
  progress: number
  updated_at: string | null
}

const SECTION_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'company-profile': Building2,
  'benefits': Gift,
  'culture': Heart,
  'departments': Users,
  'documents': FileText
}

const DEFAULT_SECTIONS: SetupSection[] = [
  {
    id: 'company-profile',
    title: 'Perfil da Empresa',
    description: 'Informações básicas, logo, missão e valores',
    status: 'pending',
    progress: 0,
    updated_at: null
  },
  {
    id: 'benefits',
    title: 'Benefícios',
    description: 'Pacote de benefícios oferecidos',
    status: 'pending',
    progress: 0,
    updated_at: null
  },
  {
    id: 'culture',
    title: 'Cultura & EVP',
    description: 'Proposta de valor ao empregado',
    status: 'pending',
    progress: 0,
    updated_at: null
  },
  {
    id: 'departments',
    title: 'Departamentos',
    description: 'Estrutura organizacional',
    status: 'pending',
    progress: 0,
    updated_at: null
  },
  {
    id: 'documents',
    title: 'Documentos',
    description: 'Templates e documentação padrão',
    status: 'pending',
    progress: 0,
    updated_at: null
  }
]

export default function ClientSetupPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [sections, setSections] = useState<SetupSection[]>(DEFAULT_SECTIONS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSetup() {
      try {
        setLoading(true)
        setError(null)
        const response = await fetch(`/api/backend-proxy/clients/${clientId}/setup`)
        
        if (!response.ok) {
          throw new Error('Falha ao carregar dados do setup')
        }
        
        const data = await response.json()
        if (data.success && data.data?.sections) {
          setSections(data.data.sections)
        }
      } catch (err) {
        console.error('Error fetching setup:', err)
        setError(err instanceof Error ? err.message : 'Erro ao carregar dados')
      } finally {
        setLoading(false)
      }
    }
    
    fetchSetup()
  }, [clientId])

  const overallProgress = sections.length > 0 
    ? Math.round(sections.reduce((acc, s) => acc + s.progress, 0) / sections.length)
    : 0

  const completedSections = sections.filter(s => s.status === 'complete').length

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'complete':
        return <Badge variant="success">Completo</Badge>
      case 'partial':
        return <Badge variant="warning">Parcial</Badge>
      case 'pending':
        return <Badge variant="default">Pendente</Badge>
      default:
        return null
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return <CheckCircle2 className="w-5 h-5 text-status-success" />
      case 'partial':
        return <Clock className="w-5 h-5 text-status-warning" />
      case 'pending':
        return <Clock className="w-5 h-5 text-gray-400" />
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400" />
          <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Carregando setup...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="border-status-error/30 bg-status-error/10/50 dark:border-status-error/30 dark:bg-status-error/20 max-w-md">
          <CardContent className="p-6 text-center">
            <p className="text-sm font-medium text-status-error dark:text-status-error mb-2">
              Erro ao carregar dados
            </p>
            <p className="text-xs text-status-error dark:text-status-error">
              {error}
            </p>
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              Tentar novamente
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Settings className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <h2 
              className="text-lg font-semibold"
              style={{ color: 'var(--eleven-text-primary)' }}
            >
              Setup da Empresa
            </h2>
          </div>
          <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
            Configuração inicial e perfil do cliente
          </p>
        </div>
        <Link href="/admin/setup-empresa" target="_blank">
          <Button variant="outline" size="sm">
            <ExternalLink className="w-4 h-4 mr-2" />
            Abrir Setup Global
          </Button>
        </Link>
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
                Estas configurações são específicas para este cliente.
                Todas as chamadas de API utilizarão o header X-Company-ID: {clientId}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base" style={{ color: 'var(--eleven-text-primary)' }}>
              Progresso Geral do Setup
            </CardTitle>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-50">{overallProgress}%</span>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={overallProgress} className="h-2" />
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
              {completedSections} de {sections.length} seções completas
            </span>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        {sections.map((section) => {
          const Icon = SECTION_ICONS[section.id] || FileText
          return (
            <Card 
              key={section.id}
              className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer"
            >
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center shrink-0">
                    <Icon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 
                        className="font-medium"
                        style={{ color: 'var(--eleven-text-primary)' }}
                      >
                        {section.title}
                      </h3>
                      {getStatusBadge(section.status)}
                    </div>
                    <p 
                      className="text-sm mb-2"
                      style={{ color: 'var(--eleven-text-tertiary)' }}
                    >
                      {section.description}
                    </p>
                    <div className="flex items-center gap-3">
                      <Progress value={section.progress} className="h-1.5 flex-1" />
                      <span className="text-xs tabular-nums" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        {section.progress}%
                      </span>
                    </div>
                  </div>
                  <div className="shrink-0">
                    {getStatusIcon(section.status)}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
