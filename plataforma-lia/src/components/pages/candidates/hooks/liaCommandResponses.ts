import { formatScorePercent } from "@/lib/design-tokens"
import type { LIAChatMessage } from "./useCandidatesLIAHandlers"
import type { Candidate } from "../types"

export function buildSearchSummaryResponse(candidates: Candidate[]): LIAChatMessage {
  if (candidates.length === 0) {
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: `📊 **Resumo da Busca**\n\nNenhum candidato encontrado ainda.\n\n💡 *Faça uma busca digitando o perfil desejado acima, como "Desenvolvedor Python Sênior".*`,
      timestamp: new Date()
    }
  }

  const totalCandidates = candidates.length
  const localCount = candidates.filter(c => c.source === 'local' || !c.source).length
  const avgScore = Math.round(candidates.reduce((acc, c) => acc + (c.score || 0), 0) / totalCandidates)
  const topSkills = candidates.flatMap(c => c.skills || c.technical_skills || []).reduce((acc, skill) => {
    if (skill && typeof skill === 'string') {
      acc[skill] = (acc[skill] || 0) + 1
    }
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
    id: `lia-${Date.now()}`,
    type: 'lia',
    content: `📊 **Resumo da Busca**\n\nEncontrei **${totalCandidates} candidato${totalCandidates !== 1 ? 's' : ''}** (${localCount} da base local).\n\n**Nota média de compatibilidade:** ${formatScorePercent(avgScore)}\n\n**Top skills mais comuns:**\n${skillsText}\n\n**Localizações:** ${locationsText}\n\n💡 *Posso analisar candidatos específicos ou comparar os selecionados.*`,
    timestamp: new Date()
  }
}

export function buildTopCandidatesResponse(candidates: Candidate[]): LIAChatMessage {
  if (candidates.length === 0) {
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: `🏆 **Top Candidatos**\n\nNenhum candidato disponível ainda.\n\n💡 *Faça uma busca para encontrar candidatos.*`,
      timestamp: new Date()
    }
  }

  const topCandidates = [...candidates].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 5)
  const topCount = topCandidates.length
  const topList = topCandidates.map((c, i) => {
    const candidateSkills = c.skills || c.technical_skills || []
    const skillsPreview = candidateSkills.length > 0
      ? ` | Skills: ${candidateSkills.slice(0, 3).join(', ')}${candidateSkills.length > 3 ? '...' : ''}`
      : ''
    return `${i + 1}. **${c.name}** - ${c.position || c.current_title || 'N/A'} @ ${c.current_company || 'N/A'} (Nota: ${formatScorePercent(c.score || 0)})${skillsPreview}`
  }).join('\n')

  return {
    id: `lia-${Date.now()}`,
    type: 'lia',
    content: `🏆 **Top ${topCount} Candidatos**\n\n${topList}\n\n💡 *Selecione candidatos para análise mais detalhada ou comparação.*`,
    timestamp: new Date()
  }
}

export function buildCompareResponse(candidates: Candidate[], selectedIds: Set<string>): LIAChatMessage {
  if (selectedIds.size < 2) {
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: `⚠️ **Selecione pelo menos 2 candidatos** para fazer a comparação.\n\nClique na checkbox ao lado de cada candidato na tabela.`,
      timestamp: new Date()
    }
  }

  const selectedCandidates = candidates.filter(c => selectedIds.has(c.id))
  if (selectedCandidates.length === 0) {
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: `⚠️ **Candidatos não encontrados**\n\nOs candidatos selecionados não foram localizados. Tente fazer uma nova busca.`,
      timestamp: new Date()
    }
  }

  const comparison = selectedCandidates.map(c => {
    const candidateSkills = c.skills || c.technical_skills || []
    const skillsText = candidateSkills.length > 0
      ? candidateSkills.slice(0, 5).join(', ')
      : 'Não informadas'
    const expYears = c.experience ?? c.years_of_experience
    const experienceText = typeof expYears === 'number'
      ? `${expYears} ${expYears === 1 ? 'ano' : 'anos'}`
      : 'Não informado'
    return `**${c.name}**\n• Cargo: ${c.position || c.current_title || 'Não informado'}\n• Empresa: ${c.current_company || 'Não informada'}\n• Experiência: ${experienceText}\n• Nota: ${formatScorePercent(c.score || 0)}\n• Skills: ${skillsText}`
  }).join('\n\n')

  return {
    id: `lia-${Date.now()}`,
    type: 'lia',
    content: `⚖️ **Comparação de ${selectedCandidates.length} Candidatos**\n\n${comparison}\n\n💡 *Clique no score CV de cada candidato na tabela para ver a análise detalhada.*`,
    timestamp: new Date()
  }
}

