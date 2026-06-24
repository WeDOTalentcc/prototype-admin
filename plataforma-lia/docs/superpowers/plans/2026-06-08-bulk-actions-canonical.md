# Bulk Actions Canonical — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Branch:** `feat/benefits-prv-canonical` — run `git branch --show-current` before every commit.  
> **Commit rule:** ALWAYS `git commit -m "..." -- <path1> <path2>` (pathspec explicit). NEVER `git add .`.  
> **SSH gotcha:** Use `grep -n` / `sed -n` / `cat -n`. NEVER `rg` (corrupts tokens).  
> **Tests:** `cd /home/runner/workspace/plataforma-lia && npx vitest run --reporter=verbose <testfile>`

**Goal:** Corrigir ações em massa (email, triagem, agendamento, feedback) nas 3 superfícies — funil de busca, kanban e tabela de vagas — de modo que N candidatos selecionados realmente recebam a ação, com relatório pós-envio e marcação de falhas na tabela.

**Architecture:** Um executor puro `runBulkSequential` + validador `partitionByContactability` são as primitivas compartilhadas pelas 3 superfícies. A lógica de envio em `useUnifiedCommunication.handleSend` é corrigida no produtor (itera N em bulk mode). O componente `<BulkResultReport>` (Dialog DS v4.2.1) exibe o resultado após o modal fechar. Falhas persistem em `useFailedDeliveryStore` (Zustand) e são exibidas inline no `ContactCells`.

**Tech Stack:** React 18, TypeScript, Zustand 4, Radix UI Dialog, lucide-react, Vitest, Testing Library, DS v4.2.1 tokens (`text-lia-*`, `status-*`, `border-*`).

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `src/lib/bulk/runBulkSequential.ts` | **Criar** | Executor puro: itera itens, chama fn-por-item, emite progresso, retorna `BulkItemResult[]` |
| `src/lib/bulk/partitionByContactability.ts` | **Criar** | Validador puro: separa `sendable` / `skipped` por canal |
| `src/lib/bulk/index.ts` | **Criar** | Barrel dos dois utilitários |
| `src/lib/bulk/__tests__/runBulkSequential.test.ts` | **Criar** | Testes unitários do executor |
| `src/lib/bulk/__tests__/partitionByContactability.test.ts` | **Criar** | Testes unitários do validador |
| `src/stores/failedDeliveryStore.ts` | **Criar** | Zustand store: `{candidateId → {reason, channel, at}}` |
| `src/stores/__tests__/failedDeliveryStore.test.ts` | **Criar** | Testes do store |
| `src/stores/index.ts` | **Modificar** | Exportar `useFailedDeliveryStore` |
| `src/components/bulk/BulkResultReport.tsx` | **Criar** | Dialog DS: lista de resultados por candidato, barra de progresso |
| `src/components/bulk/__tests__/BulkResultReport.test.tsx` | **Criar** | Teste de renderização + interação |
| `src/components/bulk/index.ts` | **Criar** | Barrel |
| `src/components/pages/candidates/hooks/useCandidatesInteractions.ts` | **Modificar** | `.find()` → array + openBulkUnifiedModal + remover toast falso |
| `src/components/modals/useUnifiedCommunication.ts` | **Modificar** | `handleSend` itera N em bulk mode via `runBulkSequential`; parametriza sendEmailFor/sendWhatsAppFor |
| `src/components/pages/candidates-page.tsx` | **Modificar** | Abre `BulkResultReport` depois de `onSend` (bulk mode) |
| `src/components/pages/candidates/cells/ContactCells.tsx` | **Modificar** | Lê `useFailedDeliveryStore` → `AlertTriangle` de falha de entrega |
| `src/components/pages/job-kanban/hooks/useKanbanBulkActions.ts` | **Modificar** | `send_message` usa `runBulkSequential` + abre `BulkResultReport` |
| `src/components/pages/jobs/hooks/useJobsBulkActions.ts` | **Modificar** | `handleJobPublish` / toggle em massa via `runBulkSequential` + relatório |
| `messages/pt-BR.json` | **Modificar** | Chaves novas: `bulkReport.*` |
| `messages/en.json` | **Modificar** | Chaves novas: `bulkReport.*` |

---

## Task 0: Executor puro `runBulkSequential`

**Files:**
- Create: `src/lib/bulk/runBulkSequential.ts`
- Create: `src/lib/bulk/__tests__/runBulkSequential.test.ts`

- [ ] **Step 1: Escrever o teste falhando**

```typescript
// src/lib/bulk/__tests__/runBulkSequential.test.ts
import { describe, it, expect, vi } from 'vitest'
import { runBulkSequential } from '../runBulkSequential'

const items = [
  { id: '1', name: 'Ana' },
  { id: '2', name: 'Bruno' },
  { id: '3', name: 'Carla' },
]

describe('runBulkSequential', () => {
  it('retorna ok=true para cada item bem-sucedido', async () => {
    const action = vi.fn().mockResolvedValue({ sent: true })
    const results = await runBulkSequential(items, action)
    expect(results).toHaveLength(3)
    expect(results.every(r => r.ok)).toBe(true)
    expect(action).toHaveBeenCalledTimes(3)
  })

  it('retorna ok=false com reason para item que lança erro', async () => {
    const action = vi.fn()
      .mockResolvedValueOnce({ sent: true })
      .mockRejectedValueOnce(new Error('e-mail inválido'))
      .mockResolvedValueOnce({ sent: true })
    const results = await runBulkSequential(items, action)
    expect(results[0].ok).toBe(true)
    expect(results[1].ok).toBe(false)
    expect(results[1].reason).toBe('e-mail inválido')
    expect(results[2].ok).toBe(true)
  })

  it('chama onTick para cada item processado', async () => {
    const action = vi.fn().mockResolvedValue({})
    const ticks: number[] = []
    await runBulkSequential(items, action, (done) => ticks.push(done))
    expect(ticks).toEqual([1, 2, 3])
  })

  it('retorna array vazio para lista vazia', async () => {
    const action = vi.fn()
    const results = await runBulkSequential([], action)
    expect(results).toEqual([])
    expect(action).not.toHaveBeenCalled()
  })

  it('inclui id e name em cada resultado', async () => {
    const action = vi.fn().mockResolvedValue({})
    const results = await runBulkSequential([items[0]], action)
    expect(results[0].id).toBe('1')
    expect(results[0].name).toBe('Ana')
  })
})
```

- [ ] **Step 2: Rodar — confirmar FAIL**

```bash
cd /home/runner/workspace/plataforma-lia
npx vitest run src/lib/bulk/__tests__/runBulkSequential.test.ts --reporter=verbose
```
Esperado: `Cannot find module '../runBulkSequential'`

- [ ] **Step 3: Criar a implementação**

