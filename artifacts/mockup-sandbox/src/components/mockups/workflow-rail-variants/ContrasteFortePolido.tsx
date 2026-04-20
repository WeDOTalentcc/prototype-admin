import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, ChevronUp, type LucideIcon,
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
const URGENT_THRESHOLD = 3;

export function ContrasteFortePolido() {
  const [current, setCurrent] = useState("entrevista");
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];
  const utilityStart = STAGES.findIndex((s) => s.group === "utility");

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>BP1 · ContrasteForte · Polido — conectores tonais, divisor de grupos, urgência seletiva</span>
        <span>Etapa atual: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      <div className="w-[min(780px,calc(100%-1rem))]">
        <div
          className="rounded-2xl border border-[#1F2937] shadow-[0_18px_40px_-16px_rgba(15,23,42,0.55)] overflow-hidden"
          style={{ background: "linear-gradient(180deg, #111B2F 0%, #0B1322 100%)" }}
        >
          <div className="flex items-center px-3 py-2 gap-0.5">
            {STAGES.map((s, i) => {
              const isCurrent = s.key === current;
              const isPast = i < idx;
              const isUtility = s.group === "utility";
              const Icon = s.Icon;
              const insertSep = i === utilityStart;
              const isUrgent = (s.count ?? 0) >= URGENT_THRESHOLD && !isCurrent;

              return (
                <div key={s.key} className="flex items-center">
                  {i > 0 && !insertSep && (
                    <span
                      aria-hidden
                      className="h-px w-2 mx-px transition-colors"
                      style={{
                        backgroundColor: isPast || isCurrent ? STAGES[i - 1].accent : "rgba(255,255,255,0.10)",
                        opacity: isPast || isCurrent ? 0.7 : 1,
                      }}
                    />
                  )}
                  {insertSep && (
                    <span aria-hidden className="h-5 w-px bg-white/12 mx-2" />
                  )}

                  <button
                    type="button"
                    onClick={() => setCurrent(s.key)}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={s.count ? `${s.label} — ${s.count} pendência(s)` : s.label}
                    title={s.label}
                    style={
                      isCurrent
                        ? { backgroundColor: s.accent, color: "#0B1322", boxShadow: `0 0 0 2px ${s.accent}40, 0 4px 12px -2px ${s.accent}80` }
                        : isPast
                        ? { color: s.accent }
                        : undefined
                    }
                    className={`relative flex items-center gap-1.5 px-2 py-1 rounded-full text-[11px] font-bold whitespace-nowrap transition-all
                      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70
                      ${isCurrent ? "" : isPast ? "hover:ring-1 hover:ring-white/20" : isUtility ? "text-white/35 hover:text-white/65 hover:ring-1 hover:ring-white/15" : "text-white/45 hover:text-white/80 hover:ring-1 hover:ring-white/15"}`}
                  >
                    <Icon className="w-3.5 h-3.5" strokeWidth={isCurrent ? 2.6 : 2} />
                    {isCurrent && <span className="tracking-wide">{s.label}</span>}
                    {!isCurrent && s.count != null && s.count > 0 && (
                      <span
                        aria-hidden
                        className={`absolute -top-1 -right-1 min-w-[14px] h-[14px] px-1 rounded-full text-[9px] font-bold flex items-center justify-center
                          ${isUrgent ? "bg-[#FACC15] text-[#0B1322] ring-2 ring-[#FACC15]/35 motion-safe:animate-pulse" : "bg-white text-[#0B1322]"}`}
                      >
                        {s.count}
                      </span>
                    )}
                  </button>
                </div>
              );
            })}

            <button
              type="button"
              aria-label="Mais opções do funil"
              title="Mais opções"
              className="ml-1 inline-flex items-center gap-1 px-1.5 py-1 rounded text-[10px] font-semibold text-white/45 hover:text-white hover:bg-white/8 transition-colors"
            >
              <ChevronUp className="w-3.5 h-3.5" /> mais
            </button>

            <div className="ml-auto pl-2 flex items-center">
              <span aria-hidden className="h-5 w-px bg-white/15 mr-2" />
              <button
                type="button"
                aria-label="Criar vaga"
                title="Criar vaga"
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold text-[#0B1322] bg-[#5DA47A] hover:bg-[#6FB58A] transition-colors whitespace-nowrap shadow-[0_0_0_3px_rgba(93,164,122,0.22),0_4px_12px_-2px_rgba(93,164,122,0.55)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
              >
                <span className="relative inline-flex items-center">
                  <Briefcase className="w-3.5 h-3.5" />
                  <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#0B1322] rounded-full" />
                </span>
                Criar vaga
              </button>
            </div>
          </div>

          <div aria-hidden className="h-px bg-white/10" />
          <div className="flex items-center justify-between gap-3 px-3 py-1.5 bg-[#070C16]">
            <span className="text-[10px] text-white/55 truncate" title="Engenheiro(a) de Dados Sr — Itaú">
              Vaga ativa: <span className="text-white/95 font-semibold">Engenheiro(a) de Dados Sr — Itaú</span>
            </span>
            <span className="text-[10px] font-semibold inline-flex items-center gap-1 shrink-0" style={{ color: stage.accent }}>
              <span aria-hidden className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: stage.accent }} />
              {stage.count ?? 0} pendência(s) em <span className="text-white/85">{stage.label.toLowerCase()}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
