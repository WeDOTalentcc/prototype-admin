# Templates de Pareceres e Feedbacks WSI

## Guia de Referência para Geração de Pareceres Estruturados

Os exemplos abaixo servem como referência para gerar pareceres de alta qualidade
baseados na metodologia WSI (WeDoTalent Skill Index). Cada parecer deve ser
fundamentado em evidências concretas extraídas das respostas do candidato.

---

## Exemplo 1: Candidato Excelente (WSI ≥ 4.5) — APROVADO

Vaga: Desenvolvedor(a) Python Sênior | WSI Geral: 4.7/5.0

```json
{
  "executive_summary": "Candidato com perfil técnico excepcional e forte alinhamento cultural. Demonstrou domínio avançado em Python, arquitetura de microsserviços e práticas de engenharia de software, com evidências concretas de impacto em projetos de alta complexidade. Recomendação: APROVADO para próxima etapa.",
  "technical_analysis": {
    "pontos_fortes": [
      "Domínio avançado de Python com experiência comprovada em FastAPI, SQLAlchemy e arquitetura hexagonal — citou refatoração que reduziu latência em 40%",
      "Experiência sólida em design de microsserviços com event-driven architecture, incluindo uso de Kafka e RabbitMQ em produção",
      "Práticas maduras de engenharia: TDD com cobertura >90%, CI/CD automatizado, observabilidade com Datadog e OpenTelemetry"
    ],
    "gaps": [],
    "evidencias": [
      "Liderou migração de monolito para microsserviços atendendo 2M req/dia",
      "Implementou pipeline de ML em produção com redução de 35% no churn",
      "Contribuiu com bibliotecas open-source (pytest-asyncio, httpx)"
    ]
  },
  "behavioral_analysis": {
    "colaboracao": 4.8,
    "inovacao": 4.7,
    "organizacao": 4.5,
    "resiliencia": 4.6
  },
  "cultural_fit": {
    "score": 4.7,
    "valores_alinhados": [
      "Excelência técnica e melhoria contínua",
      "Colaboração e mentoria de desenvolvedores juniores",
      "Ownership e responsabilidade por resultados end-to-end"
    ],
    "atencoes": []
  },
  "recommendation": {
    "decisao": "APROVADO",
    "justificativa": "Candidato demonstra competências técnicas e comportamentais alinhadas com o nível sênior exigido. Evidências concretas de impacto em projetos complexos, capacidade de liderança técnica e forte fit cultural. Perfil raro no mercado atual.",
    "proximos_passos": [
      "Agendar entrevista técnica aprofundada com Tech Lead",
      "Preparar case de system design para avaliação presencial",
      "Validar expectativa salarial e disponibilidade de início"
    ]
  }
}
```

---

## Exemplo 2: Candidato Médio (WSI 3.0–3.9) — AGUARDANDO

Vaga: Desenvolvedor(a) Python Sênior | WSI Geral: 3.4/5.0

```json
{
  "executive_summary": "Candidato apresenta base técnica sólida em Python, porém com lacunas em arquitetura de sistemas distribuídos e práticas avançadas de engenharia. Demonstrou boa capacidade colaborativa, mas precisa desenvolver habilidades de liderança técnica esperadas para o nível sênior. Recomendação: AGUARDANDO avaliação complementar.",
  "technical_analysis": {
    "pontos_fortes": [
      "Conhecimento sólido de Python e Django com 4 anos de experiência em aplicações web",
      "Familiaridade com bancos relacionais (PostgreSQL) e modelagem de dados",
      "Experiência prática com Docker e deploy em ambientes cloud (AWS EC2)"
    ],
    "gaps": [
      "Sem experiência prática com arquitetura de microsserviços — trabalhou apenas com monolitos",
      "Cobertura de testes limitada (~40%) e sem prática consistente de TDD",
      "Pouca experiência com mensageria assíncrona e event-driven architecture"
    ],
    "evidencias": [
      "Desenvolveu API REST com Django que atende 50K req/dia",
      "Participou de migração de banco de dados com downtime de 2h",
      "Não conseguiu descrever estratégias de escalabilidade horizontal"
    ]
  },
  "behavioral_analysis": {
    "colaboracao": 3.8,
    "inovacao": 3.0,
    "organizacao": 3.5,
    "resiliencia": 3.2
  },
  "cultural_fit": {
    "score": 3.5,
    "valores_alinhados": [
      "Trabalho em equipe e comunicação transparente",
      "Disposição para aprender novas tecnologias"
    ],
    "atencoes": [
      "Pode necessitar de ramp-up significativo em práticas de engenharia avançadas",
      "Perfil mais executor do que proponente de soluções arquiteturais"
    ]
  },
  "recommendation": {
    "decisao": "AGUARDANDO",
    "justificativa": "Candidato demonstra potencial técnico, mas apresenta gaps relevantes para o nível sênior, especialmente em arquitetura distribuída e práticas de engenharia. Recomenda-se avaliação técnica complementar para verificar capacidade de evolução rápida.",
    "proximos_passos": [
      "Aplicar teste técnico prático focado em design de APIs escaláveis",
      "Agendar conversa com gestor para avaliar fit com senioridade da vaga",
      "Considerar reposicionamento para vaga Pleno caso gaps se confirmem"
    ]
  }
}
```

