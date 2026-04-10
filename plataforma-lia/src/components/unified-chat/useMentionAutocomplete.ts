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

  const handleSelect = useCallback((item: DropdownItem) => {
    const type = item.category === "Candidatos" ? "candidate" : "job"
    const mention = "@[" + item.label + "](" + type + ":" + item.id + ")"
    onInsertMention(dropdown.triggerStart, mention)
  }, [onInsertMention])

  const dropdown = useInputDropdown({
    triggerChar: "@",
    requireStartOfLine: false,
    onSelect: handleSelect,
  })

  const fetchResults = useCallback(async (query: string) => {
    if (query.length < 2) {
      dropdown.setItems([])
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

      dropdown.setItems(items)
    } catch {
      // Silently ignore aborted/network errors
    }
  }, [dropdown])

  // Watch input changes and trigger search
  useEffect(() => {
    const { triggered, query, triggerStart } = dropdown.checkTrigger(inputText, selectionStart)

    if (!triggered) {
      if (dropdown.isOpen) dropdown.close()
      return
    }

    if (!dropdown.isOpen) {
      dropdown.open([], triggerStart, query)
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
  }, [inputText, selectionStart, dropdown, fetchResults])

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
