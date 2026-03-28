"use client";

import React, { useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Brain, ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { useAgentMemory } from "@/hooks/useAgentMemory";
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

function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return "";
  try {
    const diff = Date.now() - new Date(dateStr).getTime();
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) return "agora";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `há ${minutes} min`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `há ${hours}h`;
    const days = Math.floor(hours / 24);
    return `há ${days}d`;
  } catch {
    return "";
  }
}

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
        className="flex items-center gap-2.5 px-2.5 py-[5px] rounded-md border border-gray-200 bg-gray-50 cursor-pointer text-xs text-gray-500 select-none transition-colors"
      >
        <Brain
          className="text-wedo-cyan flex-shrink-0 w-3.5 h-3.5"
        />

        <span
          className="text-gray-800 font-medium whitespace-nowrap"
        >
          {stageName}
        </span>

        <div
          className="flex items-center gap-1 min-w-[80px]"
        >
          <div
            className="bg-gray-200 flex-1 h-1 rounded-[2px] overflow-hidden"
          >
            <div
              className="h-full rounded-[2px] bg-wedo-cyan transition-[width] duration-300 ease-in-out"
              style={{width: `${pct}%`}}
            />
          </div>
          <span className="text-[11px]">
            {pct}%
          </span>
        </div>

        <span
          className="text-gray-400 border-l border-l-gray-200 text-[11px] pl-2"
        >
          {memory.fields_count} campos
        </span>

        {relTime && (
          <span
            className="text-gray-400 border-l border-l-gray-200 text-[11px] pl-2"
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

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div
              className="mt-1 px-3.5 py-3 rounded-md border border-gray-200 bg-gray-50 max-h-[280px] overflow-y-auto text-xs text-gray-800"
            >
              <div
                className="font-semibold text-[13px] mb-2"
              >
                Memória do Agente
              </div>

              <div
                className="bg-gray-200 h-px mb-2"
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
                    className="italic text-[11px]"
                  >
                    {fullMemory.agent_notes}
                  </div>
                </div>
              )}

              {!fullMemory && (
                <div
                  className="text-gray-400 text-[11px] italic"
                >
                  Carregando detalhes...
                </div>
              )}

              <div
                className="bg-gray-200 h-px my-2"
              />

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleReset();
                }}
                className={cn("border flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] cursor-pointer transition-all", confirmReset ? "bg-gray-100 text-gray-600 border-wedo-cyan" : "bg-transparent text-gray-400 border-gray-200")}
              >
                <Trash2 className="w-3 h-3" />
                {confirmReset ? "Confirmar limpeza?" : "Limpar memória"}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
