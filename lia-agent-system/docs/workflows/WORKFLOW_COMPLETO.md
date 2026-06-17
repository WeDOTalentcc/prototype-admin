# Workflow Completo LIA - Documentação Detalhada

## Visão Geral

O workflow completo da LIA consiste em **FASE 0 + 27 Etapas** organizadas em 7 fases:

| Fase | Etapas | Descrição | Status |
|------|--------|-----------|--------|
| **FASE 0** | 0.1 - 0.6 | Setup & Calibração de Perfil Ideal | 🔴 Pendente |
| **FASE 1** | 1 - 13 | Criação da Vaga | ✅ Implementado |
| **FASE 2** | 14 - 17 | Sourcing Automatizado | 🟡 Parcial |
| **FASE 3** | 18 - 19 | Engajamento de Candidatos | 🟡 Parcial |
| **FASE 4** | 20 - 22 | Triagem WSI | 🟡 Parcial |
| **FASE 5** | 23 - 25 | Decisão e Agendamento | 🟡 Parcial |
| **FASE 6** | 26 - 27 | Fechamento | 🟡 Parcial |

---

## FASE 0: Setup & Calibração de Perfil Ideal

### Etapa 0.1: Company Setup Node

**Objetivo:** Configurar a empresa na plataforma com todas as informações necessárias para automatizar o processo de recrutamento.

**Inputs Esperados:**
- Nome da empresa
- Setor/indústria
- Porte (pequena, média, grande)
- Lista de áreas/departamentos
- Benefícios oferecidos por área e/ou nível
- Credenciais de integração (ATS, Workforce Planning)

**Outputs Esperados:**
- Perfil da empresa cadastrado
- Catálogo de benefícios configurado
- Integrações ativadas

**Critérios de Sucesso:**
- Todos os campos obrigatórios preenchidos
- Pelo menos uma integração configurada (ATS ou manual)
- Benefícios cadastrados para pelo menos uma área

**Comportamento da LIA:**
```
LIA: "Olá! Sou a LIA, sua assistente de recrutamento. Antes de começarmos 
a trabalhar juntos, preciso conhecer melhor a [Empresa]. Isso me ajudará 
a encontrar os melhores candidatos para vocês.

Vamos começar? Primeiro, me conte: quais são as principais áreas da empresa 
que costumam contratar?"
```

**Comportamento do Recrutador:**
- Fornece informações sobre a empresa
- Configura integrações
- Cadastra benefícios

**Exemplos de Diálogo:**

*Exemplo 1 - Início do Setup:*
```
RECRUTADOR: "Olá LIA, acabamos de contratar a WeDOTalent"

LIA: "Que ótimo ter vocês aqui! Para eu poder ajudar da melhor forma, 
preciso conhecer a empresa. Vou te fazer algumas perguntas rápidas:

1. Qual o nome oficial da empresa?
2. Em qual setor vocês atuam?
3. Aproximadamente quantos funcionários têm hoje?

Pode me contar?"

RECRUTADOR: "Somos a TechCorp, atuamos em tecnologia, temos cerca de 500 funcionários"

LIA: "Perfeito! TechCorp, setor de tecnologia, ~500 colaboradores. 
Agora me conta: quais são as principais áreas que costumam contratar? 
Por exemplo: Engenharia, Produto, Comercial..."
```

*Exemplo 2 - Cadastro de Benefícios:*
```
LIA: "Agora vamos falar de benefícios. Isso é importante porque vou 
usar essas informações automaticamente quando você abrir uma vaga.

Vocês têm benefícios diferentes por área ou é igual para todos?"

RECRUTADOR: "Temos alguns benefícios gerais e alguns específicos para tech"

LIA: "Entendi! Vamos cadastrar primeiro os benefícios gerais que valem 
para toda empresa. Me lista eles?"

RECRUTADOR: "VR de R$35/dia, plano de saúde Bradesco, VT, Gympass"

LIA: "Anotado! E para a área de Tech, quais benefícios extras vocês oferecem?"

RECRUTADOR: "Auxílio home office de R$200 e budget de educação de R$500/mês"

LIA: "Perfeito! Já cadastrei:

📋 Benefícios Gerais:
- VR: R$35/dia
- Plano de Saúde: Bradesco
- VT: Integral
- Gympass: Incluso

🖥️ Benefícios Tech (adicional):
- Auxílio Home Office: R$200/mês
- Budget Educação: R$500/mês

Está correto?"
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Coleta e estrutura informações da empresa
- **ATS Integrator Agent**: Configura conexões com sistemas externos

**Status:** 🔴 Não implementado

**Pendências:**
- [ ] Schema `CompanySetupState`
- [ ] Node `company_setup_node`
- [ ] Modelo de dados para benefícios por área/nível
- [ ] UI de configuração da empresa
- [ ] Integração com ATS para importar dados

---

### Etapa 0.2: Culture Discovery Node

**Objetivo:** Analisar automaticamente o website e materiais da empresa para extrair cultura, visão, missão e valores.

**Inputs Esperados:**
- URL do website da empresa
- Materiais adicionais (PDF de cultura, handbook)
- LinkedIn da empresa (opcional)

**Outputs Esperados:**
- Visão da empresa
- Missão da empresa
- Valores identificados
- Tom de comunicação
- Palavras-chave culturais
- Proposta de valor ao colaborador

**Critérios de Sucesso:**
- Pelo menos 3 valores identificados
- Tom de comunicação definido
- Recruiter valida as informações extraídas

**Comportamento da LIA:**
```
LIA: "Agora vou analisar a cultura da empresa. Me passa o site principal 
da [Empresa] que vou extrair as informações automaticamente."
```

**Comportamento do Recrutador:**
- Fornece URL do website
- Valida informações extraídas
- Complementa se necessário

**Exemplos de Diálogo:**

*Exemplo 1 - Análise de Website:*
```
RECRUTADOR: "Nosso site é www.techcorp.com.br"

LIA: "Perfeito! Analisando o site da TechCorp...

🔍 Encontrei as seguintes informações:

📌 MISSÃO:
'Transformar negócios através da tecnologia'

🎯 VISÃO:
'Ser referência em inovação na América Latina até 2030'

💡 VALORES IDENTIFICADOS:
1. Inovação - mencionado 12x no site
2. Colaboração - mencionado 8x
3. Excelência - mencionado 6x
4. Diversidade - mencionado 5x

🗣️ TOM DE COMUNICAÇÃO:
Informal e inspirador, foco em crescimento e desafios

Isso está alinhado com a realidade da empresa?"

RECRUTADOR: "Sim, mas adiciona 'Autonomia' que é muito forte aqui"

LIA: "Adicionado! 'Autonomia' agora faz parte dos valores core. 
Isso vai me ajudar a identificar candidatos que valorizam 
independência e ownership."
```

*Exemplo 2 - Proposta de Valor:*
```
LIA: "Baseado na análise, identifiquei a Proposta de Valor ao Colaborador:

🏆 EVP (Employee Value Proposition):

'Na TechCorp, você terá:
- Projetos desafiadores com impacto real
- Autonomia para inovar
- Ambiente colaborativo e diverso
- Crescimento acelerado na carreira'

Posso usar essa proposta nas comunicações com candidatos?"

RECRUTADOR: "Sim, ficou ótimo!"
```

**Agentes Envolvidos:**
- **Analytics Agent**: Realiza web scraping e análise de texto
- **Job Planner Agent**: Estrutura informações culturais

**Status:** 🔴 Não implementado

**Pendências:**
- [ ] Serviço de web scraping para análise de sites
- [ ] Modelo de NLP para extração de cultura/valores
- [ ] Schema `CompanyCultureState`
- [ ] Node `culture_discovery_node`

---

### Etapa 0.3: Historical Analysis Node

**Objetivo:** Conectar ao ATS do cliente e analisar histórico de contratações dos últimos 12 meses para identificar padrões.

**Inputs Esperados:**
- Credenciais do ATS (Gupy, Pandapé, etc.)
- Período de análise (default: 12 meses)
- Áreas de interesse

**Outputs Esperados:**
- Lista de contratações realizadas
- Lista de candidatos entrevistados (aprovados e rejeitados)
- Métricas: tempo médio de contratação, taxa de conversão
- Dados brutos para pattern recognition

**Critérios de Sucesso:**
- Conexão com ATS estabelecida
- Mínimo de 10 contratações analisadas
- Dados suficientes para análise estatística

**Comportamento da LIA:**
```
LIA: "Para eu aprender o que funciona para a TechCorp, preciso analisar 
as contratações anteriores. Vocês usam algum ATS como Gupy ou Pandapé?"
```

**Comportamento do Recrutador:**
- Autoriza conexão com ATS
- Fornece credenciais ou convite de integração

**Exemplos de Diálogo:**

*Exemplo 1 - Conexão com ATS:*
```
RECRUTADOR: "Usamos Gupy"

LIA: "Ótimo! O Gupy é bem completo. Para conectar, você pode:

1. Me enviar um convite de integração pelo painel do Gupy
2. Ou me passar a API Key (mais técnico)

Qual prefere?"

RECRUTADOR: "Vou enviar o convite"

LIA: "Perfeito! Assim que receber, vou importar os dados dos últimos 
12 meses de contratações e entrevistas. Isso me permitirá entender 
padrões de sucesso na TechCorp."

[... após integração ...]

LIA: "Conexão estabelecida! Importei dados de:
- 47 vagas fechadas
- 312 candidatos entrevistados
- 52 contratações realizadas
- Taxa de conversão: 16.7%

Agora vou analisar os padrões. Me dá alguns minutos..."
```

*Exemplo 2 - Análise Manual (sem ATS):*
```
RECRUTADOR: "Não usamos ATS, é tudo em planilha"

LIA: "Sem problemas! Podemos fazer de outra forma. Você consegue me 
enviar uma planilha com os últimos contratados? Preciso de:

- Nome do cargo
- Data de contratação
- Currículo ou LinkedIn (se tiver)
- Área da vaga

Outra opção: posso te fazer um questionário sobre os perfis que 
costumam dar certo. Qual prefere?"

RECRUTADOR: "Prefiro o questionário"

