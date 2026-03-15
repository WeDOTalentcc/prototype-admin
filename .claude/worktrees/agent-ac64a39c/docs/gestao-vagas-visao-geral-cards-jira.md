# CARDS JIRA - GESTAO DE VAGAS (VISAO GERAL)

> **Total de Cards:** 129 cards (96 frontend + 15 backend Rails + 18 backend IA)  
> **Organizacao:** Por Epico/Funcionalidade  
> **Data:** 22 Janeiro 2026  
> **Atualizado:** 22 Janeiro 2026 - Cards IA implementados + correcoes wizard  
> **Baseado em:** Screenshot pagina Visao Geral - Gestao de Vagas  
> **Estimativa Total:** 7-8 sprints  
> **Metodologia IA:** LIA Unified Methodology (Pre-requisitos + Rubricas BARS + WSI + Calibration Loop) - Ver `docs/LIA_UNIFIED_METHODOLOGY.md`

---

## DOCUMENTOS RELACIONADOS

> **Referência rápida para o time de desenvolvimento consultar durante a implementação**

| Documento | Descrição | Atualização |
|-----------|-----------|-------------|
| `LIA_UNIFIED_METHODOLOGY.md` | Metodologia unificada 4 camadas (Pré-req + BARS + WSI + Calibração) | 22 Jan ✅ |
| `WSI_METHODOLOGY_REFERENCE.md` | Referência completa WSI (Bloom, Dreyfus, Big Five, CBI) | 22 Jan ✅ |
| `JOB_CREATION_WIZARD_FLOW.md` | Fluxo wizard conversacional 9 steps com Saturação e Governança | 22 Jan ✅ |
| `funil-talentos-ia-architecture.md` | Arquitetura IA do funil (agentes, saturação, governança, calibração) | 22 Jan ✅ |
| `funil-talentos-cards-jira.md` | Cards Jira do Funil de Talentos (complementar a este documento) | 22 Jan ✅ |
| `AI_STAGE_AUTOMATION_ARCHITECTURE.md` | Arquitetura de automação de estágios com IA | 19 Jan ⚠️ |
| `CANDIDATE_STATUS_REFERENCE.md` | Referência completa de status e sub-status de candidatos dentro da vaga | 19 Jan ⚠️ |
| `gestao-vagas-fluxos.md` | Fluxos de usuário da gestão de vagas (UX/UI patterns) | 12 Dez ❌ |
| `DATABASE_FIELDS_REFERENCE.md` | Mapeamento completo de campos do banco de dados (65 tabelas) | 22 Jan ✅ |
| `COMPANY_DEFAULTS_SYNC_ARCHITECTURE.md` | Arquitetura de pré-preenchimento inteligente com defaults da empresa | 22 Jan ✅ |
| `SETTINGS_MENU_MAPPING_FOR_WIZARD.md` | Mapeamento completo do menu Configurações para consumo no Wizard | 22 Jan ✅ |

**Legenda:** ✅ Atualizado | ⚠️ Revisar | ❌ Desatualizado

---

## CONTEXTO DE USO DOS CARDS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AMBIENTE ATUAL (Prototipo/Referencia)    →    AMBIENTE PRODUCAO (Time)    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FRONTEND                                                                   │
│  plataforma-lia/                               Stack Producao:              │
│  ├── Next.js + React + TypeScript      →       ├── Vue.js + Vuetify         │
│  ├── Tailwind CSS + shadcn/ui                  ├── Nuxt.js                  │
│  └── Drizzle ORM                               └── CSS Framework            │
│                                                                              │
│  BACKEND CRUD/API                                                           │
│  (Endpoints REST para CRUD de vagas)           Stack Producao:              │
│  ├── Python + FastAPI                  →       ├── Ruby on Rails 7          │
│  └── SQLAlchemy                                └── ActiveRecord             │
│                                                                              │
│  BACKEND IA (MESMO STACK)                                                   │
│  lia-agent-system/                             Stack Producao:              │
│  ├── Python + FastAPI                  =       ├── Python + FastAPI         │
│  ├── LangGraph + Gemini                        ├── LangGraph + Gemini       │
│  └── Agentes Especializados                    └── Agentes Especializados   │
│                                                                              │
│  PROPOSITO: Estes cards servem como ESPECIFICACAO para o time              │
│  replicar as funcionalidades no stack de producao.                         │
│                                                                              │
│  STATUS DOS CARDS:                                                          │
│  • "Implementado" = Funcional aqui, pronto para replicar/usar              │
│  • "Pendente" = Ainda nao replicado no stack de producao                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## RESUMO EXECUTIVO

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              VISAO GERAL - GESTAO DE VAGAS                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   EPIC-VAG-001: Header & Navegacao           EPIC-VAG-002: Filtros por Status           │
│   ─────────────────────────────              ──────────────────────────────              │
│   4 cards | Sprint 1                          7 cards | Sprint 1-2                       │
│                                                                                          │
│   ├── VAG-001: Header principal               ├── VAG-005: Tabs de filtro               │
│   ├── VAG-002: Botao Nova Vaga                ├── VAG-006: Contador por status          │
│   ├── VAG-003: Busca global                   ├── VAG-007: Filtro Todas                 │
│   └── VAG-004: Notificacoes                   ├── VAG-008: Filtro Ativas                │
│                                               ├── VAG-009: Filtro Urgentes              │
│                                               ├── VAG-010: Filtro Paralisadas           │
│                                               └── VAG-011: Filtro Concluidas/Canceladas │
│                                                                                          │
│   EPIC-VAG-003: LIA Prompt Central           EPIC-VAG-004: Quick Actions                │
│   ────────────────────────────               ────────────────────────                    │
│   6 cards | Sprint 2                          5 cards | Sprint 2                         │
│                                                                                          │
│   ├── VAG-012: Container LIA central          ├── VAG-018: Criar nova vaga              │
│   ├── VAG-013: Titulo contextual              ├── VAG-019: Ver minhas vagas             │
│   ├── VAG-014: Input de chat                  ├── VAG-020: Ver todas as vagas           │
│   ├── VAG-015: Icones mic/busca               ├── VAG-021: Resumo das vagas             │
│   ├── VAG-016: Sugestoes contextuais          └── VAG-022: Mais ideias (AI)             │
│   └── VAG-017: Integracao backend LIA                                                   │
│                                                                                          │
│   EPIC-VAG-005: Pagina Vazia/Onboarding      EPIC-VAG-006: Tabela de Vagas              │
│   ─────────────────────────────────          ─────────────────────────────              │
│   2 cards | Sprint 3                          9 cards | Sprint 4                         │
│                                                                                          │
│   ├── VAG-023: Empty state design             ├── VAG-028: Tabela estrutura base        │
│   └── VAG-024: Mensagem boas-vindas           ├── VAG-029: Colunas configuraveis        │
│                                               ├── VAG-030: Ordenacao multi-coluna       │
│   EPIC-VAG-007: Preview da Vaga              ├── VAG-031: Resize colunas                │
│   ─────────────────────────────              ├── VAG-032: Selecao em lote               │
│   11 cards | Sprint 4                         ├── VAG-033: Persistencia config          │
│                                               ├── VAG-034: Coluna Performance LIA       │
│   ├── VAG-037: Preview Panel base             ├── VAG-035: Coluna Roteiro Triagem       │
│   ├── VAG-038: Tab Visao Geral Funil          └── VAG-036: Acoes por linha              │
│   ├── VAG-039: Tab Metricas LIA                                                         │
│   ├── VAG-040: Tab Responsaveis              EPIC-VAG-008: Modais Acao Lote             │
│   ├── VAG-041: Tab Datas Criticas            ───────────────────────────                │
│   ├── VAG-042: WSI Blocks                     9 cards | Sprint 5                         │
│   ├── VAG-043: WSI Accordion                                                            │
│   ├── VAG-044: Editor Perguntas               ├── VAG-048: JobActionsBar                │
│   ├── VAG-045: Config Canais Triagem          ├── VAG-049: JobPublishModal              │
│   ├── VAG-046: Processo Breadcrumb            ├── VAG-050: JobInsightsModal             │
│   └── VAG-047: Resize Preview                 ├── VAG-051: JobDuplicateModal            │
│                                               ├── VAG-052: JobStatusModal               │
│   EPIC-VAG-009: Filtros e Busca              ├── VAG-053: JobAssignRecruiterModal       │
│   ─────────────────────────────              ├── VAG-054: JobUnpublishModal             │
│   9 cards | Sprint 4                          ├── VAG-055: JobCompareModal              │
│                                               └── VAG-056: EditJobModal                 │
│   ├── VAG-057: JobFiltersPanel                                                          │
│   ├── VAG-058: Filtros rapidos               EPIC-VAG-010: Chat LIA Multi-Nivel         │
│   ├── VAG-059: Filtro por status             ─────────────────────────────              │
│   ├── VAG-060: Filtro por etapa               9 cards | Sprint 5                         │
│   ├── VAG-061: Filtro modelo trabalho                                                   │
│   ├── VAG-062: Filtro recrutador/gestor       ├── VAG-066: Mini Prompt Inline           │
│   ├── VAG-063: Busca booleana                 ├── VAG-067: Chat Expandido Lateral       │
│   ├── VAG-064: Pesquisas salvas               ├── VAG-068: Super Chat Criacao           │
│   └── VAG-065: Persistencia filtros           ├── VAG-069: Deteccao Intent              │
│                                               ├── VAG-070: Auto-Expand LIA              │
│   EPIC-VAG-011: Job Creation Wizard          ├── VAG-071: Historico Mensagens          │
│   ─────────────────────────────              ├── VAG-072: AudioRecordButton             │
│   19 cards | Sprint 6                         ├── VAG-073: LiaQueriesGuide              │
│                                               └── VAG-074: ExpandedChatModal            │
│   ├── VAG-075: Botao Nova Vaga Header                                                   │
│   ├── VAG-076: Super Chat Container                                                     │
│   ├── VAG-077-087: Wizard Steps 1-11                                                    │
│   ├── VAG-088: Backend Endpoint                                                         │
│   ├── VAG-089: Navegacao Stepper                                                        │
│   ├── VAG-090: Calibracao Candidatos                                                    │
│   ├── VAG-091: ScreeningQuestionsPanel                                                  │
│   ├── VAG-092: Integracao Pearch                                                        │
│   └── VAG-093: Validacao Zod                                                            │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## INTEGRACOES EXTERNAS UTILIZADAS

### LLMs e AI

| Integracao | Tipo | Cards Relacionados | Custo Estimado |
|------------|------|-------------------|----------------|
| **Anthropic Claude 4 Sonnet** | LLM Principal | VAG-017, VAG-021, VAG-022 | $3-15/1M tokens |
| **Google Gemini 1.5 Flash** | LLM Fallback/Voice | VAG-015, VAG-017 | $0.075-0.30/1M tokens |
| **LangGraph** | Orquestrador AI | VAG-017 | Open Source |

### Voice & Audio

| Integracao | Tipo | Cards Relacionados | Custo Estimado |
|------------|------|-------------------|----------------|
| **Web Speech API** | Browser Voice | VAG-015 | Gratuito |
| **Deepgram** | Voice-to-Text (alt) | VAG-015 | ~$0.0043/min |

### Banco de Dados & Cache

| Integracao | Tipo | Cards Relacionados | Custo Estimado |
|------------|------|-------------------|----------------|
| **PostgreSQL (Neon)** | Banco Principal | VAG-006, VAG-007-011, VAG-017 | Incluso Replit |
| **Redis** | Cache/Sessions | VAG-022 | Interno |
| **Drizzle ORM** | ORM TypeScript | Todos com dados | Open Source |
| **SQLAlchemy** | ORM Python | VAG-006, VAG-017 | Open Source |

### Autenticacao & Seguranca

| Integracao | Tipo | Cards Relacionados | Custo Estimado |
|------------|------|-------------------|----------------|
| **WorkOS** | SSO/SCIM/MFA | VAG-004 | ~$125/mo base |
| **JWT** | Auth Tokens | Todos | Interno |

### Agentes LIA (Multi-Agent System) - IMPLEMENTADO

| Servico/Agente | Arquivo | Cards Relacionados | Funcao Principal |
|----------------|---------|-------------------|------------------|
| **IntentClassifierService** | intent_classifier.py | VAG-017 | Classificacao de intents do usuario |
| **salary_insights** | lia_assistant.py | VAG-017 | Benchmark salarial interno e de mercado |
| **skills_insights** | lia_assistant.py | VAG-017 | Analise de skills e requisitos |
| **time_insights** | lia_assistant.py | VAG-017 | Tempo de preenchimento de vagas |
| **process_explainer** | lia_assistant.py | VAG-017 | Explicacao do processo WSI |
| **general_assistant** | lia_assistant.py | VAG-017, VAG-021, VAG-022 | Respostas gerais via Gemini LLM |

> ✅ **STATUS**: Arquitetura implementada e funcional. Roteamento por tipo de pergunta (SALARY, SKILLS, TIME_TO_FILL, PROCESS, GENERAL) operacional.

### Comunicacao

| Integracao | Tipo | Cards Relacionados | Custo Estimado |
|------------|------|-------------------|----------------|
| **Twilio** | WhatsApp/SMS | Notificacoes | ~$0.005/msg |
| **SendGrid** | Email | Notificacoes | Tier gratuito |

### Secrets Necessarios

```
# LLMs (Via Replit Integration - ja configurados)
ANTHROPIC_API_KEY      
GEMINI_API_KEY         

# Banco de Dados (Via Replit - automatico)
DATABASE_URL           
PGHOST, PGUSER, PGPASSWORD, PGDATABASE

# Autenticacao
WORKOS_API_KEY         
WORKOS_CLIENT_ID       

# Comunicacao
TWILIO_ACCOUNT_SID     
TWILIO_AUTH_TOKEN      
TWILIO_PHONE_NUMBER    
SENDGRID_API_KEY       # Opcional

# Voice (Opcional)
DEEPGRAM_API_KEY       
```

---

## INDICE DE CARDS

### EPIC-VAG-001: Header & Navegacao (4 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-001 | Header Principal Gestao de Vagas | 3 | Alta |
| VAG-002 | Botao Nova Vaga | 5 | Critica |
| VAG-003 | Integracao Busca Global | 3 | Media |
| VAG-004 | Integracao Notificacoes | 3 | Media |

### EPIC-VAG-002: Filtros por Status (7 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-005 | Sistema de Tabs de Filtro | 8 | Alta |
| VAG-006 | Contadores Dinamicos por Status | 5 | Alta |
| VAG-007 | Filtro Todas as Vagas | 3 | Alta |
| VAG-008 | Filtro Vagas Ativas | 3 | Alta |
| VAG-009 | Filtro Vagas Urgentes | 5 | Alta |
| VAG-010 | Filtro Vagas Paralisadas | 3 | Media |
| VAG-011 | Filtro Concluidas e Canceladas | 3 | Baixa |

### EPIC-VAG-003: LIA Prompt Central (6 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-012 | Container LIA Centralizado | 8 | Critica |
| VAG-013 | Titulo Contextual Dinamico | 3 | Alta |
| VAG-014 | Input de Chat LIA | 8 | Critica |
| VAG-015 | Icones Microfone e Busca | 5 | Media |
| VAG-016 | Sugestoes Contextuais | 8 | Alta |
| VAG-017 | Integracao Backend LIA | 13 | Critica |

### EPIC-VAG-004: Quick Actions (5 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-018 | Acao Criar Nova Vaga | 5 | Critica |
| VAG-019 | Acao Ver Minhas Vagas | 3 | Alta |
| VAG-020 | Acao Ver Todas as Vagas | 3 | Alta |
| VAG-021 | Acao Resumo das Vagas | 5 | Media |
| VAG-022 | Acao Mais Ideias (AI) | 8 | Media |

### EPIC-VAG-005: Pagina Vazia/Onboarding (2 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-023 | Empty State Design | 5 | Alta |
| VAG-024 | Mensagem Boas-Vindas LIA | 3 | Alta |

### EPIC-VAG-006: Tabela de Vagas (9 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-028 | Tabela de Vagas - Estrutura Base | 8 | Critica |
| VAG-029 | Colunas Configuraveis Toggle/Order | 5 | Alta |
| VAG-030 | Ordenacao Multi-Coluna Sort | 3 | Alta |
| VAG-031 | Redimensionamento de Colunas | 5 | Media |
| VAG-032 | Selecao em Lote Checkbox | 5 | Alta |
| VAG-033 | Persistencia de Config localStorage | 3 | Media |
| VAG-034 | Coluna Performance LIA Triagens | 5 | Alta |
| VAG-035 | Coluna Roteiro de Triagem | 3 | Media |
| VAG-036 | Acoes por Linha Menu Dropdown | 5 | Alta |

### EPIC-VAG-007: Painel de Preview da Vaga (11 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-037 | Preview Panel - Estrutura Base | 8 | Critica |
| VAG-038 | Tab Visao Geral - Funil Rapido | 5 | Alta |
| VAG-039 | Tab Visao Geral - Metricas LIA | 5 | Alta |
| VAG-040 | Tab Visao Geral - Responsaveis | 3 | Media |
| VAG-041 | Tab Visao Geral - Datas Criticas | 3 | Media |
| VAG-042 | Tab Roteiro de Triagem - WSI Blocks | 13 | Critica |
| VAG-043 | WSI Blocks - Accordion Expansivel | 5 | Alta |
| VAG-044 | WSI Blocks - Editor de Perguntas | 8 | Alta |
| VAG-045 | Configuracao de Canais de Triagem | 5 | Alta |
| VAG-046 | Processo Seletivo Inline Breadcrumb | 3 | Media |
| VAG-047 | Resize do Painel de Preview | 3 | Baixa |

### EPIC-VAG-008: Modais de Acao em Lote (9 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-048 | JobActionsBar - Barra de Acoes | 5 | Alta |
| VAG-049 | JobPublishModal - Publicar em Canais | 8 | Alta |
| VAG-050 | JobInsightsModal - Metricas Expandidas | 13 | Critica |
| VAG-051 | JobDuplicateModal - Duplicar Vaga | 5 | Media |
| VAG-052 | JobStatusModal - Pausar/Ativar Vaga | 5 | Alta |
| VAG-053 | JobAssignRecruiterModal - Atribuir Recrutador | 5 | Media |
| VAG-054 | JobUnpublishModal - Despublicar Vaga | 5 | Baixa |
| VAG-055 | JobCompareModal - Comparar Vagas | 8 | Media |
| VAG-056 | EditJobModal - Edicao Completa | 13 | Critica |

### EPIC-VAG-009: Sistema de Filtros e Busca (9 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-057 | JobFiltersPanel - Painel Lateral | 8 | Alta |
| VAG-058 | Filtros Rapidos Ativas/Urgentes/Remotas | 3 | Alta |
| VAG-059 | Filtro por Status da Vaga | 3 | Alta |
| VAG-060 | Filtro por Etapa do Processo | 3 | Media |
| VAG-061 | Filtro por Modelo de Trabalho | 3 | Media |
| VAG-062 | Filtro por Recrutador/Gestor | 3 | Media |
| VAG-063 | Busca Booleana AND/OR/NOT | 5 | Baixa |
| VAG-064 | Pesquisas Salvas Templates | 5 | Media |
| VAG-065 | Persistencia de Filtros Hook | 3 | Alta |

### EPIC-VAG-010: Chat LIA Multi-Nivel (9 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-066 | Nivel 1 Mini Prompt Inline | 5 | Alta |
| VAG-067 | Nivel 2 Chat Expandido Lateral | 8 | Critica |
| VAG-068 | Nivel 3 Super Chat Criacao de Vaga | 13 | Critica |
| VAG-069 | Deteccao de Intent de Criacao | 5 | Alta |
| VAG-070 | Auto-Expand LIA ao Selecionar Vagas | 3 | Media |
| VAG-071 | Historico de Mensagens Inline | 3 | Media |
| VAG-072 | AudioRecordButton Gravacao de Voz | 5 | Media |
| VAG-073 | LiaVacancyQueriesGuide Popover | 5 | Alta |
| VAG-074 | ExpandedChatModal Modal Full | 8 | Critica |

### EPIC-VAG-011: Job Creation Wizard (19 cards)
| Card | Titulo | Pontos | Prioridade |
|------|--------|--------|------------|
| VAG-075 | Botao Nova Vaga Header | 3 | Alta |
| VAG-076 | Super Chat Modal Container | 8 | Critica |
| VAG-077 | Wizard Step 1 Descricao Inicial | 8 | Critica |
| VAG-078 | Wizard Step 2 Informacoes Basicas | 5 | Alta |
| VAG-079 | Wizard Step 3 Remuneracao e Beneficios | 5 | Alta |
| VAG-080 | Wizard Step 4 Competencias Tecnicas | 8 | Alta |
| VAG-081 | Wizard Step 5 Competencias WSI | 8 | Alta |
| VAG-082 | Wizard Step 6 Requisitos Idiomas | 5 | Media |
| VAG-083 | Wizard Step 7 Scorecard Avaliacao | 5 | Media |
| VAG-084 | Wizard Step 8 Prazos e Cronograma | 5 | Alta |
| VAG-085 | Wizard Step 9 Pipeline do Processo | 8 | Alta |
| VAG-086 | Wizard Step 10 Solicitacao de Dados | 5 | Media |
| VAG-087 | Wizard Step 11 Revisao Final | 8 | Critica |
| VAG-088 | [BACK] Endpoint /lia/job-wizard/step | 13 | Critica |
| VAG-089 | Navegacao entre Etapas Stepper | 5 | Alta |
| VAG-090 | Calibracao de Candidatos Sourcing | 8 | Alta |
| VAG-091 | ScreeningQuestionsPanel Perguntas | 8 | Alta |
| VAG-092 | Integracao com Busca Global Pearch | 8 | Alta |
| VAG-093 | Validacao de Dados Zod Schema | 3 | Media |

---

# EPIC-VAG-001: HEADER & NAVEGACAO

> **Responsavel:** Frontend Developer  
> **Sprint:** 1  
> **Pontos Total:** 19  
> **Foco:** Estrutura principal da pagina com header, botoes e indicadores

---

### CARD VAG-001: Header Principal Gestao de Vagas

```yaml
Titulo: [FRONT] Header Principal - Gestao de Vagas
Tipo: Feature
Sprint: 1
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-001

Descricao: |
  Implementar header principal da pagina de Gestao de Vagas
  com icone, titulo e alinhamento conforme design system.

Historia de Usuario: |
  Como recrutador, eu quero ver o titulo da pagina claramente
  identificado para saber onde estou na plataforma.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobsPageHeader
    - Icone: Building2 (Lucide) ou icone customizado
    - Titulo: "Gestao de Vagas"
    - Fonte: Open Sans 18px semibold
    - Cor: #2D2D2D (gray-950)
  Layout:
    - Position: Topo esquerdo
    - Padding: px-6 py-4
    - Flex: items-center gap-2

Design & Componentes:
  Componentes Existentes:
    - Icon wrapper com size props
    - Text heading component
  Design Tokens:
    - Text: --lia-text-primary (#2D2D2D)
    - Icon: --lia-text-secondary (#666666)
  Estados:
    - Default apenas

Criterios de Aceitacao:
  - [ ] Icone Building2 24px visivel
  - [ ] Titulo "Gestao de Vagas" visivel
  - [ ] Fonte Open Sans 18px semibold
  - [ ] Alinhamento correto com sidebar
  - [ ] Responsivo em tablets
```

---

### CARD VAG-002: Botao Nova Vaga

```yaml
Titulo: [FRONT] Botao Nova Vaga - CTA Principal
Tipo: Feature
Sprint: 1
Pontos: 5
Prioridade: Critica
Epic: EPIC-VAG-001

Descricao: |
  Implementar botao principal de criacao de vaga no header,
  com estilo cyan (#60BED1), icone plus e acao de abertura
  do wizard de criacao via LIA.

Historia de Usuario: |
  Como recrutador, eu quero criar uma nova vaga rapidamente
  clicando em um botao visivel no topo da pagina.

Requisitos Tecnicos:
  Frontend:
    - Componente: NewJobButton
    - Estilo: bg-[#60BED1] text-white rounded-lg
    - Icone: Plus (Lucide) 16px
    - Texto: "Nova Vaga"
    - Fonte: Open Sans 13px medium
    - Hover: opacity-90 ou bg-[#4FAABD]
  Acao:
    - onClick: Abrir ExpandedChatModal em modo job-creation
    - Props: isInJobCreationMode={true}
  Layout:
    - Position: Header direito (end)
    - Size: h-9 px-4
    - Shadow: shadow-sm

Design & Componentes:
  Componentes Existentes:
    - Button (shadcn) - variant customizado
  Design Tokens:
    - Background: --wedo-cyan (#60BED1)
    - Text: white
    - Hover: --wedo-cyan-hover (#4FAABD)
  Estados:
    - Default: bg-cyan text-white
    - Hover: levemente mais escuro
    - Active: scale-98
    - Loading: spinner + "Criando..."

Comportamento de UI:
  Fluxo Principal:
    1. Usuario clica no botao "Nova Vaga"
    2. Modal LIA abre em modo super-expandido
    3. Wizard de criacao de vaga inicia
    4. LIA guia o processo passo a passo

Criterios de Aceitacao:
  - [ ] Botao visivel no header direito
  - [ ] Cor cyan (#60BED1) correta
  - [ ] Icone Plus + texto "Nova Vaga"
  - [ ] Abre ExpandedChatModal corretamente
  - [ ] Estado hover funciona
  - [ ] Responsivo (apenas icone em mobile)
```

---

### CARD VAG-003: Integracao Busca Global

```yaml
Titulo: [FRONT] Integracao Busca Global - Header Icon
Tipo: Feature
Sprint: 1
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-001

Descricao: |
  Integrar icone de busca global no header da pagina de vagas,
  conectando com o GlobalSearchModal existente.

Historia de Usuario: |
  Como recrutador, eu quero buscar vagas, candidatos ou qualquer
  coisa rapidamente usando a busca global.

Requisitos Tecnicos:
  Frontend:
    - Componente: GlobalSearchButton (reutilizar)
    - Icone: Search (Lucide) 20px
    - Cor: #666666 (gray-500)
  Acao:
    - onClick: Abrir GlobalSearchModal
    - Atalho: Cmd+K / Ctrl+K
  Layout:
    - Position: Header direito, antes de notificacoes
    - Size: 40px button area

Design & Componentes:
  Componentes Existentes:
    - GlobalSearchModal (ja existe)
    - IconButton
  Estados:
    - Default: icon gray-500
    - Hover: bg-gray-100, icon gray-700

Criterios de Aceitacao:
  - [ ] Icone de busca visivel no header
  - [ ] Abre GlobalSearchModal ao clicar
  - [ ] Atalho Cmd+K funciona
  - [ ] Tooltip "Buscar (Cmd+K)"
```

---

### CARD VAG-004: Integracao Notificacoes

```yaml
Titulo: [FRONT] Integracao Notificacoes - Bell Icon
Tipo: Feature
Sprint: 1
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-001

Descricao: |
  Integrar icone de notificacoes no header com badge de contador
  de nao lidas e dropdown de notificacoes recentes.

Historia de Usuario: |
  Como recrutador, eu quero ver rapidamente se tenho
  notificacoes novas relacionadas as vagas.

Requisitos Tecnicos:
  Frontend:
    - Componente: NotificationBell (reutilizar)
    - Icone: Bell (Lucide) 20px
    - Badge: Contador vermelho se > 0
  Backend:
    - GET /api/v1/notifications?unread=true
  Layout:
    - Position: Header direito, ultimo antes do avatar

Design & Componentes:
  Componentes Existentes:
    - NotificationDropdown (ja existe)
    - Badge counter
  Estados:
    - Default: icon gray-500
    - Com notificacoes: badge vermelho
    - Hover: bg-gray-100

Criterios de Aceitacao:
  - [ ] Icone Bell visivel no header
  - [ ] Badge vermelho com contador
  - [ ] Dropdown abre ao clicar
  - [ ] Marca como lido ao visualizar
```

