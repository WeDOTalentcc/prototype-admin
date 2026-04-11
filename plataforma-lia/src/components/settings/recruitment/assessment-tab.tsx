"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ClipboardList } from "lucide-react"

export function AssessmentTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <ClipboardList className="w-4 h-4" />
            Critérios de Avaliação
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {[
              { categoria: 'Competências Técnicas', peso: 40, criterios: ['Conhecimento específico', 'Experiência prática'] },
              { categoria: 'Soft Skills', peso: 30, criterios: ['Comunicação', 'Liderança'] },
              { categoria: 'Fit Cultural', peso: 20, criterios: ['Alinhamento com valores', 'Adaptabilidade'] },
              { categoria: 'Potencial de Crescimento', peso: 10, criterios: ['Aprendizado contínuo', 'Ambição'] }
            ].map((item) => (
              <div key={item.categoria} className="p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-lia-text-primary">
                    {item.categoria}
                  </h4>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={item.peso}
                      onChange={() => onSettingsChange(true)}
                      className="w-16 px-2 py-1 border border-lia-border-default dark:border-lia-border-default rounded-xl text-sm text-center"
                    />
                    <span className="text-sm text-lia-text-primary">%</span>
                  </div>
                </div>
                <div className="space-y-1">
                  {item.criterios.map((criterio, idx) => (
                    <div key={idx} className="text-sm text-lia-text-primary">
                      • {criterio}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
