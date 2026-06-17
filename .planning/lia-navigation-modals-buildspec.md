# Build-Spec — Navegação + Modais Universais da LIA (instrução técnica auto-contida)

> **Para uma sessão NOVA executar do zero.** Objetivo: a LIA (chat) consegue **navegar para qualquer página** da plataforma e **abrir qualquer modal/painel relevante** — de forma o mais determinística possível, segura (HITL onde precisa) e auditável.
> Escrito 2026-06-06. Fonte da verdade: Replit `ssh replit-wedo-0405` → `/home/runner/workspace/` (`lia-agent-system/` backend Python, `plataforma-lia/` frontend Next.js), branch `feat/benefits-prv-canonical`.
> **NÃO confunda com "o restante" da saga chat-fixes** (funil-zero + PII-contato) — isto é só navegação/modais.

---

## 0. CONSTRAINTS INQUEBRÁVEIS (CLAUDE.md — ler ANTES de tocar código)
- **Replit é a ÚNICA fonte da verdade.** Ler/editar SÓ em `/home/runner/workspace/` via SSH. NUNCA ler de clone GitHub. NUNCA `git push` / `gh pr` / escrita remota. Commits ficam locais no Replit.
- **Commit atômico com pathspec explícito:** `git commit -m "..." -- <paths>`. Arquivo novo: `git add <path-exato> && git commit -- <path>`. NUNCA `git add .`/`-A`. Paths com `[brackets]` (App Router): prefixar `GIT_LITERAL_PATHSPECS=1`. Verificar `git branch --show-current` == `feat/benefits-prv-canonical` ANTES.
- **TDD obrigatório:** Red→Green. Sensor por mudança.
- **Multi-tenancy:** `company_id` SEMPRE do JWT (`Depends(require_company_id)`), nunca do payload/LLM.
- **Computacional > inferencial:** preferir mapa determinístico a "o LLM decide". Marker emitido pelo LLM é inferencial — minimizar dependência onde der.
- **Frontend:** hooks no topo (rules-of-hooks), design tokens (sem cor/spacing hardcoded), i18n via next-intl (toda key em `messages/pt-BR.json` E `messages/en.json`), `npx eslint <arquivo> --max-warnings=0`.
- **Next.js App Router:** um único nome de slug dinâmico por nível (`[id]`, não `[id]`+`[masterId]`).
- **Sem silent fallback / sem proveniência fabricada.**
- **Editar no Replit:** Python longo às vezes dropa SSH (osv-scanner storm); `rg` corrompe tokens — usar `sed`/`grep -n`/`cat`. Editar via `python3` string-replace OU heredoc `<<'PYEOF'` (quoted = backticks literais).

---

## 1. COMO FUNCIONA HOJE (arquitetura end-to-end)

### 1.1 Navegação (page)
```
Agente LLM emite no texto da resposta: [NAVIGATE:<canonical_page>]  ou  [NAVIGATE:vaga_detalhe:<id>]
   │ (instrução no prompt: app/shared/prompts/system_prompt_builder.py — seção "Capabilities — Navegação")
   ▼
BACKEND extrai o marker:
   app/orchestrator/context/chat_adapter.py :: _extract_navigate_marker(text)
     -> regex L244: \[NAVIGATE:\s*([a-z][a-z0-9_-]*)\s*(?:[:?]\s*(?:id=)?\s*([^\]\s]+))?\s*\]
     -> retorna 3-tupla (clean_text, canonical_page, params{id?})  [normaliza via app/shared/canonical_pages.normalize_page]
   Caminho bolha/SSE: app/api/v1/agent_chat_sse.py (~L817-833) reusa _extract_navigate_marker -> ui_action="navigate_to", ui_action_params={page, **params}
   Serializer: app/shared/chat_event_serializer.py (serialize_message recebe ui_action + ui_action_params)
   ▼
FRONTEND consome:
   plataforma-lia/src/hooks/chat/useUIAction.ts :: case "navigate_to"
     -> canonicalPageToUrl(page, locale, id) (src/lib/canonical-pages.ts) -> router.push(url)
     -> se canonicalPageToUrl retorna null (page sem rota) -> return false (re-emite p/ handler page-specific; NÃO navega)
```

