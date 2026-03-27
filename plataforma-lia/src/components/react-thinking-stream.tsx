/**
 * ReactThinkingStream — E7 (Streaming de Pensamentos ReAct)
 *
 * Exibe as etapas de raciocínio do agente durante processamento.
 * Colapsável. Só aparece durante streaming ativo.
 */
"use client";
import { useState } from "react";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";

interface ReactThinkingStreamProps {
  steps: string[];
  isThinking: boolean;
}

export function ReactThinkingStream({ steps, isThinking }: ReactThinkingStreamProps) {
  const [expanded, setExpanded] = useState(false);

  if (!isThinking && steps.length === 0) return null;

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-md text-xs text-gray-500 my-2">
      <button
        className="flex items-center gap-2 w-full px-3 py-2 hover:bg-gray-100 transition-colors rounded-md"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        {isThinking ? (
          <Loader2 className="h-3 w-3 animate-spin text-gray-400" />
        ) : (
          <span className="h-3 w-3 rounded-full bg-status-success inline-block" />
        )}
        <span className="flex-1 text-left">
          {isThinking ? "LIA está pensando..." : `Raciocínio concluído (${steps.length} etapas)`}
        </span>
        {steps.length > 0 && (
          expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
        )}
      </button>

      {expanded && steps.length > 0 && (
        <ul className="px-3 pb-2 space-y-1">
          {steps.map((step, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-gray-300 select-none">{i + 1}.</span>
              <span>{step}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
