import type { DetectedCriteria } from '../ExpandedChatContext'

export function extractCriteriaFromTextPure(text: string, currentCriteria: DetectedCriteria): DetectedCriteria {
    const lowerText = text.toLowerCase()
    const newCriteria = { ...currentCriteria }

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
      'proatividade', 'resiliência', 'resiliencia', 'criatividade', 'pensamento crítico',
      'pensamento critico', 'negociação', 'negociacao', 'empatia', 'organização', 'organizacao',
      'adaptabilidade', 'gestão de tempo', 'gestao de tempo', 'resolução de problemas',
      'resolucao de problemas', 'colaboração', 'colaboracao', 'autogestão', 'autogestao',
      'inteligência emocional', 'inteligencia emocional', 'foco em resultados',
      'orientação ao cliente', 'orientacao ao cliente', 'capacidade analítica',
      'capacidade analitica', 'visão estratégica', 'visao estrategica', 'inovação', 'inovacao',
      'flexibilidade', 'autonomia', 'accountability', 'ownership', 'senso de urgência',
      'senso de urgencia', 'atenção aos detalhes', 'atencao aos detalhes', 'mentoria',
      'influência', 'influencia', 'tomada de decisão', 'tomada de decisao',
      'gestão de stakeholders', 'gestao de stakeholders', 'visão sistêmica', 'visao sistemica',
      'pensamento analítico', 'pensamento analitico', 'orientação a dados', 'orientacao a dados',
      'comunicação assertiva', 'comunicacao assertiva', 'gestão de conflitos', 'gestao de conflitos',
      'networking', 'storytelling', 'apresentação', 'apresentacao', 'facilitação', 'facilitacao'
    ]
    
    const foundBehavioral: string[] = []
    behavioralSkills.forEach(skill => {
      const skillPattern = new RegExp(`\\b${skill.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
      if (skillPattern.test(lowerText)) {
        foundBehavioral.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
      }
    })
    
    const explicitBehavioralPatterns = [
      /compet[êe]ncias?\s+comportamentais?\s*[:\-]\s*([^.]+)/i,
      /soft\s*skills?\s*[:\-]\s*([^.]+)/i,
      /habilidades?\s+interpessoais?\s*[:\-]\s*([^.]+)/i,
    ]
    
    for (const pattern of explicitBehavioralPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const skillsList = match[1].split(/[,;e]/).map(s => s.trim()).filter(s => s.length > 2)
        skillsList.forEach(skill => {
          if (skill && skill.length > 2 && !['e', 'ou', 'com', 'de', 'para'].includes(skill.toLowerCase())) {
            foundBehavioral.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' '))
          }
        })
      }
    }
    
    if (foundBehavioral.length > 0) {
      const existingLower = new Set((newCriteria.competenciasComportamentais || []).map(s => s.toLowerCase()))
      const uniqueNew = foundBehavioral.filter(s => !existingLower.has(s.toLowerCase()))
      newCriteria.competenciasComportamentais = [...(newCriteria.competenciasComportamentais || []), ...uniqueNew]
    }

    const seniorityPatterns = [
      /\b(s[eê]nior|sr\.?)\b/i,
      /\b(pleno|pl\.?)\b/i,
      /\b(j[uú]nior|jr\.?)\b/i,
      /\b(est[aá]gio|estagi[aá]rio|estagi[aá]ria|trainee)\b/i,
      /\b(especialista|specialist)\b/i,
      /\b(l[ií]der|lead|head|diretor|director|gerente|manager|coordenador|supervisor)\b/i,
    ]
    
    const seniorityMap: Record<number, string> = {
      0: 'Sênior',
      1: 'Pleno',
      2: 'Júnior',
      3: 'Estágio/Trainee',
      4: 'Especialista',
      5: 'Liderança',
    }
    
    for (let i = 0; i < seniorityPatterns.length; i++) {
      if (seniorityPatterns[i].test(text)) {
        newCriteria.senioridadeIdiomas = seniorityMap[i]
        break
      }
    }

    const modeloTrabalhoPatterns = [
      { pattern: /\b(?:100%\s*)?(?:remoto|remote|home\s*office|trabalho\s*remoto|totalmente\s*remoto)\b/i, value: 'Remoto' },
      { pattern: /\b(?:h[ií]brido|hybrid|modelo\s*h[ií]brido)\b/i, value: 'Híbrido' },
      { pattern: /\b(?:presencial|on[\s-]?site|onsite|in[\s-]?loco)\b/i, value: 'Presencial' },
    ]
    
    for (const { pattern, value } of modeloTrabalhoPatterns) {
      if (pattern.test(text)) {
        newCriteria.modeloTrabalho = value
        break
      }
    }

    const diasPresenciaisPatterns = [
      /(\d+)\s*(?:dias?\s*(?:por\s*semana|semanais?|presenciais?))/i,
      /presencial\s*(\d+)\s*(?:x|vezes)\s*(?:por\s*semana|semanais?)?/i,
      /(\d+)\s*(?:x|vezes)\s*presencial/i,
      /(\d+)\s*dias?\s*(?:no\s*escrit[oó]rio|na\s*empresa|presenciais?)/i,
    ]
    
    for (const pattern of diasPresenciaisPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const days = parseInt(match[1])
        if (days >= 1 && days <= 5) {
          newCriteria.diasPresenciais = days
          if (!newCriteria.modeloTrabalho) {
            newCriteria.modeloTrabalho = days >= 5 ? 'Presencial' : 'Híbrido'
          }
          break
        }
      }
    }

    const locationPatterns = [
      /\b(?:em|localizado|baseado|sede|escrit[oó]rio)\s+(?:em|no|na|de)?\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][a-záàâãéèêíïóôõöúç]+(?:\s+(?:do|da|de|dos|das)\s+)?(?:[A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][a-záàâãéèêíïóôõöúç]+)?(?:\s*[-\/]\s*[A-Z]{2})?)/,
      /\b([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][a-záàâãéèêíïóôõöúç]+(?:\s+(?:do|da|de|dos|das)\s+)?(?:[A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][a-záàâãéèêíïóôõöúç]+)?)\s*[-\/]\s*([A-Z]{2})\b/,
      /\b(?:cidade|regi[ãa]o)\s+(?:de|do|da)?\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][a-záàâãéèêíïóôõöúç]+(?:\s+[A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ][a-záàâãéèêíïóôõöúç]+)?)/,
    ]
    
    const knownCities = ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Curitiba', 'Porto Alegre', 'Brasília', 'Salvador', 'Recife', 'Fortaleza', 'Campinas', 'Florianópolis', 'Goiânia', 'Manaus', 'Belém', 'Vitória', 'Natal', 'São Luís', 'João Pessoa', 'Maceió', 'Aracaju', 'Campo Grande', 'Cuiabá', 'Teresina', 'Uberlândia', 'Ribeirão Preto', 'Sorocaba', 'Santos', 'Joinville', 'Londrina', 'Maringá', 'Niterói', 'Osasco', 'Guarulhos', 'Barueri', 'Alphaville']
    
    for (const city of knownCities) {
      const cityPattern = new RegExp(`\\b${city.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
      if (cityPattern.test(text)) {
        newCriteria.localizacao = city
        break
      }
    }
    
    if (!newCriteria.localizacao) {
      for (const pattern of locationPatterns) {
        const match = text.match(pattern)
        if (match) {
          const excludeWords = ['Preciso', 'Busco', 'Quero', 'Tenho', 'Estou', 'Nossa', 'Nosso', 'Vaga', 'Cargo', 'Python', 'React', 'Java', 'Angular', 'Vue', 'Django', 'Node', 'SQL']
          const locationText = match[1] + (match[2] ? `/${match[2]}` : '')
          const firstWord = locationText.split(/[\s\/]/)[0]
          if (!excludeWords.includes(firstWord)) {
            newCriteria.localizacao = locationText.trim()
            break
          }
        }
      }
    }

    const tipoContratoPatterns = [
      { pattern: /\b(?:clt|regime\s+clt|contrato\s+clt|carteira\s+assinada)\b/i, value: 'CLT' },
      { pattern: /\b(?:pj|pessoa\s+jur[ií]dica|contrato\s+pj|cnpj)\b/i, value: 'PJ' },
      { pattern: /\b(?:est[áa]gio|contrato\s+de\s+est[áa]gio|programa\s+de\s+est[áa]gio)\b/i, value: 'Estágio' },
      { pattern: /\b(?:tempor[áa]rio|contrato\s+tempor[áa]rio|prazo\s+determinado)\b/i, value: 'Temporário' },
      { pattern: /\b(?:freelancer|freelance|aut[oô]nomo|trabalho\s+aut[oô]nomo)\b/i, value: 'Freelancer' },
      { pattern: /\b(?:cooperado|cooperativa)\b/i, value: 'Cooperado' },
      { pattern: /\b(?:trainee|programa\s+de\s+trainee)\b/i, value: 'Trainee' },
    ]
    
    for (const { pattern, value } of tipoContratoPatterns) {
      if (pattern.test(text)) {
        newCriteria.tipoContrato = value
        break
      }
    }

    const salaryPatterns = [
      /(?:sal[áa]rio|remunera[çc][ãa]o|faixa\s+salarial)\s*(?:de|:|\-)?\s*(?:R\$\s*)?(\d[\d.,]*)\s*(?:a|até|at[ée]|\-)\s*(?:R\$\s*)?(\d[\d.,]*)/i,
      /(?:R\$\s*)?(\d[\d.,]*)\s*(?:a|até|at[ée]|\-)\s*(?:R\$\s*)?(\d[\d.,]*)\s*(?:mil|k|reais|mensal|m[eê]s)/i,
      /(?:sal[áa]rio|remunera[çc][ãa]o)\s*(?:de|:|\-)?\s*(?:R\$\s*)?(\d[\d.,]*)\s*(?:mil|k|reais)?/i,
      /(?:R\$\s*)?(\d[\d.,]*)\s*(?:mil|k)\s*(?:a|até|at[ée]|\-)?\s*(?:R\$\s*)?(\d[\d.,]*)?/i,
    ]
    
    for (const pattern of salaryPatterns) {
      const match = text.match(pattern)
      if (match) {
        const val1 = match[1]?.replace(/\./g, '').replace(',', '.')
        const val2 = match[2]?.replace(/\./g, '').replace(',', '.')
        
        if (val1 && val2) {
          const num1 = parseFloat(val1)
          const num2 = parseFloat(val2)
          if (!isNaN(num1) && !isNaN(num2)) {
            const min = num1 < 1000 ? num1 * 1000 : num1
            const max = num2 < 1000 ? num2 * 1000 : num2
            newCriteria.salario = `R$ ${min.toLocaleString('pt-BR')} - R$ ${max.toLocaleString('pt-BR')}`
          }
        } else if (val1) {
          const num = parseFloat(val1)
          if (!isNaN(num)) {
            const value = num < 1000 ? num * 1000 : num
            newCriteria.salario = `R$ ${value.toLocaleString('pt-BR')}`
          }
        }
        break
      }
    }

    const idiomasPatterns = [
      { pattern: /ingl[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Inglês' },
      { pattern: /espanhol\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Espanhol' },
      { pattern: /franc[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Francês' },
      { pattern: /alem[aã]o\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Alemão' },
      { pattern: /italiano\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Italiano' },
      { pattern: /mandarim\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Mandarim' },
      { pattern: /japon[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Japonês' },
    ]
    
    const foundIdiomas: string[] = []
    idiomasPatterns.forEach(({ pattern, name }) => {
      if (pattern.test(text)) {
        foundIdiomas.push(name)
      }
    })
    
    if (foundIdiomas.length > 0) {
      const existingLower = new Set((newCriteria.idiomas || []).map(s => s.toLowerCase()))
      const uniqueNew = foundIdiomas.filter(s => !existingLower.has(s.toLowerCase()))
      newCriteria.idiomas = [...(newCriteria.idiomas || []), ...uniqueNew]
    }

    const experienciaPatterns = [
      /(\d+)\s*(?:\+\s*)?anos?\s*(?:de\s*)?experi[eê]ncia/i,
      /experi[eê]ncia\s*(?:m[ií]nima\s*(?:de\s*)?)?(\d+)\s*anos?/i,
      /m[ií]nimo\s*(?:de\s*)?(\d+)\s*anos?\s*(?:de\s*)?experi[eê]ncia/i,
      /(\d+)\s*anos?\s*(?:na\s+[áa]rea|atuando|de\s+mercado|de\s+carreira)/i,
    ]
    
    for (const pattern of experienciaPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        newCriteria.experienciaMinima = `${match[1]} anos`
        break
      }
    }

    const formacaoPatterns = [
      /(?:gradua[çc][aã]o|forma[çc][aã]o|superior|bacharelado|bacharel|licenciatura)\s+(?:em|de)\s+([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-]|\s+(?:com|ou|e\s+|$))/i,
      /(?:p[oó]s[\-\s]?gradua[çc][aã]o|mba|mestrado|doutorado|especializa[çc][aã]o)\s+(?:em|de)\s+([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-]|\s+(?:com|ou|e\s+|$))/i,
      /(?:superior\s+completo|n[ií]vel\s+superior)\s+(?:em\s+)?([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-]|\s+(?:com|ou|e\s+|$))/i,
      /(?:curso\s+superior|faculdade|universidade)\s+(?:de|em)\s+([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-]|\s+(?:com|ou|e\s+|$))/i,
    ]
    
    for (const pattern of formacaoPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const formacao = match[1].trim()
        if (formacao.length > 2 && formacao.length < 60) {
          const formatted = formacao.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
          if (!newCriteria.formacao.includes(formatted)) {
            newCriteria.formacao = [...newCriteria.formacao, formatted]
          }
        }
      }
    }

    const certificacaoPatterns = [
      /certifica[çc][aã]o\s+(?:em\s+)?([a-záàâãéèêíïóôõöúç\s\-]+?)(?:\s*[,.\-]|\s+(?:com|ou|e\s+|$))/i,
      /certificado\s+(?:de|em)\s+([a-záàâãéèêíïóôõöúç\s\-]+?)(?:\s*[,.\-]|\s+(?:com|ou|e\s+|$))/i,
      /\b(pmp|prince2|itil|cobit|cissp|cisa|aws\s+certified|azure\s+certified|gcp\s+certified|scrum\s+master|csm|psm|safe|togaf|six\s+sigma|lean|cfa|cpa|oab|crc|crea|crm)\b/i,
    ]
    
    for (const pattern of certificacaoPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const cert = match[1].trim()
        if (cert.length > 1 && cert.length < 50) {
          const formatted = cert.toUpperCase().length <= 5 ? cert.toUpperCase() : cert.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
          if (!newCriteria.certificacoes.includes(formatted)) {
            newCriteria.certificacoes = [...newCriteria.certificacoes, formatted]
          }
        }
      }
    }

    const ferramentasPatterns = [
      /(?:ferramentas?|tools?)\s*[:\-]?\s*([^.]+)/i,
      /(?:dom[ií]nio|conhecimento)\s+(?:em|de|das?\s+)?(?:ferramentas?\s+)?([^.]+)/i,
    ]
    
    for (const pattern of ferramentasPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const tools = match[1].split(/[,;e]/).map(t => t.trim()).filter(t => t.length > 1 && !['e', 'ou', 'de', 'da', 'do'].includes(t.toLowerCase()))
        tools.forEach(tool => {
          if (tool.length > 1 && tool.length < 30) {
            const formatted = tool.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
            if (!newCriteria.ferramentas.includes(formatted)) {
              newCriteria.ferramentas = [...newCriteria.ferramentas, formatted]
            }
          }
        })
      }
    }

    const responsabilidadesPatterns = [
      /(?:responsabilidades?|atribui[çc][oõ]es?|atividades?)\s*[:\-]\s*([^.]+(?:\.[^.]+)*)/i,
      /(?:vai|ir[áa]|dever[áa])\s+(?:ser\s+)?responsável\s+por\s+([^.]+)/i,
      /(?:entre\s+as\s+)?(?:principais?\s+)?(?:responsabilidades?|fun[çc][oõ]es?)\s*[:\-]?\s*([^.]+)/i,
    ]
    
    for (const pattern of responsabilidadesPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const items = match[1].split(/[;•\-\n]/).map(r => r.trim()).filter(r => r.length > 5 && r.length < 100)
        items.forEach(item => {
          const formatted = item.charAt(0).toUpperCase() + item.slice(1)
          if (!newCriteria.responsabilidades.includes(formatted)) {
            newCriteria.responsabilidades = [...newCriteria.responsabilidades, formatted]
          }
        })
      }
    }

    const affirmativePatterns = [
      /\b(?:vaga\s+)?afirmativ[oa]\s+(?:para|destinada?\s+[aà])?\s*((?:pessoas?\s+)?(?:negr[oa]s?|pret[oa]s?|pard[oa]s?))/i,
      /\b(?:vaga\s+)?afirmativ[oa]\s+(?:para|destinada?\s+[aà])?\s*((?:pessoas?\s+)?(?:com\s+defici[eê]ncia|pcd))/i,
      /\b(?:vaga\s+)?afirmativ[oa]\s+(?:para|destinada?\s+[aà])?\s*(mulheres?|g[eê]nero\s+feminino)/i,
      /\b(?:vaga\s+)?afirmativ[oa]\s+(?:para|destinada?\s+[aà])?\s*((?:pessoas?\s+)?(?:lgbtqi?\+?|lgbtqia?\+?))/i,
      /\b(?:vaga\s+)?afirmativ[oa]\s+(?:para|destinada?\s+[aà])?\s*((?:pessoas?\s+)?(?:ind[ií]genas?|povos?\s+origin[aá]rios?))/i,
      /\b(?:vaga\s+)?afirmativ[oa]\s+(?:para|destinada?\s+[aà])?\s*(pessoas?\s+(?:acima\s+de\s+)?\d+\s*(?:\+\s*)?anos?|50\+|profissionais?\s+s[eê]nior)/i,
      /\b(?:vaga\s+)?afirmativ[oa]\b/i,
    ]
    
    for (const pattern of affirmativePatterns) {
      const match = text.match(pattern)
      if (match) {
        newCriteria.isAffirmative = true
        if (match[1]) {
          const criteria = match[1].trim()
          newCriteria.affirmativeCriteriaPrimary = criteria.charAt(0).toUpperCase() + criteria.slice(1)
        }
        break
      }
    }
    
    if (newCriteria.isAffirmative === null) {
      if (/\bn[ãa]o\s+(?:[ée]\s+)?afirmativ[oa]\b/i.test(text) || /\bvaga\s+(?:n[ãa]o[\-\s])?afirmativ[oa]\s*(?:n[ãa]o|false)\b/i.test(text)) {
        newCriteria.isAffirmative = false
      }
    }

    const beneficiosPatterns = [
      /(?:benef[ií]cios?)\s*[:\-]\s*([^.]+)/i,
      /(?:oferecemos?|incluem?|pacote\s+de\s+benef[ií]cios?)\s*[:\-]?\s*([^.]+)/i,
    ]
    
    const knownBenefits = [
      'vale refeição', 'vale alimentação', 'vale transporte', 'plano de saúde', 'plano de saude',
      'plano odontológico', 'plano odontologico', 'seguro de vida', 'previdência privada',
      'previdencia privada', 'gympass', 'wellhub', 'totalpass', 'day off', 'auxílio home office',
      'auxilio home office', 'auxílio educação', 'auxilio educacao', 'participação nos lucros',
      'participacao nos lucros', 'plr', 'bônus', 'bonus', 'stock options', 'ações',
      'horário flexível', 'horario flexivel', 'short friday', 'sexta curta', 'vale cultura',
      'auxílio creche', 'auxilio creche', 'licença maternidade estendida', 'licença paternidade estendida',
    ]
    
    const foundBenefits: string[] = []
    
    knownBenefits.forEach(benefit => {
      const benefitPattern = new RegExp(`\\b${benefit.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
      if (benefitPattern.test(lowerText)) {
        foundBenefits.push(benefit.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
      }
    })
    
    for (const pattern of beneficiosPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const items = match[1].split(/[,;•\-]/).map(b => b.trim()).filter(b => b.length > 2)
        items.forEach(item => {
          if (!['e', 'ou', 'com', 'de', 'para', 'mais'].includes(item.toLowerCase())) {
            foundBenefits.push(item.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' '))
          }
        })
      }
    }
    
    if (foundBenefits.length > 0) {
      const existingLower = new Set((newCriteria.beneficiosMencionados || []).map(b => b.toLowerCase()))
      const uniqueNew = foundBenefits.filter(b => !existingLower.has(b.toLowerCase()))
      newCriteria.beneficiosMencionados = [...(newCriteria.beneficiosMencionados || []), ...uniqueNew]
    }

    const bonusPatterns = [
      /(?:b[oô]nus|bonus|bonifica[çc][aã]o)\s*(?:de\s+)?(?:at[ée]\s+)?(\d+)\s*(?:sal[áa]rios?|meses)/i,
      /(?:b[oô]nus|bonus|bonifica[çc][aã]o)\s*(?:de\s+)?(?:R\$\s*)?(\d[\d.,]*)/i,
      /(\d+)\s*(?:a\s+)?(\d+)?\s*sal[áa]rios?\s*(?:de\s+)?(?:b[oô]nus|bonus|bonifica[çc][aã]o)/i,
    ]
    
    for (const pattern of bonusPatterns) {
      const match = text.match(pattern)
      if (match) {
        if (match[2]) {
          newCriteria.bonus = `${match[1]} a ${match[2]} salários`
        } else if (match[1]) {
          newCriteria.bonus = match[1].includes('.') || match[1].includes(',') 
            ? `R$ ${match[1]}` 
            : `${match[1]} salários`
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

    return newCriteria
  }
