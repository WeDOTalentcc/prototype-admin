/**
 * Wizard A11y — WCAG Contrast Sweep (A-09)
 *
 * Audit #837 lente design/WCAG 2.1 AA highlighted small (10–11 px) text rendered
 * with `text-lia-text-disabled` (≈2.85:1) inside the OutreachCard and several
 * wizard panels. After the fix (text-xs + text-lia-text-secondary), this spec
 * runs `@axe-core/playwright` on the live wizard surface and fails the build on
 * any SERIOUS or CRITICAL violation — anchoring Inegociável WeDO #8.
 *
 * Focus-trap behavior (A-08) was originally guarded by a jsdom test
 * (`src/components/__tests__/expanded-chat-focus-lock.test.tsx`) tied to
 * the deprecated `expanded-chat-modal` wrapper. That surface was removed
 * in Task #860 (A-01); the canonical `UnifiedChat` does not own its own
 * modal wrapper today, so focus-trap is no longer a stand-alone contract.
 * If the next chat surface that owns a modal wrapper lands, re-introduce a
 * jsdom smoke against the new component before relying on it for A-08.
 */
import AxeBuilder from '@axe-core/playwright'

import { test, expect } from '../../fixtures/auth.fixture'

test.describe('Wizard A11y — Contrast (A-09)', () => {
  test('axe-core: zero serious or critical violations on /vagas/nova', async ({
    authenticatedPage,
  }) => {
    await authenticatedPage.goto('/vagas/nova', { waitUntil: 'load', timeout: 30_000 })
    await authenticatedPage.waitForLoadState('networkidle').catch(() => {
      // Dev server keeps HMR sockets open; ignore networkidle timeout.
    })

    const results = await new AxeBuilder({ page: authenticatedPage })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    const blocking = results.violations.filter(
      (v) => v.impact === 'serious' || v.impact === 'critical',
    )

    if (blocking.length > 0) {
      // Surface offending selectors so CI logs make the fix obvious.
      const summary = blocking
        .map(
          (v) =>
            `${v.id} (${v.impact}) — ${v.help}\n  nodes: ${v.nodes
              .map((n) => n.target.join(' > '))
              .join('\n         ')}`,
        )
        .join('\n')
      console.error('axe-core violations:\n' + summary)
    }

    expect(blocking, 'No serious/critical axe violations allowed on wizard surface').toHaveLength(0)
  })
})