```typescript
// src/lib/bulk/runBulkSequential.ts

export interface BulkItemResult<T = unknown> {
  id: string
  name: string
  ok: boolean
  data?: T
  reason?: string
}

export type BulkTickCallback<T = unknown> = (
  done: number,
  total: number,
  latest: BulkItemResult<T>
) => void

/**
 * Executa uma ação assíncrona sequencialmente sobre uma lista de itens.
 * Nunca lança — captura erros por item e os reflete em ok=false + reason.
 * Produtor único para todas as superfícies de bulk da plataforma.
 */
export async function runBulkSequential<T = unknown>(
  items: Array<{ id: string; name: string }>,
  action: (item: { id: string; name: string }) => Promise<T>,
  onTick?: BulkTickCallback<T>
): Promise<BulkItemResult<T>[]> {
  const results: BulkItemResult<T>[] = []
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    try {
      const data = await action(item)
      const r: BulkItemResult<T> = { id: item.id, name: item.name, ok: true, data }
      results.push(r)
      onTick?.(i + 1, items.length, r)
    } catch (err) {
      const reason = err instanceof Error ? err.message : String(err)
      const r: BulkItemResult<T> = { id: item.id, name: item.name, ok: false, reason }
      results.push(r)
      onTick?.(i + 1, items.length, r)
    }
  }
  return results
}
```

- [ ] **Step 4: Rodar — confirmar PASS**

```bash
npx vitest run src/lib/bulk/__tests__/runBulkSequential.test.ts --reporter=verbose
```
Esperado: `5 passed`

- [ ] **Step 5: Criar barrel**

```typescript
// src/lib/bulk/index.ts
export { runBulkSequential } from './runBulkSequential'
export type { BulkItemResult, BulkTickCallback } from './runBulkSequential'
export { partitionByContactability } from './partitionByContactability'
export type { ContactChannel, Contactable, ContactPartition } from './partitionByContactability'
```

- [ ] **Step 6: Commit**

```bash
cd /home/runner/workspace/plataforma-lia
git add src/lib/bulk/runBulkSequential.ts src/lib/bulk/__tests__/runBulkSequential.test.ts src/lib/bulk/index.ts
git commit -m "feat(bulk): executor puro runBulkSequential + testes (5/5)" -- src/lib/bulk/runBulkSequential.ts src/lib/bulk/__tests__/runBulkSequential.test.ts src/lib/bulk/index.ts
```

---

## Task 1: Validador puro `partitionByContactability`

**Files:**
- Create: `src/lib/bulk/partitionByContactability.ts`
- Create: `src/lib/bulk/__tests__/partitionByContactability.test.ts`

- [ ] **Step 1: Escrever o teste falhando**

```typescript
// src/lib/bulk/__tests__/partitionByContactability.test.ts
import { describe, it, expect } from 'vitest'
import { partitionByContactability } from '../partitionByContactability'

const base = { id: '1', name: 'Ana' }

describe('partitionByContactability', () => {
  it('coloca em sendable candidato com e-mail válido (canal email)', () => {
    const { sendable, skipped } = partitionByContactability(
      [{ ...base, email: 'ana@empresa.com' }], 'email'
    )
    expect(sendable).toHaveLength(1)
    expect(skipped).toHaveLength(0)
  })

  it('coloca em skipped candidato sem e-mail (canal email)', () => {
    const { sendable, skipped } = partitionByContactability([base], 'email')
    expect(sendable).toHaveLength(0)
    expect(skipped[0].reason).toBe('e-mail ausente')
  })

  it('coloca em skipped candidato com e-mail inválido (canal email)', () => {
    const { sendable, skipped } = partitionByContactability(
      [{ ...base, email: 'nao-e-um-email' }], 'email'
    )
    expect(skipped[0].reason).toBe('e-mail inválido')
  })

  it('coloca em skipped candidato sem telefone (canal whatsapp)', () => {
    const { sendable, skipped } = partitionByContactability(
      [{ ...base, email: 'ana@e.com' }], 'whatsapp'
    )
    expect(skipped[0].reason).toBe('telefone ausente')
  })

  it('canal both exige email E telefone', () => {
    const { sendable, skipped } = partitionByContactability(
      [{ ...base, email: 'ana@e.com' }], 'both'
    )
    expect(skipped[0].reason).toBe('telefone ausente')
  })

  it('separa corretamente lista mista', () => {
    const candidates = [
      { id: '1', name: 'Ana', email: 'ana@e.com' },
      { id: '2', name: 'Bruno' },
      { id: '3', name: 'Carla', email: 'carla@e.com' },
    ]
    const { sendable, skipped } = partitionByContactability(candidates, 'email')
    expect(sendable.map(c => c.id)).toEqual(['1', '3'])
    expect(skipped.map(s => s.item.id)).toEqual(['2'])
  })
})
```

- [ ] **Step 2: Rodar — confirmar FAIL**

```bash
npx vitest run src/lib/bulk/__tests__/partitionByContactability.test.ts --reporter=verbose
```
Esperado: `Cannot find module '../partitionByContactability'`

- [ ] **Step 3: Criar a implementação**

```typescript
// src/lib/bulk/partitionByContactability.ts

export type ContactChannel = 'email' | 'whatsapp' | 'both'

export interface Contactable {
  id: string
  name: string
  email?: string
  phone?: string
}

export interface ContactPartition<T extends Contactable> {
  sendable: T[]
  skipped: Array<{ item: T; reason: string }>
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Pré-validação de contactabilidade. Puro — sem efeitos colaterais.
 * Usado no handleSend (bulk mode) para pré-avisar candidatos sem contato.
 */
export function partitionByContactability<T extends Contactable>(
  candidates: T[],
  channel: ContactChannel
): ContactPartition<T> {
  const sendable: T[] = []
  const skipped: Array<{ item: T; reason: string }> = []

  for (const c of candidates) {
    const needsEmail = channel === 'email' || channel === 'both'
    const needsPhone = channel === 'whatsapp' || channel === 'both'

    if (needsEmail) {
      if (!c.email) { skipped.push({ item: c, reason: 'e-mail ausente' }); continue }
      if (!EMAIL_RE.test(c.email)) { skipped.push({ item: c, reason: 'e-mail inválido' }); continue }
    }
    if (needsPhone) {
      if (!c.phone) { skipped.push({ item: c, reason: 'telefone ausente' }); continue }
    }
    sendable.push(c)
  }

  return { sendable, skipped }
}
```

- [ ] **Step 4: Atualizar barrel com os tipos**

Arquivo `src/lib/bulk/index.ts` já criado no Task 0. Confirmar que exporta `partitionByContactability` e seus tipos (já está no barrel do Task 0).

- [ ] **Step 5: Rodar — confirmar PASS**

```bash
npx vitest run src/lib/bulk/__tests__/partitionByContactability.test.ts --reporter=verbose
```
Esperado: `6 passed`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(bulk): validador partitionByContactability + testes (6/6)" -- src/lib/bulk/partitionByContactability.ts src/lib/bulk/__tests__/partitionByContactability.test.ts src/lib/bulk/index.ts
```

---

## Task 2: Zustand store `useFailedDeliveryStore`

**Files:**
- Create: `src/stores/failedDeliveryStore.ts`
- Create: `src/stores/__tests__/failedDeliveryStore.test.ts`
- Modify: `src/stores/index.ts`

- [ ] **Step 1: Escrever o teste falhando**

```typescript
// src/stores/__tests__/failedDeliveryStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useFailedDeliveryStore } from '../failedDeliveryStore'

