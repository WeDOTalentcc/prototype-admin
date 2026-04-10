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

vi.mock('@/components/candidate-profile/CandidateAvatar', () => {
  function CandidateAvatar({ name }: { name: string }) {
    return <div data-testid="candidate-avatar">{name}</div>
  }
  return { CandidateAvatar }
})

vi.mock('@/components/ui/dropdown-menu', () => {
  function DropdownMenu({ children }: { children: React.ReactNode }) { return <div>{children}</div> }
  function DropdownMenuContent({ children }: { children: React.ReactNode }) { return <div>{children}</div> }
  function DropdownMenuItem({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) { return <div role="menuitem" onClick={onClick}>{children}</div> }
  function DropdownMenuTrigger({ children }: { children: React.ReactNode }) { return <div>{children}</div> }
  function DropdownMenuSeparator() { return <hr /> }
  function DropdownMenuLabel({ children }: { children: React.ReactNode }) { return <div>{children}</div> }
  return { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator, DropdownMenuLabel }
})

vi.mock('@/components/ui/score-icon-button', () => {
  function ScoreIconButton({ score }: { score: number | null }) { return <span data-testid="score-icon">{score}</span> }
  return { ScoreIconButton }
})

vi.mock('@/components/ui/status-badge', () => {
  function WarningBadge() { return <span data-testid="warning-badge" /> }
  function SourceBadge({ source }: { source: string }) { return <span data-testid="source-badge">{source}</span> }
  function StatusBadge() { return <span data-testid="status-badge" /> }
  function ChannelBadge() { return <span data-testid="channel-badge" /> }
  function DateTimeBadge() { return <span data-testid="datetime-badge" /> }
  function OriginBadge() { return <span data-testid="origin-badge" /> }
  function AwaitingBadge() { return <span data-testid="awaiting-badge" /> }
  function HiredBadge() { return <span data-testid="hired-badge" /> }
  function OffLimitsBadge() { return <span data-testid="offlimits-badge" /> }
  return { WarningBadge, SourceBadge, StatusBadge, ChannelBadge, DateTimeBadge, OriginBadge, AwaitingBadge, HiredBadge, OffLimitsBadge }
})

vi.mock('../CandidateBadges', () => {
  function CandidateBadges() { return <div data-testid="candidate-badges" /> }
  return { CandidateBadges }
})

vi.mock('../OverrideApproveButton', () => {
  function OverrideApproveButton() { return <button data-testid="override-btn" /> }
  return { OverrideApproveButton }
})

vi.mock('../../utils/badge-utils', () => ({
  SUB_STATUS_DISPLAY_MAP: {},
}))

vi.mock('lucide-react', () => {
  const icon = (name: string) => {
    const IconComponent = () => <span data-testid={`icon-${name}`} />
    IconComponent.displayName = name
    return IconComponent
  }
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

  it('calls onSelect when selection checkbox area is toggled', () => {
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
