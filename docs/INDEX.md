# Documentação WeDo Talent / Plataforma LIA

**Última Atualização:** 15 Abril 2026

---

## ⭐ DOCUMENTO CANÔNICO

**[ARCHITECTURE.md](./architecture/ARCHITECTURE.md)** — Source of truth técnica completa da plataforma. ~1300 linhas cobrindo backend, frontend, chat, data layer, infrastructure, agentes, compliance, deploy. Cruza código real com decisões arquiteturais. Atualizar a cada PR estrutural.

---

## Estrutura de Pastas

```
docs/
├── architecture/          # Arquitetura do sistema
│   ├── core/              # Stack, evolução, banco de dados
│   ├── agents/            # Arquitetura multi-agente LIA
│   └── services/          # Serviços e sincronização
├── vagas/                 # Gestão e criação de vagas
├── funil/                 # Funil de talentos e candidatos
├── admin/                 # Painel administrativo
├── integracao/            # Integrações externas (Deepgram, WhatsApp, etc)
├── analises/              # Análises, QA e diagnósticos
├── roadmap/               # Planos de implementação e PRD
├── comercial/             # Design system, onboarding, pitch
├── compliance/            # Trust Center, LGPD, compliance
├── archived/              # Documentos arquivados
│   ├── old-proposals/     # Propostas antigas
│   └── old-training/      # Materiais de treinamento antigos
└── [Jira Cards]           # Arquivos de cards Jira (não alterar)
```

---

## Índice por Categoria

### Arquitetura

| Documento | Descrição |
|-----------|-----------|
| [architecture/agents/LIA_AGENT_ARCHITECTURE_COMPLETE.md](./architecture/agents/LIA_AGENT_ARCHITECTURE_COMPLETE.md) | Arquitetura completa multi-agente v3.0 |
| [architecture/agents/AGENT_INTEGRATION_MAP.md](./architecture/agents/AGENT_INTEGRATION_MAP.md) | Mapa de integração dos agentes |
| [architecture/core/TECHNICAL_STACK.md](./architecture/core/TECHNICAL_STACK.md) | Stack tecnológica completa |
| [architecture/core/DATABASE_FIELDS_REFERENCE.md](./architecture/core/DATABASE_FIELDS_REFERENCE.md) | Referência de campos do banco |
| [architecture/core/AI_EVOLUTION_STRATEGY.md](./architecture/core/AI_EVOLUTION_STRATEGY.md) | Estratégia de evolução da IA |
| [architecture/core/AI_STAGE_AUTOMATION_ARCHITECTURE.md](./architecture/core/AI_STAGE_AUTOMATION_ARCHITECTURE.md) | Automação de etapas com IA |
| [architecture/core/PORTABILITY_GUIDE.md](./architecture/core/PORTABILITY_GUIDE.md) | Guia de portabilidade |
| [architecture/services/COMPANY_DEFAULTS_SYNC_ARCHITECTURE.md](./architecture/services/COMPANY_DEFAULTS_SYNC_ARCHITECTURE.md) | Sincronização de defaults |
| [architecture/services/CONFIG_SYNC_FEATURE_PROPOSAL.md](./architecture/services/CONFIG_SYNC_FEATURE_PROPOSAL.md) | Proposta de sync de config |
| [architecture/c4-diagram.md](./architecture/c4-diagram.md) | Diagrama C4 |
| [architecture/COMPLETE_SYSTEM_ARCHITECTURE.md](./architecture/COMPLETE_SYSTEM_ARCHITECTURE.md) | Arquitetura completa do sistema |
| [architecture/id-boundary-policy.md](./architecture/id-boundary-policy.md) | ID Boundary Policy LIA × Rails (UUID vs bigint, naming, RailsAdapter) — derivado de [ADR 003](./adr/003-id-strategy-lia-vs-rails.md) |
| [architecture/tenant-context-history.md](./architecture/tenant-context-history.md) | Histórico técnico das tasks T-A → T-F (`TenantAwareAgentMixin`, `CompanyId`, helper non-ReAct, golden dataset). Fonte da verdade do contrato anti-bug *"LIA pergunta company_id no chat"*. Runbook on-call associado: [`runbooks/missing_tenant_context.md`](./runbooks/missing_tenant_context.md). |

