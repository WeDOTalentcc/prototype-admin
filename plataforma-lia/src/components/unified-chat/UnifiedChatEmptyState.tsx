"use client";

import {
  type ChatSuggestionMetadata,
  ChatWorkflowReels,
} from "@/components/ui/chat-workflow-reels";
import type { ChatContextType } from "@/contexts/lia-float-context";
import { cn } from "@/lib/utils";
import { Brain, Building, FileSpreadsheet, Globe } from "lucide-react";
import { useTranslations } from "next-intl";
import React, { useEffect } from "react";
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

const SETTINGS_CHIPS = [
  {
    label: "Completar perfil da empresa",
    command: "Quero completar o perfil da minha empresa",
    icon: Building,
  },
  {
    label: "Importar planilha",
    command: "Quero importar uma planilha de colaboradores",
    icon: FileSpreadsheet,
  },
  {
    label: "Analisar website",
    command: "Analise o website da minha empresa e extraia informacoes",
    icon: Globe,
  },
];

export function UnifiedChatEmptyState({
  mode,
  onSuggestionClick,
  contextType,
}: Props) {
  const isCompact = mode === "sidebar" || mode === "floating";
  const t = useTranslations("chat");

  // Sinaliza para o WorkflowRail global que o trilho interno do chat
  // (ChatWorkflowReels) está montado/visível, evitando duplicação visual.
  // Em settings_config não renderizamos o reels, então não contamos.
  // Uso de ref-count global (window.__liaChatReelsCount) para tolerar
  // múltiplas instâncias do empty state montadas em paralelo
  // (ex: sidebar + dashboard inline) sem uma desmontagem zerar o sinal
  // enquanto outra ainda está visível.
  const reelsVisible = contextType !== "settings_config";
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!reelsVisible) return;
    const w = window as unknown as { __liaChatReelsCount?: number };
    w.__liaChatReelsCount = (w.__liaChatReelsCount ?? 0) + 1;
    window.dispatchEvent(
      new CustomEvent("lia:chat-reels-visibility", {
        detail: { count: w.__liaChatReelsCount },
      }),
    );
    return () => {
      const cur = (w.__liaChatReelsCount ?? 1) - 1;
      w.__liaChatReelsCount = Math.max(0, cur);
      window.dispatchEvent(
        new CustomEvent("lia:chat-reels-visibility", {
          detail: { count: w.__liaChatReelsCount },
        }),
      );
    };
  }, [reelsVisible]);

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
            className={cn("text-wedo-cyan", isCompact ? "w-6 h-6" : "w-8 h-8")}
            strokeWidth={1.5}
          />
        </div>

        <h2
          className={cn(
            "font-semibold text-lia-text-primary text-center",
            isCompact ? "text-base" : "text-xl",
          )}
        >
          Configure sua empresa
        </h2>
        <p className="text-sm text-lia-text-secondary text-center max-w-[280px]">
          Me conte sobre sua empresa e eu vou preencher os dados
          automaticamente.
        </p>

        <div
          className={cn(
            "w-full flex flex-col gap-2",
            isCompact ? "max-w-[280px]" : "max-w-[400px]",
          )}
        >
          {SETTINGS_CHIPS.map((chip) => (
            <button
              key={chip.command}
              onClick={() => onSuggestionClick(chip.command)}
              className="flex items-center gap-3 p-3 rounded-md text-left border border-lia-border-subtle bg-lia-bg-primary hover:bg-lia-bg-secondary hover:border-wedo-cyan/30 transition-all"
            >
              <div className="p-1.5 rounded-md bg-wedo-cyan/10 text-wedo-cyan flex-shrink-0">
                <chip.icon className="w-4 h-4" />
              </div>
              <span className="text-sm font-medium text-lia-text-primary">
                {chip.label}
              </span>
            </button>
          ))}
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
          className={cn("text-wedo-cyan", isCompact ? "w-6 h-6" : "w-8 h-8")}
          strokeWidth={1.5}
        />
      </div>

      <h2
        className={cn(
          "font-semibold text-lia-text-primary text-center",
          isCompact ? "text-base" : "text-xl",
        )}
      >
        {t("greeting")}
      </h2>

      <div
        className={cn("w-full", isCompact ? "max-w-[280px]" : "max-w-[640px]")}
      >
        <ChatWorkflowReels onSelect={onSuggestionClick} compact={isCompact} />
      </div>
    </div>
  );
}
