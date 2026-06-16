# Wizard Manus F1 — Estados + Dock + Stepper + tools open/close_panel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Painel lateral do wizard vira opcional: inicia minimizado num dock acima do input (thumbnail vivo + progresso), expande/minimiza com escolha sticky, ✕ honesto, e a LIA pode abrir/fechar via tools `open_panel`/`close_panel`.

**Architecture:** FE: novo `wizardPanelMode: 'docked'|'expanded'` no `lia-float-context` (default docked, sticky por sessão de wizard, `done`/`handoff` força docked); novo `WizardDock` acima do input; `WizardProgressBar` sai do topo do chat (rodapé do painel quando expandido / dentro do dock quando minimizado). BE: 2 tools no padrão `navigate_to_jobs` (flag de state → payload `wizard_stage` → bridge FE) + prompt atualizado. Spec: `docs/superpowers/specs/2026-06-11-wizard-manus-optional-panel-design.md`.

**Tech Stack:** Next.js/React + Vitest (plataforma-lia) · Python/FastAPI + pytest (lia-agent-system) · tudo no Replit via `ssh replit-wedo-0405`, workspace `/home/runner/workspace/`.

---

## Regras de execução (NÃO PULAR)

1. **Branch:** antes de qualquer edit: `ssh replit-wedo-0405 'cd /home/runner/workspace && git branch --show-current'` → DEVE ser `feat/benefits-prv-canonical`. Se não for, checkout de volta e avisar.
2. **Hot files (REGRA 6):** `UnifiedChat.tsx` e `lia-float-context.tsx` são hot. Antes de tocar: `git log --since="6 hours ago" -- plataforma-lia/src/components/unified-chat/UnifiedChat.tsx plataforma-lia/src/contexts/lia-float-context.tsx`. Commits recentes de outra sessão → PARAR e avisar Paulo.
3. **Commits SEMPRE com pathspec** (REGRA 8): `git add <paths-explícitos> && git commit -m "..." -- <paths>`. Verificar `git log -1 --stat` (nº de arquivos = nº de paths nomeados). **NUNCA push.**
4. **Transferência de arquivos novos do Mac → Replit:** heredoc SSH corrompe; usar `base64 -i <local> | ssh replit-wedo-0405 'base64 -d > <remoto>'`. Edits pequenos: `python3` inline ou editar via sed só quando trivial — preferir mandar o arquivo inteiro por base64.
5. **Âncoras de linha são da leitura de 2026-06-11** — sessões paralelas commitam no mesmo repo. Se um trecho `old_string` não casar, re-grep pelo conteúdo (os snippets abaixo incluem strings únicas pra grep).
6. Strings de UI em PT hardcoded — segue o padrão atual do módulo unified-chat (i18n entra na F3 com o consent card).

---

### Task 1: `wizardPanelMode` no lia-float-context (estado + sticky + força-docked)

**Files:**
- Modify: `plataforma-lia/src/contexts/lia-float-context.tsx`
- Test: `plataforma-lia/src/contexts/__tests__/lia-float-context.panel-mode.test.tsx` (novo; espelhar harness do teste existente `lia-float-context.wizard-stage-bridge.test.ts` — localizar com `grep -rl "wizard-stage-bridge" plataforma-lia/src`)

- [ ] **Step 1: Ler o teste-harness existente do bridge** (imports, como renderiza o provider e consome o contexto) e escrever o teste novo no mesmo molde:

```tsx
// lia-float-context.panel-mode.test.tsx — adaptar imports ao harness do bridge test
import { describe, it, expect } from "vitest"
import { render, act } from "@testing-library/react"
// ... mesmo setup de Provider/consumer do bridge test ...

describe("wizardPanelMode — Manus F1", () => {
  it("default é 'docked'", () => {
    // render provider; expect(ctx.wizardPanelMode).toBe("docked")
  })

  it("setWizardPanelMode('expanded') persiste através de novos wizard_stage payloads (sticky)", () => {
    // act: ctx.setWizardPanelMode("expanded")
    // act: window.dispatchEvent(new CustomEvent("lia:wizard-stage-payload",
    //        { detail: { stage: "wsi_questions", data: {} } }))
    // expect(ctx.wizardPanelMode).toBe("expanded")  // payload NÃO reseta o modo
  })

  it("stage done/handoff força 'docked' mesmo se estava expanded", () => {
    // act: ctx.setWizardPanelMode("expanded")
    // act: dispatch payload { stage: "done", data: {} }
    // expect(ctx.wizardPanelMode).toBe("docked")
  })

  it("payload com data.panel_pref aplica o modo (tool open/close_panel)", () => {
    // act: dispatch payload { stage: "wsi_questions", data: { panel_pref: "expanded" } }
    // expect(ctx.wizardPanelMode).toBe("expanded")
    // act: dispatch payload { stage: "wsi_questions", data: { panel_pref: "docked" } }
    // expect(ctx.wizardPanelMode).toBe("docked")
  })
})
```

