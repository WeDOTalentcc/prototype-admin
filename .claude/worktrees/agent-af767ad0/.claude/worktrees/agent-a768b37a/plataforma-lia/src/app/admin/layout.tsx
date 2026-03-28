"use client"

import React, { useState, useMemo } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { useAuth } from "@/components/auth-context"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ClientProvider, useClient } from "@/contexts/ClientContext"
import { ClientSelector } from "@/components/admin/ClientSelector"
import {
  Settings,
  Users,
  CreditCard,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Shield,
  Home,
  Zap,
  LogOut,
  Building2,
  Plug,
  Brain,
  FileCode,
  FileText,
  CalendarDays,
  Workflow,
  Mail,
  Eye,
  Cpu,
  LayoutDashboard,
  TrendingUp,
  ScrollText,
  X,
  Award,
  FileCheck,
  Lock,
  AlertTriangle,
  Activity,
  ClipboardList,
  ClipboardCheck,
  Globe,
  UserCheck
} from "lucide-react"

type NavItem = {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

type NavGroup = {
  label: string
  items: NavItem[]
}

const overviewNavigation: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { name: "Dashboard Geral", href: "/admin", icon: LayoutDashboard },
      { name: "Métricas da Plataforma", href: "/admin/metricas-plataforma", icon: TrendingUp },
    ]
  },
  {
    label: "Gestão de Clientes",
    items: [
      { name: "Lista de Clientes", href: "/admin/clientes", icon: Users },
      { name: "Onboarding Clientes", href: "/admin/onboarding-clientes", icon: UserCheck },
    ]
  }
]

const getClientNavigation = (clientId: string): NavGroup[] => [
  {
    label: "Operações do Cliente",
    items: [
      { name: "Visão Geral", href: `/admin/clientes/${clientId}`, icon: Home },
      { name: "Usuários", href: `/admin/clientes/${clientId}/usuarios`, icon: Users },
      { name: "Setup Empresa", href: `/admin/clientes/${clientId}/setup`, icon: Building2 },
      { name: "Jornada de Recrutamento", href: `/admin/clientes/${clientId}/jornada`, icon: Workflow },
      { name: "Planejamento de Contratações", href: `/admin/clientes/${clientId}/workforce`, icon: CalendarDays },
      { name: "Integrações", href: `/admin/clientes/${clientId}/integracoes`, icon: Plug },
      { name: "Automações", href: `/admin/clientes/${clientId}/automacoes`, icon: Zap },
      { name: "Big Five", href: `/admin/clientes/${clientId}/big-five`, icon: Brain },
      { name: "Testes Técnicos", href: `/admin/clientes/${clientId}/testes`, icon: FileCode },
      { name: "Comunicações", href: `/admin/clientes/${clientId}/comunicacoes`, icon: Mail },
    ]
  },
  {
    label: "Faturamento & Métricas",
    items: [
      { name: "Faturamento", href: `/admin/clientes/${clientId}/faturamento`, icon: CreditCard },
      { name: "Consumo de IA", href: `/admin/clientes/${clientId}/consumo-ia`, icon: Cpu },
      { name: "Métricas SaaS", href: `/admin/clientes/${clientId}/metricas`, icon: BarChart3 },
    ]
  },
  {
    label: "Operações & Suporte",
    items: [
      { name: "Observabilidade", href: `/admin/clientes/${clientId}/observabilidade`, icon: Eye },
    ]
  }
]

const globalNavigation: NavGroup[] = [
  {
    label: "Configurações Globais",
    items: [
      { name: "Políticas Globais", href: "/admin/configuracoes/politicas", icon: Shield },
      { name: "Comunicações", href: "/admin/configuracoes/comunicacoes", icon: Mail },
      { name: "Templates de Sistema", href: "/admin/templates", icon: FileText },
      { name: "Configurações do Sistema", href: "/admin/configuracoes", icon: Settings },
      { name: "Auditoria & Logs", href: "/admin/configuracoes/auditoria", icon: ScrollText },
      { name: "SSO Empresarial", href: "/admin/sso", icon: Lock },
    ]
  }
]

const complianceNavigation: NavGroup[] = [
  {
    label: "Compliance & Segurança",
    items: [
      { name: "Dashboard Compliance", href: "/admin/compliance", icon: Shield },
      { name: "Trust Center", href: "/admin/compliance/trust-center", icon: Award },
      { name: "Controles", href: "/admin/compliance/controles", icon: FileCheck },
      { name: "LGPD & Privacidade", href: "/admin/compliance/lgpd", icon: Lock },
      { name: "Gestão de Riscos", href: "/admin/compliance/riscos", icon: AlertTriangle },
      { name: "Monitoramento", href: "/admin/compliance/monitoramento", icon: Activity },
      { name: "Sala de Auditoria", href: "/admin/compliance/auditoria", icon: ClipboardList },
      { name: "Health Check", href: "/admin/compliance/health-check", icon: ClipboardCheck },
      { name: "Saúde dos Agentes", href: "/admin/monitoring/agents", icon: Brain },
    ]
  }
]

