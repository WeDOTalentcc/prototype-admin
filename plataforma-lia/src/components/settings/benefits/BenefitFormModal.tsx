"use client"

import React from "react"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DraggableDialogContent,
} from "@/components/ui/dialog"
import {
  DollarSign,
  Percent,
  Info,
  Loader2,
  Stethoscope,
  Utensils,
  Car,
  GraduationCap,
  Wallet,
  Home,
  Baby,
  Shield,
} from "lucide-react"

const BENEFIT_CATEGORIES = [
  { id: "health", name: "Saúde & Bem-estar", icon: Stethoscope, color: "text-status-error" },
  { id: "food", name: "Alimentação", icon: Utensils, color: "text-wedo-orange" },
  { id: "transport", name: "Transporte", icon: Car, color: "lia-text-700 dark:text-lia-text-secondary" },
  { id: "education", name: "Educação & Desenvolvimento", icon: GraduationCap, color: "text-wedo-purple" },
  { id: "financial", name: "Financeiro", icon: Wallet, color: "text-status-success" },
  { id: "quality_life", name: "Qualidade de Vida", icon: Home, color: "lia-text-600 dark:text-lia-text-tertiary" },
  { id: "family", name: "Família", icon: Baby, color: "text-wedo-magenta" },
  { id: "security", name: "Segurança", icon: Shield, color: "lia-text-800 dark:text-lia-text-primary" },
]

const VALUE_TYPES = [
  { id: "monetary", name: "Valor Monetário", icon: DollarSign, description: "Valor fixo em R$" },
  { id: "percentage", name: "Percentual", icon: Percent, description: "Porcentagem (ex: 5% contribuição)" },
  { id: "informative", name: "Informativo", icon: Info, description: "Apenas descrição, sem valor" },
]

const SENIORITY_LEVELS = [
  { id: "all", name: "Todos os Níveis" },
  { id: "junior", name: "Júnior" },
  { id: "pleno", name: "Pleno" },
  { id: "senior", name: "Sênior" },
  { id: "coordinator", name: "Coordenação+" },
  { id: "manager", name: "Gerência+" },
  { id: "director", name: "Diretoria" },
  { id: "c-level", name: "C-Level" },
]

const WAITING_PERIODS = [
  { id: 0, name: "Imediato" },
  { id: 30, name: "30 dias" },
  { id: 60, name: "60 dias" },
  { id: 90, name: "90 dias" },
  { id: 180, name: "6 meses" },
  { id: 365, name: "1 ano" },
]

interface Benefit {
  id?: string
  name: string
  description: string
  category: string
  value_type: string
  value?: number
  percentage_value?: number
  value_details?: string
  seniority_levels: string[]
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean
  provider?: string
}

interface BenefitFormModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editingBenefit: Benefit | null
  setEditingBenefit: (b: Benefit | null) => void
  isSaving: boolean
  onSave: (benefit: Benefit) => void
}

