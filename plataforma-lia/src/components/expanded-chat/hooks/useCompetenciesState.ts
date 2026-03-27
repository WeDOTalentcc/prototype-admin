/**
 * useCompetenciesState
 *
 * Sprint 4.2 — 2026-03-27
 * Encapsula os ~20 estados relacionados às etapas de Competências (Stage 3-4).
 * Inclui: habilidades técnicas, comportamentais, modais de adição/edição,
 * sugestões da IA, e estado do painel de competências no chat.
 * Padrão { state, actions } compatível com Pinia stores (Vue 3).
 */

import { useState } from 'react'
import type { TechnicalSkill, BehavioralCompetency } from '../ExpandedChatContext'
import type { TechnicalSkillSuggestion, BehavioralCompetencySuggestion } from '../../job-creation/competencies-chat-message'

const DEFAULT_BEHAVIORAL_COMPETENCIES: BehavioralCompetency[] = [
  { id: '1', name: 'Comunicação Eficaz', weight: 4, justification: 'Colaboração com time multidisciplinar', enabled: true },
  { id: '2', name: 'Resolução de Problemas', weight: 5, justification: 'Arquitetura de sistemas complexos', enabled: true },
  { id: '3', name: 'Adaptabilidade', weight: 4, justification: 'Ambiente ágil com mudanças frequentes', enabled: true },
  { id: '4', name: 'Trabalho em Equipe', weight: 4, justification: 'Projetos colaborativos', enabled: true },
  { id: '5', name: 'Proatividade', weight: 3, justification: 'Iniciativa em melhorias técnicas', enabled: false },
]

export interface CompetencySuggestionsData {
  technicalSkills: TechnicalSkillSuggestion[]
  behavioralCompetencies: BehavioralCompetencySuggestion[]
}

export interface CompetenciesStateValues {
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  showAddCompetencyModal: boolean
  newCompetencyName: string
  newCompetencyJustification: string
  newSkillName: string
  editingCompetency: BehavioralCompetency | null
  showAddSkillModal: boolean
  newSkillCategory: 'language' | 'framework' | 'database' | 'tool'
  showSkipCompetenciesWarning: boolean
  competenciesPanelExpanded: boolean
  showCompetenciesSuggestionsModal: boolean
  suggestedTechnicalSkills: string[]
  suggestedBehavioralSkills: string[]
  selectedSuggestedTechnical: Set<string>
  selectedSuggestedBehavioral: Set<string>
  showCompetenciesInChat: boolean
  competenciesChatLoading: boolean
  competencySuggestions: CompetencySuggestionsData | null
  competenciesTab: 'technical' | 'behavioral'
}

export interface CompetenciesStateActions {
  setTechnicalSkills: React.Dispatch<React.SetStateAction<TechnicalSkill[]>>
  setBehavioralCompetencies: React.Dispatch<React.SetStateAction<BehavioralCompetency[]>>
  setShowAddCompetencyModal: React.Dispatch<React.SetStateAction<boolean>>
  setNewCompetencyName: React.Dispatch<React.SetStateAction<string>>
  setNewCompetencyJustification: React.Dispatch<React.SetStateAction<string>>
  setNewSkillName: React.Dispatch<React.SetStateAction<string>>
  setEditingCompetency: React.Dispatch<React.SetStateAction<BehavioralCompetency | null>>
  setShowAddSkillModal: React.Dispatch<React.SetStateAction<boolean>>
  setNewSkillCategory: React.Dispatch<React.SetStateAction<CompetenciesStateValues['newSkillCategory']>>
  setShowSkipCompetenciesWarning: React.Dispatch<React.SetStateAction<boolean>>
  setCompetenciesPanelExpanded: React.Dispatch<React.SetStateAction<boolean>>
  setShowCompetenciesSuggestionsModal: React.Dispatch<React.SetStateAction<boolean>>
  setSuggestedTechnicalSkills: React.Dispatch<React.SetStateAction<string[]>>
  setSuggestedBehavioralSkills: React.Dispatch<React.SetStateAction<string[]>>
  setSelectedSuggestedTechnical: React.Dispatch<React.SetStateAction<Set<string>>>
  setSelectedSuggestedBehavioral: React.Dispatch<React.SetStateAction<Set<string>>>
  setShowCompetenciesInChat: React.Dispatch<React.SetStateAction<boolean>>
  setCompetenciesChatLoading: React.Dispatch<React.SetStateAction<boolean>>
  setCompetencySuggestions: React.Dispatch<React.SetStateAction<CompetencySuggestionsData | null>>
  setCompetenciesTab: React.Dispatch<React.SetStateAction<CompetenciesStateValues['competenciesTab']>>
  resetAddCompetencyForm: () => void
  resetAddSkillForm: () => void
  resetSuggestionsModal: () => void
  resetCompetenciesState: () => void
}

