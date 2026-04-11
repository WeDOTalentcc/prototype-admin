'use client'

import React, { useState, useEffect } from 'react'
import { UserCheck, Loader2 } from 'lucide-react'
import { useOverrideApprove } from '@/hooks/recruitment/use-override-approve'
import { toast } from "sonner"
interface OverrideApproveButtonProps {
  candidateId: string
  candidateName: string
  vacancyId: string
  onApproved?: (candidateId: string) => void
  disabled?: boolean
}

export function OverrideApproveButton({
  candidateId,
  candidateName,
  vacancyId,
  onApproved,
  disabled = false,
}: OverrideApproveButtonProps) {
  const { isLoading, error, approveOverride } = useOverrideApprove()
  const [showConfirm, setShowConfirm] = useState(false)
useEffect(() => {
    if (error) {
      toast.error('Erro ao aprovar candidato', { description: error })
    }
  }, [error])

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowConfirm(true)
  }

  const handleConfirm = async (e: React.MouseEvent) => {
    e.stopPropagation()
    const result = await approveOverride(candidateId, vacancyId)
    if (result?.success) {
      setShowConfirm(false)
      onApproved?.(candidateId)
    }
  }

  const handleCancel = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowConfirm(false)
  }

  if (showConfirm) {
    return (
      <div
        className="flex items-center gap-1 mt-1"
        onClick={(e) => e.stopPropagation()}
      >
        <span className="text-micro text-lia-text-secondary">
          Aprovar {candidateName.split(' ')[0]}?
        </span>
        <button
          onClick={handleConfirm}
          disabled={isLoading || disabled}
          className={
            'inline-flex items-center gap-0.5 px-2 py-0.5 text-micro font-medium rounded-md ' +
            'bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover active:bg-lia-btn-primary-hover ' +
            'disabled:bg-lia-border-default disabled:text-lia-text-secondary disabled:cursor-not-allowed ' +
            'transition-colors duration-150'
          }
          aria-label={`Confirmar aprovação de ${candidateName}`}
        >
          {isLoading ? (
            <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
          ) : (
            'Sim'
          )}
        </button>
        <button
          onClick={handleCancel}
          disabled={isLoading}
          className={
            'inline-flex items-center px-2 py-0.5 text-micro font-medium rounded-md ' +
            'bg-lia-bg-primary text-lia-text-primary border border-lia-border-default hover:bg-lia-interactive-hover ' +
            'transition-colors duration-150'
          }
          aria-label="Cancelar aprovação"
        >
          Não
        </button>
      </div>
    )
  }

  return (
    <button
      data-testid="override-approve-btn"
      onClick={handleClick}
      disabled={isLoading || disabled}
      className={
        'inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium rounded-md ' +
        'bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover active:bg-lia-btn-primary-hover ' +
        'disabled:bg-lia-border-default disabled:text-lia-text-secondary disabled:cursor-not-allowed ' +
        'transition-colors duration-150 mt-1'
      }
      aria-label={`Aprovar ${candidateName} da fila de espera`}
    >
      <UserCheck className="w-3 h-3" />
      Aprovar da Fila
    </button>
  )
}
