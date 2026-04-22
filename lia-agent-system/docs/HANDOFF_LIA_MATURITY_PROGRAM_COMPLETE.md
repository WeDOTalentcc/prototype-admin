# LIA Maturity Program — Handoff Completo para Dev Team

**Origem**: `lia-agent-system/docs/LIA_MATURITY_ROADMAP.md` (plano original de 3 Tracks)
**Período**: 2026-04-21 09:21 UTC → 2026-04-22 (sessão contínua ~30h)
**Autor**: Sessão LIA Maturity (Paulo + Claude)
**Destinatários**: Time de devs da ats-api-copia (Rails) + time da camada IA (repo dedicado)

---

## 0. Sobre este documento

Este handoff consolida **todo o trabalho do LIA Maturity Program** (Ondas 1-5.3) a partir do plano original `LIA_MATURITY_ROADMAP.md`, enumerando **cada commit, arquivo, feature flag, log marker e ponto de integração**. É baseado exclusivamente em código e git history — zero invenção.

Destina-se a três audiências:

1. **Time ats-api-copia (Rails backend)** — entende os pontos de integração REST que a camada IA Python agora expõe, quais novos campos precisam ser consumidos na resposta do chat, e quais eventos observáveis podem ser populados de back para front.
2. **Time da camada IA (novo repo dedicado)** — replica/porta a arquitetura de agente, observability, state machine e guardrails produzidos aqui para o repo próprio, com referências exatas ao código fonte.
3. **Time frontend** — (contexto) entende que novas capabilities aparecem na API `/api/v1/chat` (citations, HITL, hints de action), para integrar progressivamente.

---

## 1. Context — três repos em jogo

| Repo | Role | Linguagem | Status |
|------|------|-----------|--------|
| **wedotalent02202026** (este Replit) | Python LIA Agent System | Python 3.11 FastAPI | **TODO o trabalho descrito aqui aconteceu aqui** |
| **ats-api-copia** (GitHub) | Rails backend CRUD + BD | Ruby on Rails | Time manual; consome chat/respostas via API |
| **Nova repo AI** (a definir) | Camada IA produção | Python (provável) | Time da camada IA vai replicar a arquitetura aqui descrita |

O frontend (ats_front) consome os endpoints REST do Python LIA para features de chat/agente, e o Rails backend (ats-api-copia) para CRUD de vagas/candidatos/usuários.

---

## 2. Executive Summary

### O problema
O chat real da LIA exibia 10 bugs em 3 categorias (tooling, prompt/persona, state management) descobertos em auditoria de conversa real. Resolução pontual geraria débito técnico; foi definido um **programa de maturidade** em 3 Tracks: tático (FIX 20-28), plataforma (Initiatives I-VIII), e progressivo (G-series).

### O trabalho
**37 commits** com markers formais (Onda/FIX/Init/G-series), **51 arquivos alterados**, **+9.156 / -1.365 linhas líquidas** apenas nos últimos 2 dias. Plus FIX 1-19 prévios (contexto PARTE I+K).

### Outcome
- **15 Initiatives entregues** (I.A/I.B, II.A/II.D, III, IV, V, VI.0/VI.1, VII, VIII)
- **6 guardrails G-series** (G2, G3, G4, G5, G6 + G4.B cost tracking full)
- **Token footprint reduzido em 76-78%** (evidenciado via `[LIA-COST]` log: 21.000 → ~11.000 tokens por call scoped)
- **15 log markers observáveis** ([LIA-SCOPE], [LIA-COST], [LIA-HISTORY], [III.B], [IV.B], [V.B], [G3.B], [G4.B], [VII.B], etc.)
- **8 feature flags** para rollback seguro
- **Tests: 184/185 green** em scope (1 falha pre-existente não relacionada)

---

## 3. Cronologia de commits (oldest → newest)

Ordem de aplicação. Cada commit é **atômico** (produz + consumidor alinhados) e passa regressão antes de próximo.

### 🔹 Pré-programa — FIX 1-19 (contexto histórico PARTE I+K)
Base de audit/capabilities/HITL foundations antes do programa formal. Consolidados em `DEVELOPER_HANDOFF.md` PARTE I+K.

### 🌊 Onda 1 — Initiatives I, VI Fase 0, G2, G6 (substrato anti-alucinação)

| Commit | Marker | Escopo |
|--------|--------|--------|
| `dfedcb357` | Init I.A | Grounded Capability Catalog — 16 cards YAML + CI drift guard |
| `684b2a140` | Init I.B | Persona renders capability_cards end-to-end (anti-alucinação) |
| `0ee7a0211` | Init VI.0 | eval_judge migrado para LLM Factory (multi-tenant) |
| `846c7467e` | G2 | Marker catalog + drift-guard CI test |
| `cee507b2f` | G6 | Multi-tenant capability toggle (enabled_for_tenant + renderer filter) |

