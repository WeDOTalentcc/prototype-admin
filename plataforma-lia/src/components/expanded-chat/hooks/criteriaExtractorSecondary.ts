import { formatBRL } from "@/lib/pricing"
import type { DetectedCriteria } from ".."
import {
  knownCities, stateAbbrev, knownCertifications, knownTools, beneficiosKeywords
} from './criteriaExtractorData'

export function extractLocationFromText(text: string, lowerText: string, newCriteria: DetectedCriteria): void {
  for (const [cityKey, cityFormatted] of Object.entries(knownCities)) {
    const cityPattern = new RegExp(`\\b${cityKey.replace(/\s+/g, '\\s+')}\\b`, 'i')
    if (cityPattern.test(lowerText)) {
      newCriteria.localizacao = cityFormatted
      return
    }
  }

  const locationPatterns = [
    /(?:base\s+(?:em|no|na)\s+)([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,\-]\s*([A-Z]{2}))?(?:\s*[,.;]|\s+(?:modelo|remoto|híbrido|presencial)|$)/i,
    /(?:localização|localizacao|cidade|local)\s*[:\-]?\s*([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,\-]\s*([A-Z]{2}))?(?:\s*[,.;]|$)/i,
    /\b([A-Z][a-záàâãéèêíïóôõöúç]+(?:\s+[A-Z]?[a-záàâãéèêíïóôõöúç]+)*)\s*[,\-]\s*([A-Z]{2})\b/
  ]

  for (const pattern of locationPatterns) {
    const match = text.match(pattern)
    if (match && match[1]) {
      let location = match[1].trim()
      const state = match[2]?.toUpperCase()

      const commonWords = ['empresa', 'vaga', 'equipe', 'time', 'área', 'area', 'modelo', 'trabalho', 'contrato', 'salário', 'salario']
      if (commonWords.some(w => location.toLowerCase().includes(w))) continue

      if (stateAbbrev[location.toLowerCase()]) {
        location = stateAbbrev[location.toLowerCase()]
      } else {
        location = location.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
        if (state) {
          location = `${location}, ${state}`
        }
      }

      if (location.length > 2 && location.length < 50) {
        newCriteria.localizacao = location
        return
      }
    }
  }
}

export function extractContractFromText(text: string, newCriteria: DetectedCriteria): void {
  const contratoMatch = text.match(/\b(clt|pj|pessoa\s*jurídica|pessoa\s*juridica|terceirizado|freelancer|temporário|temporario|efetivo|contrato\s*fixo|contratação\s*clt|contratacao\s*clt)\b/i)
  if (contratoMatch) {
    const contrato = contratoMatch[1].toLowerCase()
    if (contrato.includes('clt') || contrato.includes('efetivo')) {
      newCriteria.tipoContrato = 'CLT'
    } else if (contrato.includes('pj') || contrato.includes('jurídica') || contrato.includes('juridica')) {
      newCriteria.tipoContrato = 'PJ'
    } else if (contrato.includes('temporário') || contrato.includes('temporario')) {
      newCriteria.tipoContrato = 'Temporário'
    } else if (contrato.includes('freelancer')) {
      newCriteria.tipoContrato = 'Freelancer'
    } else if (contrato.includes('terceirizado')) {
      newCriteria.tipoContrato = 'Terceirizado'
    }
  }
}

