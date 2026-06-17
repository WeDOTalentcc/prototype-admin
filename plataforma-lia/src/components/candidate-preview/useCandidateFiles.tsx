"use client"

import React from "react"
import { useState, useEffect, useCallback } from "react"
import { FileText, FileVideo, Award, File, Image } from "lucide-react"
import { formatRelativeTime } from "@/lib/format-utils"
import type { FileItem } from "@/components/candidate-preview/FilePreviewModal"
import { toast } from "sonner"
import { useCurrentCompany } from '@/hooks/company/use-current-company'

export { formatFileSize, formatRelativeTime } from "@/lib/format-utils"

export function getCategoryColor(fileType: string): { bg: string; text: string } {
  const colors: Record<string, { bg: string; text: string }> = {
    'cv': { bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
    'portfolio': { bg: 'var(--lia-border-subtle)', text: 'var(--lia-text-secondary)' },
    'video': { bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
    'certificate': { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)' },
    'document': { bg: 'var(--lia-bg-tertiary)', text: 'var(--lia-text-tertiary)' },
    'transcript': { bg: 'var(--lia-bg-tertiary)', text: 'var(--wedo-purple)' },
  }
  return colors[fileType] || colors['document']
}

export function getFileIcon(fileType: string, mimeType?: string) {
  if (fileType === 'cv') return <FileText className="w-3.5 h-3.5 text-lia-text-primary" />
  if (fileType === 'video' || mimeType?.startsWith('video/')) return <FileVideo className="w-3.5 h-3.5 text-status-error" />
  if (fileType === 'certificate') return <Award className="w-3.5 h-3.5 text-status-warning" />
  if (mimeType?.startsWith('image/')) return <Image className="w-3.5 h-3.5 text-status-success" />
  return <File className="w-3.5 h-3.5 text-lia-text-secondary" />
}

export function useCandidateFiles(candidate: Record<string, any>) {
  const { companyId } = useCurrentCompany()
  const [candidateFiles, setCandidateFiles] = useState<any[]>([])
  const [fileCategories, setFileCategories] = useState<any[]>([])
  const [isLoadingFiles, setIsLoadingFiles] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [previewType, setPreviewType] = useState<'pdf' | 'image' | 'video' | 'audio' | null>(null)
  const [expandedActivity, setExpandedActivity] = useState<string | null>(null)
  const fetchCandidateFiles = useCallback(async () => {
    if (!candidate?.id || !companyId) return

    setIsLoadingFiles(true)
    try {
      const url = `/api/backend-proxy/candidates/${candidate.id}/files?company_id=${encodeURIComponent(companyId)}`
      const response = await fetch(url)
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({})) as { error?: string }
        toast.error("Erro ao carregar arquivos", { description: errorData.error || "Não foi possível carregar os arquivos" })
        return
      }
      const data = await response.json()
      setCandidateFiles(data.attachments || [])
      setFileCategories(data.categories || [])
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      toast.error("Erro ao carregar arquivos", { description: message })
    } finally {
      setIsLoadingFiles(false)
    }
  }, [candidate?.id, companyId])

  useEffect(() => {
    if (candidate?.id && companyId) {
      fetchCandidateFiles()
    }
  }, [candidate?.id, companyId, fetchCandidateFiles])

  const handleFileUpload = async (files: File[]) => {
    if (!candidate?.id || !companyId || files.length === 0) return

    setIsUploading(true)
    setUploadProgress(0)

    let successCount = 0
    let errorCount = 0

    for (let i = 0; i < files.length; i++) {
      const file = files[i]

      if (file.size > 10 * 1024 * 1024) {
        toast.error("Arquivo muito grande", { description: `${file.name} excede o limite de 10MB` })
        errorCount++
        continue
      }

      const formData = new FormData()
      formData.append('file', file)
      formData.append('candidate_name', String(candidate.name || 'Candidato'))
      formData.append('uploaded_by', 'user')
      formData.append('uploaded_by_name', 'Recrutador')

      try {
        const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/files`, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({})) as { error?: string }
          errorCount++
          toast.error("Erro no upload", { description: errorData.error || `Erro ao enviar ${file.name}` })
          setUploadProgress(Math.round(((i + 1) / files.length) * 100))
          continue
        }

        const data = await response.json()

        if (data.success) {
          successCount++
        } else {
          errorCount++
          toast.error("Erro no upload", { description: data.error || `Erro ao enviar ${file.name}` })
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Erro desconhecido'
        errorCount++
        toast.error("Erro no upload", { description: message || `Erro ao enviar ${file.name}` })
      }

      setUploadProgress(Math.round(((i + 1) / files.length) * 100))
    }

    setIsUploading(false)
    setUploadProgress(0)

    if (successCount > 0) {
      toast.success("Upload concluído", { description: `${successCount} arquivo(s) enviado(s) com sucesso` })
      fetchCandidateFiles()
    }
  }

  const handleDeleteFile = async (attachmentId: string) => {
    if (!candidate?.id) return

    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/files/${attachmentId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({})) as { error?: string }
        toast.error("Erro", { description: errorData.error || "Não foi possível excluir o arquivo" })
        return
      }

      const data = await response.json()

      if (data.success) {
        toast.info("Arquivo excluído", { description: "O arquivo foi removido com sucesso" })
        fetchCandidateFiles()
      } else {
        toast.error("Erro", { description: "Não foi possível excluir o arquivo" })
      }
    } catch (error) {
      toast.error("Erro", { description: "Erro ao excluir arquivo" })
    }
  }

  const handleDownloadFile = (fileUrl: string, fileName: string) => {
    const downloadUrl = `/api/backend-proxy${fileUrl.startsWith('/api/v1') ? fileUrl.replace('/api/v1', '') : fileUrl}`
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fileName
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return {
    candidateFiles,
    fileCategories,
    isLoadingFiles,
    isUploading,
    uploadProgress,
    selectedCategory,
    setSelectedCategory,
    isDragging,
    setIsDragging,
    selectedFile,
    setSelectedFile,
    showPreview,
    setShowPreview,
    previewType,
    setPreviewType,
    expandedActivity,
    setExpandedActivity,
    handleFileUpload,
    handleDeleteFile,
    handleDownloadFile,
  }
}
