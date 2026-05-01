
"""
Few-shot examples for the Job Planner Agent.

Exemplos de criação de vagas, extração de requisitos, geração de perguntas WSI,
atualização de vagas e definição de matriz de competências.
"""

CREATE_DEVELOPER_JOB = {
    "user": "Crie uma vaga de Desenvolvedor Python Sênior, CLT, híbrido em São Paulo, faixa de 18 a 22k, precisa ter experiência com FastAPI, PostgreSQL e AWS.",
    "assistant": """📋 **Vaga Criada com Sucesso**

**Informações Básicas**
- Título: Desenvolvedor Python Sênior
- Senioridade: Sênior (5+ anos)
- Modalidade: CLT
- Modelo de trabalho: Híbrido (São Paulo)
- Faixa Salarial: R$ 18.000 - R$ 22.000

**Requisitos Obrigatórios (Hard Skills)**
| Competência | Nível Mínimo | Peso |
|-------------|--------------|------|
| Python | Proficiente (4) | 5 |
| FastAPI | Competente (3) | 4 |
| PostgreSQL | Competente (3) | 4 |
| AWS (EC2, S3, Lambda) | Competente (3) | 4 |
| Git/GitHub | Competente (3) | 3 |
| APIs REST | Proficiente (4) | 4 |

**Requisitos Desejáveis**
- Docker e Kubernetes
- Redis ou sistemas de cache
- Experiência com microsserviços
- Conhecimento em CI/CD

**Competências Comportamentais (Soft Skills)**
| Competência | Importância |
|-------------|-------------|
| Resolução de problemas | Alta |
| Comunicação técnica | Alta |
| Trabalho em equipe | Média |
| Proatividade | Média |
| Mentoria | Média |

**Perfil Ideal**
Profissional sênior com sólida experiência em desenvolvimento backend Python, capaz de arquitetar soluções escaláveis em cloud. Deve ter visão sistêmica, capacidade de mentoria de desenvolvedores mais juniores e boa comunicação para interagir com outras áreas.

**Perguntas WSI Sugeridas** (3 iniciais)
1. [Técnica - Dreyfus 4] "Descreva uma situação em que você precisou otimizar a performance de uma aplicação Python em produção. Qual foi o problema, como diagnosticou e qual solução implementou?"
2. [Comportamental - Big Five C] "Conte sobre um projeto complexo que você liderou tecnicamente. Como organizou as entregas e garantiu a qualidade?"
3. [Técnica - Bloom Analisar] "Como você decidiria entre usar Lambda functions ou containers EC2/ECS para um novo serviço? Quais critérios consideraria?"

💾 **Persistência**
- Dados salvos no WedoTalent: ✅
- ID da vaga: #DEV-PY-2024-001
- Sincronizado com ATS: ✅

➡️ **Próximos Passos**
1. Revisar e ajustar requisitos se necessário
2. Publicar vaga nos canais desejados
3. Iniciar sourcing de candidatos

Deseja que eu gere mais perguntas WSI ou ajuste algum requisito?""",
    "intent": "create_job",
    "context": {
        "vaga": "Desenvolvedor Python Sênior",
        "vaga_id": "DEV-PY-2024-001",
        "etapa": "criacao"
    }
}

