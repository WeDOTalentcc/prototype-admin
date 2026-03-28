# Sistema de Análise Proativa da LIA no Wizard de Vagas

**Data:** 25 de Janeiro de 2026  
**Versão:** 1.0  
**Referência:** Wizard de Criação de Vagas (7 Etapas)

---

## 1. Visão Geral do Sistema de Análise

O Wizard de Criação de Vagas utiliza uma **camada de inteligência proativa** que analisa as informações fornecidas pelo recrutador em tempo real, inferindo:

- Skills técnicas e comportamentais
- Responsabilidades e requisitos
- Faixa salarial e benefícios
- Alinhamento com políticas da empresa
- Benchmarks de mercado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE ANÁLISE PROATIVA DA LIA                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────────────────────────────────┐  │
│  │ Descrição do     │     │              SERVIÇOS DE ANÁLISE             │  │
│  │ Recrutador       │────▶│                                              │  │
│  │                  │     │  ┌────────────────────────────────────────┐  │  │
│  │ "Preciso de um   │     │  │ IntelligenceLayerService               │  │  │
│  │  Dev Python      │     │  │ - Detecção de padrões                  │  │  │
│  │  Sênior para     │     │  │ - Correlação de outcomes               │  │  │
│  │  Dados em SP"    │     │  │ - Sugestões contextuais                │  │  │
│  └──────────────────┘     │  └────────────────────────────────────────┘  │  │
│                           │                    │                          │  │
│                           │                    ▼                          │  │
│                           │  ┌────────────────────────────────────────┐  │  │
│                           │  │ SkillsCatalogService                   │  │  │
│                           │  │ - Catálogo de skills por área          │  │  │
│                           │  │ - Mapeamento cargo → competências      │  │  │
│                           │  │ - Ajuste por senioridade               │  │  │
│                           │  └────────────────────────────────────────┘  │  │
│                           │                    │                          │  │
│                           │                    ▼                          │  │
│                           │  ┌────────────────────────────────────────┐  │  │
│                           │  │ CompensationAnalysisService            │  │  │
│                           │  │ - Política salarial da empresa         │  │  │
│                           │  │ - Benchmark de mercado                 │  │  │
│                           │  │ - Análise de benefícios                │  │  │
│                           │  │ - Total Compensation                   │  │  │
│                           │  └────────────────────────────────────────┘  │  │
│                           │                    │                          │  │
│                           │                    ▼                          │  │
│                           │  ┌────────────────────────────────────────┐  │  │
│                           │  │ MarketBenchmarkService                 │  │  │
│                           │  │ - Pesquisa web de salários             │  │  │
│                           │  │ - Tendências de mercado                │  │  │
│                           │  │ - Skills em demanda                    │  │  │
│                           │  └────────────────────────────────────────┘  │  │
│                           └──────────────────────────────────────────────┘  │
│                                               │                              │
│                                               ▼                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    PARECER DA LIA (EvaluationResponse)               │   │
│  │                                                                       │   │
│  │  • detected_fields: {title, seniority, department, skills...}        │   │
│  │  • completeness_score: 85%                                           │   │
│  │  • company_alignment: {culture_match, skills_from_catalog}           │   │
│  │  • market_alignment: {salary_percentile, market_demand}              │   │
│  │  • compensation_analysis: {salary, bonus, benefits, total_comp}      │   │
│  │  • suggestions: [{field, suggested, reason, source}...]              │   │
│  │  • recommended_action: "proceed" | "review_compensation" | "missing" │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                               │                              │
│                                               ▼                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    INTERFACE DO RECRUTADOR                            │   │
│  │                                                                       │   │
│  │  ┌─ Painel de Sugestões ────────────────────────────────────────┐    │   │
│  │  │  ✅ Python, SQL, Spark (detectados da descrição)             │    │   │
│  │  │  💡 Machine Learning, Docker (sugeridos pelo catálogo)       │    │   │
│  │  │  ⚠️ Faixa salarial 15% abaixo do mercado                     │    │   │
│  │  │                                                               │    │   │
│  │  │  [Aceitar Todas] [Revisar Individualmente] [Ignorar]         │    │   │
│  │  └───────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fluxo dos Agentes de IA

### 2.1. Job Intake Agent - Detecção de Critérios

O **JobIntakeAgent** é o agente principal responsável pela análise inicial:

