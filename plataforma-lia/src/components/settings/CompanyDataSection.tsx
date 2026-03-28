'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Building,
  Edit,
  Save,
  Globe,
  Mail,
  Phone,
  MapPin,
  CheckCircle,
  AlertCircle,
  Crown,
  Building2,
  Image,
  Loader2,
  Brain,
  Briefcase,
  TrendingUp,
  Code,
  Calendar,
  Linkedin,
  Leaf,
  Heart,
  HelpCircle,
  Server,
  Layout,
  Database,
  Cloud,
  Settings,
  Palette,
  Smartphone,
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  FileText,
  Users,
} from "lucide-react"
import { CompanyDataCard, SimpleDataCard } from './CompanyDataCard'
import { defaultLiaFieldExamples } from './LiaFieldToggle'
import { BigFiveRadar } from './BigFiveRadar'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  INDUSTRIES,
  INDUSTRY_CATEGORIES,
  type IndustryCategory,
} from "@/lib/industry-constants"
import { LiaFieldKey } from '@/hooks/use-company-lia-instructions'
import { textStyles } from '@/lib/design-tokens'

interface CompanyDataSectionProps {
  companyData: any
  setCompanyData: (fn: (prev: any) => any) => void
  isEditingCompanyData: boolean
  setIsEditingCompanyData: (value: boolean) => void
  companyDataBackup: any
  setCompanyDataBackup: (data: any) => void
  saveCompanyData: () => Promise<void>
  saving: boolean
  loading: boolean
  successMessage: string | null
  error: string | null
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void
  updateLiaInstruction: (fieldKey: string, instruction: string) => void
  isLiaAnalyzing: boolean
  liaAnalysisProgress: number
  liaAnalysisStep: string | null
  handleLiaAnalysis: () => void
  handleSaveCultureFields: () => Promise<void>
  techStackByCategory: Record<string, string[]>
  expandedCategories: Record<string, boolean>
  setExpandedCategories: (fn: (prev: Record<string, boolean>) => Record<string, boolean>) => void
  addTechToCategory: (category: string, tech: string) => void
  removeTechFromCategory: (category: string, tech: string) => void
  TECH_STACK_CATEGORIES: readonly any[]
}

const inputClass = (disabled: boolean) => 
 `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors ${disabled ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`

const textareaClass = (disabled: boolean) => 
 `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors resize-none ${disabled ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`

const selectClass = (disabled: boolean) => 
 `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 dark:focus:ring-gray-50/10 dark:focus:border-gray-50 transition-colors ${disabled ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`

