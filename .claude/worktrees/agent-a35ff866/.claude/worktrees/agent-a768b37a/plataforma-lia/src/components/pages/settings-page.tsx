"use client"

import { useState, useEffect, useCallback } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Settings, Bell, Zap, User, Shield, Database, Globe, Bot,
  Mail, MessageSquare, Phone, Calendar, Clock, Target, MessageCircle,
  ChevronRight, Plus, Save, X, RotateCcw, Check,
  Lightbulb, Filter, Heart, Briefcase, Users, BarChart3,
  Volume2, Languages, Palette, Monitor, Moon, Sun,
  Workflow, Upload, Download, Trash2, Edit, Copy,
  Building, Network, ClipboardList, Star, Brain, FileText,
  Timer, ArrowUp, ArrowDown, Send, CheckCircle, UserPlus,
  ExternalLink, Eye, Search, MoreVertical, CreditCard,
  Package, Rocket, Activity, AlertCircle, Link2, Server,
  Wifi, Minus, RefreshCw, GitBranch, ArrowRight, ArrowLeft, XCircle,
  Info, CheckCircle2, MoreHorizontal, Map, Cog, Loader2,
  ChevronDown, Lock
} from "lucide-react"
import { Slack } from "lucide-react"
import { hasModuleAccess } from "@/utils/license-manager"
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import { RealTimeDashboardPage } from "./real-time-dashboard-page"
import {
  SUB_STATUSES,
  REJECTION_REASONS,
  OFFER_DECLINE_REASONS,
  TEST_STATUSES,
  DOCUMENT_STATUSES,
  RECRUITMENT_STAGES
} from "@/lib/recruitment-stages"

interface SettingsTabProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

// Interfaces para o sistema ATS
interface ATSSystem {
  id: string
  name: string
  type: 'sap' | 'workday' | 'bamboohr' | 'greenhouse' | 'custom'
  status: 'connected' | 'connecting' | 'error' | 'disabled'
  description: string
  logo?: string
  lastSync?: string
  totalRecords: number
  syncedRecords: number
  errorCount: number
  features: string[]
  webhookUrl?: string
  apiEndpoint?: string
  version?: string
}

interface SystemField {
  id: string
  name: string
  type: 'string' | 'email' | 'phone' | 'number' | 'date' | 'url' | 'select'
  required: boolean
  description: string
}

interface FieldMapping {
  id: string
  sourceField: string
  targetField: string
  sourceFieldName: string
  targetFieldName: string
  isActive: boolean
  confidence: number
}

// Interfaces para integrações de comunicação
interface CommunicationIntegration {
  id: string
  name: string
  type: 'slack' | 'teams'
  status: 'active' | 'inactive' | 'error'
  icon: any
  color: string
  webhookUrl: string
  channels: string[]
  events: string[]
  lastActivity: string
  messagesCount: number
  errorCount: number
  createdAt: string
  createdBy: string
}

interface NotificationTemplate {
  id: string
  name: string
  event: string
  title: string
  message: string
  mentions: string[]
  active: boolean
  integrations: string[]
}