### LIA / Inteligência Artificial (Não Alterar)

| Documento | Descrição |
|-----------|-----------|
| [AI_TRAINING_COMPLETE.md](./AI_TRAINING_COMPLETE.md) | Documentação completa de IA e Treinamento (consolidado) |
| [LIA_AUTOMATION_SYSTEM.md](./LIA_AUTOMATION_SYSTEM.md) | Sistema de automação LIA |
| [LIA_AUTOMATION_DEVELOPMENT_GUIDE.md](./LIA_AUTOMATION_DEVELOPMENT_GUIDE.md) | Guia de desenvolvimento |
| [LIA_AUTOMATION_IMPLEMENTATION_PLAN.md](./LIA_AUTOMATION_IMPLEMENTATION_PLAN.md) | Plano de implementação |
| [LIA_METHODOLOGY.md](./LIA_METHODOLOGY.md) | Metodologia LIA |
| [LIA_RESPONSE_TEMPLATES.md](./LIA_RESPONSE_TEMPLATES.md) | Templates de resposta |
| [LIA_UNIFIED_METHODOLOGY.md](./LIA_UNIFIED_METHODOLOGY.md) | Metodologia unificada |
| [LLM_COMPARISON_TRAINING.md](./LLM_COMPARISON_TRAINING.md) | Comparação de LLMs |
| [NLP_CLUSTERING_STRATEGIC_ANALYSIS.md](./NLP_CLUSTERING_STRATEGIC_ANALYSIS.md) | Análise de NLP/clustering |
| [PENDENTES_IA.md](./PENDENTES_IA.md) | Pendentes de IA |
| [PLANO_ACAO_AGENTES_IA.md](./PLANO_ACAO_AGENTES_IA.md) | Plano de ação agentes |
| [RELATORIO_TRANSFORMACAO_IA_LIA.md](./RELATORIO_TRANSFORMACAO_IA_LIA.md) | Relatório de transformação |
| [WSI_METHODOLOGY_REFERENCE.md](./WSI_METHODOLOGY_REFERENCE.md) | Referência metodologia WSI |

### Vagas

| Documento | Descrição |
|-----------|-----------|
| [FLUXO_CRIACAO_VAGA.md](./FLUXO_CRIACAO_VAGA.md) | Fluxo de criação de vaga (Não Alterar) |
| [JOB_CREATION_WIZARD_FLOW.md](./JOB_CREATION_WIZARD_FLOW.md) | Fluxo do wizard (Não Alterar) |
| [WIZARD_CRIACAO_VAGA_COMPLETO.md](./WIZARD_CRIACAO_VAGA_COMPLETO.md) | Wizard completo (Não Alterar) |
| [vagas/wizard-configuration-technical-spec.md](./vagas/wizard-configuration-technical-spec.md) | Spec técnico do wizard |
| [vagas/gestao-vagas-fluxos.md](./vagas/gestao-vagas-fluxos.md) | Fluxos de gestão |
| [vagas/DIAGNOSTICO_CAMPOS_VAGA.md](./vagas/DIAGNOSTICO_CAMPOS_VAGA.md) | Diagnóstico de campos |
| [vagas/DIAGNOSTICO_GESTAO_VAGAS_GOLIVE.md](./vagas/DIAGNOSTICO_GESTAO_VAGAS_GOLIVE.md) | Diagnóstico go-live |
| [vagas/gaps-criacao-vagas.md](./vagas/gaps-criacao-vagas.md) | Gaps identificados |

### Funil de Talentos

| Documento | Descrição |
|-----------|-----------|
| [funil/CANDIDATE_STATUS_REFERENCE.md](./funil/CANDIDATE_STATUS_REFERENCE.md) | Referência de status |
| [funil/FUNIL_DE_TALENTOS_AUDIT.md](./funil/FUNIL_DE_TALENTOS_AUDIT.md) | Auditoria do funil |
| [funil/funil-talentos-documentation.md](./funil/funil-talentos-documentation.md) | Documentação do funil |
| [funil/funil-talentos-fluxos.md](./funil/funil-talentos-fluxos.md) | Fluxos do funil |
| [funil/funil-talentos-ia-architecture.md](./funil/funil-talentos-ia-architecture.md) | Arquitetura IA do funil |
| [funil/LEARNING_SYSTEM_DATA_EXAMPLES.md](./funil/LEARNING_SYSTEM_DATA_EXAMPLES.md) | Exemplos do sistema de aprendizado |

