"use client"

import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Chip } from "@/components/ui/chip"
import { MessageCircle, UserCheck, Clock, CheckCircle, Users, FileText, Star } from"lucide-react"

const liaActivities = [
  {
    id: 1,
    icon: MessageCircle,
    activity:"Feedback dado para candidato João Silva",
    details:"Avaliação positiva com recomendações de melhoria técnica",
    time:"09:00hrs",
    date:"26/03/2025",
    type:"feedback"
  },
  {
    id: 2,
    icon: Users,
    activity:"05 candidatos foram avaliados nos últimos 15 minutos",
    details:"Vaga: Desenvolvedor Frontend Sênior",
    time:"08:45hrs",
    date:"26/03/2025",
    type:"evaluation"
  },
  {
    id: 3,
    icon: UserCheck,
    activity:"Triagem automática realizada",
    details:"Candidata Maria Santos aprovada para próxima fase",
    time:"08:30hrs",
    date:"26/03/2025",
    type:"screening"
  },
  {
    id: 4,
    icon: FileText,
    activity:"Relatório de análise de CV gerado",
    details:"15 currículos analisados para vaga de UX Designer",
    time:"08:15hrs",
    date:"26/03/2025",
    type:"analysis"
  },
  {
    id: 5,
    icon: CheckCircle,
    activity:"Status atualizado automaticamente",
    details:"Carlos Oliveira movido para 'Aguardando entrevista'",
    time:"08:00hrs",
    date:"26/03/2025",
    type:"status_update"
  },
  {
    id: 6,
    icon: Star,
    activity:"Nota de adequação calculada",
    details:"3 novos candidatos receberam pontuação inicial",
    time:"07:45hrs",
    date:"26/03/2025",
    type:"scoring"
  }
]

export function TimelineSection() {
  return (
    <Card className="border border-lia-border-subtle">
      <CardHeader className="pb-4">
        <CardTitle className="text-base font-semibold text-lia-text-primary">
          Atividades sendo executadas pela IA
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4 pt-0">
        {/* Timeline Items */}
        <div className="space-y-4">
          {liaActivities.map((item, index) => (
            <div key={item.id} className="relative">
              {/* Timeline Line */}
              {index < liaActivities.length - 1 && (
                <div className="absolute left-4 top-8 bottom-0 w-px bg-lia-interactive-active"></div>
              )}

              <div className="flex gap-3">
                <div className="w-8 h-8 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full flex items-center justify-center relative z-10 flex-shrink-0">
                  <item.icon className="w-4 h-4 text-lia-text-secondary" />
                </div>

                <div className="flex-1 min-w-0 pb-4">
                  <div className="flex items-start justify-between mb-1">
                    <h4 className="font-medium text-lia-text-primary text-sm">
                      {item.activity}
                    </h4>
                    <div className="text-xs text-lia-text-secondary flex-shrink-0 ml-2">
                      {item.date} • {item.time}
                    </div>
                  </div>

                  <p className="text-sm text-lia-text-secondary leading-relaxed">
                    {item.details}
                  </p>

                  <div className="mt-2">
                    <Chip
                      variant={
                        item.type === 'feedback' ? 'success' :
                        item.type === 'screening' || item.type === 'analysis' ? 'neutral' :
                        item.type === 'evaluation' || item.type === 'status_update' ? 'neutral' :
                        'warning'
                      }
                      className={`text-xs ${
                        item.type === 'screening' ? 'border-wedo-purple/30 text-wedo-purple-text' :
                        item.type === 'analysis' ? 'border-wedo-orange/30 text-wedo-orange-text' :
                        item.type === 'status_update' ? 'border-lia-border-subtle text-lia-text-primary' :
                        ''
                      }`}
                    >
                      {item.type === 'feedback' ? 'Feedback' :
                       item.type === 'evaluation' ? 'Avaliação' :
                       item.type === 'screening' ? 'Triagem' :
                       item.type === 'analysis' ? 'Análise' :
                       item.type === 'status_update' ? 'Atualização' :
                       'Pontuação'}
                    </Chip>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <span className="text-sm text-lia-text-primary">
              Mostrando atividades das últimas 2 horas
            </span>
            <Button variant="ghost" size="sm" className="text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse text-xs">
              Ver histórico completo
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
