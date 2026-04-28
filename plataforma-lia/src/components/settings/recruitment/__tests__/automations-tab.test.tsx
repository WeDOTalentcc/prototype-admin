/**
 * PR-AUTO — AutomationsTab API wiring tests (TDD red→green)
 *
 * Verifica que AutomationsTab busca automações da API real em vez de
 * usar dados hardcoded. Resolve achado P0 do audit enterprise (2026-04-26):
 * `useState` com 3 workflows falsos de 2024 — dados fantasma exibidos
 * ao recrutador como se fossem reais.
 *
 * Sensor computacional: este teste detecta regressão se alguém
 * reintroduzir dados hardcoded no componente.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => "/configuracoes/recruitment",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "test-company-123", isLoading: false }),
}));

vi.mock("@/utils/license-manager", () => ({
  hasModuleAccess: () => true,
}));

beforeAll(() => {
  if (typeof window !== "undefined" && !window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        matches: false, media: query, onchange: null,
        addEventListener: () => {}, removeEventListener: () => {},
        addListener: () => {}, removeListener: () => {},
        dispatchEvent: () => false,
      }),
    });
  }
  if (typeof window !== "undefined" && !(window as unknown as { ResizeObserver?: unknown }).ResizeObserver) {
    (window as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
      observe() {} unobserve() {} disconnect() {}
    };
  }
});

import { AutomationsTab } from "../automations-tab";

const MESSAGES = {
  settings: {
    recruitment: {
      automations: { title: "Automações", noAutomations: "Nenhuma automação" },
    },
  },
};

function renderWithIntl(ui: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={MESSAGES}>
      {ui}
    </NextIntlClientProvider>,
  );
}

// ── API response fixtures ────────────────────────────────────────────────

const MOCK_AUTOMATIONS = [
  {
    id: "auto-001",
    name: "Notificação Automática de Aprovação",
    description: "Envia email quando candidato é aprovado na triagem",
    trigger_type: "candidate_stage_changed",
    action_type: "send_email",
    is_active: true,
    executions_count: 42,
    last_executed_at: "2026-04-20T10:00:00Z",
    success_rate: 99,
  },
  {
    id: "auto-002",
    name: "Lembrete de Entrevista",
    description: "WhatsApp 24h antes da entrevista",
    trigger_type: "interview_scheduled",
    action_type: "send_whatsapp",
    is_active: false,
    executions_count: 0,
    last_executed_at: null,
    success_rate: 100,
  },
];

// ── Tests ────────────────────────────────────────────────────────────────

describe("AutomationsTab — API wiring (PR-AUTO)", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          data: { automations: MOCK_AUTOMATIONS, total: 2 },
        }),
      }),
    );
  });

  it("faz fetch para /api/backend-proxy/automations com company_id correto", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/backend-proxy/automations"),
      );
    });

    const url = (fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(url).toContain("company_id=test-company-123");
  });

  it("exibe nome da automação retornada pela API", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText("Notificação Automática de Aprovação");
    expect(
      screen.getByText("Notificação Automática de Aprovação"),
    ).toBeInTheDocument();
  });

  it("NÃO exibe dados hardcoded de 2024 ('Triagem Automática de Candidatos')", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      expect(
        screen.queryByText("Triagem Automática de Candidatos"),
      ).not.toBeInTheDocument();
    });
  });

  it("mapeia trigger_type para label legível", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      // candidate_stage_changed → "Candidato movimentado"
      expect(screen.getByText(/Candidato movimentado/i)).toBeInTheDocument();
    });
  });

  it("mapeia is_active=false para status Pausado", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      expect(screen.getByText("Pausado")).toBeInTheDocument();
    });
  });

  it("exibe estado vazio quando API retorna lista vazia", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true, data: { automations: [], total: 0 } }),
      }),
    );
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      expect(
        screen.getByText(/nenhuma automação/i),
      ).toBeInTheDocument();
    });
  });

  it("exibe estado de erro quando fetch falha", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network error")));
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      expect(
        screen.getByText(/não foi possível carregar/i),
      ).toBeInTheDocument();
    });
  });
});
