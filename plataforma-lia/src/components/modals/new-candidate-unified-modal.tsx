"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Checkbox } from "@/components/ui/checkbox"
import { cn } from "@/lib/utils"
import {
  User, Mail, Phone, Upload, FileText,
  X, Brain, CheckCircle, AlertCircle,
  Linkedin, Loader2, File, ExternalLink, Building, MapPin
} from "lucide-react"
import { duplicateDetectionService, type DuplicateCheckResult, type CandidateBasicInfo } from '@/services/duplicate-detection-service'
import { textStyles, buttonStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { useToast } from "@/hooks/use-toast"

const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'text/plain': ['.txt'],
}

const MAX_FILE_SIZE = 5 * 1024 * 1024

interface ParsedCV {
  full_name: string
  email?: string
  phone?: string
  linkedin?: string
  github?: string
  portfolio?: string
  location?: string
  current_title?: string
  seniority_level?: string
  summary?: string
  experiences: Array<{
    company: string
    title: string
    start_date?: string
    end_date?: string
    is_current: boolean
    description?: string
    location?: string
  }>
  education: Array<{
    institution: string
    degree?: string
    field_of_study?: string
    start_date?: string
    end_date?: string
    is_completed: boolean
    description?: string
  }>
  skills: string[]
  languages: string[]
  certifications: string[]
  raw_text: string
  file_name?: string
  file_type?: string
  file_size_bytes?: number
  confidence_score: number
  extraction_notes: string[]
  parsed_at: string
}

interface ParsedCVResponse {
  success: boolean
  message: string
  parsed_cv: ParsedCV | null
  duplicate_warning?: {
    message: string
    existing_candidate_id: string
    existing_candidate_name: string
    match_type: string
    similarity_score: number
  } | null
  candidate_id?: string | null
}

interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
}

interface NewCandidateUnifiedModalProps {
  isOpen: boolean
  onClose: () => void
  onCandidateAdded: (candidate: any) => void
  jobVacancies?: JobVacancy[]
  candidateLists?: Array<{ id: string; name: string; color?: string }>
  preSelectedListId?: string
  preSelectedListName?: string
  onGoToSearch?: () => void
  onOpenFullProfile?: (candidateId: string) => void
}

type Step = 'input' | 'duplicate-found' | 'processing' | 'success'
type InputTab = 'cv' | 'linkedin' | 'manual'

