import { render, screen, fireEvent } from '@testing-library/react'
import type { Message } from '@/types/chat'

vi.mock('@/lib/utils', () => ({
  cn: (...args: (string | boolean | undefined | null)[]) => args.filter(Boolean).join(' '),
}))

vi.mock('@/stores/auth-store', () => ({
  useAuthStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ user: { name: 'Demo User', email: 'demo@test.com' } }),
}))

vi.mock('lucide-react', () => {
  const icon = (name: string) => (props: Record<string, unknown>) => (
    <span data-testid={`icon-${name}`} {...props} />
  )
  return {
    Loader2: icon('loader'),
    Clock: icon('clock'),
    Globe: icon('globe'),
    CheckCircle: icon('check'),
    XCircle: icon('x'),
  }
})

vi.mock('@/components/ui/avatar', () => ({
  Avatar: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AvatarFallback: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  AvatarImage: ({ src }: { src?: string }) => <img src={src} alt="" />,
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick}>{children}</button>
  ),
}))

vi.mock('@/components/ui/lia-icon', () => ({
  LIAIcon: () => <span data-testid="lia-icon" />,
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

vi.mock('@/components/ui/chat-status-indicators', () => ({
  ProgressSteps: () => null,
  CommandExecution: () => null,
  FileCreationIndicator: () => null,
  CompletionMessage: () => null,
}))

vi.mock('@/components/chat/action-result-card', () => ({
  ActionResultCard: () => <div data-testid="action-card" />,
}))

vi.mock('@/components/chat/plan-progress-card', () => ({
  PlanProgressCard: () => <div data-testid="plan-card" />,
}))

vi.mock('@/components/chat/typing-indicator', () => ({
  TypingIndicator: () => <div data-testid="typing-indicator" />,
}))

vi.mock('@/lib/sanitize', () => ({
  sanitizeHtml: (s: string) => s,
}))

import { ChatMessageList } from '../ChatMessageList'

const baseProps = {
  isLoading: false,
  searchTerm: '',
  currentMessageIndex: -1,
  messagesContainerClass: 'test-container',
  availableCredits: 100,
  onRenderChatCard: () => null,
  onHighlightSearchTerm: (text: string) => text,
  getRelativeTime: () => '2 min atrás',
  onLoadMoreCandidates: vi.fn(),
  onSendMessage: vi.fn(),
}

function makeMessage(overrides: Partial<Message> & { id: string; role: 'user' | 'lia'; content: string }): Message {
  return {
    timestamp: new Date().toISOString(),
    ...overrides,
  } as unknown as Message
}

describe('ChatMessageList — message rendering flow', () => {
  it('renders without crashing with empty messages', () => {
    expect(() =>
      render(<ChatMessageList messages={[]} {...baseProps} />)
    ).not.toThrow()
  })

  it('renders user message content', () => {
    const msgs = [
      makeMessage({ id: 'm1', role: 'user', content: 'Olá, preciso de ajuda' }),
    ]
    render(<ChatMessageList messages={msgs} {...baseProps} />)
    expect(screen.getByText('Olá, preciso de ajuda')).toBeTruthy()
  })

  it('renders LIA message content', () => {
    const msgs = [
      makeMessage({ id: 'm2', role: 'lia', content: 'Como posso ajudar?' }),
    ]
    const { container } = render(<ChatMessageList messages={msgs} {...baseProps} />)
    expect(container.innerHTML).toContain('Como posso ajudar?')
  })

  it('renders multiple messages in order', () => {
    const msgs = [
      makeMessage({ id: 'm1', role: 'user', content: 'Primeira mensagem' }),
      makeMessage({ id: 'm2', role: 'lia', content: 'Segunda mensagem' }),
      makeMessage({ id: 'm3', role: 'user', content: 'Terceira mensagem' }),
    ]
    const { container } = render(<ChatMessageList messages={msgs} {...baseProps} />)
    const html = container.innerHTML
    const pos1 = html.indexOf('Primeira mensagem')
    const pos2 = html.indexOf('Segunda mensagem')
    const pos3 = html.indexOf('Terceira mensagem')
    expect(pos1).toBeLessThan(pos2)
    expect(pos2).toBeLessThan(pos3)
  })

  it('shows user avatar initials', () => {
    const msgs = [
      makeMessage({ id: 'm1', role: 'user', content: 'test' }),
    ]
    render(<ChatMessageList messages={msgs} {...baseProps} />)
    expect(screen.getByText('DU')).toBeTruthy()
  })

  it('shows typing indicator when isLoading is true', () => {
    render(
      <ChatMessageList messages={[]} {...baseProps} isLoading={true} />
    )
    expect(screen.getByText(/digitando/i)).toBeTruthy()
  })
})