```python
# Prompt de extração de critérios
ENHANCED_CRITERIA_EXTRACTION_PROMPT = """
Extraia APENAS os critérios mencionados EXPLICITAMENTE ou fortemente implícitos:

## Campos a Detectar:
- cargo: Título/cargo da vaga
- senioridade: Nível (Júnior, Pleno, Sênior, Lead, etc.)
- departamento: Área ou departamento
- localizacao: Cidade, estado ou região
- competencias_tecnicas: Lista de tecnologias, linguagens, ferramentas
- competencias_comportamentais: Soft skills mencionadas
- faixa_salarial: Se mencionada explicitamente

## Para cada critério:
- value: O valor extraído
- confidence: "alta" | "média" | "baixa"
- source: Trecho original que suporta a extração
"""
```

**Ações do Agente:**
1. `detect_criteria` - Detecta critérios automaticamente do texto
2. `generate_wsi_questions` - Gera perguntas de triagem baseadas em metodologia WSI
3. `sugerir_melhorias` - Sugere melhorias para a job description

---

## 3. Inferência de Skills Técnicas e Comportamentais

### 3.1. SkillsCatalogService

O serviço mantém um catálogo completo de skills organizadas por área:

```python
TECH_SKILLS_CATALOG = {
    "engineering": {
        "backend": ["Python", "Java", "Node.js", "Go", "Ruby", "C#", ".NET"],
        "frontend": ["React", "Vue.js", "Angular", "TypeScript", "Next.js"],
        "devops": ["Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform"],
        "data": ["SQL", "PostgreSQL", "MongoDB", "Redis", "Spark", "Airflow"],
        "ai_ml": ["Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch"]
    },
    "finance": {
        "accounting": ["IFRS", "GAAP", "SAP FI/CO", "Contabilidade Geral"],
        "fp_a": ["Orçamento", "Forecast", "Power BI", "Excel Avançado"]
    },
    # ... outras áreas
}

BEHAVIORAL_COMPETENCIES_CATALOG = {
    "leadership": {
        "name": "Liderança",
        "subcategories": ["Liderança de Equipe", "Desenvolvimento de Pessoas", "Tomada de Decisão"]
    },
    "problem_solving": {
        "name": "Resolução de Problemas",
        "subcategories": ["Pensamento Analítico", "Pensamento Crítico", "Inovação"]
    },
    # ... outras competências
}
```

### 3.2. Mapeamento Cargo → Skills

```python
ROLE_SKILLS_MAPPING = {
    "desenvolvedor backend": {
        "area": "engineering", 
        "category": "backend", 
        "behavioral": ["problem_solving", "collaboration"]
    },
    "cientista de dados": {
        "area": "engineering", 
        "category": "ai_ml", 
        "behavioral": ["problem_solving", "communication"]
    },
    "tech lead": {
        "area": "engineering", 
        "category": "backend", 
        "behavioral": ["leadership", "communication"]
    }
}
```

### 3.3. Ajuste por Senioridade

O catálogo ajusta automaticamente a quantidade de skills esperada:

```python
SENIORITY_SKILL_COUNTS = {
    "junior": {"min": 3, "max": 5},
    "pleno": {"min": 5, "max": 8},
    "senior": {"min": 8, "max": 12},
    "lead": {"min": 10, "max": 15},
    "diretor": {"min": 10, "max": 15}
}
```

### 3.4. Fluxo de Sugestão de Skills

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUXO DE INFERÊNCIA DE SKILLS                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Recrutador informa: "Dev Python Sênior para Dados"          │
│     │                                                            │
│     ▼                                                            │
│  2. JobIntakeAgent extrai:                                       │
│     • cargo: "Desenvolvedor Python"                              │
│     • senioridade: "Sênior" (confiança: alta)                   │
│     • competencias_tecnicas: ["Python", "Dados"] (detectadas)   │
│     │                                                            │
│     ▼                                                            │
│  3. SkillsCatalogService consulta:                               │
│     • normalize_role("Dev Python") → "desenvolvedor backend"     │
│     • get_skills_for_role("desenvolvedor backend", "senior")    │
│     │                                                            │
│     ▼                                                            │
│  4. Catálogo retorna:                                            │
│     • Skills técnicas: Python, Java, Node.js, SQL, PostgreSQL   │
│     • Skills comportamentais: Resolução de Problemas, Colaboração│
│     • Quantidade esperada: 8-12 skills (sênior)                 │
│     │                                                            │
│     ▼                                                            │
│  5. Combinação com defaults da empresa:                          │
│     • Skills padrão do departamento Tecnologia                   │
│     • Competências comportamentais obrigatórias                 │
│     │                                                            │
│     ▼                                                            │
│  6. Resultado final:                                             │
│     ├── Detectadas: [Python, Dados] ← do texto                  │
│     ├── Sugeridas: [SQL, PostgreSQL, Docker, AWS] ← do catálogo │
│     └── Obrigatórias: [Ética, Colaboração] ← da empresa         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Análise de Compensação (Salário + Bônus + Benefícios)

