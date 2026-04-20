import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, Check, ArrowRight, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number; nextHint?: string; group: "funnel" | "utility" };
const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#60BED1", count: 1, nextHint: "publicar 1 rascunho", group: "funnel" },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#5DA47A", count: 12, nextHint: "revisar 12 candidatos", group: "funnel" },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#5DA47A", count: 3, nextHint: "aprovar 3 para entrevista", group: "funnel" },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#D19960", count: 2, nextHint: "revisar 2 entrevistas hoje", group: "funnel" },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#9860D1", count: 1, nextHint: "enviar 1 carta-oferta", group: "funnel" },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#9860D1", group: "funnel" },
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960", group: "utility" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#60BED1", group: "utility" },
];

export function ContrasteForteEnergetico() {
  const [current, setCurrent] = useState("entrevista");
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];
  const utilityStart = STAGES.findIndex((s) => s.group === "utility");

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>BP2 · ContrasteForte · Energético — badges tonais, check em concluídas, hint de próxima ação</span>
        <span>Etapa atual: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      <div className="w-[min(800px,calc(100%-1rem))]">
        <div
          className="rounded-2xl border border-[#1F2937] shadow-[0_18px_40px_-16px_rgba(15,23,42,0.55)] overflow-hidden"
          style={{ background: "linear-gradient(180deg, #111B2F 0%, #0B1322 100%)" }}
        >
          <div className="flex items-center px-3 py-2.5 gap-0.5">
            {STAGES.map((s, i) => {
              const isCurrent = s.key === current;
              const isPast = i < idx;
              const isUtility = s.group === "utility";
              const Icon = s.Icon;
              const insertSep = i === utilityStart;

              return (
                <div key={s.key} className="flex items-center">
                  {i > 0 && !insertSep && (
                    <span
                      aria-hidden
                      className="h-px w-2 mx-px"
                      style={{
                        background:
                          isPast || isCurrent
                            ? `linear-gradient(90deg, ${STAGES[i - 1].accent} 0%, ${s.accent} 100%)`
                            : "rgba(255,255,255,0.10)",
                        opacity: isPast || isCurrent ? 0.85 : 1,
                      }}
                    />
                  )}
                  {insertSep && <span aria-hidden className="h-5 w-px bg-white/12 mx-2" />}

                  <div className="relative">
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
                        ${isCurrent ? "" : isPast ? "hover:ring-1 hover:ring-white/25" : isUtility ? "text-white/35 hover:text-white/65 hover:ring-1 hover:ring-white/15" : "text-white/45 hover:text-white/80 hover:ring-1 hover:ring-white/15"}`}
                    >
                      <Icon className="w-3.5 h-3.5" strokeWidth={isCurrent ? 2.6 : 2} />
                      {isCurrent && <span className="tracking-wide">{s.label}</span>}
                      {/* Past = check overlay */}
                      {isPast && (
                        <span
                          aria-hidden
                          className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full flex items-center justify-center"
                          style={{ backgroundColor: s.accent, color: "#0B1322" }}
                        >
                          <Check className="w-2.5 h-2.5" strokeWidth={3.5} />
                        </span>
                      )}
                      {/* Future with pending = badge in stage accent (not all yellow) */}
                      {!isCurrent && !isPast && s.count != null && s.count > 0 && (
                        <span
                          aria-hidden
                          className="absolute -top-1 -right-1 min-w-[14px] h-[14px] px-1 rounded-full text-[9px] font-bold flex items-center justify-center"
                          style={{ backgroundColor: s.accent, color: "#0B1322" }}
                        >
                          {s.count}
                        </span>
                      )}
                    </button>

                    {/* Current — animated underline */}
                    {isCurrent && (
                      <span
                        aria-hidden
                        className="absolute left-2 right-2 -bottom-1 h-[2px] rounded-full motion-safe:animate-pulse"
                        style={{ backgroundColor: s.accent, opacity: 0.65 }}
                      />
                    )}
                  </div>
                </div>
              );
            })}

            <div className="ml-auto pl-2 flex items-center">
              <span aria-hidden className="h-5 w-px bg-white/15 mr-2" />
              <button
                type="button"
                aria-label="Criar vaga"
                title="Criar vaga"
                className="relative flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold text-[#0B1322] bg-[#5DA47A] hover:bg-[#6FB58A] transition-colors whitespace-nowrap shadow-[0_0_0_3px_rgba(93,164,122,0.22),0_4px_12px_-2px_rgba(93,164,122,0.55)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
              >
                <span aria-hidden className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#FACC15] motion-safe:animate-ping opacity-75" />
                <span aria-hidden className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#FACC15]" />
                <span className="relative inline-flex items-center">
                  <Briefcase className="w-3.5 h-3.5" />
                  <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#0B1322] rounded-full" />
                </span>
                Criar vaga
              </button>
            </div>
          </div>

          <div aria-hidden className="h-px bg-white/10" />
          <div className="flex items-center gap-3 px-3 py-1.5 bg-[#070C16]">
            <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-1.5 py-px rounded text-[#86EFAC] bg-[#86EFAC]/12">
              <span aria-hidden className="w-1.5 h-1.5 rounded-full bg-[#86EFAC] motion-safe:animate-pulse" />
              ao vivo
            </span>
            <span className="text-[10px] text-white/55 truncate flex-1" title="Engenheiro(a) de Dados Sr — Itaú">
              <span className="text-white/95 font-semibold">Eng. Dados Sr — Itaú</span>
            </span>
            {stage.nextHint && (
              <span className="text-[10px] font-semibold inline-flex items-center gap-1 shrink-0" style={{ color: stage.accent }}>
                <ArrowRight className="w-3 h-3" />
                {stage.nextHint}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
