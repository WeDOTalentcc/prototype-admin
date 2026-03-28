# Camada de Inteligência Artificial da WedoTalent

## Documento Educacional e Conceitual — Versão 1.0

> **Objetivo:** Explicar de forma didática, macro e estruturada todos os conceitos de IA implementados na plataforma WedoTalent, com diagramas visuais, para que qualquer pessoa de tecnologia compreenda como a IA funciona e **por quê** cada escolha foi feita.
>
> **Data:** 24/02/2026  
> **Baseado em:** `MAPA_CAMADA_INTELIGENCIA.md` (2.647 linhas) + `ai-architecture-audit.md` (7.550 linhas)

---

## Índice

1. [Introdução e Visão Geral](#1-introdução-e-visão-geral)
2. [Fundamentos: Como os Agentes Pensam](#2-fundamentos-como-os-agentes-pensam)
3. [Orquestração: Quem Decide o Quê](#3-orquestração-quem-decide-o-quê)
4. [Busca Inteligente: Encontrando o Candidato Certo](#4-busca-inteligente-encontrando-o-candidato-certo)
5. [Triagem WSI: A Metodologia Proprietária de Avaliação](#5-triagem-wsi-a-metodologia-proprietária-de-avaliação)
6. [Memória e Aprendizado: Uma IA que Lembra e Evolui](#6-memória-e-aprendizado-uma-ia-que-lembra-e-evolui)
7. [Processamento Assíncrono: Trabalhando em Escala](#7-processamento-assíncrono-trabalhando-em-escala)
8. [Compliance e Ética: IA Responsável por Design](#8-compliance-e-ética-ia-responsável-por-design)
9. [Automação e Predição: De Reativa a Proativa](#9-automação-e-predição-de-reativa-a-proativa)
10. [Por Que Escolhemos Esta Arquitetura](#10-por-que-escolhemos-esta-arquitetura)

---

## 1. Introdução e Visão Geral

### 1.1 O que é a LIA?

A **LIA** (Learning Intelligence Assistant) é a camada de inteligência artificial da plataforma WedoTalent. Ela não é um chatbot — é um **sistema de agentes especializados** que auxilia recrutadores em todo o ciclo de contratação: desde a criação de vagas até a contratação final.

**Analogia:** Pense na LIA como uma equipe de especialistas invisíveis. Quando o recrutador pede algo, a LIA decide qual especialista é mais adequado, encaminha a tarefa, e o especialista usa suas ferramentas para entregar o resultado. Tudo isso acontece em segundos, de forma transparente.

### 1.2 Números da Plataforma

```
┌──────────────────────────────────────────────────────────────┐
│                  LIA EM NÚMEROS                              │
│                                                              │
│   11 Domínios de conhecimento                                │
│    7 Agentes ReAct (arquitetura moderna)                     │
│   18 Agentes Legacy (em migração)                            │
│    1 Agente LangGraph (orquestração de workflow)             │
│   89 Ferramentas ReAct (tools autônomas)                     │
│  109 Ferramentas Legacy                                      │
│  140+ Serviços de negócio                                    │
│    3 Provedores LLM (Claude, Gemini, OpenAI)                 │
│    3 Camadas de cache                                        │
│    3 Camadas de proteção contra viés (FairnessGuard)         │
│    4 Frameworks psicométricos integrados (WSI)               │
│    7 Frameworks de compliance monitorados                    │
│   86 Modelos de dados (entidades no banco)                   │
│  768 Dimensões vetoriais (embeddings semânticos)             │
└──────────────────────────────────────────────────────────────┘
```

### 1.3 Arquitetura em Camadas — Visão de 10.000 Pés

A LIA é organizada em camadas que se comunicam de cima para baixo:

```
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 1: INTERFACE                                            │
│  Chat (recrutador) │ WhatsApp (candidato) │ Teams/Email (gestor)│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 2: ORQUESTRAÇÃO                                         │
│  CascadedRouter → StateManager → PolicyEngine → TaskPlanner     │
│  "Quem deve atender?" "Qual o contexto?" "É permitido?" "Como?"│
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐
│  CAMADA 3A:     │ │  CAMADA 3B:   │ │  CAMADA 3C:      │
│  AGENTES REACT  │ │  AGENTE       │ │  AGENTES LEGACY  │
│  (7 agentes,    │ │  LANGGRAPH    │ │  (18 agentes,    │
│   89 tools)     │ │  (Job Wizard) │ │   109 tools)     │
│  Autônomos      │ │  Workflow     │ │  Em migração     │
└────────┬────────┘ └───────┬───────┘ └────────┬─────────┘
         │                  │                   │
         └──────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 4: SERVIÇOS ESPECIALIZADOS                              │
│  WSI Scoring │ Busca Semântica │ Análise Multimodal │ Analytics │
│  CV Parser   │ WRF Ranking     │ Voz (Deepgram)     │ Predição  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 5: INFRAESTRUTURA TRANSVERSAL                           │
│  Compliance    │ Cache        │ Memória       │ Observabilidade │
│  FairnessGuard │ 3 camadas    │ Working+LT    │ Audit Logs      │
│  FactChecker   │ Redis+PG     │ Embeddings    │ Telemetria      │
│  LGPD/EU AI   │ Semântico    │ Cross-session │ Health Checks   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 6: DADOS E INTEGRAÇÕES                                  │
│  PostgreSQL  │ pgvector    │ Redis      │ Elasticsearch         │
│  (ACID)      │ (768 dims)  │ (cache)    │ (full-text + BM25)    │
│  RabbitMQ    │ S3/Storage  │ ATS APIs   │ LLM APIs              │
│  (filas)     │ (arquivos)  │ (Gupy/etc) │ (Claude/Gemini/OpenAI)│
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 Os 11 Domínios de Conhecimento

Cada domínio é uma área de especialização da LIA. Pense neles como "departamentos" de uma empresa:

```
┌────────────────────────────────────────────────────────────────────┐
│                    11 DOMÍNIOS DA LIA                              │
│                                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 1. SOURCING │ │ 2. JOB      │ │ 3. CV       │ │ 4. COMMUNI- │ │
│  │             │ │ MANAGEMENT  │ │ SCREENING   │ │ CATION      │ │
│  │ Busca e     │ │ Criação e   │ │ Triagem     │ │ Email,      │ │
│  │ captação de │ │ gestão de   │ │ WSI, scoring│ │ WhatsApp,   │ │
│  │ candidatos  │ │ vagas       │ │ e avaliação │ │ Teams, SMS  │ │
│  │ 30 actions  │ │ 29 actions  │ │ 25 actions  │ │ 20 actions  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 5. INTER-   │ │ 6. ANALY-   │ │ 7. ATS      │ │ 8. AUTOMA-  │ │
│  │ VIEW &      │ │ TICS        │ │ INTEGRATION │ │ TION        │ │
│  │ SCHEDULING  │ │             │ │             │ │             │ │
│  │ Agendamento,│ │ KPIs,       │ │ Sync com    │ │ Regras,     │ │
│  │ voz, WSI    │ │ previsões,  │ │ Gupy,       │ │ alertas,    │ │
│  │ interview   │ │ dashboards  │ │ Pandapé,etc │ │ agentes     │ │
│  │ 20 actions  │ │ 18 actions  │ │ 18 actions  │ │ 20 actions  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                 │
│  │ 9. RECRUI-  │ │ 10.PIPELINE │ │ 11.HIRING   │                 │
│  │ TER ASSIST. │ │ TRANSITION  │ │ POLICY      │                 │
│  │             │ │             │ │             │                 │
│  │ Assistente  │ │ Movimentação│ │ Políticas   │                 │
│  │ pessoal do  │ │ de candidat.│ │ de contrata-│                 │
│  │ recrutador  │ │ no pipeline │ │ ção via IA  │                 │
│  │ 20 actions  │ │ 5 actions   │ │ ReAct agent │                 │
│  └─────────────┘ └─────────────┘ └─────────────┘                 │
└────────────────────────────────────────────────────────────────────┘
```

**Princípio de design:** Cada domínio é **autossuficiente** — possui seus próprios agentes, ações e ferramentas. O orquestrador apenas decide para qual domínio encaminhar a mensagem. Isso permite que novos domínios sejam adicionados sem alterar os existentes.

---

## 2. Fundamentos: Como os Agentes Pensam

### 2.1 O Padrão ReAct — Thought → Action → Observation

O ReAct (Reasoning + Acting) é o padrão central de raciocínio dos agentes modernos da LIA. Ele resolve um problema fundamental da IA: **como um modelo de linguagem pode executar ações no mundo real de forma controlada?**

**A ideia central:** Em vez de pedir ao LLM uma resposta direta, o ReAct faz o LLM **pensar em voz alta**, decidir qual ferramenta usar, observar o resultado, e repetir até ter informação suficiente para responder.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REACT LOOP — CICLO DE RACIOCÍNIO                 │
│                    (máximo 5 iterações por segurança)                │
│                                                                     │
│                        Mensagem do Recrutador                       │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 1. REASON (Raciocinar)                                     │     │
│  │                                                            │     │
│  │  O LLM recebe:                                            │     │
│  │  • System prompt (personalidade + regras do domínio)       │     │
│  │  • Lista de tools disponíveis (nome + descrição + params)  │     │
│  │  • Contexto da conversa (histórico + estado)               │     │
│  │  • Observações anteriores (resultados de tools)            │     │
│  │  • Memórias de longo prazo (cross-session learnings)       │     │
│  │                                                            │     │
│  │  Produz JSON: { thought, action, tool_name, tool_args }   │     │
│  └──────────────────────────┬─────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 2. PARSE & DECIDE (Analisar e Decidir)                     │     │
│  │                                                            │     │
│  │  action == "respond"            → Gera resposta final ──────── FIM
│  │  action == "ask_clarification"  → Pede mais info ───────────── FIM
│  │  action == "call_tool"          → Continua para ACT ──┐  │     │
│  └───────────────────────────────────────────────────────│──┘     │
│                                                          │         │
│                                                          ▼         │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 3. ACT (Executar)                                          │     │
│  │                                                            │     │
│  │  Verificações de segurança:                                │     │
│  │  ✓ Tool existe no registry?                                │     │
│  │  ✓ Já falhou com esses mesmos argumentos?                  │     │
│  │  ✓ É uma chamada duplicada? (≥2 repetições → break)       │     │
│  │  ✓ Tool está em guardrails? → Pede confirmação ao humano  │     │
│  │                                                            │     │
│  │  Se tudo OK: executa tool_function(**tool_args)            │     │
│  └──────────────────────────┬─────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 4. OBSERVE (Observar)                                      │     │
│  │                                                            │     │
│  │  Interpreta o resultado da ferramenta                      │     │
│  │  Adiciona observação ao estado do loop                     │     │
│  └──────────────────────────┬─────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ 5. SHOULD RESPOND? (Já posso responder?)                   │     │
│  │                                                            │     │
│  │  Heurística: tool sucedeu? dados suficientes?              │     │
│  │  SIM → Gera resposta final ──────────────────────────────── FIM  │
│  │  NÃO → Volta para REASON (próxima iteração) ─────────── LOOP   │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                     │
│  PROTEÇÕES CONTRA LOOPS INFINITOS:                                  │
│  • Máximo 5 iterações → resposta de fallback                       │
│  • Detecção de chamadas duplicadas (≥2 repetições → para)          │
│  • Tracking de falhas (não repete tool com mesmos params)           │
│  • Guardrail tools → requerem confirmação do recrutador             │
│  • Error handling → resposta de fallback segura                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Exemplo concreto:** O recrutador pergunta "Qual o salário de mercado para Dev Python Sênior em SP?"

```
Iteração 1:
  THOUGHT: "Preciso buscar dados salariais reais para Python Sênior em SP"
  ACTION:  call_tool → get_salary_benchmarks(role="Python Developer", 
                         seniority="Senior", location="São Paulo")
  OBSERVE: "Resultado: R$ 12.000 — R$ 22.000 (mediana R$ 16.500)"

  SHOULD RESPOND? SIM — tenho dados suficientes.

  RESPONSE: "O salário de mercado para Dev Python Sênior em São Paulo
             está entre R$ 12.000 e R$ 22.000, com mediana de R$ 16.500
             (fonte: benchmarks internos + Robert Half/Gupy 2024)."
```

**Por que ReAct e não chamada direta?** Porque o agente escolhe sozinho quais ferramentas usar e em qual ordem. Ele pode precisar de 1, 2 ou 5 ferramentas dependendo da complexidade da pergunta. Essa flexibilidade é impossível com código hardcoded.

### 2.2 Os Três Provedores LLM — Por Que Três?

A LIA não depende de um único modelo de linguagem. Ela usa três provedores, cada um escolhido para o que faz melhor:

```
┌──────────────────────────────────────────────────────────────┐
│               ESTRATÉGIA MULTI-LLM                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐      │
│  │ CLAUDE (Anthropic) — "O Pensador"                  │      │
│  │                                                    │      │
│  │ Modelo: claude-sonnet-4-20250514                   │      │
│  │ Temperatura: 0.3 (respostas mais consistentes)     │      │
│  │                                                    │      │
│  │ Usado para:                                        │      │
│  │ • Raciocínio complexo (ReAct loop, análise de CV)  │      │
│  │ • Geração de Job Descriptions                      │      │
│  │ • Classificação de intent (camada 3 do router)     │      │
│  │ • Análise de imagens (Claude Vision)               │      │
│  │ • Avaliação WSI (blocos comportamentais)            │      │
│  │                                                    │      │
│  │ Por quê: Melhor raciocínio estruturado e seguimento│      │
│  │ de instruções complexas. Output JSON mais confiável│      │
│  └────────────────────────────────────────────────────┘      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐      │
│  │ GEMINI (Google) — "O Rápido"                       │      │
│  │                                                    │      │
│  │ Usado para:                                        │      │
│  │ • Expansão semântica de termos de busca             │      │
│  │   "Python" → [FastAPI, Django, Flask, PyTorch...]   │      │
│  │ • Análise de vídeo de entrevista                    │      │
│  │ • Tarefas de baixa latência (<300ms target)         │      │
│  │                                                    │      │
│  │ Por quê: Menor latência para expansão semântica.   │      │
│  │ Bom custo-benefício para tarefas rápidas.          │      │
│  └────────────────────────────────────────────────────┘      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐      │
│  │ OPENAI — "O Versátil"                              │      │
│  │                                                    │      │
│  │ Usado para:                                        │      │
│  │ • Embeddings (text-embedding-004, 768 dimensões)   │      │
│  │ • Text-to-Speech (tts-1, tts-1-hd)                 │      │
│  │ • Speech-to-Text fallback (Whisper)                 │      │
│  │ • Tarefas auxiliares e fallback geral               │      │
│  │                                                    │      │
│  │ Por quê: Melhor ecossistema de embeddings e voz.   │      │
│  │ API madura e estável para produção.                │      │
│  └────────────────────────────────────────────────────┘      │
│                                                              │
│  PRINCÍPIO: "Best tool for the job"                          │
│  O LLMFactory seleciona o provedor ideal por tarefa.         │
│  Se um provedor falha, há fallback automático.               │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Tools — As Mãos dos Agentes

Os LLMs pensam, mas não podem agir sozinhos. As **tools** (ferramentas) são funções que o agente pode chamar para buscar dados, executar ações ou interagir com sistemas externos.

```
┌──────────────────────────────────────────────────────────────────┐
│               TOOL DEFINITION — ANATOMIA DE UMA FERRAMENTA       │
│                                                                  │
│  Cada tool é definida por:                                       │
│                                                                  │
│  ToolDefinition {                                                │
│    name: "get_salary_benchmarks"                                 │
│    description: "Busca benchmarks salariais reais por cargo..."  │
│    parameters: JSON Schema (quais argumentos aceita)             │
│    function: referência para a função Python que executa         │
│  }                                                               │
│                                                                  │
│  O agente NÃO sabe o código da ferramenta.                       │
│  Ele só vê nome + descrição + parâmetros.                        │
│  É a DESCRIÇÃO que permite ao agente escolher a ferramenta certa.│
└──────────────────────────────────────────────────────────────────┘
```

**89 ferramentas ReAct** distribuídas em **7 registries** especializados:

```
┌──────────────────────────────────────────────────────────────────┐
│          7 REGISTRIES DE FERRAMENTAS REACT                       │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Wizard Registry  │  │ Kanban Registry  │                     │
│  │ (9 tools)        │  │ (14 tools)       │                     │
│  │                  │  │                  │                     │
│  │ validate_job_req │  │ get_benchmarks   │                     │
│  │ get_salary_bench │  │ pipeline_summary │                     │
│  │ validate_fields  │  │ identify_bottle. │                     │
│  │ get_suggestions  │  │ suggest_movements│                     │
│  │ save_job_draft   │  │ batch_move       │                     │
│  │ generate_jd      │  │ check_fairness   │                     │
│  │ ...              │  │ ...              │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Talent Registry  │  │ Jobs Mgmt Reg.   │                     │
│  │ (12 tools)       │  │ (13 tools)       │                     │
│  │                  │  │                  │                     │
│  │ search_candidates│  │ list_jobs        │                     │
│  │ compare_candidat.│  │ check_sla        │                     │
│  │ rank_candidates  │  │ analyze_bottlen. │                     │
│  │ check_fairness   │  │ pause/reopen/    │                     │
│  │ pool_health      │  │ close_job        │                     │
│  │ ...              │  │ ...              │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Policy Registry  │  │ Sourcing Reg.    │  │ Screening Reg. │ │
│  │ (13 tools)       │  │ (14 tools)       │  │ (14 tools)     │ │
│  │                  │  │                  │  │                │ │
│  │ get/save_policy  │  │ set_criteria     │  │ parse_cv       │ │
│  │ validate_complia.│  │ execute_search   │  │ calculate_wsi  │ │
│  │ industry_bench.  │  │ validate_fair.   │  │ generate_ques. │ │
│  │ explain_impact   │  │ analyze_results  │  │ evaluate_resp. │ │
│  │ ...              │  │ ...              │  │ ...            │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                  │
│  DIFERENÇA FUNDAMENTAL:                                          │
│  Legacy tools: código decide qual tool chamar (hardcoded)        │
│  ReAct tools:  IA decide qual tool chamar (por descrição)        │
│  → Desacoplamento total, flexibilidade máxima                    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.4 Enhanced Base Agent — A Camada de Robustez

Todos os agentes herdam de uma base comum que fornece proteções automáticas. Pense nela como um "sistema imunológico" dos agentes:

```
┌──────────────────────────────────────────────────────────────────┐
│          ENHANCED BASE AGENT — 6 PROTEÇÕES AUTOMÁTICAS           │
│                                                                  │
│  BaseAgent → EnhancedBaseAgent → [Agente Específico]             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 1. ROTEAMENTO INTELIGENTE (can_handle)                     │  │
│  │    Cada agente define IntentSchemas que descrevem           │  │
│  │    quais intenções ele sabe atender, com entidades          │  │
│  │    obrigatórias e opcionais. O router consulta todos        │  │
│  │    os agentes e escolhe o com maior confiança.              │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 2. ERROR HANDLING AUTOMÁTICO                               │  │
│  │    @handle_agent_errors transforma erros técnicos em       │  │
│  │    mensagens amigáveis para o recrutador.                  │  │
│  │    Exemplo: "ConnectionError" → "Não consegui acessar      │  │
│  │    o serviço agora. Tente novamente em instantes."          │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 3. VALIDAÇÃO E SANITIZAÇÃO DE INPUT                        │  │
│  │    sanitize_text() remove tentativas de XSS, SQL injection │  │
│  │    detect_language() identifica idioma (pt-BR padrão)      │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 4. DETECÇÃO DE CANCELAMENTO                                │  │
│  │    Se o contexto de processamento é cancelado (ex:         │  │
│  │    recrutador fecha a página), o agente para de forma      │  │
│  │    segura em vez de continuar gastando recursos.            │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 5. PROMPTS DEFENSIVOS                                      │  │
│  │    Mensagens pré-formatadas para intents ambíguos           │  │
│  │    ("Não entendi exatamente. Você quer X ou Y?")            │  │
│  │    e requests fora do escopo do domínio.                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 6. TELEMETRIA AUTOMÁTICA                                   │  │
│  │    Métricas coletadas por request:                          │  │
│  │    • total_requests, successful, failed                     │  │
│  │    • avg_response_time_ms                                   │  │
│  │    • cancellations                                          │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.5 ReAct vs Legacy — Duas Gerações de Agentes

A plataforma está em migração da arquitetura legacy para ReAct. Ambas coexistem, controladas por feature flag:

```
┌──────────────────────────────────────────────────────────────────┐
│          LEGACY vs REACT — COMPARAÇÃO                            │
│                                                                  │
│  ┌─────────────────────┐      ┌─────────────────────┐           │
│  │  LEGACY (18 agents) │      │  REACT (7 agents)   │           │
│  │                     │      │                     │           │
│  │  DomainPrompt       │      │  ReActLoop          │           │
│  │  ↓                  │      │  ↓                  │           │
│  │  process_intent()   │      │  Thought→Action→Obs │           │
│  │  ↓                  │      │  ↓                  │           │
│  │  Action mapeada     │      │  Tool escolhida     │           │
│  │  (código decide)    │      │  (IA decide)        │           │
│  │  ↓                  │      │  ↓                  │           │
│  │  Tool executada     │      │  Tool executada     │           │
│  │                     │      │                     │           │
│  │  PRÓ: Previsível    │      │  PRÓ: Flexível      │           │
│  │  CON: Rígido        │      │  PRÓ: Autônomo      │           │
│  │  CON: Escalabilidade│      │  PRÓ: Explainability│           │
│  └─────────────────────┘      └─────────────────────┘           │
│                                                                  │
│  Feature Flag: USE_REACT_AGENTS                                  │
│  ├── true (default) → Orchestrator usa ReactAgentRegistry        │
│  └── false → Orchestrator usa DomainPrompt.process_intent()      │
│                                                                  │
│  Fallback automático:                                            │
│  Se ReAct falha com exceção → tenta agente legacy                │
│  Se domínio não tem ReAct → usa legacy automaticamente           │
└──────────────────────────────────────────────────────────────────┘
```

#### 2.5.1 Análise da Migração Legacy → ReAct — Status, Impacto e Direção

> **Contexto**: A plataforma WedoTalent nasceu com a arquitetura legacy (18 agentes) e está sendo
> progressivamente migrada para ReAct (7 agentes já migrados). A migração foi **iniciada mas ainda
> não concluída**. As duas gerações coexistem porque é mais seguro migrar domínio por domínio do que
> reescrever tudo de uma vez. Esta seção documenta o estado atual da migração, o impacto em consumo
> de tokens, a projeção de consolidação ao concluir a migração, e uma análise de alinhamento entre
> o WeDO REAL (Recruiter Agent V5) construído pelo time de desenvolvimento e a direção arquitetural
> da WedoTalent.

##### O que ainda é Legacy — Mapa Completo

Os 18 agentes legacy que ainda existem na plataforma, distribuídos em 7 áreas:

| # | Agente Legacy | Área (Domínio) | O que faz |
|---|---|---|---|
| 1 | JobDraftingAgent | Gestão de Vagas | Rascunho de descrição de vaga |
| 2 | JobIntakeAgent | Gestão de Vagas | Intake de requisitos de vaga |
| 3 | JobLifecycleAgent | Gestão de Vagas | Ciclo de vida da vaga |
| 4 | JobInsightsAgent | Gestão de Vagas | Insights sobre vagas |
| 5 | JobBenefitsCompAgent | Gestão de Vagas | Benefícios e compensação |
| 6 | JobRubricAgent | Gestão de Vagas | Rubricas de avaliação |
| 7 | RecruiterAssistantAgent | Assistente do Recrutador | Assistente geral (fallback) |
| 8 | ScreeningAgent | Triagem de CVs | Screening de candidatos |
| 9 | AvaliadorWSIAgent | Triagem de CVs | Avaliação WSI |
| 10 | TriagemCurricularAgent | Triagem de CVs | Triagem curricular |
| 11 | SourcingAgent | Sourcing | Sourcing (fallback) |
| 12 | CommunicationAgent | Comunicação | Comunicação multi-canal |
| 13 | SchedulingAgent | Entrevistas | Agendamento de entrevistas |
| 14 | EntrevistadorAgent | Entrevistas | Condução de entrevistas |
| 15 | AnalyticsAgent | Analytics | Relatórios e analytics |
| 16 | AnalistaFeedbackAgent | Analytics | Análise de feedback |
| 17 | IntegradorATSAgent | Integração ATS | Integração com ATS externos |
| 18 | TaskPlannerAgent | Automação | Planejamento de tarefas |

##### Status da Migração por Domínio

```
┌──────────────────────────────────────────────────────────────┐
│         MIGRAÇÃO POR DOMÍNIO — STATUS ATUAL                  │
│                                                              │
│  DOMÍNIO              │ ReAct        │ Legacy     │ Status   │
│  ─────────────────────┼──────────────┼────────────┼──────────│
│  Gestão de Vagas      │ WizardReAct  │ 6 agentes  │ PARCIAL  │
│                       │ (9 tools)    │            │          │
│  Assistente Recrutador│ KanbanReAct  │ 1 agente   │ PARCIAL  │
│                       │ TalentReAct  │ (fallback) │          │
│                       │ JobsMgmtReAct│            │          │
│  Triagem de CVs       │ PipelineReAct│ 3 agentes  │ PARCIAL  │
│                       │ (14 tools)   │            │          │
│  Sourcing             │ SourcingReAct│ 1 agente   │ PARCIAL  │
│                       │ (14 tools)   │ (fallback) │          │
│  Políticas Contratação│ PolicyReAct  │ NENHUM     │ ✅ 100%  │
│                       │ (13 tools)   │            │          │
│  Comunicação          │ —            │ 1 agente   │ ❌ 0%    │
│  Entrevistas          │ —            │ 2 agentes  │ ❌ 0%    │
│  Analytics            │ —            │ 2 agentes  │ ❌ 0%    │
│  Integração ATS       │ —            │ 1 agente   │ ❌ 0%    │
│  Automação            │ —            │ 1 agente   │ ❌ 0%    │
└──────────────────────────────────────────────────────────────┘
```

**Resumo**: Apenas 1 domínio (Políticas de Contratação) está 100% migrado. 4 domínios têm ReAct
mas mantêm legacy como fallback. 5 domínios ainda são 100% legacy.

##### Diferença de Consumo de Tokens — Legacy vs ReAct

O ReAct tende a consumir mais tokens por interação individual, mas resolve problemas mais
complexos em menos interações. O impacto real no custo depende do cenário:

```
LEGACY (1 chamada LLM por interação):
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Input   │ ──→ │  1x LLM  │ ──→ │ Resposta │
│  do user │     │  call    │     │  final   │
└──────────┘     └──────────┘     └──────────┘
Tokens: ~1.000-3.000 por interação (1 chamada)

ReAct (até 5 chamadas LLM por interação):
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Input   │ ──→ │ Thought  │ ──→ │  Action  │ ──→ │ Observe  │ ──╮
│  do user │     │ (LLM #1) │     │ (Tool)   │     │ (result) │   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘   │
                                                                   │
     ╭─────────────────────────────────────────────────────────────╯
     │  Loop repete até 5x (max_iterations = 5)
     ▼
┌──────────┐
│ Resposta │
│  final   │
└──────────┘
Tokens: ~3.000-15.000 por interação (1-5 chamadas)
```

| Aspecto | Legacy | ReAct |
|---------|--------|-------|
| Chamadas LLM por interação | 1 (fixa) | 1 a 5 (dinâmica) |
| Tokens por chamada | ~1.000-3.000 | ~1.000-3.000 cada |
| Total por interação | ~1.000-3.000 | ~3.000-15.000 |
| Custo estimado | ~$0.01 | ~$0.01-0.05 |
| **Mas...** | Pode precisar de 3-4 interações para resolver | Frequentemente resolve em 1 interação |

**O ponto-chave: custo por RESULTADO, não por chamada.**

- **Legacy**: O usuário pergunta algo complexo → agente dá resposta parcial → usuário precisa
  reformular → outra resposta parcial → 3-4 trocas para resolver. Total: 4 x $0.01 = **$0.04**
- **ReAct**: O usuário pergunta algo complexo → agente raciocina, usa 3 tools, dá resposta
  completa. Total: 1 x $0.04 = **$0.04**

O custo total tende a ser similar, mas a experiência do usuário é muito melhor com ReAct porque
resolve em uma interação só. A plataforma rastreia tudo isso na tabela `AiConsumption` — cada
chamada LLM registra `input_tokens`, `output_tokens`, `cost_cents`, `agent_type` e `model`, com
limite mensal de 100.000 tokens por empresa (configurável).

##### Projeção de Consolidação — De 26 Agentes (Hoje) para ~12 ReAct (Futuro)

A recomendação é migrar tudo para ReAct. Hoje a plataforma tem **26 agentes no total** (7 ReAct +
1 LangGraph + 18 Legacy). Após a migração completa, a projeção é de **~12 agentes ReAct** — uma
redução de ~14 agentes. A mágica é que **um agente ReAct substitui vários agentes legacy**, porque
ele é flexível o suficiente para cobrir múltiplas funções dentro do mesmo domínio:

```
EXEMPLO REAL — DOMÍNIO "GESTÃO DE VAGAS":

ANTES (Legacy):                    DEPOIS (ReAct):
├── JobDraftingAgent               ├── WizardReActAgent (9 tools)
├── JobIntakeAgent                 │   └── 1 agente faz TUDO que
├── JobLifecycleAgent              │       os 6 faziam, porque
├── JobInsightsAgent               │       escolhe a tool certa
├── JobBenefitsCompAgent           │       conforme o contexto
├── JobRubricAgent                 │
│                                  │
│   6 agentes                      │   1 agente
│   6 arquivos de lógica           │   4 arquivos (padrão fixo)
│   Código duplicado entre eles    │   Zero duplicação
```

| Domínio | Hoje (total de agentes) | Futuro (só ReAct) | Redução |
|---------|:---:|:---:|:---:|
| Gestão de Vagas | 7 (1 ReAct + 6 Legacy) | 1 (WizardReAct) ✅ já existe | -6 |
| Assistente Recrutador | 4 (3 ReAct + 1 Legacy) | 3 (Kanban + Talent + JobsMgmt) ✅ já existe | -1 |
| Triagem de CVs | 4 (1 ReAct + 3 Legacy) | 1 (PipelineReAct) ✅ já existe | -3 |
| Sourcing | 2 (1 ReAct + 1 Legacy) | 1 (SourcingReAct) ✅ já existe | -1 |
| Políticas | 1 (1 ReAct) | 1 (PolicyReAct) ✅ já existe | 0 |
| Gestão de Vagas (LangGraph) | 1 (JobWizardGraph) | absorvido pelo WizardReAct | -1 |
| Comunicação | 1 Legacy | 1 ReAct (futuro) | 0 |
| Entrevistas | 2 Legacy | 1 ReAct (futuro) | -1 |
| Analytics | 2 Legacy | 1 ReAct (futuro) | -1 |
| Integração ATS | 1 Legacy | 1 ReAct (futuro) | 0 |
| Automação | 1 Legacy | 1 ReAct (futuro) | 0 |
| **TOTAL** | **26 agentes** | **~12 ReAct** | **~14 a menos** |

*\*O domínio "Assistente do Recrutador" tinha 1 agente legacy genérico que fazia tudo de forma
limitada. A versão ReAct dividiu em 3 agentes especializados (Kanban, Talent, JobsMgmt) que fazem
tudo bem — mas mesmo assim o total líquido da plataforma diminui de 26 para ~12.*

**O que enxuga de verdade não é só o número de agentes — é a complexidade total:**

- **Menos código**: Cada agente ReAct segue o padrão de 4 arquivos. Hoje os 18 legacy têm
  estruturas diferentes entre si.
- **Zero duplicação**: Serviços compartilhados (FairnessGuard, busca, cache) são acessados via
  tools, não replicados em cada agente.
- **Um único motor**: Todos os agentes ReAct usam o mesmo `ReActLoop`. Manutenção centralizada —
  melhora um, melhora todos.
- **Menos rotas de decisão**: O Orchestrator precisa saber rotear para 26 agentes hoje. Com
  migração completa, seriam ~12, todos via `ReactAgentRegistry`.

> **Analogia**: Hoje é como ter 26 funcionários, cada um com um manual de instruções diferente.
> Depois da migração, seriam ~12 funcionários, todos treinados pelo mesmo método, com acesso às
> mesmas ferramentas, mas cada um especialista na sua área.

##### Análise de Alinhamento — WeDO REAL (Recruiter Agent V5) vs WedoTalent

> **Contexto**: O time de desenvolvimento construiu o WeDO REAL (Recruiter Agent V5)
> baseado na documentação arquitetural da WedoTalent. Esta análise avalia o grau de alinhamento
> entre o que foi construído no WeDO REAL e a direção arquitetural da WedoTalent.

**Diagnóstico: O WeDO REAL é 100% Legacy.**

O Recruiter Agent V5 foi construído inteiramente na arquitetura legacy — não possui nenhum
componente ReAct. O WeDO REAL reproduziu fielmente a geração antiga da WedoTalent:

```
WeDO REAL (Recruiter Agent V5)        WEDOTALENT
─────────────────────────────         ──────────────────────────
DomainPrompt (ABC)                    DomainPrompt (ABC) ← LEGACY
  → process_intent()                    → process_intent() ← LEGACY
  → execute_action()                    → execute_action() ← LEGACY
DomainRegistry                        DomainRegistry ← LEGACY
DomainWorkflow (LangGraph 3 nós)      DomainWorkflow ← LEGACY
  intent → execute → format             (mesma estrutura)
DomainOrchestrator                    Orchestrator ← tem AMBOS
RouterAgent (keywords+regex+LLM)      CascadedRouter ← SIMILAR
MultiAgentOrchestrator                NÃO EXISTE na WeDoTalent
6 agentes especializados              18 agentes legacy equivalentes

❌ NÃO TEM: ReActLoop                ✅ TEM: ReActLoop
❌ NÃO TEM: Thought→Action→Observe   ✅ TEM: ciclo completo
❌ NÃO TEM: ToolDefinition/Registry   ✅ TEM: 89 tools tipadas
❌ NÃO TEM: Feature Flag             ✅ TEM: USE_REACT_AGENTS
```

**O que ESTÁ alinhado** (o WeDO REAL reproduz bem o legado):

| Conceito | WeDO REAL | WedoTalent (Legacy) | Veredicto |
|----------|---------|---------------------|-----------|
| DomainPrompt ABC | Implementado | Idêntico | ✅ Alinhado |
| process_intent() → LLM classifica | Gemini | Claude/Gemini | ✅ Alinhado |
| execute_action() → ação mapeada | Implementado | Idêntico | ✅ Alinhado |
| DomainRegistry + decorator | @register_domain | Mesmo padrão | ✅ Alinhado |
| DomainWorkflow (3 nós LangGraph) | intent→execute→format | Mesmo fluxo | ✅ Alinhado |
| ConversationMemory | Implementado | Equivalente | ✅ Alinhado |
| FairnessGuard | Implementado | Mais completo na WT | ⚠️ Parcial |
| Fast Routing (regex/keywords) | RouterAgent 3 cascatas | CascadedRouter 3 tiers | ✅ Similar |
| Cache/StatsManager | Implementado | Mais sofisticado na WT | ⚠️ Parcial |

**O que NÃO está alinhado** (o WeDO REAL não tem):

| Conceito da WedoTalent | Status no WeDO REAL | Impacto |
|-------------------------|-------------------|---------|
| **ReActLoop** (motor central) | ❌ Ausente | ALTO — é o futuro da plataforma |
| **89 ReAct Tools tipadas** | ❌ Ausente | ALTO — escalabilidade |
| **4-file pattern** (agent/prompt/tools/context) | ❌ Ausente | ALTO — padrão de organização |
| **Feature Flag** USE_REACT_AGENTS | ❌ Ausente | MÉDIO — controle de migração |
| **Fallback automático** ReAct→Legacy | ❌ Ausente | MÉDIO — resiliência |
| **Multi-provider LLM** (Claude+Gemini+GPT) | ❌ Só Gemini | MÉDIO — diversificação |
| **WSI (4 frameworks psicométricos)** | ❌ Ausente | MÉDIO — diferencial do produto |
| **PolicyEngine** (políticas por empresa) | ❌ Ausente | MÉDIO — compliance |
| **Token Tracking/Billing** | ❌ Ausente | BAIXO — operacional |

**O que o WeDO REAL tem que a WedoTalent NÃO tem:**

| Conceito do WeDO REAL | Existe na WT? | Observação |
|---------------------|---------------|------------|
| **MultiAgentOrchestrator** (6 sub-agentes) | ❌ Não | Abordagem diferente — na WT cada domínio é 1 agente com N tools |
| **ExecutionPlan** (8 planos multi-etapa) | ❌ Não | Na WT o ReActLoop decide sozinho a sequência |
| **FactChecker** (verifica claims da IA) | ❌ Não | Conceito interessante ausente na WT |
| **Pipeline Global** (6 nós sem domínio) | ❌ Não | Na WT tudo passa por domínio |

```
┌──────────────────────────────────────────────────────────────┐
│                  DIAGNÓSTICO DE ALINHAMENTO                   │
│                                                              │
│  O WeDO REAL reproduziu fielmente a GERAÇÃO ANTIGA (legacy)  │
│  da WedoTalent. Porém, a WedoTalent já está migrando         │
│  para a GERAÇÃO NOVA (ReAct).                                │
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│  │WeDO REAL│    │ WT hoje │    │ WT futuro│                  │
│  │ 100%    │    │ ~60%    │    │ 100%     │                  │
│  │ Legacy  │    │ ReAct   │    │ ReAct    │                  │
│  └─────────┘    └─────────┘    └─────────┘                  │
│       ↑              ↑              ↑                        │
│   WeDO REAL      WedoTalent     Para onde                    │
│    está AQUI      está AQUI      estamos indo                │
│                                                              │
│  RECOMENDAÇÃO: O WeDO REAL precisa incorporar o padrão       │
│  ReAct para estar alinhado com a direção da WedoTalent.      │
│  Caso contrário, estará construindo sobre uma base que       │
│  será descontinuada.                                         │
└──────────────────────────────────────────────────────────────┘
```

##### Plano de Alinhamento do WeDO REAL — Orientação Inicial

- **Fase 1 — Fundação (criar o motor ReAct)**: Implementar o `ReActLoop` (ciclo
  Thought→Action→Observation), a `ReActConfig` (max_iterations=5, temperature=0.3, guardrails,
  provider), o `BaseAgent` interface e o `ReactAgentRegistry` (singleton).
- **Fase 2 — Padrão de 4 arquivos**: Cada agente ReAct segue a estrutura
  `{nome}_react_agent.py` + `{nome}_system_prompt.py` + `{nome}_tool_registry.py` +
  `{nome}_stage_context.py`.
- **Fase 3 — Migrar Sourcing como piloto**: Converter os 6 sub-agentes (Search, Analytics,
  Detail, Comparison, Report, Action) em tools de um único `SourcingReActAgent`. O ReActLoop
  decide sozinho qual tool usar — eliminando RouterAgent, MultiAgentOrchestrator e ExecutionPlan.
- **Fase 4 — Feature Flag + Fallback**: Implementar `USE_REACT_AGENTS`, manter legacy funcionando
  em paralelo com fallback automático e logs de monitoramento.
- **Fase 5 — Multi-provider LLM**: Implementar `LLMFactory` que abstrai o provider (hoje só
  Gemini, futuro: Claude + GPT-4).

> **Prioridade sugerida**: (1) ReActLoop + ReActConfig → sem isso, nada mais funciona. (2) Migrar
> Sourcing como piloto → maior domínio, maior impacto. (3) Feature Flag → segurança na transição.
> (4) Multi-provider → pode vir depois.
>
> **O ponto mais importante**: No WeDO REAL hoje, o **código decide** o que fazer (if/else, handlers
> mapeados). No ReAct, a **IA decide** o que fazer (raciocina e escolhe tools). Essa é a mudança
> fundamental.

### 2.6 Observabilidade — Rastreando Cada Decisão

Cada execução do loop ReAct é registrada com telemetria completa:

```
┌──────────────────────────────────────────────────────────────────┐
│          REACT OBSERVER — TELEMETRIA DE EXECUÇÃO                 │
│                                                                  │
│  Para cada request do recrutador, é criado um registro:          │
│                                                                  │
│  AgentExecutionLog {                                             │
│    session_id          → Sessão do recrutador                    │
│    domain              → Qual domínio atendeu                    │
│    agent_class         → Qual agente específico                  │
│    total_duration_ms   → Tempo total de processamento            │
│    total_iterations    → Quantas vezes o loop rodou              │
│    tools_called        → Lista de ferramentas usadas             │
│    tools_succeeded     → Quantas sucederam                       │
│    tools_failed        → Quantas falharam                        │
│    final_confidence    → Confiança na resposta (0.0-1.0)         │
│    model_provider      → Qual LLM foi usado                     │
│    reasoning_chain     → Cadeia completa de raciocínio           │
│    stage_before/after  → Se houve transição de estágio           │
│  }                                                               │
│                                                                  │
│  Cada ITERAÇÃO dentro do loop também é registrada:               │
│                                                                  │
│  IterationLog {                                                  │
│    iteration, timestamp, phase, duration_ms                      │
│    tool_name, tool_args, tool_success                             │
│    reasoning   → "O que o agente pensou"                         │
│    observation → "O que o agente viu como resultado"              │
│    decision    → "respond" | "continue" | "error"                │
│  }                                                               │
│                                                                  │
│  → Permite auditoria completa: por que o agente fez X?           │
│  → Reprodutibilidade: mesma entrada → mesma cadeia               │
│  → Debugging: onde exatamente o agente errou?                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Orquestração: Quem Decide o Quê

### 3.1 CascadedRouter — Roteamento em 3 Camadas

Quando o recrutador envia uma mensagem, a primeira decisão é: **qual domínio deve atender?** O CascadedRouter resolve isso com uma estratégia em cascata — começa rápido e barato, e só escala para IA quando necessário:

```
┌──────────────────────────────────────────────────────────────────┐
│          CASCADED ROUTER — 3 CAMADAS DE ROTEAMENTO               │
│                                                                  │
│  Mensagem: "Qual o salário de mercado para dev Python?"          │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  CAMADA 1: MEMORY CACHE                              │       │
│  │                                                      │       │
│  │  Verifica cache de sessão/memória.                    │       │
│  │  "Esse usuário já perguntou sobre salários nesta      │       │
│  │   sessão? Se sim, manda para job_management."         │       │
│  │                                                      │       │
│  │  Latência: < 1ms  │  Custo: $0  │  Acurácia: Alta    │       │
│  └──────────┬───────────────────────────────────────────┘       │
│             │ MISS (primeira vez)                                │
│             ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  CAMADA 2: FAST ROUTER (Regex/Keywords)              │       │
│  │                                                      │       │
│  │  Cada domínio contribui um _KEYWORD_ACTION_MAP:      │       │
│  │  "salário"  → job_management    (conf: 0.72)         │       │
│  │  "cv"       → cv_screening      (conf: 0.64)         │       │
│  │  "agendar"  → interview_sched.  (conf: 0.74)         │       │
│  │                                                      │       │
│  │  Confiança = min(0.95, 0.6 + len(keyword) × 0.02)   │       │
│  │                                                      │       │
│  │  Latência: < 5ms  │  Custo: $0  │  Acurácia: Média   │       │
│  └──────────┬───────────────────────────────────────────┘       │
│             │ confidence < threshold                             │
│             ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  CAMADA 3: INTENT ROUTER (LLM)                       │       │
│  │                                                      │       │
│  │  Claude classifica intent + domínio em formato JSON:  │       │
│  │  { domain: "job_management", confidence: 0.92 }      │       │
│  │                                                      │       │
│  │  Usado apenas quando regex não tem confiança.         │       │
│  │  Representa ~15-20% dos requests.                     │       │
│  │                                                      │       │
│  │  Latência: 500-2000ms  │  Custo: ~$0.01              │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  RESULTADO: RouteResult { domain_id, confidence }                │
│                                                                  │
│  NOTA: O "intent" no orquestrador É o domain_id.                │
│  A classificação granular (qual ação dentro do domínio)          │
│  é feita pelo próprio domínio em process_intent().               │
└──────────────────────────────────────────────────────────────────┘
```

**Por que 3 camadas?**
- **Economia:** ~80% dos requests são resolvidos nas camadas 1+2 (custo $0)
- **Velocidade:** Latência média cai de ~1.5s (se fosse tudo LLM) para ~10ms
- **Resiliência:** Se o LLM estiver indisponível, as camadas 1+2 continuam funcionando

### 3.2 Orquestrador Central — O Hub de Coordenação

O Orchestrator é o componente central que coordena todos os outros. Ele é o "controlador de tráfego aéreo" da LIA:

```
┌──────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR — FLUXO COMPLETO                  │
│                                                                  │
│  Mensagem do Recrutador                                          │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────┐                                                │
│  │ 1. Cascaded  │  "Para qual domínio vai?"                      │
│  │    Router    │  → domain_id + confidence                      │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                                │
│  │ 2. State     │  "Qual o contexto atual?"                      │
│  │    Manager   │  → histórico, vaga ativa, candidato ativo,     │
│  │              │    etapa do wizard                              │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                                │
│  │ 3. Policy    │  "O recrutador PODE fazer isso?"               │
│  │    Engine    │  → RBAC, rate limits, regras de negócio        │
│  │              │  → max 10 buscas Pearch/dia                    │
│  │              │  → max 50.000 tokens/request                   │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                                │
│  │ 4. Task      │  "É uma tarefa simples ou complexa?"           │
│  │    Planner   │  Simples → direto para o domínio               │
│  │              │  Complexa → decompõe em sub-tarefas:           │
│  │              │  "Busque Python SR e compare com pipeline"     │
│  │              │  → Task 0: sourcing.search(Python, Senior)     │
│  │              │  → Task 1: assistant.compare(task_0.results)   │
│  └──────┬───────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                                │
│  │ 5. Plan      │  Executa as tarefas:                           │
│  │    Executor  │  • Resultado da task N → contexto da task N+1  │
│  │              │  • Execução paralela quando possível            │
│  │              │  • Retry com backoff exponencial em falha       │
│  └──────────────┘                                                │
│                                                                  │
│  RESULTADO: Resposta formatada para o recrutador                 │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 ConversationGraph — Conversas como Grafo de Estados

Para fluxos que precisam de uma sequência definida de passos (como criação de vaga), a LIA usa um **grafo de conversação** baseado em LangGraph:

```
┌──────────────────────────────────────────────────────────────────┐
│          CONVERSATION GRAPH — FLUXO DE ESTADOS                   │
│                                                                  │
│  Conceito: A conversa é modelada como um grafo onde cada         │
│  NÓ é um estado e cada ARESTA é uma transição possível.          │
│                                                                  │
│  GraphSession {                                                  │
│    session_id    → Identifica a sessão                           │
│    graph_type    → Tipo do grafo ("job_wizard", "screening"...)  │
│    current_node  → Estado atual no grafo                         │
│    state_data    → Dados acumulados (JSON)                       │
│  }                                                               │
│                                                                  │
│  Exemplo: Job Wizard Graph                                       │
│                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │  INPUT   │────▸│ JD           │────▸│ SALARY       │         │
│  │ EVALUAT. │     │ ENRICHMENT   │     │ BENCHMARK    │         │
│  │          │     │              │     │              │         │
│  │ Coleta   │     │ Gera JD com  │     │ Busca faixa  │         │
│  │ requisit.│     │ IA + enrique.│     │ salarial     │         │
│  └──────────┘     └──────────────┘     └──────┬───────┘         │
│                                               │                  │
│                                               ▼                  │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │ REVIEW   │◂────│ WSI          │◂────│ COMPETEN-    │         │
│  │ PUBLISH  │     │ QUESTIONS    │     │ CIES         │         │
│  │          │     │              │     │              │         │
│  │ Revisão  │     │ Gera perguntas│     │ Mapeia       │         │
│  │ final +  │     │ de triagem   │     │ competências │         │
│  │ publicar │     │ baseadas na JD│     │ e skills     │         │
│  └──────────┘     └──────────────┘     └──────────────┘         │
│                                                                  │
│  Cada nó pode:                                                   │
│  • Avançar para o próximo (dados suficientes)                    │
│  • Voltar para o anterior (recrutador quer editar)               │
│  • Permanecer (pedindo mais informações)                         │
│  • A cada nó, um agente ReAct específico é ativado               │
│                                                                  │
│  O estado persiste: se o recrutador sai e volta no dia           │
│  seguinte, a vaga continua exatamente onde parou.                │
└──────────────────────────────────────────────────────────────────┘
```

### 3.4 Anti-Sycophancy — A IA que Discorda

Um dos guardrails mais importantes é o sistema **anti-sycophancy** (anti-bajulação). A LIA não concorda cegamente com o recrutador:

```
┌─────────────────────────────────────────────────────────────────┐
│      ANTI-SYCOPHANCY — CONTRA-ARGUMENTAÇÃO BASEADA EM DADOS     │
│                                                                 │
│  CENÁRIO                          │ COMPORTAMENTO DA LIA        │
│  ─────────────────────────────────┼────────────────────────────  │
│  Salário muito abaixo do mercado  │ Apresenta benchmark +       │
│                                   │ contra-argumenta com dados  │
│                                   │                             │
│  "10 anos de experiência para     │ Aponta incompatibilidade +  │
│   cargo junior"                   │ sugere ajuste               │
│                                   │                             │
│  Skills conflitantes              │ "Java + .NET no mesmo       │
│  (Java + .NET juntos)             │ projeto é incomum" +        │
│                                   │ sugere stack coerente       │
│                                   │                             │
│  Rejeição sem critério objetivo   │ Mostra score do candidato + │
│                                   │ pede critérios técnicos     │
│                                   │                             │
│  Mover candidatos sem avaliação   │ Recomenda triagem WSI antes │
│                                   │                             │
│  ─────────────────────────────────┼────────────────────────────  │
│  REGRA: "NUNCA concorde silenciosamente com requisitos que      │
│  prejudicam a vaga / comprometam a qualidade do processo."      │
│                                                                 │
│  Se recrutador insiste após ver os dados:                       │
│  → Executa, mas documenta: "Configurado conforme solicitado.    │
│  Registro que o benchmark sugere [X]."                          │
│                                                                 │
│  Calibração por porte da empresa:                               │
│  STARTUP (<50 func.):   Requisitos flexíveis, equity OK         │
│  PME (50-500):          Equilíbrio requisitos/realidade          │
│  CORPORAÇÃO (>500):     Requisitos detalhados, compliance       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Busca Inteligente: Encontrando o Candidato Certo

### 4.1 O Pipeline de Busca — 6 Etapas

Buscar candidatos na WedoTalent não é uma query SQL simples. É um pipeline de 6 etapas que combina busca textual, busca vetorial, filtragem e ranking:

```
┌──────────────────────────────────────────────────────────────────┐
│          TALENT FUNNEL SEARCH PIPELINE — 6 ETAPAS                │
│                                                                  │
│  Recrutador digita: "Python sênior em São Paulo"                 │
│       │                                                          │
│       ▼                                                          │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 1: Expansão Semântica (Gemini)          │              │
│  │                                               │              │
│  │ "Python" → [FastAPI, Django, Flask, PyTorch,  │              │
│  │             Pandas, NumPy, Celery, SQLAlchemy] │              │
│  │                                               │              │
│  │ Amplia a busca para incluir tecnologias       │              │
│  │ relacionadas que o recrutador não digitou      │              │
│  │ Target: P95 < 300ms │ Cache: 5-10 min (Redis) │              │
│  └───────────────────┬───────────────────────────┘              │
│                      │                                           │
│         ┌────────────┴────────────┐                              │
│         │                         │                              │
│         ▼                         ▼                              │
│  ┌──────────────┐          ┌──────────────┐                     │
│  │ ETAPA 2A:    │          │ ETAPA 2B:    │                     │
│  │ Elasticsearch│          │ PG Vector    │                     │
│  │              │          │              │                     │
│  │ Full-text    │          │ Cosine       │                     │
│  │ search +     │          │ similarity   │                     │
│  │ BM25 scoring │          │ on embeddings│                     │
│  │              │          │ (768 dims)   │                     │
│  │ Encontra por │          │ Encontra por │                     │
│  │ palavras     │          │ significado  │                     │
│  │ exatas       │          │ semântico    │                     │
│  └──────┬───────┘          └──────┬───────┘                     │
│         │                         │                              │
│         └────────────┬────────────┘                              │
│                      ▼                                           │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 3: Pre-WRF Filter                       │              │
│  │                                               │              │
│  │ Filtragem determinística rápida:               │              │
│  │ • Senioridade compatível                       │              │
│  │ • Localização no raio de busca                 │              │
│  │ • Anos de experiência mínima                   │              │
│  │                                               │              │
│  │ Remove candidatos claramente inadequados       │              │
│  │ ANTES do ranking caro                          │              │
│  └───────────────────┬───────────────────────────┘              │
│                      ▼                                           │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 4: WRF (Weighted Ranking Framework)      │              │
│  │                                               │              │
│  │ Score = w1 × skills_match                      │              │
│  │       + w2 × experience_match                  │              │
│  │       + w3 × semantic_similarity               │              │
│  │       + w4 × location_match                    │              │
│  │       + w5 × seniority_match                   │              │
│  │                                               │              │
│  │ Pesos (w1-w5) são determinísticos e            │              │
│  │ ajustáveis por tipo de vaga                    │              │
│  └───────────────────┬───────────────────────────┘              │
│                      ▼                                           │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 5: PGV Gap Analyzer                      │              │
│  │                                               │              │
│  │ Analisa gaps semânticos: quais skills o        │              │
│  │ candidato NÃO tem comparado com o requerido?   │              │
│  │                                               │              │
│  │ Candidato tem Python + Django, mas não FastAPI  │              │
│  │ → Gap de FastAPI informado no resultado        │              │
│  └───────────────────┬───────────────────────────┘              │
│                      ▼                                           │
│  ┌───────────────────────────────────────────────┐              │
│  │ ETAPA 6: ES Score Drop Analyzer                │              │
│  │                                               │              │
│  │ Detecta quedas abruptas de score entre         │              │
│  │ candidatos consecutivos. Determina o           │              │
│  │ "corte natural" de relevância.                 │              │
│  │                                               │              │
│  │ Candidatos 1-15: score 85-92 (cluster A)       │              │
│  │ Candidatos 16-18: score 71-73 (QUEDA)          │              │
│  │ → Sugere corte nos 15 primeiros                │              │
│  └───────────────────────────────────────────────┘              │
│                                                                  │
│  Resultado: Lista rankeada + gaps + corte sugerido               │
│  + feedback loop para otimização estatística                     │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Por Que Duas Engines de Busca?

```
┌──────────────────────────────────────────────────────────────────┐
│  ELASTICSEARCH vs PG VECTOR — COMPLEMENTARES, NÃO CONCORRENTES  │
│                                                                  │
│  Elasticsearch (BM25):                                           │
│  ✓ "Python Developer" encontra "Desenvolvedora Python"          │
│  ✓ Busca por termos exatos, booleanos, proximidade              │
│  ✗ Não entende que "Machine Learning" ≈ "Deep Learning"         │
│                                                                  │
│  PG Vector (Cosine Similarity):                                  │
│  ✓ "Machine Learning" encontra "Deep Learning Engineer"         │
│  ✓ Entende significado semântico das palavras                    │
│  ✗ Pode retornar resultados semanticamente similares             │
│    mas não exatamente relevantes                                 │
│                                                                  │
│  JUNTOS: Cobertura máxima                                        │
│  • Elasticsearch garante que termos exatos são encontrados       │
│  • PG Vector garante que termos semanticamente próximos          │
│    também são encontrados                                        │
│  • WRF combina os scores de ambos em ranking unificado           │
│                                                                  │
│  Embeddings: text-embedding-004 (768 dimensões)                  │
│  Indexação: IVFFlat (>10k registros) ou HNSW                     │
│  Operador: <=> (cosine distance) │ Threshold: 0.7 (busca)       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Triagem WSI: A Metodologia Proprietária de Avaliação

### 5.1 O que é o WSI?

O **WSI (WeDoTalent Skill Index)** é a metodologia proprietária de avaliação de candidatos. Ele combina múltiplos frameworks psicométricos estabelecidos em um score composto de **7 blocos**, produzindo uma avaliação holística e não apenas técnica.

### 5.2 Os 7 Blocos do WSI

```
┌──────────────────────────────────────────────────────────────────┐
│                   WSI SCORE (0-100)                               │
│          WeDoTalent Skill Index — 7 Blocos                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ BLOCO 1: Competências Técnicas                    ████████│  │
│  │   Hard skills, certificações, domínio do stack            │  │
│  │   Avaliado por: extração de CV + perguntas técnicas       │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 2: Competências Comportamentais             ███████ │  │
│  │   Soft skills + mapeamento Big Five (OCEAN)               │  │
│  │   Avaliado por: perguntas comportamentais CBI             │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 3: Experiência Profissional                 ████████│  │
│  │   Histórico, senioridade, progressão de carreira          │  │
│  │   Avaliado por: parsing de CV + Modelo Dreyfus            │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 4: Fit Cultural                             ██████  │  │
│  │   Alinhamento com valores e cultura da empresa            │  │
│  │   Avaliado por: perguntas contextuais + CompanyCulture    │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 5: Potencial de Crescimento                 █████████│  │
│  │   Learning agility, adaptabilidade, curiosidade           │  │
│  │   Avaliado por: Taxonomia de Bloom + perguntas situac.    │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 6: Formação Acadêmica                       ████    │  │
│  │   Educação formal, cursos, certificações, idiomas         │  │
│  │   Avaliado por: extração de CV                            │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ BLOCO 7: Alinhamento com a Vaga                   ████████│  │
│  │   Match específico: requisitos da JD vs perfil            │  │
│  │   Avaliado por: comparação estruturada JD ↔ CV           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SCORE GLOBAL = Média ponderada dos 7 blocos                     │
│  (pesos configuráveis por empresa via CompanyHiringPolicy)       │
└──────────────────────────────────────────────────────────────────┘
```

### 5.3 Os 4 Frameworks Psicométricos Integrados

O WSI não inventa frameworks próprios. Ele integra 4 frameworks acadêmicos reconhecidos:

```
┌──────────────────────────────────────────────────────────────────┐
│          4 FRAMEWORKS PSICOMÉTRICOS DO WSI                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ 1. TAXONOMIA DE BLOOM                                │        │
│  │    "Quão PROFUNDO é o conhecimento?"                  │        │
│  │                                                      │        │
│  │    Nível 6: Criar      ████████████████████ (Expert) │        │
│  │    Nível 5: Avaliar    ██████████████████            │        │
│  │    Nível 4: Analisar   ████████████████              │        │
│  │    Nível 3: Aplicar    ██████████████                │        │
│  │    Nível 2: Entender   ████████████                  │        │
│  │    Nível 1: Lembrar    ████████        (Iniciante)   │        │
│  │                                                      │        │
│  │    Uso: Classifica profundidade cognitiva das         │        │
│  │    respostas do candidato na triagem                   │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ 2. MODELO DE DREYFUS                                 │        │
│  │    "Qual o NÍVEL DE PROFICIÊNCIA prática?"            │        │
│  │                                                      │        │
│  │    Novice → Adv. Beginner → Competent → Proficient   │        │
│  │                                          → Expert     │        │
│  │                                                      │        │
│  │    Uso: Classifica nível de expertise do candidato    │        │
│  │    baseado em experiência demonstrada                 │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ 3. BIG FIVE (OCEAN)                                  │        │
│  │    "Qual o PERFIL COMPORTAMENTAL?"                    │        │
│  │                                                      │        │
│  │    O = Openness (Abertura)                            │        │
│  │    C = Conscientiousness (Conscienciosidade)          │        │
│  │    E = Extraversion (Extroversão)                     │        │
│  │    A = Agreeableness (Amabilidade)                    │        │
│  │    N = Neuroticism (Neuroticismo)                     │        │
│  │                                                      │        │
│  │    Uso: Mapeia traços de personalidade do candidato   │        │
│  │    para avaliar fit cultural e comportamental         │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ 4. CBI (Competency-Based Interview)                  │        │
│  │    "As respostas têm EVIDÊNCIAS CONCRETAS?"           │        │
│  │                                                      │        │
│  │    Framework STAR:                                     │        │
│  │    S = Situation (contexto)                            │        │
│  │    T = Task (tarefa específica)                        │        │
│  │    A = Action (ação tomada)                            │        │
│  │    R = Result (resultado obtido)                       │        │
│  │                                                      │        │
│  │    Uso: Valida se o candidato apresenta evidências    │        │
│  │    comportamentais concretas, não apenas opiniões      │        │
│  └─────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

### 5.4 Pipeline Completo de Triagem

```
┌──────────────────────────────────────────────────────────────────┐
│          PIPELINE DE TRIAGEM WSI — 7 ETAPAS                      │
│                                                                  │
│  ┌──────────┐                                                    │
│  │ 1. PARSE │  CV (PDF/Docx) → Extração estruturada             │
│  │    CV     │  Nome, email, skills, experiência, formação       │
│  │          │  + Layout score (Claude Vision: 1-10)              │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 2. SCORE │  Avaliação automática contra requisitos da vaga    │
│  │    AUTO   │  "Candidato tem 70% das skills obrigatórias"      │
│  │          │  Scoring quantitativo (determinístico + LLM)       │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 3. GERAR │  3 camadas de perguntas:                           │
│  │ PERGUNTAS│  1. Derived: geradas pelo LLM a partir da JD      │
│  │    WSI   │  2. Company Bank: banco de perguntas da empresa    │
│  │          │  3. Custom: criadas pelo recrutador                │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 4. ENTRE-│  Candidato responde as perguntas                   │
│  │ VISTA WSI│  Opções: texto, áudio (Deepgram transcreve),       │
│  │          │  ou vídeo (Gemini analisa body language)            │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 5. CALCU-│  Avaliação das respostas usando 4 frameworks:      │
│  │ LAR WSI  │  Bloom + Dreyfus + Big Five + CBI                  │
│  │          │  → Score final por bloco (0-100)                   │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 6. RANK  │  Normalização de scores entre candidatos           │
│  │          │  Score Normalization Service unifica escalas        │
│  │          │  (WSI, entrevista, CV, testes) → comparação justa  │
│  └────┬─────┘                                                    │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ 7. CORTE │  Seleção do top 25% (corte dinâmico)              │
│  │ DINÂMICO │  Baseado em distribuição estatística real           │
│  │          │  + ES Score Drop (queda abrupta de relevância)     │
│  └──────────┘                                                    │
│                                                                  │
│  SAÍDA: Parecer completo com WSI Scorecard + Evidências          │
│  + Pontos fortes/atenção + Recomendação + Senioridade calibrada  │
│  + Compliance (FairnessGuard ✓ │ FactChecker ✓ │ LGPD ✓)       │
└──────────────────────────────────────────────────────────────────┘
```

### 5.5 Análise Multimodal — Além do Texto

A triagem WSI não se limita a texto. A LIA pode analisar múltiplos formatos:

```
┌──────────────────────────────────────────────────────────────────┐
│          ANÁLISE MULTIMODAL — 3 PROVEDORES                       │
│                                                                  │
│  ┌────────────────────────────────────────────────┐             │
│  │ CLAUDE VISION (Anthropic)                       │             │
│  │ • CV visual → layout score (1-10), organização  │             │
│  │ • Foto profissional → professionalism score     │             │
│  │ • Documento → extração estruturada              │             │
│  │ Formatos: jpg, png, gif, webp                   │             │
│  └────────────────────────────────────────────────┘             │
│                                                                  │
│  ┌────────────────────────────────────────────────┐             │
│  │ GEMINI (Google)                                 │             │
│  │ • Vídeo de entrevista → body language,          │             │
│  │   eye contact, confiança (score 1-10)           │             │
│  │ • Apresentação técnica → effectiveness score    │             │
│  └────────────────────────────────────────────────┘             │
│                                                                  │
│  ┌────────────────────────────────────────────────┐             │
│  │ VOZ (Deepgram Nova-2 + OpenAI Whisper fallback) │             │
│  │ • Transcrição de áudio (pt-BR)                  │             │
│  │ • WSI Voice Orchestrator: candidato responde     │             │
│  │   perguntas WSI por áudio → transcrição → score │             │
│  │ • TTS: LIA fala as perguntas (OpenAI TTS)       │             │
│  │ Formatos: mp3, wav, webm, m4a, ogg, flac        │             │
│  └────────────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Memória e Aprendizado: Uma IA que Lembra e Evolui

### 6.1 Arquitetura de Memória em 3 Níveis

A LIA possui um sistema de memória sofisticado que opera em três horizontes temporais:

```
┌──────────────────────────────────────────────────────────────────┐
│          SISTEMA DE MEMÓRIA — 3 HORIZONTES                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 1: Working Memory (Memória de Trabalho)              │  │
│  │ Horizonte: Sessão atual (minutos/horas)                    │  │
│  │                                                            │  │
│  │ O que armazena:                                            │  │
│  │ • Histórico de mensagens da conversa atual                 │  │
│  │ • Contexto acumulado (vaga ativa, candidato ativo)         │  │
│  │ • Estado do wizard (etapa atual, dados preenchidos)        │  │
│  │                                                            │  │
│  │ Como funciona:                                             │  │
│  │ Cada mensagem é adicionada ao estado do StateManager.      │  │
│  │ O agente sempre vê as últimas N mensagens como contexto.   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 2: Conversation Memory (Memória Conversacional)      │  │
│  │ Horizonte: Cross-sessão (dias/semanas)                     │  │
│  │                                                            │  │
│  │ O que armazena:                                            │  │
│  │ • Embeddings das conversas anteriores (Vector 768)         │  │
│  │ • Busca por similaridade semântica                         │  │
│  │                                                            │  │
│  │ Tabela: conversation_memories                              │  │
│  │ • embedding: Vector(768)                                   │  │
│  │ • content: texto da conversa                               │  │
│  │ • session_id: de qual sessão veio                          │  │
│  │                                                            │  │
│  │ Exemplo: "Na semana passada discutimos que a vaga de       │  │
│  │ Python Senior precisa de experiência com FastAPI."          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 3: Long-Term Memory (Memória de Longo Prazo)         │  │
│  │ Horizonte: Permanente (meses/anos)                         │  │
│  │                                                            │  │
│  │ O que armazena:                                            │  │
│  │ • Padrões aprendidos ("pattern")                           │  │
│  │ • Preferências da empresa ("preference")                   │  │
│  │ • Aprendizados ("learning")                                │  │
│  │ • Resultados de contratações ("outcome")                   │  │
│  │                                                            │  │
│  │ Tabela: agent_long_term_memory                             │  │
│  │ • company_id: escopo por empresa (multi-tenant)            │  │
│  │ • domain: qual agente criou                                │  │
│  │ • memory_key: ex: "salary_range_dev_senior"                │  │
│  │ • memory_value: JSON com dados                             │  │
│  │ • usage_count: popularidade (quantas vezes usada)          │  │
│  │ • relevance_score: 0.0-1.0 (com decay temporal)           │  │
│  │                                                            │  │
│  │ Ranking: score = relevance × (usage_count + 1)             │  │
│  │ → Memórias mais usadas e mais relevantes aparecem primeiro │  │
│  │ → Relevância decai com o tempo (decay_factor = 0.95)       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  INTEGRAÇÃO: MemoryIntegration combina os 3 níveis              │
│  get_enriched_context() → "=== Session Memory ===" +            │
│                            "=== Cross-Session Learnings ==="     │
│  → Injetado no prompt do agente como extra_context              │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Cache Inteligente de 3 Camadas

Para evitar chamadas repetidas (e caras) ao LLM, a LIA usa cache em 3 camadas:

```
┌──────────────────────────────────────────────────────────────────┐
│          CACHE MANAGER — 3 CAMADAS                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 1: Session Cache (In-Memory)      HOT              │  │
│  │ TTL: 1 hora │ Max: 1.000 entries │ Latência: <1ms         │  │
│  │ Escopo: Por conversa/sessão                                │  │
│  │ Uso: Respostas recentes, estado de workflow                │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │ miss                               │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 2: Redis Cache                    WARM              │  │
│  │ TTL: 1-30 dias (por namespace) │ Latência: ~1-5ms          │  │
│  │ Escopo: Global (compartilhado entre sessões)               │  │
│  │                                                            │  │
│  │ Namespaces:                                                │  │
│  │ • SALARY_BENCHMARK:    7 dias   (dados salariais)          │  │
│  │ • SKILLS_SUGGESTIONS:  30 dias  (expansão semântica)       │  │
│  │ • LLM_RESPONSE:        7 dias   (respostas cacheadas)      │  │
│  │ • EMBEDDINGS:          30 dias  (vetores gerados)          │  │
│  │ • COMPANY_CONFIG:      7 dias   (config da empresa)        │  │
│  │ • LEARNING_PATTERNS:   30 dias  (padrões aprendidos)       │  │
│  │                                                            │  │
│  │ Features: similarity matching (threshold 0.75-0.90),       │  │
│  │ graceful degradation para in-memory se Redis cai,          │  │
│  │ multi-tenant via company_id scoping                        │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │ miss                               │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 3: PostgreSQL Cache               COLD              │  │
│  │ TTL: 30+ dias │ Latência: ~5-20ms                          │  │
│  │ Tabela: intelligent_cache                                  │  │
│  │ Uso: Configurações de empresa, padrões aprendidos,         │  │
│  │      embeddings, dados estáveis                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  AI Cache Service (camada especializada para conteúdo IA):       │
│  • jd_generation:      24h, threshold 0.85                       │
│  • wsi_questions:      48h, threshold 0.90                       │
│  • skills_extraction:  72h, threshold 0.80                       │
│  • salary_analysis:    12h, threshold 0.75                       │
│  • competency_mapping: 48h, threshold 0.85                       │
│                                                                  │
│  → Cache semântico: não precisa ser a MESMA query,               │
│    basta ser SIMILAR o suficiente (cosine similarity)             │
└──────────────────────────────────────────────────────────────────┘
```

### 6.3 Learning Loop — Aprendizado Contínuo

A LIA aprende com os resultados das contratações para melhorar ao longo do tempo:

```
┌──────────────────────────────────────────────────────────────────┐
│          LEARNING LOOP — CICLO DE APRENDIZADO                    │
│                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │ AÇÃO     │────▸│ RESULTADO    │────▸│ FEEDBACK     │         │
│  │          │     │              │     │              │         │
│  │ LIA faz  │     │ Candidato    │     │ Recrutador   │         │
│  │ triagem  │     │ contratado   │     │ avalia:      │         │
│  │ e dá     │     │ ou rejeitado │     │ útil/inútil  │         │
│  │ score 85 │     │              │     │ preciso/imp. │         │
│  └──────────┘     └──────────────┘     └──────┬───────┘         │
│                                               │                  │
│                                               ▼                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ APRENDIZADO                                                │  │
│  │                                                            │  │
│  │ 1. LearningPattern registra padrão:                        │  │
│  │    "Para vagas Python Senior em SP, candidatos com         │  │
│  │     FastAPI+Docker tiveram 80% de sucesso"                 │  │
│  │                                                            │  │
│  │ 2. InteractionFeedback grava avaliação:                    │  │
│  │    rating=4/5, "recomendação foi precisa"                  │  │
│  │                                                            │  │
│  │ 3. FeedbackEvent registra evento:                          │  │
│  │    "recrutador aceitou sugestão de skills"                 │  │
│  │                                                            │  │
│  │ 4. LongTermMemory persiste como "outcome":                 │  │
│  │    key="hiring_success_python_sr_sp",                      │  │
│  │    value={success_rate: 0.80, sample_size: 15}             │  │
│  └────────────────────────────────┬───────────────────────────┘  │
│                                   │                              │
│                                   ▼                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ APLICAÇÃO                                                  │  │
│  │                                                            │  │
│  │ Na próxima triagem similar, a memória é injetada:          │  │
│  │ "=== Cross-Session Learnings ===                           │  │
│  │  Known Patterns: Para Python Senior em SP, priorize        │  │
│  │  candidatos com FastAPI+Docker (80% success rate, n=15)"   │  │
│  │                                                            │  │
│  │ → O agente usa esse contexto para calibrar sua avaliação   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Processamento Assíncrono: Trabalhando em Escala

### 7.1 Por Que Processamento Assíncrono?

Algumas operações são pesadas demais para executar em tempo real. Quando o recrutador pede "triar 200 candidatos", a LIA não pode fazê-lo esperar 30 minutos. A solução: **processamento em background**.

```
┌──────────────────────────────────────────────────────────────────┐
│          PROCESSAMENTO ASSÍNCRONO — ARQUITETURA                  │
│                                                                  │
│  Recrutador: "Faça a triagem dos 200 candidatos da vaga X"       │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────────┐                                        │
│  │ Resposta Imediata    │  "Iniciei a triagem de 200 candidatos. │
│  │ (< 2 segundos)       │   Vou notificá-lo quando terminar."   │
│  └──────────┬───────────┘                                        │
│             │                                                    │
│             ▼                                                    │
│  ┌──────────────────────────────────────────────┐               │
│  │ RabbitMQ (Fila de Mensagens)                  │               │
│  │                                              │               │
│  │ 4 filas especializadas:                       │               │
│  │ ├── cv_screening:  bulk_screen, batch_eval    │               │
│  │ ├── communication: mass_email, mass_whatsapp  │               │
│  │ ├── ats_sync:      bulk_sync, full_import     │               │
│  │ └── reports:       full_report, export_data   │               │
│  └──────────────┬───────────────────────────────┘               │
│                 │                                                │
│                 ▼                                                │
│  ┌──────────────────────────────────────────────┐               │
│  │ Celery Workers (Pool de Processamento)        │               │
│  │                                              │               │
│  │ Worker 1: bulk_screening_task                 │               │
│  │   → WSI pipeline para cada candidato          │               │
│  │   → Usa Claude para scoring                   │               │
│  │                                              │               │
│  │ Worker 2: mass_communication_task             │               │
│  │   → Envia emails/WhatsApp em lote             │               │
│  │   → Rate limiting por provider                │               │
│  │                                              │               │
│  │ Worker 3: ats_sync_task                       │               │
│  │   → Sincroniza com Gupy/Pandapé               │               │
│  │   → Idempotency e retry automático            │               │
│  │                                              │               │
│  │ Worker 4: scheduled_reports_task              │               │
│  │   → Daily briefings, weekly reports           │               │
│  └──────────────────────────────────────────────┘               │
│                                                                  │
│  Configuração de domínios elegíveis para async:                  │
│  max_concurrent_per_domain = 3                                   │
│  max_queue_size = 100                                            │
│                                                                  │
│  9 domínios × ações elegíveis:                                   │
│  sourcing: bulk_search, mass_outreach, import_candidates         │
│  cv_screening: bulk_screen, batch_evaluate, full_pipeline        │
│  communication: mass_email, mass_whatsapp, bulk_notification     │
│  analytics: generate_full_report, export_dataset, predictive     │
│  ...e mais 5 domínios                                            │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 EnhancedTaskManager — Resiliência de Tarefas

O sistema nativo de tarefas (não Celery) provê funcionalidades adicionais:

```
┌──────────────────────────────────────────────────────────────────┐
│          ENHANCED TASK MANAGER — RESILIÊNCIA                     │
│                                                                  │
│  TaskQueue        → Fila de tarefas com prioridade               │
│       │                                                          │
│       ▼                                                          │
│  TaskScheduler    → Agendamento (cron + interval)                │
│       │                                                          │
│       ▼                                                          │
│  TaskPersistence  → Salva estado no banco (sobrevive restart)    │
│       │                                                          │
│       ▼                                                          │
│  EnhancedTask     → Retry com backoff exponencial                │
│  Manager          → Dead Letter Queue (DLQ) para falhas          │
│                   → Monitoring com health checks                 │
│                   → MAX_TOOL_CALLS_PER_REQUEST: 3                │
│                                                                  │
│  Se uma task falha 3x:                                           │
│  → Move para DLQ (Dead Letter Queue)                             │
│  → Pode ser reprocessada manualmente                             │
│  → Alerta de monitoramento é gerado                              │
│                                                                  │
│  Proteção anti-loop: máximo 3 chamadas de tool por request       │
│  → Evita que um bug gere centenas de chamadas LLM               │
└──────────────────────────────────────────────────────────────────┘
```

### 7.3 Comunicação Multi-Canal

A LIA se comunica por 5 canais, todos gerenciados por uma abstração unificada:

```
┌──────────────────────────────────────────────────────────────────┐
│          MULTI-CHANNEL SERVICE — 5 CANAIS                        │
│                                                                  │
│  MultiChannelService                                             │
│       │                                                          │
│       ├── ChannelRouter (decide o melhor canal)                  │
│       │                                                          │
│       ├── EmailAdapter       → SendGrid / SMTP                  │
│       ├── WhatsAppAdapter    → Twilio / Meta API                │
│       ├── SMSAdapter         → Twilio                           │
│       ├── TeamsAdapter       → Microsoft Graph                  │
│       └── InAppAdapter       → Notificações internas            │
│                                                                  │
│  Cada adapter:                                                   │
│  • Template engine com variáveis dinâmicas                       │
│  • Rate limiting por provider                                    │
│  • Retry automático em falha                                     │
│  • Tracking de entrega e abertura                                │
│  • LGPD: registro de consentimento e opt-out                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Compliance e Ética: IA Responsável por Design

### 8.1 FairnessGuard — 3 Camadas Contra Viés

O **FairnessGuard** é o sistema de proteção contra viés discriminatório. Ele opera em 3 camadas progressivas, de rápida a profunda:

```
┌──────────────────────────────────────────────────────────────────┐
│          FAIRNESS GUARD — 3 CAMADAS ANTI-VIÉS                    │
│                                                                  │
│  Texto a verificar: "Preciso de um candidato jovem e dinâmico"   │
│       │                                                          │
│       ▼                                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 1: Regex/Keyword Matching                           │  │
│  │ Latência: < 1ms │ Custo: $0                                │  │
│  │                                                            │  │
│  │ Detecta termos explicitamente discriminatórios:             │  │
│  │ "jovem" → ALERTA (discriminação por idade)                 │  │
│  │ "bonita" → ALERTA (aparência física)                       │  │
│  │ "casado" → ALERTA (estado civil)                           │  │
│  │ "cristão" → ALERTA (religião)                              │  │
│  │                                                            │  │
│  │ Se detecta → Para imediatamente com alerta                 │  │
│  │ Se não detecta → Passa para Camada 2                       │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │ passou                             │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 2: Detecção de Viés Implícito                       │  │
│  │ Latência: < 5ms │ Custo: $0                                │  │
│  │                                                            │  │
│  │ Detecta padrões que sugerem viés sem termos explícitos:     │  │
│  │ "boa aparência" → Viés de aparência                        │  │
│  │ "formação em universidade de ponta" → Viés socioeconômico  │  │
│  │ "sem filhos" → Discriminação familiar                      │  │
│  │                                                            │  │
│  │ Se detecta → Alerta com sugestão de reformulação           │  │
│  │ Se não detecta → Passa para Camada 3 (quando ativada)      │  │
│  └──────────────────────────┬─────────────────────────────────┘  │
│                             │ passou                             │
│                             ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CAMADA 3: Análise Semântica LLM (Deep Check)               │  │
│  │ Latência: 500-2000ms │ Custo: ~$0.01                       │  │
│  │                                                            │  │
│  │ LLM analisa o CONTEXTO COMPLETO para viés sutil:           │  │
│  │ "Buscamos alguém com energia para acompanhar nosso         │  │
│  │  ritmo acelerado" → Pode indicar discriminação por idade   │  │
│  │                                                            │  │
│  │ Usado em: validação de políticas de contratação,           │  │
│  │ análise profunda de JDs, revisão de critérios de rejeição  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  INTEGRAÇÃO nos agentes ReAct:                                   │
│  • Wizard: validate_job_requirements usa FairnessGuard 3-tier    │
│  • Kanban: check_rejection_fairness ANTES de qualquer rejeição   │
│  • Talent: check_search_fairness valida critérios de busca       │
│  • JobsMgmt: validate_job_action_fairness em ações de gestão     │
│  • Policy: validate_policy_compliance com deep check semântico   │
│                                                                  │
│  REGRA no system prompt do Kanban:                               │
│  "SEMPRE use check_rejection_fairness ANTES de registrar         │
│   qualquer rejeição"                                             │
└──────────────────────────────────────────────────────────────────┘
```

### 8.2 FactChecker — Validação de Veracidade

O **FactChecker** é um middleware pós-processamento que valida se a resposta da IA contém afirmações factualmente corretas:

```
┌──────────────────────────────────────────────────────────────────┐
│          FACT CHECKER — 4 VALIDADORES                            │
│                                                                  │
│  Resposta do LLM                                                 │
│       │                                                          │
│       ▼                                                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 1. _check_salary_claims()                                  │  │
│  │    Regex: R$\s*([\d.,]+)                                   │  │
│  │    Range válido: R$ 1.500 — R$ 200.000                     │  │
│  │    Se há dados reais → compara desvio %                    │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 2. _check_candidate_counts()                               │  │
│  │    Regex: (\d+)\s*candidatos?                              │  │
│  │    Limite: max 50.000                                      │  │
│  │    Se há dado real → compara com context["total_candidat."]│  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 3. _check_percentage_claims()                              │  │
│  │    Regex: (\d+(?:[.,]\d+)?)\s*%                            │  │
│  │    Range: 0% — 100%                                        │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 4. _check_date_claims()                                    │  │
│  │    Regex: (\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})        │  │
│  │    Validação de formato e razoabilidade                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│       │                                                          │
│       ▼                                                          │
│  FactCheckResult {                                               │
│    total_claims         → Quantas afirmações detectadas          │
│    verified_claims      → Quantas verificadas contra dados reais │
│    accurate_claims      → Quantas estão corretas                 │
│    inaccurate_claims    → Quantas estão ERRADAS                  │
│    overall_accuracy     → accurate / verified                    │
│  }                                                               │
│                                                                  │
│  Se inaccurate_claims > 0 → WARNING no log                      │
│  Metadata adicionada à resposta para transparência               │
└──────────────────────────────────────────────────────────────────┘
```

### 8.3 AuditService — Explicabilidade Completa

Toda decisão de IA é registrada para auditoria (LGPD Art. 20, EU AI Act Art. 14):

```
┌──────────────────────────────────────────────────────────────────┐
│          AUDIT SERVICE — RASTREABILIDADE COMPLETA                 │
│                                                                  │
│  Cada decisão registra:                                          │
│  • decision_type:     SCORE_CANDIDATE, REJECT, MOVE_STAGE...    │
│  • agent_id:          Qual agente decidiu                        │
│  • input_data:        Dados de entrada (contexto)                │
│  • output_data:       Resultado da decisão                       │
│  • criteria_evaluated: Critérios avaliados (prova de não-bias)   │
│  • criteria_ignored:  Critérios deliberadamente ignorados        │
│  • justification:     Justificativa textual                      │
│  • llm_model:         Modelo LLM usado                           │
│  • prompt_hash:       Hash do prompt (reprodutibilidade)         │
│                                                                  │
│  Retenção por tipo (LGPD):                                       │
│  • Decisões de scoring:   730 dias (2 anos)                      │
│  • Rejeições:             1.095 dias (3 anos)                    │
│  • Contratações:          1.825 dias (5 anos)                    │
│                                                                  │
│  → Permite responder: "Por que a IA rejeitou o candidato X?"     │
│  → Com cadeia completa: raciocínio + dados + critérios           │
└──────────────────────────────────────────────────────────────────┘
```

### 8.4 Human-in-the-Loop — Quando a IA Pede Permissão

Nem tudo é automático. Ações com impacto externo requerem confirmação:

```
┌──────────────────────────────────────────────────────────────────┐
│          HUMAN-IN-THE-LOOP — O QUE PRECISA DE APROVAÇÃO          │
│                                                                  │
│  REQUER CONFIRMAÇÃO (efeito externo):                            │
│  ✓ Envio de email em massa        → Comunicação irreversível     │
│  ✓ Rejeição de candidato          → Decisão final negativa       │
│  ✓ Publicação de vaga             → Exposição pública            │
│  ✓ Movimentação no pipeline       → Mudança de etapa             │
│  ✓ Agendamento de entrevista      → Compromisso com candidato    │
│  ✓ Envio via WhatsApp             → Comunicação direta           │
│                                                                  │
│  AUTOMÁTICO (informativo, sem efeito externo):                   │
│  ✗ Geração de Job Description     → Preview antes de publicar    │
│  ✗ Scoring WSI                    → Informativo                  │
│  ✗ Sugestões de skills            → Sugestão editável            │
│  ✗ Busca de candidatos            → Apenas listagem              │
│                                                                  │
│  PRINCÍPIO: "Toda ação que causa efeito externo                  │
│  (envia, publica, rejeita, agenda) requer confirmação.           │
│  Ações informativas são automáticas."                            │
│                                                                  │
│  Implementação: guardrails no ReActConfig                        │
│  → Tool marcada como guardrail → agente pede confirmação         │
│  → Recrutador confirma → agente executa                          │
│  → Recrutador rejeita → agente para                              │
└──────────────────────────────────────────────────────────────────┘
```

### 8.5 LGPD — Proteção de Dados Pessoais

```
┌──────────────────────────────────────────────────────────────────┐
│          LGPD — IMPLEMENTAÇÃO TÉCNICA                            │
│                                                                  │
│  PII Masking (mascaramento de dados pessoais):                   │
│  • Dados sensíveis mascarados em logs e traces                   │
│  • Pretensão salarial NUNCA sincronizada com ATS                │
│                                                                  │
│  Consentimento (Art. 8):                                         │
│  • ConsentRecord: registro de consentimento com base legal       │
│  • ConsentVersion: versionamento de termos                       │
│  • ConsentEvent: grant / revoke / renew                          │
│                                                                  │
│  Direitos do Titular (Art. 18):                                  │
│  • DataSubjectRequest: requisições de acesso/exclusão/correção   │
│  • DataAccessLog: log de todo acesso a dados pessoais            │
│                                                                  │
│  Agentes ReAct (system prompts):                                 │
│  • Wizard: "Nunca solicite dados pessoais sensíveis              │
│    (raça, religião, orientação sexual, estado civil)"            │
│  • Kanban: "Proteja dados pessoais dos candidatos em             │
│    todas as comunicações"                                        │
│                                                                  │
│  7 frameworks de compliance monitorados:                         │
│  SOX, SOC2, ISO27001, LGPD, BCB498, EU AI Act, NYC LL144        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. Automação e Predição: De Reativa a Proativa

### 9.1 Stage Automation Engine — 16 Triggers

O motor de automação observa eventos no pipeline e dispara ações automaticamente (ou sugere ao recrutador):

```
┌──────────────────────────────────────────────────────────────────┐
│          STAGE AUTOMATION — 16 TRIGGERS                          │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ EVENTOS DE TRIGGER:                                        │   │
│  │                                                           │   │
│  │ Triagem:                        Pipeline:                  │   │
│  │ • SCREENING_COMPLETED           • STAGE_CHANGED            │   │
│  │ • CANDIDATE_APPLIED             • CANDIDATE_INACTIVE       │   │
│  │ • CANDIDATES_SOURCED            • NO_RESPONSE_48H          │   │
│  │                                                           │   │
│  │ Entrevista:                     Ofertas:                   │   │
│  │ • INTERVIEW_SCHEDULED           • OFFER_SENT               │   │
│  │ • INTERVIEW_COMPLETED           • CANDIDATE_HIRED          │   │
│  │ • CANDIDATE_NO_SHOW             • CANDIDATE_REJECTED       │   │
│  │                                                           │   │
│  │ Outros:                                                    │   │
│  │ • ATS_SYNC                      • FEEDBACK_RECEIVED        │   │
│  │ • JOB_PUBLISHED                 • DEADLINE_APPROACHING     │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  FLUXO DE PROCESSAMENTO:                                         │
│                                                                  │
│  Evento → Validação Multi-Tenant → Avaliar Regras da Empresa     │
│                                         │                        │
│                          ┌──────────────┴──────────────┐        │
│                          ▼                             ▼        │
│                    auto_execute?                  Criar Sugestão │
│                    (nível autonomia)              para Aprovação  │
│                          │                             │        │
│                          ▼                             ▼        │
│                    Executar handler              Recrutador      │
│                    automaticamente               aprova/rejeita  │
│                          │                             │        │
│                          └──────────────┬──────────────┘        │
│                                         ▼                        │
│                                    Audit Log                     │
│                                                                  │
│  Condições avaliáveis por regra:                                 │
│  • min_wsi_score    → Score WSI mínimo                           │
│  • stages           → Etapa específica do pipeline               │
│  • min_confidence   → Confiança mínima da IA                     │
│  • source_types     → Tipo de fonte (interno, Pearch)            │
│  • min_cv_score     → Score mínimo de CV                         │
└──────────────────────────────────────────────────────────────────┘
```

### 9.2 Alertas Proativos — 5 Categorias

A LIA monitora continuamente e gera alertas inteligentes:

```
┌──────────────────────────────────────────────────────────────────┐
│          ALERTAS PROATIVOS — 5 CATEGORIAS                        │
│                                                                  │
│  ┌────────────────────────────────────┐                         │
│  │ 1. PIPELINE (saúde do funil)       │                         │
│  │ • Conversão < 5% → WARNING         │                         │
│  │ • 5+ candidatos parados 10+ dias   │                         │
│  │ • Oferta sem resposta há 72h       │ → URGENT                │
│  │ • Pipeline com < 3 candidatos      │ → URGENT                │
│  └────────────────────────────────────┘                         │
│  ┌────────────────────────────────────┐                         │
│  │ 2. PRODUTIVIDADE (recrutador)      │                         │
│  │ • 5+ tarefas atrasadas            │ → URGENT                │
│  │ • Sem atividade há 2h             │ → INFO                  │
│  │ • < 50% da meta às 16h            │ → WARNING               │
│  │ • Scorecards pendentes            │                         │
│  └────────────────────────────────────┘                         │
│  ┌────────────────────────────────────┐                         │
│  │ 3. COMUNICAÇÃO (saúde de comms)    │                         │
│  │ • Taxa de entrega de email baixa   │                         │
│  │ • Candidatos sem resposta          │                         │
│  │ • Taxa alta de opt-out             │                         │
│  └────────────────────────────────────┘                         │
│  ┌────────────────────────────────────┐                         │
│  │ 4. PREDITIVO (insights IA)         │                         │
│  │ • Dropout risk alto                │                         │
│  │ • Time-to-fill em risco de SLA     │                         │
│  │ • Candidato ideal detectado!       │                         │
│  │ • Padrão de rejeição detectado     │                         │
│  └────────────────────────────────────┘                         │
│  ┌────────────────────────────────────┐                         │
│  │ 5. SISTEMA (saúde técnica)         │                         │
│  │ • Falha na sincronização ATS       │                         │
│  │ • Agente IA com health baixo       │                         │
│  │ • Créditos de IA acabando          │                         │
│  │ • Erro em decisão de IA            │                         │
│  └────────────────────────────────────┘                         │
│                                                                  │
│  Cada alerta tem:                                                │
│  • threshold configurável                                        │
│  • severity: INFO | WARNING | URGENT                             │
│  • cooldown_hours: evita repetição excessiva                     │
└──────────────────────────────────────────────────────────────────┘
```

### 9.3 OutcomePredictor — Predições Acionáveis

O sistema preditivo calcula probabilidades para ajudar decisões:

```
┌──────────────────────────────────────────────────────────────────┐
│          OUTCOME PREDICTOR — 4 TIPOS DE PREDIÇÃO                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 1. predict_hiring_probability()                            │  │
│  │    "Qual a chance deste candidato ser contratado?"          │  │
│  │    Fatores: WSI score, fit cultural, senioridade match,     │  │
│  │    disponibilidade, pretensão salarial vs range             │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 2. predict_dropout_risk()                                  │  │
│  │    "Qual o risco de desistência?"                           │  │
│  │    Fatores e pesos:                                        │  │
│  │    • dropout_base:             0.15                         │  │
│  │    • time_in_pipeline:         0.25 (mais tempo → risco)   │  │
│  │    • communication_frequency:  0.20 (menos comms → risco)  │  │
│  │    • response_time:            0.10 (mais lento → risco)   │  │
│  │                                                            │  │
│  │    Classificação: LOW <30% │ MEDIUM 30-60% │               │  │
│  │                    HIGH 60-80% │ CRITICAL >80%              │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 3. predict_time_to_fill()                                  │  │
│  │    "Quanto tempo até preencher esta vaga?"                  │  │
│  │    Baseado em histórico da empresa + benchmarks do setor    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 4. predict_offer_acceptance()                              │  │
│  │    "O candidato vai aceitar a oferta?"                      │  │
│  │    Baseado em pretensão salarial, fit, engajamento          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Onde são aplicados:                                             │
│  • Pipeline Kanban → Badges de risco por candidato               │
│  • Alertas Proativos → dropout_risk gera alertas automáticos     │
│  • Dashboard → Métricas preditivas no painel de analytics        │
│  • Decisões de IA → Agentes priorizam ações por probabilidade    │
└──────────────────────────────────────────────────────────────────┘
```

### 9.4 CompanyHiringPolicy — 5 Níveis de Autonomia

Cada empresa configura quanto de autonomia a LIA tem, desde "assistente passivo" até "piloto automático":

```
┌──────────────────────────────────────────────────────────────────┐
│       COMPANY HIRING POLICY — 5 NÍVEIS DE AUTONOMIA              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 1: ASSISTENTE (Padrão Inicial)                       │  │
│  │ • LIA só age quando perguntada                             │  │
│  │ • Toda decisão requer confirmação                          │  │
│  │ • Não monitora proativamente                               │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 2: RECOMENDADOR                                      │  │
│  │ • LIA sugere ações proativamente                           │  │
│  │ • Recrutador decide se executa                             │  │
│  │ • Alertas e notificações automáticas                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 3: SEMI-AUTÔNOMO                                     │  │
│  │ • Ações de baixo risco automáticas                         │  │
│  │ • Ações de médio/alto risco requerem aprovação             │  │
│  │ • Ex: triagem automática, mas rejeição requer confirmação  │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 4: AUTÔNOMO                                          │  │
│  │ • Maioria das ações automatizadas                          │  │
│  │ • Apenas decisões críticas requerem humano                 │  │
│  │ • Relatórios automáticos de tudo que foi feito             │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NÍVEL 5: PILOTO AUTOMÁTICO                                 │  │
│  │ • LIA gerencia o pipeline completo                         │  │
│  │ • Humano supervisiona e intervém quando quer               │  │
│  │ • Todas as ações documentadas e auditáveis                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Configuração: PolicyReActAgent (13 tools) guia o setup          │
│  → Onboarding de 19 perguntas adaptativas por setor              │
│  → Benchmarks por indústria (8 setores: tech, finance, retail,   │
│    healthcare, legal, education, manufacturing, services)        │
│  → Fontes: ABRH/GPTW (dados do mercado brasileiro)              │
│  → Calibrado por porte: Startup / PME / Corporação              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 10. Por Que Escolhemos Esta Arquitetura

### 10.1 Decisões de Design e Seus Trade-offs

```
┌──────────────────────────────────────────────────────────────────┐
│          DECISÕES ARQUITETURAIS — TRADE-OFFS                     │
│                                                                  │
│  DECISÃO 1: Domain-Driven em vez de Agent-First                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Domínios como fronteira, agentes subordinados  │  │
│  │ ALTERNATIVA: Agentes como entidade principal                │  │
│  │ POR QUÊ: Domínios são estáveis (sourcing sempre existe);  │  │
│  │ agentes mudam (legacy → ReAct → futuro). Domínios como     │  │
│  │ contratos de interface facilitam migração incremental.      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 2: Multi-LLM em vez de Single Provider                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Claude + Gemini + OpenAI, cada um para o       │  │
│  │ que faz melhor                                             │  │
│  │ ALTERNATIVA: Usar apenas um provedor para tudo              │  │
│  │ POR QUÊ: Reduz vendor lock-in, aproveita forças de cada   │  │
│  │ modelo, resilência se um ficar indisponível.                │  │
│  │ TRADE-OFF: Mais complexidade na abstração (LLMFactory)     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 3: CascadedRouter (3 camadas) em vez de LLM direto     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Cache → Regex → LLM (cascata progressiva)     │  │
│  │ ALTERNATIVA: Chamar LLM para toda classificação             │  │
│  │ POR QUÊ: ~80% dos requests resolvidos sem LLM ($0, <5ms). │  │
│  │ Economia massiva em tokens + latência.                      │  │
│  │ TRADE-OFF: Regex pode classificar errado; mitigado pela    │  │
│  │ camada 3 (LLM) como fallback.                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 4: ReAct Loop com max 5 iterações                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Limite rígido de 5 iterações + proteções       │  │
│  │ ALTERNATIVA: Loop livre até o agente decidir parar          │  │
│  │ POR QUÊ: LLMs podem entrar em loops, gerando custo         │  │
│  │ infinito. 5 iterações cobrem 99% dos casos de uso.         │  │
│  │ TRADE-OFF: Perguntas muito complexas podem ser truncadas;  │  │
│  │ mitigado por TaskPlanner (decompõe em sub-tarefas).        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 5: Duas engines de busca (Elasticsearch + pgvector)     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Full-text (BM25) + Vetorial (cosine) + WRF    │  │
│  │ ALTERNATIVA: Apenas Elasticsearch ou apenas vetorial        │  │
│  │ POR QUÊ: Texto garante match exato; vetorial garante       │  │
│  │ match semântico. Juntos, cobertura máxima.                  │  │
│  │ TRADE-OFF: Dois sistemas para manter e sincronizar;        │  │
│  │ mitigado pelo WRF que unifica os scores.                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 6: FairnessGuard em 3 camadas                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Regex → Implícito → LLM (cascata progressiva) │  │
│  │ ALTERNATIVA: Apenas LLM para todo viés                      │  │
│  │ POR QUÊ: Regex é determinístico (sem false negatives para  │  │
│  │ termos óbvios), rápido ($0), e pega a maioria dos casos.   │  │
│  │ LLM só é ativado para análise profunda.                     │  │
│  │ TRADE-OFF: Regex pode ter falsos positivos; mitigado        │  │
│  │ pela camada 2 que refina antes de escalar.                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  DECISÃO 7: Coexistência Legacy + ReAct com feature flag        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ESCOLHEMOS: Migração gradual com fallback automático       │  │
│  │ ALTERNATIVA: Big bang — migrar tudo de uma vez              │  │
│  │ POR QUÊ: Risco zero. Se ReAct falha, legacy assume.       │  │
│  │ Permite migrar domínio por domínio, validando cada um.     │  │
│  │ TRADE-OFF: Duas arquiteturas para manter durante           │  │
│  │ migração; custos de manutenção temporariamente maiores.     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 10.2 O Que É IA vs O Que É Determinístico

Uma decisão crucial é saber onde usar IA e onde usar código determinístico:

```
┌──────────────────────────────────────────────────────────────────┐
│          IA vs DETERMINÍSTICO — MAPA COMPLETO                    │
│                                                                  │
│  100% IA (LLM):                                                  │
│  ├─ Classificação de intent (o que o recrutador quer)            │
│  ├─ Geração de Job Description                                   │
│  ├─ Análise de CV e extração de dados                            │
│  ├─ WSI scoring qualitativo (blocos comportamentais)             │
│  ├─ Geração de perguntas de triagem                              │
│  ├─ Sugestões de competências e skills                           │
│  ├─ Análise de fit cultural                                       │
│  ├─ Geração de comunicações personalizadas                       │
│  ├─ Análise multimodal (vídeo, imagem, voz)                     │
│  └─ Predição de sub-status de pipeline                           │
│                                                                  │
│  HÍBRIDO (IA + Regras):                                          │
│  ├─ Roteamento: Cache → Regex → LLM (cascata)                  │
│  ├─ WSI quantitativo: LLM extrai → Algoritmo pontua             │
│  ├─ Busca: WRF (pesos determinísticos) + embeddings (IA)        │
│  ├─ Personalização: Estatísticas históricas + LLM ajusta        │
│  ├─ Automação: Triggers determinísticos + LLM prediz             │
│  └─ Cache semântico: Cosine similarity (math) + LLM (fallback)  │
│                                                                  │
│  100% DETERMINÍSTICO:                                            │
│  ├─ Autenticação e autorização (JWT + RBAC)                     │
│  ├─ FairnessGuard camada 1 (regex pattern matching)              │
│  ├─ FactChecker (validação numérica com ranges fixos)            │
│  ├─ Rate limiting e PolicyEngine (contadores + limites)          │
│  ├─ Retenção LGPD (dias fixos por tipo)                          │
│  ├─ Pipeline state machine (transições válidas hardcoded)        │
│  ├─ Multi-tenancy isolation (company_id filter)                  │
│  ├─ Token tracking e billing (contagem exata)                    │
│  └─ Feature flags (boolean per tenant)                           │
│                                                                  │
│  PRINCÍPIO: "IA onde precisa de inteligência;                    │
│  código onde precisa de garantia."                                │
│  Decisões de segurança e compliance são SEMPRE determinísticas.  │
└──────────────────────────────────────────────────────────────────┘
```

### 10.3 Resumo: Os Princípios da Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│         10 PRINCÍPIOS DA ARQUITETURA DE IA DA WEDOTALENT         │
│                                                                  │
│  1. DOMAIN-FIRST: Domínios definem fronteiras, agentes servem    │
│                                                                  │
│  2. BEST TOOL FOR THE JOB: Cada LLM usado para sua força        │
│                                                                  │
│  3. CASCATA ECONÔMICA: Sempre tente o mais barato primeiro       │
│     (cache → regex → LLM)                                       │
│                                                                  │
│  4. HUMAN-IN-THE-LOOP: IA sugere, humano decide em ações        │
│     com impacto externo                                          │
│                                                                  │
│  5. EXPLICABILIDADE: Toda decisão de IA é auditável              │
│     (raciocínio + dados + critérios registrados)                 │
│                                                                  │
│  6. FAIRNESS BY DESIGN: Anti-viés integrado em toda ação         │
│     (3 camadas + anti-sycophancy)                                │
│                                                                  │
│  7. MEMÓRIA EVOLUTIVA: IA aprende com resultados e               │
│     personaliza por empresa                                      │
│                                                                  │
│  8. MIGRAÇÃO SEGURA: Feature flags + fallback automático         │
│     (legacy → ReAct sem risco)                                   │
│                                                                  │
│  9. MULTI-TENANT ISOLATION: Dados e aprendizados isolados        │
│     por empresa (company_id em tudo)                             │
│                                                                  │
│  10. IA ONDE PRECISA, CÓDIGO ONDE GARANTE:                       │
│      Segurança e compliance são sempre determinísticos            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Apêndice: Glossário de Termos

| Termo | Significado |
|-------|-------------|
| **ReAct** | Reasoning + Acting — padrão de raciocínio dos agentes |
| **LLM** | Large Language Model — modelo de linguagem (Claude, GPT, Gemini) |
| **Tool** | Ferramenta que o agente pode chamar para executar ações |
| **WSI** | WeDoTalent Skill Index — metodologia de avaliação de candidatos |
| **WRF** | Weighted Ranking Framework — ranking ponderado de busca |
| **pgvector** | Extensão PostgreSQL para busca vetorial |
| **Embedding** | Representação vetorial de texto (768 dimensões) |
| **BM25** | Algoritmo de ranking textual do Elasticsearch |
| **FairnessGuard** | Sistema anti-viés em 3 camadas |
| **FactChecker** | Validador de veracidade pós-resposta |
| **LGPD** | Lei Geral de Proteção de Dados (brasileira) |
| **EU AI Act** | Regulamento europeu de IA |
| **CBI** | Competency-Based Interview — entrevista por competências |
| **OCEAN** | Big Five personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) |
| **Dreyfus** | Modelo de proficiência: Novice → Expert |
| **Bloom** | Taxonomia de profundidade cognitiva (6 níveis) |
| **DLQ** | Dead Letter Queue — fila de tarefas falhadas |
| **Multi-tenant** | Isolamento de dados por empresa (company_id) |
| **Feature Flag** | Chave liga/desliga para funcionalidades (per tenant) |
| **ReActConfig** | Configuração do loop ReAct por agente |
| **ToolDefinition** | Estrutura de registro de ferramenta ReAct |
| **AgentExecutionLog** | Registro de execução com cadeia de raciocínio |
| **CascadedRouter** | Roteador em 3 camadas (cache → regex → LLM) |
| **CompanyHiringPolicy** | Política de contratação configurável por empresa |
| **Anti-Sycophancy** | Guardrail contra concordância cega da IA |

---

*Documento gerado em 24/02/2026. Baseado em análise completa de 10.197 linhas de documentação técnica.*
