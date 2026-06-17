/**
 * PR-A — Rail A metadata routing
 *
 * Cobre o fix de FE-H03 (audit enterprise 2026-04-26): ao clicar num card do
 * Rail A, o `onSelect` deve receber `(command, metadata)` onde `metadata`
 * carrega `source: "rail_a"`, `card_id`, `stage`, `domain_hint` e `intent_hint`.
 *
 * Esses hints são consumidos pelo orchestrator (`main_orchestrator.py`)
 * como **guide computacional** (per harness-engineering): rota determinística
 * para o domínio/action correto antes do fallback keyword-based.
 *
 * Skill: lia-testing PARTE 1 (TDD red→green) + harness-engineering (guide).
 */

import { fireEvent, render, screen } from "@testing-library/react";

// Phase 4J post-cherry-pick fix: ChatWorkflowReels uses useRouter() (added by
// later commit PR-Q1 direct nav). This test was authored before that change
// and lacks Next.js router mock — without it, render() fails with
// "invariant expected app router to be mounted".
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));
import { NextIntlClientProvider } from "next-intl";
import { beforeAll, describe, expect, it, vi } from "vitest";

// jsdom não implementa matchMedia — mock global p/ useDockMagnifier (prefers-reduced-motion).
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
  // ResizeObserver tampouco existe — stub mínimo.
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
  type ChatSuggestionMetadata,
  ChatWorkflowReels,
  SUGGESTION_HINTS,
  buildSuggestionMetadata,
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
        "create-job": {
          title: "Criar nova vaga",
          description: "...",
          command: "Criar uma nova vaga",
        },
        "job-template": {
          title: "Usar modelo",
          description: "...",
          command: "Criar vaga a partir de template",
        },
        "search-candidates": {
          title: "Buscar",
          description: "...",
          command: "Buscar candidatos",
        },
        "add-candidate": {
          title: "Adicionar",
          description: "...",
          command: "Adicione novo candidato",
        },
        "talent-pool": {
          title: "Banco",
          description: "...",
          command: "Mostrar meus bancos de talentos",
        },
        "candidate-info": {
          title: "Consultar",
          description: "...",
          command: "Consulte informações sobre candidato",
        },
        "update-status": {
          title: "Status",
          description: "...",
          command: "Atualize status do candidato",
        },
        "schedule-interview": {
          title: "Agendar",
          description: "...",
          command: "Agendar uma entrevista",
        },
        "reschedule-interview": {
          title: "Reagendar",
          description: "...",
          command: "Reagende uma entrevista",
        },
        "send-offer": {
          title: "Proposta",
          description: "...",
          command: "Enviar proposta para candidato",
        },
        "compare-candidates": {
          title: "Comparar",
          description: "...",
          command: "Comparar candidatos finalistas",
        },
        "register-hire": {
          title: "Registrar",
          description: "...",
          command: "Registrar contratação de candidato",
        },
        "close-vacancy": {
          title: "Encerrar",
          description: "...",
          command: "Encerrar vaga",
        },
        "job-report": {
          title: "Relatório",
          description: "...",
          command: "Gerar relatório da vaga",
        },
        "daily-briefing": {
          title: "Briefing",
          description: "...",
          command: "Me dê o briefing de hoje",
        },
        "hiring-predictions": {
          title: "Previsões",
          description: "...",
          command: "Mostrar previsões de contratação",
        },
        "configure-automations": {
          title: "Automações",
          description: "...",
          command: "Configurar automações de recrutamento",
        },
        "wsi-screening": {
          title: "WSI",
          description: "...",
          command: "Iniciar triagem WSI para candidatos",
        },
        "ai-suggestions": {
          title: "Sugestões",
          description: "...",
          command: "O que você sugere para minhas vagas?",
        },
        "ai-credits": {
          title: "Créditos",
          description: "...",
          command: "Verificar meus créditos de IA",
        },
        "hiring-policy": {
          title: "Política",
          description: "...",
          command: "Configurar política de contratação",
        },
        "email-templates": {
          title: "Templates",
          description: "...",
          command: "Gerenciar templates de email",
        },
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

// ─── Pure function: buildSuggestionMetadata ──────────────────────────────

describe("buildSuggestionMetadata — pure metadata constructor", () => {
  it("monta metadata completa para card 1.1 (create-job)", () => {
    expect(buildSuggestionMetadata("create-job", "definir-vaga")).toEqual({
      source: "rail_a",
      card_id: "create-job",
      stage: "definir-vaga",
      domain_hint: "job_management",
      intent_hint: "create_job",
    } satisfies ChatSuggestionMetadata);
  });

  it("monta metadata para card 6.2 (close-vacancy)", () => {
    expect(buildSuggestionMetadata("close-vacancy", "contratacao")).toEqual({
      source: "rail_a",
      card_id: "close-vacancy",
      stage: "contratacao",
      domain_hint: "job_management",
      intent_hint: "close_job",
    });
  });

  it("monta metadata para card utilitário 9.2 (hiring-policy)", () => {
    expect(buildSuggestionMetadata("hiring-policy", "configuracoes")).toEqual({
      source: "rail_a",
      card_id: "hiring-policy",
      stage: "configuracoes",
      domain_hint: "hiring_policy",
      intent_hint: "configure_policy",
    });
  });

  it("retorna metadata sem hints quando card não tem mapeamento (defensivo)", () => {
    const m = buildSuggestionMetadata("unknown-card", "definir-vaga");
    expect(m.source).toBe("rail_a");
    expect(m.card_id).toBe("unknown-card");
    expect(m.stage).toBe("definir-vaga");
    expect(m.domain_hint).toBeUndefined();
    expect(m.intent_hint).toBeUndefined();
  });
});

