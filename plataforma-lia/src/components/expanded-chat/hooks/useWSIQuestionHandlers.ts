"use client"

import React, { useCallback, useEffect } from "react"
import { liaApi } from "@/services/lia-api"
import {
  type TechnicalSkill,
  type BehavioralCompetency,
  type BasicInfoFields,
  type DetectedCriteria,
} from "../ExpandedChatContext"
import {
  type Message,
  type WSIQuestionCandidate,
} from "../types"

export interface WSIQuestionHandlersContext {
  basicInfoFields: BasicInfoFields
  detectedCriteria: DetectedCriteria
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  wsiCandidates: WSIQuestionCandidate[]
  setWsiCandidates: React.Dispatch<React.SetStateAction<WSIQuestionCandidate[]>>
  wsiGenerationBatch: number
  setWsiGenerationBatch: React.Dispatch<React.SetStateAction<number>>
  isGeneratingWSI: boolean
  setIsGeneratingWSI: React.Dispatch<React.SetStateAction<boolean>>
  wsiHasGenerated: boolean
  setWsiHasGenerated: React.Dispatch<React.SetStateAction<boolean>>
  setWsiQuestions: React.Dispatch<React.SetStateAction<WSIQuestionCandidate[]>>
  customQuestionText: string
  customQuestionType: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  customQuestionRequired: boolean
  setShowCustomQuestionForm: (val: boolean) => void
  setCustomQuestionText: (val: string) => void
  setCustomQuestionType: (val: 'open' | 'yes-no' | 'numeric' | 'multiple-choice') => void
  setCustomQuestionRequired: (val: boolean) => void
  currentStage: string
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
}

