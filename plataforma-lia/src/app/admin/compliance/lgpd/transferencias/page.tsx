"use client"

import React, { useState } from "react"
import Link from "next/link"
import { Globe, ChevronLeft, Plus, AlertTriangle, Shield, Calendar, FileText, Search, Info, Building2, Database, MoreHorizontal } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const transfers = [
  { id: 1, country: 'Estados Unidos', legalBasis: 'Cláusulas Contratuais Padrão (SCCs)', subprocessors: ['AWS', 'Anthropic', 'Pearch AI'], safeguards: 'SCCs 2021', status: 'compliant', lastReview: '2024-12-01' },
  { id: 2, country: 'União Europeia', legalBasis: 'Adequação (GDPR)', subprocessors: [], safeguards: 'Adequação reconhecida', status: 'compliant', lastReview: '2024-10-20' },
  { id: 3, country: 'Reino Unido', legalBasis: 'Cláusulas Contratuais Padrão (SCCs)', subprocessors: ['Clientes UK'], safeguards: 'SCCs 2021 + UK Addendum', status: 'compliant', lastReview: '2024-09-15' },
  { id: 4, country: 'Canadá', legalBasis: 'Decisão de Adequação', subprocessors: ['Parceiro Tecnológico'], safeguards: 'PIPEDA Adequação', status: 'pending_review', lastReview: '2024-06-10' },
]

const paisesAdequados = ['União Europeia', 'Reino Unido', 'Canadá', 'Argentina', 'Uruguai', 'Suíça', 'Nova Zelândia', 'Japão', 'Coreia do Sul', 'Israel']

const legalBasisOptions = [
  { value: 'scc', label: 'Standard Contractual Clauses (SCCs)' },
  { value: 'adequacy', label: 'Adequacy Decision' },
  { value: 'consent', label: 'Consentimento Específico' },
  { value: 'bcr', label: 'Binding Corporate Rules (BCRs)' },
]

export default function TransferenciasPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [isModalOpen, setIsModalOpen] = useState(false)

  const filteredTransfers = transfers.filter(t =>
    t.country.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.legalBasis.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.subprocessors.some(s => s.toLowerCase().includes(searchTerm.toLowerCase())) ||
    t.safeguards.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getRiskBadge = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low':
        return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Baixo</Badge>
      case 'medium':
        return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">Médio</Badge>
      case 'high':
        return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">Alto</Badge>
      default:
        return <Badge>{riskLevel}</Badge>
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'compliant':
        return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Conforme</Badge>
      case 'pending_review':
        return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">Revisão Pendente</Badge>
      case 'under_review':
 return <Badge className="text-gray-600 dark:text-gray-400 hover:bg-gray-100">Em Análise</Badge>
      case 'non_compliant':
        return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">Não Conforme</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const isAdequateCountry = (country: string) => {
    return paisesAdequados.some(p => country.toLowerCase().includes(p.toLowerCase()))
  }

  const compliantTransfers = transfers.filter(t => t.status === 'compliant').length
  const pendingReviews = transfers.filter(t => t.status === 'pending_review' || t.status === 'under_review').length
  const uniqueCountries = [...new Set(transfers.map(t => t.country))].length

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-2 mb-4">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/admin/compliance/lgpd">
              <ChevronLeft className="w-4 h-4 mr-1" />
              Voltar
            </Link>
          </Button>
        </div>

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center"
              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
            >
              <Globe className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold"
                style={{ 
                  color: 'var(--eleven-text-primary)',
                  
                }}
              >
                Transferências Internacionais
              </h1>
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Gestão de transferências internacionais de dados pessoais
              </p>
            </div>
          </div>
          
          <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Nova Transferência
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[550px]">
              <DialogHeader>
                <DialogTitle>Registrar Transferência Internacional</DialogTitle>
                <DialogDescription>
                  Registre uma nova transferência internacional de dados pessoais.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="country">País de Destino</Label>
                  <Input id="country" placeholder="Ex: Estados Unidos" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="recipient">Destinatário</Label>
                  <Input id="recipient" placeholder="Ex: Amazon Web Services" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="legal-basis">Base Legal</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione a base legal" />
                    </SelectTrigger>
                    <SelectContent>
                      {legalBasisOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="data-types">Tipos de Dados Transferidos</Label>
                  <Input id="data-types" placeholder="Ex: Dados de candidatos, currículos" />
                </div>
                <div className="p-3 rounded-md bg-status-warning/10 border border-status-warning/30">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-status-warning mt-0.5" />
                    <p className="text-xs text-status-warning">
                      Para países sem decisão de adequação, é obrigatório o uso de mecanismos de proteção 
                      como SCCs ou BCRs, conforme Art. 33 da LGPD.
                    </p>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" onClick={() => setIsModalOpen(false)}>
                  Registrar Transferência
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <Card className="mb-6" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', borderColor: 'rgba(245, 158, 11, 0.3)', backgroundColor: 'rgba(245, 158, 11, 0.05)' }}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-status-warning mt-0.5" />
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  Aviso sobre Adequação de Países (Art. 33 LGPD)
                </p>
                <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Transferências para países sem decisão de adequação da ANPD exigem mecanismos adicionais 
                  de proteção: Cláusulas Contratuais Padrão (SCCs), Binding Corporate Rules (BCRs), 
                  ou consentimento específico e destacado do titular.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <Globe className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{transfers.length}</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Total de Transferências</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                  <Shield className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{compliantTransfers}</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Conformes</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
                  <Calendar className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{pendingReviews}</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Revisões Pendentes</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <Database className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{uniqueCountries}</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Países de Destino</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Lista de Transferências Internacionais
              </CardTitle>
              <div className="relative w-72">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
                <Input
                  placeholder="Buscar por país, destinatário..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>País</TableHead>
                  <TableHead>Base Legal</TableHead>
                  <TableHead>Subprocessadores</TableHead>
                  <TableHead>Salvaguardas</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Adequação</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTransfers.map((transfer) => (
                  <TableRow key={transfer.id} className="hover:bg-gray-50">
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                          <Globe className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        </div>
                        <span className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{transfer.country}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {transfer.legalBasis}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {transfer.subprocessors.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {transfer.subprocessors.map((sp, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs bg-gray-100">
                              <Building2 className="w-3 h-3 mr-1" />
                              {sp}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Nenhum</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Shield className="w-3 h-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
                        <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                          {transfer.safeguards}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(transfer.status)}</TableCell>
                    <TableCell>
                      {isAdequateCountry(transfer.country) ? (
                        <div className="flex items-center gap-1">
                          <Shield className="w-4 h-4 text-status-success" />
                          <span className="text-xs text-status-success">País Adequado</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1">
                          <Info className="w-4 h-4 text-status-warning" />
                          <span className="text-xs text-status-warning">Requer SCCs</span>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>Ver detalhes</DropdownMenuItem>
                          <DropdownMenuItem>Editar</DropdownMenuItem>
                          <DropdownMenuItem>Agendar revisão</DropdownMenuItem>
                          <DropdownMenuItem className="text-status-error">Desativar</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card className="mt-6" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardHeader>
            <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Países com Decisão de Adequação
            </CardTitle>
            <CardDescription>
              Países reconhecidos internacionalmente como tendo nível adequado de proteção de dados
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {paisesAdequados.map((pais) => (
                <Badge key={pais} variant="outline" className="bg-status-success/10 border-status-success/30 text-status-success">
                  <Shield className="w-3 h-3 mr-1" />
                  {pais}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