export interface UseCompetenciesStateReturn {
  state: CompetenciesStateValues
  actions: CompetenciesStateActions
}

export function useCompetenciesState(): UseCompetenciesStateReturn {
  const [technicalSkills, setTechnicalSkills] = useState<TechnicalSkill[]>([])
  const [behavioralCompetencies, setBehavioralCompetencies] = useState<BehavioralCompetency[]>(DEFAULT_BEHAVIORAL_COMPETENCIES)
  const [showAddCompetencyModal, setShowAddCompetencyModal] = useState(false)
  const [newCompetencyName, setNewCompetencyName] = useState('')
  const [newCompetencyJustification, setNewCompetencyJustification] = useState('')
  const [newSkillName, setNewSkillName] = useState('')
  const [editingCompetency, setEditingCompetency] = useState<BehavioralCompetency | null>(null)
  const [showAddSkillModal, setShowAddSkillModal] = useState(false)
  const [newSkillCategory, setNewSkillCategory] = useState<CompetenciesStateValues['newSkillCategory']>('language')
  const [showSkipCompetenciesWarning, setShowSkipCompetenciesWarning] = useState(false)
  const [competenciesPanelExpanded, setCompetenciesPanelExpanded] = useState(true)
  const [showCompetenciesSuggestionsModal, setShowCompetenciesSuggestionsModal] = useState(false)
  const [suggestedTechnicalSkills, setSuggestedTechnicalSkills] = useState<string[]>([])
  const [suggestedBehavioralSkills, setSuggestedBehavioralSkills] = useState<string[]>([])
  const [selectedSuggestedTechnical, setSelectedSuggestedTechnical] = useState<Set<string>>(new Set())
  const [selectedSuggestedBehavioral, setSelectedSuggestedBehavioral] = useState<Set<string>>(new Set())
  const [showCompetenciesInChat, setShowCompetenciesInChat] = useState(false)
  const [competenciesChatLoading, setCompetenciesChatLoading] = useState(false)
  const [competencySuggestions, setCompetencySuggestions] = useState<CompetencySuggestionsData | null>(null)
  const [competenciesTab, setCompetenciesTab] = useState<CompetenciesStateValues['competenciesTab']>('technical')

  const resetAddCompetencyForm = () => {
    setShowAddCompetencyModal(false)
    setNewCompetencyName('')
    setNewCompetencyJustification('')
    setEditingCompetency(null)
  }

  const resetAddSkillForm = () => {
    setShowAddSkillModal(false)
    setNewSkillName('')
    setNewSkillCategory('language')
  }

  const resetSuggestionsModal = () => {
    setShowCompetenciesSuggestionsModal(false)
    setSuggestedTechnicalSkills([])
    setSuggestedBehavioralSkills([])
    setSelectedSuggestedTechnical(new Set())
    setSelectedSuggestedBehavioral(new Set())
  }

  const resetCompetenciesState = () => {
    setTechnicalSkills([])
    setBehavioralCompetencies(DEFAULT_BEHAVIORAL_COMPETENCIES)
    resetAddCompetencyForm()
    resetAddSkillForm()
    resetSuggestionsModal()
    setShowSkipCompetenciesWarning(false)
    setCompetenciesPanelExpanded(true)
    setShowCompetenciesInChat(false)
    setCompetenciesChatLoading(false)
    setCompetencySuggestions(null)
    setCompetenciesTab('technical')
  }

  return {
    state: {
      technicalSkills,
      behavioralCompetencies,
      showAddCompetencyModal,
      newCompetencyName,
      newCompetencyJustification,
      newSkillName,
      editingCompetency,
      showAddSkillModal,
      newSkillCategory,
      showSkipCompetenciesWarning,
      competenciesPanelExpanded,
      showCompetenciesSuggestionsModal,
      suggestedTechnicalSkills,
      suggestedBehavioralSkills,
      selectedSuggestedTechnical,
      selectedSuggestedBehavioral,
      showCompetenciesInChat,
      competenciesChatLoading,
      competencySuggestions,
      competenciesTab,
    },
    actions: {
      setTechnicalSkills,
      setBehavioralCompetencies,
      setShowAddCompetencyModal,
      setNewCompetencyName,
      setNewCompetencyJustification,
      setNewSkillName,
      setEditingCompetency,
      setShowAddSkillModal,
      setNewSkillCategory,
      setShowSkipCompetenciesWarning,
      setCompetenciesPanelExpanded,
      setShowCompetenciesSuggestionsModal,
      setSuggestedTechnicalSkills,
      setSuggestedBehavioralSkills,
      setSelectedSuggestedTechnical,
      setSelectedSuggestedBehavioral,
      setShowCompetenciesInChat,
      setCompetenciesChatLoading,
      setCompetencySuggestions,
      setCompetenciesTab,
      resetAddCompetencyForm,
      resetAddSkillForm,
      resetSuggestionsModal,
      resetCompetenciesState,
    },
  }
}