---

# EPIC-VAG-002: FILTROS POR STATUS

> **Responsavel:** Full-Stack Developer  
> **Sprint:** 1-2  
> **Pontos Total:** 30  
> **Foco:** Sistema de tabs de filtro com contadores dinamicos

---

### CARD VAG-005: Sistema de Tabs de Filtro

```yaml
Titulo: [FULL] Sistema de Tabs de Filtro por Status
Tipo: Feature
Sprint: 1
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-002

Descricao: |
  Implementar sistema de tabs horizontais para filtrar vagas
  por status, com design ElevenLabs (monocromatico + accent).

Historia de Usuario: |
  Como recrutador, eu quero filtrar vagas por status
  para focar nas que precisam de atencao.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobStatusTabs
    - Tabs: Visao Geral | Todas | Ativas | Urgentes | Paralisadas | Concluidas | Canceladas
    - Estilo: Underline tabs com contador
    - Font: Open Sans 12px
  Backend:
    - GET /api/v1/job-vacancies/counts-by-status
    - Retorna: { active: 9, urgent: 5, paused: 1, completed: 5, cancelled: 0 }
  State:
    - useState: activeTab
    - useSearchParams: persistir na URL

Design & Componentes:
  Componentes Existentes:
    - Tabs (shadcn) - modificado
  Design Tokens:
    - Tab default: text-gray-500
    - Tab active: text-gray-900, border-b-2 border-gray-900
    - Counter: text-gray-500 ml-1.5
  Layout:
    - Position: Abaixo do header
    - Padding: px-6
    - Height: h-10
    - Overflow: scroll horizontal em mobile

Comportamento de UI:
  Fluxo Principal:
    1. Usuario ve todas as tabs com contadores
    2. Tab ativa tem underline escuro
    3. Click em tab filtra a lista
    4. URL atualiza para refletir filtro

Criterios de Aceitacao:
  - [ ] Todas as 7 tabs visiveis
  - [ ] Contadores dinamicos ao lado
  - [ ] Tab ativa com underline
  - [ ] Filtro persiste na URL
  - [ ] Scroll horizontal mobile
  - [ ] Loading state nos contadores
```

---

### CARD VAG-006: Contadores Dinamicos por Status

```yaml
Titulo: [BACK] API Contadores de Vagas por Status
Tipo: Feature
Sprint: 1
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-002

Descricao: |
  Implementar endpoint que retorna contagem de vagas
  agrupadas por status para alimentar as tabs.

Historia de Usuario: |
  Como recrutador, eu quero ver quantas vagas tenho
  em cada status sem precisar abrir cada filtro.

Requisitos Tecnicos:
  Backend:
    - Endpoint: GET /api/v1/job-vacancies/counts-by-status
    - Query: company_id (do token)
    - Response:
      ```json
      {
        "total": 22,
        "active": 9,
        "urgent": 5,
        "paused": 1,
        "completed": 5,
        "cancelled": 0
      }
      ```
  Database:
    - Query agregada por status
    - Filtro por company_id
    - Cache: 30s (opcional)

Criterios de Aceitacao:
  - [ ] Endpoint retorna contagens corretas
  - [ ] Filtrado por company do usuario
  - [ ] Response < 100ms
  - [ ] Trata vagas sem status
```

---

### CARD VAG-007: Filtro Todas as Vagas

```yaml
Titulo: [FRONT] Tab Todas - Listagem Completa
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-002

Descricao: |
  Implementar visualizacao de todas as vagas quando
  tab "Todas" esta selecionada, com paginacao.

Historia de Usuario: |
  Como recrutador, eu quero ver todas as vagas da empresa
  independente do status.

Requisitos Tecnicos:
  Frontend:
    - Lista todas as vagas
    - Paginacao: 20 por pagina
    - Ordenacao: created_at DESC
  Backend:
    - GET /api/v1/job-vacancies?limit=20&offset=0

Criterios de Aceitacao:
  - [ ] Lista todas as vagas
  - [ ] Paginacao funciona
  - [ ] Ordenacao por data
  - [ ] Empty state se nenhuma vaga
```

---

### CARD VAG-008: Filtro Vagas Ativas

```yaml
Titulo: [FRONT] Tab Ativas - Vagas em Andamento
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-002

Descricao: |
  Implementar filtro para mostrar apenas vagas com
  status "active" ou "open".

Historia de Usuario: |
  Como recrutador, eu quero ver apenas vagas ativas
  para focar nas que estao em andamento.

Requisitos Tecnicos:
  Frontend:
    - Filtro: status IN ['active', 'open', 'in_progress']
  Backend:
    - GET /api/v1/job-vacancies?status=active

Criterios de Aceitacao:
  - [ ] Mostra apenas vagas ativas
  - [ ] Contador correto na tab
  - [ ] Transicao suave entre tabs
```

---

### CARD VAG-009: Filtro Vagas Urgentes

```yaml
Titulo: [FRONT] Tab Urgentes - Vagas Prioritarias
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-002

Descricao: |
  Implementar filtro para vagas marcadas como urgentes
  ou com deadline proximo (< 7 dias).

Historia de Usuario: |
  Como recrutador, eu quero ver vagas urgentes primeiro
  para nao perder prazos importantes.

Requisitos Tecnicos:
  Frontend:
    - Filtro: urgency_level = 'high' OR deadline < NOW() + 7 days
    - Badge vermelho no card
  Backend:
    - GET /api/v1/job-vacancies?urgency=high

Regras de Negocio:
  Vaga e urgente se:
    - urgency_level = 'high' ou 'critical'
    - deadline em menos de 7 dias
    - priority = 'urgent'
    - Marcada manualmente como urgente

Criterios de Aceitacao:
  - [ ] Filtra vagas urgentes corretamente
  - [ ] Inclui vagas com deadline proximo
  - [ ] Badge visual de urgencia
  - [ ] Ordenacao por deadline ASC
```

---

### CARD VAG-010: Filtro Vagas Paralisadas

```yaml
Titulo: [FRONT] Tab Paralisadas - Vagas On-Hold
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-002

Descricao: |
  Implementar filtro para vagas com status paralisado/pausado,
  com indicacao do motivo quando disponivel.

Historia de Usuario: |
  Como recrutador, eu quero ver vagas paralisadas
  para decidir se reativo ou cancelo.

Requisitos Tecnicos:
  Frontend:
    - Filtro: status = 'paused' OR 'on_hold'
    - Mostrar motivo da pausa se disponivel
  Backend:
    - GET /api/v1/job-vacancies?status=paused

Criterios de Aceitacao:
  - [ ] Filtra vagas paralisadas
  - [ ] Mostra motivo da pausa
  - [ ] Acao rapida para reativar
```

---

### CARD VAG-011: Filtro Concluidas e Canceladas

```yaml
Titulo: [FRONT] Tab Concluidas/Canceladas - Historico
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Baixa
Epic: EPIC-VAG-002

Descricao: |
  Implementar filtros para vagas concluidas (contratacao feita)
  e canceladas (vaga fechada sem contratacao).

Historia de Usuario: |
  Como recrutador, eu quero ver historico de vagas
  para consultar processos anteriores.

Requisitos Tecnicos:
  Frontend:
    - Tab Concluidas: status = 'completed' ou 'filled'
    - Tab Canceladas: status = 'cancelled' ou 'closed'
  Backend:
    - GET /api/v1/job-vacancies?status=completed
    - GET /api/v1/job-vacancies?status=cancelled

Criterios de Aceitacao:
  - [ ] Ambas as tabs funcionam
  - [ ] Data de conclusao/cancelamento visivel
  - [ ] Acao para duplicar vaga concluida
```

---

# EPIC-VAG-003: LIA PROMPT CENTRAL

> **Responsavel:** Full-Stack Developer  
> **Sprint:** 2  
> **Pontos Total:** 45  
> **Foco:** Componente central de interacao com LIA na pagina de vagas

---

### CARD VAG-012: Container LIA Centralizado

```yaml
Titulo: [FRONT] Container LIA Centralizado - Layout Principal
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Critica
Epic: EPIC-VAG-003

Descricao: |
  Implementar container centralizado para o prompt da LIA
  na pagina de visao geral, seguindo design specs v3.1.

Historia de Usuario: |
  Como recrutador, eu quero ver a LIA em destaque
  para interagir facilmente com a assistente.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobsLIAPromptContainer
    - Position: Centro da pagina (empty state)
    - Width: max-w-2xl
    - Background: white
    - Border: 1px solid #E5E7EB
    - Border-radius: rounded-xl
    - Shadow: shadow-sm
  Layout:
    - Vertical center quando sem vagas
    - Padding: p-6
    - Margin: mx-auto

Design & Componentes:
  Seguir: lia-prompt-design-specs.md
  Design Tokens:
    - Background: white
    - Border: --lia-border-subtle (#E5E7EB)
    - Shadow: --lia-shadow-sm
  Estados:
    - Compact: Apenas input
    - Expanded: Com quick actions
    - Super-expanded: Modal full

Criterios de Aceitacao:
  - [ ] Container centralizado
  - [ ] Border e shadow corretos
  - [ ] Responsivo em todas as telas
  - [ ] Transicao suave entre estados
```

---

### CARD VAG-013: Titulo Contextual Dinamico

```yaml
Titulo: [FRONT] Titulo Contextual LIA - Mensagem Dinamica
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-003

Descricao: |
  Implementar titulo dinamico acima do prompt que muda
  conforme contexto (primeira visita, vagas abertas, etc).

Historia de Usuario: |
  Como recrutador, eu quero ver mensagens contextuais
  da LIA que sejam relevantes para minha situacao.

Requisitos Tecnicos:
  Frontend:
    - Componente: LIAContextTitle
    - Icone: Brain (Lucide) 24px cyan
    - Texto: dinamico baseado em contexto
    - Fonte: Open Sans 16px semibold
  Contextos:
    - Sem vagas: "Vamos criar sua primeira vaga?"
    - Vagas abertas: "Posso te ajudar com analises de vagas?"
    - Vagas urgentes: "Voce tem X vagas precisando de atencao"
    - Todas concluidas: "Excelente! Todas as vagas estao em dia"

Design & Componentes:
  Design Tokens:
    - Icon: --wedo-cyan (#60BED1)
    - Text: --lia-text-primary (#2D2D2D)
  Layout:
    - Flex: items-center gap-3
    - Margin-bottom: mb-4

Criterios de Aceitacao:
  - [ ] Icone Brain 24px cyan
  - [ ] Texto muda por contexto
  - [ ] Animacao suave na troca
  - [ ] Fonte correta
```

---

### CARD VAG-014: Input de Chat LIA

```yaml
Titulo: [FRONT] Input de Chat LIA - Campo Principal
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Critica
Epic: EPIC-VAG-003

Descricao: |
  Implementar input de chat principal para comunicacao
  com a LIA, seguindo design specs v3.1.

Historia de Usuario: |
  Como recrutador, eu quero digitar comandos ou perguntas
  para a LIA de forma rapida e intuitiva.

Requisitos Tecnicos:
  Frontend:
    - Componente: LIAChatInput
    - Placeholder: "Como posso te ajudar com suas vagas hoje?"
    - Border: 1px solid #E5E7EB
    - Border-radius: rounded-full (pill shape)
    - Height: h-12
    - Font: Open Sans 13px
  Focus State:
    - Border: #60BED1
    - Shadow: 0 0 0 3px rgba(96, 190, 209, 0.12)
  Icons:
    - Esquerda: nenhum ou Brain subtle
    - Direita: Mic + Search ou Send

Design & Componentes:
  Seguir: lia-prompt-design-specs.md
  Estados:
    - Default: border gray
    - Focus: border cyan + shadow
    - Typing: cursor blink
    - Loading: spinner

Comportamento de UI:
  Fluxo Principal:
    1. Usuario clica no input
    2. Focus state ativa (cyan border)
    3. Usuario digita
    4. Enter ou click em send
    5. Mensagem enviada para LIA

Criterios de Aceitacao:
  - [ ] Input pill-shaped funcional
  - [ ] Placeholder correto
  - [ ] Focus state cyan
  - [ ] Enter envia mensagem
  - [ ] Limpa apos envio
```

---

### CARD VAG-015: Icones Microfone e Busca

```yaml
Titulo: [FRONT] Icones Mic e Busca - Acoes Secundarias
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-003

Descricao: |
  Implementar icones de microfone (voice input) e busca
  no input da LIA.

Historia de Usuario: |
  Como recrutador, eu quero usar voz para interagir
  com a LIA quando nao quero digitar.

Requisitos Tecnicos:
  Frontend:
    - Componente: LIAInputIcons
    - Mic: Microfone (Lucide) 18px
    - Search: MagnifyingGlass ou Search 18px
    - Cor: #9CA3AF (gray-400)
    - Hover: #60BED1 (cyan)
  Mic Action:
    - Integrar com Web Speech API
    - Fallback: Gemini voice-to-text
  Search Action:
    - Ativar modo busca semantica

Integracoes Externas:
  Web Speech API:
    - Tipo: Browser API (nativa)
    - Uso: Reconhecimento de voz em tempo real
    - Suporte: Chrome, Edge, Safari (parcial)
    - Fallback: Gemini quando nao suportado
    - Custo: Gratuito
  
  Google Gemini 1.5 Flash:
    - Tipo: REST API
    - Uso: Fallback para voice-to-text quando Web Speech nao disponivel
    - Endpoint: POST /api/v1/voice/transcribe
    - Secret: GEMINI_API_KEY (ja configurado)
    - Custo: ~$0.0001 por transcricao curta
    - Latencia: ~500ms para audio < 10s
  
  Deepgram (alternativa):
    - Tipo: WebSocket API
    - Uso: Transcricao em tempo real com maior precisao
    - Endpoint: wss://api.deepgram.com/v1/listen
    - Secret: DEEPGRAM_API_KEY
    - Custo: ~$0.0043/min
    - Vantagens: Streaming, portugues BR nativo

Criterios de Aceitacao:
  - [ ] Icones visiveis no input
  - [ ] Hover muda cor para cyan
  - [ ] Mic ativa gravacao de voz
  - [ ] Search ativa modo busca
  - [ ] Estados de loading
  - [ ] Fallback para Gemini funciona
  - [ ] Indicador visual de gravacao
```

---

### CARD VAG-016: Sugestoes Contextuais

```yaml
Titulo: [FRONT] Sugestoes Contextuais - Quick Suggestions
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-003

Descricao: |
  Implementar pills de sugestoes abaixo do input que
  mudam baseadas no contexto das vagas do usuario.

Historia de Usuario: |
  Como recrutador, eu quero ver sugestoes relevantes
  para clicar rapidamente sem precisar digitar.

Requisitos Tecnicos:
  Frontend:
    - Componente: LIASuggestionPills
    - Layout: Flex wrap, gap-2
    - Pill style: bg-gray-100 rounded-full px-3 py-1.5
    - Fonte: Open Sans 11px medium
  Sugestoes Base:
    - "Vagas com deadline proximo"
    - "Performance dos ultimos 30 dias"
    - "Candidatos pendentes de feedback"
    - "Vagas sem movimentacao"
  Contextuais (dinamicas):
    - Se vagas urgentes: "Ver 5 vagas urgentes"
    - Se deadline hoje: "Vagas com deadline hoje"

Design & Componentes:
  Design Tokens:
    - Background: --lia-bg-tertiary (#F3F4F6)
    - Text: --lia-text-secondary (#4B5563)
    - Hover: border-cyan + bg-cyan/5
  Estados:
    - Default: bg gray
    - Hover: border cyan, bg cyan/5
    - Click: feedback visual

Criterios de Aceitacao:
  - [ ] Pills visiveis abaixo do input
  - [ ] Click envia sugestao para LIA
  - [ ] Sugestoes mudam por contexto
  - [ ] Hover state correto
  - [ ] Responsivo (2 linhas se necessario)
```

---

### CARD VAG-017: Integracao Backend LIA

```yaml
Titulo: [BACK] Integracao Backend LIA - Vagas Context
Tipo: Feature
Sprint: 2
Pontos: 13
Prioridade: Critica
Epic: EPIC-VAG-003
Status: ✅ IMPLEMENTADO

Descricao: |
  Integrar frontend com backend da LIA para processar
  comandos especificos de gestao de vagas.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA entenda meus
  comandos sobre vagas e execute acoes relevantes.

Requisitos Tecnicos:
  Backend:
    - Endpoint: POST /api/v1/lia/expanded-prompt
    - Request: { message, context_type, context_ids?, context? }
    - Response: { response, agent_used, actions, follow_up_suggestions }
  Frontend:
    - Funcao: sendLiaInlineMessage() em jobs-page.tsx
    - Chat inline com mensagens persistentes
    - Deteccao de intent de criacao de vaga (abre wizard)
  LIA Capabilities:
    - Criar nova vaga (detecta intent e abre wizard)
    - Responder perguntas sobre salarios (benchmark)
    - Responder perguntas sobre skills/requisitos
    - Informar tempo de preenchimento de vagas
    - Explicar processo WSI/metodologia
    - Respostas gerais via LLM

Integracoes Externas:
  Google Gemini 1.5 Flash:
    - Tipo: REST API
    - Uso: LLM principal para respostas gerais e contextuais
    - Endpoint: POST /v1/models/gemini-1.5-flash:generateContent
    - Secret: GEMINI_API_KEY (via Replit integration)
    - Custo: $0.075/1M input, $0.30/1M output
    - Latencia: ~500ms
    - Uso no projeto: Respostas gerais, explicacoes de processo

Servicos de Insights (Backend):
  IntentClassifierService:
    - Arquivo: app/services/intent_classifier.py
    - Funcao: Classifica intencao do usuario para roteamento
  
  JobInsightsService:
    - Arquivo: app/services/job_insights_service.py
    - Funcao: Benchmark salarial interno, metricas de vagas
  
  MarketBenchmarkService:
    - Arquivo: app/services/market_benchmark_service.py
    - Funcao: Dados de mercado para comparacao
  
  FeedbackLearningService:
    - Arquivo: app/services/feedback_learning_service.py
    - Funcao: Aprendizado baseado em feedback

Regras de Negocio:
  Roteamento por Tipo de Pergunta:
    - SALARY: Perguntas sobre salario -> salary_insights
    - SKILLS: Perguntas sobre habilidades -> skills_insights
    - TIME_TO_FILL: Perguntas sobre prazo -> time_insights
    - PROCESS: Perguntas sobre WSI/metodologia -> process_explainer
    - GENERAL: Outras perguntas -> general_assistant (Gemini LLM)

  Deteccao de Intent de Criacao:
    - Detecta padroes como "criar vaga", "nova vaga", "abrir posicao"
    - Abre automaticamente o JobCreationWizard
    - Funcao: isJobCreationIntent() no frontend

Agentes Especializados (Implementados):
  salary_insights:
    - Funcao: handle_salary_question()
    - Usa: JobInsightsService.get_salary_benchmark()
    - Output: Faixa salarial com dados internos e de mercado
  
  skills_insights:
    - Funcao: handle_skills_question()
    - Usa: MarketBenchmarkService
    - Output: Skills mais comuns para a funcao
  
  time_insights:
    - Funcao: handle_time_to_fill_question()
    - Usa: JobInsightsService
    - Output: Tempo medio de preenchimento
  
  process_explainer:
    - Funcao: handle_process_question()
    - Usa: LLMService com contexto WSI
    - Output: Explicacao da metodologia
  
  general_assistant:
    - Funcao: LLMService.generate()
    - Provider: Gemini
    - Output: Resposta contextual

Criterios de Aceitacao:
  - [x] Comandos processados corretamente
  - [x] Respostas sincronas (sem streaming)
  - [x] Deteccao de intent de criacao funciona
  - [x] Erro handling gracioso
  - [x] Historico de chat mantido no frontend
  - [x] Roteamento por tipo de pergunta funciona
  - [x] Latencia < 2s para respostas simples
```

---

# EPIC-VAG-004: QUICK ACTIONS

> **Responsavel:** Frontend Developer  
> **Sprint:** 2  
> **Pontos Total:** 24  
> **Foco:** Botoes de acao rapida para operacoes comuns

---

### CARD VAG-018: Acao Criar Nova Vaga

```yaml
Titulo: [FRONT] Quick Action - Criar Nova Vaga
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Critica
Epic: EPIC-VAG-004

Descricao: |
  Implementar botao de quick action "+ Criar nova vaga"
  que abre o wizard de criacao.

Historia de Usuario: |
  Como recrutador, eu quero criar vaga com um clique
  sem precisar digitar comando.

Requisitos Tecnicos:
  Frontend:
    - Componente: QuickActionButton
    - Icone: Plus 14px
    - Texto: "Criar nova vaga"
    - Estilo: bg-white border rounded-full
  Acao:
    - onClick: openJobCreationWizard()
    - Abre ExpandedChatModal em modo job-creation

Design & Componentes:
  Design Tokens:
    - Background: white
    - Border: 1px solid #E5E7EB
    - Text: #374151 (gray-700)
    - Hover: border-cyan, bg-cyan/5
  Estados:
    - Default, Hover, Active, Disabled

Agentes Relacionados:
  Agente Primario:
    - Nome: job_intake_agent
    - Arquivo: app/agents/specialized/job_intake_agent.py
    - Funcao: Coleta de requisitos para nova vaga via conversa guiada
    - Inputs: Titulo, descricao, requisitos, beneficios, localidade
    - Output: JobVacancy criada no banco de dados
  
  Fluxo de Ativacao:
    1. Usuario clica no botao "Criar nova vaga"
    2. ExpandedChatModal abre em modo job-creation
    3. Orchestrator roteia para job_intake_agent
    4. Agente inicia conversa de coleta de requisitos

Observacao: |
  ⚠️ VALIDACAO PENDENTE - Andre Bevilaqua
  O fluxo de ativacao do job_intake_agent precisa ser validado.
  Topicos a validar:
  - Campos obrigatorios na coleta
  - Ordem das perguntas do agente
  - Integracao com wizard existente

Criterios de Aceitacao:
  - [ ] Botao visivel nas quick actions
  - [ ] Abre wizard de criacao
  - [ ] Icone Plus correto
  - [ ] Hover state funciona
```

---

### CARD VAG-019: Acao Ver Minhas Vagas

```yaml
Titulo: [FRONT] Quick Action - Ver Minhas Vagas
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-004

Descricao: |
  Implementar botao que filtra lista para mostrar apenas
  vagas onde o usuario e o recrutador responsavel.

Historia de Usuario: |
  Como recrutador, eu quero ver rapidamente apenas
  as vagas que estou gerenciando.

Requisitos Tecnicos:
  Frontend:
    - Icone: User 14px
    - Texto: "Ver minhas vagas"
  Acao:
    - onClick: setFilter({ recruiter_email: user.email })

Criterios de Aceitacao:
  - [ ] Filtra por recrutador logado
  - [ ] Badge com contador
  - [ ] URL atualiza com filtro
```

---

### CARD VAG-020: Acao Ver Todas as Vagas

```yaml
Titulo: [FRONT] Quick Action - Ver Todas as Vagas
Tipo: Feature
Sprint: 2
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-004

Descricao: |
  Implementar botao que navega para tab "Todas"
  mostrando lista completa de vagas.

Historia de Usuario: |
  Como recrutador, eu quero ver todas as vagas
  da empresa de uma vez.

Requisitos Tecnicos:
  Frontend:
    - Icone: LayoutGrid 14px
    - Texto: "Ver todas as vagas"
  Acao:
    - onClick: setActiveTab('todas')

Criterios de Aceitacao:
  - [ ] Navega para tab Todas
  - [ ] Scroll suave ate lista
  - [ ] Transicao visual
```

---

### CARD VAG-021: Acao Resumo das Vagas

```yaml
Titulo: [FRONT] Quick Action - Resumo das Vagas
Tipo: Feature
Sprint: 2
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-004
Status: ✅ IMPLEMENTADO

Descricao: |
  Implementar botao que pede para LIA gerar um resumo
  analytics das vagas abertas.

Historia de Usuario: |
  Como recrutador, eu quero um resumo rapido
  do status geral das minhas vagas.

Requisitos Tecnicos:
  Frontend:
    - Icone: BarChart3 14px (Lucide)
    - Texto: "Resumo das vagas"
    - Componente: Quick action pill em jobs-page.tsx
  Acao:
    - onClick: openGeneralChat('Resumo das minhas vagas ativas')
    - Abre chat lateral com mensagem pre-definida
    - Chat envia para /api/v1/lia/expanded-prompt

Integracoes Externas:
  Google Gemini 1.5 Flash:
    - Tipo: REST API
    - Uso: Geracao de resumo contextual das vagas
    - Prompt: LIA recebe contexto e gera resposta
    - Output: Texto formatado com analise
    - Custo: ~$0.001 por resumo

Fluxo Implementado:
  1. Usuario clica em "Resumo das vagas"
  2. setActiveFilter('todas') - muda para tab Todas
  3. openGeneralChat('Resumo das minhas vagas ativas')
  4. Chat lateral abre com mensagem inicial
  5. Mensagem e enviada para /lia/expanded-prompt
  6. general_assistant processa com Gemini LLM
  7. Resposta exibida no chat

Output Gerado:
  - Analise contextual das vagas
  - Sugestoes baseadas no estado atual
  - Follow-up suggestions automaticas

Criterios de Aceitacao:
  - [x] Envia comando para LIA
  - [x] LIA retorna resumo contextual
  - [x] Chat lateral abre automaticamente
  - [x] Hover state funciona
```

---

### CARD VAG-022: Acao Mais Ideias (AI)

```yaml
Titulo: [FRONT] Quick Action - Mais Ideias (AI)
Tipo: Feature
Sprint: 2
Pontos: 8
Prioridade: Media
Epic: EPIC-VAG-004
Status: ✅ IMPLEMENTADO

Descricao: |
  Implementar componente que oferece sugestoes de queries
  para a LIA baseadas no contexto de vagas.

Historia de Usuario: |
  Como recrutador, eu quero ver sugestoes de perguntas
  que posso fazer para a LIA sobre minhas vagas.

Requisitos Tecnicos:
  Frontend:
    - Componente: LiaVacancyQueriesGuide (popover com tabs)
    - Icone: Sparkles 14px (AI indicator)
    - Texto: "Mais ideias"
    - Estilo: Pill com hover state cyan
  Acao:
    - onClick: Abre popover com categorias de queries
    - Selecionar query: openGeneralChat(query)
    - Chat processa via /lia/expanded-prompt

Implementacao Atual:
  Componente: LiaVacancyQueriesGuide
    - Arquivo: plataforma-lia/src/components/ui/lia-vacancy-queries-guide.tsx
    - Tabs: Analise | Pipeline | Comparativo | Estrategico
    - Queries pre-definidas por categoria
    - onClick: Envia query selecionada para o chat

  Categorias de Queries:
    Analise:
      - "Analise de funil das vagas selecionadas"
      - "Quais vagas estao com gargalos?"
      - "Qual a taxa de conversao media?"
    Pipeline:
      - "Quantos candidatos por etapa?"
      - "Candidatos pendentes de feedback"
      - "Tempo medio em cada etapa"
    Comparativo:
      - "Compare as vagas selecionadas"
      - "Qual vaga tem melhor performance?"
    Estrategico:
      - "Sugestoes para melhorar conversao"
      - "Vagas que precisam de atencao"

Fluxo Implementado:
  1. Usuario clica em "Mais ideias"
  2. Popover abre com tabs de categorias
  3. Usuario seleciona uma query
  4. setActiveFilter('todas')
  5. openGeneralChat(query)
  6. Chat lateral processa via expanded-prompt
  7. general_assistant responde com Gemini LLM

Design & Componentes:
  Pill Style:
    - Background: bg-gray-100
    - Text: text-gray-950
    - Hover: bg-gray-900 text-white
  Popover:
    - Tabs para categorias
    - Pills clicaveis para cada query
    - Estilo consistente com design system

Criterios de Aceitacao:
  - [x] Estilo diferenciado (AI feature com Sparkles)
  - [x] Popover com categorias de queries
  - [x] Queries sao enviadas para o chat
  - [x] Chat processa e retorna resposta
  - [x] Transicao suave ao selecionar
```

