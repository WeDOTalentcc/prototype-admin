import "./_group.css";
import { useState } from "react";
import {
  Briefcase,
  Search,
  UserCheck,
  Calendar,
  FileText,
  TrendingUp,
  BarChart3,
  Sparkles,
  Plus,
  ChevronUp,
  type LucideIcon,
} from "lucide-react";

type Stage = {
  key: string;
  label: string;
  Icon: LucideIcon;
  accent: string;
  count?: number;
};

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

export function ContrasteForte() {
  const [current, setCurrent] = useState("entrevista");
  const currentIdx = STAGES.findIndex((s) => s.key === current);
  const currentStage = STAGES[currentIdx];

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>Variante B · ContrasteForte · superfície escura + accents vivos</span>
        <span>Etapa atual: <strong className="text-[#111827]">{currentStage.label}</strong></span>
      </div>

      <div className="w-[min(760px,calc(100%-1rem))]">
        <div className="rounded-2xl bg-[#0F172A] shadow-[0_12px_32px_-12px_rgba(15,23,42,0.45)] overflow-hidden border border-[#1F2937]">
          <div className="flex items-center px-3 py-2 gap-1">
            {STAGES.map((stage, idx) => {
              const isCurrent = stage.key === current;
              const isPast = idx < currentIdx;
              const Icon = stage.Icon;

              return (
                <div key={stage.key} className="flex items-center">
                  {idx > 0 && (
                    <span aria-hidden className={`h-px w-2.5 ${isPast || isCurrent ? "bg-white/40" : "bg-white/10"}`} />
                  )}
                  <button
                    type="button"
                    onClick={() => setCurrent(stage.key)}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={stage.count != null && stage.count > 0 ? `${stage.label} — ${stage.count} pendência(s)` : stage.label}
                    title={stage.label}
                    style={
                      isCurrent
                        ? { backgroundColor: stage.accent, color: "#0F172A", boxShadow: `0 0 0 2px ${stage.accent}40` }
                        : isPast
                        ? { color: stage.accent }
                        : undefined
                    }
                    className={`relative flex items-center gap-1.5 px-2 py-1 rounded-full text-[11px] font-bold transition-all whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60
                      ${isCurrent ? "" : isPast ? "hover:bg-white/5" : "text-white/40 hover:text-white/70 hover:bg-white/5"}`}
                  >
                    <Icon className="w-3.5 h-3.5" strokeWidth={isCurrent ? 2.5 : 2} />
                    {isCurrent && <span className="tracking-wide">{stage.label}</span>}
                    {!isCurrent && stage.count != null && stage.count > 0 && (
                      <span className="absolute -top-1 -right-1 min-w-[14px] h-[14px] px-1 rounded-full bg-[#FACC15] text-[#0F172A] text-[9px] font-bold flex items-center justify-center">
                        {stage.count}
                      </span>
                    )}
                  </button>
                </div>
              );
            })}

            <button
              type="button"
              aria-label="Expandir próximos passos"
              className="ml-1 p-1 rounded text-white/50 hover:text-white hover:bg-white/10 transition-colors"
            >
              <ChevronUp className="w-3.5 h-3.5" />
            </button>

            <div className="ml-auto pl-2 flex items-center">
              <span aria-hidden className="h-5 w-px bg-white/15 mr-2" />
              <button
                type="button"
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold text-[#0F172A] bg-[#5DA47A] hover:bg-[#6FB58A] transition-colors whitespace-nowrap shadow-[0_0_0_3px_rgba(93,164,122,0.25)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
                aria-label="Criar vaga"
                title="Criar vaga"
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
            <span className="text-[10px] text-white/60 truncate max-w-[60%]">
              Vaga ativa: <span className="text-white/90 font-semibold">Engenheiro(a) de Dados Sr — Itaú</span>
            </span>
            <span className="text-[10px] text-[#FACC15] font-semibold inline-flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#FACC15] animate-pulse" />
              {currentStage.count ?? 0} pendência(s)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
