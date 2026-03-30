"use client"

import React, { useState, useCallback, useEffect } from "react"
import { textStyles, cardStyles, badgeStyles, actionButtonStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DraggableDialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Gift,
  Plus,
  Pencil,
  Trash2,
  ChevronDown,
  ChevronRight,
  DollarSign,
  Percent,
  Info,
  CheckCircle,
  Loader2,
  X,
  Star,
  Clock,
  Users,
  AlertCircle,
  Utensils,
  Car,
  GraduationCap,
  Wallet,
  Home,
  Baby,
  Stethoscope,
  Shield,
  Search,
  Library,
  Check,
} from "lucide-react"
import { SmartImportZone } from "./SmartImportZone"
import { LiaFieldToggle, defaultLiaFieldExamples } from "./LiaFieldToggle"
import { useCompanyLiaInstructions } from "@/hooks/use-company-lia-instructions"

const BENEFIT_CATEGORIES = [
  { id: "health", name: "Saúde & Bem-estar", icon: Stethoscope, color: "text-status-error", bgColor: "bg-status-error/10 dark:bg-status-error/20" },
  { id: "food", name: "Alimentação", icon: Utensils, color: "text-wedo-orange", bgColor: "bg-wedo-orange/10 dark:bg-wedo-orange/20" },
  { id: "transport", name: "Transporte", icon: Car, color: "lia-text-700 dark:text-lia-text-secondary", bgColor: "bg-gray-100 dark:bg-lia-bg-secondary" },
  { id: "education", name: "Educação & Desenvolvimento", icon: GraduationCap, color: "text-wedo-purple", bgColor: "bg-wedo-purple/10 dark:bg-wedo-purple/20" },
  { id: "financial", name: "Financeiro", icon: Wallet, color: "text-status-success", bgColor: "bg-status-success/10 dark:bg-status-success/20" },
  { id: "quality_life", name: "Qualidade de Vida", icon: Home, color: "lia-text-600 dark:text-lia-text-tertiary", bgColor: "bg-gray-100 dark:bg-lia-bg-secondary" },
  { id: "family", name: "Família", icon: Baby, color: "text-wedo-magenta", bgColor: "bg-wedo-magenta/10 dark:bg-wedo-magenta/20" },
  { id: "security", name: "Segurança", icon: Shield, color: "lia-text-800 dark:text-lia-text-primary", bgColor: "bg-gray-50 dark:bg-lia-bg-secondary/50" },
]

const SENIORITY_LEVELS = [
  { id: "all", name: "Todos os Níveis" },
  { id: "junior", name: "Júnior" },
  { id: "pleno", name: "Pleno" },
  { id: "senior", name: "Sênior" },
  { id: "coordinator", name: "Coordenação+" },
  { id: "manager", name: "Gerência+" },
  { id: "director", name: "Diretoria" },
  { id: "c-level", name: "C-Level" },
]

const VALUE_TYPES = [
  { id: "monetary", name: "Valor Monetário", icon: DollarSign, description: "Valor fixo em R$" },
  { id: "percentage", name: "Percentual", icon: Percent, description: "Porcentagem (ex: 5% contribuição)" },
  { id: "informative", name: "Informativo", icon: Info, description: "Apenas descrição, sem valor" },
]

const WAITING_PERIODS = [
  { id: 0, name: "Imediato" },
  { id: 30, name: "30 dias" },
  { id: 60, name: "60 dias" },
  { id: 90, name: "90 dias" },
  { id: 180, name: "6 meses" },
  { id: 365, name: "1 ano" },
]

interface Benefit {
  id?: string
  name: string
  description: string
  category: string
  value_type: string
  value?: number
  percentage_value?: number
  value_details?: string
  seniority_levels: string[]
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean
  provider?: string
}

interface BenefitTemplate {
  id: string
  name: string
  description: string
  category: string
  is_popular: boolean
  is_active: boolean
  order: number
}

const defaultBenefit: Benefit = {
  name: "",
  description: "",
  category: "health",
  value_type: "monetary",
  value: undefined,
  percentage_value: undefined,
  value_details: "",
  seniority_levels: ["all"],
  waiting_period_days: 0,
  is_mandatory: false,
  is_active: true,
  is_highlighted: false,
  is_discount: false,
  provider: "",
}