EXTRACT_JD_REQUIREMENTS = {
    "user": """Extraia os requisitos desta JD:

"Buscamos um Engenheiro de Machine Learning para atuar no desenvolvimento de modelos de NLP para análise de sentimentos. Requisitos: Graduação em Ciência da Computação ou áreas afins, 3+ anos com Python, experiência com TensorFlow ou PyTorch, conhecimento em processamento de linguagem natural. Desejável: experiência com transformers (BERT, GPT), MLOps e deploy de modelos em produção. Oferecemos: CLT, remoto, benefícios flexíveis.""",
    "assistant": """📄 **Análise do Job Description**

**Cargo Identificado**: Engenheiro de Machine Learning
**Área**: Machine Learning / NLP
**Senioridade**: Pleno a Sênior (3+ anos)

**Hard Skills Extraídas**

*Requisitos Obrigatórios*
| Skill | Categoria | Peso Sugerido |
|-------|-----------|---------------|
| Python | Linguagem | 5 |
| TensorFlow ou PyTorch | Framework ML | 5 |
| NLP (Processamento de Linguagem Natural) | Especialidade | 5 |
| Análise de Sentimentos | Especialidade | 4 |
| Machine Learning | Área | 5 |

*Requisitos Desejáveis*
| Skill | Categoria | Peso Sugerido |
|-------|-----------|---------------|
| Transformers (BERT, GPT) | Framework NLP | 4 |
| MLOps | DevOps/ML | 3 |
| Deploy de modelos em produção | Operações | 3 |

**Soft Skills Identificadas** (implícitas no contexto)
- Pensamento analítico (necessário para ML)
- Curiosidade/Aprendizado contínuo (área em evolução)
- Comunicação técnica (explicar modelos)

**Formação**
- Graduação em Ciência da Computação ou áreas afins (obrigatório)
- Pós-graduação em IA/ML (desejável, não mencionado)

**Experiência Necessária**
- Mínimo: 3 anos com Python
- Experiência prática com projetos de ML/NLP

**Benefícios Identificados**
- Modalidade: CLT
- Modelo: Remoto
- Benefícios flexíveis

⚠️ **Pontos de Atenção**
1. JD não especifica faixa salarial - recomendo definir
2. Não menciona nível de senioridade explícito
3. Falta clareza sobre tamanho do time e escopo de responsabilidades
4. Considerar adicionar requisito de inglês (literatura técnica)

➡️ **Sugestões de Melhoria**
1. Adicionar faixa salarial para atrair candidatos qualificados
2. Especificar se é posição individual ou com gestão de equipe
3. Mencionar projetos/desafios específicos da área
4. Incluir stack de dados (Spark, Databricks, etc.) se aplicável

💾 **Persistência**
- Requisitos extraídos e salvos: ✅
- Pronto para criar vaga estruturada

Deseja que eu crie a vaga com base nestes requisitos?""",
    "intent": "extract_requirements",
    "context": {
        "vaga": "Engenheiro de Machine Learning",
        "etapa": "analise_jd"
    }
}

GENERATE_WSI_QUESTIONS = {
    "user": "Gere 5 perguntas WSI para a vaga de Product Manager com foco em métricas e stakeholder management.",
    "assistant": """🎯 **Perguntas WSI - Product Manager**

**Competências Avaliadas**: Métricas de Produto, Gestão de Stakeholders

---

**1. Pergunta Técnica - Métricas (Bloom: Analisar | Dreyfus: 4)**

> "Conte sobre uma situação em que você usou dados e métricas para tomar uma decisão importante de produto. Quais métricas você priorizou e por quê? Qual foi o impacto da decisão?"

**O que avaliar na resposta:**
- Conhecimento de métricas relevantes (NPS, retention, conversion, LTV)
- Capacidade analítica e pensamento crítico
- Conexão entre dados e decisões de negócio
- Mensuração de impacto

**Red flags:** Respostas genéricas sem métricas específicas, decisões baseadas apenas em intuição

---

**2. Pergunta Comportamental - Stakeholders (Big Five: Amabilidade + Extroversão)**

> "Descreva uma situação em que você precisou alinhar stakeholders com expectativas conflitantes sobre o roadmap do produto. Como você conduziu as conversas e chegou a um consenso?"

**O que avaliar na resposta:**
- Habilidade de negociação e mediação
- Comunicação assertiva mas empática
- Técnicas de priorização (RICE, MoSCoW, etc.)
- Construção de relacionamentos

**Red flags:** Imposição de decisões, evitar conflitos, falta de método de priorização

---

**3. Pergunta Técnica - Roadmap (Bloom: Criar | Dreyfus: 4)**

> "Se você assumisse nosso produto hoje, como estruturaria o processo para definir OKRs e métricas de sucesso do próximo trimestre? Que frameworks e rituais implementaria?"

**O que avaliar na resposta:**
- Conhecimento de OKRs e frameworks de produto
- Pensamento estratégico
- Capacidade de estruturar processos
- Visão de curto e longo prazo

**Red flags:** Foco apenas em features sem métricas, falta de envolvimento de stakeholders

---

**4. Pergunta Situacional - Métricas (Bloom: Avaliar | Dreyfus: 3)**

> "Imagine que uma métrica-chave do produto (ex: retenção) caiu 15% no último mês. Como você investigaria a causa e quais ações tomaria? Descreva seu processo de análise."

**O que avaliar na resposta:**
- Metodologia de investigação (hipóteses, segmentação, cohorts)
- Conhecimento de ferramentas analíticas
- Capacidade de agir sob pressão
- Comunicação de problemas para stakeholders

**Red flags:** Respostas superficiais, culpar outras áreas, falta de método estruturado

---

**5. Pergunta Comportamental - Influência (Big Five: Conscienciosidade + Extroversão)**

> "Conte sobre uma situação em que você precisou convencer a liderança a investir em uma iniciativa que não era prioridade inicialmente. Qual foi sua estratégia e como mediu o sucesso depois?"

**O que avaliar na resposta:**
- Habilidade de influência sem autoridade
- Uso de dados para persuasão
- Persistência e resiliência
- Foco em resultados

**Red flags:** Imposição, falta de dados de suporte, não mencionar resultados

---

**Matriz de Avaliação Resumida**

| Pergunta | Competência | Framework | Nível |
|----------|-------------|-----------|-------|
| 1 | Métricas de Produto | Bloom Analisar | Proficiente |
| 2 | Gestão de Stakeholders | Big Five A+E | - |
| 3 | Roadmap/OKRs | Bloom Criar | Proficiente |
| 4 | Análise de Dados | Bloom Avaliar | Competente |
| 5 | Influência | Big Five C+E | - |

💾 **Persistência**
- Perguntas salvas na vaga: ✅
- Prontas para uso em entrevistas

➡️ **Próximos Passos**
1. Revisar e personalizar para contexto específico
2. Definir peso de cada pergunta no score final
3. Treinar entrevistadores no método WSI

Deseja que eu gere perguntas adicionais focadas em outras competências?""",
    "intent": "generate_wsi_questions",
    "context": {
        "vaga": "Product Manager",
        "etapa": "definicao_entrevista",
        "foco": ["métricas", "stakeholder management"]
    }
}

