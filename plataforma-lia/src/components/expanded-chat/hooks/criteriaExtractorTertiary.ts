import type { DetectedCriteria } from ".."
import { beneficiosKeywords } from './criteriaExtractorData'

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
