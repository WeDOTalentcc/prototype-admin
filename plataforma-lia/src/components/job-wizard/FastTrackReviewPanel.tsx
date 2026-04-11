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

import { formatBRL, formatBRLCompact } from"@/lib/pricing"
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
import type { FastTrackJobData } from '@/hooks/recruitment/useFastTrack'
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
    <div className="border border-lia-border-default rounded-xl overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-lia-btn-primary-hover/50 hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
      >
        <div className="flex items-center gap-2">
          <span className="text-lia-text-tertiary">{icon}</span>
          <span className="text-sm font-medium text-white">{title}</span>
          {count !== undefined && (
            <Badge variant="outline" className="text-xs border-lia-border-default text-lia-text-tertiary">
              {count}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {onEdit && (
            <button 
              onClick={(e) => { e.stopPropagation(); onEdit() }}
              className="p-1 text-lia-text-secondary hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none"
            >
              <Edit2 className="w-3 h-3" />
            </button>
          )}
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-lia-text-secondary" />
          ) : (
            <ChevronRight className="w-4 h-4 text-lia-text-secondary" />
          )}
        </div>
      </button>
      
      {isOpen && (
        <div className="p-3 border-t border-lia-border-default/50 bg-lia-bg-overlay/50">
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
    return formatBRLCompact(num)
  }
  
  const canPublish = 
    sensitiveFields.gestor && 
    sensitiveFields.localidade && 
    sensitiveFields.dataLimite &&
    sensitiveFields.isAffirmative !== null
  
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 p-3 bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default rounded-xl">
        <Zap className="w-4 h-4 text-lia-text-secondary" />
        <div>
          <span className="text-sm font-medium text-lia-text-secondary">Vaga criada com Fast Track</span>
          <p className="text-xs text-lia-text-tertiary">
            Baseada em: {jobData.sourceJobTitle}
          </p>
        </div>
      </div>
      
      <div className="p-3 bg-status-warning/10 border border-status-warning/30/30 rounded-xl space-y-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-status-warning" />
          <span className="text-sm font-medium text-status-warning">
            Campos que precisam sua atenção
          </span>
        </div>
        
        <div className="space-y-3">
          <div className="space-y-1">
            <Label htmlFor="gestor" className="text-xs text-lia-text-tertiary flex items-center gap-1">
              <User className="w-3 h-3" /> Gestor responsável
            </Label>
            <Input
              id="gestor"
              value={sensitiveFields.gestor}
              onChange={(e) => handleFieldChange('gestor', e.target.value)}
              placeholder="Nome do gestor"
              className="bg-lia-btn-primary-hover border-lia-border-default text-white"
            />
          </div>
          
          <div className="space-y-1">
            <Label htmlFor="localidade" className="text-xs text-lia-text-tertiary flex items-center gap-1">
              <MapPin className="w-3 h-3" /> Localização
            </Label>
            <Input
              id="localidade"
              value={sensitiveFields.localidade}
              onChange={(e) => handleFieldChange('localidade', e.target.value)}
              placeholder="Cidade, Estado"
              className="bg-lia-btn-primary-hover border-lia-border-default text-white"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="numeroVagas" className="text-xs text-lia-text-tertiary flex items-center gap-1">
                <Briefcase className="w-3 h-3" /> Nº de vagas
              </Label>
              <Input
                id="numeroVagas"
                type="number"
                min="1"
                value={sensitiveFields.numeroVagas}
                onChange={(e) => handleFieldChange('numeroVagas', e.target.value)}
                className="bg-lia-btn-primary-hover border-lia-border-default text-white"
              />
            </div>
            
            <div className="space-y-1">
              <Label htmlFor="dataLimite" className="text-xs text-lia-text-tertiary flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Data limite
              </Label>
              <Input
                id="dataLimite"
                type="date"
                value={sensitiveFields.dataLimite}
                onChange={(e) => handleFieldChange('dataLimite', e.target.value)}
                className="bg-lia-btn-primary-hover border-lia-border-default text-white"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label className="text-xs text-lia-text-tertiary">Vaga afirmativa?</Label>
            <RadioGroup
              value={sensitiveFields.isAffirmative || ''}
              onValueChange={(value) => handleFieldChange('isAffirmative', value as 'yes' | 'no')}
              className="flex gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="no" id="affirmative-no" />
                <Label htmlFor="affirmative-no" className="text-sm text-lia-text-disabled">Não</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="yes" id="affirmative-yes" />
                <Label htmlFor="affirmative-yes" className="text-sm text-lia-text-disabled">Sim</Label>
              </div>
            </RadioGroup>
          </div>
        </div>
      </div>
      
      {hasCompetencyChanges && (
        <div className="p-3 bg-wedo-cyan/10 border border-wedo-cyan/30/30 rounded-xl">
          <div className="flex items-start gap-2">
            <HelpCircle className="w-4 h-4 text-wedo-cyan-dark mt-0.5" />
            <div>
              <span className="text-sm font-medium text-wedo-cyan-dark">
                Competências foram alteradas
              </span>
              <p className="text-xs text-wedo-cyan-dark/70 mt-1">
                As perguntas WSI podem precisar de atualização.
              </p>
              <Button
                onClick={onRequestWSIRegeneration}
                size="sm"
                variant="outline"
                className="mt-2 text-xs border-wedo-cyan/30/50 text-wedo-cyan-dark hover:bg-wedo-cyan/10"
              >
                Regenerar perguntas WSI
              </Button>
            </div>
          </div>
        </div>
      )}
      
      <div className="space-y-2">
        <span className="text-xs text-lia-text-secondary uppercase tracking-wide">
          Campos copiados
        </span>
        
        <CollapsibleSection 
          title="Descrição da Vaga" 
          icon={<FileText className="w-4 h-4" />}
          onEdit={() => onEditSection('description')}
        >
          <div className="space-y-2 text-sm text-lia-text-disabled">
            <div>
              <span className="text-lia-text-secondary">Cargo:</span>{' '}
              {jobData.basicInfo.cargo || '-'}
            </div>
            <div>
              <span className="text-lia-text-secondary">Área:</span>{' '}
              {jobData.basicInfo.area || '-'}
            </div>
            <div>
              <span className="text-lia-text-secondary">Modelo:</span>{' '}
              {jobData.basicInfo.modeloTrabalho || '-'}
            </div>
            <div>
              <span className="text-lia-text-secondary">Contrato:</span>{' '}
              {jobData.basicInfo.tipoContrato || '-'}
            </div>
            {jobData.generatedDescription && (
              <div className="mt-2 p-2 bg-lia-btn-primary-hover rounded-md text-xs text-lia-text-tertiary max-h-24 overflow-y-auto">
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
                className={cn("text-xs",
                  skill.required 
                    ?"bg-lia-bg-tertiary dark:bg-lia-bg-secondary border-lia-border-default dark:border-lia-border-default text-lia-text-secondary" 
                    :"bg-lia-btn-primary-hover border-lia-border-default text-lia-text-disabled"
                )}
              >
                {skill.name}
                {skill.required && <span className="ml-1 text-lia-text-secondary">*</span>}
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
                <span className="text-sm text-lia-text-disabled">{comp.name}</span>
                <div className="flex items-center gap-1">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div
                      key={i}
                      className={cn("w-2 h-2 rounded-full",
                        i < comp.weight ?"bg-lia-border-medium" :"bg-lia-bg-inverse"
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
              <span className="text-lia-text-secondary">Salário:</span>
              <span className="text-lia-text-disabled">
                {formatSalary(jobData.salaryInfo.minSalary)} - {formatSalary(jobData.salaryInfo.maxSalary)}
              </span>
            </div>
            {jobData.salaryInfo.benefits && (
              <div className="flex flex-wrap gap-1 mt-2">
                {jobData.salaryInfo.benefits.filter(b => b.enabled).map((benefit) => (
                  <Badge 
                    key={benefit.id}
                    variant="outline" 
                    className="text-xs bg-lia-btn-primary-hover border-lia-border-default text-lia-text-tertiary"
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
                  <span className="text-lia-text-secondary">{index + 1}.</span>{' '}
                  <span className="text-lia-text-disabled">{question.question}</span>
                  <Badge 
                    variant="outline" 
                    className="ml-2 text-xs border-lia-border-default text-lia-text-secondary"
                  >
                    {question.type}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-lia-text-secondary italic">
              Nenhuma pergunta configurada. As perguntas globais da empresa serão aplicadas.
            </p>
          )}
        </CollapsibleSection>
      </div>
      
      <Button
        onClick={onPublish}
        disabled={!canPublish || isPublishing}
        className={cn("w-full",
          canPublish 
            ?"bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active" 
            :"bg-lia-bg-inverse text-lia-text-secondary cursor-not-allowed"
        )}
      >
        {isPublishing ? (
          <>
            <span className="animate-spin motion-reduce:animate-none mr-2">⏳</span>
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
        <p className="text-xs text-center text-status-warning">
          Preencha todos os campos obrigatórios acima
        </p>
      )}
    </div>
  )
}

export default FastTrackReviewPanel
