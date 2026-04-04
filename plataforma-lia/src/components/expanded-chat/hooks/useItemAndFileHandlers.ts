"use client"

import React from "react"
import type {
  TechnicalSkill, BehavioralCompetency
} from '..'
import type { Message } from '../types'
import { cn } from "@/lib/utils"
import { type AnalysisResult, type AnalysisType } from "@/components/chat/multimodal-upload"
import { type ResumeAnalysisResponse } from "@/services/lia-api"
import { type Benefit } from '../ExpandedChatContext'

interface UseItemAndFileHandlersParams {
  newSkillCategory: string
  newBenefitName: string
  newBenefitValue: string
  newCompetencyName: string
  newCompetencyJustification: string
  detectedCriteria: {
    cargo: string | null
    gestorArea: string | null
    responsabilidades: string | null
    competenciasTecnicas: string[]
    competenciasComportamentais: string[]
    senioridadeIdiomas: string | null
    salario: string | null
    isAffirmative: boolean | null
    modeloTrabalho: string | null
    localizacao: string | null
    tipoContrato: string | null
    [key: string]: unknown
  }
  isFullscreen: boolean
  inline: boolean
  setTechnicalSkills: React.Dispatch<React.SetStateAction<TechnicalSkill[]>>
  setBehavioralCompetencies: React.Dispatch<React.SetStateAction<BehavioralCompetency[]>>
  setSalaryInfo: React.Dispatch<React.SetStateAction<{
    minSalary: string
    maxSalary: string
    benefits: Benefit[]
    [key: string]: unknown
  }>>
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setShowAddSkillModal: (v: boolean) => void
  setNewSkillName: (v: string) => void
  setShowAddBenefitModal: (v: boolean) => void
  setNewBenefitName: (v: string) => void
  setNewBenefitValue: (v: string) => void
  setShowAddCompetencyModal: (v: boolean) => void
  setNewCompetencyName: (v: string) => void
  setNewCompetencyJustification: (v: string) => void
  setUploadedFile: (v: File | null) => void
  setShowUploadModal: (v: boolean) => void
  setFileAnalysisResult: (v: AnalysisResult | null) => void
  setFileAnalysisType: (v: AnalysisType | null) => void
}