LIA: "Perfeito! Vamos lá então. Pensa nos seus últimos 5 contratados 
que você considera 'acertos'. Me conta: eles tinham algo em comum 
em termos de formação?"
```

**Agentes Envolvidos:**
- **ATS Integrator Agent**: Conexão e importação de dados
- **Analytics Agent**: Processamento e estruturação dos dados

**Status:** 🔴 Não implementado

**Pendências:**
- [ ] Integração com Gupy API
- [ ] Integração com Pandapé API
- [x] Integração com Merge.dev (unified ATS)
- [ ] Schema `ATSHistoricalData`
- [ ] Node `historical_analysis_node`
- [ ] Fallback para análise manual (questionário)

---

### Etapa 0.4: Pattern Recognition Node

**Objetivo:** Identificar padrões nos candidatos contratados que podem prever sucesso na empresa.

**Inputs Esperados:**
- Dados históricos de contratações (da etapa 0.3)
- Currículos dos candidatos contratados
- Avaliações de desempenho (se disponível)

**Outputs Esperados:**
- Padrões de formação acadêmica
- Padrões de estabilidade curricular
- Perfil de empresas anteriores
- Competências técnicas comuns
- Competências comportamentais comuns
- Outros padrões identificados

**Critérios de Sucesso:**
- Mínimo de 5 padrões identificados com confiança > 70%
- Padrões validados pelo recrutador

**Comportamento da LIA:**
```
LIA: "Analisei 52 contratações e encontrei padrões interessantes. 
Vou te mostrar o que os profissionais bem-sucedidos na TechCorp 
têm em comum."
```

**Comportamento do Recrutador:**
- Valida padrões identificados
- Adiciona insights qualitativos
- Ajusta pesos de importância

**Exemplos de Diálogo:**

*Exemplo 1 - Apresentação de Padrões:*
```
LIA: "Analisei os 52 contratados dos últimos 12 meses. Encontrei 
padrões bem claros:

📚 FORMAÇÃO:
- 78% têm graduação em áreas de exatas
- 45% têm pós-graduação/MBA
- Instituições mais comuns: USP, Unicamp, PUC

⏱️ ESTABILIDADE:
- Tempo médio em cada empresa: 2.8 anos
- 85% ficaram pelo menos 2 anos no emprego anterior
- Média de 3.2 empresas na carreira

🏢 EMPRESAS ANTERIORES:
- 67% vieram de startups ou scale-ups
- 52% passaram por big techs (Google, Meta, etc.)
- Setores: 72% tech, 18% financeiro, 10% outros

💡 COMPETÊNCIAS TÉCNICAS RECORRENTES:
- Python (68%)
- Cloud (AWS/GCP) (61%)
- Metodologias ágeis (89%)

🧠 PERFIL COMPORTAMENTAL:
- Alta autonomia
- Perfil hands-on
- Boa comunicação

Isso faz sentido para você?"

RECRUTADOR: "Sim, faz muito sentido! Mas não necessariamente precisamos 
de pós, isso é mais nice to have"

LIA: "Anotado! Vou reduzir o peso da pós-graduação no scoring. 
Algo mais que você percebe nos seus melhores contratados que 
talvez eu não tenha captado nos dados?"

RECRUTADOR: "Pessoas que têm projetos pessoais ou open source costumam 
ir muito bem aqui"

LIA: "Excelente insight! Vou adicionar 'contribuições open source' 
e 'projetos pessoais' como indicadores positivos. Isso é exatamente 
o tipo de padrão qualitativo que eu não conseguiria identificar 
sozinha nos dados."
```

*Exemplo 2 - Padrões por Área:*
```
LIA: "Percebi que os padrões variam por área. Quer que eu detalhe 
por departamento?"

RECRUTADOR: "Sim, mostra Engenharia e Produto"

LIA: "📊 ENGENHARIA DE SOFTWARE:
- 92% com graduação em Computação/Eng. de Software
- Tempo médio: 3.1 anos por empresa
- 78% vieram de startups
- Skills top: Python, React, AWS

📊 PRODUTO:
- 65% com graduação variada (Eng, Admin, Design)
- 40% têm MBA
- Tempo médio: 2.3 anos por empresa
- 55% vieram de consultorias ou big techs
- Skills top: SQL, Figma, metodologias ágeis

Interessante: Engenharia prefere estabilidade, Produto aceita 
mais rotatividade. Faz sentido?"
```

**Agentes Envolvidos:**
- **Analytics Agent**: Análise estatística e machine learning
- **Job Planner Agent**: Estruturação dos padrões

**Status:** 🔴 Não implementado

**Pendências:**
- [ ] Modelo de ML para pattern recognition
- [ ] Schema `PatternAnalysisState`
- [ ] Node `pattern_recognition_node`
- [ ] Algoritmo de scoring baseado em padrões

---

### Etapa 0.5: Ideal Profile Builder Node

**Objetivo:** Consolidar todas as análises em um "Perfil Ideal" documentado que servirá de base para scoring e matching.

**Inputs Esperados:**
- Cultura da empresa (etapa 0.2)
- Padrões identificados (etapa 0.4)
- Ajustes do recrutador

**Outputs Esperados:**
- "Company DNA Profile" documentado
- Critérios obrigatórios vs. desejáveis
- Pesos para cada critério no scoring
- Triggers de match/no-match

**Critérios de Sucesso:**
- Perfil aprovado pelo recrutador
- Mínimo de 10 critérios definidos
- Pesos configurados

**Comportamento da LIA:**
```
LIA: "Com base em tudo que analisamos, vou criar o 'DNA de Contratação' 
da TechCorp. Esse perfil vai guiar todas as minhas avaliações de 
candidatos daqui pra frente."
```

**Comportamento do Recrutador:**
- Valida o perfil consolidado
- Ajusta critérios e pesos
- Aprova para uso

**Exemplos de Diálogo:**

*Exemplo 1 - Apresentação do DNA:*
```
LIA: "Pronto! Criei o DNA de Contratação da TechCorp. Veja:

🧬 COMPANY DNA PROFILE - TECHCORP

📋 CRITÉRIOS OBRIGATÓRIOS:
1. Graduação em área de exatas (eliminatório)
2. Mínimo 2 anos de experiência relevante
3. Inglês intermediário ou superior
4. Experiência com metodologias ágeis

⭐ CRITÉRIOS DESEJÁVEIS (com pesos):
1. Passagem por startups/scale-ups (peso: 20%)
2. Projetos pessoais/open source (peso: 15%)
3. Estabilidade > 2 anos por empresa (peso: 15%)
4. Pós-graduação/MBA (peso: 10%)
5. Experiência com cloud (peso: 15%)
6. Perfil hands-on (peso: 15%)
7. Big Five: alta abertura a experiências (peso: 10%)

🚫 RED FLAGS (eliminatórios):
- Mais de 3 empregos com menos de 1 ano
- Mentiras no currículo
- Indisponibilidade para modelo híbrido

Esse perfil está alinhado com o que vocês buscam?"

RECRUTADOR: "Quase! Remove a pós-graduação como critério e aumenta 
o peso de projetos pessoais"

LIA: "Feito! Removi pós-graduação e projetos pessoais agora tem peso 
de 25%. Esse será o padrão para todas as vagas de tech. Posso 
ajustar para áreas específicas quando você abrir vagas."
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Consolidação e estruturação
- **Analytics Agent**: Cálculo de pesos e scoring

**Status:** 🔴 Não implementado

**Pendências:**
- [ ] Schema `IdealProfileState`
- [ ] Node `ideal_profile_builder_node`
- [ ] UI para visualização/edição do perfil
- [ ] Persistência do perfil por empresa

---

### Etapa 0.6: Profile Validation Node

**Objetivo:** Obter validação formal do recrutador antes de ativar o perfil para uso em avaliações.

**Inputs Esperados:**
- Perfil ideal consolidado
- Histórico de ajustes

**Outputs Esperados:**
- Perfil validado e ativado
- Timestamp de aprovação
- Registro de quem aprovou

**Critérios de Sucesso:**
- Aprovação explícita do recrutador
- Perfil ativado no sistema

**Comportamento da LIA:**
```
LIA: "Antes de começarmos a usar esse perfil, preciso da sua 
aprovação formal. Depois disso, vou aplicar esses critérios 
em todas as análises de candidatos."
```

**Exemplos de Diálogo:**

```
LIA: "Resumo final do DNA de Contratação TechCorp:

✅ 4 critérios obrigatórios
✅ 6 critérios desejáveis com pesos
✅ 3 red flags definidos
✅ Perfil cultural mapeado

Você confirma a ativação deste perfil? A partir de agora, vou 
usar esses critérios para avaliar todos os candidatos.

[APROVAR] [REVISAR] [CANCELAR]"

RECRUTADOR: "Aprovar"

LIA: "Perfil ativado com sucesso! 🎉

Agora estou pronta para te ajudar a encontrar os melhores 
candidatos para a TechCorp. Quando quiser abrir uma vaga, 
é só me avisar!

💡 Dica: Você pode revisar ou atualizar esse perfil a qualquer 
momento. Recomendo fazermos uma revisão a cada 6 meses."
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Registro da validação

**Status:** 🔴 Não implementado

**Pendências:**
- [ ] Node `profile_validation_node`
- [ ] Sistema de versionamento de perfis
- [ ] Audit log de alterações

---

## FASE 1: Criação da Vaga (Etapas 1-13)

### Etapa 1: Onboarding Node

**Objetivo:** Apresentar ao recrutador a jornada completa de abertura de vaga e coletar tipo de vaga.

**Inputs Esperados:**
- Mensagem inicial do recrutador solicitando abertura de vaga

**Outputs Esperados:**
- Confirmação do recrutador para iniciar
- Tipo de vaga (nova ou substituição)

**Critérios de Sucesso:**
- Recrutador entendeu o processo
- Confirmou desejo de continuar

**Comportamento da LIA:**
```
LIA: "Vamos abrir uma nova vaga juntos! O processo tem 13 etapas 
e leva cerca de 10 minutos. Vou te guiar em cada uma delas.

Essa vaga é para:
1. Nova posição (headcount novo)
2. Substituição (alguém saiu/vai sair)

Qual das opções?"
```

**Exemplos de Diálogo:**

*Exemplo 1 - Início Proativo (via Workforce Planning):*
```
LIA: "Bom dia, João! 🌅

Detectei que há uma vaga programada para abertura esta semana:

