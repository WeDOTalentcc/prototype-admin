/**
 * Canonical glossary lookup — surfaces the official WSI/Bloom/BARS/etc.
 * definitions inside the chat (Task #745). Backed by the FastAPI endpoint
 * `GET /api/v1/glossary/terms/{term}` which reads from `docs/GLOSSARY.md`.
 */

export interface GlossaryEntryDTO {
  name: string
  sigla: string
  definition: string
  category: string
}

export type GlossaryLookupResult =
  | { ok: true; entry: GlossaryEntryDTO }
  | { ok: false; status: number; message: string }

let cachedTerms: GlossaryEntryDTO[] | null = null
let pendingTerms: Promise<GlossaryEntryDTO[]> | null = null

/**
 * Return the canonical glossary terms (cached client-side). Powers passive
 * tooltip highlighting in chat replies (Task #759). Falls back to an empty
 * list when the backend is unreachable so callers can render plain text.
 */
export async function listGlossaryTerms(): Promise<GlossaryEntryDTO[]> {
  if (cachedTerms) return cachedTerms
  if (pendingTerms) return pendingTerms
  pendingTerms = (async () => {
    try {
      const resp = await fetch("/api/backend-proxy/api/v1/glossary/terms", {
        method: "GET",
        headers: { "Accept": "application/json" },
      })
      if (!resp.ok) {
        cachedTerms = []
        return cachedTerms
      }
      const body = (await resp.json()) as {
        success?: boolean
        data?: { terms?: GlossaryEntryDTO[] }
      }
      cachedTerms = body?.data?.terms ?? []
      return cachedTerms
    } catch {
      cachedTerms = []
      return cachedTerms
    } finally {
      pendingTerms = null
    }
  })()
  return pendingTerms
}

/** Test-only helper to reset the in-memory cache between specs. */
export function __resetGlossaryCache(): void {
  cachedTerms = null
  pendingTerms = null
}

export async function lookupGlossaryTerm(term: string): Promise<GlossaryLookupResult> {
  const cleaned = term.trim()
  if (!cleaned) {
    return { ok: false, status: 422, message: "Informe um termo apos /definir." }
  }
  try {
    const resp = await fetch(`/api/backend-proxy/api/v1/glossary/terms/${encodeURIComponent(cleaned)}`, {
      method: "GET",
      headers: { "Accept": "application/json" },
    })
    if (resp.status === 404) {
      return {
        ok: false,
        status: 404,
        message: `Nao encontrei "${cleaned}" no glossario canonico (docs/GLOSSARY.md).`,
      }
    }
    if (!resp.ok) {
      return {
        ok: false,
        status: resp.status,
        message: `Falha ao consultar o glossario (HTTP ${resp.status}).`,
      }
    }
    const body = (await resp.json()) as { success: boolean; data: GlossaryEntryDTO }
    if (!body?.success || !body.data) {
      return { ok: false, status: 500, message: "Resposta invalida do servico de glossario." }
    }
    return { ok: true, entry: body.data }
  } catch (err) {
    return {
      ok: false,
      status: 0,
      message: `Sem conexao com o servico de glossario: ${(err as Error).message}`,
    }
  }
}

/**
 * Format a glossary entry as a chat-friendly Markdown string. Used by
 * UnifiedChat to render the LIA reply for `/definir <termo>`.
 */
export function formatGlossaryEntryMarkdown(entry: GlossaryEntryDTO): string {
  const heading = entry.sigla
    ? `**${entry.name}** (${entry.sigla})`
    : `**${entry.name}**`
  const lines = [heading, "", entry.definition]
  if (entry.category) {
    lines.push("", `_Categoria: ${entry.category} • Fonte: docs/GLOSSARY.md_`)
  } else {
    lines.push("", `_Fonte: docs/GLOSSARY.md_`)
  }
  return lines.join("\n")
}
