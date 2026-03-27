"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog"
import { 
  Building2, 
  Users, 
  Gift, 
  Heart, 
  Upload, 
  Plus, 
  Pencil, 
  Trash2,
  ChevronDown,
  ChevronRight,
  Brain,
  FileSpreadsheet,
  DollarSign,
  Percent,
  Info,
  CheckCircle,
  Loader2,
  GripVertical,
  Utensils,
  Car,
  GraduationCap,
  Wallet,
  Home,
  Baby,
  Stethoscope,
  Shield,
  Library,
  Search,
  Check,
  Star,
  X,
  Linkedin,
  Globe,
  MapPin,
  Building,
  Save
} from "lucide-react"

const BENEFIT_CATEGORIES = [
  { id: "health", name: "Saúde & Bem-estar", icon: Stethoscope, color: "text-status-error" },
  { id: "food", name: "Alimentação", icon: Utensils, color: "text-wedo-orange" },
  { id: "transport", name: "Transporte", icon: Car, color: "text-gray-600 dark:text-gray-400" },
  { id: "education", name: "Educação & Desenvolvimento", icon: GraduationCap, color: "text-wedo-purple" },
  { id: "financial", name: "Financeiro", icon: Wallet, color: "text-status-success" },
  { id: "quality_life", name: "Qualidade de Vida", icon: Home, color: "text-gray-700 dark:text-gray-300" },
  { id: "family", name: "Família", icon: Baby, color: "text-wedo-magenta" },
  { id: "security", name: "Segurança", icon: Shield, color: "text-gray-500" },
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
  icon?: string
  value?: number
  value_type: string
  value_details?: string
  percentage_value?: number
  applicable_to: string[]
  seniority_levels: string[]
  contract_types: string[]
  departments: string[]
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean
  provider?: string
  order: number
}

interface CompanyProfile {
  id?: string
  name: string
  trading_name?: string
  website?: string
  cnpj?: string
  industry?: string
  sector?: string
  company_size?: string
  description?: string
  headquarters_city?: string
  headquarters_state?: string
  linkedin_url?: string
  mission?: string
  vision?: string
  values?: string
  tagline?: string
  additional_data?: Record<string, any>
}