export function NewCandidateUnifiedModal({ 
  isOpen, 
  onClose, 
  onCandidateAdded,
  jobVacancies = [],
  candidateLists = [],
  preSelectedListId = "",
  preSelectedListName = "",
  onGoToSearch,
  onOpenFullProfile
}: NewCandidateUnifiedModalProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [currentStep, setCurrentStep] = useState<Step>('input')
  const [activeTab, setActiveTab] = useState<InputTab>('cv')
  
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [cvText, setCvText] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [isEnriching, setIsEnriching] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [parsedCV, setParsedCV] = useState<ParsedCV | null>(null)
  
  const [linkedinUrl, setLinkedinUrl] = useState("")
  
  const [manualData, setManualData] = useState({
    name: "",
    email: "",
    phone: "",
    linkedinUrl: ""
  })
  
  const [duplicateResult, setDuplicateResult] = useState<DuplicateCheckResult | null>(null)
  const [savedCandidateId, setSavedCandidateId] = useState<string>('')

  useEffect(() => {
    if (!isOpen) {
      resetModal()
    }
  }, [isOpen])

  const resetModal = () => {
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
  }

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
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    setError(null)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        return
      }
      setSelectedFile(file)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    const files = e.target.files
    if (files && files.length > 0) {
      const file = files[0]
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        return
      }
      setSelectedFile(file)
    }
  }

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    if (ext === 'pdf') return <FileText className="w-4 h-4 text-status-error" />
    if (['doc', 'docx'].includes(ext || '')) return <FileText className="w-4 h-4 text-wedo-cyan-dark" />
    return <File className="w-4 h-4 text-gray-500 dark:text-gray-400" />
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const enrichCandidate = async (candidateId: string, linkedinUrlToEnrich: string): Promise<boolean> => {
    try {
      setIsEnriching(true)
      const enrichResponse = await fetch(`/api/backend-proxy/candidates/${candidateId}/enrich`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          linkedin_url: linkedinUrlToEnrich,
          include_experiences: true,
          include_education: true,
          include_email_discovery: true
        })
      })

      if (!enrichResponse.ok) {
        return false
      }

      return true
    } catch (err) {
      return false
    } finally {
      setIsEnriching(false)
    }
  }

  const handleProcessCV = async (file: File): Promise<ParsedCV | null> => {
    setUploadProgress(10)

    try {
      const formData = new FormData()
      formData.append("file", file)

      setUploadProgress(30)

      const response = await fetch("/api/backend-proxy/cv/upload", {
        method: "POST",
        body: formData,
      })

      setUploadProgress(70)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || errorData.detail || "Erro ao processar CV")
      }

      const data: ParsedCVResponse = await response.json()
      setUploadProgress(100)

      if (data.success && data.parsed_cv) {
        return data.parsed_cv
      } else {
        throw new Error(data.message || "Erro ao processar CV")
      }
    } catch (err) {
      throw err
    }
  }

  const handleParseText = async (): Promise<ParsedCV | null> => {
    if (cvText.trim().length < 50) {
      throw new Error("O texto do CV deve ter pelo menos 50 caracteres.")
    }

    setUploadProgress(20)

    try {
      const response = await fetch("/api/backend-proxy/cv/parse-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: cvText, source: "manual_paste" }),
      })

      setUploadProgress(70)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || errorData.detail || "Erro ao processar texto")
      }

      const data: ParsedCVResponse = await response.json()
      setUploadProgress(100)

      if (data.success && data.parsed_cv) {
        return data.parsed_cv
      } else {
        throw new Error(data.message || "Erro ao processar texto")
      }
    } catch (err) {
      throw err
    }
  }

  const createCandidate = async (candidateData: any): Promise<string> => {
    const response = await fetch("/api/backend-proxy/candidates/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(candidateData),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || errorData.detail || "Erro ao criar candidato")
    }

    const result = await response.json()
    return result.id
  }

  const handleSubmitCV = async () => {
    setIsProcessing(true)
    setError(null)
    setCurrentStep('processing')

    try {
      let parsed: ParsedCV | null = null
      
      if (selectedFile) {
        parsed = await handleProcessCV(selectedFile)
      } else if (cvText.trim().length >= 50) {
        parsed = await handleParseText()
      } else {
        throw new Error("Selecione um arquivo ou cole o texto do CV")
      }

      if (!parsed) {
        throw new Error("Não foi possível extrair dados do CV")
      }

      setParsedCV(parsed)

      const duplicateCheck = await duplicateDetectionService.checkByParsedCV({
        full_name: parsed.full_name,
        email: parsed.email,
        phone: parsed.phone,
        linkedin: parsed.linkedin
      })

      if (duplicateCheck.found) {
        setDuplicateResult(duplicateCheck)
        setCurrentStep('duplicate-found')
        return
      }

      await createAndOpenCandidate(parsed, !!parsed.linkedin)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Erro ao processar CV"
      setError(errorMessage)
      toast({
        title: "Erro no processamento",
        description: errorMessage,
        variant: "destructive"
      })
      setCurrentStep('input')
    } finally {
      setIsProcessing(false)
      setUploadProgress(0)
    }
  }

  const handleSubmitLinkedin = async () => {
    if (!linkedinUrl.trim()) {
      setError("Cole a URL do LinkedIn")
      return
    }

    if (!linkedinUrl.includes('linkedin.com/in/')) {
      setError("URL inválida. Use o formato: linkedin.com/in/nome-do-usuario")
      return
    }

    setIsProcessing(true)
    setError(null)
    setCurrentStep('processing')

    try {
      const duplicateCheck = await duplicateDetectionService.checkDuplicate({
        linkedinUrl: linkedinUrl.trim()
      })

      if (duplicateCheck.found) {
        setDuplicateResult(duplicateCheck)
        setCurrentStep('duplicate-found')
        return
      }

      const candidateData = {
        name: "Importação LinkedIn",
        linkedin_url: linkedinUrl.trim(),
        source: "linkedin",
        auto_enrich: true
      }

      const candidateId = await createCandidate(candidateData)
      setSavedCandidateId(candidateId)
      
      onCandidateAdded({ id: candidateId, ...candidateData })

      toast({
        title: "Candidato cadastrado com sucesso!",
        description: "LIA irá buscar os dados do LinkedIn em segundo plano. Abrindo perfil...",
      })

      openFullProfile(candidateId)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Erro ao cadastrar via LinkedIn"
      setError(errorMessage)
      toast({
        title: "Erro no cadastro",
        description: errorMessage,
        variant: "destructive"
      })
      setCurrentStep('input')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSubmitManual = async () => {
    if (!manualData.name.trim()) {
      setError("O nome é obrigatório")
      return
    }

    if (!manualData.email.trim() && !manualData.phone.trim()) {
      setError("Informe pelo menos um contato (email ou telefone)")
      return
    }

    setIsProcessing(true)
    setError(null)
    setCurrentStep('processing')

    try {
      const duplicateCheck = await duplicateDetectionService.checkDuplicate({
        name: manualData.name.trim(),
        email: manualData.email.trim() || undefined,
        phone: manualData.phone.trim() || undefined,
        linkedinUrl: manualData.linkedinUrl.trim() || undefined
      })

      if (duplicateCheck.found) {
        setDuplicateResult(duplicateCheck)
        setCurrentStep('duplicate-found')
        return
      }

      const hasLinkedin = manualData.linkedinUrl.trim() && manualData.linkedinUrl.includes('linkedin.com/in/')
      const candidateData = {
        name: manualData.name.trim(),
        email: manualData.email.trim() || null,
        phone: manualData.phone.trim() || null,
        linkedin_url: manualData.linkedinUrl.trim() || null,
        source: "manual",
        auto_enrich: hasLinkedin
      }

      const candidateId = await createCandidate(candidateData)
      setSavedCandidateId(candidateId)
      
      onCandidateAdded({ id: candidateId, ...candidateData })

      if (hasLinkedin) {
        toast({
          title: "Candidato cadastrado com sucesso!",
          description: "LIA irá buscar os dados do LinkedIn em segundo plano. Abrindo perfil...",
        })
      } else {
        toast({
          title: "Candidato cadastrado com sucesso!",
          description: "Abrindo perfil completo...",
        })
      }

      openFullProfile(candidateId)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Erro ao cadastrar candidato"
      setError(errorMessage)
      toast({
        title: "Erro no cadastro",
        description: errorMessage,
        variant: "destructive"
      })
      setCurrentStep('input')
    } finally {
      setIsProcessing(false)
    }
  }

  const createAndOpenCandidate = async (parsed: ParsedCV, shouldEnrich: boolean = false) => {
    const languagesDict: Record<string, string> = {}
    if (parsed.languages && Array.isArray(parsed.languages)) {
      parsed.languages.forEach((lang: string) => {
        languagesDict[lang] = "intermediate"
      })
    }

    const candidateData = {
      name: parsed.full_name,
      email: parsed.email || null,
      phone: parsed.phone || null,
      current_title: parsed.current_title || parsed.experiences?.[0]?.title || null,
      current_company: parsed.experiences?.[0]?.company || null,
      location_city: parsed.location || null,
      linkedin_url: parsed.linkedin || null,
      github_url: parsed.github || null,
      portfolio_url: parsed.portfolio || null,
      technical_skills: parsed.skills || [],
      languages: languagesDict,
      certifications: parsed.certifications || [],
      seniority_level: parsed.seniority_level || null,
      notes: parsed.summary || null,
      source: "manual",
      auto_enrich: shouldEnrich && !!parsed.linkedin
    }

    const candidateId = await createCandidate(candidateData)
    setSavedCandidateId(candidateId)
    
    onCandidateAdded({ id: candidateId, ...candidateData })

    if (shouldEnrich && parsed.linkedin) {
      toast({
        title: "Candidato cadastrado com sucesso!",
        description: "LIA irá buscar os dados do LinkedIn em segundo plano. Abrindo perfil...",
      })
    } else {
      toast({
        title: "Candidato cadastrado com sucesso!",
        description: "Abrindo perfil completo...",
      })
    }

    openFullProfile(candidateId)
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
    setIsProcessing(true)
    setError(null)
    setCurrentStep('processing')

    try {
      if (activeTab === 'cv' && parsedCV) {
        await createAndOpenCandidate(parsedCV, !!parsedCV.linkedin)
      } else if (activeTab === 'linkedin') {
        const candidateData = {
          name: "Importação LinkedIn",
          linkedin_url: linkedinUrl.trim(),
          source: "linkedin",
          auto_enrich: true
        }
        const candidateId = await createCandidate(candidateData)
        onCandidateAdded({ id: candidateId, ...candidateData })
        
        toast({
          title: "Candidato cadastrado com sucesso!",
          description: "LIA irá buscar os dados do LinkedIn em segundo plano. Abrindo perfil...",
        })
        
        openFullProfile(candidateId)
      } else if (activeTab === 'manual') {
        const hasLinkedin = manualData.linkedinUrl.trim() && manualData.linkedinUrl.includes('linkedin.com/in/')
        const candidateData = {
          name: manualData.name.trim(),
          email: manualData.email.trim() || null,
          phone: manualData.phone.trim() || null,
          linkedin_url: manualData.linkedinUrl.trim() || null,
          source: "manual",
          auto_enrich: hasLinkedin
        }
        const candidateId = await createCandidate(candidateData)
        onCandidateAdded({ id: candidateId, ...candidateData })
        
        if (hasLinkedin) {
          toast({
            title: "Candidato cadastrado com sucesso!",
            description: "LIA irá buscar os dados do LinkedIn em segundo plano. Abrindo perfil...",
          })
        } else {
          toast({
            title: "Candidato cadastrado com sucesso!",
            description: "Abrindo perfil completo...",
          })
        }
        
        openFullProfile(candidateId)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Erro ao cadastrar candidato"
      setError(errorMessage)
      toast({
        title: "Erro no cadastro",
        description: errorMessage,
        variant: "destructive"
      })
      setCurrentStep('input')
    } finally {
      setIsProcessing(false)
    }
  }

  const canSubmitCV = selectedFile || cvText.trim().length >= 50
  const canSubmitLinkedin = linkedinUrl.trim().includes('linkedin.com/in/')
  const canSubmitManual = manualData.name.trim() && (manualData.email.trim() || manualData.phone.trim())


  const renderInputStep = () => (
    <div className="space-y-4">
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => { setActiveTab('cv'); setError(null) }}
          className={cn(
            "flex-1 py-2.5 text-xs font-medium transition-colors relative",
            activeTab === 'cv'
              ? "text-gray-900 dark:text-gray-100"
              : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          )}
        >
          <div className="flex items-center justify-center gap-1.5">
            <FileText className="w-3.5 h-3.5" />
            CV
          </div>
          {activeTab === 'cv' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-900 dark:bg-gray-100" />
          )}
        </button>
        <button
          onClick={() => { setActiveTab('linkedin'); setError(null) }}
          className={cn(
            "flex-1 py-2.5 text-xs font-medium transition-colors relative",
            activeTab === 'linkedin'
              ? "text-gray-900 dark:text-gray-100"
              : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          )}
        >
          <div className="flex items-center justify-center gap-1.5">
            <Linkedin className="w-3.5 h-3.5" />
            LinkedIn
          </div>
          {activeTab === 'linkedin' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-900 dark:bg-gray-100" />
          )}
        </button>
        <button
          onClick={() => { setActiveTab('manual'); setError(null) }}
          className={cn(
            "flex-1 py-2.5 text-xs font-medium transition-colors relative",
            activeTab === 'manual'
              ? "text-gray-900 dark:text-gray-100"
              : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          )}
        >
          <div className="flex items-center justify-center gap-1.5">
            <User className="w-3.5 h-3.5" />
            Manual
          </div>
          {activeTab === 'manual' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-900 dark:bg-gray-100" />
          )}
        </button>
      </div>

      {activeTab === 'cv' && (
        <div className="space-y-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            onChange={handleFileSelect}
            className="hidden"
            id="cv-file-input"
          />

          {!selectedFile ? (
            <div
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition-all",
                isDragging
                  ? "border-gray-900 bg-gray-100 dark:border-gray-100 dark:bg-gray-800"
                  : "border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800"
              )}
            >
              <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-3">
                <Upload className={cn("w-5 h-5", isDragging ? "text-gray-900 dark:text-gray-100" : "text-gray-500")} />
              </div>
              <p className="text-xs font-medium text-gray-800 dark:text-gray-200">
                {isDragging ? "Solte o arquivo aqui" : "Arraste ou clique para selecionar"}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                PDF, DOCX, DOC ou TXT (máx. 5MB)
              </p>
            </div>
          ) : (
            <div className="border border-gray-200 dark:border-gray-700 rounded-md p-3">
              <div className="flex items-center gap-2">
                {getFileIcon(selectedFile.name)}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => {
                    setSelectedFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ""
                  }}
                >
                  <X className="w-3 h-3" />
                </Button>
              </div>
            </div>
          )}

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-200 dark:border-gray-700" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white dark:bg-gray-900 px-2 text-gray-500 dark:text-gray-400">ou cole o texto</span>
            </div>
          </div>

          <Textarea
            placeholder="Cole aqui o conteúdo do currículo..."
            value={cvText}
            onChange={(e) => setCvText(e.target.value)}
            rows={4}
            className="resize-none text-xs"
          />
          <div className="flex justify-between items-center">
            <span className={cn(
              "text-xs",
              cvText.length < 50 ? "text-gray-500" : "text-status-success"
            )}>
              {cvText.length} caracteres (mín. 50)
            </span>
          </div>


          <Button
            onClick={handleSubmitCV}
            disabled={!canSubmitCV || isProcessing}
            className="w-full h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Processando...
              </>
            ) : (
              <>
                <Brain className="w-3.5 h-3.5 mr-1.5 text-wedo-cyan" />
                Cadastrar com CV
              </>
            )}
          </Button>
        </div>
      )}

      {activeTab === 'linkedin' && (
        <div className="space-y-4">
          <div className="text-center py-2">
            <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
              <Linkedin className="w-6 h-6 text-gray-600" />
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Cole a URL do perfil do LinkedIn do candidato
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="linkedin-url" className="text-xs font-sans">URL do LinkedIn</Label>
            <Input
              id="linkedin-url"
              placeholder="https://linkedin.com/in/nome-do-usuario"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              className="h-9 text-xs font-sans"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 font-sans">
              Ex: linkedin.com/in/joao-silva
            </p>
          </div>

          <div className="flex items-center gap-2 p-2.5 bg-gray-50 dark:bg-gray-800/50 border border-gray-300 dark:border-gray-600 rounded-md">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            <p className="text-xs text-gray-600 dark:text-gray-400 font-sans">
              A LIA irá buscar os dados do candidato
            </p>
          </div>

          <Button
            onClick={handleSubmitLinkedin}
            disabled={!canSubmitLinkedin || isProcessing}
            className="w-full h-9 text-xs bg-gray-900 hover:bg-gray-950 text-white"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Cadastrando...
              </>
            ) : (
              <>
                <Linkedin className="w-3.5 h-3.5 mr-1.5" />
                Cadastrar via LinkedIn
              </>
            )}
          </Button>
        </div>
      )}

      {activeTab === 'manual' && (
        <div className="space-y-4">
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="manual-name" className="text-xs">Nome Completo *</Label>
              <div className="relative">
                <User className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                <Input
                  id="manual-name"
                  placeholder="João Silva"
                  value={manualData.name}
                  onChange={(e) => setManualData(prev => ({ ...prev, name: e.target.value }))}
                  className="pl-8 h-9 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="manual-email" className="text-xs">E-mail</Label>
              <div className="relative">
                <Mail className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                <Input
                  id="manual-email"
                  type="email"
                  placeholder="joao.silva@email.com"
                  value={manualData.email}
                  onChange={(e) => setManualData(prev => ({ ...prev, email: e.target.value }))}
                  className="pl-8 h-9 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="manual-phone" className="text-xs">Telefone</Label>
              <div className="relative">
                <Phone className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                <Input
                  id="manual-phone"
                  placeholder="(11) 99999-9999"
                  value={manualData.phone}
                  onChange={(e) => setManualData(prev => ({ ...prev, phone: e.target.value }))}
                  className="pl-8 h-9 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="manual-linkedin" className="text-xs font-sans">LinkedIn (opcional)</Label>
              <div className="relative">
                <Linkedin className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                <Input
                  id="manual-linkedin"
                  placeholder="linkedin.com/in/joao-silva"
                  value={manualData.linkedinUrl}
                  onChange={(e) => setManualData(prev => ({ ...prev, linkedinUrl: e.target.value }))}
                  className="pl-8 h-9 text-xs font-sans"
                />
              </div>
              {manualData.linkedinUrl.includes('linkedin.com/in/') && (
                <p className="text-micro text-gray-600 dark:text-gray-400 flex items-center gap-1 font-sans">
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  A LIA irá buscar os dados do candidato
                </p>
              )}
            </div>

            <p className="text-xs text-gray-500 dark:text-gray-400">
              * Informe pelo menos um contato (email ou telefone)
            </p>
          </div>

          <Button
            onClick={handleSubmitManual}
            disabled={!canSubmitManual || isProcessing}
            className="w-full h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Cadastrando...
              </>
            ) : (
              <>
                <User className="w-3.5 h-3.5 mr-1.5" />
                Cadastrar Candidato
              </>
            )}
          </Button>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-2.5 bg-status-error/10 border border-status-error/30 rounded-md">
          <AlertCircle className="w-4 h-4 text-status-error flex-shrink-0" />
          <p className="text-xs text-status-error">{error}</p>
        </div>
      )}
    </div>
  )

  const renderDuplicateFound = () => (
    <div className="space-y-4">
      <div className="text-center">
        <div className="w-12 h-12 rounded-full bg-status-warning/15 dark:bg-status-warning/30 flex items-center justify-center mx-auto mb-3">
          <AlertCircle className="w-6 h-6 text-status-warning" />
        </div>
        <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
          Candidato já existe
        </h3>
        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
          {duplicateResult?.message}
        </p>
      </div>

      {duplicateResult?.candidate && (
        <Card className="border-status-warning/30 dark:border-status-warning/30 bg-status-warning/10/50 dark:bg-status-warning/20 rounded-md">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-gray-600 dark:bg-gray-500 flex items-center justify-center text-white text-xs font-medium flex-shrink-0">
                {duplicateResult.candidate.name?.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase() || '?'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  {duplicateResult.candidate.name}
                </p>
                {duplicateResult.candidate.current_title && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                    {duplicateResult.candidate.current_title}
                  </p>
                )}
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  {duplicateResult.candidate.current_company && (
                    <Badge variant="outline" className="text-micro py-0 px-1.5">
                      <Building className="w-2.5 h-2.5 mr-1" />
                      {duplicateResult.candidate.current_company}
                    </Badge>
                  )}
                  {duplicateResult.candidate.location_city && (
                    <Badge variant="outline" className="text-micro py-0 px-1.5">
                      <MapPin className="w-2.5 h-2.5 mr-1" />
                      {duplicateResult.candidate.location_city}
                    </Badge>
                  )}
                </div>
                {duplicateResult.matchType && (
                  <p className="text-micro text-status-warning mt-2">
                    Encontrado por: {
                      duplicateResult.matchType === 'email' ? 'E-mail' :
                      duplicateResult.matchType === 'phone' ? 'Telefone' :
                      duplicateResult.matchType === 'linkedin' ? 'LinkedIn' :
                      duplicateResult.matchType === 'name_similarity' ? 'Nome similar' : 
                      duplicateResult.matchType
                    }
                    {duplicateResult.confidence < 1 && ` (${Math.round(duplicateResult.confidence * 100)}% similar)`}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col gap-2">
        <Button
          onClick={handleOpenExistingCandidate}
          className="w-full h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
        >
          <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
          Abrir Perfil Existente
        </Button>
        <Button
          onClick={handleCreateAnyway}
          variant="outline"
          className="w-full h-9 text-xs"
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
              Cadastrando...
            </>
          ) : (
            "Cadastrar Mesmo Assim"
          )}
        </Button>
        <Button
          onClick={() => { setCurrentStep('input'); setDuplicateResult(null) }}
          variant="ghost"
          className="w-full h-9 text-xs text-gray-500"
        >
          Voltar
        </Button>
      </div>
    </div>
  )

  const renderProcessing = () => (
    <div className="py-8 text-center">
      <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
        {isEnriching ? (
          <Brain className="w-6 h-6 text-wedo-cyan animate-pulse" />
        ) : (
          <Loader2 className="w-6 h-6 text-gray-600 dark:text-gray-400 animate-spin" />
        )}
      </div>
      <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-2">
        {isEnriching ? 'Enriquecendo perfil...' : 'Processando...'}
      </h3>
      <p className="text-xs text-gray-600 dark:text-gray-400">
        {isEnriching 
          ? 'Buscando dados adicionais via LinkedIn...'
          : activeTab === 'cv' 
            ? 'Extraindo dados do CV com IA...' 
            : 'Verificando e cadastrando candidato...'
        }
      </p>
      {uploadProgress > 0 && !isEnriching && (
        <Progress value={uploadProgress} className="max-w-sidebar-content mx-auto h-1.5 mt-4" />
      )}
    </div>
  )

  const renderSuccess = () => (
    <div className="py-8 text-center">
      <div className="w-12 h-12 rounded-full bg-status-success/15 dark:bg-status-success/30 flex items-center justify-center mx-auto mb-4">
        <CheckCircle className="w-6 h-6 text-status-success" />
      </div>
      <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-2">
        Candidato cadastrado!
      </h3>
      <p className="text-xs text-gray-600 dark:text-gray-400">
        Abrindo perfil completo...
      </p>
    </div>
  )

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md p-0 gap-0 overflow-hidden bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700">
        <DialogHeader className="p-4 pb-0">
          <DialogTitle className="text-base font-semibold text-gray-950 dark:text-gray-50 font-sans">
            Novo Candidato
          </DialogTitle>
          <DialogDescription className="text-xs text-gray-500 font-sans">
            Cadastre um candidato usando CV, LinkedIn ou manualmente
          </DialogDescription>
        </DialogHeader>

        <div className="p-4">
          {currentStep === 'input' && renderInputStep()}
          {currentStep === 'duplicate-found' && renderDuplicateFound()}
          {currentStep === 'processing' && renderProcessing()}
          {currentStep === 'success' && renderSuccess()}
        </div>
      </DialogContent>
    </Dialog>
  )
}
