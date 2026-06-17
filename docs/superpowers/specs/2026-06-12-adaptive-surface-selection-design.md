# Adaptive Surface Selection — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Implementar um sistema declarativo de surface selection que decide onde renderizar cada tool result do recruiter — inline no chat (card compacto) ou no painel lateral (detalhe expandido) — com base em densidade de dados, disponibilidade de painel e regras HITL. Zero mudanças no `lia-agent-system`.

**Data:** 2026-06-12  
**Baseado em:** pesquisa Suna/kortix-ai (código verificado) + auditoria `plataforma-lia` (2026-06-12)  
**Branch:** `feat/benefits-prv-canonical`

---

## Contexto e Motivação

O WeDOTalent tem hoje dois mundos paralelos:

1. **Wizard** — cards visuais no chat (WizardJdCard, WizardWsiCard) + painéis ricos laterais (JdEnrichmentPanel, WsiQuestionsPanel). Já funciona, mas com dois componentes separados para a mesma informação.

2. **Recruiter geral** — tool results como texto markdown puro. `search_candidates` retorna um blob de texto. `get_candidate_profile` idem. O recrutador não consegue clicar num resultado para ver o detalhe no painel.

O padrão dominante em produtos como Suna, Cursor e v0 usa **um único componente com duas apresentações** (inline compacto / painel expandido), decidido por um React Context. O chat sempre mostra uma linha de resumo por tool call; o painel mostra o detalhe do item em foco.

**Princípio de harness:** o modelo decide QUAL tool chamar; o harness FE decide ONDE exibir. Nunca o contrário.

---

## Estado Atual (diagnóstico auditoria 2026-06-12)

### O que já existe ✅

| Componente | Arquivo | Estado |
|---|---|---|
| Panel routing | `DynamicContextPanel.tsx` (161 linhas, switch/lazy) | Funciona, hardcoded |
| 12 painéis wizard | `wizard/panels/IntakePanel.tsx` … `DonePanel.tsx` | Funcionam |
| 14+ card types inline | `UnifiedMessageList.tsx` linhas 381-674 | Funcionam |
| Panel state | `lia-float-context.tsx`: `openDynamicPanel/closeDynamicPanel` | Funciona |
| SSE events | `tool_started`, `tool_finished`, `panel_update`, `ws_stage_payload` | Chegam |
| WizardJdCard / WizardWsiCard | `wizard/WizardJdCard.tsx`, `WizardWsiCard.tsx` | Funcionam |

### O que falta ❌

| Gap | Impacto |
|---|---|
| `focusedToolCallId` ausente | Painel não sabe qual tool call o abriu; não pode destacar card relacionado no chat |
| Switch hardcoded em DynamicContextPanel | Adicionar stage novo = modificar o switch; sem registry declarativo |
| `ToolSurfaceContext` ausente | WizardJdCard e JdEnrichmentPanel são componentes separados; duplicação de lógica |
| SURFACE_CONFIG ausente | Nenhum mapeamento declarativo `tool → superfície`; cada tool result é caso especial |
| Tool results não-wizard sem card | `search_candidates`, `get_candidate_profile`, `list_jobs` chegam como texto puro |

---

## Arquitetura

### Princípio central (Suna-inspired)

```
SURFACE_CONFIG (constante)
  ↓
useSurfaceForTool(toolName, itemCount?) → 'inline' | 'panel'
  ↓
ToolSurfaceContext.Provider
  ↓  
Um único componente de card — duas apresentações
```

### Onde vive cada peça

```
plataforma-lia/src/
├── lib/
│   └── surface-config.ts          # SURFACE_CONFIG — constante declarativa
├── contexts/
│   ├── lia-float-context.tsx       # + focusedToolCallId em DynamicPanelData
│   └── ToolSurfaceContext.tsx      # NOVO — 'inline' | 'panel' default 'inline'
├── hooks/chat/
│   └── useSurfaceForTool.ts        # NOVO — resolve superfície por tool
├── stores/
│   └── lia-panel-store.ts          # NOVO (Zustand) — focusedToolCallId + _panelOpenBySession
└── components/unified-chat/
    ├── wizard/DynamicContextPanel.tsx  # REFACTOR — switch → registry
    ├── tool-cards/                     # NOVO — cards surface-aware
    │   ├── CandidateResultCard.tsx
    │   ├── JobListCard.tsx
    │   └── CalibrationResultCard.tsx
    └── UnifiedMessageList.tsx          # + ToolActivateContext
```