---

# EPIC-VAG-005: PAGINA VAZIA/ONBOARDING

> **Responsavel:** Frontend Developer  
> **Sprint:** 3  
> **Pontos Total:** 26  
> **Foco:** Experiencia quando usuario nao tem vagas

---

### CARD VAG-023: Empty State Design

```yaml
Titulo: [FRONT] Empty State - Design Pagina Vazia
Tipo: Feature
Sprint: 3
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-005

Descricao: |
  Implementar design de empty state quando usuario
  nao tem nenhuma vaga cadastrada.

Historia de Usuario: |
  Como recrutador novo, eu quero ver uma pagina
  acolhedora que me guie para criar minha primeira vaga.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobsEmptyState
    - Ilustracao: SVG ou Lottie sutil
    - Centralizado verticalmente
    - CTA proeminente

Design & Componentes:
  Layout:
    - Container: max-w-lg mx-auto text-center
    - Ilustracao: 200x200px, cores brand
    - Titulo: Open Sans 20px semibold
    - Subtitulo: Open Sans 14px gray-500
    - CTA: Botao cyan grande

Criterios de Aceitacao:
  - [ ] Aparece quando 0 vagas
  - [ ] Design acolhedor
  - [ ] CTA visivel
  - [ ] Transicao suave quando cria primeira vaga
```

---

### CARD VAG-024: Mensagem Boas-Vindas LIA

```yaml
Titulo: [FRONT] Mensagem Boas-Vindas LIA - Empty State
Tipo: Feature
Sprint: 3
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-005

Descricao: |
  Implementar mensagem de boas-vindas da LIA no empty state
  com tom amigavel e orientativo.

Historia de Usuario: |
  Como recrutador novo, eu quero que a LIA me cumprimente
  e me ajude a comecar.

Requisitos Tecnicos:
  Frontend:
    - Componente: LIAWelcomeMessage
    - Icone: Brain animado sutil
    - Mensagem: "Ola! Sou a LIA, sua assistente de recrutamento. Vamos criar sua primeira vaga?"
    - Fonte: Source Serif 4 para mensagem
  Animacao:
    - Typewriter effect opcional
    - Fade in suave

Criterios de Aceitacao:
  - [ ] Mensagem personalizada
  - [ ] Tom amigavel
  - [ ] Icone Brain visivel
  - [ ] Transicao suave
```

---

# EPIC-VAG-006: TABELA DE VAGAS

> **Responsavel:** Frontend Developer  
> **Sprint:** 4  
> **Pontos Total:** 42  
> **Foco:** Componente principal de tabela de vagas com features avancadas

---

### CARD VAG-028: Tabela de Vagas - Estrutura Base

```yaml
Titulo: [FRONT] Tabela de Vagas - Estrutura Base
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Critica
Epic: EPIC-VAG-006
Status: Implementado

Descricao: |
  Componente principal de tabela para listagem de vagas com
  suporte a colunas dinamicas, ordenacao, selecao e preview.
  Implementado nas linhas 3500-4400 do jobs-page.tsx.

Historia de Usuario: |
  Como recrutador, eu quero ver todas as vagas em uma tabela
  organizada para gerenciar facilmente o pipeline de vagas.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobsTable (inline em jobs-page.tsx)
    - Estrutura: Table, TableHeader, TableBody, TableRow
    - Colunas: Titulo, Status, Recrutador, Candidatos, Criacao, Acoes
    - Virtual scroll para performance em listas grandes
  State:
    - filteredJobs: Job[] - vagas filtradas
    - jobsSortColumn: string - coluna de ordenacao
    - jobsSortDirection: 'asc' | 'desc'
    - jobsColumnWidths: Record<string, number>

Design & Componentes:
  Componente: Table (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - filteredJobs, jobsSortColumn, jobsSortDirection
    - jobsColumnWidths, selectedJobsForBatch
  Layout:
    - Table: w-full com colunas responsivas
    - Header: sticky top-0 bg-white
    - Row: hover:bg-gray-50 cursor-pointer

Criterios de Aceitacao:
  - [x] Tabela renderiza lista de vagas
  - [x] Header com nomes das colunas
  - [x] Rows clicaveis abrem preview
  - [x] Responsivo em diferentes tamanhos
  - [x] Performance aceitavel com 100+ vagas
```

---

### CARD VAG-029: Colunas Configuraveis Toggle/Order

```yaml
Titulo: [FRONT] Colunas Configuraveis - Toggle e Reordenacao
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-006
Status: Implementado

Descricao: |
  Sistema para mostrar/ocultar e reordenar colunas da tabela
  de vagas usando o hook useJobColumnConfig.

Historia de Usuario: |
  Como recrutador, eu quero escolher quais colunas ver
  para personalizar minha visualizacao de vagas.

Requisitos Tecnicos:
  Frontend:
    - Hook: useJobColumnConfig
    - Arquivo: plataforma-lia/src/hooks/useJobColumnConfig.ts
    - Features: toggle visibility, drag-and-drop reorder
  State:
    - columnVisibility: Record<string, boolean>
    - columnOrder: string[]
  Persistencia:
    - localStorage: 'jobs-table-column-order'

Design & Componentes:
  Componente: useJobColumnConfig
  Arquivo: plataforma-lia/src/hooks/useJobColumnConfig.ts
  Props/Estados:
    - visibleColumns, columnOrder, toggleColumn, reorderColumns

Criterios de Aceitacao:
  - [x] Toggle de visibilidade por coluna
  - [x] Drag-and-drop para reordenar
  - [x] Persistencia no localStorage
  - [x] UI para configurar colunas
```

---

### CARD VAG-030: Ordenacao Multi-Coluna Sort

```yaml
Titulo: [FRONT] Ordenacao Multi-Coluna - Sort Headers
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-006
Status: Implementado

Descricao: |
  Ordenacao de vagas clicando nos headers das colunas
  com indicador visual de direcao (asc/desc).

Historia de Usuario: |
  Como recrutador, eu quero ordenar vagas por diferentes
  criterios para encontrar rapidamente o que procuro.

Requisitos Tecnicos:
  Frontend:
    - Handler: handleJobsSort(column: string)
    - State: jobsSortColumn, jobsSortDirection
    - Icones: ArrowUp, ArrowDown, ArrowUpDown (Lucide)
  Logica:
    - Click em coluna: toggle asc -> desc -> unsorted
    - Sort client-side para lista atual

Design & Componentes:
  Componente: TableHeader (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - jobsSortColumn, jobsSortDirection, handleJobsSort
  Visual:
    - Header clicavel com cursor-pointer
    - Icone de direcao ao lado do titulo

Criterios de Aceitacao:
  - [x] Click no header ordena a coluna
  - [x] Toggle entre asc/desc/none
  - [x] Icone visual indica direcao
  - [x] Ordenacao funciona corretamente
```

---

### CARD VAG-031: Redimensionamento de Colunas Resize

```yaml
Titulo: [FRONT] Redimensionamento de Colunas - Column Resize
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-006
Status: Implementado

Descricao: |
  Permitir redimensionamento de colunas arrastando a borda
  entre colunas do header da tabela.

Historia de Usuario: |
  Como recrutador, eu quero ajustar a largura das colunas
  para ver mais ou menos informacao em cada uma.

Requisitos Tecnicos:
  Frontend:
    - Handler: startJobsColumnResize(column, startX)
    - State: jobsColumnWidths: Record<string, number>
    - Events: onMouseDown, onMouseMove, onMouseUp
  Persistencia:
    - localStorage: 'jobs-table-column-widths'

Design & Componentes:
  Componente: ColumnResizer (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - jobsColumnWidths, startJobsColumnResize
  Visual:
    - Resize handle: 4px wide, cursor-col-resize
    - Hover: bg-cyan highlight

Criterios de Aceitacao:
  - [x] Arraste redimensiona coluna
  - [x] Larguras persistem no localStorage
  - [x] Min/max width respeitados
  - [x] Cursor visual durante resize
```

---

### CARD VAG-032: Selecao em Lote Checkbox

```yaml
Titulo: [FRONT] Selecao em Lote - Checkboxes + Select All
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-006
Status: Implementado

Descricao: |
  Checkboxes para selecionar multiplas vagas e executar
  acoes em lote (publicar, pausar, atribuir recrutador).

Historia de Usuario: |
  Como recrutador, eu quero selecionar varias vagas
  para executar acoes em lote eficientemente.

Requisitos Tecnicos:
  Frontend:
    - State: selectedJobsForBatch: Set<string>
    - Checkbox no header: "Selecionar Todos"
    - Checkbox por row: toggle individual
  Integracao:
    - JobActionsBar: exibe quando selectedCount > 0

Design & Componentes:
  Componente: Checkbox (shadcn)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - selectedJobsForBatch, toggleJobSelection, selectAllJobs
  Visual:
    - Checkbox cyan quando selecionado
    - Row com bg-cyan/5 quando selecionada

Criterios de Aceitacao:
  - [x] Checkbox individual por vaga
  - [x] "Selecionar Todos" no header
  - [x] Contador de selecionados visivel
  - [x] JobActionsBar aparece ao selecionar
```

---

### CARD VAG-033: Persistencia de Config localStorage

```yaml
Titulo: [FRONT] Persistencia de Configuracao - localStorage
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-006
Status: Implementado

Descricao: |
  Salvar preferencias da tabela (largura colunas, ordem,
  visibilidade) no localStorage para persistir entre sessoes.

Historia de Usuario: |
  Como recrutador, eu quero que minhas configuracoes da
  tabela sejam lembradas quando voltar a pagina.

Requisitos Tecnicos:
  Frontend:
    - Keys: 'jobs-table-column-widths', 'jobs-table-column-order'
    - useEffect: load on mount, save on change
    - Fallback: valores default se nao existir

Design & Componentes:
  Componente: useJobColumnConfig hook
  Arquivo: plataforma-lia/src/hooks/useJobColumnConfig.ts
  Props/Estados:
    - Getters e setters com persistencia automatica

Criterios de Aceitacao:
  - [x] Configuracoes salvas no localStorage
  - [x] Carregadas ao montar componente
  - [x] Fallback para defaults
  - [x] Clear funciona corretamente
```

---

### CARD VAG-034: Coluna Performance LIA Triagens

```yaml
Titulo: [FRONT] Coluna Performance LIA - Metricas de Triagem
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-006
Status: Implementado

Descricao: |
  Coluna na tabela mostrando metricas de performance da
  LIA: pipeline, triagens agendadas, taxas de conversao.

Historia de Usuario: |
  Como recrutador, eu quero ver rapidamente o desempenho
  da LIA em cada vaga na propria tabela.

Requisitos Tecnicos:
  Frontend:
    - Coluna: "LIA Performance"
    - Dados: liaMetrics.pipeline_lia, triagens_agendadas
    - Visual: Badge com cor por performance
  Backend:
    - Job.liaMetrics: { pipeline_lia, triagens_agendadas, taxa_conversao }

Design & Componentes:
  Componente: LiaMetricsCell (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - liaMetrics: { pipeline_lia, triagens_agendadas, taxa_conversao }
  Visual:
    - Badge verde se taxa > 50%
    - Badge amarelo se taxa 25-50%
    - Badge vermelho se taxa < 25%

Criterios de Aceitacao:
  - [x] Coluna mostra metricas LIA
  - [x] Cor indica performance
  - [x] Tooltip com detalhes
  - [x] Dados carregam da API
```

---

### CARD VAG-035: Coluna Roteiro de Triagem Link

```yaml
Titulo: [FRONT] Coluna Roteiro de Triagem - Quick Link
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-006
Status: Implementado

Descricao: |
  Link rapido na tabela para abrir o roteiro de triagem
  da vaga diretamente na tab de screening do preview.

Historia de Usuario: |
  Como recrutador, eu quero acessar rapidamente o roteiro
  de triagem de uma vaga sem precisar navegar.

Requisitos Tecnicos:
  Frontend:
    - Icone: ClipboardList (Lucide)
    - Action: openPreview(job, 'screening')
    - Tooltip: "Ver roteiro de triagem"

Design & Componentes:
  Componente: ScreeningLink (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - job, openPreview callback
  Visual:
    - Icone pequeno com hover:text-cyan

Criterios de Aceitacao:
  - [x] Icone clicavel na coluna
  - [x] Abre preview na tab screening
  - [x] Tooltip informativo
  - [x] Hover state funciona
```

---

### CARD VAG-036: Acoes por Linha Menu Dropdown

```yaml
Titulo: [FRONT] Acoes por Linha - Menu Dropdown
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-006
Status: Implementado

Descricao: |
  Menu dropdown em cada linha da tabela com acoes rapidas:
  Editar, Duplicar, Pausar/Ativar, Ver detalhes.

Historia de Usuario: |
  Como recrutador, eu quero executar acoes em uma vaga
  diretamente da tabela sem abrir o preview.

Requisitos Tecnicos:
  Frontend:
    - Componente: DropdownMenu (shadcn)
    - Trigger: MoreVertical icon
    - Items: Editar, Duplicar, Pausar, Ver detalhes, Publicar

Design & Componentes:
  Componente: DropdownMenu (shadcn)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - job, handlers para cada acao
  Items:
    - Edit2: Editar vaga
    - Copy: Duplicar vaga
    - Pause/Play: Pausar/Ativar
    - Eye: Ver detalhes
    - Share2: Publicar

Criterios de Aceitacao:
  - [x] Menu abre ao clicar no icone
  - [x] Todas as acoes funcionam
  - [x] Icones corretos por acao
  - [x] Menu fecha ao clicar fora
```

---

# EPIC-VAG-007: PAINEL DE PREVIEW DA VAGA

> **Responsavel:** Frontend Developer  
> **Sprint:** 4  
> **Pontos Total:** 61  
> **Foco:** Painel lateral de preview com detalhes da vaga selecionada

---

### CARD VAG-037: Preview Panel - Estrutura Base

```yaml
Titulo: [FRONT] Preview Panel - Estrutura Base
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Critica
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Painel lateral que exibe detalhes da vaga selecionada
  com tabs para diferentes secoes de informacao.

Historia de Usuario: |
  Como recrutador, eu quero ver detalhes de uma vaga
  em um painel lateral sem sair da lista.

Requisitos Tecnicos:
  Frontend:
    - State: showJobPreview, previewJob, previewWidth
    - Position: fixed right com largura ajustavel
    - Tabs: Visao Geral, Roteiro de Triagem
  Resize:
    - isResizingPreview, startPreviewResize()

Design & Componentes:
  Componente: JobPreviewPanel (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - showJobPreview, previewJob, previewWidth
    - previewTab, setPreviewTab
  Layout:
    - Position: fixed right-0 top-0 h-full
    - Width: previewWidth (300-600px)
    - z-index: 40

Criterios de Aceitacao:
  - [x] Painel abre ao clicar em vaga
  - [x] Tabs funcionam corretamente
  - [x] Close button funciona
  - [x] Animacao de abertura suave
```

---

### CARD VAG-038: Tab Visao Geral - Funil Rapido

```yaml
Titulo: [FRONT] Tab Visao Geral - Funil Rapido
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Visualizacao rapida do funil de candidatos da vaga
  com contadores por etapa do processo.

Historia de Usuario: |
  Como recrutador, eu quero ver rapidamente quantos
  candidatos estao em cada etapa do processo.

Requisitos Tecnicos:
  Frontend:
    - Dados: funnel.total, screening, interview, final, hired
    - Visual: Barras horizontais ou numeros grandes
    - Cores: Por etapa do funil

Design & Componentes:
  Componente: FunnelQuickView (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - funnel: { total, screening, interview, final, hired }
  Visual:
    - Numeros grandes com labels
    - Icones por etapa

Criterios de Aceitacao:
  - [x] Mostra contadores corretos
  - [x] Visual claro e legivel
  - [x] Click navega para etapa
  - [x] Atualiza em tempo real
```

---

### CARD VAG-039: Tab Visao Geral - Metricas LIA

```yaml
Titulo: [FRONT] Tab Visao Geral - Metricas LIA
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Exibicao das metricas de performance da LIA para a vaga:
  pipeline, triagens agendadas, taxas de conversao.

Historia de Usuario: |
  Como recrutador, eu quero ver as metricas de performance
  da LIA para avaliar a eficacia das triagens.

Requisitos Tecnicos:
  Frontend:
    - Dados: liaMetrics.pipeline_lia, triagens_agendadas
    - Cards: Pipeline LIA, Triagens, Taxa Conversao
    - Visual: Numeros com trend indicators

Design & Componentes:
  Componente: LiaMetricsView (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - liaMetrics: { pipeline_lia, triagens_agendadas, taxa_conversao }

Criterios de Aceitacao:
  - [x] Metricas exibidas corretamente
  - [x] Trend indicators funcionam
  - [x] Tooltip com detalhes
  - [x] Loading state adequado
```

---

### CARD VAG-040: Tab Visao Geral - Responsaveis

```yaml
Titulo: [FRONT] Tab Visao Geral - Responsaveis
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Exibicao dos responsaveis pela vaga (recrutador e gestor)
  com botoes de contato rapido via WhatsApp e Email.

Historia de Usuario: |
  Como recrutador, eu quero ver quem sao os responsaveis
  e poder contatá-los rapidamente.

Requisitos Tecnicos:
  Frontend:
    - Dados: recruiter, manager (nome, email, phone)
    - Botoes: WhatsApp, Email (icons)
    - Avatar: Iniciais do nome

Design & Componentes:
  Componente: ResponsibleContacts (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - recruiter, manager objects
  Actions:
    - WhatsApp: window.open('https://wa.me/...')
    - Email: mailto: link

Criterios de Aceitacao:
  - [x] Avatar e nome do recrutador
  - [x] Avatar e nome do gestor
  - [x] Botao WhatsApp funciona
  - [x] Botao Email funciona
```

---

### CARD VAG-041: Tab Visao Geral - Datas Criticas

```yaml
Titulo: [FRONT] Tab Visao Geral - Datas Criticas
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Exibicao das datas importantes da vaga: abertura,
  deadline de triagem, shortlist e fechamento.

Historia de Usuario: |
  Como recrutador, eu quero ver as datas criticas
  para nao perder prazos importantes.

Requisitos Tecnicos:
  Frontend:
    - Dados: openDate, deadline, deadlineScreening, deadlineShortlist
    - Visual: Timeline ou lista com cores por urgencia
    - Alert: Badge vermelho se prazo < 3 dias

Design & Componentes:
  Componente: CriticalDates (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - openDate, deadline, deadlineScreening, deadlineShortlist, deadlineClosing

Criterios de Aceitacao:
  - [x] Todas as datas exibidas
  - [x] Formatacao correta
  - [x] Alerta visual para prazos proximos
  - [x] Cores indicam urgencia
```

---

### CARD VAG-042: Tab Roteiro de Triagem - WSI Blocks

```yaml
Titulo: [FRONT] Tab Roteiro de Triagem - WSI Blocks
Tipo: Feature
Sprint: 4
Pontos: 13
Prioridade: Critica
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Exibicao dos 7 blocos WSI do roteiro de triagem
  em formato de accordion expansivel.

Historia de Usuario: |
  Como recrutador, eu quero ver e editar o roteiro
  de triagem da vaga com todos os blocos WSI.

Requisitos Tecnicos:
  Frontend:
    - Blocos: WSI_BLOCKS constant (7 blocos)
    - Accordion: expandedBlocks state
    - Edit: showQuestionEditModal, editingQuestion
  Backend:
    - Job.screeningConfig.questions

Design & Componentes:
  Componente: WSIBlocksView (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Constantes: plataforma-lia/src/components/jobs/jobsPageConstants.tsx
  Props/Estados:
    - WSI_BLOCKS, expandedBlocks, toggleBlock

Blocos WSI:
  - Bloco 0: Abordagem Inicial (template WhatsApp)
  - Bloco 1: Apresentacao da Oportunidade
  - Bloco 1.5: Perguntas Padrao da Empresa
  - Bloco 2: Elegibilidade WSI
  - Bloco 3: Avaliacao Tecnica
  - Bloco 4: Analise Situacional e Fit
  - Bloco 5: Resultado e Encerramento

Criterios de Aceitacao:
  - [x] 7 blocos WSI exibidos
  - [x] Accordion funciona
  - [x] Conteudo de cada bloco correto
  - [x] Edicao de perguntas possivel
```

---

### CARD VAG-043: WSI Blocks - Accordion Expansivel

```yaml
Titulo: [FRONT] WSI Blocks - Accordion Expansivel
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Controle de expansao/colapso individual dos blocos WSI
  com state persistente e animacao suave.

Historia de Usuario: |
  Como recrutador, eu quero expandir/colapsar blocos
  para focar na secao que estou editando.

Requisitos Tecnicos:
  Frontend:
    - State: expandedBlocks: Set<number>
    - Toggle: toggleBlock(blockId)
    - Animation: framer-motion ou CSS transitions

Design & Componentes:
  Componente: Accordion (inline implementation)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - expandedBlocks, toggleBlock

Criterios de Aceitacao:
  - [x] Click expande/colapsa bloco
  - [x] Icone ChevronDown rotaciona
  - [x] Animacao suave
  - [x] Multiplos blocos podem estar abertos
```

---

### CARD VAG-044: WSI Blocks - Editor de Perguntas

```yaml
Titulo: [FRONT] WSI Blocks - Editor de Perguntas
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Modal para editar perguntas de triagem dentro de cada
  bloco WSI com preview e validacao.

Historia de Usuario: |
  Como recrutador, eu quero editar as perguntas de
  triagem para personalizar o roteiro.

Requisitos Tecnicos:
  Frontend:
    - State: showQuestionEditModal, editingQuestion
    - Modal: QuestionEditModal component
    - Form: Textarea com preview

Design & Componentes:
  Componente: QuestionEditModal (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - showQuestionEditModal, editingQuestion, handleSaveQuestion

Criterios de Aceitacao:
  - [x] Modal abre ao clicar em editar
  - [x] Textarea editavel
  - [x] Preview do resultado
  - [x] Salvar atualiza a lista
```

---

### CARD VAG-045: Configuracao de Canais de Triagem

```yaml
Titulo: [FRONT] Configuracao de Canais de Triagem
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Modal para configurar canais de triagem da vaga:
  WhatsApp, Email, Portal de candidatos.

Historia de Usuario: |
  Como recrutador, eu quero escolher por qual canal
  a LIA deve fazer a triagem dos candidatos.

Requisitos Tecnicos:
  Frontend:
    - Component: ScreeningChannelsModal
    - Channels: WhatsApp, Email, Portal
    - Config: enabled, priority, settings

Design & Componentes:
  Componente: ScreeningChannelsModal
  Arquivo: plataforma-lia/src/components/screening-config/ScreeningChannelsModal.tsx
  Props/Estados:
    - channels, onSave, onClose

Criterios de Aceitacao:
  - [x] Modal com opcoes de canais
  - [x] Toggle para habilitar/desabilitar
  - [x] Prioridade configuravel
  - [x] Salvar persiste configuracao
```

---

### CARD VAG-046: Processo Seletivo Inline Breadcrumb

```yaml
Titulo: [FRONT] Processo Seletivo - Inline Breadcrumb
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Visualizacao do pipeline de processo seletivo como
  breadcrumb horizontal mostrando as etapas.

Historia de Usuario: |
  Como recrutador, eu quero ver visualmente as etapas
  do processo seletivo da vaga.

Requisitos Tecnicos:
  Frontend:
    - Dados: hiringProcess.steps
    - Visual: Breadcrumb horizontal
    - Highlight: Etapa atual destacada

Design & Componentes:
  Componente: ProcessBreadcrumb (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - hiringProcess steps array

Criterios de Aceitacao:
  - [x] Etapas exibidas em sequencia
  - [x] Etapa atual destacada
  - [x] Responsivo (scroll horizontal)
  - [x] Tooltip com detalhes da etapa
```

---

### CARD VAG-047: Resize do Painel de Preview

```yaml
Titulo: [FRONT] Resize do Painel de Preview
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Baixa
Epic: EPIC-VAG-007
Status: Implementado

Descricao: |
  Permitir redimensionamento do painel de preview
  arrastando a borda esquerda.

Historia de Usuario: |
  Como recrutador, eu quero ajustar a largura do
  preview para ver mais ou menos detalhes.

Requisitos Tecnicos:
  Frontend:
    - State: isResizingPreview, previewWidth
    - Handler: startPreviewResize, handlePreviewResize
    - Limits: min 300px, max 600px

Design & Componentes:
  Componente: PreviewResizeHandle (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - isResizingPreview, previewWidth

Criterios de Aceitacao:
  - [x] Arraste redimensiona painel
  - [x] Limites min/max respeitados
  - [x] Cursor visual durante resize
  - [x] Persistencia da largura
```

---

# EPIC-VAG-008: MODAIS DE ACAO EM LOTE

> **Responsavel:** Frontend + Backend Developer  
> **Sprint:** 5  
> **Pontos Total:** 67  
> **Foco:** Modais para acoes em lote sobre vagas selecionadas

---

### CARD VAG-048: JobActionsBar - Barra de Acoes em Lote

```yaml
Titulo: [FRONT] JobActionsBar - Barra de Acoes em Lote
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-008
Status: Implementado

Descricao: |
  Barra fixa que aparece quando vagas sao selecionadas,
  com botoes para acoes em lote.

Historia de Usuario: |
  Como recrutador, eu quero ver uma barra de acoes
  quando seleciono vagas para executar operacoes em lote.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobActionsBar
    - Trigger: selectedJobsForBatch.size > 0
    - Acoes: Publicar, Insights, Duplicar, Pausar, Atribuir

Design & Componentes:
  Componente: JobActionsBar
  Arquivo: plataforma-lia/src/components/job-actions-bar.tsx
  Props/Estados:
    - selectedCount, onDeselectAll, onPublish, onInsights
    - onDuplicate, onToggleStatus, onAssignRecruiter

Criterios de Aceitacao:
  - [x] Barra aparece ao selecionar
  - [x] Contador de vagas selecionadas
  - [x] Todos os botoes funcionam
  - [x] Botao X limpa selecao
```

---

### CARD VAG-049: JobPublishModal - Publicar em Canais

