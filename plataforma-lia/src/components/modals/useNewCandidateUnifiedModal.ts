"use client"

import { useState, useCallback, useEffect } from "react"
import { useRouter } from "next/navigation"
import type { DuplicateCheckResult } from '@/services/duplicate-detection-service'
import {
  ACCEPTED_FILE_TYPES,
  MAX_FILE_SIZE,
  type ParsedCV,
  type Step,
  type InputTab,
  type ManualData,
  type UseNewCandidateModalReturn,
} from "./new-candidate-unified-types"
import {
  processCV,
  parseText,
  createCandidateAPI,
  buildCandidateDataFromParsed,
  checkDuplicateByParsedCV,
  checkDuplicateByLinkedin,
  checkDuplicateByManual,
  buildLinkedinCandidateData,
  buildManualCandidateData,
  showSuccessToast,
} from "./new-candidate-unified-actions"

interface UseNewCandidateUnifiedModalOptions {
  isOpen: boolean
  onClose: () => void
  onCandidateAdded: (candidate: Record<string, unknown>) => void
  onOpenFullProfile?: (candidateId: string) => void
}

export function useNewCandidateUnifiedModal({
  isOpen,
  onClose,
  onCandidateAdded,
  onOpenFullProfile,
}: UseNewCandidateUnifiedModalOptions): UseNewCandidateModalReturn {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState<Step>('input')
  const [activeTab, setActiveTab] = useState<InputTab>('cv')

  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [cvText, setCvText] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [isEnriching, setIsEnriching] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const [parsedCV, setParsedCV] = useState<ParsedCV | null>(null)
  const [linkedinUrl, setLinkedinUrl] = useState("")
  const [manualData, setManualData] = useState<ManualData>({
    name: "", email: "", phone: "", linkedinUrl: ""
  })

  const [duplicateResult, setDuplicateResult] = useState<DuplicateCheckResult | null>(null)
  const [savedCandidateId, setSavedCandidateId] = useState<string>('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!isOpen) {
      setCurrentStep('input')
      setActiveTab('cv')
      setParsedCV(null)
      setDuplicateResult(null)
      setSelectedFile(null)
      setCvText("")
      setLinkedinUrl("")
      setManualData({ name: "", email: "", phone: "", linkedinUrl: "" })
      setIsProcessing(false)
      setIsEnriching(false)
      setUploadProgress(0)
      setError(null)
      setSavedCandidateId('')
      setFieldErrors({})
    }
  }, [isOpen])

  const validateFile = (file: File): string | null => {
    const acceptedMimeTypes = Object.keys(ACCEPTED_FILE_TYPES)
    if (!acceptedMimeTypes.includes(file.type)) {
      const extension = file.name.split('.').pop()?.toLowerCase()
      const validExtensions = ['pdf', 'docx', 'doc', 'txt']
      if (!extension || !validExtensions.includes(extension)) {
        return "Formato de arquivo não suportado. Use PDF, DOCX, DOC ou TXT."
      }
    }
    if (file.size > MAX_FILE_SIZE) {
      return "Arquivo muito grande. O tamanho máximo é 5MB."
    }
    return null
  }

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false); setError(null)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      const validationError = validateFile(file)
      if (validationError) { setError(validationError); return }
      setSelectedFile(file)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    const files = e.target.files
    if (files && files.length > 0) {
      const file = files[0]
      const validationError = validateFile(file)
      if (validationError) { setError(validationError); return }
      setSelectedFile(file)
    }
  }

  const openFullProfile = (candidateId: string) => {
    setCurrentStep('success')
    setTimeout(() => {
      if (onOpenFullProfile) {
        onOpenFullProfile(candidateId)
      } else {
        router.push(`/funil-de-talentos/candidato/${candidateId}`)
      }
      onClose()
    }, 800)
  }

  const createAndOpen = async (parsed: ParsedCV, shouldEnrich: boolean = false) => {
    const candidateData = buildCandidateDataFromParsed(parsed, shouldEnrich)
    const candidateId = await createCandidateAPI(candidateData)
    setSavedCandidateId(candidateId)
    onCandidateAdded({ id: candidateId, ...candidateData })
    showSuccessToast(shouldEnrich && !!parsed.linkedin)
    openFullProfile(candidateId)
  }

  const handleSubmitCV = async () => {
    setIsProcessing(true); setError(null); setCurrentStep('processing')
    try {
      let parsed: ParsedCV | null = null
      if (selectedFile) {
        parsed = await processCV(selectedFile, setUploadProgress)
      } else if (cvText.trim().length >= 50) {
        parsed = await parseText(cvText, setUploadProgress)
      } else {
        throw new Error("Selecione um arquivo ou cole o texto do CV")
      }
      if (!parsed) throw new Error("Não foi possível extrair dados do CV")
      setParsedCV(parsed)
      const dup = await checkDuplicateByParsedCV(parsed)
      if (dup.found) { setDuplicateResult(dup); setCurrentStep('duplicate-found'); return }
      await createAndOpen(parsed, !!parsed.linkedin)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao processar CV"
      setError(msg); setCurrentStep('input')
    } finally {
      setIsProcessing(false); setUploadProgress(0)
    }
  }

  const handleSubmitLinkedin = async () => {
    setFieldErrors({})
    if (!linkedinUrl.trim()) {
      setFieldErrors({ linkedinUrl: "Cole a URL do LinkedIn" }); return
    }
    if (!linkedinUrl.includes('linkedin.com/in/')) {
      setFieldErrors({ linkedinUrl: "URL inválida. Use o formato: linkedin.com/in/nome-do-usuario" }); return
    }
    setIsProcessing(true); setError(null); setCurrentStep('processing')
    try {
      const dup = await checkDuplicateByLinkedin(linkedinUrl)
      if (dup.found) { setDuplicateResult(dup); setCurrentStep('duplicate-found'); return }
      const candidateData = buildLinkedinCandidateData(linkedinUrl)
      const candidateId = await createCandidateAPI(candidateData)
      setSavedCandidateId(candidateId)
      onCandidateAdded({ id: candidateId, ...candidateData })
      showSuccessToast(true)
      openFullProfile(candidateId)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao cadastrar via LinkedIn"
      setError(msg); setCurrentStep('input')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSubmitManual = async () => {
    const errors: Record<string, string> = {}
    if (!manualData.name.trim()) {
      errors.name = "O nome é obrigatório"
    }
    if (!manualData.email.trim() && !manualData.phone.trim()) {
      errors.contact = "Informe pelo menos um contato (email ou telefone)"
    }
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors); return
    }
    setFieldErrors({})
    setIsProcessing(true); setError(null); setCurrentStep('processing')
    try {
      const dup = await checkDuplicateByManual(manualData)
      if (dup.found) { setDuplicateResult(dup); setCurrentStep('duplicate-found'); return }
      const { data: candidateData, hasLinkedin } = buildManualCandidateData(manualData)
      const candidateId = await createCandidateAPI(candidateData)
      setSavedCandidateId(candidateId)
      onCandidateAdded({ id: candidateId, ...candidateData })
      showSuccessToast(hasLinkedin)
      openFullProfile(candidateId)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao cadastrar candidato"
      setError(msg); setCurrentStep('input')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleOpenExistingCandidate = () => {
    if (duplicateResult?.candidate?.id) {
      if (onOpenFullProfile) {
        onOpenFullProfile(duplicateResult.candidate.id)
      } else {
        router.push(`/funil-de-talentos/candidato/${duplicateResult.candidate.id}`)
      }
      onClose()
    }
  }

  const handleCreateAnyway = async () => {
    setIsProcessing(true); setError(null); setCurrentStep('processing')
    try {
      if (activeTab === 'cv' && parsedCV) {
        await createAndOpen(parsedCV, !!parsedCV.linkedin)
      } else if (activeTab === 'linkedin') {
        const candidateData = buildLinkedinCandidateData(linkedinUrl)
        const candidateId = await createCandidateAPI(candidateData)
        onCandidateAdded({ id: candidateId, ...candidateData })
        showSuccessToast(true)
        openFullProfile(candidateId)
      } else if (activeTab === 'manual') {
        const { data: candidateData, hasLinkedin } = buildManualCandidateData(manualData)
        const candidateId = await createCandidateAPI(candidateData)
        onCandidateAdded({ id: candidateId, ...candidateData })
        showSuccessToast(hasLinkedin)
        openFullProfile(candidateId)
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Erro ao cadastrar candidato"
      setError(msg); setCurrentStep('input')
    } finally {
      setIsProcessing(false)
    }
  }

  return {
    currentStep, setCurrentStep,
    activeTab, setActiveTab,
    isDragging,
    selectedFile, setSelectedFile,
    cvText, setCvText,
    isProcessing, isEnriching,
    uploadProgress,
    error, setError,
    fieldErrors, setFieldErrors,
    parsedCV,
    linkedinUrl, setLinkedinUrl,
    manualData, setManualData,
    duplicateResult, setDuplicateResult,
    savedCandidateId,
    canSubmitCV: !!(selectedFile || cvText.trim().length >= 50),
    canSubmitLinkedin: linkedinUrl.trim().includes('linkedin.com/in/'),
    canSubmitManual: !!(manualData.name.trim() && (manualData.email.trim() || manualData.phone.trim())),
    handleDragEnter, handleDragLeave, handleDragOver, handleDrop,
    handleFileSelect,
    handleSubmitCV, handleSubmitLinkedin, handleSubmitManual,
    handleOpenExistingCandidate, handleCreateAnyway,
  }
}