---

## Phase 0 — Fundação (precondição)

**Objetivo:** adicionar `focusedToolCallId` ao pipeline e substituir o switch hardcoded por registry declarativo. Sem isso, as fases seguintes não funcionam.

### P0.1 — `focusedToolCallId` no DynamicPanelData

**Arquivo:** `src/contexts/lia-float-context.tsx`

```typescript
// ANTES (linha ~81):
export interface DynamicPanelData {
  panelType: DynamicPanelType
  data: Record<string, unknown>
  title?: string
  stage?: string | null
  requires_approval?: boolean
}

// DEPOIS:
export interface DynamicPanelData {
  panelType: DynamicPanelType
  data: Record<string, unknown>
  title?: string
  stage?: string | null
  requires_approval?: boolean
  focusedToolCallId?: string | null   // ← NOVO
  openedBy?: { toolName: string; toolCallId: string; ts: number } | null  // ← NOVO
}
```

**Onde flui:** `useChatSocket.ts` → CustomEvent `lia:wizard-stage-payload` → listener em `lia-float-context` → `openDynamicPanel`. O `toolCallId` pode ser gerado com `crypto.randomUUID()` no momento do dispatch se o backend não enviar um.

### P0.2 — Registry declarativo no DynamicContextPanel

**Arquivo:** `src/components/unified-chat/wizard/DynamicContextPanel.tsx`

```typescript
// ANTES: switch(stage) { case "jd_enrichment": return <JdEnrichmentPanel> ... }

// DEPOIS:
import type { WizardStage } from "../wizard/wizard-types"

const PANEL_REGISTRY: Record<WizardStage, React.LazyExoticComponent<...>> = {
  intake:         lazy(() => import("./panels/IntakePanel")),
  jd_enrichment:  lazy(() => import("./panels/JdEnrichmentPanel")),
  wsi_questions:  lazy(() => import("./panels/WsiQuestionsPanel")),
  bigfive:        lazy(() => import("./panels/BigFivePanel")),
  salary:         lazy(() => import("./panels/SalaryPanel")),
  competency:     lazy(() => import("./panels/CompetencyPanel")),
  eligibility:    lazy(() => import("./panels/EligibilityPanel")),
  review:         lazy(() => import("./panels/ReviewPanel")),
  publish:        lazy(() => import("./panels/PublishPanel")),
  calibration:    lazy(() => import("./panels/CalibrationPanel")),
  handoff:        lazy(() => import("./panels/HandoffPanel")),
  done:           lazy(() => import("./panels/DonePanel")),
  scheduling:     lazy(() => import("./panels/SchedulingPanel")),
  pipeline_template: lazy(() => import("./panels/PipelineTemplatePanel")),
}

// Render:
const PanelComponent = PANEL_REGISTRY[stage]
if (!PanelComponent) return <FallbackPanel stage={stage} />
return (
  <Suspense fallback={<PanelSkeleton />}>
    <PanelComponent data={data} ... />
  </Suspense>
)
```

**Sensor obrigatório (harness):** `check_panel_registry_sync.ts` — verifica que todo valor de `WizardStage` tem entrada em `PANEL_REGISTRY`. Falha em CI se stage novo for adicionado sem panel correspondente.

### P0.3 — `LiaPanelStore` (Zustand, per-session)

**Arquivo novo:** `src/stores/lia-panel-store.ts`

