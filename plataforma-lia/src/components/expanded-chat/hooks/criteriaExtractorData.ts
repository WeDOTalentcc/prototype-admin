export const commonJobTitles = [
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

export const areaKeywordMap: Record<string, string> = {
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

export const techSkillsList = [
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

export const softSkillsList = [
  'liderança', 'lideranca', 'gestão de pessoas', 'gestao de pessoas', 'comunicação', 'comunicacao',
  'trabalho em equipe', 'proatividade', 'pro-atividade', 'organização', 'organizacao',
  'negociação', 'negociacao', 'resiliência', 'resiliencia', 'empatia', 'criatividade',
  'pensamento crítico', 'resolução de problemas', 'adaptabilidade', 'flexibilidade',
  'autonomia', 'iniciativa', 'colaboração', 'colaboracao', 'foco em resultados',
  'orientação para resultados', 'relacionamento interpessoal', 'inteligência emocional',
  'tomada de decisão', 'visão estratégica', 'visao estrategica', 'gestão de conflitos',
  'mentoria', 'coaching', 'feedback', 'influência', 'influencia', 'persuasão', 'persuasao'
]

export const knownCities: Record<string, string> = {
  'são paulo': 'São Paulo, SP', 'sao paulo': 'São Paulo, SP',
  'rio de janeiro': 'Rio de Janeiro, RJ', 'belo horizonte': 'Belo Horizonte, MG',
  'curitiba': 'Curitiba, PR', 'porto alegre': 'Porto Alegre, RS',
  'brasília': 'Brasília, DF', 'brasilia': 'Brasília, DF',
  'salvador': 'Salvador, BA', 'recife': 'Recife, PE', 'fortaleza': 'Fortaleza, CE',
  'campinas': 'Campinas, SP',
  'florianópolis': 'Florianópolis, SC', 'florianopolis': 'Florianópolis, SC',
  'goiânia': 'Goiânia, GO', 'goiania': 'Goiânia, GO',
  'manaus': 'Manaus, AM', 'belém': 'Belém, PA', 'belem': 'Belém, PA',
  'vitória': 'Vitória, ES', 'vitoria': 'Vitória, ES', 'natal': 'Natal, RN',
  'joão pessoa': 'João Pessoa, PB', 'joao pessoa': 'João Pessoa, PB',
  'maceió': 'Maceió, AL', 'maceio': 'Maceió, AL',
  'cuiabá': 'Cuiabá, MT', 'cuiaba': 'Cuiabá, MT',
  'campo grande': 'Campo Grande, MS', 'teresina': 'Teresina, PI',
  'são luís': 'São Luís, MA', 'sao luis': 'São Luís, MA',
  'aracaju': 'Aracaju, SE',
  'ribeirão preto': 'Ribeirão Preto, SP', 'ribeirao preto': 'Ribeirão Preto, SP',
  'santos': 'Santos, SP', 'sorocaba': 'Sorocaba, SP',
  'são josé dos campos': 'São José dos Campos, SP', 'sao jose dos campos': 'São José dos Campos, SP',
  'londrina': 'Londrina, PR', 'joinville': 'Joinville, SC',
  'blumenau': 'Blumenau, SC',
  'uberlândia': 'Uberlândia, MG', 'uberlandia': 'Uberlândia, MG'
}

export const stateAbbrev: Record<string, string> = {
  'sp': 'São Paulo, SP', 'rj': 'Rio de Janeiro, RJ', 'mg': 'Belo Horizonte, MG',
  'pr': 'Curitiba, PR', 'rs': 'Porto Alegre, RS', 'df': 'Brasília, DF',
  'ba': 'Salvador, BA', 'pe': 'Recife, PE', 'ce': 'Fortaleza, CE',
  'sc': 'Florianópolis, SC', 'go': 'Goiânia, GO', 'am': 'Manaus, AM',
  'pa': 'Belém, PA', 'es': 'Vitória, ES', 'rn': 'Natal, RN'
}

export const knownCertifications = [
  'aws', 'azure', 'gcp', 'google cloud', 'pmp', 'scrum master', 'csm', 'psm', 'safe', 'itil',
  'cissp', 'cisa', 'ceh', 'comptia', 'ccna', 'ccnp', 'oracle', 'java certified', 'microsoft certified',
  'cpa', 'cpa-10', 'cpa-20', 'cga', 'crc', 'oab', 'cfc', 'crea', 'cfp', 'cea', 'cnpi',
  'iso 9001', 'iso 27001', 'six sigma', 'lean', 'green belt', 'black belt', 'yellow belt',
  'tableau certified', 'salesforce certified', 'hubspot', 'google analytics', 'meta blueprint',
]

export const knownTools = [
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

export const beneficiosKeywords = [
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

export const idiomasNormalize: Record<string, string> = {
  'ingles': 'Inglês', 'inglês': 'Inglês', 'english': 'Inglês',
  'espanhol': 'Espanhol', 'spanish': 'Espanhol',
  'frances': 'Francês', 'francês': 'Francês', 'french': 'Francês',
  'alemao': 'Alemão', 'alemão': 'Alemão', 'german': 'Alemão',
  'italiano': 'Italiano', 'italian': 'Italiano',
  'portugues': 'Português', 'português': 'Português', 'portuguese': 'Português',
  'mandarim': 'Mandarim', 'chines': 'Chinês', 'chinês': 'Chinês', 'chinese': 'Chinês',
  'japones': 'Japonês', 'japonês': 'Japonês', 'japanese': 'Japonês',
}

export const nivelNormalize: Record<string, string> = {
  'avancado': 'Avançado', 'avançado': 'Avançado',
  'fluente': 'Fluente', 'nativo': 'Nativo',
  'intermediario': 'Intermediário', 'intermediário': 'Intermediário',
  'basico': 'Básico', 'básico': 'Básico',
  'c1': 'C1', 'c2': 'C2', 'b1': 'B1', 'b2': 'B2', 'a1': 'A1', 'a2': 'A2',
}

export const seniorityMap: Record<string, string> = {
  'junior': 'Júnior', 'júnior': 'Júnior', 'jr': 'Júnior',
  'pleno': 'Pleno', 'pl': 'Pleno',
  'senior': 'Sênior', 'sênior': 'Sênior', 'sr': 'Sênior',
  'especialista': 'Especialista',
  'trainee': 'Trainee',
  'estagiário': 'Estagiário', 'estagiario': 'Estagiário', 'estágio': 'Estágio', 'estagio': 'Estágio'
}
