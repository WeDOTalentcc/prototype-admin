/**
 * Tests — CandidateEditContext provider + useCandidateEdit hook.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { CandidateEditProvider, useCandidateEdit } from "../CandidateEditContext"

function Probe() {
  const { editable, candidateId, updateField, isSaving } = useCandidateEdit()
  return (
    <div>
      <span data-testid="editable">{String(editable)}</span>
      <span data-testid="id">{candidateId ?? "none"}</span>
      <span data-testid="hasUpdate">{updateField ? "yes" : "no"}</span>
      <span data-testid="hasSaving">{isSaving ? "yes" : "no"}</span>
    </div>
  )
}

describe("CandidateEditContext", () => {
  it("default values when no provider: editable=false, candidateId=undefined", () => {
    render(<Probe />)
    expect(screen.getByTestId("editable").textContent).toBe("false")
    expect(screen.getByTestId("id").textContent).toBe("none")
    expect(screen.getByTestId("hasUpdate").textContent).toBe("no")
  })

  it("provider supplies editable + candidateId + callbacks", () => {
    const updateField = vi.fn().mockResolvedValue({ success: true })
    const isSaving = vi.fn().mockReturnValue(false)
    render(
      <CandidateEditProvider editable={true} candidateId="cand-42" updateField={updateField} isSaving={isSaving}>
        <Probe />
      </CandidateEditProvider>
    )
    expect(screen.getByTestId("editable").textContent).toBe("true")
    expect(screen.getByTestId("id").textContent).toBe("cand-42")
    expect(screen.getByTestId("hasUpdate").textContent).toBe("yes")
    expect(screen.getByTestId("hasSaving").textContent).toBe("yes")
  })

  it("editable=false provider still wraps subtree", () => {
    render(
      <CandidateEditProvider editable={false} candidateId="x">
        <Probe />
      </CandidateEditProvider>
    )
    expect(screen.getByTestId("editable").textContent).toBe("false")
    expect(screen.getByTestId("id").textContent).toBe("x")
  })
})
