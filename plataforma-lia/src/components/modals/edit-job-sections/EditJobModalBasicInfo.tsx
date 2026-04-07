"use client"

import React from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Briefcase,
  Users,
  Calendar,
  FileText,
  AlertTriangle,
} from "lucide-react"
import {
  WORK_MODELS,
  CONTRACT_TYPES,
  SENIORITY_LEVELS,
  inputStyle,
  selectTriggerStyle,
} from '../edit-job-modal.constants'
import type { Job } from '../edit-job/edit-job.types'

interface Department {
  id: string
  name: string
}

interface EditJobModalBasicInfoProps {
  formData: Partial<Job>
  updateField: (field: keyof Job, value: unknown) => void
  companyDepartments: Department[]
}

export function EditJobModalBasicInfo({
  formData,
  updateField,
  companyDepartments,
}: EditJobModalBasicInfoProps) {
  return (
    <>
      <section data-testid="edit-job-basic-info-section">
        <div className="flex items-center gap-2 mb-3">
          <Briefcase className="w-4 h-4 text-lia-text-secondary" />
          <h3 className="text-base-ui font-semibold text-lia-text-primary">Informações Básicas</h3>
        </div>
        
        <div className="space-y-4">
          <div>
            <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Título da Vaga</Label>
            <Input
              value={formData.title || ''}
              onChange={(e) => updateField('title', e.target.value)}
              className={inputStyle}
              placeholder="Ex: Desenvolvedor Full Stack"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Departamento</Label>
              {companyDepartments.length > 0 ? (
                <Select 
                  value={formData.department || ''} 
                  onValueChange={(v) => updateField('department', v)}
                >
                  <SelectTrigger className={selectTriggerStyle}>
                    <SelectValue placeholder="Selecione um departamento" />
                  </SelectTrigger>
                  <SelectContent>
                    {companyDepartments.map(dept => (
                      <SelectItem key={dept.id} value={dept.name} className="text-sm">
                        {dept.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  value={formData.department || ''}
                  onChange={(e) => updateField('department', e.target.value)}
                  className={inputStyle}
                  placeholder="Ex: Tecnologia"
                />
              )}
            </div>
            <div>
              <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Localização</Label>
              <Input
                value={formData.location || ''}
                onChange={(e) => updateField('location', e.target.value)}
                className={inputStyle}
                placeholder="Ex: São Paulo, SP"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Modelo de Trabalho</Label>
              <Select value={formData.workModel} onValueChange={(v) => updateField('workModel', v as Job['workModel'])}>
                <SelectTrigger className={selectTriggerStyle}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {WORK_MODELS.map(m => (
                    <SelectItem key={m.value} value={m.value} className="text-sm">{m.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Tipo de Contrato</Label>
              <Select value={formData.type} onValueChange={(v) => updateField('type', v)}>
                <SelectTrigger className={selectTriggerStyle}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CONTRACT_TYPES.map(t => (
                    <SelectItem key={t.value} value={t.value} className="text-sm">{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Senioridade</Label>
              <Select value={formData.level} onValueChange={(v) => updateField('level', v)}>
                <SelectTrigger className={selectTriggerStyle}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SENIORITY_LEVELS.map(l => (
                    <SelectItem key={l.value} value={l.value} className="text-sm">{l.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-lia-border-subtle" />

      <section>
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-lia-text-secondary" />
          <h3 className="text-base-ui font-semibold text-lia-text-primary">Pessoas Responsáveis</h3>
        </div>
        
        <div className="space-y-4">
          <div className="p-3 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
            <p className="text-xs font-medium uppercase text-lia-text-secondary mb-2">Recrutador(a)</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Nome</Label>
                <Input
                  value={formData.recruiter || ''}
                  onChange={(e) => updateField('recruiter', e.target.value)}
                  className={`${inputStyle} bg-lia-bg-secondary`}
                  placeholder="Nome do recrutador"
                />
              </div>
              <div>
                <Label className="text-xs font-medium text-lia-text-primary mb-1 block">E-mail</Label>
                <Input
                  value={formData.recruiterEmail || ''}
                  onChange={(e) => updateField('recruiterEmail', e.target.value)}
                  className={`${inputStyle} bg-lia-bg-secondary`}
                  placeholder="email@empresa.com"
                />
              </div>
            </div>
          </div>

          <div className="p-3 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
            <p className="text-xs font-medium uppercase text-lia-text-secondary mb-2">Gestor(a) Solicitante</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Nome</Label>
                <Input
                  value={formData.manager || ''}
                  onChange={(e) => updateField('manager', e.target.value)}
                  className={`${inputStyle} bg-lia-bg-secondary`}
                  placeholder="Nome do gestor"
                />
              </div>
              <div>
                <Label className="text-xs font-medium text-lia-text-primary mb-1 block">E-mail</Label>
                <Input
                  value={formData.managerEmail || ''}
                  onChange={(e) => updateField('managerEmail', e.target.value)}
                  className={`${inputStyle} bg-lia-bg-secondary`}
                  placeholder="email@empresa.com"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-lia-border-subtle" />

      <section>
        <div className="flex items-center gap-2 mb-3">
          <Calendar className="w-4 h-4 text-lia-text-secondary" />
          <h3 className="text-base-ui font-semibold text-lia-text-primary">Timeline do Processo</h3>
        </div>
        
        <div className="relative pl-4 border-l-2 border-lia-border-default space-y-4">
          <div className="relative">
            <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-status-success border-2 border-white" />
            <div className="ml-4">
              <Label className="text-xs font-medium text-lia-text-primary mb-1 block flex items-center gap-1.5">
                <span className="text-status-success font-medium">1.</span> Data de Abertura
              </Label>
              <Input
                type="date"
                value={formData.openDate || ''}
                onChange={(e) => updateField('openDate', e.target.value)}
                className={`${inputStyle} w-48`}
              />
            </div>
          </div>
          
          <div className="relative">
            <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-wedo-cyan border-2 border-white" />
            <div className="ml-4">
              <Label className="text-xs font-medium text-lia-text-primary mb-1 block flex items-center gap-1.5">
                <span className="text-wedo-cyan-dark font-medium">2.</span> Prazo Screening
                <span className="text-micro text-lia-text-disabled">(triagem inicial)</span>
              </Label>
              <Input
                type="date"
                value={formData.deadlineScreening || ''}
                onChange={(e) => updateField('deadlineScreening', e.target.value)}
                className={`${inputStyle} w-48`}
              />
            </div>
          </div>
          
          <div className="relative">
            <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-wedo-purple border-2 border-white" />
            <div className="ml-4">
              <Label className="text-xs font-medium text-lia-text-primary mb-1 block flex items-center gap-1.5">
                <span className="text-wedo-purple font-medium">3.</span> Prazo Shortlist
                <span className="text-micro text-lia-text-disabled">(lista curta)</span>
              </Label>
              <Input
                type="date"
                value={formData.deadlineShortlist || ''}
                onChange={(e) => updateField('deadlineShortlist', e.target.value)}
                className={`${inputStyle} w-48`}
              />
            </div>
          </div>
          
          <div className="relative">
            <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-wedo-orange border-2 border-white" />
            <div className="ml-4">
              <Label className="text-xs font-medium text-lia-text-primary mb-1 block flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-wedo-orange" />
                <span className="text-wedo-orange font-medium">4.</span> Prazo Final
              </Label>
              <Input
                type="date"
                value={formData.deadline || ''}
                onChange={(e) => updateField('deadline', e.target.value)}
                className={`${inputStyle} w-48`}
              />
            </div>
          </div>
        </div>
      </section>

      <hr className="border-lia-border-subtle" />

      <section>
        <div className="flex items-center gap-2 mb-4">
          <FileText className="w-4 h-4 text-lia-text-secondary" />
          <h3 className="text-base-ui font-semibold text-lia-text-primary">Descrição</h3>
        </div>
        
        <div className="space-y-4">
          <div>
            <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Descrição da Vaga</Label>
            <Textarea
              value={formData.description || ''}
              onChange={(e) => updateField('description', e.target.value)}
              className="min-h-[100px] text-sm resize-none bg-lia-bg-secondary border-lia-border-subtle focus:border-lia-border-medium focus:ring-1 focus:ring-lia-btn-primary-bg/20"
              placeholder="Descreva as responsabilidades, objetivos e contexto da vaga..."
            />
          </div>
        </div>
      </section>
    </>
  )
}
