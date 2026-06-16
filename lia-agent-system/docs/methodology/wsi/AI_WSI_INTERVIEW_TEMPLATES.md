# WSI Templates: Frameworks, Perguntas, Calibração e Pareceres

**Última Atualização:** 30 Janeiro 2026

> **Documento Consolidado**: Este guia integra todos os templates e frameworks científicos da metodologia WSI.

---

## Índice

1. [Frameworks Científicos (CBI, Bloom, Dreyfus, Big Five)](#1-frameworks-científicos)
2. [Templates de Perguntas por Framework](#2-templates-de-perguntas-por-framework)
3. [Guia de Calibração de Scores](#3-guia-de-calibração-de-scores)
4. [Templates de Pareceres e Feedbacks](#4-templates-de-pareceres-e-feedbacks)

---

## 1. Frameworks Científicos

A metodologia WSI integra **4 frameworks científicos consolidados** para avaliação de competências:

1. **CBI** (Competency-Based Interviewing) - McClelland, 1973
2. **Bloom's Taxonomy** (Revisada) - Anderson et al., 2001  
3. **Dreyfus Model** - Dreyfus & Dreyfus, 1980
4. **Big Five (OCEAN)** - Goldberg, 1992

### 1.1 CBI - Competency-Based Interviewing

#### Princípio Fundamental
> "Comportamentos passados são os melhores preditores de performance futura."

#### Estrutura de Pergunta CBI
```
"Conte sobre uma situação em que [contexto específico]."
```

#### Análise STAR
- **S**ituation: Quando? Onde? Qual o contexto?
- **T**ask: Qual era o desafio/objetivo?
- **A**ction: O que você fez especificamente?
- **R**esult: Qual foi o resultado/impacto?

#### Aplicação na LIA
- Perguntas contextuais para validar experiência real
- Análise de microhistórias profissionais
- Detecção de evidências concretas vs. genéricas

---

### 1.2 Taxonomia de Bloom (Revisada)

#### Hierarquia Cognitiva (6 Níveis)

```
Nível 6: CRIAR
↑       Gerar soluções novas, arquitetar sistemas
│
Nível 5: AVALIAR  
↑       Julgar qualidade, tomar decisões
│
Nível 4: ANALISAR
↑       Diferenciar conceitos, identificar padrões
│
Nível 3: APLICAR
↑       Usar conhecimento em prática
│
Nível 2: COMPREENDER
↑       Explicar ideias, interpretar
│
Nível 1: LEMBRAR
        Recordar fatos e conceitos
```

#### Aplicação na LIA
- Classificar profundidade técnica das respostas
- Perguntas tipo microcase (níveis 3-5)
- Diferenciar conhecimento teórico (1-2) de prático (3-5)

---

### 1.3 Modelo Dreyfus - 5 Estágios de Maturidade

#### Escala 1-5 (Novice → Expert)

**Score 5 - EXPERT (Especialista)**
- Domínio intuitivo e contextual
- Toma decisões sem deliberação consciente
- Ensina outros, documenta, lidera tecnicamente
- Exemplos: Contribui para open source, mentora, arquiteta soluções

**Score 4 - PROFICIENT (Proficiente)**
- Aplicação autônoma e adaptativa
- Reconhece padrões, antecipa problemas
- Resolve problemas complexos sem supervisão
- Exemplos: Otimiza performance, mentora juniors, toma decisões técnicas

**Score 3 - COMPETENT (Competente)**
- Execução estável e consistente
- Segue boas práticas, entrega com qualidade
- Precisa de orientação em cenários novos
- Exemplos: Desenvolve features, escreve testes, documenta código

**Score 2 - ADVANCED BEGINNER (Iniciante Avançado)**
- Aplicação parcial e guiada
- Conhece ferramentas, mas precisa de supervisão
- Entrega tarefas simples com sucesso
- Exemplos: Fez projetos simples, estudando frameworks

**Score 1 - NOVICE (Novato)**
- Conhecimento apenas teórico
- Sem experiência prática relevante
- Precisa de treinamento extensivo
- Exemplos: Fez curso online, sem projeto real

#### Aplicação na LIA
- Base do sistema de scoring 1-5
- Calibração automática de respostas
- Validação: autodeclaração vs. contexto real

---

### 1.4 Big Five (OCEAN Model)

#### Os 5 Traços Comportamentais

**O - Openness (Abertura)**
- Curiosidade, criatividade, inovação
- Abertura para novas experiências
- Pergunta LIA: "Conte sobre uma vez em que propôs uma solução inovadora"

**C - Conscientiousness (Conscienciosidade)**
- Organização, disciplina, foco em resultado
- Confiabilidade e responsabilidade
- Pergunta LIA: "Como você garante qualidade e prazos em projetos complexos?"

**E - Extraversion (Extroversão)**
- Energia, assertividade, liderança
- Comunicação e influência
- Pergunta LIA: "Descreva como você se comunica em reuniões técnicas"

**A - Agreeableness (Amabilidade)**
- Empatia, colaboração, trabalho em equipe
- Capacidade de conciliar opiniões
- Pergunta LIA: "Fale sobre um projeto onde precisou conciliar opiniões divergentes"

**N - Neuroticism (Estabilidade Emocional)**
- Controle emocional sob pressão
- Resiliência e adaptabilidade
- Pergunta LIA: "Como você reage quando recebe feedback crítico?"

#### Aplicação na LIA
- Avaliação de fit cultural e comportamental
- Perguntas situacionais
- Score de aderência à cultura da empresa

---

### 1.5 Convergência dos 4 Frameworks

```
┌─────────────────────────────────────────┐
│         Pergunta Técnica                │
│  "De 1 a 5, quanto domina Python?      │
│   Cite um projeto recente."             │
└─────────────────────────────────────────┘
           │
           ├──────────────┬──────────────┬──────────────┐
           ▼              ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │   CBI    │   │  Dreyfus │   │  Bloom   │   │ Big Five │
    │          │   │          │   │          │   │          │
    │ Valida   │   │ Score    │   │ Nível    │   │ Fit      │
    │ contexto │   │ 1-5      │   │ cognitivo│   │ cultural │
    │ real     │   │          │   │          │   │          │
    └──────────┘   └──────────┘   └──────────┘   └──────────┘
           │              │              │              │
           └──────────────┴──────────────┴──────────────┘
                          ▼
              ┌────────────────────────┐
              │   Score Final WSI      │
              │   (média ponderada)    │
              └────────────────────────┘
```

### 1.6 Validade Preditiva

```
Metodologia Tradicional:
└─ Entrevista não estruturada: r < 0.30

Metodologia WSI (4 frameworks):
└─ Validação cruzada: r ≥ 0.60

Ganho: +100% em validade preditiva!
```

### 1.7 Referências

1. McClelland, D. C. (1973). Testing for competence rather than for intelligence. American Psychologist.
2. Anderson, L. W., et al. (2001). A Taxonomy for Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy.
3. Dreyfus, H. L., & Dreyfus, S. E. (1980). A Five-Stage Model of the Mental Activities Involved in Directed Skill Acquisition.
4. Goldberg, L. R. (1992). The development of markers for the Big-Five factor structure.

---

## 2. Templates de Perguntas por Framework

### 2.1 Perguntas CBI (Competency-Based Interviewing)

#### Estrutura Base
```
"Conte sobre uma situação em que [desafio/contexto específico]. 
 O que você fez e qual foi o resultado?"
```

#### Templates por Área Técnica

##### Python
```
1. "Conte sobre uma situação em que você precisou otimizar código Python para melhorar performance. O que você fez e qual foi o resultado?"

2. "Descreva um projeto em que você usou Python para resolver um problema complexo de dados. Qual era o desafio, o que você implementou e qual foi o impacto?"

3. "Fale sobre uma vez em que você teve que debugar um problema crítico em produção usando Python. Como você identificou e resolveu?"

4. "Conte sobre uma biblioteca Python que você domina profundamente. Em qual projeto aplicou e quais decisões técnicas tomou?"

5. "Descreva uma situação em que você precisou implementar testes automatizados em Python. Como estruturou e qual foi a cobertura alcançada?"
```

##### JavaScript/React
```
1. "Conte sobre um componente React complexo que você desenvolveu. Qual era o desafio, como estruturou e quais padrões aplicou?"

2. "Descreva uma situação em que você precisou otimizar performance de uma aplicação React. O que você identificou e como resolveu?"

3. "Fale sobre uma vez em que você integrou APIs externas em React. Quais desafios enfrentou e como tratou erros/loading?"

4. "Conte sobre um projeto em que você usou state management (Redux/Context/etc). Por que escolheu essa abordagem e qual foi o resultado?"

5. "Descreva uma experiência em que você trabalhou com formulários complexos em React. Como estruturou validação e UX?"
```

##### SQL/Databases
```
1. "Conte sobre uma query SQL complexa que você otimizou. Qual era o problema de performance e como melhorou?"

2. "Descreva uma situação em que você modelou um banco de dados do zero. Quais decisões técnicas tomou e por quê?"

3. "Fale sobre uma vez em que você precisou fazer migrations em banco com dados em produção. Como planejou e executou?"

4. "Conte sobre um problema de performance em banco de dados que você resolveu. Quais técnicas aplicou (índices, partições, etc.)?"

5. "Descreva uma experiência com transações e consistência de dados. Qual era o desafio e como garantiu integridade?"
```

##### DevOps/Cloud
```
1. "Conte sobre um pipeline CI/CD que você implementou do zero. Quais ferramentas usou e qual foi o impacto no time?"

2. "Descreva uma situação em que você configurou infraestrutura em cloud (AWS/GCP/Azure). Quais decisões arquiteturais tomou?"

3. "Fale sobre uma vez em que você resolveu um problema crítico de deployment ou downtime. Como diagnosticou e resolveu?"

4. "Conte sobre uma experiência com containers (Docker/Kubernetes). Qual era o projeto e como estruturou?"

5. "Descreva uma situação em que você implementou monitoramento e observability. Quais métricas escolheu e por quê?"
```

##### Design/UX
```
1. "Conte sobre um redesign de interface que você liderou. Qual era o problema de UX e como validou a solução?"

2. "Descreva uma situação em que você conduziu pesquisa com usuários. Quais métodos usou e quais insights descobriu?"

3. "Fale sobre um design system que você criou ou contribuiu. Como estruturou componentes e documentação?"

4. "Conte sobre uma vez em que você precisou balancear requisitos de negócio com UX. Como negociou e qual foi o resultado?"

5. "Descreva uma experiência com acessibilidade (WCAG). Quais desafios enfrentou e como implementou?"
```

##### Produto/PM
```
1. "Conte sobre uma feature que você priorizou no roadmap. Como tomou a decisão e qual foi o impacto?"

2. "Descreva uma situação em que você usou dados para tomar uma decisão de produto. Quais métricas analisou?"

3. "Fale sobre um projeto em que você precisou alinhar stakeholders com visões divergentes. Como conduziu?"

4. "Conte sobre uma vez em que você definiu KPIs para uma nova funcionalidade. Como escolheu e acompanhou?"

5. "Descreva uma experiência com discovery de produto. Quais técnicas usou para validar hipóteses?"
```

---

### 2.2 Perguntas Dreyfus (Autodeclaração + Contexto)

#### Estrutura Base
```
"De 1 a 5, quanto você domina [tecnologia/skill]?
 Pode citar um projeto recente onde aplicou?"
```

#### Templates por Tecnologia

##### Linguagens
```
1. "De 1 a 5, quanto você domina Python? Pode citar um projeto recente onde aplicou?"
2. "De 1 a 5, quanto você domina JavaScript? Pode citar um projeto onde usou conceitos avançados?"
3. "De 1 a 5, quanto você domina TypeScript? Pode descrever como estruturou tipos em um projeto?"
4. "De 1 a 5, quanto você domina SQL? Pode citar uma query complexa que escreveu recentemente?"
5. "De 1 a 5, quanto você domina HTML/CSS? Pode falar sobre um layout desafiador que implementou?"
```

##### Frameworks/Libraries
```
1. "De 1 a 5, quanto você domina React? Pode citar um projeto onde aplicou padrões avançados?"
2. "De 1 a 5, quanto você domina FastAPI/Django? Pode descrever uma API complexa que desenvolveu?"
3. "De 1 a 5, quanto você domina Next.js? Pode falar sobre otimizações de performance que fez?"
4. "De 1 a 5, quanto você domina Docker? Pode citar como estruturou containers em um projeto?"
5. "De 1 a 5, quanto você domina Figma? Pode descrever um design system que criou?"
```

##### Conceitos
```
1. "De 1 a 5, quanto você domina Arquitetura de Software? Pode citar decisões arquiteturais que tomou?"
2. "De 1 a 5, quanto você domina Testes Automatizados? Pode descrever sua estratégia de testes?"
3. "De 1 a 5, quanto você domina Git/Versionamento? Pode falar sobre workflows que já usou?"
4. "De 1 a 5, quanto você domina Performance Optimization? Pode citar otimizações que fez?"
5. "De 1 a 5, quanto você domina Segurança? Pode descrever boas práticas que aplica?"
```

---

### 2.3 Microcases Bloom (Aplicar/Analisar/Criar)

#### Nível 3: APLICAR

```
1. "Como você implementaria autenticação JWT em uma API FastAPI?"
   Framework: Bloom (Aplicar)
   Expected: Código prático, bibliotecas, fluxo básico

2. "Descreva como você estruturaria um formulário multi-step em React."
   Framework: Bloom (Aplicar)
   Expected: State management, validação, UX

3. "Como você faria deploy de uma aplicação Node.js na AWS?"
   Framework: Bloom (Aplicar)
   Expected: Serviços AWS, configuração, CI/CD básico
```

#### Nível 4: ANALISAR

```
1. "Uma query SQL está demorando 30 segundos. Como você diagnosticaria o problema?"
   Framework: Bloom (Analisar)
   Expected: EXPLAIN, índices, plano de execução

2. "Sua aplicação React está renderizando muito. Quais técnicas usaria para otimizar?"
   Framework: Bloom (Analisar)
   Expected: React DevTools, memo, useMemo, profiling

3. "Compare REST vs GraphQL para uma API de e-commerce. Qual escolheria e por quê?"
   Framework: Bloom (Analisar)
   Expected: Trade-offs, casos de uso, decisão fundamentada
```

#### Nível 5: CRIAR

```
1. "Projete uma arquitetura de microsserviços para uma plataforma de streaming com 1M usuários."
   Framework: Bloom (Criar)
   Expected: Decisões arquiteturais, comunicação, escalabilidade

2. "Crie uma estratégia de testes para uma aplicação crítica de pagamentos."
   Framework: Bloom (Criar)
   Expected: Pirâmide de testes, cobertura, automação

3. "Desenhe um sistema de cache distribuído para reduzir latência em 80%."
   Framework: Bloom (Criar)
   Expected: Tecnologias (Redis, etc.), invalidação, consistência
```

---

### 2.4 Perguntas Big Five (Comportamental/Cultural)

#### Openness (Inovação, Aprendizado)
```
1. "Conte sobre uma vez em que você propôs uma solução inovadora para um problema técnico. Como foi recebida?"

2. "Descreva uma situação em que você aprendeu uma nova tecnologia por conta própria. O que motivou e como aplicou?"

3. "Fale sobre um projeto em que você experimentou uma abordagem não convencional. Qual foi o resultado?"

4. "Conte sobre uma vez em que você questionou um processo estabelecido e sugeriu melhorias."

5. "Descreva como você se mantém atualizado com tendências tecnológicas."
```

#### Conscientiousness (Organização, Entrega)
```
1. "Como você garante qualidade e prazos em projetos complexos?"

2. "Descreva sua abordagem para documentação de código e projetos."

3. "Conte sobre uma situação em que você teve que gerenciar múltiplas prioridades. Como organizou?"

4. "Fale sobre um projeto em que você implementou padrões de qualidade (code review, testes, etc.)."

5. "Descreva como você estrutura suas tarefas diárias para maximizar produtividade."
```

#### Extraversion (Comunicação, Liderança)
```
1. "Descreva como você se comunica em reuniões técnicas com stakeholders não-técnicos."

2. "Conte sobre uma vez em que você liderou uma discussão técnica importante."

3. "Fale sobre uma situação em que você apresentou uma solução para um grupo. Como se preparou?"

4. "Descreva sua experiência com pair programming ou code review."

5. "Conte sobre um projeto em que você colaborou intensamente com outros times."
```

#### Agreeableness (Colaboração, Empatia)
```
1. "Fale sobre um projeto onde precisou conciliar opiniões divergentes no time."

2. "Conte sobre uma vez em que você ajudou um colega a resolver um problema técnico complexo."

3. "Descreva uma situação em que você recebeu feedback crítico. Como reagiu?"

4. "Fale sobre um conflito técnico que você mediou no time."

5. "Conte sobre uma experiência de mentoria (formal ou informal)."
```

#### Emotional Stability (Resiliência, Pressão)
```
1. "Como você reage quando recebe feedback crítico sobre seu trabalho?"

2. "Conte sobre uma situação de alta pressão (deadline, bug crítico, etc.). Como lidou?"

3. "Descreva uma vez em que um projeto fracassou ou não saiu como planejado. O que aprendeu?"

4. "Fale sobre como você gerencia estresse em períodos intensos de trabalho."

5. "Conte sobre uma situação em que você precisou se adaptar rapidamente a mudanças inesperadas."
```

---

### 2.5 Variáveis de Customização

#### Por Senioridade

**Junior:**
- Focar em projetos de estudo, freelas, primeiro emprego
- Exemplos: "curso", "tutorial seguido", "projeto acadêmico"

**Pleno:**
- Projetos reais, features completas, trabalho em equipe
- Exemplos: "no projeto atual", "na empresa anterior"

**Senior:**
- Arquitetura, otimizações, mentoria, liderança técnica
- Exemplos: "arquitetei", "defini padrões", "mentorei"

**Lead/Principal:**
- Decisões estratégicas, impacto em múltiplos times
- Exemplos: "estabeleci", "transformei", "escalei"

#### Por Cultura da Empresa

**Startup:**
- Velocidade, autonomia, ownership
- "Como você priorizou em contexto de recursos limitados?"

**Enterprise:**
- Processos, compliance, governança
- "Como você seguiu padrões corporativos mantendo inovação?"

**Remote-first:**
- Comunicação assíncrona, autonomia
- "Como você colaborou em time 100% remoto?"

**Tech-heavy:**
- Inovação, experimentação, contribuição open source
- "Conte sobre contribuições técnicas fora do trabalho."

---

### 2.6 Exemplo de Customização Completa

#### Vaga: Senior Python Backend Engineer

```yaml
Competências:
  - Python (peso: 0.25)
  - FastAPI/Django (peso: 0.20)
  - SQL/PostgreSQL (peso: 0.15)
  - Docker/K8s (peso: 0.10)
  - Arquitetura (peso: 0.15)
  - Colaboração (peso: 0.15)

Perguntas Geradas (Compact Mode - 6 perguntas):
  1. [CBI] "Conte sobre uma arquitetura de microsserviços Python que você desenhou. Quais decisões tomou e qual foi o impacto?" (Arquitetura)
  
  2. [Dreyfus] "De 1 a 5, quanto domina FastAPI? Cite uma API complexa que desenvolveu." (FastAPI)
  
  3. [CBI] "Descreva uma otimização de SQL/PostgreSQL que fez. Qual era o problema e como resolveu?" (SQL)
  
  4. [Bloom] "Uma API FastAPI está com latência de 3s. Como diagnosticaria e otimizaria?" (Python + FastAPI)
  
  5. [Dreyfus] "De 1 a 5, quanto domina Docker/Kubernetes? Cite como estruturou containers." (DevOps)
  
  6. [Big Five] "Fale sobre um projeto onde precisou alinhar stakeholders técnicos e de negócio." (Colaboração)

Total: 6 perguntas, ~5-7 min via WhatsApp
```

---

### 2.7 Diretrizes para Geração

1. **Especificidade:** Sempre pedir projeto/contexto concreto
2. **Mensurabilidade:** Incluir "qual foi o resultado/impacto"
3. **Autenticidade:** Detectar respostas genéricas
4. **Profundidade:** STAR (Situation, Task, Action, Result)
5. **Relevância:** Alinhar com JD e competências priorizadas

---

### 2.8 Output de Pergunta Bem Estruturada

```json
{
  "id": "q_001",
  "framework": "CBI",
  "competency": "Python",
  "question_type": "contextual",
  "question_text": "Conte sobre uma situação em que você precisou otimizar código Python para melhorar performance. O que você fez e qual foi o resultado?",
  "weight": 0.25,
  "expected_signals": [
    "Contexto claro (quando, onde, projeto)",
    "Ação técnica específica (profiling, algoritmo, biblioteca)",
    "Resultado mensurável (latência, throughput, custo)"
  ],
  "scoring_criteria": {
    "score_5": "Contexto complexo + decisões técnicas avançadas (Cython, multiprocessing) + impacto quantificado (50% redução)",
    "score_3": "Contexto claro + ação técnica (list comprehension, caching) + resultado visível",
    "score_1": "Contexto vago + ação genérica (pesquisei, melhorei) + sem resultado"
  }
}
```

---

## 3. Guia de Calibração de Scores

### 3.1 Metodologia de Scoring

#### Fórmula Base
```
Score Final = (0.6 × Autodeclaração) + (0.4 × Contexto) - Penalty + Bonus
```

#### Componentes

**1. Autodeclaração (Score 1-5)**
- Número declarado pelo candidato ("4 de 5")
- Se não declarou: inferir do tom da resposta

**2. Contexto (Score 1-5)**
- Baseado em evidências concretas (STAR)
- Nível Bloom (1-5 cognitivo)
- Profundidade técnica

**3. Penalty**
- Inflação de score: -1.0 a -1.5
- Resposta genérica: -0.5
- Falta de contexto: -0.3

**4. Bonus**
- Humildade (autodeclara 3, contexto mostra 5): +0.5
- Evidências excepcionais: +0.3

---

### 3.2 Score 5 - EXPERT (Especialista)

#### Sinais Obrigatórios
✅ Liderança técnica (mentora, ensina, documenta)
✅ Contribuições significativas (open source, comunidade)
✅ Decisões arquiteturais complexas
✅ Métricas de impacto quantificáveis
✅ Domínio intuitivo e contextual

#### Exemplos REAIS de Score 5

**Exemplo 1 - Python**
```
Pergunta: "De 1 a 5, quanto domina Python? Cite projeto recente."

Resposta Score 5:
"5. Sou maintainer de uma biblioteca open source com 8K stars no GitHub 
(httpx-async). Arquitetei o sistema de retry e circuit breaker que hoje 
processa 50M requisições/dia em produção. Também contribuí para o CPython 
(PR #12345 sobre async context managers). No projeto atual, otimizei pipeline 
de ML que reduziu latência de 12s para 800ms usando multiprocessing + Cython. 
Mentoro 3 devs Python e dou talks sobre asyncio."

Análise LIA:
├─ Autodeclaração: 5
├─ Contexto: 5 (evidências excepcionais)
├─ Bloom Level: 5 (Criar - otimizações avançadas)
├─ Dreyfus: 5 (Expert - liderança técnica)
├─ Evidências:
│  ├─ Maintainer open source (8K stars)
│  ├─ Contribuição para CPython
│  ├─ Métricas quantificadas (50M req/dia, 12s→800ms)
│  ├─ Decisões técnicas complexas (circuit breaker)
│  └─ Mentoria + talks (ensina outros)
└─ Score Final: 5.0
```

**Exemplo 2 - Arquitetura**
```
Resposta Score 5:
"5. Arquitetei a migração de monolito para microsserviços em empresa com 
5M usuários. Defini padrões de comunicação (event-driven com Kafka), 
estratégia de deployment (blue-green + canary), e observability stack 
(Prometheus + Grafana + Jaeger). Resultado: 99.99% uptime (antes 99.5%), 
time to market de features reduziu de 2 semanas para 2 dias. Documentei 
tudo em ADRs (Architecture Decision Records) e treinei 4 squads."

Análise LIA:
├─ Autodeclaração: 5
├─ Contexto: 5
├─ Decisões arquiteturais de alto impacto
├─ Métricas de negócio (uptime, time to market)
├─ Documentação (ADRs) + Treinamento
└─ Score Final: 5.0
```

---

### 3.3 Score 4 - PROFICIENT (Proficiente)

#### Sinais Obrigatórios
✅ Autonomia completa em projetos complexos
✅ Otimizações e melhorias proativas
✅ Mentoria de juniors (mesmo que informal)
✅ Decisões técnicas sem supervisão
✅ Reconhece padrões e antecipa problemas

#### Exemplos REAIS de Score 4

**Exemplo 1 - FastAPI**
```
Resposta Score 4:
"4. Desenvolvo APIs complexas em FastAPI há 3 anos. No projeto atual, 
implementei rate limiting com Redis (100 req/min por usuário), caching 
de queries pesadas (reduziu tempo de 2s para 150ms), e observability 
com New Relic. Configurei CI/CD completo com testes automatizados 
(coverage 85%). Já mentorei 2 devs juniors em boas práticas de API design."

Análise LIA:
├─ Autodeclaração: 4
├─ Contexto: 4
├─ Bloom Level: 4 (Analisar - otimizações)
├─ Dreyfus: 4 (Proficient - autonomia)
├─ Evidências:
│  ├─ 3 anos experiência
│  ├─ Decisões técnicas (rate limiting, caching)
│  ├─ Métricas (2s→150ms, coverage 85%)
│  └─ Mentoria informal
└─ Score Final: 4.0
```

---

### 3.4 Score 3 - COMPETENT (Competente)

#### Sinais Obrigatórios
✅ Execução consistente de features
✅ Segue boas práticas (testes, code review)
✅ Entrega com qualidade
✅ Precisa orientação em cenários novos
✅ 1-3 anos de experiência prática

#### Exemplos REAIS de Score 3

**Exemplo 1 - React**
```
Resposta Score 3:
"3. Desenvolvo interfaces React há 2 anos. No projeto atual, implementei 
dashboard com gráficos (Chart.js), formulários com validação (React Hook Form), 
e state management com Context API. Escrevo testes com Jest e sigo padrões 
de componentização. Ainda tenho dúvidas em performance optimization, mas 
entrego features com qualidade."

Análise LIA:
├─ Autodeclaração: 3
├─ Contexto: 3
├─ Bloom Level: 3 (Aplicar - usa frameworks)
├─ Dreyfus: 3 (Competent - execução consistente)
├─ Evidências:
│  ├─ 2 anos experiência
│  ├─ Ferramentas específicas (Chart.js, Hook Form)
│  ├─ Boas práticas (testes, padrões)
│  └─ Reconhece gaps (performance)
└─ Score Final: 3.0
```

---

### 3.5 Score 2 - ADVANCED BEGINNER (Iniciante Avançado)

#### Sinais Obrigatórios
✅ Conhece ferramentas básicas
✅ Precisa de supervisão constante
✅ Entrega tarefas simples com sucesso
✅ 6 meses - 1 ano de experiência
✅ Projetos de estudo ou simples

#### Exemplos REAIS de Score 2

**Exemplo 1 - SQL**
```
Resposta Score 2:
"2. Fiz alguns projetos com SQL na faculdade e num freela simples. 
Sei fazer queries básicas (SELECT, JOIN, WHERE), mas ainda tenho 
dificuldade com queries complexas e otimização. Usei PostgreSQL 
num projeto de to-do list."

Análise LIA:
├─ Autodeclaração: 2
├─ Contexto: 2
├─ Bloom Level: 2 (Compreender - conceitos básicos)
├─ Dreyfus: 2 (Advanced Beginner - guiado)
├─ Evidências:
│  ├─ Projetos simples (faculdade, freela)
│  ├─ Conhecimento básico (SELECT, JOIN)
│  ├─ Reconhece limitações (otimização)
│  └─ Sem experiência em produção
└─ Score Final: 2.0
```

---

### 3.6 Score 1 - NOVICE (Novato)

#### Sinais Obrigatórios
✅ Apenas conhecimento teórico
✅ Sem experiência prática relevante
✅ Estudando ou fez curso recentemente
✅ Não cita projetos reais
✅ Linguagem vaga e genérica

#### Exemplos REAIS de Score 1

**Exemplo 1 - Docker**
```
Resposta Score 1:
"1. Fiz um curso de Docker na Udemy há 3 meses, mas ainda não usei 
profissionalmente. Entendo os conceitos de containers e imagens, 
mas só rodei exemplos do curso no meu notebook."

Análise LIA:
├─ Autodeclaração: 1
├─ Contexto: 1
├─ Bloom Level: 1 (Lembrar - conceitos)
├─ Dreyfus: 1 (Novice - apenas teórico)
├─ Evidências:
│  └─ Apenas curso (sem projeto real)
└─ Score Final: 1.0
```

---

### 3.7 Red Flags: Casos Problemáticos

#### 1. Inflação de Score

```
Resposta PROBLEMÁTICA:
"5. Sou expert em Python, domino totalmente."

Contexto: Não cita projetos, tecnologias específicas, métricas.

Análise LIA:
├─ Autodeclaração: 5
├─ Contexto: 1.5 (genérico, sem evidências)
├─ Inconsistência detectada: SIM
├─ Penalty: -1.5
└─ Score Final: 2.0
   Alert: "Autodeclaração não validada por evidências"
```

#### 2. Resposta Genérica

```
Resposta PROBLEMÁTICA:
"4. Trabalhei com React em alguns projetos."

Análise LIA:
├─ Autodeclaração: 4
├─ Contexto: 2.0 (vago, sem especificidade)
├─ Penalty: -0.5 (falta de contexto)
└─ Score Final: 2.5
   Alert: "Resposta muito genérica - pedir mais detalhes"
```

#### 3. Resposta Copiada

```
Resposta PROBLEMÁTICA:
"React é uma biblioteca JavaScript para construir interfaces de usuário, 
desenvolvida pelo Facebook, que utiliza componentes reutilizáveis..."

(Texto copiado de documentação)

Análise LIA:
├─ Red Flag: Resposta parece documentação
├─ Penalty: -1.0
└─ Score Final: 1.5
   Alert: "Resposta aparenta ser copiada - avaliar autenticidade"
```

---

### 3.8 Casos Edge: Como Decidir

#### Caso 1: Entre Scores (3.5-4.0)
```
Regra: Se em dúvida, arredondar para BAIXO (conservador).
Exceção: Se evidências excepcionais, arredondar para CIMA.

Exemplo:
Autodeclaração: 4
Contexto: 3.5 (bom, mas falta mentoria/liderança)
→ Score Final: 3.8 (arredonda para 4 se >3.75, senão 3)
```

#### Caso 2: Humildade (Autodeclara Baixo, Contexto Alto)
```
Resposta:
"3. Desenvolvo APIs, mas ainda estou aprendendo."
Contexto: Cita otimizações, métricas, decisões técnicas (Score 4).

Análise LIA:
├─ Autodeclaração: 3
├─ Contexto: 4
├─ Bonus: +0.5 (humildade)
└─ Score Final: 4.0
```

#### Caso 3: Resposta Longa mas Superficial
```
Regra: Quantidade ≠ Qualidade.
Avaliar: Evidências concretas, não número de palavras.

Exemplo:
Resposta de 200 palavras, mas sem projeto específico, sem métricas.
→ Score: 2.0 (superficial, apesar de longo)
```

---

### 3.9 Checklist de Validação

Antes de atribuir score final, LIA deve verificar:

```
✅ Autodeclaração foi extraída corretamente?
✅ Contexto tem evidências concretas (STAR)?
✅ Nível Bloom foi identificado (1-5)?
✅ Nível Dreyfus condiz com experiência descrita?
✅ Red flags foram detectados?
✅ Penalty/Bonus foram aplicados corretamente?
✅ Score final está entre 1.0 e 5.0?
✅ Justificativa está clara e fundamentada?
```

---

### 3.10 Exemplos de Justificativas

**Score 5:**
"Domínio expert comprovado por liderança técnica (maintainer open source com 8K stars), contribuições para CPython, e impacto mensurável (50M req/dia, redução de latência de 12s para 800ms). Mentoria ativa e talks demonstram capacidade de ensinar."

**Score 4:**
"Domínio proficiente com autonomia completa em projetos complexos. Implementou otimizações (rate limiting, caching com ganho de 2s→150ms) e mentoria de 2 devs juniors. Experiência sólida de 3 anos."

**Score 3:**
"Execução competente com 2 anos de experiência. Segue boas práticas (testes, padrões de código) e entrega features com qualidade. Reconhece limitações em performance optimization."

**Score 2:**
"Conhecimento inicial com prática limitada. Projetos simples (faculdade, freela) demonstram conceitos básicos, mas sem experiência em produção ou problemas complexos."

**Score 1:**
"Conhecimento apenas teórico. Fez curso recentemente mas sem aplicação prática. Precisa de experiência hands-on para evoluir."

---

### 3.11 Target de Precisão

```yaml
Cohen's Kappa: ≥ 0.85
  (Agreement entre LIA e avaliadores humanos)

Margem de Erro: ±0.3
  (Ex: Score humano 4.0, LIA pode dar 3.7-4.3)

Red Flag Detection:
  Precision: ≥ 90%
  Recall: ≥ 80%
```

---

## 4. Templates de Pareceres e Feedbacks

### 4.1 Parecer Estruturado (Para Recrutadores)

#### Estrutura Completa

```markdown
# PARECER TÉCNICO - [Nome do Candidato]

**Vaga:** [Título da Vaga]
**Data da Triagem:** [DD/MM/AAAA]
**Avaliado por:** LIA (WeDoTalent Skill Index)

---

## SUMÁRIO EXECUTIVO

[2-3 frases resumindo o perfil geral, pontos fortes principais e recomendação]

**WSI Geral:** [X.X]/5.0 - [Classificação]
**Recomendação:** [APROVADO / AGUARDANDO / NÃO APROVADO]

---

## ANÁLISE TÉCNICA

### Pontos Fortes
- **[Competência 1]** (Score: [X.X]/5): [Breve descrição da evidência]
- **[Competência 2]** (Score: [X.X]/5): [Breve descrição da evidência]
- **[Competência 3]** (Score: [X.X]/5): [Breve descrição da evidência]

### Gaps Identificados
- **[Competência 4]** (Score: [X.X]/5): [Descrição do gap]
- **[Competência 5]** (Score: [X.X]/5): [Descrição do gap]

### Evidências Concretas
[Lista de projetos, métricas, contribuições mencionadas pelo candidato]

---

## ANÁLISE COMPORTAMENTAL

### Colaboração e Comunicação
[Avaliação baseada em Big Five - Agreeableness + Extraversion]
Score: [X.X]/5

### Inovação e Aprendizado
[Avaliação baseada em Big Five - Openness]
Score: [X.X]/5

### Organização e Entrega
[Avaliação baseada em Big Five - Conscientiousness]
Score: [X.X]/5

### Resiliência
[Avaliação baseada em Big Five - Emotional Stability]
Score: [X.X]/5

---

## FIT CULTURAL

**Score Geral:** [X.X]/5

### Valores Alinhados
- [Valor 1]: [Como demonstrou alinhamento]
- [Valor 2]: [Como demonstrou alinhamento]

### Pontos de Atenção
- [Potencial desalinhamento cultural]

---

## RECOMENDAÇÃO FINAL

**Decisão:** [APROVADO / AGUARDANDO ENTREVISTA TÉCNICA / NÃO APROVADO]

**Justificativa:**
[2-3 parágrafos explicando a decisão baseada em WSI, fit técnico, fit cultural]

**Próximos Passos Sugeridos:**
[Se aprovado: agendar técnica, verificar X, Y]
[Se aguardando: pedir código, avaliar Z]
[Se não aprovado: perfil não condizente com senioridade/stack]

---

**Gerado por:** LIA WSI v1.0
**Data:** [DD/MM/AAAA HH:MM]
```

---

### 4.2 Exemplo: APROVADO (WSI 4.5 - Excelente)

```markdown
# PARECER TÉCNICO - João Silva

**Vaga:** Senior Python Backend Engineer
**Data da Triagem:** 24/11/2025
**Avaliado por:** LIA (WeDoTalent Skill Index)

---

## SUMÁRIO EXECUTIVO

João demonstrou domínio expert em Python e FastAPI, comprovado por liderança técnica, contribuições open source (8K stars), e impacto mensurável em produção (50M req/dia, latência reduzida de 12s para 800ms). Perfil altamente qualificado para vaga senior com excelente fit cultural.

**WSI Geral:** 4.5/5.0 - Excelente
**Recomendação:** APROVADO

---

## ANÁLISE TÉCNICA

### Pontos Fortes
- **Python** (Score: 5.0/5): Maintainer de biblioteca open source (httpx-async, 8K stars), contribuiu para CPython, aplicou Cython em produção com impacto mensurável (12s→800ms).
- **Arquitetura** (Score: 4.5/5): Implementou circuit breaker e retry patterns processando 50M req/dia em produção.
- **FastAPI** (Score: 4.5/5): APIs complexas com rate limiting, caching, e observability (New Relic).
- **Mentoria** (Score: 5.0/5): Mentora 3 devs Python, dá talks sobre asyncio, documentação ativa.

### Gaps Identificados
- **Kubernetes** (Score: 3.0/5): Conhecimento intermediário, usou em projetos mas sem decisões arquiteturais complexas.

### Evidências Concretas
- Maintainer httpx-async (8K stars GitHub)
- Contribuição CPython (PR #12345 async context managers)
- Otimização ML pipeline: 12s → 800ms (Cython + multiprocessing)
- Sistema em produção: 50M requisições/dia, 99.99% uptime
- Mentoria de 3 desenvolvedores Python
- Talks públicas sobre asyncio

---

## ANÁLISE COMPORTAMENTAL

### Colaboração e Comunicação
Excelente capacidade de ensinar (mentoria, talks, documentação detalhada). Compartilha conhecimento ativamente na comunidade open source.
Score: 5.0/5

### Inovação e Aprendizado
Contribui para CPython e mantém biblioteca open source popular. Busca proativamente otimizações e soluções de alto impacto.
Score: 5.0/5

### Organização e Entrega
Implementou sistema processando 50M req/dia com uptime de 99.99%, demonstrando excelência operacional e confiabilidade.
Score: 4.5/5

### Resiliência
Não avaliado diretamente nesta triagem, mas histórico de contribuições consistentes sugere boa resiliência.
Score: N/A

---

## FIT CULTURAL

**Score Geral:** 4.5/5

### Valores Alinhados
- **Excelência Técnica**: Contribuições para CPython e biblioteca com 8K stars demonstram compromisso com qualidade.
- **Compartilhamento de Conhecimento**: Mentoria ativa e talks públicas alinham perfeitamente com cultura colaborativa.
- **Orientação a Resultados**: Todas as otimizações foram medidas e tiveram impacto quantificável.

### Pontos de Atenção
- Nenhum identificado. Perfil altamente alinhado com valores da empresa.

---

## RECOMENDAÇÃO FINAL

**Decisão:** APROVADO PARA ENTREVISTA TÉCNICA

**Justificativa:**
João apresenta um dos perfis mais fortes já avaliados pela LIA com WSI de 4.5 (Excelente). O domínio expert em Python está comprovado por liderança técnica (maintainer open source, contribuições CPython, mentoria), impacto mensurável em produção (50M req/dia, otimizações significativas), e engajamento com a comunidade (talks, documentação). 

O único gap identificado (Kubernetes intermediário) é facilmente mitigável e não impacta negativamente a senioridade para a vaga de Python Backend, que prioriza domínio da linguagem e arquitetura de APIs.

O fit cultural é excepcional, especialmente em compartilhamento de conhecimento e excelência técnica, valores core da empresa.

**Próximos Passos Sugeridos:**
1. Agendar entrevista técnica presencial
2. Preparar case técnico focado em arquitetura de APIs (área de força)
3. Discutir expectativas de liderança técnica e mentoria no time
4. Validar interesse em contribuições open source como parte do trabalho

---

**Gerado por:** LIA WSI v1.0
**Data:** 24/11/2025 18:45
```

---

### 4.3 Exemplo: NÃO APROVADO (WSI 2.0 - Regular)

```markdown
# PARECER TÉCNICO - Maria Santos

**Vaga:** Senior Python Backend Engineer
**Data da Triagem:** 24/11/2025
**Avaliado por:** LIA (WeDoTalent Skill Index)

---

## SUMÁRIO EXECUTIVO

Maria demonstra conhecimento teórico de Python e conceitos de backend, mas sem experiência prática relevante para nível senior. Projetos mencionados são acadêmicos ou muito simples, sem evidências de produção, otimizações, ou liderança técnica. Perfil mais adequado para vagas pleno ou junior.

**WSI Geral:** 2.0/5.0 - Regular
**Recomendação:** NÃO APROVADO (senioridade abaixo do esperado)

---

## ANÁLISE TÉCNICA

### Pontos Fortes
- **Python** (Score: 2.5/5): Conhece sintaxe básica, fez projetos acadêmicos.
- **SQL** (Score: 2.0/5): Queries básicas (SELECT, JOIN), sem otimização.

### Gaps Identificados
- **FastAPI/Django** (Score: 1.5/5): Apenas conhecimento teórico, sem projeto real.
- **Arquitetura** (Score: 1.0/5): Não demonstrou experiência com decisões arquiteturais.
- **Produção** (Score: 1.0/5): Nenhum projeto em produção mencionado.
- **Liderança Técnica** (Score: 1.0/5): Sem experiência de mentoria ou liderança.

### Evidências Concretas
- Projeto acadêmico: to-do list com Flask
- Freela simples: script de automação Python
- Curso Udemy de FastAPI (não aplicado)

---

## ANÁLISE COMPORTAMENTAL

### Colaboração e Comunicação
Limitada. Projetos principalmente solo, sem experiência de code review ou trabalho em equipe técnico.
Score: 2.0/5

### Inovação e Aprendizado
Demonstra interesse em aprender (curso Udemy), mas sem aplicação prática ou projetos pessoais relevantes.
Score: 2.5/5

### Organização e Entrega
Não foi possível avaliar por falta de projetos estruturados.
Score: N/A

---

## FIT CULTURAL

**Score Geral:** 2.5/5

### Valores Alinhados
- **Aprendizado Contínuo**: Demonstra interesse em estudar, fez curso recentemente.

### Pontos de Atenção
- **Falta de Ownership**: Projetos simples, sem evidências de iniciativa ou projetos pessoais.
- **Experiência Limitada**: Perfil muito junior para cultura de autonomia esperada.

---

## RECOMENDAÇÃO FINAL

**Decisão:** NÃO APROVADO (senioridade incompatível)

**Justificativa:**
Maria apresenta um perfil de iniciante avançado (WSI 2.0) com conhecimento teórico de Python, mas sem experiência prática relevante para uma vaga senior. Os projetos mencionados (to-do list acadêmico, script de automação) são típicos de perfil júnior e não demonstram:
- Trabalho em produção
- Otimizações ou decisões técnicas complexas
- Arquitetura ou design de sistemas
- Liderança técnica ou mentoria

A vaga exige domínio avançado de Python, FastAPI, arquitetura de microsserviços e capacidade de mentoria – nenhum desses critérios foi atendido.

**Próximos Passos Sugeridos:**
1. Não seguir com processo para vaga senior
2. Considerar perfil para vagas pleno ou júnior (após validação adicional)
3. Se houver interesse futuro, candidata deve buscar:
   - Experiência hands-on em produção (1-2 anos)
   - Projetos pessoais ou contribuições open source
   - Estudo aplicado de FastAPI/Django em projetos reais

---

**Gerado por:** LIA WSI v1.0
**Data:** 24/11/2025 19:15
```

---

### 4.4 Feedback para Candidatos

#### Template Geral

```markdown
Olá [Nome]!

Obrigado por participar do processo seletivo para [Vaga] na [Empresa]. 

[MENSAGEM PRINCIPAL - varia por decisão]

---

## 💪 Seus Pontos Fortes

Durante a triagem, identificamos estas qualidades:

**Técnico:**
- [Ponto forte 1]
- [Ponto forte 2]
- [Ponto forte 3]

**Comportamental:**
- [Ponto forte 1]
- [Ponto forte 2]

---

## 🎯 Oportunidades de Desenvolvimento

Para continuar evoluindo sua carreira, sugerimos foco em:

- [Oportunidade 1]
- [Oportunidade 2]
- [Oportunidade 3]

---

## 📚 Recursos Recomendados

[Se não aprovado, incluir sugestões de cursos, projetos, leituras]

---

## 🚀 Próximos Passos

[Varia por decisão]

---

Qualquer dúvida, estamos à disposição!

Equipe [Empresa] + LIA
```

---

### 4.5 Exemplo: Feedback APROVADO

```markdown
Olá João!

Obrigado por participar do processo seletivo para Senior Python Backend Engineer na TechCorp.

**Parabéns! Você foi aprovado para a próxima etapa!** 🎉

Ficamos muito impressionados com seu domínio técnico em Python, suas contribuições open source, e especialmente com os resultados mensuráveis que você alcançou em projetos anteriores.

---

## 💪 Seus Pontos Fortes

Durante a triagem, identificamos estas qualidades excepcionais:

**Técnico:**
- **Python Expert**: Maintainer de biblioteca com 8K stars, contribuições para CPython
- **Impacto em Produção**: Sistema processando 50M req/dia com 99.99% uptime
- **Otimizações Avançadas**: Reduziu latência de 12s para 800ms usando Cython + multiprocessing
- **Arquitetura**: Implementou circuit breaker e retry patterns em escala

**Comportamental:**
- **Liderança Técnica**: Mentoria de 3 desenvolvedores, talks públicas
- **Compartilhamento de Conhecimento**: Documentação ativa, contribuições comunidade
- **Orientação a Resultados**: Todas otimizações medidas e quantificadas

---

## 🎯 Oportunidades de Desenvolvimento

Identificamos uma oportunidade de crescimento:

- **Kubernetes/Orquestração**: Aprofundar conhecimento em K8s para decisões arquiteturais de infra

(Mas isso não é impeditivo! É apenas uma sugestão para evolução contínua.)

---

## 🚀 Próximos Passos

1. **Entrevista Técnica Presencial** - Agendaremos para a semana de [data]
2. **Case Técnico** - Focado em arquitetura de APIs (sua área de força)
3. **Bate-papo com CTO** - Discutir liderança técnica e mentoria no time

Nossa equipe entrará em contato em até 2 dias úteis para agendar.

---

Estamos muito animados para conhecê-lo melhor!

Equipe TechCorp + LIA
```

---

### 4.6 Exemplo: Feedback NÃO APROVADO (Tom Construtivo)

```markdown
Olá Maria!

Obrigado por participar do processo seletivo para Senior Python Backend Engineer na TechCorp.

Após análise cuidadosa, decidimos não seguir com seu perfil para esta vaga especificamente. Mas queremos compartilhar feedback construtivo para ajudar sua evolução profissional! 🚀

---

## 💪 Seus Pontos Fortes

Durante a triagem, identificamos estas qualidades:

**Técnico:**
- **Fundamentos Python**: Você domina a sintaxe básica e conceitos fundamentais
- **Vontade de Aprender**: Fez curso de FastAPI por iniciativa própria
- **SQL Básico**: Conhece queries essenciais (SELECT, JOIN)

**Comportamental:**
- **Proatividade no Aprendizado**: Busca ativamente novos conhecimentos
- **Comunicação Clara**: Respondeu de forma objetiva e honesta

---

## 🎯 Oportunidades de Desenvolvimento

Para alcançar nível senior, sugerimos foco em:

### Curto Prazo (3-6 meses)
- **Projeto Real em Produção**: Desenvolver uma API completa em FastAPI e colocá-la online
- **GitHub Ativo**: Criar portfólio com 3-5 projetos bem documentados
- **Boas Práticas**: Estudar e aplicar testes, CI/CD, code review

### Médio Prazo (6-12 meses)
- **Experiência Profissional**: Buscar vaga pleno para ganhar vivência em produção
- **Otimizações**: Estudar performance, profiling, caching
- **Arquitetura**: Aprender padrões de design, microsserviços

---

## 📚 Recursos Recomendados

### Cursos
- [FastAPI - The Complete Course](link) - Do básico ao avançado
- [SQL Performance Explained](link) - Otimização de queries
- [Python Design Patterns](link) - Padrões arquiteturais

### Projetos Sugeridos
1. **API de Blog** - CRUD completo, autenticação JWT, deploy
2. **E-commerce Backend** - Carrinho, pagamentos, webhooks
3. **Sistema de Notificações** - Workers assíncronos, filas

### Comunidades
- Python Brasil (Discord)
- FastAPI Brasil (Telegram)
- Stack Overflow em Português

---

## 🚀 Próximos Passos

Embora não sigamos com esta vaga senior, **adoraríamos vê-la aplicar novamente** quando tiver mais experiência prática!

**Sugestão:**
1. Desenvolva 2-3 projetos relevantes nos próximos 6 meses
2. Busque uma vaga pleno para ganhar experiência em produção
3. Reaplique quando se sentir confiante!

**Você tem potencial! Só precisa de mais prática hands-on. 💪**

---

Continue crescendo e não desista! Estamos torcendo por você.

Equipe TechCorp + LIA
```

---

### 4.7 Variáveis de Customização

#### Tom por Decisão
- **Aprovado**: Empolgação, reconhecimento, transparência
- **Aguardando**: Encorajamento, expectativa clara, próximos passos
- **Não Aprovado**: Empatia, construtividade, recursos práticos

#### Personalização
- Sempre citar evidências específicas do candidato
- Evitar feedback genérico ("bom profissional", "continue estudando")
- Sugestões práticas e acionáveis
- Tom respeitoso e profissional sempre

#### Evitar
- ❌ Comparações com outros candidatos
- ❌ Negatividade excessiva
- ❌ Julgamentos pessoais
- ❌ Promessas vagas ("quem sabe no futuro")

---

*Documento Consolidado - Versão 1.0*
*Última atualização: Janeiro 2026*
*Metodologia: Rubric-Based Assessment + WSI Framework*
