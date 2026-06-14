"use client"

import React, { useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Paperclip, X, FileText, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface UploadedFile {
  file: File
  id: string
  status: "pending" | "uploading" | "success" | "error"
  extractedText?: string
}

interface FileUploadButtonProps {
  onFilesSelected: (files: File[]) => void
  onFileAnalyzed?: (file: File, analysis: FileAnalysisResult) => void
  maxFiles?: number
  acceptedTypes?: string
  disabled?: boolean
  className?: string
  showPreview?: boolean
  autoAnalyze?: boolean
}

export interface FileAnalysisResult {
  success: boolean
  filename: string
  extractedText?: string
  keywords?: string[]
  summary?: string
  entities?: {
    skills?: string[]
    job_titles?: string[]
    companies?: string[]
    locations?: string[]
    experience_years?: number
  }
  error?: string
}

export function FileUploadButton({
  onFilesSelected,
  onFileAnalyzed,
  maxFiles = 3,
  acceptedTypes = ".pdf,.doc,.docx,.txt,.xls,.xlsx",
  disabled = false,
  className,
  showPreview = true,
  autoAnalyze = true,
}: FileUploadButtonProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const newFiles = Array.from(files).slice(0, maxFiles - uploadedFiles.length)
    
    const newUploadedFiles: UploadedFile[] = newFiles.map(file => ({
      file,
      id: `${file.name}-${Date.now()}`,
      status: "pending" as const,
    }))

    setUploadedFiles(prev => [...prev, ...newUploadedFiles])
    onFilesSelected(newFiles)

    if (autoAnalyze && onFileAnalyzed) {
      setIsAnalyzing(true)
      for (const uploadedFile of newUploadedFiles) {
        try {
          setUploadedFiles(prev =>
            prev.map(f =>
              f.id === uploadedFile.id ? { ...f, status: "uploading" as const } : f
            )
          )

          const analysis = await analyzeFile(uploadedFile.file)
          
          setUploadedFiles(prev =>
            prev.map(f =>
              f.id === uploadedFile.id
                ? { ...f, status: analysis.success ? "success" : "error", extractedText: analysis.extractedText }
                : f
            )
          )

          onFileAnalyzed(uploadedFile.file, analysis)
        } catch (error) {
          setUploadedFiles(prev =>
            prev.map(f =>
              f.id === uploadedFile.id ? { ...f, status: "error" as const } : f
            )
          )
          onFileAnalyzed(uploadedFile.file, {
            success: false,
            filename: uploadedFile.file.name,
            error: error instanceof Error ? error.message : "Erro ao analisar arquivo",
          })
        }
      }
      setIsAnalyzing(false)
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id))
  }

  const analyzeFile = async (file: File): Promise<FileAnalysisResult> => {
    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch("/api/backend-proxy/analysis/file", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      return {
        success: false,
        filename: file.name,
        error: error instanceof Error ? error.message : "Unknown error",
      }
    }
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedTypes}
        multiple={maxFiles > 1}
        onChange={handleFileChange}
        className="hidden"
      />

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleClick}
              disabled={disabled || uploadedFiles.length >= maxFiles || isAnalyzing}
              className="h-8 w-8 text-lia-text-secondary hover:text-lia-text-primary hover:bg-lia-interactive-hover"
            >
              {isAnalyzing ? (
                <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
              ) : (
                <Paperclip className="h-4 w-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Anexar arquivo para análise (PDF, DOC, XLS)</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {showPreview && uploadedFiles.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {uploadedFiles.map(uf => (
            <div
              key={uf.id}
              className={cn(
 "flex items-center gap-1 px-2 py-1 rounded-md text-xs",
                uf.status === "uploading" && "bg-wedo-cyan/10 text-lia-text-secondary",
                uf.status === "success" && "bg-status-success/10 text-status-success",
                uf.status === "error" && "bg-status-error/10 text-status-error",
                uf.status === "pending" && "bg-lia-bg-secondary text-lia-text-secondary"
              )}
            >
              {uf.status === "uploading" ? (
                <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" />
              ) : (
                <FileText className="h-3 w-3" />
              )}
              <span className="max-w-[100px] truncate">{uf.file.name}</span>
              <button
                onClick={() => removeFile(uf.id)}
                className="hover:text-status-error"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