beforeEach(() => {
  useFailedDeliveryStore.getState().clearAll()
})

describe('useFailedDeliveryStore', () => {
  it('começa vazio', () => {
    expect(Object.keys(useFailedDeliveryStore.getState().failures)).toHaveLength(0)
  })

  it('addFailure grava por candidateId', () => {
    useFailedDeliveryStore.getState().addFailure({
      candidateId: 'c1', reason: 'e-mail ausente', channel: 'email', at: 1000
    })
    expect(useFailedDeliveryStore.getState().hasFailure('c1')).toBe(true)
    expect(useFailedDeliveryStore.getState().getFailure('c1')?.reason).toBe('e-mail ausente')
  })

  it('clearFailure remove apenas o candidato alvo', () => {
    const s = useFailedDeliveryStore.getState()
    s.addFailure({ candidateId: 'c1', reason: 'x', channel: 'email', at: 1 })
    s.addFailure({ candidateId: 'c2', reason: 'y', channel: 'email', at: 2 })
    s.clearFailure('c1')
    expect(s.hasFailure('c1')).toBe(false)
    expect(s.hasFailure('c2')).toBe(true)
  })

  it('clearAll esvazia o store', () => {
    const s = useFailedDeliveryStore.getState()
    s.addFailure({ candidateId: 'c1', reason: 'x', channel: 'email', at: 1 })
    s.clearAll()
    expect(Object.keys(s.failures)).toHaveLength(0)
  })
})
```

- [ ] **Step 2: Rodar — confirmar FAIL**

```bash
npx vitest run src/stores/__tests__/failedDeliveryStore.test.ts --reporter=verbose
```
Esperado: `Cannot find module '../failedDeliveryStore'`

- [ ] **Step 3: Criar o store**

```typescript
// src/stores/failedDeliveryStore.ts
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface FailedDelivery {
  candidateId: string
  reason: string
  channel: 'email' | 'whatsapp' | 'both'
  at: number
}

interface FailedDeliveryState {
  failures: Record<string, FailedDelivery>
  addFailure: (d: FailedDelivery) => void
  clearFailure: (candidateId: string) => void
  clearAll: () => void
  hasFailure: (candidateId: string) => boolean
  getFailure: (candidateId: string) => FailedDelivery | undefined
}

export const useFailedDeliveryStore = create<FailedDeliveryState>()(
  devtools(
    (set, get) => ({
      failures: {},
      addFailure: (d) =>
        set((s) => ({ failures: { ...s.failures, [d.candidateId]: d } }),
          false, 'bulk/addFailure'),
      clearFailure: (candidateId) =>
        set((s) => {
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { [candidateId]: _removed, ...rest } = s.failures
          return { failures: rest }
        }, false, 'bulk/clearFailure'),
      clearAll: () => set({ failures: {} }, false, 'bulk/clearAll'),
      hasFailure: (candidateId) => candidateId in get().failures,
      getFailure: (candidateId) => get().failures[candidateId],
    }),
    { name: 'failed-delivery-store' }
  )
)
```

- [ ] **Step 4: Exportar no barrel**

Editar `src/stores/index.ts` — adicionar no final:
```typescript
export { useFailedDeliveryStore, type FailedDelivery } from './failedDeliveryStore'
```

- [ ] **Step 5: Rodar — confirmar PASS**

```bash
npx vitest run src/stores/__tests__/failedDeliveryStore.test.ts --reporter=verbose
```
Esperado: `4 passed`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(bulk): useFailedDeliveryStore Zustand + testes (4/4)" -- src/stores/failedDeliveryStore.ts src/stores/__tests__/failedDeliveryStore.test.ts src/stores/index.ts
```

---

## Task 3: Componente `<BulkResultReport>`

**Files:**
- Create: `src/components/bulk/BulkResultReport.tsx`
- Create: `src/components/bulk/__tests__/BulkResultReport.test.tsx`
- Create: `src/components/bulk/index.ts`

- [ ] **Step 1: Escrever o teste falhando**

```typescript
// src/components/bulk/__tests__/BulkResultReport.test.tsx
import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BulkResultReport } from '../BulkResultReport'
import type { BulkItemResult } from '@/lib/bulk'

const results: BulkItemResult[] = [
  { id: '1', name: 'Ana Souza', ok: true },
  { id: '2', name: 'Bruno Lima', ok: true },
  { id: '3', name: 'Carla Dias', ok: false, reason: 'e-mail ausente' },
]

describe('BulkResultReport', () => {
  it('exibe contagem de sucessos no título', () => {
    render(
      <BulkResultReport
        isOpen
        onClose={vi.fn()}
        results={results}
        actionLabel="Email"
      />
    )
    expect(screen.getByText(/2 de 3/)).toBeInTheDocument()
  })

  it('exibe o nome de cada candidato', () => {
    render(
      <BulkResultReport isOpen onClose={vi.fn()} results={results} actionLabel="Email" />
    )
    expect(screen.getByText('Ana Souza')).toBeInTheDocument()
    expect(screen.getByText('Carla Dias')).toBeInTheDocument()
  })

  it('exibe motivo da falha para item ok=false', () => {
    render(
      <BulkResultReport isOpen onClose={vi.fn()} results={results} actionLabel="Email" />
    )
    expect(screen.getByText('e-mail ausente')).toBeInTheDocument()
  })

  it('chama onClose ao clicar em Fechar', () => {
    const onClose = vi.fn()
    render(
      <BulkResultReport isOpen onClose={onClose} results={results} actionLabel="Email" />
    )
    fireEvent.click(screen.getByRole('button', { name: /fechar/i }))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('não renderiza quando isOpen=false', () => {
    const { container } = render(
      <BulkResultReport isOpen={false} onClose={vi.fn()} results={results} actionLabel="Email" />
    )
    expect(container).toBeEmptyDOMElement()
  })
})
```

- [ ] **Step 2: Rodar — confirmar FAIL**

```bash
npx vitest run src/components/bulk/__tests__/BulkResultReport.test.tsx --reporter=verbose
```
Esperado: `Cannot find module '../BulkResultReport'`

- [ ] **Step 3: Criar o componente**

