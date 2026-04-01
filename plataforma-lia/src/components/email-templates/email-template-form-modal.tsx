"use client"

import { useState, useEffect, useMemo } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent } from "@/components/ui/card"
import { Mail, Save, X, Eye, Code, FileText, RefreshCw, Info, Copy } from "lucide-react"
import { liaApi, type EmailTemplate, type EmailTemplateCreateRequest, type EmailTemplateUpdateRequest } from "@/services/lia-api"
import { sanitizeEmailHtml } from "@/lib/sanitize"

interface EmailTemplateFormModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  template?: EmailTemplate | null
}

const AVAILABLE_VARIABLES = [
  { name: "candidate_name", description: "Nome completo do candidato" },
  { name: "candidate_email", description: "Email do candidato" },
  { name: "candidate_phone", description: "Telefone do candidato" },
  { name: "job_title", description: "Título da vaga" },
  { name: "job_department", description: "Departamento da vaga" },
  { name: "job_location", description: "Localização da vaga" },
  { name: "company_name", description: "Nome da empresa" },
  { name: "interview_date", description: "Data da entrevista" },
  { name: "interview_time", description: "Horário da entrevista" },
  { name: "interview_location", description: "Local/link da entrevista" },
  { name: "recruiter_name", description: "Nome do recrutador" },
  { name: "recruiter_email", description: "Email do recrutador" },
  { name: "offer_salary", description: "Salário oferecido" },
  { name: "offer_benefits", description: "Benefícios oferecidos" },
  { name: "start_date", description: "Data de início" },
]

const MOCK_DATA: Record<string, string> = {
  candidate_name: "João Silva",
  candidate_email: "joao.silva@email.com",
  candidate_phone: "(11) 99999-9999",
  job_title: "Desenvolvedor Full Stack",
  job_department: "Tecnologia",
  job_location: "São Paulo, SP",
  company_name: "TechCorp Brasil",
  interview_date: "15 de Janeiro de 2025",
  interview_time: "14:00",
  interview_location: "Sala de Reuniões Virtual - Link: meet.google.com/abc-xyz",
  recruiter_name: "Ana Costa",
  recruiter_email: "ana.costa@techcorp.com.br",
  offer_salary: "R$ 12.000,00",
  offer_benefits: "VR, VT, Plano de Saúde, Gympass",
  start_date: "1º de Fevereiro de 2025",
}

const CATEGORY_OPTIONS = [
  { value: "interview", label: "Entrevista" },
  { value: "rejection", label: "Rejeição" },
  { value: "offer", label: "Proposta" },
  { value: "followup", label: "Follow-up" },
]

