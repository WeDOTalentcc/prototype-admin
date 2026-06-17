/**
 * PR-D — useUIAction hook tests
 *
 * Cobre o fix de UI-S03 (audit enterprise 2026-04-26): hook unificado
 * que despacha UIActions globais e re-emite as não-tratadas via
 * `lia:unhandled_ui_action` CustomEvent (fallback p/ handlers page-specific).
 *
 * Skill: lia-testing PARTE 1 (TDD red→green).
 */

import { useUIAction } from "@/hooks/chat/useUIAction";
import {
  UNHANDLED_UI_ACTION_EVENT,
  type UnhandledUIActionEventDetail,
} from "@/types/ui-action";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ─── Mocks ───────────────────────────────────────────────────────────────

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn(), back: vi.fn() }),
}));

beforeEach(() => {
  pushMock.mockClear();
});

// ─── Suites ──────────────────────────────────────────────────────────────

describe("useUIAction — handler unificado de ações globais", () => {
  it("dispatch retorna true para 'navigate_to' e chama router.push com URL correta", () => {
    const { result } = renderHook(() => useUIAction());

    let handled = false;
    act(() => {
      handled = result.current.dispatch("navigate_to", {
        page: "/configuracoes/ai-credits",
      });
    });

    expect(handled).toBe(true);
    expect(pushMock).toHaveBeenCalledWith("/configuracoes/ai-credits");
  });

  it("'navigate_to' com query monta URL com search params", () => {
    const { result } = renderHook(() => useUIAction());

    act(() => {
      result.current.dispatch("navigate_to", {
        page: "/configuracoes",
        query: { tab: "hiring-policy" },
      });
    });

    expect(pushMock).toHaveBeenCalledWith("/configuracoes?tab=hiring-policy");
  });

  it("dispatch retorna true para 'open_offer_review' (placeholder até PR-B)", () => {
    const { result } = renderHook(() => useUIAction());

    let handled = false;
    act(() => {
      handled = result.current.dispatch("open_offer_review", {
        candidate_id: "cand-1",
        job_id: "job-1",
      });
    });

    // Mesmo sem PR-B implementado, o handler reconhece o tipo e retorna true.
    // Quando PR-B chegar, ele substitui o no-op por chamada real ao store.
    expect(handled).toBe(true);
  });

  it("dispatch retorna false para action desconhecida (page-specific)", () => {
    const { result } = renderHook(() => useUIAction());

    let handled = false;
    act(() => {
      handled = result.current.dispatch("move_candidate", {
        candidate_id: "x",
      });
    });

    expect(handled).toBe(false);
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("dispatch com action vazia/null retorna false sem efeito colateral", () => {
    const { result } = renderHook(() => useUIAction());

    let handled1 = false;
    let handled2 = false;
    act(() => {
      handled1 = result.current.dispatch("", {});
      handled2 = result.current.dispatch(null as unknown as string, {});
    });

    expect(handled1).toBe(false);
    expect(handled2).toBe(false);
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("dispatch defensivo: 'navigate_to' sem 'page' retorna false (params inválidos)", () => {
    const { result } = renderHook(() => useUIAction());

    let handled = false;
    act(() => {
      handled = result.current.dispatch(
        "navigate_to",
        {} as Record<string, unknown>,
      );
    });

    expect(handled).toBe(false);
    expect(pushMock).not.toHaveBeenCalled();
  });
});

describe("useUIAction — fallback via CustomEvent", () => {
  let received: UnhandledUIActionEventDetail | null = null;
  const listener = (e: Event) => {
    received = (e as CustomEvent<UnhandledUIActionEventDetail>).detail;
  };

  beforeEach(() => {
    received = null;
    window.addEventListener(UNHANDLED_UI_ACTION_EVENT, listener);
  });

  afterEach(() => {
    window.removeEventListener(UNHANDLED_UI_ACTION_EVENT, listener);
  });

  it("dispatchOrEmit emite CustomEvent quando action é desconhecida", () => {
    const { result } = renderHook(() => useUIAction());

    act(() => {
      result.current.dispatchOrEmit("move_candidate", {
        candidate_id: "cand-1",
        target_stage: "interview",
      });
    });

    expect(received).not.toBeNull();
    expect(received?.action).toBe("move_candidate");
    expect(received?.params).toEqual({
      candidate_id: "cand-1",
      target_stage: "interview",
    });
  });

  it("dispatchOrEmit NÃO emite CustomEvent quando action é global (já tratada)", () => {
    const { result } = renderHook(() => useUIAction());

    act(() => {
      result.current.dispatchOrEmit("navigate_to", { page: "/jobs" });
    });

    expect(received).toBeNull();
    expect(pushMock).toHaveBeenCalledWith("/jobs");
  });

  it("dispatchOrEmit propaga conversation_id no detail do evento", () => {
    const { result } = renderHook(() => useUIAction());

    act(() => {
      result.current.dispatchOrEmit(
        "filter_jobs",
        { filter: "active" },
        "conv-abc",
      );
    });

    expect(received?.conversation_id).toBe("conv-abc");
  });
});

describe("useUIAction — acoes de candidatos globalizadas (P0.2 anti-ghost 2026-06-04)", () => {
  it("dispatch trata open_communication_modal como global: navega + re-emite", () => {
    const { result } = renderHook(() => useUIAction());
    const captured: UnhandledUIActionEventDetail[] = [];
    const listener = (e: Event) =>
      captured.push((e as CustomEvent<UnhandledUIActionEventDetail>).detail);
    window.addEventListener(UNHANDLED_UI_ACTION_EVENT, listener);

    let handled = false;
    act(() => {
      handled = result.current.dispatch("open_communication_modal", {
        candidate_id: "cand-1",
      });
    });
    window.removeEventListener(UNHANDLED_UI_ACTION_EVENT, listener);

    expect(handled).toBe(true);
    expect(pushMock).toHaveBeenCalledWith("/funil-de-talentos");
    expect(captured).toHaveLength(1);
    expect(captured[0].action).toBe("open_communication_modal");
  });

  it("open_schedule_modal e open_screening_modal tambem sao globais", () => {
    const { result } = renderHook(() => useUIAction());
    let a = false;
    let b = false;
    act(() => {
      a = result.current.dispatch("open_schedule_modal", {});
      b = result.current.dispatch("open_screening_modal", { candidate_id: "x" });
    });
    expect(a).toBe(true);
    expect(b).toBe(true);
  });

  it("estao registradas em GLOBAL_UI_ACTION_TYPES (nao sao mais ghost)", () => {
    const { result } = renderHook(() => useUIAction());
    const types = result.current.globalActionTypes as readonly string[];
    expect(types).toContain("open_communication_modal");
    expect(types).toContain("open_schedule_modal");
    expect(types).toContain("open_screening_modal");
  });
});
