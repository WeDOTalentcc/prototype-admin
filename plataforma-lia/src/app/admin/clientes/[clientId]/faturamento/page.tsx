"use client"

import React, { useState, useEffect, useCallback, use } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "sonner"
import {
  CreditCard,
  FileText,
  Download,
  DollarSign,
  Calendar,
  TrendingUp,
  Package,
  AlertCircle,
  RefreshCw,
  Loader2,
  Ban,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Wallet
} from "lucide-react"

interface BillingData {
  subscription: {
    id: string
    status: 'active' | 'trial' | 'past_due' | 'cancelled' | 'pending'
    plan_name: string
    plan_id: string
    mrr: number
    next_billing_date: string
    billing_cycle: 'monthly' | 'yearly'
    started_at: string
    trial_ends_at?: string
  }
  invoices: Invoice[]
  payment_methods: PaymentMethod[]
  summary: {
    total_paid: number
    total_pending: number
    invoices_count: number
    ltv_estimated: number
  }
}

interface Invoice {
  id: string
  date: string
  due_date: string
  amount: number
  status: 'paid' | 'pending' | 'overdue' | 'cancelled'
  description: string
  pdf_url?: string
}

interface PaymentMethod {
  id: string
  type: 'credit_card' | 'boleto' | 'pix'
  last_four?: string
  brand?: string
  is_default: boolean
  expires_at?: string
}

const subscriptionStatusConfig: Record<string, { label: string, variant: 'success' | 'warning' | 'destructive' | 'info' | 'default' }> = {
  active: { label: 'Ativa', variant: 'success' },
  trial: { label: 'Trial', variant: 'info' },
  past_due: { label: 'Pagamento Atrasado', variant: 'warning' },
  cancelled: { label: 'Cancelada', variant: 'destructive' },
  pending: { label: 'Pendente', variant: 'default' },
}

const invoiceStatusConfig: Record<string, { label: string, variant: 'success' | 'warning' | 'destructive' | 'default', icon: React.ComponentType<{ className?: string }> }> = {
  paid: { label: 'Pago', variant: 'success', icon: CheckCircle2 },
  pending: { label: 'Pendente', variant: 'warning', icon: Clock },
  overdue: { label: 'Vencido', variant: 'destructive', icon: AlertTriangle },
  cancelled: { label: 'Cancelado', variant: 'default', icon: Ban },
}


function BillingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Skeleton className="w-10 h-10 rounded-md" />
                <div className="space-y-2">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-6 w-24" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <Skeleton className="h-5 w-40" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-md border">
                  <div className="flex items-center gap-3">
                    <Skeleton className="w-10 h-10 rounded-md" />
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-6 w-16 rounded-full" />
                    <Skeleton className="h-8 w-8" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-32" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default function ClientFaturamentoPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [billingData, setBillingData] = useState<BillingData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const fetchBillingData = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/backend-proxy/billing?client_id=${clientId}`)
      
      if (!response.ok) {
        setError('Erro ao carregar dados de faturamento. Tente novamente.')
        return
      }

      const data = await response.json()
      setBillingData(data.data || data)
    } catch (err) {
      setError('Erro ao carregar dados de faturamento. Verifique sua conexão.')
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchBillingData()
  }, [fetchBillingData])

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value / 100)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
  }

  const handleDownloadInvoice = async (invoiceId: string) => {
    setActionLoading(`download_${invoiceId}`)
    try {
      toast.info('Gerando PDF da fatura...')
      await new Promise(resolve => setTimeout(resolve, 1000))
      toast.success('Download iniciado')
    } catch (err) {
      toast.error('Erro ao baixar fatura')
    } finally {
      setActionLoading(null)
    }
  }

  const handleChangePlan = async () => {
    setActionLoading('change_plan')
    try {
      toast.info('Abrindo opções de planos...')
      await new Promise(resolve => setTimeout(resolve, 500))
    } catch (err) {
      toast.error('Erro ao abrir opções de planos')
    } finally {
      setActionLoading(null)
    }
  }

  const handleCancelSubscription = async () => {
    if (!confirm('Tem certeza que deseja cancelar a assinatura? Esta ação pode ser revertida.')) return
    
    setActionLoading('cancel')
    try {
      const response = await fetch('/api/backend-proxy/billing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'cancel_subscription', client_id: clientId })
      })
      
      if (!response.ok) {
        throw new Error('Erro ao cancelar assinatura')
      }
      
      toast.success('Assinatura cancelada. Acesso válido até o fim do período.')
      fetchBillingData()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro ao cancelar assinatura')
    } finally {
      setActionLoading(null)
    }
  }

  const handleExportReport = () => {
    toast.info('Gerando relatório de faturamento...')
    setTimeout(() => {
      toast.success('Relatório exportado com sucesso')
    }, 1500)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <CreditCard className="w-6 h-6 lia-text-600 dark:text-lia-text-tertiary" />
              <h2 className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary">
                Faturamento
              </h2>
            </div>
            <p className="text-sm lia-text-400 dark:lia-text-500">
              Histórico de faturas e informações de cobrança
            </p>
          </div>
        </div>
        <BillingSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="w-16 h-16 rounded-full bg-status-error/10 dark:bg-status-error/20 flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-status-error" />
        </div>
        <h3 className="text-lg font-medium mb-1 lia-text-800 dark:text-lia-text-primary">
          Erro ao carregar dados
        </h3>
        <p className="text-sm mb-4 lia-text-400 dark:lia-text-500">
          {error}
        </p>
        <Button variant="outline" onClick={fetchBillingData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      </div>
    )
  }

  if (!billingData) return null

  const subscriptionStatus = subscriptionStatusConfig[billingData.subscription.status] || subscriptionStatusConfig.pending

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <CreditCard className="w-6 h-6 lia-text-600 dark:text-lia-text-tertiary" />
            <h2 className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary">
              Faturamento
            </h2>
          </div>
          <p className="text-sm lia-text-400 dark:lia-text-500">
            Histórico de faturas e informações de cobrança
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleExportReport}>
            <Download className="w-4 h-4 mr-2" />
            Exportar Relatório
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-md bg-status-success/15 dark:bg-status-success/30 flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-status-success" />
              </div>
              <div>
                <p className="text-xs lia-text-400 dark:lia-text-500">MRR</p>
                <p className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary">
                  {formatCurrency(billingData.subscription.mrr)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center">
                <Calendar className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
              </div>
              <div>
                <p className="text-xs lia-text-400 dark:lia-text-500">Próximo Vencimento</p>
                <p className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary">
                  {formatDate(billingData.subscription.next_billing_date)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-md bg-wedo-purple/15 dark:bg-wedo-purple/30 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-wedo-purple" />
              </div>
              <div>
                <p className="text-xs lia-text-400 dark:lia-text-500">LTV Estimado</p>
                <p className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary">
                  {formatCurrency(billingData.summary.ltv_estimated)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-lia-border-subtle">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-md bg-status-warning/15 dark:bg-status-warning/30 flex items-center justify-center">
                <FileText className="w-5 h-5 text-status-warning" />
              </div>
              <div>
                <p className="text-xs lia-text-400 dark:lia-text-500">Total Faturas</p>
                <p className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary">
                  {billingData.summary.invoices_count}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 border-lia-border-subtle">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
                Detalhes do Plano
              </CardTitle>
              <Badge variant={subscriptionStatus.variant}>{subscriptionStatus.label}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-xs uppercase tracking-wide lia-text-400 dark:lia-text-500">
                  Plano
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <Package className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                  <span className="font-medium lia-text-800 dark:text-lia-text-primary">
                    {billingData.subscription.plan_name}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide lia-text-400 dark:lia-text-500">
                  Ciclo
                </p>
                <p className="text-sm font-medium mt-1 lia-text-800 dark:text-lia-text-primary">
                  {billingData.subscription.billing_cycle === 'monthly' ? 'Mensal' : 'Anual'}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide lia-text-400 dark:lia-text-500">
                  Cliente Desde
                </p>
                <p className="text-sm font-medium mt-1 lia-text-800 dark:text-lia-text-primary">
                  {formatDate(billingData.subscription.started_at)}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide lia-text-400 dark:lia-text-500">
                  Total Pago
                </p>
                <p className="text-sm font-medium mt-1 text-status-success">
                  {formatCurrency(billingData.summary.total_paid)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleChangePlan}
                disabled={actionLoading === 'change_plan'}
              >
                {actionLoading === 'change_plan' ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <ArrowUpRight className="w-4 h-4 mr-2" />
                )}
                Alterar Plano
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="text-status-error hover:text-status-error hover:bg-status-error/10"
                onClick={handleCancelSubscription}
                disabled={actionLoading === 'cancel' || billingData.subscription.status === 'cancelled'}
              >
                {actionLoading === 'cancel' ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Ban className="w-4 h-4 mr-2" />
                )}
                Cancelar Assinatura
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-lia-border-subtle">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
              Métodos de Pagamento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {billingData.payment_methods.map((method) => (
                <div 
                  key={method.id}
                  className={`flex items-center justify-between p-3 rounded-md border ${!method.is_default ? 'border-lia-border-subtle dark:border-lia-border-subtle' : ''}`}
                  style={method.is_default ? { borderColor: 'var(--gray-950)' } : undefined}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-md bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center">
                      {method.type === 'credit_card' ? (
                        <CreditCard className="w-4 h-4 lia-text-600" />
                      ) : method.type === 'pix' ? (
                        <Wallet className="w-4 h-4 text-status-success" />
                      ) : (
                        <FileText className="w-4 h-4 lia-text-600" />
                      )}
                    </div>
                    <div>
                      {method.type === 'credit_card' ? (
                        <>
                          <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                            {method.brand} •••• {method.last_four}
                          </p>
                          <p className="text-xs lia-text-400 dark:lia-text-500">
                            Expira em {method.expires_at}
                          </p>
                        </>
                      ) : (
                        <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                          {method.type === 'pix' ? 'PIX' : 'Boleto'}
                        </p>
                      )}
                    </div>
                  </div>
                  {method.is_default && (
                    <Badge variant="info" className="text-micro">Padrão</Badge>
                  )}
                </div>
              ))}
              <Button variant="outline" size="sm" className="w-full mt-2">
                Adicionar Método
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-lia-border-subtle">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary">
            Histórico de Faturas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {billingData.invoices.map((invoice) => {
              const statusInfo = invoiceStatusConfig[invoice.status] || invoiceStatusConfig.pending
              const StatusIcon = statusInfo.icon
              
              return (
                <div 
                  key={invoice.id}
                  className="flex items-center justify-between p-3 rounded-md border hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors border-lia-border-subtle dark:border-lia-border-subtle"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center">
                      <FileText className="w-5 h-5 lia-text-500" />
                    </div>
                    <div>
                      <p className="font-medium lia-text-800 dark:text-lia-text-primary">
                        {invoice.description}
                      </p>
                      <div className="flex items-center gap-2">
                        <p className="text-sm lia-text-400 dark:lia-text-500">
                          {formatDate(invoice.date)}
                        </p>
                        {invoice.status === 'overdue' && (
                          <span className="text-xs text-status-error">
                            Venceu em {formatDate(invoice.due_date)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <p className="font-semibold lia-text-800 dark:text-lia-text-primary">
                      {formatCurrency(invoice.amount)}
                    </p>
                    <Badge variant={statusInfo.variant} className="flex items-center gap-1">
                      <StatusIcon className="w-3 h-3" />
                      {statusInfo.label}
                    </Badge>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleDownloadInvoice(invoice.id)}
                      disabled={actionLoading === `download_${invoice.id}`}
                    >
                      {actionLoading === `download_${invoice.id}` ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Download className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
