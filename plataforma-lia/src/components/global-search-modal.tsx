"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { usePathname } from "next/navigation"
import { useLocale } from "next-intl"
import { navigationCatalog } from "@/lib/navigation/navigation-commands"
import { useCommandCatalog } from "@/hooks/lia/use-command-catalog"
import { cn } from "@/lib/utils"
import {
  Search, X, User, Briefcase, MessageSquare,
  Compass, Sparkles, ArrowUpRight, Loader2, Brain,
  Settings, Zap, FolderOpen,
} from "lucide-react"

interface GlobalSearchModalProps {
  isOpen: boolean
  onClose: () => void
  onNavigate?: (page: string, id?: string) => void
}

interface SearchHit {
  id: string
  type: "candidate" | "job"
  title: string
  subtitle: string
}

interface Section {
  id: string
  label: string
  items: Item[]
}

interface Item {
  id: string
  label: string
  sublabel?: string
  icon: React.ElementType
  iconColor?: string
  onSelect: () => void
}

const ICON_COLORS: Record<string, string> = {
  nav:       "text-wedo-cyan-text",
  action:    "text-wedo-orange-text",
  candidate: "text-blue-500",
  job:       "text-emerald-600",
}

export function GlobalSearchModal({ isOpen, onClose, onNavigate }: GlobalSearchModalProps) {
  const [query, setQuery] = useState("")
  const [hits, setHits] = useState<SearchHit[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [activeIdx, setActiveIdx] = useState(0)
  const router = useRouter()
  const locale = useLocale()
  const pathname = usePathname()
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const { data: actionCatalog } = useCommandCatalog()
  const [contextualHints, setContextualHints] = useState<Item[]>([])

  // ── Nav + action items (static, always shown when no query) ──────────
  const navItems: Item[] = navigationCatalog(locale).map((n) => ({
    id: `nav-${n.page}`,
    label: `Ir para ${n.label}`,
    icon: Compass,
    iconColor: ICON_COLORS.nav,
    onSelect: () => { router.push(n.url); onClose() },
  }))

  const actionItems: Item[] = (actionCatalog ?? []).slice(0, 8).map((a) => ({
    id: `action-${a.intent}`,
    label: a.label,
    sublabel: a.requires_confirmation ? "Confirma na tela" : "Via IA",
    icon: Sparkles,
    iconColor: ICON_COLORS.action,
    onSelect: () => {
      window.dispatchEvent(new CustomEvent("lia:prefill-message", { detail: { message: a.label } }))
      onClose()
    },
  }))

  // ── LIA Contextual Hints (load on open, by page context) ─────────────
  useEffect(() => {
    if (!isOpen) return
    const pageContext = pathname?.split("/").filter(Boolean).slice(1).join("/") ?? ""
    const abort = new AbortController()

    fetch(
      `/api/backend-proxy/search/contextual-hints?page_context=${encodeURIComponent(pageContext)}&limit=5`,
      { signal: abort.signal }
    )
      .then(r => (r.ok ? r.json() : null))
      .then(data => {
        if (!data?.hints) return
        setContextualHints(
          data.hints.map((h: { label: string; target: string; context?: string }) => ({
            id: `hint-${h.label}`,
            label: h.label,
            sublabel: h.context,
            icon: Brain,
            iconColor: "text-wedo-cyan",
            onSelect: () => { router.push(h.target); onClose() },
          }))
        )
      })
      .catch(() => {}) // timeout ou erro: silencioso

    const timer = setTimeout(() => abort.abort(), 2000)
    return () => { clearTimeout(timer); abort.abort() }
  }, [isOpen, pathname, router, onClose])

  // ── Real search ───────────────────────────────────────────────────────
  useEffect(() => {
    const q = query.trim()
    if (!q) { setHits([]); return }

    const abort = new AbortController()
    setIsSearching(true)

    const run = async () => {
      try {
        const [jobsRes, candidatesRes] = await Promise.allSettled([
          fetch(`/api/backend-proxy/job-vacancies/search?query=${encodeURIComponent(q)}&page=1&page_size=5`, { signal: abort.signal }),
          fetch(`/api/backend-proxy/candidates/search/local`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: q, page: 1, page_size: 5 }),
            signal: abort.signal,
          }),
        ])

        const results: SearchHit[] = []

        if (jobsRes.status === "fulfilled" && jobsRes.value.ok) {
          const data = await jobsRes.value.json()
          const jobs = data?.data ?? data?.results ?? data?.items ?? []
          for (const j of jobs.slice(0, 5)) {
            results.push({
              id: `job-${j.id}`,
              type: "job",
              title: j.title ?? j.name ?? "Vaga",
              subtitle: j.status ?? j.department ?? "",
            })
          }
        }

        if (candidatesRes.status === "fulfilled" && candidatesRes.value.ok) {
          const data = await candidatesRes.value.json()
          const candidates = data?.data ?? data?.results ?? data?.candidates ?? []
          for (const c of candidates.slice(0, 5)) {
            results.push({
              id: `candidate-${c.id}`,
              type: "candidate",
              title: c.name ?? c.full_name ?? "Candidato",
              subtitle: c.current_position ?? c.email ?? "",
            })
          }
        }

        setHits(results)
      } catch {
        // abort ou erro — silencioso
      } finally {
        setIsSearching(false)
      }
    }

    const timer = setTimeout(run, 300)
    return () => { clearTimeout(timer); abort.abort() }
  }, [query])

  // ── Build sections ────────────────────────────────────────────────────
  const sections: Section[] = query.trim()
    ? [
        hits.filter(h => h.type === "job").length > 0 && {
          id: "jobs",
          label: "VAGAS",
          items: hits.filter(h => h.type === "job").map(h => ({
            id: h.id,
            label: h.title,
            sublabel: h.subtitle,
            icon: Briefcase,
            iconColor: ICON_COLORS.job,
            onSelect: () => { onNavigate?.("Vagas", h.id.replace("job-", "")); onClose() },
          })),
        },
        hits.filter(h => h.type === "candidate").length > 0 && {
          id: "candidates",
          label: "CANDIDATOS",
          items: hits.filter(h => h.type === "candidate").map(h => ({
            id: h.id,
            label: h.title,
            sublabel: h.subtitle,
            icon: User,
            iconColor: ICON_COLORS.candidate,
            onSelect: () => { onNavigate?.("Funil de Talentos", h.id.replace("candidate-", "")); onClose() },
          })),
        },
        navItems.filter(n => n.label.toLowerCase().includes(query.toLowerCase())).length > 0 && {
          id: "nav-filtered",
          label: "NAVEGAÇÃO",
          items: navItems.filter(n => n.label.toLowerCase().includes(query.toLowerCase())).slice(0, 5),
        },
        actionItems.filter(a => a.label.toLowerCase().includes(query.toLowerCase())).length > 0 && {
          id: "actions-filtered",
          label: "AÇÕES",
          items: actionItems.filter(a => a.label.toLowerCase().includes(query.toLowerCase())).slice(0, 5),
        },
      ].filter(Boolean) as Section[]
    : [
        contextualHints.length > 0
          ? { id: "lia-hints", label: "SUGESTÕES DA LIA", items: contextualHints }
          : null,
        { id: "nav", label: "NAVEGAÇÃO", items: navItems },
        actionItems.length > 0 ? { id: "actions", label: "AÇÕES RÁPIDAS", items: actionItems } : null,
      ].filter(Boolean) as Section[]

  const allItems = sections.flatMap(s => s.items)

  // ── Keyboard navigation ───────────────────────────────────────────────
  useEffect(() => { setActiveIdx(0) }, [query, hits])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setActiveIdx(i => Math.min(i + 1, allItems.length - 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setActiveIdx(i => Math.max(i - 1, 0))
    } else if (e.key === "Tab") {
      e.preventDefault()
      // Jump to next section
      let cumIdx = 0
      for (const s of sections) {
        if (cumIdx + s.items.length > activeIdx) {
          const nextSectionStart = cumIdx + s.items.length
          setActiveIdx(nextSectionStart < allItems.length ? nextSectionStart : 0)
          break
        }
        cumIdx += s.items.length
      }
    } else if (e.key === "Enter") {
      e.preventDefault()
      allItems[activeIdx]?.onSelect()
    } else if (e.key === "Escape") {
      onClose()
    }
  }, [allItems, activeIdx, sections, onClose])

  // ── Scroll active item into view ──────────────────────────────────────
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-idx="${activeIdx}"]`)
    el?.scrollIntoView({ block: "nearest" })
  }, [activeIdx])

  // ── Focus on open ─────────────────────────────────────────────────────
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus()
      setQuery("")
      setHits([])
      setActiveIdx(0)
    }
  }, [isOpen])

  if (!isOpen) return null

  let globalIdx = 0

  return (
    <div className="fixed inset-0 bg-lia-overlay z-50 flex items-start justify-center pt-16" onClick={onClose}>
      <div
        className="bg-lia-bg-primary rounded-xl w-full max-w-2xl max-h-[70vh] overflow-hidden border border-lia-border-subtle shadow-2xl flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Input */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-lia-border-subtle">
          <Search className="w-4 h-4 text-lia-text-secondary flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Pesquisar ou executar um comando..."
            className="flex-1 bg-transparent text-sm text-lia-text-primary placeholder:text-lia-text-tertiary outline-none"
          />
          {isSearching
            ? <Loader2 className="w-4 h-4 text-lia-text-secondary animate-spin flex-shrink-0" />
            : query
              ? <button onClick={() => setQuery("")} className="text-lia-text-secondary hover:text-lia-text-primary"><X className="w-4 h-4" /></button>
              : <kbd className="text-[10px] text-lia-text-muted font-mono bg-lia-bg-secondary px-1.5 py-0.5 rounded border border-lia-border-subtle">Esc</kbd>
          }
        </div>

        {/* Scrollable list */}
        <div ref={listRef} className="flex-1 overflow-y-auto">
          {query.trim() && !isSearching && hits.length === 0 &&
            sections.filter(s => s.id.includes("filtered")).length === 0 && (
            <div className="py-12 text-center">
              <p className="text-sm text-lia-text-secondary">Nenhum resultado para &quot;{query}&quot;</p>
            </div>
          )}

          {sections.map((section) => (
            <div key={section.id}>
              <div className="px-4 pt-4 pb-1">
                <span className="text-[10px] font-semibold text-lia-text-tertiary tracking-widest">
                  {section.label}
                </span>
              </div>
              {section.items.map((item) => {
                const idx = globalIdx++
                const isActive = idx === activeIdx
                const Icon = item.icon
                return (
                  <button
                    key={item.id}
                    data-idx={idx}
                    onClick={item.onSelect}
                    onMouseEnter={() => setActiveIdx(idx)}
                    className={cn(
                      "w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors",
                      isActive
                        ? "bg-lia-bg-secondary border-l-2 border-l-wedo-cyan"
                        : "border-l-2 border-l-transparent hover:bg-lia-bg-secondary"
                    )}
                  >
                    <Icon className={cn("w-4 h-4 flex-shrink-0", item.iconColor ?? "text-lia-text-secondary")} />
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-lia-text-primary truncate block">{item.label}</span>
                      {item.sublabel && (
                        <span className="text-xs text-lia-text-tertiary truncate block">{item.sublabel}</span>
                      )}
                    </div>
                    <ArrowUpRight className={cn("w-3.5 h-3.5 flex-shrink-0 transition-opacity", isActive ? "text-lia-text-secondary opacity-100" : "opacity-0")} />
                  </button>
                )
              })}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-lia-border-subtle bg-lia-bg-primary flex items-center justify-between text-[11px] text-lia-text-tertiary">
          <div className="flex items-center gap-4">
            <span><kbd className="font-mono bg-lia-bg-secondary px-1 py-0.5 rounded border border-lia-border-subtle">↵</kbd> selecionar</span>
            <span><kbd className="font-mono bg-lia-bg-secondary px-1 py-0.5 rounded border border-lia-border-subtle">↑↓</kbd> navegar</span>
            <span><kbd className="font-mono bg-lia-bg-secondary px-1 py-0.5 rounded border border-lia-border-subtle">Tab</kbd> pular seção</span>
            <span><kbd className="font-mono bg-lia-bg-secondary px-1 py-0.5 rounded border border-lia-border-subtle">Esc</kbd> fechar</span>
          </div>
          <div className="flex items-center gap-1">
            <Brain className="w-3 h-3 text-wedo-cyan" />
            <span>IA</span>
          </div>
        </div>
      </div>
    </div>
  )
}