```typescript
import { create } from "zustand"

interface LiaPanelState {
  focusedToolCallId: string | null
  _panelOpenBySession: Record<string, boolean>  // sessionId → isOpen
  openForToolCall: (callId: string, sessionId: string) => void
  closePanel: (sessionId: string) => void
  isPanelOpenForSession: (sessionId: string) => boolean
}

export const useLiaPanelStore = create<LiaPanelState>((set, get) => ({
  focusedToolCallId: null,
  _panelOpenBySession: {},
  openForToolCall: (callId, sessionId) =>
    set({ focusedToolCallId: callId, _panelOpenBySession: { ...get()._panelOpenBySession, [sessionId]: true } }),
  closePanel: (sessionId) =>
    set({ _panelOpenBySession: { ...get()._panelOpenBySession, [sessionId]: false } }),
  isPanelOpenForSession: (sessionId) => get()._panelOpenBySession[sessionId] ?? false,
}))
```

---

## Phase 1 — ToolSurfaceContext Pattern

**Objetivo:** um componente, duas apresentações. Qualquer card do chat pode abrir o painel focado naquele tool call.

### P1.1 — ToolSurfaceContext

**Arquivo novo:** `src/contexts/ToolSurfaceContext.tsx`

```typescript
import { createContext, useContext } from "react"

export type ToolSurface = "inline" | "panel"

/** Default: 'inline'. DynamicContextPanel define 'panel'. */
export const ToolSurfaceContext = createContext<ToolSurface>("inline")

export const useToolSurface = () => useContext(ToolSurfaceContext)
```

**Uso no DynamicContextPanel:**
```tsx
<ToolSurfaceContext.Provider value="panel">
  <PanelComponent data={data} ... />
</ToolSurfaceContext.Provider>
```

### P1.2 — SURFACE_CONFIG

**Arquivo novo:** `src/lib/surface-config.ts`

```typescript
export type SurfaceConfig = {
  default_surface: "inline" | "panel"
  fallback_surface: "inline-card" | "inline-notification" | "inline-hitl"
  can_show_both: boolean
  hitl: boolean
  density_threshold?: number  // itens acima → panel; abaixo → inline
}

export const SURFACE_CONFIG: Record<string, SurfaceConfig> = {
  // ── Dados densos → painel ──────────────────────────────────────
  search_candidates:      { default_surface: "panel", fallback_surface: "inline-card",         can_show_both: true,  hitl: false, density_threshold: 3 },
  get_candidate_profile:  { default_surface: "panel", fallback_surface: "inline-card",         can_show_both: true,  hitl: false },
  get_job_details:        { default_surface: "panel", fallback_surface: "inline-card",         can_show_both: true,  hitl: false },
  get_wsi_questions:      { default_surface: "panel", fallback_surface: "inline-card",         can_show_both: true,  hitl: false },
  get_calibration:        { default_surface: "panel", fallback_surface: "inline-card",         can_show_both: true,  hitl: false },
  list_jobs:              { default_surface: "inline", fallback_surface: "inline-card",        can_show_both: true,  hitl: false, density_threshold: 5 },

  // ── HITL → inline obrigatório ──────────────────────────────────
  send_email:             { default_surface: "inline", fallback_surface: "inline-hitl",        can_show_both: false, hitl: true },
  send_whatsapp:          { default_surface: "inline", fallback_surface: "inline-hitl",        can_show_both: false, hitl: true },
  reject_candidate:       { default_surface: "inline", fallback_surface: "inline-hitl",        can_show_both: false, hitl: true },
  bulk_update_stage:      { default_surface: "inline", fallback_surface: "inline-hitl",        can_show_both: false, hitl: true },
  approve_job:            { default_surface: "inline", fallback_surface: "inline-hitl",        can_show_both: false, hitl: true },
  close_job:              { default_surface: "inline", fallback_surface: "inline-hitl",        can_show_both: false, hitl: true },

  // ── Ações instantâneas → inline-notification ──────────────────
  navigate_page:          { default_surface: "inline", fallback_surface: "inline-notification", can_show_both: false, hitl: false },
  open_ui:                { default_surface: "inline", fallback_surface: "inline-notification", can_show_both: false, hitl: false },

  // ── Wizard (já tem painel próprio) ────────────────────────────
  // Stages do wizard usam DynamicContextPanel diretamente via ws_stage_payload.
  // Não entram no SURFACE_CONFIG — são roteados pelo PANEL_REGISTRY (Phase 0).
} as const
```

### P1.3 — `useSurfaceForTool` hook