export function CompanyDataSection({
  companyData,
  setCompanyData,
  isEditingCompanyData,
  setIsEditingCompanyData,
  companyDataBackup,
  setCompanyDataBackup,
  saveCompanyData,
  saving,
  loading,
  successMessage,
  error,
  updateLiaToggle,
  updateLiaInstruction,
  isLiaAnalyzing,
  liaAnalysisProgress,
  liaAnalysisStep,
  handleLiaAnalysis,
  handleSaveCultureFields,
  techStackByCategory,
  expandedCategories,
  setExpandedCategories,
  addTechToCategory,
  removeTechFromCategory,
  TECH_STACK_CATEGORIES,
}: CompanyDataSectionProps) {

  const countActiveFields = () => {
    const toggles = companyData.lia_field_toggles || {}
    return Object.values(toggles).filter(Boolean).length
  }

  const totalFields = Object.keys(companyData.lia_field_toggles || {}).length || 34

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-md" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {successMessage && (
        <div className="bg-status-success/10 border border-status-success/30 text-status-success dark:bg-status-success/20 dark:border-status-success/30 dark:text-status-success px-3 py-2 rounded-md flex items-center gap-2 text-xs font-['Open_Sans',sans-serif]">
          <CheckCircle className="w-3.5 h-3.5" />
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error dark:bg-status-error/20 dark:border-status-error/30 dark:text-status-error px-3 py-2 rounded-md flex items-center gap-2 text-xs font-['Open_Sans',sans-serif]">
          <AlertCircle className="w-3.5 h-3.5" />
          {error}
        </div>
      )}

      {/* Header com botão Editar/Salvar */}
      <div className="flex items-center justify-between bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-900 dark:bg-gray-50">
            <Building className="w-5 h-5 text-white dark:text-gray-900" />
          </div>
          <div>
            <h2 className={textStyles.h3}>
              Dados da Empresa
            </h2>
            <p className={textStyles.description}>
              Configure os dados institucionais e preferências da LIA
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 font-['Open_Sans',sans-serif]">
            {countActiveFields()} de {totalFields} campos ativos
          </span>
          {!isEditingCompanyData ? (
            <Button
              onClick={() => {
                setCompanyDataBackup({ ...companyData })
                setIsEditingCompanyData(true)
              }}
              variant="outline"
              size="sm"
              className="gap-1.5 text-xs rounded-md"
            >
              <Edit className="w-3.5 h-3.5" />
              Editar
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <Button
                onClick={() => {
                  if (companyDataBackup) {
                    setCompanyData(() => companyDataBackup)
                  }
                  setIsEditingCompanyData(false)
                  setCompanyDataBackup(null)
                }}
                disabled={saving}
                variant="outline"
                size="sm"
                className="text-xs rounded-md"
              >
                Cancelar
              </Button>
              <Button
                onClick={async () => {
                  await saveCompanyData()
                  setIsEditingCompanyData(false)
                  setCompanyDataBackup(null)
                }}
                disabled={saving}
                size="sm"
                className="gap-1.5 text-xs rounded-md bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    Salvar
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Seção: Informações Gerais */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
          Informações Gerais
        </h3>
        
        <div className="grid grid-cols-1 gap-3">
          {/* Logo - Card especial com logo antes do nome e largura auto */}
          <div className="inline-flex items-center gap-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md px-4 py-3 w-fit">
            <div className="w-14 h-14 rounded-md bg-gray-100 dark:bg-gray-800 border-2 border-dashed border-gray-300 flex items-center justify-center cursor-pointer hover:bg-gray-50 transition-colors hover:border-gray-900 dark:hover:border-gray-50 flex-shrink-0">
              {companyData.logo ? (
                <img src={companyData.logo} alt="Logo" className="w-full h-full object-cover rounded-md" />
              ) : (
                <div className="text-center">
                  <Image className="w-5 h-5 mx-auto text-gray-400 dark:text-gray-500 mb-0.5" />
                  <span className="text-micro text-gray-500 dark:text-gray-400 font-['Open_Sans',sans-serif]">Upload</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <span className={textStyles.label}>
                Logo da Empresa
              </span>
              <span className="text-micro text-gray-500 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded-full font-['Open_Sans',sans-serif]">
                Identidade Visual
              </span>
            </div>
          </div>

          {/* Razão Social */}
          <SimpleDataCard
            label="Razão Social"
            category="Registro"
            
            isEditing={isEditingCompanyData}
          >
            <input
              type="text"
              value={companyData.name}
              onChange={(e) => setCompanyData((prev: any) => ({ ...prev, name: e.target.value }))}
              disabled={!isEditingCompanyData}
              className={inputClass(!isEditingCompanyData)}
              placeholder="Nome legal da empresa"
            />
          </SimpleDataCard>

          {/* Nome Fantasia */}
          <CompanyDataCard
            fieldKey="trade_name"
            label="Nome Fantasia"
            category="Informações da Empresa"
            
            isActive={companyData.lia_field_toggles?.trade_name ?? true}
            currentInstruction={companyData.lia_instructions?.trade_name || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <input
              type="text"
              value={companyData.tradeName || ''}
              onChange={(e) => setCompanyData((prev: any) => ({ ...prev, tradeName: e.target.value }))}
              disabled={!isEditingCompanyData}
              className={inputClass(!isEditingCompanyData)}
              placeholder="Nome comercial da empresa"
            />
          </CompanyDataCard>

          {/* CNPJ */}
          <SimpleDataCard
            label="CNPJ"
            category="Registro"
            
            isEditing={isEditingCompanyData}
          >
            <input
              type="text"
              value={companyData.cnpj || ''}
              onChange={(e) => setCompanyData((prev: any) => ({ ...prev, cnpj: e.target.value }))}
              disabled={!isEditingCompanyData}
              className={inputClass(!isEditingCompanyData)}
              placeholder="00.000.000/0000-00"
            />
          </SimpleDataCard>

          {/* Setor */}
          <CompanyDataCard
            fieldKey="industry"
            label="Setor/Indústria"
            category="Informações da Empresa"
            
            isActive={companyData.lia_field_toggles?.industry ?? true}
            currentInstruction={companyData.lia_instructions?.industry || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <select
              value={companyData.industry || ''}
              onChange={(e) => setCompanyData((prev: any) => ({ ...prev, industry: e.target.value }))}
              disabled={!isEditingCompanyData}
              className={selectClass(!isEditingCompanyData)}
            >
              <option value="">Selecione o setor...</option>
              {(Object.keys(INDUSTRY_CATEGORIES) as IndustryCategory[]).map((category) => (
                <optgroup key={category} label={INDUSTRY_CATEGORIES[category].labelPt}>
                  {INDUSTRIES.filter((ind) => ind.category === category).map((ind) => (
                    <option key={ind.key} value={ind.labelPt}>{ind.labelPt}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </CompanyDataCard>
        </div>
      </div>

      {/* Seção: Contato e Presença Online */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
          Contato e Presença Online
        </h3>
        
        <div className="grid grid-cols-1 gap-3">
          {/* Website */}
          <CompanyDataCard
            fieldKey="website"
            label="Website"
            category="Presença Online"
            
            isActive={companyData.lia_field_toggles?.website ?? true}
            currentInstruction={companyData.lia_instructions?.website || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <div className="flex items-center gap-2">
              <input
                type="url"
                value={companyData.website || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, website: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={inputClass(!isEditingCompanyData)}
                placeholder="https://www.empresa.com.br"
              />
            </div>
          </CompanyDataCard>

          {/* LinkedIn */}
          <CompanyDataCard
            fieldKey="linkedin_url"
            label="LinkedIn"
            category="Presença Online"
            
            isActive={companyData.lia_field_toggles?.linkedin_url ?? true}
            currentInstruction={companyData.lia_instructions?.linkedin_url || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <div className="flex items-center gap-2">
              <input
                type="url"
                value={companyData.linkedin_url || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, linkedin_url: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={inputClass(!isEditingCompanyData)}
                placeholder="https://linkedin.com/company/..."
              />
            </div>
          </CompanyDataCard>

          {/* Email */}
          <SimpleDataCard
            label="Email"
            category="Contato"
            
            isEditing={isEditingCompanyData}
          >
            <div className="flex items-center gap-2">
              <input
                type="email"
                value={companyData.email || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, email: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={inputClass(!isEditingCompanyData)}
                placeholder="contato@empresa.com.br"
              />
            </div>
          </SimpleDataCard>

          {/* Telefone */}
          <SimpleDataCard
            label="Telefone"
            category="Contato"
            
            isEditing={isEditingCompanyData}
          >
            <div className="flex items-center gap-2">
              <input
                type="tel"
                value={companyData.phone || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, phone: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={inputClass(!isEditingCompanyData)}
                placeholder="(11) 9999-9999"
              />
            </div>
          </SimpleDataCard>

          {/* Endereço */}
          <CompanyDataCard
            fieldKey="locations"
            label="Endereço"
            category="Localização"
            
            isActive={companyData.lia_field_toggles?.locations ?? true}
            currentInstruction={companyData.lia_instructions?.locations || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
            className="md:col-span-2"
          >
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-gray-400 dark:text-gray-500" />
              <input
                type="text"
                value={companyData.address || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, address: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={inputClass(!isEditingCompanyData)}
                placeholder="Endereço completo"
              />
            </div>
          </CompanyDataCard>
        </div>
      </div>

      {/* LIA Analysis Card - CYAN é mantido aqui pois é seção LIA/IA */}
      <div className="rounded-md border border-gray-300 dark:border-gray-600 bg-gradient-to-r from-gray-50 dark:from-gray-900 to-transparent p-5">
        <div className="flex items-start gap-4">
          <div
            className="w-12 h-12 rounded-md flex items-center justify-center flex-shrink-0 bg-gray-900 dark:bg-gray-50"
          >
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-bold text-gray-950 dark:text-gray-50 mb-1 font-['Open_Sans',sans-serif]">
              Análise Inteligente com LIA
            </h4>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 leading-relaxed font-['Open_Sans',sans-serif]">
              A LIA pode analisar o website e LinkedIn da empresa para preencher automaticamente os campos de Cultura, Missão, Visão, Valores e ajustar o perfil Big Five.
            </p>

            {isLiaAnalyzing ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-gray-700">
                    {liaAnalysisStep || "Iniciando..."}
                  </span>
                  <span className="font-bold tabular-nums text-gray-700">
                    {Math.round(liaAnalysisProgress)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-2 rounded-full transition-all duration-500 bg-gray-900" style={{width: `${liaAnalysisProgress}%`}}
                  />
                </div>
              </div>
            ) : (
              <Button
                onClick={handleLiaAnalysis}
                disabled={!isEditingCompanyData || !companyData.website}
                className="gap-2 text-white hover:opacity-90 transition-opacity text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              >
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Analisar com LIA
              </Button>
            )}

            {!isLiaAnalyzing && (!isEditingCompanyData || !companyData.website) && (
              <p className="text-micro text-status-warning mt-2">
                {!isEditingCompanyData 
                  ? "Clique em 'Editar' para habilitar a análise"
                  : "Informe o website da empresa acima para habilitar a análise"
                }
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Seção: Cultura e Identidade */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
          Cultura e Identidade
        </h3>
        
        <div className="grid grid-cols-1 gap-3">
          {/* Missão */}
          <CompanyDataCard
            fieldKey="mission"
            label="Missão"
            category="Cultura"
            
            isActive={companyData.lia_field_toggles?.mission ?? true}
            currentInstruction={companyData.lia_instructions?.mission || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <textarea
              value={companyData.mission || ''}
              onChange={(e) => setCompanyData((prev: any) => ({ ...prev, mission: e.target.value }))}
              disabled={!isEditingCompanyData}
              className={textareaClass(!isEditingCompanyData)}
              rows={2}
              placeholder="Missão da empresa..."
            />
          </CompanyDataCard>

          {/* Visão */}
          <CompanyDataCard
            fieldKey="vision"
            label="Visão"
            category="Cultura"
            
            isActive={companyData.lia_field_toggles?.vision ?? true}
            currentInstruction={companyData.lia_instructions?.vision || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <textarea
              value={companyData.vision || ''}
              onChange={(e) => setCompanyData((prev: any) => ({ ...prev, vision: e.target.value }))}
              disabled={!isEditingCompanyData}
              className={textareaClass(!isEditingCompanyData)}
              rows={2}
              placeholder="Visão da empresa..."
            />
          </CompanyDataCard>

          {/* Valores */}
          <CompanyDataCard
            fieldKey="values"
            label="Valores"
            category="Cultura"
            
            isActive={companyData.lia_field_toggles?.values ?? true}
            currentInstruction={companyData.lia_instructions?.values || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <div className="space-y-2">
              <div className="flex flex-wrap gap-2">
                {(companyData.values || []).map((value: string, idx: number) => (
                  <Badge key={idx} className="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 text-micro px-2 py-0.5 rounded-full">
                    {value}
                    {isEditingCompanyData && (
                      <button
                        onClick={() => setCompanyData((prev: any) => ({
                          ...prev,
                          values: prev.values?.filter((_: any, i: number) => i !== idx),
                        }))}
                        className="ml-1 hover:text-status-error"
                      >×</button>
                    )}
                  </Badge>
                ))}
              </div>
              <input
                type="text"
                placeholder="Adicionar valor e pressionar Enter..."
                disabled={!isEditingCompanyData}
                className={inputClass(!isEditingCompanyData)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && e.currentTarget.value.trim()) {
                    e.preventDefault()
                    setCompanyData((prev: any) => ({
                      ...prev,
                      values: [...(prev.values || []), e.currentTarget.value.trim()],
                    }))
                    e.currentTarget.value = ""
                  }
                }}
              />
            </div>
          </CompanyDataCard>

          {/* Competências Comportamentais */}
          <CompanyDataCard
            fieldKey="core_competencies"
            label="Competências Comportamentais"
            category="Cultura"
            
            isActive={companyData.lia_field_toggles?.core_competencies ?? true}
            currentInstruction={companyData.lia_instructions?.core_competencies || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <div className="space-y-2">
              <div className="flex flex-wrap gap-2">
                {(companyData.coreCompetencies || []).map((comp: string, idx: number) => (
                  <Badge key={idx} className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-micro px-2 py-0.5 rounded-full">
                    {comp}
                    {isEditingCompanyData && (
                      <button
                        onClick={() => setCompanyData((prev: any) => ({
                          ...prev,
                          coreCompetencies: prev.coreCompetencies?.filter((_: any, i: number) => i !== idx),
                        }))}
                        className="ml-1 hover:text-status-error"
                      >×</button>
                    )}
                  </Badge>
                ))}
              </div>
              <input
                type="text"
                placeholder="Adicionar competência e pressionar Enter..."
                disabled={!isEditingCompanyData}
                className={inputClass(!isEditingCompanyData)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && e.currentTarget.value.trim()) {
                    e.preventDefault()
                    setCompanyData((prev: any) => ({
                      ...prev,
                      coreCompetencies: [...(prev.coreCompetencies || []), e.currentTarget.value.trim()],
                    }))
                    e.currentTarget.value = ""
                  }
                }}
              />
            </div>
          </CompanyDataCard>
        </div>
      </div>

      {/* Seção: Informações Corporativas */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
          Informações Corporativas
        </h3>
        
        <div className="grid grid-cols-1 gap-3">
          {/* Nº de Funcionários */}
          <SimpleDataCard
            label="Nº de Funcionários"
            category="Estrutura"
            
            isEditing={isEditingCompanyData}
          >
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-gray-400 dark:text-gray-500" />
              <input
                type="number"
                value={companyData.employee_count || ''}
                onChange={(e) => setCompanyData((prev: any) => ({
                  ...prev,
                  employee_count: parseInt(e.target.value) || undefined,
                }))}
                disabled={!isEditingCompanyData}
                className={inputClass(!isEditingCompanyData)}
                placeholder="Ex: 500"
              />
            </div>
          </SimpleDataCard>

          {/* Porte da Empresa */}
          <SimpleDataCard
            label="Porte da Empresa"
            category="Estrutura"
            
            isEditing={isEditingCompanyData}
          >
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-gray-400 dark:text-gray-500" />
              <select
                value={companyData.company_size || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, company_size: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={selectClass(!isEditingCompanyData)}
              >
                <option value="">Selecione...</option>
                <option value="startup">Startup (1-50)</option>
                <option value="small">Pequena (51-200)</option>
                <option value="medium">Média (201-1000)</option>
                <option value="large">Grande (1001-5000)</option>
                <option value="enterprise">Enterprise (5000+)</option>
              </select>
            </div>
          </SimpleDataCard>

          {/* Ano de Fundação */}
          <SimpleDataCard
            label="Ano de Fundação"
            category="História"
            
            isEditing={isEditingCompanyData}
          >
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-400 dark:text-gray-500" />
              <input
                type="number"
                value={companyData.founded_year || ''}
                onChange={(e) => setCompanyData((prev: any) => ({
                  ...prev,
                  founded_year: parseInt(e.target.value) || undefined,
                }))}
                disabled={!isEditingCompanyData}
                className={inputClass(!isEditingCompanyData)}
                placeholder="Ex: 2020"
              />
            </div>
          </SimpleDataCard>
        </div>
      </div>

      {/* Seção: Modelo de Trabalho e Contratação */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
          Modelo de Trabalho e Contratação
        </h3>
        
        <div className="grid grid-cols-1 gap-3">
          {/* Modelo de Trabalho */}
          <CompanyDataCard
            fieldKey="work_model"
            label="Modelo de Trabalho"
            category="Trabalho & Contratação"
            
            isActive={companyData.lia_field_toggles?.work_model ?? true}
            currentInstruction={companyData.lia_instructions?.work_model || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <div className="flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-gray-400 dark:text-gray-500" />
              <select
                value={companyData.work_model || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, work_model: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={selectClass(!isEditingCompanyData)}
              >
                <option value="">Selecione...</option>
                <option value="remote">100% Remoto</option>
                <option value="hybrid">Híbrido</option>
                <option value="onsite">Presencial</option>
                <option value="flexible">Flexível</option>
              </select>
            </div>
          </CompanyDataCard>

          {/* Modelos de Contratação */}
          <CompanyDataCard
            fieldKey="employment_types"
            label="Modelos de Contratação"
            category="Trabalho & Contratação"
            
            isActive={companyData.lia_field_toggles?.employment_types ?? true}
            currentInstruction={companyData.lia_instructions?.employment_types || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <div className="flex flex-wrap gap-1.5">
              {['CLT', 'PJ', 'Freelancer', 'Estágio', 'Temporário', 'Aprendiz'].map((type) => {
                const isSelected = (companyData.employment_types || []).includes(type)
                return (
                  <button
                    key={type}
                    type="button"
                    disabled={!isEditingCompanyData}
                    onClick={() => {
                      if (!isEditingCompanyData) return
                      const current = companyData.employment_types || []
                      const updated = isSelected
                        ? current.filter((t: string) => t !== type)
                        : [...current, type]
                      setCompanyData((prev: any) => ({ ...prev, employment_types: updated }))
                    }}
                    className={`px-2.5 py-1.5 text-micro rounded-full border transition-colors ${
                      isSelected
                        ? 'bg-gray-900 border-gray-900 text-white dark:bg-gray-50 dark:border-gray-50 dark:text-gray-900'
                        : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300'
                    } ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                  >
                    {isSelected && <CheckCircle className="w-2.5 h-2.5 inline mr-0.5" />}
                    {type}
                  </button>
                )
              })}
            </div>
          </CompanyDataCard>

          {/* Níveis de Senioridade */}
          <CompanyDataCard
            fieldKey="seniority_levels"
            label="Níveis de Senioridade"
            category="Trabalho & Contratação"
            
            isActive={companyData.lia_field_toggles?.seniority_levels ?? true}
            currentInstruction={companyData.lia_instructions?.seniority_levels || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
            className="md:col-span-2"
          >
            <div className="space-y-2">
              <div className="flex flex-wrap gap-2">
                {(companyData.seniority_levels || []).map((level: string, idx: number) => (
                  <Badge key={idx} className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-micro px-2 py-0.5 rounded-full">
                    {level}
                    {isEditingCompanyData && (
                      <button
                        onClick={() => setCompanyData((prev: any) => ({
                          ...prev,
                          seniority_levels: (prev.seniority_levels || []).filter((_: any, i: number) => i !== idx),
                        }))}
                        className="ml-1 hover:text-status-error"
                      >×</button>
                    )}
                  </Badge>
                ))}
              </div>
              <div className="flex flex-wrap gap-1">
                {["Estágio", "Júnior", "Pleno", "Sênior", "Especialista", "Coordenador", "Gerente", "Diretor", "C-Level"]
                  .filter((level) => !(companyData.seniority_levels || []).includes(level))
                  .map((level) => (
                    <button
                      key={level}
                      type="button"
                      disabled={!isEditingCompanyData}
                      onClick={() => {
                        if (!isEditingCompanyData) return
                        setCompanyData((prev: any) => ({
                          ...prev,
                          seniority_levels: [...(prev.seniority_levels || []), level],
                        }))
                      }}
                      className={`text-micro px-2 py-0.5 border border-dashed border-gray-300 dark:border-gray-600 rounded-full text-gray-500 dark:text-gray-400 hover:border-wedo-purple/30 hover:text-wedo-purple transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                    >
                      + {level}
                    </button>
                  ))}
              </div>
            </div>
          </CompanyDataCard>
        </div>
      </div>

      {/* Seção: Responsabilidade Social */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
          Responsabilidade Social
        </h3>
        
        <div className="grid grid-cols-1 gap-3">
          {/* DEI */}
          <CompanyDataCard
            fieldKey="dei_initiatives"
            label="Diversidade e Inclusão"
            category="Responsabilidade Social"
            
            isActive={companyData.lia_field_toggles?.dei_initiatives ?? true}
            currentInstruction={companyData.lia_instructions?.dei_initiatives || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <div className="flex items-start gap-2">
              <Users className="w-4 h-4 text-gray-400 dark:text-gray-500 mt-2" />
              <textarea
                value={companyData.dei_initiatives || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, dei_initiatives: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={textareaClass(!isEditingCompanyData)}
                rows={2}
                placeholder="Descreva as iniciativas de D&I..."
              />
            </div>
          </CompanyDataCard>

          {/* Sustentabilidade */}
          <CompanyDataCard
            fieldKey="sustainability"
            label="Sustentabilidade"
            category="Responsabilidade Social"
            
            isActive={companyData.lia_field_toggles?.sustainability ?? true}
            currentInstruction={companyData.lia_instructions?.sustainability || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <div className="flex items-start gap-2">
              <Leaf className="w-4 h-4 text-gray-400 dark:text-gray-500 mt-2" />
              <textarea
                value={companyData.sustainability || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, sustainability: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={textareaClass(!isEditingCompanyData)}
                rows={2}
                placeholder="Descreva as práticas de sustentabilidade..."
              />
            </div>
          </CompanyDataCard>

          {/* Impacto Social */}
          <CompanyDataCard
            fieldKey="social_impact"
            label="Impacto Social"
            category="Responsabilidade Social"
            
            isActive={companyData.lia_field_toggles?.social_impact ?? true}
            currentInstruction={companyData.lia_instructions?.social_impact || ''}
            isEditing={isEditingCompanyData}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
          >
            <div className="flex items-start gap-2">
              <Heart className="w-4 h-4 text-gray-400 dark:text-gray-500 mt-2" />
              <textarea
                value={companyData.social_impact || ''}
                onChange={(e) => setCompanyData((prev: any) => ({ ...prev, social_impact: e.target.value }))}
                disabled={!isEditingCompanyData}
                className={textareaClass(!isEditingCompanyData)}
                rows={2}
                placeholder="Descreva o impacto social da empresa..."
              />
            </div>
          </CompanyDataCard>
        </div>
      </div>

      {/* Seção: Perfil Organizacional (Big Five) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1 font-['Open_Sans',sans-serif]">
            Perfil Organizacional (Big Five)
          </h3>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveCultureFields}
            disabled={saving}
            className="text-micro rounded-md border-gray-300 hover:bg-gray-100 dark:border-gray-600 dark:hover:bg-gray-700"
          >
            {saving ? (
              <>
                <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                <Save className="w-3 h-3 mr-1.5 text-gray-700 dark:text-gray-300" />
                Salvar Perfil
              </>
            )}
          </Button>
        </div>
        
        <CompanyDataCard
          fieldKey="company_big_five"
          label="Perfil Cultural Big Five"
          category="Cultura Organizacional"
          
          isActive={companyData.lia_field_toggles?.company_big_five ?? true}
          currentInstruction={companyData.lia_instructions?.company_big_five || ''}
          isEditing={isEditingCompanyData}
          onToggleChange={updateLiaToggle}
          onInstructionSave={updateLiaInstruction}
        >
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-4">
            <BigFiveRadar
              scores={{
                openness: companyData.openness_score ?? 50,
                conscientiousness: companyData.conscientiousness_score ?? 50,
                extraversion: companyData.extraversion_score ?? 50,
                agreeableness: companyData.agreeableness_score ?? 50,
                stability: companyData.stability_score ?? 50,
              }}
              onScoresChange={(scores) => {
                if (!isEditingCompanyData) return
                setCompanyData((prev: any) => ({
                  ...prev,
                  openness_score: scores.openness,
                  conscientiousness_score: scores.conscientiousness,
                  extraversion_score: scores.extraversion,
                  agreeableness_score: scores.agreeableness,
                  stability_score: scores.stability,
                }))
              }}
              isEditable={isEditingCompanyData}
              size={200}
            />
          </div>
        </CompanyDataCard>
      </div>
    </div>
  )
}
