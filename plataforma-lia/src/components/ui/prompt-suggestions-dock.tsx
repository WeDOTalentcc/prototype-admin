"use client"

import React, { useState, useEffect, useRef } from "react"
import { Brain, X, Move } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"
import { ChatWorkflowReels } from "@/components/ui/chat-workflow-reels"

interface PromptSuggestionsDockProps {
  onSelect: (command: string) => void
  isEmpty: boolean
  onClose?: () => void
}

export function PromptSuggestionsDock({ onSelect, isEmpty, onClose }: PromptSuggestionsDockProps) {
  const [isExpanded, setIsExpanded] = useState(isEmpty)

  const storePosition = useUIPreferencesStore((s) => s.promptSuggestionsPosition)
  const setStorePosition = useUIPreferencesStore((s) => s.setPromptSuggestionsPosition)
  const [position, setPositionLocal] = useState(storePosition)
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const cardRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setPositionLocal(storePosition)
  }, [storePosition])

  const setPosition = (pos: { top: number; right: number }) => {
    setPositionLocal(pos)
    setStorePosition(pos)
  }

  React.useEffect(() => {
    if (!isEmpty) {
      setIsExpanded(false)
    }
  }, [isEmpty])

  const handleMouseDown = (e: React.MouseEvent) => {
    const targetElement = cardRef.current || buttonRef.current
    if (targetElement) {
      setIsDragging(true)
      const rect = targetElement.getBoundingClientRect()
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      })
    }
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      const newTop = e.clientY - dragOffset.y
      const newLeft = e.clientX - dragOffset.x

      const newRight = window.innerWidth - newLeft - (cardRef.current?.offsetWidth || 384)

      setPosition({
        top: Math.max(0, Math.min(newTop, window.innerHeight - 100)),
        right: Math.max(0, Math.min(newRight, window.innerWidth - 100))
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDragging, dragOffset])

  if (isEmpty) {
    return (
      <div className="w-full">
        <ChatWorkflowReels onSelect={onSelect} />
      </div>
    )
  }

  return (
    <>
      {!isExpanded && (
        <Button
          ref={buttonRef}
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(true)}
          onMouseDown={handleMouseDown}
          className="fixed h-9 px-4 rounded-md transition-transform motion-reduce:transition-none hover:scale-105 z-50 select-none opacity-80 hover:opacity-100"
          style={{
            top: `${position.top}px`,
            right: `${position.right}px`,
            backgroundColor: 'var(--lia-bg-secondary)',
            border: '1px solid var(--lia-border-subtle)',
            cursor: isDragging ? 'grabbing' : 'grab'
          }}
        >
          <div className="p-1 rounded-md mr-2 bg-lia-btn-primary-bg/[0.08]">
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          </div>
          <span className="text-base-ui font-medium text-lia-text-primary">
            Sugestões
          </span>
        </Button>
      )}

      {isExpanded && (
        <Card
          ref={cardRef}
          className="fixed w-96 max-h-[520px] overflow-hidden z-50 select-none rounded-xl border border-lia-border-subtle bg-lia-bg-secondary"
          style={{
            top: `${position.top}px`,
            right: `${position.right}px`
          }}
        >
          <div
            className={`px-4 py-3 flex items-center justify-between rounded-t-xl bg-lia-bg-secondary ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
            onMouseDown={handleMouseDown}
          >
            <div className="flex items-center gap-2">
              <Move className="w-3 h-3 text-lia-text-tertiary" />
              <div className="p-1.5 rounded-md bg-lia-btn-primary-bg/[0.08]">
                <Brain className="w-4 h-4 text-wedo-cyan" />
              </div>
              <h3 className="text-base-ui font-semibold text-lia-text-primary">
                Fluxo de Recrutamento
              </h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(false)}
              className="h-7 w-7 p-0 rounded-md hover:bg-lia-interactive-active"
            >
              <X className="w-4 h-4 text-lia-text-secondary" />
            </Button>
          </div>

          <div className="p-4 overflow-y-auto max-h-content-lg">
            <ChatWorkflowReels onSelect={(command) => {
              onSelect(command)
              setIsExpanded(false)
            }} compact />
          </div>
        </Card>
      )}
    </>
  )
}
