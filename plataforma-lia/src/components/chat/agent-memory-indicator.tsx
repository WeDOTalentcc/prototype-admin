"use client";

import React, { useState, useCallback } from "react";
import { Brain, ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { useAgentMemory } from "@/hooks/chat/useAgentMemory";
import { formatRelativeTime } from "@/lib/format-utils";
import { cn } from "@/lib/utils";

const stageLabels: Record<string, string> = {
  "input-evaluation": "Avaliação Inicial",
  "hierarchy-definition": "Definição de Hierarquia",
  "competencies": "Competências",
  "salary": "Remuneração",
  "jd-enrichment": "Enriquecimento JD",
  "review": "Revisão Final",
  "triage": "Triagem",
  "screening": "Screening WSI",
  "shortlist": "Shortlist",
  "interview": "Entrevistas",
  "offer": "Proposta",
  "hired": "Contratação",
  "search-criteria": "Critérios de Busca",
  "talent-search": "Busca de Talentos",
  "profile-analysis": "Análise de Perfis",
  "shortlist-creation": "Criação de Shortlist",
  "outreach": "Abordagem",
};


interface AgentMemoryIndicatorProps {
  sessionId: string;
  domain?: string;
}

export function AgentMemoryIndicator({
  sessionId,
  domain = "wizard",
}: AgentMemoryIndicatorProps) {
  const { memory, fullMemory, isLoading, loadFull, reset } = useAgentMemory({
    sessionId,
    domain,
  });
  const [expanded, setExpanded] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);

  const handleExpand = useCallback(() => {
    if (!expanded && !fullMemory) {
      loadFull();
    }
    setExpanded((v) => !v);
    setConfirmReset(false);
  }, [expanded, fullMemory, loadFull]);

  const handleReset = useCallback(async () => {
    if (!confirmReset) {
      setConfirmReset(true);
      return;
    }
    await reset();
    setExpanded(false);
    setConfirmReset(false);
  }, [confirmReset, reset]);

  if (isLoading && !memory) return null;
  if (!memory) return null;

  const stageName =
    (memory.current_stage && stageLabels[memory.current_stage]) ||
    memory.current_stage ||
    "Iniciando";
  const pct = Math.min(100, Math.max(0, memory.completion_percentage));
  const relTime = formatRelativeTime(memory.last_updated);

  return (
    <div className="relative mt-1.5">
      <div
        role="button"
        tabIndex={0}
        onClick={handleExpand}
        onKeyDown={(e) => e.key === "Enter" && handleExpand()}
        // [OPT-023] py-1.5 px arbitrário — sem canônico Tailwind
        className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-md border border-lia-border-subtle bg-lia-bg-secondary cursor-pointer text-xs text-lia-text-secondary select-none transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover"
      >
        <Brain
          className="text-wedo-cyan-text flex-shrink-0 w-3.5 h-3.5"
        />

        <span
          className="text-lia-text-primary font-medium whitespace-nowrap"
        >
          {stageName}
        </span>

        <div
          className="flex items-center gap-1 min-w-[80px]"
        >
          <div
            className="bg-lia-interactive-active flex-1 h-1 rounded-[2px] overflow-hidden"
          >
            <div
              className="h-full rounded-[2px] bg-wedo-cyan transition-[width] duration-300 ease-in-out"
              style={{width: `${pct}%`}}
            />
          </div>
          <span className="text-xs">
            {pct}%
          </span>
        </div>

        <span
          className="text-lia-text-tertiary border-l border-l-lia-border-subtle text-xs pl-2"
        >
          {memory.fields_count} campos
        </span>

        {relTime && (
          <span
            className="text-lia-text-tertiary border-l border-l-lia-border-subtle text-xs pl-2"
          >
            {relTime}
          </span>
        )}

        {expanded ? (
          <ChevronUp className="w-3 h-3 ml-auto" />
        ) : (
          <ChevronDown className="w-3 h-3 ml-auto" />
        )}
      </div>

      {expanded && (
          <div
            className="overflow-hidden animate-in fade-in slide-in-from-top-1 duration-200"
          >
            <div
              className="mt-1 px-3.5 py-3 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary max-h-[280px] overflow-y-auto text-xs text-lia-text-primary"
            >
              <div
                className="font-semibold text-sm mb-2"
              >
                Memória do Agente
              </div>

              <div
                className="bg-lia-interactive-active h-px mb-2"
              />

              <div className="mb-1.5">
                <span className="font-medium">Estágio: </span>
                <span>
                  {stageName}
                </span>
              </div>

              <div className="mb-2.5">
                <span className="font-medium">Progresso: </span>
                <span>
                  {pct}% ({memory.fields_count} campos)
                </span>
              </div>

              {fullMemory &&
                Object.keys(fullMemory.collected_fields).length > 0 && (
                  <div className="mb-2.5">
                    <div
                      className="font-medium mb-1"
                    >
                      Campos coletados:
                    </div>
                    <ul
                      className="m-0 pl-4 list-disc"
                    >
                      {Object.entries(fullMemory.collected_fields).map(
                        ([key, val]) => (
                          <li
                            key={key}
                            className="mb-0.5"
                          >
                            <span className="font-medium">
                              {key}:
                            </span>{" "}
                            {typeof val === "object"
                              ? JSON.stringify(val)
                              : String(val)}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}

              {fullMemory &&
                fullMemory.pending_actions &&
                fullMemory.pending_actions.length > 0 && (
                  <div className="mb-1.5">
                    <span className="font-medium">Ações pendentes: </span>
                    <span>
                      {fullMemory.pending_actions.length}
                    </span>
                  </div>
                )}

              {fullMemory && fullMemory.agent_notes && (
                <div className="mb-2.5">
                  <div
                    className="font-medium mb-1"
                  >
                    Notas do agente:
                  </div>
                  <div
                    className="italic text-xs"
                  >
                    {fullMemory.agent_notes}
                  </div>
                </div>
              )}

              {!fullMemory && (
                <div
                  className="text-lia-text-tertiary text-xs italic"
                >
                  Carregando detalhes...
                </div>
              )}

              <div
                className="bg-lia-interactive-active h-px my-2"
              />

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleReset();
                }}
                className={cn("border flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs cursor-pointer transition-colors motion-reduce:transition-none", confirmReset ? "bg-lia-bg-tertiary text-lia-text-secondary border-wedo-cyan" : "bg-transparent text-lia-text-tertiary border-lia-border-subtle")}
              >
                <Trash2 className="w-3 h-3" />
                {confirmReset ? "Confirmar limpeza?" : "Limpar memória"}
              </button>
            </div>
          </div>
        )}
    </div>
  );
}