UPDATE_EXISTING_JOB = {
    "user": "Atualize a vaga de Desenvolvedor Python: adicione conhecimento em Kafka como requisito desejável e aumente a faixa salarial para 20-25k.",
    "assistant": """✏️ **Vaga Atualizada**

**Vaga**: Desenvolvedor Python Sênior
**ID**: #DEV-PY-2024-001

**Alterações Realizadas**

| Campo | Valor Anterior | Novo Valor |
|-------|----------------|------------|
| Faixa Salarial | R$ 18.000 - R$ 22.000 | R$ 20.000 - R$ 25.000 |
| Requisitos Desejáveis | Docker, Kubernetes, Redis, CI/CD | Docker, Kubernetes, Redis, CI/CD, **Apache Kafka** |

**Detalhamento da Adição**

*Novo Requisito Desejável*
| Skill | Categoria | Peso | Justificativa |
|-------|-----------|------|---------------|
| Apache Kafka | Streaming/Mensageria | 3 | Processamento de eventos em tempo real |

**Impacto Estimado**
- A nova faixa salarial está 13% acima da anterior
- O requisito de Kafka pode reduzir o pool de candidatos em ~15%
- Recomendação: Manter como desejável, não obrigatório

**Estado Atual da Vaga**
```
Requisitos Obrigatórios:
✓ Python (Proficiente)
✓ FastAPI (Competente)
✓ PostgreSQL (Competente)
✓ AWS (Competente)
✓ Git/GitHub (Competente)
✓ APIs REST (Proficiente)

Requisitos Desejáveis:
○ Docker e Kubernetes
○ Redis ou sistemas de cache
○ Microsserviços
○ CI/CD
○ Apache Kafka (NOVO)

Faixa Salarial: R$ 20.000 - R$ 25.000 (ATUALIZADO)
```

💾 **Persistência**
- Vaga atualizada no WedoTalent: ✅
- Histórico de alteração registrado: ✅
- Sincronizado com ATS: ✅
- Timestamp: 30/01/2024 14:35

➡️ **Próximos Passos**
1. Notificar equipe de sourcing sobre novos critérios
2. Reavaliar candidatos já no pipeline (podem ter Kafka)
3. Ajustar boolean string de busca

Deseja que eu notifique a equipe ou faça alguma outra alteração?""",
    "intent": "update_job",
    "context": {
        "vaga": "Desenvolvedor Python Sênior",
        "vaga_id": "DEV-PY-2024-001",
        "etapa": "edicao"
    }
}

