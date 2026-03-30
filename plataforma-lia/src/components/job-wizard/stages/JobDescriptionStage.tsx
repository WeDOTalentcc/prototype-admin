'use client'

import React from 'react'
import { MapPin } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWizardContext } from '../WizardContext'
import { FieldOriginBadge } from '@/components/job-creation/field-origin-badge'

const DEPARTMENT_OPTIONS = [
  'Engenharia',
  'Tecnologia/TI',
  'Produto',
  'Design',
  'Dados/BI',
  'Marketing',
  'Vendas',
  'Comercial',
  'RH',
  'Financeiro',
  'Operações',
  'Jurídico',
  'Administrativo',
  'Qualidade',
  'Logística',
  'Compras',
  'Suporte',
  'Atendimento ao Cliente',
  'Supply Chain',
  'P&D (Pesquisa e Desenvolvimento)',
  'Infraestrutura'
]

const WORK_MODELS = ['Presencial', 'Híbrido', 'Remoto']
const HYBRID_DAYS = [1, 2, 3, 4]

export function JobDescriptionStage() {
  const {
    basicInfoFields,
    setBasicInfoFields,
    fieldOrigins,
    setFieldOrigins,
    jobConfig,
    setJobConfig,
    companyConfig
  } = useWizardContext()

  const handleFieldChange = (field: keyof typeof basicInfoFields, value: string) => {
    setBasicInfoFields(prev => ({ ...prev, [field]: value }))
    // Mark as manually edited
    const originKey = field === 'cargo' ? 'job_title' : 
                      field === 'localidade' ? 'location' : 
                      field === 'modeloTrabalho' ? 'work_model' : field
    setFieldOrigins(prev => ({ ...prev, [originKey]: { source: 'manual', confidence: 1 } }))
  }

  const employmentTypes = companyConfig?.employmentTypes && companyConfig.employmentTypes.length > 0 
    ? companyConfig.employmentTypes 
    : ['CLT', 'PJ']

  return (
    <div className="space-y-2.5">
      {/* Cargo */}
      <div>
        <label className="flex items-center gap-2 text-micro font-medium lia-text-secondary mb-1">
          Cargo *
          {fieldOrigins['job_title'] && (
            <FieldOriginBadge 
              origin={fieldOrigins['job_title'].source as any} 
              confidence={fieldOrigins['job_title'].confidence}
              size="sm"
            />
          )}
        </label>
        <input
          type="text"
          value={basicInfoFields.cargo}
          onChange={(e) => handleFieldChange('cargo', e.target.value)}
          placeholder="Ex: Desenvolvedor Python Sr"
          className="w-full px-3 py-1.5 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
         
          aria-label="Título do cargo"
          aria-required="true"
        />
      </div>

      {/* Área */}
      <div>
        <label className="flex items-center gap-2 text-micro font-medium lia-text-secondary mb-1">
          Área/Departamento *
          {fieldOrigins['department'] && (
            <FieldOriginBadge 
              origin={fieldOrigins['department'].source as any} 
              confidence={fieldOrigins['department'].confidence}
              size="sm"
            />
          )}
        </label>
        <select
          value={basicInfoFields.area}
          onChange={(e) => handleFieldChange('area', e.target.value)}
          className="w-full px-3 py-1.5 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors bg-lia-bg-primary"
         
          aria-label="Área ou departamento"
          aria-required="true"
        >
          <option value="">Selecione...</option>
          {DEPARTMENT_OPTIONS.map(dept => (
            <option key={dept} value={dept}>{dept}</option>
          ))}
        </select>
      </div>

      {/* Gestor */}
      <div>
        <label className="block text-micro font-medium lia-text-secondary mb-1">
          Gestor Responsável
        </label>
        <input
          type="text"
          value={basicInfoFields.gestor}
          onChange={(e) => setBasicInfoFields(prev => ({ ...prev, gestor: e.target.value }))}
          placeholder="Ex: João Silva"
          className="w-full px-3 py-1.5 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
         
          aria-label="Nome do gestor responsável"
        />
      </div>

      {/* Localidade */}
      <div>
        <label className="flex items-center gap-2 text-micro font-medium lia-text-secondary mb-1">
          Localidade
          {fieldOrigins['location'] && (
            <FieldOriginBadge 
              origin={fieldOrigins['location'].source as any} 
              confidence={fieldOrigins['location'].confidence}
              size="sm"
            />
          )}
        </label>
        <div className="relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 lia-text-secondary" />
          <input
            type="text"
            value={basicInfoFields.localidade}
            onChange={(e) => handleFieldChange('localidade', e.target.value)}
            placeholder="Ex: São Paulo, SP"
            className="w-full pl-9 pr-3 py-1.5 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
           
            aria-label="Localidade ou cidade"
          />
        </div>
      </div>

      {/* Modelo de Trabalho */}
      <div>
        <label className="flex items-center gap-2 text-micro font-medium lia-text-secondary mb-1">
          Modelo de Trabalho
          {fieldOrigins['work_model'] && (
            <FieldOriginBadge 
              origin={fieldOrigins['work_model'].source as any} 
              confidence={fieldOrigins['work_model'].confidence}
              size="sm"
            />
          )}
        </label>
        <div className="flex gap-2">
          {WORK_MODELS.map((modelo) => (
            <button
              key={modelo}
              onClick={() => handleFieldChange('modeloTrabalho', modelo)}
              className={cn(
 "flex-1 py-1.5 px-2 rounded-md text-xs font-medium transition-colors",
                basicInfoFields.modeloTrabalho === modelo
                  ? "bg-gray-900 text-white"
                  : "border border-lia-border-subtle lia-text-secondary hover:border-gray-900 dark:hover:border-gray-50"
              )}
             
            >
              {modelo}
            </button>
          ))}
        </div>
      </div>

      {/* Dias Híbridos - só aparece se modelo for híbrido */}
      {basicInfoFields.modeloTrabalho === 'Híbrido' && (
        <div>
          <label className="block text-micro font-medium lia-text-secondary mb-1">
            Dias Presenciais por Semana
          </label>
          <div className="flex gap-1.5">
            {HYBRID_DAYS.map((dias) => (
              <button
                key={dias}
                onClick={() => setJobConfig(prev => ({ ...prev, hybridDaysOnsite: dias }))}
                className={cn(
 "flex-1 py-1.5 px-2 rounded-md text-xs font-medium transition-colors",
                  jobConfig.hybridDaysOnsite === dias || 
                  (jobConfig.hybridDaysOnsite === undefined && dias === (companyConfig?.hybridDaysOnsite || 3))
                    ? "bg-gray-900 text-white"
                    : "border border-lia-border-subtle lia-text-secondary hover:border-gray-900 dark:hover:border-gray-50"
                )}
               
              >
                {dias} {dias === 1 ? 'dia' : 'dias'}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tipo de Contrato */}
      <div>
        <label className="block text-micro font-medium lia-text-secondary mb-1">
          Tipo de Contrato
        </label>
        <div className="flex flex-wrap gap-2">
          {employmentTypes.map((tipo) => (
            <button
              key={tipo}
              onClick={() => setBasicInfoFields(prev => ({ ...prev, tipoContrato: tipo }))}
              className={cn(
 "py-1.5 px-3 rounded-md text-xs font-medium transition-colors",
                basicInfoFields.tipoContrato === tipo
                  ? "bg-gray-900 text-white"
                  : "border border-lia-border-subtle lia-text-secondary hover:border-gray-900 dark:hover:border-gray-50"
              )}
             
            >
              {tipo}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default JobDescriptionStage
