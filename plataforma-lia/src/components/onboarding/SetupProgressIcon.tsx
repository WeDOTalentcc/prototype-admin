"use client"

import { useState, useCallback, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useLocale } from "next-intl"
import { useQuery } from "@tanstack/react-query"
import { CheckCircle2, Circle, ChevronRight, Settings2 } from "lucide-react"
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Button } from "@/components/ui/button"

// ─── Types ──────────────────────────────────────────────────────────────────

interface ProgressResponse {
  overall: number
  sections: Record<string, number>
}

interface Task {
  id: string
  label: string
  sectionId: string
}

// ─── Task definitions (6 canonical setup sections) ───────────────────────

const SETUP_TASKS: Task[] = [
  { id: "minha-empresa",          label: "Perfil da empresa",        sectionId: "minha-empresa" },
  { id: "lia-personalizacao",     label: "Personalização da IA",     sectionId: "lia-personalizacao" },
  { id: "pipeline",               label: "Pipeline de seleção",      sectionId: "pipeline" },
  { id: "screening",              label: "Triagem de candidatos",    sectionId: "screening" },
  { id: "usuarios-departamentos", label: "Usuários & Departamentos", sectionId: "usuarios-departamentos" },
  { id: "comunicacao-alertas",    label: "Comunicação & Alertas",    sectionId: "comunicacao-alertas" },
]

const COMPLETE_THRESHOLD = 80   // overall >= 80 → hide icon
const SECTION_DONE_AT   = 70   // section >= 70 → checked

// ─── SVG Progress Ring ────────────────────────────────────────────────────

function ProgressRing({ progress, size = 28 }: { progress: number; size?: number }) {
  const r = (size - 4) / 2
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - Math.min(100, Math.max(0, progress)) / 100)

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="-rotate-90"
      aria-hidden="true"
    >
      <circle
        cx={size / 2} cy={size / 2} r={r}
        fill="none" stroke="currentColor" strokeWidth="2"
        className="text-lia-text-muted"
      />
      <circle
        cx={size / 2} cy={size / 2} r={r}
        fill="none" stroke="currentColor" strokeWidth="2"
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        className="text-wedo-cyan transition-all duration-500 motion-reduce:transition-none"
      />
    </svg>
  )
}

// ─── Main Component ────────────────────────────────────────────────────────

export function SetupProgressIcon() {
  const router = useRouter()
  const locale = useLocale()
  const [open, setOpen] = useState(false)

  const { data, refetch } = useQuery<ProgressResponse>({
    queryKey: SETTINGS_QUERY_KEYS.settingsProgress(),
    queryFn: () =>
      fetch("/api/backend-proxy/settings/progress/", { credentials: "include" }).then(r => r.json()),
    staleTime: 30_000,
  })

  useEffect(() => {
    if (typeof window === "undefined") return
    const handler = () => { refetch() }
    window.addEventListener("lia:settings-success", handler)
    window.addEventListener("lia:settings-updated", handler)
    return () => {
      window.removeEventListener("lia:settings-success", handler)
      window.removeEventListener("lia:settings-updated", handler)
    }
  }, [refetch])

  const overall = data?.overall ?? 0
  const sections = data?.sections ?? {}

  // Hide once setup is complete
  if (data && overall >= COMPLETE_THRESHOLD) return null

  const badgeCount = SETUP_TASKS.filter(
    t => (sections[t.sectionId] ?? 0) < SECTION_DONE_AT
  ).length

  const handleTaskClick = useCallback((sectionId: string) => {
    setOpen(false)
    router.push(`/${locale}/configuracoes?section=${sectionId}`)
  }, [router, locale])

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={`Configurar empresa — ${Math.round(overall)}% completo`}
          title="Configurar empresa"
          className="relative h-7 w-7 flex items-center justify-center rounded-full hover:bg-lia-interactive-hover transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan"
        >
          <ProgressRing progress={overall} size={24} />
          {badgeCount > 0 && (
            <span
              aria-hidden="true"
              className="absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] flex items-center justify-center rounded-full bg-wedo-cyan text-white text-[9px] font-semibold leading-none px-[3px]"
            >
              {badgeCount}
            </span>
          )}
        </button>
      </PopoverTrigger>

      <PopoverContent
        side="right"
        align="end"
        sideOffset={10}
        className="w-72 p-0 shadow-xl rounded-xl border border-lia-border-subtle bg-lia-bg-primary z-50"
      >
        {/* Header */}
        <div className="px-4 pt-4 pb-3 border-b border-lia-border-subtle">
          <div className="flex items-center justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-lia-text-primary">Configure sua empresa</p>
              <p className="text-xs text-lia-text-secondary mt-0.5">{Math.round(overall)}% completo</p>
            </div>
            <ProgressRing progress={overall} size={36} />
          </div>
          <div className="mt-3 h-1.5 rounded-full bg-lia-bg-tertiary overflow-hidden">
            <div
              className="h-full rounded-full bg-wedo-cyan transition-all duration-500 motion-reduce:transition-none"
              style={{ width: `${overall}%` }}
            />
          </div>
        </div>

        {/* Task list */}
        <div className="py-2">
          {SETUP_TASKS.map(task => {
            const done = (sections[task.sectionId] ?? 0) >= SECTION_DONE_AT
            return (
              <button
                key={task.id}
                type="button"
                onClick={() => handleTaskClick(task.sectionId)}
                className="w-full flex items-center gap-3 px-4 py-2 hover:bg-lia-interactive-hover transition-colors duration-150 text-left group"
              >
                {done ? (
                  <CheckCircle2 className="w-4 h-4 text-status-success flex-shrink-0" />
                ) : (
                  <Circle className="w-4 h-4 text-lia-text-muted flex-shrink-0" />
                )}
                <span className={`flex-1 text-xs leading-snug ${done ? "text-lia-text-muted line-through" : "text-lia-text-primary"}`}>
                  {task.label}
                </span>
                {!done && (
                  <ChevronRight className="w-3 h-3 text-lia-text-muted flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                )}
              </button>
            )
          })}
        </div>

        {/* Footer */}
        <div className="px-4 pb-4 pt-1 border-t border-lia-border-subtle">
          <Button
            variant="outline"
            size="sm"
            className="w-full text-xs mt-2"
            onClick={() => {
              setOpen(false)
              router.push(`/${locale}/configuracoes`)
            }}
          >
            <Settings2 className="w-3.5 h-3.5 mr-1.5" aria-hidden="true" />
            Ver todas as configurações
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
