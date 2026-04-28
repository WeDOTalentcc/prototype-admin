/**
 * TaskContextBar — rodapé persistente do wizard mostrando ação atual da LIA.
 * E.5 Frente E
 */
'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

interface TaskItem {
  id: string
  label: string
  type: 'vacancy' | 'screening' | 'calibration'
}

interface TaskContextBarProps {
  currentAction: string      // ex: "Criando vaga: Engenheiro Sênior"
  activeTasks?: TaskItem[]   // outras tarefas em andamento
  onSwitchTask?: (taskId: string) => void
}

const TYPE_ICONS: Record<TaskItem['type'], string> = {
  vacancy: '📋',
  screening: '🔍',
  calibration: '🎯',
}

export function TaskContextBar({
  currentAction,
  activeTasks = [],
  onSwitchTask,
}: TaskContextBarProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const openDropdown = useCallback(() => setDropdownOpen(true), [])
  const closeDropdown = useCallback(() => setDropdownOpen(false), [])

  const handleSelectTask = useCallback(
    (taskId: string) => {
      onSwitchTask?.(taskId)
      closeDropdown()
    },
    [onSwitchTask, closeDropdown],
  )

  // Cmd+K / Ctrl+K keyboard shortcut
  useEffect(() => {
    if (activeTasks.length === 0) return
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setDropdownOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeTasks.length])

  // Close dropdown on outside click
  useEffect(() => {
    if (!dropdownOpen) return
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        closeDropdown()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [dropdownOpen, closeDropdown])

  return (
    <div className="relative" ref={dropdownRef}>
      <div className="rounded-lg border bg-muted/50 px-4 py-2 flex items-center justify-between">
        {/* Left: current action */}
        <span className="text-xs text-muted-foreground truncate max-w-[70%]">
          📂 {currentAction}
        </span>

        {/* Right: switch task button (only when other tasks exist) */}
        {activeTasks.length > 0 && (
          <button
            type="button"
            onClick={openDropdown}
            className="flex items-center gap-1.5 text-xs font-medium text-foreground/80 hover:text-foreground px-2 py-0.5 rounded-md hover:bg-accent transition-colors motion-reduce:transition-none flex-shrink-0"
            aria-expanded={dropdownOpen}
            aria-haspopup="listbox"
          >
            Switch Task
            <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1 py-0.5 rounded border border-border bg-background text-[10px] font-mono leading-none">
              ⌘K
            </kbd>
          </button>
        )}
      </div>

      {/* Dropdown */}
      {dropdownOpen && activeTasks.length > 0 && (
        <div
          className="absolute bottom-full mb-1 left-0 right-0 z-50 rounded-lg border border-border bg-popover shadow-lg overflow-hidden"
          role="listbox"
          aria-label="Outras tarefas em andamento"
        >
          <div className="px-3 py-2 border-b border-border">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Outras tarefas
            </span>
          </div>
          <ul className="py-1 max-h-48 overflow-y-auto">
            {activeTasks.map((task) => (
              <li key={task.id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={false}
                  onClick={() => handleSelectTask(task.id)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-accent hover:text-accent-foreground transition-colors motion-reduce:transition-none"
                >
                  <span aria-hidden="true">{TYPE_ICONS[task.type]}</span>
                  <span className="truncate">{task.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
