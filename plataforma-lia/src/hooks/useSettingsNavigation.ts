"use client"

import { useState, useEffect, useCallback } from "react"
import {
  Building, Heart, Network, Map, Link2, Workflow, FileText,
  User, Bell, Shield, Bot, ClipboardList, Star, Cog
} from "lucide-react"

export interface SettingsTab {
  id: string
  name: string
  icon: React.ComponentType<{ className?: string }>
  description: string
  category: string
}

export interface SettingsCategory {
  id: string
  name: string
}

export interface SettingsNavigationState {
  activeTab: string
  sidebarWidth: number
  isResizing: boolean
  tabs: SettingsTab[]
  categories: SettingsCategory[]
}

export interface SettingsNavigationActions {
  setActiveTab: (tab: string) => void
  startResize: (e: React.MouseEvent) => void
}

export function useSettingsNavigation(): { state: SettingsNavigationState; actions: SettingsNavigationActions } {
  const [activeTab, setActiveTab] = useState("preferences")
  const [sidebarWidth, setSidebarWidth] = useState(256)
  const [isResizing, setIsResizing] = useState(false)

  const tabs: SettingsTab[] = [
    {
      id: "institutional",
      name: "Dados Institucionais",
      icon: Building,
      description: "CNPJ, endereço, contatos e redes sociais",
      category: "Empresa"
    },
    {
      id: "culture",
      name: "Cultura & EVP",
      icon: Heart,
      description: "Missão, visão, valores e marca empregadora",
      category: "Empresa"
    },
    {
      id: "structure",
      name: "Estrutura",
      icon: Network,
      description: "Organograma, cargos e hierarquia",
      category: "Empresa"
    },
    {
      id: "journey-mapping",
      name: "Journey Mapping",
      icon: Map,
      description: "Wizard inicial e mapa da jornada de recrutamento",
      category: "JourneyMapping"
    },
    {
      id: "integrations",
      name: "Integrações",
      icon: Link2,
      description: "ATS, Workforce Planning, Job Boards e Comunicação",
      category: "Integracoes"
    },
    {
      id: "recruitment-journey",
      name: "Etapas do Processo",
      icon: Workflow,
      description: "Configurar etapas do funil de recrutamento",
      category: "JornadaRecrutamento"
    },
    {
      id: "communication",
      name: "Templates de Vaga",
      icon: FileText,
      description: "Templates e modelos de descrição de vagas",
      category: "JornadaRecrutamento"
    },
    {
      id: "preferences",
      name: "Preferências",
      icon: User,
      description: "Configurações pessoais e interface",
      category: "Configuracoes"
    },
    {
      id: "notifications",
      name: "Notificações",
      icon: Bell,
      description: "Alertas e comunicações",
      category: "Configuracoes"
    },
    {
      id: "security",
      name: "Segurança",
      icon: Shield,
      description: "Privacidade e acessos",
      category: "Configuracoes"
    },
    {
      id: "lia",
      name: "LIA",
      icon: Bot,
      description: "Assistente de IA e automações",
      category: "Configuracoes"
    },
    {
      id: "assessment",
      name: "Assessment",
      icon: ClipboardList,
      description: "Critérios de avaliação e scoring",
      category: "JornadaRecrutamento"
    },
    {
      id: "nps",
      name: "NPS",
      icon: Star,
      description: "Sistema de feedback e avaliação",
      category: "JornadaRecrutamento"
    },
    {
      id: "admin-wedotalent",
      name: "ADMIN WeDOTalent",
      icon: Cog,
      description: "Gerenciar clientes, tenants e onboarding",
      category: "Admin"
    }
  ]

  const categories: SettingsCategory[] = [
    { id: "Empresa", name: "🏢 Empresa" },
    { id: "JourneyMapping", name: "🗺️ Journey Mapping" },
    { id: "Integracoes", name: "🔗 Integrações" },
    { id: "JornadaRecrutamento", name: "📋 Jornada de Recrutamento" },
    { id: "Configuracoes", name: "⚙️ Configurações" },
    { id: "Admin", name: "🔧 Administração" }
  ]

  useEffect(() => {
    const savedWidth = localStorage.getItem('settings-sidebar-width')
    if (savedWidth !== null) {
      setSidebarWidth(parseInt(savedWidth))
    }
  }, [])

  useEffect(() => {
    localStorage.setItem('settings-sidebar-width', sidebarWidth.toString())
  }, [sidebarWidth])

  const startResize = useCallback((e: React.MouseEvent) => {
    setIsResizing(true)
    e.preventDefault()
  }, [])

  useEffect(() => {
    if (!isResizing) return

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(200, Math.min(400, e.clientX))
      setSidebarWidth(newWidth)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizing])

  return {
    state: { activeTab, sidebarWidth, isResizing, tabs, categories },
    actions: { setActiveTab, startResize }
  }
}
