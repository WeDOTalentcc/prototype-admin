"use client"

import React, { useState, useEffect, useCallback, use } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Building2,
  ChevronRight,
  Home,
  Users,
  Settings,
  MessageSquare,
  Workflow,
  Plug,
  Zap,
  Brain,
  CreditCard,
  BarChart3,
  Loader2,
  AlertCircle,
  RefreshCw,
  Shield,
  CalendarRange
} from "lucide-react"

interface ClientData {
  id: string
  name: string
  trade_name?: string
  logo_url?: string
  status: string
  plan_id?: string
  cnpj?: string
  primary_email?: string
}

const statusConfig: Record<string, { label: string, variant: 'success' | 'warning' | 'destructive' | 'info' | 'default' }> = {
  active: { label: 'Ativo', variant: 'success' },
  trial: { label: 'Trial', variant: 'info' },
  suspended: { label: 'Suspenso', variant: 'warning' },
  churned: { label: 'Churned', variant: 'destructive' },
  pending_setup: { label: 'Pendente Setup', variant: 'default' },
}

const navigationTabs = [
  { name: 'Visão Geral', href: '', icon: Home },
  { name: 'Usuários', href: '/usuarios', icon: Users },
  { name: 'Setup', href: '/setup', icon: Settings },
  { name: 'Comunicações', href: '/comunicacoes', icon: MessageSquare },
  { name: 'Jornada', href: '/jornada', icon: Workflow },
  { name: 'Integrações', href: '/integracoes', icon: Plug },
  { name: 'Automações', href: '/automacoes', icon: Zap },
  { name: 'Workforce', href: '/workforce', icon: CalendarRange },
  { name: 'Big Five', href: '/big-five', icon: Brain },
  { name: 'Faturamento', href: '/faturamento', icon: CreditCard },
  { name: 'Métricas', href: '/metricas', icon: BarChart3 },
  { name: 'Conformidade', href: '/conformidade', icon: Shield },
]

function ClientHeaderSkeleton() {
  return (
    <div className="flex items-center gap-4">
      <Skeleton className="w-14 h-14 rounded-md" />
      <div className="space-y-2">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-32" />
      </div>
    </div>
  )
}

export default function ClientLayout({
  children,
  params
}: {
  children: React.ReactNode
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const pathname = usePathname()
  const [client, setClient] = useState<ClientData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchClient = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}`)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || 'Erro ao carregar cliente')
      }
      
      const data = await response.json()
      setClient(data.data || data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar cliente')
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchClient()
  }, [fetchClient])

  const basePath = `/admin/clientes/${clientId}`

  const isTabActive = (tabHref: string) => {
    const fullPath = basePath + tabHref
    if (tabHref === '') {
      return pathname === basePath
    }
    return pathname.startsWith(fullPath)
  }

  const status = client?.status ? (statusConfig[client.status] || statusConfig.pending_setup) : statusConfig.pending_setup

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--eleven-bg-main)' }}>
      <div 
        className="border-b"
        style={{ 
          backgroundColor: 'var(--eleven-bg-card)',
          borderColor: 'var(--eleven-border-subtle)'
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex items-center gap-2 py-3 text-sm">
            <Link 
              href="/admin"
              className="hover:text-gray-900 dark:hover:text-gray-50 transition-colors"
              style={{ color: 'var(--eleven-text-tertiary)' }}
            >
              Admin
            </Link>
            <ChevronRight className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
            <Link 
              href="/admin/clientes"
              className="hover:text-gray-900 dark:hover:text-gray-50 transition-colors"
              style={{ color: 'var(--eleven-text-tertiary)' }}
            >
              Clientes
            </Link>
            <ChevronRight className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
            <span style={{ color: 'var(--eleven-text-primary)' }}>
              {loading ? '...' : (client?.name || 'Cliente')}
            </span>
          </nav>

          <div className="py-6">
            {loading ? (
              <ClientHeaderSkeleton />
            ) : error ? (
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-md bg-status-error/10 dark:bg-status-error/20 flex items-center justify-center">
                  <AlertCircle className="w-7 h-7 text-status-error" />
                </div>
                <div>
                  <p className="text-sm text-status-error dark:text-status-error">{error}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={fetchClient}
                    className="mt-1 -ml-2"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Tentar novamente
                  </Button>
                </div>
              </div>
            ) : client ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {client.logo_url ? (
                    <img
                      src={client.logo_url}
                      alt={client.name}
                      className="w-14 h-14 rounded-md object-cover border"
                      style={{ borderColor: 'var(--eleven-border-subtle)' }}
                    />
                  ) : (
                    <div 
                      className="w-14 h-14 rounded-md flex items-center justify-center border"
                      style={{ 
                        backgroundColor: 'var(--eleven-bg-main)',
                        borderColor: 'var(--eleven-border-subtle)'
                      }}
                    >
                      <Building2 className="w-7 h-7" style={{ color: 'var(--eleven-text-tertiary)' }} />
                    </div>
                  )}
                  <div>
                    <div className="flex items-center gap-3">
                      <h1 
                        className="text-xl font-semibold"
                        style={{ 
                          color: 'var(--eleven-text-primary)',
                          
                        }}
                      >
                        {client.name}
                      </h1>
                      <Badge variant={status.variant}>{status.label}</Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-1">
                      {client.trade_name && (
                        <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                          {client.trade_name}
                        </span>
                      )}
                      {client.plan_id && (
                        <Badge variant="outline" className="text-xs">
                          {client.plan_id}
                        </Badge>
                      )}
                      {client.primary_email && (
                        <span className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          {client.primary_email}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          <div className="flex items-center gap-1 overflow-x-auto pb-px -mb-px">
            {navigationTabs.map((tab) => {
              const isActive = isTabActive(tab.href)
              const Icon = tab.icon
              return (
                <Link
                  key={tab.href}
                  href={basePath + tab.href}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                    isActive
                      ? "border-gray-900 dark:border-gray-50 text-gray-900 dark:text-gray-50"
                      : "border-transparent hover:border-gray-300 dark:hover:border-gray-600"
                  )}
                  style={!isActive ? { color: 'var(--eleven-text-secondary)' } : {}}
                >
                  <Icon className="w-4 h-4" />
                  {tab.name}
                </Link>
              )
            })}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </div>
    </div>
  )
}
