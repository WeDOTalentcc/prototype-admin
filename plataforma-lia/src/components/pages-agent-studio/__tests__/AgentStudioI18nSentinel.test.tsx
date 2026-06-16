/**
 * Sentinela i18n — pages-agent-studio
 *
 * Origem: bug observado em 2026-05-13 onde `DigitalTwinEmptyState`
 * (renderizado quando `twins.length === 0`) chamava
 * `useTranslations("agents.studio.twins.emptyState")` mas o bloco
 * `emptyState` nunca foi adicionado a `messages/pt-BR.json` nem a
 * `messages/en.json` — Task #1044 só adicionou `headerTitle/headerDesc`
 * e `onboarding.*`. next-intl é fail-LOUD: gerou
 * `MISSING_MESSAGE: Could not resolve 'agents.studio.twins.emptyState'`
 * no console e quebrou a UI assim que um tenant sem twins abria a aba.
 *
 * Esta sentinela varre TODOS os `.tsx` sob `pages-agent-studio/`
 * (excluindo testes/snapshots/stories), extrai cada par
 * `useTranslations("<NS>")` + `t("<KEY>")` da mesma função, e falha se
 * qualquer `<NS>.<KEY>` não existir em `messages/pt-BR.json` ou
 * `messages/en.json`. Cobre os 16 callsites de `t(...)` do Agent Studio
 * de uma só vez — incluindo `agents.studio.twins.emptyState.*`,
 * `agents.studio.twins.createModal.*`, `agents.digitalTwin.*`, etc.
 *
 * Ignora: chaves dinâmicas (`t(variable)`, `t(\`literal-${x}\`)`) —
 * apenas chaves string literais simples são validadas.
 */
import { describe, expect, it } from "vitest"
import { readdirSync, readFileSync, statSync } from "node:fs"
import { join, resolve } from "node:path"

const STUDIO_DIR = resolve(__dirname, "..")
const MESSAGES_DIR = resolve(__dirname, "../../../../messages")
const LOCALES = ["pt-BR", "en"] as const

function listTsxFiles(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) {
      if (entry === "__tests__" || entry === "__snapshots__") continue
      out.push(...listTsxFiles(full))
    } else if (
      entry.endsWith(".tsx") &&
      !entry.endsWith(".test.tsx") &&
      !entry.endsWith(".stories.tsx")
    ) {
      out.push(full)
    }
  }
  return out
}

function loadMessages(locale: string): Record<string, unknown> {
  const path = join(MESSAGES_DIR, `${locale}.json`)
  return JSON.parse(readFileSync(path, "utf-8"))
}

function resolveKey(
  messages: Record<string, unknown>,
  dottedPath: string,
): unknown {
  const parts = dottedPath.split(".")
  let node: unknown = messages
  for (const p of parts) {
    if (typeof node !== "object" || node === null) return undefined
    node = (node as Record<string, unknown>)[p]
    if (node === undefined) return undefined
  }
  return node
}

/**
 * Extrai pares (namespace, key) de um arquivo .tsx.
 *
 * Heurística:
 *  - Cada `useTranslations("<NS>")` define o namespace ativo a partir
 *    daquela linha até a próxima `useTranslations(...)` ou `function/const ... =>`.
 *  - Para cada `t("<KEY>")` (ou `tOnboarding("<KEY>")`, etc.) dentro do
 *    escopo daquele namespace, registra `<NS>.<KEY>`.
 *
 * Como o regex de escopo é frouxo, a sentinela pode gerar falsos
 * positivos em arquivos com múltiplos namespaces/funções aninhadas.
 * Para evitar isso, cada arquivo é analisado por blocos delimitados
 * por `function ` / `const ... = (` no nível raiz — boa o suficiente
 * para o estilo de código do Agent Studio (componentes top-level).
 */
type ExtractedKey = {
  file: string
  line: number
  namespace: string
  key: string
  fullPath: string
}

