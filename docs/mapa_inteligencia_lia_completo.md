# Mapa Completo da Camada de Inteligência — Plataforma LIA

> Documento de referência para o time de desenvolvimento reproduzir a camada de inteligência da plataforma LIA no produto paralelo.
>
> Cada seção lista os arquivos-fonte que implementam aquela capacidade, com uma breve descrição do papel de cada um.
>
> **Base path:** `lia-agent-system/`
>
> **Última atualização:** 11/03/2026 — Verificado contra codebase real. Corrected: policy domain path, prompt architecture (YAML-only vs shared/prompts Python), agent_health_alert_service absent, added missing files in orchestrator/shared/agents/compliance.

---

## 1. Orquestrador Central

O "cérebro" que recebe inputs do frontend/API, classifica a intenção e decide qual agente ou fluxo invocar.

| Arquivo | Papel |
|---------|-------|
| `app/orchestrator/orchestrator.py` | Ponto de entrada principal — recebe a requisição, coordena agentes e retorna resposta |
| `app/orchestrator/intent_router.py` | Classificação de intenção (NLU) — decide qual domínio atende o pedido |
| `app/orchestrator/fast_router.py` | Router rápido para comandos simples que não precisam de LLM |
| `app/orchestrator/cascaded_router.py` | Router em cascata — tenta fast_router primeiro, depois LLM |
| `app/orchestrator/task_planner.py` | Decompõe tarefas complexas em subtarefas sequenciais |
| `app/orchestrator/policy_engine.py` | Aplica políticas de negócio e guardrails antes/depois da execução |
| `app/orchestrator/action_executor.py` | Executa ações decididas pelo orquestrador |
| `app/orchestrator/pending_action.py` | Gerencia ações pendentes que aguardam confirmação humana |
| `app/orchestrator/state_manager.py` | Gerencia estado da conversa entre turnos |
| `app/orchestrator/main_orchestrator.py` | MainOrchestrator — ponto de entrada de alto nível com ciclo de vida completo |
| `app/orchestrator/context_adapter.py` | Adaptação de contexto entre componentes do orquestrador |
| `app/orchestrator/memory_resolver.py` | Resolução de memória — carrega contexto relevante para o agente |
| `app/orchestrator/navigation_intent.py` | Grupos de intent de navegação: Configurações, Indicadores, WSI (Sprint J) |
| `app/orchestrator/llm_cascade.py` | Implementação da cascata LLM (Haiku→Sonnet→Opus) |
| `app/orchestrator/semantic_cache.py` | Cache semântico de intents (alias do vector_semantic_cache) |
| `app/orchestrator/vector_semantic_cache.py` | Cache semântico via pgvector cosine similarity |
| `app/orchestrator/tenant_budget.py` | Controle de budget de tokens por tenant |

---

## 2. Arquitetura de Agentes ReAct

Sistema de agentes baseado no padrão **ReAct (Reasoning + Acting)** — cada agente raciocina, escolhe uma ferramenta, observa o resultado e repete.

### 2.1 Infraestrutura Compartilhada

| Arquivo | Papel |
|---------|-------|
| `app/shared/agents/react_agent_registry.py` | Registry central — registra e instancia os 11 agentes de domínio |
| `app/shared/agents/agent_interface.py` | Interface base que todo agente implementa |
| `app/shared/agents/react_loop.py` | Loop ReAct genérico — raciocínio → ação → observação → repetir |
| `app/shared/agents/working_memory.py` | Memória de trabalho do agente durante uma execução |
| `app/shared/agents/enhanced_agent_mixin.py` | EnhancedAgentMixin — adiciona memória working/LTM + guardrails + learning a qualquer agente |
| `app/shared/agents/langgraph_react_base.py` | LangGraphReActBase — base para agentes ReAct com LangGraph prebuilt |
| `app/shared/agents/langgraph_base.py` | LangGraphBase — base genérica para grafos LangGraph stateful |
| `app/shared/agents/checkpointer.py` | Checkpointer — wrapper do PostgresSaver com isolamento por tenant |
| `app/shared/agents/agent_scaffold.py` | Scaffold para criação de novos agentes (template 4-file) |
| `app/shared/agents/autonomy_engine.py` | Engine de autonomia — decide quando agir proativamente |
| `app/shared/agents/confidence.py` | Estimativa de confiança das respostas do agente |
| `app/shared/agents/execution_log_store.py` | Store de logs de execução para debugging e auditoria |
| `app/shared/agents/learning_extractor.py` | Extrai aprendizados da interação para salvar no LTM |
| `app/shared/agents/long_term_memory.py` | Memória de longo prazo — insights de sessões anteriores do recrutador |
| `app/shared/agents/memory_integration.py` | Integração entre working memory e long-term memory |
| `app/shared/agents/nodes.py` | Nós compartilhados reutilizáveis entre múltiplos grafos |
| `app/shared/agents/observability.py` | Observabilidade dos agentes (métricas, traces, latência) |
| `app/shared/agents/base_state_machine.py` | State machine base para agentes com estados definidos |
| `app/shared/agents/state_machine.py` | State machine implementada para fluxos de agentes |
| `app/shared/agents/streaming_callback.py` | Callback de streaming (respostas token-a-token ao frontend) |
| `app/shared/agents/timed_tool_node.py` | Nó de tool com timeout configurável (evita hanging) |
| `app/shared/agents/agent_types.py` | Tipos e enums de agentes (AgentType, AgentStatus, etc.) |
| `app/shared/agents/sourcing_engagement_nodes.py` | Nós de engajamento específicos do sourcing |

