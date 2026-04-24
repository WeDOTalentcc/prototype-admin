"use client"

/**
 * Renders chat HTML with canonical glossary terms (WSI, BARS, Bloom, etc.)
 * highlighted and surfaced as hover/tap tooltips. Powers Task #759 — recruiters
 * see the official meaning passively, without typing `/definir <termo>`.
 *
 * The list of terms to highlight comes from `GET /api/v1/glossary/terms` and
 * each tooltip definition is fetched from `GET /api/v1/glossary/terms/{term}`
 * (the same endpoint backing the `/definir` slash command), so there is a
 * single source of truth (`docs/GLOSSARY.md`).
 */

import {
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react"
import { createPortal } from "react-dom"

import { cn } from "@/lib/utils"
import { sanitizeHtml } from "@/lib/sanitize"
import {
  GlossaryEntryDTO,
  listGlossaryTerms,
  lookupGlossaryTerm,
} from "@/services/lia-api/glossary-api"
import { GlossaryDrawer } from "./glossary-drawer"

interface GlossaryHighlightedTextProps {
  html: string
  className?: string
}

const HIGHLIGHT_CLASS =
  "underline decoration-dotted decoration-wedo-cyan underline-offset-2 cursor-help focus:outline-none focus:ring-1 focus:ring-wedo-cyan rounded-sm"

const SKIP_TAGS = new Set(["A", "CODE", "PRE", "SCRIPT", "STYLE", "BUTTON"])

function buildAliases(entry: GlossaryEntryDTO): string[] {
  const aliases = new Set<string>()
  if (entry.name) aliases.add(entry.name)
  if (entry.sigla) aliases.add(entry.sigla)
  return Array.from(aliases).filter(
    (a) => a.length >= 2 && !a.includes("_"),
  )
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

interface CompiledMatcher {
  pattern: RegExp
  aliasToCanonical: Map<string, string>
}

function compileMatcher(terms: GlossaryEntryDTO[]): CompiledMatcher | null {
  const aliasToCanonical = new Map<string, string>()
  const aliases: string[] = []
  for (const entry of terms) {
    for (const alias of buildAliases(entry)) {
      const lower = alias.toLowerCase()
      if (!aliasToCanonical.has(lower)) {
        aliasToCanonical.set(lower, entry.name)
        aliases.push(alias)
      }
    }
  }
  if (!aliases.length) return null
  aliases.sort((a, b) => b.length - a.length)
  const pattern = new RegExp(
    `\\b(${aliases.map(escapeRegex).join("|")})\\b`,
    "giu",
  )
  return { pattern, aliasToCanonical }
}

function highlightInRoot(root: HTMLElement, matcher: CompiledMatcher): void {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      let parent: Node | null = node.parentNode
      while (parent && parent !== root) {
        if (parent.nodeType === 1) {
          const el = parent as HTMLElement
          if (SKIP_TAGS.has(el.tagName)) return NodeFilter.FILTER_REJECT
          if (el.hasAttribute("data-glossary-term")) {
            return NodeFilter.FILTER_REJECT
          }
        }
        parent = parent.parentNode
      }
      const value = node.nodeValue ?? ""
      if (!value.trim()) return NodeFilter.FILTER_REJECT
      const probe = new RegExp(matcher.pattern.source, matcher.pattern.flags)
      return probe.test(value) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
    },
  })

  const targets: Text[] = []
  let current: Node | null
  while ((current = walker.nextNode())) {
    targets.push(current as Text)
  }

  for (const text of targets) {
    const parent = text.parentNode
    if (!parent) continue
    const value = text.nodeValue ?? ""
    const re = new RegExp(matcher.pattern.source, matcher.pattern.flags)
    const fragment = document.createDocumentFragment()
    let last = 0
    let match: RegExpExecArray | null
    while ((match = re.exec(value))) {
      if (match.index > last) {
        fragment.appendChild(
          document.createTextNode(value.slice(last, match.index)),
        )
      }
      const canonical =
        matcher.aliasToCanonical.get(match[0].toLowerCase()) ?? match[0]
      const span = document.createElement("span")
      span.setAttribute("data-glossary-term", canonical)
      span.setAttribute("tabindex", "0")
      span.setAttribute("role", "button")
      span.setAttribute(
        "aria-label",
        `Ver definicao canonica de ${canonical}`,
      )
      span.className = HIGHLIGHT_CLASS
      span.textContent = match[0]
      fragment.appendChild(span)
      last = match.index + match[0].length
    }
    if (last < value.length) {
      fragment.appendChild(document.createTextNode(value.slice(last)))
    }
    parent.replaceChild(fragment, text)
  }
}

