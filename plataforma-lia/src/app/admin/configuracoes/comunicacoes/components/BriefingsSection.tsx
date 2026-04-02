'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Clock, FileText, MessageSquare, ClipboardCheck } from "lucide-react"

export function BriefingsSection() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2 text-lia-text-primary dark:text-lia-text-primary" >
          Briefings LIA
        </h3>
        <p className="text-sm mb-4 text-lia-text-secondary dark:text-lia-text-tertiary" >
          Templates de briefings automáticos da LIA
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
 <div className="w-10 h-10 rounded-md bg-lia-bg-tertiary flex items-center justify-center">
 <MessageSquare className="w-5 h-5 text-lia-text-primary dark:text-lia-text-secondary" />
                </div>
                <div>
                  <CardTitle className="text-base">Briefing Diário</CardTitle>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Resumo matinal das atividades
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                Atualização automática com novos candidatos, entrevistas agendadas e tarefas pendentes do dia.
              </p>
              <div className="flex items-center gap-2 mt-3">
 <Badge className="bg-lia-bg-secondary text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-secondary">
                  Automático
                </Badge>
                <Badge className="bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-tertiary">
                  Diário às 08:00
                </Badge>
              </div>
            </CardContent>
          </Card>
          
          <Card className="hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-status-warning/15 dark:bg-status-warning/30 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-status-warning dark:text-status-warning" />
                </div>
                <div>
                  <CardTitle className="text-base">Resumo de Fim de Dia</CardTitle>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Consolidação das atividades do dia
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                Relatório consolidado com candidatos processados, feedbacks recebidos e próximos passos.
              </p>
              <div className="flex items-center gap-2 mt-3">
 <Badge className="bg-lia-bg-secondary text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-secondary">
                  Automático
                </Badge>
                <Badge className="bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-tertiary">
                  Diário às 18:00
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-semibold mb-2 text-lia-text-primary dark:text-lia-text-primary" >
          Pareceres LIA
        </h3>
        <p className="text-sm mb-4 text-lia-text-secondary dark:text-lia-text-tertiary" >
          Estrutura dos pareceres gerados pela LIA
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-status-success/15 dark:bg-status-success/30 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-status-success dark:text-status-success" />
                </div>
                <div>
                  <CardTitle className="text-base">Parecer Resumido</CardTitle>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Análise rápida do candidato
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                Parecer conciso com pontos-chave, score de aderência e recomendação principal.
              </p>
              <div className="flex items-center gap-2 mt-3">
                <Badge className="bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success">
                  Sob demanda
                </Badge>
                <Badge className="bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-tertiary">
                  ~500 caracteres
                </Badge>
              </div>
            </CardContent>
          </Card>
          
          <Card className="hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-wedo-purple/15 dark:bg-wedo-purple/30 flex items-center justify-center">
                  <ClipboardCheck className="w-5 h-5 text-wedo-purple dark:text-wedo-purple" />
                </div>
                <div>
                  <CardTitle className="text-base">Parecer Completo</CardTitle>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Análise detalhada do candidato
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                Parecer detalhado com análise técnica, comportamental, cultural e histórico profissional.
              </p>
              <div className="flex items-center gap-2 mt-3">
                <Badge className="bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple">
                  Sob demanda
                </Badge>
                <Badge className="bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary dark:text-lia-text-tertiary">
                  ~2000 caracteres
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
