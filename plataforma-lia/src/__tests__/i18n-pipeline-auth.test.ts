import { describe, it, expect } from "vitest"
import ptBR from "../../messages/pt-BR.json"
import en from "../../messages/en.json"

// Contrato i18n do estado de relogin do Funil (task #293).
// Garante que o mapeamento errorKind → t(`auth.<kind>Message`) em
// candidates-page.tsx (canônico 719L) nunca aponte para chave inexistente.
const REQUIRED_KEYS = [
  "reloginTitle",
  "reloginCta",
  "unauthorizedMessage",
  "forbiddenMessage",
  "serverErrorMessage",
  "networkErrorMessage",
] as const

type Dict = Record<string, unknown>

function getAuthSection(bundle: Dict): Dict {
  const pipeline = bundle["pipeline"] as Dict | undefined
  expect(pipeline, "bundle must expose a `pipeline` namespace").toBeDefined()
  const auth = pipeline!["auth"] as Dict | undefined
  expect(auth, "`pipeline.auth` namespace must exist").toBeDefined()
  return auth!
}

describe("i18n contract: pipeline.auth for Funil relogin UX", () => {
  it.each([
    ["pt-BR", ptBR as Dict],
    ["en", en as Dict],
  ])("%s bundle exposes all required auth keys", (_label, bundle) => {
    const auth = getAuthSection(bundle)
    for (const key of REQUIRED_KEYS) {
      expect(auth[key], `missing pipeline.auth.${key}`).toEqual(
        expect.any(String),
      )
      expect((auth[key] as string).length).toBeGreaterThan(0)
    }
  })

  it("pt-BR and en have identical auth key sets (no drift)", () => {
    const ptKeys = Object.keys(getAuthSection(ptBR as Dict)).sort()
    const enKeys = Object.keys(getAuthSection(en as Dict)).sort()
    expect(ptKeys).toEqual(enKeys)
  })
})
