/**
 * AutomationLogsView — Sprint C canonical tests.
 *
 * 12 vitest specs cobrindo: filters, states (loading/error/empty/hint),
 * table render, drill-down modal, status filter, cyan canonical, PT-BR date.
 */

import { fireEvent, render, screen, within } from "@testing-library/react"
import { describe, expect, it, vi, beforeEach } from "vitest"

// ── Mocks ────────────────────────────────────────────────────────────

const mockUseAutomationsList = vi.fn()
const mockUseAutomationLogs = vi.fn()

vi.mock("@/hooks/automations/useAutomationMutations", () => ({
  useAutomationsList: () => mockUseAutomationsList(),
  useAutomationLogs: (id: string | null) => mockUseAutomationLogs(id),
}))

// Mock Radix Dialog para render previsivel em jsdom.
vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({
    open,
    children,
  }: {
    open: boolean
    onOpenChange?: (open: boolean) => void
    children: React.ReactNode
  }) => (open ? <div data-testid="mock-dialog">{children}</div> : null),
  DialogContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="mock-dialog-content">{children}</div>
  ),
  DialogHeader: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  DialogTitle: ({ children }: { children: React.ReactNode }) => (
    <h2>{children}</h2>
  ),
}))

import { AutomationLogsView } from "../AutomationLogsView"

// ── Fixtures ─────────────────────────────────────────────────────────

const AUTOMATIONS = [
  { id: "auto-1-uuid", name: "Triagem rapida" },
  { id: "auto-2-uuid", name: "Convite WSI" },
]

const LOGS = [
  {
    id: "log-1",
    automation_id: "auto-1-uuid",
    trigger_event: "candidate.applied",
    trigger_data: { source: "linkedin" },
    action_type: "send_whatsapp",
    candidate_id: "cand-aaaaaaaa-bbbb",
    candidate_name: "Maria Silva",
    status: "success" as const,
    execution_time_ms: 234,
    executed_at: "2026-05-20T14:30:00Z",
  },
  {
    id: "log-2",
    automation_id: "auto-1-uuid",
    trigger_event: "candidate.applied",
    action_type: "send_email",
    candidate_id: "cand-cccccccc-dddd",
    candidate_name: "Joao Souza",
    status: "failure" as const,
    error_message: "WhatsApp API timeout",
    execution_time_ms: 5012,
    executed_at: "2026-05-21T09:15:00Z",
  },
  {
    id: "log-3",
    automation_id: "auto-1-uuid",
    trigger_event: "candidate.applied",
    action_type: "tag_candidate",
    status: "skipped" as const,
    execution_time_ms: 12,
    executed_at: "2026-05-21T10:00:00Z",
  },
]

beforeEach(() => {
  mockUseAutomationsList.mockReturnValue({ data: AUTOMATIONS })
  mockUseAutomationLogs.mockReturnValue({
    data: undefined,
    isLoading: false,
    error: null,
  })
})

// ── Specs ────────────────────────────────────────────────────────────

