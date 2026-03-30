"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Plus, Upload, Download, X, Tag } from "lucide-react"
import { TabsContent } from "@/components/ui/tabs"
import { ACCEPTED_FILE_TYPES, MAX_FILE_SIZE_LABEL } from "../candidato-page.constants"
import type { CandidatoFileItem, FileCategoryItem } from "../candidato-page.types"

interface CandidatoFilesTabProps {
  candidateFiles: CandidatoFileItem[]
  fileCategories: FileCategoryItem[]
  isLoadingFiles: boolean
  isUploading: boolean
  uploadProgress: number
  isDragging: boolean
  selectedCategory: string | null
  setIsDragging: (v: boolean) => void
  setSelectedCategory: (v: string | null) => void
  handleFileUpload: (files: File[]) => void
  handleDownloadFile: (url: unknown, name: unknown) => void
  handleDeleteFile: (id: unknown) => void
  formatFileSize: (v: unknown) => string
  formatRelativeTime: (v: unknown) => string
  getCategoryColor: (type: unknown) => { bg: string; text: string }
  getCategoryLabel: (type: unknown) => string
  getFileIcon: (type: unknown, mime: unknown) => React.ReactNode
}

function triggerFileInput(
  isUploading: boolean,
  handleFileUpload: (files: File[]) => void
) {
  if (isUploading) return
  const input = document.createElement("input")
  input.type = "file"
  input.multiple = true
  input.accept = ACCEPTED_FILE_TYPES
  input.onchange = (e) => {
    const files = Array.from((e.target as HTMLInputElement).files || [])
    handleFileUpload(files)
  }
  input.click()
}

