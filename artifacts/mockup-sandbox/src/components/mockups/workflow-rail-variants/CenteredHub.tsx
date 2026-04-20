import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number };
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

export function CenteredHub() {
  const [current, setCurrent] = useState("entrevista");
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];
  const past = STAGES.slice(0, idx);
  const future = STAGES.slice(idx + 1);

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>L3 · Centered Hub · etapa atual hero, passado/futuro colapsados nas laterais</span>
        <span>Etapa atual: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      <div className="w-[min(820px,calc(100%-1rem))] flex items-center gap-2">
        <div
          className="flex-1 rounded-2xl border border-[#1F2937] shadow-[0_18px_40px_-16px_rgba(15,23,42,0.55)] overflow-hidden flex items-stretch"
          style={{ background: "linear-gradient(180deg, #111B2F 0%, #0B1322 100%)" }}
        >
          {/* PAST — collapsed dots */}
          <div className="flex items-center gap-0.5 px-2 py-2 border-r border-white/8 bg-black/15">
            {past.map((s, i) => (
              <button
                key={s.key}
                type="button"
                onClick={() => setCurrent(s.key)}
                aria-label={`Voltar para ${s.label}`}
                title={s.label}
                className="group relative w-7 h-7 rounded-full flex items-center justify-center transition-all hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
                style={{ backgroundColor: `${s.accent}22`, color: s.accent }}
              >
                <s.Icon className="w-3.5 h-3.5" strokeWidth={2} />
                {i < past.length - 1 && (
                  <span aria-hidden className="absolute -right-1 top-1/2 -translate-y-1/2 w-1 h-px" style={{ backgroundColor: s.accent, opacity: 0.5 }} />
                )}
              </button>
            ))}
          </div>

          {/* HERO — current stage as the main subject */}
          <div className="flex-1 flex items-center gap-3 px-4 py-3 min-w-0">
            <div
              className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
              style={{ backgroundColor: stage.accent, boxShadow: `0 0 0 4px ${stage.accent}33, 0 8px 20px -4px ${stage.accent}80` }}
            >
              <stage.Icon className="w-6 h-6 text-[#0B1322]" strokeWidth={2.6} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline gap-2">
                <span className="text-[9px] font-bold uppercase tracking-[0.14em]" style={{ color: stage.accent }}>
                  etapa {idx + 1}/{STAGES.length}
                </span>
                {stage.count != null && stage.count > 0 && (
                  <span className="text-[10px] text-[#FACC15] font-bold">{stage.count} pendência(s)</span>
                )}
              </div>
              <div className="text-[16px] font-bold text-white leading-tight tracking-tight truncate">{stage.label}</div>
              <div className="text-[10px] text-white/55 truncate" title="Engenheiro(a) de Dados Sr — Itaú">
                Eng. Dados Sr — Itaú
              </div>
            </div>
          </div>

          {/* FUTURE — collapsed dots */}
          <div className="flex items-center gap-0.5 px-2 py-2 border-l border-white/8 bg-black/15">
            {future.map((s, i) => {
              const hasCount = s.count != null && s.count > 0;
              return (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => setCurrent(s.key)}
                  aria-label={hasCount ? `Pular para ${s.label} — ${s.count} pendência(s)` : `Pular para ${s.label}`}
                  title={s.label}
                  className="group relative w-7 h-7 rounded-full flex items-center justify-center transition-all hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70 text-white/45 hover:text-white"
                  style={{ backgroundColor: "rgba(255,255,255,0.05)" }}
                >
                  <s.Icon className="w-3.5 h-3.5" strokeWidth={2} />
                  {hasCount && (
                    <span
                      aria-hidden
                      className="absolute -top-0.5 -right-0.5 min-w-[12px] h-[12px] px-0.5 rounded-full text-[8.5px] font-bold flex items-center justify-center"
                      style={{ backgroundColor: s.accent, color: "#0B1322" }}
                    >
                      {s.count}
                    </span>
                  )}
                  {i < future.length - 1 && (
                    <span aria-hidden className="absolute -right-1 top-1/2 -translate-y-1/2 w-1 h-px bg-white/15" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* CTA — floating, decoupled */}
        <button
          type="button"
          aria-label="Criar vaga"
          title="Criar vaga"
          className="shrink-0 flex flex-col items-center justify-center gap-0.5 px-3 py-2.5 rounded-2xl text-[10px] font-bold text-[#0B1322] bg-[#5DA47A] hover:bg-[#6FB58A] transition-colors whitespace-nowrap shadow-[0_0_0_3px_rgba(93,164,122,0.22),0_8px_20px_-4px_rgba(93,164,122,0.55)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
        >
          <span className="relative inline-flex items-center">
            <Briefcase className="w-5 h-5" strokeWidth={2.4} />
            <Plus className="w-2.5 h-2.5 absolute -top-0.5 -right-0.5 bg-white text-[#0B1322] rounded-full" />
          </span>
          <span className="leading-tight">Criar<br />vaga</span>
        </button>
      </div>
    </div>
  );
}
