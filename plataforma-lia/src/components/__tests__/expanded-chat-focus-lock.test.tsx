/**
 * ExpandedChatModal — Focus Trap Contract (A-08)
 *
 * Component-level (jsdom) test for the wrapper introduced in
 * `expanded-chat-modal.tsx`. We mirror the exact `react-focus-lock`
 * invocation used by the modal so this suite catches:
 *   - Tab / Shift+Tab cycling within the dialog (WCAG 2.1.2 / 2.4.3)
 *   - `disabled={inline}` honoring the inline embedding mode (no trap)
 *   - `returnFocus` restoring focus to the trigger when the dialog unmounts
 *
 * Rationale for not driving this through Playwright today: the
 * `ExpandedChatModal` wrapper component is not yet mounted from any
 * application route (it is a defensive surface prepared for upcoming
 * sprints — see `scripts/jira-create-cards.ts`). A jsdom test against a
 * minimal harness with the same wrapper config gives us deterministic
 * regression coverage without depending on a production trigger that
 * doesn't exist yet. The `@axe-core/playwright` spec
 * (`e2e/tests/wizard/wizard-a11y.spec.ts`) covers contrast on the live
 * wizard surface (A-09).
 */
import { useRef, useState } from 'react'

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FocusLock from 'react-focus-lock'
import { describe, it, expect } from 'vitest'

interface HarnessProps {
  inline?: boolean
}

function ModalHarness({ inline = false }: HarnessProps) {
  const [open, setOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)

  return (
    <div
      onKeyDown={(e) => {
        if (open && e.key === 'Escape') setOpen(false)
      }}
    >
      <button
        ref={triggerRef}
        data-testid="trigger"
        onClick={() => setOpen(true)}
      >
        Open
      </button>

      {open && (
        // Same invocation as expanded-chat-modal.tsx (lines 113–119).
        <FocusLock
          as="div"
          disabled={inline}
          returnFocus
          autoFocus
          className="contents"
        >
          <div role="dialog" aria-modal="true" aria-label="Chat">
            <button data-testid="dialog-1">B1</button>
            <button data-testid="dialog-2">B2</button>
            <button data-testid="dialog-3">B3</button>
          </div>
        </FocusLock>
      )}
    </div>
  )
}

describe('ExpandedChatModal — focus trap (A-08)', () => {
  it('Tab cycles inside the dialog and never escapes (modal mode)', async () => {
    const user = userEvent.setup()
    render(<ModalHarness />)

    await user.click(screen.getByTestId('trigger'))

    // FocusLock autoFocus should land on the first focusable inside the lock.
    expect(screen.getByTestId('dialog-1')).toHaveFocus()

    await user.tab()
    expect(screen.getByTestId('dialog-2')).toHaveFocus()

    await user.tab()
    expect(screen.getByTestId('dialog-3')).toHaveFocus()

    // Cycle: from last back to first — focus must NOT escape to <body> or trigger.
    await user.tab()
    expect(screen.getByTestId('dialog-1')).toHaveFocus()
    expect(screen.getByTestId('trigger')).not.toHaveFocus()
  })

  it('Shift+Tab cycles backwards inside the dialog', async () => {
    const user = userEvent.setup()
    render(<ModalHarness />)

    await user.click(screen.getByTestId('trigger'))
    expect(screen.getByTestId('dialog-1')).toHaveFocus()

    await user.tab({ shift: true })
    // Shift+Tab from first wraps to last inside the lock.
    expect(screen.getByTestId('dialog-3')).toHaveFocus()
    expect(screen.getByTestId('trigger')).not.toHaveFocus()
  })

  it('Escape closes the dialog and focus returns to the trigger', async () => {
    const user = userEvent.setup()
    render(<ModalHarness />)

    const trigger = screen.getByTestId('trigger')
    await user.click(trigger)
    expect(screen.queryByRole('dialog')).toBeInTheDocument()

    await user.keyboard('{Escape}')

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    // returnFocus prop on FocusLock restores focus to the originating trigger.
    expect(trigger).toHaveFocus()
  })

  it('inline mode disables the trap so Tab can leave the dialog', async () => {
    const user = userEvent.setup()
    render(
      <>
        <button data-testid="before">Before</button>
        <ModalHarness inline />
        <button data-testid="after">After</button>
      </>,
    )

    await user.click(screen.getByTestId('trigger'))
    // Without the lock, autoFocus does not steal focus into the dialog.
    // Tabbing forward from the trigger must reach the dialog buttons and
    // continue out to the next sibling, proving no trap is in effect.
    screen.getByTestId('trigger').focus()

    await user.tab()
    expect(screen.getByTestId('dialog-1')).toHaveFocus()
    await user.tab()
    expect(screen.getByTestId('dialog-2')).toHaveFocus()
    await user.tab()
    expect(screen.getByTestId('dialog-3')).toHaveFocus()
    await user.tab()
    // Focus exits the dialog because the lock is disabled.
    expect(screen.getByTestId('after')).toHaveFocus()
  })
})