### 2.2 Agentes de Domínio (13 no total)

Cada agente possui 4 arquivos padrão: `*_react_agent.py` (lógica), `*_system_prompt.py` (prompt de sistema), `*_tool_registry.py` (ferramentas disponíveis), `*_stage_context.py` (contexto por estágio).

#### Wizard (Criação de Vagas)
| Arquivo | Papel |
|---------|-------|
| `app/domains/job_management/agents/wizard_react_agent.py` | Agente que guia o recrutador na criação de vagas |
| `app/domains/job_management/agents/wizard_system_prompt.py` | Prompt de sistema do wizard |
| `app/domains/job_management/agents/wizard_tool_registry.py` | Ferramentas: criar vaga, sugerir requisitos, gerar descrição |
| `app/domains/job_management/agents/wizard_stage_context.py` | Contexto por etapa do wizard |
| `app/domains/job_management/agents/stage_context.py` | Contexto de estágio adicional |

#### Pipeline (Screening/Triagem)
| Arquivo | Papel |
|---------|-------|
| `app/domains/cv_screening/agents/pipeline_react_agent.py` | Agente de triagem e avaliação de candidatos |
| `app/domains/cv_screening/agents/pipeline_system_prompt.py` | Prompt de sistema do screening |
| `app/domains/cv_screening/agents/pipeline_tool_registry.py` | Ferramentas: avaliar CV, gerar perguntas, calcular score |
| `app/domains/cv_screening/agents/pipeline_stage_context.py` | Contexto por estágio do pipeline |

#### Sourcing (Busca de Candidatos)
| Arquivo | Papel |
|---------|-------|
| `app/domains/sourcing/agents/sourcing_react_agent.py` | Agente de sourcing ativo de candidatos |
| `app/domains/sourcing/agents/sourcing_system_prompt.py` | Prompt de sistema do sourcing |
| `app/domains/sourcing/agents/sourcing_tool_registry.py` | Ferramentas: buscar perfis, ranquear candidatos |
| `app/domains/sourcing/agents/sourcing_stage_context.py` | Contexto por estágio do sourcing |
| `app/domains/sourcing/agents/engagement_nodes.py` | Nós de engajamento para fluxos de sourcing |

#### Automation (Automação de Pipeline)
| Arquivo | Papel |
|---------|-------|
| `app/domains/automation/agents/automation_react_agent.py` | Agente de automação de tarefas recorrentes |
| `app/domains/automation/agents/automation_system_prompt.py` | Prompt de sistema da automação |
| `app/domains/automation/agents/automation_tool_registry.py` | Ferramentas: criar regras, agendar ações, disparar emails |
| `app/domains/automation/agents/automation_stage_context.py` | Contexto por estágio da automação |

#### Talent Assistant (Assistente de Talentos)
| Arquivo | Papel |
|---------|-------|
| `app/domains/recruiter_assistant/agents/talent_react_agent.py` | Assistente geral de recrutamento |
| `app/domains/recruiter_assistant/agents/talent_system_prompt.py` | Prompt de sistema do talent assistant |
| `app/domains/recruiter_assistant/agents/talent_tool_registry.py` | Ferramentas: consultar candidatos, gerar relatórios, sugerir ações |
| `app/domains/recruiter_assistant/agents/talent_stage_context.py` | Contexto por estágio |

#### Kanban Assistant (Assistente de Kanban)
| Arquivo | Papel |
|---------|-------|
| `app/domains/recruiter_assistant/agents/kanban_react_agent.py` | Assistente contextual do board Kanban |
| `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` | Prompt de sistema do Kanban |
| `app/domains/recruiter_assistant/agents/kanban_tool_registry.py` | Ferramentas: mover candidatos, filtrar, sugerir ações |
| `app/domains/recruiter_assistant/agents/kanban_stage_context.py` | Contexto por estágio do Kanban |

