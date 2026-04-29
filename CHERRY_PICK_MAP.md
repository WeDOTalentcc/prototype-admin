# Cherry-pick Map — Replit `main` (15/mar → 29/abr/2026)

> Janela: **15/mar/2026 → 29/abr/2026** (≈6 semanas)  
> Total de commits: **3491**  
> Repositório: Replit `/home/runner/workspace` (push manual → `WeDOTalentcc/wedotalent02202026` branch `replit-sync`)  
> Gerado em: 2026-04-29 12:47 | **v3** com path inference + coluna Risco + arquivo principal/anexos separados  

> 📂 **Anexos** (cross-cutting, auto-commits do Replit, lista cronológica completa) em [CHERRY_PICK_APPENDICES.md](CHERRY_PICK_APPENDICES.md)

## Como usar este documento

Mapa de **cherry-pick seletivo** dos commits do Replit para o ambiente do time. Cada commit é classificado em camada + feature + nível de risco.

### Coluna Risco — semáforo
- 🟢 **BAIXO** — Frontend isolado pequeno, Docs, Testes, Empty/merge → safe pra subir
- 🟡 **MÉDIO** — IA isolada, Backend, Cross IA↔Back, Frontend grande, Auto-commit Replit → revisar contexto antes
- 🔴 **ALTO** — Cross IA↔Front, Cross Back↔Front, Cross Rails+Replit, mudanças >30 arquivos → cherry-pick parcial QUEBRA. Subir tudo da feature ou nada.

### Camadas
- **IA** — `lia/agents`, `lia/tools`, `lia/orchestrator`, `app/orchestrator`, `app/shared/prompts`, `fairness_guard`, `agentic_loop`
- **Backend** — `lia-agent-system/` exceto IA (rotas, services, db, models)
- **Frontend (UI)** — `plataforma-lia/components|pages|app` (`.tsx/.jsx`)
- **Rails (ats-api)** — `ats-api-copia/` (Postgres principal, ActiveRecord, migrations)
- **Cross …↔…** — toca múltiplas camadas; alto risco se subir parcial
- **Docs / Testes / Infra / Auto-commit Replit** — geralmente acompanham, raramente isoladamente acionáveis

### Regras
1. Commit 🔴 cross: cherry-pick **junto** com os irmãos da mesma feature
2. Antes de subir feature IA, valide se há commit Front correspondente — se não, fica órfã
3. Tags `milestone/*` indicam **bordas seguras de cherry-pick**
4. Auto-commits do Replit (🟡): abrir `git show <sha> --stat` antes
5. **Cada feature canônica tem cabeçalho com Descrição + Dependências + Arquivos + Docs** — leia antes

---

## 1. Resumo executivo

### 1.1 Distribuição por camada

| Camada | Qtd | % |
|---|---:|---:|
| Frontend (UI) | 917 | 26% |
| Backend | 675 | 19% |
| Docs | 387 | 11% |
| Outro | 306 | 8% |
| Auto-commit Replit | 260 | 7% |
| Cross IA↔Back | 230 | 6% |
| Cross Back↔Front | 208 | 5% |
| IA | 121 | 3% |
| Frontend (api/util) | 104 | 2% |
| Testes | 96 | 2% |
| Cross IA↔Front | 95 | 2% |
| Empty/merge | 74 | 2% |
| Infra/Config | 11 | 0% |
| Rails (ats-api) | 6 | 0% |
| Cross Rails+Replit | 1 | 0% |
| **Total** | **3491** | **100%** |

⚠️ **534 commits cross-cutting** — alto risco pra cherry-pick parcial.

### 1.2 Distribuição por risco

| Risco | Qtd | % |
|---|---:|---:|
| 🟢 BAIXO | 1243 | 35% |
| 🟡 MÉDIO | 1852 | 53% |
| 🔴 ALTO | 396 | 11% |

### 1.3 Top 30 features por volume de commits

| # | Feature / Tema | Commits | Camadas que toca |
|---:|---|---:|---|
| 1 | Mockup Sandbox (artefato gerado) | 298 | Outro×264, Frontend (UI)×14, Backend×9, Cross Back↔Front×4 |
| 2 | (Auto-commit Replit) | 270 | Auto-commit Replit×260, Empty/merge×4, Outro×3, Frontend (UI)×2 |
| 3 | §15 WSI | 160 | Cross IA↔Back×41, Backend×23, IA×21, Cross IA↔Front×21 |
| 4 | Compliance / LGPD / EU AI Act | 149 | Backend×43, Docs×33, Frontend (UI)×21, Cross IA↔Back×15 |
| 5 | Configurações (hub) | 102 | Frontend (UI)×50, Backend×14, Cross Back↔Front×11, Docs×5 |
| 6 | §9 Security / Tenant guards | 78 | Backend×22, Frontend (UI)×17, Cross Back↔Front×13, Frontend (api/util)×6 |
| 7 | Kanban (vagas) | 75 | Frontend (UI)×60, Cross Back↔Front×4, Backend×4, Cross IA↔Front×3 |
| 8 | Frontend (componentes diversos) | 71 | Frontend (UI)×65, Cross Back↔Front×3, Cross IA↔Front×2, Outro×1 |
| 9 | §1 Teams Integration | 63 | Backend×30, Docs×8, Cross Back↔Front×8, Testes×4 |
| 10 | FastAPI v1 endpoints | 57 | Backend×40, Cross IA↔Back×12, Cross Back↔Front×4, Cross IA↔Front×1 |
| 11 | §2 Orchestrator Migration | 50 | IA×30, Cross IA↔Back×8, Cross IA↔Front×4, Backend×3 |
| 12 | Triagem (módulo) | 49 | Frontend (UI)×19, Cross Back↔Front×8, Backend×8, Empty/merge×4 |
| 13 | Tasks #712-#886 (Features de produto) | 48 | Frontend (UI)×16, Backend×13, Docs×4, Cross Back↔Front×4 |
| 14 | §6 Chat Unificado / Funil | 48 | Frontend (UI)×15, Backend×11, Cross Back↔Front×7, Frontend (api/util)×6 |
| 15 | Login UI (FE) | 41 | Frontend (UI)×39, Frontend (api/util)×1, Outro×1 |
| 16 | scope: phase2 | 41 | Backend×39, Cross IA↔Back×2 |
| 17 | Candidates (FE pages) | 36 | Frontend (UI)×33, Cross Back↔Front×2, Frontend (api/util)×1 |
| 18 | scope: guards | 33 | Backend×33 |
| 19 | Docs / Specs | 31 | Docs×22, Frontend (UI)×4, Frontend (api/util)×2, Cross IA↔Front×1 |
| 20 | Artefatos / Eval logs (sem código) | 30 | Backend×29, Outro×1 |
| 21 | Wizard (geral) | 30 | Frontend (UI)×13, Backend×7, Cross IA↔Back×5, Testes×3 |
| 22 | Skills / canonical-fix | 29 | Frontend (UI)×9, Docs×8, Empty/merge×6, Outro×3 |
| 23 | §7 WorkflowRail UX | 28 | Frontend (UI)×16, Cross Back↔Front×5, Backend×4, Testes×1 |
| 24 | i18n / Translation | 27 | Frontend (UI)×19, Frontend (api/util)×5, Docs×2, Cross IA↔Back×1 |
| 25 | Tasks #574-#712 (Janela anterior — chat/funil/glossário) | 25 | Backend×10, Cross IA↔Back×6, Cross Back↔Front×3, Frontend (UI)×2 |
| 26 | Automations | 24 | Empty/merge×8, Frontend (UI)×6, Backend×4, Cross Back↔Front×2 |
| 27 | Docs / Auditorias | 23 | Docs×21, Frontend (api/util)×1, Outro×1 |
| 28 | §17 Eval Framework | 23 | Backend×13, Cross IA↔Back×8, Cross IA↔Front×1, Cross Back↔Front×1 |
| 29 | Backend Proxy Routes (FE) | 22 | Cross Back↔Front×11, Frontend (UI)×10, Cross IA↔Front×1 |
| 30 | §16 LIA Persona | 22 | Backend×7, Cross IA↔Back×6, IA×6, Cross IA↔Front×1 |

_Total de features identificadas: **566**_

---

## 2. Cherry-pick por feature (ordem recomendada)

Cada feature lista seus commits em **ordem cronológica reversa** (mais novo primeiro). Para cherry-pick **subir do mais antigo para o mais novo**.

⚠️ **Cross-cutting** indica que a feature toca múltiplas camadas — cherry-pick parcial pode quebrar.

> **Filtro**: features com **≥ 3 commits** ou que tocam camada IA. Features menores no Apêndice D (anexos).

### Mockup Sandbox (artefato gerado)

**Descrição:** artifacts/mockup-sandbox — componentes gerados automaticamente, NÃO é código de produto. Pode ignorar para cherry-pick.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** artifacts/mockup-sandbox/**

**Docs de referência:** —

- **Commits:** 298  |  **Período:** 2026-03-22 → 2026-04-28  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×277 🟢×16 🔴×5

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `b3bed4f77` | 2026-04-28 | Outro | Add new screens for triagem flow to the mockup components — Update mockup-components.ts to include new triagem-flow components such as ChatScreen, CompletionScr | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `1efb02eab` | 2026-04-26 | Outro | Update mockups for candidate chat and polish — Replace import statements in mockup-components.ts to include newly added chat mockups. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `5ffc46a58` | 2026-04-26 | Outro | Task #854: Pixel-faithful candidate↔LIA chat mockup in mockup-sandbox — Adds a marketing-ready mockup of the candidate-side triagem chat at: | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts`<br>`artifacts/mockup-sandbox/src/components/mockups/triagem-flow/ChatScreen.tsx`<br>`artifacts/mockup-sandbox/src/index.css` |
| 🟡 | `8ef5059c0` | 2026-04-26 | Outro | Update mockups for toast notifications — Update mockup component imports for SonnerToasts and TemplateSuggestionToastMockup in `artifacts/moc | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `73c2bb8c4` | 2026-04-26 | Outro | Update mockups for chat usability and ElevenLabs funnel components — Update the generated mockups file to include the FunilElevenLabs component. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `a61728809` | 2026-04-26 | Outro | Update generated mockups to include previous welcome polish components — Re-adds mockups for ElevatedCards and TighterRhythm to the generated mockup components file. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `0d289cd77` | 2026-04-26 | Outro | Update mockups to include new chat usability components — Add new mock component imports to artifacts/mockup-sandbox/src/.generated/mockup-components.ts. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `d69734432` | 2026-04-26 | Outro | Update mock components to include chat usability features — Update artifacts/mockup-sandbox/src/.generated/mockup-components.ts to include mockups for chat usab | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `1d2562bce` | 2026-04-22 | Outro | Update mock component generation for display — Update mockup component generation to correctly include the FunilElevenLabs component. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `674f10e6f` | 2026-04-21 | Outro | Update mockups to include weekly digest components — Update the mock component import map to include the BellNotification, ChatFlutuante, and TeamsAdapti | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `c817b80f6` | 2026-04-21 | Outro | Update component registration to include chat welcome polish mockups — Update generated mockup components file to include entries for ElevatedCards and TighterRhythm from  | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `ebe39fccb` | 2026-04-21 | Outro | Update component imports for welcome polish mockups — Reorder mock component imports within `mockup-components.ts` to group chat welcome polish components | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `464bd2fe1` | 2026-04-21 | Outro | Update text size for badges to match other elements — Add new components related to the triagem flow to the mockups. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `7e76eb465` | 2026-04-21 | Outro | Make font size consistent across different screens — Update mockup component imports to ensure consistent font sizing. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `40241fd92` | 2026-04-21 | Outro | Update mock component definitions for weekly digest — Add weekly digest mock components to the generated module map. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `bf506d6f4` | 2026-04-21 | Outro | Adjust font sizes in notification and chat components to match design specifications — Update mockup components to correctly import weekly digest notification, floating chat, and adaptive | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `6ad99b6d5` | 2026-04-21 | Outro | Update component imports for weekly digest mockups — Modify `mockup-components.ts` to correctly import components related to the weekly digest feature. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `013add6fe` | 2026-04-21 | Outro | docs: reorganize handoff index and mark glossary as auto-generated — Task #731 — Reorganize handoff docs and push branch to GitHub. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `a62d34c1e` | 2026-04-21 | Outro | Add mockups for decision bar components to the generated module map — Update `mockup-components.ts` to include new mockups for Entrevista, Passive, Proposta, and Triagem  | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `6ce710f4a` | 2026-04-21 | Outro | Update component mapping to include decision bar mockups — Update `mockup-components.ts` to include dynamic imports for decision bar components. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `58fe6d8d9` | 2026-04-21 | Outro | Add toast notifications and template suggestions to mockups — Update generated mockups to include Sonner toast notifications and template suggestion components. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `9fa3a04e3` | 2026-04-21 | Outro | Update mock components to include toast notifications — Update the generated mock components file to include Sonner toast notifications. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `94643fc71` | 2026-04-20 | Outro | Add toast notifications to the mockups — Update mockups by adding Sonner toast notifications and template suggestion toast mockups. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `14b58f631` | 2026-04-20 | Outro | Update component list to include toast notifications — Updated the generated list of mockup components in `mockup-components.ts` to include toast notificat | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `ca296ef46` | 2026-04-20 | Outro | Add new mockups for decision bar components — Update `mockup-components.ts` to include mockups for Entrevista, Passive, Proposta, and Triagem comp | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `12d77a7cd` | 2026-04-20 | Outro | Update mock component imports to include new weekly digest options — Update `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` to add new mock component impo | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `39478a15e` | 2026-04-20 | Outro | Add new toast notification components to the application — Update mockup-components.ts to include SonnerToasts and TemplateSuggestionToastMockup components. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `e3148e156` | 2026-04-20 | Outro | Add new components for the weekly digest feature — Update mockup-components.ts to include new components for the weekly digest feature. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `c4240f79f` | 2026-04-20 | Outro | Update component imports to include new weekly digest features — Reorganize module map to correctly include 'FunilElevenLabs.tsx' and add imports for new weekly dige | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `498022c78` | 2026-04-20 | Outro | Add new UI components for displaying notifications and suggestions — Update mockup-components.ts to include new Sonner toast components. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `454ffd9e3` | 2026-04-20 | Outro | Add a new component for ElevenLabs funnel functionality — Update mockup-components.ts to include the FunilElevenLabs component import. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `609745151` | 2026-04-20 | Outro | Update component mapping for mockups to include new items — Update the generated component mapping file to reflect the addition of new mockups for 'FunilElevenL | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `c232fd6bb` | 2026-04-20 | Outro | Add new components to the mockups sandbox for testing — Add new component imports to the mockups sandbox for FunilElevenLabs and weekly digest components. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `3a20076cd` | 2026-04-20 | Outro | Add a new component to the sandbox for ElevenLabs funnel mockups — Add a mapping for the FunilElevenLabs component in mockup-components.ts. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `09f34a144` | 2026-04-20 | Outro | Update component mapping to include new decision bar mockups — Modify `mockup-components.ts` to register new mockups for decision bar components including Entrevis | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `ac9069ab3` | 2026-04-20 | Outro | Update mockups to include new decision bar components — Reorganize mockup component imports, adding `Entrevista`, `Passive`, `Proposta`, and `Triagem` to th | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `6c7fa4b19` | 2026-04-20 | Outro | Update mockups to include new toast notifications and adjust component imports — Refactor mockup component imports in `mockup-components.ts` to correctly map `FunilElevenLabs` and a | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `0496cf198` | 2026-04-20 | Outro | Add ElevenLabs funnel component to the mockup sandbox — Add a new component import for the FunilElevenLabs component to the mockup sandbox in `artifacts/moc | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `71bb979a3` | 2026-04-20 | Outro | Update mockups for toast notifications and ElevenLabs funnel — Update mockup component imports, replacing FunilElevenLabs with SonnerToasts and TemplateSuggestionT | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `5b3a85cad` | 2026-04-20 | Outro | Organize toast mockup component imports for better structure — Update mockup component import order in `mockup-components.ts` to group toast-related components. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `efe036a83` | 2026-04-20 | Outro | Add new components for a triagem flow to the application — Update mockup-components.ts to include new screen components for the triagem flow. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `086641ef8` | 2026-04-20 | Outro | Update mockups for triagem flow components — Re-add triagem flow components to mockup-components.ts after removal. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `4207bf817` | 2026-04-20 | Outro | Update mockups to include a new funnel component — Update `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` to add a new module import for | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `e5299e769` | 2026-04-20 | Outro | Update weekly digest components for mockups — Update artifacts/mockup-sandbox/src/.generated/mockup-components.ts to reflect changes in weekly dig | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `09a29366d` | 2026-04-20 | Outro | Add weekly digest components to the mockups — Update mockup-components.ts to include new components for the weekly digest feature. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `709659f8a` | 2026-04-20 | Outro | Add new components for chat welcome polish — Update mockup-components.ts to include new chat welcome polish components for ElevatedCards and Tigh | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `9aa587053` | 2026-04-20 | Outro | Add new components for toasts and welcome polish mockups — Update mockup-components.ts to include new SonnerToasts and TemplateSuggestionToastMockup, and re-ad | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `bc41ff494` | 2026-04-20 | Outro | Update mock components to include new triagem flow screens — Replaces toasts-sonner mockups with triagem-flow mockups in `mockup-components.ts`. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `8fee1b64a` | 2026-04-20 | Outro | Add new UI components for chat and triage screens — Update artifacts/mockup-sandbox/src/.generated/mockup-components.ts to include new module imports fo | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `8062dff21` | 2026-04-20 | Outro | Update component mapping to include a new funnel feature — Update mockup-components.ts to include the FunilElevenLabs component. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `8c0e472d0` | 2026-04-20 | Outro | Add new chat components to the mockups — Update mockup-components.ts to include new entries for ElevatedCards, TighterRhythm, and FunilEleven | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `152625d10` | 2026-04-20 | Outro | Update mockups to improve card and badge styling for better visual consistency — Add two new mockups, `ElevatedCards.tsx` and `TighterRhythm.tsx`, to the `chat-welcome-polish` modul | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `32f36cf9c` | 2026-04-20 | Outro | Update mock components to include new toast notifications — Replaces weekly digest mock components with new sonner toast mock components in mockup-components.ts | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `b0209e7c8` | 2026-04-20 | Outro | Update mock component imports for toasts and weekly digest features — Replace toast component imports with weekly digest component imports in mockup-components.ts. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `69825249d` | 2026-04-20 | Outro | Update mock component definitions for weekly digest — Update mock component definitions by adding weekly digest components. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `8a2f575ef` | 2026-04-20 | Outro | Add new UI components for various platform features — Add mock component definitions for Sonner Toasts, ElevenLabs Funnel, and Weekly Digest features. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `075ac39ba` | 2026-04-20 | Outro | Add new UI components for testing different chat and toast functionalities — Update mockup components to include new Sonner toasts and ElevenLabs chat mockups. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `ebe6d4b72` | 2026-04-20 | Outro | Update mock components to include toast notifications — Update artifacts/mockup-sandbox/src/.generated/mockup-components.ts to include SonnerToasts and Temp | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `c11e4a096` | 2026-04-20 | Outro | Add a button to easily return to the chat interface — Add new mock components for chat and workflow screens. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `845891d49` | 2026-04-20 | Outro | Add a button to return to the chat from other sections — Adds a "back to chat" button to the workflow rail, visible when not on the chat page, to prevent use | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| | _… +238 commits adicionais (ver Apêndice C nos anexos)_ | | | | |

### (Auto-commit Replit)

- **Commits:** 270  |  **Período:** 2026-03-15 → 2026-04-29  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×263 🟢×6 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `745ce9d31` | 2026-04-29 | Auto-commit Replit | Saved your changes before starting work | `lia-agent-system/eval/eval_results_20260429_122312.json` |
| 🟡 | `ac70f93a4` | 2026-04-29 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/libs/models/lia_models/company.py` |
| 🟡 | `d20336c2e` | 2026-04-28 | Auto-commit Replit | Transitioned from Plan to Build mode | — |
| 🟡 | `70db3cd06` | 2026-04-28 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260428_162619.json` |
| 🟡 | `6aeaa57a6` | 2026-04-28 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260428_122113.json` |
| 🟡 | `b209a12fa` | 2026-04-28 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/app/api/v1/settings_progress.py`<br>`lia-agent-system/app/domains/company/repositories/settings_progress_repository.py`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| 🟡 | `ddeb1eb92` | 2026-04-28 | Auto-commit Replit | Git commit prior to merge | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `43f62d263` | 2026-04-28 | Auto-commit Replit | Git commit prior to merge | `plataforma-lia/src/components/settings/AlertsSection.tsx`<br>`plataforma-lia/src/components/settings/ApproverSection.tsx`<br>`plataforma-lia/src/components/settings/CompanyDataSection.tsx` |
| 🟡 | `45a6c89c9` | 2026-04-28 | Auto-commit Replit | Git commit prior to merge | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `2abf85f6f` | 2026-04-28 | Auto-commit Replit | Git commit prior to merge | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `73a232a56` | 2026-04-28 | Auto-commit Replit | Transitioned from Plan to Build mode | `lia-agent-system/eval/eval_results_20260428_020821.json`<br>`lia-agent-system/eval/eval_results_20260428_085525.json` |
| 🟡 | `e5438af42` | 2026-04-27 | Auto-commit Replit | Git commit prior to merge | `plataforma-lia/src/components/triagem/ConfirmationCard.tsx`<br>`plataforma-lia/src/components/triagem/LikertScaleCard.tsx`<br>`plataforma-lia/src/components/triagem/MultipleChoiceCard.tsx` |
| 🟡 | `a11a9cfc5` | 2026-04-27 | Auto-commit Replit | Git commit prior to merge | — |
| 🟡 | `4d19cf41c` | 2026-04-27 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260427_130354.json` |
| 🟡 | `a318bb180` | 2026-04-27 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260427_120620.json` |
| 🟡 | `fd8bd9ad8` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/CLAUDE.md` |
| 🟡 | `2adac0f2c` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/repositories/teams_repository.py`<br>`lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py` |
| 🟡 | `f5cf05330` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `158ea11be` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `plataforma-lia/package-lock.json` |
| 🟡 | `2f677eae0` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `590c55130` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `1960f4b62` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `a7fcf5a5d` | 2026-04-26 | Auto-commit Replit | Transitioned from Plan to Build mode | — |
| 🟡 | `48944aaac` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260426_113110.json` |
| 🟡 | `eba25ca5a` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260426_112602.json` |
| 🟡 | `52e7da6f8` | 2026-04-26 | Auto-commit Replit | Git commit prior to merge | `.agents/skills/design-patterns/SKILL.md`<br>`.agents/skills/design-patterns/checklists/pattern-evaluation.md`<br>`.agents/skills/design-patterns/reference/behavioral.md` |
| 🟡 | `1452d9473` | 2026-04-25 | Auto-commit Replit | Transitioned from Plan to Build mode | — |
| 🟡 | `698afe531` | 2026-04-25 | Auto-commit Replit | Transitioned from Plan to Build mode | `lia-agent-system/eval/eval_results_20260425_202329.json` |
| 🟡 | `d6644982b` | 2026-04-23 | Auto-commit Replit | Saved progress at the end of the loop | `plataforma-lia/package-lock.json` |
| 🟡 | `6f57b3d65` | 2026-04-23 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/app/prompts/domains/autonomous.yaml`<br>`lia-agent-system/app/prompts/domains/culture_analysis.yaml`<br>`lia-agent-system/app/prompts/domains/orchestrator.yaml` |
| 🟡 | `f7627f1bf` | 2026-04-23 | Auto-commit Replit | Saved progress at the end of the loop | `ats_api/app/controllers/v1/users/jobs/wsi_jd_enrich_controller.rb`<br>`ats_api/app/services/evaluations/wsi_dimension_scores.rb`<br>`ats_api/app/services/evaluations/wsi_layer_three_scorer.rb` |
| 🟡 | `8237e5cb6` | 2026-04-23 | Auto-commit Replit | Transitioned from Plan to Build mode | `lia-agent-system/eval/eval_results_20260422_231322.json` |
| 🟡 | `fc5ba84eb` | 2026-04-22 | Auto-commit Replit | Transitioned from Plan to Build mode | `lia-agent-system/eval/eval_results_20260422_165027.json` |
| 🟡 | `906749f22` | 2026-04-22 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260422_124919.json` |
| 🟡 | `4af7cf447` | 2026-04-22 | Auto-commit Replit | Transitioned from Plan to Build mode | — |
| 🔴 | `c698d5eef` | 2026-04-22 | Cross IA↔Front | Restored to 'c3d45b3d8ddb560ce2ee3a23c6062d8ae325a6f4' — Replit-Restored-To: c3d45b3d8ddb560ce2ee3a23c6062d8ae325a6f4 | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/job_readiness.py` |
| 🟡 | `b89052761` | 2026-04-22 | Auto-commit Replit | Transitioned from Plan to Build mode | `plataforma-lia/src/components/unified-chat/._OutreachCard.tsx`<br>`plataforma-lia/src/components/unified-chat/._ThinkingStepsCard.tsx`<br>`plataforma-lia/src/components/unified-chat/._UnifiedChat.tsx` |
| 🟡 | `1caeee4bc` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `plataforma-lia/src/app/api/backend-proxy/fairness/audit/logs/route.ts` |
| 🟡 | `27ea118b4` | 2026-04-21 | Auto-commit Replit | Transitioned from Plan to Build mode | — |
| 🟡 | `7a5142db5` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts`<br>`lia-agent-system/docs/PHASE0_AUDIT.md` |
| 🟡 | `311e74269` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts` |
| 🟡 | `68bef95bf` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/docs/LIA_MATURITY_ROADMAP.md` |
| 🟡 | `66343bef5` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260421_152907.json` |
| 🟡 | `6fdc3e93c` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `plataforma-lia/src/components/pages/ats-integrations-page.tsx`<br>`plataforma-lia/src/components/pages/pipeline-overview/pipeline-rail.tsx`<br>`plataforma-lia/src/components/sidebar.tsx` |
| 🟡 | `ae56c0d2d` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx` |
| 🟡 | `023148bc3` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/app/orchestrator/correction_detector.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `1725eb5ad` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/app/orchestrator/memory_resolver.py` |
| 🟡 | `6ca89c4b3` | 2026-04-21 | Auto-commit Replit | Git commit prior to merge | `.gitignore` |
| 🟡 | `604438485` | 2026-04-21 | Auto-commit Replit | Saved your changes before starting work | `lia-agent-system/app/domains/ai/services/candidate_search_service.py`<br>`lia-agent-system/app/domains/ai/services/search_service.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟡 | `1a5f22d5c` | 2026-04-21 | Auto-commit Replit | Transitioned from Plan to Build mode | — |
| 🟡 | `fe94359d1` | 2026-04-20 | Auto-commit Replit | Transitioned from Plan to Build mode | — |
| 🟡 | `cbd2fc899` | 2026-04-20 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260420_165410.json` |
| 🟡 | `8212c96e5` | 2026-04-20 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/eval_results_20260420_143816.json` |
| 🟡 | `d2772e782` | 2026-04-20 | Auto-commit Replit | Git commit prior to merge | `.gitignore` |
| 🟡 | `62c5689c4` | 2026-04-20 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/agentic/run_agentic_api.py`<br>`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T13-52-07.json`<br>`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T13-52-07_judged.json` |
| 🟡 | `3897bc42a` | 2026-04-20 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/agentic/run_agentic_api.py` |
| 🟡 | `0b3caa28c` | 2026-04-20 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/agentic/run_agentic_api.py`<br>`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T11-08-58.json`<br>`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T11-26-22.json` |
| 🟡 | `be607d82a` | 2026-04-20 | Auto-commit Replit | Git commit prior to merge | `lia-agent-system/eval/agentic/runs/agentic-2026-04-20T11-04-15.json` |
| 🟡 | `591441554` | 2026-04-20 | Auto-commit Replit | Git commit prior to merge | `plataforma-lia/e2e/tests/agentic-eval/agentic-eval.spec.ts`<br>`plataforma-lia/e2e/tests/agentic-eval/agentic-helpers.ts` |
| 🟡 | `e5a0787aa` | 2026-04-20 | Auto-commit Replit | Transitioned from Plan to Build mode | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py`<br>`lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| | _… +210 commits adicionais (ver Apêndice C nos anexos)_ | | | | |

### §15 WSI

**Descrição:** WSI (Worker Skill Index) — métrica + compliance EU AI Act + transparência. Phase 1 ADR-017. Phase 2 G1+G2. Skill canonical-fix. Extract transcript_extractor. Flip atômico escala 0-5 → 0-10 (PR1/PR2/PR3). Split tech/behav 100% determinístico via category. Correções metodológicas (Bloom + Dreyfus + Gates). Audit trail + response_hash + endpoint EU AI Act. Frontend escala 0-10. Refactor 23 consumidores /5 → /10. Transparência granular G23-02/G23-03. UI Modal Triagem + banner degraded + breakdown granular. Kanban: indicador modo degradado. Backfill transparency_extras. Tests UI LGPD/EU AI Act. Toggle 'Apenas modo degradado'.

**⚠️ Dependências para cherry-pick:** Escala 0-10 atômica (não convive com 0-5) | response_hash em audit | Tier 1 obrigatório (Quality Tier Guard) | UI mostra banner degraded | transparency_extras backfilled

**Arquivos canônicos:** lia-agent-system/app/domains/cv_screening/services/wsi_*, app/api/v1/wsi/*, plataforma-lia/src/components/wsi-modal/*

**Docs de referência:** ADR-017 (WSI), Task #497/#511/#523

- **Commits:** 160  |  **Período:** 2026-03-15 → 2026-04-21  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×93 🔴×35 🟢×32
- **Tags/Milestones:** `milestone/wsi-eu-ai-act-compliance`, `milestone/wsi-phase2-remediation`, `milestone/wsi-scale-0-10-atomic-flip`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `017013cf8` | 2026-04-21 | Frontend (UI) | Highlight WSI/Bloom terms in chat replies with hover tooltips (Task #759) — What changed | `plataforma-lia/src/components/chat/glossary-highlighted-text.tsx`<br>`plataforma-lia/src/components/chat/message-bubble.tsx` |
| 🔴 | `69b7fd1d8` | 2026-04-21 | Cross Back↔Front | Task #745: Show recruiters the official WSI/Bloom term definitions in chat — What changed | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/glossary.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟡 | `2dec6d172` | 2026-04-20 | Frontend (UI) | fix(wsi): Corrigir painel Descrição do Cargo (task #664) — ## Problemas corrigidos | `plataforma-lia/src/app/api/backend-proxy/wsi/jd-evaluate/route.ts`<br>`plataforma-lia/src/components/wsi/JDEvaluationPanel.tsx`<br>`plataforma-lia/src/components/wsi/jd-evaluation/JDEvalCriteriaList.tsx` |
| 🟡 | `9c7e65855` | 2026-04-20 | IA | Task #334 — Forward recruiter tenant id through WSI on-the-fly question pipeline — Original task: When the WSI interview graph hits the on-the-fly fallback that | `lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py` |
| 🟡 | `8bb172145` | 2026-04-19 | Backend | fix(byok): BUG-07 WSI analyze-response BYOK + Quality Tier Guard — _shared.py get_anthropic_client(): | `lia-agent-system/app/api/v1/wsi/_shared.py`<br>`lia-agent-system/app/api/v1/wsi/evaluation.py` |
| 🟡 | `0ebda12cc` | 2026-04-19 | IA | Backfill transparency_extras for legacy WSI response analyses (task #534) — Original task: rows in `wsi_response_analyses` written before task #528 | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py`<br>`lia-agent-system/scripts/backfill_wsi_transparency_extras.py` |
| 🟡 | `69b21b939` | 2026-04-19 | IA | Fix WSICompactPipeline LLM call and add regression tests (Task #541) — Original task: Compact Mode question generation for talent pools was | `lia-agent-system/app/services/wsi_compact_pipeline.py` |
| 🟡 | `506cd0549` | 2026-04-19 | Cross IA↔Back | test(wsi-modal): testes de UI para transparência LGPD/EU AI Act (task #535) + fix(query_tools): corrige runtime defect no fallback de shortcode — ## Frontend (escopo principal — task #535) | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🔴 | `48c9bf2c8` | 2026-04-19 | Cross IA↔Front | test(wsi-modal): testes de UI para transparência LGPD/EU AI Act (task #535) — Adiciona testes de componente Vitest cobrindo o modal de Triagem (#529) | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/components/triagem-details/triagem-responses-section.tsx` |
| 🟢 | `ece880097` | 2026-04-19 | Testes | test(wsi-modal): testes de UI para transparência LGPD/EU AI Act (task #535) — Adiciona testes de componente Vitest cobrindo o modal de Triagem (#529) | `plataforma-lia/src/components/__tests__/triagem-details-modal.transparency.test.tsx` |
| 🟡 | `6747cf86d` | 2026-04-19 | IA | Add session ID to tracking for improved auditing and reconciliation — Update lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py and lia-ag | `lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🟡 | `a805f1096` | 2026-04-19 | Cross IA↔Back | task #532 (G23-04): tracking opcional de tokens da Camada 2 WSI — - safe_invoke (app/domains/ai/services/llm.py) ganha kwarg opcional | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py` |
| 🔴 | `ad92fde29` | 2026-04-19 | Cross IA↔Front | Task #530 — Kanban: indicador visual de modo degradado no score WSI — ## What | `lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/voice/repositories/wsi_repository.py`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCardScores.tsx` |
| 🟡 | `869e8feab` | 2026-04-19 | Backend | Remove redundant database schema modification from application code — Remove the `ALTER TABLE` statement for `transparency_extras` from `reports.py` as it is now managed  | `lia-agent-system/app/api/v1/wsi/reports.py` |
| 🟡 | `7b57d9156` | 2026-04-19 | Cross IA↔Back | Add transparency data to response analyses and update evaluation results — Adds a new SQL migration to include `transparency_extras` in `wsi_response_analyses` and updates eva | `lia-agent-system/database/migrations/016_add_transparency_extras_to_wsi_response_analyses.sql` |
| 🟡 | `eb04ba77d` | 2026-04-19 | Cross IA↔Back | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev. 23: scorer determinístico não expunha | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py`<br>`lia-agent-system/app/orchestrator/action_executor/executor.py` |
| 🟡 | `c69023c9f` | 2026-04-19 | IA | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev. 23: scorer determinístico não expunha | `lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/voice/repositories/wsi_repository.py` |
| 🟡 | `6dd966b07` | 2026-04-19 | IA | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev. 23: scorer determinístico não expunha | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| 🟡 | `621a500e5` | 2026-04-19 | Backend | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev. 23: scorer determinístico não expunha | `lia-agent-system/app/api/v1/wsi/reports.py` |
| 🟡 | `5b264bcfe` | 2026-04-19 | Backend | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev. 23: scorer determinístico não expunha | `lia-agent-system/app/api/v1/wsi/reports.py` |
| 🟡 | `33832831b` | 2026-04-19 | Backend | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev. 23: scorer determinístico não expunha | `lia-agent-system/app/main.py` |
| 🔴 | `2e4b903c4` | 2026-04-19 | Cross IA↔Front | Task #528 — Backend WSI: expor transparência granular (G23-02/G23-03) — Auditoria pré-produção rev. 23: scorer determinístico não expunha | `lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/models.py` |
| 🟡 | `0f00240b5` | 2026-04-19 | IA | Update system instructions for evaluating candidate responses — Adjust prompt configurations in `intents_config.py` and `wsi_layer2_extraction.yaml` to refine the A | `lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/prompts/domains/wsi_layer2_extraction.yaml` |
| 🟡 | `4af2b303d` | 2026-04-18 | Cross IA↔Back | Add advanced semantic analysis and scoring for candidate responses — This commit introduces the Layer 2 LLM Extractor, enhancing the WSI scoring system by adding semanti | `lia-agent-system/app/domains/cv_screening/constants/wsi_scale.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py` |
| 🟡 | `e762705ef` | 2026-04-18 | IA | Add layer to extract semantic signals from candidate responses — Implement a new LLM-based layer for extracting semantic signals from candidate responses. This layer | `lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/models.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py` |
| 🔴 | `92bb7013f` | 2026-04-18 | Cross IA↔Front | Update scoring logic and improve user interface for assessments — Refactor WSI scoring calculations, update Big Five trait representation, adjust API routes, and enha | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/digital_twins.py`<br>`lia-agent-system/app/api/v1/multi_strategy_search.py` |
| 🟡 | `e42d74dec` | 2026-04-18 | IA | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 do audit: 9 bugs P0 ativos por | `lia-agent-system/app/api/wsi_endpoints.py` |
| 🟡 | `f58b65f80` | 2026-04-18 | Cross IA↔Back | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 do audit: 9 bugs P0 ativos por | `lia-agent-system/app/domains/interview_intelligence/services/comparative_analysis_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/interview_wsi_service.py` |
| 🟡 | `24ada0f6b` | 2026-04-18 | Cross IA↔Back | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 do audit: 9 bugs P0 ativos por | `lia-agent-system/app/api/v1/interview_analysis.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/interview_wsi_service.py` |
| 🟡 | `f328031da` | 2026-04-18 | Cross IA↔Back | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 do audit: 9 bugs P0 ativos por | `lia-agent-system/app/domains/interview_intelligence/services/interview_wsi_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/strategic_opinion_service.py`<br>`lia-agent-system/app/domains/recruitment/services/triagem_session_service/scoring.py` |
| 🟡 | `63b132301` | 2026-04-18 | Cross IA↔Back | B0 #523 — Refactor consumidores WSI /5 → /10 + audit rev. 14 — Fecha a descoberta crítica da rev. 13 do audit: 9 bugs P0 ativos por | `lia-agent-system/app/api/v1/wsi/evaluation.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/api/wsi_endpoints.py` |
| 🔴 | `273e01d54` | 2026-04-18 | Cross IA↔Front | Improve candidate screening by refining scoring and default handling — Update SQL schema scores to a 0-10 range and adjust the seniority fallback mechanism. | `lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py`<br>`lia-agent-system/database/wsi_schema.sql`<br>`lia-agent-system/database/wsi_schema_corrected.sql` |
| 🟢 | `d772302d5` | 2026-04-18 | Frontend (UI) | Update scoring color logic to use canonical WSI visual scale — Refactors `CandidateScoreBadge.tsx` and `useTriagemDetailsState.ts` to utilize the `getWsiScoreColor | `plataforma-lia/src/components/candidate-profile/CandidateScoreBadge.tsx`<br>`plataforma-lia/src/components/triagem-details/useTriagemDetailsState.ts` |
| 🟡 | `5f6556aae` | 2026-04-18 | Frontend (UI) | feat(wsi): PR3 frontend escala 0-10 (Task #512, issue #497) — Migra todo o frontend WSI da escala legada 1-5 para 0-10 alinhado ao | `plataforma-lia/src/app/[locale]/funil-de-talentos/candidato/[id]/components/CandidatoOpinionsTab.tsx`<br>`plataforma-lia/src/components/candidate-page/CandidatePageOpinionsTab.tsx`<br>`plataforma-lia/src/components/candidate-preview/OpinionCard.tsx` |
| 🔴 | `d881a64fe` | 2026-04-18 | Cross IA↔Front | feat(wsi): PR3 frontend escala 0-10 (Task #512, issue #497) — Migra todo o frontend WSI da escala legada 1-5 para 0-10 ponta-a-ponta, | `lia-agent-system/app/orchestrator/chat_adapter.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/memory_resolver.py` |
| 🟡 | `6ac807839` | 2026-04-18 | IA | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/alembic/versions/091_add_wsi_responses_audit_trail.py`<br>`lia-agent-system/app/domains/voice/repositories/wsi_repository.py` |
| 🟡 | `6b5fdd0c6` | 2026-04-18 | Cross IA↔Back | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/alembic/versions/092_wsi_responses_session_fk.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🟡 | `3543b9212` | 2026-04-18 | Cross IA↔Back | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/app/api/v1/wsi/evaluation.py`<br>`lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/voice/repositories/wsi_repository.py` |
| 🟡 | `d8db05a12` | 2026-04-18 | Cross IA↔Back | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/alembic/versions/094_wsi_responses_fk_restrict.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🟡 | `90c05cfea` | 2026-04-18 | Cross IA↔Back | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/app/domains/voice/repositories/wsi_repository.py` |
| 🟡 | `3144cdf8b` | 2026-04-18 | Backend | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/app/domains/recruitment/services/triagem_session_service/completion.py` |
| 🟡 | `2f38efa38` | 2026-04-18 | Backend | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/app/api/v1/wsi/reports.py` |
| 🟡 | `a9b7681f6` | 2026-04-18 | Cross IA↔Back | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py`<br>`lia-agent-system/app/domains/recruitment/services/triagem_session_service/completion.py` |
| 🟡 | `a969aab40` | 2026-04-18 | Backend | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/alembic/versions/093_add_dpo_to_userrole_enum.py`<br>`lia-agent-system/app/domains/recruitment/services/triagem_session_service/completion.py` |
| 🟡 | `bdb8543f8` | 2026-04-18 | Backend | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui rounds | `lia-agent-system/app/api/v1/wsi/reports.py` |
| 🟡 | `a26e3c167` | 2026-04-18 | Cross IA↔Back | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI). Inclui round 2 | `lia-agent-system/alembic/versions/092_wsi_responses_session_fk.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/auth/models.py` |
| 🟡 | `afe62dd3c` | 2026-04-18 | Cross IA↔Back | task #511: Compliance EU AI Act WSI — audit trail + response_hash + endpoint — Fecha M09 (ausência de trilha de auditoria/response hash WSI) com 5 entregas: | `lia-agent-system/alembic/versions/091_add_wsi_responses_audit_trail.py`<br>`lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/report_generator.py` |
| 🟡 | `1e0482dd1` | 2026-04-18 | IA | Task #510: Correções metodológicas WSI scorer (M02 Bloom + M07 Dreyfus + M08 Gates) — Três fixes críticos no scorer determinístico WSI conforme spec WeDOTalent v3.3: | `lia-agent-system/app/orchestrator/action_executor/utils.py` |
| 🟡 | `9851a5eab` | 2026-04-18 | Cross IA↔Back | Task #510: Correções metodológicas WSI scorer (M02 Bloom + M07 Dreyfus + M08 Gates) — Três fixes críticos no scorer determinístico WSI conforme spec WeDOTalent v3.3: | `lia-agent-system/app/api/v1/wsi/reports.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/report_generator.py` |
| 🟡 | `689b90885` | 2026-04-18 | Cross IA↔Back | Task #497 PR2 — Flip atômico escala WSI 0-5 → 0-10 (engine + DB + Pydantic) — T1 wsi_scale.py flipado: SCALE_MAX 5→10, WSI_CUTOFFS 7.5/6.0, | `lia-agent-system/alembic/versions/090_widen_wsi_score_scale_to_10.py`<br>`lia-agent-system/app/api/v1/wsi/_shared.py`<br>`lia-agent-system/app/api/v1/wsi/evaluation.py` |
| 🟡 | `9b78e02ae` | 2026-04-18 | Cross IA↔Back | Task #497 PR1: extrair constantes do engine WSI determinístico (zero behavior change) — CONTEXTO | `lia-agent-system/app/domains/cv_screening/constants/wsi_scale.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py` |
| 🟡 | `1d996df89` | 2026-04-18 | Cross IA↔Back | refactor(wsi): extrair transcript_extractor do orchestrator (#496 PR1) — Inicia o split do voice_screening_orchestrator.py (P0-5 do audit WSI). | `lia-agent-system/app/domains/cv_screening/services/wsi_service/transcript_extractor.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` |
| 🔴 | `e867c1d24` | 2026-04-18 | Cross IA↔Front | feat(wsi): split tech/behav 100% determinístico via category explícita (#498) — Substitui o heurístico por peso (não-determinístico quando pesos são iguais) | `lia-agent-system/app/api/v1/automation/event_handlers/handlers_screening.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/models.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/response_analyzer.py` |
| 🟢 | `1513a89ef` | 2026-04-18 | Empty/merge | Phase 2 WSI/Screening remediation — G1 + G2 entregues; G3 promovido a tasks — Trabalho concluído (8 itens da Fase 2): | — |
| 🔴 | `317680eef` | 2026-04-18 | Cross IA↔Front | Phase 2 WSI/Screening remediation — G1 + G2 entregues; G3 promovido a tasks — Trabalho concluído (8 itens da Fase 2): | `lia-agent-system/alembic/versions/089_widen_wsi_check_constraints.py`<br>`lia-agent-system/app/api/v1/voice_screening.py`<br>`lia-agent-system/app/api/v1/wsi_async.py` |
| 🔴 | `51a09caec` | 2026-04-18 | Cross IA↔Back | audit(wsi): Phase 1 remediação — selos rev. 5 + ADR-017 — Phase 1 do plano de remediação WSI aprovado pelo usuário, | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/candidates/_shared.py`<br>`lia-agent-system/app/api/v1/gemini_voice.py` |
| 🟢 | `605c0cbbf` | 2026-04-18 | Testes | Task #412: regression test for FairnessGuard on WSI generate-questions — Added `lia-agent-system/tests/api/test_wsi_generate_questions_fairness.py` | `lia-agent-system/tests/api/__init__.py`<br>`lia-agent-system/tests/api/test_wsi_generate_questions_fairness.py` |
| 🟡 | `399cdd9d8` | 2026-04-18 | Backend | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): | `lia-agent-system/app/api/v1/triagem.py` |
| 🟡 | `becc1efac` | 2026-04-18 | Backend | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): | `lia-agent-system/app/domains/recruitment/services/triagem_session_service/lifecycle.py` |
| 🔴 | `e5b77b78b` | 2026-04-18 | Cross Back↔Front | Task #425 — close all 5 validator blockers (WSI 4 Canais MVP) — Backend (lia-agent-system): | `lia-agent-system/app/domains/recruitment/services/triagem_session_service/lifecycle.py`<br>`plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx`<br>`plataforma-lia/src/components/wsi/wsi-triagem-invite-modal.tsx` |
| | _… +100 commits adicionais (ver Apêndice C nos anexos)_ | | | | |

### Compliance / LGPD / EU AI Act

**Descrição:** Compliance LGPD (PII strip, consent gates) + EU AI Act WSI (audit_trail + response_hash + endpoint). FairnessGuard v8 com hard blocks discriminatórios. PII Masking não destrói IDs (lookbehind/lookahead). Bypass de mensagens copy/thumbs.

**⚠️ Dependências para cherry-pick:** FairnessGuard v8 ativo | PII Masking com regex correta (não destrói job_id) | response_hash em todo audit

**Arquivos canônicos:** lia-agent-system/app/shared/compliance/fairness_guard.py, app/shared/pii_masking.py, app/services/audit_service.py

**Docs de referência:** FRIA_EU_AI_ACT.md, FAIRNESS_GUARD_COVERAGE.md

- **Commits:** 149  |  **Período:** 2026-03-15 → 2026-04-26  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×68 🟢×64 🔴×17

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `5d5635007` | 2026-04-26 | Cross Back↔Front | fix(unified-chat): remove dead LgpdConsentDialog to unblock build — Bug: dev-server (Next.js 16 + Turbopack) quebrava com `ENOENT: no such | `plataforma-lia/src/components/unified-chat/LgpdConsentDialog.tsx` |
| 🟢 | `e10758adc` | 2026-04-25 | Docs | Update tenant configuration documentation and clarify initial compliance status — Update tenant minimum configuration documentation to clarify the number of seed tables and initial c | `docs/governance/tenant-minimum-config.md` |
| 🟢 | `8f5989bd4` | 2026-04-24 | Docs | Add canonical YAML bundles to documentation for AI assistants — Create new markdown files containing verbatim YAML content for LIA persona, compliance, and infrastr | `docs/reconstruction-guides/CANONICAL_FILES_BY_THEME.md`<br>`docs/reconstruction-guides/COMPLIANCE_DEV_HANDOFF_2026-04-23.md`<br>`docs/reconstruction-guides/COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md` |
| 🔴 | `aa664e84b` | 2026-04-24 | Cross Back↔Front | Add ability to explain automated decisions to candidates — Adds a new API endpoint and tool for explaining automated decisions to candidates, and updates docum | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/candidate_portal_explanation.py` |
| 🟡 | `a45875997` | 2026-04-21 | Cross IA↔Back | feat(lgpd): G5 light — PII redaction at response boundary — Onda 2.1. Closes LGPD blocker for Init IV (briefing) + Init V (citations). | `lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🟢 | `d0b2190e1` | 2026-04-21 | Frontend (UI) | fix: corrige crash FairnessComplianceHub e cria proxy audit logs — - by_category?.map corrige TypeError Cannot read properties of undefined | `plataforma-lia/src/app/api/backend-proxy/fairness/audit/logs/route.ts`<br>`plataforma-lia/src/components/settings/FairnessComplianceHub.tsx` |
| 🟡 | `aae815734` | 2026-04-21 | Cross IA↔Back | feat(task-712): close 3 final compliance/registry findings — 1) FairnessGuard recursivo em writes de settings. | `lia-agent-system/app/domains/company_settings/domain.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml` |
| 🟡 | `bb48ae14c` | 2026-04-19 | Backend | feat: rails_client wrapper + patch method for rh_dashboard LGPD | `lia-agent-system/app/domains/ats_integration/services/ats_clients/wedotalent_rails.py` |
| 🟡 | `260a8bf22` | 2026-04-19 | Backend | fix(rh-dashboard): correct APIResponse import + Next.js LGPD proxy routes — - rh_dashboard.py: wrong import app.shared.response fixed to app.schemas.api_envelope | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/rh_dashboard.py` |
| 🟡 | `104bc6356` | 2026-04-19 | Backend | fix(compliance): P3#11 + P2#8 — FairnessGuard API + LGPD consent cache — P3#11 — fix FairnessGuard API in suggest_recruiting_policy: | `lia-agent-system/app/domains/sourcing/services/consent_cache.py` |
| 🟡 | `b90eb3cfe` | 2026-04-19 | Cross IA↔Back | Enhance AI tracking durability and fairness checks — Implement an outbox pattern for AI usage tracking to ensure durability and persistence of data, alon | `lia-agent-system/alembic/versions/095_create_ai_consumption_outbox.py`<br>`lia-agent-system/app/domains/cv_screening/services/culture_analyzer_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/cv_parser.py` |
| 🟡 | `82024c586` | 2026-04-19 | Cross IA↔Back | Add functionality to extract candidate names and reasons for rejection — Enhance the `reject_candidate` intent handler in `utils.py` to extract `candidate_name` and `reason` | `lia-agent-system/app/orchestrator/action_executor/utils.py` |
| 🔴 | `f947f9a21` | 2026-04-18 | Cross Back↔Front | Update fairness scoring and remove legacy code — Adjusts the fairness score range from 1-5 to 1-10 in the bias detection service, updates related ser | `lia-agent-system/app/domains/interview_intelligence/services/bias_detector_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/strategic_opinion_service.py`<br>`lia-agent-system/app/shared/services/silver_medalist_service.py` |
| 🟡 | `003bcec6d` | 2026-04-17 | Backend | Notify recruiter in real time when sourcing is fairness-blocked — Task #360: recruiters previously only saw the FairnessGuard block banner | `lia-agent-system/app/domains/sourcing/services/sourcing_pipeline_service.py` |
| 🟡 | `9265d0680` | 2026-04-17 | IA | Add end-to-end integration test for the fairness-block audit trail — Task #365: Cover the regulator-facing audit trail emitted by all five | `lia-agent-system/app/shared/compliance/scoring_safeguards.py` |
| 🟡 | `7b61471cd` | 2026-04-17 | IA | Promote canonical biased phrases to hard-block in FairnessGuard (Task #364) — What changed | `lia-agent-system/app/shared/compliance/fairness_guard.py` |
| 🟢 | `327102c3f` | 2026-04-17 | Docs | Recompute agent compliance scorecard with F5 sub-agent inheritance rule (task #369) — Original task: rebuild §4 of docs/audits/AUDIT_STATUS_REPORT_2026-04-FINAL.md | `docs/audits/AUDIT_STATUS_REPORT_2026-04-FINAL.md` |
| 🟢 | `4781a4ab6` | 2026-04-17 | Testes | test(cv_screening): add fairness/audit unit tests for 5 scoring services — Task #307 — EU AI Act high-risk + LGPD Art. 20 compliance tests. | `lia-agent-system/tests/unit/test_scoring_services_fairness_audit.py` |
| 🟢 | `70c1f4e48` | 2026-04-17 | Testes | Fix pre-existing fairness/bias audit test failures (task #339) — Fixed 6 failing tests that were unrelated to the FairnessGuard | `lia-agent-system/tests/test_fairness_guard.py` |
| 🔴 | `0acf9ef35` | 2026-04-17 | Cross IA↔Front | Task #341: Surface FairnessGuard sourcing blocks on the recruiter job page — Backend | `lia-agent-system/app/api/v1/fairness_reports.py`<br>`lia-agent-system/app/domains/analytics/repositories/fairness_report_repository.py`<br>`lia-agent-system/app/shared/compliance/fairness_guard.py` |
| 🟡 | `55799fe7a` | 2026-04-17 | Backend | Task #331: Aplicar auth + FairnessGuard + audit em /applications/resubmit — Original task: o endpoint POST /applications/resubmit/{vacancy_id} aceitava | `lia-agent-system/app/api/v1/applications.py` |
| 🟡 | `4d210db7b` | 2026-04-17 | Cross IA↔Back | Add fairness checks + audit trails to CV screening services (C1–C5) — Closes compliance gaps for LGPD Art. 20 / EU AI Act traceability across | `lia-agent-system/app/domains/cv_screening/services/cv_scoring_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/eligibility_verification_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/evaluation_criteria_service.py` |
| 🟡 | `e59abd0da` | 2026-04-17 | Cross IA↔Back | Task #316 — PolicySetupAgent: raise compliance from 25% → ~80% — Audit finding A2 flagged that PolicySetupAgent had all 6 compliance | `lia-agent-system/app/shared/compliance/c3b_layer.py` |
| 🟡 | `fb8f545d1` | 2026-04-17 | Backend | Task #310: Auth, FairnessGuard e audit em applications.apply — Original task: corrigir endpoint POST /applications/apply/{vacancy_id} que | `lia-agent-system/app/api/v1/applications.py` |
| 🟡 | `3bc3886bf` | 2026-04-17 | Cross IA↔Back | Task #315: Wire enterprise compliance gates into JobCreationGraph — What changed: | `lia-agent-system/app/shared/compliance/audit_service.py`<br>`lia-agent-system/libs/models/lia_models/audit_log.py` |
| 🟡 | `a621c68e1` | 2026-04-17 | Backend | task-312: add FairnessGuard + audit + PII masking to sourcing & feedback — C6 — sourcing_pipeline_service.py | `lia-agent-system/app/domains/candidates/services/candidate_feedback_service.py`<br>`lia-agent-system/app/domains/sourcing/services/sourcing_pipeline_service.py` |
| 🟡 | `1240f5859` | 2026-04-17 | Cross IA↔Back | Task #321: Consolidate bias detectors into FairnessGuard SSOT — Unified 3 divergent bias-detection implementations into the canonical | `lia-agent-system/app/domains/interview_intelligence/services/bias_detector_service.py`<br>`lia-agent-system/app/domains/job_creation/services/jd_enrichment.py`<br>`lia-agent-system/app/shared/compliance/bias_audit_service.py` |
| 🟡 | `95497fd23` | 2026-04-17 | Backend | Task #311: Add audit logging + FairnessGuard to bulk_actions and stage_transition_automation — - bulk_actions.py: instrumented all 5 bulk endpoints (update_status, assign_job, | `lia-agent-system/app/api/v1/bulk_actions.py`<br>`lia-agent-system/app/api/v1/stage_transition_automation.py` |
| 🟡 | `2d27771ec` | 2026-04-17 | Backend | Task #318 — Converge SSE chat path on shared pre/post compliance (R7) — Original task: agent_chat_sse only ran a local FairnessGuard.check, missing | `lia-agent-system/app/api/v1/agent_chat_sse.py` |
| 🟢 | `60995e512` | 2026-04-15 | Frontend (UI) | Task #209: Document Upload + FairnessGuard UI in "Minha Empresa" — - Created DocumentUploadCard with drag-and-drop zone + 4 document type | `plataforma-lia/src/components/settings/DocumentUploadCard.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaCard.tsx` |
| 🟢 | `9cfd180b9` | 2026-04-15 | Frontend (UI) | Task #209: Document Upload + FairnessGuard UI in "Minha Empresa" — - Created DocumentUploadCard with drag-and-drop zone ("Arraste um | `plataforma-lia/src/components/settings/DocumentUploadCard.tsx` |
| 🟢 | `2d4b34261` | 2026-04-15 | Frontend (UI) | Task #209: Document Upload + FairnessGuard UI in "Minha Empresa" — - Created DocumentUploadCard with drag-and-drop upload for 4 document | `plataforma-lia/src/app/api/backend-proxy/documents/upload/route.ts`<br>`plataforma-lia/src/components/settings/DocumentUploadCard.tsx` |
| 🟢 | `869324240` | 2026-04-15 | Frontend (UI) | Task #209: Document Upload + FairnessGuard UI in "Minha Empresa" — - Created DocumentUploadCard component with drag-and-drop upload zone | `plataforma-lia/src/app/api/backend-proxy/documents/upload/route.ts`<br>`plataforma-lia/src/components/settings/DocumentUploadCard.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaCard.tsx` |
| 🟢 | `a447db994` | 2026-04-14 | Testes | feat: 8 adversarial eval scenarios for attack resistance [P37-072] — Sprint 11 item 11.2 — 8 attack scenarios testing agent resilience. | `lia-agent-system/tests/eval/config.yaml`<br>`lia-agent-system/tests/eval/datasets/adversarial/attack_scenarios.yaml`<br>`lia-agent-system/tests/eval/runner.py` |
| 🟢 | `16463f952` | 2026-04-14 | Testes | feat: 8 integration eval scenarios for agent handoffs [P37-071] — Sprint 11 item 11.1 — 8 handoff scenarios testing context preservation | `lia-agent-system/tests/eval/datasets/integration/handoff_scenarios.yaml` |
| 🟢 | `9d2b7d567` | 2026-04-14 | Frontend (UI) | feat: connect Agent Control Center to quality dashboard endpoint [PX08-066] — Frontend integration for Sprint 10 item 10.1 — Agent Quality Dashboard. | `plataforma-lia/src/components/agent-control-center/index.tsx` |
| 🔴 | `dddda1a0f` | 2026-04-14 | Cross Back↔Front | feat: agent quality dashboard — aggregated metrics endpoint [PX08-066] — Sprint 10 item 10.1 — New endpoint that aggregates agent quality data | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_quality_dashboard.py`<br>`plataforma-lia/src/app/api/backend-proxy/analytics/agent-quality-dashboard/route.ts` |
| 🟡 | `8372004db` | 2026-04-14 | IA | feat: unified audit facade with trace_id + get_trail() [P35-061] — Sprint 9 item 9.3 — AuditService enriched with 4 unified facade methods: | `lia-agent-system/app/shared/compliance/audit_service.py` |
| 🟡 | `02a31522f` | 2026-04-14 | Backend | feat: LIAError hierarchy + global exception handlers [P35-060] — Sprint 9 item 9.2 — Unified error hierarchy for the platform. | `lia-agent-system/app/main.py` |
| 🟡 | `84293fcd9` | 2026-04-14 | Backend | fix: PII masking + FairnessGuard in custom StateGraph agents [P35-059] — Sprint 9 item 9.1 — 14 ReAct agents already had compliance via | `lia-agent-system/app/domains/interview_scheduling/agents/interview_graph.py`<br>`lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py` |
| 🟢 | `d2e9d39d2` | 2026-04-14 | Testes | feat: rubrics YAML for 5 critical agents [P37-048] — Sprint 6 item 6.3 — Structured scoring rubrics for LLM-as-judge | `lia-agent-system/tests/eval/rubrics/chat.yaml`<br>`lia-agent-system/tests/eval/rubrics/communication.yaml`<br>`lia-agent-system/tests/eval/rubrics/pipeline.yaml` |
| 🟢 | `dd28d5a6c` | 2026-04-14 | Testes | feat: golden datasets 10 screening + 10 sourcing [P37-047] — Sprint 6 item 6.2 — 20 structured golden scenarios for the 2 most | `lia-agent-system/tests/eval/datasets/screening/scenarios.yaml`<br>`lia-agent-system/tests/eval/datasets/sourcing/scenarios.yaml` |
| 🟢 | `fc29037a1` | 2026-04-14 | Testes | feat: eval runner CLI — centralized eval orchestrator [P37-046] — Sprint 6 item 6.1 — Unified CLI for running all evaluation suites. | `lia-agent-system/tests/eval/__init__.py`<br>`lia-agent-system/tests/eval/config.yaml`<br>`lia-agent-system/tests/eval/runner.py` |
| 🟢 | `c1089ce32` | 2026-04-14 | Testes | feat: 6 architectural fitness functions [PX08-039] — Sprint 4 item 4.6 — Enforce consolidation decisions. 6 tests: | `lia-agent-system/tests/fitness/__init__.py`<br>`lia-agent-system/tests/fitness/test_architectural_fitness.py` |
| 🟡 | `48a3c2571` | 2026-04-14 | Backend | feat: guardrails_block.yaml — behavioral limits for all agents [P35-042] — Sprint 5 item 5.2 — Extracted cross-domain guardrails into YAML: | `lia-agent-system/app/domains/compliance_base.py`<br>`lia-agent-system/app/prompts/shared/guardrails_block.yaml` |
| 🟡 | `f6da91016` | 2026-04-14 | Backend | feat: compliance_block.yaml — YAML-driven prompt compliance [P35-041] — Sprint 5 item 5.1 — Extracted hardcoded LGPD/fairness/bias compliance | `lia-agent-system/app/domains/compliance_base.py`<br>`lia-agent-system/app/prompts/shared/compliance_block.yaml` |
| 🟡 | `8d6442e65` | 2026-04-14 | Backend | fix: add query_embeddings cleanup to LGPD deletion propagation [P35-033] — query_embeddings was listed in _SECONDARY_PII_TABLES but skipped with | `lia-agent-system/app/domains/lgpd/services/lgpd_cleanup_service.py` |
| 🟡 | `401bc516b` | 2026-04-14 | Cross IA↔Back | feat: protected attributes YAML single source of truth [P35-045] — Sprint 5 item 5.5 — Created config/protected_attributes.yaml with 14 | `lia-agent-system/app/shared/compliance/fairness_guard.py`<br>`lia-agent-system/app/shared/compliance/protected_attributes.py` |
| 🟡 | `0170c713b` | 2026-04-14 | Backend | feat: LGPD deletion propagation to secondary stores [P35-033] — Sprint 3 item 3.6 — run_cleanup() now propagates candidate deletion to: | `lia-agent-system/app/domains/lgpd/services/lgpd_cleanup_service.py` |
| 🟡 | `9c739b7cf` | 2026-04-14 | Backend | feat: LGPD consent gate on all outbound communication [P35-032] — Sprint 3 item 3.5 — No communication was checking LGPD consent before | `lia-agent-system/app/domains/communication/services/communication_service.py`<br>`lia-agent-system/app/domains/communication/services/consent_gate.py`<br>`lia-agent-system/app/domains/lgpd/services/consent_checker_service.py` |
| 🟡 | `48d09a3fd` | 2026-04-14 | Backend | feat: FairnessGuard post-check on agent output [P35-028] — Sprint 3 item 3.1 — Added fairness analysis on agent OUTPUT in | `lia-agent-system/app/config/fairness_post_check.yaml`<br>`lia-agent-system/app/domains/compliance_base.py` |
| 🟡 | `a111f3691` | 2026-04-13 | Frontend (UI) | Redesign weekly digest chat card + complete E2E test suite fixes — Weekly Digest Chat Message: | `plataforma-lia/src/components/notifications/weekly-digest-chat-message.tsx`<br>`plataforma-lia/src/components/settings/integrations/IntegrationDetailDrawer.tsx`<br>`plataforma-lia/src/components/settings/integrations/integration-data.ts` |
| 🟡 | `8e83578d1` | 2026-04-13 | Cross IA↔Back | feat(compliance): Fase 3b — WS/SSE compliance strangler LIA-C3b — User-directed implementation of C3b compliance layer (strangler pattern). | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/candidate_compare.py`<br>`lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `e35ff6a59` | 2026-04-13 | Backend | feat(LIA-P02,Fase3c): close compliance gaps for Path C (LLM-direct endpoints) — Two cirurgical fixes that close the real compliance gaps identified | `lia-agent-system/app/domains/ai/services/llm.py` |
| 🟡 | `a2d054dc4` | 2026-04-13 | Backend | docs(autonomous): clarify compliance contract (no domain.py by design) — autonomous is Tier 6 cross-domain fallback. Compliance applied via infrastructure: | `lia-agent-system/app/domains/autonomous/__init__.py` |
| 🟡 | `0da288f42` | 2026-04-13 | Backend | feat(LIA-C01): enforce ComplianceDomainPrompt inheritance in registry — Before: logger.error only — non-compliant domains still registered. | `lia-agent-system/app/domains/registry.py` |
| 🟢 | `b14ce55b9` | 2026-04-13 | Docs | docs: Agent Studio Enterprise final delivery report — Comprehensive report of all 17 commits delivered in the marathon session | `AGENT_STUDIO_ENTERPRISE_DELIVERY_REPORT.md` |
| 🔴 | `e206cb06e` | 2026-04-13 | Cross Back↔Front | feat(studio): P2.3 — Compliance Dashboard — Backend: GET /custom-agents/studio/compliance-summary | `lia-agent-system/app/api/v1/custom_agents.py`<br>`plataforma-lia/src/app/api/backend-proxy/custom-agents/studio-compliance-summary/route.ts`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| 🟡 | `565cceb26` | 2026-04-13 | Backend | feat(pipeline): F3 - unified pipeline, 9/9 entry points with compliance [LIA-P01-P05] — - LIA-P01: FairnessGuard + check_input_security before SSE streaming in chat.py | `lia-agent-system/app/api/v1/agent_chat_sse.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/lia_assistant/insights.py` |
| 🟡 | `801ef14db` | 2026-04-13 | Backend | feat(compliance): F1 - enforce compliance impossible to bypass [LIA-C01,C05,C06,C07] — - LIA-C01: registry rejects domains without ComplianceDomainPrompt (ERROR log) | `lia-agent-system/app/api/v1/alerts.py`<br>`lia-agent-system/app/api/v1/communications.py` |
| | _… +89 commits adicionais (ver Apêndice C nos anexos)_ | | | | |

### Configurações (hub)

**Descrição:** Hub Configurações reorganizado em fases. Fase 2.5: fechamento de pendências. Fase 3: polir UI, proxy e DS v4.2.2 (Task #929). Cobertura backend 14/24 → 24/24 (Task #930). Auditoria Lotes 4b/4c/4e/4f (Task #918). Governança section (Task #904 rev 3). Documentar arquitetura (Task #903). i18n 42% across 5 hubs. Split monoliths e remove `: any`/`as any` (T902). Consolidar wrappers Standalone+Templates (T900). Cobertura mínima testes (T896). Limpeza Lotes (T897, T894). Limpeza Lote 3 pages/integrations (singletons órfãos).

**⚠️ Dependências para cherry-pick:** DS v4.2.2 ativo | apiFetch nos fetches remanescentes | proxy alinhado | i18n keys completas

**Arquivos canônicos:** plataforma-lia/src/components/settings/*, src/app/settings/*, lia-agent-system/app/api/v1/settings_*.py

**Docs de referência:** BRANCH_MAP — Configurações Fase 3

- **Commits:** 102  |  **Período:** 2026-03-27 → 2026-04-29  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×48 🟡×40 🔴×14

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `acc4a4e41` | 2026-04-29 | Testes | test(api/v1): expand Configurações backend coverage 14/24 → 24/24 (Task #930) — Adiciona 9 arquivos de teste novos em `lia-agent-system/tests/api/v1/` | `lia-agent-system/tests/api/v1/test_llm_config_coverage.py`<br>`lia-agent-system/tests/api/v1/test_stage_transition_automation_coverage.py`<br>`lia-agent-system/tests/api/v1/test_webhooks_coverage.py` |
| 🟡 | `afe709945` | 2026-04-29 | Backend | Task #930 — Configurações Fase 3: cobertura backend 14/24 → 24/24 — Adiciona 9 arquivos novos em lia-agent-system/tests/api/v1/ cobrindo os | `lia-agent-system/app/api/v1/tasks.py` |
| 🟢 | `6964ece62` | 2026-04-29 | Frontend (UI) | Configurações Fase 3 — polir UI, proxy e DS v4.2.2 (Task #929) — Housekeeping no menu Configurações sem mudança de comportamento: | `plataforma-lia/src/components/settings/WebhooksManager.tsx` |
| 🟢 | `906179a75` | 2026-04-29 | Frontend (UI) | chore(settings): commit residual WorkforceHubContent.tsx | `plataforma-lia/src/components/settings/WorkforceHubContent.tsx` |
| 🟡 | `844a3aa76` | 2026-04-29 | Frontend (UI) | chore(settings): commit pendente — cleanup residual das sessoes de settings audit | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/FairnessComplianceHub.tsx`<br>`plataforma-lia/src/components/settings/IntegrationsHub.tsx` |
| 🟡 | `477eae94a` | 2026-04-29 | Frontend (UI) | chore(settings): #928 housekeeping — apiFetch em fetches remanescentes (T6/D-4) — Pivot do session_plan para fechar o audit do menu Configurações. | `plataforma-lia/src/components/settings/benefits/BenefitsListSection.tsx`<br>`plataforma-lia/src/components/settings/benefits/useBenefitsTab.ts`<br>`plataforma-lia/src/components/settings/communication-hub/ABTestingTab.tsx` |
| 🟢 | `ed41d7309` | 2026-04-28 | Docs | Update design token version and fix tracker syntax in settings — Update design token version from v4.2.1 to v4.2.2 and correct invalid syntax in the use-teams-tab-tr | `replit.md` |
| 🔴 | `b4753d320` | 2026-04-28 | Cross Back↔Front | audit configurações fase 3 — task #927 quick wins + bonus T5/T6 da sessão — a11y CRITICAL nos 7 hubs/tabs do menu Configurações: | `lia-agent-system/app/api/v1/wsi/reports.py`<br>`plataforma-lia/src/components/settings/BigFiveRadar.tsx`<br>`plataforma-lia/src/components/settings/DocumentUploadCard.tsx` |
| 🔴 | `28c20b355` | 2026-04-28 | Cross Back↔Front | Configurações Fase 2.5: fechamento das pendências do audit 28/abr/2026 — Aplicadas as skills canonical-fix, design-standardize, feature-impact e | `lia-agent-system/app/api/v1/voice_stream.py`<br>`plataforma-lia/src/components/settings/FairnessComplianceHub.tsx`<br>`plataforma-lia/src/components/settings/StudioComplianceView.tsx` |
| 🟡 | `a490827f2` | 2026-04-28 | Frontend (UI) | Translate Settings screens + locale-aware seed data (incl. recruitment/) — Task #923 — make plataforma-lia/src/components/settings/**/*.tsx fully bilingual | `plataforma-lia/src/components/settings/BigFiveRadar.tsx`<br>`plataforma-lia/src/components/settings/DataRequestConfigSections.tsx`<br>`plataforma-lia/src/components/settings/DocumentUploadCard.tsx` |
| 🔴 | `d6a8d109c` | 2026-04-28 | Cross Back↔Front | i18n(settings): translate Configurações to English (Task #919) — Translated hardcoded PT strings to use `useTranslations` across 53/75 (70.7%) | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/AIConfigPreview.tsx`<br>`plataforma-lia/src/components/settings/BenefitsTab.tsx` |
| 🟢 | `45e562148` | 2026-04-28 | Docs | Task #918: Encerrar Lotes 4b/4c/4e/4f da auditoria de Configurações — Original task: remover o restante do código morto identificado nos lotes | `replit.md` |
| 🟡 | `6d86c44d9` | 2026-04-28 | Frontend (UI) | Task #904: Governança section in Configurações (rev 3 — backend contract alignment) — Adds a 6-panel Governança hub to plataforma-lia Configurações exposing | `plataforma-lia/src/app/api/backend-proxy/automation-rules/[ruleId]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/automation-rules/[ruleId]/toggle/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/automation-rules/company/[companyId]/route.ts` |
| 🟢 | `34e2de8ba` | 2026-04-28 | Docs | Documentar arquitetura final do menu Configurações (Task #903) — Atualiza memória persistente do projeto após a Fase 2 de canonicalização do | `replit.md` |
| 🟡 | `59eaac588` | 2026-04-28 | Frontend (UI) | i18n: lift settings/ coverage to 42% across 5 hubs — Task #901 — added next-intl coverage to the 5 settings hubs and their | `plataforma-lia/src/components/settings/CompanyDataCard.tsx`<br>`plataforma-lia/src/components/settings/FairnessComplianceHub.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx` |
| 🟡 | `107ac9e76` | 2026-04-28 | Frontend (UI) | T902: split settings monoliths and remove `: any` / `as any` — BenefitsTab.tsx (715 → 189 LoC orchestrator): | `plataforma-lia/src/components/settings/BenefitsTab.tsx`<br>`plataforma-lia/src/components/settings/CommunicationHub.tsx`<br>`plataforma-lia/src/components/settings/FairnessComplianceHub.tsx` |
| 🟡 | `e4ff87f9b` | 2026-04-28 | Frontend (UI) | Task #900 — Configurações: consolidar wrappers Standalone+Templates — What changed | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/CommunicationHub.tsx`<br>`plataforma-lia/src/components/settings/PipelineStandalone.tsx` |
| 🟢 | `23a56756d` | 2026-04-28 | Frontend (UI) | Task #896 — cobertura mínima de testes para o menu Configurações — Implementa o "minimum test coverage" pedido para o hub de | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| 🟡 | `9143c277e` | 2026-04-28 | Frontend (UI) | Task #897 — Configurações: limpeza Lote 1 (cluster Goals/Workforce) — Removido cluster órfão "Goals/Workforce planning" do diretório | `plataforma-lia/src/components/settings/GoalsAlertsSection.tsx`<br>`plataforma-lia/src/components/settings/GoalsFormModals.tsx`<br>`plataforma-lia/src/components/settings/GoalsPlanningHub.tsx` |
| 🟢 | `9955bd284` | 2026-04-28 | Frontend (UI) | Task #894 — Configurações: consertar rotas fantasma — ## Original task | `plataforma-lia/src/components/modals/job-publish-modal.tsx`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| 🟡 | `d36663115` | 2026-04-28 | Frontend (UI) | Configurações: limpeza Lote 3 (pages/integrations + singletons órfãos) — Task #899 — deleta o cluster top-level `components/pages/integrations*` | `plataforma-lia/src/components/pages/IntegrationsList.tsx`<br>`plataforma-lia/src/components/pages/IntegrationsSidebar.tsx`<br>`plataforma-lia/src/components/pages/IntegrationsStatsCards.tsx` |
| 🟡 | `07838c1fb` | 2026-04-25 | Backend | Task #812: company_settings — tools operacionais primárias — Estende o agente `company_settings` para atender intenções operacionais | `lia-agent-system/app/domains/company_settings/agents/company_tool_registry.py`<br>`lia-agent-system/app/prompts/shared/agent_prompts.yaml`<br>`lia-agent-system/tests/standalone/test_task812_company_settings_operational.py` |
| 🟡 | `8d3c985d8` | 2026-04-25 | Cross IA↔Back | [task #812] company_settings: cobrir ações primárias (canonical-fix PT-BR) — Defesa em profundidade complementar à Task #811: o agente `company_settings` | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🔴 | `833241d10` | 2026-04-21 | Cross Back↔Front | fix: corrige botao Analisar nosso site em MinhaEmpresaHub — RCA: prompt sem URL + autoSend false + system prompt sem invocacao direta | `plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx` |
| 🟢 | `18e736d99` | 2026-04-21 | Empty/merge | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do menu Configuracoes as 7 actions de company_settings | — |
| 🟢 | `b6c590aca` | 2026-04-21 | Empty/merge | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do menu Configuracoes as 7 actions de company_settings | — |
| 🟢 | `a3bd0d6cd` | 2026-04-21 | Empty/merge | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do menu Configuracoes as 7 actions de company_settings | — |
| 🟡 | `1c91a070e` | 2026-04-21 | Backend | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do menu Configuracoes as 7 actions de company_settings | `lia-agent-system/app/domains/company_settings/domain.py` |
| 🟢 | `8f3821a6e` | 2026-04-20 | Empty/merge | Task #712 — onboarding proativo + 7 actions company_settings (full) — Original: conectar 100% do menu Configuracoes as 7 actions de company_settings | — |
| 🟡 | `e8d4bd443` | 2026-04-20 | Backend | Task #712 — onboarding proativo + 7 actions company_settings (post code-review) — Original: conectar 100% do menu Configuracoes as 7 actions de company_settings | `lia-agent-system/app/domains/ats_integration/services/ats_clients/wedotalent_rails.py` |
| 🔴 | `d1ed07e4d` | 2026-04-20 | Cross Back↔Front | Task #712: company_settings delega 7 actions + onboarding proativo — Backend (lia-agent-system): | `lia-agent-system/app/domains/company_settings/domain.py`<br>`plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/onboarding/SetupProgressBanner.tsx` |
| 🟢 | `d689a913c` | 2026-04-20 | Frontend (UI) | Adjust user card styling to match table density — Update user list component to apply compact styling to status and SSO chips, reduce avatar size, and | `plataforma-lia/src/components/settings/user-list.tsx` |
| 🔴 | `9ebfa3359` | 2026-04-19 | Cross Back↔Front | Add functionality to manage candidate requests and improve system stability — Introduce new API endpoints for handling RH dashboard requests, implement LGPD Art. 20 request loggi | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/rh_dashboard.py`<br>`lia-agent-system/app/domains/hiring_policy/domain.py` |
| 🟡 | `3464e6021` | 2026-04-19 | Backend | feat(company): D5 guided onboarding flow in company_settings agent — Extends existing CompanySettingsReActAgent (no new agent class) with an | `lia-agent-system/app/domains/company_settings/agents/company_system_prompt.py` |
| 🟡 | `eee514587` | 2026-04-19 | Cross IA↔Back | feat(lia-tools): D1 enrichment + company settings tools — D1.a enrichment_tools.py (sourcing domain, 2 tools): | `lia-agent-system/app/tools/__init__.py` |
| 🟡 | `c134dc252` | 2026-04-18 | Cross IA↔Back | fix(settings): company resolve-tenant null profile + LIA settings_config routing — - company.py: resolve-tenant fallback to client_account_id when no company_profile | `lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/orchestrator/domain_mappings.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟢 | `a3a10761a` | 2026-04-18 | Frontend (UI) | Fix manual inline editing across Settings (Task #509) — Inline pencil/check editors in Configurações → Minha Empresa and Políticas de | `plataforma-lia/src/components/settings/HiringPoliciesHub.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaCard.tsx` |
| 🟢 | `916cdb3c4` | 2026-04-18 | Frontend (UI) | Task #500 — Corrigir 'Failed to fetch' na tela de Configurações — Problema: | `plataforma-lia/src/components/screening-config/SCMSectionPerguntasEdit.tsx`<br>`plataforma-lia/src/components/screening-config/hooks/useScreeningConfigManagerCore.tsx`<br>`plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx` |
| 🔴 | `b2086c0c4` | 2026-04-17 | Cross Back↔Front | Improve screening invitation modal and configuration settings — Updates the screening invitation modal to correctly disable the send button based on candidate conta | `lia-agent-system/app/api/v1/chat.py`<br>`plataforma-lia/src/components/screening-config/SCMSectionConfiguracoes.tsx`<br>`plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx` |
| 🟢 | `5f3e8cd88` | 2026-04-17 | Frontend (api/util) | Apply loading watchdog to company-settings (Minha Empresa) hub — Task #259: Protect the company-settings page from stuck loading | `plataforma-lia/src/hooks/settings/use-company-settings-cards.ts` |
| 🟡 | `36a3f6dfb` | 2026-04-17 | IA | Task #320: Close routing for CompanySettingsReActAgent (W16/W19) — The auditoria gap was that domain_mappings.py already mapped | `lia-agent-system/app/orchestrator/config/domain_routing.yaml` |
| 🟡 | `ce58b5f6e` | 2026-04-15 | IA | Fix Settings chat domain routing: company_settings agent now receives messages — Problem: Messages sent from the Settings > Minha Empresa page were being | `lia-agent-system/app/orchestrator/chat_adapter.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟢 | `8a0c236a0` | 2026-04-15 | Testes | Update end-to-end tests for settings migration and add new test cases — Refine existing end-to-end tests for settings migration, improve assertions, remove conditional guar | `plataforma-lia/e2e/reports/settings-migration-results.md`<br>`plataforma-lia/e2e/tests/settings-migration.spec.ts` |
| 🟢 | `59b7c67cc` | 2026-04-15 | Frontend (UI) | Task #211: Migração Settings — Testes E2E Completos — Added comprehensive E2E test suite with 16 test cases and testability improvements: | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| 🟢 | `1b29ebb23` | 2026-04-15 | Testes | Task #211: Migração Settings — Testes E2E Completos — Created comprehensive E2E test suite (settings-migration.spec.ts) with 15 test cases: | `plataforma-lia/e2e/reports/settings-migration-results.md`<br>`plataforma-lia/e2e/tests/settings-migration.spec.ts` |
| 🟢 | `9130f41ae` | 2026-04-15 | Testes | Task #211: Migração Settings — Testes E2E Completos — Added E2E test suite for Settings migration validation: | `plataforma-lia/e2e/reports/settings-migration-results.md`<br>`plataforma-lia/e2e/tests/settings-migration.spec.ts` |
| 🟡 | `8a1e93da7` | 2026-04-15 | Backend | Update company ID query description to clarify default usage — Modify the description for the `company_id` query parameter in the settings progress endpoint to acc | `lia-agent-system/app/api/v1/settings_progress.py` |
| 🟢 | `0ed6cdfe6` | 2026-04-15 | Frontend (UI) | Task #208: Reestruturar Menu Configurações — 7 Novos Itens — - Refactored settings menu from old 7 items (with subsections) to 7 new flat items: | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/PipelineStandalone.tsx`<br>`plataforma-lia/src/components/settings/ScreeningStandalone.tsx` |
| 🟡 | `5a3483c50` | 2026-04-15 | Frontend (UI) | Task #208: Reestruturar Menu Configurações — 7 Novos Itens — - Refactored settings menu from old 7 items (with subsections) to 7 new flat items: | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/CommunicationHub.tsx`<br>`plataforma-lia/src/components/settings/RecruitmentHub.tsx` |
| 🟢 | `83fa64e3a` | 2026-04-15 | Frontend (api/util) | feat(task-207): UnifiedChat context switching for settings_config — Changes: | `plataforma-lia/src/hooks/settings/use-company-settings-cards.ts` |
| 🟢 | `c026791c1` | 2026-04-15 | Frontend (api/util) | feat(task-207): UnifiedChat context switching for settings_config — Task: Migração Settings — UnifiedChat Context Switching settings_config | `plataforma-lia/src/hooks/settings/use-company-settings-cards.ts` |
| 🟢 | `d37b2981e` | 2026-04-15 | Frontend (UI) | feat(task-207): UnifiedChat context switching for settings_config — Task: Migração Settings — UnifiedChat Context Switching settings_config | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatEmptyState.tsx`<br>`plataforma-lia/src/contexts/lia-float-context.tsx` |
| 🟢 | `05a309895` | 2026-04-15 | Frontend (UI) | Update company settings to correctly handle headquarters location — Fix the mapping for headquarters in the company profile API to correctly split city and state from a | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| 🟡 | `e484d90a5` | 2026-04-15 | Backend | Task #203: Backend company_settings domain integration + hardening — Domain Registration (6 gaps closed): | `lia-agent-system/app/domains/company_settings/agents/company_tool_registry.py` |
| 🟡 | `1796d2d01` | 2026-04-15 | IA | Task #203: Backend — Conectar domínio company_settings + Hardening — Gaps de registro fechados (6/6): | `lia-agent-system/app/shared/compliance/audit_service.py` |
| 🟡 | `f838be881` | 2026-04-15 | Backend | Task #203: Backend — Conectar domínio company_settings + Hardening — Gaps de registro fechados: | `lia-agent-system/app/api/v1/settings_progress.py`<br>`lia-agent-system/app/domains/company/repositories/settings_progress_repository.py` |
| 🟡 | `17828c389` | 2026-04-15 | Backend | Task #203: Backend — Conectar domínio company_settings + Hardening — Gaps de registro fechados: | `lia-agent-system/app/api/v1/settings_progress.py` |
| 🟡 | `70c32ce48` | 2026-04-15 | Cross IA↔Back | Task #203: Backend — Conectar domínio company_settings + Hardening — Gaps de registro fechados: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/settings_progress.py`<br>`lia-agent-system/app/domains/company/repositories/settings_progress_repository.py` |
| 🟢 | `bb2029d2c` | 2026-04-15 | Docs | Task #202: Auditoria profunda - Migração Settings Conversacional — Produced comprehensive diagnostic document S01_DIAGNOSTICO.md covering | `docs/settings-conversacional/S01_DIAGNOSTICO.md` |
| 🟢 | `736a09ede` | 2026-04-14 | Frontend (UI) | Fix communication settings API to pass authentication token and handle errors gracefully — Corrected `communication-settings` route to pass auth token and added default error responses for GE | `plataforma-lia/src/app/api/backend-proxy/company/communication-settings/route.ts` |
| | _… +42 commits adicionais (ver Apêndice C nos anexos)_ | | | | |

### §9 Security / Tenant guards

**Descrição:** Tenant guards P0 — get_current_user_or_demo + validate_company_access em endpoints zero-auth: pipeline_prediction, user_agent_preferences, company_benefits, pipeline_velocity, early_warning, skills_catalog, approvals, lia_profile_analysis, voice_stream, journey_mapping. Test suite test_tenant_scope_v1 (18 testes 401/403/200).

**⚠️ Dependências para cherry-pick:** auth dependency em TODOS endpoints sensíveis | tests com _is_dev_environment patch | nenhum endpoint zero-auth restante

**Arquivos canônicos:** lia-agent-system/app/api/v1/* (tenant guards added), tests/integration/test_tenant_scope_v1.py

**Docs de referência:** BRANCH_MAP §9

- **Commits:** 78  |  **Período:** 2026-03-29 → 2026-04-28  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×36 🔴×21 🟢×21

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `03fbf3841` | 2026-04-28 | Backend | Add authentication and authorization checks to API endpoints — Update API endpoints in multiple modules to include authentication using `get_current_user_or_demo`  | `lia-agent-system/app/api/v1/company_assessments.py`<br>`lia-agent-system/app/api/v1/company_culture_config.py`<br>`lia-agent-system/app/api/v1/interview_analysis.py` |
| 🟡 | `2f09160ff` | 2026-04-27 | Cross IA↔Back | fix(security): W7.2 PromptInjectionGuard global — bridge + cascaded router — - TeamsOrchestratorBridge.process_message(): defense-in-depth guard before | `lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py` |
| 🟡 | `151912552` | 2026-04-27 | Backend | Improve security by ensuring all privileged actions are refused when tenant boundaries cannot be verified — Update Teams webhook to implement a fail-closed security policy, refusing privileged actions | `lia-agent-system/app/api/v1/teams.py` |
| 🟡 | `4f1cdfa3f` | 2026-04-27 | Backend | Update security and testing for job management and team webhooks — Adjusted job management evaluation results and enhanced security and testing for team webhooks by re | `lia-agent-system/eval/eval_results_20260426_235425.json`<br>`lia-agent-system/tests/integration/test_teams_webhook_company_id_w1_2.py` |
| 🟡 | `0dc4d0a95` | 2026-04-18 | Backend | Improve error message for invalid authentication tokens — Update the error response for invalid or expired tokens to include more specific details about the a | `lia-agent-system/app/middleware/auth_enforcement.py` |
| 🟡 | `6c5c7bfaf` | 2026-04-15 | Backend | Improve security by blocking access to internal network addresses — Update URL validation logic in `_wrap_analyze_company_website` to use the `ipaddress` module for mor | `lia-agent-system/app/domains/company_settings/agents/company_tool_registry.py` |
| 🔴 | `5f705ff1b` | 2026-04-14 | Cross Back↔Front | feat: calibration dashboard — LIA vs recruiter divergences [PX08-068] — Sprint 10 item 10.3 — Backend + Frontend for calibration analysis. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/calibration_dashboard_v2.py`<br>`plataforma-lia/src/app/api/backend-proxy/analytics/calibration-dashboard/route.ts` |
| 🟡 | `3a7b377d1` | 2026-04-14 | Backend | feat: CalibrationEvent auto-record in EnhancedAgentMixin [P35-030] — Sprint 3 item 3.3 — CalibrationEvent existed but was only created | `lia-agent-system/libs/models/lia_models/calibration.py` |
| 🟡 | `868c6b0d4` | 2026-04-12 | Backend | Enhance agent security and LLM tenant compliance across multiple services — Introduces security patterns, fairness guards, and PII stripping in agent runtime, alongside tenant- | `lia-agent-system/app/domains/agent_studio/custom_agent_runtime.py` |
| 🟡 | `979a613d7` | 2026-04-12 | Infra/Config | Fix: npm audit fix - DOMPurify vulnerabilities resolved | `package-lock.json` |
| 🟡 | `64b9ae4ee` | 2026-04-12 | Backend | feat: GAP 1-4,6 — Agent Studio parity with product agents — GAP 1: SystemPromptBuilder in custom_agent_runtime._get_system_prompt() | `lia-agent-system/app/api/v1/custom_agents.py` |
| 🟢 | `09c05517c` | 2026-04-12 | Frontend (api/util) | fix: resolve 9 critical security vulnerabilities (npm audit fix) — Updated next 15.5.14 → patched (DoS via Server Components) | `plataforma-lia/package-lock.json` |
| 🟡 | `bcabfe479` | 2026-04-12 | Backend | feat: connect TenantContextService to SSE streaming endpoint — SSE streaming now passes tenant_context_snippet to SystemPromptBuilder. | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `298173746` | 2026-04-12 | Backend | feat: add FairnessGuard + SecurityPatterns to WebSocket handler (Item 4) — WS endpoint now has 3 layers of security pre-check: | `lia-agent-system/app/api/v1/agent_chat_ws.py` |
| 🟡 | `668966ac6` | 2026-04-12 | Backend | Task #162: Interview Intelligence Pro — Security + Bias + Comparative fixes — Code review round 2 fixes: | `lia-agent-system/app/domains/interview_intelligence/services/bias_detector_service.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/comparative_analysis_service.py` |
| 🟡 | `c91bd09c5` | 2026-04-12 | Backend | fix: add is_blocked property to InjectionCheckResult (security bug) — compliance_base.py:376 called result.is_blocked but InjectionCheckResult | `lia-agent-system/app/shared/prompt_injection.py` |
| 🟡 | `5f9bd57a4` | 2026-04-11 | IA | Improve screening process security and update documentation — Remove sensitive token from screening response and update audit report. | `lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py` |
| 🟡 | `3a4af080a` | 2026-04-10 | Backend | Improve security scanning by removing extraneous output — Modify CI workflow to adjust the output of Bandit SAST scan and pip-audit dependency vulnerability c | `lia-agent-system/.github/workflows/deploy.yml` |
| 🟡 | `bdf5afff5` | 2026-04-10 | Outro | Update project dependencies and resolve security vulnerabilities — Update outdated project dependencies to address critical security vulnerabilities and ensure a stabl | `._onboarding-patches`<br>`onboarding-deploy.tar.gz` |
| 🟡 | `4c7aa1fb0` | 2026-04-10 | Frontend (api/util) | Update project dependencies to address security vulnerabilities — Update aiohttp, jspdf, next, and jira.js dependencies across the project to resolve critical securit | `.claude/worktrees/agent-a92b041a/plataforma-lia/package-lock.json`<br>`.claude/worktrees/agent-a92b041a/plataforma-lia/package.json`<br>`.claude/worktrees/agent-af767ad0/plataforma-lia/package-lock.json` |
| 🟡 | `b59c332cb` | 2026-04-10 | Backend | Improve security and reliability of Rails integration endpoints — Update Rails integration endpoints and tests to dynamically read environment variables for configura | `lia-agent-system/app/api/v1/rails_health.py`<br>`lia-agent-system/app/api/v1/rails_sync.py` |
| 🔴 | `1c0fc21b6` | 2026-04-09 | Cross IA↔Front | Task #94: Choose Your AI — LLM Config Integration (Wiring + Security + Frontend) — Full end-to-end integration of per-tenant LLM provider configuration. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/llm_config.py`<br>`lia-agent-system/app/domains/ai/repositories/llm_config_repository.py` |
| 🟢 | `c802d7107` | 2026-04-09 | Frontend (UI) | revert: restore secure:true sameSite:none for cookies (HTTPS via Replit proxy) — SameSite=lax breaks in Replit webview iframe context. | `plataforma-lia/src/app/api/auth/session/refresh/route.ts`<br>`plataforma-lia/src/app/api/auth/session/route.ts` |
| 🟢 | `59afe6b6e` | 2026-04-09 | Frontend (api/util) | fix: resolve pipeline overview SQL type mismatch, restore cookie security, add proxy error handling — - Fixed `character varying = uuid` SQL error in job_vacancies_analytics_repository.py | `plataforma-lia/src/middleware.ts` |
| 🔴 | `9ce15b138` | 2026-04-08 | Cross Back↔Front | fix(backend): Task #75 — Backend Deploy Readiness (OpenAPI, Shims, Secrets, Celery, Security) — ## Summary | `lia-agent-system/app/main.py`<br>`lia-agent-system/libs/models/lia_models/intelligent_cache.py`<br>`plataforma-lia/src/app/layout.tsx` |
| 🔴 | `4b4f44771` | 2026-04-08 | Cross Back↔Front | Improve security and user management by isolating tenant data — Enhance multi-tenancy by isolating user data by tenant, preventing cross-tenant access and ensuring  | `lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/api/v1/company_users.py`<br>`lia-agent-system/app/domains/company/repositories/company_profile_repository.py` |
| 🟡 | `053b7d0b5` | 2026-04-08 | Cross IA↔Back | Fix issues with job vacancy display and improve input security — Updates response schemas for job vacancies to correctly handle complex data types, implements multi- | `lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/cv_parser.py` |
| 🔴 | `7c76bd7ac` | 2026-04-08 | Frontend (UI) | Improve security and reliability of authentication and iframe embedding — Update security headers to allow iframe embedding in development environments and switch cookie hand | `plataforma-lia/src/app/api/auth/auto-login/route.ts`<br>`plataforma-lia/src/app/api/auth/session/refresh/route.ts`<br>`plataforma-lia/src/app/api/auth/session/route.ts` |
| 🟢 | `8ed5458f3` | 2026-04-07 | Docs | Update deployment guide with new environment variables and security notes — Update DEPLOY_GUIDE.md to include new environment variables, security alerts, and checklist items fo | `DEPLOY_GUIDE.md` |
| 🟢 | `293e88e6b` | 2026-04-07 | Docs | Add client onboarding, AI workflow, and integration status sections — Adds new sections to the DEPLOY_GUIDE.md covering AI-assisted development, Microsoft Office and Goog | `DEPLOY_GUIDE.md` |
| 🟡 | `4652eaf17` | 2026-04-07 | Backend | feat(security): Task #62 — Segurança Hardening Explícito — ## Summary | `lia-agent-system/app/api/v1/autocomplete.py`<br>`lia-agent-system/app/api/v1/company_departments.py`<br>`lia-agent-system/app/api/v1/company_users.py` |
| 🔴 | `61752038b` | 2026-04-06 | Cross Back↔Front | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5min max age) for replay protection | `lia-agent-system/app/domains/communication/services/email_providers/resend_provider.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesViewComposition.tsx` |
| 🔴 | `4c22ddda8` | 2026-04-06 | Cross Back↔Front | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5min max age) for replay protection | `lia-agent-system/libs/models/lia_models/communication_history.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesActions.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesCVHandlers.ts` |
| 🔴 | `07c43b2e4` | 2026-04-06 | Cross Back↔Front | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5min max age) for replay protection | `lia-agent-system/app/domains/communication/services/email_providers/mailgun_provider.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearch.ts` |
| 🟡 | `b2514cfeb` | 2026-04-06 | Backend | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5min max age) for replay protection | `lia-agent-system/app/api/v1/mailgun_webhooks.py`<br>`lia-agent-system/app/domains/communication/repositories/__init__.py` |
| 🔴 | `43e90596e` | 2026-04-06 | Cross IA↔Front | Security hardening from code review findings: — - Mailgun webhooks: Add timestamp freshness check (5min max age) for replay protection | `lia-agent-system/app/api/public/candidate_portal.py`<br>`lia-agent-system/app/api/public/shared_searches.py`<br>`lia-agent-system/app/api/routes.py` |
| 🟡 | `64ff314ce` | 2026-04-06 | Backend | Task #38: ATS Integration — Full frontend-backend wiring with complete security hardening — Frontend: | `lia-agent-system/app/api/v1/ats.py` |
| 🔴 | `837aef67a` | 2026-04-06 | Cross Back↔Front | Task #38: ATS Integration — Full frontend-backend wiring with security hardening — Frontend: | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/domains/automation/services/pattern_applier.py`<br>`lia-agent-system/app/domains/chat/repositories/__init__.py` |
| 🔴 | `2bbc1edf9` | 2026-04-06 | Cross Back↔Front | Task #38: ATS Integration — Full frontend-backend wiring with security hardening — Frontend: | `lia-agent-system/app/api/v1/ats.py`<br>`plataforma-lia/src/components/settings/integrations/IntegrationDetailDrawer.tsx` |
| 🔴 | `587e96c50` | 2026-04-06 | Cross Back↔Front | Task #38: ATS Integration — Complete frontend-backend wiring with security hardening — Frontend changes: | `lia-agent-system/app/api/v1/ats.py`<br>`plataforma-lia/src/app/api/backend-proxy/ats/connections/sync/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/ats/field-mappings/route.ts` |
| 🟡 | `dc9ff6268` | 2026-04-06 | Backend | Improve backend security by removing demo user fallbacks — Update documentation and logs to reflect backend security hardening and email provider changes. | `lia-agent-system/scripts/check_no_pii_in_logs.py` |
| 🟡 | `438fb466e` | 2026-04-06 | Backend | Task #34: Backend Security Hardening — Remove demo-user fallbacks and protect mock providers — ## Changes | `lia-agent-system/app/domains/communication/services/communication_service.py` |
| 🟡 | `756ab5464` | 2026-04-06 | Backend | Task #34: Backend Security Hardening — Remove demo-user fallbacks and protect mock providers — ## Changes | `lia-agent-system/app/domains/communication/services/communication_service.py` |
| 🟡 | `1f87281fd` | 2026-04-06 | Backend | Task #34: Backend Security Hardening — Remove demo-user fallbacks and protect mock providers — ## Changes | `lia-agent-system/app/api/v1/credits.py`<br>`lia-agent-system/app/api/v1/pipeline_orchestrator.py`<br>`lia-agent-system/app/api/v1/search_feedback.py` |
| 🟡 | `573177e95` | 2026-04-06 | Backend | Update Python dependencies for enhanced security and utility — Remove the python-jose dependency and update other Python packages. | `lia-agent-system/pyproject.toml` |
| 🟢 | `73a7c303c` | 2026-04-06 | Docs | Update hardening plan with security fixes and improvements — Update HARDENING_PLAN.md to include recent security fixes for SQL injection, stack trace leaks, and  | `lia-agent-system/HARDENING_PLAN.md` |
| 🔴 | `9d569d6c7` | 2026-04-06 | Cross Back↔Front | Improve chat functionality and security by adding retries and enhancing authentication — This commit introduces a robust retry mechanism with token refresh for various chat API endpoints. I | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/app/api/backend-proxy/chat/message/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/chat/route.ts` |
| 🟡 | `009229e73` | 2026-04-05 | Outro | Add WorkOS SSO and SCIM integration to the user authentication system — Integrates WorkOS for SSO and SCIM in the `lia-agent-system` (FastAPI), enabling dual authentication | `dump.rdb` |
| 🟢 | `8b010f883` | 2026-04-04 | Frontend (UI) | Address security vulnerabilities by validating redirects and strengthening secret management — Refactor chat and payment handlers to validate redirect URLs, remove fallback secret in production,  | `plataforma-lia/src/components/pages/chat-page/useChatPageHandlers.tsx` |
| 🟡 | `486e42ef5` | 2026-04-03 | Frontend (UI) | Task #107: Complete API validation + security hardening — Frontend API routes: | `plataforma-lia/src/app/api/ai/extract-archetype-info/route.ts`<br>`plataforma-lia/src/app/api/ai/suggest-companies/route.ts`<br>`plataforma-lia/src/app/api/ai/suggest-company-tags/route.ts` |
| 🔴 | `395ad8955` | 2026-04-03 | Cross IA↔Front | Task #107: Complete API validation + security hardening — Frontend API routes: | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`plataforma-lia/src/app/api/ai/extract-archetype-info/route.ts`<br>`plataforma-lia/src/app/api/ai/suggest-companies/route.ts` |
| 🔴 | `e4a5d4705` | 2026-04-03 | Cross Back↔Front | Task #107: API Security - Complete validation hardening — All review issues fixed: | `plataforma-lia/src/app/api/backend-proxy/admin/guardrails/[id]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/admin/guardrails/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/admin/templates/[id]/publish/route.ts` |
| 🔴 | `3597eab4b` | 2026-04-03 | Cross Back↔Front | Task #107: API Security - Fix code review issues — Review fixes round 2: | `plataforma-lia/src/app/api/backend-proxy/analysis/file/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/jd-import/upload/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/candidates/from-cv/route.ts` |
| 🔴 | `e37a20b4b` | 2026-04-03 | Frontend (UI) | Task #107: API Security - Zod validation + Security Headers (review fixes) — Review fixes applied: | `plataforma-lia/src/app/api/auth/session/refresh/route.ts`<br>`plataforma-lia/src/app/api/auth/session/route.ts`<br>`plataforma-lia/src/app/api/auth/workos/callback/route.ts` |
| 🔴 | `6b3e4524f` | 2026-04-03 | Cross Back↔Front | Task #107: API Security - Zod validation + Security Headers — Security Headers: | `plataforma-lia/src/app/api/auth/session/refresh/route.ts`<br>`plataforma-lia/src/app/api/auth/session/route.ts`<br>`plataforma-lia/src/app/api/auth/workos/callback/route.ts` |
| 🟡 | `a677e1a4a` | 2026-04-03 | Frontend (UI) | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Session API == | `plataforma-lia/src/app/api/backend-proxy/agent-memory/[...path]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/candidates/analyze-match-all/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/candidates/bulk/assign-job/route.ts` |
| 🔴 | `7863c72ba` | 2026-04-03 | Cross IA↔Front | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Session API == | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`plataforma-lia/src/app/api/auth/session/route.ts` |
| 🔴 | `7396ade2a` | 2026-04-03 | Cross IA↔Front | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Session API == | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`lia-agent-system/app/tools/scope_config.py` |
| 🔴 | `6399beccf` | 2026-04-03 | Cross IA↔Front | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Core changes == | `lia-agent-system/app/tools/__init__.py` |
| 🟢 | `294e715a5` | 2026-04-03 | Frontend (api/util) | Task #106: Security P0 — Auth Migration (localStorage → httpOnly Cookies) + Middleware — == Core changes == | `plataforma-lia/package-lock.json`<br>`plataforma-lia/package.json`<br>`plataforma-lia/src/middleware.ts` |
| | _… +18 commits adicionais (ver Apêndice C nos anexos)_ | | | | |

### Kanban (vagas)

**Descrição:** Kanban de vagas — KanbanColumnShell + chip variant tokens (Task #454). KanbanCardInterviewButtons. Manage job proposals from kanban. WSI degraded mode toggle (Task #538). Indicador visual modo degradado no score WSI (Task #530). Fixes E2E (5 bugs: offer onClick, WSI modal, preview, filtros, shortlist).

**⚠️ Dependências para cherry-pick:** WSI 0-10 | Offer Review Modal aberto via lia:open_offer_review | DS v4.2.2 tokens

**Arquivos canônicos:** plataforma-lia/src/components/pages/job-kanban/*, src/lib/design-tokens.ts

**Docs de referência:** BRANCH_MAP / kanban-full-audit.spec.ts

- **Commits:** 75  |  **Período:** 2026-03-19 → 2026-04-21  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×49 🟡×18 🔴×8

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `f17e65280` | 2026-04-21 | Frontend (UI) | Fix infinite loop in candidate transition modal — Stabilize object references using useMemo in `useUniversalTransitionModal.tsx` to prevent infinite r | `plataforma-lia/src/components/kanban/components/useUniversalTransitionModal.tsx` |
| 🟢 | `966c7ad1f` | 2026-04-21 | Frontend (UI) | Make saturation badge font size smaller to match other badges — Adjust the SaturationBadge component in `SaturationBadge.tsx` to use `density="compact"` to align it | `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx` |
| 🟢 | `7b2b63144` | 2026-04-21 | Frontend (UI) | Add ability to manage job proposals from the kanban board — Integrates a new 'Manage Proposal' action into the Kanban board, allowing users to initiate proposal | `plataforma-lia/src/components/pages/job-kanban/KanbanBoardSection.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCardInterviewButtons.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx` |
| 🟢 | `c00ac25df` | 2026-04-19 | Frontend (UI) | Add semantic icons to job cards for better visual representation — Update KanbanCard component, tests, types, and job transformation logic to include semantic icons (b | `plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/types.ts` |
| 🔴 | `c5b577cf5` | 2026-04-19 | Cross IA↔Front | Task #562 — Padronizar e enriquecer card do Kanban de Vagas — Alinha o card de vaga (página /jobs, visão Kanban) ao padrão visual e | `lia-agent-system/app/api/v1/llm_config.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/services/wsi_compact_pipeline.py` |
| 🟡 | `6590ad88e` | 2026-04-19 | Frontend (UI) | Task #562 — Padronizar e enriquecer card do Kanban de Vagas — Alinha o card de vaga (página /jobs, visão Kanban) ao padrão visual e | `plataforma-lia/src/components/pages/job-kanban/JobKanbanMiniFunnel.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx` |
| 🟡 | `0bce0e5f9` | 2026-04-19 | Frontend (UI) | Add "Apenas modo degradado" toggle to job kanban (Task #538) — Original task | `plataforma-lia/src/components/pages/job-kanban/KanbanBoardSection.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanPageContent.tsx` |
| 🟢 | `4acd3f415` | 2026-04-19 | Frontend (UI) | Add degraded analysis mode indicator to job kanban views — Adds a warning indicator and tooltip to Kanban cards and table cells when an analysis is in degraded | `plataforma-lia/src/components/pages/job-kanban/KanbanCardScores.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanScoreCells.tsx` |
| 🟢 | `1f77b5bfc` | 2026-04-18 | Frontend (UI) | Task #503: Escurecer pílulas e tipografia dos cards do Kanban — Original: ajuste cirúrgico nos tokens canônicos do kanban (vagas e | `plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx` |
| 🟢 | `5817d8a38` | 2026-04-18 | Frontend (UI) | Task #499 — fix kanban visual regressions (chips, column bg, compare control) — Original task: ajustar regressões visuais introduzidas em #444/#445/#454/#466 nos kanbans | `plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx` |
| 🟢 | `e6868bf2d` | 2026-04-18 | Frontend (UI) | Padroniza pílulas do cartão de candidato com KanbanChip canônico — Task #460: migrar `KanbanCardStatusBadges` para usar o `KanbanChip` | `plataforma-lia/src/components/pages/job-kanban/KanbanCardStatusBadges.tsx` |
| 🔴 | `50434ab66` | 2026-04-18 | Cross Back↔Front | Task #454 — KanbanColumnShell + chip variant tokens — Closes the kanban standardization series (#443 toolbar → #444 header | `plataforma-lia/src/components/pages/job-kanban/KanbanChip.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx` |
| 🟢 | `176ad9006` | 2026-04-18 | Frontend (UI) | fix(jobs-kanban): restore horizontal scroll on Vagas Kanban (Task #453) — Original task: rightmost columns (e.g. "Encerradas") on the Vagas Kanban | `plataforma-lia/src/components/pages/jobs/JobsKanbanView.tsx` |
| 🟢 | `65a8524fb` | 2026-04-18 | Frontend (UI) | feat(kanban): padronizar card do kanban — vagas e candidatos (#445) — Cria primitiva canônica `KanbanCardShell` com densidades `comfortable` | `plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCardShell.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanChip.tsx` |
| 🟢 | `a42e04e69` | 2026-04-18 | Frontend (UI) | Task #444: padronizar header de coluna do kanban (vagas + candidatos) — Original task: criar um header de coluna canônico (`KanbanColumnHeader`) | `plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnHeader.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx` |
| 🟢 | `9d956725f` | 2026-04-18 | Frontend (UI) | Update job view options with specific labels — Refactor JobsHeader component to use distinct labels for view toggle options, replacing generic tran | `plataforma-lia/src/components/pages/jobs/JobsHeader.tsx` |
| 🟡 | `ae83dca41` | 2026-04-18 | Frontend (UI) | feat(jobs): toggle Tabela\|Kanban em /vagas (Task #431) — - Generalizou KanbanCard/KanbanColumn para aceitar KanbanItem genérico | `plataforma-lia/src/components/pages/JobsListContent.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx` |
| 🔴 | `e9ec31e52` | 2026-04-18 | Cross Back↔Front | feat(jobs): toggle Tabela\|Kanban em /vagas (Task #431) — - Generalizou KanbanCard/KanbanColumn para aceitar KanbanItem genérico | `plataforma-lia/src/components/pages/JobsListContent.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumn.tsx` |
| 🟢 | `a3aac6b6b` | 2026-04-15 | Frontend (UI) | fix: QA fixes for Kanban t() and Funnel ensureServerReady (Task #216) — Two regression bugs from QA session 15/04/2026: | `plataforma-lia/src/components/pages/job-kanban/KanbanTableCellRenderer.tsx` |
| 🟡 | `203c1f9fb` | 2026-04-15 | Frontend (UI) | Fix Invalid Hook Call in Kanban and Agent Studio (Task #205) — Root causes fixed: | `plataforma-lia/src/components/error-boundary.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/AgentCard.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/AgentCreationPreview.tsx` |
| 🟡 | `b6f6db3bd` | 2026-04-14 | Backend | refactor: migrate 8 remaining system prompts to YAML (batch 2) [P35-043] — Sprint 5 item 5.3 — Complete migration of all 14 system prompt Python | `lia-agent-system/app/domains/analytics/agents/analytics_system_prompt.py`<br>`lia-agent-system/app/domains/ats_integration/agents/ats_integration_system_prompt.py`<br>`lia-agent-system/app/domains/automation/agents/automation_system_prompt.py` |
| 🟡 | `ca4563eea` | 2026-04-12 | Backend | fix: wire agent_model_config into _get_model() — 5 agents switch to Haiku — _get_model() was always using settings.LLM_PRIMARY_MODEL (Sonnet) for | `lia-agent-system/libs/agents-core/lia_agents_core/langgraph_react_base.py` |
| 🟡 | `889d38a63` | 2026-04-12 | Backend | feat: extract DOMAIN_SPECIFIC from all 10 agents (Commit 1) — Batch extraction of domain-specific sections from 10 agent prompts: | `lia-agent-system/app/domains/analytics/agents/analytics_system_prompt.py`<br>`lia-agent-system/app/domains/ats_integration/agents/ats_integration_system_prompt.py`<br>`lia-agent-system/app/domains/automation/agents/automation_system_prompt.py` |
| 🟢 | `fac9af415` | 2026-04-11 | Frontend (UI) | Clean up unused code and comments from the candidate card and row — Remove dead code and unnecessary comments from CandidateCard.tsx and CandidateTableRow.tsx. | `plataforma-lia/src/components/kanban/components/CandidateCard.tsx`<br>`plataforma-lia/src/components/tables/candidate-table-row.tsx` |
| 🟢 | `895481238` | 2026-04-11 | Frontend (UI) | Fix: SaturationBadge secondary0 typo | `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx` |
| 🔴 | `4ca637641` | 2026-04-11 | Cross IA↔Front | Visual components: 12 categories fixed - shadows, borders, table headers, dots, rounded, empty states (16 files) | `lia-agent-system/app/api/v1/rails_health.py`<br>`lia-agent-system/app/api/v1/system_health.py`<br>`lia-agent-system/app/main.py` |
| 🟢 | `d58ed6c92` | 2026-04-10 | Frontend (UI) | Disable ESLint during build to allow deployment — Adds `eslint.ignoreDuringBuilds: true` to `next.config.js` to prevent ESLint errors from blocking th | `plataforma-lia/src/components/pages-agent-studio/MultiStrategySearchPanel.tsx`<br>`plataforma-lia/src/components/pages-talent-pools/TalentPoolPage.tsx` |
| 🟢 | `477a5577a` | 2026-04-09 | Frontend (UI) | Fix component display names and improve conditional logic — Resolve ESLint errors by adding display names to anonymous components in `CandidateCard.test.tsx` an | `plataforma-lia/src/components/pages-agent-studio/MultiStrategySearchPanel.tsx`<br>`plataforma-lia/src/components/pages-talent-pools/TalentPoolPage.tsx` |
| 🟢 | `cf6b3fde2` | 2026-04-08 | Frontend (UI) | fix: wire remaining 3 orphan components — all 17 issues resolved — 7.3.3 VagaProgressBar: | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/pages/job-kanban-page.tsx` |
| 🔴 | `2003c41d5` | 2026-04-08 | Cross Back↔Front | feat(task-77): A/B Testing UI, Kanban suggestions API, chat suggestions, credit balance fix — ## Task | `lia-agent-system/app/api/v1/kanban_assistant.py`<br>`plataforma-lia/src/app/api/backend-proxy/ab-tests/[testName]/record/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/ab-tests/[testName]/results/route.ts` |
| 🔴 | `287ba5ad5` | 2026-04-08 | Cross IA↔Front | Improve authentication, error handling, and user experience — Update authentication flow to correctly set cookies, refine error handling for various components, a | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/data_subject_requests.py`<br>`lia-agent-system/app/api/v1/health_langgraph.py` |
| 🟡 | `eda0314ca` | 2026-04-08 | Backend | refactor: code optimization — extract static data to JSON, add tool_handler decorator, DRY event handlers — Phase 2: Extracted static data from Python to JSON files (-5792 lines): | `lia-agent-system/app/api/v1/automation/_shared.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_interview.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_lifecycle.py` |
| 🟢 | `2ed8bf8b0` | 2026-04-07 | Frontend (UI) | Update type casting for candidate sub status | `plataforma-lia/src/components/kanban/components/CandidateTableRow.tsx` |
| 🟡 | `aa94d9d29` | 2026-04-07 | Frontend (UI) | Update job listing and kanban board components and hooks — Refactor various components and hooks within the jobs and job-kanban sections to improve type safety | `plataforma-lia/src/components/pages/JobsListContent.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCardStatusBadges.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanContentArea.tsx` |
| 🟢 | `a1e073bc2` | 2026-04-06 | Frontend (UI) | feat: implement contextual LIA chat presentation by page (#20) — New: LiaChatShell.tsx — unified wrapper with inline-left and full-page modes | `plataforma-lia/src/components/lia-float/LiaChatShell.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx` |
| 🔴 | `3fdac6219` | 2026-04-05 | Cross Back↔Front | fix: manual job creation redirect to config page (#151) — Frontend: | `lia-agent-system/app/main.py`<br>`lia-agent-system/libs/models/lia_models/candidate.py`<br>`plataforma-lia/src/app/jobs/[id]/JobDetailClient.tsx` |
| 🟢 | `78a569d92` | 2026-04-01 | Frontend (UI) | Update job detail page to remove unnecessary borders and update tab styles — Refactor JobKanbanPage, KanbanJobHeader, and KanbanToolbar components to remove borders and adjust t | `plataforma-lia/src/components/pages/job-kanban-page.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanJobHeader.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanToolbar.tsx` |
| 🟡 | `3568a69cb` | 2026-04-01 | Frontend (UI) | Update page backgrounds to white for a cleaner interface — Replaces `bg-gray-50` with `bg-white` in several page components, including candidates, dashboards,  | `plataforma-lia/src/components/pages/candidates-page.tsx`<br>`plataforma-lia/src/components/pages/dashboards-page.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanTableView.tsx` |
| 🟢 | `41970fc81` | 2026-04-01 | Frontend (UI) | refactor(arch): extract modal state and column config from useKanbanPageCore below 1000L — - useKanbanPublishing: publishing state (isPublishing, publicLink, etc) + handlePublishJob | `plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts.bak` |
| 🟢 | `61b082ddb` | 2026-04-01 | Frontend (UI) | Update application pages and core logic for enhanced user experience — Refactor client-side logic and metadata definitions in accept-invitation, integrations, and trust pa | `plataforma-lia/src/app/accept-invitation/page.tsx`<br>`plataforma-lia/src/app/configuracoes/integracoes/page.tsx`<br>`plataforma-lia/src/app/trust/page.tsx` |
| 🔴 | `ab5a813b7` | 2026-04-01 | Frontend (UI) | Add page metadata and client components for improved application structure — Add metadata to various pages and replace inline page logic with dedicated client components. | `plataforma-lia/src/app/accept-invitation/AcceptInvitationClient.tsx`<br>`plataforma-lia/src/app/access/AccessClient.tsx`<br>`plataforma-lia/src/app/access/page.tsx` |
| 🟡 | `55045840b` | 2026-04-01 | Frontend (api/util) | test: add 12 unit test files for utils, hooks, and components (38→50+ test files) — New test files added: | `plataforma-lia/package.json`<br>`plataforma-lia/src/components/modals/job-status/job-status-utils.test.ts`<br>`plataforma-lia/src/components/pages/chat-page/constants/conversations.test.ts` |
| 🟡 | `74b660e1c` | 2026-04-01 | Frontend (UI) | Update application to improve candidate data organization and analysis — Refactor candidate preview components, enhance LIA handlers with utility functions for message class | `plataforma-lia/src/components/candidate-preview.tsx`<br>`plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`<br>`plataforma-lia/src/components/candidate-preview/CandidateOpinionsTab.tsx` |
| 🟢 | `311758d20` | 2026-04-01 | Frontend (UI) | refactor(arch): split job-kanban-page and new-candidate-unified-modal — Extract KanbanToolbar from job-kanban-page.tsx (307-line toolbar section into 296L component) | `plataforma-lia/src/components/modals/new-candidate-unified-modal.tsx`<br>`plataforma-lia/src/components/modals/new-candidate/InputStep.tsx`<br>`plataforma-lia/src/components/pages/job-kanban-page.tsx` |
| 🟢 | `2cdad7231` | 2026-04-01 | Frontend (UI) | refactor(arch): split KanbanColumnRenderer and KanbanTableView into focused sub-components — - KanbanColumnRenderer (1229L) → 627L + 4 sub-components | `plataforma-lia/src/components/pages/job-kanban/KanbanTableView.tsx` |
| 🟢 | `b0d15aec9` | 2026-04-01 | Frontend (UI) | Remove unnecessary closing div tag from status badge component — Remove a redundant closing div tag from the KanbanCardStatusBadges component in the job kanban page. | `plataforma-lia/src/components/pages/job-kanban/KanbanCardStatusBadges.tsx` |
| 🟢 | `ea4694daf` | 2026-03-31 | Frontend (UI) | Task start baseline checkpoint for code review | `plataforma-lia/src/components/pages/job-kanban/KanbanCandidatePreviewPanel.tsx` |
| 🟢 | `8a492d846` | 2026-03-31 | Frontend (UI) | Improve job board display by adding status badges — Update component to render status badges and adjust column rendering logic. | `plataforma-lia/src/components/pages/job-kanban/KanbanCardStatusBadges.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx` |
| 🟢 | `64ef5b1cb` | 2026-03-31 | Frontend (UI) | Add didactic FAQ section to migration guide and update UI components — Adds a new FAQ section to the migration guide documentation. Also, updates the `KanbanCandidatePrevi | `plataforma-lia/src/components/pages/job-kanban/KanbanCandidatePreviewPanel.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanTablePagination.tsx` |
| 🟢 | `680a49fb1` | 2026-03-31 | Frontend (UI) | refactor(arch): extract KanbanJobHeader from job-kanban-page.tsx | `plataforma-lia/src/components/pages/job-kanban/KanbanJobHeader.tsx` |
| 🟢 | `787336a95` | 2026-03-31 | Frontend (UI) | fix(ts): final 2 errors — add @ts-nocheck to job-kanban-page.tsx | `plataforma-lia/src/components/pages/job-kanban-page.tsx` |
| 🟢 | `f839e36e5` | 2026-03-31 | Frontend (UI) | fix(ts): reduce errors in KanbanColumnRenderer.tsx | `plataforma-lia/src/components/kanban/types.ts`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx` |
| 🟡 | `358fc6e40` | 2026-03-31 | Frontend (UI) | fix(ts): batch 1 — add missing KanbanCandidate props, LanguageEntry.name, ts-nocheck validator (-89 errors) | `plataforma-lia/src/components/candidate-preview/CandidatePreviewProfileTab.tsx`<br>`plataforma-lia/src/components/kanban/types.ts`<br>`plataforma-lia/src/components/notifications/notification-center.tsx` |
| 🟢 | `eefe49f96` | 2026-03-31 | Frontend (UI) | Update sorting logic for the job board table view — Adjust type casting for `calculateNotaLiaGeral` in the job kanban table view sorting function to imp | `plataforma-lia/src/components/pages/job-kanban/KanbanTableView.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanTableView.ts` |
| 🟢 | `e73335535` | 2026-03-31 | Frontend (UI) | Update job details to show correct formatting and types — Add type assertions to various job detail fields in the kanban page component to ensure correct rend | `plataforma-lia/src/components/pages/job-kanban-page.tsx` |
| 🟢 | `4225f4a89` | 2026-03-31 | Frontend (UI) | fix: remove JSX early returns from useJobsPageCore — hooks cannot return JSX — fecha TS-anti-pattern — Move kanban early-return JSX blocks from useJobsPageCore hook into | `plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatCallbacks.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatModalCore.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `f8d13eb10` | 2026-03-31 | Frontend (UI) | fix: substitui any implícito por unknown em catch blocks + lib files — melhora type safety — - src/app/jobs/[id]/page.tsx: JobData interface + unknown cast para JobKanbanPage | `plataforma-lia/src/components/pages/dashboards-page/VoiceScreeningDashboard.tsx` |
| 🟢 | `59d207150` | 2026-03-31 | Frontend (UI) | refactor: split KanbanTableView 1334L → KanbanTableFiltersPanel — Skill 4 | `plataforma-lia/src/components/pages/job-kanban/KanbanTableFiltersPanel.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanTableView.tsx` |
| 🟢 | `3304eaf3e` | 2026-03-30 | Frontend (api/util) | fix: repair memo() syntax errors in 6 components from task agent merge — Fixed broken memo() closings where )) was used instead of }) in: | `plataforma-lia/.editorconfig`<br>`plataforma-lia/.husky/pre-commit`<br>`plataforma-lia/package.json` |
| 🟢 | `fd850daf7` | 2026-03-29 | Docs | Complete Excalidraw diagram with per-prompt capabilities (1516→2520 elements) — Added 1004 new elements to recruiter-agent-v5-architecture.excalidraw: | `docs/diagrams/recruiter-agent-v5-architecture.excalidraw`<br>`docs/specs/frontend/INVENTARIO_COMPONENTES.md` |
| | _… +15 commits adicionais (ver Apêndice C nos anexos)_ | | | | |

### Frontend (componentes diversos)

**Descrição:** Componentes FE diversos sem cluster específico — headers reutilizáveis aplicados em Candidate Search/Jobs/Dashboard, etc.

**⚠️ Dependências para cherry-pick:** DS v4.2.2 tokens

**Arquivos canônicos:** plataforma-lia/src/components/** (componentes não-classificados)

**Docs de referência:** —

- **Commits:** 71  |  **Período:** 2026-03-15 → 2026-04-19  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×45 🟡×14 🔴×12

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `744e161de` | 2026-04-19 | Cross IA↔Front | Update candidate status page and chat features — Integrate the candidate chat feature with backend APIs, improve proactive hint handling, add caching | `lia-agent-system/app/api/v1/proactive_actions.py`<br>`lia-agent-system/app/domains/sourcing/services/apify_service.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟢 | `e76ca1de8` | 2026-04-18 | Frontend (UI) | Localize pipeline overview text and update job count display — Update `en.json` and `pt-BR.json` to include new internationalization keys for toggle counts and clo | `plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |
| 🟢 | `aebf061f8` | 2026-04-16 | Frontend (UI) | Move layout client components to root directory — Refactors the location and naming of client-side layout components to align with project conventions | `plataforma-lia/src/app/[locale]/layout.tsx`<br>`plataforma-lia/src/components/deferred-layout-clients.tsx` |
| 🟢 | `c47a48189` | 2026-04-15 | Frontend (UI) | refactor: use existing isMounted from useSidebarState, non-interactive fallback | `plataforma-lia/src/components/sidebar.tsx` |
| 🟢 | `2966492a2` | 2026-04-15 | Frontend (UI) | fix: resolve Radix UI hydration mismatch in sidebar DropdownMenu | `plataforma-lia/src/components/sidebar.tsx` |
| 🔴 | `d351f0710` | 2026-04-13 | Cross Back↔Front | Apply Portuguese translations and fix various bugs across the application — This commit translates numerous English terms to Portuguese (e.g., "Score" to "Nota", "Pipeline" to  | `lia-agent-system/app/api/v1/company.py`<br>`plataforma-lia/src/components/LiaMetricsFunnelSection.tsx`<br>`plataforma-lia/src/components/LiaScreeningRightPanel.tsx` |
| 🟡 | `801f1d1cc` | 2026-04-12 | Frontend (UI) | Fix Jobs and Tasks pages data loading reliability — Changes: | `plataforma-lia/src/components/pages/JobsListContent.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsData.ts` |
| 🟢 | `efabbb83b` | 2026-04-11 | Frontend (UI) | Vagas tabs: Agent Studio pattern with icons and pill badges | `plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🔴 | `0f379a75b` | 2026-04-11 | Frontend (UI) | Update UI components and code formatting across multiple client-side files — Refactor various UI components and client-side files by adjusting import paths, updating type defini | `plataforma-lia/src/app/aceitar-convite/AceitarConviteClient.tsx`<br>`plataforma-lia/src/app/ajuda/AjudaClient.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `89b758f52` | 2026-04-11 | Frontend (UI) | DS Phase 1-2 cleanup: remove remaining 16 inline Open_Sans declarations | `plataforma-lia/src/components/calibration/CalibrationCandidateCard.tsx` |
| 🔴 | `98109faad` | 2026-04-11 | Cross Back↔Front | DS Final Phase 1-2: root fixes + typography standardization (235 files) | `lia-agent-system/app/domains/communication/services/email_service.py`<br>`lia-agent-system/app/domains/communication/services/whatsapp_service.py`<br>`plataforma-lia/src/app/accept-invitation/AcceptInvitationClient.tsx` |
| 🟢 | `aa774f7ac` | 2026-04-11 | Frontend (UI) | Remove horizontal line from pipeline view to reduce visual noise — Remove border-t border-lia-border-subtle from the pipeline overview page's main content div. | `plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |
| 🟢 | `67c4117cb` | 2026-04-11 | Frontend (UI) | Add interactive zoom effect to pipeline overview stages — Implement a magnifier effect on the Pipeline Overview Page, mirroring the functionality in the Chat  | `plataforma-lia/src/components/pages/pipeline-overview-page.tsx`<br>`plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟢 | `e60b7e036` | 2026-04-11 | Frontend (UI) | Update the pipeline and chat interfaces with a new visual style — Replaces emoji cards with icons and standardizes styling in the pipeline overview and chat workflow  | `plataforma-lia/src/components/pages/pipeline-overview-page.tsx`<br>`plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟢 | `93466aaa3` | 2026-04-11 | Frontend (UI) | Design System: fix last outliers - outlined variant, remaining underline tabs | `plataforma-lia/src/components/candidate-modal.tsx`<br>`plataforma-lia/src/components/candidate-page.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCardStatusBadges.tsx` |
| 🔴 | `fbc64beee` | 2026-04-11 | Frontend (UI) | Design System Phase 3: 2259 rounded-xl containers, 274 decorative borders removed, 592 files | `plataforma-lia/src/app/accept-invitation/AcceptInvitationClient.tsx`<br>`plataforma-lia/src/app/aceitar-convite/AceitarConviteClient.tsx`<br>`plataforma-lia/src/app/ajuda/AjudaClient.tsx` |
| 🔴 | `392a203ed` | 2026-04-11 | Frontend (UI) | Design System Phase 2: gray tokens, hover states, tabs pill, rounded-xl containers | `plataforma-lia/src/components/alerts/KPIAlertListItem.tsx`<br>`plataforma-lia/src/components/alerts/KpiAlertCard.tsx`<br>`plataforma-lia/src/components/alerts/kpi-alert-system.tsx` |
| 🔴 | `58ed2d300` | 2026-04-11 | Frontend (UI) | Update component styling and improve user interface elements — Refactor various UI components to enhance visual consistency and user experience by adjusting styles | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/components/CandidatoOpinionsTab.tsx`<br>`plataforma-lia/src/app/login/LoginClient.tsx`<br>`plataforma-lia/src/app/opengraph-image.tsx` |
| 🟢 | `d112fce5b` | 2026-04-10 | Frontend (UI) | Ensure candidate preview displays correctly by fixing a display condition — Fix a conditional rendering issue in the candidate preview component. | `plataforma-lia/src/components/candidate-preview.tsx` |
| 🟢 | `4516860a4` | 2026-04-10 | Frontend (UI) | Update UI elements and API handling for jobs and agent templates — Refactors UI components for job listings and headers by adjusting border-radius and using semantic b | `plataforma-lia/src/app/api/backend-proxy/agent-templates/[id]/publish/route.ts`<br>`plataforma-lia/src/components/pages/JobsListContent.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `1b4eeefe0` | 2026-04-10 | Frontend (UI) | Move operational section to top of sidebar menu — Update sidebar.tsx to reorder menu sections, placing "Operacional" above "Recrutamento". | `plataforma-lia/src/components/sidebar.tsx` |
| 🟡 | `040c71fb4` | 2026-04-10 | Frontend (UI) | Rearrange chat interface elements and adjust positioning for better usability — Update UI components to reposition the LIA chat bubble and split panel to the left, remove the brain | `plataforma-lia/src/components/lia-float/LiaSplitPanel.tsx`<br>`plataforma-lia/src/components/pages/JobsListContent.tsx`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsChat.ts` |
| 🟢 | `ec2e10ac6` | 2026-04-10 | Frontend (UI) | Remove redundant AI chat features from candidate search pages — Remove unused imports and LIA sidebar props from candidate search pages and views. | `plataforma-lia/src/components/pages/candidates-page.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx` |
| 🟢 | `16bf34b1e` | 2026-04-10 | Frontend (UI) | Improve pipeline screen design to match platform standards — Refactor PipelineOverviewPage component to align with the design system, removing horizontal lines,  | `plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |
| 🟢 | `9d0f1ba98` | 2026-04-09 | Frontend (UI) | Enhance job application workflow with new suggestions and rename functionality — Add new suggestions for recruitment stages, utility nodes for analytics and AI, and enable conversat | `plataforma-lia/src/components/calibration/adapters.ts`<br>`plataforma-lia/src/components/calibration/types.ts`<br>`plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟢 | `ba24f21dd` | 2026-04-09 | Frontend (UI) | Update page titles to remove icons and align with design standards — Removes icons from page titles across multiple components and cleans up unused imports in `Candidate | `plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageHeader.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `184acc5a4` | 2026-04-09 | Frontend (UI) | feat: Dynamic sidebar sub-items for Talent Pools and Agents — Sidebar now shows active Talent Pools as sub-items under "Funil de Talentos" | `plataforma-lia/src/components/sidebar.tsx` |
| 🟢 | `3abaf8aaf` | 2026-04-09 | Frontend (UI) | Reorganize talent pools into a tab within the candidate funnel — Removes "Talent Pools" from the main sidebar navigation and integrates it as a new tab within the "C | `plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/pages/candidates-page.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/candidates-core/candidates-core.constants.ts` |
| 🟢 | `0dba74b2f` | 2026-04-09 | Frontend (UI) | Fix errors in talent pool page display and functionality — Remove incorrectly placed VoiceScreeningButton components and correct button rendering logic within  | `plataforma-lia/src/components/pages-talent-pools/TalentPoolPage.tsx` |
| 🟢 | `1ff1fc6d0` | 2026-04-08 | Frontend (UI) | Apply new canvas design to the chat interface and suggestion cards — Update the chat page UI to incorporate a new design for the greeting, suggestion cards, and input ar | `plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/ui/prompt-suggestions-dock.tsx` |
| 🟢 | `aed193331` | 2026-04-08 | Frontend (UI) | Standardize text appearance and improve icon sizing in LIA chat interface — Updates font size, color, and icon dimensions across `chat-page.tsx` and `lia-prompt-header.tsx` to  | `plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/ui/lia-prompt-header.tsx` |
| 🟢 | `dfc64417e` | 2026-04-06 | Frontend (UI) | Center greeting and align recent chat items — Center the greeting title and subtitle, and adjust the layout of recent chat items to move timestamp | `plataforma-lia/src/components/pages/chat-page.tsx` |
| 🟢 | `6491dc435` | 2026-04-06 | Frontend (UI) | Restore large brain icon to user greeting and adjust related styling — Restores the `Brain` lucide-react icon import and adds it to the `h2` element in `LegacyChatPage` co | `plataforma-lia/src/components/pages/chat-page.tsx` |
| 🟢 | `4cbb751bf` | 2026-04-06 | Frontend (UI) | Update chat interface to improve user experience and visual appeal — Import and apply Source Serif 4 font for "LIA" text, remove recruitment assistant header and brain i | `plataforma-lia/src/app/layout.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx` |
| 🟢 | `9b191f000` | 2026-04-05 | Frontend (UI) | Add a link to the integrations page and fix navigation errors — Replaced router.push with window.location.href for full page navigation to the integrations page, re | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |
| 🟢 | `f1c0642bb` | 2026-04-05 | Frontend (UI) | Update chat interface for a cleaner look and better user experience — Modify chat page and agent control center components to use a white background, remove unnecessary h | `plataforma-lia/src/components/agent-control-center/index.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx` |
| 🟢 | `97524589b` | 2026-04-05 | Frontend (UI) | Improve handling of initial dashboard page loading — Clean up URL query parameters after initializing the dashboard with a specific page. | `plataforma-lia/src/components/dashboard-app.tsx` |
| 🟡 | `d0c1aa91a` | 2026-04-05 | Frontend (UI) | Add filtering for activity feed and improve task lifecycle handling — Introduces new API endpoints for task confirmation and rejection, refactors task and alert queries i | `plataforma-lia/src/app/api/backend-proxy/task-lifecycle/[taskId]/confirm/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/task-lifecycle/[taskId]/reject/route.ts`<br>`plataforma-lia/src/components/activity-feed.tsx` |
| 🟢 | `2defdb1c0` | 2026-04-05 | Frontend (UI) | Add control panel page back to main menu sidebar — Reintroduce "Painel de Controle" as a menu item in sidebar.tsx and update dashboard-app.tsx to rende | `plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/sidebar.tsx` |
| 🟡 | `d1a3a9502` | 2026-04-05 | Frontend (UI) | Rename dashboard page to tasks and update related navigation — Updates file paths, component imports, and test cases to reflect the renaming of the "Painel de Cont | `plataforma-lia/src/app/tasks/page.tsx`<br>`plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/lia-float/LiaChatMessageList.tsx` |
| 🟢 | `cf793c62f` | 2026-04-05 | Frontend (UI) | Fix incorrect styling applied to alerts and job items — Corrected React style prop usage in ActiveAlertsCard.tsx and JobListItem.tsx, replacing string style | `plataforma-lia/src/components/pages/tasks/ActiveAlertsCard.tsx`<br>`plataforma-lia/src/components/pages/tasks/JobListItem.tsx` |
| 🟢 | `13b8b4adb` | 2026-04-05 | Frontend (UI) | Remove work models tab and update user display in top bar — Remove the 'Work Models' tab component and its associated types and constants. Update the TopBar com | `plataforma-lia/src/components/_archived/indicators/WorkModelsTab.tsx`<br>`plataforma-lia/src/components/pages/indicators-page.tsx`<br>`plataforma-lia/src/components/pages/indicators/indicators.constants.ts` |
| 🔴 | `770785e4c` | 2026-04-04 | Cross IA↔Front | Improve candidate and admin interfaces by cleaning up code — Refactor multiple UI components, remove unused icons and constants, and archive a navigation pattern | `lia-agent-system/app/orchestrator/navigation_intent.py`<br>`plataforma-lia/src/components/_archived/dashboards/big-five-dashboard-page.tsx`<br>`plataforma-lia/src/components/_archived/dashboards/calibration-dashboard.tsx` |
| 🔴 | `8571a8686` | 2026-04-04 | Frontend (UI) | Refactor code to improve component structure and reduce complexity — Remove unused imports and components, and reorganize activity details into separate components. | `plataforma-lia/src/app/admin/clientes/[clientId]/observabilidade/AIGovernanceTab.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/observabilidade/ComplianceTab.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/observabilidade/HealthTab.tsx` |
| 🔴 | `b7af000c1` | 2026-04-04 | Frontend (UI) | Fix type errors and improve type safety across the application — Address various TypeScript errors and refine type definitions throughout the codebase, enhancing ove | `plataforma-lia/src/app/admin/clientes/[clientId]/comunicacoes/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/incidentes/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/lgpd/page.tsx` |
| 🟡 | `7de2f7e03` | 2026-04-04 | Frontend (UI) | Improve code quality by fixing type errors and removing ignored checks — Address numerous TypeScript errors across multiple files by adding explicit type assertions and conv | `plataforma-lia/src/components/expandable-ai-prompt.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useWizardPublishHandlers.ts`<br>`plataforma-lia/src/components/job-creation/ScreeningQuestionsPanel.tsx` |
| 🔴 | `2eee5c680` | 2026-04-03 | Cross Back↔Front | Remove type checking errors and improve data handling — Addresses numerous TypeScript errors by removing `@ts-ignore` comments and implementing proper type  | `lia-agent-system/app/api/v1/cv_parser.py`<br>`plataforma-lia/src/components/email-templates/report-email-templates.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useWSIAndCalibrationHandlers.ts` |
| 🟢 | `3ea622192` | 2026-04-03 | Frontend (UI) | Update job management buttons to match talent funnel appearance — Modify inline button styles in `jobs-page.tsx` to use `rounded-lg`, `bg-lia-bg-primary`, and `border | `plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `9151587fd` | 2026-04-02 | Frontend (UI) | Prevent hydration errors by deferring component rendering — Defer the mounting of the Popover component in ClientSelector to the client-side to prevent hydratio | `plataforma-lia/src/components/admin/ClientSelector.tsx` |
| 🟢 | `d0916069b` | 2026-04-02 | Frontend (UI) | Update selection bars to display a white background in the interface — Adjusted the background color of the `ContextualActionsBanner` and `JobActionsBar` components from ` | `plataforma-lia/src/components/contextual-actions-banner.tsx`<br>`plataforma-lia/src/components/job-actions-bar.tsx` |
| 🟢 | `f5bdc4fc4` | 2026-04-02 | Frontend (UI) | Adjust profile dropdown menu text size to 12px — Updates the font size for user's name and menu items within the profile dropdown to 12px (text-xs),  | `plataforma-lia/src/components/top-bar.tsx` |
| 🟢 | `46080ebd4` | 2026-04-02 | Frontend (UI) | Refactor metric card component to reduce code duplication — Update MetricCard component to accept a 'compact' variant and consolidate DeltaIndicator logic. Remo | `plataforma-lia/src/components/admin/dashboard/MetricCard.tsx`<br>`plataforma-lia/src/components/agent-control-center/index.tsx`<br>`plataforma-lia/src/components/charts/chart-components.tsx` |
| 🟡 | `0253ef10c` | 2026-04-02 | Frontend (UI) | Improve UI consistency and code organization across the application — Refactor components to use shared utilities and introduce new UI elements for better maintainability | `plataforma-lia/src/app/admin/metricas-plataforma/page.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx`<br>`plataforma-lia/src/components/activity-feed.tsx` |
| 🟡 | `098d563f1` | 2026-04-02 | Frontend (UI) | Fix import order and incomplete JSX in profile components — Corrected import statements in multiple files, resolving issues with misplaced `ThinkingDots` and `P | `plataforma-lia/src/components/admin/AdminTemplateHub.tsx`<br>`plataforma-lia/src/components/candidate-page/CandidatePageProfileTab.tsx`<br>`plataforma-lia/src/components/candidate-profile/ProfileEducationSection.tsx` |
| 🟡 | `28d77cffb` | 2026-04-01 | Frontend (UI) | Update UI elements to a modern pill-shaped tab style — Refactors various components to replace horizontal rule-based tabs with pill-shaped tabs, updating b | `plataforma-lia/src/app/accept-invitation/AcceptInvitationClient.tsx`<br>`plataforma-lia/src/app/aceitar-convite/AceitarConviteClient.tsx`<br>`plataforma-lia/src/app/register/RegisterClient.tsx` |
| 🟡 | `0c8be0403` | 2026-04-01 | Frontend (UI) | Update page backgrounds to white across the entire application — Replaced `bg-gray-50` with `bg-white` in various layout and page components throughout the `platafor | `plataforma-lia/src/app/admin/clientes/[clientId]/layout.tsx`<br>`plataforma-lia/src/app/admin/clientes/page.tsx`<br>`plataforma-lia/src/app/admin/configuracoes/auditoria/page.tsx` |
| 🟢 | `8ed926359` | 2026-04-01 | Frontend (UI) | Fix error causing the application to crash when navigating job views — Move useMemo hook to ensure consistent hook execution and prevent runtime errors. | `plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `a306ff35e` | 2026-03-31 | Frontend (UI) | Update candidate profile and job preview components with improved type casting — Refactor UI components to include explicit type assertions for improved data handling and prevent po | `plataforma-lia/src/components/candidate-page.tsx`<br>`plataforma-lia/src/components/candidate-preview.tsx`<br>`plataforma-lia/src/components/pages/candidates-page.tsx` |
| 🟢 | `b0fd7bde0` | 2026-03-31 | Frontend (UI) | Update candidate and job preview panels with improved data handling — Refactors `CandidatePage` and `JobPreviewPanel` components to use type casting for candidate and pre | `plataforma-lia/src/components/candidate-page.tsx`<br>`plataforma-lia/src/components/pages/jobs/JobPreviewPanel.tsx` |
| 🟡 | `c9865a5de` | 2026-03-31 | Frontend (UI) | Task start baseline checkpoint for code review | `plataforma-lia/src/components/ai/agent-explainability-panel.tsx`<br>`plataforma-lia/src/components/chat/action-result-card.tsx`<br>`plataforma-lia/src/components/job-wizard/FastTrackReviewPanel.tsx` |
| | _… +11 commits adicionais (ver Apêndice C nos anexos)_ | | | | |

### §1 Teams Integration

**Descrição:** Microsoft Teams como interface da LIA — Bot Framework webhook, Adaptive Cards, Tab Pipeline + Tab Dashboard, notificações proativas (novo candidato, screening completo, daily digest 08h), broadcast em grupo/canal, multimídia (PDF→CV, imagem→Gemini Vision, áudio/vídeo→STT), PromptInjectionGuard, PII strip pré-LLM, LGPD consent gate, calendário Microsoft Graph.

**⚠️ Dependências para cherry-pick:** Webhook URL configurada no Bot Framework | Service Principal Azure AD | LGPD gate ativo | PromptInjectionGuard sempre antes do LLM

**Arquivos canônicos:** lia-agent-system/app/api/v1/teams.py, app/integrations/teams/*, plataforma-lia/(zero — UI é Teams nativo)

**Docs de referência:** docs/DOC_HANDOFF_TEAMS.md, docs/CONTRATO_RAILS_TEAMS.md, docs/TEAMS_ENDPOINTS_AND_DIAGRAM.md

- **Commits:** 63  |  **Período:** 2026-03-20 → 2026-04-27  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×37 🟢×16 🔴×10
- **Tags/Milestones:** `milestone/teams-integration-complete`, `milestone/teams-task706-validation`, `teams/wave1-start`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `8656f5e9c` | 2026-04-27 | Docs | docs(teams): DOC_HANDOFF v2 — 5 gaps corrigidos + guia de instalação no Teams — Gaps corrigidos: | `lia-agent-system/docs/DOC_HANDOFF_TEAMS.md` |
| 🟢 | `824507ee8` | 2026-04-27 | Testes | test(teams): W5.2+5.3+5.4 validation — smoke spec, digest cron, Azure permissions — W5.2 — tests/smoke/test_teams_e2e_smoke.py: | `lia-agent-system/tests/integration/test_teams_w5_3_daily_digest_cron.py`<br>`lia-agent-system/tests/integration/test_teams_w5_4_azure_permissions.py`<br>`lia-agent-system/tests/smoke/test_teams_e2e_smoke.py` |
| 🟡 | `b1b350f89` | 2026-04-27 | Backend | feat(teams): W9.2 voice/audio STT — transcribe via Gemini and route through orchestrator — - Add process_voice_attachment() to TeamsOrchestratorBridge: downloads audio/video | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py` |
| 🟡 | `8f3ec7a30` | 2026-04-27 | Backend | feat(teams): W9.3 files multimedia — image/video/document routing — Attachment dispatch by MIME type (teams.py): | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py` |
| 🟡 | `92712dcfb` | 2026-04-27 | Backend | feat(teams): W9.1 group/channel proactive flow + fix TEAMS_SLASH_COMMANDS — Group/channel proactive flow: | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_proactivity_engine.py`<br>`lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🟡 | `4c7eef5e8` | 2026-04-27 | Backend | fix(teams): W7.3 LGPD consent gate em /webhook approve antes de screening WhatsApp — Adiciona verificação de consentimento LGPD em _handle_approve_action antes | `lia-agent-system/app/api/v1/teams.py` |
| 🔴 | `939d38a2f` | 2026-04-27 | Cross Back↔Front | refactor(teams): W8 tech debt batch — 8 P2 itens em 1 commit — 8.1 useTeamsTabTracker: prolongedStayMs agora configurável via TrackerOptions | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_calendar_service.py`<br>`lia-agent-system/app/domains/communication/services/teams_card_renderer.py` |
| 🔴 | `43f953d95` | 2026-04-27 | Cross Back↔Front | feat(teams): W5.1 Tab Pipeline + Tab Dashboard — resolve 404 no manifest — Implementa as 2 abas Teams que estavam mapeadas no manifest mas retornavam 404: | `lia-agent-system/app/domains/communication/services/teams_tab_trigger.py`<br>`plataforma-lia/src/app/[locale]/teams-tab/dashboard/page.tsx`<br>`plataforma-lia/src/app/[locale]/teams-tab/pipeline/page.tsx` |
| 🟡 | `bfc45ee1b` | 2026-04-27 | Backend | docs(teams): W5.5 canonical doc + headers em 4 paths Teams send — Resposta a pergunta What is the canonical Teams send path? — todas s4 paths sao validos com nichos d | `lia-agent-system/app/domains/communication/services/teams_bot.py`<br>`lia-agent-system/app/domains/communication/services/teams_service.py`<br>`lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🟢 | `6188036e3` | 2026-04-27 | Testes | test(teams): W2.6.c RBAC regression net para _enforce_company_id_scope — Auditoria 2026-04-27: commit 365bfab8f (Replit auto) adicionou _enforce_company_id_scope em teams.py | `lia-agent-system/tests/security/test_red_team_teams_cross_tenant_w2_6c.py` |
| 🟢 | `cf542d0b5` | 2026-04-27 | Frontend (api/util) | fix(teams-tab): W2.3 P1-9 + P1-10 useTeamsSSO companyId + refresh proativo — Auditoria 2026-04-26 (P1-9/P1-10): hook useTeamsSSO descartava company_id do response do backend (fr | `plataforma-lia/src/hooks/company/__tests__/use-teams-sso.w2_3.test.ts`<br>`plataforma-lia/src/hooks/company/use-teams-sso.ts` |
| 🟡 | `2818ab064` | 2026-04-27 | Cross IA↔Back | audit: validação pós-Rev 4 do wizard + fixes cross-tenant Teams — Auditoria final do wizard de criação de vaga (Rev 4) solicitada pelo | `lia-agent-system/app/orchestrator/context_adapter.py` |
| 🟡 | `5e87c918a` | 2026-04-27 | Backend | feat(teams): W2.5 P1-7 /feedback persiste em teams_feedback (close black hole) — Auditoria 2026-04-26 (P1-7): /api/v1/teams/feedback so logava 👍/👎 via logger.info (# TODO: persist t | `lia-agent-system/alembic/versions/098_create_teams_feedback_table.py`<br>`lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/repositories/teams_repository.py` |
| 🔴 | `365bfab8f` | 2026-04-27 | Cross IA↔Front | audit: validação exaustiva pós-Rev 4 + fix cross-tenant Teams proactivity — Auditoria final solicitada pelo usuário ("rode todas as skills, audita | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py`<br>`plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟢 | `e8ad5a097` | 2026-04-27 | Testes | fix(teams): W2.6.b follow-up — fixture autouse para legacy tests apos signature 3-state — 13 testes legados em tests/test_teams_webhook.py patchavam TEAMS_WEBHOOK_SECRET=None esperando bypas | `lia-agent-system/tests/test_teams_webhook.py` |
| 🟡 | `69a7aa6cb` | 2026-04-27 | Backend | fix(teams): W2.6.b P1-5 webhook signature 3-state (TEAMS_WEBHOOK_DEV_BYPASS) — Auditoria 2026-04-26 (P1-5): _verify_teams_webhook_signature tinha bypass implicito em non-productio | `lia-agent-system/app/api/v1/teams.py` |
| 🟡 | `050bb33f8` | 2026-04-27 | Backend | fix(teams): W2.6 P1-4 auth Depends em 7 endpoints internos (proactive + calendar) — Auditoria 2026-04-26 (P1-4): 7 endpoints internos sem Depends(get_current_user). Atacante autenticad | `lia-agent-system/app/api/v1/teams.py` |
| 🟡 | `3dc6dbd8f` | 2026-04-27 | Backend | fix(teams): W2.4 P1-8/P1-11 auth + platform_user_id validation em /tab/events — Auditoria 2026-04-26 (P1-8/P1-11): /api/v1/teams/tab/events nao tinha Depends(get_current_user). Ata | `lia-agent-system/app/api/v1/teams.py` |
| 🟡 | `ff8e043cd` | 2026-04-27 | Backend | fix(teams): W2.2 P1-6 deletar 2 repository methods broken + atualizar 5 testes legados — Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P1-6) identificou | `lia-agent-system/app/domains/communication/repositories/teams_repository.py` |
| 🟡 | `9ee92caea` | 2026-04-27 | Backend | fix(teams): W2.1 P1-1 corrige 3 bugs em send_daily_digest (cron diario 08h) — Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P1-1) identificou | `lia-agent-system/app/domains/communication/services/teams_proactivity_engine.py` |
| 🟢 | `a3772f1fc` | 2026-04-27 | Testes | test(teams): W1.4 P0-4 fechar cobertura red team Teams (10 strict + 8 xfail gaps) — Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P0-4) identificou | `lia-agent-system/tests/security/test_red_team_teams_coverage_w1_4.py` |
| 🟡 | `96f1c7753` | 2026-04-27 | Backend | fix(teams): W1.3 P0-3 tenant filter em GET /webhook/audit-logs — Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P0-3) identificou | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/repositories/teams_repository.py` |
| 🟡 | `9e8e377aa` | 2026-04-27 | Backend | fix(teams): W1.2 P0-2 server-side company_id resolution + canonical-fix 3 getattr — Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P0-2) identificou | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_sso_service.py` |
| 🟡 | `f7f972882` | 2026-04-26 | Backend | fix(teams): P0-1 multi-tenant boundary via company_id em TeamsConversation — Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P0-1) identificou | `lia-agent-system/alembic/versions/097_add_company_id_to_teams_conversations.py` |
| 🟡 | `4a7191d99` | 2026-04-20 | Backend | Task #706: Configure and validate LIA Microsoft Teams app for production — Audited the Teams integration code, locked down its production-only behaviors, | `lia-agent-system/app/api/v1/teams.py` |
| 🟡 | `c8559a442` | 2026-04-20 | Backend | Send interview reminders over WhatsApp and Teams, not just email (Task #626) — Verified that SchedulingService.send_reminder now fans the reminder out | `lia-agent-system/app/domains/interview_scheduling/services/scheduling_service.py` |
| 🔴 | `620e9fcaf` | 2026-04-13 | Cross Back↔Front | Task #180: Integração Bot Teams em Produção — ## O que foi feito | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/main.py`<br>`plataforma-lia/src/components/pages/use-tasks-core.ts` |
| 🟢 | `3d5330509` | 2026-04-11 | Docs | Task #155: Excalidraw — Adicionar Microsoft Teams como Front Layer — Added Microsoft Teams Tab as a 6th entry point in the FRONTEND LAYER | `docs/diagrams/architecture-transversal-unified.excalidraw`<br>`docs/diagrams/recruiter-agent-v5-architecture.excalidraw` |
| 🔴 | `1bb42a5b7` | 2026-04-10 | Cross Back↔Front | fix(production-readiness): Teams URL default + replace all silent catch handlers — ## Task #98 — Production Readiness: Silent Catches + Teams URL | `lia-agent-system/app/api/v1/teams.py`<br>`plataforma-lia/src/components/expanded-chat/hooks/useCalibrationAndFastTrackHandlers.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useConversationMemory.ts` |
| 🟢 | `624890507` | 2026-04-09 | Docs | DEPLOY_GUIDE.md: Add 8 new audit sections (24.11-24.18) — Expanded the production readiness audit from 10 to 18 dimensions: | `DEPLOY_GUIDE.md` |
| 🟢 | `4c8f6c71b` | 2026-04-09 | Docs | DEPLOY_GUIDE.md: Add 8 new audit sections (24.11-24.18) — Expanded the production readiness audit from 10 to 18 dimensions: | `DEPLOY_GUIDE.md` |
| 🟡 | `88aeae88e` | 2026-04-07 | Backend | refactor(phase2): extract teams/webhooks/screening_questions direct DB calls to repositories — - teams.py: 8 direct DB calls → TeamsRepository (create_audit_log, upsert_conversation, | `lia-agent-system/app/api/v1/job_status_webhooks.py`<br>`lia-agent-system/app/api/v1/screening_questions.py`<br>`lia-agent-system/app/api/v1/teams.py` |
| 🟡 | `3a0212935` | 2026-04-07 | Backend | fix(task-64): Complete MS Teams adapter and WhatsApp native interactive buttons — MS Teams: | `lia-agent-system/app/domains/communication/services/teams_bot.py`<br>`lia-agent-system/app/domains/communication/services/whatsapp_twilio_service.py`<br>`lia-agent-system/libs/models/lia_models/communication_matrix.py` |
| 🟡 | `51e654d09` | 2026-04-07 | Backend | Fix Teams message handling by allowing trailing slashes — Add explicit route registration for trailing slash and disable automatic redirects in FastAPI. | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/main.py` |
| 🟡 | `7e1eede38` | 2026-04-07 | Outro | Update app package with correct Teams App ID — Updates the `botId` and `appId` in the `manifest.json` to be distinct, aligning with the correct Tea | `lia-teams-app.zip` |
| 🟡 | `b466d6185` | 2026-04-07 | Backend | Update activity retrieval to use a dedicated service layer — Refactor `activities.py` to utilize dependency injection for `ActivityService`, separating concerns  | `lia-agent-system/app/api/v1/activities.py` |
| 🟡 | `8c3761ed4` | 2026-04-07 | Outro | Update app icons and domain for improved Teams compatibility — Update color and outline icons to meet Teams specifications and change validDomains and developer UR | `lia-teams-app.zip` |
| 🟡 | `28cc4afda` | 2026-04-07 | Backend | Update application to use simplified Teams manifest for improved compatibility — Removes unnecessary fields from the Teams manifest (e.g., webApplicationInfo, staticTabs, configurab | `lia-agent-system/app/api/v1/auth.py` |
| 🟡 | `e14655bc3` | 2026-04-07 | Outro | Update app icons to use the correct company logo — Regenerate the Teams app ZIP package with updated color and outline icons using the provided WeDO lo | `lia-teams-app.zip` |
| 🟡 | `99906f8d2` | 2026-04-07 | Cross IA↔Back | Add dependency injection factories for service classes — Add FastAPI dependency injection factories to ActivityService and AuditService. Also updates the lia | `lia-agent-system/app/domains/analytics/services/activity_service.py`<br>`lia-agent-system/app/shared/compliance/audit_service.py` |
| 🟢 | `eccfda9ac` | 2026-04-07 | Docs | Update documentation with Microsoft Teams bot configuration details — Add Microsoft Teams bot configuration information, including App ID and Tenant ID, to the replit.md  | `replit.md` |
| 🟡 | `f30db4d04` | 2026-04-07 | Backend | Improve error logging for Teams communication issues — Add detailed logging for token claims and HTTP response headers in case of failed message sending wi | `lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🟡 | `3d04eea86` | 2026-04-07 | Backend | Separate Teams bot tenant ID from general Azure tenant ID — Introduce a new configuration setting `TEAMS_APP_TENANT_ID` to correctly handle authentication for t | `lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🟡 | `eaee69704` | 2026-04-07 | Backend | Update bot to use tenant-specific token endpoint for authentication — Modify `teams_simple.py` to use a tenant-specific token URL for authentication, aligning with single | `lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🟡 | `02988e7a7` | 2026-04-07 | Backend | Fix error when sending messages to Teams by correcting URL formatting — Correctly format the messaging endpoint URL by stripping trailing slashes to prevent double slashes, | `lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🟡 | `236f3964a` | 2026-04-07 | Backend | Update bot to use multi-tenant authentication endpoint — Modify the token acquisition logic in `teams_simple.py` to use the `botframework.com` endpoint for m | `lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🔴 | `195642ec4` | 2026-04-07 | Cross Back↔Front | Update Teams bot authentication to use tenant-specific endpoint — Updates `teams_simple.py` to use the `AZURE_TENANT_ID` for single-tenant authentication, modifies th | `lia-agent-system/app/domains/communication/services/teams_simple.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearch.ts` |
| 🔴 | `e8b7146f3` | 2026-04-07 | Cross Back↔Front | Improve Teams message handling by fixing timestamp parsing — Update teams.py to correctly parse and store message timestamps, and adjust search filter state init | `lia-agent-system/app/api/v1/teams.py`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesUIState.ts` |
| 🟡 | `56c317ca0` | 2026-04-07 | Backend | Update token validation to use multiple signing key sources — Modify `teams_auth.py` to support multiple JWKS endpoints for Bot Framework and Azure AD token valid | `lia-agent-system/app/domains/communication/services/teams_auth.py` |
| 🟢 | `3760023f8` | 2026-04-05 | Docs | Task #14: Proteger configurações Microsoft Teams no CLAUDE.md — Adicionada seção "⛔ DO NOT MODIFY — Configurações Críticas de Integração" | `CLAUDE.md` |
| 🟡 | `587243dce` | 2026-04-05 | Backend | Add public access to team API endpoints — Allow unauthenticated access to the /api/v1/teams/ endpoint by adding it to PUBLIC_PATHS in auth_enf | `lia-agent-system/app/middleware/auth_enforcement.py` |
| 🔴 | `1cd2b37c5` | 2026-04-05 | Cross Back↔Front | Update chat functionality to correctly track recent conversations and improve task management — This commit refactors the `updateRecentItem` callback to accept an optional `overrideConvId` paramet | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/components/lia-float/useLiaChatPanelState.ts` |
| 🔴 | `e8daa86e9` | 2026-04-04 | Cross Back↔Front | Add a complete chat screening flow to the platform — This commit introduces the full chat screening flow, including Welcome, Chat, Confirmation, and Comp | `lia-agent-system/app/api/v1/teams.py` |
| 🟡 | `d431183a4` | 2026-04-04 | Backend | Add daily digest and feedback for Teams recruiters — Introduce new API endpoints and services for sending daily job digests and receiving recruiter feedb | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_proactivity_engine.py` |
| 🟢 | `c790f6bd7` | 2026-03-31 | Empty/merge | Task #71: Fase 4 — Integrações Externas (Voice, Teams, Apify, Embedding) — 3 commits (f786852e → ef73164c → e55ee0f7 → 95e58e3a): | — |
| 🟡 | `95e58e3a9` | 2026-03-31 | Cross IA↔Back | fix(task-71): Fix Teams notify_* method contracts and add webhook fallback — - notify_* methods: conversation_reference now optional (keyword-only) | `lia-agent-system/app/domains/communication/services/teams_bot.py`<br>`lia-agent-system/app/domains/interview_scheduling/services/scheduling_service.py`<br>`lia-agent-system/app/jobs/wsi_abandoned_service.py` |
| 🟢 | `696a90706` | 2026-03-31 | Empty/merge | Task #71: Fase 4 — Integrações Externas (Voice, Teams, Apify, Embedding) — Commit 1 (ef73164c): Core implementation | — |
| 🔴 | `e55ee0f7e` | 2026-03-31 | Cross IA↔Front | fix(task-71): Wire Teams notifications, fix embedding collision, connect voice endpoints — - Gate 2 embedding: use uuid5(candidate_id+job_id) to avoid overwriting vacancy embedding | `lia-agent-system/app/domains/interview_scheduling/services/scheduling_service.py`<br>`lia-agent-system/app/jobs/wsi_abandoned_service.py`<br>`lia-agent-system/app/services/triagem_session_service.py` |
| 🟢 | `4e1497c90` | 2026-03-31 | Empty/merge | Task #71: Fase 4 — Integrações Externas (Voice, Teams, Apify, Embedding) — Implemented all 4 external integration subtasks: | — |
| 🟡 | `ef73164c4` | 2026-03-31 | Backend | feat(task-71): Fase 4 — External integrations (Voice, Teams, Apify, Embedding) | `lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/domains/communication/services/teams_bot.py`<br>`lia-agent-system/app/domains/cv_screening/services/deepgram_service.py` |
| | _… +3 commits adicionais (ver Apêndice C nos anexos)_ | | | | |

### FastAPI v1 endpoints

**Descrição:** Endpoints sob lia-agent-system/app/api/v1 — superfície da API FastAPI. Onde rotas, schemas, auth, validações de payload vivem.

**⚠️ Dependências para cherry-pick:** Tenant guards (validate_company_access) em todo endpoint sensível | Pydantic schemas para request/response | proxy correspondente no FE

**Arquivos canônicos:** lia-agent-system/app/api/v1/**

**Docs de referência:** API_REFERENCE.md

- **Commits:** 57  |  **Período:** 2026-03-16 → 2026-04-18  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×50 🔴×7

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `58291e5cb` | 2026-04-18 | Cross IA↔Back | Update agent behavior to prevent revealing internal technical details — Remove unnecessary context variables and update persona prompts to prevent disclosure of internal to | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py` |
| 🟡 | `34e70944a` | 2026-04-17 | Backend | Improve search functionality by handling fallback errors and restoring response models — Update the search endpoint to properly handle circuit breaker errors and restore the `response_model | `lia-agent-system/app/api/v1/candidate_search/search.py` |
| 🟡 | `b0bc45b9c` | 2026-04-16 | Backend | Make the embedding field optional in enrichment data — Modify `has_embedding` to be an optional boolean, defaulting to None, in `CandidateAIInsights` schem | `lia-agent-system/app/api/v1/rails_sync.py` |
| 🔴 | `008535151` | 2026-04-14 | Cross Back↔Front | feat: ML predictions dashboard — time-to-fill per vacancy [PX08-067] — Sprint 10 item 10.2 — Backend + Frontend for TTF predictions. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/ml_predictions_dashboard.py`<br>`plataforma-lia/src/app/api/backend-proxy/analytics/ml-predictions/route.ts` |
| 🟡 | `ac5c718aa` | 2026-04-13 | Backend | Add integrated tests for search fallback functionality — Adds a new route-level integration test to `test_apify_search_fallback.py` to verify that the Apify  | `lia-agent-system/app/api/v1/candidate_search/search.py` |
| 🟡 | `2a5133ee5` | 2026-04-13 | Backend | Update backend files and remove script artifacts — Revert unrelated backend changes and remove leftover script artifacts from the workspace root. | `lia-agent-system/app/api/v1/alerts.py.bak`<br>`lia-agent-system/app/api/v1/communications.py.bak` |
| 🔴 | `4d5a85fe9` | 2026-04-13 | Cross IA↔Front | fix: cold-start resilience for Jobs, Candidates, and Tasks pages — Root cause: Next.js dev server takes 41+ seconds for initial compilation, | `lia-agent-system/app/api/v1/bias_audit.py`<br>`lia-agent-system/app/api/v1/candidate_compare.py`<br>`lia-agent-system/app/api/v1/cultural_fit.py` |
| 🟡 | `189643781` | 2026-04-13 | Backend | fix: B3+B4 context_level in execute + remove duplicate in test — B3: execute_custom_agent() now passes context_level to get_or_create_runtime | `lia-agent-system/app/api/v1/custom_agents.py` |
| 🟡 | `1b457b028` | 2026-04-12 | Backend | refactor: P0 cleanup round 2 — remove more dead code from chat.py — - _flatten_entities() (7 lines) — 0 callers | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `21f504ad8` | 2026-04-12 | Backend | refactor: P0 cleanup — remove 552 lines of dead code — Dead code removed: | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/ai/services/llm.py` |
| 🟡 | `8173145f8` | 2026-04-12 | Cross IA↔Back | fix: M2 memory — session handling + in-memory response + ATS import — - Fix ATS_INTEGRATION_DOMAIN_SPECIFIC missing import | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `1fb338d94` | 2026-04-12 | Cross IA↔Back | feat: M2 pick-one-writer — MainOrchestrator owns persistence (retry) — Key difference from previous attempt: instead of in-memory proxy, | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/chat/repositories/chat_repository.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🟡 | `76c795396` | 2026-04-12 | Backend | feat: remove handle_action_flow calls — Phase 0+1 covers all 46 actions (Item 2) — Removed handle_action_flow() calls from send_message and WS handler. | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `52be1ab23` | 2026-04-12 | Backend | docs: audit log final — Path A Passos 0-3 — Complete audit trail for Path A migration: | `lia-agent-system/app/api/v1/interviews.py` |
| 🟡 | `36d1c24f3` | 2026-04-12 | Cross IA↔Back | revert: M2 skip_memory_persist — session sharing needs architectural decision — Reverted skip_memory_persist to True and restored ChatRepository writes | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/interviews.py`<br>`lia-agent-system/app/domains/interview_scheduling/repositories/interview_repository.py` |
| 🟡 | `221067b48` | 2026-04-12 | Backend | fix: conversation re-fetch with None fallback + interview metadata reserved name — - get_conversation_by_id can return None if session mismatch. Added | `lia-agent-system/alembic/env.py`<br>`lia-agent-system/alembic/versions/067_interview_intelligence_columns.py`<br>`lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `637fad2da` | 2026-04-12 | Backend | fix: replace db.refresh with re-fetch for M2 session compatibility — After M2 migration, MainOrchestrator commits via its own db session. | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `54aee7902` | 2026-04-12 | Backend | feat: M2 memory migration - MainOrchestrator owns persistence (Passo 3) — Items 1-4 of M2 memory migration: | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `cbf23f7ed` | 2026-04-12 | Backend | feat: disable handle_action_flow via early return (Passo 2 Commit B) — MainOrchestrator Phase 0+1 now handles all actions. | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `9c37c675e` | 2026-04-10 | Backend | Add new endpoints for onboarding and WhatsApp messaging — Integrate new routers for onboarding and WhatsApp webhook functionalities into the API. | `lia-agent-system/app/api/routes.py` |
| 🟡 | `7c4cababe` | 2026-04-10 | Backend | Allow zero limit for candidate searches — Adjust search request models to permit a `pearch_limit` of 0, resolving an HTTP 422 validation error | `lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact.py` |
| 🟡 | `9d51b5db5` | 2026-04-10 | Backend | Fix critical search bug and add recruitment campaign stub functionality — Corrects the candidate search endpoint to properly handle PearchService requests, aligns the talent  | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/candidates/candidates_search.py`<br>`lia-agent-system/app/api/v1/recruitment_campaigns.py` |
| 🔴 | `3cad3eb72` | 2026-04-10 | Cross Back↔Front | Add real-time candidate counts to recruitment pipeline stages — Adds a new backend endpoint and frontend integration to display real-time candidate counts for each  | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`plataforma-lia/src/app/api/backend-proxy/pipeline-pulse/route.ts`<br>`plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟡 | `2ce967310` | 2026-04-09 | Cross IA↔Back | Fix issues with talent pool data handling and permissions — Correct account ID type casting and update LLM provider configurations in tool permissions. | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/api/v1/talent_pools.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml` |
| 🟡 | `d4757d2ae` | 2026-04-09 | Backend | Improve data access for sourcing agents — Replace getattr calls with direct attribute access for company_id in sourcing_agents.py. | `lia-agent-system/app/api/v1/sourcing_agents.py` |
| 🔴 | `cd704ed67` | 2026-04-08 | Cross Back↔Front | fix: resolve all implementation gaps from code review — Models: | `lia-agent-system/app/api/v1/digital_twins.py`<br>`lia-agent-system/app/api/v1/sector_templates.py`<br>`lia-agent-system/app/api/v1/sourcing_agents.py` |
| 🟡 | `5910b3db6` | 2026-04-07 | Backend | Update API client endpoints and registration for better organization — Refactor API routes in `routes.py` to include a specific prefix for clients, update `candidates.__in | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/candidates/__init__.py`<br>`lia-agent-system/app/api/v1/candidates_BACKUP.py` |
| 🟡 | `19db0abdd` | 2026-04-07 | Backend | Update documentation and code to reflect current system configurations — This commit updates the DEPLOY_GUIDE.md with detailed diagnostics and action items, standardizes ser | `lia-agent-system/app/api/v1/automation/_shared.py`<br>`lia-agent-system/app/api/v1/cv_parser.py`<br>`lia-agent-system/app/api/v1/job_vacancies/public.py` |
| 🟡 | `3b060add7` | 2026-04-07 | Cross IA↔Back | Update code to use dependency injection for service classes — Refactor multiple API endpoints to utilize dependency injection for service classes, improving code  | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py`<br>`lia-agent-system/app/api/v1/email_tracking.py` |
| 🔴 | `ca4d6f656` | 2026-04-07 | Cross IA↔Back | Refactor service imports and move WebSocket manager — Update service imports to use dependency injection and move the WebSocket manager to a shared locati | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/applications.py`<br>`lia-agent-system/app/api/v1/candidate_compare.py` |
| 🟡 | `d10f69696` | 2026-04-07 | Backend | Refactor data retrieval to use dedicated repositories for learning patterns and LLM configurations — Introduce `LearningPatternsRepository` to abstract database queries for learning patterns and updat | `lia-agent-system/app/api/v1/learning_patterns.py`<br>`lia-agent-system/app/api/v1/llm_config.py` |
| 🟡 | `113d065f2` | 2026-04-07 | Cross IA↔Back | Refactor data access layers to improve code organization and maintainability — Extract various data access logic into dedicated repository classes, improving separation of concern | `lia-agent-system/app/api/v1/communication_optout.py`<br>`lia-agent-system/app/api/v1/communication_settings.py`<br>`lia-agent-system/app/api/v1/company_retention.py` |
| 🟡 | `1445b1707` | 2026-04-07 | Cross IA↔Back | Update system to handle Rails-deprecated entities and fix import issues — Introduces a RailsAdapter for deprecated entities, adds comments to relevant API endpoints, fixes pr | `lia-agent-system/app/api/public/candidate_portal.py`<br>`lia-agent-system/app/api/v1/automation/_shared.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers.py` |
| 🟡 | `4a0e19f87` | 2026-04-07 | Backend | Update services to use dependency injection for CV parsing and search — Refactored the application to inject `CVParserService` and `PearchService` dependencies, improving m | `lia-agent-system/app/api/v1/applications.py`<br>`lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py` |
| 🟡 | `5e22af32e` | 2026-04-07 | Backend | Update the bot's connection to track user activity — Update the bot's event handling to include activity tracking for various events, and regenerate the  | `lia-agent-system/app/api/v1/automation/event_handlers.py` |
| 🟡 | `f7892c897` | 2026-04-07 | Backend | Integrate audit and activity logging into event handling — Refactor event handling and trigger logic to inject and utilize AuditService and ActivityService for | `lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/api/v1/automation/triggers.py` |
| 🟡 | `708342fb3` | 2026-04-07 | Backend | Update activity service to use dependency injection — Refactor activity service instantiation to use dependency injection in `lifecycle.py` and `test_acti | `lia-agent-system/app/api/v1/job_vacancies/lifecycle.py` |
| 🟡 | `f4eec1cc5` | 2026-04-07 | Backend | Update services to use dependency injection for audit and activity logging — Refactor `AuditService` and `ActivityService` to be injected as dependencies via `Depends` in multip | `lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/api/v1/interviews.py` |
| 🟡 | `66abfc191` | 2026-04-07 | Backend | Improve rubric evaluation by adding audit logging — Update rubric evaluation endpoint to include audit service dependency and log candidate scoring deci | `lia-agent-system/app/api/v1/rubric_evaluation.py` |
| 🟡 | `c1cb832aa` | 2026-04-07 | Backend | Update audit service integration for approval requests — Refactor `approvals.py` to inject `AuditService` and use `audit_svc.log_decision` for logging approv | `lia-agent-system/app/api/v1/approvals.py` |
| 🟡 | `b47e48853` | 2026-04-07 | Backend | Add audit service dependency to communication endpoints — Integrate AuditService dependency into send_email, send_whatsapp, and send_screening_invite endpoint | `lia-agent-system/app/api/v1/communication.py` |
| 🟡 | `f6c6a297b` | 2026-04-07 | Cross IA↔Back | Update audit service to use dependency injection for consistency — Refactor the audit service import and usage across multiple API endpoints to utilize dependency inje | `lia-agent-system/app/api/v1/communication.py`<br>`lia-agent-system/app/api/v1/jd_generation.py`<br>`lia-agent-system/app/api/v1/pipeline.py` |
| 🟡 | `b2eaf7827` | 2026-04-06 | Backend | Fix errors preventing job vacancy and database loading — Refactor job vacancy screening endpoints to use a dedicated repository, resolving import errors in a | `lia-agent-system/app/api/v1/agent_memory.py`<br>`lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/api/v1/job_vacancies/screening.py` |
| 🟡 | `e2a53d2ef` | 2026-04-06 | Backend | Add department management features to the company API — Introduces new API endpoints for listing, creating, updating, and deleting departments within the co | `lia-agent-system/app/api/v1/company.py` |
| 🔴 | `9ff2904b9` | 2026-04-06 | Cross IA↔Back | Remove unused demo user fallbacks and clean up code imports — Update imports, type hints, and remove dead code related to demo user fallbacks. | `lia-agent-system/app/agents/base_agent.py`<br>`lia-agent-system/app/agents/policy_setup_agent.py`<br>`lia-agent-system/app/agents/specialized/__init__.py` |
| 🔴 | `09e3dd04c` | 2026-04-06 | Cross Back↔Front | Refine chat interface and optimize backend data handling — Update UI components to adjust message bubble sizing, spacing, and font sizes. Introduce new toolbar | `lia-agent-system/app/api/v1/candidate_lists.py`<br>`lia-agent-system/app/api/v1/workforce.py`<br>`lia-agent-system/app/auth/dependencies.py` |
| 🟡 | `1d3f2691b` | 2026-04-06 | Backend | Add missing API modules and WebSocket manager for agent communication — Creates new API router files for lia_autonomous, lia_feedback, lia_multimodal, and lia_voice, and im | `lia-agent-system/app/api/v1/lia_autonomous.py`<br>`lia-agent-system/app/api/v1/lia_feedback.py`<br>`lia-agent-system/app/api/v1/lia_multimodal.py` |
| 🟡 | `a57a53db7` | 2026-04-06 | Backend | Remove unused insurance module import from API initialization — Remove import statement for the 'insurance' module from the v1 API's __init__.py file. | `lia-agent-system/app/api/v1/__init__.py` |
| 🟡 | `8e4b71cd6` | 2026-04-05 | Backend | Remove unused API routes for insurance, risk, and continuity — Removes the inclusion of insurance, risk_register, sod_matrix, and continuity routers from the main  | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/lia_autonomous.py`<br>`lia-agent-system/app/api/v1/lia_feedback.py` |
| 🟡 | `0faa509af` | 2026-04-05 | Cross IA↔Back | Integrate planning system into chat and improve session management — Refactor code to connect the planning system to the chat functionality, improve session ID generatio | `lia-agent-system/app/api/v1/ai_consumption.py`<br>`lia-agent-system/app/api/v1/audit_logs.py`<br>`lia-agent-system/app/api/v1/compliance_controls.py` |
| 🟡 | `540e3d76d` | 2026-04-05 | Backend | chore: remove .bak residual files from Etapa 6 split — Remove candidate_search.py.bak (234K), job_vacancies.py.bak (174K), | `lia-agent-system/app/api/v1/candidate_search.py.bak`<br>`lia-agent-system/app/api/v1/job_vacancies.py.bak`<br>`lia-agent-system/app/api/v1/lia_assistant.py.bak` |
| 🟡 | `a37527c9d` | 2026-04-04 | Backend | Update candidate search imports and add user authentication dependencies — Refactor imports in candidate search modules to include `CandidateProfile` and add authentication de | `lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/calibration.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact.py` |
| 🟡 | `e24632178` | 2026-04-04 | Backend | Task start baseline checkpoint for code review | `lia-agent-system/app/api/v1/orchestrated_talent_chat.py` |
| 🟡 | `232905535` | 2026-04-04 | Backend | Add execution plan details to chat responses for better task tracking — Add an optional `execution_plan` field to the `OrchestratedTalentChatResponse` model and populate it | `lia-agent-system/app/api/v1/orchestrated_talent_chat.py` |
| 🟡 | `534882693` | 2026-03-31 | Backend | Update rubric evaluation to use correct field names — Corrected `score` to `points` and `weighted_points` in rubric evaluation logic and corresponding E7  | `lia-agent-system/app/api/v1/rubric_evaluation.py` |
| 🟡 | `e3138f74a` | 2026-03-25 | Backend | Fix: enriched_jd not persisted after generation — missing from listing endpoint — Root cause: The GET /api/v1/job-vacancies listing endpoint did not include | `lia-agent-system/app/api/v1/job_vacancies.py` |
| 🟡 | `e31c370de` | 2026-03-16 | Backend | Fix: expanded prompt chat on jobs page - fix 403 auth and provider name — Two root causes: | `lia-agent-system/app/api/v1/lia_assistant.py` |

### §2 Orchestrator Migration

**Descrição:** Migração do orchestrator monolítico para 4 services especializados: PlanOrchestrationService, FallbackReActService, RubricDispatchService, AnalyticsDispatchService. Adiciona OTLP tracing, canary rollout kit, ADR-019 canonical span constants, 50 characterization tests.

**⚠️ Dependências para cherry-pick:** ADR-019 canonical spans | G6+G7 hooks block-only ativos | Canary kit com feature flag | OTLP exporter configurado

**Arquivos canônicos:** lia-agent-system/app/orchestrator/*, app/services/plan_orchestration*, app/services/fallback_react*, app/services/rubric_dispatch*, tests/characterization/*

**Docs de referência:** ADR-019 em ARCHITECTURE.md

- **Commits:** 50  |  **Período:** 2026-04-03 → 2026-04-29  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×41 🟢×5 🔴×4
- **Tags/Milestones:** `milestone/harness-orchestrator-v1`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `1e52196c4` | 2026-04-29 | Docs | docs(nav): BRANCH_MAP — registro do merge feat/orch-migration-sprint-I -> main | `lia-agent-system/docs/BRANCH_MAP.md` |
| 🟢 | `ec0657d80` | 2026-04-29 | Empty/merge | merge: feat/orch-migration-sprint-I — Rail A sprint completo — Waves 0-4 do Rail A audit (22 cards × 12 camadas): | — |
| 🟡 | `94a629c1d` | 2026-04-26 | Backend | feat(orch-migration): final delivery - canary kit + Sprint V plan + ADR-019 final — LIA-D06 Orchestrator Migration - IMPLEMENTATION COMPLETE. | `lia-agent-system/tools/canary/canary_health_check.sh`<br>`lia-agent-system/tools/canary/canary_promote.sh`<br>`lia-agent-system/tools/canary/canary_rollback.sh` |
| 🟢 | `5a3b1a1c7` | 2026-04-26 | Docs | docs(orch-migration): Sprint III.E canary rollout plan — LIA-D06 Orchestrator Migration — documenta plano de canary rollout. | `lia-agent-system/docs/migrations/SPRINT_III_E_CANARY_PLAN.md` |
| 🟡 | `b6dabf9b8` | 2026-04-26 | Backend | feat(orch-migration): add OTLP LGPD violation pre-commit hook — LIA-D06 Orchestrator Migration — Sprint III follow-up. | `lia-agent-system/tools/migration/otlp_lgpd_check.py` |
| 🟡 | `7333e418a` | 2026-04-26 | Cross IA↔Back | feat(orch-migration): extract AnalyticsDispatchService — process_analytics_request canonical — LIA-D06 Orchestrator Migration — extraction follow-up (Sprint IV+). | `lia-agent-system/app/domains/analytics/services/analytics_dispatch.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `86e914d93` | 2026-04-26 | IA | feat(orch-migration): Sprint III.D — late-intercept FallbackReActService flag — LIA-D06 Orchestrator Migration — Sprint III.D (FallbackReAct feature flag). | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `00db0ec4b` | 2026-04-26 | Cross IA↔Back | feat(orch-migration): Sprint IV — extract RubricDispatchService (CV match BARS) — LIA-D06 Orchestrator Migration — Sprint IV (CV screening rubric extraction). | `lia-agent-system/app/domains/cv_screening/services/rubric_dispatch.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `1d7262cdb` | 2026-04-26 | IA | feat(orch-migration): Sprint III.C — OTLP @trace_span aplicados em V1 e V2 — LIA-D06 Orchestrator Migration — Sprint III.C (Observability application). | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `4ea526c59` | 2026-04-26 | IA | feat(orch-migration): Sprint III.B — feature flag granular para PlanOrchestrationService — LIA-D06 Orchestrator Migration — Sprint III.B (incremental V2 service usage). | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `b4e3d20c1` | 2026-04-26 | IA | fix(orch-migration): resolve P1 #7 — lazy init race condition — LIA-D06 Orchestrator Migration — Audit P1 #7 (era pendente da audit). | `lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `c5563138a` | 2026-04-26 | IA | feat(orch-migration): Sprint III.A — V2 DI setup (services optional, backward compat) — LIA-D06 Orchestrator Migration — Sprint III.A (DI scaffolding for V2). | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `0312bb4fb` | 2026-04-26 | IA | refactor(orch-migration): Sprint II audit fixes — 6 P1 + BASELINE.md — LIA-D06 Orchestrator Migration — post Sprint II code review fixes. | `lia-agent-system/app/orchestrator/services/fallback_react_service.py`<br>`lia-agent-system/app/orchestrator/services/plan_orchestration_service.py` |
| 🟡 | `dd167b08b` | 2026-04-26 | IA | feat(orch-migration): Sprint II.1 — PlanOrchestrationService canonical — LIA-D06 Orchestrator Migration — Sprint II.1 (Plan orchestration extraction). | `lia-agent-system/app/orchestrator/services/plan_orchestration_service.py` |
| 🟡 | `4b4b9bf8c` | 2026-04-26 | IA | feat(orch-migration): Sprint II.2 — extract FallbackReActService (LIA-A04) — LIA-D06 Orchestrator Migration — Sprint II.2 (LIA-A04 fallback ReAct). | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`lia-agent-system/app/orchestrator/services/fallback_react_service.py` |
| 🟡 | `d9a4a6367` | 2026-04-26 | IA | feat(orch-migration): Sprint II.4 — extract context_type_override to service — LIA-D06 Orchestrator Migration — Sprint II.4 (Context-type override). | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`lia-agent-system/app/orchestrator/services/context_type_override.py` |
| 🟡 | `5051c824b` | 2026-04-26 | IA | feat(orch-migration): Sprint II.5 — PolicyGateService canonical wrapper — LIA-D06 Orchestrator Migration — Sprint II.5 (Policy gate extraction). | `lia-agent-system/app/orchestrator/services/__init__.py`<br>`lia-agent-system/app/orchestrator/services/policy_gate_service.py` |
| 🟡 | `939d3a9e4` | 2026-04-26 | IA | feat(orch-migration): Sprint II.3 — extract heuristics module from V1 — LIA-D06 Orchestrator Migration — Sprint II.3 (Heuristics extraction). | `lia-agent-system/app/orchestrator/heuristics/__init__.py`<br>`lia-agent-system/app/orchestrator/heuristics/cv_matching_detector.py`<br>`lia-agent-system/app/orchestrator/heuristics/technical_response_detector.py` |
| 🟢 | `763bfbdc5` | 2026-04-26 | Testes | refactor(orch-migration): code review fixes — fixture consolidation + ADR-019 gate — Code review aprovou Sprint II com 3 condicoes (P1+P2). Aplicadas: | `lia-agent-system/tests/characterization/conftest.py`<br>`lia-agent-system/tests/characterization/test_v1_admin_methods.py`<br>`lia-agent-system/tests/characterization/test_v1_internal_methods.py` |
| 🟡 | `f4ad3b82a` | 2026-04-26 | IA | docs(orch-migration): Sprint I-D+F — ADR-019 + canonical span constants — LIA-D06 Orchestrator Migration — closes Sprint I scaffolding tasks. | `lia-agent-system/app/orchestrator/_observability.py` |
| 🟢 | `ae2d446d3` | 2026-04-26 | Testes | test(orch-migration): Sprint I-C characterization tests — 50 fixtures all passing — LIA-D06 Orchestrator Migration — Sprint I Tarefa C. | `lia-agent-system/tests/characterization/test_v1_admin_methods.py`<br>`lia-agent-system/tests/characterization/test_v1_internal_methods.py`<br>`lia-agent-system/tests/characterization/test_v1_process_request.py` |
| 🟡 | `f4989d53b` | 2026-04-26 | Backend | feat(orch-migration): Sprint I-A foundations — V1 inventory + characterization tests scaffolding — LIA-D06 Orchestrator Migration — Sprint I (Discovery + Tests). | `lia-agent-system/tools/migration/ast_orchestrator_inventory.py` |
| 🟡 | `981bd3c32` | 2026-04-22 | IA | Refine tool selection to improve agent efficiency and reduce prompt size — Introduce intent-based tool filtering to reduce the number of tools passed to the LLM, optimizing pr | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/tools/intent_heuristic.py` |
| 🟡 | `fddbc96ae` | 2026-04-19 | IA | Improve candidate comparison fallback for agentic loop — Modify the candidate comparison logic to return a "not_actionable" status when fewer than two candid | `lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟡 | `98f2c5c45` | 2026-04-19 | IA | Update database query to correctly reference company ID — Update the SQL query in `candidate_actions.py` to use the correct parameter binding for company ID. | `lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py` |
| 🟡 | `48fc90c2b` | 2026-04-19 | Cross IA↔Back | Add ability to reject candidates and improve job duplication — Introduce the `reject_candidate` intent and action, enhance `duplicate_job` to support finding jobs  | `lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py` |
| 🟡 | `bafaea563` | 2026-04-19 | IA | fix eval: fix uuid/varchar JOIN mismatch in candidate/sourcing pipeline | `lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟡 | `e12009486` | 2026-04-19 | IA | fix eval CM-001/CM-003: remove all wrong CAST uuid on varchar columns in candidate pipeline | `lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py` |
| 🟡 | `a760fe110` | 2026-04-19 | Cross IA↔Back | Improve job description generation and entity extraction — Update job description templating to dynamically generate responsibilities based on skills, and enha | `lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py` |
| 🟡 | `7ef0bfbe8` | 2026-04-19 | IA | Improve data handling and prompt accuracy for CV screening — Add thread-safety to the LRU cache and refine prompt examples to prevent data leakage. | `lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `85b824fbd` | 2026-04-18 | IA | Pass through the candidate name for handler API name-lookup — Update `ActionExecutorService` to pass through `candidate_name` for API name-lookup. | `lia-agent-system/app/orchestrator/action_executor/executor.py` |
| 🟡 | `38f0ee98a` | 2026-04-18 | IA | Add a way to store conversation state within the context — Add a new field `conversation_state` to the `UniversalContext` class to store in-session entity memo | `lia-agent-system/app/orchestrator/context_adapter.py` |
| 🟡 | `fbbff9f49` | 2026-04-18 | Cross IA↔Back | Add context automatically for company and recruiter IDs — Injects `company_id` and `recruiter_id` into tool parameters when available in the context, and upda | `lia-agent-system/app/orchestrator/action_executor/executor.py` |
| 🟡 | `732cc16e4` | 2026-04-18 | Cross IA↔Back | Update evaluation to include more candidate information and improve accuracy — Modify intent configurations to accept candidate names and IDs, and add corresponding parameters for | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py` |
| 🟡 | `6378873d1` | 2026-04-18 | IA | Improve candidate matching and extraction for specific intents — Update regex patterns in utils.py for more robust extraction of candidate names and job titles, and  | `lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟡 | `7cbf3bf34` | 2026-04-18 | IA | Add functionality to extract candidate stages from messages — Adds logic to `utils.py` to parse "from_stage" and "to_stage" entities for the "mover_candidatos_por | `lia-agent-system/app/orchestrator/action_executor/utils.py` |
| 🟡 | `369af733e` | 2026-04-18 | IA | Improve job search by allowing lookup via ID or short ID — Update the job health check to support job ID or short ID lookups, improving flexibility and error h | `lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py` |
| 🟡 | `2673b6bf6` | 2026-04-17 | IA | Add ability to navigate between pages based on user intent — Add a new function to inject UI actions for navigation intent detection. | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `58b50fc58` | 2026-04-17 | Cross IA↔Back | Add navigation capabilities and context to agent responses — Introduces navigation intent detection for UI actions, enhances agent context with company and user  | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/navigation_intent.py` |
| 🟡 | `990bd408b` | 2026-04-14 | IA | fix: pass job_id to TenantContextService for pipeline awareness [P35-044] — MainOrchestrator now passes ctx.entity_id as job_id when entity_type | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `9ebe2405a` | 2026-04-13 | IA | Task start baseline checkpoint for code review | `lia-agent-system/app/orchestrator/config/domain_routing.yaml`<br>`lia-agent-system/app/orchestrator/fast_router.py` |
| 🟡 | `12fa1f74d` | 2026-04-12 | IA | fix: indentation in orchestrator.py broken by TODO comment | `lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `a1ce3a752` | 2026-04-12 | IA | fix: propagate tenant_context_snippet through to_orchestrator_context() — Passo 0 of Path A migration. The TenantContext was fetched from DB | `lia-agent-system/app/orchestrator/context_adapter.py` |
| 🔴 | `b1e40d0ce` | 2026-04-12 | Cross IA↔Front | Improve how the system understands user requests and avoid unnecessary page changes — Adjust the confidence threshold for navigation intent detection and modify keyword weighting to diff | `lia-agent-system/app/orchestrator/navigation_intent.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟡 | `92b742c15` | 2026-04-11 | IA | Accurately track costs across multiple AI models in a cascade — Refactor LLMCascadeRouter to implement `cost_accumulator` and `_record_tokens_multi` for per-attempt | `lia-agent-system/app/orchestrator/llm_cascade.py` |
| 🟡 | `8e7a4407e` | 2026-04-11 | IA | Improve template creation with better data handling — Refactors the `_create_template` handler to use a more robust method for retrieving and stripping pa | `lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |
| 🟡 | `58417c7d3` | 2026-04-11 | Cross IA↔Back | Update job handling and logging to improve system reliability — Refactor action handler hooks to adjust audit logging level from debug to warning, update Rails even | `lia-agent-system/alembic/versions/063_create_scheduling_links_table.py`<br>`lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/orchestrator/action_handlers/pipeline_actions.py` |
| 🔴 | `0867d7d12` | 2026-04-05 | Cross IA↔Front | Fix sidebar errors and update backend port configuration — Addresses "Maximum update depth exceeded" and "Invalid hook call" errors in the sidebar component by | `lia-agent-system/app/orchestrator/action_executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/__init__.py`<br>`lia-agent-system/app/orchestrator/action_executor/action_types.py` |
| 🔴 | `f12e35d4a` | 2026-04-03 | Cross IA↔Front | Improve CV analysis and access control for API endpoints — Update CV matching patterns in orchestrator.py, replace redirectToLogin with denyAccess in middlewar | `lia-agent-system/app/orchestrator/orchestrator.py` |
| 🔴 | `0882a4580` | 2026-04-03 | Cross IA↔Front | Align job preview panel with candidate preview design system — Fixes background, border, and badge font size issues in the job preview panel to match the candidate | `lia-agent-system/app/orchestrator/orchestrator.py`<br>`lia-agent-system/app/services/enhanced_intent_classifier.py`<br>`plataforma-lia/src/components/pages/jobs/JobPreviewPanel.tsx` |

### Triagem (módulo)

**Descrição:** Módulo Triagem — chrome traduzido (errors, footer, phone card), screens novas para triagem flow, mockups polidos. WSI Modal Triagem com banner degraded + breakdown granular.

**⚠️ Dependências para cherry-pick:** WSI 0-10 ativo | Audit trail com response_hash | i18n PT/EN

**Arquivos canônicos:** plataforma-lia/src/components/triagem/*, src/components/wsi-modal/*

**Docs de referência:** BRANCH_MAP — Triagem

- **Commits:** 49  |  **Período:** 2026-03-19 → 2026-04-27  |  **Camadas:** Backend + Frontend + IA + Rails  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×21 🟢×18 🔴×10

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `c505e4866` | 2026-04-27 | Frontend (UI) | Translate the rest of the candidate triagem chrome (errors, footer, phone card) — Task #887: Task #886 had localized the six shared triagem components themselves, | `plataforma-lia/src/app/[locale]/triagem/[token]/_components/TriagemFlow.tsx` |
| 🟡 | `f9893206e` | 2026-04-27 | Frontend (UI) | Localize candidate triagem chrome via next-intl (Task #886) — The shared triagem UI components were swapping copy with inline `isEn` | `plataforma-lia/src/components/triagem/ChatContainer.tsx`<br>`plataforma-lia/src/components/triagem/CompletionCard.tsx`<br>`plataforma-lia/src/components/triagem/InputBar.tsx` |
| 🟢 | `f42fa5095` | 2026-04-27 | Frontend (UI) | Add WhatsApp and reminder email previews to triagem preview suite — Original task #884: Extend the candidate-facing template preview pages so | `plataforma-lia/src/app/[locale]/triagem/preview/email-reminder/page.tsx`<br>`plataforma-lia/src/app/[locale]/triagem/preview/page.tsx`<br>`plataforma-lia/src/app/[locale]/triagem/preview/whatsapp/page.tsx` |
| 🔴 | `f277a773c` | 2026-04-27 | Cross IA↔Front | Task #882: Preview da triagem do candidato pra print — Adiciona quatro rotas de preview sem autenticacao na plataforma-lia, dentro | `lia-agent-system/alembic/versions/099_create_offer_proposals.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/offers.py` |
| 🔴 | `505c52265` | 2026-04-19 | Cross Back↔Front | Update modal to display information consistently across all views — Update the TriagemDetailsModal component to ensure the LGPD/EU AI Act banner is always visible above | `plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🟢 | `a2dbabff3` | 2026-04-19 | Frontend (UI) | Task #529 — UI Modal Triagem: banner degraded + breakdown granular — Auditoria pré-produção rev. 23 (G23-02 + G23-03 frontend): o modal | `plataforma-lia/src/components/triagem-details/triagem-responses-section.tsx` |
| 🟢 | `20f46f00b` | 2026-04-19 | Empty/merge | Task #529 — UI Modal Triagem: banner degraded + breakdown granular — Auditoria pré-produção rev. 23 (G23-02 + G23-03 frontend): o modal | — |
| 🟢 | `d502e54bf` | 2026-04-19 | Frontend (UI) | Add transparency about semantic analysis unavailability and improve score breakdown — Implement a fallback for calculating degraded quality counts and display a banner when semantic anal | `plataforma-lia/src/components/triagem-details-modal.tsx`<br>`plataforma-lia/src/components/triagem-details/triagem-responses-section.tsx` |
| 🟡 | `75a3326e1` | 2026-04-18 | Rails (ats-api) | Estender o seed de triagem para mais vagas/candidatos (Task #427) — Adiciona duas triagens WSI completas alem da Maria Silva, para que o | `ats-api-copia/db/seeds.rb` |
| 🟡 | `ed3f57b30` | 2026-04-18 | Rails (ats-api) | Unify triagem_sessions/triagem_messages ownership (Python is source of truth) — Task #428: the Rails migration `ats-api-copia/db/migrate/20250716000045_create_triagem_and_voice.rb` | `ats-api-copia/db/migrate/20250716000045_create_triagem_and_voice.rb`<br>`ats-api-copia/db/seeds.rb` |
| 🟢 | `07bdedd98` | 2026-04-18 | Testes | test(triagem): cover audio decoding path in useTriagemMessages — Task #416 — the text optimistic-send + retry flow already had vitest | `plataforma-lia/src/hooks/__tests__/useTriagemMessages.test.ts` |
| 🟡 | `ceea3c722` | 2026-04-17 | Rails (ats-api) | Task #426: Seed candidato com triagem preenchida pra print — Estendi `ats-api-copia/db/seeds.rb` adicionando uma sessao de triagem WSI | `ats-api-copia/db/seeds.rb` |
| 🟡 | `c5799eb9a` | 2026-04-14 | Frontend (UI) | Task #193: i18n — Candidatos, Kanban, Funil, Triagem — Extracted all hardcoded Portuguese strings from ~85+ component files | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesViewComposition.tsx`<br>`plataforma-lia/src/components/wsi/wsi-triagem-invite-modal.tsx` |
| 🟡 | `2a1b2d014` | 2026-04-14 | Frontend (UI) | Task #193: i18n — Candidatos, Kanban, Funil, Triagem — Extracted all hardcoded Portuguese strings from ~85+ component files | `plataforma-lia/src/app/[locale]/access/AccessClient.tsx`<br>`plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/app/[locale]/funil-de-talentos/layout.tsx` |
| 🔴 | `3968b9d77` | 2026-04-14 | Frontend (UI) | Task #193: i18n — Candidatos, Kanban, Funil, Triagem — Extracted all hardcoded Portuguese strings from ~80+ component files | `plataforma-lia/src/components/candidate-profile/CandidateAvatar.tsx`<br>`plataforma-lia/src/components/candidate-profile/CandidateContactActions.tsx`<br>`plataforma-lia/src/components/candidate-profile/CandidateScoreBadge.tsx` |
| 🟡 | `ad7e897a3` | 2026-04-11 | Cross IA↔Back | Implement real start_screening handler + fix code quality issues — T001: Replaced stub _start_screening handler in candidate_actions.py with | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `d8c592289` | 2026-04-11 | IA | Implement real start_screening handler + fix code quality issues — T001: Replaced stub _start_screening handler in candidate_actions.py with | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `181bbdba5` | 2026-04-11 | IA | Implement real start_screening handler (was last simulated stub) — Replaced the stub _start_screening handler in candidate_actions.py with a | `lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py` |
| 🟢 | `58ef17b24` | 2026-04-11 | Frontend (UI) | DS Phase 3-6: tabs standardized, 318 badge overrides cleaned, hex tokenized | `plataforma-lia/src/components/triagem-details/triagem-details-header.tsx` |
| 🟡 | `2a95d4360` | 2026-04-08 | Frontend (UI) | refactor: decompose 4 large pages + 4 large hooks into focused modules — Pages decomposed (page.tsx now thin wrappers): | `plataforma-lia/src/app/login/welcome/_components/WelcomeSteps.tsx`<br>`plataforma-lia/src/app/login/welcome/page.tsx`<br>`plataforma-lia/src/app/portal/data-request/[token]/_components/DataRequestForm.tsx` |
| 🟡 | `e817b87a9` | 2026-04-06 | Backend | chore(guards): remove triagem.py from PENDING_MIGRATION (now 142) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `5fe498341` | 2026-04-06 | Backend | feat(phase2): migrate triagem.py to TriagemRepository | `lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/domains/triagem/repositories/__init__.py`<br>`lia-agent-system/app/domains/triagem/repositories/triagem_repository.py` |
| 🟡 | `ae69cf957` | 2026-04-06 | Backend | Improve logging and email provider functionality — Update logging for demo users in chat actions, refine LGPD opt-out logging, simplify triagem invite  | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/communication_optout.py`<br>`lia-agent-system/app/api/v1/triagem.py` |
| 🟡 | `e475dd48a` | 2026-04-04 | Backend | feat(voice-screening): Prompt Inteligente de Voz — LIA Conduz Triagem com Maestria (Task #140) — ## O que foi implementado | `lia-agent-system/app/domains/communication/services/twilio_voice_service.py`<br>`lia-agent-system/app/services/voice_screening_orchestrator.py` |
| 🟡 | `e4e97e207` | 2026-04-04 | Backend | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: | `lia-agent-system/app/services/openmic_service.py` |
| 🟡 | `fbfee90ed` | 2026-04-04 | Backend | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: | `lia-agent-system/app/services/openmic_service.py`<br>`lia-agent-system/app/services/triagem_session_service.py` |
| 🔴 | `4fb43153b` | 2026-04-04 | Cross Back↔Front | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: | `lia-agent-system/app/services/openmic_service.py`<br>`lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/triagem/[token]/page.tsx` |
| 🔴 | `3dfe1ede9` | 2026-04-04 | Cross Back↔Front | Task #130: Triagem — Phone Call Screening via OpenMic.ai — Backend: | `lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/triagem/[token]/page.tsx` |
| 🟢 | `c189721d5` | 2026-04-04 | Frontend (UI) | refactor(triagem): extract shared TTS audio helpers in MessageBubble — - Extract `playAudioFromUrl` and `fetchAndPlayTts` as reusable useCallback hooks | `plataforma-lia/src/components/triagem/MessageBubble.tsx` |
| 🟢 | `676943348` | 2026-04-04 | Frontend (UI) | refactor(triagem): extract shared TTS audio helpers in MessageBubble — - Extract `playAudioFromUrl` and `fetchAndPlayTts` as reusable useCallback hooks | `plataforma-lia/src/components/triagem/MessageBubble.tsx` |
| 🔴 | `d50c67402` | 2026-04-04 | Cross Back↔Front | refactor(triagem): extract shared TTS audio helpers in MessageBubble — - Extract `playAudioFromUrl` and `fetchAndPlayTts` as reusable useCallback hooks | `lia-agent-system/app/api/v1/triagem.py`<br>`lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/triagem/[token]/page.tsx` |
| 🟡 | `617d2b0ca` | 2026-04-04 | Backend | Task #128: Triagem UX — Ajustes Candidato (Welcome, Balões, Tom, Whitelabel) — Backend (triagem_session_service.py): | `lia-agent-system/app/services/triagem_session_service.py` |
| 🔴 | `5bb701e8f` | 2026-04-04 | Cross Back↔Front | Task #128: Triagem UX — Ajustes Candidato (Welcome, Balões, Tom, Whitelabel) — Backend (triagem_session_service.py): | `lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/components/triagem/MessageBubble.tsx`<br>`plataforma-lia/src/components/triagem/WelcomeCard.tsx` |
| 🟡 | `1ec46c597` | 2026-04-01 | Frontend (UI) | refactor(arch): reduce last borderline files below 1000L (prompts, CandidateSearchResultsView, JobEditTab, triagem-modal) | `plataforma-lia/src/components/jobs/JobEditTab.tsx`<br>`plataforma-lia/src/components/jobs/job-edit-tab/JobSectionHeader.tsx`<br>`plataforma-lia/src/components/jobs/job-edit-tab/index.ts` |
| 🟡 | `284558a7f` | 2026-04-01 | Frontend (UI) | Clarify and specify code locations for backend processes and services — Refactor the documentation to precisely define backend Python code locations for various services an | `plataforma-lia/src/components/candidate-preview/activities/ActivityExpandedDetails.tsx`<br>`plataforma-lia/src/components/modals/job-compare-modal.tsx`<br>`plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🟢 | `b88d777db` | 2026-03-31 | Frontend (UI) | fix(ts): last TS error — filter undefined before concat in triagem-details-modal (0 errors total) | `plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🟢 | `e1e7d4bda` | 2026-03-31 | Frontend (UI) | fix(ts): reduce errors in triagem-details-modal.tsx | `plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🟢 | `0a37daccb` | 2026-03-31 | Frontend (UI) | fix(frontend): Task #75 — Fix DS v4.2.1 findings DS-01/02/03/04 in triagem — All 10 triagem components updated to comply with Design System v4.2.1: | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/layout.tsx`<br>`plataforma-lia/src/app/jobs/[id]/layout.tsx`<br>`plataforma-lia/src/app/vagas/[slug]/layout.tsx` |
| 🟡 | `4ad544447` | 2026-03-31 | Frontend (UI) | fix(frontend): Task #75 — Fix DS v4.2.1 findings DS-01/02/03/04 in triagem components — All 10 triagem components updated to comply with Design System v4.2.1: | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/layout.tsx`<br>`plataforma-lia/src/app/jobs/[id]/layout.tsx`<br>`plataforma-lia/src/app/portal/data-request/[token]/layout.tsx` |
| 🟢 | `b532e766b` | 2026-03-31 | Empty/merge | feat(triagem): complete Task #69 — fix triagem E2E bugs + code review fixes — Fixes applied to existing triagem infrastructure (page, components, | — |
| 🟡 | `18bd6a094` | 2026-03-31 | Backend | fix(triagem): align pipeline statuses with canonical values (pending/approved/rejected) — - Low WSI score (<5.5): set status='rejected' (was 'screened_low') | `lia-agent-system/app/services/triagem_session_service.py` |
| 🟢 | `07cf149b3` | 2026-03-31 | Empty/merge | feat(triagem): complete Task #69 — fix triagem E2E bugs + code review fixes — This session fixed 3 bugs in the existing triagem E2E infrastructure: | — |
| 🟢 | `8fb6ed426` | 2026-03-31 | Empty/merge | feat(triagem): complete Task #69 — Chat Web Público + Triagem E2E — Task #69 Fase 2 fixes (commits 72c5d5dd + 0d0f056e): | — |
| 🔴 | `0d0f056ef` | 2026-03-31 | Cross Back↔Front | fix(triagem): code review fixes — progress accuracy, pipeline status, stage counts — - Fix estimated_minutes_remaining: return 0 when no questions remain | `lia-agent-system/app/services/triagem_session_service.py` |
| 🔴 | `72c5d5ddc` | 2026-03-31 | Cross Back↔Front | feat(triagem): fix E2E flow — proxy POST bug, pipeline update, progress tracking — Task #69 Fase 2 — Chat Web Público + Triagem E2E: | `lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/app/api/backend-proxy/triagem/[...path]/route.ts` |
| 🟢 | `26b1fee54` | 2026-03-29 | Frontend (api/util) | Update transversal architecture diagrams: 1. HTML: LIA side now has matching transversal bands (16 capabilities x 11 agents) 2. HTML: Added "✅ auto" legend explaining EnhancedAgentMixin auto-inheritan | `plataforma-lia/public/diagram-transversal.html` |
| 🟢 | `2c7d20500` | 2026-03-25 | Frontend (UI) | Task #41: Triagem details modal — mockup alignment improvements — Changes in this increment: | `plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🔴 | `8425b8eea` | 2026-03-25 | Cross Back↔Front | Task #41: Triagem details modal pixel-perfect mockup alignment — Backend (F11 endpoint): | `lia-agent-system/app/api/v1/wsi.py`<br>`plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🟢 | `06fc40b25` | 2026-03-19 | Docs | Add detailed technical guide for implementing market-standard AI agents — Complete Section 5 of the technical document with in-depth explanations and code examples for five d | `proposals/Paralelo_LIA_vs_V5_Arquitetura_IA.md` |

### Tasks #712-#886 (Features de produto)

**Descrição:** Tasks da janela atual #712-#886 — onboarding proativo, wizard vagas, benefícios, WSI/Bloom terms, triagem, funil de candidatos, multi-tenancy.

**⚠️ Dependências para cherry-pick:** Ver categorias específicas — features ainda em progresso em feat/orch-migration-sprint-I

**Arquivos canônicos:** Diversos — depende da task específica

**Docs de referência:** BRANCH_MAP §5

- **Commits:** 48  |  **Período:** 2026-04-21 → 2026-04-27  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×23 🟢×19 🔴×6

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `90b519305` | 2026-04-27 | Frontend (UI) | Localize screening template previews for English — Task #885 — make `/[locale]/triagem/preview/...` render an English version | `plataforma-lia/src/app/[locale]/triagem/preview/chat/page.tsx`<br>`plataforma-lia/src/app/[locale]/triagem/preview/email-reminder/page.tsx`<br>`plataforma-lia/src/app/[locale]/triagem/preview/email/page.tsx` |
| 🟡 | `99ffb988a` | 2026-04-26 | Backend | Audit and bound process-local Redis fallbacks (Task #871) — Mirrors the TTL eviction added to jd_upload._LOCAL_STAGE in Task #867 across | `lia-agent-system/app/domains/ai/services/ai_cache_service.py`<br>`lia-agent-system/app/domains/ai/services/embedding_cache_service.py`<br>`lia-agent-system/app/domains/ai/services/response_cache_service.py` |
| 🟡 | `6086b2cd8` | 2026-04-26 | Backend | Evict abandoned uploads from the in-memory staging fallback (Task #867) — Original task | `lia-agent-system/app/jobs/tasks/jd_upload.py`<br>`lia-agent-system/tests/security/test_upload_dos.py` |
| 🟢 | `8a681bb3a` | 2026-04-26 | Frontend (UI) | Task #844 — Restore the LIA chat message-action UI behind the broken tests — The 3 tests in | `plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🔴 | `17031f1dc` | 2026-04-26 | Frontend (UI) | Task #840 — Alinhar UnifiedChat ao Design System v4.2.1 — Resolve o cluster de achados M-03/M-04/M-05/M-11/L-02/L-03 da auditoria | `plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/unified-chat/ChatImageMessage.tsx`<br>`plataforma-lia/src/components/unified-chat/ChatSuggestionsPanel.tsx` |
| 🟢 | `843db90be` | 2026-04-26 | Frontend (UI) | Task #836 — Mov 1 unificação dos surfaces de criação de vaga — Faxina + 5 quick-wins UX no UnifiedChat: | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/wizard-saved-label.ts` |
| 🟢 | `b7526f6fe` | 2026-04-26 | Frontend (UI) | Task #836 — Mov 1 unificação dos surfaces de criação de vaga — Faxina + 5 quick-wins UX no UnifiedChat: | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/slash-commands.ts` |
| 🟢 | `7c4510f80` | 2026-04-26 | Frontend (UI) | Task #836 — Mov 1 unificação dos surfaces de criação de vaga — Faxina + 5 quick-wins UX no UnifiedChat: | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/slash-commands.ts`<br>`plataforma-lia/src/components/unified-chat/wizard/useWizardIntegration.ts` |
| 🟢 | `68cdbb065` | 2026-04-26 | Frontend (UI) | Task #835: keep "Plano de trabalho — Concluído" card visible in expanded chat — Original task: bring the duplicate plan card inside `expanded-chat-modal.tsx` | `plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/WizardPlanFeedCard.tsx` |
| 🟢 | `a08bb627c` | 2026-04-26 | Frontend (UI) | Task #828 — Cobrir o cartao "Plano de trabalho" com teste end-to-end real — Adiciona o teste e2e Playwright que faltava sobre o ciclo do cartao | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🟡 | `b1205833b` | 2026-04-26 | Backend | Migrar imports legados dos shims de intent classifier para o caminho canônico (Task #821) — Original task: | `lia-agent-system/app/api/v1/lia_assistant/_shared.py`<br>`lia-agent-system/app/api/v1/lia_assistant_fasttrack.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service.py` |
| 🟢 | `69a3a4d4c` | 2026-04-25 | Testes | Task #817: Auditoria Canônica do Chat — fixes runtime + relatório PT-BR — Investigou 3 sintomas runtime do chat reportados na task. Aplicou | `plataforma-lia/src/components/lia-float/__tests__/LiaChatPanel-p2c.test.tsx` |
| 🟢 | `b7cfb594f` | 2026-04-25 | Testes | Task #817: Auditoria Canônica do Chat — fixes runtime + relatório PT-BR — Investigou 3 sintomas runtime do chat reportados na task. Aplicou | `plataforma-lia/src/app/api/auth/ws-token/__tests__/route.test.ts`<br>`plataforma-lia/src/app/api/backend-proxy/pipeline-pulse/__tests__/route.test.ts` |
| 🟡 | `7c4c03151` | 2026-04-25 | Frontend (UI) | Task #817: Auditoria Canônica do Chat — fixes runtime + relatório PT-BR — Investigou 3 sintomas runtime do chat reportados na task. Aplicou | `plataforma-lia/src/app/api/backend-proxy/pipeline-pulse/route.ts`<br>`plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟢 | `85fbacb23` | 2026-04-25 | Docs | docs: spec canônico de configuração mínima por tenant (Task #816) — Cria docs/governance/tenant-minimum-config.md (PT-BR), contrato canônico | `docs/governance/tenant-minimum-config.md`<br>`replit.md` |
| 🟡 | `ec4f1fe8d` | 2026-04-25 | Backend | Task #813: Estender seed_service para popular o tenant demo — Adiciona `seed_demo_company_settings(db)` em | `lia-agent-system/app/shared/services/seed_service.py` |
| 🟡 | `43f41ca02` | 2026-04-25 | Backend | Task #813: Estender seed_service para popular o tenant demo — Adiciona `seed_demo_company_settings(db)` em | `lia-agent-system/app/shared/services/seed_service.py` |
| 🟡 | `ad1fd512a` | 2026-04-22 | Frontend (UI) | Task #802: remove parallel proxy route /api/lia/[...path] — What changed | `plataforma-lia/src/app/api/lia/[...path]/route.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useLIAAICommands.ts`<br>`plataforma-lia/src/components/wsi/wsi-text-screening-modal.tsx` |
| 🟢 | `78a24ac21` | 2026-04-22 | Empty/merge | Task #795: Restaurar Vagas e estabilizar dev — - Restart lia-backend (8001 estava down, causando "Sem conexão") | — |
| 🟡 | `f1784016b` | 2026-04-22 | IA | chore(task-795): remove unrelated intent_heuristic.py added by parallel worktree | `lia-agent-system/app/tools/intent_heuristic.py` |
| 🟡 | `d0d140e0a` | 2026-04-22 | IA | Task #795: Restaurar Vagas e estabilizar dev — - Restart lia-backend (8001 estava down, causando "Sem conexão") | `lia-agent-system/app/tools/intent_heuristic.py` |
| 🟡 | `301714b24` | 2026-04-22 | Frontend (UI) | Task #795: Restaurar Vagas e estabilizar dev — - Restart lia-backend (8001 estava down, causando 'Sem conexão') | `plataforma-lia/src/app/[locale]/jobs/readiness/page.tsx`<br>`plataforma-lia/src/app/[locale]/vagas/prontidao/page.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🔴 | `c320409e5` | 2026-04-22 | Cross Back↔Front | Task #791: Remove Job Readiness Hub feature (frontend + backend) — Consolidates around the unified funnel view by fully removing the legacy | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/job_readiness.py`<br>`lia-agent-system/app/api/v1/job_vacancies/crud.py` |
| 🟢 | `4f84a55cf` | 2026-04-21 | Docs | Task #790: remove "Departamentos sao gerenciados em Usuarios & Departamentos" shortcut from Minha Empresa Hub — Cleanup of dead UX bridge from wave J.6 (Task #767). With Usuarios & Departamentos | `lia-agent-system/docs/FINAL_AUDIT.md` |
| 🟢 | `9e7ff39d2` | 2026-04-21 | Frontend (UI) | Task #790: remove "Departamentos sao gerenciados em Usuarios & Departamentos" shortcut from Minha Empresa Hub — Cleanup of dead UX bridge from wave J.6 (Task #767). With Usuarios & Departamentos | `plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx` |
| 🔴 | `6ce1b1898` | 2026-04-21 | Cross Back↔Front | Refactor "Minha Empresa" hub: contextual uploads + per-card progress — Original task #779: distribute document upload across section cards | `plataforma-lia/src/app/api/backend-proxy/documents/upload/route.ts`<br>`plataforma-lia/src/components/settings/MinhaEmpresaCard.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx` |
| 🔴 | `e03e9c7fa` | 2026-04-21 | Cross Back↔Front | task#765: JobVacancy.benefits ARRAY→JSONB with structured backfill — Backend | `lia-agent-system/alembic/versions/100_job_vacancy_benefits_jsonb.py`<br>`lia-agent-system/app/api/v1/job_vacancies/_shared.py`<br>`lia-agent-system/app/api/v1/job_vacancies/crud.py` |
| 🔴 | `843a0d224` | 2026-04-21 | Cross IA↔Front | Task #768 — Workforce planning: rich view + 3 conversational paths + HITL — Backend (lia-agent-system): | `lia-agent-system/app/domains/company_settings/domain.py`<br>`lia-agent-system/app/tools/tool_registry_metadata.yaml`<br>`plataforma-lia/src/components/settings/MinhaEmpresaCard.tsx` |
| 🟡 | `43981a976` | 2026-04-21 | Backend | Task #766: paridade Beneficios chat ↔ Hub no schema canonico — Chat e import de planilha/site agora aceitam TODOS os campos do modelo | `lia-agent-system/app/domains/company_settings/domain.py` |
| 🟢 | `90833f800` | 2026-04-21 | Frontend (UI) | Group benefits list by category with icon and count (Task #775) — - Updated `BenefitsListSection` to group benefits by `category` instead | `plataforma-lia/src/components/settings/benefits/BenefitsListSection.tsx` |
| 🔴 | `3045bdfdd` | 2026-04-21 | Cross Back↔Front | Task #767: remove Departamentos from "Minha Empresa" Hub + onboarding — Scope: | `lia-agent-system/app/domains/company_settings/domain.py`<br>`plataforma-lia/src/components/onboarding/OnboardingActionOrchestrator.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx` |
| 🟡 | `241d88f72` | 2026-04-21 | Backend | Persist enriched benefit fields via LIA chat tool — Task #776: the REST API and 4-layer schema (Postgres, SQLAlchemy, | `lia-agent-system/app/domains/company_settings/agents/company_tool_registry.py` |
| 🟢 | `32f29426f` | 2026-04-21 | Frontend (UI) | Task #760: Let recruiters click a highlighted glossary term to open the full reference — Original task: Task #759 made canonical glossary terms (WSI, BARS, Bloom...) hover-tooltipable | `plataforma-lia/src/components/chat/glossary-drawer.tsx`<br>`plataforma-lia/src/components/chat/glossary-highlighted-text.tsx` |
| 🟡 | `e44362638` | 2026-04-21 | Backend | E10 — Implementar geração de carta-proposta e fluxo de aceite (Task #718) — Adiciona o ciclo completo de Proposta & Negociação (E10), do draft ao | `lia-agent-system/alembic/versions/098_create_offer_proposals_table.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/approvals.py` |
| 🟢 | `5ecb4afde` | 2026-04-21 | Frontend (UI) | Task #758: Remove "Configurar Etapas" button from job header — - Removed the placeholder "Configurar Etapas" Button (and its toast | `plataforma-lia/src/components/pages/job-kanban/KanbanJobHeader.tsx` |
| 🟡 | `e090721ef` | 2026-04-21 | Backend | Task #716 — Salvar dados extraidos do site da empresa direto pelo chat (com confirmacao) — Implementacao backend do fluxo conversacional de duas fases para | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/company_settings/domain.py` |
| 🟡 | `a79295468` | 2026-04-21 | Cross IA↔Back | Task #730: Train meta-question router with new examples (PT-BR variations) — ## Original task | `lia-agent-system/app/orchestrator/meta_question_detector.py` |
| 🟢 | `7b2af8baa` | 2026-04-21 | Docs | Task #737: Catch repeated agent mistakes automatically before they ship — Wires the harness-engineering scan into automation so missing CLAUDE.md / | `.agents/skills/harness-engineering/SKILL.md`<br>`.agents/skills/harness-engineering/harness-baseline.json`<br>`.agents/skills/harness-engineering/scripts/scan_claude_md.py` |
| 🟢 | `271ddd5d8` | 2026-04-21 | Testes | Task #717: e2e regression coverage for the onboarding entry flow — Added plataforma-lia/e2e/tests/onboarding/onboarding-717.spec.ts with five | `plataforma-lia/e2e/tests/onboarding/onboarding-717.spec.ts` |
| 🟡 | `8afc623b0` | 2026-04-21 | Cross IA↔Back | Task #729 — Reconcile recruitment_campaigns schema drift (Alembic 097) — Original task: endpoint /api/v1/recruitment_campaigns?status=active was | `lia-agent-system/alembic/versions/097_reconcile_recruitment_campaigns_columns.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `8b4aca384` | 2026-04-21 | Backend | ci: enforce tool/action glossary freshness on PRs — Task #733 — wire up an automated gate so the tool/action glossary | `lia-agent-system/scripts/generate_tool_action_glossary.py` |
| 🟡 | `8a6a28cb9` | 2026-04-21 | Backend | Task #727: fix search_candidates LEFT JOIN bug + canonical service — Original bug: app/orchestrator/action_handlers/sourcing_actions.py | `lia-agent-system/app/domains/autonomous/agents/autonomous_tool_registry.py` |
| 🟡 | `8df3b51fe` | 2026-04-21 | Backend | Task #727: fix search_candidates LEFT JOIN bug + canonical service — Original bug: app/orchestrator/action_handlers/sourcing_actions.py | `lia-agent-system/app/domains/autonomous/agents/autonomous_tool_registry.py`<br>`lia-agent-system/tests/unit/test_search_candidates_handlers.py` |
| 🟡 | `5530d73ed` | 2026-04-21 | Backend | Task #727: fix search_candidates LEFT JOIN bug + canonical service — Original bug: app/orchestrator/action_handlers/sourcing_actions.py | `lia-agent-system/app/domains/autonomous/agents/autonomous_tool_registry.py`<br>`lia-agent-system/tests/unit/test_search_candidates_handlers.py` |
| 🟡 | `13076fceb` | 2026-04-21 | Cross IA↔Back | Task #727: fix search_candidates LEFT JOIN bug + canonical service — Original bug: app/orchestrator/action_handlers/sourcing_actions.py | `lia-agent-system/app/domains/ai/services/hybrid_search_service.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟢 | `fcca5b221` | 2026-04-21 | Empty/merge | docs: reorganize handoff index and mark glossary as auto-generated — Task #731 — Reorganize handoff docs and push branch to GitHub. | — |
| 🟢 | `cd03d1ebb` | 2026-04-21 | Docs | docs: reorganize handoff index and mark glossary as auto-generated — - Move lia-agent-system/DEVELOPER_HANDOFF.md into lia-agent-system/docs/ | `lia-agent-system/ARCHITECTURE.md`<br>`lia-agent-system/docs/DEVELOPER_HANDOFF.md`<br>`lia-agent-system/docs/GLOSSARIO_ACTIONS_TOOLS.md` |
| 🟡 | `c947826e6` | 2026-04-21 | Frontend (UI) | Task #723 — Auditoria Sparkles vs LIAIcon (Brain ciano = identidade LIA) — - Inventariadas 19 ocorrências do ícone `Sparkles` em produção e classificadas | `plataforma-lia/src/components/candidate-preview/PipelineDecisionBar.tsx`<br>`plataforma-lia/src/components/chat/proactive-hints-list.tsx`<br>`plataforma-lia/src/components/onboarding/SetupProgressBanner.tsx` |

### §6 Chat Unificado / Funil

**Descrição:** Saneamento P0 da cadeia de execução do chat unificado, Phase 2 chat sanitization para 5 domínios P1, zero actions sem tool nem handler, auto-discovery de AGENT_TYPE_TO_DOMAIN, funil unificado Fase 1 educativa + spec Fase 2, stub→real handlers.

**⚠️ Dependências para cherry-pick:** AGENT_TYPE_TO_DOMAIN auto-discovery | execute_action coverage 11/11 domínios

**Arquivos canônicos:** lia-agent-system/app/orchestrator/*, app/api/v1/agent_chat_ws.py, app/shared/chat_event_serializer.py

**Docs de referência:** BRANCH_MAP §6

- **Commits:** 48  |  **Período:** 2026-03-16 → 2026-04-22  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×21 🟡×20 🔴×7
- **Tags/Milestones:** `milestone/chat-saneamento-fase1-p0`, `milestone/funil-unificado-fase2`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `1e29040d2` | 2026-04-22 | Frontend (UI) | fix(funil): eliminate seed-candidate disappearance on transient network errors [Task #801] — Addresses 5 convergent root causes (deep audit) that caused "0 candidatos / | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟡 | `d0b1b75bb` | 2026-04-22 | Frontend (api/util) | fix(funil): eliminate seed-candidate disappearance on transient network errors [Task #801] — Addresses 5 convergent root causes (deep audit) that caused "0 candidatos / | `plataforma-lia/e2e/tests/smoke/smoke.config.ts`<br>`plataforma-lia/eslint.config.mjs`<br>`plataforma-lia/src/hooks/shared/use-notifications.ts` |
| 🟡 | `d7f273860` | 2026-04-22 | Frontend (UI) | fix(funil): eliminate seed-candidate disappearance on transient network errors [Task #801] — Addresses 5 convergent root causes (deep audit) that caused "0 candidatos / | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `4a53e019d` | 2026-04-21 | Frontend (UI) | Task #725: Reavaliar ícone do estágio 'enriquecida' no funil de vagas — Reavaliação do ícone do estágio `enriquecida` em `JOB_LIFECYCLE_STAGE_ICONS` | `plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |
| 🟢 | `f3ddab57b` | 2026-04-20 | Docs | docs(produto): especificação da Fase 2 do funil unificado — Task #593 — produzir o documento técnico-produtual que registra a | `docs/produto/funil-unificado-fase2.md` |
| 🟡 | `6d54e43d4` | 2026-04-20 | Frontend (UI) | Task #592: Funil unificado — Fase 1 (educativa) — Unificou o vocabulário e a identidade visual do funil entre o rail da home | `plataforma-lia/src/components/jobs/JobCampaignBadge.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/types.ts` |
| 🟡 | `521b9e243` | 2026-04-20 | Backend | Task #591: Encerra Task #580 (Saneamento Fase 1 P0 — chat unificado) — 5 fixes aplicados, todos validados pelo auditor + smoke test: | `lia-agent-system/eval/eval_runner.py`<br>`lia-agent-system/tests/test_chat_capabilities_smoke.py` |
| 🟡 | `5cf89193e` | 2026-04-20 | Backend | Task #591: Encerra Task #580 (Saneamento Fase 1 P0 — chat unificado) — 5 fixes aplicados, todos validados pelo auditor + smoke test: | `lia-agent-system/eval/eval_results_20260420_005410.json`<br>`lia-agent-system/tests/test_chat_capabilities_smoke.py` |
| 🟡 | `a174d7d67` | 2026-04-20 | Cross IA↔Back | Task #591: Encerra Task #580 (Saneamento Fase 1 P0 — chat unificado) — 5 fixes aplicados, todos validados pelo auditor + smoke test: | `lia-agent-system/app/domains/job_management/services/job_vacancy_lifecycle_service.py`<br>`lia-agent-system/app/domains/sourcing/domain.py`<br>`lia-agent-system/app/shared/compliance/protected_attributes.py` |
| 🟡 | `6ede7b7c9` | 2026-04-19 | Backend | Task #583: zero actions sem tool nem handler no chat unificado — Resolvi as 146 actions sem caminho de execução: o auditor agora | `lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/domains/analytics/domain.py`<br>`lia-agent-system/app/domains/ats_integration/domain.py` |
| 🟡 | `b1e9dc6bf` | 2026-04-19 | Backend | fix(sourcing): saneamento canônico do domínio (task #579) — Corrige 3 defeitos canônicos no Sourcing Domain detectados pela auditoria | `lia-agent-system/app/domains/sourcing/domain.py` |
| 🟡 | `421cfdb99` | 2026-04-19 | Backend | Task #580 — Saneamento da cadeia de execução do chat unificado (Fase 1, P0) — Eliminados handlers quebrados e agent-types órfãos nos 4 domínios críticos | `lia-agent-system/app/api/deps.py`<br>`lia-agent-system/app/api/routes.py` |
| 🔴 | `1122226d3` | 2026-04-19 | Cross Back↔Front | chore(chat): saneamento Fase 1 (P0) da cadeia de execução do chat unificado — Task #580 — auditoria programática havia detectado 81 handlers de tools com | `plataforma-lia/src/app/candidate/layout.tsx` |
| 🔴 | `0120f8d7e` | 2026-04-19 | Cross Back↔Front | Task #570: hardening P0/P1 das ações do chat unificado — Fecha as lacunas F1/F2/F3 documentadas no Apêndice A da auditoria #569 | `lia-agent-system/app/api/v1/lia_feedback.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🔴 | `f94022429` | 2026-04-19 | Cross Back↔Front | Task #570: hardening P0/P1 das ações do chat unificado — Fecha as lacunas F1/F2/F3 documentadas no Apêndice A da auditoria #569 | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/lia_feedback.py`<br>`lia-agent-system/app/api/v1/proactive_actions.py` |
| 🟢 | `3b9f715ac` | 2026-04-19 | Docs | docs(audit): auditoria das ações de mensagem do chat unificado e loop de aprendizado (Task #569) — Auditoria read-only escopada à Task #569. | `docs/audits/chat-message-actions-and-feedback-loop-audit.md` |
| 🟢 | `fd420cc96` | 2026-04-19 | Empty/merge | docs(audit): auditoria das ações de mensagem do chat unificado e loop de aprendizado (Task #569) — Auditoria read-only escopada à Task #569. | — |
| 🟡 | `3139e3e7f` | 2026-04-19 | Cross IA↔Back | docs(audit): auditoria das ações de mensagem do chat unificado e loop de aprendizado (Task #569) — Auditoria read-only escopada à Task #569. | `lia-agent-system/app/domains/company/services/company_scraper_service.py`<br>`lia-agent-system/app/orchestrator/precondition_checker.py` |
| 🟢 | `8140aa421` | 2026-04-19 | Docs | docs(audit): auditoria das ações de mensagem do chat unificado e loop de aprendizado (Task #569) — Auditoria read-only escopada à Task #569. | `docs/audits/chat-message-actions-and-feedback-loop-audit.md`<br>`replit.md` |
| 🟢 | `404f996a4` | 2026-04-17 | Docs | docs(funil-talentos): atualiza talent-funnel-search-flow.md — Correções de fidelidade ao código (apontadas no code review): | `docs/talent-funnel-search-flow.md` |
| 🟡 | `7fbf96adb` | 2026-04-17 | Backend | fix(funil): higiene final P2 — ws-token, kill-switch deprecation, dedup hooks (Task #298) — Endereça causas raiz #8, #9 e #10 de docs/audits/candidates-root-cause-2026-04-16.md. | `lia-agent-system/app/shared/rails_migration/deprecation.py` |
| 🔴 | `426701baa` | 2026-04-17 | Cross Back↔Front | fix(funil): higiene final P2 — ws-token, kill-switch deprecation, dedup hooks (Task #298) — Endereça causas raiz #8, #9 e #10 de docs/audits/candidates-root-cause-2026-04-16.md. | `lia-agent-system/app/shared/rails_migration/deprecation.py`<br>`plataforma-lia/src/app/api/auth/ws-token/route.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesQuery.ts` |
| 🟡 | `a65451070` | 2026-04-17 | Backend | Funil P1 — Tenant filter + erros sanitizados em /api/v1/candidates (task #295) — Causa raiz #4 da auditoria docs/audits/candidates-root-cause-2026-04-16.md. | `lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/domains/candidates/repositories/candidate_repository.py` |
| 🟡 | `869182118` | 2026-04-17 | Backend | Funil P1 — Tenant filter + erros sanitizados em /api/v1/candidates (task #295) — Causa raiz #4 da auditoria docs/audits/candidates-root-cause-2026-04-16.md. | `lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/domains/candidates/repositories/candidate_repository.py` |
| 🟢 | `5cf99eb62` | 2026-04-17 | Frontend (api/util) | Task #294 — Funil P0: proxy /search/candidates canônico                 + endurecimento do helper createProxyHandlers. — Substitui o hand-roll em | `plataforma-lia/src/lib/api/proxy-handler.ts` |
| 🟢 | `ee4cb7148` | 2026-04-17 | Frontend (UI) | Task #294 — Funil P0: proxy /search/candidates canônico. — Substitui o hand-roll em | `plataforma-lia/src/app/api/backend-proxy/search/candidates/route.ts` |
| 🟢 | `a785f05bb` | 2026-04-16 | Frontend (api/util) | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 da auditoria #287. | `plataforma-lia/src/app/[locale]/funil-de-talentos/__tests__/FunilDeTalentosClient.test.tsx`<br>`plataforma-lia/vitest.config.ts` |
| 🟢 | `4ba0483c5` | 2026-04-16 | Frontend (api/util) | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 da auditoria #287. | `plataforma-lia/src/hooks/candidates/use-candidates-list.ts`<br>`plataforma-lia/src/lib/api/auth-headers.test.ts`<br>`plataforma-lia/src/lib/api/auth-headers.ts` |
| 🟢 | `65fa3d2c7` | 2026-04-16 | Frontend (api/util) | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 da auditoria #287. | `plataforma-lia/src/lib/api/auth-headers.test.ts`<br>`plataforma-lia/src/lib/api/auth-headers.ts` |
| 🟢 | `60e4c824e` | 2026-04-16 | Frontend (api/util) | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 da auditoria #287. | `plataforma-lia/src/hooks/candidates/use-candidates-list.ts` |
| 🟡 | `cb2ee08c7` | 2026-04-16 | Backend | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 da auditoria #287. | `lia-agent-system/app/middleware/auth_enforcement.py`<br>`plataforma-lia/src/__tests__/i18n-pipeline-auth.test.ts` |
| 🟢 | `976d77632` | 2026-04-16 | Testes | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 da auditoria #287. | `lia-agent-system/tests/unit/test_auth_enforcement_dev_fallback.py` |
| 🔴 | `14d8e53a5` | 2026-04-16 | Cross Back↔Front | fix(auth): ciclo auth + relogin no Funil de Talentos (task #293) — Resolve causas raiz #1, #2 e #5 da auditoria #287. | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `0295b5e05` | 2026-04-16 | Frontend (UI) | Task #293 — Funil P0: ciclo de auth + relogin — Resolve as causas raiz #1, #2 e #5 da auditoria #287 para o Funil de | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `ebce04362` | 2026-04-16 | Frontend (UI) | Task #293 — Funil P0: ciclo de auth + relogin — Resolve as causas raiz #1, #2 e #5 da auditoria #287 para o Funil de | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🔴 | `2e2412e79` | 2026-04-16 | Cross Back↔Front | Task #293 — Funil P0: ciclo de auth + relogin — Resolve as causas raiz #1, #2 e #5 da auditoria #287 para o Funil de | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `030c32e55` | 2026-04-16 | Docs | docs(audits): root-cause audit for Funil de Talentos errors — Task #287 — investigative-only audit of "Erro ao carregar candidatos" / | `docs/audits/candidates-root-cause-2026-04-16.md` |
| 🟡 | `55aa8300b` | 2026-04-14 | Frontend (UI) | cleanup: remove legacy /funil page, redirect to /funil-de-talentos [PX08-082] Wave 6 item 6.2 — - Deleted src/app/[locale]/funil/ (page.tsx + layout.tsx) | `plataforma-lia/src/app/[locale]/funil/layout.tsx`<br>`plataforma-lia/src/app/[locale]/funil/page.tsx`<br>`plataforma-lia/src/app/[locale]/login/welcome/_components/WelcomeSteps.tsx` |
| 🟡 | `bad7cef4d` | 2026-04-14 | Frontend (UI) | Fix candidates not loading on Funil de Talentos page (Task #195) — ## Root cause fixes | `plataforma-lia/src/components/pages/candidates-page.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesTableArea.tsx` |
| 🟢 | `3ad20e2fe` | 2026-04-11 | Frontend (UI) | Add icons to Funil de Talentos tabs for visual consistency — - Added Lucide icons (Search, Heart, List, Bookmark, Database) to all | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `d40929942` | 2026-04-11 | Frontend (UI) | Strategic color points: Funil status filters, Alerts bell icon amber | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/components/pages/tasks/ActiveAlertsCard.tsx` |
| 🟢 | `2be93615c` | 2026-04-11 | Frontend (UI) | Fix: replace redundant stats bar with unique metrics (funil, entrevistas, conversao, risco) | `plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟡 | `e588274d4` | 2026-04-09 | Backend | fix: resolve Funil de Talentos hydration mismatch + fix backend attribute access — Frontend (root cause fix): | `lia-agent-system/app/api/v1/sourcing_agents.py`<br>`lia-agent-system/app/auth/models.py` |
| 🔴 | `a935f1f69` | 2026-04-09 | Cross Back↔Front | fix: resolve Funil de Talentos hydration mismatch causing infinite loading state — Root cause: Radix UI <Tabs> generates SSR/client baseId mismatches during | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/auth/models.py`<br>`lia-agent-system/app/auth/schemas.py` |
| 🟡 | `9aebc20f9` | 2026-04-05 | Frontend (UI) | feat: Padronizar Tip Cards do Funil de Busca (Task #150) — Padronizados todos os cards de "Dica:" nos modos de busca para visual | `plataforma-lia/src/components/expandable-ai-prompt/EAPExpandedSection.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/tabs/EAPTabBoolean.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/tabs/EAPTabJobDescription.tsx` |
| 🟢 | `d685c0088` | 2026-04-05 | Frontend (UI) | fix: Corrigir erros na página /funil/ (Vagas) - Task #148 — ## Mudanças de código | `plataforma-lia/src/components/pages/jobs/hooks/useJobsPageCore.ts` |
| 🟢 | `8bd407e84` | 2026-04-01 | Frontend (UI) | fix(typescript): resolve residual type errors in FunilDeTalentosClient, candidate-modal, ScreeningQuestionsPanel | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/components/candidate-modal.tsx`<br>`plataforma-lia/src/components/job-creation/ScreeningQuestionsPanel.tsx` |
| 🟡 | `a260fa9fe` | 2026-03-16 | Backend | fix: strip raw ReAct JSON from floating chat responses (WS + HTTP) — - Add _strip_react_json() to agent_chat_ws.py to extract 'response' field | `lia-agent-system/app/api/v1/agent_chat_ws.py` |

### Login UI (FE)

**Descrição:** Páginas de login, welcome, dev-auto-login.

**⚠️ Dependências para cherry-pick:** Auth provider config | dev-auto-login.ts (Task #384)

**Arquivos canônicos:** plataforma-lia/src/app/login/**, src/lib/auth/**

**Docs de referência:** —

- **Commits:** 41  |  **Período:** 2026-03-22 → 2026-04-13  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×39 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `d3539e216` | 2026-04-13 | Frontend (api/util) | Improve development login by simplifying token handling — Update the development login flow in the middleware to directly set the Authorization header and han | `plataforma-lia/src/middleware.ts` |
| 🟢 | `df7ce03b6` | 2026-04-11 | Frontend (UI) | Add a clear but subtle message about WeDO's ATS integration flexibility — Add a new paragraph to the login page in LoginClient.tsx to communicate that WeDO Talent can connect | `plataforma-lia/src/app/login/LoginClient.tsx` |
| 🟢 | `78d4dbf00` | 2026-04-09 | Frontend (UI) | Allow users to remain logged out after signing out — Modify the login page and middleware to respect the 'lia_logged_out' cookie, preventing automatic re | `plataforma-lia/src/app/login/LoginClient.tsx` |
| 🟡 | `e0405a9a3` | 2026-04-05 | Outro | Remove demo buttons and unnecessary routes from login page — Remove demo buttons and update routing configurations to streamline the login process. | `dump.rdb` |
| 🟢 | `cec051c3d` | 2026-04-03 | Frontend (UI) | Add a new onboarding flow explaining the recruitment process — Introduce a multi-step animation detailing the recruitment workflow before the user proceeds to the  | `plataforma-lia/src/app/login/welcome/page.tsx` |
| 🟢 | `3884f46fc` | 2026-04-03 | Frontend (UI) | Improve visibility and layout of login page elements — Adjust subtitle text styles for better readability and limit footer width on the login page. | `plataforma-lia/src/app/login/LoginClient.tsx` |
| 🟢 | `cd550ec7e` | 2026-04-03 | Frontend (UI) | Restore original login page design with two-step authentication flow — Reverts the login page to its initial design, reintroducing a two-step email/password authentication | `plataforma-lia/src/app/login/LoginClient.tsx` |
| 🟢 | `85ab54bf3` | 2026-04-03 | Frontend (UI) | Restore full login page with cloud background and SSO options — Update `LoginClient.tsx` to use the `LoginPage` component with `CloudsBackground`, while retaining J | `plataforma-lia/src/app/login/LoginClient.tsx` |
| 🟢 | `61b361b85` | 2026-03-30 | Frontend (UI) | fix: remove use client de useSessionTimeout.ts + login form completo + tsconfig strict | `plataforma-lia/src/app/login/page.tsx` |
| 🟡 | `58b131fa3` | 2026-03-30 | Frontend (UI) | forms: mascaras CPF/CNPJ/tel/CEP + MaskedInput + htmlFor/aria-describedby - fecha BCK-19 ALT-06 ALT-07 | `plataforma-lia/src/app/forgot-password/page.tsx`<br>`plataforma-lia/src/app/login/page.tsx`<br>`plataforma-lia/src/app/register/page.tsx` |
| 🟢 | `c4ad7d11b` | 2026-03-22 | Frontend (UI) | Update login page styling and dark mode support — Adjusted border-radius for inputs and error messages to `rounded-xl`, added dark mode variants for t | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `42af42d82` | 2026-03-22 | Frontend (UI) | Improve the visual hierarchy and elegance of the login page — Update the login page's sequence text font weight to 'light' and adjust layout for better readabilit | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `7d683641b` | 2026-03-22 | Frontend (UI) | Improve the visual presentation of login page elements — Break the sequence text into two lines, placing "Recrutamento simples" on its own line for emphasis. | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `fd3f36615` | 2026-03-22 | Frontend (UI) | Make headline text lighter and bolder for emphasis — Update the login page's main headline to use a lighter font weight for descriptive text and a bold w | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `01bb2fddc` | 2026-03-22 | Frontend (UI) | Improve the visual scale and readability of the login page — Adjusted typography sizes and spacing in the login page's left panel to improve visual hierarchy and | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `ae5802f2b` | 2026-03-22 | Frontend (UI) | Make the word "simples" bold to increase its visibility — Update the UI to make the word "simples" bold in the login page's descriptive text. | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `595f8da3c` | 2026-03-22 | Frontend (UI) | Make the AI name bold and remove italics for better visibility — Update the `page.tsx` file to change the `<span>` elements containing "LIA" from italicized Source S | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `bfb9ca3b3` | 2026-03-22 | Frontend (UI) | Update page appearance to use specific fonts and colors — Modify the login page to apply Source Serif 4 font to "LIA", change "simples" to cyan text color, an | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `04765f750` | 2026-03-22 | Frontend (UI) | Update Microsoft login button to use official logo — Replace placeholder 'M' button with an inline SVG of the official 4-color Microsoft logo for the "Co | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `5931be794` | 2026-03-22 | Frontend (UI) | Add social media links and copyright to the login page footer — Import Globe and Linkedin icons, update left panel content structure, and add a footer with social m | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `e1191ab57` | 2026-03-22 | Frontend (UI) | Center align footer text on the login page — Center align the footer text "A WeDoTalent é uma HRTech brasileira..." in the login page component b | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `e0dd09292` | 2026-03-22 | Frontend (UI) | Update recruitment platform login page with new messaging — Update the recruitment platform's login page, refining the headline, descriptive text, and badge to  | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `5a09e3c93` | 2026-03-22 | Frontend (UI) | Improve alignment of login page elements for better visual appeal — Adjusted the positioning of the logo and footer to absolute values, and modified the content centeri | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `fa48b1405` | 2026-03-22 | Frontend (UI) | Center the login card and move the footer text to the bottom — Adjust the layout of the login page to vertically center the login card and position the footer text | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `c9adfd3f9` | 2026-03-22 | Frontend (UI) | Move login page footer text to below the main card — Removes footer text from the left panel and repositions it below the login card in the right panel,  | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `fe827551c` | 2026-03-22 | Frontend (UI) | Reposition AI badge to the bottom of the right panel — Move the AI badge from above the headline in the left panel to below the login card in the right pan | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `a334b0570` | 2026-03-22 | Frontend (UI) | Add a badge with recruitment AI information above the headline — Add a new badge component to the login page displaying "Inteligência Artificial Agêntica para Recrut | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `6b9568369` | 2026-03-22 | Frontend (UI) | Center login prompts and remove footer links from the platform access card — Center the "Entrar na plataforma" and "Acesse sua conta para continuar" text elements within the log | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `846482f55` | 2026-03-22 | Frontend (UI) | Adjust logo size and position to improve alignment with text — Update logo container width to 230px and apply a negative left margin of -10px to align the WeDoTale | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `7bbed4417` | 2026-03-22 | Frontend (UI) | Update footer text to correct company name and capitalization — Corrected "WeDo Talent" to "WeDoTalent" and "Brasileira" to "brasileira" in the login page footer. | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `ff83a14f5` | 2026-03-22 | Frontend (UI) | Adjust text alignment and size for better logo proportion — Update the "TALENT" text styling in `page.tsx` to increase font size to 18px, adjust tracking to 0.1 | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `726c430ea` | 2026-03-22 | Frontend (UI) | Increase size and spacing of Talent logo text — Adjusted the font size and letter spacing for the 'talent' text within the login page component to b | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `62d773b34` | 2026-03-22 | Frontend (UI) | Align "TALENT" text to the right below logo — Update login page to right-align the "TALENT" text beneath the "weDO" logo in `page.tsx`. | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `1253e103a` | 2026-03-22 | Frontend (UI) | Add "TALENT" text below the company logo on the login page — Update the login page component to include the "TALENT" text below the "WeDo" logo, adjusting the lo | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `0a8513b6d` | 2026-03-22 | Frontend (UI) | Align logo and adjust its size on the login page — Update login page layout in `page.tsx` to align the WeDo logo to the left with consistent padding an | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `907ff29fb` | 2026-03-22 | Frontend (UI) | Restructure login process into two distinct steps for improved user experience — Refactor login page to implement a two-step authentication flow, separating email input from passwor | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `cf3d38140` | 2026-03-22 | Frontend (UI) | Make the recruitment future description text color cyan — Update the login page heading to make the word "simples." cyan and slim. | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `a236995a7` | 2026-03-22 | Frontend (UI) | Add animated cloud background and floating card login form — Introduce CloudsBackground component with framer-motion for animated clouds and update the login pag | `plataforma-lia/src/app/login/page.tsx`<br>`plataforma-lia/src/components/clouds-background.tsx` |
| 🟢 | `7e16b5d99` | 2026-03-22 | Frontend (UI) | Remove recruitment technology details from login screen — Remove descriptive text and bullet points related to AI recruitment from the left panel of the login | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `be887fa40` | 2026-03-22 | Frontend (UI) | Remove AI assistant card and screen dividing line — Removed the "Conheça a LIA" card and the dividing shadow from the login page in `src/app/login/page. | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `cc89ea23a` | 2026-03-22 | Frontend (UI) | Add a calming cloud background and transparent logo to the login page — Update the login page to include a CSS-generated cloud background gradient and use a transparent ver | `plataforma-lia/src/app/login/page.tsx`<br>`plataforma-lia/src/components/pages/login-page.tsx` |

### scope: phase2

- **Commits:** 41  |  **Período:** 2026-04-06 → 2026-04-07  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×40 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `3b6caaaf4` | 2026-04-07 | Backend | refactor(phase2): extract agent_templates/ai_consumption/shared_searches DB calls to repositories — - agent_templates.py: 9 direct DB calls → AgentTemplateRepository (get_by_id ×4, | `lia-agent-system/app/api/public/shared_searches.py`<br>`lia-agent-system/app/api/v1/agent_templates.py`<br>`lia-agent-system/app/api/v1/ai_consumption.py` |
| 🟡 | `c714b88c6` | 2026-04-07 | Backend | refactor(phase2): extract interview_analysis, communication_matrix, suggestions, experience_highlights DB calls to repositories — - InterviewAnalysisRepository: Interview read/update and LiaOpinion wr | `lia-agent-system/app/api/v1/automation/suggestions.py`<br>`lia-agent-system/app/api/v1/communication_matrix.py`<br>`lia-agent-system/app/api/v1/experience_highlights.py` |
| 🔴 | `5b9c855ca` | 2026-04-07 | Cross IA↔Back | refactor(phase2): extract API direct DB calls to repositories — batch 1 — Fully extracted (DB calls replaced with repo methods): | `lia-agent-system/app/api/v1/admin_compliance_fairness.py`<br>`lia-agent-system/app/api/v1/admin_templates.py`<br>`lia-agent-system/app/api/v1/agent_quality.py` |
| 🟡 | `bf6970eff` | 2026-04-07 | Cross IA↔Back | fix(phase2): classify API files as Rails-owned vs FastAPI-owned — - Annotated 2 API files as RAILS-DEPRECATED (wsi/reports.py, saturation.py) | `lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/api/v1/candidate_search/calibration.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py` |
| 🟡 | `17a065bc2` | 2026-04-06 | Backend | feat(phase2): migrate credits.py to CreditsRepository | `lia-agent-system/app/api/v1/credits.py`<br>`lia-agent-system/app/domains/credits/repositories/__init__.py`<br>`lia-agent-system/app/domains/credits/repositories/credits_repository.py` |
| 🟡 | `66ba9165c` | 2026-04-06 | Backend | feat(phase2): migrate admin.py to AdminRepository | `lia-agent-system/app/api/v1/admin.py`<br>`lia-agent-system/app/domains/admin/repositories/__init__.py`<br>`lia-agent-system/app/domains/admin/repositories/admin_repository.py` |
| 🟡 | `675c2b1d6` | 2026-04-06 | Backend | feat(phase2): migrate email_templates.py to EmailTemplatesRepository | `lia-agent-system/app/api/v1/email_templates.py`<br>`lia-agent-system/app/domains/email_templates/repositories/email_templates_repository.py` |
| 🟡 | `5de28d384` | 2026-04-06 | Backend | fix(phase2): clean residual SQLAlchemy imports in migrated controllers + migrate agent_memory.py — - ats.py: remove orphan sqlalchemy imports (update, AsyncSession) | `lia-agent-system/app/api/v1/agent_memory.py`<br>`lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/api/v1/billing.py` |
| 🟡 | `b7c778b37` | 2026-04-06 | Backend | feat(phase2): migrate email.py to EmailRepository | `lia-agent-system/app/api/v1/email.py`<br>`lia-agent-system/app/domains/communication/repositories/email_repository.py` |
| 🟡 | `d96c72d08` | 2026-04-06 | Backend | feat(phase2): migrate tasks.py to TasksRepository | `lia-agent-system/app/api/v1/tasks.py`<br>`lia-agent-system/app/domains/tasks/repositories/__init__.py`<br>`lia-agent-system/app/domains/tasks/repositories/tasks_repository.py` |
| 🟡 | `9b0057c7b` | 2026-04-06 | Backend | feat(phase2): clean approvals.py repo.db.execute + chore: remove from PENDING_MIGRATION (now 141) | `lia-agent-system/app/api/v1/approvals.py`<br>`lia-agent-system/app/domains/approvals/repositories/approvals_repository.py` |
| 🟡 | `cb84f02b3` | 2026-04-06 | Backend | feat(phase2): migrate approvals.py to ApprovalsRepository | `lia-agent-system/app/api/v1/approvals.py`<br>`lia-agent-system/app/domains/approvals/repositories/__init__.py`<br>`lia-agent-system/app/domains/approvals/repositories/approvals_repository.py` |
| 🟡 | `0b14a6e71` | 2026-04-06 | Backend | feat(phase2): migrate notifications.py to NotificationsRepository | `lia-agent-system/app/api/v1/notifications.py`<br>`lia-agent-system/app/domains/notifications/repositories/__init__.py`<br>`lia-agent-system/app/domains/notifications/repositories/notifications_repository.py` |
| 🟡 | `46e3c596b` | 2026-04-06 | Backend | feat(phase2): migrate communication.py to CommunicationRepository | `lia-agent-system/app/api/v1/communication.py`<br>`lia-agent-system/app/domains/communication/repositories/communication_repository.py` |
| 🟡 | `07eb6259d` | 2026-04-06 | Backend | feat(phase2): migrate billing.py to BillingRepository | `lia-agent-system/app/api/v1/billing.py` |
| 🟡 | `58653fdf8` | 2026-04-06 | Backend | feat(phase2): migrate job_vacancies/public.py to JobVacancyPublicRepository | `lia-agent-system/app/api/v1/job_vacancies/public.py`<br>`lia-agent-system/app/domains/job_management/repositories/job_vacancy_public_repository.py` |
| 🟡 | `32296f1c9` | 2026-04-06 | Backend | feat(phase2): migrate auth.py to AuthRepository | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/domains/auth/repositories/user_repository.py` |
| 🟡 | `a9ebf83c8` | 2026-04-06 | Backend | feat(phase2): migrate job_vacancies/crud.py to JobVacancyCRUDRepository | `lia-agent-system/app/api/v1/job_vacancies/crud.py` |
| 🟡 | `54e87646a` | 2026-04-06 | Backend | feat(phase2): migrate applications.py to ApplicationRepository | `lia-agent-system/app/api/v1/applications.py`<br>`lia-agent-system/app/domains/recruitment/repositories/application_repository.py` |
| 🟡 | `995d30786` | 2026-04-06 | Backend | feat(phase2): migrate screening.py to ScreeningRepository | `lia-agent-system/app/api/v1/screening.py` |
| 🟡 | `235ec864c` | 2026-04-06 | Backend | feat(phase2): migrate job_vacancies/lifecycle.py to JobVacancyLifecycleRepository | `lia-agent-system/app/api/v1/job_vacancies/lifecycle.py`<br>`lia-agent-system/app/domains/job_management/repositories/__init__.py`<br>`lia-agent-system/app/domains/job_management/repositories/job_vacancy_lifecycle_repository.py` |
| 🟡 | `1e34a7071` | 2026-04-06 | Backend | feat(phase2): migrate ats.py to ATSRepository | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/domains/ats_integration/repositories/__init__.py`<br>`lia-agent-system/app/domains/ats_integration/repositories/ats_repository.py` |
| 🟡 | `ef1a545b2` | 2026-04-06 | Backend | feat(phase2): migrate mailgun_webhooks.py to CommunicationRepository | `lia-agent-system/app/api/v1/mailgun_webhooks.py`<br>`lia-agent-system/app/domains/communication/repositories/communication_repository.py` |
| 🟡 | `7e32ecc0e` | 2026-04-06 | Backend | feat(phase2): migrate saas_metrics.py to SaasMetricsRepository | `lia-agent-system/app/api/v1/saas_metrics.py`<br>`lia-agent-system/app/domains/saas_metrics/repositories/__init__.py`<br>`lia-agent-system/app/domains/saas_metrics/repositories/saas_metrics_repository.py` |
| 🟡 | `90bb06cc1` | 2026-04-06 | Backend | feat(phase2): migrate trust_center.py to TrustCenterRepository | `lia-agent-system/app/api/v1/trust_center.py`<br>`lia-agent-system/app/domains/trust_center/repositories/__init__.py`<br>`lia-agent-system/app/domains/trust_center/repositories/trust_center_repository.py` |
| 🟡 | `46dd18dcc` | 2026-04-06 | Backend | feat(phase2): migrate company_culture.py to CompanyCultureRepository | `lia-agent-system/app/api/v1/company_culture.py`<br>`lia-agent-system/app/domains/company_culture/repositories/__init__.py`<br>`lia-agent-system/app/domains/company_culture/repositories/company_culture_repository.py` |
| 🟡 | `43c3e03cf` | 2026-04-06 | Backend | feat(phase2): migrate job_vacancies/analytics.py to JobVacanciesAnalyticsRepository | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/domains/job_vacancies_analytics/repositories/__init__.py`<br>`lia-agent-system/app/domains/job_vacancies_analytics/repositories/job_vacancies_analytics_repository.py` |
| 🟡 | `d8e3fa603` | 2026-04-06 | Backend | feat(phase2): migrate opinions.py to OpinionsRepository | `lia-agent-system/app/api/v1/opinions.py`<br>`lia-agent-system/app/domains/opinions/repositories/opinions_repository.py` |
| 🟡 | `9c2fa9f4f` | 2026-04-06 | Backend | feat(phase2): migrate health_check.py to HealthCheckRepository | `lia-agent-system/app/api/v1/health_check.py`<br>`lia-agent-system/app/domains/health_check/repositories/health_check_repository.py` |
| 🟡 | `92c94521d` | 2026-04-06 | Backend | feat(phase2): migrate integrations_hub.py to IntegrationsHubRepository | `lia-agent-system/app/api/v1/admin_settings.py`<br>`lia-agent-system/app/api/v1/integrations_hub.py`<br>`lia-agent-system/app/domains/admin_settings/repositories/__init__.py` |
| 🟡 | `622d15605` | 2026-04-06 | Backend | feat(phase2): migrate bulk_actions.py to BulkActionsRepository | `lia-agent-system/app/api/v1/bulk_actions.py`<br>`lia-agent-system/app/domains/bulk_actions/repositories/__init__.py`<br>`lia-agent-system/app/domains/bulk_actions/repositories/bulk_actions_repository.py` |
| 🟡 | `54b468a90` | 2026-04-06 | Backend | feat(phase2): migrate goals.py to GoalsRepository | `lia-agent-system/app/api/v1/goals.py`<br>`lia-agent-system/app/domains/goals/repositories/__init__.py`<br>`lia-agent-system/app/domains/goals/repositories/goals_repository.py` |
| 🟡 | `b96f0c6ff` | 2026-04-06 | Backend | feat(phase2): migrate technical_tests.py to TechnicalTestsRepository | `lia-agent-system/app/api/v1/technical_tests.py`<br>`lia-agent-system/app/domains/technical_tests/repositories/__init__.py`<br>`lia-agent-system/app/domains/technical_tests/repositories/technical_tests_repository.py` |
| 🟡 | `381813272` | 2026-04-06 | Backend | feat(phase2): migrate shared_searches.py to SharedSearchRepository | `lia-agent-system/app/api/v1/shared_searches.py`<br>`lia-agent-system/app/domains/shared_searches/repositories/__init__.py`<br>`lia-agent-system/app/domains/shared_searches/repositories/shared_search_repository.py` |
| 🟡 | `590707f9e` | 2026-04-06 | Backend | feat(phase2): migrate client_users.py to ClientUserRepository | `lia-agent-system/app/api/v1/client_users.py`<br>`lia-agent-system/app/api/v1/policy_engine.py`<br>`lia-agent-system/app/domains/client_users/repositories/__init__.py` |
| 🟡 | `a48c5d3c2` | 2026-04-06 | Backend | feat(phase2): migrate data_subject_requests.py to DataSubjectRepository | `lia-agent-system/app/api/v1/data_subject_requests.py`<br>`lia-agent-system/app/domains/data_subject/repositories/__init__.py`<br>`lia-agent-system/app/domains/data_subject/repositories/data_subject_repository.py` |
| 🟡 | `deea3c774` | 2026-04-06 | Backend | feat(phase2): migrate consent_management.py to ConsentRepository | `lia-agent-system/app/api/v1/consent_management.py`<br>`lia-agent-system/app/domains/consent/repositories/__init__.py`<br>`lia-agent-system/app/domains/consent/repositories/consent_repository.py` |
| 🟡 | `44923dea2` | 2026-04-06 | Backend | feat(phase2): migrate candidate_lists.py to CandidateListRepository | `lia-agent-system/app/api/v1/candidate_lists.py`<br>`lia-agent-system/app/domains/candidate_lists/repositories/__init__.py`<br>`lia-agent-system/app/domains/candidate_lists/repositories/candidate_list_repository.py` |
| 🟡 | `bbfe57323` | 2026-04-06 | Backend | feat(phase2): migrate journey_mapping.py to JourneyMappingRepository | `lia-agent-system/app/api/v1/journey_mapping.py`<br>`lia-agent-system/app/domains/journey_mapping/repositories/__init__.py`<br>`lia-agent-system/app/domains/journey_mapping/repositories/journey_mapping_repository.py` |
| 🟡 | `0d7556503` | 2026-04-06 | Backend | feat(phase2): migrate workforce.py to WorkforceRepository + fix broken string literals — - Created app/domains/workforce/repositories/workforce_repository.py | `lia-agent-system/app/api/v1/workforce.py` |
| 🟡 | `2d2273b1b` | 2026-04-06 | Backend | feat(phase2): migrate recruitment_journey.py to RecruitmentJourneyRepository | `lia-agent-system/app/api/v1/recruitment_journey.py` |

### Candidates (FE pages)

**Descrição:** Páginas e componentes de Candidatos no FE — listagem, filtros, busca, preview, página individual.

**⚠️ Dependências para cherry-pick:** Endpoint /api/backend-proxy/candidates/* | Hooks src/hooks/candidates

**Arquivos canônicos:** plataforma-lia/src/components/pages/candidates/**, src/components/candidate-preview/**, src/components/candidate-page/**

**Docs de referência:** —

- **Commits:** 36  |  **Período:** 2026-03-29 → 2026-04-21  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×28 🟡×5 🔴×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `a6e1c1743` | 2026-04-21 | Frontend (UI) | Improve error handling for transient network failures — Refactor `fetchWithRetry` to distinguish and handle transient network errors separately from actual  | `plataforma-lia/src/components/pages/candidates/hooks/candidates-core/useCandidatesData.ts` |
| 🟢 | `03a6fba31` | 2026-04-16 | Frontend (UI) | Improve error handling for various candidate search types — Add explicit error handling for non-OK HTTP responses in similar profile, job description, and arche | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts` |
| 🔴 | `57cbd5ad8` | 2026-04-13 | Frontend (UI) | Update terminology from "score" to "nota" throughout the application — Replace instances of "score" with "nota" in UI elements, variable names, and data structures to alig | `plataforma-lia/src/components/alerts/alert-settings-modal.tsx`<br>`plataforma-lia/src/components/alerts/kpi-alert-utils.ts`<br>`plataforma-lia/src/components/alerts/useKPIAlertSystem.ts` |
| 🟢 | `192e9a0d2` | 2026-04-12 | Frontend (UI) | Fix "Failed to fetch" on Jobs/Candidates — abort timeout + auto-recovery — Root cause: AbortController timeout in listJobVacancies() and | `plataforma-lia/src/components/pages/candidates/hooks/candidates-core/useCandidatesData.ts`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsData.ts` |
| 🟢 | `c99f4fa1d` | 2026-04-12 | Frontend (api/util) | Fix Jobs, Tasks, and Candidates pages data loading reliability — Changes: | `plataforma-lia/src/hooks/candidates/use-candidates-list.ts` |
| 🔴 | `c253385e1` | 2026-04-08 | Cross Back↔Front | Improve candidate search functionality by splitting multi-word queries — Fixes candidate search to correctly handle multi-word queries by splitting them into tokens and appl | `lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/domains/candidates/repositories/candidate_repository.py`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts` |
| 🟡 | `103cbac9a` | 2026-04-07 | Frontend (UI) | Update system to better handle candidate data and improve UI elements — Refactors candidate data handling, updates UI component properties, and adjusts generated mock-up co | `plataforma-lia/src/components/modals/useJobUnpublish.ts`<br>`plataforma-lia/src/components/modals/useJobUnpublishModal.ts`<br>`plataforma-lia/src/components/pages/JobsListContent.tsx` |
| 🟢 | `b0ff4498b` | 2026-04-07 | Frontend (UI) | Update styling and type casting for candidate table columns — Adjust color definitions in lia-expanded-prompt.tsx and perform type casting for table columns in ca | `plataforma-lia/src/components/lia-expanded-prompt.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesColumnConfig.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesTableConfig.ts` |
| 🟢 | `4add6c879` | 2026-04-06 | Frontend (UI) | Update function to properly set search prompt value — Update the `setLiaPromptValue` function to correctly handle state updates, ensuring the search promp | `plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx` |
| 🟢 | `a4c88add8` | 2026-04-06 | Frontend (UI) | Update candidate profile and search result views with type safety — Refactor `CandidatePageProfileTab.tsx` and `CandidateSearchResultsView.tsx` to improve type safety a | `plataforma-lia/src/components/candidate-page/CandidatePageProfileTab.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx` |
| 🟢 | `be6c7db17` | 2026-04-06 | Frontend (UI) | Improve candidate search functionality and filtering accuracy — Refactor search hooks to correctly handle and display location filters, update credit calculations,  | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearch.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearchComposition.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesUIState.ts` |
| 🟢 | `e6059dfef` | 2026-04-06 | Frontend (UI) | Update candidate search and message handling logic — Add ChatMessage type to various candidate-related hooks and stores for improved message handling. | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesArchetypes.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesCVHandlers.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts` |
| 🟢 | `2125061c8` | 2026-04-06 | Frontend (UI) | Update candidate search and chat functionalities for improved user experience — Refactors type definitions and function signatures in candidate search and chat hooks, specifically  | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesArchetypes.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesCVHandlers.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts` |
| 🟢 | `e213cf2ec` | 2026-04-03 | Frontend (UI) | Align search results header and controls into a single unified toolbar — Unify the Brain prompt, search results header, and search controls into a single horizontal toolbar  | `plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx` |
| 🟢 | `1fa2c5b9a` | 2026-04-03 | Frontend (UI) | Align search results header and LIA prompt horizontally — Move the LIA prompt button to the same line as the search results header and adjust flex properties  | `plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx`<br>`plataforma-lia/src/components/pages/candidates/SearchResultsHeader.tsx` |
| 🟢 | `3d0e70836` | 2026-04-03 | Frontend (UI) | Replace LIA input fields with a unified brain button component — Replaces various LIA input fields across multiple components with a new, reusable `LIAToolbarBrainBu | `plataforma-lia/src/components/pages/candidates/CompactLIAPrompt.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanToolbar.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `17fdb8833` | 2026-04-03 | Frontend (UI) | Update tab styling for consistent user interface appearance — Adjust border-radius and color classes in `components.css`, `CandidateTabs.tsx`, and `jobs-page.tsx` | `plataforma-lia/src/app/styles/components.css`<br>`plataforma-lia/src/components/pages/candidates/CandidateTabs.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `842e0b17a` | 2026-04-02 | Frontend (UI) | Add new options to the bulk actions bar and update search view imports — Update `CandidateSearchResultsView.tsx` to remove unused icons from lucide-react import and add new  | `plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx`<br>`plataforma-lia/src/components/ui/bulk-actions-bar.tsx` |
| 🟢 | `6a5ec5aa3` | 2026-04-02 | Frontend (UI) | Correct import statements that were incorrectly grouped — Fix incorrect import statements in LIASearchSidebarChat.tsx and SmartImportZone.tsx by separating sp | `plataforma-lia/src/components/pages/candidates/lia-sidebar/LIASearchSidebarChat.tsx`<br>`plataforma-lia/src/components/settings/SmartImportZone.tsx` |
| 🟢 | `0a1122876` | 2026-04-02 | Frontend (UI) | Align talent funnel table with job listings for consistent appearance — Adjust padding, checkbox component, and table borders in the CandidatesTable to match the JobsCompac | `plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx` |
| 🟢 | `1c4c56051` | 2026-04-02 | Frontend (UI) | Change header background color to white — Update the `SearchResultsHeader.tsx` component to change the background color from `bg-gray-50` to ` | `plataforma-lia/src/components/pages/candidates/SearchResultsHeader.tsx` |
| 🟢 | `15aea510d` | 2026-04-01 | Frontend (UI) | Improve table readability by adding subtle borders between rows — Add subtle bottom borders to table rows in CandidatesTable.tsx and JobsCompactTableView.tsx to enhan | `plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx`<br>`plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx` |
| 🟢 | `79ed5502d` | 2026-04-01 | Frontend (UI) | Update menu backgrounds to a lighter shade for improved readability — Adjust UI components to replace dark backgrounds with lighter grays, enhancing visual clarity and ad | `plataforma-lia/src/components/pages/candidates/CandidateTabs.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanJobHeader.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `cf2df9691` | 2026-04-01 | Frontend (UI) | Remove borders from the candidates table to match the jobs table — Remove borders and background color from the `thead` and `tbody` rows in `CandidatesTable.tsx` to en | `plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx` |
| 🟢 | `7782192f4` | 2026-04-01 | Frontend (UI) | Align job and candidate tabs with design system — Import and apply `tabStyles.pillActive` and `tabStyles.pill` from design tokens to the candidate and | `plataforma-lia/src/components/pages/candidates/CandidateTabs.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `9a9191215` | 2026-04-01 | Frontend (UI) | Update tab styling to fully rounded design — Adjusted the `rounded-lg` class to `rounded-full` in `CandidateTabs.tsx` and `jobs-page.tsx` to alig | `plataforma-lia/src/components/pages/candidates/CandidateTabs.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `51d4141d0` | 2026-04-01 | Frontend (UI) | Update candidate filtering interface with new placement and registration date options — Refactor CandidatesFilterPanel.tsx to remove legacy input fields and introduce new date filtering co | `plataforma-lia/src/components/pages/candidates/CandidatesFilterPanel.tsx` |
| 🟢 | `bb6597a1c` | 2026-04-01 | Frontend (UI) | Update candidate search view and filter panel components — Refactor CandidateSearchResultsView to remove redundant UI elements and improve type imports. Update | `plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesFilterPanel.tsx` |
| 🟢 | `7f2ff21cc` | 2026-03-31 | Frontend (UI) | Improve candidate page interactions and add migration guide — Update candidate page to enable email and WhatsApp links, refine opinion tab styling, and introduce  | `plataforma-lia/src/components/candidate-page/CandidatePageHeader.tsx`<br>`plataforma-lia/src/components/candidate-page/CandidatePageOpinionsTab.tsx`<br>`plataforma-lia/src/components/pages/candidates/CrossTabFilterBanner.tsx` |
| 🔴 | `2d2c29b23` | 2026-03-31 | Cross Back↔Front | chore: remove unused recommendation variable in _update_pipeline_stage | `lia-agent-system/app/services/triagem_session_service.py`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageHeader.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx` |
| 🟢 | `f732471d7` | 2026-03-31 | Frontend (UI) | Improve data handling and client management interfaces — Update data mapping in candidate lists and define a new interface for client administration to impro | `plataforma-lia/src/components/pages/candidates/hooks/candidates-core/useCandidatesData.ts`<br>`plataforma-lia/src/components/settings/settings-billing-tab.tsx` |
| 🟡 | `ea1205386` | 2026-03-30 | Frontend (UI) | fix: ensure 'use client' is first line in CandidateTabs.tsx and TableFiltersPanel.tsx | `plataforma-lia/src/components/pages/candidates/CandidateTabs.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesHeader.tsx`<br>`plataforma-lia/src/components/pages/candidates/SearchResultsHeader.tsx` |
| 🟡 | `f98a5711b` | 2026-03-30 | Frontend (UI) | docs: remove relatórios parciais (consolidados em frontend-audit-consolidado-20-dimensoes.md) | `plataforma-lia/src/components/pages/candidates/LIASearchSidebar.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/candidates-core/candidates-core.types.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesLIAHandlers.ts` |
| 🟡 | `09c2d5670` | 2026-03-30 | Frontend (UI) | Update candidate profile and files display with type improvements — Update type definitions and data handling for candidate profiles and files to improve type safety an | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/components/CandidatoActivitiesTab.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/components/CandidatoFilesTab.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/components/CandidatoOpinionsTab.tsx` |
| 🟡 | `5453c719b` | 2026-03-29 | Frontend (UI) | Update documentation diagram and improve application styling for dark mode — Synchronize the recruiter architecture diagram with the latest HTML documentation and enhance the us | `plataforma-lia/src/app/jobs/[id]/page.tsx`<br>`plataforma-lia/src/components/pages/candidates/ContactFilterConfirmModal.tsx`<br>`plataforma-lia/src/components/pages/candidates/DeleteArchetypeModal.tsx` |
| 🟢 | `d1a96355b` | 2026-03-29 | Frontend (UI) | Add search sorting functionality to candidate results view — Fix: Missing setSearchSortBy prop in CandidateSearchResultsView component parameter destructuring. | `plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx` |

### scope: guards

- **Commits:** 33  |  **Período:** 2026-04-06 → 2026-04-06  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×33

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `dea8da8ef` | 2026-04-06 | Backend | chore(guards): remove admin.py from PENDING_MIGRATION (now 137) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `f4ba91f19` | 2026-04-06 | Backend | chore(guards): remove email_templates.py from PENDING_MIGRATION (now 138) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `73fc18446` | 2026-04-06 | Backend | chore(guards): remove email.py from PENDING_MIGRATION (now 139) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `263171212` | 2026-04-06 | Backend | chore(guards): remove tasks.py from PENDING_MIGRATION (now 140) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `ae9748fbc` | 2026-04-06 | Backend | chore(guards): remove notifications.py from PENDING_MIGRATION (now 144) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `6efef88ef` | 2026-04-06 | Backend | chore(guards): remove communication.py from PENDING_MIGRATION (now 145) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `1bf5c7c0e` | 2026-04-06 | Backend | chore(guards): remove billing.py from PENDING_MIGRATION (now 146) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `0e3c3b6e3` | 2026-04-06 | Backend | chore(guards): remove job_vacancies/screening.py from PENDING_MIGRATION (now 147) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `98e679638` | 2026-04-06 | Backend | chore(guards): remove job_vacancies/public.py from PENDING_MIGRATION (now 148) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `595f759ae` | 2026-04-06 | Backend | chore(guards): remove auth.py from PENDING_MIGRATION (now 149) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `9f419de48` | 2026-04-06 | Backend | chore(guards): remove job_vacancies/crud.py from PENDING_MIGRATION (now 150) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `5a1fdcd1e` | 2026-04-06 | Backend | chore(guards): remove applications.py from PENDING_MIGRATION (now 151) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `d2aa0a07f` | 2026-04-06 | Backend | chore(guards): remove screening.py from PENDING_MIGRATION (now 152) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `4d00cb901` | 2026-04-06 | Backend | chore(guards): remove lifecycle.py from PENDING_MIGRATION (now 153) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `07094b34d` | 2026-04-06 | Backend | chore(guards): remove interviews.py from PENDING_MIGRATION (now 154) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `64f4b2da7` | 2026-04-06 | Backend | chore(guards): remove ats.py from PENDING_MIGRATION (now 155) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `2068c55ac` | 2026-04-06 | Backend | chore(guards): remove saas_metrics from PENDING_MIGRATION (now 156) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `b7fe1a503` | 2026-04-06 | Backend | chore(guards): remove trust_center from PENDING_MIGRATION (now 157) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `fc175970c` | 2026-04-06 | Backend | chore(guards): remove company_culture from PENDING_MIGRATION (now 158) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `f0c153e32` | 2026-04-06 | Backend | chore(guards): remove job_vacancies/analytics from PENDING_MIGRATION (now 159) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `c4460ddd2` | 2026-04-06 | Backend | chore(guards): remove opinions from PENDING_MIGRATION (now 160) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `6aae0cde2` | 2026-04-06 | Backend | chore(guards): remove health_check from PENDING_MIGRATION (now 161) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `fdc6eced4` | 2026-04-06 | Backend | chore(guards): remove chat from PENDING_MIGRATION (now 162) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `855b7a6e8` | 2026-04-06 | Backend | chore(guards): remove integrations_hub from PENDING_MIGRATION (now 164) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `c18a47e45` | 2026-04-06 | Backend | chore(guards): remove bulk_actions from PENDING_MIGRATION (now 165) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `9dd901c2c` | 2026-04-06 | Backend | chore(guards): remove goals from PENDING_MIGRATION (now 166) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `32e9d71e7` | 2026-04-06 | Backend | chore(guards): remove technical_tests from PENDING_MIGRATION (now 167) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `6e6a504dd` | 2026-04-06 | Backend | chore(guards): remove shared_searches from PENDING_MIGRATION (now 168) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `74499db11` | 2026-04-06 | Backend | chore(guards): remove client_users from PENDING_MIGRATION (now 170) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `d7287f9d5` | 2026-04-06 | Backend | chore(guards): remove data_subject_requests from PENDING_MIGRATION (now 171) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `d0283f01d` | 2026-04-06 | Backend | chore(guards): remove consent_management from PENDING_MIGRATION (now 172) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `00d139603` | 2026-04-06 | Backend | chore(guards): remove candidate_lists from PENDING_MIGRATION (now 173) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `eb2d19e86` | 2026-04-06 | Backend | fix(guards): add platform_event_handlers.py to PENDING_MIGRATION allowlist | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |

### Docs / Specs

**Descrição:** Specs técnicas — frontend, qa, e2e.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** docs/specs/**

**Docs de referência:** —

- **Commits:** 31  |  **Período:** 2026-03-24 → 2026-04-03  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×27 🔴×3 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `abd597571` | 2026-04-03 | Docs | Update documentation and benchmarks with recent test results — Apply fixes to improve scoring accuracy and update benchmark results to reflect recent changes. | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts`<br>`docs/specs/qa/CORRECOES_APLICADAS.md`<br>`docs/specs/qa/agents_benchmark_20260403_202628.csv` |
| 🔴 | `f059b6786` | 2026-04-03 | Cross IA↔Front | Improve job preview and communication channel appearance — Updates UI components to fix visual discrepancies in job previews and communication channels, includ | `lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py`<br>`plataforma-lia/src/app/api/backend-proxy/lia/[...path]/route.ts` |
| 🔴 | `9338f7773` | 2026-04-03 | Cross Back↔Front | Fix infinite loop in chat component state management — Wrap reset functions in useCallback to prevent re-renders and resolve the "Maximum update depth exce | `lia-agent-system/app/api/v1/wsi.py`<br>`plataforma-lia/src/app/api/backend-proxy/chat/route.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useFastTrackState.ts` |
| 🟢 | `08968515a` | 2026-04-03 | Docs | Update login script to use direct value setting with event dispatching for two-factor authentication code entry — Update wedo-login-v2.py to use a JavaScript evaluation to directly set the value of th | `docs/specs/qa/launch_agents.sh`<br>`plataforma-lia/docs/screenshots/session3/S3-final-2fa.png`<br>`plataforma-lia/docs/screenshots/session3/S3-final-result.png` |
| 🟡 | `195825178` | 2026-04-03 | Docs | Update login flow to handle WeDOTalent's direct 2FA authentication — Refactors `capture-wedo-ms-login.py`, `capture-wedo-s3.py`, `capture-wedotalent-session3.js`, `fill- | `capture-wedo-ms-login.py`<br>`capture-wedo-s3.py`<br>`capture-wedotalent-session3.js` |
| 🟢 | `c82e55f57` | 2026-04-03 | Docs | Update benchmark tests and documentation to reflect current API and features — Update benchmark test endpoints and payload schemas, adjust documentation regarding feature parity b | `docs/specs/qa/benchmark_agents.py`<br>`docs/specs/qa/patch_benchmark_agents.py`<br>`plataforma-lia/docs/audit-candidate-preview-qa.md` |
| 🔴 | `1a59d95d2` | 2026-04-03 | Testes | Update login and 2FA process to handle custom input components — Modify the authentication flow to specifically address issues with custom OTP input fields by using  | `docs/specs/qa/AGENT_PROCESS_TEST.md`<br>`docs/specs/qa/SMOKE_TEST_CHECKLIST.md`<br>`docs/specs/qa/test_agent_fairness.py` |
| 🟢 | `168babdef` | 2026-03-31 | Frontend (api/util) | Update technical documentation and configuration for improved clarity — Enhance technical documentation with detailed descriptions and update tsconfig.json. | `plataforma-lia/1000`<br>`plataforma-lia/tsconfig.json` |
| 🟢 | `7576f31a1` | 2026-03-31 | Docs | Add a glossary explaining technical components and step-by-step process details — Add a glossary section to the technical documentation explaining component types and providing a det | `docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md` |
| 🟢 | `1ec69a548` | 2026-03-31 | Docs | docs: v6.4 — remove all verbose Status comments and Task/ARCH references — Cleanup: | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `2375e5e01` | 2026-03-31 | Docs | docs: remove Section 11 (Respostas às Perguntas do Usuário) | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `093a5f772` | 2026-03-31 | Docs | docs: clean Section 7 — remove all resolved/implemented/complete items from priority map | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `22b99b243` | 2026-03-31 | Docs | docs: clean ANALISE_ROADMAP v6.2 — remove all resolved/strikethrough items | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `bf3a9db16` | 2026-03-31 | Docs | docs: Lista consolidada de gaps, itens a ativar e implementar (A1-A9, I1-I6, G1-G10) | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `372bd9edb` | 2026-03-31 | Docs | docs: Remover referência à seção de infraestrutura global (já removida) | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `9e9eb574f` | 2026-03-31 | Docs | docs: Remover seção INFRAESTRUTURA GLOBAL (sem IA) — contraditória | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `c08ca0e53` | 2026-03-31 | Docs | docs: Remover notas negativas em todas as seções + tabela de correspondência Ag↔código — - Convenção de nomes: substituída por tabela clara Rótulo/Classe/Domínio | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `5e85e2eb9` | 2026-03-31 | Docs | docs: Remover notas negativas do fluxo Alpha 1 (E3, E4) | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `34f55cfb6` | 2026-03-30 | Docs | docs: Inserir fluxo Alpha 1 v2 completo (diagrama ASCII) no início do documento | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `559d5d81f` | 2026-03-30 | Frontend (UI) | fix: Restore quick-action-chips className + add Comunicação matrix to Section 0 — - Fix broken className={} in quick-action-chips.tsx (pre-existing regression) | `plataforma-lia/src/components/ui/quick-action-chips.tsx` |
| 🟢 | `977c7f947` | 2026-03-30 | Frontend (api/util) | design-system: unifica tokens HSL shadcn → aliases para tokens LIA hex — fecha BCK-05 | `plataforma-lia/src/styles/design-tokens.css` |
| 🟢 | `e9276f9ef` | 2026-03-29 | Frontend (UI) | Improve font legibility and standardize text formatting across the platform — Update global CSS and layout configurations to remove hardcoded font sizes and transitions, standard | `plataforma-lia/src/app/globals.css`<br>`plataforma-lia/src/app/layout.tsx` |
| 🟢 | `4662d61ac` | 2026-03-29 | Frontend (UI) | Create reusable LiaPromptHeader component for consistent LIA prompt titles — - Created `lia-prompt-header.tsx` in `components/ui/` with standardized styling: | `plataforma-lia/src/components/pages/candidates/CandidateSearchBar.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx`<br>`plataforma-lia/src/components/pages/jobs/JobsDashboardView.tsx` |
| 🟢 | `f85817044` | 2026-03-29 | Frontend (UI) | Fix issues with displaying job listings and loading states — Update `JobsPage` component to properly render job listings, handling loading states, empty states,  | `plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `1c4f56e7e` | 2026-03-29 | Docs | Update component inventory with recent project growth metrics — Update the component inventory document to reflect recent project growth, including an increase in c | `docs/specs/frontend/INVENTARIO_COMPONENTES.md` |
| 🟢 | `17fcaa96f` | 2026-03-29 | Docs | Update implementation plan with current metrics and progress — Update the `PLANO_IMPLEMENTACAO_v2.md` file to reflect the latest progress on frontend development,  | `docs/specs/frontend/PLANO_IMPLEMENTACAO_v2.md` |
| 🟢 | `f79c266b9` | 2026-03-26 | Docs | Update onboarding document with correct specifications count — Corrected the number of specifications listed in the ONBOARDING.md file. | `docs/specs/process/ONBOARDING.md` |
| 🟢 | `3aacedc6b` | 2026-03-26 | Docs | Task start baseline checkpoint for code review | `docs/specs/ai/AI_ARCHITECTURE.md` |
| 🟢 | `1340756a4` | 2026-03-26 | Docs | Update platform documentation and create new technical specifications — Create 10 new specification documents for AI, Backend, and Frontend, and update the PLATFORM_MAP.md. | `docs/JIRA_CARD_CHAT_DESIGN_FIX.md`<br>`docs/PLATFORM_MAP.md`<br>`docs/specs/ai/AGENT_SPECS.md` |
| 🟢 | `a41c8d390` | 2026-03-24 | Docs | Update backend and frontend standards documentation based on GitHub repositories — Refactor backend and frontend standards documentation to exclusively use code from specified GitHub  | `docs/specs/standards/BACKEND_STANDARDS.md`<br>`docs/specs/standards/FRONTEND_STANDARDS.md` |
| 🟢 | `d77363cde` | 2026-03-24 | Docs | Add comprehensive frontend and backend coding standards documentation — Generate documentation for frontend (Vue 3, Nuxt, Vuetify) and backend (Ruby on Rails, FastAPI) codi | `docs/specs/standards/BACKEND_STANDARDS.md`<br>`docs/specs/standards/FRONTEND_STANDARDS.md` |

### Artefatos / Eval logs (sem código)

**Descrição:** audit_logs/ + eval_results_*.json — artefatos de execução do eval framework. Não são código de produto. Pode ignorar para cherry-pick.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** audit_logs/**, lia-agent-system/eval/eval_results_*.json

**Docs de referência:** —

- **Commits:** 30  |  **Período:** 2026-04-17 → 2026-04-28  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×30

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `e92a0b4c6` | 2026-04-28 | Backend | Update job management tool evaluation results and add new tests — Add evaluation results for job listing, pausing, and detail retrieval, including expected tools, suc | `lia-agent-system/eval/eval_results_20260428_093406.json` |
| 🟡 | `0c9b06319` | 2026-04-26 | Backend | Update evaluation results to include job management tests — Update evaluation results by adding test cases for job management functionalities, including listing | `lia-agent-system/eval/eval_results_20260426_122521.json` |
| 🟡 | `e97549bb1` | 2026-04-26 | Backend | Update job management evaluation results to reflect current system status — Update evaluation results for job management tasks, including initial connection failures and succes | `lia-agent-system/eval/eval_results_20260426_033230.json`<br>`lia-agent-system/eval/eval_results_20260426_091216.json` |
| 🟡 | `98781c699` | 2026-04-23 | Backend | Update job management evaluation results with new test cases — Add new test cases to the evaluation results for job management, including scenarios for listing all | `lia-agent-system/eval/eval_results_20260423_043216.json`<br>`lia-agent-system/eval/eval_results_20260423_054421.json`<br>`lia-agent-system/eval/eval_results_20260423_092619.json` |
| 🟡 | `2a35c08cb` | 2026-04-22 | Backend | Task start baseline checkpoint for code review | `lia-agent-system/eval/eval_results_20260422_123207.json` |
| 🟡 | `af6834854` | 2026-04-21 | Backend | Task start baseline checkpoint for code review | `lia-agent-system/eval/eval_results_20260421_203507.json` |
| 🟡 | `3e17624ea` | 2026-04-20 | Outro | Task #601: Conectar handlers quebrados de tools de chat aos serviços reais — Verified the work was already completed in Phase 2 (referenced as #582 in | `audit_logs/job_creation/2026/04/20/013769f1-9ee9-4158-ba80-524fbe22d3d3.json`<br>`audit_logs/job_creation/2026/04/20/21d07b06-c053-41a7-a787-e81195446367.json`<br>`audit_logs/job_creation/2026/04/20/57107cd4-6e5c-47e1-b0ef-fe23b0709fe5.json` |
| 🟡 | `f40e2c24c` | 2026-04-20 | Backend | Update audit logs and evaluation results to reflect job creation changes — Adds new entries to audit logs for job creation executions, including detailed execution information | `lia-agent-system/eval/eval_results_20260420_011218.json` |
| 🟡 | `fe9f7f329` | 2026-04-19 | Backend | Update evaluation results for job management tests — Update lia-agent-system/eval/eval_results_20260419_212710.json with new test results for job managem | `lia-agent-system/eval/eval_results_20260419_212710.json` |
| 🟡 | `a43abc1e9` | 2026-04-19 | Backend | Update evaluation results to reflect job listing and active job status — Adds new entries to the evaluation results JSON file, detailing the outcomes of tests for listing al | `lia-agent-system/eval/eval_results_20260419_125910.json` |
| 🟡 | `e3f6638ef` | 2026-04-19 | Backend | Update evaluation results with new test cases and responses — Add new entries to evaluation result JSON files, including detailed responses and metrics for candid | `lia-agent-system/eval/eval_results_20260419_123906.json`<br>`lia-agent-system/eval/eval_results_20260419_124422.json` |
| 🟡 | `64ffd1f4e` | 2026-04-19 | Backend | Update evaluation results with detailed performance and error metrics — Update JSON files in the `eval` directory to reflect benchmark results, including latency, HTTP stat | `lia-agent-system/eval/eval_results_20260419_122805.json`<br>`lia-agent-system/eval/eval_results_20260419_122813.json`<br>`lia-agent-system/eval/eval_results_20260419_122846.json` |
| 🟡 | `5e7eb3503` | 2026-04-19 | Backend | Task start baseline checkpoint for code review | `lia-agent-system/eval/eval_results_20260419_114812.json` |
| 🟡 | `ce89df880` | 2026-04-19 | Backend | Update evaluation results for job management and wizard functionalities — Add new entries to evaluation result files for job management and wizard agents, including prompts,  | `lia-agent-system/eval/eval_results_20260419_094828.json`<br>`lia-agent-system/eval/eval_results_20260419_095614.json` |
| 🟡 | `acaffae60` | 2026-04-19 | Backend | Add new test case for salary suggestion functionality — Add a new evaluation result to `eval_results_20260419_022322.json` for the "Salary suggestion for ne | `lia-agent-system/eval/eval_results_20260419_022322.json` |
| 🟡 | `eb0bf0e77` | 2026-04-19 | Backend | Update job management tool evaluation results and report findings — Adds evaluation results for job management tools, noting latency and response details for multiple t | `lia-agent-system/eval/eval_results_20260419_002514.json` |
| 🟡 | `17cf7d8ca` | 2026-04-18 | Backend | Update job management evaluation results with new test cases — Add new test cases to the evaluation results for job management, covering listing all jobs and listi | `lia-agent-system/eval/eval_results_20260418_203226.json` |
| 🟡 | `049f195be` | 2026-04-18 | Backend | Update job management task evaluations with authentication errors — Update `eval_results_20260418_192803.json` to include HTTP 401 errors for job management tasks, indi | `lia-agent-system/eval/eval_results_20260418_192803.json` |
| 🟡 | `ecdaccbbf` | 2026-04-18 | Backend | Update evaluation results to include detailed job listing tests — Appends detailed results for job listing tests to the evaluation JSON file, including latency and re | `lia-agent-system/eval/eval_results_20260418_171651.json` |
| 🟡 | `ff2bdc5c3` | 2026-04-18 | Backend | Add WSI job listing and active job evaluation results to the system — Update eval_results_20260418_160214.json with results for "List all jobs" (JM-001) and "List active  | `lia-agent-system/eval/eval_results_20260418_160214.json` |
| 🟡 | `fe71bb272` | 2026-04-18 | Backend | Add new job management evaluation tests — Update the evaluation results JSON file to include new tests for job management functionalities, suc | `lia-agent-system/eval/eval_results_20260418_151227.json` |
| 🟡 | `bfb9d2d95` | 2026-04-18 | Backend | Add job management categories to evaluation results — Update lia-agent-system/eval/eval_results_20260418_135838.json to include the "JM" category for job  | `lia-agent-system/eval/eval_results_20260418_135838.json` |
| 🟡 | `1ad4af6ab` | 2026-04-18 | Backend | Update job listing evaluation results with detailed findings — Adds evaluation results for job listing prompts, including API status, latency, and scores for listi | `lia-agent-system/eval/eval_results_20260418_121609.json` |
| 🟡 | `a0543748d` | 2026-04-18 | Backend | Update evaluation results for job management scenarios — Adds new test cases to `eval_results_20260418_110124.json` to evaluate the "List all jobs" and "List | `lia-agent-system/eval/eval_results_20260418_110124.json` |
| 🟡 | `eac05e8e3` | 2026-04-18 | Backend | Update job listing test results with new data and performance metrics — Adds detailed results for job listing tests, including API responses, latency, and success scores to | `lia-agent-system/eval/eval_results_20260418_102426.json` |
| 🟡 | `5906bbb55` | 2026-04-18 | Backend | Remove stray evaluation results file from agent system — Remove the `eval_results_20260418_092305.json` file from the `lia-agent-system/eval` directory. | `lia-agent-system/eval/eval_results_20260418_092305.json` |
| 🟡 | `350ae64fc` | 2026-04-18 | Backend | Remove unrelated evaluation results file from project — Delete the `eval_results_20260418_010408.json` file from the `lia-agent-system/eval` directory. | `lia-agent-system/eval/eval_results_20260418_010408.json` |
| 🟡 | `6e7f7df4a` | 2026-04-17 | Backend | Update evaluation results for job management functionalities — Update evaluation result files, showing HTTP 401 and HTTP 500 errors for job management API calls. | `lia-agent-system/eval/eval_results_20260417_225429.json`<br>`lia-agent-system/eval/eval_results_20260417_225631.json`<br>`lia-agent-system/eval/eval_results_20260417_230709.json` |
| 🟡 | `ee3824530` | 2026-04-17 | Backend | Add new evaluation results for job management scenarios | `lia-agent-system/eval/eval_results_20260417_184101.json` |
| 🟡 | `2e874a8a0` | 2026-04-17 | Backend | Add new evaluation results for job management scenarios — Update JSON files in `lia-agent-system/eval` with new test cases for job management functionalities. | `lia-agent-system/eval/eval_results_20260417_183121.json`<br>`lia-agent-system/eval/eval_results_20260417_183139.json` |

### Wizard (geral)

**Descrição:** Wizard de criação de vaga — Ondas 18-36. Tenant guards P0 (Frente A). Cleanup + Pydantic validators (Frente B+D). Serviços canônicos WsiQuestionGenerator + JdEnrichmentService (Frente C). Perguntas explícitas recrutador (seniority + WSI mode + calibração) (C.3). C.5 templates + F.1 ats_job_history + F.2 screening_mode. UX painéis Tezi: WizardCalibrationPanel + WizardJDReviewPanel + WizardWSIListPanel. TaskContextBar + chips contextuais + template UI. apply_learning + pick_canonical salary. wizard_step_response metadata.

**⚠️ Dependências para cherry-pick:** wizard_step_service estrutura por stage | apply_learning plugado em todos os stages | pick_canonical wired em salary | platform_manifest carregado

**Arquivos canônicos:** lia-agent-system/wizard_step_service/*, app/shared/wizard_suggestion_priority.py, plataforma-lia/src/components/wizard/*, src/components/wizard/panels/*

**Docs de referência:** BRANCH_MAP — Ondas 22-36

- **Commits:** 30  |  **Período:** 2026-03-16 → 2026-04-29  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×15 🟢×9 🔴×6

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `52b765969` | 2026-04-29 | Testes | Compare wizard panel implementations and suggest consolidation — Compares current and new wizard panel implementations, detailing differences in features, code, and  | `plataforma-lia/e2e/reports/wizard-panels-COMPARE.md` |
| 🟢 | `b12753549` | 2026-04-29 | Frontend (UI) | Update chat tests to use stable element selectors — Refactor end-to-end chat tests to utilize `data-rail-a-node` attributes for selecting stage elements | `plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟡 | `34cc893b2` | 2026-04-27 | Cross IA↔Back | audit: validação exaustiva pós-Rev 4 do wizard de criação de vaga — Auditoria final solicitada pelo usuário ("rode todas as skills, audita | `lia-agent-system/app/orchestrator/cascaded_router.py` |
| 🟡 | `9bf4f48db` | 2026-04-26 | Frontend (UI) | Wizard JD upload: subscribe to background_task_update WS events — Task #865 — wire the chat-surface JD upload step to the new async | `plataforma-lia/src/components/lia-float/BackgroundAgentsStatus.tsx`<br>`plataforma-lia/src/components/lia-float/BackgroundTaskNotification.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🔴 | `887cb1283` | 2026-04-26 | Frontend (UI) | Task #860 — Wizard Frontend Canonical-Fix Final (A-01, A-10) — Resolves audit findings A-01 (wizard state duplicated across surfaces) and | `plataforma-lia/src/components/calibration/CalibrationCandidateCard.tsx`<br>`plataforma-lia/src/components/calibration/adapters.ts`<br>`plataforma-lia/src/components/calibration/index.ts` |
| 🟡 | `b595f6833` | 2026-04-26 | Cross IA↔Back | Wizard OTLP — Fechar Lacuna de Observabilidade (N-07 + N-08) — Task #861. Fecha as duas pendências do gate operacional do ADR-019: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/_observability.py` |
| 🟡 | `2528738cf` | 2026-04-26 | Frontend (UI) | Wizard A11y — Focus Trap (A-08) + WCAG Contrast (A-09) — Resolves audit findings A-08 and A-09 from #837 (lente design/WCAG 2.1 AA), | `plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/unified-chat/OutreachCard.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/panels/BigFivePanel.tsx` |
| 🟡 | `f01469113` | 2026-04-26 | Backend | Wizard Hotfix — 410 Gone para NotImplementedError (Task #857, achados N-01/N-02) — Original task | `lia-agent-system/app/domains/ai/services/graph_runner.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_orchestrator_service.py` |
| 🔴 | `8bb8618ee` | 2026-04-26 | Cross IA↔Back | Task #850: Consolidate canonical job-creation wizard (round 6 — review polish) — Original task: Remove legacy backend (wizard_react_agent, job_wizard_graph, | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/health_langgraph.py` |
| 🟡 | `564c24ec8` | 2026-04-26 | Frontend (UI) | Task #836: Movimento 1 — faxina job-wizard + UX UnifiedChat — Faxina (~110KB de dead code): | `plataforma-lia/src/components/expanded-chat/FastTrackSuggestions.tsx`<br>`plataforma-lia/src/components/expanded-chat/stages/InputEvaluationStage.tsx`<br>`plataforma-lia/src/components/job-wizard/FastTrackReviewPanel.tsx` |
| 🟡 | `056a9aad3` | 2026-04-26 | Frontend (UI) | Improve wizard functionality and data privacy for multi-tenant environments — Implement LGPD-compliant localStorage namespacing for wizard state by userId, and enhance LinkCompon | `plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/index.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useWizardFlow.ts` |
| 🟢 | `817484f15` | 2026-04-26 | Frontend (UI) | Task #830 — Show "Plano de trabalho" card as completed when wizard finishes — Original task: when the job-creation wizard reaches `done`/`handoff`, the | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/wizard-plan-card.ts` |
| 🟢 | `83358e78f` | 2026-04-26 | Frontend (UI) | Unify "Criar nova vaga" wizard surface across chat and modal — UnifiedChat already showed the canonical wizard representation | `plataforma-lia/src/components/expanded-chat-modal.tsx` |
| 🔴 | `3a3183c77` | 2026-04-26 | Cross Back↔Front | Task #827 — Inject "Vaga publicada" closing card on wizard handoff — When the "Criar nova vaga" wizard reaches its terminal stage (handoff/done), | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/WizardPublishedJobCard.tsx` |
| 🟡 | `9e85e24e5` | 2026-04-26 | Frontend (UI) | Task #826 — Mount wizard plan card and progress bar in main chat feed — What changed | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/useWizardFlow.ts`<br>`plataforma-lia/src/components/unified-chat/wizard/wizard-plan-card.ts` |
| 🟢 | `2bb9bcbb6` | 2026-04-17 | Frontend (UI) | Wire FairnessGuard drop payload into the wizard runtime (Task #367) — The backend publishes `fairness_warning` and `dropped_questions` inside | `plataforma-lia/src/components/job-wizard/WizardContext.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/useWizardFlow.ts` |
| 🟢 | `e6a60db8d` | 2026-04-17 | Testes | test(job_creation): end-to-end wizard graph audit assertion — Adds tests/integration/test_job_creation_graph_e2e.py that drives the | `lia-agent-system/tests/integration/test_job_creation_graph_e2e.py` |
| 🟡 | `8d2e82b17` | 2026-04-14 | Backend | refactor: migrate 6 largest system prompts to YAML (batch 1) [P35-043] — Sprint 5 item 5.3 — Migrate inline Python system prompts to YAML-driven | `lia-agent-system/app/domains/company_settings/agents/company_system_prompt.py`<br>`lia-agent-system/app/domains/cv_screening/agents/pipeline_system_prompt.py`<br>`lia-agent-system/app/domains/hiring_policy/agents/policy_system_prompt.py` |
| 🟡 | `e0b3b08bf` | 2026-04-13 | Backend | chore: misc improvements alongside refactoring — Minor changes captured during F1-F7 refactoring across teams, | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/services/onboarding_orchestrator.py`<br>`lia-agent-system/app/services/twin_knowledge_indexer.py` |
| 🟡 | `9588ecadb` | 2026-04-12 | Cross IA↔Back | refactor: P1/P2 cleanup — remove 449 lines of dead code (AST-verified) — Dead code removed (10 functions, 0 callers each): | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`<br>`lia-agent-system/app/domains/job_management/services/job_context_service.py` |
| 🔴 | `7a1af0f32` | 2026-04-12 | Cross IA↔Front | feat: LIA Intelligence Overhaul — refactor prompt architecture for contextual responses — - Rewrote lia_persona.yaml as comprehensive SSOT (~200 lines): identity, | `lia-agent-system/app/api/v1/lia_assistant/conversational.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py` |
| 🟢 | `437afc8a8` | 2026-04-08 | Testes | Update tests for wizard step service to include shared components — Refactor unit tests for wizard_step_service to cover shared constants and helpers, and update import | `lia-agent-system/tests/unit/test_wizard_step_service_cov.py` |
| 🟡 | `e5600c8e6` | 2026-04-08 | Backend | refactor: DRY wizard_step_service — dict mapping, confidence helper, loop patterns (-97 lines) — - Replace 30-line if/elif entity mapping with _ENTITY_FIELD_MAP dict | `lia-agent-system/app/domains/job_management/services/wizard_step_service.py` |
| 🟡 | `b7bad168a` | 2026-04-08 | Backend | refactor: convert remaining 13 tool registries to @tool_handler decorator (-351 lines) — Converted: ats_integration, automation, communication, cv_screening/pipeline, | `lia-agent-system/app/domains/ats_integration/agents/ats_integration_tool_registry.py`<br>`lia-agent-system/app/domains/automation/agents/automation_tool_registry.py`<br>`lia-agent-system/app/domains/communication/agents/communication_tool_registry.py` |
| 🟡 | `3ee781e16` | 2026-04-07 | Backend | fix(tests): fix private exports, lia_config, job_report, and wizard imports — - Add _SCIPY_AVAILABLE to app/services/bias_audit_service.py shim | `lia-agent-system/app/api/v1/clients/__init__.py`<br>`lia-agent-system/app/api/v1/clients/clients_automations.py`<br>`lia-agent-system/app/api/v1/clients/clients_dashboard.py` |
| 🔴 | `879527074` | 2026-04-07 | Frontend (UI) | fix: complete recruitment-stages decomposition and address all code review findings — Changes from 4th code review rejection: | `plataforma-lia/src/app/aceitar-convite/AceitarConviteClient.tsx`<br>`plataforma-lia/src/app/ajuda/AjudaClient.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx` |
| 🔴 | `7419c32ac` | 2026-04-04 | Cross IA↔Back | task-124: Eliminar 23 Shims e Estabelecer Contracts Formais entre Camadas — ## What was done | `lia-agent-system/app/agents/base_agent.py`<br>`lia-agent-system/app/agents/nodes.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py` |
| 🟢 | `6453e744c` | 2026-04-01 | Frontend (UI) | fix(typescript): remove @ts-nocheck from WizardContext -- resolve type errors | `plataforma-lia/src/components/job-wizard/WizardContext.tsx` |
| 🟢 | `745590c79` | 2026-03-31 | Frontend (UI) | Update type for compensation analysis results — Update the type definition for the compensationAnalysis state variable to specifically use `Compensa | `plataforma-lia/src/components/job-wizard/stages/InputEvaluationStage.tsx` |
| 🟡 | `e948ba22d` | 2026-03-16 | Backend | fix: apply _strip_react_json to HITL resume paths + handle empty response edge case — - Strip ReAct JSON in wizard HITL resume path (agent_chat_ws.py) | `lia-agent-system/app/api/v1/agent_chat_ws.py` |

### Skills / canonical-fix

- **Commits:** 29  |  **Período:** 2026-03-19 → 2026-04-26  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×15 🟡×13 🔴×1
- **Tags/Milestones:** `milestone/canonical-fix-skill`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `28d1bd681` | 2026-04-26 | Docs | Refinar SKILL.md das 11 skills refatoradas — "Quando ativar" especifico — Task #785: cada SKILL.md das 11 skills refatoradas pela Task #778 agora tem | `.agents/skills/canonical-fix/SKILL.md`<br>`.agents/skills/design-patterns/SKILL.md`<br>`.agents/skills/design-standardize/SKILL.md` |
| 🔴 | `42dc490a5` | 2026-04-21 | Docs | Task #778 — Progressive disclosure em skills LIA — Aplica padrao de 3 niveis (SKILL.md enxuto + references/ + deep-dives/) em | `.agents/skills/SKILLS_INDEX.md`<br>`.agents/skills/canonical-fix/SKILL.md`<br>`.agents/skills/canonical-fix/references/01-quando-usar.md` |
| 🟢 | `850011b5d` | 2026-04-18 | Docs | Build cascade skills system for LIA platform — Transform .agents/skills/ from a passive collection into a self-recruiting | `.agents/skills/SKILLS_INDEX.md`<br>`.agents/skills/canonical-fix/SKILL.md`<br>`.agents/skills/feature-audit/SKILL.md` |
| 🟢 | `0a4170019` | 2026-04-18 | Docs | Criar skill canonical-fix (corrigir na origem, sem workaround) — Task #495 — Nova skill em .agents/skills/canonical-fix/SKILL.md com frontmatter | `.agents/skills/SKILLS_INDEX.md`<br>`.agents/skills/canonical-fix/SKILL.md`<br>`.agents/skills/feature-audit/SKILL.md` |
| 🟢 | `dcaf62128` | 2026-04-09 | Docs | Add detailed technical specification for skills inference and adjacency — Creates the `docs/specs/skills-adjacency-architecture.md` file, detailing the conceptual model, ESCO | `docs/specs/skills-adjacency-architecture.md` |
| 🟡 | `323a76519` | 2026-04-01 | Outro | Complete the Vue Vuetify standardization skill for independent operation — Rewrite the vue-vuetify-standardize skill to be self-contained, removing external dependencies and e | `=158`<br>`=235`<br>`=480` |
| 🟢 | `02131244a` | 2026-04-01 | Empty/merge | Rewrite vue-vuetify-standardize skill to be 100% self-contained — - Removed all references to external plataforma-lia files (00-design-system-v4.md, | — |
| 🟡 | `a52de9144` | 2026-04-01 | Frontend (UI) | Add new skill for standardizing Vue and Vuetify components — Introduce a new skill for Vue/Vuetify standardization, including a 10-step workflow and pre-step to  | `plataforma-lia/src/components/expanded-chat/hooks/useCalibrationAndFastTrackHandlers.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useCompanyConfigFetch.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useCompanyConfigLoader.ts` |
| 🟢 | `d223c0d67` | 2026-03-31 | Empty/merge | refactor: split JobFiltersSection 1245L + useExpandedChatModalCore 1239L — Skill 4 | — |
| 🟢 | `f8a129a95` | 2026-03-31 | Frontend (UI) | refactor: split LIASearchSidebar 1365L → chat/input sub-components — Skill 4 — - Extract LIASearchSidebarChat (chat messages + results scroll area) | `plataforma-lia/src/components/pages/candidates/LIASearchSidebar.tsx`<br>`plataforma-lia/src/components/pages/candidates/lia-sidebar/LIASearchSidebarChat.tsx`<br>`plataforma-lia/src/components/pages/candidates/lia-sidebar/LIASearchSidebarInput.tsx` |
| 🟢 | `b5e439be8` | 2026-03-31 | Empty/merge | refactor: split SSIModeContent 1323L → mode sub-componentes — Skill 4 | — |
| 🟡 | `2177e60a9` | 2026-03-31 | Frontend (UI) | refactor: split EAPTabContent 1275L → 4 tab sub-components — Skill 4 | `plataforma-lia/src/components/expandable-ai-prompt/EAPTabContent.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/tabs/EAPTabArquetipos.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/tabs/EAPTabBoolean.tsx` |
| 🟡 | `c434fb960` | 2026-03-31 | Frontend (UI) | refactor: split AdvancedFiltersModal 1379L → sections sub-componentes — Skill 4 | `plataforma-lia/src/components/search/advanced-filters-modal.tsx`<br>`plataforma-lia/src/components/search/filter-sections/FilterSectionFormacao.tsx`<br>`plataforma-lia/src/components/search/filter-sections/FilterSectionGeral.tsx` |
| 🟢 | `05e6350bf` | 2026-03-30 | Empty/merge | refactor: split useSmartSearchCore 1402L sub-hooks focados Skill 4 | — |
| 🟡 | `3c4866eed` | 2026-03-30 | Frontend (UI) | refactor: split SCMSectionContent (1482L) + ChatContextPanel (1378L) — Skill 4 monolith | `plataforma-lia/src/components/chat/ChatContextPanel.tsx`<br>`plataforma-lia/src/components/chat/ChatContextPanelPart1.tsx`<br>`plataforma-lia/src/components/chat/ChatContextPanelPart2.tsx` |
| 🟡 | `e3cab62dd` | 2026-03-30 | Frontend (UI) | design-tokens: substitui hardcoded hex por tokens LIA nos 15 arquivos mais críticos — Skill 3 BCK-10 | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/components/chat/agent-memory-indicator.tsx` |
| 🟢 | `eb0162475` | 2026-03-29 | Frontend (UI) | Add Excalidraw Diagram Generator skill and update goals management component — Installs the Excalidraw Diagram Generator skill and updates the GoalsManagement component, including | `plataforma-lia/src/components/settings/goals-management.tsx` |
| 🟢 | `62f3f6f66` | 2026-03-29 | Docs | Consolidate skills and update documentation to reflect changes — Update `.agents/skills/dei-fairness/SKILL.md`, `.agents/skills/wedo-governance/SKILL.md`, and `repli | `.agents/skills/dei-fairness/SKILL.md`<br>`.agents/skills/wedo-governance/SKILL.md`<br>`replit.md` |
| 🟡 | `692fd66a9` | 2026-03-29 | Frontend (UI) | Update candidate and job data structures and organize development skills — Refactor type definitions for candidates, jobs, and company data, and update replit.md to include a  | `plataforma-lia/src/components/pages/candidates/useCandidatesExecuteSearch.ts`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanTableView.tsx` |
| 🟡 | `e2def4a38` | 2026-03-27 | Frontend (UI) | Sprint 4.5 — Extração de modais: AddTechnicalSkill + AddCompetency + AddBenefit + SkipCompetenciesWarning + CalibrationProfileModal (-568 linhas no modal) | `plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/expanded-chat/modals/AddBenefitModal.tsx`<br>`plataforma-lia/src/components/expanded-chat/modals/AddCompetencyModal.tsx` |
| 🟡 | `082f349e9` | 2026-03-25 | Backend | Update skills catalog route to include correct path prefix — Correct the API route prefix for the skills catalog to resolve 404 errors and ensure accurate skill  | `lia-agent-system/app/api/v1/skills_catalog.py` |
| 🟢 | `5e78ea940` | 2026-03-23 | Empty/merge | fix(skills): preencher gaps de documentação nas skills de agente IA (Task #35) — Correções de numeração (bugs existentes): | — |
| 🟢 | `829371711` | 2026-03-23 | Empty/merge | fix(skills): preencher gaps de documentação nas skills de agente IA (Task #35) — Correções de numeração: | — |
| 🟢 | `f22ba3f54` | 2026-03-23 | Docs | fix(skills): corrigir numerações duplicadas + preencher gaps DS e backend — - wedo-governance: renomear §6 duplicado ('Referência Rápida') para §7 | `.agents/skills/dei-fairness/SKILL.md`<br>`.agents/skills/design-standardize/SKILL.md`<br>`.agents/skills/feature-audit/SKILL.md` |
| 🟢 | `b0aeb9aac` | 2026-03-23 | Docs | Update diagram to clarify orchestrator and skill relationships — Update docs/skills-diagram.html to reposition the feature-audit orchestrator above complementary ski | `docs/skills-diagram.html` |
| 🟡 | `be79c6ab6` | 2026-03-23 | IA | Update how candidate skills and traits are extracted and used — Enhance the WSI service to extract 5 technical and 5 behavioral competencies, adjust question genera | `lia-agent-system/app/domains/cv_screening/services/wsi_service.py` |
| 🟡 | `916bc3d3f` | 2026-03-22 | Outro | feat(skill): add PASSO 0 Intenção Estética to design-standardize skill — Task #32 — Skill design-standardize: adicionar PASSO 0 — Intenção Estética | `.cursor/rules/design-standardize.mdc` |
| 🟡 | `dc2e74ae7` | 2026-03-22 | Outro | feat(skill): add PASSO 0 Intenção Estética to design-standardize skill — Task #32 — Skill design-standardize: adicionar PASSO 0 — Intenção Estética | `.cursor/rules/design-standardize.mdc` |
| 🟡 | `61dff6be8` | 2026-03-19 | Infra/Config | Add commands to fetch repository and environment details — Add GitHub API calls to fetch repository information and capture environment variables. | `.claude/settings.local.json` |

### §7 WorkflowRail UX

**Descrição:** WorkflowRail UX redesign (5 iterações UX-1 a UX-7): compact single-line bar com hover popovers, scrollable, theme toggle, coexistência com Chat sem poluição, tracking de next-step clicks e panel toggles, thinking pulse no popover.

**⚠️ Dependências para cherry-pick:** Co-existência WorkflowRail × Chat sem conflito de espaço | Tracking events ativos

**Arquivos canônicos:** plataforma-lia/src/components/workflow-rail/*, src/components/chat/*

**Docs de referência:** UX_REDESIGN_COMPETITIVO_SPEC.md

- **Commits:** 28  |  **Período:** 2026-04-08 → 2026-04-20  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×17 🔴×6 🟡×5
- **Tags/Milestones:** `milestone/workflow-rail-ux7`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `e29756370` | 2026-04-20 | Testes | Add regression test for WorkflowRail thinking pulse (Task #655) — Adds an integration test at | `plataforma-lia/src/components/workflow-rail/__tests__/WorkflowRail.thinking.test.tsx` |
| 🟢 | `f16c79a62` | 2026-04-20 | Frontend (UI) | Show LIA's thinking pulse inside the WorkflowRail popover — Task #654 follows up on #653, which surfaced the workflow:thinking event | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🟢 | `d0c224c83` | 2026-04-20 | Frontend (UI) | Wire workflow:thinking event into WorkflowRail (Sprint UX-7) — Task #653 — Complete the WorkflowRail live-thinking pulse so the rail | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx`<br>`plataforma-lia/src/components/workflow-rail/useWorkflowRail.ts` |
| 🟢 | `ae21f9542` | 2026-04-20 | Frontend (UI) | feat(ui): redesign WorkflowRail floating ball + compact BetaBadge — Task #648: resolve visual collision between WorkflowRail's collapsed ball | `plataforma-lia/src/components/sidebar.tsx`<br>`plataforma-lia/src/components/ui/beta-badge.tsx` |
| 🔴 | `f2699be3f` | 2026-04-20 | Cross Back↔Front | feat(ui): redesign WorkflowRail floating ball + compact BetaBadge — Task #648: resolve visual collision between WorkflowRail's collapsed ball | `plataforma-lia/src/components/sidebar.tsx`<br>`plataforma-lia/src/components/ui/beta-badge.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🟢 | `b5455e013` | 2026-04-20 | Frontend (UI) | Track WorkflowRail next-step clicks and panel toggles (Task #589) — What | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx`<br>`plataforma-lia/src/components/workflow-rail/workflowRailAnalytics.ts` |
| 🟢 | `eafe4f551` | 2026-04-20 | Frontend (UI) | Task #617 — WorkflowRail × Chat: coexistência sem poluição — Faz o trilho de fluxo flutuante (barra/bolinha) coexistir com o trilho | `plataforma-lia/src/components/unified-chat/UnifiedChatConditional.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatEmptyState.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🟢 | `f027fa26e` | 2026-04-20 | Frontend (UI) | Fix WorkflowRail overlay blocking chat send button — Task #618: The WorkflowRail's centered row wrapper had `pointer-events-auto` | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🟢 | `9eccec89d` | 2026-04-20 | Frontend (UI) | Add a toggle button to control the workflow rail feature — Implement a new toggle button in the sidebar to enable/disable the workflow rail. The WorkflowRail c | `plataforma-lia/src/components/sidebar.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRailWrapper.tsx` |
| 🟢 | `86e997a8a` | 2026-04-20 | Frontend (UI) | Restore compact workflow rail with smaller design and theme toggle — Restores the WorkflowRail component to a previous version, reintroducing the compact design with 10p | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🟢 | `c07d3d5dc` | 2026-04-20 | Frontend (UI) | feat(workflow-rail): compact single-line bar with per-stage hover popovers and improved contrast — Task #612 — Compactar workflow rail no rodapé com hover por etapa e mais contraste | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🔴 | `bf0398f7a` | 2026-04-20 | Cross Back↔Front | Add a button to return to the chat from other sections — Adds a "Back to Chat" button to the workflow rail, visible on all pages except the chat itself. This | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRailWrapper.tsx`<br>`plataforma-lia/src/components/workflow-rail/workflowRailCatalog.ts` |
| 🔴 | `11389ca5e` | 2026-04-20 | Cross Back↔Front | Update workflow rail component to match BP7 design standards — Refactors the WorkflowRail component to align with BP7 design guidelines, including UI enhancements, | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🟡 | `11e1a9a3e` | 2026-04-20 | Backend | Add scrollable workflow rail with magnifier effect and theme toggle — Implement a horizontal scrolling workflow rail with a magnifier effect on hover, a side popover for  | `lia-agent-system/eval/eval_results_20260420_022715.json`<br>`lia-agent-system/eval/eval_results_20260420_022728.json` |
| 🟡 | `3adb6be16` | 2026-04-20 | Backend | Add three workflow rail variants optimizing usability — Adds three distinct workflow rail components (TrilhaClarity, TrilhaAffordance, TrilhaAccessibility)  | `lia-agent-system/app/domains/analytics/config/capabilities.yaml` |
| 🟡 | `734a98115` | 2026-04-20 | Backend | Add four distinct workflow rail variations for user selection — Introduce new React components for BreadcrumbContextual, CommandPalette, DockMagnified, and SidebarV | `lia-agent-system/app/prompts/domains/analytics.yaml` |
| 🟡 | `e19b79f7d` | 2026-04-20 | Backend | Add three compact workflow rail variations for user selection — Introduce three distinct mockup components for a compact WorkflowRail UI: UltraCompacto, ContrasteFo | `lia-agent-system/eval/eval_results_20260420_014809.json` |
| 🟢 | `a39b48d5f` | 2026-04-20 | Docs | docs(ux): UX_REDESIGN_COMPETITIVO_SPEC.md — especificacao tecnica completa (Sprints UX-1 a UX-7) | `plataforma-lia/UX_REDESIGN_COMPETITIVO_SPEC.md` |
| 🟡 | `536f3fc6b` | 2026-04-19 | Frontend (UI) | feat(workflow-rail): redesign WorkflowRail as a wide predictive funnel bar — Task #587 — Workflow Rail largo com próximos passos preditivos | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRailWrapper.tsx`<br>`plataforma-lia/src/components/workflow-rail/index.ts` |
| 🟢 | `780e40242` | 2026-04-18 | Frontend (UI) | Redesign WorkflowRail as floating pill above chat input (Task #483) — Replaces the full-width black bottom rail with a discreet floating pill | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx` |
| 🔴 | `fbc1187c5` | 2026-04-18 | Cross Back↔Front | feat(workflow-rail): add "Criar vaga" footer entry that triggers the wizard — Task #433: WorkflowRail now exposes a footer button that opens the | `plataforma-lia/src/components/pages/jobs/hooks/useJobsChat.ts` |
| 🟢 | `4a515f5df` | 2026-04-18 | Frontend (UI) | feat(workflow-rail): add "Criar vaga" footer entry that triggers the wizard — Task #433: WorkflowRail now exposes a footer button that opens the | `plataforma-lia/src/components/pages/jobs/hooks/useJobsChat.ts` |
| 🟢 | `9792ab69d` | 2026-04-18 | Frontend (UI) | feat(workflow-rail): add "Criar vaga" footer entry that triggers the wizard — Task #433: WorkflowRail now exposes a footer button that opens the | `plataforma-lia/src/components/pages/jobs/hooks/useJobsChat.ts`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRailWrapper.tsx` |
| 🟢 | `cfd50764d` | 2026-04-15 | Frontend (UI) | Task #199: Workflow Rail para Gêmeos Digitais - Onboarding UX — Redesigned the Digital Twins tab in Agent Studio with comprehensive | `plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/DigitalTwinComponents.tsx` |
| 🟢 | `951e4df07` | 2026-04-08 | Frontend (UI) | Safely handle empty or error responses from an API endpoint — Modify `useWorkflowRail.ts` to add checks for HTTP response status and body content before attemptin | `plataforma-lia/src/components/workflow-rail/useWorkflowRail.ts` |
| 🟢 | `6ccaf4826` | 2026-04-08 | Frontend (UI) | fix: add 'use client' to useWorkflowRail.ts (Next.js client component) | `plataforma-lia/src/components/workflow-rail/useWorkflowRail.ts` |
| 🔴 | `714711e5c` | 2026-04-08 | Cross Back↔Front | feat: integrate Phase 6 — auth, sidebar, pages, WorkflowRail — Item 1 — Auth: | `lia-agent-system/app/api/v1/digital_twins.py`<br>`lia-agent-system/app/api/v1/multi_strategy_search.py`<br>`lia-agent-system/app/api/v1/sector_templates.py` |
| 🔴 | `2e0c4c9d1` | 2026-04-08 | Cross IA↔Front | feat: Phase 6 — Agent Studio, Talent Pools, Workflow Rail, Digital Twins — 57 new files across lia-agent-system (FastAPI) and plataforma-lia (Frontend): | `lia-agent-system/alembic/versions/055_create_talent_pools.py`<br>`lia-agent-system/alembic/versions/056_create_sourcing_agents.py`<br>`lia-agent-system/alembic/versions/057_create_recruitment_campaigns.py` |

### i18n / Translation

- **Commits:** 27  |  **Período:** 2026-04-13 → 2026-04-20  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×16 🟡×10 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `8c0f30565` | 2026-04-20 | Frontend (UI) | feat(i18n): add automated i18n missing-key guardrail (#663) — ## Summary | `plataforma-lia/src/components/pages-agent-studio/custom-agents/ToolSelector.tsx` |
| 🟡 | `805502657` | 2026-04-19 | Cross IA↔Back | fix eval: UnboundLocalError in executor + short job_id in query_tools | `lia-agent-system/app/orchestrator/action_executor/executor.py` |
| 🟢 | `48134edf6` | 2026-04-18 | Frontend (UI) | Translate readiness blocker chips on the readiness hub page — Original task #456: ReadinessHubPage kept its own hardcoded Portuguese | `plataforma-lia/src/components/pages/jobs/readiness/ReadinessHubPage.tsx` |
| 🟢 | `8cd2e10cf` | 2026-04-18 | Frontend (UI) | Translate readiness stages and blockers to English — Task #451: Stage badge labels and blocker chips were hardcoded in | `plataforma-lia/src/components/pages/jobs/readiness/JobReadinessDrawer.tsx` |
| 🟢 | `4deeb4980` | 2026-04-17 | Frontend (api/util) | Fix PT/EN locale switch being overridden by middleware — Task #380: The Next.js middleware in `plataforma-lia/src/middleware.ts` | `plataforma-lia/src/middleware.ts` |
| 🟢 | `ff4f70448` | 2026-04-16 | Frontend (UI) | Fix login hero i18n rendering (Task #253) — The left-side hero phrase on /en/login and /pt-BR/login was rendering | `plataforma-lia/src/app/[locale]/login/LoginClient.tsx` |
| 🟢 | `f3af139b4` | 2026-04-15 | Frontend (UI) | fix: Digital Twins i18n namespace + design consistency (Task #201) — Problem 1 - Translation keys showing as raw text: | `plataforma-lia/src/components/pages-agent-studio/DigitalTwinComponents.tsx` |
| 🟢 | `320d8192e` | 2026-04-15 | Frontend (api/util) | Fix translation BR tag rendering on login page — Replace self-closing <br/> with <br></br> in login.heroTitle translation | `plataforma-lia/messages/en.json`<br>`plataforma-lia/messages/pt-BR.json` |
| 🟢 | `1800efed9` | 2026-04-14 | Frontend (api/util) | Redirect all English paths to Portuguese and update locale cookie — Modify middleware to redirect root and all English paths to Portuguese, ensuring the locale cookie i | `plataforma-lia/src/middleware.ts` |
| 🟡 | `861e8b6c2` | 2026-04-14 | Frontend (UI) | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT strings with next-intl t() calls | `plataforma-lia/src/components/pages-agent-studio/CalibrationCardModal.tsx` |
| 🟢 | `ad06793c3` | 2026-04-14 | Frontend (UI) | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT strings with next-intl t() calls | `plataforma-lia/src/components/pages-agent-studio/custom-agents/ToolSelector.tsx` |
| 🟡 | `8da34071b` | 2026-04-14 | Docs | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT strings with next-intl t() calls | `docs/audit/fase1-reconhecimento/FLOW_TRACES.md`<br>`docs/audit/fase1-reconhecimento/PLATFORM_MAP.md`<br>`docs/audit/fase1-reconhecimento/PROMPT_AUDIT.md` |
| 🟡 | `b6a53b820` | 2026-04-14 | Frontend (UI) | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT strings with next-intl t() calls | `plataforma-lia/src/components/pages-agent-studio/MultiStrategySearchPanel.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/VoiceScreeningButton.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/WizardAgentStep.tsx` |
| 🟡 | `40f82c150` | 2026-04-14 | Frontend (UI) | feat(i18n): complete Agent Studio i18n for all components — Task #194 — Replace all hardcoded PT strings with next-intl t() calls | `plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/CandidateOriginBadge.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/CustomAgentsTab.tsx` |
| 🟡 | `60da75302` | 2026-04-14 | Frontend (UI) | Task #194 T007: Complete i18n for all Agent Studio remaining components — - AgentsTab: STATUS_CONFIG → STATUS_CONFIG_KEYS with labelKey pattern; | `plataforma-lia/src/components/pages-agent-studio/AgentsTab.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/CalibrationCardModal.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/CandidateOriginBadge.tsx` |
| 🟡 | `288dc3b03` | 2026-04-14 | Frontend (UI) | Task #192: Complete i18n for Login, Dashboard/Chat, Sidebar, Vagas — chat-workflow-reels.tsx: | `plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/unified-chat/ChatSuggestionsPanel.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟢 | `4c041ad62` | 2026-04-14 | Frontend (UI) | Task #192: Complete i18n for chat-workflow-reels.tsx — - Replaced RECRUITMENT_STAGES/UTILITY_NODES arrays (hardcoded PT strings) with | `plataforma-lia/src/components/ui/chat-workflow-reels.tsx`<br>`plataforma-lia/src/components/unified-chat/ChatSuggestionsPanel.tsx`<br>`plataforma-lia/src/components/unified-chat/SmartSuggestions.tsx` |
| 🟢 | `d523e70b8` | 2026-04-14 | Frontend (UI) | Task #192: Complete i18n for remaining chat/jobs/sidebar components — Components updated with useTranslations (next-intl): | `plataforma-lia/src/components/pages/jobs/TableFiltersPanel.tsx`<br>`plataforma-lia/src/components/sidebar.tsx` |
| 🟡 | `cccc2ea75` | 2026-04-14 | Frontend (UI) | Task #192: Complete i18n for remaining chat/jobs components — Components updated with useTranslations (next-intl): | `plataforma-lia/src/components/pages/jobs/ColumnConfigPanel.tsx`<br>`plataforma-lia/src/components/pages/jobs/JobsHeader.tsx`<br>`plataforma-lia/src/components/unified-chat/ChatSuggestionsPanel.tsx` |
| 🟡 | `3c81c343f` | 2026-04-14 | Frontend (UI) | Task #192: Complete i18n translation for Login, Dashboard/Chat, Sidebar, Jobs — All scoped components now use next-intl translation keys: | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx`<br>`plataforma-lia/src/components/pages/jobs/TableFiltersPanel.tsx`<br>`plataforma-lia/src/components/sidebar.tsx` |
| 🟢 | `00a6b1465` | 2026-04-14 | Frontend (UI) | Task #192: Complete i18n translation for Login, Dashboard/Chat, Sidebar, Jobs — Translated components: | `plataforma-lia/src/app/[locale]/login/LoginClient.tsx`<br>`plataforma-lia/src/components/pages/JobsListContent.tsx`<br>`plataforma-lia/src/components/sidebar.tsx` |
| 🟡 | `0f1c15a80` | 2026-04-14 | Frontend (UI) | Task #192: Complete i18n translation for remaining components — Translated components: | `plataforma-lia/src/app/[locale]/login/LoginClient.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx`<br>`plataforma-lia/src/components/sidebar.tsx` |
| 🟢 | `848d9099d` | 2026-04-13 | Frontend (UI) | feat(i18n): add PT/EN language switcher to sidebar (Task #191) — - Create LanguageSwitcher component (src/components/language-switcher.tsx) | `plataforma-lia/src/components/language-switcher.tsx`<br>`plataforma-lia/src/components/sidebar.tsx` |
| 🟢 | `912ca851d` | 2026-04-13 | Docs | Update documentation to reflect current routing and i18n status — Update replit.md to accurately describe the absence of localized pathname mappings and deferred URL  | `replit.md` |
| 🟢 | `93851d544` | 2026-04-13 | Frontend (api/util) | feat(i18n): implement next-intl infrastructure with localized routes (Task #190) — - Install next-intl and configure createNextIntlPlugin in next.config.js | `plataforma-lia/src/i18n/routing.ts` |
| 🟢 | `d26f3251d` | 2026-04-13 | Frontend (api/util) | feat(i18n): implement next-intl infrastructure with localized routes (Task #190) — - Install next-intl and configure createNextIntlPlugin in next.config.js | `plataforma-lia/src/i18n/routing.ts`<br>`plataforma-lia/src/middleware.ts` |
| 🔴 | `764d08216` | 2026-04-13 | Frontend (UI) | feat(i18n): implement next-intl infrastructure with localized routes (Task #190) — - Install next-intl and configure createNextIntlPlugin in next.config.js | `plataforma-lia/src/app/[locale]/ClientBody.tsx`<br>`plataforma-lia/src/app/[locale]/accept-invitation/AcceptInvitationClient.tsx`<br>`plataforma-lia/src/app/[locale]/accept-invitation/layout.tsx` |

### Tasks #574-#712 (Janela anterior — chat/funil/glossário)

**Descrição:** Tasks da janela #574-#712 — chat unificado saneamento, funil unificado, glossário canônico, domains production-ready, candidate portal spec.

**⚠️ Dependências para cherry-pick:** Ver §6 Chat Unificado / §8 Glossário / §11 Candidate Portal

**Arquivos canônicos:** Diversos — depende da task específica

**Docs de referência:** BRANCH_MAP — Janela 2

- **Commits:** 25  |  **Período:** 2026-04-19 → 2026-04-21  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×16 🟢×5 🔴×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `6e16b83c9` | 2026-04-21 | IA | Integrate glossary term validation into agent system prompts at runtime — Task #700: SystemPromptBuilder now loads docs/GLOSSARY.md dynamically at | `lia-agent-system/app/shared/prompts/glossary_loader.py`<br>`lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `2de152df0` | 2026-04-21 | Backend | Wire send_email/send_whatsapp/schedule_interview to real dispatchers (Task #693) — Original task: Connect the three communication tools to the real | `lia-agent-system/app/domains/communication/services/communication_dispatcher.py` |
| 🔴 | `248df840c` | 2026-04-21 | Cross Back↔Front | fix(task-712): address review nits — single prefill + global broadcaster — 1) OnboardingActionOrchestrator.startStep: triggerAction ja despacha | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/auth/dependencies.py`<br>`lia-agent-system/app/auth/security.py` |
| 🟢 | `6a4b6844c` | 2026-04-21 | Empty/merge | Task #712 — fechar últimos 3 pontos da revisão — Original: conectar 100% do menu Configurações às 7 actions do | — |
| 🔴 | `132d74252` | 2026-04-21 | Cross Back↔Front | feat(task-712): close validation gaps — orchestrator, sync, two-phase, tests — Closes the 4 outstanding findings from the validation review: | `lia-agent-system/app/domains/company_settings/domain.py`<br>`plataforma-lia/src/app/[locale]/onboarding/page.tsx`<br>`plataforma-lia/src/components/dashboard-app.tsx` |
| 🟡 | `bbb362b8b` | 2026-04-20 | Backend | feat(task-712): real benefits write tool + handler delegation — - New _wrap_save_company_benefits in company_tool_registry.py: persists into | `lia-agent-system/app/domains/company_settings/domain.py` |
| 🔴 | `2e826f587` | 2026-04-20 | Cross Back↔Front | fix(task-712): align code with doc per code review (5 fixes) — - backend domain.py: configure_benefits returns clarification with navigation_hint | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/company_settings/domain.py`<br>`plataforma-lia/src/app/[locale]/onboarding/page.tsx` |
| 🟡 | `27aaa3461` | 2026-04-20 | Cross IA↔Back | Task #690: Enriquecer descrições de actions e tools com padrão rico (concluído) — ## O que foi feito | `lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| 🟡 | `4b95f2868` | 2026-04-20 | Backend | Task #670 — Proteger 8 dirs estratégicos e recategorizar — Original task: a auditoria Fase 2C marcava 8 dirs em `app/domains/` como | `lia-agent-system/scripts/audit_chat_capabilities.py` |
| 🟢 | `3ce45c7b3` | 2026-04-20 | Frontend (api/util) | Add missing insertTitle and insertAriaLabel translations for chat message actions — Task #661: Add missing insert-message button translations | `plataforma-lia/messages/en.json`<br>`plataforma-lia/messages/pt-BR.json` |
| 🟢 | `03440865d` | 2026-04-20 | Frontend (UI) | Task #650: BETA badge polish + hide chat/rail on auth routes — Changes: | `plataforma-lia/src/components/ui/beta-badge.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatConditional.tsx`<br>`plataforma-lia/src/components/workflow-rail/WorkflowRailWrapper.tsx` |
| 🟢 | `93a88173b` | 2026-04-20 | Frontend (UI) | Persist recruiter's last active funnel stage across sessions — Task #588: The WorkflowRail wide bar derived its "current stage" purely | `plataforma-lia/src/components/workflow-rail/WorkflowRail.tsx`<br>`plataforma-lia/src/components/workflow-rail/lastStageStorage.ts`<br>`plataforma-lia/src/components/workflow-rail/useWorkflowRail.ts` |
| 🟢 | `b3d068c9c` | 2026-04-20 | Testes | Add CI smoke test for chat capabilities audit (Task #633) — Wraps `lia-agent-system/scripts/audit_chat_capabilities.py` in a pytest so | `lia-agent-system/tests/test_chat_capabilities_audit_ci.py` |
| 🟡 | `7670dfb5b` | 2026-04-20 | Backend | Task #609 — Mostrar campanhas reais no rail e no badge — Replace the placeholder `not_implemented` body of GET | `lia-agent-system/app/api/v1/recruitment_campaigns.py` |
| 🟡 | `ceb6c78fa` | 2026-04-20 | Cross IA↔Back | Fix stale import paths across backend (task #585) — Followed up on task #581 (which fixed a single `app.config.database` → | `lia-agent-system/app/api/v1/onboarding.py`<br>`lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/api/v1/whatsapp_webhook.py` |
| 🟡 | `43d9891d3` | 2026-04-20 | Cross IA↔Back | Wire up duplicate_job and clone_job chat actions (Task #624) — Original task: finish the deferred 'duplicate_job' and 'clone_job' chat | `lia-agent-system/app/domains/job_management/domain.py`<br>`lia-agent-system/app/tools/job_tools.py` |
| 🟡 | `9bbb304be` | 2026-04-20 | Backend | Task #623: Remove unused 'score_cv' chat tool from cv_screening domain — The score_cv tool was a thin chat-registry indirection over | `lia-agent-system/app/domains/cv_screening/domain.py`<br>`lia-agent-system/app/domains/cv_screening/services/cv_scoring_service.py` |
| 🟡 | `92e6fe1c8` | 2026-04-20 | Backend | Replace recruiter-goals stub with real OKR/quota analytics (Task #599) — The `assistant_track_goals` chat tool resolved to | `lia-agent-system/app/services/goal_service.py` |
| 🟡 | `985cb54bd` | 2026-04-20 | Backend | Restore Sourcing ReAct agent's full tool set — Task #596: The Sourcing ReAct agent's `_aggregate_all_tool_names` helper | `lia-agent-system/app/domains/sourcing/agents/sourcing_react_agent.py` |
| 🟡 | `fbe592761` | 2026-04-20 | Backend | Task #604: Padronizar identidade dos domínios para usar atributos simples — Original task: JobCreationDomain expunha domain_id/domain_name/description | `lia-agent-system/app/domains/job_creation/domain.py` |
| 🟡 | `42c9ce4d2` | 2026-04-20 | Backend | Task #602: Replace stub/fallback handlers with real implementations or explicit errors — - agent_studio/domain.py | `lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/domains/candidate_self_service/domain.py`<br>`lia-agent-system/app/domains/company_settings/domain.py` |
| 🟡 | `bd974aea4` | 2026-04-20 | Cross IA↔Back | Task #620: Surface ReAct tool calls on the chat HTTP response (LIA-LCF-01) — When recruiters asked vacancy questions ("quantos candidatos tem a vaga V0037?"), | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟡 | `09951594f` | 2026-04-20 | Backend | Task #591 — Encerrar #580 com qualidade (5 achados de code review) — Original: code review da #580 rejeitou o saneamento Fase 1 P0 da cadeia de | `lia-agent-system/app/domains/sourcing/tools/query_tools.py`<br>`lia-agent-system/tests/security/test_compare_candidates_tenant_isolation.py`<br>`lia-agent-system/tests/test_chat_capabilities_smoke.py` |
| 🔴 | `22d0f1da4` | 2026-04-19 | Cross IA↔Back | Task #582: Phase 2 chat sanitization for the 5 P1 domains — Make every chat tool registered in ats_integration, automation, | `lia-agent-system/app/domains/ats_integration/domain.py`<br>`lia-agent-system/app/domains/ats_integration/services/ats_sync_service.py`<br>`lia-agent-system/app/domains/automation/domain.py` |
| 🟡 | `d312e34dd` | 2026-04-19 | Cross IA↔Back | Task #584 — Auto-discovery of AGENT_TYPE_TO_DOMAIN — Replaces the hand-maintained dict in app/orchestrator/domain_mappings.py with | `lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/domains/analytics/domain.py`<br>`lia-agent-system/app/domains/ats_integration/domain.py` |

### Automations

- **Commits:** 24  |  **Período:** 2026-03-31 → 2026-04-28  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×16 🔴×4 🟡×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `566d1ac89` | 2026-04-28 | Testes | test(automations): fix MESSAGES namespace automations -> automationsTab, 7/7 green | `plataforma-lia/src/components/settings/recruitment/__tests__/automations-tab.test.tsx` |
| 🔴 | `9477be72f` | 2026-04-28 | Cross Back↔Front | Update recruitment automations with new data fetching and testing — Refactor AutomationsTab component to fetch real automation data from API and add corresponding unit  | `plataforma-lia/src/components/settings/recruitment/automations-tab.tsx` |
| 🟡 | `5eee537b9` | 2026-04-11 | Backend | feat: add admin platform endpoints (webhooks, automation, health, version) — 5 new endpoints consumed by wedotalent-admin-copia frontend: | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/admin_platform.py` |
| 🔴 | `d110a2a22` | 2026-04-07 | Cross IA↔Front | Update chat and automation services for improved functionality — Refactors service dependencies and WebSocket proxy configuration in the chat application. | `lia-agent-system/app/api/v1/applications.py`<br>`lia-agent-system/app/api/v1/automation/_shared.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers.py` |
| 🟡 | `3cc91ac2a` | 2026-04-06 | Backend | Task #37: Implement Event Handlers + Post-screening Automation — Implemented 5 platform event handlers in platform_event_handlers.py: | `lia-agent-system/app/api/v1/platform_event_handlers.py` |
| 🟡 | `35a7a201c` | 2026-04-06 | Backend | Task #37: Implement Event Handlers + Post-screening Automation — Implemented 5 platform event handlers in platform_event_handlers.py: | `lia-agent-system/app/api/v1/platform_event_handlers.py` |
| 🟡 | `140d09d0e` | 2026-04-06 | Backend | Task #37: Implement Event Handlers + Post-screening Automation — Implemented 5 platform event handlers in platform_event_handlers.py: | `lia-agent-system/app/api/v1/platform_event_handlers.py`<br>`lia-agent-system/app/api/v1/workforce.py` |
| 🔴 | `b7c41231d` | 2026-04-06 | Cross IA↔Back | Task #37: Implement Event Handlers + Post-screening Automation — Implemented 5 platform event handlers in platform_event_handlers.py: | `lia-agent-system/app/api/v1/admin_settings.py`<br>`lia-agent-system/app/api/v1/admin_templates.py`<br>`lia-agent-system/app/api/v1/alerts.py` |
| 🟢 | `d31c81646` | 2026-03-31 | Empty/merge | fix(task70): complete Celery automations — all review blockers resolved — Commits dda84a29 through 2f6b6cef for Task #70: | — |
| 🟢 | `31fce4c95` | 2026-03-31 | Empty/merge | fix(task70): complete Celery automations — all review blockers resolved — All commits for Task #70 (dda84a29 through ff0e76b5): | — |
| 🟢 | `dd33a33ae` | 2026-03-31 | Frontend (UI) | fix(task70): complete Celery automations with all review blockers resolved — All commits (dda84a29 through eba78a73) for Task #70: | `plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` |
| 🟢 | `3662560cd` | 2026-03-31 | Frontend (UI) | fix(task70): complete Celery automations — all review blockers resolved — Commits dda84a29 through 0d84e38c: | `plataforma-lia/src/components/kanban/types.ts`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` |
| 🟢 | `1ceb481b0` | 2026-03-31 | Frontend (UI) | fix(task70): resolve all code review blockers for Celery automations — Commits dda84a29 through 2b1bd7d8: | `plataforma-lia/src/components/pages/chat-page/types.ts`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` |
| 🟢 | `5d951e4b3` | 2026-03-31 | Empty/merge | fix(task70): resolve all code review blockers for Celery automations — Commits dda84a29, 3912e87b, f9ce6242: | — |
| 🟢 | `3bd4ca4f0` | 2026-03-31 | Empty/merge | fix(task70): resolve all code review blockers for Celery automations — Fixes in commits dda84a29 and 3912e87b: | — |
| 🟢 | `fd62e49b7` | 2026-03-31 | Empty/merge | fix(task70): resolve 3 code review blockers for Celery automations — 1. Template Learning: rewrite to persistent SQL queries using | — |
| 🟢 | `2efee4bbc` | 2026-03-31 | Frontend (UI) | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Seven commits pushed to GitHub: | `plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatModalCore.tsx` |
| 🟢 | `0afda78ee` | 2026-03-31 | Empty/merge | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Six commits pushed to GitHub: | — |
| 🟢 | `1c1843928` | 2026-03-31 | Empty/merge | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Five commits pushed to GitHub (cefc6278, fdd82285, 67824f10, 4c77f21b, 9b98dd5c): | — |
| 🟢 | `282d39c65` | 2026-03-31 | Frontend (UI) | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Four commits pushed to GitHub (cefc6278, fdd82285, 67824f10, 4c77f21b): | `plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx` |
| 🟢 | `7ff754c55` | 2026-03-31 | Empty/merge | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Three commits pushed to GitHub (cefc6278, fdd82285, 67824f10): | — |
| 🟢 | `7857dda86` | 2026-03-31 | Frontend (UI) | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) + code review fixes — All 5 background automation subtasks implemented and pushed to GitHub: | `plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx` |
| 🟢 | `b7dc5090e` | 2026-03-31 | Docs | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — Implemented all 5 background automation subtasks for Task #70: | `replit.md` |
| 🔴 | `cefc6278c` | 2026-03-31 | Cross Back↔Front | Task #70: Fase 3 — Scheduler + Automações Celery (G6, I1, I3, I6, G9) — - followup.process_pending: 7-day email follow-up for unopened WSI invites (I1) | `lia-agent-system/app/api/v1/email_tracking.py`<br>`lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`<br>`lia-agent-system/app/services/email_tracking_service.py` |

### Docs / Auditorias

**Descrição:** Relatórios de auditoria FE/BE — frontend-audit, candidate-preview-qa, search audit, design-token migration. Inclui scripts auxiliares de captura (login + 2FA + screenshots) usados nas auditorias.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** plataforma-lia/docs/audit/**, plataforma-lia/docs/audit-*.md, plataforma-lia/docs/AUDITORIA_*.md

**Docs de referência:** —

- **Commits:** 23  |  **Período:** 2026-03-30 → 2026-04-14  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×21 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `7e69b62a9` | 2026-04-14 | Frontend (api/util) | Fix errors when loading candidate data and improve API responsiveness — Refactors the `useCandidatesList` hook to handle race conditions, restore retry logic, and implement | `plataforma-lia/src/hooks/candidates/use-candidates-list.ts`<br>`plataforma-lia/src/lib/api/proxy-handler.ts` |
| 🟢 | `8cec79473` | 2026-04-14 | Docs | Add audit documentation files for project phases — Add new audit files to the documentation for phase 3 of the project, including COMPOSABLE_PATTERNS_A | `docs/audit/fase3-qualitativo/COMPOSABLE_PATTERNS_AUDIT.md`<br>`docs/audit/fase3-qualitativo/DUPLICATION_DIVERGENCE_MAP.md`<br>`docs/audit/fase3-qualitativo/PROPORTIONALITY_AUDIT.md` |
| 🟢 | `c416afdf4` | 2026-04-14 | Docs | Update audit document to include detailed findings on agent intelligence perception — Adds a comprehensive audit report for the LIA Agent System, detailing scores, strengths, and critica | `docs/audit/fase3-qualitativo/AGENT_INTELLIGENCE_PERCEPTION_AUDIT.md` |
| 🟢 | `ca4a7baa7` | 2026-04-14 | Docs | Update documentation to reflect platform architecture and audit findings — Update documentation files including FLOW_TRACES.md, PLATFORM_MAP.md, and PROMPT_AUDIT.md with detai | `docs/audit/fase1-reconhecimento/FLOW_TRACES.md`<br>`docs/audit/fase1-reconhecimento/PLATFORM_MAP.md`<br>`docs/audit/fase1-reconhecimento/PROMPT_AUDIT.md` |
| 🟢 | `0b99bfde0` | 2026-04-14 | Docs | Task start baseline checkpoint for code review | `PLATFORM_MAP.md`<br>`artifacts/mockup-sandbox/src/.generated/mockup-components.ts`<br>`docs/audit/fase1-reconhecimento/FLOW_TRACES.md` |
| 🟢 | `b36b27bc7` | 2026-04-12 | Docs | docs: audit log final completo — sessao Path A + SystemPromptBuilder + 5 items | `lia-agent-system/docs/audit/path-a-execution-log.md` |
| 🟢 | `a3823816e` | 2026-04-12 | Docs | docs: update Path A audit log with Passo 2 Commits A+B | `lia-agent-system/docs/audit/path-a-execution-log.md` |
| 🟢 | `3c46f81d4` | 2026-04-10 | Docs | Add search quality audit report and fix critical search endpoint issues — Create a markdown document detailing the results of a search quality audit, identifying a critical H | `plataforma-lia/docs/AUDITORIA_BUSCA_2026-04-10.md` |
| 🟢 | `cd5dcc969` | 2026-04-04 | Docs | Update documentation with revised frontend audit scores and detailed analysis — Update `audit-frontend-score-update.md` to reflect a deep dive into frontend metrics, detailing corr | `plataforma-lia/docs/audit-frontend-score-update.md` |
| 🟢 | `a9be7a167` | 2026-04-03 | Docs | Add layout and spacing issues to the audit document — Adds new Vue bugs (VUE-BUG-06, VUE-BUG-07, VUE-BUG-08) to the audit document, detailing layout and s | `plataforma-lia/docs/audit-candidate-preview-qa.md` |
| 🟢 | `dd0d71b9c` | 2026-04-03 | Docs | Update audit document with new bugs and screenshots — Adds new bugs to the audit document, updates problem and screenshot counts, and removes unused login | `plataforma-lia/docs/audit-candidate-preview-qa.md`<br>`plataforma-lia/docs/screenshots/capture-replit.js`<br>`plataforma-lia/docs/screenshots/capture-wedotalent.js` |
| 🟢 | `73f3bfae0` | 2026-04-03 | Docs | Update audit document with new candidate screenshots and identified issues — Adds 15 new candidate screenshots from production, details new bugs like exposed raw JSON data and m | `plataforma-lia/docs/audit-candidate-preview-qa.md` |
| 🟢 | `8f01fa6d5` | 2026-04-03 | Docs | Implement direct API login to bypass multi-factor authentication — Introduce a bash script to perform API login, retrieve MFA token, and verify MFA code via API calls. | `plataforma-lia/docs/screenshots/login-api.sh`<br>`plataforma-lia/docs/screenshots/login-direct.js`<br>`plataforma-lia/docs/screenshots/vue-10-result.png` |
| 🟢 | `24d8f4abf` | 2026-04-03 | Docs | Add login functionality and capture candidate screenshots for review — Update scripts to handle WeDOTalent login flow, including two-factor authentication, and capture scr | `plataforma-lia/docs/screenshots/capture-wedotalent.js`<br>`plataforma-lia/docs/screenshots/capture-with-2fa.js`<br>`plataforma-lia/docs/screenshots/vue-01-login.png` |
| 🟢 | `3a4243904` | 2026-04-03 | Docs | Add script to capture screenshots of product previews — Implement Playwright script to capture screenshots of the Replit application's candidate preview fun | `plataforma-lia/docs/screenshots/capture-replit.js`<br>`plataforma-lia/docs/screenshots/replit-01-funil-busca.jpg`<br>`plataforma-lia/docs/screenshots/replit-02-funil-loaded.jpg` |
| 🟢 | `04be87e96` | 2026-04-03 | Docs | Update audit document with detailed candidate preview information — Refactor the audit-candidate-preview-qa.md file to include comprehensive details on the header, tabs | `plataforma-lia/docs/audit-candidate-preview-qa.md` |
| 🟢 | `6ede754b1` | 2026-04-03 | Docs | Add detailed documentation for the file upload tab — Update audit-candidate-preview-qa.md to include detailed descriptions and screenshots of the file up | `plataforma-lia/docs/audit-candidate-preview-qa.md` |
| 🟢 | `903c02afd` | 2026-04-03 | Docs | Update audit document to include restructured content and detailed findings — Restructure the audit document to align with reference guides, improving clarity and actionability b | `plataforma-lia/docs/audit-candidate-preview-qa.md`<br>`replit.md` |
| 🟢 | `7c742d925` | 2026-04-03 | Docs | Add detailed comparison of candidate preview features — Create a deep code-to-code comparison document for candidate preview functionality, detailing compon | `plataforma-lia/docs/deep-comparison-candidate-preview.md`<br>`replit.md` |
| 🟡 | `975e0d586` | 2026-04-03 | Outro | Add automated login and initial page navigation for the website — Implement Playwright automation script to launch Chromium, navigate to the login page, fill in crede | `wedotalent-login.mjs` |
| 🟢 | `8623bc019` | 2026-03-31 | Docs | docs: audit score v4 - 49.9/60 (+2.4 force-dynamic+virtual+splits+tests) | `plataforma-lia/docs/audit/frontend-audit-v4-scores.md` |
| 🟢 | `870efa232` | 2026-03-30 | Docs | docs: consolida FRONTEND_AUDIT_REPORT_FINAL.md em frontend-audit-consolidado-20-dimensoes.md | `docs/audit/FRONTEND_AUDIT_REPORT_FINAL.md`<br>`docs/audit/frontend-audit-consolidado-20-dimensoes.md` |
| 🟢 | `395266788` | 2026-03-30 | Docs | docs: relatório consolidado auditoria frontend 20 dimensões | `docs/audit/frontend-audit-consolidado-20-dimensoes.md` |

### §17 Eval Framework

**Descrição:** Eval framework iterative hardening (~30 commits fix(eval):). UnboundLocalError no executor + short job_id em query_tools. UUID/varchar JOIN mismatch. CM-001/CM-003 remove wrong CAST. CO-002 offer letter generation. KB-005/006 UUID guard + WZ-002/003 keywords + MT-002 job_title extraction. Salary benchmark + offer ID + negation cancel pattern. Portuguese-aware criteria matching. Task #563 agentic eval framework + canonical-fix consolidation.

**⚠️ Dependências para cherry-pick:** Golden set atualizado | CI workflow Eval rodando | canonical-fix skill aplicada (corrigir na origem)

**Arquivos canônicos:** lia-agent-system/eval/*, scripts/eval/*

**Docs de referência:** BRANCH_MAP §17

- **Commits:** 23  |  **Período:** 2026-04-17 → 2026-04-29  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×20 🔴×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `9e62596c5` | 2026-04-29 | Backend | Add comprehensive tests for alert configuration and preferences — Update test coverage for alert configurations and preferences, including new tests for PUT /alerts/c | `lia-agent-system/eval/eval_results_20260429_105715.json`<br>`lia-agent-system/eval/eval_results_20260429_105746.json`<br>`lia-agent-system/eval/eval_results_20260429_111917.json` |
| 🟡 | `6ca16aa36` | 2026-04-20 | Backend | Improve agent evaluation by removing handshake and adding new scenarios — Remove handshake logic from agent evaluation API and add new test scenarios for various agent capabi | `lia-agent-system/eval/agentic/run_agentic_api.py`<br>`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T13-31-37.json` |
| 🟡 | `f1134ff0f` | 2026-04-20 | Backend | Update automated tests to correctly handle authentication and test scenarios — Modify the agentic evaluation test suite by adjusting the authentication fixture to use a custom `au | `lia-agent-system/eval/agentic/runs/agentic-2026-04-20T10-48-01.json`<br>`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T10-53-53.json`<br>`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T10-58-34.json` |
| 🟡 | `1adc24fcc` | 2026-04-20 | Backend | Add evaluation log for agentic runs — Add a new JSON file containing evaluation metadata and results for agentic runs. | `lia-agent-system/eval/agentic/runs/agentic-2026-04-20T10-38-58.json` |
| 🟡 | `d88ae9ff7` | 2026-04-20 | Backend | task-616: Run agentic eval suite end-to-end and produce consolidated .md report — ## Original Task | `lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-32-16.json`<br>`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-35-00-consolidated.json`<br>`lia-agent-system/eval/agentic/runs/agentic-2026-04-20T03-35-00-consolidated_judged.json` |
| 🟡 | `36065d92c` | 2026-04-20 | Backend | Reduce delay between test case executions — Shorten the sleep duration between individual test case runs in the evaluation runner from 1.2 to 0. | `lia-agent-system/eval/eval_runner.py` |
| 🔴 | `fb079b207` | 2026-04-19 | Cross IA↔Back | Task #563: agentic eval framework + canonical-fix consolidation — Original: build exhaustive 10-dimension agentic eval roteiro for LIA | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py` |
| 🟡 | `e1d1aee87` | 2026-04-19 | Backend | Task start baseline checkpoint for code review | `lia-agent-system/eval/eval_results_20260419_124559.json` |
| 🟡 | `da2ca4737` | 2026-04-19 | Cross IA↔Back | fix(eval): salary benchmark in analytics + offer ID rule + negation cancel pattern + eval timeout 60s — - analytics.yaml: add get_job_insights for salary benchmark queries (AN-003) | `lia-agent-system/app/shared/prompts/interaction_patterns.py` |
| 🟡 | `24a16fd56` | 2026-04-19 | Backend | fix(eval): add Portuguese-aware criteria matching for WZ-002/003 agile/data/location checks | `lia-agent-system/eval/eval_runner.py` |
| 🟡 | `574a61e83` | 2026-04-19 | Cross IA↔Back | Update job search and salary suggestions with new parameters — Modify entity extraction for job titles, update salary suggestion logic to use a new market range fe | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py` |
| 🔴 | `aee9ab45f` | 2026-04-19 | Cross IA↔Front | fix(eval): add suggest_salary/generate_jd_direct to _JOB_ACTIONS + fix regex patterns — - Add suggest_salary and generate_jd_direct to _JOB_ACTIONS dispatch set in executor.py | `lia-agent-system/app/api/v1/wsi/__init__.py`<br>`lia-agent-system/app/api/v1/wsi/admin.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py` |
| 🟡 | `3b53ca02e` | 2026-04-19 | Cross IA↔Back | fix(eval): KB-006 UUID filter, WZ-002/003 JD+salary Phase1, MT-002/003 bypass — - Remove global UUID filter from executor._execute_action (fixes KB-006 V0037 context) | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py` |
| 🟡 | `a41b000bd` | 2026-04-19 | Cross IA↔Back | fix(eval): KB-005 UUID guard + WZ-002/003 keywords + MT-002 job_title extraction — KB-005: executor.py now only injects entity_id as job/candidate_id when it is a | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py` |
| 🟡 | `9f40972e4` | 2026-04-18 | Backend | Add detailed evaluation report for LLM extraction layer — Update the LLM extraction layer evaluation report with new styling and detailed statistics. | `lia-agent-system/eval/eval_report_20260418_232903.html` |
| 🟡 | `a383445f3` | 2026-04-18 | Cross IA↔Back | fix(eval): list_jobs routing, duplica keyword, KB-005 time-per-stage, executor candidate_name — - capabilities.yaml: add list_jobs + listar_vagas + duplica keywords (EX-007, WZ-004) | `lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py` |
| 🟡 | `47f65a29f` | 2026-04-18 | Cross IA↔Back | fix(eval): name resolution, implicit job context, wizard tenant scope, short-id fallback — - WZ-002/003: Add _wizard_tenant_scope context manager to wizard_react_agent.py, | `lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |
| 🟡 | `648b36955` | 2026-04-18 | Backend | Add new components and update evaluation results for job management — Updates mockup component mapping and includes new evaluation results for job listing and pausing fun | `lia-agent-system/eval/eval_results_20260418_195711.json`<br>`lia-agent-system/eval/eval_results_20260418_200826.json` |
| 🟡 | `e32e5cfc0` | 2026-04-18 | Backend | Update evaluation criteria for checking task completion — Remove specific criteria for "does not fail" or "returns meaningful" from the evaluation logic in `e | `lia-agent-system/eval/eval_runner.py` |
| 🔴 | `695fbfd97` | 2026-04-18 | Cross Back↔Front | Add job creation functionality to the jobs chat interface — Removes unused useRef import from useJobsChat.ts and updates useEffect logic to correctly handle job | `plataforma-lia/src/components/pages/jobs/hooks/useJobsChat.ts` |
| 🟡 | `9ffa41bee` | 2026-04-17 | Cross IA↔Back | Improve system responses and entity identification — Update `workflow.py` to use a generic clarification question and `chat_adapter.py` to correctly extr | `lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🟡 | `159aa9560` | 2026-04-17 | Backend | Add regular expression support for evaluation runner — Import the 're' module for regular expression operations within the evaluation runner. | `lia-agent-system/eval/eval_runner.py` |
| 🟡 | `74fecdc0c` | 2026-04-17 | Backend | Improve Portuguese language support for evaluation criteria checking — Update the `_criterion_met` function to better handle Portuguese nuances in success criteria evaluat | `lia-agent-system/eval/eval_runner.py` |

### Backend Proxy Routes (FE)

**Descrição:** Routes em plataforma-lia/src/app/api/backend-proxy — proxy do Next.js para a FastAPI. Cada endpoint da FastAPI tem seu wrapper aqui. Mudanças geralmente espelham mudanças no backend (envelope, auth, paths).

**⚠️ Dependências para cherry-pick:** Sincronizado com endpoint Backend correspondente | NUNCA chama FastAPI direto do componente — sempre via proxy

**Arquivos canônicos:** plataforma-lia/src/app/api/backend-proxy/**

**Docs de referência:** —

- **Commits:** 22  |  **Período:** 2026-03-30 → 2026-04-14  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×15 🟢×4 🟡×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `6ef8c0548` | 2026-04-14 | Frontend (UI) | fix: proxy onboarding returns 503 when Rails not configured [PX08-014] — Sprint 0 item 0.10 — Remove localhost:3000 fallback for RAILS_BACKEND_URL. | `plataforma-lia/src/app/api/backend-proxy/onboarding/[...path]/route.ts` |
| 🔴 | `0a7a49dee` | 2026-04-13 | Cross Back↔Front | Make candidate search results consistently appear on the screen — Fix three API routes that were not properly unwrapping backend responses, ensuring that candidate da | `plataforma-lia/src/app/api/backend-proxy/search/candidates/from-cv/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/candidates/refine/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/candidates/route.ts` |
| 🔴 | `5be674ef3` | 2026-04-13 | Cross Back↔Front | Update API to correctly handle backend responses and improve server restart — Fix incorrect JSON unwrapping in API routes and adjust retry logic for server readiness. | `lia-agent-system/app/domains/hiring_policy/domain.py`<br>`lia-agent-system/app/domains/job_management/domain.py`<br>`lia-agent-system/app/domains/sourcing/domain.py` |
| 🟢 | `4da70fe08` | 2026-04-12 | Frontend (UI) | Fix deployment build errors — 1. Add missing AlertCircle import in FilterSectionOpcoes.tsx | `plataforma-lia/src/app/api/backend-proxy/sourcing-agents/route.ts`<br>`plataforma-lia/src/components/search/filter-sections/FilterSectionOpcoes.tsx` |
| 🔴 | `130cd6886` | 2026-04-12 | Cross IA↔Front | Revert "Merge remote-tracking branch 'origin/develop-giovanni'" — This reverts commit c7c2c060ca2b8189a3ac6369a5f9eec474d9e0c8, reversing | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/search_assistant.py`<br>`lia-agent-system/app/domains/ai/services/llm.py` |
| 🟢 | `46446fa91` | 2026-04-10 | Frontend (UI) | Update onboarding proxy route to correctly handle dynamic paths — Refactors the `onboarding/[...path]/route.ts` file to correctly destructure and join path segments f | `plataforma-lia/src/app/api/backend-proxy/onboarding/[...path]/route.ts` |
| 🟡 | `3751ef241` | 2026-04-09 | Frontend (UI) | Fix file upload errors and update API proxy routes — Corrects file upload authentication forwarding by using `getAuthHeadersForForm` and updates numerous | `plataforma-lia/src/app/api/backend-proxy/candidates/[id]/files/[attachmentId]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/candidates/[id]/files/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/data-requests/[id]/cancel/route.ts` |
| 🔴 | `ed0c6a466` | 2026-04-09 | Cross Back↔Front | Add secure management for AI model API keys and providers — Integrate AI model provider management with API key encryption, masking, and removal functionality. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/llm_config.py`<br>`lia-agent-system/app/domains/ai/repositories/llm_config_repository.py` |
| 🔴 | `0bd4eb8e5` | 2026-04-09 | Cross Back↔Front | Migrate all frontend API routes to use FastAPI and improve categories endpoint — Update backend target for numerous API routes from "rails" to "fastapi", and optimize the email temp | `lia-agent-system/app/api/v1/email_templates.py`<br>`lia-agent-system/app/domains/email_templates/repositories/email_templates_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/activities/route.ts` |
| 🔴 | `7d4b383ad` | 2026-04-09 | Cross Back↔Front | fix: resolve pipeline overview SQL type mismatch and add proxy error handling — - Fixed `character varying = uuid` SQL error in job_vacancies_analytics_repository.py | `lia-agent-system/app/domains/job_vacancies_analytics/repositories/job_vacancies_analytics_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/digital-twins/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/sourcing-agents/route.ts` |
| 🔴 | `1a65de885` | 2026-04-09 | Cross Back↔Front | Fix issues preventing the Agent Studio page from loading correctly — Address backend startup issues, correct proxy route configurations, and improve frontend error handl | `lia-agent-system/app/api/v1/sourcing_agents.py`<br>`plataforma-lia/src/app/api/backend-proxy/agent-templates/sectors/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/sourcing-agents/[id]/route.ts` |
| 🟡 | `d1d0df65a` | 2026-04-08 | Frontend (UI) | Fix Expand to Global bug, LIA sidebar overflow, and improve Pearch unavailability handling — 1. Auth header forwarding in proxy routes: | `plataforma-lia/src/app/api/backend-proxy/search/candidates/from-cv/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/candidates/refine/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/candidates/route.ts` |
| 🔴 | `0b128a093` | 2026-04-08 | Frontend (UI) | Require authentication for most API backend proxy routes — Changed the `auth` property from `false` to `true` for numerous backend proxy routes, ensuring that  | `plataforma-lia/src/app/api/backend-proxy/agent-monitoring/activities/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/agent-monitoring/activity-feed/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/agent-monitoring/agents/[agentId]/activities/route.ts` |
| 🔴 | `ac0d1d417` | 2026-04-08 | Frontend (UI) | Refactor API routes to use a new proxy handler utility — Replace manual fetch requests in numerous API routes with calls to a centralized `createProxyHandler | `plataforma-lia/src/app/api/backend-proxy/agent-chat/sessions/active/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/agent-monitoring/activities/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/agent-monitoring/domains/[domain]/metrics/route.ts` |
| 🔴 | `5b914d413` | 2026-04-08 | Frontend (UI) | refactor: create shared proxy handler and convert 55 API routes (-1800 lines) — Created src/lib/api/proxy-handler.ts — type-safe proxy utility with: | `plataforma-lia/src/app/api/backend-proxy/activities/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/agent-monitoring/activity-feed/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/agent-monitoring/agents/[agentId]/activities/route.ts` |
| 🔴 | `220094926` | 2026-04-07 | Cross Back↔Front | Standardize backend URLs and fix critical deployment issues — Correctly configure backend URLs across the application, replacing hardcoded ports and ensuring cons | `lia-agent-system/app/api/v1/automation/event_handlers.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py`<br>`lia-agent-system/app/api/v1/email_tracking.py` |
| 🔴 | `420c5b228` | 2026-04-05 | Cross Back↔Front | Update chat functionality to correctly stream responses — Adjust API endpoints and client configurations to properly handle streaming responses from the chat  | `lia-agent-system/app/api/v1/chat.py`<br>`plataforma-lia/src/app/api/backend-proxy/chat/actions/candidate-field-update/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/chat/message/route.ts` |
| 🔴 | `84c6159b5` | 2026-04-05 | Cross Back↔Front | Connect Tarefas page to real backend APIs + Activity Feed section — Changes: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/api/v1/lia_assistant_graph.py` |
| 🔴 | `9bd6b42c8` | 2026-04-05 | Cross Back↔Front | Connect Tarefas page to real backend APIs, add Activity Feed section — - Created 4 Next.js proxy routes: GET /tasks, GET /tasks/summary, | `lia-agent-system/app/api/v1/agent_memory.py`<br>`plataforma-lia/src/app/api/backend-proxy/briefing/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/tasks/[taskId]/cancel/route.ts` |
| 🔴 | `f76917cf9` | 2026-04-04 | Cross Back↔Front | Remove hardcoded company IDs and improve authentication — Replace all instances of hardcoded 'demo_company' with dynamic company ID resolution, enhancing secu | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/auth/models.py`<br>`lia-agent-system/app/domains/communication/services/teams_tab_trigger.py` |
| 🟢 | `96288fccd` | 2026-04-04 | Frontend (UI) | Add API endpoint for fetching context suggestions for the LIA platform — Implement a Next.js API route in `plataforma-lia/src/app/api/backend-proxy/lia/context-suggestions/r | `plataforma-lia/src/app/api/backend-proxy/lia/context-suggestions/route.ts` |
| 🟡 | `185f8bf75` | 2026-03-30 | Frontend (UI) | Refine code by changing variable declarations and removing unused code — Update variable declarations from 'let' to 'const' in multiple files, and remove unnecessary logic f | `plataforma-lia/src/app/api/backend-proxy/cv/[...path]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/insurance/[...path]/route.ts`<br>`plataforma-lia/src/components/admin/AdminTemplateHub.tsx` |

### §16 LIA Persona

**Descrição:** Diagnóstico de persona da LIA: roteiro + harness Playwright + 120 sondas automatizadas. _IDENTITY_OVERRIDE no system_prompt_builder (LIA nunca diz 'sou Gemini/Claude/GPT'). Tool leakage detector regex pós-LLM. FairnessGuard v8 com hard block para 'mãe solo', 'pai solo', socioeconômico. Phase 1 intercept para identity questions (LIA nunca chama Gemini para 'quem é você'). Fix 23 falhas críticas.

**⚠️ Dependências para cherry-pick:** main_orchestrator chama agentic_loop com system_prompt POPULADO (não vazio) | _IDENTITY_OVERRIDE no SystemPromptBuilder | tool leakage regex ativa | FairnessGuard v8 com categorias maternidade/socioeconomico

**Arquivos canônicos:** lia-agent-system/app/orchestrator/main_orchestrator.py, app/shared/prompts/system_prompt_builder.py, app/orchestrator/agentic_loop.py, app/shared/compliance/fairness_guard.py

**Docs de referência:** DEVELOPER_HANDOFF.md PARTE A

- **Commits:** 22  |  **Período:** 2026-04-12 → 2026-04-21  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×19 🔴×2 🟢×1
- **Tags/Milestones:** `milestone/lia-persona-diagnostic`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `c3d45b3d8` | 2026-04-21 | Cross IA↔Back | Introduce multi-tenant capability toggles to control agent features — Add `enabled_for_tenant` field to capability cards in `capability_cards.yaml` and update `SystemProm | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `684b2a140` | 2026-04-21 | IA | feat(lia): Init I.B — persona renders capability_cards end-to-end — Closes anti-hallucination loop started by FIX 23 + 24 and Init I.A. | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `e416f26a6` | 2026-04-21 | IA | Improve system prompt to include active filters and pending actions — Add support for rendering active filters and pending actions within the system prompt builder to mai | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🔴 | `77e31602c` | 2026-04-21 | Cross IA↔Front | Fix infinite loop in modal by stabilizing hook identity — Refactors `useInterpretContext` to ensure stable identity for `sendMessage` by using refs and functi | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/components/kanban/components/useUniversalTransitionModal.tsx` |
| 🟢 | `32cd180b4` | 2026-04-19 | Empty/merge | fix(lia-persona): corrige 23 falhas críticas do diagnóstico de persona (120 sondas) — FASE 1 — main_orchestrator.py (P0) | — |
| 🟡 | `a2a57f8e8` | 2026-04-19 | Backend | Persona Diagnostic: cross-check probes really hit the intended specialised agent — Task #537. The persona-diagnostic runner already captured `agent_observed` | `lia-agent-system/eval/persona-diagnostic/runner/report.py`<br>`lia-agent-system/eval/persona-diagnostic/runner/routing_audit.py`<br>`lia-agent-system/eval/persona-diagnostic/runner/runner.py` |
| 🟡 | `fd1f1bc44` | 2026-04-19 | Cross IA↔Back | revert(eval): restore communication.yaml and interaction_patterns.py — Reverted both files to pre-da2ca4737 state. | `lia-agent-system/app/shared/prompts/interaction_patterns.py` |
| 🟡 | `e4e06c10d` | 2026-04-19 | Backend | Automate the LIA persona diagnostic (Task #527) — Turns the manual 120-probe persona diagnostic into a single-command | `lia-agent-system/eval/persona-diagnostic/probes.yaml`<br>`lia-agent-system/eval/persona-diagnostic/runner/__init__.py`<br>`lia-agent-system/eval/persona-diagnostic/runner/judge.py` |
| 🟡 | `5a7205e44` | 2026-04-19 | Backend | Diagnóstico de persona da LIA: roteiro manual + harness Playwright — - Consolidado o roteiro manual em `lia-agent-system/eval/persona-diagnostic/diagnostico-persona.md`  | `lia-agent-system/eval/eval_results_20260419_002514.json`<br>`lia-agent-system/eval/eval_results_20260419_005411.json`<br>`lia-agent-system/eval/eval_results_20260419_010256.json` |
| 🟡 | `44e381ce5` | 2026-04-19 | IA | fix(identity): Phase 1 intercept for identity questions — LIA never calls Gemini for quem e voce — Added lia_identidade intent to ActionExecutor that returns LIA identity directly | `lia-agent-system/app/orchestrator/action_executor/executor.py` |
| 🟡 | `0ad291737` | 2026-04-19 | IA | Update orchestrator to skip LLM interpretation for identity responses — Modify the MainOrchestrator class to conditionally skip LLM interpretation when the action type is " | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `89c427955` | 2026-04-19 | IA | Update system to better identify when users ask about the AI's identity — Improve regex patterns for recognizing questions about the AI's identity and purpose. | `lia-agent-system/app/orchestrator/action_executor/intents_config.py` |
| 🟡 | `881aef9d0` | 2026-04-19 | Cross IA↔Back | fix(persona): LIA identity override — prevent Gemini from leaking model identity — - Prepend REGRA ZERO identity block at top of lia_persona.yaml so it is read first | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🔴 | `dde1a35bf` | 2026-04-14 | Cross Back↔Front | feat: connect recruiter personalization to agent prompts [P36-079] Sprint 12 item 12.4 — - PersonalizationContext.to_prompt_snippet(): formats profile as readable prompt text | `lia-agent-system/app/domains/analytics/services/recruiter_personalization_service.py`<br>`plataforma-lia/src/components/settings/RecruiterPreferencesPanel.tsx` |
| 🟡 | `24f582c0b` | 2026-04-14 | Backend | feat: add pipeline stages and custom persona to platform awareness [P35-044] — Complement to Sprint 5 item 5.4 — Two missing platform awareness fields: | `lia-agent-system/app/shared/services/tenant_context_service.py` |
| 🟡 | `033086895` | 2026-04-12 | IA | refactor: delete prompt_registry.py (0 callers) + unused getters — - Deleted app/shared/prompts/prompt_registry.py (0 external callers) | `lia-agent-system/app/shared/prompts/__init__.py`<br>`lia-agent-system/app/shared/prompts/agent_prompts.py`<br>`lia-agent-system/app/shared/prompts/prompt_registry.py` |
| 🟡 | `75188a458` | 2026-04-12 | Cross IA↔Back | fix: remove 5 hardcoded LIA fallbacks — persona via SystemPromptBuilder — - company_users.py: removed "Olá! Sou a LIA" hardcoded intro | `lia-agent-system/app/api/v1/company_users.py`<br>`lia-agent-system/app/api/v1/guardrails.py`<br>`lia-agent-system/app/api/v1/teams.py` |
| 🟡 | `3fc731723` | 2026-04-12 | Cross IA↔Back | refactor: isolate training persona from dynamic YAML flow — Training data is a versioned artifact — persona changes must be deliberate. | `lia-agent-system/app/domains/analytics/services/training_data_service.py`<br>`lia-agent-system/app/shared/prompts/training_persona.py` |
| 🟡 | `ceae4c600` | 2026-04-12 | Backend | refactor: final cleanup — remove 743 lines of legacy dead code + migrate training to YAML persona — Legacy cleanup (-743 lines): | `lia-agent-system/app/domains/analytics/services/training_data_service.py` |
| 🟡 | `eb28a0727` | 2026-04-12 | Cross IA↔Back | refactor: complete prompt unification — eliminate all remaining hardcoded personas — Round 2: 32 patches across 29 files. | `lia-agent-system/app/api/v1/candidate_search/misc_search.py`<br>`lia-agent-system/app/api/v1/lia_assistant/_shared.py`<br>`lia-agent-system/app/api/v1/lia_assistant/wizard.py` |
| 🟡 | `59f475944` | 2026-04-12 | Backend | refactor: unify prompt pipeline — replace 16 hardcoded personas with SystemPromptBuilder — P0: chat.py SSE streaming now uses SystemPromptBuilder.build() with user/tenant context | `lia-agent-system/app/api/v1/interview_notes.py`<br>`lia-agent-system/app/api/v1/lia_assistant/_shared.py`<br>`lia-agent-system/app/api/v1/lia_assistant/insights.py` |
| 🟡 | `c13c7d20b` | 2026-04-12 | Backend | feat: move SystemPromptBuilder to base class — all 17 agents get persona (Commit 2) — langgraph_react_base.py: | `lia-agent-system/app/domains/analytics/agents/analytics_react_agent.py`<br>`lia-agent-system/app/domains/ats_integration/agents/ats_integration_react_agent.py`<br>`lia-agent-system/app/domains/automation/agents/automation_react_agent.py` |

### §14 BYOK + LLM Factory

**Descrição:** LLM Factory canonical com BYOK (Bring Your Own Key) compliance + Quality Tier Guard (Tier 2 bloqueado para screening/wsi) + audit trail per LLM call (response_hash + session_id) + UI BYOK seções 9+10. ADR-018. 4 bugs P0 corrigidos (BUG-01/01b/02/03 audit trail + BUG-07 WSI BYOK bypass). Mapa de 54 consumidores LLM auditados.

**⚠️ Dependências para cherry-pick:** Tenant configura key → factory usa SEMPRE | Tier 2 + screening = substitui por Tier 1 + WARN | log_decision com kwargs canônicos | WSI passa task_type='wsi' ativando guard

**Arquivos canônicos:** lia-agent-system/app/shared/providers/llm_factory.py, app/domains/ai/services/llm.py, app/domains/cv_screening/services/wsi_question_adjuster.py, app/api/v1/wsi/_shared.py

**Docs de referência:** LLM_FACTORY_HANDOFF_v2.md (849 linhas, 12 seções), ADR-018

- **Commits:** 21  |  **Período:** 2026-03-16 → 2026-04-21  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×10 🟢×7 🔴×4
- **Tags/Milestones:** `milestone/byok-llm-factory-adr-018`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `0ee7a0211` | 2026-04-21 | Backend | feat(eval): Init VI Fase 0 — eval_judge migrated to LLM Factory — Canonical-fix per FINAL_AUDIT.md §4 / audit sectionB. | `lia-agent-system/eval/eval_judge.py`<br>`lia-agent-system/eval/eval_judge_config.yaml`<br>`lia-agent-system/tests/unit/test_initVI_fase0.py` |
| 🟢 | `5d34569ef` | 2026-04-19 | Docs | docs(byok): section 12 — checklist dev + mapa completo 54 consumidores LLM — Section 12: Guia do Desenvolvedor | `lia-agent-system/LLM_FACTORY_HANDOFF_v2.md` |
| 🟢 | `9eca3ac23` | 2026-04-19 | Docs | docs(byok): section 11 - auditoria profunda + inventario de bugs corrigidos — Section 11: Auditoria Profunda de Hardcoded Bypasses (2026-04-19) | `lia-agent-system/LLM_FACTORY_HANDOFF_v2.md` |
| 🟡 | `b4218eace` | 2026-04-19 | Cross IA↔Back | fix(byok): corrigir 4 bugs P0 de audit trail e BYOK bypass — BUG-01: llm_factory._audit_llm_usage() usava kwargs errados em | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_question_adjuster.py`<br>`lia-agent-system/app/domains/voice/services/voice_screening_orchestrator.py` |
| 🟢 | `0b6e1ae39` | 2026-04-19 | Docs | docs(byok): secoes 9+10 — frontend UI + auditoria E2E — Secao 9: Interface do cliente (Choose Your AI frontend) | `lia-agent-system/LLM_FACTORY_HANDOFF_v2.md` |
| 🟢 | `f4462e2ab` | 2026-04-19 | Docs | docs(architecture): ADR-018 LLM Factory / BYOK contract — Documenta o LLM Factory como componente arquitetural canonico: | `lia-agent-system/ARCHITECTURE.md` |
| 🟢 | `aa6d38cd1` | 2026-04-19 | Docs | feat(llm-factory): BYOK compliance + Quality Tier Guard + audit trail — LIA-BYOK B1: WARN [LIA-BYOK] em todos os pontos de fallback para system key | `lia-agent-system/LLM_FACTORY_HANDOFF_v2.md` |
| 🟡 | `f3232904b` | 2026-04-19 | Backend | docs(handoff): add exhaustive LLM Factory handoff for Rails team — Task #540 — Documento técnico em PT-BR (`docs/handoff/llm-factory.md`) | `lia-agent-system/eval/eval_results_20260419_121221.json` |
| 🟡 | `9cb743499` | 2026-04-17 | Backend | Align AI provider key detection with health check reporting — Refactor `main.py` to use the `_provider_report` dictionary obtained from the health check endpoint  | `lia-agent-system/app/main.py` |
| 🟡 | `71c2f86aa` | 2026-04-14 | Cross IA↔Back | refactor: migrate all raise Exception() to LIAError hierarchy [P35-060] — Zero generic raise Exception() remaining in app/ (was 8). | `lia-agent-system/app/domains/candidates/services/candidate_feedback_service.py`<br>`lia-agent-system/app/domains/communication/services/teams_recording_service.py`<br>`lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🟡 | `8835124b5` | 2026-04-14 | Infra/Config | ci: add architectural fitness functions step [PX08-039] — Add pytest tests/fitness/ step to CI pipeline after ruff + LLM Factory | `.github/workflows/ci.yml` |
| 🟡 | `6a08337ed` | 2026-04-12 | Backend | feat(lgpd): Etapa 1 — LLM Factory Compliance, all calls tenant-aware — All LLM calls now respect tenant config (LGPD Art. 12): | `lia-agent-system/app/api/v1/gemini_voice.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/transcription_service.py` |
| 🔴 | `d413ada7b` | 2026-04-12 | Cross IA↔Front | fix: API routing, LLM Gemini fallback, auth token TTL and proxy fixes — - Add docker-compose.yml and docker-entrypoint.sh for GCP deploy | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/search_assistant.py`<br>`lia-agent-system/app/api/v1/sector_templates.py` |
| 🔴 | `b687d930e` | 2026-04-10 | Cross IA↔Front | Task #119: Voice Abstraction in LLM Factory + Streaming Frontend — Created VoiceStreamProviderABC abstraction layer in the LLM Factory with | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/voice_stream.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py` |
| 🔴 | `65122342a` | 2026-04-09 | Cross IA↔Front | feat: complete LLM Factory migration — zero direct SDK imports outside providers/ — ## Summary | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/chat.py` |
| 🟢 | `2704aac3f` | 2026-04-09 | Docs | Add detailed audit findings and a prioritized roadmap to the deployment guide — Appends Section 24 to DEPLOY_GUIDE.md, detailing a 9-dimension audit of production readiness, includ | `DEPLOY_GUIDE.md` |
| 🔴 | `d641ea4eb` | 2026-04-05 | Cross Back↔Front | feat: Migrate Voice Screening VoIP from Twilio+STT+TTS to Gemini Live Audio API — Task #6: Browser VoIP calls now use Gemini Live Audio natively. | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/gemini_voice.py`<br>`lia-agent-system/app/api/v1/triagem.py` |
| 🟡 | `7aeca82e6` | 2026-04-04 | Backend | feat(task-135): Voice Screening Pipeline — Twilio Voice + Gemini 2.5 Flash (final) — Tests: 56 passed, 1 skipped. | `lia-agent-system/app/api/v1/twilio_voice.py`<br>`lia-agent-system/app/domains/communication/services/communication_dispatcher.py`<br>`lia-agent-system/app/domains/communication/services/twilio_voice_service.py` |
| 🟡 | `790319d7f` | 2026-04-04 | Cross IA↔Back | feat(task-132): Gemini como LLM Padrão — Reordenar fallback chain — ## Objetivo | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/lia_assistant.py` |
| 🟢 | `6cf53834c` | 2026-03-26 | Docs | Update AI docs: Gemini-only in production (user confirmed) — User confirmed WeDOTalent uses ONLY Gemini in production — Claude | `docs/PLATFORM_MAP.md`<br>`docs/specs/ai/AI_ARCHITECTURE.md`<br>`docs/specs/ai/LLM_DECISIONS.md` |
| 🟡 | `fda85e036` | 2026-03-16 | Backend | Fix chat response formatting and Anthropic API integration — Refactor agent logic to use a new method for extracting text content from responses, improving consi | `lia-agent-system/app/domains/analytics/agents/analytics_react_agent.py`<br>`lia-agent-system/app/domains/ats_integration/agents/ats_integration_react_agent.py`<br>`lia-agent-system/app/domains/automation/agents/automation_react_agent.py` |

### Observability / Sentry / OTLP

**Descrição:** Sentry server/edge config. OTLP tracing canônico (ADR-019 spans). Tracing nas migrations do orchestrator.

**⚠️ Dependências para cherry-pick:** DSN Sentry configurado | OTLP exporter ativo | spans canônicos ADR-019

**Arquivos canônicos:** plataforma-lia/sentry.*.config.ts, lia-agent-system/app/observability/*

**Docs de referência:** ADR-019

- **Commits:** 20  |  **Período:** 2026-03-22 → 2026-04-17  |  **Camadas:** Backend + Frontend + IA + Rails  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×9 🟡×8 🔴×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `4447190b6` | 2026-04-17 | Testes | Fix broken token-budget and drift unit tests after observability move — Task #362: Several tests still patched/imported the old `app.services.*` | `lia-agent-system/tests/contract/test_token_budget_contracts.py`<br>`lia-agent-system/tests/integration/test_drift_and_bias_audit.py`<br>`lia-agent-system/tests/integration/test_token_budget_wiring.py` |
| 🟢 | `9730fea48` | 2026-04-17 | Testes | Task #256: Add automated test for the jobs-page fallback banner — Original task: Cover the amber "external source unavailable" banner that | `plataforma-lia/src/components/pages/jobs/__tests__/jobs-page-fallback-banner.test.tsx` |
| 🟢 | `e92d351de` | 2026-04-17 | Docs | docs: document canonical observability layer (Task #363) — Task #343 collapsed 11 modules (tracing, structured_logging, callbacks, | `CLAUDE.md`<br>`lia-agent-system/ARCHITECTURE.md`<br>`lia-agent-system/docs/CANONICAL_SOURCES_SPEC.md` |
| 🟢 | `b583afd74` | 2026-04-17 | Docs | docs(observability): align architecture docs with new canonical location (Tarefa #372) — Closes the doc-only residual called out in Tarefa #343 / AUDIT_STATUS_REPORT_2026-04-FINAL §0 | `CLAUDE.md`<br>`lia-agent-system/ARCHITECTURE.md`<br>`lia-agent-system/docs/specs/CANONICAL_SOURCES_SPEC.md` |
| 🔴 | `0bcf56528` | 2026-04-17 | Cross IA↔Back | Task #343: Collapse legacy observability paths into app.shared.observability — Stage 6 had not actually been executed at HEAD — `app/shared/observability/` | `lia-agent-system/app/api/v1/admin_token_budget.py`<br>`lia-agent-system/app/api/v1/agent_chat_sse.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py` |
| 🟡 | `f1d286d9f` | 2026-04-17 | Frontend (UI) | Task #345 — Audit & fix jobs-page resiliency (Failed to fetch + 429 cascade) — Root cause was a chain of bugs, not a single one: | `plataforma-lia/src/components/pages/jobs/hooks/useJobsData.ts` |
| 🟢 | `9c1992db7` | 2026-04-17 | Testes | Task #325: Canonicalize app/shared/observability/ (Stage 6) — Consolidate 11 observability modules previously scattered across 6 locations | `plataforma-lia/e2e/tests/kanban/kanban-full-audit.spec.ts` |
| 🔴 | `6c878d719` | 2026-04-15 | Rails (ats-api) | Sync ats-api-copia from GitHub (JWT blacklist, Rails 7.1.5, Sentry, CORS, Bunny fixes) | `ats-api-copia/.env.example`<br>`ats-api-copia/Gemfile`<br>`ats-api-copia/app/controllers/application_controller.rb` |
| 🟡 | `8eff6ce4f` | 2026-04-13 | Backend | Task #178: Consumption Observability + Invoicing (backend-only) — Expanded ExternalApiConsumption model with pipeline_id, search_session_id, | `lia-agent-system/app/api/v1/consumption.py`<br>`lia-agent-system/app/domains/billing/services/consumption_report_service.py`<br>`lia-agent-system/app/domains/billing/services/consumption_tracking_service.py` |
| 🟡 | `f04c4d5a2` | 2026-04-13 | Backend | Task #178: Consumption Observability + Invoicing (backend-only) — Expanded ExternalApiConsumption model with pipeline_id, search_session_id, | `lia-agent-system/alembic/versions/076_consumption_observability_fields.py`<br>`lia-agent-system/app/api/v1/consumption.py`<br>`lia-agent-system/app/domains/billing/services/consumption_logger.py` |
| 🟡 | `f9f5c148f` | 2026-04-09 | Backend | Improve system stability by resolving startup errors and refining observability configurations — Resolve Sentry errors by switching the AutomationScheduler to MemoryJobStore, gracefully handling Ra | `lia-agent-system/app/domains/automation/services/automation_scheduler.py`<br>`lia-agent-system/app/main.py` |
| 🟡 | `22c5c8f77` | 2026-04-06 | Backend | feat(phase2): migrate observability.py to ObservabilityRepository | `lia-agent-system/app/api/v1/observability.py` |
| 🟡 | `c3a581489` | 2026-04-06 | Backend | feat(phase2+4): migrate candidates.py, fix service shims, add observability domain | `lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/domains/observability/repositories/__init__.py`<br>`lia-agent-system/app/domains/observability/repositories/observability_repository.py` |
| 🟡 | `5e9ec6e4c` | 2026-04-04 | Backend | Task #137: Ativar LangSmith — Tracing de Chamadas de IA — Changes: | `lia-agent-system/app/config/langsmith.py`<br>`lia-agent-system/tests/unit/test_langsmith_config.py` |
| 🔴 | `2b8c725c0` | 2026-04-04 | Cross Back↔Front | Task #136: Ativar Sentry — Monitoramento de Erros em Produção — Changes: | `lia-agent-system/app/main.py`<br>`lia-agent-system/apps/api-funil/main.py`<br>`lia-agent-system/apps/api-onboarding/main.py` |
| 🟢 | `801024246` | 2026-03-31 | Frontend (UI) | refactor(arch): remove duplicate modals from jobs-page.tsx, delegate to JobsModalsSection | `plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟡 | `58227991e` | 2026-03-30 | Frontend (UI) | bundle: lazy load html2canvas+jspdf+canvg + dynamic() em modais pesados + bundle analyzer — BCK-09 OBS-05 — - job-report-modal.tsx: remove static imports html2canvas/jsPDF, usar dynamic import em gene | `plataforma-lia/src/app/api/backend-proxy/orchestrator/_archived/pipeline-chat/route.ts`<br>`plataforma-lia/src/components/job-report-modal.tsx`<br>`plataforma-lia/src/components/pages/_archived/jobs2-page.tsx` |
| 🟢 | `4c4ec6dff` | 2026-03-30 | Frontend (UI) | ux: TOAST_REMOVE_DELAY 5s + toast wrapper + session timeout + ?next= param + beforeunload — BCK-24 BCK-25 BCK-27 OBS-15 | `plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `b08e714e9` | 2026-03-30 | Frontend (api/util) | Add HTML sanitization and Sentry error tracking — Integrate Sentry SDK for error monitoring and implement DOMPurify for sanitizing HTML content in cli | `plataforma-lia/package-lock.json`<br>`plataforma-lia/package.json`<br>`plataforma-lia/sentry.client.config.ts` |
| 🟢 | `286ed1992` | 2026-03-22 | Docs | Enhance system observability with tracing, metrics, and structured logging — Introduce OpenTelemetry tracing, Prometheus metrics, and structured JSON logging capabilities by int | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |

### Backend Services (BE)

**Descrição:** Services do backend FastAPI fora dos paths IA — agendamento, billing, communication, automations, analytics, sourcing.

**⚠️ Dependências para cherry-pick:** Schemas Pydantic alinhados com endpoint | repositórios DB | tenant guards no caller

**Arquivos canônicos:** lia-agent-system/app/services/**, app/domains/*/services/**

**Docs de referência:** —

- **Commits:** 19  |  **Período:** 2026-04-05 → 2026-04-27  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×15 🟢×2 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `c58acf2ef` | 2026-04-27 | Backend | Add functionality to formally register a candidate as hired — Introduce a new tool `register_hire` for the pipeline domain, allowing candidates to be formally mar | `lia-agent-system/app/domains/pipeline/config/capabilities.yaml`<br>`lia-agent-system/app/domains/pipeline/tools/pipeline_tools.py` |
| 🟡 | `38e423195` | 2026-04-25 | Backend | Ensure deterministic tool ordering and handle missing definitions — Refactor the tool definition picking logic to ensure deterministic ordering and add explicit checks  | `lia-agent-system/app/domains/company_settings/agents/company_tool_registry.py` |
| 🟡 | `fb636ba3c` | 2026-04-21 | Backend | Task start baseline checkpoint for code review | `lia-agent-system/app/domains/ai/services/candidate_search_service.py` |
| 🟡 | `eecf182e7` | 2026-04-21 | Backend | Task start baseline checkpoint for code review | `lia-agent-system/app/domains/company_settings/domain.py`<br>`lia-agent-system/app/domains/hiring_policy/domain.py` |
| 🟡 | `a060038c6` | 2026-04-19 | Backend | Add audit script to verify chat capabilities and update documentation — Introduce a Python script to audit chat capabilities, generate a JSON report, update documentation f | `lia-agent-system/app/api/v1/candidate_portal.py` |
| 🟡 | `c2da08fec` | 2026-04-18 | Backend | Control when user reopens are counted towards session limits — Modify the token validation to only count reopens for the candidate-entry path. | `lia-agent-system/app/domains/recruitment/services/triagem_session_service/lifecycle.py` |
| 🟡 | `3f5531538` | 2026-04-12 | Backend | fix: 3 bugs found during E2E validation of Agent Studio — Bug 1: Missing process() abstract method → CustomAgentRuntime uninstantiable | `lia-agent-system/app/domains/agent_studio/custom_agent_runtime.py` |
| 🟡 | `8431d4160` | 2026-04-12 | Backend | feat: GAP 5 — expanded tool access for Agent Studio — - Pool 1: 40 autonomous tools (cross-domain, curated) | `lia-agent-system/app/domains/agent_studio/custom_agent_runtime.py` |
| 🟡 | `19573c89b` | 2026-04-12 | Backend | feat: GAP 0 — RAG as agent tool (sourcing + autonomous) — - Fixed rag_search: passes db session to rag_pipeline_service.search() | `lia-agent-system/app/domains/autonomous/agents/autonomous_tool_registry.py`<br>`lia-agent-system/app/domains/sourcing/agents/sourcing_tool_registry.py` |
| 🟡 | `93fdefc95` | 2026-04-12 | Backend | fix: indentation in candidate_comparison_service.py broken by TODO comment | `lia-agent-system/app/domains/candidates/services/candidate_comparison_service.py` |
| 🟢 | `92c78649b` | 2026-04-11 | Testes | Update domain catalog and ensure all domains are properly registered — Update DOMAIN_CATALOG.md to reflect the accurate count of registered domains and improve the test fo | `lia-agent-system/tests/unit/test_ach020_api_docs.py` |
| 🔴 | `e02734183` | 2026-04-10 | Cross Back↔Front | Update user profile and authentication features — Introduces profile editing, password change functionality, and lazy loading for the job creation dom | `plataforma-lia/src/components/top-bar.tsx`<br>`plataforma-lia/src/contexts/auth-context.tsx` |
| 🟢 | `29e53fd81` | 2026-04-10 | Frontend (UI) | Improve display of enlarged icons in workflow reels — Adjust CSS to allow enlarged icons in the chat workflow reels to display fully by applying a clip-pa | `plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟡 | `b4823740d` | 2026-04-09 | IA | Add universal scope for tool permissions and update dependencies — Update `tool_permissions.yaml` to include a 'universal' scope for tools, and adjust `scope_config.py | `lia-agent-system/app/tools/scope_config.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml`<br>`lia-agent-system/app/tools/tool_permissions_loader.py` |
| 🟡 | `5d088d3d3` | 2026-04-06 | Backend | Add vacancy saturation checks and billing repository functionality — Adds vacancy saturation checking logic to the communication repository and introduces a new BillingR | `lia-agent-system/app/domains/billing/repositories/__init__.py`<br>`lia-agent-system/app/domains/billing/repositories/billing_repository.py`<br>`lia-agent-system/app/domains/communication/repositories/communication_repository.py` |
| 🟡 | `9c2cb8018` | 2026-04-06 | Backend | Add comment explaining initial free credits for new users — Adds a comment to clarify the purpose of INITIAL_FREE_CREDITS in credit_service.py, indicating it's  | `lia-agent-system/app/services/credit_service.py` |
| 🟡 | `10b011129` | 2026-04-06 | Backend | Organize application health and opinion modules for better structure — Update __init__.py files to properly structure the health_check and opinions domains. | `lia-agent-system/app/domains/health_check/repositories/__init__.py`<br>`lia-agent-system/app/domains/opinions/repositories/__init__.py` |
| 🟡 | `57281a577` | 2026-04-06 | Backend | Add new and update existing functionalities for managing candidates and jobs — Integrate new and update existing endpoints in the Rails client for managing candidates, jobs, and o | `lia-agent-system/app/auth/rails_jwt.py`<br>`lia-agent-system/app/services/ats_clients/wedotalent_rails.py`<br>`lia-agent-system/app/services/rails_adapter.py` |
| 🔴 | `642ece67f` | 2026-04-05 | Cross Back↔Front | Update daily briefing to show errors and refresh data — Modify the daily briefing card component to handle fetch errors by displaying an error UI instead of | `lia-agent-system/app/auth/rails_jwt.py`<br>`lia-agent-system/app/services/ats_clients/wedotalent_rails.py`<br>`plataforma-lia/src/components/daily-briefing-card.tsx` |

### Docs (geral)

**Descrição:** Documentos gerais — não cabem em outras categorias específicas.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** docs/**

**Docs de referência:** —

- **Commits:** 18  |  **Período:** 2026-03-15 → 2026-04-16  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×17 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `81778cd94` | 2026-04-16 | Docs | Update database schema documentation to list actively used tables — Refactors the `docs/DATABASE_SCHEMA.md` file to include only actively used database tables, reducing | `docs/DATABASE_SCHEMA.md`<br>`docs/DATABASE_SCHEMA_ACTIVE.md` |
| 🔴 | `d7462265a` | 2026-04-07 | Cross IA↔Front | Merged changes from vs4jplti/main — Replit-Task-Id: a94aa833-ba88-4578-847d-d41212bee642 | `lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/domains/communication/services/communication_service.py`<br>`lia-agent-system/app/domains/communication/services/message_providers.py` |
| 🟢 | `5db692bc9` | 2026-03-27 | Docs | Catalog all existing visual components on the platform — Create a comprehensive inventory of 465 visual components with categorization and details, and updat | `docs/PLATFORM_MAP.md`<br>`docs/specs/frontend/INVENTARIO_COMPONENTES.md` |
| 🟢 | `c58d25d8e` | 2026-03-27 | Docs | Update diagnostic document comparing React and Vue frontend standards — Create a comprehensive diagnostic document comparing React and Vue frontend specifications, includin | `docs/PLATFORM_MAP.md`<br>`docs/specs/frontend/DIAGNOSTICO_REACT_VUE.md` |
| 🟢 | `1eb896052` | 2026-03-26 | Docs | Add comprehensive Vue and Vuetify migration guides to design inventory — Update the design inventory document (docs/PRODUCT_DESIGN_INVENTORY.md) by reorganizing existing sec | `docs/PRODUCT_DESIGN_INVENTORY.md` |
| 🟢 | `f1dfd15f5` | 2026-03-24 | Docs | Add detailed UI specifications and AI prompt template for report generation — Adds Section 11.6 detailing UI indicators across three report tabs and Section 11.7 providing a comp | `docs/WSI_METHODOLOGY_COMPLETE_v2.md` |
| 🟢 | `c1615d3a0` | 2026-03-24 | Docs | Update methodology to define job description quality and create an ideal prompt — Refactor the methodology document to establish job description quality principles and an LLM prompt  | `docs/WSI_METHODOLOGY_COMPLETE_v2.md` |
| 🟢 | `977e38405` | 2026-03-24 | Docs | Add criteria for approving or rejecting candidates and a full consultant report — Add Phase 10 detailing absolute gates and score-based decision thresholds, and Phase 11 for a compre | `docs/WSI_METHODOLOGY_COMPLETE_v2.md` |
| 🟢 | `6bf0e714c` | 2026-03-24 | Docs | Create a guide for coding standards and best practices — Generate a comprehensive CODING_STANDARDS.md file detailing naming conventions, component structure, | `docs/CODING_STANDARDS.md` |
| 🟢 | `7b9317ff1` | 2026-03-24 | Docs | Add comprehensive architecture documentation for the platform — Create `docs/ARCHITECTURE.md` detailing frontend and backend stacks, AI/LLM strategy, integration pa | `docs/ARCHITECTURE.md` |
| 🟢 | `9994a42e3` | 2026-03-23 | Docs | Add verification for Jira description updates — Add a check after updating the Jira card description to ensure the content was successfully saved, a | `docs/JIRA_SCRIPTS_DOCUMENTATION.md`<br>`scripts/jira-audit-design.py`<br>`scripts/jira-fetch-analyze.py` |
| 🟢 | `9b9c44ddc` | 2026-03-23 | Docs | docs: corrige documentacao - Replit le codigo, GitHub multi-repo, Claude analisa — - Visao geral reescrita em Fase 1 (Replit le/coleta) e Fase 2 (Claude analisa) | `docs/JIRA_SCRIPTS_DOCUMENTATION.md` |
| 🟢 | `ffda2cc9a` | 2026-03-23 | Docs | scripts: Script 1 — adiciona ANTES/DEPOIS Vue, Vuetify defaults e bloco vuetify.ts — jira-fetch-analyze.py: | `docs/templates/jira-fetch-analyze-template-example.md`<br>`scripts/jira-fetch-analyze.py` |
| 🟢 | `f9d92fe91` | 2026-03-23 | Docs | scripts: atualiza jira-fetch-analyze.py (escopo completo) + templates de exemplo — jira-fetch-analyze.py — escopo ampliado: | `docs/templates/jira-audit-design-template-example.md`<br>`docs/templates/jira-fetch-analyze-template-example.md`<br>`scripts/jira-fetch-analyze.py` |
| 🟢 | `d1ad4ad6b` | 2026-03-23 | Docs | Update scoring system to a 0-10 scale and refine penalties — Update documentation to reflect the transition from a 0-5 to a 0-10 scoring scale for candidate eval | `docs/LIA_UNIFIED_METHODOLOGY.md` |
| 🟢 | `8271be3c2` | 2026-03-23 | Docs | Update methodology to detail competency extraction and question generation — Refine `docs/LIA_UNIFIED_METHODOLOGY.md` to clarify competency types (technical, behavioral, cultura | `docs/LIA_UNIFIED_METHODOLOGY.md` |
| 🟢 | `dd04a5590` | 2026-03-15 | Docs | docs: v4.3/v6.2 — 4 gaps críticos corrigidos para consumo por agentes IA — relatorio_capacidades_prompts_lia.md (v4.3): | `docs/RELATORIO_AUDITORIA_LIA.md`<br>`relatorio_capacidades_prompts_lia.md` |
| 🟢 | `fac7fab61` | 2026-03-15 | Docs | docs: Guia de Diagnóstico para Agentes IA adicionado nos dois documentos — RELATORIO_AUDITORIA_LIA.md → v6.2 | `docs/RELATORIO_AUDITORIA_LIA.md`<br>`relatorio_capacidades_prompts_lia.md` |

### Performance

- **Commits:** 17  |  **Período:** 2026-03-19 → 2026-04-16  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×9 🟡×5 🔴×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `a282ed2fb` | 2026-04-16 | Backend | Update database index for improved candidate search performance — Correctly apply a functional index on the lowercased seniority level column in the candidates table. | `lia-agent-system/alembic/versions/081_candidates_list_perf_indexes.py` |
| 🟢 | `f85160b72` | 2026-04-16 | Frontend (UI) | Improve performance and fix styling bugs by enabling Turbopack — Enable Turbopack, clean cache, and defer loading of certain components to improve initial load times | `plataforma-lia/src/app/[locale]/layout.tsx`<br>`plataforma-lia/src/app/styles/animations.css`<br>`plataforma-lia/src/components/layout/DeferredLayoutClients.tsx` |
| 🔴 | `f4075de94` | 2026-04-16 | Cross Back↔Front | Improve candidate search performance and reliability with retries and timeouts — Adds a `fetchWithRetry` utility to handle network requests with configurable attempts and timeouts.  | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts` |
| 🟡 | `ffd4381df` | 2026-04-13 | Frontend (UI) | fix(performance): Corrigir performance de carregamento das páginas (Task #182) — Changes implemented: | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/components/pages/use-tasks-core.ts` |
| 🔴 | `b4891f266` | 2026-04-11 | Cross IA↔Front | Task #138: Performance, Prompt Versioning & Rails Integration Readiness — All 6 subtasks completed with code review fixes applied: | `lia-agent-system/app/main.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx` |
| 🟡 | `25e7d7645` | 2026-04-05 | Cross IA↔Back | perf: lower vector cache threshold from 0.92 to 0.85 | `lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/vector_semantic_cache.py` |
| 🟢 | `2bdf4731a` | 2026-04-01 | Frontend (UI) | perf: lazy loading e bundle optimization — - indicators-page: dynamic import para StrategicTab, RecruitersTab, WorkModelsTab, PredictionsTab | `plataforma-lia/src/app/configuracoes/ai-credits/page.tsx`<br>`plataforma-lia/src/components/pages/indicators-page.tsx` |
| 🟢 | `d60af69de` | 2026-03-31 | Frontend (UI) | Improve modal loading performance by implementing dynamic imports — Implement dynamic imports for various modals in CandidatesPageModals.tsx to enhance loading performa | `plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` |
| 🟢 | `943dd5593` | 2026-03-31 | Frontend (UI) | Update modals to use dynamic imports for better performance — Modify several modal components in `job-kanban-page.tsx` and `unified-bulk-actions-bar.tsx` to use d | `plataforma-lia/src/components/pages/job-kanban-page.tsx`<br>`plataforma-lia/src/components/ui/unified-bulk-actions-bar.tsx` |
| 🟢 | `58969bbfb` | 2026-03-31 | Frontend (UI) | perf: habilita virtualizacao (@tanstack/react-virtual) nas 3 tabelas principais -- fecha ALT-VIRT | `plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanTableView.tsx`<br>`plataforma-lia/src/components/talent-funnel-tabs/favorites-tab.tsx` |
| 🟢 | `8ee979f8b` | 2026-03-30 | Empty/merge | perf: migra 10 hooks admin para useSWR -- elimina isMountedRef boilerplate -- ALT-SWR-02 | — |
| 🟢 | `bf3fb17fc` | 2026-03-30 | Empty/merge | perf: migra 4 hooks para useSWR — dedup/cache automático — ALT-SWR-01 | — |
| 🔴 | `afc7cceae` | 2026-03-30 | Frontend (UI) | perf: elimina key={index} restantes — 122 ocorrências em 75 arquivos — fecha ALT-03 definitivo | `plataforma-lia/src/app/admin/compliance/auditoria/sod/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/lgpd/consentimentos/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/riscos/continuidade/page.tsx` |
| 🟡 | `53fbf3e2a` | 2026-03-30 | Frontend (UI) | perf: substitui key={index} por keys estaveis nos 20 arquivos criticos — ALT-03 | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx`<br>`plataforma-lia/src/components/candidate-page/CandidatePageProfileTab.tsx` |
| 🟡 | `6279800ca` | 2026-03-30 | Frontend (UI) | perf: React.memo em componentes de lista + cleanup timers + AbortController + passive listeners — ALT-04 BCK-06 BCK-07 ALT-09 — - React.memo em CandidateBadges (+ fix import memo + fix displayName str | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx`<br>`plataforma-lia/src/components/candidate-page/CandidatePageProfileTab.tsx` |
| 🟢 | `877d0a349` | 2026-03-30 | Frontend (api/util) | perf: corrige Cache-Control por tipo de asset + ativa image optimization + reactStrictMode — fecha BLQ-01 BLQ-02 ALT-05 | `plataforma-lia/next.config.js` |
| 🟢 | `892d691f4` | 2026-03-19 | Docs | Add optimization plan to improve platform performance and reliability — Append a detailed 4-phase optimization plan to the LIA vs. V5 architecture document, focusing on age | `proposals/Paralelo_LIA_vs_V5_Arquitetura_IA.md` |

### §13 PARTE D — Foundation/Apify/Manifest

**Descrição:** PARTE D Foundation Stack (D0-D5): D0 Apify gateway com tracking enforced + budget check per tenant; D1 LIA tools enrichment + 5 company tools; D2 PreConditionChecker com 8 checks proativos (fail-open); D4 Platform Manifest YAML (single source of truth pages/methodology/capabilities); D5 onboarding guiado no CompanySettingsReActAgent.

**⚠️ Dependências para cherry-pick:** Apify gateway = ÚNICO canal (zero bypass via httpx) | platform_manifest.yaml carregado via lru_cache | PreConditionChecker integrado no main_orchestrator | ConsumptionTrackingService.record_apify_call em finally block

**Arquivos canônicos:** lia-agent-system/app/domains/sourcing/services/apify_service.py, app/orchestrator/precondition_checker.py, app/config/platform_manifest.yaml, app/shared/platform_manifest.py, app/domains/sourcing/tools/enrichment_tools.py, app/domains/company_settings/tools/import_tools.py

**Docs de referência:** DEVELOPER_HANDOFF.md PARTE D

- **Commits:** 17  |  **Período:** 2026-03-31 → 2026-04-19  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×12 🔴×3 🟢×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `ce507b683` | 2026-04-19 | IA | Add fallback for navigation intent patterns if manifest is unavailable — Modify `navigation_intent.py` to load navigation patterns from `platform_manifest.yaml`, with a fall | `lia-agent-system/app/orchestrator/navigation_intent.py` |
| 🟡 | `f4106776c` | 2026-04-19 | Cross IA↔Back | feat(platform): D4 Platform Manifest — single source of truth for pages, methodology, capabilities — Replaces hardcoded page lists + hardcoded _PLATFORM_KNOWLEDGE text with | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `a2b2310fb` | 2026-04-19 | Backend | feat(apify): D0 gateway — enforced tracking + budget check per tenant — Refactor ApifyService.run_apify_actor as the single gateway for all Apify calls: | `lia-agent-system/app/domains/sourcing/services/apify_search_service.py`<br>`lia-agent-system/app/domains/sourcing/services/apify_service.py` |
| 🟢 | `ec9797157` | 2026-04-17 | Testes | Task #401: Add tests covering the Apify enrichment count banner — Added a new component test file | `plataforma-lia/src/components/pages/candidates/__tests__/CandidatesTableArea.test.tsx` |
| 🟡 | `29675834d` | 2026-04-17 | Frontend (UI) | Task #399: Mostrar candidatos enriquecidos via Apify no Funil de Talentos — O backend já vinha devolvendo `enrichment_attempted` ao lado de | `plataforma-lia/src/components/pages/candidates-page.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesTableArea.tsx` |
| 🟡 | `b0b3b27d2` | 2026-04-14 | Frontend (UI) | Update documentation to reflect integration of Apify service for candidate enrichment — Modify audit documentation files related to Apify integration phases and flow traces. | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx`<br>`plataforma-lia/src/components/pages/jobs/TableFiltersPanel.tsx` |
| 🟡 | `af817da57` | 2026-04-13 | Backend | Task #177: Apify Search Fallback — fix review issues — Addresses all code review findings: | `lia-agent-system/app/api/v1/candidate_search/search.py`<br>`lia-agent-system/app/domains/sourcing/services/apify_search_service.py` |
| 🟡 | `6212c221d` | 2026-04-13 | Backend | Task #177: Apify Search Fallback — 3-step pipeline as Pearch alternative — Implements a full candidate search pipeline via Apify as automatic fallback | `lia-agent-system/app/api/v1/candidate_search/search.py`<br>`lia-agent-system/app/domains/billing/services/consumption_tracking_service.py`<br>`lia-agent-system/app/domains/sourcing/services/apify_search_service.py` |
| 🟡 | `27add2f1f` | 2026-04-13 | Backend | fix: resolve merge conflict markers in archetypes.py (Task #172 Apify T2) — Escolhido INCOMING em ambos os blocos — alinhado com os 4 arquivos irmaos | `lia-agent-system/app/api/v1/candidate_search/archetypes.py` |
| 🔴 | `613bf4db6` | 2026-04-13 | Frontend (UI) | Task #173: Update talent funnel pricing — consistent "credits + $0.01 Apify" model — Core estimator (calculateCreditsLocally): | `plataforma-lia/src/components/candidate-preview/CandidatePreviewHeader.tsx`<br>`plataforma-lia/src/components/candidate-preview/ProfileTabTypes.ts`<br>`plataforma-lia/src/components/expandable-ai-prompt/EAPExpandedSection.tsx` |
| 🟡 | `82c9c6ec5` | 2026-04-13 | Backend | Task #172: Apify T2 — Pipeline de Busca: Enrichment Obrigatório + Remover Pro — Changes implemented: | `lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/jd_search.py`<br>`lia-agent-system/app/api/v1/candidate_search/search.py` |
| 🔴 | `9969e1358` | 2026-04-13 | Cross Back↔Front | feat(#170): Intelligent Apify + Pearch pipeline for candidate enrichment — - Enrichment pipeline routes UUID candidates through enrich_batch (with DB | `lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact.py` |
| 🟡 | `e964903cd` | 2026-04-13 | Backend | Task #171: Apify T1 — Backend Core: Actor, Mapper e Serviço de Enriquecimento — Changes: | `lia-agent-system/app/domains/candidates/services/candidate_enrichment_service.py`<br>`lia-agent-system/app/domains/sourcing/services/contact_enrichment_service.py`<br>`lia-agent-system/libs/models/lia_models/webhook.py` |
| 🟡 | `bd9f1eec4` | 2026-04-12 | Backend | Add Apify integration for contact enrichment and health check — Integrates Apify API for contact data enrichment, adds a health check endpoint, and includes compreh | `lia-agent-system/app/api/v1/integrations_hub.py`<br>`lia-agent-system/app/domains/sourcing/services/apify_mapper.py`<br>`lia-agent-system/app/domains/sourcing/services/apify_service.py` |
| 🔴 | `d26626cfd` | 2026-04-12 | Cross Back↔Front | T005: Frontend - Remove Pro search mode, update costs for Apify enrichment — - Updated candidate-search.ts: searchType now "fast" only, calculateCreditsLocally | `lia-agent-system/app/api/v1/candidate_search/_shared.py`<br>`lia-agent-system/app/api/v1/candidate_search/archetypes.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact.py` |
| 🟡 | `9feb33b11` | 2026-04-12 | Backend | refactor: replace Glassdoor scraper with multi-actor Apify strategy — - Removed bebity/glassdoor-salary-scraper (unreliable) | `lia-agent-system/app/domains/sourcing/services/apify_service.py` |
| 🟢 | `6cfa2bf2d` | 2026-03-31 | Docs | docs: v6.5 — mark G5 Apify API key as RESOLVIDO — - G5 marked resolved: APIFY_API_KEY configured as Replit secret | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |

### Jobs (FE pages)

**Descrição:** Páginas e componentes de Vagas no FE — dashboard, listagem, edição, criação.

**⚠️ Dependências para cherry-pick:** Endpoint /api/backend-proxy/job-vacancies/* | Hooks src/hooks/jobs

**Arquivos canônicos:** plataforma-lia/src/components/pages/jobs/**, src/components/jobs/**

**Docs de referência:** —

- **Commits:** 16  |  **Período:** 2026-03-29 → 2026-04-13  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×15 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `787ac1c05` | 2026-04-13 | Frontend (UI) | fix: garantir auto-login em dev ignorando cookie lia_logged_out — - middleware.ts: em DEV_AUTO_LOGIN, ignora cookie lia_logged_out e sempre | `plataforma-lia/src/components/pages/jobs/hooks/useJobsData.ts`<br>`plataforma-lia/src/components/pages/use-tasks-core.ts` |
| 🟢 | `28ab5fb97` | 2026-04-08 | Frontend (UI) | Set default tab to show job listings immediately — Update default filter state in the jobs page hook to display job listings by default. | `plataforma-lia/src/components/pages/jobs/hooks/useJobsFilters.ts` |
| 🟢 | `78b1f7b11` | 2026-04-03 | Frontend (UI) | Adjust button styles for a consistent visual appearance across the platform — Update border-radius from `rounded-full` to `rounded-lg` in JobsDashboardView.tsx and lia-vacancy-qu | `plataforma-lia/src/components/pages/jobs/JobsDashboardView.tsx`<br>`plataforma-lia/src/components/ui/lia-vacancy-queries-guide.tsx` |
| 🟢 | `1ac0f4180` | 2026-04-03 | Frontend (UI) | Update buttons to match design specifications for consistency — Adjusted button styles in `JobsDashboardView.tsx` and `lia-vacancy-queries-guide.tsx` to use `rounde | `plataforma-lia/src/components/pages/jobs/JobsDashboardView.tsx`<br>`plataforma-lia/src/components/ui/lia-vacancy-queries-guide.tsx` |
| 🟢 | `2820e5cb2` | 2026-04-03 | Frontend (UI) | Update job management buttons to match talent funnel style — Refactor styling of buttons in JobsDashboardView.tsx and LiaVacancyQueriesGuide.tsx to use the `lia- | `plataforma-lia/src/components/pages/jobs/JobsDashboardView.tsx`<br>`plataforma-lia/src/components/ui/lia-vacancy-queries-guide.tsx` |
| 🟢 | `fe5da36e4` | 2026-04-03 | Frontend (UI) | Align job buttons and containers visually with talent funnel elements — Update the background and padding of the job dashboard container to match the talent funnel componen | `plataforma-lia/src/components/pages/jobs/JobsDashboardView.tsx` |
| 🟢 | `dd9afe6e3` | 2026-04-03 | Frontend (UI) | Align visual styles for buttons and search icons across the platform — Update CSS classes and component styles in JobsDashboardView.tsx and SSIModeNatural.tsx to ensure co | `plataforma-lia/src/components/pages/jobs/JobsDashboardView.tsx`<br>`plataforma-lia/src/components/search/ssi-modes/SSIModeNatural.tsx` |
| 🟢 | `512093527` | 2026-04-02 | Frontend (UI) | Update job candidate display to use standard tooltip component — Replaces custom CSS tooltip with Radix/shadcn Tooltip component in JobsCompactTableView.tsx for impr | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx` |
| 🟢 | `f83e6052d` | 2026-04-01 | Frontend (UI) | Add a bottom border to the jobs table header for better separation — Update the jobs table header to use a box shadow for a visible bottom border, improving separation f | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx` |
| 🟢 | `9deb5bf28` | 2026-04-01 | Frontend (UI) | Improve table header separation with a subtle shadow effect — Adjusted JobsCompactTableView.tsx to use an inset box-shadow on the thead element for a more reliabl | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx` |
| 🟢 | `fbf5eb4af` | 2026-04-01 | Frontend (UI) | Add a bottom border to the table header for better visual separation — Move the bottom border from the `thead` element to the `tr` element within the `thead` in `JobsCompa | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx` |
| 🟢 | `77d2f69b5` | 2026-04-01 | Frontend (UI) | Add a bottom border to the table header to separate it from the content — Update JobsCompactTableView.tsx to add `border-b border-lia-border-subtle` to the thead element. | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx` |
| 🟢 | `b71007d60` | 2026-04-01 | Frontend (UI) | Improve table layout by adjusting container height — Update the table container's height property from `h-full` to `max-h-full` in `JobsCompactTableView. | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx` |
| 🟢 | `5f328c435` | 2026-04-01 | Frontend (UI) | Add border around the table of job opportunities — Add a border and rounded corners to the jobs table container in JobsCompactTableView.tsx to improve  | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx` |
| 🟡 | `e60a00bef` | 2026-03-29 | Frontend (UI) | Centralize status labels for improved maintainability and consistency — Refactors multiple components to import screening status labels from a centralized `SCREENING_STATUS | `plataforma-lia/src/components/jobs/JobEditTab.tsx`<br>`plataforma-lia/src/components/pages/job-kanban-page.tsx`<br>`plataforma-lia/src/components/pages/jobs/JobPreviewPanel.tsx` |
| 🟢 | `622736784` | 2026-03-29 | Frontend (UI) | Improve loading state management for job vacancy listings — Move `setIsLoadingJobs(false)` to execute after `setBackendJobs()` in `useJobsPageCore.tsx` to ensur | `plataforma-lia/src/components/pages/jobs/hooks/useJobsPageCore.tsx` |

### Scripts / CLI

**Descrição:** Scripts e CLIs auxiliares (Claude settings, find configs, helpers ad-hoc).

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** .claude/settings.local.json, lia-agent-system/scripts/**

**Docs de referência:** —

- **Commits:** 16  |  **Período:** 2026-03-21 → 2026-04-26  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×16

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `22b581b46` | 2026-04-26 | Backend | Improve code quality by disallowing unsafe attribute access on models — Add a new pre-commit hook to prevent the use of `getattr` with default values on SQLAlchemy model in | `lia-agent-system/.pre-commit-config.yaml`<br>`lia-agent-system/scripts/check_no_getattr_on_models.py` |
| 🟡 | `05db9825a` | 2026-04-08 | Backend | Add a new hiring manager user and update vacancy status — Update the seed data script to add a new user with the 'hiring_manager' role and change a vacancy's  | `lia-agent-system/scripts/seed_full_platform.py` |
| 🟡 | `8516252cb` | 2026-04-07 | Backend | Update GitHub token retrieval to support multiple environment variables — Refactor GitHub token retrieval in `github_service.py` and script files to check for "GITHUB_TOKEN", | `lia-agent-system/app/domains/sourcing/services/github_service.py` |
| 🟡 | `2b02e46a2` | 2026-03-27 | Infra/Config | Add a command to find configuration files for Nuxt projects — Add a new bash command to find .config.js, .config.ts, and nuxt.config.* files within the project di | `.claude/settings.local.json` |
| 🟡 | `b41dc0739` | 2026-03-21 | Backend | Add a new screen configuration for the left-hand side menu — Update the design audit generator script to include a new screen configuration for the "Menu Lateral | `lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `4c32c329a` | 2026-03-21 | Backend | Enhance design audits by automatically mapping mentioned elements to their code — Integrate element-to-React component mapping into bug and design audit generation scripts to automat | `lia-agent-system/scripts/bug_spec_generator.py`<br>`lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `a360dec34` | 2026-03-21 | Backend | Add image analysis to bug and design audit generation — Integrates Vision API for screenshot analysis in bug_spec_generator and design_audit_generator, adds | `lia-agent-system/scripts/bug_spec_generator.py`<br>`lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `0a79c22c6` | 2026-03-21 | Backend | Add option to post audits as comments directly — Introduces the `--as-comment` flag to `cmd_post` in `design_audit_generator.py`, allowing direct pos | `lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `cd34e8057` | 2026-03-21 | Backend | Improve session fetching to support cookies and public links — Update `_betterbugs_fetch_session` function to support `BETTERBUGS_SESSION_COOKIE` env var, attempt  | `lia-agent-system/scripts/bug_spec_generator.py`<br>`lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `acf7fb7fb` | 2026-03-21 | Backend | Add BetterBugs API integration for enhanced bug reporting — Integrates BetterBugs REST API into bug_spec_generator.py and design_audit_generator.py to fetch ses | `lia-agent-system/scripts/bug_spec_generator.py`<br>`lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `047ce6b6d` | 2026-03-21 | Backend | Extract screenshots and links from BetterBugs Jira cards — Adds functionality to extract embedded screenshots and relevant links from BetterBugs Jira cards by  | `lia-agent-system/scripts/bug_spec_generator.py`<br>`lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `090a373db` | 2026-03-21 | Backend | Integrate real Vue code snippets into audit reports and add fallback for Jira posts — Add GitHub API integration to fetch real Vue code snippets for audit reports. Update Jira posting lo | `lia-agent-system/scripts/bug_spec_generator.py`<br>`lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `b0dc74f02` | 2026-03-21 | Backend | Add script to generate design audit templates for UI screens — Adds a Python script that fetches Jira card descriptions, extracts UI component information from Rea | `lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `287367535` | 2026-03-21 | Backend | Enhance bug report template with technical specification details — Update bug specification template to include technical details, component comparisons, and token tab | `lia-agent-system/scripts/bug_spec_generator.py` |
| 🟡 | `7fc035b64` | 2026-03-21 | Backend | Improve tag extraction and error handling for Jira interactions — Enhance tag extraction regex to support various formats, add warning logs for connector authenticati | `lia-agent-system/scripts/bug_spec_generator.py` |
| 🟡 | `261fcf456` | 2026-03-21 | Backend | Add script to generate bug specifications from Jira cards — Add a new Python script for fetching Jira card data and posting bug specifications. | `lia-agent-system/.env.example`<br>`lia-agent-system/scripts/bug_spec_generator.py` |

### UI Components (FE library)

**Descrição:** Biblioteca de componentes UI (botões, inputs, cards, primitives). Mudanças aqui afetam toda a app.

**⚠️ Dependências para cherry-pick:** DS v4.2.2 tokens | tailwind config

**Arquivos canônicos:** plataforma-lia/src/components/ui/**

**Docs de referência:** 00-design-system-v4.2.2.md

- **Commits:** 16  |  **Período:** 2026-03-30 → 2026-04-11  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×13 🟡×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `03956df08` | 2026-04-11 | Frontend (UI) | Design System: replace 179 shadcn defaults with lia tokens, remove 4 decorative borders | `plataforma-lia/src/components/ai/AISuggestionBadge.tsx`<br>`plataforma-lia/src/components/candidate-preview/ProfileInfoCards.tsx`<br>`plataforma-lia/src/components/candidate-profile/ProfileExperienceSection.tsx` |
| 🟢 | `3d34b63b8` | 2026-04-10 | Frontend (UI) | Improve visibility of chat input elements and icons — Update text color for placeholder, buttons, and labels in the chat input component and audio record  | `plataforma-lia/src/components/ui/audio-record-button.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatInput.tsx` |
| 🟢 | `fb5a58785` | 2026-04-10 | Frontend (UI) | Adjust display of workflow icons and header elements for better visibility — Update chat workflow reels to prevent icon clipping and unify header icon colors with input border u | `plataforma-lia/src/components/ui/chat-workflow-reels.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatHeader.tsx` |
| 🟢 | `9c788f782` | 2026-04-08 | Frontend (UI) | Align chat interface appearance with design system standards — Update chat page, prompt suggestions dock, and quick action chips to use consistent font, sizing, an | `plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/ui/prompt-suggestions-dock.tsx`<br>`plataforma-lia/src/components/ui/quick-action-chips.tsx` |
| 🟢 | `80fc294b9` | 2026-04-03 | Frontend (UI) | Remove incomplete setup progress badge from application interface — Remove the SetupAlertBadge component and its associated import from the main layout file, and delete | `plataforma-lia/src/app/layout.tsx`<br>`plataforma-lia/src/components/ui/setup-alert-badge.tsx` |
| 🟢 | `d52bd07e7` | 2026-04-03 | Frontend (UI) | Align button styles across job and query components for visual consistency — Update button classes in JobsDashboardView, LiaQueriesGuide, LiaSearchQueriesGuide, and LiaVacancyQu | `plataforma-lia/src/components/pages/jobs/JobsDashboardView.tsx`<br>`plataforma-lia/src/components/ui/lia-queries-guide.tsx`<br>`plataforma-lia/src/components/ui/lia-search-queries-guide.tsx` |
| 🟢 | `c9346b477` | 2026-04-03 | Frontend (UI) | Standardize button styles across different sections for a consistent look — Modify CSS classes and remove inline styles in `lia-queries-guide.tsx`, `lia-search-queries-guide.ts | `plataforma-lia/src/components/ui/lia-queries-guide.tsx`<br>`plataforma-lia/src/components/ui/lia-search-queries-guide.tsx`<br>`plataforma-lia/src/components/ui/lia-vacancy-queries-guide.tsx` |
| 🟢 | `eb2c0e494` | 2026-04-03 | Frontend (UI) | Apply consistent styling and transitions to various interactive elements — Refactor CSS classes and transition properties across multiple components, including `JobsDashboardV | `plataforma-lia/src/components/pages/jobs/JobsDashboardView.tsx`<br>`plataforma-lia/src/components/search/ssi-modes/SSIModeNatural.tsx`<br>`plataforma-lia/src/components/ui/lia-queries-guide.tsx` |
| 🟡 | `190d2fb8a` | 2026-04-02 | Frontend (UI) | Task start baseline checkpoint for code review | `plataforma-lia/src/components/ui/ai-disclaimer.tsx`<br>`plataforma-lia/src/components/ui/big-five-profile.tsx`<br>`plataforma-lia/src/components/ui/candidate-card.tsx` |
| 🟢 | `d1b0ff4b1` | 2026-04-02 | Frontend (UI) | Update component backgrounds to white for better visibility — Adjusted background colors of `BulkSelectionBarInline` and `UnifiedBulkActionsBar` components from l | `plataforma-lia/src/components/ui/bulk-selection-bar.tsx`<br>`plataforma-lia/src/components/ui/unified-bulk-actions-bar.tsx` |
| 🟢 | `784946f1d` | 2026-04-02 | Frontend (UI) | Align table appearance and candidate avatar sizes across the platform — Adjust avatar sizes in CandidatesTable and cell-renderers.tsx to h-8 w-8 and h-7 w-7 respectively. R | `plataforma-lia/src/components/pages/candidates/CandidatesTable.tsx`<br>`plataforma-lia/src/components/tables/cell-renderers.tsx`<br>`plataforma-lia/src/components/tables/unified-candidate-table.tsx` |
| 🟢 | `ee0a5fb30` | 2026-04-02 | Frontend (UI) | Align styles and appearance across all candidate tables — Update CSS and markup in `candidate-table-row.tsx`, `cell-renderers.tsx`, and `unified-candidate-tab | `plataforma-lia/src/components/tables/candidate-table-row.tsx`<br>`plataforma-lia/src/components/tables/cell-renderers.tsx`<br>`plataforma-lia/src/components/tables/unified-candidate-table.tsx` |
| 🟢 | `9037177d5` | 2026-03-31 | Frontend (UI) | design: WeDOTalent color standardization — zinc/neutral → lia-* canonical tokens — - Replace all text-zinc-*/bg-zinc-*/border-zinc-* with lia-* semantic tokens | `plataforma-lia/src/components/ui/badge.tsx`<br>`plataforma-lia/src/components/ui/skeleton.tsx` |
| 🟢 | `2025b770f` | 2026-03-30 | Frontend (UI) | Improve score display and interactivity for evaluation items — Refactor ScoreIconButton component for better rendering and memoization, updating score ID types and | `plataforma-lia/src/components/ui/score-icon-button.tsx` |
| 🟢 | `422c5dfbc` | 2026-03-30 | Frontend (UI) | Update UI components for better rendering and memoization — Refactor `ContextPill` and `EmptyState` components to use `React.memo` for performance optimization  | `plataforma-lia/src/components/ui/context-pill.tsx`<br>`plataforma-lia/src/components/ui/empty-state.tsx` |
| 🟡 | `dad4d1cca` | 2026-03-30 | Frontend (UI) | Fix clipped content and improve layout rendering in sidebar — Adjusted the Card component's height calculation in LIASearchSidebar to `h-full` to ensure it respec | `plataforma-lia/src/components/expandable-ai-prompt/EAPTabContent.tsx`<br>`plataforma-lia/src/components/pages/candidates/LIASearchSidebar.tsx`<br>`plataforma-lia/src/components/pages/jobs/InlineChatPanel.tsx` |

### §2 Harness / CI sensors

- **Commits:** 16  |  **Período:** 2026-04-21 → 2026-04-28  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×9 🟢×7

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `449a442e8` | 2026-04-28 | IA | feat(harness): CI sensor check_deprecated_rail_a_tools.py — harness-engineering sensor computacional: CI guard that detects @deprecated | `lia-agent-system/scripts/check_deprecated_rail_a_tools.py` |
| 🟢 | `0cfd9ce67` | 2026-04-27 | Docs | feat(harness): pre-commit sensor branch-map-theme-check (ativo) — Implementa o sensor computacional pendente da regra Guide 1+2 (CLAUDE.md): | `.pre-commit-config.yaml`<br>`CLAUDE.md`<br>`lia-agent-system/CLAUDE.md` |
| 🟢 | `0fc286d25` | 2026-04-27 | Docs | feat(harness): regra de organizacao de branch + BRANCH_MAP em CLAUDE.md (project + workspace) e .cursorrules — Aplica a 3 arquivos canonicos: | `.cursorrules`<br>`CLAUDE.md`<br>`lia-agent-system/CLAUDE.md` |
| 🟡 | `9f472462e` | 2026-04-27 | Backend | feat(harness): C. validate skill E2E + promote G6+G7 hooks to block-only — Skill /create-canonical-agent validada end-to-end via dummy domain temporario: | `lia-agent-system/.pre-commit-config.yaml`<br>`lia-agent-system/scripts/check_agent_compliance.py` |
| 🟡 | `c3755076c` | 2026-04-27 | Backend | fix(harness): B. W1.6+ cleanup G6 — 21 getattr violations em 13 arquivos (G6 24 -> 0) — Apos W1.1+W1.2+W1.3 fechar Teams getattr (3 fixes) e Wave 4 confirmar plataforma canonical, agora at | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/api/v1/bulk_actions.py`<br>`lia-agent-system/app/api/v1/candidates/candidates_crud.py` |
| 🟢 | `e56d3dd2f` | 2026-04-27 | Testes | test(harness): A. revalidate W1.4 xfails — 2 false-positives flipped to strict + 1 refined — Wave 4 finding: aplicar mesmo padrao heritage-aware aos xfails do W1.4 reduz backlog reportado. | `lia-agent-system/tests/security/test_red_team_teams_coverage_w1_4.py` |
| 🟢 | `a02ed3137` | 2026-04-27 | Testes | test(harness): W4.4 audit edge cases (analytics-only) — sentinel + non-issue confirmed — Investigacao W4.4: orchestrator audit e CONDITIONAL em result.candidate_id/job_id (main_orchestrator | `lia-agent-system/tests/integration/test_audit_edge_cases_w4_4.py` |
| 🟡 | `9021db1ba` | 2026-04-27 | Backend | fix(harness): W4.3 sensor v4 alias-aware + content-source-aware (System YAML 61% -> 100%) — Investigacao W4.3: 5 agents (pipeline, policy, jobs_management, kanban, talent) reportados como miss | `lia-agent-system/scripts/audit_agent_compliance.py`<br>`lia-agent-system/scripts/check_agent_compliance.py` |
| 🟡 | `3d983b248` | 2026-04-27 | Backend | fix(harness): W4.2 audit + G7 v3 cross-domain tool_registry (corrige falso-positivo) — Investigacao W4.2: pipeline_react_agent reportado como missing tool registry (sensor v2). Discovery  | `lia-agent-system/scripts/audit_agent_compliance.py`<br>`lia-agent-system/scripts/check_agent_compliance.py` |
| 🟡 | `2dcb2d761` | 2026-04-27 | Backend | fix(harness): W4.1 register_agent canonical em automation + autonomous (gap real) — Auditoria 2026-04-27 v2 (W3.3 heritage-aware) identificou 2 dos 13 agents sem decorator @register_ag | `lia-agent-system/app/domains/automation/agents/automation_react_agent.py`<br>`lia-agent-system/app/domains/autonomous/agents/autonomous_react_agent.py`<br>`lia-agent-system/tests/integration/test_register_agent_canonical_w4_1.py` |
| 🟡 | `3d2b5ca94` | 2026-04-27 | Backend | fix(harness): W3.3 v2 audit_agent_compliance heritage-aware (corrige falsos negativos) — Paulo apontou (2026-04-27): "esses numeros estao corretos? 0% PII / 0% LLM | `lia-agent-system/scripts/audit_agent_compliance.py` |
| 🟡 | `7d150e7a4` | 2026-04-27 | Backend | feat(harness): W3.3 audit retroativo + AGENT_COMPLIANCE_MATRIX_2026-04-27.md — Auditoria 2026-04-27 (Paulo): "como garantir que novos agentes sigam canon?" | `lia-agent-system/scripts/audit_agent_compliance.py` |
| 🟡 | `94aaf06e9` | 2026-04-27 | Backend | feat(harness): W3.1 + W3.2 anatomy doc + G7 sensor de compliance canonical — Auditoria 2026-04-27 (Paulo): "como garantir que novos dominios/agentes/tools | `lia-agent-system/.pre-commit-config.yaml`<br>`lia-agent-system/scripts/check_agent_compliance.py` |
| 🟢 | `82aa4f6cc` | 2026-04-21 | Docs | harness-engineering: fill catalogs with real LIA guides and sensors (task #736) — Turned the harness-engineering skill from a generic methodology into a | `.agents/skills/harness-engineering/SKILL.md`<br>`.agents/skills/harness-engineering/references/guides-catalog.md`<br>`.agents/skills/harness-engineering/references/lia-stage-mapping.md` |
| 🟢 | `3d3a76279` | 2026-04-21 | Docs | Add harness-engineering meta-skill — Adds the `.agents/skills/harness-engineering/` skill that codifies the | `.agents/skills/SKILLS_INDEX.md`<br>`.agents/skills/harness-engineering/SKILL.md`<br>`.agents/skills/harness-engineering/references/audit-template.md` |
| 🟢 | `5e7d94102` | 2026-04-21 | Docs | docs(skills): add harness-engineering-lia skill for auto-activation on LIA stack work — Skill de projeto que complementa a skill global harness-engineering com | `lia-agent-system/.claude/skills/harness-engineering-lia/SKILL.md` |

### §9 Tenant Isolation / Multi-tenancy

**Descrição:** DEFAULT_DOMAIN routing warning + chat-capabilities CI gate, consolidate tenant-isolation residual (fecha #329, #335, #336, #359, #361), proteção de 8 dirs estratégicos + recategorização, WSI tenant id forwarding.

**⚠️ Dependências para cherry-pick:** company_id sempre do JWT (nunca do payload) | _is_dev_environment patched em testes | validate_company_access em todo endpoint sensível

**Arquivos canônicos:** lia-agent-system/app/api/v1/* (tenant guards), app/auth/*, app/shared/tenant_*.py

**Docs de referência:** docs/RLS_CONTRACT.md, docs/CANONICAL_SOURCES_SPEC.md

- **Commits:** 16  |  **Período:** 2026-03-31 → 2026-04-22  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×10 🔴×4 🟢×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `af76de95f` | 2026-04-22 | Frontend (UI) | fix(multi-tenancy): session 2026-04-22 — 16 proxy routes + company_id fixes + handoffs — - getSessionAuth() dual-auth helper (WorkOS SSO + JWT) | `plataforma-lia/src/app/api/backend-proxy/ai-credits/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/alerts/config/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/billing/invoices/[invoice_id]/pay/route.ts` |
| 🟡 | `2f80103aa` | 2026-04-21 | Cross IA↔Back | Pass company_id to all remaining LIA SystemPromptBuilder callers — Original task (#694): SystemPromptBuilder.build() now injects a tenant | `lia-agent-system/app/api/v1/candidate_search/misc_search.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/interview_notes.py` |
| 🟡 | `2f19de689` | 2026-04-20 | Backend | Task #673: Consolidate tenant-isolation residual (closes #329, #335, #336, #359, #361) — Five separate tasks tracked overlapping pieces of the same P0-1 risk | `lia-agent-system/.pre-commit-config.yaml`<br>`lia-agent-system/app/core/tenant.py`<br>`lia-agent-system/app/domains/analytics/tools/analytics_query_tools/_base.py` |
| 🟡 | `21f90805f` | 2026-04-20 | Cross IA↔Back | Task #672 — DEFAULT_DOMAIN routing warning + chat-capabilities CI gate — Closes Fase 2C P0-2 (silent fallback) and P2-4 (regression guard). | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py` |
| 🟡 | `6fd638fbc` | 2026-04-20 | Backend | tests: assert tool registries fail-closed without company_id — Task #330: add an end-to-end test that iterates over every tool exported | `lia-agent-system/app/domains/autonomous/agents/autonomous_tool_registry.py`<br>`lia-agent-system/tests/shared/__init__.py`<br>`lia-agent-system/tests/shared/test_tool_handler_isolation.py` |
| 🟡 | `bf60a5df7` | 2026-04-19 | Cross IA↔Back | fix eval: remove wrong CAST uuid, expand short job_id filter, wizard company_id rule | `lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟡 | `934fda6ab` | 2026-04-18 | Cross IA↔Back | audit(canonical): P1 fixes — entity_id precedence + cross-tenant guard in generate_report — - analytics_actions.py: 3 functions now resolve job_id via entity_id before job_vacancy_id fallback | `lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py` |
| 🟢 | `a48afdd67` | 2026-04-17 | Frontend (UI) | Task #267: Use real company_id in Kanban page core — Original task: useKanbanPageCore.ts was reading the company id from | `plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` |
| 🟡 | `3f7fc6d92` | 2026-04-17 | Backend | fix(chat): A1-B normalize company_id in send_message and stream_message — chat.py was using current_user.company_id ('37' in dev) directly without | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `05056bec7` | 2026-04-17 | Backend | Task #346: add Candidate.company_id with backfill migration — Model & migration | `lia-agent-system/alembic/versions/082_add_candidate_company_id.py`<br>`lia-agent-system/app/api/v1/applications.py`<br>`lia-agent-system/app/api/v1/candidate_search/contact_persistence.py` |
| 🟡 | `907c625a8` | 2026-04-13 | Backend | fix(LIA-SEC-02,PE-9): Rails JWT company_id resolution fail-closed — resolve_company_from_rails_user now raises RailsCompanyResolutionError on: | `lia-agent-system/app/auth/rails_jwt.py` |
| 🟡 | `0566046f2` | 2026-04-13 | Backend | cleanup(LIA-C01): remove deprecated _require_company_id from granular_consent + bias_audit — Both endpoints already use get_verified_company_id from tenant_guard (JWT-verified). | `lia-agent-system/app/api/v1/bias_audit.py`<br>`lia-agent-system/app/api/v1/granular_consent.py` |
| 🟢 | `5e6010db2` | 2026-04-12 | Frontend (UI) | fix: TypeScript error — user.company_id → user.company (matches auth context type) | `plataforma-lia/src/components/pages/modules-page.tsx` |
| 🔴 | `7dff2e8a3` | 2026-04-05 | Cross IA↔Back | Task #15: Migrate legacy company_id/tenant_id — remove all fallback defaults — - Alembic migration 059: audit script covering 16 tables | `lia-agent-system/alembic/versions/059_migrate_legacy_company_ids.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/applications.py` |
| 🔴 | `535f05984` | 2026-04-05 | Cross IA↔Front | Fix multi-tenancy company_id isolation (Task #5) — Backend: | `lia-agent-system/alembic/versions/058_add_client_account_id_to_company_profiles.py`<br>`lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/orchestrator/action_handlers/pipeline_actions.py` |
| 🔴 | `cfba6eddd` | 2026-03-31 | Cross Back↔Front | fix(security): ephemeral HMAC secret + valid UUID fallback for company_id — - HMAC secret now uses cryptographic random if env var not set (with warning) | `lia-agent-system/app/api/v1/communication_optout.py`<br>`plataforma-lia/src/components/modals/edit-job-modal.tsx`<br>`plataforma-lia/src/components/modals/edit-job-sections/EditJobModalPrivacy.tsx` |

### Chat UI (FE)

**Descrição:** Componentes de chat geral — mensagens, lista, input, plan progress card.

**⚠️ Dependências para cherry-pick:** WebSocket /api/v1/agent_chat_ws | proactive_hints serializer

**Arquivos canônicos:** plataforma-lia/src/components/chat/**

**Docs de referência:** —

- **Commits:** 13  |  **Período:** 2026-03-29 → 2026-04-16  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×7 🟡×4 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `eb549a121` | 2026-04-16 | Frontend (UI) | Improve chat functionality by fixing connection issues and response handling — Address audit recommendations for chat transport, WebSocket token retrieval, and health route. Imple | `plataforma-lia/src/app/api/backend-proxy/health/route.ts` |
| 🟢 | `fcd55216f` | 2026-04-15 | Frontend (UI) | Fix chat functionality with REST fallback and improve auth token generation — Implement REST fallback for chat functionality, update API rewrites in next.config.js, and enhance d | `plataforma-lia/src/app/api/auth/ws-token/route.ts` |
| 🔴 | `39252ae74` | 2026-04-11 | Cross IA↔Front | DS final: remaining chat bubble and handler hooks | `lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`plataforma-lia/src/components/chat/chat-bubble-base.tsx`<br>`plataforma-lia/src/components/chat/message-bubble.tsx` |
| 🟡 | `4f36afab2` | 2026-04-09 | Frontend (UI) | Replace all instances of the sparkles icon with the brain icon — Replaces the 'Sparkles' icon component with the 'Brain' icon component across multiple files in the  | `plataforma-lia/src/components/ai/agent-explainability-panel.tsx`<br>`plataforma-lia/src/components/chat/detected-fields-card.tsx`<br>`plataforma-lia/src/components/chat/parecer-lia-card.tsx` |
| 🔴 | `e27f8342e` | 2026-04-08 | Cross Back↔Front | Add filtering and sorting to candidate list and fix total count — Update backend API to support seniority, sort by, and sort order filters for candidates. Modify endp | `lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/domains/candidates/repositories/candidate_repository.py`<br>`plataforma-lia/src/app/api/auth/session/refresh/route.ts` |
| 🟡 | `b84beae5a` | 2026-04-08 | Frontend (UI) | Update middleware to bypass redirects for authentication — Rewrite the middleware to directly fetch authentication tokens and inject them into request headers, | `plataforma-lia/src/components/chat/multimodal-upload.tsx`<br>`plataforma-lia/src/components/chat/voice-chat-button.tsx`<br>`plataforma-lia/src/components/modals/job-status/useJobStatusModal.ts` |
| 🟢 | `bb0f280e0` | 2026-04-07 | Frontend (UI) | task(55): Reduzir fontes do chat LIA (placeholder e mensagens) — ## Original Task | `plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx` |
| 🟡 | `052f3c4c2` | 2026-04-06 | Frontend (UI) | Merged changes from nng5i7ac/main — Replit-Task-Id: 962f54f9-66bc-4345-bd00-4674bed92299 | `plataforma-lia/src/components/lia-float/LiaSplitPanel.tsx`<br>`plataforma-lia/src/components/lia-float/LiaSuperPrompt.tsx`<br>`plataforma-lia/src/components/lia-float/useLiaChatPanelState.ts` |
| 🟢 | `5c8be64c7` | 2026-04-05 | Frontend (UI) | Improve chat functionality by ensuring secure connections and fixing message errors — Fixes WebSocket authentication and improves error handling for SSE streams in the chat component. | `plataforma-lia/src/components/pages/chat-page/chat-core/useChatSession.ts`<br>`plataforma-lia/src/components/pages/chat-page/useChatPageHandlers.tsx` |
| 🟢 | `9da87e7d6` | 2026-04-05 | Frontend (UI) | Fix chat interface issues including message highlighting and input positioning — Corrected duplicated CSS class, initialized currentMessageIndex to -1 to fix default message highlig | `plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/pages/chat-page/chat-core/useChatMessages.ts` |
| 🟢 | `7ad70055f` | 2026-04-03 | Frontend (UI) | Task start baseline checkpoint for code review | `plataforma-lia/src/components/chat/plan-progress-card.tsx` |
| 🟡 | `b9d9a070d` | 2026-04-03 | Frontend (UI) | Fix issues with loading, image display, and search cancellation — Addresses an infinite loading bug by removing a root-level loading component, adds a missing search  | `plataforma-lia/src/app/loading.tsx`<br>`plataforma-lia/src/app/page.tsx`<br>`plataforma-lia/src/app/tasks/page.tsx` |
| 🟢 | `8cc0a8ca0` | 2026-03-29 | Frontend (UI) | Adjust font sizes and remove unused CSS for improved readability — Update text sizes in AgentMemoryIndicator component and remove deprecated typography CSS classes fro | `plataforma-lia/src/app/globals.css`<br>`plataforma-lia/src/components/chat/agent-memory-indicator.tsx` |

### DevOps / Deploy (Docker/GCP)

**Descrição:** Docker, docker-compose, entrypoint, GCP deploy. Configuração de infraestrutura.

**⚠️ Dependências para cherry-pick:** Configurar secrets antes do deploy | rebuild da imagem

**Arquivos canônicos:** Dockerfile, docker-compose.yml, lia-agent-system/docker-entrypoint.sh, .github/workflows/**

**Docs de referência:** —

- **Commits:** 13  |  **Período:** 2026-03-19 → 2026-04-12  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×5 🟢×4 🔴×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `ba2f483bc` | 2026-04-12 | Backend | fix: production Dockerfile and uvicorn command for GCP deploy | `lia-agent-system/Dockerfile` |
| 🟢 | `74a271623` | 2026-04-12 | Frontend (api/util) | fix: update plataforma-lia Dockerfile for GCP deploy | `plataforma-lia/Dockerfile` |
| 🟡 | `cb0af1f76` | 2026-04-12 | Backend | feat: add docker-compose.yml and docker-entrypoint.sh for GCP deploy | `lia-agent-system/docker-entrypoint.sh` |
| 🟢 | `11f66809b` | 2026-04-10 | Docs | Update infrastructure checklist and worker health check — Update GCP Infrastructure Checklist for enabled APIs and modify worker health check to use authentic | `GCP_INFRASTRUCTURE_CHECKLIST.md` |
| 🟡 | `93c9df0e9` | 2026-04-10 | Backend | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — CI/CD workflows for both repositories + infrastructure docs: | `lia-agent-system/.dockerignore` |
| 🔴 | `f86387396` | 2026-04-10 | Cross Back↔Front | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — CI/CD workflows for both repositories + infrastructure docs: | `lia-agent-system/.github/workflows/deploy.yml`<br>`lia-agent-system/Dockerfile.worker`<br>`lia-agent-system/scripts/worker_health.py` |
| 🟡 | `386c67465` | 2026-04-10 | Backend | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — Created deployment workflows and infrastructure documentation: | `lia-agent-system/.github/workflows/deploy.yml` |
| 🔴 | `e1bd7d78e` | 2026-04-10 | Cross Back↔Front | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — Created deployment workflows and infrastructure documentation: | `lia-agent-system/.github/workflows/deploy.yml`<br>`plataforma-lia/.github/workflows/deploy.yml` |
| 🔴 | `dde1d6f0d` | 2026-04-10 | Cross Back↔Front | Task #114: GitHub CI/CD — Repositórios, Actions e Docker — Created deployment workflows and infrastructure documentation: | `plataforma-lia/src/components/candidate-preview/PipelineDecisionBar.tsx` |
| 🔴 | `49d6b02a1` | 2026-04-07 | Cross IA↔Front | Update application configuration and Dockerfile for standalone deployment — Refactors several Python files to use repository patterns, updates Next.js configuration for standal | `lia-agent-system/app/api/v1/benefits.py`<br>`lia-agent-system/app/api/v1/calendar.py`<br>`lia-agent-system/app/api/v1/data_request.py` |
| 🟢 | `80e190bcd` | 2026-04-07 | Frontend (api/util) | Update proxy to connect to the correct backend server — Corrected the hardcoded backend port in the Next.js proxy configuration from 8000 to 8001 in `plataf | `plataforma-lia/next.config.js` |
| 🟢 | `a84040218` | 2026-04-01 | Frontend (api/util) | Add UI avatars to image hosting configuration — Update next.config.js to include ui-avatars.com in allowed image domains and remote patterns. | `plataforma-lia/next.config.js` |
| 🟡 | `d7dd8100c` | 2026-03-19 | Infra/Config | Add Replit connectors SDK to manage GitHub integrations — Add @replit/connectors-sdk as a dependency in package.json to enable GitHub integration management. | `package-lock.json`<br>`package.json` |

### Policy / Job Creation

**Descrição:** PolicyGateService + ConfidencePolicyService wired into JobCreationGraph. Policy domain isolation sensor + canonical comment. Hardening de jd-import upload-file.

**⚠️ Dependências para cherry-pick:** PolicyGateService no JobCreationGraph | sensor de isolation ativo | jd-import com guards

**Arquivos canônicos:** lia-agent-system/app/domains/policy/*, app/services/job_creation_graph.py

**Docs de referência:** BRANCH_MAP §4 PR-Q4

- **Commits:** 13  |  **Período:** 2026-03-19 → 2026-04-26  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×10 🟢×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `ea8418688` | 2026-04-26 | Cross IA↔Back | Wire PolicyGateService + ConfidencePolicyService into JobCreationGraph — Resolves N-09 (PolicyGateService unused in wizard) and M-06 (silent vs. | `lia-agent-system/app/domains/job_creation/policy_gate.py` |
| 🟢 | `8c3c2eb71` | 2026-04-19 | Docs | Update audit documentation to reflect new hiring policy actions — Modify `chat_capabilities_audit.json` to include `configure_candidate_portal` action under `hiring_p | `lia-agent-system/docs/chat_capabilities_audit.json` |
| 🟡 | `105b1e6f4` | 2026-04-18 | Backend | Task #476: Generalised structural test for the ID Boundary Policy — Original task | `lia-agent-system/app/api/v1/attachments.py`<br>`lia-agent-system/app/api/v1/communications.py`<br>`lia-agent-system/app/api/v1/cultural_fit.py` |
| 🟢 | `7dd82c72b` | 2026-04-18 | Docs | docs: add ID Boundary Policy for LIA × Rails — Task #471 — Document the LIA × Rails ID rules in one place so new endpoints, | `docs/INDEX.md`<br>`docs/adr/003-id-strategy-lia-vs-rails.md`<br>`docs/architecture/id-boundary-policy.md` |
| 🟡 | `0a6a412c8` | 2026-04-17 | Cross IA↔Back | Task #337: Forward actor_user_id to policy audit log — The policy chat orchestrator did not forward the logged-in user's id | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py` |
| 🟡 | `1a3acb7fb` | 2026-04-13 | Backend | fix(B-1): create missing app/services/ott_service.py — unblocks JobCreationDomain — JobCreationAPIClient:18 imports get_ott_service() which did not exist. | `lia-agent-system/app/services/ott_service.py` |
| 🟡 | `75ac7a8f1` | 2026-04-11 | Backend | Task #153: Per-request cost + RAG recursive default + policy doc type — 1. LLMCascade: Wire request_id through all route() paths with auto-generation. | `lia-agent-system/app/shared/intelligence/chunking/base.py`<br>`lia-agent-system/app/shared/intelligence/chunking/factory.py`<br>`lia-agent-system/app/shared/intelligence/chunking/section_aware.py` |
| 🟡 | `81c352abb` | 2026-04-07 | Backend | Fix error in backend policy engine rule loading — Corrected a NameError in `main.py` by changing dictionary key access from variables to strings to pr | `lia-agent-system/app/main.py` |
| 🟡 | `84452a74d` | 2026-04-06 | Backend | fix(phase2): remove stray AsyncSession/get_db from policy_engine.py apply_sector_defaults | `lia-agent-system/app/api/v1/policy_engine.py` |
| 🟡 | `ede167a88` | 2026-04-06 | Backend | chore(guards): remove policy_engine from PENDING_MIGRATION (now 169) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `2b1bd7d81` | 2026-03-31 | Backend | fix(task70): structured failure_type for policy-blocked feedback — - mark_as_failed sets failure_type='policy_blocked' for FairnessGuard | `lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py` |
| 🟢 | `2e07c287d` | 2026-03-23 | Docs | fix(skills): corrigir shadow policy, checklist backend e breakpoints — - design-standardize: shadow policy mais precisa | `.agents/skills/design-standardize/SKILL.md`<br>`.agents/skills/feature-audit/SKILL.md` |
| 🟡 | `0f71a4bc8` | 2026-03-19 | Cross IA↔Back | Z5-03 + Z5-02: threshold semântico configurável e consolidação PolicySetupAgent — Z5-03 — Threshold semântico: | `lia-agent-system/app/agents/policy_setup_agent.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/vector_semantic_cache.py` |

### Task #57

- **Commits:** 13  |  **Período:** 2026-03-29 → 2026-04-07  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×8 🟡×4 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `bcf2fadb9` | 2026-04-07 | Frontend (UI) | feat: Remove balloon/background from LIA messages (Task #57) — ## Summary | `plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/chat/chat-bubble-base.tsx` |
| 🟢 | `dc2a58a68` | 2026-03-29 | Frontend (UI) | Task #57: Fix code review rejections - remove unsafe `any` and clean up split artifacts — - Removed all `as any` casts in candidato/[id]/page.tsx (34 candidate field casts + 3 inline casts) | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx` |
| 🟢 | `4837d6c8a` | 2026-03-29 | Frontend (UI) | Task #57: Fix code review rejections - remove unsafe `any` and clean up split artifacts — - Removed all `as any` casts in candidato/[id]/page.tsx (34 candidate field casts + 3 inline casts) | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx` |
| 🟢 | `9deb437bc` | 2026-03-29 | Frontend (UI) | Task #57: Fix split wiring, remove unsafe any, resolve merge conflicts — - Fixed SCMSectionContent missing imports and props destructuring | `plataforma-lia/src/components/expandable-ai-prompt/EAPTabContent.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/useExpandableAIPromptCore.tsx` |
| 🟡 | `e98512e2a` | 2026-03-29 | Frontend (UI) | Task #57: Fix SCMSectionContent split wiring + type cleanup — - Fixed SCMSectionContent missing imports: toast, MessageSquare, Globe, | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatEffects.tsx` |
| 🟢 | `eed3f3972` | 2026-03-29 | Frontend (UI) | Task #57: Split ALL monolithic files <1500L + fix type contracts — Monolith splits completed: | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx` |
| 🟢 | `1aff17772` | 2026-03-29 | Frontend (UI) | Task #57: Split ALL monolithic files <1500L + fix type contracts — Monolith splits completed: | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx` |
| 🟢 | `beaf84528` | 2026-03-29 | Frontend (UI) | Task #57: Split ALL monolithic files to <1500L, fix canSubmit runtime error — Completed monolith split of all target files: | `plataforma-lia/src/components/search/hooks/useSmartSearchCore.tsx` |
| 🟡 | `b4c6a5476` | 2026-03-29 | Frontend (UI) | Task #57: Split useExpandedChatModalCore.tsx from 4033L to <1500L — Completed monolith split of all target files: | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/useEAPCallbacks.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/useEAPEffects.tsx` |
| 🟢 | `da339b228` | 2026-03-29 | Frontend (UI) | Task #57: Complete monolith split + any elimination + inline styles — Build fixes: | `plataforma-lia/src/components/candidate-page.tsx`<br>`plataforma-lia/src/components/candidate-preview.tsx`<br>`plataforma-lia/src/components/expanded-chat-modal.tsx` |
| 🟡 | `dcb34aec2` | 2026-03-29 | Frontend (UI) | Task #57: Complete monolith split + inline style conversion — Build fixes: | `plataforma-lia/src/components/candidate-page.tsx`<br>`plataforma-lia/src/components/candidate-page/CandidatePageActivitiesTab.tsx`<br>`plataforma-lia/src/components/candidate-page/CandidatePageProfileTab.tsx` |
| 🟡 | `f63f7b988` | 2026-03-29 | Frontend (UI) | Task #57 T009: Fix build errors from monolith split — - advancedFiltersTypes.tsx: Add missing `export` to all constants | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx` |
| 🔴 | `8cbf52ed5` | 2026-03-29 | Frontend (UI) | Task #57: Fix syntax errors in split monolithic files — - Removed undefined 'prompt' variable from useSmartSearchCore.tsx | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx`<br>`plataforma-lia/src/components/candidate-page.tsx` |

### scope: arch

- **Commits:** 13  |  **Período:** 2026-03-31 → 2026-04-01  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×7 🟢×6

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `db8a19604` | 2026-04-01 | Frontend (UI) | refactor(arch): preventive splits for borderline files (990-997L) | `plataforma-lia/src/components/candidate-preview/CandidateFilesTab.tsx`<br>`plataforma-lia/src/components/candidate-preview/useCandidateFiles.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useCompanyConfigLoader.tsx` |
| 🟢 | `a552d5660` | 2026-04-01 | Frontend (UI) | refactor(arch): split useCandidatesPageCore into domain hooks | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesInteractions.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesNavigation.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesPageCore.tsx` |
| 🟡 | `e6c0ce72d` | 2026-04-01 | Frontend (UI) | refactor(arch): reduce useEAPCallbacks and useExpandedChatModalCore below 1000L | `plataforma-lia/src/components/expandable-ai-prompt/useEAPCallbacks.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/useEAPCallbacksTypes.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useAnalyticsSession.ts` |
| 🟢 | `a849e3b8b` | 2026-04-01 | Frontend (UI) | refactor(arch): reduce modern-conversations and CandidatesFilterPanel below 1000L | `plataforma-lia/src/components/pages/candidates/CandidatesFilterPanel.tsx`<br>`plataforma-lia/src/components/pages/candidates/types.ts`<br>`plataforma-lia/src/components/pages/chat-page/constants/modern-conversations-part2.ts` |
| 🟢 | `88e3ddbfc` | 2026-04-01 | Frontend (UI) | refactor(arch): extract sub-hooks from useExpandedChatModalCore and useEAPCallbacks | `plataforma-lia/src/components/expandable-ai-prompt/useArchetypeHandlers.ts`<br>`plataforma-lia/src/components/expandable-ai-prompt/useEAPCallbacks.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatModalCore.tsx` |
| 🟢 | `5bfff47b2` | 2026-04-01 | Frontend (UI) | refactor(arch): extract sub-hooks from useSendMessageHandlers and useExpandedChatModalCore | `plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatModalCore.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useMessageConfirmationHandlers.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useSendMessageHandlers.ts` |
| 🟢 | `38c7cd2bb` | 2026-04-01 | Frontend (UI) | refactor(arch): decompose admin pages, job-status-modal steps, lia-screening-guide | `plataforma-lia/src/components/jobs/JobEditTab.tsx`<br>`plataforma-lia/src/components/lia-screening-guide.tsx`<br>`plataforma-lia/src/components/modals/job-status-modal.tsx` |
| 🟡 | `60ad6e82d` | 2026-04-01 | Frontend (UI) | refactor(arch): split chat-page constants, goals-management, CompanyDataSection, JobEditTab | `plataforma-lia/src/components/jobs/JobEditTab.tsx`<br>`plataforma-lia/src/components/jobs/job-edit-tab/StatusChangeConfirmModal.tsx`<br>`plataforma-lia/src/components/jobs/job-edit-tab/index.ts` |
| 🟡 | `669494b28` | 2026-04-01 | Frontend (UI) | refactor(arch): reduce borderline large files below 1000L (JDEvaluationPanel, GoalsPlanningHub, CandidatesPageModals, usePromptState, useCandidatesLIAHandlers) | `plataforma-lia/src/components/GoalsPlanningHub.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.types.ts` |
| 🟡 | `a2447576a` | 2026-04-01 | Frontend (UI) | refactor(arch): extract sub-components from JDEvaluationPanel and tasks-page — - JDEvaluationPanel (1305L -> 1004L): extract JDEvaluationHeader (266L), | `plataforma-lia/src/components/pages/tasks-page.tsx`<br>`plataforma-lia/src/components/pages/tasks/ActiveAlertsCard.tsx`<br>`plataforma-lia/src/components/pages/tasks/TaskCard.tsx` |
| 🟡 | `b3d3b14f4` | 2026-04-01 | Frontend (UI) | refactor(arch): extract sub-components from JobEditTab, expandable-ai-prompt, BenefitsTab (2nd pass) | `plataforma-lia/src/components/expandable-ai-prompt.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/EAPModals.tsx`<br>`plataforma-lia/src/components/jobs/JobEditTab.tsx` |
| 🟢 | `326804725` | 2026-03-31 | Frontend (UI) | refactor(arch): decompose CandidateSearchResultsView and candidate-page into focused components | `plataforma-lia/src/components/candidate-page/CandidatePageFilesTab.tsx` |
| 🟡 | `46f637841` | 2026-03-31 | Frontend (UI) | refactor(arch): extract sub-components from BenefitsTab, DepartmentsTab, job-status-modal | `plataforma-lia/src/components/modals/job-status-modal.tsx`<br>`plataforma-lia/src/components/modals/job-status/job-status-utils.ts`<br>`plataforma-lia/src/components/settings/ApproverSection.tsx` |

### §18 Senioridade + Job Migration

**Descrição:** Migração job.level → seniority (write-both + leitura unificada). Remove legacy level. Show 'Senioridade não informada' em vez de chutar 'Pleno'. E2E coverage de edição. Padronizar e enriquecer card do Kanban de Vagas.

**⚠️ Dependências para cherry-pick:** Backend write-both (level + seniority) | FE leitura unificada | Card Kanban com seniority badge

**Arquivos canônicos:** lia-agent-system/app/models/job.py, plataforma-lia/src/types/job.ts, src/components/pages/jobs/*, src/components/pages/job-kanban/*

**Docs de referência:** Task #531/#539/#559/#560/#562

- **Commits:** 13  |  **Período:** 2026-03-24 → 2026-04-19  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×7 🟡×4 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `39e61c38f` | 2026-04-19 | Testes | test(jobs): cobertura ponta-a-ponta de edição de senioridade (Task #560) — Adiciona um teste de fluxo que exercita toda a cadeia de senioridade | `plataforma-lia/src/components/pages/jobs/__tests__/seniority-edit-flow.test.tsx` |
| 🟡 | `9f6371873` | 2026-04-19 | Frontend (UI) | Task #559 — Show "Senioridade não informada" instead of guessing "Pleno" — Problem: when the backend returned a job vacancy without `seniority_level` | `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`<br>`plataforma-lia/src/components/jobs/jobsPageTypes.ts`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsData.ts` |
| 🟡 | `dfda1e1a4` | 2026-04-19 | Frontend (UI) | Task #539 — Remove legacy `level` field from Job type — After the observation window from Task #531 (write-both seniority+level), | `plataforma-lia/src/app/api/backend-proxy/pipeline-overview/route.ts`<br>`plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`<br>`plataforma-lia/src/components/jobs/jobsPageTypes.ts` |
| 🟢 | `d0308bdd7` | 2026-04-19 | Frontend (UI) | Task #531 — Migração `job.level` → `seniority` (write-both + leitura unificada) — ## What | `plataforma-lia/src/components/screening-config/SCMSectionContent.tsx`<br>`plataforma-lia/src/components/screening-config/hooks/useScreeningConfigManagerCore.tsx` |
| 🔴 | `7de66b24a` | 2026-04-19 | Cross Back↔Front | Task #531 — Migração `job.level` → `seniority` (write-both + leitura unificada) — ## What | `plataforma-lia/src/app/api/backend-proxy/pipeline-overview/route.ts`<br>`plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx`<br>`plataforma-lia/src/components/screening-config/SCMSectionContent.tsx` |
| 🟡 | `9cca4e782` | 2026-04-19 | IA | fix(quality): move regex constants and ActionResult/_fetch_market_range to module level — - executor.py: _UUID_RE/_JOB_ID_RE defined at module level (not inside execute() on every call) | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_handlers/job_actions.py` |
| 🔴 | `75334b40f` | 2026-04-18 | Cross IA↔Front | Add caching for job extraction and update job seniority fields — Implement an in-memory cache for Layer 2 extraction to improve performance and reduce redundant LLM  | `lia-agent-system/app/domains/cv_screening/services/wsi_service/layer2_extractor.py`<br>`plataforma-lia/src/components/jobs/jobsPageTypes.ts`<br>`plataforma-lia/src/components/screening-config/SCMSectionContent.tsx` |
| 🟢 | `3ec61f4f6` | 2026-04-18 | Frontend (UI) | Clarify seniority and level precedence for job postings — Add inline comments to `SCMSectionContent.tsx` explaining the explicit precedence of 'seniority' ove | `plataforma-lia/src/components/screening-config/SCMSectionContent.tsx` |
| 🟢 | `6e6dc705f` | 2026-04-17 | Docs | docs(audits): apply F5 inheritance rule to top-level ReActAgent rows in scorecard (task #371) — Original task: extend the F5 inheritance-pass policy (defined in task #352 | `docs/audits/AUDIT_STATUS_REPORT_2026-04-FINAL.md` |
| 🟡 | `ca32d1ae3` | 2026-04-16 | Backend | Expand forbidden import checker to scan root-level patch scripts (Task #223) — Changes to lia-agent-system/scripts/check_forbidden_imports.py: | `lia-agent-system/scripts/check_forbidden_imports.py` |
| 🟢 | `f37c4994e` | 2026-04-06 | Frontend (UI) | Add market percentile to job report quality metrics and hide empty seniority section — Expose `marketPercentile` from salary data in `JobReportModal`'s quality metrics and conditionally r | `plataforma-lia/src/components/job-report-modal.tsx`<br>`plataforma-lia/src/components/pages/work-model-analytics-page.tsx` |
| 🟢 | `5f6517039` | 2026-04-05 | Frontend (UI) | Update action executor and resolve seniority logic — Refactor tests for action executor and action handlers, update seniority resolver parameters, and im | `plataforma-lia/src/components/top-bar.tsx`<br>`plataforma-lia/src/contexts/auth-context.tsx` |
| 🟢 | `e066566a9` | 2026-03-24 | Docs | Update scoring methodology to adapt question distribution by seniority — Refine WSI calculation methodology by updating section 5.1 and 5.2 of docs/WSI_METHODOLOGY_COMPLETE_ | `docs/WSI_METHODOLOGY_COMPLETE_v2.md` |

### Bridge React→Vue

**Descrição:** Inventário completo de portabilidade React→Vue — 131 hooks classificados em 3 tiers (Skill 6).

**⚠️ Dependências para cherry-pick:** Decisão de portabilidade pendente | Roadmap migração Vue não confirmado

**Arquivos canônicos:** plataforma-lia/docs/specs/frontend/REACT_VUE_BRIDGE.md

**Docs de referência:** REACT_VUE_BRIDGE.md

- **Commits:** 12  |  **Período:** 2026-03-28 → 2026-04-21  |  **Camadas:** Backend + Frontend + Rails  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×6 🟡×6

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `c473ee71a` | 2026-04-21 | Frontend (UI) | feat(task-712): close 3 final findings — useOnboardingFlow + UI->chat bridge — 1) useOnboardingFlow agora le setup_progress real | `plataforma-lia/src/components/onboarding/useOnboardingFlow.ts`<br>`plataforma-lia/src/components/settings/SettingsSyncBroadcaster.tsx` |
| 🟡 | `df9c8847f` | 2026-04-13 | Rails (ats-api) | feat(rails): Phase 5 — Rails Bridge handlers for Agent Studio events — Mirror commit on Rails side (ats-api-copia subfolder). | `ats-api-copia/app/services/lia_events/event_registry.rb`<br>`ats-api-copia/app/workers/lia_events_worker.rb` |
| 🟡 | `40b868ac7` | 2026-04-13 | Backend | feat(studio): Phase 5 — Rails Bridge for Agent Studio events (Python side) — Python side: webhook_dispatcher now publishes to Rails RabbitMQ in | `lia-agent-system/app/services/webhook_dispatcher.py` |
| 🟡 | `a17d35ffd` | 2026-04-09 | Frontend (UI) | feat(unified-chat): Phase 6 — Deprecate old chats, add InlineChatBridge — - Created InlineChatBridge component (opens sidebar with context) | `plataforma-lia/src/components/candidate-preview/LiaChatModal.tsx`<br>`plataforma-lia/src/components/lia-float/LiaChatButton.tsx`<br>`plataforma-lia/src/components/lia-float/LiaChatPanel.tsx` |
| 🟢 | `1dbc3592a` | 2026-04-01 | Frontend (UI) | feat(bridge): document TSX hooks refactor list + convert 4 false-positive hooks to .ts — - Rename 4 hooks from .tsx to .ts (no real JSX, only React type annotations): | `plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatSubHooks.ts`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsPageCore.ts` |
| 🟢 | `c5b2a396f` | 2026-04-01 | Frontend (UI) | feat(bridge): convert hooks .tsx->ts + add context-store map to vue-bridge | `plataforma-lia/src/components/expanded-chat/hooks/useCompanyConfigLoader.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatEffects.ts` |
| 🟢 | `4b1d2816c` | 2026-03-31 | Frontend (UI) | fix(bridge): replace hardcoded hex with LIA design tokens in task-helpers, tasks-page, search-preview, dashboard | `plataforma-lia/src/components/dashboard/strategic-dashboard.tsx`<br>`plataforma-lia/src/components/pages/task-helpers.tsx`<br>`plataforma-lia/src/components/pages/tasks-page.tsx` |
| 🟡 | `9740ee2ed` | 2026-03-31 | Backend | docs: frontend-audit-v5 — 14 dimensoes (inclui Bridge Architecture + Monochromatic DS) | `lia-agent-system/app/api/v1/rag_search.py`<br>`lia-agent-system/app/domains/communication/services/email_service.py`<br>`lia-agent-system/app/domains/sourcing/services/llm_job_classification_service.py` |
| 🟡 | `012b826cc` | 2026-03-31 | Frontend (UI) | feat: Vue migration prep — React.memo+displayName, vue-bridge.ts, hook purity audit — - Add React.memo + displayName to 7 pure UI components: | `plataforma-lia/src/components/bulk-actions-bar.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanCard.tsx`<br>`plataforma-lia/src/components/ui/data-request-indicator.tsx` |
| 🟢 | `f84aea2ab` | 2026-03-30 | Docs | bridge: inventário completo de portabilidade React→Vue — 131 hooks classificados em 3 tiers — Skill 6 | `plataforma-lia/docs/specs/frontend/REACT_VUE_BRIDGE.md` |
| 🟢 | `70d56b82b` | 2026-03-28 | Frontend (UI) | Bridge Vue — fixes residuais: imports type-only + chatScrollRef externalizado — useCandidatesSearch: import React → import type React (sem valor runtime) | `plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx`<br>`plataforma-lia/src/components/pages/candidates/LIASearchSidebar.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesCVHandlers.ts` |
| 🟡 | `cb109cdc1` | 2026-03-28 | Frontend (UI) | Auditoria DS + Bridge Vue + Code Review — Sprints 4.6-4.8 — DS v4.2.1 (5 correções): | `plataforma-lia/src/components/expanded-chat/components/ExpandedChatInput.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesActions.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesCVHandlers.ts` |

### scope: ts

- **Commits:** 12  |  **Período:** 2026-03-31 → 2026-04-01  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×8 🟡×2 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `3b368d583` | 2026-04-01 | Frontend (UI) | fix(ts): @ts-nocheck on useExpandedChatModalCore — type mismatch from extracted useConversationMemoryInit | `plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatModalCore.tsx` |
| 🟢 | `3762d311c` | 2026-04-01 | Frontend (UI) | fix(ts): restore CandidatesFilterPanel.tsx truncated by dedup agent — 0 TS errors | `plataforma-lia/src/components/pages/candidates/CandidatesFilterPanel.tsx` |
| 🟡 | `db9dfae7b` | 2026-04-01 | Frontend (UI) | fix(ts): repair agent-introduced errors — duplicate imports, missing AlertCircle, broken return values, empty className | `plataforma-lia/src/components/candidate-preview/CandidateOpinionsTab.tsx`<br>`plataforma-lia/src/components/candidate-preview/activities/ActivityExpandedDetails.tsx`<br>`plataforma-lia/src/components/jobs/JobEditTab.tsx` |
| 🟢 | `350fab898` | 2026-03-31 | Frontend (api/util) | fix(ts): exclude out/ from tsconfig — Next.js 15 async params type issue in generated validator | `plataforma-lia/tsconfig.json` |
| 🔴 | `59eea4b6a` | 2026-03-31 | Cross Back↔Front | fix(ts): @ts-nocheck sweep — all remaining 239 error files | `lia-agent-system/app/api/v1/rubric_evaluation.py`<br>`lia-agent-system/app/domains/automation/services/proactive_service.py`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/lgpd/page.tsx` |
| 🟢 | `898bc9c3f` | 2026-03-31 | Frontend (UI) | fix(ts): 0 errors — ts-nocheck validator.ts, merge duplicate tailwind boxShadow | `plataforma-lia/src/components/pages/chat-page/useChatPageCore.tsx` |
| 🔴 | `9458ab019` | 2026-03-31 | Frontend (UI) | fix(ts): @ts-nocheck all 233 remaining error files — achieving <50 TS errors | `plataforma-lia/src/app/admin/clientes/[clientId]/comunicacoes/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/controles/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/incidentes/page.tsx` |
| 🟢 | `dd5e115d3` | 2026-03-31 | Frontend (UI) | fix(ts): reduce errors in JobEditTab.tsx and useJobEditTab.ts | `plataforma-lia/src/components/jobs/JobEditTab.tsx` |
| 🟢 | `d5011f2b7` | 2026-03-31 | Frontend (UI) | fix(ts): 0 errors — fix useJobEditTab invalid property access syntax | `plataforma-lia/src/components/jobs/job-edit-tab/useJobEditTab.ts` |
| 🟡 | `0c7f86eb4` | 2026-03-31 | Frontend (UI) | fix(ts): @ts-nocheck all remaining error files — targeting 0 TS errors | `plataforma-lia/src/components/candidate-preview/CandidatePreviewProfileTab.tsx`<br>`plataforma-lia/src/components/email-templates/report-email-templates.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useWSIAndCalibrationHandlers.ts` |
| 🟢 | `5cc1e4030` | 2026-03-31 | Frontend (UI) | fix(ts): reduce errors in lia-metrics-dashboard.tsx | `plataforma-lia/src/components/lia-metrics-dashboard.tsx` |
| 🟢 | `a7a27fed8` | 2026-03-31 | Frontend (UI) | fix(ts): reduce errors in report-email-templates.tsx | `plataforma-lia/src/components/email-templates/report-email-templates.tsx` |

### Acessibilidade (a11y)

**Descrição:** Acessibilidade: motion-reduce em spinners, skip-to-content, alt text em imgs, role=alert nos banners HITL, aria-invalid em campos com erro.

**⚠️ Dependências para cherry-pick:** WCAG 2.1 AA (Guard 8) | Sentry server/edge configurado

**Arquivos canônicos:** plataforma-lia/src/app/*, src/components/* (transversal)

**Docs de referência:** OBS-27, OBS-08, OBS-10

- **Commits:** 11  |  **Período:** 2026-03-18 → 2026-04-17  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×5 🟡×5 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `7db2a5c0c` | 2026-04-17 | Frontend (UI) | Add keyboard accessibility to the chat header drag handle — Update UnifiedChatHeader.tsx to include tabIndex, role, and aria-label for keyboard accessibility wh | `plataforma-lia/src/components/unified-chat/UnifiedChatHeader.tsx` |
| 🟢 | `712cb9be0` | 2026-04-04 | Frontend (api/util) | Improve modal accessibility by enforcing focus within the dialog — Refactor the `useModalA11y` hook to implement strict containment, ensuring focus remains within the  | `plataforma-lia/src/hooks/use-modal-a11y.ts` |
| 🟡 | `34008bf0e` | 2026-04-04 | Frontend (UI) | Task #118: Acessibilidade — Labels, ARIA, Focus Management, Dialog Semantics — Comprehensive accessibility improvements across 14+ files: | `plataforma-lia/src/components/candidate-modal.tsx`<br>`plataforma-lia/src/components/candidate-preview/FilePreviewModal.tsx`<br>`plataforma-lia/src/components/candidate-preview/LiaChatModal.tsx` |
| 🟢 | `c3a73cd6f` | 2026-04-04 | Frontend (UI) | Task #118: Acessibilidade — Labels, ARIA, Focus Management e Dialog Semantics — Comprehensive accessibility improvements across 14 files: | `plataforma-lia/src/components/settings/CompanyDataCard.tsx`<br>`plataforma-lia/src/components/settings/CompanyDataSection.tsx` |
| 🟡 | `16485ec76` | 2026-04-04 | Frontend (UI) | Task #118: Acessibilidade — Labels, ARIA, Focus Management e Dialog Semantics — Changes across 12 files: | `plataforma-lia/src/components/candidate-modal.tsx`<br>`plataforma-lia/src/components/candidate-preview/FilePreviewModal.tsx`<br>`plataforma-lia/src/components/candidate-preview/LiaChatModal.tsx` |
| 🟡 | `2f3f45e0c` | 2026-04-04 | Frontend (UI) | Task #118: Acessibilidade — Labels, ARIA e Focus Management — Changes: | `plataforma-lia/src/app/login/LoginClient.tsx`<br>`plataforma-lia/src/components/modals/unified-communication-modal.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesFilterPanel.tsx` |
| 🟢 | `2902809cb` | 2026-04-03 | Frontend (UI) | Task #110: Design System + Accessibility + Dead Code cleanup — Changes: | `plataforma-lia/src/components/candidate-preview.tsx` |
| 🔴 | `72875a661` | 2026-04-03 | Cross Back↔Front | Task #110: Design System v4.2.1 + Accessibility + Dead Code cleanup — Changes: | `lia-agent-system/app/api/v1/cv_parser.py`<br>`plataforma-lia/src/app/portal/data-request/[token]/PortalFieldRenderer.tsx`<br>`plataforma-lia/src/components/candidate-preview.tsx` |
| 🟢 | `bbccd9f2e` | 2026-04-02 | Frontend (UI) | Update job listing details and improve accessibility of job titles — Update the product design inventory to reflect accurate counts for various components, including UI  | `plataforma-lia/src/components/pages/jobs/JobsCompactTableView.tsx` |
| 🟡 | `cd6fe7cec` | 2026-03-30 | Frontend (UI) | a11y+obs: motion-reduce nos spinners + skip-to-content + alt em imgs + Sentry server/edge — OBS-27 OBS-08 OBS-10 | `plataforma-lia/src/app/admin/layout.tsx`<br>`plataforma-lia/src/app/admin/setup-empresa/components/BenefitsContent.tsx`<br>`plataforma-lia/src/app/admin/setup-empresa/page.tsx` |
| 🟡 | `135abcb4d` | 2026-03-18 | Outro | Improve automated accessibility checks for improved user experience — Update the automated accessibility audit to enhance its checks and ensure broader compliance. | `qa-a11y-audit.ts` |

### Task #33

- **Commits:** 11  |  **Período:** 2026-03-22 → 2026-04-06  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×11

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `19c0894cb` | 2026-04-06 | Frontend (UI) | Task #33: Equalizar espaçamento do input no chat da LIA — Changed the margin-bottom of the suggestion cards container in the chat | `plataforma-lia/src/components/pages/chat-page.tsx` |
| 🟢 | `07bb528b0` | 2026-03-22 | Docs | docs: Task #33 — seção 23.9+23.10 com 1653 linhas, 23 blocos de integração exata, zero código inventado — Correções dos 3 blockers apontados pelo code review: | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `2870155c9` | 2026-03-22 | Docs | docs: Task #33 — corrige dois blockers do code review — Blocker 1: Código inventado ("padrão de integração proposto") | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `d428c42a6` | 2026-03-22 | Docs | docs: Task #33 — seção 23.9 com código real v5 e caminhos exatos verificados no repositório — Dados reais lidos do repositório WeDOTalent/recruiter_agent_v5 via GitHub API: | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `4897ca3ec` | 2026-03-22 | Docs | docs: Task #33 — corrigidos inconsistências de mapeamento e caminhos exatos de arquivos v5 — Problemas corrigidos desta iteração: | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `0c07091c9` | 2026-03-22 | Docs | docs: Task #33 — seção 23.9 reescrita com 23 concerns domain-specific corretos — Problema anterior: seção tinha concerns cross-domain (C01-C23 por tipo de concern) | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `5fb0f09e2` | 2026-03-22 | Docs | docs: Task #33 — seção 23 finalizada com tabela de cobertura por domínio e correções — Documento: proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `f47838381` | 2026-03-22 | Docs | docs: Task #33 finalizada — correção de assinaturas reais de métodos LIA — Documento: proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `e1f074bfd` | 2026-03-22 | Docs | docs: Task #33 finalizada — seção 23 completa com 23 concerns + diagnóstico arquitetural — Documento: proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `ae08dda10` | 2026-03-22 | Docs | docs: Task #33 — seções 23.9 e 23.10 completas com 23 concerns detalhados e diagnóstico arquitetural — Documento: proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `a31ddaf6b` | 2026-03-22 | Docs | docs: Task #33 — adicionar seção 23.9 com análise detalhada de todos os 23 concerns — Objetivo da task: adicionar ao documento proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |

### scope: unified-chat

- **Commits:** 11  |  **Período:** 2026-04-09 → 2026-04-10  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×9 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `aba75e8c8` | 2026-04-10 | Frontend (UI) | feat(unified-chat): Phase A — @mention autocomplete + /slash commands — 5 new files: | `plataforma-lia/src/components/unified-chat/MentionDropdown.tsx`<br>`plataforma-lia/src/components/unified-chat/SlashCommandDropdown.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatInput.tsx` |
| 🟢 | `19989a377` | 2026-04-09 | Frontend (UI) | fix(unified-chat): P1 — file attachment now sends via useCvScreening — - Integrated useCvScreening hook in UnifiedChat | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟡 | `0dc2ab41e` | 2026-04-09 | Frontend (UI) | fix(unified-chat): Sprint 1 — eliminate ALL mock buttons, wire real integrations — 7 MOCK buttons now functional (M1-M7) | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatHeader.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatInput.tsx` |
| 🟢 | `e485d9b42` | 2026-04-09 | Frontend (UI) | feat(unified-chat): Phase 5 — Universal scope + Navigation hints — Backend: | `plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟢 | `10c37071e` | 2026-04-09 | Frontend (UI) | feat(unified-chat): Phase 4 — Task Context Bar integration — - SwitchTaskModal connected to UnifiedChat header (arrow button) | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatHeader.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🟢 | `aab86a1f7` | 2026-04-09 | Frontend (UI) | feat(unified-chat): Phase 3 — Split View + HITL in all modes — - DynamicContextPanel renders inside UnifiedChat (sidebar + fullscreen) | `plataforma-lia/src/components/unified-chat/ChatPageFullscreen.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟢 | `de4811f97` | 2026-04-09 | Frontend (UI) | feat(unified-chat): Phase 2 — Fullscreen mode replaces legacy ChatPage — - ChatPageFullscreen wraps UnifiedChat in fullscreen with HITL + DynamicPanel | `plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/unified-chat/ChatPageFullscreen.tsx` |
| 🟢 | `4e5b572f6` | 2026-04-09 | Frontend (UI) | fix(unified-chat): eliminate double bubble, single source of truth — - DashboardChatPanel returns null when closed (no bubble inside flex) | `plataforma-lia/src/components/unified-chat/DashboardChatPanel.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatConditional.tsx` |
| 🟢 | `c72d92a45` | 2026-04-09 | Frontend (UI) | feat(unified-chat): Phase 1 — Replit-style inline sidebar — - DashboardChatPanel renders UnifiedChat as flex child in dashboard layout | `plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/unified-chat/DashboardChatPanel.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟢 | `82d6992ed` | 2026-04-09 | Frontend (UI) | fix(unified-chat): restore hasInlineChat check and LiaSuperPrompt — - Hide UnifiedChat when ChatPage is active (hasInlineChat=true) | `plataforma-lia/src/components/unified-chat/UnifiedChatConditional.tsx` |
| 🟢 | `31f811f35` | 2026-04-09 | Frontend (UI) | fix(unified-chat): implement handleNewChat, add plus menu, persist mode, fix TS types — - handleNewChat now properly calls switchChatContext and clears messages | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatInput.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |

### Privacy / PII (W7)

**Descrição:** W7.1 PII strip antes do router LLM cascade. W7.2 PromptInjectionGuard. W7.3 LGPD consent gate em /webhook approve. PII Masking corrigida (não destrói job_id).

**⚠️ Dependências para cherry-pick:** PromptInjectionGuard SEMPRE antes do LLM | PII strip recursivo | consent gate ativo no webhook

**Arquivos canônicos:** lia-agent-system/app/shared/pii_masking.py, app/integrations/teams/prompt_injection_guard.py, app/api/v1/webhook_*.py

**Docs de referência:** DEVELOPER_HANDOFF.md PARTE C

- **Commits:** 10  |  **Período:** 2026-03-19 → 2026-04-27  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×9 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `cbc71c70e` | 2026-04-27 | IA | fix(privacy): W7.1 PII strip antes do router LLM cascade — Gap: LLMCascadeRouter._call_model() interpolava user message raw no routing | `lia-agent-system/app/orchestrator/llm_cascade.py` |
| 🔴 | `30fd75ff9` | 2026-04-26 | Cross Back↔Front | Task #838 — Privacy & audit hardening on JD upload endpoint — Reforço de privacidade e auditoria no `/import/upload-file`: | `lia-agent-system/app/api/v1/jd_import.py`<br>`plataforma-lia/src/app/api/backend-proxy/jd-import/consent-status/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/jd-import/upload/route.ts` |
| 🟡 | `cb56abc90` | 2026-04-21 | Cross IA↔Back | feat(task-712): real PII masking + structured extraction + tool metadata — Closes the 3 remaining findings from the second code review. | `lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| 🟡 | `6b4cf486b` | 2026-04-19 | Cross IA↔Back | Reforça regex de ANO_FORMATURA em pii_masking (task #549) — Achado #3 da investigação Presidio (#533): a regex `_GRADUATION_YEAR_PATTERN` | `lia-agent-system/app/shared/compliance/c3b_layer.py` |
| 🟡 | `a995eacef` | 2026-04-17 | Backend | Hotfix: imports canônicos de PII e Audit (Task #309) — Origem: auditoria docs/audits/AUDIT_STATUS_REPORT_2026-04.md | `lia-agent-system/app/api/v1/automation/_shared.py`<br>`lia-agent-system/app/domains/analytics/services/weekly_digest_service.py`<br>`lia-agent-system/app/domains/automation/services/proactive_alert_service.py` |
| 🟡 | `f8b6c1a57` | 2026-04-14 | Backend | fix: encrypt PII in Redis via Fernet [PX08-086] Wave 6 item 6.6 — - New RedisCrypto module: Fernet encryption with fail-open (no key = plaintext) | `lia-agent-system/app/domains/ai/services/response_cache_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/interview_session_store.py`<br>`lia-agent-system/app/services/toon_service.py` |
| 🟡 | `b41c542e4` | 2026-04-14 | Backend | fix: PII in logs remediation — 50 violations → 0 [PX08-062] — Sprint 9 item 9.4 — Removed PII (email, cpf, phone, full_name) from | `lia-agent-system/app/api/public/candidate_portal.py`<br>`lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/api/v1/bulk_actions.py` |
| 🟡 | `55ba81b35` | 2026-04-12 | Cross IA↔Back | feat: Item A Tipo C — audited Gemini native calls with PII strip + audit — - Add generate_native_gemini() async wrapper to LLMService | `lia-agent-system/app/api/v1/lia_assistant/wizard.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_question_adjuster.py` |
| 🟡 | `b1ed88497` | 2026-04-12 | Cross IA↔Back | feat: Item A Tipo B — audited LangChain chain calls with PII strip + audit — - Create PIIStripCallback: strips PII from messages before LLM call | `lia-agent-system/app/api/v1/company.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/analytics/services/candidate_report_service.py` |
| 🟡 | `39660c549` | 2026-03-19 | Cross IA↔Back | Z6-01 + Z6-02 + Z6-03 + Z7-01: observabilidade, PII NER e comportamento de recrutador — Z6-01 — Consolidação ATS clients: | `lia-agent-system/app/api/v1/recruiter_behavior.py`<br>`lia-agent-system/app/api/v1/traces.py`<br>`lia-agent-system/app/domains/ats_integration/services/ats_clients/__init__.py` |

### Talent Funnel (FE)

**Descrição:** Funil de Talentos — tabs, candidato page, components específicos.

**⚠️ Dependências para cherry-pick:** Endpoint /api/backend-proxy/talent-funnel | hooks de funil

**Arquivos canônicos:** plataforma-lia/src/app/funil-de-talentos/**, src/components/talent-funnel-tabs/**

**Docs de referência:** —

- **Commits:** 10  |  **Período:** 2026-03-30 → 2026-04-11  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×9 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `30551691d` | 2026-04-11 | Frontend (UI) | Improve tab loading by rendering them only when active — Conditionally render tab content within TabsContent components to ensure components and their associ | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `788baa5c7` | 2026-04-11 | Frontend (UI) | Improve ability to load candidate lists by adding automatic retries — Add retry logic with delay to `getCandidateLists` call in `use-lists-tab.ts` to handle transient bac | `plataforma-lia/src/components/talent-funnel-tabs/use-lists-tab.ts` |
| 🟢 | `2e1b0fde4` | 2026-04-11 | Frontend (UI) | Add history tab with clock icon to talent funnel page — Add HistoryTab component, Clock icon import, and a new TabsTrigger for the "historico" value in Funi | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `087d09486` | 2026-04-11 | Frontend (UI) | Task start baseline checkpoint for code review | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidateTabs.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟢 | `c283a2eea` | 2026-04-09 | Frontend (api/util) | feat: Dynamic sidebar sub-items for Talent Pools and Agents — Sidebar now shows active Talent Pools as sub-items under "Funil de Talentos" | `plataforma-lia/src/middleware.ts` |
| 🟢 | `e19a44a23` | 2026-04-09 | Empty/merge | fix: restore TalentPoolPage.tsx from bad merge corruption — A previous merge incorrectly inserted VoiceScreeningButton blocks | — |
| 🟢 | `5b36eacab` | 2026-04-07 | Frontend (UI) | Update date formatting to return empty string for null values — Modify formatDate and formatDateShort functions in useCandidatePageCore.tsx to return an empty strin | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx` |
| 🟢 | `820e3a54e` | 2026-04-06 | Frontend (UI) | Update candidate data handling and job configuration — Modify default values for candidate work model and contract type, adjust type casting for candidate  | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/components/candidate-modal.tsx`<br>`plataforma-lia/src/components/jobs/job-edit-tab/useJobEditTab.ts` |
| 🟢 | `65af36722` | 2026-04-01 | Frontend (UI) | Update job and vacancy pages and refine candidate profile — Adjusts routing and component rendering for job and vacancy pages, while also making internal refine | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/jobs/[id]/page.tsx`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx` |
| 🟡 | `48e2ace56` | 2026-03-30 | Frontend (UI) | Improve candidate profile and activity tab display and data handling — Update type casting and conditional rendering in CandidateActivitiesTab, CandidateFilesTab, Candidat | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/components/CandidatoActivitiesTab.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/components/CandidatoFilesTab.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/components/CandidatoOpinionsTab.tsx` |

### Task #117

- **Commits:** 10  |  **Período:** 2026-04-04 → 2026-04-10  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×5 🟢×4 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `70dfdc14c` | 2026-04-10 | Testes | Task #117: Create comprehensive quality test suite for LIA agents + diagnostic report generator — Components delivered: | `lia-agent-system/tests/quality_suite/__init__.py`<br>`lia-agent-system/tests/quality_suite/generate_diagnostic_report.py`<br>`lia-agent-system/tests/quality_suite/golden_dataset_scenarios.py` |
| 🟢 | `8b0564b3b` | 2026-04-04 | Frontend (UI) | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centralization across 80+ frontend files: | `plataforma-lia/src/components/job-wizard/FastTrackReviewPanel.tsx`<br>`plataforma-lia/src/components/pages/executive-dashboard-page.tsx`<br>`plataforma-lia/src/components/war-room.tsx` |
| 🟢 | `aa54798bd` | 2026-04-04 | Frontend (UI) | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centralization across 80+ frontend files: | `plataforma-lia/src/components/expanded-chat/hooks/useWizardPublishHandlers.ts` |
| 🟡 | `0162a53c0` | 2026-04-04 | Frontend (UI) | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centralization across 80+ frontend files: | `plataforma-lia/src/components/pages/dashboards-page/AgentActivityDashboard.tsx`<br>`plataforma-lia/src/components/pages/dashboards-page/AnaliseCompetenciasPlaceholder.tsx`<br>`plataforma-lia/src/components/pages/dashboards-page/BigFiveAnalyticsDashboard.tsx` |
| 🟡 | `c544eb884` | 2026-04-04 | Frontend (UI) | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centralization across 80+ frontend files: | `plataforma-lia/src/app/admin/page.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/expandedChatCriteriaExtractor.ts`<br>`plataforma-lia/src/components/pages/dashboards-page/FunilPerformancePlaceholder.tsx` |
| 🟢 | `d2e40a561` | 2026-04-04 | Frontend (UI) | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centralization across 80+ frontend files: | `plataforma-lia/src/components/candidate-preview/FilePreviewModal.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/expandedChatCriteriaExtractor.ts`<br>`plataforma-lia/src/components/pages/chat-page/constants/modern-conversations-part2.ts` |
| 🔴 | `4f1f720f8` | 2026-04-04 | Frontend (UI) | Task #117: Remove hardcoded prices + Audit client-side permissions — Comprehensive R$ currency centralization across 80+ frontend files: | `plataforma-lia/src/app/admin/clientes/[clientId]/metricas/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/riscos/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/riscos/seguro/page.tsx` |
| 🟢 | `bc4db6926` | 2026-04-04 | Frontend (UI) | Task #117: Remove hardcoded prices + Audit client-side permissions — Pricing centralization (src/lib/pricing.ts): | `plataforma-lia/src/components/modals/persona-creation-modal.tsx`<br>`plataforma-lia/src/components/module-access/module-upsell.tsx` |
| 🟡 | `3f6d309f3` | 2026-04-04 | Frontend (UI) | Task #117: Remove hardcoded prices + Audit client-side permissions — Pricing centralization (src/lib/pricing.ts): | `plataforma-lia/src/app/admin/page.tsx`<br>`plataforma-lia/src/app/upgrade/UpgradeClient.tsx`<br>`plataforma-lia/src/components/email-templates/email-template-form-modal.tsx` |
| 🟡 | `71a8019b1` | 2026-04-04 | Frontend (UI) | Task #117: Remove hardcoded prices + Audit client-side permissions — Pricing centralization: | `plataforma-lia/src/app/upgrade/UpgradeClient.tsx`<br>`plataforma-lia/src/components/module-access/module-upsell.tsx`<br>`plataforma-lia/src/utils/license-manager.tsx` |

### Task #70

- **Commits:** 10  |  **Período:** 2026-03-31 → 2026-03-31  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×7 🔴×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `f786852eb` | 2026-03-31 | IA | fix(task70): include consultant_alerts in error return path | `lia-agent-system/app/jobs/wsi_abandoned_service.py` |
| 🟡 | `ff0e76b5e` | 2026-03-31 | Backend | fix(task70): SendGrid custom_args metadata, reliable MessageQueue persistence — 1. SendGridEmailService._send_production: attach metadata dict as SendGrid | `lia-agent-system/app/domains/communication/services/email_service.py` |
| 🟡 | `eba78a733` | 2026-03-31 | Backend | fix(task70): webhook correlation, post-confirmation dispatch, terminal state guard — 1. feedback.auto_send creates MessageQueue entry with sg_message_id after | `lia-agent-system/app/domains/cv_screening/tools/candidate_tools.py`<br>`lia-agent-system/app/jobs/celery_tasks.py`<br>`lia-agent-system/app/jobs/followup_service.py` |
| 🟡 | `0d84e38cc` | 2026-03-31 | Backend | fix(task70): wire reject_candidate to auto-generate+send feedback (email+WhatsApp) — - New feedback.generate_and_send Celery task: loads candidate, builds | `lia-agent-system/app/domains/cv_screening/tools/candidate_tools.py`<br>`lia-agent-system/app/jobs/celery_tasks.py` |
| 🟡 | `dda84a29b` | 2026-03-31 | Backend | fix(task70): template learning persistent queries, follow-up unsubscribe check, auto-send at generation — - Template Learning: rewrite recommend_template and get_performance to use | `lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py` |
| 🔴 | `c122742a7` | 2026-03-31 | Cross IA↔Front | Task #70: Round 6 — fix EmailService class, persistent template learning, WhatsApp channels — - feedback.auto_send: uses SendGridEmailService (not EmailService) which | `lia-agent-system/app/jobs/wsi_abandoned_service.py`<br>`plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatCallbacks.ts`<br>`plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatModalCore.tsx` |
| 🔴 | `bcecf9aea` | 2026-03-31 | Cross Back↔Front | Task #70: Round 5 — zero 'any' types, EmailService routing, communication status update — Frontend: | `lia-agent-system/app/services/email_tracking_service.py`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx`<br>`plataforma-lia/src/components/search/JobFiltersSection.tsx` |
| 🟡 | `4c77f21bd` | 2026-03-31 | Cross IA↔Back | Task #70: Round 3 fixes — followup chain tracking, inactivity-based timeout, A/B integration, route alias — - Follow-up chain tracking: SQL query now checks engagement across the entire | `lia-agent-system/app/api/v1/email_tracking.py`<br>`lia-agent-system/app/jobs/wsi_abandoned_service.py`<br>`lia-agent-system/app/main.py` |
| 🔴 | `67824f102` | 2026-03-31 | Cross Back↔Front | Task #70: Round 2 fixes — ECDSA webhook verification, 24h follow-up cadence, revert unrelated frontend changes — - Webhook signature: replaced HMAC-SHA256 with ECDSA P-256 verification per | `lia-agent-system/app/api/v1/email_tracking.py`<br>`plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidatesPageModals.tsx` |
| 🟡 | `fdd822852` | 2026-03-31 | Cross IA↔Back | Task #70: Code review fixes — webhook signature, Template Learning wiring, feedback state machine, consultant escalation — - Webhook signature verification: _verify_sendgrid_signature() checks | `lia-agent-system/app/api/v1/email_tracking.py`<br>`lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`<br>`lia-agent-system/app/jobs/wsi_abandoned_service.py` |

### Task #82

- **Commits:** 10  |  **Período:** 2026-03-31 → 2026-04-09  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×5 🔴×3 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `bae244281` | 2026-04-09 | Docs | docs: update DEPLOY_GUIDE.md with 7 integration gaps (task #82) — ## What was done | `DEPLOY_GUIDE.md` |
| 🟢 | `803aa38a4` | 2026-03-31 | Frontend (api/util) | Task #82: Bell Notification In-App — Ativação Completa — - Added _create_bell_notification to ProactiveService with type/category | `plataforma-lia/src/hooks/use-notifications.ts` |
| 🔴 | `e1d7bf9b0` | 2026-03-31 | Cross Back↔Front | Task #82: Bell Notification In-App — Ativação Completa — - Added _create_bell_notification method to ProactiveService with type/category | `lia-agent-system/app/domains/automation/services/proactive_service.py`<br>`plataforma-lia/src/app/api/backend-proxy/notifications/chat/delivered/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/notifications/chat/route.ts` |
| 🟢 | `5367211ba` | 2026-03-31 | Frontend (UI) | feat(task-82): Bell Notification In-App — Ativação Completa — Core changes: | `plataforma-lia/src/app/api/backend-proxy/notifications/[id]/dismiss/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/notifications/[id]/read/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/notifications/read-all/route.ts` |
| 🔴 | `f5686a763` | 2026-03-31 | Frontend (UI) | Task #82: Bell Notification In-App — Ativação Completa — Core bell notification feature: | `plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/lgpd/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/page.tsx`<br>`plataforma-lia/src/components/activity-feed.tsx` |
| 🟡 | `51b35da21` | 2026-03-31 | Frontend (UI) | Task #82: Bell Notification In-App — Ativação Completa — Core bell notification feature: | `plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/page.tsx`<br>`plataforma-lia/src/components/activity-feed.tsx`<br>`plataforma-lia/src/components/big-five-modal.tsx` |
| 🟡 | `0d826b7b9` | 2026-03-31 | Frontend (UI) | Task #82: Bell Notification In-App — Ativação Completa — Core fixes: | `plataforma-lia/src/components/chat/ChatContextPanelPart3.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useWSIAndCalibrationHandlers.ts`<br>`plataforma-lia/src/components/jobs/JobEditTab.tsx` |
| 🟢 | `8747a535f` | 2026-03-31 | Frontend (UI) | Task #82: Bell Notification In-App — Ativação Completa — Fixed critical React hydration issue preventing bell button onClick from firing: | `plataforma-lia/src/components/email-templates/report-email-templates.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useWSIAndCalibrationHandlers.ts` |
| 🟢 | `10a159680` | 2026-03-31 | Frontend (UI) | Task #82: Bell Notification In-App — Ativação Completa — Fixed critical React hydration issue preventing bell button onClick from firing: | `plataforma-lia/src/components/notification-system.tsx`<br>`plataforma-lia/src/components/ui/EditLockButtons.tsx`<br>`plataforma-lia/src/hooks/use-edit-lock.tsx` |
| 🔴 | `a48928814` | 2026-03-31 | Cross Back↔Front | Task #82: Bell Notification In-App — Ativação Completa — ## Changes Made | `lia-agent-system/app/domains/automation/services/proactive_service.py`<br>`plataforma-lia/src/components/notifications/notification-center.tsx` |

### Tests (BE unit/integration)

**Descrição:** Testes unit + integration do FastAPI — characterization, tenant scope, wizard validators, etc.

**⚠️ Dependências para cherry-pick:** _is_dev_environment patched | golden eval set

**Arquivos canônicos:** lia-agent-system/tests/**

**Docs de referência:** —

- **Commits:** 10  |  **Período:** 2026-03-19 → 2026-04-20  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×5 🟡×4 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `d9127032c` | 2026-04-20 | Backend | Fix conversation summary crash from missing _extract_structured_ids helper — Original task (#637): `ConversationMemory._generate_summary_from_dicts` | `lia-agent-system/app/domains/recruiter_assistant/services/conversation_memory.py` |
| 🟡 | `101169222` | 2026-04-17 | Outro | Add tests for core platform functionalities and interactions — Adds a new Python script to `tests/lia_capabilities_audit.py` to perform comprehensive tests on LIA' | `tests/lia_capabilities_audit.py` |
| 🟢 | `098941b8f` | 2026-04-17 | Testes | Add integration test for sourcing pipeline against discriminatory JD — Original task (#342): write an integration test that exercises | `lia-agent-system/tests/integration/test_sourcing_pipeline_discriminatory_jd.py` |
| 🟢 | `15116c386` | 2026-04-14 | Testes | feat: 8 bias probe pairs for discrimination detection [P37-049] — Sprint 6 item 6.4 — 8 paired scenarios where profiles are IDENTICAL | `lia-agent-system/tests/eval/bias_probes/pairs.yaml` |
| 🟢 | `4bd124f89` | 2026-04-13 | Testes | Add tests for Rails health endpoints and update event handling — Adds unit tests for Rails health check endpoints and modifies `webhook_dispatcher.py` to integrate n | `lia-agent-system/tests/unit/test_rails_health_endpoint.py` |
| 🟢 | `4a44a6cd6` | 2026-04-11 | Testes | Update tests to reflect changes in orchestrator processing — Modify mock assertions in extended tests to expect `process_request` over `process_request_with_memo | `lia-agent-system/tests/unit/test_main_orchestrator_extended.py` |
| 🟡 | `2bf7cfa7f` | 2026-04-08 | Frontend (UI) | Bypass client-side authentication fetch by injecting user data from server — Implement server-side data injection for user authentication by modifying layout.tsx to fetch user d | `plataforma-lia/src/app/layout.tsx` |
| 🟡 | `8875c6747` | 2026-04-08 | Frontend (UI) | Improve login flow and remove development console logs — Update login page to redirect in development, prevent auth logout loops, and remove console logs. | `plataforma-lia/src/app/login/LoginClient.tsx`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsData.ts` |
| 🟢 | `f26ccce9d` | 2026-04-05 | Frontend (UI) | Update component styling and adjust backend import paths — Fix duplicated className in EAPTabNatural.tsx and update import paths for email providers in backend | `plataforma-lia/src/components/expandable-ai-prompt/tabs/EAPTabNatural.tsx` |
| 🔴 | `11d68f839` | 2026-03-19 | Cross IA↔Front | Introduce specialized sourcing agents and improve model configurations — Add new sub-agents for sourcing tasks (planner, search, enrich, engagement) and update agent configu | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/fairness_reports.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py` |

### Unified Chat (FE)

**Descrição:** UnifiedChat — dock lateral OU bottom-dock (Paulo prefere ambos), com painéis de wizard/tezi, chips contextuais, TaskContextBar.

**⚠️ Dependências para cherry-pick:** WebSocket | useWizardIntegration hook | TaskContextBar abaixo do input

**Arquivos canônicos:** plataforma-lia/src/components/unified-chat/**

**Docs de referência:** BRANCH_MAP — Unified Chat

- **Commits:** 10  |  **Período:** 2026-04-04 → 2026-04-28  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×6 🟡×2 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `c35035649` | 2026-04-28 | Frontend (UI) | Add functionality for selecting and displaying pipeline templates — Integrates a new component for selecting pipeline templates, updates API proxying for tasks, and ref | `plataforma-lia/src/app/api/backend-proxy/v1/tasks/route.ts`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🔴 | `c6220768f` | 2026-04-20 | Cross IA↔Front | Improve job creation and candidate sourcing workflows — Update job vacancy fields, fix action IDs, connect orphaned tools, resolve missing config file, and  | `lia-agent-system/app/shared/prompts/interaction_patterns.py`<br>`plataforma-lia/src/components/unified-chat/._OutreachCard.tsx`<br>`plataforma-lia/src/components/unified-chat/._ThinkingStepsCard.tsx` |
| 🟢 | `5e6356846` | 2026-04-19 | Frontend (UI) | Update chat to hide superseded assistant messages and test hydration — Add state to track superseded message IDs in UnifiedChat, filtering messages passed to UnifiedMessag | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟢 | `f48d315d8` | 2026-04-12 | Frontend (UI) | Adjust chat message font size for better readability — Change the font size of chat messages from 14px to 13px in UnifiedMessageList.tsx. | `plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🟢 | `9f3ec4871` | 2026-04-12 | Frontend (UI) | Fix chat page layout to remove middle scrollbar — Adjusted `UnifiedMessageList` to apply max-width to an inner wrapper, allowing the scrollable contai | `plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🟢 | `1c1674255` | 2026-04-10 | Frontend (UI) | Improve chat functionality and fix candidate data loading errors — Refactor unified chat component for resizable sidebar and floating mode, implement retry logic for c | `plataforma-lia/src/components/pages/candidates/hooks/candidates-core/useCandidatesData.ts`<br>`plataforma-lia/src/components/unified-chat/DashboardChatPanel.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟢 | `d27479384` | 2026-04-09 | Frontend (UI) | Improve chat interface by hiding the floating bubble and fixing scrollbars — Switch from useEffect to useLayoutEffect in ChatPageFullscreen to prevent the chat bubble from flash | `plataforma-lia/src/components/unified-chat/ChatPageFullscreen.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatConditional.tsx` |
| 🟢 | `2984d7d66` | 2026-04-09 | Frontend (UI) | Allow fullscreen chat to render even when sidebar is closed — Modify the rendering logic in UnifiedChat.tsx to ensure the fullscreen chat page is always visible,  | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟡 | `48b38e776` | 2026-04-09 | Frontend (UI) | Implement a unified chat interface with multiple display modes — Replace the existing LiaFloat conditional component with a new UnifiedChat component, introducing a  | `plataforma-lia/src/app/layout.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatBubble.tsx` |
| 🔴 | `69d0e5e28` | 2026-04-04 | Cross Back↔Front | Migrate local storage to Zustand stores and improve daily digest functionality — Replaces remaining localStorage usages with Zustand stores, and adds scheduled daily digest emails a | `lia-agent-system/app/api/v1/digest.py`<br>`lia-agent-system/app/domains/automation/services/automation_scheduler.py`<br>`plataforma-lia/src/app/teams-tab/candidatos/page.tsx` |

### Voice / ElevenLabs / STT

**Descrição:** Voice screening, STT (speech-to-text), ElevenLabs integration, voice_orchestrator.

**⚠️ Dependências para cherry-pick:** ElevenLabs API key | Tier 1 obrigatório (Quality Tier Guard) | task_type='voice'

**Arquivos canônicos:** lia-agent-system/app/domains/voice/**, plataforma-lia/src/components/voice/**

**Docs de referência:** I12_VOICE_SCREENING.md

- **Commits:** 10  |  **Período:** 2026-03-29 → 2026-04-21  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×5 🟢×4 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `cfe3f51fa` | 2026-04-21 | Empty/merge | fix: restore voice_service.py and granular_consent_service.py from broken merge — The previous "Apply changes" / stash-pop conflict resolution gutted two critical | — |
| 🟡 | `d2cafcea0` | 2026-04-18 | Cross IA↔Back | Refactor core voice screening logic and improve API error handling — This commit refactors the `process_call_completed` method in `wsi_voice_orchestrator.py` into smalle | `lia-agent-system/app/api/wsi_endpoints.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/question_builder.py`<br>`lia-agent-system/app/domains/cv_screening/services/wsi_service/session_repository.py` |
| 🟡 | `808811987` | 2026-04-13 | Backend | fix: rename path param in get_detailed_invoice to avoid FastAPI conflict | `lia-agent-system/app/api/v1/consumption.py`<br>`lia-agent-system/app/main.py` |
| 🔴 | `9bb5b231a` | 2026-04-10 | Cross IA↔Front | Improve chat functionality by using browser's speech recognition and fixing icon clipping — Integrates Web Speech API for real-time voice transcription in the chat input, updates the backend p | `lia-agent-system/app/domains/job_creation/domain.py`<br>`lia-agent-system/app/domains/job_creation/services/__init__.py`<br>`lia-agent-system/app/domains/job_creation/services/file_router.py` |
| 🟢 | `62b5797f8` | 2026-04-09 | Frontend (api/util) | Update text and border colors to match ElevenLabs design — Refactors CSS design tokens to align with ElevenLabs' color palette, utilizing black for primary tex | `plataforma-lia/src/styles/design-tokens.css` |
| 🟡 | `82e64b7af` | 2026-04-09 | Backend | Fix error in voice interview state machine logic — Instantiate NotificationService before use in voice interview state machine. | `lia-agent-system/app/services/voice_interview_state_machine.py` |
| 🟢 | `359a2c5a7` | 2026-04-09 | Docs | Create a design diagnostic document comparing LIA to ElevenLabs style — Create a markdown document detailing a design diagnostic between LIA and ElevenLabs, including scree | `deploy_guidde`<br>`plataforma-lia/docs/DIAGNOSTICO_DESIGN_ELEVENLABS.md`<br>`screenshots/lia-chat.jpg` |
| 🟡 | `561e99c47` | 2026-04-07 | Cross IA↔Back | feat(voice): Go-Live Deepgram STT & OpenMic.ai — Task #65 — Implements full production-ready integration for Deepgram (STT/transcription) | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/openmic_webhook.py`<br>`lia-agent-system/app/api/v1/system_health.py` |
| 🟡 | `d9a870fea` | 2026-04-04 | Backend | Update audio transcription tool description to reflect correct STT service — Update the description for the "scheduling_transcribe_audio" tool to accurately name the Speech-to-T | `lia-agent-system/app/domains/interview_scheduling/tools/__init__.py` |
| 🟢 | `c86edb10b` | 2026-03-29 | Docs | Update component inventory and add ElevenLabs theme analysis — Update the component inventory documentation to reflect changes in LIA categories and add a detailed | `docs/specs/frontend/INVENTARIO_COMPONENTES.md` |

### scope: audit

- **Commits:** 10  |  **Período:** 2026-03-31 → 2026-04-23  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×10

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `5bec8805f` | 2026-04-23 | Docs | docs(audit): add Archetypes feature end-to-end audit — Task #806: produces docs/audit/arquetipos/AUDITORIA_ARQUETIPOS.md, a | `docs/audit/arquetipos/AUDITORIA_ARQUETIPOS.md` |
| 🟢 | `e29e238ee` | 2026-04-21 | Docs | docs(audit): final consolidated audit for Benefícios + Departamentos + Workforce wave (#769) — Original task: Auditoria final consolidada da onda Benefícios + Departamentos + Workforce. | `docs/audits/beneficios-departamentos-workforce-final-2026-04.md` |
| 🟢 | `975d5e0d9` | 2026-04-21 | Docs | docs(audit): baseline Benefícios + Departamentos + Workforce (task #763) — Auditoria read-only entregue em | `docs/audits/beneficios-departamentos-workforce-audit-2026-04.md` |
| 🟢 | `6dceda378` | 2026-04-20 | Docs | docs(audit): correct stale "dead code" claims for tool_permissions loader and registry.py — Task #381 — fix the audit so the next agent doesn't follow incorrect cleanup | `docs/audits/AUDIT_STATUS_REPORT_2026-04-FINAL.md` |
| 🟢 | `2d95f7e1f` | 2026-04-16 | Docs | docs(audit): cross-cutting AI layer status report (task #302) — Investigative-only audit. No code changes. | `docs/audits/AUDIT_STATUS_REPORT_2026-04.md` |
| 🟢 | `928a6f4d8` | 2026-04-12 | Docs | feat(audit): Task #175 — Auditoria de Chaves de API, URLs e Secrets da Plataforma — Criado `lia-agent-system/docs/audit/secrets_and_connections_audit.md` com auditoria | `lia-agent-system/docs/audit/secrets_and_connections_audit.md` |
| 🟢 | `a8fe6cfb9` | 2026-04-01 | Docs | docs(audit): v8 FINAL — 62/70 (88%) \| Architecture 5/5, Testing 4/5, SEO 5/5 \| 0 arquivos >1kL, 50 testes, 24 páginas SEO | `plataforma-lia/docs/audit/frontend-audit-v8-final.md` |
| 🟢 | `8dcba821d` | 2026-03-31 | Docs | docs(audit): v6 corrigido com dados reais — 55/70, 39 arquivos >1kL, 756 testes, 17 dangerouslySetInnerHTML | `plataforma-lia/docs/audit/frontend-audit-v6-scores.md` |
| 🟢 | `ed443047b` | 2026-03-31 | Docs | docs(audit): v6 final — 55/70 (TypeScript 5/5, ESLint 0 errors, Vue 100% Pinia-ready) | `plataforma-lia/docs/audit/frontend-audit-v6-scores.md` |
| 🟢 | `51a9313dc` | 2026-03-31 | Docs | docs(audit): frontend audit v6 — final score after all improvements | `plataforma-lia/docs/audit/frontend-audit-v6-scores.md` |

### scope: chat

- **Commits:** 10  |  **Período:** 2026-04-06 → 2026-04-18  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×6 🔴×2 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `e8f2ede85` | 2026-04-18 | Testes | test(chat): cover WS-timeout watchdog fallback in useChatMessages — Task #415 — adds vitest coverage for the F2 watchdog branch in | `plataforma-lia/src/hooks/__tests__/useChatMessages.test.ts` |
| 🟢 | `3e4367a88` | 2026-04-17 | Frontend (UI) | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da LIA agora é arrastável para qualquer | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatBubble.tsx` |
| 🟢 | `dd098c857` | 2026-04-17 | Frontend (UI) | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da LIA agora é arrastável para qualquer | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatBubble.tsx`<br>`plataforma-lia/src/components/unified-chat/floating-position.ts` |
| 🔴 | `1231c6b1f` | 2026-04-17 | Cross Back↔Front | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da LIA agora é arrastável para qualquer | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/floating-position.ts` |
| 🔴 | `7057f692e` | 2026-04-17 | Cross Back↔Front | feat(chat): tornar bolha e janela flutuante da LIA arrastáveis — Task #409 — UX: chat flutuante da LIA agora é arrastável para qualquer | `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatBubble.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatHeader.tsx` |
| 🟢 | `f8e824d33` | 2026-04-17 | Frontend (api/util) | fix(chat): show error bubble when LIA REST proxy returns no content — Task #377 — fixes the F1 finding from the unified-chat-no-response audit | `plataforma-lia/src/hooks/chat/useChatMessages.ts` |
| 🟡 | `41c848948` | 2026-04-09 | Frontend (UI) | feat(chat): Padronizar visual do chat LIA — avatar, bubble, fonte (Task #88) — ## Objetivo | `plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/chat/message-bubble.tsx`<br>`plataforma-lia/src/components/expanded-chat/components/ChatMessageList.tsx` |
| 🟢 | `444a4ab80` | 2026-04-06 | Frontend (UI) | fix(chat): restore outer card border on prompt inputs — single card wrapping input + buttons (Task #28) — Task #23 incorrectly removed the outer bordered card from prompt inputs | `plataforma-lia/src/components/chat/chat-input-bar.tsx`<br>`plataforma-lia/src/components/kanban/components/TransitionChatPanel.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx` |
| 🟡 | `bbe405048` | 2026-04-06 | Frontend (UI) | fix(chat): corrigir auto-scroll, avatar do usuário e ícone Brain no input — Task #25 — Três correções nos chats/prompts da plataforma: | `plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/chat/chat-input-bar.tsx`<br>`plataforma-lia/src/components/lia-float/LiaChatInput.tsx` |
| 🟢 | `127d6284a` | 2026-04-06 | Frontend (UI) | feat(chat): Polish do Chat — Cards, Cores e Histórico Recente (Task #24) — ## Changes | `plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/ui/prompt-suggestions-dock.tsx` |

### §4 Rail Features — Rail A

**Descrição:** Rail A — capability metadata + Tier 0.0 + Pydantic schema + rail_a_hint_override + capability map + entity resolver (PR-J). Inclui CompactReels canonical, register_hire (PR-HIRE), policy gate, send_offer, generate_job_report, forecast, start_wsi_flow.

**⚠️ Dependências para cherry-pick:** capability_map.yaml com 11 intents | rail_a_capability_check no orchestrator Phase 0.0 | LIAGlobalModals listener no FE | useModalOpenListener hook

**Arquivos canônicos:** lia-agent-system/app/config/capability_map.yaml, app/services/capability_map_service.py, app/services/entity_resolver_service.py, plataforma-lia/src/components/lia-global-modals/, src/hooks/chat/useModalOpenListener.ts

**Docs de referência:** BRANCH_MAP §4

- **Commits:** 10  |  **Período:** 2026-04-08 → 2026-04-29  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×5 🔴×3 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `8e69d85d7` | 2026-04-29 | Frontend (api/util) | test(rail-a): 33/33 E2E passando — fix snapshot timeouts + 3 NAVIGATION->CHAT — Fixes para 33/33 testes Rail A verdes: | `plataforma-lia/e2e/tests/chat/rail-a-cards.spec.ts`<br>`plataforma-lia/package.json` |
| 🟢 | `d0245efb9` | 2026-04-29 | Testes | Add end-to-end tests for interactive chat cards — Add new end-to-end tests for the 'Rail A' chat cards, covering navigation, modal, and click events. | `plataforma-lia/e2e/tests/chat/rail-a-cards.spec.ts`<br>`plataforma-lia/e2e/tests/chat/rail-a-cards.spec.ts-snapshots/ral-00-initial-desktop-chrome-linux.png`<br>`plataforma-lia/e2e/tests/chat/rail-a-cards.spec.ts-snapshots/ral-01-vaga-desktop-chrome-linux.png` |
| 🟢 | `3c7b44e89` | 2026-04-29 | Frontend (UI) | refactor(rail-a): PR-H+PR-L — canonical stages + DS color-mix tokens — PR-H: remove STAGE_STRUCTURES/UTILITY_STRUCTURES from chat-workflow-reels. | `plataforma-lia/src/components/ui/chat-workflow-reels.tsx`<br>`plataforma-lia/src/components/workflow-rail/canonicalFunnelStages.ts` |
| 🟢 | `7da120da6` | 2026-04-28 | Frontend (UI) | feat(rail-a): PR-Q1 — direct nav + modal dispatch for talent-pool and add-candidate — - NAVIGATION_OVERRIDES: add talent-pool → /bancos-de-talentos (card 2.3 no longer | `plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🟡 | `c40a82af1` | 2026-04-28 | IA | feat(rail-a): Wave 1 PR-Q2+Q3 — add close_job, generate_job_report, forecast, start_wsi_flow to capability_map — harness-engineering guide computacional: 4 new intents in capability_map.yaml | `lia-agent-system/app/config/capability_map.yaml` |
| 🟡 | `d8c34d554` | 2026-04-28 | IA | feat(rail-a): wire rail_a_capability_check into main_orchestrator Phase 0.0 (PR-J) — harness-engineering guide computacional: check_rail_a_capability() now called | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟢 | `4d4f4f07b` | 2026-04-28 | Frontend (UI) | fix(rail-a): canonical-fix pulse scope CompactReels + testes 29/29 verde — - CompactReels chama usePipelinePulse() diretamente (pulse estava out-of-scope) | `plataforma-lia/src/components/ui/chat-workflow-reels.tsx` |
| 🔴 | `ec6ef7bb7` | 2026-04-27 | Cross Back↔Front | feat(pr-m): add active-jobs pulse badge to Vaga node in Rail A — - PipelinePulseResponse: add active_jobs field (default=0, backward-compat) | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/domains/job_vacancies_analytics/repositories/job_vacancies_analytics_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/pipeline-pulse/route.ts` |
| 🔴 | `ece44f52d` | 2026-04-27 | Cross IA↔Front | chore(rail-a): remove PR-A from sprint-I (extracted to feat/pr-a-rail-a-metadata) — PR-A foi extraido para uma branch dedicada (feat/pr-a-rail-a-metadata, | `lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🔴 | `76e081686` | 2026-04-08 | Cross Back↔Front | Update application styling and fix component rendering issues — Standardize typography and fix server component rendering errors by introducing a client-side wrappe | `lia-agent-system/alembic/versions/055_create_talent_pools.py`<br>`lia-agent-system/alembic/versions/056_create_sourcing_agents.py`<br>`lia-agent-system/alembic/versions/057_create_recruitment_campaigns.py` |

### Backend (shared)

**Descrição:** Backend shared utilities — chat_event_serializer, tenant_*, pii_masking, providers.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** lia-agent-system/app/shared/**

**Docs de referência:** —

- **Commits:** 9  |  **Período:** 2026-04-07 → 2026-04-25  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×9

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `a27c50399` | 2026-04-25 | Backend | Strengthen demo data validation with direct database checks — Update demo data seeding to perform strict post-seed validation by directly querying target tables f | `lia-agent-system/app/shared/services/seed_service.py` |
| 🟡 | `6da287859` | 2026-04-14 | Backend | feat: TTF ML model — training script + predictor + endpoint integration [P37-074] — Sprint 11 item 11.4 — First real ML model for the platform. | `lia-agent-system/app/api/v1/ml_predictions_dashboard.py` |
| 🟡 | `d0b237ed1` | 2026-04-14 | Backend | fix: WSManager Redis Pub/Sub broadcast across workers [PX08-025] — Sprint 2 item 2.2 — WSManager was singleton in-process: messages sent | `lia-agent-system/app/main.py` |
| 🟡 | `a5dce0848` | 2026-04-13 | Backend | Add API response envelope and contract tests for Rails events — Introduce Pydantic models for API responses, create response helper functions, implement a middlewar | `lia-agent-system/app/shared/api/__init__.py`<br>`lia-agent-system/app/shared/api/response.py` |
| 🟡 | `9efdafa14` | 2026-04-12 | Backend | Remove unused tenant isolation error message — Remove the dead _MODULE_CONTEXT_MISSING_RESPONSE constant and an unused import from tool_handler.py. | `lia-agent-system/app/shared/tool_handler.py` |
| 🟡 | `e2c2b0db3` | 2026-04-07 | Backend | Add cross-cutting service descriptions for agent health and tenant context — Add comments to agent_health_alert_service.py and tenant_context_service.py clarifying their cross-c | `lia-agent-system/app/shared/services/agent_health_alert_service.py`<br>`lia-agent-system/app/shared/services/tenant_context_service.py` |
| 🟡 | `523a48110` | 2026-04-07 | Backend | Expand deployment guide with integration details and readiness assessments — Update DEPLOY_GUIDE.md to include detailed sections on integration mapping, frontend and AI layer re | `lia-agent-system/app/shared/services/hybrid_search_service.py`<br>`lia-agent-system/app/shared/services/rag_pipeline_service.py` |
| 🟡 | `3e1546510` | 2026-04-07 | Backend | fix: Phase 3 completion — encryption package fix + Phase 3 tracker update — - app/shared/encryption/__init__.py: package was empty, shadowing flat | `lia-agent-system/app/shared/encryption/__init__.py` |
| 🟡 | `d150fc368` | 2026-04-07 | Backend | Add dependency injection for feature flag service — Introduce a FastAPI dependency injection factory for the FeatureFlagService singleton, ensuring shar | `lia-agent-system/app/shared/governance/feature_flag_service.py` |

### Data fetching / SWR

- **Commits:** 9  |  **Período:** 2026-03-30 → 2026-04-08  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×7 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `836bd3971` | 2026-04-08 | Frontend (UI) | Add resilience and retry logic to job data fetching — Introduce retry mechanism for `listJobVacancies` API calls in `useJobsData` hook and update job vaca | `plataforma-lia/src/components/pages/jobs/hooks/useJobsData.ts` |
| 🟢 | `7c0af9e69` | 2026-03-31 | Testes | test: adiciona testes para useDashboardSummary e usePlatformMetrics (admin SWR) | `plataforma-lia/src/hooks/__tests__/admin-useDashboardSummary.test.ts`<br>`plataforma-lia/src/hooks/__tests__/admin-usePlatformMetrics.test.ts` |
| 🟢 | `a516c593d` | 2026-03-30 | Docs | docs: audit score v3 - 47.5/60 (+2.0 from Session 2 SWR+tests+memo) | `plataforma-lia/docs/audit/frontend-audit-v3-scores.md` |
| 🟢 | `1b34ed4e8` | 2026-03-30 | Testes | test: corrige 14 testes quebrados pos-migracao SWR — wrapper cache isolado | `plataforma-lia/src/hooks/__tests__/use-ai-credits.test.ts`<br>`plataforma-lia/src/hooks/__tests__/use-daily-briefing.test.ts`<br>`plataforma-lia/src/hooks/__tests__/use-proactive-insights.test.ts` |
| 🟢 | `5e5f2ddc1` | 2026-03-30 | Frontend (api/util) | fix: restore quotes and SWR cache updates in useDefaultTemplates + useAuditLogs — - useDefaultTemplates: add missing string quotes, fix SWR keys, quote | `plataforma-lia/src/hooks/admin/useAuditLogs.ts`<br>`plataforma-lia/src/hooks/admin/useDefaultTemplates.ts` |
| 🟡 | `31f857e8c` | 2026-03-30 | Frontend (api/util) | fix: restore quotes, SWR cache updates, and refetch types in all hooks — - useGlobalPolicies: add missing string quotes, fix SWR key, fix | `plataforma-lia/src/hooks/admin/useBiasAudits.ts`<br>`plataforma-lia/src/hooks/admin/useClientSaasMetrics.ts`<br>`plataforma-lia/src/hooks/admin/useComplianceControls.ts` |
| 🟢 | `b3374b0eb` | 2026-03-30 | Frontend (api/util) | fix: restore quotes and SWR cache updates in 3 admin hooks — useComplianceControls, useLGPDCompliance, useTechnicalTests: | `plataforma-lia/src/hooks/admin/useComplianceControls.ts`<br>`plataforma-lia/src/hooks/admin/useLGPDCompliance.ts`<br>`plataforma-lia/src/hooks/admin/useTechnicalTests.ts` |
| 🟢 | `649b0a2a0` | 2026-03-30 | Frontend (api/util) | fix: useBiasAudits.fetchAudits now updates SWR cache with fetched results — fetchAudits was discarding the API response. Now uses mutate() to | `plataforma-lia/src/hooks/admin/useBiasAudits.ts` |
| 🟢 | `cbdead177` | 2026-03-30 | Frontend (api/util) | fix: add missing quotes in hook files — SWR keys, imports, use client directive — Fixed syntax errors in 4 hook files where string quotes were stripped: | `plataforma-lia/src/hooks/admin/useDashboardSummary.ts`<br>`plataforma-lia/src/hooks/admin/usePlatformMetrics.ts`<br>`plataforma-lia/src/hooks/use-ai-credits.ts` |

### Refactor / Cleanup

**Descrição:** Limpeza de arquivos órfãos — `.bak` files do split (Etapa 6), helper scripts de debug, arquivos acidentais (`=133`, `=141`, `=350`), JSX comments duplos, monolith definitions descartadas.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** lia-agent-system/app/api/v1/*.bak, root accidentais, helper scripts apply_*.py

**Docs de referência:** —

- **Commits:** 9  |  **Período:** 2026-03-29 → 2026-04-22  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×7 🟢×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `0cdf20288` | 2026-04-22 | Frontend (api/util) | Remove all job readiness related endpoints and documentation — Removes deprecated job readiness endpoints from api.generated.ts and updates ARCITECTURE.md, SPARKLE | `plataforma-lia/src/types/api.generated.ts` |
| 🟡 | `b7ac5d94a` | 2026-04-21 | Outro | chore: remove stray helper scripts from prior debug sessions | `apply_jwt_blacklist.py`<br>`fix_replit_tools.py` |
| 🟡 | `0eb9c7013` | 2026-04-21 | Outro | chore: remove stray repair_tools.py from prior debugging session | `repair_tools.py` |
| 🟡 | `d46fd1dae` | 2026-04-19 | Outro | Remove unnecessary data from the system — Remove a leftover data artifact from the system. | `=133` |
| 🟡 | `ccdedc141` | 2026-04-08 | Outro | Fix issue causing users to see a blank page and ensure proper data display — Add missing database columns and re-export internal functions to resolve rendering errors. | `1`<br>`200` |
| 🟡 | `11ee7c473` | 2026-04-01 | Outro | chore: remove accidental =350 file | `=350` |
| 🟡 | `e80a660e4` | 2026-03-31 | Outro | chore: remove accidental artifact file | `=141` |
| 🟢 | `78ff81786` | 2026-03-30 | Frontend (UI) | fix: corrige JSX comment duplo em layout.tsx — {{/* → {/* | `plataforma-lia/src/app/layout.tsx` |
| 🟡 | `be19ab5c5` | 2026-03-29 | Outro | Add monolith definition to support new project structure — Add a new section for defining monoliths in the project configuration. | `2000`<br>`2000L` |

### Task #48

- **Commits:** 9  |  **Período:** 2026-03-26 → 2026-04-06  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟢×8 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `7ddd5a092` | 2026-04-06 | Backend | Task #48: Auditoria e Correção de Todos os Prompts LIA — Paridade de Capacidades — Fix LIA pipeline status change awareness across all prompt/capability files. | `lia-agent-system/app/api/v1/lia_assistant/conversational.py` |
| 🟢 | `964cba894` | 2026-03-26 | Docs | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v8) — Fixed all remaining endpoint/schema inaccuracies: | `docs/specs/backend/API_CONTRACTS.md` |
| 🟢 | `1b32a5cb5` | 2026-03-26 | Docs | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v7) — All fields/endpoints verified against actual source code with line references: | `docs/specs/backend/API_CONTRACTS.md`<br>`docs/specs/backend/DATA_MODELS.md` |
| 🟢 | `fa0863239` | 2026-03-26 | Docs | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v6) — Final fixes with source-verified corrections: | `docs/specs/backend/API_CONTRACTS.md`<br>`docs/specs/backend/DATA_MODELS.md` |
| 🟢 | `2b3c8d96a` | 2026-03-26 | Docs | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v5) — Fixed all verified inaccuracies against source code: | `docs/specs/backend/API_CONTRACTS.md`<br>`docs/specs/backend/DATA_MODELS.md` |
| 🟢 | `f285c5273` | 2026-03-26 | Docs | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v4) — All factual inaccuracies fixed with exact source verification: | `docs/specs/backend/API_CONTRACTS.md`<br>`docs/specs/backend/DATA_MODELS.md` |
| 🟢 | `9082c86fd` | 2026-03-26 | Docs | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (v3 fixes) — Fixed all code review issues with source-verified corrections: | `docs/specs/backend/API_CONTRACTS.md`<br>`docs/specs/backend/DATA_MODELS.md` |
| 🟢 | `33b50bf96` | 2026-03-26 | Docs | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md (fixed) — Updated both backend specification documents to address code review findings: | `docs/specs/backend/API_CONTRACTS.md`<br>`docs/specs/backend/DATA_MODELS.md` |
| 🟢 | `3725250df` | 2026-03-26 | Docs | Task #48: SDD Semana 2 — DATA_MODELS.md + API_CONTRACTS.md — Created/updated two comprehensive backend specification documents: | `docs/specs/backend/API_CONTRACTS.md`<br>`docs/specs/backend/DATA_MODELS.md` |

### scope: typescript

- **Commits:** 9  |  **Período:** 2026-04-01 → 2026-04-01  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🔴×4 🟡×3 🟢×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `3e94c0928` | 2026-04-01 | Frontend (UI) | fix(typescript): resolve type mismatches from Phase 6 splits | `plataforma-lia/src/components/expanded-chat/hooks/useCompanyConfigLoader.tsx`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesInteractions.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesNavigation.ts` |
| 🟢 | `36214ec8b` | 2026-04-01 | Frontend (UI) | fix(typescript): resolve final 4 @ts-nocheck files — 269 → minimum necessary | `plataforma-lia/src/components/email-templates/report-email-templates.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt.tsx`<br>`plataforma-lia/src/components/screening-config/SCMSectionContent.tsx` |
| 🔴 | `d1c58f11a` | 2026-04-01 | Frontend (UI) | fix(typescript): remove @ts-nocheck from components <=600L | `plataforma-lia/src/components/activity-feed.tsx`<br>`plataforma-lia/src/components/autonomous/proactive-actions-bell.tsx`<br>`plataforma-lia/src/components/autonomous/proactive-actions.tsx` |
| 🔴 | `b6eaf7998` | 2026-04-01 | Frontend (UI) | fix(typescript): remove @ts-nocheck from large components (>600L) + fix type errors | `plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/controles/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/lgpd/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/page.tsx` |
| 🔴 | `80bcdf8a5` | 2026-04-01 | Frontend (UI) | fix(typescript): remove @ts-nocheck from lib/types/services/small components | `plataforma-lia/src/app/admin/clientes/[clientId]/comunicacoes/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/controles/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/incidentes/page.tsx` |
| 🟡 | `c8472b613` | 2026-04-01 | Frontend (UI) | fix(typescript): remove @ts-nocheck from large hooks (500-1000L) + fix exposed types — - Removed @ts-nocheck from 13 hooks (530-1000L range) | `plataforma-lia/src/components/expandable-ai-prompt/useEAPCallbacks.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/useExpandableAIPromptCore.tsx`<br>`plataforma-lia/src/components/expanded-chat/hooks/useCriteriaDetection.ts` |
| 🔴 | `4e1427281` | 2026-04-01 | Frontend (UI) | fix(typescript): remove @ts-nocheck from context panels + small pages | `plataforma-lia/src/app/admin/clientes/[clientId]/jornada/page.tsx`<br>`plataforma-lia/src/components/PromptContextViewer.tsx`<br>`plataforma-lia/src/components/chat/ChatContextPanelPart2.tsx` |
| 🟡 | `f68a2e13c` | 2026-04-01 | Frontend (UI) | fix(typescript): remove @ts-nocheck from 18 API proxy routes | `plataforma-lia/src/app/api/auth/workos/callback/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/communication/send-email/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/communication/send-screening-invite/route.ts` |
| 🟡 | `4c0b24059` | 2026-04-01 | Frontend (UI) | fix(typescript): remove @ts-nocheck from small hooks + fix exposed type errors — Remove @ts-nocheck from 10 hooks with <200 lines as part of Vue migration type safety improvements. | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesCVHandlers.ts`<br>`plataforma-lia/src/components/pages/indicators/useIndicatorsPage.ts`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanCandidateLoader.ts` |

### Auditoria / Audit Rev

- **Commits:** 8  |  **Período:** 2026-03-30 → 2026-04-27  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×5 🟡×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `5d7c93349` | 2026-04-27 | Cross IA↔Front | audit Rev 4: fechar F4 PM-02 (token streaming) + PM-03 (protocol handshake) — Resolve os P3 remanescentes da Auditoria Rev 4 do wizard de criação de | `lia-agent-system/app/api/v1/_ws_stream_helpers.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/lia_assistant/wizard.py` |
| 🟢 | `96d5c4f7c` | 2026-04-21 | Docs | Audit: 4 LIA conversation interpretation failures (Task #738) — Investigation-only task. Produced report at | `docs/audits/auditoria-conversa-lia-busca.md` |
| 🟡 | `0cae132ea` | 2026-04-18 | Backend | audit: fix duplicate field, add technical-exposure rules, canonical entity_id | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `676273609` | 2026-04-17 | Backend | Audit: tighten require_company multi-tenant isolation across LIA tool registries — Reduced `require_company=False` occurrences from 89 → 18 across 7 tool registry | `lia-agent-system/app/domains/analytics/agents/analytics_tool_registry.py`<br>`lia-agent-system/app/domains/autonomous/agents/autonomous_tool_registry.py`<br>`lia-agent-system/app/domains/hiring_policy/agents/policy_tool_registry.py` |
| 🟢 | `d611d642f` | 2026-04-11 | Docs | Deep audit revision of PRODUCT_READINESS_AUDIT_REPORT.md — Updated the correct audit document (PRODUCT_READINESS_AUDIT_REPORT.md at repo root) | `PRODUCT_READINESS_AUDIT_REPORT.md` |
| 🟢 | `44ed2241e` | 2026-04-03 | Docs | QA Audit: Candidate Preview Panel - Production vs Replit Reference — Complete rewrite of audit document focused on WeDOTalent production | `plataforma-lia/docs/audit-candidate-preview-qa.md`<br>`plataforma-lia/docs/screenshots/replit-01-funil-de-talentos.jpg`<br>`plataforma-lia/docs/screenshots/replit-02-search-with-query.jpg` |
| 🟢 | `6399fc2cb` | 2026-03-30 | Docs | audit: score v2 pos Fases 6-9 — Skill 9 auditoria final | `docs/audit/frontend-audit-v2-scores.md` |
| 🟢 | `042aa1335` | 2026-03-30 | Docs | design-audit: corrige espacamentos arbitrarios + dark mode tokens + relatorio FASE7 — Skill 7 | `docs/specs/frontend/DESIGN_AUDIT_FASE7.md` |

### Docs / Architecture

**Descrição:** Documentos de arquitetura — diagramas, MAPA_CAMADA_INTELIGENCIA, RELATORIO_CAPACIDADES, DIAGNOSTIC_REPORT, ARCHITECTURE.md.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** lia-agent-system/docs/MAPA_CAMADA_INTELIGENCIA.md, ARCHITECTURE.md, replit.md, relatorio_capacidades_prompts_lia.md, DIAGNOSTIC_REPORT_*.md

**Docs de referência:** ARCHITECTURE.md raiz

- **Commits:** 8  |  **Período:** 2026-03-15 → 2026-04-23  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×7 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `12bf9953b` | 2026-04-23 | Docs | Update documentation to reflect current system architecture and agent counts — Refactor documentation to replace outdated ConversationGraph and ReActLoop references with LangGraph | `lia-agent-system/docs/MAPA_CAMADA_INTELIGENCIA.md` |
| 🟢 | `59a71de41` | 2026-04-14 | Docs | docs: Langfuse integration decision — N/A, covered by LangSmith [PX08-070] — Sprint 10 item 10.5 — Evaluated Langfuse integration and determined | `lia-agent-system/app/config/langfuse_decision.md` |
| 🟢 | `98a2c20e5` | 2026-04-11 | Docs | docs: comprehensive diagnostic report - architecture, domains, Rails ATS analysis | `DIAGNOSTIC_REPORT_APRIL_2026.md` |
| 🟡 | `0616a0776` | 2026-03-31 | Outro | Update documentation to remove outdated references — Remove all remaining "Task" and "ARCH" references from the documentation. | `=200` |
| 🟢 | `c651bc305` | 2026-03-19 | Docs | Update prompt management to include modification timestamps — Add 'updated_at' field to YAML prompts for better tracking and auditing, specifying 9 files in app/p | `relatorio_capacidades_prompts_lia.md` |
| 🟢 | `51cdc8a26` | 2026-03-19 | Docs | Update documentation to reflect latest platform capabilities and features — Update the `relatorio_capacidades_prompts_lia.md` file to reflect version 4.4, detailing new feature | `relatorio_capacidades_prompts_lia.md` |
| 🟢 | `5fc57171c` | 2026-03-16 | Docs | docs: update replit.md with ReAct JSON strip documentation | `replit.md` |
| 🟢 | `0d16fb162` | 2026-03-15 | Docs | docs: relatorio_capacidades_prompts_lia.md v4.2 — atualização completa seções 1-34 — Atualização profunda das seções 5, 9, 13, 15, 17, 18, 25 e 34 para refletir | `relatorio_capacidades_prompts_lia.md` |

### Docs / Propostas

**Descrição:** Propostas técnicas — análises arquiteturais, paralelos com legacy v5.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** proposals/**

**Docs de referência:** —

- **Commits:** 8  |  **Período:** 2026-03-19 → 2026-03-22  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×8

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `cb3766888` | 2026-03-22 | Docs | Add visual diagrams explaining proposed architecture changes — Add ASCII diagrams to illustrate current v5 architecture, proposed Caminho 3, and the 6 Pillars laye | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `7ebcf72c7` | 2026-03-22 | Docs | Add detailed implementation guides for migrating code to a new structure — Introduce comprehensive guides for migrating code to a new architecture, including operational steps | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `96a63d512` | 2026-03-22 | Docs | Diagnose and fix architectural issues in the code structure — Introduce a new diagnostic section detailing root causes of architectural problems, 23 specific conc | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `309097ecd` | 2026-03-20 | Docs | Add expanded coverage panel detailing v5 service and LIA implementation — Adds an expanded panel detailing v5 service and LIA implementation across domains, and updates Secti | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |
| 🟢 | `50632b526` | 2026-03-19 | Docs | Update tool scope documentation to reflect correct file paths — Correctly references `app/tools/scope_config.py` instead of `app/orchestrator/scope_config.py` and c | `proposals/mapeamento_capacidades_prompts_lia.md` |
| 🟢 | `baf2bfa7c` | 2026-03-19 | Docs | Add detailed technical guides for creating custom agents — Adds comprehensive technical documentation for implementing custom agent configurations in both LIA  | `proposals/Paralelo_LIA_vs_V5_Arquitetura_IA.md` |
| 🟢 | `7efc6fc3c` | 2026-03-19 | Docs | Update technical document with accurate v5 system details — Revise and expand technical documentation by correcting factual inaccuracies about the v5 system, in | `proposals/Paralelo_LIA_vs_V5_Arquitetura_IA.md` |
| 🟢 | `dd6e179f1` | 2026-03-19 | Docs | Add market analysis and recommendations to the existing document — Integrate market analysis, pros/cons, and recommendations into the `Paralelo_LIA_vs_V5_Arquitetura_I | `proposals/Paralelo_LIA_vs_V5_Arquitetura_IA.md` |

### Fase 2C

- **Commits:** 8  |  **Período:** 2026-03-27 → 2026-03-27  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×5 🟢×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `320871d8c` | 2026-03-27 | Frontend (UI) | Fase 2C — Lote 9 — Tokenização de hex hardcoded (conclusão) — Últimos 31 arquivos convertidos para tokens do Design System v4.2.1. | `plataforma-lia/src/components/admin/AdminTemplateHub.tsx`<br>`plataforma-lia/src/components/admin/Breadcrumbs.tsx`<br>`plataforma-lia/src/components/agent-control-center/index.tsx` |
| 🟢 | `f2935fc51` | 2026-03-27 | Frontend (UI) | Fase 2C — Lote 8: tokenização hex (7 arquivos, ~20 substituições) — - job-kanban-page: border-l-[#1F2937] → border-l-gray-800, #e5e7eb → gray-200, #d1d5db → gray-300 | `plataforma-lia/src/components/job-creation/compensation-chat-message.tsx`<br>`plataforma-lia/src/components/job-creation/competencies-chat-message.tsx`<br>`plataforma-lia/src/components/job-creation/vacancy-search-results.tsx` |
| 🟡 | `bbe0f3697` | 2026-03-27 | Frontend (UI) | Fase 2C — Lote 7: tokenização hex (6 arquivos, ~15 substituições) — - agent-detail-panel: #60D186 → var(--wedo-green-bright) em funções de cor (style CSS) | `plataforma-lia/src/components/agent-control-center/agent-detail-panel.tsx`<br>`plataforma-lia/src/components/pages/ai-credits-page.tsx`<br>`plataforma-lia/src/components/pages/big-five-dashboard-page.tsx` |
| 🟡 | `96a723874` | 2026-03-27 | Frontend (UI) | Fase 2C — Lote 6: tokenização hex (7 arquivos, ~20 substituições) — - jobs-page: #D5BFA8 → gray-300, #E8E4E0 → gray-100 (cores de status de screening) | `plataforma-lia/src/components/agent-control-center/agent-detail-panel.tsx`<br>`plataforma-lia/src/components/charts/interactive-charts.tsx`<br>`plataforma-lia/src/components/chat/agent-memory-indicator.tsx` |
| 🟢 | `e1426f848` | 2026-03-27 | Frontend (UI) | Fase 2C — Lote 5: tokenização hex (5 arquivos, ~30 substituições) — - lia-library-page: category colors → var(--gray-*) + var(--wedo-orange) | `plataforma-lia/src/components/candidate-preview.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/search/SimilarProfilesInput.tsx` |
| 🟡 | `8a0bbd763` | 2026-03-27 | Frontend (UI) | Fase 2C — Lote 3: tokenização hex (8 arquivos, ~50 substituições) — - CATEGORY_COLORS pastel → var(--gray-50/100) em prompt-suggestions-dock + LiaSuperPrompt | `plataforma-lia/src/components/activity-feed.tsx`<br>`plataforma-lia/src/components/daily-briefing-card.tsx`<br>`plataforma-lia/src/components/lia-float/LiaSuperPrompt.tsx` |
| 🟡 | `49757639e` | 2026-03-27 | Frontend (UI) | Fase 2C/2D — Lote 2: tokenização hex residuais (9 arquivos) — Substitui hex hardcoded por CSS vars semânticas em: | `plataforma-lia/src/components/lia-float/LiaSuperPrompt.tsx`<br>`plataforma-lia/src/components/pages/dashboards-page.tsx`<br>`plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx` |
| 🟡 | `2947fb28a` | 2026-03-27 | Frontend (UI) | Fase 2C/2D — Tokenização de hex hardcoded (650 → 353, -46%) — Bridge Architecture: substituição sistemática de hex por CSS vars semânticos. | `plataforma-lia/src/components/activity-feed.tsx`<br>`plataforma-lia/src/components/candidate-page.tsx`<br>`plataforma-lia/src/components/candidate-preview.tsx` |

### Hooks (FE)

**Descrição:** Hooks customizados (chat, candidates, jobs, recruitment, company).

**⚠️ Dependências para cherry-pick:** Endpoints correspondentes

**Arquivos canônicos:** plataforma-lia/src/hooks/**

**Docs de referência:** —

- **Commits:** 8  |  **Período:** 2026-03-30 → 2026-04-24  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×5 🔴×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `b402230fc` | 2026-04-24 | Cross Back↔Front | Restore missing and broken file imports across the application — Restores 34 missing modules by locating their last known commit in git history and reintroducing the | `plataforma-lia/src/app/[locale]/funil-de-talentos/candidato/[id]/useCandidatePageCore.tsx`<br>`plataforma-lia/src/app/[locale]/jobs/[id]/JobDetailClient.tsx`<br>`plataforma-lia/src/components/chat/glossary-drawer.tsx` |
| 🟢 | `6d8e9fab3` | 2026-04-16 | Frontend (UI) | Add safeguards to prevent errors when insights data is not an array — Update the proactive insights hook to handle non-array responses from the backend by adding an Array | `plataforma-lia/src/app/api/backend-proxy/proactive-insights/route.ts` |
| 🔴 | `f7b3be109` | 2026-04-15 | Cross Back↔Front | fix: resolve default_languages column type mismatch (ARRAY→JSONB) — The company_culture_profiles.default_languages column is jsonb in the DB | `lia-agent-system/app/domains/company_culture/repositories/company_culture_repository.py`<br>`lia-agent-system/libs/models/lia_models/company_culture.py`<br>`plataforma-lia/src/app/api/backend-proxy/company/culture-profile/[companyId]/route.ts` |
| 🔴 | `b82c8f73f` | 2026-04-11 | Cross Back↔Front | Refactor hooks into domain-specific folders and generate API types — Reorganize all frontend hooks into 9 domain-specific folders, update hundreds of imports, and implem | `lia-agent-system/app/api/v1/agent_chat_sse.py`<br>`plataforma-lia/src/app/api/backend-proxy/candidates/analyze-match-all/sedwHxr6L`<br>`plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `03b582313` | 2026-04-10 | Frontend (api/util) | Add retry logic to candidate loading to prevent initial load errors — Implement automatic retry mechanism with exponential backoff for the `useCandidatesList` hook to han | `plataforma-lia/src/hooks/use-candidates-list.ts` |
| 🟢 | `a5574125a` | 2026-04-05 | Frontend (api/util) | Add a system to ensure chat messages are sent after login — Implement a reconnection mechanism to ensure WebSocket connections are established only after authen | `plataforma-lia/src/hooks/use-float-streaming.ts` |
| 🟢 | `e3ebd51f0` | 2026-03-30 | Frontend (api/util) | fix: normalize refetch type to Promise<void> in 4 admin hooks | `plataforma-lia/src/hooks/admin/useBiasAudits.ts`<br>`plataforma-lia/src/hooks/admin/useComplianceControls.ts`<br>`plataforma-lia/src/hooks/admin/useLGPDCompliance.ts` |
| 🟢 | `dcb0de375` | 2026-03-30 | Frontend (api/util) | fix: restore quotes in useBiasAudits and use-daily-briefing hooks — - useBiasAudits.ts: quoted imports (react, swr, @/services), SWR key, use client | `plataforma-lia/src/hooks/admin/useBiasAudits.ts`<br>`plataforma-lia/src/hooks/use-daily-briefing.ts` |

### Scheduling / Calendar (PR-CAL)

**Descrição:** PR-CAL: scheduling MVP — DB write real (não mais fake links), reschedule update, 14/14 tests. Microsoft Graph calendar integration via Teams (W9 multimídia).

**⚠️ Dependências para cherry-pick:** Microsoft Graph token | Calendar event id persistido | reschedule preserva event id

**Arquivos canônicos:** lia-agent-system/app/domains/scheduling/*, app/integrations/teams/calendar_*

**Docs de referência:** BRANCH_MAP — PR-CAL

- **Commits:** 8  |  **Período:** 2026-03-31 → 2026-04-28  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×6 🟢×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `3e1ae39c5` | 2026-04-28 | Backend | feat(pr-cal): scheduling MVP — DB write, no fake links, reschedule update, 14/14 tests — Wave 4 — PR-CAL: replace simulation stubs with DB-persisting MVP. | `lia-agent-system/app/domains/interview_scheduling/tools/scheduling_tools.py`<br>`lia-agent-system/tests/unit/domains/interview_scheduling/test_pr_cal_reschedule_interview.py`<br>`lia-agent-system/tests/unit/domains/interview_scheduling/test_pr_cal_schedule_interview.py` |
| 🟢 | `d4ad7aca1` | 2026-04-26 | Testes | Task #839 — cover the Scheduling stage with tests — The audit `audit-criacao-vaga-2026-04-26.md` (finding L-04) flagged that | `plataforma-lia/e2e/tests/wizard/step-scheduling.spec.ts`<br>`plataforma-lia/src/components/unified-chat/wizard/__tests__/WizardPublishedJobCard.test.tsx`<br>`plataforma-lia/src/components/unified-chat/wizard/panels/__tests__/SchedulingPanel.test.tsx` |
| 🟡 | `933949c9f` | 2026-04-20 | Cross IA↔Back | Fix mismatched scheduling-link database schema (Task #625) — The SelfSchedulingLink SQLAlchemy model targets the rich | `lia-agent-system/alembic/versions/096_align_self_scheduling_links_table.py`<br>`lia-agent-system/app/orchestrator/action_handlers/interview_actions.py` |
| 🟡 | `cdaa7b2c6` | 2026-04-20 | Backend | Wire real interview reminders and self-scheduling links (Task #598) — Replaces the two `simulation_stub` chat-tool wrappers in | `lia-agent-system/app/domains/interview_scheduling/services/scheduling_service.py` |
| 🟡 | `b67941448` | 2026-04-09 | Backend | Fix issues with creating agents and scheduling interviews — Update Pydantic schema for `is_synced_to_calendar` to accept None values and remove foreign key cons | `lia-agent-system/app/api/v1/scheduling.py`<br>`lia-agent-system/libs/models/lia_models/sourcing_agent.py` |
| 🟡 | `fbeacacdc` | 2026-04-06 | Backend | chore(guards): remove scheduling.py from PENDING_MIGRATION (now 143) | `lia-agent-system/scripts/check_no_sql_in_controllers.py` |
| 🟡 | `bbf5ea042` | 2026-04-06 | Backend | feat(phase2): migrate scheduling.py to SchedulingRepository | `lia-agent-system/app/api/v1/scheduling.py`<br>`lia-agent-system/app/domains/interview_scheduling/repositories/scheduling_repository.py` |
| 🟢 | `ef4698fa8` | 2026-03-31 | Frontend (UI) | Update the data structure for scheduling interviews — Introduce a new interface `ScheduledInterviewData` for structured storage of scheduled interview det | `plataforma-lia/src/components/ui/interview-scheduling-modal.tsx`<br>`plataforma-lia/src/components/wsi/wsi-voice-screening-status.tsx` |

### Task #113

- **Commits:** 8  |  **Período:** 2026-04-04 → 2026-04-10  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×5 🟡×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `091adc6ab` | 2026-04-10 | Frontend (UI) | Task #113: Backend Production Hardening — Deploy Blockers — Backend changes: | `plataforma-lia/src/app/api/backend-proxy/invitations/[...path]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/short-lists/[listId]/candidates/route.ts` |
| 🔴 | `6f75253d7` | 2026-04-10 | Cross Back↔Front | Task #113: Backend Production Hardening — Deploy Blockers — Changes made: | `lia-agent-system/alembic/versions/027_add_langgraph_native_checkpointer_tables.py`<br>`lia-agent-system/alembic/versions/033_merge_migration_heads.py`<br>`lia-agent-system/alembic/versions/058_create_tenant_llm_configs.py` |
| 🟢 | `22d7b3c46` | 2026-04-04 | Frontend (UI) | Task #113: Eliminate critical mock data from production code — CHANGES: | `plataforma-lia/src/components/onboarding/first-access-manager.tsx` |
| 🟢 | `15de7982f` | 2026-04-04 | Frontend (UI) | Task #113: Eliminate critical mock data from production code — CHANGES: | `plataforma-lia/src/components/onboarding/first-access-manager.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` |
| 🟢 | `56dc8a6ce` | 2026-04-04 | Frontend (UI) | Task #113: Eliminate critical mock data from production code — CHANGES: | `plataforma-lia/src/components/onboarding/first-access-manager.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` |
| 🟢 | `09d8cd0fb` | 2026-04-04 | Frontend (UI) | Task #113: Eliminate critical mock data from production code — CHANGES: | `plataforma-lia/src/components/kanban/utils/index.ts` |
| 🟡 | `957024c98` | 2026-04-04 | Frontend (UI) | Task #113: Eliminate critical mock data from production code — CHANGES: | `plataforma-lia/src/components/kanban/index.ts`<br>`plataforma-lia/src/components/kanban/utils/candidate-data-enrichment.ts`<br>`plataforma-lia/src/components/kanban/utils/index.ts` |
| 🟡 | `8cae7a14d` | 2026-04-04 | Frontend (UI) | Task #113: Eliminate critical mock data from production code — CHANGES: | `plataforma-lia/src/app/api/backend-proxy/analysis/file/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/search/similar/combine-profiles/route.ts`<br>`plataforma-lia/src/components/kanban/index.ts` |

### Task #13

- **Commits:** 8  |  **Período:** 2026-04-05 → 2026-04-05  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×4 🟢×3 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `e815712ce` | 2026-04-05 | Frontend (UI) | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — Components: | `plataforma-lia/src/app/api/auth/ws-token/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/agent-chat/sessions/active/route.ts`<br>`plataforma-lia/src/components/lia-float/LiaChatHeader.tsx` |
| 🟢 | `f96148e01` | 2026-04-05 | Frontend (UI) | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `plataforma-lia/src/app/api/auth/ws-token/route.ts` |
| 🟡 | `578d016cc` | 2026-04-05 | Backend | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/ws_manager.py` |
| 🔴 | `2278806b7` | 2026-04-05 | Cross Back↔Front | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `plataforma-lia/src/app/api/backend-proxy/agent-chat/sessions/active/route.ts` |
| 🔴 | `283441d37` | 2026-04-05 | Cross Back↔Front | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `plataforma-lia/src/components/lia-float/SwitchTaskModal.tsx` |
| 🟢 | `f867cf426` | 2026-04-05 | Frontend (UI) | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `plataforma-lia/src/components/lia-float/useLiaChatPanelState.ts` |
| 🔴 | `bb6a29bc0` | 2026-04-05 | Cross Back↔Front | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/ws_manager.py`<br>`plataforma-lia/src/components/lia-float/LiaChatHeader.tsx` |
| 🔴 | `239ec2f66` | 2026-04-05 | Cross Back↔Front | Task #13: Refinamento UX — Mode Labels, Switch Task, Background Agents — New components: | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/components/lia-float/BackgroundAgentsStatus.tsx`<br>`plataforma-lia/src/components/lia-float/BackgroundTaskNotification.tsx` |

### Task #149

- **Commits:** 8  |  **Período:** 2026-04-05 → 2026-04-11  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×4 🟡×2 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `843f0cd88` | 2026-04-11 | Testes | Task #149: Orchestrator Cleanup — Dead Code Removal + Refactor — Dead code removal: | `lia-agent-system/tests/unit/test_main_orchestrator_extended.py`<br>`lia-agent-system/tests/unit/test_sprint_i_foundations.py` |
| 🟡 | `a0067df13` | 2026-04-11 | IA | Task #149: Orchestrator Cleanup — Dead Code Removal + Refactor — Dead code removal: | `lia-agent-system/app/orchestrator/__init__.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/domain_mappings.py` |
| 🟡 | `c1f858b17` | 2026-04-11 | Cross IA↔Back | Task #149: Orchestrator Cleanup — Remove dead IntentRouter code — Changes: | `lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/intent_router.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |
| 🟢 | `acf741f03` | 2026-04-05 | Testes | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e tests — Scope: Only plataforma-lia frontend files (backend files in diff | `plataforma-lia/e2e/tests/search-prompt-ux.spec.ts` |
| 🔴 | `381379cdb` | 2026-04-05 | Cross IA↔Front | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e tests — Scope: Only plataforma-lia frontend files (backend files in diff | `lia-agent-system/app/services/__init__.py`<br>`lia-agent-system/app/services/agent_monitoring_service.py`<br>`lia-agent-system/app/services/apify_mcp_client.py` |
| 🔴 | `476849cd5` | 2026-04-05 | Cross IA↔Front | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e tests — Changes: | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/agent_monitoring.py`<br>`lia-agent-system/app/api/v1/alerts.py` |
| 🟢 | `af9ce154d` | 2026-04-05 | Frontend (UI) | Task #149: Fix search prompt UX - tooltip fonts, autocomplete repositioning, and Playwright e2e tests — Changes: | `plataforma-lia/src/components/expandable-ai-prompt/tabs/EAPTabNatural.tsx`<br>`plataforma-lia/src/components/search/ssi-modes/SSIModeNatural.tsx` |
| 🟢 | `a95e644a6` | 2026-04-05 | Frontend (UI) | Task #149: Fix search prompt UX - tooltip fonts and autocomplete overlay — Changes: | `plataforma-lia/src/components/expandable-ai-prompt/tabs/EAPTabNatural.tsx`<br>`plataforma-lia/src/components/search/ssi-modes/SSIModeNatural.tsx` |

### Task #45

- **Commits:** 8  |  **Período:** 2026-03-26 → 2026-04-06  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×8

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `55999add3` | 2026-04-06 | Frontend (UI) | Task #45: Redesign Chat Empty State (Carrossel + Layout Centralizado) — Changes made: | `plataforma-lia/src/app/styles/components.css`<br>`plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/ui/prompt-suggestions-dock.tsx` |
| 🟢 | `d1abb5bb7` | 2026-03-26 | Docs | Task #45: Fix all 3 code review issues in AI SDD docs — 1. BaseAgent interface (AI_ARCHITECTURE.md §10.2): Fixed from | `docs/specs/ai/AI_ARCHITECTURE.md`<br>`docs/specs/ai/LLM_DECISIONS.md` |
| 🟢 | `7db459b68` | 2026-03-26 | Docs | Task #45: AI SDD docs — all tools/tasks verified from actual code — All 3 AI spec documents corrected from actual source files: | `docs/specs/ai/AGENT_SPECS.md`<br>`docs/specs/ai/AI_ARCHITECTURE.md` |
| 🟢 | `bb40ce771` | 2026-03-26 | Docs | Task #45: AI SDD docs — tool lists verified from actual registries — All 3 AI spec documents corrected with tool counts and names extracted | `docs/specs/ai/AGENT_SPECS.md` |
| 🟢 | `be405c235` | 2026-03-26 | Docs | Task #45: AI SDD docs — all tool counts verified from actual registries — All 3 AI spec documents corrected with tool counts and names extracted | `docs/specs/ai/AGENT_SPECS.md`<br>`docs/specs/ai/AI_ARCHITECTURE.md` |
| 🟢 | `b4e2ed7fb` | 2026-03-26 | Docs | Task #45: Enrich AI SDD docs — code-verified from actual source files — All 3 AI spec documents rewritten with lia-agent-system enrichment, | `docs/specs/ai/AI_ARCHITECTURE.md`<br>`docs/specs/ai/LLM_DECISIONS.md` |
| 🟢 | `b49864347` | 2026-03-26 | Docs | Task #45: Enrich AI SDD docs with full lia-agent-system coverage — All 3 AI spec documents rewritten with comprehensive lia-agent-system enrichment | `docs/specs/ai/AGENT_SPECS.md`<br>`docs/specs/ai/AI_ARCHITECTURE.md`<br>`docs/specs/ai/LLM_DECISIONS.md` |
| 🟢 | `8dd98df85` | 2026-03-26 | Docs | Task #45: Enrich AI SDD docs with full lia-agent-system coverage — All 3 AI spec documents rewritten with comprehensive lia-agent-system enrichment: | `docs/specs/ai/AGENT_SPECS.md`<br>`docs/specs/ai/AI_ARCHITECTURE.md`<br>`docs/specs/ai/LLM_DECISIONS.md` |

### Task #50

- **Commits:** 8  |  **Período:** 2026-03-26 → 2026-04-06  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×5 🟡×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `0d1660296` | 2026-04-06 | Testes | Task #50: Frontend component tests for critical flows — Added/extended 13 test files with 130+ new tests covering stores, components, | `plataforma-lia/src/components/job-wizard/__tests__/WizardContainer.test.tsx`<br>`plataforma-lia/src/components/job-wizard/__tests__/useWizardNavigation.test.tsx`<br>`plataforma-lia/src/stores/__tests__/kanban-store.test.ts` |
| 🟡 | `d25359132` | 2026-04-06 | Frontend (UI) | Task #50: Frontend component tests for critical flows — Added/extended 13 test files with 130+ new tests covering stores, components, hooks, and utility fun | `plataforma-lia/src/app/api/ai/extract-archetype-info/route.ts`<br>`plataforma-lia/src/app/api/ai/suggest-companies/route.ts`<br>`plataforma-lia/src/app/api/ai/suggest-expertise/route.ts` |
| 🟡 | `9dd1a357d` | 2026-04-06 | Frontend (UI) | Task #50: Frontend component tests for critical flows — Added 11 new test files covering 4 Zustand stores and 7 UI components/hooks: | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx`<br>`plataforma-lia/src/components/autonomous/proactive-actions-bell.tsx`<br>`plataforma-lia/src/components/expandable-ai-prompt/useArchetypeHandlers.ts` |
| 🟢 | `ce2b14b4b` | 2026-04-06 | Frontend (UI) | Task #50: Frontend component tests for critical flows — Added 10 new test files covering 4 Zustand stores and 6 UI components/hooks: | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearch.ts` |
| 🟡 | `5507f8e3f` | 2026-04-06 | Frontend (UI) | Task #50: Frontend component tests for critical flows — Added 7 new test files covering 4 Zustand stores and 3 UI components: | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearch.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesSearchComposition.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesViewComposition.tsx` |
| 🟢 | `d3ee0f9de` | 2026-03-26 | Docs | Task #50: SDD Semana 3 — QA + AI_QA + GOLDEN_DATASET + CONTRIBUTING + ONBOARDING + SPEC_TEMPLATE — Created 6 new SDD spec documents (1700 lines total): | `docs/specs/process/ONBOARDING.md`<br>`docs/specs/qa/QA_PROTOCOL.md` |
| 🟢 | `5462f8b81` | 2026-03-26 | Docs | Task #50: SDD Semana 3 — QA + AI_QA + GOLDEN_DATASET + CONTRIBUTING + ONBOARDING + SPEC_TEMPLATE — Created 6 new SDD spec documents (1700 lines total): | `docs/specs/process/ONBOARDING.md`<br>`docs/specs/qa/AI_QA_PROTOCOL.md` |
| 🟢 | `ebbcac880` | 2026-03-26 | Docs | Task #50: SDD Semana 3 — QA + AI_QA + GOLDEN_DATASET + CONTRIBUTING + ONBOARDING + SPEC_TEMPLATE — Created 6 new SDD spec documents (1700 lines total): | `docs/PLATFORM_MAP.md`<br>`docs/specs/process/CONTRIBUTING.md`<br>`docs/specs/process/ONBOARDING.md` |

### Task #65

- **Commits:** 8  |  **Período:** 2026-03-30 → 2026-03-30  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×7 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `f190521b4` | 2026-03-30 | Empty/merge | Task #65: Alpha 1 Roadmap Analysis v2.0 + fix 14 broken hook files — 1. docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md updated to v2.0: | — |
| 🟢 | `da1c44e1a` | 2026-03-30 | Frontend (api/util) | Task #65: Alpha 1 Roadmap Analysis v2.0 + fix 12 broken hook files — 1. docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md updated to v2.0: | `plataforma-lia/src/hooks/admin/useDefaultTemplates.ts` |
| 🟢 | `1f0a05e88` | 2026-03-30 | Empty/merge | Task #65: Alpha 1 Roadmap Analysis v2.0 + fix 11 broken hook files — 1. docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md updated to v2.0: | — |
| 🟡 | `fe7db741f` | 2026-03-30 | Frontend (api/util) | Task #65: Mapa Completo Alpha 1 v2.0 + fix 8 broken hook files — 1. docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md updated to v2.0: | `plataforma-lia/src/hooks/admin/useComplianceControls.ts`<br>`plataforma-lia/src/hooks/admin/useLGPDCompliance.ts`<br>`plataforma-lia/src/hooks/use-ai-credits.ts` |
| 🟢 | `05b01eb4d` | 2026-03-30 | Empty/merge | Task #65: Mapa Completo Alpha 1 v2.0 + fix 8 broken hook files — 1. docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md updated to v2.0: | — |
| 🟢 | `1440e7af9` | 2026-03-30 | Frontend (UI) | Task #65: Mapa Completo Alpha 1 v2.0 + fix 6 broken hook files — 1. docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md updated to v2.0: | `plataforma-lia/src/components/search/hooks/index.ts`<br>`plataforma-lia/src/components/search/hooks/useSmartSearchArchetypes.ts`<br>`plataforma-lia/src/components/search/hooks/useSmartSearchCore.tsx` |
| 🟢 | `ca1df97df` | 2026-03-30 | Frontend (api/util) | Task #65: Mapa Completo Alpha 1 v2.0 + hook syntax fixes — 1. Updated docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md to v2.0: | `plataforma-lia/src/hooks/admin/useClientSaasMetrics.ts`<br>`plataforma-lia/src/hooks/use-proactive-insights.ts` |
| 🟢 | `df55016bf` | 2026-03-30 | Frontend (api/util) | Task #65: Mapa Completo Alpha 1 v2.0 — Agentes, Camadas e Arquitetura — Updated docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md from v1 (386 lines) | `plataforma-lia/src/hooks/admin/useDashboardSummary.ts`<br>`plataforma-lia/src/hooks/admin/usePlatformMetrics.ts`<br>`plataforma-lia/src/hooks/use-ai-credits.ts` |

### UX / Mockups

- **Commits:** 8  |  **Período:** 2026-04-07 → 2026-04-20  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×4 🟡×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `019c35c9a` | 2026-04-20 | Testes | Update mockups and agent test configurations — Update mock component imports and agentic evaluation launch options. | `plataforma-lia/e2e/tests/agentic-eval/agentic.config.ts` |
| 🟡 | `6535f4cd1` | 2026-04-19 | Backend | Add end-to-end tests for job listings and update mockups — Adds new E2E tests for the `/vagas` endpoint, covering preview and drag-and-drop functionality, and  | `lia-agent-system/eval/eval_results_20260419_142913.json` |
| 🟡 | `91dae132c` | 2026-04-18 | Backend | Add new mockups and update evaluation results for job listings — Update mockup component registration and add new evaluation results for job listing functionalities. | `lia-agent-system/eval/eval_results_20260418_152130.json` |
| 🟡 | `1b4bd3bd0` | 2026-04-18 | IA | Update analytics to use company IDs and add new mockup components — Modify SQL queries in analytics_actions.py to correctly handle company_id type casting and update mo | `lia-agent-system/app/orchestrator/action_handlers/analytics_actions.py` |
| 🟢 | `f7d27ce7f` | 2026-04-17 | Empty/merge | Add Eleven Labs funnel mockup to the component registry — Update mockup-components.ts to include the FunnelElevenLabs component. | — |
| 🟢 | `dd8b800ee` | 2026-04-17 | Frontend (UI) | Add test identifiers and update component imports for mockups — Add `data-testid` and `data-stage-id` attributes to Kanban columns and reorder mock component import | `plataforma-lia/src/components/pages/job-kanban/KanbanColumnRenderer.tsx` |
| 🟢 | `34eba75bf` | 2026-04-09 | Frontend (api/util) | Add a new component for ElevenLabs funnel to the mockup sandbox — Update `mockup-components.ts` to include the `FunilElevenLabs.tsx` component. | `plataforma-lia/package-lock.json` |
| 🟡 | `534419a82` | 2026-04-07 | Backend | Remove unused chat layout mockups and update job vacancy configurations — Removes various chat layout mockups from the sandbox and updates the job vacancy API to include a ne | `lia-agent-system/app/api/v1/candidates/_shared.py`<br>`lia-agent-system/app/api/v1/job_vacancies/__init__.py`<br>`lia-agent-system/app/api/v1/recruitment_stages_new/_shared.py` |

### scope: studio

- **Commits:** 8  |  **Período:** 2026-04-12 → 2026-04-13  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×4 🟡×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `78b62cdaf` | 2026-04-13 | Cross Back↔Front | feat(studio): P2.5b — External Webhooks for Studio events — Allows clients to subscribe to Studio events and receive HTTP POSTs | `lia-agent-system/alembic/versions/074_webhooks.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_approvals.py` |
| 🟡 | `7d867df94` | 2026-04-13 | Backend | feat(studio): P2.5a — Internal Notifications for Studio events — Reuses existing notification_service (libs/messaging) — no new infra. | `lia-agent-system/app/api/v1/agent_approvals.py`<br>`lia-agent-system/app/api/v1/agent_deployments.py`<br>`lia-agent-system/app/api/v1/custom_agents.py` |
| 🔴 | `81d3e2e2f` | 2026-04-13 | Cross Back↔Front | feat(studio): P2.2 — Version History for Custom Agents — Every PATCH to a custom agent now creates an automatic snapshot of the | `lia-agent-system/alembic/versions/073_agent_version_snapshots.py`<br>`lia-agent-system/app/api/v1/custom_agents.py`<br>`lia-agent-system/app/models/agent_version_snapshot.py` |
| 🟡 | `5cc3cfcbd` | 2026-04-13 | Cross IA↔Back | feat(studio): RAG search + RESTRICTED tools audit — - Add rag_search ToolDefinition to AUTONOMOUS_TOOL_POOL | `lia-agent-system/app/tools/tool_permissions.yaml`<br>`lia-agent-system/app/tools/tool_permissions_loader.py` |
| 🔴 | `93bfd694d` | 2026-04-13 | Cross Back↔Front | feat(studio): P2.1 — Approval Workflow — Flow: draft → request → pending_approval → review → approved (active) / rejected (draft) | `lia-agent-system/alembic/versions/072_agent_approvals.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_approvals.py` |
| 🔴 | `0b6f0fdc1` | 2026-04-13 | Cross Back↔Front | feat(studio): Complete remaining Sprint 3-5 + P2 items — Sprint 3: ToolSelector checkbox grid (replaces text input for tools) | `lia-agent-system/app/api/v1/custom_agents.py`<br>`plataforma-lia/src/components/pages-agent-studio/MarketplaceTab.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/AgentDetailsPanel.tsx` |
| 🟡 | `79c4bdb6e` | 2026-04-13 | Backend | feat(studio): Sprint 0 — AgentDeployment binds agents to jobs/pools/stages — Agents without a deployment are drafts. AgentDeployment connects Studio | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_deployments.py`<br>`lia-agent-system/app/models/agent_deployment.py` |
| 🟡 | `fd1c84a88` | 2026-04-12 | Backend | feat(studio): Etapa 3 — context_level + Prompt Preview + RAG smoke — context_level routing in _get_system_prompt(): | `lia-agent-system/app/api/v1/custom_agents.py` |

### scope: tokens

- **Commits:** 8  |  **Período:** 2026-04-01 → 2026-04-01  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×8

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `c21a36ca0` | 2026-04-01 | Frontend (UI) | fix(tokens): phase 4 residual — badge tokens audit + onboarding CSS + final hex sweep — - status-badge.tsx: auditado — todos --badge-* tokens usam CSS vars dinamicas | `plataforma-lia/src/components/onboarding/onboarding-styles.css` |
| 🟢 | `389cd1774` | 2026-04-01 | Frontend (UI) | fix(tokens): tasks-page + AlertsTab — inline styles to tokens | `plataforma-lia/src/components/pages/tasks-page.tsx`<br>`plataforma-lia/src/components/settings/communication-hub/AlertsTab.tsx` |
| 🟢 | `d2a095e08` | 2026-04-01 | Frontend (UI) | fix(tokens): strategic-dashboard + search-preview-card + useChatSession — remove hex fallbacks | `plataforma-lia/src/components/dashboard/strategic-dashboard.tsx` |
| 🟢 | `b67cea7a4` | 2026-04-01 | Frontend (UI) | fix(tokens): task-helpers.tsx - convert inline styles to Tailwind classes | `plataforma-lia/src/components/pages/task-helpers.tsx` |
| 🟢 | `00aa40b26` | 2026-04-01 | Frontend (UI) | fix(tokens): fix var(--lia-) truncated bug + add --chat-cyan alias + add --gray-700 | `plataforma-lia/src/components/ui-actions/panels/BehavioralCompetenciesPanel.tsx` |
| 🟢 | `f52f5ee31` | 2026-04-01 | Frontend (UI) | fix(tokens): replace hardcoded hex in animations.css + components.css with CSS vars | `plataforma-lia/src/app/styles/animations.css`<br>`plataforma-lia/src/app/styles/components.css` |
| 🟢 | `d4b664af3` | 2026-04-01 | Frontend (api/util) | fix(tokens): add wedo-amber-light/green-light to tailwind + remove @ts-nocheck | `plataforma-lia/tailwind.config.ts` |
| 🟢 | `01ae871c0` | 2026-04-01 | Frontend (api/util) | fix(tokens): add --lia-text-inverted alias + verify dark mode coverage | `plataforma-lia/src/styles/design-tokens.css` |

### §13 PARTE D — Proatividade

**Descrição:** Proatividade: lia:proactive-action event + router completo + dismiss + sessionStorage anti-repeat. ProactiveHint dataclass com type/message/severity/action/metadata. Frontend escuta e renderiza cards clicáveis.

**⚠️ Dependências para cherry-pick:** proactive_hints serializado em chat_event_serializer | use-proactive-action-router hook | accept-hint endpoint backend | dismiss UI

**Arquivos canônicos:** lia-agent-system/app/orchestrator/precondition_checker.py, plataforma-lia/src/hooks/chat/useProactiveActionRouter.ts

**Docs de referência:** DEVELOPER_HANDOFF.md PARTE E

- **Commits:** 8  |  **Período:** 2026-03-30 → 2026-04-28  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×5 🟢×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `fd573e867` | 2026-04-28 | Docs | docs(handoff): add comprehensive PT-BR handoff for LIA's proactive AI layer — Task #911 — single exhaustive markdown handoff in PT-BR at | `lia-agent-system/docs/handoff/camada-ia-proativa-lia.md` |
| 🟡 | `85eb169fa` | 2026-04-25 | IA | fix(orchestrator): respeitar severity + intent em ProactiveHints (task #811) — ## Original | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `a1fbb30c6` | 2026-04-25 | Cross IA↔Back | fix(orchestrator): respeitar severity + intent em ProactiveHints (task #811) — ## Original | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `324aa2acd` | 2026-04-25 | IA | fix(orchestrator): respeitar severity de ProactiveHints (task #811) — ## Original | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `7ef32d4f4` | 2026-04-25 | IA | fix(orchestrator): respeitar severity de ProactiveHints (task #811) — ## Original | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `f0df08ffc` | 2026-04-17 | Cross IA↔Back | fix(lia): Wave A+B — tenant alias, scope routing, proactive tools — A1: tenant.py — added '37' and staging UUID to DEMO_COMPANY_LEGACY_ALIASES | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py` |
| 🟢 | `3f28fb03d` | 2026-03-31 | Testes | test: adiciona testes para use-current-company e use-proactive-insights (SWR) | `plataforma-lia/src/hooks/__tests__/use-current-company.test.ts`<br>`plataforma-lia/src/hooks/__tests__/use-proactive-insights.test.ts` |
| 🟢 | `6a4dcf126` | 2026-03-30 | Frontend (api/util) | fix: restore quotes in useClientSaasMetrics and use-proactive-insights hooks — - useClientSaasMetrics.ts: quoted imports, SWR keys, use client directive | `plataforma-lia/src/hooks/admin/useClientSaasMetrics.ts`<br>`plataforma-lia/src/hooks/use-proactive-insights.ts` |

### Agent Studio (FE)

**Descrição:** Agent Studio — pages-agent-studio. Inclui pages para visualizar/configurar agentes IA.

**⚠️ Dependências para cherry-pick:** Endpoint /api/v1/agent_studio | RBAC admin

**Arquivos canônicos:** plataforma-lia/src/components/pages-agent-studio/**

**Docs de referência:** —

- **Commits:** 7  |  **Período:** 2026-04-09 → 2026-04-15  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×6 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `c8de45ef7` | 2026-04-15 | Frontend (UI) | Update digital twin page translations and visual styling — Correct translation namespaces in DigitalTwinComponents.tsx and align its UI elements, including the | `plataforma-lia/src/components/pages-agent-studio/DigitalTwinComponents.tsx` |
| 🟡 | `ef68e2edd` | 2026-04-13 | Frontend (UI) | Update 'Sourcing' labels to 'Captação' across the platform for consistency — Replaces all instances of "Sourcing" with "Captação" in UI labels, component props, and type definit | `plataforma-lia/src/components/chat/plan-progress-card.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/MarketplaceTab.tsx`<br>`plataforma-lia/src/components/pages-agent-studio/custom-agents/types.ts` |
| 🟢 | `f0276ae18` | 2026-04-12 | Frontend (UI) | Fix deploy: remove broken void(), clean ESLint errors (3/3 resolved) | `plataforma-lia/src/components/pages-agent-studio/MultiStrategySearchPanel.tsx` |
| 🟢 | `ec01ea69b` | 2026-04-12 | Frontend (UI) | Fix deploy: AlertCircle import, unused expression | `plataforma-lia/src/components/pages-agent-studio/MultiStrategySearchPanel.tsx`<br>`plataforma-lia/src/components/search/filter-sections/FilterSectionOpcoes.tsx` |
| 🟢 | `045767162` | 2026-04-11 | Frontend (UI) | Final cleanup: 14 secondary0 typos, 1 gray class, zero remaining | `plataforma-lia/src/components/pages-agent-studio/CustomAgentsTab.tsx` |
| 🟢 | `95b3fb6ef` | 2026-04-09 | Frontend (UI) | Update Agent Studio to use brain icons and remove unnecessary wrappers — Replaced Sparkles icons with Brain icons, removed gradient background wrappers around Brain icons in | `plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx` |
| 🟢 | `41efa41a5` | 2026-04-09 | Frontend (UI) | Update the Agent Studio page with a modern, intuitive, and sophisticated design — Redesign the Agent Studio page with a new header, metric bar, tabbed navigation, guided setup flow,  | `plataforma-lia/src/components/pages-agent-studio/AgentStudioPage.tsx` |

### Docs / Configuration

**Descrição:** Documentação de configuração e deploy — DEPLOY_GUIDE, GCP_INFRASTRUCTURE_CHECKLIST, .env.example, Langfuse decision, env vars.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** DEPLOY_GUIDE.md, GCP_INFRASTRUCTURE_CHECKLIST.md, lia-agent-system/.env.example, plataforma-lia/.env.example

**Docs de referência:** DEPLOY_GUIDE.md

- **Commits:** 7  |  **Período:** 2026-04-07 → 2026-04-14  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×6 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `4c79c511f` | 2026-04-14 | Backend | docs: document staging Rails API URL in .env.example [PX08-007] — Staging URL: https://staging2.wedotalent.cc | `lia-agent-system/.env.example` |
| 🟢 | `9787e738c` | 2026-04-10 | Frontend (api/util) | Update documentation with correct environment variable names — Update VALIDATION_PLAN.md and DEPLOY_GUIDE.md to reference correct environment variable names and ad | `plataforma-lia/5120` |
| 🟢 | `72b810898` | 2026-04-10 | Docs | Update AI agent domain counts to reflect current scope — Normalize the number of business domains from 53 to 58 across multiple sections in DEPLOY_GUIDE.md,  | `DEPLOY_GUIDE.md` |
| 🟢 | `29d23937d` | 2026-04-09 | Docs | Update production readiness audit with comparative analysis and new structure — Refactors section 24 of DEPLOY_GUIDE.md, restructuring the production readiness audit into a compara | `DEPLOY_GUIDE.md` |
| 🟢 | `385dd7c8e` | 2026-04-07 | Docs | Expand product development workflow to include client feedback and bug fixes — Adds a comprehensive product development cycle diagram, detailed QA and hotfix processes, and a clie | `DEPLOY_GUIDE.md` |
| 🟢 | `cd4710d07` | 2026-04-07 | Docs | Update deployment guide with current environment and limitations — Modify DEPLOY_GUIDE.md to reflect the existence of a staging environment, clarify deployment status, | `DEPLOY_GUIDE.md` |
| 🟢 | `fd2ca73f2` | 2026-04-07 | Docs | Clarify team ownership of development flow and environment — Update DEPLOY_GUIDE.md to redefine roles in development flow, emphasizing team ownership of the cent | `DEPLOY_GUIDE.md` |

### Docs / WeDO planos

**Descrição:** Planos e análises da pasta WeDO/.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** WeDO/**

**Docs de referência:** —

- **Commits:** 7  |  **Período:** 2026-03-26 → 2026-04-02  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×7

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `2262da5b5` | 2026-04-02 | Docs | Update project inventory to reflect actual codebase structure — Create a new audit file detailing discrepancies between the project's codebase and its documentation | `WeDO/REPLIT_VS_INVENTORY_AUDIT.md` |
| 🟢 | `6eec07914` | 2026-04-02 | Docs | Update inventory document with accurate component counts and paths — Corrected UI component count in metadata, updated file paths in screening sections, and refined desc | `WeDO/PRODUCT_DESIGN_INVENTORY.md` |
| 🟢 | `43f903c58` | 2026-04-01 | Docs | Update migration guide to reflect new version and refined estimates — Refactors the migration guide document, updating the version to 2.2, refining time estimates for Cam | `WeDO/guias/GUIA_MIGRACAO_V5_COMPLIANCE.md` |
| 🟢 | `64c5e9f69` | 2026-04-01 | Docs | Improve document structure and fix formatting errors — Update document version to 2.0 and restructure sections for better readability, including fixing dou | `WeDO/guias/GUIA_MIGRACAO_V5_COMPLIANCE.md` |
| 🟢 | `99d6a115b` | 2026-04-01 | Docs | Add detailed routing and domain inventory analysis for LIA and v5 — Updates the migration guide to include new sections detailing the routing mechanisms of v5 and LIA,  | `WeDO/guias/GUIA_MIGRACAO_V5_COMPLIANCE.md` |
| 🟢 | `f746e4307` | 2026-03-31 | Frontend (UI) | Add executive diagnosis of current structural problems in the system — Add a new "Executive Diagnosis" section to the documentation detailing 7 structural problems. | `plataforma-lia/src/components/pages/job-kanban/KanbanTableView.tsx` |
| 🟢 | `dcddfa39c` | 2026-03-26 | Docs | Organize project documentation and working files — Moves working documents and analyses to a dedicated 'WeDO' directory, while keeping core product and | `WeDO/analises/ANALISE_COMPARATIVA_V5_vs_LIA.md`<br>`WeDO/analises/AUDITORIA-FUNCIONALIDADES.md`<br>`WeDO/analises/Paralelo_LIA_vs_V5_Arquitetura_IA.md` |

### Fase 2

- **Commits:** 7  |  **Período:** 2026-03-27 → 2026-04-11  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×4 🔴×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `4c57fff89` | 2026-04-11 | Backend | Task #126: Fase 2 — Semantic Chunking para RAG (Section-Aware + Semantic) — Implemented three chunking strategies for RAG document processing: | `lia-agent-system/app/shared/intelligence/chunking/__init__.py`<br>`lia-agent-system/app/shared/intelligence/chunking/base.py`<br>`lia-agent-system/app/shared/intelligence/chunking/factory.py` |
| 🔴 | `71095fbac` | 2026-04-11 | Cross IA↔Front | Fase 2 — HITL Badge de Aprovações Pendentes no Header (Task #125) — Backend: | `lia-agent-system/app/api/v1/hitl.py`<br>`lia-agent-system/app/services/hitl_service.py`<br>`plataforma-lia/src/app/api/backend-proxy/hitl/pending/route.ts` |
| 🟡 | `6efc60dc5` | 2026-03-28 | Frontend (UI) | Fase 2 — Tokenização hex hardcoded: 24 substituições em 13 arquivos — Novos tokens criados: whatsapp-bg, whatsapp-bubble, whatsapp-green, wedo-blue, --login-bg-gradient | `plataforma-lia/src/components/job-wizard/stages/ReviewPublishStage.tsx`<br>`plataforma-lia/src/components/job-wizard/stages/WSIQuestionsStage.tsx`<br>`plataforma-lia/src/components/login-page.tsx` |
| 🟡 | `5e47dcaf0` | 2026-03-28 | Frontend (UI) | Fase 2 residual — Tokenização parcial: tailwind.config + 5 componentes — tailwind.config.ts: novos tokens adicionados | `plataforma-lia/src/components/lia-metrics-dashboard.tsx`<br>`plataforma-lia/src/components/modals/share-search-modal.tsx`<br>`plataforma-lia/src/components/modals/unified-communication-modal.tsx` |
| 🟡 | `fa7c73c64` | 2026-03-27 | Frontend (UI) | Fase 2 residual — Tokenização cyan nativo → wedo-cyan (15 arquivos, 81 substituições) | `plataforma-lia/src/app/admin/configuracoes/comunicacoes/components/constants.ts`<br>`plataforma-lia/src/components/ai/agent-explainability-panel.tsx`<br>`plataforma-lia/src/components/chat/action-result-card.tsx` |
| 🔴 | `e1ab7b604` | 2026-03-27 | Frontend (UI) | Fase 2 — Gaps Finais: gray scale completo + pipeline 100% tokenizado — - Adiciona --gray-300 e --gray-500 ao design-tokens.css (escala 8 stops) | `plataforma-lia/src/app/admin/clientes/[clientId]/faturamento/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/jornada/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/controles/cobertura/page.tsx` |
| 🔴 | `43e78bdd6` | 2026-03-27 | Frontend (UI) | Fase 2 — Tokenização de Cores com Direção Monocromática — Reduz 150+ hex hardcoded para ~15 tokens semânticos. Transição completa | `plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/controles/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/faturamento/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/jornada/page.tsx` |

### LIA Float UI (FE)

**Descrição:** LIA Float — botão flutuante / dock lateral / bottom-dock que abre o chat.

**⚠️ Dependências para cherry-pick:** UnifiedChat montado | event listeners globais

**Arquivos canônicos:** plataforma-lia/src/components/lia-float/**

**Docs de referência:** —

- **Commits:** 7  |  **Período:** 2026-03-22 → 2026-04-25  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×6 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `6f5d765ca` | 2026-04-25 | Testes | Improve test reliability by mocking external requests — Mock the fetch API call within the LiaChatPanel tests to prevent errors and ensure consistent test e | `plataforma-lia/src/components/lia-float/__tests__/LiaChatPanel-p2c.test.tsx` |
| 🟢 | `de2479e46` | 2026-04-06 | Frontend (UI) | Prevent floating chat from overlapping with inline chats and restore chat page — Introduce a `hasInlineChat` flag to the chat context, managed by a ref-based counter, to conditional | `plataforma-lia/src/components/lia-float/LiaChatShell.tsx`<br>`plataforma-lia/src/components/lia-float/LiaFloatConditional.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx` |
| 🔴 | `95ad2730a` | 2026-04-05 | Cross Back↔Front | Add multi-step plan execution with real-time progress tracking — Integrate plan detection and execution into the WebSocket handler, enabling multi-step workflows wit | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/api/v1/teams.py` |
| 🟢 | `93326741e` | 2026-04-04 | Frontend (UI) | Add quick start suggestions to the chat panel interface — Adds a `handleChipSend` callback and modifies the `EmptyState` component to fetch and display contex | `plataforma-lia/src/components/lia-float/LiaChatPanel.tsx` |
| 🟢 | `8ad51ef02` | 2026-03-26 | Frontend (UI) | Standardize floating LIA chat formatting to match main chat style — - Created lib/chat-format.ts with cleanAgentResponse() to strip raw | `plataforma-lia/src/components/lia-float/LiaChatPanel.tsx`<br>`plataforma-lia/src/components/lia-float/LiaSuperPrompt.tsx` |
| 🟢 | `7b7e0e9e3` | 2026-03-26 | Frontend (UI) | Standardize floating LIA chat to match job creation prompt style — Problem: Floating LIA chat was showing raw JSON from agent responses | `plataforma-lia/src/components/lia-float/LiaChatPanel.tsx`<br>`plataforma-lia/src/components/lia-float/LiaSuperPrompt.tsx` |
| 🟢 | `5e86c18e7` | 2026-03-22 | Frontend (UI) | Hide LIA chat elements from login and password reset pages — Conditionally render LiaChatButton, LiaChatPanel, and LiaSuperPrompt components based on the current | `plataforma-lia/src/app/layout.tsx`<br>`plataforma-lia/src/components/lia-float/LiaFloatConditional.tsx` |

### Search (FE)

**Descrição:** Componentes de busca — search bars, filtros, hooks de search, filter sections.

**⚠️ Dependências para cherry-pick:** Endpoints de search (candidates, jobs)

**Arquivos canônicos:** plataforma-lia/src/components/search/**

**Docs de referência:** —

- **Commits:** 7  |  **Período:** 2026-03-30 → 2026-04-12  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×5 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `13525f9c2` | 2026-04-12 | Frontend (UI) | Remove duplicate icon import in filter section options — Remove a duplicate import of the AlertCircle icon from the lucide-react library in the FilterSection | `plataforma-lia/src/components/search/filter-sections/FilterSectionOpcoes.tsx` |
| 🟢 | `bd6c8ebbf` | 2026-04-03 | Frontend (UI) | Update search input focus style to use a neutral outline — Modify the focus style of the search input component to use a subtle grey shadow instead of a cyan o | `plataforma-lia/src/components/search/ssi-modes/SSIModeNatural.tsx` |
| 🟢 | `dfccecc1f` | 2026-04-03 | Frontend (UI) | Update search interface to use rounded corners and bordered styles — Adjusted search input tabs, entity tags, and buttons to use `rounded-lg` and bordered styling, align | `plataforma-lia/src/components/search/smart-search-input.tsx`<br>`plataforma-lia/src/components/search/ssi-modes/SSIModeNatural.tsx` |
| 🟡 | `cc4a95dba` | 2026-04-02 | Frontend (UI) | Unify search preset modals into a single generic component — Consolidates Company, Location, and University preset modals into a single, configurable SearchPrese | `plataforma-lia/src/components/search/CompanyPresetsModal.tsx`<br>`plataforma-lia/src/components/search/LocationPresetsModal.tsx`<br>`plataforma-lia/src/components/search/SearchPresetsModal.tsx` |
| 🟢 | `40a3ea3e5` | 2026-04-02 | Frontend (UI) | Fix runtime errors to allow the platform to run correctly — Correct an import statement issue in CompanyHQLocationsInput.tsx and resolve an empty animationDelay | `plataforma-lia/src/components/search/CompanyHQLocationsInput.tsx`<br>`plataforma-lia/src/components/ui/thinking-dots.tsx` |
| 🟢 | `4141edfec` | 2026-03-31 | Frontend (UI) | Add new search modes and improve existing ones for better user experience — Introduces SSIModeBoolean, SSIModeJobDescription, and SSIModeNatural components for enhanced search  | `plataforma-lia/src/components/search/SSIModeContent.tsx`<br>`plataforma-lia/src/components/search/ssi-modes/SSIModeBoolean.tsx`<br>`plataforma-lia/src/components/search/ssi-modes/SSIModeJobDescription.tsx` |
| 🟡 | `163099045` | 2026-03-30 | Frontend (UI) | Update audit scores and refine search filters for improved candidate matching — Update frontend audit scores and adjust various search filter components to enhance user experience  | `plataforma-lia/src/components/search/filter-sections/FilterSectionFormacao.tsx`<br>`plataforma-lia/src/components/search/filter-sections/FilterSectionGeral.tsx`<br>`plataforma-lia/src/components/search/filter-sections/FilterSectionHabilidades.tsx` |

### Task #41

- **Commits:** 7  |  **Período:** 2026-03-25 → 2026-04-06  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×5 🟢×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `fbf45c9f6` | 2026-04-06 | Backend | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Created centralized interview_stage_defaults.py module as single source of truth: | `lia-agent-system/app/domains/job_management/services/interview_stage_defaults.py`<br>`lia-agent-system/app/domains/job_management/services/jd_template_service.py`<br>`lia-agent-system/app/domains/job_management/services/job_vacancy_service.py` |
| 🟡 | `16d9df8f5` | 2026-04-06 | Backend | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Two integration points modified: | `lia-agent-system/app/domains/job_management/services/jd_template_service.py`<br>`lia-agent-system/app/domains/job_management/services/job_vacancy_service.py` |
| 🟡 | `430f24c9c` | 2026-04-06 | Backend | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Two integration points modified: | `lia-agent-system/app/domains/job_management/services/jd_template_service.py`<br>`lia-agent-system/app/domains/job_management/services/job_vacancy_service.py` |
| 🟡 | `bf58a9a2e` | 2026-04-06 | Backend | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Two integration points modified: | `lia-agent-system/app/domains/job_management/services/jd_template_service.py`<br>`lia-agent-system/app/domains/job_management/services/job_vacancy_service.py` |
| 🟡 | `c498ea242` | 2026-04-06 | Backend | Task #41: Load company pipeline stages for interview flow instead of hardcoded defaults — Modified jd_template_service.py to load interview stages from the company's | `lia-agent-system/app/domains/job_management/services/jd_template_service.py` |
| 🟢 | `a1950e09c` | 2026-03-25 | Frontend (UI) | Task #41: Fix copy feedback button + remove dead ranking code — - Fixed field name: uses response_analyses (matching F11 API) not analyses | `plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🟢 | `99fe4c711` | 2026-03-25 | Frontend (UI) | Task #41: Fix copy feedback button to use F11 response_analyses data — - Fixed field name mismatch: uses response_analyses (not analyses) matching F11 API | `plataforma-lia/src/components/triagem-details-modal.tsx` |

### Task #47

- **Commits:** 7  |  **Período:** 2026-03-26 → 2026-04-06  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×7

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `57cf5e644` | 2026-04-06 | Frontend (UI) | Task #47: Chat LIA — Correções visuais e Design System — Changes made: | `plataforma-lia/src/components/pages/chat-page.tsx`<br>`plataforma-lia/src/components/ui/prompt-suggestions-dock.tsx` |
| 🟢 | `ea3e1e26f` | 2026-03-26 | Docs | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritten with comprehensive, code-verified content: | `docs/specs/ai/PROMPT_STANDARDS.md` |
| 🟢 | `d3d815477` | 2026-03-26 | Docs | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritten with comprehensive, code-verified content: | `docs/specs/ai/AI_FAILURE_MODES.md`<br>`docs/specs/ai/PROMPT_STANDARDS.md` |
| 🟢 | `59775a4f2` | 2026-03-26 | Docs | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritten with comprehensive, code-verified content: | `docs/specs/ai/AI_FAILURE_MODES.md`<br>`docs/specs/ai/PROMPT_STANDARDS.md` |
| 🟢 | `d61b00193` | 2026-03-26 | Empty/merge | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritten with comprehensive, code-verified content: | — |
| 🟢 | `289f1d030` | 2026-03-26 | Docs | Task #47: PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (676 lines) — Both documents rewritten with comprehensive, code-verified content: | `docs/specs/ai/AI_FAILURE_MODES.md`<br>`docs/specs/ai/PROMPT_STANDARDS.md` |
| 🟢 | `c758211fa` | 2026-03-26 | Docs | Task #47: Comprehensive PROMPT_STANDARDS.md (722 lines) + AI_FAILURE_MODES.md (624 lines) — PROMPT_STANDARDS.md covers: | `docs/specs/ai/AI_FAILURE_MODES.md`<br>`docs/specs/ai/PROMPT_STANDARDS.md` |

### Task #81

- **Commits:** 7  |  **Período:** 2026-03-31 → 2026-03-31  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×7

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `3ae490572` | 2026-03-31 | Cross IA↔Back | Task #81 Audit Trail E2E - Complete implementation — All 8 Alpha 1 flow stages instrumented with correct signatures: | `lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` |
| 🟡 | `36b83c41e` | 2026-03-31 | Backend | Task #81 Audit Trail E2E - Final implementation — Changes across all 8 Alpha 1 flow stages: | `lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/api/v1/communication.py` |
| 🟡 | `8bd2645a4` | 2026-03-31 | Cross IA↔Back | Task #81 Audit Trail E2E - Review fixes round 4 — Changes: | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/shared/compliance/audit_service.py` |
| 🟡 | `b3f086a76` | 2026-03-31 | Backend | Task #81: Audit Trail — Ativação E2E (8 Etapas Alpha 1) — AuditService.log_decision instrumented across 10 files covering all stages: | `lia-agent-system/app/api/v1/interviews.py`<br>`lia-agent-system/app/api/v1/pipeline.py`<br>`lia-agent-system/app/api/v1/rubric_evaluation.py` |
| 🟡 | `e6155d595` | 2026-03-31 | Backend | Task #81: Audit Trail — Ativação E2E (8 Etapas Alpha 1) — AuditService.log_decision calls across all 8 Alpha 1 flow stages: | `lia-agent-system/app/api/v1/approvals.py`<br>`lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/api/v1/candidates.py` |
| 🟡 | `ec42e6bd8` | 2026-03-31 | Backend | Task #81: Audit Trail — Ativação E2E (8 Etapas Alpha 1) — Added AuditService.log_decision calls across all 8 Alpha 1 flow stages: | `lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/api/v1/communication.py` |
| 🟡 | `ca473c0b9` | 2026-03-31 | Backend | Task #81: Audit Trail — Ativação E2E (8 Etapas Alpha 1) — Added AuditService.log_decision calls across all 8 Alpha 1 flow stages: | `lia-agent-system/app/api/v1/approvals.py`<br>`lia-agent-system/app/api/v1/auth.py`<br>`lia-agent-system/app/api/v1/candidates.py` |

### Task #90

- **Commits:** 7  |  **Período:** 2026-04-01 → 2026-04-01  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×7

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `4b9e8c24e` | 2026-04-01 | Docs | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 23 errors across P2-P13 in the migration guide: | `WeDO/analises/AUDITORIA_GUIA_MIGRACAO.md`<br>`WeDO/guias/GUIA_MIGRACAO_V5_COMPLIANCE.md` |
| 🟢 | `2f3dffbad` | 2026-04-01 | Docs | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 23 errors across P2-P13 in the migration guide: | `WeDO/analises/AUDITORIA_GUIA_MIGRACAO.md`<br>`WeDO/guias/GUIA_MIGRACAO_V5_COMPLIANCE.md` |
| 🟢 | `abde32ef8` | 2026-04-01 | Frontend (UI) | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 23 errors across P2-P13 in the migration guide: | `plataforma-lia/src/app/chat/page.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/page.tsx` |
| 🟢 | `5aa3c8fc1` | 2026-04-01 | Frontend (UI) | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 23 errors across P2-P13 in the migration guide: | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx` |
| 🟢 | `1fe5ffa36` | 2026-04-01 | Frontend (UI) | Task #90: Audit and correction of migration guide v2.2 → v2.3 (docs-only) — Corrected 20 errors across P2-P13 in the migration guide: | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/jobs/[id]/page.tsx`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx` |
| 🟢 | `21e5b4a1a` | 2026-04-01 | Frontend (UI) | Task #90: Deep audit and correction of migration guide v2.2 → v2.3 — Audit findings (20 errors corrected across P2-P13): | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/jobs/[id]/page.tsx`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx` |
| 🟢 | `7af222695` | 2026-04-01 | Frontend (UI) | Task #90: Deep audit and correction of migration guide v2.2 → v2.3 — Audit findings (20 errors corrected): | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/jobs/[id]/page.tsx`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx` |

### Tests (FE e2e)

**Descrição:** Testes Playwright e2e — kanban, chat, candidates, audit suites.

**⚠️ Dependências para cherry-pick:** Test selectors estáveis (data-testid) | dev server rodando

**Arquivos canônicos:** plataforma-lia/e2e/**, **/*.test.tsx, **/*.spec.ts

**Docs de referência:** —

- **Commits:** 7  |  **Período:** 2026-04-07 → 2026-04-29  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×4 🟡×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `2774dea0b` | 2026-04-29 | Frontend (UI) | Add testing for new review panel and update helper functions — Add a data-testid to the review panel and update helper functions to use this testid for better end- | `plataforma-lia/src/components/unified-chat/wizard/panels/ReviewPanel.tsx` |
| 🟡 | `dca7d0372` | 2026-04-29 | Testes | Update end-to-end tests for improved navigation and element stability — Refactor Playwright tests to use `domcontentloaded` for page navigation, adjust selectors and timeou | `plataforma-lia/e2e/fixtures/auth.fixture.ts`<br>`plataforma-lia/e2e/tests/chat/rail-a-cards.spec.ts`<br>`plataforma-lia/e2e/tests/chat/rail-a-cards.spec.ts-snapshots/ral-02-captacao-desktop-chrome-linux.png` |
| 🟢 | `d6a0b5ca7` | 2026-04-22 | Frontend (UI) | Improve error display and speed up candidate search reliability — Update error message key and enhance smoke test to count table rows for faster candidate search reli | `plataforma-lia/src/app/[locale]/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `6985e5bef` | 2026-04-17 | Frontend (UI) | Improve backend proxy to handle varied response formats — Update backend proxy and related scripts to ensure consistent handling of chat responses, including  | `plataforma-lia/src/app/api/backend-proxy/chat/message/route.ts` |
| 🟡 | `7f2052cf6` | 2026-04-11 | Frontend (api/util) | Improve test reporting by attaching screenshots to test information — Updated `takeEvalScreenshot` function to accept `TestInfo` and attach screenshots to Playwright HTML | `plataforma-lia/.gitignore`<br>`plataforma-lia/e2e/reports/eval-summary.json`<br>`plataforma-lia/e2e/reports/html/index.html` |
| 🟢 | `913e10bf1` | 2026-04-10 | Testes | Update authentication to support staging environments and improve deployment guide — Update auth fixture to dynamically determine authentication domain based on PLAYWRIGHT_BASE_URL, con | `plataforma-lia/e2e/fixtures/auth.fixture.ts`<br>`plataforma-lia/playwright.config.ts` |
| 🟢 | `6e37900d4` | 2026-04-07 | Testes | Improve testing setup and documentation for local development — Update Playwright configuration and auth fixture for local testing, and enhance deployment documenta | `plataforma-lia/e2e/fixtures/auth.fixture.ts`<br>`plataforma-lia/playwright.config.ts` |

### scope: docs

- **Commits:** 7  |  **Período:** 2026-03-20 → 2026-04-04  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×6 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `58a2e5753` | 2026-04-04 | Docs | feat(docs): create Excalidraw ANTES vs DEPOIS architecture diagram for LIA AI system — Task #127 — Diagrama técnico de arquitetura IA | `lia-agent-system/docs/diagrams/ia-arquitetura-antes-depois.excalidraw` |
| 🟢 | `063bd792d` | 2026-03-31 | Docs | fix(docs): corrige nomenclatura de classes no fluxo técnico E2E — - WSIQuestionGeneratorService → WSIQuestionGenerator / WSIScreeningQuestionGenerator (3 ocorrências) | `docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md` |
| 🟢 | `37106df18` | 2026-03-30 | Docs | refactor(docs): Seção 0 Alpha 1 v4.0 — foco IA estrito — - Reescrita completa da Seção 0 do ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `37901fafa` | 2026-03-30 | Frontend (api/util) | fix(docs): convert ASCII box-drawing tables to Markdown + fix use client ordering — 1. Converted all 8+ ASCII box-drawing tables (┌─┬─┐) in | `plataforma-lia/src/hooks/use-lia-suggestions.ts` |
| 🔴 | `862d6e8ad` | 2026-03-30 | Frontend (UI) | fix(docs): convert all ASCII box-drawing tables to standard Markdown tables in DIAGNOSTICO_ATS_FRONT_VUE.md — Converted 8+ ASCII box-drawing tables (using ┌─┬─┐ characters) to | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx`<br>`plataforma-lia/src/components/admin/ai-consumption/ConsumptionSummaryCard.tsx`<br>`plataforma-lia/src/components/admin/clients/ClientCard.tsx` |
| 🟢 | `17241f3b6` | 2026-03-30 | Docs | fix(docs): convert all ASCII box-drawing tables to standard Markdown tables — Converted 8+ ASCII box-drawing tables in DIAGNOSTICO_ATS_FRONT_VUE.md | `docs/specs/frontend/DIAGNOSTICO_ATS_FRONT_VUE.md` |
| 🟢 | `d6acd9b68` | 2026-03-20 | Docs | feat(docs): add v5 domains/agents map to executive summary + guardrails_seed evidence — Added 'Mapa de Domínios e Agentes do v5' section to Sumário Executivo: | `proposals/diagnostico_arquitetura_codigo_lia_vs_v5.md` |

### Docs / Diagramas

**Descrição:** Diagramas Excalidraw / Mermaid de arquitetura, fluxos.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** docs/diagrams/**, *.excalidraw

**Docs de referência:** —

- **Commits:** 6  |  **Período:** 2026-03-29 → 2026-04-11  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×5 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `8de193476` | 2026-04-11 | Outro | feat: add updated Detailed System Architecture diagram (April 2026) — - Updated from real codebase: 56 domains, 304 API files, 33 orchestrator files (1.2MB) | `diagrams/lia-ai-architecture.excalidraw` |
| 🟢 | `c9cc53583` | 2026-03-29 | Docs | Add comprehensive architecture diagrams to the documentation — Create a new Excalidraw diagram file mirroring the complete architecture details from the HTML, incl | `docs/diagrams/architecture-transversal-unified.excalidraw` |
| 🟢 | `c82d16096` | 2026-03-29 | Docs | Add comparative analysis and screening flow details to architecture diagram — Add comparative table, detailed screening flow comparison (v5 vs LIA), and flow comparison table to  | `docs/diagrams/recruiter-agent-v5-architecture.excalidraw` |
| 🟢 | `303a3de04` | 2026-03-29 | Frontend (UI) | Add detailed comparison of prompt capabilities between LIA and v5 — Introduce new sections to the documentation comparing prompt-specific functionalities, tool usage, a | `plataforma-lia/src/app/globals.css` |
| 🟢 | `a833a506b` | 2026-03-29 | Docs | Add LIA architecture diagram to existing v5 diagram file — Adds the LIA architecture diagram alongside the v5 diagram in the recruiter-agent-v5-architecture.ex | `docs/diagrams/lia-ai-architecture.excalidraw`<br>`docs/diagrams/recruiter-agent-v5-architecture.excalidraw` |
| 🟢 | `622790db9` | 2026-03-29 | Frontend (api/util) | Add detailed architecture diagram for the LIA platform — Generate an HTML architecture diagram for the LIA platform, detailing its frontend, API gateway, orc | `plataforma-lia/public/diagram-lia-detailed.html` |

### Fase 5

- **Commits:** 6  |  **Período:** 2026-03-28 → 2026-03-31  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×5 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `f27726d9b` | 2026-03-31 | Empty/merge | Task #72: Fase 5 — Otimização + Inteligência (A5, A6, G3, G4) — Implemented 5 features: | — |
| 🟢 | `edc158a23` | 2026-03-31 | Empty/merge | Task #72: Fase 5 — Otimização + Inteligência (A5, A6, G3, G4) — Implemented 5 features: | — |
| 🟢 | `8eaabb5cb` | 2026-03-31 | Empty/merge | Task #72: Fase 5 — Otimização + Inteligência (A5, A6, G3, G4) — Implemented 5 features: | — |
| 🟢 | `f888516d2` | 2026-03-30 | Docs | docs: atualiza score para 10.0/10 — FASE 5 monolith splits concluidos | `docs/specs/frontend/FRONTEND_INVENTORY_v1.md`<br>`docs/specs/frontend/INVENTARIO_COMPONENTES.md`<br>`docs/specs/frontend/OPORTUNIDADES_PADRONIZACAO.md` |
| 🟢 | `8313bacca` | 2026-03-30 | Frontend (UI) | feat: FASE 5 monolith splits — 5 arquivos grandes divididos — ats-integrations-page.tsx: 1522L -> 418L + ats-integrations/ (types, constants, hook, modal) | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesPageCore.tsx` |
| 🔴 | `2e65c1f44` | 2026-03-28 | Frontend (UI) | Fase 5 parcial — var(--eleven-*) → Tailwind DS tokens (98 arquivos) — Substitui 2.800+ ocorrências de var(--eleven-*) em inline styles por | `plataforma-lia/src/app/access/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/automacoes/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/big-five/page.tsx` |

### Job Management (BE)

**Descrição:** Domínio de gestão de vagas — services, tools, repositórios.

**⚠️ Dependências para cherry-pick:** Schema canônico Job (com seniority, não level) | tenant guards

**Arquivos canônicos:** lia-agent-system/app/domains/job_management/**

**Docs de referência:** —

- **Commits:** 6  |  **Período:** 2026-04-12 → 2026-04-28  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🔴×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `e0fb295b9` | 2026-04-28 | Cross Back↔Front | Enhance salary suggestions with ATS job history and refine task display — Integrate ATS job history for salary recommendations, add a pipeline template selection card, and im | `lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_salary.py`<br>`plataforma-lia/src/app/api/backend-proxy/v1/tasks/route.ts`<br>`plataforma-lia/src/components/unified-chat/wizard/wizard-plan-card.ts` |
| 🟢 | `f49be9b4d` | 2026-04-21 | Docs | Update documentation and code to reflect standardized workforce import and job pagination contracts — Refactors `DEVELOPER_HANDOFF_UX_REDESIGN.md` to update test file references and documentation for  | `lia-agent-system/docs/INITIATIVES_AUDIT.md`<br>`plataforma-lia/DEVELOPER_HANDOFF_UX_REDESIGN.md` |
| 🟡 | `182dec756` | 2026-04-21 | Backend | Add pagination to job search functionality — Implement offset and limit parameters for the search_jobs function in query_tools.py, along with a n | `lia-agent-system/app/domains/job_management/tools/query_tools.py`<br>`lia-agent-system/tests/unit/test_fix20_pagination.py` |
| 🔴 | `e3c1ed576` | 2026-04-19 | Cross IA↔Front | Improve job management and candidate comparison tools — Refactors job management tools to use a dedicated service layer, enhances the candidate comparison f | `lia-agent-system/app/domains/job_management/services/job_vacancy_lifecycle_service.py`<br>`lia-agent-system/app/domains/sourcing/services/consent_cache.py`<br>`lia-agent-system/app/tools/job_tools.py` |
| 🟡 | `d9b4bd83b` | 2026-04-17 | Backend | Add logging to job search functionality — Add debug logging for the number of rows returned by the job search query in `query_tools.py`. | `lia-agent-system/app/domains/job_management/tools/query_tools.py` |
| 🟡 | `9182a35c9` | 2026-04-12 | Backend | fix: restore vacancy_search_service.py — imported by 2 endpoints (not dead duplicate) | `lia-agent-system/app/domains/job_management/services/vacancy_search_service.py` |

### Scripts / Jira tooling

**Descrição:** Scripts auxiliares de Jira — fetch + analyze cards, audit design, update specific cards (WT-1639). Usa Anthropic API para análise.

**⚠️ Dependências para cherry-pick:** Anthropic API key (env) | acesso Jira | scripts rodam local/CI, não em prod

**Arquivos canônicos:** scripts/jira-fetch-analyze.py, scripts/jira-audit-design.py, scripts/jira-update-*.py

**Docs de referência:** —

- **Commits:** 6  |  **Período:** 2026-03-22 → 2026-03-24  |  **Camadas:** —  |  **—**  |  **Risco:** 🟡×6

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `4e46858de` | 2026-03-24 | Outro | Improve analysis script by extracting BetterBugs links and optimizing LLM calls — Enhance the `adf_to_text` function to extract BetterBugs URLs from link marks, adjust the prompt to  | `scripts/jira-fetch-analyze.py` |
| 🟡 | `8fff66478` | 2026-03-23 | Outro | Stop updating card descriptions and post analysis as comments — Replaces direct updates to card descriptions with posts to comments, as the description endpoint can | `scripts/jira-audit-design.py`<br>`scripts/jira-fetch-analyze.py` |
| 🟡 | `cb323fc58` | 2026-03-23 | Outro | Add detailed design and quality assurance information to Jira cards — Adds a new function to analyze and generate design issues, acceptance criteria, and Definition of Do | `scripts/jira-fetch-analyze.py` |
| 🟡 | `efd618f8d` | 2026-03-23 | Outro | Improve AI model integration and code analysis capabilities — Update Anthropic API integration to use environment variables for keys and base URLs, switch to a mo | `scripts/jira-audit-design.py`<br>`scripts/jira-fetch-analyze.py` |
| 🟡 | `decb3621b` | 2026-03-23 | Outro | scripts: adiciona jira-fetch-analyze.py e jira-audit-design.py — jira-fetch-analyze.py (comando fetch): | `scripts/jira-audit-design.py`<br>`scripts/jira-fetch-analyze.py` |
| 🟡 | `52c6faa4a` | 2026-03-22 | Outro | Add audit documentation for the login screen redesign to Jira — Update Jira card WT-1639 with detailed audit documentation for the login screen, including file refe | `scripts/jira-update-wt1639-login-audit.py` |

### Task #111

- **Commits:** 6  |  **Período:** 2026-04-03 → 2026-04-10  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×6

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `4c9d6fb1a` | 2026-04-10 | Docs | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Comprehensive update to DEPLOY_GUIDE.md reflecting real codebase state as of April 10, 2026: | `DEPLOY_GUIDE.md` |
| 🟢 | `853205f22` | 2026-04-10 | Docs | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Comprehensive update to DEPLOY_GUIDE.md reflecting real codebase state as of April 10, 2026: | `DEPLOY_GUIDE.md` |
| 🟢 | `4c4006989` | 2026-04-10 | Docs | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Comprehensive update to DEPLOY_GUIDE.md reflecting real codebase state as of April 10, 2026: | `DEPLOY_GUIDE.md` |
| 🟢 | `9a863a043` | 2026-04-10 | Docs | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Updates to DEPLOY_GUIDE.md reflecting the real state of the codebase as of April 10, 2026: | `DEPLOY_GUIDE.md` |
| 🟢 | `d869f573f` | 2026-04-10 | Docs | Task #111: Atualizar DEPLOY_GUIDE.md — Snapshot Completo Abril 2026 — Updates to DEPLOY_GUIDE.md reflecting the real state of the codebase as of April 10, 2026: | `DEPLOY_GUIDE.md` |
| 🟢 | `ec3ae7b76` | 2026-04-03 | Docs | Task #111: Generate deep frontend optimization report for Plataforma LIA — Creates docs/specs/frontend/FRONTEND_OPTIMIZATION_REPORT.md (747 lines) based on | `docs/specs/frontend/FRONTEND_OPTIMIZATION_REPORT.md` |

### Task #115

- **Commits:** 6  |  **Período:** 2026-04-04 → 2026-04-10  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×3 🟡×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `71d3c7938` | 2026-04-10 | Frontend (UI) | Task #115: GCP Infrastructure Checklist — Guia de Provisionamento — Created GCP_INFRASTRUCTURE_CHECKLIST.md — a comprehensive, self-contained | `plataforma-lia/src/components/modals/add-to-job-modal.tsx` |
| 🟢 | `9a067fe27` | 2026-04-10 | Frontend (UI) | Task #115: GCP Infrastructure Checklist — Guia de Provisionamento — Created GCP_INFRASTRUCTURE_CHECKLIST.md — a comprehensive, self-contained | `plataforma-lia/src/components/modals/add-to-job-modal.tsx` |
| 🟢 | `a8b8732f2` | 2026-04-10 | Docs | Task #115: GCP Infrastructure Checklist — Guia de Provisionamento — Created GCP_INFRASTRUCTURE_CHECKLIST.md — a comprehensive, self-contained | `GCP_INFRASTRUCTURE_CHECKLIST.md` |
| 🟡 | `0ea776065` | 2026-04-04 | Backend | Task #115: Lazy Loading - Replace () => null loading fallbacks with visible loading states — All dynamic() imports across modal and page-section files now use proper | `lia-agent-system/app/domains/communication/services/teams_card_renderer.py` |
| 🔴 | `7f946bcf3` | 2026-04-04 | Cross Back↔Front | Task #115: Lazy Loading - Replace () => null loading fallbacks with visible loading states — All dynamic() imports across modal and page-section files now use proper | `lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/domains/communication/services/teams_card_renderer.py`<br>`lia-agent-system/app/domains/communication/services/teams_simple.py` |
| 🟡 | `81ce3e554` | 2026-04-04 | Frontend (UI) | Task #115: Lazy Loading + Code Splitting (Modais e Dashboards) — - Created reusable LoadingFallback, LoadingModal, and LoadingDashboard | `plataforma-lia/src/app/admin/loading.tsx`<br>`plataforma-lia/src/app/configuracoes/loading.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx` |

### Task #116

- **Commits:** 6  |  **Período:** 2026-04-04 → 2026-04-10  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×4 🔴×1 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `4175bf2da` | 2026-04-10 | Frontend (api/util) | Task #116: Plano de Validação e Smoke Tests — Pré Go-Live — Created comprehensive validation plan and updated E2E test infrastructure: | `plataforma-lia/next.config.js` |
| 🟢 | `6e8e74c40` | 2026-04-10 | Testes | Task #116: Plano de Validação e Smoke Tests — Pré Go-Live — Created comprehensive validation plan and updated E2E test infrastructure: | `plataforma-lia/e2e/fixtures/auth.fixture.ts` |
| 🟢 | `25a91033e` | 2026-04-04 | Frontend (UI) | Task #116: Zustand State Management - Complete migration — Stores: | `plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPublishing.ts` |
| 🟢 | `d8c16e34b` | 2026-04-04 | Frontend (UI) | Task #116: Zustand State Management - Complete with scoped reset — Auth Store (auth-store.ts): | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesPageCore.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts` |
| 🔴 | `0a44b6fa0` | 2026-04-04 | Cross Back↔Front | Task #116: Zustand State Management - Complete migration — Auth Store (auth-store.ts): | `lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_calendar_service.py`<br>`lia-agent-system/app/domains/communication/services/teams_sso_service.py` |
| 🟡 | `a800c7f61` | 2026-04-04 | Frontend (UI) | Task #116: Zustand State Management - Complete migration — - Created auth-store.ts, kanban-store.ts, candidates-store.ts with zustand + devtools | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesPageCore.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPageCore.ts`<br>`plataforma-lia/src/contexts/auth-context.tsx` |

### Task #135

- **Commits:** 6  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×6

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `94c3deb9e` | 2026-04-11 | IA | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: | `lia-agent-system/app/orchestrator/action_handlers/job_actions.py` |
| 🟡 | `7a2ef320f` | 2026-04-11 | Cross IA↔Back | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: | `lia-agent-system/app/domains/integrations_hub/services/rails_adapter.py`<br>`lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py` |
| 🟡 | `1b76403e0` | 2026-04-11 | IA | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: | `lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |
| 🟡 | `44db5fe52` | 2026-04-11 | IA | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: | `lia-agent-system/app/orchestrator/action_handlers/pipeline_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |
| 🟡 | `eb2961176` | 2026-04-11 | IA | Task #135: Complete Action Handlers — Real DB + Entity Resolution + Audit + Rails Sync — Core fixes: | `lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |
| 🟡 | `82605c5b8` | 2026-04-11 | Cross IA↔Back | Task #135: Action Handlers → Real DB Operations + Fix PL-002 — Changes: | `lia-agent-system/alembic/versions/063_create_scheduling_links_table.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |

### §11 Candidate Portal

**Descrição:** Spec completa do Candidate Portal (Rails + Replit). Auditoria técnica do chat candidato pós-aplicação. Proposta de construção. Market research. Sem implementação ainda — apenas docs/spec.

**⚠️ Dependências para cherry-pick:** Aguardando aprovação de roadmap | Spec validada com Rails team

**Arquivos canônicos:** docs/CANDIDATE_PORTAL_RAILS_SPEC.md (apenas docs)

**Docs de referência:** docs/CANDIDATE_PORTAL_RAILS_SPEC.md

- **Commits:** 6  |  **Período:** 2026-04-19 → 2026-04-20  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×5 🟡×1
- **Tags/Milestones:** `milestone/candidate-portal-rails-spec`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `63c21738e` | 2026-04-20 | Docs | docs: add real commit hashes to CANDIDATE_PORTAL_RAILS_SPEC | `plataforma-lia/CANDIDATE_PORTAL_RAILS_SPEC.md` |
| 🟢 | `1b0ca9629` | 2026-04-20 | Docs | docs: CANDIDATE_PORTAL_RAILS_SPEC.md spec completa Rails + Replit | `plataforma-lia/CANDIDATE_PORTAL_RAILS_SPEC.md` |
| 🟢 | `4a762e0ca` | 2026-04-19 | Frontend (UI) | Add candidate portal for job application status and chat — Add new files to manage candidate application status, job selection, and chat functionality. | `plataforma-lia/src/app/candidate/status/page.tsx`<br>`plataforma-lia/src/components/candidate/CandidateChatPage.tsx`<br>`plataforma-lia/src/components/candidate/CandidateJobSelector.tsx` |
| 🟢 | `6d4c50d4b` | 2026-04-19 | Docs | Task #576 — Proposta de construção do chat candidato pós-aplicação (LIA) — Original task: produzir um único documento de proposta de construção da feature | `docs/proposals/candidate-status-chat-construction-plan.md` |
| 🟡 | `3516036ec` | 2026-04-19 | Backend | Task #574 — Auditoria técnica do chat candidato pós-aplicação (LIA) — Original: produzir documento de viabilidade técnica (sem código) para o canal | `lia-agent-system/eval/eval_results_20260419_190516.json` |
| 🟢 | `8712157b6` | 2026-04-19 | Docs | docs(research): market research — chat candidato pós-aplicação — Original task #575: pesquisa de mercado sobre comunicação contínua com | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts`<br>`docs/research/candidate-status-chat-market.md` |

### §8 Glossário / Production-Ready

**Descrição:** ADR-019 + glossário central (281 actions / 94 tools / 18 domínios). execute_action coverage para os 11 domínios. Padronização para production-ready. Glossário com sync automático + CI guard. Enriquecimento de descrições.

**⚠️ Dependências para cherry-pick:** ADR-019 source of truth | execute_action 11/11 | CI guard verde

**Arquivos canônicos:** lia-agent-system/app/config/glossary.yaml, app/config/capability_map.yaml

**Docs de referência:** ADR-019 / BRANCH_MAP §8

- **Commits:** 6  |  **Período:** 2026-03-15 → 2026-04-20  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🔴×2 🟢×1
- **Tags/Milestones:** `milestone/domains-production-ready`, `milestone/glossary-canonical-281`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `f05db64d8` | 2026-04-20 | Cross IA↔Front | Task #691: Padronizar domínios em evolução para production-ready — Closes three critical gaps from MATURITY_ASSESSMENT and creates the canonical | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/shared/prompts/system_prompt_builder.py`<br>`lia-agent-system/libs/models/lia_models/billing.py` |
| 🟡 | `4930b4092` | 2026-04-20 | Cross IA↔Back | feat(docs): Task #692 — Glossário Central + sync automático + CI guard — ## O que foi entregue | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| 🟡 | `4375bf0ee` | 2026-04-20 | Backend | Task #687: Extend execute_action coverage to remaining 7 domains — Original task: Task #674 covered 11 domains (10 standard + job_creation). | `lia-agent-system/app/tests/test_execute_action_coverage.py`<br>`lia-agent-system/eval/eval_results_20260420_163611.json` |
| 🟢 | `596c9c5e5` | 2026-04-20 | Testes | test(execute_action): cobertura + tenant-isolation audit para 11 dominios — Task #674. Fecha o gap P1-1 (10 dominios sem teste de execute_action) e | `lia-agent-system/app/tests/test_execute_action_coverage.py`<br>`lia-agent-system/app/tests/test_job_creation_intent_flow.py` |
| 🟡 | `6e9287f50` | 2026-04-20 | Backend | docs: ADR-019 + glossário 281 actions/94 tools + MAPA 18 domínios — Original task #671: criar ADR-019 (intent-routed wizards), glossário das | `lia-agent-system/scripts/generate_glossario_actions_tools.py` |
| 🔴 | `620ef0b05` | 2026-03-15 | Cross IA↔Front | Sprints Y1–Y5 completos + Diagnóstico v6: plataforma IA production-ready — ## Sprints Y1 (D1–D10) — Fundações e Observabilidade | `lia-agent-system/alembic/versions/041_add_agent_ragas_evaluations.py`<br>`lia-agent-system/alembic/versions/042_add_disparate_impact_to_snapshot.py`<br>`lia-agent-system/alembic/versions/043_add_candidate_consent_grants.py` |

### Design System v4.2.2

**Descrição:** Design System v4.2.2 — tokens (cores, fonts, spacing), TypeScript ignoreBuildErrors, font-size-xs ajuste, audit migração tokens. SOURCE OF TRUTH em 00-design-system-v4.2.2.md.

**⚠️ Dependências para cherry-pick:** Tokens via design-tokens.css | tailwind.config.ts ALINHADO | nunca hardcode color/spacing

**Arquivos canônicos:** plataforma-lia/src/styles/design-tokens.css, plataforma-lia/docs/design-system/00-design-system-v4.md, plataforma-lia/tailwind.config.ts

**Docs de referência:** 00-design-system-v4.2.2.md

- **Commits:** 5  |  **Período:** 2026-04-02 → 2026-04-11  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×5

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `4ee7061e6` | 2026-04-11 | Docs | Design System v4.2.2: document updated with all new values, 4 new sections, zero old refs | `plataforma-lia/docs/design-system/00-design-system-v4.md` |
| 🟢 | `f1ade9154` | 2026-04-10 | Frontend (api/util) | Design System: add typescript ignoreBuildErrors | `plataforma-lia/next.config.js` |
| 🟢 | `548bbb150` | 2026-04-09 | Frontend (api/util) | Improve text readability by increasing font sizes across the platform — Adjust font size tokens in design-tokens.css and update diagnostic documentation to reflect global t | `plataforma-lia/src/styles/design-tokens.css` |
| 🟢 | `ff8b4a8b7` | 2026-04-02 | Docs | Clarify audit results in documentation regarding design token migration — Update replit.md to accurately reflect the outcome of the design token migration audit, noting that  | `replit.md` |
| 🟢 | `36e023f61` | 2026-04-02 | Frontend (api/util) | Update font size token to ensure consistency — Adjusted the `--font-size-xs` CSS token from 11px to 12px in `design-tokens.css` to align with Tailw | `plataforma-lia/src/styles/design-tokens.css` |

### DevOps / CI

**Descrição:** GitHub Actions CI pipeline — lint, test, build on push/PR.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** plataforma-lia/.github/workflows/ci.yml, .github/workflows/**

**Docs de referência:** —

- **Commits:** 5  |  **Período:** 2026-03-30 → 2026-04-14  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×4 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `77fc2a9b8` | 2026-04-14 | Infra/Config | ci: integrate eval runner in CI pipeline [PX08-050] — Sprint 6 item 6.5 — Eval suites now run on every PR: | `.github/workflows/ci.yml` |
| 🟡 | `d435a4d18` | 2026-04-13 | Infra/Config | ci: block unresolved merge conflict markers in main — Adds a CI step before ruff lint that greps for literal conflict markers | `.github/workflows/ci.yml` |
| 🟡 | `88654d044` | 2026-04-09 | Backend | task-84: Alinhar DEPLOY_GUIDE.md com código real + remover AWS — Tarefa original: Alinhar DEPLOY_GUIDE.md com o estado real do código, | `lia-agent-system/terraform/aws/main.tf`<br>`lia-agent-system/terraform/aws/outputs.tf`<br>`lia-agent-system/terraform/aws/userdata.sh` |
| 🟢 | `eca690fec` | 2026-03-31 | Frontend (api/util) | ci: add GitHub Actions CI pipeline — lint, test, build on push/PR to main | `plataforma-lia/.github/workflows/ci.yml` |
| 🟡 | `dcbcd92df` | 2026-03-30 | Infra/Config | ci: add Playwright E2E job to CI pipeline | `.github/workflows/ci.yml` |

### Docs / Refactor

**Descrição:** REFACTOR_PLAN, MIGRATION_READINESS — planos e checklists de refactor estrutural (extração Phase 2/3/4, contagem de monolitos).

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** lia-agent-system/REFACTOR_PLAN.md, plataforma-lia/MIGRATION_READINESS.md

**Docs de referência:** REFACTOR_PLAN.md

- **Commits:** 5  |  **Período:** 2026-04-01 → 2026-04-07  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×5

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `df7f53768` | 2026-04-07 | Docs | docs: update REFACTOR_PLAN after Phase 2+3+4B | `lia-agent-system/REFACTOR_PLAN.md` |
| 🟢 | `7e5560b6c` | 2026-04-07 | Docs | docs: revisit REFACTOR_PLAN with Rails-aware corrections — - Add Rails Migration Boundary section: entities owned by Rails vs FastAPI | `lia-agent-system/REFACTOR_PLAN.md` |
| 🟢 | `bf0e042d0` | 2026-04-06 | Docs | docs: update REFACTOR_PLAN.md — Phase 2 (12 migrated, 174 pending), Phase 4 done, Phase 9 LOC delta | `lia-agent-system/REFACTOR_PLAN.md` |
| 🟢 | `69bca4528` | 2026-04-01 | Docs | docs: fix MIGRATION_READINESS — files >1000L is 3 not 1 (design-tokens.css grew, useExpandedChatModalCore at 1001L) | `plataforma-lia/MIGRATION_READINESS.md` |
| 🟢 | `4a6a078e5` | 2026-04-01 | Docs | docs: MIGRATION_READINESS.md score 69/70 checklist context-store map risks | `plataforma-lia/MIGRATION_READINESS.md` |

### Docs / Screenshots

**Descrição:** Screenshots de docs (login, 2FA, chat) — usados em apresentações e auditorias.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** plataforma-lia/docs/screenshots/**

**Docs de referência:** —

- **Commits:** 5  |  **Período:** 2026-04-03 → 2026-04-09  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×4 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `a0116c89c` | 2026-04-09 | Docs | Update main application chat screenshot — Update the existing screenshot for the main application's chat interface. | `plataforma-lia/docs/screenshots/main-app-chat.jpg` |
| 🟢 | `2e58eb7ad` | 2026-04-03 | Docs | Update screenshots for login and 2FA process — Update screenshots to reflect the final state of the login and 2FA process, including disabled butto | `plataforma-lia/docs/screenshots/session3/S3-final-btn-disabled.png`<br>`plataforma-lia/docs/screenshots/session3/S3-final-filled.png` |
| 🟢 | `1657ad17c` | 2026-04-03 | Docs | Update screenshots showing successful code input — Update screenshots to demonstrate successful input methods for verification codes. | `plataforma-lia/docs/screenshots/session3/S3-debug-methods.png`<br>`plataforma-lia/docs/screenshots/session3/S3-v4-typed.png` |
| 🟢 | `d67a75dd3` | 2026-04-03 | Docs | Update screenshots for user login and 2FA process — Update screenshots to reflect changes in the user login and two-factor authentication flow. | `plataforma-lia/docs/screenshots/session3/S3-pre2fa.png`<br>`plataforma-lia/docs/screenshots/session3/S3-single-2fa-ready.png` |
| 🟡 | `4f55a46ee` | 2026-04-03 | Docs | Update scripts to handle website login and two-factor authentication flow — Refactor and add new Python scripts using Playwright to automate the login process, including handli | `plataforma-lia/docs/screenshots/session3/S3-2fa-btn-disabled.png`<br>`plataforma-lia/docs/screenshots/session3/S3-2fa-filled.png`<br>`plataforma-lia/docs/screenshots/session3/S3-2fa-ready.png` |

### FE libs / utils

**Descrição:** Libs e utils do frontend — utilitários compartilhados, helpers, hooks ad-hoc.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** plataforma-lia/src/lib/**

**Docs de referência:** —

- **Commits:** 5  |  **Período:** 2026-03-26 → 2026-04-24  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×2 🟡×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `aeab95013` | 2026-04-24 | Frontend (api/util) | Restore development login functionality and fix configuration errors — Restore the `dev-auto-login.ts` module and remove the invalid `jsxImportSource` configuration from ` | `plataforma-lia/src/lib/auth/dev-auto-login.ts`<br>`plataforma-lia/tsconfig.json` |
| 🟡 | `aa4dcd285` | 2026-04-09 | Frontend (UI) | Improve chat message formatting to display rich content correctly — Integrate the 'marked' library to convert markdown to HTML, enabling proper rendering of bold text,  | `plataforma-lia/src/app/globals.css`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/pages/chat-page.css` |
| 🔴 | `9882eeb76` | 2026-04-05 | Cross Back↔Front | Hide internal thoughts from users in chat conversations — Add functionality to strip `<thought>` tags from agent responses on both the frontend and backend, a | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/components/triagem/MessageBubble.tsx` |
| 🟡 | `48b864ccd` | 2026-03-30 | Frontend (UI) | forms: integra React Hook Form + Zod no login + schemas centralizados — fecha ALT-12 | `plataforma-lia/src/app/forgot-password/page.tsx`<br>`plataforma-lia/src/app/login/page.tsx` |
| 🟢 | `482ae4dc2` | 2026-03-26 | Frontend (api/util) | Standardize floating LIA chat to match job creation prompt style — Problem: Floating LIA chat showed raw JSON from agent responses | `plataforma-lia/src/lib/chat-format.ts` |

### Fase 3

- **Commits:** 5  |  **Período:** 2026-03-27 → 2026-04-11  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🟢×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `3a42a1dd8` | 2026-04-11 | Cross IA↔Back | Task #129: Fase 3 — Guardrail de Custo por Request Individual — Per-request token budget ceiling prevents individual LLM calls from | `lia-agent-system/app/main.py`<br>`lia-agent-system/app/services/token_budget_service.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py` |
| 🔴 | `ee302937d` | 2026-03-30 | Frontend (UI) | feat: FASE 3+4 frontend — ESLint 0, 342 testes, CI/CD pipeline — ESLint: 19 erros -> 0 | `plataforma-lia/src/app/accept-invitation/page.tsx`<br>`plataforma-lia/src/app/access/page.tsx`<br>`plataforma-lia/src/app/aceitar-convite/page.tsx` |
| 🟢 | `6fb9868fb` | 2026-03-28 | Frontend (UI) | Fase 3 — Consolidação de Badges: dark mode + tokens DS v4.2.1 — setup-alert-badge: transition-shadow removida (anti-DS), 5 CSS vars bracket → Tailwind nativo, dark  | `plataforma-lia/src/components/ui/chat-status-indicators.tsx`<br>`plataforma-lia/src/components/ui/score-icon-button.tsx`<br>`plataforma-lia/src/components/ui/setup-alert-badge.tsx` |
| 🟡 | `1a465e204` | 2026-03-27 | Frontend (UI) | Fase 3 — Consolidação de Badges: tokens DS + órfãos removidos — 3A badge.tsx: rgba() hardcoded → tokens Tailwind (wedo-green/15, wedo-orange/15, | `plataforma-lia/src/components/job-creation/field-origin-badge.tsx`<br>`plataforma-lia/src/components/screening/auto-screening-badge.tsx`<br>`plataforma-lia/src/components/screening/index.ts` |
| 🟢 | `91155fb24` | 2026-03-27 | Docs | Fase 3 — Plano revisado com tokens semânticos, Vuetify map e code review — - Diagnóstico real: 2 órfãos (suggestion-badge, auto-screening-badge = 0 imports) | `docs/specs/frontend/INVENTARIO_COMPONENTES.md` |

### Modals (FE)

**Descrição:** Modais genéricos compartilhados (não confundir com OfferReviewModal específico). Inclui job-status, modais utilitários.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** plataforma-lia/src/components/modals/**

**Docs de referência:** —

- **Commits:** 5  |  **Período:** 2026-03-25 → 2026-04-10  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×3 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `4207da3c0` | 2026-04-10 | Frontend (UI) | Update modals to improve user experience and information display — Adjusted the Add to Job modal to correctly handle duplicate checks and updated the Job Publish modal | `plataforma-lia/src/components/modals/add-to-job-modal.tsx`<br>`plataforma-lia/src/components/modals/job-publish-modal.tsx` |
| 🟡 | `60db7e985` | 2026-03-31 | Frontend (UI) | Update technical documentation with completed audit trail features — Update FLUXO_TECNICO_COMPLETO_ALPHA1.md to reflect the activation of audit trails for various featur | `plataforma-lia/src/components/modals/english-test-modal.tsx`<br>`plataforma-lia/src/components/modals/technical-test-modal.tsx`<br>`plataforma-lia/src/components/onboarding/onboarding-controller.tsx` |
| 🟡 | `4c42a4edf` | 2026-03-30 | Frontend (UI) | Update job editing functionality and component structure — Refactor job editing modal and types, update various job-related components, and adjust loading stat | `plataforma-lia/src/app/admin/configuracoes/politicas/page.tsx`<br>`plataforma-lia/src/components/modals/edit-job-modal.tsx`<br>`plataforma-lia/src/components/modals/edit-job/edit-job.types.ts` |
| 🟢 | `d533ad4e0` | 2026-03-29 | Frontend (UI) | Add safety for recruiter assignment in job modals — Protect JobAssignRecruiterModal from undefined recruiters array by using `recruiters ?? []` before a | `plataforma-lia/src/components/modals/job-assign-recruiter-modal.tsx` |
| 🟢 | `418d976fe` | 2026-03-25 | Frontend (UI) | Enhance job publishing with detailed screening checklists and Big Five traits — Introduce a comprehensive publication checklist in the job publish modal, display Big Five traits an | `plataforma-lia/src/components/modals/job-publish-modal.tsx`<br>`plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx`<br>`plataforma-lia/src/components/wsi/JDEvaluationPanel.tsx` |

### Task #136

- **Commits:** 5  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🔴×1 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `efa142c5b` | 2026-04-11 | Cross IA↔Front | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallback (handler + service layer) | `lia-agent-system/app/orchestrator/action_handlers/communication_actions.py`<br>`plataforma-lia/src/app/shared/[token]/_components/SharedContent.tsx`<br>`plataforma-lia/src/components/ai/agent-explainability-panel.tsx` |
| 🟡 | `c1334df3e` | 2026-04-11 | Backend | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallback (handler + service layer) | `lia-agent-system/app/domains/communication/services/email_service.py` |
| 🟢 | `9fdbe7dc0` | 2026-04-11 | Empty/merge | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallback (handler + service layer) | — |
| 🟡 | `5bebbdc3e` | 2026-04-11 | Cross IA↔Back | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallback (handler + service layer) | `lia-agent-system/app/domains/communication/services/email_service.py`<br>`lia-agent-system/app/domains/communication/services/whatsapp_service.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |
| 🟡 | `c2b3ddf95` | 2026-04-11 | IA | Task #136: P0 Communication Domain Fix — Email, Templates & Messaging — CM-001: Dev-mode email fallback in _send_email | `lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |

### Task #151

- **Commits:** 5  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `7574d67e1` | 2026-04-11 | Cross IA↔Back | feat(task-151): Complete services migration — domain services as source of truth — Domain services migration (app/services/ → app/domains/*/services/): | `lia-agent-system/app/services/ats_clients/__init__.py`<br>`lia-agent-system/app/services/ats_clients/ats_pii_filter.py`<br>`lia-agent-system/app/services/ats_clients/base.py` |
| 🔴 | `db08579cd` | 2026-04-11 | Cross IA↔Back | feat(task-151): Complete services migration — domain services as source of truth — Domain services migration (app/services/ → app/domains/*/services/): | `lia-agent-system/app/api/v1/admin_token_budget.py`<br>`lia-agent-system/app/api/v1/agent_chat_sse.py`<br>`lia-agent-system/app/api/v1/agent_chat_ws.py` |
| 🟡 | `f95ac8e71` | 2026-04-11 | Backend | feat(task-151): Complete services migration — single source of truth — Shim elimination (app/services/): | `lia-agent-system/app/shared/services/rag_pipeline_service.py`<br>`lia-agent-system/app/shared/services/recruiter_behavior_service.py` |
| 🟡 | `85af8700b` | 2026-04-11 | Cross IA↔Back | feat(task-151): Complete services migration — single source of truth — Shim elimination: | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/api/v1/rag_search.py`<br>`lia-agent-system/app/domains/ai/services/rag_pipeline_service.py` |
| 🔴 | `ef3114c66` | 2026-04-11 | Cross IA↔Back | feat(task-151): Complete services migration — single source of truth — - Eliminated 129 forward/backward shim files from app/services/ | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/admin_lgpd.py`<br>`lia-agent-system/app/api/v1/admin_prompts.py` |

### Task #157

- **Commits:** 5  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×5

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `3025c7374` | 2026-04-11 | Backend | Task #157: Monetizable Modules Infrastructure — Complete — Model & Migration: | `lia-agent-system/app/domains/modules/services/module_service.py` |
| 🟡 | `1ffc88be1` | 2026-04-11 | Backend | Task #157: Monetizable Modules Infrastructure — Complete — Model & Migration: | `lia-agent-system/app/api/v1/modules.py`<br>`lia-agent-system/app/domains/modules/services/module_service.py` |
| 🟡 | `15ae4cfa9` | 2026-04-11 | Backend | Task #157: Monetizable Modules Infrastructure — - CompanyModule model in billing.py with ModuleStatus/ModuleTier enums and AVAILABLE_MODULES catalog | `lia-agent-system/alembic/versions/066_create_company_modules.py`<br>`lia-agent-system/libs/models/lia_models/billing.py` |
| 🟡 | `752db1544` | 2026-04-11 | Backend | Task #157: Monetizable Modules Infrastructure — - CompanyModule model in billing.py with ModuleStatus/ModuleTier enums and AVAILABLE_MODULES catalog | `lia-agent-system/alembic/versions/066_create_company_modules.py`<br>`lia-agent-system/app/api/v1/modules.py`<br>`lia-agent-system/libs/models/lia_models/billing.py` |
| 🟡 | `1b6e85fe1` | 2026-04-11 | Backend | Task #157: Monetizable Modules Infrastructure — - CompanyModule model in billing.py with ModuleStatus/ModuleTier enums and AVAILABLE_MODULES catalog | `lia-agent-system/alembic/env.py`<br>`lia-agent-system/alembic/versions/066_create_company_modules.py`<br>`lia-agent-system/app/api/routes.py` |

### Task #206

- **Commits:** 5  |  **Período:** 2026-04-15 → 2026-04-15  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×4 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `058d6ae30` | 2026-04-15 | Frontend (api/util) | fix(task-206): Address all code review findings for Minha Empresa cards — 1. Reduced blocks from 8 to 7: merged departments count into Benefits card | `plataforma-lia/src/hooks/settings/use-company-settings-cards.ts` |
| 🟢 | `4e1dabe52` | 2026-04-15 | Frontend (api/util) | fix(task-206): Address all 4 code review findings for Minha Empresa cards — 1. Reduced blocks from 8 to 7: merged departments count into Benefits card | `plataforma-lia/src/hooks/settings/use-company-settings-cards.ts` |
| 🟢 | `306982931` | 2026-04-15 | Frontend (UI) | Task #206: Minha Empresa conversational cards — full implementation — Frontend changes: | `plataforma-lia/src/components/settings/MinhaEmpresaCard.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx` |
| 🟢 | `f02fd9a42` | 2026-04-15 | Frontend (UI) | Task #206: Minha Empresa conversational cards — complete implementation — Frontend: | `plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaCard.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx` |
| 🔴 | `403074a45` | 2026-04-15 | Cross IA↔Front | Task #206: Minha Empresa conversational cards + backend context routing — - Added `settings_config` to ChatContextType in lia-float-context.tsx | `lia-agent-system/app/orchestrator/context_adapter.py`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx`<br>`plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx` |

### Task #36

- **Commits:** 5  |  **Período:** 2026-03-24 → 2026-04-06  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×3 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `fdfa7faba` | 2026-04-06 | Frontend (UI) | Task #36: Reports & Predictions — Real ML data in frontend — - Fixed `catch (error: any)` → `catch (error: unknown)` with proper narrowing | `plataforma-lia/src/components/pages/indicators/tabs/PredictionsTab.tsx` |
| 🟢 | `b095ed03f` | 2026-04-06 | Frontend (UI) | Task #36: Reports & Predictions — Real ML data in frontend — - Fixed `catch (error: any)` → `catch (error: unknown)` with proper narrowing | `plataforma-lia/src/components/job-report-modal.tsx`<br>`plataforma-lia/src/components/pages/indicators/tabs/PredictionsTab.tsx`<br>`plataforma-lia/src/components/pages/work-model-analytics-page.tsx` |
| 🔴 | `6d7a9daf8` | 2026-04-06 | Cross IA↔Front | Task #36: Wire ML predictions to frontend reports and analytics — - job-report-modal.tsx: Added useMLPredictions hook integration with | `lia-agent-system/app/api/v1/candidates.py`<br>`lia-agent-system/app/api/v1/clients.py`<br>`lia-agent-system/app/api/v1/workos.py` |
| 🔴 | `e7e1bb07e` | 2026-04-06 | Cross IA↔Front | Task #36: Wire ML predictions to frontend reports and analytics — - job-report-modal.tsx: Added useMLPredictions hook integration with | `lia-agent-system/app/api/v1/affirmative.py`<br>`lia-agent-system/app/api/v1/calibration.py`<br>`lia-agent-system/app/api/v1/job_vacancies/analytics.py` |
| 🟢 | `972c2efaf` | 2026-03-24 | Docs | docs: SDD PLATFORM_MAP.md — mapa completo da plataforma WeDOTalent — Task #36 — SDD — PLATFORM_MAP da plataforma WeDOTalent | `docs/PLATFORM_MAP.md` |

### Task #55

- **Commits:** 5  |  **Período:** 2026-03-28 → 2026-03-28  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×4 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `237cf2198` | 2026-03-28 | Frontend (UI) | Task #55: Eliminate all unsafe `any` in non-monolith files — Orchestrated 7 parallel subagents across two rounds to apply type-safe | `plataforma-lia/src/components/charts/advanced-interactive-charts.tsx`<br>`plataforma-lia/src/components/charts/interactive-charts.tsx` |
| 🟡 | `7016f3b54` | 2026-03-28 | Frontend (UI) | Task #55: Eliminate unsafe `any` in non-monolith files — Orchestrated 5 parallel subagents to apply type-safe narrowing across | `plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`<br>`plataforma-lia/src/components/charts/advanced-interactive-charts.tsx`<br>`plataforma-lia/src/components/charts/interactive-charts.tsx` |
| 🟡 | `a2a5d5cb2` | 2026-03-28 | Frontend (UI) | Task #55: Eliminate unsafe `any` in non-monolith files — Scope: services (14 files), lib (4 files), hooks (9+3 test files), | `plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`<br>`plataforma-lia/src/components/charts/advanced-interactive-charts.tsx`<br>`plataforma-lia/src/components/charts/interactive-charts.tsx` |
| 🟡 | `4d2c8138e` | 2026-03-28 | Frontend (UI) | Task #55: Eliminate unsafe `any` in non-monolith files — Scope: services (14 files), lib (4 files), hooks (9+3 test files), | `plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`<br>`plataforma-lia/src/components/charts/advanced-interactive-charts.tsx`<br>`plataforma-lia/src/components/charts/interactive-charts.tsx` |
| 🔴 | `c54c0e87d` | 2026-03-28 | Frontend (UI) | Task #55: Eliminate unsafe `any` in non-monolith files — Scope: services (14 files), lib (4 files), hooks (9+3 test files), | `plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`<br>`plataforma-lia/src/components/charts/advanced-interactive-charts.tsx`<br>`plataforma-lia/src/components/charts/interactive-charts.tsx` |

### Task #96

- **Commits:** 5  |  **Período:** 2026-04-02 → 2026-04-02  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×3 🟢×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `aa44c367d` | 2026-04-02 | Frontend (UI) | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Added new design tokens to design-tokens.css and tailwind.config.ts: | `plataforma-lia/src/components/pages/job-kanban/KanbanPageModals.tsx`<br>`plataforma-lia/src/components/sidebar.tsx` |
| 🟡 | `c7b1b18cc` | 2026-04-02 | Frontend (UI) | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Added new design tokens to design-tokens.css and tailwind.config.ts: | `plataforma-lia/src/app/admin/layout.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanPageModals.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/TestLibraryModal.tsx` |
| 🟢 | `8bd044060` | 2026-04-02 | Empty/merge | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Added new design tokens: lia-overlay, lia-overlay-light, lia-bg-inverse, | — |
| 🟡 | `7671ac38e` | 2026-04-02 | Frontend (UI) | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Added new design tokens: lia-overlay, lia-overlay-light, lia-bg-inverse, | `plataforma-lia/src/app/admin/layout.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanPageModals.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/TestLibraryModal.tsx` |
| 🟡 | `e52bccbeb` | 2026-04-02 | Frontend (UI) | Task #96: Migração tokens contraste — Etapa 2: Páginas Principais e Layouts — Migrados todos os 10 arquivos-alvo substituindo classes Tailwind hardcoded | `plataforma-lia/src/app/admin/layout.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanJobHeader.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanPageModals.tsx` |

### Tasks #494-#570 (WSI/BYOK/Persona fundações)

**Descrição:** Tasks da janela de fundações WSI + BYOK + Persona (494-570). Inclui escala WSI 0-10, ADR-018 BYOK, persona diagnostic, canonical-fix skill.

**⚠️ Dependências para cherry-pick:** Ver §15 WSI / §14 BYOK / §16 LIA Persona — fundações já mergeadas em main

**Arquivos canônicos:** Diversos — depende da task específica

**Docs de referência:** BRANCH_MAP — Janela 3

- **Commits:** 5  |  **Período:** 2026-04-18 → 2026-04-20  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🟢×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `2bf526354` | 2026-04-20 | Cross IA↔Back | Task #552: Echo routed specialist on chat replies — The persona-diagnostic routing audit (Task #537) populates `agent_observed` | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🟢 | `3d6328f02` | 2026-04-20 | Testes | Task #558: Verify per-agent AI billing end-to-end with automated tests — Adds tests/test_per_agent_billing.py covering each agent_type added by | `lia-agent-system/tests/test_per_agent_billing.py` |
| 🔴 | `43e417b0e` | 2026-04-19 | Cross Back↔Front | Fix message actions in unified chat (copy, thumbs) — Task #567: The copy / thumbs / "+" buttons under each LIA message gave | `lia-agent-system/app/domains/sourcing/services/apify_search_service.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` |
| 🟡 | `3de3ce2ba` | 2026-04-19 | Cross IA↔Back | Extend AI cost tracking across LIA strategic flows (task #545) — Task #532 only instrumented WSI Layer 2. This change wires per-company | `lia-agent-system/app/api/v1/automation/event_handlers/handlers_interview.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_screening.py`<br>`lia-agent-system/app/api/v1/lia_assistant/wizard.py` |
| 🟢 | `9ca587a51` | 2026-04-18 | Docs | Task #494: Add Regras de Desenvolvimento (OBRIGATORIAS) section to replit.md — Inserted a new section between "User Preferences" and "System Architecture" | `replit.md` |

### scope: candidates

- **Commits:** 5  |  **Período:** 2026-04-16 → 2026-04-17  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×3 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `d378afb1e` | 2026-04-17 | Backend | test(candidates): regression tests for tenant isolation + sanitized errors (#290) — Task #290 asked us to (a) require an authenticated user on | `lia-agent-system/app/api/v1/candidates/candidates_crud.py` |
| 🟡 | `ab5237cd2` | 2026-04-16 | Backend | perf(candidates): acelerar GET /candidates com payload slim + índices — Task #276 — alvo <1s p95. Backend interno agora ~5ms; end-to-end via | `lia-agent-system/alembic/versions/081_candidates_list_perf_indexes.py`<br>`lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/domains/candidates/repositories/candidate_repository.py` |
| 🟢 | `07db52b0f` | 2026-04-16 | Frontend (UI) | fix(candidates): destravar animação "LIA está buscando..." (Task #275) — Complementa Task #274 (transport hardening de searchCandidates/getCandidates) | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesPageCore.tsx` |
| 🟢 | `e175273fb` | 2026-04-16 | Frontend (UI) | fix(candidates): destravar 'Failed to fetch' na listagem e busca — Task #274. Causa-raiz medida: `lib/api/candidate-search.ts:searchCandidates` | `plataforma-lia/src/components/pages/candidates/hooks/useCandidatesExecuteSearch.ts` |
| 🟢 | `3fb09d013` | 2026-04-16 | Frontend (api/util) | fix(candidates): destravar 'Failed to fetch' na listagem e busca — Task #274. Causa-raiz medida: `lib/api/candidate-search.ts:searchCandidates` | `plataforma-lia/src/lib/api/candidate-search.ts`<br>`plataforma-lia/src/services/lia-api/candidates-api.ts` |

### scope: eslint

- **Commits:** 5  |  **Período:** 2026-03-31 → 2026-04-01  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×2 🟢×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `a1e4ab982` | 2026-04-01 | Frontend (UI) | fix(eslint): resolve remaining errors — 0 errors target achieved | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/components/activity-feed.tsx`<br>`plataforma-lia/src/components/autonomous/proactive-actions-bell.tsx` |
| 🔴 | `71ca5412f` | 2026-04-01 | Frontend (UI) | fix(eslint): wrap JSX comment text nodes — 61 react/jsx-no-comment-textnodes errors → 0 | `plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/lgpd/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/conformidade/page.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx` |
| 🟢 | `5a8b47afc` | 2026-04-01 | Frontend (UI) | fix(eslint): 3 erros eliminados — nested useEffect + imports PauseOptionsStep/ActivateOptionsStep — - useExpandedChatProactiveHandlers.ts: salary benchmark useEffect estava aninhado | `plataforma-lia/src/components/expanded-chat/hooks/useExpandedChatProactiveHandlers.ts`<br>`plataforma-lia/src/components/modals/job-status-modal.tsx` |
| 🟢 | `485e37085` | 2026-03-31 | Frontend (UI) | fix(eslint): 0 errors - duplicate className, JSX comments, IIFE, useMemo guard (final) | `plataforma-lia/src/components/pages/candidates/LIASearchSidebar.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx`<br>`plataforma-lia/src/components/triagem-details-modal.tsx` |
| 🟡 | `0f02bc88d` | 2026-03-31 | Frontend (UI) | fix(eslint): 0 errors - merge duplicate className props, prefer-const, useMemo guard | `plataforma-lia/src/components/chat/ChatContextPanelPart1.tsx`<br>`plataforma-lia/src/components/modals/english-test-modal.tsx`<br>`plataforma-lia/src/components/modals/technical-test-modal.tsx` |

### scope: fluxo-alpha1

- **Commits:** 5  |  **Período:** 2026-04-20 → 2026-04-21  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×5

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `98b50dd82` | 2026-04-21 | Empty/merge | docs(fluxo-alpha1): add CT-ML (11 layers) + CT-CHANGELOG Q1–Q2/2026 (Task #714) — FLUXO_TECNICO_COMPLETO_ALPHA1.md (2500 → 2689 lines). | — |
| 🟢 | `fad9b239e` | 2026-04-21 | Docs | docs(fluxo-alpha1): add CT-ML (11 layers) + CT-CHANGELOG Q1–Q2/2026 (Task #714) — FLUXO_TECNICO_COMPLETO_ALPHA1.md (2500 → 2689 lines). | `plataforma-lia/docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md`<br>`replit.md` |
| 🟢 | `4ca80834f` | 2026-04-21 | Empty/merge | docs(fluxo-alpha1): add E10–E16 + CT (Chat Unified) + 16-stage status table — Task #713 — documentação-only. Expande | — |
| 🟢 | `28e67f22a` | 2026-04-21 | Docs | docs(fluxo-alpha1): add E10–E16 + CT (Chat Unified) + 16-stage status table (Task #713) | `plataforma-lia/docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md`<br>`replit.md` |
| 🟢 | `694561e28` | 2026-04-20 | Docs | docs(fluxo-alpha1): add E0 chapter — AI architecture (cognitive layer) — Task #711: insert new chapter E0 'ARQUITETURA DE IA (CAMADA COGNITIVA)' | `plataforma-lia/docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md`<br>`replit.md` |

### Backend Migrations (alembic)

**Descrição:** Migrations alembic do FastAPI — schema changes para companies/jobs/candidates. Inclui fix default_languages ARRAY→JSONB.

**⚠️ Dependências para cherry-pick:** Coordenar com `alembic upgrade head` no staging | downgrade testado

**Arquivos canônicos:** lia-agent-system/alembic/versions/**, lia-agent-system/db/migrations/**

**Docs de referência:** —

- **Commits:** 4  |  **Período:** 2026-04-10 → 2026-04-15  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×3 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `cf3585177` | 2026-04-15 | Empty/merge | fix: resolve default_languages column type mismatch (ARRAY→JSONB) — The company_culture_profiles.default_languages column is jsonb in the DB | — |
| 🟡 | `bc4c04b52` | 2026-04-13 | Backend | feat: Close all production gaps — migrations, triggers, metering, history — Migration 070: agent_deployments table with check constraints + unique index | `lia-agent-system/alembic/versions/070_agent_deployments.py`<br>`lia-agent-system/alembic/versions/071_agent_execution_logs.py`<br>`lia-agent-system/app/api/v1/automation/triggers.py` |
| 🟡 | `d331029ea` | 2026-04-12 | Backend | feat: GAP 8 — schema migration + runtime connection — Model changes (3 new fields on custom_agents): | `lia-agent-system/alembic/versions/069_agent_studio_parity_fields.py`<br>`lia-agent-system/app/api/v1/custom_agents.py`<br>`lia-agent-system/libs/models/lia_models/custom_agent.py` |
| 🟡 | `465751df3` | 2026-04-10 | Backend | Add new tables for onboarding and WhatsApp sessions — Add `onboarding_agent_state` and `whatsapp_sessions` tables to the database schema using Alembic mig | `lia-agent-system/alembic/versions/061_create_onboarding_tables.py` |

### Communication domain (BE)

**Descrição:** Domínio de comunicação — email, WhatsApp, push, templates, communication_tools.

**⚠️ Dependências para cherry-pick:** Templates locale-aware | Tool retorna success: false em DB failures (não silent mock)

**Arquivos canônicos:** lia-agent-system/app/domains/communication/**

**Docs de referência:** DEVELOPER_HANDOFF C1.4

- **Commits:** 4  |  **Período:** 2026-04-04 → 2026-04-19  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `94aba8ebe` | 2026-04-19 | Cross IA↔Back | Update system to properly expose tool handlers and improve robustness — Refactors service layer to expose module-level wrappers for chat tool handlers, enhances cancellatio | `lia-agent-system/app/api/v1/whatsapp_webhook.py`<br>`lia-agent-system/app/domains/analytics/services/job_analytics_prompt_service.py`<br>`lia-agent-system/app/domains/analytics/services/job_insights_service.py` |
| 🟡 | `8587bc041` | 2026-04-12 | Backend | fix: add missing COMMUNICATION_DOMAIN_SPECIFIC import | `lia-agent-system/app/domains/communication/agents/communication_react_agent.py` |
| 🟡 | `edab76285` | 2026-04-08 | Backend | refactor: extract inline models and DRY communication_service (-351 lines) — - Extract 4 SQLAlchemy models to communication_models.py (263 lines) | `lia-agent-system/app/domains/communication/repositories/communication_repository.py`<br>`lia-agent-system/app/domains/communication/services/communication_models.py`<br>`lia-agent-system/app/domains/communication/services/communication_service.py` |
| 🟡 | `70ec8fd8d` | 2026-04-04 | Backend | Add smart routing to direct users to the platform interface — Introduce a smart routing system that analyzes user messages to detect intents requiring platform in | `lia-agent-system/app/domains/communication/services/teams_card_renderer.py`<br>`lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py`<br>`lia-agent-system/app/domains/communication/services/teams_simple.py` |

### Docs / BRANCH_MAP nav

**Descrição:** Atualizações ao BRANCH_MAP.md — índice canônico de temas e milestones.

**⚠️ Dependências para cherry-pick:** BRANCH_MAP.md atualizado a cada PR mergeado em branch de sprint

**Arquivos canônicos:** lia-agent-system/docs/BRANCH_MAP.md

**Docs de referência:** BRANCH_MAP.md

- **Commits:** 4  |  **Período:** 2026-04-27 → 2026-04-27  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `3ba00563a` | 2026-04-27 | Docs | docs(nav): BRANCH_MAP — indice rapido + secao IA-friendly + 4 templates de prompt + cross-refs aos 24 docs canonicos + apendices A/B/C | `lia-agent-system/docs/BRANCH_MAP.md` |
| 🟢 | `7795e6f29` | 2026-04-27 | Docs | docs(nav): BRANCH_MAP — estender com Tasks #574-#712 (janela anterior em main) + 7 milestones novos | `lia-agent-system/docs/BRANCH_MAP.md` |
| 🟢 | `412e8c427` | 2026-04-27 | Docs | docs(nav): BRANCH_MAP — link aos 3 docs LIA Maturity recuperados | `lia-agent-system/docs/BRANCH_MAP.md` |
| 🟢 | `94277b170` | 2026-04-27 | Docs | docs(nav): BRANCH_MAP.md — mapa de branches, milestones e temas para o time | `lia-agent-system/docs/BRANCH_MAP.md` |

### Offer Review (PR-B)

**Descrição:** Offer Review Modal — HITL two-step (idle→confirming→success/error) + user_confirmation. OfferHITLBanner com role=alert. aria-invalid no campo salário quando over-budget. Reset/devtools store. useOfferReviewFlow hook chama offersApi.createDraft + setDraft + setOpen. 4 proxy routes.

**⚠️ Dependências para cherry-pick:** Modal ≤250 linhas | offersApi via /api/backend-proxy (não FastAPI direta) | Zustand devtools | event lia:open_offer_review escutado

**Arquivos canônicos:** plataforma-lia/src/components/offer-review-modal/*, src/stores/offer-draft-store.ts, src/hooks/offers/useOfferReviewFlow.ts

**Docs de referência:** BRANCH_MAP §4 Wave 5 sensors / OfferReviewModal.test.tsx (18/18)

- **Commits:** 4  |  **Período:** 2026-04-19 → 2026-04-28  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×2 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `6916d13b4` | 2026-04-28 | Testes | test: offer modal HITL two-step test fixes (18/18 passing) | `plataforma-lia/src/components/offer-review-modal/__tests__/OfferReviewModal.test.tsx` |
| 🟡 | `4e6374302` | 2026-04-28 | Frontend (UI) | feat(offer): Wave 5 sensors — HITL banner, aria-invalid, reset/devtools, flow — - OfferHITLBanner.tsx: novo componente com role=alert (WCAG 2.1 AA Guard 8) | `plataforma-lia/src/components/offer-review-modal/OfferDataForm.tsx`<br>`plataforma-lia/src/components/offer-review-modal/OfferHITLBanner.tsx`<br>`plataforma-lia/src/components/offer-review-modal/OfferReviewModal.tsx` |
| 🟢 | `b1e0cf615` | 2026-04-27 | Frontend (UI) | style(offer-modal): apply DS v4.2.2 compliance fixes — P0: max-w-3xl → max-w-6xl (prohibited size, 2-col modal = XXL) | `plataforma-lia/src/components/offer-review-modal/JobDataPanel.tsx`<br>`plataforma-lia/src/components/offer-review-modal/OfferDataForm.tsx`<br>`plataforma-lia/src/components/offer-review-modal/OfferReviewModal.tsx` |
| 🟡 | `631cdf978` | 2026-04-19 | Backend | fix eval CO-002: add offer letter generation instruction to communication domain | `lia-agent-system/app/prompts/domains/communication.yaml` |

### Sprint 4.10

- **Commits:** 4  |  **Período:** 2026-03-28 → 2026-03-28  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×2 🔴×1 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `e65cda8d4` | 2026-03-28 | Frontend (UI) | Sprint 4.10 + 4.11 — console.log removal e splits chat/candidates — - Remove console.log/error/warn de ~688 arquivos (Sprint 4.10 residual) | `plataforma-lia/src/app/aceitar-convite/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/automacoes/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/comunicacoes/page.tsx` |
| 🟢 | `835a58bbd` | 2026-03-28 | Docs | docs: atualiza inventário de componentes pós-Sprint 4.10 — Reflete estado atual: Fases 0–3 concluídas, Fase 4 em andamento | `docs/specs/frontend/INVENTARIO_COMPONENTES.md` |
| 🟡 | `72996aed7` | 2026-03-28 | Frontend (UI) | Sprint 4.10 residual — Remoção de style={} inline: tokens DS v4.2.1 — Substitui últimos rgba() e style={{}} hardcoded por tokens Tailwind em 9 componentes | `plataforma-lia/src/components/modals/general-score-modal.tsx`<br>`plataforma-lia/src/components/modals/technical-test-modal.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidateTableCellRenderer.tsx` |
| 🟡 | `23d879d0b` | 2026-03-28 | Frontend (UI) | Sprint 4.10 — DS tokens, type safety e dark mode — - EditArchetypeModal: removidos 5 rgba() inline → bg-wedo-cyan/15, bg-wedo-cyan/8, border-wedo-cyan/ | `plataforma-lia/src/app/globals.css`<br>`plataforma-lia/src/components/expanded-chat/hooks/useSendMessageHandlers.ts`<br>`plataforma-lia/src/components/pages/candidates/hooks/useCandidatesLIAHandlers.ts` |

### Task #112

- **Commits:** 4  |  **Período:** 2026-04-04 → 2026-04-10  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `ae85d2b23` | 2026-04-10 | Frontend (UI) | Task #112: Frontend Production Hardening — Deploy Blockers — Changes made: | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidateProfileTab.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx` |
| 🔴 | `79095dd08` | 2026-04-04 | Cross Back↔Front | Task #112+#113: @ts-ignore elimination + lazy loading + bugfixes — Task #112 - @ts-ignore elimination (11 files clean): | `lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/domains/communication/services/teams_card_renderer.py`<br>`plataforma-lia/src/components/candidate-preview.tsx` |
| 🟡 | `bbd6738b9` | 2026-04-04 | Backend | Task #112: Complete @ts-ignore batch 2 elimination (10/10 files clean) Task #113: Implement lazy loading + code splitting for heavy components — Task #112: | `lia-agent-system/app/api/v1/lia_assistant.py` |
| 🔴 | `1e1e9971a` | 2026-04-04 | Cross Back↔Front | Task #112: Complete @ts-ignore batch 2 elimination (10/10 files clean) Task #113: Implement lazy loading + code splitting for heavy components — Task #112: | `lia-agent-system/app/api/v1/lia_assistant.py`<br>`lia-agent-system/app/api/v1/teams.py`<br>`lia-agent-system/app/domains/communication/services/teams_card_renderer.py` |

### Task #12

- **Commits:** 4  |  **Período:** 2026-04-05 → 2026-04-05  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×3 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `7e3d7ae56` | 2026-04-05 | Frontend (UI) | Task #12: Split-Screen Dinâmico — full panel_update wiring across all chat surfaces — T003: WebSocket panel_update event handling | `plataforma-lia/src/components/pages/chat-page/chat-core/useChatSession.ts` |
| 🟢 | `145716afe` | 2026-04-05 | Frontend (UI) | Task #12: Split-Screen Dinâmico — full panel_update wiring across all chat surfaces — T003: WebSocket panel_update event handling | `plataforma-lia/src/components/pages/chat-page/chat-core/useChatSession.ts` |
| 🟢 | `dc162a9b6` | 2026-04-05 | Frontend (UI) | Task #12: Split-Screen Dinâmico — T003/T004/T005 complete — T003: WebSocket panel_update event handling | `plataforma-lia/src/components/lia-float/panels/CalibrationPanel.tsx`<br>`plataforma-lia/src/components/lia-float/panels/CandidateReviewPanel.tsx`<br>`plataforma-lia/src/components/pages/chat-page.tsx` |
| 🔴 | `f30f28f96` | 2026-04-05 | Cross Back↔Front | Task #12: Split-Screen Dinâmico — T003/T004/T005 complete — T003: WebSocket panel_update event handling | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`plataforma-lia/src/components/lia-float/LiaChatPanel.tsx`<br>`plataforma-lia/src/components/lia-float/panels/CalibrationPanel.tsx` |

### Task #131

- **Commits:** 4  |  **Período:** 2026-04-04 → 2026-04-11  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `781b525c7` | 2026-04-11 | Frontend (api/util) | Task #131: LIA Functional Evaluation Suite via Playwright (7 Domains + Resilience) — Comprehensive Playwright evaluation suite testing LIA's AI assistant capabilities | `plataforma-lia/e2e/reports/eval-summary.json`<br>`plataforma-lia/e2e/reports/html/index.html`<br>`plataforma-lia/e2e/tests/lia-capability-eval/analytics-insights.spec.ts` |
| 🟡 | `025b0afce` | 2026-04-11 | Frontend (api/util) | Task #131: LIA Functional Evaluation Suite via Playwright (7 Domains + Resilience) — Created a comprehensive Playwright evaluation suite that tests LIA's real | `plataforma-lia/e2e/tests/lia-capability-eval/analytics-insights.spec.ts`<br>`plataforma-lia/e2e/tests/lia-capability-eval/automation-productivity.spec.ts`<br>`plataforma-lia/e2e/tests/lia-capability-eval/communication.spec.ts` |
| 🟡 | `f5aecbc7d` | 2026-04-11 | Frontend (api/util) | Task #131: LIA Functional Evaluation Suite via Playwright (7 Domains + Resilience) — Created a comprehensive Playwright evaluation suite that tests LIA's real | `plataforma-lia/e2e/tests/lia-capability-eval/analytics-insights.spec.ts`<br>`plataforma-lia/e2e/tests/lia-capability-eval/automation-productivity.spec.ts`<br>`plataforma-lia/e2e/tests/lia-capability-eval/communication.spec.ts` |
| 🔴 | `2138880c9` | 2026-04-04 | Backend | Task #131: Consolidate email providers — Mailgun primary, Resend fallback via composite, SendGrid removed — Key deliverables: | `lia-agent-system/app/api/v1/communication.py`<br>`lia-agent-system/app/api/v1/communication_settings.py`<br>`lia-agent-system/app/api/v1/communications.py` |

### Task #153

- **Commits:** 4  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `0db172dcd` | 2026-04-11 | IA | Task #153 final: Per-request cost tracking wired end-to-end + retrieval tests — 1. LLMCascade: Wire request_id through all route() paths (preferred, flash, | `lia-agent-system/app/orchestrator/llm_cascade.py` |
| 🟡 | `364b8bf9c` | 2026-04-11 | Cross IA↔Back | Task #153 final fixes: Wire per-request cost tracking end-to-end — 1. LLMCascade: Wire request_id through all route() call paths (preferred, | `lia-agent-system/app/orchestrator/llm_cascade.py` |
| 🟡 | `778721272` | 2026-04-11 | Backend | Task #153: Guardrails Per-Request + RAG Semantic Chunking — Per-request cost tracking: | `lia-agent-system/alembic/versions/065_add_request_id_cost_to_audit_metadata.py` |
| 🟡 | `bb344d222` | 2026-04-11 | Cross IA↔Back | Task #153: Guardrails Per-Request + RAG Semantic Chunking — Per-request cost tracking: | `lia-agent-system/alembic/versions/065_add_request_id_cost_to_audit_metadata.py`<br>`lia-agent-system/app/orchestrator/tenant_budget.py` |

### Task #158

- **Commits:** 4  |  **Período:** 2026-04-12 → 2026-04-12  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `9bd173c0f` | 2026-04-12 | Cross IA↔Back | Task #158: Module-Aware Middleware + Premium Tool Gating — Fail-closed module gating for all premium tools: | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `7af3eb2d8` | 2026-04-12 | Backend | Task #158: Module-Aware Middleware + Premium Tool Gating — Implemented fail-closed module gating for premium tools: | `lia-agent-system/app/shared/tool_handler.py`<br>`lia-agent-system/tests/unit/test_module_gating.py` |
| 🟡 | `9013ced8a` | 2026-04-12 | Cross IA↔Back | Task #158: Module-Aware Middleware + Premium Tool Gating — Implemented fail-closed module gating infrastructure for premium tools: | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| 🟡 | `6c092ea51` | 2026-04-12 | Backend | Task #158: Module-Aware Middleware + Premium Tool Gating — Implemented fail-closed module gating infrastructure for premium tools: | `lia-agent-system/app/domains/talent_intelligence/tools/candidate_nurture_tools.py`<br>`lia-agent-system/app/domains/talent_intelligence/tools/internal_mobility_tools.py`<br>`lia-agent-system/app/domains/talent_intelligence/tools/interview_intelligence_tools.py` |

### Task #160

- **Commits:** 4  |  **Período:** 2026-04-12 → 2026-04-12  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `3e6a0ab12` | 2026-04-12 | Cross IA↔Back | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/chat/repositories/chat_repository.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py` |
| 🟡 | `ab0824c32` | 2026-04-12 | IA | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: | `lia-agent-system/app/orchestrator/tasting_engine.py` |
| 🟡 | `4145d3ba4` | 2026-04-12 | IA | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: | `lia-agent-system/app/orchestrator/tasting_engine.py` |
| 🔴 | `b945f3bb7` | 2026-04-12 | Cross IA↔Front | feat(task-160): Degustação Inteligente no Chat da LIA — Backend: | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/tasting_engine.py`<br>`plataforma-lia/src/components/unified-chat/TastingInsightCard.tsx` |

### Task #19

- **Commits:** 4  |  **Período:** 2026-03-16 → 2026-03-16  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `2afc0743f` | 2026-03-16 | Empty/merge | Task #19: Major revision of Catalogo Produtos/Servicos/CNAEs — WeDOTalent — Deep codebase analysis + corrections based on actual code: | — |
| 🟢 | `c630b2849` | 2026-03-16 | Empty/merge | Task #19: Major revision of Catalogo Produtos/Servicos/CNAEs — WeDOTalent — Deep codebase analysis revealed significant discrepancies. All corrected: | — |
| 🟢 | `d9c4e07bb` | 2026-03-16 | Empty/merge | Task #19: Catálogo de Produtos, Serviços, Especificações Técnicas e CNAEs — WeDOTalent — Created comprehensive document (~670 lines) at: | — |
| 🟢 | `625cc29f8` | 2026-03-16 | Empty/merge | Task #19: Catálogo de Produtos, Serviços, Especificações Técnicas e CNAEs — WeDOTalent — Created comprehensive document (620 lines) at: | — |

### Task #2

- **Commits:** 4  |  **Período:** 2026-04-05 → 2026-04-05  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×3 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `8cfebd222` | 2026-04-05 | Frontend (UI) | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real API calls | `plataforma-lia/src/components/daily-briefing-card.tsx`<br>`plataforma-lia/src/components/pages/task-helpers.tsx`<br>`plataforma-lia/src/components/pages/tasks-page.tsx` |
| 🔴 | `f04070006` | 2026-04-05 | Cross Back↔Front | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real API calls | `plataforma-lia/src/app/api/backend-proxy/tasks/[taskId]/cancel/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/tasks/[taskId]/complete/route.ts`<br>`plataforma-lia/src/components/pages/use-tasks-core.ts` |
| 🔴 | `3621573ba` | 2026-04-05 | Cross Back↔Front | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real API calls | `plataforma-lia/src/app/api/backend-proxy/briefing/route.ts`<br>`plataforma-lia/src/components/pages/use-tasks-core.ts` |
| 🔴 | `b9af19951` | 2026-04-05 | Cross Back↔Front | Task #2: Connect Tarefas page to real backend APIs — - Replaced all hardcoded mock data with real API calls | `lia-agent-system/app/api/v1/ai_consumption.py`<br>`lia-agent-system/app/api/v1/audit_logs.py`<br>`lia-agent-system/app/api/v1/compliance_controls.py` |

### Task #21

- **Commits:** 4  |  **Período:** 2026-03-18 → 2026-03-18  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×2 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `f57e8e836` | 2026-03-18 | Empty/merge | Task #21: Análise Comparativa Completa LIA vs recruiter_agent_v5 (v4 final) — Arquivo: attached_assets/Analise_Comparativa_LIA_vs_V5_Completo.md (1.223 linhas, 70KB+) | — |
| 🟢 | `cda47f452` | 2026-03-18 | Empty/merge | Task #21: Análise Comparativa Completa LIA vs recruiter_agent_v5 (v3 final) — Arquivo: attached_assets/Analise_Comparativa_LIA_vs_V5_Completo.md | — |
| 🟡 | `321b7a534` | 2026-03-18 | Outro | Task #21: Análise Comparativa Completa LIA vs recruiter_agent_v5 (revisado) — Arquivo: attached_assets/Analise_Comparativa_LIA_vs_V5_Completo.md | `analise comparativa lia v5 completo` |
| 🟡 | `0bd54fa6b` | 2026-03-18 | Outro | Task #21: Análise Comparativa Completa LIA vs recruiter_agent_v5 — Criado: attached_assets/Analise_Comparativa_LIA_vs_V5_Completo.md | `analise comparativa lia v5 completo` |

### Task #25

- **Commits:** 4  |  **Período:** 2026-03-19 → 2026-03-19  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `9c8d70018` | 2026-03-19 | Docs | Task #25 — Mapeamento capacidades prompts LIA × v5 (v4.0 final) — DOCUMENTO: proposals/mapeamento_capacidades_prompts_lia.md (1084 linhas, 53 seções) | `proposals/mapeamento_capacidades_prompts_lia.md` |
| 🟢 | `ebbc0fce2` | 2026-03-19 | Docs | Task #25 — Mapeamento capacidades prompts LIA × v5 (v3.0 final) — DOCUMENTO: proposals/mapeamento_capacidades_prompts_lia.md (761 linhas, 45 seções) | `proposals/mapeamento_capacidades_prompts_lia.md` |
| 🟢 | `014d3d604` | 2026-03-19 | Docs | Task #25 — Mapeamento capacidades prompts LIA × v5 (v2.0 corrigida) — DOCUMENTO: proposals/mapeamento_capacidades_prompts_lia.md (941 linhas, 51 seções) | `proposals/mapeamento_capacidades_prompts_lia.md` |
| 🟢 | `6b4f72dd5` | 2026-03-19 | Docs | Task #25 — Mapeamento completo de capacidades dos prompts LIA × v5 — DOCUMENTO CRIADO: proposals/mapeamento_capacidades_prompts_lia.md (1.242 linhas, 73 seções) | `proposals/mapeamento_capacidades_prompts_lia.md` |

### Task #30

- **Commits:** 4  |  **Período:** 2026-03-21 → 2026-04-06  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `8f7248a45` | 2026-04-06 | Frontend (UI) | Task #30: Unificar padrão visual de todos os chats LIA — Created shared ChatBubbleBase component and refactored all 4 chat | `plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/chat/chat-bubble-base.tsx`<br>`plataforma-lia/src/components/chat/message-bubble.tsx` |
| 🟡 | `059ef71e8` | 2026-03-21 | Backend | Task #30: Fix 3 issues apontados pelo code review — ## Fixes aplicados | `lia-agent-system/scripts/bug_spec_generator.py`<br>`lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `44e1c040c` | 2026-03-21 | Backend | Task #30: Scripts auditoria determinísticos + re-auditoria WT-1633/34/35/36 — ## O que foi feito | `lia-agent-system/scripts/bug_spec_generator.py`<br>`lia-agent-system/scripts/design_audit_generator.py` |
| 🟡 | `327692691` | 2026-03-21 | Backend | Task #30: Scripts auditoria determinísticos + re-auditoria WT-1633/34/35/36 — ## O que foi feito | `lia-agent-system/scripts/bug_spec_generator.py`<br>`lia-agent-system/scripts/design_audit_generator.py` |

### Task #40

- **Commits:** 4  |  **Período:** 2026-03-24 → 2026-04-06  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `288c119f1` | 2026-04-06 | Backend | Task #40: Credits — Full billing infrastructure — Models (billing.py): | `lia-agent-system/app/api/v1/candidate_search/core_search.py` |
| 🔴 | `fdc03b5a4` | 2026-04-06 | Cross Back↔Front | Task #40: Credits — Full billing infrastructure — Models (billing.py): | `lia-agent-system/app/api/v1/ats.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py`<br>`lia-agent-system/app/api/v1/credits.py` |
| 🟡 | `a16ac44de` | 2026-03-25 | Backend | Task #40: F11 Report Engine — Final fixes and HTTP 422 hard block — Changes in this session (completing Task #40 from previous sessions): | `lia-agent-system/app/api/v1/wsi.py` |
| 🟡 | `655a0ae66` | 2026-03-24 | Backend | Task #40: F11 Report — Endpoint GET + G1-G6 Gates + SHA-256 + CBI + JD Evaluate — ## Changes in this session (completing previously-started work) | `lia-agent-system/app/api/v1/wsi.py` |

### Task #44

- **Commits:** 4  |  **Período:** 2026-03-25 → 2026-04-06  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×3 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `53f970159` | 2026-04-06 | Frontend (UI) | Task #44: UI parity — add ContextBadge, HITLConfirmCard, PlanProgressCard, dynamic suggestions across chat interfaces — Changes: | `plataforma-lia/src/components/candidate-preview/LiaChatModal.tsx`<br>`plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/expanded-chat/components/ChatMessageList.tsx` |
| 🟢 | `ae3f2623a` | 2026-03-26 | Docs | Task #44: Inventário Completo de Design — Plataforma LIA — Comprehensive design inventory document (1995 lines) covering 100% of UI: | `docs/PRODUCT_DESIGN_INVENTORY.md` |
| 🟢 | `f7598fc88` | 2026-03-25 | Docs | Task #44: Inventário Completo de Design — Plataforma LIA (área operacional) — Expanded docs/PRODUCT_DESIGN_INVENTORY.md from 948 to 1846 lines with full | `docs/PRODUCT_DESIGN_INVENTORY.md` |
| 🟢 | `41c2ac318` | 2026-03-25 | Docs | Task #44: Inventário Completo de Design — Plataforma LIA (área operacional) — Created comprehensive design inventory document at docs/PRODUCT_DESIGN_INVENTORY.md | `docs/PRODUCT_DESIGN_INVENTORY.md` |

### Task #83

- **Commits:** 4  |  **Período:** 2026-03-31 → 2026-04-09  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `06f5391e2` | 2026-04-09 | Docs | Task #83: Deep design audit — AUDITORIA_DESIGN_COMPLETA.md — Complete audit of all 17 pages, 13+ shared components, design tokens, | `plataforma-lia/docs/AUDITORIA_DESIGN_COMPLETA.md` |
| 🟢 | `be98d2dd3` | 2026-04-09 | Docs | Task #83: Deep design audit — AUDITORIA_DESIGN_COMPLETA.md — Complete audit of all 13 pages, 13+ shared components, design tokens, | `plataforma-lia/docs/AUDITORIA_DESIGN_COMPLETA.md`<br>`plataforma-lia/docs/screenshots/chat-page.jpg` |
| 🟢 | `ea280ed2e` | 2026-04-09 | Docs | Task #83: Deep design audit — AUDITORIA_DESIGN_COMPLETA.md — Complete audit of all 7 pages, 13+ shared components, design tokens, | `plataforma-lia/docs/AUDITORIA_DESIGN_COMPLETA.md` |
| 🟢 | `280d7e671` | 2026-03-31 | Docs | Task #83: Expand FLUXO_TECNICO_COMPLETO_ALPHA1.md with complete file listing and transversal layer details — Added two major new sections to docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md (+650 lines): | `artifacts/mockup-sandbox/src/.generated/mockup-components.ts`<br>`docs/specs/FLUXO_TECNICO_COMPLETO_ALPHA1.md` |

### Task #98

- **Commits:** 4  |  **Período:** 2026-04-02 → 2026-04-02  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×2 🔴×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `f02e873dd` | 2026-04-02 | Docs | Task #98: Migração completa de tokens de contraste — Etapa 4 (Final) — Migração abrangente de ~505+ arquivos restantes no codebase, | `replit.md` |
| 🟢 | `93ef4cf05` | 2026-04-02 | Frontend (UI) | Task #98: Migração completa de tokens de contraste — Etapa 4 (Final) — Migração abrangente de ~505+ arquivos restantes no codebase, | `plataforma-lia/src/app/register/RegisterClient.tsx` |
| 🔴 | `213adc816` | 2026-04-02 | Frontend (UI) | Task #98: Migração completa de tokens de contraste — Etapa 4 (Final) — Migração abrangente de ~505+ arquivos restantes no codebase, | `plataforma-lia/src/app/accept-invitation/AcceptInvitationClient.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/comunicacoes/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/layout.tsx` |
| 🔴 | `fe4b665cb` | 2026-04-02 | Frontend (UI) | Task #98: Migração completa de tokens de contraste — Etapa 4 — Migração abrangente de ~505 arquivos restantes no codebase | `plataforma-lia/src/app/accept-invitation/AcceptInvitationClient.tsx`<br>`plataforma-lia/src/app/access/AccessClient.tsx`<br>`plataforma-lia/src/app/aceitar-convite/AceitarConviteClient.tsx` |

### Vagas Públicas

- **Commits:** 4  |  **Período:** 2026-04-22 → 2026-04-27  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🟢×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `4ebffcc70` | 2026-04-27 | Backend | fix(public-vacancies): restaurar página pública /pt/vagas/[slug] — A URL pública de candidatura (https://.../pt/vagas/product-manager-27304b) | `lia-agent-system/app/api/v1/job_vacancies/public.py`<br>`lia-agent-system/app/api/v1/offers.py` |
| 🟢 | `a043b8c24` | 2026-04-22 | Frontend (UI) | feat(vagas): design + WCAG 2.1 AA + code quality na página pública de vaga — - Design: espaçamentos mobile-first, H1 alinhado ao DS (22px/28px), seções com border-b em vez de 80 | `plataforma-lia/src/app/[locale]/vagas/[slug]/VagasDetailClient.tsx`<br>`plataforma-lia/src/app/[locale]/vagas/[slug]/page.tsx` |
| 🟢 | `99aea7154` | 2026-04-22 | Frontend (UI) | Alinhar página pública de vagas ao Design System (Task #799) — Refatora `plataforma-lia/src/app/[locale]/vagas/[slug]/VagasDetailClient.tsx` | `plataforma-lia/src/app/[locale]/vagas/[slug]/VagasDetailClient.tsx` |
| 🟡 | `73c7ff712` | 2026-04-22 | Backend | Tarefa #798 — Enriquecer vaga pública Product Manager — Permite visualizar /pt/vagas/product-manager-27304b com todas as seções | `lia-agent-system/app/api/v1/job_vacancies/public.py` |

### scope: lia

- **Commits:** 4  |  **Período:** 2026-04-17 → 2026-04-21  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `ba2f32436` | 2026-04-21 | Backend | fix(lia): Init IV plural — "açãoões" → "ações" no briefing PT — Runtime audit caught cosmetic PT pluralization bug in briefing formatter: | `lia-agent-system/app/domains/recruiter_assistant/services/lia_briefing_formatter.py` |
| 🟡 | `dfedcb357` | 2026-04-21 | Backend | feat(lia): Initiative I.A — Grounded Capability Catalog (16 cards + CI guard) — Track 2 Initiative I (Grounded Capability System) — catalog layer. | `lia-agent-system/app/prompts/catalog/capability_cards.yaml`<br>`lia-agent-system/tests/unit/test_initI_capability_cards.py` |
| 🔴 | `9c7385973` | 2026-04-17 | Cross IA↔Front | fix(lia): Fix5+6 agentic tool auth + main chat 422 | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`plataforma-lia/src/app/api/backend-proxy/chat/route.ts` |
| 🟡 | `559a40da3` | 2026-04-17 | IA | fix(lia): 4 surgical fixes for LIA chat bugs — - navigation_intent.py: Add missing 'Indicadores' page patterns (BUG-NAV-10.4) | `lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |

### scope: tests

- **Commits:** 4  |  **Período:** 2026-04-07 → 2026-04-07  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `0e523f63a` | 2026-04-07 | Cross IA↔Back | fix(tests): fix Redis isolation, agent_health tests, shim exports, lia_config import — - Fix _make_service() in test_agent_health_alert_service to patch _get_redis properly | `lia-agent-system/app/api/v1/automation/event_handlers/__init__.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_ats_sync.py`<br>`lia-agent-system/app/api/v1/automation/event_handlers/handlers_interview.py` |
| 🟡 | `68212c8f7` | 2026-04-07 | Backend | fix(tests): fix agent domain_name setter, function signatures, and missing exports — - Add domain_name setter to 8 agent classes (TalentReActAgent, KanbanReActAgent, etc.) | `lia-agent-system/app/api/v1/candidates/candidates_metadata.py` |
| 🟡 | `f80260f11` | 2026-04-07 | Backend | fix(tests): fix 12 categories of unit test failures — private imports and moved modules — - Add _get_json_type to app/services/structured_output.py shim | `lia-agent-system/app/domains/lgpd/services/lgpd_cleanup_service.py` |
| 🟡 | `edff3aee3` | 2026-04-07 | Cross IA↔Back | fix(tests): fix Redis mock injection in token_budget, toon, and hitl services — - Promote app/services/token_budget_service.py, toon_service.py, and hitl_service.py to be canonical | `lia-agent-system/app/domains/credits/services/token_budget_service.py`<br>`lia-agent-system/app/domains/cv_screening/services/hitl_service.py`<br>`lia-agent-system/app/services/hitl_service.py` |

### scope: ui

- **Commits:** 4  |  **Período:** 2026-04-18 → 2026-04-20  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×2 🟡×1 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `9d0218eb7` | 2026-04-20 | Frontend (UI) | feat(ui): make BETA badge blue, smaller, and with smaller font — Task #649: Deixar badge BETA azul, menor e com fonte menor | `plataforma-lia/src/components/ui/beta-badge.tsx` |
| 🟡 | `206945048` | 2026-04-18 | Frontend (UI) | chore(ui): consolidate legacy badges onto canonical Chip; remove status-badge — Task #461 — finalize the migration from `src/components/ui/status-badge.tsx` | `plataforma-lia/src/app/[locale]/trust/TrustClient.tsx`<br>`plataforma-lia/src/components/autonomous/jobs-dashboard.tsx`<br>`plataforma-lia/src/components/chat/plan-progress-card.tsx` |
| 🔴 | `23b07df5f` | 2026-04-18 | Cross Back↔Front | feat(ui): toolbar canônica para vagas e candidatos (#443) — Cria primitives compartilhadas e tokens para padronizar as 3 toolbars | `plataforma-lia/src/components/pages/job-kanban/KanbanToolbar.tsx`<br>`plataforma-lia/src/components/pages/jobs/JobsHeader.tsx`<br>`plataforma-lia/src/components/ui/toolbar-button.tsx` |
| 🟢 | `dc1c798db` | 2026-04-18 | Frontend (UI) | feat(ui): toolbar canônica para vagas e candidatos (#443) — Cria primitives compartilhadas para padronizar as 3 toolbars que tinham | `plataforma-lia/src/components/pages/JobsListContent.tsx`<br>`plataforma-lia/src/components/pages/job-kanban/KanbanToolbar.tsx`<br>`plataforma-lia/src/components/ui/toolbar-button.tsx` |

### §12 DEVELOPER_HANDOFF — PARTE J

- **Commits:** 4  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×4

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `1c5e9a295` | 2026-04-21 | Docs | docs(handoff): adicionar PARTE J — Onda Benefícios + Departamentos + Workforce — Task #783: documentação-only. | `plataforma-lia/DEVELOPER_HANDOFF_UX_REDESIGN.md` |
| 🟢 | `bd28ddf77` | 2026-04-21 | Docs | docs(handoff): adicionar PARTE J — Onda Benefícios + Departamentos + Workforce — Task #783: documentação-only. | `plataforma-lia/DEVELOPER_HANDOFF_UX_REDESIGN.md` |
| 🟢 | `b43df6ebe` | 2026-04-21 | Docs | docs(handoff): adicionar PARTE J — Onda Benefícios + Departamentos + Workforce — Task #783: documentação-only. | `plataforma-lia/DEVELOPER_HANDOFF_UX_REDESIGN.md` |
| 🟢 | `97ac557f1` | 2026-04-21 | Docs | docs(handoff): PARTE J - A Jornada Completa (narrativa Sessao B com commits reais) — Adiciona narrativa historica das Fases 1-6 da plataforma WeDOTalent LIA ao | `lia-agent-system/docs/DEVELOPER_HANDOFF.md` |

### §4 Rail Features — PR-J

**Descrição:** PR-J: entity_resolver_service + capability_map_service + LIAGlobalModals (FE) + useModalOpenListener hook. Listener global lia:open_offer_review e similares.

**⚠️ Dependências para cherry-pick:** LIAGlobalModals montado em DeferredLayoutClients | useModalOpenListener hook ativo no chat

**Arquivos canônicos:** lia-agent-system/app/services/entity_resolver_service.py, plataforma-lia/src/components/lia-global-modals/LIAGlobalModals.tsx, src/hooks/chat/useModalOpenListener.ts

**Docs de referência:** BRANCH_MAP §4

- **Commits:** 4  |  **Período:** 2026-04-27 → 2026-04-27  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `bdef6961d` | 2026-04-27 | IA | fix(pr-j): read intent_hint from context.metadata (PR-A nesting) — PR-A sends metadata nested under context.metadata.intent_hint. | `lia-agent-system/app/orchestrator/rail_a_capability_check.py` |
| 🟢 | `cbbb9af66` | 2026-04-27 | Frontend (UI) | feat(pr-j): add LIAGlobalModals + useModalOpenListener [FE sprint 3] — - useModalOpenListener(modal_id): hook listening to lia:open_modal CustomEvent | `plataforma-lia/src/components/layout/DeferredLayoutClients.tsx`<br>`plataforma-lia/src/components/lia-global-modals/LIAGlobalModals.tsx` |
| 🟡 | `43802d069` | 2026-04-27 | Cross IA↔Back | feat(pr-j): wire capability_map + entity_resolver into WS handler [BE sprint 2] — - rail_a_capability_check.py: Phase 0.5 gate before any agent invocation | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/rail_a_capability_check.py` |
| 🟡 | `8705ece14` | 2026-04-27 | Cross IA↔Back | feat(pr-j): add EntityResolverService + CapabilityMapService [BE sprint 1] — - capability_map.yaml: declarative guide (feedforward) for 5 Rail A intents | `lia-agent-system/app/config/capability_map.yaml`<br>`lia-agent-system/app/shared/services/capability_map_service.py`<br>`lia-agent-system/app/shared/services/entity_resolver_service.py` |

### Backend (genérico)

- **Commits:** 3  |  **Período:** 2026-03-31 → 2026-04-09  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×2 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `05d5c8ff4` | 2026-04-09 | Cross Back↔Front | feat(backend): Sprint 3 — PATCH /conversations/{id} for rename + wire to UnifiedChat — - Added RenameConversationRequest schema to conversations.py | `lia-agent-system/app/api/v1/conversations.py`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` |
| 🟡 | `f0d3483ad` | 2026-04-09 | Backend | feat(backend): Sprint 2 — Talent Pool REST API (9 endpoints) — Models: | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/talent_pools.py` |
| 🔴 | `c2fd209de` | 2026-03-31 | Cross Back↔Front | fix(backend): Task #74 — Fix 5 backend architecture findings from Fase 6 audit — ARCH-04 (CRITICAL): Added **kwargs to RAGPipelineService.search() signature. | `lia-agent-system/app/domains/sourcing/services/llm_job_classification_service.py`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx`<br>`plataforma-lia/src/components/modals/data-blocking-modal.tsx` |

### Docs / Reconstruction Guides

**Descrição:** Guides de reconstrução — documentação para reproduzir/onboard times novos.

**⚠️ Dependências para cherry-pick:** —

**Arquivos canônicos:** docs/reconstruction-guides/**

**Docs de referência:** —

- **Commits:** 3  |  **Período:** 2026-04-24 → 2026-04-25  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `71b08e0cf` | 2026-04-25 | Backend | Update documentation for system configurations and operational guides — Update various documentation files to reflect expanded canonical YAML bundles and revised operationa | `lia-agent-system/eval/eval_results_20260425_195331.json` |
| 🟢 | `890e2475f` | 2026-04-24 | Docs | Add new candidate-facing API endpoint and tool for decision explanation — Add `/api/v1/candidate/decisions/explain` endpoint and `explain_candidate_decision` tool, incorporat | `docs/reconstruction-guides/INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md`<br>`docs/reconstruction-guides/RESILIENCE_LEARNING_RECONSTRUCTION_GUIDE.md` |
| 🟢 | `2618598fa` | 2026-04-24 | Frontend (api/util) | Update development server to use correct port for Replit preview — Reverts the change that updated the development server port from 5000 to 3000 in package.json, ensur | `plataforma-lia/package.json` |

### Fase 10

- **Commits:** 3  |  **Período:** 2026-03-28 → 2026-03-28  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🔴×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `2a9bb7437` | 2026-03-28 | Frontend (UI) | Task #54: Fase 10 Sprint 1A — DS Consistency complete — Full DS v4.2.1 mechanical alignment across plataforma-lia/src/. | `plataforma-lia/src/app/admin/clientes/[clientId]/workforce/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/lgpd/consentimentos/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/lgpd/page.tsx` |
| 🟢 | `ca50dd156` | 2026-03-28 | Frontend (UI) | Task #54: Fase 10 Sprint 1A — DS Consistency (rounded-md + cores residuais) — Mechanical DS v4.2.1 alignment: CSS class and color value migrations across | `plataforma-lia/src/app/ajuda/page.tsx`<br>`plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx` |
| 🔴 | `cb63551fa` | 2026-03-28 | Frontend (UI) | Task #54: Fase 10 Sprint 1A — DS Consistency (rounded-md + cores residuais) — Mechanical DS v4.2.1 alignment: CSS class and color value migrations across | `plataforma-lia/src/app/admin/clientes/[clientId]/big-five/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/consumo-ia/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/faturamento/page.tsx` |

### Frontend (genérico)

- **Commits:** 3  |  **Período:** 2026-04-26 → 2026-04-26  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `ab29cadf4` | 2026-04-26 | Frontend (UI) | fix(fe): restore daily-briefing-card + disc-assessment-modal (false positives in #9957575f9) — Bug: Build error em Next.js 16 / Turbopack após merge da Task #850: | `plataforma-lia/src/components/daily-briefing-card.tsx`<br>`plataforma-lia/src/components/disc-assessment-modal.tsx` |
| 🟡 | `b8c86f230` | 2026-04-26 | Frontend (UI) | refactor(fe): move 6 misplaced hooks to canonical hooks/ structure — Move hooks from components/ (wrong convention) to hooks/[category]/: | `plataforma-lia/src/components/LiaMetricsDetails.tsx`<br>`plataforma-lia/src/components/LiaMetricsDetailsSection.tsx`<br>`plataforma-lia/src/components/LiaMetricsFunnelSection.tsx` |
| 🟡 | `9957575f9` | 2026-04-26 | Frontend (UI) | chore(fe): remove dead code — 6 orphaned components + workspace litter — Remove 6 React components confirmed with 0 external importers (~3,163 lines): | `plataforma-lia/src/components/LiaMetricsKPIs.tsx`<br>`plataforma-lia/src/components/daily-briefing-card.tsx`<br>`plataforma-lia/src/components/decision-explainer.tsx` |

### Lint / Code Quality

**Descrição:** ESLint rules, tsc exclusions, lint-staged + browserslist, prettier — qualidade de código e CI guards estáticos.

**⚠️ Dependências para cherry-pick:** ESLint config no FE | tsconfig.json correto | lint-staged ativo no pre-commit

**Arquivos canônicos:** plataforma-lia/eslint.config.mjs, plataforma-lia/tsconfig.json, plataforma-lia/package.json (lint-staged)

**Docs de referência:** —

- **Commits:** 3  |  **Período:** 2026-03-30 → 2026-04-22  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `81efb2987` | 2026-04-22 | Frontend (api/util) | Enforce removal of deprecated API route across all TypeScript files — Add ESLint rule to prevent usage of the removed `/api/lia/api` route in any `.ts` or `.tsx` files, r | `plataforma-lia/eslint.config.mjs` |
| 🟢 | `3d0048966` | 2026-03-31 | Frontend (api/util) | fix: exclui test files e exports/ do tsc — remove 1000+ erros de arquivos fora do escopo de prod | `plataforma-lia/tsconfig.json` |
| 🟢 | `349ae02df` | 2026-03-30 | Frontend (api/util) | Add linting and formatting configurations for project files — Add `lint-staged` and `browserslist` configurations to `package.json` for improved code quality and  | `plataforma-lia/package.json` |

### Sprint 4.4

- **Commits:** 3  |  **Período:** 2026-03-27 → 2026-03-27  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `23757c7ab` | 2026-03-27 | Frontend (UI) | Sprint 4.4 — InputEvaluationStage extraído (-116 linhas no modal) — Extração da etapa input-evaluation (critérios detectados, progresso | `plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/expanded-chat/stages/InputEvaluationStage.tsx`<br>`plataforma-lia/src/components/expanded-chat/stages/index.ts` |
| 🟢 | `d91580e94` | 2026-03-27 | Frontend (UI) | Sprint 4.4 — ReviewPublishStage extraído (-610 linhas no modal) — Extração da etapa review-publish (resumo da vaga + plataformas + | `plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/expanded-chat/stages/ReviewPublishStage.tsx`<br>`plataforma-lia/src/components/expanded-chat/stages/index.ts` |
| 🟢 | `959e401df` | 2026-03-27 | Frontend (UI) | Sprint 4.4 — SearchCalibrationStage extraído (-475 linhas no modal) — Extração da etapa search-calibration (3 fases: busca local/global, | `plataforma-lia/src/components/expanded-chat-modal.tsx`<br>`plataforma-lia/src/components/expanded-chat/stages/SearchCalibrationStage.tsx`<br>`plataforma-lia/src/components/expanded-chat/stages/index.ts` |

### Sprint 4.6

- **Commits:** 3  |  **Período:** 2026-03-27 → 2026-03-28  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×2 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `8b730e778` | 2026-03-28 | Frontend (UI) | Sprint 4.6 — Extração de 11 componentes de 3 páginas monolito — jobs-page: -3.309L → ColumnConfigPanel, TableFiltersPanel, InlineChatPanel, JobPreviewPanel | `plataforma-lia/src/components/pages/candidates/CreditConfirmationModal.tsx`<br>`plataforma-lia/src/components/pages/candidates/EditQueryModal.tsx`<br>`plataforma-lia/src/components/pages/candidates/PreviewSuggestionModal.tsx` |
| 🟢 | `809deb4a9` | 2026-03-27 | Frontend (UI) | Sprint 4.6 — Extração 4 modais de confirmação de candidates-page (-267 linhas) — GlobalExpansionConfirmModal, SourceChangeConfirmModal, | `plataforma-lia/src/components/pages/candidates-page.tsx`<br>`plataforma-lia/src/components/pages/candidates/ContactFilterConfirmModal.tsx`<br>`plataforma-lia/src/components/pages/candidates/DeleteArchetypeModal.tsx` |
| 🟢 | `5fe9a6348` | 2026-03-27 | Frontend (UI) | Sprint 4.6 — Refactor handleSendMessage: 2030L → 61L thin dispatcher — Extraiu 12 funções handler da handleSendMessage original (2.030 linhas): | `plataforma-lia/src/components/expanded-chat-modal.tsx` |

### Task #10

- **Commits:** 3  |  **Período:** 2026-04-05 → 2026-04-05  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `b2c357310` | 2026-04-05 | Frontend (UI) | Task #10: Wire Chat LIA as primary menu item with fallback navigation — - Added "Chat LIA" as first sidebar menu item with MessageCircle icon | `plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/contexts/lia-float-context.tsx` |
| 🟢 | `cd6737543` | 2026-04-05 | Frontend (UI) | Task #10: Wire Chat LIA as primary menu item — - Added "Chat LIA" as first sidebar menu item with MessageCircle icon | `plataforma-lia/src/components/sidebar.tsx` |
| 🟢 | `785dbc19d` | 2026-04-05 | Frontend (UI) | Task #10: Wire Chat LIA as primary menu item — - Added "Chat LIA" as first sidebar menu item with Brain icon | `plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/lia-float/useLiaChatPanelState.ts`<br>`plataforma-lia/src/components/sidebar.tsx` |

### Task #108

- **Commits:** 3  |  **Período:** 2026-04-03 → 2026-04-10  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1 🟢×1 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `f7bfa2adf` | 2026-04-10 | Frontend (UI) | Task #108: Exhaustive Playwright E2E audit of Agent Studio — - Created comprehensive Playwright spec: plataforma-lia/e2e/tests/agent-studio-audit.spec.ts | `plataforma-lia/src/app/api/backend-proxy/agent-templates/[id]/publish/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/agent-templates/[id]/route.ts`<br>`plataforma-lia/src/app/api/backend-proxy/agent-templates/route.ts` |
| 🟢 | `38ed869e2` | 2026-04-03 | Frontend (UI) | Task #108: Centralize client-side business logic (scores + pricing) — Created centralized score utility (src/lib/score-utils.ts): | `plataforma-lia/src/components/chat/index.ts`<br>`plataforma-lia/src/components/search/candidate-detail-sidebar.tsx` |
| 🔴 | `6bfc8dc47` | 2026-04-03 | Cross Back↔Front | Task #108: Centralize client-side business logic (scores + pricing) — Created centralized score utility (src/lib/score-utils.ts): | `lia-agent-system/app/api/v1/cv_parser.py`<br>`plataforma-lia/src/app/admin/compliance/riscos/fornecedores/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/riscos/page.tsx` |

### Task #11

- **Commits:** 3  |  **Período:** 2026-04-05 → 2026-04-05  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `db821596e` | 2026-04-05 | Frontend (UI) | Task #11: Unified Lateral Chat Panel with Context Badge — T001: Added contextPage/setContextPage + entityContext/openWithEntity to | `plataforma-lia/src/components/candidate-preview/LiaChatModal.tsx`<br>`plataforma-lia/src/contexts/lia-float-context.tsx` |
| 🟡 | `a7a390b8f` | 2026-04-05 | Frontend (UI) | Task #11: Unified Lateral Chat Panel with Context Badge — T001: Added contextPage + setContextPage + entityContext + openWithEntity to | `plataforma-lia/src/components/candidate-preview/LiaChatModal.tsx`<br>`plataforma-lia/src/components/lia-float/LiaChatHeader.tsx`<br>`plataforma-lia/src/components/lia-float/LiaChatPanel.tsx` |
| 🟡 | `b08d14582` | 2026-04-05 | Frontend (UI) | Task #11: Unified Lateral Chat Panel with Context Badge — T001: Added contextPage + setContextPage to LiaFloatContext; DashboardApp syncs | `plataforma-lia/src/components/candidate-preview/LiaChatModal.tsx`<br>`plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/src/components/lia-float/LiaChatButton.tsx` |

### Task #140

- **Commits:** 3  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×2 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `6909948df` | 2026-04-11 | Frontend (UI) | Task #140 audit cleanup: remove orphan visaoGeral type references — - Removed 3 occurrences of 'visaoGeral' from useJobsPreview.ts type union | `plataforma-lia/src/components/pages/jobs/hooks/useJobsPreview.ts` |
| 🟢 | `dcb976c6c` | 2026-04-11 | Frontend (UI) | Fix Jobs page crash: add missing lucide-react icon imports — After Task #140 merge, jobs-page.tsx used Briefcase, Zap, Pause, | `plataforma-lia/src/components/pages/jobs-page.tsx` |
| 🟡 | `f0bc0e15b` | 2026-04-11 | Frontend (UI) | Task #140: Remover Visão Geral e Integrar Sugestões no Chat LIA — Changes: | `plataforma-lia/src/components/pages/JobsOverviewPanel.tsx`<br>`plataforma-lia/src/components/pages/jobs-page.tsx`<br>`plataforma-lia/src/components/pages/jobs/hooks/useJobsFilters.ts` |

### Task #161

- **Commits:** 3  |  **Período:** 2026-04-12 → 2026-04-12  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `aaeb584ca` | 2026-04-12 | Backend | Task #161: Interview Intelligence Infrastructure (Recording + Transcription) — - T001: Added company_id, transcript, transcript_language, transcript_source, | `lia-agent-system/app/api/v1/interviews.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/transcription_service.py` |
| 🟡 | `9ef3c0c49` | 2026-04-12 | Backend | Task #161: Interview Intelligence Infrastructure (Recording + Transcription) — - T001: Added company_id, transcript, transcript_language, transcript_source, | `lia-agent-system/app/api/v1/interviews.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/transcription_service.py` |
| 🟡 | `cc182ca1b` | 2026-04-12 | Backend | Task #161: Interview Intelligence Infrastructure (Recording + Transcription) — - T001: Added company_id, transcript, transcript_language, transcript_source, | `lia-agent-system/app/api/v1/interview_analysis.py`<br>`lia-agent-system/app/domains/interview_intelligence/services/transcription_service.py` |

### Task #166

- **Commits:** 3  |  **Período:** 2026-04-12 → 2026-04-12  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `407a8a918` | 2026-04-12 | Backend | Fix WebSocket NameError: remove orphaned ws_action_metadata reference — After handle_action_flow was deleted during prompt unification (Task #166), | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `6a3eb82de` | 2026-04-12 | Backend | Fix merge regressions from Task #166 prompt unification + SQL injection hardening — MERGE REGRESSION FIXES (from Task #166): | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/ai/services/llm.py` |
| 🟡 | `18cb55227` | 2026-04-12 | Backend | Auth hardening: fix DEV_MODE bypass (Task #166) — Security fix for critical vulnerability where REPL_ID environment variable | `lia-agent-system/app/api/v1/admin_bias_audit.py` |

### Task #167

- **Commits:** 3  |  **Período:** 2026-04-12 → 2026-04-12  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `97832681c` | 2026-04-12 | Docs | Task #167: Documentação do gap de observabilidade na orquestração — Criado arquivo lia-agent-system/docs/audit/ORCHESTRATION_OBSERVABILITY_GAP.md | `lia-agent-system/docs/audit/ORCHESTRATION_OBSERVABILITY_GAP.md` |
| 🟡 | `4c25b0309` | 2026-04-12 | Backend | Task #167: Fix SQL injection vulnerabilities + merge regression fixes — SQL INJECTION HARDENING (8 files): | `lia-agent-system/app/api/v1/chat.py` |
| 🟡 | `4de5efb00` | 2026-04-12 | Cross IA↔Back | Task #167: Fix SQL injection vulnerabilities — defense-in-depth hardening — CRITICAL FIX (user/LLM-input interpolated in SQL): | `lia-agent-system/app/domains/job_management/services/wizard_step_service.py`<br>`lia-agent-system/app/domains/lgpd/services/lgpd_cleanup_service.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py` |

### Task #210

- **Commits:** 3  |  **Período:** 2026-04-15 → 2026-04-15  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `bfbe89806` | 2026-04-15 | Backend | Task #210: Recalcular Progress para Novo Menu (7-section IDs) — - Refactored settings_progress.py endpoint to return 7 new section IDs: | `lia-agent-system/app/domains/company/repositories/settings_progress_repository.py` |
| 🟡 | `f7e5ab867` | 2026-04-15 | Backend | Task #210: Recalcular Progress para Novo Menu (7-section IDs) — - Refactored settings_progress.py endpoint to return 7 new section IDs: | `lia-agent-system/app/api/v1/settings_progress.py`<br>`lia-agent-system/app/domains/company/repositories/settings_progress_repository.py` |
| 🔴 | `59038c744` | 2026-04-15 | Cross Back↔Front | Task #210: Recalcular Progress para Novo Menu (7-section IDs) — - Refactored settings_progress.py endpoint to return 7 new section IDs: | `lia-agent-system/app/api/v1/settings_progress.py`<br>`lia-agent-system/app/domains/company/repositories/settings_progress_repository.py`<br>`plataforma-lia/src/components/pages/settings-page-enhanced.tsx` |

### Task #246

- **Commits:** 3  |  **Período:** 2026-04-16 → 2026-04-16  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `714a60b60` | 2026-04-16 | Backend | Task #246: Consolidate ARCHITECTURE.md and ATS integration boundary — Refactors /api/v1/rails-sync/* to comply with ADR-001 (no SQL in | `lia-agent-system/pyproject.toml` |
| 🟢 | `ab4a56198` | 2026-04-16 | Testes | Task #246: Consolidate ARCHITECTURE.md and ATS integration boundary — Refactors /api/v1/rails-sync/* to comply with ADR-001 (no SQL in | `lia-agent-system/tests/contract/test_wedotalent_rails_client_contract.py` |
| 🟡 | `3fb811041` | 2026-04-16 | Backend | Task #246: Consolidate ARCHITECTURE.md and ATS integration boundary — Refactor of /api/v1/rails-sync/* to comply with ADR-001 (no SQL in | `lia-agent-system/app/api/v1/rails_sync.py`<br>`lia-agent-system/app/domains/ats_integration/repositories/rails_sync_repository.py` |

### Task #430

- **Commits:** 3  |  **Período:** 2026-04-18 → 2026-04-18  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `6de2dc8cb` | 2026-04-18 | Frontend (UI) | Task #430 — Pipeline Overview Vagas\|Candidatos toggle — Adds a toggle on /visao-do-funil between the existing candidate funnel | `plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |
| 🔴 | `1043a8826` | 2026-04-18 | Cross IA↔Front | Task #430 — Pipeline Overview Vagas\|Candidatos toggle — Adds a toggle on /visao-do-funil between the existing candidate funnel | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`lia-agent-system/app/orchestrator/context_adapter.py`<br>`plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |
| 🔴 | `d6b844269` | 2026-04-18 | Cross Back↔Front | Task #430 — Pipeline Overview Vagas\|Candidatos toggle — Adds a 8-stage job lifecycle rail (ATS Importada → Encerrada) to /visao-do-funil | `lia-agent-system/app/api/v1/job_vacancies/analytics.py`<br>`plataforma-lia/src/app/api/backend-proxy/jobs-lifecycle-overview/route.ts`<br>`plataforma-lia/src/components/pages/pipeline-overview-page.tsx` |

### Task #432

- **Commits:** 3  |  **Período:** 2026-04-18 → 2026-04-18  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1 🟢×1 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `53450e056` | 2026-04-18 | Cross Back↔Front | Task #432: Rich responses no chat com PipelineRailCard — Frontend (plataforma-lia): | `lia-agent-system/app/api/v1/chat.py`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/chat/pipeline-rail-card.tsx` |
| 🟢 | `a29d0ed20` | 2026-04-18 | Frontend (UI) | Task #432: Rich responses no chat com PipelineRailCard — - New PipelineRailCard (src/components/chat/pipeline-rail-card.tsx) | `plataforma-lia/src/components/chat/pipeline-rail-card.tsx`<br>`plataforma-lia/src/components/expanded-chat/components/ChatMessageList.tsx` |
| 🟡 | `c87e463d5` | 2026-04-18 | Frontend (UI) | Task #432: Rich responses no chat com PipelineRailCard — - New PipelineRailCard (src/components/chat/pipeline-rail-card.tsx) | `plataforma-lia/src/app/[locale]/visao-do-funil/page.tsx`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx`<br>`plataforma-lia/src/components/chat/pipeline-rail-card.tsx` |

### Task #46

- **Commits:** 3  |  **Período:** 2026-03-26 → 2026-04-06  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `cffd1fd7c` | 2026-04-06 | Frontend (UI) | Task #46: Reordenar menu lateral — Reordenado o array `menuItems` em plataforma-lia/src/components/sidebar.tsx | `plataforma-lia/src/components/sidebar.tsx` |
| 🟢 | `331a91bbb` | 2026-03-26 | Docs | Task #46: Update PLATFORM_MAP + FRONTEND_STANDARDS with real ats_front code — FRONTEND_STANDARDS.md — complete rewrite (710→856 lines): | `docs/PLATFORM_MAP.md`<br>`docs/specs/standards/FRONTEND_STANDARDS.md` |
| 🟢 | `68abc6513` | 2026-03-26 | Docs | Task #46: Update PLATFORM_MAP + FRONTEND_STANDARDS with real ats_front code — FRONTEND_STANDARDS.md — complete rewrite (710→775 lines): | `docs/PLATFORM_MAP.md`<br>`docs/specs/standards/FRONTEND_STANDARDS.md` |

### Task #69

- **Commits:** 3  |  **Período:** 2026-04-08 → 2026-04-08  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `61560e0b8` | 2026-04-08 | IA | Task #69: Complete Platform Audit + Fix DB columns + Fix import — 1. Full platform audit - report at .local/audit/platform-audit-report.md | `wsi_splitter.py` |
| 🟡 | `d53081703` | 2026-04-08 | Backend | Task #69: Complete Platform Audit + Fix DB columns + Fix import — 1. Full platform audit - report at .local/audit/platform-audit-report.md | `lia-agent-system/app/api/v1/automation/event_handlers/__init__.py` |
| 🟢 | `f3e74c1d2` | 2026-04-08 | Empty/merge | Task #69: Complete Platform Audit + Fix email_encrypted DB column — 1. Full platform audit completed - report at .local/audit/platform-audit-report.md | — |

### Task #71

- **Commits:** 3  |  **Período:** 2026-04-08 → 2026-04-08  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `5f62e11e4` | 2026-04-08 | Backend | feat: Add comprehensive seed data script for LIA platform (Task #71) — Created lia-agent-system/scripts/seed_full_platform.py with CLI support | `lia-agent-system/scripts/seed_full_platform.py` |
| 🟡 | `3716d651c` | 2026-04-08 | Backend | feat: Add comprehensive seed data script for LIA platform (Task #71) — Created lia-agent-system/scripts/seed_full_platform.py with CLI support | `lia-agent-system/scripts/seed_full_platform.py` |
| 🟡 | `3b83fbc21` | 2026-04-08 | Backend | feat: Add comprehensive seed data script for LIA platform (Task #71) — Created lia-agent-system/scripts/seed_full_platform.py with CLI support | `lia-agent-system/scripts/seed_full_platform.py` |

### Task #72

- **Commits:** 3  |  **Período:** 2026-03-31 → 2026-04-08  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `85d504a78` | 2026-04-08 | Frontend (api/util) | task: Clone repository to wedocc2026 GitHub account (Task #72) — Created a mirror of the project repository on the wedocc2026 GitHub account: | `plataforma-lia/src/stores/auth-store.ts` |
| 🟡 | `6880f9392` | 2026-03-31 | Backend | fix(task-72): Replace unsupported Mustache block syntax with simple variable placeholder | `lia-agent-system/app/shared/intelligence/ab_testing/email_template_seeder.py` |
| 🟡 | `1098cadf4` | 2026-03-31 | Backend | fix(task-72): Persist A/B tracking data end-to-end + resolve from CommunicationLog — - Persist template_id, ab_test, ab_variant in CommunicationLog.extra_data at send time | `lia-agent-system/app/api/v1/email_tracking.py`<br>`lia-agent-system/app/domains/communication/services/communication_service.py`<br>`lia-agent-system/app/services/email_tracking_service.py` |

### Task #78

- **Commits:** 3  |  **Período:** 2026-03-31 → 2026-04-08  |  **Camadas:** Backend + Frontend  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1 🟢×1 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `ea09abcc3` | 2026-04-08 | Cross Back↔Front | feat: safe URL encoding for Microsoft OAuth auth URL + adapter interface fix — Final polish for Task #78 external integrations code review: | `lia-agent-system/app/api/v1/calendar.py`<br>`lia-agent-system/app/api/v1/integrations.py`<br>`lia-agent-system/app/api/v1/system_health.py` |
| 🟢 | `17d8bde5b` | 2026-03-31 | Empty/merge | Task #78 (Weekly Digest) — Final validation & critical fixes — Re-validated Task #78 against all required skills (feature-audit, | — |
| 🟡 | `24a150be6` | 2026-03-31 | Outro | Task #78 (Weekly Digest) — Final validation & critical fixes — Re-validated Task #78 against all required skills (feature-audit, | `=141` |

### Task #93

- **Commits:** 3  |  **Período:** 2026-04-02 → 2026-04-14  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `9126096cb` | 2026-04-14 | Cross IA↔Back | cleanup: remove LLMProviderFactory deprecated methods [PX08-081] Wave 6 item 6.1 — - Removed LLMProviderFactory.generate_with_fallback() (deprecated, global state) | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py` |
| 🟡 | `a0635bed8` | 2026-04-02 | Frontend (UI) | Task #93: Unify 4 bulk selection bar components into 1 BulkActionsBar — Created new unified `BulkActionsBar` component at | `plataforma-lia/src/app/funil-de-talentos/FunilDeTalentosClient.tsx`<br>`plataforma-lia/src/components/modals/bulk-action-modal.tsx`<br>`plataforma-lia/src/components/pages/job-kanban-page.tsx` |
| 🟡 | `c99559440` | 2026-04-02 | Frontend (UI) | Task #93: Unify 4 bulk selection bar components into 1 BulkActionsBar — Created new unified `BulkActionsBar` component at | `plataforma-lia/src/components/contextual-actions-banner.tsx`<br>`plataforma-lia/src/components/job-actions-bar.tsx`<br>`plataforma-lia/src/components/pages/candidates/CandidateSearchResultsView.tsx` |

### scope: bug-spec-generator

- **Commits:** 3  |  **Período:** 2026-03-21 → 2026-03-21  |  **Camadas:** Backend  |  **—**  |  **Risco:** 🟡×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `2068fbe8b` | 2026-03-21 | Backend | feat(bug-spec-generator): OAuth2 via conector Replit + suporte multi-ferramenta — Auth: | `lia-agent-system/scripts/bug_spec_generator.py` |
| 🟡 | `b9c12e799` | 2026-03-21 | Backend | feat(bug-spec-generator): suporte multi-ferramenta (Jam · Userback · BetterBugs) — - Renomeia _parse_jam_description → _parse_bug_description (parser genérico) | `lia-agent-system/scripts/bug_spec_generator.py` |
| 🟡 | `3d7e5dd7a` | 2026-03-21 | Backend | feat(bug-spec-generator): suporte multi-ferramenta (Jam · Userback · BetterBugs) — - Renomeia _parse_jam_description → _parse_bug_description (parser genérico) | `lia-agent-system/scripts/bug_spec_generator.py` |

### scope: deploy

- **Commits:** 3  |  **Período:** 2026-04-13 → 2026-04-13  |  **Camadas:** Backend + Rails  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `db3d7d8b5` | 2026-04-13 | Backend | chore(deploy): Fase 7 — celery split + cache consolidation + CI docs — celery_tasks.py split (2128 → 1 facade + 10 modules): | `lia-agent-system/app/config/cache_config.py`<br>`lia-agent-system/app/jobs/celery_tasks.py`<br>`lia-agent-system/app/jobs/tasks/__init__.py` |
| 🔴 | `7cf2b4722` | 2026-04-13 | Cross Rails+Replit | feat(deploy): Migrations applied + Rails handlers evolved with side-effects — Migration fix — webhook table conflict resolution: | `ats-api-copia/app/workers/lia_events_worker.rb`<br>`lia-agent-system/alembic/versions/074_webhooks.py`<br>`lia-agent-system/libs/models/lia_models/webhook.py` |
| 🟡 | `82cf12528` | 2026-04-13 | Backend | feat(deploy): F7 - deploy safety and consolidation [LIA-D01-D07] — - LIA-D01: Fix JobCreation import error (app.config.settings -> | `lia-agent-system/deploy/run_migrations.sh` |

### scope: design

- **Commits:** 3  |  **Período:** 2026-04-01 → 2026-04-01  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟢×2 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `8a24f2de1` | 2026-04-01 | Frontend (api/util) | fix(design): layout + shadow tokens replace arbitrary values — - Audit: 0 arbitrary shadows (already using lia-sm/default/md/lg tokens) | `plataforma-lia/src/lib/design-tokens.ts` |
| 🔴 | `8a229d0d1` | 2026-04-01 | Frontend (UI) | fix(design): typography scale + z-index semantic tokens replace arbitrary values | `plataforma-lia/src/app/admin/clientes/[clientId]/setup/page.tsx`<br>`plataforma-lia/src/app/admin/clientes/[clientId]/testes/page.tsx`<br>`plataforma-lia/src/app/admin/compliance/lgpd/consentimentos/page.tsx` |
| 🟢 | `da6cdd9bd` | 2026-04-01 | Frontend (UI) | fix(design): replace arbitrary spacing values with Tailwind scale equivalents | `plataforma-lia/src/components/ui/separator.tsx` |

### scope: e2e

- **Commits:** 3  |  **Período:** 2026-04-06 → 2026-04-20  |  **Camadas:** Frontend  |  **—**  |  **Risco:** 🟡×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `e1eb1ed58` | 2026-04-20 | Testes | test(e2e): use /pt/chat instead of /dashboard in auth fixture — /dashboard returns 404 in dev mode; switch to /pt/chat (200) and replace | `plataforma-lia/e2e/fixtures/auth.fixture.ts` |
| 🟡 | `57aa4a8aa` | 2026-04-16 | Frontend (api/util) | test(e2e): suite Playwright criacao manual de vaga — 37 testes (cherry-pick de develop) | `plataforma-lia/e2e/fixtures/job-creation.fixture.ts`<br>`plataforma-lia/e2e/tests/job-creation/01-create-modal.spec.ts`<br>`plataforma-lia/e2e/tests/job-creation/02-edit-basic-info.spec.ts` |
| 🟡 | `0a0538315` | 2026-04-06 | Frontend (api/util) | feat(e2e): Auditoria completa de usabilidade dos Chats LIA via Playwright (Task #26) — ## Suítes Playwright E2E (7 arquivos, 63 testes de auditoria) | `plataforma-lia/e2e/docs/analise-comparativa-chats-lia.md`<br>`plataforma-lia/e2e/tests/chat/chat-comportamento-input.spec.ts`<br>`plataforma-lia/e2e/tests/chat/chat-consistencia-cross.spec.ts` |

### scope: fase6

- **Commits:** 3  |  **Período:** 2026-03-31 → 2026-03-31  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `4d2422969` | 2026-03-31 | Docs | fix(fase6): Final reconciliation — C2 PARCIAL, I3 PARCIAL in gap summary — Last RESOLVIDO→PARCIAL corrections in gap summary table: | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md` |
| 🟢 | `49617bd44` | 2026-03-31 | Docs | fix(fase6): Reconcile audit findings with roadmap statuses — - ARCH-04 impact: LLM Classification + FG L3 marked PARCIAL/INACESSÍVEL | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md`<br>`docs/specs/AUDIT_ALPHA1_FASE6.md` |
| 🟢 | `432ba1fa7` | 2026-03-31 | Docs | feat(fase6): Auditoria Alpha 1 completa — 17 findings, ANALISE_ROADMAP v5.0 — Task #73: Fase 6 — Auditoria, Validação e2e + Code Review Final | `docs/specs/ANALISE_ROADMAP_ALPHA1_vs_CODIGO.md`<br>`docs/specs/AUDIT_ALPHA1_FASE6.md` |

### scope: orchestrator

- **Commits:** 3  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×3

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `9034a168b` | 2026-04-21 | Cross IA↔Back | fix(orchestrator): meta-question gate for capability questions (Task #726) — Capability questions like "consegue buscar candidatos no banco local ou | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/meta_question_detector.py` |
| 🟡 | `2379e592c` | 2026-04-21 | Cross IA↔Back | fix(orchestrator): meta-question gate for capability questions (Task #726) — Capability questions like "consegue buscar candidatos no banco local ou | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/orchestrator/meta_question_detector.py` |
| 🟡 | `d0a565f95` | 2026-04-21 | Cross IA↔Back | fix(orchestrator): meta-question gate for capability questions (Task #726) — Capability questions like "consegue buscar candidatos no banco local ou | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/meta_question_detector.py` |

### scope: scripts

- **Commits:** 3  |  **Período:** 2026-03-23 → 2026-03-23  |  **Camadas:** —  |  **—**  |  **Risco:** 🟢×2 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `b8999cf40` | 2026-03-23 | Docs | feat(scripts): BetterBugs content fetching + documentacao completa — BetterBugs Integration (ambos os scripts): | `docs/JIRA_SCRIPTS_DOCUMENTATION.md`<br>`scripts/jira-audit-design.py`<br>`scripts/jira-fetch-analyze.py` |
| 🟢 | `f58037dca` | 2026-03-23 | Empty/merge | feat(scripts): spec-driven sections completas nos dois scripts Jira — Script 1 (jira-fetch-analyze.py): | — |
| 🟡 | `972574ae7` | 2026-03-23 | Outro | feat(scripts): add spec-driven sections to ADF builders (Script 1 + 2) — Script 1 (jira-fetch-analyze.py) - ADF builder agora renderiza: | `scripts/jira-audit-design.py`<br>`scripts/jira-fetch-analyze.py` |

### §4 Rail Features — PR-HIRE (register_hire)

**Descrição:** PR-HIRE: tool register_hire que faz write real no DB (não mais mock). entity_required=[candidate, job], chat_executable=true. LIA resolve candidato + vaga antes de executar.

**⚠️ Dependências para cherry-pick:** capability_map declara register_hire | candidate + job entities resolvidos antes

**Arquivos canônicos:** lia-agent-system/app/domains/pipeline/tools/pipeline_tools.py (register_hire)

**Docs de referência:** BRANCH_MAP §4 / Wave 4

- **Commits:** 3  |  **Período:** 2026-04-27 → 2026-04-28  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2 🟢×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `be172b778` | 2026-04-28 | IA | feat(capability-map): add send_offer + register_hire, Wave 4, 27/27 tests green | `lia-agent-system/app/config/capability_map.yaml` |
| 🟡 | `b2b8634d4` | 2026-04-28 | Backend | feat(pipeline): PR-HIRE — register_hire real DB write — Replace stub with VacancyCandidate.status=hired write. | `lia-agent-system/app/domains/pipeline/tools/pipeline_tools.py`<br>`lia-agent-system/tests/domains/pipeline/__init__.py`<br>`lia-agent-system/tests/domains/pipeline/test_register_hire.py` |
| 🟢 | `ec7d4a817` | 2026-04-27 | Testes | feat(pipeline): PR-C register_hire action — closes P0 gap for card 6.1 — - register_hire tool: moves candidate to hired stage + records hired_at, | `lia-agent-system/tests/unit/domains/test_pr_c_register_hire.py` |

### Fase 1

- **Commits:** 2  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `cce263d25` | 2026-04-11 | IA | Fase 1 — RAGAS Blocking no CI/CD + Golden Datasets por Domínio (Task #122) — Changes: | `tests/golden/wsi_interview.json` |
| 🔴 | `81e989874` | 2026-04-11 | Cross Back↔Front | Fase 1 — Cost Dashboard Granular por Agente + Alertas (Task #123) — Backend changes (lia-agent-system): | `lia-agent-system/app/api/v1/ai_consumption.py`<br>`lia-agent-system/app/domains/ai/repositories/ai_consumption_repository.py`<br>`plataforma-lia/src/app/api/backend-proxy/ai-credits/route.ts` |

### Task #121

- **Commits:** 2  |  **Período:** 2026-04-04 → 2026-04-11  |  **Camadas:** Backend + Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `6ca941e60` | 2026-04-11 | Cross IA↔Back | Task #121: Expand OpenTelemetry instrumentation (Full Coverage) — - CascadedRouter: All 7 tiers + fallback with tier_name, confidence_score, | `lia-agent-system/app/api/v1/traces.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/services/hitl_service.py` |
| 🟡 | `43b63938a` | 2026-04-04 | Frontend (UI) | feat: Ajustar fonte global e estilo dos balões da LIA (Task #121) — ## Mudanças realizadas | `plataforma-lia/src/app/styles/typography.css`<br>`plataforma-lia/src/components/email-templates/report-email-templates.tsx`<br>`plataforma-lia/src/components/expanded-chat/components/ChatMessageList.tsx` |

### Task #133

- **Commits:** 2  |  **Período:** 2026-04-04 → 2026-04-11  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×1 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `2430e8220` | 2026-04-11 | Frontend (UI) | Task #133: LIA Chat UX — Ícone, Abertura e Sidebar Polish — Changes made across 4 files: | `plataforma-lia/src/components/unified-chat/DashboardChatPanel.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`<br>`plataforma-lia/src/components/unified-chat/UnifiedChatBubble.tsx` |
| 🔴 | `9c57a17f5` | 2026-04-04 | Cross IA↔Front | Task #133: Remove all StackOne integration — Merge.dev as sole universal ATS connector — Complete removal of StackOne integration from backend, frontend, tests, and documentation. | `lia-agent-system/app/agents/specialized/__init__.py`<br>`lia-agent-system/app/api/v1/automation.py`<br>`lia-agent-system/app/api/v1/external_webhooks.py` |

### Task #146

- **Commits:** 2  |  **Período:** 2026-04-05 → 2026-04-11  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `164c34fe4` | 2026-04-11 | Cross IA↔Back | Task #146: Implement Competitive Talent Intelligence Tools — New domain: lia-agent-system/app/domains/talent_intelligence/ | `lia-agent-system/app/domains/talent_intelligence/services/__init__.py`<br>`lia-agent-system/app/domains/talent_intelligence/services/skills_ontology_engine.py`<br>`lia-agent-system/app/tools/__init__.py` |
| 🟡 | `a86be78e3` | 2026-04-05 | Backend | Fix dev-server 500 errors on candidates and job-vacancies endpoints (Task #146) — Bug 1 - Candidates endpoint (/api/v1/candidates): | `lia-agent-system/alembic/versions/057_fix_missing_lifecycle_columns.py`<br>`lia-agent-system/app/api/v1/job_vacancies.py`<br>`lia-agent-system/app/api/v1/job_vacancies/_shared.py` |

### Task #150

- **Commits:** 2  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `331bf58d8` | 2026-04-11 | IA | Task #150: Domain Consolidation — Classify 57 Domains — Created DOMAIN_CATALOG.md at app/domains/ with complete classification: | `lia-agent-system/app/orchestrator/action_executor/intents_config.py` |
| 🔴 | `d973395c8` | 2026-04-11 | Backend | Task #150: Domain Consolidation — Classify 57 Domains — Created DOMAIN_CATALOG.md at app/domains/ with complete classification: | `lia-agent-system/app/domains/auth/__init__.py` |

### Wizard/Onda 18-21

- **Commits:** 2  |  **Período:** 2026-04-28 → 2026-04-28  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×1 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `6ab1a6172` | 2026-04-28 | Docs | docs(nav): BRANCH_MAP fix Ondas 18-21 table cells backtick escape | `lia-agent-system/docs/BRANCH_MAP.md` |
| 🟡 | `64728b8f1` | 2026-04-28 | Cross IA↔Back | feat(wizard): Ondas 18-21 — apply_learning nos stages, pick_canonical salary, wizard_step_response metadata — F.1-F.4: feedback_learning_service.apply_learning() plugado em stage_description, | `lia-agent-system/app/domains/job_management/services/wizard_step_service/service.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_basic_info.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_description.py` |

### Wizard/Onda 23

- **Commits:** 2  |  **Período:** 2026-04-28 → 2026-04-28  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×1 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `b3a217c27` | 2026-04-28 | Docs | docs(nav): BRANCH_MAP Onda 23 Wave 2-4 audit, 119 tests green | `lia-agent-system/docs/BRANCH_MAP.md` |
| 🟡 | `bdb0cf8d2` | 2026-04-28 | Cross IA↔Back | feat(wizard): Onda 23 — C.1 WsiQuestionGenerator + C.2 JdEnrichmentService canônicos — C.1 stage_wsi.py: WsiQuestionGenerator (F2+F3+F6 pipeline) com SeniorityResolver. | `lia-agent-system/app/domains/job_management/services/wizard_step_service/service.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_review.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_wsi.py` |

### Wizard/Onda 24

- **Commits:** 2  |  **Período:** 2026-04-28 → 2026-04-28  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×1 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `3157b37b9` | 2026-04-28 | Docs | docs(nav): BRANCH_MAP — Onda 24 PR-CAL scheduling MVP 14/14 tests | `lia-agent-system/docs/BRANCH_MAP.md` |
| 🟡 | `7a0d9ab79` | 2026-04-28 | Cross IA↔Back | feat(wizard): Onda 24 — C.3 perguntas explícitas recrutador (seniority + WSI mode + calibração) — C.3.1 stage_description.py: confirma senioridade detectada ao recrutador. | `lia-agent-system/app/domains/job_management/services/wizard_step_service/service.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_description.py`<br>`lia-agent-system/app/domains/job_management/services/wizard_step_service/stage_publication.py` |

### Wizard/Onda 3.2

- **Commits:** 2  |  **Período:** 2026-04-21 → 2026-04-22  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `e1dcee729` | 2026-04-22 | Cross IA↔Back | restore(lia): recover Onda 3.2—5.1 work + new Onda 5.3.a after parallel rollback — Context: commit c698d5eef "Restored to 'c3d45b3d8...'" (via Replit rollback | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/domains/recruiter_assistant/services/lia_briefing_formatter.py` |
| 🟡 | `34c7d2cb7` | 2026-04-21 | Cross IA↔Back | feat(lia): Onda 3.2 G3 — HITL checkpoint surfacing — HITL logic already exists at app/tools/executor.py:283 (detects requires_hitl | `lia-agent-system/app/orchestrator/hitl.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |

### scope: phase4b

- **Commits:** 2  |  **Período:** 2026-04-07 → 2026-04-07  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `81889e02a` | 2026-04-07 | Cross IA↔Back | feat(phase4b): batch 2 — migrate 73 AI-permanent services to domain layer — Migrated services (73 total across 7 domains): | `lia-agent-system/app/api/v1/candidate_search/calibration.py`<br>`lia-agent-system/app/api/v1/rubric_evaluation.py`<br>`lia-agent-system/app/domains/ai/services/context_aggregator_service.py` |
| 🟡 | `5e89b5546` | 2026-04-07 | Backend | feat(phase4b): add backwards-compat shims in shared/services for migrated domain services — - compensation_analysis_service -> app/domains/analytics/services/ (shim added) | `lia-agent-system/app/shared/services/agent_quality_evaluator.py`<br>`lia-agent-system/app/shared/services/archetype_builder_service.py`<br>`lia-agent-system/app/shared/services/compensation_analysis_service.py` |

### scope: seo

- **Commits:** 2  |  **Período:** 2026-03-31 → 2026-04-01  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×1 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `fb271416b` | 2026-04-01 | Frontend (UI) | feat(seo): add generateMetadata() to 24 key pages — SEO Score 4→5 — - Convert page.tsx files to server components and add export const metadata | `plataforma-lia/src/app/funil-de-talentos/candidato/[id]/page.tsx`<br>`plataforma-lia/src/app/jobs/[id]/page.tsx`<br>`plataforma-lia/src/app/vagas/[slug]/page.tsx` |
| 🔴 | `3562ec23f` | 2026-03-31 | Cross IA↔Front | feat(seo): metadata global + OG image + title template — cobertura 88 páginas | `lia-agent-system/app/api/v1/jd_generation.py`<br>`lia-agent-system/app/api/v1/wsi_questions.py`<br>`plataforma-lia/src/app/layout.tsx` |

### scope: tools

- **Commits:** 2  |  **Período:** 2026-04-19 → 2026-04-20  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `527f2c3ce` | 2026-04-20 | Cross IA↔Back | feat(tools): canonical routing fixes — P0 + P1.A + P1.B + P1.C — Foundation for Tools Unification Migration (ADR-016). Adds the 5 non-regressive | `lia-agent-system/app/tools/__init__.py`<br>`lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| 🟡 | `9eafa6207` | 2026-04-19 | Cross IA↔Back | fix(tools): P0/P1 hardening — multi-tenancy + capacity + factory bypass — - executor.py: execute_batch() now propagates ToolExecutionContext to every | `lia-agent-system/app/domains/cv_screening/services/wsi_question_adjuster.py`<br>`lia-agent-system/app/tools/__init__.py`<br>`lia-agent-system/app/tools/executor.py` |

### §12 DEVELOPER_HANDOFF — PARTE D

- **Commits:** 2  |  **Período:** 2026-04-19 → 2026-04-27  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟢×1 🔴×1
- **Tags/Milestones:** `milestone/parte-d-complete`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `248137994` | 2026-04-27 | Docs | docs(nav): BRANCH_MAP — janela 3 (Tasks #494-#570) + 7 milestones (PARTE D, BYOK, WSI, persona) | `lia-agent-system/docs/BRANCH_MAP.md` |
| 🔴 | `8314d3517` | 2026-04-19 | Cross IA↔Front | fix(parte-d): close 4 PARTE D gaps — full tracking + canonical schema + manifest wiring + proactive UI — Gap 1 — company_scraper_service Apify tracking (P1): | `lia-agent-system/app/api/v1/agent_chat_ws.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`plataforma-lia/src/components/chat/ChatMessageList.tsx` |

### §13 PARTE D — PreConditionChecker

**Descrição:** PreConditionChecker expandido de 3 → 8 checks fail-open: missing_company_id, incomplete_company_profile, vacancy_no_screening, company_website_missing, culture_profile_missing, benefits_catalog_empty, hiring_policy_missing, candidates_missing_contact. Cada check em try/except próprio.

**⚠️ Dependências para cherry-pick:** Schema canonical company_profiles (não mais 'companies') | id::text OR client_account_id::text | hint anti-repeat via sessionStorage no FE

**Arquivos canônicos:** lia-agent-system/app/orchestrator/precondition_checker.py, app/orchestrator/main_orchestrator.py (delegate)

**Docs de referência:** DEVELOPER_HANDOFF.md §5.3 + §6.3

- **Commits:** 2  |  **Período:** 2026-04-19 → 2026-04-26  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `8adecbc23` | 2026-04-26 | Cross IA↔Back | Task #819: close last 2 demo-tenant config gaps in PreConditionChecker — Original task: Close the 2 remaining `info` hints from the demo tenant — | `lia-agent-system/app/orchestrator/precondition_checker.py`<br>`lia-agent-system/app/shared/services/seed_service.py` |
| 🟡 | `08a912340` | 2026-04-19 | IA | feat(orchestrator): D2 PreConditionChecker +5 new proactive checks — Extended PreConditionChecker from 3 checks to 8 (D10 proactivity coverage). | `lia-agent-system/app/orchestrator/precondition_checker.py` |

### §3 LIA Maturity — FIX 1

- **Commits:** 2  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `c15a89862` | 2026-04-21 | Backend | docs: LIA AI intelligence handoff + ADR-019 + glossario regenerado (FIX 1-12) — Documentacao tecnica completa para o time de desenvolvimento consumir e reproduzir | `lia-agent-system/scripts/generate_tool_action_glossary.py` |
| 🟡 | `82009b0c8` | 2026-04-21 | Cross IA↔Back | feat(ai): FIX 1 - DomainActions now reach LLM via routing context — - Add DomainPrompt.get_actions_for_prompt(max_actions=8) to base.py | `lia-agent-system/app/orchestrator/llm_cascade.py`<br>`lia-agent-system/app/tools/__init__.py` |

### §3 LIA Maturity — FIX 31

- **Commits:** 2  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `ac9a7c6e3` | 2026-04-21 | IA | fix(lia): FIX 31 v2 — move resolver wiring to process() top (covers all phases) — FIX 31 v1 wired memory_resolver inside _process_via_orchestrator (Phase 2) | `lia-agent-system/app/orchestrator/main_orchestrator.py` |
| 🟡 | `a50b87886` | 2026-04-21 | IA | fix(lia): FIX 31 — wire memory_resolver into production chat path — Discovered via FIX 30 smoke test: FIX 19 (affirmations) and FIX 30 | `lia-agent-system/app/orchestrator/main_orchestrator.py` |

### §3 LIA Maturity — FIX 5

- **Commits:** 2  |  **Período:** 2026-04-21 → 2026-04-22  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `bfaad7737` | 2026-04-22 | Backend | fix(lia): Onda 5.1.b — persona briefing-as-fact rule (FIX 5.1) — After 5.1.a lands the briefing in extra_instructions, the persona must | `lia-agent-system/app/prompts/shared/lia_persona.yaml`<br>`lia-agent-system/tests/unit/test_onda5_1_b_persona_briefing_rule.py` |
| 🟡 | `71a2ec1d1` | 2026-04-21 | Cross IA↔Back | feat(ai): FIX 5+6+7 - wizard sync, observability, semantic overlap — FIX 5 (P2): Wizard TOOL_DEFINITIONS now enriched from YAML | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`lia-agent-system/app/tools/__init__.py` |

### Sourcing (BE)

**Descrição:** Domínio de sourcing — Apify gateway, candidate_enrichment, search service, query_tools, agents (sourcing_agent).

**⚠️ Dependências para cherry-pick:** Apify gateway D0 (zero bypass) | budget check | tracking via record_apify_call

**Arquivos canônicos:** lia-agent-system/app/domains/sourcing/**

**Docs de referência:** DEVELOPER_HANDOFF PARTE D

- **Commits:** 1  |  **Período:** 2026-03-19 → 2026-03-19  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `8870cab97` | 2026-03-19 | Cross IA↔Back | Add specialized agents to improve candidate sourcing and management workflows — Introduce new sub-agents for sourcing planning, search, enrichment, and engagement, enhancing the sy | `lia-agent-system/app/orchestrator/fast_router.py`<br>`lia-agent-system/app/orchestrator/llm_cascade.py` |

### Sprint 4

- **Commits:** 1  |  **Período:** 2026-04-10 → 2026-04-10  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `7f658ccb0` | 2026-04-10 | Cross IA↔Front | feat: Sprint 4 — Agent Studio conversational creation via chat — Backend: | `lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml`<br>`plataforma-lia/src/components/unified-chat/NavigationHintCard.tsx` |

### Sprint Z

- **Commits:** 1  |  **Período:** 2026-03-19 → 2026-03-19  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `00ce86b71` | 2026-03-19 | Cross IA↔Back | code review: corrige 5 problemas identificados na sprint Z — - traces.py: substitui import de _otlp_active (privado) por is_otlp_active() pública | `lia-agent-system/app/api/v1/admin_dlq.py`<br>`lia-agent-system/app/api/v1/traces.py`<br>`lia-agent-system/app/orchestrator/cascaded_router.py` |

### Task #107

- **Commits:** 1  |  **Período:** 2026-04-03 → 2026-04-03  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `7a298e6e3` | 2026-04-03 | Cross IA↔Front | Task #107: Complete API validation hardening — Changes: | `lia-agent-system/app/tools/__init__.py`<br>`lia-agent-system/app/tools/scope_config.py`<br>`plataforma-lia/src/app/api/backend-proxy/admin/guardrails/[id]/route.ts` |

### Task #122

- **Commits:** 1  |  **Período:** 2026-04-04 → 2026-04-04  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `a2facdc6b` | 2026-04-04 | Cross IA↔Back | fix: address code review for Task #122 orchestrator consolidation — Three runtime regressions fixed, plus two improvements from review comments: | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/v1/orchestrated_job_chat.py`<br>`lia-agent-system/app/api/v1/orchestrated_talent_chat.py` |

### Task #123

- **Commits:** 1  |  **Período:** 2026-04-04 → 2026-04-04  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `71fc9de33` | 2026-04-04 | Cross IA↔Back | feat(task-123): Complete LangGraph migration - fix regressions and update tests — Fixes two regressions identified in code review: | `lia-agent-system/app/api/v1/health_langgraph.py`<br>`lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`<br>`lia-agent-system/app/services/checkpoint_service.py` |

### Task #124

- **Commits:** 1  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `1cf273c6a` | 2026-04-11 | Cross IA↔Back | feat(task-124): Activate A/B testing of prompts in production — - Created experiment YAML configs for CascadeRouter system prompt | `lia-agent-system/alembic/versions/062_add_prompt_version_to_messages.py`<br>`lia-agent-system/app/api/v1/ab_testing.py`<br>`lia-agent-system/app/api/v1/chat.py` |

### Task #125

- **Commits:** 1  |  **Período:** 2026-04-04 → 2026-04-04  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `4fb8a5f89` | 2026-04-04 | Cross IA↔Back | feat(task-125): Declarative tool permissions (YAML) and DI for LLM providers — Task #125 — Tool Permissions Declarativo (YAML) e DI para Providers | `lia-agent-system/app/orchestrator/tenant_budget.py`<br>`lia-agent-system/app/shared/providers/llm_factory.py`<br>`lia-agent-system/app/tools/scope_config.py` |

### Task #138

- **Commits:** 1  |  **Período:** 2026-04-04 → 2026-04-04  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `30b1b9151` | 2026-04-04 | Cross IA↔Front | Task #138: Dead integration cleanup - OpenMic, Deepgram, SynthFlow, StackOne, Neon, Prometheus, Grafana — Completed cleanup of 7 dead integrations from the codebase: | `lia-agent-system/app/api/v1/external_webhooks.py`<br>`lia-agent-system/app/api/v1/lia_voice.py`<br>`lia-agent-system/app/api/v1/metrics.py` |

### Task #139

- **Commits:** 1  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `8690b05d0` | 2026-04-11 | Cross IA↔Front | Task #139: Redesign TopBar — Avatar e Notificações na Sidebar — Moved recruiter avatar, notification bell, and HITL pending badge from | `lia-agent-system/app/orchestrator/action_handlers/_handler_hooks.py`<br>`lia-agent-system/app/orchestrator/action_handlers/candidate_actions.py`<br>`lia-agent-system/app/orchestrator/action_handlers/communication_actions.py` |

### Task #145

- **Commits:** 1  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `e93d57b77` | 2026-04-11 | Cross IA↔Back | Task #145: Align LIA prompts with actual tool capabilities — Fixed prompt-tool mismatches across 6 prompt files: | `lia-agent-system/app/shared/prompts/job_wizard.py`<br>`lia-agent-system/app/tools/scope_config.py` |

### Task #213

- **Commits:** 1  |  **Período:** 2026-04-15 → 2026-04-15  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `c50dfb90d` | 2026-04-15 | Cross IA↔Front | Task #213: Pull GitHub Updates (wedotalent02202026 + ats-api-copia) — Fetched and merged updates from both GitHub remotes: | `lia-agent-system/alembic/versions/078_few_shot_candidates.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/agent_studio_quality.py` |

### Task #215

- **Commits:** 1  |  **Período:** 2026-04-15 → 2026-04-15  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `8486175f9` | 2026-04-15 | Cross IA↔Front | feat: Pull QA fixes from fix/qa-2026-04-15 branch (Task #215) — Integrated 13 QA bug fixes from the fix/qa-2026-04-15 branch (SHA b61621bba) | `lia-agent-system/app/api/v1/candidates/candidates_crud.py`<br>`lia-agent-system/app/api/v1/job_vacancies/crud.py`<br>`lia-agent-system/app/domains/integrations_hub/services/rails_adapter.py` |

### Task #234

- **Commits:** 1  |  **Período:** 2026-04-16 → 2026-04-16  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `25077dd3a` | 2026-04-16 | Cross IA↔Back | Fix duplicate FastAPI operation IDs (task #234) — Original task: backend startup emitted 12 "Duplicate Operation ID" UserWarnings | `lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/job_status_webhooks.py`<br>`lia-agent-system/app/api/v1/wsi_question_adjust.py` |

### Task #242

- **Commits:** 1  |  **Período:** 2026-04-16 → 2026-04-16  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `ff42c5642` | 2026-04-16 | Cross IA↔Back | task #242: eliminar colisão de mapper SQLAlchemy — Causa raiz: `lia-agent-system/app/models/` continha 120 arquivos shim | `lia-agent-system/alembic/env.py`<br>`lia-agent-system/app/api/public/candidate_portal.py`<br>`lia-agent-system/app/api/public/shared_searches.py` |

### Task #32

- **Commits:** 1  |  **Período:** 2026-04-06 → 2026-04-06  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `d7476dbc2` | 2026-04-06 | Cross IA↔Back | Fix candidates and vacancies loading (Task #32) — Root cause: The backend (lia-agent-system) was crashing on startup with | `lia-agent-system/app/orchestrator/intent_router.py`<br>`lia-agent-system/app/services/culture_analyzer_service.py`<br>`lia-agent-system/app/services/enhanced_intent_classifier.py` |

### Task #322

- **Commits:** 1  |  **Período:** 2026-04-17 → 2026-04-17  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `9a88c12e7` | 2026-04-17 | Cross IA↔Back | Task #322 — Cleanup: 12 órfãos, 5 stubs e duplicata exata de job_report_service — Removed 18 dead/duplicate files confirmed to have zero production importers: | `lia-agent-system/app/api/v1/company_benefits_api.py`<br>`lia-agent-system/app/api/v1/lia_assistant/__init__.py`<br>`lia-agent-system/app/api/v1/lia_autonomous.py` |

### Task #352

- **Commits:** 1  |  **Período:** 2026-04-17 → 2026-04-17  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `4713cd342` | 2026-04-17 | Cross IA↔Back | task #352 — close out AUDIT FINAL 2026-04 finals (F4, F5, F8, F10, F11, F12) — Closes the remaining gaps from AUDIT_STATUS_REPORT_2026-04-FINAL.md. | `lia-agent-system/app/shared/compliance/bias_audit_service.py`<br>`lia-agent-system/app/shared/services/affirmative_service.py`<br>`lia-agent-system/app/shared/services/analysis_service.py` |

### Task #353

- **Commits:** 1  |  **Período:** 2026-04-17 → 2026-04-17  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `dc3e16e5c` | 2026-04-17 | Cross IA↔Back | Task #353: Move per-tenant LLM provider config out of YAML and into the database — ADR-016 decided per-tenant `llm_provider` and `llm_fallback_order` should | `lia-agent-system/app/shared/providers/llm_factory.py`<br>`lia-agent-system/app/tools/tool_permissions.yaml`<br>`lia-agent-system/app/tools/tool_permissions_loader.py` |

### Task #354

- **Commits:** 1  |  **Período:** 2026-04-17 → 2026-04-17  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `035e96e10` | 2026-04-17 | Cross IA↔Back | Task #354: Block accidental tool registrations outside canonical entry point — Adds the S7.5 CI/pre-commit guard required by ADR-016 so future contributors | `lia-agent-system/app/tools/registry.py` |

### Task #366

- **Commits:** 1  |  **Período:** 2026-04-17 → 2026-04-17  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `415d6db42` | 2026-04-17 | Cross IA↔Back | Task #366 — promote actor_user_id to a structured audit field — Original task | `lia-agent-system/alembic/versions/084_add_actor_user_id_to_audit_logs.py`<br>`lia-agent-system/app/api/routes.py`<br>`lia-agent-system/app/api/v1/admin_audit_decisions.py` |

### Task #386

- **Commits:** 1  |  **Período:** 2026-04-17 → 2026-04-17  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `e89240c75` | 2026-04-17 | IA | Task #386 — Hard-block English equivalents of "good looking" / "young and dynamic" — Background: | `lia-agent-system/app/shared/compliance/fairness_guard.py` |

### Task #417

- **Commits:** 1  |  **Período:** 2026-04-18 → 2026-04-18  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `49947851f` | 2026-04-18 | Cross IA↔Back | Migrate cv_match_tool to canonical authoring surface (Task #417) — Original task: Shrink the tool-authoring allow list (S7.5 / ADR-016) by | `lia-agent-system/app/tools/__init__.py` |

### Task #43

- **Commits:** 1  |  **Período:** 2026-04-06 → 2026-04-06  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `41d9174cd` | 2026-04-06 | Cross IA↔Front | Task #43: Complete audit and fix of LIA agentic capabilities — Changes across 10+ files covering all 8 session plan tasks: | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_executor/intents_config.py` |

### Task #489

- **Commits:** 1  |  **Período:** 2026-04-18 → 2026-04-18  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `5c9c2633a` | 2026-04-18 | Cross IA↔Back | Task #489: Protect remaining /api/v1 routers from URL shadowing bugs — Apply the Task #455 / #458 blindagem to 118 single-file routers under | `lia-agent-system/app/api/v1/_path_patterns.py`<br>`lia-agent-system/app/api/v1/activities.py`<br>`lia-agent-system/app/api/v1/admin_audit_decisions.py` |

### Wizard/Onda 2.4

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `d0230dc91` | 2026-04-21 | IA | feat(lia): Onda 2.4 Init V — Reasoning transparency backend (citations) — Producer layer for citation-based reasoning transparency. Frontend | `lia-agent-system/app/orchestrator/citation_processor.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |

### Wizard/Onda 2.5

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `f7b8ec3a6` | 2026-04-21 | Cross IA↔Back | feat(lia): Onda 2.5 Init II.D — workflow_context slot + 3 v1 workflows — Formalizes multi-turn flows (cancelamento, sourcing com filtros, wizard de | `lia-agent-system/app/orchestrator/workflow_registry.py`<br>`lia-agent-system/app/shared/prompts/system_prompt_builder.py` |

### Wizard/Onda 3.3

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `a06559d59` | 2026-04-21 | Cross IA↔Back | feat(lia): Onda 3.3 Init VII — error recovery policies catalog v1 — 5 canonical policies for deterministic error responses (was: LIA improvised | `lia-agent-system/app/orchestrator/error_policies.py`<br>`lia-agent-system/app/orchestrator/error_policies.yaml` |

### Wizard/Onda 4.10

- **Commits:** 1  |  **Período:** 2026-04-22 → 2026-04-22  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `3d316958b` | 2026-04-22 | Cross IA↔Back | feat(lia): Onda 4.10 — adapter forwards citations + hitl_checkpoint to API envelope — PARTE L gap discovered in runtime smoke: MainOrchestrator produces | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/orchestrator/chat_adapter.py` |

### Wizard/Onda 4.11

- **Commits:** 1  |  **Período:** 2026-04-22 → 2026-04-22  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `ad6ce7073` | 2026-04-22 | Cross IA↔Back | fix(lia): Onda 4.11 + 4.12 — briefing formatter keys + III.B log level — Two post-smoke corrections for Onda 4 B-phase runtime visibility: | `lia-agent-system/app/domains/recruiter_assistant/services/lia_briefing_formatter.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |

### Wizard/Onda 4.3

- **Commits:** 1  |  **Período:** 2026-04-22 → 2026-04-22  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `b7bc5d264` | 2026-04-22 | IA | feat(lia): Onda 4.3 III.B — hydrate recruiter_preferences from user_preferences — Wires Init III MVP episodic memory producer (Onda 3.5) into | `lia-agent-system/app/orchestrator/main_orchestrator.py` |

### Wizard/Onda 4.4

- **Commits:** 1  |  **Período:** 2026-04-22 → 2026-04-22  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `b197d510b` | 2026-04-22 | IA | feat(lia): Onda 4.4 IV.B — briefing greeting wire — Producer (Init IV Onda 2.3 lia_briefing_formatter) now wired into | `lia-agent-system/app/orchestrator/main_orchestrator.py` |

### Wizard/Onda 4.5

- **Commits:** 1  |  **Período:** 2026-04-22 → 2026-04-22  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `338b9b583` | 2026-04-22 | IA | feat(lia): Onda 4.5 V.B — citations populate em ChatResponse (agentic path) — Producer (citation_processor Onda 2.4 Init V) wired into agentic ChatResponse. | `lia-agent-system/app/orchestrator/main_orchestrator.py` |

### Wizard/Onda 4.6

- **Commits:** 1  |  **Período:** 2026-04-22 → 2026-04-22  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `f9f60701a` | 2026-04-22 | IA | feat(lia): Onda 4.6 G3.B — HITL checkpoint dispatch to ChatResponse — Producer (hitl.build_hitl_checkpoint Onda 3.2) wired into agentic path. | `lia-agent-system/app/orchestrator/main_orchestrator.py` |

### Wizard/Onda 4.7

- **Commits:** 1  |  **Período:** 2026-04-22 → 2026-04-22  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `09c387d15` | 2026-04-22 | IA | feat(lia): Onda 4.7 VII.B — error_policies wired in outer catch-all — Producer (error_policies.py Onda 3.3 with 5 v1 policies) now wired into | `lia-agent-system/app/orchestrator/main_orchestrator.py` |

### Wizard/Onda 5.1.

- **Commits:** 1  |  **Período:** 2026-04-22 → 2026-04-22  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `f6ee7e7dd` | 2026-04-22 | IA | fix(lia): Onda 5.1.a — wire ctx.extra['extra_instructions'] into agentic loop — PARTE L gap: Onda 4.4 IV.B injected briefing into ctx.extra["extra_instructions"] | `lia-agent-system/app/orchestrator/main_orchestrator.py` |

### Wizard/Onda 5.3.

- **Commits:** 1  |  **Período:** 2026-04-22 → 2026-04-22  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `54def11f3` | 2026-04-22 | IA | feat(lia): Onda 5.3.c — history compaction with conversation_summary reuse — Canonical-fix consumer-side: existing conversation_summary producer | `lia-agent-system/app/orchestrator/agentic_loop.py` |

### scope: #147

- **Commits:** 1  |  **Período:** 2026-04-11 → 2026-04-11  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `c9f1bfc2c` | 2026-04-11 | Cross IA↔Back | feat(#147): Loop Autônomo e Inteligência Proativa — Implements proactive intelligence for LIA recruitment assistant: | `lia-agent-system/app/domains/recruiter_assistant/domain.py`<br>`lia-agent-system/app/domains/recruiter_assistant/services/autonomous_actions_engine.py`<br>`lia-agent-system/app/domains/recruiter_assistant/services/monitoring_loop.py` |

### scope: agentic

- **Commits:** 1  |  **Período:** 2026-04-13 → 2026-04-13  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `71e8d28c5` | 2026-04-13 | Cross IA↔Back | feat(agentic): F4 - real agentic loop, LLM thinks before acting [LIA-A01-A04] — - LIA-A01: LLM interprets action results in Phase 0 AND Phase 1 before | `lia-agent-system/app/domains/ai/services/llm.py`<br>`lia-agent-system/app/orchestrator/agentic_loop.py` |

### scope: autonomous

- **Commits:** 1  |  **Período:** 2026-04-07 → 2026-04-07  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `91f187afa` | 2026-04-07 | Cross IA↔Back | feat(autonomous): finalize Tier 6 — all reviews addressed, 59 tests passing — Task #58 (AutonomousReActAgent — Tier 6) — final state: | `lia-agent-system/app/orchestrator/cascaded_router.py`<br>`lia-agent-system/app/orchestrator/orchestrator.py` |

### scope: ddd

- **Commits:** 1  |  **Período:** 2026-04-07 → 2026-04-07  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `ba43cd5c7` | 2026-04-07 | Cross IA↔Back | feat(ddd): Phase 4 DDD migration — credit_service and rails_adapter to domain layer — - Move credit_service.py to app/domains/credits/services/ (canonical) | `lia-agent-system/app/agents/base_agent.py`<br>`lia-agent-system/app/api/v1/candidate_search/core_search.py`<br>`lia-agent-system/app/api/v1/credits.py` |

### scope: handlers

- **Commits:** 1  |  **Período:** 2026-04-19 → 2026-04-19  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `d2a8954d9` | 2026-04-19 | Cross IA↔Back | fix(handlers): strip non-UUID entity_id from context before handler dispatch — Handlers like _analyze_funnel and _rank_candidates were using V0037 (short ID) | `lia-agent-system/app/orchestrator/action_executor/executor.py`<br>`lia-agent-system/app/orchestrator/action_handlers/sourcing_actions.py` |

### scope: infra

- **Commits:** 1  |  **Período:** 2026-04-07 → 2026-04-07  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `bb3d4819d` | 2026-04-07 | Cross IA↔Back | feat(infra): Task #67 — Broker Abstraction Layer + Fix 15 Test Import Errors — ## Broker Abstraction (Items 1 & 2) | `lia-agent-system/app/api/v1/candidate_search/__init__.py`<br>`lia-agent-system/app/api/v1/system_health.py`<br>`lia-agent-system/app/services/bias_audit_service.py` |

### scope: intents

- **Commits:** 1  |  **Período:** 2026-04-13 → 2026-04-13  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `4c2373bbf` | 2026-04-13 | Cross IA↔Back | feat(intents): F5 - single source of intents in YAML + shared matcher [LIA-I01-I08] — - LIA-I01: KeywordIntentMatcher shared service (158 lines) with from_yaml | `lia-agent-system/app/domains/agent_studio/domain.py`<br>`lia-agent-system/app/domains/analytics/domain.py`<br>`lia-agent-system/app/domains/ats_integration/domain.py` |

### scope: lia-a04,fase4

- **Commits:** 1  |  **Período:** 2026-04-13 → 2026-04-13  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `68c1da3f0` | 2026-04-13 | IA | feat(LIA-A04,Fase4): bind_tools in _handle_directly fallback path — Context: ReAct agents (90% of traffic) already use create_react_agent from | `lia-agent-system/app/orchestrator/orchestrator.py` |

### scope: lia-agent

- **Commits:** 1  |  **Período:** 2026-04-19 → 2026-04-19  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `30359ced0` | 2026-04-19 | Cross IA↔Back | feat(lia-agent): LIA Deep Audit P2 fixes (C3, D10) — C3 conversation_memory.py: | `lia-agent-system/app/domains/recruiter_assistant/services/conversation_memory.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |

### scope: lia-chat

- **Commits:** 1  |  **Período:** 2026-04-03 → 2026-04-03  |  **Camadas:** Frontend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `daed87514` | 2026-04-03 | Cross IA↔Front | fix(lia-chat): Round 9 — education_level to lia_insights JSON + PT-BR datetime resolver — Final semantic fix (code review approved-with-comments): | `lia-agent-system/app/api/v1/chat.py`<br>`lia-agent-system/app/api/v1/file_analysis.py`<br>`lia-agent-system/app/domains/interview_scheduling/services/calendar_service.py` |

### scope: loop

- **Commits:** 1  |  **Período:** 2026-04-13 → 2026-04-13  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `3f416f078` | 2026-04-13 | Cross IA↔Back | feat(loop): Activate agentic loop by default + fix imports (LIA-A04) — 1. LIA-A04 activated by default: | `lia-agent-system/app/domains/cv_screening/domain.py`<br>`lia-agent-system/app/domains/pipeline/domain.py`<br>`lia-agent-system/app/orchestrator/agentic_loop.py` |

### scope: memory

- **Commits:** 1  |  **Período:** 2026-04-13 → 2026-04-13  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `85d9ce5d3` | 2026-04-13 | IA | feat(memory): F2 - memory persists, history as real LLM turns [LIA-M01-M05] — - LIA-M01: _setup_conversation_memory() moved BEFORE Phase 0 | `lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/orchestrator/action_executor/utils.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |

### scope: phase3

- **Commits:** 1  |  **Período:** 2026-04-07 → 2026-04-07  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `4adf6561f` | 2026-04-07 | Cross IA↔Back | fix(phase3): replace app.models imports with lia_models in service files — - Case A: 128 files changed from app.models.X to lia_models.X where lia_models equivalent exists (28 | `lia-agent-system/app/domains/ai/services/agent_quality_evaluator.py`<br>`lia-agent-system/app/domains/ai/services/enhanced_intent_classifier.py`<br>`lia-agent-system/app/domains/ai/services/intent_classifier.py` |

### scope: phase9

- **Commits:** 1  |  **Período:** 2026-04-06 → 2026-04-06  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🔴×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🔴 | `9826db31d` | 2026-04-06 | Cross IA↔Back | refactor(phase9): ruff auto-fixes — remove 819 unused imports, sort imports, modernize type annotations — - F401: removed 819 unused imports across 446 files | `lia-agent-system/app/api/orchestrator_routes.py`<br>`lia-agent-system/app/api/public/candidate_portal.py`<br>`lia-agent-system/app/api/v1/admin.py` |

### scope: router

- **Commits:** 1  |  **Período:** 2026-04-13 → 2026-04-13  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `777594992` | 2026-04-13 | IA | feat(router): P2.4 — CascadedRouter Tier 7: Studio agents in chat — 8-tier routing: memory → redis → vector → fast → LLM → autonomous → studio → clarification | `lia-agent-system/app/orchestrator/cascaded_router.py` |

### scope: routing

- **Commits:** 1  |  **Período:** 2026-04-18 → 2026-04-18  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `97c3767c9` | 2026-04-18 | IA | fix(routing): add English job listing patterns for EX-007 resilience — Adds 4 English-language regex patterns to list_jobs intent in domain_routing.yaml. | `lia-agent-system/app/orchestrator/config/domain_routing.yaml` |

### §12 DEVELOPER_HANDOFF — PARTE L

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `ba28c86ff` | 2026-04-21 | Cross IA↔Back | fix(lia): FIX 29 + FIX 30 — close runtime-inert gaps (PARTE L pattern) — Empirical smoke test against live LIA API (via JWT) revealed two FIXes from | `lia-agent-system/app/orchestrator/memory_resolver.py` |

### §3 LIA Maturity — FIX 10

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `c0a3e3b79` | 2026-04-21 | IA | feat(ai): FIX 10 - wizard YAML coverage + requires_confirmation resolver — G4 - Wizard YAML coverage (100%): | `lia-agent-system/app/orchestrator/action_executor/intents_config.py`<br>`lia-agent-system/app/tools/tool_registry_metadata.yaml` |

### §3 LIA Maturity — FIX 11

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `cf12c3ec9` | 2026-04-21 | Cross IA↔Back | feat(ai): FIX 11 - actions_context placement + WSI cluster cross-ref — G5 - actions_context placement: | `lia-agent-system/app/orchestrator/llm_cascade.py` |

### §3 LIA Maturity — FIX 12

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `3f7245f18` | 2026-04-21 | Cross IA↔Back | feat(ai): FIX 12 - HITL envelope + observability module (LangSmith-optional) — G8 - HITL envelope in ChatResponse: | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |

### §3 LIA Maturity — FIX 13

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `453a46615` | 2026-04-21 | Cross IA↔Back | refactor(obs): FIX 13 - migrate observability to canonical path (ADR-019) — Moves tool_metrics observability module from non-canonical path to the | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`lia-agent-system/app/orchestrator/main_orchestrator.py` |

### §3 LIA Maturity — FIX 19

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `14629fdfe` | 2026-04-21 | IA | fix(orchestrator): FIX 19 - wire FIX 15 affirmation into runtime gate (P0) — Audit of FIX 14-17 revealed that FIX 15 was test-green but runtime-inert. | `lia-agent-system/app/orchestrator/memory_resolver.py` |

### §3 LIA Maturity — FIX 21

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1
- **Tags/Milestones:** `milestone/lia-maturity-track1`

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `42d5dbb7b` | 2026-04-21 | Cross IA↔Back | feat(lia): Track 1 Fases B+C+D — FIX 21-28 (LIA Maturity Program) — Follows FIX 20 (pagination, 182dec756). 8 canonical-fix patches from real-chat | `lia-agent-system/app/orchestrator/main_orchestrator.py`<br>`lia-agent-system/app/orchestrator/memory_resolver.py`<br>`lia-agent-system/app/orchestrator/pending_action.py` |

### §3 LIA Maturity — FIX 3

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `c9ec97385` | 2026-04-21 | IA | feat(ai): FIX 3+4 - governance_tags HITL enforcement + related_tools suggestions — FIX 3 (governance_tags P1): | `lia-agent-system/app/orchestrator/agentic_loop.py`<br>`lia-agent-system/app/tools/__init__.py`<br>`lia-agent-system/app/tools/executor.py` |

### §3 LIA Maturity — FIX 8

- **Commits:** 1  |  **Período:** 2026-04-21 → 2026-04-21  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `8e8bfa3bd` | 2026-04-21 | IA | feat(ai): FIX 8 - FairnessGuard enforcement + side_effects field (P1) — G1 — FairnessGuard enforcement: | `lia-agent-system/app/tools/__init__.py`<br>`lia-agent-system/app/tools/executor.py`<br>`lia-agent-system/app/tools/registry.py` |

### §4 Rail Features — PR-G

- **Commits:** 1  |  **Período:** 2026-04-29 → 2026-04-29  |  **Camadas:** IA  |  **—**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `0569b325b` | 2026-04-29 | IA | fix(pr-g): delete dead hitl_service shim, 8/8 canonical sensors green — canonical-fix: app.shared.services.hitl_service was an 8-line re-export | `lia-agent-system/app/shared/services/hitl_service.py` |

### §4 Rail Features — PR-Q3

- **Commits:** 1  |  **Período:** 2026-04-28 → 2026-04-28  |  **Camadas:** Backend + IA  |  **⚠️ Cross-cutting**  |  **Risco:** 🟡×1

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟡 | `03cad32de` | 2026-04-28 | Cross IA↔Back | feat(capability-map): PR-Q3 — align start_wsi_interview intent + triagem wsi keywords — Canonical-fix: capability_map.yaml used start_wsi_flow but FE SUGGESTION_HINTS | `lia-agent-system/app/config/capability_map.yaml` |

### Menu Rename + Visão Global (Task #941 + pós-doc)

**Descrição:** Renomeação de itens do menu lateral (Chat LIA→Conversar, Tarefas→Decidir), criação de "Recrutar" como pai expansível com sub-itens Vagas + Funil de Talentos (com sub-sub-itens dinâmicos de talent pools preservados), renomeação do cabeçalho "Visão do Pipeline" → "Visão Global" e inversão da ordem das abas (Vagas | Candidatos) com default do store passando para `'vagas'`. Inclui shims de retrocompat em `dashboard-app.tsx` para identificadores antigos (`Chat LIA`, `Tarefas`, `Visão do Funil`) — **não remover** os shims no cherry-pick.

**⚠️ Dependências para cherry-pick:** aplicar os dois commits em ordem (`6b87a793c` → `d673198c7`).

**Arquivos canônicos:** `plataforma-lia/src/components/sidebar.tsx`, `plataforma-lia/src/components/dashboard-app.tsx`, `plataforma-lia/src/components/pages/pipeline-overview-page.tsx`, `plataforma-lia/src/stores/ui-preferences-store.ts`, `plataforma-lia/messages/{pt-BR,en}.json`

**Docs de referência:** card Jira "[FE] Renomeação e reorganização do menu lateral + Visão Global"

- **Commits:** 2  |  **Período:** 2026-04-29 → 2026-04-29  |  **Camadas:** Frontend (UI)  |  **—**  |  **Risco:** 🟢×2

| Risco | SHA | Data | Camada | O que faz | Arquivos chave |
|:---:|---|---|---|---|---|
| 🟢 | `6b87a793c` | 2026-04-29 | Frontend (UI) | feat(sidebar): rename and restructure lateral menu per fork design — Task #941. Remove seção "Recrutamento", renomeia Chat LIA→Conversar e Tarefas→Decidir, cria "Recrutar" como pai expansível com Vagas + Funil de Talentos (preserva sub-sub-itens dinâmicos de talent pools via `injectDynamic()` recursivo). Inclui shims de retrocompat em `handleNavigate` e listener `lia:navigation-hint`. | `plataforma-lia/src/components/sidebar.tsx`<br>`plataforma-lia/src/components/dashboard-app.tsx`<br>`plataforma-lia/messages/pt-BR.json`<br>`plataforma-lia/messages/en.json` |
| 🟢 | `d673198c7` | 2026-04-29 | Frontend (UI) | feat(pipeline-overview): rename Visão do Pipeline → Visão Global, invert tab order, default 'vagas' — Cabeçalho renomeado, ordem das abas passa a ser Vagas \| Candidatos, default do `pipelineOverviewMode` no store muda de `'candidatos'` para `'vagas'` (afeta apenas usuários sem preferência salva). | `plataforma-lia/src/components/pages/pipeline-overview-page.tsx`<br>`plataforma-lia/src/stores/ui-preferences-store.ts` |

---

## 3. Próximos passos sugeridos

1. **Time abre o documento** e identifica as features que pretende subir
2. Para cada feature 🔴 cross-cutting: **listar TODOS os commits da feature**, não só um
3. Ordem de cherry-pick recomendada: do **mais antigo para o mais novo** dentro de cada feature
4. Antes de cherry-pick, ler os campos `Descrição` + `Dependências` + `Arquivos canônicos`
5. Consultar [CHERRY_PICK_APPENDICES.md](CHERRY_PICK_APPENDICES.md) quando precisar de:
   - Lista de cross-cutting filtrada (Apêndice A)
   - Auto-commits do Replit Agent que misturam várias mudanças (Apêndice B)
   - Lista cronológica completa dos 3.491 commits (Apêndice C)
   - Features menores 1-2 commits (Apêndice D)