---

## Exemplo 3: Candidato Baixo (WSI < 2.0) — NÃO APROVADO

Vaga: Desenvolvedor(a) Python Sênior | WSI Geral: 1.8/5.0

```json
{
  "executive_summary": "Candidato apresenta conhecimentos básicos em Python, insuficientes para o nível sênior exigido pela vaga. As respostas revelaram dificuldades em conceitos fundamentais de engenharia de software e ausência de experiência com sistemas em escala. Recomendação: NÃO APROVADO para esta posição, com feedback construtivo para desenvolvimento.",
  "technical_analysis": {
    "pontos_fortes": [
      "Conhecimento básico de sintaxe Python e uso de bibliotecas comuns (requests, pandas)"
    ],
    "gaps": [
      "Não demonstrou compreensão de padrões de projeto ou princípios SOLID",
      "Sem experiência com frameworks web profissionais — apenas scripts e automações simples",
      "Desconhecimento de práticas de versionamento avançado, CI/CD e testes automatizados",
      "Incapaz de descrever experiência com bancos de dados além de queries simples"
    ],
    "evidencias": [
      "Não conseguiu explicar diferença entre REST e GraphQL",
      "Descreveu apenas projetos pessoais e acadêmicos sem complexidade real",
      "Confundiu conceitos de concorrência com paralelismo"
    ]
  },
  "behavioral_analysis": {
    "colaboracao": 2.5,
    "inovacao": 1.5,
    "organizacao": 2.0,
    "resiliencia": 1.8
  },
  "cultural_fit": {
    "score": 2.0,
    "valores_alinhados": [
      "Interesse genuíno por tecnologia e disposição para aprender"
    ],
    "atencoes": [
      "Nível técnico atual incompatível com a senioridade da vaga",
      "Necessita de mentoria estruturada e experiência em projetos reais",
      "Risco de frustração mútua caso posicionado em equipe sênior"
    ]
  },
  "recommendation": {
    "decisao": "NAO_APROVADO",
    "justificativa": "O perfil técnico do candidato está significativamente abaixo do esperado para a posição sênior. Embora demonstre interesse em tecnologia, os gaps em fundamentos de engenharia, ausência de experiência profissional relevante e desconhecimento de práticas modernas de desenvolvimento tornam o candidato incompatível com os requisitos da vaga neste momento.",
    "proximos_passos": [
      "Enviar feedback construtivo com plano de desenvolvimento personalizado",
      "Sugerir recolocação em vagas de nível Júnior quando disponíveis",
      "Indicar recursos de aprendizado para evolução técnica"
    ]
  }
}
```

---

## Diretrizes para Geração de Pareceres WSI

### Princípios Fundamentais da Metodologia WSI para Pareceres

A geração de pareceres estruturados segue princípios científicos rigorosos baseados
nos 4 frameworks da metodologia WSI. Cada parecer deve refletir evidências concretas
coletadas durante a triagem e analisadas através dos frameworks CBI, Bloom, Dreyfus
e Big Five.

### Regras de Classificação e Decisão

| Faixa WSI    | Classificação | Decisão Recomendada | Ação                                     |
|-------------|---------------|--------------------|--------------------------------------------|
| 4.5 – 5.0   | Excelente     | APROVADO           | Avançar imediatamente para entrevista       |
| 4.0 – 4.4   | Alto          | APROVADO           | Avançar com prioridade                      |
| 3.0 – 3.9   | Médio         | AGUARDANDO         | Avaliação complementar necessária           |
| 2.0 – 2.9   | Regular       | AGUARDANDO/NÃO     | Considerar reposicionamento de senioridade  |
| Abaixo 2.0  | Baixo         | NÃO APROVADO       | Feedback construtivo + plano desenvolvimento|

### Estrutura Obrigatória do Parecer

Todo parecer WSI deve conter obrigatoriamente os seguintes componentes:

1. **Sumário Executivo**: Síntese em 2-3 frases que capture o perfil geral do
   candidato, seus diferenciais e a recomendação final. Deve ser suficiente para
   que o recrutador entenda o posicionamento sem ler o parecer completo.

2. **Análise Técnica**: Detalhamento dos pontos fortes técnicos (mínimo 1, máximo 5),
   gaps identificados (se houver), e evidências concretas extraídas das respostas.
   As evidências devem citar projetos, métricas ou situações específicas mencionadas.

