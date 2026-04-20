import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, ArrowRight, GripVertical, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number; disabled?: boolean };
const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#60BED1", count: 1 },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#5DA47A", count: 12 },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#5DA47A", count: 3 },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#D19960", count: 2 },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#9860D1", count: 1 },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#9860D1" },
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#60BED1", disabled: true },
];

export function AffordanceMaximal() {
  const [current, setCurrent] = useState("entrevista");
  const [pressed, setPressed] = useState<string | null>(null);
  const idx = STAGES.findIndex((s) => s.key === current);

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>C2 · Affordance · tudo clicável parece clicável (borda + hover + press)</span>
        <span className="text-[#9CA3AF]">trade-off: mais chrome visual, menos minimalismo</span>
      </div>

      <div className="w-[min(820px,calc(100%-1rem))] rounded-2xl bg-[#0F172A] border border-[#1F2937] shadow-[0_12px_32px_-12px_rgba(15,23,42,0.45)] p-2.5">
        <div className="flex items-stretch gap-1.5">
          {STAGES.map((stage, i) => {
            const isCurrent = stage.key === current;
            const isPast = i < idx;
            const isPressed = pressed === stage.key;
            const isDisabled = !!stage.disabled;
            const Icon = stage.Icon;

            return (
              <button
                key={stage.key}
                type="button"
                disabled={isDisabled}
                onClick={() => !isDisabled && setCurrent(stage.key)}
                onMouseDown={() => !isDisabled && setPressed(stage.key)}
                onMouseUp={() => setPressed(null)}
                onMouseLeave={() => setPressed(null)}
                aria-current={isCurrent ? "step" : undefined}
                aria-label={
                  isDisabled ? `${stage.label} — indisponível` :
                  stage.count ? `${stage.label} — ${stage.count} pendências, clique para abrir` :
                  `${stage.label} — clique para abrir`
                }
                title={isDisabled ? `${stage.label} (indisponível)` : `Abrir ${stage.label}`}
                style={
                  isCurrent
                    ? { backgroundColor: stage.accent, color: "#0F172A", borderColor: stage.accent }
                    : isPast
                    ? { borderColor: `${stage.accent}66`, color: stage.accent }
                    : undefined
                }
                className={`group relative flex flex-col items-center gap-0.5 px-1.5 py-1.5 rounded-lg border-2 text-[10px] font-bold transition-all
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70
                  ${isCurrent ? "shadow-[0_4px_0_0_rgba(0,0,0,0.35)]" : ""}
                  ${isPressed && !isCurrent ? "translate-y-[2px] shadow-none" : ""}
                  ${!isCurrent && !isPast && !isDisabled ? "border-white/15 text-white/70 hover:border-white/40 hover:bg-white/5 hover:-translate-y-[1px] hover:shadow-[0_3px_0_0_rgba(0,0,0,0.3)]" : ""}
                  ${isPast && !isCurrent ? "hover:bg-white/5 hover:-translate-y-[1px] hover:shadow-[0_3px_0_0_rgba(0,0,0,0.3)]" : ""}
                  ${isDisabled ? "opacity-35 cursor-not-allowed border-dashed border-white/15 text-white/40" : "cursor-pointer"}`}
              >
                <Icon className="w-4 h-4" strokeWidth={isCurrent ? 2.6 : 2.2} />
                <span className="leading-tight max-w-[64px] truncate">{stage.label}</span>
                {!isCurrent && stage.count != null && stage.count > 0 && (
                  <span
                    aria-hidden
                    className="absolute -top-1 -right-1 min-w-[16px] h-[16px] px-1 rounded-full bg-[#FACC15] text-[#0F172A] text-[9px] font-bold flex items-center justify-center border border-[#0F172A]"
                  >
                    {stage.count}
                  </span>
                )}
                {isDisabled && (
                  <span className="absolute top-0.5 right-0.5 text-[7px] text-white/50 uppercase tracking-wider">soon</span>
                )}
                {/* Drag handle visible on hover — affordance for reorder */}
                {!isDisabled && !isCurrent && (
                  <span aria-hidden className="absolute -left-px top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-60 transition-opacity">
                    <GripVertical className="w-2.5 h-2.5 text-white/50" />
                  </span>
                )}
              </button>
            );
          })}

          <span aria-hidden className="w-px self-stretch bg-white/15 mx-1" />

          {/* CTA — clearly the primary action */}
          <button
            type="button"
            onMouseDown={() => setPressed("__cta")}
            onMouseUp={() => setPressed(null)}
            onMouseLeave={() => setPressed(null)}
            aria-label="Criar nova vaga — abre formulário"
            title="Criar nova vaga"
            className={`relative flex flex-col items-center justify-center gap-0.5 px-3 py-1.5 rounded-lg border-2 border-[#5DA47A] bg-[#5DA47A] text-[#0F172A] text-[10px] font-bold transition-all
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70
              shadow-[0_4px_0_0_rgba(0,0,0,0.35)]
              hover:bg-[#6FB58A] hover:border-[#6FB58A]
              ${pressed === "__cta" ? "translate-y-[3px] shadow-[0_1px_0_0_rgba(0,0,0,0.35)]" : ""}`}
          >
            <span className="relative inline-flex items-center">
              <Briefcase className="w-4 h-4" strokeWidth={2.6} />
              <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-[#0F172A] text-[#5DA47A] rounded-full" />
            </span>
            <span className="leading-tight">Criar vaga</span>
          </button>
        </div>

        {/* Help row — explicit micro-copy of next action */}
        <div className="mt-2 pt-2 border-t border-white/8 flex items-center justify-between text-[10px]">
          <span className="text-white/50 inline-flex items-center gap-1">
            <ArrowRight className="w-3 h-3 text-[#FACC15]" />
            <span className="text-white/80">Clique numa etapa para abrir</span>, segure
            <span className="font-mono mx-1 px-1 py-px rounded bg-white/10 text-white/80">⇧</span>
            para selecionar várias
          </span>
          <span className="text-white/50">{idx + 1} de {STAGES.length}</span>
        </div>
      </div>
    </div>
  );
}