// ─── Cobertura completa: 22 cards × hints válidos ────────────────────────

describe("SUGGESTION_HINTS — completude do mapa de 22 cards", () => {
  const expectedCards = [
    // Funil (13)
    { id: "create-job", domain: "job_management", intent: "create_job" },
    {
      id: "job-template",
      domain: "job_management",
      intent: "create_from_template",
    },
    {
      id: "search-candidates",
      domain: "sourcing",
      intent: "search_candidates",
    },
    { id: "add-candidate", domain: "sourcing", intent: "add_candidate" },
    { id: "talent-pool", domain: "talent_pool", intent: "list_talent_pools" },
    {
      id: "candidate-info",
      domain: "recruiter_assistant",
      intent: "quick_question",
    },
    { id: "update-status", domain: "pipeline", intent: "move_candidate" },
    {
      id: "schedule-interview",
      domain: "interview_scheduling",
      intent: "schedule_interview",
    },
    {
      id: "reschedule-interview",
      domain: "interview_scheduling",
      intent: "reschedule_interview",
    },
    { id: "send-offer", domain: "offer", intent: "send_offer" }, // PR-B implemented
    {
      id: "compare-candidates",
      domain: "sourcing",
      intent: "compare_candidates",
    },
    { id: "register-hire", domain: "pipeline", intent: "register_hire" }, // PR-C implemented
    { id: "close-vacancy", domain: "job_management", intent: "close_job" },
    // Utilitárias (9)
    { id: "job-report", domain: "analytics", intent: "generate_job_report" },
    {
      id: "daily-briefing",
      domain: "recruiter_assistant",
      intent: "daily_briefing",
    },
    { id: "hiring-predictions", domain: "analytics", intent: "forecast" },
    {
      id: "configure-automations",
      domain: "automation",
      intent: "create_automation",
    },
    {
      id: "wsi-screening",
      domain: "interview_scheduling",
      intent: "start_wsi_interview",
    },
    {
      id: "ai-suggestions",
      domain: "recruiter_assistant",
      intent: "suggest_action",
    },
    {
      id: "ai-credits",
      domain: "agent_studio",
      intent: "get_studio_consumption",
    },
    {
      id: "hiring-policy",
      domain: "hiring_policy",
      intent: "configure_policy",
    },
    {
      id: "email-templates",
      domain: "communication",
      intent: "create_template",
    },
  ];

  it("tem entrada para os 22 cards do Rail A", () => {
    expect(Object.keys(SUGGESTION_HINTS)).toHaveLength(22);
  });

  it.each(expectedCards)(
    "card $id roteia para domain=$domain intent=$intent",
    ({ id, domain, intent }) => {
      const hint = SUGGESTION_HINTS[id];
      expect(hint).toBeDefined();
      expect(hint.domain_hint).toBe(domain);
      expect(hint.intent_hint).toBe(intent);
    },
  );
});

// ─── Integração: click envia metadata via onSelect ───────────────────────

describe("ChatWorkflowReels — click handler (PR-Q1 direct nav + MODAL_OVERRIDES)", () => {
  /**
   * Post PR-Q1: click handler has 3 paths (priority order):
   *   1. NAVIGATION_OVERRIDES → router.push (direct nav)
   *   2. MODAL_OVERRIDES → lia:open_modal CustomEvent
   *   3. fallback → onSelect(command, metadata)
   *
   * "create-job" is in MODAL_OVERRIDES (modal_id: "create_job"), so clicking
   * it dispatches the modal event instead of calling onSelect. The test
   * below verifies this canonical path.
   */
  it("clique no card 'Criar nova vaga' dispara lia:open_modal (PR-Q1)", () => {
    const onSelect = vi.fn();
    const dispatchSpy = vi.spyOn(window, "dispatchEvent");
    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} />);

    const card = screen.getByRole("button", { name: /Criar nova vaga/i });
    fireEvent.click(card);

    // create-job tem modal_id="create_job" → dispatch lia:open_modal,
    // NÃO chama onSelect (PR-Q1 direct dispatch).
    expect(onSelect).not.toHaveBeenCalled();

    // Eventos disparados: lia:rail-a-card-click (analytics) + lia:open_modal
    const openModalCall = dispatchSpy.mock.calls.find(
      (c) => (c[0] as CustomEvent).type === "lia:open_modal",
    );
    expect(openModalCall).toBeDefined();
    expect((openModalCall![0] as CustomEvent).detail).toMatchObject({
      modal_id: "create_job",
    });

    dispatchSpy.mockRestore();
  });

  it("modo compact: clique em 'Criar nova vaga' dispara lia:open_modal", () => {
    const onSelect = vi.fn();
    const dispatchSpy = vi.spyOn(window, "dispatchEvent");
    renderWithIntl(<ChatWorkflowReels onSelect={onSelect} compact />);

    const card = screen.getByRole("button", { name: /Criar nova vaga/i });
    fireEvent.click(card);

    expect(onSelect).not.toHaveBeenCalled();

    const openModalCall = dispatchSpy.mock.calls.find(
      (c) => (c[0] as CustomEvent).type === "lia:open_modal",
    );
    expect(openModalCall).toBeDefined();
    expect((openModalCall![0] as CustomEvent).detail).toMatchObject({
      modal_id: "create_job",
    });

    dispatchSpy.mockRestore();
  });
});
