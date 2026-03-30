"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Shield, Phone, Download } from "lucide-react"

export interface SettingsSecurityTabProps {
  onSettingsChange: (changed: boolean) => void
}

export function SettingsSecurityTab({ onSettingsChange }: SettingsSecurityTabProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Shield className="w-4 h-4" />
            Segurança da Conta
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Button variant="outline" className="w-full justify-start">
              <Shield className="w-4 h-4 mr-2" />
              Alterar Senha
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Phone className="w-4 h-4 mr-2" />
              Configurar 2FA
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Download className="w-4 h-4 mr-2" />
              Baixar Dados
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Privacidade</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Compartilhar dados de uso</div>
                <div className="text-xs lia-text-800 dark:text-lia-text-tertiary">Ajuda a melhorar a plataforma</div>
              </div>
              <input type="checkbox" defaultChecked onChange={() => onSettingsChange(true)} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">Análise de comportamento</div>
                <div className="text-xs lia-text-800 dark:text-lia-text-tertiary">Para personalizar sua experiência</div>
              </div>
              <input type="checkbox" defaultChecked onChange={() => onSettingsChange(true)} />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
