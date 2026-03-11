# Roadmap MVP Alpha 1 — Cards Jira Unificados
## WeDOTalent / Plataforma LIA

**Versão:** 1.0 | **Data:** 11/março/2026 | **Classificação:** Referência técnica do time — Confidencial

> **Documento único de referência.** Consolida todos os cards Jira criados nos documentos de especificação e os organiza segundo o fluxo real do MVP Alpha 1. Fontes: `saturacao-chatweb-comunicacao-cards-jira.md`, `pipeline-transition-cards-jira.md` (gerado a partir de `pipeline-transition-system.md`), `jira-cards-job-creation-lifecycle.md`, `diagnostico-agentes-mvp.md` e `ANALISE_COMPARATIVA_V5_vs_LIA.md`.

---

## ÍNDICE

1. [Índice de Todos os Cards por Documento de Origem](#1-índice-de-todos-os-cards-por-documento-de-origem)
2. [Roadmap MVP Alpha 1 — Por Passo do Fluxo](#2-roadmap-mvp-alpha-1--por-passo-do-fluxo)
3. [Cards Completos — É24/É25/É26 Pipeline & Transições](#3-cards-completos--é24é25é26-pipeline--transições-pip)
4. [Cards Completos — É30 Saturação e Controle de Pools](#4-cards-completos--é30-saturação-e-controle-de-pools-sat)
5. [Cards Completos — É31 Chat Web de Triagem](#5-cards-completos--é31-chat-web-de-triagem-tri)
6. [Cards Completos — É32 Comunicação Multicanal](#6-cards-completos--é32-comunicação-multicanal-com)
7. [Cards Completos — É33 Inscrição Web](#7-cards-completos--é33-inscrição-web-ins)
8. [Cards Completos — É34 Voz Bidirecional](#8-cards-completos--é34-voz-bidirecional-voz)
9. [Cards Completos — VGM Gestão de Vagas](#9-cards-completos--vgm-gestão-de-vagas-vgm)
10. [Cards Completos — AUD Auditoria e Compliance (WT-1505→WT-1512)](#10-cards-completos--aud-auditoria-e-compliance-wt-1505wt-1512)
11. [Tabela de Dependências Cross-Épico](#11-tabela-de-dependências-cross-épico)

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
| SAT-001 | [Saturação] Modelo de Dados — Pools Separados, Thresholds e Governance Rules | 8 | 🔴 Crítica | A1 | S1 |
| SAT-002 | [Saturação] SaturationBadge — Badge Visual com Popover de Ações no Kanban | 5 | 🟠 Alta | A1 | S1 |
| SAT-003 | [Saturação] Seção de Configuração no Card Triagem (Settings → Pipeline) | 5 | 🟠 Alta | A1 | S1 |
| SAT-004 | [Saturação] Badges de Origem — Web, WhatsApp, Busca, ATS, Aguardando | 3 | 🟡 Média | A1 | S1 |
| SAT-005 | [Saturação] Fila de Espera — Status awaiting_screening + Promoção Automática | 8 | 🔴 Crítica | A1 | S2 |
| SAT-006 | [Saturação] Override Manual — Recrutador Aprova Candidato da Fila | 5 | 🟠 Alta | A1 | S2 |
| SAT-007 | [Saturação] Gate 1 — Máquina de Estados da Inscrição Web até Triagem WSI | 5 | 🔴 Crítica | A1 | S1 |

**Subtotal É30:** 7 cards · 39 SPs

---

**Épico É31 — Chat Web de Triagem (WSI + IA Conversacional)**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| TRI-001 | [Chat Web] Tipos e Interfaces TypeScript — types.ts Completo | 3 | 🔴 Crítica | A1 | S1 |
| TRI-002 | [Chat Web] Hook useTriagemChat — State Management + API Integration (~537L) | 13 | 🔴 Crítica | A1 | S2 |
| TRI-003 | [Chat Web] WelcomeCard — Tela de Boas-Vindas com Branding da Empresa | 3 | 🟠 Alta | A1 | S2 |
| TRI-004 | [Chat Web] MessageBubble — Bolha de Mensagem com AudioPlayer e Animação | 5 | 🟠 Alta | A1 | S2 |
| TRI-005 | [Chat Web] TriagemSessionService — Motor de IA Conversacional + WSI Scoring (~887L) | 21 | 🔴 Crítica | A1 | S2 |
| TRI-006 | [Chat Web] InputBar — Campo de Texto + Gravação de Áudio + Controles de Voz | 5 | 🟠 Alta | A1 | S2 |
| TRI-007 | [Chat Web] Página de Triagem — /triagem/[token] (~311L) | 8 | 🔴 Crítica | A1 | S2 |
| TRI-008 | [Chat Web] Proxy Route Next.js — /api/backend-proxy/triagem/[...path] | 3 | 🔴 Crítica | A1 | S1 |

**Subtotal É31:** 8 cards · 61 SPs

---

**Épico É32 — Comunicação Multicanal**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| COM-001 | [Comunicação] CommunicationDispatcher — SendGrid + Twilio + Tone Policy (~533L) | 8 | 🔴 Crítica | A1 | S1 |
| COM-002 | [Comunicação] Dispatch Automático #1 — Feedback de Triagem (Aprovado/Reprovado) | 3 | 🟠 Alta | A1 | S2 |
| COM-003 | [Comunicação] Dispatch Automático #2 — Rejeição ao Mudar de Stage | 3 | 🟠 Alta | A1 | S2 |
| COM-004 | [Comunicação] Dispatch Automático #3 — Convite de Fila quando Slot Abre | 3 | 🟠 Alta | A1 | S2 |
| COM-005 | [Comunicação] Dispatch Automático #5 — Confirmação Real Pós-Conclusão da Triagem | 3 | 🟠 Alta | A1 | S2 |

**Subtotal É32:** 5 cards · 20 SPs

---

**Épico É33 — Inscrição Web (Formulário Público)**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| INS-001 | [Inscrição Web] Formulário Público — Candidatar-se Online na Página da Vaga | 8 | 🟠 Alta | A1 | S2 |
| INS-002 | [Inscrição Web] Página Pública da Vaga — Detalhes + Formulário (/vagas/[slug]) | 5 | 🟠 Alta | A1 | S2 |
| INS-003 | [Inscrição Web] Endpoint POST /public-vacancies/{slug}/apply | 5 | 🟠 Alta | A1 | S2 |

**Subtotal É33:** 3 cards · 18 SPs

---

**Épico É34 — Suporte a Voz Bidirecional**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| VOZ-001 | [Voz] AudioRecordButton — Gravação de Áudio + Transcrição (STT) | 5 | 🟡 Média | A1 | S2 |
| VOZ-002 | [Voz] AudioPlayer — Reprodução de Áudio com Controles | 3 | 🟡 Média | A1 | S2 |
| VOZ-003 | [Voz] TTS Backend — Geração de Áudio via OpenAI tts-1 | 5 | 🟡 Média | A1 | S2 |
| VOZ-004 | [Voz] Propagação de isVoiceMode — Estado Runtime no UI | 3 | 🟠 Alta | A1 | S2 |

**Subtotal É34:** 4 cards · 16 SPs

---

### 1.2 — `pipeline-transition-cards-jira.md` (gerado a partir de `pipeline-transition-system.md`)

**Épicos É24 / É25 / É26 — Pipeline & Transições**

| Card | Título | SP | Prioridade | Fase | Sprint |
|------|--------|----|------------|------|--------|
| PIP-001 | [Pipeline] Arquitetura de 3 Camadas de Colunas + Catálogo de Etapas | 8 | 🔴 Crítica | A1 | S1 |
| PIP-002 | [Pipeline] Motor de action_behavior — 10 Tipos de Ação Nativa | 8 | 🔴 Crítica | A1 | S1 |
| PIP-003 | [Pipeline] UniversalTransitionModal — Hub de Transições (Frontend) | 8 | 🔴 Crítica | A1 | S2 |
| PIP-004 | [Pipeline] use-transition-context — Hook de Estado de Transição | 5 | 🟠 Alta | A1 | S2 |
| PIP-005 | [Pipeline] Movimentação Livre — Drag-Drop e Dropdown | 5 | 🔴 Crítica | A1 | S2 |
| PIP-006 | [Pipeline] Sistema de Badges nos Cards do Kanban | 5 | 🟠 Alta | A1 | S2 |
| PIP-007 | [Pipeline] TransitionDispatchService — Disparos Automáticos Layer 1 | 8 | 🟠 Alta | A1 | S2 |
| PIP-008 | [Pipeline] Endpoints de Transição — API REST | 5 | 🔴 Crítica | A1 | S1 |
| PIP-009 | [Pipeline] Pipeline CRUD — Gestão de Colunas por Vaga | 5 | 🟠 Alta | A1 | S1 |
| PIP-010 | [Pipeline] Barra de Ações em Massa — Seleção Múltipla | 5 | 🟠 Alta | A1 | S2 |
| PIP-011 | [Pipeline] Pipeline Padrão da Empresa — Menu Configurações | 5 | 🟡 Média | A2 | S3 |
| PIP-012 | [Pipeline] Herança de Pipeline — Empresa → Vaga (Copy-on-Write) | 5 | 🟡 Média | A2 | S3 |
| PIP-013 | [Pipeline] Criação de Colunas Customizadas — LIA sugere action_behavior | 5 | 🟡 Média | A2 | S3 |
| PIP-014 | [Pipeline] TestSendModal — Modal de Envio de Testes Técnicos | 5 | 🟠 Alta | A2 | S3 |
| PIP-015 | [Pipeline] ProposalModal — Modal de Proposta Formal ao Candidato | 5 | 🟠 Alta | A2 | S3 |
| PIP-016 | [Pipeline] SchedulingModal — Agendamento com Calendário Integrado | 8 | 🟡 Média | A2+ | S4 |
| PIP-017 | [Pipeline] Mini-Prompt LLM — Interpretação Layer 2 do Dispatch | 5 | 🟡 Média | A2 | S3 |
| PIP-018 | [Pipeline] Sistema de Timeout e Escalação por Pipeline | 5 | 🟡 Média | A2+ | S4 |

**Subtotal É24/É25/É26:** 18 cards · 105 SPs

---

### 1.3 — `jira-cards-job-creation-lifecycle.md`

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

**Subtotal VGM:** 10 cards · 50 SPs

---

### 1.4 — `diagnostico-agentes-mvp.md` + `ANALISE_COMPARATIVA_V5_vs_LIA.md`

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

### 1.5 — Totais Consolidados

| Épico | Prefixo | Cards | SPs | Fase |
|-------|---------|-------|-----|------|
| É30 Saturação | SAT | 7 | 39 | Alpha 1 |
| É31 Chat Web Triagem | TRI | 8 | 61 | Alpha 1 |
| É32 Comunicação | COM | 5 | 20 | Alpha 1 |
| É33 Inscrição Web | INS | 3 | 18 | Alpha 1 |
| É34 Voz | VOZ | 4 | 16 | Alpha 1 |
| É24/25/26 Pipeline | PIP | 18 | 105 | Alpha 1/2 |
| VGM Vagas | VGM | 10 | 53 | Alpha 1 |
| WT-1505 Auditoria | AUD/WT | 7 | 15 | Alpha 1 |
| **TOTAL** | | **62** | **327** | |

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
| 2 | **COM-001** | [Comunicação] CommunicationDispatcher — SendGrid + Twilio + Tone Policy | 8 | Transversal | Ag.7 |
| 3 | **PIP-001** | [Pipeline] Arquitetura de 3 Camadas de Colunas + Catálogo de Etapas | 8 | Passo 5/8 | Ag.9 |
| 4 | **PIP-002** | [Pipeline] Motor de action_behavior — 10 Tipos de Ação Nativa | 8 | Passo 5/8 | Ag.9 |
| 5 | **PIP-008** | [Pipeline] Endpoints de Transição — API REST | 5 | Passo 5/8 | Ag.9 |
| 6 | **PIP-009** | [Pipeline] Pipeline CRUD — Gestão de Colunas por Vaga | 5 | Passo 5/8 | Ag.9 |
| 7 | **TRI-001** | [Chat Web] Tipos e Interfaces TypeScript — types.ts Completo | 3 | Passo 7 | Ag.4+5 |
| 8 | **VGM-001** | [FULLSTACK] Modal de Escolha: LIA vs Criação Manual | 3 | Passo 2 | Ag.1 |
| 9 | **VGM-002** | [FULLSTACK] Formulário de Criação Manual de Vaga | 5 | Passo 2 | Ag.1 |
| 10 | **VGM-003** | [FULLSTACK] Navegação Automática pós-criação → Tab Configurações | 3 | Passo 2 | Ag.1 |
| 11 | **VGM-004** | [FULLSTACK] Tab Configurações da Vaga (Edição Completa) | 8 | Passo 2 | Ag.1 |
| 12 | **VGM-005** | [FULLSTACK] Publicação da Vaga — Auto-save + Link + Status Ativa | 5 | Passo 2 | Ag.1 |
| 13 | **VGM-006** | [FULLSTACK] Header da Vaga — Badge Status + Popover de Ações | 5 | Passo 2 | Ag.1 |
| 14 | **TRI-008** | [Chat Web] Proxy Route Next.js — /api/backend-proxy/triagem/[...path] | 3 | Passo 7 | Ag.4+5 |
| 16 | SAT-002 | [Saturação] SaturationBadge — Badge Visual com Popover de Ações no Kanban | 5 | Passo 4 | — |
| 17 | SAT-003 | [Saturação] Seção de Configuração no Card Triagem (Settings → Pipeline) | 5 | Passo 3 | — |
| 18 | SAT-004 | [Saturação] Badges de Origem — Web, WhatsApp, Busca, ATS, Aguardando | 3 | Passo 4 | — |
| 19 | **SAT-007** | [Saturação] Gate 1 — Máquina de Estados da Inscrição Web até Triagem WSI | 5 | Passo 5 | Ag.9 |
| 20 | **AUD-001** | Propagar AuditCallback para ReAct Agents (WT-1506) | 2 | Transversal | Todos |
| 21 | **AUD-002** | Rastrear Tools Chamadas por Nome (WT-1507) | 1 | Transversal | Todos |
| 22 | **AUD-003** | Circuit Breaker no Autonomous Agent (WT-1508) | 2 | Transversal | Todos |

**S1 Total:** 21 cards · ~106 SPs

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
| 6 | **SAT-005** | [Saturação] Fila de Espera — awaiting_screening + Promoção Automática | 8 | Passo 4/7 | SAT-001, COM-001 |
| 7 | SAT-006 | [Saturação] Override Manual — Recrutador Aprova Candidato da Fila | 5 | Passo 5 | SAT-005, COM-001 |

**Bloco C — Pipeline Operacional (Passo 5 e Passo 8)**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 8 | **PIP-003** | [Pipeline] UniversalTransitionModal — Hub de Transições (Frontend) | 8 | Passo 5/8 | PIP-002, PIP-008 |
| 9 | PIP-004 | [Pipeline] use-transition-context — Hook de Estado de Transição | 5 | Passo 5/8 | PIP-003 |
| 10 | **PIP-005** | [Pipeline] Movimentação Livre — Drag-Drop e Dropdown | 5 | Passo 5/8 | PIP-003 |
| 11 | PIP-006 | [Pipeline] Sistema de Badges nos Cards do Kanban | 5 | Passo 5/8 | PIP-002 |
| 12 | **PIP-007** | [Pipeline] TransitionDispatchService — Disparos Automáticos Layer 1 | 8 | Passo 5/8 | PIP-008 |
| 13 | PIP-010 | [Pipeline] Barra de Ações em Massa — Seleção Múltipla | 5 | Passo 5/8 | PIP-003 |

**Bloco D — Comunicação Automática (Passo 5 → Passo 6 → Passo 7)**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 14 | **COM-002** | [Comunicação] Dispatch Automático #1 — Feedback de Triagem | 3 | Passo 5/6 | COM-001 |
| 15 | **COM-003** | [Comunicação] Dispatch Automático #2 — Rejeição ao Mudar de Stage | 3 | Passo 5/8 | COM-001 |
| 16 | **COM-004** | [Comunicação] Dispatch Automático #3 — Convite de Fila quando Slot Abre | 3 | Passo 6 | COM-001, SAT-005 |
| 17 | COM-005 | [Comunicação] Dispatch Automático #5 — Confirmação Pós-Conclusão da Triagem | 3 | Passo 7B | COM-001, TRI-005 |

**Bloco E — Chat Web de Triagem WSI (Passo 7)**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 19 | **TRI-005** | [Chat Web] TriagemSessionService — Motor IA Conversacional + WSI Scoring | 21 | Passo 7 | COM-001 |
| 20 | **TRI-002** | [Chat Web] Hook useTriagemChat — State Management + API Integration | 13 | Passo 7 | TRI-001, TRI-005 |
| 21 | TRI-003 | [Chat Web] WelcomeCard — Boas-Vindas com Branding da Empresa | 3 | Passo 7 | TRI-001 |
| 22 | TRI-004 | [Chat Web] MessageBubble — Bolha de Mensagem com AudioPlayer | 5 | Passo 7 | TRI-001, VOZ-002 |
| 23 | **TRI-006** | [Chat Web] InputBar — Campo de Texto + Gravação de Áudio + Controles de Voz | 5 | Passo 7 | TRI-001, VOZ-001 |
| 24 | **TRI-007** | [Chat Web] Página de Triagem — /triagem/[token] (~311L) | 8 | Passo 7 | TRI-001, TRI-002, TRI-003, TRI-004, TRI-006 |

**Bloco F — Voz Bidirecional (Passo 7 — paralelo ao Chat Web)**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 25 | VOZ-003 | [Voz] TTS Backend — Geração de Áudio via OpenAI tts-1 | 5 | Passo 7 | — |
| 26 | VOZ-002 | [Voz] AudioPlayer — Reprodução de Áudio com Controles | 3 | Passo 7 | — |
| 27 | VOZ-001 | [Voz] AudioRecordButton — Gravação de Áudio + STT | 5 | Passo 7 | — |
| 28 | VOZ-004 | [Voz] Propagação de isVoiceMode — Estado Runtime no UI | 3 | Passo 7 | TRI-002, TRI-007 |

**Bloco G — Auditoria S2**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 29 | AUD-004 | Retention/Cleanup de agent_executions (WT-1509) | 1 | Transversal | AUD-001 |

**S2 Total:** 30 cards · ~188 SPs

---

### 2.3 — Sprint S3 — Refinamentos, Observabilidade e Alpha 2

> Com S1 + S2, o fluxo MVP Alpha 1 está completo. S3 adiciona configurações avançadas de pipeline, observabilidade e prepara Alpha 2.

**Bloco A — Pipeline Configurações Avançadas**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 1 | PIP-011 | [Pipeline] Pipeline Padrão da Empresa — Menu Configurações | 5 | Config | PIP-009 |
| 2 | PIP-012 | [Pipeline] Herança de Pipeline — Empresa → Vaga (Copy-on-Write) | 5 | Config | PIP-011 |
| 3 | PIP-013 | [Pipeline] Criação de Colunas Customizadas — LIA sugere action_behavior | 5 | Config | PIP-009 |
| 4 | PIP-014 | [Pipeline] TestSendModal — Modal de Envio de Testes Técnicos | 5 | Passo 8 | PIP-003 |
| 5 | PIP-015 | [Pipeline] ProposalModal — Modal de Proposta Formal ao Candidato | 5 | Passo 8 | PIP-003 |
| 6 | PIP-017 | [Pipeline] Mini-Prompt LLM — Interpretação Layer 2 do Dispatch | 5 | Passo 5/8 | PIP-007 |

**Bloco B — Auditoria e Observabilidade**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 7 | AUD-005 | Storage Externo para Logs Pesados S3/GCS (WT-1510) | 3 | Transversal | AUD-001 |
| 8 | AUD-006 | Endpoints REST de Timeline (WT-1511) | 3 | Transversal | AUD-001 |
| 9 | AUD-007 | Métricas Prometheus (WT-1512) | 3 | Transversal | AUD-001 |

**Bloco C — Gestão de Vagas S3**

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 10 | VGM-010 | [BACKEND] Endpoints de Notificação de Fechamento e Placement de Candidatos | 8 | Passo 9 | VGM-009 |

**S3 Total:** 10 cards · 47 SPs

---

### 2.4 — Sprint S4 — Alpha 2+ (Funcionalidades Avançadas)

| Ordem | Card | Título | SP | Passo | Depende de |
|-------|------|--------|----|-------|------------|
| 1 | PIP-016 | [Pipeline] SchedulingModal — Agendamento com Calendário Integrado | 8 | Passo 9 | PIP-003 |
| 2 | PIP-018 | [Pipeline] Sistema de Timeout e Escalação por Pipeline | 5 | Transversal | PIP-006 |

**S4 Total:** 2 cards · 13 SPs

---

### 2.5 — Mapa de Passos → Cards (visão inversa)

| Passo do Fluxo | Agente(s) | Cards do Sprint S1 | Cards do Sprint S2 | Cards S3+ |
|---|---|---|---|---|
| Passo 2 — Criar/Editar Vaga | Ag.1 JD Generator, Ag.8 ATS | VGM-001→008 | VGM-009, VGM-010 | — |
| Passo 3 — Configurar WSI | Ag.4+5 WSI Graph | SAT-003 | — | PIP-013 |
| Passo 4 — Buscar Candidatos | Ag.2 Sourcing, Ag.3 Triagem | SAT-001, SAT-002, SAT-004, SAT-007 | INS-001→003, SAT-005, SAT-006 | — |
| Passo 5 — Gate 1 | Ag.9 Pipeline, Ag.7 Comm | PIP-001, PIP-002, PIP-008, PIP-009 | PIP-003→007, PIP-010, COM-002, COM-003 | PIP-014, PIP-015, PIP-017 |
| Passo 6 — Contato Email | Ag.0 Orch, Ag.7 Comm | COM-001 | COM-004, COM-005 | — |
| Passo 7 — Triagem WSI Chat | Ag.4+5 WSI, Ag.0 Orch | TRI-001 | TRI-002→005, VOZ-001→004 | — |
| Passo 8 — Gate 2 | Ag.9 Pipeline, Ag.7 Comm, Ag.8 ATS | PIP-001, PIP-008 | PIP-003, PIP-005, COM-003 | PIP-014, PIP-015 |
| Passo 9 — Entrevista | Ag.6 Scheduling, Ag.7 Comm | — | VGM-009, VGM-010 | PIP-016 |
| Transversal — Auditoria | Todos | AUD-001→003 | AUD-004 | AUD-005→007, PIP-018 |

---

## 3. Cards Completos — É24/É25/É26 Pipeline & Transições (PIP)

> **Fonte:** `pipeline-transition-cards-jira.md` v1.0 (19/fev/2026), gerado a partir de `pipeline-transition-system.md` v1.2.
> **Épicos:** É24 (Modelo de Dados) · É25 (Frontend) · É26 (Configuração)

---

### PIP-001 — [Pipeline] Arquitetura de 3 Camadas de Colunas + Catálogo de Etapas

- **Épico:** É24 — Pipeline & Transições — Modelo de Dados
- **Sprint:** S1 · **Prioridade:** 🔴 Crítica · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Backend + Frontend
- **Tags:** `pipeline` `modelo-de-dados` `kanban` `backend` `mvp-alpha-1`
- **Dependências:** Nenhuma (card fundacional)

**Contexto:** Define a arquitetura de dados que suporta colunas personalizáveis no Kanban. Sem este card, nenhum outro card de pipeline pode ser construído.

**Escopo:**
- Modelo `PipelineColumn` com 3 camadas: standard (triagem, seleção, aprovação), custom e archived
- Catálogo de etapas com tipos pré-definidos (triagem_ia, entrevista_rh, proposta, etc.)
- Suporte a multi-tenancy: `company_id` em todas as queries
- Migration Alembic correspondente

**DoD:**
- [ ] Migration executada em staging sem erros
- [ ] CRUD de colunas funcionando via API
- [ ] Testes unitários: mínimo 80% coverage no model

**Referências cruzadas:** PIP-002 (depende), PIP-008 (depende), PIP-009 (depende)

---

### PIP-002 — [Pipeline] Motor de action_behavior — 10 Tipos de Ação Nativa

- **Épico:** É24 — Pipeline & Transições — Modelo de Dados
- **Sprint:** S1 · **Prioridade:** 🔴 Crítica · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Backend + Frontend
- **Tags:** `pipeline` `action-behavior` `automação` `backend` `mvp-alpha-1`
- **Dependências:** PIP-001

**Contexto:** Cada coluna do Kanban tem um `action_behavior` que define o que acontece automaticamente quando um candidato é movido para ela. Este motor é o coração do sistema de automação do pipeline.

**10 tipos de action_behavior:**
1. `intake` — Análise inicial (Like/Dislike, Gate 1)
2. `screening` — Triagem WSI (convite + acompanhamento)
3. `scheduling` — Agendamento de entrevista
4. `evaluation` — Avaliação técnica (teste, case study)
5. `verification` — Verificação de dados/documentos
6. `offer` — Proposta formal ao candidato
7. `passive` — Sem ação (aguardando, banco de talentos)
8. `conclusion_hired` — Contratação finalizada
9. `conclusion_rejected` — Rejeição com feedback
10. `conclusion_declined` — Candidato desistiu

Cada tipo define: `sub_statuses[]`, `modal_type`, `channels[]`, `auto_dispatch_eligible`. Tipos `conclusion_*` são terminais (candidato sai do pipeline ativo). `intake` é o único tipo com ação Like/Dislike (sem comunicação).

**DoD:**
- [ ] Enum `ActionBehavior` com os 10 tipos
- [ ] Validação de transição (candidato não pode pular etapas obrigatórias)
- [ ] Testes para cada tipo de ação

**Referências cruzadas:** PIP-003, PIP-006, PIP-007 (dependem)

---

### PIP-003 — [Pipeline] UniversalTransitionModal — Hub de Transições (Frontend)

- **Épico:** É25 — Pipeline & Transições — Frontend
- **Sprint:** S2 · **Prioridade:** 🔴 Crítica · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `pipeline` `modal` `frontend` `transição` `mvp-alpha-1`
- **Dependências:** PIP-002, PIP-008
- **Referências IA:** SRV-016 (SubStatusPredictor via API), AGT-011 (CommunicationAgent via dispatch)

**Contexto:** Modal unificado que aparece sempre que o recrutador move um candidato de stage. É o ponto central de UX para todas as transições — exibe campos dinâmicos conforme o `action_behavior` da coluna destino.

**Escopo:**
- Campos dinâmicos por tipo de transição
- Preview da mensagem a ser enviada ao candidato
- Confirmação e envio
- Integração com SubStatusPredictor (sugere sub-status automaticamente)
- Design System v4.2.1: `rounded-md`, sem sombras, 90% monocromático

**DoD:**
- [ ] Modal abre corretamente para todas as 10 action_behaviors
- [ ] Preview de mensagem funcionando
- [ ] Testes Vitest para cada variação de modal

**Referências cruzadas:** PIP-004, PIP-005, PIP-010 (dependem)

---

### PIP-004 — [Pipeline] use-transition-context — Hook de Estado de Transição

- **Épico:** É25 — Pipeline & Transições — Frontend
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `pipeline` `hook` `react` `frontend` `mvp-alpha-1`
- **Dependências:** PIP-003
- **Referências IA:** SRV-016 (predict-substatus chamado pelo hook)

**Escopo:** Hook React que gerencia o estado local de uma transição em andamento: candidato selecionado, coluna destino, campos preenchidos, loading e erros.

**Interface:**
```typescript
interface TransitionContext {
  candidateId: string | null;
  sourceColumn: string;
  targetColumn: string;
  actionBehavior: ActionBehavior;
  fields: Record<string, unknown>;
  isLoading: boolean;
  error: string | null;
}
```

**DoD:**
- [ ] Hook isolado e testável sem dependência de DOM
- [ ] Testes Vitest cobrindo estados de loading/erro/sucesso

---

### PIP-005 — [Pipeline] Movimentação Livre — Drag-Drop e Dropdown

- **Épico:** É25 — Pipeline & Transições — Frontend
- **Sprint:** S2 · **Prioridade:** 🔴 Crítica · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `pipeline` `kanban` `drag-drop` `frontend` `mvp-alpha-1`
- **Dependências:** PIP-003

**Escopo:**
- Drag & drop entre colunas do Kanban (dnd-kit ou @hello-pangea/dnd)
- Dropdown de "Mover para..." nos cards individuais
- Ao soltar/selecionar: abre UniversalTransitionModal (PIP-003)
- Otimistic update: card se move visualmente antes da confirmação da API

**DoD:**
- [ ] Drag-drop funcionando com feedback visual (ghost + highlight de coluna destino)
- [ ] Dropdown acessível por teclado
- [ ] Rollback visual se API retornar erro

---

### PIP-006 — [Pipeline] Sistema de Badges nos Cards do Kanban

- **Épico:** É25 — Pipeline & Transições — Frontend
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `pipeline` `kanban` `badges` `frontend` `mvp-alpha-1`
- **Dependências:** PIP-002
- **Referências IA:** SRV-016 (sub-status nos badges), AUT-005 (return events atualizam badges)

**5 tipos de badge (derivados de `f(action_behavior, sub_status, timestamps, activity)`):**
1. **Sub-status** — Estado atual dentro da coluna (ex: "Agendada", "Em análise"); cores por categoria: info/warning/success/error
2. **Ação pendente candidato** — Candidato precisa responder/agir (ex: "Aguardando resposta", "Teste pendente", "Documentos pendentes")
3. **Ação pendente recrutador** — Recrutador precisa tomar decisão (ex: "Avaliar resultado", "Revisar proposta", "Confirmar entrevista")
4. **Alerta temporal** — Timeout se aproximando ou expirado (ex: "3 dias sem resposta", "Prazo vencido")
5. **Conclusão** — Status terminal do candidato (ex: "Contratado", "Reprovado", "Desistiu")

**Regras:** Badge é CALCULADO automaticamente (não definido manualmente). Prioridade: alerta temporal > ação pendente > sub-status. Máximo 2 badges visíveis por card (mais → tooltip). Badges se atualizam em tempo real.

**DoD:**
- [ ] Todos os badges renderizando com dados reais da API
- [ ] Testes de snapshot para cada variação de badge

---

### PIP-007 — [Pipeline] TransitionDispatchService — Disparos Automáticos Layer 1

- **Épico:** É24 — Pipeline & Transições — Modelo de Dados
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `pipeline` `automação` `dispatch` `backend` `mvp-alpha-1`
- **Dependências:** PIP-008, AGT-011 (CommunicationAgent)
- **Referências IA:** AGT-011 (executa envio), SRV-016 (Layer 2 estende este serviço)

**Contexto:** Serviço determinístico (Layer 1) que dispara ações automaticamente após uma transição de stage. Para ações que requerem personalização com LLM, delega para AGT-011.

**Fluxo:**
```
Transição confirmada → TransitionDispatchService.dispatch(transition)
  → verifica action_behavior
  → dispatcha ação correspondente (email, notification, ats_sync, etc.)
  → registra audit log
  → notifica CommunicationAgent se mensagem personalizada necessária
```

**DoD:**
- [ ] Todos os 10 action_behaviors cobertos pelo dispatcher
- [ ] Audit log registrado para cada dispatch
- [ ] Testes unitários com mocks de AGT-011

---

### PIP-008 — [Pipeline] Endpoints de Transição — API REST

- **Épico:** É24 — Pipeline & Transições — Modelo de Dados
- **Sprint:** S1 · **Prioridade:** 🔴 Crítica · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `pipeline` `api` `rest` `backend` `mvp-alpha-1`
- **Dependências:** PIP-001, PIP-002
- **Referências IA:** SRV-016 (endpoint predict-substatus), INF-005 (event dispatch pós-transição)

**Endpoints:**
```
POST   /api/v1/pipeline/{job_id}/columns          → criar coluna
GET    /api/v1/pipeline/{job_id}/columns          → listar colunas
PUT    /api/v1/pipeline/{job_id}/columns/{id}     → atualizar coluna
DELETE /api/v1/pipeline/{job_id}/columns/{id}     → remover coluna
POST   /api/v1/pipeline/candidates/{id}/move      → mover candidato
GET    /api/v1/pipeline/candidates/{id}/substatus → prever sub-status (SRV-016)
```

**DoD:**
- [ ] Todos os endpoints com schemas Pydantic tipados
- [ ] Validação de company_id em todos os endpoints (multi-tenancy)
- [ ] Testes de integração com DB real

---

### PIP-009 — [Pipeline] Pipeline CRUD — Gestão de Colunas por Vaga

- **Épico:** É24 — Pipeline & Transições — Modelo de Dados
- **Sprint:** S1 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Backend + Frontend
- **Tags:** `pipeline` `crud` `vagas` `backend` `frontend` `mvp-alpha-1`
- **Dependências:** PIP-001

**Escopo:**
- UI de gestão de colunas dentro da Tab Configurações da Vaga
- Drag-drop para reordenar colunas
- Adicionar/remover colunas
- Configurar action_behavior por coluna

**DoD:**
- [ ] UI de CRUD funcional com Design System v4.2.1
- [ ] Persistência via API (PIP-008)
- [ ] Testes E2E básicos

---

### PIP-010 — [Pipeline] Barra de Ações em Massa — Seleção Múltipla

- **Épico:** É25 — Pipeline & Transições — Frontend
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `pipeline` `kanban` `bulk-actions` `frontend` `mvp-alpha-1`
- **Dependências:** PIP-003
- **Referências IA:** AUT-006 (bulk reject com AI), AGT-011 (bulk messages)

**Escopo:**
- Checkbox em cada card do Kanban
- Barra flutuante ao selecionar 2+ candidatos
- Ações: Mover todos, Rejeitar todos, Enviar mensagem em massa
- Confirmação obrigatória antes de ações em massa

**DoD:**
- [ ] Seleção múltipla funcionando
- [ ] Barra de ações aparece/desaparece corretamente
- [ ] Ações em massa chamam PIP-003 (UniversalTransitionModal) em modo bulk

---

### PIP-011 — [Pipeline] Pipeline Padrão da Empresa — Menu Configurações

- **Épico:** É26 — Pipeline & Transições — Configuração
- **Sprint:** S3 · **Prioridade:** 🟡 Média · **SPs:** 5
- **Fase:** Alpha 2 · **Área:** Backend + Frontend
- **Tags:** `pipeline` `configuração` `empresa` `alpha-2`
- **Dependências:** PIP-009

**Escopo:** Permite ao admin da empresa definir um pipeline padrão que é aplicado a novas vagas automaticamente. Economiza configuração repetitiva.

---

### PIP-012 — [Pipeline] Herança de Pipeline — Empresa → Vaga (Copy-on-Write)

- **Épico:** É26 — Pipeline & Transições — Configuração
- **Sprint:** S3 · **Prioridade:** 🟡 Média · **SPs:** 5
- **Fase:** Alpha 2 · **Área:** Backend
- **Tags:** `pipeline` `herança` `copy-on-write` `backend` `alpha-2`
- **Dependências:** PIP-011

**Escopo:** Quando uma vaga é criada, herda o pipeline padrão da empresa como cópia independente (copy-on-write). Alterações na vaga não afetam o template da empresa.

---

### PIP-013 — [Pipeline] Criação de Colunas Customizadas — LIA sugere action_behavior

- **Épico:** É26 — Pipeline & Transições — Configuração
- **Sprint:** S3 · **Prioridade:** 🟡 Média · **SPs:** 5
- **Fase:** Alpha 2 · **Área:** Backend + Frontend
- **Tags:** `pipeline` `ia` `customização` `alpha-2`
- **Dependências:** PIP-009, SRV-016
- **Referências IA:** SRV-016 (LLM inference), INF-012 (feature flag ENABLE_INFER_BEHAVIOR)

**Escopo:** Quando o recrutador cria uma coluna com nome personalizado (ex: "Apresentação Cultural"), a LIA sugere o `action_behavior` mais adequado baseado no nome e contexto da vaga.

---

### PIP-014 — [Pipeline] TestSendModal — Modal de Envio de Testes Técnicos

- **Épico:** É26 — Pipeline & Transições — Configuração
- **Sprint:** S3 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** Alpha 2 · **Área:** Frontend
- **Tags:** `pipeline` `teste-técnico` `modal` `frontend` `alpha-2`
- **Dependências:** PIP-003
- **Referências IA:** AGT-011 (envio via CommunicationAgent)

**Escopo:** Modal especializado ativado quando action_behavior = `send_test`. Permite configurar o teste a ser enviado, prazo de entrega e instruções adicionais.

---

### PIP-015 — [Pipeline] ProposalModal — Modal de Proposta Formal ao Candidato

- **Épico:** É26 — Pipeline & Transições — Configuração
- **Sprint:** S3 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** Alpha 2 · **Área:** Frontend
- **Tags:** `pipeline` `proposta` `modal` `frontend` `alpha-2`
- **Dependências:** PIP-003
- **Referências IA:** AGT-011 (envio via CommunicationAgent)

**Escopo:** Modal especializado para action_behavior = `send_proposal`. Campos: salário, benefícios, data de início, modalidade. Gera carta de oferta personalizada.

---

### PIP-016 — [Pipeline] SchedulingModal — Agendamento com Calendário Integrado

- **Épico:** É26 — Pipeline & Transições — Configuração
- **Sprint:** S4 · **Prioridade:** 🟡 Média · **SPs:** 8
- **Fase:** Alpha 2+ · **Área:** Frontend + Backend
- **Tags:** `pipeline` `agendamento` `calendário` `alpha-2+`
- **Dependências:** PIP-003, AGT-003 (SchedulingAgent)
- **Referências IA:** AGT-003 (SchedulingAgent), SRV-010 (Calendar Service), INT-AI-005 (MS Graph)

**Escopo:** Modal especializado para action_behavior = `schedule_interview`. Integra com Google Calendar, Outlook e Teams para propor horários disponíveis e confirmar entrevista.

---

### PIP-017 — [Pipeline] Mini-Prompt LLM — Interpretação Layer 2 do Dispatch

- **Épico:** É24 — Pipeline & Transições — Modelo de Dados
- **Sprint:** S3 · **Prioridade:** 🟡 Média · **SPs:** 5
- **Fase:** Alpha 2 · **Área:** Backend
- **Tags:** `pipeline` `ia` `llm` `dispatch` `alpha-2`
- **Dependências:** PIP-007, SRV-016
- **Referências IA:** SRV-016 (LLM inference), AGT-011 (personalização de mensagem)

**Escopo:** Extensão do TransitionDispatchService (Layer 2): quando o dispatch determinístico não consegue determinar a mensagem ideal, invoca mini-prompt LLM para personalizar a comunicação com base no perfil do candidato e contexto da vaga.

---

### PIP-018 — [Pipeline] Sistema de Timeout e Escalação por Pipeline

- **Épico:** É24 — Pipeline & Transições — Modelo de Dados
- **Sprint:** S4 · **Prioridade:** 🟡 Média · **SPs:** 5
- **Fase:** Alpha 2+ · **Área:** Backend
- **Tags:** `pipeline` `timeout` `escalação` `automação` `alpha-2+`
- **Dependências:** PIP-006, INF-005
- **Referências IA:** INF-005 (dispara eventos de timeout), AUT-002 (timeout de triagem)

**Escopo:** Candidatos que ficam mais de N dias em uma coluna disparam alertas e, opcionalmente, ações automáticas de escalação (notificação ao gestor, retorno para pool, etc.).

---

## 4. Cards Completos — É30 Saturação e Controle de Pools (SAT)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md`
> **Épico:** É30 — Saturação e Controle de Pools

---

### SAT-001 — [Saturação] Modelo de Dados — Pools Separados, Thresholds e Governance Rules

- **Épico:** É30 — Saturação e Controle de Pools
- **Sprint:** S1 · **Prioridade:** 🔴 Crítica · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `api` `database` `saturação` `multi-tenant` `mvp-alpha-1`
- **Dependências:** Nenhuma

**Contexto:** Base de dados para controle de saturação. Define quantos candidatos podem estar em triagem simultânea por vaga (pool ativo) e mantém os demais em fila de espera.

**Campos do modelo `ScreeningPool`:**
```python
job_id: UUID
company_id: UUID
max_active: int          # threshold: máximo simultâneo (default 50)
active_count: int        # candidatos em triagem agora
waiting_count: int       # candidatos na fila
governance_mode: str     # 'auto' | 'manual' | 'hybrid'
auto_promote: bool       # promover da fila automaticamente
notify_on_promote: bool  # notificar candidato ao promover
```

**Endpoints:**
```
GET  /api/v1/screening-pool/{job_id}          → status do pool
PUT  /api/v1/screening-pool/{job_id}/settings → configurar thresholds
POST /api/v1/screening-pool/{job_id}/promote  → promover manualmente da fila
```

**DoD:**
- [ ] Migration executada em staging
- [ ] CRUD completo com multi-tenancy
- [ ] Testes unitários cobrindo lógica de threshold

---

### SAT-002 — [Saturação] SaturationBadge — Badge Visual com Popover de Ações no Kanban

- **Épico:** É30 — Saturação e Controle de Pools
- **Sprint:** S1 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `componente` `kanban` `saturação` `design-system` `mvp-alpha-1`
- **Dependências:** SAT-001

**Escopo:** Componente visual exibido no header do Kanban da coluna de Triagem quando o pool está saturado. Inclui indicador numérico (ativos/máximo) e popover com ações rápidas.

**Variações visuais:**
- `normal`: verde, pool < 70% do máximo
- `warning`: amarelo, pool entre 70-90%
- `full`: vermelho, pool no máximo
- `overflow`: vermelho + ícone de fila ativa

**DoD:**
- [ ] Componente com todas as variações visuais
- [ ] Popover com ações (ver fila, configurar, aprovar próximo)
- [ ] Testes de snapshot

---

### SAT-003 — [Saturação] Seção de Configuração no Card Triagem (Settings → Pipeline)

- **Épico:** É30 — Saturação e Controle de Pools
- **Sprint:** S1 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend + Backend
- **Tags:** `frontend` `settings` `configuração` `saturação` `design-system` `mvp-alpha-1`
- **Dependências:** SAT-001

**Escopo:** Seção "Controle de Triagem" dentro da Tab Configurações da Vaga. Permite ao recrutador definir o threshold de pool, modo de governance e comportamento automático.

**Campos:**
- Máximo de candidatos simultâneos (slider ou input)
- Modo de promoção (auto / manual / híbrido)
- Notificar candidato ao promover (toggle)
- Canal de notificação (Email / WhatsApp / Ambos)

**DoD:**
- [ ] UI com Design System v4.2.1
- [ ] Salva via API (SAT-001 endpoints)
- [ ] Testes de componente

---

### SAT-004 — [Saturação] Badges de Origem — Web, WhatsApp, Busca, ATS, Aguardando

- **Épico:** É30 — Saturação e Controle de Pools
- **Sprint:** S1 · **Prioridade:** 🟡 Média · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `kanban` `componente` `ux` `mvp-alpha-1`
- **Dependências:** SAT-001

**Escopo:** Badges pequenos em cada card do Kanban indicando por qual canal o candidato se inscreveu. Facilita priorização e identificação de origem.

**Variações:**
- 🌐 Web (formulário público)
- 💬 WhatsApp
- 🔍 Busca (sourcing ativo)
- 🔄 ATS (sincronizado do ATS externo)
- ⏳ Aguardando (na fila de saturação)

---

### SAT-005 — [Saturação] Fila de Espera — Status awaiting_screening + Promoção Automática

- **Épico:** É30 — Saturação e Controle de Pools
- **Sprint:** S2 · **Prioridade:** 🔴 Crítica · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `automação` `fila` `comunicação` `saturação` `mvp-alpha-1`
- **Dependências:** SAT-001, COM-001

**Contexto:** Quando o pool está cheio (SAT-001), novos candidatos entram com status `awaiting_screening`. Quando um slot abre (candidato conclui ou é reprovado), o próximo da fila é automaticamente promovido e notificado.

**Lógica de promoção:**
```python
def on_screening_slot_freed(job_id, company_id):
    next_candidate = get_next_in_queue(job_id, order_by="created_at")
    if next_candidate and pool.auto_promote:
        promote_to_active(next_candidate)
        COM-001.send(channel="email", template="queue_slot_opened", candidate=next_candidate)
        if pool.notify_on_promote and candidate.whatsapp:
            COM-001.send(channel="whatsapp", ...)
```

**DoD:**
- [ ] Celery task para promoção automática
- [ ] Notificação via COM-001 ao promover
- [ ] Testes com mocks de fila

---

### SAT-006 — [Saturação] Override Manual — Recrutador Aprova Candidato da Fila

- **Épico:** É30 — Saturação e Controle de Pools
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Backend + Frontend
- **Tags:** `backend` `frontend` `kanban` `automação` `mvp-alpha-1`
- **Dependências:** SAT-005, COM-001

**Escopo:** O recrutador pode manualmente promover um candidato específico da fila, mesmo que o pool ainda esteja cheio — forçando um "override" com confirmação.

**Fluxo UI:**
1. Recrutador clica em "Aprovar da Fila" no popover do SaturationBadge (SAT-002)
2. Modal de confirmação: "Isso irá adicionar um candidato além do limite configurado."
3. Recrutador confirma
4. Backend promove + notifica candidato (COM-001)
5. Badge atualizado com novo count

---

### SAT-007 — [Saturação] Gate 1 — Máquina de Estados da Inscrição Web até Triagem WSI

- **Épico:** É30 — Saturação e Controle de Pools
- **Sprint:** S1 · **Prioridade:** 🔴 Crítica · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `automação` `gate` `saturação` `mvp-alpha-1`
- **Dependências:** SAT-001, SAT-005, INS-001

**Contexto:** Define e documenta a máquina de estados canônica desde que o candidato se inscreve até iniciar a triagem WSI, incluindo todos os estados intermediários de saturação.

**Estados:**
```
applied → pending_gate1 → [pool cheio?]
  → YES: awaiting_screening (COM-001 notifica "em lista de espera")
  → NO:  screening_invited (COM-001 envia link WSI)
       → screening_in_progress (candidato iniciou)
       → screening_completed (concluiu)
       → gate1_approved / gate1_rejected
```

**DoD:**
- [ ] Diagrama de estados documentado e validado pelo time
- [ ] Todos os estados mapeados no banco (enum + migration)
- [ ] Testes de transição de estado

---

## 5. Cards Completos — É31 Chat Web de Triagem (TRI)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md`
> **Épico:** É31 — Chat Web de Triagem (WSI + IA Conversacional)

---

### TRI-001 — [Chat Web] Tipos e Interfaces TypeScript — types.ts Completo

- **Épico:** É31 — Chat Web de Triagem
- **Sprint:** S1 · **Prioridade:** 🔴 Crítica · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `typescript` `tipos` `triagem` `mvp-alpha-1`
- **Dependências:** Nenhuma

**Escopo:** Define todas as interfaces TypeScript usadas pelo Chat Web de Triagem. Card de fundação — sem isso nenhum componente de triagem pode ser tipado corretamente.

**Interfaces principais:**
```typescript
interface TriagemSession { id, jobId, candidateId, status, startedAt, completedAt }
interface TriagemMessage { id, role: 'lia'|'candidate', content, timestamp, audioUrl? }
interface TriagemScore { total, dimensions: DimensionScore[], recommendation }
interface TriagemConfig { companyId, jobId, voiceEnabled, language, maxDuration }
```

---

### TRI-002 — [Chat Web] Hook useTriagemChat — State Management + API Integration (~537L)

- **Épico:** É31 — Chat Web de Triagem
- **Sprint:** S2 · **Prioridade:** 🔴 Crítica · **SPs:** 13
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `hook` `react` `api` `state-management` `triagem` `mvp-alpha-1`
- **Dependências:** TRI-001, TRI-005

**Escopo:** Hook principal que gerencia toda a lógica do chat de triagem. ~537 linhas de lógica pura, sem JSX.

**Responsabilidades:**
- Inicializar sessão via API (TRI-005)
- Gerenciar histórico de mensagens
- Enviar respostas do candidato
- Receber respostas da LIA (polling ou WebSocket)
- Controlar estados: loading, error, completed
- Integrar com voice mode (VOZ-004)

---

### TRI-003 — [Chat Web] WelcomeCard — Tela de Boas-Vindas com Branding da Empresa

- **Épico:** É31 — Chat Web de Triagem
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `componente` `triagem` `design-system` `branding` `mvp-alpha-1`
- **Dependências:** TRI-001

**Escopo:** Tela inicial exibida antes da triagem começar. Apresenta o logo da empresa, nome da vaga, instruções e botão "Iniciar Triagem". Suporta branding customizado por empresa.

---

### TRI-004 — [Chat Web] MessageBubble — Bolha de Mensagem com AudioPlayer e Animação

- **Épico:** É31 — Chat Web de Triagem
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `componente` `triagem` `áudio` `design-system` `mvp-alpha-1`
- **Dependências:** TRI-001, VOZ-002

**Escopo:** Componente de bolha de mensagem. Renderiza mensagens da LIA e do candidato com diferenciação visual. Para mensagens da LIA com áudio, exibe AudioPlayer (VOZ-002) integrado.

---

### TRI-005 — [Chat Web] TriagemSessionService — Motor de IA Conversacional + WSI Scoring (~887L)

- **Épico:** É31 — Chat Web de Triagem
- **Sprint:** S2 · **Prioridade:** 🔴 Crítica · **SPs:** 21
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `ia` `llm` `scoring` `triagem` `wsi` `voz` `mvp-alpha-1`
- **Dependências:** COM-001

**Contexto:** Serviço backend que conduz a triagem conversacional usando a LIA como entrevistadora. É o motor central do MVP — sem ele, a triagem WSI não funciona.

**Responsabilidades:**
- Criar e manter sessão de triagem
- Gerar perguntas WSI baseadas na JD e perfil do candidato
- Processar respostas (texto e áudio via STT)
- Calcular score WSI por dimensão (Taxonomia de Bloom)
- Gerar feedback final ao candidato
- Integrar com TTS (VOZ-003) para resposta em áudio

**Endpoints:**
```
POST /api/v1/triagem/sessions                  → criar sessão
POST /api/v1/triagem/sessions/{id}/messages    → enviar mensagem
GET  /api/v1/triagem/sessions/{id}/status      → status e score
POST /api/v1/triagem/sessions/{id}/complete    → finalizar
```

---

### TRI-006 — [Chat Web] InputBar — Campo de Texto + Gravação de Áudio + Controles de Voz

- **Épico:** É31 — Chat Web de Triagem
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `componente` `triagem` `voz` `acessibilidade` `mvp-alpha-1`
- **Dependências:** TRI-001, VOZ-001

**Escopo:** Componente React (~155L) que renderiza a barra de input fixa no bottom do chat. Combina:
1. Textarea auto-resize (max 120px)
2. Botão de gravação de áudio (AudioRecordButton — VOZ-001)
3. Botão de envio (Send icon)
4. Controles de voz mode (mute/unmute, finalizar conversa)

Quando `voiceMode=true`, exibe barra extra acima do input com: botão mute/unmute (Volume2/VolumeX icons) e botão "Finalizar Conversa" (PhoneOff icon, vermelho).

**Props:**
```typescript
{ onSend, onAudioTranscription?, isSending?, disabled?,
  audioEnabled?, placeholder?, className?, voiceMode?, isMuted?,
  onToggleMute?, onEndConversation? }
```

**Comportamento:** Enter envia (sem Shift), Shift+Enter nova linha. AudioRecordButton renderiza apenas se `audioEnabled=true`. Controles de voz condicionais ao `voiceMode`.

**Arquivo de referência:** `plataforma-lia/src/components/triagem/InputBar.tsx` (155L)

---

### TRI-007 — [Chat Web] Página de Triagem — /triagem/[token] (~311L)

- **Épico:** É31 — Chat Web de Triagem
- **Sprint:** S2 · **Prioridade:** 🔴 Crítica · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `página` `triagem` `layout` `routing` `mvp-alpha-1`
- **Dependências:** TRI-001, TRI-002, TRI-003, TRI-004, TRI-006

**Contexto:** Página Next.js (~311L) que orquestra todos os componentes do chat. Rota dinâmica: `/triagem/[token]` onde token é UUID da sessão (screening_invite_token). Sem login — acesso apenas por token.

**6 estados de página via `pageState` do hook `useTriagemChat`:**
- `"loading"` → spinner centralizado
- `"error"` → mensagem de erro (token inválido, expirado, etc.)
- `"welcome"` → WelcomeCard com branding da empresa
- `"chat"` → ChatContainer com MessageBubble[] + InputBar + ProgressBar
- `"confirmation"` → ConfirmationCard (pré-conclusão)
- `"completion"` → CompletionCard (pós-conclusão)

**Estado de voz:** `isVoiceMode: boolean` (ativado pelo WelcomeCard `onStart(true)`), `isMuted: boolean` (toggle via InputBar), `autoPlayAudio: boolean`.

**LGPD/Compliance:**
- Token-only access: sem login — screening_invite_token é a autenticação
- localStorage: mensagens + estado persistidos — deve ser limpável (LGPD)
- CompletionCard: mostra resumo APENAS da performance, NÃO dos dados pessoais
- Sessão já concluída → CompletionCard direto (sem re-triagem)

**Arquivo de referência:** `plataforma-lia/src/app/triagem/[token]/page.tsx` (311L)

---

### TRI-008 — [Chat Web] Proxy Route Next.js — /api/backend-proxy/triagem/[...path]

- **Épico:** É31 — Chat Web de Triagem
- **Sprint:** S1 · **Prioridade:** 🔴 Crítica · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Frontend (API Route)
- **Tags:** `frontend` `api-route` `proxy` `next.js` `mvp-alpha-1`
- **Dependências:** TRI-005

**Contexto:** Rota catch-all do Next.js que proxeia todas as chamadas de triagem para o backend FastAPI. Necessário porque o frontend (port 5000) e o backend (port 8000) rodam em portas diferentes — mesma convenção dos outros proxies da plataforma.

**Pattern:**
```
/api/backend-proxy/triagem/{...path}
→ http://localhost:8000/api/v1/triagem/{...path}
```

Suporta: GET, POST, PUT, DELETE. Propaga headers, body, query params.

**Endpoints obrigatórios no Alpha 1:**
- GET `/triagem/{token}` — busca sessão existente
- POST `/triagem/{token}/start` — inicia sessão
- POST `/triagem/{token}/message` — envia mensagem do candidato

**Arquivo de referência:** `plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts`

---

## 6. Cards Completos — É32 Comunicação Multicanal (COM)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md`
> **Épico:** É32 — Comunicação Multicanal

---

### COM-001 — [Comunicação] CommunicationDispatcher — SendGrid + Twilio + Tone Policy (~533L)

- **Épico:** É32 — Comunicação Multicanal
- **Sprint:** S1 · **Prioridade:** 🔴 Crítica · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `comunicação` `email` `whatsapp` `sms` `sendgrid` `twilio` `mvp-alpha-1`
- **Dependências:** Nenhuma

**Contexto:** Classe central de envio de comunicações para candidatos. Toda comunicação da plataforma com candidatos passa por aqui — email, WhatsApp, SMS. Implementa Tone Policy (tom adequado por contexto).

**Interface principal:**
```python
class CommunicationDispatcher:
    def send(
        self,
        candidate_id: UUID,
        company_id: UUID,
        template: str,           # ex: "screening_invited", "gate1_rejected"
        channel: str,            # "email" | "whatsapp" | "sms" | "auto"
        variables: dict,
        tone: str = "professional"  # "professional" | "friendly" | "formal"
    ) -> SendResult
```

**Templates implementados no Alpha 1:**
- `screening_invited` — convite para triagem WSI
- `queue_slot_opened` — slot abriu na fila
- `gate1_rejected` — reprovado na triagem
- `gate2_rejected` — reprovado na seleção
- `screening_completed` — triagem concluída

---

### COM-002 — [Comunicação] Dispatch Automático #1 — Feedback de Triagem (Aprovado/Reprovado)

- **Épico:** É32 — Comunicação Multicanal
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `automação` `comunicação` `triagem` `mvp-alpha-1`
- **Dependências:** COM-001

**Escopo:** Wiring automático: quando `TriagemSessionService` (TRI-005) finaliza uma sessão, dispara automaticamente o template correto via COM-001 dependendo do resultado (aprovado → próximo passo; reprovado → `gate1_rejected`).

---

### COM-003 — [Comunicação] Dispatch Automático #2 — Rejeição ao Mudar de Stage

- **Épico:** É32 — Comunicação Multicanal
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `automação` `comunicação` `rejeição` `mvp-alpha-1`
- **Dependências:** COM-001

**Escopo:** Wiring automático com o `TransitionDispatchService` (PIP-007): quando um candidato é movido para coluna com `action_behavior = send_feedback` após rejeição, dispara o template adequado (gate1_rejected ou gate2_rejected).

---

### COM-004 — [Comunicação] Dispatch Automático #3 — Convite de Fila quando Slot Abre

- **Épico:** É32 — Comunicação Multicanal
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `automação` `comunicação` `fila` `saturação` `mvp-alpha-1`
- **Dependências:** COM-001, SAT-005

**Escopo:** Wiring com SAT-005: quando um candidato é promovido da fila de espera, envia automaticamente o convite para triagem WSI (template `screening_invited` com link).

---

### COM-005 — [Comunicação] Dispatch Automático #5 — Confirmação Real Pós-Conclusão da Triagem

- **Épico:** É32 — Comunicação Multicanal
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `comunicação` `triagem` `confirmação` `mvp-alpha-1`
- **Dependências:** COM-001, TRI-005

**Escopo:** Após `TRI-005` registrar a conclusão da triagem, envia confirmação ao candidato com agradecimento e previsão de retorno. Template: `screening_completed`.

---

## 7. Cards Completos — É33 Inscrição Web (INS)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md`
> **Épico:** É33 — Inscrição Web (Formulário Público)

---

### INS-001 — [Inscrição Web] Formulário Público — Candidatar-se Online na Página da Vaga

- **Épico:** É33 — Inscrição Web
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Frontend + Backend
- **Tags:** `frontend` `backend` `formulário` `candidatura` `lgpd` `upload` `mvp-alpha-1`
- **Dependências:** SAT-001

**Escopo:** Formulário público de candidatura embedado na página da vaga. Sem login. Candidato preenche dados básicos, faz upload do CV e aceita os termos LGPD.

**Campos:**
- Nome completo (obrigatório)
- Email (obrigatório, validado)
- Telefone/WhatsApp (obrigatório)
- Upload de CV (PDF/DOCX, máx 5MB)
- Aceite LGPD (checkbox obrigatório)
- Campos customizados por vaga (opcionais)

**LGPD:** consentimento explícito registrado com timestamp e IP. Versão do texto de consentimento versionada.

---

### INS-002 — [Inscrição Web] Página Pública da Vaga — Detalhes + Formulário (/vagas/[slug])

- **Épico:** É33 — Inscrição Web
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `página` `público` `seo` `vaga` `mvp-alpha-1`
- **Dependências:** INS-001

**Escopo:** Página pública Next.js com SSR para SEO. URL: `/vagas/[empresa-slug]/[vaga-slug]`. Exibe descrição da vaga, requisitos e embedda o formulário INS-001.

---

### INS-003 — [Inscrição Web] Endpoint POST /public-vacancies/{slug}/apply

- **Épico:** É33 — Inscrição Web
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `api` `candidatura` `upload` `lgpd` `mvp-alpha-1`
- **Dependências:** SAT-001

**Escopo:** Endpoint público (sem autenticação) que recebe candidaturas do formulário INS-001. Faz upload do CV para S3, cria o candidato e verifica saturação do pool (SAT-001) para determinar status inicial.

**Lógica de status:**
```python
if pool.is_full():
    candidate.status = "awaiting_screening"
    COM-001.send("queue_slot_opened_waiting")
else:
    candidate.status = "screening_invited"
    COM-001.send("screening_invited")
```

---

## 8. Cards Completos — É34 Voz Bidirecional (VOZ)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md`
> **Épico:** É34 — Suporte a Voz Bidirecional

---

### VOZ-001 — [Voz] AudioRecordButton — Gravação de Áudio + Transcrição (STT)

- **Épico:** É34 — Voz Bidirecional
- **Sprint:** S2 · **Prioridade:** 🟡 Média · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `componente` `voz` `stt` `acessibilidade` `mvp-alpha-1`
- **Dependências:** Nenhuma

**Escopo:** Botão de gravação de áudio no Chat Web de Triagem. Candidato pressiona e fala a resposta. Ao soltar, áudio é enviado para STT (Deepgram/OpenAI Whisper) e transcrição retorna como texto.

**Estados visuais:**
- Idle: microfone cinza
- Recording: microfone vermelho + animação de pulso
- Processing: spinner
- Done: checkmark verde

---

### VOZ-002 — [Voz] AudioPlayer — Reprodução de Áudio com Controles

- **Épico:** É34 — Voz Bidirecional
- **Sprint:** S2 · **Prioridade:** 🟡 Média · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `componente` `voz` `tts` `áudio` `mvp-alpha-1`
- **Dependências:** Nenhuma

**Escopo:** Player de áudio embutido nas bolhas de mensagem da LIA (TRI-004). Reproduz o áudio gerado pelo TTS (VOZ-003). Controles: play/pause, barra de progresso, velocidade (1x / 1.5x / 2x).

---

### VOZ-003 — [Voz] TTS Backend — Geração de Áudio via OpenAI tts-1

- **Épico:** É34 — Voz Bidirecional
- **Sprint:** S2 · **Prioridade:** 🟡 Média · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `voz` `tts` `openai` `ia` `mvp-alpha-1`
- **Dependências:** Nenhuma

**Escopo:** Serviço backend que converte texto em áudio usando OpenAI tts-1. Cacheia resultado no Redis (TTL 1h) para evitar custo redundante. Retorna URL do áudio para o frontend.

**Voz padrão LIA:** `alloy` (OpenAI) ou equivalente — voz feminina, profissional, português brasileiro.

---

### VOZ-004 — [Voz] Propagação de isVoiceMode — Estado Runtime no UI

- **Épico:** É34 — Voz Bidirecional
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Frontend
- **Tags:** `frontend` `voz` `state-management` `mvp-alpha-1`
- **Dependências:** TRI-002

**Escopo:** Controle de estado global `isVoiceMode` no Chat Web. Quando ativo: AudioRecordButton visível, AudioPlayer auto-play, input de texto ocultado. Quando inativo: input de texto padrão, áudio opcional. O estado `isVoiceMode` é definido na página TRI-007 e propagado via props para TRI-006 (InputBar) e TRI-004 (MessageBubble).

---

## 9. Cards Completos — VGM Gestão de Vagas (VGM)

> **Fonte:** `jira-cards-job-creation-lifecycle.md`
> **Épico:** VGM — Gestão de Vagas

---

### VGM-001 — [FULLSTACK] Modal de Escolha: LIA vs Criação Manual

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S1 · **Prioridade:** 🟠 Alta · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Full-Stack
- **Tags:** `fullstack` `modal` `vagas` `ia` `mvp-alpha-1`
- **Status Protótipo:** ✅ Implementado
- **Dependências:** Nenhuma
- **Data alvo:** 10–20/Mar/2026

**Escopo:** Modal exibido ao clicar em "Nova Vaga". Oferece duas opções:
1. **Criar com LIA** → abre chat com Wizard Agent para coleta conversacional
2. **Criar Manualmente** → abre formulário estruturado (VGM-002)

---

### VGM-002 — [FULLSTACK] Formulário de Criação Manual de Vaga

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S1 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Full-Stack
- **Tags:** `fullstack` `formulário` `vagas` `mvp-alpha-1`
- **Status Protótipo:** ✅ Implementado
- **Dependências:** VGM-001

**Campos obrigatórios:** título, departamento, localização, modalidade, nível de senioridade, tipo de contrato, faixa salarial (opcional), descrição (texto livre ou gerado por LIA).

---

### VGM-003 — [FULLSTACK] Navegação Automática pós-criação → Tab Configurações

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S1 · **Prioridade:** 🟠 Alta · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Full-Stack
- **Tags:** `fullstack` `navegação` `vagas` `ux` `mvp-alpha-1`
- **Status Protótipo:** ✅ Implementado
- **Dependências:** VGM-002

**Escopo:** Após criar a vaga (manual ou LIA), redireciona automaticamente para a Tab Configurações da vaga recém-criada, pré-selecionando a seção "Roteiro de Triagem" para o próximo passo natural.

---

### VGM-004 — [FULLSTACK] Tab Configurações da Vaga (Edição Completa)

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S1 · **Prioridade:** 🟠 Alta · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Full-Stack
- **Tags:** `fullstack` `configuração` `vagas` `mvp-alpha-1`
- **Status Protótipo:** ✅ Implementado
- **Dependências:** VGM-003

**Seções da Tab Configurações:**
- Informações Básicas (editar campos do VGM-002)
- Roteiro de Triagem (configurar WSI — integra com Passo 3 do fluxo)
- Pipeline (integra com PIP-009)
- Saturação (integra com SAT-003)
- Publicação e Links

---

### VGM-005 — [FULLSTACK] Publicação da Vaga — Auto-save + Link + Status Ativa

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S1 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Full-Stack
- **Tags:** `fullstack` `publicação` `vagas` `mvp-alpha-1`
- **Status Protótipo:** ✅ Implementado
- **Dependências:** VGM-004

**Escopo:** Botão "Publicar Vaga" que muda o status para `active`, gera o slug único para a URL pública, ativa o auto-save periódico e exibe o link de candidatura (integra com INS-002).

---

### VGM-006 — [FULLSTACK] Header da Vaga — Badge Status + Popover de Ações

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S1 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Full-Stack
- **Tags:** `fullstack` `header` `vagas` `popover` `mvp-alpha-1`
- **Status Protótipo:** ✅ Implementado
- **Dependências:** VGM-005

**Escopo:** Header fixo no topo da página de vaga. Exibe: título da vaga, badge de status (Rascunho/Ativa/Pausada/Fechada), e popover com ações rápidas (editar, pausar, fechar, copiar link, compartilhar).

---

### VGM-007 — [FULLSTACK] Badge de Triagem WSI no Header + Controle de Status

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S2 · **Prioridade:** 🟡 Média · **SPs:** 3
- **Fase:** MVP Alpha 1 · **Área:** Full-Stack
- **Tags:** `fullstack` `header` `triagem` `badge` `mvp-alpha-1`
- **Status Protótipo:** ✅ Implementado (📋 Pendente Jira)
- **Dependências:** VGM-006
- **Datas alvo:** 21/Mar–31/Mar/2026

**Escopo:** Badge secundário no header exibindo o status da triagem (Triagem Ativa / Pausada / Pool Cheio). Toggle para pausar/ativar triagem sem pausar a vaga inteira.

---

### VGM-008 — [FULLSTACK] Modal Pausar / Reativar Vaga com Notificação de Candidatos

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 5
- **Fase:** MVP Alpha 1 · **Área:** Full-Stack
- **Tags:** `fullstack` `modal` `vagas` `mvp-alpha-1`
- **Status Protótipo:** ✅ Implementado (📋 Pendente Jira)
- **Dependências:** VGM-006
- **Datas alvo:** 21/Mar–31/Mar/2026

**Escopo:** Modal de confirmação para pausar a vaga. Exibe: impacto da pausa (candidatos em triagem, convites pendentes), opção de notificar candidatos sobre a pausa, e botão de confirmação.

---

### VGM-009 — [FULLSTACK] Modal Fechar Vaga com Registro de Placement

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S2 · **Prioridade:** 🟠 Alta · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Full-Stack
- **Tags:** `fullstack` `modal` `vagas` `placement` `mvp-alpha-1`
- **Status Protótipo:** ⚠️ UI OK, lógica incompleta — **NÃO IMPLEMENTAR AGORA** (aguardar VGM-010 aprovado)
- **Dependências:** VGM-006
- **Datas alvo:** 21/Mar–31/Mar/2026

**Escopo:** Modal de encerramento de vaga. Registra: motivo do fechamento (contratado, cancelado, congelado), candidato contratado (se houver), data de início prevista.

---

### VGM-010 — [BACKEND] Endpoints de Notificação de Fechamento e Placement de Candidatos

- **Épico:** VGM — Gestão de Vagas
- **Sprint:** S3 · **Prioridade:** 🟠 Alta · **SPs:** 8
- **Fase:** MVP Alpha 1 · **Área:** Backend
- **Tags:** `backend` `notificações` `vagas` `comunicação` `mvp-alpha-1`
- **Status Protótipo:** ❌ Não implementado — **NÃO IMPLEMENTAR AGORA** (depende de VGM-009 finalizado e aprovado)
- **Dependências:** VGM-009
- **Datas alvo:** 01/Abr–14/Abr/2026

**Escopo:** Ao fechar a vaga, envia notificações automáticas via COM-001:
- Candidatos em pipeline: email de encerramento do processo
- Candidato contratado (se houver): confirmação formal
- Recrutador responsável: resumo final (via Teams)

---

## 10. Cards Completos — AUD Auditoria e Compliance (WT-1505→WT-1512)

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

---

## 11. Tabela de Dependências Cross-Épico

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
| PIP-003 | PIP-002, PIP-008 | Modal não tem dados do backend |
| PIP-007 | PIP-008 | Dispatcher não tem endpoints para chamar |
| PIP-010 | PIP-003 | Bulk actions não têm modal para usar |
| VOZ-004 | TRI-002 | Voice mode não propaga estado |
| VGM-010 | COM-001 | Notificações de fechamento não são enviadas |
| AUD-004 | AUD-001 | Cleanup sem logs para limpar |
| AUD-005 | AUD-001 | Storage externo sem origem de dados |
| AUD-006 | AUD-001 | Endpoints sem dados para retornar |
| AUD-007 | AUD-001 | Métricas sem fonte de dados |

---

## Resumo Executivo

| Sprint | Cards | SPs | Entregável Principal |
|--------|-------|-----|----------------------|
| **S1 — Fundação** | 21 | ~106 | Modelos de dados, APIs base, VGM S1, TRI-008 proxy, AUD P0/P1 |
| **S2 — Fluxo Completo** | 30 | ~188 | Inscrição → Chat Web Triagem → Gate 1 → Gate 2 → Comunicação |
| **S3 — Refinamentos** | 10 | ~47 | Pipeline avançado, AUD observabilidade, VGM-010 |
| **S4 — Alpha 2+** | 2 | ~13 | Scheduling modal, timeout/escalação |
| **TOTAL** | **63** | **354** | MVP Alpha 1 completo em S1+S2 |

**Caminho crítico do MVP Alpha 1:**
```
SAT-001 → INS-003 → INS-001 → SAT-007
COM-001 → SAT-005 → COM-004
PIP-001 → PIP-002 → PIP-008 → PIP-003 → PIP-005
TRI-001 → TRI-005 → TRI-002 → (Chat Web funcional)
VGM-001 → VGM-005 → VGM-006 (Vaga publicada)
AUD-001 → AUD-002 → AUD-003 (Auditoria mínima ativa)
```

---

*Documento v1.1 — 11/março/2026. Consolida cards de: `saturacao-chatweb-comunicacao-cards-jira.md` (27 cards — TRI-006, TRI-007, TRI-008 adicionados na v1.1), `pipeline-transition-cards-jira.md` (18 cards — PIP-002 e PIP-006 corrigidos na v1.1), `jira-cards-job-creation-lifecycle.md` (10 cards — VGM-007/008/009/010 títulos, sprints e SPs corrigidos na v1.1), `diagnostico-agentes-mvp.md` + `ANALISE_COMPARATIVA_V5_vs_LIA.md` (7 cards AUD). Roadmap alinhado ao fluxo MVP Alpha 1 (9 passos) do diagnóstico de agentes. Total: 62 cards · 327 SPs (excluindo S4).*
