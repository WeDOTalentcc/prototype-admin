# ExecutionTracker no Chat — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Exibir um plano de execução interativo em tempo real no chat da LIA — quando o backend envia `execution_tracking` via WebSocket, o chat mostra um tracker visual com progress ring, lista de steps animada e transição suave para a resposta final com streaming de texto.

**Architecture:** Reutilizar a pipeline WebSocket existente (`useMessageChannel` → `LiaChatStore.patchExecutionTracking`) e adicionar:
1. Tipos fortes para `ExecutionTracking` (spec shape: `plan[]`, `progress`, `tools_executed`, `budget`).
2. Hook `useExecutionTracking(messageId, workspaceId)` que lê do store e agenda cleanup 3s após conclusão.
3. Componente visual `ExecutionTracker` (header com progress ring, barra linear, lista de steps expansível, footer budget+elapsed).
4. Hook `useMessageStreaming` — anima resposta final caractere a caractere.
5. Wrapper `BotMessage` que decide: tracker ativo → tracker; resposta pronta → streaming text.

**Tech Stack:** React 19 + Next.js 15, Zustand (store existente), Tailwind + shadcn/ui, lucide-react, tailwindcss-animate, Vitest para testes.

---

## File Structure

**Novos arquivos:**
- `plataforma-lia/src/types/execution-tracking.ts` — Types canônicos.
- `plataforma-lia/src/lib/execution-tracking/normalize.ts` — Converte `Record<string, unknown>` do store para `ExecutionTracking` tipado.
- `plataforma-lia/src/hooks/lia-chat/use-execution-tracking.ts` — Lê tracking de uma mensagem + cleanup timer 3s.
- `plataforma-lia/src/hooks/lia-chat/use-message-streaming.ts` — Animação de streaming de texto.
- `plataforma-lia/src/components/chat/execution-tracker/execution-tracker.tsx` — Componente principal.
- `plataforma-lia/src/components/chat/execution-tracker/progress-ring.tsx` — SVG progress ring.
- `plataforma-lia/src/components/chat/execution-tracker/step-item.tsx` — Item individual da lista.
- `plataforma-lia/src/components/chat/execution-tracker/status-config.ts` — Labels/colors por thinking_status.
- `plataforma-lia/src/components/chat/bot-message-with-tracker.tsx` — Wrapper de renderização condicional.

**Testes:**
- `plataforma-lia/src/lib/execution-tracking/__tests__/normalize.test.ts`
- `plataforma-lia/src/hooks/lia-chat/__tests__/use-execution-tracking.test.ts`
- `plataforma-lia/src/hooks/lia-chat/__tests__/use-message-streaming.test.ts`
- `plataforma-lia/src/components/chat/execution-tracker/__tests__/execution-tracker.test.tsx`

**Arquivos modificados:**
- `plataforma-lia/src/components/chat/ChatMessageList.tsx` — Integrar `BotMessageWithTracker` quando mensagem tem tracking ativo.
- `plataforma-lia/src/components/pages/chat-page/types.ts` — Adicionar `executionTracking` e `isThinking` em `Message`.
- `plataforma-lia/src/components/pages/chat-page/chat-core/useChatMessages.ts` — Mapear `unifiedMessages` incluindo tracking.
- `plataforma-lia/src/hooks/chat/lia-chat-connection-types.ts` — Garantir que `LiaChatMessage` carrega `executionTracking` + `isThinking` + `thinkingStatus`.
- `plataforma-lia/src/hooks/lia-chat/use-rails-chat-connection.ts` — Passar `isThinking`, `thinkingStatus`, `executionTracking` raw no `toConnectionMessage()`.
- `plataforma-lia/src/contexts/lia-float-context.tsx` — Propagar campos de thinking para `addChatMessage`.

---

## Task 1: Tipos canônicos de ExecutionTracking

**Files:**
- Create: `plataforma-lia/src/types/execution-tracking.ts`

- [ ] **Step 1: Criar arquivo de types**

```typescript
export type StepStatus = "pending" | "in_progress" | "done" | "error"

export type ThinkingStatus =
  | "planning"
  | "searching"
  | "executing"
  | "analyzing"
  | "finalizing"
  | "completed"
  | "error"
  | (string & {})

export interface PlanStep {
  step: number
  task: string
  status: StepStatus
  tool?: string | null
  duration_ms?: number | null
}

export interface ToolExecution {
  name: string
  success: boolean
  duration_ms?: number | null
  executed_at: string
}

export interface ExecutionProgress {
  done: number
  total: number
  percentage: number
}

export interface ExecutionBudget {
  used: number
  limit: number
}

export interface ExecutionTracking {
  plan: PlanStep[]
  progress: ExecutionProgress
  tools_executed: ToolExecution[]
  started_at: string
  budget: ExecutionBudget
}

export interface ThinkingState {
  messageId: number | string
  isThinking: boolean
  thinkingStatus: ThinkingStatus
  tracking: ExecutionTracking | null
}
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/types/execution-tracking.ts
git commit -m "feat(chat): adicionar types de execution tracking"
```

---

## Task 2: Normalizador do tracking raw

**Files:**
- Create: `plataforma-lia/src/lib/execution-tracking/normalize.ts`
- Test: `plataforma-lia/src/lib/execution-tracking/__tests__/normalize.test.ts`

- [ ] **Step 1: Criar teste que falha**

