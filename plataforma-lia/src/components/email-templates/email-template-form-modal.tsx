"use client"

import { useState, useEffect, useMemo, useRef, useCallback } from"react"
import { useTranslations } from"next-intl"
import { DEMO_VALUES } from"@/lib/pricing"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from"@/components/ui/dialog"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from"@/components/ui/select"
import { Chip } from "@/components/ui/chip"
import { Tabs, TabsContent, TabsList, TabsTrigger } from"@/components/ui/tabs"
import { Card, CardContent } from"@/components/ui/card"
import { AlertTriangle, Loader2, Mail, Save, X, Eye, Edit3, FileText, RefreshCw, Info, Copy } from"lucide-react"
import { liaApi, type EmailTemplate, type EmailTemplateCreateRequest, type EmailTemplateUpdateRequest } from"@/services/lia-api"
import { sanitizeEmailHtml } from"@/lib/sanitize"
import { LiaEditor, type Editor } from"@/components/ui/lia-editor"
import {
  TemplateVariable,
  htmlToTiptapContent,
  tiptapContentToHtml,
} from"@/components/ui/lia-editor-variable-extension"
import { useEmailTemplatePreview } from"@/hooks/communication/use-email-template-preview"

interface EmailTemplateFormModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  template?: EmailTemplate | null
}

const AVAILABLE_VARIABLES = [
  { name:"candidate_name", description:"Nome completo do candidato" },
  { name:"candidate_email", description:"Email do candidato" },
  { name:"candidate_phone", description:"Telefone do candidato" },
  { name:"job_title", description:"Título da vaga" },
  { name:"job_department", description:"Departamento da vaga" },
  { name:"job_location", description:"Localização da vaga" },
  { name:"company_name", description:"Nome da empresa" },
  { name:"interview_date", description:"Data da entrevista" },
  { name:"interview_time", description:"Horário da entrevista" },
  { name:"interview_location", description:"Local/link da entrevista" },
  { name:"recruiter_name", description:"Nome do recrutador" },
  { name:"recruiter_email", description:"Email do recrutador" },
  { name:"offer_salary", description:"Salário oferecido" },
  { name:"offer_benefits", description:"Benefícios oferecidos" },
  { name:"start_date", description:"Data de início" },
]

const MOCK_DATA: Record<string, string> = {
  candidate_name:"João Silva",
  candidate_email:"joao.silva@email.com",
  candidate_phone:"(11) 99999-9999",
  job_title:"Desenvolvedor Full Stack",
  job_department:"Tecnologia",
  job_location:"São Paulo, SP",
  company_name:"TechCorp Brasil",
  interview_date:"15 de Janeiro de 2025",
  interview_time:"14:00",
  interview_location:"Sala de Reuniões Virtual - Link: meet.google.com/abc-xyz",
  recruiter_name:"Ana Costa",
  recruiter_email:"ana.costa@techcorp.com.br",
  offer_salary: DEMO_VALUES.OFFER_SALARY_EXAMPLE,
  offer_benefits:"VR, VT, Plano de Saúde, Gympass",
  start_date:"1º de Fevereiro de 2025",
}

const CATEGORY_OPTIONS = [
  { value:"interview", label:"Entrevista" },
  { value:"rejection", label:"Rejeição" },
  { value:"offer", label:"Proposta" },
  { value:"followup", label:"Follow-up" },
]

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const DEFAULT_TEMPLATE = `<h2>Olá, {{candidate_name}}!</h2><p>Escreva aqui o conteúdo do seu email...</p><p>Atenciosamente,<br><strong>{{recruiter_name}}</strong><br>{{company_name}}</p>`

const TEMPLATE_VARIABLE_EXTENSIONS = [TemplateVariable]

