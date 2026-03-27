/**
 * useSalaryState
 *
 * Sprint 4.2 — 2026-03-27
 * Encapsula os ~9 estados relacionados à etapa de Remuneração (Stage 5).
 * Inclui: salário, benefícios, benchmark de mercado, análise de compensação.
 * Padrão { state, actions } compatível com Pinia stores (Vue 3).
 */

import { useState } from 'react'
import type { SalaryInfo } from '../ExpandedChatContext'
import type { CompensationAnalysisResult } from '../../job-creation/compensation-analysis-panel'

const DEFAULT_SALARY_INFO: SalaryInfo = {
  minSalary: '',
  maxSalary: '',
  minBonus: '',
  maxBonus: '',
  bonusCriteria: '',
  benefits: [
    { id: '1', name: 'Vale Refeição', value: 'R$ 35/dia', enabled: true },
    { id: '2', name: 'Vale Transporte', enabled: true },
    { id: '3', name: 'Plano de Saúde', enabled: true },
    { id: '4', name: 'Plano Odontológico', enabled: true },
    { id: '5', name: 'Seguro de Vida', enabled: true },
    { id: '6', name: 'Stock Options', enabled: false },
    { id: '7', name: 'Auxílio Home Office', value: 'R$ 200/mês', enabled: true },
    { id: '8', name: 'Auxílio Educação', value: 'Até R$ 500/mês', enabled: true },
    { id: '9', name: 'Gympass', enabled: false },
    { id: '10', name: 'Day Off Aniversário', enabled: true },
  ],
}

export interface SalaryBenchmarkData {
  internal?: { min: number; max: number; median: number; sample_size: number; trend?: string }
  market?: { min: number; max: number; median: number; sources: string[]; confidence: string; learning_adjusted?: boolean }
  combined?: { min: number; max: number; median: number; confidence: string; recommendation: string }
}

export interface SalaryStateValues {
  salaryInfo: SalaryInfo
  showAddBenefitModal: boolean
  newBenefitName: string
  newBenefitValue: string
  salaryPanelExpanded: boolean
  showAutoFilledNotification: boolean
  salaryBenchmark: SalaryBenchmarkData | null
  isLoadingBenchmark: boolean
  compensationAnalysis: CompensationAnalysisResult | null
}

export interface SalaryStateActions {
  setSalaryInfo: React.Dispatch<React.SetStateAction<SalaryInfo>>
  setShowAddBenefitModal: React.Dispatch<React.SetStateAction<boolean>>
  setNewBenefitName: React.Dispatch<React.SetStateAction<string>>
  setNewBenefitValue: React.Dispatch<React.SetStateAction<string>>
  setSalaryPanelExpanded: React.Dispatch<React.SetStateAction<boolean>>
  setShowAutoFilledNotification: React.Dispatch<React.SetStateAction<boolean>>
  setSalaryBenchmark: React.Dispatch<React.SetStateAction<SalaryBenchmarkData | null>>
  setIsLoadingBenchmark: React.Dispatch<React.SetStateAction<boolean>>
  setCompensationAnalysis: React.Dispatch<React.SetStateAction<CompensationAnalysisResult | null>>
  resetBenefitForm: () => void
  resetSalaryState: () => void
}

export interface UseSalaryStateReturn {
  state: SalaryStateValues
  actions: SalaryStateActions
}

export function useSalaryState(): UseSalaryStateReturn {
  const [salaryInfo, setSalaryInfo] = useState<SalaryInfo>(DEFAULT_SALARY_INFO)
  const [showAddBenefitModal, setShowAddBenefitModal] = useState(false)
  const [newBenefitName, setNewBenefitName] = useState('')
  const [newBenefitValue, setNewBenefitValue] = useState('')
  const [salaryPanelExpanded, setSalaryPanelExpanded] = useState(true)
  const [showAutoFilledNotification, setShowAutoFilledNotification] = useState(false)
  const [salaryBenchmark, setSalaryBenchmark] = useState<SalaryBenchmarkData | null>(null)
  const [isLoadingBenchmark, setIsLoadingBenchmark] = useState(false)
  const [compensationAnalysis, setCompensationAnalysis] = useState<CompensationAnalysisResult | null>(null)

  const resetBenefitForm = () => {
    setShowAddBenefitModal(false)
    setNewBenefitName('')
    setNewBenefitValue('')
  }

  const resetSalaryState = () => {
    setSalaryInfo(DEFAULT_SALARY_INFO)
    resetBenefitForm()
    setSalaryPanelExpanded(true)
    setShowAutoFilledNotification(false)
    setSalaryBenchmark(null)
    setIsLoadingBenchmark(false)
    setCompensationAnalysis(null)
  }

  return {
    state: {
      salaryInfo,
      showAddBenefitModal,
      newBenefitName,
      newBenefitValue,
      salaryPanelExpanded,
      showAutoFilledNotification,
      salaryBenchmark,
      isLoadingBenchmark,
      compensationAnalysis,
    },
    actions: {
      setSalaryInfo,
      setShowAddBenefitModal,
      setNewBenefitName,
      setNewBenefitValue,
      setSalaryPanelExpanded,
      setShowAutoFilledNotification,
      setSalaryBenchmark,
      setIsLoadingBenchmark,
      setCompensationAnalysis,
      resetBenefitForm,
      resetSalaryState,
    },
  }
}