```typescript
import { describe, it, expect } from "vitest"
import { normalizeExecutionTracking } from "../normalize"

describe("normalizeExecutionTracking", () => {
  it("retorna null quando input é null/undefined", () => {
    expect(normalizeExecutionTracking(null)).toBeNull()
    expect(normalizeExecutionTracking(undefined)).toBeNull()
  })

  it("retorna null quando plan ausente ou vazio", () => {
    expect(normalizeExecutionTracking({})).toBeNull()
    expect(normalizeExecutionTracking({ plan: [] })).toBeNull()
  })

  it("normaliza plan completo com defaults seguros", () => {
    const raw = {
      plan: [
        { step: 1, task: "Buscar vagas", status: "done", tool: "search", duration_ms: 100 },
        { step: 2, task: "Filtrar", status: "in_progress" },
      ],
      progress: { done: 1, total: 2, percentage: 50 },
      started_at: "2026-04-20T10:00:00Z",
      budget: { used: 1, limit: 10 },
    }
    const result = normalizeExecutionTracking(raw)
    expect(result).not.toBeNull()
    expect(result!.plan).toHaveLength(2)
    expect(result!.plan[0].status).toBe("done")
    expect(result!.progress.percentage).toBe(50)
    expect(result!.budget.limit).toBe(10)
    expect(result!.tools_executed).toEqual([])
  })

  it("usa progress calculado quando ausente", () => {
    const raw = {
      plan: [
        { step: 1, task: "A", status: "done" },
        { step: 2, task: "B", status: "done" },
        { step: 3, task: "C", status: "pending" },
      ],
    }
    const result = normalizeExecutionTracking(raw)
    expect(result!.progress).toEqual({ done: 2, total: 3, percentage: 67 })
  })

  it("coerciona status desconhecido para 'pending'", () => {
    const raw = { plan: [{ step: 1, task: "X", status: "foo" }] }
    const result = normalizeExecutionTracking(raw)
    expect(result!.plan[0].status).toBe("pending")
  })
})
```

- [ ] **Step 2: Rodar teste — falha esperada**

Run: `cd plataforma-lia && npx vitest run src/lib/execution-tracking/__tests__/normalize.test.ts`
Expected: FAIL com "Cannot find module"

- [ ] **Step 3: Implementar normalizer**

```typescript
import type {
  ExecutionTracking,
  PlanStep,
  StepStatus,
  ToolExecution,
} from "@/types/execution-tracking"

const STEP_STATUSES: readonly StepStatus[] = ["pending", "in_progress", "done", "error"]

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function toNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) return value
  if (typeof value === "string" && value.trim() !== "") {
    const n = Number(value)
    return Number.isFinite(n) ? n : fallback
  }
  return fallback
}

function toStatus(value: unknown): StepStatus {
  return typeof value === "string" && (STEP_STATUSES as readonly string[]).includes(value)
    ? (value as StepStatus)
    : "pending"
}

function toOptionalString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null
}

function toOptionalNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value
  return null
}

function normalizePlan(raw: unknown): PlanStep[] {
  if (!Array.isArray(raw)) return []
  return raw.map((item, idx) => {
    if (!isRecord(item)) {
      return { step: idx + 1, task: "", status: "pending" as StepStatus }
    }
    return {
      step: toNumber(item.step, idx + 1),
      task: typeof item.task === "string" ? item.task : "",
      status: toStatus(item.status),
      tool: toOptionalString(item.tool),
      duration_ms: toOptionalNumber(item.duration_ms),
    }
  })
}

function normalizeTools(raw: unknown): ToolExecution[] {
  if (!Array.isArray(raw)) return []
  return raw
    .filter(isRecord)
    .map((item) => ({
      name: typeof item.name === "string" ? item.name : "",
      success: Boolean(item.success),
      duration_ms: toOptionalNumber(item.duration_ms),
      executed_at: typeof item.executed_at === "string" ? item.executed_at : "",
    }))
}

function computeProgress(plan: PlanStep[], raw: unknown): ExecutionTracking["progress"] {
  if (isRecord(raw)) {
    return {
      done: toNumber(raw.done),
      total: toNumber(raw.total, plan.length),
      percentage: toNumber(raw.percentage),
    }
  }
  const done = plan.filter((s) => s.status === "done").length
  const total = plan.length
  const percentage = total > 0 ? Math.round((done / total) * 100) : 0
  return { done, total, percentage }
}

function normalizeBudget(raw: unknown): ExecutionTracking["budget"] {
  if (isRecord(raw)) {
    return { used: toNumber(raw.used), limit: toNumber(raw.limit) }
  }
  return { used: 0, limit: 0 }
}

export function normalizeExecutionTracking(
  raw: Record<string, unknown> | null | undefined,
): ExecutionTracking | null {
  if (!raw) return null
  const plan = normalizePlan(raw.plan)
  if (plan.length === 0) return null
  return {
    plan,
    progress: computeProgress(plan, raw.progress),
    tools_executed: normalizeTools(raw.tools_executed),
    started_at: typeof raw.started_at === "string" ? raw.started_at : new Date().toISOString(),
    budget: normalizeBudget(raw.budget),
  }
}
```

- [ ] **Step 4: Rodar teste — passa**

Run: `cd plataforma-lia && npx vitest run src/lib/execution-tracking/__tests__/normalize.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plataforma-lia/src/lib/execution-tracking/
git commit -m "feat(chat): normalizador de execution tracking"
```

---

## Task 3: Status config (labels, cores, ícones)

**Files:**
- Create: `plataforma-lia/src/components/chat/execution-tracker/status-config.ts`

- [ ] **Step 1: Criar config**