export function useWSIQuestionHandlers(ctx: WSIQuestionHandlersContext) {
  const generateWSIQuestions = useCallback(async (count: number = 7, category: 'technical' | 'behavioral' = 'technical') => {
    ctx.setIsGeneratingWSI(true)
    const newBatch = ctx.wsiGenerationBatch + 1
    ctx.setWsiGenerationBatch(newBatch)
    
    try {
      // Call backend API to generate WSI questions using LLM
      const response = await liaApi.generateJobScreeningQuestions({
        job_title: ctx.basicInfoFields.cargo || 'Vaga',
        job_description: ctx.detectedCriteria.cargo ? `Vaga de ${ctx.detectedCriteria.cargo}` : undefined,
        technical_skills: ctx.technicalSkills.filter(s => s.required).map(s => s.name),
        behavioral_competencies: ctx.behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
        seniority_level: ctx.detectedCriteria.senioridadeIdiomas?.toLowerCase() || 'pleno',
        work_model: ctx.basicInfoFields.modeloTrabalho?.toLowerCase(),
        location: ctx.basicInfoFields.localidade,
        count: count,
        category: category
      })
      
      // Convert API response to WSIQuestionCandidate format
      const existingTexts = new Set(ctx.wsiCandidates.map(q => q.question.toLowerCase()))
      
      const newQuestions: WSIQuestionCandidate[] = response.questions
        .filter(q => !existingTexts.has(q.question.toLowerCase()))
        .map((q) => ({
          id: q.id,
          question: q.question,
          type: q.type as 'open' | 'yes-no' | 'numeric' | 'multiple-choice',
          required: q.required,
          options: q.options,
          expectedAnswer: q.expected_answer,
          correctOptionIndex: q.correct_option_index,
          selected: false,
          batch: newBatch,
          isWSI: true,
          competency: q.competency,
          framework: q.framework,
          category: q.category
        }))
      
      ctx.setWsiCandidates(prev => [...prev, ...newQuestions])
      ctx.setWsiHasGenerated(true)
      
      // Add LIA feedback message
      const selectedCount = ctx.wsiCandidates.filter(q => q.selected).length
      const feedbackMessage: Message = {
        id: `wsi-feedback-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        role: 'assistant',
        content: newBatch === 1 
          ? `Gerei ${newQuestions.length} perguntas de triagem baseadas na **metodologia WSI** (Work Sample Interview) e no perfil da vaga.\n\nAs perguntas foram criadas com base em frameworks científicos:\n- **CBI** (Competency-Based Interviewing)\n- **Dreyfus Model** (Avaliação de Expertise)\n- **Bloom's Taxonomy** (Níveis de Conhecimento)\n\nSelecione **5 perguntas** que melhor se adequam ao processo seletivo. As respostas esperadas já foram definidas pela LIA com base no perfil ideal.`
          : `Adicionei mais ${newQuestions.length} opções de perguntas WSI! Você tem ${selectedCount}/5 selecionadas.`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, feedbackMessage])
      
    } catch (error) {
      
      // Fallback to static questions if API fails
      const baseTs = Date.now()
      const fallbackQuestions: WSIQuestionCandidate[] = [
        { id: `wsi-fallback-${baseTs}-1-${Math.random().toString(36).slice(2, 8)}`, question: 'Qual sua pretensão salarial para regime CLT?', type: 'open', required: true, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-2-${Math.random().toString(36).slice(2, 8)}`, question: `Você tem disponibilidade para trabalho ${ctx.basicInfoFields.modeloTrabalho || 'híbrido'}${ctx.basicInfoFields.localidade ? ` em ${ctx.basicInfoFields.localidade}` : ''}?`, type: 'yes-no', required: true, expectedAnswer: true, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-3-${Math.random().toString(36).slice(2, 8)}`, question: 'Quantos anos de experiência você tem com a principal tecnologia da vaga?', type: 'numeric', required: true, expectedAnswer: 3, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-4-${Math.random().toString(36).slice(2, 8)}`, question: 'Você tem experiência com metodologias ágeis (Scrum, Kanban)?', type: 'yes-no', required: true, expectedAnswer: true, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-5-${Math.random().toString(36).slice(2, 8)}`, question: 'Qual seu nível de inglês?', type: 'multiple-choice', options: ['Básico', 'Intermediário', 'Avançado', 'Fluente'], required: true, correctOptionIndex: 2, selected: false, batch: newBatch },
      ]
      
      const existingTexts = new Set(ctx.wsiCandidates.map(q => q.question.toLowerCase()))
      const newQuestions = fallbackQuestions.filter(q => !existingTexts.has(q.question.toLowerCase())).slice(0, count)
      
      ctx.setWsiCandidates(prev => [...prev, ...newQuestions])
      ctx.setWsiHasGenerated(true)
      
      const feedbackMessage: Message = {
        id: `wsi-feedback-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        role: 'assistant',
        content: `Gerei ${newQuestions.length} perguntas de triagem padrão. Selecione **5 perguntas** para a triagem.`,
        timestamp: new Date()
      }
      ctx.setMessages(prev => [...prev, feedbackMessage])
    } finally {
      ctx.setIsGeneratingWSI(false)
    }
  }, [ctx])

  const toggleWSIQuestionSelection = (questionId: string) => {
    ctx.setWsiCandidates(prev => {
      const currentlySelected = prev.filter(q => q.selected).length
      const question = prev.find(q => q.id === questionId)
      
      if (!question) return prev
      
      // If already at max (5) and trying to select more, don't allow
      if (!question.selected && currentlySelected >= 5) {
        return prev
      }
      
      const updated = prev.map(q => 
        q.id === questionId ? { ...q, selected: !q.selected } : q
      )
      
      // Sync selected questions to wsiQuestions
      const selected = updated.filter(q => q.selected)
        // @ts-ignore
      ctx.setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      
      // If reached 5 questions, add confirmation message
      const newCount = question.selected ? currentlySelected - 1 : currentlySelected + 1
      if (newCount === 5) {
        const confirmMessage: Message = {
          id: `wsi-confirm-${Date.now()}`,
          role: 'assistant',
          content: `Perfeito! Você selecionou **5 perguntas** de triagem.\n\nRevise as respostas esperadas no painel e clique em "Confirmar Triagem" quando estiver pronto para a revisão final.`,
          timestamp: new Date()
        }
        ctx.setMessages(msgs => [...msgs, confirmMessage])
      }
      
      return updated
    })
  }

  const updateWSIQuestionExpectedAnswer = (questionId: string, answer: string | number | boolean) => {
    ctx.setWsiCandidates(prev => {
      const updated = prev.map(q => 
        q.id === questionId ? { ...q, expectedAnswer: answer } : q
      )
      // Sync to wsiQuestions
      const selected = updated.filter(q => q.selected)
        // @ts-ignore
      ctx.setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      return updated
    })
  }

  const updateWSIQuestionCorrectOption = (questionId: string, optionIndex: number) => {
    ctx.setWsiCandidates(prev => {
      const updated = prev.map(q => 
        q.id === questionId ? { ...q, correctOptionIndex: optionIndex } : q
      )
      // Sync to wsiQuestions
      const selected = updated.filter(q => q.selected)
        // @ts-ignore
      ctx.setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      return updated
    })
  }

  const deleteWSIQuestion = (questionId: string) => {
    ctx.setWsiCandidates(prev => {
      const updated = prev.filter(q => q.id !== questionId)
      const selected = updated.filter(q => q.selected)
        // @ts-ignore
      ctx.setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      return updated
    })
  }

  const addCustomQuestion = () => {
    if (!ctx.customQuestionText.trim()) return
    
    const newQuestion: WSIQuestionCandidate = {
      id: `custom-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      question: ctx.customQuestionText.trim(),
      type: ctx.customQuestionType,
      required: ctx.customQuestionRequired,
      selected: false,
      batch: ctx.wsiGenerationBatch,
      isWSI: false,
      category: 'technical'
    }
    
    ctx.setWsiCandidates(prev => [...prev, newQuestion])
    ctx.setShowCustomQuestionForm(false)
    ctx.setCustomQuestionText('')
    ctx.setCustomQuestionType('open')
    ctx.setCustomQuestionRequired(false)
  }

  // Auto-generate WSI questions when entering the stage
  useEffect(() => {
    if (ctx.currentStage === 'wsi-questions' && !ctx.wsiHasGenerated && !ctx.isGeneratingWSI) {
      // Generate technical questions first
      generateWSIQuestions(7, 'technical')
      // Also generate behavioral/fit questions (3-5 based on selected competencies)
      const enabledBehavioralCount = ctx.behavioralCompetencies.filter(c => c.enabled).length
      const behavioralQuestionCount = Math.max(3, Math.min(5, enabledBehavioralCount))
      setTimeout(() => {
        generateWSIQuestions(behavioralQuestionCount, 'behavioral')
      }, 1500) // Small delay to avoid race conditions
    }
  }, [ctx.currentStage, ctx.wsiHasGenerated, ctx.isGeneratingWSI, ctx.behavioralCompetencies, generateWSIQuestions])


  return {
    generateWSIQuestions,
    toggleWSIQuestionSelection,
    updateWSIQuestionExpectedAnswer,
    updateWSIQuestionCorrectOption,
    deleteWSIQuestion,
    addCustomQuestion,
  }
}
