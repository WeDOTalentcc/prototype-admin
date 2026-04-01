"use client"

import React from "react"
import { useState, useEffect, useCallback } from "react"
import { FileText, FileVideo, Award, File, Image } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import type { FileItem } from "@/components/candidate-preview/FilePreviewModal"

export function formatFileSize(bytes: number): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export function formatRelativeTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'Agora'
  if (diffMins < 60) return `Há ${diffMins} min`
  if (diffHours < 24) return `Há ${diffHours}h`
  if (diffDays === 1) return 'Ontem'
  if (diffDays < 7) return `Há ${diffDays} dias`
  return date.toLocaleDateString('pt-BR')
}

export function getCategoryColor(fileType: string): { bg: string; text: string } {
  const colors: Record<string, { bg: string; text: string }> = {
    'cv': { bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
    'portfolio': { bg: 'var(--gray-200)', text: 'var(--gray-600)' },
    'video': { bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
    'certificate': { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)' },
    'document': { bg: 'var(--gray-100)', text: 'var(--gray-400)' },
    'transcript': { bg: 'var(--gray-100)', text: 'var(--wedo-purple)' },
  }
  return colors[fileType] || colors['document']
}


export function getFileIcon(fileType: string, mimeType?: string) {
  if (fileType === 'cv') return <FileText className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
  if (fileType === 'video' || mimeType?.startsWith('video/')) return <FileVideo className="w-3.5 h-3.5 text-status-error" />
  if (fileType === 'certificate') return <Award className="w-3.5 h-3.5 text-status-warning" />
  if (mimeType?.startsWith('image/')) return <Image className="w-3.5 h-3.5 text-status-success" />
  return <File className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
}

export function useCandidateFiles(candidate: Record<string, any>) {
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

  const { toast } = useToast()
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  const fetchCandidateFiles = useCallback(async () => {
    if (!candidate?.id) return

    setIsLoadingFiles(true)
    try {
      const url = `${BACKEND_URL}/api/v1/candidates/${candidate.id}/files?company_id=demo_company`
      const response = await fetch(url)
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({})) as { error?: string }
        toast({
          title: "Erro ao carregar arquivos",
          description: errorData.error || "Não foi possível carregar os arquivos",
          variant: "destructive"
        })
        return
      }
      const data = await response.json()
      setCandidateFiles(data.attachments || [])
      setFileCategories(data.categories || [])
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
      toast({
        title: "Erro ao carregar arquivos",
        description: message,
        variant: "destructive"
      })
    } finally {
      setIsLoadingFiles(false)
    }
  }, [candidate?.id, BACKEND_URL])

  useEffect(() => {
    if (candidate?.id) {
      fetchCandidateFiles()
    }
  }, [candidate?.id, fetchCandidateFiles])

  const handleFileUpload = async (files: File[]) => {
    if (!candidate?.id || files.length === 0) return

    setIsUploading(true)
    setUploadProgress(0)

    let successCount = 0
    let errorCount = 0

    for (let i = 0; i < files.length; i++) {
      const file = files[i]

      if (file.size > 10 * 1024 * 1024) {
        toast({
          title: "Arquivo muito grande",
          description: `${file.name} excede o limite de 10MB`,
          variant: "destructive"
        })
        errorCount++
        continue
      }

      const formData = new FormData()
      formData.append('file', file)
      // @ts-ignore TODO: fix type
      formData.append('candidate_name', candidate.name || 'Candidato')
      formData.append('company_id', 'demo_company')
      formData.append('uploaded_by', 'user')
      formData.append('uploaded_by_name', 'Recrutador')

      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/candidates/${candidate.id}/files`, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({})) as { error?: string }
          errorCount++
          toast({
            title: "Erro no upload",
            description: errorData.error || `Erro ao enviar ${file.name}`,
            variant: "destructive"
          })
          setUploadProgress(Math.round(((i + 1) / files.length) * 100))
          continue
        }

        const data = await response.json()

        if (data.success) {
          successCount++
        } else {
          errorCount++
          toast({
            title: "Erro no upload",
            description: data.error || `Erro ao enviar ${file.name}`,
            variant: "destructive"
          })
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Erro desconhecido'
        errorCount++
        toast({
          title: "Erro no upload",
          description: message || `Erro ao enviar ${file.name}`,
          variant: "destructive"
        })
      }

      setUploadProgress(Math.round(((i + 1) / files.length) * 100))
    }

    setIsUploading(false)
    setUploadProgress(0)

    if (successCount > 0) {
      toast({
        title: "Upload concluído",
        description: `${successCount} arquivo(s) enviado(s) com sucesso`
      })
      fetchCandidateFiles()
    }
  }

  const handleDeleteFile = async (attachmentId: string) => {
    if (!candidate?.id) return

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/candidates/${candidate.id}/files/${attachmentId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({})) as { error?: string }
        toast({
          title: "Erro",
          description: errorData.error || "Não foi possível excluir o arquivo",
          variant: "destructive"
        })
        return
      }

      const data = await response.json()

      if (data.success) {
        toast({
          title: "Arquivo excluído",
          description: "O arquivo foi removido com sucesso"
        })
        fetchCandidateFiles()
      } else {
        toast({
          title: "Erro",
          description: "Não foi possível excluir o arquivo",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Erro",
        description: "Erro ao excluir arquivo",
        variant: "destructive"
      })
    }
  }

  const handleDownloadFile = (fileUrl: string, fileName: string) => {
    const downloadUrl = `${BACKEND_URL}${fileUrl}`
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