export function extractResponsibilitiesFromText(text: string, newCriteria: DetectedCriteria): void {
  const responsibilityPatterns = [
    /(?:vai\s+ser|será|serás?|sendo|é|era|foi)\s+respons[áa]vel\s+por\s+([^.!?]+)/i,
    /respons[áa]vel\s+por\s*[:\-]?\s*([^.!?]+)/i,
    /responsabilidades?\s+como\s+([^.!?]+)/i,
    /responsabilidades?\s*[:\-]\s*([^.!?]+)/i,
    /(?:principais\s+)?atribui[çc][õo]es?\s*[:\-]\s*([^.!?]+)/i,
    /atividades?\s*[:\-]\s*([^.!?]+)/i,
    /vai\s+(liderar|gerenciar|coordenar|supervisionar|desenvolver|implementar|criar|construir|mentorar|treinar)\s+([^.!?]+)/i,
    /ir[áa]\s+(liderar|gerenciar|coordenar|supervisionar|desenvolver|implementar|criar|construir|mentorar|treinar|gerir)\s+([^.!?]+)/i,
    /al[ée]m\s+(?:de|da|do|das|dos)\s+([^.!?,]+)/i,
  ]

  const foundResponsibilities: string[] = []
  for (const pattern of responsibilityPatterns) {
    const match = text.match(pattern)
    if (match) {
      const matchedText = match[1] || match[2] || ''
      const items = matchedText.split(/[,;]|\s+e\s+/).map(s => s.trim()).filter(s => {
        if (s.length < 3) return false
        const stopWords = ['o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'para', 'com', 'por']
        return !stopWords.includes(s.toLowerCase())
      })
      items.forEach(item => {
        if (item.length > 3 && item.length < 100) {
          const formatted = item.charAt(0).toUpperCase() + item.slice(1).toLowerCase()
          if (!foundResponsibilities.includes(formatted)) {
            foundResponsibilities.push(formatted)
          }
        }
      })
    }
  }
  if (foundResponsibilities.length > 0) {
    const existingNotPartial = newCriteria.responsabilidades.filter(existing => {
      return !foundResponsibilities.some(newResp =>
        newResp.toLowerCase().startsWith(existing.toLowerCase()) ||
        existing.toLowerCase().startsWith(newResp.toLowerCase())
      )
    })
    newCriteria.responsabilidades = [...new Set([...existingNotPartial, ...foundResponsibilities])]
  }
}

export function extractSalaryFromText(text: string, lowerText: string, newCriteria: DetectedCriteria): void {
  const parseSalaryValue = (value: string): number | null => {
    if (!value) return null
    let cleaned = value.toLowerCase().trim()

    let multiplier = 1
    if (cleaned.includes('k')) {
      multiplier = 1000
      cleaned = cleaned.replace(/k/gi, '')
    } else if (cleaned.includes('mil')) {
      multiplier = 1000
      cleaned = cleaned.replace(/mil/gi, '')
    }

    cleaned = cleaned.replace(/[^\d.,]/g, '')
    cleaned = cleaned.replace(/\./g, '').replace(',', '.')

    const num = parseFloat(cleaned)
    if (isNaN(num)) return null

    return Math.round(num * multiplier)
  }

  const salarioPatterns = [
    /sal[áa]rio\s+entre\s+([\d.,]+)\s*(?:mil)?\s*(?:reais?)?\s*(?:e|a|até|-)\s*([\d.,]+)\s*(?:mil|k)?\s*(?:reais?)?/i,
    /entre\s+([\d.,]+)\s*(?:mil)?\s*(?:reais?)?\s*(?:e|a|até|-)\s*([\d.,]+)\s*(?:mil|k)\s*(?:reais?)?/i,
    /(?:de\s+)?([\d.,]+)\s*(?:a|até|-)\s*([\d.,]+)\s*(?:mil|k)\s*(?:reais?)?/i,
    /sal[áa]rio\s*(?:de)?\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)\s*(?:a|até|-)\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
    /(?:r\$)\s*([\d.,]+\s*(?:k|mil)?)\s*(?:a|até|-)\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
    /faixa\s*(?:salarial)?\s*(?:de)?\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)\s*(?:a|até|-)\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
    /remunera[çc][ãa]o\s*(?:de)?\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)\s*(?:a|até|-)\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
    /([\d]{1,3}(?:[.,][\d]{3})*)\s*(?:a|até|-)\s*([\d]{1,3}(?:[.,][\d]{3})*)/i,
    /sal[áa]rio\s*(?:de)?\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
    /(?:r\$)\s*([\d.,]+\s*(?:k|mil)?)/i
  ]

  for (const pattern of salarioPatterns) {
    const match = text.match(pattern)
    if (match) {
      let minValue = parseSalaryValue(match[1])
      let maxValue = match[2] ? parseSalaryValue(match[2]) : null

      if (minValue && maxValue && minValue < 100 && maxValue >= 1000) {
        minValue = minValue * 1000
      }
      if (minValue && minValue < 100 && (lowerText.includes('mil') || lowerText.includes('k '))) {
        minValue = minValue * 1000
      }
      if (maxValue && maxValue < 100 && (lowerText.includes('mil') || lowerText.includes('k '))) {
        maxValue = maxValue * 1000
      }

      if (minValue && minValue >= 1000) {
        if (maxValue && maxValue >= minValue) {
          newCriteria.salario = `${formatBRL(minValue)} - ${formatBRL(maxValue)}`
        } else {
          newCriteria.salario = `${formatBRL(minValue)}`
        }
        break
      }
    }
  }
}