(Os corpos comentados viram código real copiando o setup do bridge test — ele já resolve Provider + consumer + dispatch de CustomEvent.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && npx vitest run src/contexts/__tests__/lia-float-context.panel-mode.test.tsx'`
Expected: FAIL (`wizardPanelMode` undefined).

- [ ] **Step 3: Implementar no contexto.** Em `lia-float-context.tsx`:

(a) Estado novo ao lado do `useState<LiaFloatState>` (âncora: `dynamicPanel: null,`) — manter FORA de `LiaFloatState` pra não mexer no shape existente:

```tsx
const [wizardPanelMode, setWizardPanelModeState] = useState<"docked" | "expanded">("docked")
const setWizardPanelMode = useCallback((mode: "docked" | "expanded") => {
  setWizardPanelModeState(mode)
}, [])
```

(b) No handler do bridge (âncora: `window.addEventListener("lia:wizard-stage-payload", handler)`), dentro de `handler` após o `openDynamicPanel({...})`:

```tsx
// Manus F1 — done/handoff recolhe pro dock; tool open/close_panel aplica preferência
if (stage === "done" || stage === "handoff") {
  setWizardPanelModeState("docked")
} else {
  const pref = (detail.data as Record<string, unknown> | undefined)?.panel_pref
  if (pref === "expanded" || pref === "docked") setWizardPanelModeState(pref)
}
```

(c) Exportar `wizardPanelMode` + `setWizardPanelMode` no value do Provider e no tipo do contexto (âncora: onde `openDynamicPanel`/`closeDynamicPanel` são expostos — grep `closeDynamicPanel,` no objeto value e na interface).

- [ ] **Step 4: Rodar e ver passar**

Run: mesmo comando do Step 2. Expected: PASS (4 testes). Rodar também o sensor existente do bridge: `npx vitest run src/contexts` → sem regressão.

- [ ] **Step 5: Commit**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace && git add plataforma-lia/src/contexts/__tests__/lia-float-context.panel-mode.test.tsx && git commit -m "feat(wizard-manus-f1): wizardPanelMode docked|expanded sticky no lia-float-context" -- plataforma-lia/src/contexts/lia-float-context.tsx plataforma-lia/src/contexts/__tests__/lia-float-context.panel-mode.test.tsx'
```

---

### Task 2: Componente `WizardDock` (thumbnail vivo + progresso + maximizar)

**Files:**
- Create: `plataforma-lia/src/components/unified-chat/wizard/WizardDock.tsx`
- Test: `plataforma-lia/src/components/unified-chat/wizard/__tests__/WizardDock.test.tsx`

- [ ] **Step 1: Teste primeiro**

```tsx
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { WizardDock } from "../WizardDock"

const baseProps = {
  stage: "wsi_questions" as const,
  stageLabel: "Perguntas WSI",
  requiresApproval: true,
  onExpand: vi.fn(),
  progressBar: <div data-testid="progress-slot" />,
  thumbnail: <div data-testid="thumb-slot" />,
}

describe("WizardDock — Manus F1", () => {
  it("renderiza label da etapa, slot de progresso e thumbnail inerte", () => {
    render(<WizardDock {...baseProps} />)
    expect(screen.getByText("Perguntas WSI")).toBeInTheDocument()
    expect(screen.getByTestId("progress-slot")).toBeInTheDocument()
    const thumb = screen.getByTestId("wizard-dock-thumbnail")
    expect(thumb).toHaveAttribute("aria-hidden", "true")
  })

  it("badge de pendência quando requiresApproval", () => {
    render(<WizardDock {...baseProps} />)
    expect(screen.getByText(/aprovação pendente/i)).toBeInTheDocument()
  })

  it("clique no card chama onExpand", () => {
    const onExpand = vi.fn()
    render(<WizardDock {...baseProps} onExpand={onExpand} />)
    fireEvent.click(screen.getByTestId("wizard-dock"))
    expect(onExpand).toHaveBeenCalledTimes(1)
  })

  it("smoke rerender mount/unmount sem throw (Rules of Hooks)", () => {
    const { rerender, unmount } = render(<WizardDock {...baseProps} />)
    rerender(<WizardDock {...baseProps} requiresApproval={false} />)
    unmount()
  })
})
```

- [ ] **Step 2: Rodar e ver falhar** (módulo inexistente).

- [ ] **Step 3: Implementar**

```tsx
"use client"

import { Maximize2 } from "lucide-react"
import type { ReactNode } from "react"

interface WizardDockProps {
  stage: string
  stageLabel: string
  requiresApproval: boolean
  onExpand: () => void
  /** WizardProgressBar compacto — projetado aqui quando o painel está docked */
  progressBar: ReactNode
  /** Painel real renderizado em escala (thumbnail vivo) — pointer-events none */
  thumbnail: ReactNode
}

/**
 * Manus F1 — card minimizado do painel do wizard, acima do input.
 * Padrão FloatingToolPreview (Suna): affordance viva + maximizar.
 * Container clicável é div role=button (NUNCA <button> aninhando interativos).
 */
export function WizardDock({
  stageLabel,
  requiresApproval,
  onExpand,
  progressBar,
  thumbnail,
}: WizardDockProps) {
  return (
    <div
      data-testid="wizard-dock"
      role="button"
      tabIndex={0}
      onClick={onExpand}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          onExpand()
        }
      }}
      aria-label={`Abrir painel: ${stageLabel}`}
      className="mx-3 mb-2 flex items-stretch gap-3 rounded-xl border border-lia-border-subtle bg-lia-bg-primary shadow-md shadow-black/10 p-2 cursor-pointer hover:border-wedo-cyan/50 transition-colors motion-reduce:transition-none"
    >
      <div
        data-testid="wizard-dock-thumbnail"
        aria-hidden="true"
        className="pointer-events-none select-none w-20 h-14 overflow-hidden rounded-md border border-lia-border-subtle bg-lia-bg-secondary flex-shrink-0"
      >
        <div className="origin-top-left scale-[0.18] w-[420px] h-[600px]">{thumbnail}</div>
      </div>
      <div className="flex-1 min-w-0 flex flex-col justify-center gap-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-lia-text-primary truncate">{stageLabel}</span>
          {requiresApproval && (
            <span className="px-1.5 py-0.5 rounded bg-status-warning/10 text-status-warning text-[10px] font-medium whitespace-nowrap">
              1 aprovação pendente
            </span>
          )}
        </div>
        <div className="min-w-0">{progressBar}</div>
      </div>
      <div className="flex items-center pr-1 text-lia-text-disabled">
        <Maximize2 className="w-4 h-4" aria-hidden="true" />
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Rodar e ver passar** + `npx eslint src/components/unified-chat/wizard/WizardDock.tsx --max-warnings=0`.