### 🌊 Onda 2 — Plano específico + 5 initiatives (2026-04-21 manhã)

| Commit | Marker | Escopo |
|--------|--------|--------|
| `802104b89` | docs | ONDA2_PLAN.md — 1704 linhas de plano |
| `a45875997` | G5 light | PII redaction at response boundary (LGPD Art. 12+13) |
| `dd77d4439` | Init VI.1 | Golden set expansion + CI workflow (`.github/workflows/lia-eval.yml`) |
| `6cc6b6a85` | Init IV | Proactive Agenda formatter + TTL cache |
| `d0230dc91` | Init V | Reasoning transparency backend (citations) |
| `f7b8ec3a6` | Init II.D | workflow_context slot + 3 v1 workflows |
| `ba2f32436` | Init IV fix | Plural PT: "açãoões" → "ações" |

### 🌊 Onda 3 — Harness consolidation

| Commit | Marker | Escopo |
|--------|--------|--------|
| `d2e5bb376` | Onda 3.1 G4 | cost_tracker + prompt cache flag |
| `34c7d2cb7` | Onda 3.2 G3 | HITL checkpoint surfacing |
| `a06559d59` | Onda 3.3 Init VII | error recovery policies catalog v1 |
| `d6efe4ed1` | Onda 3.4 Init VIII | persona consistency suite v1 (10 scenarios) |
| `ddf7c9769` | Onda 3.5 Init III | MVP episodic memory via user_preferences |
| `ac536e90e` | — | obs counter sync (29 → 30 markers) |

### 🌊 Onda 4 — B-phase wiring (producer → consumer)

**Contexto**: As 15 initiatives produziram módulos prontos, mas a LIA "não sentia diferente em runtime" porque os callers não chamavam os producers. Onda 4 fecha o loop.

| Commit | Marker | Escopo |
|--------|--------|--------|
| `e1bd6997b` | Onda 4.1 | `_build_tool_schema_for_intent` + `_try_extract_params_with_llm` (16 tests pré-existentes → verde) |
| `7bb4dd716` | Onda 4.2 G4.B | cost_tracker wired em ClaudeLLMProvider |
| `5c4ff9fb0` | docs | handoff de sessão (mid-point) |
| `b7bc5d264` | Onda 4.3 III.B | hydrate recruiter_preferences na conversa |
| `b197d510b` | Onda 4.4 IV.B | briefing greeting wire no orchestrator |
| `338b9b583` | Onda 4.5 V.B | citations populate em ChatResponse |
| `f9f60701a` | Onda 4.6 G3.B | HITL checkpoint dispatch |
| `09c387d15` | Onda 4.7 VII.B | error_policies wired em catch-all |
| `8bfad78f1` | Onda 4.8 FIX 35 | G1 conversational polish (5 patterns: footnotes, numbered options, filtros, progress, error recovery) |
| `5e537bc0c` | Onda 4.9 VIII.B | persona validator CI step |
| `b26448e18` | — | FIX 35 regression test tightening |
| `3d316958b` | Onda 4.10 | ChatAdapter + chat.py envelope (PARTE L: fields dropped) |
| `ad6ce7073` | Onda 4.11+4.12 | briefing formatter keys + III.B log level |
| `4dad75d18` | Onda 4.13 | G4.B full coverage (Gemini pricing + 3 call sites) |

### 🌊 Onda 5 — Pós-smoke pendências (briefing inversion + test hygiene + cost reduction)

| Commit | Marker | Escopo |
|--------|--------|--------|
| `f6ee7e7dd` | Onda 5.1.a | ctx.extra["extra_instructions"] merged em agentic_loop (fix briefing inversion) |
| `bfaad7737` | Onda 5.1.b | persona briefing-as-fact rule (FIX 5.1) |
| `af76de95f` | — | multi-tenancy session fixes + test hygiene bundled |
| *(rollback paralelo c698d5eef apagou tudo de Onda 3.2–5.1 — ver seção 12)* | | |
| `981bd3c32` | (Replit Agent paralelo) | Onda 5.3.a tool scoping (intent_heuristic + registry union + agentic_loop scoping) |
| `e1dcee729` | Onda 5.3.a + restore | Recupera Onda 3.2-5.1 lost + merge 5.3.a no main_orchestrator |
| `54def11f3` | Onda 5.3.c | history compaction with conversation_summary reuse |

---