### 1.2 Modais / painéis (ui_action != navigate_to)
```
Mecanismo SEPARADO de navegação. ui_actions suportados pelo FE (src/types/ui-action.ts :: GLOBAL_UI_ACTION_TYPES):
   navigate_to, open_modal, open_offer_review, wizard_step, open_panel, scroll_to,
   settings_open_tab, open_communication_modal, open_schedule_modal, open_screening_modal
Handler: src/hooks/chat/useUIAction.ts despacha cada um:
   - open_modal -> window.dispatchEvent(new CustomEvent("lia:open_modal", {detail:{modal_id, data}}))
   - open_panel -> "lia:open_panel"; open_offer_review -> "lia:open_offer_review"; settings_open_tab -> router.push(/configuracoes?section=...) + "lia:settings-action"
Dispatcher central de modais:
   src/components/lia-global-modals/LIAGlobalModals.tsx — escuta lia:open_modal / lia:open_offer_review e monta o modal.
   (montado em src/components/layout/DeferredLayoutClients.tsx)
REGISTRY canônico de capabilities (SINGLE SOURCE OF TRUTH):
   lia-agent-system/app/config/capability_map.yaml — cada intent tem: chat_executable, entity_required[], modal_id?, navigate_fallback?
     Regra (sensor tests/unit/services/test_pr_j_capability_map.py): todo intent tem navigate_fallback OU modal_id.
Atalhos de UI (cards do chat): src/components/ui/chat-workflow-reels.tsx :: MODAL_OVERRIDES (hoje só add_candidate, create_job)
```

### 1.3 Quem dispara o ui_action de modal hoje
- O **agente NÃO emite modais por navegação livre.** Modais só abrem quando uma **tool específica** retorna um ui_action (ex: tools de config -> settings_open_tab; tool de oferta -> open_offer_review) OU quando um card do chat (chat-workflow-reels) tem modal_id (MODAL_OVERRIDES).
- A seção de prompt "Capabilities — Navegação" cobre **só `[NAVIGATE:...]`** (páginas), NÃO modais.

---

## 2. INVENTÁRIO DO ESTADO ATUAL (exaustivo — verificado 2026-06-06)

### 2.1 Páginas canônicas (`CanonicalPage` enum)
Mirror obrigatório TS↔Py:
- `lia-agent-system/app/shared/canonical_pages.py` (enum + PAGE_SHORT_LABELS_PT_BR + LEGACY_PAGE_ALIASES + normalize_page)
- `plataforma-lia/src/lib/canonical-pages.ts` (CANONICAL_PAGES + routeToCanonicalPage + canonicalPageToUrl + labels)

Enum atual (18): home, vagas, vaga_detalhe, recrutar, funil_talentos, candidato_detalhe, pipeline_kanban, dashboard, configuracoes, agent_studio, ajuda, bancos_talentos, biblioteca, central_comunicacao, tasks, chat, trust, general(sentinel).

`canonicalPageToUrl(page, locale, id)` → rota (estado atual):
| canonical | rota | navega? |
|---|---|---|
| home | /{loc}/ | ✅ |
| vagas | /{loc}/jobs | ✅ |
| recrutar | /{loc}/recrutar | ✅ |
| funil_talentos | /{loc}/funil-de-talentos | ✅ |
| configuracoes | /{loc}/configuracoes | ✅ |
| agent_studio | /{loc}/agent-studio | ✅ |
| ajuda | /{loc}/ajuda | ✅ |
| bancos_talentos | /{loc}/bancos-de-talentos | ✅ |
| biblioteca | /{loc}/biblioteca-lia | ✅ |
| central_comunicacao | /{loc}/central-comunicacao | ✅ |
| tasks | /{loc}/tasks | ✅ |
| chat | /{loc}/chat | ✅ |
| trust | /{loc}/trust | ✅ |
| vaga_detalhe + id | /{loc}/jobs/{id} | ✅ (só com id) |
| candidato_detalhe + id | /{loc}/funil-de-talentos/candidato/{id} | ✅ (só com id) |
| **pipeline_kanban** | **null** | ❌ GAP |
| **dashboard** | **null** | ❌ GAP |
| general | null | ✅ (sentinel, correto) |