export function extractAffirmativeFromText(text: string, newCriteria: DetectedCriteria): void {
  const affirmativePatterns = [
    /(?:n[aã]o\s+[eé]\s+(?:uma?\s+)?(?:vaga\s+)?afirmativa|vaga\s+n[aã]o\s+afirmativa|n[aã]o\s+afirmativa)/i,
    /(?:[eé]\s+(?:uma?\s+)?(?:vaga\s+)?afirmativa|vaga\s+afirmativa|exclusiva\s+para)/i,
  ]

  const negativeAffirmativeMatch = text.match(affirmativePatterns[0])
  if (negativeAffirmativeMatch) {
    newCriteria.isAffirmative = false
  } else {
    const positiveAffirmativeMatch = text.match(affirmativePatterns[1])
    if (positiveAffirmativeMatch) {
      newCriteria.isAffirmative = true
    }
  }

  const affirmativeCriteriaPatterns = [
    /(?:exclusiv[oa]\s+para|voltad[oa]\s+para|destinad[oa]\s+(?:a|para))\s+(mulheres?|pcd|pessoas?\s+com\s+defici[êe]ncia|negr[oa]s?|lgbtq?\+?|50\+|idosos?|trans)/gi,
    /(?:vaga\s+)?(?:afirmativa|exclusiva)\s+(?:para\s+)?(mulheres?|pcd|pessoas?\s+com\s+defici[êe]ncia|negr[oa]s?|lgbtq?\+?|50\+|idosos?|trans)/gi,
  ]
  for (const pattern of affirmativeCriteriaPatterns) {
    const matches = text.matchAll(pattern)
    for (const match of matches) {
      if (match[1]) {
        const criterio = match[1].toLowerCase()
        if (criterio.includes('mulher')) {
          newCriteria.affirmativeCriteriaPrimary = newCriteria.affirmativeCriteriaPrimary || 'Mulheres'
        } else if (criterio.includes('pcd') || criterio.includes('defici')) {
          if (!newCriteria.affirmativeCriteriaPrimary) newCriteria.affirmativeCriteriaPrimary = 'PCD'
          else newCriteria.affirmativeCriteriaSecondary = 'PCD'
        } else if (criterio.includes('negr')) {
          if (!newCriteria.affirmativeCriteriaPrimary) newCriteria.affirmativeCriteriaPrimary = 'Pessoas Negras'
          else newCriteria.affirmativeCriteriaSecondary = 'Pessoas Negras'
        } else if (criterio.includes('lgbtq') || criterio.includes('trans')) {
          if (!newCriteria.affirmativeCriteriaPrimary) newCriteria.affirmativeCriteriaPrimary = 'LGBTQ+'
          else newCriteria.affirmativeCriteriaSecondary = 'LGBTQ+'
        } else if (criterio.includes('50') || criterio.includes('idoso')) {
          if (!newCriteria.affirmativeCriteriaPrimary) newCriteria.affirmativeCriteriaPrimary = '50+'
          else newCriteria.affirmativeCriteriaSecondary = '50+'
        }
        newCriteria.isAffirmative = true
      }
    }
  }
}

export function extractExperienceFromText(text: string, newCriteria: DetectedCriteria): void {
  const experienciaPatterns = [
    /(\d+)\s*(?:\+\s*)?anos?\s+(?:de\s+)?experi[êe]ncia/i,
    /experi[êe]ncia\s+(?:m[íi]nima\s+)?(?:de\s+)?(\d+)\s*(?:\+\s*)?anos?/i,
    /m[íi]nimo\s+(?:de\s+)?(\d+)\s*(?:\+\s*)?anos?\s+(?:de\s+)?experi[êe]ncia/i,
    /(?:pelo\s+menos|no\s+m[íi]nimo)\s+(\d+)\s*anos?\s+(?:de\s+)?experi[êe]ncia/i,
  ]
  for (const pattern of experienciaPatterns) {
    const match = text.match(pattern)
    if (match && match[1]) {
      newCriteria.experienciaMinima = `${match[1]} anos`
      break
    }
  }
}

