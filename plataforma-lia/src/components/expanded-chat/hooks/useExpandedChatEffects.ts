"use client"

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react"
import type {
  DetectedCriteria, BasicInfoFields, WizardStage,
  TechnicalSkill, BehavioralCompetency, SalaryInfo, WSIQuestion,
  ExtendedWizardStageConfig
} from '..'
import type { Message, WizardDraftData } from '../types'
import type { Benefit } from '../stages/SalaryStage'
import {
  WIZARD_STAGES, getMissingCriticalFields, DRAFT_DETECTED_MESSAGE,
  INITIAL_JOB_CREATION_MESSAGE, FROM_SCRATCH_ORIENTATION_MESSAGE
} from '..'
import { liaApi } from "@/services/lia-api"
import { useWSIQualityGates } from '.'
import { useWizardAutoSave } from "@/hooks/use-wizard-auto-save"
import { Plus, Brain } from "lucide-react"

import { useExpandedChatProactiveHandlers } from "./useExpandedChatProactiveHandlers"
import { useCompanyConfigLoader } from "./useCompanyConfigLoader"
import { useCompanyId } from "@/hooks/useCompanyId"
export function useExpandedChatEffects(ctx) {
  const {
    INITIAL_STAGES, PROACTIVE_MESSAGE_DELAY, analytics, approvedCandidates,
    awaitingWSIRegenerationConfirmation, basicInfoFields, behavioralCompetencies, calibrationComplete, calibrationProactiveTimerRef,
    calibrationStageCompletionShown, checkForExistingDraftSync, companyConfig, companyDefaultQuestions, competenciesProactiveTimerRef,
    competenciesStageCompletionShown, configLoaded, currentStage, detectedCriteria, displayedText,
    fastTrack, fastTrackOriginalCompetencies, generatedJobDescription, initialLiaMessage,
    initialMessages, inputEvaluationProactiveTimerRef, inputEvaluationStageCompletionShown, inputRef, internalJobCreationMode,
    isJobCreationMode, isOpen, isResizing, isTypingEffect, jobConfig,
    jobDescription, learning, messages, messagesEndRef,
    mode, proactiveActionIds, rejectedCandidates,
    resizeRef, salaryBenchmark, salaryInfo, salaryProactiveTimerRef, salaryStageCompletionShown,
    setAwaitingStageAdvanceConfirmation, setAwaitingWSIRegenerationConfirmation, setBasicInfoFields, setBehavioralCompetencies,
    setCalibrationStageCompletionShown, setCompanyConfig, setCompanyDefaultQuestions, setCompetenciesPanelExpanded, setCompetenciesStageCompletionShown,
    setConfigLoaded, setCurrentStage, setDetectedCriteria, setDisplayedText, setFastTrackMessageSent,
    setFieldOrigins, setFieldsFromConfig, setGeneratedJobDescription, setInputEvaluationStageCompletionShown, setInputValue,
    setIsLoadingBenchmark, setIsResizing, setIsTypingEffect, setJobConfig, setMessages,
    setPanelWidth, setProactiveActionIds, setSalaryBenchmark, setSalaryInfo, setSalaryPanelExpanded,
    setSalaryStageCompletionShown, setShowAutoFilledNotification, setTechnicalSkills, setWizardGreeting, setWizardGreetingLoaded,
    setWsiCandidates, setWsiQuestionsStageCompletionShown, setWsiRegenerationPrompted, sla,
    technicalSkills, typingTimeoutRef, user,
    wizardGreeting, wsiCandidates, wsiQuestionsProactiveTimerRef, wsiQuestionsStageCompletionShown, wsiRegenerationPrompted,
    publishingState, publishingActions, wizardDraftId, STAGE_DISPLAY_NAMES,
    onMessagesUpdate, isLoadingEligibilityQuestions, companyEligibilityQuestions,
    isLoadingStages,
  } = ctx

  const { companyId: resolvedTenantId } = useCompanyId()

  useEffect(() => {
    if (!fastTrackOriginalCompetencies || wsiRegenerationPrompted || awaitingWSIRegenerationConfirmation) {
      return
    }
    
    // Get current competency names
    const currentTechnicalSkillNames = technicalSkills.map(s => s.name.toLowerCase())
    const currentBehavioralNames = behavioralCompetencies.map(c => c.name.toLowerCase())
    
    // Check if competencies have changed
    const technicalAdded = currentTechnicalSkillNames.filter(
      n => !fastTrackOriginalCompetencies.technicalSkillNames.includes(n)
    )
    const technicalRemoved = fastTrackOriginalCompetencies.technicalSkillNames.filter(
      n => !currentTechnicalSkillNames.includes(n)
    )
    const behavioralAdded = currentBehavioralNames.filter(
      n => !fastTrackOriginalCompetencies.behavioralCompetencyNames.includes(n)
    )
    const behavioralRemoved = fastTrackOriginalCompetencies.behavioralCompetencyNames.filter(
      n => !currentBehavioralNames.includes(n)
    )
    
    const hasChanges = technicalAdded.length > 0 || technicalRemoved.length > 0 || 
                       behavioralAdded.length > 0 || behavioralRemoved.length > 0
    
    if (hasChanges && currentStage === 'competencies') {
      setWsiRegenerationPrompted(true)
      setAwaitingWSIRegenerationConfirmation(true)
      
      const changesSummary = [
        ...technicalAdded.map(n => `+${n}`),
        ...technicalRemoved.map(n => `-${n}`),
        ...behavioralAdded.map(n => `+${n}`),
        ...behavioralRemoved.map(n => `-${n}`)
      ].slice(0, 5).join(', ')
      
      const wsiRegenMessage: Message = {
        id: `wsi-regen-prompt-${Date.now()}`,
        role: 'assistant',
        content: `Percebi que você alterou algumas competências (${changesSummary}${technicalAdded.length + technicalRemoved.length + behavioralAdded.length + behavioralRemoved.length > 5 ? '...' : ''}).\n\n**Quer que eu atualize as perguntas WSI** para refletir essas mudanças? As perguntas atuais foram geradas com base nas competências anteriores.`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, wsiRegenMessage])
    }
  }, [technicalSkills, behavioralCompetencies, fastTrackOriginalCompetencies, wsiRegenerationPrompted, awaitingWSIRegenerationConfirmation, currentStage, setAwaitingWSIRegenerationConfirmation, setMessages, setWsiRegenerationPrompted])
  
  // Reset message sent flag when suggestions change (new set of suggestions = new prompt)
  const suggestionsKey = fastTrack.suggestions.map(s => s.job_id).join(',')
  const prevSuggestionsKeyRef = useRef(suggestionsKey)
  useEffect(() => {
    if (suggestionsKey !== prevSuggestionsKeyRef.current && suggestionsKey !== '') {
      setFastTrackMessageSent(false)
      prevSuggestionsKeyRef.current = suggestionsKey
    }
  }, [suggestionsKey, setFastTrackMessageSent])
  
  // State to track if learning suggestions have been applied
  const [learningSuggestionsApplied, setLearningSuggestionsApplied] = useState(false)
  
  // Apply learning suggestions to wizard fields when available
  useEffect(() => {
    if (!learning.suggestions || !learning.suggestions.has_suggestions || learningSuggestionsApplied) {
      return
    }
    
    const { salary, skills, behavioral } = learning.suggestions
    
    // Apply salary suggestions if no salary is set
    if (salary?.has_suggestion && salary.min_salary && salary.max_salary) {
      if (!salaryInfo.minSalary && !salaryInfo.maxSalary) {
        setSalaryInfo(prev => ({
          ...prev,
          minSalary: salary.min_salary!.toLocaleString('pt-BR'),
          maxSalary: salary.max_salary!.toLocaleString('pt-BR')
        }))
        analytics.trackFieldUpdate('salario', 'suggestion')
        analytics.trackSuggestion('salary', true)
      }
    }
    
    // Apply skills suggestions if no skills are set
    if (skills?.has_recommendations && skills.recommended_skills?.length && technicalSkills.length === 0) {
      const newSkills: TechnicalSkill[] = skills.recommended_skills.slice(0, 5).map((skill, idx) => ({
        id: `learning-skill-${idx}`,
        name: skill.name,
        level: 'Intermediário' as const,
        required: skill.score > 0.7,
        category: 'tool' as const,
        weight: Math.round(skill.score * 5),
        isWeightInferred: true
      }))
      setTechnicalSkills(newSkills)
      analytics.trackFieldUpdate('technicalSkills', 'suggestion')
      analytics.trackSuggestion('skills', true)
    }
    
    // Apply behavioral suggestions if no behavioral competencies are set
    if (behavioral?.has_recommendations && behavioral.recommended_behavioral?.length && behavioralCompetencies.length === 0) {
      const newBehavioral: BehavioralCompetency[] = behavioral.recommended_behavioral.slice(0, 3).map((comp, idx) => ({
        id: `learning-behavioral-${idx}`,
        name: comp.name,
        weight: Math.round(comp.score * 5),
        justification: 'Sugerido com base em padrões de vagas similares',
        enabled: true,
        isWeightInferred: true
      }))
      setBehavioralCompetencies(newBehavioral)
      analytics.trackFieldUpdate('behavioralCompetencies', 'suggestion')
      analytics.trackSuggestion('behavioral', true)
    }
    
    setLearningSuggestionsApplied(true)
  }, [learning.suggestions, learningSuggestionsApplied, salaryInfo.minSalary, salaryInfo.maxSalary, technicalSkills.length, behavioralCompetencies.length, analytics, setBehavioralCompetencies, setSalaryInfo, setTechnicalSkills])
  
  // Reset learning suggestions when job title changes
  useEffect(() => {
    setLearningSuggestionsApplied(false)
  }, [detectedCriteria?.cargo])
  
  // Helper to check if a field should be shown (is required based on catalog maturity)
  const isFieldRequiredForWizard = useCallback((fieldName: string): boolean => {
    if (!wizardGreeting?.catalog_status?.required_fields_for_wizard) {
      return true // Show all fields if no data available
    }
    return wizardGreeting.catalog_status.required_fields_for_wizard.includes(fieldName)
  }, [wizardGreeting])
  
  // Effect to auto-collapse sections based on catalog maturity
  useEffect(() => {
    if (wizardGreeting?.catalog_status) {
      const isComplete = wizardGreeting.catalog_status.maturity_level === 'complete'
      const isPartial = wizardGreeting.catalog_status.maturity_level === 'partial'
      
      // For complete/partial maturity, collapse non-required sections by default
      if (isComplete || isPartial) {
        if (!isFieldRequiredForWizard('salario')) {
          setSalaryPanelExpanded(false)
        }
        if (!isFieldRequiredForWizard('competencias')) {
          setCompetenciesPanelExpanded(false)
        }
        // Show notification if any fields were auto-filled
        if (!isFieldRequiredForWizard('salario') || !isFieldRequiredForWizard('competencias')) {
          setShowAutoFilledNotification(true)
          // Auto-hide after 10 seconds
          const autoHideTimer = setTimeout(() => setShowAutoFilledNotification(false), 10000)
          return () => clearTimeout(autoHideTimer)
        }
      }
    }
  }, [wizardGreeting, isFieldRequiredForWizard, setCompetenciesPanelExpanded, setSalaryPanelExpanded, setShowAutoFilledNotification])
  
  // Publishing state — company members, languages (from usePublishingState — Sprint 4.2)
  const { companyMembersMap, languagesUserEdited } = publishingState
  const { setCompanyMembersMap, setLanguagesUserEdited } = publishingActions

  // Determine if we're in job creation mode (either from prop or internal state)
  const isInJobCreationMode = isJobCreationMode || internalJobCreationMode

  // Extract languages from conversation messages (only once, when not edited by user)
  useEffect(() => {
    if (languagesUserEdited || jobConfig.languages.length > 0) return // Don't overwrite user edits

    const languagePatterns = [
      { pattern: /ingl[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Inglês' },
      { pattern: /espanhol\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Espanhol' },
      { pattern: /franc[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Francês' },
      { pattern: /alem[aã]o\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Alemão' },
      { pattern: /italiano\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Italiano' },
      { pattern: /mandarim\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Mandarim' },
      { pattern: /japon[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Japonês' },
    ]

    const allText = messages.map(m => m.content).join(' ').toLowerCase()
    const detectedLanguages: { name: string; level: string }[] = []

    languagePatterns.forEach(({ pattern, name }) => {
      const match = allText.match(pattern)
      if (match) {
        const fullMatch = match[0].toLowerCase()
        let level = 'Intermediário'
        if (fullMatch.includes('fluente') || fullMatch.includes('avançado') || fullMatch.includes('avancado')) {
          level = 'Avançado'
        } else if (fullMatch.includes('básico') || fullMatch.includes('basico')) {
          level = 'Básico'
        }
        detectedLanguages.push({ name, level })
      }
    })

    if (detectedLanguages.length > 0) {
      setJobConfig(prev => ({ ...prev, languages: detectedLanguages }))
    }
  }, [messages, languagesUserEdited, jobConfig.languages.length, setJobConfig])
  
  // Check if we have any config data
  const hasConfigData = companyConfig && (
    companyConfig.workModel ||
    (companyConfig.techStack && companyConfig.techStack.length > 0) ||
    (companyConfig.departments && companyConfig.departments.length > 0) ||
    (companyConfig.benefits && companyConfig.benefits.length > 0) ||
    companyConfig.headquarters ||
    (companyConfig.locations && companyConfig.locations.length > 0)
  )
  
  // Check if minimum competencies are met for competencies stage
  const hasMinimumCompetencies = technicalSkills.length >= 3 && behavioralCompetencies.filter(c => c.enabled).length >= 3
  
  // WSI Quality Gates - calculate completeness score
  const wsiQualityGates = useWSIQualityGates({
    technicalSkills,
    behavioralCompetencies,
    detectedCriteria,
    generatedJobDescription,
    minScoreToAdvance: 70,
  })
  
  // State for draft restoration (must be before hook to avoid race condition)
  const [hasAppliedRestoredDraft, setHasAppliedRestoredDraft] = useState(false)
  
  // State to track if we're awaiting user choice about existing draft
  const [awaitingDraftChoice, setAwaitingDraftChoice] = useState(false)
  const [pendingDraftData, setPendingDraftData] = useState<typeof loadedDraft | null>(null)
  
  // Reset restoration flag when wizard mode changes (for re-entry scenarios)
  useEffect(() => {
    if (!isJobCreationMode) {
      setHasAppliedRestoredDraft(false)
    }
  }, [isJobCreationMode])
  
  // Auto-save hook for wizard draft
  const { isSaving: isAutoSaving, lastSavedAt: autoSaveLastSaved, hasPendingChanges, saveNow: saveWizardDraft, clearDraft: clearWizardDraft, loadedDraft, hasRestoredDraft, hasAttemptedRestore, getLastSavedText } = useWizardAutoSave(
    {
      jobDraftId: wizardDraftId,
      basicInfoFields: {
        jobTitle: basicInfoFields.cargo,
        department: basicInfoFields.area,
        manager: basicInfoFields.gestor,
        locality: basicInfoFields.localidade,
        workModel: basicInfoFields.modeloTrabalho,
        employmentType: basicInfoFields.tipoContrato
      },
      salaryInfo: salaryInfo,
      technicalSkills,
      behavioralCompetencies,
      wsiCandidates,
      currentStage: currentStage,
      jobDescription: generatedJobDescription || ''
    },
    { enabled: isJobCreationMode, saveInterval: 30000, jobDraftId: wizardDraftId, skipUntilRestored: !hasAppliedRestoredDraft }
  )
  
  useEffect(() => {
    const fetchProactiveSuggestions = async () => {
      try {
        const companyId = resolvedTenantId ?? ''
        const res = await fetch(`/api/backend-proxy/proactive-actions?path=feed/${companyId}&limit=5`)
        if (!res.ok) return
        const data = await res.json()
        if (!Array.isArray(data) || data.length === 0) return

        const newSuggestions = data.filter((s: Record<string, unknown>) => !proactiveActionIds.has(s.id))
        if (newSuggestions.length === 0) return

        const newIds = new Set(proactiveActionIds)
        const proactiveMessages = newSuggestions.map((s: Record<string, unknown>) => {
          newIds.add(s.id)
          return {
            id: `proactive-${s.id}`,
            role: 'assistant' as const,
            content: String(s.message || s.title || ''),
            timestamp: new Date((s.created_at as string) || Date.now()),
            messageType: 'proactive' as const,
            proactiveData: {
              actionId: String(s.id),
              severity: String(s.severity || 'info'),
              actionLabel: String(s.action_label || 'Executar'),
              suggestedAction: (s.suggested_action || {}) as Record<string, unknown>,
            },
          }
        }) as Message[]

        setProactiveActionIds(newIds)
        setMessages(prev => [...prev, ...proactiveMessages])
      } catch (err) {
        // Silent fail - proactive suggestions are non-critical
      }
    }

    const timer = setTimeout(fetchProactiveSuggestions, 10000)
    const interval = setInterval(fetchProactiveSuggestions, 300000)
    return () => {
      clearTimeout(timer)
      clearInterval(interval)
    }
  }, [user, proactiveActionIds, setMessages, setProactiveActionIds, resolvedTenantId])

  // Detect draft and show choice message instead of auto-restoring
  // NOTE: The synchronous check in checkForExistingDraftSync() handles immediate UI feedback
  // This useEffect handles loading draft data from the hook and storing it for restoration
  // It only adds a message if the synchronous check didn't already handle it
  useEffect(() => {
    if (hasRestoredDraft && loadedDraft && !hasAppliedRestoredDraft && isJobCreationMode) {
      // Check if draft has meaningful content (beyond initial stages)
      const currentStage = loadedDraft.currentStage as string
      const hasMeaningfulDraft = currentStage && !INITIAL_STAGES.includes(currentStage)
      
      if (hasMeaningfulDraft) {
        // Always store pending draft data for restoration when user chooses "continue"
        // This ensures the data is available even if sync check already showed the message
        if (!pendingDraftData) {
          setPendingDraftData(loadedDraft)
        }
        
        // Only add the message if we're not already awaiting draft choice
        // (synchronous check in button handler may have already shown the message and set this flag)
        if (!awaitingDraftChoice) {
          setAwaitingDraftChoice(true)
          
          // Use unified stage name mapping
          const stageName = STAGE_DISPLAY_NAMES[currentStage] || currentStage
          
          // Add message asking user what to do
          const draftChoiceMessage: Message = {
            id: `draft-choice-${Date.now()}`,
            role: 'assistant' as const,
            content: DRAFT_DETECTED_MESSAGE(stageName),
            timestamp: new Date()
          }
          setMessages(prev => [...prev, draftChoiceMessage])
        }
        
        // Don't enable auto-save yet - wait for user choice
      } else {
        // No meaningful draft, proceed normally
        setHasAppliedRestoredDraft(true)
      }
    } else if (isJobCreationMode && !hasAppliedRestoredDraft && hasAttemptedRestore && !loadedDraft && !awaitingDraftChoice) {
      // No draft to restore and restore attempt is complete - enable auto-save
      // This handles new sessions without any saved draft
      setHasAppliedRestoredDraft(true)
    }
  }, [hasRestoredDraft, loadedDraft, hasAppliedRestoredDraft, isJobCreationMode, hasAttemptedRestore, awaitingDraftChoice, INITIAL_STAGES, STAGE_DISPLAY_NAMES, pendingDraftData, setMessages])
  
  // Helper function to apply pending draft data
  const applyPendingDraft = useCallback(() => {
    if (!pendingDraftData) return
    
    // Restore basic info fields
    if (pendingDraftData.basicInfoFields) {
      const bf = pendingDraftData.basicInfoFields
      setBasicInfoFields({
        cargo: bf.jobTitle || '',
        area: bf.department || bf.area || '',
        gestor: bf.manager || '',
        localidade: bf.locality || '',
        modeloTrabalho: bf.workModel || '',
        tipoContrato: bf.employmentType || ''
      })
    }
    
    // Restore salary info
    if (pendingDraftData.salaryInfo) {
      setSalaryInfo(pendingDraftData.salaryInfo)
    }
    
    // Restore technical skills
    if (pendingDraftData.technicalSkills && pendingDraftData.technicalSkills.length > 0) {
      setTechnicalSkills(pendingDraftData.technicalSkills)
    }
    
    // Restore behavioral competencies
    if (pendingDraftData.behavioralCompetencies && pendingDraftData.behavioralCompetencies.length > 0) {
      setBehavioralCompetencies(pendingDraftData.behavioralCompetencies)
    }
    
    // Restore WSI candidates
    if (pendingDraftData.wsiCandidates && pendingDraftData.wsiCandidates.length > 0) {
      setWsiCandidates(pendingDraftData.wsiCandidates)
    }
    
    // Restore current stage
    if (pendingDraftData.currentStage) {
      setCurrentStage(pendingDraftData.currentStage as WizardStage)
    }
    
    // Restore job description
    if (pendingDraftData.jobDescription) {
      setGeneratedJobDescription(pendingDraftData.jobDescription)
    }
    
    // Clear pending state and enable auto-save
    setPendingDraftData(null)
    setAwaitingDraftChoice(false)
    setHasAppliedRestoredDraft(true)
  }, [pendingDraftData, setBasicInfoFields, setBehavioralCompetencies, setCurrentStage, setGeneratedJobDescription, setSalaryInfo, setTechnicalSkills, setWsiCandidates])
  
  // Update basic info fields when criteria are detected
  useEffect(() => {
    if (detectedCriteria.cargo && !basicInfoFields.cargo) {
      setBasicInfoFields(prev => ({ ...prev, cargo: detectedCriteria.cargo || '' }))
    }
    if (detectedCriteria.gestorArea && !basicInfoFields.gestor) {
      setBasicInfoFields(prev => ({ ...prev, gestor: detectedCriteria.gestorArea || '' }))
    }
    if (detectedCriteria.localizacao && !basicInfoFields.localidade) {
      setBasicInfoFields(prev => ({ ...prev, localidade: detectedCriteria.localizacao || '' }))
    }
    if (detectedCriteria.modeloTrabalho && !basicInfoFields.modeloTrabalho) {
      setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: detectedCriteria.modeloTrabalho || '' }))
    }
    if (detectedCriteria.tipoContrato && !basicInfoFields.tipoContrato) {
      setBasicInfoFields(prev => ({ ...prev, tipoContrato: detectedCriteria.tipoContrato || '' }))
    }
    if (detectedCriteria.departamento && !basicInfoFields.area) {
      setBasicInfoFields(prev => ({ ...prev, area: detectedCriteria.departamento || '' }))
    }
    
    // Update technical skills when detected
    if (detectedCriteria.competenciasTecnicas.length > 0) {
      const skillCategories: Record<string, 'language' | 'framework' | 'database' | 'tool'> = {
        'Python': 'language', 'JavaScript': 'language', 'TypeScript': 'language', 'Java': 'language',
        'Go': 'language', 'Rust': 'language', 'C#': 'language', 'Ruby': 'language', 'PHP': 'language',
        'Swift': 'language', 'Kotlin': 'language', 'Scala': 'language',
        'React': 'framework', 'Angular': 'framework', 'Vue': 'framework', 'Django': 'framework',
        'FastAPI': 'framework', 'Flask': 'framework', 'Spring': 'framework', 'Rails': 'framework',
        'Laravel': 'framework', 'Express': 'framework', 'Next.js': 'framework', 'Node': 'framework',
        'Nodejs': 'framework', 'React Native': 'framework', 'Flutter': 'framework',
        'PostgreSQL': 'database', 'MySQL': 'database', 'MongoDB': 'database', 'Redis': 'database',
        'Elasticsearch': 'database', 'SQL': 'database', 'Oracle': 'database', 'Cassandra': 'database',
        'Docker': 'tool', 'Kubernetes': 'tool', 'AWS': 'tool', 'Azure': 'tool', 'GCP': 'tool',
        'Git': 'tool', 'Jenkins': 'tool', 'Terraform': 'tool', 'Ansible': 'tool', 'Linux': 'tool',
        'Kafka': 'tool', 'RabbitMQ': 'tool', 'GraphQL': 'tool', 'CI/CD': 'tool',
      }
      
      const baseTs = Date.now()
      const newSkills: TechnicalSkill[] = detectedCriteria.competenciasTecnicas.map((skill, index) => ({
        id: `skill-${baseTs}-${index}-${Math.random().toString(36).slice(2, 6)}`,
        name: skill,
        level: 'Avançado' as const,
        required: index < 3,
        category: skillCategories[skill] || 'tool',
        weight: index < 3 ? 3 : 2
      }))
      
      setTechnicalSkills(prev => {
        const existingNames = prev.map(s => s.name.toLowerCase())
        const filteredNew = newSkills.filter(s => !existingNames.includes(s.name.toLowerCase()))
        return [...prev, ...filteredNew]
      })
      
      // Auto-select department based on detected technical skills
      if (!basicInfoFields.area) {
        const skillsLower = detectedCriteria.competenciasTecnicas.map(s => s.toLowerCase())
        
        // Tech/IT skills
        const techSkills = ['python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue', 'django', 'fastapi', 'flask', 'spring', 'node', 'nodejs', 'go', 'rust', 'c#', '.net', 'ruby', 'rails', 'php', 'swift', 'kotlin', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'devops', 'ci/cd', 'backend', 'frontend', 'full stack', 'fullstack', 'mobile', 'microservices']
        const hasTechSkills = skillsLower.some(s => techSkills.some(ts => s.includes(ts)))
        
        // Data/BI skills - only very specific data roles, NOT generic SQL or "data" which are common in all tech
        const dataSkills = ['data science', 'machine learning', 'power bi', 'tableau', 'data analyst', 'data engineer', 'big data', 'spark', 'hadoop', 'etl', 'data warehouse', 'estatística', 'estatistica', 'cientista de dados', 'engenheiro de dados', 'analista de dados']
        const hasDataSkills = skillsLower.some(s => dataSkills.some(ds => s.includes(ds)))
        
        // Design skills
        const designSkills = ['figma', 'ui', 'ux', 'design', 'photoshop', 'illustrator', 'sketch', 'xd', 'protótipo', 'prototipo', 'wireframe']
        const hasDesignSkills = skillsLower.some(s => designSkills.some(ds => s.includes(ds)))
        
        // Marketing skills
        const marketingSkills = ['marketing', 'seo', 'sem', 'google ads', 'facebook ads', 'analytics', 'mídia', 'midia', 'growth', 'inbound', 'conteúdo', 'conteudo', 'copywriting']
        const hasMarketingSkills = skillsLower.some(s => marketingSkills.some(ms => s.includes(ms)))
        
        // Sales/Commercial skills
        const salesSkills = ['sales', 'vendas', 'salesforce', 'crm', 'hubspot', 'pipedrive', 'prospecção', 'prospeccao', 'negociação', 'negociacao', 'comercial']
        const hasSalesSkills = skillsLower.some(s => salesSkills.some(ss => s.includes(ss)))
        
        // Finance/Operations skills - include excel as a finance indicator
        const financeSkills = ['sap', 'erp', 'oracle', 'totvs', 'contabilidade', 'financeiro', 'fiscal', 'controladoria', 'excel avançado', 'excel']
        const hasFinanceSkills = skillsLower.some(s => financeSkills.some(fs => s.includes(fs)))
        
        // Determine department based on skill priorities
        // IMPORTANT: Tech skills have priority - developers with SQL should still be Tecnologia/TI
        let selectedArea = ''
        if (hasTechSkills) {
          selectedArea = 'Tecnologia/TI'
        } else if (hasDataSkills) {
          // Only Dados/BI if no core tech skills detected
          selectedArea = 'Dados/BI'
        } else if (hasDesignSkills) {
          selectedArea = 'Design'
        } else if (hasMarketingSkills) {
          selectedArea = 'Marketing'
        } else if (hasSalesSkills) {
          selectedArea = 'Comercial'
        } else if (hasFinanceSkills) {
          selectedArea = 'Financeiro'
        }
        
        if (selectedArea) {
          setBasicInfoFields(prev => ({ ...prev, area: selectedArea }))
        }
      }
    }
    
    // Also try to detect area from job title if not yet selected
    if (!basicInfoFields.area && detectedCriteria.cargo) {
      const cargoLower = detectedCriteria.cargo.toLowerCase()
      
      // Map cargo keywords to areas
      const areaKeywords: Record<string, string[]> = {
        'Fiscal/Tributário': ['impostos', 'fiscal', 'tributário', 'tributario', 'tax', 'tributos', 'imposto', 'icms', 'pis', 'cofins', 'irpj', 'csll', 'sped', 'obrigações acessórias', 'obrigacoes acessorias'],
        'Financeiro': ['financeiro', 'financeira', 'finanças', 'financas', 'controladoria', 'contábil', 'contabil', 'tesouraria', 'planejamento financeiro', 'fp&a', 'controller', 'contabilidade'],
        'Recursos Humanos': ['rh', 'recursos humanos', 'people', 'gente', 'talent', 'talentos', 'recrutamento', 'seleção', 'selecao', 'dp', 'departamento pessoal', 'cultura', 'treinamento'],
        'Comercial': ['comercial', 'vendas', 'sales', 'account', 'cliente', 'negócios', 'negocios', 'business'],
        'Marketing': ['marketing', 'comunicação', 'comunicacao', 'branding', 'brand', 'mídia', 'midia', 'digital'],
        'Operações': ['operações', 'operacoes', 'operacional', 'logística', 'logistica', 'supply', 'suprimentos', 'compras', 'procurement'],
        'Jurídico': ['jurídico', 'juridico', 'legal', 'compliance', 'contratos'],
        'Tecnologia/TI': ['tecnologia', 'ti', 'sistemas', 'desenvolvimento', 'software', 'infraestrutura', 'dados', 'data', 'produto', 'product'],
        'Administrativo': ['administrativo', 'administrativa', 'facilities', 'escritório', 'escritorio', 'secretaria'],
        'Qualidade': ['qualidade', 'quality', 'processos', 'melhoria contínua'],
      }
      
      for (const [area, keywords] of Object.entries(areaKeywords)) {
        if (keywords.some(kw => cargoLower.includes(kw))) {
          setBasicInfoFields(prev => ({ ...prev, area }))
          break
        }
      }
    }
  }, [detectedCriteria, basicInfoFields.area, basicInfoFields.cargo, basicInfoFields.gestor, basicInfoFields.localidade, basicInfoFields.modeloTrabalho, basicInfoFields.tipoContrato, setBasicInfoFields, setTechnicalSkills])

  const quickSuggestions = [
    "Anexar JD",
    "Usar anterior",
    "Ver exemplos"
  ]

  const suggestionTags = [
    { label: "Criar vaga", icon: Plus, action: "criar_vaga" },
    { label: "Sugerir melhorias", icon: Brain, action: "sugerir_melhorias" },
  ]

  const typeText = useCallback((text: string, messageId: string) => {
    setIsTypingEffect(true)
    let currentIndex = 0
    const speed = 12

    const typeNextChar = () => {
      if (currentIndex < text.length) {
        setDisplayedText(text.slice(0, currentIndex + 1))
        currentIndex++
        typingTimeoutRef.current = setTimeout(typeNextChar, speed)
      } else {
        setIsTypingEffect(false)
        setMessages(prev => prev.map(msg => 
          msg.id === messageId ? { ...msg, isTyping: false } : msg
        ))
      }
    }

    typeNextChar()
  }, [setDisplayedText, setIsTypingEffect, setMessages, typingTimeoutRef])

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      if (initialMessages && initialMessages.length > 0) {
        const convertedMessages: Message[] = initialMessages.map(m => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: m.timestamp,
          isTyping: false
        }))
        setMessages(convertedMessages)
        setDisplayedText("")
      } else {
        const messageToShow = isJobCreationMode 
          ? INITIAL_JOB_CREATION_MESSAGE 
          : initialLiaMessage
        
        const initialMsg: Message = {
          id: 'initial-lia',
          role: 'assistant',
          content: messageToShow,
          timestamp: new Date(),
          isTyping: true
        }
        setMessages([initialMsg])
        setDisplayedText("")
        const initTimer = setTimeout(() => {
          typeText(messageToShow, 'initial-lia')
        }, 100)
        return () => clearTimeout(initTimer)
      }
    }
  }, [isOpen, messages.length, typeText, initialLiaMessage, initialMessages, isJobCreationMode, setDisplayedText, setMessages])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, displayedText, messagesEndRef])

  useEffect(() => {
    if (isOpen && !isTypingEffect) {
      inputRef.current?.focus()
    }
  }, [isOpen, isTypingEffect, inputRef])

  // Sync messages back to parent component for persistence across fullscreen transitions
  // Use ref to avoid infinite loop caused by callback changing on every render
  const onMessagesUpdateRef = useRef(onMessagesUpdate)
  onMessagesUpdateRef.current = onMessagesUpdate
  
  const lastSyncedMessagesRef = useRef<string>('')
  
  useEffect(() => {
    if (messages.length > 0) {
      // Only sync if messages actually changed (avoid infinite loop)
      const messagesKey = messages.map(m => `${m.id}:${m.content.substring(0, 50)}`).join('|')
      if (messagesKey !== lastSyncedMessagesRef.current && onMessagesUpdateRef.current) {
        lastSyncedMessagesRef.current = messagesKey
        const syncMessages = messages.filter(m => m.role !== 'system').map(m => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: m.timestamp
        }))
        onMessagesUpdateRef.current(syncMessages)
      }
    }
  }, [messages])

  // Company config loading, questions sync, and SLA sync — extracted to useCompanyConfigLoader
  useCompanyConfigLoader({
    isOpen, isInJobCreationMode, configLoaded, companyConfig,
    basicInfoFields, companyEligibilityQuestions, isLoadingEligibilityQuestions,
    isLoadingStages, sla, technicalSkills,
    setBasicInfoFields, setDetectedCriteria, setFieldOrigins, setFieldsFromConfig,
    setJobConfig, setCompanyConfig, setCompanyMembersMap, setCompanyDefaultQuestions,
    setConfigLoaded, setTechnicalSkills, setSalaryInfo, setWizardGreeting, setWizardGreetingLoaded,
  })
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }, [typingTimeoutRef])



  // Proactive stage completion handlers + panel resize — extracted to useExpandedChatProactiveHandlers
  useExpandedChatProactiveHandlers({
    PROACTIVE_MESSAGE_DELAY,
    approvedCandidates, basicInfoFields, behavioralCompetencies,
    calibrationComplete, calibrationProactiveTimerRef, calibrationStageCompletionShown,
    competenciesProactiveTimerRef, competenciesStageCompletionShown,
    currentStage, inputEvaluationProactiveTimerRef, inputEvaluationStageCompletionShown,
    isFieldRequiredForWizard, isResizing, rejectedCandidates, resizeRef,
    salaryInfo, salaryProactiveTimerRef, salaryStageCompletionShown,
    setAwaitingStageAdvanceConfirmation, setCalibrationStageCompletionShown,
    setCompetenciesStageCompletionShown, setInputEvaluationStageCompletionShown,
    setIsResizing, setMessages, setPanelWidth, setSalaryStageCompletionShown,
    setWsiQuestionsStageCompletionShown, technicalSkills,
    wsiCandidates, wsiQuestionsProactiveTimerRef, wsiQuestionsStageCompletionShown,
    salaryBenchmark, detectedCriteria, setSalaryBenchmark, setSalaryInfo, setIsLoadingBenchmark,
  })

  return {
    typeText, isFieldRequiredForWizard, hasConfigData, isInJobCreationMode,
    wsiQualityGates, applyPendingDraft,
    companyMembersMap, languagesUserEdited, setCompanyMembersMap, setLanguagesUserEdited,
    hasAppliedRestoredDraft, setHasAppliedRestoredDraft,
    awaitingDraftChoice, setAwaitingDraftChoice,
    pendingDraftData, setPendingDraftData,
    saveWizardDraft, clearWizardDraft, loadedDraft, hasRestoredDraft,
    hasAttemptedRestore, isAutoSaving, autoSaveLastSaved, hasPendingChanges, getLastSavedText,
    hasMinimumCompetencies,
  }
}
