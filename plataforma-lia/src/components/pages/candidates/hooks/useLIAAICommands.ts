"use client"

import { formatScorePercent } from "@/lib/design-tokens"
import type { Candidate } from "../types"
import type { LIAChatMessage, CandidatesLIAHandlersContext } from "./useCandidatesLIAHandlers"
import { useLiaChatContext } from "@/contexts/lia-float-context"

export function useLIAAICommands(ctx: CandidatesLIAHandlersContext) {
  const {
    candidates,
    setChatMessages,
    selectedCandidatesForBatch,
    searchResults,
    setIsLIAThinking,
  } = ctx

  const { switchChatContext } = useLiaChatContext()

  const handleAICommand = async (command: string) => {
    // Ensure unified context is set to candidates before any send
    switchChatContext("talent_chat")
    const trimmedCommand = command.trim().toLowerCase()

    const userMessage: LIAChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: command,
      timestamp: new Date()
    }
    setChatMessages(prev => [...prev, userMessage])
    setIsLIAThinking(true)

    try {
      let liaResponse: LIAChatMessage

      if (trimmedCommand.includes('resumir') && (trimmedCommand.includes('busca') || trimmedCommand.includes('resultado'))) {
        liaResponse = buildSearchSummaryResponse(candidates, searchResults)
      }
      else if (trimmedCommand.includes('top 5') || trimmedCommand.includes('top5') || trimmedCommand.includes('melhores candidatos')) {
        liaResponse = buildTopCandidatesResponse(candidates)
      }
      else if (trimmedCommand.includes('comparar') && (trimmedCommand.includes('selecionado') || selectedCandidatesForBatch.size >= 2)) {
        liaResponse = buildComparisonResponse(candidates, selectedCandidatesForBatch)
      }
      else if (
        trimmedCommand.includes('analisar potencial') ||
        trimmedCommand.includes('potencial de crescimento') ||
        trimmedCommand.includes('definir tipo') ||
        trimmedCommand.includes('tipo de perfil') ||
        trimmedCommand.includes('resumo executivo') ||
        trimmedCommand.includes('pontos a desenvolver') ||
        trimmedCommand.includes('vagas ideais')
      ) {
        liaResponse = await buildCandidateAnalysisResponse(candidates, selectedCandidatesForBatch, searchResults)
      }
      else {
        liaResponse = buildSearchAnalysisResponse(trimmedCommand, candidates, selectedCandidatesForBatch)
      }

      setChatMessages(prev => [...prev, liaResponse])
    } catch (error) {
      const errorMessage: LIAChatMessage = {
        id: `lia-error-${Date.now()}`,
        type: 'lia',
        content: `❌ Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.`,
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLIAThinking(false)
    }
  }

  return { handleAICommand }
}

