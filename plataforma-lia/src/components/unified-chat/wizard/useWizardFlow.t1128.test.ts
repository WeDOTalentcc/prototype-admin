/**
 * Task #1128 — sentinela arquitetural do hook `useWizardFlow`.
 *
 * Cenários:
 *   S1 — `useWizardFlow.ts` NÃO contém leituras/escritas em localStorage
 *        nem helpers de persistência (`loadPersistedState`, `persistState`).
 *        Esses símbolos foram removidos junto com a abolição do cache
 *        client-side; reintroduzí-los ressuscita o bug do screenshot
 *        (Nova conversa não cancela o wizard porque o reducer rehidrata
 *        de disco no próximo mount).
 *   S2 — `purgeLegacyWizardStorage` existe e remove TODAS as chaves com
 *        prefixo `lia-wizard-state` — o frontend precisa do purge para
 *        usuários que instalaram a app antes do rollout.
 *   S3 — `fetchWizardSessionState` e `resetWizardSession` chamam o proxy
 *        canônico `/api/backend-proxy/lia/job-wizard/session/<id>`. Se o
 *        path mudar sem atualizar essa expectativa, a sentinela quebra.
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import fs from "node:fs"
import path from "node:path"

import {
  fetchWizardSessionState,
  resetWizardSession,
  purgeLegacyWizardStorage,
  LEGACY_WIZARD_STORAGE_PREFIX,
} from "./useWizardSessionApi"

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const _typecheck_imports = [
  fetchWizardSessionState,
  resetWizardSession,
  purgeLegacyWizardStorage,
  LEGACY_WIZARD_STORAGE_PREFIX,
]

const WIZARD_FLOW_PATH = path.join(__dirname, "useWizardFlow.ts")
const UNIFIED_CHAT_DIR = path.resolve(__dirname, "..")
const SRC_ROOT = path.resolve(__dirname, "..", "..", "..")

/** Recursively list .ts/.tsx files under `dir`, skipping node_modules + tests. */
function listSourceFiles(dir: string, acc: string[] = []): string[] {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === "__tests__") continue
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      listSourceFiles(full, acc)
      continue
    }
    if (!/\.(ts|tsx)$/.test(entry.name)) continue
    if (/\.(test|spec)\.(ts|tsx)$/.test(entry.name)) continue
    acc.push(full)
  }
  return acc
}

