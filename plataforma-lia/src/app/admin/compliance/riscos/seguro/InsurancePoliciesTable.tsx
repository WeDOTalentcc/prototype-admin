import React from "react"
import { Edit2, Trash2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { InsurancePolicy } from "@/services/admin/insurance-service"

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'active':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15"><span className="mr-1">✓</span>Ativo</Badge>
    case 'expired':
      return <Badge className="bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-bg-tertiary">Expirado</Badge>
    case 'pending':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">Pendente</Badge>
    case 'cancelled':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">Cancelado</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

const getClaimStatusBadge = (status: string) => {
  switch (status) {
    case 'open':
      return <Badge className="text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-lia-bg-tertiary">Aberto</Badge>
    case 'under_review':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">Em Análise</Badge>
    case 'approved':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Aprovado</Badge>
    case 'denied':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">Negado</Badge>
    case 'paid':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Pago</Badge>
    case 'closed':
      return <Badge className="bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-bg-tertiary">Encerrado</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

interface InsurancePoliciesTableProps {
  policies: InsurancePolicy[]
  onEdit: (policy: InsurancePolicy) => void
  onDelete: (policyId: string) => void
}

export function InsurancePoliciesTable({ policies, onEdit, onDelete }: InsurancePoliciesTableProps) {
  if (policies.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
        Nenhuma apólice cadastrada
      </div>
    )
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Número da Apólice</TableHead>
          <TableHead>Seguradora</TableHead>
          <TableHead>Cobertura</TableHead>
          <TableHead>Vigência</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="w-[100px]">Ações</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {policies.map((policy) => (
          <TableRow key={policy.id}>
            <TableCell>
              <Badge variant="outline" className="font-mono text-xs">{policy.policyNumber}</Badge>
            </TableCell>
            <TableCell>
              <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">{policy.insurer}</span>
            </TableCell>
            <TableCell>
              <span className="text-sm text-status-success font-medium">{formatCurrency(policy.coverage)}</span>
            </TableCell>
            <TableCell>
              <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                {new Date(policy.startDate).toLocaleDateString('pt-BR')} - {new Date(policy.endDate).toLocaleDateString('pt-BR')}
              </span>
            </TableCell>
            <TableCell>{getStatusBadge(policy.status)}</TableCell>
            <TableCell>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => onEdit(policy)}>
                  <Edit2 className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-status-error" onClick={() => onDelete(policy.id)}>
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

interface InsuranceClaimsTableProps {
  claims: Array<{
    id: string
    claimNumber: string
    incidentDate: string
    description: string
    claimAmount?: number
    status: string
  }>
}

export function InsuranceClaimsTable({ claims }: InsuranceClaimsTableProps) {
  if (claims.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
        Nenhum sinistro registrado
      </div>
    )
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Número</TableHead>
          <TableHead>Data do Incidente</TableHead>
          <TableHead>Descrição</TableHead>
          <TableHead>Valor</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {claims.map((claim) => (
          <TableRow key={claim.id}>
            <TableCell>
              <Badge variant="outline" className="font-mono text-xs">{claim.claimNumber}</Badge>
            </TableCell>
            <TableCell>
              <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                {new Date(claim.incidentDate).toLocaleDateString('pt-BR')}
              </span>
            </TableCell>
            <TableCell>
              <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                {claim.description.length > 50 ? `${claim.description.substring(0, 50)}...` : claim.description}
              </span>
            </TableCell>
            <TableCell>
              {claim.claimAmount ? (
                <span className="text-sm text-status-warning font-medium">{formatCurrency(claim.claimAmount)}</span>
              ) : (
                <span className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">-</span>
              )}
            </TableCell>
            <TableCell>{getClaimStatusBadge(claim.status)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
