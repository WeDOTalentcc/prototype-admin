"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { X, Save, User, Briefcase, Shield } from "lucide-react"
import { textStyles } from '@/lib/design-tokens'
import type { UserData } from './user-management-types'

interface UserFormProps {
  isCreating: boolean
  formData: Partial<UserData>
  setFormData: React.Dispatch<React.SetStateAction<Partial<UserData>>>
  onSave: () => void
  onCancel: () => void
}

export function UserForm({ isCreating, formData, setFormData, onSave, onCancel }: UserFormProps) {
  const inputClass = "w-full py-1.5 px-2 text-xs border border-lia-border-default dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary focus:ring-1 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg"

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className={textStyles.title}>
            {isCreating ? 'Novo Usuário' : 'Editar Usuário'}
          </h3>
          <p className={textStyles.description}>
            {isCreating ? 'Cadastre um novo recrutador na plataforma' : 'Atualize as informações do usuário'}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onCancel}>
          <X className="w-3.5 h-3.5 mr-1.5" />
          Cancelar
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h4 className={`${textStyles.title} flex items-center gap-2`}>
                <User className="w-3.5 h-3.5" />
                Dados Pessoais
              </h4>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>Nome Completo</label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className={inputClass}
                  placeholder="Ex: Ana Silva"
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>Email</label>
                <input
                  type="email"
                  value={formData.email || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  className={inputClass}
                  placeholder="ana.silva@empresa.com"
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>Telefone</label>
                <input
                  type="tel"
                  value={formData.phone || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  className={inputClass}
                  placeholder="+55 11 99999-9999"
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>WhatsApp</label>
                <input
                  type="tel"
                  value={formData.whatsapp || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, whatsapp: e.target.value }))}
                  className={inputClass}
                  placeholder="+55 11 99999-9999"
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>Localização</label>
                <input
                  type="text"
                  value={formData.location || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                  className={inputClass}
                  placeholder="São Paulo, SP"
                />
              </div>
            </div>

            <div className="space-y-3">
              <h4 className={`${textStyles.title} flex items-center gap-2`}>
                <Briefcase className="w-3.5 h-3.5" />
                Dados Profissionais
              </h4>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>Cargo/Função</label>
                <input
                  type="text"
                  value={formData.role || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                  className={inputClass}
                  placeholder="Ex: Recrutadora Sênior"
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>Departamento</label>
                <select
                  value={formData.department || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                  className={inputClass}
                >
                  <option value="">Selecione...</option>
                  <option value="Talent Acquisition">Talent Acquisition</option>
                  <option value="RH">Recursos Humanos</option>
                  <option value="Operações">Operações</option>
                  <option value="Tecnologia">Tecnologia</option>
                </select>
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>Posição</label>
                <input
                  type="text"
                  value={formData.position || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, position: e.target.value }))}
                  className={inputClass}
                  placeholder="Senior Recruiter"
                />
              </div>

              <div>
                <label className={textStyles.label + " block mb-1.5"}>Status</label>
                <select
                  value={formData.status || 'ativo'}
                  onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value as typeof prev.status }))}
                  className={inputClass}
                >
                  <option value="ativo">Ativo</option>
                  <option value="inativo">Inativo</option>
                  <option value="pendente">Pendente</option>
                </select>
              </div>

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.isManager || false}
                    onChange={(e) => setFormData(prev => ({ ...prev, isManager: e.target.checked }))}
                    className="w-3.5 h-3.5 rounded-md border-lia-border-default"
                  />
                  <span className={textStyles.label}>É Gestor</span>
                </label>
              </div>
            </div>
          </div>

          <div className="mt-4">
            <h4 className={`${textStyles.title} flex items-center gap-2 mb-3`}>
              <Shield className="w-3.5 h-3.5" />
              Permissões
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                { id: 'recruitment', label: 'Recrutamento' },
                { id: 'candidates', label: 'Candidatos' },
                { id: 'interviews', label: 'Entrevistas' },
                { id: 'reports', label: 'Relatórios' },
                { id: 'settings', label: 'Configurações' },
                { id: 'users', label: 'Usuários' },
                { id: 'admin', label: 'Administrador' },
                { id: 'analytics', label: 'Analytics' }
              ].map((permission) => (
                <label key={permission.id} className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={(formData.permissions || []).includes(permission.id)}
                    onChange={(e) => {
                      const permissions = formData.permissions || []
                      if (e.target.checked) {
                        setFormData(prev => ({ ...prev, permissions: [...permissions, permission.id] }))
                      } else {
                        setFormData(prev => ({ ...prev, permissions: permissions.filter(p => p !== permission.id) }))
                      }
                    }}
                    className="w-3.5 h-3.5 rounded-md border-lia-border-default"
                  />
                  <span className={textStyles.label}>{permission.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
            <Button variant="outline" size="sm" onClick={onCancel}>
              Cancelar
            </Button>
            <Button onClick={onSave} size="sm" className="gap-1.5 hover:bg-lia-interactive-hover transition-colors cursor-pointer">
              <Save className="w-3.5 h-3.5" />
              {isCreating ? 'Criar Usuário' : 'Salvar Alterações'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
