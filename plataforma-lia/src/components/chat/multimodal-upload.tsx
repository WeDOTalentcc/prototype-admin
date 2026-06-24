"use client"

import React, { useState, useRef, useCallback } from "react"
import { Upload, FileText, Image as ImageIcon, X, Loader2, Check, AlertCircle, File } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import { analyzeImage, analyzeDocument, analyzeResume, type ImageAnalysisResponse, type DocumentAnalysisResponse, type ResumeAnalysisResponse } from "@/services/lia-api"

export type AnalysisType = 'image' | 'document' | 'resume'
export type AnalysisResult = ImageAnalysisResponse | DocumentAnalysisResponse | ResumeAnalysisResponse

interface MultimodalUploadProps {
  onAnalysisComplete?: (result: AnalysisResult, type: AnalysisType) => void
  onFileSelect?: (file: File) => void
  onError?: (error: string) => void
  className?: string
  acceptedTypes?: string[]
  analysisType?: 'auto' | AnalysisType
  compact?: boolean
  autoAnalyze?: boolean
}

export function MultimodalUpload({
  onAnalysisComplete,
  onFileSelect,
  onError,
  className,
  acceptedTypes = ['image/*', 'application/pdf', '.doc', '.docx'],
  analysisType = 'auto',
  compact = false,
  autoAnalyze = false
}: MultimodalUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [resultType, setResultType] = useState<AnalysisType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) return <ImageIcon className="h-8 w-8 text-lia-text-secondary" />
    return <FileText className="h-8 w-8 text-lia-text-secondary" />
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const detectAnalysisType = useCallback((file: File): AnalysisType => {
    if (analysisType !== 'auto') return analysisType
    
    const fileName = file.name.toLowerCase()
    if (
      fileName.includes('cv') || 
      fileName.includes('curriculo') || 
      fileName.includes('currículo') ||
      fileName.includes('resume')
    ) {
      return 'resume'
    }
    
    if (file.type.startsWith('image/')) return 'image'
    return 'document'
  }, [analysisType])

  const analyzeFile = useCallback(async (fileToAnalyze?: File) => {
    const targetFile = fileToAnalyze || file
    if (!targetFile) return
    
    setIsAnalyzing(true)
    setProgress(0)
    setError(null)

    try {
      const type = detectAnalysisType(targetFile)
      let analysisResult: AnalysisResult

      setProgress(20)

      switch (type) {
        case 'resume':
          analysisResult = await analyzeResume(targetFile)
          break
        case 'image':
          analysisResult = await analyzeImage(targetFile)
          break
        case 'document':
        default:
          analysisResult = await analyzeDocument(targetFile)
          break
      }

      setProgress(100)
      setResult(analysisResult)
      setResultType(type)
      onAnalysisComplete?.(analysisResult, type)
    } catch (err) {
      const errorMsg = 'Erro ao analisar arquivo. Tente novamente.'
      setError(errorMsg)
      onError?.(errorMsg)
    } finally {
      setIsAnalyzing(false)
    }
  }, [file, detectAnalysisType, onAnalysisComplete, onError])

  const handleFileSelect = useCallback(async (selectedFile: File) => {
    setFile(selectedFile)
    setError(null)
    setResult(null)
    setResultType(null)
    setProgress(0)
    onFileSelect?.(selectedFile)

    if (selectedFile.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onload = (e) => setPreview(e.target?.result as string)
      reader.readAsDataURL(selectedFile)
    } else {
      setPreview(null)
    }

    if (autoAnalyze) {
      await analyzeFile(selectedFile)
    }
  }, [autoAnalyze, analyzeFile, onFileSelect])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      handleFileSelect(selectedFile)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) {
      handleFileSelect(droppedFile)
    }
  }



  const clearFile = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setResultType(null)
    setError(null)
    setProgress(0)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedTypes.join(',')}
          onChange={handleInputChange}
          className="hidden"
        />
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={() => fileInputRef.current?.click()}
          disabled={isAnalyzing}
          className="h-8 w-8 text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover focus-visible:ring-2 focus-visible:ring-lia-border-default"
          title="Anexar arquivo para análise"
          aria-label="Anexar arquivo para análise"
        >
          {isAnalyzing ? (
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
          ) : (
            <Upload className="h-4 w-4" />
          )}
        </Button>
        {file && (
          <div className="flex items-center gap-2 px-2 py-1 bg-lia-bg-tertiary rounded-xl text-xs">
            <span className="max-w-[100px] truncate">{file.name}</span>
            <button
              onClick={clearFile}
              className="text-lia-text-tertiary hover:text-lia-text-secondary focus-visible:ring-2 focus-visible:ring-lia-border-default rounded-md"
              aria-label="Remover arquivo"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <Card className={cn("p-4", className)}>
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedTypes.join(',')}
        onChange={handleInputChange}
        className="hidden"
      />

      {!file ? (
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "border-2 border-dashed rounded-md p-8 text-center cursor-pointer transition-colors",
            isDragOver 
              ? "border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-secondary/50" 
              : "border-lia-border-subtle hover:border-lia-btn-primary-bg hover:bg-lia-interactive-hover"
          )}
        >
          <Upload className={cn(
            "h-10 w-10 mx-auto mb-3 transition-colors",
            isDragOver ? "text-lia-text-secondary" : "text-lia-text-tertiary"
          )} />
          <p className="text-sm font-medium text-lia-text-primary mb-1">
            Arraste um arquivo ou clique para selecionar
          </p>
          <p className="text-xs text-lia-text-secondary">
            Imagens, PDFs, documentos Word
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            {preview ? (
              <img 
                src={preview} 
                alt="Preview" 
                className="w-16 h-16 object-cover rounded-md border"
              />
            ) : (
              <div className="w-16 h-16 bg-lia-bg-tertiary rounded-xl flex items-center justify-center">
                {getFileIcon(file.type)}
              </div>
            )}
            
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-lia-text-primary truncate">
                {file.name}
              </p>
              <p className="text-xs text-lia-text-secondary">
                {formatFileSize(file.size)}
              </p>
              {resultType && (
                <span className={cn(
                  "inline-flex items-center gap-1 text-micro mt-1 px-2 py-0.5 rounded-full",
                  resultType === 'resume' 
                    ? "bg-wedo-purple/15 text-wedo-purple-text"
                    : resultType === 'image'
                      ? "bg-wedo-cyan/15 text-wedo-cyan-text"
                      : "bg-status-warning/15 text-status-warning"
                )}>
                  {resultType === 'resume' ? 'Currículo' : resultType === 'image' ? 'Imagem' : 'Documento'}
                </span>
              )}
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={clearFile}
              className="h-8 w-8 text-lia-text-tertiary hover:text-lia-text-secondary focus-visible:ring-2 focus-visible:ring-lia-border-default"
              aria-label="Remover arquivo"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {isAnalyzing && (
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <p className="text-xs text-center text-lia-text-secondary">
                Analisando arquivo...
              </p>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 text-sm text-status-error bg-status-error/10 p-3 rounded-md">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="flex items-center gap-2 text-sm text-status-success bg-status-success/10 p-3 rounded-md">
              <Check className="h-4 w-4 flex-shrink-0" />
              <span>Análise concluída com sucesso!</span>
            </div>
          )}

          {!result && !isAnalyzing && !error && (
            <Button
              onClick={() => analyzeFile()}
              className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              <FileText className="h-4 w-4 mr-2" />
              Analisar Arquivo
            </Button>
          )}
        </div>
      )}
    </Card>
  )
}
