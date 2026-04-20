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
};

const FUNNEL: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", short: "Vaga", Icon: Briefcase, accent: "#60BED1", hint: "1 rascunho aberto", count: 1 },
  { key: "sourcing", label: "Sourcing", short: "Sourcing", Icon: Search, accent: "#5DA47A", hint: "12 candidatos novos", count: 12 },
  { key: "triagem", label: "Triagem", short: "Triagem", Icon: UserCheck, accent: "#5DA47A", hint: "3 aguardando review", count: 3 },
  { key: "entrevista", label: "Entrevista", short: "Entrev.", Icon: Calendar, accent: "#D19960", hint: "2 agendadas hoje", count: 2 },
  { key: "oferta", label: "Oferta", short: "Oferta", Icon: FileText, accent: "#9860D1", hint: "1 carta pendente", count: 1 },
  { key: "contratacao", label: "Contratação", short: "Contrat.", Icon: TrendingUp, accent: "#9860D1", hint: "—" },
];

const UTILITIES: Stage[] = [
  { key: "analytics", label: "Analytics", short: "BI", Icon: BarChart3, accent: "#D1A960", hint: "Relatório semanal" },
  { key: "ia-automacoes", label: "IA & Automações", short: "IA", Icon: Sparkles, accent: "#60BED1", hint: "2 agentes ativos" },
];