export function extractFormacaoFromText(text: string, newCriteria: DetectedCriteria): void {
  const formacaoPatterns = [
    /(?:gradua[çc][ãa]o|graduado|bacharelado|bacharel|licenciatura|tecnólogo|tecnologo)\s+em\s+([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-;]|\s+(?:ou|e|com|$))/gi,
    /(?:forma[çc][ãa]o)\s+em\s+([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-;]|\s+(?:ou|e|com|$))/gi,
    /(?:p[óo]s[- ]?gradua[çc][ãa]o|mba|mestrado|doutorado|especializa[çc][ãa]o)\s+em\s+([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-;]|\s+(?:ou|e|com|$))/gi,
    /\b(ensino\s+(?:superior|m[ée]dio|t[ée]cnico)(?:\s+completo)?)\b/gi,
    /\b(curso\s+(?:superior|t[ée]cnico)\s+em\s+[a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-;]|$)/gi,
  ]
  const invalidFormacaoTerms = ['nivel', 'nível', 'senior', 'sênior', 'pleno', 'junior', 'júnior', 'de', 'da', 'do']
  const foundFormacao: string[] = []
  for (const pattern of formacaoPatterns) {
    const regex = new RegExp(pattern.source, pattern.flags)
    let match
    while ((match = regex.exec(text)) !== null) {
      const formacao = (match[1] || match[0]).trim()
      const firstWord = formacao.split(' ')[0].toLowerCase()
      if (formacao.length > 3 && formacao.length < 60 && !invalidFormacaoTerms.includes(firstWord)) {
        foundFormacao.push(formacao.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' '))
      }
    }
  }
  if (foundFormacao.length > 0) {
    newCriteria.formacao = [...new Set([...newCriteria.formacao, ...foundFormacao])]
  }
}

