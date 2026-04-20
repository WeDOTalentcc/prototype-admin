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
  accentBg: string;
  hint: string;
};

const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", short: "Vaga", Icon: Briefcase, accent: "#60BED1", accentBg: "rgba(96,190,209,0.10)", hint: "1 rascunho aberto" },
  { key: "sourcing", label: "Sourcing", short: "Sourcing", Icon: Search, accent: "#5DA47A", accentBg: "rgba(93,164,122,0.10)", hint: "12 candidatos novos" },
  { key: "triagem", label: "Triagem", short: "Triagem", Icon: UserCheck, accent: "#5DA47A", accentBg: "rgba(93,164,122,0.10)", hint: "3 aguardando review" },
  { key: "entrevista", label: "Entrevista", short: "Entrev.", Icon: Calendar, accent: "#D19960", accentBg: "rgba(209,153,96,0.10)", hint: "2 agendadas hoje" },
  { key: "oferta", label: "Oferta", short: "Oferta", Icon: FileText, accent: "#9860D1", accentBg: "rgba(152,96,209,0.10)", hint: "1 carta pendente" },
  { key: "contratacao", label: "Contratação", short: "Contrat.", Icon: TrendingUp, accent: "#9860D1", accentBg: "rgba(152,96,209,0.10)", hint: "—" },
  { key: "analytics", label: "Analytics", short: "BI", Icon: BarChart3, accent: "#D1A960", accentBg: "rgba(209,169,96,0.10)", hint: "Relatório semanal" },
  { key: "ia-automacoes", label: "IA & Automações", short: "IA", Icon: Sparkles, accent: "#60BED1", accentBg: "rgba(96,190,209,0.10)", hint: "2 agentes ativos" },
];

export function UltraCompacto() {
  const [current, setCurrent] = useState("triagem");
  const [hovered, setHovered] = useState<string | null>(null);
  const currentIdx = STAGES.findIndex((s) => s.key === current);

  return (
    <div className="min-h-screen w-full bg-[#F9FAFB] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>Variante A · UltraCompacto · rail single-row</span>
        <span>Etapa atual: <strong className="text-[#6B7280]">{STAGES[currentIdx].label}</strong></span>
      </div>

      <div className="relative w-[min(760px,calc(100%-1rem))]">
        <div className="rounded-full border border-[#E5E7EB] bg-white shadow-[0_8px_24px_-12px_rgba(17,24,39,0.18)] flex items-center pl-2 pr-1 py-1 gap-0.5">
          {STAGES.map((stage, idx) => {
            const isCurrent = stage.key === current;
            const isPast = idx < currentIdx;
            const Icon = stage.Icon;
            return (
              <div key={stage.key} className="relative flex items-center">
                {idx > 0 && (
                  <span aria-hidden className={`h-px w-2 ${isPast || isCurrent ? "bg-[#111827]" : "bg-[#E5E7EB]"}`} />
                )}
                <button
                  type="button"
                  onClick={() => setCurrent(stage.key)}
                  onMouseEnter={() => setHovered(stage.key)}
                  onMouseLeave={() => setHovered(null)}
                  aria-current={isCurrent ? "step" : undefined}
                  aria-label={stage.label}
                  title={stage.label}
                  style={isCurrent ? { backgroundColor: stage.accent, color: "#fff" } : undefined}
                  className={`flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-semibold whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
                    ${isCurrent ? "" : isPast ? "text-[#6B7280] hover:bg-[#F3F4F6]" : "text-[#9CA3AF] hover:text-[#6B7280] hover:bg-[#F3F4F6]"}`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {isCurrent && <span>{stage.short}</span>}
                </button>

                {hovered === stage.key && (
                  <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 z-10 whitespace-nowrap">
                    <div className="rounded-lg bg-[#111827] text-white text-[11px] px-2.5 py-1.5 shadow-lg">
                      <div className="font-semibold">{stage.label}</div>
                      <div className="text-[10px] text-white/70">{stage.hint}</div>
                    </div>
                    <div className="w-2 h-2 bg-[#111827] rotate-45 absolute left-1/2 -translate-x-1/2 -bottom-1" />
                  </div>
                )}
              </div>
            );
          })}

          <div className="ml-auto pl-2 flex items-center gap-1">
            <span aria-hidden className="h-4 w-px bg-[#E5E7EB] mx-1" />
            <button
              type="button"
              className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold text-white bg-[#111827] hover:bg-[#1F2937] transition-colors whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50"
              aria-label="Criar vaga"
              title="Criar vaga"
            >
              <span className="relative inline-flex items-center">
                <Briefcase className="w-3.5 h-3.5" />
                <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#111827] rounded-full" />
              </span>
              Criar vaga
            </button>
          </div>
        </div>

        <div className="mt-2 px-3 flex items-center justify-between text-[10px] text-[#9CA3AF]">
          <span>Hover em qualquer etapa revela o estado atual.</span>
          <span className="inline-flex items-center gap-1">
            Próxima: <ArrowRight className="w-3 h-3" /> {STAGES[Math.min(currentIdx + 1, STAGES.length - 1)].label}
          </span>
        </div>
      </div>
    </div>
  );
}
