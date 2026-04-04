import type { DetectedCriteria } from ".."
import {
  commonJobTitles, areaKeywordMap, techSkillsList, softSkillsList,
  idiomasNormalize, nivelNormalize, seniorityMap
} from './criteriaExtractorData'

const ptLetters = 'a-zA-ZáàâãéèêíïóôõöúçÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ'

export function extractCargoFromText(text: string, newCriteria: DetectedCriteria): void {
  for (const title of commonJobTitles) {
    const titlePattern = new RegExp(`\\b${title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?:\\s+(?:s[eê]nior|sr\\.?|pleno|pl\\.?|j[uú]nior|jr\\.?))?\\b`, 'i')
    const match = text.match(titlePattern)
    if (match) {
      newCriteria.cargo = match[0].split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
      return
    }
  }

  const cargoPatterns = [
    new RegExp(`(?:preciso\\s+de\\s+(?:um|uma)?|busco\\s+(?:um|uma)?|contratando|procuro\\s+(?:um|uma)?)\\s+([${ptLetters}\\s]+?)(?:\\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?(?:\\s+(?:para|que|com|\\.|,|$))`, 'i'),
    new RegExp(`vaga\\s+(?:de|para)\\s+([${ptLetters}\\s]+?)(?:\\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?(?:\\s+(?:que|para\\s+a|com\\s+experi[êe]ncia|na|no|em|,|\\.|$))`, 'i'),
    new RegExp(`(?:cargo|posi[çc][aã]o|fun[çc][aã]o)\\s*[:\\-]?\\s*([${ptLetters}\\s]+?)(?:\\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?(?:\\s+(?:que|para|com|,|\\.|$))`, 'i'),
    /\b(desenvolvedor[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|na|no|,|\.|$))/i,
    /\b(analista\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|na|no|,|\.|$))/i,
    /\b(gerente\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
    /\b(coordenador[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
    /\b(diretor[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
    /\b(engenheiro[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|na|no|,|\.|$))/i,
    /\b(especialista\s+(?:em\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|que|para|com|na|no|,|\.|$))/i,
    /\b(arquiteto[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|que|para|com|na|no|,|\.|$))/i,
    /\b(head\s+(?:de\s+|of\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
    /\b(l[ií]der\s+(?:de\s+|t[eé]cnico\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
    /\b(product\s+(?:manager|owner))(?:\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?/i,
    /\b(tech\s+lead(?:er)?)(?:\s+(?:s[eê]nior|sr))?/i,
    /\b(designer\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]*)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|,|\.|$))/i,
    /\b(consultor[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|na|no|,|\.|$))/i,
    /\b(supervisor[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
    /\b(assistente\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
    /\b(auxiliar\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i
  ]

  const stopWords = ['que', 'para', 'com', 'experiência', 'experiencia', 'na', 'no', 'em', 'da', 'do', 'base', 'localizado', 'localizada', 'atuando', 'trabalhar', 'vai', 'será', 'sera', 'deve', 'precisa']

  for (const pattern of cargoPatterns) {
    const match = text.match(pattern)
    if (match) {
      let cargo = match[1] || match[0]
      cargo = cargo.replace(/^(?:vaga\s+(?:de|para)\s+|cargo\s*[:\-]?\s*|posi[çc][aã]o\s*[:\-]?\s*|fun[çc][aã]o\s*[:\-]?\s*|preciso\s+de\s+(?:um|uma)?\s*|busco\s+(?:um|uma)?\s*|contratando\s*|procuro\s+(?:um|uma)?\s*)/i, '')
      const words = cargo.split(/\s+/)
      const cleanWords: string[] = []
      for (const word of words) {
        if (stopWords.includes(word.toLowerCase())) break
        cleanWords.push(word)
      }
      cargo = cleanWords.join(' ').trim()
      if (cargo.length > 2 && cargo.length < 60) {
        newCriteria.cargo = cargo.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ').trim()
        return
      }
    }
  }
}

export function extractAreaFromText(text: string, newCriteria: DetectedCriteria): void {
  const areaPatterns = [
    /\b(?:área|area|departamento|setor)\s*(?:de|do|da)?\s*[:\-]?\s*([a-záàâãéèêíïóôõöúç\s\/]+?)(?:\s*[,.\-]|\s+(?:com|para|que|na|no|em|$))/i,
    /\b(?:time|equipe)\s+(?:de|do|da)\s+([a-záàâãéèêíïóôõöúç\s\/]+?)(?:\s*[,.\-]|\s+(?:com|para|que|$))/i,
    /\bpara\s+(?:o|a)?\s*(?:área|area|departamento|time|equipe)\s+(?:de|do|da)?\s*([a-záàâãéèêíïóôõöúç\s\/]+?)(?:\s*[,.\-]|\s+(?:com|que|$))/i
  ]

  for (const pattern of areaPatterns) {
    const match = text.match(pattern)
    if (match && match[1]) {
      const areaText = match[1].trim().toLowerCase()
      for (const [key, value] of Object.entries(areaKeywordMap)) {
        if (areaText.includes(key)) {
          newCriteria.departamento = value
          break
        }
      }
      if (newCriteria.departamento) break
      if (areaText.length > 1 && areaText.length < 40) {
        newCriteria.departamento = match[1].trim().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
        break
      }
    }
  }

  if (!newCriteria.departamento && newCriteria.cargo) {
    const cargoLower = newCriteria.cargo.toLowerCase()
    for (const [key, value] of Object.entries(areaKeywordMap)) {
      if (cargoLower.includes(key)) {
        newCriteria.departamento = value
        break
      }
    }
  }
}

export function extractGestorFromText(text: string, newCriteria: DetectedCriteria): void {
  const gestorPatterns = [
    new RegExp(`gestor(?:a)?[:\\s]+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    new RegExp(`(?:área|area|departamento|setor)[:\\s]+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    new RegExp(`gestor(?:a)?[:\\s]+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})(?:\\/|$)`, 'i'),
    new RegExp(`reporta(?:r[áa])?\\s+(?:para|ao?|diretamente\\s+ao?)\\s+(?:o\\s+|a\\s+)?([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    new RegExp(`equipe\\s+d[oa]\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,2})`, 'i'),
    new RegExp(`time\\s+d[oa]\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,2})`, 'i'),
    new RegExp(`(?:sob\\s+)?(?:supervisão|liderança|gestão)\\s+(?:do?a?\\s+)?([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,2})`, 'i'),
    new RegExp(`gestor(?:a)?\\s+de\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    new RegExp(`(?:área|departamento|setor)\\s+de\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    new RegExp(`gestão\\s+de\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
  ]

  const invalidGestorTerms = ['de', 'da', 'do', 'para', 'com', 'nivel', 'nível', 'senior', 'sênior', 'pleno', 'junior', 'júnior', 'vagas', 'vaga', 'posição', 'posicao', 'cargo', 'responsabilidades']

  for (const pattern of gestorPatterns) {
    const match = text.match(pattern)
    if (match && match[1]) {
      const name = match[1].trim()
      const firstWord = name.split(' ')[0].toLowerCase()
      if (name.length > 2 && !invalidGestorTerms.includes(firstWord)) {
        newCriteria.gestorArea = name.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
        break
      }
    }
  }
}

export function extractSkillsFromText(text: string, lowerText: string, newCriteria: DetectedCriteria): void {
  const foundTechSkills: string[] = []
  techSkillsList.forEach(skill => {
    const skillPattern = new RegExp(`\\b${skill.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
    if (skillPattern.test(lowerText)) {
      foundTechSkills.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
    }
  })

  const explicitSkillsPatterns = [
    /compet[êe]ncias?\s+t[ée]cnicas?\s*[:\-]\s*([^.]+)/i,
    /skills?\s+t[ée]cnic[oa]s?\s*[:\-]\s*([^.]+)/i,
    /requisitos?\s+t[ée]cnicos?\s*[:\-]\s*([^.]+)/i,
    /conhecimentos?\s*[:\-]\s*([^.]+)/i
  ]

  for (const pattern of explicitSkillsPatterns) {
    const match = text.match(pattern)
    if (match && match[1]) {
      const skillsList = match[1].split(/[,;e]/).map(s => s.trim()).filter(s => s.length > 1)
      skillsList.forEach(skill => {
        if (skill && skill.length > 1 && !['e', 'ou', 'com', 'de', 'para'].includes(skill.toLowerCase())) {
          foundTechSkills.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' '))
        }
      })
    }
  }

  if (foundTechSkills.length > 0) {
    const existingLower = new Set((newCriteria.competenciasTecnicas || []).map(s => s.toLowerCase()))
    const uniqueNewSkills = foundTechSkills.filter(s => !existingLower.has(s.toLowerCase()))
    newCriteria.competenciasTecnicas = [...(newCriteria.competenciasTecnicas || []), ...uniqueNewSkills]
  }

  const foundSoftSkills: string[] = []
  softSkillsList.forEach(skill => {
    if (lowerText.includes(skill)) {
      foundSoftSkills.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
    }
  })
  if (foundSoftSkills.length > 0) {
    const existingLower = new Set((newCriteria.competenciasComportamentais || []).map(s => s.toLowerCase()))
    const uniqueNewComps = foundSoftSkills.filter(s => !existingLower.has(s.toLowerCase()))
    newCriteria.competenciasComportamentais = [...(newCriteria.competenciasComportamentais || []), ...uniqueNewComps]
  }
}

export function extractIdiomasFromText(text: string, newCriteria: DetectedCriteria): void {
  const idiomasPatterns = [
    /\b(ingl[eê]s|english)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(espanhol|spanish)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(franc[eê]s|french)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(alem[aã]o|german)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(italiano|italian)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(portugu[eê]s|portuguese)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(mandarim|chin[eê]s|chinese)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(japon[eê]s|japanese)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)\s+(?:em\s+)?(ingl[eê]s|espanhol|franc[eê]s|alem[aã]o|italiano|mandarim|chin[eê]s|japon[eê]s)/gi,
    /\b(ingl[eê]s|espanhol|franc[eê]s|alem[aã]o|italiano|mandarim|chin[eê]s|japon[eê]s)\s+(?:n[ií]vel\s+)?(C1|C2|B1|B2|A1|A2)/gi,
  ]

  const foundIdiomas: string[] = []
  for (const pattern of idiomasPatterns) {
    const regex = new RegExp(pattern.source, pattern.flags)
    let match
    while ((match = regex.exec(text)) !== null) {
      const idioma = idiomasNormalize[match[1].toLowerCase()] || match[1]
      const nivel = nivelNormalize[match[2]?.toLowerCase()] || match[2] || ''
      const formatted = nivel ? `${idioma} ${nivel}` : idioma
      if (!foundIdiomas.some(i => i.toLowerCase() === formatted.toLowerCase())) {
        foundIdiomas.push(formatted)
      }
    }
  }

  if (foundIdiomas.length > 0) {
    newCriteria.idiomas = [...new Set([...newCriteria.idiomas, ...foundIdiomas])]
  }
}

export function extractSeniorityFromText(text: string, newCriteria: DetectedCriteria): void {
  const seniorityMatch = text.match(/\b(júnior|junior|jr|pleno|pl|sênior|senior|sr|especialista|trainee|estagiário|estagiario|estágio|estagio)\b/i)
  if (seniorityMatch) {
    const seniority = seniorityMatch[1].toLowerCase()
    newCriteria.senioridadeIdiomas = seniorityMap[seniority] || seniority.charAt(0).toUpperCase() + seniority.slice(1)
  }
}

export function extractWorkModelFromText(text: string, newCriteria: DetectedCriteria): void {
  const modeloMatch = text.match(/\b(remoto|100%\s*remoto|totalmente\s*remoto|híbrido|hibrido|presencial|home\s*office|trabalho\s*remoto)\b/i)
  if (modeloMatch) {
    const modelo = modeloMatch[1].toLowerCase()
    if (modelo.includes('remoto') || modelo.includes('home')) {
      newCriteria.modeloTrabalho = 'Remoto'
    } else if (modelo.includes('híbrido') || modelo.includes('hibrido')) {
      newCriteria.modeloTrabalho = 'Híbrido'
    } else if (modelo.includes('presencial')) {
      newCriteria.modeloTrabalho = 'Presencial'
    }
  }
}
