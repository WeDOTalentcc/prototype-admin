"use client"

import { Button } from "@/components/ui/button"
import { AlertTriangle, Pause, CheckCircle2, Play } from "lucide-react"
import type { ScreeningStatus } from "@/types/screening"

interface StatusChangeConfirmState {
  newStatus: string
  screeningImpact: "pause" | "complete" | "ask_reactivate" | "none"
}

interface StatusChangeConfirmModalProps {
  state: StatusChangeConfirmState
  jobTitle: string
  onCancel: () => void
  onChange: (newStatus: string, reactivateScreening?: boolean) => void
}

export function StatusChangeConfirmModal({
  state,
  jobTitle,
  onCancel,
  onChange,
}: StatusChangeConfirmModalProps) {
  const { newStatus, screeningImpact } = state
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-lia-overlay">
      <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle w-[420px] p-5 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full flex items-center justify-center bg-lia-bg-tertiary">
            <AlertTriangle className="w-5 h-5 text-lia-text-secondary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-lia-text-primary">
              Alterar Status para {newStatus}
            </h3>
            <p className="text-xs text-lia-text-secondary">{jobTitle}</p>
          </div>
        </div>
        <div className="rounded-xl p-3 mb-4 border border-lia-border-subtle bg-lia-bg-secondary/50">
          <div className="flex items-start gap-2.5">
            <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
              screeningImpact === "pause"
                ? "bg-status-warning/15 dark:bg-status-warning/30"
                : screeningImpact === "complete"
                ? "bg-wedo-cyan/15"
                : "bg-status-success/15 dark:bg-status-success/30"
            }`}>
              {screeningImpact === "pause" && <Pause className="w-3 h-3 text-status-warning" />}
              {screeningImpact === "complete" && <CheckCircle2 className="w-3 h-3 text-wedo-cyan-text" />}
              {screeningImpact === "ask_reactivate" && <Play className="w-3 h-3 text-status-success" />}
            </div>
            <div>
              <p className="text-xs font-semibold text-lia-text-primary mb-1">Impacto na Triagem</p>
              <p className="text-xs leading-relaxed text-lia-text-secondary">
                {screeningImpact === "pause" &&
                  "Ao paralisar esta vaga, a triagem ativa será pausada automaticamente. Candidatos em avaliação serão mantidos no estado atual até a reativação."}
                {screeningImpact === "complete" && newStatus === "Concluída" &&
                  "Ao concluir esta vaga, a triagem será finalizada automaticamente. Nenhum novo candidato será avaliado."}
                {screeningImpact === "complete" && newStatus === "Cancelada" &&
                  "Ao cancelar esta vaga, a triagem será finalizada automaticamente. Todos os processos de avaliação serão encerrados."}
                {screeningImpact === "ask_reactivate" &&
                  "A triagem desta vaga está pausada. Deseja reativar a triagem automaticamente junto com a vaga?"}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 pt-1">
          <Button
            variant="outline"
            size="sm"
            className="text-xs rounded-xl px-4 border-lia-border-subtle"
            onClick={onCancel}
          >
            Cancelar
          </Button>
          {screeningImpact === "ask_reactivate" ? (
            <>
              <Button
                variant="outline"
                size="sm"
                className="text-xs rounded-xl px-4 border-lia-border-default"
                onClick={() => onChange(newStatus, false)}
              >
                Manter Pausada
              </Button>
              <Button
                size="sm"
                className="text-xs rounded-md px-4 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                onClick={() => onChange(newStatus, true)}
              >
                Reativar Triagem
              </Button>
            </>
          ) : (
            <Button
              size="sm"
              className="text-xs rounded-md px-4 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
              onClick={() => onChange(newStatus)}
            >
              Confirmar
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
