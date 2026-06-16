"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { CheckCircle, Clock, ChevronRight } from"lucide-react"

export function ScreeningTimelineSection() {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold text-lia-text-primary mb-4">Timeline do Processo</h4>
        <p className="text-sm text-lia-text-secondary mb-6">
          Cronograma sugerido para execução eficiente da triagem e próximos passos
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Clock className="w-4 h-4 text-lia-text-secondary" />
            Cronograma de Execução
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full flex items-center justify-center text-lia-text-secondary text-sm font-bold">
                1
              </div>
              <div className="flex-1">
                <div className="font-medium text-lia-text-primary">Preparação (5 min antes)</div>
                <p className="text-sm text-lia-text-secondary">Revisar currículo, preparar perguntas específicas, configurar ambiente</p>
              </div>
              <Chip density="relaxed" variant="neutral" >5 min</Chip>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-status-success/15 dark:bg-status-success/20 rounded-full flex items-center justify-center text-status-success text-sm font-bold">
                2
              </div>
              <div className="flex-1">
                <div className="font-medium text-lia-text-primary">Triagem (20-30 min)</div>
                <p className="text-sm text-lia-text-secondary">Execução da conversa seguindo roteiro estruturado</p>
              </div>
              <Chip density="relaxed" variant="neutral" >25 min</Chip>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-wedo-purple/15 dark:bg-wedo-purple/20 rounded-full flex items-center justify-center text-wedo-purple-text text-sm font-bold">
                3
              </div>
              <div className="flex-1">
                <div className="font-medium text-lia-text-primary">Avaliação (5-10 min após)</div>
                <p className="text-sm text-lia-text-secondary">Análise das respostas, decisão e anotações</p>
              </div>
              <Chip density="relaxed" variant="neutral" >10 min</Chip>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-wedo-orange/15 dark:bg-wedo-orange/10/20 rounded-full flex items-center justify-center text-wedo-orange-text text-sm font-bold">
                4
              </div>
              <div className="flex-1">
                <div className="font-medium text-lia-text-primary">Feedback (24-48h após)</div>
                <p className="text-sm text-lia-text-secondary">Envio de retorno personalizado ao candidato</p>
              </div>
              <Chip density="relaxed" variant="neutral" >1-2 dias</Chip>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <ChevronRight className="w-4 h-4 text-status-success" />
            Próximos Passos Possíveis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-status-success/10 dark:bg-status-success/20 rounded-xl border border-status-success/30">
              <div className="font-medium text-status-success dark:text-status-success mb-2">Se Aprovado</div>
              <div className="space-y-1 text-sm text-status-success dark:text-status-success">
                <div>• Entrevista técnica detalhada</div>
                <div>• Apresentação de case/portfolio</div>
                <div>• Conversa com futuro gestor</div>
                <div>• Verificação de referências</div>
              </div>
            </div>
            <div className="p-4 bg-wedo-orange/10 dark:bg-wedo-orange/10/20 rounded-xl border border-wedo-orange/30">
              <div className="font-medium text-wedo-orange-text dark:text-wedo-orange mb-2">Se Não Aprovado</div>
              <div className="space-y-1 text-sm text-wedo-orange-text dark:text-wedo-orange">
                <div>• Feedback construtivo personalizado</div>
                <div>• Inclusão no banco de talentos</div>
                <div>• Convite para vagas futuras</div>
                <div>• Manutenção do relacionamento</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-wedo-purple" />
            Checklist Pós-Triagem
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {["Preencher avaliação na plataforma","Atualizar status do candidato","Enviar feedback personalizado","Agendar próxima etapa (se aprovado)","Documentar insights para equipe","Atualizar funil de candidatos"
            ].map((item, index) => (
              <div key={`ci-${index}`} className="flex items-center gap-3">
                <input type="checkbox" className="rounded-xl border-lia-border-default" />
                <span className="text-sm text-lia-text-primary">{item}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
