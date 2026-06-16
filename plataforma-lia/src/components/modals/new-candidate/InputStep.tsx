"use client"

import React, { useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import {
  User, Mail, Phone, Upload, FileText,
  X, Brain, AlertCircle,
  Linkedin, Loader2, File
} from "lucide-react"

type InputTab = 'cv' | 'linkedin' | 'manual'

interface InputStepProps {
  activeTab: InputTab
  setActiveTab: (tab: InputTab) => void
  setError: (e: string | null) => void

  // CV tab
  selectedFile: File | null
  setSelectedFile: (f: File | null) => void
  cvText: string
  setCvText: (t: string) => void
  isDragging: boolean
  handleDragEnter: (e: React.DragEvent) => void
  handleDragLeave: (e: React.DragEvent) => void
  handleDragOver: (e: React.DragEvent) => void
  handleDrop: (e: React.DragEvent) => void
  handleFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  isProcessing: boolean
  canSubmitCV: boolean
  handleSubmitCV: () => void

  // LinkedIn tab
  linkedinUrl: string
  setLinkedinUrl: (u: string) => void
  canSubmitLinkedin: boolean
  handleSubmitLinkedin: () => void

  // Manual tab
  manualData: { name: string; email: string; phone: string; linkedinUrl: string }
  setManualData: (d: (prev: { name: string; email: string; phone: string; linkedinUrl: string }) => { name: string; email: string; phone: string; linkedinUrl: string }) => void
  canSubmitManual: boolean
  handleSubmitManual: () => void

  error: string | null
  fieldErrors: Record<string, string>
  setFieldErrors: React.Dispatch<React.SetStateAction<Record<string, string>>>
}

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase()
  if (ext === 'pdf') return <FileText className="w-4 h-4 text-status-error" />
  if (['doc', 'docx'].includes(ext || '')) return <FileText className="w-4 h-4 text-wedo-cyan-text" />
  return <File className="w-4 h-4 text-lia-text-tertiary" />
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function InputStep({
  activeTab,
  setActiveTab,
  setError,
  selectedFile,
  setSelectedFile,
  cvText,
  setCvText,
  isDragging,
  handleDragEnter,
  handleDragLeave,
  handleDragOver,
  handleDrop,
  handleFileSelect,
  isProcessing,
  canSubmitCV,
  handleSubmitCV,
  linkedinUrl,
  setLinkedinUrl,
  canSubmitLinkedin,
  handleSubmitLinkedin,
  manualData,
  setManualData,
  canSubmitManual,
  handleSubmitManual,
  error,
  fieldErrors,
  setFieldErrors,
}: InputStepProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  return (
    <div data-testid="new-candidate-input-step" className="space-y-4">
      <div className="flex">
        <button
          onClick={() => { setActiveTab('cv'); setError(null); setFieldErrors({}) }}
          className={cn(
            "flex-1 py-2.5 text-xs font-medium transition-colors relative",
            activeTab === 'cv'
              ? "text-lia-text-primary"
              : "text-lia-text-tertiary hover:text-lia-text-secondary"
          )}
        >
          <div className="flex items-center justify-center gap-1.5">
            <FileText className="w-3.5 h-3.5" />
            CV
          </div>
          {activeTab === 'cv' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg" />
          )}
        </button>
        <button
          onClick={() => { setActiveTab('linkedin'); setError(null); setFieldErrors({}) }}
          className={cn(
            "flex-1 py-2.5 text-xs font-medium transition-colors relative",
            activeTab === 'linkedin'
              ? "text-lia-text-primary"
              : "text-lia-text-tertiary hover:text-lia-text-secondary"
          )}
        >
          <div className="flex items-center justify-center gap-1.5">
            <Linkedin className="w-3.5 h-3.5" />
            LinkedIn
          </div>
          {activeTab === 'linkedin' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg" />
          )}
        </button>
        <button
          onClick={() => { setActiveTab('manual'); setError(null); setFieldErrors({}) }}
          className={cn(
            "flex-1 py-2.5 text-xs font-medium transition-colors relative",
            activeTab === 'manual'
              ? "text-lia-text-primary"
              : "text-lia-text-tertiary hover:text-lia-text-secondary"
          )}
        >
          <div className="flex items-center justify-center gap-1.5">
            <User className="w-3.5 h-3.5" />
            Manual
          </div>
          {activeTab === 'manual' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg" />
          )}
        </button>
      </div>

      {activeTab === 'cv' && (
        <div className="space-y-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            onChange={handleFileSelect}
            className="hidden"
            id="cv-file-input"
          />

          {!selectedFile ? (
            <div
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition-colors",
                isDragging
                  ? "border-lia-btn-primary-bg bg-lia-bg-tertiary"
                  : "border-lia-border-subtle hover:border-lia-border-medium dark:hover:border-lia-border-medium hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover"
              )}
            >
              <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary flex items-center justify-center mx-auto mb-3">
                <Upload className={cn("w-5 h-5", isDragging ? "text-lia-text-primary" : "text-lia-text-tertiary")} />
              </div>
              <p className="text-xs font-medium text-lia-text-primary">
                {isDragging ? "Solte o arquivo aqui" : "Arraste ou clique para selecionar"}
              </p>
              <p className="text-xs text-lia-text-tertiary mt-1">
                PDF, DOCX, DOC ou TXT (máx. 5MB)
              </p>
            </div>
          ) : (
            <div className="border border-lia-border-subtle rounded-xl p-3">
              <div className="flex items-center gap-2">
                {getFileIcon(selectedFile.name)}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-lia-text-primary truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-lia-text-tertiary">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => {
                    setSelectedFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ""
                  }}
                >
                  <X className="w-3 h-3" />
                </Button>
              </div>
            </div>
          )}

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-lia-border-subtle" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-lia-bg-primary px-2 text-lia-text-tertiary">ou cole o texto</span>
            </div>
          </div>

          <Textarea
            placeholder="Cole aqui o conteúdo do currículo..."
            value={cvText}
            onChange={(e) => setCvText(e.target.value)}
            rows={4}
            className="resize-none text-xs"
          />
          <div className="flex justify-between items-center">
            <span className={cn(
              "text-xs",
              cvText.length < 50 ? "text-lia-text-tertiary" : "text-status-success"
            )}>
              {cvText.length} caracteres (mín. 50)
            </span>
          </div>

          <Button
            onClick={handleSubmitCV}
            disabled={!canSubmitCV || isProcessing}
            className="w-full h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
                Processando...
              </>
            ) : (
              <>
                <Brain className="w-3.5 h-3.5 mr-1.5 text-wedo-cyan" />
                Cadastrar com CV
              </>
            )}
          </Button>
        </div>
      )}

      {activeTab === 'linkedin' && (
        <div className="space-y-4">
          <div className="text-center py-2">
            <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary flex items-center justify-center mx-auto mb-3">
              <Linkedin className="w-6 h-6 text-lia-text-secondary" />
            </div>
            <p className="text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
              Cole a URL do perfil do LinkedIn do candidato
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="linkedin-url" className="text-xs font-sans">URL do LinkedIn</Label>
            <Input
              id="linkedin-url"
              placeholder="https://linkedin.com/in/nome-do-usuario"
              value={linkedinUrl}
              onChange={(e) => { setLinkedinUrl(e.target.value); setFieldErrors(prev => { const { linkedinUrl: _, ...rest } = prev; return rest }) }}
              aria-invalid={!!fieldErrors.linkedinUrl}
              className="h-9 text-xs font-sans"
            />
            {fieldErrors.linkedinUrl ? (
              <p role="alert" className="text-xs text-status-error">{fieldErrors.linkedinUrl}</p>
            ) : (
              <p className="text-xs text-lia-text-tertiary font-sans">
                Ex: linkedin.com/in/joao-silva
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 p-2.5 bg-lia-bg-secondary/50 border border-lia-border-default rounded-xl">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            <p className="text-xs text-lia-text-secondary font-sans" aria-live="polite" aria-atomic="true">
              A LIA irá buscar os dados do candidato
            </p>
          </div>

          <Button
            onClick={handleSubmitLinkedin}
            disabled={!canSubmitLinkedin || isProcessing}
            className="w-full h-9 text-xs bg-lia-btn-primary-bg hover:bg-lia-bg-primary text-white"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
                Cadastrando...
              </>
            ) : (
              <>
                <Linkedin className="w-3.5 h-3.5 mr-1.5" />
                Cadastrar via LinkedIn
              </>
            )}
          </Button>
        </div>
      )}

      {activeTab === 'manual' && (
        <div className="space-y-4">
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="manual-name" className="text-xs">Nome Completo *</Label>
              <div className="relative">
                <User className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-muted" />
                <Input
                  id="manual-name"
                  placeholder="João Silva"
                  value={manualData.name}
                  onChange={(e) => { setManualData(prev => ({ ...prev, name: e.target.value })); setFieldErrors(prev => { const { name: _, ...rest } = prev; return rest }) }}
                  aria-invalid={!!fieldErrors.name}
                  className="pl-8 h-9 text-xs"
                />
              </div>
              {fieldErrors.name && (
                <p role="alert" className="text-xs text-status-error">{fieldErrors.name}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="manual-email" className="text-xs">E-mail</Label>
              <div className="relative">
                <Mail className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-muted" />
                <Input
                  id="manual-email"
                  type="email"
                  placeholder="joao.silva@email.com"
                  value={manualData.email}
                  onChange={(e) => { setManualData(prev => ({ ...prev, email: e.target.value })); setFieldErrors(prev => { const { contact: _, ...rest } = prev; return rest }) }}
                  className="pl-8 h-9 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="manual-phone" className="text-xs">Telefone</Label>
              <div className="relative">
                <Phone className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-muted" />
                <Input
                  id="manual-phone"
                  placeholder="(11) 99999-9999"
                  value={manualData.phone}
                  onChange={(e) => { setManualData(prev => ({ ...prev, phone: e.target.value })); setFieldErrors(prev => { const { contact: _, ...rest } = prev; return rest }) }}
                  aria-invalid={!!fieldErrors.contact}
                  className="pl-8 h-9 text-xs"
                />
              </div>
              {fieldErrors.contact && (
                <p role="alert" className="text-xs text-status-error">{fieldErrors.contact}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="manual-linkedin" className="text-xs font-sans">LinkedIn (opcional)</Label>
              <div className="relative">
                <Linkedin className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-muted" />
                <Input
                  id="manual-linkedin"
                  placeholder="linkedin.com/in/joao-silva"
                  value={manualData.linkedinUrl}
                  onChange={(e) => setManualData(prev => ({ ...prev, linkedinUrl: e.target.value }))}
                  className="pl-8 h-9 text-xs font-sans"
                />
              </div>
              {manualData.linkedinUrl.includes('linkedin.com/in/') && (
                <p className="text-micro text-lia-text-secondary flex items-center gap-1 font-sans">
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  A LIA irá buscar os dados do candidato
                </p>
              )}
            </div>

            <p className="text-xs text-lia-text-tertiary">
              * Informe pelo menos um contato (email ou telefone)
            </p>
          </div>

          <Button
            onClick={handleSubmitManual}
            disabled={!canSubmitManual || isProcessing}
            className="w-full h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
                Cadastrando...
              </>
            ) : (
              <>
                <User className="w-3.5 h-3.5 mr-1.5" />
                Cadastrar Candidato
              </>
            )}
          </Button>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-2.5 bg-status-error/10 border border-status-error/30 rounded-xl">
          <AlertCircle className="w-4 h-4 text-status-error flex-shrink-0" />
          <p className="text-xs text-status-error">{error}</p>
        </div>
      )}
    </div>
  )
}
