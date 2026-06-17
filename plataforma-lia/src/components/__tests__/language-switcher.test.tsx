/**
 * Tests — LanguageSwitcher click behavior (task #391, regression guard for #380)
 *
 * Verifies that clicking the switcher:
 *   1. Sets the NEXT_LOCALE cookie to the target locale.
 *   2. Calls the locale-aware router.replace with the SAME pathname and the
 *      target locale (so /pt/dashboard ↔ /en/dashboard).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, cleanup } from "@testing-library/react"

const replaceMock = vi.fn()
let mockedLocale = "pt"
const mockedPathname = "/dashboard"

vi.mock("next-intl", () => ({
  useLocale: () => mockedLocale,
}))

vi.mock("@/i18n/routing", () => ({
  useRouter: () => ({ replace: replaceMock }),
  usePathname: () => mockedPathname,
}))

import { LanguageSwitcher } from "../language-switcher"

describe("LanguageSwitcher — click navigates between /pt/... and /en/...", () => {
  beforeEach(() => {
    replaceMock.mockReset()
    // Reset cookies between tests
    document.cookie
      .split(";")
      .map((c) => c.split("=")[0].trim())
      .filter(Boolean)
      .forEach((name) => {
        document.cookie = `${name}=; path=/; max-age=0`
      })
  })

  afterEach(() => {
    cleanup()
  })

  it("from PT: clicking switches to EN, sets NEXT_LOCALE=en, and navigates same path with locale=en", () => {
    mockedLocale = "pt"
    render(<LanguageSwitcher />)

    const button = screen.getByRole("button")
    expect(button).toHaveTextContent("PT")

    fireEvent.click(button)

    expect(document.cookie).toContain("NEXT_LOCALE=en")
    expect(replaceMock).toHaveBeenCalledTimes(1)
    expect(replaceMock).toHaveBeenCalledWith(mockedPathname, { locale: "en" })
  })

  it("from EN: clicking switches to PT, sets NEXT_LOCALE=pt, and navigates same path with locale=pt", () => {
    mockedLocale = "en"
    render(<LanguageSwitcher />)

    const button = screen.getByRole("button")
    expect(button).toHaveTextContent("EN")

    fireEvent.click(button)

    expect(document.cookie).toContain("NEXT_LOCALE=pt")
    expect(replaceMock).toHaveBeenCalledTimes(1)
    expect(replaceMock).toHaveBeenCalledWith(mockedPathname, { locale: "pt" })
  })
})
