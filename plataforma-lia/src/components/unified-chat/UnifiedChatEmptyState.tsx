"use client";

import {
  type ChatSuggestionMetadata,
  ChatWorkflowReels,
} from "@/components/ui/chat-workflow-reels";
import type { ChatContextType } from "@/contexts/lia-float-context";
import { cn } from "@/lib/utils";
import { useDynamicGreeting } from "@/hooks/ui/use-dynamic-greeting";
import { Brain, Building, FileSpreadsheet, Globe } from "lucide-react";
import { useTranslations } from "next-intl";
import React from "react";
import type { ChatMode } from "./unified-chat-types";

interface Props {
  mode: ChatMode;
  /**
   * PR-A: aceita opcionalmente `metadata` com hints de routing emitidos pelo
   * Rail A. Consumidores antigos que ignoram o 2º arg seguem funcionando.
   */
  onSuggestionClick: (
    prompt: string,
    metadata?: ChatSuggestionMetadata,
  ) => void;
  contextType?: ChatContextType;
}

// P1-5 (Fase B 2026-05-23): keys de SETTINGS_CHIPS movidas pra i18n.
// SETTINGS_CHIP_DEFS carrega apenas o icon (TS-only, nao i18n-able). Labels
// e commands sao resolvidos via t() dentro do componente. Mantem icon+key
// pareados em uma estrutura unica pra evitar drift entre array e JSON.
const SETTINGS_CHIP_DEFS = [
  { key: "profile", icon: Building },
  { key: "spreadsheet", icon: FileSpreadsheet },
  { key: "website", icon: Globe },
] as const;

export function UnifiedChatEmptyState({
  mode,
  onSuggestionClick,
  contextType,
}: Props) {
  const isCompact = mode === "sidebar" || mode === "floating";
  const t = useTranslations("chat");
  const tSettings = useTranslations("chat.emptyState.settings");
  const greeting = useDynamicGreeting("chat", t("greeting"));

  if (contextType === "settings_config") {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center flex-1 px-6",
          isCompact ? "py-8 gap-4" : "py-12 gap-6",
        )}
      >
        <div
          className={cn(
            "rounded-full border border-lia-border-subtle flex items-center justify-center bg-lia-bg-primary",
            isCompact ? "w-12 h-12" : "w-16 h-16",
          )}
        >
          <Building
            className={cn("text-wedo-cyan-text", isCompact ? "w-6 h-6" : "w-8 h-8")}
            strokeWidth={1.5}
          />
        </div>

        <h2
          className={cn(
            "font-semibold text-lia-text-primary text-center",
            isCompact ? "text-base" : "text-xl",
          )}
        >
          {tSettings("heading")}
        </h2>
        <p className="text-sm text-lia-text-secondary text-center max-w-[280px]">
          {tSettings("subtitle")}
        </p>

        <div
          className={cn(
            "w-full flex flex-col gap-2",
            isCompact ? "max-w-[280px]" : "max-w-[400px]",
          )}
        >
          {SETTINGS_CHIP_DEFS.map((chip) => {
            const label = tSettings(`chips.${chip.key}.label`);
            const command = tSettings(`chips.${chip.key}.command`);
            return (
              <button
                key={chip.key}
                onClick={() => onSuggestionClick(command)}
                className="flex items-center gap-3 p-3 rounded-md text-left border border-lia-border-subtle bg-lia-bg-primary hover:bg-lia-bg-secondary hover:border-wedo-cyan/30 transition-all"
              >
                <div className="p-1.5 rounded-md bg-wedo-cyan/10 text-wedo-cyan-text flex-shrink-0">
                  <chip.icon className="w-4 h-4" />
                </div>
                <span className="text-sm font-medium text-lia-text-primary">
                  {label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center flex-1 px-6",
        isCompact ? "py-8 gap-4" : "py-12 gap-6",
      )}
    >
      <div
        className={cn(
          "rounded-full border border-lia-border-subtle flex items-center justify-center bg-lia-bg-primary",
          isCompact ? "w-12 h-12" : "w-16 h-16",
        )}
      >
        <Brain
          className={cn("text-wedo-cyan-text", isCompact ? "w-6 h-6" : "w-8 h-8")}
          strokeWidth={1.5}
        />
      </div>

      <h2
        className={cn(
          "font-semibold text-lia-text-primary text-center",
          isCompact ? "text-base" : "text-xl",
        )}
      >
        {greeting}
      </h2>

      <div
        className={cn("w-full", isCompact ? "max-w-[280px]" : "max-w-[640px]")}
      >
        <ChatWorkflowReels onSelect={onSuggestionClick} compact={isCompact} />
      </div>
    </div>
  );
}