- [ ] **Step 5: Commit** (pathspec: os 2 arquivos novos, com `git add` explícito).

---

### Task 3: Wiring no UnifiedChat — gate por modo, dock acima do input, ✕ honesto

**Files:**
- Modify: `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx` (HOT — REGRA 6 antes)
- Modify: `plataforma-lia/src/components/unified-chat/wizard/DynamicContextPanel.tsx`
- Test: `plataforma-lia/src/components/unified-chat/wizard/__tests__/wizard-dock-wiring.test.tsx` (novo) + atualizar testes que assumam painel sempre visível (rodar suite e corrigir)

- [ ] **Step 1: Teste de wiring** — testar a lógica de gate como função pura extraída (evita renderizar UnifiedChat inteiro). Criar em `wizard/panel-visibility.ts`:

```ts
import { SPLIT_STAGES, type WizardStage } from "./DynamicContextPanel"

export type WizardPanelMode = "docked" | "expanded"

export function wizardPanelVisibility(args: {
  stage: string | null | undefined
  mode: WizardPanelMode
}): { showPanel: boolean; showDock: boolean } {
  const isSplit = !!args.stage && SPLIT_STAGES.includes(args.stage as WizardStage)
  return {
    showPanel: isSplit && args.mode === "expanded",
    showDock: isSplit && args.mode === "docked",
  }
}
```

