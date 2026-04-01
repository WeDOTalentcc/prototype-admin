import React from "react"
import { FileText, Plus } from "lucide-react"
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
import { ConsentVersion } from "@/services/admin/consent-management-service"

const CONSENT_TYPE_LABELS: Record<string, string> = {
  personal_data: 'Dados Pessoais',
  marketing: 'Comunicações Marketing',
  sensitive_data: 'Dados Sensíveis',
  data_sharing: 'Compartilhamento com Clientes',
  cookies: 'Cookies',
  analytics: 'Analytics',
  third_party: 'Terceiros',
}

interface ConsentVersionsTableProps {
  versions: ConsentVersion[]
  onNewVersion: (version: ConsentVersion) => void
}

export function ConsentVersionsTable({ versions, onNewVersion }: ConsentVersionsTableProps) {
  if (versions.length === 0) {
    return null
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Tipo de Consentimento</TableHead>
          <TableHead className="text-center">Versão</TableHead>
          <TableHead>Título</TableHead>
          <TableHead className="text-center">Ativos</TableHead>
          <TableHead className="text-center">Renovação</TableHead>
          <TableHead className="text-center">Expirados</TableHead>
          <TableHead>Criado Em</TableHead>
          <TableHead className="text-center">Status</TableHead>
          <TableHead className="text-right">Ações</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {versions.map((version) => (
          <TableRow key={version.id} className="hover:bg-gray-50">
            <TableCell>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-md flex items-center justify-center bg-gray-200/30">
                  <FileText className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                </div>
                <span className="font-medium lia-text-800 dark:text-lia-text-primary">
                  {CONSENT_TYPE_LABELS[version.consentType] || version.consentType}
                </span>
              </div>
            </TableCell>
            <TableCell className="text-center">
              <Badge variant={version.isCurrent ? "default" : "outline"} className={version.isCurrent ? "bg-gray-900 dark:lia-bg-50" : ""}>
                v{version.version}
              </Badge>
            </TableCell>
            <TableCell>
              <span className="lia-text-500 dark:text-lia-text-tertiary">{version.title}</span>
            </TableCell>
            <TableCell className="text-center">
              <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
                {(version.activeConsentsCount || 0).toLocaleString('pt-BR')}
              </Badge>
            </TableCell>
            <TableCell className="text-center">
              <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
                {version.pendingRenewalCount || 0}
              </Badge>
            </TableCell>
            <TableCell className="text-center">
              <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">
                {version.expiredCount || 0}
              </Badge>
            </TableCell>
            <TableCell>
              <span className="lia-text-500 dark:text-lia-text-tertiary">
                {new Date(version.createdAt).toLocaleDateString('pt-BR')}
              </span>
            </TableCell>
            <TableCell className="text-center">
              {version.isCurrent ? (
                <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Atual</Badge>
              ) : version.isActive ? (
                <Badge className="lia-text-900 dark:lia-text-50 hover:bg-gray-100">Ativo</Badge>
              ) : (
                <Badge className="bg-gray-100 lia-text-800 dark:text-lia-text-primary hover:bg-gray-100">Inativo</Badge>
              )}
            </TableCell>
            <TableCell className="text-right">
              <Button variant="ghost" size="sm" onClick={() => onNewVersion(version)}>
                <Plus className="w-4 h-4 mr-1" />
                Nova Versão
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
