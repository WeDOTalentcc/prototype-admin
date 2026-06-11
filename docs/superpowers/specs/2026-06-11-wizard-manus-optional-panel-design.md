# Wizard chat-first com painel lateral opcional (padrão Manus) — Design

**Data:** 2026-06-11
**Status:** Aprovado por Paulo (brainstorming 2026-06-11). Funde o design "wizard lateral→tela cheia consentida" aprovado em sessão paralela do mesmo dia.
**Escopo:** wizard de criação de vagas (caminho vivo `wizard_orchestrator`, flag `LIA_WIZARD_ORCHESTRATOR=1`) — FE `plataforma-lia/src/components/unified-chat/` + BE `lia-agent-system/app/domains/job_creation/orchestrator/`.

## 1. Problema

Hoje o painel lateral do wizard (`DynamicContextPanel`) é obrigatório e dono do fluxo:

- Auto-abre em toda etapa; o recrutador não escolhe.
- A LIA aponta pro painel ("As perguntas estão no painel lateral 👉") — o chat não é autossuficiente.
- No fim do wizard (`done`/`handoff` estão em `SPLIT_STAGES`) o painel **fica preso**: nada o fecha, nem chat nem botões do `DonePanel`.
- O ✕ atual rotulado "Cancelar" só esconde o painel localmente (rótulo enganoso) — o cancel real é outro fluxo.
- O prompt do `wizard_orchestrator.py:172-178` proíbe a LIA de afirmar controle sobre o painel (correto hoje: a capability não existe).
- Em chat lateral/bolha o painel espreme o layout (problema da sessão paralela 2026-06-11).

## 2. Referência de produto

Manus AI ("Manus's computer") e o clone open-source **Suna** (kortix-ai/suna @ `adadb9b`, paths verificados):

- `frontend/src/components/thread/chat-input/floating-tool-preview.tsx` — dock card acima do input (ícone, nome amigável, dot de status, maximizar; shared-element transition `layoutId` Framer Motion).
- `frontend/src/components/thread/tool-call-side-panel.tsx` — painel com ✕/minimizar; **base** com contador "N/N" + slider + modo Live vs scrub manual.
- `frontend/src/hooks/messages/useThreadToolCalls.ts` — conteúdo do painel **derivado do histórico de mensagens**; `userClosedPanelRef` (fechou = fica fechado); auto-open só se rodando E usuário nunca fechou.
- `frontend/src/components/thread/tool-views/wrapper/ToolViewRegistry.tsx` — registry de vistas por tipo + fallback genérico.

**Contrato extraído:** chat = narrativa autossuficiente; painel = projeção opcional do mesmo dado; card inline no chat = âncora de reabertura; progress no dock quando fechado / na base do painel quando aberto.

**Anti-patterns a NÃO copiar:** encanamento cru (terminal/JSON) na frente do recrutador; painel aberto por default em 40% da tela; auto-switch de vista durante revisão; slot de status com upsell rotativo; dependência de screenshot/VNC (nossa projeção = componentes React de domínio).

## 3. Decisões de produto (Paulo, 2026-06-11)

1. **Dock por padrão + escolha lembrada na sessão** — painel inicia minimizado (card acima do input); expandir/fechar persiste pelas etapas seguintes do mesmo wizard.
2. **Cards expansíveis no chat** — conteúdo denso (JD, perguntas WSI) revisável 100% no chat, renderizado deterministicamente pelo FE a partir do payload do painel (nunca do texto do LLM).
3. **Thumbnail vivo no dock** — miniatura real do painel (estilo Manus), não chip genérico.
4. **Progress bar**: dentro do painel (rodapé) quando expandido; no dock quando minimizado.
5. (Sessão paralela) **Consent card em lateral/bolha**: 2 botões [Ir pra tela cheia]/[Continuar aqui]; recusa = modo compacto sem painel; pergunta a cada novo wizard, sem persistência.

## 4. Arquitetura

### 4.1 Máquina de estados do painel (fullscreen)

`lia-float-context` ganha `wizardPanelMode: 'docked' | 'expanded'` (default `docked`) + sticky por sessão de wizard (espelha `userClosedPanelRef` do Suna):

- `wizard_stage` payload chegando **atualiza conteúdo** sem mudar o modo.
- Expandir (clique no dock) → `expanded` persistente; ✕ → `docked` persistente.
- `done`/`handoff` → força `docked` com card "Vaga publicada ✓" (mata o painel preso por construção).
- **Regra estrutural (fusão):** `DynamicContextPanel` SÓ monta em fullscreen. Em lateral/bolha, nunca — nem docked.

### 4.2 WizardDock (novo componente)

Acima do input, visível quando wizard ativo e `wizardPanelMode === 'docked'`:

- Thumbnail vivo: o próprio painel renderizado em escala (~0.25, CSS `transform: scale`, `pointer-events: none`, `aria-hidden`), atualizando com o estado real.
- Título da etapa, progresso "Etapa 3/6", badge de pendência ("1 aprovação aguardando") quando `requires_approval`.
- Clique/botão maximizar → `expanded`, com shared-element transition (`layoutId`, spring ~300/30).
- Sem conteúdo rotativo, sem marketing no slot.

### 4.3 Stepper/progress

