'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Clock, FileText, MessageSquare, ClipboardCheck } from "lucide-react"

export function BriefingsSection() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-100" >
          Briefings LIA
        </h3>
        <p className="text-sm mb-4 text-gray-500 dark:text-gray-400" >
          Templates de briefings automáticos da LIA
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
 <div className="w-10 h-10 rounded-md bg-gray-100 flex items-center justify-center">
 <MessageSquare className="w-5 h-5 text-gray-900 dark:text-gray-300" />
                </div>
                <div>
                  <CardTitle className="text-base">Briefing Diário</CardTitle>
                  <p className="text-xs text-gray-400 dark:text-gray-500" >
                    Resumo matinal das atividades
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400" >
                Atualização automática com novos candidatos, entrevistas agendadas e tarefas pendentes do dia.
              </p>
              <div className="flex items-center gap-2 mt-3">
 <Badge className="bg-gray-50 text-gray-900 dark:bg-gray-800 dark:text-gray-300">
                  Automático
                </Badge>
                <Badge className="bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                  Diário às 08:00
                </Badge>
              </div>
            </CardContent>
          </Card>
          
          <Card className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-status-warning/15 dark:bg-status-warning/30 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-status-warning dark:text-status-warning" />
                </div>
                <div>
                  <CardTitle className="text-base">Resumo de Fim de Dia</CardTitle>
                  <p className="text-xs text-gray-400 dark:text-gray-500" >
                    Consolidação das atividades do dia
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400" >
                Relatório consolidado com candidatos processados, feedbacks recebidos e próximos passos.
              </p>
              <div className="flex items-center gap-2 mt-3">
 <Badge className="bg-gray-50 text-gray-900 dark:bg-gray-800 dark:text-gray-300">
                  Automático
                </Badge>
                <Badge className="bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                  Diário às 18:00
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-semibold mb-2 text-gray-800 dark:text-gray-100" >
          Pareceres LIA
        </h3>
        <p className="text-sm mb-4 text-gray-500 dark:text-gray-400" >
          Estrutura dos pareceres gerados pela LIA
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-status-success/15 dark:bg-status-success/30 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-status-success dark:text-status-success" />
                </div>
                <div>
                  <CardTitle className="text-base">Parecer Resumido</CardTitle>
                  <p className="text-xs text-gray-400 dark:text-gray-500" >
                    Análise rápida do candidato
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400" >
                Parecer conciso com pontos-chave, score de aderência e recomendação principal.
              </p>
              <div className="flex items-center gap-2 mt-3">
                <Badge className="bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success">
                  Sob demanda
                </Badge>
                <Badge className="bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                  ~500 caracteres
                </Badge>
              </div>
            </CardContent>
          </Card>
          
          <Card className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-wedo-purple/15 dark:bg-wedo-purple/30 flex items-center justify-center">
                  <ClipboardCheck className="w-5 h-5 text-wedo-purple dark:text-wedo-purple" />
                </div>
                <div>
                  <CardTitle className="text-base">Parecer Completo</CardTitle>
                  <p className="text-xs text-gray-400 dark:text-gray-500" >
                    Análise detalhada do candidato
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400" >
                Parecer detalhado com análise técnica, comportamental, cultural e histórico profissional.
              </p>
              <div className="flex items-center gap-2 mt-3">
                <Badge className="bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple">
                  Sob demanda
                </Badge>
                <Badge className="bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
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