```yaml
Titulo: [FRONT] JobPublishModal - Publicar em Canais
Tipo: Feature
Sprint: 5
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-008
Status: Implementado

Descricao: |
  Modal para publicar vagas em canais externos:
  LinkedIn, Website, Indeed, portais de vagas.

Historia de Usuario: |
  Como recrutador, eu quero publicar vagas em varios
  canais de uma vez para ampliar o alcance.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobPublishModal
    - Canais: LinkedIn, Website, Indeed, Glassdoor
    - Selecao: Checkbox por canal

Design & Componentes:
  Componente: JobPublishModal
  Arquivo: plataforma-lia/src/components/modals/job-publish-modal.tsx
  Props/Estados:
    - isOpen, onClose, jobs, onPublish

Criterios de Aceitacao:
  - [x] Modal lista canais disponiveis
  - [x] Checkbox para selecionar canais
  - [x] Botao publicar funciona
  - [x] Feedback de sucesso/erro
```

---

### CARD VAG-050: JobInsightsModal - Metricas Expandidas

```yaml
Titulo: [FRONT] JobInsightsModal - Metricas Expandidas
Tipo: Feature
Sprint: 5
Pontos: 13
Prioridade: Critica
Epic: EPIC-VAG-008
Status: Implementado

Descricao: |
  Modal com metricas detalhadas das vagas selecionadas:
  WSI scores, demographics, performance analytics.

Historia de Usuario: |
  Como recrutador, eu quero ver analises detalhadas
  das vagas para tomar decisoes informadas.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobInsightsModal
    - Dados: WSI scores, demographics, funnel analytics
    - Charts: Graficos de performance
  Backend:
    - GET /api/v1/job-vacancies/{id}/analytics

Integracoes Externas:
  Google Gemini 1.5 Flash:
    - Tipo: REST API
    - Uso: Geracao de insights e recomendacoes
    - Custo: ~$0.002 por analise

Design & Componentes:
  Componente: JobInsightsModal
  Arquivo: plataforma-lia/src/components/modals/job-insights-modal.tsx
  Props/Estados:
    - isOpen, onClose, jobs

Criterios de Aceitacao:
  - [x] Modal exibe metricas
  - [x] Graficos funcionam
  - [x] Insights LIA gerados
  - [x] Export de dados possivel
```

---

### CARD VAG-051: JobDuplicateModal - Duplicar Vaga

```yaml
Titulo: [FRONT] JobDuplicateModal - Duplicar Vaga
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-008
Status: Implementado

Descricao: |
  Modal para duplicar vaga selecionada com opcao
  de alterar recrutador e configuracoes basicas.

Historia de Usuario: |
  Como recrutador, eu quero duplicar uma vaga existente
  para criar uma similar rapidamente.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobDuplicateModal
    - Form: Novo titulo, novo recrutador
    - Action: POST /api/v1/job-vacancies (clone)

Design & Componentes:
  Componente: JobDuplicateModal
  Arquivo: plataforma-lia/src/components/modals/job-duplicate-modal.tsx
  Props/Estados:
    - isOpen, onClose, job, onDuplicate

Criterios de Aceitacao:
  - [x] Modal exibe dados da vaga original
  - [x] Form para alterar titulo
  - [x] Selector para recrutador
  - [x] Duplicacao cria nova vaga
```

---

### CARD VAG-052: JobStatusModal - Pausar/Ativar Vaga

```yaml
Titulo: [FRONT] JobStatusModal - Pausar/Ativar Vaga
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-008
Status: Implementado

Descricao: |
  Modal para pausar ou reativar vagas selecionadas
  com campo para motivo/comentario.

Historia de Usuario: |
  Como recrutador, eu quero pausar ou ativar vagas
  com registro do motivo.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobStatusModal
    - Mode: statusModalMode ('pause' | 'activate')
    - Form: Textarea para motivo

Design & Componentes:
  Componente: JobStatusModal
  Arquivo: plataforma-lia/src/components/modals/job-status-modal.tsx
  Props/Estados:
    - isOpen, onClose, jobs, mode, onConfirm

Criterios de Aceitacao:
  - [x] Modal exibe acao correta (pausar/ativar)
  - [x] Campo para motivo
  - [x] Confirmacao atualiza status
  - [x] Feedback visual adequado
```

---

### CARD VAG-053: JobAssignRecruiterModal - Atribuir Recrutador

```yaml
Titulo: [FRONT] JobAssignRecruiterModal - Atribuir Recrutador
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-008
Status: Implementado

Descricao: |
  Modal para atribuir ou trocar o recrutador responsavel
  pelas vagas selecionadas.

Historia de Usuario: |
  Como gestor, eu quero atribuir vagas a diferentes
  recrutadores da minha equipe.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobAssignRecruiterModal
    - Data: companyRecruiters list
    - Action: PATCH /api/v1/job-vacancies/{id}/recruiter

Design & Componentes:
  Componente: JobAssignRecruiterModal
  Arquivo: plataforma-lia/src/components/modals/job-assign-recruiter-modal.tsx
  Props/Estados:
    - isOpen, onClose, jobs, recruiters, onAssign

Criterios de Aceitacao:
  - [x] Lista de recrutadores disponiveis
  - [x] Selecao de novo recrutador
  - [x] Confirmacao atualiza vagas
  - [x] Notificacao ao novo recrutador
```

---

### CARD VAG-054: JobUnpublishModal - Despublicar Vaga

```yaml
Titulo: [FRONT] JobUnpublishModal - Despublicar Vaga
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Baixa
Epic: EPIC-VAG-008
Status: Implementado

Descricao: |
  Modal para remover vaga de canais onde foi publicada
  (LinkedIn, Indeed, Website).

Historia de Usuario: |
  Como recrutador, eu quero despublicar uma vaga
  quando nao estiver mais disponivel.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobUnpublishModal
    - Dados: canais onde vaga esta publicada
    - Action: Remover de canais selecionados

Design & Componentes:
  Componente: JobUnpublishModal
  Arquivo: plataforma-lia/src/components/modals/job-unpublish-modal.tsx
  Props/Estados:
    - isOpen, onClose, job, publishedChannels, onUnpublish

Criterios de Aceitacao:
  - [x] Lista canais publicados
  - [x] Checkbox para selecionar
  - [x] Confirmacao remove de canais
  - [x] Status atualiza na vaga
```

---

### CARD VAG-055: JobCompareModal - Comparar Vagas

```yaml
Titulo: [FRONT] JobCompareModal - Comparar Vagas
Tipo: Feature
Sprint: 5
Pontos: 8
Prioridade: Media
Epic: EPIC-VAG-008
Status: Implementado

Descricao: |
  Modal para comparar 2 ou mais vagas lado a lado
  com metricas e caracteristicas.

Historia de Usuario: |
  Como recrutador, eu quero comparar vagas similares
  para entender diferencas de performance.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobCompareModal
    - Layout: Grid lado a lado
    - Dados: Metricas, requisitos, configuracoes

Design & Componentes:
  Componente: JobCompareModal
  Arquivo: plataforma-lia/src/components/modals/job-compare-modal.tsx
  Props/Estados:
    - isOpen, onClose, jobs

Criterios de Aceitacao:
  - [x] Vagas exibidas lado a lado
  - [x] Metricas comparadas
  - [x] Diferencas destacadas
  - [x] Scroll sincronizado
```

---

### CARD VAG-056: EditJobModal - Edicao Completa

```yaml
Titulo: [FRONT] EditJobModal - Edicao Completa da Vaga
Tipo: Feature
Sprint: 5
Pontos: 13
Prioridade: Critica
Epic: EPIC-VAG-008
Status: Implementado

Descricao: |
  Modal completo para edicao de todos os campos da vaga
  com validacao e preview.

Historia de Usuario: |
  Como recrutador, eu quero editar todos os detalhes
  de uma vaga em um unico lugar.

Requisitos Tecnicos:
  Frontend:
    - Componente: EditJobModal
    - Tabs: Basico, Requisitos, Triagem, Pipeline
    - Validacao: Zod schema

Design & Componentes:
  Componente: EditJobModal
  Arquivo: plataforma-lia/src/components/modals/edit-job-modal.tsx
  Props/Estados:
    - isOpen, onClose, job, onSave

Criterios de Aceitacao:
  - [x] Todos os campos editaveis
  - [x] Validacao em tempo real
  - [x] Preview das mudancas
  - [x] Salvar atualiza a vaga
```

---

# EPIC-VAG-009: SISTEMA DE FILTROS E BUSCA

> **Responsavel:** Frontend Developer  
> **Sprint:** 4  
> **Pontos Total:** 36  
> **Foco:** Sistema avancado de filtros e busca para vagas

---

### CARD VAG-057: JobFiltersPanel - Painel Lateral

```yaml
Titulo: [FRONT] JobFiltersPanel - Painel Lateral de Filtros
Tipo: Feature
Sprint: 4
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-009
Status: Implementado

Descricao: |
  Painel lateral com todos os filtros disponiveis para
  vagas, organizado por categorias.

Historia de Usuario: |
  Como recrutador, eu quero ter um painel de filtros
  organizado para refinar minha busca de vagas.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobFiltersPanel
    - Arquivo: plataforma-lia/src/components/jobs/JobFilters.tsx
    - Categorias: Status, Posicao, Funil, Recrutador

Design & Componentes:
  Componente: JobFiltersPanel
  Arquivo: plataforma-lia/src/components/jobs/JobFilters.tsx
  Props/Estados:
    - isOpen, jobFilters, toggleJobFilter, clearAllJobFilters

Criterios de Aceitacao:
  - [x] Painel lateral funcional
  - [x] Categorias organizadas
  - [x] Badge com contador de filtros ativos
  - [x] Botao limpar todos os filtros
```

---

### CARD VAG-058: Filtros Rapidos Ativas/Urgentes/Remotas

```yaml
Titulo: [FRONT] Filtros Rapidos - Botoes Pre-definidos
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-009
Status: Implementado

Descricao: |
  Botoes de filtro rapido no topo do painel para os
  filtros mais usados: Ativas, Urgentes, Remotas, Sem Candidatos.

Historia de Usuario: |
  Como recrutador, eu quero filtrar rapidamente por
  criterios comuns com um clique.

Requisitos Tecnicos:
  Frontend:
    - 4 botoes pre-definidos
    - Toggle: clique ativa/desativa
    - Visual: Destaque quando ativo

Design & Componentes:
  Componente: QuickFilters (inline em JobFiltersPanel)
  Arquivo: plataforma-lia/src/components/jobs/JobFilters.tsx
  Props/Estados:
    - jobFilters, toggleJobFilter

Criterios de Aceitacao:
  - [x] 4 botoes visiveis
  - [x] Toggle funciona
  - [x] Visual de estado ativo
  - [x] Combina com outros filtros
```

---

### CARD VAG-059: Filtro por Status da Vaga

```yaml
Titulo: [FRONT] Filtro por Status da Vaga
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-009
Status: Implementado

Descricao: |
  Filtro para selecionar vagas por status: Ativa,
  Rascunho, Paralisada, Fechada, etc.

Historia de Usuario: |
  Como recrutador, eu quero filtrar vagas pelo status
  para focar nas que preciso trabalhar.

Requisitos Tecnicos:
  Frontend:
    - Checkbox list com status
    - Status: STATUS_ORDER constant
    - Multi-selecao permitida

Design & Componentes:
  Componente: StatusFilter (inline em JobFiltersPanel)
  Arquivo: plataforma-lia/src/components/jobs/JobFilters.tsx
  Constantes: plataforma-lia/src/components/jobs/jobsPageConstants.tsx

Criterios de Aceitacao:
  - [x] Lista todos os status
  - [x] Multi-selecao funciona
  - [x] Contador por status
  - [x] Cores por status
```

---

### CARD VAG-060: Filtro por Etapa do Processo

```yaml
Titulo: [FRONT] Filtro por Etapa do Processo
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-009
Status: Implementado

Descricao: |
  Filtro para selecionar vagas pela etapa atual do
  processo: Triagem, Entrevistas, Finalistas, etc.

Historia de Usuario: |
  Como recrutador, eu quero ver vagas que estao em
  determinada etapa do processo.

Requisitos Tecnicos:
  Frontend:
    - Checkbox list com etapas
    - Etapas: DEFAULT_STAGES
    - Filtro por currentStage

Design & Componentes:
  Componente: StageFilter (inline)
  Arquivo: plataforma-lia/src/components/jobs/JobFilters.tsx

Criterios de Aceitacao:
  - [x] Lista etapas do processo
  - [x] Multi-selecao funciona
  - [x] Icones por etapa
  - [x] Contador de vagas por etapa
```

---

### CARD VAG-061: Filtro por Modelo de Trabalho

```yaml
Titulo: [FRONT] Filtro por Modelo de Trabalho
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-009
Status: Implementado

Descricao: |
  Filtro para selecionar vagas pelo modelo de trabalho:
  Remoto, Hibrido, Presencial.

Historia de Usuario: |
  Como recrutador, eu quero filtrar vagas pelo modelo
  de trabalho para agrupar similares.

Requisitos Tecnicos:
  Frontend:
    - Radio ou checkbox: Remoto, Hibrido, Presencial
    - Field: jobFilters.position.workModels

Design & Componentes:
  Componente: WorkModelFilter (inline)
  Arquivo: plataforma-lia/src/components/jobs/JobFilters.tsx

Criterios de Aceitacao:
  - [x] 3 opcoes visiveis
  - [x] Multi-selecao permitida
  - [x] Icone por modelo
  - [x] Filtro funciona corretamente
```

---

### CARD VAG-062: Filtro por Recrutador/Gestor

```yaml
Titulo: [FRONT] Filtro por Recrutador/Gestor
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-009
Status: Implementado

Descricao: |
  Dropdown para filtrar vagas pelo recrutador responsavel
  ou gestor da vaga.

Historia de Usuario: |
  Como gestor, eu quero ver vagas de um recrutador
  especifico da minha equipe.

Requisitos Tecnicos:
  Frontend:
    - Select/Combobox com lista de recrutadores
    - Data: companyRecruiters, companyManagers
    - Field: jobFilters.recruiter

Design & Componentes:
  Componente: RecruiterFilter (inline)
  Arquivo: plataforma-lia/src/components/jobs/JobFilters.tsx

Criterios de Aceitacao:
  - [x] Dropdown com recrutadores
  - [x] Dropdown com gestores
  - [x] Busca por nome
  - [x] Filtro funciona
```

---

### CARD VAG-063: Busca Booleana AND/OR/NOT

```yaml
Titulo: [FRONT] Busca Booleana - Operadores AND/OR/NOT
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Baixa
Epic: EPIC-VAG-009
Status: Pendente

Descricao: |
  Campo de busca avancada com suporte a operadores
  booleanos para queries complexas.

Historia de Usuario: |
  Como recrutador avancado, eu quero usar operadores
  booleanos para buscas mais precisas.

Requisitos Tecnicos:
  Frontend:
    - State: booleanSearch: boolean
    - Parser: parseSearchQuery()
    - Operadores: AND, OR, NOT, aspas

Design & Componentes:
  Componente: BooleanSearchInput (a implementar)
  Arquivo: plataforma-lia/src/components/jobs/JobFilters.tsx

Criterios de Aceitacao:
  - [ ] Toggle para modo booleano
  - [ ] Parsing de operadores
  - [ ] Highlighting de sintaxe
  - [ ] Ajuda de sintaxe disponivel
```

---

### CARD VAG-064: Pesquisas Salvas Templates

```yaml
Titulo: [FRONT] Pesquisas Salvas - Templates de Busca
Tipo: Feature
Sprint: 4
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-009
Status: Implementado

Descricao: |
  Sistema para salvar combinacoes de filtros como
  templates reutilizaveis.

Historia de Usuario: |
  Como recrutador, eu quero salvar minhas buscas
  frequentes para reutilizar depois.

Requisitos Tecnicos:
  Frontend:
    - State: savedSearches: SavedSearch[]
    - Actions: saveCurrentSearch, applySearch, deleteSearch
    - Persistencia: localStorage ou backend

Design & Componentes:
  Componente: SavedSearches (inline)
  Arquivo: plataforma-lia/src/components/jobs/JobFilters.tsx
  Hook: useJobFiltersPersistence

Criterios de Aceitacao:
  - [x] Botao salvar busca atual
  - [x] Lista de buscas salvas
  - [x] Aplicar busca salva
  - [x] Deletar busca salva
```

---

### CARD VAG-065: Persistencia de Filtros Hook

```yaml
Titulo: [FRONT] Persistencia de Filtros - Custom Hook
Tipo: Feature
Sprint: 4
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-009
Status: Implementado

Descricao: |
  Hook customizado para persistir estado dos filtros
  no localStorage e URL search params.

Historia de Usuario: |
  Como recrutador, eu quero que meus filtros sejam
  lembrados entre sessoes.

Requisitos Tecnicos:
  Frontend:
    - Hook: useJobFiltersPersistence
    - Persistencia: localStorage + URL params
    - Sync: bidirecional

Design & Componentes:
  Componente: useJobFiltersPersistence
  Arquivo: plataforma-lia/src/hooks/useJobFiltersPersistence.ts

Criterios de Aceitacao:
  - [x] Filtros salvos no localStorage
  - [x] URL reflete filtros ativos
  - [x] Carregar filtros da URL
  - [x] Clear limpa tudo
```

---

# EPIC-VAG-010: CHAT LIA MULTI-NIVEL

> **Responsavel:** Frontend + Backend Developer  
> **Sprint:** 5  
> **Pontos Total:** 55  
> **Foco:** Sistema de chat com LIA em diferentes niveis de expansao

---

### CARD VAG-066: Nivel 1 Mini Prompt Inline

```yaml
Titulo: [FRONT] Nivel 1 - Mini Prompt Inline
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-010
Status: Implementado

Descricao: |
  Campo de input compacto no header da tabela para
  perguntas rapidas a LIA.

Historia de Usuario: |
  Como recrutador, eu quero fazer perguntas rapidas
  sem abrir um chat completo.

Requisitos Tecnicos:
  Frontend:
    - Input: Compacto com icones
    - Icons: Mic, Send, Sparkles
    - State: liaInlineInput

Design & Componentes:
  Componente: LiaInlinePrompt (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - liaInlineInput, setLiaInlineInput, sendLiaInlineMessage

Criterios de Aceitacao:
  - [x] Input visivel no header
  - [x] Icones funcionais
  - [x] Enter envia mensagem
  - [x] Resposta exibida inline
```

---

### CARD VAG-067: Nivel 2 Chat Expandido Lateral

```yaml
Titulo: [FRONT] Nivel 2 - Chat Expandido Lateral
Tipo: Feature
Sprint: 5
Pontos: 8
Prioridade: Critica
Epic: EPIC-VAG-010
Status: Implementado

Descricao: |
  Painel lateral de chat expandido para conversas
  mais longas com LIA.

Historia de Usuario: |
  Como recrutador, eu quero ter um chat completo
  para conversas mais detalhadas.

Requisitos Tecnicos:
  Frontend:
    - State: showExpandedLIA, liaWidth
    - Resize: startLiaResize, handleLiaResize
    - Chat: Messages history, input

Design & Componentes:
  Componente: ExpandedLiaChat (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx
  Props/Estados:
    - showExpandedLIA, liaWidth, liaChatMessages

Criterios de Aceitacao:
  - [x] Painel lateral abre
  - [x] Historico de mensagens
  - [x] Resize funciona
  - [x] Close button funciona
```

---

### CARD VAG-068: Nivel 3 Super Chat Criacao de Vaga

```yaml
Titulo: [FRONT] Nivel 3 - Super Chat Criacao de Vaga
Tipo: Feature
Sprint: 5
Pontos: 13
Prioridade: Critica
Epic: EPIC-VAG-010
Status: Implementado

Descricao: |
  Modal expandido para criacao de vaga guiada por LIA
  com wizard de etapas.

Historia de Usuario: |
  Como recrutador, eu quero criar vagas conversando
  com a LIA de forma guiada.

Requisitos Tecnicos:
  Frontend:
    - Componente: ExpandedChatModal + JobCreationWizard
    - Mode: isInJobCreationMode
    - Wizard: 11 etapas de criacao

Integracoes Externas:
  Google Gemini 1.5 Flash:
    - Tipo: REST API
    - Uso: Geracao de sugestoes e extracao de requisitos
    - Custo: ~$0.005 por criacao

Design & Componentes:
  Componente: ExpandedChatModal
  Arquivo: plataforma-lia/src/components/expanded-chat-modal.tsx
  Componente: JobCreationWizard
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] Modal expande para criacao
  - [x] Wizard de etapas funciona
  - [x] LIA guia o processo
  - [x] Vaga criada ao final
```

---

### CARD VAG-069: Deteccao de Intent de Criacao

```yaml
Titulo: [FRONT] Deteccao de Intent de Criacao de Vaga
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-010
Status: Implementado

Descricao: |
  Funcao que detecta quando usuario quer criar vaga
  e abre automaticamente o wizard.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA entenda quando
  quero criar uma vaga e inicie o processo.

Requisitos Tecnicos:
  Frontend:
    - Funcao: isJobCreationIntent(message)
    - Keywords: 'criar vaga', 'nova vaga', 'abrir posicao'
    - Action: Abrir JobCreationWizard

Design & Componentes:
  Componente: isJobCreationIntent function
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx

Criterios de Aceitacao:
  - [x] Detecta intents de criacao
  - [x] Abre wizard automaticamente
  - [x] Keywords configuradas
  - [x] Fallback para chat normal
```

---

### CARD VAG-070: Auto-Expand LIA ao Selecionar Vagas

```yaml
Titulo: [FRONT] Auto-Expand LIA ao Selecionar Vagas
Tipo: Feature
Sprint: 5
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-010
Status: Implementado

Descricao: |
  Expandir automaticamente o chat LIA quando vagas
  sao selecionadas para acoes em lote.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA esteja pronta
  para me ajudar quando seleciono vagas.

Requisitos Tecnicos:
  Frontend:
    - useEffect: watch selectedJobsForBatch
    - Action: setShowExpandedLIA(true)
    - Context: Passar vagas selecionadas para LIA

Design & Componentes:
  Componente: useEffect hook
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx

Criterios de Aceitacao:
  - [x] Chat expande ao selecionar
  - [x] Contexto das vagas passado
  - [x] Mensagem inicial contextual
  - [x] Nao expande se ja aberto
```

---

### CARD VAG-071: Historico de Mensagens Inline

```yaml
Titulo: [FRONT] Historico de Mensagens Inline
Tipo: Feature
Sprint: 5
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-010
Status: Implementado

Descricao: |
  Manter historico de mensagens do chat inline
  durante a sessao.

Historia de Usuario: |
  Como recrutador, eu quero ver o historico das minhas
  perguntas anteriores.

Requisitos Tecnicos:
  Frontend:
    - State: liaInlineMessages: Message[]
    - Limit: Ultimas 10 mensagens
    - Clear: Button para limpar

Design & Componentes:
  Componente: InlineMessageHistory (inline)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx

Criterios de Aceitacao:
  - [x] Mensagens mantidas na sessao
  - [x] Scroll para ver historico
  - [x] Botao limpar funciona
  - [x] Limite de mensagens
```

---

### CARD VAG-072: AudioRecordButton Gravacao de Voz

```yaml
Titulo: [FRONT] AudioRecordButton - Gravacao de Voz
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-010
Status: Implementado

Descricao: |
  Botao para gravar audio e transcrever usando
  Web Speech API ou Deepgram.

Historia de Usuario: |
  Como recrutador, eu quero falar com a LIA
  ao inves de digitar.

Requisitos Tecnicos:
  Frontend:
    - Componente: AudioRecordButton
    - API: Web Speech API (browser)
    - Fallback: Deepgram API

Integracoes Externas:
  Web Speech API:
    - Tipo: Browser API
    - Uso: Transcricao de voz em tempo real
    - Custo: Gratuito

Design & Componentes:
  Componente: AudioRecordButton
  Arquivo: plataforma-lia/src/components/ui/audio-record-button.tsx

Criterios de Aceitacao:
  - [x] Botao mic visivel
  - [x] Gravacao inicia ao clicar
  - [x] Transcricao automatica
  - [x] Texto inserido no input
```

---

### CARD VAG-073: LiaVacancyQueriesGuide Popover

```yaml
Titulo: [FRONT] LiaVacancyQueriesGuide - Popover de Sugestoes
Tipo: Feature
Sprint: 5
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-010
Status: Implementado

Descricao: |
  Popover com tabs mostrando queries pre-definidas
  para perguntar a LIA sobre vagas.

Historia de Usuario: |
  Como recrutador, eu quero ver sugestoes de perguntas
  que posso fazer sobre vagas.

Requisitos Tecnicos:
  Frontend:
    - Componente: LiaVacancyQueriesGuide
    - Tabs: Analise, Pipeline, Comparativo, Estrategico
    - Actions: Clicar envia query para chat

Design & Componentes:
  Componente: LiaVacancyQueriesGuide
  Arquivo: plataforma-lia/src/components/ui/lia-vacancy-queries-guide.tsx

Criterios de Aceitacao:
  - [x] Popover abre ao clicar
  - [x] Tabs organizadas
  - [x] Queries clicaveis
  - [x] Envia para chat ao clicar
```

---

### CARD VAG-074: ExpandedChatModal Modal Full

```yaml
Titulo: [FRONT] ExpandedChatModal - Modal Full Screen
Tipo: Feature
Sprint: 5
Pontos: 8
Prioridade: Critica
Epic: EPIC-VAG-010
Status: Implementado

Descricao: |
  Modal de chat expandido em tela cheia para conversas
  complexas e criacao de vagas.

Historia de Usuario: |
  Como recrutador, eu quero ter espaco total para
  conversar com a LIA em tarefas complexas.

Requisitos Tecnicos:
  Frontend:
    - Componente: ExpandedChatModal
    - Layout: Full screen modal
    - Modes: Normal chat, Job creation wizard

Design & Componentes:
  Componente: ExpandedChatModal
  Arquivo: plataforma-lia/src/components/expanded-chat-modal.tsx

Criterios de Aceitacao:
  - [x] Modal abre em full screen
  - [x] Chat funcional completo
  - [x] Modo criacao de vaga
  - [x] Close e minimize funcionam
```

---

# EPIC-VAG-011: JOB CREATION WIZARD (SUPER CHAT LIA)

> **Responsavel:** Frontend + Backend Developer  
> **Sprint:** 6  
> **Pontos Total:** 124  
> **Foco:** Wizard completo de criacao de vaga guiada por LIA

---

### CARD VAG-075: Botao Nova Vaga Header

```yaml
Titulo: [FRONT] Botao Nova Vaga - Header Principal
Tipo: Feature
Sprint: 6
Pontos: 3
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Botao principal no header para iniciar criacao
  de nova vaga via wizard LIA.

Historia de Usuario: |
  Como recrutador, eu quero um botao claro para
  iniciar a criacao de uma nova vaga.

Requisitos Tecnicos:
  Frontend:
    - Componente: Button com Plus icon
    - Action: Abrir JobCreationWizard
    - Style: bg-cyan, text-white

Design & Componentes:
  Componente: Button (shadcn)
  Arquivo: plataforma-lia/src/components/pages/jobs-page.tsx

Criterios de Aceitacao:
  - [x] Botao visivel no header
  - [x] Icone Plus correto
  - [x] Abre wizard ao clicar
  - [x] Hover state funciona
```

---

### CARD VAG-076: Super Chat Modal Container Principal

```yaml
Titulo: [FRONT] Super Chat Modal - Container Principal
Tipo: Feature
Sprint: 6
Pontos: 8
Prioridade: Critica
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Container principal do wizard de criacao de vaga
  com layout split (chat + formulario).

Historia de Usuario: |
  Como recrutador, eu quero uma interface clara
  para criar vagas passo a passo.

Requisitos Tecnicos:
  Frontend:
    - Componente: JobCreationWizard
    - Layout: Split view (chat left, form right)
    - Stepper: Progress indicator

Design & Componentes:
  Componente: JobCreationWizard
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] Layout split funcional
  - [x] Stepper de progresso
  - [x] Chat side funciona
  - [x] Form side funciona
```

