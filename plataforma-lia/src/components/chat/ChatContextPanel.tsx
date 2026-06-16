"use client"

import React from "react"
import { X } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ContextPanelData } from "@/types/chat"
import { ChatContextPanelPart1 } from "./ChatContextPanelPart1"
import { ChatContextPanelPart2 } from "./ChatContextPanelPart2"
import { ChatContextPanelPart3 } from "./ChatContextPanelPart3"

// ──────────────────────────────────────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────────────────────────────────────

interface Props {
  contextData: ContextPanelData | null
  isPanelOpen: boolean
  onClose: () => void
  onPipelineAction: (candidateId: string, actionId: string, candidateName: string) => Promise<void>
}

// ──────────────────────────────────────────────────────────────────────────────
// Component
// ──────────────────────────────────────────────────────────────────────────────

export function ChatContextPanel({ contextData, isPanelOpen, onClose, onPipelineAction }: Props) {
  if (!contextData || !isPanelOpen) return null

  return (
    <div className="w-2/5 p-4 flex transition-colors motion-reduce:transition-none duration-300 overflow-hidden bg-lia-bg-primary">
      <Card className="w-full border-0 rounded-xl overflow-hidden flex flex-col bg-lia-bg-primary bg-lia-bg-primary">
        <CardHeader className="p-6 border-0 bg-lia-bg-primary bg-lia-bg-primary">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-lia-text-primary">{contextData.title}</h3>
              <p className="text-sm text-lia-text-secondary">Potencializado por IA</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => onClose()} className="rounded-full">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent
          className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-6 space-y-6 scrollbar-thin scrollbar-thumb-lia-border-default  scrollbar-track-transparent hover:scrollbar-thumb-lia-border-medium dark:hover:scrollbar-thumb-lia-border-medium"
         
        >
          <ChatContextPanelPart1 contextData={contextData} />
          <ChatContextPanelPart2 contextData={contextData} />
          <ChatContextPanelPart3 contextData={contextData} onPipelineAction={onPipelineAction} onClose={onClose} />
        </CardContent>
      </Card>
    </div>
  )
}