**Arquivo novo:** `src/hooks/chat/useSurfaceForTool.ts`

```typescript
import { SURFACE_CONFIG } from "@/lib/surface-config"
import { useLiaFloatContext } from "@/contexts/lia-float-context"

export function useSurfaceForTool(toolName: string, itemCount?: number): "inline" | "panel" {
  const { mode } = useLiaFloatContext()
  const isFullscreen = mode === "fullscreen"
  const config = SURFACE_CONFIG[toolName]

  if (!config) return "inline"         // safe default: desconhecido → inline
  if (config.hitl) return "inline"     // HITL: sempre inline, sem exceção
  if (!isFullscreen) return "inline"   // sidebar/floating: sem painel disponível

  if (config.density_threshold && itemCount !== undefined && itemCount <= config.density_threshold) {
    return "inline"
  }
  return config.default_surface
}
```

### P1.4 — ToolActivateContext (chat → painel)

**Arquivo:** `src/contexts/ToolSurfaceContext.tsx` (append)

```typescript
/**
 * Handler que o chat injeta. Clique num tool call row → abre painel focado no callId.
 * Ausente quando renderizando dentro do próprio painel (evita loop).
 */
export const ToolActivateContext = createContext<((callId: string) => void) | null>(null)
export const useToolActivate = () => useContext(ToolActivateContext)
```

**Uso em UnifiedChat.tsx:**
```tsx
const handleActivateTool = useCallback((callId: string) => {
  panelStore.openForToolCall(callId, conversationId)
  setWizardPanelMode("expanded")
}, [conversationId, setWizardPanelMode])

<ToolActivateContext.Provider value={hasDynamicPanelFull ? handleActivateTool : null}>
  <UnifiedMessageList ... />
</ToolActivateContext.Provider>
```

---

## Phase 2 — Tool Result Cards (maior ganho de UX)

**Objetivo:** eliminar o "texto puro" para os tool results mais usados pelo recrutador. Cada card existe em dois modos via `useToolSurface()`.

### Componentes a criar

#### CandidateResultCard

**Arquivo:** `src/components/unified-chat/tool-cards/CandidateResultCard.tsx`

```typescript
// Props comuns aos dois modos
interface Props {
  candidates: CandidateSummary[]
  totalCount: number
  query?: string
  onOpenPanel?: () => void
}

export function CandidateResultCard({ candidates, totalCount, query, onOpenPanel }: Props) {
  const surface = useToolSurface()

  // ── PANEL: lista completa sem cap de altura ──────────────────
  if (surface === "panel") {
    return (
      <div className="flex flex-col gap-2 px-1">
        {candidates.map(c => <CandidateRow key={c.id} candidate={c} expanded />)}
      </div>
    )
  }

  // ── INLINE: top 3 + "Ver todos N" ───────────────────────────
  const preview = candidates.slice(0, 3)
  return (
    <div className="rounded-lg border border-border-default bg-surface-primary p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{totalCount} candidatos encontrados</span>
        {onOpenPanel && (
          <button onClick={onOpenPanel} className="text-xs text-accent-primary hover:underline flex items-center gap-1">
            Ver todos <PanelRight className="size-3" />
          </button>
        )}
      </div>
      {preview.map(c => <CandidateRow key={c.id} candidate={c} />)}
      {totalCount > 3 && (
        <p className="text-xs text-content-secondary">+{totalCount - 3} outros</p>
      )}
    </div>
  )
}
```

#### JobListCard

**Arquivo:** `src/components/unified-chat/tool-cards/JobListCard.tsx`

Mesmo padrão: `useToolSurface()` → inline mostra top 5 com status badges; panel mostra lista completa com filtros.

#### CalibrationResultCard

**Arquivo:** `src/components/unified-chat/tool-cards/CalibrationResultCard.tsx`

Inline: score médio + top 3 candidatos calibrados. Panel: tabela completa com scores por critério.

### Wiring no UnifiedMessageList

