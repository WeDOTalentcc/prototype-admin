import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, ArrowRight, Check, type LucideIcon,
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

export function TrilhaGranular() {
  const [current, setCurrent] = useState("sourcing");
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];
  const next = STAGES[Math.min(idx + 1, STAGES.length - 1)];
  const progressPct = ((idx + 0.5) / STAGES.length) * 100;

  return (
    <div className="min-h-screen w-full bg-[#FAFAF9] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>TP2 · Granular · trilha segmentada por etapa, % inline, contagens como mini-pills</span>
        <span>Etapa atual: <strong className="text-[#6B7280]">{stage.label}</strong></span>
      </div>

      <div className="w-[min(820px,calc(100%-1rem))] rounded-2xl bg-white border border-[#E5E7EB] shadow-[0_10px_28px_-14px_rgba(17,24,39,0.18)] overflow-hidden">
        <div className="px-5 pt-3.5 pb-1 flex items-center justify-between gap-3">
          <div className="text-[11px] font-semibold text-[#111827] inline-flex items-center gap-1.5 min-w-0">
            <stage.Icon className="w-3.5 h-3.5 shrink-0" style={{ color: stage.accent }} />
            <span className="truncate">{stage.label}</span>
            <span className="text-[10px] font-normal text-[#9CA3AF] shrink-0">· etapa {idx + 1} de {STAGES.length}</span>
            <span
              className="text-[10px] font-bold px-1.5 py-px rounded-full shrink-0"
              style={{ backgroundColor: `${stage.accent}1A`, color: stage.accent }}
            >
              {Math.round(progressPct)}% completo
            </span>
          </div>
          <div className="text-[10px] text-[#9CA3AF] inline-flex items-center gap-1 shrink-0">
            próxima
            <ArrowRight className="w-3 h-3" />
            <span className="text-[#6B7280] font-medium">{next.label}</span>
          </div>
        </div>

        <div className="px-5 pt-3 pb-8">
          {/* Segmented trail */}
          <div className="relative h-9">
            {/* segments — one between each pair of nodes */}
            <div aria-hidden className="absolute left-[14px] right-[14px] top-1/2 -translate-y-1/2 h-[5px] flex">
              {STAGES.map((s, i) => {
                if (i === STAGES.length - 1) return null;
                const segIsPast = i < idx;
                const segIsCurrent = i === idx;
                return (
                  <div
                    key={`seg-${i}`}
                    className="flex-1 h-full"
                    style={{
                      background: segIsPast
                        ? STAGES[i + 1].accent
                        : segIsCurrent
                        ? `linear-gradient(90deg, ${s.accent} 0%, ${s.accent} 50%, #F3F4F6 50%, #F3F4F6 100%)`
                        : "#F3F4F6",
                      borderRadius: i === 0 ? "9999px 0 0 9999px" : i === STAGES.length - 2 ? "0 9999px 9999px 0" : 0,
                    }}
                  />
                );
              })}
            </div>

            <div className="relative h-full flex items-center justify-between">
              {STAGES.map((s, i) => {
                const isCurrent = s.key === current;
                const isPast = i < idx;
                return (
                  <div key={s.key} className="relative flex flex-col items-center">
                    {/* tick mark */}
                    <span
                      aria-hidden
                      className="absolute -top-2 w-[2px] rounded-full"
                      style={{
                        height: isCurrent ? 6 : 4,
                        backgroundColor: isPast || isCurrent ? s.accent : "#D1D5DB",
                        opacity: isPast || isCurrent ? 1 : 0.6,
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setCurrent(s.key)}
                      aria-current={isCurrent ? "step" : undefined}
                      aria-label={s.count ? `${s.label} — ${s.count} pendência(s)` : s.label}
                      title={s.label}
                      style={
                        isCurrent
                          ? { backgroundColor: s.accent, borderColor: s.accent, color: "#fff", boxShadow: `0 0 0 4px ${s.accent}33, 0 6px 14px -4px ${s.accent}80` }
                          : isPast
                          ? { backgroundColor: s.accent, borderColor: s.accent, color: "#fff" }
                          : undefined
                      }
                      className={`relative z-10 w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all
                        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
                        ${isCurrent ? "scale-110" : ""}
                        ${!isCurrent && !isPast ? "bg-white border-[#E5E7EB] text-[#9CA3AF] hover:border-[#9CA3AF] hover:text-[#6B7280]" : ""}`}
                    >
                      {isPast ? <Check className="w-3.5 h-3.5" strokeWidth={3} /> : <s.Icon className="w-3.5 h-3.5" strokeWidth={2.25} />}
                    </button>

                    {/* label + inline mini-pill count */}
                    <div className="absolute top-full mt-1.5 flex flex-col items-center gap-0.5 whitespace-nowrap">
                      <span
                        className={`text-[10px] leading-tight font-semibold ${isPast && !isCurrent ? "text-[#6B7280]" : !isCurrent ? "text-[#9CA3AF]" : ""}`}
                        style={isCurrent ? { color: s.accent } : undefined}
                      >
                        {s.label}
                      </span>
                      {s.count != null && s.count > 0 && (
                        <span
                          className="text-[9px] font-bold leading-none px-1.5 py-[2px] rounded-full"
                          style={{
                            backgroundColor: isCurrent ? `${s.accent}` : `${s.accent}14`,
                            color: isCurrent ? "#fff" : s.accent,
                          }}
                        >
                          {s.count} pend.
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div aria-hidden className="h-px bg-[#F3F4F6]" />
        <div className="flex items-center justify-between px-5 py-2 gap-3">
          <div className="flex items-center gap-3 min-w-0">
            {UTILITIES.map((u) => (
              <button
                key={u.key}
                type="button"
                title={u.label}
                className="inline-flex items-center gap-1 text-[10.5px] font-medium text-[#6B7280] hover:text-[#111827] transition-colors"
              >
                <u.Icon className="w-3.5 h-3.5" style={{ color: u.accent }} />
                {u.label}
              </button>
            ))}
            <span aria-hidden className="h-3 w-px bg-[#E5E7EB] shrink-0" />
            <span className="text-[10px] text-[#9CA3AF] truncate min-w-0" title="Engenheiro(a) de Dados Sr — Itaú">
              <span className="text-[#9CA3AF]">vaga:</span> <span className="text-[#6B7280] font-semibold">Eng. Dados Sr — Itaú</span>
            </span>
          </div>

          <button
            type="button"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[11px] font-bold text-white whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 shadow-[0_4px_12px_-2px_rgba(96,190,209,0.55)]"
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
  );
}
