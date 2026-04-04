"use client"

import type { DetectedCriteria } from "../ExpandedChatContext"

export function generateCriteriaResponse(criteria: DetectedCriteria): string {
  const detected: string[] = []
  const missing: string[] = []

  if (criteria.cargo) detected.push(`**Cargo**: ${criteria.cargo}`)
  else missing.push('cargo')

  if (criteria.gestorArea) detected.push(`**Gestor**: ${criteria.gestorArea}`)

  if (criteria.responsabilidades.length > 0) {
    detected.push(`**Responsabilidades**: ${criteria.responsabilidades.slice(0, 4).join(', ')}${criteria.responsabilidades.length > 4 ? ` (+${criteria.responsabilidades.length - 4})` : ''}`)
  }

  if (criteria.competenciasTecnicas.length > 0) {
    detected.push(`**Skills técnicos**: ${criteria.competenciasTecnicas.slice(0, 5).join(', ')}${criteria.competenciasTecnicas.length > 5 ? ` (+${criteria.competenciasTecnicas.length - 5})` : ''}`)
  } else {
    missing.push('competências técnicas')
  }

  if (criteria.competenciasComportamentais.length > 0) {
    detected.push(`**Competências comportamentais**: ${criteria.competenciasComportamentais.slice(0, 3).join(', ')}`)
  }

  if (criteria.idiomas && criteria.idiomas.length > 0) {
    detected.push(`**Idiomas**: ${criteria.idiomas.join(', ')}`)
  }

  if (criteria.senioridadeIdiomas) detected.push(`**Senioridade**: ${criteria.senioridadeIdiomas}`)
  else missing.push('senioridade')

  if (criteria.modeloTrabalho) {
    let modeloText = `**Modelo**: ${criteria.modeloTrabalho}`
    if (criteria.diasPresenciais) {
      modeloText += ` (${criteria.diasPresenciais}x por semana no escritório)`
    }
    detected.push(modeloText)
  }
  if (criteria.localizacao) detected.push(`**Local**: ${criteria.localizacao}`)
  if (criteria.tipoContrato) detected.push(`**Contrato**: ${criteria.tipoContrato}`)
  if (criteria.salario) detected.push(`**Salário**: ${criteria.salario}`)
  if (criteria.bonus) detected.push(`**Bônus**: ${criteria.bonus}`)
  if (criteria.isAffirmative !== null) {
    let affirmText = `**Vaga Afirmativa**: ${criteria.isAffirmative ? 'Sim' : 'Não'}`
    if (criteria.affirmativeCriteriaPrimary) {
      affirmText += ` (${criteria.affirmativeCriteriaPrimary}${criteria.affirmativeCriteriaSecondary ? `, ${criteria.affirmativeCriteriaSecondary}` : ''})`
    }
    detected.push(affirmText)
  }

  if (criteria.experienciaMinima) detected.push(`**Experiência**: ${criteria.experienciaMinima}`)
  if (criteria.formacao && criteria.formacao.length > 0) {
    detected.push(`**Formação**: ${criteria.formacao.join(', ')}`)
  }
  if (criteria.certificacoes && criteria.certificacoes.length > 0) {
    detected.push(`**Certificações**: ${criteria.certificacoes.join(', ')}`)
  }
  if (criteria.ferramentas && criteria.ferramentas.length > 0) {
    detected.push(`**Ferramentas**: ${criteria.ferramentas.slice(0, 5).join(', ')}${criteria.ferramentas.length > 5 ? ` (+${criteria.ferramentas.length - 5})` : ''}`)
  }
  if (criteria.beneficiosMencionados && criteria.beneficiosMencionados.length > 0) {
    detected.push(`**Benefícios**: ${criteria.beneficiosMencionados.slice(0, 4).join(', ')}${criteria.beneficiosMencionados.length > 4 ? ` (+${criteria.beneficiosMencionados.length - 4})` : ''}`)
  }
  if (criteria.viagensFrequentes) detected.push(`**Viagens**: Sim`)
  if (criteria.disponibilidade) detected.push(`**Início**: ${criteria.disponibilidade}`)
  if (criteria.cnh) detected.push(`**CNH**: ${criteria.cnh}`)
  if (criteria.horario) detected.push(`**Horário**: ${criteria.horario}`)

  let response = ''

  if (detected.length > 0) {
    response = `Detectei os seguintes critérios:\n\n${detected.map(d => `- ${d}`).join('\n')}`

    if (missing.length > 0 && missing.length <= 2) {
      response += `\n\nPara completar, informe: **${missing.join('** e **')}**.`
    } else if (detected.length >= 3) {
      response += `\n\nÓtimo progresso! Você pode adicionar mais detalhes para enriquecer a vaga.`
    }
  } else {
    response = 'Não consegui detectar critérios específicos. Tente descrever o cargo, senioridade, skills técnicos e modelo de trabalho.'
  }

  return response
}

export function generateCompetencyAnalysisMessage(
  cargo: string | null,
  area: string | null,
  criteria: DetectedCriteria,
  deduplicatedSkills?: string[]
): string {
  const role = cargo || 'profissional'

  let message = `**Análise de Competências para ${role}**\n\n`
  message += `Com base nas informações da vaga e dados de mercado, preparei sugestões de competências:\n\n`

  if (criteria.competenciasTecnicas.length > 0) {
    message += `**Competências Técnicas Identificadas:**\n`
    criteria.competenciasTecnicas.slice(0, 5).forEach(skill => {
      message += `• ${skill}\n`
    })
    message += `\n`
  }

  if (criteria.competenciasComportamentais.length > 0) {
    message += `**Competências Comportamentais Sugeridas:**\n`
    criteria.competenciasComportamentais.slice(0, 4).forEach(comp => {
      message += `• ${comp}\n`
    })
    message += `\n`
  }

  message += `📊 *Fontes: histórico de vagas similares + dados de mercado*\n\n`
  message += `Me informe aqui no chat se deseja adicionar, remover ou alterar os pesos das competências.`

  return message
}

export function generateWSIExplanationMessage(
  technicalSkillsList: string[],
  behavioralCompetenciesList: string[],
  cargo: string | null
): string {
  const role = cargo || 'a vaga'
  const totalCompetencies = technicalSkillsList.length + behavioralCompetenciesList.length

  let message = `**Gerando Perguntas de Triagem WSI**\n\n`
  message += `Vou criar perguntas baseadas na metodologia WSI (Work Sample Interview), que combina:\n\n`
  message += `• **Taxonomia de Bloom** - níveis cognitivos\n`
  message += `• **Modelo Dreyfus** - proficiência técnica\n`
  message += `• **Big Five** - traços comportamentais\n\n`

  message += `Considerando as ${totalCompetencies} competências definidas para ${role}, `
  message += `as perguntas avaliarão tanto habilidades técnicas quanto comportamentais.\n\n`

  message += `⏳ *Aguarde enquanto gero as perguntas personalizadas...*`

  return message
}
