/**
 * Tests — MessageBubble component
 *
 * Covers:
 * - Renders without crashing for user and LIA messages
 * - Correct alignment class (justify-end for user, justify-start for LIA)
 * - Renders message content text
 * - Renders Brain icon for LIA messages
 * - Does not render Brain icon for user messages
 * - Renders actionResult card when provided
 * - Handles empty content gracefully
 * - Applies custom className
 * - Renders correctly with and without showFeedback
 */
import { render, screen } from '@testing-library/react'
import { MessageBubble } from '../message-bubble'

vi.mock('@/lib/utils', () => ({
  cn: (...args: string[]) => args.filter(Boolean).join(' '),
}))
vi.mock('@/components/chat/action-result-card', () => ({
  ActionResultCard: ({ actionType }: { actionType: string }) => (
    <div data-testid="action-result-card">{actionType}</div>
  ),
}))
vi.mock('@/components/ui/avatar', () => ({
  Avatar: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AvatarImage: ({ src }: { src?: string }) => <img src={src} alt="" />,
  AvatarFallback: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}))
vi.mock('@/components/chat/message-feedback', () => ({
  MessageFeedback: () => <div data-testid="message-feedback" />,
}))
vi.mock('@/lib/chat-format', () => ({
  cleanAgentResponse: (s: string) => s,
  parseChatMarkdown: (s: string) => `<p>${s}</p>`,
  escapeHtml: (s: string) => s,
}))
vi.mock('lucide-react', () => ({
  User: () => <span data-testid="icon-user">user</span>,
  Brain: () => <span data-testid="icon-brain">brain</span>,
}))

const BASE_TIMESTAMP = '2026-03-30T10:00:00Z'

describe('MessageBubble', () => {
  // ── Rendering ─────────────────────────────────────────────────────────────

  it('renders without crashing (user message)', () => {
    expect(() =>
      render(
        <MessageBubble
          sender="user"
          content="Hello LIA"
          timestamp={BASE_TIMESTAMP}
        />
      )
    ).not.toThrow()
  })

  it('renders without crashing (LIA message)', () => {
    expect(() =>
      render(
        <MessageBubble
          sender="lia"
          content="Ola! Como posso ajudar?"
          timestamp={BASE_TIMESTAMP}
        />
      )
    ).not.toThrow()
  })

  // ── LIA message ───────────────────────────────────────────────────────────

  it('renders Brain icon for LIA messages', () => {
    render(
      <MessageBubble sender="lia" content="Hello" timestamp={BASE_TIMESTAMP} />
    )
    expect(screen.getByTestId('icon-brain')).toBeTruthy()
  })

  it('does not render Brain icon for user messages', () => {
    render(
      <MessageBubble sender="user" content="Hello" timestamp={BASE_TIMESTAMP} />
    )
    expect(screen.queryByTestId('icon-brain')).toBeNull()
  })

  it('LIA message container has justify-start class', () => {
    const { container } = render(
      <MessageBubble sender="lia" content="Hi" timestamp={BASE_TIMESTAMP} />
    )
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper?.className).toContain('justify-start')
  })

  it('user message container has justify-end class', () => {
    const { container } = render(
      <MessageBubble sender="user" content="Hi" timestamp={BASE_TIMESTAMP} />
    )
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper?.className).toContain('justify-end')
  })

  // ── Content rendering ─────────────────────────────────────────────────────

  it('renders user message content', () => {
    render(
      <MessageBubble sender="user" content="My question here" timestamp={BASE_TIMESTAMP} />
    )
    expect(screen.getByText(/My question here/)).toBeTruthy()
  })

  it('renders LIA message content via dangerouslySetInnerHTML', () => {
    const { container } = render(
      <MessageBubble sender="lia" content="Resposta importante" timestamp={BASE_TIMESTAMP} />
    )
    expect(container.innerHTML).toContain('Resposta importante')
  })

  it('handles empty content without crashing', () => {
    expect(() =>
      render(<MessageBubble sender="user" content="" timestamp={BASE_TIMESTAMP} />)
    ).not.toThrow()
  })

  it('handles multiline user content', () => {
    const { container } = render(
      <MessageBubble
        sender="user"
        content={"Line one\nLine two"}
        timestamp={BASE_TIMESTAMP}
      />
    )
    expect(container.innerHTML).toBeTruthy()
  })

  // ── Action result ─────────────────────────────────────────────────────────

  it('renders ActionResultCard when actionResult is provided', () => {
    render(
      <MessageBubble
        sender="lia"
        content="Done"
        timestamp={BASE_TIMESTAMP}
        actionResult={{ action_type: 'move_candidate', result: {} }}
      />
    )
    expect(screen.getByTestId('action-result-card')).toBeTruthy()
  })

  it('does not render ActionResultCard when actionResult is absent', () => {
    render(
      <MessageBubble sender="lia" content="Done" timestamp={BASE_TIMESTAMP} />
    )
    expect(screen.queryByTestId('action-result-card')).toBeNull()
  })

  it('passes action_type to ActionResultCard', () => {
    render(
      <MessageBubble
        sender="lia"
        content="Done"
        timestamp={BASE_TIMESTAMP}
        actionResult={{ action_type: 'send_email', result: {} }}
      />
    )
    expect(screen.getByText('send_email')).toBeTruthy()
  })

  // ── Feedback ──────────────────────────────────────────────────────────────

  it('renders MessageFeedback for LIA messages when showFeedback is true and ids provided', () => {
    render(
      <MessageBubble
        sender="lia"
        content="Response"
        timestamp={BASE_TIMESTAMP}
        showFeedback={true}
        sessionId="sess-1"
        messageId="msg-1"
      />
    )
    expect(screen.getByTestId('message-feedback')).toBeTruthy()
  })

  it('does not render MessageFeedback when showFeedback is false', () => {
    render(
      <MessageBubble
        sender="lia"
        content="Response"
        timestamp={BASE_TIMESTAMP}
        showFeedback={false}
        sessionId="sess-1"
        messageId="msg-1"
      />
    )
    expect(screen.queryByTestId('message-feedback')).toBeNull()
  })

  // ── Custom className ──────────────────────────────────────────────────────

  it('applies custom className to wrapper', () => {
    const { container } = render(
      <MessageBubble
        sender="user"
        content="Hi"
        timestamp={BASE_TIMESTAMP}
        className="custom-test-class"
      />
    )
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper?.className).toContain('custom-test-class')
  })
})
