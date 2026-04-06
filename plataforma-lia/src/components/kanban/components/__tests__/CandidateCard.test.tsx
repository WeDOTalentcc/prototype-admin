import { render, screen, fireEvent } from '@testing-library/react'
import { CandidateCard } from '../CandidateCard'
import type { KanbanCandidate } from '../../types'

vi.mock('@/lib/utils', () => ({
  cn: (...args: (string | boolean | undefined | null)[]) => args.filter(Boolean).join(' '),
}))

vi.mock('@/lib/design-tokens', () => ({
  textStyles: { label: '' },
  buttonStyles: {},
  cardStyles: { container: '' },
  badgeStyles: {},
  formatScorePercent: (n: number | null) => (n != null ? `${Math.round(n)}%` : '—'),
}))

vi.mock('@/lib/recruitment-stages', () => ({
  isApplicationSource: (s: string) => s === 'application',
}))

vi.mock('@/components/candidate-profile/CandidateAvatar', () => ({
  CandidateAvatar: ({ name }: { name: string }) => (
    <div data-testid="candidate-avatar">{name}</div>
  ),
}))

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <div role="menuitem" onClick={onClick}>{children}</div>
  ),
  DropdownMenuTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuSeparator: () => <hr />,
  DropdownMenuLabel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

vi.mock('@/components/ui/score-icon-button', () => ({
  ScoreIconButton: ({ score }: { score: number | null }) => (
    <span data-testid="score-icon">{score}</span>
  ),
}))

vi.mock('@/components/ui/status-badge', () => ({
  WarningBadge: () => <span data-testid="warning-badge" />,
  SourceBadge: ({ source }: { source: string }) => <span data-testid="source-badge">{source}</span>,
  StatusBadge: () => <span data-testid="status-badge" />,
  ChannelBadge: () => <span data-testid="channel-badge" />,
  DateTimeBadge: () => <span data-testid="datetime-badge" />,
  OriginBadge: () => <span data-testid="origin-badge" />,
  AwaitingBadge: () => <span data-testid="awaiting-badge" />,
  HiredBadge: () => <span data-testid="hired-badge" />,
  OffLimitsBadge: () => <span data-testid="offlimits-badge" />,
}))

vi.mock('../CandidateBadges', () => ({
  CandidateBadges: () => <div data-testid="candidate-badges" />,
}))

vi.mock('../OverrideApproveButton', () => ({
  OverrideApproveButton: () => <button data-testid="override-btn" />,
}))

vi.mock('../../utils/badge-utils', () => ({
  SUB_STATUS_DISPLAY_MAP: {},
}))

vi.mock('lucide-react', () => {
  const icon = (name: string) => () => <span data-testid={`icon-${name}`} />
  return {
    MoreVertical: icon('more'),
    Eye: icon('eye'),
    Mail: icon('mail'),
    MessageCircle: icon('message'),
    Calendar: icon('calendar'),
    ClipboardList: icon('clipboard'),
    MessageSquareText: icon('msg-text'),
    Heart: icon('heart'),
    EyeOff: icon('eye-off'),
    Zap: icon('zap'),
    Briefcase: icon('briefcase'),
    Building: icon('building'),
    MapPin: icon('map-pin'),
    Gauge: icon('gauge'),
    BrainCircuit: icon('brain'),
    Target: icon('target'),
    Code: icon('code'),
    Globe: icon('globe'),
    Fingerprint: icon('fingerprint'),
  }
})

const mockCandidate: KanbanCandidate = {
  id: 'cand-1',
  name: 'Maria Silva',
  email: 'maria@test.com',
  currentTitle: 'Frontend Developer',
  currentCompany: 'TechCo',
  location: 'São Paulo, SP',
  score: 85,
  source: 'linkedin',
  origin: 'sourcing',
  stage: 'triagem',
  appliedDate: '2026-03-15',
}

describe('CandidateCard', () => {
  it('renders without crashing', () => {
    expect(() =>
      render(<CandidateCard candidate={mockCandidate} stageId="triagem" />)
    ).not.toThrow()
  })

  it('displays candidate name', () => {
    render(<CandidateCard candidate={mockCandidate} stageId="triagem" />)
    expect(screen.getAllByText('Maria Silva').length).toBeGreaterThanOrEqual(1)
  })

  it('renders CandidateAvatar with name', () => {
    render(<CandidateCard candidate={mockCandidate} stageId="triagem" />)
    expect(screen.getByTestId('candidate-avatar')).toBeTruthy()
  })

  it('calls onClick when card body is clicked', () => {
    const onClick = vi.fn()
    render(
      <CandidateCard
        candidate={mockCandidate}
        stageId="triagem"
        onClick={onClick}
      />
    )
    const nameEls = screen.getAllByText('Maria Silva')
    const nameEl = nameEls[nameEls.length - 1]
    fireEvent.click(nameEl.closest('[class]') || nameEl)
    expect(onClick).toHaveBeenCalled()
  })

  it('calls onSelect when checkbox is clicked', () => {
    const onSelect = vi.fn()
    render(
      <CandidateCard
        candidate={mockCandidate}
        stageId="triagem"
        onSelect={onSelect}
      />
    )
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)
    expect(onSelect).toHaveBeenCalledWith('cand-1')
  })

  it('renders with isSelected styling', () => {
    const { container } = render(
      <CandidateCard candidate={mockCandidate} stageId="triagem" isSelected />
    )
    const checkbox = screen.getByRole('checkbox') as HTMLInputElement
    expect(checkbox.checked).toBe(true)
  })

  it('shows badges component', () => {
    render(<CandidateCard candidate={mockCandidate} stageId="triagem" />)
    expect(screen.getByTestId('candidate-badges')).toBeTruthy()
  })
})