export function useItemAndFileHandlers({
  newSkillCategory,
  newBenefitName,
  newBenefitValue,
  newCompetencyName,
  newCompetencyJustification,
  detectedCriteria,
  isFullscreen,
  inline,
  setTechnicalSkills,
  setBehavioralCompetencies,
  setSalaryInfo,
  setMessages,
  setShowAddSkillModal,
  setNewSkillName,
  setShowAddBenefitModal,
  setNewBenefitName,
  setNewBenefitValue,
  setShowAddCompetencyModal,
  setNewCompetencyName,
  setNewCompetencyJustification,
  setUploadedFile,
  setShowUploadModal,
  setFileAnalysisResult,
  setFileAnalysisType,
}: UseItemAndFileHandlersParams) {
  const addNewSkill = (name: string) => {
    if (!name.trim()) return
    const newSkill: TechnicalSkill = {
      id: `skill-${Date.now()}`,
      name: name.trim(),
      level: 'Intermediário',
      required: false,
      category: newSkillCategory as 'general' | 'language' | 'framework' | 'database' | 'tool',
      weight: 2
    }
    setTechnicalSkills(prev => [...prev, newSkill])
    setShowAddSkillModal(false)
    setNewSkillName('')
  }

  const addNewBenefit = () => {
    if (!newBenefitName.trim()) return
    const newBenefit: Benefit = {
      id: `benefit-${Date.now()}`,
      name: newBenefitName.trim(),
      value: newBenefitValue.trim() || undefined,
      enabled: true
    }
    setSalaryInfo(prev => ({
      ...prev,
      benefits: [...prev.benefits, newBenefit]
    }))
    setShowAddBenefitModal(false)
    setNewBenefitName('')
    setNewBenefitValue('')
  }

  const addNewCompetency = () => {
    if (!newCompetencyName.trim()) return
    const newCompetency: BehavioralCompetency = {
      id: `comp-${Date.now()}`,
      name: newCompetencyName.trim(),
      weight: 3,
      justification: newCompetencyJustification.trim() || 'Competência adicionada pelo recrutador',
      enabled: true
    }
    setBehavioralCompetencies(prev => [...prev, newCompetency])
    setShowAddCompetencyModal(false)
    setNewCompetencyName('')
    setNewCompetencyJustification('')
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadedFile(file)
      setShowUploadModal(true)
    }
  }

  const handleFileAnalysisComplete = (result: AnalysisResult, type: AnalysisType) => {
    setFileAnalysisResult(result)
    setFileAnalysisType(type)
    setShowUploadModal(false)
    
    let analysisMessage = ''
    if (type === 'resume') {
      const resumeResult = result as ResumeAnalysisResponse
      analysisMessage = `📄 **Análise de Currículo**\n\n**Candidato:** ${resumeResult.candidate_name || 'Não identificado'}\n**Qualidade do Layout:** ${resumeResult.layout_score}%\n\n${resumeResult.improvement_suggestions.length > 0 ? `**Sugestões de Melhoria:**\n${resumeResult.improvement_suggestions.map(s => `• ${s}`).join('\n')}` : '✅ Currículo bem estruturado!'}`
    } else if (type === 'image') {
      analysisMessage = `🖼️ **Análise de Imagem**\n\n${(result as unknown as Record<string, unknown>).analysis || 'Análise concluída.'}`
    } else {
      analysisMessage = `📑 **Análise de Documento**\n\n${String((result as unknown as Record<string, unknown>).text_content || '').substring(0, 500) || 'Documento analisado com sucesso.'}`
    }
    
    const analysisMsg: Message = {
      id: `analysis-${Date.now()}`,
      role: 'assistant',
      content: analysisMessage,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, analysisMsg])
    setUploadedFile(null)
  }

  const handleFileAnalysisError = (error: string) => {
    const errorMsg: Message = {
      id: `error-${Date.now()}`,
      role: 'assistant',
      content: `❌ **Erro ao analisar arquivo:** ${error}`,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, errorMsg])
    setUploadedFile(null)
    setShowUploadModal(false)
  }

  const handleVoiceResponse = (response: { text: string; audio?: string }) => {
    const voiceMsg: Message = {
      id: `voice-${Date.now()}`,
      role: 'assistant',
      content: response.text,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, voiceMsg])
  }

  const getCriteriaStatus = (value: string | string[] | null) => {
    if (Array.isArray(value)) {
      return value.length > 0
    }
    return value !== null && value !== ''
  }

  const getUnifiedCargoLabel = () => {
    const cargo = detectedCriteria.cargo
    const seniority = detectedCriteria.senioridadeIdiomas
    if (cargo && seniority) {
      return `${cargo} ${seniority}`
    }
    return cargo || null
  }

  const detectedCriteriaItems = [
    { key: 'cargo', label: 'Cargo + Senioridade', value: getUnifiedCargoLabel() },
    { key: 'gestorArea', label: 'Gestor/Área', value: detectedCriteria.gestorArea },
    { key: 'responsabilidades', label: 'Principais responsabilidades', value: detectedCriteria.responsabilidades },
    { key: 'competenciasTecnicas', label: 'Competências técnicas (mín. 3)', value: detectedCriteria.competenciasTecnicas },
    { key: 'competenciasComportamentais', label: 'Comp. comportamentais (mín. 3)', value: detectedCriteria.competenciasComportamentais },
    { key: 'salario', label: 'Faixa salarial', value: detectedCriteria.salario },
    { key: 'isAffirmative', label: 'Vaga Afirmativa', value: detectedCriteria.isAffirmative !== null ? (detectedCriteria.isAffirmative ? 'Sim' : 'Não') : null },
  ]

  const companyDefaultsItems = [
    { key: 'modeloTrabalho', label: 'Modelo de trabalho', value: detectedCriteria.modeloTrabalho },
    { key: 'localizacao', label: 'Localização', value: detectedCriteria.localizacao },
    { key: 'tipoContrato', label: 'Tipo de contrato', value: detectedCriteria.tipoContrato },
  ]

  const criteriaItems = [...detectedCriteriaItems]

  const containerClasses = inline
    ? cn(
        "flex flex-col bg-lia-bg-primary overflow-hidden rounded-md border border-lia-border-subtle transition-colors duration-300 ease-in-out",
        isFullscreen 
          ? "fixed inset-4 z-50 animate-in zoom-in-95 duration-200" 
          : "h-full"
      )
    : cn(
        "fixed inset-0 z-50 bg-lia-overlay flex items-center justify-center",
        "animate-in fade-in-0 duration-200"
      )

  const contentClasses = inline
    ? "flex-1 flex flex-col bg-lia-bg-primary min-h-0 h-full transition-[width,height] duration-300"
    : cn(
        "bg-lia-bg-primary w-full rounded-md flex flex-col overflow-hidden border border-lia-btn-primary-bg transition-colors duration-300 ease-in-out",
        "animate-in fade-in-0 zoom-in-95 duration-300",
        isFullscreen 
          ? "max-w-[98vw] h-[95vh]" 
          : "max-w-5xl h-[85vh]"
      )

  return {
    addNewSkill,
    addNewBenefit,
    addNewCompetency,
    handleFileSelect,
    handleFileAnalysisComplete,
    handleFileAnalysisError,
    handleVoiceResponse,
    getCriteriaStatus,
    getUnifiedCargoLabel,
    detectedCriteriaItems,
    companyDefaultsItems,
    criteriaItems,
    containerClasses,
    contentClasses,
  }
}
