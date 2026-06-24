/**
 * useAutoSave — Generic auto-save hook with debounce (GAP-06-005).
 *
 * Saves form data after a debounce window expires.  Wire to any wizard or form
 * that has a draft endpoint so partial state survives navigation away.
 *
 * @example
 * const { isSaving, lastSavedAt } = useAutoSave({
 *   data: formValues,
 *   onSave: async (d) => await patchDraft(jobId, d),
 *   debounceMs: 2000,
 * })
 */
import { useEffect, useRef, useCallback, useState } from "react"

export interface UseAutoSaveOptions<T> {
  /** Data to auto-save — changes to this value reset the debounce timer. */
  data: T
  /** Stable save function (wrap in useCallback in the consumer). */
  onSave: (data: T) => Promise<void> | void
  /** Debounce delay in ms (default 2000). */
  debounceMs?: number
  /** Pause auto-save when true — e.g. during manual submit or on unmount. */
  disabled?: boolean
}

export interface UseAutoSaveReturn {
  /** True while the onSave call is in flight. */
  isSaving: boolean
  /** Timestamp of the last successful save, or null if never saved. */
  lastSavedAt: Date | null
  /** Immediately trigger a save bypassing the debounce timer. */
  triggerSave: () => void
}

export function useAutoSave<T>({
  data,
  onSave,
  debounceMs = 2000,
  disabled = false,
}: UseAutoSaveOptions<T>): UseAutoSaveReturn {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isSavingRef = useRef(false)
  const [isSaving, setIsSaving] = useState(false)
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)

  const doSave = useCallback(async () => {
    // Guard against concurrent saves
    if (isSavingRef.current) return
    isSavingRef.current = true
    setIsSaving(true)
    try {
      await onSave(data)
      setLastSavedAt(new Date())
    } finally {
      isSavingRef.current = false
      setIsSaving(false)
    }
  }, [data, onSave])

  useEffect(() => {
    if (disabled) return
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(doSave, debounceMs)
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [data, debounceMs, disabled, doSave])

  const triggerSave = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    void doSave()
  }, [doSave])

  return { isSaving, lastSavedAt, triggerSave }
}