export function BenefitsTab() {
  const [benefits, setBenefits] = useState<Benefit[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [showBenefitModal, setShowBenefitModal] = useState(false)
  const [editingBenefit, setEditingBenefit] = useState<Benefit | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<string[]>(BENEFIT_CATEGORIES.map(c => c.id))
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [templates, setTemplates] = useState<BenefitTemplate[]>([])
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false)
  const [templateSearch, setTemplateSearch] = useState("")
  const [templateCategoryFilter, setTemplateCategoryFilter] = useState<string>("all")
  const [isEditingBenefits, setIsEditingBenefits] = useState(false)
  const [benefitsBackup, setBenefitsBackup] = useState<Benefit[]>([])
  const [pendingChanges, setPendingChanges] = useState<Map<string, Benefit>>(new Map())

  const { config, isLoading: isLoadingLia, refetch: refetchLia } = useCompanyLiaInstructions()
  const [liaToggles, setLiaToggles] = useState<Record<string, boolean>>({})
  const [liaInstructions, setLiaInstructions] = useState<Record<string, string>>({})

  useEffect(() => {
    if (config) {
      setLiaToggles(config.lia_field_toggles || { benefits: true })
      setLiaInstructions(config.lia_instructions || {})
    }
  }, [config])

  const handleLiaToggleChange = useCallback((fieldKey: string, isActive: boolean) => {
    const updatedToggles = { ...liaToggles, [fieldKey]: isActive }
    setLiaToggles(updatedToggles)
    saveLiaFieldToggles(updatedToggles)
  }, [liaToggles])

  const handleLiaInstructionSave = useCallback(async (fieldKey: string, instruction: string) => {
    const updatedInstructions = { ...liaInstructions, [fieldKey]: instruction }
    setLiaInstructions(updatedInstructions)
    await saveLiaFieldToggles(liaToggles, updatedInstructions)
  }, [liaInstructions, liaToggles])

  const getCompanyId = async (): Promise<string> => {
    try {
      const res = await fetch('/api/backend-proxy/company/profile')
      if (res.ok) {
        const company = await res.json()
        return company.id || 'default'
      }
    } catch (e) {
    }
    return 'default'
  }

  const saveLiaFieldToggles = async (toggles: Record<string, boolean>, instructions?: Record<string, string>) => {
    try {
      const companyId = await getCompanyId()
      const response = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${companyId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lia_field_toggles: toggles,
          lia_instructions: instructions || liaInstructions,
        }),
      })

      if (!response.ok) {
      } else {
        await refetchLia()
      }
    } catch (err) {
    }
  }

  const normalizeBenefit = (benefit: any): Benefit => ({
    ...benefit,
    description: benefit.description || "",
    value_type: benefit.value_type || "informative",
    seniority_levels: Array.isArray(benefit.seniority_levels) 
      ? benefit.seniority_levels 
      : benefit.seniority_levels 
        ? [benefit.seniority_levels] 
        : ["all"],
    waiting_period_days: benefit.waiting_period_days ?? 0,
    is_mandatory: benefit.is_mandatory ?? false,
    is_active: benefit.is_active ?? true,
    is_highlighted: benefit.is_highlighted ?? false,
    is_discount: benefit.is_discount ?? false,
    provider: benefit.provider || "",
  })

  const loadBenefits = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/backend-proxy/company/benefits/?company_id=default')
      if (response.ok) {
        const data = await response.json()
        const rawBenefits = Array.isArray(data) ? data : data.items || []
        setBenefits(rawBenefits.map(normalizeBenefit))
      }
    } catch (err) {
      setError("Erro ao carregar benefícios")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadBenefits()
  }, [loadBenefits])

  const loadTemplates = useCallback(async () => {
    setIsLoadingTemplates(true)
    try {
      const response = await fetch('/api/backend-proxy/benefits/templates')
      if (response.ok) {
        const data = await response.json()
        setTemplates(data.items || [])
      }
    } catch (err) {
    } finally {
      setIsLoadingTemplates(false)
    }
  }, [])

  const seedTemplates = useCallback(async () => {
    try {
      await fetch('/api/backend-proxy/benefits/templates', {
        method: 'POST',
      })
      await loadTemplates()
    } catch (err) {
    }
  }, [loadTemplates])

  useEffect(() => {
    if (showTemplateModal && templates.length === 0) {
      loadTemplates().then(() => {
        if (templates.length === 0) {
          seedTemplates()
        }
      })
    }
  }, [showTemplateModal, templates.length, loadTemplates, seedTemplates])

  const handleAddTemplateDirectly = async (template: BenefitTemplate) => {
    const newBenefit: Benefit = {
      name: template.name,
      description: template.description || "",
      category: template.category,
      value_type: "informative",
      value: undefined,
      percentage_value: undefined,
      value_details: "",
      seniority_levels: ["all"],
      waiting_period_days: 0,
      is_mandatory: false,
      is_active: true,
      is_highlighted: template.is_popular,
      is_discount: false,
      provider: "",
    }
    
    try {
      const response = await fetch('/api/backend-proxy/company/benefits/?company_id=default', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newBenefit),
      })

      if (response.ok) {
        await loadBenefits()
        setSuccessMessage(`Benefício "${template.name}" adicionado com sucesso!`)
        setTimeout(() => setSuccessMessage(null), 3000)
      } else {
        throw new Error('Falha ao adicionar benefício')
      }
    } catch (err) {
      setError("Erro ao adicionar benefício")
      setTimeout(() => setError(null), 3000)
    }
  }

  const handleSelectTemplate = (template: BenefitTemplate) => {
    handleAddTemplateDirectly(template)
  }

  const isTemplateAlreadyAdded = (templateName: string) => {
    return benefits.some(b => b.name.toLowerCase() === templateName.toLowerCase())
  }

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = templateSearch === "" || 
      template.name.toLowerCase().includes(templateSearch.toLowerCase()) ||
      (template.description && template.description.toLowerCase().includes(templateSearch.toLowerCase()))
    const matchesCategory = templateCategoryFilter === "all" || template.category === templateCategoryFilter
    return matchesSearch && matchesCategory
  })

  const templatesByCategory = BENEFIT_CATEGORIES.reduce((acc, cat) => {
    acc[cat.id] = filteredTemplates.filter(t => t.category === cat.id)
    return acc
  }, {} as Record<string, BenefitTemplate[]>)

  const handleSaveBenefit = async (benefit: Benefit) => {
    setIsSaving(true)
    setError(null)
    try {
      const url = benefit.id 
        ? `/api/backend-proxy/company/benefits/${benefit.id}?company_id=default`
        : '/api/backend-proxy/company/benefits/?company_id=default'
      
      const response = await fetch(url, {
        method: benefit.id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(benefit),
      })

      if (response.ok) {
        await loadBenefits()
        setShowBenefitModal(false)
        setEditingBenefit(null)
        setSuccessMessage(benefit.id ? 'Benefício atualizado com sucesso!' : 'Benefício criado com sucesso!')
        setTimeout(() => setSuccessMessage(null), 3000)
      } else {
        throw new Error('Falha ao salvar benefício')
      }
    } catch (err) {
      setError("Erro ao salvar benefício")
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteBenefit = async (benefitId: string) => {
    if (!confirm("Tem certeza que deseja excluir este benefício?")) return
    
    try {
      const response = await fetch(`/api/backend-proxy/company/benefits/${benefitId}?company_id=default`, {
        method: 'DELETE',
      })
      if (response.ok) {
        await loadBenefits()
        setSuccessMessage('Benefício excluído com sucesso!')
        setTimeout(() => setSuccessMessage(null), 3000)
      }
    } catch (err) {
      setError("Erro ao excluir benefício")
    }
  }

  const handleToggleBenefitStatus = (benefit: Benefit) => {
    if (!benefit.id) return
    const benefitId = benefit.id
    const updatedBenefit = { ...benefit, is_active: !benefit.is_active }
    setBenefits(prev => prev.map(b => b.id === benefitId ? updatedBenefit : b))
    setPendingChanges(prev => {
      const newChanges = new Map(prev)
      newChanges.set(benefitId, updatedBenefit)
      return newChanges
    })
  }

  const handleEnterEditMode = () => {
    setBenefitsBackup([...benefits])
    setPendingChanges(new Map())
    setIsEditingBenefits(true)
  }

  const handleCancelEdit = () => {
    setBenefits(benefitsBackup)
    setPendingChanges(new Map())
    setIsEditingBenefits(false)
  }

  const handleSaveChanges = async () => {
    if (pendingChanges.size === 0) {
      setIsEditingBenefits(false)
      return
    }

    setIsSaving(true)
    setError(null)
    try {
      const savePromises = Array.from(pendingChanges.values()).map(benefit => 
        fetch(`/api/backend-proxy/company/benefits/${benefit.id}?company_id=default`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(benefit),
        })
      )
      
      const results = await Promise.all(savePromises)
      const allSuccess = results.every(r => r.ok)
      
      if (allSuccess) {
        await loadBenefits()
        setSuccessMessage('Alterações salvas com sucesso!')
        setTimeout(() => setSuccessMessage(null), 3000)
      } else {
        throw new Error('Algumas alterações não puderam ser salvas')
      }
    } catch (err) {
      setError("Erro ao salvar alterações")
    } finally {
      setIsSaving(false)
      setPendingChanges(new Map())
      setIsEditingBenefits(false)
    }
  }

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev => 
      prev.includes(categoryId) 
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    )
  }

  const getBenefitsByCategory = (categoryId: string) => {
    return benefits.filter(b => b.category === categoryId)
  }

  const getCategoryInfo = (categoryId: string) => {
    return BENEFIT_CATEGORIES.find(c => c.id === categoryId) || BENEFIT_CATEGORIES[0]
  }

  const formatBenefitValue = (benefit: Benefit) => {
    if (benefit.value_type === "monetary" && benefit.value) {
      const prefix = benefit.is_discount ? "Desconto: " : ""
      return `${prefix}R$ ${benefit.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
    }
    if (benefit.value_type === "percentage" && benefit.percentage_value) {
      return `${benefit.percentage_value}%`
    }
    if (benefit.value_type === "informative") {
      return benefit.value_details || "Informativo"
    }
    return "-"
  }

  const getSeniorityLabel = (levels: string[]) => {
    if (!levels || levels.length === 0 || levels.includes('all')) {
      return "Todos"
    }
    if (levels.length === 1) {
      return SENIORITY_LEVELS.find(l => l.id === levels[0])?.name || levels[0]
    }
    return `${levels.length} níveis`
  }

  const getWaitingPeriodLabel = (days: number) => {
    const period = WAITING_PERIODS.find(p => p.id === days)
    return period?.name || `${days} dias`
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2 lia-text-600 dark:text-lia-text-tertiary" />
            <p className={`${textStyles.description}`}>Carregando benefícios...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {successMessage && (
        <div className={`${badgeStyles.success} px-2 py-1.5 rounded-md flex items-center gap-2`}>
          <CheckCircle className="w-4 h-4" />
          {successMessage}
        </div>
      )}
      
      {error && (
        <div className={`${badgeStyles.error} px-2 py-1.5 rounded-md flex items-center gap-2`}>
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${textStyles.titleLarge} dark:text-lia-text-primary`}>
            Benefícios da Empresa
          </h2>
          <p className={`${textStyles.body} mt-1`}>
            Gerencie os benefícios oferecidos aos colaboradores
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3">
            <LiaFieldToggle
              fieldKey="benefits"
              isActive={liaToggles.benefits ?? true}
              currentInstruction={liaInstructions.benefits || ''}
              examples={defaultLiaFieldExamples.benefits}
              onToggleChange={handleLiaToggleChange}
              onInstructionSave={handleLiaInstructionSave}
              compact
            />
            <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">Consumido pela LIA</span>
          </div>
          {!isEditingBenefits ? (
            <button
              onClick={handleEnterEditMode}
              className={actionButtonStyles.smOutline}
            >
              <Pencil className={actionButtonStyles.icon} />
              Editar
            </button>
          ) : (
            <>
              <button
                onClick={handleCancelEdit}
                className={actionButtonStyles.smSecondary}
                disabled={isSaving}
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveChanges}
                disabled={isSaving}
                className={actionButtonStyles.smPrimary}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  'Salvar Alterações'
                )}
              </button>
            </>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTemplateModal(true)}
            disabled={!isEditingBenefits}
            className="gap-1.5 rounded-md text-xs border-lia-border-default lia-text-700 dark:border-lia-border-default dark:text-lia-text-secondary hover:bg-gray-50 dark:hover:bg-gray-800"
          >
            <Library className="w-3.5 h-3.5" />
            Adicionar da Lista
          </Button>
          <Button
            size="sm"
            onClick={() => {
              setEditingBenefit({ ...defaultBenefit })
              setShowBenefitModal(true)
            }}
            disabled={!isEditingBenefits}
            className="gap-1.5 rounded-md text-xs bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
          >
            <Plus className="w-3.5 h-3.5" />
            Novo Benefício
          </Button>
        </div>
      </div>

      <SmartImportZone
        title="Importar Benefícios"
        description="Arraste uma planilha Excel ou CSV com os benefícios da empresa. A LIA vai cruzar com a lista de benefícios pré-cadastrados e cadastrar automaticamente."
        importEndpoint="/api/backend-proxy/benefits/import?company_id=default"
        templateDownloadEndpoint="/api/backend-proxy/benefits/import/template"
        expectedFields={["name", "description", "category", "value_type", "value", "seniority_levels", "waiting_period_days", "provider"]}
        onImportSuccess={() => { loadBenefits() }}
        disabled={!isEditingBenefits}
      />

      <div className="space-y-3">
        {BENEFIT_CATEGORIES.map((category) => {
          const categoryBenefits = getBenefitsByCategory(category.id)
          const isExpanded = expandedCategories.includes(category.id)
          const CategoryIcon = category.icon

          return (
            <Card key={category.id} className={`${cardStyles.default} dark:border-lia-border-subtle/50 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md overflow-hidden`}>
              <div
                className={`flex items-center justify-between p-3 cursor-pointer transition-colors ${category.bgColor}`}
                onClick={() => toggleCategory(category.id)}
              >
                <div className="flex items-center gap-2">
                  <div className={`p-1.5 rounded-md bg-white dark:bg-lia-bg-secondary`}>
                    <CategoryIcon className={`w-4 h-4 ${category.color}`} />
                  </div>
                  <div>
                    <h3 className={`${textStyles.title} dark:text-lia-text-primary`}>
                      {category.name}
                    </h3>
                    <p className={textStyles.caption}>
                      {categoryBenefits.length} {categoryBenefits.length === 1 ? 'benefício' : 'benefícios'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-micro">
                    {categoryBenefits.filter(b => b.is_active).length} ativos
                  </Badge>
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                  ) : (
                    <ChevronRight className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                  )}
                </div>
              </div>

              {isExpanded && (
                <CardContent className="p-0">
                  {categoryBenefits.length === 0 ? (
                    <div className="p-3 text-center">
                      <Gift className="w-4 h-4 mx-auto lia-text-300 dark:lia-text-600 mb-2" />
                      <p className={textStyles.bodySmall}>
                        Nenhum benefício nesta categoria
                      </p>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-2 text-xs lia-text-700 hover:lia-text-900 dark:text-lia-text-secondary dark:hover:lia-text-50"
                        onClick={() => {
                          setEditingBenefit({ ...defaultBenefit, category: category.id })
                          setShowBenefitModal(true)
                        }}
                        disabled={!isEditingBenefits}
                      >
                        <Plus className="w-3.5 h-3.5 mr-1" />
                        Adicionar benefício
                      </Button>
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-100 dark:lia-divide-700">
                      {categoryBenefits.map((benefit) => (
                        <div
                          key={benefit.id}
                          className={`p-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors ${
                            !benefit.is_active ? 'opacity-60' : ''
                          }`}
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className={`${textStyles.subtitle} dark:text-lia-text-primary truncate`}>
                                {benefit.name}
                              </h4>
                              {benefit.is_highlighted && (
                                <Star className="w-3.5 h-3.5 text-status-warning fill-yellow-500" />
                              )}
                              {benefit.is_mandatory && (
                                <Badge variant="secondary" className="text-micro">Obrigatório</Badge>
                              )}
                              {benefit.is_discount && (
                                <Badge variant="outline" className="text-micro text-status-error border-status-error/30">Desconto</Badge>
                              )}
                            </div>
                            <p className={`${textStyles.description} truncate mb-1.5`}>
                              {benefit.description || 'Sem descrição'}
                            </p>
                            <div className="flex items-center gap-3 text-xs lia-text-600 dark:text-lia-text-tertiary">
                              <span className="flex items-center gap-1">
                                <DollarSign className="w-3.5 h-3.5" />
                                {formatBenefitValue(benefit)}
                              </span>
                              <span className="flex items-center gap-1">
                                <Users className="w-3.5 h-3.5" />
                                {getSeniorityLabel(benefit.seniority_levels)}
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="w-3.5 h-3.5" />
                                {getWaitingPeriodLabel(benefit.waiting_period_days)}
                              </span>
                              {benefit.provider && (
                                <span className="lia-text-600 dark:text-lia-text-tertiary">
                                  {benefit.provider}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-3 ml-3">
                            <Switch
                              checked={benefit.is_active}
                              onCheckedChange={() => handleToggleBenefitStatus(benefit)}
                              disabled={!isEditingBenefits}
                              className={!isEditingBenefits ? 'opacity-60' : ''}
                            />
                            {isEditingBenefits && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-7 w-7"
                                  onClick={() => {
                                    setEditingBenefit(benefit)
                                    setShowBenefitModal(true)
                                  }}
                                >
                                  <Pencil className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-7 w-7 text-status-error hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20 dark:hover:text-status-error"
                                  onClick={() => benefit.id && handleDeleteBenefit(benefit.id)}
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          )
        })}
      </div>

      <Dialog open={showBenefitModal} onOpenChange={setShowBenefitModal}>
        <DraggableDialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className={textStyles.h3}>
              {editingBenefit?.id ? 'Editar Benefício' : 'Novo Benefício'}
            </DialogTitle>
            <DialogDescription className={textStyles.description}>
              Preencha os dados do benefício abaixo
            </DialogDescription>
          </DialogHeader>

          {editingBenefit && (
            <div className="space-y-3 py-1.5">
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <Label htmlFor="name" className={textStyles.label}>Nome do Benefício *</Label>
                  <Input
                    id="name"
                    value={editingBenefit.name}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, name: e.target.value })}
                    placeholder="Ex: Plano de Saúde Bradesco"
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>

                <div className="col-span-2">
                  <Label htmlFor="description" className={textStyles.label}>Descrição</Label>
                  <Textarea
                    id="description"
                    value={editingBenefit.description}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, description: e.target.value })}
                    placeholder="Descreva os detalhes do benefício..."
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                    rows={2}
                  />
                </div>

                <div>
                  <Label className={textStyles.label}>Categoria *</Label>
                  <Select
                    value={editingBenefit.category}
                    onValueChange={(value) => setEditingBenefit({ ...editingBenefit, category: value })}
                  >
                    <SelectTrigger className="mt-1 rounded-md text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {BENEFIT_CATEGORIES.map((cat) => {
                        const Icon = cat.icon
                        return (
                          <SelectItem key={cat.id} value={cat.id} className="text-xs">
                            <div className="flex items-center gap-2">
                              <Icon className={`w-3.5 h-3.5 ${cat.color}`} />
                              <span>{cat.name}</span>
                            </div>
                          </SelectItem>
                        )
                      })}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className={textStyles.label}>Fornecedor/Operadora</Label>
                  <Input
                    value={editingBenefit.provider || ''}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, provider: e.target.value })}
                    placeholder="Ex: Bradesco Saúde"
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>

                <div>
                  <Label className={textStyles.label}>Tipo de Valor</Label>
                  <Select
                    value={editingBenefit.value_type}
                    onValueChange={(value) => setEditingBenefit({ ...editingBenefit, value_type: value })}
                  >
                    <SelectTrigger className="mt-1 rounded-md text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {VALUE_TYPES.map((type) => {
                        const Icon = type.icon
                        return (
                          <SelectItem key={type.id} value={type.id} className="text-xs">
                            <div className="flex items-center gap-2">
                              <Icon className="w-3.5 h-3.5" />
                              <span>{type.name}</span>
                            </div>
                          </SelectItem>
                        )
                      })}
                    </SelectContent>
                  </Select>
                </div>

                {editingBenefit.value_type === 'monetary' && (
                  <div>
                    <Label className={textStyles.label}>Valor (R$)</Label>
                    <Input
                      type="number"
                      value={editingBenefit.value || ''}
                      onChange={(e) => setEditingBenefit({ ...editingBenefit, value: parseFloat(e.target.value) || undefined })}
                      placeholder="0,00"
                      className="mt-1 rounded-full text-xs py-1.5 px-2"
                    />
                  </div>
                )}

                {editingBenefit.value_type === 'percentage' && (
                  <div>
                    <Label className={textStyles.label}>Percentual (%)</Label>
                    <Input
                      type="number"
                      value={editingBenefit.percentage_value || ''}
                      onChange={(e) => setEditingBenefit({ ...editingBenefit, percentage_value: parseFloat(e.target.value) || undefined })}
                      placeholder="0"
                      className="mt-1 rounded-full text-xs py-1.5 px-2"
                    />
                  </div>
                )}

                {editingBenefit.value_type === 'informative' && (
                  <div className="col-span-2">
                    <Label className={textStyles.label}>Detalhes do Valor</Label>
                    <Input
                      value={editingBenefit.value_details || ''}
                      onChange={(e) => setEditingBenefit({ ...editingBenefit, value_details: e.target.value })}
                      placeholder="Ex: Conforme política interna"
                      className="mt-1 rounded-full text-xs py-1.5 px-2"
                    />
                  </div>
                )}

                <div>
                  <Label className={textStyles.label}>Elegibilidade</Label>
                  <Select
                    value={editingBenefit.seniority_levels[0] || 'all'}
                    onValueChange={(value) => setEditingBenefit({ ...editingBenefit, seniority_levels: [value] })}
                  >
                    <SelectTrigger className="mt-1 rounded-md text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SENIORITY_LEVELS.map((level) => (
                        <SelectItem key={level.id} value={level.id} className="text-xs">
                          {level.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className={textStyles.label}>Período de Carência</Label>
                  <Select
                    value={String(editingBenefit.waiting_period_days)}
                    onValueChange={(value) => setEditingBenefit({ ...editingBenefit, waiting_period_days: parseInt(value) })}
                  >
                    <SelectTrigger className="mt-1 rounded-md text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {WAITING_PERIODS.map((period) => (
                        <SelectItem key={period.id} value={String(period.id)} className="text-xs">
                          {period.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="border-t border-lia-border-subtle dark:lia-border-800 pt-3 space-y-2">
                <h4 className={`${textStyles.labelSmall} uppercase tracking-wider`}>
                  Configurações
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center justify-between p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary">
                    <div>
                      <Label className={textStyles.label}>Ativo</Label>
                      <p className={textStyles.caption}>Disponível para colaboradores</p>
                    </div>
                    <Switch
                      checked={editingBenefit.is_active}
                      onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_active: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary">
                    <div>
                      <Label className={textStyles.label}>Destaque</Label>
                      <p className={textStyles.caption}>Exibir com destaque</p>
                    </div>
                    <Switch
                      checked={editingBenefit.is_highlighted}
                      onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_highlighted: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary">
                    <div>
                      <Label className={textStyles.label}>Obrigatório</Label>
                      <p className={textStyles.caption}>Adesão obrigatória</p>
                    </div>
                    <Switch
                      checked={editingBenefit.is_mandatory}
                      onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_mandatory: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary">
                    <div>
                      <Label className={textStyles.label}>Desconto em Folha</Label>
                      <p className={textStyles.caption}>Valor descontado do salário</p>
                    </div>
                    <Switch
                      checked={editingBenefit.is_discount}
                      onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_discount: checked })}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowBenefitModal(false)
                setEditingBenefit(null)
              }}
              className="rounded-md text-xs"
            >
              Cancelar
            </Button>
            <Button
              onClick={() => editingBenefit && handleSaveBenefit(editingBenefit)}
              disabled={isSaving || !editingBenefit?.name}
              className="rounded-md text-xs bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                  Salvando...
                </>
              ) : (
                editingBenefit?.id ? 'Salvar Alterações' : 'Criar Benefício'
              )}
            </Button>
          </DialogFooter>
        </DraggableDialogContent>
      </Dialog>

      <Dialog open={showTemplateModal} onOpenChange={setShowTemplateModal}>
        <DraggableDialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-hidden flex flex-col p-3">
          <DialogHeader className="flex-shrink-0 pb-2">
            <DialogTitle className={`flex items-center gap-2 ${textStyles.h3}`}>
              <Library className="w-4 h-4 lia-text-700 dark:text-lia-text-secondary" />
              Biblioteca de Benefícios
            </DialogTitle>
            <DialogDescription className={`${textStyles.description}`}>
              Selecione um benefício da lista para adicionar à sua empresa.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-shrink-0 space-y-2 py-1.5">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 lia-text-500 dark:text-lia-text-tertiary" />
                <Input
                  placeholder="Buscar benefício..."
                  value={templateSearch}
                  onChange={(e) => setTemplateSearch(e.target.value)}
                  className="pl-8 h-8 text-xs rounded-full py-1.5 px-2"
                />
              </div>
              <Select value={templateCategoryFilter} onValueChange={setTemplateCategoryFilter}>
                <SelectTrigger className="w-[180px] h-8 text-xs rounded-md">
                  <SelectValue placeholder="Todas categorias" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all" className="text-xs">Todas as categorias</SelectItem>
                  {BENEFIT_CATEGORIES.map((cat) => {
                    const Icon = cat.icon
                    return (
                      <SelectItem key={cat.id} value={cat.id} className="text-xs">
                        <div className="flex items-center gap-1.5">
                          <Icon className={`w-3.5 h-3.5 ${cat.color}`} />
                          <span>{cat.name}</span>
                        </div>
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
            </div>

            <div className={`flex items-center gap-2 ${textStyles.caption}`}>
              <span>{filteredTemplates.length} benefícios encontrados</span>
              {templateSearch && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="h-5 text-micro px-1.5"
                  onClick={() => { setTemplateSearch(""); setTemplateCategoryFilter("all"); }}
                >
                  Limpar
                </Button>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 py-1 pr-1 -mr-1">
            {isLoadingTemplates ? (
              <div className="flex items-center justify-center py-6">
                <div className="text-center">
                  <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2 lia-text-600 dark:text-lia-text-tertiary" />
                  <p className={`${textStyles.description}`}>Carregando...</p>
                </div>
              </div>
            ) : filteredTemplates.length === 0 ? (
              <div className="text-center py-6">
                <Gift className="w-4 h-4 mx-auto lia-text-300 dark:lia-text-600 mb-2" />
                <p className={`${textStyles.description}`}>
                  Nenhum benefício encontrado
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-1 h-6 text-xs lia-text-700 hover:lia-text-900 dark:text-lia-text-secondary dark:hover:lia-text-50"
                  onClick={() => { setTemplateSearch(""); setTemplateCategoryFilter("all"); }}
                >
                  Limpar filtros
                </Button>
              </div>
            ) : (
              BENEFIT_CATEGORIES.map((category) => {
                const catTemplates = templatesByCategory[category.id] || []
                if (catTemplates.length === 0) return null
                
                const CategoryIcon = category.icon
                
                return (
                  <div key={category.id} className="space-y-1.5">
                    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md ${category.bgColor}`}>
                      <CategoryIcon className={`w-3.5 h-3.5 ${category.color}`} />
                      <span className={`${textStyles.label}`}>
                        {category.name}
                      </span>
                      <Badge variant="secondary" className="text-micro h-4 px-1">
                        {catTemplates.length}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-1 gap-1">
                      {catTemplates.map((template) => {
                        const alreadyAdded = isTemplateAlreadyAdded(template.name)
                        return (
                          <div
                            key={template.id}
                            className={`p-2 border rounded-md cursor-pointer transition-colors ${
                              alreadyAdded 
                                ? 'bg-status-success/10 dark:bg-status-success/20 border-status-success/30 dark:border-status-success/30' 
                                : 'bg-white dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 dark:hover:border-gray-600 hover:'
                            }`}
                            onClick={() => !alreadyAdded && handleSelectTemplate(template)}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1.5">
                                  <h4 className={`${textStyles.label} truncate`}>
                                    {template.name}
                                  </h4>
                                  {template.is_popular && (
                                    <Star className="w-3 h-3 text-status-warning fill-yellow-500 flex-shrink-0" />
                                  )}
                                </div>
                                <p className={`${textStyles.caption} truncate`}>
                                  {template.description}
                                </p>
                              </div>
                              {alreadyAdded ? (
                                <div className="flex items-center gap-0.5 text-status-success text-micro flex-shrink-0">
                                  <Check className="w-3.5 h-3.5" />
                                </div>
                              ) : (
                                <Plus className="w-3.5 h-3.5 lia-text-400 dark:lia-text-500 flex-shrink-0" />
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })
            )}
          </div>

          <DialogFooter className="flex-shrink-0 border-t pt-3 mt-3">
            <div className="flex items-center justify-between w-full">
              <p className={`${textStyles.description}`}>
                Não encontrou? <Button variant="link" className={`h-auto p-0 ${textStyles.link}`} onClick={() => {
                  setShowTemplateModal(false)
                  setEditingBenefit({ ...defaultBenefit })
                  setShowBenefitModal(true)
                }}>Crie um benefício personalizado</Button>
              </p>
              <Button
                variant="outline"
                onClick={() => {
                  setShowTemplateModal(false)
                  setTemplateSearch("")
                  setTemplateCategoryFilter("all")
                }}
                className="rounded-md text-xs"
              >
                Fechar
              </Button>
            </div>
          </DialogFooter>
        </DraggableDialogContent>
      </Dialog>
    </div>
  )
}

export default BenefitsTab
