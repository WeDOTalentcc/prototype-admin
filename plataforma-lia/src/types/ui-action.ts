/**
 * PR-D — UIAction discriminated union
 *
 * Tipo canônico de ações de UI que o backend pode disparar via
 * `ChatResponse.ui_action` + `ui_action_params`. Resolve UI-S03 do audit
 * enterprise 2026-04-26: handler unificado em `UnifiedChat` para os
 * actions GLOBAIS, com fallback via event broadcast para handlers
 * page-specific (kanban, talent, jobs).
 *
 * **Princípio:** este tipo cobre apenas ações **globais** (cross-surface).
 * Ações específicas de página (`move_candidate`, `start_job_wizard`,
 * `filter_jobs`, `switch_search_mode`, etc.) continuam tratadas pelos
 * hooks de cada surface — o fallback via `lia:unhandled_ui_action` event
 * preserva esse comportamento sem regressão.
 *
 * **Mirror canônico no BE:** `app/shared/websocket/ws_message_schemas.py`
 * (`UIAction*` Pydantic models). Validação acontece no boundary WS.
 *
 * Skill: harness-engineering [guide computacional + sensor no boundary].
 */

/**
 * Ações globais com schema validado. Cada surface pode disparar qualquer uma.
 * Implementadas no `useUIAction()` hook canonical.
 */
export type GlobalUIAction =
  | {
      type: "navigate_to";
      params: {
        page: string;
        query?: Record<string, string>;
      };
    }
  | {
      type: "open_modal";
      params: {
        modal_id: string;
        data?: unknown;
      };
    }
  | {
      type: "open_offer_review";
      params: {
        candidate_id: string;
        job_id: string;
        draft_id?: string;
      };
    }
  | {
      type: "wizard_step";
      params: {
        wizard: string;
        step: string;
      };
    }
  | {
      type: "open_panel";
      params: {
        panel: string;
        entity_id?: string;
      };
    }
  | {
      type: "scroll_to";
      params: {
        element_id: string;
      };
    }
  | {
      // WT-2022 Fase 4: tools `toggle_learning_loop`, `toggle_lia_field`,
      // `record_dsr_action` retornam essa action para abrir a aba de
      // Configurações + subsection certa + (opcional) highlight do field.
      // Bridge: useUIAction dispatcha CustomEvent `lia:settings-action` que
      // SettingsPageEnhanced escuta (settings-page-enhanced.tsx:327).
      type: "settings_open_tab";
      params: {
        section: string;
        subsection?: string;
        field?: string;
      };
    }
  | {
      // P0.2 (2026-06-04) anti-ghost: acoes de candidatos globalizadas.
      // Vivem na superficie funil-de-talentos; useUIAction navega pra la e
      // re-emite pro handler page-specific (useLIAQuickActions).
      type: "open_communication_modal";
      params?: { candidate_id?: string };
    }
  | {
      type: "open_schedule_modal";
      params?: Record<string, never>;
    }
  | {
      type: "open_screening_modal";
      params?: { candidate_id?: string };
    }
  | {
      // Fase 2 slice 1 (ponte in-page): aplica busca/ordenação/filtros à
      // tabela JÁ ABERTA. useUIAction despacha `lia:apply_table_state`;
      // LiaTableStateBridge escuta e dirige o store da superfície
      // (slice 1: candidates → useCandidatesStore). Sem navegação/mutação.
      type: "apply_table_state";
      params: {
        surface: "candidates" | "jobs" | "kanban" | "talent_pool" | "recrutar";
        patch: {
          search?: string; // candidates/jobs/kanban
          sortBy?: string; // candidates
          sortOrder?: "asc" | "desc"; // candidates
          quickFilters?: string[]; // candidates (bridge converte para Set)
          // candidates: troca a aba do Funil (Fase 2 funil tabs) -> setActiveTab
          tab?:
            | "search"
            | "favorites"
            | "lists"
            | "history"
            | "saved-searches"
            | "agents";
          filter?: string; // jobs (activeFilter: todas/ativas/urgentes/ats/...)
          scoreMin?: number; // kanban (0-100)
          statusFilter?: string[]; // kanban (novo/em_analise/...)
          originFilter?: string[]; // kanban (web/whatsapp/sourcing/ats)
          workModelFilter?: string[]; // kanban (remoto/hibrido/presencial)
          stage?: string | null; // talent_pool: etapa (discovered/contacted/...) | recrutar: nome da etapa do pipeline
          poolTab?: string; // talent_pool: aba (candidates/sourcing/agents/config)
        };
      };
    }
  | {
      // Fase 2 surface close: LIA seleciona candidatos in-page para pre-marcar
      // bulk actions. useUIAction despacha `lia:select_rows`; LiaTableStateBridge
      // escuta e dirige useCandidatesStore (set/add/clear).
      type: "select_rows";
      params: {
        surface: "candidates";
        mode: "set" | "add" | "clear";
        ids?: string[]; // obrigatorio para mode="set"/"add", omitido para "clear"
      };
    };

/**
 * Tipo string das ações globais conhecidas. Útil para narrowing em runtime.
 */
export type GlobalUIActionType = GlobalUIAction["type"];

/** Lista runtime de tipos globais — usado pelo `useUIAction` para roteamento. */
export const GLOBAL_UI_ACTION_TYPES: readonly GlobalUIActionType[] = [
  "navigate_to",
  "open_modal",
  "open_offer_review",
  "wizard_step",
  "open_panel",
  "scroll_to",
  "settings_open_tab",
  "open_communication_modal",
  "open_schedule_modal",
  "open_screening_modal",
  "apply_table_state",
  "select_rows",
] as const;

export function isGlobalUIActionType(type: string): type is GlobalUIActionType {
  return (GLOBAL_UI_ACTION_TYPES as readonly string[]).includes(type);
}

/**
 * Wire-format que chega do backend (via ChatResponse): tipo é string
 * livre, params é dict aberto. O hook `useUIAction` faz narrowing
 * defensivo antes de executar.
 *
 * Ações conhecidas (globais) são roteadas; desconhecidas (page-specific)
 * são re-emitidas via `lia:unhandled_ui_action` CustomEvent.
 */
export interface RawUIAction {
  type: string;
  params?: Record<string, unknown>;
}

/** Detalhe do CustomEvent emitido quando UIAction não é tratada pelo handler global. */
export interface UnhandledUIActionEventDetail {
  action: string;
  params: Record<string, unknown>;
  conversation_id?: string;
}

export const UNHANDLED_UI_ACTION_EVENT = "lia:unhandled_ui_action" as const;
