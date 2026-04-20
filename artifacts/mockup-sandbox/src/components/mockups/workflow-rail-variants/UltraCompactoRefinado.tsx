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
  short: string;
  Icon: LucideIcon;
  accent: string;
  hint: string;
  count?: number;
  group: "funnel" | "utility";
};

const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", short: "Vaga", Icon: Briefcase, accent: "#60BED1", hint: "1 rascunho aberto", count: 1, group: "funnel" },
  { key: "sourcing", label: "Sourcing", short: "Sourcing", Icon: Search, accent: "#5DA47A", hint: "12 candidatos novos", count: 12, group: "funnel" },
  { key: "triagem", label: "Triagem", short: "Triagem", Icon: UserCheck, accent: "#5DA47A", hint: "3 aguardando review", count: 3, group: "funnel" },
  { key: "entrevista", label: "Entrevista", short: "Entrev.", Icon: Calendar, accent: "#D19960", hint: "2 agendadas hoje", count: 2, group: "funnel" },
  { key: "oferta", label: "Oferta", short: "Oferta", Icon: FileText, accent: "#9860D1", hint: "1 carta pendente", count: 1, group: "funnel" },
  { key: "contratacao", label: "Contratação", short: "Contrat.", Icon: TrendingUp, accent: "#9860D1", hint: "—", group: "funnel" },
  { key: "analytics", label: "Analytics", short: "BI", Icon: BarChart3, accent: "#D1A960", hint: "Relatório semanal", group: "utility" },
  { key: "ia-automacoes", label: "IA & Automações", short: "IA", Icon: Sparkles, accent: "#60BED1", hint: "2 agentes ativos", group: "utility" },
];

export function UltraCompactoRefinado() {
  const [current, setCurrent] = useState("triagem");
  const [hovered, setHovered] = useState<string | null>(null);
  const currentIdx = STAGES.findIndex((s) => s.key === current);
  const utilityStartIdx = STAGES.findIndex((s) => s.group === "utility");

  return (
    <div
      className="min-h-screen w-full bg-[#F9FAFB] flex items-end justify-center p-6"
      style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}
    >
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>Variante A1 · Refinado · accents nas etapas, divisor de grupos, CTA cyan</span>
        <span>
          Etapa atual: <strong className="text-[#6B7280]">{STAGES[currentIdx].label}</strong>
        </span>
      </div>

      <div className="relative w-[min(760px,calc(100%-1rem))]">
        <div className="rounded-full border border-[#E5E7EB] bg-white shadow-[0_10px_28px_-14px_rgba(17,24,39,0.18)] flex items-center pl-1.5 pr-1 py-1 gap-0.5">
          {STAGES.map((stage, idx) => {
            const isCurrent = stage.key === current;
            const isPast = idx < currentIdx && stage.group === "funnel";
            const isUtility = stage.group === "utility";
            const Icon = stage.Icon;
            const insertGroupSep = idx === utilityStartIdx;

            return (
              <div key={stage.key} className="relative flex items-center">
                {idx > 0 && !insertGroupSep && (
                  <span
                    aria-hidden
                    className="h-px w-1.5 mx-px"
                    style={{
                      backgroundColor: isPast || isCurrent ? STAGES[idx - 1].accent : "#E5E7EB",
                      opacity: isPast || isCurrent ? 0.5 : 1,
                    }}
                  />
                )}
                {insertGroupSep && (
                  <span aria-hidden className="h-4 w-px bg-[#E5E7EB] mx-1.5" />
                )}

                <button
                  type="button"
                  onClick={() => setCurrent(stage.key)}
                  onMouseEnter={() => setHovered(stage.key)}
                  onMouseLeave={() => setHovered(null)}
                  aria-current={isCurrent ? "step" : undefined}
                  aria-label={
                    stage.count != null && stage.count > 0
                      ? `${stage.label} — ${stage.count} pendência(s)`
                      : stage.label
                  }
                  title={stage.label}
                  style={
                    isCurrent
                      ? { backgroundColor: stage.accent, color: "#fff" }
                      : isPast
                      ? { color: stage.accent, backgroundColor: `${stage.accent}14` }
                      : undefined
                  }
                  className={`relative flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-semibold whitespace-nowrap transition-all
                    focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
                    ${
                      isCurrent
                        ? ""
                        : isPast
                        ? "hover:brightness-95"
                        : isUtility
                        ? "text-[#9CA3AF] hover:text-[#6B7280] hover:bg-[#F3F4F6]"
                        : "text-[#9CA3AF] hover:text-[#6B7280] hover:bg-[#F3F4F6]"
                    }`}
                >
                  <Icon className="w-3.5 h-3.5" strokeWidth={isCurrent ? 2.4 : 2} />
                  {isCurrent && <span>{stage.short}</span>}
                  {!isCurrent && stage.count != null && stage.count > 0 && (
                    <span
                      aria-hidden
                      className="absolute -top-0.5 -right-0.5 min-w-[12px] h-[12px] px-[3px] rounded-full text-[8.5px] font-bold flex items-center justify-center text-white"
                      style={{ backgroundColor: stage.accent }}
                    >
                      {stage.count}
                    </span>
                  )}
                </button>

                {hovered === stage.key && !isCurrent && (
                  <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 z-10 whitespace-nowrap pointer-events-none">
                    <div
                      className="rounded-lg bg-white text-[#111827] text-[11px] px-2.5 py-1.5 shadow-[0_8px_20px_-6px_rgba(17,24,39,0.18)] border border-[#E5E7EB]"
                    >
                      <div className="font-semibold flex items-center gap-1.5">
                        <span
                          aria-hidden
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ backgroundColor: stage.accent }}
                        />
                        {stage.label}
                      </div>
                      <div className="text-[10px] text-[#6B7280] mt-0.5">{stage.hint}</div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          <div className="ml-auto pl-1.5 flex items-center">
            <span aria-hidden className="h-4 w-px bg-[#E5E7EB] mr-1" />
            <button
              type="button"
              className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold text-white whitespace-nowrap transition-all
                hover:brightness-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
                shadow-[0_2px_8px_-2px_rgba(96,190,209,0.55)]"
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

        <div className="mt-1.5 px-3 flex items-center justify-end text-[10px] text-[#9CA3AF]">
          <span className="inline-flex items-center gap-1">
            próxima
            <ArrowRight className="w-3 h-3" />
            <span className="font-medium text-[#6B7280]">
              {STAGES[Math.min(currentIdx + 1, STAGES.length - 1)].label}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
}
