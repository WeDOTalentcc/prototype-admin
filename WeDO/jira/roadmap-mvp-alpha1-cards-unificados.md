# Roadmap MVP Alpha 1 — Cards Jira Unificados
## WeDOTalent / Plataforma LIA

**Versão:** 5.0 | **Data:** 11/março/2026 | **Classificação:** Referência técnica do time — Confidencial

> **Documento único de referência.** Consolida todos os cards Jira criados nos documentos de especificação e os organiza segundo o fluxo real do MVP Alpha 1. Fontes: `saturacao-chatweb-comunicacao-cards-jira.md`, `jira-cards-job-creation-lifecycle.md`, `diagnostico-agentes-mvp.md` e `ANALISE_COMPARATIVA_V5_vs_LIA.md`.

---

## ÍNDICE

1. [Índice de Todos os Cards por Documento de Origem](#1-índice-de-todos-os-cards-por-documento-de-origem)
2. [Roadmap MVP Alpha 1 — Por Passo do Fluxo](#2-roadmap-mvp-alpha-1--por-passo-do-fluxo)
3. [Cards Completos — É30 Saturação e Controle de Pools](#3-cards-completos--é30-saturação-e-controle-de-pools-sat)
4. [Cards Completos — É31 Chat Web de Triagem](#4-cards-completos--é31-chat-web-de-triagem-tri)
5. [Cards Completos — É32 Comunicação Multicanal](#5-cards-completos--é32-comunicação-multicanal-com)
6. [Cards Completos — É33 Inscrição Web](#6-cards-completos--é33-inscrição-web-ins)
7. [Cards Completos — É34 Voz Bidirecional](#7-cards-completos--é34-voz-bidirecional-voz)
8. [Cards Completos — VGM Gestão de Vagas](#8-cards-completos--vgm-gestão-de-vagas-vgm)
9. [Cards Completos — AUD Auditoria e Compliance (WT-1505→WT-1512)](#9-cards-completos--aud-auditoria-e-compliance-wt-1505wt-1512)
10. [Tabela de Dependências Cross-Épico](#10-tabela-de-dependências-cross-épico)
11. [Cards Completos — É35 Arquitetura de IA: Agentes, Tools, Serviços e Automações (AGT)](#11-cards-completos--é35-arquitetura-de-ia-agentes-tools-serviços-e-automações-agt)

---

## 1. Índice de Todos os Cards por Documento de Origem

### Legenda de Prioridade e Fase
- 🔴 Crítica | 🟠 Alta | 🟡 Média | 🟢 Baixa
- **A1** = MVP Alpha 1 | **A2** = Alpha 2 | **A2+** = Futuro

---

### 1.1 — `saturacao-chatweb-comunicacao-cards-jira.md`

**Épico É30 — Saturação e Controle de Pools**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| SAT-001 / [WT-1525](https://wedotalent.atlassian.net/browse/WT-1525) | [Saturação] Modelo de Dados — Pools Separados, Thresholds e Governance Rules | 8 | 🔴 Crítica | A1 | S1 |
| SAT-002 / [WT-1523](https://wedotalent.atlassian.net/browse/WT-1523) | [Saturação] SaturationBadge — Badge Visual com Popover de Ações no Kanban | 5 | 🟠 Alta | A1 | S1 |
| SAT-003 / [WT-1527](https://wedotalent.atlassian.net/browse/WT-1527) | [Saturação] Seção de Configuração no Card Triagem (Settings → Pipeline) | 5 | 🟠 Alta | A1 | S1 |
| SAT-004 / [WT-1526](https://wedotalent.atlassian.net/browse/WT-1526) | [Saturação] Badges de Origem — Web, WhatsApp, Busca, ATS, Aguardando | 3 | 🟡 Média | A1 | S1 |
| SAT-005 / [WT-1524](https://wedotalent.atlassian.net/browse/WT-1524) | [Saturação] Fila de Espera — Status awaiting_screening + Promoção Automática | 8 | 🔴 Crítica | A1 | S2 |
| SAT-006 / [WT-1530](https://wedotalent.atlassian.net/browse/WT-1530) | [Saturação] Override Manual — Recrutador Aprova Candidato da Fila | 5 | 🟠 Alta | A1 | S2 |
| SAT-007 / [WT-1529](https://wedotalent.atlassian.net/browse/WT-1529) | [Saturação] Gate 1 — Máquina de Estados da Inscrição Web até Triagem WSI | 5 | 🔴 Crítica | A1 | S1 |

**Subtotal É30:** 7 cards · 39 SPs

---

**Épico É31 — Chat Web de Triagem (WSI + IA Conversacional)**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| TRI-001 / [WT-1532](https://wedotalent.atlassian.net/browse/WT-1532) | [Chat Web] Tipos e Interfaces TypeScript — types.ts Completo | 3 | 🔴 Crítica | A1 | S1 |
| TRI-002 / [WT-1528](https://wedotalent.atlassian.net/browse/WT-1528) | [Chat Web] Hook useTriagemChat — State Management + API Integration (~537L) | 13 | 🔴 Crítica | A1 | S2 |
| TRI-003 / [WT-1531](https://wedotalent.atlassian.net/browse/WT-1531) | [Chat Web] WelcomeCard — Tela de Boas-Vindas com Branding da Empresa | 3 | 🟠 Alta | A1 | S2 |
| TRI-004 / [WT-1535](https://wedotalent.atlassian.net/browse/WT-1535) | [Chat Web] MessageBubble — Bolha de Mensagem com AudioPlayer e Animação | 5 | 🟠 Alta | A1 | S2 |
| TRI-005 / [WT-1536](https://wedotalent.atlassian.net/browse/WT-1536) | [Chat Web] TriagemSessionService — Motor de IA Conversacional + WSI Scoring (~887L) | 21 | 🔴 Crítica | A1 | S2 |
| TRI-006 / [WT-1534](https://wedotalent.atlassian.net/browse/WT-1534) | [Chat Web] InputBar — Campo de Texto + Gravação de Áudio + Controles de Voz | 5 | 🟠 Alta | A1 | S2 |
| TRI-007 / [WT-1537](https://wedotalent.atlassian.net/browse/WT-1537) | [Chat Web] Página de Triagem — /triagem/[token] (~311L) | 8 | 🔴 Crítica | A1 | S2 |
| TRI-008 / [WT-1533](https://wedotalent.atlassian.net/browse/WT-1533) | [Chat Web] Proxy Route Next.js — /api/backend-proxy/triagem/[...path] | 3 | 🔴 Crítica | A1 | S1 |

**Subtotal É31:** 8 cards · 61 SPs

---

**Épico É32 — Comunicação Multicanal**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| COM-001 / [WT-1542](https://wedotalent.atlassian.net/browse/WT-1542) | [Comunicação] CommunicationDispatcher — Mailgun + Mailgun + Meta WhatsApp + Tone Policy (~533L) | 8 | 🔴 Crítica | A1 | S1 |
| COM-002 / [WT-1538](https://wedotalent.atlassian.net/browse/WT-1538) | [Comunicação] Dispatch Automático #1 — Feedback de Triagem (Aprovado/Reprovado) | 3 | 🟠 Alta | A1 | S2 |
| COM-003 / [WT-1540](https://wedotalent.atlassian.net/browse/WT-1540) | [Comunicação] Dispatch Automático #2 — Rejeição ao Mudar de Stage | 3 | 🟠 Alta | A1 | S2 |
| COM-004 / [WT-1541](https://wedotalent.atlassian.net/browse/WT-1541) | [Comunicação] Dispatch Automático #3 — Convite de Fila quando Slot Abre | 3 | 🟠 Alta | A1 | S2 |
| COM-005 / [WT-1539](https://wedotalent.atlassian.net/browse/WT-1539) | [Comunicação] Dispatch Automático #5 — Confirmação Real Pós-Conclusão da Triagem | 3 | 🟠 Alta | A1 | S2 |

**Subtotal É32:** 5 cards · 20 SPs

---

**Épico É33 — Inscrição Web (Formulário Público)**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| INS-001 / [WT-1546](https://wedotalent.atlassian.net/browse/WT-1546) | [Inscrição Web] Formulário Público — Candidatar-se Online na Página da Vaga | 8 | 🟠 Alta | A1 | S2 |
| INS-002 / [WT-1543](https://wedotalent.atlassian.net/browse/WT-1543) | [Inscrição Web] Página Pública da Vaga — Detalhes + Formulário (/vagas/[slug]) | 5 | 🟠 Alta | A1 | S2 |
| INS-003 / [WT-1544](https://wedotalent.atlassian.net/browse/WT-1544) | [Inscrição Web] Endpoint POST /public-vacancies/{slug}/apply | 5 | 🟠 Alta | A1 | S2 |

**Subtotal É33:** 3 cards · 18 SPs

---

**Épico É34 — Suporte a Voz Bidirecional**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| VOZ-001 / [WT-1547](https://wedotalent.atlassian.net/browse/WT-1547) | [Voz] AudioRecordButton — Gravação de Áudio + Transcrição (STT) | 5 | 🟡 Média | A1 | S2 |
| VOZ-002 / [WT-1545](https://wedotalent.atlassian.net/browse/WT-1545) | [Voz] AudioPlayer — Reprodução de Áudio com Controles | 3 | 🟡 Média | A1 | S2 |
| VOZ-003 / [WT-1552](https://wedotalent.atlassian.net/browse/WT-1552) | [Voz] TTS Backend — Geração de Áudio via OpenAI tts-1 | 5 | 🟡 Média | A1 | S2 |
| VOZ-004 / [WT-1551](https://wedotalent.atlassian.net/browse/WT-1551) | [Voz] Propagação de isVoiceMode — Estado Runtime no UI | 3 | 🟠 Alta | A1 | S2 |

**Subtotal É34:** 4 cards · 16 SPs

---

### 1.2 — `jira-cards-job-creation-lifecycle.md`

**Épico VGM — Gestão de Vagas**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| VGM-001 | [FULLSTACK] Modal de Escolha: LIA vs Criação Manual | 3 | 🟠 Alta | A1 | S1 |
| VGM-002 | [FULLSTACK] Formulário de Criação Manual de Vaga | 5 | 🟠 Alta | A1 | S1 |
| VGM-003 | [FULLSTACK] Navegação Automática pós-criação → Tab Configurações | 3 | 🟠 Alta | A1 | S1 |
| VGM-004 | [FULLSTACK] Tab Configurações da Vaga (Edição Completa) | 8 | 🟠 Alta | A1 | S1 |
| VGM-005 | [FULLSTACK] Publicação da Vaga — Auto-save + Link + Status Ativa | 5 | 🟠 Alta | A1 | S1 |
| VGM-006 | [FULLSTACK] Header da Vaga — Badge Status + Popover de Ações | 5 | 🟠 Alta | A1 | S1 |
| VGM-007 | [FULLSTACK] Badge de Triagem WSI no Header + Controle de Status | 3 | 🟡 Média | A1 | S2 |
| VGM-008 | [FULLSTACK] Modal Pausar / Reativar Vaga com Notificação de Candidatos | 5 | 🟠 Alta | A1 | S2 |
| VGM-009 | [FULLSTACK] Modal Fechar Vaga com Registro de Placement | 8 | 🟠 Alta | A1 | S2 |
| VGM-010 | [BACKEND] Endpoints de Notificação de Fechamento e Placement de Candidatos | 8 | 🟠 Alta | A1 | S3 |

**Subtotal VGM:** 10 cards · 53 SPs

---

### 1.3 — `diagnostico-agentes-mvp.md` + `ANALISE_COMPARATIVA_V5_vs_LIA.md`

**Épico WT-1505 — AUD: Auditoria e Compliance do Agente Python**

| Card | Jira Key | Título | SP | Prioridade | Fase | Sprint |
|------|----------|--------|----|------------|------|--------|
| AUD-001 | WT-1506 | Propagar AuditCallback para ReAct Agents | 2 | P0 🔴 | A1 | S1 |
| AUD-002 | WT-1507 | Rastrear Tools Chamadas por Nome | 1 | P1 🟠 | A1 | S1 |
| AUD-003 | WT-1508 | Circuit Breaker no Autonomous Agent | 2 | P1 🟠 | A1 | S1 |
| AUD-004 | WT-1509 | Retention/Cleanup de agent_executions | 1 | P2 🟡 | A1 | S2 |
| AUD-005 | WT-1510 | Storage Externo para Logs Pesados (S3/GCS) | 3 | P3 🟡 | A1 | S3 |
| AUD-006 | WT-1511 | Endpoints REST de Timeline | 3 | P3 🟡 | A1 | S3 |
| AUD-007 | WT-1512 | Métricas Prometheus | 3 | P3 🟡 | A1 | S3 |

**Subtotal AUD:** 7 cards · 15 SPs

---

**Épico [WT-1558](https://wedotalent.atlassian.net/browse/WT-1558) — É35: Arquitetura de IA: Agentes, Tools, Serviços e Automações**

| Card | Jira Key | Título | SP | Classificação | Sprint |
|------|----------|--------|----|:-------------:|:------:|
| AGT-000 | [WT-1559](https://wedotalent.atlassian.net/browse/WT-1559) | Padronização & Setup Base — 4-File Pattern + Checklist 18 Itens | 5 | 🟢 MVP CRÍTICO | S0 |
| AGT-002 | [WT-1560](https://wedotalent.atlassian.net/browse/WT-1560) | Infraestrutura Compartilhada — BaseAgent + FairnessGuard + PII + Audit | 21 | 🟢 MVP CRÍTICO | S0 |
| AGT-001 | [WT-1561](https://wedotalent.atlassian.net/browse/WT-1561) | MainOrchestrator — CascadedRouter 6-Tier + HITL + 9 Agentes | 13 | 🟢 MVP CRÍTICO | S0 |
| AGT-003 | [WT-1562](https://wedotalent.atlassian.net/browse/WT-1562) | ATSIntegrationService — Integração Bidirecional (Gupy) | 8 | 🟢 MVP CRÍTICO | S0 |
| AGT-004 | [WT-1563](https://wedotalent.atlassian.net/browse/WT-1563) | SourcingReActAgent — 14 Tools (ES + PGVector + WRF + Pearch) | 13 | 🟡 MVP SUPORTE | S1 |
| AGT-005 | [WT-1564](https://wedotalent.atlassian.net/browse/WT-1564) | CommunicationService + Adapters (Email + WhatsApp + Teams) | 13 | 🟢 MVP CRÍTICO | S1 |
| AGT-006 | [WT-1565](https://wedotalent.atlassian.net/browse/WT-1565) | JD Generator Service — LLM + FairnessGuard | 5 | 🟡 MVP SUPORTE | S1 |
| AGT-017 | [WT-1566](https://wedotalent.atlassian.net/browse/WT-1566) | HiringPolicyService — 4 Tools como Serviço | 5 | 🟡 MVP SUPORTE | S1 |
| AGT-015 | [WT-1567](https://wedotalent.atlassian.net/browse/WT-1567) | PipelineGateService — Gate 1 + Gate 2 + HITL | 8 | 🟢 MVP CRÍTICO | S1 |
| AGT-007 | [WT-1568](https://wedotalent.atlassian.net/browse/WT-1568) | WSIInterviewGraph — 7 Blocos + 15 Serviços + Scoring Determinístico | 21 | 🟢 MVP CRÍTICO | S2 |
| AGT-008 | [WT-1569](https://wedotalent.atlassian.net/browse/WT-1569) | CVScreeningReActAgent — 8 Tools (CV Parsing + Matching) | 8 | 🟡 MVP SUPORTE | S2 |
| AGT-009 | [WT-1570](https://wedotalent.atlassian.net/browse/WT-1570) | Chat Web Canal — WebSocket Backend + PromptInjectionGuard | 8 | 🟢 MVP CRÍTICO | S2 |
| AGT-016 | [WT-1571](https://wedotalent.atlassian.net/browse/WT-1571) | EventRetryOrchestrator — Celery Scheduler + DLQ | 8 | 🟡 MVP SUPORTE | S2 |
| AGT-010 | [WT-1572](https://wedotalent.atlassian.net/browse/WT-1572) | Follow-up 7d + Email Tracking | 8 | 🟡 MVP SUPORTE | S2 |
| AGT-FE-001 | [WT-1573](https://wedotalent.atlassian.net/browse/WT-1573) | Chat Web UI — Interface Candidato (Mobile-First + LGPD) | 8 | 🟢 MVP CRÍTICO | S2 |
| AGT-FE-002 | [WT-1574](https://wedotalent.atlassian.net/browse/WT-1574) | HITLConfirmCard — Aprovação do Consultor (5 Estados) | 5 | 🟢 MVP CRÍTICO | S2 |
| AGT-011 | [WT-1575](https://wedotalent.atlassian.net/browse/WT-1575) | Gate HITL Wiring — Interrupt → Approve → Resume (Redis + PG) | 8 | 🟢 MVP CRÍTICO | S3 |
| AGT-012 | [WT-1576](https://wedotalent.atlassian.net/browse/WT-1576) | SchedulingGraph — LangGraph 6 Nós (MS Graph + Calendar) | 13 | 🔵 PÓS-MVP | S3 |
| AGT-013 | [WT-1577](https://wedotalent.atlassian.net/browse/WT-1577) | Triagem Abandonada Monitor — Celery Beat 48h | 5 | 🔵 PÓS-MVP | S3 |
| AGT-014 | [WT-1578](https://wedotalent.atlassian.net/browse/WT-1578) | Teams/Slack Notifications — 3 Tipos Adaptive Cards | 3 | 🔵 PÓS-MVP | S3 |
| AGT-FE-003 | [WT-1579](https://wedotalent.atlassian.net/browse/WT-1579) | Pipeline Status UI — Dashboard Consultor | 5 | 🔵 PÓS-MVP | S3 |

**Subtotal É35 AGT:** 21 cards · 191 SPs

---

### 1.4 — Totais Consolidados

| Épico | Prefixo | Cards | SPs | Fase |
|-------|---------|-------|-----|------|
| É30 Saturação | SAT | 7 | 39 | Alpha 1 |
| É31 Chat Web Triagem | TRI | 8 | 61 | Alpha 1 |
| É32 Comunicação | COM | 5 | 20 | Alpha 1 |
| É33 Inscrição Web | INS | 3 | 18 | Alpha 1 |
| É34 Voz | VOZ | 4 | 16 | Alpha 1 |
| VGM Vagas | VGM | 10 | 53 | Alpha 1 |
| WT-1505 Auditoria | AUD/WT | 7 | 15 | Alpha 1 |
| É35 Arquitetura IA | AGT | 21 | 191 | Alpha 1 + Alpha 1.1 |
| **TOTAL** | | **65** | **413** | |

---

## 2. Roadmap MVP Alpha 1 — Por Passo do Fluxo

> **Referência:** Fluxo 2.1 do diagnóstico de agentes — 9 passos do recrutador + infraestrutura transversal.
> **Convenção:** cards em negrito = bloqueantes (dependências de outros cards). Sem eles os passos seguintes não podem ser executados.

---

### Visão Geral do Fluxo

```
Passo 1: Login           → Sem agente (infraestrutura)
Passo 2: Criar/Editar Vaga → Ag.8 ATS + Ag.1 JD Generator (Wizard)
Passo 3: Configurar WSI  → Ag.4+5 WSI Graph
Passo 4: Buscar Candidatos → Ag.2 Sourcing + Ag.3 Triagem CV + Ag.4+5 WSI
Passo 5: Gate 1          → Ag.9 Pipeline + Ag.7 Communication + Ag.8 ATS
Passo 6: Contato Email   → Ag.0 Orchestrator + Ag.7 Communication
Passo 7: Triagem WSI Chat → Ag.0 + Ag.4+5 WSI (candidato responde)
Passo 8: Gate 2          → Ag.9 Pipeline + Ag.7 Communication + Ag.8 ATS
Passo 9: Entrevista      → Ag.6 Scheduling + Ag.7 Communication
Transversal              → AUD: Auditoria, Circuit Breaker, Observabilidade
```

---

### 2.1 — Sprint S1 — Fundação (deve estar completo antes de qualquer fluxo)

> Sem o S1, nenhum fluxo funciona. São os cards que criam a base de dados, APIs e contratos que tudo mais consome.

**Prioridade máxima. Iniciar primeiro.**

| Ordem | Card | Título | SP | Passo do Fluxo | Agente |
|-------|------|--------|----|----------------|--------|
| 1 | **SAT-001** | [Saturação] Modelo de Dados — Pools Separados, Thresholds e Governance Rules | 8 | Transversal | — |
| 2 | **COM-001** | [Comunicação] CommunicationDispatcher — Mailgun + Mailgun + Meta WhatsApp + Tone Policy | 8 | Transversal | Ag.7 |
| 3 | **TRI-001** | [Chat Web] Tipos e Interfaces TypeScript — types.ts Completo | 3 | Passo 7 | Ag.4+5 |
| 4 | **VGM-001** | [FULLSTACK] Modal de Escolha: LIA vs Criação Manual | 3 | Passo 2 | Ag.1 |
| 5 | **VGM-002** | [FULLSTACK] Formulário de Criação Manual de Vaga | 5 | Passo 2 | Ag.1 |
| 6 | **VGM-003** | [FULLSTACK] Navegação Automática pós-criação → Tab Configurações | 3 | Passo 2 | Ag.1 |
| 7 | **VGM-004** | [FULLSTACK] Tab Configurações da Vaga (Edição Completa) | 8 | Passo 2 | Ag.1 |
| 8 | **VGM-005** | [FULLSTACK] Publicação da Vaga — Auto-save + Link + Status Ativa | 5 | Passo 2 | Ag.1 |
| 9 | **VGM-006** | [FULLSTACK] Header da Vaga — Badge Status + Popover de Ações | 5 | Passo 2 | Ag.1 |
| 10 | **TRI-008** | [Chat Web] Proxy Route Next.js — /api/backend-proxy/triagem/[...path] | 3 | Passo 7 | Ag.4+5 |
| 11 | SAT-002 | [Saturação] SaturationBadge — Badge Visual com Popover de Ações no Kanban | 5 | Passo 4 | — |
| 12 | SAT-003 | [Saturação] Seção de Configuração no Card Triagem (Settings → Pipeline) | 5 | Passo 3 | — |
| 13 | SAT-004 | [Saturação] Badges de Origem — Web, WhatsApp, Busca, ATS, Aguardando | 3 | Passo 4 | — |
| 14 | **SAT-007** | [Saturação] Gate 1 — Máquina de Estados da Inscrição Web até Triagem WSI | 5 | Passo 5 | Ag.9 |
| 15 | **AUD-001** | Propagar AuditCallback para ReAct Agents (WT-1506) | 2 | Transversal | Todos |
| 16 | **AUD-002** | Rastrear Tools Chamadas por Nome (WT-1507) | 1 | Transversal | Todos |
| 17 | **AUD-003** | Circuit Breaker no Autonomous Agent (WT-1508) | 2 | Transversal | Todos |

**S1 Total:** 17 cards · 74 SPs

---

### 2.2 — Sprint S2 — Fluxo Completo do Candidato

> Com S1 completo, S2 constrói o fluxo de ponta a ponta: o candidato se inscreve → é triado pelo WSI Chat → recebe feedback. E o pipeline do recrutador fica operacional para movimentar candidatos.

**Bloco A — Inscrição Pública (Passo 2 → Gate 1)**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 1 | **INS-003** | [Inscrição Web] Endpoint POST /public-vacancies/{slug}/apply | 5 | Passo 4 | SAT-001 |
| 2 | **INS-002** | [Inscrição Web] Página Pública da Vaga (/vagas/[slug]) | 5 | Passo 4 | INS-003 |
| 3 | **INS-001** | [Inscrição Web] Formulário Público — Candidatar-se Online | 8 | Passo 4 | INS-002, SAT-001 |
| 4 | VGM-007 | [FULLSTACK] Badge de Triagem WSI no Header + Controle de Status | 3 | Passo 2 | VGM-006 |
| 5 | VGM-008 | [FULLSTACK] Modal Pausar / Reativar Vaga com Notificação de Candidatos | 5 | Passo 2 | VGM-006 |
| 6 | VGM-009 | [FULLSTACK] Modal Fechar Vaga com Registro de Placement | 8 | Passo 9 | VGM-006 |

**Bloco B — Saturação e Controle de Pool (Passo 4 → Passo 7)**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 7 | **SAT-005** | [Saturação] Fila de Espera — awaiting_screening + Promoção Automática | 8 | Passo 4/7 | SAT-001, COM-001 |
| 8 | SAT-006 | [Saturação] Override Manual — Recrutador Aprova Candidato da Fila | 5 | Passo 5 | SAT-005, COM-001 |

**Bloco C — Comunicação Automática (Passo 5 → Passo 6 → Passo 7)**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 9 | **COM-002** | [Comunicação] Dispatch Automático #1 — Feedback de Triagem | 3 | Passo 5/6 | COM-001 |
| 10 | **COM-003** | [Comunicação] Dispatch Automático #2 — Rejeição ao Mudar de Stage | 3 | Passo 5/8 | COM-001 |
| 11 | **COM-004** | [Comunicação] Dispatch Automático #3 — Convite de Fila quando Slot Abre | 3 | Passo 6 | COM-001, SAT-005 |
| 12 | COM-005 | [Comunicação] Dispatch Automático #5 — Confirmação Pós-Conclusão da Triagem | 3 | Passo 7B | COM-001, TRI-005 |

**Bloco D — Chat Web de Triagem WSI (Passo 7)**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 13 | **TRI-005** | [Chat Web] TriagemSessionService — Motor IA Conversacional + WSI Scoring | 21 | Passo 7 | COM-001 |
| 14 | **TRI-002** | [Chat Web] Hook useTriagemChat — State Management + API Integration | 13 | Passo 7 | TRI-001, TRI-005 |
| 15 | TRI-003 | [Chat Web] WelcomeCard — Boas-Vindas com Branding da Empresa | 3 | Passo 7 | TRI-001 |
| 16 | TRI-004 | [Chat Web] MessageBubble — Bolha de Mensagem com AudioPlayer | 5 | Passo 7 | TRI-001, VOZ-002 |
| 17 | **TRI-006** | [Chat Web] InputBar — Campo de Texto + Gravação de Áudio + Controles de Voz | 5 | Passo 7 | TRI-001, VOZ-001 |
| 18 | **TRI-007** | [Chat Web] Página de Triagem — /triagem/[token] (~311L) | 8 | Passo 7 | TRI-001, TRI-002, TRI-003, TRI-004, TRI-006 |

**Bloco E — Voz Bidirecional (Passo 7 — paralelo ao Chat Web)**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 19 | VOZ-003 | [Voz] TTS Backend — Geração de Áudio via OpenAI tts-1 | 5 | Passo 7 | — |
| 20 | VOZ-002 | [Voz] AudioPlayer — Reprodução de Áudio com Controles | 3 | Passo 7 | — |
| 21 | VOZ-001 | [Voz] AudioRecordButton — Gravação de Áudio + STT | 5 | Passo 7 | — |
| 22 | VOZ-004 | [Voz] Propagação de isVoiceMode — Estado Runtime no UI | 3 | Passo 7 | TRI-002, TRI-007 |

**Bloco F — Auditoria S2**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 23 | AUD-004 | Retention/Cleanup de agent_executions (WT-1509) | 1 | Transversal | AUD-001 |

**S2 Total:** 23 cards · 131 SPs

---

### 2.3 — Sprint S3 — Refinamentos, Observabilidade e Alpha 2

> Com S1 + S2, o fluxo MVP Alpha 1 está completo. S3 adiciona observabilidade e prepara Alpha 2.

**Bloco A — Auditoria e Observabilidade**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 1 | AUD-005 | Storage Externo para Logs Pesados S3/GCS (WT-1510) | 3 | Transversal | AUD-001 |
| 2 | AUD-006 | Endpoints REST de Timeline (WT-1511) | 3 | Transversal | AUD-001 |
| 3 | AUD-007 | Métricas Prometheus (WT-1512) | 3 | Transversal | AUD-001 |

**Bloco B — Gestão de Vagas S3**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 4 | VGM-010 | [BACKEND] Endpoints de Notificação de Fechamento e Placement de Candidatos | 8 | Passo 9 | VGM-009 |

**S3 Total:** 4 cards · 17 SPs

---

### 2.4 — Mapa de Passos → Cards (visão inversa)

| Passo do Fluxo | Agente(s) | Cards do Sprint S1 | Cards do Sprint S2 | Cards S3+ |
|---|---|---|---|---|
| Passo 2 — Criar/Editar Vaga | Ag.1 JD Generator, Ag.8 ATS | VGM-001→008 | VGM-009, VGM-010 | — |
| Passo 4 — Buscar Candidatos | Ag.2 Sourcing, Ag.3 Triagem | SAT-001, SAT-002, SAT-004, SAT-007 | INS-001→003, SAT-005, SAT-006 | — |
| Passo 6 — Contato Email | Ag.0 Orch, Ag.7 Comm | COM-001 | COM-004, COM-005 | — |
| Passo 7 — Triagem WSI Chat | Ag.4+5 WSI, Ag.0 Orch | TRI-001 | TRI-002→005, VOZ-001→004 | — |
| Transversal — Auditoria | Todos | AUD-001→003 | AUD-004 | AUD-005→007 |

---


### Legenda de Tags Padronizadas

| Tag | Significado |
|-----|-------------|
| `backend` | Endpoint, service, ou lógica Python/FastAPI no lia-agent-system |
| `frontend` | Componente, hook, ou página TypeScript/React no plataforma-lia |
| `fullstack` | Card com mudanças obrigatórias em ambos os lados |
| `dados` | Modelo de banco de dados, migração, schema PostgreSQL |
| `IA` | Agente ReAct, LLM, prompt engineering, scoring, governance IA |
| `comunicacao` | Email (Mailgun), WhatsApp (Meta API), SMS, notificação |
| `voz` | TTS (OpenAI tts-1), STT (Deepgram/Whisper), áudio |
| `multi-tenant` | Isolamento por company_id, configuração por empresa |

### Mapa de Agentes IA → Cards

| Agente | Domain | Papel no MVP | Cards Impactados |
|--------|--------|--------------|-----------------|
| **Orchestrator** | core | Roteamento de conversa, LLM cascade | TRI-005, COM-001 |
| **PipelineReActAgent** | cv_screening | Kanban, movimentação de candidatos | SAT-005, SAT-007 |
| **WizardReActAgent** | job_management | Criação e enriquecimento de vagas | VGM-001→005 |
| **CommunicationReActAgent** | communication | Envio multicanal, templates | COM-001→005 |
| **PolicyReActAgent** | policy | Políticas de saturação, compliance | SAT-001, SAT-003 |
| **KanbanReActAgent** | recruiter_assistant | Análise de pipeline e saturação | SAT-002, SAT-004 |
| **SourceReActAgent** | sourcing | Busca ativa de candidatos | SAT-001 (pool sourcing) |
| **AnalyticsReActAgent** | analytics | KPIs, relatórios, funnel analysis | AUD-006, AUD-007 |

### Modelos de Banco de Dados Relevantes (PostgreSQL)

| Tabela | Modelo SQLAlchemy | Campos Críticos MVP |
|--------|-------------------|---------------------|
| `job_vacancies` | `lia_models/job_vacancy.py` | governance_rules (JSONB), status, title |
| `vacancy_candidates` | `lia_models/candidate.py` | origin, status, lia_score, additional_data |
| `company_profiles` | `lia_models/company.py` | additional_data.saturation_settings |
| `triagem_sessions` | `lia_models/triagem.py` | token, status, voice_mode, wsi_final_score |
| `triagem_messages` | `lia_models/triagem.py` | role, content, block_index, audio_base64 |
| `communication_history` | `lia_models/communication_history.py` | channel, status, template_id |
| `communication_matrix` | `lia_models/communication_matrix.py` | event_type, channels, tone |
| `email_templates` | `lia_models/email_template.py` | name, subject, body, variables |
| `whatsapp_conversations` | `lia_models/whatsapp_conversation.py` | phone, status, provider |
| `voice_screenings` | `lia_models/voice_screening.py` | status, audio_url, transcript |
| `audit_logs` | `lia_models/audit_log.py` | agent_name, decision_type, reasoning |
| `screening_questions` | `lia_models/screening_question.py` | question, block, weight |
| `recruitment_stages` | `lia_models/recruitment_stages.py` | name, display_name, order |

### Stack de Serviços de Comunicação

```
┌─────────────────────────────────────────────────────┐
│              MultiChannelService                     │
│  lia-agent-system/app/shared/channels/              │
├─────────────────────────────────────────────────────┤
│  ChannelRouter (fallback: WhatsApp → Email → SMS)   │
├──────────┬──────────┬──────────┬────────────────────┤
│ WhatsApp │  Email   │   SMS    │  MS Teams          │
│ Adapter  │ Adapter  │ Adapter  │  Adapter           │
├──────────┼──────────┼──────────┼────────────────────┤
│ Meta API │ Mailgun  │ Twilio   │  Graph API         │
│(primário)│(primário)│  SMS     │  (pendente)        │
│ Twilio   │ Resend   │          │                    │
│(fallback)│(fallback)│          │                    │
└──────────┴──────────┴──────────┴────────────────────┘
Env vars: MAILGUN_API_KEY, MAILGUN_DOMAIN, MAILGUN_FROM_EMAIL
          WHATSAPP_META_TOKEN, WHATSAPP_PHONE_ID
          TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
```



### Tools do Tool Registry por Agente (91 tools Alpha 1)

> **Fonte:** `diagnostico-agentes-mvp.md` §8 + §14. Cada agente só pode usar as tools registradas em seu `_tool_registry.py`.

| Agente (LIA) | Tools | Tipo | Cards Impactados | Arquivo Registry |
|-------------|:-----:|------|-----------------|------------------|
| MainOrchestrator (Ag.0) | 9 | Orchestrator | TRI-005, COM-001 | `app/orchestrator/orchestrator.py` |
| Job Wizard (Ag.1) | 9 | ReAct + Graph | VGM-001→005 | `app/domains/job_management/agents/job_wizard_tool_registry.py` |
| Sourcing (Ag.2) | 14 | ReAct | SAT-001 (pool sourcing) | `app/domains/sourcing/agents/sourcing_tool_registry.py` |
| CV Screening (Ag.3) | 13 | ReAct | SAT-005, TRI-005 | `app/domains/cv_screening/agents/pipeline_tool_registry.py` |
| WSI Interview (Ag.4+5) | 6 nós | StateGraph | TRI-005, TRI-007 | `app/domains/cv_screening/agents/wsi_interview_graph.py` |
| Scheduling (Ag.6) | 6 nós | StateGraph | (pós-Alpha) | `app/domains/interview_scheduling/agents/interview_graph.py` |
| Communication (Ag.7) | 5 | ReAct | COM-001→005 | `app/domains/communication/agents/communication_tool_registry.py` |
| ATS Integration (Ag.8) | 5 | ReAct | (serviço REST) | `app/domains/ats_integration/agents/ats_tool_registry.py` |
| Pipeline Transition (Ag.9) | 20 | ReAct + HITL | SAT-005, SAT-007 | `app/domains/cv_screening/agents/pipeline_tool_registry.py` |
| Hiring Policy (Ag.10) | 4 | Serviço | SAT-003 | `app/domains/policy/agents/agent.py` |
| **Total Alpha 1** | **91** | | | |

### Shared Tools (disponíveis para todos os agentes via EnhancedAgentMixin)

| Tool | O que faz | Arquivo |
|------|----------|---------|
| `get_pipeline_health` | Detecta gargalos e estagnação | `app/shared/tools/insight_tools.py` |
| `get_conversion_rates` | Taxas de conversão entre estágios | `app/shared/tools/insight_tools.py` |
| `get_time_to_fill` | Duração média de preenchimento | `app/shared/tools/insight_tools.py` |
| `check_stagnant_candidates` | Candidatos parados >7 dias | `app/shared/tools/proactive_tools.py` |
| `check_pipeline_risks` | Scan holístico de saúde | `app/shared/tools/proactive_tools.py` |
| `predict_dropout_risk` | Probabilidade de desistência | `app/shared/tools/predictive_tools.py` |
| `export_candidates` | Exporta lista CSV/XLSX/JSON | `app/shared/tools/export_tools.py` |
| `generate_report` | Relatórios PDF de recrutamento | `app/shared/tools/export_tools.py` |

### NFRs — Requisitos Não-Funcionais por Componente

> **Fonte:** `diagnostico-agentes-mvp.md` §20. Critérios de aceitação mensuráveis para produção.

**Latência:**

| Componente | P50 | P95 | Limite Máximo | Cards |
|-----------|:---:|:---:|:-------------:|-------|
| WebSocket handshake | <100ms | <300ms | 1s | TRI-002, TRI-007 |
| WSI — resposta por turno | <2s | <4s | 8s | TRI-005 |
| Sourcing — query inicial | <1s | <3s | 5s | SAT-001 |
| Email send | <2s | <5s | 10s | COM-001→005 |
| Gate HITL — approve | <500ms | <1s | 2s | SAT-005, SAT-007 |
| CV parsing | <3s | <8s | 15s | INS-003 |
| TTS audio generation | <1s | <3s | 5s | VOZ-003 |
| STT transcription | <2s | <5s | 10s | VOZ-001 |

**Disponibilidade e Resiliência:**

| Componente | Uptime Alvo | Fallback | Cards |
|-----------|:-----------:|---------|-------|
| Claude (LLM primário) | 99,5% | → OpenAI → Gemini | TRI-005, VGM-001 |
| PostgreSQL | 99,9% | Auto-failover | Todos |
| Redis | 99,5% | Degradar sem cache | TRI-002, SAT-001 |
| Mailgun (email) | 99% | → Resend | COM-001→005 |
| Meta WhatsApp API | 95% | → Twilio SMS | COM-001 |

**Rate Limits por Tenant (plano):**

| Recurso | Starter | Pro | Business | Enterprise | Cards |
|---------|:-------:|:---:|:--------:|:----------:|-------|
| Requisições LLM/hora | 100 | 500 | 2.000 | Ilimitado | TRI-005, VGM-001 |
| Emails/dia | 200 | 1.000 | 5.000 | Ilimitado | COM-001→005 |
| Sessões WSI simultâneas | 5 | 20 | 100 | Ilimitado | TRI-005, TRI-007 |
| Candidatos/busca | 50 | 200 | 1.000 | Ilimitado | SAT-001 |

**Implementação:** `app/orchestrator/tenant_budget.py` + `app/services/token_budget_service.py`

### Env Vars Necessárias por Épico

> **Fonte:** `diagnostico-agentes-mvp.md` §0B.1. Configurar ANTES de implementar o card.

| Épico | Variáveis de Ambiente | Quando |
|-------|----------------------|--------|
| **SAT** (Saturação) | `DATABASE_URL`, `REDIS_URL` | S1 |
| **TRI** (Triagem) | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `LANGSMITH_API_KEY` | S2 |
| **COM** (Comunicação) | `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `MAILGUN_FROM_EMAIL`, `WHATSAPP_META_TOKEN`, `WHATSAPP_PHONE_ID`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` | S2 |
| **INS** (Inscrição) | `DATABASE_URL` (nenhuma adicional — reutiliza SAT) | S2 |
| **VOZ** (Voz) | `OPENAI_API_KEY` (TTS tts-1), `DEEPGRAM_API_KEY` (STT primário) | S2 |
| **VGM** (Vagas) | `ANTHROPIC_API_KEY` (JD Generator), `DATABASE_URL` | S1 |
| **AUD** (Auditoria) | `LANGSMITH_API_KEY`, `AWS_S3_BUCKET` (storage externo), `PROMETHEUS_PORT` | S1/S3 |

### LLM Cascade — Qual Modelo Cada Card Usa

> **Fonte:** `diagnostico-agentes-mvp.md` §13 + `app/orchestrator/llm_cascade.py`. Cascade: Haiku → Sonnet → Opus.

| Tier | Modelo | Temperatura | Uso nos Cards | Custo Relativo |
|------|--------|:-----------:|--------------|:--------------:|
| **Tier 3a (Fast)** | Claude Haiku | 0.1 | Router de intenções (TRI-002 roteamento), classificação rápida | $ |
| **Tier 3b (Mid)** | Claude Sonnet | 0.3 | TRI-005 (WSI perguntas/scoring), VGM-001 (JD generation), COM-001 (feedback personalizado) | $$ |
| **Tier 3c (Power)** | Claude Opus | 0.3 | Análises complexas, rubric evaluation (SAT-001 scoring avançado) | $$$ |
| **Fallback 1** | OpenAI GPT-4 | 0.3 | Quando Anthropic indisponível — todos os cards com IA | $$ |
| **Fallback 2** | Gemini Pro | 0.3 | Quando Anthropic + OpenAI indisponíveis | $$ |
| **Embeddings** | Gemini text-embedding-004 | — | SAT-001 (busca semântica), TRI-005 (cache semântico) | $ |
| **TTS** | OpenAI tts-1 (voice "nova") | — | VOZ-003 (geração de áudio) | $ |
| **STT** | Deepgram Nova-2 | — | VOZ-001 (transcrição de áudio) | $ |

**Configuração:** `libs/config/lia_config/config.py` → `LLMSettings` (model names, temperatures, cascade thresholds)

### HITL — Mapa de Confirmação Humana por Ação

> **Fonte:** `diagnostico-agentes-mvp.md` §21.6. Ações que requerem aprovação do recrutador antes de executar.

| Ação | Confirmação | Risco | Cards Impactados |
|------|:-----------:|-------|-----------------|
| `analisar_perfil` | NÃO | Baixo | SAT-001 |
| `disparar_triagem` | NÃO | Baixo | TRI-005 |
| `scoring_wsi` | NÃO | Baixo | TRI-005 |
| `buscar_candidatos` | NÃO | Baixo | SAT-001 |
| `gerar_jd` | NÃO | Baixo | VGM-001 |
| `mover_candidato` | **SIM** | Médio | SAT-005, SAT-007 |
| `aprovar_candidato` | **SIM** | Médio | SAT-005 |
| `agendar_entrevista` | **SIM** | Médio | (pós-Alpha) |
| `enviar_email` | **SIM** | Alto | COM-001→005 |
| `reprovar_candidato` | **SIM** | Alto | SAT-005, SAT-007 |
| `publicar_vaga` | **SIM** | Alto | VGM-005 |
| `enviar_whatsapp_massa` | **SIM** | Alto | COM-001 |
| `pausar_vaga` | **SIM** | Alto | VGM-008 |
| `fechar_vaga` | **SIM** | Alto | VGM-009 |

**Implementação:** `requires_confirmation=True` no `ToolDefinition` + `ActionExecutorService` (`app/orchestrator/action_executor.py`)

### Prompt Templates e YAMLs de Domínio

> **Fonte:** `diagnostico-agentes-mvp.md` §13B.5 + `app/prompts/domains/`.

| Domínio | YAML | Agente/Graph | Cards |
|---------|------|-------------|-------|
| `sourcing.yaml` | Busca de candidatos | SourcingReActAgent | SAT-001 |
| `cv_screening.yaml` | Triagem curricular + WSI | PipelineReActAgent, WSIGraph | SAT-005, TRI-005 |
| `communication.yaml` | Email, WhatsApp, notificação | CommunicationReActAgent | COM-001→005 |
| `job_management.yaml` | Criação/edição de vagas | WizardReActAgent, JobWizardGraph | VGM-001→005 |
| `ats_integration.yaml` | Sync ATS (Gupy/Pandapé) | ATSIntegrationAgent (serviço) | — |
| `analytics.yaml` | KPIs, relatórios | AnalyticsReActAgent | AUD-006, AUD-007 |
| `recruiter_assistant.yaml` | Kanban, pipeline | KanbanReActAgent | SAT-002 |
| `automation.yaml` | Jobs agendados | AutomationReActAgent | AUD-003 |
| Persona compartilhada | `app/prompts/shared/lia_persona.yaml` | Todos os agentes | Todos |

**Prompt Registry:** `app/shared/prompts/prompt_registry.py` — versionamento de prompts (ex: `orchestrator` v2.0.0)

### Limites Operacionais — Referência Rápida

> **Fonte:** `diagnostico-agentes-mvp.md` §21.7

| Recurso | Limite | Configuração | Cards |
|---------|--------|-------------|-------|
| LLM timeout (Claude/OpenAI) | 120 segundos | `shared/providers/llm_*.py` | Todos com IA |
| Max tool calls por request | 3 | `REACT_MAX_TOOL_CALLS` | Todos com agente |
| Max iterações ReActLoop | 5 | `ReActConfig.max_iterations` | Todos com agente |
| Rate limit por minuto | 200 req/min por tenant | Rate limiter middleware | Todos |
| Cache hot (Tier 1) | TTL 5 minutos | `cache_manager_service.py` | SAT-001, TRI-002 |
| Cache warm (Tier 2) | TTL 1 hora | idem | SAT-001 |
| Pearch searches/dia | 10 por tenant | PolicyEngine | SAT-001 |
| Voice screenings/dia | 20 por tenant | PolicyEngine | VOZ-003, VOZ-004 |
| Max tokens/request | 50.000 | PolicyEngine | TRI-005 |
| Max concurrent requests | 5 por tenant | PolicyEngine | TRI-005 |
| Duplicate action threshold | 2 | `REACT_DUPLICATE_THRESHOLD` | Todos com agente |
| Observation max chars | 5.000 | `REACT_OBSERVATION_MAX_CHARS` | Todos com agente |

### Anti-Patterns — NUNCA Faça Isso (Referência para Todos os Cards)

> **Fonte:** `diagnostico-agentes-mvp.md` §21.5

| Anti-Pattern | Consequência | Alternativa Correta |
|-------------|-------------|-------------------|
| Hardcodar regras por empresa | Impossível escalar multi-tenant | Use `CompanyHiringPolicy` no banco |
| Colocar dados sensíveis em logs | Violação LGPD (Art. 46) | Use `PIIMasking` antes de logar |
| Criar tool sem `try/except` | Erro não tratado crasha o ReActLoop | Sempre envolva em try/except com log |
| Mudar tool sem atualizar `STAGE_TOOLS` | Tool existe mas agente não pode usar | Atualizar STAGE_TOOLS junto com a tool |
| Lógica crítica apenas no prompt | LLM pode ignorar a regra | Implemente em código (tool ou guard) |
| Chamar LLM sem circuit breaker | Falha do provider derruba o sistema | Use `CircuitBreaker` para chamadas externas |
| Ignorar FairnessGuard no input | Viés discriminatório passa sem detecção | Sempre valide texto com `check()` |
| Retornar traceback ao usuário | UX ruim + expõe internals | Retorne mensagem amigável no catch |

### Infraestrutura Compartilhada Obrigatória (usada por todos os agentes)

> **Fonte:** `diagnostico-agentes-mvp.md` §13

| Componente | Arquivo | Função | Obrigatório |
|-----------|--------|--------|:-----------:|
| BaseAgent | `libs/agents-core/lia_agents_core/langgraph_react_base.py` | Base ReAct com lifecycle hooks | ✅ |
| EnhancedAgentMixin | `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` | Memória + guardrails + learning | ✅ |
| FairnessGuard | `app/shared/agents/fairness_guard.py` | 3 camadas (pre-prompt, post-response, aggregate) | ✅ |
| AuditCallback | `app/shared/compliance/audit_service.py` | Log estruturado de decisões IA | ✅ |
| PII Masking | `app/shared/pii_masking.py` | Masking LGPD (CPF, email, tel) | ✅ |
| PromptInjectionGuard | `app/shared/prompt_injection.py` | Detecção de prompt injection (177L) | ✅ |
| Token Budget | `app/services/token_budget_service.py` | Rate limiting por tenant/plano | ✅ |
| HITL Service | `app/services/hitl_service.py` | Human-in-the-Loop via LangGraph interrupt | ✅ |
| EmbeddingService | `app/shared/intelligence/embedding_service.py` | Gemini text-embedding-004 (768 dim) | ✅ |
| WorkingMemoryService | `app/shared/agents/working_memory.py` | Memória de trabalho persistente por sessão | ✅ |
| PolicyEngine | `app/orchestrator/policy_engine.py` | Guardrails antes/depois de cada execução | ✅ |
| CircuitBreaker | `app/shared/providers/` | Circuit breaker para APIs externas | ✅ |

### Migrations Alembic Necessárias (mínimo Alpha 1)

> **Fonte:** `diagnostico-agentes-mvp.md` §0B.2

| Migration | O que cria | Sprint | Cards Dependentes |
|-----------|-----------|:------:|------------------|
| `001`–`019` | Modelos base (candidates, jobs, pipeline, users) | Pré-req | Todos |
| `020_add_guardrails_table` | Tabela `guardrails` — regras de agentes por tenant | S0 | SAT-003, AUD-001 |
| `028_add_pgvector` | Extensão pgvector para embeddings | S0 | SAT-001 |
| `032_add_hitl_tables` | `hitl_pending_actions` + `hitl_audit_trail` | S0 | SAT-005, SAT-007 |
| `034_add_agent_quality_evaluations` | Avaliação qualidade do agente | S0 | AUD-001 |
| `035_add_user_agent_preferences` | Preferências de agente por usuário | S0 | — |
| `saturation_*` | Tabelas/campos de saturação | S1 | SAT-001→007 |
| `triagem_*` | `triagem_sessions`, `triagem_messages` | S2 | TRI-001→008 |
| `communication_*` | `communication_history`, `email_templates`, etc. | S2 | COM-001→005 |
| `voice_*` | `voice_screenings` | S2 | VOZ-001→004 |

**Comando:** `cd lia-agent-system && alembic upgrade head`

### Production Templates de Comunicação

> **Fonte:** `app/templates/communication_templates.py` + `docs/templates/biblioteca-templates-completa.md`

| Template | Arquivo | Cards |
|----------|---------|-------|
| Email convite para triagem WSI | `app/templates/communication_templates.py` | COM-001, COM-002 |
| Email feedback construtivo (Gate 1) | `app/templates/communication_templates.py` | COM-003 |
| Email feedback final (Gate 2) | `app/templates/communication_templates.py` | COM-003 |
| Email confirmação de inscrição | `app/templates/communication_templates.py` | INS-003, COM-005 |
| WhatsApp template — convite | `app/templates/communication_templates.py` | COM-001 |
| Email fila de espera (saturação) | `app/templates/communication_templates.py` | SAT-005, COM-004 |
| Email pausar/reativar vaga | `app/templates/communication_templates.py` | VGM-008 |
| Email fechamento de vaga | `app/templates/communication_templates.py` | VGM-010 |
| Relatório PDF de triagem | `app/templates/report_templates.py` | TRI-005, AUD-006 |
| Taxonomia de templates | `docs/templates/TAXONOMIA_TEMPLATES.md` | Referência |
| Biblioteca completa | `docs/templates/biblioteca-templates-completa.md` | Referência |

### Webhooks e Pontos de Integração Externa

> **Fonte:** `app/api/v1/external_webhooks.py` + docs de integração

| Webhook/Integração | Endpoint | Cards | Direção |
|---------------------|---------|-------|---------|
| ATS (Gupy/Pandapé) sync | `POST /api/v1/webhooks/ats` | VGM-001 (import), SAT-001 | Inbound |
| Merge.dev ATS connector | `POST /api/v1/webhooks/merge` | VGM-001 | Inbound |
| WorkOS SCIM/Auth | `POST /api/v1/webhooks/workos` | (Auth — cross-cutting) | Inbound |
| Billing (Iugu/Vindi) | `POST /api/v1/webhooks/billing` | (Billing — pós-Alpha) | Inbound |
| Deepgram transcription | `POST /api/v1/webhooks/deepgram` | VOZ-001 | Inbound |
| Mailgun delivery status | `POST /api/v1/webhooks/mailgun` | COM-001 (tracking) | Inbound |
| Meta WhatsApp status | `POST /api/v1/webhooks/whatsapp` | COM-001 | Inbound |
| Job status notification | `POST /api/v1/job-status-webhooks` | VGM-008, VGM-010 | Outbound |

### Checklist de Impacto — 12 Dimensões (Mini Feature-Impact por Card)

> **Fonte:** `.agents/skills/feature-impact/SKILL.md`. Antes de implementar qualquer card, verificar se há impacto nessas dimensões.

| # | Dimensão | Verificação Rápida | Cards com Impacto |
|---|---------|-------------------|------------------|
| 1 | Frontend | Novas páginas, componentes, hooks, proxy routes? | SAT-002→004, TRI-001→007, INS-001→002, VOZ-001→002, VGM-001→009 |
| 2 | Backend API | Novos endpoints REST, schemas Pydantic? | SAT-001, TRI-005, COM-001, VGM-010, AUD-006 |
| 3 | Serviços | Novos serviços ou ajuste em existentes? | SAT-005, TRI-005, COM-001, VOZ-003, AUD-003 |
| 4 | Banco de Dados | Novas tabelas, campos, migrations, índices? | SAT-001, TRI-005, COM-001, INS-003, VOZ-003 |
| 5 | Agentes IA | Tools, prompts, state machine, domínios? | TRI-005, VGM-001, COM-001, SAT-001 |
| 6 | Comunicações | Email, WhatsApp, Teams, notificações? | COM-001→005, SAT-005, VGM-008, VGM-010 |
| 7 | Integrações | WorkOS, ATS, Deepgram, Pearch? | VOZ-001, INS-003, VGM-001 |
| 8 | Compliance/LGPD | PII, consentimento, auditoria, retenção? | AUD-001→007, TRI-005, COM-001 |
| 9 | Segurança | Multi-tenant, CORS, rate limiting? | Todos (company_id obrigatório) |
| 10 | Infra/Async | Celery tasks, Redis cache, migrations? | SAT-005, AUD-004, COM-001 |
| 11 | Observabilidade | Logs, métricas Prometheus, LangSmith? | AUD-001, AUD-007 |
| 12 | Testes | Unitários, integração, fairness, edge cases? | Todos |

### Checklist de Conformidade do Agente (18 itens — obrigatório para cards com IA)

> **Fonte:** `diagnostico-agentes-mvp.md` §13B.9. Todo card que envolve agente ReAct/Graph deve passar nestes 18 itens antes de "Done".

| # | Critério | Cards |
|---|---------|-------|
| 1 | Padrão 4-file completo (agent, prompt, tools, context) | TRI-005, VGM-001, COM-001, SAT-001 |
| 2 | EnhancedAgentMixin herdado | Todos com agente |
| 3 | FairnessGuard wired | Todos com agente |
| 4 | PromptInjectionGuard wired | TRI-005, TRI-007 |
| 5 | AuditCallback registrado | Todos com agente (AUD-001) |
| 6 | `company_id` propagado em TODAS as queries | Todos |
| 7 | PII Masking ativo nos logs | Todos |
| 8 | PolicyEngine consultado antes de execução | Todos com agente |
| 9 | Circuit breaker em chamadas LLM/API | Todos com IA (AUD-003) |
| 10 | System prompt com 10 seções obrigatórias | TRI-005, VGM-001, COM-001 |
| 11 | STAGE_TOOLS correto | TRI-005, COM-001 |
| 12 | Testes unitários (mín. 5 por tool) | Todos |
| 13 | Testes fairness (5+ queries discriminatórias bloqueadas) | TRI-005, VGM-001, COM-001 |
| 14 | Testes integração (fluxo completo com mocks) | Todos |
| 15 | Sem dados hardcoded (CPF, email, tel) | Todos |
| 16 | Sem secrets em código | Todos |
| 17 | Logs sem PII | Todos |
| 18 | FRIA documentada (se toma decisões sobre candidatos) | TRI-005, SAT-005 |


---

## 3. Cards Completos — É30 Saturação e Controle de Pools (SAT) — Épico [WT-1518](https://wedotalent.atlassian.net/browse/WT-1518)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md` §6
> **Épico:** É30 — Saturação e Controle de Pools
> **Status Jira:** SAT-001→007 = WT-1523→WT-1530 (criados)

### SAT-001: Modelo de Dados e Endpoints de Saturação

```yaml
Titulo: "[Saturação] Modelo de Dados — Pools Separados, Thresholds e Governance Rules"
Tipo: Feature
Area: Backend
Sprint: S1
Pontos: 8
Prioridade: Crítica
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend + Frontend proxy)
Fase: MVP Alpha 1
Tags: [backend, api, database, saturação, multi-tenant]
Referências IA: Nenhuma (feature de regra de negócio pura)

Descricao: |
  Criar o modelo de dados e endpoints REST para o sistema de controle de
  saturação com pools separados (orgânico vs sourcing). Cada vaga tem
  limites independentes para candidatos orgânicos (web/whatsapp) e de
  busca ativa (sourcing/ats), configuráveis globalmente por empresa e
  com override por vaga.
  
  O sistema separa candidatos em 2 pools baseados no campo `origin` da
  tabela VacancyCandidate:
  - Pool Orgânico: origin IN ('web', 'whatsapp') + origin IS NULL
  - Pool Sourcing: origin IN ('sourcing', 'ats')
  
  Defaults do sistema: threshold_web=20, threshold_sourcing=20,
  unlock_increment=10, unlock_hours=24.

Historia de Usuario: |
  Como recrutador, eu quero definir limites separados para candidatos
  que se inscrevem voluntariamente e candidatos que eu busco ativamente,
  para gerenciar melhor o volume do pipeline por vaga.

Regras de Negocio:
  1. Cada pool (orgânico/sourcing) tem threshold independente
  2. Empresa define defaults globais em company_profiles.additional_data.saturation_settings
  3. Vaga pode ter overrides em job_vacancies.governance_rules (threshold_web, threshold_sourcing)
  4. Resolução de threshold: override vaga > default empresa > default sistema (20)
  5. Candidatos com status IN ('rejected', 'declined', 'withdrawn') NÃO contam no pool
  6. Candidatos com origin IS NULL contam como orgânicos
  7. Isolamento multi-tenant: toda query filtra por vacancy_id (que pertence a company_id)
  8. saturation_disabled_until (ISO datetime) permite bypass temporário de AMBOS os pools
  9. Quando bypass ativo: is_saturated = False para ambos os pools

Requisitos Tecnicos:
  Backend — Schemas Pydantic:
    - ChannelCounts(web: int, whatsapp: int, sourcing: int, ats: int)
    - ChannelSaturation(count: int, threshold: int, is_saturated: bool,
        slots_remaining: int, percentage: float)
    - SaturationSettingsRequest(threshold_web?, threshold_sourcing?,
        unlock_increment?, unlock_hours?) — todos Optional com ge/le validação
    - SaturationSettingsResponse(company_id, threshold_web, threshold_sourcing,
        unlock_increment, unlock_hours, updated_at)
    - SaturationStatusResponse (ver schemas completos abaixo)
    - UnlockPipelineRequest(action: "increase_threshold"|"disable_temporarily",
        new_threshold?, disable_hours?)
    - UnlockPipelineResponse(success, message, new_threshold?,
        saturation_disabled_until?)
  
  Backend — Endpoints:
    GET  /api/v1/settings/saturation?company_id={id}
      Headers: X-Company-ID, X-User-ID
      Resposta: SaturationSettingsResponse
      Fluxo: _find_company(db, company_id) → _get_company_saturation_defaults()
    
    PUT  /api/v1/settings/saturation?company_id={id}
      Headers: X-Company-ID, X-User-ID
      Body: SaturationSettingsRequest (partial update)
      Fluxo: Atualiza company.additional_data.saturation_settings
      ⚠️ Não altera thresholds de vagas existentes, só o default futuro
    
    GET  /api/v1/job-vacancies/{job_id}/saturation-status
      Resposta completa: {
        job_id, approved_count (total ativo), saturation_threshold (legacy),
        is_saturated (OR de ambos pools), slots_remaining (soma),
        recommendation ("continue_screening"|"pause_screening"),
        saturation_percentage (total/total_threshold * 100),
        queued_count (awaiting_screening + sourced),
        last_screened_at, saturation_disabled_until,
        counts_by_channel: { web, whatsapp, sourcing, ats },
        organic: { count, threshold, is_saturated, slots_remaining, percentage },
        sourcing: { count, threshold, is_saturated, slots_remaining, percentage },
        threshold_web, threshold_sourcing, unlock_increment, unlock_hours
      }
      Fluxo interno:
        1. Busca vacancy e company
        2. _resolve_thresholds(governance_rules, company_defaults)
        3. Query com func.count().filter() por origin (5 contagens separadas)
        4. Calcula organic_count = web + whatsapp + unknown
        5. Calcula source_count = sourcing + ats
        6. Verifica bypass (saturation_disabled_until > utcnow)
    
    POST /api/v1/job-vacancies/{job_id}/unlock-pipeline
      Headers: X-Company-ID, X-User-ID
      Body: UnlockPipelineRequest
      Ação "increase_threshold":
        - Calcula increment = new_threshold - current_saturation_threshold
        - Se increment < 1: usa DEFAULT_UNLOCK_INCREMENT (10)
        - Atualiza governance_rules: saturation_threshold, threshold_web (+increment),
          threshold_sourcing (+increment)
        - Chama process_screening_queue(max_promote=increment)
      Ação "disable_temporarily":
        - Grava saturation_disabled_until = utcnow + disable_hours
        - Chama process_screening_queue(max_promote=5)
    
    GET  /api/v1/job-vacancies/{job_id}/screening-queue
      Resposta: { job_id, queued_count, candidates[] }
      Ordenação: lia_score DESC NULLS LAST, created_at ASC
    
    POST /api/v1/job-vacancies/{job_id}/process-queue
      Body: { max_promote: int (1-50, default 1) }
      Chama: process_screening_queue() de automation_handlers.py
  
  Frontend — Proxy Routes:
    src/app/api/backend-proxy/settings/saturation/route.ts
      → Proxy GET/PUT para /api/v1/settings/saturation
    src/app/api/backend-proxy/job-vacancies/[jobId]/saturation-status/route.ts
      → Proxy GET para /api/v1/job-vacancies/{jobId}/saturation-status
  
  Database — Campos existentes usados:
    job_vacancies.governance_rules (JSONB): threshold_web, threshold_sourcing,
      unlock_increment, unlock_hours, saturation_threshold (legacy),
      saturation_disabled_until
    company_profiles.additional_data (JSONB): saturation_settings {
      threshold_web, threshold_sourcing, unlock_increment, unlock_hours }
    vacancy_candidates.origin (VARCHAR): 'web', 'whatsapp', 'sourcing', 'ats', NULL
    vacancy_candidates.status (VARCHAR): 'awaiting_screening' para fila

  Constantes no código:
    EXCLUDED_STATUSES = ('rejected', 'declined', 'withdrawn')
    ORGANIC_ORIGINS = ('web', 'whatsapp')
    SOURCING_ORIGINS = ('sourcing', 'ats')
    DEFAULT_SATURATION_THRESHOLD = 20
    DEFAULT_UNLOCK_INCREMENT = 10
    DEFAULT_UNLOCK_HOURS = 24

DoD:
  - [x] Schemas Pydantic para todas as requests/responses
  - [x] 6 endpoints implementados e testados
  - [x] Resolução de thresholds com 3 níveis (vaga > empresa > sistema)
  - [x] Query por origin com func.count().filter() (não N+1)
  - [x] Bypass temporário (saturation_disabled_until) funcional
  - [x] process_screening_queue chamado após unlock
  - [x] Headers X-Company-ID e X-User-ID aceitos em endpoints de settings
  - [ ] Testes unitários para cada endpoint
  - [ ] Testes de integração para resolução de thresholds

Criterios de Aceitacao:
  - [x] GET /saturation-status retorna contagens separadas por pool
  - [x] PUT /settings/saturation com threshold_web=30 altera default da empresa
  - [x] unlock-pipeline com action="increase_threshold" incrementa AMBOS os pools
  - [x] unlock-pipeline com action="disable_temporarily" define bypass de 24h
  - [x] Durante bypass, is_saturated retorna false para ambos pools
  - [x] Candidatos rejected/declined/withdrawn NÃO são contados
  - [x] Candidatos com origin NULL são contados como orgânicos

Como Testar:
  1. Criar vaga com 20 candidatos orgânicos
  2. GET /saturation-status → organic.is_saturated = true, organic.percentage = 100%
  3. POST /unlock-pipeline { action: "increase_threshold", new_threshold: 30 }
  4. GET /saturation-status → organic.threshold = 30, is_saturated = false
  5. PUT /settings/saturation { threshold_sourcing: 50 } → defaults atualizados
  6. Criar nova vaga → herda threshold_sourcing = 50 da empresa

Inteligencia e Automacao:
  Agentes Envolvidos:
    - PolicyReActAgent (domain=policy): Consulta/valida políticas de saturação da empresa
    - KanbanReActAgent (domain=kanban): Consome dados de saturação para análise de pipeline
  Tools Utilizadas:
    - get_pipeline_summary: Retorna saturation_status por vaga no overview do kanban
    - validate_policy_compliance: Valida se thresholds estão dentro dos limites da empresa
  Servicos IA:
    - SaturationStatusService (saturation.py): Calcula is_saturated por pool (orgânico/sourcing)
    - Fórmula: activeInScreening / max_screening_slots (per pool)
    - governance_rules JSONB: Armazena thresholds configuráveis por vaga
  Modelo LLM: Nenhum — lógica de saturação é 100% determinística (regras de negócio)
  Governanca e Compliance:
    - PolicyEngine: Regra "max_candidates_per_vacancy" (default 500) aplicada como teto absoluto
    - Multi-tenant isolation: Toda query filtra por vacancy_id → company_id (sem cross-tenant leak)
    - saturation_disabled_until: Bypass temporário de ambos os pools, registrado em audit_log
    - IndustryDefaults: Financeiro (BCB 498) pode ter allow_global_search=False
  Fairness e Bias:
    - Pools separados (orgânico vs sourcing) evitam que sourcing ativo prejudique candidatos orgânicos
    - Thresholds independentes garantem equidade entre canais de entrada
    - BiasAuditService: Pode gerar snapshot de distribuição demográfica por pool (futuro)
  Automacoes/Triggers:
    - unlock-pipeline (increase_threshold/disable_temporarily) → dispara process_screening_queue
    - Mudança de status de candidato (rejected/withdrawn) → reavalia is_saturated → pode promover fila
  Fallbacks:
    - governance_rules ausente → defaults: max_organic=10, max_sourcing=5
    - saturation_disabled_until expirado → reativa automaticamente
    - Erro no cálculo → is_saturated=False (candidato NÃO é bloqueado)

Arquivos de Referencia (Prototipo LIA):
  - backend: lia-agent-system/app/api/v1/saturation.py (496L — código completo)
  - model: lia-agent-system/app/models/job_vacancy.py (governance_rules JSONB)
  - model: lia-agent-system/app/models/candidate.py (VacancyCandidate.origin)
  - model: lia-agent-system/app/models/company.py (additional_data JSONB)
  - proxy: plataforma-lia/src/app/api/backend-proxy/settings/saturation/route.ts
  - proxy: plataforma-lia/src/app/api/backend-proxy/job-vacancies/[jobId]/saturation-status/route.ts

Arquivos Adicionais no Replit (Código Existente):
  - handler: lia-agent-system/app/services/automation_handlers.py (process_screening_queue)
  - schema: lia-agent-system/app/schemas/saturation.py
  - model-db: lia-agent-system/libs/models/lia_models/job_vacancy.py (governance_rules JSONB)
  - model-db: lia-agent-system/libs/models/lia_models/candidate.py (VacancyCandidate)
  - model-db: lia-agent-system/libs/models/lia_models/company.py (additional_data JSONB)

Tabelas PostgreSQL:
  job_vacancies (governance_rules), company_profiles (additional_data), vacancy_candidates (origin, status)
```


---

### SAT-002: SaturationBadge — Componente Visual no Kanban

```yaml
Titulo: "[Saturação] SaturationBadge — Badge Visual com Popover de Ações no Kanban"
Tipo: Feature
Area: Frontend
Sprint: S1
Pontos: 5
Prioridade: Alta
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, kanban, saturação, design-system]
Dependências: SAT-001

Descricao: |
  Componente React (~267L) que exibe o estado de saturação de uma vaga
  no header do Kanban. Mostra contagens separadas dos pools orgânico e
  sourcing, com cor dinâmica por estado (saturated/almost/normal).
  
  Inclui popover com:
  - Detalhamento por pool (orgânico e sourcing)
  - Recomendação do sistema
  - Contagem de candidatos na fila
  - Botão de desbloqueio (+N)
  - Botão de desbloqueio temporário (Nh)
  - Link "Ver Configurações" → navega para /configuracoes
  
  Design System v4.2.1:
  - rounded-md em todos os elementos
  - Open Sans como tipografia principal
  - Cores: gray-900 (botões), #60BED1 (apenas LIA icon), sem shadows
  - Dark mode support com dark: variants

Historia de Usuario: |
  Como recrutador, eu quero ver rapidamente o estado de saturação de
  cada vaga no Kanban, com opções para desbloquear quando necessário.

Regras de Negocio:
  1. Badge não aparece enquanto dados estão carregando (loading state)
  2. Estados visuais:
     - saturated (🔴): organic.is_saturated || sourcing.is_saturated
     - almost (🟡): organic.percentage >= 90 || sourcing.percentage >= 90
     - normal (🟢): default
  3. Durante bypass ativo: estado = "normal" mesmo se contagem > threshold
  4. Valores de incremento e horas vêm da API (dinâmicos, não hardcoded)
  5. Após ação de unlock: refetch automático dos dados
  6. Toast de sucesso/erro após ações de desbloqueio
  7. Link "Ver Configurações" usa router.push('/configuracoes')

Requisitos Tecnicos:
  Frontend:
    - Props: { jobId: string }
    - Interface SaturationStatus com todos os campos da API
    - Estados: data, loading, actionLoading
    - Polling: fetchStatus via useCallback + useEffect
    - Popover: @radix-ui/react-popover (via @/components/ui/popover)
    - Ícones: lucide-react (AlertTriangle, TrendingUp, Lightbulb, Clock,
        Users, Globe, Search, Settings)
    - Navegação: useRouter de next/navigation
    - Toast: sonner (toast.success / toast.error)
    - getSaturationState(data): calcula estado visual
    - formatLastScreened(dateStr): "Último triado hoje/há N dias"
    - getRecommendationText(rec): texto amigável
    - handleUnlock(): POST unlock-pipeline com action="increase_threshold"
    - handleTemporaryUnlock(): POST unlock-pipeline com action="disable_temporarily"
  
  Layout do Popover:
    ┌──────────────────────────────────────┐
    │ Saturação do Pipeline               │
    ├──────────────────────────────────────┤
    │ Pool Orgânico: 42/20 (🔴 210%)     │
    │ Pool Sourcing: 0/20 (🟢 0%)        │
    ├──────────────────────────────────────┤
    │ Na fila: 5 candidatos               │
    │ Último triado: há 2 dias            │
    ├──────────────────────────────────────┤
    │ Recomendação: "Agendar entrevistas  │
    │ antes de desbloquear"               │
    ├──────────────────────────────────────┤
    │ [+10 Vagas] [Desbloquear 24h]       │
    │ Ver Configurações →                 │
    └──────────────────────────────────────┘

DoD:
  - [x] Badge renderiza com estado correto (saturated/almost/normal)
  - [x] Popover mostra pools orgânico e sourcing separados
  - [x] Botão "+N" chama unlock-pipeline e refetch após sucesso
  - [x] Botão "Desbloquear Nh" chama unlock-pipeline temporário
  - [x] Link "Ver Configurações" navega corretamente
  - [x] Toast de feedback após ações
  - [x] Dark mode funcional
  - [ ] Responsive (mobile-friendly)

Criterios de Aceitacao:
  - [x] Vaga com 42 orgânicos / threshold 20 → badge vermelho "42/20"
  - [x] Vaga com 18 orgânicos / threshold 20 → badge amarelo "18/20"
  - [x] Vaga com 5 orgânicos / threshold 20 → badge verde "5/20"
  - [x] Click no badge abre popover com detalhes dos 2 pools
  - [x] Botão "+10" incrementa threshold e mostra toast "Thresholds updated"
  - [x] Valores de +N e Nh vêm dinâmicos da API (unlock_increment, unlock_hours)

Como Testar:
  1. Abrir Kanban de vaga com candidatos
  2. Verificar badge de saturação no header
  3. Clicar no badge → popover abre com detalhes
  4. Clicar "+10 Vagas" → threshold incrementa, badge atualiza
  5. Verificar dark mode (alternar tema)

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/kanban/components/SaturationBadge.tsx (267L)
  - integração: plataforma-lia/src/components/pages/job-kanban-page.tsx (usa <SaturationBadge jobId={...} />)
  - proxy: plataforma-lia/src/app/api/backend-proxy/job-vacancies/[jobId]/saturation-status/route.ts

Arquivos Adicionais no Replit (Código Existente):
  - component: plataforma-lia/src/components/kanban/components/SaturationBadge.tsx
  - kanban: plataforma-lia/src/components/kanban/components/KanbanColumn.tsx (integração)
  - proxy: plataforma-lia/src/app/api/backend-proxy/job-vacancies/[jobId]/saturation-status/route.ts
  - hook: plataforma-lia/src/components/kanban/hooks/useSaturationStatus.ts
```


---

### SAT-003: Configuração Global de Saturação (Settings UI)

```yaml
Titulo: "[Saturação] Seção de Configuração no Card Triagem (Settings → Pipeline)"
Tipo: Feature
Area: Frontend + Backend
Sprint: S1
Pontos: 5
Prioridade: Alta
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend + Backend)
Fase: MVP Alpha 1
Tags: [frontend, settings, configuração, saturação, design-system]
Dependências: SAT-001

Descricao: |
  Adicionar seção "Controle de Saturação" no card "Triagem" da página
  de Configurações → Pipeline de Recrutamento. A seção contém 4 campos
  numéricos editáveis que controlam os defaults globais da empresa:
  1. Limite Inscrições Orgânicas (web/whatsapp): default 20
  2. Limite Busca Ativa (sourcing): default 20
  3. Incremento de Desbloqueio: default +10
  4. Horas de Desbloqueio Temporário: default 24h
  
  Os valores são salvos via PUT /api/v1/settings/saturation e carregados
  via GET /api/v1/settings/saturation. Cada campo usa input type="number"
  com validação de range (1-500 para thresholds, 1-100 para increment,
  1-168 para hours).
  
  O card Triagem já existe em StageCard.tsx — a seção de saturação é
  uma sub-seção colapsável com ícone de Gauge.

Historia de Usuario: |
  Como recrutador ou admin, eu quero configurar os limites de saturação
  globais da empresa, para que todas as novas vagas herdem esses valores.

Regras de Negocio:
  1. Valores alterados afetam APENAS vagas futuras (não retroativo)
  2. Vagas existentes mantêm seus overrides em governance_rules
  3. Validação client-side: min 1, max varia por campo
  4. Validação server-side: Pydantic com Field(ge=1, le=500)
  5. Exibir toast de sucesso/erro após salvar
  6. Loading state durante fetch e save

Requisitos Tecnicos:
  Frontend:
    - Localização: dentro do StageCard.tsx, na seção do card "Triagem"
    - Sub-seção colapsável: ChevronDown/ChevronRight toggle
    - Ícone: Gauge (lucide-react) ao lado do título "Controle de Saturação"
    - 4 campos Input type="number" com labels descritivos
    - Fetch: GET /api/backend-proxy/settings/saturation/ ao abrir seção
    - Save: PUT /api/backend-proxy/settings/saturation/ ao alterar valor
    - Toast: sonner para feedback
    - Design: bg-gray-50 dark:bg-gray-900 para seção diferenciada
  
  Backend:
    - Já implementado em SAT-001 (endpoints GET/PUT /settings/saturation)

DoD:
  - [x] Seção "Controle de Saturação" visível no card Triagem
  - [x] 4 campos editáveis com valores carregados da API
  - [x] Alterações salvam automaticamente ou com botão "Salvar"
  - [x] Validação de range no frontend e backend
  - [x] Toast de feedback
  - [x] Dark mode funcional

Criterios de Aceitacao:
  - [x] Abrir Configurações → Pipeline → Triagem → ver 4 campos de saturação
  - [x] Alterar "Limite Orgânico" para 30 → salva → recarregar → valor 30
  - [x] Inserir valor 0 → validação impede (mínimo 1)
  - [x] Inserir valor 600 → validação impede (máximo 500)

Como Testar:
  1. Navegar para /configuracoes
  2. Encontrar card "Triagem" no pipeline
  3. Expandir seção "Controle de Saturação"
  4. Alterar valores e verificar persistência
  5. Verificar que vaga existente não é afetada

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/settings/StageCard.tsx (855L — seção de saturação dentro)
  - proxy: plataforma-lia/src/app/api/backend-proxy/settings/saturation/route.ts

Arquivos Adicionais no Replit (Código Existente):
  - proxy: plataforma-lia/src/app/api/backend-proxy/settings/saturation/route.ts
  - page: plataforma-lia/src/app/admin/configuracoes/page.tsx (seção saturação)
  - backend: lia-agent-system/app/api/v1/saturation.py (PUT /settings/saturation)
```


---

### SAT-004: Badges de Origem nos Cards do Kanban

```yaml
Titulo: "[Saturação] Badges de Origem — Web, WhatsApp, Busca, ATS, Aguardando"
Tipo: Feature
Area: Frontend
Sprint: S1
Pontos: 3
Prioridade: Média
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, kanban, componente, ux]
Dependências: SAT-001

Descricao: |
  Cada card de candidato no Kanban exibe um badge colorido indicando
  a origem/canal de entrada do candidato:
  - 🔵 "Web" (azul) — origin = "web"
  - 🟢 "WhatsApp" (verde) — origin = "whatsapp"
  - ⚫ "Busca" (cinza) — origin = "sourcing"
  - 🟣 "ATS" (roxo) — origin = "ats"
  - 🟡 "Aguardando" (âmbar) — status = "awaiting_screening"
  
  O badge de "Aguardando" tem prioridade sobre o badge de origem
  quando o candidato está na fila de espera.

Historia de Usuario: |
  Como recrutador, eu quero ver de onde cada candidato veio, para
  entender a composição do pipeline e a eficácia de cada canal.

Requisitos Tecnicos:
  Frontend:
    - Componente OriginBadge com prop origin: string e status: string
    - Renderiza dentro do card de candidato no Kanban
    - Cores por origin: web→blue, whatsapp→green, sourcing→gray,
      ats→purple, awaiting→amber
    - Badge pequeno: text-[10px], px-1.5, py-0.5, rounded-full
    - Campo origin vem do backend em VacancyCandidate.origin

DoD:
  - [x] Badge renderiza para todas as 5 origens
  - [x] Cores corretas por tipo
  - [x] "Aguardando" tem prioridade sobre origem
  - [x] Dark mode funcional

Criterios de Aceitacao:
  - [x] Candidato com origin="web" mostra badge azul "Web"
  - [x] Candidato na fila mostra badge âmbar "Aguardando" (não "Web")
  - [x] Badge é pequeno e não interfere no layout do card

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/kanban/components/index.ts (exporta badges)
  - integração: plataforma-lia/src/components/pages/job-kanban-page.tsx
```


---

### SAT-005: Fila de Espera com Retomada Automática

```yaml
Titulo: "[Saturação] Fila de Espera — Status awaiting_screening + Promoção Automática"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 8
Prioridade: Crítica
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, automação, fila, comunicação, saturação]
Dependências: SAT-001, COM-001

Descricao: |
  Sistema de fila de espera para candidatos que chegam quando o pool
  está saturado. Candidatos recebem status "awaiting_screening" e são
  promovidos automaticamente quando slots abrem.
  
  A função process_screening_queue() é o motor de promoção:
  1. Busca candidatos com status "awaiting_screening" na vaga
  2. Ordena por: lia_score DESC NULLS LAST, created_at ASC
     (prioriza melhor score, desempate por antiguidade)
  3. Para cada candidato (até max_promote):
     a. Muda status → screening
     b. Tenta enviar convite WhatsApp (se há conversa existente)
     c. Se não há WhatsApp: envia convite multicanal via CommunicationDispatcher
     d. Grava metadata: promoted_from_queue_at, invite_channel, invite_sent
  4. Commit e retorna lista de promovidos
  
  Triggers de promoção:
  - unlock-pipeline (increase_threshold ou disable_temporarily)
  - Candidato sai do pool (rejeitado, desistiu, withdrawn)
  - Chamada manual via POST /process-queue

Historia de Usuario: |
  Como candidato, eu quero ser automaticamente convidado para triagem
  quando uma vaga abrir, sem precisar verificar manualmente.

Regras de Negocio:
  1. Prioridade da fila: score > data de inscrição
  2. Convite tenta WhatsApp primeiro (se há conversa prévia)
  3. Fallback para email + WhatsApp via dispatcher
  4. Candidato promovido recebe link de triagem
  5. metadata.promoted_from_queue_at registra momento da promoção
  6. max_promote tem range 1-50 (default 1)

Requisitos Tecnicos:
  Backend:
    - Função: process_screening_queue(db, vacancy_id, company_id, max_promote)
    - Localização: automation_handlers.py (linha ~919)
    - Queries: SELECT vacancy_candidates WHERE status='awaiting_screening'
      ORDER BY lia_score DESC NULLS LAST, created_at ASC LIMIT max_promote
    - Para cada candidato:
      - SELECT candidate WHERE id = vc.candidate_id (dados de contato)
      - Tenta WhatsApp via WhatsAppConversation (se exists e active)
      - Fallback: Email via candidate_feedback_service.send_gate_feedback("screening_invited")
    - Mensagem WhatsApp: "Olá, {nome}! 👋\n\nTemos uma ótima notícia!
      Agora há uma vaga disponível para continuar o processo de triagem
      para *{job_title}*.\n\nVamos continuar? Responda *SIM*! 🚀"
    - Email subject: "[WeDOTalent] Convite para triagem — {vacancy_title}"
    - Email body: Template canônico via _GATE_BODIES["screening_invited"]
    - screening_link: "/triagem/{screening_invite_token}" (token do additional_data)
    - job_title e company_name carregados ANTES das branches de canal (evita NameError)
    - Token de triagem: consumido do additional_data.screening_invite_token;
      se ausente (candidato legado), gera novo via secrets.token_urlsafe(32)

  ⚠️ Bugs corrigidos na implementação:
    - job_title era definido apenas dentro do bloco WhatsApp, causando NameError
      para candidatos sem WhatsApp (corrigido: carregamento movido para antes das branches)
    - CommunicationDispatcher substituído por send_gate_feedback canônico (consistência)

DoD:
  - [x] process_screening_queue funcional com ordenação correta
  - [x] Convite WhatsApp enviado se conversa existente
  - [x] Fallback para email via send_gate_feedback (não CommunicationDispatcher)
  - [x] metadata registrada (promoted_from_queue_at, invite_channel)
  - [x] Chamada automática após unlock-pipeline
  - [x] Endpoint manual POST /process-queue funcional
  - [ ] Testes unitários para a função

Criterios de Aceitacao:
  - [x] 5 candidatos na fila → unlock +10 → 5 candidatos promovidos
  - [x] Candidato com maior score é promovido primeiro
  - [x] Candidato recebe convite com link /triagem/{token}
  - [x] metadata mostra promoted_from_queue_at correto

Como Testar:
  1. Criar vaga saturada (20 orgânicos, threshold 20)
  2. Adicionar 5 candidatos → status "awaiting_screening"
  3. POST /unlock-pipeline { action: "increase_threshold", new_threshold: 30 }
  4. Verificar que 5 candidatos foram promovidos (status → screening)
  5. Verificar logs de envio de convite

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Orquestra promoção da fila como tarefa automatizada
    - CommunicationReActAgent (domain=communication): Pode ser acionado para personalizar convites
  Tools Utilizadas:
    - schedule_secondary_task: Agenda promoção como task secundária após unlock
    - send_communication: Envia convite multicanal (WhatsApp/email)
  Servicos IA:
    - candidate_feedback_service.send_gate_feedback("screening_invited"):
      Gera email de convite com template canônico _GATE_BODIES["screening_invited"]
    - LIAScoreService: lia_score é usado para priorizar fila (ORDER BY lia_score DESC)
  Modelo LLM: Nenhum direto — ordenação e promoção são determinísticas
  Governanca e Compliance:
    - PolicyEngine: Regra "communication_hours" (08h-20h) limita horário de envio de convites
    - PII Masking: PIIMaskingFilter redige email/telefone nos logs de envio (LGPD Art. 46)
    - Audit Trail: promoted_from_queue_at + invite_channel registrados em additional_data (SOX/ISO 27001)
    - ConsentChecker: Soft enforcement — se consent ausente, loga warning mas prossegue;
      se consent revogado, bloqueia envio (HTTP 451)
  Fairness e Bias:
    - Priorização por lia_score + created_at (FIFO como desempate) — sem critérios demográficos
    - BiasAuditService: Recomendado gerar snapshot de distribuição demográfica dos promovidos
    - FairnessGuard: Não se aplica diretamente (sem query de busca de candidatos)
  Automacoes/Triggers:
    - Trigger 1: unlock-pipeline (POST /unlock-pipeline) → chama process_screening_queue
    - Trigger 2: Candidato sai do pool ativo (rejected/withdrawn) → reavalia saturação
    - Trigger 3: POST /process-queue (chamada manual pelo recrutador)
    - AutomationScheduler: auto_complete_expired_screenings roda a cada hora
  Fallbacks:
    - WhatsApp falha → fallback para email via send_gate_feedback
    - Email falha → invite_sent=False registrado, candidato permanece na fila
    - Token ausente (candidato legado) → gera novo via secrets.token_urlsafe(32)

Arquivos de Referencia (Prototipo LIA):
  - função: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 919-1080)
  - endpoint: lia-agent-system/app/api/v1/saturation.py (linhas 396-420, POST /process-queue)
  - dispatcher: lia-agent-system/app/domains/communication/services/communication_dispatcher.py
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py (send_gate_feedback)
  - score: lia-agent-system/app/services/lia_score_service.py (LIAScoreService)
  - pii: lia-agent-system/app/shared/pii_masking.py (PIIMaskingFilter)
  - consent: lia-agent-system/app/services/consent_checker_service.py

Arquivos Adicionais no Replit (Código Existente):
  - handler: lia-agent-system/app/services/automation_handlers.py (process_screening_queue)
  - model-db: lia-agent-system/libs/models/lia_models/candidate.py (status=awaiting_screening)
  - endpoint: lia-agent-system/app/api/v1/saturation.py (screening-queue, process-queue)
```


---

### SAT-006: Override Manual do Recrutador

```yaml
Titulo: "[Saturação] Override Manual — Recrutador Aprova Candidato da Fila"
Tipo: Feature
Area: Backend + Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend + Frontend)
Fase: MVP Alpha 1
Tags: [backend, frontend, kanban, automação]
Dependências: SAT-005, COM-001

Descricao: |
  Permite ao recrutador aprovar manualmente um candidato da fila de
  espera (status "awaiting_screening"), ignorando a ordem da fila.
  
  Função handle_recruiter_override_approve():
  1. Valida que o candidato está em awaiting_screening
  2. Muda status → screening
  3. Envia convite multicanal (email + WhatsApp)
  4. Registra atividade "recruiter_override_approve"
  5. Grava recruiter_override_at no additional_data do VacancyCandidate

Historia de Usuario: |
  Como recrutador, eu quero poder priorizar um candidato específico
  da fila, para que perfis excepcionais não esperem na ordem normal.

Requisitos Tecnicos:
  Backend:
    - Função: handle_recruiter_override_approve(db, candidate_id, vacancy_id, company_id)
    - Localização: automation_handlers.py (linha ~1074)
    - Validação: vc.status == "awaiting_screening" (senão retorna error)
    - Promoção: Chama process_screening_queue(max_promote=1) internamente
    - Convite WhatsApp: se conversa ativa, envia mensagem direta
    - Convite Email: candidate_feedback_service.send_gate_feedback("screening_invited")
    - Link: /triagem/{screening_invite_token} (consome do additional_data ou gera novo)
    - Activity: activity_type="recruiter_override_approve"
  Frontend:
    - Botão "Aprovar" no card do candidato com status "awaiting_screening"
    - Confirmação antes de executar (modal simples)
    - Refetch do kanban após ação

DoD:
  - [x] Função override funcional
  - [x] Convite via send_gate_feedback canônico (email) ou WhatsApp direto
  - [x] Atividade registrada
  - [x] Botão no frontend com confirmação
  - [x] Badge muda de "Aguardando" para o normal

Criterios de Aceitacao:
  - [x] Candidato na fila → override → status muda para screening
  - [x] Candidato recebe convite por email (send_gate_feedback) ou WhatsApp
  - [x] Activity feed mostra "Override manual pelo recrutador"
  - [x] Candidato sem contato → erro amigável no toast (frontend)

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa override como decompose_task
    - KanbanReActAgent (domain=kanban): Atualiza visualização do pipeline após override
  Tools Utilizadas:
    - update_candidate_stage: Move candidato de awaiting_screening → screening
    - send_communication: Envia convite multicanal pós-override
  Servicos IA:
    - process_screening_queue(max_promote=1): Internamente chamado — mesmo motor de promoção
    - send_gate_feedback("screening_invited"): Email canônico de convite
  Modelo LLM: Nenhum — decisão é 100% do recrutador humano
  Governanca e Compliance:
    - Audit Trail: activity_type="recruiter_override_approve" registrado com user_id do recrutador
    - recruiter_override_at gravado em additional_data (rastreabilidade SOX)
    - PolicyEngine: override NÃO desrespeita "max_candidates_per_vacancy" (500) — apenas pula fila
    - PII Masking: Email do candidato mascarado nos logs
  Fairness e Bias:
    - Override manual é decisão humana — FairnessGuard não bloqueia, mas BiasAuditService
      deve registrar overrides para análise posterior de padrões discriminatórios
    - Recomendação: Dashboard de overrides por recrutador + distribuição demográfica
  Fallbacks:
    - Candidato não está em awaiting_screening → retorna error (validação pré-override)
    - WhatsApp indisponível → fallback para email via send_gate_feedback
    - Email falha → registra invite_sent=False, candidato já foi promovido (status=screening)

Arquivos de Referencia (Prototipo LIA):
  - função: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 1074-1250)
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py
  - pii: lia-agent-system/app/shared/pii_masking.py
```


---

### SAT-007: Máquina de Estados Gate 1 — Inscrição Web → Triagem

```yaml
Titulo: "[Saturação] Gate 1 — Máquina de Estados da Inscrição Web até Triagem WSI"
Tipo: Technical Debt / Fix
Area: Backend
Sprint: S1
Pontos: 5
Prioridade: Crítica
Epic: É30
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)

Arquivos Adicionais no Replit (Código Existente):
  - endpoint: lia-agent-system/app/api/v1/saturation.py (verificação de saturação no apply)
  - spec: docs/saturacao-chatweb-comunicacao-cards-jira.md §4.3 (Gate 1 state machine)
```

**Contexto:**

Dois endpoints aceitam candidaturas web — ambos devem respeitar o mesmo
fluxo Gate 1 para evitar bypass da triagem WSI:

| Endpoint | Arquivo | Uso |
|----------|---------|-----|
| `POST /api/v1/applications/apply/{vacancy_id}` | `applications.py` | Formulário de candidatura (mobile/SPA) |
| `POST /api/v1/vacancies/{id}/apply-web` | `job_vacancies.py` | Formulário de inscrição web público |

**Máquina de estados Gate 1:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   INSCRIÇÃO WEB                                                     │
│   (qualquer endpoint)                                               │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────────┐     adherence < 50%    ┌────────────────────┐   │
│   │ Calcula Score │ ────────────────────── │ Feedback + Rejeição│   │
│   │ (LIA Score)   │                        │ (low_adherence)     │   │
│   └──────┬───────┘                        └────────────────────┘   │
│          │ adherence ≥ 50%                                          │
│          ▼                                                          │
│   ┌──────────────────┐                                              │
│   │ Verifica Saturação│                                             │
│   │ (threshold_web)   │                                             │
│   └──────┬───────────┘                                              │
│          │                                                          │
│    ┌─────┴──────┐                                                   │
│    │             │                                                   │
│    ▼ NÃO sat.   ▼ SATURADO                                         │
│ ┌──────────┐  ┌───────────────────┐                                 │
│ │ status=  │  │ status=           │                                 │
│ │ "applied"│  │ "awaiting_screen."│                                 │
│ │ stage=   │  │ stage=            │                                 │
│ │ "pending │  │ "pending_gate1"   │                                 │
│ │  _gate1" │  │                   │                                 │
│ └────┬─────┘  └────────┬──────────┘                                 │
│      │                 │                                            │
│      │ (promoção       │ Entra na FILA de espera                    │
│      │  imediata*)     │ (process_screening_queue)                  │
│      │                 │                                            │
│      │                 │  Quando abrir capacidade:                  │
│      │                 │  - Saturação natural (outro sai)           │
│      │                 │  - Recruiter override (SAT-006)            │
│      │                 │  - Aumentar limite (SaturationBadge)       │
│      │                 │  - Desbloqueio temporário (24h)            │
│      │                 │                                            │
│      ▼                 ▼                                            │
│   ┌────────────────────────┐                                        │
│   │ status = "screening"   │                                        │
│   │ stage  = "screening"   │                                        │
│   │ Convite enviado via:   │                                        │
│   │  - WhatsApp (se conv.  │                                        │
│   │    ativa existe)       │                                        │
│   │  - Email (send_gate_   │                                        │
│   │    feedback canônico)  │                                        │
│   └────────────┬───────────┘                                        │
│                │                                                    │
│                ▼                                                    │
│   ┌────────────────────────┐                                        │
│   │ Candidato acessa       │                                        │
│   │ /triagem/{token}       │                                        │
│   │ Inicia Chat WSI        │                                        │
│   └────────────────────────┘                                        │
│                                                                     │
│   (*) Candidatos em pipeline não-saturado recebem convite direto    │
│   via automação imediata, sem passar pela fila de espera.           │
│                                                                     │
│   DADOS GERADOS NA INSCRIÇÃO:                                      │
│   additional_data = {                                               │
│     "screening_invite_token": token_urlsafe(32),                   │
│     "applied_at": ISO timestamp,                                   │
│     "is_saturated_at_apply": bool                                  │
│   }                                                                 │
│                                                                     │
│   DADOS ADICIONADOS NA PROMOÇÃO:                                   │
│   additional_data += {                                              │
│     "promoted_from_queue_at": ISO timestamp,                       │
│     "invite_channel": "whatsapp" | "email",                       │
│     "invite_sent": bool                                            │
│   }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

**Token de triagem (`screening_invite_token`):**
- Gerado na inscrição via `secrets.token_urlsafe(32)` — 256 bits de entropia
- Salvo em `additional_data` do `VacancyCandidate`
- Consumido por `process_screening_queue` ao montar o link `/triagem/{token}`
- Se token ausente (candidatos legados), o sistema gera um novo no momento da promoção
- Link canônico: `/triagem/{screening_invite_token}` (não `/triagem/{vacancy_id}?candidate=...`)

**Email de convite — mecanismo canônico:**
- Função: `candidate_feedback_service.send_gate_feedback("screening_invited", ...)`
- Template: `_GATE_BODIES["screening_invited"]` em `candidate_feedback_service.py` L610
- Subject: `[WeDOTalent] Convite para triagem — {vacancy_title}`
- Inclui `screening_url` como variável interpolada

```yaml
Dependencias:
  - SAT-001 (modelo de dados com thresholds)
  - SAT-005 (fila de espera com process_screening_queue)
  - INS-001 (formulário de inscrição pública)

Tasks:
  - [x] Ambos endpoints usam stage="pending_gate1"
  - [x] Ambos endpoints geram screening_invite_token
  - [x] Ambos endpoints verificam saturação e definem status correto
  - [x] process_screening_queue consome token do additional_data
  - [x] Link de triagem usa formato /triagem/{token} (não IDs diretos)
  - [x] Email de convite usa send_gate_feedback canônico (não inline)
  - [x] Fallback: gera token se ausente em candidatos legados
  - [x] Log: PII mascarado nos logs de envio

Criterios de Aceitacao:
  - [x] Candidato via applications.py com pipeline saturado → status=awaiting_screening
  - [x] Candidato via job_vacancies.py com pipeline saturado → status=awaiting_screening
  - [x] Candidato promovido da fila → recebe email com link /triagem/{token}
  - [x] Token é o mesmo gerado na inscrição (não um novo)
  - [x] Candidato legado (sem token) → sistema gera novo token na promoção

Bugs Corrigidos (code review):
  1. Import errado em applications.py: `from app.models.company_profile` → `from app.models.company`
     (import inexistente fazia o fallback forçar is_saturated=True, enfileirando todos)
  2. NameError em process_screening_queue: job_title definido apenas no bloco WhatsApp,
     causando crash no branch de email para candidatos sem WhatsApp
     (corrigido: job_title + company_name carregados antes das branches de canal)
  3. Fallback de saturação inconsistente: applications.py defaultava is_saturated=True,
     job_vacancies.py defaultava False — ambos agora defaultam False (permite inscrição)

Inteligencia e Automacao:
  Agentes Envolvidos:
    - PipelineReActAgent (domain=pipeline): Gerencia transições de stage (pending_gate1 → screening)
    - AutomationReActAgent (domain=automation): Executa process_screening_queue como task agendada
    - CommunicationReActAgent (domain=communication): Dispara convites multicanal
  Tools Utilizadas:
    - update_candidate_stage: Transição pending_gate1 → screening
    - send_communication: Convite multicanal (WhatsApp + email)
    - add_candidate_to_vacancy: Associa candidato à vaga com stage/status corretos
  Servicos IA:
    - LIAScoreService: Calcula lia_score na inscrição (usado para priorização da fila)
      Formula: Ranking_Score = (Rubricas * W_rub + WSI * W_wsi + Prerequisites * W_pre
      + Recency * W_rec + Calibration) * Completeness_Factor
    - candidate_feedback_service.send_gate_feedback("screening_invited"): Email canônico
    - CVScoringService: Score de aderência do CV contra rubricas da vaga (threshold 50%)
  Modelo LLM:
    - Claude (Anthropic): Scoring de CV + aderência (structured output)
    - Nenhum no fluxo de saturação em si (determinístico)
  Governanca e Compliance:
    - ConsentChecker: Verificação de consentimento para ai_screening antes de processar
      Soft enforcement: consent ausente → warning + prossegue; revogado → HTTP 451
    - PII Masking: strip_pii_for_llm_prompt() antes de enviar CV ao LLM (LGPD Art. 12)
    - PII Masking: PIIMaskingFilter nos logs de envio de convite (LGPD Art. 46)
    - Audit Trail: additional_data registra todo o histórico de estados para SOX/ISO 27001:
      screening_invite_token, applied_at, is_saturated_at_apply, promoted_from_queue_at
    - PolicyEngine: max_candidates_per_vacancy (500) como teto absoluto
    - EscalationRules: Se candidato fica >7 dias em awaiting_screening → escalation automático
  Fairness e Bias:
    - FairnessGuard: Filtro ativo no scoring de CV — bloqueia critérios discriminatórios
      (gênero, raça, idade, religião, orientação sexual, deficiência)
    - BiasAuditService: Snapshot de distribuição Four-Fifths Rule para inscritos vs promovidos
    - Priorização da fila: lia_score + FIFO (created_at) — sem critérios demográficos
    - Dois endpoints idênticos: Mesmo comportamento evita disparidade por canal de entrada
  Automacoes/Triggers:
    - Inscrição web → score adherence → saturação check → status/stage automáticos
    - Promoção da fila: process_screening_queue → convite WhatsApp/email
    - Override manual: handle_recruiter_override_approve → promoção individual
    - AutomationScheduler: check_inactive_candidates (7 dias sem atividade)
  Fallbacks:
    - Saturação check falha → is_saturated=False (permite inscrição, não penaliza candidato)
    - Token ausente → gera novo na promoção (candidatos legados)
    - WhatsApp falha → email; email falha → invite_sent=False
    - LLM scoring falha → lia_score=NULL (candidato vai para fim da fila, FIFO decide)

Arquivos de Referencia (Prototipo LIA):
  - applications.py: lia-agent-system/app/api/v1/applications.py (linhas 261-310)
  - job_vacancies.py: lia-agent-system/app/api/v1/job_vacancies.py (linhas 3668-3740)
  - automation_handlers.py: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 919-1070)
  - candidate_feedback_service.py: lia-agent-system/app/services/candidate_feedback_service.py (linhas 598-730)
  - lia_score: lia-agent-system/app/services/lia_score_service.py
  - cv_scoring: lia-agent-system/app/services/cv_scoring_service.py
  - fairness: lia-agent-system/app/shared/compliance/fairness_guard.py
  - bias_audit: lia-agent-system/app/services/bias_audit_service.py
  - consent: lia-agent-system/app/services/consent_checker_service.py
  - pii: lia-agent-system/app/shared/pii_masking.py
  - policy: lia-agent-system/app/orchestrator/policy_engine.py
```


---

## 4. Cards Completos — É31 Chat Web de Triagem (TRI) — Épico [WT-1519](https://wedotalent.atlassian.net/browse/WT-1519)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md` §7
> **Épico:** É31 — Chat Web de Triagem (WSI + IA Conversacional)
> **Status Jira:** TRI-001→008 = WT-1528→WT-1537 (criados)

### TRI-001: Tipos e Interfaces TypeScript

```yaml
Titulo: "[Chat Web] Tipos e Interfaces TypeScript — types.ts Completo"
Tipo: Feature
Area: Frontend
Sprint: S1
Pontos: 3
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, typescript, tipos, triagem]
Dependências: Nenhuma

Descricao: |
  Arquivo de tipos TypeScript (~125L) que define todas as interfaces
  usadas pela feature de triagem:
  
  Types:
    TriagemStatus = "invited"|"started"|"in_progress"|"completed"|"expired"|"cancelled"
    TriagemMessageRole = "lia"|"candidate"
    TriagemMessageType = "text"|"multiple_choice"|"likert_scale"|"audio"|"system"
    TriagemPageState = "loading"|"error"|"welcome"|"chat"|"confirmation"|"completion"
  
  Interfaces:
    WSIProgress { currentBlock, totalBlocks, currentBlockName,
      questionsAnswered, totalQuestions, estimatedMinutesRemaining }
    TriagemSession { id, token, status, candidateId, candidateName,
      jobId, jobTitle, companyName, companyLogoUrl, progress,
      createdAt, expiresAt, startedAt, completedAt,
      wsiFinalScore, recommendation }
    TriagemMessage { id, sessionId, role, type, content,
      options, selectedOption, likertValue, likertLabels,
      timestamp, blockIndex, blockName, audioUrl }
    TriagemConfig { companyName, companyLogoUrl, jobTitle,
      candidateName, estimatedMinutes, privacyPolicyUrl,
      audioEnabled, feedbackEnabled, welcomeMessage, voiceMode }
    TriagemError { code, message }
    TriagemCompletionSummary { questionsAnswered, durationMinutes, nextSteps[] }
    SendMessagePayload { content, type, selectedOption?, likertValue?, voiceMode? }
    UseTriagemChatReturn { pageState, session, config, messages,
      progress, error, completionSummary, isLiaTyping, isSending,
      isLoadingHistory, initSession, startChat, sendMessage,
      completeSession, reviewSession, loadHistory }

DoD:
  - [x] Todos os types e interfaces definidos
  - [x] Exportados corretamente para uso em componentes
  - [x] Sem dependências externas (apenas tipos nativos)

Arquivos de Referencia (Prototipo LIA):
  - file: plataforma-lia/src/components/triagem/types.ts (125L — copiar diretamente)

Arquivos Adicionais no Replit (Código Existente):
  - types: plataforma-lia/src/hooks/use-triagem-chat.ts (interfaces TriagemMessage, SessionStatus)
  - model-db: lia-agent-system/libs/models/lia_models/triagem.py (TriagemSession, TriagemMessage)
```


---

### TRI-002: Hook useTriagemChat — Gerenciamento de Estado

```yaml
Titulo: "[Chat Web] Hook useTriagemChat — State Management + API Integration (~537L)"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 13
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, hook, react, api, state-management, triagem]
Dependências: TRI-001, TRI-005

Descricao: |
  Hook React (~537L) que gerencia todo o ciclo de vida de uma sessão
  de triagem. É o "cérebro" do frontend do chat web.
  
  Responsabilidades:
  1. Validar token e carregar sessão (initSession)
  2. Iniciar conversa com opção de voz (startChat)
  3. Enviar mensagens com debounce e retry (sendMessage)
  4. Gerenciar progresso WSI (progress)
  5. Completar sessão (completeSession)
  6. Persistir estado local via localStorage
  7. Converter áudio base64 em blob URLs
  8. Mapear responses do backend para tipos TypeScript
  
  Funcionalidades robustas:
  - fetchWithTimeout: 30s timeout com AbortController
  - fetchWithRetry: até 2 retries com backoff exponencial (1s, 2s)
  - Debounce de envio: 300ms para evitar double-send
  - mapBackendMessage: converte snake_case → camelCase
  - mapBackendSession: converte session data
  - mapBackendProgress: converte progress data
  - mapErrorResponse: HTTP status → error codes amigáveis
  - localStorage persistence: salva messages + pageState por token
  - mountedRef: evita setState em componente desmontado

Historia de Usuario: |
  Como desenvolvedor, eu quero um hook centralizado que gerencie toda
  a comunicação com o backend de triagem, para que os componentes
  de UI sejam puramente visuais.

Requisitos Tecnicos:
  Frontend:
    - Hook: useTriagemChat(token: string): UseTriagemChatReturn
    - Estados: pageState, session, config, messages, progress, error,
        completionSummary, isLiaTyping, isSending, isLoadingHistory
    - API calls:
      GET  /api/backend-proxy/triagem/{token} → initSession
      POST /api/backend-proxy/triagem/{token}/start → startChat
      POST /api/backend-proxy/triagem/{token}/message → sendMessage
      POST /api/backend-proxy/triagem/{token}/complete → completeSession
      GET  /api/backend-proxy/triagem/{token}/history → loadHistory
    - base64ToAudioUrl(): converte audio_base64 em object URL (blob)
    - Timeout: 30s (TIMEOUT_MS)
    - Retries: 2 (MAX_RETRIES)
    - Debounce: 300ms (DEBOUNCE_MS)
    - localStorage key: "triagem_state_{token}"
    - Cleanup: URL.revokeObjectURL para audio blobs
    - voiceMode propagation: sendMessage inclui { voiceMode: isVoiceMode }
      (estado runtime do UI, não config inicial do servidor)

DoD:
  - [x] Hook funcional com todos os métodos
  - [x] fetchWithTimeout e fetchWithRetry implementados
  - [x] Conversão base64 → audio URL funcional
  - [x] localStorage persistence funcional
  - [x] Mapeamento snake_case → camelCase completo
  - [x] Error handling com códigos amigáveis
  - [x] voiceMode propagado em sendMessage

Criterios de Aceitacao:
  - [x] Token inválido → pageState="error", error.code="TOKEN_INVALID"
  - [x] Token expirado → pageState="error", error.code="TOKEN_EXPIRED"
  - [x] Sessão já completada → pageState="completion"
  - [x] Sessão in_progress → pageState="chat", mensagens restauradas
  - [x] Sessão invited → pageState="welcome"
  - [x] Envio de mensagem com retry → até 3 tentativas
  - [x] Fechar e reabrir página → mensagens restauradas do localStorage

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — hook é consumidor de APIs REST, não orquestra agentes
    - Indiretamente consome respostas do PipelineReActAgent (via backend screening endpoints)
  Tools Utilizadas: Nenhuma — hook consome endpoints REST, não invoca tools de agentes
  Servicos IA Consumidos (via REST):
    - TriagemSessionService: process_message() retorna pergunta_lia + scoring parcial
    - Intent classification: Backend classifica intent (ANSWER/QUESTION/GREETING/UNCLEAR)
    - TTS: Quando voiceMode=true, backend retorna audio_base64 na resposta
  Modelo LLM: Nenhum no frontend — toda IA roda no backend
  Governanca e Compliance:
    - Token-based auth: Sessão identificada por screening_invite_token (sem password/login)
    - localStorage: Mensagens persistidas localmente — dados PII do candidato em client-side
      ⚠️ Candidato deve poder limpar dados (LGPD direito de esquecimento)
    - fetchWithTimeout (30s): Previne travamento se backend não responder
    - fetchWithRetry (2 retries, backoff exponencial): Resiliência sem sobrecarregar backend
  Fairness e Bias:
    - Hook é agnóstico — apenas renderiza perguntas e respostas do backend
    - Determinismo: Backend garante que mesmas respostas geram mesmo score
  Fallbacks:
    - Backend offline → error.code="NETWORK_ERROR", mensagem amigável ao candidato
    - Token inválido → pageState="error" com orientação ao candidato
    - Sessão expirada → pageState="error" com mensagem específica
    - Audio base64 inválido → degrada para texto-only (sem crash)

Arquivos de Referencia (Prototipo LIA):
  - hook: plataforma-lia/src/hooks/use-triagem-chat.ts (537L — copiar e adaptar)
  - proxy: plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts

Arquivos Adicionais no Replit (Código Existente):
  - hook: plataforma-lia/src/hooks/use-triagem-chat.ts (hook completo ~537L)
  - proxy: plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts
  - api: lia-agent-system/app/api/v1/triagem.py (6 endpoints REST)
  - service: lia-agent-system/app/services/triagem_session_service.py
```


---

### TRI-003: WelcomeCard — Tela de Boas-Vindas com Branding

```yaml
Titulo: "[Chat Web] WelcomeCard — Tela de Boas-Vindas com Branding da Empresa"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, triagem, design-system, branding]
Dependências: TRI-001

Descricao: |
  Componente React (~101L) que é a primeira tela que o candidato vê.
  Exibe branding da empresa CLIENTE (não WeDo), título da vaga,
  mensagem personalizada da LIA com nome do candidato, e botões
  para iniciar conversa em modo texto ou voz.
  
  ⚠️ REGRA CRÍTICA: O logo e nome SEMPRE são da empresa cliente
  (config.companyName, config.companyLogoUrl), NUNCA do WeDo Talent.
  O candidato NÃO sabe que está usando a plataforma WeDo.

  Design System v4.2.1:
  - Botão principal: bg-gray-900 (dark: bg-gray-50)
  - Botão secundário (voz): border border-gray-900, bg-transparent
  - LIA icon: bg-[#60BED1]/10 (único uso de cyan)
  - Mensagem da LIA: fundo bg-[#60BED1]/10 com rounded-md
  - Tipografia: Open Sans (font-['Open_Sans',sans-serif])
  - Todos os cantos: rounded-md
  - Max width: max-w-md (448px)

Requisitos Tecnicos:
  Frontend:
    - Props: { config: TriagemConfig, onStart: (voiceMode?: boolean) => void,
        isStarting?: boolean, className?: string }
    - Seções:
      1. Logo/nome empresa (img ou fallback texto)
      2. Título da vaga (h1)
      3. Mensagem LIA com ícone (bg-[#60BED1]/10)
      4. Tempo estimado (Clock icon + config.estimatedMinutes)
      5. Botão "Iniciar Conversa" → onStart(false)
      6. Botão "Iniciar Conversa por Voz" → onStart(true)
         (só aparece se config.voiceMode === true)
      7. Link "Política de Privacidade" (Shield icon)
    - Acessibilidade: aria-label em todos os botões e link

DoD:
  - [x] Logo da empresa renderiza (img ou fallback texto)
  - [x] Nome do candidato personalizado na mensagem
  - [x] Botão de voz condicional (só se voiceMode=true)
  - [x] isStarting state desabilita botões e mostra "Iniciando..."
  - [x] Dark mode funcional
  - [ ] Acessibilidade completa (aria-labels)

Criterios de Aceitacao:
  - [x] Logo "TechCorp" aparece (não "WeDo Talent")
  - [x] "Olá, Maria! Eu sou a LIA 👋" com nome do candidato
  - [x] Botão voz aparece se config.voiceMode=true
  - [x] Botão voz NÃO aparece se config.voiceMode=false
  - [x] Click em "Iniciar Conversa" chama onStart(false)
  - [x] Click em "Iniciar Conversa por Voz" chama onStart(true)

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/triagem/WelcomeCard.tsx (101L)
  - lia-icon: plataforma-lia/src/components/ui/lia-icon.tsx

Arquivos Adicionais no Replit (Código Existente):
  - component: plataforma-lia/src/components/triagem/WelcomeCard.tsx
```


---

### TRI-004: MessageBubble — Bolha de Mensagem com Áudio

```yaml
Titulo: "[Chat Web] MessageBubble — Bolha de Mensagem com AudioPlayer e Animação"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, triagem, áudio, design-system]
Dependências: TRI-001, VOZ-002

Descricao: |
  Componente React (~117L) que renderiza uma mensagem no chat.
  Layout diferenciado por role:
  - LIA (role="lia"): justify-start, bg-white border, LIAIcon à esquerda
  - Candidato (role="candidate"): justify-end, bg-gray-900, initials à direita
  
  Suporta áudio: se message.audioUrl presente, renderiza AudioPlayer
  abaixo do texto. Quando áudio está tocando, LIAIcon exibe animação
  de "speaking" (pulsação).
  
  Suporta markdown simples: **bold**, *italic*, \n → <br>
  (com sanitização XSS: escapeHtml antes de parsing)

Requisitos Tecnicos:
  Frontend:
    - Props: { message: TriagemMessage, candidateName?: string,
        className?: string, autoPlayAudio?: boolean }
    - Layout LIA: LIAIcon(size="sm", speaking={isAudioPlaying}) + bubble
    - Layout Candidato: bubble + initials circle (getInitials(name))
    - AudioPlayer: renderiza se role=lia && message.audioUrl
    - parseSimpleMarkdown(): escapeHtml() → **bold** → *italic* → \n
    - Timestamp: formatTimestamp(iso) → "14:30" (pt-BR)
    - Animação: animate-in fade-in slide-in-from-bottom-2 duration-300

DoD:
  - [x] Bolha de LIA renderiza com LIAIcon
  - [x] Bolha de candidato renderiza com initials
  - [x] AudioPlayer renderiza quando audioUrl presente
  - [x] LIAIcon pulsa durante reprodução de áudio
  - [x] Markdown simples funcional
  - [x] XSS prevention (escapeHtml)
  - [x] Dark mode funcional

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/triagem/MessageBubble.tsx (117L)
  - audio-player: plataforma-lia/src/components/ui/audio-player.tsx
  - lia-icon: plataforma-lia/src/components/ui/lia-icon.tsx

Arquivos Adicionais no Replit (Código Existente):
  - component: plataforma-lia/src/components/triagem/MessageBubble.tsx
  - audio: plataforma-lia/src/components/ui/audio-player.tsx
```


---

### TRI-005: Backend — TriagemSessionService (Motor de IA)

```yaml
Titulo: "[Chat Web] TriagemSessionService — Motor de IA Conversacional + WSI Scoring (~887L)"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 21
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, ia, llm, scoring, triagem, wsi, voz]
Dependências: COM-001

Descricao: |
  Serviço Python (~887L) que é o motor de IA da triagem WSI via chat.
  Gerencia sessões, processa mensagens, gera perguntas contextuais,
  classifica intents, calcula scores determinísticos e integra TTS.
  
  Arquitetura de funções (16 funções/métodos):
  
  UTILITÁRIOS LLM:
    _generate_tts_audio(text) → Optional[str] (base64 audio)
      - Provider: OpenAI tts-1, voice "nova"
      - Formato: mp3, converte bytes → base64
      - Fallback: None se OpenAI não disponível
    
    _call_llm(prompt) → Optional[str]
      - Tenta Anthropic Claude Sonnet primeiro
      - Fallback Google Gemini
      - Fallback OpenAI GPT-4
      - Retorna None se todos falham
    
    _classify_intent(message, block_name, current_question) → str
      - Classifica: "ANSWER" | "QUESTION" | "GREETING"
      - Usa _call_llm com prompt específico
      - Default: "ANSWER" se LLM falha
    
    _generate_off_script_response(question, job_context) → str
      - Gera resposta para perguntas do candidato
      - Usa contexto da vaga/empresa
      - Retoma roteiro naturalmente
    
    _generate_contextual_question(block_name, previous_response, job_title, previous_questions) → str
      - Gera próxima pergunta CONTEXTUAL baseada na resposta anterior
      - Evita perguntas já feitas (previous_questions)
      - Adapta para o bloco WSI atual
  
  SCORING:
    _score_response_deterministic(response_text, block_type, competency) → Dict
      - Score baseado em keywords e indicadores de profundidade
      - Bloom taxonomy: 6 níveis (1-6 pts)
      - Dreyfus model: 5 níveis (1-5 pts)
      - ⚠️ NÃO usa random.uniform — 100% determinístico
      - Retorna: { score, bloom_level, dreyfus_level, indicators_found }
    
    _calculate_final_score(response_scores) → Tuple[float, str]
      - Pesos: Competências Técnicas e Resolução de Problemas = 2x
      - Score final: média ponderada normalizada para 0-10
      - Recommendation: ≥7.5 "approved", 5.0-7.4 "pending", <5.0 "rejected"
  
  CLASSE TriagemSessionService:
    validate_token(db, token) → Dict
      - Busca TriagemSession pelo token
      - Retorna status, metadados
    
    get_session_config(db, token) → Optional[Dict]
      - Retorna: session + config { companyName, companyLogoUrl, jobTitle,
        candidateName, estimatedMinutes, privacyPolicyUrl, audioEnabled,
        feedbackEnabled, welcomeMessage, voiceMode }
      - Config monta: branding da empresa cliente (nunca WeDo)
    
    create_session(db, token, ..., voice_mode) → Dict
      - Cria TriagemSession com dados do candidato e vaga
    
    start_session(db, token, voice_mode?) → Dict
      - Muda status → in_progress
      - Se voice_mode passado: grava session.voice_mode
      - Gera primeira mensagem (transição para bloco 1)
      - Se voice_mode: gera áudio TTS
      - Retorna { session, lia_message, progress }
    
    process_message(db, token, content, type, voice_mode?) → Dict
      - Resolve voice_mode: parâmetro > session.voice_mode
      - Classifica intent (_classify_intent)
      - Se ANSWER: score + próxima pergunta contextual
      - Se QUESTION: off-script response + retomada
      - Se voice_mode: gera TTS áudio
      - Retorna { lia_message, progress, audio_base64? }
    
    _generate_lia_response(db, session, content, type) → Dict
      - Lógica principal de geração de resposta
      - Gerencia transição entre blocos WSI
      - Acumula scores por bloco
      - Detecta completude do bloco
    
    _pre_completion_response(session, total_questions) → Dict
      - Mensagem antes de completar a triagem
    
    get_history(db, token) → Dict
      - Retorna todas as mensagens da sessão
    
    complete_session(db, token) → Dict
      - Calcula score final via _calculate_final_score
      - Grava wsi_final_score e recommendation na sessão
      - Chama _trigger_post_completion
    
    _trigger_post_completion(db, session) → Dict
      - Email de confirmação via CommunicationDispatcher
      - Notificação ao recrutador
      - Auto-move pipeline (score ≥ 7.5 → Entrevista)
      - Audit log

Historia de Usuario: |
  Como candidato, eu quero ter uma conversa natural com a LIA durante
  a triagem, onde ela me faz perguntas relevantes baseadas nas minhas
  respostas anteriores, não perguntas genéricas.

Regras de Negocio:
  1. Perguntas são geradas pelo LLM com base na resposta anterior
  2. Score é determinístico (Bloom/Dreyfus, sem randomização)
  3. Off-script: candidato pode fazer até 3 perguntas antes de retomada forçada
  4. Auto-move: score ≥ 7.5 → candidato avança para "Entrevista"
  5. Score < 7.5: cria sugestão para recrutador (não auto-rejeita)
  6. Branding: config SEMPRE mostra empresa cliente, não WeDo
  7. TTS: somente quando voiceMode=True (via OpenAI tts-1)
  8. LLM cascade: Anthropic → Gemini → OpenAI (3 fallbacks)
  9. Email de confirmação enviado via CommunicationDispatcher (real, não mock)

Requisitos Tecnicos:
  Backend:
    - Arquivo: triagem_session_service.py (~887L)
    - Dependências: openai (TTS), anthropic/gemini/openai (LLM)
    - Modelo: TriagemSession (SQLAlchemy)
    - Dispatcher: CommunicationDispatcher (pós-conclusão)
  
  Endpoints REST (via triagem router):
    GET    /api/v1/triagem/{token}           → validate + get_session_config
    POST   /api/v1/triagem/{token}/start     → start_session
    POST   /api/v1/triagem/{token}/message   → process_message
    POST   /api/v1/triagem/{token}/complete  → complete_session
    GET    /api/v1/triagem/{token}/history   → get_history
  
  Variáveis de Ambiente:
    ANTHROPIC_API_KEY — LLM primário (Claude Sonnet)
    GOOGLE_API_KEY — LLM fallback (Gemini)
    OPENAI_API_KEY — LLM fallback + TTS (tts-1)

DoD:
  - [x] TriagemSessionService com todos os 16 métodos
  - [x] Score determinístico via Bloom/Dreyfus (sem random)
  - [x] Intent classification (ANSWER/QUESTION/GREETING)
  - [x] Off-script handling com limite de 3 desvios
  - [x] TTS integration (OpenAI tts-1)
  - [x] LLM cascade (3 providers)
  - [x] Pós-conclusão: email real via dispatcher
  - [x] Auto-move pipeline (score ≥ 7.5)
  - [x] 5 endpoints REST funcionais
  - [ ] Testes unitários para scoring determinístico
  - [ ] Testes de integração para fluxo completo

Criterios de Aceitacao:
  - [x] Candidato responde → LIA faz pergunta contextual (não repetida)
  - [x] Candidato pergunta "qual o salário?" → LIA responde e retoma
  - [x] Mesma resposta → mesmo score (determinístico)
  - [x] Score 8.0 → candidato auto-move para Entrevista
  - [x] Score 6.5 → sugestão criada para recrutador
  - [x] voiceMode=true → resposta inclui audio_base64
  - [x] Após completar → email de confirmação enviado

Como Testar:
  1. Criar sessão: POST /triagem com token
  2. Start: POST /triagem/{token}/start { voice_mode: false }
  3. Enviar resposta: POST /triagem/{token}/message { content: "..." }
  4. Verificar que próxima pergunta é contextual
  5. Enviar pergunta: { content: "Qual o salário?" } → LIA responde
  6. Completar 7 blocos → verificar score final e email

Inteligencia e Automacao:
  Agentes Envolvidos:
    - PipelineReActAgent (domain=pipeline): Pode disparar run_wsi_screening via tool
    - AutomationReActAgent (domain=automation): Pós-conclusão, executa handle_screening_completed
    - CommunicationReActAgent (domain=communication): Despacha feedback/confirmação ao candidato
  Tools Utilizadas:
    - run_wsi_screening: Inicia sessão de triagem WSI para candidato (tool do PipelineReActAgent)
    - wsi_screening: Alias alternativo — mesma funcionalidade
    - get_candidate_wsi_scores: Consulta scores WSI de candidato já avaliado
    - send_feedback: Envia resultado de triagem ao candidato
    - update_candidate_stage: Auto-move para "Entrevista" se score ≥ 7.5
  Servicos IA:
    - TriagemSessionService.process_message():
      1. Classifica intent do candidato (ANSWER/QUESTION/GREETING/UNCLEAR)
      2. Se ANSWER: avalia resposta com rubrica WSI (Bloom/Dreyfus/Big5/CBI)
      3. Se QUESTION (off-script): gera resposta + retoma script
      4. Gera próxima pergunta contextual baseada em respostas anteriores
      5. Calcula score parcial a cada bloco (7 blocos total)
    - WSIService: Orquestra análise de JD, sugere competências, gera perguntas WSI
    - WSIDeterministicScorer: Scoring rule-based como baseline/validação do LLM scoring
    - WSIInterviewGraph (LangGraph): State machine para entrevistas síncronas — garante
      transições determinísticas e auditabilidade (compliance-ready)
    - LIAScoreService: Score unificado pós-triagem (fórmula Rubricas+WSI+Prerequisites+Recency)
    - CVScoringService: Score de CV contra rubricas da vaga (complementa WSI)
    - _generate_tts_audio(): OpenAI tts-1 para voz (se voiceMode=true)
  Modelos LLM:
    - Primário: Claude (Anthropic) — avaliação estruturada de respostas WSI, scoring
    - Secundário: Gemini (Google) — geração conversacional, intent classification, fallback
    - Terciário: OpenAI (gpt-4o) — fallback final para LLM tasks
    - TTS: OpenAI tts-1 (voice "nova") — geração de áudio em PT-BR
    - Cascade: Anthropic → Gemini → OpenAI (3 fallbacks automáticos)
  Governanca e Compliance:
    - ConsentChecker: Verificação de consentimento para ai_screening antes de iniciar sessão
      Soft enforcement: ausente → warning; revogado → HTTP 451 + bloqueia triagem
    - PII Masking: strip_pii_for_llm_prompt() em TODA resposta do candidato antes do LLM
      Remove: CPF, email, telefone, ano de formação, idade explícita, fragmentos de endereço
      Base legal: LGPD Art. 12 (dados anonimizados para processamento por terceiros)
    - PII Masking: PIIMaskingFilter nos logs de triagem (nome, email mascarados)
    - Audit Trail: TriagemSession model registra todas as interações para rastreabilidade
      Campos: messages_history (JSON), scores_by_block, final_score, completed_at
    - EU AI Act: Sistema classificado como HIGH-RISK (triagem automatizada de candidatos)
      Requer: explicabilidade do score, human-in-the-loop (recrutador revisa), audit trail
    - ModelDriftService: Monitora degradação dos modelos de scoring ao longo do tempo
  Fairness e Bias:
    - FairnessGuard: 3 camadas ativas durante toda triagem:
      1. Explicit Bias Detection (regex): Bloqueia critérios discriminatórios nas rubricas
      2. Implicit Bias Detection: Identifica termos problemáticos ("boa aparência", etc)
      3. Semantic Analysis (LLM): Detecta viés sutil nas perguntas geradas
    - WSIDeterministicScorer: Score rule-based como baseline — evita viés do LLM
    - BiasAuditService: Gera snapshots Four-Fifths Rule por 4 dimensões:
      Gender, Age Group, Disability, Region — sem PII nos stats (SOX/ISO 27001)
    - Determinismo: Mesma resposta → mesmo score (scorer determinístico valida LLM)
    - Off-script máximo: 3 perguntas antes de retomada forçada — evita manipulação
  Automacoes/Triggers:
    - Triagem completa → handle_screening_completed (automation_handlers.py)
      → CommunicationDispatcher despacha feedback multicanal
    - Score ≥ 7.5 → auto_move_to_interview (cria activity + move stage)
    - Score < 7.5 → cria sugestão para recrutador (NÃO auto-rejeita — human-in-the-loop)
    - _trigger_post_completion() → email de confirmação ao candidato
    - AutomationScheduler: auto_complete_expired_screenings (a cada hora)
  Fallbacks:
    - LLM cascade: Anthropic → Gemini → OpenAI (3 fallbacks)
    - TTS falha → resposta texto-only (chat funciona sem áudio)
    - Intent unclear → resposta genérica + retoma script
    - CommunicationDispatcher falha → log warning, não bloqueia conclusão

Arquivos de Referencia (Prototipo LIA):
  - serviço: lia-agent-system/app/services/triagem_session_service.py (887L — copiar e adaptar)
  - modelo: lia-agent-system/app/models/triagem_session.py
  - dispatcher: lia-agent-system/app/domains/communication/services/communication_dispatcher.py
  - wsi_service: lia-agent-system/app/domains/cv_screening/services/wsi_service.py
  - wsi_scorer: lia-agent-system/app/services/wsi_deterministic_scorer.py
  - wsi_graph: lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py
  - lia_score: lia-agent-system/app/services/lia_score_service.py
  - fairness: lia-agent-system/app/shared/compliance/fairness_guard.py
  - bias_audit: lia-agent-system/app/services/bias_audit_service.py
  - pii: lia-agent-system/app/shared/pii_masking.py
  - consent: lia-agent-system/app/services/consent_checker_service.py
  - model_drift: lia-agent-system/app/services/model_drift_service.py
  - llm: lia-agent-system/app/services/llm.py (LLM provider cascade)

Arquivos Adicionais no Replit (Código Existente):
  - service: lia-agent-system/app/services/triagem_session_service.py (~887L)
  - model-db: lia-agent-system/libs/models/lia_models/triagem.py (TriagemSession)
  - model-db: lia-agent-system/libs/models/lia_models/screening.py (ScreeningResult)
  - wsi: lia-agent-system/app/services/wsi_screening_pipeline.py
  - prompts: lia-agent-system/app/prompts/domains/cv_screening.yaml
  - domain: lia-agent-system/app/domains/cv_screening/ (inteiro)
  - agent: lia-agent-system/app/domains/cv_screening/agents/ (PipelineReActAgent)
  - scoring: lia-agent-system/app/services/voice_screening_analysis.py (wsi_deterministic_scorer)

Tabelas PostgreSQL:
  triagem_sessions (token, status, voice_mode, wsi_final_score, recommendation), triagem_messages (role, content, block_index, audio_base64)
```


---

### TRI-006: InputBar — Barra de Input com Áudio e Controles

```yaml
Titulo: "[Chat Web] InputBar — Campo de Texto + Gravação de Áudio + Controles de Voz"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, triagem, voz, acessibilidade]
Dependências: TRI-001, VOZ-001

Descricao: |
  Componente React (~155L) que renderiza a barra de input fixa
  no bottom do chat. Combina:
  1. Textarea auto-resize (max 120px)
  2. Botão de gravação de áudio (AudioRecordButton)
  3. Botão de envio (Send icon)
  4. Controles de voz mode (mute/unmute, finalizar conversa)
  
  Quando voiceMode=true, exibe barra extra acima do input com:
  - Botão mute/unmute (Volume2/VolumeX icons)
  - Botão "Finalizar Conversa" (PhoneOff icon, vermelho)

Requisitos Tecnicos:
  Frontend:
    - Props: { onSend, onAudioTranscription?, isSending?, disabled?,
        audioEnabled?, placeholder?, className?, voiceMode?, isMuted?,
        onToggleMute?, onEndConversation? }
    - Textarea: auto-resize via scrollHeight, max-height 120px
    - Enter key: envia (sem Shift), Shift+Enter: nova linha
    - AudioRecordButton: renderiza se audioEnabled=true
    - Controles voz: renderiza se voiceMode=true
    - Mute button: bg-[#60BED1]/10 quando ativo
    - End call button: bg-red-50, text-red-600

DoD:
  - [x] Textarea funcional com auto-resize
  - [x] Enter envia, Shift+Enter nova linha
  - [x] AudioRecordButton renderiza
  - [x] Controles de voz condicionais
  - [x] Disabled state durante envio

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/triagem/InputBar.tsx (155L)
  - audio-button: plataforma-lia/src/components/ui/audio-record-button.tsx

Arquivos Adicionais no Replit (Código Existente):
  - component: plataforma-lia/src/components/triagem/InputBar.tsx
  - audio-rec: plataforma-lia/src/components/ui/audio-record-button.tsx
  - voice-btn: plataforma-lia/src/components/chat/voice-chat-button.tsx
```


---

### TRI-007: Página de Triagem — /triagem/[token]

```yaml
Titulo: "[Chat Web] Página de Triagem — /triagem/[token] (~311L)"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 8
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, página, triagem, layout, routing]
Dependências: TRI-001, TRI-002, TRI-003, TRI-004, TRI-006

Descricao: |
  Página Next.js (~311L) que orquestra todos os componentes do chat.
  Rota dinâmica: /triagem/[token] onde token é UUID da sessão.
  
  Estado da página via pageState do hook useTriagemChat:
  - "loading": spinner centralizado
  - "error": mensagem de erro (token inválido, expirado, etc)
  - "welcome": WelcomeCard com branding da empresa
  - "chat": ChatContainer com MessageBubble[] + InputBar + ProgressBar
  - "confirmation": ConfirmationCard (pré-conclusão)
  - "completion": CompletionCard (pós-conclusão)
  
  Estado de voz gerenciado localmente:
  - isVoiceMode: boolean (ativado pelo WelcomeCard onStart(true))
  - isMuted: boolean (toggle via InputBar)
  - autoPlayAudio: boolean (última mensagem LIA auto-play se !isMuted)

Requisitos Tecnicos:
  Frontend:
    - Rota: src/app/triagem/[token]/page.tsx
    - Hook: useTriagemChat(token)
    - Componentes usados: WelcomeCard, ChatContainer, MessageBubble,
        InputBar, ProgressBar, CompletionCard, ConfirmationCard
    - Layout: flex flex-col h-screen, scroll automático ao fundo
    - voiceMode state: useState(false), setado por startChat callback
    - Auto-scroll: useRef + scrollIntoView ao adicionar mensagens
    - Metadata: <title> dinâmico com nome da empresa e vaga

DoD:
  - [x] Todos os 6 pageStates renderizam corretamente
  - [x] Voice mode propaga para sendMessage e InputBar
  - [x] Auto-scroll funcional
  - [x] Layout full-height (h-screen)
  - [x] Responsive (mobile-first)

Criterios de Aceitacao:
  - [x] /triagem/{token_valido} → WelcomeCard com branding
  - [x] /triagem/{token_invalido} → error com mensagem amigável
  - [x] Iniciar conversa → chat com mensagens
  - [x] Completar → CompletionCard com resumo

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — página é consumidora do hook useTriagemChat
    - Indiretamente: Backend PipelineReActAgent gerencia sessão e scoring
  Tools Utilizadas: Nenhuma — página é frontend, consome hook useTriagemChat
  Servicos IA Consumidos (via hook):
    - start_session: Backend cria sessão WSI + gera welcome_message personalizado
    - process_message: Backend classifica intent, avalia resposta, gera próxima pergunta
    - TTS: Se voiceMode=true, backend retorna audio_base64 junto com cada mensagem
  Modelo LLM: Nenhum no frontend — toda IA roda no backend
  Governanca e Compliance:
    - Token-only access: Sem login — screening_invite_token é a autenticação
    - localStorage: Mensagens + estado persistidos — LGPD: deve ser limpável
    - CompletionCard: Mostra resumo APENAS da performance, NÃO dos dados pessoais
    - ProgressBar: Indica progresso (blocos concluídos / total) — transparência ao candidato
    - WelcomeCard: Branding da empresa + consentimento implícito (iniciar = aceitar)
  Fairness e Bias:
    - Mesma interface para todos os candidatos — sem variação por perfil
    - VoiceMode opcional — acessibilidade para candidatos com deficiência visual
  Fallbacks:
    - Token inválido → error page com mensagem amigável
    - Backend offline → mensagem de erro + retry automático
    - Sessão já concluída → CompletionCard direto (sem re-triagem)

Arquivos de Referencia (Prototipo LIA):
  - página: plataforma-lia/src/app/triagem/[token]/page.tsx (311L)
  - container: plataforma-lia/src/components/triagem/ChatContainer.tsx (24L)
  - progress: plataforma-lia/src/components/triagem/ProgressBar.tsx (48L)
  - completion: plataforma-lia/src/components/triagem/CompletionCard.tsx (82L)

Arquivos Adicionais no Replit (Código Existente):
  - page: plataforma-lia/src/app/triagem/[token]/page.tsx (~311L)
  - layout: plataforma-lia/src/app/triagem/[token]/layout.tsx (standalone, sem nav)
  - container: plataforma-lia/src/components/triagem/ChatContainer.tsx
  - progress: plataforma-lia/src/components/triagem/ProgressBar.tsx
  - completion: plataforma-lia/src/components/triagem/CompletionCard.tsx
  - likert: plataforma-lia/src/components/triagem/LikertScaleCard.tsx
  - mcq: plataforma-lia/src/components/triagem/MultipleChoiceCard.tsx
```


---

### TRI-008: Proxy Route — Backend Proxy para Triagem

```yaml
Titulo: "[Chat Web] Proxy Route Next.js — /api/backend-proxy/triagem/[...path]"
Tipo: Feature
Area: Frontend (API Route)
Sprint: S1
Pontos: 3
Prioridade: Crítica
Epic: É31
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend proxy)
Fase: MVP Alpha 1
Tags: [frontend, api-route, proxy, next.js]
Dependências: TRI-005

Descricao: |
  Rota catch-all do Next.js que proxeia todas as chamadas de triagem
  para o backend FastAPI. Necessário porque o frontend (port 5000)
  e o backend (port 8000) rodam em portas diferentes.
  
  Pattern: /api/backend-proxy/triagem/{...path}
  → http://localhost:8000/api/v1/triagem/{...path}
  
  Suporta: GET, POST, PUT, DELETE
  Propaga: headers, body, query params

Requisitos Tecnicos:
  Frontend:
    - Arquivo: src/app/api/backend-proxy/triagem/[...path]/route.ts
    - Backend URL: http://localhost:8000 (ou BACKEND_URL env var)
    - Catch-all: [...path] captura todos os sub-paths
    - Métodos: GET e POST são obrigatórios

DoD:
  - [x] Proxy funcional para GET /triagem/{token}
  - [x] Proxy funcional para POST /triagem/{token}/start
  - [x] Proxy funcional para POST /triagem/{token}/message
  - [x] Headers propagados corretamente

Arquivos de Referencia (Prototipo LIA):
  - proxy: plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts

Arquivos Adicionais no Replit (Código Existente):
  - proxy: plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts
  - backend: lia-agent-system/app/api/v1/triagem.py
```


---

## 5. Cards Completos — É32 Comunicação Multicanal (COM) — Épico [WT-1520](https://wedotalent.atlassian.net/browse/WT-1520)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md` §8
> **Épico:** É32 — Comunicação Multicanal
> **Status Jira:** COM-001→005 = WT-1538→WT-1542 (criados)

### COM-001: CommunicationDispatcher — Classe Central de Envio

```yaml
Titulo: "[Comunicação] CommunicationDispatcher — Mailgun + Mailgun + Meta WhatsApp + Tone Policy (~533L)"
Tipo: Feature
Area: Backend
Sprint: S1
Pontos: 8
Prioridade: Crítica
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, comunicação, email, whatsapp, sms, mailgun, twilio]
Dependências: Nenhuma

Descricao: |
  Classe Python (~533L) que centraliza TODA comunicação da plataforma
  com candidatos. Encapsula Mailgun (email) e Meta WhatsApp API (primário) + Twilio (fallback SMS)
  com lazy initialization, mock em desenvolvimento, e aplicação de
  tone policy por empresa.
  
  Métodos de envio direto (low-level):
  - send_email(to, subject, html, text?, from_name?, reply_to?) → Dict
  - send_whatsapp(to_phone, message, template_sid?) → Dict
  - send_sms(to_phone, message) → Dict
  
  Método inteligente (high-level):
  - dispatch_message(company_id, email?, phone?, subject?, message,
      channel?, candidate_name?, db?, multi_channel=True) → Dict
    - Carrega lia_tone via get_policy_for_company()
    - Aplica tone ao texto via _apply_tone()
    - Se multi_channel=True: envia para TODOS os canais disponíveis
    - Se channel especificado: envia para canal único
    - Retorna { success, channels_sent[], results{} }
  
  Padrão de retorno (todos os métodos):
    { success: bool, message_id: str, mock: bool, channel: str,
      recipient: str, timestamp: str, error?: str }
  
  Mock em dev: quando API keys não configuradas, retorna mock success
  com message_id tipo "mock-email-{uuid12}" para não bloquear dev.

Historia de Usuario: |
  Como sistema, eu quero um ponto único de envio de comunicações,
  para que qualquer parte da plataforma possa notificar candidatos
  sem se preocupar com providers ou configuração.

Regras de Negocio:
  1. Lazy init: clients só inicializam quando necessário
  2. Mock em dev: retorna success=true com mock=true (não bloqueia)
  3. lia_tone consultado via get_policy_for_company(company_id, db)
  4. _apply_tone modifica APENAS o greeting (não reescreve mensagem)
  5. Multi-channel default: envia para email E WhatsApp quando ambos disponíveis
  6. Rate limit: 10 emails/minuto por usuário (em email_templates.py)
  7. WhatsApp: auto-prefix "whatsapp:" no número se não presente
  8. Singleton: communication_dispatcher = CommunicationDispatcher()

Requisitos Tecnicos:
  Backend:
    - Classe: CommunicationDispatcher
    - Dependências: mailgun, twilio
    - Env vars: MAILGUN_API_KEY, MAILGUN_FROM_EMAIL, MAILGUN_FROM_NAME,
        TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM,
        TWILIO_SMS_FROM (ou TWILIO_PHONE_NUMBER)
    - Policy: app.shared.policy_middleware.get_policy_for_company()
    - Tones: professional, friendly, formal
    - Greetings por tone:
      professional → "Olá, {nome_completo}. "
      friendly → "Oi, {primeiro_nome}! "
      formal → "Prezado(a) Sr(a). {nome_completo}, "

DoD:
  - [x] send_email funcional com Mailgun
  - [x] send_whatsapp funcional com Twilio
  - [x] send_sms funcional com Twilio
  - [x] dispatch_message com multi_channel
  - [x] Mock em dev quando keys não configuradas
  - [x] lia_tone aplicado corretamente
  - [x] Singleton instanciado
  - [ ] Testes unitários para cada método

Criterios de Aceitacao:
  - [x] Sem MAILGUN_API_KEY → retorna {success:true, mock:true}
  - [x] Com MAILGUN_API_KEY → email enviado, retorna message_id
  - [x] dispatch_message com email + phone → 2 canais enviados
  - [x] dispatch_message com tone="friendly" → "Oi, Maria!"
  - [x] dispatch_message com tone="formal" → "Prezado(a) Sr(a). Maria Silva,"

Inteligencia e Automacao:
  Agentes Envolvidos:
    - CommunicationReActAgent (domain=communication): Usa dispatch como tool para envio
    - Todos os agentes que precisam notificar candidatos chamam dispatcher indiretamente
  Tools Utilizadas:
    - send_communication: Proxy para dispatch_message (CommunicationReActAgent)
    - send_batch_communication: Envio em lote para múltiplos candidatos
    - generate_message: Geração de texto personalizado via LLM
    - personalize_communication: Ajusta tom/conteúdo por candidato
  Servicos IA:
    - get_policy_for_company(): Carrega lia_tone da empresa (professional/friendly/formal)
    - _apply_tone(): Modifica APENAS o greeting baseado no tone — não reescreve mensagem
    - candidate_feedback_service: Complementa dispatcher para emails Gate-specific
  Modelo LLM: Nenhum no dispatcher em si — tone é rule-based (templates por tone)
  Governanca e Compliance:
    - PolicyEngine: Regra "communication_hours" (08h-20h) — restringe horário de envio
    - Rate Limiting: 10 emails/minuto por usuário (rate_limit_rules.messages_per_hour)
    - PII Masking: PIIMaskingFilter em todos os logs de envio
    - ConsentChecker: Verificação antes de envio (soft enforcement)
    - Mock em dev: Quando API keys não configuradas, retorna mock success sem enviar
      (previne vazamento de dados reais em ambiente dev)
    - Email Tracking: inject_pixel_and_links() para rastreamento de opens/clicks
    - Multi-tenant: lia_tone é per-company — cada empresa tem tom próprio
  Fairness e Bias:
    - Tone uniforme por empresa: Todos os candidatos recebem mesmo tom de comunicação
    - Templates padronizados: Evitam linguagem discriminatória ad-hoc
  Fallbacks:
    - Mailgun offline → mock success (dev), error logged (prod)
    - Twilio offline → mock success (dev), email-only fallback (prod)
    - multi_channel=True + apenas email disponível → envia só email (sem error)

Arquivos de Referencia (Prototipo LIA):
  - dispatcher: lia-agent-system/app/domains/communication/services/communication_dispatcher.py (533L — copiar)
  - service ref: lia-agent-system/app/services/communication_dispatcher.py (1L import re-export)
  - policy: lia-agent-system/app/shared/policy_middleware.py
  - channels: lia-agent-system/app/core/template_channels.py (8 canais definidos)
  - email_tracking: lia-agent-system/app/services/email_tracking_service.py
  - rate_limits: lia-agent-system/app/config/default_rules.json (messages_per_hour)

Arquivos Adicionais no Replit (Código Existente):
  - service: lia-agent-system/app/services/communication_dispatcher.py
  - email-svc: lia-agent-system/app/domains/communication/services/email_service.py
  - email-provider-factory: lia-agent-system/app/services/email_providers/__init__.py
  - email-provider-mailgun: lia-agent-system/app/services/email_providers/sendgrid_provider.py (→ migrar para mailgun_provider.py)
  - email-provider-resend: lia-agent-system/app/services/email_providers/resend_provider.py (fallback)
  - whatsapp-factory: lia-agent-system/app/services/whatsapp_factory.py
  - whatsapp-meta: lia-agent-system/app/services/whatsapp_meta_service.py (Meta Cloud API — primário)
  - whatsapp-twilio: lia-agent-system/app/services/whatsapp_twilio_service.py (Twilio — fallback)
  - whatsapp-webhook: lia-agent-system/app/api/v1/whatsapp.py
  - multi-channel: lia-agent-system/app/shared/channels/multi_channel_service.py
  - channel-router: lia-agent-system/app/shared/channels/channel_router.py (fallback logic)
  - email-adapter: lia-agent-system/app/shared/channels/adapters/email_adapter.py
  - whatsapp-adapter: lia-agent-system/app/shared/channels/adapters/whatsapp_adapter.py
  - notification: lia-agent-system/libs/messaging/lia_messaging/notification_service.py
  - model-db: lia-agent-system/libs/models/lia_models/communication_history.py
  - model-db: lia-agent-system/libs/models/lia_models/communication_matrix.py
  - model-db: lia-agent-system/libs/models/lia_models/communication_settings.py
  - model-db: lia-agent-system/libs/models/lia_models/email_template.py
  - model-db: lia-agent-system/libs/models/lia_models/whatsapp_conversation.py
  - api: lia-agent-system/app/api/v1/communication.py
  - api: lia-agent-system/app/api/v1/communication_settings.py
  - api: lia-agent-system/app/api/v1/communication_matrix.py
  - api: lia-agent-system/app/api/v1/email.py
  - api: lia-agent-system/app/api/v1/email_templates.py
  - api: lia-agent-system/app/api/v1/email_tracking.py
  - frontend: plataforma-lia/src/app/admin/configuracoes/comunicacoes/page.tsx
  - frontend: plataforma-lia/src/components/communication/message-composer.tsx
  - frontend: plataforma-lia/src/components/email-templates/email-templates-manager.tsx
  - frontend: plataforma-lia/src/components/modals/unified-communication-modal.tsx

Tabelas PostgreSQL:
  communication_history, communication_matrix, communication_settings, email_templates, email_logs, whatsapp_conversations
```


---

### COM-002: Dispatch Automático — Screening Feedback

```yaml
Titulo: "[Comunicação] Dispatch Automático #1 — Feedback de Triagem (Aprovado/Reprovado)"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, automação, comunicação, triagem]
Dependências: COM-001

Descricao: |
  Quando um candidato completa a triagem WSI (via handle_screening_completed),
  o sistema envia feedback multicanal automático.
  
  Trigger: handle_screening_completed()
  Subject: "Resultado da Triagem - {Aprovado|Reprovado}"
  Body: "Sua triagem ({WSI}) foi concluída. Resultado: {status}."
  Canais: email + WhatsApp (multi_channel=True)
  Tone: lia_tone da empresa (via policy)

Requisitos Tecnicos:
  Backend:
    - Localização: automation_handlers.py, handle_screening_completed() (linhas 60-142)
    - Busca candidate por ID para obter email/phone
    - CommunicationDispatcher.dispatch_message() com candidate_name
    - Registra: result["feedback_sent"], result["feedback_channels"]

DoD:
  - [x] Dispatch multicanal após triagem aprovada
  - [x] Dispatch multicanal após triagem reprovada
  - [x] Fallback se candidato sem contato (log warning)
  - [x] Result registra canais usados

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa handle_screening_completed como task
    - CommunicationReActAgent (domain=communication): Personaliza e envia feedback multicanal
    - PipelineReActAgent (domain=pipeline): Pós-screening, decide próximo stage
  Tools Utilizadas:
    - send_feedback: Envia resultado estruturado ao candidato
    - update_candidate_stage: Move candidato para próximo stage baseado no score
  Servicos IA:
    - candidate_feedback_service.send_gate_feedback(): 4 gates disponíveis:
      "screening_invited" / "gate1_rejected" / "gate2_rejected" / "approved"
    - CommunicationDispatcher.dispatch_message(): Envio multicanal com lia_tone
  Modelo LLM: Nenhum — feedback usa templates canônicos (_GATE_BODIES)
  Governanca e Compliance:
    - PII Masking: PIIMaskingFilter nos logs de feedback
    - Audit Trail: result["feedback_sent"], result["feedback_channels"] registrados
    - LGPD: Candidato tem direito de saber resultado — feedback é obrigação legal
    - EU AI Act: Candidato rejeitado por IA deve receber explicação (human-readable)
  Fairness e Bias:
    - Feedback idêntico por gate: Template garante que aprovados/reprovados recebem
      mesmo formato de comunicação — sem variação por perfil demográfico
    - BiasAuditService: Snapshot de taxa aprovação/reprovação por grupo demográfico
  Fallbacks:
    - Candidato sem email/phone → log warning, feedback_sent=False (não crasheia)
    - Mailgun/Twilio offline → registra falha, candidato pode consultar status via portal

Arquivos de Referencia (Prototipo LIA):
  - handler: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 60-142)
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py
```


---

### COM-003: Dispatch Automático — Rejeição por Stage Change

```yaml
Titulo: "[Comunicação] Dispatch Automático #2 — Rejeição ao Mudar de Stage"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, automação, comunicação, rejeição]
Dependências: COM-001

Descricao: |
  Quando candidato é movido para stage de rejeição (rejected, reprovado,
  declined, desistente, etc), sistema envia comunicação de rejeição.
  
  Trigger: handle_stage_changed() → stage in rejected_stages
  Subject: "Atualização sobre sua candidatura"
  Body: "Agradecemos seu interesse e participação no processo seletivo.
  Após análise cuidadosa, decidimos seguir com outros candidatos.
  Motivo: {rejection_reason}"
  Default reason: "Perfil não aderente aos requisitos da vaga"

Requisitos Tecnicos:
  Backend:
    - Localização: automation_handlers.py, handle_stage_changed() (linhas 529-670)
    - ⚠️ Bug fix aplicado: variável `company_id` usada corretamente
      (era `vacancy` antes — NameError corrigido)
    - CommunicationDispatcher.dispatch_message() multicanal

DoD:
  - [x] Rejeição enviada com reason
  - [x] Default reason quando não especificado
  - [x] Multicanal (email + WhatsApp)

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa handle_stage_changed como cascade
    - CommunicationReActAgent (domain=communication): Despacha mensagem de rejeição
    - KanbanReActAgent (domain=kanban): Detecta move para stage rejeitado e dispara cascade
  Tools Utilizadas:
    - send_communication: Envio de rejeição multicanal
    - update_candidate_stage: Stage change que trigger o handler
  Servicos IA:
    - CommunicationDispatcher.dispatch_message(): Envio com lia_tone da empresa
    - candidate_feedback_service.send_gate_feedback("gate1_rejected" | "gate2_rejected"):
      Templates canônicos com dicas de melhoria personalizadas
  Modelo LLM: Nenhum — mensagem de rejeição usa templates (não IA generativa)
  Governanca e Compliance:
    - LGPD: Candidato tem direito de saber motivo da rejeição (Art. 20)
    - EU AI Act: Se rejeição foi baseada em scoring IA, explicação é obrigatória
    - Audit Trail: rejection_reason registrado em additional_data
    - PII Masking: Dados do candidato mascarados nos logs
  Fairness e Bias:
    - Default reason: "Perfil não aderente aos requisitos da vaga" — neutro, sem critérios pessoais
    - BiasAuditService: Taxa de rejeição por grupo demográfico monitorada (Four-Fifths Rule)
    - FairnessGuard: Se rejection_reason contém termos discriminatórios → bloqueia
  Fallbacks:
    - Candidato sem contato → log warning (não crasheia pipeline)
    - Dispatcher falha → rejeição registrada, comunicação fica pendente

Arquivos de Referencia (Prototipo LIA):
  - handler: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 629-670)
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py
  - fairness: lia-agent-system/app/shared/compliance/fairness_guard.py
```


---

### COM-004: Dispatch Automático — Convite de Fila (Queue Invite)

```yaml
Titulo: "[Comunicação] Dispatch Automático #3 — Convite de Fila quando Slot Abre"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, automação, comunicação, fila, saturação]
Dependências: COM-001, SAT-005

Descricao: |
  Quando um slot abre na fila de triagem (via process_screening_queue),
  o sistema envia convite multicanal ao próximo candidato.
  
  2 canais de envio:
  1. WhatsApp direto (se conversa existente e ativa):
     "Olá, {nome}! 👋\n\nTemos uma ótima notícia! Agora há vaga
     para continuar o processo de triagem para *{job_title}*.\n\n
     Vamos continuar? Responda *SIM*! 🚀"
  2. Email via CommunicationDispatcher (fallback):
     Subject: "Convite para Triagem - {job_title}"
     Body: "Temos uma ótima notícia!... Acesse o link: {screening_link}"
     Link: "/triagem/{vacancy_id}?candidate={candidate_id}"

Requisitos Tecnicos:
  Backend:
    - Localização: automation_handlers.py, process_screening_queue() (linhas 980-1080)
    - WhatsApp: via WhatsAppConversation model (se conversa existente)
    - Fallback: CommunicationDispatcher.dispatch_message()
    - metadata: invite_channel, invite_sent gravados no additional_data

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa process_screening_queue
    - CommunicationReActAgent (domain=communication): Envia convite personalizado
  Tools Utilizadas:
    - send_communication: Envio de convite multicanal
    - schedule_secondary_task: Agenda promoção como task após unlock
  Servicos IA:
    - send_gate_feedback("screening_invited"): Email canônico com link /triagem/{token}
    - LIAScoreService: lia_score usado para priorizar ordem de promoção
  Modelo LLM: Nenhum — promoção e convite são determinísticos
  Governanca e Compliance:
    - PII Masking: Email/telefone mascarados nos logs de envio
    - ConsentChecker: Verifica consentimento antes de envio (soft enforcement)
    - Audit Trail: invite_channel + invite_sent registrados em additional_data
    - PolicyEngine: communication_hours (08h-20h) restringe envio
  Fairness e Bias:
    - Priorização por lia_score + FIFO — sem critérios demográficos
    - Mesmo convite para todos os candidatos promovidos (template uniforme)
  Fallbacks:
    - WhatsApp ativo → convite direto; sem WhatsApp → email via send_gate_feedback
    - Email falha → invite_sent=False, candidato permanece promovido (status=screening)
    - Token ausente (legado) → gera novo via secrets.token_urlsafe(32)

Arquivos de Referencia (Prototipo LIA):
  - handler: lia-agent-system/app/domains/automation/services/automation_handlers.py (linhas 980-1080)
  - feedback: lia-agent-system/app/services/candidate_feedback_service.py
```


---

### COM-005: Dispatch Automático — Confirmação Pós-Triagem

```yaml
Titulo: "[Comunicação] Dispatch Automático #5 — Confirmação Real Pós-Conclusão da Triagem"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, comunicação, triagem, confirmação]
Dependências: COM-001, TRI-005

Descricao: |
  Quando candidato completa a triagem WSI, o sistema envia email de
  confirmação REAL (não apenas log "queued") via CommunicationDispatcher.
  
  Trigger: _trigger_post_completion() no TriagemSessionService
  Subject: "Triagem Concluída - {job_title}"
  Body: "Sua triagem para a vaga de {job_title} foi concluída com
  sucesso! Nossa equipe avaliará seu perfil e você receberá uma
  resposta em até 5 dias úteis. Agradecemos sua participação!"
  Canal: email apenas (recipient_phone=None)

Requisitos Tecnicos:
  Backend:
    - Localização: triagem_session_service.py, _trigger_post_completion() (linhas 815-883)
    - CommunicationDispatcher.dispatch_message(recipient_phone=None)
    - Registra: actions["email_confirmation"] = "sent"|"failed"
    - Registra: actions["confirmation_channels"]

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Executa _trigger_post_completion como cascade
    - CommunicationReActAgent (domain=communication): Despacha email de confirmação
  Tools Utilizadas:
    - send_communication: Envio de confirmação (email apenas, recipient_phone=None)
  Servicos IA:
    - CommunicationDispatcher.dispatch_message(): Envio com lia_tone da empresa
    - TriagemSessionService._trigger_post_completion(): Dispara pós-conclusão automática
  Modelo LLM: Nenhum — confirmação usa template fixo
  Governanca e Compliance:
    - LGPD: Confirmação de recebimento é boa prática de transparência
    - Audit Trail: actions["email_confirmation"] = "sent"|"failed" registrado na sessão
    - PII Masking: Email do candidato mascarado nos logs
  Fairness e Bias:
    - Template uniforme: Todos os candidatos recebem mesma confirmação (sem variação)
  Fallbacks:
    - Email falha → actions["email_confirmation"] = "failed" (não bloqueia conclusão)
    - Dispatcher offline → log warning, sessão já está concluída no banco

Arquivos de Referencia (Prototipo LIA):
  - serviço: lia-agent-system/app/services/triagem_session_service.py (linhas 815-883)
  - dispatcher: lia-agent-system/app/domains/communication/services/communication_dispatcher.py
```


---

## 6. Cards Completos — É33 Inscrição Web (INS) — Épico [WT-1521](https://wedotalent.atlassian.net/browse/WT-1521)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md` §9
> **Épico:** É33 — Inscrição Web (Formulário Público)
> **Status Jira:** INS-001→003 = WT-1543→WT-1546 (criados)

### INS-001: Formulário de Inscrição Pública na Página da Vaga

```yaml
Titulo: "[Inscrição Web] Formulário Público — Candidatar-se Online na Página da Vaga"
Tipo: Feature
Area: Frontend + Backend
Sprint: S2
Pontos: 8
Prioridade: Alta
Epic: É33
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend + Backend)
Fase: MVP Alpha 1
Tags: [frontend, backend, formulário, candidatura, lgpd, upload]
Dependências: SAT-001

Descricao: |
  Na página pública da vaga (/vagas/{slug}), além do botão de WhatsApp,
  adicionar formulário "Candidatar-se Online" com:
  1. Nome completo (obrigatório)
  2. Email (obrigatório, validação format)
  3. Telefone/WhatsApp (obrigatório, validação +55)
  4. Upload de CV (obrigatório, PDF/DOCX, max 10MB)
  5. Checkbox LGPD (obrigatório): "Li e concordo com a Política de
     Privacidade e o tratamento dos meus dados pessoais conforme a LGPD."
  
  Backend processa o formulário:
  1. Valida campos e arquivo
  2. Cria Candidate + VacancyCandidate com origin="web"
  3. Verifica saturação do pool orgânico
  4. Se saturado: status = "awaiting_screening" (fila)
  5. Se não saturado: status = "screening" (triagem imediata)
  6. Retorna { success, candidate_id, status, message }

Historia de Usuario: |
  Como candidato, eu quero me candidatar diretamente pela página da
  vaga sem precisar usar WhatsApp.

Regras de Negocio:
  1. Checkbox LGPD é OBRIGATÓRIO (não pode submeter sem marcar)
  2. Upload: aceita PDF e DOCX, max 10MB
  3. Email: validação de formato básica
  4. Telefone: aceita formatos BR (+55 11 99999-9999)
  5. Candidato duplicado: verifica por email antes de criar
  6. origin="web" para todos os candidatos deste formulário
  7. Saturação verificada APÓS criar candidato

Requisitos Tecnicos:
  Backend:
    - Endpoint: POST /api/v1/public-vacancies/p/{slug}/apply
    - Multipart form data (arquivo + campos)
    - Campos: name, email, phone, cv_file, lgpd_consent
    - Validações: email format, file size/type, lgpd=true
    - Cria: Candidate(name, email, phone) + VacancyCandidate(origin="web")
    - Verifica saturação: consulta pool orgânico
  Frontend:
    - Componente: WebApplicationForm
    - Upload: input type="file" accept=".pdf,.docx"
    - Validação client-side antes de submit
    - Loading state durante upload
    - Feedback: mensagem de sucesso com status (fila ou triagem)

DoD:
  - [x] Formulário com 5 campos renderiza
  - [x] Validação client-side e server-side
  - [x] Upload de CV funcional
  - [x] Candidato criado com origin="web"
  - [x] Verificação de saturação
  - [x] LGPD checkbox obrigatório
  - [x] Feedback ao candidato

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — formulário é UI pura
    - Indiretamente: INS-003 endpoint processa candidatura e verifica saturação
  Tools Utilizadas: Nenhuma — formulário frontend, POST via fetch
  Servicos IA Consumidos (via REST):
    - POST /public-vacancies/{slug}/apply: Backend verifica saturação, cria candidato
    - Se vaga saturada: candidato entra em awaiting_screening (fila automática)
  Modelo LLM: Nenhum
  Governanca e Compliance:
    - LGPD consent checkbox: lgpd_consent=true obrigatório antes de submit
    - CV upload: Max 10MB, formatos PDF/DOCX apenas (sem executáveis)
    - Dados mínimos: name, email, phone, cv_file — sem coleta excessiva
    - Sem login: Formulário público — reduz fricção mas aumenta risco de spam
      Mitigação: rate limiting no endpoint + validação de email
  Fairness e Bias:
    - Campos de diversidade (deficiência, gênero) são OPCIONAIS — nunca blocking
    - Mesma interface para todos os candidatos
  Fallbacks:
    - Validação client-side: Erros mostrados inline antes de submit
    - Vaga não encontrada → error message com link para listagem
    - Upload falha → mensagem clara + botão retry

Arquivos de Referencia (Prototipo LIA):
  - spec: docs/pipeline-transition-system.md (bypass Gate 1 para inscrição web)

Arquivos Adicionais no Replit (Código Existente):
  - proxy: plataforma-lia/src/app/api/backend-proxy/public-vacancies/route.ts
  - proxy: plataforma-lia/src/app/api/public-proxy/ (rota pública sem auth)
```


---

### INS-002: Página Pública da Vaga (/vagas/[slug])

```yaml
Titulo: "[Inscrição Web] Página Pública da Vaga — Detalhes + Formulário"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É33
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, página, público, seo, vaga]
Dependências: INS-001

Descricao: |
  Página pública (sem autenticação) que exibe detalhes da vaga e
  permite candidatura direta. URL: /vagas/{slug}
  
  Seções:
  1. Header: logo empresa + nome empresa
  2. Título da vaga + localização + tipo (CLT/PJ)
  3. Descrição da vaga (rich text)
  4. Requisitos
  5. Benefícios
  6. Formulário de candidatura (INS-001)
  7. Botão alternativo WhatsApp (se configurado)
  8. Footer: "Powered by WeDo Talent" (aqui sim, pode mostrar)

Requisitos Tecnicos:
  Backend:
    - Endpoint: GET /api/v1/public-vacancies/p/{slug}
    - Retorna dados da vaga sem autenticação
    - Campos: title, description, requirements, benefits, location,
        employment_type, company_name, company_logo_url, slug
  Frontend:
    - Rota: src/app/vagas/[slug]/page.tsx
    - SEO: meta tags dinâmicos (title, description, og:image)
    - Responsive: mobile-first
    - Sem autenticação necessária

DoD:
  - [x] Página renderiza sem login
  - [x] Detalhes da vaga completos
  - [x] Formulário de candidatura integrado
  - [ ] SEO meta tags
  - [x] Responsive

Arquivos de Referencia (Prototipo LIA):
  - endpoint: lia-agent-system/app/api/v1/job_board.py

Arquivos Adicionais no Replit (Código Existente):
  - proxy: plataforma-lia/src/app/api/backend-proxy/public-vacancies/route.ts
  - backend: lia-agent-system/app/api/v1/job_board.py (public vacancy listing)
```


---

### INS-003: Endpoint de Candidatura Pública

```yaml
Titulo: "[Inscrição Web] Endpoint POST /public-vacancies/{slug}/apply"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 5
Prioridade: Alta
Epic: É33
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, api, candidatura, upload, lgpd]
Dependências: SAT-001

Descricao: |
  Endpoint público (sem autenticação) que recebe candidaturas.
  Processa upload de CV, cria candidato, verifica saturação.

Requisitos Tecnicos:
  Backend:
    - Endpoint: POST /api/v1/public-vacancies/p/{slug}/apply
    - Content-Type: multipart/form-data
    - Campos: name (str), email (str), phone (str),
        cv_file (UploadFile), lgpd_consent (bool)
    - Validações:
      - slug existe e vaga está publicada
      - lgpd_consent == True (400 se False)
      - cv_file: max 10MB, type in [pdf, docx]
      - email format válido
      - Duplicata: SELECT candidate WHERE email = ?
    - Fluxo:
      1. Busca vaga por slug
      2. Valida campos
      3. Processa CV (storage)
      4. Cria Candidate se não existe
      5. Cria VacancyCandidate(origin="web")
      6. Verifica saturação pool orgânico
      7. Se saturado: status = "awaiting_screening"
      8. Se livre: status = "screening"
      9. Retorna { success, candidate_id, status, message }

DoD:
  - [x] Upload de CV funcional
  - [x] Candidato criado com origin="web"
  - [x] Duplicata detectada por email
  - [x] Saturação verificada
  - [x] LGPD validado

Inteligencia e Automacao:
  Agentes Envolvidos:
    - AutomationReActAgent (domain=automation): Pós-inscrição, verifica saturação
    - CommunicationReActAgent (domain=communication): Dispara confirmação/convite ao candidato
  Tools Utilizadas:
    - check_saturation: Verifica se pool orgânico está saturado
    - send_communication: Confirmação de recebimento ao candidato
  Servicos IA:
    - SaturationService: Calcula saturação do pool orgânico (activeInScreening/max_screening_slots)
    - CVScoringService (futuro): Score de CV para priorização na fila (se saturado)
  Modelo LLM: Nenhum — endpoint é determinístico (CRUD + check saturação)
  Governanca e Compliance:
    - LGPD: lgpd_consent == True é pré-requisito (400 se False)
    - LGPD: CV armazenado com referência ao consentimento
    - PII: Dados do candidato (nome, email, phone) são PII — storage criptografado
    - Duplicata: email unique check — candidato existente é reutilizado (sem duplicação)
    - origin="web": Tracking de fonte de candidatura para analytics de diversidade
    - EU AI Act: Se saturação leva a rejeição implícita (fila), candidato deve saber
  Fairness e Bias:
    - Saturação é numérica: Baseada em contagem, não em perfil do candidato
    - FIFO: Fila de espera por order de inscrição (sem critérios demográficos)
    - origin tracking: Permite análise de diversidade por canal de entrada
  Fallbacks:
    - CV upload falha → 400 com mensagem clara (formato inválido ou tamanho)
    - Saturação check falha → is_saturated=False (candidato NÃO é bloqueado)
    - Email duplicado → reutiliza candidato existente, cria nova VacancyCandidate

Arquivos de Referencia (Prototipo LIA):
  - endpoint: lia-agent-system/app/api/v1/job_board.py
  - saturação: lia-agent-system/app/api/v1/saturation.py

Arquivos Adicionais no Replit (Código Existente):
  - backend: lia-agent-system/app/api/v1/job_board.py (POST apply endpoint)
  - saturation-check: lia-agent-system/app/api/v1/saturation.py (verifica saturação no apply)
  - model-db: lia-agent-system/libs/models/lia_models/candidate.py
  - model-db: lia-agent-system/libs/models/lia_models/job_vacancy.py
```


---

## 7. Cards Completos — É34 Voz Bidirecional (VOZ) — Épico [WT-1522](https://wedotalent.atlassian.net/browse/WT-1522)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md` §10
> **Épico:** É34 — Suporte a Voz Bidirecional
> **Status Jira:** VOZ-001→004 = WT-1545→WT-1552 (criados)

### VOZ-001: AudioRecordButton — Gravação de Áudio do Candidato (STT)

```yaml
Titulo: "[Voz] AudioRecordButton — Gravação de Áudio + Transcrição (STT)"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: Média
Epic: É34
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, voz, stt, acessibilidade]
Dependências: Nenhuma

Descricao: |
  Componente React que permite ao candidato gravar áudio que é
  transcrito para texto. Integra com API de STT (Deepgram/Whisper).
  
  UX:
  - Botão microfone no InputBar
  - Pressionar inicia gravação (visual: ícone pulsante vermelho)
  - Soltar finaliza e transcreve
  - Texto transcrito é enviado como mensagem

Requisitos Tecnicos:
  Frontend:
    - Componente: AudioRecordButton
    - Props: { onTranscription: (text: string) => void, disabled?: boolean }
    - API: MediaRecorder (Web API)
    - Formato: webm ou wav
    - Transcrição: enviar áudio para backend → retorna texto
  Backend:
    - Endpoint: POST /api/v1/transcribe-audio
    - Provider: Deepgram ou OpenAI Whisper
    - Env vars: DEEPGRAM_API_KEY ou OPENAI_API_KEY

DoD:
  - [x] Gravação de áudio funcional
  - [x] Transcrição via STT provider
  - [x] Texto retornado e enviado como mensagem
  - [x] Visual de gravação (pulsante vermelho)

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — componente é consumidor de API STT
  Tools Utilizadas: Nenhuma — componente frontend, envia áudio via fetch ao backend
  Servicos IA:
    - POST /api/v1/transcribe/audio: Backend transcreve áudio usando STT provider (Deepgram Nova-2)
    - Provider: Deepgram (primário) ou OpenAI Whisper (fallback)
  Modelo LLM:
    - Whisper (OpenAI): Modelo de transcrição speech-to-text
    - Deepgram: Alternativa STT com suporte PT-BR
  Governanca e Compliance:
    - Áudio é PII: Voz do candidato é dado biométrico (LGPD Art. 5, XIV)
    - Áudio NÃO é persistido: Apenas transcrito e descartado após resposta
    - Consentimento: Uso de microfone requer permissão explícita do browser
    - EU AI Act: STT em contexto de recrutamento é HIGH-RISK
  Fairness e Bias:
    - Whisper/Deepgram: Accuracy pode variar por sotaque/dialeto
      ⚠️ Monitorar taxa de erro por região geográfica do candidato
    - Candidato sempre pode digitar: Voice é complementar, nunca obrigatório
  Fallbacks:
    - Microfone negado → botão desabilitado, input texto disponível
    - STT offline → error toast, candidato digita manualmente
    - Transcrição imprecisa → candidato pode editar texto antes de enviar

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/ui/audio-record-button.tsx

Arquivos Adicionais no Replit (Código Existente):
  - component: plataforma-lia/src/components/ui/audio-record-button.tsx
  - voice-btn: plataforma-lia/src/components/chat/voice-chat-button.tsx
  - stt-service: lia-agent-system/app/services/deepgram_service.py
  - voice-api: lia-agent-system/app/api/v1/voice.py
  - proxy: plataforma-lia/src/app/api/backend-proxy/transcribe/audio/route.ts
```


---

### VOZ-002: AudioPlayer — Reprodução de Áudio da LIA (TTS)

```yaml
Titulo: "[Voz] AudioPlayer — Reprodução de Áudio com Controles"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 3
Prioridade: Média
Epic: É34
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend)
Fase: MVP Alpha 1
Tags: [frontend, componente, voz, tts, áudio]
Dependências: Nenhuma

Descricao: |
  Componente React que reproduz áudio gerado pela LIA (TTS).
  Renderiza dentro do MessageBubble quando message.audioUrl presente.
  
  Features:
  - Play/Pause toggle
  - Progress bar
  - Auto-play (configurável)
  - Callbacks: onPlay, onPause, onEnded (para speaking animation)

Requisitos Tecnicos:
  Frontend:
    - Componente: AudioPlayer
    - Props: { src: string, autoPlay?: boolean, className?: string,
        onPlay?, onPause?, onEnded? }
    - HTML5 Audio element
    - Progress bar: input[type=range] sincronizado com currentTime

DoD:
  - [x] Play/Pause funcional
  - [x] Progress bar sincronizado
  - [x] Auto-play funcional
  - [x] Callbacks disparados corretamente

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum — componente é player HTML5 puro
  Tools Utilizadas: Nenhuma — componente frontend, reproduz áudio via HTML5 Audio
  Servicos IA:
    - Consome audio_base64 gerado pelo VOZ-003 (TTS Backend)
    - Nenhuma chamada IA no componente em si
  Modelo LLM: Nenhum
  Governanca e Compliance:
    - Áudio da LIA NÃO é PII — é gerado pela plataforma, não pelo candidato
    - Auto-play: Respeitar preferências de acessibilidade do browser (prefers-reduced-motion)
    - Volume: Respeitar configuração de volume do sistema
  Fairness e Bias:
    - Voz "nova" (OpenAI): Voz feminina neutra — consistente para todos os candidatos
    - Auto-play opcional: Candidatos com deficiência auditiva não são prejudicados
      (texto sempre visível, áudio é complementar)
  Fallbacks:
    - Audio base64 inválido → player oculto, texto visível (graceful degradation)
    - Browser sem suporte a áudio → componente não renderiza

Arquivos de Referencia (Prototipo LIA):
  - componente: plataforma-lia/src/components/ui/audio-player.tsx

Arquivos Adicionais no Replit (Código Existente):
  - component: plataforma-lia/src/components/ui/audio-player.tsx
```


---

### VOZ-003: TTS Backend — Geração de Áudio (OpenAI tts-1)

```yaml
Titulo: "[Voz] TTS Backend — Geração de Áudio via OpenAI tts-1"
Tipo: Feature
Area: Backend
Sprint: S2
Pontos: 5
Prioridade: Média
Epic: É34
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, voz, tts, openai, ia]
Dependências: Nenhuma

Descricao: |
  Função backend que gera áudio a partir do texto da LIA usando
  OpenAI TTS API (modelo tts-1, voice "nova").
  
  Retorna: base64-encoded mp3 audio string
  Fallback: None se OpenAI não disponível
  
  Integração: chamada por start_session() e process_message()
  quando voice_mode=True.

Requisitos Tecnicos:
  Backend:
    - Função: _generate_tts_audio(text: str) → Optional[str]
    - Provider: OpenAI (openai.audio.speech.create)
    - Model: "tts-1"
    - Voice: "nova"
    - Response format: mp3
    - Conversão: response.read() → base64.b64encode → string
    - Env var: OPENAI_API_KEY
    - Fallback: retorna None se falha (chat funciona sem áudio)

DoD:
  - [x] Áudio gerado para texto em português
  - [x] base64 encoding correto
  - [x] Fallback graceful se OpenAI indisponível
  - [x] Integrado com process_message quando voiceMode=True

Inteligencia e Automacao:
  Agentes Envolvidos:
    - Nenhum diretamente — função chamada pelo TriagemSessionService
  Tools Utilizadas: Nenhuma — função interna do serviço, não é tool de agente
  Servicos IA:
    - OpenAI Audio API: openai.audio.speech.create()
    - Modelo: tts-1 (baixa latência, otimizado para streaming)
    - Voice: "nova" (feminina, neutra, tom profissional)
    - Formato: mp3 → base64 encode → retornado na resposta JSON
  Modelo LLM:
    - OpenAI tts-1: Text-to-Speech model
    - NÃO é LLM generativo — é modelo de síntese de voz
  Governanca e Compliance:
    - Áudio gerado é efêmero: base64 retornado na resposta, NÃO persistido no banco
    - Custo: tts-1 é cobrado por caractere — monitorar usage/cost per session
    - OPENAI_API_KEY: Necessária via env var (não hardcoded)
    - Dados enviados ao OpenAI: APENAS texto da LIA (já gerado), sem PII do candidato
  Fairness e Bias:
    - Voz "nova" consistente: Mesmo tom/velocidade para todos os candidatos
    - Idioma: PT-BR — tts-1 suporta português nativamente
    - Acessibilidade: Voz complementa texto, nunca substitui
  Fallbacks:
    - OpenAI indisponível → retorna None (chat funciona sem áudio)
    - API key ausente → retorna None (sem crash, sem log de erro sensível)
    - Texto vazio → retorna None (não gera áudio para mensagem vazia)

Arquivos de Referencia (Prototipo LIA):
  - função: lia-agent-system/app/services/triagem_session_service.py (linhas 16-41)

Arquivos Adicionais no Replit (Código Existente):
  - voice-service: lia-agent-system/app/services/voice_service.py
  - gemini-voice: lia-agent-system/app/services/gemini_voice_service.py
  - voice-provider: lia-agent-system/app/shared/providers/voice_provider.py
  - lia-voice-api: lia-agent-system/app/api/v1/lia_voice.py
  - wsi-voice: lia-agent-system/app/services/wsi_voice_orchestrator.py
  - model-db: lia-agent-system/libs/models/lia_models/voice_screening.py

Tabelas PostgreSQL:
  voice_screenings (status, audio_url, transcript, analysis)
```


---

### VOZ-004: Propagação de Voice Mode no Frontend

```yaml
Titulo: "[Voz] Propagação de isVoiceMode — Estado Runtime no UI"
Tipo: Feature
Area: Frontend
Sprint: S2
Pontos: 3
Prioridade: Alta
Epic: É34
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Frontend + Backend)
Fase: MVP Alpha 1
Tags: [frontend, voz, state-management]
Dependências: TRI-002, TRI-007

Descricao: |
  O estado isVoiceMode do UI é propagado em cada mensagem enviada
  pelo candidato. Isso garante que se o candidato alternar entre
  texto e voz durante a sessão, o backend responde no modo correto.
  
  ⚠️ CORREÇÃO CRÍTICA: Antes, o voiceMode usava apenas o config
  inicial do servidor (session.voice_mode). Agora, o payload de cada
  mensagem inclui { voiceMode: isVoiceMode } com o estado RUNTIME
  do UI, e o backend resolve: parâmetro voiceMode > session.voice_mode.
  
  Tipo SendMessagePayload atualizado com campo voiceMode?: boolean.

Requisitos Tecnicos:
  Frontend:
    - page.tsx: state isVoiceMode (useState(false))
    - Setado por: WelcomeCard onStart(voiceMode=true)
    - Propagado em: sendMessage({ ..., voiceMode: isVoiceMode })
    - SendMessagePayload.voiceMode é Optional<boolean>
  Backend:
    - process_message(voice_mode?: bool):
      use_voice = voice_mode if voice_mode is not None else session.voice_mode
    - Se use_voice=True: gera audio_base64

DoD:
  - [x] isVoiceMode state no page.tsx
  - [x] voiceMode propagado em sendMessage payload
  - [x] Backend resolve voiceMode corretamente
  - [x] Alternar entre texto e voz mid-session funciona

Arquivos de Referencia (Prototipo LIA):
  - types: plataforma-lia/src/components/triagem/types.ts (SendMessagePayload.voiceMode)
  - page: plataforma-lia/src/app/triagem/[token]/page.tsx
  - hook: plataforma-lia/src/hooks/use-triagem-chat.ts
  - backend: lia-agent-system/app/services/triagem_session_service.py (process_message, linhas 499-518)

Arquivos Adicionais no Replit (Código Existente):
  - hook: plataforma-lia/src/hooks/use-triagem-chat.ts (isVoiceMode state)
  - wsi-status: plataforma-lia/src/components/wsi/wsi-voice-screening-status.tsx
```


---

## 8. Cards Completos — VGM Gestão de Vagas (VGM)

> **Fonte:** `jira-cards-job-creation-lifecycle.md`
> **Épico:** VGM — Gestão de Vagas
> **Status Jira:** VGM-001→010 = WT-1494→WT-1504 (existentes)
> **Stack produção:** Vue 3 + Vuetify 3 + Nuxt 3 + Pinia (FE) · FastAPI/Python (BE) · PostgreSQL
> **Skills obrigatórias FE:** `/vue-migration-prep` · `/design-standardize` · `/feature-impact`


### Tags Padronizadas — Cards VGM

| Card | Tags |
|------|------|
| VGM-001 | `fullstack`, `frontend`, `backend`, `IA` |
| VGM-002 | `fullstack`, `frontend`, `backend`, `dados` |
| VGM-003 | `frontend`, `UX` |
| VGM-004 | `fullstack`, `frontend`, `backend`, `dados` |
| VGM-005 | `fullstack`, `frontend`, `backend` |
| VGM-006 | `fullstack`, `frontend`, `backend` |
| VGM-007 | `fullstack`, `frontend`, `IA` |
| VGM-008 | `fullstack`, `frontend`, `backend`, `comunicacao` |
| VGM-009 | `fullstack`, `frontend`, `backend`, `dados` |
| VGM-010 | `backend`, `comunicacao`, `dados` |

### Agentes IA Envolvidos (VGM)

| Agente | Cards | Função |
|--------|-------|--------|
| WizardReActAgent (job_management) | VGM-001→005 | Criação e enriquecimento de vagas via LIA |
| PipelineReActAgent (cv_screening) | VGM-007, VGM-009 | WSI badge, placement tracking |
| CommunicationReActAgent (communication) | VGM-008, VGM-010 | Notificações de pausa/fechamento |

### Tabelas PostgreSQL (VGM)

| Tabela | Modelo | Campos Críticos |
|--------|--------|----------------|
| `job_vacancies` | `lia_models/job_vacancy.py` | title, status, governance_rules, public_link |
| `vacancy_candidates` | `lia_models/candidate.py` | status, lia_score, pipeline_stage |
| `job_vacancy_audit` | `lia_models/job_vacancy_audit.py` | action, old_status, new_status |
| `job_drafts` | `lia_models/job_draft.py` | draft_data (wizard state) |
| `communication_history` | `lia_models/communication_history.py` | channel, template, recipient |


### Fontes de Verdade — Referências do Repositório (VGM)

> Para agentes de IA: **não reimplemente os padrões abaixo**. Leia os arquivos indicados e replique os padrões exatos já estabelecidos no protótipo.

**Frontend (TypeScript / Next.js → migrar para Vue 3 + Nuxt 3):**

| Contrato | Arquivo | Linha |
|---------|---------|-------|
| `JobVacancy` interface | `plataforma-lia/src/services/lia-api.ts` | 2691 |
| `JobVacancyCreateRequest` interface | `plataforma-lia/src/services/lia-api.ts` | 2814 |
| `ManualFormData` interface | `plataforma-lia/src/components/modals/create-job-modal.tsx` | ~35 |
| `createJobVacancy(payload)` | `plataforma-lia/src/services/lia-api.ts` | ~2820 |
| `generatePublicLink(jobId)` | `plataforma-lia/src/services/lia-api.ts` | 974 |
| `closeJobVacancy(jobId, payload)` | `plataforma-lia/src/services/lia-api.ts` | ~2900 |
| Modal escolha + formulário | `plataforma-lia/src/components/modals/create-job-modal.tsx` | 1–226 |
| Modal fechar vaga | `plataforma-lia/src/components/modals/close-vacancy-modal.tsx` | completo |
| Modal pausar/reativar | `plataforma-lia/src/components/modals/job-status-modal.tsx` | completo |

**Backend (FastAPI / Python):**

| Endpoint | Arquivo | Método |
|---------|---------|--------|
| `POST /api/v1/job-vacancies` | `lia-agent-system/app/api/v1/job_vacancies.py` L2021 | Criar vaga |
| `PATCH /api/v1/job-vacancies/{id}` | `lia-agent-system/app/api/v1/job_vacancies.py` ~L2100 | Partial update |
| `POST /api/v1/job-vacancies/{id}/generate-link` | `lia-agent-system/app/api/v1/job_vacancies.py` ~L2200 | Publicar |
| `PATCH /api/v1/job-vacancies/{id}/status` | `lia-agent-system/app/api/v1/job_vacancies.py` ~L3119 | Alterar status |
| `POST /api/v1/job-vacancies/{id}/close` | `lia-agent-system/app/api/v1/job_vacancies.py` ~L2400 | Fechar vaga |

**Resumo de Dependências VGM:**
```
VGM-001 → VGM-002 → VGM-003 → VGM-004 → VGM-005 → VGM-006
  ├── VGM-007 (Triagem Badge)  ├── VGM-008 (Pausar/Reativar)
  └── VGM-009 (Fechar) → VGM-010 (Notificações)
```

---

### CARD VGM-001: Modal de Escolha — LIA vs Criação Manual
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Modal de Escolha: LIA vs Criação Manual"
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 3
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: Nenhuma

Descricao: |
  Ponto de entrada do fluxo de criação de vagas. O botão "+ Nova Vaga"
  na página de gestão de vagas abre um modal com duas opções visuais
  lado a lado. A escolha determina o fluxo subsequente: wizard
  conversacional da LIA ou formulário manual direto.

Historia de Usuario: |
  Como recrutador, quero escolher entre criar a vaga com a ajuda da LIA
  (Wizard conversacional) ou preenchendo manualmente um formulário
  direto, para ter flexibilidade no processo de abertura de vagas.

Regras de Negocio:
  1. O modal aparece ao clicar em qualquer botão "+ Nova Vaga" na página de vagas
  2. Opção "Criar com a LIA" → fecha o modal e abre o chat de criação de vaga (Wizard conversacional)
  3. Opção "Criar manualmente" → avança para o step manual-form dentro do mesmo modal (não abre nova janela)
  4. Fechar o modal (X ou click fora) descarta qualquer estado intermediário e não cria nenhum registro
  5. Multi-tenant: a opção LIA respeita os limites de plano (verificado no backend ao tentar criar)

Requisitos Tecnicos:
  Frontend:
    - Componente CreateJobModal.vue com v-model para isOpen
    - Estado interno step: 'choose' | 'manual-form'
    - Emit choose-wizard para ativar wizard LIA
    - Emit choose-manual para avançar para formulário
    - Composable useJobModal.ts com open/close
  Backend:
    - Nenhum endpoint novo — verificação de limites de plano ao criar vaga (VGM-002)
  Dados:
    - Nenhuma tabela nova neste card
  Validacoes:
    - Fechar modal não deve criar registro no banco

Design & Componentes:
  Componentes Existentes:
    - v-dialog (Vuetify) — container do modal
    - v-card — estrutura interna
    - v-row / v-col — layout dos cards de escolha
  Novos Componentes:
    - CreateJobModal.vue — modal principal com step machine
    - CreateJobForm.vue — formulário manual (step manual-form)
  Design Tokens:
    Modal max-width: 448px
    Border-radius: rounded-md (8px)
    Ícone LIA: color wedo-cyan (#60BED1)
    Ícone Manual: color text-gray-600
    Background hover card: translateY(-2px) com borda
  Layout:
    Modal centralizado, max-width 448px
    Cards de escolha em grid 2 colunas (50/50)
    Botão X no canto superior direito
  Estados:
    - step choose: exibe dois cards de escolha
    - step manual-form: exibe CreateJobForm com botão Voltar
  Acessibilidade:
    - aria-label no botão fechar
    - Role dialog no v-dialog
    - Tab order: LIA → Manual → Fechar

Comportamento de UI:
  Fluxo Principal:
    1. Usuário clica "+ Nova Vaga"
    2. Modal abre no step choose
    3. Dois cards: "Criar com a LIA" e "Criar manualmente"
    4. Clicar "LIA" → emit choose-wizard, modal fecha, chat abre
    5. Clicar "Manual" → step muda para manual-form
    6. No manual-form: botão Voltar retorna para choose
  Estados de Botoes:
    Fechar (X):
      - Default: icon-only, text-gray-500
      - Hover: text-gray-900
  Validacoes Inline:
    Nenhuma neste step
  Mensagens de Feedback:
    Nenhuma — a escolha é silenciosa

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Clicar "Criar com a LIA" emite choose-wizard e fecha modal
  - [ ] Clicar "Criar manualmente" avança para step manual-form
  - [ ] Clicar fora do modal fecha sem criar vaga
  - [ ] Clicar X fecha sem criar vaga
  - [ ] Step manual-form tem botão Voltar que retorna para choose
  - [ ] Dark mode implementado
  - [ ] Responsivo mobile

Criterios de Aceitacao:
  - [ ] Modal abre ao clicar "+ Nova Vaga"
  - [ ] Dois cards de escolha visíveis side by side
  - [ ] Ícone LIA em cyan (#60BED1), ícone Manual em gray-600
  - [ ] Escolher LIA → fecha modal imediatamente
  - [ ] Escolher Manual → exibe formulário sem fechar modal
  - [ ] Fechar modal → nenhum registro criado no banco

Arquivos de Referencia (Prototipo):
  - create-job-modal.tsx: plataforma-lia/src/components/modals/create-job-modal.tsx (linhas 1-226)
  - jobs-page.tsx showCreateJobModal: plataforma-lia/src/components/pages/jobs-page.tsx (linha 142)
  - jobs-page.tsx botão gatilho: plataforma-lia/src/components/pages/jobs-page.tsx (linha 3530)
```

### Implementação Vue/Nuxt

#### Componente: `components/modals/CreateJobModal.vue`

**Props e Emits:**
```typescript
interface Props {
  modelValue: boolean // v-model para isOpen
}
interface Emits {
  (e: 'update:modelValue', val: boolean): void
  (e: 'choose-wizard'): void
  (e: 'choose-manual'): void
}
```

**Estado interno:**
```typescript
const step = ref<'choose' | 'manual-form'>('choose')
```

**Template (Vuetify):**
```vue
<v-dialog v-model="modelValue" max-width="448" persistent>
  <v-card rounded="lg">
    <v-card-title>Nova Vaga</v-card-title>
    <v-card-text>
      <v-row v-if="step === 'choose'">
        <v-col cols="6">
          <v-card variant="outlined" class="cursor-pointer" @click="emit('choose-wizard')">
            <!-- Brain icon cyan + texto "Criar com a LIA" -->
          </v-card>
        </v-col>
        <v-col cols="6">
          <v-card variant="outlined" class="cursor-pointer" @click="step = 'manual-form'">
            <!-- ClipboardList icon + texto "Criar manualmente" -->
          </v-card>
        </v-col>
      </v-row>
      <CreateJobForm v-else @back="step = 'choose'" @created="onJobCreated" />
    </v-card-text>
  </v-card>
</v-dialog>
```

**Composable:** `composables/useJobModal.ts`
```typescript
export function useJobModal() {
  const isOpen = ref(false)
  const open = () => { isOpen.value = true }
  const close = () => { isOpen.value = false }
  return { isOpen, open, close }
}
```


---

### CARD VGM-002: Formulário de Criação Manual de Vaga
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Formulário de Criação Manual de Vaga"
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-001

Descricao: |
  Step manual-form dentro do CreateJobModal. Coleta dados mínimos
  necessários para criação do registro no banco. Após envio, a vaga
  é criada com status "Rascunho" e o usuário é direcionado
  automaticamente para a tab de configurações (VGM-003).

Historia de Usuario: |
  Como recrutador, quero preencher um formulário enxuto com os dados
  essenciais da vaga para criá-la rapidamente como rascunho, sem
  precisar passar pelo wizard conversacional da LIA.

Regras de Negocio:
  1. Campos obrigatórios: title, manager, manager_email
  2. Campos opcionais não enviados se vazios (undefined no payload — sem string vazia)
  3. Ao submeter, o status inicial é sempre "Rascunho" — nunca "Ativa"
  4. work_model usa valores internos do backend: "remoto", "hibrido", "presencial" (sem acento em "híbrido")
  5. employment_type usa os valores: "CLT", "PJ", "Estágio", "Temporário", "Freelancer"
  6. Após criação bem-sucedida: modal fecha, toast de sucesso exibe, e o fluxo de navegação automática inicia (VGM-003)
  7. Em caso de erro da API: toast de erro com mensagem do backend, modal permanece aberto
  8. O botão "Criar e Configurar" fica desabilitado durante o loading (isSubmitting: true)
  9. Multi-tenant: company_id é injetado automaticamente no backend via get_user_company_id(current_user) — não enviado pelo frontend

Requisitos Tecnicos:
  Frontend:
    - Componente CreateJobForm.vue com validação reativa
    - Composable useJobCreate.ts encapsulando chamada de API
    - Validação client-side antes de enviar
    - Estado isSubmitting para desabilitar botão
    - Emit created(jobId, jobTitle) ao sucesso
  Backend:
    - POST /api/v1/job-vacancies (já implementado no protótipo)
    - Auth via get_current_user_or_demo
    - Plano check via check_active_jobs_limit_or_demo
    - company_id injetado via get_user_company_id
    - Status default "Rascunho"
  Dados:
    - Tabela job_vacancies (já existente)
    - Campos mínimos: title, department, work_model, employment_type, manager, manager_email, status, company_id
  Validacoes:
    - title: obrigatório, min 1 char, max 255
    - manager: obrigatório, min 1 char
    - manager_email: obrigatório, formato email válido
    - work_model: enum remoto|hibrido|presencial
    - employment_type: enum CLT|PJ|Estágio|Temporário|Freelancer

Design & Componentes:
  Componentes Existentes:
    - v-text-field (Vuetify) — título, gestor, email
    - v-select (Vuetify) — departamento, modelo trabalho, contratação
    - v-btn — Criar e Configurar, Voltar
    - v-form — container com validação
  Novos Componentes:
    - CreateJobForm.vue — formulário inline dentro do modal
  Design Tokens:
    Botão primário: bg-gray-900, text-white, rounded-md
    Erro de campo: borda vermelha + mensagem abaixo
    Asterisco obrigatório: text-red-500
  Layout:
    Stack vertical de campos, gap 16px
    Modelo de Trabalho + Forma de Contratação: grid 2 colunas (50/50)
    Ações: Voltar (text) à esquerda + Criar e Configurar (filled) à direita
  Estados:
    - Default, Loading (isSubmitting), Error por campo
  Acessibilidade:
    - Labels em todos os campos
    - error-messages associadas aos campos
    - Botão submit desabilitado com aria-disabled durante loading

Comportamento de UI:
  Fluxo Principal:
    1. Usuário está no step manual-form do modal
    2. Preenche Título da Vaga (obrigatório)
    3. Preenche opcionalmente Departamento, Modelo de Trabalho, Contratação
    4. Preenche Gestor Responsável e Email do Gestor (obrigatórios)
    5. Clica "Criar e Configurar"
    6. Validação client-side — se inválido, exibe erros inline
    7. POST para API com payload mapeado
    8. Sucesso: emit created(jobId), modal fecha, toast sucesso, navegação inicia
    9. Erro: toast de erro, modal permanece aberto com dados preservados
  Estados de Botoes:
    Criar e Configurar:
      - Default: bg-gray-900, text-white
      - Loading: spinner + "Criando..."
      - Disabled: durante isSubmitting
    Voltar:
      - Default: variant text, text-gray-600
  Validacoes Inline:
    Título:
      - Erro: "Título é obrigatório"
    Gestor:
      - Erro: "Nome do gestor é obrigatório"
    Email do Gestor:
      - Erro vazio: "Email é obrigatório"
      - Erro formato: "Email inválido"
  Mensagens de Feedback:
    - Sucesso: toast verde "Vaga criada com sucesso!"
    - Erro API: toast vermelho com mensagem do backend

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Submit sem título mostra erro de validação no campo
  - [ ] Submit sem gestor mostra erro de validação
  - [ ] Submit com email inválido mostra erro de validação
  - [ ] Submit válido faz POST para API, toast de sucesso, modal fecha
  - [ ] Erro da API mostra toast de erro, modal permanece aberto
  - [ ] Campos opcionais vazios não enviados no payload (undefined, não string vazia)
  - [ ] work_model "hibrido" sem acento no payload
  - [ ] Botão desabilitado durante isSubmitting
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] Campos obrigatórios com asterisco e validação
  - [ ] Payload POST contém apenas campos preenchidos
  - [ ] Status criado sempre "Rascunho"
  - [ ] company_id não enviado pelo frontend
  - [ ] Resposta 201 retorna id da vaga criada
  - [ ] Após sucesso: emit created(jobId, jobTitle)

Arquivos de Referencia (Prototipo):
  - create-job-modal.tsx ManualFormData: plataforma-lia/src/components/modals/create-job-modal.tsx (linha 16-23)
  - create-job-modal.tsx handleSubmit: plataforma-lia/src/components/modals/create-job-modal.tsx (linhas 118-149)
  - create-job-modal.tsx JSX form: plataforma-lia/src/components/modals/create-job-modal.tsx (linhas 228-375)
  - lia-api.ts createJobVacancy: plataforma-lia/src/services/lia-api.ts (linha 839)
  - job_vacancies.py POST endpoint: lia-agent-system/app/api/v1/job_vacancies.py (linha 2021)
  - job_vacancies.py JobVacancyCreate schema: lia-agent-system/app/api/v1/job_vacancies.py (linhas 99-138)
```

### Implementação Vue/Nuxt

#### Componente: `components/modals/CreateJobForm.vue`

**Emits:**
```typescript
interface Emits {
  (e: 'back'): void
  (e: 'created', jobId: string, jobTitle: string): void
}
```

**Estado reativo:**
```typescript
const form = reactive({
  title: '',
  department: '',
  workModel: '',
  employmentType: '',
  manager: '',
  managerEmail: ''
})
const errors = reactive<Record<string, string>>({})
const isSubmitting = ref(false)
```

**Composable:** `composables/useJobCreate.ts`
```typescript
export function useJobCreate() {
  const jobsApi = useJobsApi()
  async function createJob(data: JobCreatePayload): Promise<{ id: string }> {
    return jobsApi.post('/job-vacancies', data)
  }
  return { createJob }
}
```

**Validação:**
```typescript
function validate(): boolean {
  errors.title = !form.title.trim() ? 'Título é obrigatório' : ''
  errors.manager = !form.manager.trim() ? 'Nome do gestor é obrigatório' : ''
  errors.managerEmail = !form.managerEmail.trim()
    ? 'Email é obrigatório'
    : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.managerEmail)
    ? 'Email inválido'
    : ''
  return !Object.values(errors).some(Boolean)
}
```

**Template (Vuetify):**
```vue
<v-form @submit.prevent="handleSubmit">
  <v-text-field v-model="form.title" label="Título da Vaga *"
    :error-messages="errors.title" />

  <v-select v-model="form.department" label="Departamento"
    :items="DEPARTMENT_OPTIONS" />

  <v-row>
    <v-col cols="6">
      <v-select v-model="form.workModel" label="Modelo de Trabalho"
        :items="WORK_MODEL_OPTIONS" item-title="label" item-value="value" />
    </v-col>
    <v-col cols="6">
      <v-select v-model="form.employmentType" label="Forma de Contratação"
        :items="EMPLOYMENT_TYPE_OPTIONS" />
    </v-col>
  </v-row>

  <v-text-field v-model="form.manager" label="Gestor Responsável *"
    :error-messages="errors.manager" />

  <v-text-field v-model="form.managerEmail" label="Email do Gestor *"
    type="email" :error-messages="errors.managerEmail" />

  <v-card-actions>
    <v-btn variant="text" @click="emit('back')">Voltar</v-btn>
    <v-btn type="submit" color="surface-variant" variant="flat"
      :loading="isSubmitting" class="bg-gray-900 text-white">
      Criar e Configurar
    </v-btn>
  </v-card-actions>
</v-form>
```

### Payload da API (POST)

```json
POST /api/v1/job-vacancies

{
  "title": "Engenheiro de Software Sênior",
  "department": "Tecnologia",
  "work_model": "hibrido",
  "employment_type": "CLT",
  "manager": "João Silva",
  "manager_email": "joao@empresa.com",
  "status": "Rascunho"
}
```

**Resposta (201):**
```json
{
  "id": "uuid-da-vaga",
  "title": "Engenheiro de Software Sênior",
  "status": "Rascunho",
  "created_at": "2026-03-10T..."
}
```

### Banco de Dados

Tabela `job_vacancies` (já existente):
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
company_id      UUID NOT NULL REFERENCES companies(id)
title           VARCHAR(255) NOT NULL
department      VARCHAR(100)
work_model      VARCHAR(50)       -- 'remoto' | 'hibrido' | 'presencial'
employment_type VARCHAR(50)       -- 'CLT' | 'PJ' | 'Estágio' | 'Temporário' | 'Freelancer'
manager         VARCHAR(255)
manager_email   VARCHAR(255)
status          VARCHAR(50) DEFAULT 'Rascunho'
created_at      TIMESTAMP DEFAULT now()
updated_at      TIMESTAMP DEFAULT now()
```


---

### CARD VGM-003: Navegação Automática pós-criação → Tab Configurações
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FRONTEND] Navegação Automática pós-criação para Tab Configurações"
Tipo: Feature
Area: Frontend
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 3
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-002

Descricao: |
  Após criação bem-sucedida via VGM-002, o sistema deve:
  (1) atualizar a lista de vagas incluindo a nova vaga,
  (2) navegar automaticamente para o kanban/view da vaga recém-criada,
  (3) abrir a tab "Configurações" em modo de edição.
  Tudo sem reload da página usando estado reativo e Pinia.

Historia de Usuario: |
  Como recrutador, após criar a vaga manualmente, quero ser redirecionado
  automaticamente para a view de configurações dessa vaga, sem precisar
  procurá-la na lista.

Regras de Negocio:
  1. A navegação ocorre sem window.location.reload() — usando estado reativo (Pinia + Vue Router)
  2. A lista de vagas é re-fetchada imediatamente após criação (refreshKey trigger)
  3. pendingNavigateJobId é setado com o UUID da vaga criada
  4. Um watcher monitora pendingNavigateJobId + jobs e, ao encontrar a vaga na lista, navega
  5. localStorage.setItem("jobCreationMode", jobId) sinaliza para o componente de kanban abrir a tab Configurações
  6. O item jobCreationMode é lido e removido do localStorage pelo componente de kanban no mount
  7. Se a vaga não aparecer na lista em até 10s (timeout), exibir toast de aviso e limpar pendingNavigateJobId
  8. Toast de loading opcional: "Abrindo configurações da vaga..." durante a navegação

Requisitos Tecnicos:
  Frontend:
    - Store Pinia useJobsStore com pendingNavigateJobId e refreshKey
    - Composable useJobNavigation.ts com watcher reativo
    - Vue Router push para /vagas/[id]?tab=configuracoes
    - localStorage flag jobCreationMode para sinalizar modo criação
    - Timeout de 10s com fallback toast
  Backend:
    - Nenhum endpoint novo
  Dados:
    - localStorage: chave jobCreationMode com valor = jobId
  Validacoes:
    - Navegação só ocorre quando a vaga existe na lista local (não navega com dados parciais)

Design & Componentes:
  Componentes Existentes:
    - Skeleton loader da tela de kanban (durante carregamento)
    - Toast de feedback
  Novos Componentes:
    - Nenhum componente visual novo
  Design Tokens:
    Loading skeleton: bg-gray-200 animado
  Layout:
    Sem nova tela — transição transparente para o usuário
  Estados:
    - Aguardando lista atualizar: skeleton ou spinner
    - Vaga encontrada: navegação imediata
    - Timeout 10s: toast amarelo de aviso
  Acessibilidade:
    - Toast de aviso com role="alert"

Comportamento de UI:
  Fluxo Principal:
    1. Modal cria vaga via API → response.id
    2. Callback onJobCreated(jobId) no pai
    3. Modal fecha, toast de sucesso exibe
    4. localStorage.setItem("jobCreationMode", jobId)
    5. store.pendingNavigateJobId = jobId
    6. store.triggerRefresh() — dispara re-fetch da lista
    7. Watcher detecta vaga na lista
    8. router.push('/vagas/[id]?tab=configuracoes')
    9. Componente kanban lê jobCreationMode, seta isCreationMode=true, activeTab='configuracoes'
    10. localStorage.removeItem("jobCreationMode")
  Estados de Botoes:
    Nenhum botão novo
  Validacoes Inline:
    Nenhuma
  Mensagens de Feedback:
    - Loading: "Abrindo configurações da vaga..."
    - Timeout: "A vaga foi criada. Clique aqui para acessá-la."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Criar vaga → lista re-fetcha e inclui nova vaga
  - [ ] Após criação → navegação para kanban da vaga acontece automaticamente
  - [ ] Tab Configurações abre em modo criação (isCreationMode: true)
  - [ ] localStorage.jobCreationMode é removido após leitura
  - [ ] Se API de lista demorar > 10s → toast de feedback ao usuário
  - [ ] Sem window.reload() em nenhum ponto do fluxo

Criterios de Aceitacao:
  - [ ] Após criação bem-sucedida, usuário chega na tab Configurações sem ação manual
  - [ ] isCreationMode=true ativo apenas na primeira abertura pós-criação
  - [ ] localStorage limpo após leitura
  - [ ] Pinia store atualizado com nova vaga

Arquivos de Referencia (Prototipo):
  - jobs-page.tsx onJobCreated callback: plataforma-lia/src/components/pages/jobs-page.tsx (linhas 7514-7519)
  - jobs-page.tsx pendingNavigateJobId: plataforma-lia/src/components/pages/jobs-page.tsx (linhas 143-144)
  - jobs-page.tsx watcher navegação: plataforma-lia/src/components/pages/jobs-page.tsx (linhas 448-457)
  - job-kanban-page.tsx jobCreationMode: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 434-440)
```

### Implementação Vue/Nuxt

#### Store (Pinia): `stores/jobsStore.ts`
```typescript
export const useJobsStore = defineStore('jobs', () => {
  const jobs = ref<Job[]>([])
  const pendingNavigateJobId = ref<string | null>(null)
  const refreshKey = ref(0)

  async function loadJobs() {
    const response = await jobsApi.list()
    jobs.value = response.items.map(mapJob)
  }

  function triggerRefresh() { refreshKey.value++ }

  return { jobs, pendingNavigateJobId, refreshKey, loadJobs, triggerRefresh }
})
```

#### Composable: `composables/useJobNavigation.ts`
```typescript
export function useJobNavigation() {
  const store = useJobsStore()
  const router = useRouter()

  function navigateToJobAfterCreate(jobId: string) {
    localStorage.setItem('jobCreationMode', jobId)
    store.pendingNavigateJobId = jobId
    store.triggerRefresh()
  }

  watch(
    [() => store.jobs, () => store.pendingNavigateJobId],
    ([jobs, pendingId]) => {
      if (!pendingId || !jobs.length) return
      const job = jobs.find(j => j.backendId === pendingId)
      if (!job) return
      store.pendingNavigateJobId = null
      router.push(`/vagas/${job.backendId}?tab=configuracoes`)
    }
  )

  return { navigateToJobAfterCreate }
}
```

#### Rota Vue/Nuxt: `pages/vagas/[id].vue`
```
pages/vagas/[id].vue
  → recebe query param ?tab=configuracoes
  → lê localStorage.getItem('jobCreationMode')
  → se match: activeTab = 'configuracoes', isCreationMode = true
  → localStorage.removeItem('jobCreationMode')
```


---

### CARD VGM-004: Tab Configurações da Vaga (Edição Completa)
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Tab Configurações da Vaga — Edição Completa por Seções"
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 21/Mar
Término: 31/Mar
Data Inicio Jira: 2026-03-21
Data Termino Jira: 2026-03-31
Pontos: 8
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-003

Descricao: |
  Tab "Configurações" dentro da view da vaga. Interface com navegação
  lateral por seções e formulário à direita. Em modo criação
  (isCreationMode: true), exibe banner de rascunho e botão "Publicar Vaga".
  Cada seção pode ser salva individualmente via PATCH na API.

Historia de Usuario: |
  Como recrutador, quero configurar todos os detalhes da vaga em uma
  interface organizada por seções, com salvamento individual por seção,
  para ter controle granular sobre o que foi preenchido.

Regras de Negocio:
  1. Cada seção tem botão "Salvar" individual — salva apenas os campos daquela seção via PUT /api/v1/job-vacancies/{id}
  2. Em modo criação (isCreationMode: true): banner âmbar "Vaga em rascunho" + botão "Publicar Vaga" fixo no topo
  3. Indicador visual de completude por seção (ícone check quando seção tem dados preenchidos)
  4. Mapeamento FE→BE obrigatório para todos os campos (camelCase → snake_case)
  5. interviewStages tem atualização especial: após salvar, recalcula o kanban dinâmico
  6. Campos de vaga afirmativa: isAffirmative toggle → exibe sub-campos condicionais
  7. Visibilidade is_confidential: true → exibe campo masked_company_name
  8. saving_section state: enquanto salva uma seção, botão mostra spinner "Salvando..."
  9. Após salvar com sucesso: toast "Seção salva com sucesso"

Requisitos Tecnicos:
  Frontend:
    - Componente JobConfigTab.vue com navegação lateral
    - Composable useJobConfig.ts com saveSection e buildPayload
    - Mapeamento completo camelCase→snake_case
    - salary_range e bonus_range construídos como objetos { min, max, currency }
    - isCreationMode prop controla visibilidade do banner e botão publicar
  Backend:
    - PUT /api/v1/job-vacancies/{vacancy_id} (já implementado)
    - Aceita qualquer subset dos campos JobVacancyCreate
    - Retorna JobVacancyResponse completo
  Dados:
    - Tabela job_vacancies com todos os campos das seções (ver schema abaixo)
  Validacoes:
    - Campos de data: formato ISO 8601
    - salary_range e bonus_range: min <= max
    - isAffirmative: true requer affirmativeCriteriaPrimary preenchido

Design & Componentes:
  Componentes Existentes:
    - v-navigation-drawer (Vuetify) — nav lateral
    - v-list / v-list-item — itens de seção
    - v-text-field, v-select, v-textarea, v-switch — campos
    - v-btn — salvar por seção
  Novos Componentes:
    - JobConfigTab.vue — componente principal da tab
    - SectionInfoGeral.vue — seção Informações Gerais
    - SectionPessoas.vue — seção Pessoas
    - SectionCompetencias.vue — seção Competências e Requisitos
    - SectionRemuneracao.vue — seção Remuneração
    - SectionPipeline.vue — seção Pipeline de Entrevistas
    - SectionTriagem.vue — seção Triagem WSI
    - SectionAvancadas.vue — seção Configurações Avançadas
  Design Tokens:
    Nav lateral: bg-white, border-r border-gray-200, width 220px
    Seção ativa: border border-gray-900 (borda preta)
    Check completude: mdi-check-circle, color success, size 14
    Banner criação: bg-amber-50, border-amber-200, ícone Info âmbar
    Botão Publicar: bg-gray-900, text-white, rounded-md
    Botão Salvar seção: bg-gray-900, text-white, rounded-md
  Layout:
    Duas colunas: nav lateral 220px fixo + área de conteúdo flex
    Nav lateral flat, sem sombra
    Conteúdo: padding 24px, max-width 720px
  Estados:
    - Default: formulário editável
    - saving_section: botão com spinner "Salvando..."
    - isCreationMode=true: banner âmbar visível, botão Publicar visível
    - isCreationMode=false: sem banner, sem botão Publicar
  Acessibilidade:
    - aria-current="true" no item de seção ativa
    - Labels descritivos em todos os campos
    - Mensagens de erro anunciadas para screen readers

Comportamento de UI:
  Fluxo Principal:
    1. Usuário chega na tab Configurações (via VGM-003 ou navegação manual)
    2. Nav lateral exibe 7 seções com ícone de check nas completas
    3. Seção ativa exibe formulário à direita
    4. Usuário preenche campos e clica "Salvar" da seção
    5. Spinner no botão durante requisição
    6. Toast de sucesso ou erro
    7. Se isCreationMode: botão "Publicar Vaga" no banner do topo
  Estados de Botoes:
    Salvar (por seção):
      - Default: bg-gray-900, text-white
      - Loading: spinner + "Salvando..."
      - Disabled: durante saving_section de qualquer seção
    Publicar Vaga (banner):
      - Default: bg-gray-900, text-white, ícone send
      - Loading: spinner + "Publicando..."
  Validacoes Inline:
    salary_range: min > max → "Salário mínimo deve ser menor que o máximo"
    email campos: formato email válido
    campos de data: formato válido
  Mensagens de Feedback:
    - Sucesso: "Seção salva com sucesso"
    - Erro: "Erro ao salvar. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Cada seção tem botão Salvar funcional
  - [ ] Mapeamento camelCase→snake_case correto em todos os campos
  - [ ] salary_range construído corretamente ao salvar Remuneração
  - [ ] isCreationMode: banner âmbar + botão Publicar visíveis
  - [ ] !isCreationMode: banner e botão ocultos
  - [ ] Salvar → toast de sucesso
  - [ ] Erro ao salvar → toast de erro, dados mantidos no form
  - [ ] Check de completude: aparece quando seção tem dados
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] 7 seções navegáveis na lateral
  - [ ] Seção ativa destacada com borda preta
  - [ ] Check verde em seções com dados preenchidos
  - [ ] PUT API chamado apenas com campos da seção em questão
  - [ ] Banner de criação visível apenas em modo criação
  - [ ] isAffirmative toggle exibe campos condicionais

Arquivos de Referencia (Prototipo):
  - JobEditTab.tsx SECTIONS: plataforma-lia/src/components/jobs/JobEditTab.tsx (linhas 65-100)
  - JobEditTab.tsx isCreationMode banner: plataforma-lia/src/components/jobs/JobEditTab.tsx (linhas 316-342)
  - job-kanban-page.tsx handleSaveJobSection: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 3102-3170)
  - job-kanban-page.tsx fieldMapping: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 3106-3130)
  - job-kanban-page.tsx init form: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 1676-1730)
  - job_vacancies.py PUT endpoint: lia-agent-system/app/api/v1/job_vacancies.py (~linha 2100)
```

### Implementação Vue/Nuxt

#### Composable principal: `composables/useJobConfig.ts`
```typescript
export function useJobConfig(jobId: string) {
  const form = reactive<JobEditForm>({})
  const savingSection = ref<string | null>(null)

  async function saveSection(sectionId: string, fields: string[]) {
    savingSection.value = sectionId
    try {
      const payload = buildPayload(fields, form)
      await jobsApi.update(jobId, payload)
    } finally {
      savingSection.value = null
    }
  }

  function buildPayload(fields: string[], form: JobEditForm) {
    const mapping: Record<string, string> = {
      workModel: 'work_model',
      type: 'employment_type',
      level: 'seniority_level',
      manager: 'hiring_manager',
      managerEmail: 'hiring_manager_email',
      urgencyLevel: 'urgency_level',
      recruiterEmail: 'recruiter_email',
    }
    const payload: Record<string, any> = {}
    fields.forEach(f => {
      if (f === 'salaryMin' || f === 'salaryMax') {
        payload['salary_range'] = { min: form.salaryMin, max: form.salaryMax, currency: 'BRL' }
        return
      }
      if (f === 'bonusMin' || f === 'bonusMax') {
        payload['bonus_range'] = { min: form.bonusMin, max: form.bonusMax, currency: 'BRL' }
        return
      }
      payload[mapping[f] || f] = (form as any)[f]
    })
    return payload
  }

  return { form, savingSection, saveSection }
}
```

#### Navegação lateral (Vuetify):
```vue
<v-navigation-drawer permanent width="220">
  <v-list nav>
    <v-list-item v-for="section in SECTIONS" :key="section.id"
      :value="section.id" @click="activeSection = section.id"
      :active="activeSection === section.id">
      <template #prepend>
        <v-icon :icon="section.icon" size="16" />
      </template>
      <v-list-item-title>{{ section.title }}</v-list-item-title>
      <template #append>
        <v-icon v-if="isSectionComplete(section)" icon="mdi-check-circle"
          color="success" size="14" />
      </template>
    </v-list-item>
  </v-list>
</v-navigation-drawer>
```

### Banco de Dados

Campos adicionais na tabela `job_vacancies`:
```sql
seniority_level               VARCHAR(50)
description                   TEXT
requirements                  JSONB DEFAULT '[]'
technical_requirements        JSONB DEFAULT '[]'
behavioral_competencies       JSONB DEFAULT '[]'
languages                     JSONB DEFAULT '[]'
salary_range                  JSONB            -- { min, max, currency }
bonus_range                   JSONB            -- { min, max, currency }
benefits                      JSONB DEFAULT '[]'
interview_stages              JSONB DEFAULT '[]'
screening_questions           JSONB DEFAULT '[]'
eligibility_questions         JSONB DEFAULT '[]'
visibility                    VARCHAR(30) DEFAULT 'public'
is_confidential               BOOLEAN DEFAULT false
masked_company_name           VARCHAR(255)
is_affirmative                BOOLEAN DEFAULT false
affirmative_criteria_primary  VARCHAR(100)
affirmative_criteria_secondary VARCHAR(100)
affirmative_description       TEXT
affirmative_document_required BOOLEAN DEFAULT false
affirmative_document_types    JSONB DEFAULT '[]'
urgency_level                 INTEGER DEFAULT 3
priority                      VARCHAR(20) DEFAULT 'média'
open_date                     DATE
deadline                      DATE
deadline_screening            DATE
deadline_shortlist            DATE
deadline_closing              DATE
published_linkedin            BOOLEAN DEFAULT false
published_website             BOOLEAN DEFAULT false
published_indeed              BOOLEAN DEFAULT false
target_audience               TEXT
target_sector                 VARCHAR(100)
target_segment                VARCHAR(100)
exclude_from_sync             BOOLEAN DEFAULT false
```


---

### CARD VGM-005: Publicação da Vaga — Auto-save + Link + Status Ativa
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Publicação da Vaga: Auto-save + Geração de Link + Status Ativa"
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-004

Descricao: |
  Ação de publicação da vaga. Executa 3 operações sequenciais:
  (1) auto-save de todos os campos preenchidos no formulário,
  (2) geração do link público de candidatura,
  (3) atualização do status para "Ativa".
  Exibe modal de sucesso com o link copiável. Ao fechar o modal,
  permanece na view da vaga sem redirecionamento.

Historia de Usuario: |
  Como recrutador, quero publicar a vaga clicando em "Publicar Vaga",
  tendo certeza de que todos os dados do formulário serão salvos antes
  da publicação, e receber um link público de candidatura para compartilhar.

Regras de Negocio:
  1. Auto-save obrigatório antes de publicar — todos os campos preenchidos no jobEditForm são enviados antes da publicação
  2. O auto-save usa o mesmo mapeamento de campos de VGM-004 (camelCase→snake_case)
  3. Campos vazios ('', null, undefined) NÃO são incluídos no payload do auto-save
  4. salary_range e bonus_range construídos apenas se salaryMin ou salaryMax estão preenchidos
  5. Após auto-save → generatePublicLink(vacancyId) → retorna { public_url: string }
  6. Após gerar link → updateJobVacancy(vacancyId, { status: "Ativa" })
  7. Modal de sucesso exibe o link copiável, botão de copiar para clipboard
  8. Fechar modal de sucesso → apenas fecha o modal. NÃO redireciona. NÃO recarrega.
  9. Após publicação: banner de rascunho desaparece (isCreationMode: false)
  10. Status no header atualiza para "Ativa" imediatamente (estado local, sem re-fetch)
  11. Botão "Publicar Vaga" fica desabilitado durante loading com spinner "Publicando..."
  12. Em caso de erro em qualquer etapa → toast de erro, vaga permanece em rascunho

Requisitos Tecnicos:
  Frontend:
    - Composable useJobPublish.ts com função publish() sequencial
    - buildAutoSavePayload() filtra campos vazios e mapeia nomes
    - Dialog de sucesso com link copiável (clipboard API)
    - Estado isPublishing para desabilitar botão
    - Emit success para atualizar isCreationMode e status local
  Backend:
    - PUT /api/v1/job-vacancies/{id} (já implementado)
    - POST /api/v1/job-vacancies/{id}/generate-public-link
    - Retorna { public_url: "https://..." }
  Dados:
    - Colunas public_url, slug, published_at na tabela job_vacancies
  Validacoes:
    - Título obrigatório para publicar (validação no backend)
    - Status só muda para "Ativa" após geração bem-sucedida do link

Design & Componentes:
  Componentes Existentes:
    - v-dialog — dialog de sucesso
    - v-text-field readonly — exibe link
    - v-btn — copiar, fechar
  Novos Componentes:
    - PublishSuccessDialog.vue — dialog com link copiável
  Design Tokens:
    Botão Publicar: bg-gray-900, text-white, rounded-md, ícone mdi-send
    Loading: spinner mdi-loading + "Publicando..."
    Dialog: max-width 400px
    Link field: readonly, append-inner-icon mdi-content-copy
  Layout:
    Dialog centralizado, max-width 400px
    Input do link: largura total, readonly
    Ações: botão Fechar à direita
  Estados:
    - Default: botão Publicar ativo
    - isPublishing: spinner + "Publicando...", botão disabled
    - Sucesso: dialog abre com link
    - Erro: toast vermelho, dialog não abre
  Acessibilidade:
    - aria-label no botão copiar link
    - Dialog com foco gerenciado

Comportamento de UI:
  Fluxo Principal:
    1. Usuário clica "Publicar Vaga" no banner de rascunho
    2. Botão muda para "Publicando..." + spinner
    3. Auto-save de todos os campos preenchidos
    4. POST para gerar link público
    5. PUT para mudar status para "Ativa"
    6. Dialog de sucesso abre com link copiável
    7. Usuário copia link e fecha dialog
    8. Banner de rascunho desaparece
    9. Badge de status muda para "Ativa" (verde)
  Estados de Botoes:
    Publicar Vaga:
      - Default: bg-gray-900, text-white, ícone mdi-send
      - Loading: spinner mdi-loading + "Publicando..."
      - Disabled: durante isPublishing
    Copiar link:
      - Default: ícone mdi-content-copy
      - Sucesso: ícone mdi-check por 2s
  Validacoes Inline:
    Nenhuma — validação ocorre no backend
  Mensagens de Feedback:
    - Copiar link: toast "Link copiado!"
    - Erro de publicação: toast "Erro ao publicar a vaga. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Clicar "Publicar" → auto-save roda antes de gerar link
  - [ ] Auto-save não inclui campos vazios no payload
  - [ ] salary_range construído corretamente se salaryMin/Max preenchidos
  - [ ] Link gerado aparece no dialog copiável
  - [ ] Botão copiar → clipboard.writeText + toast "Link copiado!"
  - [ ] Fechar dialog → permanece na view da vaga
  - [ ] isCreationMode → false após publicação
  - [ ] Status do header → "Ativa"
  - [ ] Falha na API → toast de erro, vaga não muda de status

Criterios de Aceitacao:
  - [ ] 3 chamadas API na ordem correta: PUT save → POST link → PUT status
  - [ ] Campos vazios excluídos do payload de auto-save
  - [ ] public_url retornado e exibido no dialog
  - [ ] Clipboard API chamada ao clicar copiar
  - [ ] Banner âmbar desaparece após publicação bem-sucedida

Arquivos de Referencia (Prototipo):
  - job-kanban-page.tsx handlePublishJob: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 442-514)
  - JobEditTab.tsx botão publicar: plataforma-lia/src/components/jobs/JobEditTab.tsx (linhas 324-341)
  - job-kanban-page.tsx dialog sucesso: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 9972-10010)
  - lia-api.ts generatePublicLink: plataforma-lia/src/services/lia-api.ts (linha 974)
```

### Implementação Vue/Nuxt

#### Composable: `composables/useJobPublish.ts`
```typescript
export function useJobPublish(jobId: string, form: JobEditForm) {
  const isPublishing = ref(false)
  const publicLink = ref<string | null>(null)
  const showSuccessDialog = ref(false)

  async function publish() {
    isPublishing.value = true
    try {
      const payload = buildAutoSavePayload(form)
      if (Object.keys(payload).length > 0) {
        await jobsApi.update(jobId, payload)
      }
      const { public_url } = await jobsApi.generatePublicLink(jobId)
      await jobsApi.update(jobId, { status: 'Ativa' })
      publicLink.value = public_url
      showSuccessDialog.value = true
    } catch (e) {
      useToast().error('Erro ao publicar a vaga')
    } finally {
      isPublishing.value = false
    }
  }

  return { publish, isPublishing, publicLink, showSuccessDialog }
}
```

#### Payload de Auto-save (campos mapeados):
```typescript
const fieldMapping = {
  title: 'title', department: 'department', location: 'location',
  workModel: 'work_model', type: 'employment_type', level: 'seniority_level',
  urgencyLevel: 'urgency_level', priority: 'priority',
  recruiter: 'recruiter', recruiterEmail: 'recruiter_email',
  manager: 'hiring_manager', managerEmail: 'hiring_manager_email',
  openDate: 'open_date', deadline: 'deadline',
  deadlineScreening: 'deadline_screening',
  deadlineShortlist: 'deadline_shortlist',
  deadlineClosing: 'deadline_closing',
  benefits: 'benefits', description: 'description',
  targetAudience: 'target_audience', targetSector: 'target_sector',
  visibility: 'visibility', isConfidential: 'is_confidential',
  isAffirmative: 'is_affirmative', languages: 'languages',
}
// salary_range: { min, max, currency: 'BRL' } se salaryMin ou salaryMax preenchidos
// bonus_range: { min, max, currency: 'BRL' } se bonusMin ou bonusMax preenchidos
```

#### Dialog de sucesso (Vuetify):
```vue
<v-dialog v-model="showSuccessDialog" max-width="400" persistent>
  <v-card rounded="lg">
    <v-card-title>Vaga Publicada!</v-card-title>
    <v-card-text>
      <p>A vaga está ativa. Compartilhe o link:</p>
      <v-text-field :model-value="publicLink" readonly
        append-inner-icon="mdi-content-copy"
        @click:append-inner="copyLink" />
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn color="surface-variant" variant="flat"
        @click="showSuccessDialog = false">Fechar</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```


---

### CARD VGM-006: Header da Vaga — Badge Status + Popover de Ações
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FRONTEND] Header da Vaga: Badge de Status Clicável + Popover de Ações"
Tipo: Feature
Area: Frontend
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 3
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-005

Descricao: |
  Header fixo da view de vaga exibe título, ID interno (WDT-XXXXXXXX),
  badge de status clicável com popover de ações contextuais. As ações
  disponíveis variam conforme o status atual da vaga.

Historia de Usuario: |
  Como recrutador, quero ver o status atual da vaga no cabeçalho e ter
  acesso rápido às ações de mudança de status (pausar, reativar, fechar),
  para gerenciar o ciclo de vida da vaga sem navegar por menus.

Regras de Negocio:
  1. Badge de status é um <button> que abre Popover ao clicar
  2. Status "Ativa" ou "active": mostra Pausar + Fechar
  3. Status "Pausada", "Paused": mostra Reativar + Fechar
  4. Status "Encerrada": badge NÃO abre popover
  5. "Pausar vaga" → abre JobStatusModal com mode 'pause' (VGM-008)
  6. "Reativar vaga" → abre JobStatusModal com mode 'activate' (VGM-008)
  7. "Fechar vaga" → abre CloseVacancyModal (VGM-009)
  8. O badge exibe o valor de jobEditForm.status || currentJob.status (estado local tem prioridade)
  9. Badge ID: WDT-{primeiros 8 chars do UUID em maiúsculas} — ex: WDT-A1B2C3D4

Requisitos Tecnicos:
  Frontend:
    - Componente JobHeader.vue com props job, currentStatus, screeningStatus
    - Emits: pause, reactivate, close-vacancy, screening-action
    - Computed isActive e canChangeStatus
    - v-menu do Vuetify para o popover
    - ID interno formatado: WDT-{uuid.slice(0,8).toUpperCase()}
  Backend:
    - Nenhum endpoint novo neste card
  Dados:
    - Nenhuma tabela nova
  Validacoes:
    - Status "Encerrada" → sem ação de popover

Design & Componentes:
  Componentes Existentes:
    - v-menu (Vuetify) — popover de ações
    - v-chip — badge de status
    - v-list / v-list-item — itens do popover
  Novos Componentes:
    - JobHeader.vue — header completo da view de vaga
  Design Tokens:
    Header: height 56px, border-bottom 1px solid, bg-white
    Badge status: bg-[#DCE4DB], text-gray-800, border-gray-200, text-xs
    Hover badge: bg-[#c9d6c8], cursor-pointer
    Popover: min-width 176px, border-radius 8px, sem sombra (borda)
    Item Fechar: color red-600, ícone mdi-archive
    Item Pausar: ícone mdi-pause-circle, color warning (âmbar)
    Item Reativar: ícone mdi-play-circle, color success (verde)
  Layout:
    Header horizontal: título + código + badge status + badge triagem
    Altura fixa 56px
    Sticky top-0
  Estados:
    - Status Ativa: badge verde-acinzentado, popover com Pausar + Fechar
    - Status Pausada: badge âmbar, popover com Reativar + Fechar
    - Status Encerrada: badge cinza, sem popover
    - Status Rascunho: badge cinza, sem popover de ações
  Acessibilidade:
    - aria-haspopup="true" no badge clicável
    - aria-expanded no estado de menu aberto
    - Role menuitem nos itens do popover

Comportamento de UI:
  Fluxo Principal:
    1. Header exibe título da vaga + ID interno (WDT-XXXXXXXX)
    2. Badge de status à direita do ID
    3. Clicar no badge (se permitido) abre popover
    4. Ações contextuais baseadas no status atual
    5. Clicar em ação → emite evento correto para o pai
    6. Pai abre modal correspondente (VGM-008 ou VGM-009)
  Estados de Botoes:
    Badge status:
      - Clicável: cursor-pointer, hover escurece
      - Não clicável (Encerrada): cursor-default, sem hover
  Validacoes Inline:
    Nenhuma
  Mensagens de Feedback:
    Nenhuma diretamente no header

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Status "Ativa" → popover mostra Pausar + Fechar
  - [ ] Status "Pausada" → popover mostra Reativar + Fechar
  - [ ] Status "Encerrada" → badge sem popover
  - [ ] Clicar "Pausar" → emite evento pause
  - [ ] Clicar "Reativar" → emite evento reactivate
  - [ ] Clicar "Fechar vaga" → emite evento close-vacancy
  - [ ] ID interno renderizado no formato WDT-XXXXXXXX
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] Badge reflete status local (sem re-fetch para mudanças otimistas)
  - [ ] Popover fecha ao clicar em ação
  - [ ] ID formatado como WDT- + 8 chars UUID maiúsculos
  - [ ] Eventos emitidos corretamente para os modais

Arquivos de Referencia (Prototipo):
  - job-kanban-page.tsx header completo: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 4940-5090)
  - job-kanban-page.tsx badge status: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 4951-4993)
  - job-kanban-page.tsx estados modal: plataforma-lia/src/components/pages/job-kanban-page.tsx (showJobStatusModal, jobStatusModalMode, showCloseVacancyModal)
```

### Implementação Vue/Nuxt

#### Componente: `components/jobs/JobHeader.vue`

**Props e Emits:**
```typescript
interface Props {
  job: Job
  currentStatus: string
  screeningStatus: string
}
interface Emits {
  (e: 'pause'): void
  (e: 'reactivate'): void
  (e: 'close-vacancy'): void
  (e: 'screening-action', action: string): void
}
```

**Computeds:**
```typescript
const isActive = computed(() =>
  ['Ativa', 'active'].includes(props.currentStatus)
)
const canChangeStatus = computed(() =>
  !['Encerrada', 'closed'].includes(props.currentStatus)
)
const jobInternalId = computed(() =>
  `WDT-${props.job.id.slice(0, 8).toUpperCase()}`
)
```


---

### CARD VGM-007: Badge de Triagem no Header + Controle de Status
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Badge de Triagem WSI no Header + Controle de Status"
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 21/Mar
Término: 31/Mar
Data Inicio Jira: 2026-03-21
Data Termino Jira: 2026-03-31
Pontos: 3
Prioridade: Média
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-006

Descricao: |
  Badge de triagem ao lado do badge de status da vaga no header.
  Indica o estado atual do processo de triagem WSI/LIA. Clicável com
  popover de ações contextuais para iniciar, pausar ou retomar triagem.

Historia de Usuario: |
  Como recrutador, quero ver o status da triagem WSI no cabeçalho da
  vaga e poder iniciar, pausar ou retomar a triagem rapidamente sem
  sair da view.

Regras de Negocio:
  1. Status completed → badge fixo sem ação (Popover não abre)
  2. Ação "Configurar Triagem" → navega para a sub-seção de triagem na tab Configurações
  3. Ações de status → chamam PUT /api/v1/job-vacancies/{id} com { screening_status: newStatus }
  4. Update otimista: estado local atualiza imediatamente, reverter em caso de erro
  5. Toast de confirmação após mudança de status
  6. A triagem só pode ser iniciada se a vaga estiver com status "Ativa" (validação FE + BE)
  7. O campo screening_status é separado do status da vaga

Requisitos Tecnicos:
  Frontend:
    - Componente ScreeningBadge.vue com prop status e vacancyStatus
    - Emits configure e change-status
    - Update otimista com rollback em caso de erro
    - v-menu para popover de ações
  Backend:
    - PATCH /api/v1/job-vacancies/{id} com { screening_status: newStatus }
    - Validação: triagem só pode iniciar se vaga Ativa
  Dados:
    - Coluna screening_status VARCHAR(20) na tabela job_vacancies
  Validacoes:
    - Iniciar triagem requer status da vaga = "Ativa"
    - screening_status enum: not_configured | not_started | active | paused | completed

Design & Componentes:
  Componentes Existentes:
    - v-chip — badge visual
    - v-menu / v-list — popover de ações
  Novos Componentes:
    - ScreeningBadge.vue — badge de triagem com popover
  Design Tokens:
    not_configured: bg-gray-100, text-gray-700, border-gray-300
    not_started: bg-amber-50, text-amber-800, border-amber-300
    active: bg-emerald-50, text-emerald-800, border-emerald-300
    paused: bg-orange-50, text-orange-800, border-orange-300
    completed: bg-sky-50, text-sky-800, border-sky-300
  Layout:
    Posicionado à direita do badge de status no header
    Mesmo tamanho e estilo geral dos badges
  Estados:
    - not_configured: popover com ação "Configurar"
    - not_started: popover com "Iniciar Triagem" e "Configurar"
    - active: popover com "Pausar Triagem"
    - paused: popover com "Retomar" e "Configurar"
    - completed: badge sem popover
  Acessibilidade:
    - aria-label descritivo no badge
    - Itens do popover com role menuitem

Comportamento de UI:
  Fluxo Principal:
    1. Badge exibe status da triagem com cor contextual
    2. Clicar no badge (se não completed) abre popover
    3. Ações contextuais conforme status atual
    4. Clicar em ação → update otimista + chamada API
    5. Sucesso: toast de confirmação
    6. Erro: rollback do estado otimista + toast de erro
  Estados de Botoes:
    Badge triagem:
      - Clicável (non-completed): cursor-pointer
      - Completed: cursor-default
  Validacoes Inline:
    Tentativa de iniciar triagem com vaga pausada → toast de aviso
  Mensagens de Feedback:
    - Sucesso: "Status da triagem atualizado"
    - Erro: "Erro ao atualizar triagem. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Status completed → badge sem popover
  - [ ] Status not_configured → ação "Configurar" disponível
  - [ ] Status active → ação "Pausar" disponível
  - [ ] Status paused → ações "Retomar" e "Configurar" disponíveis
  - [ ] Mudança de status → PATCH API + toast de confirmação
  - [ ] Erro → rollback do estado otimista + toast de erro
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] 5 estados visuais distintos com cores corretas
  - [ ] Update otimista: badge muda antes da resposta da API
  - [ ] Rollback: badge retorna ao estado anterior em caso de erro
  - [ ] Triagem não pode iniciar com vaga pausada ou encerrada

Arquivos de Referencia (Prototipo):
  - job-kanban-page.tsx badge triagem: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 4995-5088)
  - job-kanban-page.tsx handleScreeningStatusChange: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 5011-5019)
```


---

### CARD VGM-008: Modal Pausar / Reativar Vaga
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Modal Pausar / Reativar Vaga com Notificação de Candidatos"
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 21/Mar
Término: 31/Mar
Data Inicio Jira: 2026-03-21
Data Termino Jira: 2026-03-31
Pontos: 5
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-006

Descricao: |
  Modal multi-step acionado pelo popover de status (VGM-006). Suporta
  dois modos: pause (pausar) e activate (reativar). No modo pause permite
  informar motivo, notificar candidatos ativos via email/WhatsApp e
  cancelar entrevistas agendadas.

Historia de Usuario: |
  Como recrutador, quero pausar uma vaga ativa informando o motivo e
  opcionalmente notificando candidatos em processo, ou reativar uma
  vaga pausada, para gerenciar o fluxo sem perder histórico.

Regras de Negocio:
  1. Motivo da pausa: texto livre opcional
  2. Toggle "Notificar candidatos em processo" (default: false)
  3. Se notificar: selecionar canal (email / WhatsApp / ambos), selecionar template, selecionar candidatos
  4. Entrevistas agendadas: opção "Cancelar entrevistas agendadas" (toggle)
  5. Ao confirmar pausar: PUT /api/v1/job-vacancies/{id} com { status: "Pausada", pause_reason: "..." }
  6. Se notificar candidatos: disparar notificações separadamente (VGM-010)
  7. Status local atualiza imediatamente para "Pausada"
  8. Ao reativar: PUT /api/v1/job-vacancies/{id} com { status: "Ativa" }
  9. Opcional no reativar: notificar candidatos que vaga voltou
  10. Status local atualiza para "Ativa"

Requisitos Tecnicos:
  Frontend:
    - Componente JobStatusModal.vue com prop mode: 'pause' | 'activate'
    - Composable useJobStatus.ts com pause() e reactivate()
    - Lista de candidatos ativos passada como prop
    - Template selector com preview da mensagem
  Backend:
    - PUT /api/v1/job-vacancies/{id} (já implementado)
    - POST /api/v1/job-vacancies/{id}/notify-candidates (novo)
  Dados:
    - Colunas pause_reason TEXT, paused_at TIMESTAMP, reactivated_at TIMESTAMP na tabela job_vacancies
  Validacoes:
    - Canal de notificação obrigatório se toggle notificar ativo
    - Pelo menos 1 candidato selecionado se toggle notificar ativo

Design & Componentes:
  Componentes Existentes:
    - v-dialog — container do modal
    - v-switch — toggles
    - v-select — canal de notificação, template
    - v-checkbox — seleção de candidatos
    - v-textarea — motivo da pausa
  Novos Componentes:
    - JobStatusModal.vue — modal de pausa/reativação
  Design Tokens:
    Modal: max-width 560px
    Seção notificação: bg-gray-50 border border-gray-200 rounded-md, padding 16px
    Candidato item: flex row com checkbox, avatar inicial, nome, stage
    Botão confirmar Pausar: bg-amber-600, text-white
    Botão confirmar Reativar: bg-green-700, text-white
  Layout:
    Formulário vertical no modo pause
    Seção de notificação aparece condicionalmente quando toggle ativo
    Lista de candidatos scrollável (max-height 200px)
  Estados:
    - mode=pause: formulário com motivo + toggle notificar + toggle cancelar entrevistas
    - mode=activate: confirmação simples + toggle notificar opcionalmente
    - notifyApplicants=true: campos adicionais visíveis
  Acessibilidade:
    - aria-expanded no toggle de notificação
    - Lista de candidatos com role listbox

Comportamento de UI:
  Fluxo Principal (pause):
    1. Modal abre no modo pause
    2. Campo de motivo (opcional)
    3. Toggle "Notificar candidatos"
    4. Se ON: canal + template + lista de candidatos com checkboxes
    5. Toggle "Cancelar entrevistas agendadas" (opcional)
    6. Confirmar → PUT API + notificações + status local
  Fluxo Principal (activate):
    1. Modal abre no modo activate
    2. Confirmação simples da reativação
    3. Toggle opcional para notificar candidatos
    4. Confirmar → PUT API + status local
  Estados de Botoes:
    Confirmar Pausar:
      - bg-amber-600, text-white
      - Loading: "Pausando..."
    Confirmar Reativar:
      - bg-green-700, text-white
      - Loading: "Reativando..."
    Cancelar:
      - variant text
  Validacoes Inline:
    Toggle notificar ON sem candidatos selecionados → aviso
  Mensagens de Feedback:
    - Pausar: toast "Vaga pausada com sucesso"
    - Reativar: toast "Vaga reativada com sucesso"
    - Erro: toast de erro com mensagem

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Modo pause: form com motivo + opção notificação + opção cancelar entrevistas
  - [ ] Toggle notificar OFF: sem campos de notificação
  - [ ] Toggle notificar ON: campos de canal + template + candidatos visíveis
  - [ ] Confirmar pause → PUT API + status local = "Pausada"
  - [ ] Modo activate → PUT API + status local = "Ativa"
  - [ ] Fechar modal sem confirmar → nenhuma mudança
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] Status da vaga atualizado localmente sem re-fetch
  - [ ] pause_reason salvo no banco quando informado
  - [ ] Candidatos notificados apenas quando toggle ativo e candidatos selecionados
  - [ ] Entrevistas canceladas quando toggle ativo (integração futura)

Arquivos de Referencia (Prototipo):
  - job-status-modal.tsx: plataforma-lia/src/components/modals/job-status-modal.tsx (arquivo completo)
  - job-status-modal.tsx PauseData interface: plataforma-lia/src/components/modals/job-status-modal.tsx (linhas 52-65)
  - job-kanban-page.tsx uso modal: plataforma-lia/src/components/pages/job-kanban-page.tsx (showJobStatusModal, jobStatusModalMode)
```

### Implementação Vue/Nuxt

#### Composable: `composables/useJobStatus.ts`
```typescript
export function useJobStatus(jobId: string) {
  async function pause(data: PauseData) {
    await jobsApi.update(jobId, { status: 'Pausada', pause_reason: data.reason })
    if (data.notifyApplicants && data.candidateIds?.length) {
      await jobsApi.notifyCandidates(jobId, data)
    }
  }
  async function reactivate() {
    await jobsApi.update(jobId, { status: 'Ativa' })
  }
  return { pause, reactivate }
}
```

### Payload API

```json
PUT /api/v1/job-vacancies/{id}
{
  "status": "Pausada",
  "pause_reason": "Aguardando aprovação de headcount"
}

POST /api/v1/job-vacancies/{id}/notify-candidates
{
  "candidate_ids": ["uuid1", "uuid2"],
  "channel": "email",
  "template_id": "vaga_pausada",
  "message": "..."
}
```

### Banco de Dados

```sql
-- Adicionar à tabela job_vacancies:
pause_reason    TEXT
paused_at       TIMESTAMP
reactivated_at  TIMESTAMP
```


---

### CARD VGM-009: Modal Fechar Vaga com Placement de Candidato
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Modal Fechar Vaga com Registro de Placement"
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 21/Mar
Término: 31/Mar
Data Inicio Jira: 2026-03-21
Data Termino Jira: 2026-03-31
Pontos: 8
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-006

Descricao: |
  Modal multi-step para encerramento definitivo da vaga. Inclui:
  seleção do candidato contratado (placement), configuração da
  notificação para o contratado, e configuração de notificação em
  massa para os demais candidatos.
  ⚠️ GAP ATUAL: o protótipo implementa apenas a UI — o envio real
  das notificações e as chamadas à API precisam ser implementados
  (cobertos por VGM-010).

Historia de Usuario: |
  Como recrutador, quero fechar a vaga registrando o candidato
  contratado (placement), enviar mensagem de parabéns a ele e
  notificar os demais candidatos que a vaga foi encerrada, para
  finalizar o ciclo de forma completa e comunicada.

Regras de Negocio:
  1. O candidato da coluna "hired/Contratado" é pré-selecionado automaticamente no Step 1
  2. O placement é obrigatório para registrar fechamento completo. Se não há contratado, o recrutador pode pular (fechar sem placement)
  3. Ao confirmar: atualiza status da vaga para "Encerrada" + registra hired_candidate_id + closed_at
  4. Notificação do contratado: disparada imediatamente
  5. Notificação dos demais: disparada para os selecionados
  6. O campo hired_candidate_id na vaga registra o placement para relatórios
  7. Após confirmar: status local da vaga = "Encerrada", badge do header atualiza
  8. Badge de status "Encerrada" não abre popover de ações
  9. "⚠️ GAP ATUAL (PROTÓTIPO): o onConfirm no protótipo só atualiza estado local, não chama a API real e não envia notificações. Isso precisa ser implementado no produto."

Requisitos Tecnicos:
  Frontend:
    - Componente CloseVacancyModal.vue com 3 steps
    - Composable useVacancyClosure.ts com closeVacancy()
    - Step indicator com progresso 1-2-3
    - Lista scrollável de candidatos com checkboxes
    - Toggle "Selecionar todos"
    - Preview de mensagem com merge fields
  Backend:
    - PUT /api/v1/job-vacancies/{id} com status Encerrada + hired_candidate_id
    - POST /api/v1/placements — cria registro de placement
    - POST /api/v1/communications/send — notificação contratado
    - POST /api/v1/communications/batch-send — notificações em massa
  Dados:
    - Colunas hired_candidate_id, closed_at, closure_reason, closed_by na tabela job_vacancies
    - Nova tabela placements (ver schema abaixo)
  Validacoes:
    - Canal de notificação obrigatório se notificação ativa
    - Pelo menos 1 candidato selecionado para notificação em massa

Design & Componentes:
  Componentes Existentes:
    - v-dialog — container do modal
    - v-stepper (Vuetify) — step indicator
    - v-list com v-checkbox — lista de candidatos
    - v-select — canal, template
    - v-textarea — preview de mensagem
  Novos Componentes:
    - CloseVacancyModal.vue — modal multi-step de fechamento
  Design Tokens:
    Modal: max-width 640px
    Step indicator: pills numeradas 1-2-3
    Card candidato contratado: avatar inicial, nome, email
    Lista candidatos: scrollável, max-height 240px
    Botão confirmar: bg-gray-900, text-white, ícone mdi-archive
  Layout:
    Modal 640px com step indicator no topo
    Step 1: card do contratado + canal + template
    Step 2: lista com "Selecionar todos" + candidatos + preview
    Step 3: resumo + botão confirmar
  Estados:
    - Step 1: candidato pré-selecionado ou campo de seleção manual
    - Step 2: todos os candidatos ativos (exceto hired/rejected)
    - Step 3: resumo das ações a executar
  Acessibilidade:
    - Step indicator com aria-current
    - Checkbox lista com role listbox
    - Preview de mensagem em aria-live

Comportamento de UI:
  Fluxo Principal:
    1. Modal abre com candidato contratado pré-selecionado (se existir)
    2. Step 1: confirmar contratado + canal de notificação
    3. "Próximo" → Step 2: candidatos para notificar
    4. Selecionar candidatos + template
    5. "Próximo" → Step 3: resumo
    6. "Confirmar Encerramento" → 4 chamadas API em sequência
    7. Modal fecha, status local = "Encerrada"
  Estados de Botoes:
    Próximo:
      - bg-gray-900, text-white
    Confirmar Encerramento:
      - bg-gray-900, text-white, ícone mdi-archive
      - Loading: spinner + "Encerrando..."
    Voltar:
      - variant text
  Validacoes Inline:
    Step 3: sem candidato identificado → aviso, mas permite pular
  Mensagens de Feedback:
    - Sucesso: "Vaga encerrada com sucesso"
    - Erro: "Erro ao encerrar vaga. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Candidato na coluna "hired" pré-selecionado no Step 1
  - [ ] Sem candidato contratado → campo de seleção manual disponível
  - [ ] Step 2: todos os candidatos ativos listados (exceto hired/rejected)
  - [ ] "Selecionar todos" → marca/desmarca todos
  - [ ] Confirmar → PUT API status "Encerrada" + hired_candidate_id
  - [ ] Confirmar → POST placement criado
  - [ ] Confirmar → notificações disparadas (email/WhatsApp)
  - [ ] Fechar sem confirmar → nenhuma mudança
  - [ ] Badge de status → "Encerrada" após confirmação
  - [ ] Badge "Encerrada" → sem popover de ações

Criterios de Aceitacao:
  - [ ] 3 steps com indicador de progresso
  - [ ] PUT API com status=Encerrada + hired_candidate_id + closed_at
  - [ ] Placement registrado na tabela placements
  - [ ] Notificações disparadas (VGM-010) após confirmação
  - [ ] Status local atualizado sem re-fetch

Arquivos de Referencia (Prototipo):
  - close-vacancy-modal.tsx: plataforma-lia/src/components/modals/close-vacancy-modal.tsx (arquivo completo)
  - close-vacancy-modal.tsx CloseVacancyPayload: plataforma-lia/src/components/modals/close-vacancy-modal.tsx (linhas 44-61)
  - job-kanban-page.tsx uso modal: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 9935-9970)
  - job-kanban-page.tsx GAP onConfirm: plataforma-lia/src/components/pages/job-kanban-page.tsx (linha 9963)
```

### Implementação Vue/Nuxt

#### Composable: `composables/useVacancyClosure.ts`
```typescript
export function useVacancyClosure(vacancyId: string) {
  async function closeVacancy(payload: ClosurePayload) {
    await jobsApi.update(vacancyId, {
      status: 'Encerrada',
      hired_candidate_id: payload.hiredCandidateId,
      closed_at: new Date().toISOString(),
      closure_reason: 'filled'
    })
    if (payload.hiredCandidateId) {
      await placementsApi.create({
        job_vacancy_id: vacancyId,
        candidate_id: payload.hiredCandidateId
      })
    }
    if (payload.hiredNotification?.channel) {
      await communicationsApi.send({
        recipient_id: payload.hiredCandidateId,
        ...payload.hiredNotification
      })
    }
    if (payload.otherNotifications?.candidateIds?.length) {
      await communicationsApi.batchSend(payload.otherNotifications)
    }
  }
  return { closeVacancy }
}
```

### Payload API

```json
PUT /api/v1/job-vacancies/{id}
{
  "status": "Encerrada",
  "hired_candidate_id": "uuid-candidato",
  "closed_at": "2026-03-10T...",
  "closure_reason": "filled"
}

POST /api/v1/communications/send
{
  "recipient_type": "candidate",
  "recipient_id": "uuid-candidato",
  "channel": "email",
  "template_id": "proposta_aceita",
  "context": {
    "candidate_name": "João Silva",
    "job_title": "Engenheiro de Software Sênior",
    "company_name": "WeDOTalent"
  }
}

POST /api/v1/communications/batch-send
{
  "recipient_ids": ["uuid1", "uuid2"],
  "channel": "email",
  "template_id": "vaga_encerrada",
  "context": { "job_title": "..." }
}
```

### Banco de Dados

```sql
-- Adicionar à tabela job_vacancies:
hired_candidate_id  UUID REFERENCES candidates(id)
closed_at           TIMESTAMP
closure_reason      VARCHAR(50)  -- 'filled' | 'cancelled' | 'on_hold'
closed_by           UUID REFERENCES users(id)

-- Nova tabela placements:
CREATE TABLE placements (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id       UUID NOT NULL REFERENCES companies(id),
  job_vacancy_id   UUID NOT NULL REFERENCES job_vacancies(id),
  candidate_id     UUID NOT NULL REFERENCES candidates(id),
  placed_at        TIMESTAMP DEFAULT now(),
  placed_by        UUID REFERENCES users(id),
  start_date       DATE,
  salary_agreed    DECIMAL(10,2),
  notes            TEXT,
  created_at       TIMESTAMP DEFAULT now(),
  UNIQUE(job_vacancy_id)
);
```


---

### CARD VGM-010: Envio de Notificações de Fechamento e Placement
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[BACKEND] Endpoints de Notificação de Fechamento e Placement de Candidatos"
Tipo: Feature
Area: Backend
Sprint: 3
Início: 01/Abr
Término: 14/Abr
Data Inicio Jira: 2026-04-01
Data Termino Jira: 2026-04-14
Pontos: 8
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-009

Descricao: |
  ⚠️ Este card implementa o que está faltando no protótipo. O modal de
  fechamento (VGM-009) captura os dados de notificação, mas o envio real
  ainda não foi implementado. Este card cobre os endpoints de envio de
  comunicação, os templates, e a integração com os canais (email via
  Mailgun/Resend, WhatsApp via Meta/Twilio).

Historia de Usuario: |
  Como candidato contratado, quero receber uma mensagem de parabéns
  pela contratação. Como candidato não selecionado, quero receber uma
  comunicação respeitosa informando que a vaga foi encerrada, para ter
  um encerramento digno do processo.

Regras de Negocio:
  1. Envio é assíncrono (não bloqueia a UI) — disparado via fila (RabbitMQ/Celery)
  2. Email via Mailgun (primário) com fallback para Resend/Mailgun
  3. WhatsApp via Meta Business API ou Twilio WhatsApp
  4. Canal "ambos": dispara email E WhatsApp independentemente
  5. Rastreamento: cada envio gera registro em communication_logs
  6. Falha no envio: retry automático 3x com backoff exponencial
  7. LGPD: candidato deve ter dado consentimento para receber mensagens (verificar consent_status)
  8. Rate limiting: máximo 100 emails/minuto por company para envios em massa
  9. Template da mensagem é editável pelo recrutador no modal antes do envio

Requisitos Tecnicos:
  Frontend:
    - Service communicationsApi.ts com send(), batchSend(), getHistory()
    - Composable useCommunicationTemplates.ts com templates por situação
    - Integrado ao modal VGM-009 — sem nova tela
  Backend:
    - POST /api/v1/communications/send
    - POST /api/v1/communications/batch-send
    - GET /api/v1/job-vacancies/{id}/communication-history
    - Celery task send_closure_notifications com retry 3x backoff exponencial
    - Verificação de consent_status antes de enviar
    - Rate limiter 100 emails/min por company
  Dados:
    - Nova tabela communication_logs (ver schema abaixo)
    - Índices em job_vacancy_id, candidate_id, status
  Validacoes:
    - candidate_id obrigatório no send
    - channel enum email|whatsapp|both
    - template_id obrigatório ou custom_message obrigatório
    - Candidato sem email/telefone: ignorar com log
    - Candidato sem consentimento LGPD: ignorar com log

Design & Componentes:
  Componentes Existentes:
    - Integrado ao CloseVacancyModal.vue (VGM-009)
    - Toast para feedback pós-envio
  Novos Componentes:
    - Nenhum componente novo — backend + service layer
  Design Tokens:
    N/A — sem nova UI
  Layout:
    N/A
  Estados:
    - loading durante envio: spinner no botão Confirmar do modal VGM-009
    - Pós-envio: toast com contagem de notificações
  Acessibilidade:
    N/A — sem nova UI

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador confirma fechamento no modal VGM-009
    2. Frontend chama communicationsApi.send() para contratado
    3. Frontend chama communicationsApi.batchSend() para demais
    4. Backend enfileira tasks Celery
    5. Tasks processam e registram em communication_logs
    6. Toast "Notificações enviadas para X candidatos"
  Estados de Botoes:
    Confirmar Encerramento (do modal VGM-009):
      - Loading durante envio: spinner
  Validacoes Inline:
    N/A no frontend
  Mensagens de Feedback:
    - Sucesso: "Notificações enviadas para X candidatos"
    - Erro parcial: "Vaga encerrada, mas algumas notificações falharam"

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Candidato contratado → email/WhatsApp de parabéns disparado
  - [ ] Demais candidatos selecionados → email "vaga encerrada" disparado
  - [ ] Canal "ambos" → email E WhatsApp enviados separadamente
  - [ ] Falha no envio → retry automático 3x com backoff
  - [ ] Candidato sem email/telefone → notificação ignorada com log
  - [ ] LGPD: candidato sem consentimento → não notificado, log registrado
  - [ ] communication_logs registrado para cada tentativa
  - [ ] Rate limiting: >100/min → fila respeita limite

Criterios de Aceitacao:
  - [ ] Envio assíncrono: resposta da API imediata, processamento em background
  - [ ] Celery task com max_retries=3 e backoff exponencial
  - [ ] communication_logs com status pending → sent/failed
  - [ ] GET /communication-history retorna histórico paginado
  - [ ] Merge fields substituídos corretamente nos templates

Arquivos de Referencia (Prototipo):
  - screening-email-templates.ts: plataforma-lia/src/data/screening-email-templates.ts
  - use-communication-templates.ts: plataforma-lia/src/hooks/use-communication-templates.ts
  - email_service.py: lia-agent-system/app/services/email_service.py
  - whatsapp_service.py: lia-agent-system/app/services/whatsapp_service.py
  - notification_service.py: lia-agent-system/app/services/notification_service.py
  - celery_app.py: lia-agent-system/app/core/celery_app.py
```

### Implementação Vue/Nuxt

#### Service: `services/communicationsApi.ts`
```typescript
export const communicationsApi = {
  async send(payload: SendPayload) {
    return api.post('/communications/send', payload)
  },
  async batchSend(payload: BatchSendPayload) {
    return api.post('/communications/batch-send', payload)
  },
  async getHistory(jobId: string) {
    return api.get(`/job-vacancies/${jobId}/communication-history`)
  }
}
```

#### Composable: `composables/useCommunicationTemplates.ts`
```typescript
export function useCommunicationTemplates(situation: string) {
  const templates = ref<Template[]>([])
  onMounted(async () => {
    templates.value = await communicationsApi.getTemplates({ situation })
  })
  return { templates }
}
```

### Backend

#### Templates necessários

| Situação | Template ID | Canal | Destinatário |
|----------|-------------|-------|--------------|
| Proposta aceita / Contratação | `proposta_aceita` | email + WhatsApp | Candidato contratado |
| Vaga encerrada | `vaga_fechada` | email + WhatsApp | Demais candidatos |
| Feedback construtivo | `feedback_construtivo` | email | Demais candidatos |

**Merge fields disponíveis:**
```
{{ candidate_name }}, {{ job_title }}, {{ company_name }},
{{ recruiter_name }}, {{ start_date }}, {{ department }}
```

#### Endpoints Backend

```
POST /api/v1/communications/send
Body: {
  recipient_type: 'candidate',
  recipient_id: UUID,
  channel: 'email' | 'whatsapp' | 'both',
  template_id: string,
  custom_message?: string,
  subject?: string,
  context: { candidate_name, job_title, company_name, ... }
}

POST /api/v1/communications/batch-send
Body: {
  recipient_ids: UUID[],
  channel: 'email' | 'whatsapp' | 'both',
  template_id: string,
  custom_message?: string,
  context: { job_title, company_name, ... }
}

GET /api/v1/job-vacancies/{id}/communication-history
Response: [{ id, recipient, channel, template, status, sent_at, opened_at }]
```

#### Integrações

**Email (Mailgun):**
```python
# lia-agent-system/app/services/email_service.py
from mailgun import MailgunAPIClient
from mailgun.helpers.mail import Mail

async def send_email(to: str, subject: str, body: str, template_id: str = None):
    sg = MailgunAPIClient(api_key=settings.MAILGUN_API_KEY)
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=to,
        subject=subject,
        html_content=body
    )
    sg.send(message)
```

**WhatsApp (Meta API):**
```python
# lia-agent-system/app/services/whatsapp_service.py
async def send_whatsapp(phone: str, message: str, template: str = None):
    url = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": { "body": message }
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload,
                         headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"})
```

**Celery Task:**
```python
# lia-agent-system/app/jobs/celery_tasks.py
@celery_app.task(bind=True, max_retries=3)
def send_closure_notifications(self, job_id: str, payload: dict):
    try:
        # processa envios
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### Banco de Dados

```sql
CREATE TABLE communication_logs (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id           UUID NOT NULL REFERENCES companies(id),
  job_vacancy_id       UUID REFERENCES job_vacancies(id),
  candidate_id         UUID REFERENCES candidates(id),
  channel              VARCHAR(20) NOT NULL,
  template_id          VARCHAR(100),
  message              TEXT,
  subject              VARCHAR(255),
  status               VARCHAR(20) DEFAULT 'pending',
  provider             VARCHAR(50),
  provider_message_id  VARCHAR(255),
  sent_at              TIMESTAMP,
  opened_at            TIMESTAMP,
  failed_at            TIMESTAMP,
  error_message        TEXT,
  created_at           TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_comm_logs_vacancy   ON communication_logs(job_vacancy_id);
CREATE INDEX idx_comm_logs_candidate ON communication_logs(candidate_id);
CREATE INDEX idx_comm_logs_status    ON communication_logs(status);
```

---

## 9. Cards Completos — AUD Auditoria e Compliance (WT-1505→WT-1512)

> **Fonte:** `diagnostico-agentes-mvp.md` + `ANALISE_COMPARATIVA_V5_vs_LIA.md`
> **Épico:** [WT-1505](https://wedotalent.atlassian.net/browse/WT-1505) — AUD — Auditoria e Compliance do Agente Python

---

### AUD-001 / WT-1506 — Propagar AuditCallback para ReAct Agents

- **Épico:** WT-1505 — AUD — Auditoria e Compliance do Agente Python
- **Jira Key:** [WT-1506](https://wedotalent.atlassian.net/browse/WT-1506)
- **Sprint:** S1 · **Prioridade:** P0 🔴 · **SPs:** 2
- **Fase:** MVP Alpha 1
- **Tags:** `auditoria` `react-agents` `langchain` `compliance` `mvp-alpha-1`
- **Dependências:** Nenhuma

**Contexto (Gap 1):** O `AuditCallback` da LIA (`libs/audit/audit_callback.py`) já existe mas não está injetado nos agentes ReAct do sistema de agentes Python (v5). Toda chamada LLM dos agentes deve ser auditada automaticamente — entrada, saída, custo, latência — sem que o agente "saiba" que está sendo auditado.

**Escopo:**
- Injetar `AuditCallback` no `config` de todos os agentes ReAct via `create_react_agent(config={"callbacks": [audit_callback]})`
- Garantir que `company_id` e `user_id` propagam pelo callback
- Dual storage: metadados no PostgreSQL + logs completos no S3

**DoD:**
- [ ] AuditCallback injetado em todos os 11 agentes ReAct do registry
- [ ] Testes verificando que cada chamada LLM gera um registro de auditoria


**Arquivos de Referência no Replit:**
- `lia-agent-system/libs/audit/audit_callback.py` — AuditCallback existente
- `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py` — Registry dos 11 agentes ReAct
- `lia-agent-system/app/shared/agents/langgraph_react_base.py` — Base class dos agentes
- `lia-agent-system/app/domains/workflow.py` — DomainWorkflow (ponto de injeção)
- `lia-agent-system/libs/models/lia_models/audit_log.py` — Modelo AuditLog
- `lia-agent-system/libs/models/lia_models/audit_logs.py` — Modelo estendido
- `lia-agent-system/libs/models/lia_models/agent_activity.py` — AgentActivity tracking
- `lia-agent-system/app/api/v1/audit_logs.py` — Endpoints existentes de audit
- `lia-agent-system/app/api/v1/audit_timeline.py` — Timeline endpoint

**Tabelas PostgreSQL:** `audit_logs (agent_name, decision_type, reasoning, candidate_id, job_vacancy_id)`, `agent_activity`

**Tags padronizadas:** `backend`, `IA`, `dados`, `compliance`, `auditoria`

**Como Testar:**
1. Invocar qualquer agente ReAct via chat
2. Verificar que `audit_logs` recebeu registro com agent_name, token count, latência
3. Verificar que company_id e user_id estão presentes no registro

---

### AUD-002 / WT-1507 — Rastrear Tools Chamadas por Nome

- **Épico:** WT-1505
- **Jira Key:** [WT-1507](https://wedotalent.atlassian.net/browse/WT-1507)
- **Sprint:** S1 · **Prioridade:** P1 🟠 · **SPs:** 1
- **Fase:** MVP Alpha 1
- **Tags:** `auditoria` `tools` `rastreamento` `mvp-alpha-1`
- **Dependências:** AUD-001 (WT-1506)

**Contexto (Gap 2):** O audit log atual não registra quais tools foram chamadas durante uma execução de agente. Essencial para debugar comportamento e para auditoria regulatória (saber que critério o agente consultou).

**Escopo:** Adicionar hook `on_tool_start` / `on_tool_end` no AuditCallback para registrar nome da tool, input e output em cada chamada.


**Arquivos de Referência no Replit:**
- `lia-agent-system/libs/audit/audit_callback.py` — Adicionar on_tool_start/on_tool_end
- `lia-agent-system/app/domains/cv_screening/agents/pipeline_tool_registry.py` — Tools do PipelineAgent
- `lia-agent-system/app/domains/job_management/tools/` — Tools do WizardAgent
- `lia-agent-system/app/domains/communication/tools/` — Tools do CommunicationAgent

**Tags padronizadas:** `backend`, `IA`, `dados`, `auditoria`

**Como Testar:**
1. Executar agente que usa tool (ex: PipelineAgent move candidato)
2. Verificar que audit_log inclui tool_name, tool_input, tool_output
3. Endpoint GET /audit/timeline retorna tools chamadas

---

### AUD-003 / WT-1508 — Circuit Breaker no Autonomous Agent

- **Épico:** WT-1505
- **Jira Key:** [WT-1508](https://wedotalent.atlassian.net/browse/WT-1508)
- **Sprint:** S1 · **Prioridade:** P1 🟠 · **SPs:** 2
- **Fase:** MVP Alpha 1
- **Tags:** `circuit-breaker` `resiliência` `autonomous-agent` `mvp-alpha-1`
- **Dependências:** Nenhuma

**Contexto (Gap 7):** O `AutomationReActAgent` (agente autônomo de tarefas) não tem circuit breaker. Se um provider LLM (Anthropic, OpenAI) cair, o agente continua tentando e esgotando budget de tokens.

**Escopo:** Integrar `CircuitBreaker` da plataforma no `AutomationReActAgent`. Se circuit abrir: falha rápida + log + notificação via `AgentHealthAlertService`.


**Arquivos de Referência no Replit:**
- `lia-agent-system/app/domains/automation/agents/` — AutomationReActAgent
- `lia-agent-system/app/shared/agents/langgraph_react_base.py` — Base com max_iterations
- `lia-agent-system/libs/models/lia_models/health_check.py` — HealthCheck model
- `lia-agent-system/libs/models/lia_models/observability.py` — Observability model

**Tags padronizadas:** `backend`, `IA`, `resiliência`

**Como Testar:**
1. Simular falha de provider LLM (mock Anthropic 503)
2. Verificar que circuit breaker abre após N falhas consecutivas
3. Verificar que AgentHealthAlertService notifica
4. Verificar que agente retorna erro graceful em vez de loop infinito

---

### AUD-004 / WT-1509 — Retention/Cleanup de agent_executions

- **Épico:** WT-1505
- **Jira Key:** [WT-1509](https://wedotalent.atlassian.net/browse/WT-1509)
- **Sprint:** S2 · **Prioridade:** P2 🟡 · **SPs:** 1
- **Fase:** MVP Alpha 1
- **Tags:** `retenção` `cleanup` `lgpd` `celery` `mvp-alpha-1`
- **Dependências:** AUD-001 (WT-1506)

**Contexto (Gap 6):** A tabela `agent_executions` cresce indefinidamente. LGPD e ISO 27001 exigem política de retenção definida. Registros antigos devem ser arquivados ou deletados conforme política.

**Escopo:** Celery beat task que executa diariamente: move registros > 90 dias para cold storage, deleta registros > 7 anos.


**Arquivos de Referência no Replit:**
- `lia-agent-system/libs/models/lia_models/audit_log.py` — Tabela audit_logs
- `lia-agent-system/libs/models/lia_models/agent_activity.py` — Tabela agent_activity

**Tags padronizadas:** `backend`, `dados`, `compliance`, `LGPD`

**Como Testar:**
1. Inserir registros de audit com created_at > 90 dias
2. Executar cleanup task
3. Verificar que registros foram movidos para cold storage
4. Verificar que registros < 90 dias permanecem intactos

---

### AUD-005 / WT-1510 — Storage Externo para Logs Pesados (S3/GCS)

- **Épico:** WT-1505
- **Jira Key:** [WT-1510](https://wedotalent.atlassian.net/browse/WT-1510)
- **Sprint:** S3 · **Prioridade:** P3 🟡 · **SPs:** 3
- **Fase:** MVP Alpha 1
- **Tags:** `s3` `storage` `auditoria` `sox` `iso27001` `mvp-alpha-1`
- **Dependências:** AUD-001 (WT-1506)

**Contexto (Gap 3):** Logs completos de execução de agentes (inputs/outputs completos) não devem ser armazenados em PostgreSQL — são grandes demais e têm política de retenção diferente (7 anos SOX).

**Escopo:** Configurar pipeline: metadados em PG (query rápida) + corpo completo em S3/GCS com lifecycle policy (90d → Glacier → 7 anos → deletar).


**Arquivos de Referência no Replit:**
- `lia-agent-system/libs/audit/audit_callback.py` — Source dos logs
- `lia-agent-system/libs/models/lia_models/audit_log.py` — Metadados PG

**Tags padronizadas:** `backend`, `dados`, `infra`, `compliance`, `SOX`

---

### AUD-006 / WT-1511 — Endpoints REST de Timeline

- **Épico:** WT-1505
- **Jira Key:** [WT-1511](https://wedotalent.atlassian.net/browse/WT-1511)
- **Sprint:** S3 · **Prioridade:** P3 🟡 · **SPs:** 3
- **Fase:** MVP Alpha 1
- **Tags:** `api` `timeline` `auditoria` `observabilidade` `mvp-alpha-1`
- **Dependências:** AUD-001 (WT-1506)

**Contexto (Gap 4):** Não existe API para consultar a timeline de execução de um agente específico. Dificulta debug e auditoria regulatória.

**Endpoints:**
```
GET /api/v1/audit/agents/{agent_name}/executions          → lista de execuções
GET /api/v1/audit/agents/{agent_name}/executions/{id}     → detalhe + tools chamadas
GET /api/v1/audit/candidates/{candidate_id}/timeline      → timeline por candidato
```


**Arquivos de Referência no Replit:**
- `lia-agent-system/app/api/v1/audit_timeline.py` — Endpoint existente (expandir)
- `lia-agent-system/app/api/v1/audit_logs.py` — Endpoints de audit_logs (expandir)
- `lia-agent-system/libs/models/lia_models/audit_log.py` — Queries
- Frontend: `plataforma-lia/src/app/admin/` — Painel de admin (integrar timeline)

**Tags padronizadas:** `backend`, `frontend`, `dados`, `auditoria`

**Como Testar:**
1. GET /audit/agents/PipelineReActAgent/executions → lista paginada
2. GET /audit/candidates/{id}/timeline → timeline completa do candidato
3. Verificar que tools chamadas aparecem na timeline

---

### AUD-007 / WT-1512 — Métricas Prometheus

- **Épico:** WT-1505
- **Jira Key:** [WT-1512](https://wedotalent.atlassian.net/browse/WT-1512)
- **Sprint:** S3 · **Prioridade:** P3 🟡 · **SPs:** 3
- **Fase:** MVP Alpha 1
- **Tags:** `prometheus` `métricas` `observabilidade` `grafana` `mvp-alpha-1`
- **Dependências:** AUD-001 (WT-1506)

**Contexto (Gap 5):** O sistema de agentes Python (v5) não emite métricas Prometheus. Sem métricas, não é possível criar alertas ou dashboards Grafana.

**Métricas a adicionar:**
```
agent_executions_total{agent, status, company_id}
agent_execution_duration_seconds{agent}
agent_tool_calls_total{agent, tool}
agent_llm_cost_dollars{agent, model}
agent_circuit_breaker_state{circuit}
```


**Arquivos de Referência no Replit:**
- `lia-agent-system/libs/models/lia_models/observability.py` — Modelo existente
- `lia-agent-system/app/shared/agents/langgraph_react_base.py` — Instrumentar com counters

**Tags padronizadas:** `backend`, `infra`, `observabilidade`

**Como Testar:**
1. GET /metrics → retorna métricas Prometheus text format
2. Verificar counters: agent_executions_total, agent_llm_cost_dollars
3. Verificar histograms: agent_execution_duration_seconds

---

## 10. Tabela de Dependências Cross-Épico

> Dependências entre cards de épicos diferentes. Críticas para planejamento de sprint.

| Card | Depende de | Impacto se bloqueado |
|------|-----------|----------------------|
| SAT-005 | COM-001 | Fila de espera não notifica candidatos |
| SAT-006 | COM-001 | Override não envia notificação |
| SAT-007 | SAT-001, INS-001 | Gate 1 não funciona |
| TRI-002 | TRI-005 | Hook não tem backend para chamar |
| TRI-004 | VOZ-002 | Bolha de mensagem sem player de áudio |
| TRI-005 | COM-001 | Motor de triagem não consegue enviar feedback |
| COM-002 | TRI-005 | Feedback pós-triagem não é disparado |
| COM-004 | SAT-005 | Convite de fila não é enviado ao promover |
| COM-005 | TRI-005 | Confirmação pós-triagem não é enviada |
| INS-001 | SAT-001 | Formulário não sabe se pool está cheio |
| INS-003 | SAT-001 | Endpoint não verifica saturação |
| VOZ-004 | TRI-002 | Voice mode não propaga estado |
| VGM-010 | COM-001 | Notificações de fechamento não são enviadas |
| AUD-004 | AUD-001 | Cleanup sem logs para limpar |
| AUD-005 | AUD-001 | Storage externo sem origem de dados |
| AUD-006 | AUD-001 | Endpoints sem dados para retornar |
| AUD-007 | AUD-001 | Métricas sem fonte de dados |

---

## Resumo Executivo

| Sprint | Cards (Épicos 30-34+AUD) | Cards (É35 AGT) | SPs Total | Entregável Principal |
|--------|:------------------------:|:----------------:|:---------:|----------------------|
| **S0 — Infra IA** | — | 4 (AGT-000,001,002,003) | 47 | Padronização, BaseAgent, Orchestrator, ATS |
| **S1 — Fundação** | 17 | 5 (AGT-004,005,006,015,017) | 118 | APIs base, VGM S1, Sourcing, Communication, Gates |
| **S2 — Fluxo Completo** | 23 | 7 (AGT-007,008,009,010,016,FE-001,FE-002) | 205 | Chat Web Triagem + WSI + CV Screening + HITL UI |
| **S3 — Refinamentos** | 4 | 5 (AGT-011,012,013,014,FE-003) | 51 | HITL Wiring, Scheduling, Monitores, Pipeline UI |
| **TOTAL** | **44** | **21** | **413** | MVP Alpha 1 completo (65 cards · 8 épicos) |

**Caminho crítico do MVP Alpha 1 (funcionalidade):**
```
SAT-001 → INS-003 → INS-001 → SAT-007
COM-001 → SAT-005 → COM-004
TRI-001 → TRI-005 → TRI-002 → (Chat Web funcional)
VGM-001 → VGM-005 → VGM-006 (Vaga publicada)
AUD-001 → AUD-002 → AUD-003 (Auditoria mínima ativa)
```

**Caminho crítico da Arquitetura de IA (É35 AGT):**
```
AGT-002 → AGT-015 → AGT-011 → AGT-FE-002 (HITL end-to-end)
AGT-003 → AGT-007 → AGT-009 → AGT-FE-001 (Triagem WSI end-to-end)
```

---

## 11. Cards Completos — É35 Arquitetura de IA: Agentes, Tools, Serviços e Automações (AGT)

### Épico [WT-1558](https://wedotalent.atlassian.net/browse/WT-1558) — É35: Arquitetura de IA

> **Escopo:** 21 cards cobrindo a camada de inteligência artificial da Plataforma LIA — agentes Python (LangGraph + LangChain), orquestrador central, serviços de IA, infraestrutura compartilhada (BaseAgent, FairnessGuard, PII Masking, AuditCallback), automações (Celery Beat), HITL e interfaces frontend. Fonte: `diagnostico-agentes-mvp.md` §17–§21.

> **Stack:** LangGraph + LangChain · Claude Sonnet (primário) → OpenAI → Gemini (fallback) · Celery Beat + RabbitMQ · PostgresSaver · Redis · PGVector + Elasticsearch · WebSocket · React/Next.js

> **Sobreposições complementares:** AGT-005↔COM-001, AGT-007↔TRI-005, AGT-009↔TRI-002, AGT-FE-001↔TRI-002, AGT-015↔SAT-007. São camadas complementares — os cards AGT adicionam inteligência de IA sobre a funcionalidade base.

---

### AGT-000: Padronização & Setup Base — [WT-1559](https://wedotalent.atlassian.net/browse/WT-1559)

```yaml
Titulo: "[AGT-000] Padronização & Setup Base — 4-File Pattern + Dev Environment + Checklist 18 Itens"
Tipo: Infra/Dev
Area: Backend
Sprint: S0
Pontos: 5
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Fase: MVP Alpha 1
Tags: [backend, IA, infra, devops, compliance, react-agents, langgraph]
Classificação: 🟢 MVP CRÍTICO
Dependências: Nenhuma — pré-requisito de TODOS os outros cards AGT
Referências Diagnóstico: §13B (blueprint), §13D (compliance), §13F (IA vs Determinístico), §13C.17

Estado V5 vs LIA:
  V5: Não existe — estrutura de diretórios diferente
  LIA: Padrão 4-file já definido, EnhancedAgentMixin, AgentScaffold
  Veredicto: Card de padronização — define padrão V5 baseado nas melhores práticas LIA

Descricao: |
  Card de infraestrutura de desenvolvimento. Define o padrão obrigatório para
  todos os agentes (4-file pattern), a estrutura de diretórios V5, configuração
  do ambiente (env vars, Docker, serviços externos) e o checklist de 18 itens
  de produção que TODOS os agentes devem passar antes de marcar como "Done".
  Nenhum outro card AGT pode ser iniciado sem este estar concluído.

Historia de Usuario: |
  Como desenvolvedor do time, eu quero ter uma estrutura padronizada de
  diretórios, padrão 4-file obrigatório para agentes, ambiente Docker
  configurado e checklist de produção documentado, para que todos os agentes
  sejam construídos de forma consistente e auditável.

Padrao 4-File Obrigatorio por Agente:
  - {domain}_react_agent.py — Classe principal (herda EnhancedAgentMixin)
  - {domain}_system_prompt.py — build_system_prompt() → str (10 seções obrigatórias)
  - {domain}_tool_registry.py — TOOL_DEFINITIONS, STAGE_TOOLS, funções wrapper async
  - {domain}_stage_context.py — get_stage_context(stage) → str

10 Secoes Obrigatorias do System Prompt:
  1. IDENTIDADE E PAPEL
  2. CONTEXTO DA EMPRESA (dinâmico via stage_context)
  3. FERRAMENTAS DISPONÍVEIS
  4. REGRAS DE USO DAS FERRAMENTAS
  5. CONTEXTO DO ESTÁGIO ATUAL (dinâmico por stage)
  6. GUARDRAILS E LIMITAÇÕES
  7. COMPLIANCE E ÉTICA
  8. EXEMPLOS DE USO (FEW-SHOT) — mínimo 2-3
  9. TRATAMENTO DE ERROS
  10. FORMATO DE RESPOSTA

Checklist de Producao — 18 Itens:
  1. Padrão 4-file completo
  2. EnhancedAgentMixin herdado — process() implementado
  3. FairnessGuard wired — em TODAS as entradas de texto
  4. PromptInjectionGuard wired — sanitiza input antes do LLM
  5. AuditCallback registrado — toda execução trackeada com company_id
  6. company_id propagado — em TODAS queries, registros e logs
  7. PII Masking ativo — CPF, email, tel mascarados nos logs
  8. PolicyEngine consultado — antes de cada execução
  9. Circuit breaker — em TODAS chamadas LLM e APIs externas
  10. System prompt 10 seções — incluindo 2+ few-shot examples
  11. STAGE_TOOLS correto — tools por estágio definidas
  12. Testes unitários — mínimo 5 por tool registrada
  13. Testes fairness — 5+ queries discriminatórias bloqueadas
  14. Testes integração — fluxo completo com mocks
  15. Sem dados hardcoded — sem PII em código
  16. Sem secrets em código — todas via env vars
  17. Logs sem PII — verificado com PIIMaskingTest
  18. FRIA documentada — se agente toma decisões (EU AI Act)

Requisitos Tecnicos:
  Arquivos a criar:
    - docker-compose.yml (PostgreSQL 15 + Redis 7 + RabbitMQ 3)
    - .env.example (todas vars obrigatórias documentadas)
    - alembic.ini + alembic/env.py (suporte async SQLAlchemy)
    - src/core/config.py (Settings Pydantic BaseSettings)
    - src/shared/agents/agent_scaffold.py (AgentScaffold.generate(domain='X') → 4 arquivos)
  Dependências:
    langchain-anthropic, langgraph, celery, aio-pika, pgvector, alembic, asyncpg

Criterios de Aceitacao:
  - [ ] docker-compose up sobe PostgreSQL + Redis + RabbitMQ sem erros
  - [ ] alembic upgrade head roda sem erros
  - [ ] AgentScaffold.generate(domain='test') cria 4 arquivos
  - [ ] .env.example documentado e revisado
  - [ ] Checklist 18 itens publicado internamente
  - [ ] README de setup completo (passos 1–10)

DoD:
  - [ ] Docker Compose funcional — todos serviços healthy
  - [ ] Checklist 18 itens aprovado pelo tech lead
  - [ ] AgentScaffold.generate() testado
  - [ ] README atualizado

Inteligencia e Automacao:
  Agentes Envolvidos: Nenhum — define a infra que todos usam
  Tools: AgentScaffold.generate() — gera 4 arquivos por domínio
  Servicos IA: Nenhum — card de infraestrutura/padronização
  Modelo LLM: Nenhum — configuração de ambiente
  Governanca: Checklist 18 itens = gate obrigatório para todo agente ir a produção
  Fairness: FairnessGuard definido como obrigatório (item #3 do checklist)
  Automacoes: AgentScaffold gera templates ao criar novo domínio
  Fallbacks: Env vars de integrações externas usam mocks no início

Arquivos de Referencia (Codigo Existente no Replit):
  - lia-agent-system/app/shared/agents/langgraph_react_base.py
  - lia-agent-system/app/shared/agents/enhanced_agent_mixin.py
  - lia-agent-system/app/shared/compliance/fairness_guard.py
  - lia-agent-system/app/shared/compliance/audit_callback.py
  - lia-agent-system/app/shared/pii_masking.py
  - lia-agent-system/app/shared/prompt_injection.py
  - lia-agent-system/app/core/celery_app.py

Riscos:
  - V5 pode ter estrutura de diretórios diferente — mapear e decidir
  - agent_scaffold.py gera templates — devs implementam conteúdo real
  - Env vars externas (Gupy, Pearch) podem não estar disponíveis — usar mocks
```

---

### AGT-002: Infraestrutura Compartilhada — [WT-1560](https://wedotalent.atlassian.net/browse/WT-1560)

```yaml
Titulo: "[AGT-002] Infraestrutura Compartilhada — BaseAgent + FairnessGuard + PII Masking + AuditCallback + LLM Providers"
Tipo: Infra
Area: Backend
Sprint: S0
Pontos: 21
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Fase: MVP Alpha 1
Tags: [backend, IA, infra, compliance, fairness, langchain, langgraph, lgpd, multi-tenant]
Classificação: 🟢 MVP CRÍTICO
Dependências: Nenhuma (pré-requisito de todos os outros cards)
Referências Diagnóstico: §13B, §13C.2, §13C.3, §13C.14, §13D, §13D.5, §13C.17

Estado V5 vs LIA:
  V5: Estrutura a ser criada no novo diretório src/
  LIA: Todos os componentes existem em app/shared/ (9 arquivos base + compliance)
  Veredicto: Adaptar todos de LIA para V5 — apenas reestruturar diretórios

Roteiro de Reproducao (§13C.17):
  Provedores e LLM (7 arquivos): §13C.17
  Robustez e segurança (10 arquivos): §13C.17
  Prompts (13 arquivos): §13C.17

Descricao: |
  Setup da infraestrutura base que todos os agentes dependem:
  BaseAgent/EnhancedAgentMixin, provedores LLM (Claude primário, OpenAI/Gemini
  fallback), sistema de prompts YAML, compliance (FairnessGuard 3 camadas,
  PII Masking, AuditCallback, PromptInjectionGuard), guardrails seed e
  configuração base.

Historia de Usuario: |
  Como desenvolvedor de agentes IA, eu quero ter infraestrutura compartilhada
  com BaseAgent, provedores LLM, compliance (FairnessGuard, PII Masking,
  AuditCallback) e prompts YAML, para construir agentes seguros e auditáveis.

Requisitos Tecnicos:
  Arquivos a Criar/Modificar:
    | Ação    | Arquivo V5                                  | Referência LIA                              |
    | Criar   | src/shared/agents/enhanced_agent_mixin.py   | app/shared/agents/enhanced_agent_mixin.py   |
    | Criar   | src/shared/agents/langgraph_react_base.py   | app/shared/agents/langgraph_react_base.py   |
    | Criar   | src/shared/providers/llm_factory.py         | app/shared/providers/llm_factory.py         |
    | Criar   | src/shared/providers/llm_claude.py          | app/shared/providers/llm_claude.py          |
    | Criar   | src/shared/compliance/fairness_guard.py     | app/shared/compliance/fairness_guard.py     |
    | Criar   | src/shared/compliance/audit_callback.py     | app/shared/compliance/audit_callback.py     |
    | Criar   | src/shared/compliance/audit_service.py      | app/shared/compliance/audit_service.py      |
    | Criar   | src/shared/pii_masking.py                   | app/shared/pii_masking.py                   |
    | Criar   | src/shared/prompt_injection.py              | app/shared/prompt_injection.py              |
    | Criar   | src/shared/prompts/loader.py                | app/shared/prompts/loader.py                |
    | Criar   | src/prompts/shared/lia_persona.yaml         | app/prompts/shared/lia_persona.yaml         |
    | Criar   | src/core/seeds/guardrails_seed.py           | app/core/seeds/guardrails_seed.py           |
    | Executar| Migrations 020, 032, 034, 035              | ver 0B.2                                    |
    | Executar| guardrails_seed.py                          | ver 0B.3                                    |

Criterios de Aceitacao:
  - [ ] EnhancedAgentMixin.process() funciona com 6 passos (ver 13B.7)
  - [ ] FairnessGuard.check() detecta padrões discriminatórios (Camadas 1+2)
  - [ ] PII Masking ativo nos loggers (CPF, email, tel mascarados)
  - [ ] AuditCallback registra todas execuções no DB
  - [ ] PromptInjectionGuard bloqueia tentativas de injection
  - [ ] 13 guardrails do seed carregados no DB
  - [ ] Providers LLM: Claude primário, OpenAI e Gemini fallback

Testes Obrigatorios:
  - Unit: FairnessGuard com 10+ casos discriminatórios
  - Unit: PII Masking — log com CPF/email/tel mascarado
  - Unit: PromptInjectionGuard — jailbreak bloqueado

Inteligencia e Automacao:
  Agentes: EnhancedAgentMixin — base de todos os ReAct agents
  Servicos IA: LLMFactory (Claude Sonnet → OpenAI → Gemini fallback)
  Modelo LLM: Claude 3.5 Sonnet via langchain-anthropic
  Governanca: FairnessGuard 3 camadas + 13 guardrails seed
  Fairness: Camada 1 regex, Camada 2 semântica, Camada 3 LLM (opt-in)
  Compliance: LGPD Art. 46 (PII Masking), EU AI Act (FRIA)
  Fallbacks: LLM cascade Claude → OpenAI → Gemini

Arquivos de Referencia:
  - lia-agent-system/app/shared/agents/enhanced_agent_mixin.py
  - lia-agent-system/app/shared/agents/langgraph_react_base.py
  - lia-agent-system/app/shared/compliance/fairness_guard.py
  - lia-agent-system/app/shared/compliance/audit_callback.py
  - lia-agent-system/app/shared/compliance/audit_service.py
  - lia-agent-system/app/shared/pii_masking.py
  - lia-agent-system/app/shared/prompt_injection.py
  - lia-agent-system/app/shared/providers/llm_factory.py

Tabelas PostgreSQL:
  - agent_executions (migration 020)
  - guardrails (migration 034)
  - hitl_pending_actions (migration 032)
  - hitl_audit_trail (migration 032)
```

---

### AGT-001: MainOrchestrator — [WT-1561](https://wedotalent.atlassian.net/browse/WT-1561)

```yaml
Titulo: "[AGT-001] MainOrchestrator — 3-Tier CascadedRouter + HITL + Roteamento de 9 Agentes"
Tipo: Orchestrator
Area: Backend
Sprint: S0
Pontos: 13
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Tags: [backend, IA, orchestrator, websocket, hitl, langgraph, multi-tenant]
Classificação: 🟢 MVP CRÍTICO
Dependências: AGT-002 (bloqueante)
Referências Diagnóstico: §14.1, §13C.1, §13B.7, §13C.17

Estado V5 vs LIA:
  V5: Mesma arquitetura (orchestrator.py + cascaded_router) — sem HITL
  LIA: CascadedRouter 6 tiers + PendingActions + HITL + PolicyEngine
  Veredicto: LIA mais completa — usar LIA, adaptar para 9 domínios Alpha 1

Dominios Roteados Alpha 1:
  | Domínio              | Agente                        | Card AGT |
  | wizard               | WizardReActAgent              | AGT-006  |
  | sourcing             | SourcingReActAgent            | AGT-004  |
  | cv_screening         | CVScreeningReActAgent         | AGT-008  |
  | pipeline_transition  | PipelineTransitionReActAgent  | AGT-015  |
  | communication        | CommunicationReActAgent       | AGT-005  |
  | ats_integration      | ATSIntegrationService         | AGT-003  |
  | wsi                  | WSIInterviewGraph             | AGT-007  |
  | policy               | HiringPolicyService           | AGT-017  |
  | scheduling           | SchedulingGraph (Pós-Alpha)   | AGT-012  |

Roteiro de Reproducao (§13C.17):
  Orquestrador (9 arquivos): §13C.17

Descricao: |
  Orquestrador central que recebe mensagens do frontend via WebSocket,
  classifica a intenção com CascadedRouter (6 tiers) e roteia para o agente
  correto. Cobre passos 5, 6 e 7 do fluxo Alpha 1.

Historia de Usuario: |
  Como recrutador usando a LIA, eu quero enviar mensagens via chat e ter minha
  intenção classificada e roteada automaticamente para o agente especialista
  correto, sem precisar navegar por menus.

Requisitos Tecnicos:
  CascadedRouter — 6 Tiers:
    T1 Hard Rules (<1ms): Comandos diretos (/help, /cancel)
    T2 State Check (<1ms): Contexto de sessão
    T3 Domain Lock (<1ms): Sessão associada a domínio
    T4 FastRouter (<5ms): Regex patterns por domínio
    T5 Intent LLM (~500ms): Claude classifica intenção
    T6 Fallback (<1ms): Default domain
  
  Arquivos:
    | Ação    | Arquivo V5                            | Referência LIA                        |
    | Adaptar | src/domains/orchestrator.py            | app/orchestrator/orchestrator.py      |
    | Criar   | src/orchestrator/cascaded_router.py    | app/orchestrator/cascaded_router.py   |
    | Criar   | src/orchestrator/intent_router.py      | app/orchestrator/intent_router.py     |
    | Criar   | src/orchestrator/fast_router.py        | app/orchestrator/fast_router.py       |
    | Criar   | src/orchestrator/pending_action.py     | app/orchestrator/pending_action.py    |
    | Criar   | src/orchestrator/task_planner.py       | app/orchestrator/task_planner.py      |
    | Criar   | src/orchestrator/state_manager.py      | app/orchestrator/state_manager.py     |
    | Criar   | src/orchestrator/llm_cascade.py        | app/orchestrator/llm_cascade.py       |

Criterios de Aceitacao:
  - [ ] WebSocket /ws/chat/{session_id} roteia para agente correto
  - [ ] CascadedRouter T4 cobre intents Alpha 1
  - [ ] PendingActions suporta fluxos multi-turn
  - [ ] Roteamento para 9 agentes Alpha 1
  - [ ] HITL inline: interrupt → hitl_request no frontend
  - [ ] PolicyEngine carrega guardrails antes de cada execução
  - [ ] company_id extraído do JWT e propagado

Inteligencia e Automacao:
  Agentes: MainOrchestrator — orquestrador central
  Servicos IA: IntentRouter (T5) — classificação LLM
  Modelo LLM: Claude Sonnet (intent classification)
  HITL: interrupt → hitl_request → approve/reject → resume
  Governanca: PolicyEngine carrega guardrails do DB
  Fallbacks: LLM cascade simplificado para Sonnet no MVP

Arquivos de Referencia:
  - lia-agent-system/app/api/orchestrator_routes.py
  - lia-agent-system/app/services/enhanced_intent_classifier.py
  - lia-agent-system/app/services/wizard_orchestrator_service.py
```

---

### AGT-003: ATSIntegrationService — [WT-1562](https://wedotalent.atlassian.net/browse/WT-1562)

```yaml
Titulo: "[AGT-003] ATSIntegrationService — Integração Bidirecional com ATS (Gupy Primário)"
Tipo: Serviço REST (Alpha 1) / ReAct Agent (Pós-Alpha)
Area: Backend
Sprint: S0
Pontos: 8
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Tags: [backend, IA, serviço, integração, ats, multi-tenant]
Classificação: 🟢 MVP CRÍTICO
Dependências: AGT-002
Referências Diagnóstico: §14.8, §4.8, §13B.7, §13C.17

Estado V5 vs LIA:
  V5: SourcingAPIClient (consumidor REST) + 67 YAMLs de endpoints
  LIA: ReAct Agent com 5 tools + 5 clientes ATS (Gupy, PandaPé, Merge, StackOne, base) + sync bidirecional + webhooks
  Veredicto: Alpha 1 usa como serviço REST (CRUD bidirecional é determinístico). Pós-Alpha ativa agente conversacional

Descricao: |
  Serviço REST de integração bidirecional com ATS externo. Premissa do Alpha 1:
  vagas importadas do ATS antes de tudo mais. Alpha 1 usa como serviço REST
  simples (não agente ReAct). Cobre passos 2, 5 e 8.

5 Tools (Pos-Alpha como agente ReAct):
  | Tool                     | O que faz                       | Serviço        |
  | sync_candidate_to_ats    | Sync candidato para ATS externo | ATSSyncService |
  | fetch_candidate_from_ats | Importa candidato do ATS        | ATSSyncService |
  | validate_ats_fields      | Valida campos ATS               | Validation     |
  | bulk_sync_candidates     | Sync em lote                    | ATSSyncService |
  | get_sync_status          | Status do sync                  | ATSSyncService |

Servicos Chamados:
  | Serviço              | Arquivo                                         |
  | ATSSyncService       | app/domains/ats_integration/services/ats_sync_service.py |
  | GupyService          | app/services/gupy_service.py                     |
  | PandapeService       | app/services/pandape_service.py                  |
  | MergeATSService      | app/services/merge_ats_service.py                |
  | ATSJobHistoryService | app/services/ats_job_history_service.py           |

API Endpoints:
  | Método | Endpoint                       | Descrição                     |
  | POST   | /ats/connections                | Cria conexão ATS (Gupy/Pandapé) |
  | POST   | /ats/connections/{id}/sync      | Dispara sync bidirecional     |
  | WS     | /ws/chat/{session_id} (ats_integration) | WebSocket (pós-Alpha)  |

Automacoes Relacionadas:
  | Automação              | Frequência | Ação                            |
  | ATS_SYNC (evento)      | Imediato   | Sincroniza mudanças com ATS     |
  | CANDIDATE_HIRED (evento)| Imediato  | Sync final com ATS              |

Padrao de Implementacao (13B.7):
  Classe: ATSIntegrationReActAgent(EnhancedAgentMixin, BaseAgent)
  Domain: "ats_integration"
  Tools: get_ats_tools() (5 tools)
  System_prompt: get_ats_system_prompt(guardrails, memory_context)
  Guardrails: 13D.5 — #1-#6 globais
  Particularidade: Alpha 1 usa como serviço REST — não instancia ReAct loop

Camadas de Suporte Obrigatorias:
  | Camada         | Seção  | Arquivos                                    |
  | Provedores LLM | 13C.2  | ats_factory.py (factory de providers ATS)    |
  | Config/Infra   | 13C.14 | config.py (chaves API dos ATS)              |

Roteiro de Reproducao (§13C.17):
  ReAct (domínio=ats_integration): 7 arquivos padrão

Criterios de Aceitacao:
  - [ ] GET /api/v1/ats/jobs importa vagas do Gupy
  - [ ] Vagas salvas como job_vacancies com company_id
  - [ ] POST /api/v1/ats/sync-status exporta status/score de volta
  - [ ] Mapeamento de campos ATS ↔ WeDo funcional
  - [ ] Circuit breaker/retry se ATS indisponível
  - [ ] Audit log para cada sync

Para Alpha 1:
  - Premissa: vaga importada do ATS
  - Validar fetch_candidate_from_ats com pelo menos 1 provedor real (Gupy ou Merge)
  - Garantir que importação popula dados suficientes para o wizard editar

Arquivos de Referencia:
  - lia-agent-system/app/domains/ats_integration/ (4-file pattern completo)
  - lia-agent-system/app/domains/ats_integration/agents/ats_integration_tool_registry.py
  - lia-agent-system/app/domains/ats_integration/services/ats_clients/gupy.py
  - lia-agent-system/app/services/ats_sync_service.py
```

---

### AGT-004: SourcingReActAgent — [WT-1563](https://wedotalent.atlassian.net/browse/WT-1563)

```yaml
Titulo: "[AGT-004] SourcingReActAgent — Busca de Candidatos com 14 Tools"
Tipo: ReAct Agent (4-file pattern)
Area: Backend
Sprint: S1
Pontos: 13
Prioridade: P0
Epic: É35 (WT-1558)
Tags: [backend, IA, react-agents, sourcing, pgvector, elasticsearch, fairness]
Classificação: 🟡 MVP SUPORTE
Dependências: AGT-002, AGT-003
Referências Diagnóstico: §14.3, §4.2, §13B.7, §13C.6, §13C.17

Estado V5 vs LIA:
  V5: MultiAgentOrchestrator com 6 sub-agents (search, detail, comparison, analytics, report, action) — padrão fragmentado
  LIA: 1 ReAct agent coeso com 14 tools + WRF + LearningLoop
  Veredicto: LIA é mais coeso — usar padrão LIA (ReAct puro, 4-file)

Descricao: |
  Agente ReAct puro (4-file pattern) de busca de candidatos. Ciclo ReAct iterativo:
  mensagem → raciocínio LLM → escolha de tool (14 disponíveis) → execução →
  observação → próximo passo. Sem LangGraph. Exemplo canônico da seção 13B.7.

14 Tools com Servicos:
  | Tool                    | O que faz                           | Serviço                     |
  | set_search_criteria     | Define critérios de busca           | Search Context              |
  | suggest_skills          | Sugestões IA de skills para cargo   | LLM / Skill Taxonomy        |
  | search_candidates       | Busca candidatos (ES+PGV+WRF)      | CandidateSearchService      |
  | filter_results          | Filtra resultados por critério      | In-memory filter            |
  | view_candidate          | Visualiza perfil do candidato       | DB: candidates              |
  | analyze_profile         | Análise IA do perfil                | Profile Analysis Service    |
  | compare_candidates      | Comparação lado a lado              | ComparisonService           |
  | score_candidate         | Scoring WSI do candidato            | WSI Scoring Service         |
  | add_to_shortlist        | Adiciona à shortlist                | DB: vacancy_candidates      |
  | remove_from_shortlist   | Remove da shortlist                 | DB: vacancy_candidates      |
  | rank_candidates         | Rankeia shortlist por score IA      | Scoring Engine              |
  | send_outreach           | Envia mensagem de contato           | CommunicationService        |
  | generate_message        | Gera mensagem personalizada com IA  | LLM                         |
  | track_response          | Rastreia resposta do candidato      | DB: communication_history   |

Servicos Chamados:
  | Serviço                  | Arquivo                                            |
  | HybridSearchService      | app/services/hybrid_search_service.py               |
  | WRFDynamicKService       | app/services/wrf_dynamic_k_service.py               |
  | PreWRFFilterService      | app/services/pre_wrf_filter_service.py              |
  | RAGPipelineService       | app/services/rag_pipeline_service.py                |
  | PearchService            | app/services/pearch_service.py                      |
  | ApifyService             | app/services/apify_service.py                       |
  | CandidateEnrichmentSvc   | app/services/candidate_enrichment_service.py        |
  | SourcingPipelineService  | app/services/sourcing_pipeline_service.py           |
  | SemanticSearchService    | app/shared/intelligence/semantic_search_service.py  |
  | EmbeddingService         | app/shared/intelligence/embedding_service.py        |
  | WorkingMemoryService     | app/shared/agents/working_memory.py                 |

API Endpoints:
  | Método | Endpoint                            | Descrição                     |
  | POST   | /sourcing/search                    | Busca booleana                |
  | POST   | /sourcing/match-candidates          | Matching candidato×vaga       |
  | GET    | /sourcing/suggestions/{job_id}      | Sugestões por vaga            |
  | POST   | /candidates/search/local            | Busca local (PostgreSQL)      |
  | POST   | /candidates/search                  | Busca externa (Pearch 190M+)  |
  | POST   | /candidates/{id}/enrich             | Enriquecimento (Apify)        |
  | GET    | /candidates/rag-search              | Busca RAG híbrida             |
  | WS     | /ws/chat/{session_id} (sourcing)    | WebSocket conversacional      |

Padrao de Implementacao (13B.7):
  Classe: SourcingReActAgent(EnhancedAgentMixin, BaseAgent)
  Domain: "sourcing"
  Tools: get_sourcing_tools() (14 tools)
  System_prompt: get_sourcing_system_prompt(guardrails, memory_context)
  Guardrails: 13D.5 — #1-#6 globais + #10 (sourcing — não contatar recusados <6 meses)
  Particularidade: ReAct puro — exemplo canônico da seção 13B.7

Camadas de Suporte Obrigatorias:
  | Camada            | Seção  | Arquivos                                         |
  | Sourcing Services | 13C.6  | 13 arquivos (pipeline, WRF, Pearch, ES, pgvector) |
  | Provedores LLM    | 13C.2  | llm.py, embedding_service.py, semantic_search     |
  | Prompts           | 13C.17 | sourcing.yaml, lia_persona.yaml                   |

Roteiro de Reproducao:
  1. app/shared/agents/react_agent_registry.py
  2. app/domains/sourcing/agents/sourcing_react_agent.py
  3. app/domains/sourcing/agents/sourcing_system_prompt.py
  4. app/domains/sourcing/agents/sourcing_tool_registry.py
  5. app/domains/sourcing/agents/sourcing_stage_context.py
  6. app/prompts/domains/sourcing.yaml
  7. app/prompts/shared/lia_persona.yaml
  Sourcing inteligente (8 arquivos): §13C.17

Gaps V5 Aplicaveis:
  | Gap V5                                              | Impacto                         |
  | ParamExtractor (492L, extração detalhada)            | 🟡 V5 mais detalhado na extração |
  | FactChecker domain-specific (313L, verifica claims)  | 🟡 LIA tem genérico em shared    |
  | Template Formatter (256L, formatação por tipo)        | 🟢 Nice-to-have                  |
  | Validators (367L, validação de dados sourcing)        | 🟢 LIA valida inline             |

Para Alpha 1:
  - Integrar busca com dados importados do ATS (candidatos da vaga)
  - Validar que WRF+PGV+ES funciona em produção
  - Configurar Pearch/Apify para busca externa (se no scope Alpha 1)

Arquivos de Referencia:
  - lia-agent-system/app/domains/sourcing/agents/ (4-file completo)
  - lia-agent-system/app/services/rag_pipeline_service.py
  - lia-agent-system/app/services/wrf_dynamic_k_service.py
  - lia-agent-system/app/services/pre_wrf_filter_service.py
  - lia-agent-system/app/services/hybrid_search_service.py
```

---

### AGT-005: CommunicationService — [WT-1564](https://wedotalent.atlassian.net/browse/WT-1564)

```yaml
Titulo: "[AGT-005] CommunicationService + Adapters — Email + WhatsApp + Teams + Feedback Personalizado"
Tipo: ReAct Agent (4-file pattern)
Area: Backend
Sprint: S1
Pontos: 13
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Tags: [backend, IA, comunicação, email, whatsapp, teams, lgpd]
Classificação: 🟢 MVP CRÍTICO
Dependências: AGT-002
Sobreposição: COM-001 — camada complementar de IA
Referências Diagnóstico: §14.7, §4.7, §13C.5, §13C.17, §13D.3

Estado V5 vs LIA:
  V5: Mesma arquitetura (communication_react_agent.py), mas só email básico
  LIA: Agent com 5 tools + WhatsApp + Teams + template engine + 23 arquivos de suporte
  Veredicto: LIA significativamente mais completa — usar LIA. Absorve AnalistaFeedback (Ag.7 reclassificado)

Descricao: |
  Agente ReAct puro (4-file pattern) de comunicação multi-canal. Ciclo ReAct iterativo
  com 5 tools. Decide qual canal enviar (email vs WhatsApp vs Teams), com que template,
  em que momento. 23 arquivos de suporte: Adapters (Resend, SendGrid, Meta, Twilio),
  dispatcher, templates, history — ver camada 13C.5.
  Complementa COM-001 adicionando IA: tone policy, AI_GENERATED_FOOTER, PersonalizedFeedbackService.

5 Tools com Servicos:
  | Tool                       | O que faz                        | Serviço                       |
  | send_email                 | Envia email (Resend ou SendGrid) | EmailService                  |
  | send_whatsapp              | Envia WhatsApp (Meta ou Twilio)  | WhatsAppService               |
  | get_communication_history  | Histórico de comunicações        | CommunicationHistoryService   |
  | schedule_message           | Agenda envio futuro              | AutomationScheduler           |
  | check_rate_limit           | Verifica rate limit por canal    | TokenBudgetService            |

Servicos Chamados:
  | Serviço                      | Arquivo                                                       |
  | CommunicationService         | app/domains/communication/services/communication_service.py    |
  | CommunicationDispatcher      | app/services/communication_dispatcher.py                       |
  | EmailService                 | app/services/email_service.py                                  |
  | EmailProviders               | app/services/email_providers/ (Resend + SendGrid)              |
  | RecruitmentEmailTemplates    | app/services/recruitment_email_templates.py                    |
  | WhatsAppService              | app/domains/communication/services/whatsapp_service.py         |
  | WhatsAppTwilioService        | app/services/whatsapp_twilio_service.py                        |
  | WhatsAppMetaService          | app/services/whatsapp_meta_service.py                          |
  | WhatsAppFactory              | app/services/whatsapp_factory.py                               |
  | CommunicationHistoryService  | app/domains/communication/services/communication_history.py    |
  | TeamsService                 | app/domains/communication/services/teams_service.py            |

API Endpoints:
  | Método | Endpoint                             | Descrição                     |
  | POST   | /communication/send-email             | Envia email                   |
  | POST   | /communication/send-whatsapp          | Envia WhatsApp                |
  | POST   | /communication/send-screening-invite  | Convite de triagem            |
  | WS     | /ws/chat/{session_id} (communication) | WebSocket conversacional      |

Communication Matrix Triggers:
  | Trigger                    | Canal          | Timing         |
  | match_alto_detectado       | Bell + Email   | Imediato       |
  | triagem_abandonada         | Email          | 24h após início|
  | entrevista_nao_confirmada  | Alerta         | 6h antes       |
  | briefing_2x_dia            | Dashboard      | 08:00 e 14:00  |
  | sla_em_risco               | Alerta         | Quando ultrapassado |
  | sla_violado                | Alerta + Email | Quando violado |

Padrao de Implementacao (13B.7):
  Classe: CommunicationReActAgent(EnhancedAgentMixin, BaseAgent)
  Domain: "communication"
  Tools: get_communication_tools() (5 tools)
  System_prompt: get_communication_system_prompt(guardrails, memory_context)
  Guardrails: 13D.5 — #1-#6 globais + #3 (IA identificada) + #9 (footer IA obrigatório)
  Particularidade: Absorve AnalistaFeedback — PersonalizedFeedbackService é serviço interno, não agente

Camadas de Suporte Obrigatorias:
  | Camada              | Seção  | Arquivos                                           |
  | Comunicação Services| 13C.5  | 23 arquivos (serviço, dispatcher, providers, templates) |
  | Provedores LLM      | 13C.2  | interpret_context_llm_service.py usa LLM             |
  | Config/Infra        | 13C.14 | email_service.py, recruitment_email_templates.py     |

Roteiro de Reproducao (§13C.17):
  1. app/domains/communication/services/communication_service.py
  2. app/domains/communication/services/interpret_context_llm_service.py
  3. app/domains/communication/services/infer_behavior_service.py
  4. app/domains/communication/services/communication_dispatcher.py
  5. app/domains/communication/services/email_service.py
  6. app/domains/communication/services/email_providers/resend_provider.py
  7. app/domains/communication/services/whatsapp_service.py
  8. app/domains/communication/services/whatsapp_meta_service.py
  9. app/domains/communication/services/email_templates_data.py
  10. app/domains/communication/services/transition_dispatch_service.py

Gaps — Funcionalidades Faltantes:
  | Gap                                        | Status     | Impacto                 |
  | Email tracking pixel (abertura/clique)      | ❌ Absent  | 🔴 Implementar do zero  |
  | Feedback diferenciado por Gate (G1≠G2)      | ❌ Absent  | 🟡 Template novo        |

Automacoes Relacionadas:
  | Automação                  | Frequência | Ação                            |
  | CANDIDATE_NO_CONTACT_48H   | 48h        | Email follow-up + tarefa        |
  | CANDIDATE_REJECTED (evento) | Imediato   | Email rejeição + talent pool    |
  | STAGE_CHANGED (evento)      | Imediato   | Comunicação automática          |

Para Alpha 1:
  - Email é canal primário — configurar EmailService com provider real (Resend ou SendGrid)
  - Criar templates Alpha 1: convite triagem, follow-up 7d, feedback Gate 1 (construtivo), feedback Gate 2 (final)
  - Implementar tracking pixel para métricas de abertura/clique
  - Configurar follow-up automático em 7 dias

Arquivos de Referencia:
  - lia-agent-system/app/domains/communication/ (4-file + services — 23 arquivos)
  - lia-agent-system/app/services/communication_dispatcher.py
  - lia-agent-system/app/services/recruitment_email_templates.py
  - lia-agent-system/app/services/email_service.py
  - lia-agent-system/app/domains/communication/services/whatsapp_service.py
```

---

### AGT-006: JD Generator Service — [WT-1565](https://wedotalent.atlassian.net/browse/WT-1565)

```yaml
Titulo: "[AGT-006] JD Generator Service — Geração/Ajuste de Job Description por LLM + FairnessGuard"
Tipo: ReAct Agent + LangGraph StateGraph (dual mode)
Area: Backend
Sprint: S1
Pontos: 5
Prioridade: P1
Epic: É35 (WT-1558)
Tags: [backend, IA, llm, fairness, langgraph, hitl]
Classificação: 🟡 MVP SUPORTE
Dependências: AGT-002, AGT-003
Referências Diagnóstico: §14.2, §4.9, §13B.7, §13C.17

Estado V5 vs LIA:
  V5: Mesma arquitetura dual (wizard_react_agent + jd_generator_service)
  LIA: ReAct conversacional + LangGraph StateGraph com HITL no stage_transition
  Veredicto: Mesma base — adaptar para modo "editar vaga importada do ATS"

Descricao: |
  Dual mode: ReAct (4-file pattern) para interação livre com consultor (criar/editar vaga)
  + LangGraph StateGraph (job_wizard_graph.py) para fluxo guiado passo-a-passo.
  FairnessGuard obrigatório na geração de JD. HITL no stage_transition.

9 Tools com Servicos:
  | Tool                    | O que faz                         | Serviço                              |
  | validate_job_requirements | Valida requisitos da vaga        | FairnessGuard                        |
  | get_salary_benchmarks   | Benchmarks salariais do mercado   | DB Analytics                         |
  | search_salary_benchmark | Busca benchmark salarial          | DB Analytics                         |
  | validate_job_fields     | Valida campos obrigatórios        | Validation rules                     |
  | get_job_suggestions     | Sugestões IA para campos          | LLM                                  |
  | save_job_draft          | Salva rascunho da vaga            | DB: job_vacancies                    |
  | get_company_config      | Configuração da empresa           | DB: companies                        |
  | generate_enriched_jd    | Gera JD enriquecida com IA        | JDGeneratorService + JDEnrichmentSvc |
  | check_job_draft_health  | Verifica completude do draft      | Validation rules                     |

LangGraph — Job Wizard Graph:
  Nós: intent_classifier → field_extractor → tool_router → tool_executor → response_generator → stage_transition → END
  State: JobWizardState { intent, fields{}, current_stage, tool_calls[] }
  Checkpointer: PostgresSaver
  HITL: interrupt_before=["stage_transition"]

Servicos Chamados:
  | Serviço                    | Arquivo                                                     |
  | JDGeneratorService         | app/services/jd_generator_service.py                         |
  | JDEnrichmentService        | app/services/jd_enrichment_service.py                        |
  | JDParserService            | app/services/jd_parser_service.py                            |
  | JDImportService            | app/services/jd_import_service.py                            |
  | JDTemplateService          | app/services/jd_template_service.py                          |
  | JobVacancyService          | app/services/job_vacancy_service.py                          |
  | JobRequirementsService     | app/services/job_requirements_service.py                     |
  | WizardOrchestratorService  | app/domains/job_management/services/wizard_orchestrator.py   |
  | WizardDataPriorityService  | app/domains/job_management/services/wizard_data_priority.py  |

API Endpoints:
  | Método | Endpoint                              | Descrição                     |
  | POST   | /wizard/start                          | Inicia wizard de vaga         |
  | POST   | /wizard/message                        | Envia mensagem ao wizard      |
  | WS     | /ws/chat/{session_id} (domain=wizard)  | WebSocket conversacional      |

Padrao de Implementacao (13B.7):
  Classe: WizardReActAgent(EnhancedAgentMixin, BaseAgent)
  Domain: "job_management"
  Tools: get_job_management_tools() (10 tools)
  System_prompt: get_job_management_system_prompt(guardrails, memory_context)
  Guardrails: 13D.5 — #1-#6 globais (FairnessGuard no JD é crítico)
  Particularidade: Dual ReAct+Graph — job_wizard_graph.py orquestra nós, ReAct escolhe tools dentro de cada nó

Camadas de Suporte Obrigatorias:
  | Camada         | Seção  | Arquivos                                    |
  | Provedores LLM | 13C.2  | llm.py, llm_factory.py, llm_claude.py       |
  | HITL           | 13C.8  | hitl_service.py, HITLConfirmCard.tsx         |
  | Prompts        | 13C.17 | job_management.yaml, lia_persona.yaml       |

Roteiro de Reproducao (§13C.17):
  ReAct (domínio=job_management): 7 arquivos padrão
  HITL (Graph usa HITL): 5 arquivos — §13C.17

Para Alpha 1:
  - Adaptar para modo "editar vaga importada do ATS" (não criar do zero)
  - JDImportService precisa receber dados do ATS e popular o wizard
  - HITL no stage_transition para aprovação de JD

Arquivos de Referencia:
  - lia-agent-system/app/domains/job_management/agents/wizard_react_agent.py
  - lia-agent-system/app/domains/job_management/agents/wizard_tool_registry.py
  - lia-agent-system/app/domains/job_management/agents/wizard_system_prompt.py
  - lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py
  - lia-agent-system/app/services/jd_generator_service.py
```

---

### AGT-017: HiringPolicyService — [WT-1566](https://wedotalent.atlassian.net/browse/WT-1566)

```yaml
Titulo: "[AGT-017] HiringPolicyService — 4 Tools como Serviço + PolicySetupAgent (19 Perguntas)"
Tipo: Serviço (Alpha 1) / ReAct Agent (Pós-Alpha)
Area: Backend
Sprint: S1
Pontos: 5
Prioridade: P1
Epic: É35 (WT-1558)
Tags: [backend, IA, policy, compliance, multi-tenant, fairness]
Classificação: 🟡 MVP SUPORTE
Dependências: AGT-002
Referências Diagnóstico: §14.10, §4.10, §13D.5, §13B.7

Estado V5 vs LIA:
  V5: Mesma arquitetura (policy_react_agent.py)
  LIA: PolicySetupAgent com 19 perguntas, 5 blocos + 13 tools (Alpha 1 usa 4 como serviço)
  Veredicto: Alpha 1 usa 4 tools essenciais como serviço REST. Pós-Alpha ativa agente conversacional completo

Descricao: |
  4 tools como serviço REST interno (sem agente conversacional no Alpha 1).
  Reclassificado de PÓS-ALPHA para Alpha 1 P1 porque: get_current_policy + apply_industry_defaults
  definem defaults, validate_policy_compliance chama FairnessGuard (Inegociável),
  save_policy_block configura regras por cliente. Triagem (Ag.3) e Gates (Ag.9) dependem
  de políticas configuradas.

4 Tools Alpha 1 (modo servico):
  | Tool                       | O que faz                        | Serviço            | Consumidor Alpha 1                     |
  | get_current_policy         | Carrega políticas da empresa     | DB: hiring_policies | Orchestrator, CVScreening, Pipeline     |
  | save_policy_block          | Salva bloco inteiro de política  | DB                 | Setup inicial (onboarding)              |
  | apply_industry_defaults    | Aplica padrões do setor em lote  | DB                 | Setup inicial (onboarding)              |
  | validate_policy_compliance | Verifica viés/violações          | FairnessGuard      | CVScreening (pré-triagem), Pipeline (pré-Gate) |

9 Tools Pos-Alpha (agente conversacional):
  save_policy_field, get_policy_summary, get_company_context, get_industry_benchmarks,
  explain_policy_impact, get_setup_progress, get_platform_benchmarks,
  detect_policy_impact_anomalies, get_policy_effectiveness_report

PolicySetupAgent — 19 Perguntas em 5 Blocos:
  Arquivo: app/domains/policy/agents/agent.py
  System Prompt: EXTRACTION_PROMPT + REPLY_PROMPT
  Tool Registry: POLICY_TOOLS = [] (LLM direto, sem tools)
  Stage Context: QUESTIONS (19), BLOCK_NAMES (5 blocos), PolicySetupSession

API Endpoints:
  | Método | Endpoint                     | Fase      | Descrição                       |
  | REST   | /hiring-policy/current        | Alpha 1   | GET política atual              |
  | REST   | /hiring-policy/apply-defaults | Alpha 1   | POST aplicar defaults do setor  |
  | REST   | /hiring-policy/save-block     | Alpha 1   | POST salvar bloco de política   |
  | REST   | /hiring-policy/validate       | Alpha 1   | POST validar compliance         |
  | WS     | /ws/chat/{session_id} (policy)| Pós-Alpha | WebSocket conversacional        |

Padrao de Implementacao (13B.7):
  Classe: PolicyReActAgent(EnhancedAgentMixin, BaseAgent)
  Domain: "policy"
  Tools: get_policy_tools() (13 tools — Alpha 1: 4 como serviço)
  System_prompt: get_policy_system_prompt(guardrails, memory_context)
  Guardrails: 13D.5 — #1-#6 globais + #13 (policy — alterações requerem confirmação explícita)
  Particularidade: Alpha 1 usa 4 tools como serviço — não instancia ReAct loop. validate_policy_compliance chama FairnessGuard

Roteiro de Reproducao (§13C.17):
  ReAct (domínio=policy): 7 arquivos padrão

Para Alpha 1 (modo servico):
  1. Sprint 1: Expor 4 tools como endpoints REST internos
  2. Sprint 1: Integrar get_current_policy no Orchestrator
  3. Sprint 1: Integrar validate_policy_compliance no CVScreening + PipelineTransition
  4. Sprint 1: Script de onboarding com apply_industry_defaults + save_policy_block

Arquivos de Referencia:
  - lia-agent-system/app/domains/policy/agents/agent.py
  - lia-agent-system/app/domains/policy/agents/system_prompt.py
  - lia-agent-system/app/domains/policy/agents/tool_registry.py
  - lia-agent-system/app/domains/policy/agents/stage_context.py
  - lia-agent-system/app/api/v1/pipeline_policy.py
```

---

### AGT-015: PipelineGateService — [WT-1567](https://wedotalent.atlassian.net/browse/WT-1567)

```yaml
Titulo: "[AGT-015] PipelineGateService — Gate 1 + Gate 2 + HITL Trigger + Bypass Inscrição Web"
Tipo: ReAct Agent (4-file pattern) + HITL inline
Area: Backend
Sprint: S1
Pontos: 8
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Tags: [backend, IA, pipeline, hitl, compliance, fairness, auditoria]
Classificação: 🟢 MVP CRÍTICO
Dependências: AGT-002, AGT-003
Sobreposição: SAT-007 — camada complementar
Referências Diagnóstico: §14.9, §4.9, §6, §13C.8, §13D.5

Estado V5 vs LIA:
  V5: Mesma arquitetura (pipeline_transition_agent.py), mas sem HITL e sem StageAutomationEngine
  LIA: ReAct com 20 tools + HITL inline + FairnessGuard + AuditCallback
  Veredicto: LIA é mais completa — agente com mais tools (20) e único ReAct com HITL inline

Descricao: |
  ReAct Agent com HITL inline. Gates 1 e 2, regras de transição, HITL obrigatório.
  Inscrição web bypassa Gate 1. Tools como approve_candidate, reject_candidate,
  move_to_gate pausam para confirmação do consultor via PendingActions.
  Complementa SAT-007 com triggers automáticos e HITL.

20 Tools com Servicos:
  | Tool                       | O que faz                          | Serviço                |
  | get_candidate_profile      | Perfil completo                    | DB: candidates         |
  | get_candidate_wsi_scores   | Scores WSI                         | DB: wsi_scores         |
  | get_candidate_screening    | Resultados de triagem              | DB: screening_results  |
  | get_candidate_salary_info  | Info salarial                      | DB: candidate_salary   |
  | update_candidate_field     | Atualiza campo do candidato        | DB: candidates         |
  | request_data_collection    | Solicita coleta de dados           | DataCollectionService  |
  | get_stage_sub_statuses     | Sub-status do estágio              | DB: pipeline_stages    |
  | suggest_sub_status         | Sugere sub-status                  | LLM                    |
  | extract_preferences        | Extrai preferências do recrutador  | NLP                    |
  | validate_transition        | Valida transição de estágio        | PolicyEngine + FairnessGuard |
  | get_job_context            | Contexto da vaga                   | DB: job_vacancies      |
  | schedule_secondary_task    | Agenda tarefa secundária           | PlannedTaskService     |
  | personalize_communication  | Personaliza comunicação            | LLM                    |
  | check_rejection_fairness   | Verifica viés na rejeição          | FairnessGuard (SOX)    |
  | check_candidate_availability | Disponibilidade do candidato     | CalendarService        |
  | get_recruiter_preferences  | Preferências do recrutador         | DB: recruiter_prefs    |
  | save_recruiter_preference  | Salva preferência                  | DB: recruiter_prefs    |
  | get_interview_details      | Detalhes da entrevista             | CalendarService        |
  | cancel_interview           | Cancela entrevista                 | CalendarService        |
  | reschedule_interview       | Reagenda entrevista                | CalendarService        |

Servicos Chamados:
  | Serviço                  | Arquivo                                           |
  | PipelineService          | app/services/pipeline_service.py                   |
  | PipelineStageService     | app/services/pipeline_stage_service.py              |
  | CommunicationDispatcher  | app/services/communication_dispatcher.py            |
  | CalendarService          | app/domains/interview_scheduling/services/calendar_service.py |
  | FairnessGuard            | app/shared/agents/fairness_guard.py                |
  | HITLService              | app/services/hitl_service.py                       |

HITL Behavior:
  Acoes que requerem aprovacao humana: move (estágios avançados), reject, offer
  Endpoint: POST /hitl/{thread_id}/approve, GET /hitl/{thread_id}/pending
  Fluxo: Agent propõe → HITL pending → Recrutador aprova/rejeita → Agent executa

API Endpoints:
  | Método | Endpoint                                    | Descrição                     |
  | POST   | /recruitment-stages/*                        | Pipeline transition endpoints |
  | POST   | /hitl/{thread_id}/approve                    | Aprova ação pendente          |
  | GET    | /hitl/{thread_id}/pending                    | Lista ações pendentes         |
  | WS     | /ws/chat/{session_id} (pipeline_transition)  | WebSocket                     |

Automacoes Relacionadas:
  | Automação                  | Frequência | Ação                              |
  | STAGE_CHANGED (evento)      | Imediato   | Log transição + auto-agenda       |
  | CANDIDATE_REJECTED (evento) | Imediato   | Email rejeição + talent pool      |
  | CANDIDATE_HIRED (evento)    | Imediato   | Sync ATS + onboarding             |
  | OFFER_SENT (evento)         | Imediato   | Monitora resposta                 |
  | JOB_NO_MOVEMENT_5D          | 5 dias     | Alerta vaga estagnada             |

Padrao de Implementacao (13B.7):
  Classe: PipelineTransitionAgent(EnhancedAgentMixin, BaseAgent)
  Domain: "pipeline"
  Tools: get_pipeline_transition_tools() (20 tools)
  System_prompt: get_pipeline_system_prompt(guardrails, memory_context)
  Guardrails: 13D.5 — #1-#6 globais + #5 (rejeição sem HITL proibida) + #11 (gate humano antes de rejeição em massa)
  Particularidade: ReAct + HITL — validate_transition chama PolicyEngine + FairnessGuard. Maior contagem de tools Alpha 1 (20)

Camadas de Suporte Obrigatorias:
  | Camada       | Seção  | Arquivos                                              |
  | HITL         | 13C.8  | 7 arquivos (BE + FE — core deste agente)              |
  | Robustez     | 13C.3  | FairnessGuard (check_rejection_fairness), Audit Trail |
  | Comunicação  | 13C.5  | Dispatch automático em transições de pipeline          |
  | Qualidade    | 13C.9  | AgentQualityEvaluator (decisões de Gate auditoráveis)  |

Roteiro de Reproducao (§13C.17):
  ReAct (domínio=pipeline): 7 arquivos padrão
  HITL: 5 arquivos — §13C.17

Para Alpha 1:
  - Configurar para Gate 1 (pós-triagem CV) e Gate 2 (pós-WSI)
  - Gate 1: HITL obrigatório antes de aprovar/rejeitar
  - Gate 2: HITL obrigatório + fairness check antes de rejeitar
  - Garantir que check_rejection_fairness funciona com FairnessGuard

Arquivos de Referencia:
  - lia-agent-system/app/domains/pipeline/agents/pipeline_transition_react_agent.py
  - lia-agent-system/app/domains/pipeline/agents/pipeline_tool_registry.py
  - lia-agent-system/app/services/pipeline_service.py
  - lia-agent-system/app/services/hitl_service.py
  - lia-agent-system/app/domains/automation/services/pipeline_monitor.py
```

---

### AGT-007: WSIInterviewGraph — [WT-1568](https://wedotalent.atlassian.net/browse/WT-1568)

```yaml
Titulo: "[AGT-007] WSIInterviewGraph — Entrevista WSI Completa (7 Blocos + 15 Serviços + Scoring)"
Tipo: LangGraph StateGraph
Area: Backend
Sprint: S2
Pontos: 21
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Tags: [backend, IA, langgraph, wsi, scoring, fairness, lgpd, hitl]
Classificação: 🟢 MVP CRÍTICO — Card mais complexo do Alpha 1
Dependências: AGT-002, AGT-005, AGT-009
Sobreposição: TRI-005 — AGT-007 detalha a implementação LangGraph
Referências Diagnóstico: §14.5, §4.4, §13B.10, §13C.17, §13C.9, §13D

Estado V5 vs LIA:
  V5: Mesma arquitetura (wsi_interview_graph.py + 15 serviços)
  LIA: WSIInterviewGraph com 7 blocos, 15 serviços (9.621 linhas), scoring determinístico (558L)
  Veredicto: Mesma base — LIA é mais madura (~9.6k linhas de implementação)

Camadas de Suporte Obrigatorias:
  | Camada            | Seção  | Arquivos                                          |
  | WSI Services      | 13B.10 | 18 arquivos (pipeline, scorer, questions, feedback) |
  | Provedores LLM    | 13C.2  | llm.py (geração de perguntas e feedback)            |
  | Compliance        | 13C.3  | FairnessGuard (perguntas não-discriminatórias)      |
  | HITL              | 13C.8  | interrupt_before=["generate_feedback"]              |
  | Qualidade         | 13C.9  | AgentQualityEvaluator (avalia qualidade das respostas) |

Roteiro de Reproducao (§13C.17):
  WSI (8 arquivos): §13C.17
  1. app/services/wsi_screening_pipeline.py
  2. app/services/wsi_deterministic_scorer.py (558L CRÍTICO)
  3. app/services/wsi_question_generator.py
  4. app/services/wsi_session_manager.py
  5. app/services/wsi_state_machine.py
  6. app/services/wsi_block_navigator.py
  7. app/services/wsi_response_validator.py
  8. app/services/wsi_report_generator.py

Descricao: |
  LangGraph StateGraph que conduz entrevista WSI completa. 7 blocos
  (Apresentação → Elegibilidade → Técnico → Comportamental CBI → Simulação
  → Fit Cultural → Encerramento). 15 serviços WSI (~9.621 linhas no LIA).
  Scoring determinístico: Score = (0.6×Autodec) + (0.4×Context) - Penalty + Bonus.

7 Blocos WSI:
  1. Apresentação — Contexto empresa/vaga (informativo)
  2. Elegibilidade — CLT, PCD, localização (eliminatório)
  3. Técnico — Hard skills (0.6×Autodec)
  4. Comportamental CBI — STAR method (0.6×Autodec + 0.4×Context)
  5. Simulação — Caso prático (0.6×Autodec + 0.4×Context + Bonus)
  6. Fit cultural — Valores (0.4×Context)
  7. Encerramento — Próximos passos (informativo)

15 Servicos WSI:
  - WSI Screening Pipeline, Deterministic Scorer (558L CRÍTICO),
    Question Generator, Feedback Generator, Calibration Profiles,
    Bloom Taxonomy, Dreyfus Assessor, Big Five Analyzer,
    CBI Question Bank (200+), Session Manager, State Machine,
    Block Navigator, Response Validator, Report Generator,
    Personalized Feedback

LangGraph Estrutura:
  State: WSIState { session_id, job_id, company_id, candidate_id,
                    current_block, questions[], answers[], scores{}, status }
  Nós: load_context → generate_question → deliver_question →
       validate_response → score_response → advance_block →
       generate_feedback → END
  Checkpointer: PostgresSaver (obrigatório)
  HITL: interrupt_before=["generate_feedback"]

Arquivos de Referencia:
  - lia-agent-system/app/services/wsi_screening_pipeline.py
  - lia-agent-system/app/services/wsi_deterministic_scorer.py (558L — CRÍTICO)
  - lia-agent-system/app/services/wsi_question_generator.py
  - lia-agent-system/app/services/wsi_service.py
  - lia-agent-system/app/api/v1/wsi_screening_pipeline_endpoint.py
```

---

### AGT-008: CVScreeningReActAgent — [WT-1569](https://wedotalent.atlassian.net/browse/WT-1569)

```yaml
Titulo: "[AGT-008] CVScreeningReActAgent — Triagem Curricular com 13 Tools"
Tipo: ReAct Agent (4-file pattern)
Area: Backend
Sprint: S2
Pontos: 8
Prioridade: P1
Epic: É35 (WT-1558)
Tags: [backend, IA, react-agents, cv-screening, fairness, compliance]
Classificação: 🟡 MVP SUPORTE
Dependências: AGT-002, AGT-007
Referências Diagnóstico: §14.4, §4.3, §13C.7, §13B.7, §13C.17

Estado V5 vs LIA:
  V5: Não existe como agente separado — scoring básico em evaluation domain
  LIA: ReAct puro (4-file pattern) com 13 tools (triagem CV, scoring, matching)
  Veredicto: LIA tem, V5 não — construir seguindo padrão LIA

Descricao: |
  Agente ReAct puro (4-file pattern) de triagem de CV. Análise documental
  (não conversacional — diferente do WSI Graph §14.5 que faz entrevista).
  13 tools incluem: parse CV, score matching, extrair skills, run WSI screening.
  FairnessGuard wiring crítico + PromptInjectionGuard + HITL para Gates.

13 Tools com Servicos:
  | Tool                   | O que faz                          | Serviço                   |
  | view_candidate_profile | Perfil completo do candidato       | DB: candidates            |
  | move_candidate         | Muda estágio no pipeline           | DB + HITLService          |
  | analyze_cv             | Extrai skills/score do CV          | CVParser + AI Analysis    |
  | run_wsi_screening      | Triagem comportamental WSI         | WSIService                |
  | schedule_interview     | Agenda entrevista                  | CalendarService           |
  | send_communication     | Envia comunicação ao candidato     | CommunicationService      |
  | add_notes              | Adiciona notas ao perfil           | DB: candidate_notes       |
  | batch_move             | Move múltiplos candidatos          | DB batch                  |
  | add_to_shortlist       | Adiciona à shortlist               | DB: vacancy_candidates    |
  | view_screening_results | Visualiza resultados de triagem    | DB: screening_results     |
  | view_interview_notes   | Notas da entrevista                | DB: interview_notes       |
  | generate_offer         | Cria proposta de contratação       | Offer Generation Service  |
  | finalize_hiring        | Registra admissão                  | Core Recruitment          |

Servicos Chamados:
  | Serviço                  | Arquivo                                           |
  | CVParser                 | app/services/cv_parser.py                          |
  | CVScoringService         | app/services/cv_scoring_service.py                 |
  | RubricEvaluationService  | app/services/rubric_evaluation_service.py           |
  | EvaluationCriteriaService| app/services/evaluation_criteria_service.py         |
  | WSIScreeningPipeline     | app/domains/cv_screening/services/wsi_screening_pipeline.py |
  | HITLService              | app/services/hitl_service.py                       |
  | FairnessGuard            | app/shared/agents/fairness_guard.py                |

API Endpoints:
  | Método | Endpoint                                    | Descrição                     |
  | POST   | /automation/screen-candidate                 | Triagem curricular (Rubric/BARS) |
  | POST   | /automation/handle-trigger/screening-completed| Pós-triagem (Bloom+Dreyfus+Big5)|
  | WS     | /ws/chat/{session_id} (domain=pipeline)      | WebSocket conversacional      |

Padrao de Implementacao (13B.7):
  Classe: PipelineReActAgent(EnhancedAgentMixin, BaseAgent)
  Domain: "cv_screening"
  Tools: get_pipeline_tools() (13 tools)
  System_prompt: get_pipeline_system_prompt(guardrails, memory_context) — inclui FAIRNESS_RULES + COMMUNICATION_TRANSPARENCY_RULES
  Guardrails: 13D.5 — #1-#6 globais + #11 (pipeline — gate humano antes de rejeição em massa)
  Particularidade: FairnessGuard wiring crítico (13D.1) + PromptInjectionGuard (13D) + HITL para Gates

Camadas de Suporte Obrigatorias:
  | Camada          | Seção  | Arquivos                                               |
  | CV Screening Svc| 13C.7  | 5 arquivos (cv_parser, scoring, batch, questions)       |
  | WSI Services    | 13B.10 | 18 arquivos (pipeline WSI completo)                     |
  | Robustez        | 13C.3  | input_validation.py, response_filter.py (PromptInjection)|
  | HITL            | 13C.8  | hitl_service.py (Gate 1/2 precisam aprovação humana)    |

Gaps V5 Aplicaveis:
  | Gap V5                                               | Impacto                          |
  | Multi-Stage Eval Graph (4 nós: classify→evaluate→decide→craft) | 🟡 V5 tem graph de avaliação |
  | Security Guard (detecção prompt injection em inputs candidatos)  | 🟡 LIA tem mas não integrado |

Roteiro de Reproducao (§13C.17):
  ReAct (domínio=cv_screening): 7 arquivos padrão

Para Alpha 1:
  - Integrar PromptInjectionGuard no fluxo de screening (antes de processar input do candidato)
  - Configurar para fluxo Alpha 1: triagem CV → score → Gate 1 (HITL)
  - Garantir que move_candidate aciona triggers automáticos (StageAutomationEngine)

Arquivos de Referencia:
  - lia-agent-system/app/domains/cv_screening/agents/ (4-file)
  - lia-agent-system/app/domains/cv_screening/services/
  - lia-agent-system/app/services/cv_parser.py
  - lia-agent-system/app/services/cv_scoring_service.py
  - lia-agent-system/app/services/rubric_evaluation_service.py
```

---

### AGT-009: Chat Web Canal — [WT-1570](https://wedotalent.atlassian.net/browse/WT-1570)

```yaml
Titulo: "[AGT-009] Chat Web Canal — WebSocket Backend para Triagem do Candidato"
Tipo: Infra/Canal
Area: Backend
Sprint: S2
Pontos: 8
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Tags: [backend, IA, websocket, lgpd, compliance, prompt-injection]
Classificação: 🟢 MVP CRÍTICO
Dependências: AGT-007, AGT-002
Sobreposição: TRI-002 — AGT-009 é o backend WebSocket
Referências Diagnóstico: §5.3, §7, §13C.17, §13D

Estado V5 vs LIA:
  V5: chat_router.py + chat_controller.py (FastAPI WebSocket)
  LIA: orchestrated_talent_chat.py + orchestrated_job_chat.py (2 endpoints WS distintos)
  Veredicto: Mesma abordagem — adaptar LIA: 1 endpoint WS unificado com domain routing

Descricao: |
  Canal WebSocket para triagem WSI do candidato. Link único /triagem/{token},
  sessões de 10-30min. PromptInjectionGuard em TODAS mensagens do candidato
  (alto risco — input externo não confiável). PostgresSaver para retomada de
  sessão após queda de conexão. Banner LGPD obrigatório no início.

Fluxo WebSocket:
  1. Candidato acessa /triagem/{token} → frontend conecta via WS
  2. Backend valida token → carrega sessão WSI (ou cria nova)
  3. Cada mensagem: PromptInjectionGuard.check() → WSIGraph.process()
  4. Respostas em streaming (token a token) via WS
  5. Desconexão → sessão salva em PostgresSaver → candidato retoma pelo mesmo link

Seguranca Obrigatoria:
  | Controle                | Implementação                    | Motivo                      |
  | PromptInjectionGuard    | Antes de cada mensagem do candidato | Input não confiável — alto risco |
  | Token validation        | JWT com exp de 48h                | Acesso sem login             |
  | Rate limiting           | Max 60 msgs/min por sessão        | Anti-spam                    |
  | PII Masking             | Logs sem dados pessoais do candidato | LGPD Art. 46              |
  | Banner LGPD             | Primeira mensagem automática       | Consentimento               |

API Endpoints:
  | Método | Endpoint                                    | Descrição                     |
  | WS     | /ws/triagem/{token}                          | WebSocket candidato (triagem WSI) |
  | GET    | /triagem/{token}/status                      | Status da sessão               |
  | POST   | /triagem/{token}/reconnect                   | Reconexão após queda          |

Camadas de Suporte Obrigatorias:
  | Camada            | Seção  | Arquivos                                    |
  | WebSocket Infra   | 13C.14 | orchestrated_talent_chat.py, starlette WS    |
  | WSI Graph         | 13B.10 | wsi_interview_graph.py (§14.5)               |
  | Compliance        | 13C.3  | prompt_injection.py, pii_masking.py           |
  | Checkpointer      | 13C.14 | PostgresSaver (retomada de sessão)            |

Roteiro de Reproducao (§13C.17):
  Orquestrador (9 arquivos): §13C.17

Gaps — Funcionalidades Faltantes:
  | Gap                                 | Status     | Impacto                 |
  | Reconexão automática no backend     | ❌ Absent  | 🔴 Implementar do zero  |
  | Rate limiting por sessão WS         | ❌ Absent  | 🟡 Implementar           |

Para Alpha 1:
  - Endpoint WS unificado /ws/triagem/{token}
  - PromptInjectionGuard em cada mensagem (OBRIGATÓRIO — candidato é input externo)
  - PostgresSaver para retomada (candidato pode perder conexão durante triagem de 10-30min)
  - Banner LGPD automático na primeira mensagem
  - Streaming token a token para UX responsiva

Arquivos de Referencia:
  - lia-agent-system/app/api/v1/orchestrated_talent_chat.py
  - lia-agent-system/app/api/v1/orchestrated_job_chat.py
  - lia-agent-system/app/shared/prompt_injection.py
```

---

### AGT-016: EventRetryOrchestrator — [WT-1571](https://wedotalent.atlassian.net/browse/WT-1571)

```yaml
Titulo: "[AGT-016] EventRetryOrchestrator — Celery Scheduler (10 Jobs + 8 Triggers + 5 Proativos) + DLQ"
Tipo: Serviço (Scheduler infra — não agente conversacional)
Area: Backend
Sprint: S2
Pontos: 8
Prioridade: P1
Epic: É35 (WT-1558)
Tags: [backend, IA, celery, automação, rabbitmq, lgpd]
Classificação: 🟡 MVP SUPORTE
Dependências: AGT-002
Referências Diagnóstico: §14.14, §7, §13C.17

Estado V5 vs LIA:
  V5: Mesma arquitetura (automation_scheduler.py + stage_automation_engine.py)
  LIA: AutomationScheduler (10 jobs) + StageAutomationEngine (8 triggers) + 5 triggers proativos
  Veredicto: Dual mode no Alpha 1 — agente conversacional NÃO entra, mas 10 jobs + 8 triggers + 5 proativos RODAM como infra

Descricao: |
  Infraestrutura background que roda sem agente conversacional.
  AutomationScheduler (10 jobs agendados) + StageAutomationEngine (8 triggers por evento) +
  AutomationTriggerService (5 triggers proativos por tempo) + DLQ para falhas.
  Roda via Celery Beat + RabbitMQ.

10 Jobs Agendados:
  | Job                        | Frequência   | O que faz                          |
  | check_inactive_candidates  | A cada 1h    | Candidatos sem atividade 7+ dias   |
  | check_interview_no_shows   | A cada 30m   | Detecta no-shows de entrevista     |
  | send_interview_reminders   | A cada 15m   | Lembretes 24h/1h antes             |
  | check_expiring_vacancies   | Diário 09:00 | Vagas próximas do deadline         |
  | cleanup_stale_reminders    | Diário 00:00 | Limpa flags obsoletos              |
  | auto_complete_screenings   | A cada 1h    | Triagens expiradas → timeout       |
  | pipeline_monitor           | A cada 30m   | Saúde do pipeline (gargalos)       |
  | learning_automation        | A cada 6h    | Padrões e promoção de skills       |
  | expire_trials              | Diário 01:00 | Trials expirados → bloqueio        |
  | run_lgpd_cleanup           | Diário 02:00 | Cleanup LGPD (dados expirados)     |

8 Triggers por Evento:
  | Evento                  | Ação                                      |
  | SCREENING_COMPLETED     | Log + email feedback ao candidato          |
  | STAGE_CHANGED           | Log transição + auto-agenda se Interview   |
  | CANDIDATE_REJECTED      | Email rejeição + adiciona ao talent pool   |
  | INTERVIEW_SCHEDULED     | Confirmação + evento no calendário         |
  | INTERVIEW_COMPLETED     | Parecer IA (LLM)                           |
  | CANDIDATE_HIRED         | Sync ATS + onboarding                      |
  | OFFER_SENT              | Monitora resposta (polling)                |
  | ATS_SYNC                | Sincroniza com ATS externo                 |

5 Triggers Proativos por Tempo:
  | Trigger                    | Threshold | Ação                          |
  | CANDIDATE_NO_CONTACT_48H   | 48h       | Follow-up + tarefa            |
  | SCORECARD_PENDING_24H      | 24h       | Notifica entrevistador        |
  | JOB_NO_MOVEMENT_5D         | 5 dias    | Alerta vaga estagnada         |
  | FEEDBACK_PENDING_48H       | 48h       | Escalação prioridade alta     |
  | JOB_DEADLINE_APPROACHING   | 3 dias    | Alerta severidade alta        |

API Endpoints:
  | Método | Endpoint                    | Descrição                     |
  | POST   | /automation/trigger-event    | Dispara evento manualmente    |
  | REST   | /tasks/*                     | CRUD de tarefas agendadas     |
  | REST   | /proactive-actions/*         | Ações proativas (autonomous)  |
  | REST   | /transition/*                | Stage transition automática   |

Servicos Chamados:
  | Serviço                   | Arquivo                                                    |
  | AutomationScheduler       | app/domains/automation/services/automation_scheduler.py      |
  | StageAutomationEngine     | app/domains/automation/services/stage_automation_engine.py    |
  | AutomationTriggerService  | app/domains/automation/services/automation_trigger_service.py |
  | AutomationHandlers        | app/domains/automation/services/automation_handlers.py        |
  | CeleryApp                 | app/core/celery_app.py                                       |
  | PipelineMonitor           | app/domains/automation/services/pipeline_monitor.py           |

Camadas de Suporte Obrigatorias:
  | Camada            | Seção  | Arquivos                                    |
  | Celery + RabbitMQ | 13C.14 | celery_app.py, celery_config.py              |
  | Comunicação       | 13C.5  | communication_dispatcher.py (emails automáticos) |
  | Compliance        | 13C.3  | pii_masking.py (logs de jobs)                |

Roteiro de Reproducao (§13C.17):
  Arquivo de entrada: app/domains/automation/services/automation_scheduler.py
  Entende dependências: stage_automation_engine.py, automation_trigger_service.py
  Configura: Celery Beat schedule em celery_app.py

Para Alpha 1 (Jobs Prioritarios):
  - check_inactive_candidates (follow-up 7d)
  - auto_complete_screenings (triagem timeout 48h)
  - check_interview_no_shows (no-show detection)
  - send_interview_reminders (lembretes de entrevista)
  - run_lgpd_cleanup (compliance LGPD obrigatório)
  - SCREENING_COMPLETED + STAGE_CHANGED + CANDIDATE_REJECTED (3 triggers prioritários)

Arquivos de Referencia:
  - lia-agent-system/app/core/celery_app.py
  - lia-agent-system/app/shared/messaging/celery_config.py
  - lia-agent-system/app/domains/automation/services/automation_scheduler.py
  - lia-agent-system/app/domains/automation/services/stage_automation_engine.py
  - lia-agent-system/app/domains/automation/services/automation_trigger_service.py
  - lia-agent-system/app/domains/automation/services/pipeline_monitor.py
```

---

### AGT-010: Follow-up 7d + Email Tracking — [WT-1572](https://wedotalent.atlassian.net/browse/WT-1572)

```yaml
Titulo: "[AGT-010] Follow-up 7 Dias + Email Tracking (Pixel + Redirect)"
Tipo: Serviço (funcionalidade NOVA)
Area: Backend
Sprint: S2
Pontos: 8
Prioridade: P1
Epic: É35 (WT-1558)
Tags: [backend, IA, email, automação, celery, lgpd, tracking]
Classificação: 🟡 MVP SUPORTE
Dependências: AGT-005, AGT-016
Referências Diagnóstico: §7, §5.3

Estado V5 vs LIA:
  V5: NÃO EXISTE — funcionalidade totalmente nova
  LIA: NÃO EXISTE — funcionalidade totalmente nova
  Veredicto: Implementar do zero — gap identificado como necessário para Alpha 1

Descricao: |
  Funcionalidade NOVA (não existe em V5 nem LIA). Re-envio automático a cada
  24h × 7 dias para candidatos que não responderam ao convite de triagem.
  Tracking de email: pixel 1×1 GIF para detectar abertura, redirect link para
  detectar clique. LGPD: limitar número de re-envios + link de opt-out obrigatório
  em todo email. Integrado com AGT-016 (Celery Beat) e AGT-005 (EmailService).

Fluxo:
  1. Convite de triagem enviado (AGT-005)
  2. Celery Beat job: check_inactive_candidates (a cada 1h)
  3. Se candidato não respondeu em 24h → re-envio automático
  4. Repetir até 7 dias ou resposta
  5. Após 7d sem resposta → alerta ao consultor

Email Tracking:
  | Tipo          | Implementação                    | O que detecta           |
  | Abertura      | Pixel 1×1 GIF com ID único       | Candidato abriu o email |
  | Clique        | Redirect URL com token tracking  | Candidato clicou no link|
  | Bounce        | Webhook do provedor (Resend)     | Email não entregue      |

Tabelas Necessarias (NOVAS):
  | Tabela                 | Campos chave                                           |
  | email_tracking_events  | id, email_id, event_type, timestamp, ip, user_agent    |
  | email_followup_status  | id, candidate_id, job_id, send_count, last_sent, opted_out |

API Endpoints:
  | Método | Endpoint                          | Descrição                     |
  | GET    | /tracking/pixel/{tracking_id}.gif  | Pixel de abertura (1×1 GIF)   |
  | GET    | /tracking/click/{tracking_id}      | Redirect com tracking         |
  | POST   | /tracking/webhook/resend           | Webhook bounce/delivery       |
  | POST   | /email/opt-out/{token}             | Candidato cancela follow-up   |

LGPD Compliance:
  - Link de opt-out obrigatório em todo email
  - Máximo 7 re-envios (1/dia × 7 dias)
  - Logs de tracking sem PII (PIIMasking)
  - Retenção de tracking events: 90 dias

Para Alpha 1:
  - Criar tabelas email_tracking_events e email_followup_status
  - Implementar pixel tracking (endpoint GET que retorna 1×1 GIF transparente)
  - Implementar redirect tracking (endpoint GET que redireciona + registra)
  - Integrar com Celery Beat job check_inactive_candidates (AGT-016)
  - Configurar opt-out obrigatório

Arquivos de Referencia:
  - Nenhum existente — funcionalidade totalmente nova
  - Dependências: AGT-005 (EmailService), AGT-016 (Celery Beat)
```

---

### AGT-FE-001: Chat Web UI — [WT-1573](https://wedotalent.atlassian.net/browse/WT-1573)

```yaml
Titulo: "[AGT-FE-001] Chat Web UI — Interface do Candidato para Triagem WSI"
Tipo: Frontend
Area: Frontend
Sprint: S2
Pontos: 8
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Tags: [frontend, IA, react, nextjs, websocket, lgpd, mobile-first, acessibilidade]
Classificação: 🟢 MVP CRÍTICO
Dependências: AGT-009, AGT-007
Sobreposição: TRI-002 — camada complementar de IA
Referências Diagnóstico: Design System v4.2.1, §13F, §13C.8 FE

Estado V5 vs LIA:
  V5: Não existe — construir do zero
  LIA: Componentes existentes (ChatContainer, MessageBubble, InputBar, WelcomeCard, use-triagem-chat)
  Veredicto: Usar componentes LIA existentes como base — adaptar para DS v4.2.1

Descricao: |
  Interface web mobile-first para candidato. Link único /triagem/{token},
  sem login. Streaming token a token via WebSocket (AGT-009),
  indicador de progresso "Bloco 2/5 • Pergunta 3/6", banner LGPD,
  identificação IA ("Gerado pela LIA"), reconexão automática.
  Design System v4.2.1: monocromático, cyan #60BED1 apenas ícone LIA,
  dark mode suportado.

Componentes:
  | Componente         | Responsabilidade                          | DS v4.2.1                |
  | CandidateChat      | Container principal do chat               | bg-gray-950, rounded-lg  |
  | MessageBubble      | Mensagem individual (IA vs candidato)     | Cores distintas por tipo |
  | InputBar           | Campo de entrada de texto                 | border-gray-700          |
  | ProgressIndicator  | "Bloco 2/5 • Pergunta 3/6"               | text-gray-400            |
  | ConsentBanner      | Banner LGPD + consentimento               | bg-yellow-900/20         |
  | WelcomeCard        | Boas-vindas + contexto da empresa/vaga    | Card com logo empresa    |
  | ReconnectionBanner | Aviso de reconexão após queda             | bg-red-900/20            |

WebSocket Integration:
  Hook: use-candidate-chat.ts
  Conecta: WS /ws/triagem/{token}
  Streaming: onmessage → append token a token
  Reconexão: Auto-reconnect com backoff exponencial (1s, 2s, 4s, 8s max)
  Estado: idle | connecting | connected | reconnecting | error

LGPD Obrigatorio:
  - ConsentBanner no início (antes da primeira pergunta)
  - Texto: "Esta triagem é conduzida pela LIA (IA da WeDo Talent). Seus dados..."
  - Botão "Aceitar e continuar" obrigatório
  - Footer: "Gerado pela LIA — assistente de IA da WeDo Talent"

Acessibilidade:
  - ARIA labels em todos elementos interativos
  - Suporte a screen reader (aria-live="polite" para novas mensagens)
  - Contraste WCAG AA mínimo
  - Navegação por teclado (Tab + Enter)

Arquivos a Criar:
  - src/app/triagem/[token]/page.tsx
  - src/components/chat/CandidateChat.tsx
  - src/components/chat/ConsentBanner.tsx
  - src/components/chat/ProgressIndicator.tsx
  - src/components/chat/ReconnectionBanner.tsx
  - src/hooks/use-candidate-chat.ts
  - src/lib/session-token.ts

Para Alpha 1:
  - Mobile-first (candidato acessa pelo celular)
  - Streaming token a token (UX responsiva)
  - ProgressIndicator (candidato sabe quanto falta)
  - ConsentBanner LGPD obrigatório
  - Reconexão automática (sessão de 10-30min pode cair)

Arquivos de Referencia:
  - plataforma-lia/src/components/triagem/ChatContainer.tsx
  - plataforma-lia/src/components/triagem/MessageBubble.tsx
  - plataforma-lia/src/components/triagem/InputBar.tsx
  - plataforma-lia/src/components/triagem/WelcomeCard.tsx
  - plataforma-lia/src/hooks/use-triagem-chat.ts
```

---

### AGT-FE-002: HITLConfirmCard — [WT-1574](https://wedotalent.atlassian.net/browse/WT-1574)

```yaml
Titulo: "[AGT-FE-002] HITLConfirmCard — Aprovação do Consultor no Chat (5 Estados)"
Tipo: Frontend Component
Area: Frontend
Sprint: S2
Pontos: 5
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Tags: [frontend, IA, react, hitl, websocket, auditoria]
Classificação: 🟢 MVP CRÍTICO
Dependências: AGT-011 (HITL wiring), AGT-001 (WebSocket)
Referências Diagnóstico: §13C.8, CLAUDE.md Sprint J, §13B.9

Estado V5 vs LIA:
  V5: Não existe — construir do zero
  LIA: HITLConfirmCard.tsx existente com 5 estados
  Veredicto: Usar componente LIA existente — adaptar para DS v4.2.1

Descricao: |
  Componente React no chat do consultor para aprovação HITL.
  5 estados: pending (botões Aprovar/Rejeitar), loading (spinner),
  approved (badge verde ✓), rejected (badge vermelho ✗ + campo de comentário),
  expired (>24h — badge cinza). Renderizado inline no chat quando o backend
  emite hitl_request via WebSocket.

5 Estados do Componente:
  | Estado    | UI                                      | Ação                           |
  | pending   | Botões "Aprovar" + "Rejeitar" + resumo   | Aguarda decisão do consultor   |
  | loading   | Spinner + "Processando..."               | Enviando decisão ao backend    |
  | approved  | Badge verde ✓ + "Aprovado por [nome]"    | Ação executada com sucesso     |
  | rejected  | Badge vermelho ✗ + comentário obrigatório | Ação rejeitada com justificativa |
  | expired   | Badge cinza + "Expirado (>24h)"          | TTL expirou sem decisão        |

Fluxo WebSocket:
  1. Backend emite: { type: "hitl_request", action: "move_candidate", data: {...} }
  2. Frontend renderiza HITLConfirmCard no chat (estado: pending)
  3. Consultor clica "Aprovar" ou "Rejeitar" (+ comentário se rejeitar)
  4. Frontend envia: POST /hitl/{thread_id}/approve { approved: true/false, comment }
  5. Backend processa → emite resultado via WS → Card muda para approved/rejected

Props do Componente:
  | Prop           | Tipo     | Descrição                     |
  | threadId       | string   | ID do thread LangGraph         |
  | action         | string   | Ação proposta (move, reject)   |
  | description    | string   | Resumo legível da ação         |
  | candidateName  | string   | Nome do candidato afetado      |
  | data           | object   | Dados completos da ação        |
  | expiresAt      | Date     | Quando expira (TTL 24h)        |
  | onApprove      | function | Callback de aprovação          |
  | onReject       | function | Callback de rejeição           |

Design System v4.2.1:
  - Background: bg-gray-800 (dark mode)
  - Border: border-gray-700
  - Botão Aprovar: bg-green-600 hover:bg-green-700
  - Botão Rejeitar: bg-red-600 hover:bg-red-700
  - Badge aprovado: text-green-400
  - Badge rejeitado: text-red-400
  - Badge expirado: text-gray-500

Para Alpha 1:
  - 5 estados completos funcionais
  - Comentário obrigatório na rejeição (auditoria)
  - TTL 24h com expiração visual
  - Integração com WebSocket do chat do consultor

Arquivos de Referencia:
  - plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx
  - plataforma-lia/src/hooks/use-float-streaming.ts
```

---

### AGT-011: Gate HITL Wiring — [WT-1575](https://wedotalent.atlassian.net/browse/WT-1575)

```yaml
Titulo: "[AGT-011] Gate HITL Wiring — Interrupt → HITLConfirmCard → Approve/Reject → Resume"
Tipo: Serviço+HITL (wiring end-to-end)
Area: Backend
Sprint: S3
Pontos: 8
Prioridade: P0 Crítica
Epic: É35 (WT-1558)
Tags: [backend, IA, hitl, langgraph, redis, websocket, compliance, auditoria]
Classificação: 🟢 MVP CRÍTICO
Dependências: AGT-015, AGT-FE-002
Referências Diagnóstico: §13C.8, CLAUDE.md Sprint J, §13B.9, §13C.17

Estado V5 vs LIA:
  V5: Não existe — construir do zero
  LIA: hitl_service.py + hitl.py existentes + HITLConfirmCard.tsx + tabelas migration 032
  Veredicto: Usar infra LIA existente — fazer wiring end-to-end

Descricao: |
  Wiring completo do fluxo HITL end-to-end: agente emite interrupt LangGraph →
  HITLService cria pending_action → WebSocket envia hitl_request ao frontend →
  consultor vê HITLConfirmCard (AGT-FE-002) → aprova/rejeita →
  HITLService resolve → agente resume do checkpoint LangGraph.
  Redis (fast-path TTL 24h) + PostgreSQL (source of truth).

Fluxo End-to-End:
  1. Agente chama tool com HITL (ex: move_candidate) → agente detecta que precisa aprovação
  2. LangGraph interrupt_before=["execute_action"] → pausa o grafo
  3. HITLService.create_pending_action() → salva em hitl_pending_actions (PostgreSQL)
  4. HITLService publica em Redis (fast-path) → WebSocket envia hitl_request ao frontend
  5. Frontend renderiza HITLConfirmCard (AGT-FE-002) no chat do consultor
  6. Consultor clica Aprovar ou Rejeitar (+comentário)
  7. Frontend chama POST /hitl/{thread_id}/approve
  8. HITLService.resolve_action() → atualiza PostgreSQL + Redis
  9. LangGraph resume do checkpoint → executa ou cancela ação
  10. Resultado enviado via WebSocket → Card muda de estado

Tabelas HITL (migration 032):
  hitl_pending_actions:
    id, company_id, thread_id, domain, action, description,
    data JSON, agent_input JSON, status (pending/approved/rejected/expired),
    ws_session_id, created_at, expires_at (TTL 24h), resolved_at, resolved_by, comment
  hitl_audit_trail:
    id, company_id, thread_id, pending_id, action,
    approved (bool), comment, resolved_by, resolved_at

14 Acoes HITL Mapeadas:
  | Ação                    | Domínio      | Quem Aprova    |
  | move_to_gate1           | pipeline     | Consultor      |
  | move_to_gate2           | pipeline     | Consultor      |
  | reject_candidate        | pipeline     | Consultor      |
  | approve_candidate       | pipeline     | Consultor      |
  | send_offer              | pipeline     | Consultor      |
  | batch_reject            | pipeline     | Consultor      |
  | schedule_interview      | scheduling   | Consultor      |
  | cancel_interview        | scheduling   | Consultor      |
  | generate_jd             | wizard       | Consultor      |
  | update_policy           | policy       | Admin          |
  | send_bulk_email         | communication| Consultor      |
  | ats_sync_full           | ats          | Admin          |
  | create_shortlist        | sourcing     | Consultor      |
  | finalize_hiring         | pipeline     | Admin          |

API Endpoints:
  | Método | Endpoint                     | Descrição                     |
  | POST   | /hitl/{thread_id}/approve     | Aprovar/rejeitar ação pendente |
  | GET    | /hitl/{thread_id}/pending     | Listar ações pendentes         |
  | GET    | /hitl/summary                 | Resumo de ações HITL           |
  | DELETE | /hitl/{pending_id}            | Cancelar ação pendente         |

Servicos Chamados:
  | Serviço        | Arquivo                          | Papel                      |
  | HITLService    | app/services/hitl_service.py      | CRUD de pending actions     |
  | Redis          | fast-path cache TTL 24h           | Notificação real-time       |
  | PostgresSaver  | LangGraph checkpointer            | Resume do grafo             |
  | WebSocket      | orchestrator WS                   | Push hitl_request ao FE     |

Camadas de Suporte Obrigatorias:
  | Camada       | Seção  | Arquivos                                    |
  | HITL BE      | 13C.8  | hitl_service.py, hitl.py (router)            |
  | HITL FE      | 13C.8  | HITLConfirmCard.tsx (AGT-FE-002)             |
  | LangGraph    | 13B.9  | PostgresSaver (checkpoint + resume)           |
  | Redis        | 13C.14 | Redis para fast-path TTL 24h                 |
  | Auditoria    | 13C.8  | hitl_audit_trail (compliance SOX)             |

Roteiro de Reproducao (§13C.17):
  HITL (5 arquivos): §13C.17
  1. app/services/hitl_service.py
  2. app/api/v1/hitl.py
  3. plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx
  4. Migration 032 (hitl_pending_actions + hitl_audit_trail)
  5. Redis configuration (fast-path)

Para Alpha 1:
  - Wiring completo end-to-end funcionando com pelo menos 3 ações:
    move_to_gate1, reject_candidate, approve_candidate
  - Redis como cache fast-path (TTL 24h) + PostgreSQL como source of truth
  - HITLConfirmCard 5 estados (AGT-FE-002) integrado no chat
  - Auditoria: toda decisão registrada em hitl_audit_trail (compliance SOX)

Arquivos de Referencia:
  - lia-agent-system/app/services/hitl_service.py
  - lia-agent-system/app/api/v1/hitl.py
  - plataforma-lia/src/components/lia-float/HITLConfirmCard.tsx
```

---

### AGT-012: SchedulingGraph — [WT-1576](https://wedotalent.atlassian.net/browse/WT-1576)

```yaml
Titulo: "[AGT-012] SchedulingGraph — LangGraph 6 Nós (MS Graph + Calendar + Teams)"
Tipo: LangGraph StateGraph
Area: Backend
Sprint: S3
Pontos: 13
Prioridade: P1
Epic: É35 (WT-1558)
Tags: [backend, IA, langgraph, scheduling, ms-graph, teams, hitl]
Classificação: 🔵 PÓS-MVP (Alpha 1.1)
Dependências: AGT-002, AGT-005
Referências Diagnóstico: §14.6, §4.6, §13B.7, §13C.17

Estado V5 vs LIA:
  V5: Mesma arquitetura (scheduling_graph.py + zero_touch_scheduling)
  LIA: LangGraph StateGraph com 6 nós, ZeroTouchSchedulingService, MS Graph integration
  Veredicto: Mesma base — adaptar para Alpha 1.1

Descricao: |
  LangGraph StateGraph de 6 nós para agendamento de entrevista pós-Gate 2.
  Zero-touch: busca disponibilidade do entrevistador via MS Graph,
  propõe horários, cria evento no Outlook Calendar, gera link Teams.
  HITL antes de confirmar agendamento.

LangGraph — Scheduling Graph (6 Nos):
  Nós: check_availability → propose_slots → candidate_selection →
       confirm_booking → create_calendar_event → send_confirmations → END
  State: SchedulingState { job_id, candidate_id, interviewer_ids[],
         available_slots[], selected_slot, calendar_event_id, status }
  Checkpointer: PostgresSaver
  HITL: interrupt_before=["confirm_booking"]

Servicos Chamados:
  | Serviço                       | Arquivo                                         |
  | SchedulingService             | app/services/scheduling_service.py                |
  | ZeroTouchSchedulingService    | app/services/zero_touch_scheduling_service.py     |
  | CalendarService               | app/services/calendar_service.py                  |
  | MSGraphService                | app/services/ms_graph_service.py                  |
  | TeamsService                  | app/domains/communication/services/teams_service.py |

API Endpoints:
  | Método | Endpoint                                    | Descrição                     |
  | POST   | /scheduling/auto-schedule                    | Inicia agendamento automático |
  | GET    | /scheduling/available-slots/{job_id}         | Slots disponíveis             |
  | POST   | /scheduling/confirm                          | Confirma agendamento          |
  | WS     | /ws/chat/{session_id} (scheduling)           | WebSocket conversacional      |

Automacoes Relacionadas:
  | Automação                  | Frequência | Ação                              |
  | INTERVIEW_SCHEDULED (evento)| Imediato  | Confirmação + evento calendário   |
  | INTERVIEW_COMPLETED (evento)| Imediato  | Parecer IA                        |
  | check_interview_no_shows    | A cada 30m | Detecta no-shows                 |
  | send_interview_reminders    | A cada 15m | Lembretes 24h/1h antes           |

Para Alpha 1.1:
  - Integrar MS Graph (OAuth2) para calendário do entrevistador
  - Zero-touch: propor 3 slots automaticamente
  - HITL antes de confirmar (consultor aprova slot)
  - Criar evento Outlook + link Teams

Arquivos de Referencia:
  - lia-agent-system/app/services/scheduling_service.py
  - lia-agent-system/app/services/zero_touch_scheduling_service.py
  - lia-agent-system/app/api/v1/scheduling.py
```

---

### AGT-013: Triagem Abandonada Monitor — [WT-1577](https://wedotalent.atlassian.net/browse/WT-1577)

```yaml
Titulo: "[AGT-013] Triagem Abandonada Monitor — Celery Beat 48h + Fluxo Escalação"
Tipo: Serviço (Celery Beat job)
Area: Backend
Sprint: S3
Pontos: 5
Prioridade: P1
Epic: É35 (WT-1558)
Tags: [backend, IA, celery, automação, lgpd, email]
Classificação: 🔵 PÓS-MVP (Alpha 1.1)
Dependências: AGT-016, AGT-005
Referências Diagnóstico: §5.3, §7, §14.14 (trigger triagem_abandonada)

Estado V5 vs LIA:
  V5: NÃO EXISTE — funcionalidade totalmente nova
  LIA: NÃO EXISTE — funcionalidade totalmente nova
  Veredicto: Implementar do zero — usa infra de AGT-016 (Celery Beat) + AGT-005 (email)

Descricao: |
  Celery Beat job detecta triagens WSI não concluídas após 48h.
  Fluxo de escalação: 48h → lembrete email → +24h → segundo lembrete →
  +24h → alerta ao consultor → marcar como abandoned.
  Candidato pode retomar a qualquer momento via PostgresSaver (sessão preservada).
  Funcionalidade NOVA — não existe em V5 nem LIA.

Fluxo de Escalacao:
  | Tempo        | Ação                             | Destinatário |
  | T+48h        | Email: "Continue sua triagem"    | Candidato    |
  | T+72h        | Email: "Última chance"           | Candidato    |
  | T+96h        | Alerta: triagem não concluída    | Consultor    |
  | T+96h        | Status → ABANDONED               | Sistema      |

Integracao com AGT-016:
  Job: auto_complete_screenings (a cada 1h)
  Query: SELECT * FROM wsi_sessions WHERE status='in_progress' AND updated_at < NOW() - INTERVAL '48 hours'
  Ação: Para cada sessão encontrada → dispara fluxo de escalação

Retomada de Sessao:
  - Candidato acessa mesmo link /triagem/{token}
  - PostgresSaver carrega checkpoint da sessão
  - Retoma do último bloco/pergunta respondido
  - Se status=ABANDONED → reativa sessão + notifica consultor

Para Alpha 1.1:
  - Implementar job auto_complete_screenings com query de timeout
  - Criar 2 templates de email (lembrete + última chance)
  - Integrar com AGT-005 para envio dos lembretes
  - Notificar consultor via chat (AGT-001) quando abandono confirmado

Arquivos de Referencia:
  - Nenhum existente — funcionalidade totalmente nova
  - Dependências: AGT-016 (Celery Beat), AGT-005 (EmailService), AGT-009 (PostgresSaver)
```

---

### AGT-014: Teams/Slack Notifications — [WT-1578](https://wedotalent.atlassian.net/browse/WT-1578)

```yaml
Titulo: "[AGT-014] Teams/Slack Notifications — 3 Adaptive Cards + Fallback Email"
Tipo: Serviço
Area: Backend
Sprint: S3
Pontos: 3
Prioridade: P2
Epic: É35 (WT-1558)
Tags: [backend, IA, teams, slack, notificação, adaptive-cards]
Classificação: 🔵 PÓS-MVP (Alpha 1.1)
Dependências: AGT-005 (Teams adapter)
Referências Diagnóstico: §5.3, §14.7 (TeamsService)

Estado V5 vs LIA:
  V5: TeamsService com sending básico
  LIA: TeamsService com Adaptive Cards + fallback email
  Veredicto: Usar LIA — adaptar para 3 tipos de Adaptive Cards

Descricao: |
  3 tipos de Adaptive Cards enviadas ao consultor via Teams (ou Slack).
  Fallback para email se Teams não configurado. Usa TeamsService do AGT-005.

3 Adaptive Cards:
  | Card                          | Trigger                    | Conteúdo                              |
  | CANDIDATE_NO_RESPONSE         | 24h sem resposta           | Nome, vaga, dias sem contato, botão "Enviar follow-up" |
  | SCREENING_ABANDONED           | 48h triagem incompleta     | Nome, vaga, bloco parado, botão "Reativar"             |
  | SCHEDULING_NO_AVAILABILITY    | Sem slots disponíveis      | Nome, vaga, período tentado, botão "Verificar agenda"   |

Fallback:
  - Se Teams não configurado → envia email equivalente
  - Se email falhar → registra em notificações internas do dashboard

Integracao com AGT-005:
  Serviço: TeamsService (app/domains/communication/services/teams_service.py)
  API: Microsoft Teams Incoming Webhook ou Bot Framework
  Adaptive Card: JSON template por tipo

Para Alpha 1.1:
  - Configurar Teams Incoming Webhook (mais simples que Bot Framework)
  - Criar 3 templates Adaptive Card em JSON
  - Implementar fallback para email
  - Integrar com triggers do AGT-016

Arquivos de Referencia:
  - lia-agent-system/app/domains/communication/services/teams_service.py
  - Dependências: AGT-005 (CommunicationService)
```

---

### AGT-FE-003: Pipeline Status UI — [WT-1579](https://wedotalent.atlassian.net/browse/WT-1579)

```yaml
Titulo: "[AGT-FE-003] Pipeline Status UI — Dashboard do Consultor (Candidatos × Estágios × Scores)"
Tipo: Frontend
Area: Frontend
Sprint: S3
Pontos: 5
Prioridade: P1
Epic: É35 (WT-1558)
Tags: [frontend, IA, react, nextjs, pipeline, websocket, polling]
Classificação: 🔵 PÓS-MVP (Alpha 1.1)
Dependências: AGT-015, AGT-007
Referências Diagnóstico: Design System v4.2.1, §13C.8 FE

Estado V5 vs LIA:
  V5: Não existe como dashboard separado
  LIA: pipeline-report.tsx + pipeline-stages-carousel.tsx existentes
  Veredicto: Usar componentes LIA existentes — adaptar para DS v4.2.1 + dados de IA

Descricao: |
  Dashboard visual para o consultor ver o status do pipeline: candidatos por
  estágio, scores WSI, Gate 1/Gate 2 actions, alertas automáticos. Atualização
  em tempo real via polling 30s ou WebSocket. Integra dados de AGT-015 (Gates)
  e AGT-007 (scores WSI).

Componentes:
  | Componente              | Responsabilidade                          | Dados                    |
  | PipelineOverview        | Visão geral: candidatos por estágio       | GET /pipeline/{job_id}   |
  | CandidateStageCard      | Card individual por candidato             | Score WSI, status, ações |
  | StageCarousel           | Carousel de estágios (horizontal)         | Contagem por estágio     |
  | GateActionPanel         | Botões Gate 1/Gate 2 (aceitar/rejeitar)   | HITL actions pendentes   |
  | AlertBanner             | Alertas: abandono, no-show, stagnação     | Proactive alerts         |
  | ScoreChart              | Radar chart de scores WSI por dimensão    | WSI scores breakdown     |

Dados em Tempo Real:
  | Método     | Endpoint                     | Frequência    |
  | Polling    | GET /pipeline/{job_id}/status | A cada 30s    |
  | WebSocket  | /ws/pipeline/{job_id}         | Real-time     |
  | REST       | GET /hitl/pending?job_id=X    | Sob demanda   |

Design System v4.2.1:
  - Background: bg-gray-950
  - Cards: bg-gray-900 border-gray-800
  - Scores: Green (>70), Yellow (50-70), Red (<50)
  - Estágios: Badges monocromáticos
  - Gate badges: green (aprovado), red (rejeitado), yellow (pendente)

Para Alpha 1.1:
  - Polling 30s (mais simples que WebSocket para Alpha 1.1)
  - Integrar com AGT-015 para mostrar ações HITL pendentes
  - Mostrar scores WSI do AGT-007
  - Alertas visuais de candidatos em risco

Arquivos de Referencia:
  - plataforma-lia/src/components/ui/pipeline-report.tsx
  - plataforma-lia/src/components/ui/pipeline-stages-carousel.tsx
  - plataforma-lia/src/hooks/use-company-pipeline.ts
```

---

### Mapa de Dependências AGT — Grafo de Bloqueios

```
AGT-002 (Infra) ─── BLOQUEANTE de tudo
  ├── AGT-001 (Orchestrator)
  ├── AGT-003 (ATS)
  ├── AGT-004 (Sourcing)
  ├── AGT-005 (Communication)
  ├── AGT-006 (JD Generator)
  ├── AGT-017 (Policy)
  ├── AGT-015 (Pipeline Gate)
  ├── AGT-016 (Scheduler)
  └── AGT-009 (Chat Web)

AGT-003 (ATS)
  ├── AGT-004 (Sourcing — precisa vagas)
  └── AGT-006 (JD Generator — precisa dados vaga)

AGT-005 (Communication)
  ├── AGT-010 (Follow-up)
  └── AGT-013 (Abandono)

AGT-007 (WSI) → AGT-008 (CV Screening usa WSI como tool)
AGT-009 (Chat Web backend) → AGT-FE-001 (Chat Web UI)
AGT-011 (HITL Wiring) → AGT-FE-002 (HITL Card)
AGT-015 (Pipeline Gate) → AGT-011 (HITL) → AGT-FE-003 (Pipeline UI)
AGT-016 (Scheduler) → AGT-010 (Follow-up), AGT-013 (Abandono)
```

### Sobreposições Complementares AGT ↔ Cards Existentes

| Card AGT | Card Existente | Natureza da Sobreposição |
|----------|---------------|--------------------------|
| AGT-005 (CommunicationService) | COM-001 (CommunicationDispatcher) | AGT-005 adiciona IA: feedback LLM, tone policy, AI footer |
| AGT-007 (WSIInterviewGraph) | TRI-005 (Motor WSI) | AGT-007 detalha implementação LangGraph com 15 serviços |
| AGT-009 (Chat Web Canal) | TRI-002 (useTriagemChat) | AGT-009 é backend WebSocket, TRI-002 é frontend hook |
| AGT-FE-001 (Chat Web UI) | TRI-002 (useTriagemChat) | AGT-FE-001 adiciona IA: streaming, progress, LGPD banner |
| AGT-015 (PipelineGateService) | SAT-007 (Gate 1 máquina de estados) | AGT-015 adiciona HITL triggers e bypass automático |

---

*Documento v5.0 — 11/março/2026. Cards PIP removidos (v3.0), SendGrid→Mailgun (v4.0). v5.0: Bloco global de referência IA expandido com 15 seções — Tools Registry (91 tools Alpha 1), NFRs (latência/disponibilidade/rate limits), Env vars por épico, LLM Cascade (6 tiers), HITL map (14 ações), Prompt templates (9 YAMLs), Limites operacionais (12 recursos), Anti-patterns (8 regras), Migrations Alembic, Production templates (11 templates), Webhooks (8 integrações), Checklist de impacto (12 dimensões feature-impact), Checklist de conformidade IA (18 itens), Shared tools (8 tools cross-agent), Infraestrutura compartilhada (12 componentes obrigatórios). v5.1: Adicionada seção §11 — É35 Arquitetura de IA (AGT) com 21 cards completos (191 SPs). v5.2: Enriquecimento completo dos 21 cards AGT com dados do `diagnostico-agentes-mvp.md` (5.251 linhas) — cada card agora contém: Estado V5 vs LIA, Gap Analysis, Tools com Serviços (tabela detalhada), API Endpoints, Padrão 13B.7, Camadas de Suporte Obrigatórias, Roteiro de Reprodução (§13C.17), Automações Relacionadas, e Para Alpha 1. Referências cruzadas: §14.1-§14.14 (catálogos por agente), §13B (blueprint), §13C (inventário ~165 arquivos), §13D (compliance + guardrails). Total: 65 cards · 413 SPs (44 cards funcionalidade + 21 cards arquitetura IA).*