```typescript
import { Loader2, CheckCircle2, XCircle } from "lucide-react"
import type { ThinkingStatus } from "@/types/execution-tracking"

export const STATUS_LABELS: Record<string, string> = {
  planning: "Planejando...",
  searching: "Buscando...",
  executing: "Executando...",
  analyzing: "Analisando...",
  finalizing: "Finalizando...",
  completed: "Concluído",
  error: "Erro na execução",
}

export type NormalizedStatus = "active" | "done" | "error"

export function normalizeStatus(status: ThinkingStatus, isThinking: boolean): NormalizedStatus {
  if (status === "error") return "error"
  if (!isThinking || status === "completed") return "done"
  return "active"
}

export function getStatusLabel(status: ThinkingStatus): string {
  return STATUS_LABELS[status] ?? (typeof status === "string" ? status : "Processando...")
}

export const STATUS_COLORS: Record<NormalizedStatus, { ring: string; bg: string; border: string; icon: typeof Loader2 }> = {
  active: {
    ring: "#00B8B8",
    bg: "#E6F9F9",
    border: "#CFEFEF",
    icon: Loader2,
  },
  done: {
    ring: "#16A34A",
    bg: "#DCFCE7",
    border: "#BBF7D0",
    icon: CheckCircle2,
  },
  error: {
    ring: "#DC2626",
    bg: "#FEE2E2",
    border: "#FECACA",
    icon: XCircle,
  },
}
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/components/chat/execution-tracker/status-config.ts
git commit -m "feat(chat): status config do execution tracker"
```

---

## Task 4: ProgressRing SVG

**Files:**
- Create: `plataforma-lia/src/components/chat/execution-tracker/progress-ring.tsx`

- [ ] **Step 1: Implementar componente**

```typescript
"use client"

import React, { memo } from "react"

interface ProgressRingProps {
  percentage: number
  color: string
  size?: number
  strokeWidth?: number
}

const ProgressRingComponent = memo(function ProgressRing({
  percentage,
  color,
  size = 36,
  strokeWidth = 3,
}: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.min(Math.max(percentage, 0), 100) / 100) * circumference

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden="true">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#F1F5F9"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.3s ease" }}
        />
      </svg>
      <span className="absolute text-[9px] font-bold text-lia-text-primary tabular-nums">
        {Math.round(percentage)}%
      </span>
    </div>
  )
})

ProgressRingComponent.displayName = "ProgressRing"
export const ProgressRing = ProgressRingComponent
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/components/chat/execution-tracker/progress-ring.tsx
git commit -m "feat(chat): progress ring svg do execution tracker"
```

---

## Task 5: StepItem (item individual da lista)

**Files:**
- Create: `plataforma-lia/src/components/chat/execution-tracker/step-item.tsx`

- [ ] **Step 1: Implementar StepItem**

```typescript
"use client"

import React, { memo } from "react"
import { CheckCircle2, XCircle, Loader2, Wrench } from "lucide-react"
import { cn } from "@/lib/utils"
import type { PlanStep } from "@/types/execution-tracking"

interface StepItemProps {
  step: PlanStep
  isLast: boolean
  index: number
}

function StepDot({ status }: { status: PlanStep["status"] }) {
  const base = "flex items-center justify-center w-5 h-5 rounded-full border-2 flex-shrink-0"

  if (status === "done") {
    return (
      <div className={cn(base, "border-status-success bg-status-success/10")}>
        <CheckCircle2 className="w-3 h-3 text-status-success" aria-hidden="true" />
      </div>
    )
  }
  if (status === "error") {
    return (
      <div className={cn(base, "border-status-error bg-status-error/10")}>
        <XCircle className="w-3 h-3 text-status-error" aria-hidden="true" />
      </div>
    )
  }
  if (status === "in_progress") {
    return (
      <div className={cn(base, "border-wedo-cyan bg-wedo-cyan/10")}>
        <Loader2 className="w-3 h-3 text-wedo-cyan animate-spin motion-reduce:animate-none" aria-hidden="true" />
      </div>
    )
  }
  return <div className={cn(base, "border-lia-border-default bg-lia-bg-primary")} />
}

function formatDuration(ms?: number | null): string | null {
  if (!ms || ms <= 0) return null
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const StepItemComponent = memo(function StepItem({ step, isLast, index }: StepItemProps) {
  const duration = formatDuration(step.duration_ms)
  const isDone = step.status === "done"
  const isInProgress = step.status === "in_progress"

  return (
    <div
      className="flex items-start gap-2.5 animate-in fade-in slide-in-from-left-2 duration-300"
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: "both" }}
    >
      <div className="flex flex-col items-center flex-shrink-0">
        <StepDot status={step.status} />
        {!isLast && (
          <div
            className={cn(
              "w-px flex-1 min-h-[12px] mt-1",
              isDone ? "bg-status-success/40" : "bg-lia-border-subtle",
            )}
          />
        )}
      </div>

      <div className="flex-1 min-w-0 pb-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span
            className={cn(
              "text-xs truncate",
              isInProgress && "font-semibold text-lia-text-primary",
              isDone && "text-lia-text-tertiary line-through decoration-lia-border-default",
              step.status === "pending" && "text-lia-text-secondary",
              step.status === "error" && "text-status-error font-medium",
            )}
          >
            {step.task}
          </span>
          {isInProgress && (
            <span
              className="w-1.5 h-1.5 rounded-full bg-wedo-cyan flex-shrink-0 animate-pulse motion-reduce:animate-none"
              aria-hidden="true"
            />
          )}
        </div>

        {(step.tool || duration) && (
          <div className="flex items-center gap-2 mt-0.5">
            {step.tool && (
              <span className="inline-flex items-center gap-1 text-[10px] text-lia-text-tertiary font-mono">
                <Wrench className="w-2.5 h-2.5" aria-hidden="true" />
                {step.tool}
              </span>
            )}
            {duration && (
              <span className="text-[10px] text-lia-text-tertiary tabular-nums">{duration}</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
})

StepItemComponent.displayName = "StepItem"
export const StepItem = StepItemComponent
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/components/chat/execution-tracker/step-item.tsx
git commit -m "feat(chat): step item do execution tracker"
```

---

## Task 6: ExecutionTracker (componente principal)

