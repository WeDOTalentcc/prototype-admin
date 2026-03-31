// @ts-nocheck
"use client"

import { useState, useEffect, useCallback } from "react"
import { useToast } from "@/hooks/use-toast"
import { textStyles } from "@/lib/design-tokens"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  FileText, Plus, Upload, Download, Eye, Play, Tag, X,
  File, FileVideo, Image, Video, Mic, Award, ChevronDown
} from "lucide-react"
import { FilePreviewModal, type FileItem } from "@/components/candidate-preview/FilePreviewModal"

interface CandidateFilesTabProps {
  candidate: Record<string, unknown>
}

export function CandidateFilesTab({ candidate }: CandidateFilesTabProps) {
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
      const message = error instanceof Error ? error.message : 'Erro desconhecido'
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

  const formatFileSize = (bytes: number): string => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const formatRelativeTime = (dateStr: string): string => {
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

  const getFileIcon = (fileType: string, mimeType?: string) => {
    if (fileType === 'cv') return <FileText className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
    if (fileType === 'video' || mimeType?.startsWith('video/')) return <FileVideo className="w-3.5 h-3.5 text-status-error" />
    if (fileType === 'certificate') return <Award className="w-3.5 h-3.5 text-status-warning" />
    if (mimeType?.startsWith('image/')) return <Image className="w-3.5 h-3.5 text-status-success" />
    return <File className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
  }

  const getCategoryColor = (fileType: string) => {
    const colors: Record<string, { bg: string, text: string }> = {
      'cv': { bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
      'portfolio': { bg: 'var(--gray-200)', text: 'var(--gray-600)' },
      'video': { bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
      'certificate': { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)' },
      'document': { bg: 'var(--gray-100)', text: 'var(--gray-400)' },
      'transcript': { bg: 'var(--gray-100)', text: 'var(--wedo-purple)' },
    }
    return colors[fileType] || colors['document']
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header com botão de adicionar */}
      <div className="p-3 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-primary">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
            Arquivos e Documentos
            <Badge className="text-xs px-1 py-0">{candidateFiles.length}</Badge>
            {isLoadingFiles && (
              <div className="animate-spin motion-reduce:animate-none rounded-full h-3 w-3 border border-gray-400 border-t-gray-700"></div>
            )}
          </h4>
          <Button
            size="sm"
            className="gap-1 px-2 py-1 text-xs h-6 bg-gray-100 hover:bg-gray-200 text-lia-text-secondary dark:text-lia-text-secondary border border-lia-border-subtle dark:border-lia-border-subtle"
            onClick={() => {
              const input = document.createElement('input')
              input.type = 'file'
              input.multiple = true
              input.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov'
              input.onchange = (e) => {
                const files = Array.from((e.target as HTMLInputElement).files || [])
                handleFileUpload(files)
              }
              input.click()
            }}
            disabled={isUploading}
          >
            <Plus className="w-3 h-3" />
            {isUploading ? 'Enviando...' : 'Adicionar Arquivo'}
          </Button>
        </div>

        {/* Categorias automáticas da LIA */}
        <div className="flex gap-1 flex-wrap">
          <Badge
            variant="outline"
            className={`text-xs px-1.5 py-0 cursor-pointer hover:bg-gray-100 ${!selectedCategory ? 'bg-gray-100' : ''}`}
            onClick={() => setSelectedCategory(null)}
          >
            📁 Todos ({candidateFiles.length})
          </Badge>
          {fileCategories.filter(c => c.count > 0).map((cat) => (
            <Badge
              key={cat.category}
              variant="outline"
              className={`text-xs px-1.5 py-0 cursor-pointer hover:bg-gray-100 ${selectedCategory === cat.category ? 'bg-gray-100' : ''}`}
              onClick={() => setSelectedCategory(selectedCategory === cat.category ? null : cat.category)}
            >
              {cat.icon} {cat.label} ({cat.count})
            </Badge>
          ))}
        </div>
      </div>

      {/* Lista de Arquivos */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {/* Drag and Drop Area */}
        <div
          className={`border-2 border-dashed rounded-md p-4 text-center transition-colors motion-reduce:transition-none cursor-pointer group ${
 isDragging
              ? 'border-gray-400 bg-gray-100'
              : 'border-lia-border-default hover:border-gray-400'
          }`}
          onDragOver={(e) => {
            e.preventDefault()
            setIsDragging(true)
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setIsDragging(false)
            const files = Array.from(e.dataTransfer.files)
            handleFileUpload(files)
          }}
          onClick={() => {
            if (isUploading) return
            const input = document.createElement('input')
            input.type = 'file'
            input.multiple = true
            input.accept = '.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov'
            input.onchange = (e) => {
              const files = Array.from((e.target as HTMLInputElement).files || [])
              handleFileUpload(files)
            }
            input.click()
          }}
        >
          <div className="flex flex-col items-center">
            {isUploading ? (
              <>
                <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center mb-2">
                  <div className="animate-spin motion-reduce:animate-none rounded-full h-5 w-5 border-2 border-gray-400 border-t-gray-700"></div>
                </div>
                <p className="text-xs text-lia-text-primary dark:text-lia-text-primary font-medium mb-1">
                  Enviando... {uploadProgress}%
                </p>
                <div className="w-32 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gray-600 rounded-full transition-[width,height] duration-300"
                    style={{width: `${uploadProgress}%`}}
                  />
                </div>
              </>
            ) : (
              <>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 transition-colors motion-reduce:transition-none ${
 isDragging
                    ? 'bg-gray-200'
                    : 'bg-gray-100 group-hover:bg-gray-200'
                }`}>
                  <Upload className={`w-5 h-5 ${isDragging ? 'text-lia-text-secondary' : 'text-lia-text-secondary dark:text-lia-text-tertiary group-hover:text-lia-text-secondary'}`} />
                </div>
                <p className={`${textStyles.bodySmall} mb-1`}>
                  {isDragging ? 'Solte os arquivos aqui' : 'Arraste arquivos ou clique para selecionar'}
                </p>
                <p className={textStyles.bodySmall}>
                  PDF, DOC, DOCX, JPG, PNG, MP4 • Máx 10MB
                </p>
              </>
            )}
          </div>
        </div>

        {/* Real files from API */}
        {candidateFiles
          .filter(file => !selectedCategory || file.file_type === selectedCategory)
          .map((file) => {
            const colors = getCategoryColor(file.file_type)
            return (
              <div key={file.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
                <div className="p-2.5">
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
                      {getFileIcon(file.file_type, file.mime_type)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className={`${textStyles.bodySmall} font-medium truncate`}>
                            {file.file_name}
                          </h5>
                          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                            <span className={textStyles.bodySmall}>
                              {formatFileSize(file.file_size)} • {file.file_name.split('.').pop()?.toUpperCase()}
                            </span>
                            <span className={textStyles.bodySmall}>
                              {formatRelativeTime(file.created_at)}
                            </span>
                            <Badge
                              className="text-xs px-1 py-0 h-3.5"
                              style={{backgroundColor: colors.bg, color: colors.text}}
                            >
                              <Tag className="w-2.5 h-2.5 mr-0.5" />
                              {file.file_type === 'cv' ? 'Currículo' :
                               file.file_type === 'portfolio' ? 'Portfólio' :
                               file.file_type === 'video' ? 'Vídeo' :
                               file.file_type === 'certificate' ? 'Certificado' :
                               file.file_type === 'transcript' ? 'Transcrição' :
                               'Documento'}
                            </Badge>
                          </div>
                          {file.description && (
                            <p className={`${textStyles.bodySmall} mt-1 truncate`}>
                              {file.description}
                            </p>
                          )}
                        </div>

                        <div className="flex items-center gap-1.5">
                          <Button
                            size="sm"
                            variant="ghost"
                            className="p-1 h-6 w-6"
                            onClick={() => handleDownloadFile(file.file_url, file.file_name)}
                            title="Baixar arquivo"
                          >
                            <Download className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="p-1 h-6 w-6 text-status-error hover:text-status-error hover:bg-status-error/10"
                            onClick={() => handleDeleteFile(file.id)}
                            title="Excluir arquivo"
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}

        {/* Empty state when no files */}
        {candidateFiles.length === 0 && !isLoadingFiles && (
          <div className="text-center py-6 text-lia-text-tertiary dark:text-lia-text-tertiary">
            <FileText className="w-8 h-8 mx-auto mb-2 lia-text-muted" />
            <p className="text-xs">Nenhum arquivo enviado</p>
            <p className={textStyles.description}>Arraste arquivos ou clique acima para enviar</p>
          </div>
        )}

        {/* Currículo com Preview PDF */}
        <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
          <div
            className="p-2.5 cursor-pointer hover:bg-lia-bg-primary dark:hover:bg-gray-800 transition-colors motion-reduce:transition-none"
            onClick={() => setExpandedActivity(expandedActivity === 'cv' ? null : 'cv')}
          >
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
                <FileText className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className={`${textStyles.bodySmall} font-medium`}>
                      CV_MariaOliveira_2024.pdf
                    </h5>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={textStyles.bodySmall}>
                        2.1 MB • PDF
                      </span>
                      <span className={textStyles.bodySmall}>
                        Enviado há 2 dias
                      </span>
                      <Badge className="text-xs px-1 py-0 h-3.5 bg-status-error-bg text-status-error" >
                        <Tag className="w-2.5 h-2.5 mr-0.5" />
                        Currículo
                      </Badge>
                    </div>
                    <p className={`${textStyles.bodySmall} mt-1`}>
                      Currículo atualizado • Categorizado pela LIA
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="p-1 h-6 w-6"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedFile({ name: 'CV_MariaOliveira_2024.pdf', type: 'pdf' })
                        setPreviewType('pdf')
                        setShowPreview(true)
                      }}
                    >
                      <Eye className="w-3 h-3" />
                    </Button>
                    <Button size="sm" variant="ghost" className="p-1 h-6 w-6">
                      <Download className="w-3 h-3" />
                    </Button>
                    <ChevronDown
                      className={`w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary transition-transform motion-reduce:transition-none ${
 expandedActivity === 'cv' ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {expandedActivity === 'cv' && (
            <div className="px-3 pb-3 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-white/50 dark:bg-lia-bg-primary/50">
              <div className="mt-2 space-y-2">
                {/* Mini Preview do PDF */}
                <div className="bg-white dark:bg-lia-bg-primary p-2 rounded-md">
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mb-2">Preview do documento</p>
                  <div className="bg-gray-100 dark:bg-lia-bg-secondary rounded-md h-32 flex items-center justify-center">
                    <div className="text-center">
                      <FileText className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary mx-auto mb-1" />
                      <p className={textStyles.bodySmall}>PDF • 5 páginas</p>
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-2 text-xs px-2 py-1 h-5"
                        onClick={() => {
                          setSelectedFile({ name: 'CV_MariaOliveira_2024.pdf', type: 'pdf' })
                          setPreviewType('pdf')
                          setShowPreview(true)
                        }}
                      >
                        Visualizar Completo
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="bg-white dark:bg-lia-bg-primary p-2 rounded-md">
                  <p className={`${textStyles.bodySmall} mb-1`}>Análise da LIA</p>
                  <p className={textStyles.bodySmall}>
                    ✓ CV bem estruturado • Match 92% com a vaga • Experiência relevante
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Foto do Candidato com Preview de Imagem */}
        <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
          <div className="p-2.5">
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
                <Image className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className={`${textStyles.bodySmall} font-medium`}>
                      foto_perfil.jpg
                    </h5>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={textStyles.bodySmall}>
                        456 KB • JPG
                      </span>
                      <span className={textStyles.bodySmall}>
                        Enviado hoje
                      </span>
                      <Badge className="text-xs px-1 py-0 h-3.5 bg-status-success-bg text-status-success" >
                        <Tag className="w-2.5 h-2.5 mr-0.5" />
                        Foto
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="p-1 h-6 w-6"
                      onClick={() => {
                        setSelectedFile({ name: 'foto_perfil.jpg', type: 'image', url: candidate.avatar_url || candidate.avatar })
                        setPreviewType('image')
                        setShowPreview(true)
                      }}
                    >
                      <Eye className="w-3 h-3" />
                    </Button>
                    <Button size="sm" variant="ghost" className="p-1 h-6 w-6">
                      <Download className="w-3 h-3" />
                    </Button>
                  </div>
                </div>

                {/* Thumbnail da imagem */}
                {(candidate.avatar_url || candidate.avatar) && (
                  <div className="mt-2">
                    <img
                      src={candidate.avatar_url || candidate.avatar}
                      alt="Preview"
                      className="w-12 h-12 rounded-md object-cover cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none"
                      onClick={() => {
                        setSelectedFile({ name: 'foto_perfil.jpg', type: 'image', url: candidate.avatar_url || candidate.avatar })
                        setPreviewType('image')
                        setShowPreview(true)
                      }}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Vídeo de Apresentação */}
        <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
          <div
            className="p-2.5 cursor-pointer hover:bg-lia-bg-primary dark:hover:bg-gray-800 transition-colors motion-reduce:transition-none"
            onClick={() => setExpandedActivity(expandedActivity === 'video1' ? null : 'video1')}
          >
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-status-error/15 flex items-center justify-center flex-shrink-0">
                <FileVideo className="w-3.5 h-3.5 text-status-error" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className={`${textStyles.bodySmall} font-medium`}>
                      Apresentacao_Pessoal.mp4
                    </h5>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={textStyles.bodySmall}>
                        25.4 MB • MP4 • 3:45
                      </span>
                      <Badge className="text-xs px-1 py-0 h-3.5 bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle">
                        <Tag className="w-2.5 h-2.5 mr-0.5" />
                        Triagem
                      </Badge>
                    </div>
                    <p className={`${textStyles.bodySmall} mt-1`}>
                      Vídeo de apresentação pessoal • Prescreening
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Badge className="text-xs px-1.5 py-0 h-4 bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary">
                      Analisado
                    </Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="p-1 h-6 w-6"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedFile({
                          name: 'Apresentacao_Pessoal.mp4',
                          type: 'video',
                          videoType: 'prescreening',
                          duration: '3:45'
                        })
                        setPreviewType('video')
                        setShowPreview(true)
                      }}
                    >
                      <Play className="w-3 h-3" />
                    </Button>
                    <ChevronDown
                      className={`w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary transition-transform motion-reduce:transition-none ${
 expandedActivity === 'video1' ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {expandedActivity === 'video1' && (
            <div className="px-3 pb-3 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-white/50 dark:bg-lia-bg-primary/50">
              <div className="mt-2 space-y-2">
                {/* Preview do vídeo com thumbnail */}
                <div className="bg-white dark:bg-lia-bg-primary p-2 rounded-md">
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mb-2">Preview do vídeo de triagem</p>
                  <div className="relative bg-gray-900 rounded-md h-24 flex items-center justify-center group cursor-pointer"
                       onClick={() => {
                         setSelectedFile({
                           name: 'Apresentacao_Pessoal.mp4',
                           type: 'video',
                           videoType: 'prescreening',
                           duration: '3:45'
                         })
                         setPreviewType('video')
                         setShowPreview(true)
                       }}>
                    <div className="absolute inset-0 bg-black/50 rounded-md flex items-center justify-center group-hover:bg-black/40 transition-colors motion-reduce:transition-none">
                      <Play className="w-8 h-8 text-white" />
                    </div>
                    <span className="absolute bottom-1 right-1 text-xs text-white bg-black/70 px-1 rounded-full">
                      3:45
                    </span>
                    <Badge className="absolute top-1 left-1 text-xs px-1.5 py-0.5" style={{backgroundColor: 'var(--gray-700)', color: 'var(--white)'}}>
                      Prescreening
                    </Badge>
                  </div>
                </div>

                {/* Análise de IA do vídeo */}
                <div className="bg-white dark:bg-lia-bg-primary p-2 rounded-md">
                  <p className={`${textStyles.bodySmall} mb-1`}>Análise da LIA</p>
                  <div className="grid grid-cols-2 gap-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-lia-text-secondary dark:text-lia-text-tertiary">Confiança:</span>
                      <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">92%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-lia-text-secondary dark:text-lia-text-tertiary">Comunicação:</span>
                      <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">95%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-lia-text-secondary dark:text-lia-text-tertiary">Clareza:</span>
                      <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">88%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-lia-text-secondary dark:text-lia-text-tertiary">Entusiasmo:</span>
                      <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">90%</span>
                    </div>
                  </div>

                  {/* Mini parecer */}
                  <div className="mt-2 pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <p className={textStyles.bodySmall}>
                      <span className="font-semibold text-lia-text-primary dark:text-lia-text-primary">Score Geral: 91%</span> - Candidato demonstra excelente comunicação e fit cultural.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Vídeo de Case Técnico */}
        <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
          <div className="p-2.5">
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
                <Video className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className={`${textStyles.bodySmall} font-medium`}>
                      Case_UX_Design.mp4
                    </h5>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={textStyles.bodySmall}>
                        45.2 MB • MP4 • 8:20
                      </span>
                      <Badge className="text-xs px-1 py-0 h-3.5 bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle">
                        <Tag className="w-2.5 h-2.5 mr-0.5" />
                        Entrevista
                      </Badge>
                    </div>
                    <p className={`${textStyles.bodySmall} mt-1`}>
                      Apresentação de case técnico • Entrevista gravada
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Badge className="text-xs px-1.5 py-0 h-4 bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary">
                      Destaque
                    </Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="p-1 h-6 w-6"
                      onClick={() => {
                        setSelectedFile({
                          name: 'Case_UX_Design.mp4',
                          type: 'video',
                          videoType: 'interview',
                          duration: '8:20'
                        })
                        setPreviewType('video')
                        setShowPreview(true)
                      }}
                    >
                      <Play className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Vídeo de Entrevista com Gestor - Novo */}
        <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
          <div className="p-2.5">
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
                <Video className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className={`${textStyles.bodySmall} font-medium`}>
                      Entrevista_TechLead_30min.mp4
                    </h5>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={textStyles.bodySmall}>
                        120.5 MB • MP4 • 30:15
                      </span>
                      <Badge className="text-xs px-1 py-0 h-3.5 bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary border-lia-border-default dark:border-lia-border-default">
                        <Tag className="w-2.5 h-2.5 mr-0.5" />
                        Entrevista
                      </Badge>
                    </div>
                    <p className={`${textStyles.bodySmall} mt-1`}>
                      Entrevista técnica com Carlos Mendes • Gravada via Meet
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Badge className="text-xs px-1.5 py-0 h-4 bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary">
                      Completa
                    </Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="p-1 h-6 w-6"
                      onClick={() => {
                        setSelectedFile({
                          name: 'Entrevista_TechLead_30min.mp4',
                          type: 'video',
                          videoType: 'interview',
                          duration: '30:15'
                        })
                        setPreviewType('video')
                        setShowPreview(true)
                      }}
                    >
                      <Play className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Áudio de Triagem por Voz - Card Compacto */}
        <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
          <div className="p-2.5">
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-wedo-purple/15 flex items-center justify-center flex-shrink-0">
                <Mic className="w-3.5 h-3.5 text-wedo-purple" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className={`${textStyles.bodySmall} font-medium`}>
                      Triagem_Voz_Resposta.mp3
                    </h5>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={textStyles.bodySmall}>
                        2.8 MB • MP3 • 4:32
                      </span>
                      <Badge className="text-xs px-1 py-0 h-3.5" style={{backgroundColor: 'var(--gray-100)', color: 'var(--wedo-purple)'}}>
                        <Tag className="w-2.5 h-2.5 mr-0.5" />
                        Triagem
                      </Badge>
                    </div>
                    <p className={`${textStyles.bodySmall} mt-1`}>
                      Resposta de triagem por voz • OpenMic.ai
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Badge className="text-xs px-1.5 py-0 h-4 bg-status-success/15 text-status-success">
                      Transcrito
                    </Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="p-1 h-6 w-6"
                      onClick={() => {
                        setSelectedFile({
                          name: 'Triagem_Voz_Resposta.mp3',
                          type: 'audio',
                          audioType: 'prescreening',
                          duration: '4:32'
                        })
                        setPreviewType('audio')
                        setShowPreview(true)
                      }}
                    >
                      <Play className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Áudio de Entrevista Gravada - Card Compacto */}
        <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
          <div className="p-2.5">
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-full bg-wedo-purple/15 flex items-center justify-center flex-shrink-0">
                <Mic className="w-3.5 h-3.5 text-wedo-purple" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className={`${textStyles.bodySmall} font-medium`}>
                      Entrevista_RH_Audio.wav
                    </h5>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={textStyles.bodySmall}>
                        18.5 MB • WAV • 15:20
                      </span>
                      <Badge className="text-xs px-1 py-0 h-3.5 bg-gray-200">
                        <Tag className="w-2.5 h-2.5 mr-0.5" />
                        Entrevista
                      </Badge>
                    </div>
                    <p className={`${textStyles.bodySmall} mt-1`}>
                      Gravação de entrevista com RH • Teams
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Badge className="text-xs px-1.5 py-0 h-4 bg-status-warning/15 text-status-warning">
                      Pendente
                    </Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="p-1 h-6 w-6"
                      onClick={() => {
                        setSelectedFile({
                          name: 'Entrevista_RH_Audio.wav',
                          type: 'audio',
                          audioType: 'interview',
                          duration: '15:20'
                        })
                        setPreviewType('audio')
                        setShowPreview(true)
                      }}
                    >
                      <Play className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <FilePreviewModal
        showPreview={showPreview}
        selectedFile={selectedFile}
        previewType={previewType}
        onClose={() => {
          setShowPreview(false)
          setSelectedFile(null)
          setPreviewType(null)
        }}
        candidate={candidate}
      />
    </div>
  )
}
