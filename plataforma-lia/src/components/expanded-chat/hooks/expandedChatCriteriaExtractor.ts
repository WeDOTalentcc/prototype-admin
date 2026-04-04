import { formatBRL, CURRENCY_SYMBOL } from "@/lib/pricing"
import type { DetectedCriteria } from ".."

export function extractCriteriaFromText(text: string, currentCriteria: DetectedCriteria): DetectedCriteria {
  const lowerText = text.toLowerCase()
  const newCriteria = { ...currentCriteria }

  // Character class that includes both lowercase and uppercase Portuguese letters
  const ptLetters = 'a-zA-ZáàâãéèêíïóôõöúçÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ'
  
  // Common job titles list for direct matching
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
  
  // Try to match common job titles first (more accurate)
  for (const title of commonJobTitles) {
    const titlePattern = new RegExp(`\\b${title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?:\\s+(?:s[eê]nior|sr\\.?|pleno|pl\\.?|j[uú]nior|jr\\.?))?\\b`, 'i')
    const match = text.match(titlePattern)
    if (match) {
      newCriteria.cargo = match[0].split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
      break
    }
  }
  
  // If no common title found, try patterns
  if (!newCriteria.cargo) {
    const cargoPatterns = [
      // "preciso de um X", "busco X", "contratando X"
      new RegExp(`(?:preciso\\s+de\\s+(?:um|uma)?|busco\\s+(?:um|uma)?|contratando|procuro\\s+(?:um|uma)?)\\s+([${ptLetters}\\s]+?)(?:\\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?(?:\\s+(?:para|que|com|\\.|,|$))`, 'i'),
      // "vaga de X", "vaga para X"
      new RegExp(`vaga\\s+(?:de|para)\\s+([${ptLetters}\\s]+?)(?:\\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?(?:\\s+(?:que|para\\s+a|com\\s+experi[êe]ncia|na|no|em|,|\\.|$))`, 'i'),
      // "cargo: X", "posição: X", "função: X"
      new RegExp(`(?:cargo|posi[çc][aã]o|fun[çc][aã]o)\\s*[:\\-]?\\s*([${ptLetters}\\s]+?)(?:\\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?(?:\\s+(?:que|para|com|,|\\.|$))`, 'i'),
      // Specific role patterns - capture the full role
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
  
  // ========== AREA/DEPARTMENT DETECTION ==========
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
  
  // Try to detect area from explicit patterns
  for (const pattern of areaPatterns) {
    const match = text.match(pattern)
    if (match && match[1]) {
      const areaText = match[1].trim().toLowerCase()
      // Check if it matches a known area
      for (const [key, value] of Object.entries(areaKeywordMap)) {
        if (areaText.includes(key)) {
          newCriteria.departamento = value
          break
        }
      }
      if (newCriteria.departamento) break
      // If not a known keyword, use the detected text directly
      if (areaText.length > 1 && areaText.length < 40) {
        newCriteria.departamento = match[1].trim().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
        break
      }
    }
  }
  
  // Also try to detect area from cargo if not found
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
    // Formato direto com dois pontos: "gestor: carlos silva", "gestor: ti"
    new RegExp(`gestor(?:a)?[:\\s]+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    // Formato direto com dois pontos: "área: tecnologia", "departamento: ti"
    new RegExp(`(?:área|area|departamento|setor)[:\\s]+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    // Formato com barra: "gestor: carlos silva/departamento de ti" - captura antes da barra
    new RegExp(`gestor(?:a)?[:\\s]+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})(?:\\/|$)`, 'i'),
    // Reporta para
    new RegExp(`reporta(?:r[áa])?\\s+(?:para|ao?|diretamente\\s+ao?)\\s+(?:o\\s+|a\\s+)?([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    // Equipe do/da
    new RegExp(`equipe\\s+d[oa]\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,2})`, 'i'),
    // Time do/da
    new RegExp(`time\\s+d[oa]\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,2})`, 'i'),
    // Supervisão/liderança/gestão de
    new RegExp(`(?:sob\\s+)?(?:supervisão|liderança|gestão)\\s+(?:do?a?\\s+)?([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,2})`, 'i'),
    // Gestor de [área]
    new RegExp(`gestor(?:a)?\\s+de\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    // Área/departamento/setor de [nome]
    new RegExp(`(?:área|departamento|setor)\\s+de\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    // Gestão de [área]
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
    // Tech/IT
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
    // Fiscal/Tributário/Contábil
    'ifrs', 'impostos diretos', 'impostos indiretos', 'compliance', 'obrigações acessórias',
    'obrigacoes acessorias', 'sped', 'ecf', 'ecd', 'reinf', 'dctf', 'per/dcomp', 'perdcomp',
    'icms', 'ipi', 'pis', 'cofins', 'irpj', 'csll', 'iss', 'inss', 'fgts',
    'legislação tributária', 'legislacao tributaria', 'planejamento tributário', 'planejamento tributario',
    'contabilidade', 'controladoria', 'auditoria', 'cpc', 'gaap', 'usgaap',
    'conciliação contábil', 'conciliacao contabil', 'fechamento contábil', 'fechamento contabil',
    'análise fiscal', 'analise fiscal', 'apuração de impostos', 'apuracao de impostos',
    'transfer pricing', 'preços de transferência', 'precos de transferencia',
    'lucro real', 'lucro presumido', 'simples nacional', 'regime tributário', 'regime tributario',
    // Financeiro
    'fp&a', 'tesouraria', 'fluxo de caixa', 'dre', 'balanço patrimonial', 'balanco patrimonial',
    'orçamento', 'orcamento', 'budget', 'forecast', 'valuation', 'm&a', 'due diligence',
    'análise financeira', 'analise financeira', 'modelagem financeira', 'excel financeiro',
    // RH/DP
    'folha de pagamento', 'e-social', 'esocial', 'clt', 'legislação trabalhista', 
    'recrutamento e seleção', 'r&s', 'treinamento e desenvolvimento', 't&d',
    'avaliação de desempenho', 'clima organizacional', 'cargos e salários',
    // Jurídico
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
  
  // Also detect when user explicitly lists skills with pattern "competências técnicas: X, Y, Z"
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
    // Case-insensitive deduplication for technical skills
    const existingLower = new Set((newCriteria.competenciasTecnicas || []).map(s => s.toLowerCase()))
    const uniqueNewSkills = foundTechSkills.filter(s => !existingLower.has(s.toLowerCase()))
    newCriteria.competenciasTecnicas = [...(newCriteria.competenciasTecnicas || []), ...uniqueNewSkills]
  }

  const softSkills = [
    'liderança', 'lideranca', 'gestão de pessoas', 'gestao de pessoas', 'comunicação', 'comunicacao',
    'trabalho em equipe', 'proatividade', 'pro-atividade', 'organização', 'organizacao',
    'negociação', 'negociacao', 'resiliência', 'resiliencia', 'empatia', 'criatividade',
    'pensamento crítico', 'resolução de problemas', 'adaptabilidade', 'flexibilidade',
    'autonomia', 'iniciativa', 'colaboração', 'colaboracao', 'foco em resultados',
    'orientação para resultados', 'relacionamento interpessoal', 'inteligência emocional',
    'tomada de decisão', 'visão estratégica', 'visao estrategica', 'gestão de conflitos',
    'mentoria', 'coaching', 'feedback', 'influência', 'influencia', 'persuasão', 'persuasao'
  ]
  const foundSoftSkills: string[] = []
  softSkills.forEach(skill => {
    if (lowerText.includes(skill)) {
      foundSoftSkills.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
    }
  })
  if (foundSoftSkills.length > 0) {
    // Case-insensitive deduplication for behavioral skills
    const existingLower = new Set((newCriteria.competenciasComportamentais || []).map(s => s.toLowerCase()))
    const uniqueNewComps = foundSoftSkills.filter(s => !existingLower.has(s.toLowerCase()))
    newCriteria.competenciasComportamentais = [...(newCriteria.competenciasComportamentais || []), ...uniqueNewComps]
  }

  // ========== IDIOMAS DETECTION ==========
  const idiomasPatterns = [
    // "inglês avançado", "inglês fluente", "inglês intermediário"
    /\b(ingl[eê]s|english)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(espanhol|spanish)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(franc[eê]s|french)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(alem[aã]o|german)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(italiano|italian)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(portugu[eê]s|portuguese)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(mandarim|chin[eê]s|chinese)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    /\b(japon[eê]s|japanese)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
    // Padrões inversos: "fluente em inglês", "avançado em espanhol"
    /\b(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)\s+(?:em\s+)?(ingl[eê]s|espanhol|franc[eê]s|alem[aã]o|italiano|mandarim|chin[eê]s|japon[eê]s)/gi,
    // Padrões com nível: "inglês nível avançado", "inglês C1", "inglês B2"
    /\b(ingl[eê]s|espanhol|franc[eê]s|alem[aã]o|italiano|mandarim|chin[eê]s|japon[eê]s)\s+(?:n[ií]vel\s+)?(C1|C2|B1|B2|A1|A2)/gi,
  ]
  
  const foundIdiomas: string[] = []
  const idiomasNormalize: Record<string, string> = {
    'ingles': 'Inglês', 'inglês': 'Inglês', 'english': 'Inglês',
    'espanhol': 'Espanhol', 'spanish': 'Espanhol',
    'frances': 'Francês', 'francês': 'Francês', 'french': 'Francês',
    'alemao': 'Alemão', 'alemão': 'Alemão', 'german': 'Alemão',
    'italiano': 'Italiano', 'italian': 'Italiano',
    'portugues': 'Português', 'português': 'Português', 'portuguese': 'Português',
    'mandarim': 'Mandarim', 'chines': 'Chinês', 'chinês': 'Chinês', 'chinese': 'Chinês',
    'japones': 'Japonês', 'japonês': 'Japonês', 'japanese': 'Japonês',
  }
  const nivelNormalize: Record<string, string> = {
    'avancado': 'Avançado', 'avançado': 'Avançado',
    'fluente': 'Fluente', 'nativo': 'Nativo',
    'intermediario': 'Intermediário', 'intermediário': 'Intermediário',
    'basico': 'Básico', 'básico': 'Básico',
    'c1': 'C1', 'c2': 'C2', 'b1': 'B1', 'b2': 'B2', 'a1': 'A1', 'a2': 'A2',
  }
  
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

  const seniorityMatch = text.match(/\b(júnior|junior|jr|pleno|pl|sênior|senior|sr|especialista|trainee|estagiário|estagiario|estágio|estagio)\b/i)
  if (seniorityMatch) {
    const seniority = seniorityMatch[1].toLowerCase()
    const seniorityMap: Record<string, string> = {
      'junior': 'Júnior', 'júnior': 'Júnior', 'jr': 'Júnior',
      'pleno': 'Pleno', 'pl': 'Pleno',
      'senior': 'Sênior', 'sênior': 'Sênior', 'sr': 'Sênior',
      'especialista': 'Especialista',
      'trainee': 'Trainee',
      'estagiário': 'Estagiário', 'estagiario': 'Estagiário', 'estágio': 'Estágio', 'estagio': 'Estágio'
    }
    newCriteria.senioridadeIdiomas = seniorityMap[seniority] || seniority.charAt(0).toUpperCase() + seniority.slice(1)
  }

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

  const knownCities: Record<string, string> = {
    'são paulo': 'São Paulo, SP',
    'sao paulo': 'São Paulo, SP',
    'rio de janeiro': 'Rio de Janeiro, RJ',
    'belo horizonte': 'Belo Horizonte, MG',
    'curitiba': 'Curitiba, PR',
    'porto alegre': 'Porto Alegre, RS',
    'brasília': 'Brasília, DF',
    'brasilia': 'Brasília, DF',
    'salvador': 'Salvador, BA',
    'recife': 'Recife, PE',
    'fortaleza': 'Fortaleza, CE',
    'campinas': 'Campinas, SP',
    'florianópolis': 'Florianópolis, SC',
    'florianopolis': 'Florianópolis, SC',
    'goiânia': 'Goiânia, GO',
    'goiania': 'Goiânia, GO',
    'manaus': 'Manaus, AM',
    'belém': 'Belém, PA',
    'belem': 'Belém, PA',
    'vitória': 'Vitória, ES',
    'vitoria': 'Vitória, ES',
    'natal': 'Natal, RN',
    'joão pessoa': 'João Pessoa, PB',
    'joao pessoa': 'João Pessoa, PB',
    'maceió': 'Maceió, AL',
    'maceio': 'Maceió, AL',
    'cuiabá': 'Cuiabá, MT',
    'cuiaba': 'Cuiabá, MT',
    'campo grande': 'Campo Grande, MS',
    'teresina': 'Teresina, PI',
    'são luís': 'São Luís, MA',
    'sao luis': 'São Luís, MA',
    'aracaju': 'Aracaju, SE',
    'ribeirão preto': 'Ribeirão Preto, SP',
    'ribeirao preto': 'Ribeirão Preto, SP',
    'santos': 'Santos, SP',
    'sorocaba': 'Sorocaba, SP',
    'são josé dos campos': 'São José dos Campos, SP',
    'sao jose dos campos': 'São José dos Campos, SP',
    'londrina': 'Londrina, PR',
    'joinville': 'Joinville, SC',
    'blumenau': 'Blumenau, SC',
    'uberlândia': 'Uberlândia, MG',
    'uberlandia': 'Uberlândia, MG'
  }
  
  const stateAbbrev: Record<string, string> = {
    'sp': 'São Paulo, SP', 'rj': 'Rio de Janeiro, RJ', 'mg': 'Belo Horizonte, MG',
    'pr': 'Curitiba, PR', 'rs': 'Porto Alegre, RS', 'df': 'Brasília, DF',
    'ba': 'Salvador, BA', 'pe': 'Recife, PE', 'ce': 'Fortaleza, CE',
    'sc': 'Florianópolis, SC', 'go': 'Goiânia, GO', 'am': 'Manaus, AM',
    'pa': 'Belém, PA', 'es': 'Vitória, ES', 'rn': 'Natal, RN'
  }
  
  for (const [cityKey, cityFormatted] of Object.entries(knownCities)) {
    const cityPattern = new RegExp(`\\b${cityKey.replace(/\s+/g, '\\s+')}\\b`, 'i')
    if (cityPattern.test(lowerText)) {
      newCriteria.localizacao = cityFormatted
      break
    }
  }
  
  if (!newCriteria.localizacao) {
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
          break
        }
      }
    }
  }

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

  // ========== RESPONSABILIDADES DETECTION ==========
  const responsibilityPatterns = [
    // "vai ser responsável por gestão de times, consolidações, reports"
    /(?:vai\s+ser|será|serás?|sendo|é|era|foi)\s+respons[áa]vel\s+por\s+([^.!?]+)/i,
    // "responsável por: X, Y, Z"
    /respons[áa]vel\s+por\s*[:\-]?\s*([^.!?]+)/i,
    // "responsabilidade como X, Y, Z" ou "responsabilidades como X, Y, Z"
    /responsabilidades?\s+como\s+([^.!?]+)/i,
    // "responsabilidades: X, Y, Z"
    /responsabilidades?\s*[:\-]\s*([^.!?]+)/i,
    // "principais atribuições: X, Y, Z"
    /(?:principais\s+)?atribui[çc][õo]es?\s*[:\-]\s*([^.!?]+)/i,
    // "atividades: X, Y, Z"
    /atividades?\s*[:\-]\s*([^.!?]+)/i,
    // "vai liderar projetos de X, desenvolver Y, mentorar Z"
    /vai\s+(liderar|gerenciar|coordenar|supervisionar|desenvolver|implementar|criar|construir|mentorar|treinar)\s+([^.!?]+)/i,
    // "irá liderar pessoas, gerir a área"
    /ir[áa]\s+(liderar|gerenciar|coordenar|supervisionar|desenvolver|implementar|criar|construir|mentorar|treinar|gerir)\s+([^.!?]+)/i,
    // "além de gestão de equipe"
    /al[ée]m\s+(?:de|da|do|das|dos)\s+([^.!?,]+)/i,
  ]
  
  const foundResponsibilities: string[] = []
  for (const pattern of responsibilityPatterns) {
    const match = text.match(pattern)
    if (match) {
      const matchedText = match[1] || match[2] || ''
      // Split by comma, "e", or semicolon
      const items = matchedText.split(/[,;]|\s+e\s+/).map(s => s.trim()).filter(s => {
        // Filter out empty, too short, or common words
        if (s.length < 3) return false
        const stopWords = ['o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'para', 'com', 'por']
        return !stopWords.includes(s.toLowerCase())
      })
      items.forEach(item => {
        if (item.length > 3 && item.length < 100) {
          // Capitalize first letter
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
    // "salário entre 20 e 25 mil reais" - PRIORITY PATTERN
    /sal[áa]rio\s+entre\s+([\d.,]+)\s*(?:mil)?\s*(?:reais?)?\s*(?:e|a|até|-)\s*([\d.,]+)\s*(?:mil|k)?\s*(?:reais?)?/i,
    // "entre 20 e 25 mil" without "salário" prefix
    /entre\s+([\d.,]+)\s*(?:mil)?\s*(?:reais?)?\s*(?:e|a|até|-)\s*([\d.,]+)\s*(?:mil|k)\s*(?:reais?)?/i,
    // "de 20 a 25 mil reais"
    /(?:de\s+)?([\d.,]+)\s*(?:a|até|-)\s*([\d.,]+)\s*(?:mil|k)\s*(?:reais?)?/i,
    // Standard patterns with currency prefix
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
      
      // Handle case like "entre 20 e 25 mil" where only max has "mil"
      // If minValue is small (< 100) and maxValue is large (> 10000), apply multiplier to min
      if (minValue && maxValue && minValue < 100 && maxValue >= 1000) {
        minValue = minValue * 1000
      }
      // Handle case where both values are small but text contains "mil"
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

  // ========== VAGA AFIRMATIVA DETECTION ==========
  const affirmativePatterns = [
    // "não é afirmativa", "não é vaga afirmativa", "vaga não afirmativa"
    /(?:n[aã]o\s+[eé]\s+(?:uma?\s+)?(?:vaga\s+)?afirmativa|vaga\s+n[aã]o\s+afirmativa|n[aã]o\s+afirmativa)/i,
    // "é vaga afirmativa", "é afirmativa", "vaga afirmativa"
    /(?:[eé]\s+(?:uma?\s+)?(?:vaga\s+)?afirmativa|vaga\s+afirmativa|exclusiva\s+para)/i,
  ]
  
  // Check for negative pattern first (more specific)
  const negativeAffirmativeMatch = text.match(affirmativePatterns[0])
  if (negativeAffirmativeMatch) {
    newCriteria.isAffirmative = false
  } else {
    // Check for positive pattern
    const positiveAffirmativeMatch = text.match(affirmativePatterns[1])
    if (positiveAffirmativeMatch) {
      newCriteria.isAffirmative = true
    }
  }

  // ========== CRITÉRIOS AFIRMATIVOS ESPECÍFICOS ==========
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

  // ========== EXPERIÊNCIA MÍNIMA ==========
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

  // ========== FORMAÇÃO ACADÊMICA ==========
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

  // ========== CERTIFICAÇÕES ==========
  const certificacoesPatterns = [
    /certifica[çc][ãa]o\s+(?:em\s+)?([a-záàâãéèêíïóôõöúç\s\-]+?)(?:\s*[,.\-;]|\s+(?:ou|e|$))/gi,
    /certificado\s+(?:em\s+|de\s+)?([a-záàâãéèêíïóôõöúç\s\-]+?)(?:\s*[,.\-;]|\s+(?:ou|e|$))/gi,
  ]
  const knownCertifications = [
    'aws', 'azure', 'gcp', 'google cloud', 'pmp', 'scrum master', 'csm', 'psm', 'safe', 'itil',
    'cissp', 'cisa', 'ceh', 'comptia', 'ccna', 'ccnp', 'oracle', 'java certified', 'microsoft certified',
    'cpa', 'cpa-10', 'cpa-20', 'cga', 'crc', 'oab', 'cfc', 'crea', 'cfp', 'cea', 'cnpi',
    'iso 9001', 'iso 27001', 'six sigma', 'lean', 'green belt', 'black belt', 'yellow belt',
    'tableau certified', 'salesforce certified', 'hubspot', 'google analytics', 'meta blueprint',
  ]
  const foundCertificacoes: string[] = []
  // Check for known certifications
  knownCertifications.forEach(cert => {
    const certPattern = new RegExp(`\\b${cert.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
    if (certPattern.test(lowerText)) {
      foundCertificacoes.push(cert.toUpperCase())
    }
  })
  // Check for patterns
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

  // ========== FERRAMENTAS ESPECÍFICAS ==========
  const knownTools = [
    'jira', 'confluence', 'trello', 'asana', 'monday', 'notion', 'slack', 'microsoft teams', 'zoom',
    'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator', 'indesign', 'premiere', 'after effects',
    'sap', 'oracle', 'totvs', 'protheus', 'senior sistemas', 'sankhya', 'omie', 'conta azul', 'bling',
    'salesforce', 'hubspot', 'pipedrive', 'rd station', 'mailchimp', 'active campaign',
    'google analytics', 'google ads', 'facebook ads', 'meta ads', 'tiktok ads', 'linkedin ads',
    'excel', 'google sheets', 'power bi', 'tableau', 'looker', 'metabase', 'qlik',
    'git', 'github', 'gitlab', 'bitbucket', 'jenkins', 'circleci', 'travis',
    'vs code', 'visual studio', 'intellij', 'eclipse', 'pycharm', 'webstorm',
    'postman', 'insomnia', 'swagger', 'docker desktop', 'kubernetes dashboard',
  ]
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

  // ========== DIAS PRESENCIAIS (HÍBRIDO) ==========
  if (newCriteria.modeloTrabalho === 'Híbrido') {
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

  // ========== BENEFÍCIOS MENCIONADOS ==========
  const beneficiosKeywords = [
    { pattern: /\b(vale\s+refei[çc][ãa]o)\b/i, name: 'Vale Refeição' },
    { pattern: /\b(vale\s+alimenta[çc][ãa]o)\b/i, name: 'Vale Alimentação' },
    { pattern: /\b(vale\s+transporte)\b/i, name: 'Vale Transporte' },
    { pattern: /\b(plano\s+(?:de\s+)?sa[úu]de)\b/i, name: 'Plano de Saúde' },
    { pattern: /\b(plano\s+odontol[óo]gico)\b/i, name: 'Plano Odontológico' },
    { pattern: /\b(seguro\s+(?:de\s+)?vida)\b/i, name: 'Seguro de Vida' },
    { pattern: /\b(gympass|totalpass|wellhub)\b/i, name: 'Gympass/TotalPass' },
    { pattern: /\b(aux[íi]lio\s+home\s*office|aux[íi]lio\s+trabalho\s+remoto)\b/i, name: 'Auxílio Home Office' },
    { pattern: /\b(aux[íi]lio\s+(?:educa[çc][ãa]o|estudos?))\b/i, name: 'Auxílio Educação' },
    { pattern: /\b(aux[íi]lio\s+creche)\b/i, name: 'Auxílio Creche' },
    { pattern: /\b(day\s*off\s*(?:de\s+)?anivers[áa]rio)\b/i, name: 'Day Off Aniversário' },
    { pattern: /\b(stock\s*options?|a[çc][õo]es\s+(?:da\s+)?empresa)\b/i, name: 'Stock Options' },
    { pattern: /\b(participa[çc][ãa]o\s+nos?\s+lucros?|plr)\b/i, name: 'PLR' },
    { pattern: /\b(previdencia\s+privada)\b/i, name: 'Previdência Privada' },
    { pattern: /\b(licen[çc]a\s+maternidade\s+estendida)\b/i, name: 'Licença Maternidade Estendida' },
    { pattern: /\b(licen[çc]a\s+paternidade\s+estendida)\b/i, name: 'Licença Paternidade Estendida' },
  ]
  const foundBeneficios: string[] = []
  beneficiosKeywords.forEach(({ pattern, name }) => {
    if (pattern.test(text)) {
      foundBeneficios.push(name)
    }
  })
  if (foundBeneficios.length > 0) {
    newCriteria.beneficiosMencionados = [...new Set([...newCriteria.beneficiosMencionados, ...foundBeneficios])]
  }

  // ========== BÔNUS ==========
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

  // ========== VIAGENS FREQUENTES ==========
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

  // ========== DISPONIBILIDADE/INÍCIO ==========
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

  // ========== CNH ==========
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

  // ========== HORÁRIO DE TRABALHO ==========
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

  return newCriteria
}
