"use client"

import { formatBRL, CURRENCY_SYMBOL } from"@/lib/pricing"

import React, { useState, useCallback, useEffect } from"react"
import { useCompanyId } from"@/hooks/company/useCompanyId"
import { textStyles, cardStyles, badgeStyles, actionButtonStyles } from '@/lib/design-tokens'
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Switch } from"@/components/ui/switch"
import {
  Gift,
  Plus,
  Pencil,
  Trash2,
  ChevronDown,
  ChevronRight,
  CheckCircle,
  Loader2,
  X,
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
  DollarSign,
  Percent,
  Info,
} from"lucide-react"

import { LiaFieldToggle, defaultLiaFieldExamples } from"./LiaFieldToggle"
import { useCompanyLiaInstructions } from"@/hooks/company/use-company-lia-instructions"
import { BenefitItemCard } from"./benefits/BenefitItemCard"
import { BenefitFormModal } from"./benefits/BenefitFormModal"
import { BenefitTemplateModal } from"./benefits/BenefitTemplateModal"

const BENEFIT_CATEGORIES = [
  { id:"health", name:"Saúde & Bem-estar", icon: Stethoscope, color:"text-status-error", bgColor:"bg-status-error/10 dark:bg-status-error/20" },
  { id:"food", name:"Alimentação", icon: Utensils, color:"text-wedo-orange", bgColor:"bg-wedo-orange/10 dark:bg-wedo-orange/20" },
  { id:"transport", name:"Transporte", icon: Car, color:"text-lia-text-primary", bgColor:"bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
  { id:"education", name:"Educação & Desenvolvimento", icon: GraduationCap, color:"text-wedo-purple", bgColor:"bg-wedo-purple/10 dark:bg-wedo-purple/20" },
  { id:"financial", name:"Financeiro", icon: Wallet, color:"text-status-success", bgColor:"bg-status-success/10 dark:bg-status-success/20" },
  { id:"quality_life", name:"Qualidade de Vida", icon: Home, color:"text-lia-text-secondary", bgColor:"bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
  { id:"family", name:"Família", icon: Baby, color:"text-wedo-magenta", bgColor:"bg-wedo-magenta/10 dark:bg-wedo-magenta/20" },
  { id:"security", name:"Segurança", icon: Shield, color:"text-lia-text-primary", bgColor:"bg-lia-bg-secondary dark:bg-lia-bg-secondary/50" },
]

const SENIORITY_LEVELS = [
  { id:"all", name:"Todos os Níveis" },
  { id:"junior", name:"Júnior" },
  { id:"pleno", name:"Pleno" },
  { id:"senior", name:"Sênior" },
  { id:"coordinator", name:"Coordenação+" },
  { id:"manager", name:"Gerência+" },
  { id:"director", name:"Diretoria" },
  { id:"c-level", name:"C-Level" },
]

const VALUE_TYPES = [
  { id:"monetary", name:"Valor Monetário", icon: DollarSign, description: `Valor fixo em ${CURRENCY_SYMBOL}` },
  { id:"percentage", name:"Percentual", icon: Percent, description:"Porcentagem (ex: 5% contribuição)" },
  { id:"informative", name:"Informativo", icon: Info, description:"Apenas descrição, sem valor" },
]

const WAITING_PERIODS = [
  { id: 0, name:"Imediato" },
  { id: 30, name:"30 dias" },
  { id: 60, name:"60 dias" },
  { id: 90, name:"90 dias" },
  { id: 180, name:"6 meses" },
  { id: 365, name:"1 ano" },
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
  name:"",
  description:"",
  category:"health",
  value_type:"monetary",
  value: undefined,
  percentage_value: undefined,
  value_details:"",
  seniority_levels: ["all"],
  waiting_period_days: 0,
  is_mandatory: false,
  is_active: true,
  is_highlighted: false,
  is_discount: false,
  provider:"",
}

export function BenefitsTab() {
  const { companyId } = useCompanyId()
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liaToggles])

  const handleLiaInstructionSave = useCallback(async (fieldKey: string, instruction: string) => {
    const updatedInstructions = { ...liaInstructions, [fieldKey]: instruction }
    setLiaInstructions(updatedInstructions)
    await saveLiaFieldToggles(liaToggles, updatedInstructions)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liaInstructions, liaToggles])

  const getCompanyId = async (): Promise<string> => {
    if (companyId) return companyId
    try {
      const res = await fetch('/api/backend-proxy/company/profile')
      if (res.ok) {
        const company = await res.json()
        return company.id || ''
      }
    } catch (e) {
    }
    return ''
  }

  const saveLiaFieldToggles = async (toggles: Record<string, boolean>, instructions?: Record<string, string>) => {
    try {
      const companyId = await getCompanyId()
      const response = await fetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`, {
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

  const normalizeBenefit = (benefit: Record<string, unknown>): Benefit => ({
    ...benefit,
    name: String(benefit.name ||""),
    category: String(benefit.category ||"other"),
    description: String(benefit.description ||""),
    value_type: String(benefit.value_type ||"informative"),
    seniority_levels: Array.isArray(benefit.seniority_levels) 
      ? benefit.seniority_levels 
      : benefit.seniority_levels 
        ? [benefit.seniority_levels] 
        : ["all"],
    waiting_period_days: Number(benefit.waiting_period_days ?? 0),
    is_mandatory: Boolean(benefit.is_mandatory ?? false),
    is_active: Boolean(benefit.is_active ?? true),
    is_highlighted: Boolean(benefit.is_highlighted ?? false),
    is_discount: Boolean(benefit.is_discount ?? false),
    provider: String(benefit.provider ||""),
  })

  const loadBenefits = useCallback(async () => {
    setIsLoading(true)
    try {
      const cid = companyId || ''
      const response = await fetch(`/api/backend-proxy/company/benefits/?company_id=${encodeURIComponent(cid)}`)
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
  }, [companyId])

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
      description: template.description ||"",
      category: template.category,
      value_type:"informative",
      value: undefined,
      percentage_value: undefined,
      value_details:"",
      seniority_levels: ["all"],
      waiting_period_days: 0,
      is_mandatory: false,
      is_active: true,
      is_highlighted: template.is_popular,
      is_discount: false,
      provider:"",
    }
    
    try {
      const response = await fetch(`/api/backend-proxy/company/benefits/?company_id=${encodeURIComponent(companyId || '')}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newBenefit),
      })

      if (response.ok) {
        await loadBenefits()
        setSuccessMessage(`Benefício"${template.name}" adicionado com sucesso!`)
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
    const matchesSearch = templateSearch ==="" || 
      template.name.toLowerCase().includes(templateSearch.toLowerCase()) ||
      (template.description && template.description.toLowerCase().includes(templateSearch.toLowerCase()))
    const matchesCategory = templateCategoryFilter ==="all" || template.category === templateCategoryFilter
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
      const cid = encodeURIComponent(companyId || '')
      const url = benefit.id 
        ? `/api/backend-proxy/company/benefits/${benefit.id}?company_id=${cid}`
        : `/api/backend-proxy/company/benefits/?company_id=${cid}`
      
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
      const response = await fetch(`/api/backend-proxy/company/benefits/${benefitId}?company_id=${encodeURIComponent(companyId || '')}`, {
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
      const cid = encodeURIComponent(companyId || '')
      const savePromises = Array.from(pendingChanges.values()).map(benefit => 
        fetch(`/api/backend-proxy/company/benefits/${benefit.id}?company_id=${cid}`, {
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
    if (benefit.value_type ==="monetary" && benefit.value) {
      const prefix = benefit.is_discount ?"Desconto:" :""
      return `${prefix}${formatBRL(benefit.value)}`
    }
    if (benefit.value_type ==="percentage" && benefit.percentage_value) {
      return `${benefit.percentage_value}%`
    }
    if (benefit.value_type ==="informative") {
      return benefit.value_details ||"Informativo"
    }
    return"-"
  }

  const getSeniorityLabel = (levels: string[]) => {
    if (!levels || levels.length === 0 || levels.includes('all')) {
      return"Todos"
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
      <div className="space-y-3" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="text-center" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mx-auto mb-2 text-lia-text-secondary" />
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
          <h2 className={`${textStyles.titleLarge}`}>
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
            <span className="text-xs text-lia-text-secondary">Consumido pela LIA</span>
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
                    <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
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
            className="gap-1.5 rounded-xl text-xs border-lia-border-default text-lia-text-primary dark:border-lia-border-default hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover"
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
            className="gap-1.5 rounded-md text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
          >
            <Plus className="w-3.5 h-3.5" />
            Novo Benefício
          </Button>
        </div>
      </div>

      <div className="space-y-3">
        {BENEFIT_CATEGORIES.map((category) => {
          const categoryBenefits = getBenefitsByCategory(category.id)
          const isExpanded = expandedCategories.includes(category.id)
          const CategoryIcon = category.icon

          return (
            <Card key={category.id} className={`${cardStyles.default} dark:border-lia-border-subtle/50 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md overflow-hidden`}>
              <div
                className={`flex items-center justify-between p-3 cursor-pointer transition-colors motion-reduce:transition-none ${category.bgColor}`}
                onClick={() => toggleCategory(category.id)}
              >
                <div className="flex items-center gap-2">
                  <div className={`p-1.5 rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary`}>
                    <CategoryIcon className={`w-4 h-4 ${category.color}`} />
                  </div>
                  <div>
                    <h3 className={`${textStyles.title}`}>
                      {category.name}
                    </h3>
                    <p className={textStyles.caption}>
                      {categoryBenefits.length} {categoryBenefits.length === 1 ? 'benefício' : 'benefícios'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Chip variant="neutral" className="text-micro">
                    {categoryBenefits.filter(b => b.is_active).length} ativos
                  </Chip>
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-lia-text-secondary" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-lia-text-secondary" />
                  )}
                </div>
              </div>

              {isExpanded && (
                <CardContent className="p-0">
                  {categoryBenefits.length === 0 ? (
                    <div className="p-3 text-center">
                      <Gift className="w-4 h-4 mx-auto text-lia-text-disabled mb-2" />
                      <p className={textStyles.bodySmall}>
                        Nenhum benefício nesta categoria
                      </p>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-2 text-xs text-lia-text-primary hover:text-lia-text-primary"
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
                    <div className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                      {categoryBenefits.map((benefit) => (
                        <BenefitItemCard
                          key={benefit.id}
                          benefit={benefit}
                          isEditingBenefits={isEditingBenefits}
                          onToggleStatus={handleToggleBenefitStatus}
                          onEdit={(b) => { setEditingBenefit(b); setShowBenefitModal(true) }}
                          onDelete={handleDeleteBenefit}
                        />
                      ))}
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          )
        })}
      </div>

      <BenefitFormModal
        open={showBenefitModal}
        onOpenChange={setShowBenefitModal}
        editingBenefit={editingBenefit}
        setEditingBenefit={setEditingBenefit}
        isSaving={isSaving}
        onSave={handleSaveBenefit}
      />

      <BenefitTemplateModal
        open={showTemplateModal}
        onOpenChange={setShowTemplateModal}
        templates={templates}
        isLoadingTemplates={isLoadingTemplates}
        templateSearch={templateSearch}
        setTemplateSearch={setTemplateSearch}
        templateCategoryFilter={templateCategoryFilter}
        setTemplateCategoryFilter={setTemplateCategoryFilter}
        filteredTemplates={filteredTemplates}
        templatesByCategory={templatesByCategory}
        isTemplateAlreadyAdded={isTemplateAlreadyAdded}
        onSelectTemplate={handleSelectTemplate}
        onOpenBenefitModal={() => {
          setEditingBenefit({ ...defaultBenefit })
          setShowBenefitModal(true)
        }}
      />
    </div>
  )
}

export default BenefitsTab
