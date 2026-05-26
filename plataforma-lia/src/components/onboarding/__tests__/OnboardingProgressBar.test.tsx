import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor, act } from "@testing-library/react"
import { OnboardingProgressBar } from "@/components/onboarding/OnboardingProgressBar"

describe("OnboardingProgressBar — P2-2 B.3", () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("renderiza compact variant com initialProgress (sem fetch)", () => {
    render(<OnboardingProgressBar variant="compact" initialProgress={45} />)
    expect(screen.getByTestId("onboarding-progress-compact")).toBeInTheDocument()
    expect(screen.getByText("45%")).toBeInTheDocument()
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it("renderiza full variant com initialProgress", () => {
    render(<OnboardingProgressBar variant="full" initialProgress={60} />)
    expect(screen.getByTestId("onboarding-progress-full")).toBeInTheDocument()
    expect(screen.getByText("60%")).toBeInTheDocument()
  })

  it("fetch inicial quando sem initialProgress", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ overall: 72 }),
    })
    render(<OnboardingProgressBar variant="compact" />)
    await waitFor(() => {
      expect(screen.getByText("72%")).toBeInTheDocument()
    })
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/backend-proxy/settings/progress/",
      expect.objectContaining({ credentials: "include" }),
    )
  })

  it("aria-valuenow reflete progress", () => {
    render(<OnboardingProgressBar variant="compact" initialProgress={42} />)
    const bar = screen.getByRole("progressbar")
    expect(bar).toHaveAttribute("aria-valuenow", "42")
  })

  it("clamp em 0 e 100", () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ overall: 150 }),
    })
    render(<OnboardingProgressBar variant="compact" />)
    return waitFor(() => {
      const bar = screen.getByRole("progressbar")
      expect(bar).toHaveAttribute("aria-valuenow", "100")
    })
  })

  it("milestones renderizados no full variant", () => {
    render(<OnboardingProgressBar variant="full" initialProgress={50} />)
    expect(screen.getByTestId("milestone-25")).toBeInTheDocument()
    expect(screen.getByTestId("milestone-50")).toBeInTheDocument()
    expect(screen.getByTestId("milestone-75")).toBeInTheDocument()
  })

  it("mensagem complete em 100%", () => {
    render(<OnboardingProgressBar variant="full" initialProgress={100} />)
    expect(screen.getByTestId("complete-message")).toBeInTheDocument()
  })

  it("sem complete-message abaixo de 100", () => {
    render(<OnboardingProgressBar variant="full" initialProgress={99} />)
    expect(screen.queryByTestId("complete-message")).not.toBeInTheDocument()
  })

  it("listener lia:settings-updated re-fetcha", async () => {
    let callCount = 0
    global.fetch = vi.fn().mockImplementation(async () => {
      callCount++
      return {
        ok: true,
        json: async () => ({ overall: callCount * 20 }),
      }
    })
    render(<OnboardingProgressBar variant="compact" />)
    await waitFor(() => {
      expect(screen.getByText("20%")).toBeInTheDocument()
    })

    // Dispatch event manualmente
    await act(async () => {
      window.dispatchEvent(new CustomEvent("lia:settings-updated", { detail: {} }))
    })

    await waitFor(() => {
      expect(screen.getByText("40%")).toBeInTheDocument()
    })
  })

  it("fetch failure não quebra component (fallback 0)", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 })
    render(<OnboardingProgressBar variant="compact" />)
    await waitFor(() => {
      expect(screen.getByText("0%")).toBeInTheDocument()
    })
  })

  it("showLabel=false esconde texto", () => {
    render(<OnboardingProgressBar variant="compact" initialProgress={50} showLabel={false} />)
    expect(screen.queryByText("50%")).not.toBeInTheDocument()
  })

  it("cleanup listener no unmount", () => {
    const removeSpy = vi.spyOn(window, "removeEventListener")
    const { unmount } = render(<OnboardingProgressBar variant="compact" initialProgress={30} />)
    unmount()
    expect(removeSpy).toHaveBeenCalledWith("lia:settings-updated", expect.any(Function))
  })
})
