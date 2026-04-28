/**
 * Task #895 — page-level wiring smoke for the Webhooks tab.
 *
 * Sister to `settings-page-target-resolution.test.ts` (which covers the
 * pure resolver) and `components/settings/__tests__/WebhooksManager.test.tsx`
 * (which covers the manager itself). This test closes the gap pointed
 * out by code review: prove the host page actually wires the new
 * section instead of only the resolver knowing about it.
 *
 * `SettingsPageEnhanced` lazy-loads 9 hubs through `next/dynamic`, reads
 * `useSearchParams`, hits `/api/backend-proxy/settings/progress`, hooks
 * into a sidebar hover-debounce that depends on `matchMedia`, and emits
 * cross-window events. Mounting the whole tree under jsdom is brittle
 * for a wiring smoke (and kept hanging the test runner). Instead we
 * read the source file and assert the four wiring contracts that have
 * to hold for the Webhooks tab to function:
 *
 *   1. The Lucide `Webhook` icon is imported.
 *   2. The `WebhooksManager` chunk is registered through `next/dynamic`.
 *   3. `getDefaultSections` declares an entry whose id is `webhooks`.
 *   4. `renderSectionContent` has a `case 'webhooks':` branch that
 *      renders the manager.
 *
 * Together with the resolver test and the manager test, these checks
 * cover the deep-link → state → render path end-to-end.
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, it } from "vitest"

const PAGE = readFileSync(
  join(__dirname, "..", "settings-page-enhanced.tsx"),
  "utf8",
)

describe("SettingsPageEnhanced — Task #895 webhooks wiring", () => {
  it("imports the Webhook icon from lucide-react", () => {
    expect(PAGE).toMatch(/from\s*["']lucide-react["']/)
    const lucideBlock = PAGE.match(/import\s*\{([\s\S]*?)\}\s*from\s*["']lucide-react["']/)
    expect(lucideBlock).toBeTruthy()
    expect(lucideBlock?.[1]).toMatch(/\bWebhook\b/)
  })

  it("registers WebhooksManager as a next/dynamic chunk", () => {
    expect(PAGE).toMatch(
      /const\s+WebhooksManager\s*=\s*dynamic\([\s\S]*?import\(["'][^"']*WebhooksManager["']\)/,
    )
  })

  it("declares a 'webhooks' section in the default settings menu", () => {
    expect(PAGE).toMatch(/id:\s*['"]webhooks['"]/)
    expect(PAGE).toMatch(/'webhooks':\s*0/)
  })

  it("renders <WebhooksManager /> when activeSection === 'webhooks'", () => {
    const branch = PAGE.match(
      /case\s+['"]webhooks['"]:[\s\S]{0,400}?<WebhooksManager\s*\/>/,
    )
    expect(branch, "renderSectionContent must render WebhooksManager for the webhooks case").toBeTruthy()
  })
})