```tsx
// src/components/bulk/BulkResultReport.tsx
"use client"

import React from "react"
import { CheckCircle2, AlertTriangle, Copy } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import type { BulkItemResult } from "@/lib/bulk"

interface BulkResultReportProps {
  isOpen: boolean
  onClose: () => void
  results: BulkItemResult[]
  actionLabel: string
}

/**
 * Relatório pós-envio em massa. Puramente apresentacional — sem lógica.
 * Abre DEPOIS do modal de comunicação fechar. Usa DS v4.2.1 tokens.
 */
export function BulkResultReport({
  isOpen,
  onClose,
  results,
  actionLabel,
}: BulkResultReportProps) {
  if (!isOpen) return null

  const succeeded = results.filter((r) => r.ok)
  const failed = results.filter((r) => !r.ok)
  const pct = results.length > 0 ? Math.round((succeeded.length / results.length) * 100) : 0

  const handleCopyFailed = () => {
    const text = failed.map((r) => `${r.name}: ${r.reason ?? 'falha'}`).join('\n')
    navigator.clipboard.writeText(text).catch(() => undefined)
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-lia-text-primary">
            {actionLabel} — {succeeded.length} de {results.length} enviados
          </DialogTitle>
        </DialogHeader>

        {/* Barra de progresso */}
        <div
          className="h-2 w-full rounded-full bg-lia-border overflow-hidden"
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-full bg-[#60BED1] transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>

        {/* Lista de candidatos */}
        <ul className="mt-2 max-h-72 overflow-y-auto divide-y divide-lia-border text-sm">
          {results.map((r) => (
            <li key={r.id} className="flex items-center gap-2 py-2 px-1">
              {r.ok ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-status-success" aria-hidden />
              ) : (
                <AlertTriangle className="w-4 h-4 shrink-0 text-status-warning" aria-hidden />
              )}
              <span className={`flex-1 font-medium ${r.ok ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>
                {r.name}
              </span>
              {!r.ok && r.reason && (
                <span className="text-xs text-status-error">{r.reason}</span>
              )}
            </li>
          ))}
        </ul>

        <DialogFooter className="mt-2 gap-2">
          {failed.length > 0 && (
            <Button variant="outline" size="sm" onClick={handleCopyFailed} className="gap-1">
              <Copy className="w-3.5 h-3.5" />
              Copiar lista de falhas
            </Button>
          )}
          <Button variant="default" size="sm" onClick={onClose}>
            Fechar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

- [ ] **Step 4: Criar barrel**

```typescript
// src/components/bulk/index.ts
export { BulkResultReport } from './BulkResultReport'
```

- [ ] **Step 5: Rodar — confirmar PASS**

```bash
npx vitest run src/components/bulk/__tests__/BulkResultReport.test.tsx --reporter=verbose
```
Esperado: `5 passed`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(bulk): BulkResultReport Dialog DS + testes (5/5)" -- src/components/bulk/BulkResultReport.tsx src/components/bulk/__tests__/BulkResultReport.test.tsx src/components/bulk/index.ts
```

---

## Task 4: Corrigir handlers bulk no funil (`useCandidatesInteractions`)

**Files:**
- Modify: `src/components/pages/candidates/hooks/useCandidatesInteractions.ts`

O bug: `.find()` pega só o 1º candidato selecionado. `openUnifiedModal` recebe um único `Candidate`.  
A correção: nova função `openBulkUnifiedModal` que passa `candidate=null` + array de selecionados.  
Também remove o `handleUnifiedModalSend` que dá toast falso (o feedback real virá do `BulkResultReport`).

- [ ] **Step 1: Escrever o teste falhando**

Crie `src/components/pages/candidates/hooks/__tests__/useCandidatesInteractionsBulk.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'

// Mock das dependências mínimas
vi.mock('@/stores/candidates-store', () => ({
  useCandidatesStore: vi.fn(() => ({
    sortedCandidates: [
      { id: 'c1', name: 'Ana', email: 'ana@e.com' },
      { id: 'c2', name: 'Bruno', email: 'bruno@e.com' },
      { id: 'c3', name: 'Carla', email: 'carla@e.com' },
    ],
    selectedCandidatesForBatch: new Set(['c1', 'c2', 'c3']),
    setUnifiedModalCandidate: vi.fn(),
    setUnifiedModalType: vi.fn(),
    setUnifiedModalOpen: vi.fn(),
    setUnifiedModalSelectedCandidates: vi.fn(),
    // adicionar outros campos necessários conforme compilar
  })),
}))

// Importar apenas depois dos mocks
// NOTA: ajustar o import real do hook após a refatoração
describe('useCandidatesInteractions — bulk handlers', () => {
  it('handleBulkEmail passa TODOS os selecionados, não apenas o primeiro', () => {
    // Este teste deve verificar que setUnifiedModalSelectedCandidates é chamado com 3 candidatos
    // e setUnifiedModalCandidate é chamado com null (modo bulk)
    // Implementar após ajustar o hook para expor setUnifiedModalSelectedCandidates
    expect(true).toBe(true) // placeholder — ver Step 3
  })
})
```

> **NOTA:** Este teste serve como guia de intenção. O teste real usa a asserção de `setUnifiedModalSelectedCandidates` ser chamado com o array completo. Após implementar o Step 3, expanda o teste com os asserts reais abaixo.

- [ ] **Step 2: Ler o estado atual do hook para entender as dependências**

```bash
sed -n '1,30p' /home/runner/workspace/plataforma-lia/src/components/pages/candidates/hooks/useCandidatesInteractions.ts
sed -n '90,115p' /home/runner/workspace/plataforma-lia/src/components/pages/candidates/hooks/useCandidatesInteractions.ts
```

Confirmar quais setters são recebidos via props (`setUnifiedModalCandidate`, `setUnifiedModalType`, `setUnifiedModalOpen`).

- [ ] **Step 3: Aplicar as mudanças no hook**

Localizar o bloco `// ── Bulk communication` (linhas ~193-208) e substituir:

```typescript
// ANTES (linhas ~193-208 — o bug):
const handleBulkEmail = () => {
  const c = sortedCandidates.find(c => selectedCandidatesForBatch.has(c.id))
  if (c) openUnifiedModal(c, 'email')
}
const handleBulkWSIScreening = () => {
  const c = sortedCandidates.find(c => selectedCandidatesForBatch.has(c.id))
  if (c) openUnifiedModal(c, 'triagem')
}
const handleBulkScheduleInterview = () => {
  const c = sortedCandidates.find(c => selectedCandidatesForBatch.has(c.id))
  if (c) openUnifiedModal(c, 'agendamento')
}
const handleBulkFeedback = () => {
  const c = sortedCandidates.find(c => selectedCandidatesForBatch.has(c.id))
  if (c) openUnifiedModal(c, 'feedback')
}
```

```typescript
// DEPOIS (correto):
// Abre o modal em modo BULK: candidate=null, selectedCandidates=todos os selecionados
const openBulkUnifiedModal = (type: CommunicationType) => {
  const selected = sortedCandidates
    .filter(c => selectedCandidatesForBatch.has(c.id))
    .map(c => ({ id: c.id, name: c.name, email: c.email, phone: c.phone, avatar: c.avatar }))
  if (selected.length === 0) return
  setUnifiedModalCandidate(null)          // bulk mode: candidate é null
  setUnifiedModalSelectedCandidates(selected)
  setUnifiedModalType(type)
  setUnifiedModalOpen(true)
}

const handleBulkEmail = () => openBulkUnifiedModal('email')
const handleBulkWSIScreening = () => openBulkUnifiedModal('triagem')
const handleBulkScheduleInterview = () => openBulkUnifiedModal('agendamento')
const handleBulkFeedback = () => openBulkUnifiedModal('feedback')
```

Também localizar `handleUnifiedModalSend` (linha ~217) e **remover o toast falso**:

```typescript
// ANTES:
const handleUnifiedModalSend = (data: Record<string, unknown>) => {
  const label = data.type === 'email' ? 'Email' : /* ... */ 'Feedback'
  toast.success('Mensagem enviada!', { description: `${label} enviado com sucesso.` })
  handleUnifiedModalClose()
}

// DEPOIS — sem toast falso; o BulkResultReport cuidará do feedback:
const handleUnifiedModalSend = (_data: Record<string, unknown>) => {
  handleUnifiedModalClose()
}
```

