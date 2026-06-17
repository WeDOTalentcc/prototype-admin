# Adaptive Surface Selection — Phase 0: Fundação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar `focusedToolCallId` ao pipeline do painel lateral, criar `LiaPanelStore` (Zustand por sessão) e substituir os lazy imports avulsos do `DynamicContextPanel` por um `PANEL_REGISTRY` declarativo — sem nenhuma mudança visual para o usuário.

**Architecture:** Três mudanças independentes que são precondições para a Phase 1 (ToolSurfaceContext). `LiaPanelStore` fornece estado per-session para o link chat↔painel. `focusedToolCallId` em `DynamicPanelData` permite que o painel saiba qual tool call o abriu. `PANEL_REGISTRY` substitui o switch hardcoded por um mapa declarativo, habilitando o sensor de harness que garante que stages novos tenham painéis correspondentes.

**Tech Stack:** TypeScript, React, Zustand (`create` from `zustand`), Vitest, SSH Replit (`replit-wedo-0405`), branch `feat/benefits-prv-canonical`

**Regras canônicas (OBRIGATÓRIO para cada commit):**
- `git commit -m "..." -- <path1> <path2>` (pathspec explícito — REGRA 8 CLAUDE.md)
- Verificar `git branch --show-current` = `feat/benefits-prv-canonical` antes de cada commit
- Todos os comandos via `ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && ...'`
- Nunca `git push`

---

## Mapa de arquivos

| Ação | Arquivo |
|---|---|
| CREATE | `src/stores/lia-panel-store.ts` |
| CREATE | `src/stores/__tests__/lia-panel-store.test.ts` |
| MODIFY | `src/contexts/lia-float-context.tsx` (linhas 79-85: interface DynamicPanelData) |
| CREATE | `src/components/unified-chat/wizard/panels/SchedulingPanel.tsx` |
| MODIFY | `src/components/unified-chat/wizard/DynamicContextPanel.tsx` (refactor lazy vars → PANEL_REGISTRY) |
| CREATE | `src/components/unified-chat/wizard/__tests__/DynamicContextPanel.panel-registry.test.ts` |

---

## Task 1: LiaPanelStore (Zustand per-session)

Cria o store que mantém `focusedToolCallId` e o estado de abertura do painel por sessão de conversa. Nenhuma mudança visual — o store ainda não é consumido nesta fase.

**Files:**
- Create: `plataforma-lia/src/stores/lia-panel-store.ts`
- Create: `plataforma-lia/src/stores/__tests__/lia-panel-store.test.ts`

- [ ] **Step 1: Escrever o teste que vai falhar**

Crie o arquivo `src/stores/__tests__/lia-panel-store.test.ts` com o seguinte conteúdo:

```typescript
// src/stores/__tests__/lia-panel-store.test.ts
// Mock registerStoreReset igual ao padrão dos outros stores neste diretório
vi.mock('../auth-store', () => ({
  registerStoreReset: vi.fn(),
}))

import { useLiaPanelStore } from '../lia-panel-store'
import { act } from '@testing-library/react'

const { getState, setState } = useLiaPanelStore

beforeEach(() => {
  act(() =>
    setState({
      focusedToolCallId: null,
      _panelOpenBySession: {},
    })
  )
})

describe('lia-panel-store', () => {
  it('starts with null focusedToolCallId and empty session map', () => {
    const s = getState()
    expect(s.focusedToolCallId).toBeNull()
    expect(s._panelOpenBySession).toEqual({})
  })

  it('openForToolCall sets focusedToolCallId and marks session open', () => {
    act(() => getState().openForToolCall('tc-abc', 'session-1'))
    const s = getState()
    expect(s.focusedToolCallId).toBe('tc-abc')
    expect(s._panelOpenBySession['session-1']).toBe(true)
  })

  it('closePanel marks session closed but preserves focusedToolCallId', () => {
    act(() => getState().openForToolCall('tc-abc', 'session-1'))
    act(() => getState().closePanel('session-1'))
    const s = getState()
    expect(s._panelOpenBySession['session-1']).toBe(false)
    expect(s.focusedToolCallId).toBe('tc-abc')
  })

  it('isPanelOpenForSession returns correct boolean', () => {
    act(() => getState().openForToolCall('tc-1', 'sess-A'))
    expect(getState().isPanelOpenForSession('sess-A')).toBe(true)
    expect(getState().isPanelOpenForSession('sess-B')).toBe(false)
    act(() => getState().closePanel('sess-A'))
    expect(getState().isPanelOpenForSession('sess-A')).toBe(false)
  })

  it('multiple sessions are independent', () => {
    act(() => getState().openForToolCall('tc-1', 'sess-A'))
    act(() => getState().openForToolCall('tc-2', 'sess-B'))
    act(() => getState().closePanel('sess-A'))
    expect(getState().isPanelOpenForSession('sess-A')).toBe(false)
    expect(getState().isPanelOpenForSession('sess-B')).toBe(true)
    // focusedToolCallId = last openForToolCall call
    expect(getState().focusedToolCallId).toBe('tc-2')
  })
})
```