type DefinitionState =
  | { status: "loading" }
  | { status: "ok"; entry: GlossaryEntryDTO }
  | { status: "error"; message: string }

interface ActiveTooltip {
  term: string
  rect: DOMRect
}

export function GlossaryHighlightedText({
  html,
  className,
}: GlossaryHighlightedTextProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [terms, setTerms] = useState<GlossaryEntryDTO[]>([])
  const [active, setActive] = useState<ActiveTooltip | null>(null)
  const [drawerTerm, setDrawerTerm] = useState<string | null>(null)
  const [definitions, setDefinitions] = useState<
    Record<string, DefinitionState>
  >({})

  const sanitized = useMemo(() => sanitizeHtml(html), [html])
  const matcher = useMemo(() => compileMatcher(terms), [terms])

  // Load (and cache) the canonical term list once on mount.
  useEffect(() => {
    let cancelled = false
    listGlossaryTerms().then((list) => {
      if (!cancelled) setTerms(list)
    })
    return () => {
      cancelled = true
    }
  }, [])

  // Walk the rendered DOM to wrap canonical term occurrences. Re-runs whenever
  // the bubble's HTML changes (streaming) or the term list arrives.
  useLayoutEffect(() => {
    const root = containerRef.current
    if (!root) return
    if (!matcher) return
    highlightInRoot(root, matcher)
  }, [sanitized, matcher])

  const inFlightRef = useRef<Set<string>>(new Set())

  const fetchDefinition = (term: string): void => {
    if (inFlightRef.current.has(term)) return
    inFlightRef.current.add(term)
    setDefinitions((prev) => {
      if (prev[term]) return prev
      return { ...prev, [term]: { status: "loading" } }
    })
    lookupGlossaryTerm(term).then((result) => {
      inFlightRef.current.delete(term)
      setDefinitions((prev) => {
        if (result.ok) {
          return { ...prev, [term]: { status: "ok", entry: result.entry } }
        }
        return {
          ...prev,
          [term]: { status: "error", message: result.message },
        }
      })
    })
  }

  const openFor = (target: HTMLElement): void => {
    const term = target.getAttribute("data-glossary-term")
    if (!term) return
    setActive({ term, rect: target.getBoundingClientRect() })
    const existing = definitions[term]
    if (!existing || existing.status === "error") fetchDefinition(term)
  }

  const handleEvent = (event: React.SyntheticEvent<HTMLDivElement>): void => {
    const target = event.target
    if (!(target instanceof HTMLElement)) return
    const trigger = target.closest<HTMLElement>("[data-glossary-term]")
    if (!trigger) return
    if (event.type === "click") {
      event.preventDefault()
      const term = trigger.getAttribute("data-glossary-term")
      if (term) {
        setActive(null)
        setDrawerTerm(term)
      }
      return
    }
    openFor(trigger)
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>): void => {
    if (event.key !== "Enter" && event.key !== " ") return
    const target = event.target
    if (!(target instanceof HTMLElement)) return
    const trigger = target.closest<HTMLElement>("[data-glossary-term]")
    if (!trigger) return
    event.preventDefault()
    const term = trigger.getAttribute("data-glossary-term")
    if (term) {
      setActive(null)
      setDrawerTerm(term)
    }
  }

  // Open the drawer automatically when the page is loaded with a deep link
  // such as `?glossary=BARS`. We attempt the open immediately on mount so the
  // drawer still works when the canonical term list endpoint fails or is
  // empty — the drawer's own lookup hits the per-term endpoint and will
  // surface a clean error if the term is unknown. Once the term list does
  // arrive we re-evaluate to upgrade the requested string to its canonical
  // form (so `?glossary=wsi` becomes the canonical "WSI").
  const deepLinkConsumedRef = useRef(false)
  useEffect(() => {
    if (typeof window === "undefined") return
    const params = new URLSearchParams(window.location.search)
    const requested = params.get("glossary")
    if (!requested) return
    const trimmed = requested.trim()
    if (!trimmed) return
    if (terms.length) {
      const lower = trimmed.toLowerCase()
      const match = terms.find(
        (entry) =>
          entry.name.toLowerCase() === lower ||
          entry.sigla?.toLowerCase() === lower,
      )
      setDrawerTerm(match ? match.name : trimmed)
      deepLinkConsumedRef.current = true
      return
    }
    if (deepLinkConsumedRef.current) return
    setDrawerTerm(trimmed)
    deepLinkConsumedRef.current = true
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terms.length])

  const handleLeave = (event: React.MouseEvent<HTMLDivElement>): void => {
    const related = event.relatedTarget as HTMLElement | null
    if (related && related.closest?.("[data-glossary-tooltip]")) return
    setActive(null)
  }

  // Close on outside click / Escape.
  useEffect(() => {
    if (!active) return
    const handlePointer = (event: MouseEvent): void => {
      const target = event.target as HTMLElement | null
      if (!target) return
      if (target.closest("[data-glossary-tooltip]")) return
      if (target.closest("[data-glossary-term]")) return
      setActive(null)
    }
    const handleKey = (event: KeyboardEvent): void => {
      if (event.key === "Escape") setActive(null)
    }
    document.addEventListener("mousedown", handlePointer)
    document.addEventListener("keydown", handleKey)
    return () => {
      document.removeEventListener("mousedown", handlePointer)
      document.removeEventListener("keydown", handleKey)
    }
  }, [active])

  return (
    <>
      <div
        ref={containerRef}
        className={className}
        dangerouslySetInnerHTML={{ __html: sanitized }}
        onMouseOver={handleEvent}
        onMouseOut={handleLeave}
        onFocus={handleEvent}
        onBlur={() => setActive(null)}
        onClick={handleEvent}
        onKeyDown={handleKeyDown}
      />
      {active ? (
        <GlossaryTooltipPortal
          rect={active.rect}
          state={definitions[active.term] ?? { status: "loading" }}
          term={active.term}
          onClose={() => setActive(null)}
        />
      ) : null}
      <GlossaryDrawer term={drawerTerm} onClose={() => setDrawerTerm(null)} />
    </>
  )
}

