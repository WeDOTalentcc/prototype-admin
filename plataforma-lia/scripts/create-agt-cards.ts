const PROJECT_KEY = 'WT';

interface AGTCard {
  id: string;
  summary: string;
  description: string;
  priority: string;
  labels: string[];
  storyPoints: number;
  sprint: string;
}

const AGT_CARDS: AGTCard[] = [
  {
    id: 'AGT-001',
    summary: '[AI/ARCH] MainOrchestrator — Roteamento 3-Tier + HITL + PendingActions (Ag.0)',
    description: `**Componente:** MainOrchestrator (Ag.0 — Orquestrador Central)
**Tipo:** Orchestrator LangGraph
**Sprint:** S0 (Infra Base) | **Prioridade:** P0
**Referência Alpha 1:** Todos os passos — coordena fluxo completo

---

## Objetivo
Implementar o orquestrador central que recebe requisições e roteia para os agentes especializados usando cascata de 3 tiers, gerencia estados pendentes (PendingActions) e implementa HITL (Human-in-the-Loop) para decisões de Gate.

## Escopo Detalhado

### 1. Roteamento 3-Tier (cascata)
- **Tier 1 — Fast Match:** Pattern matching por keywords/regex para domínios conhecidos (sourcing, triagem, agendamento, comunicação)
- **Tier 2 — LLM Cascade:** Classificação por LLM (Gemini Flash) quando fast match não resolve
- **Tier 3 — Clarification:** Pedir esclarecimento ao usuário quando nem LLM resolve
- Cache de roteamento (memory → Redis → vector) para performance

### 2. PendingActions (multi-turn)
- Fila de ações pendentes por sessão (ex: "candidato passou Gate 1, aguardando email de triagem")
- Estado persistente em Redis com TTL configurável
- Resume automático quando dependência é satisfeita

### 3. HITL (Human-in-the-Loop)
- Interrupt_before em nós de decisão (Gate 1 aprovação, Gate 2 shortlist)
- Notificação ao consultor via Teams/email quando HITL necessário
- Timeout configurável (default 24h) com escalação

### 4. Registry de Agentes
- Registro dinâmico de agentes disponíveis (SourcingReAct, CVScreening, WSIInterview, Scheduling, Communication)
- Health check periódico dos agentes
- Fallback graceful se agente indisponível

## Código Base Existente (LIA)
- \`lia-agent-system/app/orchestrator/main_orchestrator.py\` — MainOrchestrator atual (11+ domínios)
- \`lia-agent-system/app/orchestrator/cascaded_router.py\` — CascadedRouter 6 tiers (memory→redis→vector→fast→LLM→clarification)
- \`lia-agent-system/app/orchestrator/pending_actions.py\` — PendingActions manager

## Código Base Existente (V5)
- \`src/domains/orchestrator.py\` — DomainOrchestrator (2 domínios, básico)
- \`src/domains/registry.py\` — DomainRegistry singleton

## Artefatos a Produzir
1. \`orchestrator/alpha1_orchestrator.py\` — Orchestrator configurado para 9 agentes Alpha 1
2. \`orchestrator/alpha1_router.py\` — Router 3-Tier customizado
3. \`orchestrator/pending_actions_alpha1.py\` — PendingActions com regras Alpha 1
4. Testes unitários (>80% coverage)

## Critérios de Aceitação
- [ ] Roteia corretamente para todos os 9 agentes Alpha 1
- [ ] Fast match resolve >70% das requisições sem LLM
- [ ] PendingActions persiste em Redis e resume corretamente
- [ ] HITL interrompe em Gates e notifica consultor
- [ ] Fallback graceful quando agente está indisponível
- [ ] AuditCallback registra todas as decisões de roteamento
- [ ] Latência de roteamento <200ms (Tier 1), <2s (Tier 2)

## Dependências
- AGT-002 (Infraestrutura compartilhada — BaseAgent, AuditCallback)
- Redis configurado
- Gemini Flash API key (para Tier 2)

## Estimativa: 13 Story Points`,
    priority: 'Highest',
    labels: ['ai-agent', 'orchestrator', 'alpha1', 'sprint-0', 'P0'],
    storyPoints: 13,
    sprint: 'S0'
  },
  {
    id: 'AGT-002',
    summary: '[AI/INFRA] Infraestrutura Compartilhada — BaseAgent + AuditCallback + FairnessGuard + PII',
    description: `**Componente:** Infraestrutura Compartilhada (libs/agents-core)
**Tipo:** Biblioteca/Framework
**Sprint:** S0 (Infra Base) | **Prioridade:** P0
**Referência Alpha 1:** Transversal — usado por todos os agentes

---

## Objetivo
Criar a camada de infraestrutura compartilhada que todos os agentes Alpha 1 utilizam: BaseAgent (scaffold), AuditCallback, FairnessGuard 3 camadas, PII Masking e Token Budget Manager.

## Escopo Detalhado

### 1. BaseAgent (Scaffold Padronizado)
- Padrão 4-file: \`_react_agent.py\`, \`_tool_registry.py\`, \`_system_prompt.py\`, \`_stage_context.py\`
- Lifecycle hooks: on_start, on_tool_call, on_response, on_error, on_complete
- Integração automática com AuditCallback e FairnessGuard
- Context window management (token budget)

### 2. AuditCallback (Rastreabilidade)
- Log estruturado de todas as decisões de agentes (JSON)
- Campos: timestamp, agent_id, session_id, action, input_hash, output_hash, latency_ms, model_used, tokens_used
- Persistência em PostgreSQL (tabela audit_log)
- Compliance: rastreabilidade de decisões de IA conforme Guia v3.3

### 3. FairnessGuard (3 Camadas)
- **Camada 1 — Pre-prompt:** Instruções de imparcialidade injetadas no system prompt
- **Camada 2 — Post-response:** Validação de output para viés (gênero, idade, etnia, deficiência)
- **Camada 3 — Aggregate:** Métricas de fairness acumuladas por vaga (demographic parity, equal opportunity)
- Dashboard de métricas de fairness (endpoint API)

### 4. PII Masking
- Detecção de PII em inputs/outputs (CPF, email, telefone, endereço)
- Masking automático antes de enviar para LLM
- Unmasking controlado no retorno
- Compliance LGPD

### 5. Token Budget Manager
- Controle de tokens por requisição e por sessão
- Alertas quando >80% do budget consumido
- Fallback para modelo menor quando budget excedido

## Código Base Existente (LIA)
- \`lia-agent-system/app/shared/agents/agent_scaffold.py\` — BaseAgent scaffold
- \`lia-agent-system/app/shared/agents/fairness_guard.py\` — FairnessGuard 3 camadas
- \`lia-agent-system/app/shared/services/pii_masking_service.py\` — PII masking

## Código Base Existente (V5)
- \`src/domains/sourced_profile_sourcing/fairness.py\` — FairnessGuard básico (1 camada)

## Artefatos a Produzir
1. \`shared/agents/base_agent.py\` — BaseAgent com lifecycle hooks
2. \`shared/agents/audit_callback.py\` — AuditCallback logger
3. \`shared/agents/fairness_guard.py\` — FairnessGuard 3 camadas (evoluir existente)
4. \`shared/services/pii_masking.py\` — PII Masking LGPD (evoluir existente)
5. \`shared/services/token_budget.py\` — Token Budget Manager
6. Migration SQL para tabela audit_log
7. Testes unitários (>90% coverage para fairness e PII)

## Critérios de Aceitação
- [ ] BaseAgent scaffold gera corretamente os 4 arquivos por agente
- [ ] AuditCallback registra todas as decisões com <5ms overhead
- [ ] FairnessGuard bloqueia outputs com viés detectado (accuracy >95%)
- [ ] PII Masking detecta e mascara CPF, email, telefone, endereço
- [ ] Token Budget alerta e faz fallback corretamente
- [ ] Todos os componentes têm testes unitários

## Dependências
- PostgreSQL (para audit_log)
- Redis (para token budget counters)

## Estimativa: 21 Story Points`,
    priority: 'Highest',
    labels: ['ai-agent', 'infra', 'alpha1', 'sprint-0', 'P0', 'fairness', 'lgpd'],
    storyPoints: 21,
    sprint: 'S0'
  },
  {
    id: 'AGT-003',
    summary: '[AI/INTEG] ATSIntegrationService — Importação de Vagas + Sync Bidirecional (Ag.8)',
    description: `**Componente:** ATSIntegrationService (Ag.8 — Integração ATS)
**Tipo:** Serviço de Integração
**Sprint:** S0 (Infra Base) | **Prioridade:** P0
**Referência Alpha 1:** Premissa — vagas importadas do ATS do cliente

---

## Objetivo
Implementar serviço de integração bidirecional com ATSs do mercado (Gupy, Pandapé, Merge.dev) para importar vagas e exportar status/scores de candidatos. Premissa do Alpha 1: vagas já existem no ATS e são importadas.

## Escopo Detalhado

### 1. Importação de Vagas (ATS → WeDo)
- Endpoint: \`POST /api/ats/sync/vacancies\`
- Mapeamento de campos: título, descrição, requisitos, localização, modelo trabalho, faixa salarial
- Normalização de dados (diferentes formatos por ATS)
- Deduplicação (mesma vaga não importada 2x)
- Webhook para sync automático quando vaga criada/atualizada no ATS

### 2. Exportação de Status (WeDo → ATS)
- Endpoint: \`POST /api/ats/sync/candidates/{id}/status\`
- Campos: status pipeline (Gate 1/Gate 2/Aprovado/Rejeitado), scores WSI, feedback
- Write-back automático quando status muda no WeDo
- Retry com exponential backoff para falhas de API

### 3. Clientes ATS Suportados
- **Gupy:** API REST v2 (autenticação OAuth2)
- **Pandapé:** API REST (autenticação API Key)
- **Merge.dev:** API unificada (proxy para múltiplos ATSs)

### 4. Mapeamento de Campos
- Tabela de mapeamento configurável por cliente (JSON/YAML)
- Campos obrigatórios: título, descrição, localização
- Campos opcionais: skills, experiência, faixa salarial, modelo trabalho

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/ats_integration/services/ats_sync_service.py\` — Sync service
- \`lia-agent-system/app/domains/ats_integration/services/gupy_service.py\` — Cliente Gupy
- \`lia-agent-system/app/domains/ats_integration/services/pandape_service.py\` — Cliente Pandapé
- \`lia-agent-system/app/domains/ats_integration/services/merge_ats_service.py\` — Cliente Merge

## Código Base Existente (V5)
- \`src/documentation/\` — 67+ YAMLs de endpoints API ATS
- \`src/tools/\` — ToolRegistry com SourcingAPIClient

## Artefatos a Produzir
1. \`services/ats_integration/ats_service.py\` — Serviço principal (evoluir existente)
2. \`services/ats_integration/clients/gupy.py\` — Cliente Gupy (evoluir existente)
3. \`services/ats_integration/clients/pandape.py\` — Cliente Pandapé (evoluir existente)
4. \`services/ats_integration/clients/merge.py\` — Cliente Merge.dev (evoluir existente)
5. \`services/ats_integration/field_mapping.py\` — Mapeamento configurável
6. \`services/ats_integration/webhook_handler.py\` — Handler de webhooks
7. Testes de integração com mocks por ATS

## Critérios de Aceitação
- [ ] Importa vagas de pelo menos 1 ATS (Gupy ou Merge)
- [ ] Deduplicação funciona (mesma vaga não importada 2x)
- [ ] Exporta status/scores de candidatos de volta ao ATS
- [ ] Mapeamento de campos configurável por ATS
- [ ] Retry com exponential backoff para falhas de API
- [ ] Webhook recebe notificações de criação/atualização de vaga
- [ ] AuditCallback registra todas as operações de sync

## Dependências
- Credenciais de API do ATS (Gupy/Pandapé/Merge)
- AGT-002 (AuditCallback)

## Estimativa: 8 Story Points`,
    priority: 'Highest',
    labels: ['ai-agent', 'integration', 'ats', 'alpha1', 'sprint-0', 'P0'],
    storyPoints: 8,
    sprint: 'S0'
  },
  {
    id: 'AGT-004',
    summary: '[AI/AGENT] SourcingReActAgent — Busca Semântica ES+PGV+WRF+Pearch (Ag.2)',
    description: `**Componente:** SourcingReActAgent (Ag.2 — Sourcing Inteligente)
**Tipo:** Agente ReAct (LangGraph)
**Sprint:** S1 (Busca + Comunicação) | **Prioridade:** P0
**Referência Alpha 1:** Passo 4 — sourcing de candidatos para vaga publicada

---

## Objetivo
Implementar agente ReAct de sourcing que busca candidatos usando busca híbrida (Elasticsearch + PGVector + WRF) com enriquecimento via Pearch/Apify e feedback loop (Like/Dislike).

## Escopo Detalhado

### 1. Busca Híbrida (ES + PGVector + WRF)
- **Elasticsearch:** Busca textual com score drop detection (\`es_analyzer.py\`)
- **PGVector:** Busca semântica por embeddings com gap analyzer (\`pgv_analyzer.py\`)
- **WRF (Weighted Rank Fusion):** Fusão ponderada de scores ES + PGV (\`wrf_service.py\`)
- **Dynamic K:** Ajuste automático de K baseado no nível da vaga (\`wrf_service.py\`)
- **Pre-WRF Filter:** Filtragem prévia para performance (\`pre_wrf_filter.py\`)

### 2. Modos de Busca (5 modos)
- **IA (semântica):** Busca por embedding da descrição da vaga
- **Boolean:** Query booleana construída pelo SmartExtractor
- **Similar:** Busca por candidato de referência
- **JD Match:** Matching direto contra job description
- **Archetypes:** Busca por arquétipos de candidato ideais

### 3. Tools do Agente ReAct
- \`search_candidates\` — Busca híbrida ES+PGV+WRF
- \`enrich_candidate\` — Enriquecimento via Pearch/Apify
- \`get_candidate_details\` — Detalhes completos do candidato
- \`score_candidate_match\` — Score de matching candidato×vaga
- \`save_feedback\` — Like/Dislike para learning loop

### 4. Enriquecimento Externo
- **Pearch AI:** Busca de perfis profissionais (\`pearch_service.py\` existente)
- **Apify:** Scraping LinkedIn/Glassdoor para dados de empresa (\`apify_service.py\` existente)

### 5. Learning Loop (Like/Dislike)
- Feedback do recrutador incorporado nos scores futuros
- Ajuste de pesos WRF baseado no histórico de feedback
- Métricas de qualidade de busca por vaga

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/sourcing/services/wrf_service.py\` — WRF Dynamic K
- \`lia-agent-system/app/domains/sourcing/services/pre_wrf_filter.py\` — Pre-WRF Filter
- \`lia-agent-system/app/domains/sourcing/services/es_analyzer.py\` — ES Score Drop
- \`lia-agent-system/app/domains/sourcing/services/pgv_analyzer.py\` — PGV Gap Analyzer
- \`lia-agent-system/app/domains/sourcing/services/pearch_service.py\` — Pearch AI
- \`lia-agent-system/app/domains/sourcing/services/apify_service.py\` — Apify
- \`lia-agent-system/app/domains/sourcing/services/apify_mcp_client.py\` — Apify MCP

## Código Base Existente (V5)
- \`src/domains/sourced_profile_sourcing/agents/\` — 6 sub-agentes (search, detail, comparison, analytics, report, action)
- \`src/domains/sourced_profile_sourcing/smart_extractor.py\` — SmartExtractor (NL→params)
- \`src/domains/sourced_profile_sourcing/fairness.py\` — FairnessGuard

## Artefatos a Produzir
1. \`domains/sourcing/agents/sourcing_react_agent.py\` — Agente ReAct principal
2. \`domains/sourcing/agents/sourcing_tool_registry.py\` — Tools do agente
3. \`domains/sourcing/agents/sourcing_system_prompt.py\` — System prompt
4. \`domains/sourcing/agents/sourcing_stage_context.py\` — Stage context
5. Integração operacional dos serviços WRF/ES/PGV/Pearch/Apify existentes
6. Testes de integração com dados mock

## Critérios de Aceitação
- [ ] Busca híbrida retorna candidatos rankeados por WRF score
- [ ] Pelo menos 3 dos 5 modos de busca funcionam (IA, Boolean, JD Match)
- [ ] SmartExtractor converte linguagem natural em parâmetros de busca
- [ ] Pearch/Apify enriquecem perfis (quando APIs configuradas)
- [ ] Like/Dislike salva feedback e influencia scores futuros
- [ ] FairnessGuard valida que resultados não têm viés
- [ ] AuditCallback registra todas as buscas e decisões

## Dependências
- AGT-001 (Orchestrator para roteamento)
- AGT-002 (BaseAgent, FairnessGuard, AuditCallback)
- Elasticsearch configurado
- PGVector habilitado no PostgreSQL

## Estimativa: 13 Story Points`,
    priority: 'Highest',
    labels: ['ai-agent', 'sourcing', 'search', 'alpha1', 'sprint-1', 'P0'],
    storyPoints: 13,
    sprint: 'S1'
  },
  {
    id: 'AGT-005',
    summary: '[AI/COMM] CommunicationService + Email/Teams Adapters (Ag.7)',
    description: `**Componente:** CommunicationService + Adapters (Ag.7 — Comunicação Multi-Canal)
**Tipo:** Serviço + Adapters
**Sprint:** S1 (Busca + Comunicação) | **Prioridade:** P0
**Referência Alpha 1:** Passos 5, 6, 6B, 9 — contato inicial, follow-up, notificações

---

## Objetivo
Implementar serviço de comunicação multi-canal com adapters para Email (canal primário Alpha 1), Teams (notificações ao consultor) e WhatsApp (secundário). Inclui templates de mensagem, rastreamento de envio e CommunicationMatrix para decisão de canal.

## Escopo Detalhado

### 1. CommunicationService (Core)
- Endpoint: \`POST /api/communication/send\`
- Canal selection via CommunicationMatrix (regras por evento)
- Queue de envio com prioridade (urgente, normal, batch)
- Retry com exponential backoff
- Deduplicação (mesmo candidato + mesmo template + janela temporal)

### 2. Email Adapter (Canal Primário)
- Integração com provedor SMTP/SES/SendGrid
- Templates HTML responsivos para:
  - Contato inicial (convite para triagem)
  - Follow-up (lembrete 24h — até 7 envios em 7 dias)
  - Resultado Gate 1 (aprovação → link chat web)
  - Resultado Gate 2 (aprovação + agendamento de entrevista)
  - Feedback de rejeição (diferenciado por Gate)
- Personalização: nome candidato, nome vaga, nome empresa
- Tracking de abertura e clique (pixel + link redirect)

### 3. Teams Adapter (Notificações Internas)
- Notificações ao consultor via Microsoft Teams Webhooks
- Eventos: candidato sem resposta 48h, Gate 1 pendente HITL, agenda não encontrada
- Cards adaptivos do Teams com botões de ação

### 4. CommunicationMatrix
- Tabela de decisão: evento × canal × template × timing
- Configurável por vaga (override de defaults)
- Trigger \`triagem_abandonada\` (48h timeout)

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/communication/models/communication_matrix.py\` — CommunicationMatrix com trigger triagem_abandonada
- \`lia-agent-system/app/domains/communication/models/email_template.py\` — Email templates
- \`lia-agent-system/app/domains/communication/adapters/teams_adapter.py\` — Teams adapter
- \`lia-agent-system/app/domains/communication/models/teams.py\` — Teams model

## Artefatos a Produzir
1. \`services/communication/communication_service.py\` — Serviço principal
2. \`services/communication/adapters/email_adapter.py\` — Email adapter (SMTP/SES)
3. \`services/communication/adapters/teams_adapter.py\` — Teams adapter (evoluir)
4. \`services/communication/templates/\` — Templates HTML de email
5. \`services/communication/communication_matrix.py\` — Matrix de decisão (evoluir)
6. \`services/communication/tracking/email_tracker.py\` — Tracking abertura/clique
7. Testes unitários + integration tests

## Critérios de Aceitação
- [ ] Envia email de contato inicial com template personalizado
- [ ] CommunicationMatrix seleciona canal correto por evento
- [ ] Follow-up re-envia email a cada 24h (máx 7 dias)
- [ ] Tracking de abertura registra quando candidato abre email
- [ ] Teams adapter envia notificação ao consultor
- [ ] Deduplicação impede envio duplicado na mesma janela
- [ ] AuditCallback registra todos os envios

## Dependências
- AGT-002 (AuditCallback, BaseAgent)
- Credenciais SMTP/SES ou SendGrid
- Teams Webhook URL

## Estimativa: 13 Story Points`,
    priority: 'Highest',
    labels: ['ai-agent', 'communication', 'email', 'alpha1', 'sprint-1', 'P0'],
    storyPoints: 13,
    sprint: 'S1'
  },
  {
    id: 'AGT-006',
    summary: '[AI/LLM] JD Generator Service — Geração Inteligente de Job Descriptions (Ag.1)',
    description: `**Componente:** JD Generator Service (Ag.1 — Job Intake/JD)
**Tipo:** Serviço LLM
**Sprint:** S1 | **Prioridade:** P1
**Referência Alpha 1:** Passo 2 — edição e enriquecimento da vaga importada

---

## Objetivo
Serviço LLM que gera/enriquece Job Descriptions a partir de dados importados do ATS, sugerindo melhorias, competências-chave e perguntas de triagem WSI.

## Escopo Detalhado

### 1. Geração de JD
- Input: dados brutos da vaga do ATS (título, descrição, requisitos)
- Output: JD estruturada com seções padronizadas
- Seções: Sobre a Empresa, Sobre a Vaga, Responsabilidades, Requisitos, Benefícios, Modelo de Trabalho

### 2. Sugestão de Competências WSI
- Análise da JD para extrair competências comportamentais
- Mapeamento para blocos WSI (ex: Liderança, Comunicação, Resolução de Problemas)
- Sugestão de peso por competência baseado na senioridade

### 3. Sugestão de Perguntas de Triagem
- Geração de perguntas comportamentais por competência WSI
- Formato STAR (Situação, Tarefa, Ação, Resultado)
- 3-5 perguntas por bloco WSI

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/job_management/agents/\` — WizardReAct + JobWizardGraph
- \`lia-agent-system/app/domains/job_management/services/jd_generator_service.py\`

## Artefatos a Produzir
1. \`services/jd/jd_generator_service.py\` — Serviço de geração (evoluir existente)
2. \`services/jd/wsi_competency_extractor.py\` — Extrator de competências
3. \`services/jd/screening_question_generator.py\` — Gerador de perguntas
4. Testes unitários com JDs de exemplo

## Critérios de Aceitação
- [ ] Gera JD estruturada a partir de dados brutos do ATS
- [ ] Extrai 3-7 competências WSI relevantes
- [ ] Sugere 3-5 perguntas de triagem por competência
- [ ] Output em formato JSON estruturado
- [ ] FairnessGuard valida que JD não tem viés

## Dependências
- AGT-002 (FairnessGuard)
- AGT-003 (dados de vaga do ATS)
- Gemini/OpenAI API

## Estimativa: 5 Story Points`,
    priority: 'High',
    labels: ['ai-agent', 'llm', 'job-description', 'alpha1', 'sprint-1', 'P1'],
    storyPoints: 5,
    sprint: 'S1'
  },
  {
    id: 'AGT-007',
    summary: '[AI/CORE] WSIInterviewGraph — Triagem Conversacional + Scoring WSI (Ag.4+Ag.5)',
    description: `**Componente:** WSIInterviewGraph (Ag.4 — Entrevistador WSI + Ag.5 — Avaliador WSI unificados)
**Tipo:** LangGraph StateGraph
**Sprint:** S2 (Core WSI) | **Prioridade:** P0
**Referência Alpha 1:** Passo 7 — triagem conversacional WSI via chat web

---

## Objetivo
Implementar o grafo LangGraph que conduz a entrevista WSI (Work Situation Interview) com o candidato via chat web, avalia respostas em tempo real, aplica scoring por competência e gera feedback estruturado.

## Escopo Detalhado

### 1. Nós do Grafo (LangGraph StateGraph)
- **classify_input:** Classifica a mensagem do candidato (resposta, pergunta, off-topic, abandono)
- **select_question:** Seleciona próxima pergunta WSI baseada no roteiro e respostas anteriores
- **evaluate_response:** Avalia resposta usando rubrica STAR (Situação, Tarefa, Ação, Resultado)
- **probe_deeper:** Gera follow-up probe se resposta superficial (<50% rubrica)
- **score_competency:** Calcula score por competência (0-100) após todas perguntas do bloco
- **decide_flow:** Decide próximo bloco WSI ou fim da entrevista
- **craft_message:** Gera mensagem conversacional para o candidato
- **generate_feedback:** Gera feedback estruturado pós-entrevista

### 2. Estado da Entrevista (InterviewState)
- session_id, candidate_id, vacancy_id
- current_block (WSI block atual), current_question_index
- responses[] (respostas do candidato com timestamps)
- scores{} (scores por competência)
- probes_used (contagem de follow-ups)
- status (in_progress, completed, abandoned, timeout)

### 3. Scoring WSI
- Rubrica STAR por pergunta (4 dimensões × peso)
- Score normalizado 0-100 por competência
- Score composto ponderado (peso de cada competência configurável)
- Threshold de Gate 1: score composto ≥ 60 (configurável)

### 4. Feedback Diferenciado
- **Gate 1 Aprovado:** Feedback positivo + agendamento de entrevista com gestor
- **Gate 1 Reprovado:** Feedback construtivo com pontos de melhoria (sem revelar scores)
- **Gate 2 (pós entrevista gestor):** Feedback final com resultado

### 5. Adaptação Dinâmica
- Se candidato responde muito bem (>80%), pula para próximo bloco
- Se candidato luta (<40%), oferece rephrasing da pergunta
- Máximo de 2 probes por pergunta

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py\` — WSIInterviewGraph
- \`lia-agent-system/app/domains/cv_screening/agents/evaluation_criteria_generator.py\`
- \`lia-agent-system/app/domains/cv_screening/services/scoring_service.py\`

## Código Base Existente (V5)
- \`src/domains/evaluation/graph.py\` — InterviewGraph (classify→evaluate→decide→craft)
- \`src/domains/evaluation/nodes.py\` — 4 nós
- \`src/domains/evaluation/state.py\` — InterviewState
- \`src/domains/evaluation/models.py\` — InputClassification, RubricEvaluation

## Artefatos a Produzir
1. \`domains/wsi/agents/wsi_interview_graph.py\` — Grafo principal (evoluir LIA + V5)
2. \`domains/wsi/agents/wsi_nodes.py\` — Nós do grafo (8 nós)
3. \`domains/wsi/agents/wsi_state.py\` — InterviewState Alpha 1
4. \`domains/wsi/agents/wsi_prompts.py\` — Prompts por nó
5. \`domains/wsi/services/scoring_service.py\` — Scoring WSI (evoluir)
6. \`domains/wsi/services/feedback_generator.py\` — Gerador de feedback
7. Testes end-to-end com conversas simuladas

## Critérios de Aceitação
- [ ] Conduz entrevista WSI completa (3-7 blocos, 3-5 perguntas/bloco)
- [ ] Classifica inputs corretamente (resposta vs pergunta vs off-topic)
- [ ] Avalia respostas com rubrica STAR (accuracy >80% vs humano)
- [ ] Probe deeper funciona para respostas superficiais
- [ ] Score por competência calculado corretamente (0-100)
- [ ] Feedback diferenciado por resultado (aprovado vs reprovado)
- [ ] Adaptação dinâmica (skip/rephrase) funciona
- [ ] Estado persiste entre mensagens (candidato pode sair e voltar)
- [ ] FairnessGuard valida todas as avaliações
- [ ] AuditCallback registra scores e decisões

## Dependências
- AGT-001 (Orchestrator roteia para WSI)
- AGT-002 (BaseAgent, FairnessGuard, AuditCallback)
- AGT-009 (Chat Web para delivery)
- Gemini/Claude API (para avaliação)

## Estimativa: 21 Story Points`,
    priority: 'Highest',
    labels: ['ai-agent', 'wsi', 'interview', 'langgraph', 'alpha1', 'sprint-2', 'P0'],
    storyPoints: 21,
    sprint: 'S2'
  },
  {
    id: 'AGT-008',
    summary: '[AI/AGENT] CVScreeningReActAgent — Triagem Curricular Automatizada (Ag.3)',
    description: `**Componente:** CVScreeningReActAgent (Ag.3 — Triagem Curricular)
**Tipo:** Agente ReAct
**Sprint:** S2 | **Prioridade:** P1
**Referência Alpha 1:** Passo 3 — triagem de candidatos sourced ou inscritos

---

## Objetivo
Agente ReAct que analisa CVs/perfis contra requisitos da vaga, calcula matching score e decide se candidato avança para Gate 1 (triagem WSI) ou é descartado.

## Escopo Detalhado

### 1. Análise de CV
- Extração de dados do CV (skills, experiência, formação, idiomas)
- Matching contra requisitos obrigatórios da vaga
- Matching contra requisitos desejáveis
- Score de matching (0-100) com breakdown por requisito

### 2. Decisão de Triagem
- Score ≥ threshold configurável → avança para Gate 1 (triagem WSI)
- Score < threshold → descartado com feedback
- Casos borderline → flag para revisão humana (HITL)

### 3. Tools do Agente
- \`parse_cv\` — Extrai dados estruturados do CV
- \`match_requirements\` — Compara perfil vs requisitos
- \`calculate_score\` — Calcula score de matching
- \`check_duplicates\` — Verifica se candidato já foi triado nesta vaga

### 4. Inscrição Web (Bypass Gate 1)
- Candidatos que se inscrevem via web pulam a triagem curricular
- Vão direto para Gate 1 (triagem WSI) com flag \`source=web_inscription\`

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/cv_screening/agents/cv_screening_react_agent.py\`
- \`lia-agent-system/app/domains/cv_screening/agents/cv_pipeline_react_agent.py\`
- \`lia-agent-system/app/domains/cv_screening/services/matching_service.py\`

## Artefatos a Produzir
1. \`domains/screening/agents/cv_screening_react_agent.py\` — Agente ReAct (evoluir)
2. \`domains/screening/agents/cv_screening_tool_registry.py\` — Tools
3. \`domains/screening/agents/cv_screening_system_prompt.py\` — Prompt
4. \`domains/screening/services/cv_parser.py\` — Parser de CV
5. \`domains/screening/services/matching_service.py\` — Matching score (evoluir)
6. Testes com CVs de exemplo variados

## Critérios de Aceitação
- [ ] Extrai dados de CV em formato estruturado
- [ ] Calcula matching score com breakdown por requisito
- [ ] Decisão correta (avança/descarta/HITL) baseada em threshold
- [ ] Bypass para inscritos via web funciona
- [ ] FairnessGuard valida que decisões não têm viés de gênero/idade/etnia
- [ ] AuditCallback registra todas as decisões

## Dependências
- AGT-002 (BaseAgent, FairnessGuard)
- AGT-003 (dados de vaga do ATS)

## Estimativa: 8 Story Points`,
    priority: 'High',
    labels: ['ai-agent', 'screening', 'cv', 'alpha1', 'sprint-2', 'P1'],
    storyPoints: 8,
    sprint: 'S2'
  },
  {
    id: 'AGT-009',
    summary: '[INFRA] Chat Web Canal — WebSocket para Triagem WSI via Browser',
    description: `**Componente:** Chat Web Canal (Infraestrutura de Triagem)
**Tipo:** Infraestrutura WebSocket
**Sprint:** S2 | **Prioridade:** P0
**Referência Alpha 1:** Passo 7 — candidato clica link no email → chat web para triagem WSI

---

## Objetivo
Implementar canal de chat web (WebSocket) que permite ao candidato realizar a triagem WSI diretamente no browser, acessível via link enviado por email.

## Escopo Detalhado

### 1. WebSocket Gateway
- Endpoint: \`/ws/screening/{session_token}\`
- Autenticação via token único no link do email (JWT com expiração)
- Reconexão automática se conexão cair
- Heartbeat para detectar desconexão

### 2. Interface do Candidato
- Página web standalone (não requer login WeDo)
- Chat interface responsiva (mobile-first)
- Mensagens da LIA (perguntas WSI) + respostas do candidato
- Indicador de progresso (bloco X de Y)
- Opção de pausar e retomar depois

### 3. Integração com WSIInterviewGraph
- WebSocket recebe mensagem do candidato → envia para WSIInterviewGraph
- WSIInterviewGraph retorna resposta → envia via WebSocket
- Estado persistente (candidato pode fechar browser e retomar)

### 4. Segurança
- Token único por candidato×vaga (não reutilizável)
- Expiração do token (7 dias default)
- Rate limiting (máx 10 mensagens/minuto)
- Sanitização de input

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/cv_screening/routes/agent_chat_ws.py\` — WebSocket base
- \`lia-agent-system/app/core/websocket_manager.py\` — WebSocket manager

## Artefatos a Produzir
1. \`infra/websocket/screening_gateway.py\` — Gateway WebSocket (evoluir)
2. \`infra/websocket/session_manager.py\` — Gerenciamento de sessões
3. \`infra/websocket/token_service.py\` — Geração/validação de tokens JWT
4. Página web standalone (HTML/CSS/JS) para candidato
5. Testes de integração WebSocket

## Critérios de Aceitação
- [ ] Candidato acessa chat via link no email
- [ ] Token válido por 7 dias (configurável)
- [ ] WebSocket conecta e mantém sessão
- [ ] Reconexão automática funciona
- [ ] Integração com WSIInterviewGraph funciona end-to-end
- [ ] Estado persiste entre sessões (candidato pode voltar)
- [ ] Mobile-responsive
- [ ] Rate limiting implementado

## Dependências
- AGT-007 (WSIInterviewGraph para conduzir entrevista)
- AGT-005 (Email adapter para enviar link)

## Estimativa: 8 Story Points`,
    priority: 'Highest',
    labels: ['infra', 'websocket', 'chat', 'alpha1', 'sprint-2', 'P0'],
    storyPoints: 8,
    sprint: 'S2'
  },
  {
    id: 'AGT-010',
    summary: '[AI/AUTO] Follow-up Scheduler + Email Tracking — Reenvio 7 Dias + Rastreamento',
    description: `**Componente:** Follow-up Scheduler + Email Tracking
**Tipo:** Serviço de Automação
**Sprint:** S2 | **Prioridade:** P1
**Referência Alpha 1:** Passo 6B — re-envio automático a cada 24h por 7 dias + tracking de abertura

---

## Objetivo
Implementar scheduler de follow-up que re-envia emails para candidatos que não responderam (máx 7 tentativas em 7 dias) com tracking de abertura e clique.

## Escopo Detalhado

### 1. Follow-up Scheduler
- Job agendado que verifica candidatos sem resposta a cada hora
- Regra: se não abriu email em 24h, re-enviar com template variado
- Máximo de 7 re-envios (1 por dia durante 7 dias)
- Templates rotativos (template 1 diferente do template 7)
- Para automático se candidato abrir email ou responder

### 2. Email Tracking
- Pixel de rastreamento em emails HTML (1x1 transparent PNG)
- Link redirect para rastrear cliques no link de triagem
- Eventos: email_sent, email_opened, link_clicked, email_bounced
- Webhook para receber bounces do provedor (SES/SendGrid)

### 3. Dashboard de Métricas
- Taxa de abertura por template
- Taxa de clique no link de triagem
- Taxa de conversão (abriu → iniciou triagem)
- Candidatos em follow-up por vaga

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/automation/services/automation_scheduler.py\` — Scheduler base (APScheduler)
- \`lia-agent-system/app/domains/automation/services/planned_task_service.py\` — Task service

## Artefatos a Produzir
1. \`services/followup/followup_scheduler.py\` — Scheduler de follow-up (evoluir automation_scheduler)
2. \`services/followup/email_tracker.py\` — Tracking service
3. \`services/followup/tracking_pixel_handler.py\` — Endpoint para pixel 1x1
4. \`services/followup/link_redirect_handler.py\` — Endpoint para redirect
5. Migration para tabela email_tracking_events
6. Testes unitários + integration

## Critérios de Aceitação
- [ ] Re-envia email a cada 24h para candidatos sem resposta
- [ ] Máximo de 7 re-envios por candidato
- [ ] Para quando candidato abre email ou responde
- [ ] Pixel tracking registra evento de abertura
- [ ] Link redirect registra evento de clique
- [ ] Templates variam a cada re-envio
- [ ] Métricas de abertura/clique disponíveis via API

## Dependências
- AGT-005 (CommunicationService para envio)
- AGT-016 (EventRetryOrchestrator para scheduling robusto)

## Estimativa: 8 Story Points`,
    priority: 'High',
    labels: ['automation', 'email', 'tracking', 'alpha1', 'sprint-2', 'P1'],
    storyPoints: 8,
    sprint: 'S2'
  },
  {
    id: 'AGT-011',
    summary: '[AI/HITL] Gate 1/Gate 2 Pipeline — Transições HITL + Decisões Humanas',
    description: `**Componente:** Gate 1/Gate 2 HITL Pipeline
**Tipo:** Serviço + HITL
**Sprint:** S3 (Gates + Scheduling) | **Prioridade:** P0
**Referência Alpha 1:** Passos 8, 9 — Gates de decisão humana no pipeline

---

## Objetivo
Implementar o sistema de Gates (portões de decisão) onde o consultor humano revisa os resultados da IA e decide se o candidato avança no pipeline.

## Escopo Detalhado

### 1. Gate 1 (Pós-Triagem WSI)
- Consultor recebe shortlist de candidatos que passaram na triagem WSI
- Dashboard com: scores WSI, comparação entre candidatos, recomendação da IA
- Ações: Aprovar (→ agendar entrevista), Rejeitar (→ feedback), Revisitar (→ re-triagem)
- Notificação ao consultor via Teams/email quando shortlist pronta

### 2. Gate 2 (Pós-Entrevista com Gestor)
- Consultor + Gestor revisam candidatos pós-entrevista
- Dashboard com: notas da entrevista, scores WSI, feedback do gestor
- Ações: Aprovar (→ oferta), Rejeitar (→ feedback), Holdpool
- Resultado exportado para ATS

### 3. Transições de Pipeline
- Estado canônico do candidato no pipeline: sourced → cv_screened → wsi_screened → gate1_approved → interviewed → gate2_approved → offered
- Cada transição gera evento (para CommunicationService e AuditCallback)
- Rollback possível (ex: gate1_approved → wsi_screened se erro)

### 4. HITL Interface
- Endpoint API: \`GET /api/pipeline/gates/{gate_id}/candidates\`
- Endpoint API: \`POST /api/pipeline/gates/{gate_id}/decisions\`
- Timeout configurável (24h default) com escalação

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/automation/services/stage_automation_engine.py\` — Engine de transições
- \`lia-agent-system/app/domains/pipeline_management/agents/pipeline_transition_agent.py\` — Agent de transição

## Artefatos a Produzir
1. \`services/pipeline/gate_service.py\` — Serviço de Gates
2. \`services/pipeline/pipeline_state_machine.py\` — State machine do pipeline
3. \`services/pipeline/decision_endpoint.py\` — Endpoints HITL
4. \`services/pipeline/gate_notification.py\` — Notificações de Gate pendente
5. Migration para tabelas pipeline_state, gate_decisions
6. Testes de fluxo completo (Gate 1 + Gate 2)

## Critérios de Aceitação
- [ ] Gate 1: consultor vê shortlist com scores e decide
- [ ] Gate 2: consultor + gestor decidem pós-entrevista
- [ ] Transições de pipeline registradas com timestamp e responsável
- [ ] Eventos disparados a cada transição (email, Teams, ATS sync)
- [ ] Timeout + escalação funcionam
- [ ] AuditCallback registra todas as decisões humanas

## Dependências
- AGT-007 (WSIInterviewGraph para scores)
- AGT-005 (CommunicationService para notificações)
- AGT-015 (PipelineGateService para estado canônico)

## Estimativa: 8 Story Points`,
    priority: 'Highest',
    labels: ['ai-agent', 'hitl', 'pipeline', 'gates', 'alpha1', 'sprint-3', 'P0'],
    storyPoints: 8,
    sprint: 'S3'
  },
  {
    id: 'AGT-012',
    summary: '[AI/AGENT] SchedulingGraph — Agendamento de Entrevistas com Gestor (Ag.6)',
    description: `**Componente:** SchedulingGraph (Ag.6 — Agendamento)
**Tipo:** LangGraph StateGraph
**Sprint:** S3 | **Prioridade:** P1
**Referência Alpha 1:** Passo 9 — agendar entrevista candidato aprovado Gate 1 com gestor

---

## Objetivo
Implementar grafo LangGraph que coordena agendamento de entrevistas entre candidato aprovado e gestor, integrando com calendários (Google Calendar/Outlook) e gerando links de reunião.

## Escopo Detalhado

### 1. Nós do Grafo
- **check_availability:** Consulta calendário do gestor para horários disponíveis
- **propose_slots:** Propõe 3-5 horários ao candidato via email
- **collect_preference:** Recebe escolha do candidato
- **confirm_booking:** Confirma agendamento e cria evento no calendário
- **send_confirmation:** Envia confirmação + link de reunião para ambos
- **handle_conflict:** Se horário não disponível mais, re-propõe

### 2. Integração de Calendário
- Google Calendar API (OAuth2)
- Microsoft Outlook/Graph API (OAuth2)
- Fallback: horários manuais cadastrados pelo consultor

### 3. Link de Reunião
- Google Meet (gerado com evento)
- Microsoft Teams (gerado com evento)
- Zoom (API de criação de reunião)

### 4. Fluxo de Fallback
- Se gestor não tem calendário integrado: consultor define horários manualmente
- Se candidato não escolhe em 48h: alerta ao consultor via Teams
- Se nenhum horário funciona: escalação para re-proposição manual

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/scheduling/agents/\` — Scheduling agents
- \`lia-agent-system/app/domains/scheduling/services/calendar_service.py\`

## Artefatos a Produzir
1. \`domains/scheduling/agents/scheduling_graph.py\` — Grafo principal (evoluir)
2. \`domains/scheduling/agents/scheduling_nodes.py\` — Nós do grafo
3. \`domains/scheduling/services/calendar_service.py\` — Integração calendário (evoluir)
4. \`domains/scheduling/services/meeting_link_service.py\` — Geração de links
5. \`domains/scheduling/services/slot_proposer.py\` — Proposição de horários
6. Testes com calendários mock

## Critérios de Aceitação
- [ ] Consulta disponibilidade do gestor via API de calendário
- [ ] Propõe 3-5 horários ao candidato por email
- [ ] Candidato escolhe horário e evento é criado
- [ ] Link de reunião gerado automaticamente
- [ ] Confirmação enviada para candidato + gestor
- [ ] Fallback funciona quando calendário não integrado
- [ ] Alerta ao consultor se candidato não responde em 48h

## Dependências
- AGT-011 (Gate 1 aprovação dispara agendamento)
- AGT-005 (CommunicationService para emails)
- Google Calendar ou Outlook API credentials

## Estimativa: 13 Story Points`,
    priority: 'High',
    labels: ['ai-agent', 'scheduling', 'calendar', 'langgraph', 'alpha1', 'sprint-3', 'P1'],
    storyPoints: 13,
    sprint: 'S3'
  },
  {
    id: 'AGT-013',
    summary: '[AI/AUTO] Triagem Abandonada Monitor — Timeout 48h + Lembretes Automáticos',
    description: `**Componente:** Triagem Abandonada Monitor
**Tipo:** Serviço de Automação
**Sprint:** S3 | **Prioridade:** P1
**Referência Alpha 1:** Passo 7A — timeout 48h se candidato não completa triagem + 2 lembretes

---

## Objetivo
Monitorar candidatos que iniciaram triagem WSI mas não completaram, enviando lembretes e marcando como abandonada após timeout.

## Escopo Detalhado

### 1. Monitor de Timeout
- Job agendado que verifica sessões WSI inativas a cada hora
- Regra: se última mensagem > 24h, enviar lembrete 1
- Regra: se última mensagem > 36h, enviar lembrete 2
- Regra: se última mensagem > 48h, marcar como abandonada

### 2. Lembretes
- Template de lembrete 1: "Olá {nome}, notamos que sua triagem está pendente..."
- Template de lembrete 2: "Última chance! Sua triagem expira em 12 horas..."
- Canal: email (mesmo canal do contato inicial)

### 3. Notificação ao Consultor
- Quando triagem marcada como abandonada: notificação ao consultor via Teams
- Dashboard com candidatos abandonados por vaga
- Opção de re-abrir prazo (reset timer)

## Código Base Existente (LIA)
- \`communication_matrix.py\` — trigger \`triagem_abandonada\` (linha 181)
- \`automation_scheduler.py\` — Scheduler base

## Artefatos a Produzir
1. \`services/monitoring/abandoned_screening_monitor.py\` — Monitor principal
2. \`services/monitoring/screening_reminder_service.py\` — Serviço de lembretes
3. Templates de email de lembrete (2 variantes)
4. Endpoint: \`POST /api/screening/{id}/extend-deadline\` para re-abrir prazo
5. Testes unitários

## Critérios de Aceitação
- [ ] Detecta sessões WSI inativas >24h
- [ ] Envia lembrete 1 após 24h e lembrete 2 após 36h
- [ ] Marca como abandonada após 48h
- [ ] Notifica consultor via Teams quando abandonada
- [ ] Consultor pode re-abrir prazo via API
- [ ] Métricas: taxa de abandono por vaga

## Dependências
- AGT-005 (CommunicationService)
- AGT-007 (WSIInterviewGraph — status da sessão)
- AGT-016 (EventRetryOrchestrator)

## Estimativa: 5 Story Points`,
    priority: 'High',
    labels: ['automation', 'monitoring', 'screening', 'alpha1', 'sprint-3', 'P1'],
    storyPoints: 5,
    sprint: 'S3'
  },
  {
    id: 'AGT-014',
    summary: '[INTEG] Teams/Slack Notifications — Alertas ao Consultor via Webhooks',
    description: `**Componente:** Teams/Slack Notifications
**Tipo:** Serviço de Integração
**Sprint:** S3 | **Prioridade:** P2
**Referência Alpha 1:** Passos 7A, 9A — alertas ao consultor para ações urgentes

---

## Objetivo
Integrar notificações push via Microsoft Teams (primário) e Slack (secundário) para alertar consultores sobre eventos que requerem ação.

## Escopo Detalhado

### 1. Eventos Notificáveis
- Gate 1 shortlist pronta para revisão
- Triagem abandonada (48h timeout)
- Candidato sem resposta ao agendamento (48h)
- Erro em automação (falha de envio de email, API ATS down)

### 2. Teams Integration
- Webhook configurável por consultor
- Cards adaptativos com botões de ação (Aprovar/Rejeitar/Ver)
- Link direto para dashboard WeDo

### 3. Slack Integration (Secundário)
- Webhook configurável
- Block Kit messages com botões
- Fallback se Teams não configurado

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/communication/adapters/teams_adapter.py\`
- \`lia-agent-system/app/domains/communication/models/teams.py\`

## Artefatos a Produzir
1. \`services/notifications/teams_notifier.py\` — Notificador Teams (evoluir)
2. \`services/notifications/slack_notifier.py\` — Notificador Slack (novo)
3. \`services/notifications/notification_config.py\` — Configuração por consultor
4. Testes com webhook mocks

## Critérios de Aceitação
- [ ] Notificação Teams enviada para eventos configurados
- [ ] Card adaptativo com botões de ação funciona
- [ ] Link para dashboard WeDo correto
- [ ] Fallback Slack funciona se Teams não configurado
- [ ] Configuração por consultor via API

## Dependências
- AGT-005 (CommunicationService — routing)
- Teams Webhook URL / Slack Webhook URL

## Estimativa: 3 Story Points`,
    priority: 'Medium',
    labels: ['integration', 'teams', 'slack', 'notifications', 'alpha1', 'sprint-3', 'P2'],
    storyPoints: 3,
    sprint: 'S3'
  },
  {
    id: 'AGT-015',
    summary: '[AI/ARCH] PipelineGateService — Estado Canônico de Pipeline + Regras de Transição',
    description: `**Componente:** PipelineGateService
**Tipo:** Serviço Core
**Sprint:** S1 | **Prioridade:** P0
**Referência Alpha 1:** Transversal — estado canônico do candidato no pipeline

---

## Objetivo
Serviço que mantém o estado canônico (single source of truth) do candidato no pipeline de recrutamento, com regras de transição validadas, auditoria de decisões e suporte a bypass (inscrição web).

## Escopo Detalhado

### 1. Estado Canônico do Pipeline
- Estados: sourced → cv_screened → wsi_invited → wsi_in_progress → wsi_completed → gate1_pending → gate1_approved/gate1_rejected → interview_scheduled → interviewed → gate2_pending → gate2_approved/gate2_rejected → offered
- Single source of truth em PostgreSQL
- Timestamp e responsável por cada transição

### 2. Regras de Transição
- Validação: só permite transições válidas (ex: não pode ir de sourced → offered)
- Bypass: inscrição web → pula cv_screened, vai direto para wsi_invited
- Rollback: transições reversíveis com justificativa (gate1_approved → wsi_completed)

### 3. Eventos de Transição
- Cada transição emite evento para:
  - CommunicationService (email/Teams ao candidato/consultor)
  - ATSIntegrationService (sync status com ATS)
  - AuditCallback (rastreabilidade)

### 4. API
- \`GET /api/pipeline/candidates/{id}/state\` — Estado atual
- \`POST /api/pipeline/candidates/{id}/transition\` — Executar transição
- \`GET /api/pipeline/candidates/{id}/history\` — Histórico de transições

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/automation/services/stage_automation_engine.py\`
- \`lia-agent-system/app/domains/pipeline_management/agents/pipeline_transition_agent.py\`

## Artefatos a Produzir
1. \`services/pipeline/pipeline_gate_service.py\` — Serviço principal
2. \`services/pipeline/pipeline_state_machine.py\` — State machine
3. \`services/pipeline/pipeline_event_emitter.py\` — Emissão de eventos
4. Migration para tabela pipeline_states, pipeline_transitions
5. Testes de todas as transições válidas/inválidas

## Critérios de Aceitação
- [ ] Estado canônico correto para todos os candidatos
- [ ] Transições inválidas rejeitadas com erro claro
- [ ] Bypass web inscription funciona
- [ ] Rollback com justificativa funciona
- [ ] Eventos emitidos para cada transição
- [ ] Histórico completo de transições acessível via API
- [ ] AuditCallback registra todas as transições

## Dependências
- AGT-002 (AuditCallback)
- PostgreSQL (tabelas de estado)

## Estimativa: 8 Story Points`,
    priority: 'Highest',
    labels: ['ai-agent', 'pipeline', 'state-machine', 'alpha1', 'sprint-1', 'P0'],
    storyPoints: 8,
    sprint: 'S1'
  },
  {
    id: 'AGT-016',
    summary: '[AI/INFRA] EventRetryOrchestrator — Scheduler Robusto + Idempotência + DLQ',
    description: `**Componente:** EventRetryOrchestrator
**Tipo:** Serviço de Infraestrutura
**Sprint:** S2 | **Prioridade:** P1
**Referência Alpha 1:** Transversal — garantia de entrega de follow-ups, timeouts, lembretes

---

## Objetivo
Serviço de orquestração de eventos assíncronos com garantia de entrega (at-least-once), idempotência, retry com exponential backoff e Dead Letter Queue (DLQ) para eventos que falham repetidamente.

## Escopo Detalhado

### 1. Event Scheduler
- Agendamento de eventos futuros com precisão de minuto
- Eventos: follow-up email (24h), lembrete triagem (24h/36h), timeout triagem (48h)
- Persistência em PostgreSQL (não perde eventos se serviço reiniciar)
- Processamento paralelo com limite de concorrência

### 2. Idempotência
- Cada evento tem ID único (UUID)
- Tabela de idempotência: se evento já processado, skip
- Previne envio duplicado de emails/notificações

### 3. Retry com Backoff
- Retry automático: 1min → 5min → 15min → 1h → 4h (5 tentativas)
- Exponential backoff com jitter
- Após 5 tentativas → DLQ

### 4. Dead Letter Queue (DLQ)
- Eventos que falharam repetidamente vão para DLQ
- Dashboard de DLQ (endpoint API)
- Opção de replay manual de eventos da DLQ
- Alerta ao consultor quando evento vai para DLQ

### 5. Integração
- Usado por: Follow-up Scheduler, Triagem Abandonada Monitor, CommunicationService
- Interface: \`schedule_event(event_type, payload, execute_at)\`
- Interface: \`cancel_event(event_id)\`

## Código Base Existente (LIA)
- \`lia-agent-system/app/domains/automation/services/automation_scheduler.py\` — APScheduler base
- \`lia-agent-system/app/domains/automation/services/planned_task_service.py\` — Task service

## Artefatos a Produzir
1. \`services/events/event_retry_orchestrator.py\` — Orquestrador principal (evoluir)
2. \`services/events/idempotency_service.py\` — Serviço de idempotência
3. \`services/events/dead_letter_queue.py\` — DLQ
4. \`services/events/event_store.py\` — Persistência de eventos
5. Migration para tabelas scheduled_events, idempotency_keys, dead_letter_queue
6. Testes de retry, idempotência e DLQ

## Critérios de Aceitação
- [ ] Eventos agendados executam no horário correto (±1min)
- [ ] Idempotência previne processamento duplicado
- [ ] Retry com backoff funciona (5 tentativas)
- [ ] DLQ recebe eventos após esgotar retries
- [ ] Eventos persistem entre reinicializações do serviço
- [ ] Cancel event funciona corretamente
- [ ] Dashboard DLQ lista eventos falhos

## Dependências
- AGT-002 (AuditCallback)
- PostgreSQL (persistência)

## Estimativa: 8 Story Points`,
    priority: 'High',
    labels: ['infra', 'events', 'retry', 'scheduler', 'alpha1', 'sprint-2', 'P1'],
    storyPoints: 8,
    sprint: 'S2'
  }
];

