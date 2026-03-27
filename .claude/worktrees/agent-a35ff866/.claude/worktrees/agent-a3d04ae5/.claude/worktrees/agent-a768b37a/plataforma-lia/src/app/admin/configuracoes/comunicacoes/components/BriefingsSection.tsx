'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Clock, FileText, MessageSquare, ClipboardCheck } from "lucide-react"

export function BriefingsSection() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--eleven-text-primary)' }}>
          Briefings LIA
        </h3>
        <p className="text-sm mb-4" style={{ color: 'var(--eleven-text-secondary)' }}>
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
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Resumo matinal das atividades
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
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
                <div className="w-10 h-10 rounded-md bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <CardTitle className="text-base">Resumo de Fim de Dia</CardTitle>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Consolidação das atividades do dia
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
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
        <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--eleven-text-primary)' }}>
          Pareceres LIA
        </h3>
        <p className="text-sm mb-4" style={{ color: 'var(--eleven-text-secondary)' }}>
          Estrutura dos pareceres gerados pela LIA
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="hover:border-gray-900 dark:hover:border-gray-50 transition-colors cursor-pointer">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <CardTitle className="text-base">Parecer Resumido</CardTitle>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Análise rápida do candidato
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                Parecer conciso com pontos-chave, score de aderência e recomendação principal.
              </p>
              <div className="flex items-center gap-2 mt-3">
                <Badge className="bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400">
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
                <div className="w-10 h-10 rounded-md bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                  <ClipboardCheck className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <CardTitle className="text-base">Parecer Completo</CardTitle>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Análise detalhada do candidato
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                Parecer detalhado com análise técnica, comportamental, cultural e histórico profissional.
              </p>
              <div className="flex items-center gap-2 mt-3">
                <Badge className="bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400">
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