export function BenefitFormModal({
  open,
  onOpenChange,
  editingBenefit,
  setEditingBenefit,
  isSaving,
  onSave,
}: BenefitFormModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DraggableDialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            {editingBenefit?.id ? 'Editar Benefício' : 'Novo Benefício'}
          </DialogTitle>
          <DialogDescription className={textStyles.description}>
            Preencha os dados do benefício abaixo
          </DialogDescription>
        </DialogHeader>

        {editingBenefit && (
          <div className="space-y-3 py-1.5">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <Label htmlFor="name" className={textStyles.label}>Nome do Benefício *</Label>
                <Input
                  id="name"
                  value={editingBenefit.name}
                  onChange={(e) => setEditingBenefit({ ...editingBenefit, name: e.target.value })}
                  placeholder="Ex: Plano de Saúde Bradesco"
                  className="mt-1 rounded-full text-xs py-1.5 px-2"
                />
              </div>

              <div className="col-span-2">
                <Label htmlFor="description" className={textStyles.label}>Descrição</Label>
                <Textarea
                  id="description"
                  value={editingBenefit.description}
                  onChange={(e) => setEditingBenefit({ ...editingBenefit, description: e.target.value })}
                  placeholder="Descreva os detalhes do benefício..."
                  className="mt-1 rounded-full text-xs py-1.5 px-2"
                  rows={2}
                />
              </div>

              <div>
                <Label className={textStyles.label}>Categoria *</Label>
                <Select
                  value={editingBenefit.category}
                  onValueChange={(value) => setEditingBenefit({ ...editingBenefit, category: value })}
                >
                  <SelectTrigger className="mt-1 rounded-md text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BENEFIT_CATEGORIES.map((cat) => {
                      const Icon = cat.icon
                      return (
                        <SelectItem key={cat.id} value={cat.id} className="text-xs">
                          <div className="flex items-center gap-2">
                            <Icon className={`w-3.5 h-3.5 ${cat.color}`} />
                            <span>{cat.name}</span>
                          </div>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className={textStyles.label}>Fornecedor/Operadora</Label>
                <Input
                  value={editingBenefit.provider || ''}
                  onChange={(e) => setEditingBenefit({ ...editingBenefit, provider: e.target.value })}
                  placeholder="Ex: Bradesco Saúde"
                  className="mt-1 rounded-full text-xs py-1.5 px-2"
                />
              </div>

              <div>
                <Label className={textStyles.label}>Tipo de Valor</Label>
                <Select
                  value={editingBenefit.value_type}
                  onValueChange={(value) => setEditingBenefit({ ...editingBenefit, value_type: value })}
                >
                  <SelectTrigger className="mt-1 rounded-md text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {VALUE_TYPES.map((type) => {
                      const Icon = type.icon
                      return (
                        <SelectItem key={type.id} value={type.id} className="text-xs">
                          <div className="flex items-center gap-2">
                            <Icon className="w-3.5 h-3.5" />
                            <span>{type.name}</span>
                          </div>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>

              {editingBenefit.value_type === 'monetary' && (
                <div>
                  <Label className={textStyles.label}>Valor (R$)</Label>
                  <Input
                    type="number"
                    value={editingBenefit.value || ''}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, value: parseFloat(e.target.value) || undefined })}
                    placeholder="0,00"
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>
              )}

              {editingBenefit.value_type === 'percentage' && (
                <div>
                  <Label className={textStyles.label}>Percentual (%)</Label>
                  <Input
                    type="number"
                    value={editingBenefit.percentage_value || ''}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, percentage_value: parseFloat(e.target.value) || undefined })}
                    placeholder="0"
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>
              )}

              {editingBenefit.value_type === 'informative' && (
                <div className="col-span-2">
                  <Label className={textStyles.label}>Detalhes do Valor</Label>
                  <Input
                    value={editingBenefit.value_details || ''}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, value_details: e.target.value })}
                    placeholder="Ex: Conforme política interna"
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>
              )}

              <div>
                <Label className={textStyles.label}>Elegibilidade</Label>
                <Select
                  value={editingBenefit.seniority_levels[0] || 'all'}
                  onValueChange={(value) => setEditingBenefit({ ...editingBenefit, seniority_levels: [value] })}
                >
                  <SelectTrigger className="mt-1 rounded-md text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SENIORITY_LEVELS.map((level) => (
                      <SelectItem key={level.id} value={level.id} className="text-xs">
                        {level.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className={textStyles.label}>Período de Carência</Label>
                <Select
                  value={String(editingBenefit.waiting_period_days)}
                  onValueChange={(value) => setEditingBenefit({ ...editingBenefit, waiting_period_days: parseInt(value) })}
                >
                  <SelectTrigger className="mt-1 rounded-md text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {WAITING_PERIODS.map((period) => (
                      <SelectItem key={period.id} value={String(period.id)} className="text-xs">
                        {period.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="border-t border-lia-border-subtle dark:lia-border-800 pt-3 space-y-2">
              <h4 className={`${textStyles.labelSmall} uppercase tracking-wider`}>
                Configurações
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center justify-between p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary">
                  <div>
                    <Label className={textStyles.label}>Ativo</Label>
                    <p className={textStyles.caption}>Disponível para colaboradores</p>
                  </div>
                  <Switch
                    checked={editingBenefit.is_active}
                    onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_active: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary">
                  <div>
                    <Label className={textStyles.label}>Destaque</Label>
                    <p className={textStyles.caption}>Exibir com destaque</p>
                  </div>
                  <Switch
                    checked={editingBenefit.is_highlighted}
                    onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_highlighted: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary">
                  <div>
                    <Label className={textStyles.label}>Obrigatório</Label>
                    <p className={textStyles.caption}>Adesão obrigatória</p>
                  </div>
                  <Switch
                    checked={editingBenefit.is_mandatory}
                    onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_mandatory: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary">
                  <div>
                    <Label className={textStyles.label}>Desconto em Folha</Label>
                    <p className={textStyles.caption}>Valor descontado do salário</p>
                  </div>
                  <Switch
                    checked={editingBenefit.is_discount}
                    onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_discount: checked })}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              onOpenChange(false)
              setEditingBenefit(null)
            }}
            className="rounded-md text-xs"
          >
            Cancelar
          </Button>
          <Button
            onClick={() => editingBenefit && onSave(editingBenefit)}
            disabled={isSaving || !editingBenefit?.name}
            className="rounded-md text-xs bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
                Salvando...
              </>
            ) : (
              editingBenefit?.id ? 'Salvar Alterações' : 'Criar Benefício'
            )}
          </Button>
        </DialogFooter>
      </DraggableDialogContent>
    </Dialog>
  )
}