3. **Análise Comportamental**: Avaliação das 4 dimensões comportamentais baseadas
   no Big Five adaptado: colaboração (Agreeableness), inovação (Openness),
   organização (Conscientiousness) e resiliência (Emotional Stability). Cada
   dimensão recebe score de 1.0 a 5.0.

4. **Fit Cultural**: Score geral de aderência cultural (1.0-5.0), lista de valores
   da empresa que o candidato demonstrou alinhamento, e pontos de atenção que
   podem impactar a integração do candidato na equipe.

5. **Recomendação**: Decisão fundamentada (APROVADO, AGUARDANDO ou NÃO APROVADO),
   justificativa baseada em evidências e próximos passos concretos e acionáveis.

### Boas Práticas na Redação de Pareceres

- Sempre fundamentar afirmações em evidências concretas das respostas do candidato
- Evitar julgamentos subjetivos sem base factual documentada
- Usar linguagem profissional, objetiva e respeitosa independente da classificação
- Quantificar sempre que possível (métricas, anos de experiência, escala de projetos)
- Destacar diferenciais competitivos do candidato em relação ao mercado
- Em casos de NÃO APROVADO, manter tom construtivo e indicar caminhos de evolução
- Considerar o contexto da vaga e da empresa ao formular a recomendação final
- Pareceres devem ser autocontidos: qualquer recrutador deve compreender sem contexto adicional

---

# Templates de Feedback para Candidatos WSI

## Guia de Tom e Estrutura para Feedbacks

Os feedbacks devem ser sempre construtivos, respeitosos e personalizados.
Independente da decisão, o candidato deve sair do processo com clareza
sobre seus pontos fortes, oportunidades de melhoria e próximos passos.

---

## Feedback 1: Decisão APROVADO (Tom: Empolgado e Encorajador)

Vaga: Desenvolvedor(a) Python Sênior | WSI: 4.7/5.0

```json
{
  "main_message": "Parabéns! Ficamos muito impressionados com o seu desempenho na triagem técnica. Sua experiência com Python e arquitetura de sistemas demonstra um perfil sênior maduro e alinhado com o que buscamos. Estamos entusiasmados em avançar com você para a próxima etapa!",
  "technical_strengths": [
    "Domínio avançado de Python e ecossistema (FastAPI, SQLAlchemy, pytest)",
    "Experiência comprovada em arquitetura de microsserviços em produção",
    "Práticas sólidas de engenharia: TDD, CI/CD, observabilidade"
  ],
  "development_opportunities": [
    "Explorar mais sobre Kubernetes e orquestração de containers em escala",
    "Aprofundar conhecimento em arquiteturas serverless como alternativa"
  ],
  "behavioral_strengths": [
    "Excelente capacidade de comunicação técnica e storytelling de projetos",
    "Forte mentalidade de ownership e responsabilidade por resultados",
    "Habilidade demonstrada em mentoria e colaboração com times"
  ],
  "next_steps": "Você avançou para a entrevista técnica aprofundada! Nossa equipe entrará em contato nos próximos 2 dias úteis para agendar a próxima conversa com o Tech Lead do time.",
  "personalized_tip": "Sua experiência com migração de monolito para microsserviços é um diferencial muito valorizado. Na próxima etapa, prepare-se para discutir trade-offs arquiteturais e decisões de design em maior profundidade.",
  "development_plan": {
    "curto_prazo": [
      "Revisar conceitos de system design para entrevista técnica",
      "Preparar exemplos adicionais de decisões arquiteturais complexas"
    ],
    "medio_prazo": [
      "Explorar certificações AWS Solutions Architect para complementar perfil",
      "Contribuir com talks técnicas internas como forma de liderança"
    ]
  },
  "recommended_resources": [
    "Livro: Designing Data-Intensive Applications (Martin Kleppmann)",
    "Curso: System Design Interview da Educative.io",
    "Comunidade: Python Brasil e PyConf para networking avançado"
  ]
}
```

---

## Feedback 2: Decisão AGUARDANDO (Tom: Construtivo e Empático)

Vaga: Desenvolvedor(a) Python Sênior | WSI: 3.4/5.0

