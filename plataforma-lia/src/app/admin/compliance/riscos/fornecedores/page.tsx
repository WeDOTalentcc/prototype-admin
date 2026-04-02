"use client"

import React, { useState } from "react"
import { 
  Truck, 
  Search, 
  Plus, 
  Filter,
  MoreHorizontal,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Building2,
  Calendar,
  FileCheck,
  ExternalLink,
  Shield,
  Award,
  Info
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const vendors = [
  { 
    id: 1, 
    name: 'Amazon Web Services (AWS)', 
    serviceType: 'Cloud Infrastructure', 
    criticality: 'Alta',
    securityScore: 'A', 
    lastAssessment: '2024-12-01', 
    nextAssessment: '2025-06-01',
    status: 'approved', 
    certifications: ['ISO 27001', 'SOC 2 Type II', 'PCI DSS']
  },
  { 
    id: 2, 
    name: 'Anthropic', 
    serviceType: 'AI/LLM Provider', 
    criticality: 'Alta',
    securityScore: 'A', 
    lastAssessment: '2024-11-15', 
    nextAssessment: '2025-05-15',
    status: 'approved', 
    certifications: ['SOC 2 Type II']
  },
  { 
    id: 3, 
    name: 'Neon', 
    serviceType: 'Database as a Service', 
    criticality: 'Alta',
    securityScore: 'A', 
    lastAssessment: '2024-10-20', 
    nextAssessment: '2025-04-20',
    status: 'approved', 
    certifications: ['SOC 2 Type II', 'ISO 27001']
  },
  { 
    id: 4, 
    name: 'SendGrid', 
    serviceType: 'Email Service Provider', 
    criticality: 'Média',
    securityScore: 'B', 
    lastAssessment: '2024-09-10', 
    nextAssessment: '2025-03-10',
    status: 'approved', 
    certifications: ['SOC 2 Type II', 'ISO 27001']
  },
  { 
    id: 5, 
    name: 'Pearch', 
    serviceType: 'Talent Search Provider', 
    criticality: 'Alta',
    securityScore: 'B', 
    lastAssessment: '2024-11-01', 
    nextAssessment: '2025-05-01',
    status: 'approved', 
    certifications: ['SOC 2 Type II']
  },
]

const getScoreColor = (score: string) => {
  switch (score) {
    case 'A': return { bg: 'bg-status-success/15', text: 'text-status-success', border: 'border-status-success/30' }
    case 'B': return { bg: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary', text: 'text-lia-text-secondary dark:text-lia-text-tertiary', border: 'border-lia-border-default dark:border-lia-border-default' }
    case 'C': return { bg: 'bg-status-warning/15', text: 'text-status-warning', border: 'border-status-warning/30' }
    case 'D': return { bg: 'bg-wedo-orange/15', text: 'text-wedo-orange', border: 'border-wedo-orange/30' }
    case 'F': return { bg: 'bg-status-error/15', text: 'text-status-error', border: 'border-status-error/30' }
    default: return { bg: 'bg-lia-bg-tertiary', text: 'text-lia-text-primary dark:text-lia-text-primary', border: 'border-lia-border-default' }
  }
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'approved':
      return { icon: CheckCircle2, color: 'text-status-success', bg: 'bg-status-success/15', label: 'Aprovado' }
    case 'pending':
      return { icon: Clock, color: 'text-status-warning', bg: 'bg-status-warning/15', label: 'Pendente' }
    case 'rejected':
      return { icon: AlertTriangle, color: 'text-status-error', bg: 'bg-status-error/15', label: 'Rejeitado' }
    default:
      return { icon: Clock, color: 'text-lia-text-secondary', bg: 'bg-lia-bg-tertiary', label: status }
  }
}

const getCriticalityColor = (criticality: string) => {
  switch (criticality) {
    case 'Alta':
      return 'bg-status-error/15 text-status-error'
    case 'Média':
      return 'bg-status-warning/15 text-status-warning'
    case 'Baixa':
      return 'bg-status-success/15 text-status-success'
    default:
      return 'bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary'
  }
}

const getServiceTypeColor = (serviceType: string) => {
  const colors: Record<string, string> = {
    'Cloud Infrastructure': 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary',
    'AI/LLM Provider': 'bg-wedo-purple/15 text-wedo-purple',
    'Database as a Service': 'bg-status-success/15 text-status-success',
    'Email Service Provider': 'bg-status-warning/15 text-status-warning',
    'Frontend Hosting': 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary',
    'Payment Processing': 'bg-wedo-magenta/15 text-wedo-magenta',
    'Talent Search Provider': 'bg-wedo-purple/15 text-wedo-purple',
  }
  return colors[serviceType] || 'bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary'
}

export default function FornecedoresPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredVendors = vendors.filter(vendor =>
    vendor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    vendor.serviceType.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const totalVendors = vendors.length
  const approvedVendors = vendors.filter(v => v.status === 'approved').length
  const scoreAVendors = vendors.filter(v => v.securityScore === 'A').length
  const scoreBVendors = vendors.filter(v => v.securityScore === 'B').length
  const highCriticalityVendors = vendors.filter(v => v.criticality === 'Alta').length

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
            >
              <Truck className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
                
              >
                Due Diligence Supply Chain
              </h1>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                Avaliação de riscos de fornecedores e terceiros
              </p>
            </div>
          </div>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Adicionar Fornecedor
          </Button>
        </div>

        <Card className="mb-6" style={{borderLeft: '4px solid var(--status-warning)'}}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-status-warning mt-0.5" />
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium text-sm text-status-warning">
                    Due Diligence Obrigatória - BCB 498/2025
                  </p>
                  <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15 text-micro">
                    Obrigatório
                  </Badge>
                </div>
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                  A Resolução BCB 498/2025 exige due diligence para todos os fornecedores de serviços de processamento 
                  e armazenamento de dados em nuvem. Todos os fornecedores críticos devem ser avaliados quanto a 
                  certificações de segurança, políticas de privacidade e conformidade regulatória.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                  <Building2 className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary" >{totalVendors}</p>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Total</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary" >{approvedVendors}</p>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Aprovados</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-red-500/10">
                  <AlertTriangle className="w-5 h-5 text-status-error" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary" >{highCriticalityVendors}</p>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Alta Criticidade</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <Award className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary" >{scoreAVendors}</p>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Score A</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                  <Shield className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary" >{scoreBVendors}</p>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Score B</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <Card >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                Lista de Fornecedores Avaliados
              </CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                  <Input
                    placeholder="Buscar fornecedores..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <Button variant="outline" size="icon">
                  <Filter className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fornecedor</TableHead>
                    <TableHead>Tipo de Serviço</TableHead>
                    <TableHead className="text-center">Criticidade</TableHead>
                    <TableHead className="text-center">Score</TableHead>
                    <TableHead>Última Avaliação</TableHead>
                    <TableHead>Próxima Avaliação</TableHead>
                    <TableHead>Certificações</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredVendors.map((vendor) => {
                    const scoreConfig = getScoreColor(vendor.securityScore)
                    const statusConfig = getStatusConfig(vendor.status)
                    const StatusIcon = statusConfig.icon
                    
                    return (
                      <TableRow key={vendor.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                              <Building2 className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                            </div>
                            <span className="font-medium text-lia-text-primary dark:text-lia-text-primary" >
                              {vendor.name}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={`text-xs ${getServiceTypeColor(vendor.serviceType)}`}>
                            {vendor.serviceType}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge className={`text-xs ${getCriticalityColor(vendor.criticality)}`}>
                            {vendor.criticality}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge className={`text-lg font-bold px-3 py-1 ${scoreConfig.bg} ${scoreConfig.text} ${scoreConfig.border}`}>
                            {vendor.securityScore}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                            <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                              {new Date(vendor.lastAssessment).toLocaleDateString('pt-BR')}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                            <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                              {new Date(vendor.nextAssessment).toLocaleDateString('pt-BR')}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {vendor.certifications.map((cert, index) => (
                              <Badge 
                                key={cert} 
                                variant="outline" 
                                className="text-micro"
                              >
                                {cert}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.color}`}>
                            <StatusIcon className="w-3 h-3" />
                            {statusConfig.label}
                          </div>
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>
                                <ExternalLink className="w-4 h-4 mr-2" />
                                Ver detalhes
                              </DropdownMenuItem>
                              <DropdownMenuItem>Iniciar avaliação</DropdownMenuItem>
                              <DropdownMenuItem>Ver histórico</DropdownMenuItem>
                              <DropdownMenuItem>Baixar relatório</DropdownMenuItem>
                              <DropdownMenuItem className="text-status-error">Remover</DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
