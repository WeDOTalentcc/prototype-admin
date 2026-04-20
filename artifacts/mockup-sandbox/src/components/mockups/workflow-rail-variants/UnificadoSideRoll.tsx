import "./_group.css";
import { useState, useRef, useEffect, useCallback } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, Check, ArrowRight, Users, CalendarPlus, Pencil, Send, PartyPopper,
  ChevronLeft, ChevronRight, Sun, Moon, MoreHorizontal,
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

export function UnificadoSideRoll() {
  const [current, setCurrent] = useState("entrevista");
  const [hovered, setHovered] = useState<string | null>(null);
  const [popoverOpen, setPopoverOpen] = useState(true);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [canScrollL, setCanScrollL] = useState(false);
  const [canScrollR, setCanScrollR] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);

  const updateScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollL(el.scrollLeft > 4);
    setCanScrollR(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
  }, []);

  useEffect(() => {
    updateScroll();
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", updateScroll, { passive: true });
    const ro = new ResizeObserver(updateScroll);
    ro.observe(el);
    return () => { el.removeEventListener("scroll", updateScroll); ro.disconnect(); };
  }, [updateScroll]);

  const scroll = (dir: 1 | -1) => {
    scrollRef.current?.scrollBy({ left: dir * 140, behavior: "smooth" });
  };

  const idx = ALL.findIndex((s) => s.key === current);
  const stage = ALL[idx];
  const actions = STAGE_ACTIONS[stage.key] ?? [];

  // theme tokens
  const T = theme === "dark"
    ? {
        bg: "bg-[#F3F4F6]",
        rail: "bg-[#0F172A] border-[#1F2937]",
        railShadow: "shadow-[0_12px_32px_-12px_rgba(15,23,42,0.5)]",
        textDim: "text-white/45",
        textMid: "text-white/70",
        textStrong: "text-white/95",
        chipHover: "hover:bg-white/8",
        divider: "bg-white/15",
        connectorIdle: "rgba(255,255,255,0.08)",
        scrollBtn: "bg-[#0F172A]/95 border-white/10 text-white/80 hover:text-white hover:bg-[#1F2937]",
        popoverBg: "bg-[#0F172A] border-white/10",
        popoverShadow: "shadow-[0_12px_32px_-8px_rgba(15,23,42,0.6)]",
        popoverArrow: "bg-[#0F172A] border-white/10",
        actionText: "text-white/85 hover:text-white hover:bg-white/8",
        toggleBg: "bg-[#0F172A]/90 border-white/10 text-white/80",
      }
    : {
        bg: "bg-[#F3F4F6]",
        rail: "bg-white border-[#E5E7EB]",
        railShadow: "shadow-[0_10px_28px_-12px_rgba(17,24,39,0.18)]",
        textDim: "text-[#9CA3AF]",
        textMid: "text-[#6B7280]",
        textStrong: "text-[#111827]",
        chipHover: "hover:bg-[#F3F4F6]",
        divider: "bg-[#E5E7EB]",
        connectorIdle: "#E5E7EB",
        scrollBtn: "bg-white border-[#E5E7EB] text-[#6B7280] hover:text-[#111827] hover:bg-[#F9FAFB]",
        popoverBg: "bg-white border-[#E5E7EB]",
        popoverShadow: "shadow-[0_12px_32px_-8px_rgba(17,24,39,0.18)]",
        popoverArrow: "bg-white border-[#E5E7EB]",
        actionText: "text-[#374151] hover:text-[#111827] hover:bg-[#F3F4F6]",
        toggleBg: "bg-white border-[#E5E7EB] text-[#6B7280]",
      };

  // magnify scale based on distance from hovered chip
  const magnifyScale = (key: string) => {
    if (!hovered || hovered === key) return hovered === key ? 1.15 : 1;
    const hi = ALL.findIndex(s => s.key === hovered);
    const ki = ALL.findIndex(s => s.key === key);
    const d = Math.abs(hi - ki);
    if (d === 1) return 1.06;
    if (d === 2) return 1.02;
    return 1;
  };

  return (
    <div className={`min-h-screen w-full ${T.bg} flex flex-col items-center justify-end p-6 gap-3`}
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>BP7 · Unificado · largura mínima, side popover, magnifier dock, scroll ←→, dark/light</span>
        <span>Etapa atual: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      {/* Rail container — narrow, with side popover capability */}
      <div className="flex items-stretch gap-2 max-w-full">
        <div className="relative flex items-center">
          {/* Rail */}
          <div className={`relative rounded-full border ${T.rail} ${T.railShadow} flex items-center pl-1 pr-1 py-1`}>
            {/* Left scroll button */}
            {canScrollL && (
              <button
                type="button"
                onClick={() => scroll(-1)}
                aria-label="Rolar para a esquerda"
                className={`shrink-0 w-6 h-6 rounded-full border ${T.scrollBtn} flex items-center justify-center transition-colors mr-0.5 z-10`}
              >
                <ChevronLeft className="w-3.5 h-3.5" strokeWidth={2.5} />
              </button>
            )}

            {/* Scrollable chip strip */}
            <div
              ref={scrollRef}
              className="flex items-center gap-0.5 overflow-x-auto scroll-smooth py-0.5"
              style={{
                maxWidth: 360,
                scrollbarWidth: "none",
                msOverflowStyle: "none",
              }}
            >
              <style>{`.bp7-scroll::-webkit-scrollbar{display:none}`}</style>
              {ALL.map((s, i) => {
                const isCurrent = s.key === current;
                const isPast = i < idx && i < FLOW.length;
                const isUtility = i >= FLOW.length;
                const isHovered = hovered === s.key;
                const scale = magnifyScale(s.key);
                return (
                  <div key={s.key} className="flex items-center shrink-0">
                    {i > 0 && i < FLOW.length && !isUtility && (
                      <span
                        aria-hidden
                        className="h-[2px] w-2 rounded-full mx-0.5 shrink-0"
                        style={{
                          background: isPast || isCurrent
                            ? `linear-gradient(90deg, ${ALL[i - 1].accent}cc, ${s.accent}${isCurrent ? "88" : "cc"})`
                            : T.connectorIdle,
                        }}
                      />
                    )}
                    {i === FLOW.length && (
                      <span aria-hidden className={`h-4 w-px ${T.divider} mx-1.5 shrink-0`} />
                    )}
                    <button
                      type="button"
                      onClick={() => { setCurrent(s.key); setPopoverOpen(true); }}
                      onMouseEnter={() => { setHovered(s.key); if (s.key === current) setPopoverOpen(true); }}
                      onMouseLeave={() => setHovered(null)}
                      onFocus={() => { setHovered(s.key); if (s.key === current) setPopoverOpen(true); }}
                      onBlur={() => setHovered(null)}
                      aria-current={isCurrent ? "step" : undefined}
                      aria-label={s.count ? `${s.label} — ${s.count} pendência(s)` : s.label}
                      title={s.label}
                      style={{
                        transform: `scale(${scale})`,
                        transformOrigin: "center bottom",
                        ...(isCurrent
                          ? { backgroundColor: s.accent, color: "#0F172A", boxShadow: `0 0 0 3px ${s.accent}33, 0 4px 12px -2px ${s.accent}80` }
                          : isPast || isHovered
                          ? { color: s.accent }
                          : {}),
                      }}
                      className={`relative flex items-center gap-1 rounded-full text-[11px] font-bold whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/60
                        transition-[padding,background-color,color,transform] duration-150 ease-out
                        ${isCurrent ? "px-1.5 py-1" : isHovered ? `px-2 py-1 ${T.chipHover}` : `px-1.5 py-1 ${T.textDim} ${T.chipHover}`}`}
                    >
                      <span className="relative inline-flex items-center">
                        {isPast && !isHovered ? (
                          <Check className="w-3.5 h-3.5" strokeWidth={2.75} />
                        ) : (
                          <s.Icon className="w-3.5 h-3.5" strokeWidth={isCurrent ? 2.5 : 2} />
                        )}
                        {s.count != null && s.count > 0 && (
                          <span
                            aria-hidden
                            className="absolute -top-1.5 -right-1.5 min-w-[13px] h-[13px] px-1 rounded-full text-[9px] font-bold flex items-center justify-center"
                            style={
                              isCurrent
                                ? { backgroundColor: "#fff", color: s.accent }
                                : { backgroundColor: s.accent, color: theme === "dark" ? "#0F172A" : "#fff" }
                            }
                          >
                            {s.count}
                          </span>
                        )}
                      </span>
                      {isHovered && !isCurrent && <span className="tracking-wide">{s.label}</span>}
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Right scroll button */}
            {canScrollR && (
              <button
                type="button"
                onClick={() => scroll(1)}
                aria-label="Rolar para a direita"
                className={`shrink-0 w-6 h-6 rounded-full border ${T.scrollBtn} flex items-center justify-center transition-colors ml-0.5 z-10`}
              >
                <ChevronRight className="w-3.5 h-3.5" strokeWidth={2.5} />
              </button>
            )}

            {/* Vaga inline */}
            <span aria-hidden className={`mx-1.5 h-4 w-px ${T.divider} shrink-0`} />
            <span className={`text-[10.5px] ${T.textMid} truncate max-w-[140px] shrink`} title="Engenheiro(a) de Dados Sr — Itaú">
              <span className={`${T.textStrong} font-semibold`}>Eng. Dados Sr</span>
            </span>

            {/* Mini "more / popover toggle" button */}
            <button
              type="button"
              onClick={() => setPopoverOpen((v) => !v)}
              aria-label={popoverOpen ? "Ocultar ações da etapa" : "Mostrar ações da etapa"}
              aria-expanded={popoverOpen}
              title={popoverOpen ? "Ocultar ações" : "Mostrar ações"}
              className={`ml-1 shrink-0 w-6 h-6 rounded-full border ${T.scrollBtn} flex items-center justify-center transition-all ${popoverOpen ? "rotate-90" : ""}`}
            >
              <MoreHorizontal className="w-3.5 h-3.5" strokeWidth={2.5} />
            </button>
          </div>
        </div>

        {/* Side popover — slides out to the right of the rail */}
        {popoverOpen && (
          <div
            role="menu"
            aria-label={`Ações de ${stage.label}`}
            className={`rounded-full border ${T.popoverBg} ${T.popoverShadow} px-1.5 py-1 flex items-center gap-0.5 relative animate-in fade-in slide-in-from-left-2 duration-150`}
          >
            <div
              className="text-[9px] font-bold uppercase tracking-wider px-2 py-1 rounded-full mr-0.5 shrink-0"
              style={{ color: stage.accent, backgroundColor: `${stage.accent}1F` }}
            >
              {stage.label}
            </div>
            {actions.map((a) => (
              <button
                key={a.label}
                type="button"
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10.5px] font-semibold whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/60
                  ${a.primary ? "text-[#0F172A]" : T.actionText}`}
                style={a.primary ? { backgroundColor: stage.accent } : undefined}
              >
                <a.Icon className="w-3 h-3" style={a.primary ? undefined : { color: stage.accent }} strokeWidth={2.25} />
                {a.label}
              </button>
            ))}
            {/* arrow pointing left toward rail */}
            <span
              aria-hidden
              className={`absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-2 rotate-45 border-l border-b ${T.popoverArrow}`}
            />
          </div>
        )}
      </div>

      {/* Theme toggle floating */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setTheme(t => t === "dark" ? "light" : "dark")}
          aria-label="Inverter tema (claro/escuro)"
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-semibold ${T.toggleBg} hover:scale-105 transition-transform`}
        >
          {theme === "dark" ? <Sun className="w-3 h-3" /> : <Moon className="w-3 h-3" />}
          {theme === "dark" ? "Inverter para claro" : "Inverter para escuro"}
        </button>
        <span className="text-[10px] text-[#9CA3AF]">·</span>
        <span className="text-[10px] text-[#9CA3AF]">passe o mouse pra ver o magnifier · use ←→ se houver overflow</span>
      </div>
    </div>
  );
}