### 4.1. CompensationAnalysisService

O serviço analisa a proposta de remuneração contra:

1. **Políticas internas da empresa** (CompensationPolicy)
2. **Benchmark de mercado** (MarketBenchmarkService)
3. **Histórico de vagas similares** (JobInsightsService)

```python
class CompensationAnalysisResult:
    salary_analysis: SalaryAnalysis
    bonus_analysis: BonusAnalysis
    benefits_analysis: BenefitAnalysis
    total_comp_analysis: TotalCompAnalysis
    
    overall_alignment: CompensationAlignmentStatus  # ALIGNED, BELOW_MARKET, ABOVE_POLICY
    alerts: List[str]
    recommendations: List[str]
    data_sources_used: List[DataSource]
```

### 4.2. Fluxo de Análise de Compensação

```
┌─────────────────────────────────────────────────────────────────┐
│              FLUXO DE ANÁLISE DE COMPENSAÇÃO                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT: Dev Python Sênior, São Paulo, Tecnologia                │
│         Proposta: R$ 15.000 - R$ 20.000                         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 1. POLÍTICA DA EMPRESA (CompensationPolicy)                 ││
│  │    └── Query: role_pattern="Python" + seniority="Sênior"   ││
│  │                                                              ││
│  │    Resultado:                                                ││
│  │    • salary_min: R$ 14.000                                   ││
│  │    • salary_max: R$ 22.000                                   ││
│  │    • bonus_target: 15%                                       ││
│  │    • Status: ✅ DENTRO DA POLÍTICA                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 2. BENCHMARK DE MERCADO (MarketBenchmarkService)            ││
│  │    └── Web search: "salário Python Sênior São Paulo 2026"  ││
│  │                                                              ││
│  │    Fontes consultadas:                                       ││
│  │    • glassdoor.com.br                                        ││
│  │    • linkedin.com                                            ││
│  │    • indeed.com.br                                           ││
│  │                                                              ││
│  │    Resultado:                                                ││
│  │    • Mediana: R$ 18.000                                      ││
│  │    • Percentil 25: R$ 14.000                                 ││
│  │    • Percentil 75: R$ 22.000                                 ││
│  │    • Tendência: "crescente"                                  ││
│  │    • Demanda: "alta"                                         ││
│  │    • Confiança: "medium"                                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 3. HISTÓRICO INTERNO (JobInsightsService)                   ││
│  │    └── Query: vagas similares últimos 12 meses              ││
│  │                                                              ││
│  │    Resultado (15 vagas analisadas):                          ││
│  │    • Média: R$ 16.500                                        ││
│  │    • Time-to-fill médio: 32 dias                            ││
│  │    • Taxa de preenchimento: 87%                              ││
│  │    • Trend: "estável"                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 4. ANÁLISE CONSOLIDADA                                       ││
│  │                                                              ││
│  │    ┌─ Salário ─────────────────────────────────────────────┐││
│  │    │ Proposto: R$ 15.000 - R$ 20.000                        │││
│  │    │ Política: ✅ Dentro (14k-22k)                          │││
│  │    │ Mercado: ✅ Alinhado (percentil 50)                    │││
│  │    │ Sugestão: Nenhuma alteração necessária                 │││
│  │    └────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │    ┌─ Bônus ───────────────────────────────────────────────┐││
│  │    │ Proposto: 10%                                          │││
│  │    │ Política: ⚠️ Abaixo do target (15%)                   │││
│  │    │ Sugestão: Aumentar para 15% ou justificar              │││
│  │    └────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │    ┌─ Benefícios ──────────────────────────────────────────┐││
│  │    │ Propostos: VR, VA, Plano de Saúde                      │││
│  │    │ Padrão empresa: VR, VA, PS, PO, Gympass, HO           │││
│  │    │ Faltando: Gympass, Auxílio Home Office                 │││
│  │    │ Valor anual benefícios: R$ 25.560                      │││
│  │    └────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │    ┌─ Total Compensation Anual ────────────────────────────┐││
│  │    │ Salário: R$ 204.000 (média * 12)                       │││
│  │    │ Bônus: R$ 20.400 (10% anual)                           │││
│  │    │ Benefícios: R$ 25.560                                   │││
│  │    │ TOTAL: R$ 249.960/ano                                   │││
│  │    │ Mercado (P50): R$ 280.000/ano                          │││
│  │    │ Status: ⚠️ 11% abaixo do mercado                       │││
│  │    └────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Parecer da LIA (EvaluationResponse)

O parecer é estruturado em um schema Pydantic completo:

```python
class EvaluationResponse(BaseModel):
    # Campos detectados do input
    detected_fields: Dict[str, Any]
    
    # Score de completude (0-100)
    completeness_score: float
    missing_critical_fields: List[str]
    missing_probable_fields: List[str]
    
    # Alinhamento com a empresa
    company_alignment: {
        "culture_match": 0.85,
        "skills_from_catalog": ["Python", "AWS", "Docker"],
        "suggested_benefits": ["VA", "VR", "Plano de Saúde"]
    }
    
    # Alinhamento com mercado
    market_alignment: {
        "salary_percentile": 75,
        "market_demand": "high",
        "competing_companies": 15
    }
    
    # Análise de compensação completa
    compensation_analysis: CompensationAnalysisResult
    
    # Sugestões personalizadas
    suggestions: [
        {
            "field": "salary_min",
            "suggested": 18000,
            "reason": "Baseado em dados de mercado para Python Sênior em SP",
            "source": "market_benchmark"
        }
    ]
    
    # Ação recomendada
    recommended_action: "proceed" | "review_compensation" | "missing_critical"
    overall_confidence: float  # 0-1