describe("AutomationLogsView", () => {
  it("renderiza filters (automation select + status buttons)", () => {
    render(<AutomationLogsView />)
    expect(screen.getByTestId("filter-automation")).toBeInTheDocument()
    expect(screen.getByTestId("filter-status-all")).toBeInTheDocument()
    expect(screen.getByTestId("filter-status-success")).toBeInTheDocument()
    expect(screen.getByTestId("filter-status-failure")).toBeInTheDocument()
    expect(screen.getByTestId("filter-status-skipped")).toBeInTheDocument()
  })

  it("default 'Todas' mostra hint 'Selecione uma automacao'", () => {
    render(<AutomationLogsView />)
    expect(screen.getByTestId("logs-hint-select")).toBeInTheDocument()
    expect(screen.getByText(/Selecione uma automacao acima/i)).toBeInTheDocument()
  })

  it("default 'Todas' chama useAutomationLogs com null (disabled)", () => {
    render(<AutomationLogsView />)
    expect(mockUseAutomationLogs).toHaveBeenCalledWith(null)
  })

  it("selecionar automation specific chama hook com id", () => {
    render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    expect(mockUseAutomationLogs).toHaveBeenLastCalledWith("auto-1-uuid")
  })

  it("mostra loading state quando isLoading=true e automation selecionada", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    })
    render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    expect(screen.getByTestId("logs-loading")).toBeInTheDocument()
  })

  it("mostra error state quando hook retorna error", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Falha logs: 500"),
    })
    render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    expect(screen.getByTestId("logs-error")).toBeInTheDocument()
    expect(screen.getByText(/Falha logs: 500/)).toBeInTheDocument()
  })

  it("mostra empty state quando logs=[] e automation selecionada", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    })
    render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    expect(screen.getByTestId("logs-empty")).toBeInTheDocument()
    expect(
      screen.getByText(/ainda nao foi executada/i),
    ).toBeInTheDocument()
  })

  it("renderiza table com 3 logs mockados", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: LOGS,
      isLoading: false,
      error: null,
    })
    render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    expect(screen.getByTestId("logs-table")).toBeInTheDocument()
    expect(screen.getByTestId("log-row-log-1")).toBeInTheDocument()
    expect(screen.getByTestId("log-row-log-2")).toBeInTheDocument()
    expect(screen.getByTestId("log-row-log-3")).toBeInTheDocument()
    expect(screen.getByText("Maria Silva")).toBeInTheDocument()
    expect(screen.getByText("Joao Souza")).toBeInTheDocument()
  })

  it("click row abre detail modal com dados do log", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: LOGS,
      isLoading: false,
      error: null,
    })
    render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    fireEvent.click(screen.getByTestId("log-row-log-2"))
    const modal = screen.getByTestId("log-detail-modal")
    expect(modal).toBeInTheDocument()
    expect(within(modal).getByText("send_email")).toBeInTheDocument()
    expect(within(modal).getByText("candidate.applied")).toBeInTheDocument()
    expect(within(modal).getByText("5012ms")).toBeInTheDocument()
    expect(within(modal).getByText("WhatsApp API timeout")).toBeInTheDocument()
  })

  it("status filter 'success' filtra apenas logs com status=success", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: LOGS,
      isLoading: false,
      error: null,
    })
    render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    fireEvent.click(screen.getByTestId("filter-status-success"))
    expect(screen.getByTestId("log-row-log-1")).toBeInTheDocument()
    expect(screen.queryByTestId("log-row-log-2")).not.toBeInTheDocument()
    expect(screen.queryByTestId("log-row-log-3")).not.toBeInTheDocument()
  })

  it("filter status 'failure' inclui contexto no empty state", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: [LOGS[0]], // so success
      isLoading: false,
      error: null,
    })
    render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    fireEvent.click(screen.getByTestId("filter-status-failure"))
    expect(screen.getByTestId("logs-empty")).toBeInTheDocument()
    expect(screen.getByText(/status failure/i)).toBeInTheDocument()
  })

  it("aceita logsData em formato {logs: [...]} ou {items: [...]}", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: { logs: LOGS.slice(0, 1) },
      isLoading: false,
      error: null,
    })
    const { rerender } = render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    expect(screen.getByTestId("log-row-log-1")).toBeInTheDocument()

    mockUseAutomationLogs.mockReturnValue({
      data: { items: LOGS.slice(1, 2) },
      isLoading: false,
      error: null,
    })
    rerender(<AutomationLogsView />)
    expect(screen.getByTestId("log-row-log-2")).toBeInTheDocument()
  })

  it("cyan canonical aplicado em LIA Sparkles hint + status filter ativo", () => {
    render(<AutomationLogsView />)
    // Hint Sparkles tem text-wedo-cyan
    const hint = screen.getByTestId("logs-hint-select")
    expect(hint.querySelector(".text-wedo-cyan")).not.toBeNull()
    // Status filter "all" ativo por default → bg-wedo-cyan/10
    const activeBtn = screen.getByTestId("filter-status-all")
    expect(activeBtn.className).toMatch(/wedo-cyan/)
  })

  it("date formatado PT-BR (dd MMM HH:mm)", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: [LOGS[0]],
      isLoading: false,
      error: null,
    })
    render(<AutomationLogsView />)
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    // 2026-05-20T14:30:00Z → "20 mai" em PT-BR (locale ptBR de date-fns)
    const row = screen.getByTestId("log-row-log-1")
    expect(row.textContent).toMatch(/20 mai/i)
  })
})
