# Agent Studio — Resgate do Plano de Transformação + Gap Analysis

> Reconstruído em 2026-05-31 a partir de: git log (timeline de fases), testes de
> reestruturação (`AgentStudioRestructure.test.tsx`), estrutura do `ServiceFunnelView`,
> e auditoria funcional via curl/código desta sessão. **Não existia doc único** — o
> plano foi executado em fases ao longo de várias sessões, em grande parte conversacional.

---

## 1. A visão da transformação

Transformar o Agent Studio de uma **lista técnica de agentes** (jargão de IA, formulário
avançado, "criar do zero") para um **funil guiado pelas etapas do processo de recrutamento**,
operável por recrutador leigo. Cada etapa do funil = um "serviço" com status, métrica e
ação contextual.

**As 7 etapas do funil** (`ServiceSlug`):
`intake → alignment → sourcing → screening → calibration → offer → nps`

Princípios do redesign (extraídos dos testes/commits):
- Sem jargão de IA; linguagem de RH (Fase 3 Sprint 1).
- "Mostrar o agente em ação" (preview de conversa) antes de ativar (Sprint 2).
- Test-as-you-build: sandbox inline (Sprint 3).
- Galeria de templates em 2 zonas + "Seus agentes" unificado somando sourcing+custom (Sprint 5).
- Config humana do agente para recrutador (Sprint 4).
- White-label / per-tenant persona (sem marca hardcoded).

---

## 2. Timeline das fases (do git, mais antigo → recente)

| Bloco | Entrega | Status |
|---|---|---|
| **C1–C5** | Motor de runtime unificado: `dispatch_agent_deployment_task`, scheduler, BYOK, event-driven consumer, monitoring de runs, Daily Digest, índices perf | ✅ shipado |
| **Q4.x** | Sandbox dry-run (intercepta write tools), tour interno, i18n sensor BLOCKING | ✅ shipado |
| **Fase 1** | "Meus Agentes" reestruturado: remove "Criar do zero"/"Formulário Avançado", TemplateGallery com labels "Tipo/Vertical" | ✅ shipado |
| **Fase 2.5** | Sensores agregados, hardcoded-strings, CI wire | ✅ shipado |
| **Fase 3 Sprint 1–5** | Redesign card+detail panel recruiter-friendly, compliance DESIGN.md, preview de conversa, sandbox inline, config humana, galeria 2 zonas, acento de categoria | ✅ shipado |
| **Sprints 11–12** | Funil de serviços completo: linhas offer + nps + manager alignment; `ServiceFunnelView` | ✅ shipado (com bugs — ver §4) |

**Gap de numeração:** não há evidência de "Fase 2" (não-.5) nem "Sprints 6–10" como blocos
nomeados. Provavelmente trabalho intermediário absorvido nos blocos C1–C5 / Q4. Não é
lacuna de produto — é só numeração não-contígua.

---

## 3. Estado por etapa do funil (planejado vs construído vs gap)

Legenda: ✅ funcional (verificado) · ⚠️ funciona com ressalva · ❌ gap

| # | Etapa | Painel (expandir) | Ação primária | API verificada | Gaps |
|---|---|---|---|---|---|
| 1 | **intake** (vagas) | lista de vagas (live/draft) → editar | navega p/ /jobs | job-vacancies 200 | Sem ação de "criar vaga" direta no funil (só lista as existentes) |
| 2 | **alignment** (gestor) | `AlignmentStatusCard` | solicitar alinhamento → email gestor | ✅ E2E completo testado | nenhum (fechado nesta sessão) |
| 3 | **sourcing** (captação) | `sourcingPanel` (templates + criar) | criar agente | ✅ create 422-valid (corrigido) | ❌ **sem editar / re-vincular** (ver §4) |
| 4 | **screening** (triagem) | ❌ **sem painel** | navega p/ perguntas da vaga | studio-summary 200 | ❌ não tem painel de status próprio; ação é só navegação |
| 5 | **calibration** (gêmeos) | `TwinsList` + criar twin | criar/avaliar twin | twin create 422-valid | a verificar: fluxo de avaliação completo |
| 6 | **offer** (ofertas) | `OfferStatusCard` | criar/enviar oferta | offer create 422-valid | a verificar render+envio real na UI |
| 7 | **nps** (satisfação) | `NpsStatusCard` | enviar pesquisa NPS | nps send 422-valid | a verificar render+envio real na UI |