Teste `__tests__/wizard-dock-wiring.test.tsx`:

```tsx
import { describe, it, expect } from "vitest"
import { wizardPanelVisibility } from "../panel-visibility"

describe("wizardPanelVisibility — Manus F1", () => {
  it("docked: dock visível, painel oculto", () => {
    expect(wizardPanelVisibility({ stage: "wsi_questions", mode: "docked" }))
      .toEqual({ showPanel: false, showDock: true })
  })
  it("expanded: painel visível, dock oculto", () => {
    expect(wizardPanelVisibility({ stage: "wsi_questions", mode: "expanded" }))
      .toEqual({ showPanel: true, showDock: false })
  })
  it("stage não-split (ex: pipeline_template) não mostra nada", () => {
    expect(wizardPanelVisibility({ stage: "pipeline_template", mode: "expanded" }))
      .toEqual({ showPanel: false, showDock: false })
  })
  it("sem stage não mostra nada", () => {
    expect(wizardPanelVisibility({ stage: null, mode: "docked" }))
      .toEqual({ showPanel: false, showDock: false })
  })
})
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar no UnifiedChat.** Consumir `wizardPanelMode`/`setWizardPanelMode` do contexto (mesmo hook de onde vêm `dynamicPanel`/`closeDynamicPanel`).

(a) Substituir o gate (âncora: `const hasDynamicPanel =`):

```tsx
const { showPanel: hasDynamicPanel, showDock: hasWizardDock } = wizardPanelVisibility({
  stage: dynamicPanel?.stage,
  mode: wizardPanelMode,
})
```

(b) No bloco do split view (âncora: `{hasDynamicPanel && (`): trocar `onClose={closeDynamicPanel}` por `onClose={() => setWizardPanelMode("docked")}`. `closeDynamicPanel` continua existindo para o fim real da sessão (não remover).

(c) Renderizar o dock imediatamente ANTES do componente de input (âncora: `onExecuteSlashCommand={handleNewChat}` — o dock entra acima desse bloco):

```tsx
{hasWizardDock && dynamicPanel && (
  <WizardDock
    stage={dynamicPanel.stage}
    stageLabel={WIZARD_STAGE_LABELS[dynamicPanel.stage] ?? dynamicPanel.stage}
    requiresApproval={dynamicPanel.requires_approval ?? false}
    onExpand={() => setWizardPanelMode("expanded")}
    progressBar={
      <WizardProgressBar
        currentStage={wizardStage}
        completeness={wizardCompleteness}
        stageHistory={wizardHistory}
        degradedStages={wizardDegradedStages}
        compact
        onCancelWizard={handleCancelWizard}
      />
    }
    thumbnail={
      <DynamicContextPanel
        stage={(dynamicPanel.stage as WizardStage) ?? null}
        data={dynamicPanel.data ?? {}}
        requiresApproval={false}
      />
    }
  />
)}
```

(d) `done`/`handoff` no dock: nada a fazer aqui — o contexto já força `docked` (Task 1) e o `DonePanel` renderiza no thumbnail; o painel deixa de ficar preso por construção.

- [ ] **Step 4: ✕ honesto no DynamicContextPanel.** Trocar o bloco do botão (âncora: `title="Cancelar criacao"`):

```tsx
{onClose && (
  <button
    onClick={onClose}
    className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-lia-text-disabled hover:text-lia-text-primary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
    title="Minimizar painel"
  >
    <Minimize2 className="w-3.5 h-3.5" />
    <span className="hidden sm:inline">Minimizar</span>
  </button>
)}
```

(import `Minimize2` de lucide-react; remover import `X` se ficar órfão). "Cancelar wizard" real permanece no `WizardProgressBar` (AlertDialog #1133) — inalterado.

- [ ] **Step 5: Rodar testes + lint**

Run: `npx vitest run src/components/unified-chat/wizard && npx eslint src/components/unified-chat/ --max-warnings=0 && npx tsc --noEmit`
Expected: PASS. Se testes existentes pinavam "Cancelar"/painel-sempre-aberto, atualizar os asserts (são pins do comportamento antigo, substituído por decisão de produto — anotar no commit).

- [ ] **Step 6: Commit** (pathspec: UnifiedChat.tsx, DynamicContextPanel.tsx, panel-visibility.ts, wizard-dock-wiring.test.tsx + testes ajustados).

---

### Task 4: Stepper sai do topo do chat → rodapé do painel (expandido)

**Files:**
- Modify: `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`
- Test: atualizar `__tests__` que pinem `data-testid="wizard-progress-bar"` no topo (grep antes: `grep -rn "wizard-progress-bar" plataforma-lia/src --include=*.test.*`)

- [ ] **Step 1: Mover o bloco.** Remover o bloco do topo do feed (âncora: comentário `Wizard progress bar — sticky at the top of the feed` até o `)}` correspondente). Dentro do container do split view (logo APÓS `<DynamicContextPanel ... />` e antes do fechamento do wrapper `rounded-xl`), adicionar:

```tsx
{wizardStage && (
  <div
    className="border-t border-lia-border-subtle flex-shrink-0"
    role="status"
    aria-live="polite"
    aria-label="Progresso do wizard de criação de vaga"
    data-testid="wizard-progress-bar"
  >
    <WizardProgressBar
      currentStage={wizardStage}
      completeness={wizardCompleteness}
      stageHistory={wizardHistory}
      degradedStages={wizardDegradedStages}
      compact
      onCancelWizard={handleCancelWizard}
    />
  </div>
)}
```

(O wrapper interno do painel precisa virar `flex flex-col`: painel `flex-1 min-h-0` + rodapé `flex-shrink-0`. Ajustar classes do `<div className="flex-1 min-w-0 rounded-xl ...">` para `flex flex-col`.)

- [ ] **Step 2: Rodar** `npx vitest run src/components/unified-chat && npx tsc --noEmit` → corrigir pins de layout antigos.

- [ ] **Step 3: Commit** (pathspec).

---

### Task 5 (BE): tools `open_panel` / `close_panel`

**Files:**
- Modify: `lia-agent-system/app/domains/job_creation/orchestrator/wizard_tools.py`
- Test: `lia-agent-system/tests/wizard/test_panel_tools.py` (novo)

- [ ] **Step 1: Teste primeiro**

```python
"""Manus F1 — tools open_panel/close_panel (padrão navigate_to_jobs)."""
import pytest