export function buildSimpleAnalyticsResponse(
  command: string,
  candidates: Candidate[],
  selectedIds: Set<string>
): LIAChatMessage | null {
  const trimmed = command.trim().toLowerCase()

  if (trimmed.includes('quantos candidatos') || trimmed.includes('quantos encontrei')) {
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: candidates.length === 0
        ? `📊 **Nenhum candidato encontrado** ainda.\n\n💡 *Faça uma busca para ver resultados.*`
        : `📊 **Total de candidatos:** ${candidates.length}\n\n• Base local: ${candidates.filter(c => c.source === 'local' || !c.source).length}\n• Base global: ${candidates.filter(c => c.source === 'global' || c.source === 'pearch').length}\n\n💡 *Selecione candidatos para análise detalhada.*`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('score') && (trimmed.includes('médio') || trimmed.includes('media') || trimmed.includes('lia'))) {
    const avgScore = candidates.length > 0 ? Math.round(candidates.reduce((acc, c) => acc + (c.score || c.lia_score || 0), 0) / candidates.length) : 0
    const highScoreCount = candidates.filter(c => (c.score || c.lia_score || 0) >= 70).length
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: candidates.length === 0
        ? `📊 **Nenhum candidato** para calcular score médio.\n\n💡 *Faça uma busca primeiro.*`
        : `📊 **Score LIA médio:** ${formatScorePercent(avgScore)}\n\n• Candidatos com score ≥70%: **${highScoreCount}** (${Math.round(highScoreCount/candidates.length*100)}%)\n• Score máximo: ${formatScorePercent(Math.max(...candidates.map(c => c.score || c.lia_score || 0)))}\n• Score mínimo: ${formatScorePercent(Math.min(...candidates.map(c => c.score || c.lia_score || 0)))}\n\n💡 *Os candidatos de maior score geralmente têm melhor fit com a vaga.*`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('skills') && (trimmed.includes('comuns') || trimmed.includes('mais'))) {
    const allSkills = candidates.flatMap(c => c.skills || c.technical_skills || [])
    const skillCounts = allSkills.reduce((acc, skill) => {
      if (skill && typeof skill === 'string') acc[skill] = (acc[skill] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    const topSkills = Object.entries(skillCounts).sort((a, b) => b[1] - a[1]).slice(0, 10)
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: topSkills.length === 0
        ? `📊 **Nenhuma skill identificada** nos perfis.\n\n💡 *Os candidatos podem não ter skills cadastradas.*`
        : `📊 **Competências Principais mais comuns:**\n\n${topSkills.map(([skill, count], i) => `${i+1}. **${skill}** - ${count} candidato${count > 1 ? 's' : ''}`).join('\n')}\n\n💡 *Use essas competências como filtro para refinar sua busca.*`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('experiência') && trimmed.includes('média')) {
    const withExp = candidates.filter(c => typeof (c.experience ?? c.years_of_experience) === 'number')
    const avgExp = withExp.length > 0 ? (withExp.reduce((acc, c) => acc + (c.experience ?? c.years_of_experience ?? 0), 0) / withExp.length).toFixed(1) : 0
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: withExp.length === 0
        ? `📊 **Experiência não informada** nos perfis.\n\n💡 *Os candidatos podem não ter anos de experiência cadastrados.*`
        : `📊 **Experiência média:** ${avgExp} anos\n\n• Candidatos com experiência informada: ${withExp.length}/${candidates.length}\n• Mais experiente: ${Math.max(...withExp.map(c => c.experience ?? c.years_of_experience ?? 0))} anos\n• Menos experiente: ${Math.min(...withExp.map(c => c.experience ?? c.years_of_experience ?? 0))} anos\n\n💡 *Filtrar por experiência pode refinar seus resultados.*`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('onde estão') || trimmed.includes('localizados') || trimmed.includes('localização')) {
    const locations = candidates.map(c => c.location || c.location_city || c.location_state).filter(Boolean)
    const locationCounts = locations.reduce((acc, loc) => {
      acc[loc as string] = (acc[loc as string] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    const topLocations = Object.entries(locationCounts).sort((a, b) => b[1] - a[1]).slice(0, 8)
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: topLocations.length === 0
        ? `📍 **Localização não informada** nos perfis.\n\n💡 *Os candidatos podem não ter localização cadastrada.*`
        : `📍 **Distribuição por localização:**\n\n${topLocations.map(([loc, count]) => `• **${loc}**: ${count} candidato${count > 1 ? 's' : ''}`).join('\n')}\n\n💡 *${candidates.filter(c => c.is_remote).length} candidatos aceitam trabalho remoto.*`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('nota') && trimmed.includes('acima')) {
    const threshold = 70
    const aboveCount = candidates.filter(c => (c.score || c.lia_score || 0) >= threshold).length
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: `📊 **Candidatos com nota LIA ≥${threshold}%:** ${aboveCount}\n\n• Total de candidatos: ${candidates.length}\n• Porcentagem qualificados: ${candidates.length > 0 ? Math.round(aboveCount/candidates.length*100) : 0}%\n\n💡 *Candidatos acima de 70% geralmente são bons matches.*`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('pontos fortes') && trimmed.includes('comum')) {
    if (selectedIds.size === 0) {
      return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para analisar pontos fortes em comum.`, timestamp: new Date() }
    }
    const selected = candidates.filter(c => selectedIds.has(c.id))
    const allSkills = selected.flatMap(c => c.skills || c.technical_skills || [])
    const skillCounts = allSkills.reduce((acc, s) => { if (s) acc[s] = (acc[s] || 0) + 1; return acc }, {} as Record<string, number>)
    const commonSkills = Object.entries(skillCounts).filter(([_, count]) => count >= Math.ceil(selected.length * 0.5)).map(([skill]) => skill)
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: commonSkills.length === 0
        ? `📊 **Nenhuma skill em comum** encontrada entre os ${selected.length} candidatos selecionados.`
        : `📊 **Pontos fortes em comum** (${selected.length} candidatos):\n\n${commonSkills.slice(0, 8).map(s => `• **${s}**`).join('\n')}\n\n💡 *Essas são as competências compartilhadas pela maioria.*`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('gaps') || trimmed.includes('competência')) {
    if (selectedIds.size === 0) {
      return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para identificar gaps de competência.`, timestamp: new Date() }
    }
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: `🔍 **Análise de Gaps**\n\nPara identificar gaps precisos, preciso conhecer os requisitos da vaga.\n\n💡 **Sugestão:** Selecione uma vaga no seletor acima para comparar candidatos com os requisitos específicos.`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('prioridade') || trimmed.includes('organize')) {
    const sorted = [...candidates].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 10)
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: sorted.length === 0
        ? `📊 **Nenhum candidato** para organizar.\n\n💡 *Faça uma busca primeiro.*`
        : `📊 **Candidatos por prioridade:**\n\n${sorted.map((c, i) => `${i+1}. **${c.name}** - Nota: ${formatScorePercent(c.score || 0)} | ${c.position || c.current_title || 'N/A'}`).join('\n')}\n\n💡 *Ordenados por score de compatibilidade.*`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('melhorar') && trimmed.includes('busca')) {
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: `💡 **Dicas para melhorar sua busca:**\n\n• Adicione **skills específicas** (ex: "Python, AWS")\n• Defina **nível de senioridade** (júnior, pleno, sênior)\n• Especifique **localização** (cidade ou "remoto")\n• Use **palavras-chave** do cargo desejado\n• Tente **termos alternativos** para a mesma função\n\n**Exemplo:** "Desenvolvedor Backend Python sênior São Paulo remoto"`,
      timestamp: new Date()
    }
  }

  if (trimmed.includes('resuma') && trimmed.includes('perfil') && trimmed.includes('selecionado')) {
    if (selectedIds.size === 0) {
      return { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para resumir seus perfis.`, timestamp: new Date() }
    }
    const selected = candidates.filter(c => selectedIds.has(c.id))
    const summary = selected.map(c => `**${c.name}**\n${c.position || c.current_title || 'Profissional'} @ ${c.current_company || 'N/A'}`).join('\n\n')
    return {
      id: `lia-${Date.now()}`,
      type: 'lia',
      content: `📋 **Resumo dos perfis selecionados:**\n\n${summary}\n\n💡 *Para análise detalhada, use "Analisar potencial de crescimento".*`,
      timestamp: new Date()
    }
  }

  return null
}

export function buildDefaultResponse(): LIAChatMessage {
  return {
    id: `lia-${Date.now()}`,
    type: 'lia',
    content: `🤔 Entendi sua solicitação, mas **ainda não consigo responder a esse tipo de pergunta**.\n\nEstou em constante evolução e **em breve serei capaz** de atender você em diversas situações e demandas do seu dia a dia como recrutador!\n\n**Por enquanto, posso ajudar você com:**\n\n📊 **Análises de busca:**\n• Resumir esta busca\n• Top 5 candidatos\n• Skills mais comuns\n• Nota média dos candidatos\n\n👥 **Análise de candidatos selecionados:**\n• Analisar potencial de crescimento\n• Comparar candidatos\n• Pontos fortes em comum\n• Definir tipo de perfil\n\n💡 *Clique em "Mais ideias" para ver todas as opções disponíveis!*`,
    timestamp: new Date()
  }
}
