"use client"

/**
 * ReviewPublishStage — painel lateral da etapa review-publish.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.4 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import {
  Code, Brain, DollarSign, MessageCircle, FileText, Globe, Edit2,
  Settings, MapPin, Building2, Check, Rocket, Info, Heart, Calendar,
  Loader2, RefreshCw, X,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type {
  BasicInfoFields,
  TechnicalSkill,
  BehavioralCompetency,
  WSIQuestion,
  DetectedCriteria,
} from "../ExpandedChatContext"
import type { SalaryInfo } from "./SalaryStage"
import type { PublishingPlatform, JobConfig } from "../hooks/usePublishingState"
import type { WizardStage } from "../config/wizard-config"

type CompanyConfig = {
  workModel?: string
  hybridDaysOnsite?: number
  employmentTypes?: string[]
  techStack?: string[]
  values?: string[]
  coreCompetencies?: string[]
  departments?: { id: string; name: string }[]
  benefits?: { name: string; category: string; value?: number; is_active: boolean }[]
  evpBullets?: string[]
  headquarters?: string
  locations?: string[]
} | null

export interface ReviewPublishStageProps {
  // Data
  basicInfoFields: BasicInfoFields
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  salaryInfo: SalaryInfo
  wsiQuestions: WSIQuestion[]
  jobDescription: string
  isGeneratingDescription: boolean
  companyConfig: CompanyConfig
  publishingPlatforms: PublishingPlatform[]
  jobConfig: JobConfig
  detectedCriteria: DetectedCriteria
  publishedJobId: string | null
  // Actions
  onGoToStage: (stage: WizardStage) => void
  onSetCompetenciesTab: (tab: 'technical' | 'behavioral') => void
  onSetPublishingPlatforms: (updater: (prev: PublishingPlatform[]) => PublishingPlatform[]) => void
  onSetJobConfig: (updater: (prev: JobConfig) => JobConfig) => void
  onSetDetectedCriteria: (updater: (prev: DetectedCriteria) => DetectedCriteria) => void
  onUpdateLanguages: (languages: { name: string; level: string }[]) => void
  onGenerateJobDescription: () => void
}

export function ReviewPublishStage({
  basicInfoFields,
  technicalSkills,
  behavioralCompetencies,
  salaryInfo,
  wsiQuestions,
  jobDescription,
  isGeneratingDescription,
  companyConfig,
  publishingPlatforms,
  jobConfig,
  detectedCriteria,
  publishedJobId,
  onGoToStage,
  onSetCompetenciesTab,
  onSetPublishingPlatforms,
  onSetJobConfig,
  onSetDetectedCriteria,
  onUpdateLanguages,
  onGenerateJobDescription,
}: ReviewPublishStageProps) {
  return (
    <>
      {/* Review Summary */}
      <div className="space-y-2.5">
        {/* Job Title Card */}
        <div className="p-3 bg-gray-100 dark:bg-lia-bg-secondary rounded-md">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-base font-semibold lia-text-strong">
                {basicInfoFields.cargo || 'Cargo não definido'}
              </h3>
              <div className="flex items-center gap-2 mt-1 text-xs lia-text-secondary">
                <MapPin className="w-3 h-3" />
                <span>{basicInfoFields.localidade || 'Local não definido'}</span>
                <span className="lia-text-muted">|</span>
                <span>{basicInfoFields.modeloTrabalho || 'Modelo não definido'}</span>
              </div>
            </div>
            <button
              onClick={() => onGoToStage('input-evaluation')}
              className="p-1.5 text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-gray-100 dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none"
            >
              <Edit2 className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-2">
            <span className="px-1.5 py-0.5 bg-lia-bg-secondary rounded-full text-micro lia-text-secondary">{basicInfoFields.area}</span>
            <span className="px-1.5 py-0.5 bg-lia-bg-secondary rounded-full text-micro lia-text-secondary">{basicInfoFields.tipoContrato}</span>
            {basicInfoFields.gestor && (
              <span className="px-1.5 py-0.5 bg-lia-bg-secondary rounded-full text-micro lia-text-secondary">Gestor: {basicInfoFields.gestor}</span>
            )}
          </div>
        </div>

        {/* Technical Requirements Summary */}
        <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Code className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              <span className="text-xs font-medium lia-text-strong">
                Requisitos Técnicos
              </span>
            </div>
            <button
              onClick={() => { onGoToStage('competencies'); onSetCompetenciesTab('technical') }}
              className="p-1 text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-gray-100 dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none"
            >
              <Edit2 className="w-3 h-3" />
            </button>
          </div>
          <div className="flex flex-wrap gap-1">
            {technicalSkills.slice(0, 8).map((skill) => (
              <span
                key={skill.id}
                className={cn(
 "px-1.5 py-0.5 rounded-full text-micro",
                  skill.required
                    ? "bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border border-lia-border-default dark:border-lia-border-default"
                    : "bg-gray-50 lia-text-secondary"
                )}
              >
                {skill.name}
              </span>
            ))}
            {technicalSkills.length > 8 && (
              <span className="px-1.5 py-0.5 bg-gray-50 rounded-full text-micro lia-text-secondary">
                +{technicalSkills.length - 8} mais
              </span>
            )}
          </div>
        </div>

        {/* Behavioral Competencies Summary */}
        <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Brain className="w-3.5 h-3.5 text-chat-cyan" />
              <span className="text-xs font-medium lia-text-strong">
                Competências Comportamentais
              </span>
            </div>
            <button
              onClick={() => { onGoToStage('competencies'); onSetCompetenciesTab('behavioral') }}
              className="p-1 text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-gray-100 dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none"
            >
              <Edit2 className="w-3 h-3" />
            </button>
          </div>
          <div className="flex flex-wrap gap-1">
            {behavioralCompetencies.filter(c => c.enabled).map((comp) => (
              <span
                key={comp.id}
                className="px-1.5 py-0.5 bg-gray-50 rounded-full text-micro lia-text-secondary flex items-center gap-1"
              >
                {comp.name}
                <span className="text-lia-text-secondary dark:text-lia-text-tertiary">({comp.weight}/5)</span>
              </span>
            ))}
          </div>
        </div>

        {/* Salary Summary */}
        <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <DollarSign className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              <span className="text-xs font-medium lia-text-strong">
                Remuneração
              </span>
            </div>
            <button
              onClick={() => onGoToStage('salary')}
              className="p-1 text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-gray-100 dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none"
            >
              <Edit2 className="w-3 h-3" />
            </button>
          </div>
          <div className="text-xs lia-text-strong">
            {salaryInfo.minSalary && salaryInfo.maxSalary ? (
              <span className="font-medium">R$ {salaryInfo.minSalary} - R$ {salaryInfo.maxSalary}</span>
            ) : (
              <span className="lia-text-secondary">Faixa salarial não definida</span>
            )}
            {salaryInfo.minBonus && salaryInfo.maxBonus && (
              <span className="lia-text-secondary ml-2">+ Bônus R$ {salaryInfo.minBonus} - R$ {salaryInfo.maxBonus}</span>
            )}
          </div>
          <div className="text-micro lia-text-secondary mt-1">
            {salaryInfo.benefits.filter(b => b.enabled).length} benefícios inclusos
          </div>
        </div>

        {/* WSI Questions Summary */}
        <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <MessageCircle className="w-3.5 h-3.5 lia-text-secondary" />
              <span className="text-xs font-medium lia-text-strong">
                Triagem WSI
              </span>
            </div>
            <button
              onClick={() => onGoToStage('wsi-questions')}
              className="p-1 text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-gray-100 dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none"
            >
              <Edit2 className="w-3 h-3" />
            </button>
          </div>
          <div className="text-xs lia-text-secondary">
            {wsiQuestions.length} perguntas configuradas via WhatsApp
          </div>
        </div>

        {/* Job Description */}
        <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 lia-text-secondary" />
              <span className="text-xs font-medium lia-text-strong">
                Descrição do Anúncio
              </span>
              {companyConfig && (
                <div className="flex items-center gap-1 text-micro text-lia-text-secondary dark:text-lia-text-tertiary">
                  <Settings className="w-3 h-3" />
                  <span>Tom da empresa</span>
                </div>
              )}
            </div>
            <button
              onClick={onGenerateJobDescription}
              className="p-1 text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-gray-100 dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none"
              title="Regenerar descrição"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>

          {isGeneratingDescription ? (
            <div className="flex items-center gap-2 py-4" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary animate-spin motion-reduce:animate-none" />
              <span className="text-xs lia-text-secondary">Gerando descrição...</span>
            </div>
          ) : (
            <div
              className="text-xs lia-text-strong leading-relaxed whitespace-pre-line bg-gray-50 rounded-md p-2.5 max-h-card-lg overflow-y-auto"
             
            >
              {jobDescription || 'Descrição será gerada automaticamente...'}
            </div>
          )}

          <p className="text-micro lia-text-secondary mt-2 flex items-center gap-1">
            <Brain className="w-3 h-3 text-chat-cyan" />
            Texto gerado por IA baseado nas informações da vaga
          </p>
        </div>

        {/* Ready to proceed */}
        <div className="p-3 bg-gray-50 rounded-md border border-lia-border-subtle">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-wedo-green/10 rounded-full flex items-center justify-center">
              <Globe className="w-4 h-4 text-wedo-green" />
            </div>
            <div>
              <h4 className="text-xs font-medium lia-text-strong">
                Pronto para escolher plataformas!
              </h4>
              <p className="text-micro lia-text-secondary">
                Clique em "Escolher Plataformas" para definir onde publicar
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Publishing Platforms Section (shown after review, before publish) */}
      {publishedJobId === null && (
        <div className="space-y-2.5 mt-2.5">
          {/* Header */}
          <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gray-100 dark:bg-lia-bg-elevated rounded-full flex items-center justify-center">
                <Globe className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
              </div>
              <div>
                <h3 className="text-xs font-semibold lia-text-strong">
                  Onde publicar esta vaga?
                </h3>
                <p className="text-micro lia-text-secondary">
                  Selecione as plataformas para divulgação
                </p>
              </div>
            </div>
          </div>

          {/* ATS Section */}
          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
            <h4 className="text-micro font-semibold lia-text-secondary uppercase tracking-wide mb-2">
              ATS - Sistema de Vagas
            </h4>
            <div className="space-y-2">
              {publishingPlatforms.filter(p => p.type === 'ats').map(platform => (
                <label key={platform.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-md cursor-pointer hover:bg-wedo-cyan/10 transition-colors motion-reduce:transition-none">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-lia-bg-primary rounded-md flex items-center justify-center border border-lia-border-subtle">
                      <Building2 className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    </div>
                    <span className="text-xs lia-text-strong">{platform.name}</span>
                  </div>
                  <button
                    onClick={() => onSetPublishingPlatforms(prev =>
                      prev.map(p => p.id === platform.id ? { ...p, enabled: !p.enabled } : p)
                    )}
                    className={cn(
 "w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors",
                      platform.enabled
                        ? "bg-gray-900 text-white"
                        : "border-2 border-lia-border-subtle hover:border-gray-900 dark:hover:border-gray-50"
                    )}
                  >
                    {platform.enabled && <Check className="w-2.5 h-2.5" />}
                  </button>
                </label>
              ))}
            </div>
          </div>

          {/* Job Boards Section */}
          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
            <h4 className="text-micro font-semibold lia-text-secondary uppercase tracking-wide mb-2">
              Job Boards
            </h4>
            <div className="space-y-2">
              {publishingPlatforms.filter(p => p.type === 'jobboard').map(platform => (
                <label key={platform.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-md cursor-pointer hover:bg-wedo-cyan/10 transition-colors motion-reduce:transition-none">
                  <div className="flex items-center gap-2">
                    <div className={cn(
 "w-6 h-6 rounded-md flex items-center justify-center border border-lia-border-subtle",
                      "bg-gray-800"
                    )}>
                      {platform.id === 'linkedin' ? (
                        <span className="text-white text-micro font-bold">in</span>
                      ) : (
                        <span className="text-white text-micro font-bold">IN</span>
                      )}
                    </div>
                    <span className="text-xs lia-text-strong">{platform.name}</span>
                  </div>
                  <button
                    onClick={() => onSetPublishingPlatforms(prev =>
                      prev.map(p => p.id === platform.id ? { ...p, enabled: !p.enabled } : p)
                    )}
                    className={cn(
 "w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors",
                      platform.enabled
                        ? "bg-gray-900 text-white"
                        : "border-2 border-lia-border-subtle hover:border-gray-900 dark:hover:border-gray-50"
                    )}
                  >
                    {platform.enabled && <Check className="w-2.5 h-2.5" />}
                  </button>
                </label>
              ))}
            </div>
          </div>

          {/* Company Website Section */}
          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
            <h4 className="text-micro font-semibold lia-text-secondary uppercase tracking-wide mb-2">
              Website da Empresa
            </h4>
            <div className="space-y-2">
              {publishingPlatforms.filter(p => p.type === 'website').map(platform => (
                <label key={platform.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-md cursor-pointer hover:bg-wedo-cyan/10 transition-colors motion-reduce:transition-none">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-gray-100 dark:bg-lia-bg-secondary rounded-md flex items-center justify-center border border-lia-border-default dark:border-lia-border-default">
                      <Globe className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    </div>
                    <span className="text-xs lia-text-strong">{platform.name}</span>
                  </div>
                  <button
                    onClick={() => onSetPublishingPlatforms(prev =>
                      prev.map(p => p.id === platform.id ? { ...p, enabled: !p.enabled } : p)
                    )}
                    className={cn(
 "w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors",
                      platform.enabled
                        ? "bg-gray-900 text-white"
                        : "border-2 border-lia-border-subtle hover:border-gray-900 dark:hover:border-gray-50"
                    )}
                  >
                    {platform.enabled && <Check className="w-2.5 h-2.5" />}
                  </button>
                </label>
              ))}
            </div>
          </div>

          {/* Job Configuration Section */}
          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
            <h4 className="text-micro font-semibold lia-text-secondary uppercase tracking-wide mb-2">
              Configurações da Vaga
            </h4>
            <div className="space-y-3">
              {/* Urgency Level */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs lia-text-strong">Urgência</span>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map(level => (
                      <button
                        key={level}
                        onClick={() => onSetJobConfig(prev => ({ ...prev, urgencyLevel: level }))}
                        className={cn(
 "w-6 h-6 rounded-md text-xs font-medium transition-colors",
                          jobConfig.urgencyLevel === level
                            ? level <= 2 ? "bg-wedo-green text-white"
                              : level === 3 ? "bg-status-warning text-white"
                              : "bg-status-error text-white"
                            : "bg-gray-50 lia-text-secondary hover:bg-gray-200"
                        )}
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-micro lia-text-secondary">
                  {jobConfig.urgencyLevel <= 2
                    ? "Baixa: Construção de pipeline - sem pressa"
                    : jobConfig.urgencyLevel === 3
                      ? "Média: Prazo normal de recrutamento"
                      : "Alta: Necessidade imediata - SLAs reduzidos"}
                </p>
              </div>

              {/* Visibility */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs lia-text-strong">Visibilidade</span>
                  <div className="flex gap-1">
                    {[
                      { value: 'public', label: 'Pública' },
                      { value: 'internal', label: 'Interna' },
                      { value: 'confidential', label: 'Confidencial' }
                    ].map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => onSetJobConfig(prev => ({
                          ...prev,
                          visibility: opt.value as JobConfig['visibility'],
                          isConfidential: opt.value === 'confidential'
                        }))}
                        className={cn(
 "px-2 py-1 rounded-md text-micro font-medium transition-colors",
                          jobConfig.visibility === opt.value
                            ? "bg-gray-900 text-white"
                            : "bg-gray-50 lia-text-secondary hover:bg-gray-200"
                        )}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-micro lia-text-secondary" aria-live="polite" aria-atomic="true">
                  {jobConfig.visibility === 'public'
                    ? "Visível em job boards, LinkedIn e site de carreiras"
                    : jobConfig.visibility === 'internal'
                      ? "Apenas funcionários podem ver e se candidatar"
                      : "Vaga sigilosa - nome da empresa não divulgado"}
                </p>
              </div>

              {/* Affirmative Action */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <span className="text-xs lia-text-strong" aria-live="polite" aria-atomic="true">Vaga Afirmativa</span>
                    <Info className="w-3 h-3 lia-text-secondary" />
                  </div>
                  <button
                    onClick={() => onSetJobConfig(prev => ({ ...prev, isAffirmative: !prev.isAffirmative }))}
                    className={cn(
 "w-10 h-5 rounded-full transition-[width,height] relative",
                      jobConfig.isAffirmative ? "bg-gray-900" : "bg-gray-200"
                    )}
                  >
                    <div className={cn(
 "w-4 h-4 bg-lia-bg-primary rounded-full absolute top-0.5 transition-[width,height]",
                      jobConfig.isAffirmative ? "right-0.5" : "left-0.5"
                    )} />
                  </button>
                </div>
                <p className="text-micro lia-text-secondary" aria-live="polite" aria-atomic="true">
                  Vagas afirmativas priorizam grupos historicamente sub-representados (PcD, mulheres, LGBTQIA+, pessoas negras). Sua empresa deve estar preparada para acolher esses profissionais.
                </p>

                {/* Affirmative Criteria Selection */}
                {jobConfig.isAffirmative && (
                  <div className="mt-2 p-2 bg-wedo-cyan/10 rounded-md border border-lia-border-default dark:border-lia-border-default space-y-2">
                    <div>
                      <label className="text-micro font-medium lia-text-strong block mb-1">
                        Critério Principal *
                      </label>
                      <select
                        value={detectedCriteria.affirmativeCriteriaPrimary || ''}
                        onChange={(e) => onSetDetectedCriteria(prev => ({ ...prev, affirmativeCriteriaPrimary: e.target.value || null }))}
                        className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary lia-text-strong"
                      >
                        <option value="">Selecione...</option>
                        <option value="gender">Gênero (Mulheres)</option>
                        <option value="race_ethnicity">Raça/Etnia (Pessoas Negras)</option>
                        <option value="disability">Pessoa com Deficiência (PcD)</option>
                        <option value="lgbtqia">LGBTQIA+</option>
                        <option value="age">Idade 50+</option>
                        <option value="refugee">Pessoa Refugiada</option>
                        <option value="indigenous">Pessoa Indígena</option>
                        <option value="other">Outro</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-micro font-medium lia-text-strong block mb-1">
                        Critério Secundário (opcional)
                      </label>
                      <select
                        value={detectedCriteria.affirmativeCriteriaSecondary || ''}
                        onChange={(e) => onSetDetectedCriteria(prev => ({ ...prev, affirmativeCriteriaSecondary: e.target.value || null }))}
                        className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary lia-text-strong"
                      >
                        <option value="">Nenhum</option>
                        <option value="gender">Gênero (Mulheres)</option>
                        <option value="race_ethnicity">Raça/Etnia (Pessoas Negras)</option>
                        <option value="disability">Pessoa com Deficiência (PcD)</option>
                        <option value="lgbtqia">LGBTQIA+</option>
                        <option value="age">Idade 50+</option>
                        <option value="refugee">Pessoa Refugiada</option>
                        <option value="indigenous">Pessoa Indígena</option>
                        <option value="other">Outro</option>
                      </select>
                    </div>

                    <p className="text-micro lia-text-secondary flex items-center gap-1">
                      <Heart className="w-3 h-3 text-lia-text-secondary dark:text-lia-text-tertiary" />
                      Candidatos elegíveis terão 24h para enviar documentação comprobatória
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Deadlines Section */}
          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
            <h4 className="text-micro font-semibold lia-text-secondary uppercase tracking-wide mb-2 flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              Prazos do Processo
            </h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs lia-text-strong">Prazo Triagem</span>
                <input
                  type="date"
                  value={jobConfig.deadlineScreening}
                  onChange={(e) => onSetJobConfig(prev => ({ ...prev, deadlineScreening: e.target.value }))}
                  className="px-2 py-1 text-xs border border-lia-border-subtle rounded-md bg-gray-50 lia-text-strong"
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs lia-text-strong">Prazo Shortlist</span>
                <input
                  type="date"
                  value={jobConfig.deadlineShortlist}
                  onChange={(e) => onSetJobConfig(prev => ({ ...prev, deadlineShortlist: e.target.value }))}
                  className="px-2 py-1 text-xs border border-lia-border-subtle rounded-md bg-gray-50 lia-text-strong"
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs lia-text-strong">Prazo Final</span>
                <input
                  type="date"
                  value={jobConfig.deadline}
                  onChange={(e) => onSetJobConfig(prev => ({ ...prev, deadline: e.target.value }))}
                  className="px-2 py-1 text-xs border border-lia-border-subtle rounded-md bg-gray-50 lia-text-strong"
                />
              </div>
            </div>
          </div>

          {/* Languages Section */}
          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
            <h4 className="text-micro font-semibold lia-text-secondary uppercase tracking-wide mb-2 flex items-center gap-1">
              <Globe className="w-3 h-3" />
              Idiomas {jobConfig.languages.length > 0 && <span className="text-lia-text-secondary dark:text-lia-text-tertiary">({jobConfig.languages.length})</span>}
            </h4>
            {jobConfig.languages.length > 0 ? (
              <div className="space-y-1">
                {jobConfig.languages.map((lang, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded-md">
                    <select
                      value={lang.name}
                      onChange={(e) => {
                        const newLanguages = [...jobConfig.languages]
                        newLanguages[idx] = { ...newLanguages[idx], name: e.target.value }
                        onUpdateLanguages(newLanguages)
                      }}
                      className="flex-1 px-2 py-0.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary lia-text-strong"
                    >
                      <option value="Inglês">Inglês</option>
                      <option value="Espanhol">Espanhol</option>
                      <option value="Francês">Francês</option>
                      <option value="Alemão">Alemão</option>
                      <option value="Italiano">Italiano</option>
                      <option value="Mandarim">Mandarim</option>
                      <option value="Japonês">Japonês</option>
                      <option value="Português">Português</option>
                      <option value="Outro">Outro</option>
                    </select>
                    <select
                      value={lang.level}
                      onChange={(e) => {
                        const newLanguages = [...jobConfig.languages]
                        newLanguages[idx] = { ...newLanguages[idx], level: e.target.value }
                        onUpdateLanguages(newLanguages)
                      }}
                      className="px-2 py-0.5 text-micro border border-lia-border-subtle rounded-full bg-lia-bg-primary lia-text-strong"
                    >
                      <option value="Básico">Básico</option>
                      <option value="Intermediário">Intermediário</option>
                      <option value="Avançado">Avançado</option>
                      <option value="Fluente">Fluente</option>
                      <option value="Nativo">Nativo</option>
                    </select>
                    <button
                      onClick={() => {
                        const newLanguages = jobConfig.languages.filter((_, i) => i !== idx)
                        onUpdateLanguages(newLanguages)
                      }}
                      className="w-5 h-5 flex items-center justify-center lia-text-secondary hover:text-status-error hover:bg-status-error/10 rounded-md transition-colors motion-reduce:transition-none"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs lia-text-secondary">Nenhum idioma adicionado</p>
            )}
            <button
              onClick={() => onUpdateLanguages([...jobConfig.languages, { name: 'Inglês', level: 'Intermediário' }])}
              className="mt-2 text-micro text-lia-text-secondary dark:text-lia-text-tertiary hover:underline"
            >
              + Adicionar idioma
            </button>
          </div>

          {/* Summary */}
          <div className="p-3 bg-gray-50 rounded-md border border-lia-border-subtle">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-wedo-green/10 rounded-full flex items-center justify-center">
                <Rocket className="w-4 h-4 text-wedo-green" />
              </div>
              <div>
                <h4 className="text-xs font-medium lia-text-strong">
                  {publishingPlatforms.filter(p => p.enabled).length} plataforma(s) selecionada(s)
                </h4>
                <p className="text-micro lia-text-secondary" aria-live="polite" aria-atomic="true">
                  Clique em "Publicar Vaga" para ativar o recrutamento
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
