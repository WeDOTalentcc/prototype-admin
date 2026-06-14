"use client"

/**
 * Side drawer that shows the full canonical glossary entry for a term
 * (Task #760). Recruiters reach it by *clicking* a highlighted term in a
 * chat reply (the hover tooltip remains for the quick peek). The drawer
 * pulls the same canonical entry from `GET /api/v1/glossary/terms/{term}`,
 * exposes a copyable deep link (`?glossary=<term>`) and a direct link to
 * the matching `docs/GLOSSARY.md` anchor.
 */

import { useEffect, useRef, useState } from "react"
import { Copy, ExternalLink } from "lucide-react"

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import {
  GlossaryEntryDTO,
  GlossaryLookupResult,
  lookupGlossaryTerm,
} from "@/services/lia-api/glossary-api"

type DrawerState =
  | { status: "loading" }
  | { status: "ok"; entry: GlossaryEntryDTO }
  | { status: "error"; message: string }

interface GlossaryDrawerProps {
  term: string | null
  onClose: () => void
}

/**
 * Build the GitHub-style anchor used by `docs/GLOSSARY.md` headings, so the
 * "Open in docs" link lands on the exact entry. Mirrors the algorithm used
 * by GitHub's slugger: lowercase, strip diacritics, drop punctuation that
 * is not a hyphen, collapse whitespace into single hyphens.
 */
export function buildGlossaryDocAnchor(name: string): string {
  return name
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
}

/** Build the in-app shareable URL for a term (kept stable for tests). */
export function buildGlossaryDeepLink(term: string): string {
  if (typeof window === "undefined") {
    return `?glossary=${encodeURIComponent(term)}`
  }
  const url = new URL(window.location.href)
  url.searchParams.set("glossary", term)
  return url.toString()
}

export function GlossaryDrawer({ term, onClose }: GlossaryDrawerProps) {
  const [state, setState] = useState<DrawerState | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!term) {
      setState(null)
      return
    }
    let cancelled = false
    setState({ status: "loading" })
    lookupGlossaryTerm(term).then((result: GlossaryLookupResult) => {
      if (cancelled) return
      if (result.ok) setState({ status: "ok", entry: result.entry })
      else setState({ status: "error", message: result.message })
    })
    return () => {
      cancelled = true
    }
  }, [term])

  // Reflect the open term in the URL so the drawer can be deep-linked /
  // shared. Uses history.replaceState to avoid noisy back-button entries.
  // Skips the very first render when no term is open, otherwise we would
  // erase a `?glossary=` query that another component (e.g. the highlighter)
  // is about to consume to deep-link straight into the drawer.
  const didMountRef = useRef(false)
  useEffect(() => {
    if (typeof window === "undefined") return
    if (!didMountRef.current) {
      didMountRef.current = true
      if (!term) return
    }
    const url = new URL(window.location.href)
    if (term) url.searchParams.set("glossary", term)
    else url.searchParams.delete("glossary")
    window.history.replaceState({}, "", url.toString())
  }, [term])

  useEffect(() => {
    if (!copied) return
    const id = window.setTimeout(() => setCopied(false), 1500)
    return () => window.clearTimeout(id)
  }, [copied])

  const open = term !== null
  const handleOpenChange = (next: boolean) => {
    if (!next) onClose()
  }

  const handleCopy = async () => {
    if (!term) return
    const link = buildGlossaryDeepLink(term)
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(link)
      }
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  const entry = state?.status === "ok" ? state.entry : null
  const anchor = entry ? buildGlossaryDocAnchor(entry.name) : term ? buildGlossaryDocAnchor(term) : ""
  const docsHref = `/docs/GLOSSARY.md#${anchor}`

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent
        side="right"
        data-testid="glossary-drawer"
        className="flex w-full flex-col gap-4 overflow-y-auto sm:max-w-md"
      >
        <SheetHeader>
          <SheetTitle>{entry?.name ?? term ?? "Glossario"}</SheetTitle>
          {entry?.sigla ? (
            <SheetDescription>{entry.sigla}</SheetDescription>
          ) : (
            <SheetDescription>Definicao canonica do termo.</SheetDescription>
          )}
        </SheetHeader>

        {state?.status === "loading" ? (
          <p className="text-sm text-lia-text-secondary">Carregando definicao...</p>
        ) : null}

        {state?.status === "error" ? (
          <p className="text-sm text-lia-text-secondary">{state.message}</p>
        ) : null}

        {entry ? (
          <div className="space-y-3 text-sm text-lia-text-primary">
            <p className="whitespace-pre-line leading-relaxed">{entry.definition}</p>
            {entry.category ? (
              <p className="text-xs uppercase tracking-wide text-lia-text-secondary">
                Categoria: {entry.category}
              </p>
            ) : null}
          </div>
        ) : null}

        <div className="mt-auto space-y-2 border-t border-lia-border-subtle pt-4">
          <a
            href={docsHref}
            target="_blank"
            rel="noreferrer"
            data-testid="glossary-drawer-docs-link"
            className="inline-flex items-center gap-1 text-sm text-wedo-cyan-text hover:underline"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Abrir entrada completa em docs/GLOSSARY.md
          </a>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCopy}
              data-testid="glossary-drawer-copy-link"
            >
              <Copy className="mr-1.5 h-3.5 w-3.5" />
              {copied ? "Link copiado" : "Copiar link"}
            </Button>
            <span className="text-xs text-lia-text-secondary">
              Fonte: docs/GLOSSARY.md
            </span>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
