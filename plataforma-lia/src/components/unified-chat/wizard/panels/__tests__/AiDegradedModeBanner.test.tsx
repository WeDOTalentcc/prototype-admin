import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { AiDegradedModeBanner } from "../AiDegradedModeBanner"
import type { AiDegradedMode } from "../../wizard-types"

/**
 * Task #1070 — sentinela do banner agregado de modo degradado.
 *
 * O banner deve aparecer SOMENTE quando o backend (`WizardFallbackTracker`)
 * informa `active=true` no payload `ai_degraded_mode`. Sem isso, o
 * recrutador volta a ver apenas o `FallbackBanner` por etapa e perde a
 * sinalizacao de que o provedor de IA esta degradado AGORA.
 */
describe("AiDegradedModeBanner", () => {
  it("nao renderiza quando state esta ausente", () => {
    const { container } = render(<AiDegradedModeBanner state={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it("nao renderiza quando active=false", () => {
    const state: AiDegradedMode = {
      active: false,
      scope: "session",
      count: 0,
      threshold: 3,
      window_seconds: 1800,
      since: new Date().toISOString(),
      reason_breakdown: {},
    }
    const { container } = render(<AiDegradedModeBanner state={state} />)
    expect(container).toBeEmptyDOMElement()
  })

  it("renderiza copy de sessao com contagem e breakdown", () => {
    const state: AiDegradedMode = {
      active: true,
      scope: "session",
      count: 3,
      threshold: 3,
      window_seconds: 1800,
      since: new Date().toISOString(),
      reason_breakdown: { timeout: 2, provider_error: 1 },
    }
    render(<AiDegradedModeBanner state={state} />)
    const banner = screen.getByTestId("wizard-ai-degraded-banner")
    expect(banner).toHaveAttribute("data-scope", "session")
    expect(banner).toHaveTextContent(/Qualidade da IA degradada agora/i)
    expect(banner).toHaveTextContent(/nesta sessao/i)
    expect(banner).toHaveTextContent(/3 falhas/)
    expect(banner).toHaveTextContent(/2x timeout/)
    expect(banner).toHaveTextContent(/1x provider_error/)
  })

  it("usa copy de tenant quando scope=tenant", () => {
    const state: AiDegradedMode = {
      active: true,
      scope: "tenant",
      count: 5,
      threshold: 5,
      window_seconds: 3600,
      since: new Date().toISOString(),
      reason_breakdown: { provider_error: 5 },
    }
    render(<AiDegradedModeBanner state={state} />)
    const banner = screen.getByTestId("wizard-ai-degraded-banner")
    expect(banner).toHaveAttribute("data-scope", "tenant")
    expect(banner).toHaveTextContent(/ultima hora/i)
    expect(banner).toHaveTextContent(/5 falhas/)
  })
})
