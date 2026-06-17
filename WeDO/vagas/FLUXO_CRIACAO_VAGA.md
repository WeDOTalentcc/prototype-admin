# Fluxo Completo de Criação de Vaga - Plataforma LIA

> **Versão:** 3.0  
> **Data:** Janeiro 2026  
> **Status:** Consolidado e Atualizado  
> **Última Revisão:** 28 de Janeiro de 2026

Este documento descreve passo a passo o fluxo de criação de vaga, desde a descrição inicial até a busca e calibração de candidatos, incluindo todos os sistemas implementados: Learning Hub, Feature Flags, Field Toggles e integrações com agentes especializados.

---

## Índice

1. [Arquitetura de IA da Plataforma](#arquitetura-de-ia-da-plataforma)
2. [Learning Hub System (5 Fases)](#learning-hub-system-5-fases)
3. [Estrutura do Wizard (3 Fases, 7 Etapas)](#estrutura-do-wizard-3-fases-7-etapas)
4. [Fluxo Detalhado por Etapa](#fluxo-detalhado-por-etapa)
5. [Sistema de Feature Flags](#sistema-de-feature-flags)
6. [Field Toggles e Empty Field Notifications](#field-toggles-e-empty-field-notifications)
7. [Análise de Uso de LLMs](#análise-de-uso-de-llms)
8. [Pós-Wizard: Adição de Candidatos](#pós-wizard-adição-de-candidatos)
9. [Diagnóstico e Recomendações](#diagnóstico-e-recomendações)

---

## Arquitetura de IA da Plataforma

### Visão Geral do Sistema Multi-Agente

A Plataforma LIA utiliza uma **arquitetura multi-agente** (v2.2) composta por **1 Orquestrador + 9 Agentes Especializados**. Cada agente é responsável por uma área específica do processo de recrutamento.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATOR (Ag.0)                                │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│   │  Intent Router  │ │  Task Planner   │ │  Policy Engine  │               │
│   └────────┬────────┘ └────────┬────────┘ └────────┬────────┘               │
│            │                   │                   │                        │
│            └───────────────────┼───────────────────┘                        │
│                               │                                             │
│            ┌──────────────────┴──────────────────┐                          │
│            ▼                                      ▼                          │
│   ┌─────────────────┐                   ┌─────────────────┐                 │
│   │  State Manager  │                   │ Enhanced Registry│                 │
│   └─────────────────┘                   └─────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Ag.1        │   │   Ag.2        │   │   Ag.3        │   │   Ag.4        │
│  Job Planner  │   │   Sourcing    │   │  CV Screening │   │  Interviewer  │
│  (Job Intake) │   │               │   │   (Triagem)   │   │  (WSI Voice)  │
└───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Ag.5        │   │   Ag.6        │   │   Ag.7        │   │   Ag.8        │
│ WSI Evaluator │   │  Scheduling   │   │ Analyst &     │   │ ATS Integrator│
│ (Avaliador)   │   │  (Agendador)  │   │ Feedback      │   │ (Gupy/Pandapé)│
└───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Recruiter Assistant │
                        │  (Assistente Pessoal) │
                        └───────────────────────┘
```

### Descrição dos Agentes

| ID | Agente | Responsabilidade | Intents Principais |
|----|--------|------------------|-------------------|
| **Ag.0** | **Orchestrator** | Roteamento de intents, memória de contexto, delegação de tarefas | `route_intent`, `plan_tasks` |
| **Ag.1** | **Job Planner** | Criação/edição de vagas, extração de JD, geração de perguntas WSI | `create_job`, `update_job`, `generate_wsi_questions` |
| **Ag.2** | **Sourcing** | Busca de candidatos, strings booleanas, outreach, integração Pearch | `search_candidates`, `pearch_search`, `outreach_whatsapp` |
| **Ag.3** | **CV Screening** | Parsing de CV, triagem curricular, score inicial, detecção de red flags | `parse_cv`, `screen_candidate`, `rank_candidates` |
| **Ag.4** | **Interviewer** | Entrevistas WSI via WhatsApp/voz, transcrição de áudio | `start_wsi_interview`, `voice_screening` |
| **Ag.5** | **WSI Evaluator** | Scoring WSI (Bloom/Dreyfus/Big Five), pareceres, comparação | `calculate_wsi_score`, `compare_candidates`, `generate_parecer` |
| **Ag.6** | **Scheduling** | Agendamento de entrevistas, integração com calendários | `schedule_interview`, `check_availability` |
| **Ag.7** | **Analyst & Feedback** | KPIs, relatórios, comunicação em massa, feedback para candidatos | `generate_kpi_report`, `send_feedback` |
| **Ag.8** | **ATS Integrator** | Sincronização com Gupy/Pandapé, import/export, compliance LGPD | `sync_candidate`, `gupy_sync` |
| **Special** | **Recruiter Assistant** | Assistente pessoal do recrutador, tarefas pendentes, resumos | `task_summary`, `daily_briefing` |

### Serviços de Inteligência (Services Layer)

| Serviço | Função | Usado no Wizard |
|---------|--------|-----------------|
| `SkillsCatalogService` | Catálogo de skills com sugestões baseadas em cargo/senioridade | Etapa 1, 3 |
| `LearningHubService` | Hub central de aprendizado - 5 fases completas | Todas etapas |
| `FeatureFlagService` | Controle de rollout gradual de funcionalidades | Todas etapas |
| `LiaFieldConfigService` | Field Toggles para controle de consumo de dados pela IA | Etapa 1-5 |
| `FeedbackLearningService` | Aprende com correções do recrutador | Etapa 4, 7 |
| `PatternDetectorService` | Detecta padrões no histórico de vagas da empresa | Etapa 1, 4 |
| `MarketBenchmarkService` | Benchmarks de salário do mercado | Etapa 4 |
| `CompletenessService` | Verifica completude da vaga e campos obrigatórios | Etapa 6 |
| `JDGeneratorService` | Gera descrições de vaga estruturadas | Etapa 6 |
| `WSIService` | Metodologia WSI para avaliação de candidatos | Etapa 5 |

### Componentes do Orchestrator

| Componente | Função |
|------------|--------|
| **Intent Router** | Classifica a intenção do usuário e roteia para o agente correto |
| **Task Planner** | Decompõe tarefas complexas em subtarefas sequenciais |
| **Policy Engine** | Valida limites, permissões e aprovações |
| **State Manager** | Gerencia estado de conversações e contexto |
| **Enhanced Registry** | Registro de agentes com fallback chains e roteamento por confiança |

### Provedores de LLM

| Provider | Modelo | Uso Principal | Usado no Wizard | Tokens Típicos |
|----------|--------|---------------|-----------------|----------------|
| **Anthropic Claude** | claude-sonnet-4-5 | Análises complexas, geração de JD, pareceres | ✅ Sim | 2.000-4.000/chamada |
| **Google Gemini** | gemini-2.5-flash | Extração de entidades, busca semântica | ✅ Sim | 500-1.500/chamada |
| **OpenAI** | gpt-4o | Disponível como fallback alternativo | ❌ Não usado | N/A |

> **Nota:** OpenAI GPT-4o está configurado no `LLMService` mas não é utilizado no fluxo do wizard. Os provedores primários são Claude (para análise/geração) e Gemini (para extração/busca).

---

## Learning Hub System (5 Fases)

O Learning Hub é o sistema central de aprendizado da plataforma, implementado em 5 fases:

### Fase 1: Skills Learning Loop

**Objetivo:** Aprender padrões de skills por cargo/senioridade

```
┌─────────────────────────────────────────────────────────────────┐
│                    SKILLS LEARNING LOOP                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Recrutador confirma/corrige skill sugerida                  │
│     ↓                                                           │
│  2. CompanyLearning registra confirmação                        │
│     ↓                                                           │
│  3. Após 3+ confirmações → skill é "promovida"                  │
│     ↓                                                           │
│  4. Agentes usam learning context em sugestões futuras          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Modelo:** `CompanyLearning`
- `skill_confirmations`: Dict de skills confirmadas por cargo
- `promoted_skills`: Skills promovidas (threshold: 3 confirmações)

**Endpoint:** `POST /lia/learning/confirm-skill`

### Fase 2: Responsibilities Deduplication

**Objetivo:** Eliminar redundância de responsabilidades entre stages

```
┌─────────────────────────────────────────────────────────────────┐
│            RESPONSIBILITIES DEDUPLICATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Responsabilidade detectada no Stage 1                       │
│     ↓                                                           │
│  2. Hash SHA256 calculado para normalização                     │
│     ↓                                                           │
│  3. Deduplicação automática (remove variações similares)        │
│     ↓                                                           │
│  4. Confirmação do recrutador armazena versão canônica          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Endpoint:** `POST /lia/learning/confirm-responsibility`

### Fase 3: Stage Feedback Learning

**Objetivo:** Aprender com feedback de recrutadores em cada stage

```
┌─────────────────────────────────────────────────────────────────┐
│                  STAGE FEEDBACK LEARNING                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Stages 2-7:                                                    │
│  • Recrutador pode dar thumbs up/down em sugestões              │
│  • Feedback registrado por stage/field/recrutador               │
│  • Sistema ajusta sugestões baseado em padrões                  │
│                                                                  │
│  Métricas coletadas:                                            │
│  • acceptance_rate por stage                                    │
│  • correction_rate por field                                    │
│  • time_spent por stage                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Endpoint:** `POST /api/v1/lia/learning/stage-feedback`

### Fase 4: Outcome Learning

**Objetivo:** Conectar resultados de contratação ao aprendizado

```
┌─────────────────────────────────────────────────────────────────┐
│                    OUTCOME LEARNING                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Eventos monitorados:                                           │
│  • Candidato contratado (hired)                                 │
│  • Time-to-fill da vaga                                         │
│  • Desempenho pós-contratação (90 dias)                         │
│  • Retenção (180 dias)                                          │
│                                                                  │
│  Insights gerados:                                              │
│  • Skills que correlacionam com sucesso                         │
│  • Faixas salariais que atraem melhores candidatos              │
│  • Canais de sourcing mais efetivos                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Modelo:** `JobOutcome` (em `feedback_learning.py`)

**Endpoints:**
- `POST /api/v1/lia/learning/job-outcome`
- `POST /api/v1/lia/learning/outcome-insights`

### Fase 5: Analytics Dashboard

**Objetivo:** Visualização de métricas de learning e saúde do sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                   ANALYTICS DASHBOARD                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Métricas expostas:                                             │
│  • Health Score (0-100) por empresa                             │
│  • Skills coverage por cargo                                    │
│  • Acceptance rate por stage                                    │
│  • Learning velocity (skills promovidas/mês)                    │
│                                                                  │
│  Status: API Completa, UI Pendente                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Endpoint:** `POST /api/v1/lia/learning/dashboard`

### Mapeamento Completo de Endpoints (Learning Hub)

| Fase | Endpoint | Método | Descrição |
|------|----------|--------|-----------|
| 1 - Skills | `/lia/learning/confirm-skill` | POST | Confirma skill para promoção |
| 2 - Responsibilities | `/lia/learning/confirm-responsibility` | POST | Confirma responsabilidade |
| 1-2 | `/lia/learning/context` | POST | Obtém contexto de learning |
| 3 - Stage Feedback | `/api/v1/lia/learning/stage-feedback` | POST | Registra feedback por stage |
| 4 - Outcome | `/api/v1/lia/learning/job-outcome` | POST | Registra outcome de vaga |
| 4 - Outcome | `/api/v1/lia/learning/outcome-insights` | POST | Obtém insights de outcomes |
| 5 - Analytics | `/api/v1/lia/learning/dashboard` | POST | Dashboard de analytics |
| 5 - Analytics | `/api/v1/lia/learning/skills-deduplicated` | POST | Skills deduplicadas |

---

## Estrutura do Wizard (3 Fases, 7 Etapas)

### Diagrama do Fluxo Consolidado

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        WIZARD DE CRIAÇÃO DE VAGA v3.0                          │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  FASE 1: CONSTRUÇÃO          FASE 2: ATIVAÇÃO        FASE 3: SELEÇÃO          │
│  ┌─────────────────────┐    ┌──────────────────┐    ┌───────────────────────┐ │
│  │ 1. input-evaluation │    │                  │    │                       │ │
│  │ 2. job-description  │───▶│ 6. review-publish│───▶│ 7. search-calibration │ │
│  │ 3. competencies     │    │                  │    │                       │ │
│  │ 4. salary           │    │                  │    │                       │ │
│  │ 5. wsi-questions    │    │                  │    │                       │ │
│  └─────────────────────┘    └──────────────────┘    └───────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                        SISTEMAS TRANSVERSAIS                             │  │
│  ├─────────────────────────────────────────────────────────────────────────┤  │
│  │ Learning Hub │ Feature Flags │ Field Toggles │ Empty Field Notifications │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Mapeamento de Etapas

| Etapa | ID | Fase | Agentes/Serviços | LLM |
|-------|-----|------|------------------|-----|
| 1 | `input-evaluation` | Construção | Job Intake Agent, IntelligenceLayerService | Gemini |
| 2 | `job-description` | Construção | PatternDetectorService, CompanyConfigService | - |
| 3 | `competencies` | Construção | SkillsCatalogService, LearningHubService | - |
| 4 | `salary` | Construção | MarketBenchmarkService, FeedbackLearningService | - |
| 5 | `wsi-questions` | Construção | WSI Generator, WSIService | Claude |
| 6 | `review-publish` | Ativação | CompletenessService, JDGeneratorService | Claude |
| 7 | `search-calibration` | Seleção | Sourcing Agent, WSI Evaluator | Gemini + Claude |

---

## Fluxo Detalhado por Etapa

### Etapa 1: Input & Evaluation (`input-evaluation`)

**O que o Recrutador Faz:**
- Descreve a vaga em linguagem natural (ou cola JD)
- Visualiza critérios detectados automaticamente
- Recebe análise proativa de compensação vs. mercado

**O que a LIA Faz (Job Intake Agent):**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. RECEBE INPUT DO RECRUTADOR                                               │
│     • Descrição livre: "Preciso de um Dev Python Senior em SP"              │
│     • OU Job Description colada                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. EXTRAÇÃO DE ENTIDADES (LLM: Gemini 2.5 Flash)                            │
│     • Cargo: "Desenvolvedor Python"                                         │
│     • Senioridade: "Senior"                                                 │
│     • Skills detectadas: [Python, FastAPI, PostgreSQL]                      │
│     • Modelo de trabalho: "Híbrido" (inferido)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. BUSCA CONFIGURAÇÕES DA EMPRESA                                           │
│     • work_model padrão                                                     │
│     • departamentos disponíveis                                             │
│     • tech stack cadastrado                                                 │
│     • benefícios por senioridade                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. LEARNING CONTEXT (LearningHubService)                                    │
│     • Skills promovidas para o cargo                                        │
│     • Responsabilidades confirmadas anteriormente                           │
│     • Ajustes aprendidos do recrutador                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. BENCHMARK DE SKILLS (SkillsCatalogService)                               │
│     • Skills esperadas para cargo/senioridade                               │
│     • Skills detectadas vs. esperadas                                       │
│     • Completeness score                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  6. RESPOSTA AO RECRUTADOR                                                   │
│     • Campos auto-preenchidos (confiança > 85%)                             │
│     • Sugestões com contexto ("77% das suas vagas anteriores")              │
│     • Warnings de skills faltantes                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Campos Coletados:**
```
cargo, senioridade, modeloTrabalho, localizacao,
competenciasTecnicas[], competenciasComportamentais[],
responsabilidades[], experiencia, formacao, tipoContrato
```

**Tokens LLM:** ~1.000-1.500 (Gemini)

---

### Etapa 2: Job Description (`job-description`)

**O que o Recrutador Faz:**
- Confirma informações básicas da vaga
- Ajusta departamento, gestor, número de posições
- Define prazo de preenchimento

**O que a LIA Faz:**
1. Busca departamentos cadastrados (`CompanyConfigurationService`)
2. Identifica padrões administrativos (`PatternDetectorService`)
3. Sugere valores baseados no histórico

**Campos Coletados:**
```
numero_posicoes, departamento, gestor_vaga, prazo_preenchimento,
tipo_contrato (CLT/PJ/Temporário/Estágio)
```

**Tokens LLM:** 0 (processamento local)

---

### Etapa 3: Competências (`competencies`)

**O que o Recrutador Faz:**
- Revisa skills técnicas e comportamentais
- Define nível de proficiência (Básico/Intermediário/Avançado)
- Define prioridade (Essencial/Importante/Diferencial)

**O que a LIA Faz:**
1. Carrega skills confirmadas da Etapa 1
2. Busca benchmark de mercado (`MarketBenchmarkService`)
3. Sugere pesos baseados em frequência de mercado
4. Registra confirmações no Learning Hub

**Níveis de Prioridade:**

| Nível | Significado | Impacto no Score |
|-------|-------------|------------------|
| **Essencial** | Obrigatório - candidato sem é eliminado | Peso 3x |
| **Importante** | Forte diferencial | Peso 2x |
| **Diferencial** | Nice to have | Peso 1x |

**Tokens LLM:** 0 (processamento local)

---

### Etapa 4: Remuneração (`salary`)

**O que o Recrutador Faz:**
- Define faixa salarial (mínimo-máximo)
- Confirma bônus/PLR
- Seleciona benefícios

**O que a LIA Faz:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. HISTÓRICO DE SALÁRIOS (PatternDetectorService)                           │
│     • Média de vagas similares: R$ 12.000 - R$ 18.000                       │
│     • Amostra: "8 vagas nos últimos 12 meses"                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. BENCHMARK DE MERCADO (MarketBenchmarkService)                            │
│     • Mediana de mercado: R$ 15.000 - R$ 22.000                             │
│     • Tendência: +8% (alta)                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. LEARNING ADJUSTMENTS (FeedbackLearningService)                           │
│     • Recrutador ajustou para cima 3+ vezes → +12%                          │
│     • Confiança: média                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. BENEFÍCIOS (CompanyConfigurationService)                                 │
│     • Carrega benefícios filtrados por senioridade                          │
│     • Pré-seleciona benefícios padrão                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Campos Coletados:**
```
salary_min, salary_max, bonus_plr (boolean),
beneficios[]: { name, selected }
```

**Tokens LLM:** 0 (processamento local)

---

### Etapa 5: Triagem WSI (`wsi-questions`)

**O que o Recrutador Faz:**
- Revisa perguntas sugeridas pela LIA
- Edita, adiciona ou remove perguntas
- Define quais são obrigatórias

**O que a LIA Faz (WSI Question Generator):**

1. **Gera perguntas por Framework:**
   - **CBI (Competency-Based Interview)** - Para skills técnicas
   - **BigFive** - Para competências comportamentais

2. **Estrutura WSI** - 7 blocos metodológicos:
   1. Autodeclaração de contexto
   2. Micro-cases técnicos
   3. Situacional comportamental
   4. Fit cultural
   5. Autodeclaração de habilidades
   6. Perguntas técnicas
   7. Perguntas de elegibilidade

**Campos Coletados:**
```
wsi_questions[]: {
  competency, type (technical/behavioral),
  question, framework (CBI/BigFive),
  is_required, block_number
}
```

**Tokens LLM:** ~1.500-2.000 (Claude)

---

### Etapa 6: Revisão e Publicação (`review-publish`)

**O que o Recrutador Faz:**
- Revisa resumo completo da vaga
- Visualiza preview da Job Description gerada
- Seleciona plataformas de publicação

**O que a LIA Faz:**

1. **Verificação de Completude** (`CompletenessService`):
   - Score de completude (0-100%)
   - Campos obrigatórios faltantes
   - Campos recomendados faltantes

2. **Geração de JD** (`JDGeneratorService` - Claude):
   - Gera descrição estruturada
   - Preview para validação

3. **Transparência de Origens**:
   - Mostra fonte de cada campo auto-preenchido
   - Confidence score de cada campo

**Tokens LLM:** ~2.000-3.000 (Claude para JD)

**Resposta da LIA (Exemplo):**
```
**Revisão Final da Vaga**

✅ **Completude: 92%** - Vaga pronta para publicação!

💡 **Recomendamos preencher:** Idiomas

---

**Origem dos campos preenchidos automaticamente** (4 campos):
  • Modelo de Trabalho: 📊 Padrão histórico (85% confiança)
  • Tipo de Contratação: 📊 Padrão histórico (90% confiança)
  • Faixa Salarial: 🧠 Aprendizado (+12%)
  • Competências Técnicas: 🤖 Detecção automática (78% confiança)
```

---

### Etapa 7: Busca e Calibração (`search-calibration`)

> **Nota:** Esta etapa consolida os antigos Stages 8, 9 e 10.

**O que o Recrutador Faz:**
- Visualiza candidatos sugeridos
- Avalia candidatos (Aprovar/Reprovar/Comentar)
- Ajusta filtros de busca
- Monitora pipeline

**O que a LIA Faz:**

#### Sub-etapa 7.1: Busca de Candidatos (Sourcing Agent)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. BUSCA NA BASE DE TALENTOS                                                │
│     • Semantic search (Gemini embeddings)                                   │
│     • Boolean query builder                                                 │
│     • Filtros: skills, experiência, localização                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. SCORING DE ADERÊNCIA                                                     │
│     • Match de skills técnicas                                              │
│     • Match de skills comportamentais                                       │
│     • Match de experiência/senioridade                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. RANKING E APRESENTAÇÃO                                                   │
│     • Candidatos ordenados por aderência                                    │
│     • Cache em Redis para performance                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tokens LLM:** ~500-1.000 (Gemini para semantic search)

#### Sub-etapa 7.2: Calibração (WSI Evaluator)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. RECRUTADOR AVALIA CANDIDATOS                                             │
│     ✅ Aprovar - Perfil adequado                                            │
│     ❌ Reprovar - Não adequado                                              │
│     💬 Comentar - Observações                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. SISTEMA APRENDE COM FEEDBACK                                             │
│     • Registra feedback em FeedbackLearningService                          │
│     • Ajusta pesos do algoritmo de matching                                 │
│     • Identifica padrões de preferência                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. GERAÇÃO DE PARECER (se solicitado) - Claude                              │
│     • Análise detalhada do candidato                                        │
│     • Pontos fortes e fracos                                                │
│     • Recomendação final                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Tokens LLM:** ~2.000-3.000 (Claude para parecer)

#### Sub-etapa 7.3: Busca Ativa (Active Sourcing)

- **Outreach Automatizado**: Contato com candidatos passivos
- **Monitoramento**: Acompanha respostas
- **Notificações**: Alerta sobre novos candidatos compatíveis

**Endpoints Implementados (Mapeamento Stages 8-10 → Etapa 7):**

> **Nota:** Os antigos Stages 8, 9 e 10 foram consolidados na Etapa 7 (`search-calibration`) do novo wizard. Os endpoints backend mantêm a nomenclatura original para compatibilidade.

| Endpoint | Stage Original | Sub-etapa 7 | Função |
|----------|----------------|-------------|--------|
| `POST /lia/wizard/stage8/search` | Stage 8 | 7.1 Busca | Busca de candidatos |
| `POST /lia/wizard/stage8/feedback` | Stage 8 | 7.1 Busca | Feedback de busca |
| `POST /lia/wizard/stage9/evaluate` | Stage 9 | 7.2 Calibração | Avaliação WSI |
| `POST /lia/wizard/stage9/calibrate` | Stage 9 | 7.2 Calibração | Calibração de critérios |
| `POST /lia/wizard/stage10/start-sourcing` | Stage 10 | 7.3 Busca Ativa | Inicia sourcing ativo |
| `POST /lia/wizard/stage10/outreach` | Stage 10 | 7.3 Busca Ativa | Outreach automatizado |
| `POST /lia/wizard/stage10/feedback` | Stage 10 | 7.3 Busca Ativa | Feedback de sourcing |

---

## Sistema de Feature Flags

O sistema de Feature Flags permite rollout gradual de funcionalidades.

### Flags Implementadas

| Flag | Descrição | Default |
|------|-----------|---------|
| `learning_hub_skills` | Ativa learning loop de skills | `true` |
| `learning_hub_responsibilities` | Ativa deduplicação de responsabilidades | `true` |
| `stage_feedback` | Ativa feedback por stage | `true` |
| `outcome_learning` | Ativa aprendizado por outcomes | `true` |
| `analytics_dashboard` | Ativa dashboard de analytics | `false` |
| `field_toggles` | Ativa sistema de field toggles | `true` |
| `empty_field_notifications` | Ativa notificações de campos vazios | `true` |
| `proactive_compensation` | Ativa análise proativa de compensação | `true` |

### Endpoints

| Endpoint | Função |
|----------|--------|
| `POST /api/v1/lia/feature-flags/set` | Define valor de flag |
| `GET /api/v1/lia/feature-flags` | Lista todas as flags |
| `GET /api/v1/lia/feature-flags/check/{key}` | Verifica flag específica |

### Uso no Código

```python
from app.services.feature_flag_service import feature_flag_service

if await feature_flag_service.is_enabled("learning_hub_skills", company_id):
    # Executa lógica com learning hub
    pass
```

---

## Field Toggles e Empty Field Notifications

### Field Toggles

Sistema que permite ao administrador controlar quais campos a LIA pode consumir para sugestões.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FIELD TOGGLES SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Configuração por empresa:                                                  │
│  • Quais campos a LIA pode ler (tech_stack, departments, benefits, etc.)   │
│  • Quais campos a LIA pode sugerir automaticamente                         │
│  • Nível de confiança mínimo para auto-fill                                │
│                                                                              │
│  Exemplo:                                                                   │
│  - tech_stack: enabled=true, auto_suggest=true, min_confidence=0.8         │
│  - salary_range: enabled=true, auto_suggest=false (sempre perguntar)       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Endpoints:**

| Endpoint | Função |
|----------|--------|
| `GET /api/v1/lia-field-toggles/{company_id}` | Lista toggles |
| `PUT /api/v1/lia-field-toggles/{company_id}/{field_key}` | Atualiza toggle |

### Empty Field Notifications

Sistema que notifica o recrutador durante o wizard quando campos importantes estão vazios na configuração da empresa.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EMPTY FIELD NOTIFICATIONS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Fluxo:                                                                     │
│  1. LIA detecta que campo está vazio (ex: tech_stack não cadastrado)       │
│  2. Notificação aparece no chat do wizard                                   │
│  3. Recrutador pode:                                                        │
│     - "Configurar agora" → abre modal/redireciona para settings            │
│     - "Ignorar por agora" → continua wizard sem a sugestão                 │
│     - "Não lembrar mais" → desativa notificação para este campo            │
│                                                                              │
│  Benefício: Onboarding progressivo das configurações da empresa            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Endpoints:**

| Endpoint | Função |
|----------|--------|
| `GET /api/v1/lia-field-toggles/{company_id}/empty-fields` | Lista campos vazios |
| `POST /api/v1/lia-field-toggles/{company_id}/empty-fields/{field}/action` | Executa ação |
| `POST /api/v1/lia-field-toggles/{company_id}/empty-fields/{field}/suggest` | Sugere valor |

**Componentes Frontend:**
- `use-empty-field-notifications.ts` - Hook de estado
- `empty-field-notification-message.tsx` - Componente UI

---

## Análise de Uso de LLMs

### Consumo de Tokens por Etapa

| Etapa | LLM | Tokens (Input) | Tokens (Output) | Total Estimado |
|-------|-----|----------------|-----------------|----------------|
| 1. input-evaluation | Gemini | 800 | 400 | ~1.200 |
| 5. wsi-questions | Claude | 1.200 | 600 | ~1.800 |
| 6. review-publish (JD) | Claude | 1.500 | 1.200 | ~2.700 |
| 7. search (semantic) | Gemini | 500 | 200 | ~700 |
| 7. parecer | Claude | 1.800 | 1.500 | ~3.300 |

**Total por vaga (fluxo completo):** ~9.700 tokens

### Recomendações de Otimização

| Área | Problema Identificado | Solução Proposta | Economia Estimada |
|------|----------------------|------------------|-------------------|
| Etapas 1-3 | Redundância de detecção de skills | Unificar detecção na Etapa 1 com cache | -30% tokens |
| Etapa 6 (JD) | JDs similares regeneradas | Cache de templates por cargo/senioridade | -40% tokens |
| Etapa 7 (parecer) | Parecer completo sempre | Parecer resumido por default, completo on-demand | -50% tokens |
| Semantic search | Múltiplas buscas similares | Cache de embeddings por 24h | -60% buscas |

### Estratégia de Fallback

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LLM FALLBACK STRATEGY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Primário: Claude Sonnet 4.5 (análise complexa, geração de texto)          │
│     │                                                                       │
│     ▼ (se indisponível ou rate limit)                                       │
│  Fallback 1: Gemini 2.5 Flash (mais rápido, menor custo)                   │
│     │                                                                       │
│     ▼ (se indisponível)                                                     │
│  Fallback 2: Processamento local/regras (sem LLM)                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pós-Wizard: Adição de Candidatos

### Formas de Adicionar Candidatos

| Método | Descrição | Endpoint |
|--------|-----------|----------|
| Candidatura Direta | Candidato preenche formulário WSI | `POST /api/v1/applications/` |
| Adição Manual | Recrutador busca e adiciona | `POST /api/v1/job-vacancies/{id}/candidates/` |
| Sourcing LIA | LIA sugere, recrutador aprova | `POST /api/v1/sourcing/add-to-job/` |
| Upload em Massa | Upload de CVs (PDF/DOC) | `POST /api/v1/cv-parser/batch-upload/` |

### Pipeline do Kanban

| Estágio | Descrição |
|---------|-----------|
| Novo | Candidato recém adicionado |
| Triagem | Análise inicial de CV |
| Entrevista RH | Primeira entrevista |
| Entrevista Técnica | Avaliação de skills |
| Entrevista Gestor | Fit cultural |
| Proposta | Negociação salarial |
| Contratado | Candidato aceito |
| Reprovado | Não aprovado |

---

## Análise Crítica: Metodologias de Busca de Candidatos

### Metodologia Atual (Sourcing Agent)

A busca de candidatos utiliza uma abordagem em **2 camadas principais**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE BUSCA ATUAL                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1️⃣ BOOLEAN QUERY BUILDER (sourcing_agent.py:BooleanQueryBuilder)           │
│  ├── Gera queries para: LinkedIn, Banco Local, Pearch                      │
│  ├── expand_synonyms(): Expande termos com mapa estático                    │
│  │   (ex: "developer" → ["desenvolvedor", "programador", "engineer"])       │
│  ├── Suporte a seniority, location, exclude_terms                           │
│  └── Custo: 0 tokens (regras estáticas)                                     │
│                                                                              │
│  2️⃣ CANDIDATE MATCHER (sourcing_agent.py:CandidateMatcher)                  │
│  ├── Skills Match: 50% peso (weights["skills"] = 0.50)                      │
│  │   ├── Required skills: 80% do score de skills                            │
│  │   └── Nice-to-have: 20% do score de skills                               │
│  ├── Experience Match: 30% peso (weights["experience"] = 0.30)              │
│  │   ├── Meets requirement: 100 pts                                         │
│  │   ├── Slightly under (≤1 ano): 80 pts                                    │
│  │   ├── Under qualified (≤2 anos): 60 pts                                  │
│  │   └── Significantly under: 30 pts                                        │
│  ├── Location Match: 20% peso (weights["location"] = 0.20)                  │
│  │   ├── Remote/hybrid: 100 pts                                             │
│  │   ├── Same city: 100 pts                                                 │
│  │   ├── Same state: 80 pts                                                 │
│  │   └── Same country: 60 pts                                               │
│  └── Custo: 0 tokens (cálculo local, sem LLM)                               │
│                                                                              │
│  RESULTADO → Tiers: A (≥85%), B (≥70%), C (≥55%), D (<55%)                 │
│                                                                              │
│  📌 NOTA IMPORTANTE:                                                         │
│  ├── SemanticSearchService (Gemini Flash + Redis cache) existe              │
│  ├── Usado primariamente no Modal de Filtros Avançados do frontend          │
│  ├── SourcingAgent._handle_semantic_search() é user-invoked (sob demanda)   │
│  └── Pipeline automático NÃO usa semantic search, apenas expand_synonyms()  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Código fonte confirmado:**
```python
# sourcing_agent.py linha 318
weights = {"skills": 0.50, "experience": 0.30, "location": 0.20}

# sourcing_agent.py linha 330
tier = "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 55 else "D"
```

### Metodologia de Rubricas (RubricEvaluationService)

O serviço de rubricas utiliza **BARS** (Behaviorally Anchored Rating Scale):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AVALIAÇÃO POR RUBRICAS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  NÍVEIS DE AVALIAÇÃO:                                                       │
│  ├── EXCEEDS (100 pts): Evidência excepcional, >50% acima do requisito      │
│  ├── MEETS (75 pts): Demonstra claramente a competência                     │
│  ├── PARTIAL (40 pts): Evidência relacionada mas não direta                 │
│  └── MISSING (0 pts): Nenhuma evidência encontrada                          │
│                                                                              │
│  PESOS POR PRIORIDADE:                                                      │
│  ├── ESSENTIAL: 3x multiplicador                                            │
│  ├── IMPORTANT: 2x multiplicador                                            │
│  └── NICE_TO_HAVE: 1x multiplicador                                         │
│                                                                              │
│  FEATURES:                                                                   │
│  ├── Cache de avaliações (TTL 168h) via hash SHA256                         │
│  ├── Log de variações (alerta se delta > 10 pts)                            │
│  ├── Calibração com feedback do recrutador                                  │
│  └── Versionamento de calibração por vaga                                   │
│                                                                              │
│  CUSTO ESTIMADO: ~500-800 tokens por candidato (análise completa de CV)     │
│  ⚠️ Valores estimados, não medidos em produção                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Código fonte confirmado:**
```python
# rubric_evaluation_service.py linha 36-37
CACHE_TTL_HOURS = int(os.getenv("RUBRIC_CACHE_TTL_HOURS", "168"))  # 7 dias
VARIATION_THRESHOLD = float(os.getenv("RUBRIC_VARIATION_THRESHOLD", "10.0"))

# rubric_evaluation_service.py linha 543-549
multiplier_map = {
    RequirementPriorityEnum.ESSENTIAL: 3,
    RequirementPriorityEnum.IMPORTANT: 2,
    RequirementPriorityEnum.NICE_TO_HAVE: 1,
}
```

### Comparação: Scoring Atual vs Rubricas

| Critério | Scoring Atual | Rubricas (BARS) | Fonte |
|----------|---------------|-----------------|-------|
| **Custo por candidato** | 0 tokens (local) | ~500-800 tokens* | Estimado |
| **Precisão** | Média (keyword matching) | Alta (análise semântica) | Estimado |
| **Explicabilidade** | Baixa (scores numéricos) | Alta (evidências citadas) | Código |
| **Calibração** | Não tem | Sim (CalibrationFeedback) | Código |
| **Cache** | Não tem | Sim (168h TTL) | Código |
| **Tempo de resposta** | <100ms | ~2-3s* | Estimado |
| **Escala** | Excelente (ilimitado) | Limitada (top 50-100) | Estimado |

*Valores estimados, não medidos em produção

### Recomendação: Abordagem Híbrida

**Proposta de fluxo otimizado:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO HÍBRIDO RECOMENDADO                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FASE 1: TRIAGEM RÁPIDA (Scoring Atual)                                     │
│  ├── Boolean Query + Semantic Expansion                                     │
│  ├── Candidate Matcher scoring                                              │
│  ├── Filtrar top 50-100 candidatos (Tier A + B)                             │
│  └── Custo: ~0-200 tokens                                                   │
│                                                                              │
│  FASE 2: AVALIAÇÃO PROFUNDA (Rubricas)                                      │
│  ├── Aplicar apenas nos top 20-50 candidatos                                │
│  ├── Gerar rubric score + evidências                                        │
│  ├── Cache por 7 dias                                                       │
│  └── Custo: ~500-800 tokens × 20-50 = 10K-40K tokens                        │
│                                                                              │
│  ECONOMIA ESTIMADA: 80-90% vs aplicar rubricas em todos                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Viabilidade: Rubricas no Job Description

**SIM, é viável** aplicar a metodologia de rubricas ao JD para parametrizar a busca:

```python
# Proposta: Transformar requisitos do JD em rubricas automaticamente
def jd_to_rubrics(job_description: dict) -> List[JobRequirement]:
    rubrics = []
    
    # Essential requirements → ESSENTIAL priority (3x)
    for req in job_description.get("essential_requirements", []):
        rubrics.append(JobRequirementCreate(
            requirement=req,
            priority=RequirementPriorityEnum.ESSENTIAL,
            description=f"Requisito obrigatório: {req}"
        ))
    
    # Important requirements → IMPORTANT priority (2x)
    for req in job_description.get("important_requirements", []):
        rubrics.append(JobRequirementCreate(
            requirement=req,
            priority=RequirementPriorityEnum.IMPORTANT
        ))
    
    # Nice-to-have → NICE_TO_HAVE priority (1x)
    for req in job_description.get("nice_to_have", []):
        rubrics.append(JobRequirementCreate(
            requirement=req,
            priority=RequirementPriorityEnum.NICE_TO_HAVE
        ))
    
    return rubrics
```

**Custo estimado por vaga (valores especulativos, não medidos):**
- Geração de rubricas do JD: ~200 tokens* (uma vez)
- Avaliação de 50 candidatos: ~30K tokens*
- Com cache (7 dias): economia de 60-80%* em reavaliações
- **Total: ~$0.10-0.20 por vaga*** (baseado em preços Claude Sonnet Jan/2026)

*Estimativas baseadas em padrões de mercado, não validadas em produção

---

## Etapa 7.3: Busca Ativa - Detalhamento Completo

### Fluxo de Adição ao Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO BUSCA ATIVA (Stage 7.3)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1️⃣ LIA INICIA BUSCA                                                        │
│  ├── Busca no banco local do recrutador                                     │
│  ├── Se insuficiente + Pearch ativo → busca global                          │
│  └── Calcula match score para cada candidato                                │
│                                                                              │
│  2️⃣ ADIÇÃO AO PIPELINE                                                      │
│  ├── Método: `_add_candidates_to_job()` ou `_add_pearch_candidates_to_job()`│
│  ├── Cria registro Interview com:                                           │
│  │   ├── status: "pending"                                                  │
│  │   ├── application_stage: "triagem"                                       │
│  │   ├── interview_type: "triagem"                                          │
│  │   └── created_by: "sourcing_pipeline" ou "sourcing_pipeline_pearch"      │
│  ├── Score: ✅ Pearch e Local salvam lia_score corretamente                 │
│  └── Detalhes: ver seção "ONDE O SCORE É ARMAZENADO" abaixo                 │
│                                                                              │
│  3️⃣ ORDENAÇÃO (apenas em AgentResponse, não persiste no DB)                 │
│  ├── candidatos.sort(key=lambda x: x.get("overall_score", 0), reverse=True) │
│  ├── Aplicado apenas ao retornar resposta para o frontend                   │
│  └── Ordem no banco/kanban: conforme inserção (não por score)               │
│                                                                              │
│  4️⃣ ONDE O SCORE É ARMAZENADO                                               │
│  ├── Candidate.lia_score: Float (modelo candidate.py linha 206/353)         │
│  ├── ✅ Pearch: lia_score=data.get("match_score") na criação                │
│  ├── ✅ Local: lia_score via _calculate_local_match_score() (0-100)         │
│  │   └── Skills(50pts) + Seniority(10pts) + Experience(20pts) +             │
│  │       Title(15pts) + Location(5pts)                                      │
│  ├── Sorting: AgentResponse ordena por overall_score (não persiste no DB)   │
│  └── UI: implementação de exibição depende do frontend (não verificado)     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Notificações ao Recrutador

**Canais disponíveis:**
- `bell` - Notificação in-app (sino)
- `email` - E-mail automático
- `teams` - Microsoft Teams (webhook)
- `sms` - SMS (via Twilio)

**Notificação de Triagem Concluída:** ✅ MELHORADA
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📬 TEAMS / BELL NOTIFICATION (v2.0 - Janeiro 2026)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Título: "Triagem concluída: {candidate_name}"                              │
│                                                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│  📋 Vaga: {job_title} (ID: {vacancy_id})                                    │
│  👤 Candidato: {candidate_name} (ID: {candidate_id})                        │
│  👔 Gestor: {hiring_manager_name}                                           │
│  🏢 Departamento: {department}                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│  📊 Score WSI: {wsi_score}/5 | {tier_emoji} Tier: {tier}                    │
│  ✅ Confiança: {confidence}%                                                │
│  💡 Recomendação: {tier_recommendation}                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│                                                                              │
│  Tier Classification:                                                        │
│  ⭐ A (4.0-5.0): Aprovar, Agendar Entrevista, Ver Detalhes                  │
│  🟢 B (3.0-3.9): Ver Detalhes, Aprovar, Solicitar Entrevista                │
│  🟡 C (2.0-2.9): Ver Detalhes, Solicitar Avaliação Adicional                │
│  🔴 D (0.0-1.9): Ver Detalhes, Arquivar                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Status: Fluxo Recrutador → WhatsApp Triagem - ✅ IMPLEMENTADO

**✅ CONECTADO END-TO-END (Janeiro 2026)**

O conector Teams→WhatsApp foi implementado com webhook seguro:

| Componente | Status | Código Fonte |
|------------|--------|--------------|
| Notificação Teams (saída) | ✅ Implementado | `teams_service.py:send_message()` |
| Adaptive Cards | ✅ Implementado | `teams_service.py:send_adaptive_card()` |
| Webhook Teams (entrada) | ✅ Implementado | `api/v1/teams.py:webhook_handler()` |
| WhatsApp Screening | ✅ Implementado | `whatsapp_service.py` |
| Trigger Teams→WhatsApp | ✅ Implementado | `teams.py` → `whatsapp_service.start_screening()` |
| Segurança HMAC-SHA256 | ✅ Implementado | Validação obrigatória em produção |
| Audit Logs | ✅ Implementado | `TeamsActionAuditLog` modelo PostgreSQL |

**Arquitetura atual (separada):**
```
Fluxo 1: Notificações
LIA → TeamsService → Teams Channel (one-way, sem resposta)

Fluxo 2: Triagem WhatsApp
WhatsApp trigger → whatsapp_service → screening_agent (separado)
```

**Para conectar end-to-end seria necessário:**
1. Criar endpoint `/api/v1/teams/webhook` para receber ações do Adaptive Card
2. Configurar Microsoft Graph webhook ou Bot Framework
3. Criar handler que conecta action "Aprovar" → `start_whatsapp_screening()`
4. Esforço estimado: 8-12h de desenvolvimento

---

## Redundâncias UX Etapas 1-3: Análise e Plano

### Problemas Identificados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REDUNDÂNCIAS DETECTADAS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. DETECÇÃO DE SKILLS DUPLICADA                                            │
│     ├── Etapa 1: JD parsing extrai skills do texto                          │
│     ├── Etapa 2: Learning Hub sugere skills da empresa                      │
│     └── Resultado: mesmas skills podem aparecer 2x                          │
│                                                                              │
│  2. SENIORITY PERGUNTADO MÚLTIPLAS VEZES                                    │
│     ├── Etapa 1: Detectado do JD                                            │
│     ├── Etapa 2: Confirmado/ajustado                                        │
│     └── Resultado: pergunta redundante se já detectado                      │
│                                                                              │
│  3. DEPARTAMENTO/ÁREA                                                        │
│     ├── Etapa 1: Pode ser inferido do título                                │
│     ├── Etapa 2: Perguntado novamente                                       │
│     └── Resultado: UX repetitiva                                            │
│                                                                              │
│  STATUS: 🟡 PARCIALMENTE RESOLVIDO                                          │
│  ├── get_skills_without_duplicates() implementado                           │
│  └── Falta integrar no frontend do wizard                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Plano de Refatoração

| Fase | Ação | Esforço | Impacto |
|------|------|---------|---------|
| 1 | Integrar `get_skills_without_duplicates()` no Stage 2 | Baixo | Alto |
| 2 | Pular confirmação de seniority se confiança > 90% | Baixo | Médio |
| 3 | Consolidar detecção de departamento em único ponto | Médio | Médio |
| 4 | Adicionar flag `skip_confirmation_if_confident` | Baixo | Alto |

**Endpoint a usar:**
```
POST /api/v1/lia/learning/skills-deduplicated
Body: {
    "company_id": "uuid",
    "role": "Backend Developer",
    "seniority": "senior",
    "already_selected_skills": ["Python", "Django"]
}
Response: {
    "skills": ["FastAPI", "PostgreSQL", "Redis"],  // sem duplicatas
    "source": "learning_hub"
}
```

---

## Otimização de Tokens: Estratégias Detalhadas

### 1. Cache de JD Templates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CACHE DE JD TEMPLATES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PROBLEMA:                                                                   │
│  - Cada parsing de JD consome ~1.500 tokens                                 │
│  - Vagas similares reprocessam prompts idênticos                            │
│                                                                              │
│  SOLUÇÃO:                                                                    │
│  - Cache de templates de JD por (role, seniority, department)               │
│  - TTL: 7 dias ou até atualização de configuração                           │
│  - Hash key: SHA256(role + seniority + company_id)                          │
│                                                                              │
│  ECONOMIA ESTIMADA: 30-40% dos tokens de parsing                            │
│                                                                              │
│  IMPLEMENTAÇÃO:                                                              │
│  ```python                                                                   │
│  class JDTemplateCache:                                                      │
│      async def get_or_create_template(                                      │
│          self, role: str, seniority: str, company_id: str                   │
│      ) -> JDTemplate:                                                        │
│          cache_key = self._generate_key(role, seniority, company_id)        │
│          cached = await self.redis.get(cache_key)                           │
│          if cached:                                                          │
│              return JDTemplate.parse_raw(cached)                            │
│          template = await self._generate_template(role, seniority)          │
│          await self.redis.setex(cache_key, 604800, template.json())         │
│          return template                                                     │
│  ```                                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Cache de Embeddings

| Componente | Tokens Salvos | TTL |
|------------|---------------|-----|
| Skills embeddings | ~200/skill | 30 dias |
| JD section embeddings | ~500/seção | 7 dias |
| Candidate CV embeddings | ~1000/CV | 90 dias |

### 3. Batch Processing

```python
# Atual: 1 chamada por candidato
for candidate in candidates:
    score = await llm.evaluate(candidate, job)  # 500 tokens × N

# Otimizado: batch de 5-10 candidatos
batches = chunk(candidates, size=5)
for batch in batches:
    scores = await llm.evaluate_batch(batch, job)  # 2000 tokens (vs 2500)
```

**Economia estimada:** 15-20% em avaliações em lote

### 4. Fallback Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESTRATÉGIA DE FALLBACK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PRIORIDADE 1: Cache local                                                  │
│  ├── Verificar se resultado existe em cache                                 │
│  └── Se hit → retorna imediatamente (0 tokens)                              │
│                                                                              │
│  PRIORIDADE 2: Regras estáticas                                             │
│  ├── Taxonomias locais (skills, títulos, indústrias)                        │
│  ├── Boolean query builder                                                   │
│  └── Se match suficiente → usar sem LLM (0 tokens)                          │
│                                                                              │
│  PRIORIDADE 3: LLM leve (Gemini Flash)                                      │
│  ├── Para expansão semântica                                                │
│  ├── Custo: ~0.0001$/1K tokens                                              │
│  └── Latência: <300ms                                                       │
│                                                                              │
│  PRIORIDADE 4: LLM completo (Claude Sonnet)                                 │
│  ├── Para análise profunda (rubricas, WSI)                                  │
│  ├── Custo: ~0.003$/1K tokens                                               │
│  └── Latência: 2-5 segundos                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Próximos Passos: Breakdown Técnico Detalhado

### 1. Dashboard Analytics (Frontend) - PRIORIDADE ALTA

| Task | Descrição | Esforço | Deps |
|------|-----------|---------|------|
| 1.1 | Criar componente `LearningDashboard.tsx` | 2h | - |
| 1.2 | Integrar com `/api/v1/lia/learning/learning-dashboard` | 1h | 1.1 |
| 1.3 | Criar visualização de health score (gauge chart) | 2h | 1.2 |
| 1.4 | Criar tabela de skills com confirmation rate | 2h | 1.2 |
| 1.5 | Criar gráficos de tendência (últimos 30 dias) | 3h | 1.2 |
| 1.6 | Adicionar filtros (role, seniority, período) | 2h | 1.5 |
| **Total** | | **12h** | |

**Componentes necessários:**
- `LearningDashboard.tsx` - Container principal
- `HealthScoreGauge.tsx` - Gauge chart
- `SkillsConfirmationTable.tsx` - Tabela de skills
- `LearningTrendChart.tsx` - Gráficos de linha

### 2. Otimização de Tokens (Cache de JD) - ✅ IMPLEMENTADO

| Task | Descrição | Status |
|------|-----------|--------|
| 2.1 | Criar `JDTemplateCache` service | ✅ Concluído |
| 2.2 | Implementar Redis integration | ✅ Concluído |
| 2.3 | Integrar com `job_intake_agent.py` | ✅ Concluído |
| 2.4 | Adicionar métricas de cache hit/miss | ✅ Concluído |
| 2.5 | Criar endpoint de invalidação manual | ✅ Concluído |

**Arquivos criados/modificados:**
- `app/services/jd_template_cache_service.py` - Novo serviço de cache
- `app/agents/specialized/job_intake_agent.py` - Integração com cache

**Funcionalidades:**
- Cache Redis/Memory com TTL configurável (24h padrão)
- Métricas de hit/miss rate disponíveis via `get_metrics()`
- Indicador "⚡ (cache)" na resposta quando usando dados cacheados
- Invalidação por empresa ou por chave específica

**Endpoints:**
- `DELETE /api/v1/cache/jd/{company_id}` - Invalida cache da empresa
- `GET /api/v1/cache/jd/metrics` - Métricas de performance
- `POST /api/v1/cache/jd/reset-metrics` - Reseta contadores

### 3. Refatoração UX Etapas 1-3 - ✅ IMPLEMENTADO

| Task | Descrição | Status |
|------|-----------|--------|
| 3.1 | Integrar `get_skills_without_duplicates` no wizard | ✅ Concluído |
| 3.2 | Adicionar flag `skip_if_confident` ao stage config | ✅ Concluído |
| 3.3 | Refatorar StageController para pular etapas | ✅ Concluído |
| 3.4 | Atualizar testes E2E | 🟡 Pendente |
| 3.5 | QA e ajustes | 🟡 Pendente |

**Arquivos modificados:**
- `app/agents/specialized/job_intake_agent.py` - Stage configs com skip_if_confident
- `app/services/learning_hub_service.py` - Método should_skip_stage_with_learning()
- `app/api/v1/lia_assistant.py` - WizardStepResponse com stage_skipped

**Configuração por Stage:**
- Stage 2: `skip_if_confident=true`, threshold 85%
- Stage 3: `skip_if_confident=true`, threshold 80%, `use_skills_deduplication=true`

### 4. Conector Teams → WhatsApp Screening - ✅ IMPLEMENTADO

| Task | Descrição | Status |
|------|-----------|--------|
| 4.1 | Criar endpoint `/api/v1/teams/webhook` | ✅ Concluído |
| 4.2 | Parsear ações de Adaptive Cards | ✅ Concluído |
| 4.3 | Conectar action "Aprovar" → `start_screening` | ✅ Concluído |
| 4.4 | Adicionar confirmação de segurança | ✅ Concluído |
| 4.5 | Testes de integração | ✅ 20 testes |

**Arquivos criados/modificados:**
- `app/api/v1/teams.py` - Webhook endpoint
- `tests/test_teams_webhook.py` - 20 testes de integração

**Endpoints:**
- `POST /api/v1/teams/webhook` - Receber ações de Adaptive Cards
- `GET /api/v1/teams/webhook/audit-logs` - Logs de auditoria

**Segurança:**
- Validação HMAC-SHA256 via `X-Teams-Signature` header
- Requer `TEAMS_WEBHOOK_SECRET` em produção (retorna 403 se não configurado)
- Audit logs persistidos no banco de dados PostgreSQL
- Modelo TeamsActionAuditLog para compliance e auditoria

### 5. Detecção Automática de Idiomas - ✅ IMPLEMENTADO

| Task | Descrição | Status |
|------|-----------|--------|
| 5.1 | Adicionar detecção de idioma ao parsing de JD | ✅ Concluído |
| 5.2 | Salvar idioma detectado no JobDraft | ✅ Concluído |
| 5.3 | Usar idioma para localizar prompts | ✅ Concluído |

**Arquivos modificados:**
- `app/agents/specialized/job_intake_agent.py` - Prompts multilíngues (EN/PT/ES)
- `app/models/job_draft.py` - Campo detected_language
- `alembic/versions/004_add_detected_language_to_job_draft.py` - Migration

**Método de detecção:**
- Usa função `detect_language()` de `input_validation.py` (keyword-based)
- Analisa indicadores linguísticos (PT_INDICATORS, EN_INDICATORS, ES_INDICATORS)
- Não requer dependência externa (langdetect)

**Idiomas suportados:**
- `pt-BR`: Português (Brasil) - padrão/fallback
- `en-US`: Inglês (Estados Unidos)
- `es`: Espanhol

---

## Diagnóstico e Recomendações

### Status Geral: 99% Completo

| Área | Status | Observação |
|------|--------|------------|
| Learning Hub Infrastructure | ✅ Completo | Modelos, serviço, endpoints |
| Integração com Agentes | ✅ Completo | Sourcing, WSI Evaluator |
| Wizard 7 Etapas | ✅ Completo | Consolidado de 10 para 7 |
| Field Toggles System | ✅ Completo | Controle de consumo de dados |
| Empty Field Notifications | ✅ Completo | Notificações no chat |
| Outcome Learning | ✅ Completo | job-outcome, outcome-insights |
| Stage Feedback | ✅ Completo | stage-feedback, analytics |
| Feature Flags | ✅ Completo | 8 flags com rollout gradual |
| Skills Deduplication | ✅ Completo | Remove redundância |
| Analytics Dashboard (API) | ✅ Completo | learning-dashboard, health score |
| Analytics Dashboard (UI) | 🟡 Pendente | Baixa prioridade |
| JD Template Cache | ✅ Completo | Redis + métricas (Jan/2026) |
| Refatoração UX Etapas 1-3 | ✅ Completo | skip_if_confident + learning (Jan/2026) |
| Teams → WhatsApp Connector | ✅ Completo | Webhook + 20 testes (Jan/2026) |
| Detecção de Idiomas | ✅ Completo | PT-BR, EN-US, ES (Jan/2026) |

### Pontos Fortes

1. **Learning Hub robusto** - 5 fases cobrindo todo o ciclo
2. **Integração completa com agentes** - Sourcing e WSI Evaluator funcionais
3. **Personalização por empresa** - Field Toggles e Feature Flags
4. **Transparência** - Origens de campos auto-preenchidos expostas
5. **Feedback loop** - Sistema aprende com correções do recrutador
6. **Otimização de tokens** - JDTemplateCache reduz chamadas LLM redundantes
7. **UX inteligente** - Wizard pula etapas quando LIA tem confiança alta
8. **Multilíngue** - Suporte automático a PT-BR, EN-US e ES

### Próximos Passos Sugeridos

| Prioridade | Item | Esforço | Status |
|------------|------|---------|--------|
| Alta | Dashboard Analytics (Frontend) | Médio | 🟡 Pendente |
| ~~Média~~ | ~~Otimização de tokens (cache de JD)~~ | ~~Baixo~~ | ✅ Implementado |
| ~~Média~~ | ~~Refatoração UX Etapas 1-3~~ | ~~Alto~~ | ✅ Implementado |
| ~~Baixa~~ | ~~Detecção automática de idiomas~~ | ~~Baixo~~ | ✅ Implementado |
| ~~Média~~ | ~~Conector Teams → WhatsApp~~ | ~~Médio~~ | ✅ Implementado |
| Baixa | Integração com mais job boards | Médio | 🟡 Pendente |
| Baixa | Testes E2E para skip de etapas | Baixo | 🟡 Pendente |

---

## Arquivos Chave

### Backend

| Arquivo | Responsabilidade |
|---------|------------------|
| `lia-agent-system/app/models/company_learning.py` | Modelos de aprendizado |
| `lia-agent-system/app/models/feedback_learning.py` | JobOutcome model |
| `lia-agent-system/app/services/learning_hub_service.py` | Hub central de learning + skip_stage |
| `lia-agent-system/app/services/feature_flag_service.py` | Sistema de feature flags |
| `lia-agent-system/app/services/lia_field_config_service.py` | Configuração de campos |
| `lia-agent-system/app/services/llm.py` | Serviço de LLMs (Claude/Gemini) |
| `lia-agent-system/app/services/jd_template_cache_service.py` | **NOVO** Cache de extrações JD |
| `lia-agent-system/app/api/v1/lia_field_toggles.py` | Endpoints de toggles |
| `lia-agent-system/app/api/v1/lia_assistant.py` | Endpoints de learning + stage skip |
| `lia-agent-system/app/api/v1/teams.py` | **NOVO** Webhook Teams → WhatsApp |
| `lia-agent-system/app/agents/specialized/job_intake_agent.py` | Agente de criação de vagas + cache + idiomas |
| `lia-agent-system/app/agents/specialized/sourcing_agent.py` | Agente de sourcing |
| `lia-agent-system/app/agents/specialized/avaliador_wsi_agent.py` | Agente WSI |
| `lia-agent-system/tests/test_teams_webhook.py` | **NOVO** Testes do webhook Teams |

### Frontend

| Arquivo | Responsabilidade |
|---------|------------------|
| `plataforma-lia/src/hooks/use-empty-field-notifications.ts` | Hook de estado |
| `plataforma-lia/src/components/chat/empty-field-notification-message.tsx` | Componente UI |
| `plataforma-lia/src/components/pages/chat-page.tsx` | Integração no wizard |

---

*Documento consolidado em 28 de Janeiro de 2026*
