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
];
const UTILITIES = [
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960" },
  { key: "ia-automacoes", label: "IA", Icon: Sparkles, accent: "#60BED1" },
];

export function TrilhaClarity() {
  const [current, setCurrent] = useState("sourcing");
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];
  const next = STAGES[Math.min(idx + 1, STAGES.length - 1)];
  const progressPct = ((idx + 0.5) / STAGES.length) * 100;

  return (
    <div className="min-h-screen w-full bg-[#FAFAF9] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>CU1 · Clareza · etapa atual hero, trilha vira micro-stepper subordinado</span>
        <span className="text-[#9CA3AF]">trade-off: futuras etapas perdem leitura imediata de contagem</span>
      </div>

      <div className="w-[min(820px,calc(100%-1rem))] rounded-2xl bg-white border border-[#E5E7EB] shadow-[0_10px_28px_-14px_rgba(17,24,39,0.18)] overflow-hidden">
        {/* HERO — etapa atual dominante */}
        <div className="px-5 py-4 flex items-center gap-3.5">
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
            style={{ backgroundColor: stage.accent, boxShadow: `0 0 0 4px ${stage.accent}22` }}
          >
            <stage.Icon className="w-6 h-6 text-white" strokeWidth={2.4} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-baseline gap-2">
              <span className="text-[10px] font-bold uppercase tracking-[0.12em]" style={{ color: stage.accent }}>
                etapa {idx + 1}/{STAGES.length}
              </span>
              {stage.count != null && stage.count > 0 && (
                <span className="text-[11px] text-[#6B7280] font-semibold">
                  · {stage.count} pendência(s)
                </span>
              )}
            </div>
            <div className="text-[18px] leading-tight font-bold text-[#111827] tracking-tight">{stage.label}</div>
          </div>
          <button
            type="button"
            onClick={() => setCurrent(next.key)}
            className="hidden sm:flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold text-[#6B7280] hover:bg-[#F3F4F6] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 transition-colors"
            aria-label={`Avançar para ${next.label}`}
          >
            <span className="text-[#9CA3AF] font-normal">próxima</span>
            <next.Icon className="w-3.5 h-3.5" style={{ color: next.accent }} />
            <span>{next.label}</span>
            <ArrowRight className="w-3 h-3 text-[#9CA3AF]" />
          </button>
          <button
            type="button"
            aria-label="Criar vaga"
            title="Criar vaga"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold text-white whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 transition-colors"
            style={{ backgroundColor: "#60BED1" }}
          >
            <span className="relative inline-flex items-center">
              <Briefcase className="w-3.5 h-3.5" />
              <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#60BED1] rounded-full" />
            </span>
            Criar vaga
          </button>
        </div>

        {/* MICRO STEPPER — trilha subordinada */}
        <div className="border-t border-[#F3F4F6] bg-[#FAFAF9] px-5 py-2">
          <div className="relative h-3">
            <div aria-hidden className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-[3px] rounded-full bg-[#F3F4F6]" />
            <div
              aria-hidden
              className="absolute left-0 top-1/2 -translate-y-1/2 h-[3px] rounded-full transition-all"
              style={{ width: `${progressPct}%`, backgroundColor: stage.accent, opacity: 0.85 }}
            />
            <div className="relative h-full flex items-center justify-between">
              {STAGES.map((s, i) => {
                const isCurrent = s.key === current;
                const isPast = i < idx;
                return (
                  <button
                    key={s.key}
                    onClick={() => setCurrent(s.key)}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={s.label}
                    title={s.label}
                    className="group relative w-3 h-3 flex items-center justify-center focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#60BED1]/50 rounded-full"
                  >
                    <span
                      aria-hidden
                      className="rounded-full transition-all group-hover:scale-150"
                      style={
                        isCurrent
                          ? { width: 10, height: 10, backgroundColor: s.accent, boxShadow: `0 0 0 3px ${s.accent}33` }
                          : isPast
                          ? { width: 6, height: 6, backgroundColor: s.accent }
                          : { width: 6, height: 6, backgroundColor: "#E5E7EB" }
                      }
                    />
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer — utilities + vaga discretas */}
        <div className="border-t border-[#F3F4F6] px-5 py-1.5 flex items-center gap-3">
          {UTILITIES.map((u) => (
            <button
              key={u.key}
              type="button"
              title={u.label}
              className="inline-flex items-center gap-1 text-[10px] font-medium text-[#9CA3AF] hover:text-[#6B7280] transition-colors"
            >
              <u.Icon className="w-3 h-3" style={{ color: u.accent }} />
              {u.label}
            </button>
          ))}
          <span aria-hidden className="h-3 w-px bg-[#E5E7EB]" />
          <span className="text-[10px] text-[#9CA3AF] truncate flex-1" title="Engenheiro(a) de Dados Sr — Itaú">
            Eng. Dados Sr — Itaú
          </span>
        </div>
      </div>
    </div>
  );
}