#### Jobs Management (Gestão de Vagas)
| Arquivo | Papel |
|---------|-------|
| `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | Agente de gestão operacional de vagas |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` | Prompt de sistema |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py` | Ferramentas: listar vagas, editar, clonar |
| `app/domains/recruiter_assistant/agents/jobs_mgmt_stage_context.py` | Contexto por estágio |

#### Policy Setup (Configuração de Políticas de Contratação)
| Arquivo | Papel |
|---------|-------|
| `app/domains/policy/agents/agent.py` | PolicySetupAgent — conduz o onboarding de 19 perguntas para configuração de CompanyHiringPolicy |
| `app/domains/policy/agents/system_prompt.py` | EXTRACTION_PROMPT e REPLY_PROMPT — extração de valores NL e geração de respostas em PT-BR |
| `app/domains/policy/agents/tool_registry.py` | `POLICY_TOOLS = []` — agente usa LLM diretamente, sem tools externas |
| `app/domains/policy/agents/stage_context.py` | QUESTIONS (19), BLOCK_NAMES (5 blocos), PolicySetupSession, get_or_create_session |
| `app/agents/policy_setup_agent.py` | Shim de retrocompatibilidade — re-exporta de `app/domains/policy/agents/` (I3c) |

#### Pipeline Transition (Transição de Estágio) — Invocação Direta
| Arquivo | Papel |
|---------|-------|
| `app/domains/pipeline/agents/pipeline_transition_agent.py` | Agente de transição entre estágios do pipeline (invocação direta, não via registry) |
| `app/domains/pipeline/agents/pipeline_system_prompt.py` | Prompt de sistema da transição |
| `app/domains/pipeline/agents/pipeline_tool_registry.py` | Ferramentas: mover candidato, validar transição |
| `app/domains/pipeline/agents/pipeline_stage_context.py` | Contexto por estágio |

#### Analytics (Análise e Insights)
| Arquivo | Papel |
|---------|-------|
| `app/domains/analytics/agents/analytics_react_agent.py` | Agente de analytics — gera insights sobre vagas, candidatos e pipeline |
| `app/domains/analytics/agents/analytics_system_prompt.py` | Prompt de sistema do analytics |
| `app/domains/analytics/agents/analytics_tool_registry.py` | Ferramentas: gerar relatórios, calcular métricas, exportar dados |
| `app/domains/analytics/agents/analytics_stage_context.py` | Contexto por estágio do analytics |

#### Communication (Comunicação Inteligente)
| Arquivo | Papel |
|---------|-------|
| `app/domains/communication/agents/communication_react_agent.py` | Agente de comunicação — gera e envia mensagens personalizadas |
| `app/domains/communication/agents/communication_system_prompt.py` | Prompt de sistema da comunicação |
| `app/domains/communication/agents/communication_tool_registry.py` | Ferramentas: enviar email, WhatsApp, gerar mensagem contextual |
| `app/domains/communication/agents/communication_stage_context.py` | Contexto por estágio da comunicação |

#### ATS Integration (Integração com ATS)
| Arquivo | Papel |
|---------|-------|
| `app/domains/ats_integration/agents/ats_integration_react_agent.py` | Agente de integração com sistemas ATS externos |
| `app/domains/ats_integration/agents/ats_integration_system_prompt.py` | Prompt de sistema da integração ATS |
| `app/domains/ats_integration/agents/ats_integration_tool_registry.py` | Ferramentas: sincronizar candidatos, importar vagas, exportar dados |
| `app/domains/ats_integration/agents/ats_integration_stage_context.py` | Contexto por estágio da integração |

#### Automation (Automação de Tarefas)
| Arquivo | Papel |
|---------|-------|
| `app/domains/automation/agents/automation_react_agent.py` | Agente de automação — cria e executa regras de automação |
| `app/domains/automation/agents/automation_system_prompt.py` | Prompt de sistema da automação |
| `app/domains/automation/agents/automation_tool_registry.py` | Ferramentas: criar regras, agendar ações, disparar comunicações |
| `app/domains/automation/agents/automation_stage_context.py` | Contexto por estágio da automação |

---

## 3. LangGraph — Grafos Stateful

Fluxos multi-etapa complexos implementados com LangGraph (máquinas de estado).

| Arquivo | Papel |
|---------|-------|
| `app/domains/job_management/agents/job_wizard_graph.py` | Grafo do wizard de criação de vagas — coleta dados passo-a-passo, valida e cria a vaga |
| `app/domains/job_management/agents/job_vacancy_nodes.py` | Nós (nodes) do grafo de vagas — cada nó é uma etapa do wizard |
| `app/domains/cv_screening/agents/wsi_interview_graph.py` | Grafo da entrevista WSI — conduz a entrevista simulada de trabalho em tempo real |
| `app/domains/interview_scheduling/agents/interview_graph.py` | Grafo de agendamento de entrevistas |
| `app/domains/interview_scheduling/agents/interview_scheduling_nodes.py` | Nós do grafo de agendamento |

---

## 4. WSI — Work Simulation Interview (Metodologia Proprietária)

Pipeline completo de avaliação de candidatos via entrevista simulada de trabalho.

| Arquivo | Papel |
|---------|-------|
| `app/domains/cv_screening/services/wsi_screening_pipeline.py` | Pipeline principal — orquestra todo o fluxo WSI |
| `app/domains/cv_screening/services/wsi_deterministic_scorer.py` | Scorer determinístico — cálculo do WSI score com regras fixas + IA |
| `app/domains/cv_screening/services/wsi_question_generator.py` | Gerador de perguntas WSI calibradas por taxonomia de Bloom |
| `app/domains/cv_screening/services/wsi_question_adjuster.py` | Ajuste dinâmico de dificuldade das perguntas durante a entrevista |
| `app/domains/cv_screening/services/wsi_question_service.py` | Serviço CRUD de perguntas WSI |
| `app/domains/cv_screening/services/wsi_service.py` | Serviço geral WSI — coordena triagens, resultados e histórico |
| `app/domains/cv_screening/services/wsi_voice_orchestrator.py` | Orquestrador de triagem por voz |
| `app/domains/cv_screening/services/rubric_evaluation_service.py` | Avaliação por rubrica — aplica critérios estruturados às respostas |
| `app/domains/cv_screening/services/evaluation_criteria_service.py` | Definição e gestão dos critérios de avaliação |
| `app/domains/cv_screening/services/calibration_profiles.py` | Perfis de calibração por senioridade e área |
| `app/domains/cv_screening/services/seniority_context_calibrator.py` | Calibração de contexto por nível de senioridade |
| `app/domains/cv_screening/services/seniority_resolver.py` | Resolução de senioridade a partir do perfil |
| `app/domains/cv_screening/services/seniority_utils.py` | Utilitários de senioridade |
| `app/domains/cv_screening/services/score_normalization_service.py` | Normalização de scores para comparabilidade |
| `app/domains/cv_screening/services/personalized_feedback_service.py` | Geração de feedback personalizado para candidatos |
| `app/domains/cv_screening/services/pre_qualification_service.py` | Pré-qualificação automática de candidatos |
| `app/domains/cv_screening/services/eligibility_verification_service.py` | Verificação de elegibilidade |
| `app/services/wsi_screening_pipeline.py` | Pipeline WSI no nível de serviço (legacy/wrapper) |

---

## 5. CV Screening — Triagem de Currículos

| Arquivo | Papel |
|---------|-------|
| `app/domains/cv_screening/services/cv_parser.py` | Parser de currículos — extrai dados estruturados de CVs |
| `app/domains/cv_screening/services/cv_scoring_service.py` | Scoring de CV — pontua o currículo vs. requisitos da vaga |
| `app/domains/cv_screening/services/cv_screening_batch_service.py` | Triagem em lote — processa múltiplos CVs de uma vez |
| `app/domains/cv_screening/services/screening_question_set_service.py` | Gerenciamento de conjuntos de perguntas de triagem |
| `app/services/screening_question_set_service.py` | Serviço de perguntas de triagem (nível serviço) |

---

## 6. Sourcing Inteligente — Busca e Avaliação de Candidatos

| Arquivo | Papel |
|---------|-------|
| `app/domains/sourcing/services/sourcing_pipeline.py` | Pipeline principal de sourcing |
| `app/domains/sourcing/services/candidate_search_route_service.py` | Roteamento de busca de candidatos |
| `app/domains/sourcing/services/vacancy_search.py` | Busca por vagas |
| `app/domains/sourcing/services/query_builders.py` | Construtores de queries de busca |
| `app/domains/sourcing/services/search_analytics.py` | Analytics de buscas de sourcing |
| `app/domains/sourcing/services/wrf_service.py` | Serviço WRF (Work Requirements Framework) |
| `app/domains/sourcing/services/pre_wrf_filter.py` | Filtro pré-WRF |
| `app/domains/sourcing/services/evaluation_criteria.py` | Critérios de avaliação de candidatos |
| `app/domains/sourcing/services/es_analyzer.py` | Análise via Elasticsearch |
| `app/domains/sourcing/services/pgv_analyzer.py` | Análise via pgvector |
| `app/domains/sourcing/services/pearch_service.py` | Serviço de busca (Pearch) |
| `app/domains/sourcing/services/apify_service.py` | Integração com Apify (web scraping) |
| `app/domains/sourcing/services/apify_mcp_client.py` | Cliente MCP para Apify |

---

## 7. Comunicação Inteligente

Geração de mensagens, inferência de comportamento e seleção de templates via IA.

| Arquivo | Papel |
|---------|-------|
| `app/domains/communication/services/communication_service.py` | Serviço principal de comunicação — orquestra envio e geração |
| `app/domains/communication/services/interpret_context_llm_service.py` | Interpretação de contexto via LLM — entende situação para gerar mensagem adequada |
| `app/domains/communication/services/infer_behavior_service.py` | Inferência de comportamento do candidato — ajusta tom e conteúdo |
| `app/domains/communication/services/email_templates_data.py` | Banco de templates de email com variáveis |
| `app/domains/communication/services/communication_dispatcher.py` | Dispatcher — decide e executa o envio por canal (email, WhatsApp, ambos) |
| `app/domains/communication/services/communication_history_service.py` | Histórico de comunicações por candidato |
| `app/domains/communication/services/transition_dispatch_service.py` | Dispatch automático de comunicação em transições de pipeline |
| `app/domains/communication/services/email_service.py` | Serviço de envio de email |
| `app/domains/communication/services/email_providers.py` | Abstração de provedores de email (módulo) |
| `app/domains/communication/services/email_providers/` | **Diretório** com providers concretos de email |
| `app/domains/communication/services/email_providers/base.py` | Interface base do provider de email |
| `app/domains/communication/services/email_providers/resend_provider.py` | Provider Resend |
| `app/domains/communication/services/email_providers/sendgrid_provider.py` | Provider SendGrid |
| `app/domains/communication/services/whatsapp_service.py` | Serviço de WhatsApp (modo simulado) |
| `app/domains/communication/services/whatsapp_factory.py` | Factory de provedores WhatsApp |
| `app/domains/communication/services/whatsapp_provider.py` | Provider base de WhatsApp |
| `app/domains/communication/services/whatsapp_meta_service.py` | Provider WhatsApp via Meta/Graph API |
| `app/domains/communication/services/whatsapp_twilio_service.py` | Provider WhatsApp via Twilio |
| `app/domains/communication/services/data_request_service.py` | Solicitação de dados ao candidato |
| `app/domains/communication/services/data_request_whatsapp_service.py` | Solicitação de dados via WhatsApp |
| `app/domains/communication/services/webhook_service.py` | Webhooks de comunicação |
| `app/domains/communication/services/return_event_service.py` | Serviço de eventos de retorno |

---

## 8. Prompts — Templates e Registry

Gestão centralizada de prompts. Arquitetura em duas camadas:
- **`app/shared/prompts/`** — implementações Python (loader, templates, registry, few-shot)
- **`app/prompts/`** — apenas arquivos YAML (persona, domínios) — NÃO contém Python

### 8.1 Implementações Python (app/shared/prompts/)

| Arquivo | Papel |
|---------|-------|
| `app/shared/prompts/loader.py` | PromptLoader — carrega YAMLs de `app/prompts/domains/` e `app/prompts/shared/` com cache in-memory |
| `app/shared/prompts/templates.py` | PromptTemplate, PromptLibrary, prompt_library singleton — registry com versionamento |
| `app/shared/prompts/cot.py` | ChainOfThoughtBuilder, CoTStrategy — geração de prompts com Chain-of-Thought |
| `app/shared/prompts/few_shot_examples.py` | FewShotExamples — exemplos gerais de classificação e extração |
| `app/shared/prompts/job_wizard.py` | Templates específicos do Job Wizard — register/get functions |
| `app/shared/prompts/agent_prompts.py` | System prompts compartilhados dos agentes ReAct |
| `app/shared/prompts/intent_few_shot_examples.py` | Exemplos few-shot para classificação de intenção do orquestrador |
| `app/shared/prompts/prompt_registry.py` | Registry de prompts — busca e injeta prompts por domínio/versão |
| `app/shared/prompts/examples/` | **Diretório** com exemplos por domínio |
| `app/shared/prompts/examples/orchestrator_examples.py` | Exemplos de intenção do orquestrador |
| `app/shared/prompts/examples/job_planner_examples.py` | Exemplos do planejador de vagas |
| `app/shared/prompts/examples/sourcing_examples.py` | Exemplos do agente de sourcing |
| `app/shared/prompts/examples/pipeline_examples.py` | Exemplos do pipeline de triagem |

### 8.2 YAMLs de Domínio (app/prompts/domains/ e app/prompts/shared/)

> **Nota:** `app/prompts/` contém APENAS arquivos YAML. Não há arquivos Python aqui.

| Arquivo | Papel |
|---------|-------|
| `app/prompts/shared/lia_persona.yaml` | Persona da LIA — tom, estilo, restrições (inegociáveis) |
| `app/prompts/shared/agent_prompts.yaml` | Prompts compartilhados entre agentes |
| `app/prompts/shared/defensive.yaml` | Prompts defensivos — tratamento de jailbreak, off-topic |
| `app/prompts/domains/cv_screening.yaml` | Prompts do domínio de triagem de CVs |
| `app/prompts/domains/job_management.yaml` | Prompts do domínio de gestão de vagas |
| `app/prompts/domains/sourcing.yaml` | Prompts do domínio de sourcing |
| `app/prompts/domains/communication.yaml` | Prompts do domínio de comunicação |
| `app/prompts/domains/automation.yaml` | Prompts do domínio de automação |
| `app/prompts/domains/interview_scheduling.yaml` | Prompts do domínio de agendamento |
| `app/prompts/domains/pipeline_transition.yaml` | Prompts do domínio de transição de pipeline |
| `app/prompts/domains/recruiter_assistant.yaml` | Prompts do domínio de assistente do recrutador |
| `app/prompts/domains/analytics.yaml` | Prompts do domínio de analytics |
| `app/prompts/domains/ats_integration.yaml` | Prompts do domínio de integração ATS |

---

## 9. Ferramentas (Tools) dos Agentes

Cada agente invoca ferramentas específicas. Definições centralizadas e por domínio.

| Arquivo | Papel |
|---------|-------|
| `app/tools/registry.py` | Registry global de ferramentas |
| `app/tools/scope_config.py` | Configuração de escopo — define quais tools cada agente pode acessar |
| `app/tools/executor.py` | Executor de ferramentas — invoca a tool e retorna resultado |
| `app/tools/candidate_tools.py` | Tools de candidatos: buscar, filtrar, atualizar |
| `app/tools/job_tools.py` | Tools de vagas: criar, editar, listar |
| `app/tools/job_wizard_tools.py` | Tools específicas do wizard de vagas |
| `app/tools/communication_tools.py` | Tools de comunicação: enviar email, WhatsApp, gerar mensagem |
| `app/tools/query_tools.py` | Tools de consulta: queries ao banco e APIs |
| `app/tools/export_tools.py` | Tools de exportação: relatórios, CSVs |
| `app/shared/tools/insight_tools.py` | Tools de insights: análise de dados, tendências |
| `app/shared/tools/predictive_tools.py` | Tools preditivas: previsão de sucesso, tempo de contratação |
| `app/shared/tools/proactive_tools.py` | Tools proativas: sugestões automáticas, alertas |
| `app/shared/tools/export_tools.py` | Tools de exportação compartilhadas |

---

## 10. Provedores LLM e Infraestrutura de IA

Interface com modelos de linguagem e serviços de embedding.

| Arquivo | Papel |
|---------|-------|
| `app/shared/providers/llm_factory.py` | Factory — instancia o provider correto (Claude, OpenAI, Gemini) |
| `app/shared/providers/llm_provider.py` | Interface base de provider LLM |
| `app/shared/providers/llm_client.py` | Cliente HTTP para chamadas LLM |
| `app/shared/providers/llm_claude.py` | Provider Anthropic Claude |
| `app/shared/providers/llm_openai.py` | Provider OpenAI (GPT-4, etc.) |
| `app/shared/providers/llm_gemini.py` | Provider Google Gemini |
| `app/shared/providers/ats_factory.py` | Factory de integração com sistemas ATS |
| `app/shared/providers/voice_provider.py` | Provider de voz (speech-to-text, text-to-speech) |
| `app/services/llm.py` | Serviço LLM de alto nível — abstração usada pelo resto do sistema (955 linhas) |
| `app/shared/intelligence/embedding_service.py` | Serviço de embeddings — vetorização de textos para busca semântica |
| `app/shared/intelligence/semantic_search_service.py` | Busca semântica sobre embeddings |
| `app/shared/intelligence/smart_extractor.py` | Extrator inteligente — extrai dados estruturados de texto livre via LLM |
| `app/shared/intelligence/param_patterns.py` | Padrões de parâmetros para extração |

---

## 11. Robustez e Guardrails

Camadas de proteção que garantem segurança e confiabilidade das respostas da IA.

| Arquivo | Papel |
|---------|-------|
| `app/shared/robustness/input_validation.py` | Validação de inputs — sanitização e limites |
| `app/shared/robustness/response_filter.py` | Filtro de respostas — remove conteúdo inadequado, PII, alucinações |
| `app/shared/robustness/defensive_prompts.py` | Prompts defensivos — proteção contra jailbreak e manipulação |
| `app/shared/robustness/error_handling.py` | Tratamento de erros — fallbacks e recuperação |
| `app/shared/robustness/context_management.py` | Gestão de contexto — controle de tamanho e relevância |
| `app/shared/robustness/enhanced_base.py` | Base aprimorada para agentes com guardrails |
| `app/shared/robustness/enhanced_registry.py` | Registry aprimorado com validações |
| `app/shared/robustness/intent_schemas.py` | Schemas de intenção para validação estruturada |
| `app/models/guardrail.py` | Guardrail SQLAlchemy model — guardrails editáveis por company_id, domain, node, is_active |
| `app/api/v1/guardrails.py` | API de guardrails — CRUD admin para ativar/desativar regras sem deploy |
| `alembic/versions/020_add_guardrails_table.py` | Migration: tabela `guardrails` |

---

## 12. HITL — Human-in-the-Loop Persistence

Sistema completo de aprovação humana para ações de alto risco dos agentes, com persistência em banco de dados para auditoria SOX/BCB-498.

| Arquivo | Papel |
|---------|-------|
| `app/services/hitl_service.py` | HITLService — Redis fast-path + PostgreSQL source-of-truth. `request_approval()`, `receive_approval()`, `store_resume_info()` |
| `app/models/hitl.py` | HITLPendingAction + HITLAuditTrail — modelos SQLAlchemy com company_id, domain, ws_session_id, expires_at |
| `app/api/v1/hitl.py` | `POST /api/v1/hitl/{thread_id}/approve` — endpoint de aprovação |
| `alembic/versions/032_add_hitl_tables.py` | Migration: tabelas `hitl_pending_actions` + `hitl_audit_trail` |
| `tests/unit/test_hitl_persistence.py` | 25 testes de persistência HITL |
| `plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx` | Componente FE — card de aprovação HITL no float chat |
| `plataforma-lia/src/hooks/use-float-streaming.ts` | Hook FE — gerencia streaming WebSocket + HITL interception |

**Integração HITL nos agentes:**
- `app/domains/job_management/agents/job_wizard_graph.py` — `interrupt_before=["stage_transition"]`
- `app/domains/cv_screening/agents/wsi_interview_graph.py` — `interrupt_before=["lg_generate_feedback"]`
- `app/domains/pipeline/agents/pipeline_transition_agent.py` — pre-check HITL antes de `_process_langgraph()`

---

## 13. Avaliação de Qualidade de Agentes

Avaliação automática de qualidade das respostas geradas pelos agentes, com persistência para análise de drift e compliance.

| Arquivo | Papel |
|---------|-------|
| `app/services/agent_quality_evaluator.py` | AgentQualityEvaluator — avalia task_completion, fairness, response_quality, latência |
| `app/services/agent_health_alert_service.py` | AgentHealthAlertService — ❌ NÃO EXISTE no codebase atual (a ser implementado) |
| `alembic/versions/034_add_agent_quality_evaluations.py` | Migration: tabela `agent_quality_evaluations` (agent_id, company_id, overall_score, scores JSONB) |

---

## 14. Preferências de Agente por Usuário

Sistema de auto-confirm que elimina confirmações repetitivas após a primeira aprovação.

| Arquivo | Papel |
|---------|-------|
| `app/services/user_agent_preference_service.py` | UserAgentPreferenceService — `get_preference()`, `set_preference()`, `should_auto_confirm()` |
| `app/models/user_agent_preference.py` | UserAgentPreference — modelo SQLAlchemy com user_id, company_id, domain, action_type, auto_confirm |
| `alembic/versions/035_add_user_agent_preferences.py` | Migration: tabela `user_agent_preferences` com UNIQUE(user_id, company_id, domain, action_type) |

---

## 15. Testes de Carga

Testes de performance e estabilidade para cenários de produção com alto volume.

| Arquivo | Papel |
|---------|-------|
| `tests/load/locustfile.py` | Locust — WizardUser, PipelineUser, HealthCheckUser com relatório p50/p95/p99 |
| `tests/load/load_test_config.py` | Configuração de carga — targets, thresholds, cenários por tipo de usuário |

---

## 16. Observabilidade e Governança de IA

Monitoramento, tracking de tokens e explicabilidade.

| Arquivo | Papel |
|---------|-------|
| `app/shared/governance/agent_monitoring_service.py` | Monitoramento de agentes — latência, erros, throughput |
| `app/shared/governance/feature_flag_service.py` | Feature flags para controle de funcionalidades de IA |
| `app/services/token_tracking_service.py` | Tracking de tokens — contabiliza uso por agente, modelo e tenant |
| `app/services/explainability_service.py` | Explicabilidade — gera justificativas legíveis para decisões da IA |
| `app/services/agent_monitoring_service.py` | Monitoramento de agentes (nível serviço) |
| `app/services/ai_cache_service.py` | Cache de respostas de IA — evita chamadas repetidas |
| `app/services/autonomous_agent_service.py` | Serviço de agentes autônomos — execução sem supervisão |
| `app/services/training_data_service.py` | Serviço de dados de treinamento — coleta dados para fine-tuning |
| `app/services/voice_screening_analysis.py` | Análise de screening por voz |
| `app/domains/analytics/services/wsi_observability.py` | Observabilidade específica do WSI |

---

## 16B. Compliance — Arquivos Adicionais (app/shared/compliance/)

Módulos de auditoria e verificação encontrados no codebase mas não documentados anteriormente.

| Arquivo | Papel |
|---------|-------|
| `app/shared/compliance/audit_callback.py` | AuditCallback — callback LangGraph que registra cada decisão de agente para auditoria SOX/BCB-498 |
| `app/shared/compliance/audit_writer.py` | AuditWriter — persiste logs de auditoria no banco (PostgreSQL) |
| `app/shared/compliance/audit_storage.py` | AuditStorage — interface de armazenamento (abstrai backend de auditoria) |
| `app/shared/compliance/audit_models.py` | Modelos de dados dos eventos de auditoria (schemas Pydantic + SQLAlchemy) |
| `app/shared/compliance/fact_checker.py` | FactChecker — verifica consistência e veracidade de claims do agente |

---

## 17. Analytics e Insights com IA

Geração de relatórios, insights preditivos e análises via IA.

| Arquivo | Papel |
|---------|-------|
| `app/domains/analytics/services/job_analytics_prompt_service.py` | Prompts para analytics de vagas via LLM |
| `app/domains/analytics/services/job_insights_service.py` | Insights inteligentes sobre vagas |
| `app/domains/analytics/services/predictive_analytics_service.py` | Analytics preditivo — previsões de tempo de contratação, sucesso |
| `app/domains/analytics/services/job_report_service.py` | Geração de relatórios de vagas |
| `app/domains/analytics/services/candidate_report_service.py` | Geração de relatórios de candidatos |
| `app/domains/analytics/services/report_service.py` | Serviço geral de relatórios |
| `app/domains/analytics/services/search_analytics_service.py` | Analytics de buscas |
| `app/domains/analytics/services/wizard_analytics_service.py` | Analytics do wizard de criação |
| `app/domains/analytics/services/agent_monitoring_service.py` | Monitoramento de agentes (nível analytics) |

---

## 18. Intelligence Layer e Machine Learning

Serviços de inteligência de alto nível, predição de resultados e engenharia de features.

| Arquivo | Papel |
|---------|-------|
| `app/services/intelligence_layer_service.py` | Serviço central da camada de inteligência — readiness checks, predições e orquestração de ML |
| `app/services/ml/feature_engineering.py` | Engenharia de features — extrai e transforma variáveis para modelos preditivos |
| `app/services/ml/outcome_predictor.py` | Preditor de resultados — prevê sucesso de contratação, tempo de preenchimento |
| `app/services/ml/model_registry.py` | Registry de modelos ML — versionamento e seleção de modelos |
| `app/shared/agents/proactive_worker.py` | Worker proativo — executa verificações automáticas e gera sugestões sem intervenção do usuário |

---

## 19. Configuração e Infraestrutura Base

| Arquivo | Papel |
|---------|-------|
| `app/core/config.py` | Configuração central — chaves de API, modelos padrão, limites |
| `app/core/database.py` | Conexão com banco de dados |
| `app/core/logging_config.py` | Configuração de logs com PII masking |
| `app/core/taxonomy.py` | Taxonomia de categorias (skills, áreas, senioridades) |
| `app/core/template_channels.py` | Mapeamento de canais de comunicação por template |
| `app/services/email_service.py` | Serviço de email (nível serviço) |
| `app/services/email_providers.py` | Provedores de email (nível serviço) |
| `app/services/recruitment_email_templates.py` | Templates de email de recrutamento |

---

## 20. Documentação de Referência (verificada no codebase)

Documentos que EXISTEM em `lia-agent-system/docs/`:

| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| `docs/GUIA_ARQUITETURA_IA_v1.0.md` | — | Guia definitivo de arquitetura de IA — visão geral, decisões, padrões |
| `docs/ai-architecture-audit.md` | ~516 KB | Auditoria completa da arquitetura de IA (documento extenso) |
| `docs/MAPA_CAMADA_INTELIGENCIA.md` | ~329 KB | Mapa detalhado da camada de inteligência |
| `docs/CONCEITOS_IA_WEDOTALENT.md` | ~180 KB | Conceitos fundamentais da plataforma de IA |
| `docs/PLANO_CICLO_FECHADO_LIA.md` | — | Plano de ciclo fechado da LIA |
| `docs/fase2c_domain_verification_report.md` | — | Relatório de verificação dos domínios (fase 2C) |
| `docs/WSI_METHODOLOGY_REFERENCE.md` | — | Referência da metodologia WSI |

> **Nota:** Documentos listados em versões anteriores deste mapa que NÃO existem no filesystem:
> `WSI_Technical_Documentation.md`, `LIA_METHODOLOGY.md`, `LIA_UNIFIED_METHODOLOGY.md`,
> `ARQUITETURA_JOB_WIZARD.md`, `LIA_AUTOMATION_SYSTEM.md`, `LLM_COMPARISON_TRAINING.md`,
> `DIAGNOSTICO_PROMPTS_PLATAFORMA.md`, `NLP_CLUSTERING_STRATEGIC_ANALYSIS.md`

---

## Resumo Quantitativo

> Atualizado em 11/03/2026 — verificado contra codebase real (Sprints A–J concluídos).

| Dimensão | Quantidade |
|----------|-----------|
| Agentes ReAct | **13** (11 via registry + PipelineTransitionAgent invocação direta + PolicySetupAgent LLM direto) |
| Grafos LangGraph | **3** (job_wizard_graph, wsi_interview_graph, interview_graph) |
| Provedores LLM | 3 (Claude primário, OpenAI fallback, Gemini fallback + embeddings) |
| Domínios DDD | **12** (inclui `policy` adicionado no Sprint I3c; `hiring_policy` removido) |
| YAMLs de domínio | **13 arquivos** (`app/prompts/domains/` × 10 + `app/prompts/shared/` × 3) |
| Implementações Python prompts | **9 arquivos** em `app/shared/prompts/` (+ diretório `examples/` com 4 arquivos) |
| Tools registradas (YAML) | 32 (`tool_registry_metadata.yaml`) + code-driven |
| Serviços WSI | 18 arquivos (~9.621 linhas) |
| Serviços de sourcing | 13 arquivos |
| Serviços de comunicação | 23 arquivos (incl. providers) |
| Serviços de ML/Predição | 4 arquivos |
| Migrations Alembic | **35** (última: 035_add_user_agent_preferences) |
| Testes BE coletados | **3.712+** |
| Cobertura BE | **32,66%** (gate CI: 32%) |
| Arquivos na camada de inteligência | **~185 arquivos** (atualizado com novos arquivos encontrados) |

---

## Como Usar Este Mapa

1. **Para reproduzir um agente:** Comece pelo `react_agent_registry.py` para ver como o agente é registrado, depois leia o `*_react_agent.py` do domínio correspondente + seu `*_system_prompt.py` + `*_tool_registry.py`.

2. **Para reproduzir o WSI:** Comece pelo `wsi_screening_pipeline.py` (pipeline principal), depois o `wsi_interview_graph.py` (LangGraph), depois os serviços de scoring (`wsi_deterministic_scorer.py`) e geração de perguntas (`wsi_question_generator.py`).

3. **Para reproduzir a comunicação inteligente:** Comece pelo `communication_service.py`, depois `interpret_context_llm_service.py` e `infer_behavior_service.py`.

4. **Para reproduzir o orquestrador:** Comece pelo `orchestrator.py`, depois `intent_router.py` → `cascaded_router.py` → `task_planner.py`.

5. **Para entender os prompts:** Comece pelo `lia_persona.yaml` (persona base), depois os YAMLs de domínio em `app/prompts/domains/`.

---

## Nota de Precisão

> Este mapa foi verificado contra o codebase real em 11/03/2026.
> Paths e arquivos confirmados via filesystem — não são estimativas documentais.
>
> **Fonte de verdade:** sempre o código em `lia-agent-system/app/` — este mapa é um índice de navegação.
> Se encontrar discrepância entre este mapa e o código, o código prevalece.
>
> **Documento relacionado:** `docs/diagnostico-agentes-mvp.md` — diagnóstico completo com gap analysis, cards Jira, NFRs e roteiros de reprodução.
