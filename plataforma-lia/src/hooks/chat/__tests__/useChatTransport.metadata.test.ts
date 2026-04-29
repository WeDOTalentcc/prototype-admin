/**
 * Sensor: useChatTransport.sendMessage forwards metadata into the WS frame.
 *
 * Audit context (2026-04-29 wizard-domain-hint-leak):
 *   The WS transport hook serializes `{ type, content, context, domain }`
 *   on `ws.send`. Without metadata propagation, Rail A hints set by
 *   LiaFloatContext (e.g., `domain_hint: "wizard"` while the job_creation
 *   panel is active) never reach the backend `try_hint_route()` Tier -1.
 *
 * Fix: sendMessage accepts a 4th optional `metadata` arg. When provided, it
 *   is merged into `context.metadata` (caller-provided context.metadata wins,
 *   idempotent) AND mirrored at the WS frame top-level so the backend
 *   handler can promote it as a fallback (defense in depth).
 *
 * Guards (structural — regex over the source):
 *   1. sendMessage type signature exposes the 4th `metadata?` parameter.
 *   2. The runtime sendMessage closure accepts the 4th metadata arg.
 *   3. metadata is embedded into context.metadata when caller did not.
 *   4. Top-level frame.metadata is set when metadata is provided
 *      (defense-in-depth fallback for the backend).
 *
 * Fix se falhar:
 *   Verificar `src/hooks/chat/useChatTransport.ts` — UseChatTransportResult
 *   interface deve listar `metadata?` na assinatura de sendMessage; o
 *   useCallback de sendMessage deve receber o 4th arg, mesclar em
 *   context.metadata sem sobrescrever (idempotente) e enviar também em
 *   top-level frame.metadata.
 *
 * Skill canônica: harness-engineering [sensor computacional].
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const SRC = readFileSync(
  join(__dirname, "..", "useChatTransport.ts"),
  "utf8",
)

describe("PR-A FE — WS transport metadata propagation", () => {
  test("Guard 1: interface signature exposes optional metadata 4th arg", () => {
    // Type signature inside UseChatTransportResult.
    expect(SRC).toMatch(/sendMessage\s*:\s*\([^)]*metadata\?\s*:\s*Record<string,\s*unknown>/s)
  })

  test("Guard 2: runtime sendMessage closure accepts metadata arg", () => {
    const sendBlock = SRC.split("const sendMessage = useCallback")[1]
    expect(sendBlock).toBeDefined()
    expect(sendBlock).toMatch(/metadata\?\s*:\s*Record<string,\s*unknown>/)
  })

  test("Guard 3: metadata is embedded into context.metadata when caller didn't", () => {
    const sendBlock = SRC.split("const sendMessage = useCallback")[1]
    // Idempotent merge: must not overwrite caller's context.metadata.
    expect(sendBlock).toMatch(/!\s*context\.metadata/)
    // Spread context plus add metadata.
    expect(sendBlock).toMatch(/\{\s*\.\.\.context\s*,\s*metadata\s*\}/)
  })

  test("Guard 4: top-level frame.metadata mirrored when metadata provided", () => {
    const sendBlock = SRC.split("const sendMessage = useCallback")[1]
    // Defense in depth: WS handler reads msg.get('metadata') as fallback.
    expect(sendBlock).toMatch(/frame\.metadata\s*=\s*metadata/)
  })

  test("Guard 5: ws.send still emits a JSON-stringified frame", () => {
    const sendBlock = SRC.split("const sendMessage = useCallback")[1]
    expect(sendBlock).toMatch(/ws\.send\(JSON\.stringify\(frame\)\)/)
  })
})
