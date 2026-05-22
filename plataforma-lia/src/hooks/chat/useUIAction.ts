"use client";

/**
 * PR-D — `useUIAction` hook canonical para dispatch de UIActions.
 *
 * Resolve UI-S03 do audit enterprise 2026-04-26: cria fonte única de
 * verdade para tratamento de `ChatResponse.ui_action` em qualquer surface
 * (UnifiedChat, sidebar, floating, dock).
 *
 * **Escopo MÍNIMO (intencional):** este hook trata **apenas ações globais**
 * — `navigate_to`, `open_modal`, `open_offer_review`, `wizard_step`,
 * `open_panel`, `scroll_to`. Ações específicas de página (kanban, talent,
 * jobs) continuam com seus handlers locais (`handleLiaUiAction`,
 * `handleTalentUIAction`, etc.) — o método `dispatchOrEmit` re-emite o
 * `lia:unhandled_ui_action` CustomEvent que cada surface escuta para tratar
 * seu vocabulário próprio.
 *
 * **Princípio canonical-fix:** uma fonte da verdade para ações globais;
 * surface ownership preservado para ações específicas. Sem regressão.
 *
 * Skill: harness-engineering [guide computacional + sensor no boundary].
 */

import {
  GLOBAL_UI_ACTION_TYPES,
  type GlobalUIActionType,
  UNHANDLED_UI_ACTION_EVENT,
  type UnhandledUIActionEventDetail,
  isGlobalUIActionType,
} from "@/types/ui-action";
import { useRouter } from "next/navigation";
import { useCallback } from "react";

interface UseUIActionReturn {
  /**
   * Tenta tratar uma `RawUIAction` como ação global. Retorna `true` se
   * tratou, `false` se o tipo não é global ou os params são inválidos.
   * Não emite eventos — caller decide o que fazer com `false`.
   */
  dispatch: (action: string, params?: Record<string, unknown>) => boolean;

  /**
   * Como `dispatch`, mas se retornar `false` re-emite a action via
   * `lia:unhandled_ui_action` CustomEvent para que handlers page-specific
   * possam consumir. Use este em `UnifiedChat` para fluxo padrão.
   */
  dispatchOrEmit: (
    action: string,
    params?: Record<string, unknown>,
    conversation_id?: string,
  ) => boolean;

  /** Lista runtime dos tipos globais — útil pra debug/telemetria. */
  globalActionTypes: readonly GlobalUIActionType[];
}

export function useUIAction(): UseUIActionReturn {
  const router = useRouter();

  const dispatch = useCallback(
    (action: string, params: Record<string, unknown> = {}): boolean => {
      if (!action || typeof action !== "string") return false;
      if (!isGlobalUIActionType(action)) return false;

      switch (action) {
        case "navigate_to": {
          const page = params.page;
          if (typeof page !== "string" || !page) return false;
          const query = params.query as Record<string, string> | undefined;
          let url = page;
          if (query && typeof query === "object") {
            const search = new URLSearchParams(query).toString();
            if (search) url = `${page}?${search}`;
          }
          router.push(url);
          return true;
        }

        case "open_modal": {
          const modal_id = params.modal_id;
          if (typeof modal_id !== "string" || !modal_id) return false;
          // PR-D entrega o canal; consumers (modal stores) escutam
          // `lia:open_modal` ou usam sua própria store. Evento simples
          // permite que diferentes surfaces tenham modais isolados.
          window.dispatchEvent(
            new CustomEvent("lia:open_modal", {
              detail: { modal_id, data: params.data },
            }),
          );
          return true;
        }

        case "open_offer_review": {
          const candidate_id = params.candidate_id;
          const job_id = params.job_id;
          if (typeof candidate_id !== "string" || typeof job_id !== "string") {
            return false;
          }
          // PR-B vai conectar este handler ao `useOfferDraftStore.start()`.
          // Por enquanto emitimos evento dedicado para placeholder/observability.
          window.dispatchEvent(
            new CustomEvent("lia:open_offer_review", {
              detail: {
                candidate_id,
                job_id,
                draft_id: params.draft_id,
              },
            }),
          );
          return true;
        }

        case "wizard_step": {
          const wizard = params.wizard;
          const step = params.step;
          if (typeof wizard !== "string" || typeof step !== "string")
            return false;
          window.dispatchEvent(
            new CustomEvent("lia:wizard_step", {
              detail: { wizard, step },
            }),
          );
          return true;
        }

        case "open_panel": {
          const panel = params.panel;
          if (typeof panel !== "string" || !panel) return false;
          window.dispatchEvent(
            new CustomEvent("lia:open_panel", {
              detail: { panel, entity_id: params.entity_id },
            }),
          );
          return true;
        }

        case "scroll_to": {
          const element_id = params.element_id;
          if (typeof element_id !== "string" || !element_id) return false;
          if (typeof document === "undefined") return false;
          const el = document.getElementById(element_id);
          if (!el) return false;
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          return true;
        }

        case "settings_open_tab": {
          // WT-2022 Fase 4 bridge: 3 tools (toggle_learning_loop,
          // toggle_lia_field, record_dsr_action) emitem essa action. O
          // listener canonical fica em SettingsPageEnhanced
          // (settings-page-enhanced.tsx:327) — abre a section,
          // expande subsection e (opcional) scroll/highlight no field.
          const section = params.section;
          if (typeof section !== "string" || !section) return false;
          const subsection =
            typeof params.subsection === "string" ? params.subsection : undefined;
          const field =
            typeof params.field === "string" ? params.field : undefined;
          if (typeof window === "undefined") return false;
          // 1) Garante que a aba Configurações abra (caso o usuário esteja
          //    em outra surface) via router push — preserva query params
          //    pra deep-link share + back/forward funcionar.
          const qs = new URLSearchParams({ section });
          if (subsection) qs.set("subsection", subsection);
          if (field) qs.set("field", field);
          router.push(`/configuracoes?${qs.toString()}`);
          // 2) Evento canonical já consumido por SettingsPageEnhanced
          //    (settings-page-enhanced.tsx:327) — abre tab + highlight
          //    em paralelo (caso a SettingsPage já esteja montada).
          window.dispatchEvent(
            new CustomEvent("lia:settings-action", {
              detail: {
                actionId: "settings_open_tab",
                section,
                subsection,
                field,
                source: "chat",
              },
            }),
          );
          window.dispatchEvent(
            new CustomEvent("settings-open-tab", { detail: section }),
          );
          return true;
        }

        default:
          // exhaustiveness: caso TS deixe escapar um tipo, runtime falha-soft.
          return false;
      }
    },
    [router],
  );

  const dispatchOrEmit = useCallback(
    (
      action: string,
      params: Record<string, unknown> = {},
      conversation_id?: string,
    ): boolean => {
      const handled = dispatch(action, params);
      if (handled) return true;
      if (typeof window === "undefined") return false;
      const detail: UnhandledUIActionEventDetail = {
        action,
        params,
        conversation_id,
      };
      window.dispatchEvent(
        new CustomEvent(UNHANDLED_UI_ACTION_EVENT, { detail }),
      );
      return false;
    },
    [dispatch],
  );

  return {
    dispatch,
    dispatchOrEmit,
    globalActionTypes: GLOBAL_UI_ACTION_TYPES,
  };
}
