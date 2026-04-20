import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, ArrowRight, MousePointerClick, type LucideIcon,
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

export function TrilhaAffordance() {
  const [current, setCurrent] = useState("sourcing");
  const [pressed, setPressed] = useState<string | null>(null);
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];
  const progressPct = ((idx + 0.5) / STAGES.length) * 100;

  return (
    <div className="min-h-screen w-full bg-[#FAFAF9] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>CU2 · Affordance · nodes com sombra "tecla", press visível, micro-copy de ação</span>
        <span className="text-[#9CA3AF]">trade-off: mais chrome, perde minimalismo</span>
      </div>

      <div className="w-[min(820px,calc(100%-1rem))] rounded-2xl bg-white border border-[#E5E7EB] shadow-[0_10px_28px_-14px_rgba(17,24,39,0.18)] overflow-hidden">
        <div className="px-5 pt-3.5 pb-1 flex items-center justify-between">
          <div className="text-[11px] font-bold text-[#111827] inline-flex items-center gap-1.5">
            <stage.Icon className="w-3.5 h-3.5" style={{ color: stage.accent }} />
            {stage.label}
            <span className="text-[10px] font-normal text-[#9CA3AF]">· etapa {idx + 1} de {STAGES.length}</span>
          </div>
          <span className="text-[10px] text-[#6B7280] inline-flex items-center gap-1 font-medium">
            <MousePointerClick className="w-3 h-3 text-[#60BED1]" />
            clique num node para abrir
          </span>
        </div>

        <div className="px-5 pt-3 pb-5">
          <div className="relative h-12">
            <div aria-hidden className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-[5px] rounded-full bg-[#F3F4F6] shadow-inner" />
            <div
              aria-hidden
              className="absolute left-0 top-1/2 -translate-y-1/2 h-[5px] rounded-full transition-all"
              style={{ width: `${progressPct}%`, backgroundColor: stage.accent, boxShadow: `0 0 8px ${stage.accent}66` }}
            />

            <div className="relative h-full flex items-center justify-between">
              {STAGES.map((s, i) => {
                const isCurrent = s.key === current;
                const isPast = i < idx;
                const isPressed = pressed === s.key;
                return (
                  <div key={s.key} className="relative flex flex-col items-center">
                    <button
                      type="button"
                      onClick={() => setCurrent(s.key)}
                      onMouseDown={() => setPressed(s.key)}
                      onMouseUp={() => setPressed(null)}
                      onMouseLeave={() => setPressed(null)}
                      aria-current={isCurrent ? "step" : undefined}
                      aria-label={s.count ? `${s.label} — ${s.count} pendência(s), clique para abrir` : `${s.label} — clique para abrir`}
                      title={`Abrir ${s.label}`}
                      style={
                        isCurrent
                          ? { backgroundColor: s.accent, borderColor: s.accent, color: "#fff" }
                          : isPast
                          ? { backgroundColor: s.accent, borderColor: s.accent, color: "#fff" }
                          : undefined
                      }
                      className={`relative z-10 w-9 h-9 rounded-full border-2 flex items-center justify-center cursor-pointer
                        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 transition-all
                        ${isCurrent ? "scale-110 shadow-[0_4px_0_0_rgba(0,0,0,0.15),0_8px_18px_-4px_var(--accent)]" : ""}
                        ${!isCurrent && !isPast ? "bg-white border-[#D1D5DB] text-[#6B7280] shadow-[0_3px_0_0_rgba(17,24,39,0.10)] hover:border-[#9CA3AF] hover:-translate-y-[1px] hover:shadow-[0_4px_0_0_rgba(17,24,39,0.12)]" : ""}
                        ${isPast ? "shadow-[0_3px_0_0_rgba(17,24,39,0.18)] hover:-translate-y-[1px]" : ""}
                        ${isPressed ? "translate-y-[2px] shadow-none" : ""}`}
                    >
                      <s.Icon className="w-4 h-4" strokeWidth={isCurrent ? 2.5 : 2.2} />
                      {!isCurrent && s.count != null && s.count > 0 && (
                        <span
                          aria-hidden
                          className="absolute -top-1 -right-1 min-w-[16px] h-[16px] px-1 rounded-full bg-white border-2 text-[9px] font-bold flex items-center justify-center"
                          style={{ borderColor: s.accent, color: s.accent }}
                        >
                          {s.count}
                        </span>
                      )}
                    </button>
                    <span
                      className="absolute top-full mt-1.5 text-[10px] font-semibold whitespace-nowrap"
                      style={{ color: isCurrent ? s.accent : isPast ? "#6B7280" : "#9CA3AF" }}
                    >
                      {s.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div aria-hidden className="h-px bg-[#F3F4F6]" />
        <div className="flex items-center justify-between px-5 py-2 gap-3">
          <div className="flex items-center gap-2">
            {UTILITIES.map((u) => (
              <button
                key={u.key}
                type="button"
                title={u.label}
                className="inline-flex items-center gap-1 px-2 py-1 rounded border border-[#E5E7EB] text-[10.5px] font-semibold text-[#6B7280] hover:text-[#111827] hover:border-[#9CA3AF] hover:-translate-y-px hover:shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50"
              >
                <u.Icon className="w-3.5 h-3.5" style={{ color: u.accent }} />
                {u.label}
              </button>
            ))}
            <span aria-hidden className="h-3 w-px bg-[#E5E7EB] mx-1" />
            <span className="text-[10px] text-[#9CA3AF] truncate max-w-[200px]">
              Eng. Dados Sr — Itaú
            </span>
          </div>

          <button
            type="button"
            onMouseDown={() => setPressed("__cta")}
            onMouseUp={() => setPressed(null)}
            onMouseLeave={() => setPressed(null)}
            aria-label="Criar nova vaga — abre formulário"
            title="Criar nova vaga"
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[11px] font-bold text-white whitespace-nowrap transition-all
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
              shadow-[0_3px_0_0_rgba(17,24,39,0.18),0_6px_16px_-4px_rgba(96,190,209,0.6)] hover:-translate-y-[1px]
              ${pressed === "__cta" ? "translate-y-[2px] shadow-[0_1px_0_0_rgba(17,24,39,0.18)]" : ""}`}
            style={{ backgroundColor: "#60BED1" }}
          >
            <span className="relative inline-flex items-center">
              <Briefcase className="w-3.5 h-3.5" />
              <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#60BED1] rounded-full" />
            </span>
            Criar vaga
            <ArrowRight className="w-3 h-3 opacity-80" />
          </button>
        </div>
      </div>
    </div>
  );
}
