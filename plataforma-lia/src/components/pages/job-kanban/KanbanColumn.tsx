"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Plus, MoreVertical } from "lucide-react"
import { EmptyState } from "@/components/ui/empty-state"
import type { KanbanItem } from "./types"
import { KanbanCard } from "./KanbanCard"
import { KanbanColumnHeader } from "./KanbanColumnHeader"
import { KanbanColumnShell } from "./KanbanColumnShell"

interface KanbanColumnStage {
  id: string
  name: string
  /** Legacy: hex/rgb color for the dot. Prefer `accentClass`. */
  color?: string
  /** Tailwind class (DS token) for the column dot, e.g. `bg-status-success`. */
  accentClass?: string
}

interface KanbanColumnProps {
  stage: KanbanColumnStage
  items: KanbanItem[]
  onItemClick: (item: KanbanItem) => void
  onAdd?: () => void
  isDragDisabled?: boolean
  emptyMessage: string
  /** Task #562 — Repassado ao card para renderizar mini funil. */
  funnelLabels?: {
    screening: string
    interview: string
    final: string
    hired: string
  }
  /** Task #562 — Repassado ao card para chips de idade/owner. */
  infoLabels?: {
    ageDays: (days: number) => string
    ownerLabel?: string
  }
}

export function KanbanColumn({
  stage,
  items,
  onItemClick,
  onAdd,
  isDragDisabled = false,
  emptyMessage,
  funnelLabels,
  infoLabels,
}: KanbanColumnProps) {
  return (
    <KanbanColumnShell
      density="comfortable"
      data-testid="kanban-column"
      data-stage-id={stage.id}
      header={
        <KanbanColumnHeader
          title={stage.name}
          count={items.length}
          accentClass={stage.accentClass}
          accentColor={stage.color}
          width="md"
          actions={
            <>
              {onAdd && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                  onClick={onAdd}
                  aria-label="Adicionar"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                aria-label="Mais ações"
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </>
          }
        />
      }
    >
      <ScrollArea className="flex-1 p-2">
        <div
          className="space-y-2 min-h-[100px]"
          data-droppable-id={stage.id}
        >
          {items.length === 0 ? (
            <EmptyState
              title={emptyMessage}
              className="h-[100px] py-4"
            />
          ) : (
            items.map((item, index) => (
              <KanbanCard
                key={item.id}
                item={item}
                index={index}
                onClick={() => onItemClick(item)}
                isDragDisabled={isDragDisabled}
                funnelLabels={funnelLabels}
                infoLabels={infoLabels}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </KanbanColumnShell>
  )
}
