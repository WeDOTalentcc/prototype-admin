import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, Pencil, ArrowRight, Users, CalendarPlus, Send, PartyPopper,
  type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number };
const FLOW: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#60BED1", count: 1 },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#5DA47A", count: 12 },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#5DA47A", count: 3 },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#D19960", count: 2 },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#9860D1", count: 1 },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#9860D1" },
];
const UTILITIES: Stage[] = [
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#60BED1" },
];
const ALL = [...FLOW, ...UTILITIES];

type Action = { label: string; Icon: LucideIcon; primary?: boolean };
const STAGE_ACTIONS: Record<string, Action[]> = {
  "definir-vaga": [{ label: "Nova vaga", Icon: Plus, primary: true }, { label: "Editar", Icon: Pencil }, { label: "Publicar", Icon: ArrowRight }],
  "sourcing":     [{ label: "Ver candidatos", Icon: Users, primary: true }, { label: "Buscar", Icon: Search }],
  "triagem":      [{ label: "Ver candidatos", Icon: Users, primary: true }, { label: "Avançar", Icon: ArrowRight }],
  "entrevista":   [{ label: "Ver candidatos", Icon: Users, primary: true }, { label: "Agendar", Icon: CalendarPlus }, { label: "Próx: Oferta", Icon: ArrowRight }],
  "oferta":       [{ label: "Enviar proposta", Icon: Send, primary: true }, { label: "Próx: Contratação", Icon: ArrowRight }],
  "contratacao":  [{ label: "Concluir", Icon: PartyPopper, primary: true }],
  "analytics":    [{ label: "Abrir painel", Icon: BarChart3, primary: true }],
  "ia-automacoes":[{ label: "Configurar", Icon: Sparkles, primary: true }],
};

export function FloatingChips() {
  const [current, setCurrent] = useState("entrevista");
  const [hovered, setHovered] = useState<string | null>(null);
  const stage = ALL.find(s => s.key === current)!;
  const actions = STAGE_ACTIONS[stage.key] ?? [];
  const idx = ALL.findIndex(s => s.key === current);

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex flex-col items-center justify-end p-6 gap-3"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[10px] text-[#6B7280] flex items-center justify-between">
        <span>V2 · FloatingChips — chips separados · popover sobe do chip ativo</span>
        <span>Etapa: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      <div className="relative flex flex-col items-center gap-3">
        {/* Popover sobe do chip ativo — vertical, compacto */}
        <div
          role="menu"
          aria-label={`Ações de ${stage.label}`}
          className="w-[240px] rounded-xl bg-[#0F172A] border border-white/10 shadow-[0_18px_45px_-12px_rgba(15,23,42,0.55)] overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-200"
        >
          <div
            className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5"
            style={{ color: stage.accent, backgroundColor: `${stage.accent}14` }}
          >
            <stage.Icon className="w-3 h-3" strokeWidth={2.5} />
            {stage.label}
          </div>
          <ul className="py-1">
            {actions.map((a) => (
              <li key={a.label}>
                <button
                  type="button"
                  className={`w-full flex items-center gap-2 px-3 py-1.5 text-[11px] transition-colors
                    ${a.primary ? "text-white font-semibold hover:bg-white/8" : "text-white/75 hover:text-white hover:bg-white/6"}`}
                >
                  <a.Icon className="w-3 h-3 shrink-0" style={{ color: stage.accent }} strokeWidth={2.25} />
                  {a.label}
                  {a.primary && <ArrowRight className="w-3 h-3 ml-auto" style={{ color: stage.accent }} />}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Caret pointing down to active chip */}
        <span
          aria-hidden
          className="-mt-2.5 w-2 h-2 rotate-45 bg-[#0F172A] border-r border-b border-white/10"
          style={{
            marginLeft: `${(idx - (ALL.length - 1) / 2) * 36}px`,
          }}
        />

        {/* Chips flutuantes — separados, cada um com sombra própria */}
        <div className="flex items-center gap-1.5">
          {ALL.map((s, i) => {
            const isCurrent = s.key === current;
            const isPast = i < idx && i < FLOW.length;
            const isUtility = i >= FLOW.length;
            const isHovered = hovered === s.key;
            return (
              <div key={s.key} className="flex items-center gap-1.5">
                {i === FLOW.length && <span className="w-2" aria-hidden />}
                <button
                  type="button"
                  title={s.label}
                  aria-label={s.label}
                  onClick={() => setCurrent(s.key)}
                  onMouseEnter={() => setHovered(s.key)}
                  onMouseLeave={() => setHovered(null)}
                  style={{
                    ...(isCurrent
                      ? {
                          backgroundColor: s.accent,
                          color: "#0F172A",
                          boxShadow: `0 6px 16px -4px ${s.accent}80, 0 0 0 2px ${s.accent}33`,
                          transform: "translateY(-2px) scale(1.1)",
                        }
                      : {
                          backgroundColor: "#0F172A",
                          color: isPast ? s.accent : isUtility ? "rgba(255,255,255,0.45)" : "rgba(255,255,255,0.65)",
                          transform: isHovered ? "translateY(-1px) scale(1.06)" : "scale(1)",
                          boxShadow: isHovered
                            ? `0 8px 18px -6px rgba(15,23,42,0.6), 0 0 0 1px ${s.accent}55`
                            : "0 4px 10px -4px rgba(15,23,42,0.5), 0 0 0 1px rgba(255,255,255,0.08)",
                        }),
                  }}
                  className="relative w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ease-out"
                >
                  <s.Icon className="w-3.5 h-3.5" strokeWidth={isCurrent ? 2.5 : 2} />
                  {s.count != null && s.count > 0 && (
                    <span
                      aria-hidden
                      className="absolute -top-1 -right-1 min-w-[12px] h-[12px] px-0.5 rounded-full text-[8px] font-bold flex items-center justify-center"
                      style={isCurrent
                        ? { backgroundColor: "#fff", color: s.accent }
                        : { backgroundColor: s.accent, color: "#0F172A" }}
                    >
                      {s.count}
                    </span>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* Vaga label flutuante abaixo */}
        <div className="text-[10px] text-[#6B7280] mt-1">
          Vaga: <span className="text-[#111827] font-semibold">Eng. Dados Sr</span>
        </div>
      </div>

      <div className="text-[9px] text-[#9CA3AF] mt-2">Cada ícone é um chip flutuante · popover acompanha o ativo</div>
    </div>
  );
}
