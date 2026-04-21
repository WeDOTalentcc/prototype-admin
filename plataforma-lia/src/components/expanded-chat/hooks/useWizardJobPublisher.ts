"use client"

import { formatBRL } from "@/lib/pricing"
import { liaApi, type JobVacancyCreateRequest } from "@/services/lia-api"
import type { WizardPublishHandlersContext } from "./wizardPublishHandlers.types"

export function useWizardJobPublisher(ctx: WizardPublishHandlersContext) {
  const buildCandidateSearchQuery = (): string => {
    const { basicInfoFields, detectedCriteria, technicalSkills } = ctx
    const parts: string[] = []
    if (basicInfoFields.cargo) parts.push(basicInfoFields.cargo)
    if (detectedCriteria.senioridadeIdiomas) parts.push(detectedCriteria.senioridadeIdiomas)
    if (basicInfoFields.area) parts.push(basicInfoFields.area)
    const topSkills = technicalSkills.slice(0, 5).map(s => s.name)
    if (topSkills.length > 0) parts.push(topSkills.join(', '))
    if (basicInfoFields.localidade) parts.push(basicInfoFields.localidade)
    return parts.join(' ') || 'profissional'
  }

  const startLocalSearch = async () => {
    const { setSearchPhase, setLocalCandidateCount, preferredCandidateCount } = ctx
    setSearchPhase('local-searching')
    try {
      const searchQuery = buildCandidateSearchQuery()
      const response = await liaApi.searchCandidatesLocal({
        query: searchQuery,
        limit: Math.max(20, preferredCandidateCount * 5)
      })
      setLocalCandidateCount(response.total_results || response.candidates?.length || 0)
      setSearchPhase('local-complete')
    } catch (error) {
      setLocalCandidateCount(0)
      setSearchPhase('local-complete')
    }
  }

  const startGlobalSearch = async () => {
    const { setSearchPhase, setGlobalCandidateCount, preferredCandidateCount } = ctx
    setSearchPhase('global-searching')
    try {
      const searchQuery = buildCandidateSearchQuery()
      const response = await liaApi.searchCandidates({
        query: searchQuery,
        search_type: 'fast',
        limit: Math.max(100, preferredCandidateCount * 20)
      })
      setGlobalCandidateCount(response.total_results || response.candidates?.length || 0)
      setSearchPhase('global-complete')
    } catch (error) {
      setGlobalCandidateCount(0)
      setSearchPhase('global-complete')
    }
  }

  const handlePublishJob = async () => {
    const {
      basicInfoFields, detectedCriteria, technicalSkills, behavioralCompetencies,
      salaryInfo, publishingPlatforms, jobConfig, interviewStages, wsiCandidates,
      companyDefaultQuestions, companyMembersMap, conversationId, user,
      wizardFastTrackSourceJobId, setWizardFastTrackSourceJobId,
      setPublishedJobId, setAwaitingCalibrationChoice, setCurrentStage,
      clearWizardDraft, setMessages, setIsLoading
    } = ctx

    setIsLoading(true)
    try {
      const linkedinPlatform = publishingPlatforms.find(p => p.id === 'linkedin')
      const indeedPlatform = publishingPlatforms.find(p => p.id === 'indeed')
      const websitePlatform = publishingPlatforms.find(p => p.id === 'website')

      const jobData = {
        title: basicInfoFields.cargo || 'Nova Vaga',
        department: basicInfoFields.area || undefined,
        location: basicInfoFields.localidade || undefined,
        work_model: basicInfoFields.modeloTrabalho || undefined,
        hybrid_days_onsite: basicInfoFields.modeloTrabalho === 'Híbrido'
          ? (jobConfig.hybridDaysOnsite || 3)
          : undefined,
        employment_type: basicInfoFields.tipoContrato || 'CLT',
        seniority_level: detectedCriteria.senioridadeIdiomas || 'Pleno',
        description: ctx.messages.find(m => m.role === 'user')?.content || `Vaga de ${basicInfoFields.cargo}`,
        requirements: technicalSkills.filter(s => s.required).map(s => s.name),
        technical_requirements: technicalSkills.map(s => ({
          name: s.name,
          level: s.level,
          required: s.required,
          weight: s.weight
        })),
        behavioral_competencies: behavioralCompetencies.filter(c => c.enabled).map(c => ({
          name: c.name,
          weight: c.weight,
          justification: c.justification
        })),
        salary: salaryInfo.minSalary && salaryInfo.maxSalary
          ? `${formatBRL(parseInt(salaryInfo.minSalary))} - ${formatBRL(parseInt(salaryInfo.maxSalary))}`
          : undefined,
        salary_range: (salaryInfo.minSalary || salaryInfo.maxSalary || salaryInfo.minBonus || salaryInfo.maxBonus) ? {
          min: salaryInfo.minSalary ? parseInt(salaryInfo.minSalary) : undefined,
          max: salaryInfo.maxSalary ? parseInt(salaryInfo.maxSalary) : undefined,
          currency: 'BRL',
          bonus_min: salaryInfo.minBonus ? parseInt(salaryInfo.minBonus) : undefined,
          bonus_max: salaryInfo.maxBonus ? parseInt(salaryInfo.maxBonus) : undefined
        } : undefined,
        // Task #765 — send the full structured benefit objects so the
        // backend can persist category, value/value_type, provider,
        // is_highlighted, is_mandatory, etc. The previous `.map(b =>
        // b.name)` collapse silently destroyed every field but the name.
        benefits: salaryInfo.benefits
          .filter(b => b.enabled)
          .map(({ enabled: _enabled, ...rest }) => rest),
        manager: basicInfoFields.gestor || undefined,
        status: 'active' as const,
        recruiter: user?.name || user?.email?.split('@')[0] || 'Recrutador',
        recruiter_email: user?.email || '',
        open_date: new Date().toISOString(),
        urgency_level: jobConfig.urgencyLevel,
        visibility: jobConfig.visibility,
        is_confidential: jobConfig.isConfidential,
        is_affirmative: jobConfig.isAffirmative,
        affirmative_criteria_primary: detectedCriteria.affirmativeCriteriaPrimary,
        affirmative_criteria_secondary: detectedCriteria.affirmativeCriteriaSecondary,
        affirmative_description: detectedCriteria.affirmativeDescription,
        deadline: jobConfig.deadline,
        deadline_screening: jobConfig.deadlineScreening,
        deadline_shortlist: jobConfig.deadlineShortlist,
        languages: jobConfig.languages.map(l => ({ name: l.name, level: l.level })),
        stage: 'screening',
        target_audience: jobConfig.visibility === 'internal' || jobConfig.visibility === 'confidential' ? 'internal' : 'external',
        masked_company_name: jobConfig.isConfidential ? 'Empresa Confidencial' : undefined,
        interview_stages: interviewStages.length > 0
          ? interviewStages.map((stage, index) => ({
              stageName: stage.name,
              order: index + 1,
              type: stage.name.toLowerCase().includes('triagem') ? 'screening' :
                    stage.name.toLowerCase().includes('técnic') ? 'technical' :
                    stage.name.toLowerCase().includes('rh') ? 'interview' :
                    stage.name.toLowerCase().includes('final') || stage.name.toLowerCase().includes('gestor') ? 'final' :
                    'interview',
              sla: stage.sla
            }))
          : [
              { stageName: 'Triagem', order: 1, type: 'screening' },
              { stageName: 'Entrevista RH', order: 2, type: 'interview' },
              { stageName: 'Entrevista Técnica', order: 3, type: 'technical' },
              { stageName: 'Entrevista Final', order: 4, type: 'final' },
            ],
        hiring_process: interviewStages.length > 0
          ? interviewStages.map(stage => stage.name)
          : ['Triagem', 'Entrevista RH', 'Entrevista Técnica', 'Entrevista Final'],
        published_linkedin: linkedinPlatform?.enabled || false,
        published_indeed: indeedPlatform?.enabled || false,
        published_website: websitePlatform?.enabled || false,
        eligibility_questions: companyDefaultQuestions.filter(q => q.enabled).map(q => ({
          question: q.question,
          category: 'eligibility',
          type: q.type,
          weight: 3,
          is_eliminatory: true
        })),
        screening_questions: wsiCandidates.filter(q => q.selected).map(q => ({
          question: q.question,
          category: q.category,
          expected_answer: q.expectedAnswer,
          weight: 5,
          type: q.type
        })),
        conversation_id: conversationId || undefined
      }

      const createdJob = await liaApi.createJobVacancy(jobData as JobVacancyCreateRequest)

      const jobId = ((createdJob as unknown) as Record<string, unknown>).job_id || ((createdJob as unknown) as Record<string, unknown>).id
      setPublishedJobId(String(jobId))

      if (wizardFastTrackSourceJobId && jobId && jobId !== wizardFastTrackSourceJobId) {
        const tenantId = ctx.resolvedCompanyId ?? ''
        liaApi.recordFastTrackUsage({
          company_id: tenantId,
          source_job_id: wizardFastTrackSourceJobId as string,
          new_job_id: String(jobId),
          modified_fields: [],
          was_published: true
        }).catch((err) => { console.warn('[useWizardJobPublisher] recordFastTrackUsage fire-and-forget failed', err) })
        setWizardFastTrackSourceJobId(null)
      }

      try {
        await liaApi.sendJobCreatedNotification({
          job_id: String(jobId),
          job_title: basicInfoFields.cargo || 'Nova Vaga',
          department: basicInfoFields.area || undefined,
          location: basicInfoFields.localidade || undefined,
          work_model: basicInfoFields.modeloTrabalho || undefined,
          seniority_level: detectedCriteria.senioridadeIdiomas || undefined,
          job_description: ctx.messages.find(m => m.role === 'user')?.content || `Vaga de ${basicInfoFields.cargo}`,
          technical_requirements: technicalSkills.map(s => ({
            name: s.name,
            level: s.level,
            required: s.required,
            weight: s.weight
          })),
          behavioral_competencies: behavioralCompetencies.filter(c => c.enabled).map(c => ({
            name: c.name,
            weight: String(c.weight)
          })),
          languages: jobConfig.languages.map(l => ({ name: l.name, level: l.level })),
          salary_range: (salaryInfo.minSalary || salaryInfo.maxSalary) ? {
            min: salaryInfo.minSalary ? parseInt(salaryInfo.minSalary) : undefined,
            max: salaryInfo.maxSalary ? parseInt(salaryInfo.maxSalary) : undefined,
            currency: 'BRL'
          } : undefined,
          // Notification payload still expects a flat list of names —
          // structured benefits are persisted via the createJobVacancy
          // call above (see Task #765).
          benefits: salaryInfo.benefits.filter(b => b.enabled).map(b => b.name),
          deadline_screening: jobConfig.deadlineScreening,
          deadline_shortlist: jobConfig.deadlineShortlist,
          deadline_closing: jobConfig.deadline,
          interview_stages: interviewStages.map((stage, index) => ({
            stageName: stage.name,
            order: index + 1,
            sla: stage.sla
          })),
          publishing_platforms: {
            linkedin: linkedinPlatform?.enabled || false,
            indeed: indeedPlatform?.enabled || false,
            website: websitePlatform?.enabled || false
          },
          urgency_level: jobConfig.urgencyLevel,
          is_confidential: jobConfig.isConfidential,
          is_affirmative: jobConfig.isAffirmative,
          recruiter_email: user?.email || '',
          recruiter_name: user?.name || user?.email?.split('@')[0] || 'Recrutador',
          manager_email: basicInfoFields.gestor
            ? (companyMembersMap.get(basicInfoFields.gestor.trim()) ||
               companyMembersMap.get(basicInfoFields.gestor.trim().toLowerCase()))
            : undefined,
          manager_name: basicInfoFields.gestor || undefined,
          channels: ['email', 'teams']
        })
      } catch (notifError) {
      }

      const publishMessage = {
        id: `publish-${Date.now()}`,
        role: 'assistant' as const,
        content: `A vaga **${basicInfoFields.cargo || 'Nova Vaga'}** foi criada e publicada com sucesso! 🎉

📋 **ID da Vaga:** ${jobId}
🏢 **Área:** ${basicInfoFields.area || 'A definir'}
📍 **Local:** ${basicInfoFields.localidade || 'A definir'}

---

**Próximo passo: Calibração de Busca**

Posso apresentar alguns candidatos para você avaliar agora. Isso me ajuda a entender melhor o perfil ideal e melhora a precisão das próximas sugestões em até 60%.

**OU** você pode ir direto para o Kanban e eu aprendo naturalmente conforme você move candidatos pelo funil (aprovar → entrevista, reprovar → descartado).

*O que prefere?*
• "Calibrar agora" - mostro 5 perfis rápidos para você avaliar
• "Ir para o kanban" - já adiciono os candidatos e você avalia lá`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, publishMessage])

      setAwaitingCalibrationChoice(true)
      setCurrentStage('search-calibration')
      clearWizardDraft()
      startLocalSearch()
    } catch (error) {

      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant' as const,
        content: `Desculpe, ocorreu um erro ao criar a vaga. Por favor, tente novamente.\n\nErro: ${error instanceof Error ? error.message : 'Erro desconhecido'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const generateJobDescription = () => {
    const { basicInfoFields, technicalSkills, behavioralCompetencies, salaryInfo, companyConfig, setJobDescription, setIsGeneratingDescription } = ctx

    setIsGeneratingDescription(true)

    const skills = technicalSkills.slice(0, 5).map(s => s.name).join(', ')
    const competencies = behavioralCompetencies.filter(c => c.enabled).slice(0, 3).map(c => c.name).join(', ')
    const benefits = salaryInfo.benefits.filter(b => b.enabled).slice(0, 4).map(b => b.name).join(', ')

    const description = `Estamos em busca de um(a) ${basicInfoFields.cargo || 'profissional'} para integrar nossa equipe de ${basicInfoFields.area || 'alto desempenho'}.

📍 **Local:** ${basicInfoFields.localidade || 'A definir'} | ${basicInfoFields.modeloTrabalho || 'Flexível'}
📝 **Contrato:** ${basicInfoFields.tipoContrato || 'CLT'}

**O que você vai encontrar:**
• Oportunidade de crescimento em ambiente ${companyConfig?.values?.includes('inovação') ? 'inovador' : 'dinâmico'}
• Projetos desafiadores na área de ${basicInfoFields.area || 'tecnologia'}
${benefits ? `• Benefícios: ${benefits}` : '• Pacote de benefícios competitivo'}

**O que buscamos:**
${skills ? `• Experiência com: ${skills}` : '• Conhecimentos técnicos na área'}
${competencies ? `• Perfil: ${competencies}` : '• Profissional colaborativo e proativo'}
• Experiência compatível com a posição

${salaryInfo.minSalary && salaryInfo.maxSalary ? `💰 **Faixa salarial:** ${formatBRL(Number(salaryInfo.minSalary))} - ${formatBRL(Number(salaryInfo.maxSalary))}` : ''}

Venha fazer parte do nosso time! 🚀`

    setTimeout(() => {
      setJobDescription(description)
      setIsGeneratingDescription(false)
    }, 1200)
  }

  return {
    handlePublishJob,
    buildCandidateSearchQuery,
    generateJobDescription,
    startLocalSearch,
    startGlobalSearch,
  }
}
