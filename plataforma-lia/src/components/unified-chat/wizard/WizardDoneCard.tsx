import React, { useState } from "react"
import { CheckCircle2, ExternalLink, Plus, Target, Mail, Link2, ChevronDown, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import type { HandoffData } from "./wizard-types"

interface DoneData extends HandoffData {
  parsed_manager_email?: string | null
  parsed_manager_name?: string | null
}

interface Props {
  data: Record<string, unknown>
}

/**
 * WizardDoneCard — rich card inline no chat para os estágios done/handoff.
 *
 * Mostra sucesso da criação da vaga com ações contextuais: ir para a vaga,
 * calibrar perfis, enviar briefing ao gestor, copiar link, criar outra vaga.
 * Substitui o DonePanel lateral — toda interação acontece inline no chat.
 */
export function WizardDoneCard({ data }: Props) {
  const [expanded, setExpanded] = useState(true)
  const [copied, setCopied] = useState(false)
  const d = data as unknown as DoneData
  const jobId = d.job_id
  const jobTitle = d.job_title ?? null
  const handoffUrl = d.handoff_url
  const shareLink = d.share_link
  const managerEmail = d.parsed_manager_email ?? null
  const managerName = d.parsed_manager_name ?? null

  const handleCopyLink = () => {
    if (shareLink) {
      navigator.clipboard.writeText(shareLink)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleNavigateToJob = () => {
    window.dispatchEvent(new CustomEvent("lia:navigation-hint", {
      detail: { page: "vagas", hint: `Vaga ${jobTitle || jobId}` },
    }))
  }

  const handleCalibrate = () => {
    window.dispatchEvent(new CustomEvent("lia:prefill-message", {
      detail: { message: `Quero calibrar perfis de candidatos para a vaga ${jobTitle || jobId || ""}`.trim() },
    }))
  }

  const handleSendBriefing = () => {
    window.dispatchEvent(new CustomEvent("lia:prefill-message", {
      detail: { message: "Enviar plano de trabalho para o gestor" },
    }))
  }

  const handleCreateNew = () => {
    window.dispatchEvent(new CustomEvent("lia:prefill-message", {
      detail: { message: "Criar nova vaga" },
    }))
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className="mt-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary overflow-hidden"
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-lia-interactive-hover transition-colors text-left"
      >
        <div className="w-7 h-7 rounded-full bg-status-success/10 flex items-center justify-center flex-shrink-0">
          <CheckCircle2 className="w-4 h-4 text-status-success" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-lia-text-primary">
            Vaga criada com sucesso!
          </p>
          {jobTitle && (
            <p className="text-xs text-lia-text-secondary truncate">{jobTitle}</p>
          )}
        </div>
        {jobId && (
          <span className="px-2 py-0.5 rounded bg-lia-bg-tertiary text-[10px] text-lia-text-secondary flex-shrink-0">
            ID {jobId}
          </span>
        )}
        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-muted flex-shrink-0 transition-transform",
            expanded && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      {/* Body */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="done-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 space-y-2 border-t border-lia-border-subtle pt-2">
              {/* Primary: go to job */}
              {handoffUrl && (
                <button
                  type="button"
                  onClick={handleNavigateToJob}
                  className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md bg-wedo-cyan/10 text-wedo-cyan-text hover:bg-wedo-cyan/20 transition-colors text-sm font-medium"
                >
                  <ExternalLink className="w-4 h-4" />
                  Ir para a vaga
                </button>
              )}

              {/* Calibration CTA */}
              <button
                type="button"
                onClick={handleCalibrate}
                className="w-full flex flex-col gap-0.5 px-3 py-2.5 rounded-md bg-wedo-cyan/15 text-wedo-cyan-text hover:bg-wedo-cyan/25 transition-colors text-sm font-medium border border-wedo-cyan/20"
              >
                <div className="flex items-center gap-2.5">
                  <Target className="w-4 h-4" />
                  Calibrar perfis antes de buscar
                </div>
                <span className="text-[10px] text-wedo-cyan/70 font-normal ml-[26px]">
                  A IA aprende seu critério e libera o sourcing automático
                </span>
              </button>

              {/* Send briefing to manager */}
              {managerEmail && (
                <button
                  type="button"
                  onClick={handleSendBriefing}
                  className="w-full flex flex-col gap-0.5 px-3 py-2.5 rounded-md bg-lia-bg-primary hover:bg-lia-interactive-hover transition-colors text-sm border border-lia-border-subtle"
                >
                  <div className="flex items-center gap-2.5 text-lia-text-primary font-medium">
                    <Mail className="w-4 h-4 text-lia-text-secondary" />
                    Enviar briefing ao gestor
                  </div>
                  <span className="text-[10px] text-lia-text-tertiary font-normal ml-[26px]">
                    {managerName ? `Para ${managerName}` : managerEmail}
                  </span>
                </button>
              )}

              {/* Copy share link */}
              {shareLink && (
                <button
                  type="button"
                  onClick={handleCopyLink}
                  className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md bg-lia-bg-primary text-lia-text-primary hover:bg-lia-interactive-hover transition-colors text-sm border border-lia-border-subtle"
                >
                  <Link2 className="w-4 h-4 text-lia-text-secondary" />
                  {copied ? "Link copiado!" : "Copiar link de compartilhamento"}
                </button>
              )}

              {/* Create new job */}
              <button
                type="button"
                onClick={handleCreateNew}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md bg-lia-bg-primary text-lia-text-primary hover:bg-lia-interactive-hover transition-colors text-sm border border-lia-border-subtle"
              >
                <Plus className="w-4 h-4 text-lia-text-secondary" />
                Criar outra vaga
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
