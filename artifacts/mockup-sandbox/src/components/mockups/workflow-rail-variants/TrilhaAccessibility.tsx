import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, Check, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number };
const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#0E7490", count: 1 },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#15803D", count: 12 },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#15803D", count: 3 },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#B45309", count: 2 },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#6D28D9", count: 1 },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#6D28D9" },
];
const UTILITIES = [
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#A16207" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#0E7490" },
];

export function TrilhaAccessibility() {
  const [current, setCurrent] = useState("sourcing");
  const idx = STAGES.findIndex((s) => s.key === current);
  const stage = STAGES[idx];
  const progressPct = ((idx + 0.5) / STAGES.length) * 100;

  return (
    <div className="min-h-screen w-full bg-[#F9FAFB] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[12px] text-[#374151] flex items-center justify-between">
        <span>CU3 · Acessibilidade · WCAG AAA, alvos ≥44px, status em 3 canais (cor+ícone+texto)</span>
        <span className="text-[#4B5563]">trade-off: mais alto verticalmente, menos compacto</span>
      </div>

      <div className="w-[min(840px,calc(100%-1rem))] rounded-2xl bg-white border-2 border-[#E5E7EB] shadow-[0_10px_28px_-14px_rgba(17,24,39,0.22)] overflow-hidden">
        <div role="status" aria-live="polite" className="sr-only">
          Etapa atual: {stage.label}, etapa {idx + 1} de {STAGES.length}
        </div>

        <div className="px-5 pt-4 pb-1 flex items-center justify-between">
          <div className="text-[14px] font-bold text-[#111827] inline-flex items-center gap-2">
            <stage.Icon className="w-5 h-5" style={{ color: stage.accent }} aria-hidden />
            {stage.label}
            <span className="text-[12px] font-normal text-[#4B5563]">— etapa {idx + 1} de {STAGES.length}</span>
          </div>
          {stage.count != null && stage.count > 0 && (
            <span className="text-[12px] font-bold inline-flex items-center gap-1.5" style={{ color: stage.accent }}>
              <span aria-hidden className="w-2 h-2 rounded-full" style={{ backgroundColor: stage.accent }} />
              {stage.count} pendência(s)
            </span>
          )}
        </div>

        <div className="px-5 pt-3 pb-5">
          <div className="relative h-16">
            <div aria-hidden className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-[6px] rounded-full bg-[#E5E7EB]" />
            <div
              aria-hidden
              className="absolute left-0 top-1/2 -translate-y-1/2 h-[6px] rounded-full transition-all"
              style={{ width: `${progressPct}%`, backgroundColor: stage.accent }}
            />

            <ol className="relative h-full flex items-center justify-between m-0 p-0 list-none" aria-label="Etapas do funil">
              {STAGES.map((s, i) => {
                const isCurrent = s.key === current;
                const isPast = i < idx;
                const status = isPast ? "concluída" : isCurrent ? "atual" : "futura";
                return (
                  <li key={s.key} className="relative flex flex-col items-center">
                    <button
                      type="button"
                      onClick={() => setCurrent(s.key)}
                      aria-current={isCurrent ? "step" : undefined}
                      aria-label={`${s.label}, etapa ${i + 1} de ${STAGES.length}, ${status}${s.count ? `, ${s.count} pendências` : ""}`}
                      style={
                        isCurrent
                          ? { backgroundColor: s.accent, borderColor: s.accent, color: "#fff" }
                          : isPast
                          ? { backgroundColor: s.accent, borderColor: s.accent, color: "#fff" }
                          : { color: s.accent, borderColor: s.accent }
                      }
                      className={`relative z-10 w-11 h-11 min-w-[44px] min-h-[44px] rounded-full border-2 bg-white flex items-center justify-center
                        focus:outline-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-[#FCD34D] focus-visible:outline-offset-2
                        motion-reduce:transition-none
                        ${isCurrent ? "ring-4 ring-offset-2 ring-current/20" : ""}`}
                    >
                      {isPast ? (
                        <Check className="w-5 h-5" strokeWidth={3} aria-hidden />
                      ) : (
                        <s.Icon className="w-5 h-5" strokeWidth={isCurrent ? 2.6 : 2.4} aria-hidden />
                      )}
                      {s.count != null && s.count > 0 && (
                        <span
                          className="absolute -top-1.5 -right-1.5 min-w-[22px] h-[22px] px-1.5 rounded-full text-[12px] font-bold flex items-center justify-center bg-white border-2"
                          style={{ borderColor: s.accent, color: s.accent }}
                          aria-hidden
                        >
                          {s.count}
                        </span>
                      )}
                    </button>
                    <span className="absolute top-full mt-2 flex flex-col items-center gap-0.5 whitespace-nowrap">
                      <span className={`text-[12px] font-bold ${isCurrent ? "" : "text-[#374151]"}`} style={isCurrent ? { color: s.accent } : undefined}>
                        {s.label}
                      </span>
                      <span className="text-[10px] uppercase tracking-wider text-[#6B7280] font-semibold">{status}</span>
                    </span>
                  </li>
                );
              })}
            </ol>
          </div>
        </div>

        <div aria-hidden className="h-px bg-[#E5E7EB]" />
        <div className="flex items-center gap-3 px-5 py-3">
          <div className="flex items-center gap-2">
            {UTILITIES.map((u) => (
              <button
                key={u.key}
                type="button"
                title={u.label}
                aria-label={u.label}
                className="inline-flex items-center gap-1.5 px-3 min-h-[36px] rounded-lg border-2 border-[#E5E7EB] text-[12px] font-semibold text-[#374151] hover:bg-[#F3F4F6] hover:border-[#9CA3AF] focus:outline-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-[#FCD34D] focus-visible:outline-offset-2 motion-reduce:transition-none transition-colors"
              >
                <u.Icon className="w-4 h-4" style={{ color: u.accent }} aria-hidden />
                {u.label}
              </button>
            ))}
          </div>

          <span className="text-[12px] text-[#374151] truncate flex-1" title="Engenheiro(a) de Dados Sr — Itaú">
            <span className="text-[#6B7280]">Vaga ativa:</span>{" "}
            <span className="font-bold text-[#111827]">Eng. Dados Sr — Itaú</span>
          </span>

          <button
            type="button"
            aria-label="Criar nova vaga"
            title="Criar nova vaga"
            className="flex items-center gap-2 px-4 min-h-[44px] rounded-xl text-[14px] font-bold text-white whitespace-nowrap focus:outline-none focus-visible:outline focus-visible:outline-4 focus-visible:outline-[#FCD34D] focus-visible:outline-offset-2 motion-reduce:transition-none transition-colors"
            style={{ backgroundColor: "#0E7490" }}
          >
            <span className="relative inline-flex items-center">
              <Briefcase className="w-5 h-5" strokeWidth={2.6} aria-hidden />
              <Plus className="w-2.5 h-2.5 absolute -top-0.5 -right-0.5 bg-white text-[#0E7490] rounded-full" aria-hidden />
            </span>
            Criar vaga
          </button>
        </div>
      </div>
    </div>
  );
}
