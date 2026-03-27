"use client";

import React, { useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Brain, ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { useAgentMemory } from "@/hooks/useAgentMemory";

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
    <div style={{ position: "relative", marginTop: "6px" }}>
      <div
        role="button"
        tabIndex={0}
        onClick={handleExpand}
        onKeyDown={(e) => e.key === "Enter" && handleExpand()}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "5px 10px",
          borderRadius: "6px",
          border: "1px solid var(--eleven-border-subtle, #e5e7eb)",
          backgroundColor: "var(--eleven-bg-card, #f9fafb)",
          cursor: "pointer",
          fontFamily: "Inter, sans-serif",
          fontSize: "12px",
          color: "var(--eleven-text-secondary, #6B7280)",
          userSelect: "none",
          transition: "background-color 0.15s",
        }}
      >
        <Brain
          className="text-wedo-cyan flex-shrink-0"
          style={{ width: 14, height: 14 }}
        />

        <span
          style={{
            color: "var(--eleven-text-primary, #111827)",
            fontWeight: 500,
            whiteSpace: "nowrap",
          }}
        >
          {stageName}
        </span>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            minWidth: 80,
          }}
        >
          <div
            className="bg-gray-200" style={{ flex: 1, height: 4, borderRadius: 2, overflow: "hidden" }}
          >
            <div
              style={{
                width: `${pct}%`,
                height: "100%",
                borderRadius: 2,
                backgroundColor: "#06B6D4",
                transition: "width 0.3s ease",
              }}
            />
          </div>
          <span style={{ fontSize: 11, fontFamily: "Open Sans, sans-serif" }}>
            {pct}%
          </span>
        </div>

        <span
          className="text-gray-400 border-l border-l-gray-200" style={{ fontSize: 11, paddingLeft: 8, fontFamily: "Open Sans, sans-serif" }}
        >
          {memory.fields_count} campos
        </span>

        {relTime && (
          <span
            className="text-gray-400 border-l border-l-gray-200" style={{ fontSize: 11, paddingLeft: 8, fontFamily: "Open Sans, sans-serif" }}
          >
            {relTime}
          </span>
        )}

        {expanded ? (
          <ChevronUp style={{ width: 12, height: 12, marginLeft: "auto" }} />
        ) : (
          <ChevronDown style={{ width: 12, height: 12, marginLeft: "auto" }} />
        )}
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: "hidden" }}
          >
            <div
              style={{
                marginTop: 4,
                padding: "12px 14px",
                borderRadius: 6,
                border: "1px solid var(--eleven-border-subtle, #e5e7eb)",
                backgroundColor: "var(--eleven-bg-card, #f9fafb)",
                maxHeight: 280,
                overflowY: "auto",
                fontFamily: "Inter, sans-serif",
                fontSize: 12,
                color: "var(--eleven-text-primary, #111827)",
              }}
            >
              <div
                style={{
                  fontWeight: 600,
                  fontSize: 13,
                  marginBottom: 8,
                  }}
              >
                Memória do Agente
              </div>

              <div
                className="bg-gray-200" style={{ height: 1, marginBottom: 8 }}
              />

              <div style={{ marginBottom: 6 }}>
                <span style={{ fontWeight: 500 }}>Estágio: </span>
                <span style={{ fontFamily: "Open Sans, sans-serif" }}>
                  {stageName}
                </span>
              </div>

              <div style={{ marginBottom: 10 }}>
                <span style={{ fontWeight: 500 }}>Progresso: </span>
                <span style={{ fontFamily: "Open Sans, sans-serif" }}>
                  {pct}% ({memory.fields_count} campos)
                </span>
              </div>

              {fullMemory &&
                Object.keys(fullMemory.collected_fields).length > 0 && (
                  <div style={{ marginBottom: 10 }}>
                    <div
                      style={{
                        fontWeight: 500,
                        marginBottom: 4,
                        }}
                    >
                      Campos coletados:
                    </div>
                    <ul
                      style={{
                        margin: 0,
                        paddingLeft: 16,
                        listStyleType: "disc",
                      }}
                    >
                      {Object.entries(fullMemory.collected_fields).map(
                        ([key, val]) => (
                          <li
                            key={key}
                            style={{
                              marginBottom: 2,
                              fontFamily: "Open Sans, sans-serif",
                              }}
                          >
                            <span style={{ fontWeight: 500 }}>
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
                  <div style={{ marginBottom: 6 }}>
                    <span style={{ fontWeight: 500 }}>Ações pendentes: </span>
                    <span style={{ fontFamily: "Open Sans, sans-serif" }}>
                      {fullMemory.pending_actions.length}
                    </span>
                  </div>
                )}

              {fullMemory && fullMemory.agent_notes && (
                <div style={{ marginBottom: 10 }}>
                  <div
                    style={{
                      fontWeight: 500,
                      marginBottom: 4,
                      }}
                  >
                    Notas do agente:
                  </div>
                  <div
                    style={{
                      fontFamily: "Open Sans, sans-serif",
                      fontStyle: "italic",
                      fontSize: 11,
                    }}
                  >
                    {fullMemory.agent_notes}
                  </div>
                </div>
              )}

              {!fullMemory && (
                <div
                  className="text-gray-400" style={{ fontSize: 11, fontStyle: "italic" }}
                >
                  Carregando detalhes...
                </div>
              )}

              <div
                className="bg-gray-200" style={{ height: 1, margin: "8px 0" }}
              />

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleReset();
                }}
                className="border border-gray-200" style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 4, backgroundColor: confirmReset ? "#f3f4f6" : "transparent", color: confirmReset ? "var(--gray-600)" : "var(--gray-400)", borderColor: confirmReset ? "#06B6D4" : "var(--gray-200)", fontSize: 11, fontFamily: "Inter, sans-serif", cursor: "pointer", transition: "all 0.15s" }}
              >
                <Trash2 style={{ width: 12, height: 12 }} />
                {confirmReset ? "Confirmar limpeza?" : "Limpar memória"}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