### 2.2 Rotas REAIS do FE (page.tsx em src/app) que NÃO têm canonical page (gaps de cobertura)
`(dashboard)/agents/marketplace`, `(dashboard)/agent-studio/[id]/edit`, `(dashboard)/agent-studio/[id]/kpis`, `(dashboard)/configuracoes/ai-credits`, `integracoes-ats`, `(staff)/wedo-admin` (+ fairness, fairness/bias-audit, governanca/ai-performance, governanca/ai-transparency, governanca/audit-logs, governanca/automation-rules, governanca/policy-engine), `teams-tab` (+ candidatos, dashboard, pipeline, vagas), `design-system`, `onboarding`, `nps/[token]`, `align/[token]`, `portal/data-request/[token]`, `shared/[token]`, `triagem/*` (preview/token — fluxo candidato, fora de escopo de recrutador).
> Decisão necessária (§10): quais dessas devem ser navegáveis pela LIA do recrutador. Provavelmente: agents/marketplace, configuracoes/ai-credits, integracoes-ats, e (se o usuário for staff) wedo-admin/*. teams-tab/* é legado (confirmar). triagem/* é candidato (NÃO expor).

### 2.3 ui_actions suportados (src/types/ui-action.ts)
navigate_to · open_modal · open_offer_review · wizard_step · open_panel · scroll_to · settings_open_tab · open_communication_modal · open_schedule_modal · open_screening_modal.

### 2.4 Modais (componentes ~40 em src/components/modals/ + outros)
Inventário parcial: create-job, create-job-with-candidates, add-to-list, job-duplicate, new-candidate-unified, profile, candidate-compare, job-assign-recruiter, english-test, job-compare, job-insights, job-unpublish, job-status, data-request, general-score, technical-test, add-candidates-to-vacancy, close-vacancy, screening-media, share-search, unified-communication, job-publish, bulk-action, stage-transition-actions, add-candidate, alert-settings, send-email, email-template-form, etc.
Dispatcher: `LIAGlobalModals.tsx` (escuta lia:open_modal / lia:open_offer_review). Hoje wira POUCOS (offer_review + via MODAL_OVERRIDES: add_candidate, create_job). **A maioria dos modais NÃO é abrível pelo agente.**

### 2.5 O que o agente JÁ sabe (prompt)
`system_prompt_builder.py` seção "### Capabilities — Navegação": lista as 18 canonical pages, ensina `[NAVIGATE:<page>]`, REGRA 5 (navega direto, não pergunta) + REGRA 6 (forma com id para vaga_detalhe/candidato_detalhe). **NÃO ensina modais.**

### 2.6 Baseline já commitado (saga chat-fixes 2026-06-06, sem push — NÃO refazer)
`5aeae5d74` navigate_to usa canonicalPageToUrl (corrige 404 /pt/vagas) · `892fd3375` REGRAS 5+6 de navegação (#5/#6). O fix-404 + #5/#6 já estão prontos; ESTE spec EXPANDE a cobertura.

---

## 3. GAPS PRECISOS (o que falta para "navegar qualquer página + abrir qualquer modal")
1. **2 páginas canônicas sem rota** (canonicalPageToUrl → null): `dashboard`, `pipeline_kanban`.
2. **~12 rotas reais do FE sem canonical page** (§2.2) → o agente não consegue nomeá-las/navegá-las.
3. **Modais NÃO expostos ao agente:** o agente não tem como abrir a maioria dos ~40 modais (só navega páginas + os 2 de MODAL_OVERRIDES). Falta: (a) lista de modais abríveis no prompt/capability_map, (b) o LIAGlobalModals wirar cada modal_id.
4. **Deep sub-sections** não navegáveis: abas de Configurações (section/subsection/field — existe `settings_open_tab` mas o agente não emite), colunas/stages do kanban, abas de uma vaga (?tab=edit&section=X), ai-credits, etc.
5. **Segurança:** não há gate definido sobre QUAIS modais/ações o agente pode abrir sem confirmação humana (modais destrutivos: close-vacancy, bulk-action, reject — exigem HITL).

---

## 4. TARGET (definição de PRONTO)
1. **Toda página relevante ao recrutador é navegável** por nome canônico (com id quando detalhe). `canonicalPageToUrl` não retorna null para nenhuma página exposta.
2. **Todo modal/painel relevante é abrível** pelo agente via `capability_map.yaml` (single source of truth) → ui_action → `LIAGlobalModals`. O prompt ganha uma seção "Capabilities — Modais/Ações" DERIVADA do capability_map (não hand-maintained).
3. **Deep-links** suportados: abas de config, abas de vaga, stages do kanban.
4. **Segurança:** modais/ações destrutivas exigem confirmação (HITL) explícita; modais só de leitura abrem direto. Multi-tenancy + permissão de role respeitados.
5. **Lockstep TS↔Py** garantido por sensor (canonical_pages.py == canonical-pages.ts).
6. **Determinístico onde possível:** o mapa page→rota e capability→modal são computacionais; só a DECISÃO de navegar/abrir é inferencial (LLM), com a forma/id vindo do entity resolver (server-side).

---

## 5. PLANO DE IMPLEMENTAÇÃO (fases — cada uma fecha com sensor + commit atômico)

### Fase A — Cobertura completa de PÁGINAS
**A1.** Decidir o conjunto de páginas expostas (§10 decisão #1). Para cada nova página relevante:
- Adicionar à enum em `canonical_pages.py` (Py) **E** `canonical-pages.ts` (TS) — mesmos valores. (Ex: `dashboard` já existe na enum; falta a ROTA.)
- Adicionar a ROTA em `canonicalPageToUrl` (TS) — confirmar a rota real em `src/app/[locale]/(dashboard)/...`. Ex: `dashboard` → confirmar rota real (há `teams-tab/dashboard` + possivelmente uma home dashboard; decidir). `pipeline_kanban` → provavelmente `/funil-de-talentos` ou um deep-link de kanban; confirmar.
- Adicionar o pattern reverso em `routeToCanonicalPage` (TS) — para o page_type que o FE manda ao backend bater.
- Adicionar label em PAGE_SHORT_LABELS_PT_BR (Py) — o prompt lista isso.
**A2.** A seção de prompt já itera `for page in CanonicalPage` → novas páginas aparecem automaticamente. Garantir que cada uma tenha rota (senão o agente promete e o FE não cumpre).
**A3.** Sensor: teste que `canonicalPageToUrl(p)` != null para TODA página exposta (exceto general/detail-sem-id). Estender `plataforma-lia/src/lib/__tests__/canonical-pages.test.ts` (já existe; criado no fix-404).

### Fase B — MODAIS/AÇÕES via capability_map.yaml (o core do "abrir qualquer modal")
**B1.** Em `app/config/capability_map.yaml`: para cada modal/ação que o agente deve abrir, adicionar uma capability `{chat_executable, entity_required[], modal_id, navigate_fallback}`. (Já tem add_candidate, search_candidates, move_candidate→stage_transition, schedule_interview→InterviewSchedulingModal. Expandir para: compare_candidates→candidate_compare, view_profile→profile, send_communication→unified_communication, create_job→create_job, close_vacancy→close_vacancy [DESTRUTIVO→HITL], etc.)
**B2.** Backend: o agente precisa EMITIR o ui_action de modal. Padrão recomendado (computacional > marker inferencial): uma **tool federada `open_ui(capability, entity_ids)`** que valida contra o capability_map + retorna o ui_action correto (open_modal/open_panel + modal_id + data). Alternativamente (inferencial), um marker `[MODAL:<modal_id>:<entity_id>]` análogo ao [NAVIGATE:...], extraído por um `_extract_modal_marker` (espelhar `_extract_navigate_marker` em chat_adapter.py) + serializado como ui_action open_modal. **Decisão §10 #2.**
**B3.** FE: `LIAGlobalModals.tsx` deve ter um case para CADA modal_id do capability_map (montar o modal componente com a data). Hoje só tem offer_review. Padrão: `case "stage_transition": return <StageTransitionActionsModal .../>` etc. Importar os modais existentes de src/components/modals/.
**B4.** Prompt: ADICIONAR seção "### Capabilities — Modais/Ações" em `system_prompt_builder.py`, **DERIVADA do capability_map.yaml** (ler o yaml, listar capabilities com modal_id + o que cada uma faz + entity_required). NÃO hand-maintain (anti-drift, mesmo princípio da seção de navegação).
**B5.** Sensor: o test_pr_j_capability_map.py já pina "todo intent tem modal_id OU navigate_fallback". Adicionar: cada modal_id do capability_map tem um case no LIAGlobalModals (sensor cross-stack TS↔Py — pode ser um teste que lê o yaml + grep no LIAGlobalModals.tsx).

### Fase C — DEEP SUB-SECTIONS
- Configurações: `settings_open_tab` já existe (section/subsection/field) — fazer o agente emitir via capability_map (capability `open_settings_section` com params). Listener canônico: settings-page-enhanced.tsx:323.
- Vaga (abas): deep-link `/jobs/{id}?tab=edit&section=<descricao|perguntas|configuracoes>` (ver CLAUDE.md "Vacancy preview canonical pattern"). O agente pode emitir [NAVIGATE:vaga_detalhe:{id}] + query params (estender o marker/handler p/ query).
- Kanban stages: navegar p/ a vaga + foco numa coluna (scroll_to / open_panel).

### Fase D — SEGURANÇA / HITL
- Classificar cada capability: **read-only** (abre direto) vs **destrutiva/mutante** (close-vacancy, bulk-action, reject, send-email em massa → exigem confirmação humana ANTES de executar; o modal pode abrir, mas a AÇÃO dentro confirma).
- Multi-tenancy: o entity_id (vaga/candidato) sempre validado company-scoped server-side (o capability_map entity_required + a tool valida).
- Permissão de role: páginas staff (wedo-admin/*) só p/ `wedotalent_admin` — o agente não deve oferecer navegação pra elas a recrutador comum.

---

## 6. LOCKSTEP TS↔Py (CRÍTICO — não driftar)
- `canonical_pages.py` (enum, labels, aliases) DEVE espelhar `canonical-pages.ts` (CANONICAL_PAGES, labels, routeToCanonicalPage). Mudou um, muda o outro NO MESMO commit.
- Sensor recomendado (criar se não existir): script que compara os valores da enum Py vs TS + falha se divergirem. Modelo: o projeto já tem `scripts/check_lia_field_definitions_sync.py` (sync TS↔Py de outro domínio) — copiar o padrão.

## 7. TESTES/SENSORES (todos TDD, Red→Green)
1. `canonical-pages.test.ts` (TS) — toda página exposta tem rota; round-trip routeToCanonicalPage(canonicalPageToUrl(p))==p. (Estender o existente.)
2. `test_g3_navigation_capability.py` (Py) — a seção de navegação lista as páginas + a forma com id + a regra "navega direto". (Já existe; estender p/ novas páginas.)
3. Lockstep TS↔Py de canonical_pages (novo sensor §6).
4. `test_pr_j_capability_map.py` (Py) — já pina capability_map; estender: todo modal_id tem case no LIAGlobalModals.
5. Prompt-content: a seção "Capabilities — Modais/Ações" inclui as capabilities do yaml.
6. Contract: o backend (open_ui tool OU _extract_modal_marker) emite ui_action válido (modal_id ∈ capability_map). Multi-tenancy: entity company-scoped.

## 8. ARQUIVOS-CHAVE (mapa rápido)
BACKEND (lia-agent-system):
- app/shared/canonical_pages.py — enum + normalize_page + labels (lockstep TS)
- app/shared/prompts/system_prompt_builder.py — seção Capabilities — Navegação (e ADICIONAR Modais/Ações)
- app/orchestrator/context/chat_adapter.py — _extract_navigate_marker (espelhar p/ _extract_modal_marker se for marker)
- app/shared/chat_event_serializer.py — serialize_message (ui_action/ui_action_params)
- app/api/v1/agent_chat_sse.py — caminho bolha/SSE (extrai marker + emite ui_action) [HOT — coordenar]
- app/config/capability_map.yaml — REGISTRY canônico de capabilities (modais/ações)
- tests/unit/services/test_pr_j_capability_map.py — sensor do capability_map
FRONTEND (plataforma-lia):
- src/lib/canonical-pages.ts — CANONICAL_PAGES + canonicalPageToUrl + routeToCanonicalPage (lockstep Py)
- src/hooks/chat/useUIAction.ts — dispatcher de TODOS os ui_actions (navigate_to + modais)
- src/types/ui-action.ts — GLOBAL_UI_ACTION_TYPES (tipos de ui_action)
- src/components/lia-global-modals/LIAGlobalModals.tsx — dispatcher de modais (lia:open_modal) [ADICIONAR cases]
- src/components/modals/*.tsx — os ~40 modais a wirar
- src/components/ui/chat-workflow-reels.tsx — MODAL_OVERRIDES (cards do chat)
- src/lib/__tests__/canonical-pages.test.ts — sensor de rotas

## 9. COMANDOS DE DISCOVERY (re-verificar inventário antes de codar)
```
# Páginas reais do FE:
find plataforma-lia/src/app -name page.tsx | sed 's|.*/src/app/||;s|/page.tsx||' | sort
# canonicalPageToUrl (rotas atuais + nulls):
sed -n '/export function canonicalPageToUrl/,/^}/p' plataforma-lia/src/lib/canonical-pages.ts
# ui_actions suportados:
grep -nE "type:|GLOBAL_UI_ACTION_TYPES" plataforma-lia/src/types/ui-action.ts
# Modais existentes:
find plataforma-lia/src/components -iname '*modal*.tsx' | sed 's|.*/components/||'
# Modais wirados no dispatcher:
cat plataforma-lia/src/components/lia-global-modals/LIAGlobalModals.tsx
# Capabilities canônicas:
cat lia-agent-system/app/config/capability_map.yaml
# Seção de navegação do prompt:
sed -n '/Capabilities — Naveg/,/])/p' lia-agent-system/app/shared/prompts/system_prompt_builder.py
```

## 10. DECISÕES ABERTAS (precisam do Paulo antes/ durante)
1. **Quais páginas expor** (§2.2): agents/marketplace, configuracoes/ai-credits, integracoes-ats, wedo-admin/* (só staff?), teams-tab/* (legado?), triagem/* (NÃO — é candidato). 
2. **Mecanismo de modal:** tool `open_ui(capability)` (computacional, recomendado) vs marker `[MODAL:...]` (inferencial, espelha [NAVIGATE]). Recomendação: tool (determinístico + valida entity + multi-tenancy).
3. **Quais modais o agente PODE abrir** e quais são **destrutivos** (HITL obrigatório): close-vacancy, bulk-action, reject, send-email/whatsapp em massa.
4. **dashboard / pipeline_kanban:** confirmar a rota real (há `teams-tab/dashboard` + `funil-de-talentos`; decidir o destino canônico).
5. **Permissão por role:** o agente respeita role (recrutador vs wedotalent_admin) ao oferecer navegação/modais.

---
**Resumo de execução:** Fase A (páginas, lockstep+sensor) → Fase B (modais via capability_map + LIAGlobalModals + prompt derivado + tool open_ui) → Fase C (deep-links) → Fase D (segurança/HITL). Cada fase: TDD + commit atômico pathspec, sem push, branch feat/benefits-prv-canonical. Validação live do Paulo entre as fases arriscadas.