```typescript
// src/components/unified-chat/UnifiedMessageList.tsx

// Detectar tool call de search_candidates no metadata:
if (meta?.type === "tool_result" && meta?.toolName === "search_candidates") {
  const activate = useToolActivate()
  const surface = useSurfaceForTool("search_candidates", meta.data?.candidates?.length)
  
  return (
    <ToolSurfaceContext.Provider value={surface}>
      <CandidateResultCard
        candidates={meta.data.candidates}
        totalCount={meta.data.total_count}
        onOpenPanel={activate ? () => activate(msg.id) : undefined}
      />
    </ToolSurfaceContext.Provider>
  )
}
```

### Backend: decorar tool results com metadata

Para que o FE saiba que uma mensagem contém um tool result específico, o backend precisa decorar o event com `tool_name` + `tool_call_id` no metadata. Isso já existe parcialmente para o wizard via `ws_stage_payload`. Para tools gerais, adicionar ao `serialize_message` em `chat_event_serializer.py`:

```python
# chat_event_serializer.py — extend existing serialization
if tool_result_metadata:
    payload["tool_result_metadata"] = {
        "tool_name": tool_result_metadata.tool_name,
        "tool_call_id": tool_result_metadata.tool_call_id,
        "data": tool_result_metadata.data,
    }
```

---

## Harness Engineering — GUIDE + SENSOR por mecanismo

### Mecanismo 1: SURFACE_CONFIG como única fonte de verdade

**Risco:** nova tool adicionada ao `recruiter_copilot` sem entrada no `SURFACE_CONFIG` → resultado aparece como texto puro silenciosamente.

**GUIDE (computacional):**
```
// src/lib/surface-config.ts — comentário no topo do arquivo:
// REGRA: toda tool que pode retornar dados estruturados para o chat
// DEVE ter uma entrada neste arquivo. Tools desconhecidas renderizam
// como texto puro (fallback seguro mas sem UX rica).
// Para adicionar: { default_surface, fallback_surface, can_show_both, hitl }
```

**SENSOR (computacional):** `plataforma-lia/scripts/check_surface_config_sync.py`
- Lê `SURFACE_CONFIG` de `surface-config.ts`
- Lê lista de tools do capability catalog (`docs/action-surface-registry/`)
- Reporta tools com card implementado em `UnifiedMessageList` sem entrada no SURFACE_CONFIG
- Mensagem otimizada para LLM: "Tool '{tool_name}' tem card em UnifiedMessageList mas não tem entrada em SURFACE_CONFIG. Adicione: `{tool_name}: { default_surface: '...', fallback_surface: '...', can_show_both: ..., hitl: ... }` em `src/lib/surface-config.ts`"

### Mecanismo 2: HITL tools → inline obrigatório

**Risco:** tool com aprovação humana configurada com `default_surface: "panel"` → recrutador não vê o botão de aprovação.

**GUIDE (computacional):** regra em `surface-config.ts`:
```typescript
// INVARIANT: toda tool com hitl: true DEVE ter default_surface: "inline"
// O painel não pode conter aprovações — o recrutador pode não abri-lo.
```

**SENSOR (computacional):** teste unitário em `surface-config.test.ts`:
```typescript
it("toda tool com hitl:true tem default_surface:inline", () => {
  for (const [name, config] of Object.entries(SURFACE_CONFIG)) {
    if (config.hitl) {
      expect(config.default_surface, `${name}: hitl tool deve ser inline`).toBe("inline")
    }
  }
})
```

### Mecanismo 3: PANEL_REGISTRY cobre todos os WizardStage values

**Risco:** stage novo adicionado ao wizard sem painel correspondente → `DynamicContextPanel` renderiza fallback silencioso.

**GUIDE (computacional):** tipo derivado do WizardStage union (TypeScript já enforça isso se o registry for tipado como `Record<WizardStage, ...>`).

**SENSOR (computacional):** teste em `DynamicContextPanel.panel-registry.test.ts`:
```typescript
import { WIZARD_STAGES } from "../wizard-types"
import { PANEL_REGISTRY } from "../DynamicContextPanel"

it("PANEL_REGISTRY cobre todos os WizardStage values", () => {
  for (const stage of WIZARD_STAGES) {
    expect(PANEL_REGISTRY[stage], `stage "${stage}" sem painel registrado`).toBeDefined()
  }
})
```