```

---

## 6. Como o Recrutador Aceita as Sugestões

### 6.1. Interface de Sugestões no Painel

```typescript
// Componente CriteriaDetectedPanel
interface Suggestion {
  field: string
  value: any
  reason: string
  source: 'detected' | 'catalog' | 'market' | 'company'
  confidence: 'high' | 'medium' | 'low'
  status: 'pending' | 'accepted' | 'rejected'
}

// O recrutador pode:
// 1. Aceitar individualmente clicando no ✓
// 2. Rejeitar individualmente clicando no ✗
// 3. Aceitar todas as sugestões
// 4. Editar manualmente o campo no painel
```

### 6.2. Padrão "LIA sugere, Recrutador confirma"

```
┌─────────────────────────────────────────────────────────────────┐
│               PADRÃO DE ACEITE DE SUGESTÕES                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ Skill Sugerida ──────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  💡 Docker                                                 │  │
│  │     Fonte: Catálogo de Skills (Engineering > DevOps)      │  │
│  │     Razão: 85% das vagas Dev Python Sênior incluem Docker │  │
│  │     Confiança: Alta                                        │  │
│  │                                                            │  │
│  │  [✓ Aceitar] [✗ Rejeitar] [📝 Editar Nível]              │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Alerta de Compensação ───────────────────────────────────┐  │
│  │                                                            │  │
│  │  ⚠️ Salário abaixo do mercado                             │  │
│  │     Proposto: R$ 15.000 - R$ 20.000                       │  │
│  │     Mercado (P50): R$ 18.000                               │  │
│  │     Sugestão: Considere R$ 16.000 - R$ 22.000             │  │
│  │                                                            │  │
│  │  [📊 Ver Dados] [✓ Aceitar Sugestão] [Manter Original]    │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3. Feedback Learning

Quando o recrutador aceita ou rejeita sugestões, o sistema aprende:

```python
class WizardFeedback:
    field: str               # Campo afetado
    original_value: Any      # Valor sugerido pela LIA
    corrected_value: Any     # Valor escolhido pelo recrutador
    action: str              # 'accepted' | 'rejected' | 'modified'
    context: Dict            # Contexto (cargo, senioridade, etc)
    
# FeedbackLearningService armazena e analisa padrões
# PatternDetectorService detecta correções recorrentes
# Próximas sugestões são ajustadas baseadas no histórico
```

### 6.4. Interação com Sugestões via Chat

O **SuggestionInteractionService** permite que o recrutador interaja com as sugestões através de linguagem natural via chat, oferecendo uma forma conversacional e ágil de aceitar, rejeitar, substituir ou ajustar sugestões da LIA.

#### 6.4.1. Comandos Suportados

O sistema detecta automaticamente intenções do recrutador através de padrões de linguagem natural:

| Intent | Exemplos de Comando | Ação | Resultado |
|--------|-------------------|------|-----------|
| **ACCEPT** | "pode adicionar Docker", "aceito a sugestão de Python", "confirma Python", "sim, Docker é bom" | Adiciona a skill/campo à vaga | Skill adicionada ao painel com status `accepted` |
| **REJECT** | "não preciso de Kubernetes", "remova SQL", "tira Docker da lista", "sem React" | Remove a skill/campo sugerido | Skill marcada como `rejected` no painel, não exibida novamente |
| **REPLACE** | "troque Docker por Podman", "prefiro Vue ao invés de React", "use PostgreSQL em vez de MongoDB" | Substitui um campo/skill por outro | Campo original removido, novo campo adicionado com reason "user_replacement" |
| **ADJUST_LEVEL** | "Docker como diferencial", "Python é obrigatório", "Kubernetes é nice-to-have" | Ajusta o nível de importância (required/nice-to-have/differentiator) | Skill mantida mas com novo nível de prioridade |
| **CLARIFY** | "por que você sugeriu Kubernetes?", "de onde vem esse salário?", "qual a fonte dessa sugestão?" | Solicita explicação sobre uma sugestão | Retorna reason + sources + confidence + dados de suporte |

#### 6.4.2. Intent Detection

O **SuggestionInteractionService** detecta intenções através de uma abordagem híbrida:

```python
class SuggestionInteractionService:
    """
    Serviço de interação com sugestões via chat
    """
    
    def detect_intent(self, user_message: str) -> IntentResult:
        """
        Detecta intenção usando:
        1. Regex patterns (fast path para comandos diretos)
        2. LLM classification (para linguagem natural complexa)
        3. Confidence scoring (compatibilidade com ConfidencePolicyService)
        """
        
        # Passo 1: Fast path - regex patterns
        patterns = {
            'ACCEPT': [
                r'(aceito|confirmo|pode|sim|ok|certo|bom|adiciona)\s*(a|de|que)?\s*(\w+)',
                r'(adiciona|coloca|inclui)\s*(docker|python|react|...)',
            ],
            'REJECT': [
                r'(não preciso|remova|tira|sem|não|remove)\s*(de\s+)?\s*(\w+)',
                r'(exclui|elimina|tira|remove)\s*(\w+)\s*(da\s+lista)?',
            ],
            'REPLACE': [
                r'(troque|muda|substitua|prefiro|use)\s*(\w+)\s+(por|em vez de|ao invés de)\s*(\w+)',
                r'(em vez de|ao invés de)\s*(\w+),?\s*(use|tente|prefiro)\s*(\w+)',
            ],
            'ADJUST_LEVEL': [
                r'(\w+)\s+(como|é)\s+(diferencial|obrigatório|nice-to-have|desejável)',
                r'(\w+)\s+(deve ser|é)\s+(nice-to-have|obrigatório|required)',
            ],
            'CLARIFY': [
                r'(por que|pq|qual|de onde)\s+(você|a lia)\s+(sugeriu|recomendou|propôs|vem)',
                r'(explica|entendo|de onde vem|qual a fonte|dados)',
            ]
        }
        
        # Passo 2: Extract patterns
        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    return IntentResult(
                        intent=intent,
                        confidence=0.85,  # regex patterns têm alta confiança
                        method="regex_pattern",
                        extracted_entities=match.groups()
                    )
        
        # Passo 3: LLM classification para linguagem natural complexa
        llm_result = self.llm_classifier.classify(
            message=user_message,
            context=self.get_conversation_context()
        )
        
        return IntentResult(
            intent=llm_result.intent,
            confidence=llm_result.confidence,
            method="llm_classification",
            explanation=llm_result.explanation
        )

class IntentResult:
    intent: str  # ACCEPT | REJECT | REPLACE | ADJUST_LEVEL | CLARIFY
    confidence: float  # 0-1
    method: str  # regex_pattern | llm_classification
    extracted_entities: List[str]  # Entidades extraídas (skills, campos, etc)
    explanation: Optional[str]  # Explicação do LLM se necessário
```

#### 6.4.3. Fluxo de Processamento

