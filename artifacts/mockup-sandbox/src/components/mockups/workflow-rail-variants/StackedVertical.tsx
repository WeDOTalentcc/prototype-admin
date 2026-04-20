import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, Check, ChevronRight, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number; group: "funnel" | "utility" };
const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#60BED1", count: 1, group: "funnel" },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#5DA47A", count: 12, group: "funnel" },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#5DA47A", count: 3, group: "funnel" },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#D19960", count: 2, group: "funnel" },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#9860D1", count: 1, group: "funnel" },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#9860D1", group: "funnel" },
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960", group: "utility" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#60BED1", group: "utility" },
];

export function StackedVertical() {
  const [current, setCurrent] = useState("entrevista");
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-center justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>L1 · Stacked Vertical · timeline empilhada para painel lateral estreito</span>
        <span>Etapa atual: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      <div
        className="w-[300px] rounded-2xl border border-[#1F2937] shadow-[0_18px_40px_-16px_rgba(15,23,42,0.55)] overflow-hidden"
        style={{ background: "linear-gradient(180deg, #111B2F 0%, #0B1322 100%)" }}
      >
        {/* Header — vaga + CTA */}
        <div className="px-3 py-2.5 flex items-center gap-2 border-b border-white/8">
          <span className="text-[10px] uppercase tracking-wider text-white/45 shrink-0">vaga</span>
          <span className="text-[11px] font-bold text-white truncate flex-1" title="Engenheiro(a) de Dados Sr — Itaú">
            Eng. Dados Sr — Itaú
          </span>
          <button
            type="button"
            aria-label="Criar vaga"
            title="Criar vaga"
            className="shrink-0 w-6 h-6 rounded-md flex items-center justify-center bg-[#5DA47A] text-[#0B1322] hover:bg-[#6FB58A] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" strokeWidth={3} />
          </button>
        </div>

        {/* Stages — vertical list */}
        <ol className="m-0 p-0 list-none">
          {STAGES.map((s, i) => {
            const isCurrent = s.key === current;
            const isPast = i < idx;
            const isUtility = s.group === "utility";
            const prevWasFunnel = i > 0 && STAGES[i - 1].group === "funnel";
            const insertSep = isUtility && prevWasFunnel;

            return (
              <li key={s.key}>
                {insertSep && (
                  <div className="px-3 py-1 text-[9px] uppercase tracking-wider text-white/35 bg-black/20">utilities</div>
                )}
                <button
                  type="button"
                  onClick={() => setCurrent(s.key)}
                  aria-current={isCurrent ? "step" : undefined}
                  aria-label={s.count ? `${s.label} — ${s.count} pendência(s)` : s.label}
                  className={`group w-full flex items-center gap-2 px-3 py-2 text-left transition-colors relative
                    focus-visible:outline-none focus-visible:bg-white/8
                    ${isCurrent ? "bg-white/5" : "hover:bg-white/5"}`}
                >
                  {/* Rail spine */}
                  <div className="relative flex flex-col items-center w-5 shrink-0 self-stretch">
                    {i > 0 && (
                      <span
                        aria-hidden
                        className="absolute top-0 bottom-1/2 w-px"
                        style={{ backgroundColor: isPast || isCurrent ? STAGES[i - 1].accent : "rgba(255,255,255,0.10)", opacity: isPast || isCurrent ? 0.6 : 1 }}
                      />
                    )}
                    {i < STAGES.length - 1 && (
                      <span
                        aria-hidden
                        className="absolute top-1/2 bottom-0 w-px"
                        style={{ backgroundColor: isPast ? s.accent : "rgba(255,255,255,0.10)", opacity: isPast ? 0.6 : 1 }}
                      />
                    )}
                    <span
                      aria-hidden
                      className="relative z-10 w-5 h-5 rounded-full flex items-center justify-center"
                      style={
                        isCurrent
                          ? { backgroundColor: s.accent, boxShadow: `0 0 0 3px ${s.accent}40` }
                          : isPast
                          ? { backgroundColor: s.accent }
                          : { backgroundColor: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.18)" }
                      }
                    >
                      {isPast ? (
                        <Check className="w-3 h-3 text-[#0B1322]" strokeWidth={3.5} />
                      ) : (
                        <s.Icon className="w-3 h-3" style={{ color: isCurrent ? "#0B1322" : "rgba(255,255,255,0.55)" }} strokeWidth={isCurrent ? 2.6 : 2} />
                      )}
                    </span>
                  </div>

                  {/* Label + count */}
                  <span className={`text-[12px] font-semibold flex-1 ${isCurrent ? "text-white" : isPast ? "text-white/65" : "text-white/55"}`}>
                    {s.label}
                  </span>
                  {s.count != null && s.count > 0 && (
                    <span
                      className={`text-[10px] font-bold px-1.5 py-px rounded-full ${isCurrent ? "" : "ring-1"}`}
                      style={
                        isCurrent
                          ? { backgroundColor: "#0B1322", color: s.accent }
                          : { color: s.accent, borderColor: `${s.accent}66`, backgroundColor: `${s.accent}14` }
                      }
                    >
                      {s.count}
                    </span>
                  )}
                  {isCurrent && <ChevronRight className="w-3.5 h-3.5 text-white/60" />}
                </button>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