function extractKeysFromFile(filePath: string): ExtractedKey[] {
  const src = readFileSync(filePath, "utf-8")
  const lines = src.split("\n")
  const out: ExtractedKey[] = []

  // Map from variable name (e.g. "t", "tOnboarding") → namespace, scoped per top-level fn.
  // We split the file by top-level `export function` / `function ` / `const ... = ` boundaries.
  type FnBlock = { startLine: number; endLine: number; body: string[] }
  const blocks: FnBlock[] = []
  let current: FnBlock | null = null
  let depth = 0
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const isFnStart =
      /^\s*(export\s+)?(async\s+)?function\s+\w+/.test(line) ||
      /^\s*(export\s+)?const\s+\w+\s*[:=].*=>/.test(line) ||
      /^\s*(export\s+)?const\s+\w+\s*=\s*(async\s+)?\(.*\)\s*=>/.test(line)
    if (isFnStart && depth === 0) {
      if (current) {
        current.endLine = i - 1
        blocks.push(current)
      }
      current = { startLine: i, endLine: lines.length - 1, body: [] }
    }
    if (current) current.body.push(line)
    // Naive brace tracking only for module-level depth resync (good enough)
    for (const ch of line) {
      if (ch === "{") depth++
      else if (ch === "}") depth = Math.max(0, depth - 1)
    }
  }
  if (current) blocks.push(current)
  if (blocks.length === 0) {
    blocks.push({ startLine: 0, endLine: lines.length - 1, body: lines })
  }

  for (const block of blocks) {
    const varToNs = new Map<string, string>()
    for (let i = 0; i < block.body.length; i++) {
      const line = block.body[i]
      // Match: const t = useTranslations("foo.bar")  OR  const tOnboarding = useTranslations("foo.bar")
      const useT = line.match(
        /\bconst\s+(\w+)\s*=\s*useTranslations\(\s*["'`]([^"'`]+)["'`]\s*\)/,
      )
      if (useT) {
        varToNs.set(useT[1], useT[2])
        continue
      }
      // Match every t("…") / tFoo("…") on this line.
      // We REQUIRE that the closing quote is followed (after optional whitespace)
      // by `)` or `,` — that means the argument was a pure string literal, NOT
      // a concatenation like t('categories.' + x) which would partially match
      // and produce false positives. We also require that the function name is
      // NOT preceded by `.` (so we skip `t.rich(...)`, `t.markup(...)` —
      // these have different signatures and the sentinel doesn't track them).
      const callRe = /(?<![.\w])(\w+)\(\s*(["'`])([^"'`]+)\2\s*(?=[,)])/g
      let m: RegExpExecArray | null
      while ((m = callRe.exec(line)) !== null) {
        const fnName = m[1]
        const key = m[3]
        const ns = varToNs.get(fnName)
        if (!ns) continue
        // Skip dotted keys with interpolation markers (defense in depth)
        if (key.includes("${") || key.includes("{{")) continue
        out.push({
          file: filePath,
          line: block.startLine + i + 1,
          namespace: ns,
          key,
          fullPath: `${ns}.${key}`,
        })
      }
    }
  }
  return out
}

describe("Agent Studio — sentinela i18n (pages-agent-studio/**)", () => {
  const files = listTsxFiles(STUDIO_DIR)
  const allKeys = files.flatMap(extractKeysFromFile)

  it("encontrou ao menos 1 chave i18n para validar (sanity)", () => {
    expect(allKeys.length).toBeGreaterThan(0)
  })

  for (const locale of LOCALES) {
    it(`messages/${locale}.json resolve TODAS as chaves t(\"…\") usadas no Agent Studio`, () => {
      const messages = loadMessages(locale)
      const missing: string[] = []
      for (const k of allKeys) {
        const value = resolveKey(messages, k.fullPath)
        if (typeof value !== "string") {
          const rel = k.file.replace(`${resolve(__dirname, "../../../..")}/`, "")
          missing.push(`  ${k.fullPath}  ← ${rel}:${k.line}`)
        }
      }
      if (missing.length > 0) {
        const msg = [
          `${missing.length} chave(s) i18n ausente(s) em messages/${locale}.json:`,
          ...missing,
          "",
          "Adicione cada chave em messages/pt-BR.json E messages/en.json (espelhando a estrutura).",
          "Origem desta sentinela: bug 2026-05-13 (DigitalTwinEmptyState quebrou em produção porque",
          "Task #1044 esqueceu o bloco agents.studio.twins.emptyState).",
        ].join("\n")
        throw new Error(msg)
      }
    })
  }

  it("DigitalTwinEmptyState (regression specífica do bug 2026-05-13) tem todas as 4 chaves", () => {
    for (const locale of LOCALES) {
      const messages = loadMessages(locale)
      for (const key of ["title", "description", "createFirst", "noExperience"]) {
        const path = `agents.studio.twins.emptyState.${key}`
        const v = resolveKey(messages, path)
        expect(typeof v, `${path} em ${locale}`).toBe("string")
        expect((v as string).length, `${path} em ${locale} não pode ser vazio`).toBeGreaterThan(0)
      }
    }
  })
})