let accessToken: string;
let siteUrl: string;
let cloudId: string;

async function initJira() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY
    ? 'repl ' + process.env.REPL_IDENTITY
    : process.env.WEB_REPL_RENEWAL
    ? 'depl ' + process.env.WEB_REPL_RENEWAL
    : null;

  if (!hostname || !xReplitToken) throw new Error('Missing connector env vars');

  const url = `https://${hostname}/api/v2/connection?include_secrets=true&connector_names=jira`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json', 'X_REPLIT_TOKEN': xReplitToken }
  });
  if (!response.ok) throw new Error(`Connection fetch failed: ${response.status}`);
  const data = await response.json() as any;
  const conn = data.items?.[0];

  accessToken = conn?.settings?.access_token ||
    conn?.settings?.oauth?.credentials?.access_token ||
    conn?.settings?.oauth?.access_token;
  siteUrl = conn?.settings?.site_url;

  if (!accessToken) throw new Error('No access token');

  const resRes = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: { 'Accept': 'application/json', 'Authorization': `Bearer ${accessToken}` }
  });
  if (!resRes.ok) throw new Error(`Cloud ID fetch failed: ${resRes.status}`);
  const resources = await resRes.json() as any[];
  const site = resources.find((r: any) => r.url === siteUrl || r.url?.includes('wedotalent'));
  if (!site) throw new Error('Site not found in accessible resources');
  cloudId = site.id;
  console.log(`Connected to Jira: ${siteUrl} (cloud: ${cloudId})`);
}