---

### CARD VAG-077: Wizard Step 1 - Descricao Inicial Chat

```yaml
Titulo: [FRONT] Wizard Step 1 - Descricao Inicial via Chat
Tipo: Feature
Sprint: 6
Pontos: 8
Prioridade: Critica
Epic: EPIC-VAG-011
Status: Implementado
Atualizado: 22 Janeiro 2026

Descricao: |
  Primeira etapa do wizard onde usuario descreve a vaga
  conversando com LIA que extrai requisitos.

Historia de Usuario: |
  Como recrutador, eu quero descrever a vaga naturalmente
  e a LIA extrair os requisitos.

Requisitos Tecnicos:
  Frontend:
    - Chat conversacional com LIA
    - Extracao de requisitos via NLP
    - Confirmacao de criterios extraidos
  Backend:
    - POST /api/v1/lia/job-wizard/step

Integracoes Externas:
  Google Gemini 1.5 Flash:
    - Tipo: REST API
    - Uso: Extracao de requisitos da descricao
    - Prompt: System prompt para job intake (MELHORADO - Jan/2026)

Design & Componentes:
  Componente: WizardStep1Chat (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] Chat funcional
  - [x] LIA extrai requisitos
  - [x] Criterios exibidos para confirmacao
  - [x] Avancar para proxima etapa

Melhorias Implementadas (22/01/2026):
  - Prompt de extracao melhorado com instrucoes explicitas para tecnologias
  - Extracao separada de competencias tecnicas (Python, FastAPI, etc.)
  - Extracao separada de competencias comportamentais (lideranca, etc.)
  - Logging [WIZARD-STAGE1] para diagnostico
  - Cada tecnologia extraida individualmente (nao agrupada)
```

---

### CARD VAG-078: Wizard Step 2 - Informacoes Basicas

```yaml
Titulo: [FRONT] Wizard Step 2 - Informacoes Basicas
Tipo: Feature
Sprint: 6
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado
Atualizado: 22 Janeiro 2026

Descricao: |
  Formulario para titulo, departamento, localizacao
  e gestor responsavel.

Historia de Usuario: |
  Como recrutador, eu quero preencher as informacoes
  basicas da vaga de forma estruturada.

Requisitos Tecnicos:
  Frontend:
    - Fields: titulo, departamento, localizacao, modelo, gestor
    - Validation: basicInfoSchema (Zod)
    - AutoComplete: Departamentos da empresa
    - Auto-preenchimento: Dados do Stage 1 via detectedCriteria

Design & Componentes:
  Componente: WizardStep2BasicInfo (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] Todos os campos funcionam
  - [x] Validacao em tempo real
  - [x] AutoComplete departamentos
  - [x] Gestor selecionavel
  - [x] Auto-preenchimento com dados do Stage 1

Correcao Implementada (22/01/2026):
  - Mapeamento de campos backend/frontend corrigido
  - Backend agora retorna nomes em portugues:
    - job_title -> cargo
    - department -> gestorArea
    - work_model -> modeloTrabalho
    - location -> localizacao
    - detected_skills -> competenciasTecnicas
    - behavioral_skills -> competenciasComportamentais
    - seniority -> senioridadeIdiomas
```

---

### CARD VAG-079: Wizard Step 3 - Remuneracao e Beneficios

```yaml
Titulo: [FRONT] Wizard Step 3 - Remuneracao e Beneficios
Tipo: Feature
Sprint: 6
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Formulario para faixa salarial e selecao de
  beneficios da empresa.

Historia de Usuario: |
  Como recrutador, eu quero definir salario e beneficios
  usando os cadastrados da empresa.

Requisitos Tecnicos:
  Frontend:
    - Fields: salarioMin, salarioMax, moeda, beneficios
    - Hook: useCompanyBenefits
    - Multi-select: Beneficios

Design & Componentes:
  Componente: WizardStep3Compensation (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx
  Hook: plataforma-lia/src/hooks/use-company-benefits.ts

Criterios de Aceitacao:
  - [x] Range de salario funciona
  - [x] Beneficios da empresa listados
  - [x] Multi-selecao de beneficios
  - [x] Preview de total compensation
```

---

### CARD VAG-080: Wizard Step 4 - Competencias Tecnicas

```yaml
Titulo: [FRONT] Wizard Step 4 - Competencias Tecnicas
Tipo: Feature
Sprint: 6
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Formulario para skills, tecnologias e tech stack
  com sugestoes baseadas no titulo.

Historia de Usuario: |
  Como recrutador, eu quero definir os requisitos
  tecnicos com sugestoes inteligentes.

Requisitos Tecnicos:
  Frontend:
    - Fields: skills[], tecnologias[], experiencia
    - Hook: useCompanyTechStack
    - AutoSuggest: Baseado no titulo

Design & Componentes:
  Componente: WizardStep4TechSkills (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx
  Hook: plataforma-lia/src/hooks/use-company-tech-stack.ts

Criterios de Aceitacao:
  - [x] Tags de skills funcionam
  - [x] Tech stack por categoria
  - [x] Sugestoes automaticas
  - [x] Pesos por skill
```

---

### CARD VAG-081: Wizard Step 5 - Competencias WSI Comportamentais

```yaml
Titulo: [FRONT] Wizard Step 5 - Competencias WSI Comportamentais
Tipo: Feature
Sprint: 6
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Formulario para definir competencias comportamentais
  usando metodologia Big Five / WSI.

Historia de Usuario: |
  Como recrutador, eu quero definir o perfil comportamental
  ideal para a vaga.

Requisitos Tecnicos:
  Frontend:
    - Fields: Big Five dimensions
    - Sliders: Nivel por competencia
    - Hook: useCompanyCulture

Design & Componentes:
  Componente: WizardStep5BehavioralWSI (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx
  Hook: plataforma-lia/src/hooks/use-company-culture.ts

Criterios de Aceitacao:
  - [x] 5 dimensoes Big Five
  - [x] Sliders funcionam
  - [x] Peso por competencia
  - [x] Perfil ideal visualizado
```

---

### CARD VAG-082: Wizard Step 6 - Requisitos Idiomas Formacao

```yaml
Titulo: [FRONT] Wizard Step 6 - Requisitos Idiomas e Formacao
Tipo: Feature
Sprint: 6
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Formulario para requisitos de idiomas e nivel
  de formacao academica.

Historia de Usuario: |
  Como recrutador, eu quero definir requisitos de
  idiomas e formacao para a vaga.

Requisitos Tecnicos:
  Frontend:
    - Fields: idiomas[], nivelIdioma, formacao, area
    - Options: Fluente, Avancado, Intermediario, Basico
    - Options: Graduacao, Pos, Mestrado, Doutorado

Design & Componentes:
  Componente: WizardStep6LanguagesEducation (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] Multi-idiomas com nivel
  - [x] Selecao de formacao
  - [x] Area de estudo
  - [x] Campos opcionais
```

---

### CARD VAG-083: Wizard Step 7 - Scorecard de Avaliacao

```yaml
Titulo: [FRONT] Wizard Step 7 - Scorecard de Avaliacao
Tipo: Feature
Sprint: 6
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Formulario para definir criterios de avaliacao
  e pesos para scoring de candidatos.

Historia de Usuario: |
  Como recrutador, eu quero definir como os candidatos
  serao avaliados e pontuados.

Requisitos Tecnicos:
  Frontend:
    - Fields: criterios[], pesos[], rubricas
    - Builder: Adicionar/remover criterios
    - Total: Soma de pesos = 100%

Design & Componentes:
  Componente: WizardStep7Scorecard (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] Builder de criterios
  - [x] Pesos ajustaveis
  - [x] Rubricas por criterio
  - [x] Validacao de total
```

---

### CARD VAG-084: Wizard Step 8 - Prazos e Cronograma

```yaml
Titulo: [FRONT] Wizard Step 8 - Prazos e Cronograma
Tipo: Feature
Sprint: 6
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Formulario para definir prazos das etapas do processo:
  triagem, shortlist, fechamento.

Historia de Usuario: |
  Como recrutador, eu quero definir prazos para
  cada etapa do processo seletivo.

Requisitos Tecnicos:
  Frontend:
    - Fields: deadlineScreening, deadlineShortlist, deadlineClosing
    - DatePickers: Com validacao de sequencia
    - Calculation: SLA automatico

Design & Componentes:
  Componente: WizardStep8Timeline (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] DatePickers funcionam
  - [x] Validacao de sequencia
  - [x] SLA calculado
  - [x] Alertas de prazo curto
```

---

### CARD VAG-085: Wizard Step 9 - Pipeline do Processo

```yaml
Titulo: [FRONT] Wizard Step 9 - Pipeline do Processo
Tipo: Feature
Sprint: 6
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Configuracao das etapas do processo seletivo
  usando templates ou customizacao.

Historia de Usuario: |
  Como recrutador, eu quero definir as etapas do
  processo seletivo para esta vaga.

Requisitos Tecnicos:
  Frontend:
    - Hook: useRecruitmentStages
    - Templates: DEFAULT_STAGES
    - Drag-and-drop: Reordenar etapas

Design & Componentes:
  Componente: WizardStep9Pipeline (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx
  Hook: plataforma-lia/src/hooks/use-recruitment-stages.ts

Criterios de Aceitacao:
  - [x] Templates disponiveis
  - [x] Customizacao de etapas
  - [x] Drag-and-drop funciona
  - [x] Etapas salvas na vaga
```

---

### CARD VAG-086: Wizard Step 10 - Solicitacao de Dados

```yaml
Titulo: [FRONT] Wizard Step 10 - Solicitacao de Dados
Tipo: Feature
Sprint: 6
Pontos: 5
Prioridade: Media
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Configuracao dos documentos e dados a solicitar
  dos candidatos durante triagem.

Historia de Usuario: |
  Como recrutador, eu quero definir quais documentos
  solicitar dos candidatos.

Requisitos Tecnicos:
  Frontend:
    - Fields: DEFAULT_DATA_FIELDS
    - Options: CV, portfolio, certificados, etc
    - Toggle: Obrigatorio/Opcional

Design & Componentes:
  Componente: WizardStep10DataRequest (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx
  Hook: plataforma-lia/src/hooks/use-data-request-config.ts

Criterios de Aceitacao:
  - [x] Lista de campos disponiveis
  - [x] Toggle obrigatorio/opcional
  - [x] Campos customizados
  - [x] Preview da solicitacao
```

---

### CARD VAG-087: Wizard Step 11 - Revisao Final e Publicacao

```yaml
Titulo: [FRONT] Wizard Step 11 - Revisao Final e Publicacao
Tipo: Feature
Sprint: 6
Pontos: 8
Prioridade: Critica
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Tela final de revisao de todos os dados da vaga
  com opcao de publicar ou salvar como rascunho.

Historia de Usuario: |
  Como recrutador, eu quero revisar tudo antes de
  criar a vaga oficialmente.

Requisitos Tecnicos:
  Frontend:
    - Preview: Todos os campos preenchidos
    - Actions: Publicar, Salvar rascunho, Voltar
    - Validation: Campos obrigatorios

Design & Componentes:
  Componente: WizardStep11Review (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] Preview completo
  - [x] Validacao final
  - [x] Botao criar vaga
  - [x] Feedback de sucesso
```

---

### CARD VAG-088: [BACK] Endpoint /lia/job-wizard/step

```yaml
Titulo: [BACK] Endpoint /lia/job-wizard/step
Tipo: Feature
Sprint: 6
Pontos: 13
Prioridade: Critica
Epic: EPIC-VAG-011
Status: Implementado
Atualizado: 22 Janeiro 2026

Descricao: |
  Endpoint backend para processar cada etapa do wizard
  de criacao de vaga com LIA.

Historia de Usuario: |
  Como sistema, eu preciso processar as interacoes
  do wizard e manter o estado da conversa.

Requisitos Tecnicos:
  Backend:
    - Endpoint: POST /api/v1/lia/job-wizard/step
    - Request: WizardStepRequest
    - Response: WizardStepResponse
    - Storage: _job_drafts dict
    - Mapeamento: Campos LLM (ingles) -> Frontend (portugues)

Integracoes Externas:
  Google Gemini 1.5 Flash:
    - Tipo: REST API
    - Uso: Processamento de intents e geracao de respostas
    - Prompt: System prompts por etapa (MELHORADOS)

Design & Componentes:
  Componente: /lia/job-wizard/step endpoint
  Arquivo: lia-agent-system/app/api/v1/lia_assistant.py
  Models: WizardStepRequest, WizardStepResponse

Criterios de Aceitacao:
  - [x] Endpoint processa todas as etapas
  - [x] Mantem estado da conversa
  - [x] Detecta intents por etapa
  - [x] Retorna dados extraidos
  - [x] Mapeamento de campos para frontend

Melhorias Implementadas (22/01/2026):
  Stage 1 - Extracao de Descricao:
    - Prompt melhorado com instrucoes explicitas para tecnologias
    - Mapeamento de campos LLM para frontend:
      - job_title -> cargo
      - department -> gestorArea  
      - detected_skills -> competenciasTecnicas
      - behavioral_skills -> competenciasComportamentais
      - seniority -> senioridadeIdiomas
      - work_model -> modeloTrabalho
      - location -> localizacao
      - experience_years -> experiencia
      - education -> formacao
    - Logging [WIZARD-STAGE1] para diagnostico
    - Extracao individual de cada tecnologia
```

---

### CARD VAG-089: Navegacao entre Etapas Stepper

```yaml
Titulo: [FRONT] Navegacao entre Etapas - Stepper Visual
Tipo: Feature
Sprint: 6
Pontos: 5
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Componente visual de stepper mostrando progresso
  e permitindo navegacao entre etapas.

Historia de Usuario: |
  Como recrutador, eu quero ver meu progresso e poder
  voltar a etapas anteriores.

Requisitos Tecnicos:
  Frontend:
    - State: wizardSteps, currentStep
    - Visual: Steps com status (completed, current, pending)
    - Navigation: Click para ir a etapa (se permitido)

Design & Componentes:
  Componente: WizardStepper (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] Stepper visual claro
  - [x] Status por etapa
  - [x] Navegacao funciona
  - [x] Validacao ao avancar
```

---

### CARD VAG-090: Calibracao de Candidatos Sourcing

```yaml
Titulo: [FRONT] Calibracao de Candidatos - Sourcing
Tipo: Feature
Sprint: 6
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Funcionalidade de calibracao mostrando candidatos
  similares da base local e global para feedback.

Historia de Usuario: |
  Como recrutador, eu quero ver candidatos similares
  para calibrar os requisitos da vaga.

Requisitos Tecnicos:
  Frontend:
    - Interface: CalibrationCandidate cards
    - Sources: Local (base) + Global (Pearch)
    - Actions: Aprovar, Rejeitar, Adicionar a base
  Backend:
    - searchLocalCandidates, searchCandidates (Pearch)

Design & Componentes:
  Componente: CalibrationSection (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx
  Type: CalibrationCandidate interface

Criterios de Aceitacao:
  - [x] Candidatos locais exibidos
  - [x] Candidatos globais exibidos
  - [x] Feedback influencia requisitos
  - [x] Adicionar a base funciona
```

---

### CARD VAG-091: ScreeningQuestionsPanel Perguntas de Triagem

```yaml
Titulo: [FRONT] ScreeningQuestionsPanel - Perguntas de Triagem
Tipo: Feature
Sprint: 6
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Painel para configurar perguntas de triagem que
  a LIA fara aos candidatos.

Historia de Usuario: |
  Como recrutador, eu quero definir as perguntas
  que a LIA fara na triagem.

Requisitos Tecnicos:
  Frontend:
    - Componente: ScreeningQuestionsPanel
    - Fields: Pergunta, tipo, obrigatorio, peso
    - Reorder: Drag-and-drop

Design & Componentes:
  Componente: ScreeningQuestionsPanel
  Arquivo: plataforma-lia/src/components/job-creation/ScreeningQuestionsPanel.tsx
  Type: ScreeningQuestion interface

Criterios de Aceitacao:
  - [x] Lista de perguntas editavel
  - [x] Adicionar/remover perguntas
  - [x] Reordenar perguntas
  - [x] Tipos de resposta
```

---

### CARD VAG-092: Integracao com Busca Global Pearch

```yaml
Titulo: [FRONT] Integracao com Busca Global - Pearch API
Tipo: Feature
Sprint: 6
Pontos: 8
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Integracao com API Pearch para buscar candidatos
  globais durante calibracao.

Historia de Usuario: |
  Como recrutador, eu quero ver candidatos de fora
  da minha base para expandir opcoes.

Requisitos Tecnicos:
  Frontend:
    - Function: searchCandidates()
    - API: Pearch external service
    - Results: CalibrationCandidate[] com origin='global'
  Backend:
    - Proxy: /api/v1/search/candidates/global

Integracoes Externas:
  Pearch API:
    - Tipo: REST API Externa
    - Uso: Busca de candidatos em base global
    - Custo: Por credito/reveal

Design & Componentes:
  Componente: searchCandidates function
  Arquivo: plataforma-lia/src/lib/api/candidate-search.ts

Criterios de Aceitacao:
  - [x] Busca Pearch funciona
  - [x] Resultados exibidos
  - [x] Reveal com creditos
  - [x] Error handling adequado
```

---

### CARD VAG-093: Validacao de Dados por Etapa Zod Schema

```yaml
Titulo: [FRONT] Validacao de Dados por Etapa - Zod Schema
Tipo: Feature
Sprint: 6
Pontos: 3
Prioridade: Media
Epic: EPIC-VAG-011
Status: Implementado

Descricao: |
  Schemas Zod para validacao dos dados em cada
  etapa do wizard.

Historia de Usuario: |
  Como sistema, eu preciso validar os dados antes
  de permitir avancar no wizard.

Requisitos Tecnicos:
  Frontend:
    - Schema: basicInfoSchema (Zod)
    - Validation: Por etapa
    - Errors: Exibicao inline

Design & Componentes:
  Componente: Zod schemas (inline)
  Arquivo: plataforma-lia/src/components/job-creation/job-creation-wizard.tsx

Criterios de Aceitacao:
  - [x] Validacao por etapa
  - [x] Mensagens de erro claras
  - [x] Bloqueio de avanco se invalido
  - [x] Highlight de campos com erro
```

---

## CARDS BACKEND RAILS (VAG-094 a VAG-108)

> **Especificacao para o time replicar no stack de producao**
> **Total:** 15 cards | **Tecnologia Alvo:** Ruby on Rails 7 API
> **Referencia:** Funcionalidades ja implementadas em Python/FastAPI (lia-agent-system)
> **Status:** Pendente = A ser implementado pelo time no ambiente Ruby

---

### CARD VAG-094: API Listagem de Vagas

```yaml
ID: VAG-094
Titulo: [BACK] API Listagem de Vagas - GET /api/v1/jobs
Tipo: Backend
Sprint: 3
Story Points: 8
Prioridade: Critica
Epic: EPIC-VAG-006
Status: Pendente

Descricao: |
  Endpoint para listagem de vagas com paginacao, filtros,
  ordenacao e busca. Suporta todos os filtros do frontend.

Historia de Usuario: |
  Como frontend, eu preciso de uma API para listar vagas
  com suporte a paginacao, filtros e ordenacao.

Requisitos Tecnicos:
  Endpoint: GET /api/v1/jobs
  Parametros:
    - page, per_page (paginacao)
    - status (ativa, paralisada, concluida, cancelada)
    - search (busca textual)
    - sort_by, sort_order (ordenacao)
    - recruiter_id (filtro por recrutador)
    - work_model (remoto, hibrido, presencial)
    - date_from, date_to (filtro por data)
  Response:
    - jobs: Array de vagas
    - meta: { total, page, per_page, total_pages }

Criterios de Aceitacao:
  - [ ] Paginacao funciona
  - [ ] Filtros aplicados corretamente
  - [ ] Ordenacao multi-coluna
  - [ ] Performance < 200ms para 1000 vagas
  - [ ] Indices de banco otimizados
```

---

### CARD VAG-095: API Detalhes da Vaga

```yaml
ID: VAG-095
Titulo: [BACK] API Detalhes da Vaga - GET /api/v1/jobs/{id}
Tipo: Backend
Sprint: 4
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Pendente

Descricao: |
  Endpoint para obter detalhes completos de uma vaga
  incluindo responsaveis, datas e configuracoes.

Historia de Usuario: |
  Como frontend, eu preciso dos detalhes de uma vaga
  para exibir no painel de preview.

Requisitos Tecnicos:
  Endpoint: GET /api/v1/jobs/{id}
  Response:
    - job: Objeto completo da vaga
    - responsaveis: recruiter, hiring_manager
    - dates: openDate, deadline, etc.
    - config: screeningConfig, pipelineConfig

Criterios de Aceitacao:
  - [ ] Retorna todos os campos necessarios
  - [ ] 404 se vaga nao existe
  - [ ] Autorizacao por empresa
```

---

### CARD VAG-096: API Funil da Vaga

```yaml
ID: VAG-096
Titulo: [BACK] API Funil da Vaga - GET /api/v1/jobs/{id}/funnel
Tipo: Backend
Sprint: 4
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Pendente

Descricao: |
  Endpoint para obter dados do funil de candidatos
  de uma vaga especifica.

Historia de Usuario: |
  Como frontend, eu preciso dos dados do funil
  para exibir na tab Visao Geral do preview.

Requisitos Tecnicos:
  Endpoint: GET /api/v1/jobs/{id}/funnel
  Response:
    - total: numero total de candidatos
    - screening: candidatos em triagem
    - interview: candidatos em entrevista
    - final: candidatos em etapa final
    - hired: contratados

Criterios de Aceitacao:
  - [ ] Contagens corretas por etapa
  - [ ] Atualizado em tempo real
  - [ ] Cache de 60s para performance
```

---

### CARD VAG-097: API Metricas da Vaga

```yaml
ID: VAG-097
Titulo: [BACK] API Metricas da Vaga - GET /api/v1/jobs/{id}/metrics
Tipo: Backend
Sprint: 4
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Pendente

Descricao: |
  Endpoint para obter metricas de performance LIA
  de uma vaga especifica.

Historia de Usuario: |
  Como frontend, eu preciso das metricas LIA
  para exibir na tab Visao Geral do preview.

Requisitos Tecnicos:
  Endpoint: GET /api/v1/jobs/{id}/metrics
  Response:
    - triagens_realizadas: int
    - tempo_medio_triagem: duration
    - taxa_aprovacao: percentage
    - wsi_medio: float
    - taxa_resposta: percentage

Criterios de Aceitacao:
  - [ ] Metricas calculadas corretamente
  - [ ] Cache de 5min para performance
```

---

### CARD VAG-098: API Roteiro Triagem

```yaml
ID: VAG-098
Titulo: [BACK] API Roteiro Triagem - GET /api/v1/jobs/{id}/screening-script
Tipo: Backend
Sprint: 4
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Pendente

Descricao: |
  Endpoint para obter o roteiro de triagem WSI
  com os 7 blocos de perguntas.

Historia de Usuario: |
  Como frontend, eu preciso do roteiro de triagem
  para exibir na tab Roteiro de Triagem do preview.

Requisitos Tecnicos:
  Endpoint: GET /api/v1/jobs/{id}/screening-script
  Response:
    - blocks: Array de 7 blocos WSI
    - questions: Perguntas por bloco
    - config: canais ativos (whatsapp, portal, voz)

Criterios de Aceitacao:
  - [ ] 7 blocos WSI retornados
  - [ ] Perguntas ordenadas por bloco
  - [ ] Configuracao de canais incluida
```

---

### CARD VAG-099: API Editar Perguntas Triagem

```yaml
ID: VAG-099
Titulo: [BACK] API Editar Perguntas - PUT /api/v1/jobs/{id}/screening-questions
Tipo: Backend
Sprint: 4
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-007
Status: Pendente

Descricao: |
  Endpoint para editar perguntas do roteiro de triagem
  de uma vaga especifica.

Historia de Usuario: |
  Como recrutador, eu preciso editar as perguntas
  de triagem diretamente do preview da vaga.

Requisitos Tecnicos:
  Endpoint: PUT /api/v1/jobs/{id}/screening-questions
  Body:
    - questions: Array de perguntas atualizadas
    - block_id: ID do bloco WSI
  Response:
    - success: boolean
    - updated_at: timestamp

Criterios de Aceitacao:
  - [ ] Atualizacao persiste no banco
  - [ ] Validacao de estrutura das perguntas
  - [ ] Auditoria de alteracoes
```

---

### CARD VAG-100: API Publicar Vagas (Bulk)

```yaml
ID: VAG-100
Titulo: [BACK] API Publicar Vagas - POST /api/v1/jobs/bulk/publish
Tipo: Backend
Sprint: 5
Story Points: 8
Prioridade: Alta
Epic: EPIC-VAG-008
Status: Pendente

Descricao: |
  Endpoint para publicar multiplas vagas em canais
  de divulgacao (LinkedIn, Indeed, site, etc.)

Historia de Usuario: |
  Como recrutador, eu preciso publicar vagas selecionadas
  em multiplos canais de uma vez.

Requisitos Tecnicos:
  Endpoint: POST /api/v1/jobs/bulk/publish
  Body:
    - job_ids: Array de IDs das vagas
    - channels: Array de canais (linkedin, indeed, site, careers_page)
  Response:
    - results: Array com status por vaga/canal
    - success_count: int
    - error_count: int

Criterios de Aceitacao:
  - [ ] Suporta multiplas vagas
  - [ ] Suporta multiplos canais
  - [ ] Retorna status individual por vaga
  - [ ] Rollback parcial se algum falhar
```

---

### CARD VAG-101: API Pausar/Ativar Vaga

```yaml
ID: VAG-101
Titulo: [BACK] API Pausar/Ativar Vaga - PATCH /api/v1/jobs/{id}/status
Tipo: Backend
Sprint: 5
Story Points: 5
Prioridade: Critica
Epic: EPIC-VAG-008
Status: Pendente

Descricao: |
  Endpoint para alterar status da vaga entre
  ativa, paralisada, cancelada, concluida.
  Nao inclui fluxo de IA (documentado separadamente).

Historia de Usuario: |
  Como recrutador, eu preciso pausar ou ativar
  vagas de forma simples e rapida.

Requisitos Tecnicos:
  Endpoint: PATCH /api/v1/jobs/{id}/status
  Body:
    - status: "active" | "paused" | "cancelled" | "completed"
    - reason: string (opcional, para pausa)
    - unpause_date: date (opcional, para pausa)
  Response:
    - job: Vaga atualizada
    - previous_status: status anterior
    - updated_at: timestamp

Criterios de Aceitacao:
  - [ ] Altera status corretamente
  - [ ] Grava motivo da pausa se informado
  - [ ] Registra auditoria
  - [ ] Nao dispara fluxo de IA (separado)
```

---

### CARD VAG-102: API Duplicar Vaga

```yaml
ID: VAG-102
Titulo: [BACK] API Duplicar Vaga - POST /api/v1/jobs/{id}/duplicate
Tipo: Backend
Sprint: 5
Story Points: 5
Prioridade: Media
Epic: EPIC-VAG-008
Status: Pendente

Descricao: |
  Endpoint para duplicar uma vaga existente
  com novo titulo e datas.

Historia de Usuario: |
  Como recrutador, eu preciso duplicar vagas
  para criar processos similares rapidamente.

Requisitos Tecnicos:
  Endpoint: POST /api/v1/jobs/{id}/duplicate
  Body:
    - new_title: string (opcional)
    - copy_pipeline: boolean
    - copy_screening: boolean
  Response:
    - new_job: Vaga criada
    - new_job_id: UUID

Criterios de Aceitacao:
  - [ ] Copia todos os campos da vaga
  - [ ] Gera novo ID e codigo
  - [ ] Status inicial: rascunho
  - [ ] Pipeline e triagem copiados se solicitado
```