**Files:**
- Create: `plataforma-lia/src/components/chat/execution-tracker/execution-tracker.tsx`
- Test: `plataforma-lia/src/components/chat/execution-tracker/__tests__/execution-tracker.test.tsx`

- [ ] **Step 1: Criar teste**

```typescript
import { describe, it, expect } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { ExecutionTracker } from "../execution-tracker"
import type { ExecutionTracking } from "@/types/execution-tracking"

const sample: ExecutionTracking = {
  plan: [
    { step: 1, task: "Buscar vagas", status: "done", duration_ms: 1200 },
    { step: 2, task: "Filtrar", status: "in_progress" },
    { step: 3, task: "Analisar", status: "pending" },
  ],
  progress: { done: 1, total: 3, percentage: 33 },
  tools_executed: [],
  started_at: new Date().toISOString(),
  budget: { used: 1, limit: 10 },
}

describe("ExecutionTracker", () => {
  it("renderiza progresso e tasks", () => {
    render(<ExecutionTracker tracking={sample} isThinking thinkingStatus="searching" />)
    expect(screen.getByText("Buscando...")).toBeInTheDocument()
    expect(screen.getByText("1/3 etapas")).toBeInTheDocument()
    expect(screen.getByText("Buscar vagas")).toBeInTheDocument()
    expect(screen.getByText("Filtrar")).toBeInTheDocument()
  })

  it("colapsa e expande a lista de steps", () => {
    render(<ExecutionTracker tracking={sample} isThinking thinkingStatus="searching" />)
    const toggle = screen.getByRole("button", { name: /recolher|expandir/i })
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute("aria-expanded", "false")
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute("aria-expanded", "true")
  })

  it("mostra label de concluído quando não está mais pensando", () => {
    render(<ExecutionTracker tracking={{ ...sample, progress: { done: 3, total: 3, percentage: 100 } }} isThinking={false} thinkingStatus="completed" />)
    expect(screen.getByText("Concluído")).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Rodar teste — falha**

Run: `cd plataforma-lia && npx vitest run src/components/chat/execution-tracker/__tests__/execution-tracker.test.tsx`
Expected: FAIL com "Cannot find module"

- [ ] **Step 3: Implementar componente**

```typescript
"use client"

import React, { memo, useEffect, useMemo, useState } from "react"
import { ChevronDown, Wrench, Clock } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ExecutionTracking, ThinkingStatus } from "@/types/execution-tracking"
import { ProgressRing } from "./progress-ring"
import { StepItem } from "./step-item"
import {
  getStatusLabel,
  normalizeStatus,
  STATUS_COLORS,
} from "./status-config"

interface ExecutionTrackerProps {
  tracking: ExecutionTracking
  isThinking: boolean
  thinkingStatus?: ThinkingStatus
  defaultExpanded?: boolean
  className?: string
}

function useElapsedTime(startedAt: string, isActive: boolean): string {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (!isActive) return
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [isActive])

  return useMemo(() => {
    const start = new Date(startedAt).getTime()
    if (!Number.isFinite(start)) return "0s"
    const diff = Math.floor((now - start) / 1000)
    if (diff < 0) return "0s"
    if (diff < 60) return `${diff}s`
    return `${Math.floor(diff / 60)}m ${diff % 60}s`
  }, [startedAt, now])
}

