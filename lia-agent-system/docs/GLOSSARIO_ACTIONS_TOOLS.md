# Glossário de Actions e Tools — Plataforma LIA
> **Fonte da verdade:** geração programática a partir do `DomainRegistry` ao vivo + descrições declaradas em cada `DomainAction`/`tool_id`.
> **Geração:** `python3 scripts/generate_glossario_actions_tools.py` (regenerar quando registries mudarem).  
> **Documentos relacionados:** [`MAPA_CAMADA_INTELIGENCIA.md`](./MAPA_CAMADA_INTELIGENCIA.md) (fluxos), [`fase2c_domain_verification_report.md`](./fase2c_domain_verification_report.md) (auditoria viva), [`../ARCHITECTURE.md`](../ARCHITECTURE.md) (ADRs normativos).

---

## Índice — 18 domínios, 281 actions, 94 tools

| # | Domínio | Actions | Tools | Padrão de execução |
|---|---|---:|---:|---|
| 1 | [`agent_studio`](#dom-agent_studio) | 20 | 0 | via agent (sem _ACTION_TOOL_MAP) |
| 2 | [`analytics`](#dom-analytics) | 18 | 10 | _ACTION_TOOL_MAP |
| 3 | [`ats_integration`](#dom-ats_integration) | 18 | 10 | _ACTION_TOOL_MAP |
| 4 | [`automation`](#dom-automation) | 20 | 10 | _ACTION_TOOL_MAP |
| 5 | [`candidate_self_service`](#dom-candidate_self_service) | 4 | 0 | via agent |
| 6 | [`communication`](#dom-communication) | 20 | 10 | _ACTION_TOOL_MAP |
| 7 | [`company_settings`](#dom-company_settings) | 7 | 0 | via agent |
| 8 | [`cv_screening`](#dom-cv_screening) | 24 | 10 | _ACTION_TOOL_MAP |
| 9 | [`digital_twin`](#dom-digital_twin) | 5 | 0 | via agent |
| 10 | [`hiring_policy`](#dom-hiring_policy) | 9 | 0 | via agent |
| 11 | [`interview_scheduling`](#dom-interview_scheduling) | 20 | 10 | _ACTION_TOOL_MAP |
| 12 | [`job_creation`](#dom-job_creation) | 11 | 0 | process_intent + _route_by_stage (intent-routed) |
| 13 | [`job_management`](#dom-job_management) | 30 | 14 | _ACTION_TOOL_MAP |
| 14 | [`pipeline_transition`](#dom-pipeline_transition) | 5 | 0 | via agent |
| 15 | [`recruiter_assistant`](#dom-recruiter_assistant) | 24 | 10 | _ACTION_TOOL_MAP |
| 16 | [`recruitment_campaign`](#dom-recruitment_campaign) | 4 | 0 | via agent |
| 17 | [`sourcing`](#dom-sourcing) | 36 | 10 | _ACTION_TOOL_MAP |
| 18 | [`talent_pool`](#dom-talent_pool) | 6 | 0 | via agent |
| **Σ** | | **281** | **94** | |

### Convenções

Cada entrada traz três frases curtas:

1. **O que faz** — descrição declarada no registry (ou inferida do nome).
2. **O que resolve** — qual problema do recrutador resolve no fluxo conversacional.
3. **Como atua tecnicamente** — handler/serviço/integração que materializa a operação.

Tools sem entrada equivalente em actions são executadas diretamente pelo agente; actions sem tool são executadas via LLM/agent (intent-routed em `job_creation`).

---

## Glossário por Domínio

### <a id='dom-agent_studio'></a>agent_studio

**Domínio:** `agent_studio`  
**Classe:** `AgentStudioDomain`  
**Agente principal:** —  
**Padrão de execução:** via agent (sem _ACTION_TOOL_MAP)  
**Status:** evolução  

_Criação, calibração e marketplace de agentes customizados por tenant._

#### Actions (20)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `assign_to_crew` | Atribuir agente custom como role em uma crew | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `browse_marketplace` | Navegar e buscar agentes disponíveis no marketplace | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `calibrate_agent` | Iniciar calibração do agente (avaliar perfis) | Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_custom_agent` | Criar agente customizado com nome, role, prompt e tools | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_sourcing_agent` | Criar agente de sourcing com template de setor | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `deactivate_agent` | Desativar agente de sourcing ou custom (libera quota) | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `execute_custom_agent` | Executar agente customizado em produção | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `explain_agent_studio` | Explica o que e o Agent Studio e como funciona | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_agent_status` | Ver status, estratégia e métricas do agente | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_studio_consumption` | Ver consumo de tokens e créditos dos agentes do Studio | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `install_from_marketplace` | Instalar agente do marketplace na empresa | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_agents` | Listar agentes de sourcing ativos | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_custom_agents` | Listar agentes customizados da empresa | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_sector_templates` | Listar templates de setor disponíveis | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `pause_agent` | Pausar agente de sourcing | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `publish_to_marketplace` | Publicar agente no marketplace para outras empresas | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `recalibrate_agent` | Recalibrar agente com novo feedback | Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `run_multi_strategy` | Executar busca inteligente com 4 estratégias paralelas | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `test_custom_agent` | Testar agente customizado com uma mensagem | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `uninstall_agent` | Desinstalar agente do marketplace (libera quota) | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |

### <a id='dom-analytics'></a>analytics

**Domínio:** `analytics`  
**Classe:** `AnalyticsDomain`  
**Agente principal:** AnalyticsReActAgent  
**Padrão de execução:** _ACTION_TOOL_MAP  
**Status:** production  

_Relatórios de KPIs, funil de conversão, anomalias e previsões de recrutamento._

#### Actions (18)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `analyze_funnel` | Analisar métricas do funil de conversão de recrutamento | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_analyze_funnel` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `answer_data_question` | Responder perguntas sobre dados e analytics | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_get_insights` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `compare_periods` | Comparar métricas entre períodos de tempo diferentes | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_dashboard` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `detect_anomalies` | Detectar anomalias nos dados de recrutamento | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_detect_anomalies` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `forecast` | Prever métricas e tendências de recrutamento | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_predict` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_candidate_report` | Gerar relatório comparativo de candidatos | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_generate_report` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_job_report` | Gerar relatório da vaga em PDF/Excel | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_generate_report` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_kpi_report` | Gerar relatórios de KPIs para métricas de recrutamento | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_generate_kpi` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_agent_monitoring` | Monitorar desempenho dos agentes de IA | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `analytics_monitoring` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_dashboard_data` | Obter indicadores estratégicos e dados do dashboard | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `analytics_dashboard` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_job_insights` | Obter benchmarks salariais, competências e vagas similares | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `analytics_get_insights` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_search_analytics` | Analytics de desempenho de busca de candidatos | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `analytics_search_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_wizard_analytics` | Analytics de uso do wizard de criação de vagas | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `analytics_search_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `job_health_check` | Verificar indicadores de saúde da vaga de emprego | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_job_health` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `predict_dropout_risk` | Prever risco de desistência do candidato | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_predict` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `predict_hiring_probability` | Previsão com IA para probabilidade de sucesso na contratação | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_predict` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `predict_time_to_fill` | Estimar tempo para preencher uma posição | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_predict` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_strategy` | Sugestões de estratégia baseadas em dados com IA | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_get_insights` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |

#### Tools (10)

| tool_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `analytics_analyze_funnel` | Analisa métricas do funil de conversão | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.analytics.services.report_service.analyze_funnel` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `analytics_dashboard` | Obtém indicadores estratégicos e dados do dashboard | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.analytics.services.report_service.get_dashboard_data` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `analytics_detect_anomalies` | Detecta anomalias nos dados de recrutamento | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.analytics.services.report_service.detect_anomalies` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `analytics_generate_kpi` | Gera relatórios de KPIs de recrutamento | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Handler `app.domains.analytics.services.report_service.generate_kpi_report` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `analytics_generate_report` | Gera relatórios em PDF/Excel para vagas e candidatos | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Handler `app.domains.analytics.services.job_report_service.generate_report` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `analytics_get_insights` | Obtém benchmarks salariais, competências e vagas similares | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.analytics.services.job_insights_service.get_job_insights` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `analytics_job_health` | Verifica indicadores de saúde da vaga | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.analytics.services.report_service.job_health_check` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `analytics_monitoring` | Dados de monitoramento de desempenho dos agentes de IA | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.shared.observability.agent_monitoring_service.get_monitoring_data` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `analytics_predict` | Previsões de contratação, tempo de preenchimento e risco de desistência | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Handler `app.domains.analytics.services.predictive_analytics_service.predict` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `analytics_search_analytics` | Dados de desempenho de busca de candidatos | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Handler `app.domains.analytics.services.search_analytics_service.get_search_analytics` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |

### <a id='dom-ats_integration'></a>ats_integration

**Domínio:** `ats_integration`  
**Classe:** `ATSIntegrationDomain`  
**Agente principal:** ATSIntegrationReActAgent  
**Padrão de execução:** _ACTION_TOOL_MAP  
**Status:** production  

_Sincronização bidirecional com ATS externos (Gupy, Pandape, Merge)._

#### Actions (18)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `bulk_sync` | Executar sincronização em massa de múltiplos registros | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_sync_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `check_sync_status` | Verificar o status atual da sincronização com o ATS | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_check_status` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `configure_ats` | Configurar conexão e credenciais do ATS externo | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `ats_list_connections` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `disable_webhook` | Desativar webhook de sincronização com o ATS | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_test_connection` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `enable_webhook` | Ativar webhook para sincronização em tempo real com o ATS | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_test_connection` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `list_connections` | Listar conexões ATS configuradas | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `ats_list_connections` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `map_fields` | Configurar mapeamento de campos entre sistemas | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_view_sync_log` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `pull_candidates` | Importar candidatos do ATS externo para o WedoTalent | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_pull_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `pull_jobs` | Importar vagas do ATS externo para o WedoTalent | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_pull_jobs` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `resolve_conflict` | Resolver conflitos de dados entre sistemas WedoTalent e ATS | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_view_sync_log` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `send_score_ats` | Enviar score/parecer WSI do candidato para o ATS externo | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `ats_send_score` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `sync_candidate` | Sincronizar dados de candidato com o ATS externo | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_sync_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `sync_interview_result` | Sincronizar resultados de entrevista com o ATS externo | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `ats_send_score` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `sync_job` | Sincronizar dados de vaga com o ATS externo | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_sync_job` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `test_connection` | Testar a saúde da conexão com o ATS | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_test_connection` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `update_status_ats` | Enviar atualização de status do candidato para o ATS externo | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `ats_update_status` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `view_field_mapping` | Visualizar mapeamento atual de campos entre sistemas | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `ats_view_sync_log` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `view_sync_log` | Visualizar log de auditoria de sincronização | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `ats_view_sync_log` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |

#### Tools (10)

| tool_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `ats_check_status` | Verifica o status atual da sincronização com o ATS | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.check_sync_status` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `ats_list_connections` | Lista conexões ATS configuradas | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.list_connections` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `ats_pull_candidates` | Importa candidatos do ATS externo para o WedoTalent | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.pull_candidates` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `ats_pull_jobs` | Importa vagas do ATS externo para o WedoTalent | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.pull_jobs` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `ats_send_score` | Envia score/parecer WSI do candidato para o ATS | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.send_score` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `ats_sync_candidate` | Sincroniza dados de candidato com o ATS externo | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.sync_candidate` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `ats_sync_job` | Sincroniza dados de vaga com o ATS externo | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.sync_job` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `ats_test_connection` | Testa a saúde da conexão com o ATS externo | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.test_connection` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `ats_update_status` | Envia atualização de status do candidato para o ATS | Persiste a alteração solicitada sem sair do chat. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.update_candidate_status` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `ats_view_sync_log` | Visualiza log de auditoria de sincronização | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.view_sync_log` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |

### <a id='dom-automation'></a>automation

**Domínio:** `automation`  
**Classe:** `AutomationDomain`  
**Agente principal:** AutomationReActAgent  
**Padrão de execução:** _ACTION_TOOL_MAP  
**Status:** production  

_Tarefas, regras de automação, alertas proativos e agendamentos recorrentes._

#### Actions (20)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `cancel_task` | Cancel a pending task | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Mapeada para a tool `automation_cancel_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `check_proactive_alerts` | Check proactive alerts for recruiter | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_view_log` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `complete_task` | Mark task as completed | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_complete_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `configure_alert` | Configure proactive alert rules | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `automation_create_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `configure_stage_automation` | Set up stage transition automation | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `automation_create_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `create_automation` | Create a new automation rule | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `automation_create_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `create_task` | Create a new task for execution | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `automation_create_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `decompose_task` | Break complex task into subtasks using AI | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_create_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `disable_automation` | Disable an automation rule | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_disable_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `enable_automation` | Enable an automation rule | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_enable_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `get_next_tasks` | Get next tasks ready for execution | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_list_tasks` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `list_automations` | List configured automation rules | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_list_rules` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `list_tasks` | List current tasks and their status | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_list_tasks` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `plan_execution` | Create execution plan with dependencies | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_create_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `predict_substatus` | AI-predict next sub-status for candidate | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `automation_view_log` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `run_autonomous_check` | Run autonomous agent background check | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_trigger` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `schedule_recurring` | Schedule a recurring automation task | Agenda interação ou tarefa no momento certo do funil. | Mapeada para a tool `automation_create_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `trigger_automation` | Manually trigger an automation | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_trigger` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `view_automation_log` | View automation execution history | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_view_log` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `view_task_dependencies` | View task dependency graph | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_list_tasks` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |

#### Tools (10)

| tool_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `automation_cancel_task` | Cancela uma tarefa pendente | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Handler `app.domains.automation.services.task_service.task_service.cancel_task` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `automation_complete_task` | Marca uma tarefa como concluída | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.automation.services.task_service.task_service.complete_task` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `automation_create_rule` | Cria uma nova regra de automação | Materializa um novo registro/objeto solicitado pelo recrutador. | Handler `app.domains.automation.services.automation_service.automation_service.create_automation` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `automation_create_task` | Cria uma nova tarefa para execução | Materializa um novo registro/objeto solicitado pelo recrutador. | Handler `app.domains.automation.services.task_service.task_service.create_task` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `automation_disable_rule` | Desativa uma regra de automação | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.automation.services.automation_service.automation_service.disable_automation` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `automation_enable_rule` | Ativa uma regra de automação | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.automation.services.automation_service.automation_service.enable_automation` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `automation_list_rules` | Lista regras de automação configuradas | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.automation.services.automation_service.automation_service.list_automations` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `automation_list_tasks` | Lista tarefas e seus status atuais | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.automation.services.task_service.task_service.list_tasks` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `automation_trigger` | Dispara manualmente uma automação configurada | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.automation.services.automation_trigger_service.automation_trigger_service.trigger` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `automation_view_log` | Visualiza histórico de execução de automações | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.automation.services.automation_service.automation_service.get_execution_log` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |

### <a id='dom-candidate_self_service'></a>candidate_self_service

**Domínio:** `candidate_self_service`  
**Classe:** `CandidateSelfServiceDomain`  
**Agente principal:** CandidateSelfServiceAgent  
**Padrão de execução:** via agent  
**Status:** evolução  

_Portal do candidato (status, entrevista, feedback, dados LGPD)._

#### Actions (4)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `get_feedback` | Retorna feedback estruturado WSI se disponibilizado pela empresa | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`CandidateSelfServiceAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_interview_info` | Retorna data, horário e formato da entrevista agendada (se houver) | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`CandidateSelfServiceAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_lgpd_info` | Informa sobre direito de explicação (LGPD Art. 20) e canal de contato | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`CandidateSelfServiceAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_status` | Retorna etapa atual, data de entrada e próximos passos | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`CandidateSelfServiceAgent`) sem tool intermediária — usa LLM + serviços do domínio. |

### <a id='dom-communication'></a>communication

**Domínio:** `communication`  
**Classe:** `CommunicationDomain`  
**Agente principal:** CommunicationReActAgent  
**Padrão de execução:** _ACTION_TOOL_MAP  
**Status:** production  

_Email, WhatsApp, Teams, SMS e templates de comunicação multi-canal._

#### Actions (20)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `create_template` | Criar novo template de email para comunicações | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `communication_create_template` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `edit_template` | Editar template de email existente | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_communication_history` | Consultar histórico de comunicações com candidato | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `communication_get_history` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `handle_data_request` | Processar solicitações de dados (LGPD) do candidato | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `communication_data_request` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `list_templates` | Listar templates de email disponíveis | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `communication_list_templates` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `manage_webhook` | Configurar e gerenciar webhooks de comunicação | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `communication_manage_webhook` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `notify_stakeholders` | Enviar notificação para stakeholders sobre eventos do processo | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `preview_template` | Pré-visualizar template de email com dados do candidato | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `communication_preview_template` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `send_bulk_email` | Enviar email para múltiplos destinatários simultaneamente | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `communication_send_bulk` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `send_candidate_report` | Enviar relatório/parecer do candidato para o gestor contratante | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_email` | Enviar email individual para candidato ou stakeholder | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `communication_send_email` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `send_feedback` | Enviar feedback/devolutiva ao candidato sobre o processo seletivo | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_interview_invite` | Enviar convite para entrevista ao candidato | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_kpi_report` | Enviar relatório consolidado de indicadores de recrutamento | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_progress_report` | Enviar relatório de andamento da vaga para stakeholders | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_screening_invite` | Enviar convite para triagem ao candidato | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_sms` | Enviar SMS para candidato | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_teams_message` | Enviar mensagem via Microsoft Teams | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `communication_send_teams` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `send_whatsapp` | Enviar mensagem via WhatsApp para candidato | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `communication_send_whatsapp` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `update_preferences` | Atualizar preferências de comunicação e canal preferido do candidato | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |

#### Tools (10)

| tool_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `communication_create_template` | Cria novo template de email/comunicação | Materializa um novo registro/objeto solicitado pelo recrutador. | Handler `app.domains.communication.services.email_service.create_template` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `communication_data_request` | Processa solicitações de dados LGPD | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.communication.services.data_request_service.handle_request` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `communication_get_history` | Consulta histórico de comunicações com candidato | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.communication.services.communication_history_service.get_history` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `communication_list_templates` | Lista templates de comunicação disponíveis | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.communication.services.email_service.list_templates` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `communication_manage_webhook` | Configura e gerencia webhooks de comunicação | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.communication.services.webhook_service.manage_webhook` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `communication_preview_template` | Visualiza template renderizado com dados do candidato | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.communication.services.email_service.preview_template` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `communication_send_bulk` | Envia emails para múltiplos destinatários | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Handler `app.domains.communication.services.email_service.send_bulk_email` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `communication_send_email` | Envia email individual usando template ou conteúdo customizado | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Handler `app.domains.communication.services.email_service.send_email` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `communication_send_teams` | Envia mensagem via Microsoft Teams | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Handler `app.domains.communication.services.teams_service.send_teams_message` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `communication_send_whatsapp` | Envia mensagem WhatsApp para candidato via provider configurado | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Handler `app.domains.communication.services.whatsapp_service.send_whatsapp_message` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |

### <a id='dom-company_settings'></a>company_settings

**Domínio:** `company_settings`  
**Classe:** `CompanySettingsDomain`  
**Agente principal:** CompanySettingsReActAgent  
**Padrão de execução:** via agent  
**Status:** evolução  

_Configuração do perfil da empresa, cultura, stack tecnológica e benefícios._

#### Actions (7)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `analyze_website` | Analisa website da empresa para extrair dados automaticamente | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`CompanySettingsReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_benefits` | Configura pacote de beneficios da empresa | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`CompanySettingsReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_culture` | Configura missao, visao, valores, cultura e proposta de valor | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`CompanySettingsReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_profile` | Configura dados institucionais da empresa (nome, CNPJ, website, etc.) | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`CompanySettingsReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_tech_stack` | Configura stack tecnologico e cultura de engenharia | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`CompanySettingsReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_workforce` | Configura planejamento de contratacoes (workforce planning) | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`CompanySettingsReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `process_document` | Processa documento enviado para extrair dados da empresa | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`CompanySettingsReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |

### <a id='dom-cv_screening'></a>cv_screening

**Domínio:** `cv_screening`  
**Classe:** `CVScreeningDomain`  
**Agente principal:** PipelineReActAgent  
**Padrão de execução:** _ACTION_TOOL_MAP  
**Status:** production  

_Parsing de CV, score WSI, avaliação de rubricas, perguntas dinâmicas e voice screening._

#### Actions (24)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `adjust_questions` | Ajustar/refinar perguntas com IA | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `adjust_wsi_questions` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `assess_seniority` | Avaliar nível de senioridade | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assess_seniority` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `auto_screen` | Triagem automática contra requisitos da vaga | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `batch_screen` | Triagem em lote de múltiplos candidatos | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `calculate_wsi_score` | Calcular score WSI baseado no CV | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `calculate_wsi` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `calibrate_model` | Calibrar modelo com feedback do recrutador | Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `check_saturation` | Verificar saturação do pipeline | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `classify_bloom` | Classificar respostas pela Taxonomia de Bloom | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `classify_dreyfus` | Classificar nível de proficiência Dreyfus | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `compare_candidates` | Comparar candidatos lado a lado | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `detect_red_flags` | Detectar red flags no CV | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `dynamic_cutoff` | Aplicar corte dinâmico (top 25%) | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `evaluate_rubric` | Avaliar candidato por rubrica estruturada | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `evaluate_rubric` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `explain_score` | Explicar detalhadamente como o score foi calculado | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `generate_questions` | Gerar perguntas de triagem WSI | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `generate_wsi_questions` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_report` | Gerar parecer completo do candidato | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `map_big_five` | Mapear traços Big Five comportamentais | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `normalize_scores` | Normalizar scores entre candidatos | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `normalize_scores` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `parse_cv` | Analisar e extrair dados estruturados do CV | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `parse_cv` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `pre_qualify` | Pré-qualificar candidato antes da triagem | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `pre_qualify_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `rank_candidates` | Rankear candidatos por score WSI | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_feedback` | Enviar feedback personalizado ao candidato | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `send_candidate_feedback` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `validate_cbi` | Validar respostas contra framework CBI | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `voice_screening` | Triagem por voz com WSI | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `run_screening_pipeline` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |

#### Tools (10)

| tool_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `adjust_wsi_questions` | Adjust/refine questions with AI | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.cv_screening.services.wsi_question_adjuster.adjust_questions` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assess_seniority` | Assess candidate seniority level | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.cv_screening.services.seniority_resolver.resolve_seniority` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `calculate_wsi` | Calculate WSI score | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.cv_screening.services.wsi_service.calculate_wsi` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `evaluate_rubric` | Evaluate candidate by rubric | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.cv_screening.services.rubric_evaluation_service.evaluate_rubric` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `generate_wsi_questions` | Generate WSI screening questions | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Handler `app.domains.cv_screening.services.wsi_service.generate_wsi_questions_tool` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `normalize_scores` | Normalize scores across candidates | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.cv_screening.services.score_normalization_service.normalize` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `parse_cv` | Parse CV and extract structured data | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.cv_screening.services.cv_parser.parse_cv` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `pre_qualify_candidate` | Pre-qualify candidate | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.cv_screening.services.pre_qualification_service.pre_qualify` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `run_screening_pipeline` | Run full WSI screening pipeline | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.cv_screening.services.wsi_screening_pipeline.run_pipeline` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `send_candidate_feedback` | Send personalized feedback | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Handler `app.domains.cv_screening.services.personalized_feedback_service.send_feedback` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |

### <a id='dom-digital_twin'></a>digital_twin

**Domínio:** `digital_twin`  
**Classe:** `DigitalTwinDomain`  
**Agente principal:** —  
**Padrão de execução:** via agent  
**Status:** evolução  

_Gêmeo digital de avaliador (clonagem do julgamento humano)._

#### Actions (5)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `create_twin` | Criar twin de um especialista | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `deactivate_twin` | Desativar Digital Twin (libera quota) | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `evaluate_with_twin` | Avaliar candidato usando raciocínio do twin | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `index_twin_audio` | Indexar entrevista gravada com o especialista | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_twins` | Listar Digital Twins disponíveis | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |

### <a id='dom-hiring_policy'></a>hiring_policy

**Domínio:** `hiring_policy`  
**Classe:** `HiringPolicyDomain`  
**Agente principal:** PolicyReActAgent (+ PolicySetupAgent)  
**Padrão de execução:** via agent  
**Status:** production  

_Configuração das políticas de contratação da empresa via wizard de políticas._

#### Actions (9)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `configure_automation` | Define nível de autonomia da LIA e regras de automação | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`PolicyReActAgent (+ PolicySetupAgent)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_candidate_portal` | Ativa e configura o Portal do Candidato (WhatsApp + link web) para candidatos consultarem seu status no processo seletivo | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`PolicyReActAgent (+ PolicySetupAgent)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_communication` | Define regras de comunicação com candidatos | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`PolicyReActAgent (+ PolicySetupAgent)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_pipeline` | Define regras de pipeline e etapas do processo seletivo | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`PolicyReActAgent (+ PolicySetupAgent)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_policy` | Configura regras gerais da política de contratação da empresa | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`PolicyReActAgent (+ PolicySetupAgent)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_scheduling` | Define regras de agendamento de entrevistas | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`PolicyReActAgent (+ PolicySetupAgent)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `configure_screening` | Define regras de triagem e avaliação de candidatos | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`PolicyReActAgent (+ PolicySetupAgent)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_progress` | Retorna o progresso atual da configuração da política | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`PolicyReActAgent (+ PolicySetupAgent)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `validate_compliance` | Valida se a política atual está em conformidade com regras de fairness e LGPD | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PolicyReActAgent (+ PolicySetupAgent)`) sem tool intermediária — usa LLM + serviços do domínio. |

### <a id='dom-interview_scheduling'></a>interview_scheduling

**Domínio:** `interview_scheduling`  
**Classe:** `InterviewSchedulingDomain`  
**Agente principal:** —  
**Padrão de execução:** _ACTION_TOOL_MAP  
**Status:** production  

_Agendamento, lembretes, conflito de agenda, transcrição e análise de voz em entrevistas._

#### Actions (20)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `analyze_response` | Analisar resposta do candidato com IA usando metodologia WSI | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `analyze_voice` | Analisar tom de voz e confiança do candidato | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `scheduling_analyze_voice` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `cancel_interview` | Cancelar entrevista agendada | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `scheduling_cancel` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `check_availability` | Verificar disponibilidade do entrevistador no calendário | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `scheduling_check_availability` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `complete_interview` | Finalizar entrevista e gerar resumo com parecer WSI | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `detect_evasive` | Detectar respostas evasivas do candidato durante entrevista | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `find_common_slots` | Encontrar horários disponíveis comuns para todos os participantes | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `scheduling_find_slots` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_followup` | Gerar pergunta de follow-up baseada na resposta do candidato | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `generate_self_scheduling_link` | Gerar link de auto-agendamento para candidato escolher horário | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `scheduling_self_scheduling_link` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `interview_qa` | Responder dúvidas sobre o processo de entrevista | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_today_interviews` | Listar todas as entrevistas agendadas para hoje | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `scheduling_list_today` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `reschedule_interview` | Reagendar entrevista existente para novo horário | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `scheduling_reschedule` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `resolve_conflict` | Resolver conflitos de agendamento entre entrevistas | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `schedule_interview` | Agendar entrevista com candidato via calendário | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `scheduling_schedule_interview` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `schedule_reminders` | Configurar lembretes automáticos para entrevistas futuras | Agenda interação ou tarefa no momento certo do funil. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_question` | Enviar pergunta de entrevista para candidato | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_reminder` | Enviar lembrete de entrevista para participantes | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `scheduling_send_reminder` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `start_quick_screening` | Iniciar triagem rápida com candidato (10-15min) | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `start_wsi_interview` | Iniciar entrevista WSI completa com candidato (40-60min) | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `transcribe_audio` | Transcrever áudio de entrevista por voz | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `scheduling_transcribe_audio` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |

#### Tools (10)

| tool_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `scheduling_analyze_voice` | Analisa tom de voz e confiança do candidato na entrevista | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.voice.services.voice_service.voice_service.transcribe_audio` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `scheduling_cancel` | Cancela entrevista agendada e notifica participantes | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Handler `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.cancel_interview` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `scheduling_check_availability` | Verifica disponibilidade do entrevistador no calendário | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.interview_scheduling.services.calendar_service.calendar_service.check_availability` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `scheduling_find_slots` | Encontra horários disponíveis comuns para todos os participantes | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Handler `app.domains.interview_scheduling.services.calendar_service.calendar_service.find_common_slots` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `scheduling_list_today` | Lista todas as entrevistas agendadas para hoje | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.list_today_interviews` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `scheduling_reschedule` | Reagenda entrevista existente para novo horário | Agenda interação ou tarefa no momento certo do funil. | Handler `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.reschedule_interview` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `scheduling_schedule_interview` | Agenda entrevista com candidato criando evento no calendário | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.schedule_interview` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `scheduling_self_scheduling_link` | Gera link para candidato escolher horário de entrevista | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.generate_self_scheduling_link` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `scheduling_send_reminder` | Envia lembrete de entrevista para participantes | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Handler `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.send_reminder` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `scheduling_transcribe_audio` | Transcreve áudio de entrevista usando OpenAI Whisper STT | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.voice.services.voice_service.voice_service.transcribe_audio` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |

### <a id='dom-job_creation'></a>job_creation

**Domínio:** `job_creation`  
**Classe:** `JobCreationDomain`  
**Agente principal:** —  
**Padrão de execução:** process_intent + _route_by_stage (intent-routed)  
**Status:** production (ADR-019)  

_Wizard conversacional de criação de vaga com metodologia WSI (intent-routed)._

#### Actions (11)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `approve_jd` | Aprova ou rejeita o JD enriquecido pela IA (HITL ponto 1 - F1). Recrutador pode editar antes de aprovar | Materializa o gate HITL: o recrutador aprova/rejeita uma proposta da IA antes de avançar. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `approve_questions` | Aprova, edita ou regenera as perguntas de triagem WSI (HITL ponto 2 - F6). Recrutador revisa cada pergunta | Materializa o gate HITL: o recrutador aprova/rejeita uma proposta da IA antes de avançar. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `calibrate` | Apresenta candidatos para calibracao (aprovar/rejeitar com razoes). Minimo 3 perfis calibrados antes do handoff | Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `configure_publish` | Define plataformas (LinkedIn/Indeed/Website), modo de sourcing (local/global/hibrido), canais de contato e opcao de auto-screening | Persiste a alteração solicitada sem sair do chat. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `help` | Explica o fluxo de criacao de vaga e a metodologia WSI | Atende uma intenção específica do recrutador dentro do domínio. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `publish_job` | Publica a vaga nas plataformas configuradas e inicia screening automatico. Requer que todas as etapas anteriores estejam completas | Atende uma intenção específica do recrutador dentro do domínio. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `set_eligibility` | Adiciona ou remove perguntas de elegibilidade sim/nao (ex: tem CNH? aceita viagem?). Requisitos eliminatorios antes da triagem WSI | Persiste a alteração solicitada sem sair do chat. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `set_salary` | Define faixa salarial e beneficios da vaga | Persiste a alteração solicitada sem sair do chat. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `set_screening_mode` | Escolhe entre modo compacto (7 perguntas) ou completo (12 perguntas) para a triagem WSI | Persiste a alteração solicitada sem sair do chat. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `start_wizard` | Inicia o wizard de criacao de vaga. Recebe descricao inicial (titulo, senioridade, departamento) e guia o recrutador pelo fluxo WSI completo | Avança o fluxo conversacional por etapas estruturadas. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |
| `wizard_status` | Mostra o progresso atual do wizard de criacao de vaga | Avança o fluxo conversacional por etapas estruturadas. | Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph). |

### <a id='dom-job_management'></a>job_management

**Domínio:** `job_management`  
**Classe:** `JobManagementDomain`  
**Agente principal:** WizardReActAgent (+ JobWizardGraph)  
**Padrão de execução:** _ACTION_TOOL_MAP  
**Status:** production  

_Ciclo de vida de vagas: criação, atualização, pausar, fechar, clonar, templates e enriquecimento de JD._

#### Actions (30)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `advance_wizard_step` | Avançar para próxima etapa do wizard | Avança o fluxo conversacional por etapas estruturadas. | Mapeada para a tool `advance_wizard` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `analyze_jd` | Avaliar qualidade da job description | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `apply_template` | Aplicar template a nova vaga | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `search_job_templates` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `clone_job` | Clonar vaga existente | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `clone_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `close_job` | Fechar/arquivar vaga | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Mapeada para a tool `close_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `create_from_template` | Criar nova vaga usando outra como template | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `clone_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `create_job` | Criar nova vaga via conversa | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `create_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `detect_criteria` | Detectar critérios automaticamente da descrição | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `duplicate_job` | Duplicar vaga existente com todos os dados | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `duplicate_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `enrich_jd` | Enriquecer job description com IA | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `extract_requirements` | Extrair requisitos de uma job description usando IA | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_jd` | Gerar job description completa com IA | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `generate_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_rubrics` | Gerar requisitos estruturados para sistema de Rubricas | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_wsi_questions` | Gerar perguntas de triagem WSI | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `get_benefits` | Obter benefícios da empresa para a vaga | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `get_wizard_step_data` | Obter dados da etapa atual do wizard | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `get_wizard_step` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `guided_wizard` | Fluxo conversacional guiado para criação de vaga | Avança o fluxo conversacional por etapas estruturadas. | Mapeada para a tool `get_wizard_step` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `health_check` | Verificar saúde da vaga | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_health` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `import_jd` | Importar job description existente | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `import_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `job_analytics` | Métricas e analytics de vagas | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `job_status_webhook` | Gerenciar webhooks de status | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_health` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `list_jobs` | Listar vagas abertas/ativas do tenant | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `pause_job` | Pausar vaga temporariamente | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Mapeada para a tool `pause_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `publish_job` | Publicar vaga em job boards | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `update_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `qualify_job` | Qualificar vaga para publicação | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_health` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `search_templates` | Buscar templates de vaga | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `search_job_templates` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_compensation` | Sugerir faixa de compensação | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_jd_improvements` | Sugerir melhorias para job description com IA | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_strategy` | Sugerir mudanças de estratégia | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `update_job` | Atualizar vaga existente | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `update_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |

#### Tools (14)

| tool_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `advance_wizard` | Avança o wizard de criação de vaga para a próxima etapa | Avança o fluxo conversacional por etapas estruturadas. | Handler `app.domains.job_management.services.wizard_orchestrator_service.advance_wizard` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `clone_job_vacancy` | Clona uma vaga existente como nova vaga, sem trazer candidatos | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.tools.job_tools.clone_job_vacancy` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `close_job_vacancy` | Fecha ou arquiva uma vaga de emprego | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Handler `app.tools.job_tools.close_job_vacancy` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `create_job_vacancy` | Cria uma nova vaga de emprego | Materializa um novo registro/objeto solicitado pelo recrutador. | Handler `app.tools.job_tools.create_job_vacancy` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `duplicate_job_vacancy` | Duplica uma vaga existente com todos os dados (e opcionalmente candidatos) | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.tools.job_tools.duplicate_job_vacancy` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `enrich_job_description` | Enriquece uma job description existente com sugestões de IA | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.job_management.services.jd_enrichment_service.enrich_job_description` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `generate_job_description` | Gera uma job description completa usando IA | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Handler `app.domains.job_management.services.jd_generator_service.generate_job_description` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `get_job_analytics` | Obtém métricas e analytics de vagas | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.analytics.services.job_analytics_prompt_service.get_job_analytics` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `get_job_health` | Verifica a saúde e completude de uma vaga | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.analytics.services.job_insights_service.get_job_health` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `get_wizard_step` | Obtém os dados da etapa atual do wizard de criação de vaga | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.job_management.services.wizard_orchestrator_service.get_wizard_step` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `import_job_description` | Importa uma job description existente de texto | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.job_management.services.jd_import_service.import_job_description` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `pause_job_vacancy` | Pausa uma vaga de emprego temporariamente | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Handler `app.tools.job_tools.pause_job` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `search_job_templates` | Busca templates de vaga disponíveis | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Handler `app.domains.job_management.services.job_template_service.search_job_templates` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `update_job_vacancy` | Atualiza uma vaga de emprego existente | Persiste a alteração solicitada sem sair do chat. | Handler `app.tools.job_tools.update_job_vacancy` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |

### <a id='dom-pipeline_transition'></a>pipeline_transition

**Domínio:** `pipeline_transition`  
**Classe:** `PipelineTransitionDomain`  
**Agente principal:** PipelineTransitionAgent + 3 sub-agents (Action/Decision/Context)  
**Padrão de execução:** via agent  
**Status:** production  

_Movimentação de candidatos no pipeline com explicação de contexto e sub-status._

#### Actions (5)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `interpret_context` | Interpreta o contexto de uma transição usando IA | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineTransitionAgent + 3 sub-agents (Action/Decision/Context)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_pipeline_stages` | Lista todas as etapas do pipeline de recrutamento | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`PipelineTransitionAgent + 3 sub-agents (Action/Decision/Context)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `move_candidate` | Move um candidato para uma nova etapa do pipeline | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineTransitionAgent + 3 sub-agents (Action/Decision/Context)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `predict_sub_status` | Prediz o sub-status mais adequado para um candidato | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Executada diretamente pelo agente do domínio (`PipelineTransitionAgent + 3 sub-agents (Action/Decision/Context)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `suggest_next_action` | Sugere a próxima ação para um candidato no pipeline | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineTransitionAgent + 3 sub-agents (Action/Decision/Context)`) sem tool intermediária — usa LLM + serviços do domínio. |

### <a id='dom-recruiter_assistant'></a>recruiter_assistant

**Domínio:** `recruiter_assistant`  
**Classe:** `RecruiterAssistantDomain`  
**Agente principal:** KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent  
**Padrão de execução:** _ACTION_TOOL_MAP  
**Status:** production (DEFAULT_DOMAIN)  

_Assistente geral do recrutador (briefing, kanban, memória, alertas) — domínio default._

#### Actions (24)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `autonomous_actions` | Ver e gerenciar ações autônomas executadas pela LIA | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `calibrate_profile` | Calibrar o perfil ideal de candidato com feedback | Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `compare_candidates` | Comparação rápida entre candidatos | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `conversation_summary` | Gerar resumo da conversa atual | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_conversation_summary` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `daily_briefing` | Gerar briefing diário para o recrutador | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `end_of_day_summary` | Gerar resumo de fim de dia | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `generate_insights` | Gerar insights proativos de busca e recrutamento | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `help_command` | Mostrar comandos e funcionalidades disponíveis | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `kanban_analysis` | Análise por IA do quadro Kanban de recrutamento | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_kanban_analysis` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `learning_insights` | Ver o que a LIA aprendeu com contratações anteriores | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `move_candidate` | Mover candidato para uma etapa diferente do pipeline | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_move_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `pipeline_health` | Analisar a saúde do pipeline de recrutamento | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_pipeline_health` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `plan_day` | Ajudar o recrutador a planejar o dia | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `proactive_alerts` | Ver alertas proativos do pipeline (SLA, candidatos parados, gargalos) | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `quick_question` | Responder pergunta rápida do recrutador | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `recall_memory` | Recuperar informação da memória persistente | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_recall_memory` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `save_memory` | Salvar informação importante na memória persistente | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_save_memory` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `search_context` | Buscar no histórico de conversas por contexto relevante | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `assistant_search_context` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `send_notification` | Enviar notificação proativa para o recrutador | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `assistant_send_notification` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `stage_recommendation` | Recomendar próxima etapa para candidato | Avança o fluxo conversacional por etapas estruturadas. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `stakeholder_notify` | Detectar decisões pendentes e notificar hiring managers com escalação | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `stale_candidates` | Identificar candidatos inativos/parados no pipeline | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_stale_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_action` | Sugerir a próxima melhor ação para um candidato via IA | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `track_goals` | Acompanhar progresso das metas de recrutamento | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_track_goals` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |

#### Tools (10)

| tool_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `assistant_conversation_summary` | Gera resumo da conversa atual | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.recruiter_assistant.services.conversation_memory.conversation_memory.update_summary` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assistant_kanban_analysis` | Análise por IA do quadro Kanban de recrutamento | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.recruiter_assistant.services.kanban_assistant_service.kanban_assistant_service.process_command` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assistant_move_candidate` | Move candidato para uma etapa diferente do pipeline | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.recruiter_assistant.services.pipeline_stage_service.pipeline_stage_service.transition_candidate` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assistant_pipeline_health` | Verifica a saúde geral do pipeline de recrutamento | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.recruiter_assistant.services.pipeline_service.pipeline_service.get_stale_candidates` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assistant_recall_memory` | Recupera informação da memória persistente via busca semântica | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.recruiter_assistant.services.memory_service.memory_service.search_similar_messages` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assistant_save_memory` | Salva informação importante na memória persistente | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.recruiter_assistant.services.memory_service.memory_service.store_message` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assistant_search_context` | Busca no histórico de conversas por contexto relevante | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Handler `app.domains.recruiter_assistant.services.memory_service.memory_service.search_similar_messages` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assistant_send_notification` | Envia notificação proativa para o recrutador | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Handler `app.services.notification_service.notification_service.send_proactive_notification` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assistant_stale_candidates` | Encontra candidatos inativos/parados no pipeline | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.recruiter_assistant.services.pipeline_service.pipeline_service.get_stale_candidates` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `assistant_track_goals` | Acompanha progresso das metas de recrutamento | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.services.goal_service.goal_service.get_user_goals` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |

### <a id='dom-recruitment_campaign'></a>recruitment_campaign

**Domínio:** `recruitment_campaign`  
**Classe:** `RecruitmentCampaignDomain`  
**Agente principal:** —  
**Padrão de execução:** via agent  
**Status:** evolução  

_Campanhas multi-etapa de recrutamento (atração, engajamento, conversão)._

#### Actions (4)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `advance_campaign` | Avançar para próximo estágio | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_campaign` | Criar campanha de recrutamento para vaga ou pool | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_campaign_progress` | Ver estágio atual e próximos passos | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_campaigns` | Listar campanhas ativas | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |

### <a id='dom-sourcing'></a>sourcing

**Domínio:** `sourcing`  
**Classe:** `SourcingDomain`  
**Agente principal:** SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)  
**Padrão de execução:** _ACTION_TOOL_MAP  
**Status:** production  

_Busca ativa de candidatos (local, semantic, global, Pearch), enriquecimento, outreach._

#### Actions (36)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `add_candidate` | Cadastra novo candidato | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `add_candidate_to_vacancy` | Vincula candidato a uma vaga de emprego | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `sourcing_add_candidate_to_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `analyze_search_results` | Analisa efetividade da busca | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `assess_market` | Análise de mercado de talentos | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `sourcing_get_talent_quality` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `auto_source` | Pipeline automatizado | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `build_search_strategy` | Define estratégia de sourcing | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `check_volume` | Avalia volume de candidatos | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `compare_candidates` | Compara candidatos lado a lado | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `sourcing_get_candidate_details` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `contact_candidates` | Inicia outreach | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `dedup_candidates` | Remove candidatos duplicados | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `engagement_pipeline` | Fluxo de engajamento | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `enrich_profile` | Enriquece dados do candidato | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `expand_search` | Amplia critérios de busca | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `export_candidates` | Exporta lista de candidatos | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `feedback_search` | Registra feedback de resultados | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `filter_candidates` | Aplica filtros avançados | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `sourcing_search_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_boolean` | Gera query booleana | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_candidate_history` | Histórico de participação do candidato em processos seletivos | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `sourcing_get_candidate_history` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `get_candidate_stats` | Métricas e estatísticas sobre candidatos no pipeline | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `sourcing_get_candidate_stats` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `global_search` | Busca em todas as fontes | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `sourcing_search_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `import_candidates` | Importa de fonte externa | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `match_candidates` | Calcula compatibilidade | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `parse_cv` | Extrai dados de currículo | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `pearch_search` | Busca via Pearch AI | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `proactive_suggest` | Sugere ações proativas | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `rank_candidates` | Ordena por pontuação | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `sourcing_rank_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `reject_candidate` | Rejeita candidato no processo seletivo | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Mapeada para a tool `sourcing_reject_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `schedule_outreach` | Agenda contato futuro | Agenda interação ou tarefa no momento certo do funil. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `screen_candidates` | Screening inicial | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `search_candidates` | Busca candidatos com filtros | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `sourcing_search_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `semantic_search` | Busca por embeddings | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `shortlist_candidate` | Adiciona candidato à shortlist/favoritos | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `sourcing_shortlist_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_candidates` | Sugere candidatos para vaga | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `tag_candidates` | Adiciona tags aos candidatos | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `talent_pool_search` | Busca no pool interno | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `update_candidate_stage` | Move candidato para outra etapa do pipeline | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `sourcing_update_candidate_stage` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |

#### Tools (10)

| tool_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `sourcing_add_candidate_to_vacancy` | Adiciona um candidato a uma vaga de emprego | Materializa um novo registro/objeto solicitado pelo recrutador. | Handler `app.domains.cv_screening.tools.candidate_tools.add_candidate_to_vacancy` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `sourcing_get_candidate_details` | Obtém informações detalhadas de um candidato específico | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.sourcing.tools.query_tools.get_candidate_details` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `sourcing_get_candidate_history` | Consulta histórico de participação do candidato em processos | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.sourcing.tools.query_tools.get_candidate_history` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `sourcing_get_candidate_stats` | Obtém métricas e estatísticas sobre candidatos | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.sourcing.tools.query_tools.get_candidate_stats` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `sourcing_get_talent_quality` | Obtém métricas de qualidade dos talentos no pipeline | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.sourcing.tools.query_tools.get_talent_quality` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `sourcing_rank_candidates` | Ordena candidatos por pontuação usando Weighted Rank Fusion | Atende uma intenção específica do recrutador dentro do domínio. | Handler `app.domains.sourcing.tools.query_tools.rank_candidates` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `sourcing_reject_candidate` | Rejeita um candidato no processo seletivo | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Handler `app.domains.cv_screening.tools.candidate_tools.reject_candidate` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `sourcing_search_candidates` | Busca candidatos com filtros avançados (skills, experiência, localização, etc.) | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Handler `app.domains.sourcing.tools.query_tools.search_candidates` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `sourcing_shortlist_candidate` | Adiciona candidato à shortlist/favoritos | Devolve dados ao chat para o recrutador decidir o próximo passo. | Handler `app.domains.cv_screening.tools.candidate_tools.shortlist_candidate` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |
| `sourcing_update_candidate_stage` | Move um candidato para uma etapa diferente do pipeline de recrutamento | Persiste a alteração solicitada sem sair do chat. | Handler `app.domains.cv_screening.tools.candidate_tools.update_candidate_stage` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed). |

### <a id='dom-talent_pool'></a>talent_pool

**Domínio:** `talent_pool`  
**Classe:** `TalentPoolDomain`  
**Agente principal:** —  
**Padrão de execução:** via agent  
**Status:** evolução  

_Talent pools — criação, vínculo com vagas e geração de vagas a partir de pools._

#### Actions (6)

| action_id | O que faz | O que resolve | Como atua |
|---|---|---|---|
| `add_to_pool` | Adicionar candidatos ao banco de talentos | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_job_from_pool` | Criar vaga a partir de um banco de talentos (herda arquétipo) | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_talent_pool` | Criar novo banco de talentos vivo com arquétipo | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_pool_candidates` | Listar candidatos de um banco de talentos com estágios | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_talent_pools` | Listar bancos de talentos ativos | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `move_pool_to_job` | Migrar candidatos do pool para uma vaga | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |

---

## Índice Alfabético — Actions

| action_id | domínio |
|---|---|
| [`add_candidate`](#dom-sourcing) | `sourcing` |
| [`add_candidate_to_vacancy`](#dom-sourcing) | `sourcing` |
| [`add_to_pool`](#dom-talent_pool) | `talent_pool` |
| [`adjust_questions`](#dom-cv_screening) | `cv_screening` |
| [`advance_campaign`](#dom-recruitment_campaign) | `recruitment_campaign` |
| [`advance_wizard_step`](#dom-job_management) | `job_management` |
| [`analyze_funnel`](#dom-analytics) | `analytics` |
| [`analyze_jd`](#dom-job_management) | `job_management` |
| [`analyze_response`](#dom-interview_scheduling) | `interview_scheduling` |
| [`analyze_search_results`](#dom-sourcing) | `sourcing` |
| [`analyze_voice`](#dom-interview_scheduling) | `interview_scheduling` |
| [`analyze_website`](#dom-company_settings) | `company_settings` |
| [`answer_data_question`](#dom-analytics) | `analytics` |
| [`apply_template`](#dom-job_management) | `job_management` |
| [`approve_jd`](#dom-job_creation) | `job_creation` |
| [`approve_questions`](#dom-job_creation) | `job_creation` |
| [`assess_market`](#dom-sourcing) | `sourcing` |
| [`assess_seniority`](#dom-cv_screening) | `cv_screening` |
| [`assign_to_crew`](#dom-agent_studio) | `agent_studio` |
| [`auto_screen`](#dom-cv_screening) | `cv_screening` |
| [`auto_source`](#dom-sourcing) | `sourcing` |
| [`autonomous_actions`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`batch_screen`](#dom-cv_screening) | `cv_screening` |
| [`browse_marketplace`](#dom-agent_studio) | `agent_studio` |
| [`build_search_strategy`](#dom-sourcing) | `sourcing` |
| [`bulk_sync`](#dom-ats_integration) | `ats_integration` |
| [`calculate_wsi_score`](#dom-cv_screening) | `cv_screening` |
| [`calibrate`](#dom-job_creation) | `job_creation` |
| [`calibrate_agent`](#dom-agent_studio) | `agent_studio` |
| [`calibrate_model`](#dom-cv_screening) | `cv_screening` |
| [`calibrate_profile`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`cancel_interview`](#dom-interview_scheduling) | `interview_scheduling` |
| [`cancel_task`](#dom-automation) | `automation` |
| [`check_availability`](#dom-interview_scheduling) | `interview_scheduling` |
| [`check_proactive_alerts`](#dom-automation) | `automation` |
| [`check_saturation`](#dom-cv_screening) | `cv_screening` |
| [`check_sync_status`](#dom-ats_integration) | `ats_integration` |
| [`check_volume`](#dom-sourcing) | `sourcing` |
| [`classify_bloom`](#dom-cv_screening) | `cv_screening` |
| [`classify_dreyfus`](#dom-cv_screening) | `cv_screening` |
| [`clone_job`](#dom-job_management) | `job_management` |
| [`close_job`](#dom-job_management) | `job_management` |
| [`compare_candidates`](#dom-cv_screening) | `cv_screening` |
| [`compare_candidates`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`compare_candidates`](#dom-sourcing) | `sourcing` |
| [`compare_periods`](#dom-analytics) | `analytics` |
| [`complete_interview`](#dom-interview_scheduling) | `interview_scheduling` |
| [`complete_task`](#dom-automation) | `automation` |
| [`configure_alert`](#dom-automation) | `automation` |
| [`configure_ats`](#dom-ats_integration) | `ats_integration` |
| [`configure_automation`](#dom-hiring_policy) | `hiring_policy` |
| [`configure_benefits`](#dom-company_settings) | `company_settings` |
| [`configure_candidate_portal`](#dom-hiring_policy) | `hiring_policy` |
| [`configure_communication`](#dom-hiring_policy) | `hiring_policy` |
| [`configure_culture`](#dom-company_settings) | `company_settings` |
| [`configure_pipeline`](#dom-hiring_policy) | `hiring_policy` |
| [`configure_policy`](#dom-hiring_policy) | `hiring_policy` |
| [`configure_profile`](#dom-company_settings) | `company_settings` |
| [`configure_publish`](#dom-job_creation) | `job_creation` |
| [`configure_scheduling`](#dom-hiring_policy) | `hiring_policy` |
| [`configure_screening`](#dom-hiring_policy) | `hiring_policy` |
| [`configure_stage_automation`](#dom-automation) | `automation` |
| [`configure_tech_stack`](#dom-company_settings) | `company_settings` |
| [`configure_workforce`](#dom-company_settings) | `company_settings` |
| [`contact_candidates`](#dom-sourcing) | `sourcing` |
| [`conversation_summary`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`create_automation`](#dom-automation) | `automation` |
| [`create_campaign`](#dom-recruitment_campaign) | `recruitment_campaign` |
| [`create_custom_agent`](#dom-agent_studio) | `agent_studio` |
| [`create_from_template`](#dom-job_management) | `job_management` |
| [`create_job`](#dom-job_management) | `job_management` |
| [`create_job_from_pool`](#dom-talent_pool) | `talent_pool` |
| [`create_sourcing_agent`](#dom-agent_studio) | `agent_studio` |
| [`create_talent_pool`](#dom-talent_pool) | `talent_pool` |
| [`create_task`](#dom-automation) | `automation` |
| [`create_template`](#dom-communication) | `communication` |
| [`create_twin`](#dom-digital_twin) | `digital_twin` |
| [`daily_briefing`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`deactivate_agent`](#dom-agent_studio) | `agent_studio` |
| [`deactivate_twin`](#dom-digital_twin) | `digital_twin` |
| [`decompose_task`](#dom-automation) | `automation` |
| [`dedup_candidates`](#dom-sourcing) | `sourcing` |
| [`detect_anomalies`](#dom-analytics) | `analytics` |
| [`detect_criteria`](#dom-job_management) | `job_management` |
| [`detect_evasive`](#dom-interview_scheduling) | `interview_scheduling` |
| [`detect_red_flags`](#dom-cv_screening) | `cv_screening` |
| [`disable_automation`](#dom-automation) | `automation` |
| [`disable_webhook`](#dom-ats_integration) | `ats_integration` |
| [`duplicate_job`](#dom-job_management) | `job_management` |
| [`dynamic_cutoff`](#dom-cv_screening) | `cv_screening` |
| [`edit_template`](#dom-communication) | `communication` |
| [`enable_automation`](#dom-automation) | `automation` |
| [`enable_webhook`](#dom-ats_integration) | `ats_integration` |
| [`end_of_day_summary`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`engagement_pipeline`](#dom-sourcing) | `sourcing` |
| [`enrich_jd`](#dom-job_management) | `job_management` |
| [`enrich_profile`](#dom-sourcing) | `sourcing` |
| [`evaluate_rubric`](#dom-cv_screening) | `cv_screening` |
| [`evaluate_with_twin`](#dom-digital_twin) | `digital_twin` |
| [`execute_custom_agent`](#dom-agent_studio) | `agent_studio` |
| [`expand_search`](#dom-sourcing) | `sourcing` |
| [`explain_agent_studio`](#dom-agent_studio) | `agent_studio` |
| [`explain_score`](#dom-cv_screening) | `cv_screening` |
| [`export_candidates`](#dom-sourcing) | `sourcing` |
| [`extract_requirements`](#dom-job_management) | `job_management` |
| [`feedback_search`](#dom-sourcing) | `sourcing` |
| [`filter_candidates`](#dom-sourcing) | `sourcing` |
| [`find_common_slots`](#dom-interview_scheduling) | `interview_scheduling` |
| [`forecast`](#dom-analytics) | `analytics` |
| [`generate_boolean`](#dom-sourcing) | `sourcing` |
| [`generate_candidate_report`](#dom-analytics) | `analytics` |
| [`generate_followup`](#dom-interview_scheduling) | `interview_scheduling` |
| [`generate_insights`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`generate_jd`](#dom-job_management) | `job_management` |
| [`generate_job_report`](#dom-analytics) | `analytics` |
| [`generate_kpi_report`](#dom-analytics) | `analytics` |
| [`generate_questions`](#dom-cv_screening) | `cv_screening` |
| [`generate_report`](#dom-cv_screening) | `cv_screening` |
| [`generate_rubrics`](#dom-job_management) | `job_management` |
| [`generate_self_scheduling_link`](#dom-interview_scheduling) | `interview_scheduling` |
| [`generate_wsi_questions`](#dom-job_management) | `job_management` |
| [`get_agent_monitoring`](#dom-analytics) | `analytics` |
| [`get_agent_status`](#dom-agent_studio) | `agent_studio` |
| [`get_benefits`](#dom-job_management) | `job_management` |
| [`get_campaign_progress`](#dom-recruitment_campaign) | `recruitment_campaign` |
| [`get_candidate_history`](#dom-sourcing) | `sourcing` |
| [`get_candidate_stats`](#dom-sourcing) | `sourcing` |
| [`get_communication_history`](#dom-communication) | `communication` |
| [`get_dashboard_data`](#dom-analytics) | `analytics` |
| [`get_feedback`](#dom-candidate_self_service) | `candidate_self_service` |
| [`get_interview_info`](#dom-candidate_self_service) | `candidate_self_service` |
| [`get_job_insights`](#dom-analytics) | `analytics` |
| [`get_lgpd_info`](#dom-candidate_self_service) | `candidate_self_service` |
| [`get_next_tasks`](#dom-automation) | `automation` |
| [`get_pool_candidates`](#dom-talent_pool) | `talent_pool` |
| [`get_progress`](#dom-hiring_policy) | `hiring_policy` |
| [`get_search_analytics`](#dom-analytics) | `analytics` |
| [`get_status`](#dom-candidate_self_service) | `candidate_self_service` |
| [`get_studio_consumption`](#dom-agent_studio) | `agent_studio` |
| [`get_wizard_analytics`](#dom-analytics) | `analytics` |
| [`get_wizard_step_data`](#dom-job_management) | `job_management` |
| [`global_search`](#dom-sourcing) | `sourcing` |
| [`guided_wizard`](#dom-job_management) | `job_management` |
| [`handle_data_request`](#dom-communication) | `communication` |
| [`health_check`](#dom-job_management) | `job_management` |
| [`help`](#dom-job_creation) | `job_creation` |
| [`help_command`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`import_candidates`](#dom-sourcing) | `sourcing` |
| [`import_jd`](#dom-job_management) | `job_management` |
| [`index_twin_audio`](#dom-digital_twin) | `digital_twin` |
| [`install_from_marketplace`](#dom-agent_studio) | `agent_studio` |
| [`interpret_context`](#dom-pipeline_transition) | `pipeline_transition` |
| [`interview_qa`](#dom-interview_scheduling) | `interview_scheduling` |
| [`job_analytics`](#dom-job_management) | `job_management` |
| [`job_health_check`](#dom-analytics) | `analytics` |
| [`job_status_webhook`](#dom-job_management) | `job_management` |
| [`kanban_analysis`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`learning_insights`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`list_agents`](#dom-agent_studio) | `agent_studio` |
| [`list_automations`](#dom-automation) | `automation` |
| [`list_campaigns`](#dom-recruitment_campaign) | `recruitment_campaign` |
| [`list_connections`](#dom-ats_integration) | `ats_integration` |
| [`list_custom_agents`](#dom-agent_studio) | `agent_studio` |
| [`list_jobs`](#dom-job_management) | `job_management` |
| [`list_pipeline_stages`](#dom-pipeline_transition) | `pipeline_transition` |
| [`list_sector_templates`](#dom-agent_studio) | `agent_studio` |
| [`list_talent_pools`](#dom-talent_pool) | `talent_pool` |
| [`list_tasks`](#dom-automation) | `automation` |
| [`list_templates`](#dom-communication) | `communication` |
| [`list_today_interviews`](#dom-interview_scheduling) | `interview_scheduling` |
| [`list_twins`](#dom-digital_twin) | `digital_twin` |
| [`manage_webhook`](#dom-communication) | `communication` |
| [`map_big_five`](#dom-cv_screening) | `cv_screening` |
| [`map_fields`](#dom-ats_integration) | `ats_integration` |
| [`match_candidates`](#dom-sourcing) | `sourcing` |
| [`move_candidate`](#dom-pipeline_transition) | `pipeline_transition` |
| [`move_candidate`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`move_pool_to_job`](#dom-talent_pool) | `talent_pool` |
| [`normalize_scores`](#dom-cv_screening) | `cv_screening` |
| [`notify_stakeholders`](#dom-communication) | `communication` |
| [`parse_cv`](#dom-cv_screening) | `cv_screening` |
| [`parse_cv`](#dom-sourcing) | `sourcing` |
| [`pause_agent`](#dom-agent_studio) | `agent_studio` |
| [`pause_job`](#dom-job_management) | `job_management` |
| [`pearch_search`](#dom-sourcing) | `sourcing` |
| [`pipeline_health`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`plan_day`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`plan_execution`](#dom-automation) | `automation` |
| [`pre_qualify`](#dom-cv_screening) | `cv_screening` |
| [`predict_dropout_risk`](#dom-analytics) | `analytics` |
| [`predict_hiring_probability`](#dom-analytics) | `analytics` |
| [`predict_sub_status`](#dom-pipeline_transition) | `pipeline_transition` |
| [`predict_substatus`](#dom-automation) | `automation` |
| [`predict_time_to_fill`](#dom-analytics) | `analytics` |
| [`preview_template`](#dom-communication) | `communication` |
| [`proactive_alerts`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`proactive_suggest`](#dom-sourcing) | `sourcing` |
| [`process_document`](#dom-company_settings) | `company_settings` |
| [`publish_job`](#dom-job_creation) | `job_creation` |
| [`publish_job`](#dom-job_management) | `job_management` |
| [`publish_to_marketplace`](#dom-agent_studio) | `agent_studio` |
| [`pull_candidates`](#dom-ats_integration) | `ats_integration` |
| [`pull_jobs`](#dom-ats_integration) | `ats_integration` |
| [`qualify_job`](#dom-job_management) | `job_management` |
| [`quick_question`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`rank_candidates`](#dom-cv_screening) | `cv_screening` |
| [`rank_candidates`](#dom-sourcing) | `sourcing` |
| [`recalibrate_agent`](#dom-agent_studio) | `agent_studio` |
| [`recall_memory`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`reject_candidate`](#dom-sourcing) | `sourcing` |
| [`reschedule_interview`](#dom-interview_scheduling) | `interview_scheduling` |
| [`resolve_conflict`](#dom-ats_integration) | `ats_integration` |
| [`resolve_conflict`](#dom-interview_scheduling) | `interview_scheduling` |
| [`run_autonomous_check`](#dom-automation) | `automation` |
| [`run_multi_strategy`](#dom-agent_studio) | `agent_studio` |
| [`save_memory`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`schedule_interview`](#dom-interview_scheduling) | `interview_scheduling` |
| [`schedule_outreach`](#dom-sourcing) | `sourcing` |
| [`schedule_recurring`](#dom-automation) | `automation` |
| [`schedule_reminders`](#dom-interview_scheduling) | `interview_scheduling` |
| [`screen_candidates`](#dom-sourcing) | `sourcing` |
| [`search_candidates`](#dom-sourcing) | `sourcing` |
| [`search_context`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`search_templates`](#dom-job_management) | `job_management` |
| [`semantic_search`](#dom-sourcing) | `sourcing` |
| [`send_bulk_email`](#dom-communication) | `communication` |
| [`send_candidate_report`](#dom-communication) | `communication` |
| [`send_email`](#dom-communication) | `communication` |
| [`send_feedback`](#dom-communication) | `communication` |
| [`send_feedback`](#dom-cv_screening) | `cv_screening` |
| [`send_interview_invite`](#dom-communication) | `communication` |
| [`send_kpi_report`](#dom-communication) | `communication` |
| [`send_notification`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`send_progress_report`](#dom-communication) | `communication` |
| [`send_question`](#dom-interview_scheduling) | `interview_scheduling` |
| [`send_reminder`](#dom-interview_scheduling) | `interview_scheduling` |
| [`send_score_ats`](#dom-ats_integration) | `ats_integration` |
| [`send_screening_invite`](#dom-communication) | `communication` |
| [`send_sms`](#dom-communication) | `communication` |
| [`send_teams_message`](#dom-communication) | `communication` |
| [`send_whatsapp`](#dom-communication) | `communication` |
| [`set_eligibility`](#dom-job_creation) | `job_creation` |
| [`set_salary`](#dom-job_creation) | `job_creation` |
| [`set_screening_mode`](#dom-job_creation) | `job_creation` |
| [`shortlist_candidate`](#dom-sourcing) | `sourcing` |
| [`stage_recommendation`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`stakeholder_notify`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`stale_candidates`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`start_quick_screening`](#dom-interview_scheduling) | `interview_scheduling` |
| [`start_wizard`](#dom-job_creation) | `job_creation` |
| [`start_wsi_interview`](#dom-interview_scheduling) | `interview_scheduling` |
| [`suggest_action`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`suggest_candidates`](#dom-sourcing) | `sourcing` |
| [`suggest_compensation`](#dom-job_management) | `job_management` |
| [`suggest_jd_improvements`](#dom-job_management) | `job_management` |
| [`suggest_next_action`](#dom-pipeline_transition) | `pipeline_transition` |
| [`suggest_strategy`](#dom-analytics) | `analytics` |
| [`suggest_strategy`](#dom-job_management) | `job_management` |
| [`sync_candidate`](#dom-ats_integration) | `ats_integration` |
| [`sync_interview_result`](#dom-ats_integration) | `ats_integration` |
| [`sync_job`](#dom-ats_integration) | `ats_integration` |
| [`tag_candidates`](#dom-sourcing) | `sourcing` |
| [`talent_pool_search`](#dom-sourcing) | `sourcing` |
| [`test_connection`](#dom-ats_integration) | `ats_integration` |
| [`test_custom_agent`](#dom-agent_studio) | `agent_studio` |
| [`track_goals`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`transcribe_audio`](#dom-interview_scheduling) | `interview_scheduling` |
| [`trigger_automation`](#dom-automation) | `automation` |
| [`uninstall_agent`](#dom-agent_studio) | `agent_studio` |
| [`update_candidate_stage`](#dom-sourcing) | `sourcing` |
| [`update_job`](#dom-job_management) | `job_management` |
| [`update_preferences`](#dom-communication) | `communication` |
| [`update_status_ats`](#dom-ats_integration) | `ats_integration` |
| [`validate_cbi`](#dom-cv_screening) | `cv_screening` |
| [`validate_compliance`](#dom-hiring_policy) | `hiring_policy` |
| [`view_automation_log`](#dom-automation) | `automation` |
| [`view_field_mapping`](#dom-ats_integration) | `ats_integration` |
| [`view_sync_log`](#dom-ats_integration) | `ats_integration` |
| [`view_task_dependencies`](#dom-automation) | `automation` |
| [`voice_screening`](#dom-cv_screening) | `cv_screening` |
| [`wizard_status`](#dom-job_creation) | `job_creation` |

## Índice Alfabético — Tools

| tool_id | domínio |
|---|---|
| [`adjust_wsi_questions`](#dom-cv_screening) | `cv_screening` |
| [`advance_wizard`](#dom-job_management) | `job_management` |
| [`analytics_analyze_funnel`](#dom-analytics) | `analytics` |
| [`analytics_dashboard`](#dom-analytics) | `analytics` |
| [`analytics_detect_anomalies`](#dom-analytics) | `analytics` |
| [`analytics_generate_kpi`](#dom-analytics) | `analytics` |
| [`analytics_generate_report`](#dom-analytics) | `analytics` |
| [`analytics_get_insights`](#dom-analytics) | `analytics` |
| [`analytics_job_health`](#dom-analytics) | `analytics` |
| [`analytics_monitoring`](#dom-analytics) | `analytics` |
| [`analytics_predict`](#dom-analytics) | `analytics` |
| [`analytics_search_analytics`](#dom-analytics) | `analytics` |
| [`assess_seniority`](#dom-cv_screening) | `cv_screening` |
| [`assistant_conversation_summary`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`assistant_kanban_analysis`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`assistant_move_candidate`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`assistant_pipeline_health`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`assistant_recall_memory`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`assistant_save_memory`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`assistant_search_context`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`assistant_send_notification`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`assistant_stale_candidates`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`assistant_track_goals`](#dom-recruiter_assistant) | `recruiter_assistant` |
| [`ats_check_status`](#dom-ats_integration) | `ats_integration` |
| [`ats_list_connections`](#dom-ats_integration) | `ats_integration` |
| [`ats_pull_candidates`](#dom-ats_integration) | `ats_integration` |
| [`ats_pull_jobs`](#dom-ats_integration) | `ats_integration` |
| [`ats_send_score`](#dom-ats_integration) | `ats_integration` |
| [`ats_sync_candidate`](#dom-ats_integration) | `ats_integration` |
| [`ats_sync_job`](#dom-ats_integration) | `ats_integration` |
| [`ats_test_connection`](#dom-ats_integration) | `ats_integration` |
| [`ats_update_status`](#dom-ats_integration) | `ats_integration` |
| [`ats_view_sync_log`](#dom-ats_integration) | `ats_integration` |
| [`automation_cancel_task`](#dom-automation) | `automation` |
| [`automation_complete_task`](#dom-automation) | `automation` |
| [`automation_create_rule`](#dom-automation) | `automation` |
| [`automation_create_task`](#dom-automation) | `automation` |
| [`automation_disable_rule`](#dom-automation) | `automation` |
| [`automation_enable_rule`](#dom-automation) | `automation` |
| [`automation_list_rules`](#dom-automation) | `automation` |
| [`automation_list_tasks`](#dom-automation) | `automation` |
| [`automation_trigger`](#dom-automation) | `automation` |
| [`automation_view_log`](#dom-automation) | `automation` |
| [`calculate_wsi`](#dom-cv_screening) | `cv_screening` |
| [`clone_job_vacancy`](#dom-job_management) | `job_management` |
| [`close_job_vacancy`](#dom-job_management) | `job_management` |
| [`communication_create_template`](#dom-communication) | `communication` |
| [`communication_data_request`](#dom-communication) | `communication` |
| [`communication_get_history`](#dom-communication) | `communication` |
| [`communication_list_templates`](#dom-communication) | `communication` |
| [`communication_manage_webhook`](#dom-communication) | `communication` |
| [`communication_preview_template`](#dom-communication) | `communication` |
| [`communication_send_bulk`](#dom-communication) | `communication` |
| [`communication_send_email`](#dom-communication) | `communication` |
| [`communication_send_teams`](#dom-communication) | `communication` |
| [`communication_send_whatsapp`](#dom-communication) | `communication` |
| [`create_job_vacancy`](#dom-job_management) | `job_management` |
| [`duplicate_job_vacancy`](#dom-job_management) | `job_management` |
| [`enrich_job_description`](#dom-job_management) | `job_management` |
| [`evaluate_rubric`](#dom-cv_screening) | `cv_screening` |
| [`generate_job_description`](#dom-job_management) | `job_management` |
| [`generate_wsi_questions`](#dom-cv_screening) | `cv_screening` |
| [`get_job_analytics`](#dom-job_management) | `job_management` |
| [`get_job_health`](#dom-job_management) | `job_management` |
| [`get_wizard_step`](#dom-job_management) | `job_management` |
| [`import_job_description`](#dom-job_management) | `job_management` |
| [`normalize_scores`](#dom-cv_screening) | `cv_screening` |
| [`parse_cv`](#dom-cv_screening) | `cv_screening` |
| [`pause_job_vacancy`](#dom-job_management) | `job_management` |
| [`pre_qualify_candidate`](#dom-cv_screening) | `cv_screening` |
| [`run_screening_pipeline`](#dom-cv_screening) | `cv_screening` |
| [`scheduling_analyze_voice`](#dom-interview_scheduling) | `interview_scheduling` |
| [`scheduling_cancel`](#dom-interview_scheduling) | `interview_scheduling` |
| [`scheduling_check_availability`](#dom-interview_scheduling) | `interview_scheduling` |
| [`scheduling_find_slots`](#dom-interview_scheduling) | `interview_scheduling` |
| [`scheduling_list_today`](#dom-interview_scheduling) | `interview_scheduling` |
| [`scheduling_reschedule`](#dom-interview_scheduling) | `interview_scheduling` |
| [`scheduling_schedule_interview`](#dom-interview_scheduling) | `interview_scheduling` |
| [`scheduling_self_scheduling_link`](#dom-interview_scheduling) | `interview_scheduling` |
| [`scheduling_send_reminder`](#dom-interview_scheduling) | `interview_scheduling` |
| [`scheduling_transcribe_audio`](#dom-interview_scheduling) | `interview_scheduling` |
| [`search_job_templates`](#dom-job_management) | `job_management` |
| [`send_candidate_feedback`](#dom-cv_screening) | `cv_screening` |
| [`sourcing_add_candidate_to_vacancy`](#dom-sourcing) | `sourcing` |
| [`sourcing_get_candidate_details`](#dom-sourcing) | `sourcing` |
| [`sourcing_get_candidate_history`](#dom-sourcing) | `sourcing` |
| [`sourcing_get_candidate_stats`](#dom-sourcing) | `sourcing` |
| [`sourcing_get_talent_quality`](#dom-sourcing) | `sourcing` |
| [`sourcing_rank_candidates`](#dom-sourcing) | `sourcing` |
| [`sourcing_reject_candidate`](#dom-sourcing) | `sourcing` |
| [`sourcing_search_candidates`](#dom-sourcing) | `sourcing` |
| [`sourcing_shortlist_candidate`](#dom-sourcing) | `sourcing` |
| [`sourcing_update_candidate_stage`](#dom-sourcing) | `sourcing` |
| [`update_job_vacancy`](#dom-job_management) | `job_management` |

---

_Última geração programática a partir do registry. Para regenerar, rode `python3 scripts/generate_glossario_actions_tools.py` a partir de `lia-agent-system/`._
