"use client"

import { useState, useEffect, useMemo, useRef } from "react"
import { useWSIScreeningPipeline, type UnifiedScreeningQuestion, type WSIScreeningPipelineRequest } from "@/hooks/recruitment/use-screening-questions"
import { useCompanyEligibilityQuestions } from "@/hooks/company/use-company-eligibility-questions"
import type { ScreeningQuestionsPanelProps } from "./ScreeningPanelConstants"

export function useScreeningQuestionsPanel({
  jobTitle,
  department,
  seniority,
  bigFiveProfile,
  skills,
  behavioralCompetencies,
  isAffirmative,
  affirmativeType,
  onQuestionsChange,
}: Omit<ScreeningQuestionsPanelProps, 'className'>) {
  const {
    questions: pipelineQuestions,
    blocks: pipelineBlocks,
    isLoading,
    error,
    metadata,
    qualityWarnings,
    blockDistribution,
    generatePipeline,
    toggleQuestion,
    getSelectedQuestions
  } = useWSIScreeningPipeline()

  const {
    questions: companyQuestions,
    isLoading: isLoadingCompanyQuestions
  } = useCompanyEligibilityQuestions()

  const [screeningModel, setScreeningModel] = useState<'compact' | 'full'>('compact')
  const [expandedBlocks, setExpandedBlocks] = useState<Record<number, boolean>>({
    0: false,
    1: false,
    2: true,
    3: true,
    4: true,
    5: true,
    6: false
  })
  const [hasGenerated, setHasGenerated] = useState(false)
  const [selectedBlockForSuggestion, setSelectedBlockForSuggestion] = useState<number>(4)
  const [isGeneratingMore, setIsGeneratingMore] = useState(false)

  const questionsByBlock = useMemo(() => {
    const blocks: Record<number, UnifiedScreeningQuestion[]> = {
      0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []
    }

    pipelineQuestions.forEach(q => {
      const blockId = q.block_id
      if (blocks[blockId] !== undefined) {
        blocks[blockId].push(q)
      }
    })

    companyQuestions.forEach(cq => {
      const exists = blocks[2].some(q => q.id === cq.id)
      if (!exists) {
        const unifiedQuestion: UnifiedScreeningQuestion = {
          id: cq.id,
          text: cq.question_text,
          category: 'company',
          block_id: 2,
          source: 'company',
          bloom_level: 2,
          bloom_label: 'Compreender',
          dreyfus_stage: 3,
          dreyfus_label: 'Competente',
          framework: 'CBI',
          weight: 0.7,
          expected_signals: [],
          scoring_criteria: {},
          is_selected: true,
          is_eliminatory: cq.is_eliminatory,
          question_type: cq.question_type,
          options: cq.options,
          expected_answer: cq.expected_answer,
          order: cq.order
        }
        blocks[2].push(unifiedQuestion)
      }
    })

    return blocks
  }, [pipelineQuestions, companyQuestions])

  const totalEditableQuestions = useMemo(() => {
    return questionsByBlock[2].length + questionsByBlock[3].length + questionsByBlock[4].length + questionsByBlock[5].length
  }, [questionsByBlock])

  const selectedCount = useMemo(() => {
    const pipelineSelected = pipelineQuestions.filter(q => q.is_selected).length
    const companySelected = questionsByBlock[2].filter(q => q.is_selected).length
    return pipelineSelected + companySelected
  }, [pipelineQuestions, questionsByBlock])

  const totalDuration = useMemo(() => {
    return screeningModel === 'full' ? 30 : 15
  }, [screeningModel])

  const questionCountLabel = useMemo(() => {
    return screeningModel === 'full' ? '12 WSI' : '8 WSI'
  }, [screeningModel])

  useEffect(() => {
    if (jobTitle && !hasGenerated) {
      const context: WSIScreeningPipelineRequest = {
        job_title: jobTitle,
        department,
        seniority,
        technical_skills: skills,
        behavioral_competencies: behavioralCompetencies,
        big_five_profile: bigFiveProfile,
        format: screeningModel,
        include_company_questions: true,
        is_affirmative: isAffirmative || false,
        affirmative_type: affirmativeType,
      }
      generatePipeline(context)
      setHasGenerated(true)
    }
  }, [jobTitle, department, seniority, bigFiveProfile, skills, behavioralCompetencies, generatePipeline, hasGenerated, screeningModel, isAffirmative, affirmativeType])

  const onQuestionsChangeRef = useRef(onQuestionsChange)
  onQuestionsChangeRef.current = onQuestionsChange

  useEffect(() => {
    if (onQuestionsChangeRef.current) {
      const pipelineSelected = getSelectedQuestions()
      const companySelected = (questionsByBlock[2] || []).filter(q => q.is_selected)
      onQuestionsChangeRef.current([...companySelected, ...pipelineSelected] as unknown as Record<string, unknown>[])
    }
  }, [pipelineQuestions, companyQuestions, getSelectedQuestions, questionsByBlock])

  const suggestionsForSelectedBlock = useMemo(() => {
    const blockQuestions = questionsByBlock[selectedBlockForSuggestion] || []
    return blockQuestions.filter(q => !q.is_selected)
  }, [questionsByBlock, selectedBlockForSuggestion])

  const handleRegenerateAll = async () => {
    if (isLoading) return
    const context: WSIScreeningPipelineRequest = {
      job_title: jobTitle,
      department,
      seniority,
      technical_skills: skills,
      behavioral_competencies: behavioralCompetencies,
      big_five_profile: bigFiveProfile,
      format: screeningModel,
      include_company_questions: true,
      is_affirmative: isAffirmative || false,
      affirmative_type: affirmativeType,
    }
    await generatePipeline(context)
  }

  const handleGenerateMoreForBlock = async () => {
    if (isGeneratingMore) return
    setIsGeneratingMore(true)
    try {
      await handleRegenerateAll()
    } finally {
      setIsGeneratingMore(false)
    }
  }

  const handleAddSuggestion = (question: UnifiedScreeningQuestion) => {
    toggleQuestion(question.id)
  }

  const toggleBlock = (blockId: number) => {
    setExpandedBlocks(prev => ({
      ...prev,
      [blockId]: !prev[blockId]
    }))
  }

  const handleModelChange = (model: 'compact' | 'full') => {
    setScreeningModel(model)
    setHasGenerated(false)
  }

  return {
    pipelineQuestions,
    pipelineBlocks,
    isLoading,
    error,
    metadata,
    qualityWarnings,
    blockDistribution,
    toggleQuestion,
    companyQuestions,
    isLoadingCompanyQuestions,
    screeningModel,
    expandedBlocks,
    hasGenerated,
    setHasGenerated,
    selectedBlockForSuggestion,
    setSelectedBlockForSuggestion,
    isGeneratingMore,
    questionsByBlock,
    totalEditableQuestions,
    selectedCount,
    totalDuration,
    questionCountLabel,
    suggestionsForSelectedBlock,
    handleRegenerateAll,
    handleGenerateMoreForBlock,
    handleAddSuggestion,
    toggleBlock,
    handleModelChange,
  }
}