📋 VAGA PROGRAMADA:
- Cargo: Desenvolvedor Backend Sênior
- Área: Engenharia de Software
- Gestor: Maria Silva
- Previsão de início: 01/02/2024
- Headcount: Aprovado (Budget ID: #2024-127)

Quer que eu inicie o processo de abertura dessa vaga agora?"

RECRUTADOR: "Sim, vamos lá"

LIA: "Perfeito! Já puxei as informações básicas do workforce planning. 
Vou te guiar pelas 13 etapas de configuração da vaga.

Primeiro, confirma: o cargo é exatamente 'Desenvolvedor Backend Sênior' 
ou quer ajustar o título?"
```

*Exemplo 2 - Início Manual:*
```
RECRUTADOR: "LIA, preciso abrir uma vaga de Product Manager"

LIA: "Opa, vamos lá! Antes de começarmos, deixa eu te explicar:

🗺️ NOSSA JORNADA (13 etapas):
1. Informações básicas
2. Remuneração
3. Estrutura organizacional
4. Requisitos técnicos
5. Estratégia de sourcing
6. Competências comportamentais
7. Fluxo de entrevistas
8. Governança
9. Templates de comunicação
10. Descrição da vaga
11. Publicação

Leva cerca de 10-15 minutos. Vamos começar?"

RECRUTADOR: "Sim"

LIA: "Ótimo! Primeiro: essa vaga de Product Manager é uma posição 
nova ou substituição de alguém?"
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Conduz o onboarding

**Status:** ✅ Implementado

**Pendências:**
- [ ] Integração com Workforce Planning para detecção proativa
- [ ] Exibição visual da jornada no frontend

---

### Etapa 2: Basics Collector

**Objetivo:** Coletar informações básicas da vaga: título, senioridade, modelo de trabalho, confidencialidade.

**Inputs Esperados:**
- Tipo de vaga (da etapa 1)
- Título do cargo
- Nível de senioridade
- Modelo de trabalho
- Confidencialidade

**Outputs Esperados:**
- `job_title`: string
- `seniority`: enum (júnior, pleno, sênior, especialista, coordenador, gerente, diretor)
- `work_model`: enum (presencial, híbrido, remoto)
- `is_confidential`: boolean
- `confidential_company_alias`: string (se confidencial)

**Critérios de Sucesso:**
- Todos os campos obrigatórios preenchidos
- Valores válidos para enums

**Comportamento da LIA:**
```
LIA: "Me conta mais sobre a vaga:
1. Qual o título exato do cargo?
2. Qual o nível de senioridade?
3. Qual o modelo de trabalho?"
```

**Exemplos de Diálogo:**

```
RECRUTADOR: "Product Manager Sênior, híbrido"

LIA: "Anotado! Product Manager Sênior, modelo híbrido.

Mais uma pergunta: essa vaga é confidencial? Às vezes empresas 
preferem não divulgar o nome em vagas estratégicas."

RECRUTADOR: "Não, pode divulgar a TechCorp"

LIA: "Perfeito! Resumindo:

📋 INFORMAÇÕES BÁSICAS:
- Cargo: Product Manager Sênior
- Senioridade: Sênior
- Modelo: Híbrido
- Confidencial: Não

Correto? Posso seguir para remuneração?"
```

*Exemplo - Vaga Confidencial:*
```
RECRUTADOR: "Sim, é confidencial"

LIA: "Entendido! Para vagas confidenciais, uso um nome genérico 
nas publicações. Algumas opções:

1. 'Empresa líder em tecnologia'
2. 'Scale-up em forte crescimento'
3. 'Multinacional do setor tech'

Qual prefere? Ou me sugere outra descrição."

RECRUTADOR: "Scale-up em forte crescimento"

LIA: "Perfeito! A vaga será publicada como 'Product Manager Sênior 
em Scale-up em forte crescimento'. O nome TechCorp só será 
revelado na entrevista."
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Coleta e validação dos dados

**Status:** ✅ Implementado

**Pendências:** Nenhuma

---

### Etapa 3: Remuneration Collector

**Objetivo:** Definir faixa salarial e pacote de benefícios da vaga.

**Inputs Esperados:**
- Faixa salarial (mínimo e máximo)
- Moeda
- Tipo (CLT, PJ)
- Benefícios específicos da vaga

**Outputs Esperados:**
- `salary_min`: number
- `salary_max`: number
- `currency`: string
- `contract_type`: enum
- `benefits`: array

**Critérios de Sucesso:**
- Faixa salarial definida
- Faixa dentro do benchmark de mercado (±20%)
- Benefícios listados

**Comportamento da LIA:**
```
LIA: "Agora vamos falar de remuneração. Qual a faixa salarial 
dessa vaga?"
```

**Exemplos de Diálogo:**

```
RECRUTADOR: "Entre 18 e 22 mil CLT"

LIA: "Anotado! R$ 18.000 a R$ 22.000 CLT.

📊 COMPARAÇÃO COM MERCADO:
Para Product Manager Sênior em São Paulo:
- Mediana: R$ 19.500
- P25: R$ 16.000
- P75: R$ 24.000

Sua faixa está bem alinhada com o mercado! 👍

Sobre benefícios, já temos cadastrados os benefícios padrão da TechCorp:
- VR: R$35/dia
- Plano de saúde Bradesco
- VT integral
- Gympass

Quer adicionar algo específico para essa vaga?"

RECRUTADOR: "Adiciona bônus anual de até 2 salários"

LIA: "Adicionado! Pacote completo:

💰 REMUNERAÇÃO:
- Faixa: R$ 18.000 - R$ 22.000 (CLT)
- Bônus: Até 2 salários/ano

🎁 BENEFÍCIOS:
- VR: R$35/dia
- Plano de saúde Bradesco
- VT integral
- Gympass
- Bônus anual

Está correto?"
```

*Exemplo - Faixa Abaixo do Mercado:*
```
RECRUTADOR: "Entre 12 e 15 mil CLT"

LIA: "Hmm, percebi que essa faixa está abaixo do mercado:

📊 COMPARAÇÃO:
- Sua faixa: R$ 12.000 - R$ 15.000
- Mediana mercado: R$ 19.500
- Diferença: -23% a -38%

⚠️ Isso pode dificultar atrair candidatos qualificados.

Sugestões:
1. Aumentar para R$ 17.000 - R$ 20.000
2. Manter, mas destacar benefícios diferenciados
3. Manter e ajustar expectativa de tempo de contratação

O que prefere fazer?"
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Coleta dados
- **Analytics Agent**: Fornece benchmark de mercado

**Status:** ✅ Implementado

**Pendências:**
- [ ] Integração com base de dados salariais (Glassdoor, Levels.fyi)
- [ ] Usar benefícios cadastrados no Company Setup (Fase 0)

---

### Etapa 4: Org Structure Collector

**Objetivo:** Definir estrutura organizacional: gestor direto, tamanho do time, composição.

**Inputs Esperados:**
- Nome do gestor direto
- Email do gestor
- Tamanho do time atual
- Composição do time

**Outputs Esperados:**
- `hiring_manager`: object (name, email)
- `team_size`: number
- `team_composition`: string
- `reports_to`: string

**Critérios de Sucesso:**
- Gestor identificado com email válido
- Estrutura do time definida

**Comportamento da LIA:**
```
LIA: "Quem será o gestor direto dessa pessoa? E como é o time hoje?"
```

**Exemplos de Diálogo:**

```
RECRUTADOR: "A Maria Silva, que é Head de Produto"

LIA: "Maria Silva, Head de Produto. Você tem o email dela para 
eu incluir nas comunicações?"

RECRUTADOR: "maria.silva@techcorp.com.br"

LIA: "Perfeito! E como é o time de Produto hoje? Quantas pessoas 
e quais funções?"

RECRUTADOR: "Hoje são 5 PMs, essa será a sexta pessoa"

LIA: "Entendi! Estrutura:

🏢 ESTRUTURA ORGANIZACIONAL:
- Gestor: Maria Silva (Head de Produto)
- Email: maria.silva@techcorp.com.br
- Time atual: 5 PMs
- Após contratação: 6 PMs

Essa pessoa terá reports diretos ou será IC (individual contributor)?"

RECRUTADOR: "IC por enquanto, mas pode liderar squad no futuro"

LIA: "Anotado! Vou mencionar potencial de liderança na descrição 
da vaga. Isso atrai candidatos com ambição de crescimento."
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Coleta e estruturação

**Status:** ✅ Implementado

**Pendências:** Nenhuma

---

### Etapa 5: Technical Matrix Collector

**Objetivo:** Definir requisitos técnicos com níveis de proficiência.

**Inputs Esperados:**
- Lista de skills técnicas
- Nível de proficiência para cada skill
- Classificação: obrigatório vs. desejável

**Outputs Esperados:**
- `technical_requirements`: array de objetos com skill, level, required

**Critérios de Sucesso:**
- Mínimo 3 skills definidas
- Cada skill com nível de proficiência
- Pelo menos 1 skill obrigatória

**Comportamento da LIA:**
```
LIA: "Quais são os requisitos técnicos para essa vaga? Me conta 
as principais skills e eu te ajudo a definir os níveis."
```

**Exemplos de Diálogo:**

```
RECRUTADOR: "Precisa saber SQL, ter experiência com produto digital, 
metodologias ágeis"

LIA: "Vou organizar em uma matriz técnica. Para cada skill, me 
diz se é obrigatório ou desejável, e o nível mínimo esperado:

📊 MATRIZ TÉCNICA:

| Skill | Obrigatório? | Nível Mínimo |
|-------|--------------|--------------|
| SQL | ? | Básico/Intermediário/Avançado |
| Produto Digital | ? | Jr/Pl/Sr |
| Metodologias Ágeis | ? | Básico/Intermediário/Avançado |

Me ajuda a preencher?"

RECRUTADOR: "SQL é desejável, nível intermediário. Produto digital 
é obrigatório, nível sênior. Ágil é obrigatório, avançado."

LIA: "Perfeito! Matriz completa:

📊 REQUISITOS TÉCNICOS:

OBRIGATÓRIOS:
✅ Produto Digital - Nível Sênior (3+ anos)
✅ Metodologias Ágeis - Avançado (Scrum Master/PO certificado)

DESEJÁVEIS:
⭐ SQL - Intermediário (queries complexas)

Quer adicionar mais algum requisito?"

RECRUTADOR: "Adiciona Figma como desejável"

LIA: "Adicionado! Figma - Desejável, nível básico (protótipos simples)."
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Coleta e estruturação
- **CV Screener Agent**: Usará essa matriz para scoring

**Status:** ✅ Implementado

**Pendências:**
- [ ] Sugestão automática de skills baseada no cargo
- [ ] Integração com Skills Taxonomy (ESCO, O*NET)

---

### Etapa 6: Sourcing Strategy Collector

**Objetivo:** Definir estratégia de sourcing: setores-alvo, empresas de interesse, e estimativa de pool.

**Inputs Esperados:**
- Setores/indústrias de interesse
- Empresas-alvo para hunting
- Canais de divulgação preferidos

**Outputs Esperados:**
- `target_sectors`: array
- `target_companies`: array
- `sourcing_channels`: array
- `estimated_pool_size`: number

**Critérios de Sucesso:**
- Pelo menos 1 setor definido
- Estimativa de pool gerada

**Comportamento da LIA:**
```
LIA: "Agora vamos definir onde buscar candidatos. De quais setores 
ou empresas você gostaria de atrair pessoas?"
```

**Exemplos de Diálogo:**

```
RECRUTADOR: "Pessoas que venham de fintechs, startups de produto, 
ou empresas como Nubank, iFood, Loft"

LIA: "Excelente escolha! Vou mapear:

🎯 ESTRATÉGIA DE SOURCING:

SETORES PRIORITÁRIOS:
1. Fintechs
2. Startups de produto digital
3. E-commerce/marketplace

EMPRESAS-ALVO:
- Nubank
- iFood
- Loft
- Creditas
- QuintoAndar
- Loggi

📊 ESTIMATIVA DE POOL:
Baseado nesses critérios, encontrei aproximadamente:
- Base local (WeDOTalent): ~120 candidatos
- Pearch AI: ~2.400 candidatos qualificados

Quer que eu adicione ou remova alguma empresa?"
```

**Agentes Envolvidos:**
- **Sourcing Agent**: Define estratégia e estima pool
- **Job Planner Agent**: Estruturação dos dados

**Status:** ✅ Implementado

**Pendências:**
- [ ] Integração real com Pearch para estimativa de pool

---

### Etapa 7: WSI Competencies Collector

**Objetivo:** Definir competências comportamentais que serão avaliadas na triagem WSI.

**Inputs Esperados:**
- Competências comportamentais desejadas
- Mapeamento Big Five

**Outputs Esperados:**
- `wsi_competencies`: array de competências
- `big_five_mapping`: object com traços e pesos

**Critérios de Sucesso:**
- 3-5 competências definidas
- Big Five mapeado automaticamente

**Comportamento da LIA:**
```
LIA: "Agora vamos definir as competências comportamentais. Baseado 
no cargo e na cultura da TechCorp, sugiro avaliar..."
```

**Exemplos de Diálogo:**

```
LIA: "Para um Product Manager Sênior na TechCorp, sugiro avaliar 
estas competências:

🧠 COMPETÊNCIAS SUGERIDAS:

1. **Visão Estratégica** 
   Capacidade de conectar produto com objetivos de negócio
   Big Five: Alta Abertura + Alta Conscienciosidade

2. **Influência sem Autoridade**
   Habilidade de convencer stakeholders e times
   Big Five: Alta Extroversão + Alta Amabilidade

3. **Tomada de Decisão com Dados**
   Usar métricas para priorizar e validar hipóteses
   Big Five: Alta Conscienciosidade + Baixa Neuroticismo

4. **Gestão de Ambiguidade**
   Conforto com incerteza e mudanças constantes
   Big Five: Alta Abertura + Baixa Neuroticismo

Essas 4 competências cobrem bem o perfil. Quer ajustar alguma?"

RECRUTADOR: "Adiciona Ownership - pessoas que vestem a camisa"

LIA: "Adicionado! Ownership - senso de dono e responsabilidade.
Big Five: Alta Conscienciosidade + Alta Abertura

Agora temos 5 competências que serão avaliadas na triagem WSI."
```

**Agentes Envolvidos:**
- **WSI Evaluator Agent**: Define e avalia competências
- **Job Planner Agent**: Estruturação

**Status:** ✅ Implementado

**Pendências:** Nenhuma

---

### Etapa 8: Interview Flow Collector

**Objetivo:** Definir fluxo de entrevistas e timeline.

**Inputs Esperados:**
- Etapas do processo seletivo
- Responsáveis por cada etapa
- Duração estimada

**Outputs Esperados:**
- `interview_stages`: array de etapas
- `total_duration_days`: number
- `timeline`: object com datas estimadas

**Critérios de Sucesso:**
- Todas as etapas definidas
- Responsáveis identificados
- Timeline calculado

**Comportamento da LIA:**
```
LIA: "Como é o processo seletivo dessa vaga? Quantas etapas e 
quem participa de cada uma?"
```

**Exemplos de Diálogo:**

```
RECRUTADOR: "Triagem LIA, entrevista com RH, case técnico, entrevista 
com gestor, e proposta"

LIA: "Perfeito! Vou estruturar o fluxo:

📋 FLUXO DE ENTREVISTAS:

| Etapa | Responsável | Duração |
|-------|-------------|---------|
| 1. Triagem LIA | LIA (automático) | 24h |
| 2. Entrevista RH | Você | 45min |
| 3. Case Técnico | Candidato | 3-5 dias |
| 4. Entrevista Gestor | Maria Silva | 60min |
| 5. Proposta | RH + Gestor | 2-3 dias |

⏱️ TIMELINE ESTIMADO:
- Tempo total: 15-20 dias úteis
- Data estimada de contratação: 15/02/2024

Está alinhado com sua expectativa?"

RECRUTADOR: "Sim, mas o case pode ser feito em 2 dias"

LIA: "Ajustado! Case técnico: 2 dias. Timeline total: 12-15 dias."
```

**Agentes Envolvidos:**
- **Interview Scheduler Agent**: Define fluxo
- **Job Planner Agent**: Estruturação

**Status:** ✅ Implementado

**Pendências:**
- [ ] Integração com calendário para verificar disponibilidade dos entrevistadores

---

### Etapa 9: Timeline (Calculado Automaticamente)

**Objetivo:** Calcular automaticamente o timeline baseado nas etapas definidas.

Este é um cálculo automático, não requer interação do recrutador.

**Status:** ✅ Implementado (integrado na etapa 8)

---

### Etapa 10: Governance Collector

**Objetivo:** Definir regras de governança: aprovações, automações, e políticas.

**Inputs Esperados:**
- Quem aprova candidatos
- Regras de auto-agendamento
- Regras de auto-feedback
- Limites de automação

**Outputs Esperados:**
- `governance_rules`: object
- `auto_schedule_enabled`: boolean
- `auto_feedback_enabled`: boolean
- `approval_matrix`: array

**Critérios de Sucesso:**
- Todas as regras definidas
- Limites claros para automação

**Comportamento da LIA:**
```
LIA: "Agora vamos definir as 'regras do jogo'. O que posso fazer 
automaticamente e o que precisa da sua aprovação?"
```

**Exemplos de Diálogo:**

```
LIA: "Vou te fazer algumas perguntas sobre governança:

1️⃣ CANDIDATOS COM SCORE ≥ 80%:
Posso adicionar automaticamente ao pipeline ou precisa de aprovação?

a) Adicionar automaticamente
b) Pedir aprovação sempre

RECRUTADOR: "Automaticamente"

LIA: "2️⃣ AGENDAMENTO DE ENTREVISTAS:
Para candidatos aprovados na triagem, posso:

a) Agendar automaticamente no horário disponível do gestor
b) Sugerir 3 horários e deixar candidato escolher
c) Pedir sua aprovação antes de agendar

RECRUTADOR: "B, sugerir horários"

LIA: "3️⃣ FEEDBACK NEGATIVO:
Para candidatos reprovados, posso:

a) Enviar feedback automaticamente
b) Pedir sua aprovação antes de enviar
c) Não enviar feedback

RECRUTADOR: "A, pode enviar automaticamente"

LIA: "Perfeito! Regras de governança definidas:

⚙️ GOVERNANÇA:
- Score ≥80%: Adicionar automaticamente ✅
- Agendamento: Self-scheduling (3 opções) 📅
- Feedback negativo: Automático 📧
- Aprovação final: Sempre com você 👤

Posso seguir?"
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Define regras
- **Orchestrator**: Aplica regras durante execução

**Status:** ✅ Implementado

**Pendências:** Nenhuma

---

### Etapa 11: Communication Templates Collector

**Objetivo:** Personalizar templates de comunicação para a vaga.

**Inputs Esperados:**
- Tom de comunicação preferido
- Ajustes nos templates padrão
- Mensagens específicas da vaga

**Outputs Esperados:**
- `templates`: object com templates customizados
- `communication_tone`: string

**Critérios de Sucesso:**
- Templates aprovados pelo recrutador
- Tom alinhado com cultura da empresa

**Comportamento da LIA:**
```
LIA: "Preparei os templates de comunicação baseados na cultura 
da TechCorp. Quer revisar ou ajustar?"
```

**Exemplos de Diálogo:**

```
LIA: "Criei os templates para essa vaga. Veja o principal:

📧 EMAIL DE APRESENTAÇÃO:

'Oi [Nome],

Encontrei seu perfil e achei que você seria incrível para uma 
oportunidade na TechCorp!

Estamos buscando um Product Manager Sênior para liderar 
iniciativas estratégicas no nosso time de Produto.

🔥 Por que essa vaga é especial:
- Autonomia para tomar decisões de produto
- Time de alta performance
- Impacto direto em milhões de usuários

Quer saber mais? Me conta que te explico!'

Esse tom está bom ou quer algo mais formal/informal?"

RECRUTADOR: "Gostei, mas tira o emoji de fogo, é muito informal"

LIA: "Ajustado! Removi o emoji. Template aprovado para uso."
```

**Agentes Envolvidos:**
- **Recruiter Assistant Agent**: Personaliza comunicações
- **Job Planner Agent**: Armazena templates

**Status:** ✅ Implementado

**Pendências:** Nenhuma

---

### Etapa 12: Job Description Generator

**Objetivo:** Gerar descrição completa da vaga baseada em todas as informações coletadas.

**Inputs Esperados:**
- Todas as informações das etapas anteriores

**Outputs Esperados:**
- `job_description`: string (descrição completa)
- `bias_analysis`: object (análise de viés inclusivo)

**Critérios de Sucesso:**
- JD completa e bem estruturada
- Livre de viés excludente
- Aprovada pelo recrutador

**Comportamento da LIA:**
```
LIA: "Com todas as informações, gerei a descrição da vaga. 
Também fiz uma análise de viés para garantir que o texto 
seja inclusivo."
```

**Exemplos de Diálogo:**

```
LIA: "Pronto! Aqui está a descrição da vaga:

---

📋 PRODUCT MANAGER SÊNIOR | TECHCORP

Sobre a TechCorp:
Somos uma scale-up de tecnologia em forte crescimento, 
transformando negócios através da inovação...

O Desafio:
Você será responsável por liderar iniciativas estratégicas 
de produto, trabalhando com um time de alta performance...

Requisitos:
✅ 3+ anos de experiência como Product Manager
✅ Experiência com metodologias ágeis (Scrum/Kanban)
...

---

📊 ANÁLISE DE VIÉS:
✅ Linguagem neutra de gênero
✅ Requisitos focados em habilidades (não idade/formação específica)
⚠️ Sugestão: Adicionar 'Não é necessário formação específica'

Quer que eu faça esse ajuste?"

RECRUTADOR: "Sim, adiciona"

LIA: "Pronto! Descrição ajustada e livre de viés. Posso publicar?"
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Geração do JD
- **Analytics Agent**: Análise de viés

**Status:** ✅ Implementado

**Pendências:**
- [ ] Análise de viés mais sofisticada com ML

---

### Etapa 13: Publication Node

**Objetivo:** Publicar a vaga nos canais definidos e sincronizar com ATS.

**Inputs Esperados:**
- JD aprovada
- Canais de publicação
- Credenciais de ATS

**Outputs Esperados:**
- `published`: boolean
- `publication_urls`: array
- `ats_sync_status`: string

**Critérios de Sucesso:**
- Vaga publicada com sucesso
- ATS sincronizado
- Transição para Fase 2 (Sourcing)

**Comportamento da LIA:**
```
LIA: "Vaga pronta para publicação! Onde você quer publicar?"
```

**Exemplos de Diálogo:**

```
LIA: "Tudo pronto! Opções de publicação:

📢 CANAIS DISPONÍVEIS:
✅ LinkedIn Job Slot (TechCorp)
✅ Gupy (ATS interno)
✅ Indeed
⬜ Glassdoor
⬜ Catho

Quais você quer ativar?"

RECRUTADOR: "LinkedIn e Gupy"

LIA: "Publicando...

✅ LinkedIn Job Slot - Publicado!
   Link: linkedin.com/jobs/view/123456
   
✅ Gupy - Sincronizado!
   ID da vaga: #TECH-PM-2024-001

🎉 Vaga ativa! Agora vou iniciar o sourcing automatizado. 
Vou te notificar quando encontrar os primeiros candidatos.

Próximos passos:
1. Buscar na base local (gratuito)
2. Se necessário, expandir para Pearch AI (com seu ok)
3. Te apresentar os melhores perfis para calibração"

[TRANSIÇÃO AUTOMÁTICA PARA FASE 2]
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Publicação
- **ATS Integrator Agent**: Sincronização
- **Sourcing Agent**: Inicia próxima fase

**Status:** ✅ Implementado

**Pendências:**
- [ ] Integração real com LinkedIn Job Slots
- [ ] Integração real com Gupy/Pandapé

---

## FASE 2: Sourcing Automatizado (Etapas 14-17)

### Etapa 14: Local Search Node

**Objetivo:** Buscar candidatos na base de dados local antes de usar créditos externos.

**Inputs Esperados:**
- Critérios da vaga
- Perfil ideal da empresa
- Filtros de busca

**Outputs Esperados:**
- `local_candidates`: array de candidatos
- `match_scores`: object com scores de cada candidato
- `search_metadata`: object com métricas da busca

**Critérios de Sucesso:**
- Busca executada em < 30 segundos
- Candidatos rankeados por score
- Mínimo 5 candidatos encontrados (ideal: 20+)

**Comportamento da LIA:**
```
LIA: "Iniciando busca na base local... Encontrei X candidatos 
que podem ser interessantes para essa vaga."
```

**Exemplos de Diálogo:**

```
LIA: "🔍 Busca na Base Local - Resultados

Encontrei 34 candidatos na nossa base que podem ser bons 
para Product Manager Sênior na TechCorp:

📊 DISTRIBUIÇÃO POR SCORE:
- 🟢 Score ≥80%: 8 candidatos (auto-add)
- 🟡 Score 60-79%: 15 candidatos (revisão)
- 🔴 Score <60%: 11 candidatos (descartados)

TOP 5:
1. João Silva - Score 92% - PM Sênior no Nubank
2. Maria Santos - Score 88% - PM na Loft
3. Carlos Oliveira - Score 85% - PM no QuintoAndar
4. Ana Costa - Score 82% - PM no iFood
5. Pedro Lima - Score 78% - PM na Creditas

Quer ver os detalhes desses candidatos para calibração?"
```

**Agentes Envolvidos:**
- **Sourcing Agent**: Executa busca e scoring
- **CV Screener Agent**: Calcula match scores

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Algoritmo de scoring integrado com perfil ideal (Fase 0)
- [ ] Busca semântica no banco de dados

---

### Etapa 15: Calibration Node

**Objetivo:** Apresentar candidatos para o recrutador calibrar o algoritmo de matching.

**Inputs Esperados:**
- Top 5-10 candidatos da busca local
- Scores calculados

**Outputs Esperados:**
- `calibration_feedback`: array de feedbacks
- `updated_weights`: object com pesos ajustados
- `learning_log`: registro do aprendizado

**Critérios de Sucesso:**
- Recrutador avaliou pelo menos 5 candidatos
- LIA ajustou pesos baseado no feedback
- Acurácia do modelo melhorou

**Comportamento da LIA:**
```
LIA: "Para eu aprender o que você busca, me ajuda a calibrar. 
Vou te mostrar alguns perfis e você me diz se são bons ou não."
```

**Exemplos de Diálogo:**

```
LIA: "Vamos calibrar! Te mostro 5 perfis e você me diz:
👍 Bom perfil - quer que eu traga mais assim
👎 Não serve - explica o porquê
🤔 Talvez - tem potencial mas algo falta

📋 CANDIDATO 1/5: João Silva
- Atual: PM Sênior no Nubank (2 anos)
- Anterior: PM na Stone (3 anos)
- Formação: Eng. de Produção - USP
- Skills: SQL, Figma, Scrum
- Score: 92%

O que você acha?"

RECRUTADOR: "👍 Bom perfil, gosto da experiência em fintech"

LIA: "Anotado! Vou priorizar experiência em fintech.

📋 CANDIDATO 2/5: Carlos Oliveira
- Atual: PM no QuintoAndar (1 ano)
- Anterior: Consultor na McKinsey (4 anos)
- Formação: Administração - FGV
- Skills: Excel, SQL, metodologias ágeis
- Score: 85%

O que você acha?"

RECRUTADOR: "👎 Não gosto, tempo curto no QuintoAndar e 
perfil muito consultor, pouca mão na massa"

LIA: "Entendi! Vou:
- Penalizar permanência < 2 anos
- Reduzir peso de background em consultoria
- Valorizar mais perfis 'hands-on'

Isso vai afetar o score dele (novo: 68%) e de perfis similares."

[... após 5 candidatos ...]

LIA: "Calibração concluída! Aprendi:

📈 AJUSTES APLICADOS:
- Experiência em fintech: +15% peso
- Permanência mínima: 2 anos (antes: 1 ano)
- Background consultoria: -10% peso
- Projetos hands-on: +10% peso

Novo ranking gerado. Os 8 candidatos com score ≥80% continuam, 
mas a ordem mudou. Quer ver?"
```

**Agentes Envolvidos:**
- **Sourcing Agent**: Apresenta candidatos
- **Analytics Agent**: Ajusta modelo de scoring
- **Recruiter Assistant Agent**: Captura feedback

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Algoritmo de machine learning para calibração
- [ ] Persistência dos ajustes de peso
- [ ] Loop de feedback contínuo

---

### Etapa 16: Volume Assessment Node

**Objetivo:** Avaliar se o volume de candidatos qualificados é suficiente.

**Inputs Esperados:**
- Candidatos pós-calibração
- Meta de candidatos por etapa

**Outputs Esperados:**
- `volume_assessment`: enum (sufficient, insufficient)
- `recommendation`: string
- `gap_analysis`: object

**Critérios de Sucesso:**
- Decisão clara sobre necessidade de expansão
- Recomendação fundamentada

**Comportamento da LIA:**
```
LIA: "Avaliei o volume de candidatos qualificados. Aqui está 
minha análise e recomendação."
```

**Exemplos de Diálogo:**

*Exemplo 1 - Volume Suficiente:*
```
LIA: "📊 ANÁLISE DE VOLUME

Candidatos qualificados (score ≥80%): 8
Meta para entrevistas: 5-8

✅ VOLUME SUFICIENTE

Recomendação: Prosseguir com os candidatos locais.
Não é necessário buscar no Pearch AI agora.

Quer que eu inicie o contato com esses 8 candidatos?"
```

*Exemplo 2 - Volume Insuficiente:*
```
LIA: "📊 ANÁLISE DE VOLUME

Candidatos qualificados (score ≥80%): 3
Meta para entrevistas: 5-8

⚠️ VOLUME INSUFICIENTE

Gap: Precisamos de mais 2-5 candidatos qualificados.

Recomendação: Expandir busca no Pearch AI

💰 ESTIMATIVA DE CUSTO:
- Busca: ~50 créditos
- Insights: ~20 créditos/candidato
- Total estimado: 150 créditos

Autoriza a expansão?"

RECRUTADOR: "Sim, pode buscar"

LIA: "Perfeito! Iniciando busca global no Pearch..."
```

**Agentes Envolvidos:**
- **Sourcing Agent**: Avalia volume
- **Analytics Agent**: Calcula gaps

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Lógica de cálculo de meta dinâmica
- [ ] Integração com estimativa de créditos Pearch

---

### Etapa 17: Global Expansion Node

**Objetivo:** Expandir busca para Pearch AI se volume local for insuficiente.

**Inputs Esperados:**
- Critérios da vaga
- Autorização do recrutador
- Budget de créditos

**Outputs Esperados:**
- `pearch_candidates`: array
- `credits_used`: number
- `combined_pipeline`: array

**Critérios de Sucesso:**
- Busca executada com sucesso
- Candidatos adicionados ao pipeline
- Créditos dentro do budget

**Comportamento da LIA:**
```
LIA: "Buscando no Pearch AI com os critérios calibrados..."
```

**Exemplos de Diálogo:**

```
LIA: "🌎 BUSCA GLOBAL - RESULTADOS

Busquei no Pearch AI com os critérios calibrados:
- PM Sênior
- Experiência em fintech/startup
- Mínimo 2 anos em cada empresa
- Skills: SQL, metodologias ágeis

📊 RESULTADOS:
- Perfis encontrados: 156
- Perfis qualificados (score ≥80%): 12
- Créditos utilizados: 145

TOP 5 NOVOS:
1. Fernanda Costa - Score 94% - PM Sênior no Nubank
2. Ricardo Santos - Score 91% - PM na C6 Bank
3. Juliana Lima - Score 89% - PM no Mercado Pago
4. Bruno Oliveira - Score 86% - PM na PicPay
5. Camila Souza - Score 84% - PM no Banco Inter

🎯 PIPELINE ATUALIZADO:
- Candidatos locais: 8
- Candidatos Pearch: 12
- Total qualificados: 20

Posso iniciar contato com os Top 15?"
```

**Agentes Envolvidos:**
- **Sourcing Agent**: Executa busca Pearch
- **CV Screener Agent**: Scoring dos novos candidatos

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Integração real com Pearch AI API
- [ ] Sistema de gestão de créditos

---

## FASE 3: Engajamento de Candidatos (Etapas 18-19)

### Etapa 18: Contact Approval Node

**Objetivo:** Obter aprovação do recrutador para contatar candidatos selecionados.

**Inputs Esperados:**
- Lista de candidatos qualificados
- Scores e resumos

**Outputs Esperados:**
- `approved_candidates`: array
- `rejected_candidates`: array
- `approval_notes`: object

**Critérios de Sucesso:**
- Recrutador revisou lista
- Pelo menos 5 candidatos aprovados para contato

**Comportamento da LIA:**
```
LIA: "Tenho 20 candidatos qualificados. Vou te mostrar os Top 15 
para você aprovar o contato."
```

**Exemplos de Diálogo:**

```
LIA: "📋 APROVAÇÃO DE CONTATO

Preparei a lista de candidatos para contato inicial:

| # | Nome | Score | Atual | Ação |
|---|------|-------|-------|------|
| 1 | Fernanda Costa | 94% | Nubank | [Aprovar] [Recusar] |
| 2 | Ricardo Santos | 91% | C6 Bank | [Aprovar] [Recusar] |
| 3 | João Silva | 92% | Nubank | [Aprovar] [Recusar] |
...

Você pode:
1. Aprovar todos (15 candidatos)
2. Aprovar selecionados
3. Ver detalhes de algum perfil

O que prefere?"

RECRUTADOR: "Aprovar todos exceto o #7 - já conversei com ela antes"

LIA: "Perfeito! 14 candidatos aprovados para contato.
Removida: Ana Rodrigues (#7)

Vou iniciar os contatos por email personalizado. 
Te notifico quando tiver respostas!"
```

**Agentes Envolvidos:**
- **Sourcing Agent**: Apresenta candidatos
- **Recruiter Assistant Agent**: Captura aprovações

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] UI para aprovação em lote
- [ ] Histórico de interações anteriores com candidatos

---

### Etapa 19: Email Outreach Node

**Objetivo:** Enviar emails personalizados apresentando a oportunidade.

**Inputs Esperados:**
- Candidatos aprovados
- Templates de comunicação
- Dados da vaga

**Outputs Esperados:**
- `emails_sent`: number
- `delivery_status`: object por candidato
- `outreach_log`: array

**Critérios de Sucesso:**
- Todos os emails enviados
- Taxa de entrega > 95%

**Comportamento da LIA:**
```
LIA: "Enviando emails personalizados para os 14 candidatos aprovados..."
```

**Exemplos de Diálogo:**

```
LIA: "📧 CAMPANHA DE OUTREACH - STATUS

Enviados: 14/14 ✅

RESUMO:
- Entregues: 13 (93%)
- Bounce: 1 (Ricardo Santos - email inválido)
- Abertos: 8 (atualiza em tempo real)
- Respondidos: 3

📬 RESPOSTAS RECEBIDAS:

1. Fernanda Costa: 
   '✅ Tenho interesse! Podemos conversar?'
   → Sugestão: Agendar triagem WSI

2. João Silva:
   '🤔 Estou em outro processo, mas gostei da vaga'
   → Sugestão: Manter aquecido, follow-up em 1 semana

3. Juliana Lima:
   '❌ No momento não busco mudanças'
   → Sugestão: Agradecer e manter no talent pool

Como quer proceder?"

RECRUTADOR: "Para Fernanda, agenda a triagem. João, faz o follow-up. 
Juliana, pode agradecer."

LIA: "Perfeito!
- Fernanda: Enviando convite para triagem WSI
- João: Agendando follow-up para 15/01
- Juliana: Enviando agradecimento"
```

**Agentes Envolvidos:**
- **Recruiter Assistant Agent**: Envia comunicações
- **Sourcing Agent**: Atualiza status dos candidatos

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Integração com serviço de email (Mailgun, AWS SES)
- [ ] Tracking de abertura/cliques
- [ ] Detecção de respostas automáticas

---

## FASE 4: Triagem WSI (Etapas 20-22)

### Etapa 20: Async Screening Node

**Objetivo:** Conduzir triagem assíncrona por WhatsApp/chat com metodologia WSI.

**Inputs Esperados:**
- Candidato confirmado
- Competências a avaliar (WSI)
- Templates de perguntas

**Outputs Esperados:**
- `screening_transcript`: string
- `wsi_scores`: object por competência
- `overall_score`: number
- `big_five_analysis`: object

**Critérios de Sucesso:**
- Todas as competências avaliadas
- Candidato respondeu no prazo de 24h
- Score WSI calculado

**Comportamento da LIA:**
```
LIA (para candidato): "Olá Fernanda! Que bom que você tem interesse 
na vaga de PM Sênior na TechCorp. Vou fazer uma triagem rápida 
por aqui mesmo, leva cerca de 15-20 minutos. Topa?"
```

**Exemplos de Diálogo (LIA x Candidato):**

```
LIA: "Oi Fernanda! 👋

Sou a LIA, assistente de recrutamento da WeDOTalent. 
Que bom que você tem interesse na vaga de PM Sênior na TechCorp!

Vou fazer uma triagem rápida aqui pelo WhatsApp. São algumas 
perguntas sobre sua experiência e forma de trabalhar. 
Leva uns 15-20 minutos.

Pode ser agora ou prefere em outro momento?"

CANDIDATO: "Pode ser agora!"

LIA: "Ótimo! Vamos lá.

Primeira pergunta - sobre VISÃO ESTRATÉGICA:

Me conta uma situação em que você precisou conectar uma decisão 
de produto com objetivos maiores do negócio. Como foi o processo 
de pensamento e qual foi o resultado?"

CANDIDATO: "No Nubank, eu era responsável pelo produto de investimentos. 
Quando percebemos que o ticket médio estava caindo, precisei..."

[... conversa continua com perguntas STAR para cada competência ...]

LIA: "Excelente, Fernanda! Última pergunta - sobre OWNERSHIP:

Conta uma vez que você assumiu responsabilidade por algo que 
não era formalmente sua função. O que te motivou e como foi?"

CANDIDATO: "Teve uma vez que nosso time de growth estava com 
problema de conversão e eu assumi..."

LIA: "Perfeito! Obrigada pelas respostas. Foram muito completas.

Próximos passos:
1. Vou analisar nossa conversa (leva ~24h)
2. Te dou um retorno, positivo ou negativo
3. Se aprovada, agenda com o RH da TechCorp

Alguma dúvida sobre a vaga?"

CANDIDATO: "Quanto é a faixa salarial?"

LIA: "A faixa é de R$ 18.000 a R$ 22.000 CLT, mais benefícios 
como VR, plano de saúde e bônus anual. Te mando os detalhes 
por email!

Obrigada pelo tempo, Fernanda. Falo com você em breve! 🙂"
```

**Agentes Envolvidos:**
- **WSI Evaluator Agent**: Conduz a triagem e avalia respostas
- **Interview Scheduler Agent**: Agenda próximas etapas

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Integração com WhatsApp Business API
- [ ] Análise em tempo real das respostas
- [ ] Timer de 24h com reminder automático

---

### Etapa 21: Candidate Feedback Node

**Objetivo:** Enviar feedback estruturado para o candidato após triagem.

**Inputs Esperados:**
- Resultado da triagem
- Scores por competência
- Decisão (aprovado/reprovado)

**Outputs Esperados:**
- `feedback_sent`: boolean
- `feedback_content`: object

**Critérios de Sucesso:**
- Feedback enviado em até 24h após triagem
- Feedback construtivo mesmo em reprovações

**Comportamento da LIA:**
```
LIA (para candidato): "Analisei nossa conversa e aqui está meu 
feedback sobre seu perfil..."
```

**Exemplos de Diálogo:**

*Exemplo - Feedback Positivo:*
```
LIA: "Oi Fernanda! 

Analisei nossa conversa e tenho boas notícias! 🎉

Seu perfil foi aprovado para a próxima etapa do processo 
de PM Sênior na TechCorp.

📊 SEU DESEMPENHO:
- Visão Estratégica: ⭐⭐⭐⭐⭐ Excelente
- Influência: ⭐⭐⭐⭐ Muito bom
- Decisão com Dados: ⭐⭐⭐⭐⭐ Excelente
- Gestão de Ambiguidade: ⭐⭐⭐⭐ Muito bom
- Ownership: ⭐⭐⭐⭐⭐ Excelente

🏆 PONTOS FORTES:
1. Sua experiência em fintech agrega muito
2. Demonstrou forte capacidade analítica
3. Histórias bem estruturadas (formato STAR)

📅 PRÓXIMO PASSO:
Agendar entrevista com o RH da TechCorp.
Disponibilidade: [link de agendamento]

Parabéns! 🙂"
```

*Exemplo - Feedback Negativo:*
```
LIA: "Oi Carlos,

Agradeço muito o tempo que dedicou à nossa conversa!

Infelizmente, para essa vaga específica de PM Sênior na TechCorp, 
vamos seguir com outros candidatos.

📊 MEU FEEDBACK:
Você demonstrou conhecimento técnico sólido, especialmente em 
metodologias ágeis. Porém, para essa vaga, buscamos alguém com 
mais experiência hands-on em produto digital (vs. consultoria).

💡 SUGESTÃO:
Considere participar de projetos práticos de produto, mesmo 
como side project. Isso pode fortalecer muito seu perfil.

Mantenho seu currículo na base para futuras oportunidades 
mais alinhadas. Obrigada e boa sorte! 🍀"
```

**Agentes Envolvidos:**
- **WSI Evaluator Agent**: Gera análise
- **Recruiter Assistant Agent**: Envia feedback

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Templates de feedback personalizáveis
- [ ] Validação humana opcional antes do envio

---

### Etapa 22: Recruiter Report Node

**Objetivo:** Enviar relatório estruturado para o recrutador via Teams/Chat.

**Inputs Esperados:**
- Resultado da triagem
- Scores WSI
- Transcrição resumida

**Outputs Esperados:**
- `report_sent`: boolean
- `report_content`: object

**Critérios de Sucesso:**
- Relatório enviado via Teams
- Todas as informações relevantes incluídas
- Recomendação clara

**Comportamento da LIA:**
```
LIA (via Teams): "Finalizei a triagem da Fernanda Costa. Aqui 
está meu relatório completo com recomendação."
```

**Exemplos de Diálogo:**

```
[NOTIFICAÇÃO TEAMS]

LIA: "📋 RELATÓRIO DE TRIAGEM WSI

CANDIDATA: Fernanda Costa
VAGA: PM Sênior - TechCorp
DATA: 10/01/2024

📊 SCORES:
- Score LIA Geral: 91%
- Aderência ao Perfil: 94%
- Score WSI: 88%

🎯 COMPETÊNCIAS AVALIADAS:

| Competência | Score | Evidência |
|-------------|-------|-----------|
| Visão Estratégica | 95% | Excelente caso do Nubank |
| Influência | 82% | Bons exemplos de stakeholder mgmt |
| Decisão com Dados | 90% | Forte orientação analítica |
| Gestão Ambiguidade | 85% | Adaptável, histórico consistente |
| Ownership | 92% | Múltiplos exemplos convincentes |

🧠 BIG FIVE INFERIDO:
- Abertura: Alta (criativa, curiosa)
- Conscienciosidade: Alta (organizada, focada)
- Extroversão: Média-Alta (comunicativa)
- Amabilidade: Alta (colaborativa)
- Neuroticismo: Baixo (estável emocionalmente)

📝 RESUMO QUALITATIVO:
Fernanda demonstrou excelente capacidade de conectar produto 
com negócio. Sua experiência em fintech e perfil hands-on 
alinham muito bem com o DNA da TechCorp. Comunicação clara 
e respostas bem estruturadas.

✅ RECOMENDAÇÃO: APROVAR para entrevista com RH

[APROVAR] [REJEITAR] [VER TRANSCRIÇÃO]"

RECRUTADOR: [clica em APROVAR]

LIA: "Ótimo! Vou agendar a entrevista com RH. Alguma preferência 
de horário para essa semana?"
```

**Agentes Envolvidos:**
- **WSI Evaluator Agent**: Gera relatório
- **Recruiter Assistant Agent**: Notifica via Teams

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Integração com Microsoft Teams API
- [ ] Formatação de mensagens adaptativas (Adaptive Cards)

---

## FASE 5: Decisão e Agendamento (Etapas 23-25)

### Etapa 23: Recruiter Decision Node

**Objetivo:** Capturar decisão do recrutador sobre cada candidato.

**Inputs Esperados:**
- Relatório de triagem
- Ação do recrutador

**Outputs Esperados:**
- `decision`: enum (approve, reject, hold)
- `decision_notes`: string
- `next_action`: string

**Critérios de Sucesso:**
- Decisão registrada
- Próximo passo acionado

**Comportamento da LIA:**
```
LIA: "Aguardando sua decisão sobre o candidato..."
```

**Exemplos de Diálogo:**

```
[Recrutador clica em APROVAR no relatório]

LIA: "Fernanda Costa aprovada para entrevista com RH! ✅

Próximo passo: Agendar entrevista
Responsável: Você (João)
Duração sugerida: 45 minutos

Quer que eu:
1. Agende automaticamente no próximo horário livre
2. Sugira 3 opções para a Fernanda escolher
3. Te mostre a agenda para você escolher

Qual prefere?"

RECRUTADOR: "Opção 2"

LIA: "Perfeito! Vou enviar 3 opções de horário para a Fernanda 
escolher. Baseado na agenda dela e na sua:

Opções que vou sugerir:
- Terça 14/01 às 14h
- Quarta 15/01 às 10h
- Quinta 16/01 às 15h

Posso enviar?"
```

**Agentes Envolvidos:**
- **Recruiter Assistant Agent**: Captura decisão
- **Interview Scheduler Agent**: Inicia agendamento

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] UI de decisão rápida (botões no Teams)

---

### Etapa 24: Auto-Scheduling Node

**Objetivo:** Agendar entrevista automaticamente ou via self-scheduling.

**Inputs Esperados:**
- Candidato aprovado
- Regras de governança
- Disponibilidade do recrutador

**Outputs Esperados:**
- `interview_scheduled`: boolean
- `interview_datetime`: datetime
- `calendar_event_id`: string

**Critérios de Sucesso:**
- Entrevista agendada com sucesso
- Evento criado no calendário
- Candidato e recrutador notificados

**Comportamento da LIA:**
```
LIA: "Agendando entrevista baseado nas preferências configuradas..."
```

**Exemplos de Diálogo:**

*Exemplo - Self-Scheduling:*
```
LIA (para candidato): "Oi Fernanda! Ótima notícia!

Você foi aprovada na triagem e queremos agendar a entrevista 
com o RH da TechCorp.

📅 ESCOLHA SEU HORÁRIO:
- Terça 14/01 às 14h
- Quarta 15/01 às 10h
- Quinta 16/01 às 15h

Qual funciona melhor para você?"

CANDIDATO: "Quarta às 10h"

LIA: "Perfeito! Agendado:

📆 ENTREVISTA CONFIRMADA
Data: Quarta, 15/01/2024
Hora: 10h (horário de Brasília)
Duração: 45 minutos
Com: João Silva (RH - TechCorp)
Link: meet.google.com/abc-xyz-123

Adicione ao seu calendário: [link .ics]

Alguma dúvida antes da entrevista?"
```

*Notificação para Recrutador:*
```
LIA (via Teams): "📅 ENTREVISTA AGENDADA

Fernanda Costa confirmou:
- Data: 15/01/2024 às 10h
- Duração: 45 minutos
- Link: meet.google.com/abc-xyz-123

Já adicionei ao seu calendário!"
```

**Agentes Envolvidos:**
- **Interview Scheduler Agent**: Gerencia agendamento
- **Recruiter Assistant Agent**: Notificações

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Integração com Microsoft Graph Calendar
- [ ] Criação automática de eventos
- [ ] Geração de links de meet

---

### Etapa 25: Rejection Feedback Node

**Objetivo:** Enviar feedback negativo estruturado para candidatos rejeitados.

**Inputs Esperados:**
- Candidato rejeitado
- Motivo da rejeição
- Template de feedback

**Outputs Esperados:**
- `feedback_sent`: boolean
- `feedback_content`: object

**Critérios de Sucesso:**
- Feedback enviado em até 24h
- Tom respeitoso e construtivo

**Comportamento da LIA:**
```
LIA: "Enviando feedback negativo para candidato rejeitado..."
```

**Exemplos de Diálogo:**

```
LIA (para candidato): "Oi Carlos,

Obrigada pelo interesse na vaga de PM Sênior na TechCorp 
e pelo tempo dedicado à nossa conversa!

Após avaliação cuidadosa, decidimos seguir com outros 
candidatos cujos perfis estão mais alinhados com as 
necessidades específicas dessa posição.

📝 FEEDBACK:
Você demonstrou sólido conhecimento em metodologias ágeis 
e boa capacidade analítica. Para oportunidades futuras de 
produto digital, recomendo investir em experiências mais 
hands-on com desenvolvimento de features e métricas de 
produto.

Seu currículo fica em nossa base para futuras vagas. 
Desejo sucesso na sua jornada! 🍀

Atenciosamente,
LIA - WeDOTalent"
```

**Agentes Envolvidos:**
- **Recruiter Assistant Agent**: Envia feedback

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Aprovação opcional do recrutador antes do envio
- [ ] Personalização por tipo de rejeição

---

## FASE 6: Fechamento (Etapas 26-27)

### Etapa 26: Placement Node

**Objetivo:** Registrar contratação e fechar a vaga.

**Inputs Esperados:**
- Candidato contratado
- Data de início
- Detalhes da proposta aceita

**Outputs Esperados:**
- `placement_registered`: boolean
- `job_closed`: boolean
- `metrics`: object (time-to-fill, etc.)

**Critérios de Sucesso:**
- Contratação registrada
- Vaga fechada no ATS
- Métricas calculadas

**Comportamento da LIA:**
```
LIA: "Parabéns! Vou registrar a contratação e fechar a vaga."
```

**Exemplos de Diálogo:**

```
RECRUTADOR: "LIA, a Fernanda aceitou a proposta!"

LIA: "Excelente notícia! 🎉

Vou registrar a contratação:

📋 PLACEMENT REGISTRADO:
- Candidata: Fernanda Costa
- Vaga: PM Sênior - TechCorp
- Data de início: 01/02/2024
- Salário final: R$ 21.000

📊 MÉTRICAS DA VAGA:
- Time-to-fill: 18 dias
- Candidatos avaliados: 34
- Entrevistados: 8
- Taxa de conversão: 2.9%

🏆 PERFORMANCE VS. BENCHMARK:
- Time-to-fill: 25% mais rápido que média
- Qualidade: Score médio 85% (acima do esperado)

Posso fechar a vaga e avisar os outros candidatos?"

RECRUTADOR: "Sim, fecha e avisa"

LIA: "Perfeito! 
- Vaga fechada no Gupy ✅
- Vaga fechada no LinkedIn ✅
- Iniciando feedback para 7 candidatos restantes..."
```

**Agentes Envolvidos:**
- **Job Planner Agent**: Fecha vaga
- **Analytics Agent**: Calcula métricas
- **ATS Integrator Agent**: Sincroniza com ATS

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Integração com ATS para fechar vaga
- [ ] Dashboard de métricas de placement

---

### Etapa 27: Mass Feedback Node

**Objetivo:** Enviar feedback de encerramento para todos os candidatos restantes.

**Inputs Esperados:**
- Lista de candidatos não contratados
- Status de cada um no pipeline
- Template de feedback

**Outputs Esperados:**
- `feedbacks_sent`: number
- `delivery_status`: object

**Critérios de Sucesso:**
- Todos os candidatos notificados
- Feedback apropriado por estágio

**Comportamento da LIA:**
```
LIA: "Enviando feedback de encerramento para os candidatos restantes..."
```

**Exemplos de Diálogo:**

```
LIA: "📧 FEEDBACK DE ENCERRAMENTO - STATUS

Candidatos a notificar: 7

Por estágio:
- Em triagem: 2 → Feedback: Vaga encerrada
- Pós-triagem: 3 → Feedback: Outro candidato selecionado
- Shortlist final: 2 → Feedback: Personalizado (quase contratado)

Enviando...

✅ Concluído!
- Enviados: 7/7
- Entregues: 7
- Erros: 0

Todos os candidatos foram notificados sobre o encerramento 
da vaga. Os perfis permanecem na base para futuras oportunidades.

📊 RESUMO FINAL DA VAGA:
- Vaga: PM Sênior - TechCorp
- Status: FECHADA ✅
- Contratada: Fernanda Costa
- Início: 01/02/2024

Bom trabalho, João! A próxima vaga está agendada para 20/01. 
Quer que eu comece a preparar?"
```

*Exemplo de Feedback para Shortlist Final:*
```
LIA (para candidato): "Oi João,

Obrigada por participar do processo seletivo para PM Sênior 
na TechCorp. Você foi um dos finalistas e chegou muito perto!

A decisão foi extremamente difícil, e seu perfil impressionou 
todo o time. Optamos por outro candidato por uma questão de 
fit específico com o momento da empresa, não por qualificação.

Gostaria muito de manter contato para futuras oportunidades. 
Posso te avisar quando surgir algo alinhado?

Um abraço,
LIA - WeDOTalent"
```

**Agentes Envolvidos:**
- **Recruiter Assistant Agent**: Envia feedbacks em massa
- **Job Planner Agent**: Registra encerramento

**Status:** 🟡 Parcialmente Implementado

**Pendências:**
- [ ] Templates por estágio do pipeline
- [ ] Envio em batch com rate limiting

---

## SISTEMA DE SCORING LIA

### Composição do Score

O Score LIA é calculado como média ponderada de múltiplos componentes:

```
Score LIA = (
  Aderência × 0.25 +
  WSI × 0.25 +
  Técnico × 0.20 +
  Comportamental × 0.15 +
  TesteTécnico × 0.10 +  // quando disponível
  BigFive × 0.05          // quando disponível
) / SomaPesos
```

### Componentes do Score

| Componente | Descrição | Status | Peso Default |
|------------|-----------|--------|--------------|
| **Aderência ao Perfil** | Match com requisitos e perfil ideal | ✅ | 25% |
| **Score WSI** | Avaliação comportamental via triagem | ✅ | 25% |
| **Critérios Técnicos** | Hard skills da matriz técnica | ✅ | 20% |
| **Critérios Comportamentais** | Soft skills e fit cultural | ✅ | 15% |
| **Testes Técnicos** | Avaliações técnicas específicas | 🔴 | 10% |
| **Big Five** | Teste de personalidade OCEAN | 🔴 | 5% |

### Onde o Score Aparece

1. **Tabela de Candidatos**: Coluna "Score LIA" com indicador visual
2. **Kanban**: Badge no card do candidato
3. **Perfil do Candidato**: Breakdown completo por componente
4. **Relatórios**: Comparativo entre candidatos

---

## PENDÊNCIAS CONSOLIDADAS

### FASE 0: Setup & Calibração (100% pendente)

| ID | Pendência | Prioridade | Esforço |
|----|-----------|------------|---------|
| F0-1 | Schema CompanySetupState | Alta | Média |
| F0-2 | Node company_setup_node | Alta | Alta |
| F0-3 | Modelo de benefícios por área/nível | Alta | Média |
| F0-4 | Serviço de web scraping para cultura | Média | Alta |
| F0-5 | Integração Gupy API | Alta | Alta |
| F0-6 | Integração Pandapé API | Média | Alta |
| F0-7 | Integração Merge.dev | Baixa | Alta |
| F0-8 | Modelo de ML para pattern recognition | Média | Muito Alta |
| F0-9 | Schema IdealProfileState | Alta | Média |
| F0-10 | Node ideal_profile_builder_node | Alta | Alta |
| F0-11 | Sistema de versionamento de perfis | Baixa | Média |
| F0-12 | Integração Workforce Planning | Baixa | Alta |

### FASE 1: Criação da Vaga (90% implementado)

| ID | Pendência | Prioridade | Esforço |
|----|-----------|------------|---------|
| F1-1 | Integração com Workforce Planning para detecção proativa | Baixa | Alta |
| F1-2 | Sugestão automática de skills baseada no cargo | Média | Média |
| F1-3 | Integração com base de dados salariais | Média | Alta |
| F1-4 | Análise de viés mais sofisticada com ML | Baixa | Alta |
| F1-5 | Integração real com LinkedIn Job Slots | Média | Alta |
| F1-6 | Usar benefícios do Company Setup | Alta | Baixa |

### FASE 2-6: Sourcing até Fechamento (50% implementado)

| ID | Pendência | Prioridade | Esforço |
|----|-----------|------------|---------|
| F2-1 | Algoritmo de scoring com perfil ideal | Alta | Alta |
| F2-2 | Busca semântica no banco de dados | Alta | Alta |
| F2-3 | ML para calibração de scoring | Média | Muito Alta |
| F2-4 | Integração real Pearch AI API | Alta | Alta |
| F2-5 | Sistema de gestão de créditos | Alta | Média |
| F3-1 | Integração Mailgun/AWS SES | Alta | Média |
| F3-2 | Tracking de emails | Média | Média |
| F3-3 | Integração WhatsApp Business API | Alta | Alta |
| F4-1 | Timer 24h com reminder | Média | Baixa |
| F4-2 | Integração Microsoft Teams API | Alta | Alta |
| F4-3 | Adaptive Cards para Teams | Média | Média |
| F5-1 | Integração Microsoft Graph Calendar | Alta | Alta |
| F5-2 | Criação automática de eventos | Alta | Média |
| F6-1 | Dashboard de métricas de placement | Média | Média |
| F6-2 | Envio em batch com rate limiting | Baixa | Baixa |

### Sistema de Scoring (40% implementado)

| ID | Pendência | Prioridade | Esforço |
|----|-----------|------------|---------|
| SC-1 | Serviço de cálculo de score composto | Alta | Média |
| SC-2 | UI de exibição do score (tabela, kanban, perfil) | Alta | Média |
| SC-3 | Configuração de pesos por empresa | Média | Baixa |
| SC-4 | Módulo de Testes Técnicos | Baixa (pós-MVP) | Alta |
| SC-5 | Módulo Big Five | Baixa (pós-MVP) | Alta |

### Integrações Externas

| ID | Pendência | Prioridade | Esforço |
|----|-----------|------------|---------|
| INT-1 | Gupy ATS | Alta | Alta |
| INT-2 | Pandapé ATS | Média | Alta |
| INT-3 | Merge.dev (unified ATS) | Baixa | Alta |
| INT-4 | Microsoft Teams | Alta | Alta |
| INT-5 | Microsoft Graph Calendar | Alta | Alta |
| INT-6 | WhatsApp Business | Alta | Alta |
| INT-7 | Pearch AI | Alta | Alta |
| INT-8 | Mailgun/AWS SES | Alta | Média |
| INT-9 | Workforce Planning (TBD) | Baixa | Alta |

---

## PRIORIZAÇÃO PARA MVP

### Must Have (MVP)

1. ✅ Fase 1 completa (Criação da Vaga)
2. 🟡 Busca local com scoring básico
3. 🟡 Calibração manual de candidatos
4. 🟡 Triagem WSI por chat
5. 🟡 Feedback estruturado para candidatos
6. 🟡 Relatório para recrutador
7. 🔴 Agendamento de entrevistas
8. 🔴 Notificações via Teams

### Should Have (V1.1)

1. Fase 0 básica (Setup manual, sem ML)
2. Integração Pearch AI
3. Integração com 1 ATS (Gupy)
4. WhatsApp Business para triagem
5. Score composto com UI

### Nice to Have (V1.2+)

1. Fase 0 completa com ML
2. Testes Técnicos
3. Big Five Assessment
4. Múltiplos ATS
5. Workforce Planning

---

## Workflows Complementares

Os seguintes workflows são documentados em arquivos separados:

| Workflow | Documento | Descrição |
|----------|-----------|-----------|
| **Congelamento de Vaga** | [JOB_FREEZE_WORKFLOW.md](./JOB_FREEZE_WORKFLOW.md) | Fluxo completo de pausar processo seletivo, com papéis de cada agente |
| **Comunicação Omnicanal** | [communication-workflow.md](./communication-workflow.md) | Cadências de email, WhatsApp, notificações |
| **Integração ATS** | [ATS_INTEGRATION_SPEC.md](./ATS_INTEGRATION_SPEC.md) | Sincronização com Gupy, Pandapé |
| **Busca Pearch** | [PEARCH_FLOW.md](./PEARCH_FLOW.md) | Sourcing externo via Pearch AI |

---

*Documento gerado em: 30/11/2024*
*Última atualização: 21/01/2026*
*Versão: 1.1*
