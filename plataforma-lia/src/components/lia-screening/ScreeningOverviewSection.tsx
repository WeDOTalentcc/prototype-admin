"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { CheckCircle, Clock, Target, Users } from"lucide-react"

interface ScreeningOverviewSectionProps {
  requirements: string[]
}

export function ScreeningOverviewSection({ requirements }: ScreeningOverviewSectionProps) {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold font-sans text-lia-text-primary mb-4">Visão Geral do Processo</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 font-sans">
                <Target className="w-4 h-4 text-lia-text-secondary" />
                Objetivo da Triagem
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-lia-text-primary">
                Validar fit inicial do candidato com a vaga, avaliar competências básicas e motivação,
                além de esclarecer expectativas mútuas antes de avançar no processo.
              </p>
            </CardContent>
          </Card>

          <Card >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 font-sans">
                <Clock className="w-4 h-4 text-status-success" />
                Duração Sugerida
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-lia-text-primary">
                20-30 minutos para uma conversa completa, incluindo apresentação da empresa,
                perguntas de triagem e esclarecimento de dúvidas.
              </p>
            </CardContent>
          </Card>

          <Card >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 font-sans">
                <Users className="w-4 h-4 text-wedo-purple" />
                Critérios de Avaliação
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span>Competências Técnicas</span>
                  <Chip variant="neutral">40%</Chip>
                </div>
                <div className="flex items-center justify-between">
                  <span>Fit Cultural</span>
                  <Chip variant="neutral">30%</Chip>
                </div>
                <div className="flex items-center justify-between">
                  <span>Motivação</span>
                  <Chip variant="neutral">20%</Chip>
                </div>
                <div className="flex items-center justify-between">
                  <span>Expectativas</span>
                  <Chip variant="neutral">10%</Chip>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 font-sans">
                <CheckCircle className="w-4 h-4 text-wedo-orange" />
                Resultado Esperado
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-lia-text-primary">
                Decisão clara sobre prosseguir com o candidato, com feedback estruturado
                e próximos passos bem definidos.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      <div>
        <h5 className="font-medium font-sans text-lia-text-primary mb-3">Checklist de Requisitos Essenciais</h5>
        <div className="space-y-2">
          {requirements.length > 0 ? requirements.map((requirement: string) => (
            <div key={requirement} className="flex items-center gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <input type="checkbox" className="rounded-md" />
              <span className="text-sm text-lia-text-primary">{requirement}</span>
            </div>
          )) : (
            <div className="text-sm text-lia-text-secondary">Nenhum requisito específico definido</div>
          )}
        </div>
      </div>
    </div>
  )
}
