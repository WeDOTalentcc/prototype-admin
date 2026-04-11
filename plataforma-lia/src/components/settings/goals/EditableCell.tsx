"use client"
import { useState } from "react"

interface EditableCellProps {
  value: number | null
  onChange: (value: number) => void
  disabled?: boolean
  placeholder?: string
}

export function EditableCell({
  value,
  onChange,
  disabled = false,
  placeholder = "-"
}: EditableCellProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [inputValue, setInputValue] = useState(value?.toString() || "")

  const handleClick = () => {
    if (disabled) return
    setIsEditing(true)
    setInputValue(value?.toString() || "")
  }

  const handleSave = () => {
    const numValue = parseFloat(inputValue) || 0
    onChange(numValue)
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSave()
    else if (e.key === "Escape") {
      setIsEditing(false)
      setInputValue(value?.toString() || "")
    }
  }

  if (isEditing) {
    return (
      <input
        type="number"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onBlur={handleSave}
        onKeyDown={handleKeyDown}
        autoFocus
        min={0}
        className="w-10 px-1 py-1 text-xs border border-lia-border-medium rounded-xl text-center bg-lia-bg-primary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg"
      />
    )
  }

  const displayValue = value !== null && value !== undefined && value !== 0 ? value : placeholder
  return (
    <div
      onClick={handleClick}
      className="w-10 px-1 py-1 text-xs text-center cursor-pointer hover:bg-lia-bg-tertiary rounded-xl"
    >
      {displayValue}
    </div>
  )
}

EditableCell.displayName = "EditableCell"
