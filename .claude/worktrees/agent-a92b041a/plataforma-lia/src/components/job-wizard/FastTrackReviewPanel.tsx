/**
 * FastTrackReviewPanel Component
 * 
 * Displays all copied fields in collapsible sections for review.
 * Follows LIA Conversational Philosophy:
 * - All data in sidebar panel
 * - Editable fields for quick adjustments
 * - Highlights sensitive fields requiring confirmation
 */
'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { 
  ChevronDown, 
  ChevronRight, 
  Zap,
  AlertTriangle,
  Code,
  Users,
  DollarSign,
  HelpCircle,
  FileText,
  MapPin,
  Briefcase,
  User,
  Calendar,
  Edit2,
  Check
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import type { FastTrackJobData } from '@/hooks/useFastTrack'
import type { 
  TechnicalSkill, 
  BehavioralCompetency, 
  WSIQuestion 
} from '@/components/expanded-chat/ExpandedChatContext'

interface SensitiveFieldsState {
  gestor: string
  localidade: string
  numeroVagas: string
  dataLimite: string
  isAffirmative: 'yes' | 'no' | null
  affirmativeGroup?: string
}

interface FastTrackReviewPanelProps {
  jobData: FastTrackJobData
  onUpdateSensitiveFields: (fields: SensitiveFieldsState) => void
  onEditSection: (section: string) => void
  onPublish: () => void
  onRequestWSIRegeneration: () => void
  isPublishing?: boolean
  hasCompetencyChanges?: boolean
}

interface CollapsibleSectionProps {
  title: string
  icon: React.ReactNode
  count?: number
  defaultOpen?: boolean
  children: React.ReactNode
  onEdit?: () => void
}

