# Roadmap MVP Alpha 1 — Cards Jira Unificados
## WeDOTalent / Plataforma LIA

**Versão:** 3.0 | **Data:** 11/março/2026 | **Classificação:** Referência técnica do time — Confidencial

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
| COM-001 / [WT-1542](https://wedotalent.atlassian.net/browse/WT-1542) | [Comunicação] CommunicationDispatcher — SendGrid + Twilio + Tone Policy (~533L) | 8 | 🔴 Crítica | A1 | S1 |
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
| **TOTAL** | | **44** | **222** | |

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
```


---

## 5. Cards Completos — É32 Comunicação Multicanal (COM) — Épico [WT-1520](https://wedotalent.atlassian.net/browse/WT-1520)

> **Fonte:** `saturacao-chatweb-comunicacao-cards-jira.md` §8
> **Épico:** É32 — Comunicação Multicanal
> **Status Jira:** COM-001→005 = WT-1538→WT-1542 (criados)

### COM-001: CommunicationDispatcher — Classe Central de Envio

```yaml
Titulo: "[Comunicação] CommunicationDispatcher — SendGrid + Twilio + Tone Policy (~533L)"
Tipo: Feature
Area: Backend
Sprint: S1
Pontos: 8
Prioridade: Crítica
Epic: É32
Status: 📋 Pendente Jira | ✅ Protótipo Concluído (Backend)
Fase: MVP Alpha 1
Tags: [backend, comunicação, email, whatsapp, sms, sendgrid, twilio]
Dependências: Nenhuma

Descricao: |
  Classe Python (~533L) que centraliza TODA comunicação da plataforma
  com candidatos. Encapsula SendGrid (email) e Twilio (WhatsApp/SMS)
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
    - Dependências: sendgrid, twilio
    - Env vars: SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME,
        TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM,
        TWILIO_SMS_FROM (ou TWILIO_PHONE_NUMBER)
    - Policy: app.shared.policy_middleware.get_policy_for_company()
    - Tones: professional, friendly, formal
    - Greetings por tone:
      professional → "Olá, {nome_completo}. "
      friendly → "Oi, {primeiro_nome}! "
      formal → "Prezado(a) Sr(a). {nome_completo}, "

DoD:
  - [x] send_email funcional com SendGrid
  - [x] send_whatsapp funcional com Twilio
  - [x] send_sms funcional com Twilio
  - [x] dispatch_message com multi_channel
  - [x] Mock em dev quando keys não configuradas
  - [x] lia_tone aplicado corretamente
  - [x] Singleton instanciado
  - [ ] Testes unitários para cada método

Criterios de Aceitacao:
  - [x] Sem SENDGRID_API_KEY → retorna {success:true, mock:true}
  - [x] Com SENDGRID_API_KEY → email enviado, retorna message_id
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
    - SendGrid offline → mock success (dev), error logged (prod)
    - Twilio offline → mock success (dev), email-only fallback (prod)
    - multi_channel=True + apenas email disponível → envia só email (sem error)

Arquivos de Referencia (Prototipo LIA):
  - dispatcher: lia-agent-system/app/domains/communication/services/communication_dispatcher.py (533L — copiar)
  - service ref: lia-agent-system/app/services/communication_dispatcher.py (1L import re-export)
  - policy: lia-agent-system/app/shared/policy_middleware.py
  - channels: lia-agent-system/app/core/template_channels.py (8 canais definidos)
  - email_tracking: lia-agent-system/app/services/email_tracking_service.py
  - rate_limits: lia-agent-system/app/config/default_rules.json (messages_per_hour)
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
    - SendGrid/Twilio offline → registra falha, candidato pode consultar status via portal

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
```


---

## 8. Cards Completos — VGM Gestão de Vagas (VGM)

> **Fonte:** `jira-cards-job-creation-lifecycle.md`
> **Épico:** VGM — Gestão de Vagas
> **Status Jira:** VGM-001→010 = WT-1494→WT-1504 (existentes)
> **Stack produção:** Vue 3 + Vuetify 3 + Nuxt 3 + Pinia (FE) · FastAPI/Python (BE) · PostgreSQL
> **Skills obrigatórias FE:** `/vue-migration-prep` · `/design-standardize` · `/feature-impact`

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
  SendGrid/Resend, WhatsApp via Meta/Twilio).

Historia de Usuario: |
  Como candidato contratado, quero receber uma mensagem de parabéns
  pela contratação. Como candidato não selecionado, quero receber uma
  comunicação respeitosa informando que a vaga foi encerrada, para ter
  um encerramento digno do processo.

Regras de Negocio:
  1. Envio é assíncrono (não bloqueia a UI) — disparado via fila (RabbitMQ/Celery)
  2. Email via SendGrid (primário) com fallback para Resend/Mailgun
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

**Email (SendGrid):**
```python
# lia-agent-system/app/services/email_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

async def send_email(to: str, subject: str, body: str, template_id: str = None):
    sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
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

| Sprint | Cards | SPs | Entregável Principal |
|--------|-------|-----|----------------------|
| **S1 — Fundação** | 17 | 74 | Modelos de dados, APIs base, VGM S1, TRI-008 proxy, AUD P0/P1 |
| **S2 — Fluxo Completo** | 23 | 131 | Inscrição → Chat Web Triagem → Comunicação |
| **S3 — Refinamentos** | 4 | 17 | AUD observabilidade, VGM-010 |
| **TOTAL** | **44** | **222** | MVP Alpha 1 completo em S1+S2 |

**Caminho crítico do MVP Alpha 1:**
```
SAT-001 → INS-003 → INS-001 → SAT-007
COM-001 → SAT-005 → COM-004
TRI-001 → TRI-005 → TRI-002 → (Chat Web funcional)
VGM-001 → VGM-005 → VGM-006 (Vaga publicada)
AUD-001 → AUD-002 → AUD-003 (Auditoria mínima ativa)
```

---

*Documento v3.0 — 11/março/2026. Cards PIP (pipeline-transition) removidos nesta versão. Enriquecido com 100% do conteúdo das fontes canônicas. Consolida cards de: `saturacao-chatweb-comunicacao-cards-jira.md` (27 cards), `jira-cards-job-creation-lifecycle.md` (10 cards), `diagnostico-agentes-mvp.md` + `ANALISE_COMPARATIVA_V5_vs_LIA.md` (7 cards AUD). Roadmap alinhado ao fluxo MVP Alpha 1 (9 passos) do diagnóstico de agentes. Total: 44 cards · 222 SPs.*
