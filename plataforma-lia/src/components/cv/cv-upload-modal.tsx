"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React, { useState, useCallback, useRef } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  FileUp,
  Upload,
  FileText,
  X,
  AlertCircle,
  CheckCircle,
  Loader2,
  File,
} from "lucide-react"
import { cn } from "@/lib/utils"

const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
  'text/plain': ['.txt'],
}

import { MAX_FILE_SIZE } from '@/constants/upload'

interface CVUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onParsed: (data: ParsedCVResponse) => void
}

interface ParsedCV {
  full_name: string
  email?: string
  phone?: string
  linkedin?: string
  github?: string
  portfolio?: string
  location?: string
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

export interface ParsedCVResponse {
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

export function CVUploadModal({ isOpen, onClose, onParsed }: CVUploadModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('cv-upload', isOpen)

  const [activeTab, setActiveTab] = useState<"upload" | "text">("upload")
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [cvText, setCvText] = useState("")
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

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

  const handleRemoveFile = () => {
    setSelectedFile(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleUploadFile = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setError(null)
    setUploadProgress(10)

    try {
      const formData = new FormData()
      formData.append("file", selectedFile)

      setUploadProgress(30)

      const response = await fetch("/api/backend-proxy/cv-parser/upload", {
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
        onParsed(data)
        handleClose()
      } else {
        throw new Error(data.message || "Erro ao processar CV")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao processar CV")
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const handleParseText = async () => {
    if (cvText.trim().length < 50) {
      setError("O texto do CV deve ter pelo menos 50 caracteres.")
      return
    }

    setIsUploading(true)
    setError(null)
    setUploadProgress(20)

    try {
      const response = await fetch("/api/backend-proxy/cv-parser/parse-text", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: cvText,
          source: "manual_paste",
        }),
      })

      setUploadProgress(70)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || errorData.detail || "Erro ao processar texto")
      }

      const data: ParsedCVResponse = await response.json()
      setUploadProgress(100)

      if (data.success && data.parsed_cv) {
        onParsed(data)
        handleClose()
      } else {
        throw new Error(data.message || "Erro ao processar texto")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao processar texto")
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const handleClose = () => {
    setSelectedFile(null)
    setCvText("")
    setError(null)
    setIsUploading(false)
    setUploadProgress(0)
    setActiveTab("upload")
    onClose()
  }

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'pdf':
        return <FileText className="w-8 h-8 text-lia-text-primary" />
      case 'docx':
      case 'doc':
        return <FileText className="w-8 h-8 text-lia-text-primary" />
      default:
        return <File className="w-8 h-8 text-lia-text-primary" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-xl rounded-xl bg-lia-bg-primary dark:bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle">
        <DialogHeader className=" dark:border-lia-border-subtle pb-4">
          <DialogTitle className="flex items-center gap-2 text-lia-text-primary">
            <FileUp className="w-5 h-5 text-lia-text-secondary" />
            Upload de CV
          </DialogTitle>
          <DialogDescription className="text-lia-text-secondary">
            Envie um currículo para extração automática de dados com IA
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "upload" | "text")}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="upload" className="gap-2">
              <Upload className="w-4 h-4" />
              Arquivo
            </TabsTrigger>
            <TabsTrigger value="text" className="gap-2">
              <FileText className="w-4 h-4" />
              Colar Texto
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4 mt-4">
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
 "border-2 border-dashed rounded-md p-8 text-center cursor-pointer transition-colors",
                  isDragging
                    ? "border-lia-border-medium bg-lia-bg-secondary"
                    : "border-lia-border-default hover:border-lia-border-medium hover:bg-lia-bg-secondary"
                )}
              >
                <Upload className="w-10 h-10 mx-auto mb-3 text-lia-text-secondary" />
                <p className="text-sm font-medium text-lia-text-primary">
                  {isDragging ? "Solte o arquivo aqui" : "Arraste ou clique para selecionar"}
                </p>
                <p className="text-xs text-lia-text-primary mt-1">
                  PDF, DOCX, DOC ou TXT (máx. 5MB)
                </p>
              </div>
            ) : (
              <div className="border rounded-xl p-4">
                <div className="flex items-center gap-3">
                  {getFileIcon(selectedFile.name)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-lia-text-primary truncate">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-lia-text-primary">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleRemoveFile}
                    disabled={isUploading}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}

            {isUploading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-lia-text-secondary">
                  <span>Processando CV com IA...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
              </div>
            )}
          </TabsContent>

          <TabsContent value="text" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="cv-text">Cole o texto do currículo</Label>
              <Textarea
                id="cv-text"
                placeholder="Cole aqui o conteúdo do currículo..."
                value={cvText}
                onChange={(e) => setCvText(e.target.value)}
                rows={10}
                className="resize-none"
                disabled={isUploading}
              />
              <div className="flex justify-between text-xs text-lia-text-primary">
                <span>Mínimo 50 caracteres</span>
                <span className={cvText.length < 50 ? "text-lia-text-tertiary" : "text-lia-text-primary"}>
                  {cvText.length} caracteres
                </span>
              </div>
            </div>

            {isUploading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-lia-text-secondary">
                  <span>Extraindo dados com IA...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
              </div>
            )}
          </TabsContent>
        </Tabs>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-status-error/10 border border-status-error/30 rounded-xl">
            <AlertCircle className="w-4 h-4 text-status-error flex-shrink-0" />
            <p className="text-sm text-status-error">{error}</p>
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button variant="outline" onClick={handleClose} disabled={isUploading} className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse">
            Cancelar
          </Button>
          {activeTab === "upload" ? (
            <Button
              onClick={handleUploadFile}
              disabled={!selectedFile || isUploading}
              className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                  Processando...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Processar CV
                </>
              )}
            </Button>
          ) : (
            <Button
              onClick={handleParseText}
              disabled={cvText.trim().length < 50 || isUploading}
              className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                  Processando...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  Extrair Dados
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
