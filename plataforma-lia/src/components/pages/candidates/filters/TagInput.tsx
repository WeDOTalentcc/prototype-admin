"use client"

import React from"react"
import { X } from"lucide-react"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"

export interface TagInputProps {
  placeholder: string
  tags: string[]
  onAdd: (value: string) => void
  onRemove: (value: string) => void
}

export function TagInput({ placeholder, tags, onAdd, onRemove }: TagInputProps) {
  return (
    <div data-testid="tag-input-container" className="space-y-2">
      <Input
        data-testid="tag-input-field"
        placeholder={placeholder}
        className="h-8 text-xs"
        onKeyDown={(e) => {
          const value = (e.target as HTMLInputElement).value.trim()
          if (e.key ==="Enter" && value && !tags.includes(value)) {
            onAdd(value)
            ;(e.target as HTMLInputElement).value =""
          }
        }}
      />
      {tags.length > 0 && (
        <div data-testid="tag-list" className="flex flex-wrap gap-1">
          {tags.map((tag) => (
            <Chip key={tag} variant="neutral" muted className="text-micro px-2 py-0.5 flex items-center gap-1">
              {tag}
              <button data-testid={`remove-tag-${tag}`} onClick={() => onRemove(tag)}>
                <X className="w-2.5 h-2.5" />
              </button>
            </Chip>
          ))}
        </div>
      )}
    </div>
  )
}
