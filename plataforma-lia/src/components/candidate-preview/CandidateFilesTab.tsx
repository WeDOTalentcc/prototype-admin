"use client"

import { textStyles } from"@/lib/design-tokens"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  FileText, Plus, Upload, Download, Eye, Play, Tag, X,
  File, FileVideo, Image, Video, Mic, Award, ChevronDown
} from"lucide-react"
import { FilePreviewModal } from"@/components/candidate-preview/FilePreviewModal"
import { useCandidateFiles, formatFileSize, formatRelativeTime, getCategoryColor, getFileIcon } from"./useCandidateFiles"

interface CandidateFilesTabProps {
  candidate: Record<string, any>
}

export function CandidateFilesTab({ candidate }: CandidateFilesTabProps) {
  const {
    candidateFiles, fileCategories, isLoadingFiles,
    isUploading, uploadProgress,
    selectedCategory, setSelectedCategory,
    isDragging, setIsDragging,
    selectedFile, setSelectedFile,
    showPreview, setShowPreview,
    previewType, setPreviewType,
    expandedActivity, setExpandedActivity,
    handleFileUpload, handleDeleteFile, handleDownloadFile,
  } = useCandidateFiles(candidate)


  return (
    <div className="flex flex-col h-full">
      {/* Header com botão de adicionar */}
      <div className="p-3 bg-lia-bg-primary">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-medium text-lia-text-primary flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-lia-text-primary" />
            Arquivos e Documentos
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center">{candidateFiles.length}</Chip>
            {isLoadingFiles && (
              <div className="animate-spin motion-reduce:animate-none rounded-full h-3 w-3 border border-lia-border-medium border-t-lia-border-medium"></div>
            )}
          </h4>
          <Button
            size="sm"
            className="gap-1 px-2 py-1 text-xs h-6 bg-lia-bg-tertiary hover:bg-lia-interactive-active text-lia-text-secondary border border-lia-border-subtle"
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
          <Chip
            variant="neutral"
            className={`text-micro px-1.5 py-0 h-4 flex items-center cursor-pointer hover:bg-lia-interactive-hover ${!selectedCategory ? 'bg-lia-bg-tertiary' : ''}`}
            onClick={() => setSelectedCategory(null)}
          >
            📁 Todos ({candidateFiles.length})
          </Chip>
          {fileCategories.filter(c => c.count > 0).map((cat) => (
            <Chip
              key={cat.category}
              variant="neutral"
              className={`text-micro px-1.5 py-0 h-4 flex items-center cursor-pointer hover:bg-lia-interactive-hover ${selectedCategory === cat.category ? 'bg-lia-bg-tertiary' : ''}`}
              onClick={() => setSelectedCategory(selectedCategory === cat.category ? null : cat.category)}
            >
              {cat.icon} {cat.label} ({cat.count})
            </Chip>
          ))}
        </div>
      </div>

      {/* Lista de Arquivos */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {/* Drag and Drop Area */}
        <div
          className={`border-2 border-dashed rounded-md p-4 text-center transition-colors motion-reduce:transition-none cursor-pointer group ${
 isDragging
              ? 'border-lia-border-medium bg-lia-bg-tertiary'
              : 'border-lia-border-default hover:border-lia-border-medium'
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
                <div className="w-10 h-10 rounded-full bg-lia-interactive-active flex items-center justify-center mb-2">
                  <div className="animate-spin motion-reduce:animate-none rounded-full h-5 w-5 border-2 border-lia-border-medium border-t-lia-border-medium"></div>
                </div>
                <p className="text-xs text-lia-text-primary font-medium mb-1">
                  Enviando... {uploadProgress}%
                </p>
                <div className="w-32 h-1.5 bg-lia-interactive-active rounded-full overflow-hidden">
                  <div
                    className="h-full bg-lia-btn-primary-bg rounded-full transition-[width,height] duration-300"
                    style={{width: `${uploadProgress}%`}}
                  />
                </div>
              </>
            ) : (
              <>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 transition-colors motion-reduce:transition-none ${
 isDragging
                    ? 'bg-lia-interactive-active'
                    : 'bg-lia-bg-tertiary group-hover:bg-lia-interactive-active'
                }`}>
                  <Upload className={`w-5 h-5 ${isDragging ? 'text-lia-text-secondary' : 'text-lia-text-secondary group-hover:text-lia-text-secondary'}`} />
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
              <div key={file.id} className="border border-lia-border-subtle rounded-xl transition-colors motion-reduce:transition-none">
                <div className="p-2.5">
                  <div className="flex items-start gap-2">
                    <div className="w-7 h-7 rounded-full bg-lia-bg-tertiary flex items-center justify-center flex-shrink-0">
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
                            <Chip variant="neutral" muted
                              className="text-micro px-1.5 py-0 h-4 flex items-center"
                              style={{backgroundColor: colors.bg, color: colors.text}}
                            >
                              <Tag className="w-2.5 h-2.5 mr-0.5" />
                              {file.file_type === 'cv' ? 'Currículo' :
                               file.file_type === 'portfolio' ? 'Portfólio' :
                               file.file_type === 'video' ? 'Vídeo' :
                               file.file_type === 'certificate' ? 'Certificado' :
                               file.file_type === 'transcript' ? 'Transcrição' :
                               'Documento'}
                            </Chip>
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
          <div className="text-center py-6 text-lia-text-tertiary">
            <FileText className="w-8 h-8 mx-auto mb-2 text-lia-text-tertiary" />
            <p className="text-xs">Nenhum arquivo enviado</p>
            <p className={textStyles.description}>Arraste arquivos ou clique acima para enviar</p>
          </div>
        )}
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
