"use client"

import { ThumbsUp, ThumbsDown, Loader2 } from "lucide-react"
import type { Candidate } from "@/components/pages/candidates/types"
import { TwilioCallButton } from "./TwilioCallButton"

interface TriagemDetailsFooterProps {
  candidate: Candidate
  approving: boolean
  setApproving: (v: boolean) => void
  rejecting: boolean
  setRejecting: (v: boolean) => void
  confirmReject: boolean
  setConfirmReject: (v: boolean) => void
  onApprove?: (candidate: Candidate) => void
  onReject?: (candidate: Candidate) => void
  /** Task #425 — Twilio PSTN trigger context. */
  jobTitle?: string
  jobId?: string
  companyId?: string
}

export function TriagemDetailsFooter({
  candidate, approving, setApproving, rejecting, setRejecting,
  confirmReject, setConfirmReject, onApprove, onReject,
  jobTitle, jobId, companyId,
}: TriagemDetailsFooterProps) {
  return (
    <div className="flex-shrink-0 px-4 py-3 flex items-center justify-between border-t border-lia-border-subtle bg-lia-bg-secondary">
      <div className="flex items-center gap-2">
        <span className="text-micro text-lia-text-secondary">Decisão do Recrutador</span>
        <TwilioCallButton
          candidate={candidate}
          jobTitle={jobTitle}
          jobId={jobId}
          companyId={companyId}
        />
      </div>
      <div className="flex items-center gap-2">
        {confirmReject ? (
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-status-error font-medium">Confirmar reprovação?</span>
            <button
              onClick={async () => {
                setRejecting(true)
                await onReject?.(candidate)
                setRejecting(false)
                setConfirmReject(false)
              }}
              disabled={rejecting}
              className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none disabled:opacity-50 bg-status-error text-lia-text-tertiary"
            >
              {rejecting ? <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" /> : <ThumbsDown className="w-3 h-3" />}
              Sim, reprovar
            </button>
            <button
              onClick={() => setConfirmReject(false)}
              className="px-2.5 py-1.5 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover border border-lia-border-subtle bg-lia-bg-secondary"
            >
              Cancelar
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmReject(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-xl transition-colors motion-reduce:transition-none hover:bg-status-error/10 border border-lia-border-subtle text-status-error"
          >
            <ThumbsDown className="w-3.5 h-3.5" />
            Reprovar
          </button>
        )}
        <button
          onClick={async () => {
            setApproving(true)
            await onApprove?.(candidate)
            setApproving(false)
          }}
          disabled={approving}
          className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-xl transition-colors motion-reduce:transition-none hover:bg-lia-btn-primary-hover disabled:opacity-50 bg-lia-btn-primary-bg text-lia-text-tertiary"
        >
          {approving ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" /> : <ThumbsUp className="w-3.5 h-3.5" />}
          Aprovar para Entrevista
        </button>
      </div>
    </div>
  )
}
