import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, ArrowRight, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number };
const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#60BED1", count: 1 },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#5DA47A", count: 12 },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#5DA47A", count: 3 },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#D19960", count: 2 },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#9860D1", count: 1 },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#9860D1" },
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#60BED1" },
];

export function ClarityHierarchy() {
  const [current, setCurrent] = useState("entrevista");
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];
  const next = STAGES[Math.min(idx + 1, STAGES.length - 1)];

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>C1 · Clareza · 1 dominante, 1 secundário, resto subordinado</span>
        <span className="text-[#9CA3AF]">trade-off: menos scannable para futuras etapas</span>
      </div>

      <div className="w-[min(780px,calc(100%-1rem))] rounded-2xl bg-[#0F172A] border border-[#1F2937] shadow-[0_12px_32px_-12px_rgba(15,23,42,0.45)] overflow-hidden">
        {/* PRIMARY band — dominant */}
        <div className="px-4 py-3 flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            style={{ backgroundColor: stage.accent, boxShadow: `0 0 0 4px ${stage.accent}33` }}
          >
            <stage.Icon className="w-5 h-5 text-[#0F172A]" strokeWidth={2.6} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2">
              <span className="text-[10px] font-bold uppercase tracking-[0.12em]" style={{ color: stage.accent }}>etapa {idx + 1}/{STAGES.length}</span>
              {stage.count != null && stage.count > 0 && (
                <span className="text-[10px] text-[#FACC15] font-semibold">{stage.count} pendência(s)</span>
              )}
            </div>
            <div className="text-[18px] leading-tight font-bold text-white tracking-tight">{stage.label}</div>
          </div>

          {/* SECONDARY — next action */}
          <button
            type="button"
            onClick={() => setCurrent(next.key)}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-white text-[11px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
            aria-label={`Avançar para ${next.label}`}
          >
            <span className="text-white/60 font-normal">próxima</span>
            <next.Icon className="w-3.5 h-3.5" style={{ color: next.accent }} />
            <span>{next.label}</span>
            <ArrowRight className="w-3 h-3 opacity-60" />
          </button>

          {/* CTA — accent, but smaller than primary */}
          <button
            type="button"
            aria-label="Criar vaga"
            title="Criar vaga"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold text-[#0F172A] bg-[#5DA47A] hover:bg-[#6FB58A] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 whitespace-nowrap"
          >
            <span className="relative inline-flex items-center">
              <Briefcase className="w-3.5 h-3.5" />
              <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#0F172A] rounded-full" />
            </span>
            Criar vaga
          </button>
        </div>

        {/* TERTIARY band — full funnel, deeply subordinate */}
        <div aria-hidden className="h-px bg-white/8" />
        <div className="px-4 py-1.5 bg-[#0B1220] flex items-center gap-1.5">
          <span className="text-[9px] uppercase tracking-wider text-white/35 mr-1">funil</span>
          {STAGES.map((s, i) => {
            const isCur = s.key === current;
            const isPast = i < idx;
            return (
              <button
                key={s.key}
                onClick={() => setCurrent(s.key)}
                aria-current={isCur ? "step" : undefined}
                aria-label={s.label}
                title={s.label}
                className="group relative w-5 h-5 flex items-center justify-center rounded transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white/60"
              >
                <span
                  aria-hidden
                  className="w-1.5 h-1.5 rounded-full transition-all group-hover:scale-150"
                  style={{
                    backgroundColor: isCur ? s.accent : isPast ? `${s.accent}AA` : "rgba(255,255,255,0.18)",
                    boxShadow: isCur ? `0 0 0 3px ${s.accent}40` : undefined,
                  }}
                />
              </button>
            );
          })}
          <span className="ml-auto text-[10px] text-white/40">Vaga: <span className="text-white/70">Eng. Dados Sr — Itaú</span></span>
        </div>
      </div>
    </div>
  );
}