interface TooltipProps {
  rect: DOMRect
  state: DefinitionState
  term: string
  onClose: () => void
}

function GlossaryTooltipPortal({ rect, state, term, onClose }: TooltipProps) {
  if (typeof document === "undefined") return null
  const top = rect.top + window.scrollY
  const left = rect.left + window.scrollX + rect.width / 2
  return createPortal(
    <div
      data-glossary-tooltip="true"
      role="tooltip"
      onMouseLeave={onClose}
      style={{
        position: "absolute",
        top,
        left,
        transform: "translate(-50%, calc(-100% - 8px))",
        zIndex: 60,
        maxWidth: "min(20rem, calc(100vw - 1rem))",
      }}
      className={cn(
        "pointer-events-auto rounded-md border border-lia-border-default bg-lia-bg-elevated px-3 py-2 text-xs leading-snug text-lia-text-primary shadow-lg dark:bg-lia-bg-elevated"
      )}
    >
      <GlossaryTooltipBody state={state} term={term} />
      <div className="mt-1 text-[10px] text-lia-text-secondary">
        Fonte: docs/GLOSSARY.md
      </div>
    </div>,
    document.body,
  )
}

function GlossaryTooltipBody({
  state,
  term,
}: {
  state: DefinitionState
  term: string
}) {
  if (state.status === "loading") {
    return (
      <div>
        <div className="font-semibold">{term}</div>
        <div className="text-lia-text-secondary">Carregando definicao...</div>
      </div>
    )
  }
  if (state.status === "error") {
    return (
      <div>
        <div className="font-semibold">{term}</div>
        <div className="text-lia-text-secondary">{state.message}</div>
      </div>
    )
  }
  const { entry } = state
  return (
    <div>
      <div className="font-semibold">
        {entry.name}
        {entry.sigla ? (
          <span className="ml-1 font-normal text-lia-text-secondary">
            ({entry.sigla})
          </span>
        ) : null}
      </div>
      <div className="mt-0.5 whitespace-pre-line">{entry.definition}</div>
      {entry.category ? (
        <div className="mt-1 text-[10px] uppercase tracking-wide text-lia-text-secondary">
          {entry.category}
        </div>
      ) : null}
    </div>
  )
}
