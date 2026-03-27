"use client"

import React, { useState } from "react"
import Link from "next/link"
import { UserCheck, Plus, Mail, Phone, Calendar, ChevronLeft, MoreHorizontal, Search, Star, X, Building2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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

const dpos = [
  { id: 1, name: 'Ana Paula Santos', email: 'dpo@wedotalent.com', phone: '+55 11 98765-4321', company: 'WeDo Talent', since: '2024-01-01', status: 'active', isPrimary: true },
  { id: 2, name: 'Carlos Eduardo Lima', email: 'privacidade@cliente1.com', phone: '+55 21 99876-5432', company: 'Cliente Demo', since: '2024-03-15', status: 'active', isPrimary: false },
]

export default function DPOPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [newDpo, setNewDpo] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    status: 'active',
    isPrimary: false
  })

  const filteredDPOs = dpos.filter(dpo => 
    dpo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dpo.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Ativo</Badge>
      case 'inactive':
        return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">Inativo</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  const activeDPOs = dpos.filter(d => d.status === 'active').length
  const primaryDPO = dpos.find(d => d.isPrimary)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsModalOpen(false)
    setNewDpo({ name: '', email: '', phone: '', company: '', status: 'active', isPrimary: false })
  }

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
              <UserCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold"
                style={{ 
                  color: 'var(--eleven-text-primary)',
                  
                }}
              >
                Registro de DPOs
              </h1>
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Encarregados de Proteção de Dados (Data Protection Officers)
              </p>
            </div>
          </div>
          
          <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Adicionar DPO
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Cadastrar Novo DPO</DialogTitle>
                <DialogDescription>
                  Adicione um novo Encarregado de Proteção de Dados (DPO) ao sistema.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit}>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Nome Completo</Label>
                    <Input
                      id="name"
                      placeholder="Ex: Maria Silva"
                      value={newDpo.name}
                      onChange={(e) => setNewDpo({ ...newDpo, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="Ex: dpo@empresa.com"
                      value={newDpo.email}
                      onChange={(e) => setNewDpo({ ...newDpo, email: e.target.value })}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="phone">Telefone</Label>
                    <Input
                      id="phone"
                      placeholder="Ex: +55 11 99999-0000"
                      value={newDpo.phone}
                      onChange={(e) => setNewDpo({ ...newDpo, phone: e.target.value })}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="company">Empresa</Label>
                    <Input
                      id="company"
                      placeholder="Ex: WeDo Talent"
                      value={newDpo.company}
                      onChange={(e) => setNewDpo({ ...newDpo, company: e.target.value })}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="status">Status</Label>
                    <Select
                      value={newDpo.status}
                      onValueChange={(value) => setNewDpo({ ...newDpo, status: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione o status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active">Ativo</SelectItem>
                        <SelectItem value="inactive">Inativo</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="isPrimary"
                      checked={newDpo.isPrimary}
                      onChange={(e) => setNewDpo({ ...newDpo, isPrimary: e.target.checked })}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor="isPrimary" className="text-sm font-normal cursor-pointer">
                      Definir como DPO Principal
                    </Label>
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit">Salvar DPO</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <UserCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{dpos.length}</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Total de DPOs</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                  <UserCheck className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{activeDPOs}</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>DPOs Ativos</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
                  <Star className="w-5 h-5 text-amber-500" />
                </div>
                <div>
                  <p className="text-sm font-semibold truncate" style={{ color: 'var(--eleven-text-primary)' }}>
                    {primaryDPO?.name || 'Não definido'}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>DPO Principal</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Lista de DPOs Cadastrados
              </CardTitle>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
                <Input
                  placeholder="Buscar DPO..."
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
                  <TableHead>Nome</TableHead>
                  <TableHead>Empresa</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Telefone</TableHead>
                  <TableHead>Data de Nomeação</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDPOs.map((dpo) => (
                  <TableRow key={dpo.id} className="hover:bg-gray-50">
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-100 dark:bg-gray-800">
                          <UserCheck className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{dpo.name}</span>
                            {dpo.isPrimary && (
 <Badge className="text-gray-600 dark:text-gray-400 hover:bg-gray-100 text-micro px-1.5 py-0">
                                <Star className="w-3 h-3 mr-0.5" />
                                Principal
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Building2 className="w-3 h-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
                        <span style={{ color: 'var(--eleven-text-secondary)' }}>{dpo.company}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Mail className="w-3 h-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
                        <span style={{ color: 'var(--eleven-text-secondary)' }}>{dpo.email}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Phone className="w-3 h-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
                        <span style={{ color: 'var(--eleven-text-secondary)' }}>{dpo.phone}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
                        <span style={{ color: 'var(--eleven-text-secondary)' }}>
                          {new Date(dpo.since).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(dpo.status)}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>Editar</DropdownMenuItem>
                          <DropdownMenuItem>Definir como Principal</DropdownMenuItem>
                          <DropdownMenuItem>Ver histórico</DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600">Desativar</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {filteredDPOs.length === 0 && (
              <div className="text-center py-8">
                <UserCheck className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                  Nenhum DPO encontrado
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
