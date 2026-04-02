import React from "react"
import { Building2, FileText, DollarSign, Calendar, Clock, Shield, Edit2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { InsurancePolicy } from "@/services/admin/insurance-service"

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)

interface ActivePolicyCardProps {
  activePolicy: InsurancePolicy
  daysRemaining: number
  isExpiringSoon: boolean
  isExpired: boolean
  statusBadge: React.ReactNode
  onEdit: (policy: InsurancePolicy) => void
}

export function ActivePolicyCard({ activePolicy, daysRemaining, isExpiringSoon, isExpired, statusBadge, onEdit }: ActivePolicyCardProps) {
  return (
    <Card className="lg:col-span-2">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Dados da Apólice Ativa
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {statusBadge}
            <Button variant="ghost" size="icon" onClick={() => onEdit(activePolicy)}>
              <Edit2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary">
              <Building2 className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5" />
              <div>
                <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">Seguradora</p>
                <p className="font-medium text-lia-text-primary dark:text-lia-text-primary">{activePolicy.insurer}</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary">
              <FileText className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5" />
              <div>
                <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">Número da Apólice</p>
                <p className="font-mono font-medium text-lia-text-primary dark:text-lia-text-primary">{activePolicy.policyNumber}</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary">
              <DollarSign className="w-5 h-5 text-status-success mt-0.5" />
              <div>
                <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">Valor de Cobertura</p>
                <p className="font-medium text-status-success text-lg">{formatCurrency(activePolicy.coverage)}</p>
              </div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary">
              <DollarSign className="w-5 h-5 text-status-warning mt-0.5" />
              <div>
                <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">Franquia</p>
                <p className="font-medium text-lia-text-primary dark:text-lia-text-primary">{formatCurrency(activePolicy.deductible)}</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary">
              <Calendar className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5" />
              <div>
                <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">Vigência</p>
                <p className="font-medium text-lia-text-primary dark:text-lia-text-primary">
                  {new Date(activePolicy.startDate).toLocaleDateString('pt-BR')} a {new Date(activePolicy.endDate).toLocaleDateString('pt-BR')}
                </p>
              </div>
            </div>
            <div className="p-3 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
                  <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">Tempo restante</span>
                </div>
                <span className={`text-sm font-medium ${isExpiringSoon ? 'text-status-warning' : isExpired ? 'text-status-error' : 'lia-text-800 dark:text-lia-text-primary'}`}>
                  {isExpired ? 'Expirado' : `${daysRemaining} dias`}
                </span>
              </div>
              <Progress value={isExpired ? 100 : Math.min(100, (1 - daysRemaining / 365) * 100)} className="h-2" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