from app.domains.job_creation.orchestrator.wizard_tools import (
    OPEN_PANEL,
    CLOSE_PANEL,
    PURE_TOOLS,
    _handle_open_panel,
    _handle_close_panel,
)


def test_tools_registradas_em_pure_tools():
    names = {t.name for t in PURE_TOOLS}
    assert "open_panel" in names
    assert "close_panel" in names


def test_open_panel_seta_panel_pref_expanded():
    res = _handle_open_panel({}, {}, None)
    assert res.error is not True
    assert res.state_updates == {"panel_pref": "expanded"}
    assert "painel" in res.llm_message.lower()


def test_close_panel_seta_panel_pref_docked():
    res = _handle_close_panel({}, {}, None)
    assert res.error is not True
    assert res.state_updates == {"panel_pref": "docked"}


def test_schema_sem_propriedades_e_fechado():
    for tool in (OPEN_PANEL, CLOSE_PANEL):
        assert tool.input_schema["properties"] == {}
        assert tool.input_schema["additionalProperties"] is False


def test_rejeita_tenant_keys_no_input():
    res = _handle_open_panel({}, {"company_id": "x"}, None)
    assert res.error is True
```

(Se `_reject_tenant_keys` exigir `ctx`, espelhar a assinatura de `_handle_navigate_to_jobs` — mesmo arquivo, linha ~674.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && python -m pytest tests/wizard/test_panel_tools.py -x -q'`
Expected: ImportError.

- [ ] **Step 3: Implementar** em `wizard_tools.py`, logo após `_handle_navigate_to_jobs` (handler) e `NAVIGATE_TO_JOBS` (tool def):

