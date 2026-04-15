"use client"

import React, { useState, useRef, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Upload, FileText, CheckCircle, AlertTriangle, Loader2, X, Clock,
  BookOpen, Network, DollarSign, Code,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { useLiaFloat } from "@/contexts/lia-float-context"
import type { LucideIcon } from "lucide-react"

type UploadState = "idle" | "uploading" | "extracting" | "sending" | "done" | "error"

interface DocumentType {
  id: string
  label: string
  description: string
  icon: LucideIcon
  acceptHint: string
}

const DOCUMENT_TYPES: DocumentType[] = [
  { id: "handbook", label: "Manual / Handbook", description: "Cultura, missão, valores, benefícios", icon: BookOpen, acceptHint: "PDF, DOCX ou TXT" },
  { id: "org_chart", label: "Organograma", description: "Departamentos e hierarquia", icon: Network, acceptHint: "PDF, DOCX ou TXT" },
  { id: "compensation", label: "Plano de Remuneração", description: "Faixas salariais e benefícios", icon: DollarSign, acceptHint: "PDF, DOCX ou TXT" },
  { id: "tech_doc", label: "Documentação Técnica", description: "Stack, ferramentas, cultura de engenharia", icon: Code, acceptHint: "PDF, DOCX ou TXT" },
]

interface UploadedDoc {
  documentType: string
  fileName: string
  uploadedAt: string
  textLength: number
  warnings: string[]
}

const STORAGE_KEY = "lia_uploaded_documents"

function loadUploadedDocs(): UploadedDoc[] {
  if (typeof window === "undefined") return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveUploadedDoc(doc: UploadedDoc) {
  const docs = loadUploadedDocs()
  const filtered = docs.filter(d => d.documentType !== doc.documentType)
  filtered.push(doc)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
}

const MAX_FILE_SIZE = 10 * 1024 * 1024

export function DocumentUploadCard() {
  const [uploadState, setUploadState] = useState<UploadState>("idle")
  const [activeDocType, setActiveDocType] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [fairnessWarnings, setFairnessWarnings] = useState<string[]>([])
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDoc[]>(loadUploadedDocs)
  const [extractedSummary, setExtractedSummary] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { sendChatMessage } = useLiaFloat()

  const resetState = useCallback(() => {
    setUploadState("idle")
    setActiveDocType(null)
    setErrorMessage(null)
    setFairnessWarnings([])
    setExtractedSummary(null)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }, [])

  const handleSelectDocType = (docTypeId: string) => {
    setActiveDocType(docTypeId)
    fileInputRef.current?.click()
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !activeDocType) return

    const validTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain",
    ]
    const validExts = [".pdf", ".docx", ".txt"]
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase()

    if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
      setErrorMessage("Formato não suportado. Use PDF, DOCX ou TXT.")
      setUploadState("error")
      setTimeout(resetState, 4000)
      return
    }

    if (file.size > MAX_FILE_SIZE) {
      setErrorMessage("Arquivo muito grande (máximo 10MB).")
      setUploadState("error")
      setTimeout(resetState, 4000)
      return
    }

    setUploadState("uploading")
    setErrorMessage(null)
    setFairnessWarnings([])

    try {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("document_type", activeDocType)

      setUploadState("extracting")

      const response = await fetch("/api/backend-proxy/documents/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.error || "Falha ao processar o documento")
      }

      const result = await response.json()
      const extractedText = result.extracted_text || ""
      const warnings = result.fairness_warnings || []

      if (!extractedText || extractedText.trim().length < 10) {
        throw new Error("Não foi possível extrair texto suficiente do documento.")
      }

      setFairnessWarnings(warnings)
      setExtractedSummary(`${extractedText.length} caracteres extraídos`)
      setUploadState("sending")

      const docTypeLabel = DOCUMENT_TYPES.find(d => d.id === activeDocType)?.label || activeDocType
      const chatMessage = `[Upload de documento: ${docTypeLabel}]\nArquivo: ${file.name}\nTipo: ${activeDocType}\n\nTexto extraído do documento (${extractedText.length} caracteres):\n\n${extractedText.substring(0, 8000)}`

      await sendChatMessage(chatMessage, "company_settings")

      const newDoc: UploadedDoc = {
        documentType: activeDocType,
        fileName: file.name,
        uploadedAt: new Date().toISOString(),
        textLength: extractedText.length,
        warnings,
      }
      saveUploadedDoc(newDoc)
      setUploadedDocs(loadUploadedDocs())

      setUploadState("done")
      setTimeout(resetState, 6000)
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Erro ao processar documento")
      setUploadState("error")
      setTimeout(resetState, 5000)
    }
  }

  const getDocUploadInfo = (docTypeId: string): UploadedDoc | undefined => {
    return uploadedDocs.find(d => d.documentType === docTypeId)
  }

  const isProcessing = uploadState !== "idle" && uploadState !== "done" && uploadState !== "error"

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {DOCUMENT_TYPES.map((docType) => {
          const uploaded = getDocUploadInfo(docType.id)
          const isActive = activeDocType === docType.id && isProcessing
          const IconComp = docType.icon

          return (
            <Card
              key={docType.id}
              className={`border rounded-lg transition-colors motion-reduce:transition-none cursor-pointer ${
                isActive
                  ? "border-lia-btn-primary-bg bg-lia-btn-primary-bg/5"
                  : uploaded
                  ? "border-status-success/30 bg-status-success/5 hover:border-status-success/50"
                  : "border-lia-border-subtle hover:border-lia-border-medium"
              } ${isProcessing && !isActive ? "opacity-50 pointer-events-none" : ""}`}
              onClick={() => !isProcessing && handleSelectDocType(docType.id)}
            >
              <CardContent className="p-3">
                <div className="flex items-start gap-2.5">
                  <div className={`w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 ${
                    uploaded ? "bg-status-success/10" : "bg-lia-bg-tertiary dark:bg-lia-bg-elevated"
                  }`}>
                    {isActive ? (
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-btn-primary-bg" />
                    ) : uploaded ? (
                      <CheckCircle className="w-4 h-4 text-status-success" />
                    ) : (
                      <IconComp className="w-4 h-4 text-lia-text-secondary" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`${textStyles.labelSmall} truncate`}>{docType.label}</p>
                    {isActive ? (
                      <p className="text-micro text-lia-btn-primary-bg font-medium mt-0.5">
                        {uploadState === "uploading" && "Enviando..."}
                        {uploadState === "extracting" && "Extraindo texto..."}
                        {uploadState === "sending" && "Enviando para LIA..."}
                      </p>
                    ) : uploaded ? (
                      <div className="mt-0.5">
                        <p className="text-micro text-status-success truncate">{uploaded.fileName}</p>
                        <p className="text-micro text-lia-text-tertiary flex items-center gap-1 mt-0.5">
                          <Clock className="w-2.5 h-2.5" />
                          {new Date(uploaded.uploadedAt).toLocaleDateString("pt-BR")}
                        </p>
                      </div>
                    ) : (
                      <p className="text-micro text-lia-text-tertiary mt-0.5">{docType.description}</p>
                    )}

                    {uploaded && uploaded.warnings.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {uploaded.warnings.slice(0, 2).map((w, i) => (
                          <Badge
                            key={i}
                            variant="outline"
                            className="text-micro bg-status-warning/10 text-status-warning border-status-warning/30 rounded-full px-1.5 py-0"
                          >
                            <AlertTriangle className="w-2.5 h-2.5 mr-0.5" />
                            {w.length > 50 ? w.substring(0, 50) + "…" : w}
                          </Badge>
                        ))}
                        {uploaded.warnings.length > 2 && (
                          <Badge variant="outline" className="text-micro text-status-warning border-status-warning/30 rounded-full px-1.5 py-0">
                            +{uploaded.warnings.length - 2}
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                  {!isActive && !uploaded && (
                    <Upload className="w-3.5 h-3.5 text-lia-text-tertiary flex-shrink-0 mt-0.5" />
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {uploadState === "done" && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs bg-status-success/10 text-status-success border border-status-success/30">
          <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>Documento enviado para a LIA! Ela analisará e preencherá os campos automaticamente.</span>
        </div>
      )}

      {uploadState === "error" && errorMessage && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs bg-status-error/10 text-status-error border border-status-error/30">
          <X className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {fairnessWarnings.length > 0 && uploadState !== "idle" && (
        <div className="px-3 py-2 rounded-lg text-xs bg-status-warning/10 border border-status-warning/30">
          <div className="flex items-center gap-1.5 mb-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
            <span className="font-medium text-status-warning">FairnessGuard — Termos sensíveis detectados</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {fairnessWarnings.map((warning, i) => (
              <Badge
                key={i}
                variant="outline"
                className="text-micro bg-status-warning/10 text-status-warning border-status-warning/30 rounded-full"
              >
                {warning}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.txt"
        onChange={handleFileSelect}
      />

      <p className={`${textStyles.caption} text-center`}>
        <FileText className="w-3 h-3 inline mr-1" />
        PDF, DOCX ou TXT — máx. 10MB. A LIA extrairá e preencherá os campos automaticamente.
      </p>
    </div>
  )
}

export default DocumentUploadCard