export function EmailTemplateFormModal({
  isOpen,
  onClose,
  onSuccess,
  template,
}: EmailTemplateFormModalProps) {
  const [activeTab, setActiveTab] = useState("editor")
  const [saving, setSaving] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    subject: "",
    body_html: "",
    body_text: "",
    category: "" as string,
  })

  const isEditing = !!template

  useEffect(() => {
    if (isOpen) {
      if (template) {
        setFormData({
          name: template.name,
          subject: template.subject,
          body_html: template.body_html,
          body_text: template.body_text || "",
          category: template.category || "",
        })
      } else {
        setFormData({
          name: "",
          subject: "",
          body_html: getDefaultTemplate(),
          body_text: "",
          category: "",
        })
      }
      setActiveTab("editor")
    }
  }, [isOpen, template])

  const getDefaultTemplate = () => {
    return `<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <h2 style="color: #333;">Olá, {{candidate_name}}!</h2>
  
  <p style="color: #555; line-height: 1.6;">
    Escreva aqui o conteúdo do seu email...
  </p>
  
  <p style="color: #555; line-height: 1.6;">
    Atenciosamente,<br>
    <strong>{{recruiter_name}}</strong><br>
    {{company_name}}
  </p>
</div>`
  }

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
    const allContent = formData.subject + formData.body_html + formData.body_text
    return extractVariables(allContent)
  }, [formData.subject, formData.body_html, formData.body_text])

  const renderPreview = (content: string): string => {
    let rendered = content
    for (const [key, value] of Object.entries(MOCK_DATA)) {
      rendered = rendered.replace(new RegExp(`\\{\\{${key}\\}\\}`, "g"), value)
    }
    return rendered
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const insertVariable = (variableName: string) => {
    const textarea = document.getElementById("body_html") as HTMLTextAreaElement
    if (textarea) {
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const text = formData.body_html
      const before = text.substring(0, start)
      const after = text.substring(end)
      const newText = before + `{{${variableName}}}` + after

      setFormData((prev) => ({ ...prev, body_html: newText }))

      setTimeout(() => {
        textarea.focus()
        const newCursorPos = start + variableName.length + 4
        textarea.setSelectionRange(newCursorPos, newCursorPos)
      }, 0)
    }
  }

  const handleSubmit = async () => {
    try {
      setSaving(true)

      const variables = extractVariables(
        formData.subject + formData.body_html + formData.body_text
      )

      if (isEditing && template) {
        const updateData: EmailTemplateUpdateRequest = {
          name: formData.name,
          subject: formData.subject,
          body_html: formData.body_html,
          body_text: formData.body_text || undefined,
          // @ts-ignore TODO: fix type — Type 'string | undefined' is not assignable to type '"interview" | "rejection" |
          category: formData.category || undefined,
          variables,
        }
        await liaApi.updateEmailTemplate(template.id, updateData)
      } else {
        const createData: EmailTemplateCreateRequest = {
          name: formData.name,
          subject: formData.subject,
          body_html: formData.body_html,
          body_text: formData.body_text || undefined,
          // @ts-ignore TODO: fix type — Type 'string | undefined' is not assignable to type '"interview" | "rejection" |
          category: formData.category || undefined,
          variables,
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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col rounded-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-lia-text-primary" />
            {isEditing ? "Editar Template" : "Novo Template de Email"}
          </DialogTitle>
          <DialogDescription className="dark:text-lia-text-tertiary">
            {isEditing
              ? "Atualize as informações do template de email"
              : "Crie um novo template de email para comunicação com candidatos"}
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

          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden flex flex-col">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="editor" className="gap-2">
                <Code className="w-4 h-4" />
                Editor HTML
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
              <TabsContent value="editor" className="h-full m-0">
                <div className="space-y-2 h-full">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="body_html">Corpo do Email (HTML) *</Label>
                    <div className="flex items-center gap-2 text-xs lia-text-base">
                      <Info className="w-3 h-3 lia-text-base" />
                      Use {`{{variavel}}`} para inserir variáveis
                    </div>
                  </div>
                  <Textarea
                    id="body_html"
                    value={formData.body_html}
                    onChange={(e) => handleInputChange("body_html", e.target.value)}
                    placeholder="<div>...</div>"
                    className="font-mono text-sm min-h-content-md"
                    rows={15}
                  />
                </div>
              </TabsContent>

              <TabsContent value="preview" className="h-full m-0">
                <Card className="h-full">
                  <CardContent className="pt-4">
                    <div className="space-y-4">
                      <div className="p-3 bg-gray-50 rounded-md">
                        <span className="text-sm font-medium lia-text-base">Assunto:</span>
                        <p className="text-lia-text-primary">{renderPreview(formData.subject)}</p>
                      </div>
                      <div className="border rounded-md overflow-hidden">
                        <div className="bg-gray-100 px-4 py-2 text-sm font-medium lia-text-base border-b flex items-center gap-2">
                          <Eye className="w-4 h-4" />
                          Preview com dados de exemplo
                        </div>
                        <div
                          className="p-4 bg-lia-bg-primary prose prose-sm max-w-none"
                          dangerouslySetInnerHTML={{
                            __html: sanitizeEmailHtml(renderPreview(formData.body_html)),
                          }}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="variables" className="h-full m-0">
                <div className="space-y-4">
                  {detectedVariables.length > 0 && (
                    <Card className="border-wedo-green/30 bg-wedo-green/10">
                      <CardContent className="pt-4">
                        <h4 className="font-medium text-wedo-green mb-2">
                          Variáveis detectadas no template:
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {detectedVariables.map((v) => (
                            <Badge key={v} className="bg-wedo-green/15 text-wedo-green">
                              {`{{${v}}}`}
                            </Badge>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  <Card>
                    <CardContent className="pt-4">
                      <h4 className="font-medium text-lia-text-primary mb-3">
                        Variáveis disponíveis (clique para copiar):
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {AVAILABLE_VARIABLES.map((variable) => (
                          <button
                            key={variable.name}
                            onClick={() => insertVariable(variable.name)}
                            className="flex items-center justify-between p-2 rounded-md border hover:bg-gray-50 transition-colors motion-reduce:transition-none text-left"
                          >
                            <div>
                              <code className="text-sm font-mono text-lia-text-primary">
                                {`{{${variable.name}}}`}
                              </code>
                              <p className="text-xs lia-text-base mt-0.5">
                                {variable.description}
                              </p>
                            </div>
                            <Copy className="w-4 h-4 lia-text-base" />
                          </button>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-lia-border-default dark:border-lia-border-default bg-gray-100 dark:bg-lia-bg-secondary">
                    <CardContent className="pt-4">
                      <h4 className="font-medium text-lia-text-primary mb-2">
                        Dados de exemplo para preview:
                      </h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {Object.entries(MOCK_DATA).map(([key, value]) => (
                          <div key={key} className="flex">
                            <span className="font-mono text-lia-text-primary">{key}:</span>
                            <span className="text-lia-text-primary dark:text-lia-text-primary ml-2 truncate">{value}</span>
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

        <DialogFooter className="mt-4 border-t border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary dark:border-lia-border-subtle pt-4">
          <Button variant="outline" onClick={onClose} disabled={saving} className="dark:border-lia-border-default dark:text-lia-text-secondary dark:hover:bg-gray-700">
            <X className="w-4 h-4 mr-2" />
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || saving} className="bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200">
            {saving ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                Salvando...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {isEditing ? "Atualizar" : "Criar"} Template
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
