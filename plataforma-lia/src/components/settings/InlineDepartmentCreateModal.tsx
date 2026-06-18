"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
/**
 * InlineDepartmentCreateModal — Sprint 2 RBAC Phase 2.5 (2026-05-25)
 *
 * Modal lightweight para criar departamento sem sair da tab Usuários.
 *
 * Plan canonical: ~/.claude/plans/jolly-roaming-moler.md (Sprint 2 RBAC Phase 2.5)
 *
 * Fluxo:
 * 1. Aberto a partir de UserForm quando admin escolhe "+ Criar novo departamento" no select
 * 2. Captura name (required), code (optional), manager_email (optional)
 * 3. POST canonical: /api/backend-proxy/company/departments?company_id={X}
 * 4. Em sucesso: callback onCreated(newDept) → parent refresh departments + auto-select
 * 5. Cancel: callback onOpenChange(false) → user-form reseta select pro previous dept_id
 *
 * Disciplina:
 * - Scope lock: SÓ 3 campos. Full mgmt (members/budget/headcount/parent) via DepartmentFormCard na tab Departamentos.
 * - Erro inline (não silent): submit button disabled + msg de erro visível
 * - Validation client-side: name min 2 chars, sem duplicate vs lista atual
 * - Backend integration: reusa endpoint existente (mesmo que useDepartmentManagement.saveDepartmentToAPI usa)
 */

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Plus, Loader2, AlertCircle } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { apiFetch } from "@/lib/api/api-fetch"
import { useTranslations } from "next-intl"

export interface CreatedDepartment {
  id: string
  name: string
}

/** Quando fornecida, o modal delega o POST ao produtor (fix P1 save-duplicado).
 *  Quando ausente, usa fetch inline (compatibilidade retroativa). */
export type InlineDepartmentSaveFn = (
  name: string,
  payload: { code?: string; managerEmail?: string }
) => Promise<CreatedDepartment>

interface InlineDepartmentCreateModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  companyId: string | null | undefined
  existingDepartments?: Array<{ id?: string; name: string }>
  onCreated: (dept: CreatedDepartment) => void
  /** Produtor canônico de save. Quando passado, remove fetch duplicado do modal. */
  onSave?: InlineDepartmentSaveFn
}

export function InlineDepartmentCreateModal({
  open,
  onOpenChange,
  companyId,
  existingDepartments = [],
  onCreated,
  onSave,
}: InlineDepartmentCreateModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('inline-department-create', open)

  const t = useTranslations("settings.users")
  const [name, setName] = useState("")
  const [code, setCode] = useState("")
  const [managerEmail, setManagerEmail] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const inputClass =
    "w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg"

  const reset = () => {
    setName("")
    setCode("")
    setManagerEmail("")
    setError(null)
    setIsSubmitting(false)
  }

  const handleClose = (nextOpen: boolean) => {
    if (!nextOpen) reset()
    onOpenChange(nextOpen)
  }

  const handleSubmit = async () => {
    setError(null)

    // Client-side validation
    const trimmedName = name.trim()
    if (trimmedName.length < 2) {
      setError("Nome do departamento precisa ter pelo menos 2 caracteres.")
      return
    }

    const duplicate = existingDepartments.some(
      (d) => d.name.toLowerCase() === trimmedName.toLowerCase()
    )
    if (duplicate) {
      setError(`Departamento "${trimmedName}" já existe.`)
      return
    }

    if (!companyId) {
      setError("Company ID não disponível. Recarregue a página.")
      return
    }

    setIsSubmitting(true)
    try {
      let newDept: CreatedDepartment

      if (onSave) {
        // Produtor canônico delega o POST (fix P1: sem save duplicado no modal).
        // O caller é responsável pela lógica de fetch — modal fica thin.
        newDept = await onSave(trimmedName, {
          code: code.trim() || undefined,
          managerEmail: managerEmail.trim() || undefined,
        })
      } else {
        // Fallback inline mantido para compatibilidade retroativa quando
        // o caller não fornece onSave (contextos sem acesso ao hook canonical).
        const payload: Record<string, unknown> = {
          name: trimmedName,
          description: "",
          manager_name: "",
          manager_title: "",
          manager_email: managerEmail.trim() || "",
          manager_phone: "",
          headcount: 0,
          color: "",
        }
        if (code.trim()) {
          payload.code = code.trim()
        }

        const companyIdSafe = companyId ?? ""
        const res = await apiFetch(
          "/api/backend-proxy/company/departments?company_id=" + encodeURIComponent(companyIdSafe),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }
        )

        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          const detail =
            (typeof body.detail === "string" ? body.detail : null) ||
            (typeof body.message === "string" ? body.message : null) ||
            "HTTP " + res.status
          setError("Falha ao criar departamento: " + detail)
          setIsSubmitting(false)
          return
        }

        const result = await res.json().catch(() => ({}))
        // Backend canonical returns dept object com id; some routes wrap em ResponseEnvelope
        newDept = {
          id: result?.id || result?.data?.id || result?.department?.id || "",
          name: result?.name || result?.data?.name || trimmedName,
        }

        if (!newDept.id) {
          setError("Departamento criado mas resposta sem ID. Recarregue a lista.")
          setIsSubmitting(false)
          return
        }
      }

      // Success
      onCreated(newDept)
      reset()
      onOpenChange(false)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro inesperado ao criar departamento. Tente novamente."
      )
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md" data-testid="inline-dept-create-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Criar novo departamento
          </DialogTitle>
          <DialogDescription className="text-xs">
            Campos mínimos para criar rápido. Gestão completa (manager, headcount, budget, hierarquia) fica na aba "Departamentos".
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-2">
          <div>
            <label htmlFor="inline-dept-name" className={textStyles.label + " block mb-1.5"}>
              Nome do departamento <span className="text-status-error">*</span>
            </label>
            <input
              id="inline-dept-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={inputClass}
              placeholder="Ex: Engenharia, RH, Marketing"
              data-testid="inline-dept-name"
              disabled={isSubmitting}
              autoFocus
            />
          </div>

          <div>
            <label htmlFor="inline-dept-code" className={textStyles.label + " block mb-1.5"}>
              Código <span className="text-lia-text-tertiary text-xs">(opcional)</span>
            </label>
            <input
              id="inline-dept-code"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className={inputClass}
              placeholder="Ex: ENG, RH, MKT"
              data-testid="inline-dept-code"
              disabled={isSubmitting}
              maxLength={20}
            />
          </div>

          <div>
            <label htmlFor="inline-dept-manager-email" className={textStyles.label + " block mb-1.5"}>
              Email do gestor <span className="text-lia-text-tertiary text-xs">(opcional)</span>
            </label>
            <input
              id="inline-dept-manager-email"
              type="email"
              value={managerEmail}
              onChange={(e) => setManagerEmail(e.target.value)}
              className={inputClass}
              placeholder="gestor@empresa.com"
              data-testid="inline-dept-manager-email"
              disabled={isSubmitting}
            />
          </div>

          {error && (
            <div
              className="flex items-start gap-2 px-3 py-2 rounded-md bg-status-error/10 border border-status-error/30 text-status-error text-xs"
              data-testid="inline-dept-error"
            >
              <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleClose(false)}
            disabled={isSubmitting}
            data-testid="inline-dept-cancel"
          >
            Cancelar
          </Button>
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={isSubmitting || name.trim().length < 2}
            data-testid="inline-dept-submit"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Criando...
              </>
            ) : (
              <>
                <Plus className="w-3.5 h-3.5 mr-1.5" />
                Criar departamento
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