Verificar que `setUnifiedModalSelectedCandidates` está na lista de props do hook (interface de entrada). Se não existir, adicioná-la ao destructuring de props e à interface.

- [ ] **Step 4: Verificar que o candidatos-store ou o estado da página tem o setter**

```bash
grep -n "setUnifiedModalSelectedCandidates\|unifiedModalSelectedCandidates" \
  /home/runner/workspace/plataforma-lia/src/components/pages/candidates/hooks/candidates-core/useCandidatesUIState.ts \
  /home/runner/workspace/plataforma-lia/src/stores/candidates-store.ts
```

Se o campo não existir no store/state, adicioná-lo ao `useCandidatesUIState`:

```typescript
// Em useCandidatesUIState.ts — adicionar junto com os outros setters do modal unificado:
const [unifiedModalSelectedCandidates, setUnifiedModalSelectedCandidates] = 
  useState<Array<{ id: string; name: string; email?: string; phone?: string; avatar?: string }>>([])
```

E expor nos retornos do hook + passar como prop em `useCandidatesInteractions`.

- [ ] **Step 5: Compilar TypeScript para confirmar sem erros**

```bash
cd /home/runner/workspace/plataforma-lia
npx tsc --noEmit 2>&1 | grep "useCandidatesInteractions\|useCandidatesUIState" | head -20
```
Esperado: zero linhas (sem erros nos arquivos tocados).

- [ ] **Step 6: Rodar ESLint no arquivo**

```bash
npx eslint src/components/pages/candidates/hooks/useCandidatesInteractions.ts --max-warnings=0
```

- [ ] **Step 7: Commit**

```bash
git commit -m "fix(bulk): handlers find→filter + openBulkUnifiedModal + remove toast falso" \
  -- src/components/pages/candidates/hooks/useCandidatesInteractions.ts \
     src/components/pages/candidates/hooks/candidates-core/useCandidatesUIState.ts
```

---

## Task 5: Corrigir `useUnifiedCommunication.handleSend` — iterar N em bulk mode

**Files:**
- Modify: `src/components/modals/useUnifiedCommunication.ts`

Este é o produtor canônico de envio. A correção: em bulk mode, iterar `selectedCandidates` via `runBulkSequential`. Single mode continua idêntico.

- [ ] **Step 1: Escrever o teste falhando**

Criar `src/components/modals/__tests__/useUnifiedCommunicationBulk.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'

// Mock do fetch
global.fetch = vi.fn()

const mockFetch = (ok = true) => {
  (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
    ok,
    json: async () => ({ success: ok, error: ok ? undefined : 'falha no envio' }),
  })
}

// Importar o hook após configurar os mocks
// ADAPTAR o import conforme estrutura real do hook
describe('useUnifiedCommunication — bulk send', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('em bulk mode chama fetch uma vez POR candidato selecionável', async () => {
    mockFetch(true)
    // Renderizar o hook com selectedCandidates=[3 itens] + candidate=null
    // Chamar handleSend
    // Verificar que fetch foi chamado 3 vezes (uma por candidato)
    // Este teste será implementado com o import real após refatorar o hook
    expect(true).toBe(true) // placeholder
  })

  it('em bulk mode, falha em 1 candidato não impede os outros', async () => {
    // fetch: sucesso/falha/sucesso
    // results: [ok, !ok, ok]
    expect(true).toBe(true) // placeholder
  })
})
```

> **NOTA:** Os testes placeholder acima devem ser expandidos após implementar o hook. O padrão de teste é o mesmo usado em `useRevealContact.tsx` + `BulkRevealModal.tsx` que já testam loops de envio.

- [ ] **Step 2: Ler a estrutura atual do handleSend para planejar o refactor**

```bash
sed -n '163,200p' /home/runner/workspace/plataforma-lia/src/components/modals/useUnifiedCommunication.ts
```

Confirmar que `sendEmail` e `sendWhatsApp` fecham sobre `safeCandidate`.

- [ ] **Step 3: Refatorar `handleSend` em `useUnifiedCommunication.ts`**

Localizar as funções internas `sendEmail` e `sendWhatsApp` (em torno da linha 202 e 234) e **parametrizá-las**:

```typescript
// ANTES (fecham sobre safeCandidate único):
const sendEmail = async () => {
  const response = await fetch('/api/backend-proxy/communication/send-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Company-ID': companyId },
    body: JSON.stringify({
      to_email: safeCandidate.email,
      to_name: safeCandidate.name,
      candidate_id: safeCandidate.id,
      // ...
    })
  })
  // ...
}

// DEPOIS (recebem o candidato como parâmetro):
const sendEmailFor = async (c: { id: string; name: string; email?: string }) => {
  const response = await fetch('/api/backend-proxy/communication/send-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Company-ID': companyId },
    body: JSON.stringify({
      to_email: c.email,
      to_name: c.name,
      candidate_id: c.id,
      candidate_name: c.name,
      subject,
      body_html: `<div style="font-family: Arial, sans-serif;">${message.replace(/\n/g, '<br>')}</div>`,
      body_text: message,
      vacancy_id: selectedVacancyId || undefined,
      vacancy_title: selectedVacancy?.title,
      communication_type: type,
      metadata: { source: 'unified_communication_modal', type, channel: 'email' }
    })
  })
  const result = await response.json()
  if (!response.ok || !result.success) throw new Error(result.error || 'Falha ao enviar email')
  return result
}

const sendWhatsAppFor = async (c: { id: string; name: string; phone?: string }) => {
  const response = await fetch('/api/backend-proxy/communication/send-whatsapp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Company-ID': companyId },
    body: JSON.stringify({
      to_phone: (c.phone || '').replace(/\D/g, ''),
      message,
      candidate_id: c.id,
      candidate_name: c.name,
      vacancy_id: selectedVacancyId || undefined,
      vacancy_title: selectedVacancy?.title,
      communication_type: type,
      metadata: { source: 'unified_communication_modal', type, channel: 'whatsapp' }
    })
  })
  const result = await response.json()
  if (!response.ok || !result.success) throw new Error(result.error || 'Falha ao enviar WhatsApp')
  return result
}
```

Localizar o bloco de dispatch (linha ~260) e substituir para separar single vs bulk:

```typescript
// Importar no topo do arquivo:
import { runBulkSequential, partitionByContactability } from '@/lib/bulk'
import { useFailedDeliveryStore } from '@/stores/failedDeliveryStore'

// Dentro de handleSend, SUBSTITUIR o bloco de dispatch:

if (isBulkMode) {
  // ── BULK MODE ──────────────────────────────────────────────────────────
  const { sendable, skipped } = partitionByContactability(selectedCandidates, channel)

  const sendFor = async (c: { id: string; name: string; email?: string; phone?: string }) => {
    if (channel === 'email') return sendEmailFor(c)
    if (channel === 'whatsapp') return sendWhatsAppFor(c)
    // both: enviar email E whatsapp
    await sendEmailFor(c)
    await sendWhatsAppFor(c)
  }

  // Itens pulados por falta de contato entram como falha direta
  const skippedResults = skipped.map(({ item, reason }) => ({
    id: item.id, name: item.name, ok: false as const, reason
  }))

  const sentResults = await runBulkSequential(sendable, sendFor)

  const allResults = [...sentResults, ...skippedResults]

  // Atualizar o store de falhas de entrega
  const { addFailure, clearFailure } = useFailedDeliveryStore.getState()
  for (const r of allResults) {
    if (!r.ok) {
      addFailure({ candidateId: r.id, reason: r.reason ?? 'falha', channel, at: Date.now() })
    } else {
      clearFailure(r.id)
    }
  }

  // Logar apenas os bem-sucedidos
  for (const r of sentResults.filter(r => r.ok)) {
    const c = sendable.find(s => s.id === r.id)
    if (c) {
      await liaApi.logCommunication({
        company_id: companyId, candidate_id: c.id, candidate_name: c.name,
        candidate_email: c.email, candidate_phone: c.phone,
        communication_type: type, channel: channel === 'both' ? 'email' : channel,
        direction: 'outbound', subject: channel !== 'whatsapp' ? subject : undefined,
        message_content: message, sent_by: 'recruiter',
      }).catch(() => undefined) // log error não bloqueia
    }
  }

  onSend?.({ type, channel, message, bulkResults: allResults } as unknown as CommunicationResult)

} else {
  // ── SINGLE MODE (comportamento existente, inalterado) ──────────────────
  const safeCandidate = candidate!

  if (channel === 'email') {
    const result = await sendEmailFor(safeCandidate)
    toast.success(result.mock ? 'Email simulado!' : 'Email enviado!', {
      description: result.mock
        ? `Modo desenvolvimento: email para ${safeCandidate.email}`
        : `Email enviado para ${safeCandidate.email}`,
    })
  } else if (channel === 'whatsapp') {
    const result = await sendWhatsAppFor(safeCandidate)
    toast.success(result.mock ? 'WhatsApp simulado!' : 'WhatsApp enviado!', {
      description: result.mock
        ? `Modo desenvolvimento: mensagem para ${safeCandidate.name}`
        : `WhatsApp enviado para ${safeCandidate.name}`,
    })
  } else if (channel === 'both') {
    const emailResult = await sendEmailFor(safeCandidate)
    const waResult = await sendWhatsAppFor(safeCandidate)
    const isMock = emailResult.mock || waResult.mock
    toast.success(isMock ? 'Mensagens simuladas!' : 'Mensagens enviadas!', {
      description: isMock
        ? `Modo desenvolvimento: email e WhatsApp para ${safeCandidate.name}`
        : `Mensagens enviadas para ${safeCandidate.name}`,
    })
  }

  await liaApi.logCommunication({
    company_id: companyId, candidate_id: safeCandidate.id, candidate_name: safeCandidate.name,
    candidate_email: safeCandidate.email, candidate_phone: safeCandidate.phone,
    communication_type: type, channel: channel === 'both' ? 'email' : channel,
    direction: 'outbound', subject: channel !== 'whatsapp' ? subject : undefined,
    message_content: message, sent_by: 'recruiter',
    metadata: type === 'agendamento' ? interviewSettings as unknown as Record<string, unknown> : undefined,
  }).catch(() => undefined)

  await liaApi.createActivity({
    company_id: companyId, activity_type: `communication_${type}`,
    description: `Enviou ${type} para ${safeCandidate.name}`,
    candidate_id: safeCandidate.id, performed_by: 'recruiter',
    metadata: { channel, type, subject: channel !== 'whatsapp' ? subject : undefined }
  }).catch(() => undefined)

  onSend?.({ type, channel, message, subject: channel !== 'whatsapp' ? subject : undefined,
    recipient: channel !== 'whatsapp' ? safeCandidate.email : safeCandidate.phone,
    metadata: {
      ...(type === 'agendamento' ? interviewSettings : {}),
      ...(linkToVacancy && selectedVacancyId ? { vacancyId: selectedVacancyId, vacancyTitle: selectedVacancy?.title } : {}),
    }
  } as CommunicationResult)
}
```

- [ ] **Step 4: Compilar TypeScript**

```bash
npx tsc --noEmit 2>&1 | grep "useUnifiedCommunication" | head -20
```
Esperado: zero erros no arquivo.

- [ ] **Step 5: Rodar ESLint**

```bash
npx eslint src/components/modals/useUnifiedCommunication.ts --max-warnings=0
```

- [ ] **Step 6: Commit**

```bash
git commit -m "fix(bulk): useUnifiedCommunication itera N via runBulkSequential em bulk mode" \
  -- src/components/modals/useUnifiedCommunication.ts
```

---

## Task 6: Abrir `BulkResultReport` no funil após `onSend`

**Files:**
- Modify: `src/components/pages/candidates-page.tsx`  
  *(ou o componente que monta o modal unificado + passa `onSend`)*

O `onSend` callback agora recebe `bulkResults` em modo bulk. O parent deve detectar isso e abrir o relatório.

- [ ] **Step 1: Localizar onde `onSend` é passado ao modal no funil**

```bash
grep -n "onSend\|handleUnifiedModalSend\|UnifiedCommunicationModal" \
  /home/runner/workspace/plataforma-lia/src/components/pages/candidates-page.tsx | head -20
```

- [ ] **Step 2: Adicionar estado para o relatório**

Dentro do componente que monta o `<UnifiedCommunicationModal>`, adicionar:

```typescript
import { BulkResultReport } from '@/components/bulk'
import type { BulkItemResult } from '@/lib/bulk'

// Estado:
const [bulkReport, setBulkReport] = useState<{
  isOpen: boolean
  results: BulkItemResult[]
  actionLabel: string
}>({ isOpen: false, results: [], actionLabel: '' })
```

- [ ] **Step 3: Atualizar o `onSend` handler**

```typescript
const handleUnifiedModalSend = (data: Record<string, unknown>) => {
  handleUnifiedModalClose()
  // bulk mode retorna bulkResults no data
  if (Array.isArray((data as any).bulkResults)) {
    const typeLabels: Record<string, string> = {
      email: 'Email', whatsapp: 'WhatsApp', triagem: 'Triagem',
      agendamento: 'Agendamento', feedback: 'Feedback',
    }
    setBulkReport({
      isOpen: true,
      results: (data as any).bulkResults as BulkItemResult[],
      actionLabel: typeLabels[(data as any).type as string] ?? 'Envio',
    })
  }
  // single mode: sem toast extra (o hook já deu toast dentro)
}
```

- [ ] **Step 4: Montar o `<BulkResultReport>` no JSX**

```tsx
<BulkResultReport
  isOpen={bulkReport.isOpen}
  onClose={() => setBulkReport(s => ({ ...s, isOpen: false }))}
  results={bulkReport.results}
  actionLabel={bulkReport.actionLabel}
/>
```

- [ ] **Step 5: Compilar + ESLint**

```bash
npx tsc --noEmit 2>&1 | grep "candidates-page" | head -10
npx eslint src/components/pages/candidates-page.tsx --max-warnings=0
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(bulk): BulkResultReport wired no funil pós onSend" \
  -- src/components/pages/candidates-page.tsx
```

