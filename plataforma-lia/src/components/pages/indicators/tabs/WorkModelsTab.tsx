import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  WorkModelDistributionChart,
} from "@/components/charts/interactive-charts"
import {
  SourceEffectivenessChart,
} from "@/components/charts/advanced-interactive-charts"
import {
  TrendingUp, TrendingDown, Home, Mountain, Building, Star,
  BarChart3, MapPin, Lightbulb,
} from "lucide-react"

export function WorkModelsTab() {
  return (
    <div className="space-y-6">
      {/* Gráficos Interativos de Modelos de Trabalho */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WorkModelDistributionChart />
        <SourceEffectivenessChart />
      </div>

      {/* KPIs de Modelos de Trabalho */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-lia-border-default dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-lia-text-secondary font-medium">Remoto</p>
                <p className="text-2xl font-bold text-lia-text-primary">42%</p>
              </div>
              <Home className="w-8 h-8 text-lia-text-secondary" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 text-status-success" />
              <span className="text-status-success">+8% vs trimestre anterior</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-wedo-purple/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-wedo-purple font-medium">Híbrido</p>
                <p className="text-2xl font-bold text-wedo-purple">35%</p>
              </div>
              <Mountain className="w-8 h-8 text-wedo-purple" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 text-status-success" />
              <span className="text-status-success">+3% vs trimestre anterior</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-wedo-orange/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-wedo-orange font-medium">Presencial</p>
                <p className="text-2xl font-bold text-wedo-orange">23%</p>
              </div>
              <Building className="w-8 h-8 text-wedo-orange" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-xs">
              <TrendingDown className="w-3 h-3 text-status-error" />
              <span className="text-status-error">-11% vs trimestre anterior</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-status-success/30">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-status-success font-medium">Satisfação Média</p>
                <p className="text-2xl font-bold text-status-success">8.4/10</p>
              </div>
              <Star className="w-8 h-8 text-status-success" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-xs">
              <TrendingUp className="w-3 h-3 text-status-success" />
              <span className="text-status-success">+0.3 vs mês anterior</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Análise por Departamento */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-lia-text-secondary" />
              Modelos por Departamento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { dept: "Tecnologia", remote: 65, hybrid: 25, office: 10 },
                { dept: "Design", remote: 70, hybrid: 20, office: 10 },
                { dept: "Marketing", remote: 45, hybrid: 40, office: 15 },
                { dept: "Vendas", remote: 20, hybrid: 50, office: 30 },
                { dept: "Operações", remote: 15, hybrid: 35, office: 50 },
              ].map((item, index) => (
                <div key={item.dept} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-lia-text-primary">
                      {item.dept}
                    </span>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-lia-text-secondary">
                        {item.remote}% Remoto
                      </span>
                      <span className="text-wedo-purple">{item.hybrid}% Híbrido</span>
                      <span className="text-wedo-orange">{item.office}% Presencial</span>
                    </div>
                  </div>
                  <div className="flex w-full h-3 rounded-full overflow-hidden">
                    <div
                      className="bg-gray-700 dark:bg-lia-text-tertiary"
                      style={{ width: `${item.remote}%` }}
                    />
                    <div className="bg-wedo-purple" style={{ width: `${item.hybrid}%` }} />
                    <div className="bg-wedo-orange" style={{ width: `${item.office}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-status-success" />
              Distribuição Regional
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { region: "São Paulo", count: 234, percentage: 42 },
                { region: "Rio de Janeiro", count: 156, percentage: 28 },
                { region: "Minas Gerais", count: 89, percentage: 16 },
                { region: "Outros Estados", count: 78, percentage: 14 },
              ].map((item, index) => (
                <div key={item.region} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 bg-status-success rounded-full" />
                    <span className="text-sm font-medium">{item.region}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold">{item.count}</div>
                    <div className="text-xs text-lia-text-primary">
                      {item.percentage}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights e Recomendações */}
      <Card className="border-l-4 border-l-gray-400 dark:border-l-gray-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-status-warning" />
            Insights e Recomendações Estratégicas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-100 dark:bg-lia-bg-secondary rounded-md">
              <h4 className="font-medium text-lia-text-secondary mb-2">
                🚀 Tendência Crescente
              </h4>
              <p className="text-sm text-lia-text-secondary">
                Modelo remoto cresceu 8% no trimestre, especialmente em Tech e Design.
                Considere expandir políticas de trabalho remoto.
              </p>
            </div>
            <div className="p-4 bg-status-success/10 rounded-md">
              <h4 className="font-medium text-status-success mb-2">💡 Oportunidade</h4>
              <p className="text-sm text-status-success">
                Híbrido tem alta satisfação (8.7/10) e pode ser expandido para
                departamentos tradicionalmente presenciais.
              </p>
            </div>
            <div className="p-4 bg-status-warning/10 rounded-md">
              <h4 className="font-medium text-status-warning mb-2">⚠️ Atenção</h4>
              <p className="text-sm text-status-warning">
                Presencial em declínio (-11%). Avaliar necessidade real vs preferência dos
                colaboradores em Vendas e Operações.
              </p>
            </div>
            <div className="p-4 bg-wedo-purple/10 rounded-md">
              <h4 className="font-medium text-wedo-purple mb-2">📊 Benchmark</h4>
              <p className="text-sm text-wedo-purple">
                Empresa está 15% acima da média do mercado em satisfação com modelos
                flexíveis de trabalho.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
