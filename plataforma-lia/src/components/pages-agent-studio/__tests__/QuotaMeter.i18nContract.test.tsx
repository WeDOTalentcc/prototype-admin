import { describe, expect, it } from "vitest"
import { render } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import ptBR from "../../../../messages/pt-BR.json"
import en from "../../../../messages/en.json"
import { QuotaMeter } from "../QuotaMeter"

describe("QuotaMeter — i18n canonical contract", () => {
  const REQUIRED_KEYS = [
    "title", "loading", "plan", "regionLabel", "unlimited",
    "warning", "contactAm",
    "resources.custom_agents", "resources.sourcing_agents",
    "resources.digital_twins", "resources.campaigns",
  ]
  for (const locale of ["pt-BR", "en"] as const) {
    const messages = locale === "pt-BR" ? ptBR : en
    for (const key of REQUIRED_KEYS) {
      it(`${locale}: agents.studio.quotaMeter.${key} exists as string`, () => {
        const path = `agents.studio.quotaMeter.${key}`.split(".")
        const value = path.reduce<unknown>((o, k) => (o as Record<string, unknown> | null)?.[k], messages)
        expect(typeof value).toBe("string")
      })
    }
  }
  it("renders without MISSING_MESSAGE when data has null fields", () => {
    const errors: Array<{ message?: string }> = []
    render(
      <NextIntlClientProvider locale="pt" messages={ptBR}
        onError={(e) => errors.push(e)}>
        <QuotaMeter />
      </NextIntlClientProvider>
    )
    expect(errors.filter(e => e.message?.includes?.("MISSING_MESSAGE"))).toEqual([])
  })
})
