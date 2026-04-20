import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, Check, ArrowRight, Users, CalendarPlus, Pencil, Send, PartyPopper,
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

type Action = { label: string; Icon: LucideIcon; primary?: boolean };
const STAGE_ACTIONS: Record<string, Action[]> = {
  "definir-vaga": [
    { label: "Nova vaga", Icon: Plus, primary: true },
    { label: "Editar vaga ativa", Icon: Pencil },
    { label: "Publicar", Icon: ArrowRight },
  ],
  "sourcing":     [{ label: "Ver candidatos", Icon: Users, primary: true }, { label: "Buscar talentos", Icon: Search }],
  "triagem":      [{ label: "Ver candidatos", Icon: Users, primary: true }, { label: "Avançar p/ Entrevista", Icon: ArrowRight }],
  "entrevista":   [{ label: "Ver candidatos", Icon: Users, primary: true }, { label: "Agendar", Icon: CalendarPlus }, { label: "Próx: Oferta", Icon: ArrowRight }],
  "oferta":       [{ label: "Enviar proposta", Icon: Send, primary: true }, { label: "Próx: Contratação", Icon: ArrowRight }],
  "contratacao":  [{ label: "Concluir onboarding", Icon: PartyPopper, primary: true }],
};

export function DarkUnificado() {
  const [current, setCurrent] = useState("entrevista");
  const [hovered, setHovered] = useState<string | null>(null);
  const [popoverOpen, setPopoverOpen] = useState(true);
  const idx = FLOW.findIndex((s) => s.key === current);
  const stage = FLOW[idx];
  const actions = STAGE_ACTIONS[stage.key] ?? [];

  return (
    <div className="min-h-screen w-full bg-[#F3F4F6] flex items-end justify-center p-6"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#6B7280] flex items-center justify-between">
        <span>BP6 · Unificado · sem CTA solto, "Nova vaga" mora dentro de Definir vaga</span>
        <span>Etapa atual: <strong className="text-[#111827]">{stage.label}</strong></span>
      </div>

      <div className="w-[min(720px,calc(100%-1rem))] relative">
        {/* Popover de ações ancorado no chip da etapa atual */}
        {popoverOpen && (
          <div
            className="absolute bottom-full mb-2 left-0 right-0 flex justify-start pointer-events-none"
            style={{ paddingLeft: `${(idx / FLOW.length) * 100 + 2}%` }}
          >
            <div
              role="menu"
              className="pointer-events-auto rounded-xl bg-[#0F172A] border border-white/10 shadow-[0_12px_32px_-8px_rgba(15,23,42,0.6)] px-1 py-1 flex items-center gap-0.5 relative"
            >
              <div
                className="text-[9px] font-bold uppercase tracking-wider px-2 py-1 rounded-md mr-0.5"
                style={{ color: stage.accent, backgroundColor: `${stage.accent}1A` }}
              >
                {stage.label}
              </div>
              {actions.map((a) => (
                <button
                  key={a.label}
                  type="button"
                  className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[10.5px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60
                    ${a.primary
                      ? "text-[#0F172A]"
                      : "text-white/80 hover:text-white hover:bg-white/8"}`}
                  style={a.primary ? { backgroundColor: stage.accent } : undefined}
                >
                  <a.Icon className="w-3 h-3" style={a.primary ? undefined : { color: stage.accent }} strokeWidth={2.25} />
                  {a.label}
                </button>
              ))}
              <span
                aria-hidden
                className="absolute -bottom-1 w-2 h-2 rotate-45 bg-[#0F172A] border-r border-b border-white/10"
                style={{ left: "14px" }}
              />
            </div>
          </div>
        )}

        <div className="rounded-full bg-[#0F172A] shadow-[0_12px_32px_-12px_rgba(15,23,42,0.5)] border border-[#1F2937]
                        flex items-center pl-2 pr-2 py-1 gap-0.5">
          {FLOW.map((s, i) => {
            const isCurrent = s.key === current;
            const isPast = i < idx;
            const isHovered = hovered === s.key;
            return (
              <div key={s.key} className="flex items-center">
                {i > 0 && (
                  <span
                    aria-hidden
                    className="h-[2px] w-2.5 rounded-full mx-0.5"
                    style={{
                      background: isPast || isCurrent
                        ? `linear-gradient(90deg, ${FLOW[i - 1].accent}cc, ${s.accent}${isCurrent ? "88" : "cc"})`
                        : "rgba(255,255,255,0.08)",
                    }}
                  />
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
                  style={
                    isCurrent
                      ? { backgroundColor: s.accent, color: "#0F172A", boxShadow: `0 0 0 3px ${s.accent}33, 0 4px 12px -2px ${s.accent}80` }
                      : isPast || isHovered
                      ? { color: s.accent }
                      : undefined
                  }
                  className={`relative flex items-center gap-1 rounded-full text-[11px] font-bold whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60
                    transition-[padding,background-color,color] duration-150 ease-out
                    ${isCurrent ? "px-1.5 py-1 scale-[1.05]" : isHovered ? "px-2 py-1 bg-white/8" : "px-1.5 py-1 text-white/45 hover:bg-white/5"}`}
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
                            : { backgroundColor: s.accent, color: "#0F172A" }
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

          {/* Vaga inline */}
          <span aria-hidden className="ml-1.5 mr-1 h-4 w-px bg-white/15" />
          <span className="text-[10.5px] text-white/55 truncate max-w-[170px] sm:max-w-[240px] flex-1 min-w-0" title="Engenheiro(a) de Dados Sr — Itaú">
            <span className="text-white/95 font-semibold">Eng. Dados Sr</span> <span className="text-white/40">— Itaú</span>
          </span>

          {/* Utilities */}
          <span aria-hidden className="ml-1.5 mr-0.5 h-4 w-px bg-white/15" />
          {UTILITIES.map((u) => (
            <button
              key={u.key}
              type="button"
              title={u.label}
              aria-label={u.label}
              className="flex items-center px-1.5 py-1 rounded-full text-white/50 hover:text-white hover:bg-white/5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
            >
              <u.Icon className="w-3.5 h-3.5" style={{ color: u.accent }} strokeWidth={2} />
            </button>
          ))}
        </div>

        <div className="mt-2 flex justify-center gap-3">
          <button
            type="button"
            onClick={() => { setCurrent("definir-vaga"); setPopoverOpen(true); }}
            className="text-[10px] text-[#6B7280] hover:text-[#111827] underline underline-offset-2"
          >
            simular hover em "Definir vaga" (mostra "+ Nova vaga" como ação primária)
          </button>
          <span className="text-[10px] text-[#9CA3AF]">·</span>
          <button
            type="button"
            onClick={() => setPopoverOpen((v) => !v)}
            className="text-[10px] text-[#6B7280] hover:text-[#111827] underline underline-offset-2"
          >
            {popoverOpen ? "ocultar" : "mostrar"} popover
          </button>
        </div>
      </div>
    </div>
  );
}