export function CandidatoFilesTab({
  candidateFiles,
  fileCategories,
  isLoadingFiles,
  isUploading,
  uploadProgress,
  isDragging,
  selectedCategory,
  setIsDragging,
  setSelectedCategory,
  handleFileUpload,
  handleDownloadFile,
  handleDeleteFile,
  formatFileSize,
  formatRelativeTime,
  getCategoryColor,
  getCategoryLabel,
  getFileIcon,
}: CandidatoFilesTabProps) {
  const visibleFiles = candidateFiles.filter(
    (file) => !selectedCategory || file.file_type === selectedCategory
  )

  return (
    <TabsContent value="files" className="mt-4">
      <Card className="border-lia-border-subtle">
        <CardContent className="p-0">
          <div className="flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
                  <FileText className="w-4 h-4 text-lia-text-primary" />
                  Arquivos e Documentos
                  <Badge className="text-xs px-1.5 py-0">{candidateFiles.length}</Badge>
                  {isLoadingFiles && (
                    <div
                      className="animate-spin motion-reduce:animate-none rounded-full h-3.5 w-3.5 border border-gray-400 border-t-gray-700"
                      role="status"
                      aria-label="Carregando..."
                    />
                  )}
                </h4>
                <Button
                  size="sm"
                  className="gap-1.5 px-3 py-1.5 text-xs h-8 bg-gray-100 hover:bg-gray-200 text-lia-text-primary border border-lia-border-subtle"
                  onClick={() => triggerFileInput(isUploading, handleFileUpload)}
                  disabled={isUploading}
                >
                  <Plus className="w-3.5 h-3.5" />
                  {isUploading ? "Enviando..." : "Adicionar Arquivo"}
                </Button>
              </div>

              {/* Categorias */}
              <div className="flex gap-1.5 flex-wrap">
                <Badge
                  variant="outline"
                  className={`text-xs px-2 py-0.5 cursor-pointer hover:bg-gray-100 ${!selectedCategory ? "bg-gray-100" : ""}`}
                  onClick={() => setSelectedCategory(null)}
                >
                  📁 Todos ({candidateFiles.length})
                </Badge>
                {fileCategories
                  .filter((c) => c.count > 0)
                  .map((cat) => (
                    <Badge
                      key={cat.category}
                      variant="outline"
                      className={`text-xs px-2 py-0.5 cursor-pointer hover:bg-gray-100 ${selectedCategory === cat.category ? "bg-gray-100" : ""}`}
                      onClick={() => setSelectedCategory(selectedCategory === cat.category ? null : cat.category)}
                    >
                      {cat.icon} {cat.label} ({cat.count})
                    </Badge>
                  ))}
              </div>
            </div>

            {/* File list */}
            <div className="flex-1 p-4 space-y-3">
              {/* Drag & Drop area */}
              <div
                className={`border-2 border-dashed rounded-md p-6 text-center transition-colors motion-reduce:transition-none cursor-pointer group ${
                  isDragging ? "border-gray-400 bg-gray-100" : "border-lia-border-default hover:border-gray-400"
                }`}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setIsDragging(false)
                  handleFileUpload(Array.from(e.dataTransfer.files))
                }}
                onClick={() => triggerFileInput(isUploading, handleFileUpload)}
              >
                <div className="flex flex-col items-center" role="status" aria-live="polite">
                  {isUploading ? (
                    <>
                      <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center mb-3">
                        <div className="animate-spin motion-reduce:animate-none rounded-full h-6 w-6 border-2 border-gray-400 border-t-gray-700" />
                      </div>
                      <p className="text-sm text-lia-text-primary font-medium mb-2">Enviando... {uploadProgress}%</p>
                      <div className="w-40 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gray-600 rounded-full transition-[width] duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                    </>
                  ) : (
                    <>
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors motion-reduce:transition-none ${isDragging ? "bg-gray-200" : "bg-gray-100 group-hover:bg-gray-200"}`}>
                        <Upload className={`w-6 h-6 ${isDragging ? "text-lia-text-primary" : "lia-text-600 group-hover:lia-text-700"}`} />
                      </div>
                      <p className="text-sm text-lia-text-primary mb-1">
                        {isDragging ? "Solte os arquivos aqui" : "Arraste arquivos ou clique para selecionar"}
                      </p>
                      <p className="text-xs text-lia-text-secondary">{MAX_FILE_SIZE_LABEL}</p>
                    </>
                  )}
                </div>
              </div>

              {/* Files from API */}
              {visibleFiles.map((file) => {
                const colors = getCategoryColor(file.file_type)
                return (
                  <div key={file.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md transition-colors motion-reduce:transition-none">
                    <div className="p-3">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
                          {getFileIcon(file.file_type, file.mime_type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h5 className="text-sm font-semibold text-lia-text-primary truncate">{file.file_name}</h5>
                              <div className="flex items-center gap-2 mt-1 flex-wrap">
                                <span className="text-xs text-lia-text-secondary">
                                  {formatFileSize(file.file_size)} • {file.file_name.split(".").pop()?.toUpperCase()}
                                </span>
                                <span className="text-xs text-lia-text-secondary">{formatRelativeTime(file.created_at)}</span>
                                <Badge
                                  className="text-xs px-1.5 py-0 h-4"
                                  style={{ backgroundColor: colors.bg, color: colors.text }}
                                >
                                  <Tag className="w-2.5 h-2.5 mr-0.5" />
                                  {getCategoryLabel(file.file_type)}
                                </Badge>
                              </div>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="p-1.5 h-7 w-7"
                                onClick={() => handleDownloadFile(file.file_url, file.file_name)}
                                title="Baixar arquivo"
                              >
                                <Download className="w-3.5 h-3.5" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="p-1.5 h-7 w-7 text-status-error hover:text-status-error hover:bg-status-error/10"
                                onClick={() => handleDeleteFile(file.id)}
                                title="Excluir arquivo"
                              >
                                <X className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}

              {/* Empty state */}
              {candidateFiles.length === 0 && !isLoadingFiles && (
                <div className="text-center py-8 text-lia-text-secondary">
                  <FileText className="w-10 h-10 mx-auto mb-3 lia-text-300" />
                  <p className="text-sm">Nenhum arquivo enviado</p>
                  <p className="text-xs text-lia-text-secondary mt-1">Arraste arquivos ou clique acima para enviar</p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </TabsContent>
  )
}