async function jiraRequest(endpoint: string, method: string = 'GET', body?: any): Promise<any> {
  const url = `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3${endpoint}`;
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  };
  const options: RequestInit = { method, headers };
  if (body) options.body = JSON.stringify(body);
  const response = await fetch(url, options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Jira API ${response.status}: ${errorText.substring(0, 300)}`);
  }
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

async function createEpic(): Promise<string> {
  const epic = await jiraRequest('/issue', 'POST', {
    fields: {
      project: { key: PROJECT_KEY },
      summary: '[EPIC] AGT — Agentes IA Alpha 1 MVP (Ag.0→Ag.8 + Infra)',
      description: {
        type: 'doc', version: 1,
        content: [{ type: 'paragraph', content: [{ type: 'text',
          text: 'Epic contendo os 16 cards AGT para construcao dos 9 agentes IA do Alpha 1 MVP + infraestrutura compartilhada + servicos de suporte. Referencia: docs/diagnostico-agentes-mvp.md (v9.1). Roadmap Alpha 1 com Email como canal primario, Chat Web para triagem WSI, follow-up 7 dias, timeout 48h, ATS como premissa. Componentes: MainOrchestrator, SourcingReAct, CVScreeningReAct, WSIInterviewGraph, SchedulingGraph, CommunicationService, ATSIntegrationService, PipelineGateService, EventRetryOrchestrator. Total estimado: ~163 Story Points em 4 sprints (S0-S3).'
        }] }]
      },
      issuetype: { name: 'Epic' },
      labels: ['alpha1', 'ai-agents', 'mvp'],
    }
  });
  console.log(`Epic created: ${epic.key}`);
  return epic.key;
}

async function createStory(card: AGTCard, epicKey: string, index: number): Promise<string> {
  const descParagraphs = card.description.split('\n').map(line => ({
    type: 'paragraph' as const,
    content: [{ type: 'text' as const, text: line || ' ' }],
  }));

  const issue = await jiraRequest('/issue', 'POST', {
    fields: {
      project: { key: PROJECT_KEY },
      summary: `${card.id} ${card.summary}`,
      description: { type: 'doc', version: 1, content: descParagraphs },
      issuetype: { name: 'Story' },
      priority: { name: card.priority },
      labels: card.labels,
      customfield_10016: card.storyPoints,
      ...(epicKey ? { parent: { key: epicKey } } : {}),
    }
  });
  console.log(`[${index + 1}/16] ${card.id} created: ${issue.key} (${card.storyPoints} SP)`);
  return issue.key;
}

async function createRelatesLinks(issueKeys: Map<string, string>) {
  const relations: [string, string][] = [
    ['AGT-001', 'AGT-002'],
    ['AGT-004', 'AGT-001'],
    ['AGT-004', 'AGT-002'],
    ['AGT-005', 'AGT-002'],
    ['AGT-006', 'AGT-002'],
    ['AGT-006', 'AGT-003'],
    ['AGT-007', 'AGT-001'],
    ['AGT-007', 'AGT-002'],
    ['AGT-007', 'AGT-009'],
    ['AGT-008', 'AGT-002'],
    ['AGT-008', 'AGT-003'],
    ['AGT-009', 'AGT-007'],
    ['AGT-009', 'AGT-005'],
    ['AGT-010', 'AGT-005'],
    ['AGT-010', 'AGT-016'],
    ['AGT-011', 'AGT-007'],
    ['AGT-011', 'AGT-005'],
    ['AGT-011', 'AGT-015'],
    ['AGT-012', 'AGT-011'],
    ['AGT-012', 'AGT-005'],
    ['AGT-013', 'AGT-005'],
    ['AGT-013', 'AGT-007'],
    ['AGT-013', 'AGT-016'],
    ['AGT-014', 'AGT-005'],
    ['AGT-015', 'AGT-002'],
    ['AGT-016', 'AGT-002'],
  ];

  let linked = 0;
  for (const [from, to] of relations) {
    const fromKey = issueKeys.get(from);
    const toKey = issueKeys.get(to);
    if (!fromKey || !toKey) continue;
    try {
      await jiraRequest('/issueLink', 'POST', {
        type: { name: 'Relates' },
        inwardIssue: { key: fromKey },
        outwardIssue: { key: toKey },
      });
      linked++;
    } catch (e: any) {
      console.warn(`Link ${from}->${to} failed: ${e.message?.substring(0, 100)}`);
    }
  }
  console.log(`Created ${linked}/${relations.length} issue links`);
}

async function main() {
  console.log('=== Creating AGT Cards (Alpha 1 AI Agents) ===\n');
  const client = await getJiraClient();

  const epicKey = await createEpic(client);
  console.log(`\nEpic: ${epicKey}\n`);

  const issueKeys = new Map<string, string>();
  for (let i = 0; i < AGT_CARDS.length; i++) {
    const card = AGT_CARDS[i];
    try {
      const key = await createStory(client, card, epicKey, i);
      issueKeys.set(card.id, key);
      await new Promise(r => setTimeout(r, 500));
    } catch (e: any) {
      console.error(`FAILED ${card.id}: ${e.message}`);
    }
  }

  console.log('\n=== Creating Issue Links ===\n');
  await createRelatesLinks(client, issueKeys);

  console.log('\n=== Summary ===');
  console.log(`Epic: ${epicKey}`);
  console.log(`Cards created: ${issueKeys.size}/16`);
  let totalSP = 0;
  for (const card of AGT_CARDS) {
    const key = issueKeys.get(card.id) || 'FAILED';
    totalSP += card.storyPoints;
    console.log(`  ${card.id} → ${key} (${card.sprint}, ${card.storyPoints} SP)`);
  }
  console.log(`Total Story Points: ${totalSP}`);
}

main().catch(console.error);
