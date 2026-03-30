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
  }, [technicalSkills, behavioralCompetencies, fastTrackOriginalCompetencies, wsiRegenerationPrompted, awaitingWSIRegenerationConfirmation, currentStage])
  
  // Reset message sent flag when suggestions change (new set of suggestions = new prompt)
  const suggestionsKey = fastTrack.suggestions.map(s => s.job_id).join(',')
  const prevSuggestionsKeyRef = useRef(suggestionsKey)
  useEffect(() => {
    if (suggestionsKey !== prevSuggestionsKeyRef.current && suggestionsKey !== '') {
      setFastTrackMessageSent(false)
      prevSuggestionsKeyRef.current = suggestionsKey
    }
  }, [suggestionsKey])
  
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
  }, [learning.suggestions, learningSuggestionsApplied, salaryInfo.minSalary, salaryInfo.maxSalary, technicalSkills.length, behavioralCompetencies.length])
  
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
  }, [wizardGreeting, isFieldRequiredForWizard])
  
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
  }, [messages, languagesUserEdited, jobConfig.languages.length])
  
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
        const companyId = user?.company || 'default-company'
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
  }, [user, proactiveActionIds])

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
  }, [hasRestoredDraft, loadedDraft, hasAppliedRestoredDraft, isJobCreationMode, hasAttemptedRestore, awaitingDraftChoice, INITIAL_STAGES, STAGE_DISPLAY_NAMES, pendingDraftData])
  
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
  }, [pendingDraftData])
  
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
  }, [detectedCriteria, basicInfoFields.area, detectedCriteria.cargo])

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
  }, [])

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
  }, [isOpen, messages.length, typeText, initialLiaMessage, initialMessages, isJobCreationMode])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, displayedText])

  useEffect(() => {
    if (isOpen && !isTypingEffect) {
      inputRef.current?.focus()
    }
  }, [isOpen, isTypingEffect])

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

  // Fetch company configuration when modal opens in job creation mode
  useEffect(() => {
    const fetchCompanyConfig = async () => {
      if (!isOpen || !isInJobCreationMode || configLoaded) return
      
      try {
        const [profileRes, departmentsRes, benefitsRes, greetingRes] = await Promise.all([
          fetch('/api/backend-proxy/company/profile'),
          fetch('/api/backend-proxy/company/departments'),
          fetch('/api/backend-proxy/company/benefits/?company_id=default'),
          fetch('/api/backend-proxy/company/smart-wizard-greeting?company_id=default')
        ])
        
        const config: typeof companyConfig = {}
        const newFieldsFromConfig = new Set<string>()
        
        if (profileRes.ok) {
          const profileData = await profileRes.json()
          if (profileData.work_model) {
            config.workModel = profileData.work_model
          }
          if (profileData.hybrid_days_onsite) {
            config.hybridDaysOnsite = profileData.hybrid_days_onsite
          }
          if (profileData.employment_types && Array.isArray(profileData.employment_types)) {
            config.employmentTypes = profileData.employment_types
          }
          if (profileData.tech_stack && Array.isArray(profileData.tech_stack)) {
            config.techStack = profileData.tech_stack.map((t: string) => {
              const parts = t.split(':')
              return parts.length > 1 ? parts[1] : t
            })
          }
          if (profileData.values) config.values = profileData.values
          if (profileData.coreCompetencies) config.coreCompetencies = profileData.coreCompetencies
          if (profileData.evp_bullets) config.evpBullets = profileData.evp_bullets
          if (profileData.headquarters) config.headquarters = profileData.headquarters
          if (profileData.locations) config.locations = profileData.locations
        }
        
        if (departmentsRes.ok) {
          const departmentsData = await departmentsRes.json()
          if (Array.isArray(departmentsData)) {
            config.departments = departmentsData.map((d: Record<string, unknown>) => ({
              id: d.id,
              name: d.name
            }))
            
            // Fetch members from each department to build name → email map
            const membersMap = new Map<string, string>()
            try {
              const memberPromises = departmentsData.map(async (dept: Record<string, unknown>) => {
                try {
                  const membersRes = await fetch(`/api/backend-proxy/company/departments/${dept.id}/members`)
                  if (membersRes.ok) {
                    const members = await membersRes.json()
                    if (Array.isArray(members)) {
                      members.forEach((m: Record<string, unknown>) => {
                        if (m.name && m.email) {
                          const mName = String(m.name)
                          const mEmail = String(m.email)
                          membersMap.set(mName.trim().toLowerCase(), mEmail)
                          membersMap.set(mName.trim(), mEmail)
                        }
                      })
                    }
                  }
                } catch (err) {
                }
              })
              await Promise.all(memberPromises)
              setCompanyMembersMap(membersMap)
            } catch (err) {
            }
          }
        }
        
        if (benefitsRes.ok) {
          const benefitsData = await benefitsRes.json()
          const benefitsList = Array.isArray(benefitsData) ? benefitsData : benefitsData.items || []
          config.benefits = benefitsList.filter((b: Record<string, unknown>) => b.is_active)
        }
        
        // Fetch and store smart wizard greeting with prefill_data
        if (greetingRes.ok) {
          const greetingData = await greetingRes.json()
          if (greetingData.greeting_message && greetingData.catalog_status) {
            setWizardGreeting(greetingData)
            
            // Use prefill_data to enhance form population for mature catalogs
            const prefillData = greetingData.prefill_data || {}
            
            // Pre-fill departments from prefill_data (if not already set from config)
            if (prefillData.departments && Array.isArray(prefillData.departments) && prefillData.departments.length > 0) {
              if (!config.departments || config.departments.length === 0) {
                config.departments = prefillData.departments.map((d: Record<string, unknown>, idx: number) => ({
                  id: d.id || `prefill-dept-${idx}`,
                  name: d.name || d
                }))
              }
            }
            
            // Pre-fill benefits from prefill_data (if not already set from config)
            if (prefillData.benefits && Array.isArray(prefillData.benefits) && prefillData.benefits.length > 0) {
              if (!config.benefits || config.benefits.length === 0) {
                config.benefits = prefillData.benefits.map((b: Record<string, unknown>) => ({
                  id: b.id,
                  name: b.name,
                  value: b.value,
                  is_active: b.is_active ?? true
                }))
              }
            }
            
            // Enhance tech_stack suggestions from prefill_data
            if (prefillData.tech_stack && Array.isArray(prefillData.tech_stack) && prefillData.tech_stack.length > 0) {
              const existingTechStack = config.techStack || []
              const prefillTechStack = prefillData.tech_stack.map((t: string) => {
                const parts = t.split(':')
                return parts.length > 1 ? parts[1] : t
              })
              // Merge prefill tech stack with existing, avoiding duplicates
              const mergedTechStack = [...new Set([...existingTechStack, ...prefillTechStack])]
              config.techStack = mergedTechStack
            }
          }
        }
        
        // Mark wizard greeting as loaded (even if it failed - we have fallback)
        setWizardGreetingLoaded(true)
        
        setCompanyConfig(config)
        
        // Pre-fill fields from company config
        if (config.workModel) {
          const workModelMap: Record<string, string> = {
            'remote': 'Remoto',
            'hybrid': 'Híbrido',
            'onsite': 'Presencial',
            'remoto': 'Remoto',
            'híbrido': 'Híbrido',
            'presencial': 'Presencial'
          }
          const mappedModel = workModelMap[config.workModel.toLowerCase()] || config.workModel
          setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: mappedModel }))
          setDetectedCriteria(prev => ({ ...prev, modeloTrabalho: mappedModel }))
          newFieldsFromConfig.add('modeloTrabalho')
          setFieldOrigins(prev => ({ ...prev, work_model: { source: 'default', confidence: 0.85 } }))
        }
        
        // Pre-fill employment type with first company default
        if (config.employmentTypes && config.employmentTypes.length > 0) {
          setBasicInfoFields(prev => ({ ...prev, tipoContrato: config.employmentTypes![0] }))
          newFieldsFromConfig.add('tipoContrato')
          setFieldOrigins(prev => ({ ...prev, employment_type: { source: 'default', confidence: 0.85 } }))
        }
        
        // Pre-fill hybrid days onsite with company default
        if (config.hybridDaysOnsite) {
          setJobConfig(prev => ({ ...prev, hybridDaysOnsite: config.hybridDaysOnsite }))
        }
        
        if (config.headquarters || (config.locations && config.locations.length > 0)) {
          const location = config.headquarters || config.locations?.[0] || ''
          if (location) {
            setBasicInfoFields(prev => ({ ...prev, localidade: location }))
            setDetectedCriteria(prev => ({ ...prev, localizacao: location }))
            setFieldOrigins(prev => ({ ...prev, location: { source: 'default', confidence: 0.85 } }))
            newFieldsFromConfig.add('localizacao')
          }
        }
        
        // Pre-fill department with first company default
        if (config.departments && config.departments.length > 0 && !basicInfoFields.area) {
          setBasicInfoFields(prev => ({ ...prev, area: config.departments![0].name }))
          newFieldsFromConfig.add('area')
        }
        
        // Pre-fill tech stack
        if (config.techStack && config.techStack.length > 0) {
          const skillCategories: Record<string, 'language' | 'framework' | 'database' | 'tool'> = {
            'Python': 'language', 'JavaScript': 'language', 'TypeScript': 'language', 'Java': 'language',
            'Go': 'language', 'Rust': 'language', 'C#': 'language', 'Ruby': 'language', 'PHP': 'language',
            'Node.js': 'framework', 'React': 'framework', 'Angular': 'framework', 'Vue.js': 'framework',
            'Django': 'framework', 'FastAPI': 'framework', 'Flask': 'framework', 'Spring': 'framework',
            'Next.js': 'framework', 'Express': 'framework', 'React Native': 'framework', 'Flutter': 'framework',
            'PostgreSQL': 'database', 'MySQL': 'database', 'MongoDB': 'database', 'Redis': 'database',
            'Elasticsearch': 'database', 'SQL': 'database', 'Oracle': 'database',
            'Docker': 'tool', 'Kubernetes': 'tool', 'AWS': 'tool', 'Azure': 'tool', 'GCP': 'tool',
            'Git': 'tool', 'Jenkins': 'tool', 'Terraform': 'tool', 'Linux': 'tool',
          }
          
          const configSkills: TechnicalSkill[] = config.techStack.slice(0, 5).map((tech, idx) => ({
            id: `config-skill-${idx}`,
            name: tech,
            level: 'Intermediário' as const,
            required: false,
            category: skillCategories[tech] || 'tool',
            weight: 2
          }))
          
          setTechnicalSkills(prev => {
            const existingNames = prev.map(s => s.name.toLowerCase())
            const newSkills = configSkills.filter(s => !existingNames.includes(s.name.toLowerCase()))
            return [...prev, ...newSkills]
          })
          
          if (configSkills.length > 0) {
            newFieldsFromConfig.add('competenciasTecnicas')
          }
        }
        
        // Pre-fill benefits
        if (config.benefits && config.benefits.length > 0) {
          const configBenefits: Benefit[] = config.benefits.map((b, idx) => ({
            id: `config-benefit-${idx}`,
            name: b.name,
            value: b.value ? `R$ ${b.value}` : undefined,
            enabled: true
          }))
          
          setSalaryInfo(prev => {
            const existingNames = prev.benefits.map(b => b.name.toLowerCase())
            const newBenefits = configBenefits.filter(b => !existingNames.includes(b.name.toLowerCase()))
            return {
              ...prev,
              benefits: [...prev.benefits, ...newBenefits]
            }
          })
          
          if (configBenefits.length > 0) {
            newFieldsFromConfig.add('benefits')
          }
        }
        
        setFieldsFromConfig(newFieldsFromConfig)
        setConfigLoaded(true)
        
      } catch (error) {
        setConfigLoaded(true)
        // Also mark greeting as loaded to prevent blocking (fallback message will be used)
        setWizardGreetingLoaded(true)
      }
    }
    
    fetchCompanyConfig()
  }, [isOpen, isInJobCreationMode, configLoaded, basicInfoFields.modeloTrabalho, basicInfoFields.localidade])

  // Sync company screening questions from settings with companyDefaultQuestions state
  useEffect(() => {
    if (!isLoadingEligibilityQuestions) {
      const mappedQuestions = companyEligibilityQuestions.map(q => ({
        id: q.id,
        question: q.question_text,
        type: 'open' as const,
        enabled: q.is_active,
        fromConfig: true
      }))
      setCompanyDefaultQuestions(mappedQuestions)
    }
  }, [companyEligibilityQuestions, isLoadingEligibilityQuestions])

  // Sync deadlines with SLAs from recruitment stages configuration
  useEffect(() => {
    if (!isLoadingStages && sla) {
      setJobConfig(prev => ({
        ...prev,
        deadlineScreening: sla.calculateDeadline(sla.screeningSLA),
        deadlineShortlist: sla.calculateDeadline(sla.shortlistSLA),
        deadline: sla.calculateDeadline(sla.totalSLA)
      }))
    }
  }, [isLoadingStages, sla])

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }, [])

  // Fetch salary benchmark when entering salary stage
  useEffect(() => {
    const fetchBenchmark = async () => {
      if (currentStage !== 'salary' || !basicInfoFields.cargo) return
      if (salaryBenchmark !== null) return
      
      setIsLoadingBenchmark(true)
      try {
        const benchmarkData = await liaApi.getSalaryBenchmark({
          job_title: basicInfoFields.cargo,
          seniority: detectedCriteria.senioridadeIdiomas || '',
          location: basicInfoFields.localidade,
          department: basicInfoFields.area,
          company_id: 'default'
        })
        
        if (benchmarkData && (benchmarkData.internal || benchmarkData.market)) {
          setSalaryBenchmark(benchmarkData)
          
          if (benchmarkData.combined && !salaryInfo.minSalary && !salaryInfo.maxSalary) {
            setSalaryInfo(prev => ({
              ...prev,
              minSalary: benchmarkData.combined!.min.toLocaleString(),
              maxSalary: benchmarkData.combined!.max.toLocaleString()
            }))
          }
        }
      } catch (error) {
      } finally {
        setIsLoadingBenchmark(false)
      }
    }
    
    fetchBenchmark()
  }, [currentStage, basicInfoFields.cargo])

  // Proactive salary stage completion detection - timer resets on each salaryInfo change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (salaryProactiveTimerRef.current) {
      clearTimeout(salaryProactiveTimerRef.current)
      salaryProactiveTimerRef.current = null
    }
    
    // Only trigger when in salary stage and not already shown
    if (currentStage !== 'salary' || salaryStageCompletionShown) return
    
    // Parse salary values
    const minSalary = parseFloat(salaryInfo.minSalary?.replace(/\./g, '').replace(',', '.') || '0')
    const maxSalary = parseFloat(salaryInfo.maxSalary?.replace(/\./g, '').replace(',', '.') || '0')
    const enabledBenefits = salaryInfo.benefits?.filter(b => b.enabled).length || 0
    
    // Check if salary field is required for this wizard
    const isSalaryRequired = isFieldRequiredForWizard('salario')
    
    // Determine if salary stage is complete based on requirements
    let isStageComplete = false
    
    if (!isSalaryRequired) {
      // If salary is NOT required (pre-configured), stage is complete immediately
      isStageComplete = true
    } else {
      // If salary IS required, need at least min/max salary
      const hasSalaryRange = minSalary > 0 && maxSalary > 0
      isStageComplete = hasSalaryRange
    }
    
    if (!isStageComplete) return // Not enough data yet
    
    // Schedule proactive message after delay (timer resets on each salaryInfo change via cleanup)
    salaryProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
      if (currentStage !== 'salary' || salaryStageCompletionShown) return
      
      // Build message based on what's filled
      const statusParts: string[] = []
      if (minSalary > 0 && maxSalary > 0) {
        statusParts.push(`**Faixa salarial:** R$ ${minSalary.toLocaleString('pt-BR')} - R$ ${maxSalary.toLocaleString('pt-BR')}`)
      } else if (!isSalaryRequired) {
        statusParts.push('**Remuneração:** Usando configuração padrão da empresa')
      }
      if (enabledBenefits > 0) {
        statusParts.push(`**${enabledBenefits} benefícios** selecionados`)
      }
      
      const proactiveMessage: Message = {
        id: `salary-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Etapa de Remuneração pronta!**

Detectei que você configurou:
${statusParts.map(s => `• ${s}`).join('\n')}

Quer que eu avance para a etapa de **Competências**, ou prefere ajustar algo antes?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'competencies',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setAwaitingStageAdvanceConfirmation('competencies')
      setSalaryStageCompletionShown(true)
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (salaryProactiveTimerRef.current) {
        clearTimeout(salaryProactiveTimerRef.current)
        salaryProactiveTimerRef.current = null
      }
    }
  }, [currentStage, salaryInfo, salaryStageCompletionShown, isFieldRequiredForWizard, PROACTIVE_MESSAGE_DELAY])

  // Proactive input-evaluation stage completion detection - timer resets on each basicInfoFields change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (inputEvaluationProactiveTimerRef.current) {
      clearTimeout(inputEvaluationProactiveTimerRef.current)
      inputEvaluationProactiveTimerRef.current = null
    }
    
    if (currentStage !== 'input-evaluation' || inputEvaluationStageCompletionShown) return
    
    // Check minimum required fields
    const hasCargo = !!basicInfoFields.cargo?.trim()
    const hasLocalidade = !!basicInfoFields.localidade?.trim()
    const hasModeloTrabalho = !!basicInfoFields.modeloTrabalho?.trim()
    
    const isStageComplete = hasCargo && hasLocalidade && hasModeloTrabalho
    
    if (!isStageComplete) return // Not enough data yet
    
    // Schedule proactive message after delay (timer resets on each basicInfoFields change via cleanup)
    inputEvaluationProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
      if (currentStage !== 'input-evaluation' || inputEvaluationStageCompletionShown) return
      
      const proactiveMessage: Message = {
        id: `input-evaluation-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Informações básicas configuradas!**

Detectei:
• **Cargo:** ${basicInfoFields.cargo}
• **Local:** ${basicInfoFields.localidade}
• **Modelo:** ${basicInfoFields.modeloTrabalho}

Quer que eu avance para a etapa de **Enriquecimento da Vaga**, onde vou analisar dados de mercado e sugerir melhorias? Ou prefere ajustar algo antes?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'jd-enrichment',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setInputEvaluationStageCompletionShown(true)
      setAwaitingStageAdvanceConfirmation('jd-enrichment')
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (inputEvaluationProactiveTimerRef.current) {
        clearTimeout(inputEvaluationProactiveTimerRef.current)
        inputEvaluationProactiveTimerRef.current = null
      }
    }
  }, [currentStage, basicInfoFields, inputEvaluationStageCompletionShown, PROACTIVE_MESSAGE_DELAY])

  // Proactive competencies stage completion detection - timer resets on each competencies change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (competenciesProactiveTimerRef.current) {
      clearTimeout(competenciesProactiveTimerRef.current)
      competenciesProactiveTimerRef.current = null
    }
    
    if (currentStage !== 'competencies' || competenciesStageCompletionShown) return
    
    const enabledTechnical = technicalSkills.length
    const enabledBehavioral = behavioralCompetencies.filter(c => c.enabled).length
    
    // Check minimum requirements: 3 technical + 3 behavioral
    const hasMinimumCompetencies = enabledTechnical >= 3 && enabledBehavioral >= 3
    
    if (!hasMinimumCompetencies) return // Not enough data yet
    
    // Schedule proactive message after delay (timer resets on each competencies change via cleanup)
    competenciesProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
      if (currentStage !== 'competencies' || competenciesStageCompletionShown) return
      
      const proactiveMessage: Message = {
        id: `competencies-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Competências configuradas!**

Detectei:
• **${enabledTechnical} competências técnicas** definidas
• **${enabledBehavioral} competências comportamentais** habilitadas

Quer que eu avance para a etapa de **Perguntas WSI**, ou prefere ajustar algo antes?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'wsi-questions',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setAwaitingStageAdvanceConfirmation('wsi-questions')
      setCompetenciesStageCompletionShown(true)
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (competenciesProactiveTimerRef.current) {
        clearTimeout(competenciesProactiveTimerRef.current)
        competenciesProactiveTimerRef.current = null
      }
    }
  }, [currentStage, technicalSkills, behavioralCompetencies, competenciesStageCompletionShown, PROACTIVE_MESSAGE_DELAY])

  // Proactive wsi-questions stage completion detection - timer resets on each wsiCandidates change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (wsiQuestionsProactiveTimerRef.current) {
      clearTimeout(wsiQuestionsProactiveTimerRef.current)
      wsiQuestionsProactiveTimerRef.current = null
    }
    
    if (currentStage !== 'wsi-questions' || wsiQuestionsStageCompletionShown) return
    
    // Count selected questions
    const selectedQuestions = wsiCandidates.filter(q => q.selected).length
    const hasMinimumQuestions = selectedQuestions >= 3
    
    if (!hasMinimumQuestions) return // Not enough data yet
    
    // Schedule proactive message after delay (timer resets on each wsiCandidates change via cleanup)
    wsiQuestionsProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
      if (currentStage !== 'wsi-questions' || wsiQuestionsStageCompletionShown) return
      
      // Count question types
      const selectedTypes = wsiCandidates.filter(q => q.selected)
      const yesNoCount = selectedTypes.filter(q => q.type === 'yes-no').length
      const multipleChoiceCount = selectedTypes.filter(q => q.type === 'multiple-choice').length
      const openCount = selectedTypes.filter(q => q.type === 'open').length
      const numericCount = selectedTypes.filter(q => q.type === 'numeric').length
      
      const typesSummary: string[] = []
      if (yesNoCount > 0) typesSummary.push(`${yesNoCount} sim/não`)
      if (multipleChoiceCount > 0) typesSummary.push(`${multipleChoiceCount} múltipla escolha`)
      if (openCount > 0) typesSummary.push(`${openCount} aberta${openCount > 1 ? 's' : ''}`)
      if (numericCount > 0) typesSummary.push(`${numericCount} numérica${numericCount > 1 ? 's' : ''}`)
      
      const proactiveMessage: Message = {
        id: `wsi-questions-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Perguntas de triagem configuradas!**

Detectei:
• **${selectedQuestions} perguntas** selecionadas
• **Tipos:** ${typesSummary.join(', ')}

Essas perguntas serão usadas para avaliar candidatos automaticamente.

Quer que eu avance para a **Revisão Final**, ou prefere ajustar as perguntas?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'review-publish',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setWsiQuestionsStageCompletionShown(true)
      setAwaitingStageAdvanceConfirmation('review-publish')
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (wsiQuestionsProactiveTimerRef.current) {
        clearTimeout(wsiQuestionsProactiveTimerRef.current)
        wsiQuestionsProactiveTimerRef.current = null
      }
    }
  }, [currentStage, wsiCandidates, wsiQuestionsStageCompletionShown, PROACTIVE_MESSAGE_DELAY])

  // Proactive calibration stage completion detection - timer resets on each calibration data change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (calibrationProactiveTimerRef.current) {
      clearTimeout(calibrationProactiveTimerRef.current)
      calibrationProactiveTimerRef.current = null
    }
    
    if (currentStage !== 'search-calibration' || calibrationStageCompletionShown) return
    
    // Count evaluated candidates (approved + rejected)
    const likedCount = approvedCandidates.length
    const dislikedCount = rejectedCandidates.length
    const totalEvaluated = likedCount + dislikedCount
    
    const hasMinimumEvaluations = totalEvaluated >= 5
    
    if (!hasMinimumEvaluations || calibrationComplete) return // Not enough data yet or already complete
    
    // Schedule proactive message after delay (timer resets on each calibration data change via cleanup)
    calibrationProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
      if (currentStage !== 'search-calibration' || calibrationStageCompletionShown) return
      
      const proactiveMessage: Message = {
        id: `calibration-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Calibração em bom andamento!**

Você avaliou **${totalEvaluated} candidatos**:
• ✓ ${likedCount} aprovados
• ✗ ${dislikedCount} rejeitados

Com base nas suas preferências, estou refinando o perfil ideal de candidato.

Quer **finalizar a calibração** e aplicar o modelo, ou prefere continuar avaliando mais candidatos?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'calibration-complete',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setCalibrationStageCompletionShown(true)
      setAwaitingStageAdvanceConfirmation('calibration-complete')
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (calibrationProactiveTimerRef.current) {
        clearTimeout(calibrationProactiveTimerRef.current)
        calibrationProactiveTimerRef.current = null
      }
    }
  }, [currentStage, approvedCandidates.length, rejectedCandidates.length, calibrationStageCompletionShown, calibrationComplete, PROACTIVE_MESSAGE_DELAY])

  // Reset all stage completion flags and confirmation state when stage changes
  useEffect(() => {
    // Reset awaiting confirmation when stage changes (prevents stale confirmations)
    setAwaitingStageAdvanceConfirmation(null)
    
    // Reset individual stage completion flags when leaving each stage
    if (currentStage !== 'input-evaluation') {
      setInputEvaluationStageCompletionShown(false)
    }
    if (currentStage !== 'salary') {
      setSalaryStageCompletionShown(false)
    }
    if (currentStage !== 'competencies') {
      setCompetenciesStageCompletionShown(false)
    }
    if (currentStage !== 'wsi-questions') {
      setWsiQuestionsStageCompletionShown(false)
    }
    if (currentStage !== 'search-calibration') {
      setCalibrationStageCompletionShown(false)
    }
    // Note: Timer refs are automatically reset by useEffect cleanup when stage changes
    // No need for manual timestamp tracking
  }, [currentStage])

  // Panel resize handlers
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !resizeRef.current) return
      
      const container = resizeRef.current.parentElement?.parentElement
      if (!container) return
      
      const containerRect = container.getBoundingClientRect()
      const newWidth = ((containerRect.right - e.clientX) / containerRect.width) * 100
      
      // Limit between 25% and 55%
      setPanelWidth(Math.min(55, Math.max(25, newWidth)))
    }
    
    const handleMouseUp = () => {
      setIsResizing(false)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    
    if (isResizing) {
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

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
