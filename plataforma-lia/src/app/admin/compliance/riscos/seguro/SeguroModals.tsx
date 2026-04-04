"use client"

import React from "react"
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Loader2 } from "lucide-react"
import {
  InsurancePolicy,
  CreatePolicyInput,
  CreateCoverageInput,
  CreateClaimInput,
} from "@/services/admin/insurance-service"
import { BCB_COVERAGE_TYPES } from "./seguro-shared"

interface PolicyModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editingPolicy: InsurancePolicy | null
  form: CreatePolicyInput
  setForm: React.Dispatch<React.SetStateAction<CreatePolicyInput>>
  onSubmit: () => void
  submitting: boolean
}

export function PolicyModal({ open, onOpenChange, editingPolicy, form, setForm, onSubmit, submitting }: PolicyModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{editingPolicy ? 'Editar Apólice' : 'Nova Apólice'}</DialogTitle>
          <DialogDescription>
            {editingPolicy ? 'Atualize os dados da apólice de seguro cibernético.' : 'Cadastre uma nova apólice de seguro cibernético.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Número da Apólice</Label>
              <Input 
                value={form.policyNumber}
                onChange={(e) => setForm(prev => ({ ...prev, policyNumber: e.target.value }))}
                placeholder="CYB-2024-123456"
              />
            </div>
            <div className="space-y-2">
              <Label>Seguradora</Label>
              <Input 
                value={form.insurer}
                onChange={(e) => setForm(prev => ({ ...prev, insurer: e.target.value }))}
                placeholder="AIG Brasil"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Valor de Cobertura ({CURRENCY_SYMBOL})</Label>
              <Input 
                type="number"
                value={form.coverage || ''}
                onChange={(e) => setForm(prev => ({ ...prev, coverage: parseFloat(e.target.value) || 0 }))}
                placeholder="5000000"
              />
            </div>
            <div className="space-y-2">
              <Label>Franquia ({CURRENCY_SYMBOL})</Label>
              <Input 
                type="number"
                value={form.deductible || ''}
                onChange={(e) => setForm(prev => ({ ...prev, deductible: parseFloat(e.target.value) || 0 }))}
                placeholder="50000"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Data de Início</Label>
              <Input 
                type="date"
                value={form.startDate}
                onChange={(e) => setForm(prev => ({ ...prev, startDate: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Data de Término</Label>
              <Input 
                type="date"
                value={form.endDate}
                onChange={(e) => setForm(prev => ({ ...prev, endDate: e.target.value }))}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Observações</Label>
            <Textarea 
              value={form.notes}
              onChange={(e) => setForm(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Observações adicionais..."
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancelar</Button>
          <Button onClick={onSubmit} disabled={submitting}>
            {submitting && <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />}
            {editingPolicy ? 'Salvar' : 'Criar Apólice'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface CoverageModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  form: CreateCoverageInput
  setForm: React.Dispatch<React.SetStateAction<CreateCoverageInput>>
  onSubmit: () => void
  submitting: boolean
}

export function CoverageModal({ open, onOpenChange, form, setForm, onSubmit, submitting }: CoverageModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Adicionar Cobertura</DialogTitle>
          <DialogDescription>
            Adicione uma nova cobertura à apólice ativa.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Tipo de Cobertura</Label>
            <Select 
              value={form.coverageType}
              onValueChange={(value) => {
                const selected = BCB_COVERAGE_TYPES.find(ct => ct.type === value)
                setForm(prev => ({
                  ...prev,
                  coverageType: value,
                  name: selected?.name || '',
                  description: selected?.description || '',
                  bcbArticle: selected?.article || '',
                }))
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione o tipo de cobertura" />
              </SelectTrigger>
              <SelectContent>
                {BCB_COVERAGE_TYPES.map((ct) => (
                  <SelectItem key={ct.type} value={ct.type}>
                    {ct.name} ({ct.article})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Nome da Cobertura</Label>
            <Input 
              value={form.name}
              onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Violação de Dados"
            />
          </div>
          <div className="space-y-2">
            <Label>Descrição</Label>
            <Textarea 
              value={form.description}
              onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Descrição da cobertura..."
              rows={3}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Limite de Cobertura ({CURRENCY_SYMBOL})</Label>
              <Input 
                type="number"
                value={form.coverageLimit || ''}
                onChange={(e) => setForm(prev => ({ ...prev, coverageLimit: parseFloat(e.target.value) || 0 }))}
                placeholder="1000000"
              />
            </div>
            <div className="space-y-2">
              <Label>Artigo BCB</Label>
              <Input 
                value={form.bcbArticle}
                onChange={(e) => setForm(prev => ({ ...prev, bcbArticle: e.target.value }))}
                placeholder="Art. 3º, I"
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancelar</Button>
          <Button onClick={onSubmit} disabled={submitting}>
            {submitting && <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />}
            Adicionar Cobertura
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface ClaimModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  form: CreateClaimInput
  setForm: React.Dispatch<React.SetStateAction<CreateClaimInput>>
  onSubmit: () => void
  submitting: boolean
}

export function ClaimModal({ open, onOpenChange, form, setForm, onSubmit, submitting }: ClaimModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Registrar Sinistro</DialogTitle>
          <DialogDescription>
            Registre um novo sinistro para a apólice ativa.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Data do Incidente</Label>
              <Input 
                type="date"
                value={form.incidentDate}
                onChange={(e) => setForm(prev => ({ ...prev, incidentDate: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Valor Estimado ({CURRENCY_SYMBOL})</Label>
              <Input 
                type="number"
                value={form.claimAmount || ''}
                onChange={(e) => setForm(prev => ({ ...prev, claimAmount: parseFloat(e.target.value) || 0 }))}
                placeholder="100000"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Descrição do Incidente</Label>
            <Textarea 
              value={form.description}
              onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Descreva o incidente de segurança..."
              rows={4}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancelar</Button>
          <Button onClick={onSubmit} disabled={submitting}>
            {submitting && <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />}
            Registrar Sinistro
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
