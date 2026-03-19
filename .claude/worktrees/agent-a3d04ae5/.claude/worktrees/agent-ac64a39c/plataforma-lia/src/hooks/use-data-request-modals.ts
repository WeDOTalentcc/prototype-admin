"use client"

import { useState, useCallback } from 'react'
import type { DataRequestCandidate, DataBlockingCandidate, PendingField } from '@/components/modals'

interface DataRequestModalState {
  isOpen: boolean
  candidates: DataRequestCandidate[]
  jobTitle?: string
}

interface DataBlockingModalState {
  isOpen: boolean
  candidate: DataBlockingCandidate | null
  pendingFields: PendingField[]
  targetStage: string
  targetStageDisplayName: string
}

export function useDataRequestModals() {
  const [dataRequestModal, setDataRequestModal] = useState<DataRequestModalState>({
    isOpen: false,
    candidates: [],
    jobTitle: undefined
  })

  const [dataBlockingModal, setDataBlockingModal] = useState<DataBlockingModalState>({
    isOpen: false,
    candidate: null,
    pendingFields: [],
    targetStage: '',
    targetStageDisplayName: ''
  })

  const openDataRequestModal = useCallback((
    candidates: DataRequestCandidate[],
    jobTitle?: string
  ) => {
    setDataRequestModal({
      isOpen: true,
      candidates,
      jobTitle
    })
  }, [])

  const closeDataRequestModal = useCallback(() => {
    setDataRequestModal(prev => ({
      ...prev,
      isOpen: false
    }))
  }, [])

  const openDataBlockingModal = useCallback((
    candidate: DataBlockingCandidate,
    pendingFields: PendingField[],
    targetStage: string,
    targetStageDisplayName: string
  ) => {
    setDataBlockingModal({
      isOpen: true,
      candidate,
      pendingFields,
      targetStage,
      targetStageDisplayName
    })
  }, [])

  const closeDataBlockingModal = useCallback(() => {
    setDataBlockingModal(prev => ({
      ...prev,
      isOpen: false
    }))
  }, [])

  return {
    dataRequestModal,
    openDataRequestModal,
    closeDataRequestModal,
    dataBlockingModal,
    openDataBlockingModal,
    closeDataBlockingModal
  }
}