export function extractCertificacoesFromText(text: string, lowerText: string, newCriteria: DetectedCriteria): void {
  const certificacoesPatterns = [
    /certifica[çc][ãa]o\s+(?:em\s+)?([a-záàâãéèêíïóôõöúç\s\-]+?)(?:\s*[,.\-;]|\s+(?:ou|e|$))/gi,
    /certificado\s+(?:em\s+|de\s+)?([a-záàâãéèêíïóôõöúç\s\-]+?)(?:\s*[,.\-;]|\s+(?:ou|e|$))/gi,
  ]
  const foundCertificacoes: string[] = []
  knownCertifications.forEach(cert => {
    const certPattern = new RegExp(`\\b${cert.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
    if (certPattern.test(lowerText)) {
      foundCertificacoes.push(cert.toUpperCase())
    }
  })
  for (const pattern of certificacoesPatterns) {
    const regex = new RegExp(pattern.source, pattern.flags)
    let match
    while ((match = regex.exec(text)) !== null) {
      if (match[1] && match[1].length > 2 && match[1].length < 40) {
        foundCertificacoes.push(match[1].trim())
      }
    }
  }
  if (foundCertificacoes.length > 0) {
    newCriteria.certificacoes = [...new Set([...newCriteria.certificacoes, ...foundCertificacoes])]
  }
}

export function extractFerramentasFromText(lowerText: string, newCriteria: DetectedCriteria): void {
  const foundFerramentas: string[] = []
  knownTools.forEach(tool => {
    const toolPattern = new RegExp(`\\b${tool.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
    if (toolPattern.test(lowerText)) {
      foundFerramentas.push(tool.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
    }
  })
  if (foundFerramentas.length > 0) {
    newCriteria.ferramentas = [...new Set([...newCriteria.ferramentas, ...foundFerramentas])]
  }
}

export function extractHybridDaysFromText(text: string, newCriteria: DetectedCriteria): void {
  if (newCriteria.modeloTrabalho !== 'Híbrido') return
  const diasPatterns = [
    /(\d+)\s*(?:dias?\s+)?(?:por\s+semana\s+)?(?:no\s+)?(?:escrit[óo]rio|presencial)/i,
    /(\d+)x\s*(?:por\s+)?semana\s*(?:no\s+)?(?:escrit[óo]rio|presencial)?/i,
    /presencial\s+(\d+)\s*(?:dias?\s+)?(?:por\s+)?semana/i,
    /(\d+)\s*dias?\s+presenciais?/i,
  ]
  for (const pattern of diasPatterns) {
    const match = text.match(pattern)
    if (match && match[1]) {
      const dias = parseInt(match[1])
      if (dias >= 1 && dias <= 5) {
        newCriteria.diasPresenciais = dias
        break
      }
    }
  }
}

export function extractBeneficiosFromText(text: string, newCriteria: DetectedCriteria): void {
  const foundBeneficios: string[] = []
  beneficiosKeywords.forEach(({ pattern, name }) => {
    if (pattern.test(text)) {
      foundBeneficios.push(name)
    }
  })
  if (foundBeneficios.length > 0) {
    newCriteria.beneficiosMencionados = [...new Set([...newCriteria.beneficiosMencionados, ...foundBeneficios])]
  }
}

export function extractBonusFromText(text: string, newCriteria: DetectedCriteria): void {
  const bonusPatterns = [
    /b[ôo]nus\s+(?:de\s+)?(?:at[ée]\s+)?(\d+)\s*(?:sal[áa]rios?)?/i,
    /b[ôo]nus\s+(?:de\s+)?(?:r\$\s*)?([\d.,]+\s*(?:k|mil)?)/i,
    /plr\s+(?:de\s+)?(?:at[ée]\s+)?(\d+)\s*sal[áa]rios?/i,
    /(\d+)\s*sal[áa]rios?\s+(?:de\s+)?b[ôo]nus/i,
  ]
  for (const pattern of bonusPatterns) {
    const match = text.match(pattern)
    if (match && match[1]) {
      newCriteria.bonus = match[0].trim()
      break
    }
  }
}

export function extractViagensFromText(text: string, newCriteria: DetectedCriteria): void {
  const viagensPatterns = [
    /viagens?\s+frequentes?/i,
    /disponibilidade\s+para\s+viag(?:ar|ens?)/i,
    /(?:requer|exige|necessita)\s+viagens?/i,
    /viagens?\s+(?:a\s+)?(?:trabalho|nacionais?|internacionais?)/i,
  ]
  for (const pattern of viagensPatterns) {
    if (pattern.test(text)) {
      newCriteria.viagensFrequentes = true
      break
    }
  }
}

export function extractDisponibilidadeFromText(text: string, newCriteria: DetectedCriteria): void {
  const disponibilidadePatterns = [
    /in[íi]cio\s+imediato/i,
    /dispon[íi]vel\s+(?:para\s+)?(?:come[çc]ar\s+)?imediatamente/i,
    /come[çc]ar\s+(?:em\s+)?(?:at[ée]\s+)?(\d+)\s*dias?/i,
    /in[íi]cio\s+(?:em\s+|para\s+)?([a-záàâãéèêíïóôõöúç]+(?:\s+de\s+\d{4})?)/i,
    /a\s+partir\s+de\s+([a-záàâãéèêíïóôõöúç]+)/i,
  ]
  for (const pattern of disponibilidadePatterns) {
    const match = text.match(pattern)
    if (match) {
      if (match[0].toLowerCase().includes('imediato') || match[0].toLowerCase().includes('imediatamente')) {
        newCriteria.disponibilidade = 'Imediato'
      } else if (match[1]) {
        newCriteria.disponibilidade = match[1].charAt(0).toUpperCase() + match[1].slice(1)
      }
      break
    }
  }
}

export function extractCNHFromText(text: string, newCriteria: DetectedCriteria): void {
  const cnhPatterns = [
    /cnh\s*(?:categoria\s+)?([A-E](?:\s*[,\/e]\s*[A-E])*)/i,
    /habilita[çc][ãa]o\s*(?:categoria\s+)?([A-E](?:\s*[,\/e]\s*[A-E])*)/i,
    /carteira\s+(?:de\s+)?habilita[çc][ãa]o\s*(?:categoria\s+)?([A-E](?:\s*[,\/e]\s*[A-E])*)?/i,
    /\bcnh\s+([A-E])\b/i,
    /\bcnh\b/i,
  ]
  for (const pattern of cnhPatterns) {
    const match = text.match(pattern)
    if (match) {
      if (match[1]) {
        newCriteria.cnh = `CNH ${match[1].toUpperCase()}`
      } else {
        newCriteria.cnh = 'CNH (categoria não especificada)'
      }
      break
    }
  }
}

export function extractHorarioFromText(text: string, newCriteria: DetectedCriteria): void {
  const horarioPatterns = [
    /hor[áa]rio\s+flex[íi]vel/i,
    /jornada\s+flex[íi]vel/i,
    /turno\s+(noturno|diurno|matutino|vespertino)/i,
    /(\d{1,2})[h:]\s*(?:[àa]s?\s*)?(\d{1,2})h?/i,
    /das\s+(\d{1,2})h?\s+[àa]s?\s+(\d{1,2})h?/i,
    /hor[áa]rio\s+comercial/i,
  ]
  for (const pattern of horarioPatterns) {
    const match = text.match(pattern)
    if (match) {
      if (match[0].toLowerCase().includes('flex')) {
        newCriteria.horario = 'Flexível'
      } else if (match[0].toLowerCase().includes('comercial')) {
        newCriteria.horario = 'Comercial'
      } else if (match[1] && match[2]) {
        newCriteria.horario = `${match[1]}h às ${match[2]}h`
      } else if (match[1]) {
        newCriteria.horario = `Turno ${match[1].charAt(0).toUpperCase() + match[1].slice(1)}`
      }
      break
    }
  }
}
