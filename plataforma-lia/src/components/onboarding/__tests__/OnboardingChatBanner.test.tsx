import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { OnboardingChatBanner } from "@/components/onboarding/OnboardingChatBanner"

// Mock next/navigation router
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

// Mock next-intl (useLocale)
vi.mock("next-intl", () => ({
  useLocale: () => "pt",
}))

// Mock useOnboardingFlow hook
vi.mock("@/components/onboarding/useOnboardingFlow", () => ({
  useOnboardingFlow: vi.fn(),
}))

import { useOnboardingFlow } from "@/components/onboarding/useOnboardingFlow"
const mockUseOnboardingFlow = vi.mocked(useOnboardingFlow)

describe("OnboardingChatBanner — P2-2 B.1", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    if (typeof window !== "undefined") {
      window.localStorage.clear()
    }
  })

  it("não renderiza enquanto loading", () => {
    mockUseOnboardingFlow.mockReturnValue({
      needsOnboarding: false,
      sessionId: null,
      setupProgress: null,
      loading: true,
    })
    const { container } = render(<OnboardingChatBanner />)
    expect(container.firstChild).toBeNull()
  })

  it("não renderiza quando setup_progress >= threshold (needsOnboarding=false)", () => {
    mockUseOnboardingFlow.mockReturnValue({
      needsOnboarding: false,
      sessionId: null,
      setupProgress: 90,
      loading: false,
    })
    const { container } = render(<OnboardingChatBanner />)
    expect(container.firstChild).toBeNull()
  })

  it("renderiza quando needsOnboarding=true", () => {
    mockUseOnboardingFlow.mockReturnValue({
      needsOnboarding: true,
      sessionId: null,
      setupProgress: 30,
      loading: false,
    })
    render(<OnboardingChatBanner />)
    expect(screen.getByTestId("onboarding-chat-banner")).toBeInTheDocument()
  })

  it("mostra progress %", () => {
    mockUseOnboardingFlow.mockReturnValue({
      needsOnboarding: true,
      sessionId: null,
      setupProgress: 35,
      loading: false,
    })
    render(<OnboardingChatBanner />)
    expect(screen.getByText(/35%/)).toBeInTheDocument()
  })

  it("não renderiza quando dismissed", () => {
    window.localStorage.setItem("lia-onboarding-banner-dismissed", "true")
    mockUseOnboardingFlow.mockReturnValue({
      needsOnboarding: true,
      sessionId: null,
      setupProgress: 60,  // > RESHOW threshold 50
      loading: false,
    })
    const { container } = render(<OnboardingChatBanner />)
    expect(container.firstChild).toBeNull()
  })

  it("re-show automatico quando progress < 50% mesmo dismissed", () => {
    window.localStorage.setItem("lia-onboarding-banner-dismissed", "true")
    mockUseOnboardingFlow.mockReturnValue({
      needsOnboarding: true,
      sessionId: null,
      setupProgress: 40,  // < 50% trigger re-show
      loading: false,
    })
    render(<OnboardingChatBanner />)
    expect(screen.getByTestId("onboarding-chat-banner")).toBeInTheDocument()
  })

  it("botão dismiss persiste em localStorage", () => {
    mockUseOnboardingFlow.mockReturnValue({
      needsOnboarding: true,
      sessionId: null,
      setupProgress: 60,
      loading: false,
    })
    const { container } = render(<OnboardingChatBanner />)
    const dismiss = screen.getByTestId("banner-dismiss")
    fireEvent.click(dismiss)
    expect(window.localStorage.getItem("lia-onboarding-banner-dismissed")).toBe("true")
    expect(container.firstChild).toBeNull()
  })

  it("botão Configure via chat chama onOpenChat callback", () => {
    const onOpenChat = vi.fn()
    mockUseOnboardingFlow.mockReturnValue({
      needsOnboarding: true,
      sessionId: null,
      setupProgress: 30,
      loading: false,
    })
    render(<OnboardingChatBanner onOpenChat={onOpenChat} />)
    fireEvent.click(screen.getByTestId("banner-open-chat"))
    expect(onOpenChat).toHaveBeenCalledTimes(1)
  })

  it("a11y: role=region + aria-label", () => {
    mockUseOnboardingFlow.mockReturnValue({
      needsOnboarding: true,
      sessionId: null,
      setupProgress: 30,
      loading: false,
    })
    render(<OnboardingChatBanner />)
    const banner = screen.getByRole("region", { name: /onboarding/i })
    expect(banner).toBeInTheDocument()
  })
})