const ExecutionTrackerComponent = memo(function ExecutionTracker({
  tracking,
  isThinking,
  thinkingStatus = "planning",
  defaultExpanded = true,
  className,
}: ExecutionTrackerProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const normalized = normalizeStatus(thinkingStatus, isThinking)
  const colors = STATUS_COLORS[normalized]
  const label = getStatusLabel(thinkingStatus)
  const elapsed = useElapsedTime(tracking.started_at, isThinking)
  const isPlanningBar = isThinking && thinkingStatus === "planning"
  const StatusIcon = colors.icon

  return (
    <div
      className={cn(
        "w-full rounded-xl border overflow-hidden animate-in fade-in slide-in-from-bottom-1 duration-300",
        normalized === "active" && "border-wedo-cyan/30 bg-lia-bg-secondary shadow-lia-sm",
        normalized === "done" && "border-status-success/30 bg-lia-bg-secondary",
        normalized === "error" && "border-status-error/40 bg-lia-bg-secondary",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
        aria-label={expanded ? "Recolher etapas" : "Expandir etapas"}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-lia-bg-primary/40 transition-colors motion-reduce:transition-none"
      >
        <div
          className="flex items-center justify-center w-7 h-7 rounded-lg flex-shrink-0"
          style={{ backgroundColor: colors.bg }}
        >
          <StatusIcon
            className={cn(
              "w-3.5 h-3.5",
              normalized === "active" && "animate-spin motion-reduce:animate-none",
            )}
            style={{ color: colors.ring }}
            aria-hidden="true"
          />
        </div>

        <div className="flex-1 min-w-0 text-left">
          <div className="text-xs font-semibold text-lia-text-primary truncate">{label}</div>
          <div className="text-[10px] text-lia-text-tertiary">
            {tracking.progress.done}/{tracking.progress.total} etapas
          </div>
        </div>

        <ProgressRing percentage={tracking.progress.percentage} color={colors.ring} />

        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-tertiary transition-transform motion-reduce:transition-none",
            expanded && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      <div className="relative h-[3px] bg-lia-bg-primary/60 overflow-hidden">
        {isPlanningBar ? (
          <div
            className="absolute inset-y-0 w-1/3 rounded-full"
            style={{
              backgroundColor: colors.ring,
              animation: "planningShimmer 1.5s ease-in-out infinite",
            }}
          />
        ) : (
          <div
            className="h-full rounded-full"
            style={{
              width: `${tracking.progress.percentage}%`,
              backgroundColor: colors.ring,
              transition: "width 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          />
        )}
      </div>

      <div
        className={cn(
          "overflow-hidden transition-[max-height,opacity] duration-300 motion-reduce:transition-none",
          expanded ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0",
        )}
      >
        <div className="px-3 py-3 space-y-0">
          {tracking.plan.map((step, idx) => (
            <StepItem
              key={`${step.step}-${step.task}`}
              step={step}
              index={idx}
              isLast={idx === tracking.plan.length - 1}
            />
          ))}
        </div>

        <div className="px-3 py-2 border-t border-lia-border-subtle bg-lia-bg-primary/30 flex items-center justify-between text-[10px] text-lia-text-tertiary">
          <span className="inline-flex items-center gap-1">
            <Wrench className="w-3 h-3" aria-hidden="true" />
            {tracking.budget.used}/{tracking.budget.limit || "∞"}
          </span>
          <span className="inline-flex items-center gap-1 tabular-nums">
            <Clock className="w-3 h-3" aria-hidden="true" />
            {elapsed}
          </span>
        </div>
      </div>

      <style jsx>{`
        @keyframes planningShimmer {
          0% { left: -33%; }
          100% { left: 100%; }
        }
      `}</style>
    </div>
  )
})

ExecutionTrackerComponent.displayName = "ExecutionTracker"
export const ExecutionTracker = ExecutionTrackerComponent
```

- [ ] **Step 4: Rodar teste — passa**

Run: `cd plataforma-lia && npx vitest run src/components/chat/execution-tracker/__tests__/execution-tracker.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plataforma-lia/src/components/chat/execution-tracker/
git commit -m "feat(chat): componente ExecutionTracker com progress ring e steps"
```

---

## Task 7: Hook useExecutionTracking (com cleanup 3s)

**Files:**
- Create: `plataforma-lia/src/hooks/lia-chat/use-execution-tracking.ts`
- Test: `plataforma-lia/src/hooks/lia-chat/__tests__/use-execution-tracking.test.ts`

- [ ] **Step 1: Criar teste**

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useExecutionTracking } from "../use-execution-tracking"
import { useLiaChatStore } from "@/stores/lia-chat-store"
import type { LiaStoredMessage } from "@/stores/lia-chat-store"

const WORKSPACE = 1
const MESSAGE_ID = 42

function seedMessage(partial: Partial<LiaStoredMessage>) {
  const base: LiaStoredMessage = {
    id: MESSAGE_ID,
    workspaceId: WORKSPACE,
    entity: 0,
    content: "",
    contentFormat: "plain_text",
    isThinking: false,
    thinkingStatus: null,
    executionTracking: null,
    metadata: null,
    createdAt: new Date().toISOString(),
    ...partial,
  }
  useLiaChatStore.getState().setWorkspaceMessages(WORKSPACE, [base])
}

describe("useExecutionTracking", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    useLiaChatStore.getState().resetStore()
  })

  afterEach(() => {
    vi.useRealTimers()
    useLiaChatStore.getState().resetStore()
  })

  it("retorna null quando não há tracking", () => {
    seedMessage({})
    const { result } = renderHook(() => useExecutionTracking(MESSAGE_ID, WORKSPACE))
    expect(result.current.tracking).toBeNull()
    expect(result.current.isVisible).toBe(false)
  })

  it("expõe tracking normalizado quando is_thinking e plan presente", () => {
    seedMessage({
      isThinking: true,
      thinkingStatus: "searching",
      executionTracking: {
        plan: [{ step: 1, task: "A", status: "in_progress" }],
        progress: { done: 0, total: 1, percentage: 0 },
      },
    })
    const { result } = renderHook(() => useExecutionTracking(MESSAGE_ID, WORKSPACE))
    expect(result.current.isVisible).toBe(true)
    expect(result.current.tracking!.plan).toHaveLength(1)
    expect(result.current.thinkingStatus).toBe("searching")
  })

  it("mantém visibilidade por 3s após is_thinking virar false", () => {
    seedMessage({
      isThinking: true,
      thinkingStatus: "analyzing",
      executionTracking: {
        plan: [{ step: 1, task: "A", status: "in_progress" }],
      },
    })
    const { result, rerender } = renderHook(() => useExecutionTracking(MESSAGE_ID, WORKSPACE))
    expect(result.current.isVisible).toBe(true)

    act(() => {
      useLiaChatStore.getState().patchExecutionTracking(MESSAGE_ID, {
        workspaceId: WORKSPACE,
        isThinking: false,
        thinkingStatus: "completed",
        executionTracking: {
          plan: [{ step: 1, task: "A", status: "done" }],
          progress: { done: 1, total: 1, percentage: 100 },
        },
      })
    })
    rerender()
    expect(result.current.isVisible).toBe(true)

    act(() => {
      vi.advanceTimersByTime(3100)
    })
    rerender()
    expect(result.current.isVisible).toBe(false)
  })
})
```

- [ ] **Step 2: Rodar teste — falha**

Run: `cd plataforma-lia && npx vitest run src/hooks/lia-chat/__tests__/use-execution-tracking.test.ts`
Expected: FAIL

- [ ] **Step 3: Implementar hook**

```typescript
"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { useLiaChatStore } from "@/stores/lia-chat-store"
import { normalizeExecutionTracking } from "@/lib/execution-tracking/normalize"
import type { ExecutionTracking, ThinkingStatus } from "@/types/execution-tracking"

const CLEANUP_DELAY_MS = 3000

interface UseExecutionTrackingResult {
  tracking: ExecutionTracking | null
  isThinking: boolean
  thinkingStatus: ThinkingStatus
  isVisible: boolean
}

export function useExecutionTracking(
  messageId: number | string | null,
  workspaceId: number | null,
): UseExecutionTrackingResult {
  const stored = useLiaChatStore((state) => {
    if (messageId == null || workspaceId == null) return null
    const list = state.messagesByWorkspace[workspaceId]
    if (!list) return null
    return list.find((m) => m.id === messageId) ?? null
  })

  const tracking = useMemo(
    () => normalizeExecutionTracking(stored?.executionTracking ?? null),
    [stored?.executionTracking],
  )

  const isThinking = Boolean(stored?.isThinking)
  const thinkingStatus = (stored?.thinkingStatus ?? "planning") as ThinkingStatus

  const [gracePeriod, setGracePeriod] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wasThinkingRef = useRef(false)

  useEffect(() => {
    if (isThinking) {
      wasThinkingRef.current = true
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
      setGracePeriod(false)
      return
    }
    if (!wasThinkingRef.current || !tracking) return
    setGracePeriod(true)
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      setGracePeriod(false)
      wasThinkingRef.current = false
      timerRef.current = null
    }, CLEANUP_DELAY_MS)
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }
  }, [isThinking, tracking])

  const isVisible = Boolean(tracking) && (isThinking || gracePeriod)

  return { tracking, isThinking, thinkingStatus, isVisible }
}
```

- [ ] **Step 4: Rodar teste — passa**

Run: `cd plataforma-lia && npx vitest run src/hooks/lia-chat/__tests__/use-execution-tracking.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plataforma-lia/src/hooks/lia-chat/use-execution-tracking.ts plataforma-lia/src/hooks/lia-chat/__tests__/use-execution-tracking.test.ts
git commit -m "feat(chat): hook useExecutionTracking com cleanup 3s"
```

---

## Task 8: useMessageStreaming (animação caractere a caractere)

**Files:**
- Create: `plataforma-lia/src/hooks/lia-chat/use-message-streaming.ts`
- Test: `plataforma-lia/src/hooks/lia-chat/__tests__/use-message-streaming.test.ts`

- [ ] **Step 1: Criar teste**

```typescript
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useMessageStreaming } from "../use-message-streaming"

describe("useMessageStreaming", () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it("revela caracteres progressivamente", () => {
    const { result } = renderHook(() =>
      useMessageStreaming({ content: "abc", enabled: true, charIntervalMs: 10 }),
    )
    expect(result.current.visibleContent).toBe("")
    act(() => vi.advanceTimersByTime(10))
    expect(result.current.visibleContent).toBe("a")
    act(() => vi.advanceTimersByTime(20))
    expect(result.current.visibleContent).toBe("abc")
    expect(result.current.isComplete).toBe(true)
  })

  it("skipToEnd revela tudo de uma vez", () => {
    const { result } = renderHook(() =>
      useMessageStreaming({ content: "hello world", enabled: true, charIntervalMs: 10 }),
    )
    act(() => result.current.skipToEnd())
    expect(result.current.visibleContent).toBe("hello world")
    expect(result.current.isComplete).toBe(true)
  })

  it("não anima quando enabled é false", () => {
    const { result } = renderHook(() =>
      useMessageStreaming({ content: "abc", enabled: false }),
    )
    expect(result.current.visibleContent).toBe("abc")
    expect(result.current.isComplete).toBe(true)
  })
})
```

- [ ] **Step 2: Rodar teste — falha**

Run: `cd plataforma-lia && npx vitest run src/hooks/lia-chat/__tests__/use-message-streaming.test.ts`
Expected: FAIL

- [ ] **Step 3: Implementar hook**

```typescript
"use client"

import { useCallback, useEffect, useRef, useState } from "react"

interface UseMessageStreamingOptions {
  content: string
  enabled: boolean
  charIntervalMs?: number
}

interface UseMessageStreamingResult {
  visibleContent: string
  isComplete: boolean
  skipToEnd: () => void
}

export function useMessageStreaming({
  content,
  enabled,
  charIntervalMs = 20,
}: UseMessageStreamingOptions): UseMessageStreamingResult {
  const [cursor, setCursor] = useState(0)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const contentRef = useRef(content)
  contentRef.current = content

  const clear = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  useEffect(() => {
    setCursor(0)
    clear()
    if (!enabled || content.length === 0) {
      setCursor(content.length)
      return
    }
    intervalRef.current = setInterval(() => {
      setCursor((prev) => {
        const next = prev + 1
        if (next >= contentRef.current.length) {
          clear()
          return contentRef.current.length
        }
        return next
      })
    }, charIntervalMs)
    return clear
  }, [content, enabled, charIntervalMs, clear])

  const skipToEnd = useCallback(() => {
    clear()
    setCursor(contentRef.current.length)
  }, [clear])

  const visibleContent = enabled ? content.slice(0, cursor) : content
  const isComplete = !enabled || cursor >= content.length

  return { visibleContent, isComplete, skipToEnd }
}
```

- [ ] **Step 4: Rodar teste — passa**

Run: `cd plataforma-lia && npx vitest run src/hooks/lia-chat/__tests__/use-message-streaming.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plataforma-lia/src/hooks/lia-chat/use-message-streaming.ts plataforma-lia/src/hooks/lia-chat/__tests__/use-message-streaming.test.ts
git commit -m "feat(chat): hook useMessageStreaming para animação de texto"
```

---

## Task 9: Expor campos de tracking em LiaChatMessage e Message

**Files:**
- Modify: `plataforma-lia/src/hooks/chat/lia-chat-connection-types.ts`
- Modify: `plataforma-lia/src/hooks/lia-chat/use-rails-chat-connection.ts`
- Modify: `plataforma-lia/src/components/pages/chat-page/chat-core/chat-core.types.ts` (se existir) ou `types.ts`

- [ ] **Step 1: Adicionar campos em LiaChatMessage**

Em `plataforma-lia/src/hooks/chat/lia-chat-connection-types.ts`, localizar `interface LiaChatMessage` e adicionar:

```typescript
  workspaceId?: number | null
  messageNumericId?: number | null
  isThinking?: boolean
  thinkingStatus?: string | null
  executionTracking?: Record<string, unknown> | null
```

- [ ] **Step 2: Propagar no toConnectionMessage**

Em `plataforma-lia/src/hooks/lia-chat/use-rails-chat-connection.ts`, na função `toConnectionMessage`, adicionar antes do `return`:

```typescript
  base.workspaceId = stored.workspaceId
  base.messageNumericId = typeof stored.id === "number" ? stored.id : null
  base.isThinking = stored.isThinking
  base.thinkingStatus = stored.thinkingStatus
  base.executionTracking = stored.executionTracking
```

- [ ] **Step 3: Verificar tipos compilam**

Run: `cd plataforma-lia && npx tsc --noEmit`
Expected: Sem erros.

- [ ] **Step 4: Commit**

```bash
git add plataforma-lia/src/hooks/chat/lia-chat-connection-types.ts plataforma-lia/src/hooks/lia-chat/use-rails-chat-connection.ts
git commit -m "feat(chat): propagar is_thinking e execution_tracking em LiaChatMessage"
```

---

## Task 10: Propagar tracking em useChatMessages e lia-float-context

**Files:**
- Modify: `plataforma-lia/src/components/pages/chat-page/types.ts`
- Modify: `plataforma-lia/src/components/pages/chat-page/chat-core/useChatMessages.ts`

- [ ] **Step 1: Adicionar campos em Message**

Em `plataforma-lia/src/components/pages/chat-page/types.ts`, na `interface Message`, adicionar:

```typescript
  workspaceId?: number | null
  messageNumericId?: number | null
  isThinking?: boolean
  thinkingStatus?: string | null
  executionTracking?: Record<string, unknown> | null
```

- [ ] **Step 2: Mapear no useChatMessages**

Em `plataforma-lia/src/components/pages/chat-page/chat-core/useChatMessages.ts`, linhas ~29-39 e ~93-100, atualizar os dois pontos de mapeamento `unifiedMessages.map(...)`:

```typescript
unifiedMessages.map((m, idx) => ({
  id: idx + 1,
  sender: m.sender,
  content: m.content,
  timestamp: m.timestamp,
  metadata: m.metadata,
  workspaceId: m.workspaceId ?? null,
  messageNumericId: m.messageNumericId ?? null,
  isThinking: m.isThinking ?? false,
  thinkingStatus: m.thinkingStatus ?? null,
  executionTracking: m.executionTracking ?? null,
}))
```

- [ ] **Step 3: Verificar build**

Run: `cd plataforma-lia && npx tsc --noEmit`
Expected: Sem erros.

- [ ] **Step 4: Commit**

```bash
git add plataforma-lia/src/components/pages/chat-page/types.ts plataforma-lia/src/components/pages/chat-page/chat-core/useChatMessages.ts
git commit -m "feat(chat): propagar tracking em Message do chat page"
```

---

## Task 11: BotMessageWithTracker (wrapper)

**Files:**
- Create: `plataforma-lia/src/components/chat/bot-message-with-tracker.tsx`

- [ ] **Step 1: Implementar wrapper**

```typescript
"use client"

import React, { memo } from "react"
import { cn } from "@/lib/utils"
import { ExecutionTracker } from "@/components/chat/execution-tracker/execution-tracker"
import { useExecutionTracking } from "@/hooks/lia-chat/use-execution-tracking"
import { useMessageStreaming } from "@/hooks/lia-chat/use-message-streaming"
import { renderMarkdown } from "@/lib/render-markdown"

interface BotMessageWithTrackerProps {
  messageId: number | string | null
  workspaceId: number | null
  content: string
  highlightedHtml?: string
  className?: string
}

const BotMessageWithTrackerComponent = memo(function BotMessageWithTracker({
  messageId,
  workspaceId,
  content,
  highlightedHtml,
  className,
}: BotMessageWithTrackerProps) {
  const { tracking, isThinking, thinkingStatus, isVisible } = useExecutionTracking(
    typeof messageId === "number" ? messageId : null,
    workspaceId,
  )

  const shouldStream = !isVisible && !isThinking && content.length > 0
  const { visibleContent, isComplete, skipToEnd } = useMessageStreaming({
    content,
    enabled: shouldStream,
    charIntervalMs: 20,
  })

  if (isVisible && tracking) {
    return (
      <div className={cn("space-y-2", className)}>
        <ExecutionTracker tracking={tracking} isThinking={isThinking} thinkingStatus={thinkingStatus} />
      </div>
    )
  }

  if (!content) return null

  const html = highlightedHtml ?? renderMarkdown(visibleContent)
  const renderable = shouldStream ? renderMarkdown(visibleContent) : html

  return (
    <div
      onClick={!isComplete ? skipToEnd : undefined}
      role={!isComplete ? "button" : undefined}
      tabIndex={!isComplete ? 0 : undefined}
      onKeyDown={(e) => {
        if (!isComplete && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault()
          skipToEnd()
        }
      }}
      className={cn(
        "text-xs leading-relaxed text-lia-text-primary lia-markdown-content",
        !isComplete && "cursor-pointer",
        className,
      )}
      dangerouslySetInnerHTML={{ __html: renderable }}
    />
  )
})

BotMessageWithTrackerComponent.displayName = "BotMessageWithTracker"
export const BotMessageWithTracker = BotMessageWithTrackerComponent
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/components/chat/bot-message-with-tracker.tsx
git commit -m "feat(chat): wrapper BotMessageWithTracker que alterna tracker e streaming"
```

---

## Task 12: Integrar BotMessageWithTracker em ChatMessageList

**Files:**
- Modify: `plataforma-lia/src/components/chat/ChatMessageList.tsx`

- [ ] **Step 1: Substituir bloco de renderização de conteúdo**

Localizar em `ChatMessageList.tsx` o bloco da linha ~89-102 (o bloco de renderização markdown com `dangerouslySetInnerHTML`). Substituir por renderização condicional:

```typescript
import { BotMessageWithTracker } from "@/components/chat/bot-message-with-tracker"

// ... dentro do map, substituir o bloco atual:

{message.type !== "thinking" &&
  message.type !== "progress" &&
  message.type !== "command" &&
  message.type !== "file-creation" && (
    isLia && (message.isThinking || message.executionTracking) ? (
      <BotMessageWithTracker
        messageId={message.messageNumericId ?? null}
        workspaceId={message.workspaceId ?? null}
        content={message.content}
        highlightedHtml={onHighlightSearchTerm(renderMarkdown(message.content), searchTerm)}
      />
    ) : (
      <div
        className="text-xs leading-relaxed text-lia-text-primary lia-markdown-content"
        dangerouslySetInnerHTML={{
          __html: onHighlightSearchTerm(renderMarkdown(message.content), searchTerm),
        }}
      />
    )
  )}
```

- [ ] **Step 2: Verificar build**

Run: `cd plataforma-lia && npx tsc --noEmit`
Expected: Sem erros.

- [ ] **Step 3: Rodar testes de chat**

Run: `cd plataforma-lia && npx vitest run src/components/chat`
Expected: Todos passam.

- [ ] **Step 4: Commit**

```bash
git add plataforma-lia/src/components/chat/ChatMessageList.tsx
git commit -m "feat(chat): integrar ExecutionTracker no ChatMessageList"
```

---

## Task 13: Loading indicator trocado quando há tracker ativo

**Files:**
- Modify: `plataforma-lia/src/components/chat/ChatMessageList.tsx`

**Context:** O chat atual mostra `<TypingIndicator />` quando `isLoading`. Queremos que o indicator suma quando a primeira atualização de tracking chegar.

- [ ] **Step 1: Ajustar condição de isLoading**

Em `ChatMessageList.tsx`, localizar o bloco `{isLoading && (...)}` no fim. Envolver a checagem pra não exibir quando a última mensagem LIA já tiver tracking:

```typescript
const lastLia = [...messages].reverse().find((m) => m.sender === "lia")
const hideLoader = lastLia && (lastLia.isThinking || lastLia.executionTracking)

{isLoading && !hideLoader && (
  <ChatBubbleBase sender="lia">
    <div className="flex items-center space-x-2" role="status" aria-live="polite" aria-label="Carregando...">
      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
      <span className="text-xs text-lia-text-secondary">Analisando...</span>
    </div>
  </ChatBubbleBase>
)}
```

- [ ] **Step 2: Commit**

```bash
git add plataforma-lia/src/components/chat/ChatMessageList.tsx
git commit -m "fix(chat): esconder loader quando ExecutionTracker está ativo"
```

---

## Task 14: Verificação final — build + testes + lint

- [ ] **Step 1: TypeScript**

Run: `cd plataforma-lia && npx tsc --noEmit`
Expected: Sem erros.

- [ ] **Step 2: Lint**

Run: `cd plataforma-lia && npx next lint --dir src/components/chat --dir src/hooks/lia-chat --dir src/lib/execution-tracking`
Expected: Sem erros críticos.

- [ ] **Step 3: Testes unitários novos**

Run: `cd plataforma-lia && npx vitest run src/lib/execution-tracking src/hooks/lia-chat/__tests__/use-execution-tracking.test.ts src/hooks/lia-chat/__tests__/use-message-streaming.test.ts src/components/chat/execution-tracker`
Expected: Todos PASS.

- [ ] **Step 4: Build**

Run: `cd plataforma-lia && npx next build`
Expected: Build completo sem erros.

- [ ] **Step 5: Commit final (se houver ajustes)**

```bash
git add -A
git commit -m "chore(chat): ajustes finais do ExecutionTracker"
```

---

## Resumo de Integração

**Fluxo completo após implementação:**

1. Usuário envia mensagem → `useSendLiaMessage` → `POST /users/messages`.
2. Backend envia `message_created` com `is_thinking: true` + `execution_tracking.plan[]` via WS.
3. `useMessageChannel` chama `upsertMessageFromServer` → `LiaStoredMessage` no store tem `isThinking=true, executionTracking=<raw>`.
4. `useRailsChatConnection.toConnectionMessage` propaga `isThinking/thinkingStatus/executionTracking/workspaceId/messageNumericId` em `LiaChatMessage`.
5. `lia-float-context.addChatMessage` adiciona à lista compartilhada `chatMessages`.
6. `useChatMessages` mapeia para `Message[]` mantendo esses campos.
7. `ChatMessageList` renderiza `BotMessageWithTracker` para mensagens LIA com tracking.
8. `BotMessageWithTracker` chama `useExecutionTracking(messageNumericId, workspaceId)` — lê do store direto (fonte da verdade live).
9. Enquanto `isVisible` → mostra `ExecutionTracker` com progress ring, lista expansível, barra linear, footer com budget + elapsed.
10. `execution_tracking_updated` chega via WS → `patchExecutionTracking` atualiza store → hook re-renderiza tracker.
11. `message_updated` com `is_thinking=false` + `content` chega → hook detecta transição → 3s de grace period mostrando "Concluído" → tracker desaparece.
12. `useMessageStreaming` inicia animação do texto caractere a caractere (pode ser pulada com clique/Enter).
