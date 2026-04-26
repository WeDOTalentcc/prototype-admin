/**
 * Task #828 — End-to-end coverage for the "Plano de trabalho" card and the
 * sticky `WizardProgressBar` on the main /chat surface.
 *
 * The unit/component tests in
 *   src/components/unified-chat/wizard/__tests__/wizard-flow-bridge.test.tsx
 *   src/components/unified-chat/wizard/__tests__/wizard-plan-card.test.ts
 * cover the helpers and the `useWizardFlow` reducer in isolation. The
 * pytest in `lia-agent-system/tests/integration/test_job_creation_graph_e2e.py`
 * covers the backend `intake_node` emission.
 *
 * What is missing — and what this spec adds — is the full round-trip on
 * the recruiter chat surface:
 *
 *   real authenticated user
 *     → /pt/chat (UnifiedChat in fullscreen mode)
 *     → sends "Criar uma nova vaga"
 *     → real lia-backend processes intake and emits `wizard_stage`
 *     → useChatSocket bridges it into `lia:wizard-stage-payload`
 *     → useWizardFlow reduces stage → "intake"
 *     → UnifiedChat injects the "Plano de trabalho" assistant card
 *     → WizardProgressBar mounts above the message list (does not scroll
 *       with it because it sits in the column above `overflow-y-auto`)
 *     → on the terminal `done` payload the progress bar unmounts AND the
 *       plan card flips to "Plano de trabalho — Concluído" with all 6
 *       visible steps marked completed (Task #830). The card itself
 *       stays in the feed so the recruiter sees a clear "this finished"
 *       signal instead of the previous frozen "calibração — em
 *       progresso" state.
 *
 * SCOPE NOTE — backend completion path
 * -----------------------------------
 * Driving lia-backend through every wizard stage (intake →
 * jd_enrichment → bigfive → salary → competency → wsi_questions →
 * eligibility → review → publish → calibration → handoff → done) inside a
 * single Playwright run requires 8+ LLM-heavy turns and is wall-clock
 * incompatible with the suite-wide 120s timeout. We therefore make a
 * deliberate scope choice:
 *
 *   - The intake turn uses the REAL backend. This proves the full
 *     bridge works end-to-end: HTTP/WS auth, lia-backend graph, the
 *     useChatSocket → useWizardFlow → UnifiedChat → DOM chain.
 *   - The terminal `done` transition is exercised by dispatching the
 *     SAME `lia:wizard-stage-payload` CustomEvent that `useChatSocket`
 *     emits when the backend delivers
 *     `{"type": "wizard_stage", "stage": "done"}`. This is the canonical
 *     bridge under test: the production backend has no other code path
 *     into `useWizardFlow`. Driving it from the page is therefore an
 *     equivalent shortcut, not a mock. The follow-up task tracks
 *     promoting this to a fully backend-driven completion run in CI.
 */
import { test, expect } from '../../fixtures/auth.fixture';

const CHAT_URL = '/pt/chat';

// The intake turn involves an LLM call plus WebSocket round-trips. Cap it
// well below the suite's 120s budget so a regression fails loudly.
const FIRST_TURN_TIMEOUT_MS = 60_000;

