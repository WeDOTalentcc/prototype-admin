import { CURRENCY_SYMBOL } from"@/lib/pricing"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  ConversionFunnelChart,
} from"@/components/charts/interactive-charts"
import {
  DepartmentBudgetChart,
  SkillsGapChart,
} from"@/components/charts/advanced-interactive-charts"
import {
  TrendingUp, Target, Users, DollarSign, Clock, Heart,
} from"lucide-react"

export function StrategicTab() {
  return (
    <div className="space-y-6" data-testid="strategic-tab">
      {/* KPIs Estratégicos Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-status-success/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-status-success" />
              Taxa de Crescimento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold text-status-success">+24.8%</div>
            <div className="text-xs text-status-success mt-1">vs trimestre anterior</div>
            <div className="mt-3 text-xs text-lia-text-secondary">
              Contratações cresceram 35% e pipeline aumentou 18%
            </div>
          </CardContent>
        </Card>

        <Card className="border-lia-border-default dark:border-lia-border-default">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Target className="w-4 h-4 text-lia-text-secondary" />
              Eficiência Operacional
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold text-lia-text-primary">87.3%</div>
            <div className="text-xs text-lia-text-secondary mt-1">Metas atingidas</div>
            <div className="mt-3 text-xs text-lia-text-secondary">
              94% das vagas preenchidas dentro do prazo
            </div>
          </CardContent>
        </Card>

        <Card className="border-wedo-purple/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Users className="w-4 h-4 text-wedo-purple" />
              Qualidade da Contratação
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold text-wedo-purple-text">4.6/5.0</div>
            <div className="text-xs text-wedo-purple-text mt-1">Nota média</div>
            <div className="mt-3 text-xs text-lia-text-secondary">
              89% dos contratados ainda na empresa após 6 meses
            </div>
          </CardContent>
        </Card>

        <Card className="border-wedo-orange/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-wedo-orange" />
              ROI em Recrutamento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold text-wedo-orange-text">325%</div>
            <div className="text-xs text-wedo-orange-text mt-1">Retorno sobre investimento</div>
            <div className="mt-3 text-xs text-lia-text-secondary">
              Economia de {CURRENCY_SYMBOL} 2.4M em terceirização
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Indicadores de Performance Avançados */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ConversionFunnelChart />
        <SkillsGapChart />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-status-success" />
              Tempo de Preenchimento por Senioridade
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { level:"Júnior", days: 18, color:"bg-status-success", target: 20 },
                { level:"Pleno", days: 28, color:"bg-lia-bg-inverse dark:bg-lia-text-tertiary", target: 30 },
                { level:"Sênior", days: 42, color:"bg-status-warning", target: 45 },
                { level:"Liderança", days: 67, color:"bg-status-error", target: 60 },
              ].map((item, index) => (
                <div key={item.level} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>{item.level}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{item.days} dias</span>
                      <Chip variant="neutral" muted
                        className={
                          item.days <= item.target
                            ?""
                            :""
                        }
                      >
                        {item.days <= item.target ?"✓" :"!"}
                      </Chip>
                    </div>
                  </div>
                  <div className="w-full bg-lia-interactive-active rounded-full h-2">
                    <div
                      className={`${item.color} h-2 rounded-full transition-[width,height] duration-300`}
                      style={{ width: `${Math.min((item.days / 70) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Análise de Orçamento por Departamento */}
      <DepartmentBudgetChart />

      {/* Análise de Diversidade e Inclusão */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Heart className="w-5 h-5 text-wedo-magenta" />
            Diversidade e Inclusão
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-lia-text-primary mb-3">
                Distribuição por Gênero
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Feminino</span>
                  <span className="font-medium">47%</span>
                </div>
                <div className="w-full bg-lia-interactive-active rounded-full h-2">
                  <div className="bg-wedo-magenta h-2 rounded-full w-[47%]" />
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Masculino</span>
                  <span className="font-medium">51%</span>
                </div>
                <div className="w-full bg-lia-interactive-active rounded-full h-2">
                  <div className="bg-lia-bg-inverse dark:bg-lia-text-tertiary h-2 rounded-full w-[51%]" />
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Não-binário</span>
                  <span className="font-medium">2%</span>
                </div>
                <div className="w-full bg-lia-interactive-active rounded-full h-2">
                  <div className="bg-wedo-purple h-2 rounded-full w-[2%]" />
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-lia-text-primary mb-3">
                Representatividade Étnica
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Branca</span>
                  <span className="font-medium">52%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Parda</span>
                  <span className="font-medium">31%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Preta</span>
                  <span className="font-medium">14%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Outras</span>
                  <span className="font-medium">3%</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-lia-text-primary mb-3">
                Inclusão PCD
              </h4>
              <div className="text-center p-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-2xl font-semibold text-lia-text-primary">
                  8.2%
                </div>
                <div className="text-sm text-lia-text-secondary">
                  Pessoas com Deficiência
                </div>
                <div className="text-xs text-lia-text-secondary mt-2">Acima da cota legal de 5%</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
