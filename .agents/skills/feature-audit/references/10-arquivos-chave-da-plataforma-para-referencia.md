# Arquivos-Chave da Plataforma para Referência

> Parte da skill `feature-audit`. Carregue quando precisar deste topico especifico.

### Frontend (plataforma-lia/)
- Componentes Kanban: `src/components/kanban/components/`
- Hooks Kanban: `src/components/kanban/hooks/`
- Constantes/Tipos: `src/components/kanban/constants.ts`, `src/components/kanban/types.ts`
- Utils: `src/components/kanban/utils/`
- Páginas: `src/components/pages/`
- Hooks globais: `src/hooks/`
- API Proxies: `src/app/api/backend-proxy/`
- Design Tokens CSS: `src/styles/design-tokens.css`
- Design Tokens TS: `src/lib/design-tokens.ts`
- Design System Doc: `docs/design-system/00-design-system-v4.md`

### Backend (lia-agent-system/)
- Endpoints: `app/api/v1/`
- Models: `app/models/`
- Schemas: `app/schemas/`
- Services: `app/services/`
- Domains: `app/domains/`

### IA / Agentes (lia-agent-system/)
- Domínios IA: `app/domains/` (estrutura DDD com múltiplos domínios de código)
- **Agentes ReAct ativos (7):** Wizard, Pipeline (PipelineTransitionAgent), Sourcing, Talent, JobsManagement, Kanban, Policy
- Orchestrador: `app/orchestrator/` (cascaded_router.py, orchestrator.py, state_manager.py, policy_engine.py)
- Shared IA: `app/shared/` (providers, prompts, intelligence, tools, memory, compliance, resilience)
- Prompts: `app/shared/prompts/`
- Tools: `app/shared/tools/`

### Documentação
- WeDO Talent Guide v3.3: `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md`
- Design System v4.2.1: `plataforma-lia/docs/design-system/00-design-system-v4.md`
- Arquitetura IA: `docs/lia-ai-architecture-cards-jira.md`
- Pipeline: `docs/pipeline-transition-system.md`
- MVP Alpha Roadmap: `docs/mvp-alpha-scenarios.md`
- Memória: `replit.md`

---
