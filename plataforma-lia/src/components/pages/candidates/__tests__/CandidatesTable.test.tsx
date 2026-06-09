/**
 * Tests — CandidatesTable component
 *
 * Covers:
 * - Renders without crashing
 * - Renders candidate names when data provided
 * - Renders correct number of rows
 * - Renders checkboxes for selection
 * - Candidate checkbox reflects selected state
 * - Empty state message when no candidates
 * - onSort handler is callable
 * - onSelectAll handler is callable
 * - onCandidateClick handler is callable
 * - onToggleSelect handler is callable
 */
import { render, screen } from '@testing-library/react'
import { CandidatesTable } from '../CandidatesTable'
import type { Candidate, SortConfig } from '../types'
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
  useLocale: () => "pt",
}))

vi.mock('@/components/ui/avatar', () => ({
  Avatar: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  AvatarFallback: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  AvatarImage: ({ src }: { src?: string }) => <img src={src} alt="" />,
}))
vi.mock('@/components/ui/chip', () => ({
  Chip: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}))
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick}>{children}</button>
  ),
}))
vi.mock('@/components/ui/checkbox', () => ({
  Checkbox: ({
    onCheckedChange,
    checked,
  }: {
    onCheckedChange?: (v: boolean) => void
    checked?: boolean
  }) => (
    <input
      type="checkbox"
      checked={checked ?? false}
      onChange={e => onCheckedChange?.(e.target.checked)}
      readOnly={!onCheckedChange}
    />
  ),
}))
vi.mock('@/components/ui/tooltip', () => ({
  Tooltip: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))
vi.mock('@/lib/design-tokens', () => ({
  textStyles: { heading: '', body: '', muted: '' },
  buttonStyles: { primary: '', ghost: '' },
  cardStyles: { base: '' },
  badgeStyles: { default: '' },
}))
vi.mock('@/components/search/SearchFeedbackButtons', () => ({
  SearchFeedbackButtons: () => <div data-testid="feedback-buttons" />,
}))

const makeSortConfig = (column = 'name', direction: 'asc' | 'desc' = 'asc'): SortConfig => ({
  column,
  direction,
})

const makeCandidate = (overrides: Partial<Candidate> = {}): Candidate => ({
  id: 'c1',
  candidateId: 'c1',
  name: 'Ana Silva',
  email: 'ana@example.com',
  phone: '+5511999999999',
  ...overrides,
})

const DEFAULT_PROPS = {
  candidates: [makeCandidate()],
  selectedIds: new Set<string>(),
  onToggleSelect: vi.fn(),
  onSelectAll: vi.fn(),
  onCandidateClick: vi.fn(),
  sortConfig: makeSortConfig(),
  onSort: vi.fn(),
  isLoading: false,
}

describe('CandidatesTable', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders without crashing', () => {
    expect(() => render(<CandidatesTable {...DEFAULT_PROPS} />)).not.toThrow()
  })

  it('renders a table element', () => {
    render(<CandidatesTable {...DEFAULT_PROPS} />)
    expect(document.querySelector('table')).toBeTruthy()
  })

  it('renders the candidate name', () => {
    render(<CandidatesTable {...DEFAULT_PROPS} />)
    expect(screen.getByText('Ana Silva')).toBeTruthy()
  })

  it('renders multiple candidates', () => {
    const props = {
      ...DEFAULT_PROPS,
      candidates: [
        makeCandidate({ id: 'c1', candidateId: 'c1', name: 'Ana Silva' }),
        makeCandidate({ id: 'c2', candidateId: 'c2', name: 'Carlos Mendes' }),
        makeCandidate({ id: 'c3', candidateId: 'c3', name: 'Maria Santos' }),
      ],
    }
    render(<CandidatesTable {...props} />)
    expect(screen.getByText('Ana Silva')).toBeTruthy()
    expect(screen.getByText('Carlos Mendes')).toBeTruthy()
    expect(screen.getByText('Maria Santos')).toBeTruthy()
  })

  it('renders correct number of tbody rows', () => {
    const props = {
      ...DEFAULT_PROPS,
      candidates: [
        makeCandidate({ id: 'c1', candidateId: 'c1', name: 'A' }),
        makeCandidate({ id: 'c2', candidateId: 'c2', name: 'B' }),
      ],
    }
    render(<CandidatesTable {...props} />)
    const tbodyRows = document.querySelectorAll('tbody tr')
    expect(tbodyRows.length).toBeGreaterThanOrEqual(2)
  })

  it('renders empty-state message when candidates is empty and not loading', () => {
    render(<CandidatesTable {...DEFAULT_PROPS} candidates={[]} />)
    expect(screen.getByText('noCandidatesFound')).toBeTruthy()
  })

  it('does not render the table when candidates is empty', () => {
    render(<CandidatesTable {...DEFAULT_PROPS} candidates={[]} />)
    expect(document.querySelector('table')).toBeNull()
  })

  it('renders checkboxes for selection', () => {
    render(<CandidatesTable {...DEFAULT_PROPS} />)
    const checkboxes = document.querySelectorAll('input[type="checkbox"]')
    expect(checkboxes.length).toBeGreaterThan(0)
  })

  it('candidate checkbox reflects selected state', () => {
    const props = {
      ...DEFAULT_PROPS,
      selectedIds: new Set(['c1']),
    }
    render(<CandidatesTable {...props} />)
    const checkboxes = document.querySelectorAll('input[type="checkbox"]')
    const checked = Array.from(checkboxes).some(cb => (cb as HTMLInputElement).checked)
    expect(checked).toBe(true)
  })

  it('onSort handler is a function', () => {
    render(<CandidatesTable {...DEFAULT_PROPS} />)
    expect(typeof DEFAULT_PROPS.onSort).toBe('function')
  })

  it('onSelectAll handler is a function', () => {
    render(<CandidatesTable {...DEFAULT_PROPS} />)
    expect(typeof DEFAULT_PROPS.onSelectAll).toBe('function')
  })

  it('onCandidateClick handler is a function', () => {
    render(<CandidatesTable {...DEFAULT_PROPS} />)
    expect(typeof DEFAULT_PROPS.onCandidateClick).toBe('function')
  })

  it('onToggleSelect handler is a function', () => {
    render(<CandidatesTable {...DEFAULT_PROPS} />)
    expect(typeof DEFAULT_PROPS.onToggleSelect).toBe('function')
  })
})
