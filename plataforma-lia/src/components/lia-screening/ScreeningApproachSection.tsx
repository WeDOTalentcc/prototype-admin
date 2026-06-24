"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MessageSquare, Target, Zap, Star, Copy } from "lucide-react"

interface ApproachStrategy {
  tone: string
  duration: string
  structure: string[]
  tips: string[]
}

interface ScreeningApproachSectionProps {
  approachStrategy: ApproachStrategy
  candidateName: string
  jobTitle: string
  copiedSection: string | null
  onCopy: (text: string, section: string) => void
}

export function ScreeningApproachSection({
  approachStrategy,
  candidateName,
  jobTitle,
  copiedSection,
  onCopy,
}: ScreeningApproachSectionProps) {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold font-sans text-lia-text-primary mb-4">Estratégia de Abordagem</h4>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2 font-sans">
              <MessageSquare className="w-4 h-4 text-lia-text-secondary" />
              Tom e Postura
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-sm font-medium text-lia-text-secondary">Tom</div>
                <div className="text-xs text-lia-text-secondary">{approachStrategy.tone}</div>
              </div>
              <div className="text-center p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                <div className="text-sm font-medium text-status-success dark:text-status-success">Duração</div>
                <div className="text-xs text-status-success dark:text-status-success">{approachStrategy.duration}</div>
              </div>
              <div className="text-center p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md">
                <div className="text-sm font-medium text-lia-text-secondary dark:text-wedo-purple">Formato</div>
                <div className="text-xs text-lia-text-muted dark:text-wedo-purple">Conversa estruturada</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 font-sans">
                <Target className="w-4 h-4 text-status-success" />
                Estrutura da Conversa
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {approachStrategy.structure.map((step, index) => (
                  <div key={`step-${index}`} className="flex items-center gap-3 p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <div className="w-6 h-6 bg-status-success/15 dark:bg-status-success/20 rounded-full flex items-center justify-center text-status-success text-xs font-bold">
                      {index + 1}
                    </div>
                    <span className="text-sm text-lia-text-primary">{step}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2 font-sans">
                <Zap className="w-4 h-4 text-status-warning" />
                Dicas Importantes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {approachStrategy.tips.map((tip, index) => (
                  <div key={`tip-${index}`} className="flex items-start gap-2">
                    <Star className="w-3 h-3 text-status-warning mt-1 flex-shrink-0" />
                    <span className="text-sm text-lia-text-primary">{tip}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2 font-sans">
            <MessageSquare className="w-4 h-4 text-status-success" />
            Script de Abertura
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onCopy(
              `Olá ${candidateName}! Como está? Muito obrigado pelo interesse na nossa vaga de ${jobTitle}.\n\nSou [SEU NOME] da equipe de recrutamento. Esta é uma conversa inicial para nos conhecermos melhor e eu te contar mais sobre a oportunidade.\n\nTem cerca de 20-30 minutos para conversarmos? Perfeito!`,
              "opening"
            )}
            className="gap-2"
          >
            <Copy className="w-3 h-3" />
            {copiedSection === "opening" ? "Copiado!" : "Copiar"}
          </Button>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-status-success/10 dark:bg-status-success/20 rounded-xl">
            <p className="text-sm text-lia-text-primary leading-relaxed">
              &quot;Olá <strong>{candidateName}</strong>! Como está? Muito obrigado pelo interesse na nossa vaga de <strong>{jobTitle}</strong>.
              <br /><br />
              Sou <strong>[SEU NOME]</strong> da equipe de recrutamento. Esta é uma conversa inicial para nos conhecermos melhor e eu te contar mais sobre a oportunidade.
              <br /><br />
              Tem cerca de 20-30 minutos para conversarmos? Perfeito!&quot;
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