export function UltraCompactoSegmentado() {
  const [current, setCurrent] = useState("triagem");
  const [hovered, setHovered] = useState<string | null>(null);
  const idx = FUNNEL.findIndex((s) => s.key === current);
  const isUtilityCurrent = UTILITIES.some((u) => u.key === current);
  const stage = isUtilityCurrent
    ? UTILITIES.find((u) => u.key === current)!
    : FUNNEL[Math.max(idx, 0)];
  const progressPct = isUtilityCurrent ? 100 : ((idx + 1) / FUNNEL.length) * 100;

  return (
    <div
      className="min-h-screen w-full bg-[#F9FAFB] flex items-end justify-center p-6"
      style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}
    >
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>Variante A2 · Segmentado · funil ↔ utilities como pills separados, ghost-progress</span>
        <span>
          Etapa atual: <strong className="text-[#6B7280]">{stage.label}</strong>
        </span>
      </div>

      <div className="relative w-[min(780px,calc(100%-1rem))]">
        <div className="flex items-center gap-2 justify-between">
          {/* Funnel pill (solid) with ghost-progress fill */}
          <div className="relative flex-1 rounded-full border border-[#E5E7EB] bg-white shadow-[0_10px_28px_-14px_rgba(17,24,39,0.18)] overflow-hidden">
            <div
              aria-hidden
              className="absolute inset-y-0 left-0 transition-all"
              style={{
                width: `${progressPct}%`,
                background: `linear-gradient(90deg, ${stage.accent}10, ${stage.accent}1F)`,
              }}
            />
            <div className="relative flex items-center pl-1.5 pr-2 py-1">
              {FUNNEL.map((s, i) => {
                const isCurrent = s.key === current;
                const isPast = i < idx;
                const Icon = s.Icon;
                return (
                  <div key={s.key} className="relative flex items-center">
                    {i > 0 && (
                      <span
                        aria-hidden
                        className="h-px w-1.5 mx-px"
                        style={{
                          backgroundColor: isPast || isCurrent ? FUNNEL[i - 1].accent : "#E5E7EB",
                          opacity: isPast || isCurrent ? 0.45 : 1,
                        }}
                      />
                    )}
                    <button
                      type="button"
                      onClick={() => setCurrent(s.key)}
                      onMouseEnter={() => setHovered(s.key)}
                      onMouseLeave={() => setHovered(null)}
                      aria-current={isCurrent ? "step" : undefined}
                      aria-label={
                        s.count != null && s.count > 0
                          ? `${s.label} — ${s.count} pendência(s)`
                          : s.label
                      }
                      title={s.label}
                      style={
                        isCurrent
                          ? { backgroundColor: s.accent, color: "#fff" }
                          : isPast
                          ? { color: s.accent }
                          : undefined
                      }
                      className={`relative flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-semibold whitespace-nowrap transition-all
                        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
                        ${
                          isCurrent
                            ? ""
                            : isPast
                            ? "hover:bg-white/40"
                            : "text-[#9CA3AF] hover:text-[#6B7280] hover:bg-[#F3F4F6]"
                        }`}
                    >
                      <Icon className="w-3.5 h-3.5" strokeWidth={isCurrent ? 2.4 : 2} />
                      {isCurrent && <span>{s.short}</span>}
                      {!isCurrent && s.count != null && s.count > 0 && (
                        <span
                          aria-hidden
                          className="absolute -top-0.5 -right-0.5 min-w-[12px] h-[12px] px-[3px] rounded-full text-[8.5px] font-bold flex items-center justify-center text-white"
                          style={{ backgroundColor: s.accent }}
                        >
                          {s.count}
                        </span>
                      )}
                    </button>

                    {hovered === s.key && !isCurrent && (
                      <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 z-20 whitespace-nowrap pointer-events-none">
                        <div className="rounded-lg bg-white text-[#111827] text-[11px] px-2.5 py-1.5 shadow-[0_8px_20px_-6px_rgba(17,24,39,0.18)] border border-[#E5E7EB]">
                          <div className="font-semibold flex items-center gap-1.5">
                            <span
                              aria-hidden
                              className="w-1.5 h-1.5 rounded-full"
                              style={{ backgroundColor: s.accent }}
                            />
                            {s.label}
                          </div>
                          <div className="text-[10px] text-[#6B7280] mt-0.5">{s.hint}</div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Utilities pill (ghost) */}
          <div className="rounded-full border border-dashed border-[#E5E7EB] bg-[#F9FAFB]/60 flex items-center px-1.5 py-1 gap-0.5">
            {UTILITIES.map((s) => {
              const isCurrent = s.key === current;
              const Icon = s.Icon;
              return (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => setCurrent(s.key)}
                  onMouseEnter={() => setHovered(s.key)}
                  onMouseLeave={() => setHovered(null)}
                  aria-current={isCurrent ? "step" : undefined}
                  aria-label={s.label}
                  title={s.label}
                  style={isCurrent ? { backgroundColor: s.accent, color: "#fff" } : undefined}
                  className={`relative flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-semibold whitespace-nowrap transition-all
                    focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
                    ${isCurrent ? "" : "text-[#9CA3AF] hover:text-[#6B7280] hover:bg-white"}`}
                >
                  <Icon className="w-3.5 h-3.5" strokeWidth={isCurrent ? 2.4 : 2} />
                  {isCurrent && <span>{s.short}</span>}

                  {hovered === s.key && !isCurrent && (
                    <span className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 z-20 whitespace-nowrap pointer-events-none">
                      <span className="rounded-lg bg-white text-[#111827] text-[11px] px-2.5 py-1.5 shadow-[0_8px_20px_-6px_rgba(17,24,39,0.18)] border border-[#E5E7EB] flex items-center gap-1.5">
                        <span
                          aria-hidden
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ backgroundColor: s.accent }}
                        />
                        {s.label}
                      </span>
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* CTA — separated, accent */}
          <button
            type="button"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-[11px] font-bold text-white whitespace-nowrap transition-all
              hover:brightness-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
              shadow-[0_4px_14px_-4px_rgba(96,190,209,0.65)]"
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

        <div className="mt-1.5 px-3 flex items-center justify-between text-[10px] text-[#9CA3AF]">
          <span className="truncate max-w-[60%]">
            Vaga ativa: <span className="text-[#6B7280] font-medium">Engenheiro(a) de Dados Sr — Itaú</span>
          </span>
          <span>
            {Math.round(progressPct)}% do funil
          </span>
        </div>
      </div>
    </div>
  );
}
