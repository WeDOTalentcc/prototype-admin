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
  { key: "ia-automacoes", label: "IA", Icon: Sparkles, accent: "#60BED1" },
];

export function DockMagnified() {
  const [current, setCurrent] = useState("triagem");
  const [hovered, setHovered] = useState<string | null>(null);
  const currentIdx = STAGES.findIndex((s) => s.key === current);

  const sizeFor = (key: string, idx: number) => {
    if (key === current) return 56;
    if (hovered === key) return 52;
    if (hovered) {
      const hIdx = STAGES.findIndex((s) => s.key === hovered);
      const dist = Math.abs(idx - hIdx);
      if (dist === 1) return 44;
      if (dist === 2) return 38;
    }
    return 36;
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-[#F3F4F6] to-[#E5E7EB] flex items-end justify-center p-6 relative"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>Hipótese B3 · Dock Magnified · spatial, sem chrome, hover-magnify</span>
        <span>Etapa: <strong className="text-[#111827]">{STAGES[currentIdx].label}</strong></span>
      </div>

      {/* Floating dock — no surrounding pill */}
      <div className="flex items-end gap-2 mb-2">
        <div
          onMouseLeave={() => setHovered(null)}
          className="flex items-end gap-1.5 px-3 py-2 rounded-2xl bg-white/70 backdrop-blur-md border border-white/60 shadow-[0_18px_48px_-12px_rgba(17,24,39,0.28)]"
        >
          {STAGES.map((s, idx) => {
            const isCurrent = s.key === current;
            const size = sizeFor(s.key, idx);
            const showLabel = isCurrent || hovered === s.key;
            return (
              <div key={s.key} className="relative flex flex-col items-center" style={{ width: size }}>
                {showLabel && (
                  <div className="absolute -top-7 px-2 py-0.5 rounded-md bg-[#111827] text-white text-[10px] font-semibold whitespace-nowrap shadow-md pointer-events-none">
                    {s.label}
                    <div className="w-1.5 h-1.5 bg-[#111827] rotate-45 absolute left-1/2 -translate-x-1/2 -bottom-0.5" />
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => setCurrent(s.key)}
                  onMouseEnter={() => setHovered(s.key)}
                  aria-current={isCurrent ? "step" : undefined}
                  aria-label={s.count ? `${s.label} — ${s.count} pendência(s)` : s.label}
                  title={s.label}
                  style={{
                    width: size,
                    height: size,
                    backgroundColor: isCurrent ? s.accent : `${s.accent}22`,
                    color: isCurrent ? "#fff" : s.accent,
                    boxShadow: isCurrent ? `0 8px 20px -4px ${s.accent}80` : undefined,
                  }}
                  className="rounded-xl flex items-center justify-center transition-all duration-200 ease-out hover:brightness-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 relative"
                >
                  <s.Icon style={{ width: size * 0.45, height: size * 0.45 }} strokeWidth={isCurrent ? 2.4 : 2} />
                  {!isCurrent && s.count != null && s.count > 0 && (
                    <span className="absolute -top-1 -right-1 min-w-[14px] h-[14px] px-1 rounded-full bg-[#111827] text-white text-[9px] font-bold flex items-center justify-center">
                      {s.count}
                    </span>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* CTA dock — also magnifies */}
        <div
          onMouseLeave={() => setHovered(null)}
          className="px-2 py-2 rounded-2xl bg-white/70 backdrop-blur-md border border-white/60 shadow-[0_18px_48px_-12px_rgba(17,24,39,0.28)]"
        >
          <button
            type="button"
            onMouseEnter={() => setHovered("__cta")}
            style={{
              width: hovered === "__cta" ? 52 : 40,
              height: hovered === "__cta" ? 52 : 40,
              boxShadow: "0 8px 20px -4px rgba(96,190,209,0.6)",
            }}
            className="rounded-xl flex items-center justify-center bg-[#60BED1] text-white transition-all duration-200 ease-out hover:brightness-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 relative"
            aria-label="Criar vaga"
            title="Criar vaga"
          >
            {hovered === "__cta" && (
              <div className="absolute -top-7 px-2 py-0.5 rounded-md bg-[#111827] text-white text-[10px] font-semibold whitespace-nowrap shadow-md pointer-events-none">
                Criar vaga
              </div>
            )}
            <span className="relative inline-flex items-center">
              <Briefcase style={{ width: hovered === "__cta" ? 22 : 18, height: hovered === "__cta" ? 22 : 18 }} strokeWidth={2.4} />
              <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#60BED1] rounded-full" />
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