### Mecanismo 4: sem estado duplicado entre chat e painel

**Risco:** painel com estado próprio que diverge do histórico de mensagens → inconsistência visual.

**GUIDE (inferencial — CLAUDE.md):**
```
Adaptive Surface Selection — regra canônica:
O DynamicContextPanel é uma VIEW DERIVADA do histórico de tool calls.
Ele não tem estado de dados próprio. Recebe dados via props do lia-float-context,
que por sua vez deriva do histórico SSE. NUNCA fazer setPanelContent(data) em 
paralelo com a mensagem que já tem os mesmos dados.
```

**SENSOR (computacional):** grep no CI:
```bash
# Detecta estado duplicado em panel components
grep -rn "const \[.*Content.*\] = useState" src/components/unified-chat/wizard/panels/ \
  && echo "❌ Panel component com useState para dados — viola DynamicContextPanel como view derivada. Use props em vez de state local para dados que vêm do lia-float-context."
```

---

## Fases e Dependências

```
Phase 0 (Fundação)
  P0.1 focusedToolCallId em DynamicPanelData        ← sem dependências
  P0.2 PANEL_REGISTRY substitui switch              ← depende de WizardStage union completo
  P0.3 LiaPanelStore (Zustand)                      ← sem dependências
  
Phase 1 (Surface Pattern)
  P1.1 ToolSurfaceContext                           ← depende de P0.3
  P1.2 SURFACE_CONFIG                               ← sem dependências
  P1.3 useSurfaceForTool hook                       ← depende de P1.1 + P1.2
  P1.4 ToolActivateContext                          ← depende de P0.3 + P1.1
  
Phase 2 (Tool Result Cards)
  P2.1 CandidateResultCard                          ← depende de P1.1 + P1.3
  P2.2 JobListCard                                  ← depende de P1.1 + P1.3
  P2.3 CalibrationResultCard                        ← depende de P1.1 + P1.3
  P2.4 Backend: decorar tool_result_metadata        ← depende de nada (lia-agent-system)
  P2.5 Wiring em UnifiedMessageList                 ← depende de P2.1-2.3 + P1.4
```

---

## O que NÃO muda

- `DynamicContextPanel` continua sendo a coluna lateral — não é substituído
- `WizardJdCard` e `WizardWsiCard` continuam existindo como versões inline dos cards do wizard — na Fase 1 ganham `useToolSurface()` e passam a funcionar também no painel
- `lia-float-context` continua como orquestrador central — só ganha campos novos
- `ws_stage_payload` pipeline do wizard não muda
- Zero mudanças no `lia-agent-system` para Phases 0 e 1

---

## Anti-patterns a evitar (do research Suna)

1. ❌ **Modelo decide a superfície** — nenhum campo `display_surface` no output do agente
2. ❌ **Dois estados duplicados** — painel não tem `useState` para dados que já estão no histórico
3. ❌ **HITL no painel** — aprovações humanas nunca ficam "escondidas" no painel
4. ❌ **Painel sem persistência por sessão** — usar `_panelOpenBySession` no store
5. ❌ **Dense data inline sem truncamento** — sempre truncar com CTA "Ver todos" no modo sidebar

---

## Estimativa de Escopo

| Fase | Arquivos novos/modificados | Estimativa |
|---|---|---|
| Phase 0 | 3 modificados + 1 novo (LiaPanelStore) | ~3 sprints |
| Phase 1 | 3 novos + 2 modificados | ~5 sprints |
| Phase 2 | 4 novos + 2 modificados | ~6 sprints |
| Sensors harness | 2 scripts + 2 testes | ~2 sprints |
| **Total** | | **~16 sprints** |

---

## Fontes

- `kortix-ai/suna` — `tool-renderers.tsx`, `session-actions-panel.tsx`, `kortix-computer-store.ts` (código verificado)
- Auditoria `plataforma-lia` 2026-06-12 (este repositório, sessão ae76d08d)
- Pesquisa adaptive surface selection patterns 2026-06-12 (`/tmp/adaptive_surface_research.md`)
