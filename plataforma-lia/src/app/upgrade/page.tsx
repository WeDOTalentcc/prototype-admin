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
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4 py-16">
      <div className="flex items-center gap-2 mb-6">
        <Brain className="h-7 w-7 text-wedo-cyan" />
        <span className="text-xl font-semibold text-gray-900">LIA by WeDOTalent</span>
      </div>

      <div className="text-center mb-10 max-w-xl">
        <Badge variant="outline" className="mb-4 border-status-warning/30 text-status-warning bg-status-warning/10">
          Período de trial encerrado
        </Badge>
        <h1 className="text-2xl font-bold text-gray-900 mb-3">
          Seu trial expirou
        </h1>
        <p className="text-gray-500 text-sm leading-relaxed">
          Para continuar usando a plataforma e manter seus dados, selecione um plano abaixo.
          Seus candidatos e vagas ficam preservados ao fazer upgrade.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
        {PLANS.map((plan) => (
          <div
            key={plan.name}
            className={`rounded-md border bg-white p-6 flex flex-col gap-5 ${
              plan.highlighted ? "border-gray-900 ring-1 ring-gray-900" : "border-gray-200"
            }`}
          >
            <div>
              {plan.highlighted && (
                <Badge className="mb-3 bg-gray-900 text-white text-xs">Mais popular</Badge>
              )}
              <h2 className="text-lg font-semibold text-gray-900">{plan.name}</h2>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-2xl font-bold text-gray-900">{plan.price}</span>
                <span className="text-sm text-gray-500">{plan.period}</span>
              </div>
            </div>

            <ul className="flex flex-col gap-2 flex-1">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm text-gray-600">
                  <CheckCircle2 className="h-4 w-4 text-gray-400 mt-0.5 shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>

            <Button
              className={`w-full rounded-md text-sm font-medium ${
                plan.highlighted
                  ? "bg-gray-900 text-white hover:bg-gray-800"
                  : "bg-white text-gray-900 border border-gray-300 hover:bg-gray-50"
              }`}
            >
              {plan.cta}
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        ))}
      </div>

      <p className="mt-8 text-xs text-gray-400">
        Dúvidas?{" "}
        <Link href="mailto:contato@wedotalent.com.br" className="underline hover:text-gray-600">
          Fale com nosso time
        </Link>
      </p>
    </div>
  )
}
