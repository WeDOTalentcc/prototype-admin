# ADR-001: Arquitetura Multi-Agent vs Super-Agent

**Status:** Aceito  
**Data:** 2025-11-24  
**Decisor:** Equipe Técnica LIA  

## Contexto

A Plataforma LIA atualmente implementa workflows especializados via LangGraph (conversational job creation, candidate search, interview scheduling) que funcionam como "proto-agents". Precisamos decidir a arquitetura para escalar o sistema para cobrir o fluxo end-to-end de recrutamento.

## Decisão

Adotamos **arquitetura multi-agente orquestrada** com 6 agentes especializados + 2 serviços compartilhados.

### Agentes Especializados (6):
1. **Job Intake Agent** - Criação/atualização de vagas, aprovações, JD
2. **Sourcing Agent** - Busca 2-tier (BD interno + Pearch AI), enrichment
3. **Screening Agent** - Triagem automatizada (voice, WhatsApp, knockout)
4. **Evaluation Agent** - Scoring técnico/comportamental, testes, Big Five
5. **Scheduling Agent** - Microsoft Graph, coordenação de calendário
6. **Communication Agent** - Cadências omnicanal, nutrição, follow-ups

### Serviços Compartilhados (2):
7. **ATS Sync Service** - Integração Gupy/Pandapé
8. **Analytics Service** - Dashboards, relatórios, insights

## Justificativa

### Por que Multi-Agent vence:

**1. Especialização vs Sobrecarga Cognitiva**
- Multi-Agent: Cada agente é expert em uma área específica
- Super-Agent: Prompts gigantes (>30k tokens), confusão, latência >8s

**2. Observabilidade**
- Multi-Agent: Visibilidade clara de cada etapa do processo
- Super-Agent: Caixa preta opaca, debugging impossível

**3. Benchmarking da Indústria**
- Tezi, GoodTime, Moonhub: Multi-agent com orquestrador
- Popp AI (v1): Super-agent sofreu com alucinações

**4. Extensibilidade**
- Multi-Agent: Adicionar workflow = novo agente (baixo risco)
- Super-Agent: Modificar prompt = risco de quebrar tudo

## Consequências

### Positivas:
- ✅ Isolamento de responsabilidades
- ✅ Tuning específico por domínio
- ✅ Reuso de proto-agents existentes
- ✅ Observabilidade granular
- ✅ Testes independentes por agente

### Negativas:
- ⚠️ Overhead de orquestração
- ⚠️ Consistência de memória cross-agent
- ⚠️ Necessidade de telemetria granular

### Mitigações:
- Bus de eventos eficiente (Redis/Postgres)
- Conversation Store centralizado
- OpenTelemetry + LangSmith para traces

## Roadmap de Implementação

**Phase 1** (Atual): Hardening proto-agents  
**Phase 2**: Orchestrator MVP (intent router, policy engine, state store)  
**Phase 3**: Agentes especializados (Job Intake, Sourcing, Scheduling)  
**Phase 4**: Novos agentes (Screening, Evaluation, Communication)  
**Phase 5**: Serviços compartilhados (ATS Sync, Analytics)  
**Phase 6**: Observabilidade completa (OpenTelemetry, dashboards)

## Referências

- Análise competitiva: Tezi, Popp AI, Moonhub, GoodTime, hireEZ
- Proto-agents existentes: `lia-agent-system/app/agents/`
- LangGraph documentation: https://langchain-ai.github.io/langgraph/
