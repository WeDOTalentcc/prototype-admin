import { render, screen, fireEvent } from '@testing-library/react'
import { KanbanBoard } from '../KanbanBoard'
import type { DynamicStage, KanbanCandidate, CandidatesDataMap } from '../../types'

vi.mock('@/lib/utils', () => ({
  cn: (...args: (string | boolean | undefined | null)[]) => args.filter(Boolean).join(' '),
}))

vi.mock('@/lib/design-tokens', () => ({
  textStyles: {},
  buttonStyles: {},
  cardStyles: {},
  badgeStyles: {},
  formatScorePercent: (n: number | null) => (n != null ? `${Math.round(n)}%` : '—'),
}))

vi.mock('@/lib/recruitment-stages', () => ({
  isApplicationSource: () => false,
}))

vi.mock('../../hooks', () => ({
  useDragDrop: () => ({
    draggedCandidate: null,
    dragOverColumn: null,
    handleDragStart: vi.fn(),
    handleDragEnd: vi.fn(),
    handleDragOver: vi.fn(),
    handleDragLeave: vi.fn(),
    handleDrop: vi.fn(),
    isDragging: false,
    isDragEnabled: true,
  }),
}))

vi.mock('../../utils/filter-utils', () => ({
  filterKanbanCandidates: (candidates: KanbanCandidate[]) => candidates,
}))

vi.mock('@/components/ui/checkbox', () => ({
  Checkbox: ({ onCheckedChange, checked, ...props }: Record<string, unknown>) => (
    <input
      type="checkbox"
      checked={!!checked}
      onChange={() => (onCheckedChange as (v: boolean) => void)?.(true)}
      {...props}
    />
  ),
}))

vi.mock('../CandidateCard', () => ({
  CandidateCard: ({ candidate, onClick }: { candidate: KanbanCandidate; onClick?: (c: KanbanCandidate) => void }) => (
    <div data-testid={`card-${candidate.id}`} onClick={() => onClick?.(candidate)}>
      {candidate.name}
    </div>
  ),
}))

vi.mock('../KanbanColumn', () => ({
  KanbanColumn: ({
    stage,
    candidates,
    onCandidateClick,
  }: {
    stage: DynamicStage
    candidates: KanbanCandidate[]
    onCandidateClick: (c: KanbanCandidate) => void
  }) => (
    <div data-testid={`column-${stage.id}`}>
      <div data-testid={`column-header-${stage.id}`}>{stage.displayName}</div>
      <div data-testid={`column-count-${stage.id}`}>{candidates.length}</div>
      {candidates.map((c) => (
        <div
          key={c.id}
          data-testid={`candidate-${c.id}`}
          onClick={() => onCandidateClick(c)}
        >
          {c.name}
        </div>
      ))}
    </div>
  ),
}))

const stages: DynamicStage[] = [
  {
    id: 'screening',
    name: 'screening',
    displayName: 'Triagem',
    order: 1,
    color: '#3B82F6',
    stageType: 'active',
    isInitial: true,
  },
  {
    id: 'interview',
    name: 'interview',
    displayName: 'Entrevista',
    order: 2,
    color: '#8B5CF6',
    stageType: 'active',
  },
  {
    id: 'hired',
    name: 'hired',
    displayName: 'Contratado',
    order: 3,
    color: '#10B981',
    stageType: 'final',
    isFinal: true,
    isHired: true,
  },
]

const makeCandidates = (count: number, stagePrefix: string): KanbanCandidate[] =>
  Array.from({ length: count }, (_, i) => ({
    id: `${stagePrefix}-${i}`,
    name: `Candidato ${stagePrefix} ${i + 1}`,
    stage: stagePrefix,
  }))

const candidatesData: CandidatesDataMap = {
  screening: makeCandidates(3, 'screening'),
  interview: makeCandidates(2, 'interview'),
  hired: makeCandidates(1, 'hired'),
}

describe('KanbanBoard — pipeline flow', () => {
  const onCandidateClick = vi.fn()
  const onCandidateQuickAction = vi.fn()

  beforeEach(() => vi.clearAllMocks())

  it('renders a column for each active stage', () => {
    render(
      <KanbanBoard
        stages={stages}
        candidatesData={candidatesData}
        selectedCandidates={new Set()}
        onCandidateClick={onCandidateClick}
        onCandidateQuickAction={onCandidateQuickAction}
      />
    )
    expect(screen.getByTestId('column-screening')).toBeTruthy()
    expect(screen.getByTestId('column-interview')).toBeTruthy()
  })

  it('renders final stage columns separately', () => {
    render(
      <KanbanBoard
        stages={stages}
        candidatesData={candidatesData}
        selectedCandidates={new Set()}
        onCandidateClick={onCandidateClick}
        onCandidateQuickAction={onCandidateQuickAction}
      />
    )
    expect(screen.getByTestId('column-hired')).toBeTruthy()
  })

  it('displays stage names in column headers', () => {
    render(
      <KanbanBoard
        stages={stages}
        candidatesData={candidatesData}
        selectedCandidates={new Set()}
        onCandidateClick={onCandidateClick}
        onCandidateQuickAction={onCandidateQuickAction}
      />
    )
    expect(screen.getByText('Triagem')).toBeTruthy()
    expect(screen.getByText('Entrevista')).toBeTruthy()
    expect(screen.getByText('Contratado')).toBeTruthy()
  })

  it('shows correct candidate count per column', () => {
    render(
      <KanbanBoard
        stages={stages}
        candidatesData={candidatesData}
        selectedCandidates={new Set()}
        onCandidateClick={onCandidateClick}
        onCandidateQuickAction={onCandidateQuickAction}
      />
    )
    expect(screen.getByTestId('column-count-screening').textContent).toBe('3')
    expect(screen.getByTestId('column-count-interview').textContent).toBe('2')
    expect(screen.getByTestId('column-count-hired').textContent).toBe('1')
  })

  it('renders candidate names inside their columns', () => {
    render(
      <KanbanBoard
        stages={stages}
        candidatesData={candidatesData}
        selectedCandidates={new Set()}
        onCandidateClick={onCandidateClick}
        onCandidateQuickAction={onCandidateQuickAction}
      />
    )
    expect(screen.getByText('Candidato screening 1')).toBeTruthy()
    expect(screen.getByText('Candidato interview 2')).toBeTruthy()
    expect(screen.getByText('Candidato hired 1')).toBeTruthy()
  })

  it('fires onCandidateClick when candidate is clicked', () => {
    render(
      <KanbanBoard
        stages={stages}
        candidatesData={candidatesData}
        selectedCandidates={new Set()}
        onCandidateClick={onCandidateClick}
        onCandidateQuickAction={onCandidateQuickAction}
      />
    )
    fireEvent.click(screen.getByTestId('candidate-screening-0'))
    expect(onCandidateClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'screening-0', name: 'Candidato screening 1' })
    )
  })

  it('renders empty columns when no candidates for a stage', () => {
    render(
      <KanbanBoard
        stages={stages}
        candidatesData={{ screening: [], interview: [], hired: [] }}
        selectedCandidates={new Set()}
        onCandidateClick={onCandidateClick}
        onCandidateQuickAction={onCandidateQuickAction}
      />
    )
    expect(screen.getByTestId('column-count-screening').textContent).toBe('0')
    expect(screen.getByTestId('column-count-interview').textContent).toBe('0')
  })
})
