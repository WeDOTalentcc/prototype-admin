/**
 * Sentinela de cabeçalho — Task #1050
 *
 * As Tasks #1048 e #1049 padronizaram todos os cabeçalhos de seção do Agent
 * Studio para usar o componente compartilhado <TabSectionHeader />. Este teste
 * impede que um futuro PR volte a introduzir um <h2>/<h3> inline com o estilo
 * canônico (font-semibold + text-lia-text-primary) direto dentro de
 * `pages-agent-studio/`, refazendo o drift visual.
 *
 * Se este teste falhar, substitua o cabeçalho inline por:
 *
 *   import { TabSectionHeader } from "@/components/pages-agent-studio/TabSectionHeader"
 *   ...
 *   <TabSectionHeader title={...} subtitle={...} icon={...} count={...} actions={...} />
 *
 * O TabSectionHeader já aplica o estilo correto (h2 text-sm font-semibold
 * text-lia-text-primary) e mantém a harmonização entre as abas.
 */
import { describe, expect, it } from "vitest"
import { readdirSync, readFileSync, statSync } from "node:fs"
import { join, relative } from "node:path"
import { fileURLToPath } from "node:url"
import { dirname } from "node:path"

const HERE = dirname(fileURLToPath(import.meta.url))
const PAGES_AGENT_STUDIO_DIR = join(HERE, "..")

const ALLOWED_FILES = new Set<string>([
  "TabSectionHeader.tsx",
  // Cabecalhos legitimos fora do contrato TabSectionHeader:
  // - StudioEmptyState: titulo centralizado de empty state (com emoji), nao
  //   eh um cabecalho de tab/secao. Pattern visual distinto.
  // - StudioControlRoom: composicao propria do Control Room; header proprio.
  // - DecisionTreeDrawer: sub-headings (<h3>) dentro de um Sheet/drawer
  //   accordion, nao sao section headers de tab.
  // - TemplateClonePanel: modal de detalhe didatico (Dialog). Os <h3> sao
  //   sub-secoes internas do modal ("Veja em acao", "O que faz", "Como
  //   trabalha"), mesmo caso do DecisionTreeDrawer — nao sao headers de tab.
  //   (redesign 2026-05-30 + Fase 3 Sprint 2 conversation preview.)
  "StudioEmptyState.tsx",
  "control-room/StudioControlRoom.tsx",
  "decision-tree/DecisionTreeDrawer.tsx",
  "template-clone/TemplateClonePanel.tsx",
])

function listTsxFiles(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) {
      if (entry === "__tests__" || entry === "__snapshots__" || entry === "node_modules") continue
      out.push(...listTsxFiles(full))
      continue
    }
    if (!entry.endsWith(".tsx")) continue
    if (entry.endsWith(".test.tsx") || entry.endsWith(".stories.tsx")) continue
    const rel = relative(PAGES_AGENT_STUDIO_DIR, full)
    if (ALLOWED_FILES.has(rel)) continue
    out.push(full)
  }
  return out
}

/**
 * Casa qualquer tag `<h2>`/`<h3>` cuja abertura contenha as DUAS classes
 * `font-semibold` e `text-lia-text-primary` aplicadas inline (em qualquer
 * ordem). Esse é o par que define um cabeçalho de seção e que o
 * `<TabSectionHeader />` encapsula — qualquer ocorrência dele inline em
 * `pages-agent-studio/` é a drift que as Tasks #1048/#1049 eliminaram.
 *
 * Limita o lookahead dentro da tag a 400 chars para evitar matches
 * across-elementos.
 */
function matchAllInOpeningTag(tag: "h2" | "h3", classes: string[]): RegExp[] {
  const permutations: string[][] = []
  const permute = (cur: string[], rest: string[]) => {
    if (rest.length === 0) {
      permutations.push(cur)
      return
    }
    for (let i = 0; i < rest.length; i += 1) {
      const next = rest.slice(0, i).concat(rest.slice(i + 1))
      permute(cur.concat(rest[i]), next)
    }
  }
  permute([], classes)
  return permutations.map((order) => {
    const body = order.map((c) => `\\b${c}\\b`).join("[^>]{0,400}")
    return new RegExp(`<${tag}\\b[^>]{0,400}${body}`, "s")
  })
}

const SIGNATURE_CLASSES = ["font-semibold", "text-lia-text-primary"]

const HEADING_REGEXES: RegExp[] = [
  ...matchAllInOpeningTag("h2", SIGNATURE_CLASSES),
  ...matchAllInOpeningTag("h3", SIGNATURE_CLASSES),
]

describe("Agent Studio — sentinela de cabeçalho (Task #1050)", () => {
  it("nenhum arquivo de pages-agent-studio/ usa <h2|<h3> inline com font-semibold + text-lia-text-primary", () => {
    const files = listTsxFiles(PAGES_AGENT_STUDIO_DIR)
    expect(files.length).toBeGreaterThan(0)

    const offenders: string[] = []
    for (const file of files) {
      const src = readFileSync(file, "utf8")
      for (const re of HEADING_REGEXES) {
        const m = src.match(re)
        if (m) {
          const rel = relative(PAGES_AGENT_STUDIO_DIR, file)
          const lineNumber = src.slice(0, m.index ?? 0).split("\n").length
          offenders.push(`${rel}:${lineNumber} → ${m[0].slice(0, 120).replace(/\s+/g, " ")}`)
          break
        }
      }
    }

    if (offenders.length > 0) {
      const list = offenders.map((o) => `  • ${o}`).join("\n")
      throw new Error(
        [
          "Cabeçalho inline detectado em pages-agent-studio/ — isso reintroduz o drift",
          "padronizado pelas Tasks #1048/#1049. Substitua por <TabSectionHeader />:",
          "",
          '  import { TabSectionHeader } from "@/components/pages-agent-studio/TabSectionHeader"',
          "  ...",
          "  <TabSectionHeader title={...} subtitle={...} icon={...} count={...} actions={...} />",
          "",
          "Arquivos com cabeçalho inline (h2|h3 + font-semibold + text-lia-text-primary):",
          list,
        ].join("\n"),
      )
    }
  })
})
