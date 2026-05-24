"use client"

import { useCallback, useRef, useState } from "react"
import type { ImportState, PreviewData } from "./smart-import-types"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

const VALID_EXTENSIONS = ['.xlsx', '.xls', '.csv']
const VALID_MIME_TYPES = [
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'text/csv',
]

function isValidFileType(file: File): boolean {
  if (VALID_MIME_TYPES.includes(file.type)) return true
  return VALID_EXTENSIONS.some(ext => file.name.endsWith(ext))
}

interface SmartImportOptions {
  importEndpoint: string
  expectedFields: string[]
  templateDownloadEndpoint?: string
  disabled: boolean
  onImportSuccess: () => void
}

export function useSmartImport({
  importEndpoint,
  expectedFields,
  templateDownloadEndpoint,
  disabled,
  onImportSuccess,
}: SmartImportOptions) {
  const [state, setState] = useState<ImportState>('idle')
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const resetState = useCallback(() => {
    setState('idle')
    setFile(null)
    setPreviewData(null)
    setErrorMessage(null)
    setSuccessMessage(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  const processFile = useCallback(
    async (selectedFile: File) => {
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
        const response = await apiFetch(`${importEndpoint}?preview=true`, {
          method: 'POST',
          body: formData,
        })
        notifyChatOfSettingsUpdate({ actionId: "smart_import", section: "data_import" })
        if (!response.ok) throw new Error('Falha ao analisar o arquivo')
        const data = await response.json()
        const headers: string[] = data.headers || data.columns || []
        const rows: Record<string, string>[] =
          data.rows || data.preview || data.items || []
        const totalRows: number = data.total_rows || data.totalRows || rows.length
        const matchedFields = expectedFields.filter(field =>
          headers.some(
            (h: string) =>
              h.toLowerCase().includes(field.toLowerCase()) ||
              field.toLowerCase().includes(h.toLowerCase())
          )
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
    },
    [expectedFields, importEndpoint]
  )

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
    if (files.length > 0) processFile(files[0])
  }
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) processFile(files[0])
  }

  const handleConfirmImport = async () => {
    if (!file) return
    setState('importing')
    setErrorMessage(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiFetch(importEndpoint, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.detail || errorData.message || 'Falha ao importar dados'
        )
      }
      const result = await response.json()
      const count =
        result.imported_count ||
        result.count ||
        result.items?.length ||
        previewData?.totalRows ||
        0
      setSuccessMessage(
        `${count} ${count === 1 ? 'registro importado' : 'registros importados'} com sucesso!`
      )
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
      const response = await apiFetch(templateDownloadEndpoint)
      if (!response.ok) throw new Error('Falha ao baixar template')
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = 'template_importacao.csv'
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
        if (match && match[1]) filename = match[1].replace(/['"]/g, '')
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
    } catch {
      setErrorMessage('Erro ao baixar template')
      setTimeout(() => setErrorMessage(null), 3000)
    }
  }

  return {
    state,
    isDragging,
    file,
    previewData,
    errorMessage,
    successMessage,
    fileInputRef,
    resetState,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileSelect,
    handleConfirmImport,
    handleDownloadTemplate,
  }
}
