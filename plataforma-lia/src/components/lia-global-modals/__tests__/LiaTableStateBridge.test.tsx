import { cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LiaTableStateBridge } from "@/components/lia-global-modals/LiaTableStateBridge";

const setSearchTerm = vi.fn();
const setSortBy = vi.fn();
const setSortOrder = vi.fn();
const setQuickFilters = vi.fn();
const setActiveTab = vi.fn();

vi.mock("@/stores/candidates-store", () => ({
  useCandidatesStore: {
    getState: () => ({
      setSearchTerm,
      setSortBy,
      setSortOrder,
      setQuickFilters,
      setActiveTab,
    }),
  },
}));

function fire(detail: unknown) {
  window.dispatchEvent(new CustomEvent("lia:apply_table_state", { detail }));
}

describe("LiaTableStateBridge — Fase 2 slice 1", () => {
  beforeEach(() => {
    setSearchTerm.mockClear();
    setSortBy.mockClear();
    setSortOrder.mockClear();
    setQuickFilters.mockClear();
    setActiveTab.mockClear();
  });

  afterEach(() => {
    cleanup(); // desmonta componentes => remove listeners entre testes
  });

  it("aplica patch completo ao candidates-store (quickFilters → Set)", () => {
    render(<LiaTableStateBridge />);

    fire({
      surface: "candidates",
      patch: {
        search: "João",
        sortBy: "score",
        sortOrder: "desc",
        quickFilters: ["approved"],
      },
    });

    expect(setSearchTerm).toHaveBeenCalledWith("João");
    expect(setSortBy).toHaveBeenCalledWith("score");
    expect(setSortOrder).toHaveBeenCalledWith("desc");
    expect(setQuickFilters).toHaveBeenCalledWith(new Set(["approved"]));
  });

  it("aplica patch parcial (só search)", () => {
    render(<LiaTableStateBridge />);
    fire({ surface: "candidates", patch: { search: "Maria" } });
    expect(setSearchTerm).toHaveBeenCalledWith("Maria");
    expect(setSortBy).not.toHaveBeenCalled();
    expect(setQuickFilters).not.toHaveBeenCalled();
  });

  it("ignora surface diferente de candidates", () => {
    render(<LiaTableStateBridge />);
    fire({ surface: "jobs", patch: { search: "x" } });
    expect(setSearchTerm).not.toHaveBeenCalled();
  });

  it("ignora sortOrder inválido", () => {
    render(<LiaTableStateBridge />);
    fire({ surface: "candidates", patch: { sortOrder: "sideways" } });
    expect(setSortOrder).not.toHaveBeenCalled();
  });

  it("troca a aba do funil (Fase 2 funil tabs): patch.tab → setActiveTab", () => {
    render(<LiaTableStateBridge />);
    fire({ surface: "candidates", patch: { tab: "favorites" } });
    expect(setActiveTab).toHaveBeenCalledWith("favorites");
    expect(setSearchTerm).not.toHaveBeenCalled();
  });

  it("aceita tab combinada com busca no mesmo patch", () => {
    render(<LiaTableStateBridge />);
    fire({
      surface: "candidates",
      patch: { tab: "saved-searches", search: "João" },
    });
    expect(setActiveTab).toHaveBeenCalledWith("saved-searches");
    expect(setSearchTerm).toHaveBeenCalledWith("João");
  });

  it("ignora tab não-string", () => {
    render(<LiaTableStateBridge />);
    fire({ surface: "candidates", patch: { tab: 123 } });
    expect(setActiveTab).not.toHaveBeenCalled();
  });

  it("remove o listener no unmount", () => {
    const { unmount } = render(<LiaTableStateBridge />);
    unmount();
    fire({ surface: "candidates", patch: { search: "depois" } });
    expect(setSearchTerm).not.toHaveBeenCalled();
  });
});
