"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState, useEffect } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from"@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from"@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from"@/components/ui/dialog"
import {
  Mail, Plus, Search, MoreVertical, Edit, Copy, Trash2, Eye,
  Calendar, RefreshCw, Filter, FileText
} from"lucide-react"
import { liaApi, type EmailTemplate } from"@/services/lia-api"
import { EmailTemplateFormModal } from"./email-template-form-modal"
import { sanitizeEmailHtml } from"@/lib/sanitize"

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  interview: { label:"Entrevista", color:"-dark dark:bg-wedo-cyan/15 dark:text-wedo-cyan" },
  rejection: { label:"Rejeição", color:"bg-lia-bg-tertiary text-lia-text-primary" },
  offer: { label:"Proposta", color:"" },
  followup: { label:"Follow-up", color:"bg-lia-bg-tertiary text-lia-text-primary" },
  screening: { label:"Triagem", color:"" },
}

const DEFAULT_TEMPLATES: EmailTemplate[] = [
  {
    id: 'default-offer-sent',
    name: 'Proposta Salarial Enviada',
    subject: 'Proposta de Trabalho - {{job_title}} na {{company_name}}',
    body_html: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6; max-width: 600px; margin: 0 auto;">
  <div style="text-align: center; padding: 24px; background: linear-gradient(135deg, #111827 0%, #1F2937 100%); border-radius: 8px 8px 0 0;">
    <h1 style="color: white; margin: 0; font-size: 24px;">Proposta de Trabalho</h1>
  </div>
  <div style="padding: 24px; background: white; border: 1px solid #D4D4D4; border-top: none;">
    <p>Prezado(a) <strong>{{candidate_name}}</strong>,</p>
    <p>É com grande satisfação que formalizamos nossa proposta para a posição de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>.</p>
    <div style="background: #F0F9FA; border: 2px solid #999999; border-radius: 8px; padding: 20px; margin: 24px 0; text-align: center;">
      <p style="margin: 0 0 8px 0; font-size: 14px; color: #2D2D2D;">Remuneração Mensal</p>
      <p style="margin: 0; font-size: 32px; font-weight: 700; color: #1F2937;">{{salary}}</p>
    </div>
    <table style="width: 100%; border-collapse: collapse;">
      <tr><td style="padding: 12px; background: #F9FAFB; border-bottom: 1px solid #D4D4D4;"><strong>Data de Início</strong></td><td style="padding: 12px; border-bottom: 1px solid #D4D4D4;">{{start_date}}</td></tr>
      <tr><td style="padding: 12px; background: #F9FAFB; border-bottom: 1px solid #D4D4D4;"><strong>Tipo de Contrato</strong></td><td style="padding: 12px; border-bottom: 1px solid #D4D4D4;">{{contract_type}}</td></tr>
      <tr><td style="padding: 12px; background: #F9FAFB;"><strong>Modelo de Trabalho</strong></td><td style="padding: 12px;">{{work_model}}</td></tr>
    </table>
    <div style="background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 16px; margin: 24px 0;">
      <strong>Prazo para Resposta:</strong> {{response_deadline}}
    </div>
    <p>Atenciosamente,<br/><strong>{{recruiter_name}}</strong><br/>{{company_name}}</p>
  </div>
</div>`,
    category: 'offer',
    variables: ['candidate_name', 'job_title', 'company_name', 'salary', 'start_date', 'contract_type', 'work_model', 'response_deadline', 'recruiter_name'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'default-offer-reminder',
    name: 'Lembrete: Proposta Pendente',
    subject: 'Lembrete: Sua proposta de trabalho aguarda resposta - {{job_title}}',
    body_html: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  <p>Sua proposta para a posição de <strong>{{job_title}}</strong> ainda aguarda resposta.</p>
  <div style="background: #F0F9FA; border: 1px solid #999999; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
    <p style="font-size: 24px; font-weight: 700; color: #1F2937;">{{salary}}</p>
    <p style="color: #374151;">Início: {{start_date}}</p>
  </div>
  <p>O prazo para resposta é <strong>{{response_deadline}}</strong>.</p>
  <p>Atenciosamente,<br/><strong>{{recruiter_name}}</strong><br/>{{company_name}}</p>
</div>`,
    category: 'offer',
    variables: ['candidate_name', 'job_title', 'salary', 'start_date', 'response_deadline', 'recruiter_name', 'company_name'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'default-offer-accepted',
    name: 'Confirmação: Proposta Aceita',
    subject: 'Bem-vindo(a) à {{company_name}}! Próximos passos',
    body_html: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <div style="text-align: center; padding: 24px; background: linear-gradient(135deg, #111827 0%, #1F2937 100%); border-radius: 8px; margin-bottom: 20px;">
    <span style="font-size: 48px;">🎉</span>
    <h2 style="color: white; margin: 10px 0 0 0;">Bem-vindo(a) à equipe!</h2>
  </div>
  <p>Prezado(a) <strong>{{candidate_name}}</strong>,</p>
  <p>Confirmamos sua aceitação da proposta para <strong>{{job_title}}</strong>!</p>
  <p>Sua jornada na <strong>{{company_name}}</strong> começa em <strong>{{start_date}}</strong>.</p>
  <div style="background: #F0F9FA; border-left: 4px solid #999999; padding: 16px; margin: 20px 0;">
    <strong>Próximos Passos:</strong>
    <ol><li>Contrato formal em até 2 dias úteis</li><li>Contato do RH para onboarding</li><li>Documentação necessária</li></ol>
  </div>
  <p>Atenciosamente,<br/><strong>{{recruiter_name}}</strong><br/>{{company_name}}</p>
</div>`,
    category: 'offer',
    variables: ['candidate_name', 'job_title', 'company_name', 'start_date', 'recruiter_name'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'default-screening-invite',
    name: 'Convite para Triagem por Voz',
    subject: 'Próximo passo: Triagem por Voz para {{job_title}}',
    body_html: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  <p>Parabéns por avançar no processo seletivo para <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>!</p>
  <p>O próximo passo é uma triagem por voz rápida (5-7 minutos).</p>
  <div style="background: #F0F9FA; border-left: 4px solid #999999; padding: 16px; margin: 20px 0;">
    <strong style="color: #374151;">Para iniciar sua triagem:</strong>
    <ol><li>Acesse o link: <a href="{{screening_link}}" style="color: #374151;">{{screening_link}}</a></li><li>Ambiente silencioso</li><li>Responda às perguntas com calma</li></ol>
  </div>
  <p>Atenciosamente,<br/><strong>{{recruiter_name}}</strong><br/>{{company_name}}</p>
</div>`,
    category: 'screening',
    variables: ['candidate_name', 'job_title', 'company_name', 'screening_link', 'recruiter_name'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'default-interview-scheduled',
    name: 'Entrevista em Vídeo Agendada',
    subject: 'Entrevista confirmada: {{job_title}} em {{interview_date}}',
    body_html: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  <p>Sua entrevista em vídeo para <strong>{{job_title}}</strong> foi confirmada!</p>
  <div style="background: #F0F9FA; border: 2px solid #999999; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
    <p style="font-size: 14px; color: #2D2D2D;">Data e Horário</p>
    <p style="font-size: 20px; font-weight: 700; color: #1F2937;">{{interview_date}} às {{interview_time}}</p>
    <a href="{{interview_link}}" style="display: inline-block; background: #111827; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin-top: 12px;">Acessar Entrevista</a>
  </div>
  <p>Atenciosamente,<br/><strong>{{recruiter_name}}</strong><br/>{{company_name}}</p>
</div>`,
    category: 'interview',
    variables: ['candidate_name', 'job_title', 'interview_date', 'interview_time', 'interview_link', 'recruiter_name', 'company_name'],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
]

export function EmailTemplatesManager() {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('email-template-preview', isPreviewModalOpen)
  useLiaModalTracking('email-template-delete', isDeleteModalOpen)

  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [categoryFilter, setCategoryFilter] = useState<string>("all")
  const [isFormModalOpen, setIsFormModalOpen] = useState(false)
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null)
  const [templateToDelete, setTemplateToDelete] = useState<EmailTemplate | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    loadTemplates()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryFilter])

  const loadTemplates = async () => {
    try {
      setLoading(true)
      const category = categoryFilter ==="all" ? undefined : categoryFilter
      const response = await liaApi.listEmailTemplates(category)
      const apiTemplates = response.items || []
      
      if (apiTemplates.length === 0) {
        const filteredDefaults = category 
          ? DEFAULT_TEMPLATES.filter(t => t.category === category)
          : DEFAULT_TEMPLATES
        setTemplates(filteredDefaults)
      } else {
        setTemplates(apiTemplates)
      }
    } catch (error) {
      const category = categoryFilter ==="all" ? undefined : categoryFilter
      const filteredDefaults = category 
        ? DEFAULT_TEMPLATES.filter(t => t.category === category)
        : DEFAULT_TEMPLATES
      setTemplates(filteredDefaults)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateTemplate = () => {
    setSelectedTemplate(null)
    setIsFormModalOpen(true)
  }

  const handleEditTemplate = (template: EmailTemplate) => {
    setSelectedTemplate(template)
    setIsFormModalOpen(true)
  }

  const handleDuplicateTemplate = async (template: EmailTemplate) => {
    try {
      await liaApi.createEmailTemplate({
        name: `${template.name} (Cópia)`,
        subject: template.subject,
        body_html: template.body_html,
        body_text: template.body_text,
        category: template.category,
        variables: template.variables,
      })
      loadTemplates()
    } catch (error) {
    }
  }

  const handleDeleteTemplate = async () => {
    if (!templateToDelete) return

    try {
      setDeleting(true)
      await liaApi.deleteEmailTemplate(templateToDelete.id)
      setIsDeleteModalOpen(false)
      setTemplateToDelete(null)
      loadTemplates()
    } catch (error) {
    } finally {
      setDeleting(false)
    }
  }

  const handlePreviewTemplate = (template: EmailTemplate) => {
    setSelectedTemplate(template)
    setIsPreviewModalOpen(true)
  }

  const handleFormClose = () => {
    setIsFormModalOpen(false)
    setSelectedTemplate(null)
  }

  const handleFormSuccess = () => {
    setIsFormModalOpen(false)
    setSelectedTemplate(null)
    loadTemplates()
  }

  const filteredTemplates = templates.filter((template) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      template.name.toLowerCase().includes(query) ||
      template.subject.toLowerCase().includes(query)
    )
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pt-BR", {
      day:"2-digit",
      month:"short",
      year:"numeric",
    })
  }

  return (
    <div data-testid="email-templates-manager" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-sans font-semibold text-lia-text-primary">Modelos de Email</h2>
          <p className="text-lia-text-secondary mt-1">
            Gerencie os templates de email para comunicação com candidatos
          </p>
        </div>
        <Button onClick={handleCreateTemplate} className="gap-2">
          <Plus className="w-4 h-4" />
          Novo Modelo
        </Button>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
          <Input
            placeholder="Buscar modelos..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-48">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue placeholder="Categoria" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as categorias</SelectItem>
            <SelectItem value="interview">Entrevista</SelectItem>
            <SelectItem value="rejection">Rejeição</SelectItem>
            <SelectItem value="offer">Proposta</SelectItem>
            <SelectItem value="followup">Follow-up</SelectItem>
            <SelectItem value="screening">Triagem</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" size="icon" onClick={loadTemplates} disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ?"animate-spin motion-reduce:animate-none" :""}`} />
        </Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse motion-reduce:animate-none">
              <CardContent className="pt-6">
                <div className="h-4 bg-lia-interactive-active rounded-md w-3/4 mb-3" />
                <div className="h-3 bg-lia-interactive-active rounded-md w-full mb-2" />
                <div className="h-3 bg-lia-interactive-active rounded-md w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredTemplates.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-12">
            <div className="text-center">
              <FileText className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
              <h3 className="text-lg font-medium text-lia-text-primary mb-2">
                {searchQuery || categoryFilter !=="all"
                  ?"Nenhum modelo encontrado"
                  :"Nenhum modelo cadastrado"}
              </h3>
              <p className="text-lia-text-secondary mb-4">
                {searchQuery || categoryFilter !=="all"
                  ?"Tente ajustar os filtros de busca"
                  :"Crie seu primeiro modelo de email para começar"}
              </p>
              {!searchQuery && categoryFilter ==="all" && (
                <Button onClick={handleCreateTemplate}>
                  <Plus className="w-4 h-4 mr-2" />
                  Criar Template
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTemplates.map((template) => (
            <Card
              key={template.id}
              className="hover:transition-shadow cursor-pointer group"
            >
              <CardContent className="pt-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Mail className="w-4 h-4 text-lia-text-secondary flex-shrink-0" />
                      <h3 className="font-medium text-lia-text-primary truncate">
                        {template.name}
                      </h3>
                    </div>
                    {template.category && (
                      <Chip variant="neutral" muted
                        className={`text-xs ${
 CATEGORY_LABELS[template.category]?.color ||"bg-lia-bg-tertiary text-lia-text-primary"
                        }`}
                      >
                        {CATEGORY_LABELS[template.category]?.label || template.category}
                      </Chip>
                    )}
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handlePreviewTemplate(template)}>
                        <Eye className="w-4 h-4 mr-2" />
                        Visualizar
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleEditTemplate(template)}>
                        <Edit className="w-4 h-4 mr-2" />
                        Editar
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleDuplicateTemplate(template)}>
                        <Copy className="w-4 h-4 mr-2" />
                        Duplicar
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => {
                          setTemplateToDelete(template)
                          setIsDeleteModalOpen(true)
                        }}
                        className="text-status-error"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Excluir
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <p className="text-sm text-lia-text-secondary mb-3 line-clamp-2">
                  <span className="font-medium">Assunto:</span> {template.subject}
                </p>

                {template.variables && template.variables.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {template.variables.slice(0, 3).map((variable) => (
                      <Chip density="relaxed" key={variable} variant="neutral" >
                        {`{{${variable}}}`}
                      </Chip>
                    ))}
                    {template.variables.length > 3 && (
                      <Chip density="relaxed" variant="neutral" >
                        +{template.variables.length - 3}
                      </Chip>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-lia-text-secondary pt-4">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {formatDate(template.updated_at)}
                  </div>
                  <Chip
                    variant="neutral"
                    muted
                    className="text-xs"
                  >
                    {template.is_active ?"Ativo" :"Inativo"}
                  </Chip>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <EmailTemplateFormModal
        isOpen={isFormModalOpen}
        onClose={handleFormClose}
        onSuccess={handleFormSuccess}
        template={selectedTemplate}
      />

      <Dialog open={isPreviewModalOpen} onOpenChange={setIsPreviewModalOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5" />
              Preview: {selectedTemplate?.name}
            </DialogTitle>
            <DialogDescription>
              Visualização do modelo de email
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto">
            <div className="space-y-4">
              <div className="p-3 bg-lia-bg-secondary rounded-xl">
                <span className="text-sm font-medium text-lia-text-secondary">Assunto:</span>
                <p className="text-lia-text-primary">{selectedTemplate?.subject}</p>
              </div>
              <div className="border rounded-xl overflow-hidden">
                <div className="bg-lia-bg-tertiary px-4 py-2 text-sm font-medium text-lia-text-secondary border-b">
                  Corpo do Email (HTML)
                </div>
                <div
                  className="p-4 bg-lia-bg-primary prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: sanitizeEmailHtml(selectedTemplate?.body_html ||""),
                  }}
                />
              </div>
              {selectedTemplate?.variables && selectedTemplate.variables.length > 0 && (
                <div className="p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
                  <span className="text-sm font-medium text-lia-text-secondary">Variáveis:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {selectedTemplate.variables.map((v) => (
                      <Chip key={v} variant="neutral" className="bg-lia-bg-primary">
                        {`{{${v}}}`}
                      </Chip>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPreviewModalOpen(false)}>
              Fechar
            </Button>
            <Button
              onClick={() => {
                setIsPreviewModalOpen(false)
                handleEditTemplate(selectedTemplate!)
              }}
            >
              <Edit className="w-4 h-4 mr-2" />
              Editar Modelo
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isDeleteModalOpen} onOpenChange={setIsDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-status-error">Excluir Template</DialogTitle>
            <DialogDescription>
              Tem certeza que deseja excluir o modelo"{templateToDelete?.name}"? Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsDeleteModalOpen(false)
                setTemplateToDelete(null)
              }}
              disabled={deleting}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteTemplate}
              disabled={deleting}
            >
              {deleting ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                  Excluindo...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Excluir
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
