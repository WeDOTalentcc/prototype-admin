"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Shield, Plus, Copy, Eye } from "lucide-react"

export interface SettingsAPIKeysTabProps {
  onSettingsChange: (changed: boolean) => void
}

export function SettingsAPIKeysTab({ onSettingsChange }: SettingsAPIKeysTabProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl font-medium font-inter">
            <Shield className="w-4 h-4" />
            Chaves de API
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
            <div>
              <div className="text-sm font-medium text-lia-text-primary">Chave de Produção</div>
              <div className="text-xs text-lia-text-primary font-mono mt-1">sk-prod-****************************</div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm">
                <Eye className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm">
                <Copy className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-between p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
            <div>
              <div className="text-sm font-medium text-lia-text-primary">Chave de Teste</div>
              <div className="text-xs text-lia-text-primary font-mono mt-1">sk-test-****************************</div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm">
                <Eye className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm">
                <Copy className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <Button variant="outline" className="gap-2">
            <Plus className="w-4 h-4" />
            Gerar Nova Chave
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
