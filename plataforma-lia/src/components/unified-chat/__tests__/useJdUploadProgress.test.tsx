import { describe, expect, it, beforeEach, afterEach, vi } from "vitest"
import { act, renderHook } from "@testing-library/react"
import { useJdUploadProgress } from "../useJdUploadProgress"
import type { BackgroundTaskEvent } from "@/hooks/chat/lia-chat-connection-types"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function buildFile(name = "vaga.pdf"): File {
  return new File([new Uint8Array([1, 2, 3, 4])], name, { type: "application/pdf" })
}

function fireConfirmed(file: File) {
  window.dispatchEvent(
    new CustomEvent("lia:file-upload-confirmed", {
      detail: { file, type: "jd", consentAcknowledged: true },
    }),
  )
}

interface Harness {
  appendChatMessage: ReturnType<typeof vi.fn>
  seedBackgroundTask: ReturnType<typeof vi.fn>
  clearBackgroundTask: ReturnType<typeof vi.fn>
  /** Mutated by tests + drives the rerender to simulate WS events arriving. */
  setTasks: (next: BackgroundTaskEvent[]) => void
  rerender: () => void
}

function setup(): Harness {
  const appendChatMessage = vi.fn()
  const seedBackgroundTask = vi.fn()
  const clearBackgroundTask = vi.fn()
  let tasks: BackgroundTaskEvent[] = []

  const { rerender } = renderHook(
    ({ chatBackgroundTasks }) =>
      useJdUploadProgress({
        chatSessionId: "lia-session-test",
        chatBackgroundTasks,
        seedBackgroundTask,
        clearBackgroundTask,
        appendChatMessage,
      }),
    { initialProps: { chatBackgroundTasks: tasks } },
  )

  return {
    appendChatMessage,
    seedBackgroundTask,
    clearBackgroundTask,
    setTasks: (next) => {
      tasks = next
      rerender({ chatBackgroundTasks: tasks })
    },
    rerender: () => rerender({ chatBackgroundTasks: tasks }),
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

describe("useJdUploadProgress", () => {
  let fetchMock: ReturnType<typeof vi.fn>
  let prefillSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn()
    // jsdom exposes a no-op fetch; we override per test.
    Object.defineProperty(globalThis, "fetch", { value: fetchMock, configurable: true })
    prefillSpy = vi.fn()
    window.addEventListener("lia:prefill-message", prefillSpy as EventListener)
  })

  afterEach(() => {
    window.removeEventListener("lia:prefill-message", prefillSpy as EventListener)
    vi.clearAllMocks()
  })

  it("uploads a JD file, seeds queued task, then triggers wizard prefill on completed", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ success: true, task_id: "task-abc", status: "queued", message: "Upload aceito." }),
        { status: 202, headers: { "content-type": "application/json" } },
      ),
    )

    const h = setup()

    await act(async () => {
      fireConfirmed(buildFile("vaga-backend.pdf"))
      // Let the awaited fetch + JSON parse settle.
      await Promise.resolve()
      await Promise.resolve()
    })

    // POST hit the proxy with session_id and consent_acknowledged in the URL,
    // and the body is the FormData carrying the file.
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toContain("/api/backend-proxy/jd-import/upload")
    expect(url).toContain("session_id=lia-session-test")
    expect(url).toContain("consent_acknowledged=true")
    expect((init as RequestInit).method).toBe("POST")
    expect((init as RequestInit).credentials).toBe("include")
    expect((init as RequestInit).body).toBeInstanceOf(FormData)

    // Queued row was seeded with the worker's payload shape.
    expect(h.seedBackgroundTask).toHaveBeenCalledWith(
      expect.objectContaining({
        task_id: "task-abc",
        task_type: "wizard",
        status: "queued",
        label: "Importação de Job Description",
      }),
    )

    // Now simulate the WS terminal event arriving via chatBackgroundTasks.
    act(() => {
      h.setTasks([
        {
          task_id: "task-abc",
          task_type: "wizard",
          label: "Importação de Job Description",
          status: "completed",
          message: "Vaga importada com sucesso.",
          result: { imported_jd_id: "jd-99" },
        },
      ])
    })

    // Prefill event went out with the imported_jd_id in the message body.
    expect(prefillSpy).toHaveBeenCalledTimes(1)
    const prefillDetail = (prefillSpy.mock.calls[0][0] as CustomEvent).detail
    expect(prefillDetail.message).toContain("jd-99")
    expect(prefillDetail.message).toContain("vaga-backend.pdf")
    expect(h.clearBackgroundTask).toHaveBeenCalledWith("task-abc")
    expect(h.appendChatMessage).not.toHaveBeenCalled() // success ≠ chat error
  })

  it("surfaces the worker error message verbatim on failed", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ success: true, task_id: "task-fairness", status: "queued" }),
        { status: 202, headers: { "content-type": "application/json" } },
      ),
    )

    const h = setup()

    await act(async () => {
      fireConfirmed(buildFile("vaga-discriminatoria.pdf"))
      await Promise.resolve()
      await Promise.resolve()
    })

    act(() => {
      h.setTasks([
        {
          task_id: "task-fairness",
          task_type: "wizard",
          label: "Importação de Job Description",
          status: "failed",
          message:
            "JD contém linguagem discriminatória e não pode ser importada. Revise o conteúdo.",
        },
      ])
    })

    expect(prefillSpy).not.toHaveBeenCalled()
    expect(h.clearBackgroundTask).toHaveBeenCalledWith("task-fairness")
    expect(h.appendChatMessage).toHaveBeenCalledTimes(1)
    const msg = h.appendChatMessage.mock.calls[0][0]
    expect(msg.sender).toBe("lia")
    expect(msg.content).toContain("Falha ao importar Job Description")
    expect(msg.content).toContain("linguagem discriminatória")
  })

  it("surfaces a chat error when the proxy responds non-2xx", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ success: false, error: "Authentication required" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    )

    const h = setup()

    await act(async () => {
      fireConfirmed(buildFile())
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(h.seedBackgroundTask).not.toHaveBeenCalled()
    expect(h.appendChatMessage).toHaveBeenCalledTimes(1)
    expect(h.appendChatMessage.mock.calls[0][0].content).toContain("Authentication required")
  })

  it("ignores non-JD file confirmations (CV branch belongs elsewhere)", async () => {
    const h = setup()

    await act(async () => {
      window.dispatchEvent(
        new CustomEvent("lia:file-upload-confirmed", {
          detail: { file: buildFile("curriculo.pdf"), type: "cv", consentAcknowledged: true },
        }),
      )
      await Promise.resolve()
    })

    expect(fetchMock).not.toHaveBeenCalled()
    expect(h.seedBackgroundTask).not.toHaveBeenCalled()
    expect(h.appendChatMessage).not.toHaveBeenCalled()
  })

  it("recovers when WS terminal `completed` arrives BEFORE the seed call (race)", async () => {
    // Hold the response until we've staged the WS terminal in chatBackgroundTasks.
    let resolveResponse: (r: Response) => void = () => {}
    const responsePromise = new Promise<Response>((res) => {
      resolveResponse = res
    })
    fetchMock.mockReturnValueOnce(responsePromise)

    const h = setup()

    // Fire the JD upload — fetch is now suspended.
    fireConfirmed(buildFile("vaga-rapida.pdf"))

    // While fetch is in flight, simulate the WS terminal already landing
    // for the (yet-to-be-acknowledged) task_id. This is the race: the
    // worker finished and emitted `completed` before we got to seed.
    act(() => {
      h.setTasks([
        {
          task_id: "task-race",
          task_type: "wizard",
          label: "Importação de Job Description",
          status: "completed",
          message: "Vaga importada com sucesso.",
          result: { imported_jd_id: "jd-race-1" },
        },
      ])
    })

    // Sanity: prefill must NOT have fired yet — we don't even know the
    // task_id is ours until the 202 body lands.
    expect(prefillSpy).not.toHaveBeenCalled()

    // Now release the 202 + task_id response.
    await act(async () => {
      resolveResponse(
        new Response(
          JSON.stringify({ success: true, task_id: "task-race", status: "queued" }),
          { status: 202, headers: { "content-type": "application/json" } },
        ),
      )
      await Promise.resolve()
      await Promise.resolve()
    })

    // The race-recovery branch must have fired the prefill exactly once,
    // even though no fresh chatBackgroundTasks update arrived after seed.
    expect(prefillSpy).toHaveBeenCalledTimes(1)
    const detail = (prefillSpy.mock.calls[0][0] as CustomEvent).detail
    expect(detail.message).toContain("jd-race-1")
    expect(detail.message).toContain("vaga-rapida.pdf")
    expect(h.clearBackgroundTask).toHaveBeenCalledWith("task-race")
    expect(h.appendChatMessage).not.toHaveBeenCalled()
  })

  it("treats a 200 + inline body (legacy sync path) as immediate completion", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ success: true, id: "jd-77", title: "Vaga" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    )

    const h = setup()

    await act(async () => {
      fireConfirmed(buildFile("legacy.txt"))
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(h.seedBackgroundTask).not.toHaveBeenCalled()
    expect(prefillSpy).toHaveBeenCalledTimes(1)
    const detail = (prefillSpy.mock.calls[0][0] as CustomEvent).detail
    expect(detail.message).toContain("legacy.txt")
  })
})
