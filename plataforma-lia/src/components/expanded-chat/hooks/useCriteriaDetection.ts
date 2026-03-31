// @ts-nocheck
"use client"

import { useCallback } from "react"
import type { DetectedCriteria } from '../ExpandedChatContext'

export interface UseCriteriaDetectionReturn {
  extractCriteriaFromText: (text: string, currentCriteria: DetectedCriteria, setCriteria: (criteria: DetectedCriteria) => void) => DetectedCriteria
}

export function useCriteriaDetection(): UseCriteriaDetectionReturn {
  const extractCriteriaFromText = useCallback((text: string, detectedCriteria: DetectedCriteria, setDetectedCriteria: (criteria: DetectedCriteria) => void): DetectedCriteria => {
    const lowerText = text.toLowerCase()
    const newCriteria = { ...detectedCriteria }

    const ptLetters = 'a-zA-ZáàâãéèêíïóôõöúçÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ'

    const commonJobTitles = [
      'analista contábil', 'analista contabil', 'analista fiscal', 'analista financeiro', 'analista financeira',
      'analista de rh', 'analista de recursos humanos', 'analista de dp', 'analista de departamento pessoal',
      'analista de sistemas', 'analista de dados', 'analista de bi', 'analista de negócios', 'analista de negocios',
      'analista de marketing', 'analista de vendas', 'analista comercial', 'analista tributário', 'analista tributario',
      'analista de compras', 'analista de suprimentos', 'analista de logística', 'analista de logistica',
      'analista de qualidade', 'analista de processos', 'analista de projetos', 'analista de crédito', 'analista de credito',
      'desenvolvedor python', 'desenvolvedor java', 'desenvolvedor javascript', 'desenvolvedor react',
      'desenvolvedor frontend', 'desenvolvedor front-end', 'desenvolvedor backend', 'desenvolvedor back-end',
      'desenvolvedor full stack', 'desenvolvedor fullstack', 'desenvolvedor mobile', 'desenvolvedor web',
      'desenvolvedor .net', 'desenvolvedor dotnet', 'desenvolvedor node', 'desenvolvedor nodejs',
      'desenvolvedor angular', 'desenvolvedor vue', 'desenvolvedor go', 'desenvolvedor golang',
      'engenheiro de software', 'engenheiro de dados', 'engenheiro de machine learning', 'engenheiro devops',
      'engenheiro de qa', 'engenheiro de qualidade', 'engenheiro de produção', 'engenheiro de producao',
      'gerente de projetos', 'gerente de rh', 'gerente financeiro', 'gerente comercial', 'gerente de vendas',
      'gerente de marketing', 'gerente de operações', 'gerente de operacoes', 'gerente de ti', 'gerente de tecnologia',
      'gerente de produto', 'gerente de produção', 'gerente de producao', 'gerente administrativo',
      'coordenador de rh', 'coordenador financeiro', 'coordenador de projetos', 'coordenador de ti',
      'coordenador comercial', 'coordenador de marketing', 'coordenador de operações', 'coordenador de operacoes',
      'supervisor de produção', 'supervisor de producao', 'supervisor de vendas', 'supervisor de operações',
      'diretor financeiro', 'diretor de rh', 'diretor de ti', 'diretor comercial', 'diretor de operações',
      'cfo', 'cto', 'coo', 'cmo', 'cpo', 'ceo', 'chro',
      'product manager', 'product owner', 'scrum master', 'agile coach', 'tech lead', 'tech leader',
      'ux designer', 'ui designer', 'ux/ui designer', 'product designer', 'designer gráfico', 'designer grafico',
      'assistente administrativo', 'assistente financeiro', 'assistente de rh', 'assistente comercial',
      'auxiliar administrativo', 'auxiliar financeiro', 'auxiliar de escritório', 'auxiliar de escritorio',
      'contador', 'contadora', 'controller', 'tesoureiro', 'tesoureira',
      'cientista de dados', 'data scientist', 'data analyst', 'data engineer', 'machine learning engineer',
      'devops engineer', 'sre', 'site reliability engineer', 'cloud engineer', 'arquiteto de software',
      'arquiteto de soluções', 'arquiteto de solucoes', 'arquiteto cloud', 'arquiteto de sistemas',
      'consultor sap', 'consultor oracle', 'consultor de ti', 'consultor financeiro', 'consultor tributário',
      'advogado', 'advogada', 'advogado trabalhista', 'advogado tributário', 'advogado empresarial',
      'recrutador', 'recrutadora', 'talent acquisition', 'headhunter', 'business partner de rh', 'bp de rh',
      'vendedor', 'vendedora', 'executivo de vendas', 'executivo de contas', 'key account manager',
      'comprador', 'compradora', 'buyer', 'strategic buyer'
    ]

    for (const title of commonJobTitles) {
      const titlePattern = new RegExp(`\\b${title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?:\\s+(?:s[eê]nior|sr\\.?|pleno|pl\\.?|j[uú]nior|jr\\.?))?\\b`, 'i')
      const match = text.match(titlePattern)
      if (match) {
        newCriteria.cargo = match[0].split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
        break
      }
    }

    if (!newCriteria.cargo) {
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
            break
          }
        }
      }
    }

    const areaPatterns = [
      /\b(?:área|area|departamento|setor)\s*(?:de|do|da)?\s*[:\-]?\s*([a-záàâãéèêíïóôõöúç\s\/]+?)(?:\s*[,.\-]|\s+(?:com|para|que|na|no|em|$))/i,
      /\b(?:time|equipe)\s+(?:de|do|da)\s+([a-záàâãéèêíïóôõöúç\s\/]+?)(?:\s*[,.\-]|\s+(?:com|para|que|$))/i,
      /\bpara\s+(?:o|a)?\s*(?:área|area|departamento|time|equipe)\s+(?:de|do|da)?\s*([a-záàâãéèêíïóôõöúç\s\/]+?)(?:\s*[,.\-]|\s+(?:com|que|$))/i
    ]

    const areaKeywordMap: Record<string, string> = {
      'ti': 'Tecnologia/TI', 'tecnologia': 'Tecnologia/TI', 'sistemas': 'Tecnologia/TI', 'desenvolvimento': 'Tecnologia/TI',
      'financeiro': 'Financeiro', 'finanças': 'Financeiro', 'financas': 'Financeiro', 'controladoria': 'Financeiro',
      'contábil': 'Contábil', 'contabil': 'Contábil', 'contabilidade': 'Contábil',
      'fiscal': 'Fiscal/Tributário', 'tributário': 'Fiscal/Tributário', 'tributario': 'Fiscal/Tributário', 'impostos': 'Fiscal/Tributário',
      'rh': 'Recursos Humanos', 'recursos humanos': 'Recursos Humanos', 'gente e gestão': 'Recursos Humanos', 'people': 'Recursos Humanos',
      'dp': 'Departamento Pessoal', 'departamento pessoal': 'Departamento Pessoal', 'folha': 'Departamento Pessoal',
      'comercial': 'Comercial', 'vendas': 'Comercial', 'sales': 'Comercial',
      'marketing': 'Marketing', 'comunicação': 'Marketing', 'comunicacao': 'Marketing', 'growth': 'Marketing',
      'operações': 'Operações', 'operacoes': 'Operações', 'produção': 'Operações', 'producao': 'Operações',
      'logística': 'Logística', 'logistica': 'Logística', 'supply': 'Logística', 'suprimentos': 'Logística',
      'compras': 'Compras', 'procurement': 'Compras',
      'jurídico': 'Jurídico', 'juridico': 'Jurídico', 'legal': 'Jurídico',
      'qualidade': 'Qualidade', 'qa': 'Qualidade',
      'dados': 'Dados/BI', 'bi': 'Dados/BI', 'analytics': 'Dados/BI', 'data': 'Dados/BI',
      'design': 'Design', 'ux': 'Design', 'ui': 'Design', 'produto': 'Produto', 'product': 'Produto',
      'administrativo': 'Administrativo', 'admin': 'Administrativo'
    }

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

    const techSkills = [
      'python', 'javascript', 'react', 'node', 'nodejs', 'django', 'fastapi', 'java', 'typescript',
      'angular', 'vue', 'sql', 'aws', 'docker', 'kubernetes', 'data science', 'machine learning',
      'flask', 'spring', 'go', 'golang', 'rust', 'c#', '.net', 'dotnet', 'ruby', 'rails', 'php',
      'laravel', 'swift', 'kotlin', 'flutter', 'react native', 'mongodb', 'postgresql', 'mysql',
      'redis', 'elasticsearch', 'kafka', 'rabbitmq', 'graphql', 'rest api', 'microservices',
      'devops', 'ci/cd', 'jenkins', 'terraform', 'ansible', 'azure', 'gcp', 'linux', 'git',
      'infraestrutura', 'cybersegurança', 'segurança da informação', 'sre', 'site reliability',
      'engenharia de software', 'implantação', 'sistemas', 'redes', 'cloud', 'nuvem',
      'banco de dados', 'backend', 'frontend', 'full stack', 'fullstack', 'mobile',
      'scrum', 'agile', 'kanban', 'jira', 'figma', 'ux', 'ui', 'product', 'analytics',
      'power bi', 'tableau', 'excel avançado', 'sap', 'salesforce', 'crm', 'erp',
      'ifrs', 'impostos diretos', 'impostos indiretos', 'compliance', 'obrigações acessórias',
      'obrigacoes acessorias', 'sped', 'ecf', 'ecd', 'reinf', 'dctf', 'per/dcomp', 'perdcomp',
      'icms', 'ipi', 'pis', 'cofins', 'irpj', 'csll', 'iss', 'inss', 'fgts',
      'legislação tributária', 'legislacao tributaria', 'planejamento tributário', 'planejamento tributario',
      'contabilidade', 'controladoria', 'auditoria', 'cpc', 'gaap', 'usgaap',
      'conciliação contábil', 'conciliacao contabil', 'fechamento contábil', 'fechamento contabil',
      'análise fiscal', 'analise fiscal', 'apuração de impostos', 'apuracao de impostos',
      'transfer pricing', 'preços de transferência', 'precos de transferencia',
      'lucro real', 'lucro presumido', 'simples nacional', 'regime tributário', 'regime tributario',
      'fp&a', 'tesouraria', 'fluxo de caixa', 'dre', 'balanço patrimonial', 'balanco patrimonial',
      'orçamento', 'orcamento', 'budget', 'forecast', 'valuation', 'm&a', 'due diligence',
      'análise financeira', 'analise financeira', 'modelagem financeira', 'excel financeiro',
      'folha de pagamento', 'e-social', 'esocial', 'clt', 'legislação trabalhista',
      'recrutamento e seleção', 'r&s', 'treinamento e desenvolvimento', 't&d',
      'avaliação de desempenho', 'clima organizacional', 'cargos e salários',
      'direito tributário', 'direito trabalhista', 'direito empresarial', 'direito societário',
      'contratos', 'lgpd', 'due diligence jurídico'
    ]
    const foundTechSkills: string[] = []
    techSkills.forEach(skill => {
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
      const uniqueNew = foundTechSkills.filter(s => !existingLower.has(s.toLowerCase()))
      newCriteria.competenciasTecnicas = [...(newCriteria.competenciasTecnicas || []), ...uniqueNew]
    }

    const behavioralSkills = [
      'liderança', 'lideranca', 'comunicação', 'comunicacao', 'trabalho em equipe',
      'pensamento crítico', 'pensamento critico', 'resolução de problemas', 'resolucao de problemas',
      'adaptabilidade', 'proatividade', 'criatividade', 'inovação', 'inovacao',
      'gestão de tempo', 'gestao de tempo', 'organização', 'organizacao',
      'negociação', 'negociacao', 'empatia', 'resiliência', 'resiliencia',
      'tomada de decisão', 'tomada de decisao', 'autonomia', 'colaboração', 'colaboracao',
      'orientação a resultados', 'orientacao a resultados', 'visão estratégica', 'visao estrategica',
      'gestão de pessoas', 'gestao de pessoas', 'mentoria', 'coaching',
      'influência', 'influencia', 'stakeholder management', 'gestão de stakeholders',
      'foco no cliente', 'customer centric', 'perfil analítico', 'perfil analitico',
      'capacidade analítica', 'capacidade analitica', 'atenção aos detalhes', 'atencao aos detalhes',
      'senso de urgência', 'senso de urgencia', 'flexibilidade', 'dinamismo',
      'ética profissional', 'etica profissional', 'inteligência emocional', 'inteligencia emocional'
    ]
    const foundBehavioralSkills: string[] = []
    behavioralSkills.forEach(skill => {
      const skillPattern = new RegExp(`\\b${skill.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
      if (skillPattern.test(lowerText)) {
        foundBehavioralSkills.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
      }
    })
    if (foundBehavioralSkills.length > 0) {
      const existingLower = new Set((newCriteria.competenciasComportamentais || []).map(s => s.toLowerCase()))
      const uniqueNew = foundBehavioralSkills.filter(s => !existingLower.has(s.toLowerCase()))
      newCriteria.competenciasComportamentais = [...(newCriteria.competenciasComportamentais || []), ...uniqueNew]
    }

    const responsibilityPatterns = [
      /responsabilidades?\s*[:\-]\s*([^.]+(?:\.[^.]+)*)/i,
      /atividades?\s*[:\-]\s*([^.]+(?:\.[^.]+)*)/i,
      /atribui[çc][õo]es?\s*[:\-]\s*([^.]+(?:\.[^.]+)*)/i,
      /vai\s+(?:ser\s+)?responsável\s+por\s+([^.]+)/i,
      /será\s+responsável\s+por\s+([^.]+)/i,
    ]
    for (const pattern of responsibilityPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const respList = match[1].split(/[;,•\-]/).map(s => s.trim()).filter(s => s.length > 5)
        if (respList.length > 0) {
          newCriteria.responsabilidades = [...(newCriteria.responsabilidades || []), ...respList]
          break
        }
      }
    }

    const seniorityPatterns = [
      /\b(s[eê]nior|sr\.?)\b/i,
      /\b(pleno|pl\.?)\b/i,
      /\b(j[uú]nior|jr\.?)\b/i,
      /\b(especialista|principal|staff)\b/i,
      /\b(trainee|est[aá]gio|est[aá]giário|estagiario)\b/i,
      /\b(l[ií]der|lead(?:er)?|head|coordenador|gerente|diretor)\b/i,
    ]

    for (const pattern of seniorityPatterns) {
      const match = text.match(pattern)
      if (match) {
        const matched = match[1].toLowerCase()
        if (matched.match(/s[eê]nior|sr/)) newCriteria.senioridadeIdiomas = 'Sênior'
        else if (matched.match(/pleno|pl/)) newCriteria.senioridadeIdiomas = 'Pleno'
        else if (matched.match(/j[uú]nior|jr/)) newCriteria.senioridadeIdiomas = 'Júnior'
        else if (matched.match(/especialista|principal|staff/)) newCriteria.senioridadeIdiomas = 'Especialista'
        else if (matched.match(/trainee|est[aá]g/)) newCriteria.senioridadeIdiomas = 'Trainee'
        else if (matched.match(/l[ií]der|lead|head|coordenador|gerente|diretor/)) newCriteria.senioridadeIdiomas = 'Liderança'
        break
      }
    }

    const workModelPatterns = [
      { pattern: /\b(?:100%\s*)?remoto\b/i, model: 'Remoto' },
      { pattern: /\bhome\s*office\b/i, model: 'Remoto' },
      { pattern: /\bh[ií]brido\b/i, model: 'Híbrido' },
      { pattern: /\bpresencial\b/i, model: 'Presencial' },
      { pattern: /\bon[\-\s]?site\b/i, model: 'Presencial' },
    ]
    for (const { pattern, model } of workModelPatterns) {
      if (pattern.test(text)) {
        newCriteria.modeloTrabalho = model
        break
      }
    }

    const diasPresenciaisPattern = /(\d+)\s*(?:dias?|x)\s*(?:presenciais?|no\s+escrit[oó]rio|on[\-\s]?site)/i
    const diasMatch = text.match(diasPresenciaisPattern)
    if (diasMatch) {
      newCriteria.diasPresenciais = parseInt(diasMatch[1])
    }

    const locationPatterns = [
      new RegExp(`(?:localiza[çc][aã]o|local|cidade|regi[aã]o|sede|escrit[oó]rio)\\s*[:\\-]?\\s*([${ptLetters}\\s\\/]+?)(?:\\s*[,.]|\\s+(?:com|para|que|$))`, 'i'),
      /\bem\s+([A-Z][a-záàâãéèêíïóôõöúç]+(?:\s+[A-Z][a-záàâãéèêíïóôõöúç]+)*(?:\s*[-\/]\s*[A-Z]{2})?)/,
      /([A-Z][a-záàâãéèêíïóôõöúç]+(?:\s+[A-Z][a-záàâãéèêíïóôõöúç]+)*)\s*[-\/]\s*([A-Z]{2})\b/,
    ]
    for (const pattern of locationPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const loc = match[1].trim()
        if (loc.length > 2 && loc.length < 50) {
          newCriteria.localizacao = loc
          break
        }
      }
    }

    const contractPatterns = [
      { pattern: /\bclt\b/i, type: 'CLT' },
      { pattern: /\bpj\b/i, type: 'PJ' },
      { pattern: /\best[aá]gio\b/i, type: 'Estágio' },
      { pattern: /\btemporário\b/i, type: 'Temporário' },
      { pattern: /\bfreelancer?\b/i, type: 'Freelancer' },
      { pattern: /\bcooperado\b/i, type: 'Cooperado' },
    ]
    for (const { pattern, type } of contractPatterns) {
      if (pattern.test(text)) {
        newCriteria.tipoContrato = type
        break
      }
    }

    const salaryPatterns = [
      /(?:sal[aá]rio|remunera[çc][aã]o|faixa\s+salarial)\s*(?:de\s+)?R?\$?\s*([\d.,]+)\s*(?:a|até|[\-–])\s*R?\$?\s*([\d.,]+)/i,
      /R?\$\s*([\d.,]+)\s*(?:a|até|[\-–])\s*R?\$?\s*([\d.,]+)/,
      /(?:sal[aá]rio|remunera[çc][aã]o)\s*(?:de\s+)?R?\$?\s*([\d.,]+)/i,
    ]
    for (const pattern of salaryPatterns) {
      const match = text.match(pattern)
      if (match) {
        newCriteria.salario = match[0]
        break
      }
    }

    const formacaoPatterns = [
      /forma[çc][aã]o\s*(?:em|:)\s*([^.,;]+)/i,
      /gradua[çc][aã]o\s*(?:em|:)\s*([^.,;]+)/i,
      /curso\s+(?:superior\s+)?(?:de|em)\s+([^.,;]+)/i,
      /bacharelado\s+(?:em|:)\s*([^.,;]+)/i,
      /p[oó]s[\-\s]gradua[çc][aã]o\s*(?:em|:)\s*([^.,;]+)/i,
      /mba\s*(?:em|:)\s*([^.,;]+)/i,
      /mestrado\s*(?:em|:)\s*([^.,;]+)/i,
      /doutorado\s*(?:em|:)\s*([^.,;]+)/i,
    ]
    for (const pattern of formacaoPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const formacao = match[1].trim()
        if (formacao.length > 2 && !newCriteria.formacao.includes(formacao)) {
          newCriteria.formacao = [...newCriteria.formacao, formacao]
        }
      }
    }

    const certPatterns = [
      /certifica[çc][aã]o\s*(?:em|:)?\s*([^.,;]+)/i,
      /certificado\s*(?:em|de|:)?\s*([^.,;]+)/i,
      /\b(PMP|ITIL|COBIT|CPA[\-\s]?(?:10|20)?|CFA|CGA|CISA|CISSP|AWS\s+(?:Solutions?\s+)?Architect|Scrum\s+Master|CSPO|CSM)\b/i,
    ]
    for (const pattern of certPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const cert = match[1].trim()
        if (cert.length > 1 && !newCriteria.certificacoes.includes(cert)) {
          newCriteria.certificacoes = [...newCriteria.certificacoes, cert]
        }
      }
    }

    const experienciaPatterns = [
      /(\d+)\s*(?:\+\s*)?anos?\s+(?:de\s+)?experi[eê]ncia/i,
      /experi[eê]ncia\s+(?:m[ií]nima\s+)?(?:de\s+)?(\d+)\s*(?:\+\s*)?anos?/i,
      /m[ií]nimo\s+(?:de\s+)?(\d+)\s*(?:\+\s*)?anos?\s+(?:de\s+)?experi[eê]ncia/i,
    ]
    for (const pattern of experienciaPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        newCriteria.experienciaMinima = `${match[1]} anos`
        break
      }
    }

    const idiomaPatternsDetect = [
      { pattern: /ingl[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Inglês' },
      { pattern: /espanhol\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Espanhol' },
      { pattern: /franc[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Francês' },
      { pattern: /alem[aã]o\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Alemão' },
      { pattern: /italiano\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Italiano' },
      { pattern: /mandarim\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Mandarim' },
      { pattern: /japon[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Japonês' },
    ]
    for (const { pattern, name } of idiomaPatternsDetect) {
      const match = text.match(pattern)
      if (match) {
        const fullMatch = match[0].toLowerCase()
        let level = 'Intermediário'
        if (fullMatch.includes('fluente') || fullMatch.includes('avançado') || fullMatch.includes('avancado')) {
          level = 'Avançado'
        } else if (fullMatch.includes('básico') || fullMatch.includes('basico')) {
          level = 'Básico'
        }
        if (!newCriteria.idiomas.some(i => i.name === name)) {
          newCriteria.idiomas = [...newCriteria.idiomas, { name, level }]
        }
      }
    }

    const benefitsPatterns = [
      /benef[ií]cios?\s*[:\-]\s*([^.]+)/i,
      /oferecemos\s*[:\-]?\s*([^.]+)/i,
    ]
    for (const pattern of benefitsPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const benefitsList = match[1].split(/[,;•\-]/).map(s => s.trim()).filter(s => s.length > 2)
        if (benefitsList.length > 0) {
          newCriteria.beneficiosMencionados = [...(newCriteria.beneficiosMencionados || []), ...benefitsList]
        }
      }
    }

    const commonBenefits = [
      'vale refeição', 'vale refei', 'vr', 'vale alimentação', 'vale aliment', 'va',
      'plano de saúde', 'plano de saude', 'plano odontológico', 'plano odontologico',
      'seguro de vida', 'gympass', 'wellhub', 'totalpass', 'auxílio creche', 'auxilio creche',
      'ppr', 'plr', 'bônus', 'bonus', 'stock options', 'previdência privada', 'previdencia privada',
      'day off', 'short friday', 'home office', 'auxílio home office', 'auxilio home office',
      'vale transporte', 'vt', 'estacionamento', 'cesta básica', 'cesta basica',
    ]
    commonBenefits.forEach(benefit => {
      const benefitPattern = new RegExp(`\\b${benefit.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
      if (benefitPattern.test(lowerText)) {
        const capitalizedBenefit = benefit.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
        if (!(newCriteria.beneficiosMencionados || []).some(b => b.toLowerCase() === benefit.toLowerCase())) {
          newCriteria.beneficiosMencionados = [...(newCriteria.beneficiosMencionados || []), capitalizedBenefit]
        }
      }
    })

    const bonusPatterns = [
      /b[oô]nus\s*(?:de\s+)?(?:até\s+)?(\d+)\s*sal[aá]rios?/i,
      /b[oô]nus\s*(?:de\s+)?R?\$?\s*([\d.,]+)/i,
      /b[oô]nus\s*(?:de\s+)?(\d+)%/i,
      /ppr\s*(?:de\s+)?(?:até\s+)?(\d+)\s*sal[aá]rios?/i,
      /plr\s*(?:de\s+)?(?:até\s+)?(\d+)\s*sal[aá]rios?/i,
    ]
    for (const pattern of bonusPatterns) {
      const match = text.match(pattern)
      if (match) {
        newCriteria.bonus = match[0]
        break
      }
    }

    const affirmativePatterns = [
      /\bvaga\s+afirmativa\b/i,
      /\bação\s+afirmativa\b/i,
      /\binclusiva\b/i,
      /\bpcd\b/i,
      /\bpessoas?\s+com\s+defici[eê]ncia\b/i,
      /\bpessoas?\s+negras?\b/i,
      /\bpessoas?\s+trans\b/i,
      /\bdiversidade\b/i,
      /\bequidade\b/i,
      /\b50\+\b/i,
      /\bpessoas?\s+(?:acima\s+de\s+)?\d+\s*anos?\b/i,
    ]
    for (const pattern of affirmativePatterns) {
      if (pattern.test(text)) {
        newCriteria.isAffirmative = true
        const afMatch = text.match(pattern)
        if (afMatch) {
          newCriteria.affirmativeCriteriaPrimary = afMatch[0]
        }
        break
      }
    }

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

    setDetectedCriteria(newCriteria)
    return newCriteria
  }, [])

  return { extractCriteriaFromText }
}