- [ ] **Step 2: Rodar o teste para verificar que falha**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && npx vitest run src/stores/__tests__/lia-panel-store.test.ts --reporter=verbose 2>&1 | tail -20'
```

Esperado: `FAIL` com `Cannot find module '../lia-panel-store'`

- [ ] **Step 3: Criar o store**

Crie o arquivo `src/stores/lia-panel-store.ts`:

```typescript
// src/stores/lia-panel-store.ts
import { create } from 'zustand'
import { registerStoreReset } from './auth-store'

interface LiaPanelState {
  focusedToolCallId: string | null
  _panelOpenBySession: Record<string, boolean>
  openForToolCall: (callId: string, sessionId: string) => void
  closePanel: (sessionId: string) => void
  isPanelOpenForSession: (sessionId: string) => boolean
}

export const useLiaPanelStore = create<LiaPanelState>((set, get) => ({
  focusedToolCallId: null,
  _panelOpenBySession: {},

  openForToolCall: (callId, sessionId) =>
    set({
      focusedToolCallId: callId,
      _panelOpenBySession: { ...get()._panelOpenBySession, [sessionId]: true },
    }),

  closePanel: (sessionId) =>
    set({
      _panelOpenBySession: { ...get()._panelOpenBySession, [sessionId]: false },
    }),

  isPanelOpenForSession: (sessionId) =>
    get()._panelOpenBySession[sessionId] ?? false,
}))

registerStoreReset(() =>
  useLiaPanelStore.setState({ focusedToolCallId: null, _panelOpenBySession: {} })
)
```

- [ ] **Step 4: Rodar o teste para verificar que passa**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && npx vitest run src/stores/__tests__/lia-panel-store.test.ts --reporter=verbose 2>&1 | tail -20'
```

Esperado: `5 tests passed`

- [ ] **Step 5: Verificar branch e commitar**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && git branch --show-current'
```

Esperado: `feat/benefits-prv-canonical`

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && git add src/stores/lia-panel-store.ts src/stores/__tests__/lia-panel-store.test.ts && git commit -m "feat(adaptive-surface/P0.3): LiaPanelStore — focusedToolCallId + _panelOpenBySession por sessão (5 testes)" -- src/stores/lia-panel-store.ts src/stores/__tests__/lia-panel-store.test.ts'
```

Verificar: `git log -1 --stat` deve mostrar exatamente 2 arquivos.

---

## Task 2: `focusedToolCallId` em `DynamicPanelData`

Adiciona dois campos opcionais à interface `DynamicPanelData` em `lia-float-context.tsx`. Mudança puramente aditiva — nenhum consumer quebra porque os campos são opcionais.

**Files:**
- Modify: `plataforma-lia/src/contexts/lia-float-context.tsx` (linhas 79-85)

- [ ] **Step 1: Localizar a interface no arquivo**

```bash
ssh replit-wedo-0405 'grep -n "interface DynamicPanelData" /home/runner/workspace/plataforma-lia/src/contexts/lia-float-context.tsx'
```

Esperado: linha 79 (pode variar ±2 por commits anteriores).

- [ ] **Step 2: Verificar o conteúdo atual da interface**

```bash
ssh replit-wedo-0405 'sed -n "79,86p" /home/runner/workspace/plataforma-lia/src/contexts/lia-float-context.tsx'
```

Esperado:
```
export interface DynamicPanelData {
  panelType: DynamicPanelType;
  data: Record<string, unknown>;
  title?: string;
  stage?: string | null;
  requires_approval?: boolean;
}
```

- [ ] **Step 3: Aplicar a mudança**

Substitua o bloco acima pelo seguinte (dois campos novos ao final):

```typescript
export interface DynamicPanelData {
  panelType: DynamicPanelType;
  data: Record<string, unknown>;
  title?: string;
  stage?: string | null;
  requires_approval?: boolean;
  /** ID do tool call que abriu este painel. Usado pela Phase 1 para destacar
   *  o card relacionado no chat e pela LiaPanelStore para roteamento de foco. */
  focusedToolCallId?: string | null;
  /** Metadados de origem — qual tool + quando. Permite telemetria e deduplicação. */
  openedBy?: { toolName: string; toolCallId: string; ts: number } | null;
}
```

