/**
 * AutomationLogsView — Sprint C canonical tests + Sprint C.5 CSV export.
 *
 * Filters, states (loading/error/empty/hint), table render, drill-down modal,
 * status filter, cyan canonical, PT-BR date, CSV export (LGPD audit trail).
 */

import { fireEvent, render, screen, within } from "@testing-library/react"
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { NextIntlClientProvider } from "next-intl"
import ptBRMessages from "../../../../../messages/pt-BR.json"

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

import { AutomationLogsView, exportLogsToCsv } from "../AutomationLogsView"

function renderView() {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages}>
      <AutomationLogsView />
    </NextIntlClientProvider>,
  )
}

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
    renderView()
    expect(screen.getByTestId("filter-automation")).toBeInTheDocument()
    expect(screen.getByTestId("filter-status-all")).toBeInTheDocument()
    expect(screen.getByTestId("filter-status-success")).toBeInTheDocument()
    expect(screen.getByTestId("filter-status-failure")).toBeInTheDocument()
    expect(screen.getByTestId("filter-status-skipped")).toBeInTheDocument()
  })

  it("default Todas mostra hint Selecione uma automacao", () => {
    renderView()
    expect(screen.getByTestId("logs-hint-select")).toBeInTheDocument()
    expect(screen.getByText(/Selecione uma automacao acima/i)).toBeInTheDocument()
  })

  it("default Todas chama useAutomationLogs com null (disabled)", () => {
    renderView()
    expect(mockUseAutomationLogs).toHaveBeenCalledWith(null)
  })

  it("selecionar automation specific chama hook com id", () => {
    renderView()
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
    renderView()
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
    renderView()
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
    renderView()
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    expect(screen.getByTestId("logs-empty")).toBeInTheDocument()
    expect(screen.getByText(/ainda nao foi executada/i)).toBeInTheDocument()
  })

  it("renderiza table com 3 logs mockados", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: LOGS,
      isLoading: false,
      error: null,
    })
    renderView()
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
    renderView()
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

  it("status filter success filtra apenas logs com status=success", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: LOGS,
      isLoading: false,
      error: null,
    })
    renderView()
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    fireEvent.click(screen.getByTestId("filter-status-success"))
    expect(screen.getByTestId("log-row-log-1")).toBeInTheDocument()
    expect(screen.queryByTestId("log-row-log-2")).not.toBeInTheDocument()
    expect(screen.queryByTestId("log-row-log-3")).not.toBeInTheDocument()
  })

  it("filter status failure inclui contexto no empty state", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: [LOGS[0]],
      isLoading: false,
      error: null,
    })
    renderView()
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    fireEvent.click(screen.getByTestId("filter-status-failure"))
    expect(screen.getByTestId("logs-empty")).toBeInTheDocument()
    expect(screen.getByText(/status failure/i)).toBeInTheDocument()
  })

  it("aceita logsData em formato {logs:[...]} ou {items:[...]}", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: { logs: LOGS.slice(0, 1) },
      isLoading: false,
      error: null,
    })
    const { rerender } = renderView()
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    expect(screen.getByTestId("log-row-log-1")).toBeInTheDocument()

    mockUseAutomationLogs.mockReturnValue({
      data: { items: LOGS.slice(1, 2) },
      isLoading: false,
      error: null,
    })
    rerender(
      <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages}>
        <AutomationLogsView />
      </NextIntlClientProvider>,
    )
    expect(screen.getByTestId("log-row-log-2")).toBeInTheDocument()
  })

  it("cyan canonical aplicado em LIA Sparkles hint + status filter ativo", () => {
    renderView()
    const hint = screen.getByTestId("logs-hint-select")
    expect(hint.querySelector(".text-wedo-cyan")).not.toBeNull()
    const activeBtn = screen.getByTestId("filter-status-all")
    expect(activeBtn.className).toMatch(/wedo-cyan/)
  })

  it("date formatado PT-BR (dd MMM HH:mm)", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: [LOGS[0]],
      isLoading: false,
      error: null,
    })
    renderView()
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    const row = screen.getByTestId("log-row-log-1")
    expect(row.textContent).toMatch(/20 mai/i)
  })
})