function AdminSidebar({ 
  sidebarCollapsed, 
  setSidebarCollapsed,
  onLogout 
}: { 
  sidebarCollapsed: boolean
  setSidebarCollapsed: (v: boolean) => void
  onLogout: () => void
}) {
  const pathname = usePathname()
  const router = useRouter()
  const { selectedClient, clearSelectedClient, clients } = useClient()

  const clientIdFromPath = useMemo(() => {
    const match = pathname.match(/\/admin\/clientes\/([^\/]+)/)
    if (match && match[1] && match[1] !== 'novo') {
      return match[1]
    }
    return null
  }, [pathname])

  const activeClient = useMemo(() => {
    if (selectedClient) return selectedClient
    if (clientIdFromPath) {
      const found = clients.find(c => c.id === clientIdFromPath)
      if (found) return found
      return { id: clientIdFromPath, name: 'Cliente', status: 'active' }
    }
    return null
  }, [selectedClient, clientIdFromPath, clients])

  const navigationGroups = useMemo(() => {
    if (activeClient) {
      return [
        ...getClientNavigation(activeClient.id),
        ...complianceNavigation,
        ...globalNavigation
      ]
    }
    return [...overviewNavigation, ...complianceNavigation, ...globalNavigation]
  }, [activeClient])

  const handleClearClient = () => {
    clearSelectedClient()
    router.push('/admin/clientes')
  }

  const isItemActive = (href: string) => {
    if (href === "/admin") {
      return pathname === "/admin"
    }
    return pathname === href || pathname.startsWith(href + "/")
  }

  return (
    <aside
      className={cn(
        "flex flex-col border-r transition-all duration-300",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
      style={{ borderColor: 'var(--eleven-border-subtle)', backgroundColor: 'var(--eleven-bg-card)' }}
    >
      <div className="flex items-center justify-between h-16 px-4 border-b" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-gray-900 dark:text-gray-50" />
            <span className="font-semibold text-lg" style={{ color: 'var(--eleven-text-primary)' }}>
              WedoTalent Admin
            </span>
          </div>
        )}
        {sidebarCollapsed && <Shield className="w-5 h-5 text-gray-900 dark:text-gray-50 mx-auto" />}
      </div>

      {activeClient && !sidebarCollapsed && (
        <div 
          className="mx-2 mt-3 p-3 rounded-md border"
          style={{ 
            backgroundColor: 'var(--eleven-bg-secondary)', 
            borderColor: 'var(--eleven-border-subtle)' 
          }}
        >
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Cliente Ativo
              </p>
              <p className="text-sm font-semibold truncate mt-0.5" style={{ color: 'var(--eleven-text-primary)' }}>
                {activeClient.name}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="shrink-0 p-1 h-6 w-6"
              onClick={handleClearClient}
              title="Voltar para visão geral"
            >
              <X className="w-3 h-3" />
            </Button>
          </div>
        </div>
      )}

      <nav className="flex-1 px-2 py-4 space-y-4 overflow-y-auto">
        {navigationGroups.map((group) => (
          <div key={group.label}>
            {group.label === "Compliance & Segurança" && (
              <div 
                className="my-3 mx-3 border-t" 
                style={{ borderColor: 'var(--eleven-border-subtle)' }}
              />
            )}
            {!sidebarCollapsed && (
              <p 
                className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider"
                style={{ 
                  color: 'var(--eleven-text-tertiary)' 
                }}
              >
                {group.label}
              </p>
            )}
            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = isItemActive(item.href)
                const Icon = item.icon
                const isComplianceItem = item.href.startsWith('/admin/compliance')
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                      isActive
                        ? "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-50 font-semibold"
                        : "hover:bg-gray-100 dark:hover:bg-gray-800"
                    )}
                    style={!isActive ? { color: 'var(--eleven-text-secondary)' } : {}}
                    title={sidebarCollapsed ? item.name : undefined}
                  >
                    <Icon 
                      className={cn(
                        "w-5 h-5 shrink-0",
                        isComplianceItem && item.name === "Dashboard Compliance" && !isActive && "text-gray-600 dark:text-gray-400"
                      )}
                    />
                    {!sidebarCollapsed && (
                      <span className="text-sm font-medium">{item.name}</span>
                    )}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="p-2 border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="w-full justify-center"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4 mr-2" />
              Recolher
            </>
          )}
        </Button>
      </div>

      <div className="p-4 border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
        {!sidebarCollapsed ? (
          <div className="flex items-center gap-3">
            <Avatar className="w-8 h-8">
              <AvatarImage src="https://randomuser.me/api/portraits/men/32.jpg" />
              <AvatarFallback className="bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 text-xs">AD</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: 'var(--eleven-text-primary)' }}>
                Admin WedoTalent
              </p>
              <p className="text-xs truncate" style={{ color: 'var(--eleven-text-tertiary)' }}>
                admin@wedotalent.com
              </p>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              className="shrink-0 p-1"
              onClick={onLogout}
              title="Sair"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        ) : (
          <Avatar className="w-8 h-8 mx-auto">
            <AvatarImage src="https://randomuser.me/api/portraits/men/32.jpg" />
            <AvatarFallback className="bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 text-xs">AD</AvatarFallback>
          </Avatar>
        )}
      </div>
    </aside>
  )
}

function AdminLayoutContent({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { logout } = useAuth()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  return (
    <div className="flex h-screen" style={{ backgroundColor: 'var(--eleven-bg-main)' }}>
      <AdminSidebar 
        sidebarCollapsed={sidebarCollapsed}
        setSidebarCollapsed={setSidebarCollapsed}
        onLogout={handleLogout}
      />

      <main className="flex-1 flex flex-col overflow-hidden">
        <header 
          className="flex items-center justify-between h-16 px-6 border-b shrink-0"
          style={{ 
            borderColor: 'var(--eleven-border-subtle)', 
            backgroundColor: 'var(--eleven-bg-card)' 
          }}
        >
          <div className="flex items-center gap-4">
            <ClientSelector />
          </div>
          <div className="flex items-center gap-2">
            <span 
              className="text-sm"
              style={{ color: 'var(--eleven-text-tertiary)' }}
            >
              Painel Administrativo
            </span>
          </div>
        </header>
        
        <div className="flex-1 overflow-y-auto">
          <div className="h-full">
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClientProvider>
      <AdminLayoutContent>{children}</AdminLayoutContent>
    </ClientProvider>
  )
}