- [ ] **Step 4: Verificar que a suite de testes existente passa**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && npx vitest run --project=unit --project=unit-colocated 2>&1 | tail -15'
```

Esperado: todos os testes passam (sem novas falhas). TypeScript não deve reportar erros já que os campos são opcionais.

- [ ] **Step 5: Verificar branch e commitar**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && git branch --show-current'
```

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && git commit -m "feat(adaptive-surface/P0.1): DynamicPanelData + focusedToolCallId + openedBy (additive, todos campos opcionais)" -- src/contexts/lia-float-context.tsx'
```

Verificar: `git log -1 --stat` deve mostrar exatamente 1 arquivo.

---

## Task 3: SchedulingPanel + PANEL_REGISTRY + sensor de harness

Substitui os 12 `const XPanel = lazy(...)` avulsos por um `PANEL_REGISTRY` declarativo. A função `renderPanel()` continua funcionando com o mesmo switch (zero risco de regressão visual) — o PANEL_REGISTRY é adicionado como exportação paralela que habilita o sensor de harness. O sensor verifica que todos os `SPLIT_STAGES` têm entry no registry.

Também cria `SchedulingPanel.tsx` mínimo (atualmente `scheduling` retorna um `<div>` inline no switch — extrair para arquivo próprio é pré-requisito para registrá-lo no PANEL_REGISTRY).

**Files:**
- Create: `plataforma-lia/src/components/unified-chat/wizard/panels/SchedulingPanel.tsx`
- Modify: `plataforma-lia/src/components/unified-chat/wizard/DynamicContextPanel.tsx`
- Create: `plataforma-lia/src/components/unified-chat/wizard/__tests__/DynamicContextPanel.panel-registry.test.ts`

- [ ] **Step 1: Escrever o teste do sensor que vai falhar**

Crie o arquivo de teste:

```typescript
// src/components/unified-chat/wizard/__tests__/DynamicContextPanel.panel-registry.test.ts
/**
 * Sensor de harness P0.2 — garante que SPLIT_STAGES tem entrada no PANEL_REGISTRY.
 * Falha em CI se stage novo for adicionado a SPLIT_STAGES sem panel correspondente.
 */
import { SPLIT_STAGES } from '../DynamicContextPanel'
import { PANEL_REGISTRY } from '../DynamicContextPanel'

describe('PANEL_REGISTRY cobre todos os SPLIT_STAGES (harness P0.2)', () => {
  it('todo stage em SPLIT_STAGES tem entrada em PANEL_REGISTRY', () => {
    for (const stage of SPLIT_STAGES) {
      expect(
        PANEL_REGISTRY[stage],
        `Stage "${stage}" está em SPLIT_STAGES mas não tem entrada em PANEL_REGISTRY. ` +
        `Adicione: ${stage}: lazy(() => import("./panels/${toPascalCase(stage)}Panel"))` +
        ` no objeto PANEL_REGISTRY em DynamicContextPanel.tsx.`
      ).toBeDefined()
    }
  })
})

function toPascalCase(str: string): string {
  return str.replace(/(^|_)(\w)/g, (_, __, c) => c.toUpperCase())
}
```

- [ ] **Step 2: Rodar o teste para verificar que falha**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && npx vitest run src/components/unified-chat/wizard/__tests__/DynamicContextPanel.panel-registry.test.ts --reporter=verbose 2>&1 | tail -20'
```

Esperado: `FAIL` com `PANEL_REGISTRY is not exported from DynamicContextPanel` ou similar.

- [ ] **Step 3: Criar SchedulingPanel mínimo**

Crie `src/components/unified-chat/wizard/panels/SchedulingPanel.tsx`:

```typescript
// src/components/unified-chat/wizard/panels/SchedulingPanel.tsx
// Placeholder para o stage "scheduling". 
// Conteúdo real: integrar com CalendarIntegration (backlog Sprint post-Phase-1).
export function SchedulingPanel(_props: { data: Record<string, unknown> }) {
  return (
    <div className="p-4 text-sm text-lia-text-secondary">
      Agendamento de entrevistas...
    </div>
  )
}
```

- [ ] **Step 4: Adicionar PANEL_REGISTRY ao DynamicContextPanel.tsx**

Abrir `src/components/unified-chat/wizard/DynamicContextPanel.tsx`.

Após a última lazy import existente (linha ~45, após `const DonePanel = lazy(...)`), adicionar o import de SchedulingPanel e o objeto PANEL_REGISTRY:

```typescript
// Adicionar import logo após os lazy imports existentes (linha ~46):
const SchedulingPanel = lazy(() =>
  import("./panels/SchedulingPanel").then((m) => ({ default: m.SchedulingPanel }))
)

/**
 * Mapa declarativo stage → painel lazy.
 * Harness sensor em __tests__/DynamicContextPanel.panel-registry.test.ts
 * verifica que todo SPLIT_STAGES tem entrada aqui.
 * Phase 1 (ToolSurfaceContext) usará este registry para injetar surface context.
 */
export const PANEL_REGISTRY: Partial<Record<WizardStage, React.LazyExoticComponent<(props: Record<string, unknown>) => React.ReactElement | null>>> = {
  intake:       IntakePanel,
  jd_enrichment: JdEnrichmentPanel,
  bigfive:      BigFivePanel,
  salary:       SalaryPanel,
  competency:   CompetencyPanel,
  wsi_questions: WsiQuestionsPanel,
  eligibility:  EligibilityPanel,
  review:       ReviewPanel,
  publish:      PublishPanel,
  calibration:  CalibrationPanel,
  handoff:      HandoffPanel,
  done:         DonePanel,
  scheduling:   SchedulingPanel,
}
```

**IMPORTANTE:** a função `renderPanel()` e o switch permanecem exatamente como estão. Não alterar o switch. O PANEL_REGISTRY é apenas um export adicional para o sensor.

- [ ] **Step 5: Rodar o teste do sensor para verificar que passa**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && npx vitest run src/components/unified-chat/wizard/__tests__/DynamicContextPanel.panel-registry.test.ts --reporter=verbose 2>&1 | tail -20'
```

Esperado: `1 test passed`

- [ ] **Step 6: Rodar a suite completa para verificar zero regressões**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && npx vitest run --project=unit --project=unit-colocated --project=components 2>&1 | tail -20'
```

Esperado: todos os testes passam. Se `DynamicContextPanel.split-stages-canonical.test.ts` falhar por causa do `scheduling` stage, verificar que `scheduling` já estava em `SPLIT_STAGES` (estava desde commit `006bbb540`).

- [ ] **Step 7: Verificar branch e commitar**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && git branch --show-current'
```

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && git add \
  src/components/unified-chat/wizard/panels/SchedulingPanel.tsx \
  src/components/unified-chat/wizard/DynamicContextPanel.tsx \
  src/components/unified-chat/wizard/__tests__/DynamicContextPanel.panel-registry.test.ts \
  && git commit -m "feat(adaptive-surface/P0.2): PANEL_REGISTRY declarativo + SchedulingPanel + sensor de harness (cobre 13 SPLIT_STAGES)" -- \
  src/components/unified-chat/wizard/panels/SchedulingPanel.tsx \
  src/components/unified-chat/wizard/DynamicContextPanel.tsx \
  src/components/unified-chat/wizard/__tests__/DynamicContextPanel.panel-registry.test.ts'
```

Verificar: `git log -1 --stat` deve mostrar exatamente 3 arquivos.

---

## Verificação final da Phase 0

- [ ] **Rodar suite completa**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && npx vitest run 2>&1 | tail -15'
```

Esperado: todos os testes passam, sem regressões.

- [ ] **Verificar os 3 commits da Phase 0**

```bash
ssh replit-wedo-0405 'cd /home/runner/workspace/plataforma-lia && git log --oneline -5'
```

Esperado: 3 commits novos no topo com prefixos `feat(adaptive-surface/P0.1)`, `feat(adaptive-surface/P0.2)`, `feat(adaptive-surface/P0.3)`.

- [ ] **Verificar que nenhuma mudança visual ocorreu**

Phase 0 não tem mudanças visuais. O DynamicContextPanel funciona exatamente igual (switch inalterado). O único novo comportamento é o PANEL_REGISTRY exportado (usado pelo sensor de teste) e os campos opcionais em DynamicPanelData (consumers não os lêem ainda).

---

## O que esta fase habilita

Após a Phase 0:
- **Phase 1** pode criar `ToolSurfaceContext` e wiring no DynamicContextPanel usando `PANEL_REGISTRY` para injetar context
- **Phase 1** pode usar `LiaPanelStore.openForToolCall` para ligar clique no card do chat → abertura do painel
- **Phase 2** pode usar `focusedToolCallId` para destacar o card relacionado no chat quando o painel está aberto
- O **sensor de harness** `DynamicContextPanel.panel-registry.test.ts` bloqueará stages novos sem painel correspondente

## O que NÃO muda nesta fase

- Zero mudanças visuais para o usuário
- `renderPanel()` switch permanece inalterado (zero risco)
- `lia-float-context.tsx` continua como orquestrador (campos novos são opcionais)
- `lia-agent-system` não é tocado (Phase 0 e 1 são 100% FE)
- `ws_stage_payload` pipeline do wizard não muda
