/**
 * PR-Q1 — Rail A direct navigation + modal dispatch
 *
 * Cobre:
 * - NAVIGATION_OVERRIDES inclui "talent-pool" → router.push (sem onSelect)
 * - MODAL_OVERRIDES inclui "add-candidate" → lia:open_modal (sem onSelect)
 * - Cards normais continuam chamando onSelect (regressão)
 *
 * Harness:
 * - Guide computacional: NAVIGATION_OVERRIDES / MODAL_OVERRIDES eliminam
 *   detour pelo chat para ações que têm destino direto.
 * - Sensor computacional: esses testes detectam regressão silenciosa se
 *   navigate_url ou modal_id deixar de ser propagado.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { beforeAll, describe, expect, it, vi } from "vitest";

const mockRouterPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockRouterPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

beforeAll(() => {
  if (typeof window !== "undefined" && !window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addEventListener: () => {},
        removeEventListener: () => {},
        addListener: () => {},
        removeListener: () => {},
        dispatchEvent: () => false,
      }),
    });
  }
  if (
    typeof window !== "undefined" &&
    !(window as unknown as { ResizeObserver?: unknown }).ResizeObserver
  ) {
    (window as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  }
});

import {
  ChatWorkflowReels,
  MODAL_OVERRIDES,
  NAVIGATION_OVERRIDES,
} from "../chat-workflow-reels";

// ─── Messages mínimos para next-intl ─────────────────────────────────────
const messages = {
  chat: {
    workflowReels: {
      scrollLeft: "Rolar para esquerda",
      scrollRight: "Rolar para direita",
      stages: {
        "definir-vaga": { label: "Definir Vaga", shortLabel: "Vaga" },
        sourcing: { label: "Captação", shortLabel: "Captação" },
        triagem: { label: "Triagem", shortLabel: "Triagem" },
        entrevista: { label: "Entrevista", shortLabel: "Entrevista" },
        oferta: { label: "Oferta", shortLabel: "Oferta" },
        contratacao: { label: "Contratação", shortLabel: "Contratação" },
        analytics: { label: "Análises", shortLabel: "Análises" },
        "ia-automacoes": { label: "IA & Automações", shortLabel: "IA" },
        configuracoes: { label: "Configurações", shortLabel: "Config" },
      },
      suggestions: {
        "create-job": { title: "Criar nova vaga", description: "...", command: "Criar uma nova vaga" },
        "job-template": { title: "Usar modelo", description: "...", command: "Criar vaga a partir de template" },
        "search-candidates": { title: "Buscar", description: "...", command: "Buscar candidatos" },
        "add-candidate": { title: "Adicionar candidato", description: "...", command: "Adicione novo candidato" },
        "talent-pool": { title: "Banco de talentos", description: "...", command: "Mostrar meus bancos de talentos" },
        "candidate-info": { title: "Consultar", description: "...", command: "Consulte informações sobre candidato" },
        "update-status": { title: "Status", description: "...", command: "Atualize status do candidato" },
        "schedule-interview": { title: "Agendar", description: "...", command: "Agendar uma entrevista" },
        "reschedule-interview": { title: "Reagendar", description: "...", command: "Reagende uma entrevista" },
        "send-offer": { title: "Proposta", description: "...", command: "Enviar proposta para candidato" },
        "compare-candidates": { title: "Comparar", description: "...", command: "Comparar candidatos finalistas" },
        "register-hire": { title: "Registrar", description: "...", command: "Registrar contratação de candidato" },
        "close-vacancy": { title: "Encerrar", description: "...", command: "Encerrar vaga" },
        "job-report": { title: "Relatório", description: "...", command: "Gerar relatório da vaga" },
        "daily-briefing": { title: "Briefing", description: "...", command: "Me dê o briefing de hoje" },
        "hiring-predictions": { title: "Previsões", description: "...", command: "Mostrar previsões de contratação" },
        "configure-automations": { title: "Automações", description: "...", command: "Configurar automações de recrutamento" },
        "wsi-screening": { title: "WSI", description: "...", command: "Iniciar triagem WSI para candidatos" },
        "ai-suggestions": { title: "Sugestões", description: "...", command: "O que você sugere para minhas vagas?" },
        "ai-credits": { title: "Créditos IA", description: "...", command: "Verificar meus créditos de IA" },
        "hiring-policy": { title: "Política", description: "...", command: "Configurar política de contratação" },
        "email-templates": { title: "Templates", description: "...", command: "Gerenciar templates de email" },
      },
    },
    greeting: "Como posso ajudar hoje?",
    suggestionCount: "{label} — {count} sugestões",
    pulseBadge: "{count} candidatos",
  },
};

function renderWithIntl(ui: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

// ─── Static maps ─────────────────────────────────────────────────────────

describe("NAVIGATION_OVERRIDES — mapa de navegação direta", () => {
  it("inclui talent-pool → /bancos-de-talentos", () => {
    expect(NAVIGATION_OVERRIDES["talent-pool"]).toBe("/bancos-de-talentos");
  });

  it("inclui ai-credits → /configuracoes?section=consumo", () => {
    expect(NAVIGATION_OVERRIDES["ai-credits"]).toBe("/configuracoes?section=consumo");
  });

  it("inclui hiring-policy → /configuracoes?section=lia-personalizacao", () => {
    expect(NAVIGATION_OVERRIDES["hiring-policy"]).toBe("/configuracoes?section=lia-personalizacao");
  });

  it("inclui email-templates → /configuracoes?section=templates-assinatura", () => {
    expect(NAVIGATION_OVERRIDES["email-templates"]).toBe(
      "/configuracoes?section=templates-assinatura",
    );
  });

  it("tem exatamente 4 entradas", () => {
    expect(Object.keys(NAVIGATION_OVERRIDES)).toHaveLength(4);
  });
});

describe("MODAL_OVERRIDES — mapa de modais diretos", () => {
  it("inclui add-candidate → add_candidate", () => {
    expect(MODAL_OVERRIDES["add-candidate"]).toBe("add_candidate");
  });

  it("tem exatamente 2 entradas (add-candidate, create-job)", () => {
    expect(Object.keys(MODAL_OVERRIDES)).toHaveLength(2);
  });

  it("inclui create-job → create_job (abre CreateJobModal)", () => {
    expect(MODAL_OVERRIDES["create-job"]).toBe("create_job");
  });

  it("NÃO inclui job-template: 'Usar modelo' vai direto pra conversa (create_from_template)", () => {
    expect(MODAL_OVERRIDES["job-template"]).toBeUndefined();
  });
});

// ─── Integração: click handlers ──────────────────────────────────────────

describe("ChatWorkflowReels — clique em card com navigate_url chama router.push", () => {
  it("clicar em 'Banco de talentos' navega direto sem chamar onSelect", () => {
    const onSelect = vi.fn();
    mockRouterPush.mockClear();

    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} />);

    // Navegar para stage "Captação"
    const captacaoTab = screen.getByRole("button", { name: /Captação/i });
    fireEvent.click(captacaoTab);

    const card = screen.getByRole("button", { name: /Banco de talentos/i });
    fireEvent.click(card);

    expect(mockRouterPush).toHaveBeenCalledWith("/bancos-de-talentos");
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("modo compact também navega diretamente para talent-pool", () => {
    const onSelect = vi.fn();
    mockRouterPush.mockClear();

    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} compact />);

    const captacaoTab = screen.getByRole("button", { name: /Captação/i });
    fireEvent.click(captacaoTab);

    const card = screen.getByRole("button", { name: /Banco de talentos/i });
    fireEvent.click(card);

    expect(mockRouterPush).toHaveBeenCalledWith("/bancos-de-talentos");
    expect(onSelect).not.toHaveBeenCalled();
  });
});

describe("ChatWorkflowReels — clique em card com modal_id dispara lia:open_modal", () => {
  it("clicar em 'Adicionar candidato' dispara lia:open_modal com modal_id='add_candidate'", () => {
    const onSelect = vi.fn();
    const dispatchedEvents: CustomEvent[] = [];
    const originalDispatch = window.dispatchEvent.bind(window);
    const spyDispatch = vi.spyOn(window, "dispatchEvent").mockImplementation((e: Event) => {
      if ((e as CustomEvent).type === "lia:open_modal") {
        dispatchedEvents.push(e as CustomEvent);
      }
      return originalDispatch(e);
    });

    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} />);

    const captacaoTab = screen.getByRole("button", { name: /Captação/i });
    fireEvent.click(captacaoTab);

    const card = screen.getByRole("button", { name: /Adicionar candidato/i });
    fireEvent.click(card);

    const modalEvent = dispatchedEvents.find(
      (e) => e.type === "lia:open_modal" && e.detail?.modal_id === "add_candidate",
    );
    expect(modalEvent).toBeDefined();
    expect(onSelect).not.toHaveBeenCalled();

    spyDispatch.mockRestore();
  });

  it("modo compact também dispara lia:open_modal para add-candidate", () => {
    const onSelect = vi.fn();
    const dispatchedEvents: CustomEvent[] = [];
    const spyDispatch = vi.spyOn(window, "dispatchEvent").mockImplementation((e: Event) => {
      if ((e as CustomEvent).type === "lia:open_modal") {
        dispatchedEvents.push(e as CustomEvent);
      }
      return true;
    });

    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} compact />);

    const captacaoTab = screen.getByRole("button", { name: /Captação/i });
    fireEvent.click(captacaoTab);

    const card = screen.getByRole("button", { name: /Adicionar candidato/i });
    fireEvent.click(card);

    expect(dispatchedEvents.some((e) => e.detail?.modal_id === "add_candidate")).toBe(true);
    expect(onSelect).not.toHaveBeenCalled();

    spyDispatch.mockRestore();
  });
});

describe("ChatWorkflowReels — W1-3: create-job abre modal, não chama onSelect", () => {
  it("clicar em 'Criar nova vaga' (com modal_id) dispara lia:open_modal com create_job", () => {
    const onSelect = vi.fn();
    mockRouterPush.mockClear();

    const dispatchedEvents: CustomEvent[] = [];
    const spyDispatch = vi.spyOn(window, "dispatchEvent").mockImplementation((e: Event) => {
      if ((e as CustomEvent).type === "lia:open_modal") {
        dispatchedEvents.push(e as CustomEvent);
      }
      return true;
    });

    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} />);

    const card = screen.getByRole("button", { name: /Criar nova vaga/i });
    fireEvent.click(card);

    // W1-3: create-job fires lia:open_modal with modal_id="create_job"
    expect(dispatchedEvents.some((e) => e.detail?.modal_id === "create_job")).toBe(true);
    expect(onSelect).not.toHaveBeenCalled();
    expect(mockRouterPush).not.toHaveBeenCalled();

    spyDispatch.mockRestore();
  });

  it("clicar em 'Usar modelo' inicia conversa via onSelect (create_from_template), sem modal", () => {
    const onSelect = vi.fn();
    mockRouterPush.mockClear();

    const dispatchedEvents: CustomEvent[] = [];
    const spyDispatch = vi.spyOn(window, "dispatchEvent").mockImplementation((e: Event) => {
      if ((e as CustomEvent).type === "lia:open_modal") {
        dispatchedEvents.push(e as CustomEvent);
      }
      return true;
    });

    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} />);

    const card = screen.getByRole("button", { name: /Usar modelo/i });
    fireEvent.click(card);

    // job-template NÃO está em MODAL_OVERRIDES → fallback onSelect(command, metadata).
    expect(dispatchedEvents.some((e) => e.detail?.modal_id === "create_job")).toBe(false);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][1]).toMatchObject({
      card_id: "job-template",
      intent_hint: "create_from_template",
    });
    expect(mockRouterPush).not.toHaveBeenCalled();

    spyDispatch.mockRestore();
  });

  it("card genérico (search-candidates) ainda chama onSelect normalmente", () => {
    const onSelect = vi.fn();
    mockRouterPush.mockClear();

    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} />);

    // Navegar para stage "Captação"
    const captacaoTab = screen.getByRole("button", { name: /Captação/i });
    fireEvent.click(captacaoTab);

    const card = screen.getByRole("button", { name: /Buscar/i });
    fireEvent.click(card);

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(mockRouterPush).not.toHaveBeenCalled();
  });
});
