// @vitest-environment jsdom
/**
 * PR6 (Task #1006) — Bridge IA→UI sensor.
 *
 * `useChatTransport.handleParsedEvent` must intercept `message` frames whose
 * `tool_results` array contains a successful canonical settings save tool and
 * dispatch a `lia:settings-updated` CustomEvent with `detail.origin = "agent"`.
 *
 * Behavioral guards (real dispatch via JSDOM) + structural guards (regex over
 * the source) — defense-in-depth.
 *
 * Fix se falhar:
 *   Verificar `src/hooks/chat/useChatTransport.ts`:
 *   - exporta `maybeDispatchSettingsUpdated`
 *   - whitelist `SETTINGS_PERSIST_TOOLS` cobre os 5 saves canônicos
 *   - dispatch acontece com `detail.origin === "agent"`
 *   - `handleParsedEvent` chama `maybeDispatchSettingsUpdated(event)` antes do switch
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest"

import {
  SETTINGS_PERSIST_TOOLS,
  maybeDispatchSettingsUpdated,
  type TransportEvent,
} from "../useChatTransport"

const SRC = readFileSync(
  join(__dirname, "..", "useChatTransport.ts"),
  "utf8",
)

// Canonical source of truth — imported from the production module to prevent
// whitelist drift between tests and runtime (PR6 review feedback).
const CANONICAL_TOOLS = Array.from(SETTINGS_PERSIST_TOOLS) as readonly string[]

describe("PR6 FE — IA→UI bridge (lia:settings-updated)", () => {
  let listener: ReturnType<typeof vi.fn>

  beforeEach(() => {
    listener = vi.fn()
    window.addEventListener("lia:settings-updated", listener)
  })
  afterEach(() => {
    window.removeEventListener("lia:settings-updated", listener)
  })

  test.each(CANONICAL_TOOLS)(
    "dispatches CustomEvent for canonical save tool: %s",
    (toolName) => {
      const event: TransportEvent = {
        type: "message",
        content: "ok",
        tool_results: [
          { tool_name: toolName, success: true, section: "profile", field: "name" },
        ],
      }
      maybeDispatchSettingsUpdated(event)
      expect(listener).toHaveBeenCalledTimes(1)
      const detail = (listener.mock.calls[0][0] as CustomEvent).detail
      expect(detail.origin).toBe("agent")
      expect(detail.tool_name).toBe(toolName)
      expect(typeof detail.section).toBe("string")
      expect(typeof detail.ts).toBe("number")
    },
  )

  test("does NOT dispatch when frame is not a message", () => {
    maybeDispatchSettingsUpdated({
      type: "thinking",
      tool_results: [{ tool_name: "save_company_field", success: true }],
    } as TransportEvent)
    expect(listener).not.toHaveBeenCalled()
  })

  test("does NOT dispatch when tool_results is missing/empty", () => {
    maybeDispatchSettingsUpdated({ type: "message", content: "hi" })
    maybeDispatchSettingsUpdated({ type: "message", tool_results: [] })
    expect(listener).not.toHaveBeenCalled()
  })

  test("does NOT dispatch for non-whitelisted tools", () => {
    maybeDispatchSettingsUpdated({
      type: "message",
      tool_results: [{ tool_name: "search_candidates", success: true }],
    })
    expect(listener).not.toHaveBeenCalled()
  })

  test("does NOT dispatch when tool failed (success=false)", () => {
    maybeDispatchSettingsUpdated({
      type: "message",
      tool_results: [
        { tool_name: "save_company_field", success: false, section: "profile" },
      ],
    })
    expect(listener).not.toHaveBeenCalled()
  })

  test("dispatches one event per successful canonical tool in the array", () => {
    maybeDispatchSettingsUpdated({
      type: "message",
      tool_results: [
        { tool_name: "save_company_field", success: true, section: "profile" },
        { tool_name: "search_candidates", success: true },
        { tool_name: "save_hiring_policy", success: true },
      ],
    })
    expect(listener).toHaveBeenCalledTimes(2)
  })

  test("falls back to TOOL_TO_SECTION when section is absent", () => {
    maybeDispatchSettingsUpdated({
      type: "message",
      tool_results: [{ tool_name: "import_workforce_plan", success: true }],
    })
    const detail = (listener.mock.calls[0][0] as CustomEvent).detail
    expect(detail.section).toBe("workforce")
  })

  // Structural guards — protect against regression even if the runtime helper
  // is refactored.
  test("Structural Guard: handleParsedEvent calls maybeDispatchSettingsUpdated", () => {
    expect(SRC).toMatch(
      /handleParsedEvent\s*=\s*useCallback[\s\S]+?maybeDispatchSettingsUpdated\(event\)/,
    )
  })

  test("Structural Guard: SETTINGS_PERSIST_TOOLS whitelist covers all 5 canonical saves", () => {
    for (const tool of CANONICAL_TOOLS) {
      expect(SRC).toContain(`"${tool}"`)
    }
  })

  test("Structural Guard: dispatch uses origin=\"agent\"", () => {
    expect(SRC).toMatch(/origin:\s*"agent"/)
  })
})
