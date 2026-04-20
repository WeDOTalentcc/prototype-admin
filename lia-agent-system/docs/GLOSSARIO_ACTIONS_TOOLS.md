# Glossário de Actions e Tools — Plataforma LIA
> **Fonte da verdade:** geração programática a partir do `DomainRegistry` ao vivo + descrições declaradas em cada `DomainAction`/`tool_id`.
> **Geração:** `python3 scripts/generate_glossario_actions_tools.py` (regenerar quando registries mudarem).  
> **Documentos relacionados:** [`MAPA_CAMADA_INTELIGENCIA.md`](./MAPA_CAMADA_INTELIGENCIA.md) (fluxos), [`fase2c_domain_verification_report.md`](./fase2c_domain_verification_report.md) (auditoria viva), [`../ARCHITECTURE.md`](../ARCHITECTURE.md) (ADRs normativos).

---

## Índice — 18 domínios, 281 actions, 94 tools
> **Contagem de tools:** 88 tools declaradas em `app/tools/tool_registry_metadata.yaml` (com template rico completo, validadas pelo CI) + 6 tools Python-only em agent registries de domínios "via agent". Total: 94.

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
| `assign_to_crew` | Atribui agente customizado como role especializado em uma crew de agentes para fluxos complexos. Aciona na configuração de crews de automação avançada. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `browse_marketplace` | Navega e busca agentes disponíveis no marketplace por categoria ou nome. Aciona quando recruiter quer expandir capacidades com agentes prontos de outros tenants. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `calibrate_agent` | Inicia calibração do agente de sourcing avaliando perfis de candidatos com o recrutador para ajustar os critérios de seleção. Aciona quando o agente está trazendo candidatos fora do perfil ou após 20+ avaliações manuais. | Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_custom_agent` | Cria agente customizado com nome, role, system prompt e tools específicas para automatizar fluxos do recrutamento. Aciona quando recruiter quer um assistente especializado para tarefa recorrente específica. | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_sourcing_agent` | Cria um agente de sourcing especializado usando template de setor (tech, saúde, finanças, etc). O agente aprendido aplica critérios de seleção ajustados ao perfil da vaga. Aciona quando recruiter quer automatizar sourcing para uma vaga ou pool específico. | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `deactivate_agent` | Desativa agente de sourcing ou custom liberando quota da empresa. Requer confirmação. Aciona quando agente não é mais necessário ou quota precisa ser liberada. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `execute_custom_agent` | Executa agente customizado em produção com a mensagem ou contexto fornecido. Aciona quando recruiter chama o agente pelo nome no chat ou via automação. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `explain_agent_studio` | Explica o que é o Agent Studio, como criar e gerenciar agentes de sourcing e customizados. Aciona quando recruiter pergunta 'o que é o Agent Studio?' ou como começar. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_agent_status` | Obtém status atual do agente de sourcing: estratégia ativa, candidatos processados, taxa de aprovação e métricas de performance. Aciona quando recruiter quer saber como o agente está performando. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_studio_consumption` | Obtém consumo de tokens e créditos dos agentes do Studio no período. Aciona quando recruiter quer controlar custos ou entender billing de agentes. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `install_from_marketplace` | Instala agente do marketplace na empresa, adicionando-o à lista de agentes disponíveis. Requer confirmação e consome quota. Aciona ao selecionar agente no marketplace. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_agents` | Lista todos os agentes de sourcing ativos da empresa com seu status, estratégia e métricas resumidas. Aciona quando recruiter quer gerenciar seus agentes ou verificar quais estão rodando. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_custom_agents` | Lista agentes customizados criados pela empresa com status (ativo/pausado), domínio e última execução. Aciona para gerenciamento de agentes customizados do tenant. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_sector_templates` | Lista templates de setor disponíveis para criação de agentes de sourcing com critérios pré-configurados por indústria. Aciona quando recruiter escolhe criar um novo agente e quer ver opções disponíveis. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `pause_agent` | Pausa agente de sourcing interrompendo buscas automáticas (libera quota). Requer confirmação. Aciona quando recruiter quer pausar busca temporariamente ou há vagas suficientes no pipeline. | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `publish_to_marketplace` | Publica agente customizado no marketplace para ser instalado por outras empresas da plataforma. Requer confirmação. Aciona quando agente tem qualidade suficiente e empresa quer monetizá-lo. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `recalibrate_agent` | Recalibra agente com novo feedback do recrutador para ajustar critérios de seleção após novas contratações. Aciona quando há mudança no perfil da vaga ou após feedback negativo dos últimos candidatos selecionados. | Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `run_multi_strategy` | Executa busca inteligente com 4 estratégias paralelas (semântica, booleana, pearch, talent pool) para maximizar cobertura de candidatos. Aciona quando busca simples não encontrou candidatos suficientes. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `test_custom_agent` | Testa agente customizado com uma mensagem de exemplo antes de colocar em produção. Aciona durante criação ou após edição de agente customizado. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `uninstall_agent` | Desinstala agente instalado do marketplace liberando quota. Requer confirmação. Aciona quando agente não é mais utilizado. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |

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
| `analyze_funnel` | Analisa as métricas do funil de conversão de recrutamento etapa por etapa (candidaturas → triagem → entrevista → oferta). Identifica gargalos e etapas com maior perda. Aciona ao detectar queda de candidatos ou pedir análise de funil. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_analyze_funnel` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `answer_data_question` | Responde perguntas abertas sobre dados e analytics de recrutamento usando linguagem natural. Aciona para qualquer pergunta analítica: 'quantos candidatos passaram?', 'qual a taxa de aprovação?', 'quando a vaga vai fechar?'. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_get_insights` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `compare_periods` | Compara métricas de recrutamento entre dois períodos de tempo distintos (semana, mês, trimestre). Identifica tendências positivas e negativas. Aciona quando recruiter pergunta 'este mês vs o anterior' ou análises sazonais. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_dashboard` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `detect_anomalies` | Detecta anomalias estatísticas nos dados de recrutamento — picos, quedas abruptas, métricas fora do padrão histórico. Aciona automaticamente ou quando recruiter suspeita de problema de qualidade de dados. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_detect_anomalies` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `forecast` | Prevê métricas e tendências de recrutamento para os próximos dias/semanas usando modelos de IA. Aciona quando recruiter planeja capacidade, quer estimar time-to-fill ou simular cenários futuros. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_predict` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_candidate_report` | Gera relatório comparativo de candidatos selecionados com scores WSI, competências e recomendação final. Aciona antes de apresentar shortlist ao hiring manager ou para decisão de oferta. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_generate_report` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_job_report` | Gera relatório completo da vaga em formato PDF ou Excel com histórico de candidatos, métricas e análise de pipeline. Aciona quando recruiter precisa apresentar resultados ao cliente ou ao hiring manager. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_generate_report` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_kpi_report` | Gera relatório consolidado de KPIs de recrutamento (tempo de preenchimento, taxa de aprovação, volume de candidatos) para uma vaga ou período. Aciona quando o recrutador pede métricas, indicadores ou relatório gerencial. Saída: documento com gráficos e tabelas. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_generate_kpi` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_agent_monitoring` | Monitora o desempenho dos agentes de IA: chamadas, latência, taxa de sucesso, uso de tokens e erros recentes. Aciona para diagnóstico de problemas com agentes ou análise de custos. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `analytics_monitoring` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_dashboard_data` | Obtém indicadores estratégicos do dashboard principal: vagas ativas, pipeline geral, alertas e KPIs do período. Aciona ao abrir o dashboard ou pedir visão geral do recrutamento. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `analytics_dashboard` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_job_insights` | Obtém insights combinados da vaga: benchmarks salariais do mercado, competências mais demandadas e vagas similares publicadas. Aciona quando recruiter quer contextualizar a vaga ou negociar salário. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `analytics_get_insights` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_search_analytics` | Obtém analytics de desempenho das buscas de candidatos: taxa de match, qualidade dos resultados, estratégias mais eficazes. Aciona quando recruiter avalia efetividade do sourcing. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `analytics_search_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `get_wizard_analytics` | Obtém métricas de uso do wizard de criação de vagas: tempo médio, etapas com mais abandono, campos mais editados. Aciona para análise de UX e melhoria de processo. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `analytics_search_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `job_health_check` | Verifica indicadores de saúde da vaga em tempo real: volume de candidatos, taxa de triagem, SLAs, saturação do pipeline e alertas de risco. Aciona ao abrir a vaga no dashboard ou quando recruiter pede 'como está a vaga?'. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_job_health` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `predict_dropout_risk` | Prevê o risco de desistência do candidato em cada etapa do pipeline usando IA. Aciona para intervir proativamente com candidatos de alto risco antes da perda. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_predict` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `predict_hiring_probability` | Prevê via IA a probabilidade de sucesso na contratação para uma vaga ou candidato específico, baseado em dados históricos de vagas similares. Aciona quando recruiter quer priorizar vagas ou candidatos. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_predict` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `predict_time_to_fill` | Estima o tempo necessário para preencher uma posição com base em histórico de vagas similares, mercado e pipeline atual. Aciona quando recruiter planeja prazo de entrega para o cliente. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `analytics_predict` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_strategy` | Sugere mudanças de estratégia de recrutamento baseadas em dados históricos e benchmarks do mercado via IA. Aciona quando recruiter pede recomendações, plano de ação ou está com a vaga parada. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `analytics_get_insights` em `_ACTION_TOOL_MAP`; executada via `execute_analytics_tool` → handler resolvido por `resolve_handler_path`. |

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
| `bulk_sync` | Executa sincronização em massa de múltiplos candidatos ou vagas com o ATS externo. Requer confirmação. Aciona para sincronização inicial ou reconciliação periódica entre sistemas. | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_sync_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `check_sync_status` | Verifica o status atual de sincronização com o ATS: pendentes, erros, última execução e taxa de sucesso. Aciona para diagnóstico de problemas de integração ou verificação pós-sincronização. | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_check_status` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `configure_ats` | Configura conexão e credenciais do ATS externo (API key, endpoint, mapeamentos). Requer confirmação. Aciona durante setup inicial de integração ou quando credenciais mudam. | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `ats_list_connections` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `disable_webhook` | Desativa webhook de sincronização com o ATS parando eventos em tempo real. Aciona quando integração precisa ser suspensa temporariamente ou webhook está causando erros. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_test_connection` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `enable_webhook` | Ativa webhook para sincronização em tempo real entre o ATS e a plataforma LIA para eventos específicos. Aciona durante configuração de integração para automação de sincronização bidirecional. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_test_connection` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `list_connections` | Lista todas as conexões ATS configuradas pela empresa com status de saúde e última sincronização. Aciona para gerenciamento de integrações ou escolha de conexão ativa. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `ats_list_connections` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `map_fields` | Configura o mapeamento de campos entre o WedoTalent e o ATS externo para garantir que dados fluam corretamente. Requer confirmação. Aciona durante configuração ou quando campos mudam no ATS. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_view_sync_log` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `pull_candidates` | Importa candidatos do ATS externo para o WedoTalent, criando ou atualizando perfis existentes. Aciona quando recruiter quer trazer dados do ATS para usar nas ferramentas de triagem da LIA. | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_pull_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `pull_jobs` | Importa vagas do ATS externo para o WedoTalent, sincronizando requisitos e status. Aciona para iniciar gestão de vagas existentes no ATS usando a plataforma LIA. | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_pull_jobs` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `resolve_conflict` | Resolve conflitos de dados detectados entre WedoTalent e ATS externo, escolhendo qual sistema prevalece. Requer confirmação. Aciona quando sync report indica dados divergentes. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_view_sync_log` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `send_score_ats` | Envia score e parecer WSI do candidato para o campo correspondente no ATS externo. Aciona após avaliação WSI quando há integração ativa configurada. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `ats_send_score` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `sync_candidate` | Sincroniza dados de um candidato com o ATS externo (Greenhouse, Lever, etc.), propagando atualizações de status, score WSI e dados de perfil. Aciona após mudança de etapa ou avaliação de candidato quando há integração ativa. | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_sync_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `sync_interview_result` | Sincroniza resultados de entrevista (scorecard, notas, recomendação) com o ATS externo. Aciona após conclusão de entrevista estruturada quando integração está ativa. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `ats_send_score` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `sync_job` | Sincroniza dados de uma vaga com o ATS externo, incluindo requisitos, status e configurações de pipeline. Aciona após criação ou atualização de vaga quando há integração ATS configurada. | Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia. | Mapeada para a tool `ats_sync_job` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `test_connection` | Testa a saúde da conexão com o ATS verificando autenticação e disponibilidade do endpoint. Aciona antes de sincronizações críticas ou para diagnóstico de falhas de conexão. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `ats_test_connection` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `update_status_ats` | Envia atualização de status do candidato (aprovado, rejeitado, em processo) para o ATS externo em tempo real. Aciona automaticamente após mudança de etapa quando integração está ativa. | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `ats_update_status` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `view_field_mapping` | Visualiza o mapeamento atual de campos entre WedoTalent e o ATS externo. Aciona para auditoria, verificação de configuração ou antes de alterar mapeamentos. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `ats_view_sync_log` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |
| `view_sync_log` | Visualiza o log de auditoria de sincronização com registros de operações, erros e dados trocados. Aciona para auditoria, compliance ou debug de sincronizações que falharam. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `ats_view_sync_log` em `_ACTION_TOOL_MAP`; executada via `execute_ats_integration_tool` → handler resolvido por `resolve_handler_path`. |

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
| `cancel_task` | Cancela tarefa pendente com motivo, liberando recursos alocados e notificando tarefas dependentes. Requer confirmação. Aciona quando tarefa não é mais necessária ou contexto mudou. | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Mapeada para a tool `automation_cancel_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `check_proactive_alerts` | Verifica alertas proativos ativos para o recrutador: SLAs vencidos, candidatos parados, vagas sem movimento. Aciona no briefing diário ou quando recruiter pede 'o que precisa de atenção?'. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_view_log` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `complete_task` | Marca tarefa como concluída registrando o resultado e liberando tarefas dependentes bloqueadas. Requer confirmação. Aciona ao finalizar execução de uma subtarefa no fluxo de automação. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_complete_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `configure_alert` | Configura regras de alertas proativos com threshold, canal de notificação e frequência. Requer confirmação. Aciona quando recruiter quer personalizar quais alertas receber. | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `automation_create_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `configure_stage_automation` | Configura automação de transição de etapa do pipeline (ex: ao aprovado em triagem → enviar convite de entrevista). Requer confirmação. Aciona na configuração de fluxos automáticos de pipeline. | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `automation_create_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `create_automation` | Cria nova regra de automação que dispara ações automaticamente baseado em eventos do pipeline (mudança de etapa, SLA vencido, etc.). Requer confirmação. Aciona quando recruiter quer automatizar tarefa recorrente. | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `automation_create_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `create_task` | Cria nova tarefa planejada no sistema de automação com título, descrição, agente responsável e prazo. Aciona quando recruiter ou orquestrador precisa registrar uma atividade para execução futura ou delegação. | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `automation_create_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `decompose_task` | Decompõe tarefa complexa em subtarefas menores via IA, atribuindo agente responsável, prioridade e dependências para cada uma. Aciona ao receber objetivo de alto nível que requer orquestração multi-agente. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_create_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `disable_automation` | Desativa regra de automação parando execuções automáticas sem excluí-la. Requer confirmação. Aciona para pausar automação temporariamente ou quando está causando comportamento indesejado. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_disable_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `enable_automation` | Ativa regra de automação previamente criada para que comece a disparar ações automaticamente. Requer confirmação. Aciona quando automação está pronta para produção. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_enable_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `get_next_tasks` | Obtém próximas tarefas prontas para execução (todas as dependências concluídas) filtradas por agente e objetivo. Aciona no loop de execução autônoma para buscar trabalho disponível. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_list_tasks` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `list_automations` | Lista regras de automação configuradas pela empresa com status ativo/inativo e métricas de execução. Aciona para gestão das automações existentes ou verificar o que está rodando. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_list_rules` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `list_tasks` | Lista tarefas ativas e seus status (pendente, em execução, concluída, bloqueada) para o objetivo atual. Aciona quando recruiter quer ver o progresso do pipeline de automação ou tarefas pendentes. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_list_tasks` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `plan_execution` | Cria plano de execução validado com níveis paralelos e mapa de dependências para um conjunto de tarefas. Aciona após decomposição para preparar pipeline de execução autônoma. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_create_task` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `predict_substatus` | Prevê via IA o próximo sub-status mais provável para um candidato baseado no histórico e comportamento. Aciona para sugestões proativas de próxima ação ou alertas de risco de perda. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `automation_view_log` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `run_autonomous_check` | Executa verificação autônoma de background check de candidato via agente de IA. Requer confirmação. Aciona para validação de informações de candidatos finalistas. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_trigger` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `schedule_recurring` | Agenda tarefa recorrente de automação com frequência (diária, semanal, mensal). Requer confirmação. Aciona para criar relatórios automáticos ou verificações periódicas. | Agenda interação ou tarefa no momento certo do funil. | Mapeada para a tool `automation_create_rule` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `trigger_automation` | Dispara manualmente uma automação configurada para execução imediata fora do gatilho automático. Requer confirmação. Aciona para teste de automação ou execução manual pontual. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `automation_trigger` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `view_automation_log` | Visualiza histórico de execuções de automações com timestamps, resultados e erros. Aciona para auditoria, debug de automações falhas ou compliance. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_view_log` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |
| `view_task_dependencies` | Visualiza o grafo de dependências das tarefas planejadas mostrando ordem de execução e bloqueios. Aciona para debug de pipeline travado ou para entender sequência de automação. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `automation_list_tasks` em `_ACTION_TOOL_MAP`; executada via `execute_automation_tool` → handler resolvido por `resolve_handler_path`. |

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
| `create_template` | Cria novo template de email reutilizável para comunicações padronizadas (convite, rejeição, oferta, etc.). Aciona quando recruiter precisa de novo template para situação não coberta pelos existentes. | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `communication_create_template` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `edit_template` | Edita template de email existente com novo conteúdo, assunto ou personalização. Aciona para atualizar comunicações desatualizadas ou personalizar templates padrão da empresa. | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_communication_history` | Obtém histórico completo de comunicações com um candidato (emails, WhatsApp, SMS) com timestamps e status de entrega. Aciona para contexto antes de nova comunicação ou auditoria de interações. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `communication_get_history` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `handle_data_request` | Processa solicitação de dados pessoais ou exclusão (LGPD/GDPR) do candidato, registrando no audit trail. Requer confirmação. Aciona quando candidato exerce direito de acesso ou exclusão de dados. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `communication_data_request` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `list_templates` | Lista templates de email disponíveis filtrados por tipo (candidato, gestor, sistema) e status. Aciona quando recruiter quer escolher template para comunicação ou gerenciar biblioteca. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `communication_list_templates` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `manage_webhook` | Configura e gerencia webhooks de comunicação para integração com ferramentas externas (Zapier, n8n, ATS). Aciona na configuração de integrações de comunicação automática. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `communication_manage_webhook` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `notify_stakeholders` | Envia notificação para stakeholders (hiring manager, HRBP, cliente) sobre eventos críticos do processo seletivo. Requer confirmação. Aciona em marcos importantes: candidato aprovado, vaga fechada, oferta aceita. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `preview_template` | Pré-visualiza template de email com dados reais do candidato antes de enviar. Aciona antes de envio para verificar personalização e conteúdo estão corretos. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `communication_preview_template` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `send_bulk_email` | Envia email em massa para múltiplos destinatários simultaneamente usando template selecionado com personalização por candidato. Requer confirmação. Aciona para comunicações em lote como rejeições ou avanços de processo. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `communication_send_bulk` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `send_candidate_report` | Envia relatório ou parecer completo do candidato para o gestor contratante com score WSI, pontos fortes e recomendação. Requer confirmação. Aciona ao avançar candidato para entrevista com hiring manager. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_email` | Envia email individual personalizado para candidato ou stakeholder usando templates ou texto livre. Requer confirmação. Aciona quando recruiter pede para enviar email, comunicar resultado ou fazer follow-up. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `communication_send_email` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `send_feedback` | Envia feedback personalizado ao candidato sobre o resultado do processo seletivo, respeitando LGPD. Requer confirmação. Aciona quando candidato é rejeitado e recruiter quer dar devolutiva de qualidade. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_interview_invite` | Envia convite de entrevista ao candidato com data, horário, formato e informações do entrevistador. Requer confirmação. Aciona após scheduling confirmar horário disponível. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_kpi_report` | Envia relatório consolidado de KPIs de recrutamento para liderança ou cliente. Requer confirmação. Aciona em ciclos semanais/mensais de reporting ou quando solicitado por stakeholder. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_progress_report` | Envia relatório de andamento da vaga para stakeholders com métricas atuais, pipeline e próximos passos. Aciona para comunicação proativa com clientes ou quando gestor pede atualização de status. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_screening_invite` | Envia convite para triagem WSI ao candidato com link e instruções. Requer confirmação. Aciona após aprovação de candidato na primeira etapa de análise de currículo. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_sms` | Envia SMS para candidato para lembretes ou confirmações urgentes. Requer confirmação. Aciona quando tempo de resposta é crítico ou candidato não respondeu ao email. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_teams_message` | Envia mensagem via Microsoft Teams para recruiter ou stakeholder interno. Requer confirmação. Aciona para notificações urgentes de equipe interna ou comunicações com hiring manager via Teams. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `communication_send_teams` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `send_whatsapp` | Envia mensagem via WhatsApp para candidato usando template aprovado ou mensagem personalizada. Requer confirmação. Aciona quando candidato prefere WhatsApp ou resposta rápida é necessária. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `communication_send_whatsapp` em `_ACTION_TOOL_MAP`; executada via `execute_communication_tool` → handler resolvido por `resolve_handler_path`. |
| `update_preferences` | Atualiza preferências de comunicação do candidato: canal preferido (email/WhatsApp/SMS) e horários. Aciona quando candidato solicita mudança de canal ou previamente à primeira comunicação. | Persiste a alteração solicitada sem sair do chat. | Executada diretamente pelo agente do domínio (`CommunicationReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |

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
| `adjust_questions` | Ajusta e refina perguntas de triagem com IA baseado em feedback do recruiter ou resultados anteriores. Aciona quando perguntas estão muito fáceis/difíceis ou não discriminam candidatos. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `adjust_wsi_questions` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `assess_seniority` | Avalia e classifica o nível de senioridade do candidato (júnior, pleno, sênior, especialista) com base no CV e respostas. Aciona para alocação correta em vagas de nível específico. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assess_seniority` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `auto_screen` | Executa triagem automática do candidato contra os requisitos da vaga usando score WSI e rubricas configuradas. Aciona após parse_cv para aprovação/rejeição automática com base em critérios objetivos. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `batch_screen` | Executa triagem em lote de múltiplos candidatos simultaneamente para ranqueamento eficiente. Aciona quando há acúmulo de candidaturas ou para triagem semanal de novos candidatos. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `calculate_wsi_score` | Calcula o score WSI (Work Style Interview) do candidato baseado no CV e competências mapeadas para a vaga. Aciona após parse_cv ou quando recruiter quer pontuação para comparação. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `calculate_wsi` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `calibrate_model` | Calibra o modelo de triagem com feedback explícito do recrutador sobre candidatos aprovados e rejeitados. Aciona periodicamente para melhorar precisão da triagem automática. | Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `check_saturation` | Verifica se o pipeline de candidatos está saturado com volume suficiente para preenchimento da vaga. Aciona para decidir se sourcing deve continuar ou pausar. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `classify_bloom` | Classifica respostas do candidato pela Taxonomia de Bloom para avaliar profundidade de raciocínio (do básico ao criativo). Aciona durante avaliação de respostas de entrevistas estruturadas. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `classify_dreyfus` | Classifica o nível de proficiência do candidato no modelo Dreyfus (novice → expert) para competências técnicas. Aciona na avaliação de seniority para vagas técnicas. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `compare_candidates` | Compara candidatos selecionados lado a lado em dimensões de competência, score e fit cultural. Aciona quando recruiter tem múltiplos finalistas e precisa decidir quem avançar. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `detect_red_flags` | Detecta red flags no currículo: gaps não explicados, inconsistências de datas, histórico de rotatividade elevada. Aciona durante triagem para alertar recruiter sobre riscos antes de avançar candidato. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `dynamic_cutoff` | Aplica corte dinâmico ao pipeline retendo apenas o top 25% dos candidatos com base nos scores. Aciona quando pipeline está saturado e recruiter precisa focar nos melhores candidatos. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `evaluate_rubric` | Avalia candidato por rubrica estruturada com critérios e pesos específicos da vaga. Aciona para avaliação padronizada e comparável entre candidatos. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `evaluate_rubric` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `explain_score` | Explica detalhadamente como o score WSI do candidato foi calculado, indicando quais competências contribuíram e quais faltam. Aciona quando recruiter ou candidato questiona o resultado. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `generate_questions` | Gera perguntas de triagem WSI personalizadas para a vaga com base nos requisitos e competências mapeadas. Aciona na configuração de nova vaga ou antes de entrevista estruturada. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `generate_wsi_questions` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_report` | Gera parecer completo do candidato com score WSI, análise de competências, red flags e recomendação final. Aciona antes de apresentar candidato ao hiring manager. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `map_big_five` | Mapeia traços comportamentais do candidato no modelo Big Five (abertura, consciência, extroversão, amabilidade, neuroticismo). Aciona na avaliação comportamental de candidatos finalistas. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `normalize_scores` | Normaliza scores entre candidatos de diferentes buscas para comparação justa em base comum. Aciona ao combinar resultados de múltiplos processos de triagem. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `normalize_scores` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `parse_cv` | Analisa e extrai dados estruturados do currículo: experiências, competências, formação, idiomas e contatos. Aciona como primeira etapa ao receber candidatura ou ao adicionar candidato manualmente ao pipeline. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `parse_cv` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `pre_qualify` | Pré-qualifica candidato com perguntas rápidas antes da triagem formal para filtrar desqualificadores objetivos (localização, salário, disponibilidade). Aciona como etapa zero antes do processo completo. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `pre_qualify_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `rank_candidates` | Ordena candidatos por score WSI e compatibilidade com a vaga para priorização do pipeline. Aciona quando recruiter pede ranqueamento ou antes de apresentar shortlist. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_feedback` | Envia feedback personalizado ao candidato sobre o resultado da triagem com pontos positivos e áreas de desenvolvimento. Aciona após rejeição quando empresa quer oferecer experiência de qualidade. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `send_candidate_feedback` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |
| `validate_cbi` | Valida respostas do candidato contra o framework CBI (Competency-Based Interview) verificando evidências comportamentais. Aciona durante entrevista estruturada para garantir qualidade das evidências coletadas. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`PipelineReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `voice_screening` | Executa triagem por voz com candidato usando metodologia WSI via interface de áudio. Aciona quando candidato prefere formato oral ou para agilizar triagem inicial. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `run_screening_pipeline` em `_ACTION_TOOL_MAP`; executada via `execute_cv_screening_tool` → handler resolvido por `resolve_handler_path`. |

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
| `create_twin` | Cria Digital Twin de um especialista da empresa para replicar seu raciocínio de avaliação de candidatos. Aciona quando empresa quer escalar conhecimento de especialista para avaliações consistentes. | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `deactivate_twin` | Desativa Digital Twin liberando quota da empresa. Requer confirmação. Aciona quando especialista saiu da empresa ou Twin não é mais utilizado. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `evaluate_with_twin` | Avalia candidato usando o raciocínio replicado do Digital Twin do especialista para decisão de fit. Aciona como etapa avançada de avaliação de candidatos finalistas quando Twin está disponível. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `index_twin_audio` | Treina o Digital Twin indexando gravação de entrevista realizada pelo especialista para aprender seu padrão de avaliação. Aciona durante calibração do Twin com novas entrevistas do especialista. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_twins` | Lista Digital Twins disponíveis na empresa com especialidade e status de treinamento. Aciona quando recruiter quer escolher qual Twin usar ou verificar quais estão prontos. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |

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
| `analyze_response` | Analisa resposta do candidato usando metodologia WSI com IA para extrair evidências de competências e calcular score parcial. Aciona após cada resposta do candidato durante entrevista estruturada. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `analyze_voice` | Analisa tom de voz, confiança e consistência emocional do candidato durante entrevista oral. Aciona em entrevistas por voz para adicionar dimensão não-verbal à avaliação. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `scheduling_analyze_voice` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `cancel_interview` | Cancela entrevista agendada e notifica participantes com motivo da cancelamento. Requer confirmação. Aciona quando entrevista não será realizada por desistência ou indisponibilidade. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `scheduling_cancel` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `check_availability` | Verifica disponibilidade do entrevistador no calendário para data e duração específicas. Aciona antes de propor horário ao candidato para garantir slot disponível. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `scheduling_check_availability` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `complete_interview` | Finaliza entrevista WSI gerando resumo completo com scores por competência, análise e recomendação final. Aciona quando todas as perguntas foram feitas e recruiter encerra a sessão. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `detect_evasive` | Detecta padrões de respostas evasivas ou inconsistentes durante entrevista para alertar o recruiter. Aciona automaticamente durante análise de respostas ou quando recruiter suspeita de inconsistência. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `find_common_slots` | Encontra horários comuns disponíveis para múltiplos participantes (painéis com vários entrevistadores). Aciona para agendamento de entrevistas em painel com 2+ entrevistadores. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `scheduling_find_slots` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_followup` | Gera pergunta de follow-up contextualizada baseada na resposta anterior do candidato para aprofundar evidências. Aciona quando resposta foi superficial ou vaga e recruiter precisa de mais evidências. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `generate_self_scheduling_link` | Gera link para candidato escolher horário disponível do entrevistador de forma autônoma sem intervenção do recruiter. Aciona para otimizar agendamento e melhorar experiência do candidato. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `scheduling_self_scheduling_link` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `interview_qa` | Responde dúvidas do recruiter sobre processo de entrevista, metodologia WSI ou candidato específico. Aciona quando recruiter tem perguntas contextuais durante ou após entrevista. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_today_interviews` | Lista todas as entrevistas agendadas para hoje com horários, participantes e status de confirmação. Aciona no briefing diário do recruiter ou quando pede 'qual minha agenda de hoje?'. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `scheduling_list_today` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `reschedule_interview` | Reagenda entrevista existente para novo horário atualizando eventos no calendário e notificando participantes. Requer confirmação. Aciona quando candidato ou entrevistador solicita novo horário. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `scheduling_reschedule` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `resolve_conflict` | Resolve conflitos de agendamento entre entrevistas sobrepostas usando estratégia de priorização configurável. Aciona quando sistema detecta conflito de agenda ou recruiter relata problema de scheduling. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `schedule_interview` | Agenda entrevista entre candidato e entrevistador via calendário com criação de evento, envio de convites e confirmações. Requer confirmação. Aciona quando recruiter ou candidato confirma horário de entrevista. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `scheduling_schedule_interview` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `schedule_reminders` | Configura lembretes automáticos recorrentes para entrevistas futuras com canais e timing definidos. Aciona na criação do agendamento para garantir lembretes sem intervenção manual. | Agenda interação ou tarefa no momento certo do funil. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_question` | Envia pergunta de entrevista WSI para candidato durante sessão ativa, com tipo e competência alvo. Aciona durante entrevista WSI em andamento para avançar para próxima pergunta. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `send_reminder` | Envia lembrete de entrevista para candidato e entrevistador com detalhes e instruções de acesso. Requer confirmação. Aciona automaticamente 24h antes ou quando recruiter solicita lembrete manual. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `scheduling_send_reminder` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |
| `start_quick_screening` | Inicia triagem rápida estruturada com candidato (10-15 minutos) para qualificação inicial antes de entrevista completa. Aciona como alternativa à entrevista WSI completa para pré-seleção eficiente. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `start_wsi_interview` | Inicia entrevista WSI completa e estruturada com candidato via chat (40-60 minutos) com perguntas baseadas em competências. Aciona quando chegou a hora da entrevista WSI no fluxo de triagem. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `transcribe_audio` | Transcreve áudio de entrevista por voz para texto para análise e registro. Aciona em entrevistas por voz ou quando recruiter envia gravação de entrevista presencial. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `scheduling_transcribe_audio` em `_ACTION_TOOL_MAP`; executada via `execute_interview_scheduling_tool` → handler resolvido por `resolve_handler_path`. |

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
| `advance_wizard_step` | Avança para próxima etapa do wizard de criação de vaga após validação da etapa atual. Aciona durante fluxo guiado quando recruiter confirma dados da etapa presente. | Avança o fluxo conversacional por etapas estruturadas. | Mapeada para a tool `advance_wizard` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `analyze_jd` | Avalia qualidade da job description: clareza, inclusividade, completude e SEO para candidatos. Aciona antes de publicar para garantir JD de alta qualidade. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `apply_template` | Aplica template de vaga selecionado a nova posição, preenchendo requisitos e configurações automaticamente. Aciona após escolha de template para acelerar criação de vaga. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `search_job_templates` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `clone_job` | Clona vaga existente criando cópia idêntica com novo ID. Aciona para abrir posição duplicada mantendo todos os parâmetros originais. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `clone_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `close_job` | Fecha e arquiva vaga com motivo (preenchida, cancelada, orçamento) e notifica candidatos ativos. Requer atenção — ação significativa. Aciona ao preencher posição ou encerrar processo. | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Mapeada para a tool `close_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `create_from_template` | Cria nova vaga usando outra vaga como template, herdando critérios e configurações. Aciona para vagas recorrentes da empresa com requisitos padronizados. | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `clone_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `create_job` | Cria nova vaga de emprego via conversa natural extraindo requisitos, competências e configurações da descrição do cargo. Aciona quando recruiter inicia processo de nova posição ou cliente solicita abertura de vaga. | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `create_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `detect_criteria` | Detecta critérios de triagem automaticamente a partir da job description usando NLP. Aciona ao importar JD externa para configurar triagem sem inserção manual. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `duplicate_job` | Duplica vaga existente com todos os dados (requisitos, rubricas, configurações) para reaproveitamento. Aciona quando nova posição é similar a vaga já criada. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `duplicate_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `enrich_jd` | Enriquece job description com informações do mercado, competências complementares e linguagem otimizada. Aciona para melhorar JDs simples ou importadas antes de publicar. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `extract_requirements` | Extrai requisitos obrigatórios e desejáveis de uma job description usando IA para estruturar critérios de triagem. Aciona ao importar JD de documento externo ou ao colar descrição de cargo no chat. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_jd` | Gera job description completa e otimizada com IA a partir do título e requisitos básicos fornecidos. Aciona quando recruiter não tem JD pronto e quer criar do zero via IA. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `generate_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_rubrics` | Gera requisitos estruturados para o sistema de Rubricas WSI baseado no cargo e competências identificadas. Aciona após criação da vaga para configurar critérios de avaliação objetivos. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_wsi_questions` | Gera conjunto de perguntas WSI customizadas para a vaga baseadas nos requisitos e competências. Aciona na configuração de nova vaga antes do início das triagens. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `get_benefits` | Obtém lista de benefícios da empresa para incluir na vaga automaticamente. Aciona ao criar vaga quando recruiter não quer digitar benefícios manualmente. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `get_wizard_step_data` | Obtém dados e contexto da etapa atual do wizard para exibição e validação. Aciona durante wizard para carregar formulário e validações da etapa presente. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `get_wizard_step` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `guided_wizard` | Inicia fluxo conversacional guiado passo a passo para criação de vaga com validação em cada etapa. Aciona quando recruiter prefere processo estruturado ou é iniciante na plataforma. | Avança o fluxo conversacional por etapas estruturadas. | Mapeada para a tool `get_wizard_step` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `health_check` | Verifica indicadores de saúde da vaga: volume, velocidade do pipeline, SLA, taxa de triagem e alertas. Aciona na abertura do dashboard da vaga ou quando recruiter pede status geral. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_health` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `import_jd` | Importa job description de documento (PDF, Word) ou URL para a plataforma estruturando automaticamente. Aciona quando recruiter tem JD em arquivo externo. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `import_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `job_analytics` | Obtém métricas e analytics da vaga: candidatos, conversão por etapa, tempo médio e benchmark de mercado. Aciona no dashboard da vaga ou quando recruiter pede análise de desempenho. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `job_status_webhook` | Gerencia webhooks de status da vaga para integrações externas receberem atualizações em tempo real. Aciona na configuração de integrações que precisam ser notificadas de mudanças de status. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_health` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `list_jobs` | Lista vagas abertas e ativas do tenant com status, contagem de candidatos e dias abertos. Aciona quando recruiter quer visão geral das vagas ou precisa selecionar vaga para ação. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `pause_job` | Pausa vaga temporariamente interrompendo triagem automática e sourcing sem fechar o processo. Aciona quando há mudança de contexto temporária mas vaga será retomada. | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Mapeada para a tool `pause_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `publish_job` | Publica vaga em job boards (LinkedIn, Indeed, site da empresa) ativando sourcing automático. Aciona após qualificação quando vaga está pronta para receber candidaturas. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `update_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `qualify_job` | Qualifica a vaga verificando completude dos dados obrigatórios antes de publicação. Aciona antes de publicar vaga para garantir que todos os campos necessários estão preenchidos. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_health` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `search_templates` | Busca templates de vaga por cargo, setor ou palavras-chave para reutilização. Aciona quando recruiter quer criar vaga baseada em template existente na biblioteca. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `search_job_templates` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_compensation` | Sugere faixa de compensação competitiva baseada em benchmarks de mercado para o cargo e localização. Aciona quando recruiter precisa definir salário ou está negociando com candidato. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_jd_improvements` | Sugere melhorias para job description usando IA: linguagem inclusiva, clareza, SEO para candidatos. Aciona quando recruiter quer otimizar a JD antes de publicar. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `enrich_job_description` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_strategy` | Sugere mudanças de estratégia de recrutamento baseadas nos dados da vaga: sourcing, critérios, canais. Aciona quando vaga está parada, sem candidatos qualificados ou com SLA em risco. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `get_job_analytics` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |
| `update_job` | Atualiza campos da vaga existente: requisitos, salário, localização, status ou qualquer configuração. Aciona quando recruiter pede para modificar informações da vaga ativa. | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `update_job_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_job_management_tool` → handler resolvido por `resolve_handler_path`. |

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
| `autonomous_actions` | Lista e gerencia ações autônomas executadas pela LIA (emails enviados, candidatos movidos) para revisão e auditoria. Aciona quando recruiter quer saber o que a IA fez ou revisar ações automáticas. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `calibrate_profile` | Calibra o perfil ideal de candidato para a vaga com base no feedback do recruiter sobre candidatos vistos. Aciona quando triagem está retornando candidatos fora do perfil desejado. | Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `compare_candidates` | Faz comparação rápida entre candidatos selecionados com análise de pontos fortes, gaps e recomendação. Aciona quando recruiter tem dúvida entre dois ou mais finalistas. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `conversation_summary` | Gera resumo estruturado da conversa atual com pontos-chave, decisões e próximas ações. Aciona quando recruiter pede resumo ou ao fim de conversa longa. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_conversation_summary` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `daily_briefing` | Gera briefing diário personalizado para o recrutador com prioridades do dia, candidatos aguardando ação, SLAs em risco e agenda de entrevistas. Aciona automaticamente pela manhã ou quando recruiter pede 'o que tenho para hoje?'. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `end_of_day_summary` | Gera resumo de encerramento do dia com ações realizadas, pendências e destaques. Aciona no fim do expediente para registro e planejamento do dia seguinte. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `generate_insights` | Gera insights proativos sobre padrões de sourcing, efetividade de canais e oportunidades de melhoria. Aciona semanalmente ou quando recruiter pede análise de desempenho. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `help_command` | Mostra lista de comandos, funcionalidades disponíveis e exemplos de uso para orientar o recruiter. Aciona quando recruiter digita 'ajuda', 'help' ou está perdido na plataforma. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `kanban_analysis` | Analisa o quadro Kanban de recrutamento com IA identificando padrões, gargalos e oportunidades de otimização. Aciona quando recruiter quer análise estratégica do fluxo de candidatos. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_kanban_analysis` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `learning_insights` | Apresenta o que a LIA aprendeu com contratações anteriores: padrões de sucesso, preditores de performance e calibrações. Aciona quando recruiter quer entender o aprendizado do sistema. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `move_candidate` | Move candidato para etapa específica do pipeline com confirmação e registro. Requer confirmação. Aciona quando recruiter quer mover candidato sem abrir tela de candidatura. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_move_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `pipeline_health` | Analisa a saúde geral do pipeline de recrutamento: vagas com risco, candidatos parados, SLAs vencidos e volume total. Aciona quando recruiter quer visão consolidada de todos os processos. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_pipeline_health` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `plan_day` | Ajuda o recrutador a planejar e priorizar as atividades do dia baseado em pipeline, SLAs e metas. Aciona quando recruiter pede ajuda para organizar agenda ou não sabe por onde começar. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `proactive_alerts` | Lista e prioriza alertas proativos do pipeline: SLA vencidos, candidatos parados, vagas sem movimento, risco de perda. Aciona no início do dia ou quando recruiter pede 'o que precisa de atenção?'. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `quick_question` | Responde pergunta rápida do recrutador sobre candidato, vaga ou processo sem roteamento para domínio especializado. Aciona para perguntas simples de contexto ou verificações rápidas. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `recall_memory` | Recupera informação da memória persistente sobre candidato, vaga ou decisão anterior. Aciona quando recruiter pergunta 'o que você sabe sobre X?' ou referencia informação anterior. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_recall_memory` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `save_memory` | Salva informação importante na memória persistente para referência futura (preferências de candidato, acordos com cliente, etc.). Aciona quando recruiter diz 'anota isso' ou quer preservar contexto. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_save_memory` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `search_context` | Busca no histórico de conversas e memória persistente por contexto relevante sobre candidato, vaga ou situação. Aciona quando recruiter referencia algo discutido anteriormente. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `assistant_search_context` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `send_notification` | Envia notificação proativa para o recrutador sobre evento crítico (candidato que vai desistir, SLA em risco). Aciona automaticamente pela IA ao detectar situação que requer atenção imediata. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Mapeada para a tool `assistant_send_notification` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `stage_recommendation` | Recomenda próxima etapa ideal para candidato baseado em score, perfil e histórico do processo. Aciona quando recruiter pede orientação sobre como avançar com candidato específico. | Avança o fluxo conversacional por etapas estruturadas. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `stakeholder_notify` | Detecta decisões pendentes de hiring managers e dispara notificações com escalação automática. Aciona quando candidato está aguardando decisão do gestor há mais do prazo acordado. | Entrega comunicação ao candidato/stakeholder no canal apropriado. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `stale_candidates` | Identifica e lista candidatos que estão parados em etapas sem movimento há mais de N dias. Aciona para limpeza proativa de pipeline ou quando recruiter quer reativar candidatos esquecidos. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_stale_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_action` | Sugere a próxima melhor ação para um candidato ou vaga usando IA baseada no contexto atual. Aciona quando recruiter está indeciso ou quer recomendação do assistente. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent`) sem tool intermediária — usa LLM + serviços do domínio. |
| `track_goals` | Acompanha o progresso das metas de recrutamento do período (vagas fechadas, tempo médio, candidatos contratados). Aciona quando recruiter quer ver performance ou relatório para liderança. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `assistant_track_goals` em `_ACTION_TOOL_MAP`; executada via `execute_recruiter_assistant_tool` → handler resolvido por `resolve_handler_path`. |

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
| `advance_campaign` | Avança campanha para próximo estágio após validação dos critérios de entrada. Requer confirmação. Aciona quando etapa atual está concluída e recruiter confirma avanço para fase seguinte. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_campaign` | Cria campanha de recrutamento estruturada para vaga ou pool de talentos com etapas, automações e nível de autonomia configurados. Aciona quando recruiter inicia processo estruturado de atração de candidatos. | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_campaign_progress` | Obtém estágio atual da campanha com métricas de progresso, próximos passos e alertas de desvio. Aciona para acompanhar andamento da campanha ou quando recruiter pede status. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_campaigns` | Lista campanhas de recrutamento ativas e recentes com status, vagas vinculadas e métricas resumidas. Aciona quando recruiter quer gerenciar campanhas em andamento. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |

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
| `add_candidate` | Cadastra novo candidato no banco de talentos com dados básicos de perfil e origem. Aciona quando recruiter quer adicionar candidato indicado, importado ou captado manualmente. | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `add_candidate_to_vacancy` | Vincula candidato existente no banco de talentos a uma vaga específica para iniciar processo seletivo. Aciona quando candidato foi encontrado externamente e recruiter quer incluí-lo no pipeline. | Materializa um novo registro/objeto solicitado pelo recrutador. | Mapeada para a tool `sourcing_add_candidate_to_vacancy` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `analyze_search_results` | Analisa efetividade dos resultados de busca: qualidade dos matches, taxa de retorno e gaps de critérios. Aciona após busca para avaliar se estratégia precisa ser ajustada. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `assess_market` | Analisa o mercado de talentos disponíveis para a posição: volume, competição, faixa salarial e disponibilidade. Aciona no início da vaga para calibrar expectativas de prazo e salário. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `sourcing_get_talent_quality` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `auto_source` | Executa pipeline automatizado de sourcing para a vaga: busca, triagem preliminar e ranqueamento sem intervenção. Aciona para vagas com volume alto ou quando recruiter quer automação completa. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `build_search_strategy` | Define estratégia de sourcing personalizada para a vaga: canais, critérios, volume e timeline. Aciona no início de vaga nova para estruturar abordagem de busca. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `check_volume` | Avalia se o volume de candidatos qualificados no pipeline é suficiente para preencher a posição. Aciona para decidir se sourcing deve continuar ou se há candidatos suficientes. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `compare_candidates` | Compara candidatos selecionados lado a lado em skills, experiência, score e pontos fortes. Aciona quando recruiter tem múltiplos finalistas e precisa decidir quem avançar. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `sourcing_get_candidate_details` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `contact_candidates` | Inicia outreach para candidatos selecionados com mensagem personalizada via canal preferido. Aciona para engajar candidatos passivos ou confirmar interesse de candidatos ativos. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `dedup_candidates` | Remove candidatos duplicados do pipeline identificando registros com mesmo email ou documento. Aciona periodicamente ou quando pipeline mostra inconsistências de contagem. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `engagement_pipeline` | Gerencia fluxo automatizado de engajamento com candidatos passivos: sequência de contatos, follow-ups e respostas. Aciona para campanhas de nurturing de talentos no banco interno. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `enrich_profile` | Enriquece dados do candidato buscando informações públicas (LinkedIn, GitHub) para completar perfil. Aciona quando perfil do candidato está incompleto ou recruiter quer mais contexto. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `expand_search` | Amplia critérios de busca relaxando restrições quando não há candidatos suficientes no pool atual. Aciona quando busca retorna poucos resultados e recruiter precisa ampliar escopo. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `export_candidates` | Exporta lista de candidatos filtrados para CSV ou Excel para análise externa ou relatório. Aciona quando recruiter precisa compartilhar lista com cliente ou fazer análise offline. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `feedback_search` | Registra feedback do recruiter sobre qualidade dos candidatos retornados para melhorar próximas buscas. Aciona quando recruiter avalia candidatos e quer refinar busca. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `filter_candidates` | Aplica filtros avançados ao pipeline de candidatos: score, etapa, localização, disponibilidade, data de cadastro. Aciona quando recruiter quer segmentar lista de candidatos. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `sourcing_search_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `generate_boolean` | Gera query booleana otimizada para busca em LinkedIn, Indeed e outros job boards baseada nos requisitos da vaga. Aciona quando recruiter quer fazer busca manual ou exportar para ferramentas externas. | Gera artefato derivado por IA para acelerar a decisão do recrutador. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_candidate_history` | Obtém histórico completo de participação do candidato em processos seletivos anteriores na plataforma. Aciona para verificar se candidato já foi avaliado antes ou reativar candidatura anterior. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `sourcing_get_candidate_history` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `get_candidate_stats` | Obtém métricas e estatísticas do candidato no pipeline: etapa atual, score, histórico de avaliações e comunicações. Aciona para contextualização antes de ação sobre candidato específico. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `sourcing_get_candidate_stats` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `global_search` | Executa busca em todas as fontes disponíveis (banco interno, Pearch AI, LinkedIn, job boards) com estratégia unificada. Aciona quando busca simples não encontrou candidatos suficientes. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `sourcing_search_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `import_candidates` | Importa candidatos de arquivo CSV, planilha ou integração externa para o banco de talentos. Aciona ao migrar dados de outra plataforma ou receber lista de candidatos do cliente. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `match_candidates` | Calcula índice de compatibilidade entre candidato e vaga analisando skills, experiência e fit cultural. Aciona para priorização de candidatos ou validação de fit antes de avançar. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `parse_cv` | Extrai dados estruturados de currículo: experiências, competências, formação e contatos para enriquecer perfil no sistema. Aciona ao receber currículo em formato PDF ou Word. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `pearch_search` | Executa busca via Pearch AI para encontrar candidatos passivos com perfil técnico específico. Aciona para vagas técnicas de difícil preenchimento ou quando banco interno não tem candidatos suficientes. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `proactive_suggest` | Sugere ações proativas de sourcing baseadas em análise do pipeline e mercado de talentos. Aciona quando vaga está sem movimento ou pipeline abaixo do esperado. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `rank_candidates` | Ordena candidatos por score de compatibilidade, score WSI e prioridade de contato. Aciona para gerar shortlist ranqueada ou priorizar próximos a contatar. | Atende uma intenção específica do recrutador dentro do domínio. | Mapeada para a tool `sourcing_rank_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `reject_candidate` | Rejeita candidato do processo seletivo com motivo e opção de envio de feedback. FairnessGuard ativo. Aciona quando candidato não atende requisitos mínimos ou foi preterido por outro. | Encerra/desliga o item alvo respeitando políticas (HITL quando exigido). | Mapeada para a tool `sourcing_reject_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `schedule_outreach` | Agenda contato futuro com candidato passivo para momento mais adequado (ex: após período de confidencialidade). Aciona quando recruiter quer manter candidato ativo para oportunidades futuras. | Agenda interação ou tarefa no momento certo do funil. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `screen_candidates` | Executa screening inicial rápido de candidatos com checklist de desqualificadores objetivos. Aciona como pré-triagem para reduzir volume antes da triagem WSI completa. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `search_candidates` | Busca candidatos no banco de talentos com filtros de skills, localização, seniority, disponibilidade e score. Aciona quando recruiter pede busca de candidatos para uma vaga específica. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Mapeada para a tool `sourcing_search_candidates` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `semantic_search` | Busca candidatos por similaridade semântica usando embeddings vetoriais, capturando candidatos com perfil similar mesmo sem palavras-chave exatas. Aciona para vagas com requisitos difíceis de expressar em palavras. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `shortlist_candidate` | Adiciona candidato à shortlist de favoritos para decisão final ou apresentação ao hiring manager. Aciona quando recruiter identifica candidato forte para manter em evidência. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Mapeada para a tool `sourcing_shortlist_candidate` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |
| `suggest_candidates` | Sugere candidatos do banco de talentos compatíveis com os requisitos da vaga baseado em matching semântico. Aciona quando recruiter abre nova vaga para ver candidatos já disponíveis internamente. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `tag_candidates` | Adiciona tags personalizadas aos candidatos para segmentação e busca rápida posterior. Aciona quando recruiter quer categorizar candidatos por perfil, status ou interesse. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `talent_pool_search` | Busca candidatos no pool interno de talentos da empresa incluindo ex-candidatos e indicados. Aciona como primeira etapa de sourcing para aproveitar banco interno antes de busca externa. | Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional. | Executada diretamente pelo agente do domínio (`SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)`) sem tool intermediária — usa LLM + serviços do domínio. |
| `update_candidate_stage` | Move candidato para outra etapa do pipeline com registro de motivo e notificação automática. Aciona quando recruiter aprova candidato para próxima fase do processo seletivo. | Persiste a alteração solicitada sem sair do chat. | Mapeada para a tool `sourcing_update_candidate_stage` em `_ACTION_TOOL_MAP`; executada via `execute_sourcing_tool` → handler resolvido por `resolve_handler_path`. |

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
| `add_to_pool` | Adiciona candidatos ao banco de talentos com origem registrada para rastreamento. Aciona após processo seletivo para manter candidatos aprovados não contratados ou ao receber indicações. | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_job_from_pool` | Cria nova vaga a partir de um banco de talentos herdando arquétipo, critérios e configurações do pool. Requer confirmação. Aciona quando nova posição tem perfil igual ao pool existente. | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `create_talent_pool` | Cria novo banco de talentos vivo com nome, arquétipo de candidato ideal e critérios de triagem. Aciona quando empresa quer manter pool de candidatos para posições recorrentes. | Materializa um novo registro/objeto solicitado pelo recrutador. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `get_pool_candidates` | Lista candidatos de um banco de talentos com estágios, scores e disponibilidade para análise e ação. Aciona quando recruiter quer ver quem está no pool ou selecionar candidatos para vaga. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `list_talent_pools` | Lista bancos de talentos ativos com nome, arquétipo, contagem de candidatos e última atualização. Aciona quando recruiter quer gerenciar pools ou selecionar pool para ação. | Devolve dados ao chat para o recrutador decidir o próximo passo. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |
| `move_pool_to_job` | Migra candidatos do pool para uma vaga específica na etapa selecionada, iniciando processo seletivo. Requer confirmação. Aciona quando vaga abre e candidatos do pool são elegíveis. | Atende uma intenção específica do recrutador dentro do domínio. | Executada diretamente pelo agente do domínio (`—`) sem tool intermediária — usa LLM + serviços do domínio. |

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