test.describe('Cartão "Plano de trabalho" + WizardProgressBar — e2e (Task #828, #830)', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    if (!authenticatedPage.url().includes(CHAT_URL)) {
      await authenticatedPage.goto(CHAT_URL, { waitUntil: 'load', timeout: 30_000 });
    }
    await authenticatedPage
      .locator('textarea[aria-label="Mensagem para a LIA"], input[aria-label="Mensagem para a LIA"]')
      .first()
      .waitFor({ state: 'visible', timeout: 20_000 });
  });

  test('mounts plan card + progress bar after intake; bar stays put when feed scrolls; bar unmounts and plan card flips to Concluído on `done`', async ({ authenticatedPage }) => {
    const planCard = authenticatedPage.locator('[data-testid="wizard-plan-card"]').first();
    const progressBar = authenticatedPage.locator('[data-testid="wizard-progress-bar"]').first();

    // (0) Pre-conditions — neither surface exists before any wizard turn.
    await expect(
      planCard,
      'plan card must NOT be present before any wizard_stage event arrives',
    ).toHaveCount(0);
    await expect(
      progressBar,
      'progress bar must NOT be mounted before any wizard_stage event arrives',
    ).toHaveCount(0);
    await authenticatedPage.screenshot({
      path: 'e2e/screenshots/wizard-plan-card-001-empty.png',
      fullPage: true,
    });

    // (1) Send the canonical wizard-trigger phrase. The backend intake_node
    // reacts to this by emitting `wizard_stage` with stage="intake".
    const input = authenticatedPage
      .locator('textarea[aria-label="Mensagem para a LIA"], input[aria-label="Mensagem para a LIA"]')
      .first();
    await input.click();
    await input.fill('Criar uma nova vaga');
    await input.press('Enter');

    // (2) Plan card AND progress bar must mount once the first
    // `wizard_stage` event flows back from the real backend. Wait on each
    // independently so a partial mount fails loudly instead of timing out
    // in the wrong place.
    await expect(
      planCard,
      'plan card must mount after the first real wizard_stage event from lia-backend',
    ).toBeVisible({ timeout: FIRST_TURN_TIMEOUT_MS });

    await expect(
      progressBar,
      'progress bar must mount after the first real wizard_stage event from lia-backend',
    ).toBeVisible({ timeout: FIRST_TURN_TIMEOUT_MS });

    // The card surfaces the title literal exposed by `wizard-plan-card.ts`.
    await expect(
      planCard.getByText('Plano de trabalho', { exact: false }),
      'plan card must render the canonical "Plano de trabalho" title',
    ).toBeVisible();

    // (2.b) The progress bar must sit in the column ABOVE the scrollable
    // message list — verify ordering vs. the plan card first.
    const initialBarBox = await progressBar.boundingBox();
    const planCardBox = await planCard.boundingBox();
    expect(initialBarBox, 'progress bar must have a bounding box').not.toBeNull();
    expect(planCardBox, 'plan card must have a bounding box').not.toBeNull();
    if (initialBarBox && planCardBox) {
      expect(
        initialBarBox.y,
        `progress bar (y=${initialBarBox.y}) must render above the plan card (y=${planCardBox.y})`,
      ).toBeLessThan(planCardBox.y);
    }

    // (2.c) "Fica fixa no topo do feed" — scroll the message-list container
    // and assert the bar's viewport y does not move. The bar lives outside
    // the scroll container (UnifiedChat puts it in the flex column above
    // `<UnifiedMessageList overflow-y-auto>`), so it must remain visually
    // anchored even when the user scrolls through messages.
    await planCard.scrollIntoViewIfNeeded();
    await authenticatedPage.evaluate(() => {
      const scroller = document.querySelector('[data-testid="wizard-progress-bar"]')
        ?.parentElement?.parentElement?.querySelector('div.overflow-y-auto') as HTMLElement | null;
      // Walk siblings to find the message-list scroller robustly.
      const candidates = Array.from(document.querySelectorAll('div.overflow-y-auto')) as HTMLElement[];
      const target = scroller ?? candidates.find((el) => el.scrollHeight > el.clientHeight) ?? candidates[0];
      if (target) {
        target.scrollTop = Math.max(0, target.scrollHeight - target.clientHeight);
      } else {
        window.scrollTo(0, document.body.scrollHeight);
      }
    });
    await authenticatedPage.waitForTimeout(250);
    const afterScrollBarBox = await progressBar.boundingBox();
    expect(
      afterScrollBarBox,
      'progress bar must still be on screen after the message list scrolls',
    ).not.toBeNull();
    if (initialBarBox && afterScrollBarBox) {
      // Allow ~1px slack for sub-pixel layout rounding.
      expect(
        Math.abs(afterScrollBarBox.y - initialBarBox.y),
        `progress bar y moved by ${afterScrollBarBox.y - initialBarBox.y}px when feed scrolled — bar is not fixed`,
      ).toBeLessThanOrEqual(1);
    }
    await expect(
      progressBar,
      'progress bar must remain visible after scrolling the message list',
    ).toBeVisible();

    await authenticatedPage.screenshot({
      path: 'e2e/screenshots/wizard-plan-card-002-mounted-and-stuck.png',
      fullPage: true,
    });

    // (3) Simulate the wizard reaching `done`. See SCOPE NOTE at the top
    // of the file — this dispatches the same CustomEvent that
    // `useChatSocket` emits for backend `wizard_stage` payloads, so the
    // bridge under test (useWizardFlow + UnifiedChat reducer) is exactly
    // the production code path.
    await authenticatedPage.evaluate(() => {
      window.dispatchEvent(
        new CustomEvent('lia:wizard-stage-payload', {
          detail: {
            type: 'wizard_stage',
            stage: 'done',
            data: {},
            completeness: 1,
            requires_approval: false,
          },
        }),
      );
    });

    // (4) The progress bar must tear down at the terminal stage
    // (`wizardActive` flips to false), but the plan card MUST stay in
    // the feed and visually flip to "Concluído" with every visible step
    // marked completed (Task #830). Before this fix the plan card
    // unmounted alongside the bar, leaving the recruiter wondering
    // whether the wizard had actually finished.
    await expect(
      progressBar,
      'progress bar must unmount once the wizard reaches `done`',
    ).toHaveCount(0, { timeout: 10_000 });

    await expect(
      planCard,
      'plan card must STAY visible once the wizard reaches `done` (Task #830)',
    ).toBeVisible({ timeout: 10_000 });

    await expect(
      planCard.getByText('Concluído', { exact: false }),
      'plan card title must surface the "Concluído" label at the terminal stage',
    ).toBeVisible({ timeout: 10_000 });

    // Every visible step in the plan card must be completed — no chip
    // can still show the "in progress" spinner once the wizard is done.
    await expect
      .poll(
        async () => {
          return planCard.evaluate((card) => {
            const spinners = card.querySelectorAll('svg.animate-spin');
            return spinners.length;
          });
        },
        {
          message:
            'plan card must not render any in-progress (spinning) chip after `done`',
          timeout: 10_000,
        },
      )
      .toBe(0);

    await authenticatedPage.screenshot({
      path: 'e2e/screenshots/wizard-plan-card-003-done.png',
      fullPage: true,
    });
  });
});
