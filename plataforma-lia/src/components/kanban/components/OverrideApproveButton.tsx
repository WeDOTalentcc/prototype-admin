'use client'

import React, { useState, useEffect } from 'react'
import { UserCheck, Loader2 } from 'lucide-react'
import { useOverrideApprove } from '@/hooks/use-override-approve'
import { useToast } from '@/hooks/use-toast'

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
  const { toast } = useToast()

  useEffect(() => {
    if (error) {
      toast({
        title: 'Erro ao aprovar candidato',
        description: error,
        variant: 'destructive',
      })
    }
  }, [error, toast])

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
        <span className="text-micro text-gray-600 dark:text-gray-400">
          Aprovar {candidateName.split(' ')[0]}?
        </span>
        <button
          onClick={handleConfirm}
          disabled={isLoading || disabled}
          className={
            'inline-flex items-center gap-0.5 px-2 py-0.5 text-micro font-medium rounded-md ' +
            'bg-gray-900 text-white hover:bg-gray-800 active:bg-gray-700 ' +
            'dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 ' +
            'disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed ' +
            'transition-colors duration-150'
          }
          aria-label={`Confirmar aprovação de ${candidateName}`}
        >
          {isLoading ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            'Sim'
          )}
        </button>
        <button
          onClick={handleCancel}
          disabled={isLoading}
          className={
            'inline-flex items-center px-2 py-0.5 text-micro font-medium rounded-md ' +
            'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 ' +
            'dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700 ' +
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
      onClick={handleClick}
      disabled={isLoading || disabled}
      className={
        'inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium rounded-md ' +
        'bg-gray-900 text-white hover:bg-gray-800 active:bg-gray-700 ' +
        'dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 ' +
        'disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed ' +
        'transition-colors duration-150 mt-1'
      }
      aria-label={`Aprovar ${candidateName} da fila de espera`}
    >
      <UserCheck className="w-3 h-3" />
      Aprovar da Fila
    </button>
  )
}
