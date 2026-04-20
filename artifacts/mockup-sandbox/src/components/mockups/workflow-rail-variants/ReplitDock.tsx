import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, Pencil, ArrowRight, Users, CalendarPlus, Send, PartyPopper,
  ChevronUp, MoreHorizontal,
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

export function ReplitDock() {
  const [current, setCurrent] = useState("entrevista");
  const [hovered, setHovered] = useState<string | null>(null);
  const [open, setOpen] = useState(true);
  const stage = ALL.find(s => s.key === current)!;
  const actions = STAGE_ACTIONS[stage.key] ?? [];
  const idx = ALL.findIndex(s => s.key === current);

  const scale = (key: string) => {
    if (!hovered) return 1;
    if (hovered === key) return 1.18;
    const hi = ALL.findIndex(s => s.key === hovered);
    const ki = ALL.findIndex(s => s.key === key);
    const d = Math.abs(hi - ki);
    if (d === 1) return 1.08;
    if (d === 2) return 1.03;
    return 1;
  };

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex flex-col items-center justify-end p-6 gap-3"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[10px] text-[#6B7280] flex items-center justify-between">
        <span>V1 · ReplitDock — icon-only · dock flutuante · menu sobe</span>
        <span>Etapa: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      {/* Stack: popover acima do dock */}
      <div className="relative flex flex-col items-center gap-2">
        {/* Popover vertical (sobe) — estilo Replit "Show less" */}
        {open && (
          <div
            role="menu"
            className="w-[280px] rounded-2xl bg-[#0F172A]/95 backdrop-blur-sm border border-white/10 shadow-[0_20px_50px_-12px_rgba(15,23,42,0.6)] overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-200"
          >
            {/* Header */}
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="w-full flex items-center justify-between px-3 py-2 text-white/55 hover:text-white/90 hover:bg-white/5 transition-colors group"
            >
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider">
                <ChevronUp className="w-3 h-3 group-hover:-translate-y-0.5 transition-transform" strokeWidth={2.5} />
                Mostrar menos
              </span>
              <span
                className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-md"
                style={{ color: stage.accent, backgroundColor: `${stage.accent}1F` }}
              >
                {stage.label}
              </span>
            </button>
            <div className="h-px bg-white/8" />
            {/* Action rows */}
            <ul className="py-1">
              {actions.map((a) => (
                <li key={a.label}>
                  <button
                    type="button"
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-[11.5px] text-white/80 hover:text-white hover:bg-white/6 transition-colors"
                  >
                    <span
                      className="w-5 h-5 rounded-md flex items-center justify-center shrink-0"
                      style={a.primary
                        ? { backgroundColor: stage.accent, color: "#0F172A" }
                        : { backgroundColor: `${stage.accent}1A`, color: stage.accent }}
                    >
                      <a.Icon className="w-3 h-3" strokeWidth={2.25} />
                    </span>
                    <span className={a.primary ? "text-white font-semibold" : ""}>{a.label}</span>
                    {a.primary && <ArrowRight className="w-3 h-3 ml-auto text-white/30" />}
                  </button>
                </li>
              ))}
            </ul>
            <div className="h-px bg-white/8" />
            <div className="px-3 py-1.5 text-[9px] text-white/35 uppercase tracking-wider truncate">
              Vaga: <span className="text-white/65 font-semibold normal-case tracking-normal">Eng. Dados Sr</span>
            </div>
          </div>
        )}

        {/* Dock flutuante — icon-only, mais estreito */}
        <div className="relative rounded-full bg-[#0F172A]/95 backdrop-blur-sm border border-white/10 shadow-[0_12px_32px_-8px_rgba(15,23,42,0.55)] flex items-center px-1.5 py-1 gap-0.5">
          {ALL.map((s, i) => {
            const isCurrent = s.key === current;
            const isPast = i < idx && i < FLOW.length;
            const isUtility = i >= FLOW.length;
            const sc = scale(s.key);
            return (
              <div key={s.key} className="flex items-center">
                {i === FLOW.length && <span className="w-px h-3 bg-white/15 mx-1" aria-hidden />}
                {i > 0 && i < FLOW.length && (
                  <span
                    aria-hidden
                    className="h-[1.5px] w-1.5 rounded-full mx-0.5"
                    style={{ background: isPast || isCurrent ? `${s.accent}99` : "rgba(255,255,255,0.08)" }}
                  />
                )}
                <button
                  type="button"
                  title={s.label}
                  aria-label={s.label}
                  onClick={() => { setCurrent(s.key); setOpen(true); }}
                  onMouseEnter={() => setHovered(s.key)}
                  onMouseLeave={() => setHovered(null)}
                  style={{
                    transform: `scale(${sc})`,
                    transformOrigin: "center bottom",
                    ...(isCurrent
                      ? { backgroundColor: s.accent, color: "#0F172A", boxShadow: `0 0 0 2px ${s.accent}33, 0 4px 10px -2px ${s.accent}80` }
                      : isPast
                      ? { color: s.accent }
                      : {}),
                  }}
                  className={`relative w-7 h-7 rounded-full flex items-center justify-center transition-[transform,background-color,color] duration-300 ease-out
                    ${!isCurrent && !isPast ? "text-white/55 hover:text-white hover:bg-white/8" : ""}
                    ${isUtility && !isCurrent ? "text-white/40" : ""}`}
                >
                  <s.Icon className="w-3 h-3" strokeWidth={isCurrent ? 2.5 : 2} />
                  {s.count != null && s.count > 0 && (
                    <span
                      aria-hidden
                      className="absolute -top-0.5 -right-0.5 min-w-[11px] h-[11px] px-0.5 rounded-full text-[8px] font-bold flex items-center justify-center"
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
          <span className="w-px h-3 bg-white/15 mx-1" aria-hidden />
          <button
            type="button"
            onClick={() => setOpen(v => !v)}
            aria-label={open ? "Fechar menu" : "Abrir menu"}
            className={`w-7 h-7 rounded-full flex items-center justify-center text-white/55 hover:text-white hover:bg-white/8 transition-all ${open ? "rotate-90" : ""}`}
          >
            <MoreHorizontal className="w-3 h-3" strokeWidth={2.5} />
          </button>
        </div>
      </div>

      <div className="text-[9px] text-[#9CA3AF] mt-1">Hover nos ícones · clique pra trocar etapa · "..." abre/fecha menu</div>
    </div>
  );
}
