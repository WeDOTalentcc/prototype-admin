import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useUIAction } from "@/hooks/chat/useUIAction";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ locale: "pt" }),
}));

describe("useUIAction — apply_table_state (Fase 2 slice 1)", () => {
  let dispatchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    dispatchSpy = vi.spyOn(window, "dispatchEvent");
  });

  afterEach(() => {
    dispatchSpy.mockRestore();
  });

  it("despacha lia:apply_table_state com surface+patch e retorna true", () => {
    const { result } = renderHook(() => useUIAction());

    const handled = result.current.dispatch("apply_table_state", {
      surface: "candidates",
      patch: { search: "João" },
    });

    expect(handled).toBe(true);
    const ev = dispatchSpy.mock.calls
      .map((c) => c[0])
      .find(
        (e): e is CustomEvent =>
          e instanceof CustomEvent && e.type === "lia:apply_table_state",
      );
    expect(ev).toBeDefined();
    expect(ev!.detail).toEqual({
      surface: "candidates",
      patch: { search: "João" },
    });
  });

  it("despacha surface jobs (lista de Vagas) e retorna true", () => {
    const { result } = renderHook(() => useUIAction());
    const handled = result.current.dispatch("apply_table_state", {
      surface: "jobs",
      patch: { search: "backend", filter: "ativas" },
    });
    expect(handled).toBe(true);
    const ev = dispatchSpy.mock.calls
      .map((c) => c[0])
      .find(
        (e): e is CustomEvent =>
          e instanceof CustomEvent && e.type === "lia:apply_table_state",
      );
    expect(ev!.detail).toEqual({
      surface: "jobs",
      patch: { search: "backend", filter: "ativas" },
    });
  });

  it("despacha surface kanban (board) e retorna true", () => {
    const { result } = renderHook(() => useUIAction());
    const handled = result.current.dispatch("apply_table_state", {
      surface: "kanban",
      patch: { search: "x", scoreMin: 80 },
    });
    expect(handled).toBe(true);
  });

  it("rejeita surface desconhecida", () => {
    const { result } = renderHook(() => useUIAction());
    const handled = result.current.dispatch("apply_table_state", {
      surface: "settings",
      patch: { search: "x" },
    });
    expect(handled).toBe(false);
  });

  it("rejeita patch ausente/inválido", () => {
    const { result } = renderHook(() => useUIAction());
    expect(
      result.current.dispatch("apply_table_state", { surface: "candidates" }),
    ).toBe(false);
  });
});


describe("useUIAction — select_rows (Fase 2 surface close)", () => {
  let dispatchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    dispatchSpy = vi.spyOn(window, "dispatchEvent");
  });

  afterEach(() => {
    dispatchSpy.mockRestore();
  });

  it("select_rows mode=set dispatches lia:select_rows event", () => {
    const { result } = renderHook(() => useUIAction());

    const handled = result.current.dispatch("select_rows", {
      surface: "candidates",
      mode: "set",
      ids: ["id-1", "id-2"],
    });

    expect(handled).toBe(true);
    const ev = dispatchSpy.mock.calls
      .map((c) => c[0])
      .find(
        (e): e is CustomEvent =>
          e instanceof CustomEvent && e.type === "lia:select_rows",
      );
    expect(ev).toBeDefined();
    expect(ev!.detail).toEqual({
      surface: "candidates",
      mode: "set",
      ids: ["id-1", "id-2"],
    });
  });

  it("select_rows mode=clear dispatches lia:select_rows event", () => {
    const { result } = renderHook(() => useUIAction());

    const handled = result.current.dispatch("select_rows", {
      surface: "candidates",
      mode: "clear",
    });

    expect(handled).toBe(true);
    const ev = dispatchSpy.mock.calls
      .map((c) => c[0])
      .find(
        (e): e is CustomEvent =>
          e instanceof CustomEvent && e.type === "lia:select_rows",
      );
    expect(ev).toBeDefined();
    expect(ev!.detail.mode).toBe("clear");
  });
});

describe("useUIAction - bulk_execute (F3 Gap 1)", () => {
  let dispatchSpy;

  beforeEach(() => {
    dispatchSpy = vi.spyOn(window, "dispatchEvent");
  });

  afterEach(() => {
    dispatchSpy.mockRestore();
  });

  it("bulk_execute dispatches lia:bulk_execute event with correct detail", () => {
    const { result } = renderHook(() => useUIAction());
    const results = [
      { id: "c1", name: "Ana Lima", ok: true },
      { id: "c2", name: "Joao Paz", ok: false, reason: "Email invalido" },
    ];
    const handled = result.current.dispatch("bulk_execute", {
      action: "reject_candidates",
      title: "2 candidatos processados",
      results,
    });

    expect(handled).toBe(true);
    const ev = dispatchSpy.mock.calls
      .map((c) => c[0])
      .find(
        (e) =>
          e instanceof CustomEvent && e.type === "lia:bulk_execute",
      );
    expect(ev).toBeDefined();
    expect(ev.detail.action).toBe("reject_candidates");
    expect(ev.detail.title).toBe("2 candidatos processados");
    expect(ev.detail.results).toHaveLength(2);
    expect(ev.detail.results[0].ok).toBe(true);
    expect(ev.detail.results[1].ok).toBe(false);
  });

  it("bulk_execute with empty results still dispatches", () => {
    const { result } = renderHook(() => useUIAction());
    const handled = result.current.dispatch("bulk_execute", {
      action: "move_stage",
      title: "0 candidatos movidos",
      results: [],
    });
    expect(handled).toBe(true);
    const ev = dispatchSpy.mock.calls
      .map((c) => c[0])
      .find((e) => e instanceof CustomEvent && e.type === "lia:bulk_execute");
    expect(ev).toBeDefined();
    expect(ev.detail.results).toEqual([]);
  });

  it("bulk_execute without results field falls back to empty array", () => {
    const { result } = renderHook(() => useUIAction());
    result.current.dispatch("bulk_execute", {
      action: "send_communication",
      title: "Comunicacao enviada",
    });
    const ev = dispatchSpy.mock.calls
      .map((c) => c[0])
      .find((e) => e instanceof CustomEvent && e.type === "lia:bulk_execute");
    expect(ev.detail.results).toEqual([]);
  });
});