export function EmailTemplateFormModal({
  isOpen,
  onClose,
  onSuccess,
  template,
}: EmailTemplateFormModalProps) {
  const t = useTranslations("settings.communication.templates")
  const [activeTab, setActiveTab] = useState("editor")
  const [saving, setSaving] = useState(false)
  const [formData, setFormData] = useState({
    name:"",
    subject:"",
    body_html:"",
    body_text:"",
    category:"" as string,
    cc_emails: [] as string[],
  })
  const [ccInput, setCcInput] = useState("")
  const [ccInputError, setCcInputError] = useState("")

  const isEditing = !!template
  const [editorKey, setEditorKey] = useState(0)
  const editorRef = useRef<Editor | null>(null)

  // GAP-07-006: Real-data preview via backend
  const { preview, missingVariables, isLoading: previewLoading, error: previewError, fetchPreview, reset: resetPreview } = useEmailTemplatePreview()

  useEffect(() => {
    if (isOpen) {
      if (template) {
        setFormData({
          name: template.name,
          subject: template.subject,
          body_html: template.body_html,
          body_text: template.body_text ||"",
          category: template.category ||"",
          cc_emails: template.cc_emails || [],
        })
      } else {
        setFormData({
          name:"",
          subject:"",
          body_html: DEFAULT_TEMPLATE,
          body_text:"",
          category:"",
          cc_emails: [],
        })
      }
      setCcInput("")
      setCcInputError("")
      setActiveTab("editor")
      setEditorKey((k) => k + 1)
      resetPreview()
    }
  }, [isOpen, template, resetPreview])

  const extractVariables = (content: string): string[] => {
    const regex = /\{\{(\w+)\}\}/g
    const matches = content.matchAll(regex)
    const variables = new Set<string>()
    for (const match of matches) {
      variables.add(match[1])
    }
    return Array.from(variables)
  }

  const detectedVariables = useMemo(() => {
    const outputHtml = tiptapContentToHtml(formData.body_html)
    const allContent = formData.subject + outputHtml + formData.body_text
    return extractVariables(allContent)
  }, [formData.subject, formData.body_html, formData.body_text])

  /** Local substitution with MOCK_DATA — used as fallback for new (unsaved) templates */
  const renderLocalPreview = (content: string): string => {
    let rendered = tiptapContentToHtml(content)
    for (const [key, value] of Object.entries(MOCK_DATA)) {
      rendered = rendered.replace(new RegExp(`\\{\\{${key}\\}\\}`,"g"), value)
    }
    return rendered
  }

  /**
   * Fetch preview from backend using MOCK_DATA as sample variables.
   * Only available when editing (template.id exists).
   */
  const handleFetchLivePreview = useCallback(() => {
    if (template?.id) {
      fetchPreview(template.id, MOCK_DATA)
    }
  }, [template?.id, fetchPreview])

  /** Auto-fetch when switching to Preview tab (editing mode only) */
  const handleTabChange = useCallback((tab: string) => {
    setActiveTab(tab)
    if (tab === "preview" && template?.id && !preview && !previewLoading) {
      fetchPreview(template.id, MOCK_DATA)
    }
  }, [template?.id, preview, previewLoading, fetchPreview])

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleAddCcEmail = () => {
    const raw = ccInput.trim()
    if (!raw) return
    const emails = raw.split(/[,;\s]+/).map(e => e.trim()).filter(Boolean)
    const invalid = emails.find(e => !EMAIL_REGEX.test(e))
    if (invalid) {
      setCcInputError(`Email inválido: ${invalid}`)
      return
    }
    const existing = new Set(formData.cc_emails)
    const newEmails = emails.filter(e => !existing.has(e))
    setFormData((prev) => ({ ...prev, cc_emails: [...prev.cc_emails, ...newEmails] }))
    setCcInput("")
    setCcInputError("")
  }

  const handleCcKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      handleAddCcEmail()
    }
  }

  const handleRemoveCcEmail = (email: string) => {
    setFormData((prev) => ({ ...prev, cc_emails: prev.cc_emails.filter(e => e !== email) }))
  }

  const insertVariable = (variableName: string) => {
    const editor = editorRef.current
    if (editor && !editor.isDestroyed) {
      editor.chain().focus().insertVariable(variableName).run()
    }
    setActiveTab("editor")
  }

  const handleSubmit = async () => {
    try {
      setSaving(true)

      if (ccInput.trim()) {
        handleAddCcEmail()
      }

      const outputHtml = tiptapContentToHtml(formData.body_html)
      const variables = extractVariables(
        formData.subject + outputHtml + formData.body_text
      )

      if (isEditing && template) {
        const updateData: EmailTemplateUpdateRequest = {
          name: formData.name,
          subject: formData.subject,
          body_html: outputHtml,
          body_text: formData.body_text || undefined,
          category: (formData.category || undefined) as EmailTemplateUpdateRequest["category"],
          variables,
          cc_emails: formData.cc_emails.length > 0 ? formData.cc_emails : undefined,
        }
        await liaApi.updateEmailTemplate(template.id, updateData)
      } else {
        const createData: EmailTemplateCreateRequest = {
          name: formData.name,
          subject: formData.subject,
          body_html: outputHtml,
          body_text: formData.body_text || undefined,
          category: (formData.category || undefined) as EmailTemplateCreateRequest["category"],
          variables,
          cc_emails: formData.cc_emails.length > 0 ? formData.cc_emails : undefined,
        }
        await liaApi.createEmailTemplate(createData)
      }

      onSuccess()
    } catch (error) {
    } finally {
      setSaving(false)
    }
  }

  const isValid = formData.name.trim() && formData.subject.trim() && formData.body_html.trim()

  const initialContent = useMemo(
    () => htmlToTiptapContent(formData.body_html),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [editorKey]
  )

  /** Determine which subject/body to display in preview */
  const previewSubject = preview ? preview.subject : renderLocalPreview(formData.subject)
  const previewBodyHtml = preview ? preview.body_html : renderLocalPreview(formData.body_html)
  const isLivePreview = !!preview

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent data-testid="email-template-form-modal" className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col rounded-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-lia-text-primary" />
            {isEditing ?"Editar Modelo" :"Novo Modelo de Email"}
          </DialogTitle>
          <DialogDescription className="dark:text-lia-text-tertiary">
            {isEditing
              ?"Atualize as informações do modelo de email"
              :"Crie um novo modelo de email para comunicação com candidatos"}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nome do Template *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                placeholder="Ex: Convite para Entrevista"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="category">Categoria</Label>
              <Select
                value={formData.category}
                onValueChange={(value) => handleInputChange("category", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione uma categoria" />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2 mb-4">
            <Label htmlFor="subject">Assunto do Email *</Label>
            <Input
              id="subject"
              value={formData.subject}
              onChange={(e) => handleInputChange("subject", e.target.value)}
              placeholder="Ex: {{company_name}} - Convite para Entrevista: {{job_title}}"
            />
          </div>

          <div className="space-y-2 mb-4">
            <Label htmlFor="cc-input">{t("ccEmailsLabel")}</Label>
            <div className="space-y-2">
              {formData.cc_emails.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {formData.cc_emails.map((email) => (
                    <Chip
                      key={email}
                      variant="neutral"
                      className="flex items-center gap-1 text-xs"
                    >
                      {email}
                      <button
                        type="button"
                        onClick={() => handleRemoveCcEmail(email)}
                        className="ml-1 rounded-full hover:text-status-error transition-colors motion-reduce:transition-none"
                        aria-label={`Remover ${email}`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Chip>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <Input
                  id="cc-input"
                  value={ccInput}
                  onChange={(e) => { setCcInput(e.target.value); setCcInputError("") }}
                  onKeyDown={handleCcKeyDown}
                  onBlur={handleAddCcEmail}
                  placeholder={t("ccEmailsPlaceholder")}
                  className="flex-1 text-sm"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddCcEmail}
                  className="shrink-0"
                >
                  Adicionar
                </Button>
              </div>
              {ccInputError && (
                <p className="text-xs text-status-error">{ccInputError}</p>
              )}
              <p className="text-xs text-lia-text-tertiary">
                Opcional. Separe múltiplos emails por vírgula ou pressione Enter após cada um.
              </p>
            </div>
          </div>

          <Tabs value={activeTab} onValueChange={handleTabChange} className="flex-1 overflow-hidden flex flex-col">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="editor" className="gap-2">
                <Edit3 className="w-4 h-4" />
                Editor
              </TabsTrigger>
              <TabsTrigger value="preview" className="gap-2">
                <Eye className="w-4 h-4" />
                Preview
              </TabsTrigger>
              <TabsTrigger value="variables" className="gap-2">
                <FileText className="w-4 h-4" />
                Variáveis
              </TabsTrigger>
            </TabsList>

            <div className="flex-1 overflow-y-auto mt-4">
              <TabsContent value="editor" className="h-full m-0" forceMount style={{ display: activeTab ==="editor" ? undefined :"none" }}>
                <div className="space-y-2 h-full">
                  <div className="flex items-center justify-between">
                    <Label>Corpo do Email *</Label>
                    <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
                      <Info className="w-3 h-3 text-lia-text-secondary" />
                      Clique em"Variáveis" para inserir campos dinâmicos
                    </div>
                  </div>
                  <LiaEditor
                    key={editorKey}
                    content={initialContent}
                    onUpdate={(html) => setFormData((prev) => ({ ...prev, body_html: html }))}
                    placeholder="Escreva o conteúdo do email..."
                    toolbar="full"
                    minHeight="280px"
                    extensions={TEMPLATE_VARIABLE_EXTENSIONS}
                    editorRef={editorRef}
                  />
                </div>
              </TabsContent>

              <TabsContent value="preview" className="h-full m-0" data-testid="preview-tab-content">
                <Card className="h-full">
                  <CardContent className="pt-4">
                    <div className="space-y-4">
                      {/* Header: source badge + refresh button */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {isLivePreview ? (
                            <span className="text-xs text-wedo-green font-medium flex items-center gap-1">
                              <Eye className="w-3 h-3" />
                              Preview com dados reais
                            </span>
                          ) : (
                            <span className="text-xs text-lia-text-tertiary">
                              {isEditing ? "Carregando preview..." : "Preview com dados de exemplo"}
                            </span>
                          )}
                        </div>
                        {isEditing && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={handleFetchLivePreview}
                            disabled={previewLoading}
                            data-testid="refresh-preview-button"
                            className="text-xs h-7 px-2"
                          >
                            {previewLoading ? (
                              <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                            ) : (
                              <RefreshCw className="w-3 h-3" />
                            )}
                            <span className="ml-1">Atualizar</span>
                          </Button>
                        )}
                      </div>

                      {/* Missing variables warning */}
                      {missingVariables.length > 0 && (
                        <div
                          className="flex items-start gap-2 p-3 bg-status-warning/10 border border-status-warning/30 rounded-xl"
                          role="alert"
                          data-testid="missing-variables-warning"
                        >
                          <AlertTriangle className="w-4 h-4 text-status-warning shrink-0 mt-0.5" />
                          <div>
                            <p className="text-sm font-medium text-status-warning">
                              Variáveis não preenchidas:
                            </p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {missingVariables.map((v) => (
                                <code key={v} className="text-xs bg-status-warning/20 text-status-warning px-1 rounded">
                                  {`{{${v}}}`}
                                </code>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Error state */}
                      {previewError && (
                        <div className="p-3 bg-status-error/10 border border-status-error/30 rounded-xl text-sm text-status-error">
                          {previewError}
                        </div>
                      )}

                      {/* Loading skeleton */}
                      {previewLoading && (
                        <div className="space-y-3 animate-pulse" aria-live="polite" aria-label="Carregando preview">
                          <div className="h-10 bg-lia-bg-secondary rounded-xl" />
                          <div className="h-40 bg-lia-bg-secondary rounded-xl" />
                        </div>
                      )}

                      {/* Rendered preview */}
                      {!previewLoading && (
                        <>
                          <div className="p-3 bg-lia-bg-secondary rounded-xl">
                            <span className="text-sm font-medium text-lia-text-secondary">Assunto:</span>
                            <p className="text-lia-text-primary" data-testid="preview-subject">{previewSubject}</p>
                          </div>
                          {formData.cc_emails.length > 0 && (
                            <div className="p-3 bg-lia-bg-secondary rounded-xl">
                              <span className="text-sm font-medium text-lia-text-secondary">CC:</span>
                              <p className="text-lia-text-primary text-sm">{formData.cc_emails.join(", ")}</p>
                            </div>
                          )}
                          <div className="border rounded-xl overflow-hidden">
                            <div className="bg-lia-bg-tertiary px-4 py-2 text-sm font-medium text-lia-text-secondary border-b flex items-center gap-2">
                              <Eye className="w-4 h-4" />
                              {isLivePreview ? "Preview com dados reais (via servidor)" : "Preview com dados de exemplo"}
                            </div>
                            <div
                              className="p-4 bg-lia-bg-primary prose prose-sm max-w-none"
                              data-testid="preview-body-html"
                              dangerouslySetInnerHTML={{
                                __html: sanitizeEmailHtml(previewBodyHtml),
                              }}
                            />
                          </div>
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="variables" className="h-full m-0">
                <div className="space-y-4">
                  {detectedVariables.length > 0 && (
                    <Card className="border-wedo-green/30 bg-wedo-green/10">
                      <CardContent className="pt-4">
                        <h4 className="font-medium text-lia-text-secondary mb-2">
                          Variáveis detectadas no template:
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {detectedVariables.map((v) => (
                            <Chip variant="neutral" muted key={v} >
                              {`{{${v}}}`}
                            </Chip>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  <Card>
                    <CardContent className="pt-4">
                      <h4 className="font-medium text-lia-text-primary mb-3">
                        Variáveis disponíveis (clique para inserir no editor):
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {AVAILABLE_VARIABLES.map((variable) => (
                          <button
                            key={variable.name}
                            onClick={() => insertVariable(variable.name)}
                            className="flex items-center justify-between p-2 rounded-xl border hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none text-left"
                          >
                            <div>
                              <code className="text-sm font-mono text-lia-text-primary">
                                {`{{${variable.name}}}`}
                              </code>
                              <p className="text-xs text-lia-text-secondary mt-0.5">
                                {variable.description}
                              </p>
                            </div>
                            <Copy className="w-4 h-4 text-lia-text-secondary" />
                          </button>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-lia-border-default dark:border-lia-border-default bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                    <CardContent className="pt-4">
                      <h4 className="font-medium text-lia-text-primary mb-2">
                        Dados de exemplo para preview:
                      </h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {Object.entries(MOCK_DATA).map(([key, value]) => (
                          <div key={key} className="flex">
                            <span className="font-mono text-lia-text-primary">{key}:</span>
                            <span className="text-lia-text-primary ml-2 truncate">{value}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </div>

        <DialogFooter className="mt-4 border-t border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary dark:border-lia-border-subtle pt-4">
          <Button variant="outline" onClick={onClose} disabled={saving} className="dark:border-lia-border-default dark:hover:bg-lia-bg-inverse">
            <X className="w-4 h-4 mr-2" />
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || saving} className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active">
            {saving ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                Salvando...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {isEditing ?"Atualizar" :"Criar"} Template
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
