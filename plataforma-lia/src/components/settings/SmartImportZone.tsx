"use client"

import React, { useState, useRef, useCallback } from "react"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ThinkingDots } from "@/components/ui/thinking-dots"
import {
  FileSpreadsheet,
  Upload,
  Brain,
  CheckCircle,
  AlertCircle,
  Loader2,
  Download,
  X,
  Eye,
  FileText,
} from "lucide-react"

type ImportState = 'idle' | 'uploading' | 'analyzing' | 'preview' | 'importing' | 'success' | 'error'

interface PreviewData {
  headers: string[]
  rows: Record<string, string>[]
  totalRows: number
  matchedFields: string[]
  unmatchedFields: string[]
}

interface SmartImportZoneProps {
  title: string
  description: string
  importEndpoint: string
  onImportSuccess: () => void
  expectedFields: string[]
  templateDownloadEndpoint?: string
  disabled?: boolean
}

export function SmartImportZone({
  title,
  description,
  importEndpoint,
  onImportSuccess,
  expectedFields,
  templateDownloadEndpoint,
  disabled = false,
}: SmartImportZoneProps) {
  const [state, setState] = useState<ImportState>('idle')
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [importedCount, setImportedCount] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const resetState = useCallback(() => {
    setState('idle')
    setFile(null)
    setPreviewData(null)
    setErrorMessage(null)
    setSuccessMessage(null)
    setImportedCount(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  const isValidFileType = (file: File): boolean => {
    return (
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.type === 'application/vnd.ms-excel' ||
      file.type === 'text/csv' ||
      file.name.endsWith('.xlsx') ||
      file.name.endsWith('.xls') ||
      file.name.endsWith('.csv')
    )
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (disabled) return
    const files = e.dataTransfer.files
    if (files.length > 0) {
      processFile(files[0])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      processFile(files[0])
    }
  }

  const processFile = async (selectedFile: File) => {
    if (!isValidFileType(selectedFile)) {
      setErrorMessage("Por favor, selecione um arquivo Excel (.xlsx, .xls) ou CSV")
      setState('error')
      setTimeout(() => {
        setErrorMessage(null)
        setState('idle')
      }, 4000)
      return
    }

    setFile(selectedFile)
    setState('uploading')
    setErrorMessage(null)

    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      setState('analyzing')

      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('preview', 'true')

      const response = await fetch(`${importEndpoint}?preview=true`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Falha ao analisar o arquivo')
      }

      const data = await response.json()
      
      const headers = data.headers || data.columns || []
      const rows = data.rows || data.preview || data.items || []
      const totalRows = data.total_rows || data.totalRows || rows.length

      const matchedFields = expectedFields.filter(field => 
        headers.some((h: string) => h.toLowerCase().includes(field.toLowerCase()) || field.toLowerCase().includes(h.toLowerCase()))
      )
      const unmatchedFields = expectedFields.filter(field => !matchedFields.includes(field))

      setPreviewData({
        headers,
        rows: rows.slice(0, 5),
        totalRows,
        matchedFields,
        unmatchedFields,
      })
      setState('preview')
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Erro ao analisar o arquivo')
      setState('error')
    }
  }

  const handleConfirmImport = async () => {
    if (!file) return

    setState('importing')
    setErrorMessage(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(importEndpoint, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.message || 'Falha ao importar dados')
      }

      const result = await response.json()
      const count = result.imported_count || result.count || result.items?.length || previewData?.totalRows || 0
      
      setImportedCount(count)
      setSuccessMessage(`${count} ${count === 1 ? 'registro importado' : 'registros importados'} com sucesso!`)
      setState('success')
      onImportSuccess()
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Erro ao importar dados')
      setState('error')
    }
  }

  const handleDownloadTemplate = async () => {
    if (!templateDownloadEndpoint) return

    try {
      const response = await fetch(templateDownloadEndpoint)
      if (!response.ok) throw new Error('Falha ao baixar template')
      
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = 'template_importacao.csv'
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, '')
        }
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setErrorMessage('Erro ao baixar template')
      setTimeout(() => setErrorMessage(null), 3000)
    }
  }

  const renderIdleState = () => (
    <Card 
      className={`${cardStyles.interactive} border-2 border-dashed rounded-xl transition-colors motion-reduce:transition-none duration-200 ${
        disabled 
          ? 'opacity-50 cursor-not-allowed' 
          : 'cursor-pointer'
      } ${
        isDragging && !disabled
          ? 'border-gray-400 bg-gray-50 dark:bg-lia-bg-secondary/50 scale-[1.01]' 
          : 'border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 hover:bg-gray-50/50 dark:hover:bg-gray-800/30'
      }`}
      onDragOver={disabled ? undefined : handleDragOver}
      onDragLeave={disabled ? undefined : handleDragLeave}
      onDrop={disabled ? undefined : handleDrop}
      onClick={() => !disabled && fileInputRef.current?.click()}
    >
      <CardContent className="p-4">
        <div className="flex flex-col items-center justify-center text-center gap-2">
          <div className="w-10 h-10 rounded-md flex items-center justify-center transition-transform motion-reduce:transition-none duration-200 bg-gray-100 dark:bg-lia-bg-secondary">
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <h3 className={`${textStyles.title}`}>
            {title}
          </h3>
          <p className={`${textStyles.bodySmall} max-w-md`}>
            {description}
          </p>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-micro rounded-full">
              <FileSpreadsheet className="w-3.5 h-3.5 mr-1" />
              Excel (.xlsx, .xls)
            </Badge>
            <Badge variant="outline" className="text-micro rounded-full">
              <FileText className="w-3.5 h-3.5 mr-1" />
              CSV
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 rounded-md text-xs font-['Open_Sans',sans-serif]"
              onClick={(e) => {
                e.stopPropagation()
                if (!disabled) fileInputRef.current?.click()
              }}
              disabled={disabled}
            >
              <Upload className="w-3.5 h-3.5" />
              Selecionar Arquivo
            </Button>
            {templateDownloadEndpoint && (
              <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 rounded-md text-xs text-lia-text-primary hover:text-lia-text-primary font-['Open_Sans',sans-serif]"
                onClick={(e) => {
                  e.stopPropagation()
                  if (!disabled) handleDownloadTemplate()
                }}
                disabled={disabled}
              >
                <Download className="w-3.5 h-3.5" />
                Baixar Template
              </Button>
            )}
          </div>
          {expectedFields.length > 0 && (
            <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle w-full">
              <p className={`${textStyles.labelSmall} mb-2`}>
                Campos esperados:
              </p>
              <div className="flex flex-wrap justify-center gap-1.5">
                {expectedFields.map((field) => (
                  <Badge 
                    key={field} 
                    variant="secondary" 
                    className="text-micro bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary rounded-md"
                  >
                    {field}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".xlsx,.xls,.csv"
        onChange={handleFileSelect}
      />
    </Card>
  )

  const renderUploadingState = () => (
    <Card className="border border-lia-border-default dark:border-lia-border-default rounded-md bg-gray-50/50 dark:bg-lia-bg-secondary/30">
      <CardContent className="p-4">
        <div className="flex flex-col items-center justify-center text-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="w-10 h-10 rounded-md flex items-center justify-center bg-white dark:bg-lia-bg-secondary" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
          </div>
          <h3 className={`${textStyles.title}`}>
            Enviando arquivo...
          </h3>
          <p className={textStyles.bodySmall}>
            {file?.name}
          </p>
        </div>
      </CardContent>
    </Card>
  )

  const renderAnalyzingState = () => (
    <Card className="rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50 border border-lia-border-default dark:border-lia-border-default">
      <CardContent className="p-4">
        <div className="flex flex-col items-center justify-center text-center gap-2">
          <div className="w-10 h-10 rounded-md flex items-center justify-center bg-white dark:bg-lia-bg-secondary animate-pulse motion-reduce:animate-none">
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <h3 className={`${textStyles.title}`}>
            LIA está analisando...
          </h3>
          <p className={textStyles.bodySmall}>
            Identificando campos e validando dados
          </p>
          <div className="flex items-center gap-2 mt-2">
            <ThinkingDots dotClassName="bg-gray-900" size="md" />
          </div>
        </div>
      </CardContent>
    </Card>
  )

  const renderPreviewState = () => (
    <Card className={`${cardStyles.default} dark:border-lia-border-subtle rounded-md overflow-hidden`}>
      <div className="px-2 py-1.5 bg-gray-50 dark:bg-lia-bg-secondary/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-white dark:bg-lia-bg-secondary">
              <Eye className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <h3 className={`${textStyles.title}`}>
                Pré-visualização dos Dados
              </h3>
              <p className={textStyles.caption} aria-live="polite" aria-atomic="true">
                {previewData?.totalRows || 0} registros encontrados em {file?.name}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={resetState}
            className="rounded-md text-lia-text-primary hover:text-lia-text-primary"
          >
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      <CardContent className="p-4">
        {previewData && (
          <>
            <div className="flex flex-wrap gap-2 mb-3">
              {previewData.matchedFields.length > 0 && (
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5 text-status-success" />
                  <span className={`${textStyles.labelSmall}`}>
                    Campos identificados:
                  </span>
                  {previewData.matchedFields.map((field) => (
                    <Badge key={field} className="text-micro bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success rounded-full">
                      {field}
                    </Badge>
                  ))}
                </div>
              )}
              {previewData.unmatchedFields.length > 0 && (
                <div className="flex items-center gap-1.5 mt-1">
                  <AlertCircle className="w-3.5 h-3.5 text-status-warning" />
                  <span className={`${textStyles.labelSmall}`} aria-live="polite" aria-atomic="true">
                    Não encontrados:
                  </span>
                  {previewData.unmatchedFields.map((field) => (
                    <Badge key={field} className="text-micro bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning rounded-full">
                      {field}
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            {previewData.rows.length > 0 && (
              <div className="border border-lia-border-subtle dark:lia-border-800 rounded-md overflow-hidden mb-3">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-gray-50 dark:bg-lia-bg-secondary/50">
                        {previewData.headers.map((header, idx) => (
                          <th 
                            key={idx} 
                            className="px-2 py-1.5 text-left text-micro font-medium text-lia-text-secondary border-b border-lia-border-subtle dark:border-lia-border-subtle font-['Open_Sans',sans-serif]"
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.rows.map((row, rowIdx) => (
                        <tr key={rowIdx} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/30">
                          {previewData.headers.map((header, colIdx) => (
                            <td 
                              key={colIdx} 
                              className="px-2 py-1.5 text-xs text-lia-text-primary border-b border-gray-50 dark:lia-border-800 truncate max-w-sidebar-content font-['Open_Sans',sans-serif]"
                            >
                              {row[header] || '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {previewData.totalRows > 5 && (
                  <div className="px-2 py-1.5 text-center text-micro text-lia-text-secondary bg-gray-50/50 dark:bg-lia-bg-secondary/30 font-['Open_Sans',sans-serif]">
                    ... e mais {previewData.totalRows - 5} registros
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={resetState}
                className="gap-1.5 rounded-md text-xs font-['Open_Sans',sans-serif]"
              >
                <X className="w-3.5 h-3.5" />
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleConfirmImport}
                className="gap-1.5 rounded-md text-xs bg-gray-900 text-white hover:bg-gray-800 dark:hover:bg-gray-200 font-['Open_Sans',sans-serif]"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                Confirmar Importação
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )

  const renderImportingState = () => (
    <Card className="border border-lia-border-default dark:border-lia-border-default rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50">
      <CardContent className="p-4">
        <div className="flex flex-col items-center justify-center text-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="w-10 h-10 rounded-md flex items-center justify-center bg-white dark:bg-lia-bg-secondary" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
          </div>
          <h3 className={`${textStyles.title}`}>
            Importando dados...
          </h3>
          <p className={textStyles.bodySmall}>
            LIA está processando {previewData?.totalRows || 0} registros
          </p>
        </div>
      </CardContent>
    </Card>
  )

  const renderSuccessState = () => (
    <Card className={`${cardStyles.default} border border-status-success/30 dark:border-status-success/30 rounded-md bg-status-success/10/50 dark:bg-status-success/10`}>
      <CardContent className="p-4">
        <div className="flex flex-col items-center justify-center text-center gap-2">
          <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-success/15 dark:bg-status-success/30">
            <CheckCircle className="w-4 h-4 text-status-success dark:text-status-success" />
          </div>
          <h3 className={`${textStyles.title}`}>
            Importação Concluída!
          </h3>
          <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success`}>
            {successMessage}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={resetState}
            className="gap-1.5 rounded-md text-xs border-status-success/30 text-status-success hover:bg-status-success/15 dark:border-status-success/30 dark:text-status-success dark:hover:bg-status-success/30 font-['Open_Sans',sans-serif]"
          >
            <Upload className="w-3.5 h-3.5" />
            Nova Importação
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  const renderErrorState = () => (
    <Card className={`${cardStyles.default} border border-status-error/30 dark:border-status-error/30 rounded-md bg-status-error/10/50 dark:bg-status-error/10`}>
      <CardContent className="p-4">
        <div className="flex flex-col items-center justify-center text-center gap-2">
          <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-error/15 dark:bg-status-error/30">
            <AlertCircle className="w-4 h-4 text-status-error dark:text-status-error" />
          </div>
          <h3 className={`${textStyles.title}`}>
            Erro na Importação
          </h3>
          <p className={`${textStyles.bodySmall} text-status-error dark:text-status-error max-w-md`}>
            {errorMessage}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={resetState}
            className="gap-1.5 rounded-md text-xs border-status-error/30 text-status-error hover:bg-status-error/15 dark:border-status-error/30 dark:text-status-error dark:hover:bg-status-error/30 font-['Open_Sans',sans-serif]"
          >
            <X className="w-3.5 h-3.5" />
            Tentar Novamente
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  switch (state) {
    case 'uploading':
      return renderUploadingState()
    case 'analyzing':
      return renderAnalyzingState()
    case 'preview':
      return renderPreviewState()
    case 'importing':
      return renderImportingState()
    case 'success':
      return renderSuccessState()
    case 'error':
      return renderErrorState()
    default:
      return renderIdleState()
  }
}