function buildSearchSummaryResponse(
  candidates: Candidate[],
  searchResults: CandidatesLIAHandlersContext['searchResults']
): LIAChatMessage {
  const totalCandidates = candidates.length
  if (totalCandidates === 0) {
    return { id: `lia-${Date.now()}`, type: 'lia', content: `📊 **Resumo da Busca**\n\nNenhum candidato encontrado ainda.\n\n💡 *Faça uma busca digitando o perfil desejado acima, como "Desenvolvedor Python Sênior".*`, timestamp: new Date() }
  }
  const localCount = candidates.filter(c => c.source === 'local' || !c.source).length
  const avgScore = Math.round(candidates.reduce((acc, c) => acc + (c.score || 0), 0) / totalCandidates)
  const topSkills = candidates.flatMap(c => c.skills || c.technical_skills || []).reduce((acc, skill) => {
    if (skill && typeof skill === 'string') acc[skill] = (acc[skill] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  const sortedSkills = Object.entries(topSkills).sort((a, b) => b[1] - a[1]).slice(0, 5)
  const locations = [...new Set(candidates.map(c => c.location || c.location_city).filter(Boolean))]

  const skillsText = sortedSkills.length > 0
    ? sortedSkills.map(([skill, count]) => `• ${skill} (${count})`).join('\n')
    : '• Nenhuma skill identificada nos perfis'
  const locationsText = locations.length > 0
    ? `${locations.slice(0, 3).join(', ')}${locations.length > 3 ? ` e mais ${locations.length - 3}` : ''}`
    : 'Não especificadas'

  return {
    id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
    content: `📊 **Resumo da Busca**\n\nEncontrei **${totalCandidates} candidato${totalCandidates !== 1 ? 's' : ''}** (${localCount} da base local).\n\n**Nota média de compatibilidade:** ${formatScorePercent(avgScore)}\n\n**Top skills mais comuns:**\n${skillsText}\n\n**Localizações:** ${locationsText}\n\n💡 *Posso analisar candidatos específicos ou comparar os selecionados.*`
  }
}

function buildTopCandidatesResponse(candidates: Candidate[]): LIAChatMessage {
  if (candidates.length === 0) {
    return { id: `lia-${Date.now()}`, type: 'lia', content: `🏆 **Top Candidatos**\n\nNenhum candidato disponível ainda.\n\n💡 *Faça uma busca para encontrar candidatos.*`, timestamp: new Date() }
  }
  const topCandidates = [...candidates].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 5)
  const topList = topCandidates.map((c, i) => {
    const candidateSkills = c.skills || c.technical_skills || []
    const skillsPreview = candidateSkills.length > 0
      ? ` | Skills: ${candidateSkills.slice(0, 3).join(', ')}${candidateSkills.length > 3 ? '...' : ''}`
      : ''
    return `${i + 1}. **${c.name}** - ${c.position || c.current_title || 'N/A'} @ ${c.current_company || 'N/A'} (Nota: ${formatScorePercent(c.score || 0)})${skillsPreview}`
  }).join('\n')
  return { id: `lia-${Date.now()}`, type: 'lia', content: `🏆 **Top ${topCandidates.length} Candidatos**\n\n${topList}\n\n💡 *Selecione candidatos para análise mais detalhada ou comparação.*`, timestamp: new Date() }
}

function buildComparisonResponse(candidates: Candidate[], selectedCandidatesForBatch: Set<string>): LIAChatMessage {
  if (selectedCandidatesForBatch.size < 2) {
    return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione pelo menos 2 candidatos** para fazer a comparação.\n\nClique na checkbox ao lado de cada candidato na tabela.`, timestamp: new Date() }
  }
  const selectedCandidates = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
  if (selectedCandidates.length === 0) {
    return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Candidatos não encontrados**\n\nOs candidatos selecionados não foram localizados. Tente fazer uma nova busca.`, timestamp: new Date() }
  }
  const comparison = selectedCandidates.map(c => {
    const candidateSkills = c.skills || c.technical_skills || []
    const skillsText = candidateSkills.length > 0 ? candidateSkills.slice(0, 5).join(', ') : 'Não informadas'
    const expYears = c.experience ?? c.years_of_experience
    const experienceText = typeof expYears === 'number' ? `${expYears} ${expYears === 1 ? 'ano' : 'anos'}` : 'Não informado'
    return `**${c.name}**\n• Cargo: ${c.position || c.current_title || 'Não informado'}\n• Empresa: ${c.current_company || 'Não informada'}\n• Experiência: ${experienceText}\n• Nota: ${formatScorePercent(c.score || 0)}\n• Skills: ${skillsText}`
  }).join('\n\n')
  return { id: `lia-${Date.now()}`, type: 'lia', content: `⚖️ **Comparação de ${selectedCandidates.length} Candidatos**\n\n${comparison}\n\n💡 *Clique no score CV de cada candidato na tabela para ver a análise detalhada.*`, timestamp: new Date() }
}

async function buildCandidateAnalysisResponse(
  candidates: Candidate[],
  selectedCandidatesForBatch: Set<string>,
  searchResults: CandidatesLIAHandlersContext['searchResults']
): Promise<LIAChatMessage> {
  if (selectedCandidatesForBatch.size === 0) {
    return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Nenhum candidato selecionado**\n\nSelecione um ou mais candidatos na tabela para que eu possa analisar.\n\n💡 Clique na checkbox ao lado do nome do candidato.`, timestamp: new Date() }
  }
  const selectedCandidates = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
  if (selectedCandidates.length === 0) {
    return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Candidatos não encontrados**\n\nOs candidatos selecionados não foram localizados. Tente fazer uma nova busca.`, timestamp: new Date() }
  }

  try {
    const candidatesForApi = selectedCandidates.map(c => ({
      id: c.id, name: c.name,
      position: c.position || c.current_title || 'Profissional',
      location: c.location || c.location_city || 'Não especificada',
      company: c.current_company || 'Não especificada',
      skills: c.skills || c.technical_skills || [],
      experience_years: c.experience || c.years_of_experience || 0,
      seniority_level: c.seniority_level || 'pleno',
      cv_text: c.resume_text || c.self_introduction || ''
    }))

    let jobTitleForApi = 'Análise de perfil profissional'
    const queryText = searchResults?.query?.trim()
    const firstPosition = selectedCandidates[0]?.position?.trim() || selectedCandidates[0]?.current_title?.trim()
    if (queryText && queryText.length > 0) jobTitleForApi = queryText
    else if (firstPosition && firstPosition.length > 0) jobTitleForApi = firstPosition

    const response = await fetch('/api/backend-proxy/api/v1/analysis/candidates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidates: candidatesForApi, analysis_type: 'general', job_title: jobTitleForApi })
    })

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Erro desconhecido')
      let userErrorMessage = ''
      if (response.status === 422) userErrorMessage = 'Dados do candidato inválidos ou incompletos.'
      else if (response.status === 401 || response.status === 403) userErrorMessage = 'Não autorizado. Verifique suas credenciais.'
      else if (response.status >= 500) userErrorMessage = 'Serviço de análise temporariamente indisponível.'
      else userErrorMessage = `Erro ${response.status}: ${errorText.substring(0, 80)}`
      throw new Error(userErrorMessage)
    }

    const data = await response.json()
    const results = data.results || []

    if (results.length === 0) {
      return { id: `lia-${Date.now()}`, type: 'lia', content: `🧠 **Análise LIA**\n\nNenhum resultado de análise gerado para os candidatos selecionados.\n\n**Possíveis causas:**\n• Perfis com informações insuficientes\n• Erro temporário no serviço de análise\n\n💡 *Tente selecionar candidatos com perfis mais completos.*`, timestamp: new Date() }
    }

    let analysisContent = `🧠 **Análise LIA**\n\n`
    for (const result of results) {
      analysisContent += `**${result.candidate_name || 'Candidato'}**\n`
      analysisContent += `• **Arquétipo:** ${result.archetype || 'Executor Confiável'}\n`
      analysisContent += `• **Score LIA:** ${formatScorePercent(result.lia_score || 0)}\n`
      analysisContent += `• **Fit de Personalidade:** ${formatScorePercent(result.fit_score || 0)}\n`
      if (result.strengths?.length > 0) analysisContent += `• **Pontos fortes:** ${result.strengths.slice(0, 3).join(', ')}\n`
      if (result.gaps?.length > 0) analysisContent += `• **Pontos a desenvolver:** ${result.gaps.slice(0, 2).join(', ')}\n`
      if (result.recommendation) analysisContent += `• **Recomendação:** ${result.recommendation}\n`
      if (result.potential_roles?.length > 0) analysisContent += `• **Vagas ideais:** ${result.potential_roles.slice(0, 3).join(', ')}\n`
      analysisContent += `\n`
    }
    return { id: `lia-${Date.now()}`, type: 'lia', content: analysisContent, timestamp: new Date() }
  } catch (apiError) {
    const errorMessage = apiError instanceof Error ? apiError.message : 'Erro desconhecido'
    const sc = selectedCandidates[0]
    const candidateSkills = sc.skills || sc.technical_skills || []
    const skillsText = candidateSkills.length > 0 ? candidateSkills.slice(0, 5).join(', ') : 'Não informadas'
    const expYears = sc.experience ?? sc.years_of_experience
    const experienceText = typeof expYears === 'number' ? `${expYears} ${expYears === 1 ? 'ano' : 'anos'}` : 'Não informada'
    return {
      id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
      content: `🧠 **Análise de ${sc.name}** (modo offline)\n\n**⚠️ Motivo:** ${errorMessage}\n\n**Perfil:** ${sc.position || sc.current_title || 'Profissional'}\n**Empresa:** ${sc.current_company || 'Não informada'}\n**Experiência:** ${experienceText}\n**Skills:** ${skillsText}\n\n**Arquétipo sugerido:** Executor Confiável\n**Potencial:** Alto para funções técnicas\n\n💡 *Esta é uma análise simplificada. Tente novamente mais tarde para análise completa com IA.*`
    }
  }
}

