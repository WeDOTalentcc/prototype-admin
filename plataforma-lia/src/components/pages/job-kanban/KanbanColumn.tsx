"use client"

import React from"react"
import { Badge } from"@/components/ui/badge"
import { Button } from"@/components/ui/button"
import { ScrollArea } from"@/components/ui/scroll-area"
import { Plus, MoreVertical } from"lucide-react"
import { EmptyState } from"@/components/ui/empty-state"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from"@/lib/design-tokens"
import type { KanbanStage, KanbanCandidate } from"./types"
import { KanbanCard } from"./KanbanCard"

interface KanbanColumnProps {
  stage: KanbanStage
  candidates: KanbanCandidate[]
  onCandidateClick: (candidate: KanbanCandidate) => void
  onAddCandidate?: () => void
  isDragDisabled?: boolean
}

export function KanbanColumn({
  stage,
  candidates,
  onCandidateClick,
  onAddCandidate,
  isDragDisabled = false,
}: KanbanColumnProps) {
  return (
    <div 
      className="flex flex-col w-panel-sm min-w-panel-sm bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle"
      data-testid="kanban-column"
      data-stage-id={stage.id}
    >
      <div className="flex items-center justify-between p-3 dark:border-lia-border-subtle">
        <div className="flex items-center gap-2">
          <div 
            className="w-3 h-3 rounded-full" 
            style={{backgroundColor: stage.color}}
          />
          <span className="font-medium text-lia-text-primary">{stage.name}</span>
          <Badge 
            variant="outline" 
            className="ml-1 border-lia-border-default dark:border-lia-border-default text-lia-text-secondary text-xs"
          >
            {candidates.length}
          </Badge>
        </div>
        
        <div className="flex items-center gap-1">
          {onAddCandidate && (
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-7 w-7 text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              onClick={onAddCandidate}
            >
              <Plus className="h-4 w-4" />
            </Button>
          )}
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-7 w-7 text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      <ScrollArea className="flex-1 p-2">
        <div 
          className="space-y-2 min-h-[100px]"
          data-droppable-id={stage.id}
        >
          {candidates.length === 0 ? (
            <EmptyState
              title="Arraste candidatos aqui"
              className="h-[100px] py-4"
            />
          ) : (
            candidates.map((candidate, index) => (
              <KanbanCard
                key={candidate.id}
                candidate={candidate}
                index={index}
                onClick={() => onCandidateClick(candidate)}
                isDragDisabled={isDragDisabled}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
