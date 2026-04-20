import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, Check, Circle, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number };
const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#7DD3FC", count: 1 },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#86EFAC", count: 12 },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#86EFAC", count: 3 },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#FCD34D", count: 2 },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#D8B4FE", count: 1 },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#D8B4FE" },
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#FDBA74" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#7DD3FC" },
];

export function AccessibilityFirst() {
  const [current, setCurrent] = useState("entrevista");
  const idx = STAGES.findIndex((s) => s.key === current);

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[12px] text-[#374151] flex items-center justify-between">
        <span>C3 · Acessibilidade · WCAG AAA, 14px+, alvos 44px, status redundante (cor+ícone+texto)</span>
        <span className="text-[#6B7280]">trade-off: ocupa mais espaço, menos compacto</span>
      </div>

      <div className="w-[min(820px,calc(100%-1rem))] rounded-2xl bg-[#0B1220] border-2 border-[#1F2937] shadow-[0_12px_32px_-12px_rgba(11,18,32,0.55)] overflow-hidden">
        {/* Live region for current stage announcement */}
        <div role="status" aria-live="polite" className="sr-only">
          Etapa atual: {STAGES[idx].label}, etapa {idx + 1} de {STAGES.length}
        </div>

        <div className="px-3 py-3">
          <ol className="flex items-stretch gap-1.5 list-none m-0 p-0" aria-label="Etapas do funil de contratação">
            {STAGES.map((stage, i) => {
              const isCurrent = stage.key === current;
              const isPast = i < idx;
              const status = isPast ? "concluída" : isCurrent ? "atual" : "futura";
              const Icon = stage.Icon;
              const StatusGlyph = isPast ? Check : isCurrent ? Circle : null;

              return (
                <li key={stage.key} className="flex">
                  <button
                    type="button"
                    onClick={() => setCurrent(stage.key)}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={`${stage.label}, etapa ${i + 1} de ${STAGES.length}, ${status}${stage.count ? `, ${stage.count} pendências` : ""}`}
                    style={
                      isCurrent
                        ? { backgroundColor: stage.accent, color: "#0B1220" }
                        : isPast
                        ? { color: stage.accent, borderColor: `${stage.accent}80` }
                        : { color: "#FFFFFF", borderColor: "rgba(255,255,255,0.35)" }
                    }
                    className={`group relative flex flex-col items-center justify-center gap-1 min-w-[88px] min-h-[64px] px-2.5 py-2 rounded-xl border-2 text-[13px] font-bold transition-colors
                      focus:outline-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-[#FCD34D] focus-visible:outline-offset-2
                      ${isCurrent ? "" : "hover:bg-white/10"}
                      motion-reduce:transition-none`}
                  >
                    <div className="flex items-center gap-1">
                      <Icon className="w-5 h-5" strokeWidth={isCurrent ? 2.6 : 2.2} aria-hidden />
                      {StatusGlyph && <StatusGlyph className="w-3.5 h-3.5" aria-hidden strokeWidth={3} fill={isCurrent ? stage.accent : undefined} />}
                    </div>
                    <span className="text-[12px] leading-tight text-center">{stage.label}</span>
                    {/* Status text — redundant with color, never color-only */}
                    <span className="text-[9px] uppercase tracking-wider opacity-80 leading-none">{status}</span>
                    {stage.count != null && stage.count > 0 && (
                      <span
                        className={`absolute -top-2 -right-2 min-w-[22px] h-[22px] px-1.5 rounded-full text-[12px] font-bold flex items-center justify-center border-2
                          ${isCurrent ? "bg-[#0B1220] text-white border-[#0B1220]" : "bg-[#FCD34D] text-[#0B1220] border-[#0B1220]"}`}
                        aria-hidden
                      >
                        {stage.count}
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ol>
        </div>

        {/* Footer — large CTA + readable status */}
        <div className="border-t-2 border-white/10 bg-[#070C16] px-3 py-2.5 flex items-center gap-3">
          <span className="text-[13px] text-white">
            <span className="text-white/65">Vaga ativa:</span>{" "}
            <span className="font-bold">Eng. Dados Sr — Itaú</span>
          </span>

          <span className="ml-auto text-[12px] text-[#FCD34D] font-bold inline-flex items-center gap-1.5">
            <Circle className="w-2.5 h-2.5 fill-current" aria-hidden />
            <span>Pendente: ação necessária</span>
          </span>

          <button
            type="button"
            aria-label="Criar nova vaga"
            title="Criar nova vaga"
            className="flex items-center gap-2 px-4 min-h-[44px] rounded-xl text-[14px] font-bold text-[#0B1220] bg-[#86EFAC] hover:bg-[#A7F3C2] transition-colors whitespace-nowrap
              focus:outline-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-[#FCD34D] focus-visible:outline-offset-2
              motion-reduce:transition-none"
          >
            <span className="relative inline-flex items-center">
              <Briefcase className="w-5 h-5" strokeWidth={2.6} aria-hidden />
              <Plus className="w-2.5 h-2.5 absolute -top-0.5 -right-0.5 bg-[#0B1220] text-[#86EFAC] rounded-full" aria-hidden />
            </span>
            Criar vaga
          </button>
        </div>
      </div>
    </div>
  );
}