function buildSearchAnalysisResponse(
  trimmedCommand: string,
  candidates: Candidate[],
  selectedCandidatesForBatch: Set<string>
): LIAChatMessage {
  if (trimmedCommand.includes('quantos candidatos') || trimmedCommand.includes('quantos encontrei')) {
    return {
      id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
      content: candidates.length === 0
        ? `📊 **Nenhum candidato encontrado** ainda.\n\n💡 *Faça uma busca para ver resultados.*`
        : `📊 **Total de candidatos:** ${candidates.length}\n\n• Base local: ${candidates.filter(c => c.source === 'local' || !c.source).length}\n• Base global: ${candidates.filter(c => c.source === 'global' || c.source === 'pearch').length}\n\n💡 *Selecione candidatos para análise detalhada.*`
    }
  }
  if (trimmedCommand.includes('score') && (trimmedCommand.includes('médio') || trimmedCommand.includes('media') || trimmedCommand.includes('lia'))) {
    const avgScore = candidates.length > 0 ? Math.round(candidates.reduce((acc, c) => acc + (c.score || c.lia_score || 0), 0) / candidates.length) : 0
    const highScoreCount = candidates.filter(c => (c.score || c.lia_score || 0) >= 70).length
    return {
      id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
      content: candidates.length === 0
        ? `📊 **Nenhum candidato** para calcular score médio.\n\n💡 *Faça uma busca primeiro.*`
        : `📊 **Score LIA médio:** ${formatScorePercent(avgScore)}\n\n• Candidatos com score ≥70%: **${highScoreCount}** (${Math.round(highScoreCount/candidates.length*100)}%)\n• Score máximo: ${formatScorePercent(Math.max(...candidates.map(c => c.score || c.lia_score || 0)))}\n• Score mínimo: ${formatScorePercent(Math.min(...candidates.map(c => c.score || c.lia_score || 0)))}\n\n💡 *Os candidatos de maior score geralmente têm melhor fit com a vaga.*`
    }
  }
  if (trimmedCommand.includes('skills') && (trimmedCommand.includes('comuns') || trimmedCommand.includes('mais'))) {
    const allSkills = candidates.flatMap(c => c.skills || c.technical_skills || [])
    const skillCounts = allSkills.reduce((acc, skill) => { if (skill && typeof skill === 'string') acc[skill] = (acc[skill] || 0) + 1; return acc }, {} as Record<string, number>)
    const topSkills = Object.entries(skillCounts).sort((a, b) => b[1] - a[1]).slice(0, 10)
    return {
      id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
      content: topSkills.length === 0
        ? `📊 **Nenhuma skill identificada** nos perfis.\n\n💡 *Os candidatos podem não ter skills cadastradas.*`
        : `📊 **Competências Principais mais comuns:**\n\n${topSkills.map(([skill, count], i) => `${i+1}. **${skill}** - ${count} candidato${count > 1 ? 's' : ''}`).join('\n')}\n\n💡 *Use essas competências como filtro para refinar sua busca.*`
    }
  }
  if (trimmedCommand.includes('experiência') && trimmedCommand.includes('média')) {
    const withExp = candidates.filter(c => typeof (c.experience ?? c.years_of_experience) === 'number')
    const avgExp = withExp.length > 0 ? (withExp.reduce((acc, c) => acc + (c.experience ?? c.years_of_experience ?? 0), 0) / withExp.length).toFixed(1) : 0
    return {
      id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
      content: withExp.length === 0
        ? `📊 **Experiência não informada** nos perfis.\n\n💡 *Os candidatos podem não ter anos de experiência cadastrados.*`
        : `📊 **Experiência média:** ${avgExp} anos\n\n• Candidatos com experiência informada: ${withExp.length}/${candidates.length}\n• Mais experiente: ${Math.max(...withExp.map(c => c.experience ?? c.years_of_experience ?? 0))} anos\n• Menos experiente: ${Math.min(...withExp.map(c => c.experience ?? c.years_of_experience ?? 0))} anos\n\n💡 *Filtrar por experiência pode refinar seus resultados.*`
    }
  }
  if (trimmedCommand.includes('onde estão') || trimmedCommand.includes('localizados') || trimmedCommand.includes('localização')) {
    const locations = candidates.map(c => c.location || c.location_city || c.location_state).filter(Boolean)
    const locationCounts = locations.reduce((acc, loc) => { acc[loc as string] = (acc[loc as string] || 0) + 1; return acc }, {} as Record<string, number>)
    const topLocations = Object.entries(locationCounts).sort((a, b) => b[1] - a[1]).slice(0, 8)
    return {
      id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
      content: topLocations.length === 0
        ? `📍 **Localização não informada** nos perfis.\n\n💡 *Os candidatos podem não ter localização cadastrada.*`
        : `📍 **Distribuição por localização:**\n\n${topLocations.map(([loc, count]) => `• **${loc}**: ${count} candidato${count > 1 ? 's' : ''}`).join('\n')}\n\n💡 *${candidates.filter(c => c.is_remote).length} candidatos aceitam trabalho remoto.*`
    }
  }
  if (trimmedCommand.includes('nota') && trimmedCommand.includes('acima')) {
    const threshold = 70
    const aboveCount = candidates.filter(c => (c.score || c.lia_score || 0) >= threshold).length
    return {
      id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
      content: `📊 **Candidatos com nota LIA ≥${threshold}%:** ${aboveCount}\n\n• Total de candidatos: ${candidates.length}\n• Porcentagem qualificados: ${candidates.length > 0 ? Math.round(aboveCount/candidates.length*100) : 0}%\n\n💡 *Candidatos acima de 70% geralmente são bons matches.*`
    }
  }
  if (trimmedCommand.includes('pontos fortes') && trimmedCommand.includes('comum')) {
    if (selectedCandidatesForBatch.size === 0) {
      return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para analisar pontos fortes em comum.`, timestamp: new Date() }
    }
    const selected = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
    const allSkills = selected.flatMap(c => c.skills || c.technical_skills || [])
    const skillCounts = allSkills.reduce((acc, s) => { if (s) acc[s] = (acc[s] || 0) + 1; return acc }, {} as Record<string, number>)
    const commonSkills = Object.entries(skillCounts).filter(([_, count]) => count >= Math.ceil(selected.length * 0.5)).map(([skill]) => skill)
    return {
      id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
      content: commonSkills.length === 0
        ? `📊 **Nenhuma skill em comum** encontrada entre os ${selected.length} candidatos selecionados.`
        : `📊 **Pontos fortes em comum** (${selected.length} candidatos):\n\n${commonSkills.slice(0, 8).map(s => `• **${s}**`).join('\n')}\n\n💡 *Essas são as competências compartilhadas pela maioria.*`
    }
  }
  if (trimmedCommand.includes('gaps') || trimmedCommand.includes('competência')) {
    if (selectedCandidatesForBatch.size === 0) {
      return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para identificar gaps de competência.`, timestamp: new Date() }
    }
    return { id: `lia-${Date.now()}`, type: 'lia', content: `🔍 **Análise de Gaps**\n\nPara identificar gaps precisos, preciso conhecer os requisitos da vaga.\n\n💡 **Sugestão:** Selecione uma vaga no seletor acima para comparar candidatos com os requisitos específicos.`, timestamp: new Date() }
  }
  if (trimmedCommand.includes('prioridade') || trimmedCommand.includes('organize')) {
    const sorted = [...candidates].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 10)
    return {
      id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
      content: sorted.length === 0
        ? `📊 **Nenhum candidato** para organizar.\n\n💡 *Faça uma busca primeiro.*`
        : `📊 **Candidatos por prioridade:**\n\n${sorted.map((c, i) => `${i+1}. **${c.name}** - Nota: ${formatScorePercent(c.score || 0)} | ${c.position || c.current_title || 'N/A'}`).join('\n')}\n\n💡 *Ordenados por score de compatibilidade.*`
    }
  }
  if (trimmedCommand.includes('melhorar') && trimmedCommand.includes('busca')) {
    return { id: `lia-${Date.now()}`, type: 'lia', content: `💡 **Dicas para melhorar sua busca:**\n\n• Adicione **skills específicas** (ex: "Python, AWS")\n• Defina **nível de senioridade** (júnior, pleno, sênior)\n• Especifique **localização** (cidade ou "remoto")\n• Use **palavras-chave** do cargo desejado\n• Tente **termos alternativos** para a mesma função\n\n**Exemplo:** "Desenvolvedor Backend Python sênior São Paulo remoto"`, timestamp: new Date() }
  }
  if (trimmedCommand.includes('resuma') && trimmedCommand.includes('perfil') && trimmedCommand.includes('selecionado')) {
    if (selectedCandidatesForBatch.size === 0) {
      return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para resumir seus perfis.`, timestamp: new Date() }
    }
    const selected = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
    const summary = selected.map(c => `**${c.name}**\n${c.position || c.current_title || 'Profissional'} @ ${c.current_company || 'N/A'}`).join('\n\n')
    return { id: `lia-${Date.now()}`, type: 'lia', content: `📋 **Resumo dos perfis selecionados:**\n\n${summary}\n\n💡 *Para análise detalhada, use "Analisar potencial de crescimento".*`, timestamp: new Date() }
  }

  return {
    id: `lia-${Date.now()}`, type: 'lia', timestamp: new Date(),
    content: `🤔 Entendi sua solicitação, mas **ainda não consigo responder a esse tipo de pergunta**.\n\nEstou em constante evolução e **em breve serei capaz** de atender você em diversas situações e demandas do seu dia a dia como recrutador!\n\n**Por enquanto, posso ajudar você com:**\n\n📊 **Análises de busca:**\n• Resumir esta busca\n• Top 5 candidatos\n• Skills mais comuns\n• Nota média dos candidatos\n\n👥 **Análise de candidatos selecionados:**\n• Analisar potencial de crescimento\n• Comparar candidatos\n• Pontos fortes em comum\n• Definir tipo de perfil\n\n💡 *Clique em "Mais ideias" para ver todas as opções disponíveis!*`
  }
}
