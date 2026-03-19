# Plano de Implementação: Aprimoramento do Wizard de Criação de Vagas

> **Versão**: 7.2 (Orquestração Inteligente)  
> **Data**: Fevereiro 2026  
> **Status**: Em Produção  
> **Última Atualização**: 04 de Fevereiro de 2026  
> **Documentos Consolidados**: FLUXO_WIZARD_VAGA_COMPLETO.md, LIA_PROACTIVE_ANALYSIS_SYSTEM.md, SETTINGS_MENU_MAPPING_FOR_WIZARD.md (v3.0), TAXONOMIA_TEMPLATES.md  
> **Arquitetura de Agentes**: v2.2 (9 agentes ativos)

---

## Índice Geral

### PARTE 1: VISÃO GERAL E CONTEXTO
1. [Resumo Executivo](#1-resumo-executivo)
2. [Status de Implementação](#2-status-de-implementação)
3. [Métricas de Sucesso](#3-métricas-de-sucesso)
4. [Arquitetura Alto Nível](#4-arquitetura-alto-nível)

### PARTE 2: MODELO DE DADOS E ESTRUTURAS
5. [Tipologia de Campos](#5-tipologia-de-campos)
6. [JobDraft - Estado Intermediário](#6-jobdraft---estado-intermediário)
7. [Níveis de Confiança](#7-níveis-de-confiança)
8. [Catálogo de Skills e Competências](#8-catálogo-de-skills-e-competências)
9. [Mapeamento de Configurações da Empresa](#9-mapeamento-de-configurações-da-empresa)

### PARTE 3: WIZARD DE CRIAÇÃO DE VAGAS
10. [Estrutura do Wizard (3 Fases, 6 Etapas)](#10-estrutura-do-wizard-3-fases-6-etapas)
11. [Modos de Criação (Completo vs Fast Track)](#11-modos-de-criação-completo-vs-fast-track)
12. [Fast Track e Templates Curados](#12-fast-track-e-templates-curados)
13. [Sistema de Geração de Job Description](#13-sistema-de-geração-de-job-description)
14. [Sistema de Análise Proativa da LIA](#14-sistema-de-análise-proativa-da-lia)
15. [Fluxos Conversacionais Detalhados](#15-fluxos-conversacionais-detalhados)

### PARTE 4: LEARNING LOOP
16. [Visão Geral do Learning Loop](#16-visão-geral-do-learning-loop)
17. [Intelligence Layer - Camada Centralizada](#17-intelligence-layer---camada-centralizada)
18. [Personalização por Recrutador](#18-personalização-por-recrutador)
19. [Feedback Learning e Loop de Aprendizagem](#19-feedback-learning-e-loop-de-aprendizagem)
20. [Fase 1B: Importação de JDs do ATS](#20-fase-1b-importação-de-jds-do-ats)

### PARTE 5: ARQUITETURA TÉCNICA
21. [Arquitetura Multi-Agente (9 agentes)](#21-arquitetura-multi-agente-9-agentes)
22. [Sistema de Prompts](#22-sistema-de-prompts)
23. [Integrações LLM e Provedores de IA](#23-integrações-llm-e-provedores-de-ia)
24. [Integrações ATS/HRIS](#24-integrações-atshris)
25. [Cache e Otimização de Tokens](#25-cache-e-otimização-de-tokens)
26. [Serviços Principais (173+)](#26-serviços-principais-173)
27. [Arquivos Críticos para Reconstrução](#27-arquivos-críticos-para-reconstrução)

### APÊNDICES
A. [Sistema de Interação com Sugestões via Chat](#a-sistema-de-interação-com-sugestões-via-chat)
B. [Histórico de Mudanças](#b-histórico-de-mudanças)

---

# PARTE 1: VISÃO GERAL E CONTEXTO

---

## 1. Resumo Executivo

### 1.1 Objetivo

Transformar o wizard de criação de vagas da LIA em um sistema inteligente que:
- **Reduz tempo de criação**: De 15 minutos para 3 minutos (80% de economia)
- **Aprende com histórico**: Precisão de sugestões evolui de 60% para 92%
- **Usa múltiplas fontes de dados**: 6 camadas priorizadas (Company Settings → LIA History → ATS Import → Workforce Planning → ETL → Templates)
- **Oferece dois modos**: Completo (6 etapas) e Fast Track (2 etapas)

### 1.2 Princípios Orientadores

| Princípio | Descrição |
|-----------|-----------|
| **1. Company Settings First** | Configurações da empresa têm prioridade máxima (100% precisão) |
| **2. LIA sugere, recrutador confirma** | IA nunca decide sozinha, sempre oferece sugestões |
| **3. Fast Track com Learning** | Vagas similares ficam mais rápidas com o tempo |
| **4. Transparência de origem** | Todo campo mostra sua fonte (settings, histórico, template, IA) |
| **5. Fallback inteligente** | Se não há dados, usa templates curados como base |

### 1.3 Números Chave (Atualizados)

| Métrica | Valor |
|---------|-------|
| **Templates Curados** | 361 |
| **Categorias** | 10 |
| **Agentes Especializados** | 9 (v2.2) |
| **Tools Registrados** | 26+ (inclui 3 novas inteligentes) |
| **Services** | 177+ |
| **Endpoints API** | 142+ |
| **Etapas do Wizard** | 6 (3 fases) |
| **Integrações ATS** | 4 (Gupy, Pandapé, StackOne, Merge) |

---

## 2. Status de Implementação

### 2.1 Integrações de IA Completas
- ✅ Anthropic Claude (primary - Sonnet 3.5/4)
- ✅ OpenAI GPT-4 (fallback + vision)
- ✅ Google Gemini (vision/multimodal)
- ✅ Deepgram (STT - Speech to Text)
- ✅ Pearch AI (sourcing de candidatos)

### 2.2 Integrações ATS/HRIS Completas
- ✅ Gupy (API nativa brasileira)
- ✅ Pandapé (API nativa brasileira)
- ✅ StackOne (universal - 50+ ATS)
- ✅ Merge (universal - 200+ ATS/HRIS)

### 2.3 Funcionalidades Concluídas
- ✅ Wizard 3 Fases, 6 Etapas (estrutura atualizada)
- ✅ JobDraft com histórico de mudanças
- ✅ Sistema de confiança determinístico
- ✅ Intelligence Layer centralizado
- ✅ Personalização por recrutador
- ✅ Templates curados (361 templates, 10 categorias)
- ✅ Learning Loop Fase 1B (endpoints operacionais)
- ✅ Frontend integration (hooks, types, components)
- ✅ Arquitetura multi-agente v2.2 (9 agentes)
- ✅ Super Chat (fullscreen mode)
- ✅ Feedback Loop System (thumbs up/down, ratings)
- ✅ WSI Integration (perguntas de triagem)
- ✅ Search Calibration (etapa 6)

### 2.4 Em Desenvolvimento
- 🔄 Clustering e embeddings (próxima fase)
- 🔄 Importação em massa de JDs do ATS
- 🔄 Fine-tuning data export
- 🔄 Real-time voice integration aprimorada

---

## 3. Métricas de Sucesso

| Métrica | Baseline | Meta | Status |
|---------|----------|------|--------|
| Tempo de criação (modo completo) | 15 min | 8 min | ✅ |
| Tempo de criação (fast track) | 15 min | 3 min | ✅ |
| Precisão de sugestões (inicial) | 0% | 60% | ✅ |
| Precisão de sugestões (após 10 vagas) | 60% | 85% | ✅ |
| Precisão de sugestões (após 50 vagas) | 85% | 92% | 🔄 |
| Taxa de aceitação de sugestões | - | > 70% | ✅ |
| Cobertura de skills automáticas | 0% | > 80% | ✅ |

---

## 4. Arquitetura Alto Nível

### 4.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PLATAFORMA LIA v2.2                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   FRONTEND      │    │   BACKEND       │    │   AI LAYER      │             │
│  │   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (LangGraph)   │             │
│  │                 │    │                 │    │                 │             │
│  │  • Wizard UI    │    │  • 142 endpoints│    │  • 9 agentes    │             │
│  │  • Settings Hub │    │  • 173+ services│    │  • 23+ tools    │             │
│  │  • Chat Panel   │    │  • Learning Loop│    │  • Orchestrator │             │
│  │  • Super Chat   │    │  • ATS Clients  │    │  • Task Planner │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│           │                      │                      │                       │
│           └──────────────────────┼──────────────────────┘                       │
│                                  │                                              │
│                    ┌─────────────▼─────────────┐                               │
│                    │      INTELLIGENCE         │                               │
│                    │         LAYER             │                               │
│                    │                           │                               │
│                    │  • Pattern Detection      │                               │
│                    │  • Confidence Scoring     │                               │
│                    │  • Learning Hub           │                               │
│                    │  • Recruiter Profiles     │                               │
│                    └───────────────────────────┘                               │
│                                  │                                              │
│           ┌──────────────────────┼──────────────────────┐                       │
│           │                      │                      │                       │
│  ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐              │
│  │   PostgreSQL    │   │   ATS/HRIS      │   │   LLM APIs      │              │
│  │   (Neon)        │   │   Integrations  │   │   (Claude/GPT)  │              │
│  │                 │   │                 │   │                 │              │
│  │  • JobDraft     │   │  • Gupy         │   │  • Anthropic    │              │
│  │  • Patterns     │   │  • Pandapé      │   │  • OpenAI       │              │
│  │  • Feedback     │   │  • StackOne     │   │  • Gemini       │              │
│  │  • Skills       │   │  • Merge        │   │  • Deepgram     │              │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Fluxo de Dados do Wizard

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FLUXO DE CRIAÇÃO DE VAGA                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  RECRUTADOR                    LIA                           DADOS              │
│  ───────────                   ───                           ─────              │
│       │                         │                              │                │
│       │  "Criar vaga Dev Sr"    │                              │                │
│       │────────────────────────►│                              │                │
│       │                         │  Busca configurações ───────►│                │
│       │                         │◄────────────────────── (100%)│ Company Settings│
│       │                         │                              │                │
│       │                         │  Busca histórico LIA ───────►│                │
│       │                         │◄────────────────────── (95%) │ LIA History    │
│       │                         │                              │                │
│       │                         │  Busca JDs do ATS ──────────►│                │
│       │                         │◄────────────────────── (85%) │ Gupy/Pandapé   │
│       │                         │                              │                │
│       │                         │  Busca templates ───────────►│                │
│       │                         │◄────────────────────── (70%) │ 361 Templates  │
│       │                         │                              │                │
│       │  Sugestões + Painel     │                              │                │
│       │◄────────────────────────│                              │                │
│       │                         │                              │                │
│       │  Confirma/Ajusta        │                              │                │
│       │────────────────────────►│                              │                │
│       │                         │  Salva aprendizado ─────────►│                │
│       │                         │                              │                │
│       │  Vaga publicada! ✅      │                              │                │
│       │◄────────────────────────│  Sync ATS ─────────────────►│ IntegradorATS  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# PARTE 2: MODELO DE DADOS E ESTRUTURAS

---

## 5. Tipologia de Campos

### 5.1 Categorização de Campos

```python
class FieldTypology(Enum):
    COMPANY_DATA = "company_data"      # Dados da empresa (settings) - 100%
    HISTORICAL = "historical"           # Dados históricos LIA (vagas anteriores) - 95%
    ATS_IMPORT = "ats_import"           # JDs importados via API ATS - 85%
    MARKET_BENCHMARK = "market_benchmark"  # Dados de mercado - 80%
    TEMPLATE = "template"               # De template curado - 70%
    AI_INFERRED = "ai_inferred"         # Inferido por IA - 60%
    USER_INPUT = "user_input"           # Input direto do usuário - 100%
```

### 5.1.1 Hierarquia de Fontes de Dados

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      HIERARQUIA DE FONTES DE DADOS                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  PRECISÃO 100% ─────► USER_INPUT / COMPANY_DATA                                 │
│       │               Configurações da empresa + input direto                   │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 95% ──────► HISTORICAL                                                │
│       │               Histórico de vagas criadas na LIA                         │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 85% ──────► ATS_IMPORT                                                │
│       │               JDs importados via Gupy, Pandapé, StackOne, Merge         │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 80% ──────► MARKET_BENCHMARK                                          │
│       │               Dados de mercado, pesquisas salariais                     │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 70% ──────► TEMPLATE                                                  │
│       │               361 templates curados (fallback)                          │
│       │                                                                          │
│       ▼                                                                          │
│  PRECISÃO 60% ──────► AI_INFERRED                                               │
│                       Inferido por IA quando não há outras fontes               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Campos por Etapa do Wizard

| Etapa | Campos Críticos | Fonte Primária | Fontes Secundárias |
|-------|-----------------|----------------|-------------------|
| **1. Input & Evaluation** | cargo, senioridade, modelo_trabalho, localização | COMPANY_DATA | HISTORICAL, ATS_IMPORT, TEMPLATE |
| **2. Remuneração** | faixa_salarial, bônus, benefícios | MARKET_BENCHMARK | ATS_IMPORT, HISTORICAL, COMPANY_DATA |
| **3. Competências** | skills_tecnicas, competencias_comportamentais, idiomas | HISTORICAL | ATS_IMPORT, COMPANY_DATA, TEMPLATE |
| **4. Perguntas WSI** | perguntas_triagem, perguntas_eliminatórias | TEMPLATE | ATS_IMPORT, HISTORICAL, AI_INFERRED |
| **5. Revisão e Publicação** | descricao_completa, canais_publicação | AI_INFERRED | ATS_IMPORT, COMPANY_DATA, USER_INPUT |
| **6. Busca e Calibração** | cutoffs, preferencias, filtros | HISTORICAL | ATS_IMPORT, USER_INPUT |

### 5.3 Impacto das Fontes por Etapa

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 FONTES DE DADOS POR ETAPA DO WIZARD                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Etapa                    Company  Historical  ATS     Template  AI            │
│                           Settings LIA         Import  Curado    Inferred      │
│  ──────────────────────── ──────── ────────── ─────── ──────── ──────          │
│  1. Input & Evaluation    ████████ ██████     █████   ███      ██              │
│  2. Remuneração           ████     ███████    ██████  ██       ███             │
│  3. Competências          ██████   ████████   ██████  ████     ██              │
│  4. Perguntas WSI         ██       ██████     █████   ███████  ████            │
│  5. Revisão e Publicação  █████    ████       █████   ██       ██████          │
│  6. Busca e Calibração    ██       ████████   ██████  █        ███             │
│                                                                                  │
│  Legenda: ████████ = Alta influência    ██ = Baixa influência                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. JobDraft - Estado Intermediário

### 6.1 Modelo de Dados

```python
class JobDraft(Base):
    __tablename__ = "job_drafts"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    recruiter_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # Estado do wizard
    current_stage = Column(String, default="input-evaluation")
    is_fast_track = Column(Boolean, default=False)
    template_id = Column(String, nullable=True)
    
    # Dados da vaga (JSON estruturado)
    job_data = Column(JSONB, default={})
    
    # Metadados de campos
    field_sources = Column(JSONB, default={})  # {field: source_type}
    field_confidence = Column(JSONB, default={})  # {field: confidence_score}
    
    # Histórico
    history = Column(JSONB, default=[])  # Lista de mudanças
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String, default="draft")  # draft, reviewing, published, archived
```

### 6.2 Histórico de Mudanças

```python
class JobDraftChange(TypedDict):
    timestamp: str
    field: str
    old_value: Any
    new_value: Any
    source: str  # user, lia, system
    stage: str
    reason: Optional[str]
```

---

## 7. Níveis de Confiança

### 7.1 Escala de Confiança

| Nível | Score | Fonte | Comportamento |
|-------|-------|-------|---------------|
| **Máximo** | 100% | Company Settings | Auto-preenche, não pede confirmação |
| **Alto** | 95% | Histórico LIA (>3 vagas) | Auto-preenche, badge visual |
| **Médio** | 85% | ATS Import / Workforce | Sugere, pede confirmação leve |
| **Baixo** | 70% | Template curado | Sugere, pede confirmação explícita |
| **Inferido** | 50-60% | IA / LLM | Sugere com explicação, pede confirmação |

### 7.2 Política de Confiança

```python
class ConfidencePolicy:
    def calculate_confidence(self, field: str, sources: List[DataSource]) -> float:
        weights = {
            "company_settings": 1.0,
            "lia_history": 0.95,
            "ats_import": 0.85,
            "workforce_planning": 0.80,
            "etl": 0.75,
            "template": 0.70,
            "ai_inferred": 0.60
        }
        
        if not sources:
            return 0.0
        
        # Usa a fonte de maior peso
        max_weight = max(weights.get(s.type, 0.5) for s in sources)
        
        # Bonus se múltiplas fontes concordam
        if len(sources) > 1:
            max_weight = min(1.0, max_weight + 0.05)
        
        return max_weight
```

---

## 8. Catálogo de Skills e Competências

### 8.1 Estrutura do Catálogo

```python
class SkillCatalog:
    # Skills técnicas globais
    global_technical_skills: List[TechnicalSkill]
    
    # Skills por empresa (personalizadas)
    company_skills: Dict[UUID, List[TechnicalSkill]]
    
    # Competências comportamentais
    behavioral_competencies: List[BehavioralCompetency]
    
    # Mapeamento skill → competência
    skill_competency_mapping: Dict[str, List[str]]

class TechnicalSkill(BaseModel):
    id: str
    name: str
    category: str  # language, framework, database, tool, methodology
    level: str  # basic, intermediate, advanced
    aliases: List[str]  # React, ReactJS, React.js
    related_skills: List[str]
    weight: int  # 1-5

class BehavioralCompetency(BaseModel):
    id: str
    name: str
    description: str
    indicators: List[str]
    questions: List[str]  # Perguntas sugeridas
    weight: int  # 1-5
```

### 8.2 Skills Dinâmicas (Learning)

```python
class CompanySkill(Base):
    """Skills aprendidas pela LIA para cada empresa"""
    __tablename__ = "company_skills"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    skill_name = Column(String)
    skill_normalized = Column(String)  # Lowercase, sem acentos
    category = Column(String)
    usage_count = Column(Integer, default=1)
    last_used_at = Column(DateTime)
    promoted_to_catalog = Column(Boolean, default=False)  # Após 3 usos
```

---

## 9. Mapeamento de Configurações da Empresa

### 9.1 Fontes de Dados (Prioridade)

| Prioridade | Fonte | Precisão | Componente |
|------------|-------|----------|------------|
| 1 | Company Settings | 100% | CompanyTeamHub, RecruitmentHub |
| 2 | Histórico LIA | 95% | LearningHub |
| 3 | JDs Importados ATS | 85% | IntegradorATSAgent |
| 4 | Workforce Planning | 80% | PlanningHub |
| 5 | ETL Completo | 75% | DataIngestionService |
| 6 | Templates Curados | 70% | TemplateService |

### 9.2 Mapeamento Detalhado

Para mapeamento completo, consultar: `docs/SETTINGS_MENU_MAPPING_FOR_WIZARD.md` (v3.0)

---

# PARTE 3: WIZARD DE CRIAÇÃO DE VAGAS

---

## 10. Estrutura do Wizard (3 Fases, 6 Etapas)

### 10.1 Visão Geral das Fases

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    WIZARD DE CRIAÇÃO DE VAGAS - 3 FASES                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        FASE 1: CONSTRUÇÃO                                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │   Etapa 1   │  │   Etapa 2   │  │   Etapa 3   │  │   Etapa 4   │      │  │
│  │  │   Input &   │──│ Remuneração │──│Competências │──│  Perguntas  │      │  │
│  │  │  Evaluation │  │   (Salary)  │  │  (Skills)   │  │    WSI      │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                         │
│                                        ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        FASE 2: ATIVAÇÃO                                   │  │
│  │                    ┌─────────────────────┐                                │  │
│  │                    │      Etapa 5        │                                │  │
│  │                    │   Revisão &         │                                │  │
│  │                    │   Publicação        │                                │  │
│  │                    └─────────────────────┘                                │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                         │
│                                        ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        FASE 3: SELEÇÃO                                    │  │
│  │                    ┌─────────────────────┐                                │  │
│  │                    │      Etapa 6        │                                │  │
│  │                    │   Busca &           │                 [OPCIONAL]     │  │
│  │                    │   Calibração        │                                │  │
│  │                    └─────────────────────┘                                │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Detalhamento das Etapas

| Etapa | ID | Fase | Agente Principal | Descrição |
|-------|-----|------|------------------|-----------|
| 1 | `input-evaluation` | Construção | JobIntakeAgent | Cargo, senioridade, modelo, localização, responsabilidades |
| 2 | `salary` | Construção | JobIntakeAgent | Faixa salarial, bônus, benefícios por senioridade |
| 3 | `competencies` | Construção | JobIntakeAgent | Skills técnicas, competências comportamentais, Big Five |
| 4 | `wsi-questions` | Construção | JobIntakeAgent | Perguntas de triagem WSI, eliminatórias |
| 5 | `review-publish` | Ativação | JobIntakeAgent + IntegradorATS | Revisão final, publicação em canais |
| 6 | `search-calibration` | Seleção | SourcingAgent | Busca de candidatos, calibração de cutoffs |

### 10.2.1 Fontes de Dados por Etapa

Cada etapa utiliza múltiplas fontes de dados para pré-preencher e sugerir campos:

| Etapa | Fontes Primárias | Fontes Secundárias | Impacto ATS |
|-------|------------------|-------------------|-------------|
| **1. Input & Evaluation** | Company Settings, Histórico LIA | ATS Import, Templates | JDs do ATS sugerem cargo e modelo |
| **2. Remuneração** | Market Benchmark, Histórico LIA | ATS Import, Company Data | Faixas salariais de vagas ATS similares |
| **3. Competências** | Histórico LIA, Company Tech Stack | ATS Import, Templates | Skills extraídas de JDs importados |
| **4. Perguntas WSI** | Templates, Histórico LIA | ATS Import, AI Inferred | Perguntas de vagas ATS anteriores |
| **5. Revisão e Publicação** | AI Inferred, Company Data | ATS Import, User Input | Sync bidirecional com ATS |
| **6. Busca e Calibração** | Histórico LIA, User Input | ATS Import | Candidatos importados do ATS |

**Benefícios da Integração ATS em cada etapa:**
- **Etapa 1-4**: JDs importados enriquecem sugestões automaticamente
- **Etapa 5**: Publicação sincroniza com ATS configurado (Gupy, Pandapé, etc.)
- **Etapa 6**: Pool de candidatos pode incluir candidatos do ATS

### 10.3 Configuração das Etapas (TypeScript)

```typescript
export type WizardStage = 
  | 'input-evaluation' 
  | 'salary' 
  | 'competencies' 
  | 'wsi-questions' 
  | 'review-publish' 
  | 'search-calibration'

export type WizardPhase = 'construction' | 'activation' | 'selection'

export const WIZARD_PHASES: WizardPhaseConfig[] = [
  { 
    id: 'construction', 
    label: 'Construção', 
    stages: ['input-evaluation', 'salary', 'competencies', 'wsi-questions'] 
  },
  { 
    id: 'activation', 
    label: 'Ativação', 
    stages: ['review-publish'] 
  },
  { 
    id: 'selection', 
    label: 'Seleção', 
    stages: ['search-calibration'] 
  }
]
```

### 10.4 Skip Calibration

A etapa 6 (Busca e Calibração) é **opcional** e pode ser pulada:

- **Quando pular**: Vagas urgentes, pool de candidatos existente, recrutamento interno
- **Economia de tempo**: 10-15 minutos
- **Configuração**: `skipCalibration: true` no JobDraft

---

## 11. Modos de Criação (Completo vs Fast Track)

### 11.1 Fontes de Dados Compartilhadas

**Ambos os modos** (Completo e Fast Track) utilizam as mesmas fontes de dados inteligentes para acelerar o processo:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    FONTES DE DADOS PARA AMBOS OS MODOS                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  1. CONFIGURAÇÕES DA EMPRESA (100% precisão)                             │   │
│  │     • Menu Configurações → CompanyTeamHub                                │   │
│  │     • Cultura, valores, tech stack, benefícios                           │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                                        ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  2. HISTÓRICO LIA + JDs IMPORTADOS DO ATS (85-95% precisão)              │   │
│  │     • Vagas anteriores criadas na LIA                                    │   │
│  │     • JDs importados via API: Gupy, Pandapé, StackOne, Merge             │   │
│  │     • Padrões de skills, salários, benefícios por cargo                  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                                        ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  3. TEMPLATES CURADOS (70% precisão - fallback)                          │   │
│  │     • 361 templates em 10 categorias                                     │   │
│  │     • Qualidade garantida (WSI Gates)                                    │   │
│  │     • Usado quando não há histórico específico                           │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Fonte de Dados | Modo Completo | Fast Track | Precisão |
|----------------|---------------|------------|----------|
| Company Settings | ✅ Auto-preenche | ✅ Auto-preenche | 100% |
| Histórico LIA | ✅ Sugere em cada etapa | ✅ Preenche automaticamente | 95% |
| JDs do ATS (API) | ✅ Sugere padrões detectados | ✅ Base para templates dinâmicos | 85% |
| Templates Curados | ✅ Fallback inteligente | ✅ Seleção direta | 70% |

### 11.2 Modo Completo (6 Etapas)

- **Duração**: ~8 minutos
- **Etapas**: Todas as 6 etapas
- **Uso**: Vagas novas, cargos inéditos, requisitos específicos
- **LIA**: Análise proativa em cada etapa
- **Fontes de Dados**: 
  - Usa **todas as fontes** para sugestões inteligentes
  - JDs do ATS enriquecem sugestões de skills e salários
  - Templates servem como fallback quando não há histórico

### 11.3 Fast Track (2 Etapas)

- **Duração**: ~3 minutos
- **Etapas**: Seleção de base → Revisão e ajustes
- **Uso**: Vagas recorrentes, templates existentes, reuso de JDs
- **LIA**: Preenche automaticamente, pede confirmação única
- **Fontes de Dados**:
  - Prioriza **JDs importados do ATS** como base
  - Usa **histórico LIA** para vagas similares
  - **Templates curados** como opção de seleção direta

### 11.4 Benefícios da Integração ATS

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    INTEGRAÇÃO ATS → ACELERAÇÃO DO WIZARD                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────┐     ┌─────────────────────────┐     ┌─────────────────────┐   │
│  │ ATS Cliente │────►│  IntegradorATSAgent     │────►│   Learning Hub      │   │
│  │             │     │  (Ag.8)                 │     │                     │   │
│  │ • Gupy     │     │  • Parse JDs            │     │  • Extrai padrões   │   │
│  │ • Pandapé  │     │  • Normaliza campos     │     │  • Skills frequentes│   │
│  │ • StackOne │     │  • Mapeia taxonomia     │     │  • Faixas salariais │   │
│  │ • Merge    │     │                         │     │  • Benefícios       │   │
│  └─────────────┘     └─────────────────────────┘     └──────────┬──────────┘   │
│                                                                  │              │
│                                                                  ▼              │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         WIZARD (Ambos os Modos)                         │   │
│  │  • Modo Completo: Sugestões enriquecidas por etapa                      │   │
│  │  • Fast Track: JD do ATS como base pré-preenchida                       │   │
│  │  • Resultado: Criação 80% mais rápida                                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Fluxo de Decisão

```
┌────────────────────────────────────────────────────────────────┐
│                   PRÉ-WIZARD INTELLIGENCE                      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Recrutador: "Preciso criar uma vaga de Dev Sênior"            │
│                          │                                      │
│                          ▼                                      │
│  ┌────────────────────────────────────────────┐                │
│  │  LIA analisa histórico da empresa          │                │
│  │  • Encontrou 5 vagas similares? ──────────►│ FAST TRACK     │
│  │  • Sem histórico? ────────────────────────►│ MODO COMPLETO  │
│  └────────────────────────────────────────────┘                │
│                          │                                      │
│                          ▼                                      │
│  LIA: "Encontrei uma vaga 'Dev Sênior React' criada há 2       │
│        meses. Quer usar ela como base? Vai ser bem mais        │
│        rápido! 🚀"                                              │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 12. Fast Track e Templates Curados

### 12.1 Templates Curados (361 templates)

| Categoria | Quantidade | Subcategorias |
|-----------|------------|---------------|
| **tecnologia** | 119 | desenvolvimento, dados, infra, seguranca, design, gestao, arquitetura, qualidade, produto |
| **comercial/vendas** | 98 | inside_sales, field_sales, customer_success, gestao, canais, vendas_tecnicas, ecommerce, sales_ops |
| **operacoes** | 34 | logistica, supply_chain, compras, qualidade, comex, gestao |
| **rh** | 32 | recrutamento, business_partner, dp, remuneracao, td, desenvolvimento, cultura, gestao |
| **administrativo** | 21 | geral, secretariado, facilities, compras, documentacao, patrimonio, gestao |
| **financas** | 19 | contabilidade, fiscal, controladoria, planejamento, tesouraria, auditoria, gestao |
| **customer_success** | 17 | cs_management, onboarding, success_ops |
| **saude** | 13 | enfermagem, medicina, terapias, farmacia, gestao |
| **marketing** | 8 | digital, conteudo, branding, performance, growth, gestao |

### 12.2 Qualidade dos Templates (WSI Gates)

Todos os 361 templates atendem aos critérios WSI:
- ✅ Mínimo 5 skills técnicas com níveis
- ✅ Mínimo 3 competências comportamentais com justificativas
- ✅ Mínimo 5 responsabilidades

### 12.3 Arquivos de Templates

```
lia-agent-system/app/data/
├── curated_templates_tech.py       # 119 templates
├── curated_templates_vendas.py     # 98 templates
├── curated_templates_rh.py         # 32 templates
├── curated_templates_administrativo.py  # 21 templates
├── curated_templates_financas.py   # 19 templates
├── curated_templates_operacoes.py  # 14 templates
├── curated_templates_saude.py      # 13 templates
├── curated_templates_marketing.py  # 8 templates
└── curated_templates_cs.py         # 2 templates
```

---

## 13. Sistema de Geração de Job Description

### 13.1 Pipeline de Geração

```
┌────────────────────────────────────────────────────────────────┐
│                   JD GENERATION PIPELINE                       │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. COLETA DE DADOS                                            │
│     ├── Company Settings (missão, valores, cultura)            │
│     ├── Job Data (cargo, requisitos, responsabilidades)        │
│     └── Market Data (benchmark, tendências)                    │
│                                                                 │
│  2. ESTRUTURAÇÃO                                               │
│     ├── Título atrativo                                        │
│     ├── Sobre a empresa (EVP)                                  │
│     ├── Desafio do cargo                                       │
│     ├── Responsabilidades (bullet points)                      │
│     ├── Requisitos (obrigatórios vs desejáveis)                │
│     ├── Benefícios (por senioridade)                           │
│     └── Call to action                                         │
│                                                                 │
│  3. OTIMIZAÇÃO                                                 │
│     ├── SEO para job boards                                    │
│     ├── Linguagem inclusiva (D&I)                              │
│     ├── Tom da marca                                           │
│     └── Keywords estratégicas                                  │
│                                                                 │
│  4. REVISÃO                                                    │
│     ├── Compliance check                                       │
│     ├── Bias detection                                         │
│     └── Readability score                                      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 13.2 Serviço de Geração

```python
class JDTemplateService:
    async def generate_job_description(
        self,
        job_draft: JobDraft,
        company_data: CompanyData,
        style: str = "formal"  # formal, casual, tech, creative
    ) -> GeneratedJD:
        
        # 1. Prepara contexto
        context = self._build_context(job_draft, company_data)
        
        # 2. Chama LLM com prompt estruturado
        response = await self.llm_client.generate(
            prompt=self._get_jd_prompt(context, style),
            model="claude-sonnet-4-20250514",
            max_tokens=2000
        )
        
        # 3. Pós-processamento
        jd = self._parse_response(response)
        jd = self._apply_compliance_checks(jd)
        jd = self._detect_bias(jd)
        
        return jd
```

---

## 14. Sistema de Análise Proativa da LIA

### 14.1 Triggers de Análise Proativa

| Trigger | Ação da LIA | Exemplo |
|---------|-------------|---------|
| **Campo preenchido** | Analisa consistência | "Você mencionou React, mas não TypeScript. Adiciono?" |
| **Mudança de etapa** | Resume e valida | "Perfeito! Vamos agora definir a remuneração..." |
| **Inconsistência detectada** | Alerta gentil | "O salário está abaixo do mercado para Sênior. Quer ajustar?" |
| **Oportunidade de melhoria** | Sugere | "Baseado no histórico, 80% das suas vagas usam 'trabalho híbrido'..." |
| **Tempo inativo** | Oferece ajuda | "Posso ajudar com algo? Estou aqui para isso!" |

### 14.2 Tipos de Insights

```python
class InsightType(Enum):
    MARKET_BENCHMARK = "market_benchmark"   # Comparação com mercado
    HISTORICAL_PATTERN = "historical_pattern"  # Padrões da empresa
    CONSISTENCY_CHECK = "consistency_check"    # Validação de dados
    OPTIMIZATION_TIP = "optimization_tip"      # Dicas de otimização
    COMPLIANCE_ALERT = "compliance_alert"      # Alertas de compliance
```

---

## 15. Fluxos Conversacionais Detalhados

### 15.1 Filosofia de UX

**"Chat é a interface principal, painéis são apoio visual"**

- LIA faz perguntas naturais, não lista de opções
- Usuário responde em linguagem natural
- Tom consultivo e empático
- Múltiplas perguntas podem ser respondidas de uma vez

### 15.2 Estrutura Visual

```
┌────────────────────────────────────────────────────────────────┐
│ HEADER: Etapas do Wizard (Construção → Ativação → Seleção)    │
├──────────────────────────┬─────────────────────────────────────┤
│                          │                                     │
│   CHAT CONVERSACIONAL    │   PAINEL LATERAL                    │
│   (Input + Mensagens)    │   (Formulários + Preview)           │
│                          │                                     │
│   LIA conversa aqui      │   Dados estruturados aqui           │
│   Usuário responde aqui  │   Edições rápidas aqui              │
│                          │   Botões de ação aqui               │
│                          │                                     │
└──────────────────────────┴─────────────────────────────────────┘
```

### 15.3 Padrão de Interação

```
LIA: "Olá! Vamos criar essa vaga juntos. Me conta mais sobre o cargo que você precisa."

Usuário: "Preciso de um dev fullstack sênior, remoto, com React e Node"

LIA: "Entendi! Já identifiquei:
      ✓ Cargo: Desenvolvedor Fullstack
      ✓ Senioridade: Sênior
      ✓ Modelo: Remoto
      ✓ Skills: React, Node.js

      Baseado no seu histórico, 80% das vagas similares também pedem:
      • TypeScript (95% das vagas)
      • PostgreSQL (78% das vagas)
      
      Adiciono essas skills? 🎯"

Usuário: "Sim, pode adicionar"

LIA: "Pronto! Veja no painel ao lado os requisitos atualizados.
      Agora vamos para a remuneração. Qual a faixa salarial?"
```

---

# PARTE 4: LEARNING LOOP

---

## 16. Visão Geral do Learning Loop

### 16.1 Ciclo de Aprendizagem

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LEARNING LOOP - CICLO                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────┐    ┌─────────────┐    ┌─────────┐    ┌───────────┐               │
│   │ CONSUMO │───►│PROCESSAMENTO│───►│ ANÁLISE │───►│ PREDIÇÃO  │               │
│   └────┬────┘    └─────────────┘    └─────────┘    └─────┬─────┘               │
│        │                                                  │                     │
│        │              ┌──────────────────────┐           │                     │
│        │              │                      │           │                     │
│        │              ▼                      │           ▼                     │
│        │         ┌─────────┐            ┌────┴────┐                            │
│        │         │FEEDBACK │◄───────────│ SUGESTÃO│                            │
│        │         └────┬────┘            └─────────┘                            │
│        │              │                                                         │
│        │              ▼                                                         │
│        │         ┌──────────┐                                                  │
│        └────────►│APRENDIZADO│                                                 │
│                  └──────────┘                                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 16.2 Fontes de Dados (Prioridade)

| # | Fonte | Precisão | Descrição |
|---|-------|----------|-----------|
| 1 | Company Settings | 100% | Configurações no Menu Configurações |
| 2 | Histórico LIA | 95% | Vagas criadas anteriormente na LIA |
| 3 | JDs Importados ATS | 85% | Gupy, Pandapé, StackOne, Merge |
| 4 | Workforce Planning | 80% | Planos de contratação |
| 5 | ETL Completo | 75% | Extração de sistemas externos |
| 6 | Templates Curados | 70% | 361 templates (fallback) |

---

## 17. Intelligence Layer - Camada Centralizada

### 17.1 Métodos Implementados

```python
class IntelligenceLayerService:
    """Camada centralizada de inteligência para o wizard"""
    
    # Métodos Públicos (implementados em lia-agent-system/app/services/intelligence_layer_service.py)
    
    async def assess_data_quality(self, tenant_id: UUID, job_draft: JobDraft) -> DataQualityReport:
        """Avalia qualidade dos dados do draft"""
        
    async def build_intelligence_context(self, tenant_id: UUID, job_draft: JobDraft) -> IntelligenceContext:
        """Constrói contexto completo para sugestões (Company Settings + ATS + Templates)"""
        
    def apply_pattern_adjustment(self, field: str, value: Any, patterns: List[Pattern]) -> AdjustedValue:
        """Aplica ajustes baseados em padrões detectados"""
        
    def generate_field_suggestion(self, field: str, context: IntelligenceContext) -> FieldSuggestion:
        """Gera sugestão para um campo específico com fonte e confiança"""
        
    async def log_insight(self, tenant_id: UUID, insight: Insight) -> None:
        """Registra insight para aprendizado"""
        
    async def record_insight_outcome(self, insight_id: UUID, outcome: str) -> None:
        """Registra resultado do insight (aceito/rejeitado)"""
        
    async def refresh_patterns(self, tenant_id: UUID) -> PatternRefreshResult:
        """Atualiza padrões da empresa com base em novos dados (ATS + LIA History)"""
        
    async def get_wizard_enhancements(self, tenant_id: UUID, stage: WizardStage) -> WizardEnhancements:
        """Obtém melhorias específicas para cada etapa do wizard"""
    
    # Métodos Privados
    async def _is_cache_expired(self, cache_key: str) -> bool:
        """Verifica se cache expirou"""
        
    async def _ensure_patterns_detected(self, tenant_id: UUID) -> List[Pattern]:
        """Garante que padrões foram detectados"""
        
    async def _ensure_correlations_analyzed(self, tenant_id: UUID) -> List[Correlation]:
        """Garante que correlações foram analisadas"""
        
    def _generate_reasoning(self, suggestion: FieldSuggestion) -> str:
        """Gera explicação para a sugestão"""
```

### 17.2 Fluxo de Sugestões

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     INTELLIGENCE LAYER - FLUXO DE SUGESTÕES                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐                                                            │
│  │  Wizard Stage   │───► build_intelligence_context()                           │
│  │  (Requisição)   │                    │                                        │
│  └─────────────────┘                    ▼                                        │
│                          ┌──────────────────────────────────┐                   │
│                          │      COLETA DE FONTES            │                   │
│                          │  ┌────────────┐ ┌────────────┐   │                   │
│                          │  │  Company   │ │ Historical │   │                   │
│                          │  │  Settings  │ │    LIA     │   │                   │
│                          │  └────────────┘ └────────────┘   │                   │
│                          │  ┌────────────┐ ┌────────────┐   │                   │
│                          │  │    ATS     │ │  Templates │   │                   │
│                          │  │   Import   │ │   Curados  │   │                   │
│                          │  └────────────┘ └────────────┘   │                   │
│                          └──────────────────────────────────┘                   │
│                                          │                                       │
│                                          ▼                                       │
│                          ┌──────────────────────────────────┐                   │
│                          │      PROCESSAMENTO               │                   │
│                          │  • assess_data_quality()         │                   │
│                          │  • refresh_patterns()            │                   │
│                          │  • apply_pattern_adjustment()    │                   │
│                          └──────────────────────────────────┘                   │
│                                          │                                       │
│                                          ▼                                       │
│                          ┌──────────────────────────────────┐                   │
│                          │      GERAÇÃO DE SUGESTÕES        │                   │
│                          │  • generate_field_suggestion()   │                   │
│                          │  • get_wizard_enhancements()     │                   │
│                          └──────────────────────────────────┘                   │
│                                          │                                       │
│                                          ▼                                       │
│  ┌─────────────────┐    ┌──────────────────────────────────┐                   │
│  │   Wizard UI     │◄───│      RESPOSTA COM SUGESTÕES      │                   │
│  │  (Exibe para    │    │  • Campos pré-preenchidos        │                   │
│  │   recrutador)   │    │  • Fonte de cada campo           │                   │
│  └─────────────────┘    │  • Confiança (%)                 │                   │
│         │               │  • Reasoning (explicação)        │                   │
│         │               └──────────────────────────────────┘                   │
│         │                                                                        │
│         ▼                                                                        │
│  ┌─────────────────┐                                                            │
│  │  Feedback do    │───► log_insight() + record_insight_outcome()               │
│  │  Recrutador     │     (Alimenta Learning Loop)                               │
│  └─────────────────┘                                                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 17.3 Responsabilidades Originais
        suggestions = await self._generate_suggestions(patterns, confidence)
        
        return suggestions
```

### 17.2 Padrões Detectados

```python
class PatternType(Enum):
    SALARY_PATTERN = "salary_pattern"           # Padrões salariais
    SKILL_PATTERN = "skill_pattern"             # Skills recorrentes
    BENEFIT_PATTERN = "benefit_pattern"         # Benefícios por senioridade
    WORK_MODEL_PATTERN = "work_model_pattern"   # Modelo de trabalho preferido
    HIRING_VELOCITY = "hiring_velocity"         # Velocidade de contratação
    SUCCESS_PROFILE = "success_profile"         # Perfil de sucesso
```

---

## 18. Personalização por Recrutador

### 18.1 Perfil do Recrutador

```python
class RecruiterProfile(Base):
    __tablename__ = "recruiter_profiles"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    
    # Preferências de interface
    preferred_communication_style = Column(String)  # formal, casual, brief
    preferred_language = Column(String, default="pt-BR")
    
    # Padrões observados
    avg_time_per_stage = Column(JSONB, default={})  # {stage: seconds}
    most_used_templates = Column(JSONB, default=[])
    preferred_skills = Column(JSONB, default=[])
    
    # Configurações
    skip_calibration_default = Column(Boolean, default=False)
    auto_publish_channels = Column(JSONB, default=[])
    
    # Métricas
    jobs_created = Column(Integer, default=0)
    fast_track_usage_rate = Column(Float, default=0.0)
    avg_suggestion_acceptance = Column(Float, default=0.0)
```

### 18.2 Personalização em Ação

```python
async def personalize_suggestions(
    self,
    recruiter_id: UUID,
    base_suggestions: List[Suggestion]
) -> List[Suggestion]:
    
    profile = await self.get_profile(recruiter_id)
    
    # Reordena sugestões baseado no histórico do recrutador
    for suggestion in base_suggestions:
        if suggestion.skill in profile.preferred_skills:
            suggestion.boost_score(0.1)  # +10% de relevância
        
        if suggestion.acceptance_rate_for_recruiter(recruiter_id) > 0.8:
            suggestion.boost_score(0.15)  # +15% se aceita frequentemente
    
    return sorted(base_suggestions, key=lambda s: s.score, reverse=True)
```

---

## 19. Feedback Learning e Loop de Aprendizagem

### 19.1 Tipos de Feedback

| Tipo | Capture Point | Dados Coletados |
|------|---------------|-----------------|
| **Thumbs up/down** | Cada sugestão | Aceitação/rejeição |
| **Rating (1-5)** | Fim de cada etapa | Satisfação |
| **Correção** | Edição de campo | Valor original vs correção |
| **Tempo** | Automático | Tempo por etapa |
| **Abandono** | Wizard incompleto | Etapa de abandono |

### 19.2 Modelo de Aprendizado

```python
class LearningPattern(Base):
    __tablename__ = "learning_patterns"
    
    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"))
    
    # Contexto
    pattern_type = Column(String)  # skill, salary, benefit, etc.
    job_category = Column(String)
    seniority_level = Column(String)
    
    # Padrão aprendido
    pattern_data = Column(JSONB)
    confidence_score = Column(Float)
    sample_size = Column(Integer)
    
    # Métricas
    acceptance_rate = Column(Float)
    correction_rate = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime)
    last_updated_at = Column(DateTime)
```

---

## 20. Fase 1B: Importação de JDs do ATS

### 20.1 Fluxo de Importação

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        IMPORTAÇÃO DE JDs DO ATS                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────┐    ┌─────────────────┐    ┌──────────────────┐                   │
│  │   ATS    │    │  IntegradorATS  │    │   JD Parser      │                   │
│  │  (Gupy)  │───►│     Agent       │───►│   Service        │                   │
│  └──────────┘    └────────┬────────┘    └────────┬─────────┘                   │
│                           │                       │                             │
│                           ▼                       ▼                             │
│                  ┌─────────────────────────────────────────┐                   │
│                  │          NORMALIZAÇÃO                   │                   │
│                  │  • Extrai cargo, skills, requisitos     │                   │
│                  │  • Mapeia para taxonomia LIA            │                   │
│                  │  • Calcula confiança (85%)              │                   │
│                  └─────────────────────────────────────────┘                   │
│                                    │                                            │
│                                    ▼                                            │
│                  ┌─────────────────────────────────────────┐                   │
│                  │           LEARNING HUB                  │                   │
│                  │  • Armazena padrões extraídos           │                   │
│                  │  • Enriquece sugestões futuras          │                   │
│                  └─────────────────────────────────────────┘                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 20.2 Parsers Implementados

```python
class JDParserService:
    """Parsing e extração de Job Descriptions"""
    
    parsers = {
        "gupy": GupyJDParser(),
        "pandape": PandapeJDParser(),
        "stackone": StackOneJDParser(),
        "merge": MergeJDParser()
    }
    
    async def parse_jd(
        self,
        raw_jd: str,
        source: str,
        metadata: dict
    ) -> ParsedJD:
        parser = self.parsers.get(source)
        if not parser:
            parser = self.parsers["generic"]
        
        return await parser.parse(raw_jd, metadata)
```

---

# PARTE 5: ARQUITETURA TÉCNICA

---

## 21. Arquitetura Multi-Agente (9 agentes)

### 21.1 Visão Geral

A plataforma LIA utiliza uma arquitetura multi-agente com **9 agentes ativos** baseada no WeDOTalent Multi-Agent Architecture v2.2.

### 21.2 Diagrama de Agentes

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA MULTI-AGENTE LIA v2.2                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                    ORCHESTRATOR (Ag.0)                                   │   │
│  │         Roteamento, Memória, Delegação, Coordenação                      │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│    ┌───────────────────────────────────┼───────────────────────────────────┐    │
│    ▼                   ▼               ▼               ▼                   ▼    │
│  ┌────────┐  ┌────────────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Ag.1   │  │    Ag.2        │  │   Ag.3   │  │    Ag.4     │  │   Ag.5     │ │
│  │ Job    │  │   Sourcing     │  │ Triagem  │  │Entrevistador│  │ Avaliador  │ │
│  │Intake  │  │   Agent        │  │Curricular│  │  WSI Voice  │  │    WSI     │ │
│  └────────┘  └────────────────┘  └──────────┘  └─────────────┘  └────────────┘ │
│                                                                                  │
│  ┌────────┐  ┌────────────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Ag.6   │  │    Ag.7        │  │   Ag.8   │  │    Ag.9     │  │ Especial   │ │
│  │Schedu- │  │   Analista     │  │Integrador│  │   Task      │  │ Recruiter  │ │
│  │ ling   │  │   Feedback     │  │   ATS    │  │  Planner    │  │ Assistant  │ │
│  └────────┘  └────────────────┘  └──────────┘  └─────────────┘  └────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 21.3 Tabela de Agentes

| ID | Agente | Classe | Responsabilidades |
|----|--------|--------|-------------------|
| Ag.0 | Orchestrator | `Orchestrator` | Roteamento, memória, delegação |
| Ag.1 | JobIntakeAgent | `job_intake_agent.py` | Wizard de vagas (etapas 1-5) |
| Ag.2 | SourcingAgent | `sourcing_agent.py` | Busca de candidatos, Pearch AI |
| Ag.3 | TriagemCurricularAgent | `triagem_curricular_agent.py` | Parsing de CV, triagem inicial |
| Ag.4 | EntrevistadorAgent | `entrevistador_agent.py` | Entrevistas WhatsApp/Voice |
| Ag.5 | AvaliadorWSIAgent | `avaliador_wsi_agent.py` | Avaliação científica WSI |
| Ag.6 | SchedulingAgent | `scheduling_agent.py` | Agendamento (Microsoft Graph) |
| Ag.7 | AnalistaFeedbackAgent | `analista_feedback_agent.py` | KPIs, relatórios, comunicação |
| Ag.8 | IntegradorATSAgent | `integrador_ats_agent.py` | Sync ATS (Gupy, Pandapé, etc.) |
| Ag.9 | TaskPlannerAgent | `task_planner_agent.py` | Decomposição de tarefas, DAG |
| Esp. | RecruiterAssistantAgent | `recruiter_assistant_agent.py` | Briefing diário, assistência |

### 21.4 Agentes Legados (Deprecated)

| Agente | Substituição | Status |
|--------|--------------|--------|
| ScreeningAgent | TriagemCurricular + Entrevistador + AvaliadorWSI | Deprecated |
| CommunicationAgent | AnalistaFeedbackAgent | Deprecated |
| AnalyticsAgent | AnalistaFeedbackAgent | Deprecated |

---

## 22. Sistema de Prompts

### 22.1 Arquitetura de Prompts

```
lia-agent-system/app/agents/prompts/
├── __init__.py              # Exports públicos
├── agent_prompts.py         # 1568 linhas - Definições dos prompts
├── prompt_registry.py       # 497 linhas - Sistema de versionamento
├── README.md                # 430 linhas - Guia completo de criação
└── examples/
    ├── __init__.py
    ├── orchestrator_examples.py
    ├── job_planner_examples.py
    ├── sourcing_examples.py
    └── pipeline_examples.py
```

### 22.2 Prompts Registrados (11 constantes)

| # | Constante | Agente | Linha |
|---|-----------|--------|-------|
| 0 | `ORCHESTRATOR_PROMPT` | Orquestrador Central | 251 |
| 1 | `JOB_PLANNER_PROMPT` | Job Intake Agent | 325 |
| 2 | `SOURCING_PROMPT` | Sourcing Agent | 447 |
| 3 | `CV_SCREENING_PROMPT` | Triagem Curricular | 569 |
| 4 | `INTERVIEWER_PROMPT` | Entrevistador WSI | 719 |
| 5 | `WSI_EVALUATOR_PROMPT` | Avaliador WSI | 854 |
| 6 | `SCHEDULING_PROMPT` | Scheduling Agent | 1017 |
| 7 | `ANALYST_FEEDBACK_PROMPT` | Analista Feedback | 1141 |
| 8 | `ATS_INTEGRATOR_PROMPT` | Integrador ATS | 1277 |
| 9 | `RECRUITER_ASSISTANT_PROMPT` | Assistente Recrutador | 1375 |
| 10 | `PROACTIVE_INSIGHTS_PROMPT` | Insights Proativos | 1467 |

### 22.3 Componentes Compartilhados

```python
# Persona LIA unificada (incluída em todos os prompts)
LIA_PERSONA = """
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e proativo
- **Linguagem**: Formal mas acessível, sem gírias ou abreviações
- **Tratamento**: Sempre "você", nunca "vc" ou "tu"
"""

# Vocabulário técnico de RH brasileiro
HR_VOCABULARY = """
## Vocabulário Técnico de RH Brasileiro

### Processo Seletivo
| Termo | Definição |
|-------|-----------|
| Funil de contratação | Representação visual das etapas do processo seletivo |
| Pipeline de talentos | Conjunto de candidatos em diferentes fases do processo |
| Shortlist | Lista reduzida de candidatos finalistas |
...
"""

# Diretrizes éticas (para agentes de avaliação)
ETHICAL_GUIDELINES = """
## Diretrizes Éticas
...
"""

# Diretrizes de persistência de dados
DATA_PERSISTENCE_GUIDELINES = """
## Persistência de Dados (OBRIGATÓRIO)
Ao [ação principal], SEMPRE:
1. **Persistir no WedoTalent**
2. **Sincronizar com ATS** (se configurado)
3. **Registrar histórico**
"""
```

### 22.4 Registry com Versionamento

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PromptVersion:
    version: str          # Versão semântica (X.Y.Z)
    content: str          # Conteúdo do prompt
    created_at: datetime  # Data de criação
    author: str           # Autor da versão
    changelog: str        # Descrição das mudanças

class PromptRegistry:
    """Registro centralizado de prompts com versionamento."""
    
    def register_prompt(
        self,
        name: str,              # snake_case
        content: str,           # Conteúdo do prompt
        version: str = "1.0.0", # Versão semântica
        author: str = "system",
        changelog: str = "Initial version",
        description: str = "",
        agent_number: Optional[int] = None
    ) -> None:
        """Registra nova versão de prompt."""
    
    def get_prompt(
        self,
        name: str,
        version: Optional[str] = None  # None = latest
    ) -> str:
        """Obtém prompt por nome e versão."""
    
    def list_versions(self, name: str) -> List[PromptVersion]:
        """Lista todas as versões de um prompt."""
    
    def compare_versions(
        self,
        name: str,
        version_a: str,
        version_b: str
    ) -> List[str]:
        """Compara duas versões (diff)."""
```

### 22.5 Estrutura Padrão de Prompt

Todo prompt de agente segue esta estrutura obrigatória:

```python
AGENT_NAME_PROMPT = f"""{LIA_PERSONA}

{ETHICAL_GUIDELINES}  # Se aplicável

Você é o Agente [N] da LIA - [Nome do Agente].

## Sua Identidade
- Nome: [Nome]
- Papel: [Descrição do papel]
- Expertise: [Áreas de especialização]

## Vocabulário Esperado nas Respostas
Use naturalmente estes termos técnicos de RH:
- **[Categoria]**: [termos]

## Suas Responsabilidades
- [Responsabilidade 1]
- [Responsabilidade 2]

## Persistência de Dados (OBRIGATÓRIO)
Ao [ação principal], SEMPRE:
1. **[Ação de persistência 1]**
2. **[Ação de persistência 2]**

### Dados a Persistir:
| Dado | Campo WedoTalent | Sync ATS |
|------|------------------|----------|
| [dado] | [campo] | Sim/Não |

## Formato de Resposta Estruturada
[Emoji] **[Título]**
**[Seção 1]**
[Conteúdo]

💾 **Persistência**
- [Status de persistência]

## Contexto Atual
{{context}}"""
```

---

## 23. Integrações LLM e Provedores de IA

### 23.1 Provedores Configurados

| Provedor | Modelos | Uso Principal |
|----------|---------|---------------|
| **Anthropic** | Claude Sonnet 4, Opus 4 | Agentes principais, wizard |
| **OpenAI** | GPT-4o, GPT-4 Vision | Fallback, análise de imagens |
| **Google** | Gemini Pro, Gemini Vision | Multimodal, análise de documentos |
| **Deepgram** | Nova-2 | Speech-to-Text |
| **Pearch AI** | Search API | Sourcing de candidatos |

### 23.2 Configuração de Fallback

```python
class LLMConfig:
    primary_provider = "anthropic"
    primary_model = "claude-sonnet-4-20250514"
    
    fallback_chain = [
        ("openai", "gpt-4o"),
        ("anthropic", "claude-3-5-sonnet-20241022"),
        ("google", "gemini-1.5-pro")
    ]
    
    vision_provider = "openai"
    vision_model = "gpt-4o"
    
    stt_provider = "deepgram"
    stt_model = "nova-2"
```

---

## 24. Integrações ATS/HRIS

### 24.1 Provedores Implementados

| Provedor | Tipo | Cobertura | Arquivo |
|----------|------|-----------|---------|
| **Gupy** | Nativo | Brasil | `ats_clients/gupy.py` |
| **Pandapé** | Nativo | Brasil | `ats_clients/pandape.py` |
| **StackOne** | Universal | 50+ ATS | `ats_clients/stackone.py` |
| **Merge** | Universal | 200+ ATS/HRIS | `ats_clients/merge.py` |

### 24.2 Funcionalidades de Sync

```python
class ATSClient(ABC):
    """Interface base para clientes ATS"""
    
    @abstractmethod
    async def sync_jobs(self) -> List[Job]:
        """Sincroniza vagas do ATS"""
        pass
    
    @abstractmethod
    async def sync_candidates(self, job_id: str) -> List[Candidate]:
        """Sincroniza candidatos do ATS"""
        pass
    
    @abstractmethod
    async def update_status(self, candidate_id: str, status: str) -> bool:
        """Atualiza status do candidato no ATS"""
        pass
    
    @abstractmethod
    async def publish_job(self, job: Job) -> str:
        """Publica vaga no ATS"""
        pass
```

---

## 25. Cache e Otimização de Tokens

### 25.1 Arquitetura de Cache em 3 Camadas (Token Economy)

O sistema implementa uma arquitetura de cache em 3 camadas para economizar tokens de LLM e acelerar respostas:

```
┌─────────────────────────────────────────────────────────────────┐
│                   TOKEN ECONOMY ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   LAYER 1    │    │   LAYER 2    │    │   LAYER 3    │       │
│  │   Session    │ →  │    Redis     │ →  │  PostgreSQL  │       │
│  │   (1 hour)   │    │  (7 days)    │    │  (30 days)   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│   In-memory          Short TTL           Long TTL               │
│   Per conversation   Volatile data       Stable patterns        │
│   Acesso instantâneo Fallback gracioso   Padrões consolidados   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Camada | TTL | Dados | Uso |
|--------|-----|-------|-----|
| **L1: SessionCache** | 1 hora | Contexto de conversa atual | Acesso instantâneo, sem I/O |
| **L2: RedisCache** | 7 dias | Sugestões, market data | Dados voláteis, fallback se indisponível |
| **L3: PostgresCache** | 30 dias | Padrões consolidados, embeddings | Dados estáveis, learning patterns |

**Componentes Implementados:**
- `CacheManagerService` (`cache_manager_service.py`): Orquestra as 3 camadas
- `SessionCache`: Cache em memória por sessão de conversa
- `CacheEntry` (model): Persistência L3 com hit tracking
- `QueryEmbedding` (model): Similaridade semântica para cache hits

### 25.2 Orquestração Inteligente de Dados (IntelligentDataOrchestrator)

O `IntelligentDataOrchestrator` consolida dados de **5 fontes** com priorização baseada em confiança:

```
┌─────────────────────────────────────────────────────────────────┐
│                   DATA SOURCE PRIORITY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PRIORITY 1: Learning Patterns ───────── VERY_HIGH (95%)        │
│              (Preferências históricas da empresa)                │
│                          │                                       │
│  PRIORITY 2: Company Config ─────────── HIGH (85%)              │
│              (Políticas explícitas de RH)                        │
│                          │                                       │
│  PRIORITY 3: Job Insights ───────────── HIGH (85%)              │
│              (Dados internos da LIA)                             │
│                          │                                       │
│  PRIORITY 4: ATS History ────────────── MEDIUM (70%)            │
│              (Histórico de ATSs conectados)                      │
│                          │                                       │
│  PRIORITY 5: Market Benchmark ───────── LOW_MEDIUM (55%)        │
│              (Dados externos de mercado)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Fluxo de Consulta:**
1. Verifica cache (Session → Redis → PostgreSQL)
2. Se cache miss, consulta fontes em ordem de prioridade
3. Ordena resultados por confiança
4. Detecta consenso entre fontes (threshold: 20% de variação)
5. Armazena resultado no cache
6. Captura feedback silencioso para learning loop

**Tools Disponíveis para o Wizard:**

| Tool | Descrição | Schema |
|------|-----------|--------|
| `get_intelligent_salary` | Salário consolidado de múltiplas fontes | company_id, job_title, seniority, location |
| `get_intelligent_skills` | Skills consolidadas com categorização | company_id, job_title, seniority, limit |
| `capture_wizard_feedback` | Captura silenciosa de feedback | field_name, suggested_value, final_value |

### 25.3 Learning Loop Silencioso

O sistema captura feedback **silenciosamente** sem alterar a UX:

```
┌─────────────────────────────────────────────────────────────────┐
│                   SILENT LEARNING LOOP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CAPTURE                 ANALYZE                  APPLY         │
│   ────────                ───────                  ─────         │
│   ┌─────────┐            ┌─────────┐            ┌─────────┐     │
│   │Feedback │ ────────►  │Learning │ ────────►  │Improved │     │
│   │Events   │            │Patterns │            │Suggest. │     │
│   └─────────┘            └─────────┘            └─────────┘     │
│        │                      │                      │           │
│        ▼                      ▼                      ▼           │
│   Silently records      Detects patterns       Uses patterns    │
│   accepted/modified/    from accumulated       for better       │
│   rejected values       feedback data          suggestions      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Tipos de Outcome Capturados:**
- `accepted`: Usuário aceitou sugestão sem modificar
- `modified`: Usuário ajustou o valor sugerido
- `rejected`: Usuário rejeitou explicitamente

**Thresholds de Confiança para Patterns:**
- **Alta Confiança**: 20+ amostras, acceptance rate > 75%
- **Média Confiança**: 10+ amostras, acceptance rate > 50%
- **Baixa Confiança**: 5+ amostras
- **Promoção**: Pattern promovido se acceptance rate > 75%
- **Demoção**: Pattern demovido se acceptance rate < 25%

**Modelos de Dados:**

```python
# Eventos de Feedback (captura silenciosa)
class FeedbackEvent(Base):
    __tablename__ = "feedback_events"
    company_id: str           # Tenant
    field_name: str           # Campo afetado (salary, skills, etc.)
    suggested_value: JSON     # O que foi sugerido
    final_value: JSON         # O que usuário usou
    outcome: str              # accepted | modified | rejected
    processed_for_learning: bool  # Já gerou pattern?

# Padrões Aprendidos
class LearningPattern(Base):
    __tablename__ = "learning_patterns"
    company_id: str           # Tenant
    pattern_type: str         # salary_adjustment, skill_preference, etc.
    pattern_value: JSON       # Valor do padrão
    sample_size: int          # Quantas amostras geraram
    acceptance_rate: float    # Taxa de aceitação
    confidence_score: float   # Score 0-1
```

### 25.4 Otimização de Tokens

```python
class TokenOptimizer:
    def optimize_prompt(self, prompt: str, max_tokens: int) -> str:
        # 1. Remove redundâncias
        prompt = self._remove_redundancies(prompt)
        
        # 2. Comprime exemplos se necessário
        if self._count_tokens(prompt) > max_tokens * 0.8:
            prompt = self._compress_examples(prompt)
        
        # 3. Trunca histórico antigo
        if self._count_tokens(prompt) > max_tokens:
            prompt = self._truncate_history(prompt, max_tokens)
        
        return prompt
```

---

## 26. Serviços Principais (173+)

### 26.1 Serviços por Categoria

| Categoria | Quantidade | Exemplos |
|-----------|------------|----------|
| **Intelligence** | 15+ | intelligence_layer_service, confidence_policy_service |
| **Learning** | 15+ | learning_loop_service, cache_manager_service, intelligent_data_orchestrator, ats_job_history_service |
| **WSI** | 10+ | wsi_service, wsi_question_service, wsi_evaluation_service |
| **ATS** | 8+ | gupy_client, pandape_client, stackone_client, merge_client |
| **Job** | 12+ | job_draft_service, jd_template_service, job_publish_service |
| **Candidate** | 15+ | candidate_service, screening_service, ranking_service |
| **Communication** | 10+ | notification_service, email_service, whatsapp_service |
| **Integration** | 8+ | calendar_service, microsoft_graph_service |
| **Utilities** | 20+ | cache_service, token_service, file_service |
| **Outros** | 63+ | Diversos serviços especializados |

### 26.2 Arquivos de Serviço Críticos

```
lia-agent-system/app/services/
├── intelligence_layer_service.py     # Camada de inteligência
├── confidence_policy_service.py      # Cálculo de confiança
├── learning_hub_service.py           # Sistema de aprendizado
├── learning_loop_service.py          # Learning loop silencioso (NEW)
├── cache_manager_service.py          # Cache 3 camadas (NEW)
├── intelligent_data_orchestrator.py  # Orquestração multi-fonte (NEW)
├── ats_job_history_service.py        # Histórico de JDs de ATSs (NEW)
├── recruiter_personalization_service.py  # Personalização
├── jd_template_service.py            # Geração de JD
├── skills_catalog_service.py         # Catálogo de skills
├── wsi_service.py                    # Serviço WSI
├── notification_service.py           # Notificações
└── ats_clients/
    ├── base.py                       # Interface base
    ├── gupy.py                       # Cliente Gupy
    ├── pandape.py                    # Cliente Pandapé
    ├── stackone.py                   # Cliente StackOne
    └── merge.py                      # Cliente Merge
```

---

## 27. Arquivos Críticos para Reconstrução

### 27.1 Frontend (plataforma-lia/src/)

| Arquivo | Descrição |
|---------|-----------|
| `components/expanded-chat/config/wizard-config.ts` | Configuração das 6 etapas |
| `components/expanded-chat/expanded-chat-modal.tsx` | Modal principal do wizard |
| `components/settings/CompanyTeamHub.tsx` | Hub de configurações |
| `hooks/use-job-wizard-backend.ts` | Hook de integração |
| `hooks/use-wizard-suggestions.ts` | Hook do Learning Loop |
| `types/wizard-suggestions.ts` | Tipos do Learning Loop |

### 27.2 Backend (lia-agent-system/app/)

| Arquivo | Descrição |
|---------|-----------|
| `agents/specialized/job_intake_agent.py` | Agente do wizard |
| `agents/specialized/integrador_ats_agent.py` | Agente de integração ATS |
| `services/intelligence_layer_service.py` | Camada de inteligência |
| `api/v1/wizard_suggestions.py` | Endpoints do Learning Loop |
| `models/job_draft.py` | Modelo JobDraft |
| `models/intelligent_cache.py` | Modelos: CacheEntry, LearningPattern, FeedbackEvent |
| `tools/job_wizard_tools.py` | 8 tools do wizard (inclui 3 inteligentes) |
| `data/curated_templates_*.py` | 361 templates |

### 27.3 Documentação

| Arquivo | Descrição |
|---------|-----------|
| `docs/SETTINGS_MENU_MAPPING_FOR_WIZARD.md` | Mapeamento Settings → Wizard (v3.0) |
| `docs/proposals/job-wizard-enhancement-plan-v2.md` | Este documento (v7.0) |
| `docs/templates/TAXONOMIA_TEMPLATES.md` | Taxonomia de templates |

---

# APÊNDICES

---

## A. Sistema de Interação com Sugestões via Chat

### A.1 Tipos de Interação

| Interação | Exemplo | Ação |
|-----------|---------|------|
| **Aceitar** | "Sim", "Ok", "Pode ser" | Aplica sugestão |
| **Rejeitar** | "Não", "Não precisa" | Descarta, registra feedback |
| **Ajustar** | "Aumenta o salário para 15k" | Modifica valor |
| **Perguntar** | "Por que React?" | LIA explica justificativa |

### A.2 Feedback Loop

```python
class SuggestionFeedback(Base):
    __tablename__ = "suggestion_feedback"
    
    id = Column(UUID, primary_key=True)
    suggestion_id = Column(UUID)
    recruiter_id = Column(UUID)
    
    action = Column(String)  # accepted, rejected, modified
    original_value = Column(JSONB)
    modified_value = Column(JSONB, nullable=True)
    
    context = Column(JSONB)  # stage, job_category, etc.
    timestamp = Column(DateTime)
```

---

## B. Histórico de Mudanças

### Versão 7.2 (Fevereiro 2026)
- ✅ **Sistema de Orquestração Inteligente de Dados** (IntelligentDataOrchestrator)
  - Consolidação de 5 fontes com priorização baseada em confiança
  - Learning Patterns (95%), Company Config (85%), Job Insights (85%), ATS History (70%), Market Benchmark (55%)
- ✅ **Arquitetura de Cache em 3 Camadas** (Token Economy)
  - SessionCache (1h), RedisCache (7d), PostgresCache (30d)
  - Fallback gracioso quando Redis indisponível
  - Similaridade semântica com embeddings
- ✅ **Learning Loop Silencioso** 
  - Captura automática de feedback (accepted/modified/rejected)
  - Geração de patterns com thresholds de confiança
  - Sem alteração na UX existente
- ✅ **3 novas tools para o Wizard**
  - `get_intelligent_salary`, `get_intelligent_skills`, `capture_wizard_feedback`
- ✅ **Integração com histórico de ATSs**
  - ATSJobHistoryService busca JDs de Gupy, Pandapé, StackOne, Merge
- ✅ Atualização da seção 25 com arquitetura técnica detalhada

### Versão 7.1 (Fevereiro 2026)
- ✅ Correção: 9 agentes ativos (validado vs código)
- ✅ Correção: 361 templates curados (validado vs código)
- ✅ Correção: 10 categorias de templates
- ✅ Cross-reference validado com implementação real

### Versão 7.0 (Fevereiro 2026)
- ✅ Atualização completa do documento
- ✅ Correção: 6 etapas do wizard (não 7)
- ✅ Adição: Integrações ATS/HRIS (Gupy, Pandapé, StackOne, Merge)
- ✅ Atualização: 173+ serviços, 142+ endpoints
- ✅ Referência ao SETTINGS_MENU_MAPPING v3.0
- ✅ Documentação de agentes legados (deprecated)

### Versão 6.0 (Janeiro 2026)
- Consolidação de documentos
- Fast Track e templates curados
- Learning Loop Fase 1B

### Versão 5.0 (Dezembro 2025)
- Intelligence Layer centralizado
- Personalização por recrutador

### Versão 7.2 (Fevereiro 2026) - Skills Catalog Integration
- **Skills Catalog System**: Catálogo persistente de competências técnicas e comportamentais
  - 4 novos modelos: CompanySkillsCatalog, BehavioralCompetencyCatalog, SkillUsageAnalytics, SkillSuggestionPattern
  - Sincronização automática com tech stack das Configurações
  - Pré-preenchimento inteligente no wizard
  
- **IntelligentDataOrchestrator**: Nova fonte de dados (6 fontes)
  - company_skills_catalog (prioridade 2, confiança 0.90)
  - Integração com learning patterns e analytics
  
- **WSI Question Service**: Geração de perguntas baseadas em skills
  - Mapeamento skill → WSI block (technical_depth, practical_experience, problem_solving, behavioral_fit)
  - Perguntas adaptadas por senioridade (Bloom's Taxonomy + Dreyfus Model)
  
- **Frontend Components**:
  - AddSkillModal com 3 abas (Catálogo, Mercado, Customizado)
  - Categoria "Competências Técnicas Gerais" no CompetenciesStage
  - Hook useCompanySkillsCatalog
  - Auto-prefilling visual com banner
  
- **7 Novos Endpoints API**:
  - GET/POST /api/v1/company/skills-catalog
  - POST /api/v1/company/skills-catalog/sync
  - POST /api/v1/wizard/suggest-skills
  - POST /api/v1/wizard/record-skill-usage
  - GET /api/v1/skills/static/suggest
  - GET /api/v1/skills/search

- **Learning Loop Enhancement**:
  - capture_skills_feedback() - Captura silenciosa de feedback
  - generate_skill_patterns() - Geração de padrões de sugestão
  - SkillUsageAnalytics tracking
  - Promoção automática de padrões de alta confiança (>75%)

---

**Última atualização:** 04 de Fevereiro de 2026  
**Versão do Documento:** 7.2  
**Arquitetura de Agentes:** v2.2 (9 agentes ativos)  
**Etapas do Wizard:** 6 (3 fases)  
**Templates Curados:** 361 (10 categorias)
**Serviços Backend:** 177+ (inclui SkillsCatalogDBService)