---

### CARD VAG-103: API Atribuir Recrutador

```yaml
ID: VAG-103
Titulo: [BACK] API Atribuir Recrutador - PATCH /api/v1/jobs/{id}/recruiter
Tipo: Backend
Sprint: 5
Story Points: 3
Prioridade: Media
Epic: EPIC-VAG-008
Status: Pendente

Descricao: |
  Endpoint para atribuir ou alterar o recrutador
  responsavel por uma vaga.

Historia de Usuario: |
  Como gestor, eu preciso atribuir recrutadores
  as vagas da minha area.

Requisitos Tecnicos:
  Endpoint: PATCH /api/v1/jobs/{id}/recruiter
  Body:
    - recruiter_id: UUID do recrutador
    - notify: boolean (notificar recrutador)
  Response:
    - job: Vaga atualizada
    - previous_recruiter_id: UUID

Criterios de Aceitacao:
  - [ ] Atribui recrutador corretamente
  - [ ] Notifica recrutador se solicitado
  - [ ] Valida se recrutador existe
```

---

### CARD VAG-104: API Despublicar Vaga

```yaml
ID: VAG-104
Titulo: [BACK] API Despublicar Vaga - DELETE /api/v1/jobs/{id}/publications
Tipo: Backend
Sprint: 5
Story Points: 5
Prioridade: Media
Epic: EPIC-VAG-008
Status: Pendente

Descricao: |
  Endpoint para despublicar vaga de todos
  os canais de divulgacao.

Historia de Usuario: |
  Como recrutador, eu preciso despublicar vagas
  que nao devem mais receber candidaturas.

Requisitos Tecnicos:
  Endpoint: DELETE /api/v1/jobs/{id}/publications
  Parametros:
    - channels: Array de canais (opcional, todos se vazio)
  Response:
    - removed_from: Array de canais removidos
    - remaining: Array de canais ativos

Criterios de Aceitacao:
  - [ ] Remove de todos os canais se nao especificado
  - [ ] Remove de canais especificos se informado
  - [ ] Retorna status por canal
```

---

### CARD VAG-105: API Editar Vaga Completa

```yaml
ID: VAG-105
Titulo: [BACK] API Editar Vaga - PUT /api/v1/jobs/{id}
Tipo: Backend
Sprint: 5
Story Points: 8
Prioridade: Alta
Epic: EPIC-VAG-008
Status: Pendente

Descricao: |
  Endpoint para edicao completa de uma vaga,
  atualizando todos os campos permitidos.

Historia de Usuario: |
  Como recrutador, eu preciso editar todos os
  campos de uma vaga existente.

Requisitos Tecnicos:
  Endpoint: PUT /api/v1/jobs/{id}
  Body:
    - Todos os campos editaveis da vaga
  Response:
    - job: Vaga atualizada completa
    - changes: Array de campos alterados

Criterios de Aceitacao:
  - [ ] Atualiza todos os campos
  - [ ] Validacao de campos obrigatorios
  - [ ] Registra alteracoes em auditoria
  - [ ] Nao permite alterar campos bloqueados
```

---

### CARD VAG-106: API Pesquisas Salvas

```yaml
ID: VAG-106
Titulo: [BACK] API Pesquisas Salvas - CRUD /api/v1/saved-searches
Tipo: Backend
Sprint: 4
Story Points: 5
Prioridade: Media
Epic: EPIC-VAG-009
Status: Pendente

Descricao: |
  Endpoints para salvar, listar e excluir
  pesquisas/filtros favoritos do usuario.

Historia de Usuario: |
  Como recrutador, eu preciso salvar minhas
  pesquisas favoritas para reutilizar.

Requisitos Tecnicos:
  Endpoints:
    - POST /api/v1/saved-searches (criar)
    - GET /api/v1/saved-searches (listar)
    - DELETE /api/v1/saved-searches/{id} (excluir)
  Body (POST):
    - name: string
    - filters: objeto com filtros
  Response:
    - saved_searches: Array de pesquisas salvas

Criterios de Aceitacao:
  - [ ] Salva pesquisa com nome
  - [ ] Lista pesquisas do usuario
  - [ ] Exclui pesquisa existente
  - [ ] Limite de 20 pesquisas por usuario
```

---

### CARD VAG-107: API Criar Vaga

```yaml
ID: VAG-107
Titulo: [BACK] API Criar Vaga - POST /api/v1/jobs
Tipo: Backend
Sprint: 6
Story Points: 8
Prioridade: Critica
Epic: EPIC-VAG-011
Status: Pendente

Descricao: |
  Endpoint para criar nova vaga a partir dos dados
  coletados pelo wizard de criacao.

Historia de Usuario: |
  Como recrutador, eu preciso criar novas vagas
  atraves do wizard de criacao.

Requisitos Tecnicos:
  Endpoint: POST /api/v1/jobs
  Body:
    - Todos os campos das 11 etapas do wizard
  Response:
    - job: Vaga criada
    - job_id: UUID
    - job_code: Codigo gerado (ex: WDT-123)

Criterios de Aceitacao:
  - [ ] Cria vaga com todos os campos
  - [ ] Gera codigo unico automaticamente
  - [ ] Valida campos obrigatorios
  - [ ] Status inicial configuravel (rascunho/ativa)
```

---

### CARD VAG-108: API Recursos do Wizard

```yaml
ID: VAG-108
Titulo: [BACK] API Recursos do Wizard - GET endpoints auxiliares
Tipo: Backend
Sprint: 6
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-011
Status: Pendente

Descricao: |
  Endpoints auxiliares para o wizard de criacao:
  beneficios, skills, templates de pipeline.

Historia de Usuario: |
  Como frontend, eu preciso de dados auxiliares
  para popular os selects do wizard.

Requisitos Tecnicos:
  Endpoints:
    - GET /api/v1/benefits (lista de beneficios)
    - GET /api/v1/skills (lista de competencias)
    - GET /api/v1/pipeline-templates (templates de pipeline)
  Response:
    - Array de opcoes para cada endpoint

Criterios de Aceitacao:
  - [ ] Lista beneficios da empresa
  - [ ] Lista competencias por categoria
  - [ ] Lista templates de pipeline ativos
  - [ ] Cache de 1h para performance
```

---

## DEPENDENCIAS ENTRE CARDS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MAPA DE DEPENDENCIAS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   SPRINT 1                           SPRINT 2                               │
│   ────────                           ────────                               │
│   VAG-001 ─┐                                                                │
│   VAG-002 ─┼─→ VAG-006 → VAG-008 → VAG-013 → VAG-015 → VAG-018             │
│   VAG-003 ─┤            VAG-009                        VAG-019             │
│   VAG-004 ─┘            VAG-010    VAG-014             VAG-020             │
│   VAG-005               VAG-011    VAG-016 → VAG-017   VAG-021             │
│                         VAG-012                        VAG-022             │
│                                                        VAG-023             │
│                                                                              │
│   VAG-007 (API) ────────────────────→ Todos os filtros                      │
│                                                                              │
│   SPRINT 3                                                                  │
│   ────────                                                                  │
│   VAG-023 → VAG-024                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

> **Nota:** O Fluxo de Congelamento de Vaga está documentado na arquitetura dos agentes de IA: `lia-agent-system/docs/JOB_FREEZE_WORKFLOW.md`

---

## 📊 DIVISAO POR AREA TECNICA

> **Total:** 90 cards organizados por area de atuacao

### 🎨 FRONTEND (Vue.js + Nuxt + Vuetify)

> **Total:** 82 cards | **Tecnologias:** Vue.js 3, Nuxt 3, Vuetify 3, Pinia, TailwindCSS

#### EPIC-VAG-001: Header & Navegacao (4 cards)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-001 | Header Principal Gestao de Vagas | 3 | Componente UI |
| VAG-002 | Botao Nova Vaga | 5 | CTA/Interacao |
| VAG-003 | Integracao Busca Global | 3 | Componente UI |
| VAG-004 | Integracao Notificacoes | 3 | Componente UI |

#### EPIC-VAG-002: Filtros por Status (6 cards frontend)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-007 | Filtro Todas as Vagas | 3 | Filtro/Tab |
| VAG-008 | Filtro Vagas Ativas | 3 | Filtro/Tab |
| VAG-009 | Filtro Vagas Urgentes | 5 | Filtro/Tab |
| VAG-010 | Filtro Vagas Paralisadas | 3 | Filtro/Tab |
| VAG-011 | Filtro Concluidas e Canceladas | 3 | Filtro/Tab |

#### EPIC-VAG-003: LIA Prompt Central (5 cards frontend)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-012 | Container LIA Centralizado | 8 | Layout Principal |
| VAG-013 | Titulo Contextual Dinamico | 3 | Componente UI |
| VAG-014 | Input de Chat LIA | 8 | Input/Interacao |
| VAG-015 | Icones Microfone e Busca | 5 | Componente UI |
| VAG-016 | Sugestoes Contextuais | 8 | Componente AI |

#### EPIC-VAG-004: Quick Actions (5 cards)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-018 | Acao Criar Nova Vaga | 5 | Quick Action |
| VAG-019 | Acao Ver Minhas Vagas | 3 | Quick Action |
| VAG-020 | Acao Ver Todas as Vagas | 3 | Quick Action |
| VAG-021 | Acao Resumo das Vagas | 5 | Quick Action AI |
| VAG-022 | Acao Mais Ideias (AI) | 8 | Quick Action AI |

#### EPIC-VAG-005: Pagina Vazia/Onboarding (2 cards)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-023 | Empty State Design | 5 | Layout/UX |
| VAG-024 | Mensagem Boas-Vindas LIA | 3 | Componente AI |

#### EPIC-VAG-006: Tabela de Vagas (9 cards)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-028 | Tabela Estrutura Base | 8 | Componente Data |
| VAG-029 | Colunas Configuraveis | 5 | Feature Table |
| VAG-030 | Ordenacao Multi-Coluna | 3 | Feature Table |
| VAG-031 | Resize de Colunas | 5 | Feature Table |
| VAG-032 | Selecao em Lote | 5 | Feature Table |
| VAG-033 | Persistencia Config | 3 | Storage/State |
| VAG-034 | Coluna Performance LIA | 5 | Componente AI |
| VAG-035 | Coluna Roteiro Triagem | 3 | Componente UI |
| VAG-036 | Acoes por Linha | 5 | Dropdown/Menu |

#### EPIC-VAG-007: Preview da Vaga (11 cards)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-037 | Preview Panel Base | 8 | Layout Principal |
| VAG-038 | Tab Visao Geral Funil | 5 | Tab/Chart |
| VAG-039 | Tab Metricas LIA | 5 | Tab/AI |
| VAG-040 | Tab Responsaveis | 3 | Tab/Info |
| VAG-041 | Tab Datas Criticas | 3 | Tab/Info |
| VAG-042 | WSI Blocks | 13 | Componente WSI |
| VAG-043 | WSI Accordion | 5 | Componente UI |
| VAG-044 | Editor Perguntas | 8 | Editor/Form |
| VAG-045 | Config Canais Triagem | 5 | Config Panel |
| VAG-046 | Processo Breadcrumb | 3 | Componente UI |
| VAG-047 | Resize Preview | 3 | Feature UX |

#### EPIC-VAG-008: Modais Acao em Lote (9 cards)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-048 | JobActionsBar | 5 | Toolbar |
| VAG-049 | JobPublishModal | 8 | Modal |
| VAG-050 | JobInsightsModal | 13 | Modal AI |
| VAG-051 | JobDuplicateModal | 5 | Modal |
| VAG-052 | JobStatusModal | 5 | Modal |
| VAG-053 | JobAssignRecruiterModal | 5 | Modal |
| VAG-054 | JobUnpublishModal | 5 | Modal |
| VAG-055 | JobCompareModal | 8 | Modal AI |
| VAG-056 | EditJobModal | 13 | Modal Form |

#### EPIC-VAG-009: Filtros e Busca (9 cards)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-057 | JobFiltersPanel | 8 | Panel Layout |
| VAG-058 | Filtros Rapidos | 3 | Filter Buttons |
| VAG-059 | Filtro por Status | 3 | Filter Select |
| VAG-060 | Filtro por Etapa | 3 | Filter Select |
| VAG-061 | Filtro Modelo Trabalho | 3 | Filter Select |
| VAG-062 | Filtro Recrutador/Gestor | 3 | Filter Select |
| VAG-063 | Busca Booleana | 5 | Search Advanced |
| VAG-064 | Pesquisas Salvas | 5 | Feature Save |
| VAG-065 | Persistencia Filtros | 3 | Storage/Hook |

#### EPIC-VAG-010: Chat LIA Multi-Nivel (9 cards)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-066 | Mini Prompt Inline | 5 | Chat Nivel 1 |
| VAG-067 | Chat Expandido Lateral | 8 | Chat Nivel 2 |
| VAG-068 | Super Chat Criacao | 13 | Chat Nivel 3 |
| VAG-069 | Deteccao Intent | 5 | AI Feature |
| VAG-070 | Auto-Expand LIA | 3 | UX Feature |
| VAG-071 | Historico Mensagens | 3 | Chat Feature |
| VAG-072 | AudioRecordButton | 5 | Voice Input |
| VAG-073 | LiaQueriesGuide | 5 | Popover Help |
| VAG-074 | ExpandedChatModal | 8 | Modal Full |

#### EPIC-VAG-011: Job Creation Wizard (18 cards frontend)
| Card | Titulo | Pontos | Tipo |
|------|--------|--------|------|
| VAG-075 | Botao Nova Vaga Header | 3 | CTA Button |
| VAG-076 | Super Chat Container | 8 | Modal Container |
| VAG-077 | Wizard Step 1 Descricao | 8 | Wizard Step |
| VAG-078 | Wizard Step 2 Info Basicas | 5 | Wizard Step |
| VAG-079 | Wizard Step 3 Remuneracao | 5 | Wizard Step |
| VAG-080 | Wizard Step 4 Comp Tecnicas | 8 | Wizard Step |
| VAG-081 | Wizard Step 5 Comp WSI | 8 | Wizard Step |
| VAG-082 | Wizard Step 6 Idiomas | 5 | Wizard Step |
| VAG-083 | Wizard Step 7 Scorecard | 5 | Wizard Step |
| VAG-084 | Wizard Step 8 Prazos | 5 | Wizard Step |
| VAG-085 | Wizard Step 9 Pipeline | 8 | Wizard Step |
| VAG-086 | Wizard Step 10 Dados | 5 | Wizard Step |
| VAG-087 | Wizard Step 11 Revisao | 8 | Wizard Step |
| VAG-089 | Navegacao Stepper | 5 | Navigation |
| VAG-090 | Calibracao Candidatos | 8 | Feature AI |
| VAG-091 | ScreeningQuestionsPanel | 8 | Panel Form |
| VAG-092 | Integracao Pearch | 8 | Integration |
| VAG-093 | Validacao Zod | 3 | Validation |

---

### ⚙️ BACKEND (Ruby on Rails + Python)

> **Total:** 19 cards | **Tecnologias:** Rails 7 (API), Python 3.11 (IA), FastAPI, LangGraph

#### Rails API (API REST) - EPIC-VAG-006: Tabela de Vagas
| Card | Titulo | Pontos | Endpoint | Tipo |
|------|--------|--------|----------|------|
| VAG-006 | API Contadores por Status | 5 | `GET /api/v1/jobs/stats` | Endpoint GET |
| VAG-094 | API Listagem de Vagas | 8 | `GET /api/v1/jobs` | Endpoint GET |

#### Rails API (API REST) - EPIC-VAG-007: Preview da Vaga
| Card | Titulo | Pontos | Endpoint | Tipo |
|------|--------|--------|----------|------|
| VAG-095 | API Detalhes da Vaga | 5 | `GET /api/v1/jobs/{id}` | Endpoint GET |
| VAG-096 | API Funil da Vaga | 5 | `GET /api/v1/jobs/{id}/funnel` | Endpoint GET |
| VAG-097 | API Metricas da Vaga | 5 | `GET /api/v1/jobs/{id}/metrics` | Endpoint GET |
| VAG-098 | API Roteiro Triagem | 5 | `GET /api/v1/jobs/{id}/screening-script` | Endpoint GET |
| VAG-099 | API Editar Perguntas Triagem | 5 | `PUT /api/v1/jobs/{id}/screening-questions` | Endpoint PUT |

#### Rails API (API REST) - EPIC-VAG-008: Modais de Acao
| Card | Titulo | Pontos | Endpoint | Tipo |
|------|--------|--------|----------|------|
| VAG-100 | API Publicar Vagas (Bulk) | 8 | `POST /api/v1/jobs/bulk/publish` | Endpoint POST |
| VAG-101 | API Pausar/Ativar Vaga | 5 | `PATCH /api/v1/jobs/{id}/status` | Endpoint PATCH |
| VAG-102 | API Duplicar Vaga | 5 | `POST /api/v1/jobs/{id}/duplicate` | Endpoint POST |
| VAG-103 | API Atribuir Recrutador | 3 | `PATCH /api/v1/jobs/{id}/recruiter` | Endpoint PATCH |
| VAG-104 | API Despublicar Vaga | 5 | `DELETE /api/v1/jobs/{id}/publications` | Endpoint DELETE |
| VAG-105 | API Editar Vaga Completa | 8 | `PUT /api/v1/jobs/{id}` | Endpoint PUT |

#### Rails API (API REST) - EPIC-VAG-009: Filtros
| Card | Titulo | Pontos | Endpoint | Tipo |
|------|--------|--------|----------|------|
| VAG-106 | API Pesquisas Salvas | 5 | `POST/GET /api/v1/saved-searches` | Endpoint CRUD |

#### Rails API (API REST) - EPIC-VAG-011: Job Creation Wizard
| Card | Titulo | Pontos | Endpoint | Tipo |
|------|--------|--------|----------|------|
| VAG-107 | API Criar Vaga | 8 | `POST /api/v1/jobs` | Endpoint POST |
| VAG-108 | API Recursos do Wizard | 5 | `GET /api/v1/benefits`, `/skills`, `/pipeline-templates` | Endpoint GET |

#### Python/LangGraph (IA/Agentes)
| Card | Titulo | Pontos | Endpoint | Tipo |
|------|--------|--------|----------|------|
| VAG-017 | Integracao Backend LIA | 13 | `/lia/chat` | Agentes LIA |
| VAG-088 | Endpoint /lia/job-wizard/step | 13 | `/lia/job-wizard/step` | Endpoint POST |

#### Full-Stack (Rails + Vue)
| Card | Titulo | Pontos | Endpoint | Tipo |
|------|--------|--------|----------|------|
| VAG-005 | Sistema de Tabs de Filtro | 8 | N/A | Frontend + API |

---

### 🤖 INTELIGENCIA ARTIFICIAL (Python + LangGraph + Claude)

> **Cards relacionados a LIA, agentes, prompts e intents**

| Card | Descricao | Integracao AI | Sprint |
|------|-----------|---------------|--------|
| VAG-016 | Sugestoes Contextuais | Gemini/Claude - NLU | Sprint 2 |
| VAG-017 | Integracao Backend LIA | LangGraph + Claude + Gemini | Sprint 2 |
| VAG-021 | Resumo das Vagas | Claude Sonnet | Sprint 2 |
| VAG-022 | Mais Ideias (AI) | Claude Sonnet | Sprint 2 |
| VAG-024 | Boas-Vindas LIA | Gemini Flash | Sprint 3 |
| VAG-034 | Performance LIA Triagens | Metricas Agentes | Sprint 4 |
| VAG-039 | Metricas LIA | Analytics AI | Sprint 4 |
| VAG-050 | JobInsightsModal | Claude Analysis | Sprint 5 |
| VAG-055 | JobCompareModal | Claude Compare | Sprint 5 |
| VAG-068 | Super Chat Criacao | LangGraph Wizard | Sprint 5 |
| VAG-069 | Deteccao Intent | IntentClassifier | Sprint 5 |
| VAG-088 | Endpoint job-wizard | LangGraph + Claude | Sprint 6 |
| VAG-090 | Calibracao Candidatos | AI Matching | Sprint 6 |

**Servicos de IA Utilizados:**
- **IntentClassifierService:** Classificacao de intents (SALARY, SKILLS, TIME, PROCESS, GENERAL)
- **salary_insights:** Benchmark salarial interno e de mercado
- **skills_insights:** Analise de skills e requisitos
- **time_insights:** Tempo de preenchimento de vagas
- **process_explainer:** Explicacao do processo WSI
- **general_assistant:** Respostas gerais via Gemini LLM

---

### 🔗 INTEGRACOES EXTERNAS

> **APIs e servicos externos utilizados**

| Card | Integracao | Tipo | Uso |
|------|------------|------|-----|
| VAG-004 | Twilio / SendGrid | Comunicacao | Notificacoes push/email |
| VAG-015 | Web Speech API / Deepgram | Voice | Transcricao de voz |
| VAG-017 | Anthropic Claude | LLM | Respostas inteligentes |
| VAG-017 | Google Gemini | LLM | Fallback e voice |
| VAG-092 | Pearch AI | Sourcing | Busca de candidatos global |

**APIs por Categoria:**

| Categoria | Servico | Cards | Custo Estimado |
|-----------|---------|-------|----------------|
| LLM Principal | Anthropic Claude 4 Sonnet | VAG-017, VAG-021, VAG-022 | $3-15/1M tokens |
| LLM Fallback | Google Gemini 1.5 Flash | VAG-015, VAG-017 | $0.075-0.30/1M tokens |
| Voice-to-Text | Web Speech API | VAG-015, VAG-072 | Gratuito |
| Voice-to-Text | Deepgram (alternativa) | VAG-015, VAG-072 | ~$0.0043/min |
| Sourcing | Pearch AI | VAG-092 | Por credito/reveal |
| Comunicacao | Twilio (WhatsApp/SMS) | VAG-004 | ~$0.005/msg |
| Email | SendGrid | VAG-004 | Tier gratuito |
| SSO/Auth | WorkOS | VAG-004 | ~$125/mo base |

---

### 🏗️ INFRAESTRUTURA & FERRAMENTAS

> **GCP, Redis, PostgreSQL, Autenticacao, Storage, Cache**

| Componente | Tecnologia | Cards Relacionados | Ambiente |
|------------|------------|-------------------|----------|
| Banco Principal | PostgreSQL (Neon) | VAG-006, VAG-017, todos | GCP Cloud SQL |
| Cache/Sessions | Redis | VAG-022, VAG-033, VAG-065 | GCP Memorystore |
| ORM TypeScript | Drizzle ORM | Todos frontend | - |
| ORM Python | SQLAlchemy | VAG-017, VAG-088 | - |
| Autenticacao | WorkOS + JWT | VAG-004 | SSO/SCIM/MFA |
| Storage | GCP Cloud Storage | VAG-077, VAG-086 | Arquivos/CVs |
| Containers | Docker + Cloud Run | Backend | GCP |
| CI/CD | GitHub Actions | Todos | Deploy automatico |

**Secrets Necessarios:**
```
# LLMs (Via Replit Integration)
ANTHROPIC_API_KEY, GEMINI_API_KEY

# Banco (Via Replit - automatico)
DATABASE_URL, PGHOST, PGUSER, PGPASSWORD, PGDATABASE

# Autenticacao
WORKOS_API_KEY, WORKOS_CLIENT_ID

# Comunicacao
TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

# Sourcing
PEARCH_API_KEY
```

---

## ⏱️ ESTIMATIVAS DE TEMPO

> **Formula de Conversao Story Points → Horas**

| Story Points | Horas | Equivalente |
|--------------|-------|-------------|
| 1 pt | 1h | Tarefa trivial |
| 2 pts | 2h | Tarefa simples |
| 3 pts | 4h | Meio dia |
| 5 pts | 8h | 1 dia |
| 8 pts | 16h | 2 dias |
| 13 pts | 24h | 3 dias |

### 🚀 Fator de Aceleracao com Ferramentas Modernas

| Ferramenta | Reducao de Tempo |
|------------|------------------|
| Replit (Prototipacao rapida) | -20% |
| Claude Code / Cursor AI | -15% |
| Componentes prontos (Vuetify) | -10% |
| **Fator de aceleracao total** | **0.55x (45% de reducao)** |

---

### 📈 Estimativas por Epico

| Epico | Cards | Story Points | Horas Brutas | Horas c/ Aceleracao | Sprints (40h) |
|-------|-------|--------------|--------------|---------------------|---------------|
| EPIC-VAG-001: Header & Navegacao | 4 | 14 | 20h | 11h | 0.3 |
| EPIC-VAG-002: Filtros por Status | 7 | 30 | 48h | 26h | 0.7 |
| EPIC-VAG-003: LIA Prompt Central | 6 | 45 | 84h | 46h | 1.2 |
| EPIC-VAG-004: Quick Actions | 5 | 24 | 40h | 22h | 0.6 |
| EPIC-VAG-005: Pagina Vazia | 2 | 8 | 12h | 7h | 0.2 |
| EPIC-VAG-006: Tabela de Vagas | 9 | 42 | 68h | 37h | 0.9 |
| EPIC-VAG-007: Preview da Vaga | 11 | 61 | 104h | 57h | 1.4 |
| EPIC-VAG-008: Modais Acao Lote | 9 | 67 | 120h | 66h | 1.7 |
| EPIC-VAG-009: Filtros e Busca | 9 | 36 | 56h | 31h | 0.8 |
| EPIC-VAG-010: Chat LIA Multi-Nivel | 9 | 55 | 96h | 53h | 1.3 |
| EPIC-VAG-011: Job Creation Wizard | 19 | 122 | 228h | 125h | 3.1 |
| **TOTAL** | **90** | **504** | **876h** | **482h** | **12.0** |

---

### 📊 Estimativas por Area Tecnica

| Area | Cards | Story Points | Horas Brutas | Horas c/ Aceleracao | Sprints |
|------|-------|--------------|--------------|---------------------|---------|
| 🎨 Frontend (Vue.js/Nuxt) | 82 | 460 | 796h | 438h | 11.0 |
| ⚙️ Backend Rails (API) | 2 | 13 | 24h | 13h | 0.3 |
| 🤖 Backend Python (IA) | 2 | 26 | 48h | 26h | 0.7 |
| 🔧 Full-Stack | 4 | 5 | 8h | 4h | 0.1 |
| **TOTAL** | **90** | **504** | **876h** | **482h** | **12.0** |

---

### 📋 Resumo Executivo de Tempo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     RESUMO EXECUTIVO DE TEMPO                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Total de Cards:           90 cards                                     │
│   Total Story Points:       504 pts                                      │
│                                                                          │
│   ────────────────────────────────────────────────────────────────────   │
│                                                                          │
│   TEMPO BRUTO (sem ferramentas):                                         │
│   • Horas totais:           876 horas                                    │
│   • Sprints (40h/semana):   22 sprints (~5.5 meses)                      │
│                                                                          │
│   ────────────────────────────────────────────────────────────────────   │
│                                                                          │
│   TEMPO COM ACELERACAO (Replit + AI Tools):                              │
│   • Fator de reducao:       0.55x (45% menos tempo)                      │
│   • Horas totais:           482 horas                                    │
│   • Sprints (40h/semana):   12 sprints (~3 meses)                        │
│                                                                          │
│   ────────────────────────────────────────────────────────────────────   │
│                                                                          │
│   ECONOMIA DE TEMPO:        394 horas (~10 sprints / 2.5 meses)          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLUXO IDEAL DE DESENVOLVIMENTO

