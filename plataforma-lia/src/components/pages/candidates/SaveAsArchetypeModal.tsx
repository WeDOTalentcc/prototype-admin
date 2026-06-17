"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { Bookmark } from "lucide-react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Input } from "@/components/ui/input"

interface Archetype {
  id: string
  name: string
  description: string
  emoji: string
  query: string
  filters: Record<string, unknown>
  createdAt: Date
  isDefault: boolean
}

interface ChatMessage {
  id: string
  type: 'lia' | 'user'
  content: string
  timestamp: Date
}

interface SaveAsArchetypeModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentQuery: string
  isCreatingArchetype: boolean
  newArchetypeData: Partial<Archetype>
  onClose: () => void
  onSave: (archetype: Archetype, message: ChatMessage) => void
}

const EMOJI_OPTIONS = ['🎯', '🚀', '⚛️', '🛠️', '📱', '☁️', '👨‍💼', '💼', '🔧', '📊', '🧠', '🔐']

export function SaveAsArchetypeModal({
  open,
  onOpenChange,
  currentQuery,
  isCreatingArchetype,
  newArchetypeData,
  onClose,
  onSave,
}: SaveAsArchetypeModalProps) {
  const t = useTranslations('candidates.modals')
  const [nameInput, setNameInput] = useState('')
  const [emojiInput, setEmojiInput] = useState('🎯')

  const queryToDisplay = isCreatingArchetype && newArchetypeData.query
    ? newArchetypeData.query
    : (currentQuery || t('noSearchPerformed'))

  const handleOpenChange = (open: boolean) => {
    onOpenChange(open)
    if (!open) {
      setNameInput('')
      setEmojiInput('🎯')
      onClose()
    }
  }

  const handleCancel = () => {
    setNameInput('')
    setEmojiInput('🎯')
    onClose()
  }

  const handleSave = () => {
    const queryToSave = isCreatingArchetype && newArchetypeData.query
      ? newArchetypeData.query
      : currentQuery

    if (!nameInput.trim() || !queryToSave) return

    const newArchetype: Archetype = {
      id: `archetype-${Date.now()}`,
      name: nameInput.trim(),
      description: queryToSave,
      emoji: emojiInput,
      query: queryToSave,
      filters: {},
      createdAt: new Date(),
      isDefault: false,
    }

    const liaMessage: ChatMessage = {
      id: `lia-archetype-saved-${Date.now()}`,
      type: 'lia',
      content: `✅ ${t('archetypeSavedMessage', { name: nameInput.trim() })}`,
      timestamp: new Date(),
    }

    setNameInput('')
    setEmojiInput('🎯')
    onSave(newArchetype, liaMessage)
  }

  return (
    <AlertDialog open={open} onOpenChange={handleOpenChange}>
      <AlertDialogContent data-testid="save-as-archetype-modal" className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2 text-sm font-semibold">
            <Bookmark className="w-5 h-5 text-lia-text-secondary" />
            {t('saveAsArchetype')}
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-4 pt-2">
              <p className="text-xs text-lia-text-primary">
                {t('saveArchetypeDescription')}
              </p>

              {/* Query atual */}
              <div className="p-3 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                <p className="text-xs font-medium text-lia-text-primary mb-1">
                  {isCreatingArchetype ? t('profileDescription') : t('currentSearchLabel')}
                </p>
                <p className="text-xs text-lia-text-primary line-clamp-3">
                  {queryToDisplay}
                </p>
              </div>

              {/* Seletor de Emoji */}
              <div>
                <label className="text-xs font-medium mb-1.5 block">{t('iconLabel')}</label>
                <div className="flex gap-2 flex-wrap">
                  {EMOJI_OPTIONS.map((emoji) => (
                    <button
                      key={emoji}
                      onClick={() => setEmojiInput(emoji)}
                      className={`w-10 h-10 rounded-md text-xl flex items-center justify-center transition-colors motion-reduce:transition-none ${
                        emojiInput === emoji
                          ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-2 border-lia-btn-primary-bg dark:border-lia-border-medium'
                          : 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated hover:bg-lia-interactive-active dark:hover:bg-lia-border-medium'
                      }`}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>

              {/* Nome do Arquétipo */}
              <div>
                <label className="text-xs font-medium mb-1.5 block">{t('archetypeName')}</label>
                <Input
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  placeholder={t('archetypeNamePlaceholder')}
                  className="text-sm"
                />
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="mt-4">
          <AlertDialogCancel onClick={handleCancel}>
            {t('cancel')}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleSave}
            disabled={!nameInput.trim()}
            className="text-white bg-lia-btn-primary-bg"
          >
            <Bookmark className="w-4 h-4 mr-1" />
            {t('saveArchetype')}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