```python
def _handle_open_panel(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Expande o painel lateral (ficha viva) no frontend — Manus F1."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    return ToolResult(
        llm_message=(
            "Painel lateral aberto — confirme ao recrutador que a ficha viva "
            "está visível ao lado."
        ),
        state_updates={"panel_pref": "expanded"},
    )


def _handle_close_panel(
    state: dict, tool_input: dict, ctx: ToolContext
) -> ToolResult:
    """Minimiza o painel lateral para o dock acima do input — Manus F1."""
    tenant_err = _reject_tenant_keys(tool_input)
    if tenant_err:
        return ToolResult(llm_message=tenant_err, error=True)
    return ToolResult(
        llm_message=(
            "Painel minimizado para o card acima do campo de mensagem — "
            "confirme ao recrutador que ele pode reabrir clicando no card."
        ),
        state_updates={"panel_pref": "docked"},
    )
```

```python
OPEN_PANEL = WizardTool(
    name="open_panel",
    description=(
        "Expande o painel lateral (ficha viva da vaga) no frontend. Use quando "
        "o recrutador pedir para 'abrir o painel', 'mostrar o painel', 'ver a "
        "ficha ao lado'."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_open_panel,
)

CLOSE_PANEL = WizardTool(
    name="close_panel",
    description=(
        "Minimiza o painel lateral para um card compacto acima do campo de "
        "mensagem. Use quando o recrutador pedir para 'fechar o painel', "
        "'esconder o painel', 'continuar só pelo chat'."
    ),
    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    handler=_handle_close_panel,
)
```

E adicionar `OPEN_PANEL, CLOSE_PANEL,` na tupla `PURE_TOOLS` (âncora: `NAVIGATE_TO_JOBS,` dentro de `PURE_TOOLS`, linha ~934).

- [ ] **Step 4: Rodar e ver passar** (5 testes) + regressão: `python -m pytest tests/wizard -x -q`.

- [ ] **Step 5: Commit** (pathspec: wizard_tools.py + tests/wizard/test_panel_tools.py).

---

### Task 6 (BE): `panel_pref` no payload do `wizard_stage`

**Files:**
- Modify: `lia-agent-system/app/domains/job_creation/services/wizard_session_service.py`
- Test: `lia-agent-system/tests/wizard/test_panel_pref_payload.py` (novo)

- [ ] **Step 1: Localizar o builder do payload do painel** — `grep -n "distribution_gap" app/domains/job_creation/services/wizard_session_service.py` (região ~1211: onde o dict `data` do stage é montado). Entender a função que monta o payload (mesma que popula `questions`/`distribution`).

- [ ] **Step 2: Teste primeiro** — testar que o payload inclui `panel_pref` quando presente no state e omite quando ausente, e que o state key é **consumido uma vez** (one-shot: depois de emitido, limpar para o payload seguinte não re-forçar o modo e quebrar o sticky do recrutador):

```python
"""Manus F1 — panel_pref viaja no payload do wizard_stage (one-shot)."""
# Espelhar o harness de teste existente que cobre distribution_gap no payload:
# grep -rn "distribution_gap" lia-agent-system/tests/ → usar o mesmo setup/mocks.


def test_payload_inclui_panel_pref_quando_no_state(...):
    # state com {"panel_pref": "docked"} → payload["data"]["panel_pref"] == "docked"
    ...


def test_payload_omite_panel_pref_quando_ausente(...):
    # state sem a key → "panel_pref" not in payload["data"]
    ...


def test_panel_pref_e_one_shot(...):
    # após montar o payload, state não carrega mais panel_pref
    # (próximo stage não re-emite e não sobrescreve escolha manual do recrutador)
    ...
```

(Os `...` viram código real copiando o harness do teste de `distribution_gap` — mesmos fixtures/mocks; é adaptação mecânica, não invenção.)

- [ ] **Step 3: Implementar** no builder do payload (junto do `distribution_gap`):

```python
# Manus F1 — preferência de painel one-shot (tools open_panel/close_panel)
panel_pref = state.pop("panel_pref", None)
if panel_pref in ("expanded", "docked"):
    data["panel_pref"] = panel_pref
```

(Se o builder não puder mutar `state`, usar o padrão local equivalente: ler + marcar consumido do jeito que o serviço já faz com flags one-shot — `grep -n "_navigate_to_jobs" wizard_session_service.py:77` mostra o precedente de flag lida do state.)

- [ ] **Step 4: Rodar e ver passar** + `python -m pytest tests/wizard -x -q` sem regressão.

- [ ] **Step 5: Commit** (pathspec).

---

### Task 7 (BE): prompt do wizard — painel controlável + etapa final com 3 opções

