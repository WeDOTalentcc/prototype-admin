"use client"

/**
 * DepartmentScopeBanner — Sprint 2 RBAC Phase 3 (2026-05-25)
 *
 * Banner informativo no topo do Hub Usuários & Departamentos.
 * Educar admin sobre RBAC Sprint 2 soft-launch + nudge para popular dept_id.
 *
 * Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
 *
 * Lógica condicional:
 * - 0 departments cadastrados → message "Crie departments primeiro" + CTA Departamentos tab
 * - ≥1 departments + N users sem dept_id → message "Cadastre dept dos usuários para ativar granularidade"
 *
 * Dismiss: localStorage persistente per company. Reset quando dept count muda
 * (e.g., admin cria 1° dept → banner reaparece com mensagem nova).
 *
 * Sprint 2 RBAC filter logic em crud.py:577-595 enforces dept scope SOFT LAUNCH:
 * users com department_id=NULL veem TUDO (legacy). Banner explica esse comportamento.
 */

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Info, X, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface DepartmentScopeBannerProps {
  departmentsCount: number
  /** Optional: total users count. If known, can refine messaging. Banner shows regardless. */
  usersCount?: number
  /** Callback when admin clicks "Ir para Departamentos" CTA (switch tab) */
  onSwitchToDepartmentsTab?: () => void
  /** Company ID for localStorage key isolation (per tenant) */
  companyId?: string | null
}

const LS_KEY_PREFIX = "wedo.dept-scope-banner-dismissed"

export function DepartmentScopeBanner({
  departmentsCount,
  usersCount,
  onSwitchToDepartmentsTab,
  companyId,
}: DepartmentScopeBannerProps) {
  const lsKey = `${LS_KEY_PREFIX}.${companyId || "global"}.depts-${departmentsCount}`
  const [dismissed, setDismissed] = useState(false)
  const [hydrated, setHydrated] = useState(false)

  // SSR safety: read localStorage só após mount
  useEffect(() => {
    if (typeof window === "undefined") return
    try {
      setDismissed(window.localStorage.getItem(lsKey) === "1")
    } catch {
      // localStorage may be blocked; default = show banner
    }
    setHydrated(true)
  }, [lsKey])

  if (!hydrated) return null
  if (dismissed) return null

  const handleDismiss = () => {
    setDismissed(true)
    try {
      window.localStorage.setItem(lsKey, "1")
    } catch {
      // ignore — banner stays hidden in this session at minimum
    }
  }

  const hasNoDepartments = departmentsCount === 0
  const hasDepartmentsButNeedsAssignment = departmentsCount > 0

  return (
    <Card
      className={cn(
        "border border-wedo-cyan/30 bg-wedo-cyan/5 dark:border-wedo-cyan/30 dark:bg-wedo-cyan/10"
      )}
      data-testid="department-scope-banner"
    >
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          <div className="w-7 h-7 rounded-md bg-wedo-cyan/15 flex items-center justify-center flex-shrink-0 mt-0.5">
            <Info className="w-4 h-4 text-wedo-cyan-dark dark:text-wedo-cyan-dark" />
          </div>

          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium text-lia-text-primary mb-0.5">
              {hasNoDepartments
                ? "Configure departamentos para ativar visibilidade granular"
                : "Cadastre o departamento de cada usuário"}
            </h4>
            <p className="text-xs text-lia-text-secondary leading-relaxed">
              {hasNoDepartments ? (
                <>
                  Sem departamentos cadastrados, todos os recrutadores veem todas as vagas do tenant (modo legacy).
                  Crie departamentos na aba "Departamentos" para ativar o controle de acesso por área.
                </>
              ) : (
                <>
                  Usuários sem departamento atribuído continuam vendo todas as vagas (modo legacy compatível).
                  Para ativar granularidade RBAC (manager vê apenas seu departamento), edite cada usuário e selecione o departamento.
                  {typeof usersCount === "number" && usersCount > 0 && (
                    <> Você tem <strong>{usersCount} usuário{usersCount > 1 ? "s" : ""}</strong> nesta empresa.</>
                  )}
                </>
              )}
            </p>

            {hasNoDepartments && onSwitchToDepartmentsTab && (
              <Button
                variant="link"
                size="sm"
                className="h-auto p-0 mt-2 text-xs text-wedo-cyan-text hover:text-wedo-cyan dark:text-wedo-cyan-dark dark:hover:text-wedo-cyan"
                onClick={onSwitchToDepartmentsTab}
                data-testid="department-scope-banner-cta"
              >
                Ir para Departamentos
                <ArrowRight className="w-3 h-3 ml-1" />
              </Button>
            )}
          </div>

          <button
            type="button"
            onClick={handleDismiss}
            className="text-lia-text-tertiary hover:text-lia-text-secondary transition-colors flex-shrink-0"
            aria-label="Dispensar banner"
            data-testid="department-scope-banner-dismiss"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
