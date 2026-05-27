"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Building, Users, ArrowRight, Shield, Zap } from "lucide-react"
import Link from "next/link"

export default function AccessPage() {
  const t = useTranslations('pipeline')
  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-lia-btn-primary-bg dark:bg-lia-bg-primary">
      <div className="w-full max-w-5xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1
            className="text-4xl font-semibold mb-3 text-lia-text-primary dark:text-lia-text-primary"
          >
            WedoTalent
          </h1>
          <p className="text-lg text-lia-text-secondary dark:text-lia-text-tertiary">
            Selecione sua área de acesso
          </p>
        </div>

        {/* Access Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Client Portal */}
          <Card className="group hover:border-lia-border-medium dark:hover:border-lia-border-medium transition-colors motion-reduce:transition-none duration-300 cursor-pointer">
            <CardContent className="p-8">
              <div className="flex flex-col items-center text-center space-y-6">
                {/* Icon */}
                <div className="w-20 h-20 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center group-hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active/20 transition-colors motion-reduce:transition-none">
                  <Users className="w-10 h-10 text-lia-text-primary dark:text-lia-text-secondary" />
                </div>

                {/* Title */}
                <div>
                  <h2
                    className="text-2xl font-semibold mb-2 text-lia-text-primary dark:text-lia-text-primary"
                  >
                    WedoTalent
                  </h2>
                  <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                    Plataforma de Recrutamento
                  </p>
                </div>

                {/* Features */}
                <div className="space-y-3 w-full text-left">
                  <div className="flex items-start gap-3">
                    <Zap className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Assistente IA
                      </p>
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                        Busca inteligente de candidatos
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Building className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Gestão de Vagas
                      </p>
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                        {t('access.talentPipelineAndPipeline')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <ArrowRight className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Análise de Dados
                      </p>
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                        KPIs e indicadores estratégicos
                      </p>
                    </div>
                  </div>
                </div>

                {/* CTA */}
                <Link href="/" className="w-full">
                  <Button className="w-full bg-lia-btn-primary-bg dark:bg-lia-bg-secondary hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active">
                    Acessar Plataforma
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Admin Portal */}
          <Card className="group hover:border-wedo-purple/30 transition-colors motion-reduce:transition-none duration-300 cursor-pointer">
            <CardContent className="p-8">
              <div className="flex flex-col items-center text-center space-y-6">
                {/* Icon */}
                <div className="w-20 h-20 rounded-full bg-wedo-purple/10 flex items-center justify-center group-hover:bg-wedo-purple/20 transition-colors motion-reduce:transition-none">
                  <Shield className="w-10 h-10 text-wedo-purple" />
                </div>

                {/* Title */}
                <div>
                  <h2
                    className="text-2xl font-semibold mb-2 text-lia-text-primary dark:text-lia-text-primary"
                  >
                    Admin Portal
                  </h2>
                  <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                    Gestão SaaS e Configurações
                  </p>
                </div>

                {/* Features */}
                <div className="space-y-3 w-full text-left">
                  <div className="flex items-start gap-3">
                    <Building className="w-4 h-4 text-wedo-purple mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Gestão de Clientes
                      </p>
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                        Organizações, usuários e acesso
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Zap className="w-4 h-4 text-wedo-purple mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Configurações
                      </p>
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                        Integrações, APIs e limites
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <ArrowRight className="w-4 h-4 text-wedo-purple mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                        Métricas SaaS
                      </p>
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                        MRR, ARR, consumo e analytics
                      </p>
                    </div>
                  </div>
                </div>

                {/* CTA */}
                <Link href="/" className="w-full">
                  <Button className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active">
                    Acessar Plataforma
                    <Shield className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="text-center mt-12">
          <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
            WeDoTalent © 2025
          </p>
        </div>
      </div>
    </div>
  )
}