describe("Task #1128 — wizard session reset canonical contract", () => {
  // ---------------- S1 ----------------
  it("S1 — useWizardFlow.ts não contém persistência localStorage", () => {
    const src = fs.readFileSync(WIZARD_FLOW_PATH, "utf-8")
    const forbidden = [
      "loadPersistedState",
      "persistState",
      "localStorage.setItem",
      "localStorage.getItem",
      "localStorage.removeItem",
    ]
    for (const token of forbidden) {
      // Comentários explicativos sobre a remoção podem mencionar o nome
      // antigo — só filtramos linhas que NÃO começam com `//` ou `*`.
      const offending = src
        .split("\n")
        .filter((line) => {
          const trimmed = line.trim()
          if (trimmed.startsWith("//") || trimmed.startsWith("*")) return false
          return line.includes(token)
        })
      expect(
        offending,
        `useWizardFlow.ts contém '${token}' fora de comentários — Task #1128 aboliu a persistência client-side. Offending lines:\n${offending.join("\n")}`,
      ).toEqual([])
    }
  })

  // ---------------- S1b — repo-wide guard ----------------
  it("S1b — nenhum arquivo de produção persiste em `lia-wizard-state-*` (exceto purge canônico)", () => {
    // Apenas dois arquivos podem MENCIONAR a chave legada:
    //   - useWizardSessionApi.ts  → exporta LEGACY_WIZARD_STORAGE_PREFIX + purge
    //   - useWizardFlow.ts        → mantém helper `getWizardStorageKey` p/ legado
    //   - UnifiedChat.tsx         → comentário explicando o purge no useEffect
    // Qualquer outro arquivo de produção que toque a chave reabre o
    // bug do screenshot. A sentinela falha cedo apontando o ofensor.
    const ALLOWED_FILES = new Set([
      path.join(__dirname, "useWizardSessionApi.ts"),
      path.join(__dirname, "useWizardFlow.ts"),
      path.resolve(__dirname, "..", "UnifiedChat.tsx"),
    ])
    const offenders: { file: string; line: number; content: string }[] = []
    for (const file of listSourceFiles(SRC_ROOT)) {
      if (ALLOWED_FILES.has(file)) continue
      const src = fs.readFileSync(file, "utf-8")
      if (!src.includes("lia-wizard-state")) continue
      src.split("\n").forEach((line, idx) => {
        if (line.includes("lia-wizard-state")) {
          offenders.push({ file, line: idx + 1, content: line.trim() })
        }
      })
    }
    expect(
      offenders,
      `Task #1128: arquivos de produção não-autorizados referenciam 'lia-wizard-state'. ` +
        `Use o purge canônico em useWizardSessionApi.ts. Offenders:\n` +
        offenders.map((o) => `  ${o.file}:${o.line} → ${o.content}`).join("\n"),
    ).toEqual([])
  })

  // ---------------- S1c — slash wiring ----------------
  it("S1c — slash `/nova-conversa` continua roteado para o handler canônico do UnifiedChat", () => {
    // Cadeia canônica:
    //   slash-commands.ts: EXECUTE_ONLY_COMMAND_IDS inclui "nova-conversa"
    //     + entrada com id="nova-conversa" e primary="/nova-conversa"
    //   useSlashCommands.ts: ao selecionar id=="nova-conversa" chama
    //     onExecuteCommand("nova-conversa")
    //   UnifiedChat.tsx: handler do execute liga em handleNewChat
    // Quebrar qualquer elo desencadeia o bug "/nova-conversa não cancela
    // wizard". A sentinela faz scan textual leve (sem AST) para falhar
    // cedo quando alguém renomear sem atualizar todos os pontos.
    const slashCommandsSrc = fs.readFileSync(
      path.join(UNIFIED_CHAT_DIR, "slash-commands.ts"),
      "utf-8",
    )
    expect(slashCommandsSrc).toMatch(
      /EXECUTE_ONLY_COMMAND_IDS[^=]*=\s*\[[^\]]*"nova-conversa"/,
    )
    expect(slashCommandsSrc).toMatch(/id:\s*"nova-conversa"/)
    expect(slashCommandsSrc).toMatch(/primary:\s*"\/nova-conversa"/)

    const useSlashSrc = fs.readFileSync(
      path.join(UNIFIED_CHAT_DIR, "useSlashCommands.ts"),
      "utf-8",
    )
    expect(useSlashSrc).toMatch(
      /item\.id\s*===\s*"nova-conversa"[\s\S]{0,160}onExecuteCommand\(\s*"nova-conversa"\s*\)/,
    )

    const unifiedSrc = fs.readFileSync(
      path.join(UNIFIED_CHAT_DIR, "UnifiedChat.tsx"),
      "utf-8",
    )
    // O handler deve existir como callback que (a) chama resetWizardSession
    // (direta ou indiretamente via resetCurrentWizardSession) e (b) é
    // referenciado no ponto onde o `onExecuteCommand` chega no input.
    expect(unifiedSrc).toMatch(/const\s+handleNewChat\s*=\s*useCallback\(/)
    expect(unifiedSrc).toMatch(/handleCancelWizard|onCancelWizard/)
    // O execute branch precisa cair em handleNewChat — qualquer mudança
    // tem que atualizar essa expectativa de forma explícita.
    expect(unifiedSrc).toMatch(
      /case\s+"nova-conversa"|commandId\s*===\s*"nova-conversa"|"nova-conversa"\s*:\s*[^,;{]*handleNewChat/,
    )
  })

  // ---------------- S2 ----------------
  describe("S2 — purgeLegacyWizardStorage", () => {
    beforeEach(() => {
      window.localStorage.clear()
    })

    it("remove TODAS as chaves com prefixo lia-wizard-state", () => {
      window.localStorage.setItem(
        `${LEGACY_WIZARD_STORAGE_PREFIX}-user-a`,
        JSON.stringify({ active: true }),
      )
      window.localStorage.setItem(
        `${LEGACY_WIZARD_STORAGE_PREFIX}-user-b`,
        JSON.stringify({ active: true }),
      )
      window.localStorage.setItem("unrelated", "keep-me")

      const removed = purgeLegacyWizardStorage()

      expect(removed).toBe(2)
      expect(window.localStorage.getItem(`${LEGACY_WIZARD_STORAGE_PREFIX}-user-a`)).toBeNull()
      expect(window.localStorage.getItem(`${LEGACY_WIZARD_STORAGE_PREFIX}-user-b`)).toBeNull()
      expect(window.localStorage.getItem("unrelated")).toBe("keep-me")
    })

    it("é idempotente (segunda chamada não remove nada)", () => {
      window.localStorage.setItem(`${LEGACY_WIZARD_STORAGE_PREFIX}-x`, "1")
      expect(purgeLegacyWizardStorage()).toBe(1)
      expect(purgeLegacyWizardStorage()).toBe(0)
    })
  })

  // ---------------- S3 ----------------
  describe("S3 — backend proxy endpoints", () => {
    it("fetchWizardSessionState chama GET /api/backend-proxy/lia/job-wizard/session/<id>", async () => {
      const fakeFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          session_id: "sess-1",
          thread_id: "wiz-abc-sess-1",
          active: false,
          current_stage: null,
          completeness: 0,
          requires_approval: false,
          stage_data: {},
          degraded_stages: {},
          conversation_message_count: 0,
        }),
      }) as unknown as typeof fetch

      await fetchWizardSessionState("sess-1", fakeFetch)
      expect(fakeFetch).toHaveBeenCalledWith(
        "/api/backend-proxy/lia/job-wizard/session/sess-1",
        expect.objectContaining({ method: "GET", credentials: "include" }),
      )
    })

    it("resetWizardSession chama DELETE no mesmo endpoint", async () => {
      const fakeFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          session_id: "sess-2",
          thread_id: "wiz-abc-sess-2",
          was_active: true,
        }),
      }) as unknown as typeof fetch

      const result = await resetWizardSession("sess-2", fakeFetch)
      expect(fakeFetch).toHaveBeenCalledWith(
        "/api/backend-proxy/lia/job-wizard/session/sess-2",
        expect.objectContaining({ method: "DELETE", credentials: "include" }),
      )
      expect(result.was_active).toBe(true)
    })

    it("resetWizardSession lança em 404 — fail-loud (NÃO trata como no-op)", async () => {
      // Idempotência vem do backend (200 + was_active=false), NÃO do
      // cliente. Um 404 indica deploy/tenant mismatch e PRECISA chegar
      // ao caller para toast + preservar o stepper.
      const fakeFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({}),
      }) as unknown as typeof fetch

      await expect(resetWizardSession("sess-missing", fakeFetch)).rejects.toThrow(
        /DELETE wizard session failed: 404/,
      )
    })

    it("resetWizardSession lança em 5xx — falha NUNCA é silenciada", async () => {
      const fakeFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: "boom" }),
      }) as unknown as typeof fetch

      await expect(resetWizardSession("sess-x", fakeFetch)).rejects.toThrow(
        /DELETE wizard session failed: 500/,
      )
    })

    it("fetchWizardSessionState lança em 404 — fail-loud (servidor canônico devolve 200+active=false)", async () => {
      const fakeFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({}),
      }) as unknown as typeof fetch

      await expect(fetchWizardSessionState("sess-missing", fakeFetch)).rejects.toThrow(
        /GET wizard session failed: 404/,
      )
    })
  })
})