### Admin

| Documento | Descrição |
|-----------|-----------|
| [TODO_ADMIN_LAYER.md](./TODO_ADMIN_LAYER.md) | TODO admin (Não Alterar) |
| [admin/admin-audit-report.md](./admin/admin-audit-report.md) | Relatório de auditoria |
| [admin/admin-fluxos.md](./admin/admin-fluxos.md) | Fluxos admin |
| [admin/configuracoes-admin-documentation.md](./admin/configuracoes-admin-documentation.md) | Documentação de configurações |
| [admin/PLANO_IMPLEMENTACAO_WEDOTALENT_ADMIN.md](./admin/PLANO_IMPLEMENTACAO_WEDOTALENT_ADMIN.md) | Plano de implementação |
| [admin/UX_IMPROVEMENTS.md](./admin/UX_IMPROVEMENTS.md) | Melhorias de UX |

### Integrações

| Documento | Descrição |
|-----------|-----------|
| [WEDOTALENT_INTEGRACOES_COMPLETO.md](./WEDOTALENT_INTEGRACOES_COMPLETO.md) | Integrações completas (Não Alterar) |
| [integracao/DEEPGRAM_FLUXO_COMPLETO.md](./integracao/DEEPGRAM_FLUXO_COMPLETO.md) | Fluxo Deepgram |
| [integracao/WHATSAPP_APPLICATION_FLOW.md](./integracao/WHATSAPP_APPLICATION_FLOW.md) | Fluxo WhatsApp |
| [integracao/WSI_VOICE_CHAT_INTEGRATION.md](./integracao/WSI_VOICE_CHAT_INTEGRATION.md) | Voice chat WSI |
| [integracao/MERGE_INTEGRATION_FIELDS_REFERENCE.md](./integracao/MERGE_INTEGRATION_FIELDS_REFERENCE.md) | Referência Merge.dev |
| [integracao/INVENTARIO_FERRAMENTAS_INTEGRACOES.md](./integracao/INVENTARIO_FERRAMENTAS_INTEGRACOES.md) | Inventário de ferramentas |
| [integracao/BACKEND_INTEGRATION_STATUS.md](./integracao/BACKEND_INTEGRATION_STATUS.md) | Status integração backend |
| [integracao/FRONTEND_BACKEND_INTEGRATION.md](./integracao/FRONTEND_BACKEND_INTEGRATION.md) | Integração frontend-backend |
| [integracao/GEMINI_VOICE_INTEGRATION.md](./integracao/GEMINI_VOICE_INTEGRATION.md) | Integração voz Gemini |
| [integracao/OPENMIC_INTEGRATION.md](./integracao/OPENMIC_INTEGRATION.md) | Integração OpenMic.ai |

### Análises e QA

| Documento | Descrição |
|-----------|-----------|
| [DIAGNOSTICO_PROMPTS_PLATAFORMA.md](./DIAGNOSTICO_PROMPTS_PLATAFORMA.md) | Diagnóstico prompts (Não Alterar) |
| [analises/QA_VACANCY_SYSTEM_REVIEW.md](./analises/QA_VACANCY_SYSTEM_REVIEW.md) | QA sistema de vagas |
| [analises/QA_WIZARD_REVIEW_JAN2026.md](./analises/QA_WIZARD_REVIEW_JAN2026.md) | QA wizard Jan/2026 |
| [analises/COMPETITIVE_ANALYSIS_AI_RECRUITING_AGENTS.md](./analises/COMPETITIVE_ANALYSIS_AI_RECRUITING_AGENTS.md) | Análise competitiva |
| [analises/ANALISE-GAPS-COMPLETA.md](./analises/ANALISE-GAPS-COMPLETA.md) | Análise de gaps |

### Roadmap e PRD