```
┌─────────────────────────────────────────────────────────────────────────┐
│           FLUXO DE INTERAÇÃO COM SUGESTÕES VIA CHAT                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INPUT: Mensagem do Recrutador                                          │
│  ──────────────────────────────────────────────────────────────────────  │
│  "Aceito a sugestão de Python, mas prefiro Golang ao invés de Java"    │
│                                                                          │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 1. INTENT DETECTION                                              │   │
│  │    └── SuggestionInteractionService.detect_intent()             │   │
│  │                                                                   │   │
│  │    ✓ Regex Pattern Matching (Fast Path):                        │   │
│  │      • "Aceito a sugestão de Python" → ACCEPT intent            │   │
│  │      • Extracted entity: "Python"                               │   │
│  │      • Confidence: 0.95 (regex pattern)                         │   │
│  │                                                                   │   │
│  │    ✓ LLM Secondary Classification:                               │   │
│  │      • "prefiro Golang ao invés de Java" → REPLACE intent       │   │
│  │      • Extracted entities: ["Java", "Golang"]                   │   │
│  │      • Confidence: 0.88 (LLM classification)                    │   │
│  │                                                                   │   │
│  │    Result: [                                                     │   │
│  │      IntentResult(ACCEPT, "Python", conf=0.95),                │   │
│  │      IntentResult(REPLACE, ["Java", "Golang"], conf=0.88)      │   │
│  │    ]                                                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 2. AÇÃO CORRESPONDENTE                                           │   │
│  │    └── SuggestionInteractionService.execute_action()            │   │
│  │                                                                   │   │
│  │    Processamento sequencial:                                     │   │
│  │                                                                   │   │
│  │    Action 1: ACCEPT("Python")                                   │   │
│  │    ├── Valida: Python está na lista de sugeridas? ✓             │   │
│  │    ├── Localiza: suggestion_id = "skill_python_123"             │   │
│  │    ├── Atualiza: status = "accepted"                            │   │
│  │    └── Log: action="accepted", timestamp, recruiter_id          │   │
│  │                                                                   │   │
│  │    Action 2: REPLACE(["Java", "Golang"])                        │   │
│  │    ├── Valida: Java está na lista de sugeridas? ✓               │   │
│  │    ├── Processa:                                                │   │
│  │    │   - status_old = "rejected"  (Java)                        │   │
│  │    │   - nova_skill = "Golang"                                  │   │
│  │    │   - reason = "user_replacement"                            │   │
│  │    │   - source = "recruiter_interaction"                       │   │
│  │    ├── Consulta: SkillsCatalogService.validate("Golang")       │   │
│  │    │   └── Result: Valid, categoria="backend", confidence=high  │   │
│  │    └── Log: action="replaced", from="Java", to="Golang"        │   │
│  │                                                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 3. ATUALIZAÇÃO DO PAINEL DE SUGESTÕES                            │   │
│  │    └── CriteriaDetectedPanel.update_suggestions()               │   │
│  │                                                                   │   │
│  │    Estado ANTES:                                                 │   │
│  │    ├── ✅ Python (detectada) - pending review                   │   │
│  │    ├── 💡 Java (sugerida) - pending review                      │   │
│  │    └── 💡 Docker (sugerida) - pending review                    │   │
│  │                                                                   │   │
│  │    Atualização:                                                  │   │
│  │    • Python: pending → accepted ✓                               │   │
│  │    • Java: pending → rejected ✗                                 │   │
│  │    • Golang: add novo (substituição de Java)                    │   │
│  │                                                                   │   │
│  │    Estado DEPOIS:                                                │   │
│  │    ├── ✅ Python (aceita) - accepted                            │   │
│  │    ├── ✅ Golang (nova substituição) - accepted                 │   │
│  │    └── 💡 Docker (sugerida) - pending review                    │   │
│  │                                                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 4. CONFIRMAÇÃO DA LIA                                            │   │
│  │    └── LIA Chat Agent responde ao recrutador                    │   │
│  │                                                                   │   │
│  │    Mensagem de Confirmação:                                      │   │
│  │    ───────────────────────────────────────────────────────────    │   │
│  │    "Perfeito! Atualizei suas sugestões:                         │   │
│  │                                                                   │   │
│  │    ✅ Python - Confirmado como skill obrigatória                │   │
│  │    ✅ Golang - Adicionado em substituição ao Java               │   │
│  │    ──────────────────────────────────────────────────            │   │
│  │                                                                   │   │
│  │    Qualquer outra alteração que deseja fazer?"                  │   │
│  │                                                                   │   │
│  │    Data Log:                                                     │   │
│  │    • skill_changes: 3 (Python accept, Java reject, Golang add)  │   │
│  │    • total_time: 2.3s                                            │   │
│  │    • confidence: 0.91 (média ponderada)                         │   │
│  │                                                                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 6.4.4. Exemplos de Conversa

##### Exemplo 1: Aceitar e Ajustar Sugestões

```
[Painel de Sugestões Inicial]
💡 Docker (sugerida)
💡 Kubernetes (sugerida)
💡 AWS (sugerida)

RECRUTADOR: "Ok, Docker e AWS vou aceitar, mas Kubernetes é só um diferencial"