Sai do topo do chat (`UnifiedChat.tsx` wizardActive header). Expandido → rodapé do painel; docked → dentro do WizardDock. Fonte única: `wizardStage`. "Cancelar wizard" (AlertDialog canônico #1133) migra pro rodapé do painel + menu do dock. ✕ do painel = "minimizar" honesto (tooltip "Minimizar painel"), nunca "Cancelar".

### 4.4 Cards expansíveis no chat (registry)

`WizardStageCardRegistry` (padrão ToolViewRegistry): mapa stage→card + fallback genérico.

- **Card JD**: preview (título, seções-chave) + "ver completa" (expande inline) + âncora "abrir no painel".
- **Card Perguntas WSI**: lista numerada colapsável; badges técnica/comportamental/CBI/"Revisar"; contadores de distribuição (mesma fonte `distribution_gap`); expande pergunta a pergunta.
- **Card Publicação**: link da vaga + CTAs (ir pra vaga / criar outra).
- Renderização determinística do payload `wizard_stage` ancorado à mensagem da LIA que concluiu a etapa (`stage_ref` na mensagem). 12 perguntas no payload = 12 itens no card, sempre.
- Âncora "abrir no painel" reabre o painel naquela etapa (chip do padrão Manus/Suna).
- Ações de edição continuam por linguagem natural (tools add/edit/remove já existem); gates HITL server-side inalterados.

### 4.5 Backend (cirúrgico)

- Tools `open_panel` / `close_panel` no `wizard_orchestrator` (padrão `navigate_to_jobs`: flag no state → FE reage no próximo frame). Fechar/abrir pelo chat passa a funcionar.
- Prompt do wizard: remover instruções "está no painel lateral 👉"; substituir a proibição absoluta (seção "Painel lateral", `wizard_orchestrator.py:172-178`) por descrição das novas tools + honestidade quando não aplicável (lateral/bolha). Etapa final: oferecer "ir pra vaga / criar outra / continuar por aqui".
- `stage_ref` anexado ao frame da mensagem para ancoragem do card no chat (payload já existe; é referenciá-lo).

### 4.6 Fusão — consent card em lateral/bolha (design da sessão paralela, aprovado como está)

- `WizardFullscreenPromptCard` renderizado quando `SPLIT_STAGE + mode ∈ {sidebar, floating} + não respondido neste wizard`. Aceitar → bridge canônico (`handleModeChange("fullscreen")`/`navigateToChat()`).
- Recusar → modo compacto: conversa + chat cards (4.4) + stepper compacto, SEM painel.
- Remover `_autoFullscreenConversations` e a auto-escalada silenciosa (`UnifiedChat.tsx:1088-1113`).
- Escopo da pergunta = por sessão de wizard; sem persistência.

## 5. Sensores (TDD obrigatório)

**Vitest (plataforma-lia):**
- Dock é default; expandir/fechar é sticky pelas etapas; `done`/`handoff` recolhem pro dock.
- Cards renderizam do payload (12 perguntas → 12 itens; badge Revisar quando `needs_manual_review`); nunca dependem de texto do LLM.
- `DynamicContextPanel` nunca monta fora de fullscreen (atualizar `DynamicContextPanel.split-stages-canonical.test.ts`).
- Consent card aparece em split-stage+lateral; aceitar chama bridge; recusar suprime painel; wizard novo re-pergunta.
- Stepper no rodapé do painel quando expandido / no dock quando docked; ausente do topo do chat.
- Rules of Hooks (modais/cards com 5+ hooks → smoke rerender) + i18n canonical contract (pt-BR + en desde o 1º commit, `npm run lint:i18n:blocking`).

**Pytest (lia-agent-system):**
- Tools `open_panel`/`close_panel`: schema, registro na allowlist do wizard, flag de state correta, sem side effects.
- Prompt da etapa final contém as 3 opções; seção "Painel lateral" atualizada.

## 6. Fases de entrega

1. **F1 — Estados + dock + stepper:** `wizardPanelMode`, WizardDock (thumbnail vivo), stepper realocado, ✕ honesto, tools open/close_panel + prompt.
2. **F2 — Chat cards:** registry + cards JD/WSI/Publicação + `stage_ref` + prompt sem referências obrigatórias ao painel.
3. **F3 — Fusão lateral:** consent card + regra estrutural fullscreen-only + remoção da auto-escalada.
4. **F4 — Polish:** shared-element transition fina, acessibilidade do thumbnail, microinterações.

**Semente futura (fora de escopo):** replay/timeline do wizard (scrubber Live/manual) — sai quase de graça da arquitetura de projeção; valor de auditoria HITL/compliance.

## 7. Não-objetivos

- Não mexe na máquina de estados do wizard backend (etapas, gates HITL, geração) — só apresentação + 2 tools.
- Não generaliza o dock para outros painéis dinâmicos (entity modals) nesta fase.
- Não persiste preferência de painel entre sessões/wizards.
- Independente dos fixes WSI P0/P1 (split-brain senioridade etc.) — auditoria 2026-06-11, tratados em separado.

## 8. Riscos

- **Sessões paralelas no mesmo FE**: `UnifiedChat.tsx`/`lia-float-context.tsx` são hot files — REGRA 6 (checar `git log --since="6 hours ago"`) antes de cada slice; commits sempre com pathspec (REGRA 8).
- Thumbnail vivo em escala: medir custo de render; se pesar, degradar para snapshot estático por etapa (decisão registrada, não silenciosa).
- Prompt do wizard: relaxar a proibição do painel exige as tools existirem ANTES (ordem F1 → F2), senão reabre alucinação de ação.
