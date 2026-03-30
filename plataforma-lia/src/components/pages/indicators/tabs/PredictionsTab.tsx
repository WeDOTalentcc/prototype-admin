import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RecruitmentMLDashboard } from "@/components/ml/recruitment-ml-engine"
import type { RecruiterData } from "../indicators.types"
import {
  TrendingUp, Clock, AlertTriangle, DollarSign, Brain, Target,
} from "lucide-react"

interface PredictionsTabProps {
  recruiters: RecruiterData[]
}

export function PredictionsTab({ recruiters }: PredictionsTabProps) {
  return (
    <div className="space-y-6">
      {/* Sistema de Machine Learning */}
      <RecruitmentMLDashboard candidates={recruiters} />

      {/* KPIs Preditivos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-status-success/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-status-success font-medium">Previsão Q4</p>
                <p className="text-2xl font-bold text-status-success">156</p>
                <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">Contratações</p>
              </div>
              <TrendingUp className="w-8 h-8 text-status-success" />
            </div>
            <div className="mt-2 text-xs text-status-success">+12% vs Q3 (IA: 89% confiança)</div>
          </CardContent>
        </Card>

        <Card className="border-lia-border-default dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary font-medium">
                  Time to Fill
                </p>
                <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                  24 dias
                </p>
                <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                  Previsão média
                </p>
              </div>
              <Clock className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div className="mt-2 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
              -8% vs atual (IA: 92% confiança)
            </div>
          </CardContent>
        </Card>

        <Card className="border-wedo-purple/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-wedo-purple font-medium">Turnover Risk</p>
                <p className="text-2xl font-bold text-wedo-purple">8.2%</p>
                <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                  Próximos 6 meses
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-wedo-purple" />
            </div>
            <div className="mt-2 text-xs text-wedo-purple">87 funcionários em risco</div>
          </CardContent>
        </Card>

        <Card className="border-wedo-orange/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-wedo-orange font-medium">Budget Impact</p>
                <p className="text-2xl font-bold text-wedo-orange">R$ 2.8M</p>
                <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">
                  Economia prevista
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-wedo-orange" />
            </div>
            <div className="mt-2 text-xs text-wedo-orange">Otimizações em TA</div>
          </CardContent>
        </Card>
      </div>

      {/* Análise Preditiva de Demanda */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-wedo-purple" />
              Previsão de Demanda por Área
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { area: "Tecnologia", current: 45, predicted: 62, confidence: 94 },
                { area: "Vendas", current: 23, predicted: 31, confidence: 87 },
                { area: "Marketing", current: 18, predicted: 22, confidence: 91 },
                { area: "Design", current: 12, predicted: 16, confidence: 89 },
                { area: "Operações", current: 15, predicted: 18, confidence: 85 },
              ].map((item, index) => (
                <div key={item.area} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                      {item.area}
                    </span>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-lia-text-secondary">
                        {item.current} → {item.predicted}
                      </span>
                      <Badge className="bg-wedo-purple/15 text-wedo-purple text-xs">
                        {item.confidence}% confiança
                      </Badge>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gray-500 h-2 rounded-full"
                        style={{ width: `${(item.current / 70) * 100}%` }}
                      />
                    </div>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-wedo-purple h-2 rounded-full"
                        style={{ width: `${(item.predicted / 70) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-status-success" />
              Skills em Alta Demanda
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { skill: "Inteligência Artificial", growth: "+127%", urgency: "alta" },
                { skill: "React/Next.js", growth: "+89%", urgency: "alta" },
                { skill: "DevOps/K8s", growth: "+76%", urgency: "média" },
                { skill: "Product Management", growth: "+65%", urgency: "média" },
                { skill: "Data Science", growth: "+54%", urgency: "média" },
                { skill: "UX Research", growth: "+43%", urgency: "baixa" },
              ].map((item, index) => (
                <div
                  key={item.skill}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                >
                  <div>
                    <div className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                      {item.skill}
                    </div>
                    <div className="text-sm text-status-success">{item.growth} crescimento</div>
                  </div>
                  <Badge
                    className={
                      item.urgency === "alta"
                        ? "bg-status-error/15 text-status-error"
                        : item.urgency === "média"
                        ? "bg-status-warning/15 text-status-warning"
                        : "bg-status-success/15 text-status-success"
                    }
                  >
                    {item.urgency === "alta"
                      ? "🔴 Alta"
                      : item.urgency === "média"
                      ? "🟡 Média"
                      : "🟢 Baixa"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alertas e Recomendações de IA */}
      <Card className="border-l-4 border-l-red-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-status-error" />
            Alertas Inteligentes e Ações Recomendadas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                type: "urgente",
                title: "Escassez crítica em IA/ML",
                description:
                  "Demanda crescerá 127% nos próximos 3 meses, mas pipeline tem apenas 12 candidatos.",
                action: "Iniciar campanha agressiva de sourcing e aumentar budget em 40%",
                confidence: 94,
              },
              {
                type: "atencao",
                title: "Risco de turnover em Tech",
                description: "23 desenvolvedores sêniores com padrão de saída detectado.",
                action: "Implementar programa de retenção e revisar pacotes salariais",
                confidence: 87,
              },
              {
                type: "oportunidade",
                title: "Otimização de processo",
                description:
                  "IA detectou 8 etapas desnecessárias no funil que aumentam time to fill em 12 dias.",
                action: "Simplificar processo e automatizar triagem inicial",
                confidence: 91,
              },
            ].map((alert, index) => (
              <div
                key={`alert-${index}`}
                className={`p-4 rounded-md border-l-4 ${
                  alert.type === "urgente"
                    ? "bg-status-error/10 border-l-red-500"
                    : alert.type === "atencao"
                    ? "bg-status-warning/10 border-l-yellow-500"
                    : "bg-status-success/10 border-l-green-500"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4
                      className={`font-medium mb-1 ${
                        alert.type === "urgente"
                          ? "text-status-error"
                          : alert.type === "atencao"
                          ? "text-status-warning"
                          : "text-status-success"
                      }`}
                    >
                      {alert.type === "urgente" ? "🚨" : alert.type === "atencao" ? "⚠️" : "💡"}{" "}
                      {alert.title}
                    </h4>
                    <p
                      className={`text-sm mb-2 ${
                        alert.type === "urgente"
                          ? "text-status-error"
                          : alert.type === "atencao"
                          ? "text-status-warning"
                          : "text-status-success"
                      }`}
                    >
                      {alert.description}
                    </p>
                    <p
                      className={`text-sm font-medium ${
                        alert.type === "urgente"
                          ? "text-status-error"
                          : alert.type === "atencao"
                          ? "text-status-warning"
                          : "text-status-success"
                      }`}
                    >
                      💡 Ação recomendada: {alert.action}
                    </p>
                  </div>
                  <Badge className="ml-4 bg-gray-100 text-lia-text-primary dark:text-lia-text-primary">
                    {alert.confidence}% confiança
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
