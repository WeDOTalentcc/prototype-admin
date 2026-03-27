"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { VisuallyHidden } from "@radix-ui/react-visually-hidden"
import { 
  Mail, 
  Send, 
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  User
} from "lucide-react"
import { liaApi, type EmailTemplate, type CandidateLocal } from "@/services/lia-api"
import { MessageComposer } from "@/components/communication"

const api = liaApi as any

interface SendEmailModalProps {
  isOpen: boolean
  onClose: () => void
  candidate?: CandidateLocal | null
  onSuccess?: () => void
}

export function SendEmailModal({ isOpen, onClose, candidate, onSuccess }: SendEmailModalProps) {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("")
  const [recipientEmail, setRecipientEmail] = useState("")
  const [recipientName, setRecipientName] = useState("")
  const [sending, setSending] = useState(false)
  const [sendStatus, setSendStatus] = useState<"idle" | "success" | "error">("idle")
  const [errorMessage, setErrorMessage] = useState("")
  const [customVariables, setCustomVariables] = useState<Record<string, string>>({})
  const [editedSubject, setEditedSubject] = useState("")
  const [editedBody, setEditedBody] = useState("")

  useEffect(() => {
    if (isOpen) {
      setSendStatus("idle")
      setErrorMessage("")
      setEditedSubject("")
      setEditedBody("")
      setSelectedTemplateId("")

      if (candidate) {
        setRecipientEmail(candidate.email || "")
        setRecipientName(candidate.name || "")
        setCustomVariables({
          candidate_name: candidate.name || "",
          first_name: candidate.name?.split(" ")[0] || "",
          candidate_email: candidate.email || "",
          candidate_phone: candidate.phone || "",
          job_title: candidate.current_title || "",
          current_company: candidate.current_company || "",
          location: candidate.location_city || "",
          company_name: "WeDO Talent",
          recruiter_name: "Equipe de Recrutamento",
          recruiter_email: "recrutamento@wedotalent.com.br",
          sender_name: "Equipe WeDO",
          sender_title: "Recrutador",
        })
      } else {
        setRecipientEmail("")
        setRecipientName("")
        setCustomVariables({
          company_name: "WeDO Talent",
          recruiter_name: "Equipe de Recrutamento",
          recruiter_email: "recrutamento@wedotalent.com.br",
          sender_name: "Equipe WeDO",
          sender_title: "Recrutador",
        })
      }
    }
  }, [isOpen, candidate])

  const renderPreview = useCallback((content: string): string => {
    let rendered = content
    for (const [key, value] of Object.entries(customVariables)) {
      rendered = rendered.replace(new RegExp(`\\{\\{${key}\\}\\}`, "g"), value || `{{${key}}}`)
    }
    return rendered
  }, [customVariables])

  const handleSubjectChange = useCallback((subject: string) => {
    setEditedSubject(subject)
  }, [])

  const handleMessageChange = useCallback((message: string) => {
    setEditedBody(message)
  }, [])

  const handleTemplateSelect = useCallback((template: any) => {
    setSelectedTemplateId(template.id)
  }, [])

  const handleSend = async () => {
    if (!selectedTemplateId || !recipientEmail) return

    try {
      setSending(true)
      setErrorMessage("")
      
      await api.sendEmail(selectedTemplateId, {
        recipient_email: recipientEmail,
        recipient_name: recipientName,
        candidate_id: candidate?.id,
        variables: customVariables,
        send_immediately: true,
        subject_override: editedSubject || undefined,
        body_override: editedBody || undefined,
      })

      setSendStatus("success")
      
      setTimeout(() => {
        onSuccess?.()
        onClose()
      }, 2000)
    } catch (error: any) {
      console.error("Erro ao enviar email:", error)
      setSendStatus("error")
      setErrorMessage(error.message || "Erro ao enviar email. Tente novamente.")
    } finally {
      setSending(false)
    }
  }

  const isValid = selectedTemplateId && recipientEmail.trim() && recipientEmail.includes("@")

  const candidateContext = useMemo(() => ({
    name: candidate?.name,
    role: candidate?.current_title,
    location: candidate?.location_city,
  }), [candidate])

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent 
        className="max-w-4xl h-[80vh] p-0 gap-0 overflow-hidden bg-white border border-gray-100 rounded-md dark:bg-gray-800 dark:border-gray-700"
       
      >
        <VisuallyHidden>
          <DialogTitle>Enviar Email</DialogTitle>
        </VisuallyHidden>
        
        {sendStatus === "success" ? (
          <div className="flex-1 flex items-center justify-center py-12">
            <div className="text-center">
              <div className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
                <CheckCircle className="w-7 h-7 text-green-600" />
              </div>
              <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-1">
                Email Enviado!
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Enviado para {recipientEmail}
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-md bg-gray-100 flex items-center justify-center">
                  <Mail className="w-3.5 h-3.5 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                    Enviar Email
                  </h2>
                  {candidate && (
                    <p className="text-sm-ui text-gray-600">
                      para {candidate.name}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onClose}
                  className="h-9 px-4 text-sm-ui font-medium border-gray-200 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleSend}
                  disabled={!isValid || sending}
                  size="sm"
                  className="h-9 px-4 text-sm-ui font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                >
                  {sending ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5 mr-1.5" />
                      Enviar
                    </>
                  )}
                </Button>
              </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
              <div className="w-[55%] flex flex-col border-r border-gray-100 overflow-y-auto">
                <div className="p-4">
                  <MessageComposer
                    channel="email"
                    initialSubject={editedSubject}
                    initialMessage={editedBody}
                    onSubjectChange={handleSubjectChange}
                    onMessageChange={handleMessageChange}
                    onTemplateSelect={handleTemplateSelect}
                    showTemplateSelector={true}
                    showLiaAdjust={true}
                    showVariableSelector={true}
                    candidateContext={candidateContext}
                  />
                </div>
              </div>

              <div className="w-[45%] flex flex-col bg-gray-50">
                <div className="px-4 py-3 border-b border-gray-100">
                  <p className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">
                    Preview
                  </p>
                  
                  <div className="bg-white rounded-md border border-gray-100 p-2.5">
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-gray-600">
                        Para:
                      </p>
                      <div className="flex items-center gap-0.5">
                        <button className="p-0.5 hover:bg-gray-50 rounded">
                          <ChevronLeft className="w-3.5 h-3.5 text-gray-500" />
                        </button>
                        <button className="p-0.5 hover:bg-gray-50 rounded">
                          <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
                        </button>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 mt-1.5">
                      <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-gray-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-800 text-xs truncate">
                          {customVariables.candidate_name || "Nome do Candidato"}
                        </p>
                        <p className="text-xs text-gray-600 truncate">
                          {recipientEmail || "email@exemplo.com"}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <ScrollArea className="flex-1">
                  <div className="p-4 space-y-3">
                    <div>
                      <p className="text-xs text-gray-600 mb-1">Assunto</p>
                      <p className="text-xs font-medium text-gray-800">
                        {renderPreview(editedSubject) || "Sem assunto definido"}
                      </p>
                    </div>

                    <div className="border-t border-gray-100 pt-3">
                      <p className="text-xs text-gray-600 mb-2">Mensagem</p>
                      {editedBody ? (
                        <div
                          className="prose prose-sm max-w-none text-gray-800 text-xs leading-relaxed"
                          dangerouslySetInnerHTML={{
                            __html: renderPreview(editedBody).replace(/\n/g, '<br/>'),
                          }}
                        />
                      ) : (
                        <p className="text-xs text-gray-400 italic">
                          Selecione um template ou escreva sua mensagem
                        </p>
                      )}
                    </div>
                  </div>
                </ScrollArea>

                {!recipientEmail && candidate && !candidate.email && (
                  <div className="px-4 py-2 border-t border-gray-100">
                    <div className="flex items-start gap-1.5 p-2 rounded-md bg-wedo-orange/10 border border-wedo-orange/20">
                      <AlertCircle className="w-3.5 h-3.5 text-wedo-orange flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-xs font-medium text-wedo-orange">
                          Email não disponível
                        </p>
                        <p className="text-xs text-gray-600">
                          Candidato sem email cadastrado
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {sendStatus === "error" && (
              <div className="px-4 py-2 border-t border-gray-100 bg-red-50">
                <div className="flex items-center gap-1.5 text-red-700">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span className="text-xs">{errorMessage}</span>
                </div>
              </div>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