LIA: Perfeito! Atualizei:
✅ Docker - skill obrigatória
✅ AWS - skill obrigatória  
🎯 Kubernetes - marcado como diferencial (nice-to-have)

Quer adicionar mais algo?

RECRUTADOR: "Sim, adiciona Git e CI/CD também"

LIA: Adicionei Git e CI/CD como skills obrigatórias, alinhado com o catálogo 
de DevOps. Sua vaga agora tem 8 skills técnicas (dentro do esperado para 
sênior em DevOps).

[Painel Atualizado]
✅ Docker (obrigatória)
✅ AWS (obrigatória)
✅ Git (obrigatória)
✅ CI/CD (obrigatória)
🎯 Kubernetes (diferencial)
```

##### Exemplo 2: Substituir Tecnologias

```
[Sugestões Iniciais]
💡 React (sugerida)
💡 TypeScript (sugerida)
💡 Next.js (sugerida)

RECRUTADOR: "Preferimos Vue ao invés de React, e podemos trocar TypeScript 
por JavaScript vanilla?"

LIA: Entendi. Fazendo as substituições:
✅ React → Vue adicionado
   • Vue tem 92% de compatibilidade no catálogo frontend
   • 78% dos times frontend da empresa já usam Vue
   • Atualizei a sugestão de skills correlatas

⚠️ JavaScript vanilla → TypeScript
   • TypeScript é recomendado para projetos enterprise
   • Confiança: média (0.72) porque JavaScript puro é menos comum em 
     vagas sênior em 2026
   
   Quer manter a alteração mesmo assim?

RECRUTADOR: "Sim, pode manter JavaScript vanilla"

LIA: Alterado! Atualizei as sugestões de skills comportamentais também 
para manter alinhamento com a escolha tecnológica.
```

##### Exemplo 3: Esclarecer Dados de Sugestão

```
[Chat durante análise de compensação]

RECRUTADOR: "Por que vocês sugerem R$ 20.000 de salário mínimo? 
Parece alto"

LIA: Ótima pergunta! Deixa eu explicar os dados:

📊 Faixa Sugerida: R$ 18.000 - R$ 22.000

Fundamentação:
├─ Política da empresa (Python Sênior SP): R$ 14k - R$ 22k
├─ Mercado (Glassdoor + LinkedIn, 145 vagas analisadas):
│  ├─ Percentil 25: R$ 16.500
│  ├─ Mediana: R$ 19.500
│  └─ Percentil 75: R$ 23.000
├─ Histórico interno (últimos 12 meses): R$ 18.200 (média)
└─ Demanda de mercado: ⬆️ Crescente (+8% vs ano anterior)

Recomendação: R$ 20k garante competitividade (P50 do mercado)

RECRUTADOR: "Ok, faz sentido. Vou com R$ 19.000 como mínimo então"

LIA: Anotado! R$ 19.000 está no percentil 45, ainda muito competitivo.
Isso pode ajudar com time-to-fill mais rápido. 👍
```

---

## 7. Adição de Novas Informações na Dinâmica

### 7.1. Fluxo de Atualização em Tempo Real

```
┌─────────────────────────────────────────────────────────────────┐
│            ATUALIZAÇÃO DINÂMICA DURANTE O WIZARD                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Etapa 1: Input]                                                │
│       │                                                          │
│       │ Recrutador digita: "Preciso de um Dev Python Sênior"    │
│       │                                                          │
│       ▼                                                          │
│  [Detecção automática]                                           │
│       │                                                          │
│       ├── Detectado: cargo="Dev Python", senioridade="Sênior"   │
│       │                                                          │
│       ├── Triggera: SkillsCatalogService.suggest_skills()       │
│       │   └── Adiciona: Python, SQL, Docker ao painel           │
│       │                                                          │
│       ├── Triggera: CompensationAnalysisService.analyze()       │
│       │   └── Adiciona: Faixa sugerida R$ 14k-22k              │
│       │                                                          │
│       └── Triggera: CompanyConfigService.get_defaults()         │
│           └── Adiciona: Benefícios padrão da empresa            │
│                                                                  │
│  [Etapa 2: Job Description]                                      │
│       │                                                          │
│       │ Recrutador adiciona: "experiência com AWS e Kubernetes" │
│       │                                                          │
│       ▼                                                          │
│  [Re-análise incremental]                                        │
│       │                                                          │
│       ├── Novas skills detectadas: AWS, Kubernetes              │
│       │                                                          │
│       ├── Catálogo expande sugestões:                           │
│       │   └── Adiciona: Terraform, CI/CD, Docker Swarm          │
│       │                                                          │
│       └── Market benchmark atualiza:                             │
│           └── DevOps skills aumentam faixa sugerida em 10%      │
│                                                                  │
│  [Etapa 3: Competências]                                         │
│       │                                                          │
│       │ Recrutador confirma skills e ajusta pesos               │
│       │                                                          │
│       ▼                                                          │
│  [WSI Questions geradas]                                         │
│       │                                                          │
│       └── Perguntas de triagem baseadas nas competências        │
│           selecionadas com metodologia CBI + Dreyfus + Bloom    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Serviços Integrados (Resumo)

