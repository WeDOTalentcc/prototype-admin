import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, Check, ArrowRight, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number };

const FLOW: Stage[] = [
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

export function DarkPolished() {
  const [current, setCurrent] = useState("entrevista");
  const idx = FLOW.findIndex((s) => s.key === current);
  const stage = FLOW[idx];
  const next = FLOW[Math.min(idx + 1, FLOW.length - 1)];

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>BP3 · Dark Polished · stages e utilities separados, past com ✓, próxima inline</span>
        <span>Etapa atual: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      <div className="w-[min(800px,calc(100%-1rem))]">
        <div className="rounded-2xl bg-[#0F172A] shadow-[0_12px_32px_-12px_rgba(15,23,42,0.5)] overflow-hidden border border-[#1F2937]">
          <div className="flex items-center px-2.5 py-2 gap-0.5">
            {/* FLOW segment */}
            {FLOW.map((s, i) => {
              const isCurrent = s.key === current;
              const isPast = i < idx;
              const Icon = s.Icon;
              return (
                <div key={s.key} className="flex items-center">
                  {i > 0 && (
                    <span
                      aria-hidden
                      className="h-[2px] w-3 rounded-full mx-0.5"
                      style={{
                        background: isPast || isCurrent
                          ? `linear-gradient(90deg, ${FLOW[i - 1].accent}cc, ${s.accent}${isCurrent ? "66" : "cc"})`
                          : "rgba(255,255,255,0.08)",
                      }}
                    />
                  )}
                  <button
                    type="button"
                    onClick={() => setCurrent(s.key)}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={s.count ? `${s.label} — ${s.count} pendência(s)` : s.label}
                    title={s.label}
                    style={
                      isCurrent
                        ? { backgroundColor: s.accent, color: "#0F172A", boxShadow: `0 0 0 3px ${s.accent}33, 0 4px 12px -2px ${s.accent}80` }
                        : isPast
                        ? { backgroundColor: `${s.accent}1F`, color: s.accent }
                        : undefined
                    }
                    className={`relative flex items-center gap-1.5 px-2 py-1 rounded-full text-[11px] font-bold transition-all whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60
                      ${isCurrent ? "" : isPast ? "" : "text-white/40 hover:text-white/80 hover:bg-white/5"}`}
                  >
                    {isPast ? (
                      <Check className="w-3.5 h-3.5" strokeWidth={2.75} />
                    ) : (
                      <Icon className="w-3.5 h-3.5" strokeWidth={isCurrent ? 2.5 : 2} />
                    )}
                    {isCurrent && <span className="tracking-wide">{s.label}</span>}
                    {!isCurrent && s.count != null && s.count > 0 && (
                      <span
                        aria-hidden
                        className="absolute -top-1 -right-1 min-w-[14px] h-[14px] px-1 rounded-full text-[9px] font-bold flex items-center justify-center"
                        style={{ backgroundColor: s.accent, color: "#0F172A" }}
                      >
                        {s.count}
                      </span>
                    )}
                  </button>
                  {isCurrent && (
                    <span
                      className="ml-1.5 inline-flex items-center gap-1 text-[10px] text-white/60 font-medium"
                      aria-label={`próxima: ${next.label}`}
                    >
                      <ArrowRight className="w-3 h-3" />
                      <next.Icon className="w-3 h-3" style={{ color: next.accent }} />
                      <span className="text-white/80">{next.label}</span>
                    </span>
                  )}
                </div>
              );
            })}

            {/* UTILITIES compartment */}
            <span aria-hidden className="ml-2 mr-1.5 h-5 w-px bg-white/15" />
            {UTILITIES.map((u) => (
              <button
                key={u.key}
                type="button"
                title={u.label}
                aria-label={u.label}
                className="flex items-center gap-1.5 px-2 py-1 rounded-full text-[11px] font-semibold text-white/55 hover:text-white hover:bg-white/5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
              >
                <u.Icon className="w-3.5 h-3.5" style={{ color: u.accent }} strokeWidth={2} />
              </button>
            ))}

            {/* CTA */}
            <div className="ml-auto pl-2 flex items-center">
              <span aria-hidden className="h-5 w-px bg-white/15 mr-2" />
              <button
                type="button"
                aria-label="Criar vaga"
                title="Criar vaga"
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold text-[#0F172A] bg-[#5DA47A] hover:bg-[#6FB58A] transition-colors whitespace-nowrap shadow-[0_0_0_3px_rgba(93,164,122,0.22),0_4px_12px_-2px_rgba(93,164,122,0.55)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
              >
                <span className="relative inline-flex items-center">
                  <Briefcase className="w-3.5 h-3.5" />
                  <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#0F172A] rounded-full" />
                </span>
                Criar vaga
              </button>
            </div>
          </div>

          <div aria-hidden className="h-px bg-white/10" />
          <div className="flex items-center justify-between px-3 py-1.5 bg-[#111827]">
            <span className="text-[10px] text-white/55 truncate max-w-[60%]">
              Vaga ativa: <span className="text-white/95 font-semibold">Engenheiro(a) de Dados Sr — Itaú</span>
            </span>
            <span
              className="text-[10px] font-bold inline-flex items-center gap-1.5"
              style={{ color: stage.accent }}
            >
              <span aria-hidden className="w-1.5 h-1.5 rounded-full motion-safe:animate-pulse" style={{ backgroundColor: stage.accent }} />
              {stage.count ?? 0} pendência(s) em {stage.label}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
