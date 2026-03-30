'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import {
  Edit, Save, X, Trash2, Plus, Loader2, Shield,
  RefreshCw, Globe, Users
} from "lucide-react"
import type { GlobalPolicy, PolicyType, PolicyScope } from './types'

const policyTypeLabels: Record<string, { label: string; color: string }> = {
  rate_limit: { label: 'Rate Limit', color: 'bg-gray-100 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary' },
  blacklist: { label: 'Blacklist', color: 'bg-status-error/10 text-status-error dark:bg-status-error/20 dark:text-status-error' },
  whitelist: { label: 'Whitelist', color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success' },
  content_filter: { label: 'Filtro de Conteúdo', color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple' }
}

const formatPolicyValue = (value: Record<string, unknown>, type: string): string => {
  if (type === 'rate_limit') {
    const limit = value.limit || value.max_requests || 0
    const period = value.period || value.window || 'day'
    return `${limit} / ${period}`
  }
  if (type === 'blacklist' || type === 'whitelist') {
    const items = value.items || value.domains || value.emails || []
    if (Array.isArray(items)) return items.slice(0, 3).join(', ') + (items.length > 3 ? ` +${items.length - 3} mais` : '')
    return String(items)
  }
  if (type === 'content_filter') {
    return value.enabled ? 'Ativo' : 'Inativo'
  }
  return JSON.stringify(value)
}

interface NewPolicy {
  name: string
  policy_type: string
  scope: string
  value: Record<string, unknown>
  description: string
}

interface PoliciesSectionProps {
  policies: GlobalPolicy[]
  policiesLoading: boolean
  savingPolicy: boolean
  editingPolicy: GlobalPolicy | null
  setEditingPolicy: (policy: GlobalPolicy | null) => void
  showCreatePolicyModal: boolean
  setShowCreatePolicyModal: (show: boolean) => void
  newPolicy: NewPolicy
  setNewPolicy: (policy: NewPolicy) => void
  policyTypes: PolicyType[]
  policyScopes: PolicyScope[]
  fetchPolicies: () => void
  handleCreatePolicy: () => void
  handleUpdatePolicy: (policy: GlobalPolicy, updates: GlobalPolicy) => void
  handleDeletePolicy: (id: string) => void
  handleTogglePolicyActiveApi: (policy: GlobalPolicy) => void
}

export function PoliciesSection({
  policies,
  policiesLoading,
  savingPolicy,
  editingPolicy,
  setEditingPolicy,
  showCreatePolicyModal,
  setShowCreatePolicyModal,
  newPolicy,
  setNewPolicy,
  policyTypes,
  policyScopes,
  fetchPolicies,
  handleCreatePolicy,
  handleUpdatePolicy,
  handleDeletePolicy,
  handleTogglePolicyActiveApi
}: PoliciesSectionProps) {
  const groupedPolicies = policies.reduce((acc, policy) => {
    if (!acc[policy.type]) acc[policy.type] = []
    acc[policy.type].push(policy)
    return acc
  }, {} as Record<string, GlobalPolicy[]>)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium lia-text-500 dark:text-lia-text-tertiary" >
            Políticas Globais de Comunicação ({policies.length})
          </h3>
          <p className="text-xs mt-1 lia-text-400 dark:lia-text-500" >
            Configure regras e limites para comunicações na plataforma
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchPolicies}
            disabled={policiesLoading}
          >
            <RefreshCw className={`w-4 h-4 ${policiesLoading ? 'animate-spin motion-reduce:animate-none' : ''}`} />
          </Button>
          <Button
            size="sm"
            className="bg-gray-900 dark:lia-bg-50 hover:bg-gray-800 dark:hover:bg-gray-200"
            onClick={() => setShowCreatePolicyModal(true)}
            disabled={policiesLoading}
          >
            <Plus className="w-4 h-4 mr-2" />
            Nova Política
          </Button>
        </div>
      </div>

      {policiesLoading ? (
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none lia-text-700 dark:text-lia-text-secondary" />
          <span className="ml-3 text-sm lia-text-500 dark:text-lia-text-tertiary" >
            Carregando políticas...
          </span>
        </div>
      ) : policies.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-12">
          <Shield className="w-12 h-12 mb-3 lia-text-400 dark:lia-text-500"  />
          <p className="text-sm font-medium mb-1 lia-text-500 dark:text-lia-text-tertiary" >
            Nenhuma política configurada
          </p>
          <p className="text-xs mb-4 lia-text-400 dark:lia-text-500" >
            Crie políticas para controlar rate limits, blacklists e filtros
          </p>
          <Button
            size="sm"
            className="bg-gray-900 dark:lia-bg-50 hover:bg-gray-800 dark:hover:bg-gray-200"
            onClick={() => setShowCreatePolicyModal(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Criar Política
          </Button>
        </Card>
      ) : (
        <>
          {editingPolicy && (
            <Card className="mb-4">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Editar Política</CardTitle>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setEditingPolicy(null)} disabled={savingPolicy}>
                      <X className="w-4 h-4 mr-1" /> Cancelar
                    </Button>
                    <Button 
                      size="sm" 
                      className="bg-gray-900 dark:lia-bg-50 hover:bg-gray-800 dark:hover:bg-gray-200" 
                      onClick={() => handleUpdatePolicy(editingPolicy, editingPolicy)}
                      disabled={savingPolicy}
                    >
                      {savingPolicy ? (
                        <Loader2 className="w-4 h-4 mr-1 animate-spin motion-reduce:animate-none" />
                      ) : (
                        <Save className="w-4 h-4 mr-1" />
                      )}
                      Salvar
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >Nome</label>
                    <Input
                      value={editingPolicy.name}
                      onChange={(e) => setEditingPolicy({ ...editingPolicy, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >Tipo</label>
                    <select
                      className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
                      value={editingPolicy.type}
                      onChange={(e) => setEditingPolicy({ ...editingPolicy, type: e.target.value as GlobalPolicy['type'] })}
                    >
                      <option value="rate_limit">Rate Limit</option>
                      <option value="blacklist">Blacklist</option>
                      <option value="whitelist">Whitelist</option>
                      <option value="content_filter">Filtro de Conteúdo</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >Descrição</label>
                  <Input
                    value={editingPolicy.description}
                    onChange={(e) => setEditingPolicy({ ...editingPolicy, description: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >
                    Valor {editingPolicy.type === 'rate_limit' && '(limite numérico)'}
                    {(editingPolicy.type === 'blacklist' || editingPolicy.type === 'whitelist') && '(lista separada por vírgulas)'}
                  </label>
                  {editingPolicy.type === 'rate_limit' ? (
                    <div className="grid grid-cols-2 gap-2 mt-1">
                      <Input
                        type="number"
                        placeholder="Limite"
                        value={editingPolicy.value.limit as number || ''}
                        onChange={(e) => setEditingPolicy({ 
                          ...editingPolicy, 
                          value: { ...editingPolicy.value, limit: parseInt(e.target.value) || 0 }
                        })}
                      />
                      <select
                        className="px-3 py-2 border rounded-md text-sm"
                        value={(editingPolicy.value.period as string) || 'day'}
                        onChange={(e) => setEditingPolicy({ 
                          ...editingPolicy, 
                          value: { ...editingPolicy.value, period: e.target.value }
                        })}
                      >
                        <option value="minute">Por Minuto</option>
                        <option value="hour">Por Hora</option>
                        <option value="day">Por Dia</option>
                      </select>
                    </div>
                  ) : editingPolicy.type === 'blacklist' || editingPolicy.type === 'whitelist' ? (
                    <Textarea
                      placeholder="item1, item2, item3"
                      value={Array.isArray(editingPolicy.value.items) ? (editingPolicy.value.items as string[]).join(', ') : ''}
                      onChange={(e) => setEditingPolicy({ 
                        ...editingPolicy, 
                        value: { ...editingPolicy.value, items: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }
                      })}
                      rows={3}
                    />
                  ) : (
                    <div className="flex items-center gap-2 mt-1">
                      <Switch
                        checked={!!editingPolicy.value.enabled}
                        onCheckedChange={(checked) => setEditingPolicy({ 
                          ...editingPolicy, 
                          value: { ...editingPolicy.value, enabled: checked }
                        })}
                      />
                      <span className="text-sm lia-text-500 dark:text-lia-text-tertiary" >
                        {editingPolicy.value.enabled ? 'Ativo' : 'Inativo'}
                      </span>
                    </div>
                  )}
                </div>
                <div>
                  <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >Escopo</label>
                  <select
                    className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
                    value={editingPolicy.scope}
                    onChange={(e) => setEditingPolicy({ ...editingPolicy, scope: e.target.value as 'platform' | 'company' })}
                  >
                    <option value="company">Empresa</option>
                    <option value="platform">Plataforma (Global)</option>
                  </select>
                </div>
              </CardContent>
            </Card>
          )}

          {Object.entries(groupedPolicies).map(([type, typePolicies]) => (
            <div key={type} className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge className={`text-xs ${policyTypeLabels[type]?.color || 'bg-gray-100 lia-text-600'}`}>
                  {policyTypeLabels[type]?.label || type}
                </Badge>
                <span className="text-xs lia-text-400 dark:lia-text-500" >
                  ({typePolicies.length} {typePolicies.length === 1 ? 'política' : 'políticas'})
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {typePolicies.map(policy => (
                  <Card key={policy.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Shield className={`w-4 h-4 ${policy.isActive ? 'lia-text-950' : 'lia-text-400 dark:lia-text-500'}`} />
                            <h4 className="font-medium text-sm lia-text-800 dark:text-lia-text-primary" >
                              {policy.name}
                            </h4>
                            <Badge 
                              variant="outline" 
                              className={`text-xs ${policy.scope === 'platform' ? 'bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30' : 'bg-gray-50 lia-text-600 border-lia-border-subtle'}`}
                            >
                              {policy.scope === 'platform' ? (
                                <><Globe className="w-3 h-3 mr-1" />Global</>
                              ) : (
                                <><Users className="w-3 h-3 mr-1" />Empresa</>
                              )}
                            </Badge>
                          </div>
                          <p className="text-xs mb-2 lia-text-400 dark:lia-text-500" >
                            {policy.description}
                          </p>
                          <div className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >
                            {formatPolicyValue(policy.value, policy.type)}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Button size="sm" variant="ghost" onClick={() => setEditingPolicy(policy)} title="Editar">
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            className="text-status-error hover:text-status-error"
                            onClick={() => handleDeletePolicy(policy.id)}
                            title="Excluir"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                          <Switch
                            checked={policy.isActive}
                            onCheckedChange={() => handleTogglePolicyActiveApi(policy)}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </>
      )}

      {showCreatePolicyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-lg">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Nova Política</CardTitle>
                <Button size="sm" variant="ghost" onClick={() => setShowCreatePolicyModal(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >Nome *</label>
                <Input
                  value={newPolicy.name}
                  onChange={(e) => setNewPolicy({ ...newPolicy, name: e.target.value })}
                  placeholder="Ex: Rate Limit por Empresa"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >Tipo</label>
                  <select
                    className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
                    value={newPolicy.policy_type}
                    onChange={(e) => {
                      const policyType = e.target.value
                      let defaultValue: Record<string, unknown> = { limit: 100, period: 'day' }
                      if (policyType === 'blacklist' || policyType === 'whitelist') {
                        defaultValue = { items: [] }
                      } else if (policyType === 'content_filter') {
                        defaultValue = { enabled: true }
                      }
                      setNewPolicy({ ...newPolicy, policy_type: policyType, value: defaultValue })
                    }}
                  >
                    {policyTypes.length > 0 ? (
                      policyTypes.map(pt => (
                        <option key={pt.type} value={pt.type}>{policyTypeLabels[pt.type]?.label || pt.type}</option>
                      ))
                    ) : (
                      <>
                        <option value="rate_limit">Rate Limit</option>
                        <option value="blacklist">Blacklist</option>
                        <option value="whitelist">Whitelist</option>
                        <option value="content_filter">Filtro de Conteúdo</option>
                      </>
                    )}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >Escopo</label>
                  <select
                    className="w-full mt-1 px-3 py-2 border rounded-md text-sm"
                    value={newPolicy.scope}
                    onChange={(e) => setNewPolicy({ ...newPolicy, scope: e.target.value })}
                  >
                    {policyScopes.length > 0 ? (
                      policyScopes.map(ps => (
                        <option key={ps.scope} value={ps.scope}>{ps.scope === 'platform' ? 'Plataforma (Global)' : 'Empresa'}</option>
                      ))
                    ) : (
                      <>
                        <option value="company">Empresa</option>
                        <option value="platform">Plataforma (Global)</option>
                      </>
                    )}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >
                  Valor {newPolicy.policy_type === 'rate_limit' && '(limite e período)'}
                  {(newPolicy.policy_type === 'blacklist' || newPolicy.policy_type === 'whitelist') && '(itens separados por vírgulas)'}
                </label>
                {newPolicy.policy_type === 'rate_limit' ? (
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <Input
                      type="number"
                      placeholder="Limite"
                      value={newPolicy.value.limit as number || ''}
                      onChange={(e) => setNewPolicy({ 
                        ...newPolicy, 
                        value: { ...newPolicy.value, limit: parseInt(e.target.value) || 0 }
                      })}
                    />
                    <select
                      className="px-3 py-2 border rounded-md text-sm"
                      value={(newPolicy.value.period as string) || 'day'}
                      onChange={(e) => setNewPolicy({ 
                        ...newPolicy, 
                        value: { ...newPolicy.value, period: e.target.value }
                      })}
                    >
                      <option value="minute">Por Minuto</option>
                      <option value="hour">Por Hora</option>
                      <option value="day">Por Dia</option>
                    </select>
                  </div>
                ) : newPolicy.policy_type === 'blacklist' || newPolicy.policy_type === 'whitelist' ? (
                  <Textarea
                    placeholder="spam.com, fake.net, test.org"
                    value={Array.isArray(newPolicy.value.items) ? (newPolicy.value.items as string[]).join(', ') : ''}
                    onChange={(e) => setNewPolicy({ 
                      ...newPolicy, 
                      value: { ...newPolicy.value, items: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }
                    })}
                    rows={3}
                  />
                ) : (
                  <div className="flex items-center gap-2 mt-1">
                    <Switch
                      checked={!!newPolicy.value.enabled}
                      onCheckedChange={(checked) => setNewPolicy({ 
                        ...newPolicy, 
                        value: { ...newPolicy.value, enabled: checked }
                      })}
                    />
                    <span className="text-sm lia-text-500 dark:text-lia-text-tertiary" >
                      {newPolicy.value.enabled ? 'Ativo' : 'Inativo'}
                    </span>
                  </div>
                )}
              </div>
              <div>
                <label className="text-xs font-medium lia-text-500 dark:text-lia-text-tertiary" >Descrição</label>
                <Textarea
                  value={newPolicy.description}
                  onChange={(e) => setNewPolicy({ ...newPolicy, description: e.target.value })}
                  placeholder="Descrição da política"
                  rows={2}
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setShowCreatePolicyModal(false)} disabled={savingPolicy}>
                  Cancelar
                </Button>
                <Button 
                  className="bg-gray-900 dark:lia-bg-50 hover:bg-gray-800 dark:hover:bg-gray-200" 
                  onClick={handleCreatePolicy}
                  disabled={savingPolicy || !newPolicy.name.trim()}
                >
                  {savingPolicy ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
                  ) : (
                    <Plus className="w-4 h-4 mr-2" />
                  )}
                  Criar Política
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