| Serviço | Responsabilidade | Dados de Entrada | Dados de Saída |
|---------|------------------|------------------|----------------|
| **IntelligenceLayerService** | Orquestração de padrões e correlações | company_id, role, seniority | Sugestões, insights, predições |
| **SkillsCatalogService** | Catálogo de skills técnicas/comportamentais | role, seniority | Lista de skills sugeridas |
| **CompensationAnalysisService** | Análise de salário/bônus/benefícios | job_title, seniority, proposed_salary | CompensationAnalysisResult |
| **MarketBenchmarkService** | Benchmark de mercado via web search | role, location | Faixa salarial, tendências |
| **JobInsightsService** | Histórico de vagas da empresa | company_id, role | Médias, time-to-fill, skills comuns |
| **CompanyConfigurationService** | Defaults e políticas da empresa | company_id | Benefícios, policies, templates |
| **RecruiterPersonalizationService** | Personalização por recrutador | recruiter_id | Ajustes, preferências |
| **ConfidencePolicyService** | Cálculo de confiança | field, sources | Confidence score, action |
| **FeedbackLearningService** | Aprendizado com correções | feedback_data | Padrões detectados |

---

## 9. Diagrama Completo do Wizard de 7 Etapas

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    WIZARD DE CRIAÇÃO DE VAGA - 7 ETAPAS                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  FASE 1: CONSTRUÇÃO                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                          │ │
│  │  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐     │ │
│  │  │ 1. Input & │──▶│ 2. Job     │──▶│ 3. Compe-  │──▶│ 4. Remune- │     │ │
│  │  │ Evaluation │   │ Description│   │ tências    │   │ ração      │     │ │
│  │  └────────────┘   └────────────┘   └────────────┘   └────────────┘     │ │
│  │        │                                                  │              │ │
│  │        ▼                                                  ▼              │ │
│  │  ┌─────────────┐                                  ┌─────────────┐       │ │
│  │  │ Compensation│◄─────────────────────────────────│ Total Comp  │       │ │
│  │  │ Analysis    │                                  │ Preview     │       │ │
│  │  │ Panel       │                                  └─────────────┘       │ │
│  │  └─────────────┘                                                        │ │
│  │                                                                          │ │
│  │  ┌────────────┐                                                         │ │
│  │  │ 5. WSI     │                                                         │ │
│  │  │ Questions  │                                                         │ │
│  │  └────────────┘                                                         │ │
│  │                                                                          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                          │                                    │
│                                          ▼                                    │
│  FASE 2: ATIVAÇÃO                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  ┌────────────────┐                                                     │ │
│  │  │ 6. Review &    │──▶ Publicação em LinkedIn, Indeed, Site Carreiras  │ │
│  │  │ Publish        │                                                     │ │
│  │  └────────────────┘                                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                          │                                    │
│                                          ▼                                    │
│  FASE 3: SELEÇÃO                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  ┌────────────────┐                                                     │ │
│  │  │ 7. Search &    │──▶ Busca Pearch AI + Calibração + Pipeline         │ │
│  │  │ Calibration    │                                                     │ │
│  │  └────────────────┘                                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Arquivos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `lia-agent-system/app/agents/specialized/job_intake_agent.py` | Agente principal de criação de vagas |
| `lia-agent-system/app/services/skills_catalog_service.py` | Catálogo de skills e competências |
| `lia-agent-system/app/services/compensation_analysis_service.py` | Análise de compensação |
| `lia-agent-system/app/services/market_benchmark_service.py` | Benchmark de mercado via web |
| `lia-agent-system/app/services/job_insights_service.py` | Insights de vagas históricas |
| `lia-agent-system/app/services/intelligence_layer_service.py` | Camada de inteligência |
| `lia-agent-system/app/schemas/job_evaluation.py` | Schema do parecer (EvaluationResponse) |
| `docs/FLUXO_WIZARD_VAGA_COMPLETO.md` | Documentação completa do wizard |