// ── Sprint C.5: CSV export ──────────────────────────────────────────

describe("AutomationLogsView — CSV export (LGPD audit trail)", () => {
  const createObjectURLSpy = vi.fn(() => "blob:mock-url")
  const revokeObjectURLSpy = vi.fn()
  const clickSpy = vi.fn()
  let appendedAnchors: HTMLAnchorElement[] = []

  beforeEach(() => {
    appendedAnchors = []
    createObjectURLSpy.mockClear()
    revokeObjectURLSpy.mockClear()
    clickSpy.mockClear()
    // @ts-expect-error jsdom URL stub
    global.URL.createObjectURL = createObjectURLSpy
    // @ts-expect-error jsdom URL stub
    global.URL.revokeObjectURL = revokeObjectURLSpy
    const origCreate = document.createElement.bind(document)
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      const el = origCreate(tag) as HTMLElement
      if (tag === "a") {
        ;(el as HTMLAnchorElement).click = clickSpy
        appendedAnchors.push(el as HTMLAnchorElement)
      }
      return el as unknown as HTMLElement
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("botao Exportar CSV renderizado e desabilitado quando sem logs", () => {
    renderView()
    const btn = screen.getByTestId("export-csv-btn") as HTMLButtonElement
    expect(btn).toBeInTheDocument()
    expect(btn.disabled).toBe(true)
  })

  it("botao habilitado quando ha logs filtrados; click dispara download CSV", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: LOGS,
      isLoading: false,
      error: null,
    })
    renderView()
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    const btn = screen.getByTestId("export-csv-btn") as HTMLButtonElement
    expect(btn.disabled).toBe(false)
    fireEvent.click(btn)
    expect(createObjectURLSpy).toHaveBeenCalledTimes(1)
    expect(clickSpy).toHaveBeenCalledTimes(1)
    const anchor = appendedAnchors[appendedAnchors.length - 1]
    expect(anchor.download).toMatch(/^automation-logs-\d{4}-\d{2}-\d{2}\.csv$/)
    expect(revokeObjectURLSpy).toHaveBeenCalledTimes(1)
  })

  it("filename respeita filtro de status (subset visivel)", () => {
    mockUseAutomationLogs.mockReturnValue({
      data: LOGS,
      isLoading: false,
      error: null,
    })
    renderView()
    fireEvent.change(screen.getByTestId("filter-automation"), {
      target: { value: "auto-1-uuid" },
    })
    fireEvent.click(screen.getByTestId("filter-status-success"))
    const btn = screen.getByTestId("export-csv-btn") as HTMLButtonElement
    fireEvent.click(btn)
    // 1 row visivel (status=success) → 1 export → createObjectURL chamado uma vez
    expect(createObjectURLSpy).toHaveBeenCalledTimes(1)
  })
})

// ── exportLogsToCsv helper: escape edge cases ────────────────────────

