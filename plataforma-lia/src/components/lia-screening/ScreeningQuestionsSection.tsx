"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { CheckCircle, Edit, Target, Copy } from"lucide-react"

interface ScreeningQuestion {
  category: string
  questions: unknown[]
  purpose: string
  isWSI?: boolean
}

interface ScreeningQuestionsSectionProps {
  screeningQuestions: ScreeningQuestion[]
  copiedSection: string | null
  onCopy: (text: string, section: string) => void
}

export function ScreeningQuestionsSection({ screeningQuestions, copiedSection, onCopy }: ScreeningQuestionsSectionProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h4 className="text-lg font-semibold text-lia-text-primary">Perguntas de Triagem</h4>
        <Button variant="outline" size="sm" className="gap-2">
          <Edit className="w-3 h-3" />
          Personalizar
        </Button>
      </div>

      <div className="space-y-6">
        {screeningQuestions.map((section, sectionIndex) => (
          <Card key={sectionIndex}>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <Target className="w-4 h-4 text-lia-text-secondary" />
                {section.category}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Chip density="relaxed" variant="neutral" >
                  {section.questions.length} perguntas
                </Chip>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onCopy(
                    section.questions.map(q => String(q)).join('\n'),
                    `questions-${sectionIndex}`
                  )}
                  className="gap-1 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                >
                  <Copy className="w-3 h-3" />
                  {copiedSection === `questions-${sectionIndex}` ? 'Copiado!' : 'Copiar'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="p-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl text-xs text-lia-text-secondary">
                  <strong>Objetivo:</strong> {section.purpose}
                </div>
                <div className="space-y-2">
                  {section.questions.map((question: unknown, questionIndex: number) => (
                    <div key={questionIndex} className="flex items-start gap-3 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
                      <div className="w-6 h-6 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full flex items-center justify-center text-lia-text-secondary text-xs font-bold flex-shrink-0">
                        {questionIndex + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-lia-text-primary">{String(question)}</p>
                        <textarea
                          placeholder="Anotações da resposta..."
                          className="w-full mt-2 p-2 border border-lia-border-subtle dark:border-lia-border-default rounded-xl text-xs bg-lia-bg-secondary dark:bg-lia-bg-secondary"
                          rows={2}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-status-success" />
            Avaliação Final
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                Recomendação Geral
              </label>
              <select className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-xl text-sm">
                <option value="">Selecione...</option>
                <option value="aprovado">✅ Aprovado - Prosseguir</option>
                <option value="condicional">⚠️ Aprovado com ressalvas</option>
                <option value="reprovado">❌ Não aprovado</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">
                Nível de Confiança
              </label>
              <select className="w-full p-2 border border-lia-border-default dark:border-lia-border-default rounded-xl text-sm">
                <option value="">Selecione...</option>
                <option value="alta">🔥 Alta confiança</option>
                <option value="media">🎯 Média confiança</option>
                <option value="baixa">⚡ Baixa confiança</option>
              </select>
            </div>
          </div>
          <div className="mt-4">
            <label className="text-sm font-medium text-lia-text-primary mb-2 block">
              Observações e Próximos Passos
            </label>
            <textarea
              placeholder="Resumo da conversa, pontos de atenção, recomendações para próximas etapas..."
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl text-sm"
              rows={4}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
