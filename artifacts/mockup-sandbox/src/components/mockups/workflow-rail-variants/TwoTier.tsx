import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, ArrowRight, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number };
const FUNNEL: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#60BED1", count: 1 },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#5DA47A", count: 12 },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#5DA47A", count: 3 },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#D19960", count: 2 },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#9860D1", count: 1 },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#9860D1" },
];
const UTILITIES: Stage[] = [
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#60BED1" },
];
const ALL = [...FUNNEL, ...UTILITIES];

export function TwoTier() {
  const [current, setCurrent] = useState("entrevista");
  const idx = FUNNEL.findIndex((s) => s.key === current);
  const stage = ALL.find((s) => s.key === current)!;

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>L2 · Two-Tier · funil em cima generoso, utilities + footer fundidos embaixo</span>
        <span>Etapa atual: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      <div className="w-[min(820px,calc(100%-1rem))]">
        <div
          className="rounded-2xl border border-[#1F2937] shadow-[0_18px_40px_-16px_rgba(15,23,42,0.55)] overflow-hidden"
          style={{ background: "linear-gradient(180deg, #111B2F 0%, #0B1322 100%)" }}
        >
          {/* TIER 1 — funnel with breathing room + CTA top-right */}
          <div className="px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-white/45">funil de contratação</span>
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

            <div className="flex items-stretch gap-1">
              {FUNNEL.map((s, i) => {
                const isCurrent = s.key === current;
                const isPast = i < idx;
                return (
                  <div key={s.key} className="flex items-stretch flex-1 min-w-0">
                    <button
                      type="button"
                      onClick={() => setCurrent(s.key)}
                      aria-current={isCurrent ? "step" : undefined}
                      aria-label={s.count ? `${s.label} — ${s.count} pendência(s)` : s.label}
                      title={s.label}
                      style={
                        isCurrent
                          ? { backgroundColor: s.accent, color: "#0B1322", boxShadow: `0 0 0 2px ${s.accent}40` }
                          : isPast
                          ? { color: s.accent, borderColor: `${s.accent}66`, backgroundColor: `${s.accent}10` }
                          : undefined
                      }
                      className={`relative flex-1 min-w-0 flex flex-col items-center justify-center gap-0.5 px-1 py-2 rounded-lg border text-[10px] font-bold transition-all
                        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70
                        ${isCurrent ? "border-transparent" : isPast ? "" : "border-white/12 text-white/55 hover:text-white hover:border-white/30 hover:bg-white/5"}`}
                    >
                      <s.Icon className="w-4 h-4" strokeWidth={isCurrent ? 2.6 : 2} />
                      <span className="truncate w-full text-center text-[10px] leading-tight">{s.label}</span>
                      {s.count != null && s.count > 0 && (
                        <span
                          aria-hidden
                          className="absolute -top-1 -right-1 min-w-[16px] h-[16px] px-1 rounded-full text-[9px] font-bold flex items-center justify-center"
                          style={
                            isCurrent
                              ? { backgroundColor: "#0B1322", color: s.accent }
                              : { backgroundColor: s.accent, color: "#0B1322" }
                          }
                        >
                          {s.count}
                        </span>
                      )}
                    </button>
                    {i < FUNNEL.length - 1 && (
                      <span
                        aria-hidden
                        className="self-center w-2 h-px mx-px"
                        style={{
                          backgroundColor: isPast || isCurrent ? FUNNEL[i].accent : "rgba(255,255,255,0.12)",
                          opacity: isPast || isCurrent ? 0.55 : 1,
                        }}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* TIER 2 — utilities + status fundidos */}
          <div className="border-t border-white/8 bg-[#070C16] px-4 py-2 flex items-center gap-3">
            <span className="text-[9px] uppercase tracking-wider text-white/35 shrink-0">utilities</span>
            <div className="flex items-center gap-1">
              {UTILITIES.map((s) => {
                const isCurrent = s.key === current;
                return (
                  <button
                    key={s.key}
                    type="button"
                    onClick={() => setCurrent(s.key)}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={s.label}
                    title={s.label}
                    style={isCurrent ? { backgroundColor: s.accent, color: "#0B1322" } : undefined}
                    className={`flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-bold transition-colors
                      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70
                      ${isCurrent ? "" : "text-white/55 hover:text-white hover:bg-white/8"}`}
                  >
                    <s.Icon className="w-3 h-3" strokeWidth={isCurrent ? 2.6 : 2} />
                    {isCurrent && <span>{s.label}</span>}
                  </button>
                );
              })}
            </div>

            <span aria-hidden className="h-4 w-px bg-white/12 mx-1" />

            <span className="text-[10px] text-white/55 truncate flex-1" title="Engenheiro(a) de Dados Sr — Itaú">
              Vaga ativa: <span className="text-white/95 font-semibold">Eng. Dados Sr — Itaú</span>
            </span>

            <span className="text-[10px] font-semibold inline-flex items-center gap-1 shrink-0" style={{ color: stage.accent }}>
              <ArrowRight className="w-3 h-3" />
              {stage.count ?? 0} em {stage.label.toLowerCase()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
