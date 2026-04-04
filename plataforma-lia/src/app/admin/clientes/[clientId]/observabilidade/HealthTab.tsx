"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  CheckCircle2,
  Activity,
  Server,
  Wifi,
  RefreshCw,
  TrendingUp,
  AlertCircle,
} from "lucide-react"

export function HealthTab() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Integrações Online</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">—</p>
                <div className="flex items-center gap-1 mt-1">
                  <Wifi className="w-3 h-3 text-lia-text-tertiary" />
                  <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">Aguardando dados</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-success/10 dark:bg-status-success/20 flex items-center justify-center">
                <Server className="w-5 h-5 text-status-success dark:text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Incidentes Abertos</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">0</p>
                <div className="flex items-center gap-1 mt-1">
                  <CheckCircle2 className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">Nenhum incidente</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-warning/10 dark:bg-status-warning/20 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-status-warning dark:text-status-warning" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Uptime Médio</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">—</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-lia-text-tertiary" />
                  <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">Últimos 30 dias</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-secondary flex items-center justify-center">
                <Activity className="w-5 h-5 text-lia-text-primary dark:text-lia-text-secondary" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Status das Integrações
            </CardTitle>
            <Button variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Atualizar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <Server className="w-8 h-8 mb-3 text-lia-text-tertiary dark:text-lia-text-secondary" />
            <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
              Status de integrações em breve
            </p>
            <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary">
              O monitoramento em tempo real das integrações será exibido aqui.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Timeline de Incidentes
            </CardTitle>
            <Badge variant="success">0 abertos</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <CheckCircle2 className="w-8 h-8 mb-3 text-status-success" />
            <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
              Nenhum incidente registrado
            </p>
            <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary">
              Os incidentes serão listados aqui quando detectados.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
