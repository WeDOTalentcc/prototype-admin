/**
 * GAP-07-006 — useEmailTemplatePreview hook tests
 *
 * Tests:
 *   - fetchPreview: calls the correct proxy endpoint
 *   - fetchPreview: returns rendered subject/body_html/body_text on success
 *   - fetchPreview: detects missing (unfilled) variables in rendered output
 *   - fetchPreview: surfaces 404 as user-friendly error
 *   - fetchPreview: surfaces generic API error
 *   - reset: clears preview state
 */
import { renderHook, act, waitFor } from "@testing-library/react"
import { vi } from "vitest"
import { useEmailTemplatePreview } from "../use-email-template-preview"

// ─── helpers ──────────────────────────────────────────────────────────────────

function mockFetch(status: number, body: unknown) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response)
}

const TEMPLATE_ID = "550e8400-e29b-41d4-a716-446655440000"

// ─── tests ────────────────────────────────────────────────────────────────────

describe("useEmailTemplatePreview", () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("calls the correct proxy endpoint with template id and variables", async () => {
    mockFetch(200, {
      success: true,
      data: {
        subject: "Olá João Silva",
        body_html: "<p>Vaga: Desenvolvedor</p>",
        body_text: null,
      },
    })

    const { result } = renderHook(() => useEmailTemplatePreview())

    await act(async () => {
      await result.current.fetchPreview(TEMPLATE_ID, { candidate_name: "João Silva" })
    })

    expect(global.fetch).toHaveBeenCalledWith(
      `/api/backend-proxy/email-templates/${TEMPLATE_ID}/preview`,
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ variables: { candidate_name: "João Silva" } }),
      }),
    )
  })

  it("returns rendered subject and body_html on success (BE shape: data.subject)", async () => {
    mockFetch(200, {
      success: true,
      data: {
        subject: "Entrevista para Desenvolvedor",
        body_html: "<p>Olá Ana Lima, você foi chamada para entrevista.</p>",
        body_text: "Olá Ana Lima, você foi chamada para entrevista.",
      },
    })

    const { result } = renderHook(() => useEmailTemplatePreview())

    await act(async () => {
      await result.current.fetchPreview(TEMPLATE_ID, { candidate_name: "Ana Lima", job_title: "Desenvolvedor" })
    })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.preview).toEqual({
      subject: "Entrevista para Desenvolvedor",
      body_html: "<p>Olá Ana Lima, você foi chamada para entrevista.</p>",
      body_text: "Olá Ana Lima, você foi chamada para entrevista.",
    })
    expect(result.current.error).toBeNull()
    expect(result.current.missingVariables).toEqual([])
  })

  it("detects missing variables (unfilled {{...}} placeholders in rendered output)", async () => {
    // BE returns template with unfilled placeholder (variable not provided)
    mockFetch(200, {
      success: true,
      data: {
        subject: "Olá {{candidate_name}}, sua vaga: Engenheira",
        body_html: "<p>Empresa: {{company_name}}. Início: {{start_date}}.</p>",
        body_text: null,
      },
    })

    const { result } = renderHook(() => useEmailTemplatePreview())

    await act(async () => {
      // Only providing job_title, leaving candidate_name, company_name, start_date unfilled
      await result.current.fetchPreview(TEMPLATE_ID, { job_title: "Engenheira" })
    })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    // Should detect all 3 unfilled variables, sorted
    expect(result.current.missingVariables).toEqual(["candidate_name", "company_name", "start_date"])
    expect(result.current.preview).not.toBeNull()
  })

  it("sets error and clears preview on 404 (template not found)", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: vi.fn().mockResolvedValue({}),
    } as unknown as Response)

    const { result } = renderHook(() => useEmailTemplatePreview())

    await act(async () => {
      await result.current.fetchPreview("nonexistent-id", {})
    })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.preview).toBeNull()
    expect(result.current.error).toBe("Template não encontrado.")
    expect(result.current.missingVariables).toEqual([])
  })

  it("sets error on generic API failure", async () => {
    mockFetch(500, { detail: "Internal server error" })

    const { result } = renderHook(() => useEmailTemplatePreview())

    await act(async () => {
      await result.current.fetchPreview(TEMPLATE_ID, {})
    })

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.preview).toBeNull()
    expect(result.current.error).toContain("Internal server error")
  })

  it("reset() clears all state back to initial", async () => {
    mockFetch(200, {
      success: true,
      data: { subject: "Rendered", body_html: "<p>Body</p>", body_text: null },
    })

    const { result } = renderHook(() => useEmailTemplatePreview())

    await act(async () => {
      await result.current.fetchPreview(TEMPLATE_ID, { candidate_name: "Ana" })
    })

    await waitFor(() => expect(result.current.preview).not.toBeNull())

    act(() => {
      result.current.reset()
    })

    expect(result.current.preview).toBeNull()
    expect(result.current.missingVariables).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })
})
