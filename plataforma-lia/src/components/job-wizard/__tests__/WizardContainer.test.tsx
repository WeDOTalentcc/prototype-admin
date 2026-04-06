import { render, screen, fireEvent } from '@testing-library/react'
import { WizardContainer } from '../WizardContainer'

vi.mock('@/lib/utils', () => ({
  cn: (...args: (string | boolean | undefined | null)[]) => args.filter(Boolean).join(' '),
}))

vi.mock('@/lib/pricing', () => ({
  CURRENCY_SYMBOL: 'R$',
}))

vi.mock('@/stores/wizard-store', () => ({
  useWizardStore: vi.fn(() => ({
    draft: null,
    draftId: null,
    setDraft: vi.fn(),
    setDraftId: vi.fn(),
    clearDraft: vi.fn(),
  })),
}))

vi.mock('@/hooks/useCompanyBenefits', () => ({
  useCompanyBenefits: () => ({
    benefits: [],
    isLoading: false,
    error: null,
  }),
}))

vi.mock('lucide-react', () => ({
  ChevronLeft: () => <span data-testid="icon-chevron-left" />,
  ChevronRight: () => <span data-testid="icon-chevron-right" />,
  Check: () => <span data-testid="icon-check" />,
  AlertTriangle: () => <span data-testid="icon-alert" />,
}))

describe('WizardContainer', () => {
  const onClose = vi.fn()
  const onMinimize = vi.fn()
  const onJobCreated = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    expect(() =>
      render(<WizardContainer onClose={onClose} />)
    ).not.toThrow()
  })

  it('displays header with LIA branding', () => {
    render(<WizardContainer onClose={onClose} />)
    expect(screen.getByText(/LIA.*Criação de Vaga/)).toBeTruthy()
  })

  it('shows all three phase labels', () => {
    render(<WizardContainer onClose={onClose} />)
    expect(screen.getByText('Construção')).toBeTruthy()
    expect(screen.getByText('Ativação')).toBeTruthy()
    expect(screen.getByText('Seleção')).toBeTruthy()
  })

  it('renders stage navigation with first stage active', () => {
    render(<WizardContainer onClose={onClose} />)
    expect(screen.getByText('Avaliação')).toBeTruthy()
  })

  it('shows progress indicator starting at 1', () => {
    render(<WizardContainer onClose={onClose} />)
    expect(screen.getByText(/1 de 7/)).toBeTruthy()
  })

  it('renders close button that calls onClose', () => {
    render(<WizardContainer onClose={onClose} />)
    const closeBtn = screen.getByLabelText('Fechar')
    fireEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('renders minimize button when onMinimize is provided', () => {
    render(<WizardContainer onClose={onClose} onMinimize={onMinimize} />)
    const minimizeBtn = screen.getByLabelText('Minimizar')
    fireEvent.click(minimizeBtn)
    expect(onMinimize).toHaveBeenCalledTimes(1)
  })

  it('does not render minimize button when onMinimize is absent', () => {
    render(<WizardContainer onClose={onClose} />)
    expect(screen.queryByLabelText('Minimizar')).toBeNull()
  })

  it('shows Voltar button disabled on first stage', () => {
    render(<WizardContainer onClose={onClose} />)
    const backBtn = screen.getByText('Voltar')
    expect(backBtn.closest('button')?.disabled).toBe(true)
  })

  it('shows Avançar button for non-review stages', () => {
    render(<WizardContainer onClose={onClose} />)
    expect(screen.getByText('Avançar')).toBeTruthy()
  })

  it('renders inline mode with rounded border', () => {
    const { container } = render(
      <WizardContainer onClose={onClose} inline />
    )
    expect(container.firstChild).toBeTruthy()
    const rootDiv = container.firstChild as HTMLElement
    expect(rootDiv.className).toContain('rounded-md')
  })
})
