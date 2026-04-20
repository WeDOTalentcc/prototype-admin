import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, ChevronRight, MoreHorizontal, type LucideIcon,
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

export function BreadcrumbContextual() {
  const [currentIdx, setCurrentIdx] = useState(2);
  const [showOverflow, setShowOverflow] = useState(false);
  const prev = currentIdx > 0 ? STAGES[currentIdx - 1] : null;
  const cur = STAGES[currentIdx];
  const next = currentIdx < STAGES.length - 1 ? STAGES[currentIdx + 1] : null;
  const hidden = STAGES.filter((_, i) => i !== currentIdx && i !== currentIdx - 1 && i !== currentIdx + 1);

  return (
    <div className="min-h-screen w-full bg-[#F9FAFB] flex flex-col"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="px-6 pt-4 pb-2 text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>Hipótese B2 · Breadcrumb Contextual · navegação superior, 3 etapas visíveis</span>
        <span>Etapa: <strong className="text-[#6B7280]">{cur.label}</strong></span>
      </div>

      {/* Top breadcrumb bar — replaces footer entirely */}
      <header className="bg-white border-b border-[#E5E7EB] px-6 py-2.5 flex items-center justify-between">
        <nav aria-label="Funil" className="flex items-center gap-1 text-[12px]">
          {prev && (
            <>
              <button
                onClick={() => setCurrentIdx(currentIdx - 1)}
                className="flex items-center gap-1 px-2 py-1 rounded text-[#9CA3AF] hover:text-[#111827] hover:bg-[#F3F4F6] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 transition-colors"
              >
                <prev.Icon className="w-3.5 h-3.5" />
                <span>{prev.label}</span>
              </button>
              <ChevronRight className="w-3 h-3 text-[#D1D5DB]" />
            </>
          )}

          <button
            aria-current="step"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded font-bold"
            style={{ color: cur.accent, backgroundColor: `${cur.accent}14` }}
          >
            <cur.Icon className="w-3.5 h-3.5" strokeWidth={2.5} />
            <span>{cur.label}</span>
            {cur.count != null && cur.count > 0 && (
              <span className="text-[10px] text-white rounded-full px-1.5 py-px font-bold" style={{ backgroundColor: cur.accent }}>{cur.count}</span>
            )}
          </button>

          {next && (
            <>
              <ChevronRight className="w-3 h-3 text-[#D1D5DB]" />
              <button
                onClick={() => setCurrentIdx(currentIdx + 1)}
                className="flex items-center gap-1 px-2 py-1 rounded text-[#9CA3AF] hover:text-[#111827] hover:bg-[#F3F4F6] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 transition-colors"
              >
                <next.Icon className="w-3.5 h-3.5" />
                <span>{next.label}</span>
              </button>
            </>
          )}

          <ChevronRight className="w-3 h-3 text-[#D1D5DB]" />
          <div className="relative">
            <button
              onClick={() => setShowOverflow((v) => !v)}
              aria-label="Mais etapas"
              aria-expanded={showOverflow}
              className="px-1.5 py-1 rounded text-[#9CA3AF] hover:text-[#111827] hover:bg-[#F3F4F6] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>
            {showOverflow && (
              <div role="menu" className="absolute top-full left-0 mt-1 z-10 w-56 rounded-lg bg-white border border-[#E5E7EB] shadow-[0_12px_28px_-8px_rgba(17,24,39,0.22)] py-1">
                {hidden.map((s) => {
                  const realIdx = STAGES.findIndex((x) => x.key === s.key);
                  return (
                    <button
                      key={s.key}
                      onClick={() => { setCurrentIdx(realIdx); setShowOverflow(false); }}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-[12px] text-[#111827] hover:bg-[#F3F4F6] text-left"
                    >
                      <s.Icon className="w-3.5 h-3.5" style={{ color: s.accent }} />
                      <span className="flex-1">{s.label}</span>
                      {s.count != null && s.count > 0 && <span className="text-[10px] text-[#9CA3AF]">{s.count}</span>}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </nav>

        <button
          type="button"
          aria-label="Criar vaga"
          className="flex items-center gap-1.5 px-3 py-1 rounded-md text-[11px] font-bold text-white bg-[#111827] hover:bg-[#1F2937] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 transition-colors whitespace-nowrap"
        >
          <span className="relative inline-flex items-center">
            <Briefcase className="w-3.5 h-3.5" />
            <Plus className="w-2 h-2 absolute -top-0.5 -right-0.5 bg-white text-[#111827] rounded-full" />
          </span>
          Criar vaga
        </button>
      </header>

      {/* Faux content to show context */}
      <main className="flex-1 px-6 py-4">
        <div className="text-[14px] font-semibold text-[#111827] mb-1">Engenheiro(a) de Dados Sr — Itaú</div>
        <div className="text-[12px] text-[#6B7280]">
          3 candidatos aguardando seu review. O breadcrumb superior substitui o rail de rodapé — o
          funil vira navegação contextual da vaga atual.
        </div>
      </main>
    </div>
  );
}
