import { describe, expect, it } from "vitest";
import {
  GLOBAL_UI_ACTION_TYPES,
  type GlobalUIAction,
  isGlobalUIActionType,
} from "@/types/ui-action";

describe("ui-action — apply_table_state (Fase 2 slice 1)", () => {
  it("reconhece apply_table_state como tipo global em runtime", () => {
    expect(isGlobalUIActionType("apply_table_state")).toBe(true);
    expect(GLOBAL_UI_ACTION_TYPES).toContain("apply_table_state");
  });

  it("aceita a variante apply_table_state no union (type-level)", () => {
    // Fixture type-level: compila => o union cobre a variante.
    const action: GlobalUIAction = {
      type: "apply_table_state",
      params: {
        surface: "candidates",
        patch: {
          search: "João",
          sortBy: "score",
          sortOrder: "desc",
          quickFilters: ["approved"],
        },
      },
    };
    expect(action.type).toBe("apply_table_state");
    if (action.type === "apply_table_state") {
      expect(action.params.surface).toBe("candidates");
      expect(action.params.patch.search).toBe("João");
    }
  });

  it("aceita patch.tab para trocar a aba do funil (Fase 2 funil tabs)", () => {
    // Fixture type-level: compila => o patch cobre o campo opcional tab.
    const action: GlobalUIAction = {
      type: "apply_table_state",
      params: {
        surface: "candidates",
        patch: { tab: "saved-searches" },
      },
    };
    expect(action.type).toBe("apply_table_state");
    if (action.type === "apply_table_state") {
      expect(action.params.patch.tab).toBe("saved-searches");
    }
  });

  it("mantém os tipos globais pré-existentes", () => {
    expect(isGlobalUIActionType("open_modal")).toBe(true);
    expect(isGlobalUIActionType("navigate_to")).toBe(true);
    expect(isGlobalUIActionType("nope_unknown")).toBe(false);
  });
});
