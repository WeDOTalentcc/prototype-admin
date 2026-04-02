"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Star } from "lucide-react"

export function NPSTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Star className="w-4 h-4" />
            Configurações do Sistema NPS
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Escala de NPS
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary text-sm"
              >
                <option>0-10 (Padrão NPS)</option>
                <option>1-5 (Simplificado)</option>
                <option>1-10 (Personalizado)</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                Frequência de Envio
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary text-sm"
              >
                <option>Após cada processo seletivo</option>
                <option>Semanal</option>
                <option>Mensal</option>
                <option>Trimestral</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              Pergunta Principal
            </label>
            <textarea
              rows={3}
              defaultValue="De 0 a 10, o quanto você recomendaria nossa empresa como um lugar para trabalhar?"
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary text-sm"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
