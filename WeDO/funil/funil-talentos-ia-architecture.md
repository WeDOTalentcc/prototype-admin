# ARQUITETURA DE IA - FUNIL DE TALENTOS

> **Versao:** 1.0  
> **Data:** Dezembro 2024  
> **Modulo:** Funil de Talentos (candidates-page.tsx)  
> **Objetivo:** Documentar todos os pontos de IA para analise arquitetural

---

## SUMARIO

1. [Inventario de IA por Localizacao](#1-inventario-de-ia-por-localizacao)
2. [Documentacao Detalhada por Ponto de IA](#2-documentacao-detalhada-por-ponto-de-ia)
3. [Analise Arquitetural](#3-analise-arquitetural)
4. [Matriz de Decisao: Agente vs Servico vs Chamada](#4-matriz-de-decisao)
5. [O que E IA e NAO Deveria Ser](#5-o-que-e-ia-e-nao-deveria-ser)
6. [O que NAO E IA e Poderia Ser](#6-o-que-nao-e-ia-e-poderia-ser)
7. [Recomendacoes](#7-recomendacoes)
8. [Resumo Executivo](#8-apendice-resumo-executivo)
9. [Comandos e Sugestoes do Prompt Expandido](#9-comandos-e-sugestoes-do-prompt-expandido-super-chat-lia)

---

# 1. INVENTARIO DE IA POR LOCALIZACAO

## 1.1 Tab BUSCA (Principal)

| ID | Funcionalidade | Componente Frontend | Tipo Atual |
|----|----------------|---------------------|------------|
| IA-01 | Sugestao Preditiva (Autocomplete) | SmartSearchInput | Servico |
| IA-02 | Extracao de Entidades | SmartSearchInput -> ContextPills | Servico |
| IA-03 | Correcao/Ajuste de Termos | SmartSearchInput | Servico |
| IA-04 | Query Expansion | Backend (busca) | Servico |
| IA-05 | Unificacao de URLs | Modo "Perfil Similar" | Servico |
| IA-06 | Busca por Perfil Similar | ModeSelector | Agente (Sourcing) |
| IA-07 | Busca por Job Description | ModeSelector | Agente (Sourcing) |
| IA-08 | Busca por Arquetipos Big Five | ModeSelector | Servico |
| IA-09 | Validacao Boolean Assistida | ModeSelector | Servico |
| IA-10 | Scoring de Resultados (LIA Score) | UnifiedCandidateTable | Servico |
| IA-11 | Insights Pos-Busca | ProactiveInsightCard | Agente (Recruiter Assistant) |
| IA-12 | Calibracao de Preferencias | LIAFeedbackWidget | Agente (Recruiter Assistant) |
| IA-13 | Refino Inteligente | Sugestoes na busca | Servico |

## 1.2 Modais da Tab BUSCA

| ID | Funcionalidade | Componente Frontend | Tipo Atual |
|----|----------------|---------------------|------------|
| IA-14 | CV Parsing (unico) | NewCandidateUnifiedModal | Servico |
| IA-15 | CV Parsing (batch) | NewCandidateUnifiedModal | Servico |
| IA-16 | Extracao de Skills do CV | CVPreview | Servico |
| IA-17 | Comunicacao Email (Template) | UnifiedCommunicationModal | Servico |
| IA-18 | Comunicacao WhatsApp (Template) | UnifiedCommunicationModal | Servico |
| IA-19 | Personalizacao de Mensagem | UnifiedCommunicationModal | Servico |

## 1.3 Preview e Pagina do Candidato

| ID | Funcionalidade | Componente Frontend | Tipo Atual |
|----|----------------|---------------------|------------|
| IA-20 | LIA Score Geral | CandidatePreview | Servico |
| IA-21 | Parecer LIA | CandidatePreview / CandidatePage | Servico |
| IA-22 | Strengths/Concerns | CandidatePreview | Servico |
| IA-23 | Recommendation (Aprovado/Talvez/Nao) | CandidatePreview | Servico |
| IA-24 | Big Five Mapping | CandidatePage | Servico |

## 1.4 Prompt Expandido / Chat LIA

| ID | Funcionalidade | Componente Frontend | Tipo Atual |
|----|----------------|---------------------|------------|
| IA-25 | Chat Conversacional | ExpandableAIPrompt | Agente (Conversation) |
| IA-26 | Sugestoes Contextuais | ExpandableAIPrompt | Agente (Conversation) |
| IA-27 | Analise Comparativa | CandidateComparison | Servico |
| IA-28 | Resumo de Selecao | ExpandableAIPrompt | Servico |

## 1.5 Acoes em Lote

| ID | Funcionalidade | Componente Frontend | Tipo Atual |
|----|----------------|---------------------|------------|
| IA-29 | LIA Batch Analysis | LIABatchAnalysis | Servico |
| IA-30 | Batch Scoring | ContextualActionsBanner | Servico |

## 1.6 Tabs Secundarias

| ID | Funcionalidade | Tab | Tipo Atual |
|----|----------------|-----|------------|
| IA-31 | Exibicao LIA Score | Favoritos, Listas | N/A (apenas exibicao) |
| IA-32 | Entidades Salvas | Historico, Buscas Salvas | N/A (apenas exibicao) |

---

# 2. DOCUMENTACAO DETALHADA POR PONTO DE IA

---

## IA-01: Sugestao Preditiva (Autocomplete)

### Localizacao
- **Tab:** Busca
- **Componente:** `SmartSearchInput`
- **Arquivo:** `plataforma-lia/src/components/search/smart-search-input.tsx`

### Como Funciona
```
Usuario digita -> Debounce 300ms -> API autocomplete -> Lista de sugestoes
```

1. Usuario comeca a digitar no input de busca
2. Apos 300ms sem digitacao, dispara chamada
3. Combina historico local + IA para sugestoes
4. Retorna lista ordenada por relevancia

### Por Que IA E Utilizada
- Sugestoes contextuais baseadas em historico e padroes
- Completar termos tecnicos (ex: "Pyt" -> "Python Developer")
- Aprender com buscas anteriores do usuario

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Servico (LLM Service) | Manter como Servico |
| Agente? | Nao | Nao precisa ser agente |
| Justificativa | Operacao simples, stateless | - |

### Input/Output

**Input:**
```json
{
  "partial_query": "dev pyt",
  "user_id": "uuid",
  "company_id": "uuid",
  "history_context": ["Python SP", "React Senior"],
  "max_suggestions": 5
}
```

**Output:**
```json
{
  "suggestions": [
    {"text": "Desenvolvedor Python", "source": "history", "confidence": 0.95},
    {"text": "Python Senior SP", "source": "ai", "confidence": 0.85},
    {"text": "Python Django Backend", "source": "ai", "confidence": 0.75}
  ]
}
```

### Regras de Negocio
1. Minimo 3 caracteres para iniciar sugestoes
2. Maximo 10 sugestoes retornadas
3. Priorizar historico do usuario sobre sugestoes gerais
4. Cache de 1 hora para sugestoes frequentes
5. Timeout de 500ms (fallback para historico local)

### Custo Estimado
- ~200 tokens input / ~100 tokens output
- Frequencia: Alta (a cada digitacao com debounce)
- Otimizacao: Cache agressivo

---

## IA-02: Extracao de Entidades

### Localizacao
- **Tab:** Busca
- **Componente:** `SmartSearchInput` -> `ContextPills`
- **Arquivos:** `smart-search-input.tsx`, `context-pill.tsx`

### Como Funciona
```
Query completa -> Claude analisa -> Extrai entidades -> Gera Pills visuais
```

1. Usuario termina de digitar ou pressiona Enter
2. Query e enviada ao Claude com prompt estruturado
3. Claude retorna JSON com entidades identificadas
4. Frontend renderiza pills editaveis

### Por Que IA E Utilizada
- Entender linguagem natural (ex: "5 anos" = experience_years: 5)
- Identificar skills mesmo com variacoes (ex: "js" = "JavaScript")
- Detectar localizacoes em formatos diversos (ex: "sampa" = "Sao Paulo")
- Lidar com ambiguidades (ex: "Python" = skill, nao cobra)

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Servico (LLM Service) | Manter como Servico |
| Agente? | Nao | Nao precisa ser agente |
| Justificativa | Operacao deterministica, sem estado | - |

### Input/Output

**Input:**
```json
{
  "query": "Desenvolvedor Python senior 5 anos SP remoto",
  "language": "pt-BR"
}
```

**Output:**
```json
{
  "entities": {
    "skills": [
      {"name": "Python", "confidence": 0.95, "type": "technical"}
    ],
    "seniority": {"level": "senior", "confidence": 0.90},
    "experience_years": {"min": 5, "max": null, "confidence": 0.85},
    "location": {
      "city": "Sao Paulo",
      "state": "SP",
      "country": "Brasil",
      "confidence": 0.90
    },
    "work_model": {"model": "remote", "confidence": 0.95},
    "job_title": {"title": "Desenvolvedor", "confidence": 0.80}
  },
  "normalized_query": "desenvolvedor python senior 5+ anos sao paulo remoto"
}
```

### Regras de Negocio
1. Confidence < 0.5 nao gera pill (muito incerto)
2. Entidades duplicadas sao mescladas
3. Conflitos sao resolvidos pela maior confidence
4. Skills sao normalizadas (ex: "react.js" -> "React")
5. Localizacoes sao expandidas (ex: "SP" -> "Sao Paulo, SP, Brasil")

### Prompt Template
```
Voce e um especialista em recrutamento.
Extraia entidades da query de busca de candidatos.

Query: "{query}"

Retorne JSON com:
- skills: [{name, confidence, type: technical|soft}]
- seniority: {level: junior|pleno|senior|especialista, confidence}
- experience_years: {min, max, confidence}
- location: {city, state, country, confidence}
- work_model: {model: remote|hybrid|onsite, confidence}
- job_title: {title, confidence}
- salary_range: {min, max, currency, confidence} se mencionado

Regras:
- Confidence e 0 a 1
- Se nao identificar, omita o campo
- Normalize nomes de skills (React.js -> React)
```

### Custo Estimado
- ~500 tokens input / ~300 tokens output
- Frequencia: Media (1x por busca)

---

## IA-03: Correcao/Ajuste de Termos

### Localizacao
- **Tab:** Busca
- **Componente:** `SmartSearchInput`

### Como Funciona
```
Query com erros -> Detecta erros -> Sugere correcao -> Usuario confirma
```

1. Detecta possiveis erros de digitacao
2. Sugere correcao ("Voce quis dizer: Python?")
3. Usuario pode aceitar ou ignorar

### Por Que IA E Utilizada
- Corrigir typos em termos tecnicos (ex: "Pytohn" -> "Python")
- Sugerir termos mais especificos (ex: "frontend" -> "React/Vue/Angular")
- Expandir siglas (ex: "ML" -> "Machine Learning")

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Servico | Poderia ser regras + dicionario |
| Agente? | Nao | Nao precisa |
| Justificativa | 80% dos casos cobertos por dicionario | Hibrido recomendado |

### Input/Output

**Input:**
```json
{
  "query": "devenvolvedor pytohn",
  "known_terms": ["Python", "Developer", "React"]
}
```

**Output:**
```json
{
  "corrections": [
    {"original": "devenvolvedor", "suggested": "desenvolvedor", "confidence": 0.95},
    {"original": "pytohn", "suggested": "Python", "confidence": 0.98}
  ],
  "corrected_query": "desenvolvedor Python"
}
```

### Regras de Negocio
1. Mostrar correcao apenas se confidence > 0.8
2. Nao corrigir automaticamente, apenas sugerir
3. Aprender com aceites/rejeicoes do usuario

---

## IA-04: Query Expansion

### Localizacao
- **Tab:** Busca
- **Backend:** Processamento de busca

### Como Funciona
```
Query original -> Expande termos relacionados -> Busca ampliada
```

1. Recebe query com entidades extraidas
2. Expande skills para termos relacionados
3. Adiciona sinonimos e variacoes
4. Executa busca com termos expandidos

### Por Que IA E Utilizada
- "Python" tambem busca "Django", "Flask", "FastAPI"
- "Frontend" inclui "React", "Vue", "Angular"
- Aumenta recall sem perder precisao

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Servico | Poderia ser grafo de skills |
| Agente? | Nao | Nao |
| Justificativa | Mapeamento estatico possivel | Hibrido: grafo + IA para novos termos |

### Input/Output

**Input:**
```json
{
  "skills": ["Python"],
  "expansion_level": "medium"
}
```

**Output:**
```json
{
  "expanded_skills": {
    "Python": {
      "core": ["Python", "Python3"],
      "frameworks": ["Django", "Flask", "FastAPI"],
      "related": ["Data Science", "Machine Learning"],
      "tools": ["Pandas", "NumPy", "Jupyter"]
    }
  },
  "search_weights": {
    "Python": 1.0,
    "Django": 0.7,
    "Flask": 0.7,
    "FastAPI": 0.6
  }
}
```

### Regras de Negocio
1. Expansion levels: minimal, medium, aggressive
2. Nao expandir skills com alta especificidade
3. Manter peso maior para termo original

---

## IA-06: Busca por Perfil Similar

### Localizacao
- **Tab:** Busca
- **Componente:** `ModeSelector` (modo "Similar")
- **Backend:** `SourcingAgent`

### Como Funciona
```
URL/ID de candidato -> Analisa perfil -> Gera criterios -> Busca similares
```

1. Usuario fornece URL do LinkedIn ou ID de candidato
2. Sistema extrai dados do perfil de referencia
3. IA gera query de busca baseada no perfil
4. Executa busca e rankeia por similaridade

### Por Que IA E Utilizada
- Extrair dados de URL do LinkedIn
- Identificar caracteristicas-chave do perfil
- Ponderar quais atributos sao mais importantes

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Agente (Sourcing Agent) | Correto |
| Agente? | Sim | Sim, justificado |
| Justificativa | Requer multi-step reasoning | - |

### Input/Output

**Input:**
```json
{
  "source_type": "linkedin_url",
  "source_value": "https://linkedin.com/in/joaosilva",
  "similarity_threshold": 0.7
}
```

**Output:**
```json
{
  "reference_profile": {
    "name": "Joao Silva",
    "skills": ["Python", "AWS", "Docker"],
    "experience_years": 8,
    "seniority": "senior"
  },
  "generated_query": {
    "skills": ["Python", "AWS"],
    "experience_years": {"min": 5, "max": 12},
    "seniority": ["senior", "especialista"]
  },
  "candidates": [...],
  "total": 45
}
```

### Regras de Negocio
1. Requer autenticacao para acessar perfis
2. Rate limit para scraping de LinkedIn
3. Cache de 24h para perfis extraidos
4. Fallback se URL invalida

---

## IA-07: Busca por Job Description

### Localizacao
- **Tab:** Busca
- **Componente:** `ModeSelector` (modo "JD")
- **Backend:** `SourcingAgent`

### Como Funciona
```
Texto da JD -> Extrai requisitos -> Gera criterios -> Busca candidatos
```

1. Usuario cola texto de Job Description
2. IA extrai requisitos obrigatorios e desejaveis
3. Gera query estruturada
4. Busca e rankeia por aderencia

### Por Que IA E Utilizada
- JDs sao texto livre, nao estruturado
- Identificar requisitos obrigatorios vs desejaveis
- Extrair senioridade implicita

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Agente (Sourcing Agent) | Poderia ser Servico |
| Agente? | Sim atualmente | Servico seria suficiente |
| Justificativa | Parsing de JD e deterministic | Simplificar para Servico |

### Input/Output

**Input:**
```json
{
  "jd_text": "Buscamos Desenvolvedor Python Senior com 5+ anos...",
  "extract_mode": "full"
}
```

**Output:**
```json
{
  "parsed_jd": {
    "title": "Desenvolvedor Python Senior",
    "required_skills": ["Python", "SQL", "APIs REST"],
    "nice_to_have": ["Docker", "Kubernetes"],
    "experience_years": 5,
    "seniority": "senior",
    "location": "Remoto",
    "benefits": ["PLR", "Home Office"]
  },
  "search_query": {...},
  "candidates": [...]
}
```

---

## IA-10: Scoring de Resultados (LIA Score)

### Localizacao
- **Tab:** Busca
- **Componente:** `UnifiedCandidateTable` (coluna Score)
- **Backend:** `LIAScoreService`

### Como Funciona
```
Candidato + Criterios -> Analise de match -> Score 0-100
```

1. Para cada candidato retornado
2. Compara skills, experiencia, localizacao
3. Calcula score ponderado
4. Ordena por score (opcional)

### Por Que IA E Utilizada
- Match semantico de skills (ex: "React" match parcial com "Vue")
- Avaliacao de experiencias similares
- Ponderacao contextual

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Servico (LIAScoreService) | Correto |
| Agente? | Nao | Nao precisa |
| Justificativa | Formula deterministica com IA pontual | - |

### Formula de Score

```python
score = (
    skills_match * 0.35 +      # Match de skills
    experience_match * 0.20 +  # Anos de experiencia
    seniority_match * 0.15 +   # Nivel de senioridade
    location_match * 0.15 +    # Localizacao
    title_match * 0.15         # Cargo/funcao
)

# Onde cada componente e 0 a 1
skills_match = matched_skills / required_skills
experience_match = min(1, candidate_years / required_years)
seniority_match = 1 if exact, 0.5 if adjacent, 0 if far
location_match = 1 if exact, 0.7 if same_state, 0.3 if same_country
title_match = semantic_similarity(candidate_title, required_title)
```

### Regras de Negocio
1. Score minimo de 0, maximo de 100
2. Pesos universais (nao variam por industria - anti-bias)
3. Cache de score por 24h (ou ate candidato atualizar)
4. Recalcular se criterios de busca mudarem

---

## IA-14/15: CV Parsing

### Localizacao
- **Tab:** Busca
- **Componente:** `NewCandidateUnifiedModal`
- **Backend:** `CVParserService`

### Como Funciona
```
Arquivo CV -> Extrai texto -> Claude analisa -> Dados estruturados
```

1. Usuario faz upload de PDF/DOCX
2. Sistema extrai texto bruto
3. Claude analisa e estrutura
4. Retorna dados para preview/edicao

### Por Que IA E Utilizada
- CVs nao tem formato padrao
- Extrair entidades de texto livre
- Identificar experiencias e skills
- Detectar idiomas falados

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Servico (CVParserService) | Correto |
| Agente? | Nao | Nao precisa |
| Justificativa | Task isolada, sem contexto | - |

### Input/Output

**Input:**
```json
{
  "file_content": "base64...",
  "file_type": "pdf",
  "extraction_mode": "full"
}
```

**Output:**
```json
{
  "full_name": "Maria Santos",
  "email": "maria@email.com",
  "phone": "+55 11 99999-9999",
  "linkedin": "linkedin.com/in/mariasantos",
  "current_title": "Product Manager",
  "current_company": "Empresa X",
  "experiences": [
    {
      "company": "Empresa X",
      "title": "Product Manager",
      "start_date": "2022-01",
      "end_date": null,
      "description": "Lideranca de produto...",
      "skills_used": ["Agile", "SQL", "Analytics"]
    }
  ],
  "education": [...],
  "skills": ["Product Management", "SQL", "Python"],
  "languages": [{"language": "English", "level": "Fluent"}],
  "confidence_score": 0.92
}
```

### Regras de Negocio
1. Formatos aceitos: PDF, DOCX, DOC, TXT
2. Tamanho maximo: 10MB
3. Se confidence < 0.7, mostrar alerta
4. Permitir edicao manual apos parsing
5. Detectar duplicatas por email/telefone

---

## IA-17/18/19: Geracao de Templates de Comunicacao

### Localizacao
- **Tab:** Busca (acao no candidato)
- **Componente:** `UnifiedCommunicationModal`
- **Backend:** `PersonalizedFeedbackService`

### Como Funciona
```
Contexto + Template base -> Personaliza -> Mensagem final
```

1. Usuario seleciona canal (Email/WhatsApp)
2. Escolhe template ou cria novo
3. IA personaliza com dados do candidato
4. Usuario revisa e envia

### Por Que IA E Utilizada
- Personalizar templates com contexto
- Ajustar tom de voz
- Substituir variaveis complexas
- Gerar mensagens do zero

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Servico | Correto |
| Agente? | Nao | Nao precisa |
| Justificativa | Geracao direta, sem multi-step | - |

### Input/Output

**Input:**
```json
{
  "channel": "email",
  "template_id": "interview_invite",
  "candidate": {
    "name": "Joao",
    "current_title": "Developer"
  },
  "job": {
    "title": "Senior Python Developer",
    "company": "TechCorp"
  },
  "tone": "professional",
  "personalization_level": "high"
}
```

**Output:**
```json
{
  "subject": "Oportunidade: Senior Python Developer na TechCorp",
  "body": "Ola Joao,\n\nEspero que esteja bem! Vi seu perfil como Developer e acredito que voce seria um excelente fit para a posicao de Senior Python Developer aqui na TechCorp...",
  "variables_used": ["name", "current_title", "job_title", "company"]
}
```

### Regras de Negocio
1. Templates base sao editaveis pela empresa
2. Variaveis obrigatorias: {nome}, {vaga}
3. Tom de voz: formal, profissional, casual
4. Preview obrigatorio antes de enviar
5. Historico de comunicacoes salvo

---

## IA-20/21/22/23: Parecer LIA

### Localizacao
- **Tab:** Busca
- **Componente:** `CandidatePreview`, `CandidatePage`
- **Backend:** `LIAScoreService`

### Como Funciona
```
Perfil completo -> Analise profunda -> Parecer estruturado
```

1. Ao abrir preview de candidato
2. Sistema gera parecer se nao existir
3. Exibe score, strengths, concerns, recommendation

### Por Que IA E Utilizada
- Analise qualitativa alem de score numerico
- Identificar red flags e green flags
- Gerar narrativa sobre o candidato
- Recomendar aprovacao/rejeicao

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Servico | Considerar Agente |
| Agente? | Nao atualmente | Poderia ser Agente para contexto |
| Justificativa | Parecer contextual beneficiaria de memoria | - |

### Input/Output

**Input:**
```json
{
  "candidate_id": "uuid",
  "job_id": "uuid" // opcional, para parecer vinculado a vaga
}
```

**Output:**
```json
{
  "score": 85,
  "recommendation": "highly_recommended",
  "summary": "Candidato com solido background em Python e experiencia em startups de tecnologia. Demonstra progressao de carreira consistente.",
  "strengths": [
    "8+ anos de experiencia em Python",
    "Experiencia com arquitetura de microsservicos",
    "Historico de lideranca tecnica"
  ],
  "concerns": [
    "Pouca experiencia com o setor financeiro",
    "Gaps de emprego em 2020-2021"
  ],
  "big_five_archetype": "Inovador Pragmatico",
  "culture_fit_notes": "Perfil colaborativo, prefere ambientes ageis"
}
```

---

## IA-25/26: Chat Conversacional (Prompt Expandido)

### Localizacao
- **Tab:** Busca
- **Componente:** `ExpandableAIPrompt`
- **Backend:** `ConversationAgent`, `Orchestrator`

### Como Funciona
```
Mensagem usuario -> Orchestrator -> Agente apropriado -> Resposta
```

1. Usuario digita pergunta no prompt expandido
2. Orchestrator classifica intencao
3. Direciona para agente especializado
4. Retorna resposta + acoes sugeridas

### Por Que IA E Utilizada
- Conversa em linguagem natural
- Multiplas intencoes possiveis
- Contexto de sessao
- Sugestoes proativas

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Agente (Conversation + Orchestrator) | Correto |
| Agente? | Sim | Sim, essencial |
| Justificativa | Requer roteamento, contexto, multi-turn | - |

### Input/Output

**Input:**
```json
{
  "message": "Me mostre candidatos Python em SP que falam ingles",
  "context": {
    "current_tab": "search",
    "selected_candidates": [],
    "conversation_history": [...]
  }
}
```

**Output:**
```json
{
  "response": "Encontrei 23 candidatos Python em Sao Paulo com ingles fluente. Gostaria que eu filtrasse por senioridade?",
  "actions": [
    {"type": "execute_search", "params": {...}},
    {"type": "show_results", "count": 23}
  ],
  "suggestions": [
    "Filtrar por senior",
    "Ver apenas remotos",
    "Ordenar por score"
  ]
}
```

---

## IA-29/30: Batch Analysis

### Localizacao
- **Tab:** Busca (acoes em lote)
- **Componente:** `LIABatchAnalysis`, `ContextualActionsBanner`

### Como Funciona
```
Multiplos candidatos -> Analise paralela -> Relatorio consolidado
```

1. Usuario seleciona multiplos candidatos
2. Clica em "Analisar com LIA"
3. Sistema processa em paralelo
4. Retorna comparativo/resumo

### Por Que IA E Utilizada
- Comparar candidatos entre si
- Identificar o melhor fit
- Gerar ranking justificado

### Tipo de Implementacao

| Aspecto | Status Atual | Recomendacao |
|---------|--------------|--------------|
| Tipo | Servico | Correto |
| Agente? | Nao | Nao precisa |
| Justificativa | Batch de operacoes simples | - |

---

# 3. ANALISE ARQUITETURAL

## 3.1 Distribuicao por Tipo

| Tipo | Quantidade | Percentual |
|------|------------|------------|
| Servico (LLM Service) | 24 | 75% |
| Agente Especializado | 6 | 19% |
| Exibicao apenas (N/A) | 2 | 6% |
| **Total** | **32** | 100% |

## 3.2 Agentes Utilizados no Funil

| Agente | Funcionalidades | Justificativa |
|--------|-----------------|---------------|
| Orchestrator | Roteamento geral | Essencial para multi-agente |
| Conversation Agent | IA-25, IA-26 | Chat multi-turn |
| Sourcing Agent | IA-06, IA-07 | Busca complexa |
| Recruiter Assistant | IA-11, IA-12 | Insights proativos |

## 3.3 Servicos Utilizados

| Servico | Funcionalidades | Responsabilidade |
|---------|-----------------|------------------|
| LLMService | Todas chamadas Claude | Abstrai provider |
| CVParserService | IA-14, IA-15, IA-16 | Parsing de CVs |
| LIAScoreService | IA-10, IA-20-24 | Scoring e parecer |
| PersonalizedFeedbackService | IA-17-19 | Comunicacao |

---

# 4. MATRIZ DE DECISAO

## Quando Usar Cada Tipo

| Criterio | Chamada Direta | Servico | Agente |
|----------|----------------|---------|--------|
| Estado/Memoria | Nao precisa | Nao precisa | Precisa |
| Multi-step | Nao | Nao | Sim |
| Roteamento | Nao | Nao | Sim |
| Ferramentas | Nao | Opcional | Sim |
| Contexto longo | Nao | Nao | Sim |
| Custo | Baixo | Medio | Alto |
| Latencia | Baixa | Media | Alta |

## Recomendacao por Funcionalidade

| ID | Funcionalidade | Atual | Recomendado | Mudanca? |
|----|----------------|-------|-------------|----------|
| IA-01 | Autocomplete | Servico | Regras + Cache | Simplificar |
| IA-02 | Entity Extraction | Servico | Servico | Manter |
| IA-03 | Correcao Termos | Servico | Dicionario + IA | Hibrido |
| IA-04 | Query Expansion | Servico | Grafo + IA | Hibrido |
| IA-06 | Perfil Similar | Agente | Agente | Manter |
| IA-07 | Busca JD | Agente | Servico | Simplificar |
| IA-10 | Scoring | Servico | Servico | Manter |
| IA-14 | CV Parsing | Servico | Servico | Manter |
| IA-25 | Chat | Agente | Agente | Manter |

---

# 5. O QUE E IA E NAO DEVERIA SER

## Casos de Over-Engineering com IA

### 5.1 Autocomplete Preditivo (IA-01)

**Status Atual:** Usa Claude para sugestoes

**Por Que NAO Deveria Ser IA:**
- 80% das sugestoes sao do historico do usuario
- Termos tecnicos sao finiitos e mapeaveis
- Latencia de IA prejudica UX

**Recomendacao:**
```
Abordagem Hibrida:
1. Historico local (instantaneo)
2. Dicionario de termos tech (pre-carregado)
3. IA apenas para termos desconhecidos (<20% dos casos)
```

**Economia:** ~60% das chamadas de IA

---

### 5.2 Correcao de Termos (IA-03)

**Status Atual:** Claude corrige erros de digitacao

**Por Que NAO Deveria Ser IA:**
- Spell check e problema resolvido (Levenshtein, fuzzy match)
- Dicionario de termos tech cobre 95% dos casos
- Custo alto para operacao simples

**Recomendacao:**
```javascript
// Fuzzy matching local
const suggestions = fuzzySuggestions(query, techDictionary, threshold=0.8);

// IA apenas se nenhum match local
if (suggestions.length === 0) {
  return await aiSuggestTerms(query);
}
```

**Economia:** ~90% das chamadas de IA

---

### 5.3 Query Expansion (IA-04)

**Status Atual:** Claude expande "Python" para ["Django", "Flask", ...]

**Por Que NAO Deveria Ser IA:**
- Mapeamentos de skills sao estaveis
- Grafo de skills resolve 95% dos casos
- IA adiciona latencia

**Recomendacao:**
```
Grafo de Skills (pre-computado):
Python -> [Django, Flask, FastAPI, Pandas, NumPy]
React -> [JavaScript, TypeScript, Redux, Next.js]
...

IA apenas para:
- Termos novos nao no grafo
- Skills emergentes
- Consultas ambiguas
```

**Economia:** ~85% das chamadas de IA

---

### 5.4 Busca por JD (IA-07)

**Status Atual:** Agente Sourcing processa JD

**Por Que NAO Deveria Ser Agente:**
- Parsing de JD e single-step
- Nao requer memoria ou contexto
- Servico seria suficiente

**Recomendacao:**
```
Mudar de: SourcingAgent.parse_jd()
Para: JDParserService.parse()

Beneficios:
- Menos overhead de orquestracao
- Latencia 40% menor
- Codigo mais simples
```

---

### 5.5 Score de Variaveis Simples

**Status Atual:** LIA Score usa IA para comparar skills

**Por Que PARCIALMENTE NAO Deveria Ser IA:**
- Comparacao exata de skills e deterministica
- Comparacao de experiencia e matematica simples
- Match de localizacao e lookup

**Recomendacao:**
```python
# Componentes deterministicos (sem IA)
skills_match = len(set(candidate.skills) & set(required.skills)) / len(required.skills)
experience_match = min(1.0, candidate.years / required.years)
location_match = 1.0 if candidate.city == required.city else 0.5

# IA apenas para
semantic_skill_match = await ai_semantic_match(candidate.skills, required.skills)
title_similarity = await ai_title_similarity(candidate.title, required.title)

# Score final
score = (skills_match * 0.2) + (semantic_skill_match * 0.15) + ...
```

**Economia:** ~50% das chamadas de IA no scoring

---

# 6. O QUE NAO E IA E PODERIA SER

## Oportunidades de Usar IA

### 6.1 Deteccao de Candidatos Duplicados

**Status Atual:** Match por email/telefone (exato)

**Por Que PODERIA Ser IA:**
- Mesmo candidato com emails diferentes
- Nomes com variacoes (Joao vs Joao Silva)
- CVs com dados parcialmente diferentes

**Implementacao Sugerida:**
```python
# Input
candidates_to_compare = [
  {"name": "Joao Silva", "email": "joao@gmail.com", ...},
  {"name": "J. Silva", "email": "joaosilva@outlook.com", ...}
]

# IA analisa similaridade
similarity = await ai_detect_duplicate(candidates_to_compare)
# Output: {"is_duplicate": true, "confidence": 0.87, "merge_suggestion": {...}}
```

**Beneficio:** Reduzir duplicatas em 40%

---

### 6.2 Ordenacao Inteligente de Resultados

**Status Atual:** Ordena por score ou data

**Por Que PODERIA Ser IA:**
- Aprender preferencias do recrutador
- Priorizar candidatos que historicamente foram aprovados
- Considerar urgencia da vaga

**Implementacao Sugerida:**
```python
# Input
context = {
  "recruiter_id": "uuid",
  "job_urgency": "high",
  "past_hires": [...],  # Candidatos aprovados anteriormente
  "candidates": [...]
}

# IA reordena com contexto
ranked = await ai_contextual_ranking(context)
# Output: Lista reordenada com justificativa
```

---

### 6.3 Alertas Proativos de Mercado

**Status Atual:** Nenhum alerta

**Por Que PODERIA Ser IA:**
- Detectar escassez de talentos para skill
- Alertar sobre salarios acima do mercado
- Sugerir skills alternativas

**Implementacao Sugerida:**
```python
# Trigger: Busca retorna poucos resultados
if results.total < 10:
  insights = await ai_market_analysis({
    "skills": search.skills,
    "location": search.location,
    "market_data": get_salary_benchmarks()
  })
  
  # Output:
  # "Python + AWS em SP tem alta demanda. Considere:
  #  - Ampliar para remoto (3x mais candidatos)
  #  - Aceitar GCP ao inves de AWS
  #  - Aumentar faixa salarial em 15%"
```

---

### 6.4 Sugestao de Perguntas para Entrevista

**Status Atual:** Nao existe no Funil

**Por Que PODERIA Ser IA:**
- Gerar perguntas baseadas no perfil
- Focar em gaps identificados
- Personalizar por nivel

**Implementacao Sugerida:**
```python
# No preview do candidato
if recruiter.clicks("Sugerir Perguntas"):
  questions = await ai_suggest_questions({
    "candidate": candidate,
    "job": job,
    "concerns": candidate.lia_concerns,
    "interview_type": "technical"
  })
  
  # Output: Lista de perguntas WSI personalizadas
```

---

### 6.5 Resumo de Candidatos Selecionados

**Status Atual:** Lista simples

**Por Que PODERIA Ser IA:**
- Resumo narrativo para stakeholders
- Comparativo entre selecionados
- Highlights e diferenciadores

**Implementacao Sugerida:**
```python
# Apos selecionar 5 candidatos
summary = await ai_selection_summary({
  "candidates": selected_candidates,
  "job": job,
  "recipient": "hiring_manager"  # Ajusta tom
})

# Output:
# "Selecionamos 5 candidatos para a vaga de Dev Python Senior:
#  - 3 com experiencia em fintech (ideal para o projeto)
#  - Media de 7 anos de experiencia
#  - Destaque: Maria Santos combina Python + lideranca
#  - Atencao: 2 candidatos preferem 100% remoto"
```

---

### 6.6 Predicao de Aceite de Proposta

**Status Atual:** Nao existe

**Por Que PODERIA Ser IA:**
- Estimar probabilidade de aceite
- Identificar fatores decisivos
- Sugerir ajustes na proposta

**Implementacao Sugerida:**
```python
# Ao preparar proposta
prediction = await ai_offer_acceptance({
  "candidate": candidate,
  "offer": {
    "salary": 15000,
    "benefits": [...],
    "work_model": "hybrid"
  },
  "market_data": salary_benchmarks,
  "candidate_preferences": candidate.expectations
})

# Output:
# {
#   "acceptance_probability": 0.65,
#   "risk_factors": ["Salario 10% abaixo da expectativa"],
#   "suggestions": ["Aumentar para 16k ou adicionar bonus de entrada"]
# }
```

---

### 6.7 Explicacao de Score (Explainability)

**Status Atual:** Score numerico sem explicacao detalhada

**Por Que PODERIA Ser IA:**
- Explicar "por que 85 e nao 90?"
- Mostrar o que faltou
- Aumentar confianca do recrutador

**Implementacao Sugerida:**
```python
# Ao hover no score ou clicar em "?"
explanation = await ai_explain_score({
  "candidate": candidate,
  "job": job,
  "score": 85,
  "breakdown": score_components
})

# Output:
# "Score 85/100 explicado:
#  + Python expert (10/10)
#  + Experiencia adequada (9/10)
#  - Nunca trabalhou em fintech (-5)
#  - Localizacao diferente da preferida (-3)
#  
#  Para chegar a 95: experiencia em fintech seria diferencial"
```

---

### 6.8 Auto-Tag de Candidatos

**Status Atual:** Tags manuais

**Por Que PODERIA Ser IA:**
- Sugerir tags baseado no perfil
- Detectar especializacoes
- Manter consistencia de taxonomia

**Implementacao Sugerida:**
```python
# Apos parsing de CV ou visualizacao de perfil
suggested_tags = await ai_suggest_tags({
  "candidate": candidate,
  "existing_tags": company.tag_taxonomy,
  "context": "sourcing"
})

# Output:
# ["Python Specialist", "Startup Experience", "English Fluent", "Remote-first"]
```

---

# 7. RECOMENDACOES

## 7.1 Acoes Imediatas (Quick Wins)

| Acao | Impacto | Esforco | ROI |
|------|---------|---------|-----|
| Substituir autocomplete IA por dicionario | Reducao 60% chamadas | Baixo | Alto |
| Correcao de termos via fuzzy match | Reducao 90% chamadas | Baixo | Alto |
| Query expansion via grafo estatico | Reducao 85% chamadas | Medio | Alto |
| JD Parsing: Agente -> Servico | Latencia -40% | Baixo | Medio |

## 7.2 Melhorias de Medio Prazo

| Acao | Impacto | Esforco |
|------|---------|---------|
| Implementar deteccao de duplicatas com IA | Qualidade dados | Medio |
| Adicionar explicabilidade de score | Confianca usuario | Medio |
| Sugestao de perguntas de entrevista | Valor agregado | Medio |

## 7.3 Investimentos Estrategicos

| Acao | Impacto | Esforco |
|------|---------|---------|
| Predicao de aceite de proposta | Diferencial competitivo | Alto |
| Alertas proativos de mercado | Valor estrategico | Alto |
| Ranking personalizado por recrutador | UX superior | Alto |

## 7.4 Metricas de Sucesso

| Metrica | Baseline | Meta |
|---------|----------|------|
| Chamadas IA / busca | 5-7 | 2-3 |
| Latencia media busca | 3-5s | <2s |
| Custo tokens / usuario / dia | ~50k | ~20k |
| Precisao de score | - | >85% |
| Recall de busca | - | >90% |

---

# 8. APENDICE: RESUMO EXECUTIVO

## Funil de Talentos - IA em Numeros

| Categoria | Quantidade |
|-----------|------------|
| Total pontos de IA | 32 |
| Implementados como Servico | 24 (75%) |
| Implementados como Agente | 6 (19%) |
| Apenas exibicao | 2 (6%) |

## IA Desnecessaria (Remover/Simplificar)

| Funcionalidade | Economia Estimada |
|----------------|-------------------|
| Autocomplete | 60% chamadas |
| Correcao termos | 90% chamadas |
| Query expansion | 85% chamadas |
| Score deterministico | 50% chamadas |
| **Total** | ~60% reducao geral |

## IA Faltante (Adicionar)

| Funcionalidade | Valor Agregado |
|----------------|----------------|
| Deteccao duplicatas | Qualidade dados |
| Ordenacao inteligente | UX |
| Alertas mercado | Estrategico |
| Sugestao perguntas | Produtividade |
| Predicao aceite | Diferencial |
| Explicabilidade score | Confianca |
| Auto-tags | Consistencia |

---

---

# 9. COMANDOS E SUGESTOES DO PROMPT EXPANDIDO (SUPER CHAT LIA)

Esta secao documenta todos os comandos, sugestoes e queries disponiveis nos modais de ideias e no prompt expandido da LIA, organizados por contexto de uso.

---

## 9.1 Tarefas Sugeridas (Dashboard/Chat Vazio)

**Componente:** `PromptSuggestionsDock`  
**Arquivo:** `plataforma-lia/src/components/ui/prompt-suggestions-dock.tsx`  
**Contexto:** Exibido quando o chat esta vazio ou no dashboard

| # | Comando | Categoria | Descricao |
|---|---------|-----------|-----------|
| 1 | Criar uma nova vaga | Vagas | Configure requisitos do sistema com descricao detalhada |
| 2 | Solicite aprovacao de nova vaga | Vagas | Encaminhe documentacao para aprovacao gerencial e justificativa |
| 3 | Compartilhe candidatos com gestor | Candidatos | Crie relatorio com perfis aprovados e recomendacoes |
| 4 | Buscar candidatos | Candidatos | Encontre candidatos no banco de dados por perfil, skills ou experiencia |
| 5 | Consulte informacoes sobre candidato | Candidatos | Obtenha historico especifico e historico completo |
| 6 | Adicione novo candidato | Candidatos | Cadastre perfil com talentos |
| 7 | Reagende uma entrevista | Entrevistas | Cancele horario e notifique automaticamente participantes |
| 8 | Atualize status do candidato | Candidatos | Modifique situacao no processo e envie notificacoes |

---

## 9.2 Dicas e Comandos por Categoria (Modal Principal)

**Componente:** `LIATipsModal`  
**Arquivo:** `plataforma-lia/src/components/lia-tips-modal.tsx`

### 9.2.1 Geral (8 dicas)

| # | Dica/Comando |
|---|--------------|
| 1 | Use linguagem natural - a LIA entende contexto e nuances |
| 2 | Seja especifico nos criterios e filtros para melhores resultados |
| 3 | Combine comandos diferentes para fluxos mais complexos |
| 4 | A LIA aprende com suas interacoes e melhora suas sugestoes |
| 5 | Use comandos especificos como "encontrar candidatos React" |
| 6 | Pergunte sobre metricas: "qual nossa taxa de conversao?" |
| 7 | Solicite analises: "compare candidatos por score" |
| 8 | Configure automacoes: "agende follow-up automatico" |

### 9.2.2 Candidatos (8 comandos)

| # | Comando |
|---|---------|
| 1 | Analise o perfil do Joao Silva |
| 2 | Compare os top 5 para UX Designer |
| 3 | Monte pipeline com candidatos senior |
| 4 | Busque React com 5+ anos |
| 5 | Marque entrevista com Ana para terca |
| 6 | Email para candidatos em processo |
| 7 | Score de compatibilidade dos ativos |
| 8 | Relatorio de diversidade aprovados |

### 9.2.3 Vagas (8 comandos)

| # | Comando |
|---|---------|
| 1 | Nova vaga para Data Scientist Senior |
| 2 | Publique Frontend Developer no LinkedIn |
| 3 | Analise funil da vaga Product Manager |
| 4 | Melhore descricao para atrair mais |
| 5 | Setup processo automatico |
| 6 | Compare vagas similares |
| 7 | Pesquise salarios no mercado |
| 8 | Template para vagas recorrentes |

### 9.2.4 Indicadores (8 comandos)

| # | Comando |
|---|---------|
| 1 | Por que caiu o Time to Hire? |
| 2 | Relatorio diversidade mensal |
| 3 | Performance por departamento |
| 4 | Tendencias por canal |
| 5 | Onde esta o problema? |
| 6 | Contratacoes proximo trimestre |
| 7 | Retorno dos investimentos |
| 8 | Compare com mercado |

### 9.2.5 Automacoes (8 comandos)

| # | Comando |
|---|---------|
| 1 | Configure triagem automatica para posicoes |
| 2 | Setup follow-ups automaticos para candidatos |
| 3 | Crie alertas para candidatos ideais |
| 4 | Configure lembretes de entrevistas |
| 5 | Automatize envio de feedback requests |
| 6 | Setup sync automatico com ATS |
| 7 | Configure relatorios automaticos |
| 8 | Agende publicacoes em redes sociais |

### 9.2.6 Integracoes (8 dicas)

| # | Dica |
|---|------|
| 1 | Todas as acoes sao sincronizadas com seu ATS automaticamente |
| 2 | Dados de candidatos e vagas sao registrados em tempo real |
| 3 | Relatorios extraem dados diretamente do sistema integrado |
| 4 | Use Teams ou WhatsApp para comunicacao por audio |
| 5 | Integre com LinkedIn para sourcing automatico |
| 6 | Sync com calendario para agendamentos |
| 7 | Exporte relatorios para ferramentas externas |
| 8 | Configure webhooks para notificacoes |

---

## 9.3 Queries Gerais (Modal "Mais Ideias" - Geral)

**Componente:** `LiaQueriesGuide`  
**Arquivo:** `plataforma-lia/src/components/ui/lia-queries-guide.tsx`  
**Total:** 33 queries organizadas em 7 categorias

### 9.3.1 Metricas (5 queries)

| # | Query |
|---|-------|
| 1 | Quantos candidatos estao ativos no pipeline? |
| 2 | Qual e a taxa de conversao do meu funil este mes? |
| 3 | Qual o tempo medio para fechar uma vaga? |
| 4 | Quantas contratacoes fizemos este trimestre? |
| 5 | Quantas vagas estao atrasadas no SLA? |

### 9.3.2 Candidatos (6 queries)

| # | Query |
|---|-------|
| 1 | Quem sao os melhores candidatos para a vaga de Desenvolvedor? |
| 2 | Quantos candidatos aguardam entrevista? |
| 3 | Quais candidatos tem nota LIA acima de 80? |
| 4 | Encontre candidatos com experiencia em React e Node.js |
| 5 | Quais candidatos tem perfil de lideranca? |
| 6 | Buscar candidatos na Busca Global para a vaga de Data Analyst |

### 9.3.3 Vagas (5 queries)

| # | Query |
|---|-------|
| 1 | Quais vagas estao abertas ha mais de 30 dias? |
| 2 | Quais vagas estao sem candidatos? |
| 3 | Quantas vagas temos por departamento? |
| 4 | Qual vaga tem a melhor taxa de conversao? |
| 5 | Quais vagas precisam de atencao urgente? |

### 9.3.4 Pipeline (4 queries)

| # | Query |
|---|-------|
| 1 | Quantos candidatos temos em cada etapa do funil? |
| 2 | Onde esta o gargalo do meu processo seletivo? |
| 3 | Como esta a progressao dos candidatos esta semana? |
| 4 | Quais candidatos estao parados ha mais de 5 dias? |

### 9.3.5 Analise (5 queries)

| # | Query |
|---|-------|
| 1 | Quais sao as principais recomendacoes para hoje? |
| 2 | Analise o perfil de personalidade ideal para esta vaga |
| 3 | Resuma os feedbacks das ultimas entrevistas |
| 4 | Qual o perfil mais comum entre candidatos aprovados? |
| 5 | Sugira melhorias para o processo de triagem |

### 9.3.6 Previsoes (4 queries)

| # | Query |
|---|-------|
| 1 | Quando devo fechar a vaga de Product Manager? |
| 2 | Quantas contratacoes vamos fazer este mes? |
| 3 | Qual a probabilidade de sucesso do candidato Joao Silva? |
| 4 | Estimativa de tempo para preencher as vagas abertas |

### 9.3.7 Comparacao (4 queries)

| # | Query |
|---|-------|
| 1 | Compare os 3 finalistas da vaga de UX Designer |
| 2 | Compare o desempenho deste mes com o anterior |
| 3 | Qual departamento contrata mais rapido? |
| 4 | Compare a qualidade dos candidatos entre fontes |

---

## 9.4 Queries da Tab Busca (Pos-Busca)

**Componente:** `LiaSearchQueriesGuide`  
**Arquivo:** `plataforma-lia/src/components/ui/lia-search-queries-guide.tsx`  
**Total:** 27 queries especificas para analise de resultados de busca

### 9.4.1 Analise da Busca (14 queries)

| # | Query |
|---|-------|
| 1 | Quantos candidatos encontrei nesta busca? |
| 2 | Qual o score LIA medio dos resultados? |
| 3 | Quais skills sao mais comuns nesta busca? |
| 4 | Qual a experiencia media dos candidatos? |
| 5 | Quantos candidatos tem nota LIA acima de 70? |
| 6 | Qual o nivel de ingles dos candidatos? |
| 7 | Qual a origem de formacao dos candidatos? |
| 8 | Onde estao localizados os candidatos? |
| 9 | Qual a distribuicao por genero? |
| 10 | Qual a media de pretensao salarial? |
| 11 | Quantos aceitam trabalho hibrido? |
| 12 | Quantos aceitam somente remoto? |
| 13 | Quantos aceitam trabalho presencial? |
| 14 | Analise de diversidade e inclusao (raca, PCDs) |

### 9.4.2 Candidatos Selecionados (4 queries)

| # | Query |
|---|-------|
| 1 | Resuma o perfil dos candidatos selecionados |
| 2 | Quais pontos fortes eles tem em comum? |
| 3 | Quais gaps de competencia posso identificar? |
| 4 | Compare os selecionados com o perfil ideal da vaga |

### 9.4.3 Comparacoes (3 queries)

| # | Query |
|---|-------|
| 1 | Compare os 3 melhores candidatos |
| 2 | Quem tem mais experiencia relevante? |
| 3 | Compare as habilidades tecnicas dos top candidatos |

### 9.4.4 Acoes Sugeridas (3 queries)

| # | Query |
|---|-------|
| 1 | Quais candidatos devo descartar desta busca? |
| 2 | Quem precisa de triagem adicional? |
| 3 | Organize os candidatos por prioridade |

### 9.4.5 Refinamento (3 queries)

| # | Query |
|---|-------|
| 1 | Como posso melhorar esta busca? |
| 2 | Sugira filtros adicionais para refinar |
| 3 | Buscar perfis similares ao top candidato |

---

## 9.5 Queries de Candidatos (Contexto de Candidato)

**Componente:** `CandidateQueriesGuide`  
**Arquivo:** `plataforma-lia/src/components/ui/candidate-queries-guide.tsx`  
**Total:** 30 queries para analise de candidatos

### 9.5.1 Analise (5 queries)

| # | Query |
|---|-------|
| 1 | Comparar os 5 melhores candidatos desta busca |
| 2 | Qual candidato tem melhor fit para esta vaga? |
| 3 | Analisar pontos fortes e fracos dos candidatos selecionados |
| 4 | Resumir experiencia dos candidatos com score > 80 |
| 5 | Qual o perfil medio dos candidatos desta busca? |

### 9.5.2 Refinamento (5 queries)

| # | Query |
|---|-------|
| 1 | Mostrar apenas candidatos senior |
| 2 | Filtrar por experiencia em startup |
| 3 | Candidatos com ingles fluente |
| 4 | Apenas candidatos abertos a novas oportunidades |
| 5 | Candidatos disponiveis para inicio imediato |

### 9.5.3 Sourcing (5 queries)

| # | Query |
|---|-------|
| 1 | Buscar perfis similares ao melhor candidato |
| 2 | Expandir busca para base global |
| 3 | Buscar mais candidatos na base local |
| 4 | Encontrar candidatos de empresas referencia do setor |
| 5 | Ampliar criterios de busca para mais resultados |

### 9.5.4 Acoes (5 queries)

| # | Query |
|---|-------|
| 1 | Sugerir mensagem de abordagem para os selecionados |
| 2 | Agendar entrevistas com os 3 melhores |
| 3 | Mover candidatos aprovados para proxima etapa |
| 4 | Adicionar candidatos selecionados aos favoritos |
| 5 | Exportar lista de candidatos |

### 9.5.5 Insights (5 queries)

| # | Query |
|---|-------|
| 1 | Qual a media de experiencia dos candidatos? |
| 2 | Distribuicao de senioridade nesta busca |
| 3 | Candidatos mais dificeis de contratar (alta demanda) |
| 4 | O que os candidatos tem em comum? |
| 5 | Tempo medio de experiencia na area |

### 9.5.6 Comparacao (5 queries)

| # | Query |
|---|-------|
| 1 | Comparar os 3 finalistas lado a lado |
| 2 | Quem tem experiencia mais relevante para a vaga? |
| 3 | Comparar fit cultural dos candidatos |
| 4 | Comparar candidatos locais vs globais |
| 5 | Ranking de candidatos por adequacao |

---

## 9.6 Resumo de Comandos e Queries

| Fonte | Categoria | Total |
|-------|-----------|-------|
| PromptSuggestionsDock | Tarefas Sugeridas | 8 |
| LIATipsModal | Dicas Gerais | 8 |
| LIATipsModal | Candidatos | 8 |
| LIATipsModal | Vagas | 8 |
| LIATipsModal | Indicadores | 8 |
| LIATipsModal | Automacoes | 8 |
| LIATipsModal | Integracoes | 8 |
| LiaQueriesGuide | Metricas | 5 |
| LiaQueriesGuide | Candidatos | 6 |
| LiaQueriesGuide | Vagas | 5 |
| LiaQueriesGuide | Pipeline | 4 |
| LiaQueriesGuide | Analise | 5 |
| LiaQueriesGuide | Previsoes | 4 |
| LiaQueriesGuide | Comparacao | 4 |
| LiaSearchQueriesGuide | Analise Busca | 14 |
| LiaSearchQueriesGuide | Selecionados | 4 |
| LiaSearchQueriesGuide | Comparacoes | 3 |
| LiaSearchQueriesGuide | Acoes | 3 |
| LiaSearchQueriesGuide | Refinamento | 3 |
| CandidateQueriesGuide | Analise | 5 |
| CandidateQueriesGuide | Refinamento | 5 |
| CandidateQueriesGuide | Sourcing | 5 |
| CandidateQueriesGuide | Acoes | 5 |
| CandidateQueriesGuide | Insights | 5 |
| CandidateQueriesGuide | Comparacao | 5 |
| **TOTAL** | | **146 comandos/queries** |

---

## 9.7 Analise de Comandos por Tipo de IA

### Comandos que USAM IA ativamente

| Tipo | Exemplos | Quantidade |
|------|----------|------------|
| Busca semantica | "Encontre candidatos com experiencia em React" | ~20 |
| Analise de dados | "Compare candidatos por score", "Qual o perfil medio?" | ~35 |
| Geracao de texto | "Sugira mensagem de abordagem", "Resuma feedbacks" | ~10 |
| Predicao | "Quando devo fechar a vaga?", "Probabilidade de sucesso" | ~5 |
| Recomendacao | "Quais sao as principais recomendacoes para hoje?" | ~15 |

### Comandos que NAO precisam de IA

| Tipo | Exemplos | Alternativa |
|------|----------|-------------|
| Contagens simples | "Quantos candidatos aguardam entrevista?" | Query SQL |
| Filtros basicos | "Mostrar apenas candidatos senior" | Filtro de tabela |
| Acoes CRUD | "Adicione novo candidato" | Formulario UI |
| Navegacao | "Exportar lista de candidatos" | Botao de acao |

### Oportunidade de Otimizacao

~30% dos comandos poderiam ser executados **sem IA** usando:
- Queries SQL pre-definidas para contagens
- Filtros de UI para refinamentos
- Actions diretas para CRUD

Isso reduziria custos e latencia significativamente.

---

# 10. GOVERNANÇA, SATURAÇÃO E CALIBRAÇÃO

## 10.1 Saturação Inteligente

A Saturação Inteligente pausa a triagem automática quando o pipeline atinge um número máximo de candidatos aprovados.

### Parâmetros

| Parâmetro | Valor Padrão | Descrição |
|-----------|--------------|-----------|
| `saturation_threshold` | 20 | Número máximo de aprovados antes de pausar |
| `is_saturated` | false/true | Flag de saturação ativa |
| `slots_remaining` | calculado | Vagas restantes até saturação |

### Lógica de Decisão

```
SE approved_count >= saturation_threshold:
    is_saturated = TRUE
    recommendation = "pause_screening"
    AÇÃO: Pausar triagem, notificar recrutador
    SUGERIR: ["Agendar entrevistas", "Desbloquear pipeline"]
SENÃO:
    is_saturated = FALSE
    recommendation = "continue_screening"
    INFORMAR: "{slots_remaining} vagas restantes"
```

### Localização no Frontend

| Componente | Exibição |
|------------|----------|
| `CandidatesPage` | Badge "Pipeline Saturado" no header |
| `PipelineColumn` | Indicador visual de saturação |
| `ExpandableAIPrompt` | LIA alerta sobre saturação |

### API

```
GET /api/v1/job-vacancies/{job_id}/saturation-status
POST /api/v1/job-vacancies/{job_id}/unlock-pipeline
```

---

## 10.2 Governança Humana

Limites de autonomia da LIA definidos por vaga via GovernanceRules.

### Ações Automáticas (Permitidas)

| Ação | Condição |
|------|----------|
| Calcular LIA Score | Sempre |
| Rankear candidatos | Sempre |
| Gerar parecer | Sempre |
| Transcrever entrevistas | Sempre |
| Enviar lembretes | Sempre |

### Ações que Requerem Aprovação

| Ação | Motivo |
|------|--------|
| Primeiro contato com candidato | Impacta imagem da empresa |
| Feedback de rejeição | Comunicação sensível |
| Mover candidato de etapa | Decisão crítica |
| Agendar entrevista com gestor | Calendário de terceiros |
| Comunicações em massa | Risco de erro em escala |

### Modelo GovernanceRules

```python
class GovernanceRules:
    auto_schedule_interviews: bool = False
    auto_send_negative_feedback: bool = False
    requires_validation_before_shortlist: bool = True
    max_auto_sourcing_per_day: int = 50
    allow_ai_first_contact: bool = False
    saturation_threshold: int = 20
```

### Localização no Frontend

| Componente | Funcionalidade |
|------------|----------------|
| `SmartTransitionModal` | Override de decisão da LIA |
| `CandidateActions` | Botões condicionais por governança |
| `BulkActionsBar` | Limites de ações em lote |

---

## 10.3 Calibração Contínua

O CalibrationService aprende com decisões do recrutador para melhorar scores futuros.

### Tipos de Feedback

| Tipo | Evento | Score Delta |
|------|--------|-------------|
| `EXPLICIT_AGREE` | Thumbs up | +0 |
| `EXPLICIT_DISAGREE` | Thumbs down | ±10 |
| `IMPLICIT_ADVANCE` | Avançou candidato mal rankeado | +5 |
| `IMPLICIT_REJECT` | Rejeitou candidato bem rankeado | -5 |
| `POST_HIRE_SUCCESS` | Contratação bem-sucedida | +15 |
| `POST_HIRE_FAILURE` | Contratação malsucedida | -15 |

### Ciclo de Calibração

```
1. Captura feedback implícito (ações do recrutador)
2. Captura feedback explícito (thumbs up/down)
3. Analisa divergências (últimos 30 dias, delta > 5.0)
4. Gera sugestões de ajuste de pesos
5. Aprovação humana das sugestões
6. Aplica novos pesos
```

### Componentes de UI (IA-12)

| Componente | Funcionalidade |
|------------|----------------|
| `LIAFeedbackWidget` | Thumbs up/down por recomendação |
| `CalibrationInsights` | Exibe divergências detectadas |
| `WeightAdjustmentModal` | Aprovação de sugestões |

### API

```
POST /api/v1/calibration/feedback
GET /api/v1/calibration/divergences
POST /api/v1/calibration/apply-suggestions
```

### Métricas de Qualidade

| Métrica | Meta |
|---------|------|
| Taxa de concordância LIA/Recrutador | > 80% |
| Cohen's Kappa | ≥ 0.85 |
| Margem de erro de score | ±0.3 |

---

## 10.4 Inventário Atualizado - Novos Pontos de IA

| ID | Funcionalidade | Componente | Tipo |
|----|----------------|------------|------|
| IA-33 | Saturação Inteligente | PipelineColumn | Serviço |
| IA-34 | Governança por Vaga | SmartTransitionModal | Serviço |
| IA-35 | Calibração de Preferências | LIAFeedbackWidget | Agente (Recruiter Assistant) |
| IA-36 | Detecção de Divergências | CalibrationInsights | Serviço |
| IA-37 | Sugestão de Ajuste de Pesos | WeightAdjustmentModal | Serviço |

---

*Documento atualizado em Janeiro 2026.*
*Adicionado: Seção 10 (Governança, Saturação, Calibração) com detalhes de implementação.*

---

*Documento gerado para analise arquitetural da camada de IA do Funil de Talentos.*
*Objetivo: Otimizar uso de IA para balanco entre custo, latencia e valor entregue.*
