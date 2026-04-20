import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, ArrowRight, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number; hint?: string; nextAction?: string };
const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#60BED1", count: 1, hint: "1 rascunho", nextAction: "Publicar vaga" },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#5DA47A", count: 12, hint: "12 novos candidatos", nextAction: "Revisar fila de sourcing" },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#5DA47A", count: 3, hint: "3 aguardando review", nextAction: "Aprovar candidatos para entrevista" },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#D19960", count: 2, hint: "2 agendadas hoje", nextAction: "Ver agenda do dia" },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#9860D1", count: 1, hint: "1 carta pendente", nextAction: "Enviar carta-oferta" },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#9860D1", hint: "—", nextAction: "Iniciar onboarding" },
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960", hint: "Relatório semanal", nextAction: "Abrir dashboard" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#60BED1", hint: "2 agentes ativos", nextAction: "Gerenciar agentes" },
];

export function SidebarVerticalDrawer() {
  const [current, setCurrent] = useState("triagem");
  const [hovered, setHovered] = useState<string | null>(null);
  const stage = STAGES.find((s) => s.key === current)!;
  const peeked = hovered ? STAGES.find((s) => s.key === hovered)! : stage;

  return (
    <div className="min-h-screen w-full bg-[#F9FAFB] flex relative"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-4 left-4 right-[60px] text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>Hipótese B4 · Sidebar Vertical · trilha lateral persistente, drawer on-hover</span>
        <span>Etapa: <strong className="text-[#6B7280]">{stage.label}</strong></span>
      </div>

      {/* Faux content area */}
      <main className="flex-1 px-6 py-12">
        <div className="text-[14px] font-semibold text-[#111827] mb-1">Engenheiro(a) de Dados Sr — Itaú</div>
        <div className="text-[12px] text-[#6B7280]">
          O rail vira uma coluna fina à direita. Hover em qualquer etapa abre um drawer com detalhes
          inline, sem competir com o fluxo horizontal do conteúdo.
        </div>
      </main>

      {/* Drawer (slides from right when hovering) */}
      {hovered && (
        <aside
          aria-label={`Detalhes — ${peeked.label}`}
          className="absolute top-0 bottom-0 right-12 w-[260px] bg-white border-l border-[#E5E7EB] shadow-[-12px_0_28px_-8px_rgba(17,24,39,0.16)] p-4 animate-in slide-in-from-right-2 duration-150"
          onMouseEnter={() => setHovered(peeked.key)}
          onMouseLeave={() => setHovered(null)}
        >
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${peeked.accent}1F` }}>
              <peeked.Icon className="w-4 h-4" style={{ color: peeked.accent }} strokeWidth={2.4} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[12px] font-bold text-[#111827] truncate">{peeked.label}</div>
              <div className="text-[10px] text-[#9CA3AF]">{peeked.hint}</div>
            </div>
            {peeked.count != null && peeked.count > 0 && (
              <span className="text-[11px] font-bold text-white rounded-full px-2 py-0.5" style={{ backgroundColor: peeked.accent }}>{peeked.count}</span>
            )}
          </div>

          <div className="text-[10px] font-semibold text-[#9CA3AF] uppercase tracking-wide mb-1.5">Próxima ação</div>
          <button
            onClick={() => setCurrent(peeked.key)}
            className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg border border-[#E5E7EB] hover:bg-[#F3F4F6] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 transition-colors text-left"
          >
            <span className="text-[12px] font-medium text-[#111827]">{peeked.nextAction}</span>
            <ArrowRight className="w-3.5 h-3.5 text-[#9CA3AF]" />
          </button>

          <div className="mt-3 pt-3 border-t border-[#F3F4F6]">
            <button className="text-[11px] font-medium text-[#6B7280] hover:text-[#111827] inline-flex items-center gap-1">
              Ver tudo em {peeked.label.toLowerCase()} <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </aside>
      )}

      {/* Vertical rail — anchored right edge */}
      <div
        className="w-12 bg-white border-l border-[#E5E7EB] shadow-[-2px_0_8px_-4px_rgba(17,24,39,0.08)] flex flex-col items-center py-2 relative z-10"
        onMouseLeave={() => setHovered(null)}
      >
        {/* CTA pinned at top */}
        <button
          type="button"
          aria-label="Criar vaga"
          title="Criar vaga"
          className="w-9 h-9 rounded-lg flex items-center justify-center bg-[#60BED1] text-white mb-3 hover:brightness-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 transition-all shadow-[0_4px_12px_-2px_rgba(96,190,209,0.55)] relative"
        >
          <Briefcase className="w-4 h-4" strokeWidth={2.4} />
          <Plus className="w-2.5 h-2.5 absolute -top-0.5 -right-0.5 bg-white text-[#60BED1] rounded-full p-px" />
        </button>

        <div aria-hidden className="w-6 h-px bg-[#E5E7EB] mb-2" />

        <nav aria-label="Funil" className="flex flex-col items-center gap-1.5 flex-1">
          {STAGES.map((s) => {
            const isCurrent = s.key === current;
            return (
              <button
                key={s.key}
                onClick={() => setCurrent(s.key)}
                onMouseEnter={() => setHovered(s.key)}
                aria-current={isCurrent ? "step" : undefined}
                aria-label={s.label}
                title={s.label}
                style={
                  isCurrent
                    ? { backgroundColor: s.accent, color: "#fff" }
                    : { color: s.accent }
                }
                className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all relative
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50
                  ${isCurrent ? "shadow-md" : "hover:bg-[#F3F4F6]"}`}
              >
                <s.Icon className="w-4 h-4" strokeWidth={isCurrent ? 2.4 : 2} />
                {!isCurrent && s.count != null && s.count > 0 && (
                  <span className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full" style={{ backgroundColor: s.accent }} />
                )}
                {isCurrent && (
                  <span aria-hidden className="absolute -left-2 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r" style={{ backgroundColor: s.accent }} />
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
