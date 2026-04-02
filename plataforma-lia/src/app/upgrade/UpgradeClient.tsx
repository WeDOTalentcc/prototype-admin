"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, ArrowRight, Brain } from "lucide-react"
import Link from "next/link"

const PLANS = [
  {
    name: "Starter",
    price: "R$ 990",
    period: "/mês",
    features: [
      "5 vagas ativas simultâneas",
      "Até 3 recrutadores",
      "500 candidatos/mês",
      "Triagem WSI básica",
      "Suporte por email",
    ],
    cta: "Assinar Starter",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "R$ 2.490",
    period: "/mês",
    features: [
      "20 vagas ativas simultâneas",
      "Até 10 recrutadores",
      "5.000 candidatos/mês",
      "Triagem WSI completa + Big Five",
      "Integrações ATS (Gupy, Pandapé)",
      "Suporte prioritário",
    ],
    cta: "Assinar Pro",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Sob consulta",
    period: "",
    features: [
      "Vagas e recrutadores ilimitados",
      "White-label / RPO",
      "BYOK (Bring Your Own Key)",
      "SLA garantido",
      "Gerente de conta dedicado",
      "Compliance BCB 498 / SOX",
    ],
    cta: "Falar com vendas",
    highlighted: false,
  },
]

export default function UpgradePage() {
  return (
    <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex flex-col items-center justify-center px-4 py-16">
      <div className="flex items-center gap-2 mb-6">
        <Brain className="h-7 w-7 text-wedo-cyan" />
        <span className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary">LIA by WeDOTalent</span>
      </div>

      <div className="text-center mb-10 max-w-xl">
        <Badge variant="outline" className="mb-4 border-status-warning/30 text-status-warning bg-status-warning/10">
          Período de trial encerrado
        </Badge>
        <h1 className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary mb-3">
          Seu trial expirou
        </h1>
        <p className="text-lia-text-secondary dark:text-lia-text-tertiary text-sm leading-relaxed">
          Para continuar usando a plataforma e manter seus dados, selecione um plano abaixo.
          Seus candidatos e vagas ficam preservados ao fazer upgrade.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
        {PLANS.map((plan) => (
          <div
            key={plan.name}
            className={`rounded-md border bg-lia-bg-primary dark:bg-lia-bg-secondary p-6 flex flex-col gap-5 ${
              plan.highlighted ? "border-lia-btn-primary-bg dark:border-lia-border-medium ring-1 ring-lia-btn-primary-bg dark:ring-lia-border-medium" : "border-lia-border-subtle"
            }`}
          >
            <div>
              {plan.highlighted && (
                <Badge className="mb-3 bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs">Mais popular</Badge>
              )}
              <h2 className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary">{plan.name}</h2>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">{plan.price}</span>
                <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">{plan.period}</span>
              </div>
            </div>

            <ul className="flex flex-col gap-2 flex-1">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm text-lia-text-secondary dark:text-lia-text-secondary">
                  <CheckCircle2 className="h-4 w-4 text-lia-text-tertiary dark:text-lia-text-secondary mt-0.5 shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>

            <Button
              className={`w-full rounded-md text-sm font-medium ${
                plan.highlighted
                  ? "bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
                  : "bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary dark:text-lia-text-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:hover:bg-lia-border-medium"
              }`}
            >
              {plan.cta}
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        ))}
      </div>

      <p className="mt-8 text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
        Dúvidas?{" "}
        <Link href="mailto:contato@wedotalent.com.br" className="underline hover:lia-text-600 dark:hover:lia-text-300">
          Fale com nosso time
        </Link>
      </p>
    </div>
  )
}
