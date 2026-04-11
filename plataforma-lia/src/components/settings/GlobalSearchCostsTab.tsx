"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Globe, Zap, CheckCircle, AlertCircle, Info,
  DollarSign, Search, TrendingUp, Shield, Clock
} from "lucide-react"
import { limitOptions, type GlobalSearchSettings } from "./useGlobalSearchSettings"

interface GlobalSearchCostsTabProps {
  settings: GlobalSearchSettings
  estimatedCreditsPerSearch: number
}

export function GlobalSearchCostsTab({
  settings, estimatedCreditsPerSearch,
}: GlobalSearchCostsTabProps) {
  return (
    <div className="space-y-3">
      <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
            <DollarSign className="w-3.5 h-3.5 text-lia-text-secondary" />
            Tabela de Custos da Busca Global
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-3">
          <div className="overflow-hidden rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
            <table className="w-full text-xs">
              <thead className="bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                <tr>
                  <th className="px-2 py-1.5 text-left text-xs font-medium text-lia-text-secondary">Limite</th>
                  <th className="px-2 py-1.5 text-center text-xs font-medium text-lia-text-secondary">Créditos Estimados</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                {limitOptions.map((option, idx) => (
                  <tr
                    key={option.value}
                    className={`${
                      settings.defaultLimit === option.value
                        ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary/50'
                        : idx % 2 === 0 ? 'bg-lia-bg-primary' : 'bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/50'
                    }`}
                  >
                    <td className="px-2 py-1.5">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-medium text-lia-text-primary">{option.label}</span>
                        {settings.defaultLimit === option.value && (
                          <Badge className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-micro px-1.5">Atual</Badge>
                        )}
                      </div>
                    </td>
                    <td className="px-2 py-1.5 text-center">
                      <span className="text-xs font-semibold text-lia-text-primary">~{option.estimatedCredits.fast} créditos</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-3 p-3 bg-status-warning/10 dark:bg-status-warning/20 rounded-md">
            <div className="flex items-start gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-status-warning dark:text-status-warning mt-0.5 flex-shrink-0" />
              <div className="text-micro text-status-warning dark:text-status-warning">
                <strong>Nota:</strong> Os custos são estimativas baseadas no limite configurado.
                O custo real pode variar dependendo dos filtros aplicados e disponibilidade de candidatos.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
            <Zap className="w-3.5 h-3.5 text-lia-text-secondary" />
            Detalhamento de Custos por Opção
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-3">
          <div className="p-4 rounded-xl border bg-lia-bg-secondary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle mb-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Zap className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="font-medium text-xs">Custo Estimado</span>
              </div>
              <Badge variant="outline" className="text-xs px-1.5 py-0.5 border-lia-border-default text-lia-text-primary dark:border-lia-border-default">Tempo Real</Badge>
            </div>

            <div className="flex items-end justify-between mb-3">
              <div>
                <div className="text-base font-bold text-lia-text-primary">1-3</div>
                <div className="text-xs text-lia-text-secondary">créditos por candidato</div>
              </div>
              <div className="text-right">
                <div className="font-medium text-xs">{settings.defaultLimit}-{settings.defaultLimit * 3}</div>
                <div className="text-xs text-lia-text-secondary">total ({settings.defaultLimit} candidatos)</div>
              </div>
            </div>

            <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-3 space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-lia-text-secondary">Base (Busca Rápida)</span>
                <span className="font-medium">1</span>
              </div>
              <div className="flex justify-between text-xs pt-1.5 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <span className="flex items-center gap-1 font-medium text-lia-text-primary">
                  <TrendingUp className="w-3 h-3" />
                  Total Base por Candidato
                </span>
                <span className="font-bold text-lia-text-primary">1</span>
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
            <table className="w-full text-xs">
              <thead className="bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-lia-text-secondary">Opção / Campo</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-lia-text-secondary">Seção</th>
                  <th className="px-3 py-2 text-center text-xs font-medium text-lia-text-secondary">Custo Adicional</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                <tr className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary/50">
                  <td className="px-3 py-2"><div className="flex items-center gap-2"><Globe className="w-3.5 h-3.5 text-lia-text-secondary" /><span className="font-medium text-lia-text-primary">Busca Global / Híbrida</span></div></td>
                  <td className="px-3 py-2 text-lia-text-secondary">Origem da Busca</td>
                  <td className="px-3 py-2 text-center"><Badge className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary text-micro">1 crédito/cand.</Badge></td>
                </tr>
                <tr className="bg-lia-bg-primary dark:bg-lia-bg-primary">
                  <td className="px-3 py-2"><div className="flex items-center gap-2"><Clock className="w-3.5 h-3.5 text-lia-text-secondary" /><span className="font-medium text-lia-text-primary">Dados Atualizados (High Freshness)</span></div></td>
                  <td className="px-3 py-2 text-lia-text-secondary">Opções de Qualidade</td>
                  <td className="px-3 py-2 text-center"><Badge className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary text-micro">+2 créditos</Badge></td>
                </tr>
                <tr className="bg-lia-bg-primary dark:bg-lia-bg-primary">
                  <td className="px-3 py-2"><div className="flex items-center gap-2"><Search className="w-3.5 h-3.5 text-lia-text-secondary" /><span className="font-medium text-lia-text-primary">Apenas com Email (filtro)</span></div></td>
                  <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                  <td className="px-3 py-2 text-center"><Badge className="bg-lia-bg-tertiary text-lia-text-primary text-micro">+1 crédito</Badge></td>
                </tr>
                <tr className="bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/50">
                  <td className="px-3 py-2"><div className="flex items-center gap-2"><Shield className="w-3.5 h-3.5 text-status-success" /><span className="font-medium text-lia-text-primary">Mostrar Emails (revelar)</span></div></td>
                  <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                  <td className="px-3 py-2 text-center"><Badge className="bg-status-success/15 text-status-success text-micro">+2 créditos</Badge></td>
                </tr>
                <tr className="bg-lia-bg-primary dark:bg-lia-bg-primary">
                  <td className="px-3 py-2"><div className="flex items-center gap-2"><Search className="w-3.5 h-3.5 text-lia-text-secondary" /><span className="font-medium text-lia-text-primary">Apenas com Telefone (filtro)</span></div></td>
                  <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                  <td className="px-3 py-2 text-center"><Badge className="bg-lia-bg-tertiary text-lia-text-primary text-micro">+1 crédito</Badge></td>
                </tr>
                <tr className="bg-status-warning/10/50 dark:bg-status-warning/20">
                  <td className="px-3 py-2"><div className="flex items-center gap-2"><AlertCircle className="w-3.5 h-3.5 text-status-warning" /><span className="font-medium text-lia-text-primary">Mostrar Telefones (revelar)</span></div></td>
                  <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                  <td className="px-3 py-2 text-center"><Badge className="bg-status-warning/15 text-status-warning text-micro">+14 créditos</Badge></td>
                </tr>
                <tr className="bg-lia-bg-primary dark:bg-lia-bg-primary">
                  <td className="px-3 py-2"><div className="flex items-center gap-2"><Search className="w-3.5 h-3.5 text-lia-text-secondary" /><span className="font-medium text-lia-text-primary">Email OU Telefone (filtro)</span></div></td>
                  <td className="px-3 py-2 text-lia-text-secondary">Informações de Contato</td>
                  <td className="px-3 py-2 text-center"><Badge className="bg-lia-bg-tertiary text-lia-text-primary text-micro">+1 crédito</Badge></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="mt-4 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-3.5 h-3.5 text-lia-text-secondary" />
              <span className="text-xs font-medium text-lia-text-primary">Resumo de Custos</span>
            </div>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-2 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="text-micro text-lia-text-secondary">Custo Mínimo</div>
                <div className="text-sm font-bold text-status-success">1 crédito</div>
                <div className="text-micro text-lia-text-tertiary">por candidato</div>
              </div>
              <div className="p-2 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="text-micro text-lia-text-secondary">Custo Típico</div>
                <div className="text-sm font-bold text-lia-text-primary">3-5 créditos</div>
                <div className="text-micro text-lia-text-tertiary">por candidato</div>
              </div>
              <div className="p-2 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-status-warning/30 dark:border-status-warning/30">
                <div className="text-micro text-lia-text-secondary">Custo Máximo</div>
                <div className="text-sm font-bold text-status-warning">19 créditos</div>
                <div className="text-micro text-lia-text-tertiary">por candidato</div>
              </div>
            </div>
            <p className="text-micro text-lia-text-secondary mt-2 text-center">
              * O custo máximo inclui todas as opções habilitadas (Freshness + Emails + Telefones)
            </p>
          </div>

          <div className="mt-3 p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md">
            <div className="flex items-start gap-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-status-success dark:text-status-success mt-0.5 flex-shrink-0" />
              <div className="text-micro text-status-success dark:text-status-success">
                <strong>Busca Local é gratuita!</strong> Buscas na base local (candidatos já cadastrados)
                não consomem créditos. As opções acima são cobradas apenas em buscas Híbridas ou Globais.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-lia-border-subtle/50 dark:border-lia-border-subtle/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-base-ui font-semibold flex items-center gap-2 text-lia-text-primary">
            <TrendingUp className="w-3.5 h-3.5 text-lia-text-secondary" />
            Resumo da Configuração Atual
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl col-span-2">
              <div className="text-micro text-lia-text-primary mb-0.5">Limite por busca</div>
              <div className="text-lg font-semibold text-lia-text-primary">{settings.defaultLimit}</div>
              <div className="text-micro text-lia-text-primary">candidatos (~1 crédito/cand)</div>
            </div>
            <div className="p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary/50 rounded-xl col-span-2">
              <div className="text-micro text-lia-text-primary mb-0.5">Custo estimado por busca</div>
              <div className="text-xl font-semibold text-lia-text-primary">~{estimatedCreditsPerSearch} créditos</div>
              <div className="text-micro text-lia-text-secondary mt-0.5">
                {settings.showEmails && '+emails '}
                {settings.showPhoneNumbers && '+telefones '}
                {settings.highFreshness && '+freshness'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
