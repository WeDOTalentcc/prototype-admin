"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Building, Users, ArrowRight, Shield, Zap } from "lucide-react"
import Link from "next/link"

export default function AccessPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-gray-900 dark:bg-white">
      <div className="w-full max-w-5xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1
            className="text-4xl font-bold mb-3 lia-text-800 dark:text-lia-text-primary"
          >
            WedoTalent
          </h1>
          <p className="text-lg lia-text-500 dark:text-lia-text-tertiary">
            Selecione sua área de acesso
          </p>
        </div>

        {/* Access Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Client Portal */}
          <Card className="group hover:border-gray-400 dark:hover:border-gray-500 transition-colors duration-300 cursor-pointer">
            <CardContent className="p-8">
              <div className="flex flex-col items-center text-center space-y-6">
                {/* Icon */}
                <div className="w-20 h-20 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center group-hover:bg-gray-800 dark:hover:bg-gray-200/20 transition-colors">
                  <Users className="w-10 h-10 lia-text-700 dark:text-lia-text-secondary" />
                </div>

                {/* Title */}
                <div>
                  <h2
                    className="text-2xl font-semibold mb-2 lia-text-800 dark:text-lia-text-primary"
                  >
                    WedoTalent
                  </h2>
                  <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">
                    Plataforma de Recrutamento
                  </p>
                </div>

                {/* Features */}
                <div className="space-y-3 w-full text-left">
                  <div className="flex items-start gap-3">
                    <Zap className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                        Assistente LIA
                      </p>
                      <p className="text-xs lia-text-400 dark:lia-text-500">
                        Busca inteligente de candidatos
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Building className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                        Gestão de Vagas
                      </p>
                      <p className="text-xs lia-text-400 dark:lia-text-500">
                        Funil de talentos e pipeline
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <ArrowRight className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                        Análise de Dados
                      </p>
                      <p className="text-xs lia-text-400 dark:lia-text-500">
                        KPIs e indicadores estratégicos
                      </p>
                    </div>
                  </div>
                </div>

                {/* CTA */}
                <Link href="/" className="w-full">
                  <Button className="w-full bg-gray-900 dark:lia-bg-50 hover:bg-gray-800 dark:hover:bg-gray-200">
                    Acessar Plataforma
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Admin Portal */}
          <Card className="group hover:border-wedo-purple/30 transition-colors duration-300 cursor-pointer">
            <CardContent className="p-8">
              <div className="flex flex-col items-center text-center space-y-6">
                {/* Icon */}
                <div className="w-20 h-20 rounded-full bg-wedo-purple/10 flex items-center justify-center group-hover:bg-wedo-purple/20 transition-colors">
                  <Shield className="w-10 h-10 text-wedo-purple" />
                </div>

                {/* Title */}
                <div>
                  <h2
                    className="text-2xl font-semibold mb-2 lia-text-800 dark:text-lia-text-primary"
                  >
                    Admin Portal
                  </h2>
                  <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">
                    Gestão SaaS e Configurações
                  </p>
                </div>

                {/* Features */}
                <div className="space-y-3 w-full text-left">
                  <div className="flex items-start gap-3">
                    <Building className="w-4 h-4 text-wedo-purple mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                        Gestão de Clientes
                      </p>
                      <p className="text-xs lia-text-400 dark:lia-text-500">
                        Organizações, usuários e acesso
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Zap className="w-4 h-4 text-wedo-purple mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                        Configurações
                      </p>
                      <p className="text-xs lia-text-400 dark:lia-text-500">
                        Integrações, APIs e limites
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <ArrowRight className="w-4 h-4 text-wedo-purple mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                        Métricas SaaS
                      </p>
                      <p className="text-xs lia-text-400 dark:lia-text-500">
                        MRR, ARR, consumo e analytics
                      </p>
                    </div>
                  </div>
                </div>

                {/* CTA */}
                <Link href="/admin" className="w-full">
                  <Button className="w-full bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200">
                    Acessar Admin
                    <Shield className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="text-center mt-12">
          <p className="text-xs lia-text-400 dark:lia-text-500">
            Powered by LIA (Learning Intelligence Assistant) • WedoTalent © 2024
          </p>
        </div>
      </div>
    </div>
  )
}
