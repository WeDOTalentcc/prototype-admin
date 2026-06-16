"use client";

/**
 * PR-D — `useUnhandledUIActionListener` hook utilitário.
 *
 * Subscriber para o `lia:unhandled_ui_action` CustomEvent emitido pelo
 * `useUIAction.dispatchOrEmit` quando uma UIAction não é tratada pelo
 * handler global (ex.: actions page-specific como `move_candidate`,
 * `start_job_wizard`, `switch_search_mode`).
 *
 * **Padrão de uso:** cada hook page-specific (kanban, talent, jobs) chama
 * este hook passando o handler local. Listener é registrado on-mount,
 * removido on-unmount automaticamente — só responde quando a página está
 * ativa, sem efeitos colaterais cross-page.
 *
 * @example
 * ```ts
 * function useKanbanLIAHandlers() {
 *   const handleLiaUiAction = useCallback(...)
 *   useUnhandledUIActionListener(handleLiaUiAction)
 *   return { handleLiaUiAction, ... }
 * }
 * ```
 *
 * Skill: harness-engineering [pub/sub canonical, cleanup garantido].
 */

import {
  UNHANDLED_UI_ACTION_EVENT,
  type UnhandledUIActionEventDetail,
} from "@/types/ui-action";
import { useEffect, useRef } from "react";

export type UnhandledUIActionHandler = (
  action: string,
  params: Record<string, unknown>,
) => void;

export function useUnhandledUIActionListener(
  handler: UnhandledUIActionHandler | null | undefined,
): void {
  // Ref para evitar re-bind do listener a cada render — o handler real
  // pode ser recriado mas o listener referencia sempre a versão mais nova.
  const handlerRef = useRef(handler);
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const onEvent = (e: Event) => {
      const detail = (e as CustomEvent<UnhandledUIActionEventDetail>).detail;
      if (!detail || typeof detail.action !== "string") return;
      handlerRef.current?.(detail.action, detail.params ?? {});
    };

    window.addEventListener(UNHANDLED_UI_ACTION_EVENT, onEvent);
    return () => {
      window.removeEventListener(UNHANDLED_UI_ACTION_EVENT, onEvent);
    };
  }, []);
}
