/**
 * Source-level tests — W2.3: P1-9 (companyId) + P1-10 (token refresh).
 *
 * Auditoria 2026-04-26:
 *   - P1-9: useTeamsSSO descartava `company_id` do response do backend.
 *           Frontend não tinha tenant em estado para próximos fetches.
 *   - P1-10: useTeamsSSO rodava handshake apenas 1× por mount. Tab aberta
 *            por horas → JWT expirava → 401 silencioso, recrutador precisava
 *            recarregar.
 *
 * Estes tests validam o contrato source-level (não dependem do SDK Teams
 * que só roda dentro do iframe).
 */
import { describe, it, expect } from "vitest"
import * as fs from "fs"
import * as path from "path"

const SRC = fs.readFileSync(
  path.resolve(__dirname, "../use-teams-sso.ts"),
  "utf-8",
)

describe("useTeamsSSO — W2.3 P1-9 companyId", () => {
  it("interface TeamsSSOState includes companyId field", () => {
    expect(SRC).toMatch(/companyId:\s*string\s*\|\s*null/)
  })

  it("auth response destructures company_id", () => {
    expect(SRC).toMatch(/company_id\s*[},]/)
  })

  it("setState writes companyId from response", () => {
    expect(SRC).toMatch(/companyId:\s*company_id/)
  })

  it("INITIAL_STATE includes companyId: null", () => {
    expect(SRC).toMatch(/INITIAL_STATE[\s\S]*?companyId:\s*null/)
  })
})

describe("useTeamsSSO — W2.3 P1-10 refresh", () => {
  it("exposes refresh callback in result type", () => {
    expect(SRC).toMatch(/refresh:\s*\(\)\s*=>\s*Promise<void>/)
  })

  it("schedules setInterval for periodic re-handshake", () => {
    expect(SRC).toMatch(/setInterval/)
  })

  it("clears interval on unmount via useEffect cleanup", () => {
    expect(SRC).toMatch(/clearInterval/)
  })

  it("REFRESH_INTERVAL_MS exported as constant", () => {
    expect(SRC).toMatch(/export\s+const\s+REFRESH_INTERVAL_MS/)
  })

  it("returns refresh as part of hook result", () => {
    expect(SRC).toMatch(/return\s*\{[\s\S]*?\.\.\.state[\s\S]*?refresh\s*\}/)
  })
})