DEFINE_COMPETENCY_MATRIX = {
    "user": "Defina a matriz de competências para a vaga de Tech Lead Frontend.",
    "assistant": """📊 **Matriz de Competências - Tech Lead Frontend**

**Vaga**: Tech Lead Frontend
**Senioridade**: Tech Lead (6+ anos)

---

## Competências Técnicas (Hard Skills) - Peso 60%

### Essenciais (Obrigatórias)

| Competência | Nível Mínimo (Dreyfus) | Peso | Critérios de Avaliação |
|-------------|------------------------|------|------------------------|
| React/Next.js | Expert (5) | 5 | Arquitetura de apps complexos, SSR/SSG, otimização |
| TypeScript | Proficiente (4) | 5 | Tipagem avançada, generics, patterns |
| Arquitetura Frontend | Proficiente (4) | 5 | Design systems, microfrontends, state management |
| Performance Web | Proficiente (4) | 4 | Core Web Vitals, lazy loading, code splitting |
| Testes (Jest/Cypress) | Competente (3) | 4 | Cobertura, E2E, integração contínua |
| Git/GitHub | Proficiente (4) | 3 | Code review, branching strategies, CI/CD |

### Desejáveis

| Competência | Nível Ideal | Peso | Diferencial |
|-------------|-------------|------|-------------|
| Design Systems | Competente (3) | 3 | Criação e manutenção de component libraries |
| Acessibilidade (A11y) | Competente (3) | 3 | WCAG, screen readers, testes de acessibilidade |
| GraphQL | Competente (3) | 2 | Apollo, schemas, otimização de queries |
| AWS/Cloud | Iniciante Avançado (2) | 2 | CloudFront, S3, Lambda@Edge |

---

## Competências Comportamentais (Soft Skills) - Peso 40%

### Liderança e Gestão

| Competência | Importância | Indicadores Comportamentais (Big Five) |
|-------------|-------------|----------------------------------------|
| Liderança Técnica | Crítica | Mentoria, decisões arquiteturais, influência |
| Gestão de Pessoas | Alta | Feedback, desenvolvimento de equipe, delegação |
| Comunicação | Alta | Apresentação, documentação, alinhamento cross-funcional |

### Traços Big Five Relevantes

| Traço | Nível Desejado | Por quê? |
|-------|----------------|----------|
| Conscienciosidade (C) | Alto | Organização, qualidade, cumprimento de prazos |
| Extroversão (E) | Médio-Alto | Comunicação com stakeholders, liderança visível |
| Abertura (O) | Alto | Inovação, aprendizado contínuo, novas tecnologias |
| Amabilidade (A) | Médio-Alto | Colaboração, mentoria, empatia com o time |
| Neuroticismo (N) | Baixo | Estabilidade sob pressão, gestão de crises |

---

## Níveis de Avaliação (Dreyfus)

| Nível | Score | Descrição |
|-------|-------|-----------|
| Novato (1) | 0-20 | Segue regras, precisa de orientação constante |
| Iniciante Avançado (2) | 21-40 | Reconhece padrões, alguma autonomia |
| Competente (3) | 41-60 | Planeja, prioriza, resolve problemas comuns |
| Proficiente (4) | 61-80 | Visão holística, adapta soluções ao contexto |
| Expert (5) | 81-100 | Intuição, inovação, referência técnica |

---

## Perguntas de Avaliação por Competência

**React/Next.js (Expert)**
> "Descreva a arquitetura frontend mais complexa que você projetou. Quais decisões tomou sobre SSR/SSG, gerenciamento de estado e como mediu o sucesso?"

**Liderança Técnica**
> "Conte sobre uma situação em que você precisou convencer o time a adotar uma nova tecnologia ou padrão. Como conduziu o processo de decisão?"

**Performance Web**
> "Qual foi o maior problema de performance que você resolveu? Quais métricas usou para diagnóstico e qual foi o impacto da solução?"

---

## Pesos Finais para Scoring

```
Score Final = (Score Técnico × 0.60) + (Score Comportamental × 0.40)

Score Técnico = Σ(competência × peso) / Σ(pesos)
Score Comportamental = Σ(competência × peso) / Σ(pesos)

Threshold de Aprovação: 70/100
Threshold para Shortlist: 80/100
```

💾 **Persistência**
- Matriz salva na vaga: ✅
- Vinculada às perguntas WSI: ✅
- Pronta para avaliação de candidatos

➡️ **Próximos Passos**
1. Validar matriz com o gestor da vaga
2. Ajustar pesos se necessário
3. Gerar perguntas WSI para cada competência crítica

Deseja ajustar algum peso ou adicionar competências?""",
    "intent": "define_competency_matrix",
    "context": {
        "vaga": "Tech Lead Frontend",
        "etapa": "definicao_matriz"
    }
}

JOB_PLANNER_EXAMPLES = [
    CREATE_DEVELOPER_JOB,
    EXTRACT_JD_REQUIREMENTS,
    GENERATE_WSI_QUESTIONS,
    UPDATE_EXISTING_JOB,
    DEFINE_COMPETENCY_MATRIX,
]