**Observação:** "422-valid" = endpoint existe e valida o body (corpo vazio → 422). Confirma
que o caminho API está cabeado e o backend responde. NÃO confirma que o clique na UI
renderiza e completa (essa camada visual não foi testada no browser — download do headless
travou).

---

## 4. Gaps transversais (o que ainda não está 100%)

### 4.1 🔴 Ciclo de vida do sourcing agent — incompleto e "split-brain"
- **Criar** ✅ (CreateAgentModal: nome + template + vínculo vaga/pool/nenhum + preferências).
- **Editar** ⚠️ — o **card de sourcing não tem botão Editar** (só pausar/retomar, calibrar,
  navegar). No backend o sourcing agent **é** um `CustomAgent (category='sourcing')`, então
  ele aparece também em "Meus Agentes" onde há Editar (`/agent-studio/[id]/edit`). Resultado:
  o mesmo agente em dois lugares com capacidades diferentes. Confuso.
- **Re-vincular vaga/banco** ❌ — só na criação. O form de edição é o de custom agent
  genérico; não expõe os campos de vínculo. Mudar vínculo de agente existente: **não dá**.

**Causa raiz:** o backend unificou sourcing→CustomAgent (refactor Sprint 7B-3b), mas o
**frontend manteve dois modelos** (card de sourcing próprio SEM edit + card de custom COM
edit). A unificação parou no meio.

### 4.2 ⚠️ screening sem painel próprio
Único serviço do funil sem painel de status. Clicar navega p/ a aba de perguntas da vaga
(corrigido nesta sessão para não ser dead-click). Falta um painel de status de triagem
(ex: % vagas com triagem configurada, link rápido).

### 4.3 ✅ 6 bugs estruturais corrigidos nesta sessão (estavam mascarados por `allSettled`)
1. Middleware bloqueava endpoints públicos de respond (align + NPS → 401).
2. Proxy `sourcing-agents` ausente (404).
3. Handlers sourcing usavam modelo removido → ImportError 500.
4. Cliques no funil no-op em 5/7 serviços.
5. Proxies `studio-summary` + `agent-quota` ausentes (404).
6. `agent-template-catalog` 100% morto (router nunca montado + proxies quebrados).

### 4.4 Padrão de risco: `allSettled` + `.ok` mascara features quebradas
3 dos 6 bugs degradavam silenciosamente (lista vazia, sem erro visível). Recomendado:
sensor que loga quando essas chamadas falham.

---

## 5. O que falta — recomendações priorizadas

**P0 — fechar o ciclo do sourcing agent (a dor do Paulo):**
1. Card de sourcing ganha botão **Editar** → `/agent-studio/[id]/edit` (já é CustomAgent).
2. Form de edição passa a expor **re-vínculo a vaga/banco** (campos job_id/talent_pool_id).
3. Decidir a unificação visual: ou o sourcing some de "Meus Agentes" (só no funil), ou
   o card do funil vira um link pro card unificado. Eliminar o split-brain.

**P1 — completar as etapas:**
4. Painel de status para **screening** (paridade com offer/nps).
5. Verificar na UI real (browser) que offer/nps/calibration renderizam e completam o envio.

**P2 — robustez:**
6. Sensor de telemetria para falhas mascaradas por `allSettled`.
7. Doc canonical desta arquitetura (este arquivo é o início).

---

## 6. Veredito

A transformação foi **executada em ~90%**: o funil de 7 etapas existe, o motor de runtime
(C1–C5) está sólido, o redesign recruiter-friendly (Fase 1/3) está shipado, e os 6 bugs
estruturais que quebravam o uso real foram corrigidos nesta sessão.

O **10% que falta** é concentrado e claro: **o ciclo de vida do sourcing agent (editar/
re-vincular) e a unificação dos dois modelos de card**. É o que faz o Paulo sentir que
"não está claro se tudo funciona" — porque, para sourcing, de fato não está fechado.