interface EnrichmentResult {
  success: boolean
  linkedin_data: Record<string, any>
  glassdoor_data: Record<string, any>
  enriched_culture: Record<string, any>
  errors: string[]
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

interface EVPPillar {
  name: string
  description: string
  evidence: string
}

interface EVPAnalysis {
  statement: string
  pillars: EVPPillar[]
  tone_guidance: string[]
  candidate_promise: string
  generated_at: string
  sources: string[]
}

const defaultBenefit: Benefit = {
  name: "",
  description: "",
  category: "health",
  value_type: "monetary",
  value: undefined,
  percentage_value: undefined,
  value_details: "",
  applicable_to: [],
  seniority_levels: ["all"],
  contract_types: [],
  departments: [],
  waiting_period_days: 0,
  is_mandatory: false,
  is_active: true,
  is_highlighted: false,
  is_discount: false,
  provider: "",
  order: 0,
}

interface BenefitsContentProps {
  isLoading: boolean
  benefits: Benefit[]
  expandedCategories: string[]
  showImportModal: boolean
  setShowImportModal: (show: boolean) => void
  setShowTemplateModal: (show: boolean) => void
  setEditingBenefit: (benefit: Benefit | null) => void
  setShowBenefitModal: (show: boolean) => void
  toggleCategory: (categoryId: string) => void
  handleToggleBenefitStatus: (benefit: Benefit) => void
  handleDeleteBenefit: (id: string) => void
  defaultBenefit: Benefit
}

function BenefitsContent({
  isLoading,
  benefits,
  expandedCategories,
  setShowImportModal,
  setShowTemplateModal,
  setEditingBenefit,
  setShowBenefitModal,
  toggleCategory,
  handleToggleBenefitStatus,
  handleDeleteBenefit,
  defaultBenefit,
}: BenefitsContentProps) {
  console.log("[BenefitsContent] Rendering - isLoading:", isLoading, "benefits.length:", benefits.length)
  
  const renderingBranch = isLoading ? "LOADING" : benefits.length === 0 ? "EMPTY" : "LIST"
  console.log("[BenefitsContent] Rendering branch:", renderingBranch)
  
  if (!isLoading && benefits.length > 0) {
    console.log("[BenefitsContent] Benefits data:", JSON.stringify(benefits.map(b => ({ name: b.name, category: b.category }))))
  }

  const getBenefitsByCategory = (categoryId: string) => {
    return benefits.filter(b => b.category === categoryId)
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
            Benefícios da Empresa
          </h2>
          <p className="text-sm mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>
            Configure os benefícios oferecidos aos colaboradores
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => setShowImportModal(true)}
            className="gap-2"
          >
            <Upload className="w-4 h-4" />
            Importar com LIA
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowTemplateModal(true)}
            className="gap-2 border-gray-300"
          >
            <Library className="w-4 h-4" />
            Adicionar da Lista
          </Button>
          <Button
            onClick={() => {
              setEditingBenefit({ ...defaultBenefit })
              setShowBenefitModal(true)
            }}
            className="gap-2 bg-gray-800"
          >
            <Plus className="w-4 h-4" />
            Adicionar Benefício
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : benefits.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Gift className="w-12 h-12 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium mb-2" style={{ color: 'var(--eleven-text-primary)' }}>
              Nenhum benefício cadastrado
            </h3>
            <p className="text-sm text-center mb-4" style={{ color: 'var(--eleven-text-secondary)' }}>
              Comece importando uma planilha ou adicionando benefícios manualmente
            </p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowImportModal(true)} className="gap-2">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Importar com LIA
              </Button>
              <Button 
                onClick={() => {
                  setEditingBenefit({ ...defaultBenefit })
                  setShowBenefitModal(true)
                }}
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                Adicionar Manual
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {BENEFIT_CATEGORIES.map(category => {
            const categoryBenefits = getBenefitsByCategory(category.id)
            if (categoryBenefits.length === 0) return null
            
            const isExpanded = expandedCategories.includes(category.id)
            const CategoryIcon = category.icon
            
            return (
              <Card key={category.id}>
                <div 
                  className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  onClick={() => toggleCategory(category.id)}
                >
                  <div className="flex items-center gap-3">
                    <CategoryIcon className={`w-5 h-5 ${category.color}`} />
                    <span className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                      {category.name}
                    </span>
                    <Badge variant="secondary" className="text-xs">
                      {categoryBenefits.length}
                    </Badge>
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  )}
                </div>
                
                {isExpanded && (
                  <div className="border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                    {categoryBenefits.map(benefit => (
                      <div 
                        key={benefit.id}
                        className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 border-b last:border-b-0"
                        style={{ borderColor: 'var(--eleven-border-subtle)' }}
                      >
                        <div className="flex items-center gap-3 flex-1">
                          <GripVertical className="w-4 h-4 text-gray-300 cursor-grab" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                                {benefit.name}
                              </span>
                              {benefit.is_highlighted && (
                                <Badge className="text-xs bg-status-warning/15 text-status-warning dark:bg-status-warning dark:text-status-warning">
                                  Destaque
                                </Badge>
                              )}
                              {!benefit.is_active && (
                                <Badge variant="secondary" className="text-xs">
                                  Inativo
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-4 mt-1">
                              <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                                {formatBenefitValue(benefit)}
                              </span>
                              <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                                {benefit.seniority_levels?.includes("all") 
                                  ? "Todos os níveis" 
                                  : benefit.seniority_levels?.map(l => SENIORITY_LEVELS.find(s => s.id === l)?.name).join(", ") || "Todos os níveis"}
                              </span>
                              {benefit.waiting_period_days > 0 && (
                                <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                                  Carência: {WAITING_PERIODS.find(w => w.id === benefit.waiting_period_days)?.name || `${benefit.waiting_period_days} dias`}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch 
                            checked={benefit.is_active} 
                            onCheckedChange={() => handleToggleBenefitStatus(benefit)}
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingBenefit(benefit)
                              setShowBenefitModal(true)
                            }}
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => benefit.id && handleDeleteBenefit(benefit.id)}
                            className="text-status-error hover:text-status-error"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

function SetupEmpresaContent() {
  const [mounted, setMounted] = useState(false)
  const [activeTab, setActiveTab] = useState("profile")
  const [benefits, setBenefits] = useState<Benefit[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [showBenefitModal, setShowBenefitModal] = useState(false)
  const [editingBenefit, setEditingBenefit] = useState<Benefit | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<string[]>(BENEFIT_CATEGORIES.map(c => c.id))
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile>({ name: "" })
  const [departments, setDepartments] = useState<{id: string, name: string}[]>([])
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [templates, setTemplates] = useState<BenefitTemplate[]>([])
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false)
  const [templateSearch, setTemplateSearch] = useState("")
  const [templateCategoryFilter, setTemplateCategoryFilter] = useState<string>("all")
  const [isEnriching, setIsEnriching] = useState(false)
  const [enrichmentError, setEnrichmentError] = useState<string | null>(null)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [isGeneratingEvp, setIsGeneratingEvp] = useState(false)
  const [evpData, setEvpData] = useState<EVPAnalysis | null>(null)
  const [evpError, setEvpError] = useState<string | null>(null)
  
  useEffect(() => {
    setMounted(true)
  }, [])

  const loadBenefits = useCallback(async () => {
    console.log("[BenefitsTab] Starting loadBenefits...")
    try {
      const response = await fetch('/api/backend-proxy/company/benefits/')
      console.log("[BenefitsTab] Response status:", response.status, response.ok)
      if (response.ok) {
        const data = await response.json()
        console.log("[BenefitsTab] Data received:", data)
        const items = Array.isArray(data) ? data : data.items || []
        console.log("[BenefitsTab] Setting benefits:", items.length, "items")
        setBenefits(items)
      } else {
        console.error("[BenefitsTab] Response not OK:", response.status)
      }
    } catch (error) {
      console.error("[BenefitsTab] Error loading benefits:", error)
    } finally {
      console.log("[BenefitsTab] Setting isLoading to false")
      setIsLoading(false)
    }
  }, [])

  const loadCompanyProfile = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/company/profile/')
      if (response.ok) {
        const data = await response.json()
        const additionalData = data.additional_data || {}
        setCompanyProfile({
          ...data,
          mission: additionalData.mission || '',
          vision: additionalData.vision || '',
          values: additionalData.values || '',
          tagline: additionalData.tagline || ''
        })
        if (additionalData.evp_analysis) {
          setEvpData(additionalData.evp_analysis)
        }
      }
    } catch (error) {
      console.error("Error loading company profile:", error)
    }
  }, [])

  const loadDepartments = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/company/departments/')
      if (response.ok) {
        const data = await response.json()
        setDepartments(Array.isArray(data) ? data : data.items || [])
      }
    } catch (error) {
      console.error("Error loading departments:", error)
    }
  }, [])

  const handleEnrichProfile = useCallback(async () => {
    if (!companyProfile.linkedin_url) {
      setEnrichmentError("Por favor, insira a URL do LinkedIn da empresa")
      return
    }
    
    setIsEnriching(true)
    setEnrichmentError(null)
    
    try {
      const response = await fetch('/api/backend-proxy/company/enrich', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          linkedin_url: companyProfile.linkedin_url,
          glassdoor_company_name: companyProfile.name || undefined
        })
      })
      
      if (response.ok) {
        const data: EnrichmentResult = await response.json()
        
        if (data.success) {
          const updates: Partial<CompanyProfile> = {}
          
          if (data.enriched_culture.company_description) {
            updates.description = data.enriched_culture.company_description
          }
          if (data.enriched_culture.tagline) {
            updates.tagline = data.enriched_culture.tagline
          }
          if (data.enriched_culture.mission) {
            updates.mission = data.enriched_culture.mission
          }
          if (data.enriched_culture.vision) {
            updates.vision = data.enriched_culture.vision
          }
          if (data.linkedin_data.website) {
            updates.website = data.linkedin_data.website
          }
          if (data.linkedin_data.industries?.length > 0) {
            updates.industry = Array.isArray(data.linkedin_data.industries) 
              ? data.linkedin_data.industries[0] 
              : data.linkedin_data.industries
          }
          if (data.linkedin_data.company_size) {
            updates.company_size = String(data.linkedin_data.company_size)
          }
          
          const hq = data.linkedin_data.headquarters
          if (hq) {
            if (typeof hq === 'string') {
              updates.headquarters_city = hq
            } else if (typeof hq === 'object') {
              if (hq.city) updates.headquarters_city = hq.city
              if (hq.state) updates.headquarters_state = hq.state
              else if (hq.geographicArea) updates.headquarters_state = hq.geographicArea
            }
          }
          
          if (data.enriched_culture.culture_highlights && Array.isArray(data.enriched_culture.culture_highlights)) {
            updates.values = data.enriched_culture.culture_highlights.slice(0, 5).join('\n')
          }
          
          setCompanyProfile(prev => {
            const newProfile = { ...prev, ...updates }
            setTimeout(async () => {
              if (newProfile.id) {
                const { mission, vision, values, tagline, ...baseFields } = newProfile
                const existingAdditionalData = baseFields.additional_data || {}
                const profileData = {
                  ...baseFields,
                  additional_data: {
                    ...existingAdditionalData,
                    ...data.enriched_culture,
                    mission,
                    vision,
                    values,
                    tagline
                  }
                }
                try {
                  const saveRes = await fetch(`/api/backend-proxy/company/profile/${newProfile.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(profileData)
                  })
                  if (saveRes.ok) {
                    const evpRes = await fetch(`/api/backend-proxy/company/profile/${newProfile.id}/generate-evp`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' }
                    })
                    if (evpRes.ok) {
                      const evpResult = await evpRes.json()
                      if (evpResult.success && evpResult.evp_analysis) {
                        setEvpData(evpResult.evp_analysis)
                      }
                    }
                  }
                } catch (e) {
                  console.error("Error auto-generating EVP:", e)
                }
              }
            }, 100)
            return newProfile
          })
          
          if (data.errors.length > 0) {
            setEnrichmentError(`Enriquecimento parcial: ${data.errors.join(', ')}`)
          }
        } else {
          setEnrichmentError(data.errors.join(', ') || 'Falha ao enriquecer perfil')
        }
      } else {
        const errorData = await response.json().catch(() => ({}))
        setEnrichmentError(errorData.detail || 'Erro ao conectar com o serviço de enriquecimento')
      }
    } catch (error) {
      console.error("Error enriching profile:", error)
      setEnrichmentError('Erro ao processar enriquecimento. Tente novamente.')
    } finally {
      setIsEnriching(false)
    }
  }, [companyProfile.linkedin_url, companyProfile.name])

  const handleSaveProfile = useCallback(async () => {
    setIsSavingProfile(true)
    try {
      const url = companyProfile.id 
        ? `/api/backend-proxy/company/profile/${companyProfile.id}`
        : '/api/backend-proxy/company/profile'
      
      const { mission, vision, values, tagline, ...baseFields } = companyProfile
      const existingAdditionalData = baseFields.additional_data || {}
      const profileData = {
        ...baseFields,
        additional_data: {
          ...existingAdditionalData,
          mission,
          vision,
          values,
          tagline
        }
      }
      
      const response = await fetch(url, {
        method: companyProfile.id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData)
      })
      
      if (response.ok) {
        const data = await response.json()
        const additionalData = data.additional_data || {}
        setCompanyProfile({
          ...data,
          mission: additionalData.mission || '',
          vision: additionalData.vision || '',
          values: additionalData.values || '',
          tagline: additionalData.tagline || ''
        })
      } else {
        console.error("Error saving profile:", response.status)
      }
    } catch (error) {
      console.error("Error saving profile:", error)
    } finally {
      setIsSavingProfile(false)
    }
  }, [companyProfile])

  const handleGenerateEvp = useCallback(async (profileId?: string) => {
    const id = profileId || companyProfile.id
    if (!id) {
      setEvpError("Salve o perfil da empresa primeiro")
      return
    }
    
    setIsGeneratingEvp(true)
    setEvpError(null)
    
    try {
      const response = await fetch(`/api/backend-proxy/company/profile/${id}/generate-evp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.evp_analysis) {
          setEvpData(data.evp_analysis)
        } else {
          setEvpError(data.error || 'Falha ao gerar análise EVP')
        }
      } else {
        const errorData = await response.json().catch(() => ({}))
        setEvpError(errorData.detail || 'Erro ao conectar com o serviço')
      }
    } catch (error) {
      console.error("Error generating EVP:", error)
      setEvpError('Erro ao processar geração de EVP')
    } finally {
      setIsGeneratingEvp(false)
    }
  }, [companyProfile.id])

  useEffect(() => {
    let cancelled = false
    
    const fetchData = async () => {
      console.log("[SetupEmpresa] Loading data...")
      
      try {
        const benefitsResponse = await fetch('/api/backend-proxy/company/benefits/')
        console.log("[SetupEmpresa] Benefits response:", benefitsResponse.status)
        
        if (!cancelled && benefitsResponse.ok) {
          const data = await benefitsResponse.json()
          console.log("[SetupEmpresa] Benefits data:", data)
          const items = Array.isArray(data) ? data : data.items || []
          console.log("[SetupEmpresa] Setting", items.length, "benefits")
          setBenefits(items)
        }
      } catch (error) {
        console.error("[SetupEmpresa] Error fetching benefits:", error)
      } finally {
        if (!cancelled) {
          console.log("[SetupEmpresa] Setting isLoading to false")
          setIsLoading(false)
        }
      }
      
      loadCompanyProfile()
      loadDepartments()
    }
    
    fetchData()
    
    return () => {
      cancelled = true
    }
  }, [loadCompanyProfile, loadDepartments])

  const loadTemplates = useCallback(async (): Promise<number> => {
    setIsLoadingTemplates(true)
    try {
      const response = await fetch('/api/backend-proxy/benefits/templates')
      if (response.ok) {
        const data = await response.json()
        const items = data.items || []
        setTemplates(items)
        return items.length
      }
      return 0
    } catch (err) {
      console.error("Error loading templates:", err)
      return 0
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
      console.error("Error seeding templates:", err)
    }
  }, [loadTemplates])

  useEffect(() => {
    if (showTemplateModal && templates.length === 0) {
      loadTemplates().then((count) => {
        if (count === 0) {
          seedTemplates()
        }
      })
    }
  }, [showTemplateModal, templates.length, loadTemplates, seedTemplates])

  const handleSelectTemplate = (template: BenefitTemplate) => {
    const newBenefit: Benefit = {
      name: template.name,
      description: template.description || "",
      category: template.category,
      value_type: "monetary",
      value: undefined,
      percentage_value: undefined,
      value_details: "",
      applicable_to: [],
      seniority_levels: ["all"],
      contract_types: [],
      departments: [],
      waiting_period_days: 0,
      is_mandatory: false,
      is_active: true,
      is_highlighted: false,
      is_discount: false,
      provider: "",
      order: 0,
    }
    setEditingBenefit(newBenefit)
    setShowTemplateModal(false)
    setShowBenefitModal(true)
    setTemplateSearch("")
    setTemplateCategoryFilter("all")
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
      }
    } catch (error) {
      console.error("Error saving benefit:", error)
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
      }
    } catch (error) {
      console.error("Error deleting benefit:", error)
    }
  }

  const handleToggleBenefitStatus = async (benefit: Benefit) => {
    if (!benefit.id) return
    try {
      const response = await fetch(`/api/backend-proxy/company/benefits/${benefit.id}?company_id=default`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...benefit, is_active: !benefit.is_active }),
      })
      if (response.ok) {
        await loadBenefits()
      }
    } catch (error) {
      console.error("Error toggling benefit status:", error)
    }
  }

  const handleImportFile = async () => {
    if (!importFile) return
    
    setIsImporting(true)
    try {
      const formData = new FormData()
      formData.append('file', importFile)
      
      const response = await fetch('/api/backend-proxy/company/benefits/import?company_id=default', {
        method: 'POST',
        body: formData,
      })
      
      if (response.ok) {
        await loadBenefits()
        setShowImportModal(false)
        setImportFile(null)
      }
    } catch (error) {
      console.error("Error importing benefits:", error)
    } finally {
      setIsImporting(false)
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

  const getCategoryIcon = (categoryId: string) => {
    const cat = BENEFIT_CATEGORIES.find(c => c.id === categoryId)
    return cat ? cat.icon : Gift
  }

  const getCategoryColor = (categoryId: string) => {
    const cat = BENEFIT_CATEGORIES.find(c => c.id === categoryId)
    return cat ? cat.color : "text-gray-500"
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

  if (!mounted) {
    return (
      <div className="p-8" suppressHydrationWarning>
        <div className="mb-8">
          <h1
            className="text-3xl font-semibold mb-2"
            style={{ color: 'var(--eleven-text-primary)' }}
          >
            Setup Empresa
          </h1>
          <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
            Configure as informações da empresa, departamentos, benefícios e cultura organizacional
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1
          className="text-3xl font-semibold mb-2"
          style={{ color: 'var(--eleven-text-primary)' }}
        >
          Setup Empresa
        </h1>
        <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
          Configure as informações da empresa, departamentos, benefícios e cultura organizacional
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="profile" className="gap-2">
            <Building2 className="w-4 h-4" />
            Perfil
          </TabsTrigger>
          <TabsTrigger value="departments" className="gap-2">
            <Users className="w-4 h-4" />
            Departamentos
          </TabsTrigger>
          <TabsTrigger value="benefits" className="gap-2">
            <Gift className="w-4 h-4" />
            Benefícios
          </TabsTrigger>
          <TabsTrigger value="culture" className="gap-2">
            <Heart className="w-4 h-4" />
            Cultura
          </TabsTrigger>
        </TabsList>

        {activeTab === "profile" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Perfil da Empresa</CardTitle>
                    <CardDescription>Informações gerais da organização</CardDescription>
                  </div>
                  <Button
                    onClick={handleSaveProfile}
                    disabled={isSavingProfile}
                    className="gap-2 bg-gray-800"
                  >
                    {isSavingProfile ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Salvando...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        Salvar Perfil
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Nome da Empresa *</Label>
                    <Input
                      value={companyProfile.name}
                      onChange={e => setCompanyProfile({ ...companyProfile, name: e.target.value })}
                      placeholder="Ex: WeDo Talent"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Nome Fantasia</Label>
                    <Input
                      value={companyProfile.trading_name || ""}
                      onChange={e => setCompanyProfile({ ...companyProfile, trading_name: e.target.value })}
                      placeholder="Ex: WeDo"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>CNPJ</Label>
                    <Input
                      value={companyProfile.cnpj || ""}
                      onChange={e => setCompanyProfile({ ...companyProfile, cnpj: e.target.value })}
                      placeholder="00.000.000/0000-00"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-gray-500" />
                      Website
                    </Label>
                    <Input
                      value={companyProfile.website || ""}
                      onChange={e => setCompanyProfile({ ...companyProfile, website: e.target.value })}
                      placeholder="https://www.empresa.com.br"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Setor/Indústria</Label>
                    <Input
                      value={companyProfile.industry || ""}
                      onChange={e => setCompanyProfile({ ...companyProfile, industry: e.target.value })}
                      placeholder="Ex: Tecnologia, Varejo, Saúde"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <Building className="w-4 h-4 text-gray-500" />
                      Porte da Empresa
                    </Label>
                    <Select
                      value={companyProfile.company_size || ""}
                      onValueChange={value => setCompanyProfile({ ...companyProfile, company_size: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione o porte" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1-10">1-10 funcionários</SelectItem>
                        <SelectItem value="11-50">11-50 funcionários</SelectItem>
                        <SelectItem value="51-200">51-200 funcionários</SelectItem>
                        <SelectItem value="201-500">201-500 funcionários</SelectItem>
                        <SelectItem value="501-1000">501-1000 funcionários</SelectItem>
                        <SelectItem value="1001-5000">1001-5000 funcionários</SelectItem>
                        <SelectItem value="5001+">5001+ funcionários</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-gray-500" />
                      Cidade (Sede)
                    </Label>
                    <Input
                      value={companyProfile.headquarters_city || ""}
                      onChange={e => setCompanyProfile({ ...companyProfile, headquarters_city: e.target.value })}
                      placeholder="Ex: São Paulo"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Estado</Label>
                    <Input
                      value={companyProfile.headquarters_state || ""}
                      onChange={e => setCompanyProfile({ ...companyProfile, headquarters_state: e.target.value })}
                      placeholder="Ex: SP"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Descrição da Empresa</Label>
                  <Textarea
                    value={companyProfile.description || ""}
                    onChange={e => setCompanyProfile({ ...companyProfile, description: e.target.value })}
                    placeholder="Descreva a empresa, seus produtos/serviços e diferenciais..."
                    rows={4}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-wedo-cyan" />
                  Enriquecimento com IA
                </CardTitle>
                <CardDescription>
                  Preencha automaticamente os dados da empresa usando LinkedIn e Glassdoor
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-4 items-end">
                  <div className="flex-1 space-y-2">
                    <Label className="flex items-center gap-2">
                      <Linkedin className="w-4 h-4 text-[#0077B5]" />
                      URL do LinkedIn da Empresa
                    </Label>
                    <Input
                      value={companyProfile.linkedin_url || ""}
                      onChange={e => setCompanyProfile({ ...companyProfile, linkedin_url: e.target.value })}
                      placeholder="https://www.linkedin.com/company/nome-da-empresa"
                    />
                  </div>
                  <Button
                    onClick={handleEnrichProfile}
                    disabled={isEnriching || !companyProfile.linkedin_url}
                    className="gap-2 h-10 bg-gray-900"
                  >
                    {isEnriching ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Enriquecendo...
                      </>
                    ) : (
                      <>
                        <Brain className="w-4 h-4 text-wedo-cyan" />
                        Enriquecer com IA
                      </>
                    )}
                  </Button>
                </div>

                {enrichmentError && (
                  <div className="bg-status-error/10 dark:bg-status-error/20 border border-status-error/30 dark:border-status-error/30 rounded-md p-3">
                    <p className="text-sm text-status-error dark:text-status-error">{enrichmentError}</p>
                  </div>
                )}

 <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4">
                  <div className="flex items-start gap-3">
                    <Brain className="w-5 h-5 text-wedo-cyan mt-0.5" />
                    <div>
 <p className="text-sm font-medium text-gray-9000">
                        A LIA irá buscar e preencher automaticamente:
                      </p>
 <ul className="text-xs text-gray-900 dark:text-gray-300 mt-2 space-y-1">
                        <li>• Descrição e tagline da empresa</li>
                        <li>• Setor, porte e localização</li>
                        <li>• Missão, visão e valores (via Glassdoor)</li>
                        <li>• Avaliações e cultura organizacional</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cultura e Valores</CardTitle>
                <CardDescription>Missão, visão e valores organizacionais</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Tagline / Slogan</Label>
                  <Input
                    value={companyProfile.tagline || ""}
                    onChange={e => setCompanyProfile({ ...companyProfile, tagline: e.target.value })}
                    placeholder="Ex: Conectando talentos ao sucesso"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Missão</Label>
                  <Textarea
                    value={companyProfile.mission || ""}
                    onChange={e => setCompanyProfile({ ...companyProfile, mission: e.target.value })}
                    placeholder="Qual é a razão de existir da empresa?"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Visão</Label>
                  <Textarea
                    value={companyProfile.vision || ""}
                    onChange={e => setCompanyProfile({ ...companyProfile, vision: e.target.value })}
                    placeholder="Onde a empresa quer chegar?"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Valores</Label>
                  <Textarea
                    value={companyProfile.values || ""}
                    onChange={e => setCompanyProfile({ ...companyProfile, values: e.target.value })}
                    placeholder="Quais são os valores que guiam a empresa?"
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-gray-700" />
                  EVP Insights
                </CardTitle>
                <CardDescription>
                  Análise de Employee Value Proposition gerada por IA
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {evpError && (
                  <div className="bg-status-error/10 dark:bg-status-error/20 border border-status-error/30 dark:border-status-error/30 rounded-md p-3">
                    <p className="text-sm text-status-error dark:text-status-error">{evpError}</p>
                  </div>
                )}

                {!evpData ? (
                  <div className="text-center py-8">
                    <Star className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-sm mb-4" style={{ color: 'var(--eleven-text-secondary)' }}>
                      Nenhuma análise EVP gerada ainda. Enriqueça o perfil com LinkedIn/Glassdoor ou clique para gerar manualmente.
                    </p>
                    <Button
                      onClick={() => handleGenerateEvp()}
                      disabled={isGeneratingEvp || !companyProfile.id}
                      className="gap-2 bg-gray-900"
                    >
                      {isGeneratingEvp ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Gerando EVP...
                        </>
                      ) : (
                        <>
                          <Brain className="w-4 h-4 text-wedo-cyan" />
                          Gerar EVP
                        </>
                      )}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="bg-gradient-to-r from-gray-100 dark:from-gray-800 to-blue-50 dark:from-gray-900 dark:from-gray-50/20 dark:to-blue-900/20 rounded-md p-4 border border border-gray-300">
                      <p className="text-lg font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                        "{evpData.statement}"
                      </p>
                    </div>

                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                        <Building2 className="w-4 h-4 text-gray-700" />
                        Pilares do EVP
                      </h4>
                      <div className="grid gap-3">
                        {evpData.pillars.map((pillar, idx) => (
                          <div key={idx} className="bg-white dark:bg-gray-800 border rounded-md p-4" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                            <div className="flex items-start gap-3">
                              <Badge className="shrink-0 bg-gray-900" style={{ color: 'white' }}>
                                {pillar.name}
                              </Badge>
                              <div className="flex-1">
                                <p className="text-sm mb-2" style={{ color: 'var(--eleven-text-primary)' }}>
                                  {pillar.description}
                                </p>
                                <p className="text-xs italic" style={{ color: 'var(--eleven-text-tertiary)' }}>
                                  Evidência: {pillar.evidence}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                        <Heart className="w-4 h-4 text-gray-700" />
                        Tom de Comunicação
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {evpData.tone_guidance.map((tone, idx) => (
                          <Badge key={idx} variant="outline" className="border-gray-300">
                            {tone}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-4">
                      <h4 className="font-medium mb-2 flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                        <Users className="w-4 h-4 text-gray-700" />
                        Promessa ao Candidato
                      </h4>
                      <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                        {evpData.candidate_promise}
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                      <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        <span>Fontes: {evpData.sources.join(', ')}</span>
                        <span>•</span>
                        <span>Gerado em: {new Date(evpData.generated_at).toLocaleDateString('pt-BR')}</span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleGenerateEvp()}
                        disabled={isGeneratingEvp}
                        className="gap-2 border-gray-300"
                      >
                        {isGeneratingEvp ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Brain className="w-3 h-3 text-wedo-cyan" />
                        )}
                        Regenerar
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "departments" && (
          <Card>
            <CardHeader>
              <CardTitle>Departamentos</CardTitle>
              <CardDescription>Estrutura organizacional</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500">Em construção...</p>
            </CardContent>
          </Card>
        )}

        {activeTab === "benefits" && (
          <BenefitsContent
            key={`benefits-${isLoading ? 'loading' : 'loaded'}-${benefits.length}`}
            isLoading={isLoading}
            benefits={benefits}
            expandedCategories={expandedCategories}
            showImportModal={showImportModal}
            setShowImportModal={setShowImportModal}
            setShowTemplateModal={setShowTemplateModal}
            setEditingBenefit={setEditingBenefit}
            setShowBenefitModal={setShowBenefitModal}
            toggleCategory={toggleCategory}
            handleToggleBenefitStatus={handleToggleBenefitStatus}
            handleDeleteBenefit={handleDeleteBenefit}
            defaultBenefit={defaultBenefit}
          />
        )}

        {activeTab === "culture" && (
          <Card>
            <CardHeader>
              <CardTitle>Cultura Organizacional</CardTitle>
              <CardDescription>Valores e cultura da empresa</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500">Em construção...</p>
            </CardContent>
          </Card>
        )}
      </Tabs>

      <Dialog open={showBenefitModal} onOpenChange={setShowBenefitModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingBenefit?.id ? "Editar Benefício" : "Novo Benefício"}
            </DialogTitle>
            <DialogDescription>
              Configure os detalhes do benefício oferecido
            </DialogDescription>
          </DialogHeader>
          
          {editingBenefit && (
            <div className="space-y-6 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nome do Benefício *</Label>
                  <Input
                    value={editingBenefit.name}
                    onChange={e => setEditingBenefit({ ...editingBenefit, name: e.target.value })}
                    placeholder="Ex: Plano de Saúde Bradesco"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Categoria *</Label>
                  <Select
                    value={editingBenefit.category}
                    onValueChange={value => setEditingBenefit({ ...editingBenefit, category: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {BENEFIT_CATEGORIES.map(cat => (
                        <SelectItem key={cat.id} value={cat.id}>
                          <div className="flex items-center gap-2">
                            <cat.icon className={`w-4 h-4 ${cat.color}`} />
                            {cat.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Descrição</Label>
                <Textarea
                  value={editingBenefit.description}
                  onChange={e => setEditingBenefit({ ...editingBenefit, description: e.target.value })}
                  placeholder="Descreva os detalhes do benefício..."
                  rows={3}
                />
              </div>

              <div className="space-y-3">
                <Label>Tipo de Valor</Label>
                <div className="grid grid-cols-3 gap-3">
                  {VALUE_TYPES.map(type => (
                    <div
                      key={type.id}
                      className={`p-3 rounded-md border cursor-pointer transition-all ${
                        editingBenefit.value_type === type.id
                          ? 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                      }`}
                      onClick={() => setEditingBenefit({ ...editingBenefit, value_type: type.id })}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <type.icon className={`w-4 h-4 ${editingBenefit.value_type === type.id ? 'text-gray-700 dark:text-gray-300' : 'text-gray-500'}`} />
                        <span className="font-medium text-sm">{type.name}</span>
                      </div>
                      <p className="text-xs text-gray-500">{type.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {editingBenefit.value_type === "monetary" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Valor (R$)</Label>
                    <Input
                      type="number"
                      value={editingBenefit.value || ""}
                      onChange={e => setEditingBenefit({ ...editingBenefit, value: parseFloat(e.target.value) || undefined })}
                      placeholder="0,00"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>É desconto em folha?</Label>
                    <div className="flex items-center gap-2 pt-2">
                      <Switch
                        checked={editingBenefit.is_discount}
                        onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_discount: checked })}
                      />
                      <span className="text-sm text-gray-600">
                        {editingBenefit.is_discount ? "Sim, desconto" : "Não, empresa custeia"}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {editingBenefit.value_type === "percentage" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Percentual (%)</Label>
                    <Input
                      type="number"
                      value={editingBenefit.percentage_value || ""}
                      onChange={e => setEditingBenefit({ ...editingBenefit, percentage_value: parseFloat(e.target.value) || undefined })}
                      placeholder="Ex: 5"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Detalhes adicionais</Label>
                    <Input
                      value={editingBenefit.value_details || ""}
                      onChange={e => setEditingBenefit({ ...editingBenefit, value_details: e.target.value })}
                      placeholder="Ex: Contribuição sobre salário"
                    />
                  </div>
                </div>
              )}

              {editingBenefit.value_type === "informative" && (
                <div className="space-y-2">
                  <Label>Detalhes</Label>
                  <Textarea
                    value={editingBenefit.value_details || ""}
                    onChange={e => setEditingBenefit({ ...editingBenefit, value_details: e.target.value })}
                    placeholder="Descreva os detalhes do benefício..."
                    rows={2}
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Elegibilidade - Níveis</Label>
                  <Select
                    value={editingBenefit.seniority_levels?.[0] || "all"}
                    onValueChange={value => setEditingBenefit({ ...editingBenefit, seniority_levels: [value] })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SENIORITY_LEVELS.map(level => (
                        <SelectItem key={level.id} value={level.id}>
                          {level.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Carência</Label>
                  <Select
                    value={String(editingBenefit.waiting_period_days)}
                    onValueChange={value => setEditingBenefit({ ...editingBenefit, waiting_period_days: parseInt(value) })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {WAITING_PERIODS.map(period => (
                        <SelectItem key={period.id} value={String(period.id)}>
                          {period.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Fornecedor/Operadora</Label>
                <Input
                  value={editingBenefit.provider || ""}
                  onChange={e => setEditingBenefit({ ...editingBenefit, provider: e.target.value })}
                  placeholder="Ex: Bradesco Seguros, Sodexo, etc."
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={editingBenefit.is_highlighted}
                      onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_highlighted: checked })}
                    />
                    <Label className="text-sm">Benefício em destaque</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={editingBenefit.is_mandatory}
                      onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_mandatory: checked })}
                    />
                    <Label className="text-sm">Obrigatório</Label>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBenefitModal(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={() => editingBenefit && handleSaveBenefit(editingBenefit)}
              disabled={isSaving || !editingBenefit?.name || !editingBenefit?.category}
              className="bg-gray-800"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Salvando...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Salvar Benefício
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showImportModal} onOpenChange={setShowImportModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-wedo-cyan" />
              Importar Benefícios com LIA
            </DialogTitle>
            <DialogDescription>
              Faça upload de uma planilha ou documento e a LIA irá extrair e cadastrar os benefícios automaticamente
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div 
              className="border-2 border-dashed rounded-md p-8 text-center hover:border-gray-400 dark:hover:border-gray-500 transition-colors cursor-pointer"
              onClick={() => document.getElementById('file-upload')?.click()}
              onDragOver={e => { e.preventDefault(); e.stopPropagation() }}
              onDrop={e => {
                e.preventDefault()
                e.stopPropagation()
                const file = e.dataTransfer.files[0]
                if (file) setImportFile(file)
              }}
            >
              <input
                id="file-upload"
                type="file"
                className="hidden"
                accept=".xlsx,.xls,.csv,.pdf,.doc,.docx"
                onChange={e => {
                  const file = e.target.files?.[0]
                  if (file) setImportFile(file)
                }}
              />
              {importFile ? (
                <div className="flex items-center justify-center gap-3">
                  <FileSpreadsheet className="w-8 h-8 text-status-success" />
                  <div className="text-left">
                    <p className="font-medium">{importFile.name}</p>
                    <p className="text-xs text-gray-500">{(importFile.size / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                  <p className="font-medium mb-1">Arraste um arquivo ou clique para selecionar</p>
                  <p className="text-xs text-gray-500">Suportado: Excel, CSV, PDF, Word</p>
                </>
              )}
            </div>

 <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4">
              <div className="flex items-start gap-3">
                <Brain className="w-5 h-5 text-wedo-cyan mt-0.5" />
                <div>
 <p className="text-sm font-medium text-gray-9000">
                    A LIA irá analisar o arquivo e:
                  </p>
 <ul className="text-xs text-gray-900 dark:text-gray-300 mt-2 space-y-1">
                    <li>• Identificar todos os benefícios listados</li>
                    <li>• Categorizar automaticamente (saúde, alimentação, etc)</li>
                    <li>• Extrair valores, elegibilidade e carência</li>
                    <li>• Criar os cadastros prontos para sua revisão</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowImportModal(false); setImportFile(null) }}>
              Cancelar
            </Button>
            <Button 
              onClick={handleImportFile}
              disabled={isImporting || !importFile}
              className="gap-2 bg-gray-800"
            >
              {isImporting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processando...
                </>
              ) : (
                <>
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  Importar com LIA
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default function SetupEmpresaPage() {
  return <SetupEmpresaContent />
}