| Documento | Descrição |
|-----------|-----------|
| [MVP_DEVELOPMENT_SPEC.md](./MVP_DEVELOPMENT_SPEC.md) | Spec do MVP (Não Alterar) |
| [roadmap/PRD-Plataforma-LIA.md](./roadmap/PRD-Plataforma-LIA.md) | PRD da plataforma |
| [roadmap/ROADMAP-DESENVOLVIMENTO-COMPLETO.md](./roadmap/ROADMAP-DESENVOLVIMENTO-COMPLETO.md) | Roadmap completo |
| [roadmap/PLANO_IMPLEMENTACAO_GOLIVE.md](./roadmap/PLANO_IMPLEMENTACAO_GOLIVE.md) | Plano go-live |
| [roadmap/PLANO_IMPLEMENTACAO_WIZARD.md](./roadmap/PLANO_IMPLEMENTACAO_WIZARD.md) | Plano wizard |
| [roadmap/DEPLOYMENT_GUIDE.md](./roadmap/DEPLOYMENT_GUIDE.md) | Guia de deploy |
| [operations/dois-ambientes-develop-main.md](./operations/dois-ambientes-develop-main.md) | Guia operacional dos 2 ambientes publicados (`develop`/testes + `main`/produção) via GitHub `prototype` + ritual de promoção |
| [roadmap/FUTURAS_FEATURES_PARA_IRMOS.md](./roadmap/FUTURAS_FEATURES_PARA_IRMOS.md) | Features futuras |
| [roadmap/TODO.md](./roadmap/TODO.md) | Lista de tarefas |

### Comercial

| Documento | Descrição |
|-----------|-----------|
| [WEDOTALENT_PRODUCT_OVERVIEW.md](./WEDOTALENT_PRODUCT_OVERVIEW.md) | Overview do produto (Não Alterar) |
| [comercial/pitch-deck-wedo-talent.md](./comercial/pitch-deck-wedo-talent.md) | Pitch deck |
| [comercial/design-system-para-designer.md](./comercial/design-system-para-designer.md) | Design system |
| [comercial/MAPA_FLUXO_ONBOARDING_CLIENTE.md](./comercial/MAPA_FLUXO_ONBOARDING_CLIENTE.md) | Mapa de onboarding |
| [comercial/resumo-executivo-lia.md](./comercial/resumo-executivo-lia.md) | Resumo executivo |

### Compliance

| Documento | Descrição |
|-----------|-----------|
| [compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md](./compliance/WEDOTALENT_COMPLIANCE_ARCHITECTURE.md) | Arquitetura de compliance |
| [compliance/TRUST_CENTER_WEBSITE.md](./compliance/TRUST_CENTER_WEBSITE.md) | Trust Center website |
| [compliance/TRUST_CENTER_NOTION.md](./compliance/TRUST_CENTER_NOTION.md) | Trust Center Notion |
| [compliance/TRUST_CENTER_BENCHMARK_ANALISE.md](./compliance/TRUST_CENTER_BENCHMARK_ANALISE.md) | Benchmark Trust Center |
| [PLAYBOOK_AUDITORIA_PROFUNDA.md](./PLAYBOOK_AUDITORIA_PROFUNDA.md) | Playbook auto-contido de auditoria profunda (9 partes, 14 dimensões, 8 frameworks) |

---

## Arquivos Jira (Não Alterar)

- `admin-wedotalent-cards-jira.md`
- `configuracoes-admin-cards-jira.md`
- `funil-talentos-cards-jira.md`
- `gestao-vagas-cards-jira.md`
- `gestao-vagas-visao-geral-cards-jira.md`
- `lia-mvp-cards-jira.md`

---

## Propostas e Arquivados

| Documento | Status |
|-----------|--------|
| [proposals/job-wizard-enhancement-plan.md](./proposals/job-wizard-enhancement-plan.md) | Ativo (Não Alterar) |
| [archived/old-proposals/](./archived/old-proposals/) | Propostas arquivadas |
| [archived/old-training/](./archived/old-training/) | Treinamentos arquivados |

---

## Documentação Backend (lia-agent-system)

Ver: [../lia-agent-system/docs/README.md](../lia-agent-system/docs/README.md)

## Documentação Frontend (plataforma-lia)

Ver: [../plataforma-lia/docs/README.md](../plataforma-lia/docs/README.md)
