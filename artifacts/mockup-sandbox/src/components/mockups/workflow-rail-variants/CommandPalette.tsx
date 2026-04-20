import "./_group.css";
import { useState } from "react";
import {
  Briefcase, Search, UserCheck, Calendar, FileText, TrendingUp,
  BarChart3, Sparkles, Plus, ArrowRight, CornerDownLeft, Command, type LucideIcon,
} from "lucide-react";

type Stage = { key: string; label: string; Icon: LucideIcon; accent: string; count?: number; hint?: string };
const STAGES: Stage[] = [
  { key: "definir-vaga", label: "Definir vaga", Icon: Briefcase, accent: "#60BED1", count: 1, hint: "1 rascunho" },
  { key: "sourcing", label: "Sourcing", Icon: Search, accent: "#5DA47A", count: 12, hint: "12 novos" },
  { key: "triagem", label: "Triagem", Icon: UserCheck, accent: "#5DA47A", count: 3, hint: "3 review" },
  { key: "entrevista", label: "Entrevista", Icon: Calendar, accent: "#D19960", count: 2, hint: "2 hoje" },
  { key: "oferta", label: "Oferta", Icon: FileText, accent: "#9860D1", count: 1, hint: "1 carta" },
  { key: "contratacao", label: "Contratação", Icon: TrendingUp, accent: "#9860D1" },
  { key: "analytics", label: "Analytics", Icon: BarChart3, accent: "#D1A960" },
  { key: "ia-automacoes", label: "IA & Automações", Icon: Sparkles, accent: "#60BED1" },
];

const QUICK_ACTIONS = [
  { id: "criar-vaga", label: "Criar nova vaga", Icon: Briefcase, kbd: "C" },
  { id: "buscar-cand", label: "Buscar candidato por nome", Icon: Search, kbd: "/" },
  { id: "ver-pendencias", label: "Ver minhas pendências", Icon: ArrowRight, kbd: "P" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(true);
  const [query, setQuery] = useState("");
  const current = STAGES[2];
  const totalPending = STAGES.reduce((sum, s) => sum + (s.count ?? 0), 0);
  const filtered = STAGES.filter((s) => s.label.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="min-h-screen w-full bg-[#F9FAFB] flex items-end justify-end p-6 relative"
         style={{ fontFamily: "'Open Sans', system-ui, sans-serif" }}>
      <div className="absolute top-6 left-6 right-6 text-[11px] text-[#9CA3AF] flex items-center justify-between">
        <span>Hipótese B1 · Command Palette · invisível por padrão, busca-first (⌘K)</span>
        <span>Etapa: <strong className="text-[#6B7280]">{current.label}</strong></span>
      </div>

      {/* Floating pill — the only persistent UI */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Abrir paleta de comandos"
        className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-full bg-white border border-[#E5E7EB] shadow-[0_8px_20px_-6px_rgba(17,24,39,0.18)] text-[11px] font-semibold text-[#111827] hover:border-[#9CA3AF] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#60BED1]/50 transition-all"
      >
        <span className="w-5 h-5 rounded-full flex items-center justify-center" style={{ backgroundColor: `${current.accent}1F` }}>
          <current.Icon className="w-3 h-3" style={{ color: current.accent }} />
        </span>
        <span>{current.label}</span>
        {totalPending > 0 && (
          <span className="text-[10px] text-white bg-[#111827] rounded-full px-1.5 py-px font-bold">{totalPending}</span>
        )}
        <span aria-hidden className="h-3 w-px bg-[#E5E7EB] mx-0.5" />
        <span className="inline-flex items-center gap-0.5 text-[#9CA3AF] text-[10px] font-mono">
          <Command className="w-3 h-3" />K
        </span>
      </button>

      {/* Palette overlay */}
      {open && (
        <div
          role="dialog"
          aria-label="Paleta de comandos"
          className="absolute bottom-16 right-6 w-[420px] rounded-xl bg-white border border-[#E5E7EB] shadow-[0_24px_48px_-12px_rgba(17,24,39,0.32)] overflow-hidden"
        >
          <div className="flex items-center gap-2 px-3 py-2.5 border-b border-[#E5E7EB]">
            <Search className="w-4 h-4 text-[#9CA3AF]" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar etapa, candidato, ação…"
              className="flex-1 bg-transparent outline-none text-[12px] text-[#111827] placeholder-[#9CA3AF]"
            />
            <button onClick={() => setOpen(false)} aria-label="Fechar" className="text-[10px] text-[#9CA3AF] font-mono px-1.5 py-0.5 rounded border border-[#E5E7EB] hover:bg-[#F3F4F6]">esc</button>
          </div>

          <div className="max-h-[320px] overflow-y-auto py-1">
            {query === "" && (
              <div className="px-3 pt-2 pb-1 text-[10px] font-semibold text-[#9CA3AF] uppercase tracking-wide">Ações rápidas</div>
            )}
            {query === "" && QUICK_ACTIONS.map((a) => (
              <button key={a.id} className="w-full flex items-center gap-2.5 px-3 py-2 hover:bg-[#F3F4F6] focus-visible:outline-none focus-visible:bg-[#F3F4F6] text-left transition-colors">
                <a.Icon className="w-3.5 h-3.5 text-[#6B7280]" />
                <span className="flex-1 text-[12px] text-[#111827]">{a.label}</span>
                <span className="text-[10px] text-[#9CA3AF] font-mono px-1.5 py-0.5 rounded border border-[#E5E7EB]">{a.kbd}</span>
              </button>
            ))}

            <div className="px-3 pt-2 pb-1 text-[10px] font-semibold text-[#9CA3AF] uppercase tracking-wide">Etapas do funil</div>
            {filtered.map((s) => {
              const isCurrent = s.key === current.key;
              return (
                <button key={s.key} className={`w-full flex items-center gap-2.5 px-3 py-2 hover:bg-[#F3F4F6] focus-visible:outline-none focus-visible:bg-[#F3F4F6] text-left transition-colors ${isCurrent ? "bg-[#F9FAFB]" : ""}`}>
                  <span className="w-5 h-5 rounded flex items-center justify-center" style={{ backgroundColor: `${s.accent}1F` }}>
                    <s.Icon className="w-3 h-3" style={{ color: s.accent }} />
                  </span>
                  <span className="flex-1 text-[12px] text-[#111827]">{s.label}</span>
                  {s.hint && <span className="text-[10px] text-[#9CA3AF]">{s.hint}</span>}
                  {isCurrent && <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: s.accent }}>atual</span>}
                </button>
              );
            })}
          </div>

          <div className="flex items-center justify-between px-3 py-1.5 bg-[#F9FAFB] border-t border-[#E5E7EB] text-[10px] text-[#9CA3AF]">
            <span className="flex items-center gap-2">
              <span className="font-mono">↑↓</span> navegar
              <span className="font-mono inline-flex items-center"><CornerDownLeft className="w-3 h-3" /></span> ir
            </span>
            <span className="flex items-center gap-1 font-medium text-[#6B7280]">
              <Plus className="w-3 h-3" /> Criar vaga <span className="font-mono ml-1">⌘N</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
