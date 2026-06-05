// @vitest-environment jsdom
/**
 * FE-1 (wizard panel SSE parity) — Bridge transport→UI sensor.
 *
 * `useChatTransport` must dispatch a `lia:wizard-stage-payload` CustomEvent from
 * the SSE/WS transport at parity with the WS hook (useChatSocket.ts) and the
 * REST hook (useChatMessages.ts), in TWO shapes shipped by the backend
 * (commit 54f2d48d):
 *   1. a top-level `wizard_stage` frame (chat-page path); and
 *   2. nested as `ws_stage_payload` on the structured `message` frame (bubble).
 *
 * The dynamic panel listener (`lia-float-context`) only reacts to
 * `lia:wizard-stage-payload`, so without this bridge the wizard side-panel never
 * opens over SSE.
 *
 * Fix se falhar:
 *   Verificar `src/hooks/chat/useChatTransport.ts`:
 *   - exporta `maybeDispatchWizardStage`
 *   - dispatch usa o detail shape canonico {type:"wizard_stage", thread_id,
 *     stage, data, completeness, requires_approval}
 *   - `handleParsedEvent` chama `maybeDispatchWizardStage(event)`
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest"

import {
  maybeDispatchWizardStage,
  type TransportEvent,
} from "../useChatTransport"

const SRC = readFileSync(join(__dirname, "..", "useChatTransport.ts"), "utf8")

describe("FE-1 — transport→UI wizard bridge (lia:wizard-stage-payload)", () => {
  let listener: ReturnType<typeof vi.fn>

  beforeEach(() => {
    listener = vi.fn()
    window.addEventListener("lia:wizard-stage-payload", listener)
  })
  afterEach(() => {
    window.removeEventListener("lia:wizard-stage-payload", listener)
  })

  test("dispatches from the top-level wizard_stage frame (chat-page path)", () => {
    maybeDispatchWizardStage({
      type: "wizard_stage",
      thread_id: "t-chatpage-1",
      stage: "jd_enrichment",
      data: { foo: "bar" },
      completeness: 42,
      requires_approval: true,
    } as TransportEvent)
    expect(listener).toHaveBeenCalledTimes(1)
    const detail = (listener.mock.calls[0][0] as CustomEvent).detail
    expect(detail.type).toBe("wizard_stage")
    expect(detail.thread_id).toBe("t-chatpage-1")
    expect(detail.stage).toBe("jd_enrichment")
    expect(detail.data).toEqual({ foo: "bar" })
    expect(detail.completeness).toBe(42)
    expect(detail.requires_approval).toBe(true)
  })

  test("dispatches from message.ws_stage_payload (bubble path)", () => {
    maybeDispatchWizardStage({
      type: "message",
      content: "ok",
      ws_stage_payload: {
        thread_id: "t-bubble-1",
        stage: "intake",
        data: { a: 1 },
        completeness: 10,
        requires_approval: false,
      },
    } as unknown as TransportEvent)
    expect(listener).toHaveBeenCalledTimes(1)
    const detail = (listener.mock.calls[0][0] as CustomEvent).detail
    expect(detail.stage).toBe("intake")
    expect(detail.thread_id).toBe("t-bubble-1")
    expect(detail.requires_approval).toBe(false)
  })

  test("does NOT dispatch for unrelated frames", () => {
    maybeDispatchWizardStage({ type: "token", content: "x" } as TransportEvent)
    maybeDispatchWizardStage({ type: "message", content: "no payload" })
    expect(listener).not.toHaveBeenCalled()
  })

  test("does NOT dispatch when stage is missing/empty", () => {
    maybeDispatchWizardStage({
      type: "wizard_stage",
      thread_id: "t-empty",
    } as TransportEvent)
    maybeDispatchWizardStage({
      type: "wizard_stage",
      thread_id: "t-empty",
      stage: "",
    } as unknown as TransportEvent)
    expect(listener).not.toHaveBeenCalled()
  })

  test("dedups the same logical payload across both shapes", () => {
    const payload = {
      thread_id: "t-dedup",
      stage: "salary",
      data: {},
      completeness: 55,
      requires_approval: false,
    }
    // top-level frame
    maybeDispatchWizardStage({
      type: "wizard_stage",
      ...payload,
    } as TransportEvent)
    // same logical payload nested in a message frame — must NOT re-fire
    maybeDispatchWizardStage({
      type: "message",
      ws_stage_payload: payload,
    } as unknown as TransportEvent)
    expect(listener).toHaveBeenCalledTimes(1)
  })

  // Live chat-page SSE shape — agent_chat_sse.py emits the wizard ONLY as a
  // `panel_update` frame (panel_type "wizard_stage"); panel_title carries the
  // stage string and panel_data carries the inner `data` dict. Without this
  // branch the wizard side-panel never opens on the full chat-page SSE path.
  test("dispatches from a panel_update frame (chat-page SSE path)", () => {
    maybeDispatchWizardStage({
      type: "panel_update",
      panel_type: "wizard_stage",
      panel_title: "competencias",
      panel_data: { questions: ["q1"], dropped_questions: [] },
      action: "open",
    } as unknown as TransportEvent)
    expect(listener).toHaveBeenCalledTimes(1)
    const detail = (listener.mock.calls[0][0] as CustomEvent).detail
    expect(detail.type).toBe("wizard_stage")
    expect(detail.stage).toBe("competencias")
    expect(detail.data).toEqual({ questions: ["q1"], dropped_questions: [] })
  })

  test("does NOT dispatch for a panel_update of a non-wizard panel_type", () => {
    maybeDispatchWizardStage({
      type: "panel_update",
      panel_type: "candidate_detail",
      panel_title: "Some Candidate",
      panel_data: { id: 1 },
      action: "open",
    } as unknown as TransportEvent)
    expect(listener).not.toHaveBeenCalled()
  })

  // Structural guard — handleParsedEvent must wire the bridge.
  test("handleParsedEvent calls maybeDispatchWizardStage", () => {
    expect(SRC).toMatch(/maybeDispatchWizardStage\(event\)/)
  })

  // Fix 2026-06-05 (painel congelado): dois turnos do MESMO stage com data
  // DIFERENTE precisam re-despachar para o painel atualizar. A chave de dedup
  // passou a ser sensivel ao conteudo (hash de data); antes era
  // thread:stage:completeness, constante dentro do stage (completeness e
  // por-stage), entao o painel congelava no 1o payload (intake "Aguardando").
  test("re-dispatches same stage when data changes (intake gathering fields)", () => {
    const base = {
      type: "wizard_stage",
      thread_id: "t-fresh",
      stage: "intake",
      completeness: 0,
      requires_approval: true,
    }
    maybeDispatchWizardStage({
      ...base,
      data: { message: "ok", parsed_title: "Diretor" },
    } as unknown as TransportEvent)
    maybeDispatchWizardStage({
      ...base,
      data: { message: "ok", parsed_title: "Diretor", parsed_seniority: "C-level" },
    } as unknown as TransportEvent)
    expect(listener).toHaveBeenCalledTimes(2)
    const last = (listener.mock.calls[1][0] as CustomEvent).detail
    expect(last.data.parsed_seniority).toBe("C-level")
  })

  test("still dedups byte-identical data on the same stage", () => {
    const f = {
      type: "wizard_stage",
      thread_id: "t-same",
      stage: "intake",
      completeness: 0,
      requires_approval: true,
      data: { message: "ok", parsed_title: "X" },
    }
    maybeDispatchWizardStage(f as unknown as TransportEvent)
    maybeDispatchWizardStage({
      ...f,
      data: { message: "ok", parsed_title: "X" },
    } as unknown as TransportEvent)
    expect(listener).toHaveBeenCalledTimes(1)
  })
})