interface SyncLog {
  id: string
  timestamp: string
  system: string
  type: 'sync' | 'webhook' | 'manual'
  status: 'success' | 'warning' | 'error'
  records: number
  duration: number
  message: string
  details?: string
}

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState("preferences")
  const [hasChanges, setHasChanges] = useState(false)
  const [sidebarWidth, setSidebarWidth] = useState(256) // largura padrão em pixels
  const [isResizing, setIsResizing] = useState(false)

  const tabs = [
    // 🏢 Empresa
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

    // 🗺️ Journey Mapping (NEW)
    {
      id: "journey-mapping",
      name: "Journey Mapping",
      icon: Map,
      description: "Wizard inicial e mapa da jornada de recrutamento",
      category: "JourneyMapping"
    },

    // 🔗 Integrações
    {
      id: "integrations",
      name: "Integrações",
      icon: Link2,
      description: "ATS, Workforce Planning, Job Boards e Comunicação",
      category: "Integracoes"
    },

    // 📋 Jornada de Recrutamento
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

    // ⚙️ Configurações
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

    // Tabs adicionais (mantidos para compatibilidade)
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

  const categories = [
    { id: "Empresa", name: "🏢 Empresa" },
    { id: "JourneyMapping", name: "🗺️ Journey Mapping" },
    { id: "Integracoes", name: "🔗 Integrações" },
    { id: "JornadaRecrutamento", name: "📋 Jornada de Recrutamento" },
    { id: "Configuracoes", name: "⚙️ Configurações" },
    { id: "Admin", name: "🔧 Administração" }
  ]

  const handleSave = () => {
    setHasChanges(false)
    console.log("Configurações salvas!")
  }

  const handleReset = () => {
    setHasChanges(false)
    console.log("Configurações resetadas!")
  }

  // Carregar largura salva do localStorage
  useEffect(() => {
    const savedWidth = localStorage.getItem('settings-sidebar-width')
    if (savedWidth !== null) {
      setSidebarWidth(parseInt(savedWidth))
    }
  }, [])

  // Salvar largura no localStorage
  useEffect(() => {
    localStorage.setItem('settings-sidebar-width', sidebarWidth.toString())
  }, [sidebarWidth])

  // Handlers para redimensionamento
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

  return (
    <div className="space-y-4 settings-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-sm font-semibold text-gray-950 dark:text-gray-50 font-inter">Configurações</h1>
          <p className="text-xs text-gray-800 dark:text-gray-400">
            Configure sua plataforma, empresa e processos de recrutamento
          </p>
        </div>

        {hasChanges && (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleReset}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Descartar
            </Button>
            <Button size="sm" onClick={handleSave}>
              <Save className="w-4 h-4 mr-2" />
              Salvar Alterações
            </Button>
          </div>
        )}
      </div>

      <div className="flex gap-4">
        {/* Sidebar de Tabs - Redimensionável */}
        <div
          className="relative flex-shrink-0 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700"
          style={{ width: `${sidebarWidth}px`, minWidth: '200px', maxWidth: '400px' }}
        >
          <nav className="space-y-4 p-4 h-full overflow-y-auto">
            {categories.map((category) => (
              <div key={category.id}>
                <h3 className="text-xs font-semibold text-gray-800 dark:text-gray-200 uppercase tracking-wider mb-4 font-inter 2xl:text-[11px]">
                  {category.name}
                </h3>
                <div className="space-y-1">
                  {tabs.filter(tab => tab.category === category.id).map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-3 py-3 rounded-md text-left transition-colors font-open-sans settings-menu-item ${
                        activeTab === tab.id
 ? 'bg-gray-50 dark:bg-gray-800 border border-gray-900 dark:border-gray-200 text-wedo-cyan-dark dark:text-gray-300'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-200'
                      }`}
                      style={{ fontSize: '0.6875rem', lineHeight: '1.125rem', fontWeight: '500' }}
                    >
                      <tab.icon className="w-4 h-4" />
                      <div>
                        <div className="text-sm font-medium 2xl:text-xs">{tab.name}</div>
                        <div className="text-xs text-gray-800 dark:text-gray-400 2xl:text-[11px]">{tab.description}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </nav>

          {/* Resize Handle */}
          <div
            className={cn(
              "absolute top-0 right-0 w-1 h-full cursor-col-resize group z-10",
              "hover:w-1.5 transition-all duration-200",
              isResizing ? "bg-gray-400 w-1.5" : "bg-transparent hover:bg-gray-500"
            )}
            onMouseDown={startResize}
            title="Arrastar para redimensionar menu de configurações"
          >
            {/* Indicador visual mais sutil */}
            <div className="absolute inset-y-0 right-0 w-px bg-gray-200 dark:bg-gray-700 group-hover:bg-blue-300 transition-colors duration-200" />

            {/* Área de hover expandida para facilitar o clique */}
            <div className="absolute top-0 -right-2 w-4 h-full" />
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 min-w-0">
          <div className="space-y-6">
            {activeTab === "preferences" && <PreferencesTab onSettingsChange={setHasChanges} />}
            {activeTab === "lia" && <LIATab onSettingsChange={setHasChanges} />}
            {activeTab === "notifications" && <NotificationsTab onSettingsChange={setHasChanges} />}
            {activeTab === "institutional" && <InstitutionalTab onSettingsChange={setHasChanges} />}
            {activeTab === "culture" && <CultureTab onSettingsChange={setHasChanges} />}
            {activeTab === "structure" && <StructureTab onSettingsChange={setHasChanges} />}
            {activeTab === "communication" && <CommunicationTab onSettingsChange={setHasChanges} />}

            {activeTab === "journey-mapping" && <JourneyMappingTab onSettingsChange={setHasChanges} />}
            {activeTab === "recruitment-journey" && <RecruitmentJourneyTab onSettingsChange={setHasChanges} />}
            {activeTab === "assessment" && <AssessmentTab onSettingsChange={setHasChanges} />}
            {activeTab === "automations" && <AutomationsTab onSettingsChange={setHasChanges} />}
            {activeTab === "nps" && <NPSTab onSettingsChange={setHasChanges} />}
            {activeTab === "integrations" && <IntegrationsTab onSettingsChange={setHasChanges} />}
            {activeTab === "security" && <SecurityTab onSettingsChange={setHasChanges} />}
            {activeTab === "admin-wedotalent" && <AdminWeDOTalentTab onSettingsChange={setHasChanges} />}
          </div>
        </div>
      </div>

      {/* Indicador de largura durante redimensionamento */}
      {isResizing && (
        <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-black dark:bg-white text-white dark:text-black text-sm px-3 py-2 rounded-md z-50 pointer-events-none">
          {sidebarWidth}px
        </div>
      )}
    </div>
  )
}

// Componente de Preferências (mantido como estava)
function PreferencesTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [theme, setTheme] = useState("light")
  const [language, setLanguage] = useState("pt-BR")
  const [timezone, setTimezone] = useState("America/Sao_Paulo")

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Palette className="w-4 h-4" />
            Aparência
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Tema
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: "light", name: "Claro", icon: Sun },
                { id: "dark", name: "Escuro", icon: Moon },
                { id: "system", name: "Sistema", icon: Monitor }
              ].map((themeOption) => (
                <button
                  key={themeOption.id}
                  onClick={() => {
                    setTheme(themeOption.id)
                    onSettingsChange(true)
                  }}
                  className={`p-3 rounded-md border text-center transition-colors ${
                    theme === themeOption.id
 ? 'border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-800 text-wedo-cyan-dark dark:text-gray-300'
                      : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
                  }`}
                >
                  <themeOption.icon className="w-5 h-5 mx-auto mb-1" />
                  <div className="text-sm font-medium">{themeOption.name}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Idioma
            </label>
            <select
              value={language}
              onChange={(e) => {
                setLanguage(e.target.value)
                onSettingsChange(true)
              }}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            >
              <option value="pt-BR">Português (Brasil)</option>
              <option value="en-US">English (US)</option>
              <option value="es-ES">Español</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Globe className="w-4 h-4" />
            Localização
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Fuso Horário
            </label>
            <select
              value={timezone}
              onChange={(e) => {
                setTimezone(e.target.value)
                onSettingsChange(true)
              }}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            >
              <option value="America/Sao_Paulo">São Paulo (UTC-3)</option>
              <option value="America/New_York">New York (UTC-5)</option>
              <option value="Europe/London">London (UTC+0)</option>
            </select>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Configurações da LIA (mantido como estava)
function LIATab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [liaSettings, setLiaSettings] = useState({
    personality: "professional",
    responseStyle: "detailed",
    autoSuggestions: true,
    contextAwareness: true,
    proactiveInsights: true,
    learningMode: true
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Bot className="w-4 h-4" />
            Personalidade da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Estilo de Comunicação
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: "professional", name: "Profissional", desc: "Formal e objetiva" },
                { id: "casual", name: "Casual", desc: "Amigável e descontraída" },
                { id: "concise", name: "Concisa", desc: "Respostas curtas" },
                { id: "detailed", name: "Detalhada", desc: "Explicações completas" }
              ].map((style) => (
                <button
                  key={style.id}
                  onClick={() => {
                    setLiaSettings(prev => ({ ...prev, personality: style.id }))
                    onSettingsChange(true)
                  }}
                  className={`p-3 rounded-md border text-left transition-colors ${
                    liaSettings.personality === style.id
                      ? 'border-gray-900 dark:border-gray-50 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
                  }`}
                >
                  <div className="font-medium text-sm">{style.name}</div>
                  <div className="text-xs text-gray-800 dark:text-gray-400">{style.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { key: "autoSuggestions", label: "Sugestões Automáticas", desc: "LIA sugere ações proativamente" },
              { key: "contextAwareness", label: "Consciência Contextual", desc: "Considera contexto das conversas" },
              { key: "proactiveInsights", label: "Insights Proativos", desc: "Análises e alertas automáticos" },
              { key: "learningMode", label: "Modo Aprendizado", desc: "LIA aprende com suas preferências" }
            ].map((setting) => (
              <div key={setting.key} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <input
                  type="checkbox"
                  checked={liaSettings[setting.key as keyof typeof liaSettings] as boolean}
                  onChange={(e) => {
                    setLiaSettings(prev => ({ ...prev, [setting.key]: e.target.checked }))
                    onSettingsChange(true)
                  }}
                  className="mt-1"
                />
                <div>
                  <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{setting.label}</div>
                  <div className="text-xs text-gray-800 dark:text-gray-400">{setting.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Notificações (mantido como estava)
function NotificationsTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    whatsapp: false,
    slack: true,
    newCandidates: true,
    interviews: true,
    deadlines: true,
    liaInsights: true
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Bell className="w-4 h-4" />
            Canais de Notificação
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: "email", label: "Email", icon: Mail, desc: "Notificações por email" },
            { key: "push", label: "Push", icon: Bell, desc: "Notificações do navegador" },
            { key: "whatsapp", label: "WhatsApp", icon: MessageSquare, desc: "Mensagens WhatsApp" },
            { key: "slack", label: "Slack", icon: MessageSquare, desc: "Mensagens Slack" }
          ].map((channel) => (
            <div key={channel.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="flex items-center gap-3">
                <channel.icon className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                <div>
                  <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{channel.label}</div>
                  <div className="text-xs text-gray-800 dark:text-gray-400">{channel.desc}</div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={notifications[channel.key as keyof typeof notifications] as boolean}
                onChange={(e) => {
                  setNotifications(prev => ({ ...prev, [channel.key]: e.target.checked }))
                  onSettingsChange(true)
                }}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tipos de Notificação</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: "newCandidates", label: "Novos Candidatos", desc: "Quando novos candidatos se inscrevem" },
            { key: "interviews", label: "Entrevistas", desc: "Lembretes e confirmações de entrevistas" },
            { key: "deadlines", label: "Prazos", desc: "Deadlines de feedback e processos" },
            { key: "liaInsights", label: "Insights da LIA", desc: "Análises e sugestões da IA" }
          ].map((type) => (
            <div key={type.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div>
                <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{type.label}</div>
                <div className="text-xs text-gray-800 dark:text-gray-400">{type.desc}</div>
              </div>
              <input
                type="checkbox"
                checked={notifications[type.key as keyof typeof notifications] as boolean}
                onChange={(e) => {
                  setNotifications(prev => ({ ...prev, [type.key]: e.target.checked }))
                  onSettingsChange(true)
                }}
              />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Journey Mapping (NOVO)
function JourneyMappingTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [currentStep, setCurrentStep] = useState(1)
  const [wizardData, setWizardData] = useState({
    vagasAbertura: '',
    sistemasUsados: [] as string[],
    etapasProcesso: [] as string[],
    automacoesDesejadas: [] as string[],
    canaisPublicacao: [] as string[],
    canaisComunicacaoCandidatos: ['whatsapp', 'email', 'ligacao'] as string[],
    careersPageUrl: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const [blueprintId, setBlueprintId] = useState<string | null>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://7ce0a62c-6426-43d6-8c3c-f9e1dcef099b-00-1d771t3pez3we.picard.replit.dev'

  const submitWizard = async () => {
    setIsSubmitting(true)
    setSubmitError(null)
    
    try {
      let companyId: string | null = null
      try {
        const companyRes = await fetch('/api/backend-proxy/company/profile')
        if (companyRes.ok) {
          const companyData = await companyRes.json()
          companyId = companyData?.id || null
        }
      } catch (e) {
        console.warn('Could not fetch company profile:', e)
      }
      
      if (!companyId) {
        throw new Error('Não foi possível identificar a empresa. Por favor, configure o perfil da empresa primeiro.')
      }
      
      const payload = {
        company_id: companyId,
        vagas_abertura: wizardData.vagasAbertura || 'requisicao_formal',
        sistemas_usados: wizardData.sistemasUsados,
        etapas_processo: wizardData.etapasProcesso,
        automacoes_desejadas: wizardData.automacoesDesejadas,
        canais_publicacao: wizardData.canaisPublicacao,
        canais_comunicacao_candidatos: wizardData.canaisComunicacaoCandidatos,
        careers_page_url: wizardData.careersPageUrl || null
      }

      const response = await fetch(`${API_BASE}/api/v1/journey-mapping/wizard/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Erro ao salvar configuração')
      }

      const result = await response.json()
      setBlueprintId(result.id)
      setSubmitSuccess(true)
      onSettingsChange(false) // Reset dirty state
      
      console.log('Journey Mapping saved:', result)
    } catch (error) {
      console.error('Error saving journey mapping:', error)
      setSubmitError(error instanceof Error ? error.message : 'Erro desconhecido')
    } finally {
      setIsSubmitting(false)
    }
  }

  const steps = [
    { id: 1, title: 'Abertura de Vagas', description: 'Como as vagas são abertas?' },
    { id: 2, title: 'Sistemas', description: 'Quais sistemas vocês usam?' },
    { id: 3, title: 'Etapas', description: 'Etapas do processo' },
    { id: 4, title: 'Automações', description: 'Automações desejadas' },
    { id: 5, title: 'Canais', description: 'Onde publicar vagas' }
  ]

  const sistemasDisponiveis = [
    { id: 'gupy', name: 'Gupy', category: 'ATS' },
    { id: 'pandape', name: 'Pandapé', category: 'ATS' },
    { id: 'stackone', name: 'StackOne', category: 'ATS' },
    { id: 'greenhouse', name: 'Greenhouse', category: 'ATS' },
    { id: 'workday', name: 'Workday', category: 'Workforce Planning' },
    { id: 'sap_sf', name: 'SAP SuccessFactors', category: 'Workforce Planning' },
    { id: 'senior', name: 'Senior Sistemas', category: 'HRIS/Folha' },
    { id: 'totvs', name: 'TOTVS RM', category: 'HRIS/Folha' },
    { id: 'adp', name: 'ADP', category: 'HRIS/Folha' },
    { id: 'hackerrank', name: 'HackerRank', category: 'Avaliação Técnica' },
    { id: 'codility', name: 'Codility', category: 'Avaliação Técnica' },
    { id: 'mindsight', name: 'Mindsight', category: 'Assessment' },
    { id: 'docusign', name: 'DocuSign', category: 'Assinatura Digital' },
    { id: 'clicksign', name: 'Clicksign', category: 'Assinatura Digital' },
    { id: 'slack', name: 'Slack', category: 'Comunicação' },
    { id: 'teams', name: 'Microsoft Teams', category: 'Comunicação' }
  ]

  const canaisDisponiveis = [
    { id: 'linkedin_jobs', name: 'LinkedIn Jobs', desc: 'Publicação direta no LinkedIn' },
    { id: 'indeed', name: 'Indeed', desc: 'Job board internacional' },
    { id: 'glassdoor', name: 'Glassdoor', desc: 'Vagas e avaliações da empresa' },
    { id: 'catho', name: 'Catho', desc: 'Job board brasileiro' },
    { id: 'infojobs', name: 'InfoJobs', desc: 'Job board brasileiro' },
    { id: 'site_proprio', name: 'Site Próprio', desc: 'Página de carreiras da empresa' },
    { id: 'universidades', name: 'Universidades', desc: 'Portais acadêmicos' },
    { id: 'redes_sociais', name: 'Redes Sociais', desc: 'Instagram, Facebook, etc.' }
  ]

  const etapasDisponiveis = [
    'Triagem de CVs',
    'Entrevista Inicial',
    'Teste Técnico',
    'Entrevista Técnica',
    'Entrevista com Gestor',
    'Assessment Cultural',
    'Proposta',
    'Onboarding'
  ]

  const automacoesDisponiveis = [
    { id: 'auto-screening', name: 'Triagem Automática', desc: 'Filtrar candidatos automaticamente por critérios' },
    { id: 'auto-schedule', name: 'Agendamento Automático', desc: 'Agendar entrevistas automaticamente' },
    { id: 'auto-notify', name: 'Notificações Automáticas', desc: 'Enviar emails e alertas automaticamente' },
    { id: 'auto-feedback', name: 'Coleta de Feedback', desc: 'Solicitar feedback de entrevistadores' },
    { id: 'auto-offer', name: 'Geração de Proposta', desc: 'Criar propostas automaticamente' },
    { id: 'auto-report', name: 'Relatórios Automáticos', desc: 'Gerar relatórios de métricas' }
  ]

  const canaisComunicacaoCandidatosDisponiveis = [
    { id: 'whatsapp', name: 'WhatsApp', desc: 'Mensagens via WhatsApp Business', icon: 'MessageSquare', essential: true },
    { id: 'email', name: 'Email', desc: 'Comunicação por email corporativo', icon: 'Mail', essential: true },
    { id: 'ligacao', name: 'Ligação', desc: 'Ligações telefônicas', icon: 'Phone', essential: true },
    { id: 'sms', name: 'SMS', desc: 'Mensagens de texto SMS', icon: 'MessageCircle', essential: false }
  ]

  const toggleSistema = (sistemaId: string) => {
    setWizardData(prev => ({
      ...prev,
      sistemasUsados: prev.sistemasUsados.includes(sistemaId)
        ? prev.sistemasUsados.filter(s => s !== sistemaId)
        : [...prev.sistemasUsados, sistemaId]
    }))
    onSettingsChange(true)
  }

  const toggleEtapa = (etapa: string) => {
    setWizardData(prev => ({
      ...prev,
      etapasProcesso: prev.etapasProcesso.includes(etapa)
        ? prev.etapasProcesso.filter(e => e !== etapa)
        : [...prev.etapasProcesso, etapa]
    }))
    onSettingsChange(true)
  }

  const toggleAutomacao = (automacaoId: string) => {
    setWizardData(prev => ({
      ...prev,
      automacoesDesejadas: prev.automacoesDesejadas.includes(automacaoId)
        ? prev.automacoesDesejadas.filter(a => a !== automacaoId)
        : [...prev.automacoesDesejadas, automacaoId]
    }))
    onSettingsChange(true)
  }

  const toggleCanal = (canalId: string) => {
    setWizardData(prev => ({
      ...prev,
      canaisPublicacao: prev.canaisPublicacao.includes(canalId)
        ? prev.canaisPublicacao.filter(c => c !== canalId)
        : [...prev.canaisPublicacao, canalId]
    }))
    onSettingsChange(true)
  }

  const toggleCanalComunicacaoCandidato = (canalId: string) => {
    setWizardData(prev => ({
      ...prev,
      canaisComunicacaoCandidatos: prev.canaisComunicacaoCandidatos.includes(canalId)
        ? prev.canaisComunicacaoCandidatos.filter(c => c !== canalId)
        : [...prev.canaisComunicacaoCandidatos, canalId]
    }))
    onSettingsChange(true)
  }

  const essentialChannelsRemoved = canaisComunicacaoCandidatosDisponiveis
    .filter(c => c.essential)
    .some(c => !wizardData.canaisComunicacaoCandidatos.includes(c.id))

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="border-l-4 border-l-gray-300">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-xl font-medium">
            <Map className="w-5 h-5 text-gray-700" />
            Journey Mapping
          </CardTitle>
          <p className="text-sm text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
            Configure o mapa da jornada de recrutamento da sua empresa através do wizard interativo.
          </p>
        </CardHeader>
      </Card>

      {/* Wizard Steps Indicator */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-8">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <button
                  onClick={() => setCurrentStep(step.id)}
                  className={`flex flex-col items-center transition-all ${
                    currentStep === step.id
                      ? 'text-gray-600 dark:text-gray-400'
                      : currentStep > step.id
                      ? 'text-green-500'
                      : 'text-gray-500'
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 border-2 transition-all ${
                      currentStep === step.id
                        ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                        : currentStep > step.id
                        ? 'border-green-500 bg-green-500 text-white'
                        : 'border-gray-300 bg-gray-50 dark:bg-gray-800'
                    }`}
                  >
                    {currentStep > step.id ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <span className="font-semibold">{step.id}</span>
                    )}
                  </div>
                  <span className="text-xs font-medium text-center" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    {step.title}
                  </span>
                </button>
                {index < steps.length - 1 && (
                  <div
                    className={`w-16 h-0.5 mx-2 ${
                      currentStep > step.id ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      {currentStep === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Briefcase className="w-5 h-5 text-gray-600" />
              Como as vagas são abertas?
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
              Descreva o fluxo típico de abertura de vagas na sua empresa.
            </p>
            <textarea
              value={wizardData.vagasAbertura}
              onChange={(e) => {
                setWizardData(prev => ({ ...prev, vagasAbertura: e.target.value }))
                onSettingsChange(true)
              }}
              placeholder="Ex: As vagas são abertas pelo gestor da área através de um formulário no sistema interno. Após aprovação do RH e do budget, a vaga é publicada..."
              rows={6}
              className="w-full p-4 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              style={{ fontFamily: "'Open Sans', sans-serif" }}
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              {[
                { label: 'Requisição Formal', desc: 'Aprovação hierárquica necessária' },
                { label: 'Demanda Direta', desc: 'Gestor solicita diretamente ao RH' },
                { label: 'Planejamento Anual', desc: 'Vagas planejadas no workforce' }
              ].map((option) => (
                <button
                  key={option.label}
                  onClick={() => {
                    setWizardData(prev => ({ ...prev, vagasAbertura: option.label + ': ' + option.desc }))
                    onSettingsChange(true)
                  }}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-md hover:border-gray-900 dark:hover:border-gray-50 hover:bg-gray-50 dark:bg-gray-800/50 transition-all text-left"
                >
                  <div className="font-medium text-sm" style={{ fontFamily: "'Open Sans', sans-serif" }}>{option.label}</div>
                  <div className="text-xs text-gray-600 mt-1">{option.desc}</div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {currentStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Database className="w-5 h-5 text-gray-700" />
              Quais sistemas vocês usam?
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-sm text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
              Selecione os sistemas e plataformas que sua empresa utiliza no processo de recrutamento.
            </p>

            {['ATS', 'Workforce Planning', 'HRIS/Folha', 'Avaliação Técnica', 'Assessment', 'Assinatura Digital', 'Comunicação'].map((category) => (
              <div key={category}>
                <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-3" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                  {category}
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {sistemasDisponiveis.filter(s => s.category === category).map((sistema) => (
                    <button
                      key={sistema.id}
                      onClick={() => toggleSistema(sistema.id)}
                      className={`p-3 border rounded-md transition-all ${
                        wizardData.sistemasUsados.includes(sistema.id)
                          ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {wizardData.sistemasUsados.includes(sistema.id) && (
                          <Check className="w-4 h-4" />
                        )}
                        <span className="text-sm font-medium" style={{ fontFamily: "'Open Sans', sans-serif" }}>{sistema.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {currentStep === 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Workflow className="w-5 h-5 text-gray-700" />
              Etapas do processo
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
              Selecione as etapas que fazem parte do seu processo de recrutamento.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {etapasDisponiveis.map((etapa) => (
                <button
                  key={etapa}
                  onClick={() => toggleEtapa(etapa)}
                  className={`p-3 border rounded-md transition-all text-left ${
                    wizardData.etapasProcesso.includes(etapa)
                      ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-5 h-5 rounded border flex items-center justify-center ${
                      wizardData.etapasProcesso.includes(etapa)
                        ? 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 border-gray-900 dark:border-gray-50'
                        : 'border-gray-300'
                    }`}>
                      {wizardData.etapasProcesso.includes(etapa) && <Check className="w-3 h-3" />}
                    </div>
                    <span className="text-sm" style={{ fontFamily: "'Open Sans', sans-serif" }}>{etapa}</span>
                  </div>
                </button>
              ))}
            </div>

            {wizardData.etapasProcesso.length > 0 && (
              <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-md">
                <h4 className="text-sm font-semibold mb-3" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                  Ordem das etapas selecionadas:
                </h4>
                <div className="flex flex-wrap gap-2">
                  {wizardData.etapasProcesso.map((etapa, index) => (
                    <Badge key={etapa} variant="secondary" className="px-3 py-1">
                      {index + 1}. {etapa}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {currentStep === 4 && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Zap className="w-5 h-5 text-gray-700" />
                Automações desejadas
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                Selecione as automações que você gostaria de implementar no seu processo.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {automacoesDisponiveis.map((automacao) => (
                  <button
                    key={automacao.id}
                    onClick={() => toggleAutomacao(automacao.id)}
                    className={`p-4 border rounded-md transition-all text-left ${
                      wizardData.automacoesDesejadas.includes(automacao.id)
                        ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        wizardData.automacoesDesejadas.includes(automacao.id)
                          ? 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 border-gray-900 dark:border-gray-50'
                          : 'border-gray-300'
                      }`}>
                        {wizardData.automacoesDesejadas.includes(automacao.id) && <Check className="w-3 h-3" />}
                      </div>
                      <div>
                        <div className="font-medium text-sm" style={{ fontFamily: "'Open Sans', sans-serif" }}>{automacao.name}</div>
                        <div className="text-xs text-gray-600 mt-1">{automacao.desc}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <MessageSquare className="w-5 h-5 text-gray-700" />
                Canais de Comunicação com Candidatos
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                Defina como a LIA poderá se comunicar com os candidatos durante o processo seletivo.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {canaisComunicacaoCandidatosDisponiveis.map((canal) => (
                  <button
                    key={canal.id}
                    onClick={() => toggleCanalComunicacaoCandidato(canal.id)}
                    className={`p-4 border rounded-md transition-all text-left ${
                      wizardData.canaisComunicacaoCandidatos.includes(canal.id)
                        ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex flex-col items-center gap-2 text-center">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        wizardData.canaisComunicacaoCandidatos.includes(canal.id)
                          ? 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {canal.id === 'whatsapp' && <MessageSquare className="w-5 h-5" />}
                        {canal.id === 'email' && <Mail className="w-5 h-5" />}
                        {canal.id === 'ligacao' && <Phone className="w-5 h-5" />}
                        {canal.id === 'sms' && <MessageCircle className="w-5 h-5" />}
                      </div>
                      <div>
                        <div className="font-medium text-sm" style={{ fontFamily: "'Open Sans', sans-serif" }}>{canal.name}</div>
                        {canal.essential && (
                          <span className="text-[10px] text-gray-600 dark:text-gray-400 font-medium">Recomendado</span>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {essentialChannelsRemoved && (
                <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-md">
                  <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-amber-800" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                      Atenção: Canais essenciais desativados
                    </p>
                    <p className="text-xs text-amber-700 mt-1" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                      Limitar os canais de comunicação pode comprometer a velocidade e eficiência do processo seletivo, 
                      reduzindo as chances de contato rápido com os melhores candidatos.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {currentStep === 5 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Globe className="w-5 h-5 text-gray-700" />
              Canais de Publicação
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-gray-800 dark:text-gray-200" style={{ fontFamily: "'Open Sans', sans-serif" }}>
              Onde vocês publicam as vagas? Selecione os canais que sua empresa utiliza.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {canaisDisponiveis.map((canal) => (
                <button
                  key={canal.id}
                  onClick={() => toggleCanal(canal.id)}
                  className={`p-4 border rounded-md transition-all text-left ${
                    wizardData.canaisPublicacao.includes(canal.id)
                      ? 'border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      wizardData.canaisPublicacao.includes(canal.id)
                        ? 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 border-gray-900 dark:border-gray-50'
                        : 'border-gray-300'
                    }`}>
                      {wizardData.canaisPublicacao.includes(canal.id) && <Check className="w-3 h-3" />}
                    </div>
                    <div>
                      <div className="font-medium text-sm" style={{ fontFamily: "'Open Sans', sans-serif" }}>{canal.name}</div>
                      <div className="text-xs text-gray-600 mt-1">{canal.desc}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {wizardData.canaisPublicacao.includes('site_proprio') && (
              <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-md">
                <label className="text-sm font-medium" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                  URL da página de carreiras:
                </label>
                <input
                  type="url"
                  value={wizardData.careersPageUrl}
                  onChange={(e) => {
                    setWizardData(prev => ({ ...prev, careersPageUrl: e.target.value }))
                    onSettingsChange(true)
                  }}
                  placeholder="https://suaempresa.com/carreiras"
                  className="w-full mt-2 p-3 border border-gray-300 dark:border-gray-600 rounded-md text-sm"
                  style={{ fontFamily: "'Open Sans', sans-serif" }}
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Success Message */}
      {submitSuccess && (
        <Card className="border-green-500 bg-green-50 dark:bg-green-900/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center">
                <Check className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-green-800 dark:text-green-200">
                  Jornada configurada com sucesso!
                </h3>
                <p className="text-sm text-green-600 dark:text-green-300" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                  Suas configurações foram salvas. LIA está pronta para otimizar seu recrutamento.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Message */}
      {submitError && (
        <Card className="border-red-500 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center">
                <X className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-red-800 dark:text-red-200">
                  Erro ao salvar configuração
                </h3>
                <p className="text-sm text-red-600 dark:text-red-300" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                  {submitError}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => setCurrentStep(prev => Math.max(1, prev - 1))}
          disabled={currentStep === 1 || isSubmitting}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Voltar
        </Button>
        {currentStep < 5 ? (
          <Button
            onClick={() => setCurrentStep(prev => Math.min(5, prev + 1))}
            className="bg-gray-900"
          >
            Próximo
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        ) : (
          <Button
            onClick={submitWizard}
            disabled={isSubmitting || submitSuccess}
            style={{ backgroundColor: isSubmitting ? '#999' : '#374151' }}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : submitSuccess ? (
              <>
                <Check className="w-4 h-4 mr-2" />
                Configuração Salva
              </>
            ) : (
              <>
                <Check className="w-4 h-4 mr-2" />
                Concluir Configuração
              </>
            )}
          </Button>
        )}
      </div>

      {/* Journey Map Preview */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Eye className="w-5 h-5 text-gray-700" />
            Mapa da Jornada
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-6">
            {wizardData.etapasProcesso.length > 0 ? (
              <div className="flex items-center gap-2 overflow-x-auto pb-4">
                {wizardData.etapasProcesso.map((etapa, index) => (
                  <div key={etapa} className="flex items-center">
                    <div className="flex flex-col items-center">
                      <div
                        className="w-32 h-20 rounded-md border-2 flex items-center justify-center p-2 text-center"
                        style={{ backgroundColor: 'white' }}
                      >
                        <span className="text-xs font-medium" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                          {etapa}
                        </span>
                      </div>
                      <span className="text-xs text-gray-600 mt-2">Etapa {index + 1}</span>
                    </div>
                    {index < wizardData.etapasProcesso.length - 1 && (
                      <ArrowRight className="w-6 h-6 mx-2 text-gray-500 flex-shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-600">
                <Map className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                  Selecione as etapas do processo para visualizar o mapa da jornada
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Dados Institucionais Completo
function InstitutionalTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSubTab, setActiveSubTab] = useState<'basic' | 'address' | 'social' | 'segment' | 'branches'>('basic')

  const subTabs = [
    { id: 'basic', name: 'Dados Básicos', icon: Building },
    { id: 'address', name: 'Endereço', icon: Globe },
    { id: 'social', name: 'Redes Sociais', icon: MessageSquare },
    { id: 'segment', name: 'Segmento', icon: Target },
    { id: 'branches', name: 'Filiais', icon: Network }
  ]

  const renderBasicData = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Building className="w-4 h-4" />
            Informações Básicas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Razão Social
              </label>
              <input
                type="text"
                defaultValue="Sodexo do Brasil Comercial S.A."
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Nome Fantasia
              </label>
              <input
                type="text"
                defaultValue="Sodexo Brasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                CNPJ
              </label>
              <input
                type="text"
                defaultValue="12.345.678/0001-90"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Inscrição Estadual
              </label>
              <input
                type="text"
                defaultValue="123.456.789.012"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Data de Fundação
              </label>
              <input
                type="date"
                defaultValue="1966-03-15"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Número de Funcionários
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              >
                <option>1-10 funcionários</option>
                <option>11-50 funcionários</option>
                <option>51-200 funcionários</option>
                <option>201-1000 funcionários</option>
                <option>1001-5000 funcionários</option>
                <option>5000+ funcionários</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Site Institucional
              </label>
              <input
                type="url"
                defaultValue="https://sodexo.com.br"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Email Principal
              </label>
              <input
                type="email"
                defaultValue="contato@sodexo.com.br"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Telefone Principal
              </label>
              <input
                type="tel"
                defaultValue="(11) 3049-6300"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                WhatsApp Corporativo
              </label>
              <input
                type="tel"
                placeholder="(11) 99999-9999"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Descrição da Empresa
            </label>
            <textarea
              rows={4}
              defaultValue="A Sodexo é uma empresa francesa líder mundial em serviços de alimentação e facilities management, presente em 55 países. No Brasil desde 1997, oferece soluções integradas que melhoram a qualidade de vida diária."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Logotipo da Empresa</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md p-6 text-center bg-gray-50 dark:bg-gray-800">
            <Upload className="w-8 h-8 mx-auto mb-2 text-gray-800" />
            <p className="text-sm text-gray-800 dark:text-gray-200 mb-2">
              Faça upload do logotipo da empresa
            </p>
            <p className="text-xs text-gray-800">PNG, JPG ou SVG até 2MB • Tamanho recomendado: 400x400px</p>
            <Button variant="outline" className="mt-3" size="sm">
              Escolher Arquivo
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAddress = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Globe className="w-4 h-4" />
            Endereço da Matriz
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                CEP
              </label>
              <input
                type="text"
                defaultValue="04571-020"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                placeholder="00000-000"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Logradouro
              </label>
              <input
                type="text"
                defaultValue="Rua Dr. Geraldo Campos Moreira"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Número
              </label>
              <input
                type="text"
                defaultValue="375"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Complemento
              </label>
              <input
                type="text"
                placeholder="Andar, sala, bloco..."
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Bairro
              </label>
              <input
                type="text"
                defaultValue="Cidade Monções"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Cidade
              </label>
              <input
                type="text"
                defaultValue="São Paulo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Estado
              </label>
              <select
                defaultValue="SP"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              >
                <option value="">Selecione o estado</option>
                <option value="AC">Acre</option>
                <option value="AL">Alagoas</option>
                <option value="AP">Amapá</option>
                <option value="AM">Amazonas</option>
                <option value="BA">Bahia</option>
                <option value="CE">Ceará</option>
                <option value="DF">Distrito Federal</option>
                <option value="ES">Espírito Santo</option>
                <option value="GO">Goiás</option>
                <option value="MA">Maranhão</option>
                <option value="MT">Mato Grosso</option>
                <option value="MS">Mato Grosso do Sul</option>
                <option value="MG">Minas Gerais</option>
                <option value="PA">Pará</option>
                <option value="PB">Paraíba</option>
                <option value="PR">Paraná</option>
                <option value="PE">Pernambuco</option>
                <option value="PI">Piauí</option>
                <option value="RJ">Rio de Janeiro</option>
                <option value="RN">Rio Grande do Norte</option>
                <option value="RS">Rio Grande do Sul</option>
                <option value="RO">Rondônia</option>
                <option value="RR">Roraima</option>
                <option value="SC">Santa Catarina</option>
                <option value="SP">São Paulo</option>
                <option value="SE">Sergipe</option>
                <option value="TO">Tocantins</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              País
            </label>
            <select
              defaultValue="BR"
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
            >
              <option value="BR">Brasil</option>
              <option value="US">Estados Unidos</option>
              <option value="FR">França</option>
              <option value="DE">Alemanha</option>
              <option value="GB">Reino Unido</option>
            </select>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSocialMedia = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <MessageSquare className="w-4 h-4" />
            Redes Sociais e Canais Digitais
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-pink-500 rounded-md"></div>
                Instagram
              </label>
              <input
                type="url"
                placeholder="https://instagram.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-gray-700 dark:bg-gray-300 rounded-md"></div>
                Facebook
              </label>
              <input
                type="url"
                placeholder="https://facebook.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-wedo-cyan-dark rounded-md"></div>
                LinkedIn
              </label>
              <input
                type="url"
                defaultValue="https://linkedin.com/company/sodexo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-gray-900 dark:bg-gray-50 rounded-md"></div>
                Twitter/X
              </label>
              <input
                type="url"
                placeholder="https://twitter.com/sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-red-600 rounded-md"></div>
                YouTube
              </label>
              <input
                type="url"
                placeholder="https://youtube.com/@sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block flex items-center gap-2">
                <div className="w-5 h-5 bg-black rounded-md"></div>
                TikTok
              </label>
              <input
                type="url"
                placeholder="https://tiktok.com/@sodexobrasil"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3">Outros Canais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                  Blog Corporativo
                </label>
                <input
                  type="url"
                  placeholder="https://blog.sodexo.com.br"
                  onChange={() => onSettingsChange(true)}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                  Portal de Carreiras
                </label>
                <input
                  type="url"
                  placeholder="https://carreiras.sodexo.com.br"
                  onChange={() => onSettingsChange(true)}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSegment = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Target className="w-4 h-4" />
            Segmento e Mercado
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Setor Principal
              </label>
              <select
                defaultValue="servicos"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              >
                <option value="">Selecione o setor</option>
                <option value="servicos">Alimentação e Serviços</option>
                <option value="tecnologia">Tecnologia</option>
                <option value="saude">Saúde</option>
                <option value="educacao">Educação</option>
                <option value="financeiro">Financeiro</option>
                <option value="industria">Indústria</option>
                <option value="varejo">Varejo</option>
                <option value="construcao">Construção</option>
                <option value="energia">Energia</option>
                <option value="agronegocio">Agronegócio</option>
                <option value="telecomunicacoes">Telecomunicações</option>
                <option value="consultoria">Consultoria</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Subsetor
              </label>
              <input
                type="text"
                defaultValue="Facilities Management e Food Services"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                placeholder="Ex: SaaS, E-commerce, Consultoria..."
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Fase da Empresa
              </label>
              <select
                defaultValue="grande"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              >
                <option value="startup">Startup (até 50 funcionários)</option>
                <option value="scaleup">Scaleup (51-500 funcionários)</option>
                <option value="media">Empresa de médio porte (501-5000)</option>
                <option value="grande">Grande empresa (5000+ funcionários)</option>
                <option value="multinacional">Multinacional</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Modelo de Negócio
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              >
                <option value="">Selecione o modelo</option>
                <option value="b2b">B2B (Business to Business)</option>
                <option value="b2c">B2C (Business to Consumer)</option>
                <option value="b2b2c">B2B2C (Business to Business to Consumer)</option>
                <option value="marketplace">Marketplace</option>
                <option value="saas">SaaS (Software as a Service)</option>
                <option value="consultoria">Consultoria/Serviços</option>
                <option value="produto">Produto Físico</option>
                <option value="hibrido">Híbrido</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Faturamento Anual
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              >
                <option value="">Selecione a faixa</option>
                <option value="ate100k">Até R$ 100.000</option>
                <option value="100k500k">R$ 100.001 a R$ 500.000</option>
                <option value="500k2m">R$ 500.001 a R$ 2.000.000</option>
                <option value="2m10m">R$ 2.000.001 a R$ 10.000.000</option>
                <option value="10m50m">R$ 10.000.001 a R$ 50.000.000</option>
                <option value="acima50m">Acima de R$ 50.000.000</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Países de Operação
              </label>
              <input
                type="text"
                defaultValue="Brasil, França, Estados Unidos, Reino Unido, Alemanha, +50 países"
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                placeholder="Ex: Brasil, Argentina, Chile..."
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Principais Produtos/Serviços
            </label>
            <textarea
              rows={3}
              defaultValue="Serviços de alimentação corporativa, gestão de facilities, vouchers e cartões alimentação, benefícios para funcionários, gestão de espaços corporativos."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
              placeholder="Descreva os principais produtos ou serviços oferecidos..."
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderBranches = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Network className="w-4 h-4" />
              Filiais e Unidades
            </div>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Nova Filial
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                id: 1,
                name: "Sede São Paulo",
                cnpj: "12.345.678/0001-90",
                address: "Rua Dr. Geraldo Campos Moreira, 375 - Cidade Monções, São Paulo - SP",
                type: "Matriz",
                manager: "Ana Silva",
                employees: 450,
                status: "Ativa"
              },
              {
                id: 2,
                name: "Filial Rio de Janeiro",
                cnpj: "12.345.678/0002-71",
                address: "Av. Presidente Vargas, 1012 - Centro, Rio de Janeiro - RJ",
                type: "Filial",
                manager: "Carlos Santos",
                employees: 280,
                status: "Ativa"
              },
              {
                id: 3,
                name: "Unidade Belo Horizonte",
                cnpj: "12.345.678/0003-52",
                address: "Rua da Bahia, 1148 - Centro, Belo Horizonte - MG",
                type: "Filial",
                manager: "Maria Costa",
                employees: 150,
                status: "Ativa"
              }
            ].map((branch) => (
              <div key={branch.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-md">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-gray-950 dark:text-gray-50">{branch.name}</h4>
                    <p className="text-sm text-gray-800 dark:text-gray-200">CNPJ: {branch.cnpj}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={branch.type === 'Matriz' ? 'default' : 'secondary'}>
                      {branch.type}
                    </Badge>
                    <Badge variant="outline" className="text-green-600 border-green-200">
                      {branch.status}
                    </Badge>
                    <Button variant="ghost" size="sm">
                      <Edit className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-800 dark:text-gray-200">Endereço:</span>
                    <p className="font-medium text-gray-950 dark:text-gray-50">{branch.address}</p>
                  </div>
                  <div>
                    <span className="text-gray-800 dark:text-gray-200">Gestor:</span>
                    <p className="font-medium text-gray-950 dark:text-gray-50">{branch.manager}</p>
                  </div>
                  <div>
                    <span className="text-gray-800 dark:text-gray-200">Funcionários:</span>
                    <p className="font-medium text-gray-950 dark:text-gray-50">{branch.employees}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Sub Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-1 overflow-x-auto">
            {subTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium whitespace-nowrap transition-colors font-crimson ${
                  activeSubTab === tab.id
 ? 'bg-gray-50 dark:bg-gray-800 text-wedo-cyan-dark dark:text-gray-300'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-200'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.name}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sub Tab Content */}
      {activeSubTab === 'basic' && renderBasicData()}
      {activeSubTab === 'address' && renderAddress()}
      {activeSubTab === 'social' && renderSocialMedia()}
      {activeSubTab === 'segment' && renderSegment()}
      {activeSubTab === 'branches' && renderBranches()}
    </div>
  )
}

// Componente de Cultura (recuperado)
function CultureTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Heart className="w-4 h-4" />
            Identidade Corporativa
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Missão
            </label>
            <textarea
              rows={3}
              defaultValue="Melhorar a qualidade de vida diária de todos os que servimos por meio de serviços de alimentação e facilities únicos e inovadores."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Visão
            </label>
            <textarea
              rows={3}
              defaultValue="Ser a empresa líder mundial em serviços de qualidade de vida, criando valor para todas as partes interessadas."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Propósito Institucional
            </label>
            <textarea
              rows={3}
              defaultValue="Conectar pessoas, lugares e experiências para criar um mundo melhor através de serviços essenciais que melhoram a vida diária."
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Valores da Empresa</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {[
              { value: 'Espírito de Serviço', description: 'Nos concentramos nas necessidades das pessoas que servimos' },
              { value: 'Espírito de Equipe', description: 'Construímos relacionamentos duradouros baseados na confiança' },
              { value: 'Espírito de Progresso', description: 'Inovamos e nos adaptamos para um mundo em mudança' },
              { value: 'Sustentabilidade', description: 'Comprometidos com um planeta mais sustentável' }
            ].map((item, index) => (
              <div key={index} className="p-4 border border-gray-200 dark:border-gray-700 rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50">
                    {item.value}
                  </h4>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Edit className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                <p className="text-xs text-gray-800 dark:text-gray-400">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
          <Button variant="outline" className="gap-2" size="sm">
            <Plus className="w-4 h-4" />
            Adicionar Valor
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Estrutura (recuperado)
function StructureTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Network className="w-4 h-4" />
            Upload de Organograma
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md p-8 text-center bg-gray-50 dark:bg-gray-800">
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-800" />
            <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50 mb-2">
              Faça upload do organograma da empresa
            </h4>
            <p className="text-sm text-gray-800 dark:text-gray-200 mb-4">
              Formatos aceitos: PNG, JPG, PDF, SVG até 10MB
            </p>
            <Button variant="outline">
              Escolher Arquivo
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Estrutura de Cargos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md p-6 text-center mb-4 bg-gray-50 dark:bg-gray-800">
            <FileText className="w-8 h-8 mx-auto mb-2 text-gray-800" />
            <p className="text-sm text-gray-800 dark:text-gray-200 mb-2">
              Upload da planilha de cargos e descrições
            </p>
            <p className="text-xs text-gray-800 mb-3">Excel (.xlsx, .xls) ou CSV até 5MB</p>
            <Button variant="outline" size="sm">
              Upload de Cargos
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Central de Comunicação
function CommunicationTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSubTab, setActiveSubTab] = useState<'templates' | 'notifications' | 'whatsapp' | 'sms' | 'automation'>('templates')
  const [templates, setTemplates] = useState([
    {
      id: 'welcome',
      name: 'Boas-vindas',
      subject: 'Bem-vindo(a) ao processo seletivo da {empresa}',
      type: 'email',
      status: 'ativo',
      trigger: 'Novo candidato',
      lastModified: '2024-01-15'
    },
    {
      id: 'interview-invite',
      name: 'Convite para Entrevista',
      subject: 'Convite para entrevista - {vaga}',
      type: 'email',
      status: 'ativo',
      trigger: 'Agendamento de entrevista',
      lastModified: '2024-01-18'
    },
    {
      id: 'rejection',
      name: 'Feedback Negativo',
      subject: 'Agradecemos seu interesse - {vaga}',
      type: 'email',
      status: 'ativo',
      trigger: 'Candidato rejeitado',
      lastModified: '2024-01-10'
    },
    {
      id: 'offer',
      name: 'Proposta de Emprego',
      subject: 'Proposta de emprego - {vaga}',
      type: 'email',
      status: 'ativo',
      trigger: 'Aprovação final',
      lastModified: '2024-01-20'
    }
  ])

  const subTabs = [
    { id: 'templates', name: 'Templates de Email', icon: Mail },
    { id: 'notifications', name: 'Notificações', icon: Bell },
    { id: 'whatsapp', name: 'WhatsApp Business', icon: MessageSquare },
    { id: 'sms', name: 'SMS', icon: Phone },
    { id: 'automation', name: 'Automação', icon: Zap }
  ]

  const renderTemplates = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4" />
              Templates de Email
            </div>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Novo Template
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {templates.map((template) => (
              <div key={template.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-md">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-md flex items-center justify-center">
                    <Mail className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-950 dark:text-gray-50">{template.name}</h4>
                    <p className="text-sm text-gray-800 dark:text-gray-200">{template.subject}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-800">
                      <span>Trigger: {template.trigger}</span>
                      <span>•</span>
                      <span>Modificado em {new Date(template.lastModified).toLocaleDateString('pt-BR')}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={template.status === 'ativo' ? 'default' : 'secondary'}>
                    {template.status}
                  </Badge>
                  <Button variant="outline" size="sm">
                    <Edit className="w-4 h-4 mr-2" />
                    Editar
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Configurações Gerais de Email</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                Nome do Remetente
              </label>
              <input
                type="text"
                defaultValue="Equipe de Recrutamento - Sodexo"
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                Email de Resposta
              </label>
              <input
                type="email"
                defaultValue="recrutamento@sodexo.com.br"
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
              Assinatura Padrão
            </label>
            <textarea
              rows={4}
              defaultValue="Atenciosamente,&#10;Equipe de Recrutamento&#10;Sodexo Brasil&#10;www.sodexo.com.br"
              onChange={() => onSettingsChange(true)}
              className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderNotifications = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Configurações de Notificação
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: "newCandidate", label: "Novo candidato se inscreveu", desc: "Notificar recrutadores sobre novas inscrições" },
            { key: "interviewScheduled", label: "Entrevista agendada", desc: "Lembrete para recrutador e candidato" },
            { key: "interviewReminder", label: "Lembrete de entrevista", desc: "Enviar 24h antes da entrevista" },
            { key: "feedbackDue", label: "Prazo de feedback", desc: "Lembrar de dar feedback após entrevistas" },
            { key: "candidateReply", label: "Resposta do candidato", desc: "Quando candidato responde emails" },
            { key: "processDeadline", label: "Prazo do processo", desc: "Alertar sobre prazos de processos seletivos" }
          ].map((notification) => (
            <div key={notification.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div>
                <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{notification.label}</div>
                <div className="text-xs text-gray-800 dark:text-gray-400">{notification.desc}</div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <input type="checkbox" defaultChecked className="text-gray-600 dark:text-gray-400" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs text-gray-800">Email</span>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" className="text-gray-600 dark:text-gray-400" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs text-gray-800">Push</span>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" className="text-gray-600 dark:text-gray-400" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs text-gray-800">WhatsApp</span>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )

  const renderWhatsApp = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            WhatsApp Business
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="font-medium text-green-900 dark:text-green-100">WhatsApp Business Conectado</span>
            </div>
            <p className="text-sm text-green-800 dark:text-green-200">
              Número: +55 (11) 99999-9999
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                Mensagem de Boas-vindas
              </label>
              <textarea
                rows={3}
                defaultValue="Olá! 👋 Obrigado pelo interesse em nossa vaga. Em breve entraremos em contato."
                onChange={() => onSettingsChange(true)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                Horário de Atendimento
              </label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm w-16">Segunda:</span>
                  <input type="time" defaultValue="08:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs">às</span>
                  <input type="time" defaultValue="18:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm w-16">Sexta:</span>
                  <input type="time" defaultValue="08:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                  <span className="text-xs">às</span>
                  <input type="time" defaultValue="17:00" className="text-xs" onChange={() => onSettingsChange(true)} />
                </div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-3">Templates de Mensagem</h4>
            <div className="space-y-2">
              {[
                { name: "Convite para entrevista", message: "Parabéns! Você foi selecionado(a) para a próxima etapa do processo seletivo para a vaga de {vaga}. 🎉" },
                { name: "Lembrete de entrevista", message: "Olá! Lembrando que sua entrevista está agendada para amanhã às {horario}. 📅" },
                { name: "Solicitação de documentos", message: "Para prosseguir com seu processo, precisamos que envie os seguintes documentos: {documentos}" }
              ].map((template, index) => (
                <div key={index} className="p-3 border border-gray-200 dark:border-gray-700 rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{template.name}</span>
                    <Button variant="outline" size="sm">Editar</Button>
                  </div>
                  <p className="text-xs text-gray-800 dark:text-gray-400">{template.message}</p>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSMS = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="w-4 h-4" />
            SMS
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Phone className="w-12 h-12 text-gray-800 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">SMS em Desenvolvimento</h3>
            <p className="text-gray-800 dark:text-gray-200 mb-4">
              Funcionalidade de SMS será disponibilizada em breve
            </p>
            <Button variant="outline">
              Solicitar Acesso Antecipado
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAutomation = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Automação de Comunicação
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            {[
              {
                name: "Resposta Automática",
                description: "Enviar email de confirmação ao receber nova inscrição",
                status: "ativo",
                trigger: "Novo candidato"
              },
              {
                name: "Follow-up de Entrevista",
                description: "Solicitar feedback do candidato 2 dias após entrevista",
                status: "ativo",
                trigger: "2 dias após entrevista"
              },
              {
                name: "Lembrete de Prazo",
                description: "Alertar recrutadores sobre feedbacks pendentes",
                status: "pausado",
                trigger: "24h após prazo"
              },
              {
                name: "Reengajamento",
                description: "Contatar candidatos inativos há mais de 30 dias",
                status: "ativo",
                trigger: "30 dias de inatividade"
              }
            ].map((automation, index) => (
              <div key={index} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-md">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                    automation.status === 'ativo' ? 'bg-green-100 dark:bg-green-900/20' : 'bg-gray-100 dark:bg-gray-800'
                  }`}>
                    <Zap className={`w-5 h-5 ${
                      automation.status === 'ativo' ? 'text-green-600' : 'text-gray-800'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-950 dark:text-gray-50">{automation.name}</h4>
                    <p className="text-sm text-gray-800 dark:text-gray-200">{automation.description}</p>
                    <p className="text-xs text-gray-800">Trigger: {automation.trigger}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={automation.status === 'ativo' ? 'default' : 'secondary'}>
                    {automation.status}
                  </Badge>
                  <Button variant="outline" size="sm">
                    Configurar
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <Button className="w-full gap-2" variant="outline">
            <Plus className="w-4 h-4" />
            Nova Automação
          </Button>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Sub Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-1 overflow-x-auto">
            {subTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium whitespace-nowrap transition-colors font-crimson ${
                  activeSubTab === tab.id
 ? 'bg-gray-50 dark:bg-gray-800 text-wedo-cyan-dark dark:text-gray-300'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-200'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.name}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sub Tab Content */}
      {activeSubTab === 'templates' && renderTemplates()}
      {activeSubTab === 'notifications' && renderNotifications()}
      {activeSubTab === 'whatsapp' && renderWhatsApp()}
      {activeSubTab === 'sms' && renderSMS()}
      {activeSubTab === 'automation' && renderAutomation()}
    </div>
  )
}



function RecruitmentJourneyTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSubTab, setActiveSubTab] = useState("pipeline")
  const [stages, setStages] = useState(() => 
    RECRUITMENT_STAGES.filter(s => s.name !== 'standby' && s.name !== 'interview_manager2').map((stage, index) => ({
      ...stage,
      isActive: true,
      order: index + 1,
    }))
  )
  const [isEditing, setIsEditing] = useState(false)

  const subTabs = [
    { id: "pipeline", label: "Pipeline", icon: Workflow },
    { id: "eligibility", label: "Perguntas de Elegibilidade", icon: FileText },
    { id: "data-request", label: "Solicitação de Dados", icon: ClipboardList },
    { id: "lia-instructions", label: "Instruções LIA", icon: Brain },
  ]

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'system': return <Lock className="w-3.5 h-3.5 text-gray-400" />
      case 'default': return <Target className="w-3.5 h-3.5 text-gray-400" />
      case 'custom': return <Settings className="w-3.5 h-3.5 text-gray-400" />
      default: return null
    }
  }

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'system': return 'Sistema'
      case 'default': return 'Padrão'
      case 'custom': return 'Custom'
      default: return ''
    }
  }

  const toggleStageActive = (stageName: string) => {
    setStages(prev => prev.map(s => 
      s.name === stageName ? { ...s, isActive: !s.isActive } : s
    ))
    onSettingsChange(true)
  }

  const moveStage = (fromIndex: number, direction: 'up' | 'down') => {
    const newStages = [...stages]
    const toIndex = direction === 'up' ? fromIndex - 1 : fromIndex + 1
    if (toIndex >= 0 && toIndex < newStages.length) {
      const fromStage = newStages[fromIndex]
      const toStage = newStages[toIndex]
      if (fromStage.stageCategory === 'system' || toStage.stageCategory === 'system') return
      ;[newStages[fromIndex], newStages[toIndex]] = [newStages[toIndex], newStages[fromIndex]]
      newStages.forEach((s, i) => { s.order = i + 1 })
      setStages(newStages)
      onSettingsChange(true)
    }
  }

  const addCustomStage = () => {
    const newStage = {
      name: `custom_${Date.now()}`,
      displayName: 'Nova Etapa',
      stageOrder: stages.length + 1,
      color: '#94A3B8',
      icon: 'plus-circle',
      stageType: 'active' as const,
      isInitial: false,
      isFinal: false,
      stageCategory: 'custom' as const,
      allowedTransitions: [] as string[],
      isActive: true,
      order: stages.length + 1,
    }
    const offerIndex = stages.findIndex(s => s.name === 'offer')
    if (offerIndex !== -1) {
      const newStages = [...stages]
      newStages.splice(offerIndex, 0, newStage)
      newStages.forEach((s, i) => { s.order = i + 1 })
      setStages(newStages)
    } else {
      setStages([...stages, newStage])
    }
    onSettingsChange(true)
  }

  const removeStage = (stageName: string) => {
    const stage = stages.find(s => s.name === stageName)
    if (stage?.stageCategory === 'system') return
    setStages(prev => {
      const filtered = prev.filter(s => s.name !== stageName)
      filtered.forEach((s, i) => { s.order = i + 1 })
      return filtered
    })
    onSettingsChange(true)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-medium font-inter">Recrutamento</CardTitle>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Pipeline e elegibilidade</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50 dark:bg-green-950 gap-1.5">
                <CheckCircle className="w-3 h-3" />
                Sincronizado
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-1 mt-4 border-b border-gray-200 dark:border-gray-700">
            {subTabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px",
                  activeSubTab === tab.id
                    ? "border-gray-900 dark:border-gray-50 text-gray-900 dark:text-gray-50"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                )}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </CardHeader>

        <CardContent>
          {activeSubTab === "pipeline" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50 dark:bg-red-950 gap-1.5 cursor-pointer hover:bg-red-100">
                    <Trash2 className="w-3 h-3" />
                    Deletar Template
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(!isEditing)}
                    className="gap-1.5"
                  >
                    <Edit className="w-3.5 h-3.5" />
                    {isEditing ? 'Concluir' : 'Editar'}
                  </Button>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-50 mb-1">Jornada de Recrutamento</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Visualize as etapas do processo seletivo configuradas.</p>

                <div className="flex items-center gap-6 text-xs text-gray-500 dark:text-gray-400 mb-6 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="flex items-center gap-1.5">
                    <Lock className="w-3.5 h-3.5" />
                    <span><strong>Sistema:</strong> Etapas fixas (Funil, Triagem, Entrevista RH, Contratado, Reprovado)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5" />
                    <span><strong>Padrão:</strong> Editável nome e SLA</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Settings className="w-3.5 h-3.5" />
                    <span><strong>Custom:</strong> Totalmente editável</span>
                  </div>
                </div>

                <div className="space-y-2">
                  {stages.map((stage, index) => (
                    <div
                      key={stage.name}
                      className={cn(
                        "flex items-center gap-4 p-4 border rounded-md transition-all",
                        stage.isActive
                          ? "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
                          : "border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 opacity-60"
                      )}
                    >
                      <div className="flex items-center gap-3 min-w-[40px]">
                        <span className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center text-sm font-medium text-gray-600 dark:text-gray-300">
                          {stage.order}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 flex-1">
                        {getCategoryIcon(stage.stageCategory)}
                        <span className="font-medium text-gray-900 dark:text-gray-50">{stage.displayName}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        {isEditing && stage.stageCategory !== 'system' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => moveStage(index, 'up')}
                              disabled={index === 0}
                              className="h-7 w-7 p-0"
                            >
                              <ArrowUp className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => moveStage(index, 'down')}
                              disabled={index === stages.length - 1}
                              className="h-7 w-7 p-0"
                            >
                              <ArrowDown className="w-3.5 h-3.5" />
                            </Button>
                          </>
                        )}

                        {stage.stageCategory === 'system' ? (
                          <span className="text-xs text-gray-400 flex items-center gap-1">
                            <Lock className="w-3 h-3" />
                          </span>
                        ) : (
                          <button
                            onClick={() => toggleStageActive(stage.name)}
                            className={cn(
                              "flex items-center gap-1 text-xs px-2 py-1 rounded transition-colors",
                              stage.isActive
                                ? "text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950"
                                : "text-green-600 hover:bg-green-50 dark:hover:bg-green-950"
                            )}
                          >
                            {stage.isActive ? (
                              <>
                                <X className="w-3 h-3" />
                                Inativo
                              </>
                            ) : (
                              <>
                                <Check className="w-3 h-3" />
                                Ativar
                              </>
                            )}
                          </button>
                        )}

                        {isEditing && stage.stageCategory === 'custom' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeStage(stage.name)}
                            className="h-7 w-7 p-0 text-red-500 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {isEditing && (
                  <Button
                    variant="outline"
                    onClick={addCustomStage}
                    className="w-full mt-4 gap-2 border-dashed"
                  >
                    <Plus className="w-4 h-4" />
                    Adicionar Etapa Customizada
                  </Button>
                )}
              </div>
            </div>
          )}

          {activeSubTab === "eligibility" && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Configurações de Perguntas de Elegibilidade</p>
            </div>
          )}

          {activeSubTab === "data-request" && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Configurações de Solicitação de Dados</p>
            </div>
          )}

          {activeSubTab === "lia-instructions" && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <Brain className="w-12 h-12 mx-auto mb-3 opacity-30 text-wedo-cyan" />
              <p className="text-sm">Instruções para a LIA</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Assessment (recuperado)
function AssessmentTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <ClipboardList className="w-4 h-4" />
            Critérios de Avaliação
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {[
              { categoria: 'Competências Técnicas', peso: 40, criterios: ['Conhecimento específico', 'Experiência prática'] },
              { categoria: 'Soft Skills', peso: 30, criterios: ['Comunicação', 'Liderança'] },
              { categoria: 'Fit Cultural', peso: 20, criterios: ['Alinhamento com valores', 'Adaptabilidade'] },
              { categoria: 'Potencial de Crescimento', peso: 10, criterios: ['Aprendizado contínuo', 'Ambição'] }
            ].map((item, index) => (
              <div key={index} className="p-4 border border-gray-200 dark:border-gray-700 rounded-md">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50">
                    {item.categoria}
                  </h4>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={item.peso}
                      onChange={() => onSettingsChange(true)}
                      className="w-16 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm text-center"
                    />
                    <span className="text-sm text-gray-800">%</span>
                  </div>
                </div>
                <div className="space-y-1">
                  {item.criterios.map((criterio, idx) => (
                    <div key={idx} className="text-sm text-gray-800 dark:text-gray-200">
                      • {criterio}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Automação Workflows Enterprise
function AutomationsTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [selectedView, setSelectedView] = useState<'overview' | 'builder' | 'templates' | 'logs'>('overview')
  const [workflows, setWorkflows] = useState([
    {
      id: '1',
      name: 'Triagem Automática de Candidatos',
      description: 'Workflow para triagem inicial baseada em critérios pré-definidos',
      status: 'active',
      trigger: 'Novo candidato',
      actions: 5,
      lastRun: '2024-01-20T14:30:00Z',
      executions: 156,
      successRate: 98
    },
    {
      id: '2',
      name: 'Notificação de Entrevistas',
      description: 'Envio automático de lembretes para candidatos e entrevistadores',
      status: 'active',
      trigger: 'Entrevista agendada',
      actions: 3,
      lastRun: '2024-01-20T12:15:00Z',
      executions: 89,
      successRate: 100
    },
    {
      id: '3',
      name: 'Follow-up Pós-entrevista',
      description: 'Coleta automática de feedback e próximos passos',
      status: 'paused',
      trigger: 'Entrevista concluída',
      actions: 4,
      lastRun: '2024-01-19T16:20:00Z',
      executions: 67,
      successRate: 94
    }
  ])

  // Verificar se tem acesso ao módulo
  if (!hasModuleAccess('workflow_automation')) {
    return (
      <ModuleUpsell
        moduleId="workflow_automation"
        title="Automação Avançada de Workflows"
        description="Workflow builder visual com automações inteligentes e templates pré-configurados"
      />
    )
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Workflows Ativos</p>
                <p className="text-2xl font-bold text-green-600">
                  {workflows.filter(w => w.status === 'active').length}
                </p>
                <p className="text-xs text-gray-800">de {workflows.length} total</p>
              </div>
              <div className="w-10 h-10 bg-green-100 rounded-md flex items-center justify-center">
                <Workflow className="w-5 h-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Execuções Hoje</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-50">47</p>
                <p className="text-xs text-green-600">+12% vs ontem</p>
              </div>
              <div className="w-10 h-10 bg-blue-100 rounded-md flex items-center justify-center">
                <Zap className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Taxa de Sucesso</p>
                <p className="text-2xl font-bold text-orange-600">97.3%</p>
                <p className="text-xs text-gray-800">últimos 7 dias</p>
              </div>
              <div className="w-10 h-10 bg-orange-100 rounded-md flex items-center justify-center">
                <Target className="w-5 h-5 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Templates</p>
                <p className="text-2xl font-bold text-purple-600">12</p>
                <p className="text-xs text-gray-800">pré-configurados</p>
              </div>
              <div className="w-10 h-10 bg-purple-100 rounded-md flex items-center justify-center">
                <FileText className="w-5 h-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Workflows List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Workflows Configurados</span>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Novo Workflow
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {workflows.map((workflow) => (
              <div key={workflow.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-md hover:transition-shadow">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                    workflow.status === 'active' ? 'bg-green-100' : 'bg-gray-100'
                  }`}>
                    <Workflow className={`w-5 h-5 ${
                      workflow.status === 'active' ? 'text-green-600' : 'text-gray-800'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-950">{workflow.name}</h4>
                    <p className="text-sm text-gray-800">{workflow.description}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-800">
                      <span>Trigger: {workflow.trigger}</span>
                      <span>•</span>
                      <span>{workflow.actions} ações</span>
                      <span>•</span>
                      <span>{workflow.executions} execuções</span>
                      <span>•</span>
                      <span className="text-green-600">{workflow.successRate}% sucesso</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge variant={workflow.status === 'active' ? 'default' : 'secondary'}>
                    {workflow.status === 'active' ? 'Ativo' : 'Pausado'}
                  </Badge>
                  <Button variant="outline" size="sm">
                    <Edit className="w-4 h-4 mr-2" />
                    Editar
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Ações Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto p-4 justify-start gap-3">
              <Plus className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <div className="text-left">
                <div className="font-medium">Criar Workflow</div>
                <div className="text-sm text-gray-800">Do zero ou usando template</div>
              </div>
            </Button>

            <Button variant="outline" className="h-auto p-4 justify-start gap-3">
              <Download className="w-5 h-5 text-green-600" />
              <div className="text-left">
                <div className="font-medium">Importar Template</div>
                <div className="text-sm text-gray-800">Da biblioteca de templates</div>
              </div>
            </Button>

            <Button variant="outline" className="h-auto p-4 justify-start gap-3">
              <BarChart3 className="w-5 h-5 text-purple-600" />
              <div className="text-left">
                <div className="font-medium">Ver Analytics</div>
                <div className="text-sm text-gray-800">Performance detalhada</div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderBuilder = () => (
    <div className="text-center py-12">
      <Workflow className="w-12 h-12 text-gray-800 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-950 mb-2">Workflow Builder Visual</h3>
      <p className="text-gray-800">Interface de arrastar e soltar para criar workflows</p>
    </div>
  )

  const renderTemplates = () => (
    <div className="text-center py-12">
      <FileText className="w-12 h-12 text-gray-800 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-950 mb-2">Biblioteca de Templates</h3>
      <p className="text-gray-800">Templates pré-configurados para casos comuns</p>
    </div>
  )

  const renderLogs = () => (
    <div className="text-center py-12">
      <Activity className="w-12 h-12 text-gray-800 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-950 mb-2">Logs de Execução</h3>
      <p className="text-gray-800">Histórico detalhado de todas as execuções</p>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-950 flex items-center gap-2">
            <Workflow className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            Automação Workflows Enterprise
          </h2>
          <p className="text-sm text-gray-800">
            Builder visual para automações inteligentes de recrutamento
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2">
            <Download className="w-4 h-4" />
            Exportar
          </Button>
          <Button size="sm" className="gap-2">
            <Plus className="w-4 h-4" />
            Novo Workflow
          </Button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-md w-fit">
        {[
          { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
          { id: 'builder', label: 'Builder', icon: Workflow },
          { id: 'templates', label: 'Templates', icon: FileText },
          { id: 'logs', label: 'Logs', icon: Activity }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedView(tab.id as any)}
            className={`flex items-center gap-2 px-3 py-3 rounded-md text-sm font-medium transition-colors font-crimson ${
              selectedView === tab.id
                ? 'bg-white text-gray-950'
                : 'text-gray-800 hover:text-gray-950'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {selectedView === 'overview' && renderOverview()}
      {selectedView === 'builder' && renderBuilder()}
      {selectedView === 'templates' && renderTemplates()}
      {selectedView === 'logs' && renderLogs()}
    </div>
  )
}

// Componente de NPS (recuperado)
function NPSTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Star className="w-4 h-4" />
            Configurações do Sistema NPS
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Escala de NPS
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option>0-10 (Padrão NPS)</option>
                <option>1-5 (Simplificado)</option>
                <option>1-10 (Personalizado)</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
                Frequência de Envio
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option>Após cada processo seletivo</option>
                <option>Semanal</option>
                <option>Mensal</option>
                <option>Trimestral</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3 block">
              Pergunta Principal
            </label>
            <textarea
              rows={3}
              defaultValue="De 0 a 10, o quanto você recomendaria nossa empresa como um lugar para trabalhar?"
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Integrações (ATS + Comunicação)
function IntegrationsTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [selectedIntegrationType, setSelectedIntegrationType] = useState<'ats' | 'communication'>('ats')
  const [selectedView, setSelectedView] = useState<'overview' | 'systems' | 'mapping' | 'logs'>('overview')
  const [selectedSystem, setSelectedSystem] = useState<ATSSystem | null>(null)
  const [showSystemModal, setShowSystemModal] = useState(false)

  // Mock data das integrações de comunicação
  const [communicationIntegrations, setCommunicationIntegrations] = useState<CommunicationIntegration[]>([
    {
      id: 'slack-recruiting',
      name: 'Canal #recrutamento',
      type: 'slack',
      status: 'active',
      icon: Slack,
      color: 'bg-purple-100 text-purple-700',
      webhookUrl: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',
      channels: ['#recrutamento', '#aprovacoes', '#geral'],
      events: ['novo_candidato', 'aprovacao', 'nova_nota', 'mencao'],
      lastActivity: '2025-03-15T14:30:00Z',
      messagesCount: 247,
      errorCount: 2,
      createdAt: '2025-01-15T10:00:00Z',
      createdBy: 'Ana Silva'
    },
    {
      id: 'teams-rh',
      name: 'Equipe RH',
      type: 'teams',
      status: 'active',
      icon: MessageSquare,
      color: 'bg-gray-50 dark:bg-gray-900 text-wedo-cyan-dark',
      webhookUrl: 'https://outlook.office.com/webhook/xxxxx/IncomingWebhook/yyyyy',
      channels: ['RH Geral', 'Aprovações'],
      events: ['aprovacao_lote', 'candidato_final', 'relatorio_semanal'],
      lastActivity: '2025-03-15T09:15:00Z',
      messagesCount: 156,
      errorCount: 0,
      createdAt: '2025-02-01T14:00:00Z',
      createdBy: 'Carlos Mendes'
    }
  ])

  const [notificationTemplates, setNotificationTemplates] = useState<NotificationTemplate[]>([
    {
      id: 'novo-candidato',
      name: 'Novo Candidato',
      event: 'novo_candidato',
      title: '🎯 Novo candidato aplicou!',
      message: 'O candidato **{candidate_name}** se candidatou para a vaga **{job_title}**.\n\n📊 Score LIA: **{lia_score}%**\n📍 Localização: {location}\n⭐ Match: {match_score}%',
      mentions: ['@channel'],
      active: true,
      integrations: ['slack-recruiting', 'teams-rh']
    },
    {
      id: 'aprovacao-candidato',
      name: 'Aprovação de Candidato',
      event: 'aprovacao',
      title: '✅ Candidato aprovado!',
      message: 'O candidato **{candidate_name}** foi aprovado para a vaga **{job_title}**!\n\n👤 Aprovado por: {approver}\n📅 Data: {date}',
      mentions: ['@here'],
      active: true,
      integrations: ['slack-recruiting', 'teams-rh']
    }
  ])

  // Mock data dos sistemas ATS
  const atsystems: ATSSystem[] = [
    {
      id: 'sap_sf',
      name: 'SAP SuccessFactors',
      type: 'sap',
      status: 'connected',
      description: 'Sistema completo de gestão de recursos humanos',
      lastSync: '2024-01-20T14:30:00Z',
      totalRecords: 2847,
      syncedRecords: 2847,
      errorCount: 0,
      features: ['Candidatos', 'Vagas', 'Entrevistas', 'Ofertas', 'Onboarding'],
      webhookUrl: 'https://api.plataforma-lia.com/webhooks/sap',
      apiEndpoint: 'https://api.successfactors.com/v2',
      version: '2.0'
    },
    {
      id: 'workday',
      name: 'Workday HCM',
      type: 'workday',
      status: 'connecting',
      description: 'Plataforma de capital humano empresarial',
      totalRecords: 0,
      syncedRecords: 0,
      errorCount: 0,
      features: ['Funcionários', 'Requisições', 'Performance', 'Benefícios'],
      apiEndpoint: 'https://wd2-impl-services1.workday.com',
      version: '39.0'
    },
    {
      id: 'bamboohr',
      name: 'BambooHR',
      type: 'bamboohr',
      status: 'error',
      description: 'Sistema de RH para pequenas e médias empresas',
      lastSync: '2024-01-19T16:20:00Z',
      totalRecords: 156,
      syncedRecords: 134,
      errorCount: 22,
      features: ['Colaboradores', 'Relatórios', 'Time Off', 'Performance'],
      webhookUrl: 'https://api.plataforma-lia.com/webhooks/bamboo',
      apiEndpoint: 'https://api.bamboohr.com/api/gateway.php',
      version: '1.0'
    },
    {
      id: 'greenhouse',
      name: 'Greenhouse',
      type: 'greenhouse',
      status: 'disabled',
      description: 'ATS focado em recrutamento e seleção',
      totalRecords: 0,
      syncedRecords: 0,
      errorCount: 0,
      features: ['Candidatos', 'Vagas', 'Entrevistas', 'Scorecards'],
      apiEndpoint: 'https://harvest.greenhouse.io/v1',
      version: '1.0'
    }
  ]

  const syncLogs: SyncLog[] = [
    {
      id: '1',
      timestamp: '2024-01-20T14:30:00Z',
      system: 'SAP SuccessFactors',
      type: 'sync',
      status: 'success',
      records: 15,
      duration: 2340,
      message: 'Sincronização de candidatos concluída com sucesso',
      details: '15 novos candidatos importados, 3 atualizados'
    },
    {
      id: '2',
      timestamp: '2024-01-20T14:15:00Z',
      system: 'SAP SuccessFactors',
      type: 'webhook',
      status: 'success',
      records: 1,
      duration: 156,
      message: 'Nova vaga recebida via webhook',
      details: 'Vaga "Senior Developer" criada automaticamente'
    },
    {
      id: '3',
      timestamp: '2024-01-19T16:20:00Z',
      system: 'BambooHR',
      type: 'sync',
      status: 'error',
      records: 0,
      duration: 5000,
      message: 'Erro de autenticação na API',
      details: 'Token de acesso expirado - necessária renovação manual'
    }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'connecting': return <RefreshCw className="w-4 h-4 text-gray-600 dark:text-gray-400 animate-spin" />
      case 'error': return <XCircle className="w-4 h-4 text-red-600" />
      case 'disabled': return <Minus className="w-4 h-4 text-gray-800" />
      default: return <AlertCircle className="w-4 h-4 text-yellow-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-green-50 text-green-700 border-green-200'
      case 'connecting': return 'bg-gray-50 dark:bg-gray-900 text-wedo-cyan-dark border-gray-900 dark:border-gray-50'
      case 'error': return 'bg-red-50 text-red-700 border-red-200'
      case 'disabled': return 'bg-gray-50 text-gray-800 border-gray-200'
      default: return 'bg-yellow-50 text-yellow-700 border-yellow-200'
    }
  }

  const getSyncStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle2 className="w-4 h-4 text-green-600" />
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-600" />
      case 'error': return <XCircle className="w-4 h-4 text-red-600" />
      default: return <Info className="w-4 h-4 text-gray-600 dark:text-gray-400" />
    }
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Sistemas Conectados</p>
                <p className="text-2xl font-bold text-gray-950">
                  {atsystems.filter(s => s.status === 'connected').length}
                </p>
                <p className="text-xs text-gray-800">de {atsystems.length} configurados</p>
              </div>
              <div className="w-10 h-10 bg-green-100 rounded-md flex items-center justify-center">
                <Link2 className="w-5 h-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Registros Sincronizados</p>
                <p className="text-2xl font-bold text-blue-900">
                  {atsystems.reduce((acc, sys) => acc + sys.syncedRecords, 0).toLocaleString()}
                </p>
                <p className="text-xs text-green-600">+47 hoje</p>
              </div>
              <div className="w-10 h-10 bg-blue-100 rounded-md flex items-center justify-center">
                <Database className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Uptime Médio</p>
                <p className="text-2xl font-bold text-orange-900">99.7%</p>
                <p className="text-xs text-orange-600">últimos 30 dias</p>
              </div>
              <div className="w-10 h-10 bg-orange-100 rounded-md flex items-center justify-center">
                <Activity className="w-5 h-5 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">Última Sincronização</p>
                <p className="text-lg font-bold text-gray-950">Há 15min</p>
                <p className="text-xs text-gray-800">SAP SuccessFactors</p>
              </div>
              <div className="w-10 h-10 bg-purple-100 rounded-md flex items-center justify-center">
                <RefreshCw className="w-5 h-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sistemas Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Server className="w-4 h-4" />
            Status dos Sistemas ATS
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {atsystems.map(system => (
              <div key={system.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-md">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-gray-100 rounded-md flex items-center justify-center">
                    <Server className="w-5 h-5 text-gray-800" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-950">{system.name}</h4>
                    <p className="text-sm text-gray-800">{system.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(system.status)}
                      <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(system.status)}`}>
                        {system.status === 'connected' ? 'Conectado' :
                         system.status === 'connecting' ? 'Conectando' :
                         system.status === 'error' ? 'Erro' : 'Desabilitado'}
                      </span>
                      {system.lastSync && (
                        <span className="text-xs text-gray-800">
                          Última sync: {new Date(system.lastSync).toLocaleString('pt-BR')}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-sm">
                  {system.status === 'connected' && (
                    <>
                      <div className="text-center">
                        <p className="font-medium text-gray-950">{system.syncedRecords}</p>
                        <p className="text-gray-800">Registros</p>
                      </div>
                      <div className="text-center">
                        <p className="font-medium text-green-600">
                          {Math.round((system.syncedRecords / system.totalRecords) * 100)}%
                        </p>
                        <p className="text-gray-800">Sincronizado</p>
                      </div>
                    </>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedSystem(system)
                      setShowSystemModal(true)
                      onSettingsChange(true)
                    }}
                  >
                    Configurar
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Logs Recentes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Logs Recentes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {syncLogs.slice(0, 3).map(log => (
              <div key={log.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div className="flex items-center gap-3">
                  {getSyncStatusIcon(log.status)}
                  <div>
                    <p className="text-sm font-medium text-gray-950">{log.message}</p>
                    <p className="text-xs text-gray-800">
                      {log.system} • {new Date(log.timestamp).toLocaleString('pt-BR')}
                    </p>
                  </div>
                </div>
                <div className="text-right text-xs text-gray-800">
                  <p>{log.records} registros</p>
                  <p>{log.duration}ms</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-950 flex items-center gap-2">
            <Link2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            Integrações
          </h2>
          <p className="text-sm text-gray-800">
            Conecte sistemas ATS, Slack, Teams e outras plataformas
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Sincronizar Tudo
          </Button>
          <Button size="sm" className="gap-2">
            <Plus className="w-4 h-4" />
            Nova Integração
          </Button>
        </div>
      </div>

      {/* Integration Type Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-md w-fit">
        <button
          onClick={() => setSelectedIntegrationType('ats')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedIntegrationType === 'ats'
              ? 'bg-white text-gray-600 dark:text-gray-400'
              : 'text-gray-800 hover:text-gray-950'
          }`}
        >
          <Database className="w-4 h-4" />
          Sistemas ATS
        </button>
        <button
          onClick={() => setSelectedIntegrationType('communication')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selectedIntegrationType === 'communication'
              ? 'bg-white text-gray-600 dark:text-gray-400'
              : 'text-gray-800 hover:text-gray-950'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          Comunicação
        </button>
      </div>

      {/* ATS Content */}
      {selectedIntegrationType === 'ats' && (
        <>
          {/* Check module access for ATS */}
          {!hasModuleAccess('ats_integrations') ? (
            <ModuleUpsell
              moduleId="ats_integrations"
              title="Integrações ATS Enterprise"
              description="Conecte e sincronize dados com sistemas HR externos como SAP SuccessFactors, Workday e BambooHR"
            />
          ) : (
            <>
              {/* ATS Navigation Tabs */}
              <div className="flex space-x-1 bg-gray-100 p-1 rounded-md w-fit">
                {[
                  { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
                  { id: 'systems', label: 'Sistemas', icon: Server },
                  { id: 'mapping', label: 'Mapeamento', icon: GitBranch },
                  { id: 'logs', label: 'Logs', icon: FileText }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedView(tab.id as any)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      selectedView === tab.id
                        ? 'bg-white text-gray-600 dark:text-gray-400'
                        : 'text-gray-800 hover:text-gray-950'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* ATS Content based on selectedView */}
              {selectedView === 'overview' && renderOverview()}
              {selectedView === 'systems' && (
                <div className="text-center py-12">
                  <Server className="w-12 h-12 text-gray-800 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-950 mb-2">Configuração de Sistemas</h3>
                  <p className="text-gray-800">Conectar e configurar sistemas ATS externos</p>
                </div>
              )}
              {selectedView === 'mapping' && (
                <div className="text-center py-12">
                  <GitBranch className="w-12 h-12 text-gray-800 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-950 mb-2">Mapeamento de Campos</h3>
                  <p className="text-gray-800">Interface visual drag-and-drop para mapear campos entre sistemas</p>
                </div>
              )}
              {selectedView === 'logs' && (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-gray-800 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-950 mb-2">Logs Detalhados</h3>
                  <p className="text-gray-800">Histórico completo de sincronizações e operações</p>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* Communication Content */}
      {selectedIntegrationType === 'communication' && (
        <div className="space-y-6">
          {/* Communication Integrations Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-md flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">Integrações Ativas</p>
                    <p className="text-2xl font-bold text-gray-950">
                      {communicationIntegrations.filter(i => i.status === 'active').length}
                    </p>
                    <p className="text-xs text-gray-800">de {communicationIntegrations.length} total</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-md flex items-center justify-center">
                    <Send className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">Mensagens Enviadas</p>
                    <p className="text-2xl font-bold text-gray-950">
                      {communicationIntegrations.reduce((acc, i) => acc + i.messagesCount, 0)}
                    </p>
                    <p className="text-xs text-gray-800">últimos 30 dias</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-md flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">Taxa de Sucesso</p>
                    <p className="text-2xl font-bold text-gray-950">98.5%</p>
                    <p className="text-xs text-gray-800">últimos 30 dias</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Active Integrations */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Integrações Configuradas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {communicationIntegrations.map(integration => (
                  <div key={integration.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-md">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-md flex items-center justify-center ${integration.color}`}>
                        <integration.icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-950">{integration.name}</h3>
                        <p className="text-sm text-gray-800">{integration.channels.join(', ')}</p>
                        <div className="flex items-center gap-4 mt-1">
                          <span className="text-xs text-gray-800">
                            {integration.messagesCount} mensagens
                          </span>
                          <span className="text-xs text-gray-800">
                            Criado por {integration.createdBy}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={`${
                        integration.status === 'active' ? 'bg-green-100 text-green-700' :
                        integration.status === 'error' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {integration.status === 'active' ? 'Ativo' :
                         integration.status === 'error' ? 'Erro' : 'Inativo'}
                      </Badge>
                      <Button variant="outline" size="sm">
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Notification Templates */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Templates de Notificação</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {notificationTemplates.map(template => (
                  <div key={template.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-md">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-blue-100 rounded-md flex items-center justify-center">
                        <Bell className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-950">{template.name}</h3>
                        <p className="text-sm text-gray-800">{template.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-gray-800">
                            {template.integrations.length} integrações
                          </span>
                          {template.mentions.length > 0 && (
                            <Badge variant="outline" className="text-xs">
                              {template.mentions.join(', ')}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={template.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-800'}>
                        {template.active ? 'Ativo' : 'Inativo'}
                      </Badge>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-md w-fit">
        {[
          { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
          { id: 'systems', label: 'Sistemas', icon: Server },
          { id: 'mapping', label: 'Mapeamento', icon: GitBranch },
          { id: 'logs', label: 'Logs', icon: FileText }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedView(tab.id as any)}
            className={`flex items-center gap-2 px-3 py-3 rounded-md text-sm font-medium transition-colors font-crimson ${
              selectedView === tab.id
                ? 'bg-white text-gray-950'
                : 'text-gray-800 hover:text-gray-950'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {selectedView === 'overview' && renderOverview()}
      {selectedView === 'systems' && (
        <div className="text-center py-12">
          <Server className="w-12 h-12 text-gray-800 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-950 mb-2">Gerenciamento de Sistemas</h3>
          <p className="text-gray-800">Interface de configuração detalhada dos sistemas ATS</p>
        </div>
      )}
      {selectedView === 'mapping' && (
        <div className="text-center py-12">
          <GitBranch className="w-12 h-12 text-gray-800 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-950 mb-2">Mapeamento de Campos</h3>
          <p className="text-gray-800">Interface visual drag-and-drop para mapear campos entre sistemas</p>
        </div>
      )}
      {selectedView === 'logs' && (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-gray-800 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-950 mb-2">Logs Detalhados</h3>
          <p className="text-gray-800">Histórico completo de sincronizações e operações</p>
        </div>
      )}
    </div>
  )
}

// Componente de Segurança (mantido como estava)
function SecurityTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Shield className="w-4 h-4" />
            Segurança da Conta
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Button variant="outline" className="w-full justify-start">
              <Shield className="w-4 h-4 mr-2" />
              Alterar Senha
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Phone className="w-4 h-4 mr-2" />
              Configurar 2FA
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Download className="w-4 h-4 mr-2" />
              Baixar Dados
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Privacidade</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Compartilhar dados de uso</div>
                <div className="text-xs text-gray-800 dark:text-gray-400">Ajuda a melhorar a plataforma</div>
              </div>
              <input type="checkbox" defaultChecked onChange={() => onSettingsChange(true)} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Análise de comportamento</div>
                <div className="text-xs text-gray-800 dark:text-gray-400">Para personalizar sua experiência</div>
              </div>
              <input type="checkbox" defaultChecked onChange={() => onSettingsChange(true)} />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Componente de Administração WeDOTalent
function AdminWeDOTalentTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSection, setActiveSection] = useState("clients")
  const [showAddClientModal, setShowAddClientModal] = useState(false)
  const [showSendInviteModal, setShowSendInviteModal] = useState(false)
  const [selectedClient, setSelectedClient] = useState<any>(null)

  const adminSections = [
    { id: "clients", name: "Clientes", icon: Building, desc: "Gerenciar empresas cliente" },
    { id: "tenants", name: "Tenants", icon: Network, desc: "Configurar ambientes" },
    { id: "onboarding", name: "Onboarding", icon: Rocket, desc: "Setup e ativação" },
    { id: "billing", name: "Faturamento", icon: CreditCard, desc: "Contratos e pagamentos" },
    { id: "performance", name: "Dashboard Performance", icon: Activity, desc: "Monitoramento em tempo real" }
  ]

  const mockClients = [
    {
      id: 1,
      name: "Sodexo Brasil",
      cnpj: "12.345.678/0001-90",
      status: "ativo",
      plan: "Enterprise",
      users: 45,
      setupDate: "2024-01-15",
      contact: {
        name: "Ana Silva",
        email: "ana.silva@sodexo.com.br",
        phone: "(11) 99999-9999"
      },
      tenant: "sodexo-prod",
      lastAccess: "2024-01-20 14:30"
    },
    {
      id: 2,
      name: "TechCorp Inovação",
      cnpj: "98.765.432/0001-10",
      status: "setup",
      plan: "Professional",
      users: 0,
      setupDate: "2024-01-18",
      contact: {
        name: "Carlos Santos",
        email: "carlos@techcorp.com.br",
        phone: "(11) 88888-8888"
      },
      tenant: "techcorp-prod",
      lastAccess: "Nunca"
    },
    {
      id: 3,
      name: "StartupXYZ",
      cnpj: "55.444.333/0001-22",
      status: "trial",
      plan: "Starter",
      users: 3,
      setupDate: "2024-01-19",
      contact: {
        name: "Maria Costa",
        email: "maria@startupxyz.com",
        phone: "(11) 77777-7777"
      },
      tenant: "startupxyz-trial",
      lastAccess: "2024-01-20 09:15"
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ativo": return "bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400"
      case "setup": return "bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400"
 case "trial": return "bg-gray-50 text-wedo-cyan-dark dark:bg-gray-800 dark:text-gray-400"
      case "suspenso": return "bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400"
      default: return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-500"
    }
  }

  const renderClientsSection = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-800" />
            <input
              type="text"
              placeholder="Buscar clientes..."
              className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 w-64"
            />
          </div>
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-2" />
            Filtros
          </Button>
        </div>
        <Button onClick={() => setShowAddClientModal(true)} className="gap-2">
          <UserPlus className="w-4 h-4" />
          Novo Cliente
        </Button>
      </div>

      <div className="grid gap-4">
        {mockClients.map((client) => (
          <Card key={client.id} className="hover:transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-md flex items-center justify-center">
                    <Building className="w-6 h-6 text-gray-800 dark:text-gray-200" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-950 dark:text-gray-50">{client.name}</h3>
                    <p className="text-sm text-gray-800 dark:text-gray-200">CNPJ: {client.cnpj}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <Badge className={getStatusColor(client.status)}>
                        {client.status.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-gray-800">Plano {client.plan}</span>
                      <span className="text-xs text-gray-800">{client.users} usuários</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedClient(client)
                      setShowSendInviteModal(true)
                    }}
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Enviar Link
                  </Button>
                  <Button variant="outline" size="sm">
                    <Eye className="w-4 h-4 mr-2" />
                    Ver Detalhes
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-800 dark:text-gray-200">Contato:</span>
                    <div className="font-medium">{client.contact.name}</div>
                    <div className="text-gray-800 dark:text-gray-200">{client.contact.email}</div>
                  </div>
                  <div>
                    <span className="text-gray-800 dark:text-gray-200">Tenant:</span>
                    <div className="font-medium font-mono text-xs">{client.tenant}</div>
                  </div>
                  <div>
                    <span className="text-gray-800 dark:text-gray-200">Último acesso:</span>
                    <div className="font-medium">{client.lastAccess}</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )

  const renderTenantsSection = () => (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Gerenciamento de Tenants</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-md">
                <div className="text-2xl font-bold text-green-700 dark:text-green-400">12</div>
                <div className="text-sm text-green-600 dark:text-green-500">Tenants Ativos</div>
              </div>
              <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-md">
                <div className="text-2xl font-bold text-orange-700 dark:text-orange-400">3</div>
                <div className="text-sm text-orange-600 dark:text-orange-500">Em Setup</div>
              </div>
              <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                <div className="text-2xl font-bold text-wedo-cyan-dark dark:text-gray-400">2</div>
 <div className="text-sm text-gray-600">Trial</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderOnboardingSection = () => (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Central de Onboarding</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-md">
              <h4 className="font-medium mb-2">Templates de Email</h4>
              <div className="space-y-2">
                <Button variant="outline" size="sm" className="mr-2">Email de Boas-vindas</Button>
                <Button variant="outline" size="sm" className="mr-2">Instruções de Setup</Button>
                <Button variant="outline" size="sm">Link de Ativação</Button>
              </div>
            </div>

            <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-md">
              <h4 className="font-medium mb-2">Checklist de Setup</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Criar tenant no banco de dados</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Configurar domínio personalizado</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Enviar credenciais de acesso</span>
                </div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-orange-600" />
                  <span>Agendar treinamento inicial</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderPerformanceSection = () => (
    <div className="space-y-4">
      <RealTimeDashboardPage />
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-1">
            {adminSections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium transition-colors font-crimson ${
                  activeSection === section.id
 ? 'bg-gray-50 dark:bg-gray-800 text-wedo-cyan-dark dark:text-gray-300'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-200'
                }`}
              >
                <section.icon className="w-4 h-4" />
                {section.name}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Section Content */}
      {activeSection === "clients" && renderClientsSection()}
      {activeSection === "tenants" && renderTenantsSection()}
      {activeSection === "onboarding" && renderOnboardingSection()}
      {activeSection === "performance" && renderPerformanceSection()}

      {/* Modais */}
      {showAddClientModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-md w-full max-w-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Novo Cliente</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowAddClientModal(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Nome da Empresa</label>
                <input
                  type="text"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md"
                  placeholder="Ex: Sodexo Brasil"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">CNPJ</label>
                <input
                  type="text"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md"
                  placeholder="00.000.000/0001-00"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Nome do Contato</label>
                <input
                  type="text"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md"
                  placeholder="Ex: Ana Silva"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Email</label>
                <input
                  type="email"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md"
                  placeholder="ana.silva@empresa.com"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Telefone</label>
                <input
                  type="tel"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md"
                  placeholder="(11) 99999-9999"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Plano</label>
                <select className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md">
                  <option>Starter</option>
                  <option>Professional</option>
                  <option>Enterprise</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddClientModal(false)}>
                Cancelar
              </Button>
              <Button onClick={() => setShowAddClientModal(false)}>
                Criar Cliente
              </Button>
            </div>
          </div>
        </div>
      )}

      {showSendInviteModal && selectedClient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-md w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Enviar Link de Setup</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowSendInviteModal(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Cliente</label>
                <input
                  type="text"
                  value={selectedClient.name}
                  disabled
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Email do Contato</label>
                <input
                  type="email"
                  value={selectedClient.contact.email}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Tipo de Link</label>
                <select className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md">
                  <option>Setup Inicial Completo</option>
                  <option>Apenas Ativação</option>
                  <option>Resetar Senha Admin</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Mensagem Personalizada</label>
                <textarea
                  rows={3}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md"
                  placeholder="Adicione uma mensagem personalizada (opcional)"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" onClick={() => setShowSendInviteModal(false)}>
                Cancelar
              </Button>
              <Button onClick={() => setShowSendInviteModal(false)}>
                <Send className="w-4 h-4 mr-2" />
                Enviar Link
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
