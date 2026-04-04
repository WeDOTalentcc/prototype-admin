"use client"

import { Button } from "@/components/ui/button"
import {
  X, Users, Save, Loader2
} from "lucide-react"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { textStyles } from "@/lib/design-tokens"
import type { CustomGoalForm } from "./use-goals-management"

interface GoalsMgmtUser {
  id: string
  name: string
  email?: string
  role?: string
  department?: string
  isActive?: boolean
  avatar?: string
}

interface GoalsCustomGoalModalProps {
  users: GoalsMgmtUser[]
  selectedUser: GoalsMgmtUser | null
  customGoalForm: CustomGoalForm
  isSaving: boolean
  setSelectedUser: (val: GoalsMgmtUser | null) => void
  setShowCustomGoal: (val: boolean) => void
  setCustomGoalForm: (val: CustomGoalForm | ((prev: CustomGoalForm) => CustomGoalForm)) => void
  handleCreateCustomGoal: () => void
}

export function GoalsCustomGoalModal({
  users,
  selectedUser,
  customGoalForm,
  isSaving,
  setSelectedUser,
  setShowCustomGoal,
  setCustomGoalForm,
  handleCreateCustomGoal,
}: GoalsCustomGoalModalProps) {
  return (
    <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50">
      <div className="bg-lia-bg-primary rounded-md p-6 w-full max-w-lg">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Nova Meta Customizada</h3>
          <Button variant="ghost" onClick={() => {
            setShowCustomGoal(false)
            setSelectedUser(null)
          }}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-1">
              Aplicar para *
            </label>
            <Select
              value={customGoalForm.userId || selectedUser?.id || ''}
              onValueChange={(value) => {
                setCustomGoalForm(prev => ({ ...prev, userId: value }))
                if (value === '__all__') {
                  setSelectedUser(null)
                } else {
                  setSelectedUser(users.find(u => u.id === value) || null)
                }
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione usuário ou todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">
                  <span className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-lia-text-primary" />
                    <span className="font-medium">Todos os Usuários</span>
                  </span>
                </SelectItem>
                <div className="border-t border-lia-border-subtle my-1" />
                {users.map((user) => (
                  <SelectItem key={user.id} value={user.id}>
                    {user.name} - {user.role}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {customGoalForm.userId === '__all__' && (
              <p className={`${textStyles.caption} mt-1`}>
                A meta será criada para todos os {users.length} usuários
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-1">
              Nome da Meta *
            </label>
            <input
              type="text"
              value={customGoalForm.name}
              onChange={(e) => setCustomGoalForm(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
              placeholder="Ex: Aumentar taxa de conversão"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-1">
              Descrição
            </label>
            <textarea
              value={customGoalForm.description}
              onChange={(e) => setCustomGoalForm(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
              rows={2}
              placeholder="Descreva a meta..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Meta *
              </label>
              <input
                type="number"
                value={customGoalForm.target}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, target: parseFloat(e.target.value) || 0 }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                min="0"
                step="0.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Unidade
              </label>
              <input
                type="text"
                value={customGoalForm.unit}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, unit: e.target.value }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
                placeholder="Ex: %, dias, contratações"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Período
              </label>
              <select
                value={customGoalForm.period}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, period: e.target.value as CustomGoalForm['period'] }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
              >
                <option value="monthly">Mensal</option>
                <option value="quarterly">Trimestral</option>
                <option value="yearly">Anual</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Categoria
              </label>
              <select
                value={customGoalForm.category}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, category: e.target.value as CustomGoalForm['category'] }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
              >
                <option value="recruitment">Recrutamento</option>
                <option value="quality">Qualidade</option>
                <option value="efficiency">Eficiência</option>
                <option value="satisfaction">Satisfação</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Data Início
              </label>
              <input
                type="date"
                value={customGoalForm.startDate}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, startDate: e.target.value }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-1">
                Data Fim
              </label>
              <input
                type="date"
                value={customGoalForm.endDate}
                onChange={(e) => setCustomGoalForm(prev => ({ ...prev, endDate: e.target.value }))}
                className="w-full px-3 py-2 border border-lia-border-default rounded-md text-sm"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => {
              setShowCustomGoal(false)
              setSelectedUser(null)
            }}>
              Cancelar
            </Button>
            <Button onClick={handleCreateCustomGoal} disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                  Salvando...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Criar Meta
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
