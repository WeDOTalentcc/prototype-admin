"use client"

import { useState, useEffect, useCallback } from "react"
import { BENEFIT_CATEGORIES, defaultBenefit } from "./setup-empresa.constants"
import type {
  Benefit,
  BenefitTemplate,
  CompanyProfile,
  EnrichmentResult,
  EVPAnalysis,
} from "./setup-empresa.types"

export function useSetupEmpresa() {
  const [mounted, setMounted] = useState(false)
  const [activeTab, setActiveTab] = useState("profile")
  const [benefits, setBenefits] = useState<Benefit[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [showBenefitModal, setShowBenefitModal] = useState(false)
  const [editingBenefit, setEditingBenefit] = useState<Benefit | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<string[]>(
    BENEFIT_CATEGORIES.map((c) => c.id)
  )
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile>({ name: "" })
  const [departments, setDepartments] = useState<{ id: string; name: string }[]>([])
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
    try {
      const response = await fetch("/api/backend-proxy/company/benefits/")
      if (response.ok) {
        const data = await response.json()
        const items = Array.isArray(data) ? data : data.items || []
        setBenefits(items)
      }
    } catch (error) {
    } finally {
      setIsLoading(false)
    }
  }, [])

  const loadCompanyProfile = useCallback(async () => {
    try {
      const response = await fetch("/api/backend-proxy/company/profile/")
      if (response.ok) {
        const data = await response.json()
        const additionalData = data.additional_data || {}
        setCompanyProfile({
          ...data,
          mission: additionalData.mission || "",
          vision: additionalData.vision || "",
          values: additionalData.values || "",
          tagline: additionalData.tagline || "",
        })
        if (additionalData.evp_analysis) {
          setEvpData(additionalData.evp_analysis)
        }
      }
    } catch (error) {}
  }, [])

  const loadDepartments = useCallback(async () => {
    try {
      const response = await fetch("/api/backend-proxy/company/departments/")
      if (response.ok) {
        const data = await response.json()
        setDepartments(Array.isArray(data) ? data : data.items || [])
      }
    } catch (error) {}
  }, [])

  const handleEnrichProfile = useCallback(async () => {
    if (!companyProfile.linkedin_url) {
      setEnrichmentError("Por favor, insira a URL do LinkedIn da empresa")
      return
    }

    setIsEnriching(true)
    setEnrichmentError(null)

    try {
      const response = await fetch("/api/backend-proxy/company/enrich", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          linkedin_url: companyProfile.linkedin_url,
          glassdoor_company_name: companyProfile.name || undefined,
        }),
      })

      if (response.ok) {
        const data: EnrichmentResult = await response.json()

        if (data.success) {
          const updates: Partial<CompanyProfile> = {}

          if (data.enriched_culture.company_description) {
            updates.description = data.enriched_culture.company_description as string
          }
          if (data.enriched_culture.tagline) {
            updates.tagline = data.enriched_culture.tagline as string
          }
          if (data.enriched_culture.mission) {
            updates.mission = data.enriched_culture.mission as string
          }
          if (data.enriched_culture.vision) {
            updates.vision = data.enriched_culture.vision as string
          }
          if (data.linkedin_data.website) {
            updates.website = data.linkedin_data.website as string
          }
          if ((data.linkedin_data.industries as unknown[])?.length > 0) {
            updates.industry = Array.isArray(data.linkedin_data.industries)
              ? (data.linkedin_data.industries[0] as string)
              : (data.linkedin_data.industries as string)
          }
          if (data.linkedin_data.company_size) {
            updates.company_size = String(data.linkedin_data.company_size)
          }

          const hq = data.linkedin_data.headquarters
          if (hq) {
            if (typeof hq === "string") {
              updates.headquarters_city = hq
            } else if (typeof hq === "object") {
              const hqObj = hq as Record<string, string>
              if (hqObj.city) updates.headquarters_city = hqObj.city
              if (hqObj.state) updates.headquarters_state = hqObj.state
              else if (hqObj.geographicArea)
                updates.headquarters_state = hqObj.geographicArea
            }
          }

          if (
            data.enriched_culture.culture_highlights &&
            Array.isArray(data.enriched_culture.culture_highlights)
          ) {
            updates.values = (data.enriched_culture.culture_highlights as string[])
              .slice(0, 5)
              .join("\n")
          }

          setCompanyProfile((prev) => {
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
                    tagline,
                  },
                }
                try {
                  const saveRes = await fetch(
                    `/api/backend-proxy/company/profile/${newProfile.id}`,
                    {
                      method: "PUT",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify(profileData),
                    }
                  )
                  if (saveRes.ok) {
                    const evpRes = await fetch(
                      `/api/backend-proxy/company/profile/${newProfile.id}/generate-evp`,
                      {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                      }
                    )
                    if (evpRes.ok) {
                      const evpResult = await evpRes.json()
                      if (evpResult.success && evpResult.evp_analysis) {
                        setEvpData(evpResult.evp_analysis)
                      }
                    }
                  }
                } catch (e) {}
              }
            }, 100)
            return newProfile
          })

          if (data.errors.length > 0) {
            setEnrichmentError(`Enriquecimento parcial: ${data.errors.join(", ")}`)
          }
        } else {
          setEnrichmentError(data.errors.join(", ") || "Falha ao enriquecer perfil")
        }
      } else {
        const errorData = await response.json().catch(() => ({}))
        setEnrichmentError(
          (errorData as { detail?: string }).detail ||
            "Erro ao conectar com o serviço de enriquecimento"
        )
      }
    } catch (error) {
      setEnrichmentError("Erro ao processar enriquecimento. Tente novamente.")
    } finally {
      setIsEnriching(false)
    }
  }, [companyProfile.linkedin_url, companyProfile.name])

  const handleSaveProfile = useCallback(async () => {
    setIsSavingProfile(true)
    try {
      const url = companyProfile.id
        ? `/api/backend-proxy/company/profile/${companyProfile.id}`
        : "/api/backend-proxy/company/profile"

      const { mission, vision, values, tagline, ...baseFields } = companyProfile
      const existingAdditionalData = baseFields.additional_data || {}
      const profileData = {
        ...baseFields,
        additional_data: {
          ...existingAdditionalData,
          mission,
          vision,
          values,
          tagline,
        },
      }

      const response = await fetch(url, {
        method: companyProfile.id ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profileData),
      })

      if (response.ok) {
        const data = await response.json()
        const additionalData = data.additional_data || {}
        setCompanyProfile({
          ...data,
          mission: additionalData.mission || "",
          vision: additionalData.vision || "",
          values: additionalData.values || "",
          tagline: additionalData.tagline || "",
        })
      }
    } catch (error) {
    } finally {
      setIsSavingProfile(false)
    }
  }, [companyProfile])

  const handleGenerateEvp = useCallback(
    async (profileId?: string) => {
      const id = profileId || companyProfile.id
      if (!id) {
        setEvpError("Salve o perfil da empresa primeiro")
        return
      }

      setIsGeneratingEvp(true)
      setEvpError(null)

      try {
        const response = await fetch(
          `/api/backend-proxy/company/profile/${id}/generate-evp`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
          }
        )

        if (response.ok) {
          const data = await response.json()
          if (data.success && data.evp_analysis) {
            setEvpData(data.evp_analysis)
          } else {
            setEvpError(data.error || "Falha ao gerar análise EVP")
          }
        } else {
          const errorData = await response.json().catch(() => ({}))
          setEvpError(
            (errorData as { detail?: string }).detail ||
              "Erro ao conectar com o serviço"
          )
        }
      } catch (error) {
        setEvpError("Erro ao processar geração de EVP")
      } finally {
        setIsGeneratingEvp(false)
      }
    },
    [companyProfile.id]
  )

  useEffect(() => {
    let cancelled = false

    const fetchData = async () => {
      try {
        const benefitsResponse = await fetch("/api/backend-proxy/company/benefits/")
        if (!cancelled && benefitsResponse.ok) {
          const data = await benefitsResponse.json()
          const items = Array.isArray(data) ? data : data.items || []
          setBenefits(items)
        }
      } catch (error) {
      } finally {
        if (!cancelled) {
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
      const response = await fetch("/api/backend-proxy/benefits/templates")
      if (response.ok) {
        const data = await response.json()
        const items = data.items || []
        setTemplates(items)
        return items.length
      }
      return 0
    } catch (err) {
      return 0
    } finally {
      setIsLoadingTemplates(false)
    }
  }, [])

  const seedTemplates = useCallback(async () => {
    try {
      await fetch("/api/backend-proxy/benefits/templates", { method: "POST" })
      await loadTemplates()
    } catch (err) {}
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
    return benefits.some((b) => b.name.toLowerCase() === templateName.toLowerCase())
  }

  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      templateSearch === "" ||
      template.name.toLowerCase().includes(templateSearch.toLowerCase()) ||
      (template.description &&
        template.description.toLowerCase().includes(templateSearch.toLowerCase()))
    const matchesCategory =
      templateCategoryFilter === "all" || template.category === templateCategoryFilter
    return matchesSearch && matchesCategory
  })

  const templatesByCategory = BENEFIT_CATEGORIES.reduce(
    (acc, cat) => {
      acc[cat.id] = filteredTemplates.filter((t) => t.category === cat.id)
      return acc
    },
    {} as Record<string, BenefitTemplate[]>
  )

  const handleSaveBenefit = async (benefit: Benefit) => {
    setIsSaving(true)
    try {
      const url = benefit.id
        ? `/api/backend-proxy/company/benefits/${benefit.id}?company_id=default`
        : "/api/backend-proxy/company/benefits/?company_id=default"

      const response = await fetch(url, {
        method: benefit.id ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(benefit),
      })

      if (response.ok) {
        await loadBenefits()
        setShowBenefitModal(false)
        setEditingBenefit(null)
      }
    } catch (error) {
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteBenefit = async (benefitId: string) => {
    if (!confirm("Tem certeza que deseja excluir este benefício?")) return

    try {
      const response = await fetch(
        `/api/backend-proxy/company/benefits/${benefitId}?company_id=default`,
        { method: "DELETE" }
      )
      if (response.ok) {
        await loadBenefits()
      }
    } catch (error) {}
  }

  const handleToggleBenefitStatus = async (benefit: Benefit) => {
    if (!benefit.id) return
    try {
      const response = await fetch(
        `/api/backend-proxy/company/benefits/${benefit.id}?company_id=default`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...benefit, is_active: !benefit.is_active }),
        }
      )
      if (response.ok) {
        await loadBenefits()
      }
    } catch (error) {}
  }

  const handleImportFile = async () => {
    if (!importFile) return

    setIsImporting(true)
    try {
      const formData = new FormData()
      formData.append("file", importFile)

      const response = await fetch(
        "/api/backend-proxy/company/benefits/import?company_id=default",
        { method: "POST", body: formData }
      )

      if (response.ok) {
        await loadBenefits()
        setShowImportModal(false)
        setImportFile(null)
      }
    } catch (error) {
    } finally {
      setIsImporting(false)
    }
  }

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((id) => id !== categoryId)
        : [...prev, categoryId]
    )
  }

  const getCategoryIcon = (categoryId: string) => {
    const cat = BENEFIT_CATEGORIES.find((c) => c.id === categoryId)
    return cat ? cat.icon : null
  }

  const getCategoryColor = (categoryId: string) => {
    const cat = BENEFIT_CATEGORIES.find((c) => c.id === categoryId)
    return cat ? cat.color : "lia-text-500"
  }

  return {
    // state
    mounted,
    activeTab,
    setActiveTab,
    benefits,
    isLoading,
    isSaving,
    showBenefitModal,
    setShowBenefitModal,
    editingBenefit,
    setEditingBenefit,
    expandedCategories,
    showImportModal,
    setShowImportModal,
    importFile,
    setImportFile,
    isImporting,
    companyProfile,
    setCompanyProfile,
    departments,
    showTemplateModal,
    setShowTemplateModal,
    templates,
    isLoadingTemplates,
    templateSearch,
    setTemplateSearch,
    templateCategoryFilter,
    setTemplateCategoryFilter,
    isEnriching,
    enrichmentError,
    isSavingProfile,
    isGeneratingEvp,
    evpData,
    evpError,
    filteredTemplates,
    templatesByCategory,
    // handlers
    loadBenefits,
    loadCompanyProfile,
    loadDepartments,
    handleEnrichProfile,
    handleSaveProfile,
    handleGenerateEvp,
    handleSaveBenefit,
    handleDeleteBenefit,
    handleToggleBenefitStatus,
    handleImportFile,
    toggleCategory,
    handleSelectTemplate,
    isTemplateAlreadyAdded,
    getCategoryIcon,
    getCategoryColor,
  }
}
