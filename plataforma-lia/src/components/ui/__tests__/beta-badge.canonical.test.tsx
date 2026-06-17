/**
 * Sprint visual 2026-05-26 — BetaBadge canonical neutral DS.
 *
 * White-label decision: cyan e EXCLUSIVA da assistente. BetaBadge antes
 * usava bg-wedo-cyan + text-white. Agora bg-lia-bg-inverse + text-lia-text-on-inverse
 * (slate-800-ish neutro canonical), cascateando pros 8 consumers.
 */
import { describe, expect, it } from "vitest"
import { render } from "@testing-library/react"
import { BetaBadge } from "../beta-badge"

describe("BetaBadge — Sprint visual canonical neutral DS", () => {
  it("NÃO usa wedo-cyan (white-label Studio)", () => {
    const { container } = render(<BetaBadge />)
    const html = container.innerHTML
    expect(html).not.toContain("bg-wedo-cyan")
    expect(html).not.toContain("text-wedo-cyan")
  })

  it("usa neutros DS canonical (lia-bg-inverse + lia-text-on-inverse)", () => {
    const { container } = render(<BetaBadge />)
    const html = container.innerHTML
    expect(html).toContain("bg-lia-bg-inverse")
    expect(html).toContain("text-lia-text-on-inverse")
  })
})
