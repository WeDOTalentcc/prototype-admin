"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Copy, Edit, Heart, CheckCircle, Clock, Star, Brain } from "lucide-react"

interface FeedbackStrategy {
  timing: {
    approved: string
    rejected: string
  }
  approvedTemplate: {
    subject: string
    message: string
  }
  rejectedTemplate: {
    subject: string
    message: string
  }
  feedbackGuidelines: string[]
}

interface ScreeningFeedbackSectionProps {
  feedbackStrategy: FeedbackStrategy
  copiedSection: string | null
  onCopy: (text: string, section: string) => void
}

export function ScreeningFeedbackSection({ feedbackStrategy, copiedSection, onCopy }: ScreeningFeedbackSectionProps) {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold text-lia-text-primary mb-4">Estratégia de Feedback</h4>
        <p className="text-sm text-lia-text-secondary mb-6">
          Diretrizes para fornecer feedback construtivo e manter relacionamento positivo com todos os candidatos
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Clock className="w-4 h-4 text-lia-text-secondary" />
            Timeline de Feedback
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-status-success/10 dark:bg-status-success/20 rounded-xl border border-status-success/30">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-4 h-4 text-status-success" />
                <span className="font-medium text-status-success dark:text-status-success">Candidatos Aprovados</span>
              </div>
              <p className="text-sm text-status-success dark:text-status-success">{feedbackStrategy.timing.approved}</p>
            </div>
            <div className="p-4 bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded-xl border border-wedo-orange/30">
              <div className="flex items-center gap-2 mb-2">
                <Heart className="w-4 h-4 text-wedo-orange" />
                <span className="font-medium text-wedo-orange-text dark:text-wedo-orange">Candidatos Não Selecionados</span>
              </div>
              <p className="text-sm text-wedo-orange-text dark:text-wedo-orange">{feedbackStrategy.timing.rejected}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-status-success" />
            Template - Candidatos Aprovados
          </CardTitle>
          <Button variant="outline" size="sm" onClick={() => onCopy(`Assunto: ${feedbackStrategy.approvedTemplate.subject}\n\n${feedbackStrategy.approvedTemplate.message}`, 'approved-template')} className="gap-2">
            <Copy className="w-3 h-3" />{copiedSection === 'approved-template' ? 'Copiado!' : 'Copiar'}
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-lia-text-secondary">Assunto:</label>
              <div className="p-2 bg-status-success/10 dark:bg-status-success/20 rounded-md text-sm text-status-success dark:text-status-success">{feedbackStrategy.approvedTemplate.subject}</div>
            </div>
            <div>
              <label className="text-xs font-medium text-lia-text-secondary">Mensagem:</label>
              <div className="p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md text-sm text-status-success dark:text-status-success whitespace-pre-line">{feedbackStrategy.approvedTemplate.message}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Heart className="w-4 h-4 text-wedo-orange" />
            Template - Feedback Construtivo
          </CardTitle>
          <Button variant="outline" size="sm" onClick={() => onCopy(`Assunto: ${feedbackStrategy.rejectedTemplate.subject}\n\n${feedbackStrategy.rejectedTemplate.message}`, 'rejected-template')} className="gap-2">
            <Copy className="w-3 h-3" />{copiedSection === 'rejected-template' ? 'Copiado!' : 'Copiar'}
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-lia-text-secondary">Assunto:</label>
              <div className="p-2 bg-wedo-orange/10 rounded-md text-sm text-wedo-orange-text">{feedbackStrategy.rejectedTemplate.subject}</div>
            </div>
            <div>
              <label className="text-xs font-medium text-lia-text-secondary">Mensagem:</label>
              <div className="p-3 bg-wedo-orange/10 rounded-md text-sm text-wedo-orange-text whitespace-pre-line">{feedbackStrategy.rejectedTemplate.message}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Star className="w-4 h-4 text-status-warning" />
            Diretrizes para Feedback Construtivo
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {feedbackStrategy.feedbackGuidelines.map((guideline, index) => (
              <div key={`fg-${index}`} className="flex items-start gap-3 p-3 bg-status-warning/10 rounded-md">
                <Star className="w-4 h-4 text-status-warning mt-0.5" />
                <span className="text-sm text-status-warning dark:text-status-warning">{guideline}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Edit className="w-4 h-4 text-wedo-purple" />
            Formulário de Feedback Personalizado
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">Pontos Fortes Identificados</label>
              <textarea placeholder="Ex: Excelente comunicação, conhecimento técnico sólido em React..." className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl text-sm" rows={3} />
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">Áreas de Desenvolvimento Sugeridas</label>
              <textarea placeholder="Ex: Aprofundar conhecimentos em TypeScript, ganhar experiência em liderança..." className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl text-sm" rows={3} />
            </div>
            <div className="flex gap-3">
              <Button className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active">Gerar Feedback Personalizado</Button>
              <Button variant="outline" className="gap-2">
                <Brain className="w-4 h-4 text-wedo-cyan-text" />Sugerir
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
