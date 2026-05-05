import { useCallback, useRef, useEffect } from "react"
import { Users, Briefcase } from "lucide-react"
import { useInputDropdown, type DropdownItem } from "./useInputDropdown"

interface UseMentionAutocompleteOptions {
  inputText: string
  selectionStart: number
  onInsertMention: (triggerStart: number, mention: string) => void
}

export function useMentionAutocomplete(options: UseMentionAutocompleteOptions) {
  const { inputText, selectionStart, onInsertMention } = options
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const lastQueryRef = useRef("")
  // Mirror dropdown.triggerStart through a ref so handleSelect (whose
  // useCallback deps are intentionally narrow) reads the latest value
  // instead of the stale render-0 value captured by the closure.
  const triggerStartRef = useRef(-1)

  const handleSelect = useCallback((item: DropdownItem) => {
    const type = item.category === "Candidatos" ? "candidate" : "job"
    const mention = "@[" + item.label + "](" + type + ":" + item.id + ")"
    onInsertMention(triggerStartRef.current, mention)
  }, [onInsertMention])

  const dropdown = useInputDropdown({
    triggerChar: "@",
    singleWordQuery: false,
    onSelect: handleSelect,
  })

  // Stable handles. Including the whole `dropdown` object in deps
  // would loop infinitely (the hook returns a fresh object literal
  // each render); destructure the useCallback-stabilized methods.
  const { checkTrigger, open, close, setItems, isOpen } = dropdown
  triggerStartRef.current = dropdown.triggerStart

  // Suppress reopen after explicit dismissal (Escape) — same pattern
  // as useSlashCommands.
  const dismissedAtRef = useRef<number | null>(null)
  const prevIsOpenRef = useRef(isOpen)

  const fetchResults = useCallback(async (query: string) => {
    if (query.length < 2) {
      setItems([])
      return
    }

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    try {
      const candidatesUrl = "/api/backend-proxy/candidates?search=" + encodeURIComponent(query) + "&page_size=5"
      const jobsUrl = "/api/backend-proxy/job-vacancies/search?query=" + encodeURIComponent(query) + "&page_size=5"

      const [candidatesRes, jobsRes] = await Promise.allSettled([
        fetch(candidatesUrl, { signal: controller.signal }),
        fetch(jobsUrl, { signal: controller.signal }),
      ])

      if (controller.signal.aborted) return

      const items: DropdownItem[] = []

      if (candidatesRes.status === "fulfilled" && candidatesRes.value.ok) {
        const data = await candidatesRes.value.json()
        const candidates = (data.results || data.items || data.candidates || []).slice(0, 5)
        candidates.forEach((c: any) => {
          items.push({
            id: String(c.id),
            label: c.name || c.full_name || ((c.first_name || "") + " " + (c.last_name || "")).trim(),
            subtitle: c.current_title || c.headline || c.email || "",
            category: "Candidatos",
            icon: Users,
          })
        })
      }

      if (jobsRes.status === "fulfilled" && jobsRes.value.ok) {
        const data = await jobsRes.value.json()
        const jobs = (data.results || data.items || data.jobs || data.vacancies || []).slice(0, 5)
        jobs.forEach((j: any) => {
          items.push({
            id: String(j.id),
            label: j.title || j.name || "",
            subtitle: j.department || j.location || j.status || "",
            category: "Vagas",
            icon: Briefcase,
          })
        })
      }

      setItems(items)
    } catch {
      // Silently ignore aborted/network errors
    }
  }, [setItems])

  // Watch input changes and trigger search
  useEffect(() => {
    const { triggered, query, triggerStart } = checkTrigger(inputText, selectionStart)

    if (prevIsOpenRef.current && !isOpen && triggered) {
      dismissedAtRef.current = triggerStart
    }
    prevIsOpenRef.current = isOpen

    if (!triggered) {
      dismissedAtRef.current = null
      if (isOpen) close()
      return
    }

    if (dismissedAtRef.current !== null && dismissedAtRef.current !== triggerStart) {
      dismissedAtRef.current = null
    }

    if (dismissedAtRef.current === triggerStart) return

    if (!isOpen) {
      open([], triggerStart, query)
    }

    if (query === lastQueryRef.current) return
    lastQueryRef.current = query

    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      fetchResults(query)
    }, 200)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [inputText, selectionStart, checkTrigger, open, close, isOpen, fetchResults])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort()
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  return {
    isOpen: dropdown.isOpen,
    selectedIndex: dropdown.selectedIndex,
    items: dropdown.items,
    handleKeyDown: dropdown.handleKeyDown,
    close: dropdown.close,
    selectItem: dropdown.selectItem,
  }
}
