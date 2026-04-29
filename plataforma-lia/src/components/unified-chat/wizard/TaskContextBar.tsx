/**
 * TaskContextBar — rodapé persistente do wizard mostrando ação atual da LIA.
 * E.5 Frente E
 *
 * Onda 30 D: connected to GET /api/v1/tasks/?status=in_progress via
 * useActiveTasks(). When tasks/activeTasks props are not provided, the
 * component fetches its own list. When the list is empty, only the current
 * action bar is shown (no Switch Task button, no dropdown).
 */
'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useActiveTasks, type ActiveTask } from '@/hooks/use-active-tasks'

/** @deprecated kept for backward compat with Onda 28 callers. Prefer ActiveTask. */
interface TaskItem {
  id: string
  label: string
  type: 'vacancy' | 'screening' | 'calibration'
}

interface TaskContextBarProps {
  /** ex: "Criando vaga: Engenheiro Senior" */
  currentAction: string
  /**
   * Active tasks (Onda 30 D shape). When neither this nor activeTasks is
   * passed, the component fetches via useActiveTasks().
   */
  tasks?: ActiveTask[]
  /** @deprecated legacy prop from Onda 28; use `tasks` instead. */
  activeTasks?: TaskItem[]
  onSwitchTask?: (taskId: string) => void
}

const TYPE_ICONS: Record<string, string> = {
  vacancy: '📋',
  vacancy_creation: '📋',
  screening: '🔍',
  calibration: '🎯',
  general: '📌',
}

interface NormalizedTask {
  id: string
  label: string
  iconKey: string
}

function normalizeFromActiveTask(task: ActiveTask): NormalizedTask {
  return { id: task.id, label: task.title, iconKey: task.type }
}

function normalizeFromTaskItem(task: TaskItem): NormalizedTask {
  return { id: task.id, label: task.label, iconKey: task.type }
}

export function TaskContextBar({
  currentAction,
  tasks,
  activeTasks,
  onSwitchTask,
}: TaskContextBarProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Only fetch when caller did not pass either prop. SWR is fine to call
  // unconditionally, but we want to avoid network noise when a parent already
  // has the list (tests, mocks, future server-fetched contexts).
  const callerProvidedTasks = tasks !== undefined || activeTasks !== undefined
  const fetched = useActiveTasks()
  const fetchedTasks = callerProvidedTasks ? [] : fetched.tasks

  const items: NormalizedTask[] = useMemo(() => {
    if (tasks !== undefined) {
      return tasks.map(normalizeFromActiveTask)
    }
    if (activeTasks !== undefined) {
      return activeTasks.map(normalizeFromTaskItem)
    }
    return fetchedTasks.map(normalizeFromActiveTask)
  }, [tasks, activeTasks, fetchedTasks])

  const hasOtherTasks = items.length > 0

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
    if (!hasOtherTasks) return
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setDropdownOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [hasOtherTasks])

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
        {hasOtherTasks && (
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
      {dropdownOpen && hasOtherTasks && (
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
            {items.map((task) => (
              <li key={task.id}>
                <button
                  type="button"
                  role="option"
                  aria-selected={false}
                  onClick={() => handleSelectTask(task.id)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-accent hover:text-accent-foreground transition-colors motion-reduce:transition-none"
                >
                  <span aria-hidden="true">{TYPE_ICONS[task.iconKey] ?? TYPE_ICONS.general}</span>
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
