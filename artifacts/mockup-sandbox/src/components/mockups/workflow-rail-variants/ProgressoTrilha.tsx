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
  ArrowRight,
  type LucideIcon,
} from "lucide-react";

type Stage = {
  key: string;
  label: string;
  Icon: LucideIcon;
  accent: string;
};

const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#60BED1" },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#5DA47A" },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#5DA47A" },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#D19960" },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#9860D1" },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#9860D1" },
];
const UTILITIES: Stage[] = [
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960" },
  { key: "ia-automacoes", label: "IA", Icon: Sparkles, accent: "#60BED1" },
];

export function ProgressoTrilha() {
  const [current, setCurrent] = useState("sourcing");
  const [hovered, setHovered] = useState<string | null>(null);
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];
  const progressPct = ((idx + 0.5) / STAGES.length) * 100;

  return (
    <div className="min-h-screen w-full bg-[#FAFAF9] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>Variante C · ProgressoTrilha · trilha contínua + nodes</span>
        <span>Etapa atual: <strong className="text-[#6B7280]">{stage.label}</strong></span>
      </div>

      <div className="w-[min(800px,calc(100%-1rem))]">
        <div className="rounded-2xl bg-white border border-[#E5E7EB] shadow-[0_10px_28px_-14px_rgba(17,24,39,0.18)] overflow-hidden">

          <div className="px-5 pt-3.5 pb-1 flex items-center justify-between">
            <div className="text-[11px] font-semibold text-[#111827] inline-flex items-center gap-1.5">
              <stage.Icon className="w-3.5 h-3.5" style={{ color: stage.accent }} />
              {stage.label}
              <span className="text-[10px] font-normal text-[#9CA3AF]">· etapa {idx + 1} de {STAGES.length}</span>
            </div>
            <div className="text-[10px] text-[#9CA3AF] inline-flex items-center gap-1">
              próxima
              <ArrowRight className="w-3 h-3" />
              <span className="text-[#6B7280] font-medium">
                {STAGES[Math.min(idx + 1, STAGES.length - 1)].label}
              </span>
            </div>
          </div>

          <div className="px-5 pt-2 pb-4">
            <div className="relative h-9">
              <div aria-hidden className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1 rounded-full bg-[#F3F4F6]" />
              <div
                aria-hidden
                className="absolute left-0 top-1/2 -translate-y-1/2 h-1 rounded-full transition-all"
                style={{ width: `${progressPct}%`, backgroundColor: stage.accent }}
              />

              <div className="relative h-full flex items-center justify-between">
                {STAGES.map((s, i) => {
                  const isCurrent = s.key === current;
                  const isPast = i < idx;
                  const Icon = s.Icon;
                  return (
                    <div key={s.key} className="relative flex flex-col items-center">
                      <button
                        type="button"
                        onClick={() => setCurrent(s.key)}
                        onMouseEnter={() => setHovered(s.key)}
                        onMouseLeave={() => setHovered(null)}
                        aria-current={isCurrent ? "step" : undefined}
                        aria-label={s.label}
                        title={s.label}
                        style={
                          isCurrent
                            ? { backgroundColor: s.accent, borderColor: s.accent, color: "#fff", boxShadow: `0 0 0 4px ${s.accent}33` }
                            : isPast
                            ? { backgroundColor: s.accent, borderColor: s.accent, color: "#fff" }
                            : undefined
                        }
                        className={`relative z-10 w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
                          ${isCurrent ? "scale-110" : isPast ? "" : "bg-white border-[#E5E7EB] text-[#9CA3AF] hover:border-[#9CA3AF]"}`}
                      >
                        <Icon className="w-3.5 h-3.5" strokeWidth={2.25} />
                      </button>

                      {(isCurrent || hovered === s.key) && (
                        <span
                          className="absolute top-full mt-1 text-[10px] font-semibold whitespace-nowrap"
                          style={{ color: isCurrent ? s.accent : "#6B7280" }}
                        >
                          {s.label}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div aria-hidden className="h-px bg-[#F3F4F6]" />
          <div className="flex items-center justify-between px-5 py-2">
            <div className="flex items-center gap-3">
              {UTILITIES.map((u) => {
                const Icon = u.Icon;
                return (
                  <button
                    key={u.key}
                    type="button"
                    title={u.label}
                    className="inline-flex items-center gap-1 text-[10.5px] font-medium text-[#6B7280] hover:text-[#111827] transition-colors"
                  >
                    <Icon className="w-3.5 h-3.5" style={{ color: u.accent }} />
                    {u.label}
                  </button>
                );
              })}
              <span aria-hidden className="h-3 w-px bg-[#E5E7EB]" />
              <span className="text-[10px] text-[#9CA3AF] truncate max-w-[220px]">
                Engenheiro(a) de Dados Sr — Itaú
              </span>
            </div>

            <button
              type="button"
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[11px] font-bold text-white transition-colors whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50"
              style={{ backgroundColor: "#60BED1" }}
              aria-label="Criar vaga"
              title="Criar vaga"
            >
              <span className="relative inline-flex items-center">
                <Briefcase className="w-3.5 h-3.5" />
                <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#60BED1] rounded-full" />
              </span>
              Criar vaga
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