```json
{
  "main_message": "Agradecemos muito sua participação no processo seletivo! Identificamos um bom potencial técnico no seu perfil. No momento, estamos avaliando alguns pontos complementares antes de uma decisão final. Queremos compartilhar um panorama do seu desempenho para que você saiba exatamente onde está e como pode continuar evoluindo.",
  "technical_strengths": [
    "Boa base em Python e Django com experiência prática relevante",
    "Conhecimento sólido em modelagem de dados com PostgreSQL",
    "Experiência com containerização usando Docker em ambiente produtivo"
  ],
  "development_opportunities": [
    "Aprofundar conhecimento em arquitetura de microsserviços e sistemas distribuídos",
    "Investir em práticas de TDD e aumentar cobertura de testes para acima de 80%",
    "Explorar mensageria assíncrona (RabbitMQ, Kafka) para processamento escalável"
  ],
  "behavioral_strengths": [
    "Boa capacidade de trabalho colaborativo e comunicação em equipe",
    "Demonstrou abertura para feedback e disposição para aprendizado contínuo"
  ],
  "next_steps": "Estamos finalizando a avaliação do seu perfil e entraremos em contato em até 5 dias úteis com uma atualização. Enquanto isso, aproveite as sugestões de desenvolvimento abaixo para fortalecer ainda mais seu perfil.",
  "personalized_tip": "Seu conhecimento em Django é uma base excelente. Para alcançar o nível sênior, recomendamos investir em projetos pessoais com FastAPI e arquitetura hexagonal — isso demonstrará evolução e versatilidade técnica.",
  "development_plan": {
    "curto_prazo": [
      "Iniciar projeto pessoal com FastAPI + arquitetura hexagonal",
      "Estudar padrões de comunicação entre microsserviços (sync vs async)",
      "Implementar pipeline de CI/CD com testes automatizados em projeto pessoal"
    ],
    "medio_prazo": [
      "Completar curso de System Design para engenheiros backend",
      "Contribuir com projetos open-source em Python para ganhar visibilidade",
      "Buscar mentoria com engenheiros seniores para acelerar evolução"
    ]
  },
  "recommended_resources": [
    "Curso: FastAPI Full Stack (TestDriven.io)",
    "Livro: Clean Architecture (Robert C. Martin)",
    "Plataforma: Exercism.io — trilha avançada de Python",
    "Repositório: awesome-python para explorar ecossistema"
  ]
}
```

---

## Feedback 3: Decisão NÃO APROVADO (Tom: Construtivo e Empático)

Vaga: Desenvolvedor(a) Python Sênior | WSI: 1.8/5.0

```json
{
  "main_message": "Agradecemos sinceramente sua participação no processo seletivo e o tempo dedicado à triagem técnica. Após análise cuidadosa, identificamos que seu perfil atual não atende aos requisitos técnicos desta vaga sênior neste momento. Isso não é um julgamento sobre seu potencial — queremos compartilhar um feedback detalhado para apoiar seu desenvolvimento profissional.",
  "technical_strengths": [
    "Conhecimento de sintaxe Python e uso de bibliotecas para automação",
    "Interesse genuíno por tecnologia e disposição para aprender"
  ],
  "development_opportunities": [
    "Aprofundar fundamentos de engenharia de software: padrões de projeto, SOLID, clean code",
    "Adquirir experiência com frameworks web profissionais (Django ou FastAPI)",
    "Desenvolver habilidades em bancos de dados relacionais e modelagem de dados",
    "Aprender e praticar versionamento com Git, CI/CD e testes automatizados"
  ],
  "behavioral_strengths": [
    "Demonstrou disposição para enfrentar desafios e sair da zona de conforto",
    "Mostrou curiosidade e vontade de evoluir na carreira de desenvolvimento"
  ],
  "next_steps": "Embora não tenhamos avançado neste processo, gostaríamos de manter seu perfil em nosso banco de talentos. À medida que você desenvolver as competências indicadas, ficaremos felizes em reavaliar seu perfil para futuras oportunidades, incluindo posições de nível Júnior ou Pleno.",
  "personalized_tip": "Recomendamos fortemente que você invista nos próximos 6 meses em um projeto prático completo — desde a concepção até o deploy. Isso vai acelerar enormemente seu aprendizado e construir o portfólio que recrutadores buscam.",
  "development_plan": {
    "curto_prazo": [
      "Completar curso estruturado de Python intermediário/avançado",
      "Iniciar projeto web completo com Django (blog, API REST, deploy)",
      "Estudar fundamentos: estruturas de dados, algoritmos, complexidade"
    ],
    "medio_prazo": [
      "Construir 2-3 projetos com complexidade crescente e publicar no GitHub",
      "Participar de comunidades técnicas (Python Brasil, meetups locais)",
      "Buscar estágio ou posição júnior para ganhar experiência profissional real",
      "Estudar padrões de projeto e princípios SOLID com exemplos práticos"
    ]
  },
  "recommended_resources": [
    "Curso: Python para Desenvolvedores (Udemy — Luiz Otávio Miranda)",
    "Curso: CS50 de Harvard (introdução completa à ciência da computação)",
    "Livro: Python Fluente (Luciano Ramalho) — referência essencial",
    "Plataforma: freeCodeCamp — trilha de backend com projetos guiados",
    "Comunidade: He4rt Developers — comunidade inclusiva para iniciantes"
  ]
}
```

---
