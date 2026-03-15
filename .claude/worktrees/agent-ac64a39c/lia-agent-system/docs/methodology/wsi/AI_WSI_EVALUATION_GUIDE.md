# WSI Complete Guide: Sistema de Avaliação CV vs Vaga

**Última Atualização:** 30 Janeiro 2026

> **Documento Consolidado**: Este guia integra toda a documentação técnica do sistema de avaliação de candidatos WSI (Work Sample Interview).

---

## Índice

1. [Visão Geral e Fluxo de Funcionamento](#1-visão-geral-e-fluxo-de-funcionamento)
2. [Estruturas de Dados (Input/Output Schemas)](#2-estruturas-de-dados-inputoutput-schemas)
3. [Sistema de Scoring (Rubricas, Pesos, Fórmulas)](#3-sistema-de-scoring-rubricas-pesos-fórmulas)
4. [Geração por LLM (Prompts, Templates, Guardrails)](#4-geração-por-llm-prompts-templates-guardrails)
5. [Regras de Negócio e Automação](#5-regras-de-negócio-e-automação)
6. [Integração com a Plataforma](#6-integração-com-a-plataforma)
7. [Exemplos Completos](#7-exemplos-completos)

---

## 1. Visão Geral e Fluxo de Funcionamento

### 1.1 O que é?

O Sistema de Avaliação CV vs Vaga é uma funcionalidade da plataforma WeDo Talent que analisa automaticamente currículos contra requisitos de vagas, gerando:

- **Score de aderência** (0-100%)
- **Avaliação por requisito** (rubric-based)
- **Parecer narrativo** (gerado por LLM)
- **Recomendação de ação** (aprovar/aguardar/reprovar)

### 1.2 Onde é utilizada?

| Contexto | Uso |
|----------|-----|
| Kanban de Vagas | Badge de score no card do candidato |
| Modal de Análise | Visualização completa da avaliação |
| Timeline do Candidato | Registro histórico |
| Relatórios de Triagem | Exportação para gestores |
| Decisões Automatizadas | Triagem automática por regras |
| Notificações | Alertas para recrutadores |

### 1.3 Fluxo de Funcionamento

```
┌──────────────────────────────────────────────────────────────────┐
│                         TRIGGER                                   │
│  • Candidato adicionado ao pipeline                              │
│  • CV atualizado                                                 │
│  • Requisitos da vaga alterados                                  │
│  • Solicitação manual do recrutador                             │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    1. DATA EXTRACTION                             │
│  • CV parsing (texto, skills, experiências)                      │
│  • Job requirements loading (da vaga)                            │
│  • Company context loading (cultura, valores)                    │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    2. SCORING ENGINE                              │
│  • Match de skills (fuzzy matching)                              │
│  • Avaliação por requisito (rubric 4 níveis)                     │
│  • Cálculo de score ponderado                                    │
│  • Detecção de red flags                                         │
│  • OUTPUT: JSON estruturado com scores                           │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    3. LLM NARRATION                               │
│  • Gerar parecer narrativo                                       │
│  • Gerar "Por que este candidato?"                               │
│  • Gerar mitigações para gaps                                    │
│  • OUTPUT: Markdown/JSON narrativo                               │
└───────────────────────────┬──────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    4. PERSISTENCE                                 │
│  • Salvar avaliação no banco                                     │
│  • Atualizar status do candidato                                 │
│  • Criar entrada na timeline                                     │
│  • Disparar notificações (se configurado)                        │
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 Arquitetura: Evaluation Composer Service

A funcionalidade é dividida em **3 camadas**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. DATA AGGREGATION LAYER                    │
│  CV Parsing + Job Requirements + Candidate Profile + Telemetry  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. SCORING ENGINE (DETERMINÍSTICO)           │
│  Rubric Scoring + Red Flag Detection + Weighted Calculations    │
│  OUTPUT: JSON estruturado com scores, evidências, gaps          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. LLM NARRATION SERVICE                     │
│  Parecer LIA + "Por que este candidato" + Gap Mitigations       │
│  OUTPUT: Markdown narrativo + JSON estruturado                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Estruturas de Dados (Input/Output Schemas)

### 2.1 Input: Dados de Entrada

```typescript
interface CVEvaluationInput {
  // Identificadores
  candidate_id: string;        // UUID do candidato
  job_id: string;              // UUID da vaga
  company_id: string;          // UUID da empresa (multi-tenant)
  
  // Dados do Candidato (extraídos do CV)
  candidate: {
    name: string;
    email: string;
    current_title: string;           // Cargo atual
    current_company: string;         // Empresa atual
    years_of_experience: number;     // Anos totais de experiência
    seniority_level: string;         // junior/mid/senior/lead/etc
    
    // Skills extraídas
    technical_skills: string[];      // ["Python", "FastAPI", "PostgreSQL"]
    soft_skills: string[];           // ["Liderança", "Comunicação"]
    
    // Histórico profissional
    work_history: Array<{
      company: string;
      title: string;
      start_date: string;            // YYYY-MM-DD
      end_date: string | null;       // null = atual
      duration_months: number;
      description: string;
      highlights: string[];          // Conquistas mencionadas
    }>;
    
    // Formação
    education: Array<{
      degree: string;
      field: string;
      institution: string;
      year: number;
    }>;
    
    // Certificações
    certifications: Array<{
      name: string;
      issuer: string;
      year: number;
      is_valid: boolean;
    }>;
    
    // Idiomas
    languages: Array<{
      language: string;
      level: string;                 // básico/intermediário/avançado/fluente/nativo
    }>;
    
    // Localização
    location: {
      city: string;
      state: string;
      country: string;
      is_remote: boolean;
      willing_to_relocate: boolean;
    };
    
    // Texto completo do CV (para análise LLM)
    cv_text: string;
  };
  
  // Dados da Vaga
  job: {
    title: string;
    code: string;                    // JOB-XXXX
    department: string;
    level: string;                   // junior/mid/senior/lead/etc
    work_model: string;              // remoto/híbrido/presencial
    location: string;
    
    // Requisitos estruturados
    requirements: Array<{
      id: string;
      name: string;                  // "Python Avançado"
      description: string;           // "6+ anos de experiência"
      priority: 'essential' | 'important' | 'nice-to-have';
      category: string;              // technical/behavioral/cultural
      keywords: string[];            // Palavras-chave para matching
      min_years?: number;            // Anos mínimos (se aplicável)
    }>;
    
    // Descrição textual (para análise LLM)
    description_text: string;
  };
  
  // Contexto da Empresa
  company_context: {
    name: string;
    industry: string;
    size: string;                    // startup/small/medium/large/enterprise
    culture_values: string[];        // ["ownership", "collaboration"]
    team_size: number;               // Tamanho do time da vaga
  };
  
  // Configurações da Avaliação
  config: {
    include_llm_narration: boolean;  // Se deve gerar textos por LLM
    auto_approve_threshold: number;  // Score mínimo para auto-aprovar (ex: 80)
    auto_reject_threshold: number;   // Score máximo para auto-reprovar (ex: 30)
    language: string;                // Idioma do parecer (pt-BR, en-US)
  };
}
```

### 2.2 Output: Resultado da Avaliação

```typescript
interface CVEvaluationResult {
  // Metadados
  id: string;                        // UUID da avaliação
  candidate_id: string;
  job_id: string;
  company_id: string;
  created_at: string;                // ISO timestamp
  version: string;                   // "1.0.0"
  
  // ========================================
  // TAB: VISÃO GERAL
  // ========================================
  overview: {
    // Score Global
    global_score: number;            // 0-100 (calculado)
    score_label: string;             // "Excelente" | "Bom" | "Moderado" | "Fraco" | "Inadequado"
    
    // Breakdown por Categoria
    category_breakdown: {
      essential: {
        total: number;               // Total de requisitos essenciais
        met: number;                 // Quantos foram atendidos (Excede/Atende)
        percentage: number;          // % atendidos
      };
      important: {
        total: number;
        met: number;
        percentage: number;
      };
      desirable: {
        total: number;
        met: number;
        percentage: number;
      };
    };
    
    // Parecer da LIA (LLM-Generated)
    parecer_lia: {
      // Bloco 1: Contexto e Fit
      contexto_fit: string;          // 2-3 frases contextualizando
      
      // Bloco 2: Pontos Fortes com Impacto
      pontos_fortes_impacto: Array<{
        ponto: string;               // Nome do ponto forte
        evidencia: string;           // Trecho do CV ou inferência
        impacto_negocio: string;     // Por que importa para a vaga
      }>;
      
      // Bloco 3: Riscos e Mitigações
      riscos_mitigacoes: Array<{
        risco: string;               // Gap identificado
        nivel: 'baixo' | 'medio' | 'alto';
        mitigacao: string;           // Como resolver
        tempo_estimado: string;      // "2-3 meses"
      }>;
      
      // Bloco 4: Recomendação Final
      recomendacao_final: {
        decisao: 'APROVAR_TRIAGEM' | 'MANTER_ESPERA' | 'NAO_PROSSEGUIR';
        justificativa: string;       // 2-3 frases
        proximos_passos: string[];   // Lista de ações
      };
    };
    
    // Por que este candidato? (LLM-Generated)
    why_candidate: string[];         // 3 razões concretas
    
    // Pontos Fortes (lista simples)
    strengths: string[];
    
    // Preocupações (lista simples)
    concerns: string[];
  };
  
  // ========================================
  // TAB: DETALHES
  // ========================================
  details: {
    // Avaliação por Requisito
    requirements: Array<{
      requirement_id: string;
      name: string;
      priority: 'essential' | 'important' | 'nice-to-have';
      
      // Resultado da Avaliação
      level: 'exceeds' | 'meets' | 'partial' | 'missing';
      score: number;                 // 0, 40, 75, ou 100
      
      // Evidências (extraídas do CV)
      evidences: string[];           // Trechos relevantes
      
      // Narrativa explicativa (LLM-Generated)
      narrative: string;             // Por que foi classificado assim
    }>;
    
    // Red Flags
    red_flags: Array<{
      type: 'career_gaps' | 'job_hopping' | 'inconsistencies' | 'seniority_mismatch' | 'location' | 'other';
      status: 'ok' | 'warning' | 'critical';
      detail: string;                // Explicação
    }>;
    
    // Gaps e Mitigações
    gaps: Array<{
      requirement: string;
      priority: string;
      risk: 'low' | 'medium' | 'high';
      mitigation: string;            // LLM-Generated
    }>;
    
    // Análise de Red Flags (LLM-Generated)
    red_flags_analysis: string;      // Parágrafo resumindo
  };
  
  // ========================================
  // AUDITORIA (Colapsável)
  // ========================================
  audit: {
    // Métricas
    total_requirements: number;
    essential_met: number;
    essential_total: number;
    important_met: number;
    important_total: number;
    desirable_met: number;
    desirable_total: number;
    red_flags_count: number;
    
    // Performance
    analysis_time_ms: number;        // Tempo de processamento
    
    // Modelo
    model_version: string;           // "LIA CV Analyzer v1.0"
    llm_model_used: string;          // "claude-sonnet-4-20250514"
    
    // Confiança
    confidence_score: number;        // 0.0-1.0 (LLM-Generated)
    data_completeness: 'alta' | 'media' | 'baixa';
    limitations: string[];           // LLM-Generated
    
    // Rastreabilidade
    cv_hash: string;                 // SHA256 primeiros 8 chars
    job_version: number;             // Versão dos requisitos
    timestamp_utc: string;           // ISO timestamp
  };
}
```

### 2.3 Schema de Input para LLM

O LLM recebe um payload JSON estruturado:

```json
{
  "candidate": {
    "name": "João Silva",
    "current_title": "Senior Backend Developer",
    "years_experience": 6,
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "certifications": ["AWS Solutions Architect"],
    "education": [
      {"degree": "Bacharelado Ciência da Computação", "institution": "USP"}
    ],
    "work_history": [
      {
        "company": "TechCorp",
        "title": "Senior Developer",
        "duration_months": 36,
        "highlights": ["10M+ req/dia", "mentoria de 2 juniors"]
      }
    ],
    "cv_text_summary": "Resumo do CV em texto..."
  },
  "job": {
    "title": "Senior Python Backend Engineer",
    "code": "JOB-2024-0542",
    "department": "Engineering",
    "level": "Senior",
    "requirements": [
      {
        "name": "Python Avançado",
        "priority": "essential",
        "description": "6+ anos de experiência com Python em produção"
      },
      {
        "name": "FastAPI/Django",
        "priority": "essential",
        "description": "Experiência com frameworks web Python"
      }
    ]
  },
  "scoring_results": {
    "global_score": 87,
    "score_label": "Excelente",
    "requirements_evaluation": [
      {
        "requirement": "Python Avançado",
        "priority": "essential",
        "level": "exceeds",
        "score": 100,
        "evidences": [
          "6 anos de experiência com Python em produção",
          "APIs REST processando 10M+ req/dia"
        ]
      },
      {
        "requirement": "Kubernetes",
        "priority": "essential",
        "level": "partial",
        "score": 40,
        "evidences": ["Docker sólido", "Kubernetes: conhecimento básico"]
      }
    ],
    "red_flags": {
      "career_gaps": { "status": "ok", "detail": "Trajetória linear" },
      "job_hopping": { "status": "ok", "detail": "Média 2.5 anos" },
      "seniority_mismatch": { "status": "ok", "detail": "Alinhado" }
    },
    "strengths": [
      "Python Expert com escala (10M+ req/dia)",
      "Certificação AWS válida",
      "Liderança técnica comprovada"
    ],
    "gaps": [
      {
        "requirement": "Kubernetes",
        "priority": "essential",
        "risk": "medium"
      }
    ],
    "category_breakdown": {
      "essential": { "total": 5, "met": 4, "percentage": 80 },
      "important": { "total": 4, "met": 4, "percentage": 100 },
      "desirable": { "total": 3, "met": 2, "percentage": 67 }
    }
  },
  "company_context": {
    "industry": "Tech/SaaS",
    "team_size": 8,
    "culture_values": ["ownership", "collaboration", "learning"]
  }
}
```

---

## 3. Sistema de Scoring (Rubricas, Pesos, Fórmulas)

### 3.1 Níveis de Avaliação (Rubric)

Cada requisito da vaga é avaliado em **4 níveis**:

| Nível | Código | Descrição | Score |
|-------|--------|-----------|-------|
| **Excede** | E+ | Evidências superiores ao esperado | 100% |
| **Atende** | A | Evidências claras de competência | 75% |
| **Parcial** | P | Evidências limitadas ou indiretas | 40% |
| **Ausente** | X | Nenhuma evidência encontrada | 0% |

**Significado detalhado:**

| Nível | Significado | Exemplo |
|-------|-------------|---------|
| **Excede** | Candidato apresenta evidências superiores ao esperado | Vaga pede 3 anos, candidato tem 6+ anos com projetos de destaque |
| **Atende** | Candidato demonstra competência clara e direta | Experiência compatível com o requisito |
| **Parcial** | Candidato tem experiência adjacente ou limitada | Conhece a tecnologia, mas sem projetos relevantes |
| **Ausente** | Nenhuma evidência encontrada no CV | Pode ser gap real ou falta de informação |

### 3.2 Prioridades de Requisitos

| Prioridade | Peso | Significado | Impacto |
|------------|------|-------------|---------|
| **Essencial** | 3.0x | Requisito eliminatório. Candidato deve demonstrar competência | Se "Ausente" em essencial: score muito baixo, recomendação negativa |
| **Importante** | 2.0x | Requisito valorizado, mas compensável | Impacta score significativamente, mas não é eliminatório |
| **Desejável** | 1.0x | Diferencial, "nice to have" | Contribui para score, mas ausência não prejudica |

### 3.3 Fórmulas de Cálculo

#### Score por Requisito

```
score_requisito = 
  - 100 se level = 'exceeds'
  - 75  se level = 'meets'
  - 40  se level = 'partial'
  - 0   se level = 'missing'
```

#### Score Global Ponderado

```
peso_priority = 
  - 3.0 se priority = 'essential'
  - 2.0 se priority = 'important'
  - 1.0 se priority = 'nice-to-have'

score_global = 
  Σ (score_requisito × peso_priority) / Σ (100 × peso_priority) × 100
```

**Exemplo de cálculo:**
```
Requisitos:
- Python (essential, exceeds=100): 100 × 3.0 = 300
- FastAPI (essential, meets=75):   75 × 3.0 = 225
- Docker (important, partial=40):  40 × 2.0 = 80
- GraphQL (nice-to-have, missing=0): 0 × 1.0 = 0

Máximo possível: (100×3.0) + (100×3.0) + (100×2.0) + (100×1.0) = 900

Score = (300 + 225 + 80 + 0) / 900 × 100 = 67.2%
```

### 3.4 Classificação por Score

| Score | Label | Recomendação Padrão |
|-------|-------|---------------------|
| 85-100% | Excelente | APROVAR_TRIAGEM |
| 70-84% | Bom | APROVAR_TRIAGEM |
| 50-69% | Moderado | MANTER_ESPERA |
| 30-49% | Fraco | NAO_PROSSEGUIR |
| 0-29% | Inadequado | NAO_PROSSEGUIR |

### 3.5 Red Flags (Sinais de Alerta)

| Tipo | O que verifica | Critério de Warning |
|------|----------------|---------------------|
| `career_gaps` | Gaps inexplicados na carreira | Gap > 6 meses sem explicação |
| `job_hopping` | Trocas frequentes de emprego | Média < 1.5 anos por empresa |
| `inconsistencies` | Dados conflitantes | Datas sobrepostas, informações contraditórias |
| `seniority_mismatch` | Senioridade incompatível | Título declarado vs. experiência evidenciada |
| `location` | Localização/disponibilidade | Candidato não aceita modelo de trabalho da vaga |

### 3.6 Data Completeness

```
data_completeness = 
  - 'alta'  se CV tem: skills + work_history + education + 3+ anos de experiência
  - 'media' se CV tem: skills + work_history (básico)
  - 'baixa' se CV está incompleto ou parseado com erros
```

---

## 4. Geração por LLM (Prompts, Templates, Guardrails)

### 4.1 System Prompt (Guardrails)

Este prompt deve ser enviado como `system` em todas as chamadas:

```
Você é a LIA (Learning Intelligence Assistant), uma especialista em recrutamento e seleção da WeDo Talent. Sua função é gerar pareceres de avaliação de candidatos de forma objetiva, profissional e acionável.

## Sua Identidade

- Nome: LIA
- Papel: Assistente de Inteligência em Talentos
- Especialidade: Avaliação de candidatos baseada em metodologia WSI (Work Sample Interview)
- Tom de voz: Profissional, objetivo, empático, sem jargões excessivos

## Diretrizes Obrigatórias

### Formato
- Retorne SEMPRE JSON válido conforme o schema especificado
- Use Markdown apenas onde explicitamente permitido
- Mantenha estrutura consistente em todas as respostas

### Conteúdo
- Base toda afirmação em evidências do CV ou dados fornecidos
- Não faça suposições sobre informações não presentes
- Marque claramente inferências vs. fatos documentados
- Use linguagem neutra e inclusiva

### Compliance (OBRIGATÓRIO)
- NÃO mencione: idade, gênero, etnia, religião, orientação sexual, estado civil, deficiência, nacionalidade, aparência física
- NÃO use palavras como: "jovem", "maduro", "energético", "dinâmico", "agressivo"
- NÃO faça suposições baseadas em nomes, universidades ou localização
- Trate todos os dados como confidenciais

### Qualidade
- Pareceres devem ser acionáveis (o recrutador sabe o que fazer depois)
- Mitigações devem ser realistas e com prazo estimado
- Pontos fortes devem incluir impacto de negócio
- Evidências devem ser específicas (números, projetos, resultados)

## Regras de Decisão

Baseie a recomendação no score global:
- Score >= 70%: APROVAR_TRIAGEM (recomendar prosseguir)
- Score 50-69%: MANTER_ESPERA (avaliação adicional necessária)
- Score < 50%: NAO_PROSSEGUIR (gaps significativos)

Exceções:
- Red flag crítico: Sempre recomendar avaliação manual, independente do score
- Todos requisitos essenciais atendidos: Pode recomendar aprovar mesmo com score 65-70%
- Requisito essencial ausente: Máximo "MANTER_ESPERA", mesmo com score alto
```

### 4.2 Prompt Principal: Gerar Avaliação Completa

```
## Tarefa

Gere a avaliação narrativa para o candidato abaixo com base nos scores já calculados. Sua função é EXPLICAR e CONTEXTUALIZAR os dados, não recalculá-los.

## Dados de Entrada

{scoring_results_json}

## Schema de Saída (JSON)

Retorne EXATAMENTE este formato:

{
  "overview": {
    "parecer_lia": {
      "contexto_fit": "STRING - 2-3 frases contextualizando a trajetória do candidato com a vaga. Conecte experiências passadas com os requisitos.",
      
      "pontos_fortes_impacto": [
        {
          "ponto": "STRING - Nome do ponto forte (máx 5 palavras)",
          "evidencia": "STRING - Trecho do CV ou dado específico que comprova",
          "impacto_negocio": "STRING - Por que isso é valioso para a vaga/empresa"
        }
      ],
      
      "riscos_mitigacoes": [
        {
          "risco": "STRING - Gap ou preocupação identificada",
          "nivel": "baixo | medio | alto",
          "mitigacao": "STRING - Como pode ser resolvido/compensado",
          "tempo_estimado": "STRING - Ex: '2-3 meses com mentoria'"
        }
      ],
      
      "recomendacao_final": {
        "decisao": "APROVAR_TRIAGEM | MANTER_ESPERA | NAO_PROSSEGUIR",
        "justificativa": "STRING - 2-3 frases objetivas explicando a decisão",
        "proximos_passos": ["STRING - Ação 1", "STRING - Ação 2"]
      }
    },
    
    "why_candidate": [
      "STRING - Razão 1: [Título] - [Explicação com evidência]",
      "STRING - Razão 2: [Título] - [Explicação com evidência]",
      "STRING - Razão 3: [Título] - [Explicação com evidência]"
    ]
  },
  
  "details": {
    "requirements_narrative": [
      {
        "requirement_id": "STRING - ID do requisito",
        "narrative": "STRING - 1-2 frases explicando por que o candidato foi classificado neste nível"
      }
    ],
    
    "red_flags_analysis": "STRING - Parágrafo de 3-4 frases analisando os sinais de alerta. Se todos OK, explique brevemente. Se warning/critical, contextualize."
  },
  
  "audit": {
    "confidence_score": 0.0-1.0,
    "data_completeness": "alta | media | baixa",
    "limitations": ["STRING - Limitação 1", "STRING - Limitação 2"]
  }
}

## Regras de Geração

### 1. contexto_fit
- Máximo 3 frases
- Mencione a vaga específica por nome
- Conecte 1-2 experiências passadas do candidato com os requisitos
- Tom: objetivo e contextual

### 2. pontos_fortes_impacto
- Mínimo 2, máximo 4 itens
- Priorize requisitos onde candidato obteve "exceeds" ou "meets"
- Evidências devem ser específicas (números, projetos, métricas)
- Impacto deve responder "por que isso importa para a vaga?"

### 3. riscos_mitigacoes
- Liste APENAS se houver gaps (requirements com "partial" ou "missing" + priority "essential" ou "important")
- Se não houver gaps significativos, retorne array vazio []
- Mitigações devem ser realistas e acionáveis
- Tempo estimado deve ser razoável (não otimista demais)

### 4. recomendacao_final.decisao
- APROVAR_TRIAGEM: score >= 70% OU todos essenciais atendidos
- MANTER_ESPERA: score 50-69% OU essencial parcial
- NAO_PROSSEGUIR: score < 50% OU essencial ausente

### 5. why_candidate
- Exatamente 3 razões
- Formato: "[Título curto]: [Explicação com evidência]"
- Foco no valor que o candidato traz
- Evite repetir os pontos_fortes_impacto

### 6. requirements_narrative
- Uma entrada para CADA requisito
- Se "exceeds": destaque o diferencial
- Se "meets": confirme a competência
- Se "partial": explique o que falta
- Se "missing": seja objetivo, não apologético

### 7. confidence_score
- 0.9-1.0: CV completo, evidências claras, matching direto
- 0.7-0.89: CV bom, algumas inferências necessárias
- 0.5-0.69: CV incompleto ou ambíguo
- < 0.5: CV muito limitado, avaliação incerta

### 8. limitations
- Liste qualquer aspecto que limitou a análise
- Ex: "CV não menciona período específico de experiência com X"
- Ex: "Informações de certificações não verificáveis"
```

### 4.3 Prompts Específicos (Fallback)

#### Contexto e Fit

```
Gere o texto de "Contexto e Fit" para este candidato:

Candidato: {candidate_name}
Vaga: {job_title}
Score Global: {global_score}%
Requisitos Essenciais Atendidos: {essential_met}/{essential_total}
Principais Skills: {top_skills}
Experiência Relevante: {relevant_experience}

Regras:
- Máximo 3 frases
- Conecte experiências passadas com requisitos da vaga
- Mencione a vaga pelo nome
- Tom objetivo e profissional

Retorne apenas o texto, sem JSON.
```

#### Pontos Fortes com Impacto

```
Gere os Pontos Fortes com Impacto de Negócio para este candidato:

Requisitos que o candidato EXCEDE ou ATENDE:
{requirements_met_json}

Histórico do Candidato:
{work_history_summary}

Regras:
- 2-4 pontos fortes
- Cada ponto deve ter: nome, evidência específica, impacto para a vaga
- Evidências devem ser concretas (números, projetos)
- Impacto deve responder "por que isso importa?"

Retorne JSON array:
[
  {"ponto": "...", "evidencia": "...", "impacto_negocio": "..."}
]
```

#### Riscos e Mitigações

```
Analise os gaps deste candidato e proponha mitigações:

Requisitos PARCIAIS ou AUSENTES:
{gaps_json}

Contexto do Candidato:
- Anos de experiência: {years_experience}
- Skills adjacentes: {adjacent_skills}
- Potencial de desenvolvimento: {development_potential}

Regras:
- Liste apenas gaps de requisitos ESSENCIAIS ou IMPORTANTES
- Mitigações devem ser realistas
- Inclua tempo estimado para desenvolvimento
- Se não houver gaps significativos, retorne []

Retorne JSON array:
[
  {"risco": "...", "nivel": "baixo|medio|alto", "mitigacao": "...", "tempo_estimado": "..."}
]
```

#### Recomendação Final

```
Gere a recomendação final para este candidato:

Score Global: {global_score}%
Essenciais Atendidos: {essential_met}/{essential_total}
Red Flags: {red_flags_count} ({red_flags_types})
Principais Gaps: {main_gaps}
Principais Forças: {main_strengths}

Regras de Decisão:
- Score >= 70% + sem red flags críticos = APROVAR_TRIAGEM
- Score 50-69% OU essencial parcial = MANTER_ESPERA
- Score < 50% OU essencial ausente = NAO_PROSSEGUIR

Retorne JSON:
{
  "decisao": "APROVAR_TRIAGEM | MANTER_ESPERA | NAO_PROSSEGUIR",
  "justificativa": "2-3 frases objetivas",
  "proximos_passos": ["Ação 1", "Ação 2"]
}
```

#### Por que este candidato?

```
Gere 3 razões persuasivas para considerar este candidato:

Candidato: {candidate_name}
Vaga: {job_title}
Score: {global_score}%
Principais Competências Atendidas: {competencies_met}
Diferenciais: {differentials}

Regras:
- Exatamente 3 razões
- Formato: "[Título]: [Explicação com evidência]"
- Seja específico, use dados do CV
- Foco no valor para a vaga, não em qualificações genéricas

Retorne JSON array de 3 strings.
```

### 4.4 Tratamento de Erros

Se o LLM retornar formato inválido, use estes defaults:

```python
DEFAULT_PARECER = {
    "contexto_fit": "Avaliação baseada nos dados disponíveis do candidato.",
    "pontos_fortes_impacto": [],
    "riscos_mitigacoes": [],
    "recomendacao_final": {
        "decisao": "MANTER_ESPERA",
        "justificativa": "Avaliação requer revisão manual devido a limitações nos dados.",
        "proximos_passos": ["Revisar CV manualmente", "Solicitar informações adicionais"]
    }
}

DEFAULT_AUDIT = {
    "confidence_score": 0.5,
    "data_completeness": "baixa",
    "limitations": ["Avaliação automática encontrou limitações. Revisão manual recomendada."]
}
```

---

## 5. Regras de Negócio e Automação

### 5.1 Regras de Scoring

1. **Requisito Essencial Ausente**: Se qualquer requisito `essential` for `missing`, o score máximo é limitado a 60%
2. **Todos Essenciais Atendidos**: Bônus de 5% no score global
3. **Red Flag Critical**: Reduz score em 10%
4. **Red Flag Warning**: Reduz score em 5%

### 5.2 Regras de Automação

```python
# Auto-approve
if score >= config.auto_approve_threshold and red_flags_critical == 0:
    action = 'APROVAR_TRIAGEM'
    notify_recruiter = False  # Segue automaticamente

# Auto-reject
if score < config.auto_reject_threshold or red_flags_critical > 0:
    action = 'NAO_PROSSEGUIR'
    notify_recruiter = True   # Recrutador pode revisar

# Manual review
else:
    action = 'MANTER_ESPERA'
    notify_recruiter = True   # Requer decisão humana
```

### 5.3 Regras de Notificação

| Evento | Notifica | Canais |
|--------|----------|--------|
| Score >= 85% | Sim | Bell, Email |
| Score 70-84% | Sim | Bell |
| Score 50-69% | Sim | Bell (baixa prioridade) |
| Score < 50% | Não (a menos que configurado) | - |
| Red Flag Critical | Sempre | Bell, Email |

### 5.4 Decisões de Recomendação

| Decisão | Significado | Próximos Passos |
|---------|-------------|-----------------|
| `APROVAR_TRIAGEM` | Candidato atende requisitos mínimos, deve prosseguir | Agendar Quick Screening ou entrevista |
| `MANTER_ESPERA` | Candidato tem potencial, mas gaps significativos | Avaliar experiências adjacentes, considerar outras vagas |
| `NAO_PROSSEGUIR` | Candidato não atende requisitos mínimos | Manter em talent pool para futuro, enviar feedback |

---

## 6. Integração com a Plataforma

### 6.1 Implementação do Serviço

```python
# 1. Scoring Engine (Determinístico - Python/Backend)
class CVEvaluationScorer:
    def calculate_rubric_scores(self, cv: CV, job: Job) -> ScoringResult:
        """
        Calcula scores de forma determinística:
        - Match de skills (fuzzy matching)
        - Experiência vs requisito (anos)
        - Senioridade alignment
        - Red flags detection
        """
        requirements_scores = []
        for req in job.requirements:
            score = self._evaluate_requirement(cv, req)
            evidences = self._extract_evidences(cv, req)
            requirements_scores.append({
                "requirement": req.name,
                "priority": req.priority,
                "level": self._score_to_level(score),  # exceeds/meets/partial/missing
                "score": score,
                "evidences": evidences
            })
        
        return ScoringResult(
            global_score=self._calculate_weighted_score(requirements_scores),
            requirements=requirements_scores,
            red_flags=self._detect_red_flags(cv),
            strengths=self._identify_strengths(cv, job),
            gaps=self._identify_gaps(requirements_scores)
        )

# 2. LLM Narration Service
class EvaluationNarrator:
    def generate_evaluation(self, scoring_result: ScoringResult) -> EvaluationNarrative:
        """
        Chama LLM para gerar narrativas baseadas nos scores calculados
        """
        prompt = self._build_prompt(scoring_result)
        
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            system=SYSTEM_PROMPT_GUARDRAILS,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_response(response)

# 3. Orquestrador
class EvaluationComposerService:
    def compose_evaluation(self, cv: CV, job: Job) -> FullEvaluation:
        # Etapa 1: Calcular scores (determinístico)
        scoring_result = self.scorer.calculate_rubric_scores(cv, job)
        
        # Etapa 2: Gerar narrativas (LLM)
        narrative = self.narrator.generate_evaluation(scoring_result)
        
        # Etapa 3: Compor resultado final
        return FullEvaluation(
            scores=scoring_result,  # Dados calculados
            narrative=narrative,    # Texto gerado por LLM
            audit=self._generate_audit_metadata()
        )
```

### 6.2 Componentes que Consomem esta Avaliação

| Componente | Dados Consumidos | Uso |
|------------|------------------|-----|
| `JobKanbanPage` | `global_score`, `score_label` | Badge no card do candidato |
| `RubricEvaluationModal` | Todos os dados | Visualização completa |
| `CandidateTimeline` | `created_at`, `score`, `recommendation` | Registro histórico |
| `TriagemService` | `recommendation`, `score` | Decisões automatizadas |
| `NotificationService` | `score`, `red_flags` | Alertas para recrutadores |
| `ReportGenerator` | Todos os dados | Exportação PDF/Excel |
| `BiasAuditService` | `audit` | Compliance e auditoria |

### 6.3 Agentes que Utilizam os Dados

| Agente | Dados Utilizados | Decisão |
|--------|------------------|---------|
| `ScreeningAgent` | `recommendation`, `gaps` | Priorizar candidatos para triagem |
| `SchedulingAgent` | `score`, `strengths` | Definir urgência de agendamento |
| `CommunicationAgent` | `score_label`, `why_candidate` | Personalizar mensagens |
| `TaskPlannerAgent` | `recommendation` | Criar tarefas para recrutadores |

### 6.4 Prompts para Outros Agentes

#### ScreeningAgent - Priorização

```
Você é o ScreeningAgent da WeDo Talent. Sua tarefa é priorizar candidatos para triagem.

Avaliações disponíveis:
{evaluations_json}

Critérios de Priorização:
1. Score >= 85%: Alta prioridade
2. Score 70-84%: Média prioridade
3. Score 50-69%: Baixa prioridade (requer revisão)
4. Score < 50%: Não priorizar

Fatores Adicionais:
- Tempo na fila (candidatos antigos têm prioridade)
- Red flags críticos (sempre revisar antes de aprovar)
- Urgência da vaga (vagas com deadline próximo têm prioridade)

Retorne lista ordenada de candidate_ids com justificativa.
```

#### CommunicationAgent - Personalização de Mensagem

```
Você é o CommunicationAgent da WeDo Talent. Sua tarefa é personalizar comunicações.

Avaliação do Candidato:
{evaluation_json}

Template Base:
{template_text}

Regras de Personalização:
- Use "why_candidate" para destacar pontos positivos
- Não mencione gaps ou scores numéricos
- Tom: positivo, profissional, encorajador
- Se score < 50%: Use template de feedback construtivo

Retorne mensagem personalizada.
```

#### TaskPlannerAgent - Criação de Tarefas

```
Você é o TaskPlannerAgent da WeDo Talent. Crie tarefas baseadas na avaliação.

Avaliação:
{evaluation_json}

Regras:
- APROVAR_TRIAGEM: Criar tarefa "Agendar triagem para {candidate_name}"
- MANTER_ESPERA: Criar tarefa "Revisar candidato {candidate_name} - avaliação adicional"
- NAO_PROSSEGUIR: Criar tarefa "Enviar feedback para {candidate_name}"

Se houver red_flags críticos:
- Criar tarefa adicional "Verificar red flag: {flag_type} - {candidate_name}"

Retorne lista de tarefas no formato:
[
  {"title": "...", "priority": "high|medium|low", "due_in_days": N, "assignee": "recruiter|lia"}
]
```

### 6.5 Versionamento e Histórico

#### Quando Reavaliar?

- CV do candidato atualizado
- Requisitos da vaga alterados
- Nova versão do modelo de scoring
- Solicitação manual do recrutador

#### Histórico de Avaliações

Cada avaliação é imutável após criada. Novas avaliações geram novos registros:

```sql
-- Tabela: cv_evaluations
id              UUID PRIMARY KEY
candidate_id    UUID NOT NULL
job_id          UUID NOT NULL
company_id      UUID NOT NULL
version         INTEGER DEFAULT 1
evaluation_data JSONB NOT NULL       -- Schema completo
created_at      TIMESTAMP NOT NULL
created_by      VARCHAR(50)          -- 'system' | 'user:xxx'
is_current      BOOLEAN DEFAULT true -- Apenas uma é "current"
```

### 6.6 Tab de Auditoria: Recomendações de UX

**Recomendação: Manter, mas Secundária**

**Por que manter:**
1. **Compliance**: Empresas precisam auditar decisões de IA (LGPD, NYC LL144, EU AI Act)
2. **Confiança**: Mostra transparência no processo de avaliação
3. **Debugging**: Ajuda a entender por que uma avaliação foi feita de certa forma
4. **Diferencial**: Poucos sistemas de recrutamento oferecem auditabilidade

**Como melhorar UX:**
1. **Opção 1**: Manter como tab, mas ser a última (menos clicada)
2. **Opção 2**: Transformar em painel colapsável dentro de "Detalhes"
3. **Opção 3**: Botão "Ver auditoria completa" que abre um drawer/modal separado
4. **Opção 4**: Remover do modal e disponibilizar em página separada de compliance

**Sugestão**: **Opção 3** - Botão discreto no footer "Ver auditoria" que abre um drawer. Mantém a informação acessível mas não polui a experiência principal.

---

## 7. Exemplos Completos

### 7.1 Avaliação Completa - Candidato Excelente (Score 87%)

```markdown
# AVALIAÇÃO CV vs VAGA

**Candidato:** João Silva
**Vaga:** Senior Python Backend Engineer
**Código:** JOB-2024-0542
**Data:** 21/12/2024 09:30
**Avaliado por:** LIA (Análise Automatizada CV vs Vaga)

---

## SCORE DE ADERÊNCIA

**Score Global: 87%** - Excelente

| Categoria | Atendimento |
|-----------|-------------|
| Essenciais (5) | 4/5 (80%) |
| Importantes (4) | 4/4 (100%) |
| Desejáveis (3) | 2/3 (67%) |

---

## AVALIAÇÃO POR REQUISITO

### 1. Python Avançado (Essencial)
**Nível:** Excede ✓✓

**Evidências:**
- 6 anos de experiência com Python em produção
- Desenvolveu APIs REST processando 10M+ requisições/dia
- Contribuições open source (FastAPI plugins)

**Justificativa:** Candidato demonstra domínio expert comprovado por experiência em escala e contribuições à comunidade.

**Score:** 100%

---

### 2. FastAPI/Django (Essencial)
**Nível:** Atende ✓

**Evidências:**
- 3 anos com FastAPI (projeto atual)
- 2 anos anteriores com Django
- Implementou rate limiting, caching, auth JWT

**Justificativa:** Experiência sólida com ambos frameworks em contexto profissional.

**Score:** 75%

---

### 3. PostgreSQL (Essencial)
**Nível:** Atende ✓

**Evidências:**
- Modelagem de banco para sistema multi-tenant
- Otimização de queries (índices, particionamento)
- Experiência com Alembic migrations

**Justificativa:** Conhecimento aplicado em cenários de complexidade média-alta.

**Score:** 75%

---

### 4. Docker/Kubernetes (Essencial)
**Nível:** Parcial ⚠️

**Evidências:**
- Docker: uso em desenvolvimento e CI/CD
- Kubernetes: mencionado como "conhecimento básico"
- Não menciona decisões arquiteturais de orquestração

**Justificativa:** Docker sólido, mas Kubernetes superficial para nível senior.

**Score:** 40%

---

### 5. Liderança Técnica (Essencial)
**Nível:** Atende ✓

**Evidências:**
- "Mentoria de 2 desenvolvedores junior"
- "Responsável por code reviews do time"
- "Defini padrões de arquitetura do módulo de pagamentos"

**Justificativa:** Demonstra liderança técnica consistente em nível de equipe.

**Score:** 75%

---

## RED FLAGS

| Red Flag | Status | Detalhe |
|----------|--------|---------|
| Gaps na carreira | ✓ OK | Trajetória linear |
| Job hopping | ✓ OK | Média 2.5 anos por empresa |
| Inconsistências | ✓ OK | Dados consistentes |
| Senioridade | ✓ OK | 6 anos alinhado com senior |
| Localização | ✓ OK | Aceita remoto (vaga remota) |

**Red Flags Detectados:** 0

---

## PONTOS FORTES

1. **Python Expert com Escala**
   - Experiência em sistemas com 10M+ req/dia
   - Contribuições open source demonstram profundidade

2. **Cultura de Testes Matura**
   - 90% coverage é excepcional para o mercado
   - Uso de ferramentas avançadas (TestContainers)

3. **Certificação AWS**
   - Valida conhecimento teórico-prático em cloud
   - Demonstra investimento em desenvolvimento profissional

4. **Liderança Técnica Comprovada**
   - Mentoria + code reviews + definição de padrões
   - Pronto para expandir responsabilidades

---

## GAPS E MITIGAÇÕES

1. **Kubernetes (Essencial - Parcial)**
   - Risco: Médio
   - Mitigação: Pode desenvolver com mentoria em 2-3 meses
   - Docker sólido facilita curva de aprendizado

---

## POR QUE ESTE CANDIDATO?

João Silva apresenta **87% de aderência** aos requisitos da vaga Senior Python Backend Engineer, classificando-se como **Excelente**.

### Razões para Consideração:

1. **Domínio Expert em Python**: 6 anos de experiência incluindo sistemas de alta escala (10M+ req/dia) e contribuições open source demonstram maturidade técnica excepcional.

2. **Cultura de Qualidade**: Coverage de 90% e uso de ferramentas avançadas de teste indicam compromisso com qualidade e boas práticas.

3. **Liderança Pronta**: Mentoria de juniors e definição de padrões arquiteturais mostram que está pronto para responsabilidades ampliadas.

4. **Stack Alinhada**: Experiência direta com FastAPI, PostgreSQL, AWS e CI/CD cobre a maior parte das tecnologias core da vaga.

### Gap Mitigável:

O único gap essencial (Kubernetes) é compensável considerando:
- Experiência sólida em Docker (base para K8s)
- Capacidade de aprendizado demonstrada
- Time atual tem especialistas em infra

### Recomendação: **APROVAR PARA TRIAGEM**

**Justificativa:** Candidato apresenta perfil técnico forte com 4/5 requisitos essenciais atendidos plenamente. O gap em Kubernetes é mitigável e não impacta a capacidade de contribuição imediata. Recomenda-se prosseguir para triagem conversacional (Quick Screening) para validar soft skills e fit cultural.

---

## MÉTRICAS DE AUDITORIA

| Métrica | Valor |
|---------|-------|
| Total de Requisitos | 12 |
| Requisitos Essenciais | 5 (4 atendidos - 80%) |
| Requisitos Importantes | 4 (4 atendidos - 100%) |
| Requisitos Desejáveis | 3 (2 atendidos - 67%) |
| Red Flags Detectados | 0 |
| Score Ponderado Global | 87% |
| Tempo de Análise | 2.3 segundos |
| Versão do Modelo | LIA CV Analyzer v1.0 |
| Hash do CV | a3f8c2d1 |
| Timestamp UTC | 2024-12-21T09:30:45Z |
```

### 7.2 Saída JSON - Candidato Excelente

```json
{
  "overview": {
    "parecer_lia": {
      "contexto_fit": "João Silva apresenta um perfil técnico sólido e bem alinhado com a posição de Senior Python Backend Engineer. Com 6 anos de experiência em ambientes de alta escala, incluindo sistemas processando 10M+ requisições diárias, demonstra a maturidade técnica esperada para o nível sênior.",
      
      "pontos_fortes_impacto": [
        {
          "ponto": "Experiência em Alta Escala",
          "evidencia": "APIs REST processando 10M+ req/dia na TechCorp",
          "impacto_negocio": "Pode contribuir imediatamente em sistemas críticos sem curva de aprendizado em práticas de escalabilidade"
        },
        {
          "ponto": "Cultura de Qualidade",
          "evidencia": "Coverage de 90% em testes automatizados",
          "impacto_negocio": "Reduz risco de bugs em produção e acelera ciclos de deploy"
        },
        {
          "ponto": "Liderança Técnica",
          "evidencia": "Mentoria de 2 juniors + responsável por code reviews",
          "impacto_negocio": "Pronto para disseminar boas práticas e assumir responsabilidades ampliadas"
        }
      ],
      
      "riscos_mitigacoes": [
        {
          "risco": "Kubernetes superficial para nível senior",
          "nivel": "medio",
          "mitigacao": "Docker sólido facilita curva de aprendizado. Pair programming com SRE do time acelera desenvolvimento",
          "tempo_estimado": "2-3 meses"
        }
      ],
      
      "recomendacao_final": {
        "decisao": "APROVAR_TRIAGEM",
        "justificativa": "Candidato atende 4 de 5 requisitos essenciais com evidências sólidas de aplicação prática. O único gap identificado (Kubernetes) é mitigável e não impacta capacidade de contribuição imediata.",
        "proximos_passos": [
          "Agendar Quick Screening para validar soft skills e fit cultural",
          "Explorar experiência com sistemas distribuídos durante triagem"
        ]
      }
    },
    
    "why_candidate": [
      "Escala Comprovada: Experiência com sistemas de 10M+ requisições/dia demonstra capacidade de lidar com nosso volume de tráfego",
      "Qualidade Excepcional: Coverage de 90% em testes está acima da média do mercado (típico: 60-70%), indicando forte compromisso com qualidade",
      "Liderança Pronta: Já mentora desenvolvedores e define padrões técnicos, alinhado com expectativas de crescimento para a posição"
    ]
  },
  
  "details": {
    "requirements_narrative": [
      {"requirement_id": "req-001", "narrative": "Candidato excede expectativas com 6 anos de Python em produção e contribuições open source, demonstrando domínio técnico profundo."},
      {"requirement_id": "req-002", "narrative": "Atende plenamente com 3 anos de FastAPI e 2 anos anteriores de Django, cobrindo ambos frameworks requeridos."},
      {"requirement_id": "req-003", "narrative": "Atende com experiência em modelagem multi-tenant e otimização de queries em PostgreSQL."},
      {"requirement_id": "req-004", "narrative": "Atende parcialmente: Docker sólido, mas Kubernetes limitado a conhecimento básico conforme autodeclaração."},
      {"requirement_id": "req-005", "narrative": "Atende com evidências de mentoria de 2 juniors e responsabilidade por code reviews do time."}
    ],
    
    "red_flags_analysis": "Não foram identificados sinais de alerta significativos. O candidato apresenta trajetória linear de crescimento, média de 2.5 anos por empresa (dentro do esperado), e dados consistentes entre experiências declaradas."
  },
  
  "audit": {
    "confidence_score": 0.92,
    "data_completeness": "alta",
    "limitations": []
  }
}
```

---

## Limitações Conhecidas

1. **Parsing de CV**: CVs em formatos não-padrão podem ter extração imperfeita
2. **Matching de Skills**: Sinônimos e variações podem não ser 100% capturados
3. **Contexto Cultural**: LLM pode não entender nuances culturais específicas
4. **Dados Incompletos**: Avaliação é limitada pela qualidade dos dados de entrada
5. **Atualização**: Score não atualiza automaticamente se CV ou vaga mudam (precisa trigger)

---

## Boas Práticas de Aplicação

### 1. Extração de Evidências
- Cite trechos específicos do CV
- Não infira além do documentado
- Marque claramente inferências vs fatos

### 2. Calibração de Níveis
- **Excede**: Requer evidências explícitas superiores
- **Atende**: Evidência clara e direta
- **Parcial**: Experiência adjacente ou limitada
- **Ausente**: Sem menção relevante

### 3. Priorização de Requisitos
- Essenciais são eliminatórios se Ausente
- Importantes impactam significativamente o score
- Desejáveis são diferenciadores

### 4. Parecer de Potencial
- Foco em "por que sim" antes de "por que não"
- Mitigações concretas para gaps
- Recomendação acionável

### 5. Auditabilidade
- Toda decisão tem justificativa
- Métricas rastreáveis
- Hash do CV para verificação

---

*Documento Consolidado - Versão 1.0*
*Última atualização: Janeiro 2026*
*Metodologia: Rubric-Based Assessment + WSI Framework*