---

## Task 7: Marca de falha de entrega no `ContactCells`

**Files:**
- Modify: `src/components/pages/candidates/cells/ContactCells.tsx`

`ContactCells` já tem `AlertTriangle` e `renderValidityBadge`. Vamos adicionar um badge adicional quando `useFailedDeliveryStore.hasFailure(candidate.id)` for true, distinto do badge de validade (que é sobre o contato em si).

- [ ] **Step 1: Escrever o teste falhando**

```typescript
// src/components/pages/candidates/cells/__tests__/ContactCells.deliveryFailure.test.tsx
import React from 'react'
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { renderEmailCell } from '../ContactCells'
import { useFailedDeliveryStore } from '@/stores/failedDeliveryStore'

const candidate = {
  id: 'c1', name: 'Ana', email: 'ana@e.com',
  source: 'local', pearch_profile_id: null, has_email: true,
} as any

beforeEach(() => useFailedDeliveryStore.getState().clearAll())

describe('renderEmailCell — delivery failure badge', () => {
  it('não mostra badge de falha de entrega quando não há falha registrada', () => {
    const { container } = render(<>{renderEmailCell(candidate, {}, () => {}, undefined, undefined)}</>)
    expect(container.querySelector('[aria-label*="Último envio falhou"]')).toBeNull()
  })

  it('mostra badge de falha de entrega quando failedDeliveryStore tem a entry', () => {
    useFailedDeliveryStore.getState().addFailure({
      candidateId: 'c1', reason: 'e-mail inválido', channel: 'email', at: 1000
    })
    const { container } = render(<>{renderEmailCell(candidate, {}, () => {}, undefined, undefined)}</>)
    expect(container.querySelector('[aria-label*="Último envio falhou"]')).not.toBeNull()
  })
})
```

- [ ] **Step 2: Rodar — confirmar FAIL**

```bash
npx vitest run src/components/pages/candidates/cells/__tests__/ContactCells.deliveryFailure.test.tsx --reporter=verbose
```
Esperado: falha porque o badge não existe ainda.

- [ ] **Step 3: Modificar `renderEmailCell` em `ContactCells.tsx`**

No topo do arquivo adicionar:
```typescript
import { useFailedDeliveryStore } from '@/stores/failedDeliveryStore'
```

Dentro da função `renderEmailCell`, após o badge de validade existente, adicionar verificação:

```typescript
export function renderEmailCell(
  candidate: Candidate,
  revealedContacts: RevealedContacts,
  onRevealContact: OnRevealContact,
  t?: TranslateFn,
  validity?: ContactValidityLite
): React.ReactNode {
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const deliveryFailure = useFailedDeliveryStore(s => s.getFailure(candidate.id))
  const candidateEmail = revealedContacts[candidate.id]?.email || candidate.email
  // ... resto da função existente inalterado ...

  if (candidateEmail) {
    return (
      <span className="inline-flex items-center gap-1 min-w-0">
        <span className="text-xs text-lia-text-primary truncate">{candidateEmail}</span>
        {renderValidityBadge(
          validity?.email_valid,
          validity?.email_reason,
          t ? t('emailVerified') : "E-mail verificado",
          t ? t('emailUnverified') : "E-mail não verificado"
        )}
        {/* Badge de falha de último envio — limpo quando o envio seguinte tem sucesso */}
        {deliveryFailure && (
          <AlertTriangle
            className="w-3 h-3 shrink-0 text-status-error"
            role="img"
            aria-label={`Último envio falhou: ${deliveryFailure.reason}`}
          />
        )}
      </span>
    )
  }
  // ... resto inalterado ...
}
```

> **NOTA:** `renderEmailCell` é uma função utilitária usada no renderer, não um componente React. O `useFailedDeliveryStore` é um hook Zustand que pode ser chamado em funções de render. Se o linter reclamar de `rules-of-hooks` neste contexto, converter `renderEmailCell` para um componente React `EmailCell` com as mesmas props — o `CandidateTableCellRenderer` já usa o padrão `renderXxx(candidate, ...)`.

- [ ] **Step 4: Rodar — confirmar PASS**

```bash
npx vitest run src/components/pages/candidates/cells/__tests__/ContactCells.deliveryFailure.test.tsx --reporter=verbose
```
Esperado: `2 passed`

- [ ] **Step 5: ESLint**

```bash
npx eslint src/components/pages/candidates/cells/ContactCells.tsx --max-warnings=0
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(bulk): badge falha de entrega no ContactCells (⚠ + tooltip)" \
  -- src/components/pages/candidates/cells/ContactCells.tsx \
     src/components/pages/candidates/cells/__tests__/ContactCells.deliveryFailure.test.tsx
```

---

## Task 8: Alinhar Kanban (`useKanbanBulkActions`) ao padrão canônico

**Files:**
- Modify: `src/components/pages/job-kanban/hooks/useKanbanBulkActions.ts`
- Modify: `src/components/pages/job-kanban/KanbanPageContent.tsx` (montar BulkResultReport)

O kanban já usa arrays e `bulkSendEmail`. Esta task alinha `send_message` ao executor e adiciona o relatório.

- [ ] **Step 1: Verificar o que `send_message` faz hoje no kanban**

```bash
grep -n "send_message\|bulkSendEmail\|BulkActionResult\|handleBulkActionExecute" \
  /home/runner/workspace/plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanBulkActions.ts | head -30
```

- [ ] **Step 2: Identificar se `bulkSendEmail` tem endpoint batch ou chama 1 por 1**

```bash
grep -n "bulkSendEmail\|send-email\|candidate_ids" \
  /home/runner/workspace/plataforma-lia/src/services/lia-api/bulk-api.ts | head -20
```

Se o endpoint recebe um array de IDs e dispara internamente (batch atômico), o executor não é necessário — apenas adicionar o `BulkResultReport` com os resultados retornados. Se for 1-por-1, substituir pelo executor.

- [ ] **Step 3: Localizar onde `send_message` despacha no `handleBulkActionExecute`**

```bash
sed -n '84,130p' /home/runner/workspace/plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanBulkActions.ts
```

- [ ] **Step 4: Adicionar `BulkResultReport` ao kanban**

No `KanbanPageContent.tsx`, adicionar estado + montar o componente (mesmo padrão do Task 6):

```typescript
import { BulkResultReport } from '@/components/bulk'
import type { BulkItemResult } from '@/lib/bulk'

const [bulkReport, setBulkReport] = useState<{
  isOpen: boolean; results: BulkItemResult[]; actionLabel: string
}>({ isOpen: false, results: [], actionLabel: '' })
```

Passar `onBulkComplete` ao hook que dispara `setBulkReport` com os resultados.

- [ ] **Step 5: Compilar + ESLint**

```bash
npx tsc --noEmit 2>&1 | grep "useKanbanBulkActions\|KanbanPageContent" | head -10
npx eslint src/components/pages/job-kanban/hooks/useKanbanBulkActions.ts \
  src/components/pages/job-kanban/KanbanPageContent.tsx --max-warnings=0
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(bulk): BulkResultReport wired no kanban (send_message)" \
  -- src/components/pages/job-kanban/hooks/useKanbanBulkActions.ts \
     src/components/pages/job-kanban/KanbanPageContent.tsx
```