function CollapsibleSection({ 
  title, 
  icon, 
  count, 
  defaultOpen = false, 
  children,
  onEdit 
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  
  return (
    <div className="border border-neutral-700 rounded-md overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-neutral-800/50 hover:bg-neutral-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-neutral-400">{icon}</span>
          <span className="text-sm font-medium text-white">{title}</span>
          {count !== undefined && (
            <Badge variant="outline" className="text-xs border-neutral-600 text-neutral-400">
              {count}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {onEdit && (
            <button 
              onClick={(e) => { e.stopPropagation(); onEdit() }}
              className="p-1 text-neutral-500 hover:text-gray-300 transition-colors"
            >
              <Edit2 className="w-3 h-3" />
            </button>
          )}
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-neutral-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-neutral-500" />
          )}
        </div>
      </button>
      
      {isOpen && (
        <div className="p-3 border-t border-neutral-700/50 bg-neutral-900/50">
          {children}
        </div>
      )}
    </div>
  )
}

export function FastTrackReviewPanel({
  jobData,
  onUpdateSensitiveFields,
  onEditSection,
  onPublish,
  onRequestWSIRegeneration,
  isPublishing = false,
  hasCompetencyChanges = false,
}: FastTrackReviewPanelProps) {
  const [sensitiveFields, setSensitiveFields] = useState<SensitiveFieldsState>({
    gestor: jobData.basicInfo.gestor || '',
    localidade: jobData.basicInfo.localidade || '',
    numeroVagas: '1',
    dataLimite: '',
    isAffirmative: null,
  })
  
  const handleFieldChange = (field: keyof SensitiveFieldsState, value: string) => {
    const updated = { ...sensitiveFields, [field]: value }
    setSensitiveFields(updated)
    onUpdateSensitiveFields(updated)
  }
  
  const formatSalary = (value?: string) => {
    if (!value) return '-'
    const num = parseInt(value)
    if (isNaN(num)) return value
    return `R$ ${(num / 1000).toFixed(0)}k`
  }
  
  const canPublish = 
    sensitiveFields.gestor && 
    sensitiveFields.localidade && 
    sensitiveFields.dataLimite &&
    sensitiveFields.isAffirmative !== null
  
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 p-3 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md">
        <Zap className="w-4 h-4 text-gray-700 dark:text-gray-300" />
        <div>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Vaga criada com Fast Track</span>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Baseada em: {jobData.sourceJobTitle}
          </p>
        </div>
      </div>
      
      <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-md space-y-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-medium text-yellow-400">
            Campos que precisam sua atenção
          </span>
        </div>
        
        <div className="space-y-3">
          <div className="space-y-1">
            <Label htmlFor="gestor" className="text-xs text-neutral-400 flex items-center gap-1">
              <User className="w-3 h-3" /> Gestor responsável
            </Label>
            <Input
              id="gestor"
              value={sensitiveFields.gestor}
              onChange={(e) => handleFieldChange('gestor', e.target.value)}
              placeholder="Nome do gestor"
              className="bg-neutral-800 border-neutral-700 text-white"
            />
          </div>
          
          <div className="space-y-1">
            <Label htmlFor="localidade" className="text-xs text-neutral-400 flex items-center gap-1">
              <MapPin className="w-3 h-3" /> Localização
            </Label>
            <Input
              id="localidade"
              value={sensitiveFields.localidade}
              onChange={(e) => handleFieldChange('localidade', e.target.value)}
              placeholder="Cidade, Estado"
              className="bg-neutral-800 border-neutral-700 text-white"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="numeroVagas" className="text-xs text-neutral-400 flex items-center gap-1">
                <Briefcase className="w-3 h-3" /> Nº de vagas
              </Label>
              <Input
                id="numeroVagas"
                type="number"
                min="1"
                value={sensitiveFields.numeroVagas}
                onChange={(e) => handleFieldChange('numeroVagas', e.target.value)}
                className="bg-neutral-800 border-neutral-700 text-white"
              />
            </div>
            
            <div className="space-y-1">
              <Label htmlFor="dataLimite" className="text-xs text-neutral-400 flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Data limite
              </Label>
              <Input
                id="dataLimite"
                type="date"
                value={sensitiveFields.dataLimite}
                onChange={(e) => handleFieldChange('dataLimite', e.target.value)}
                className="bg-neutral-800 border-neutral-700 text-white"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label className="text-xs text-neutral-400">Vaga afirmativa?</Label>
            <RadioGroup
              value={sensitiveFields.isAffirmative || ''}
              onValueChange={(value) => handleFieldChange('isAffirmative', value as 'yes' | 'no')}
              className="flex gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="no" id="affirmative-no" />
                <Label htmlFor="affirmative-no" className="text-sm text-neutral-300">Não</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="yes" id="affirmative-yes" />
                <Label htmlFor="affirmative-yes" className="text-sm text-neutral-300">Sim</Label>
              </div>
            </RadioGroup>
          </div>
        </div>
      </div>
      
      {hasCompetencyChanges && (
        <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-md">
          <div className="flex items-start gap-2">
            <HelpCircle className="w-4 h-4 text-blue-400 mt-0.5" />
            <div>
              <span className="text-sm font-medium text-blue-400">
                Competências foram alteradas
              </span>
              <p className="text-xs text-blue-400/70 mt-1">
                As perguntas WSI podem precisar de atualização.
              </p>
              <Button
                onClick={onRequestWSIRegeneration}
                size="sm"
                variant="outline"
                className="mt-2 text-xs border-blue-500/50 text-blue-400 hover:bg-blue-500/10"
              >
                Regenerar perguntas WSI
              </Button>
            </div>
          </div>
        </div>
      )}
      
      <div className="space-y-2">
        <span className="text-xs text-neutral-500 uppercase tracking-wide">
          Campos copiados
        </span>
        
        <CollapsibleSection 
          title="Descrição da Vaga" 
          icon={<FileText className="w-4 h-4" />}
          onEdit={() => onEditSection('description')}
        >
          <div className="space-y-2 text-sm text-neutral-300">
            <div>
              <span className="text-neutral-500">Cargo:</span>{' '}
              {jobData.basicInfo.cargo || '-'}
            </div>
            <div>
              <span className="text-neutral-500">Área:</span>{' '}
              {jobData.basicInfo.area || '-'}
            </div>
            <div>
              <span className="text-neutral-500">Modelo:</span>{' '}
              {jobData.basicInfo.modeloTrabalho || '-'}
            </div>
            <div>
              <span className="text-neutral-500">Contrato:</span>{' '}
              {jobData.basicInfo.tipoContrato || '-'}
            </div>
            {jobData.generatedDescription && (
              <div className="mt-2 p-2 bg-neutral-800 rounded text-xs text-neutral-400 max-h-24 overflow-y-auto">
                {jobData.generatedDescription.slice(0, 200)}...
              </div>
            )}
          </div>
        </CollapsibleSection>
        
        <CollapsibleSection 
          title="Competências Técnicas" 
          icon={<Code className="w-4 h-4" />}
          count={jobData.technicalSkills.length}
          onEdit={() => onEditSection('skills')}
        >
          <div className="flex flex-wrap gap-1">
            {jobData.technicalSkills.map((skill) => (
              <Badge 
                key={skill.id} 
                variant="outline" 
                className={cn(
                  "text-xs",
                  skill.required 
                    ? "bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300" 
                    : "bg-neutral-800 border-neutral-700 text-neutral-300"
                )}
              >
                {skill.name}
                {skill.required && <span className="ml-1 text-gray-700 dark:text-gray-300">*</span>}
              </Badge>
            ))}
          </div>
        </CollapsibleSection>
        
        <CollapsibleSection 
          title="Competências Comportamentais" 
          icon={<Users className="w-4 h-4" />}
          count={jobData.behavioralCompetencies.length}
          onEdit={() => onEditSection('behavioral')}
        >
          <div className="space-y-1">
            {jobData.behavioralCompetencies.map((comp) => (
              <div 
                key={comp.id} 
                className="flex items-center justify-between py-1"
              >
                <span className="text-sm text-neutral-300">{comp.name}</span>
                <div className="flex items-center gap-1">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "w-2 h-2 rounded-full",
                        i < comp.weight ? "bg-gray-400 dark:bg-gray-500" : "bg-neutral-700"
                      )}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>
        
        <CollapsibleSection 
          title="Remuneração e Benefícios" 
          icon={<DollarSign className="w-4 h-4" />}
          onEdit={() => onEditSection('salary')}
        >
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-neutral-500">Salário:</span>
              <span className="text-neutral-300">
                {formatSalary(jobData.salaryInfo.minSalary)} - {formatSalary(jobData.salaryInfo.maxSalary)}
              </span>
            </div>
            {jobData.salaryInfo.benefits && (
              <div className="flex flex-wrap gap-1 mt-2">
                {jobData.salaryInfo.benefits.filter(b => b.enabled).map((benefit) => (
                  <Badge 
                    key={benefit.id}
                    variant="outline" 
                    className="text-xs bg-neutral-800 border-neutral-700 text-neutral-400"
                  >
                    {benefit.name}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </CollapsibleSection>
        
        <CollapsibleSection 
          title="Perguntas de Triagem WSI" 
          icon={<HelpCircle className="w-4 h-4" />}
          count={jobData.wsiQuestions.length}
          onEdit={() => onEditSection('wsi')}
        >
          {jobData.wsiQuestions.length > 0 ? (
            <div className="space-y-2">
              {jobData.wsiQuestions.map((question, index) => (
                <div key={question.id} className="text-sm">
                  <span className="text-neutral-500">{index + 1}.</span>{' '}
                  <span className="text-neutral-300">{question.question}</span>
                  <Badge 
                    variant="outline" 
                    className="ml-2 text-xs border-neutral-700 text-neutral-500"
                  >
                    {question.type}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-neutral-500 italic">
              Nenhuma pergunta configurada. As perguntas globais da empresa serão aplicadas.
            </p>
          )}
        </CollapsibleSection>
      </div>
      
      <Button
        onClick={onPublish}
        disabled={!canPublish || isPublishing}
        className={cn(
          "w-full",
          canPublish 
            ? "bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200" 
            : "bg-neutral-700 text-neutral-500 cursor-not-allowed"
        )}
      >
        {isPublishing ? (
          <>
            <span className="animate-spin mr-2">⏳</span>
            Publicando...
          </>
        ) : (
          <>
            <Check className="w-4 h-4 mr-2" />
            Publicar Vaga
          </>
        )}
      </Button>
      
      {!canPublish && (
        <p className="text-xs text-center text-yellow-400">
          Preencha todos os campos obrigatórios acima
        </p>
      )}
    </div>
  )
}

export default FastTrackReviewPanel