> **Cronograma otimizado de 6 sprints com ferramentas de aceleracao**

### 📅 Fase 1: Setup & Prototipacao (Sprint 0)

**Duracao:** 1 semana (40h)

| Atividade | Responsavel | Ferramentas | Entregavel |
|-----------|-------------|-------------|------------|
| Setup repo Vue.js + Nuxt | Frontend Dev | Replit, npm | Projeto base configurado |
| Setup repo Rails API | Backend Dev | Rails CLI | API skeleton |
| Setup repo Python IA | AI Dev | uv, FastAPI | Agentes base |
| Config Vuetify + TailwindCSS | Frontend Dev | npm | Design system |
| Config PostgreSQL + Redis | DevOps | Docker, GCP | Banco desenvolvimento |
| Prototipacao rapida UI | Designer/Dev | Replit, Figma | Wireframes funcionais |
| Setup Storybook | Frontend Dev | npm | Componentes isolados |

**Checklist Sprint 0:**
- [ ] Repositorios criados e configurados
- [ ] Design system base (cores, tipografia, tokens)
- [ ] Componentes base em Storybook
- [ ] Banco de dados rodando
- [ ] CI/CD configurado (GitHub Actions)
- [ ] Prototipo inicial validado

---

### 📅 Fase 2: Desenvolvimento Frontend (Sprints 1-3)

**Duracao:** 3 sprints (120h com aceleracao)

**Workflow:**
```
Prototipo Replit → Codigo Vue.js → Storybook → Review → Deploy
```

| Sprint | Epicos | Cards | Horas |
|--------|--------|-------|-------|
| Sprint 1 | EPIC-VAG-001, EPIC-VAG-002 | 11 | 37h |
| Sprint 2 | EPIC-VAG-003, EPIC-VAG-004, EPIC-VAG-005 | 13 | 75h |
| Sprint 3 | EPIC-VAG-006 (Tabela) | 9 | 37h |

**Ferramentas Utilizadas:**
- **Cursor AI:** Autocompletion para Vue.js e TypeScript
- **Claude Code:** Geracao de componentes, refactoring
- **Storybook:** Desenvolvimento isolado de componentes
- **Vuetify 3:** Componentes prontos (reduz 10% do tempo)

**Entregaveis Sprint 1-3:**
- [ ] Header com navegacao completa
- [ ] Sistema de tabs e filtros
- [ ] LIA Prompt central funcional
- [ ] Quick actions
- [ ] Tabela de vagas com todas as features
- [ ] Design system completo em Storybook

---

### 📅 Fase 3: Desenvolvimento Backend (Sprints 2-4)

**Duracao:** 3 sprints (paralelo com frontend)

| Sprint | Foco | Cards | Horas |
|--------|------|-------|-------|
| Sprint 2 | Rails API base + endpoints CRUD | VAG-006 | 13h |
| Sprint 3 | Python/LangGraph agentes LIA | VAG-017 | 26h |
| Sprint 4 | Endpoints wizard + integracao | VAG-088 | 26h |

**Rails API (Ruby on Rails 7):**
- CRUD de vagas
- Autenticacao (WorkOS)
- Webhooks
- Endpoints de estatisticas

**Python/LangGraph (Agentes LIA):**
- IntentClassifierService
- salary_insights, skills_insights, time_insights
- process_explainer, general_assistant
- Integracao com Claude + Gemini

**Entregaveis Sprint 2-4:**
- [ ] API REST completa e documentada
- [ ] Agentes LIA funcionais
- [ ] Testes unitarios e integracao
- [ ] Documentacao OpenAPI/Swagger

---

### 📅 Fase 4: Integracao & IA (Sprints 4-5)

**Duracao:** 2 sprints (80h com aceleracao)

| Sprint | Epicos | Cards | Foco |
|--------|--------|-------|------|
| Sprint 4 | EPIC-VAG-007, EPIC-VAG-009 | 20 | Preview + Filtros |
| Sprint 5 | EPIC-VAG-008, EPIC-VAG-010 | 18 | Modais + Chat LIA |

**Atividades Principais:**
- Integrar frontend + backend
- Conectar agentes LIA ao chat
- Implementar modais de acao em lote
- Chat LIA multi-nivel (inline → expanded → super)

**Entregaveis Sprint 4-5:**
- [ ] Preview de vaga com todas as tabs
- [ ] Sistema de filtros avancados
- [ ] Todos os 9 modais funcionais
- [ ] Chat LIA em todos os niveis
- [ ] Integracao completa frontend ↔ backend ↔ IA

---

### 📅 Fase 5: Job Creation Wizard (Sprint 6)

**Duracao:** 1 sprint (125h com aceleracao)

| Epico | Cards | Horas |
|-------|-------|-------|
| EPIC-VAG-011: Job Creation Wizard | 19 | 125h |

**Componentes do Wizard:**
1. Step 1: Descricao Inicial via Chat
2. Step 2: Informacoes Basicas
3. Step 3: Remuneracao e Beneficios
4. Step 4: Competencias Tecnicas
5. Step 5: Competencias WSI Comportamentais
6. Step 6: Requisitos Idiomas e Formacao
7. Step 7: Scorecard de Avaliacao
8. Step 8: Prazos e Cronograma
9. Step 9: Pipeline do Processo
10. Step 10: Solicitacao de Dados
11. Step 11: Revisao Final e Publicacao

**Entregaveis Sprint 6:**
- [ ] Wizard completo com 11 etapas
- [ ] Navegacao stepper visual
- [ ] Calibracao de candidatos (sourcing)
- [ ] Integracao com Pearch AI
- [ ] Validacao Zod em todas as etapas

---

### 📅 Fase 6: Polimento & Deploy (Sprint 7)

**Duracao:** 1 sprint (40h)

| Atividade | Responsavel | Ferramentas |
|-----------|-------------|-------------|
| Testes E2E | QA | Playwright, Cypress |
| Testes de Performance | DevOps | Lighthouse, k6 |
| Bug fixes | Todos | - |
| Code review final | Tech Lead | GitHub |
| Deploy staging | DevOps | GCP Cloud Run |
| Deploy producao | DevOps | GCP Cloud Run |
| Documentacao final | Todos | Notion, README |

**Checklist Deploy:**
- [ ] Todos os testes passando
- [ ] Performance score > 90 (Lighthouse)
- [ ] Zero erros criticos
- [ ] Documentacao atualizada
- [ ] Rollback strategy definida
- [ ] Monitoring configurado

---

### 🛠️ FERRAMENTAS DE ACELERACAO

| Ferramenta | Uso Principal | Beneficio | Reducao de Tempo |
|------------|---------------|-----------|------------------|
| **Replit** | Prototipacao | Validacao rapida de conceitos, ambiente pronto | -20% |
| **Cursor AI** | Coding diario | Autocompletion inteligente, sugestoes contextuais | -15% |
| **Claude Code** | Geracao | Codigo boilerplate, refactoring, documentacao | -15% |
| **Storybook** | Design System | Componentes isolados, visual testing | -10% |
| **VSCode** | IDE Principal | Extensoes Vue/Rails, debugging | - |
| **GitHub Copilot** | Pair programming | Sugestoes contextuais em tempo real | -10% |
| **Vuetify 3** | Componentes UI | Biblioteca pronta, reduz implementacao | -10% |
| **Drizzle ORM** | Database | Type-safe, migrations automaticas | -5% |

---

### 💻 STACK TECNICA RECOMENDADA

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        STACK TECNICA COMPLETA                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   FRONTEND                                                               │
│   ────────                                                               │
│   • Framework:     Vue.js 3 + Nuxt 3                                     │
│   • UI Library:    Vuetify 3                                             │
│   • State:         Pinia                                                 │
│   • Styling:       TailwindCSS                                           │
│   • Forms:         VeeValidate + Zod                                     │
│   • HTTP:          $fetch (Nuxt) / Axios                                 │
│   • Testing:       Vitest, Playwright                                    │
│                                                                          │
│   BACKEND API                                                            │
│   ───────────                                                            │
│   • Framework:     Ruby on Rails 7                                       │
│   • Database:      PostgreSQL 15                                         │
│   • Cache:         Redis                                                 │
│   • ORM:           ActiveRecord                                          │
│   • Auth:          WorkOS (SSO/SCIM/MFA)                                 │
│   • API Docs:      OpenAPI/Swagger                                       │
│   • Testing:       RSpec, FactoryBot                                     │
│                                                                          │
│   BACKEND IA                                                             │
│   ──────────                                                             │
│   • Runtime:       Python 3.11                                           │
│   • Framework:     FastAPI                                               │
│   • Orquestracao:  LangGraph                                             │
│   • LLM Principal: Anthropic Claude Sonnet                               │
│   • LLM Fallback:  Google Gemini 1.5 Flash                               │
│   • ORM:           SQLAlchemy 2.0                                        │
│   • Testing:       pytest                                                │
│                                                                          │
│   INFRAESTRUTURA                                                         │
│   ──────────────                                                         │
│   • Cloud:         GCP (Google Cloud Platform)                           │
│   • Compute:       Cloud Run (containers)                                │
│   • Database:      Cloud SQL (PostgreSQL)                                │
│   • Cache:         Memorystore (Redis)                                   │
│   • Storage:       Cloud Storage                                         │
│   • Containers:    Docker                                                │
│   • CI/CD:         GitHub Actions                                        │
│                                                                          │
│   DEPLOY                                                                 │
│   ──────                                                                 │
│   • Frontend:      Vercel / Netlify                                      │
│   • Backend API:   GCP Cloud Run                                         │
│   • Backend IA:    GCP Cloud Run                                         │
│   • Database:      GCP Cloud SQL                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 📊 Cronograma Visual

```
        Sprint 0   Sprint 1   Sprint 2   Sprint 3   Sprint 4   Sprint 5   Sprint 6   Sprint 7
        ────────   ────────   ────────   ────────   ────────   ────────   ────────   ────────
        
SETUP   ████████
        
FRONT              ████████   ████████   ████████   ████████   ████████   ████████
                   Header     LIA        Tabela     Preview    Modais     Wizard
                   Filtros    Quick      
                              Actions
                              
BACK                          ████████   ████████   ████████
                              API        Agentes    Wizard
                              Rails      LIA        Endpoint
                              
INTEG                                               ████████   ████████
                                                    Frontend   Chat LIA
                                                    + Backend
                                                    
DEPLOY                                                                              ████████
                                                                                    Testes
                                                                                    Deploy
```

---


## METRICAS DE SUCESSO

| Metrica | Target | Como Medir |
|---------|--------|------------|
| Tempo para criar vaga | < 3 min | Analytics |
| Uso do LIA prompt | > 40% usuarios | Event tracking |
| Filtros mais usados | Ativas, Urgentes | Click tracking |
| Empty state UX | > 90% sucesso | Funnel analytics |
| NPS pagina | > 8 | Survey |

---

## CARDS BACKEND IA - PYTHON/LANGGRAPH (VAG-109 a VAG-114)

> **Especificacao de funcionalidades de IA - JA IMPLEMENTADAS**
> **Total:** 6 cards | **Tecnologia:** Python + FastAPI + LangGraph + Gemini
> **Stack:** MESMO para prototipo e producao (Python/LangGraph)
> **Status:** Implementado = Pronto para uso em producao
> **Arquivos de Referencia:** lia-agent-system/app/services/

---

### CARD VAG-109: [BACK-IA] Servico de Comparacao de Candidatos

```yaml
ID: VAG-109
Titulo: [BACK-IA] Servico de Comparacao de Candidatos
Tipo: Backend IA
Sprint: 4
Story Points: 13
Prioridade: Alta
Epic: EPIC-VAG-008
Status: Implementado
Implementado: 22 Janeiro 2026

Descricao: |
  Servico backend para comparacao inteligente de candidatos
  usando metodologia unificada LIA com cenarios ponderados.

Historia de Usuario: |
  Como sistema LIA, eu preciso comparar candidatos de forma
  justa e cientifica usando pesos contextuais.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/candidate_comparison_service.py
  Classe: CandidateComparisonService
  
  Cenarios Implementados:
    Cenario A (Screened - WSI Completo):
      - Rubricas BARS: 40%
      - WSI Score: 25%
      - Big Five: 15%
      - Pre-requisitos: 10%
      - Historico: 10%
    
    Cenario B (CV Only - Sem WSI):
      - Rubricas BARS: 60%
      - Pre-requisitos: 25%
      - Historico: 15%
    
    Cenario C (Sem Vaga Definida):
      - Historico: 50%
      - Completude CV: 30%
      - Recency: 20%
  
  Features:
    - Deteccao automatica de cenario
    - WSI Scoped por VacancyCandidate
    - Fallback para VoiceScreeningCall
    - 39 testes de validacao

Criterios de Aceitacao:
  - [x] Cenario A calcula score corretamente
  - [x] Cenario B calcula score corretamente
  - [x] Cenario C calcula score corretamente
  - [x] Deteccao automatica de cenario funciona
  - [x] WSI scoped por job implementado
  - [x] 39 testes passando
```

---

### CARD VAG-110: [BACK-IA] Servico de Score LIA

```yaml
ID: VAG-110
Titulo: [BACK-IA] Servico de Score LIA Unificado
Tipo: Backend IA
Sprint: 4
Story Points: 13
Prioridade: Critica
Epic: EPIC-VAG-008
Status: Implementado
Implementado: 22 Janeiro 2026

Descricao: |
  Servico principal para calculo de score LIA usando
  metodologia unificada de 4 camadas.

Historia de Usuario: |
  Como sistema LIA, eu preciso calcular scores de candidatos
  usando metodologia cientifica validada.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/lia_score_service.py
  Classe: LiaScoreService
  
  Camadas Implementadas:
    1. Pre-requisitos (Filtros Eliminatorios)
    2. Rubricas BARS (Schmidt & Hunter 1998)
    3. WSI (Bloom + Dreyfus + Big Five + CBI)
    4. Calibration Loop (Aprendizado Continuo)
  
  Escala BARS:
    - Exceeds: 100 pontos
    - Meets: 75 pontos
    - Partial: 40 pontos
    - Missing: 0 pontos
  
  Prioridades de Requisitos:
    - Critico: peso 1.0
    - Alto: peso 0.8
    - Medio: peso 0.5
    - Baixo: peso 0.25

Criterios de Aceitacao:
  - [x] Calculo de score funciona
  - [x] Pre-requisitos aplicados
  - [x] Rubricas BARS calculadas
  - [x] WSI integrado
  - [x] Calibration loop registra feedback
```

---

### CARD VAG-111: [BACK-IA] Servico de Relatorio de Candidato

```yaml
ID: VAG-111
Titulo: [BACK-IA] Servico de Relatorio de Candidato (Parecer LIA)
Tipo: Backend IA
Sprint: 5
Story Points: 8
Prioridade: Alta
Epic: EPIC-VAG-008
Status: Implementado
Implementado: 22 Janeiro 2026

Descricao: |
  Servico para geracao de pareceres automaticos LIA
  com justificativas e recomendacoes.

Historia de Usuario: |
  Como recrutador, eu quero ver o parecer da LIA sobre
  cada candidato com justificativas claras.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/candidate_report_service.py
  Classe: CandidateReportService
  
  Parecer Gerado:
    - Score consolidado (0-100)
    - Classificacao (Forte/Medio/Fraco)
    - Pontos fortes (lista)
    - Areas de desenvolvimento (lista)
    - Justificativa por camada
    - Recomendacao (Aprovar/Reprovar/Revisar)
  
  Transparencia (EU AI Act):
    - Explicacao de cada fator
    - Peso de cada componente
    - Motivo de reprovacao (se aplicavel)

Criterios de Aceitacao:
  - [x] Parecer gerado automaticamente
  - [x] Justificativas claras
  - [x] Recomendacao com confianca
  - [x] Transparencia mantida
```

---

### CARD VAG-112: [BACK-IA] Metodologia Unificada LIA

```yaml
ID: VAG-112
Titulo: [BACK-IA] Documentacao Metodologia Unificada LIA
Tipo: Documentacao
Sprint: 4
Story Points: 5
Prioridade: Critica
Epic: EPIC-VAG-008
Status: Implementado
Implementado: 22 Janeiro 2026

Descricao: |
  Documentacao tecnica da metodologia unificada LIA
  consolidando todas as abordagens de IA.

Historia de Usuario: |
  Como desenvolvedor, eu preciso entender a metodologia
  LIA para implementar corretamente.

Requisitos Tecnicos:
  Arquivo: docs/LIA_UNIFIED_METHODOLOGY.md
  
  Conteudo Documentado:
    - 4 Camadas da metodologia
    - Fundamentacao cientifica (referencias)
    - Formulas de calculo
    - Cenarios de comparacao A/B/C
    - Exemplos praticos
    - Decisoes arquiteturais
  
  Decisao: Similar Search Arquivada
    - Substituida por Rubricas BARS
    - Motivo: Validacao 0.51 (Schmidt & Hunter)

Criterios de Aceitacao:
  - [x] Documentacao completa
  - [x] Fundamentacao cientifica inclusa
  - [x] Formulas explicadas
  - [x] Decisoes arquiteturais registradas
```

---

### CARD VAG-113: [BACK-IA] WSI Scoped por Vaga

```yaml
ID: VAG-113
Titulo: [BACK-IA] WSI Scoped por Vaga (VacancyCandidate)
Tipo: Backend IA
Sprint: 4
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-008
Status: Implementado
Implementado: 22 Janeiro 2026

Descricao: |
  Refinamento do WSI para priorizar dados da relacao
  VacancyCandidate sobre VoiceScreeningCall global.

Historia de Usuario: |
  Como sistema LIA, eu preciso usar o WSI especifico
  de cada vaga para comparacoes justas.

Requisitos Tecnicos:
  Logica Implementada:
    1. Buscar VacancyCandidate.wsi_score (prioridade)
    2. Se null, buscar VoiceScreeningCall mais recente
    3. Se null, wsi_score = 0
  
  Campos VacancyCandidate:
    - wsi_completed: boolean
    - wsi_score: float (0-100)
    - wsi_completed_at: timestamp
  
  Migracao: Campos adicionados via Alembic

Criterios de Aceitacao:
  - [x] Prioriza VacancyCandidate.wsi_score
  - [x] Fallback para VoiceScreeningCall funciona
  - [x] Comparacao usa WSI correto por vaga
```

---

### CARD VAG-114: [BACK-IA] Testes de Validacao de Cenarios

```yaml
ID: VAG-114
Titulo: [BACK-IA] Testes de Validacao - Cenarios de Comparacao
Tipo: QA / Testes
Sprint: 4
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-008
Status: Implementado
Implementado: 22 Janeiro 2026

Descricao: |
  Suite de testes automatizados para validar cenarios
  de comparacao de candidatos.

Historia de Usuario: |
  Como desenvolvedor, eu preciso garantir que a logica
  de comparacao esta correta.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/tests/test_comparison_scenarios.py
  
  Testes Implementados: 39 casos
    Cenario A (13 testes):
      - Pesos corretos (40/25/15/10/10)
      - WSI priorizado de VacancyCandidate
      - Fallback para VoiceScreeningCall
    
    Cenario B (13 testes):
      - Pesos corretos (60/25/15)
      - Funciona sem WSI
      - Pre-requisitos eliminatorios
    
    Cenario C (13 testes):
      - Pesos corretos (50/30/20)
      - Deteccao automatica sem job
      - Historico priorizado

Criterios de Aceitacao:
  - [x] 39 testes passando
  - [x] Cobertura de todos os cenarios
  - [x] Edge cases cobertos
  - [x] CI/CD integrado
```

---

## CARDS BACKEND IA - SERVICOS TRANSVERSAIS (VAG-115 a VAG-122)

> **Servicos de IA compartilhados entre Gestao de Vagas e Funil de Talentos**
> **Total:** 8 cards | **Tecnologia:** Python + FastAPI + LangGraph + Gemini/Claude
> **Stack:** MESMO para prototipo e producao (Python/LangGraph)
> **Status:** Implementado = Pronto para uso em producao
> **Observacao:** Estes servicos tambem estao documentados em `funil-talentos-cards-jira.md` (FUN-IA-001 a 008)

### Dependencias em Gestao de Vagas

| Card Gestao de Vagas | Servico IA Dependente |
|---------------------|----------------------|
| VAG-042 Tab WSI Blocks | VAG-115 WSI Service |
| VAG-043 WSI Accordion | VAG-115 WSI Service |
| VAG-044 Editor de Perguntas | VAG-117 WSI Question Generator |
| VAG-045 Config Canais Triagem | VAG-115 WSI Service |
| VAG-081 Wizard Step 5 - WSI | VAG-117 WSI Question Generator |
| VAG-091 ScreeningQuestionsPanel | VAG-117 WSI Question Generator |
| VAG-034 Coluna Performance LIA | VAG-110 LIA Score Service |
| VAG-035 Coluna Roteiro Triagem | VAG-115 WSI Service |

---

### CARD VAG-115: [BACK-IA] WSI Service - Metodologia Cientifica

```yaml
ID: VAG-115
Titulo: [BACK-IA] WSI Service - Metodologia Cientifica de Avaliacao
Tipo: Backend IA
Sprint: 3
Story Points: 13
Prioridade: Critica
Status: Implementado
Implementado: Janeiro 2026
Transversal: Sim (tambem em Funil de Talentos como FUN-IA-001)

Descricao: |
  Servico principal da metodologia WSI (WeDoTalent Skill Index)
  para avaliacao cientifica de candidatos.

Historia de Usuario: |
  Como sistema LIA, eu preciso avaliar candidatos usando
  frameworks cientificos validados.

Uso em Gestao de Vagas:
  - VAG-042: Exibir blocos WSI no preview da vaga
  - VAG-043: Accordion expansivel com perguntas
  - VAG-045: Configurar canais de triagem

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/wsi_service.py
  Classe: WSIService
  
  Frameworks Implementados:
    1. CBI (Competency-Based Interviewing) - McClelland, 1973
    2. Bloom's Taxonomy (Revisada) - Anderson et al., 2001
    3. Dreyfus Model - Dreyfus & Dreyfus, 1980
    4. Big Five (OCEAN) - Goldberg, 1992

Criterios de Aceitacao:
  - [x] Analise de transcricao funciona
  - [x] Scores calculados corretamente
  - [x] Big Five profile gerado
  - [x] Parecer automatico gerado
```

---

### CARD VAG-116: [BACK-IA] CV Parser Service

```yaml
ID: VAG-116
Titulo: [BACK-IA] CV Parser - Extracao Inteligente de Curriculos
Tipo: Backend IA
Sprint: 2
Story Points: 8
Prioridade: Alta
Status: Implementado
Implementado: Janeiro 2026
Transversal: Sim (tambem em Funil de Talentos como FUN-IA-002)

Descricao: |
  Servico para extracao automatica de dados estruturados
  de curriculos usando LLM.

Historia de Usuario: |
  Como recrutador, eu quero que o sistema extraia dados
  do curriculo automaticamente para agilizar o cadastro.

Uso em Gestao de Vagas:
  - Aplicacao de candidatos em vagas
  - Extracao de skills para matching
  - Pre-preenchimento de formularios

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/cv_parser.py
  Classe: CVParserService
  
  Formatos Suportados: PDF, DOCX, TXT
  
  Dados Extraidos:
    - Nome, email, telefone
    - Experiencias profissionais
    - Formacao academica
    - Skills tecnicas
    - Idiomas e certificacoes

Criterios de Aceitacao:
  - [x] PDF parseado corretamente
  - [x] DOCX parseado corretamente
  - [x] Skills extraidas como array
```

---

### CARD VAG-117: [BACK-IA] WSI Question Generator

```yaml
ID: VAG-117
Titulo: [BACK-IA] Gerador de Perguntas WSI
Tipo: Backend IA
Sprint: 3
Story Points: 8
Prioridade: Alta
Status: Implementado
Implementado: Janeiro 2026
Transversal: Sim (tambem em Funil de Talentos como FUN-IA-003)

Descricao: |
  Servico para geracao automatica de perguntas de triagem
  baseadas em frameworks cientificos.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA sugira perguntas
  relevantes para avaliar competencias especificas.

Uso em Gestao de Vagas:
  - VAG-044: Editor de perguntas no preview
  - VAG-081: Wizard Step 5 - Competencias WSI
  - VAG-091: ScreeningQuestionsPanel no wizard

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/wsi_question_generator.py
  Classe: WSIQuestionGenerator
  
  Tipos de Perguntas:
    - CBI (Situacional - STAR)
    - Bloom (Niveis cognitivos)
    - Dreyfus (Nivel de expertise)
    - Big Five (Tracos de personalidade)
  
  Entrada: Job description, competencias, senioridade
  Saida: Perguntas categorizadas, criterios, ancoras

Criterios de Aceitacao:
  - [x] Perguntas geradas por competencia
  - [x] Categorizacao por framework
  - [x] Criterios de avaliacao inclusos
```

---

### CARD VAG-118: [BACK-IA] Personalized Feedback Service

```yaml
ID: VAG-118
Titulo: [BACK-IA] Feedback Personalizado para Candidatos
Tipo: Backend IA
Sprint: 4
Story Points: 8
Prioridade: Media
Status: Implementado
Implementado: Janeiro 2026
Transversal: Sim (tambem em Funil de Talentos como FUN-IA-004)

Descricao: |
  Servico para geracao de feedback construtivo e personalizado
  para candidatos, incluindo sugestoes de desenvolvimento.

Historia de Usuario: |
  Como recrutador, eu quero enviar feedback personalizado
  para candidatos nao aprovados, de forma automatica.

Uso em Gestao de Vagas:
  - Rejeicao de candidatos em etapas do pipeline
  - Feedback automatico apos triagem WSI
  - Mensagens de encerramento personalizadas

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/personalized_feedback_service.py
  Classe: PersonalizedFeedbackService
  
  Dados Utilizados:
    - Perfil do candidato
    - Requisitos da vaga
    - Score WSI e areas de melhoria

Criterios de Aceitacao:
  - [x] Feedback gerado automaticamente
  - [x] Personalizacao baseada no perfil
  - [x] Tom construtivo mantido
```

---

### CARD VAG-119: [BACK-IA] Culture Analyzer Service

```yaml
ID: VAG-119
Titulo: [BACK-IA] Analisador de Cultura Empresarial
Tipo: Backend IA
Sprint: 4
Story Points: 8
Prioridade: Media
Status: Implementado
Implementado: Janeiro 2026
Transversal: Sim (tambem em Funil de Talentos como FUN-IA-005)

Descricao: |
  Servico para extracao e analise do perfil cultural de
  empresas a partir de fontes publicas.

Historia de Usuario: |
  Como sistema LIA, eu preciso entender a cultura da empresa
  para avaliar fit cultural dos candidatos.

Uso em Gestao de Vagas:
  - Wizard de criacao: sugestao de competencias culturais
  - Matching de candidatos por cultura
  - Geracao de perguntas de fit cultural

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/culture_analyzer_service.py
  Classe: CultureAnalyzerService
  
  Fontes: Website, LinkedIn, job descriptions
  Saida: Perfil Big Five da empresa, keywords culturais

Criterios de Aceitacao:
  - [x] Extracao de website funciona
  - [x] Big Five mapeado
  - [x] Perfil cultural gerado
```

---

