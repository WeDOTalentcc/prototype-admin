"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"

export interface CreateClientDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

interface NewClientForm {
  name: string
  trading_name: string
  cnpj: string
  email: string
  phone: string
  plan: string
  user_limit: number
  account_manager: string
}

const initialFormState: NewClientForm = {
  name: '',
  trading_name: '',
  cnpj: '',
  email: '',
  phone: '',
  plan: 'starter',
  user_limit: 10,
  account_manager: '',
}

export function CreateClientDialog({ open, onOpenChange, onSuccess }: CreateClientDialogProps) {
  const [creating, setCreating] = useState(false)
  const [newClient, setNewClient] = useState<NewClientForm>(initialFormState)

  const handleCreateClient = async () => {
    if (!newClient.name || !newClient.cnpj || !newClient.email) {
      toast.error('Preencha os campos obrigatórios: Nome, CNPJ e Email')
      return
    }
    
    setCreating(true)
    try {
      const response = await fetch('/api/backend-proxy/clients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newClient.name,
          trade_name: newClient.trading_name || null,
          cnpj: newClient.cnpj,
          primary_email: newClient.email,
          primary_phone: newClient.phone || null,
          plan_id: newClient.plan,
          user_limit: newClient.user_limit,
          account_manager_id: newClient.account_manager || null,
          status: 'pending_setup',
        }),
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || 'Erro ao criar cliente')
      }
      
      toast.success('Cliente criado com sucesso!')
      onOpenChange(false)
      setNewClient(initialFormState)
      onSuccess?.()
    } catch (err) {
      console.error('Error creating client:', err)
      toast.error(err instanceof Error ? err.message : 'Erro ao criar cliente')
    } finally {
      setCreating(false)
    }
  }

  const handleClose = () => {
    onOpenChange(false)
    setNewClient(initialFormState)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Novo Cliente</DialogTitle>
          <DialogDescription>
            Preencha as informações para cadastrar um novo cliente na plataforma.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Razão Social *</Label>
            <Input
              id="name"
              value={newClient.name}
              onChange={(e) => setNewClient({ ...newClient, name: e.target.value })}
              placeholder="Nome da empresa"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="trading_name">Nome Fantasia</Label>
            <Input
              id="trading_name"
              value={newClient.trading_name}
              onChange={(e) => setNewClient({ ...newClient, trading_name: e.target.value })}
              placeholder="Nome fantasia"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="cnpj">CNPJ *</Label>
              <Input
                id="cnpj"
                value={newClient.cnpj}
                onChange={(e) => setNewClient({ ...newClient, cnpj: e.target.value })}
                placeholder="00.000.000/0000-00"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="phone">Telefone</Label>
              <Input
                id="phone"
                value={newClient.phone}
                onChange={(e) => setNewClient({ ...newClient, phone: e.target.value })}
                placeholder="(00) 00000-0000"
              />
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">Email *</Label>
            <Input
              id="email"
              type="email"
              value={newClient.email}
              onChange={(e) => setNewClient({ ...newClient, email: e.target.value })}
              placeholder="contato@empresa.com"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="plan">Plano</Label>
              <Select 
                value={newClient.plan} 
                onValueChange={(v) => setNewClient({ ...newClient, plan: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o plano" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="starter">Starter</SelectItem>
                  <SelectItem value="professional">Professional</SelectItem>
                  <SelectItem value="enterprise">Enterprise</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="user_limit">Limite de Usuários</Label>
              <Input
                id="user_limit"
                type="number"
                min={1}
                value={newClient.user_limit}
                onChange={(e) => setNewClient({ ...newClient, user_limit: parseInt(e.target.value) || 10 })}
              />
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="account_manager">Account Manager</Label>
            <Input
              id="account_manager"
              value={newClient.account_manager}
              onChange={(e) => setNewClient({ ...newClient, account_manager: e.target.value })}
              placeholder="Nome do responsável"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancelar
          </Button>
          <Button 
            onClick={handleCreateClient}
            disabled={creating}
            className="bg-gray-900 dark:bg-gray-50 hover:bg-wedo-cyan-dark text-white"
          >
            {creating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Criando...
              </>
            ) : (
              'Criar Cliente'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