**Files:**
- Modify: `lia-agent-system/app/domains/job_creation/orchestrator/wizard_orchestrator.py` (seção `## Painel lateral (ficha viva)`, ~linhas 172-178)
- Modify: `lia-agent-system/app/domains/job_creation/orchestrator/wizard_service_tools.py` (`_handle_publish_job`, llm_message ~linha 476)
- Test: `lia-agent-system/tests/wizard/test_panel_prompt.py` (novo)

- [ ] **Step 1: Teste primeiro**

```python
"""Manus F1 — prompt do wizard reflete as novas capabilities de painel."""
from app.domains.job_creation.orchestrator import wizard_orchestrator


def _prompt() -> str:
    # localizar a constante/função do system prompt: grep -n "Painel lateral" wizard_orchestrator.py
    return wizard_orchestrator.WIZARD_SYSTEM_PROMPT  # ajustar ao nome real


def test_prompt_menciona_tools_de_painel():
    p = _prompt()
    assert "open_panel" in p
    assert "close_panel" in p


def test_prompt_nao_proibe_mais_controle_do_painel():
    p = _prompt()
    assert "NÃO controla o painel lateral" not in p


def test_prompt_mantem_anti_alucinacao_de_painel():
    # continua proibido AFIRMAR sem tool success
    p = _prompt()
    assert "sem ter chamado a TOOL correspondente" in p
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Substituir a seção do prompt** (âncora exata: `"## Painel lateral (ficha viva)\n"` até `"('Cancelar') e siga com o próximo passo real.\n\n"`):

```python
    "## Painel lateral (ficha viva)\n"
    "O painel lateral inicia MINIMIZADO como um card acima do campo de "
    "mensagem — o recrutador expande/minimiza quando quiser, e a escolha "
    "dele prevalece. Você TAMBÉM pode controlá-lo por tools: open_panel "
    "(expandir) e close_panel (minimizar para o card). Use close_panel "
    "quando ele pedir para 'fechar o painel' ou 'seguir só pelo chat'; use "
    "open_panel quando ele pedir para ver a ficha ao lado. NUNCA afirme que "
    "abriu/fechou o painel sem ter chamado a tool e recebido sucesso (mentira "
    "de ação, igual fingir publicação).\n\n"
```

- [ ] **Step 4: Etapa final com 3 opções.** Em `_handle_publish_job` (âncora: `"Avise o recrutador e ofereça os próximos passos (ver candidatos, etc.)."`), trocar por:

```python
            "Avise o recrutador e ofereça explicitamente as 3 opções: "
            "(1) ir para a página da vaga (navigate_to_jobs), (2) criar outra "
            "vaga, ou (3) continuar por aqui no chat (close_panel se ele "
            "preferir minimizar o painel)."
```

- [ ] **Step 5: Rodar e ver passar** + regressão `python -m pytest tests/wizard -x -q`.

- [ ] **Step 6: Commit** (pathspec: wizard_orchestrator.py, wizard_service_tools.py, tests/wizard/test_panel_prompt.py).

---

### Task 8: Verificação integrada + relatório

- [ ] **Step 1: Suites completas**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && npx vitest run src/components/unified-chat src/contexts && npx eslint src/components/unified-chat/ src/contexts/ --max-warnings=0 && npx tsc --noEmit'
ssh replit-wedo-0405 'cd /home/runner/workspace/lia-agent-system && python -m pytest tests/wizard -q'
```

Expected: tudo verde. Qualquer falha pré-existente alheia: reportar, não mascarar.

- [ ] **Step 2: Conferir commits** — `git log --oneline -8` deve mostrar ~6 commits F1, cada um com nº de arquivos = pathspec.

- [ ] **Step 3: Reportar a Paulo** — F1 pronta para validação live (porta 5000): criar vaga nova → painel inicia como dock; expandir/minimizar sticky; "feche o painel" via chat funciona; fim do wizard recolhe pro dock; stepper no rodapé do painel/dock.

---

## Fora deste plano (planos seguintes)

- **F2:** chat cards determinísticos (registry JD/WSI/Publicação + `stage_ref`) — plano próprio.
- **F3:** consent card lateral/bolha + regra estrutural fullscreen-only + remover `_autoFullscreenConversations` + i18n.
- **F4:** shared-element transition (Framer Motion layoutId), polish do thumbnail.