### CARD VAG-120: [BACK-IA] Interview Transcript Analysis

```yaml
ID: VAG-120
Titulo: [BACK-IA] Analise Automatica de Transcricoes de Entrevista
Tipo: Backend IA
Sprint: 5
Story Points: 13
Prioridade: Alta
Status: Implementado
Implementado: Janeiro 2026
Transversal: Sim (tambem em Funil de Talentos como FUN-IA-006)

Descricao: |
  Servico para analise automatica de transcricoes de entrevistas
  com scoring WSI deterministico.

Historia de Usuario: |
  Como recrutador, eu quero que a LIA analise a transcricao
  da entrevista e gere scores e insights automaticamente.

Uso em Gestao de Vagas:
  - Analise pos-entrevista para candidatos da vaga
  - Atualizacao automatica de scores no pipeline
  - Geracao de parecer para decisao

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/interview_transcript_analysis_service.py
  Classe: InterviewTranscriptAnalysisService
  
  Analises: WSI, Bloom, Dreyfus, CBI STAR, Big Five
  Integracao: Microsoft Teams (transcricao)

Criterios de Aceitacao:
  - [x] Transcricao processada
  - [x] WSI scores calculados
  - [x] Parecer automatico criado
```

---

### CARD VAG-121: [BACK-IA] Semantic Search Service

```yaml
ID: VAG-121
Titulo: [BACK-IA] Busca Semantica de Candidatos
Tipo: Backend IA
Sprint: 2
Story Points: 8
Prioridade: Alta
Status: Implementado
Implementado: Janeiro 2026
Transversal: Sim (tambem em Funil de Talentos como FUN-IA-007)

Descricao: |
  Servico de busca semantica usando embeddings e LLM
  para encontrar candidatos por linguagem natural.

Historia de Usuario: |
  Como recrutador, eu quero buscar candidatos usando
  linguagem natural e receber resultados relevantes.

Uso em Gestao de Vagas:
  - VAG-092: Integracao com Pearch (busca de candidatos)
  - Sugestao de candidatos ao criar vaga
  - Matching automatico vaga x candidatos

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/semantic_search_service.py
  Classe: SemanticSearchService
  
  Tecnologias: Gemini 1.5 Flash (embeddings), Redis (cache)

Criterios de Aceitacao:
  - [x] Busca semantica funciona
  - [x] Cache Redis ativo
  - [x] Ranking por relevancia
```

---

### CARD VAG-122: [BACK-IA] Candidate Enrichment Service

```yaml
ID: VAG-122
Titulo: [BACK-IA] Enriquecimento de Perfil de Candidato
Tipo: Backend IA
Sprint: 4
Story Points: 8
Prioridade: Media
Status: Implementado
Implementado: Janeiro 2026
Transversal: Sim (tambem em Funil de Talentos como FUN-IA-008)

Descricao: |
  Servico para enriquecimento automatico de perfis de
  candidatos com dados externos e inferencias.

Historia de Usuario: |
  Como recrutador, eu quero ter o perfil do candidato
  enriquecido com informacoes adicionais automaticamente.

Uso em Gestao de Vagas:
  - Enriquecimento de candidatos aplicados
  - Inferencia de senioridade para matching
  - Estimativa de pretensao salarial

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/candidate_enrichment_service.py
  Classe: CandidateEnrichmentService
  
  Enriquecimentos: LinkedIn, GitHub, skills inferidas, senioridade

Criterios de Aceitacao:
  - [x] Enriquecimento funciona
  - [x] Skills inferidas
  - [x] Senioridade estimada
```

---

## GESTAO DE MUDANCAS E CARDS DE AJUSTE

### Convenção de Nomenclatura

```
CARDS ORIGINAIS:
  VAG-001, VAG-002, ..., VAG-122

CARDS DE AJUSTE (sufixo -A + numero sequencial):
  VAG-001-A1  → Primeiro ajuste do VAG-001
  VAG-001-A2  → Segundo ajuste do VAG-001
  VAG-077-A1  → Ajuste no wizard step 1

TIPOS DE AJUSTE:
  -A  → Ajuste/Alteração (mudança de requisito)
  -B  → Bugfix (correção de bug encontrado)
  -E  → Extensão (nova funcionalidade adicional)
```

### Fluxo de Decisão

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MUDANÇA IDENTIFICADA NA PLATAFORMA                     │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  Time já iniciou o card?       │
                    └───────────────┬───────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │ NÃO                 │                     │ SIM
              ▼                     │                     ▼
    ┌─────────────────────┐         │         ┌─────────────────────┐
    │ Atualizar card      │         │         │ Time já finalizou?  │
    │ original diretamente│         │         └──────────┬──────────┘
    │ (incrementar versao)│         │                    │
    └─────────────────────┘         │         ┌──────────┼──────────┐
                                    │         │ NÃO      │          │ SIM
                                    │         ▼          │          ▼
                                    │ ┌───────────────┐  │  ┌───────────────┐
                                    │ │ Criar card    │  │  │ Criar card    │
                                    │ │ VAG-XXX-A1    │  │  │ VAG-XXX-A1    │
                                    │ │ (Ajuste)      │  │  │ (Hotfix)      │
                                    │ └───────────────┘  │  └───────────────┘
                                    │                    │
                                    └────────────────────┘
```

### Template para Card de Ajuste

```yaml
ID: VAG-XXX-A1
Titulo: [AJUSTE] <Titulo do card original> - <Descricao curta da mudanca>
Tipo: Ajuste | Bugfix | Extensao
Sprint: <Sprint atual>
Story Points: <1-5 normalmente>
Prioridade: Alta | Media | Baixa
Card Original: VAG-XXX
Versao Card Original: 1.0
Data Criacao: DD/MM/AAAA
Status Jira: <Backlog | To Do | In Progress | Done>

Motivo da Mudanca: |
  <Explicar por que a mudanca foi necessaria>
  Ex: "Ao testar na plataforma, identificamos que..."

Mudancas Especificas:
  Antes: |
    <Como era antes>
  
  Depois: |
    <Como deve ser agora>

Arquivos Afetados:
  - <caminho/arquivo1.py>
  - <caminho/arquivo2.tsx>

Impacto no Desenvolvimento:
  Se ja implementou: |
    <Instrucoes para aplicar o ajuste>
  Se nao implementou: |
    Usar especificacao atualizada do card original

Testes Necessarios:
  - [ ] <Teste 1>
  - [ ] <Teste 2>

Links:
  - Card Original: VAG-XXX
  - Screenshot: <link se houver>
```

### Integracao com Jira

> **API de Sincronizacao disponivel em:** `/api/jira`

**Consultar status de um card:**
```
GET /api/jira?action=issue&key=VAG-077
```

**Consultar multiplos cards:**
```
GET /api/jira?action=issues&keys=VAG-077,VAG-078,VAG-079
```

**Sincronizar com documentacao (detectar divergencias):**
```
POST /api/jira
{
  "action": "sync",
  "issueKeys": ["VAG-077", "VAG-078"],
  "docStatuses": {
    "VAG-077": "Implementado",
    "VAG-078": "Pendente"
  }
}
```

**Resposta de sincronizacao:**
```json
{
  "success": true,
  "data": [
    {
      "issueKey": "VAG-077",
      "jiraStatus": "Done",
      "docStatus": "Implementado",
      "synced": true
    },
    {
      "issueKey": "VAG-078",
      "jiraStatus": "In Progress",
      "docStatus": "Pendente",
      "synced": false,
      "divergence": "Jira: Em desenvolvimento | Doc: Ainda como pendente"
    }
  ],
  "summary": {
    "total": 2,
    "synced": 1,
    "divergent": 1,
    "notFound": 0
  }
}
```

### Registro de Cards de Ajuste

> **Instrução:** Adicionar novos cards de ajuste abaixo conforme forem criados

| ID | Card Original | Tipo | Data | Descrição Resumida | Status |
|----|---------------|------|------|-------------------|--------|
| *Nenhum ajuste registrado ainda* | - | - | - | - | - |

---

# EPIC-VAG-012: SATURACAO, GOVERNANCA E CALIBRACAO

> **Responsavel:** Backend IA + Frontend Developer  
> **Sprint:** 5-6  
> **Pontos Total:** 61  
> **Foco:** Funcionalidades de controle de pipeline, autonomia da IA e aprendizado continuo

---

### Resumo do Epic

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    EPIC-VAG-012: SATURACAO, GOVERNANCA E CALIBRACAO                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   SATURACAO INTELIGENTE                    GOVERNANCA HUMANA                             │
│   ──────────────────────                   ──────────────────                            │
│   4 cards | Sprint 5                        2 cards | Sprint 6                           │
│                                                                                          │
│   ├── VAG-123: Badge Pipeline Saturado     ├── VAG-127: Wizard Step 7.5 GovernanceRules │
│   ├── VAG-124: Botao Desbloquear Pipeline  └── VAG-128: GovernanceRulesForm             │
│   ├── VAG-125: [BACK-IA] API saturation                                                 │
│   └── VAG-126: [BACK-IA] API unlock                                                     │
│                                                                                          │
│   CALIBRACAO CONTINUA                                                                   │
│   ────────────────────                                                                  │
│   4 cards | Sprint 5-6                                                                  │
│                                                                                          │
│   ├── VAG-129: LIAFeedbackWidget (thumbs)                                               │
│   ├── VAG-130: CalibrationInsights                                                      │
│   ├── VAG-131: [BACK-IA] API feedback                                                   │
│   └── VAG-132: [BACK-IA] API divergences                                                │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### CARD VAG-123: Badge Pipeline Saturado

```yaml
ID: VAG-123
Titulo: [FRONT] Badge Pipeline Saturado - Indicador Visual
Tipo: Feature
Sprint: 5
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-012
Status: Pendente

Descricao: |
  Implementar badge visual no header do pipeline de candidatos
  que indica quando o pipeline atingiu o limite de candidatos
  aprovados (saturacao).

Historia de Usuario: |
  Como recrutador, eu quero ver claramente quando meu pipeline
  esta saturado para saber que preciso avancar com entrevistas.

Requisitos Tecnicos:
  Frontend:
    - Componente: SaturationBadge
    - Local: CandidatesPage header
    - API: GET /api/v1/job-vacancies/{job_id}/saturation-status
  Estados:
    - Saturado: Badge vermelho "Pipeline Saturado (20/20)"
    - Proximo: Badge amarelo "Quase saturado (18/20)"
    - Normal: Sem badge ou badge verde discreto
  Design Tokens:
    - Saturado: --wedo-danger (#EF4444)
    - Proximo: --wedo-warning (#F59E0B)
    - Normal: --wedo-success (#10B981)

Design & Componentes:
  Componentes Existentes:
    - Badge component do shadcn/ui
  Animacao:
    - Pulse animation quando saturado

Criterios de Aceitacao:
  - [ ] Badge aparece quando approved_count >= threshold * 0.9
  - [ ] Cores corretas por estado
  - [ ] Tooltip com detalhes
  - [ ] Atualizacao em tempo real
```

---

### CARD VAG-124: Botao Desbloquear Pipeline

```yaml
ID: VAG-124
Titulo: [FRONT] Botao Desbloquear Pipeline - Override Manual
Tipo: Feature
Sprint: 5
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-012
Status: Pendente

Descricao: |
  Botao que permite ao recrutador desbloquear manualmente
  o pipeline saturado, aumentando o threshold ou retomando
  a triagem automatica.

Historia de Usuario: |
  Como recrutador, eu quero poder desbloquear o pipeline
  quando decidir continuar recebendo mais candidatos.

Requisitos Tecnicos:
  Frontend:
    - Componente: UnlockPipelineButton
    - Local: SaturationBadge dropdown ou modal
    - API: POST /api/v1/job-vacancies/{job_id}/unlock-pipeline
  Fluxo:
    1. Clique no botao
    2. Modal de confirmacao com opcoes
    3. Opcao 1: Aumentar threshold (+10)
    4. Opcao 2: Desativar saturacao temporariamente
    5. Confirmacao e registro de audit

Design & Componentes:
  Componentes Existentes:
    - Button component
    - AlertDialog para confirmacao
  
Criterios de Aceitacao:
  - [ ] Botao visivel quando pipeline saturado
  - [ ] Modal de confirmacao funcional
  - [ ] API chamada corretamente
  - [ ] Registro de audit trail
  - [ ] Notificacao de sucesso
```

---

### CARD VAG-125: [BACK-IA] API Status de Saturacao

```yaml
ID: VAG-125
Titulo: [BACK-IA] API GET /saturation-status
Tipo: Backend IA
Sprint: 5
Story Points: 5
Prioridade: Critica
Epic: EPIC-VAG-012
Status: Pendente

Descricao: |
  Endpoint que retorna status atual de saturacao do pipeline
  de uma vaga especifica.

Historia de Usuario: |
  Como sistema, preciso consultar o status de saturacao
  para exibir no frontend e controlar triagem automatica.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/calibration_service.py
  Classe: CalibrationService (metodo get_saturation_status)
  Endpoint: GET /api/v1/job-vacancies/{job_id}/saturation-status
  
  Response:
    approved_count: int
    saturation_threshold: int
    is_saturated: bool
    slots_remaining: int
    recommendation: "continue_screening" | "pause_screening"
    last_updated: datetime
  
  Logica:
    - Consulta VacancyCandidate com status = approved
    - Compara com saturation_threshold da GovernanceRules
    - Retorna recomendacao baseada no resultado

Criterios de Aceitacao:
  - [ ] Endpoint funcional
  - [ ] Contagem correta de aprovados
  - [ ] Threshold correto por vaga
  - [ ] Recomendacao calculada
  - [ ] Cache de 30 segundos
```

---

### CARD VAG-126: [BACK-IA] API Desbloquear Pipeline

```yaml
ID: VAG-126
Titulo: [BACK-IA] API POST /unlock-pipeline
Tipo: Backend IA
Sprint: 5
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-012
Status: Pendente

Descricao: |
  Endpoint que desbloqueia pipeline saturado,
  aumentando threshold ou desativando temporariamente.

Historia de Usuario: |
  Como recrutador, preciso de um endpoint para
  desbloquear meu pipeline quando necessario.

Requisitos Tecnicos:
  Arquivo: lia-agent-system/app/services/calibration_service.py
  Classe: CalibrationService (metodo unlock_pipeline)
  Endpoint: POST /api/v1/job-vacancies/{job_id}/unlock-pipeline
  
  Request:
    action: "increase_threshold" | "disable_temporarily"
    new_threshold?: int (se increase)
    disable_until?: datetime (se disable)
  
  Response:
    success: bool
    message: string
    new_threshold: int
    saturation_disabled_until: datetime | null
  
  Logica:
    - Atualiza GovernanceRules da vaga
    - Registra audit log
    - Notifica sistema de triagem

Criterios de Aceitacao:
  - [ ] Endpoint funcional
  - [ ] Validacao de permissoes
  - [ ] Audit log registrado
  - [ ] GovernanceRules atualizada
  - [ ] Triagem retomada automaticamente
```

---

### CARD VAG-127: Wizard Step 7.5 - Regras de Autonomia

```yaml
ID: VAG-127
Titulo: [FRONT] Wizard Step 7.5 - Configuracao GovernanceRules
Tipo: Feature
Sprint: 6
Story Points: 8
Prioridade: Alta
Epic: EPIC-VAG-012
Status: Pendente
Dependencias: VAG-085 (Wizard Step 9 Pipeline)

Descricao: |
  Nova etapa no wizard de criacao de vaga para configurar
  as regras de autonomia da LIA (GovernanceRules).

Historia de Usuario: |
  Como recrutador, eu quero definir os limites de autonomia
  da LIA durante a criacao da vaga.

Requisitos Tecnicos:
  Frontend:
    - Componente: GovernanceRulesStep
    - Local: Entre Step 7 (Pipeline) e Step 8 (Revisao)
    - Campos:
      - auto_schedule_interviews: toggle
      - auto_send_negative_feedback: toggle
      - requires_validation_before_shortlist: toggle
      - max_auto_sourcing_per_day: number input
      - allow_ai_first_contact: toggle
      - saturation_threshold: number input (default 20)

Design & Componentes:
  Layout:
    - Cards com toggle para cada regra
    - Descricao explicativa por regra
    - Indicador de risco por configuracao
  Defaults Sugeridos:
    - Conservador: Tudo desabilitado
    - Moderado: Lembretes habilitados
    - Agressivo: Contato automatico

Criterios de Aceitacao:
  - [ ] Etapa 7.5 aparece no stepper
  - [ ] Todos os campos funcionais
  - [ ] Valores salvos no estado do wizard
  - [ ] Defaults aplicados corretamente
  - [ ] Tooltips explicativos
```

---

### CARD VAG-128: Formulario GovernanceRules

```yaml
ID: VAG-128
Titulo: [FRONT] GovernanceRulesForm - Componente Reutilizavel
Tipo: Feature
Sprint: 6
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-012
Status: Pendente

Descricao: |
  Componente de formulario reutilizavel para configurar
  GovernanceRules, usado no wizard e na edicao de vaga.

Historia de Usuario: |
  Como desenvolvedor, preciso de um componente reutilizavel
  para configurar regras de governanca em diferentes contextos.

Requisitos Tecnicos:
  Frontend:
    - Componente: GovernanceRulesForm
    - Props: initialValues, onSubmit, readOnly
    - API: PUT /api/v1/job-vacancies/{job_id}/governance-rules
  
  Campos:
    - auto_schedule_interviews: Switch
    - auto_send_negative_feedback: Switch
    - requires_validation_before_shortlist: Switch
    - max_auto_sourcing_per_day: NumberInput (0-100)
    - allow_ai_first_contact: Switch
    - saturation_threshold: NumberInput (5-100)

Design & Componentes:
  Componentes Existentes:
    - Switch do shadcn/ui
    - NumberInput customizado
    - Card para agrupamento

Criterios de Aceitacao:
  - [ ] Componente reutilizavel
  - [ ] Validacao de campos
  - [ ] Estados de loading
  - [ ] Mensagens de erro
  - [ ] Integracao com API
```

---

### CARD VAG-129: LIAFeedbackWidget

```yaml
ID: VAG-129
Titulo: [FRONT] LIAFeedbackWidget - Thumbs Up/Down
Tipo: Feature AI
Sprint: 5
Story Points: 5
Prioridade: Alta
Epic: EPIC-VAG-012
Status: Pendente

Descricao: |
  Widget de feedback para cada recomendacao da LIA,
  permitindo thumbs up/down para calibracao.

Historia de Usuario: |
  Como recrutador, eu quero dar feedback sobre as
  recomendacoes da LIA para melhorar sua precisao.

Requisitos Tecnicos:
  Frontend:
    - Componente: LIAFeedbackWidget
    - Local: LiaOpinionCard, SmartTransitionModal, etc
    - API: POST /api/v1/calibration/feedback
  Estados:
    - Neutral: Ambos cinza
    - Agree: Thumbs up verde
    - Disagree: Thumbs down vermelho + modal razao

Design & Componentes:
  Layout:
    - Dois botoes pequenos (thumbs up/down)
    - Animacao ao clicar
    - Toast de confirmacao
  Modal de Razao (disagree):
    - Textarea para justificativa
    - Opcoes pre-definidas

Criterios de Aceitacao:
  - [ ] Widget aparece em recomendacoes LIA
  - [ ] Feedback registrado na API
  - [ ] Modal de razao funcional
  - [ ] Toast de confirmacao
  - [ ] Estado persistido
```

---

### CARD VAG-130: CalibrationInsights

```yaml
ID: VAG-130
Titulo: [FRONT] CalibrationInsights - Painel de Divergencias
Tipo: Feature AI
Sprint: 6
Story Points: 8
Prioridade: Media
Epic: EPIC-VAG-012
Status: Pendente

Descricao: |
  Painel que mostra divergencias entre LIA e recrutador
  nos ultimos 30 dias, com opcao de aprovar ajustes.

Historia de Usuario: |
  Como recrutador senior, eu quero ver onde a LIA diverge
  das minhas decisoes para ajustar os pesos.

Requisitos Tecnicos:
  Frontend:
    - Componente: CalibrationInsights
    - Local: Settings ou Dashboard do recrutador
    - API: GET /api/v1/calibration/divergences
  Dados Exibidos:
    - Lista de divergencias (candidato, score LIA, acao recrutador)
    - Taxa de concordancia (%)
    - Sugestoes de ajuste de pesos
    - Botao "Aplicar sugestoes"

Design & Componentes:
  Layout:
    - Tabela de divergencias
    - Grafico de concordancia
    - Cards de sugestoes
  Acoes:
    - Aprovar sugestao individualmente
    - Aprovar todas sugestoes
    - Ignorar sugestao

Criterios de Aceitacao:
  - [ ] Painel acessivel
  - [ ] Divergencias listadas
  - [ ] Taxa calculada
  - [ ] Sugestoes exibidas
  - [ ] Aprovacao funcional
```

---

### CARD VAG-131: [BACK-IA] API Registrar Feedback

```yaml
ID: VAG-131
Titulo: [BACK-IA] API POST /calibration/feedback
Tipo: Backend IA
Sprint: 5
Story Points: 5
Prioridade: Critica
Epic: EPIC-VAG-012
Status: Implementado
Implementado: 22 Janeiro 2026

Descricao: |
  Endpoint para registrar feedback explicito do recrutador
  sobre recomendacoes da LIA.

Historia de Usuario: |
  Como sistema, preciso armazenar feedback do recrutador
  para calibrar os scores da LIA.

Requisitos Tecnicos:
  Endpoint: POST /api/v1/calibration/feedback
  Arquivo: lia-agent-system/app/services/calibration_service.py
  
  Request:
    candidate_id: uuid
    job_id: uuid
    agrees_with_lia: bool
    lia_score: float
    feedback_reason?: string
    feedback_type: "EXPLICIT_AGREE" | "EXPLICIT_DISAGREE"
  
  Response:
    success: bool
    feedback_id: uuid
    message: string

Criterios de Aceitacao:
  - [x] Endpoint funcional
  - [x] Feedback armazenado
  - [x] Tipos de feedback suportados
  - [x] Validacao de dados
```

---

### CARD VAG-132: [BACK-IA] API Consultar Divergencias

```yaml
ID: VAG-132
Titulo: [BACK-IA] API GET /calibration/divergences
Tipo: Backend IA
Sprint: 6
Story Points: 8
Prioridade: Alta
Epic: EPIC-VAG-012
Status: Implementado
Implementado: 22 Janeiro 2026

Descricao: |
  Endpoint que retorna divergencias entre LIA e recrutador
  nos ultimos 30 dias.

Historia de Usuario: |
  Como sistema, preciso consultar divergencias para
  exibir no painel de calibracao.

Requisitos Tecnicos:
  Endpoint: GET /api/v1/calibration/divergences
  Arquivo: lia-agent-system/app/services/calibration_service.py
  
  Query Params:
    recruiter_id?: uuid
    job_id?: uuid
    days?: int (default 30)
    min_delta?: float (default 5.0)
  
  Response:
    divergences: list[DivergenceRecord]
    total_divergences: int
    agreement_rate: float
    suggestions: list[WeightAdjustment]

Criterios de Aceitacao:
  - [x] Endpoint funcional
  - [x] Filtros funcionais
  - [x] Taxa calculada corretamente
  - [x] Sugestoes geradas
```

---

### Indice Atualizado - EPIC-VAG-012

| Card | Titulo | Pontos | Prioridade | Status |
|------|--------|--------|------------|--------|
| VAG-123 | Badge Pipeline Saturado | 5 | Alta | Pendente |
| VAG-124 | Botao Desbloquear Pipeline | 5 | Alta | Pendente |
| VAG-125 | [BACK-IA] API saturation-status | 5 | Critica | Pendente |
| VAG-126 | [BACK-IA] API unlock-pipeline | 5 | Alta | Pendente |
| VAG-127 | Wizard Step 7.5 GovernanceRules | 8 | Alta | Pendente |
| VAG-128 | GovernanceRulesForm | 5 | Alta | Pendente |
| VAG-129 | LIAFeedbackWidget | 5 | Alta | Pendente |
| VAG-130 | CalibrationInsights | 8 | Media | Pendente |
| VAG-131 | [BACK-IA] API calibration/feedback | 5 | Critica | Implementado |
| VAG-132 | [BACK-IA] API calibration/divergences | 8 | Alta | Implementado |

**Total Epic:** 59 pontos | **Implementados:** 13 pontos | **Pendentes:** 46 pontos

---

## CHANGELOG

| Data | Versao | Alteracao |
|------|--------|-----------|
| 21/01/2026 | 1.0 | Criacao inicial - 27 cards |
| 21/01/2026 | 1.1 | Removidos VAG-025, VAG-026, VAG-027 (onboarding) - 24 cards |
| 21/01/2026 | 1.2 | Adicionado Fluxo de Congelamento de Vaga com papeis dos agentes |
| 21/01/2026 | 1.3 | Movido Fluxo de Congelamento para arquitetura de agentes (lia-agent-system/docs/) |
| 22/01/2026 | 1.4 | **Atualizacao de cards para refletir implementacao real:** VAG-017 (arquitetura de agentes), VAG-021 (resumo via chat), VAG-022 (LiaVacancyQueriesGuide). Secao de agentes atualizada com servicos implementados. |
| 22/01/2026 | 2.0 | **Expansao completa - 90 cards (+66 novos):** Adicionados 6 novos epicos (EPIC-VAG-006 a EPIC-VAG-011): Tabela de Vagas (9 cards), Preview da Vaga (11 cards), Modais de Acao em Lote (9 cards), Filtros e Busca (9 cards), Chat LIA Multi-Nivel (9 cards), Job Creation Wizard (19 cards). Cards com referencia a componentes reais e status de implementacao. |
| 22/01/2026 | 2.1 | **Novas secoes adicionadas:** Divisao por Area Tecnica (Frontend/Backend/IA/Integracoes/Infra), Estimativas de Tempo (504 pts = 876h brutas, 482h com aceleracao = 12 sprints), Fluxo Ideal de Desenvolvimento (Sprint 0-7 com ferramentas e stack tecnica). |
| 22/01/2026 | 2.2 | **Cards IA implementados (VAG-109 a VAG-114):** Comparacao de Candidatos (Cenarios A/B/C), Score LIA Unificado, Parecer Automatico, Metodologia Unificada, WSI Scoped, Testes de Validacao. |
| 22/01/2026 | 2.3 | **Correcoes wizard atualizadas:** VAG-077 (prompt extracao competencias), VAG-078 (mapeamento campos PT/EN), VAG-088 (logging diagnostico). |
| 22/01/2026 | 2.4 | **Servicos IA transversais (VAG-115 a VAG-122):** WSI Service, CV Parser, WSI Question Generator, Personalized Feedback, Culture Analyzer, Interview Transcript Analysis, Semantic Search, Candidate Enrichment. Mapeamento de dependencias com cards de frontend. Total: 119 cards. |
| 22/01/2026 | 2.5 | **Secao de Gestao de Mudancas:** Convencao de nomenclatura (-A, -B, -E), fluxo de decisao, template para cards de ajuste, registro de ajustes futuros. |
| 22/01/2026 | 2.6 | **Integracao com Jira:** API de sincronizacao (/api/jira), campo Status Jira nos cards, servico de consulta de boards e colunas. |
| 22/01/2026 | 2.7 | **EPIC-VAG-012 Saturacao, Governanca e Calibracao:** 10 novos cards (VAG-123 a VAG-132). Saturacao Inteligente (4 cards), Governanca Humana (2 cards), Calibracao Continua (4 cards). Total: 129 cards. |