describe("exportLogsToCsv — escape canonical", () => {
  const headers = {
    executedAt: "Executado em",
    automation: "Automação",
    trigger: "Gatilho",
    status: "Status",
    candidate: "Candidato",
    error: "Mensagem de erro",
  }

  let capturedBlob: Blob | null = null
  const createObjectURLSpy = vi.fn((b: Blob) => {
    capturedBlob = b
    return "blob:mock"
  })

  beforeEach(() => {
    capturedBlob = null
    createObjectURLSpy.mockClear()
    // @ts-expect-error stub
    global.URL.createObjectURL = createObjectURLSpy
    // @ts-expect-error stub
    global.URL.revokeObjectURL = vi.fn()
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      const el = document.createElementNS("http://www.w3.org/1999/xhtml", tag) as unknown as HTMLElement
      if (tag === "a") {
        ;(el as HTMLAnchorElement).click = vi.fn()
      }
      return el as unknown as HTMLElement
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  async function readBlobText(): Promise<string> {
    if (!capturedBlob) return ""
    return await capturedBlob.text()
  }

  it("escapa virgulas envolvendo a celula em aspas", async () => {
    exportLogsToCsv(
      [
        {
          id: "x1",
          automation_id: "a",
          trigger_event: "evt",
          action_type: "act",
          candidate_name: "Silva, Maria",
          status: "success",
          execution_time_ms: 1,
          executed_at: "2026-01-01T00:00:00Z",
        },
      ],
      headers,
      "test.csv",
    )
    const text = await readBlobText()
    expect(text).toContain(`"Silva, Maria"`)
  })

  it("escapa aspas duplicando-as e envolvendo a celula", async () => {
    exportLogsToCsv(
      [
        {
          id: "x2",
          automation_id: "a",
          trigger_event: "evt",
          action_type: "act",
          candidate_name: `Joao "O Cara" Silva`,
          status: "success",
          execution_time_ms: 1,
          executed_at: "2026-01-01T00:00:00Z",
        },
      ],
      headers,
      "test.csv",
    )
    const text = await readBlobText()
    expect(text).toContain(`"Joao ""O Cara"" Silva"`)
  })

  it("escapa quebras de linha em error_message", async () => {
    exportLogsToCsv(
      [
        {
          id: "x3",
          automation_id: "a",
          trigger_event: "evt",
          action_type: "act",
          status: "failure",
          error_message: "Linha 1\nLinha 2",
          execution_time_ms: 1,
          executed_at: "2026-01-01T00:00:00Z",
        },
      ],
      headers,
      "test.csv",
    )
    const text = await readBlobText()
    expect(text).toMatch(/"Linha 1\nLinha 2"/)
  })

  it("inclui UTF-8 BOM nos bytes do blob para Excel reconhecer acentos", async () => {
    exportLogsToCsv(
      [
        {
          id: "bomtest",
          automation_id: "a",
          trigger_event: "e",
          action_type: "x",
          status: "success" as const,
          execution_time_ms: 1,
          executed_at: "2026-01-01T00:00:00Z",
        },
      ],
      headers,
      "test.csv",
    )
    expect(capturedBlob).not.toBeNull()
    const buf = await capturedBlob!.arrayBuffer()
    const view = new Uint8Array(buf)
    expect(view[0]).toBe(0xef)
    expect(view[1]).toBe(0xbb)
    expect(view[2]).toBe(0xbf)
  })

  it("retorna numero de registros exportados", () => {
    const n = exportLogsToCsv(
      [
        {
          id: "y1",
          automation_id: "a",
          trigger_event: "e",
          action_type: "x",
          status: "success",
          execution_time_ms: 1,
          executed_at: "2026-01-01T00:00:00Z",
        },
        {
          id: "y2",
          automation_id: "a",
          trigger_event: "e",
          action_type: "x",
          status: "skipped",
          execution_time_ms: 1,
          executed_at: "2026-01-01T00:00:00Z",
        },
      ],
      headers,
      "test.csv",
    )
    expect(n).toBe(2)
  })
})

// ── i18n canonical contract ────────────────────────────────────────

describe("AutomationLogsView — i18n canonical contract", () => {
  it("nao emite MISSING_MESSAGE para keys de CSV export em pt-BR", () => {
    const errors: Array<{ message?: string }> = []
    render(
      <NextIntlClientProvider
        locale="pt-BR"
        messages={ptBRMessages}
        onError={(err) => errors.push(err as { message?: string })}
      >
        <AutomationLogsView />
      </NextIntlClientProvider>,
    )
    const missing = errors.filter(
      (e) => e.message?.includes("MISSING_MESSAGE") ?? false,
    )
    expect(missing).toEqual([])
  })
})