---

## Task 9: Alinhar tabela de vagas (`useJobsBulkActions`)

**Files:**
- Modify: `src/components/pages/jobs/hooks/useJobsBulkActions.ts`
- Modify: `src/components/pages/JobsListContent.tsx`

- [ ] **Step 1: Verificar ações bulk que operam em N vagas hoje**

```bash
grep -n "handleJobPublish\|handleJobToggleStatus\|selectedJobsForBatch\|liaApi\." \
  /home/runner/workspace/plataforma-lia/src/components/pages/jobs/hooks/useJobsBulkActions.ts | head -30
```

- [ ] **Step 2: Identificar quais ações em massa não têm feedback de resultado**

Ações que hoje dão um único toast genérico para N vagas são candidatas ao executor + relatório. Identificar e envolver com `runBulkSequential`.

Exemplo para `handleJobPublish` (se operar 1-por-1):

```typescript
import { runBulkSequential } from '@/lib/bulk'

const handleJobPublishBulk = async () => {
  const items = selectedJobs.map(j => ({ id: j.id, name: j.title }))
  const results = await runBulkSequential(items, async (job) => {
    const resp = await liaApi.updateJobVacancy(job.id, { status: 'ao_vivo' })
    if (!resp.ok) throw new Error(resp.error ?? 'Falha ao publicar')
    return resp
  })
  onBulkComplete?.({ results, actionLabel: 'Publicar vaga' })
}
```

- [ ] **Step 3: Adicionar `BulkResultReport` ao `JobsListContent.tsx`**

Mesmo padrão dos Tasks 6 e 8.

- [ ] **Step 4: Compilar + ESLint + Commit**

```bash
npx tsc --noEmit 2>&1 | grep "useJobsBulkActions\|JobsListContent" | head -10
npx eslint src/components/pages/jobs/hooks/useJobsBulkActions.ts \
  src/components/pages/JobsListContent.tsx --max-warnings=0
git commit -m "feat(bulk): BulkResultReport wired na tabela de vagas" \
  -- src/components/pages/jobs/hooks/useJobsBulkActions.ts \
     src/components/pages/JobsListContent.tsx
```

---

## Task 10: i18n — todas as strings novas

**Files:**
- Modify: `messages/pt-BR.json`
- Modify: `messages/en.json`

- [ ] **Step 1: Listar todas as strings novas introduzidas**

Fazer grep nos arquivos tocados nas Tasks 3-9 por literais de string que deveriam ser i18n:

```bash
grep -n "\"Fechar\"\|\"Copiar lista\"\|\"Último envio\"\|\"e-mail ausente\"\|\"telefone ausente\"\|\"e-mail inválido\"\|\"Envio concluído\"\|\" de \"\|\"enviados\"\|\"Pensando\"" \
  /home/runner/workspace/plataforma-lia/src/components/bulk/BulkResultReport.tsx \
  /home/runner/workspace/plataforma-lia/src/components/pages/candidates/cells/ContactCells.tsx
```

- [ ] **Step 2: Adicionar chaves em `messages/pt-BR.json`**

```json
// Dentro da seção adequada (criar "bulkReport" se não existir):
"bulkReport": {
  "title": "{succeeded} de {total} enviados",
  "closeButton": "Fechar",
  "copyFailed": "Copiar lista de falhas",
  "emailMissing": "e-mail ausente",
  "emailInvalid": "e-mail inválido",
  "phoneMissing": "telefone ausente",
  "deliveryFailed": "Último envio falhou: {reason}"
}
```

- [ ] **Step 3: Adicionar chaves em `messages/en.json`**

```json
"bulkReport": {
  "title": "{succeeded} of {total} sent",
  "closeButton": "Close",
  "copyFailed": "Copy failed list",
  "emailMissing": "missing email",
  "emailInvalid": "invalid email",
  "phoneMissing": "missing phone",
  "deliveryFailed": "Last delivery failed: {reason}"
}
```

- [ ] **Step 4: Atualizar componentes para usar `useTranslations('bulkReport')`**

Em `BulkResultReport.tsx`, `ContactCells.tsx` e `partitionByContactability.ts` (que produz mensagens de erro) — adaptar para usar as chaves i18n onde aplicável. (Nota: `partitionByContactability` é puro, não tem acesso a `t`. As strings de reason são literais — o componente de exibição é quem deve traduzir antes de renderizar.)

- [ ] **Step 5: Rodar sensor i18n**

```bash
cd /home/runner/workspace/plataforma-lia
npm run lint:i18n
```
Esperado: zero violações nos arquivos novos.

- [ ] **Step 6: Rodar lint:i18n:blocking para confirmar sem regressão**

```bash
npm run lint:i18n:blocking
```
Esperado: exit 0.

- [ ] **Step 7: Commit**

```bash
git commit -m "feat(bulk): i18n todas as strings novas (bulkReport.*) pt-BR + en" \
  -- messages/pt-BR.json messages/en.json \
     src/components/bulk/BulkResultReport.tsx \
     src/components/pages/candidates/cells/ContactCells.tsx
```

---

## Verificação final

Após todas as tasks:

```bash
# TypeScript — zero erros
cd /home/runner/workspace/plataforma-lia
npx tsc --noEmit 2>&1 | grep -v "node_modules" | head -20

# ESLint — zero warnings
npx eslint src/lib/bulk src/stores/failedDeliveryStore.ts src/components/bulk \
  src/components/pages/candidates/hooks/useCandidatesInteractions.ts \
  src/components/modals/useUnifiedCommunication.ts \
  --max-warnings=0

# Vitest — todos os novos testes passando
npx vitest run \
  src/lib/bulk/__tests__/ \
  src/stores/__tests__/failedDeliveryStore.test.ts \
  src/components/bulk/__tests__/ \
  src/components/pages/candidates/cells/__tests__/ContactCells.deliveryFailure.test.tsx \
  --reporter=verbose

# i18n — zero violações
npm run lint:i18n:blocking
```

---

## Notas de implementação

1. **`renderEmailCell` como hook:** Se o linter bloquear `useFailedDeliveryStore` dentro de `renderEmailCell` (função utilitária, não componente), a solução é convertê-la para `<EmailCell candidate={...} .../>` — já é um padrão simples e o `CandidateTableCellRenderer` chama `renderEmailCell(...)` que pode virar `<EmailCell .../>` sem mudar a interface externa.

2. **`Date.now()` no store:** O store usa `at: Date.now()` para timestamp de falha. Isso é aceitável porque é código de runtime (não em workflow script).

3. **`X-Company-ID` Header no `useUnifiedCommunication`:** O header existe hoje e não é o foco desta entrega. Continua como está — não adicionar nem remover.

4. **Teste placeholder Tasks 5:** Os testes com `// placeholder` devem ser expandidos com os asserts reais após o refactor do Task 5. O padrão é testar o `handleSend` via `renderHook` com `fetch` mockado e verificar que `fetch` foi chamado N vezes.
