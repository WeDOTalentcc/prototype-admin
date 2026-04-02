'use client'

import React, { useState } from 'react'
import { 
  FileText, MapPin, Building, Users, DollarSign, Brain, Code, 
  Phone, Rocket, Loader2, RefreshCw, CheckCircle2, Eye,
  Briefcase, Clock, Globe
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWizardContext } from '../WizardContext'

export function ReviewPublishStage() {
  const {
    basicInfoFields,
    technicalSkills,
    behavioralCompetencies,
    salaryInfo,
    wsiCandidates,
    publishingPlatforms,
    setPublishingPlatforms,
    jobDescription,
    setJobDescription,
    isGeneratingDescription,
    setIsGeneratingDescription,
    jobConfig,
    detectedCriteria
  } = useWizardContext()

  const [activeSection, setActiveSection] = useState<string | null>('description')

  const enabledBehavioral = behavioralCompetencies.filter(c => c.enabled)
  const selectedWSI = wsiCandidates.filter(q => q.selected)
  const enabledBenefits = salaryInfo.benefits.filter(b => b.enabled)
  const enabledPlatforms = publishingPlatforms.filter(p => p.enabled)

  const togglePlatform = (id: string) => {
    setPublishingPlatforms(prev => prev.map(p => 
      p.id === id ? { ...p, enabled: !p.enabled } : p
    ))
  }

  /**
   * Parse Brazilian salary format to number.
   * Handles formats like "5.000", "15.000,00", "R$ 10.000"
   */
  const parseBrazilianSalary = (value: string): number | null => {
    if (!value) return null
    // Remove currency symbol, spaces, and dots (thousands separator)
    const cleaned = value.replace(/[R$\s.]/g, '')
    // Replace comma with dot for decimal parsing
    const normalized = cleaned.replace(',', '.')
    const parsed = parseFloat(normalized)
    return isNaN(parsed) ? null : parsed
  }

  const generateDescription = async () => {
    setIsGeneratingDescription(true)
    
    // Parse salaries with Brazilian format support
    const minSalary = parseBrazilianSalary(salaryInfo.minSalary)
    const maxSalary = parseBrazilianSalary(salaryInfo.maxSalary)
    
    try {
      const response = await fetch('/api/backend-proxy/lia/wizard/generate-description/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: basicInfoFields.cargo || undefined,
          department: basicInfoFields.area || undefined,
          seniority: detectedCriteria.senioridadeIdiomas || undefined,
          work_model: basicInfoFields.modeloTrabalho || undefined,
          location: basicInfoFields.localidade || undefined,
          skills: technicalSkills.length > 0 ? technicalSkills.map(s => s.name) : undefined,
          behavioral_competencies: enabledBehavioral.length > 0 ? enabledBehavioral.map(c => c.name) : undefined,
          salary_range: minSalary && maxSalary ? { min: minSalary, max: maxSalary } : undefined,
          benefits: enabledBenefits.length > 0 ? enabledBenefits.map(b => b.name) : undefined,
          responsibilities: detectedCriteria.responsabilidades?.length > 0 ? detectedCriteria.responsabilidades : undefined,
        }),
      })
      
      if (response.ok) {
        const data = await response.json()
        setJobDescription(data.full_description || data.description || '')
      } else {
        // Fallback to generated text
        generateFallbackDescription()
      }
    } catch (error) {
      generateFallbackDescription()
    } finally {
      setIsGeneratingDescription(false)
    }
  }

  const generateFallbackDescription = () => {
    const fallback = `## ${basicInfoFields.cargo || 'Desenvolvedor'}

**Sobre a oportunidade**

Estamos em busca de um profissional talentoso para integrar nossa equipe de ${basicInfoFields.area || 'Tecnologia'}. Esta é uma posição ${basicInfoFields.modeloTrabalho || 'Híbrida'} baseada em ${basicInfoFields.localidade || 'São Paulo'}.

**Competências Técnicas**
${technicalSkills.map(s => `- ${s.name} (${s.level})`).join('\n')}

**Competências Comportamentais**
${enabledBehavioral.map(c => `- ${c.name}`).join('\n')}

**Benefícios**
${enabledBenefits.map(b => `- ${b.name}${b.value ? ` - ${b.value}` : ''}`).join('\n')}

**Remuneração**
${salaryInfo.minSalary && salaryInfo.maxSalary 
  ? `R$ ${salaryInfo.minSalary} - R$ ${salaryInfo.maxSalary}`
  : 'A combinar'}`
    
    setJobDescription(fallback)
  }

  const SectionCard = ({ 
    id, 
    title, 
    icon: Icon, 
    children, 
    count 
  }: { 
    id: string
    title: string
    icon: React.ElementType
    children: React.ReactNode
    count?: number
  }) => (
    <div className="rounded-md border border-lia-border-subtle overflow-hidden">
      <button
        onClick={() => setActiveSection(activeSection === id ? null : id)}
        className="w-full px-3 py-2 bg-lia-bg-secondary flex items-center justify-between hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-lia-text-secondary" />
          <span className="text-xs font-semibold text-lia-text-primary">
            {title}
          </span>
          {count !== undefined && (
            <span className="px-1.5 py-0.5 bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary text-micro font-medium rounded-full">
              {count}
            </span>
          )}
        </div>
        <CheckCircle2 className="w-4 h-4 text-status-success" />
      </button>
      {activeSection === id && (
        <div className="p-3 bg-lia-bg-primary border-t border-lia-border-subtle">
          {children}
        </div>
      )}
    </div>
  )

  return (
    <div className="space-y-3">
      {/* Job Description Section */}
      <div className="rounded-md border border-lia-border-subtle overflow-hidden">
        <div className="px-3 py-2 bg-lia-bg-secondary flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-lia-text-secondary" />
            <span className="text-xs font-semibold text-lia-text-primary" aria-live="polite" aria-atomic="true">
              Descrição da Vaga
            </span>
          </div>
          <button
            onClick={generateDescription}
            disabled={isGeneratingDescription}
            className="flex items-center gap-1 px-2 py-1 text-micro text-lia-text-secondary hover:bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full transition-colors motion-reduce:transition-none"
          >
            {isGeneratingDescription ? (
              <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
            ) : (
              <RefreshCw className="w-3 h-3" />
            )}
            {jobDescription ? 'Regenerar' : 'Gerar'}
          </button>
        </div>
        <div className="p-3 bg-lia-bg-primary border-t border-lia-border-subtle" role="status" aria-live="polite" aria-label="Carregando...">
          {isGeneratingDescription ? (
            <div className="flex items-center justify-center py-8 gap-2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-5 h-5 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
              <span className="text-sm lia-text-secondary">Gerando descrição...</span>
            </div>
          ) : jobDescription ? (
            <div className="prose prose-sm max-w-none">
              <pre className="whitespace-pre-wrap text-xs text-lia-text-primary font-sans leading-relaxed">
                {jobDescription}
              </pre>
            </div>
          ) : (
            <button
              onClick={generateDescription}
              className="w-full py-6 border-2 border-dashed border-lia-border-subtle rounded-md text-lia-text-secondary hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex flex-col items-center gap-2"
            >
              <FileText className="w-6 h-6" />
              <span className="text-xs font-medium" aria-live="polite" aria-atomic="true">Clique para gerar a descrição da vaga</span>
            </button>
          )}
        </div>
      </div>

      {/* Basic Info Summary */}
      <SectionCard id="basic" title="Informações Básicas" icon={Briefcase}>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1.5">
            <Briefcase className="w-3 h-3 lia-text-secondary" />
            <span className="lia-text-secondary">Cargo:</span>
            <span className="font-medium text-lia-text-primary">{basicInfoFields.cargo || '-'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Building className="w-3 h-3 lia-text-secondary" />
            <span className="lia-text-secondary">Área:</span>
            <span className="font-medium text-lia-text-primary">{basicInfoFields.area || '-'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <MapPin className="w-3 h-3 lia-text-secondary" />
            <span className="lia-text-secondary">Local:</span>
            <span className="font-medium text-lia-text-primary">{basicInfoFields.localidade || '-'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Globe className="w-3 h-3 lia-text-secondary" />
            <span className="lia-text-secondary">Modelo:</span>
            <span className="font-medium text-lia-text-primary">{basicInfoFields.modeloTrabalho || '-'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="w-3 h-3 lia-text-secondary" />
            <span className="lia-text-secondary">Contrato:</span>
            <span className="font-medium text-lia-text-primary">{basicInfoFields.tipoContrato || '-'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Users className="w-3 h-3 lia-text-secondary" />
            <span className="lia-text-secondary">Gestor:</span>
            <span className="font-medium text-lia-text-primary">{basicInfoFields.gestor || '-'}</span>
          </div>
        </div>
      </SectionCard>

      {/* Competencies Summary */}
      <SectionCard id="competencies" title="Competências" icon={Code} count={technicalSkills.length + enabledBehavioral.length}>
        <div className="space-y-2">
          <div>
            <span className="text-micro font-semibold lia-text-secondary uppercase">Técnicas ({technicalSkills.length})</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {technicalSkills.slice(0, 8).map(s => (
                <span key={s.id} className="px-1.5 py-0.5 bg-wedo-cyan/10 text-wedo-cyan-dark text-micro rounded-full">
                  {s.name}
                </span>
              ))}
              {technicalSkills.length > 8 && (
                <span className="px-1.5 py-0.5 bg-lia-bg-tertiary lia-text-secondary text-micro rounded-full">
                  +{technicalSkills.length - 8} mais
                </span>
              )}
            </div>
          </div>
          <div>
            <span className="text-micro font-semibold lia-text-secondary uppercase">Comportamentais ({enabledBehavioral.length})</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {enabledBehavioral.map(c => (
                <span key={c.id} className="px-1.5 py-0.5 bg-wedo-purple/10 text-wedo-purple text-micro rounded-full">
                  {c.name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Salary Summary */}
      <SectionCard id="salary" title="Remuneração" icon={DollarSign}>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="lia-text-secondary">Salário Base:</span>
            <span className="font-medium text-lia-text-primary">
              {salaryInfo.minSalary && salaryInfo.maxSalary 
                ? `R$ ${salaryInfo.minSalary} - R$ ${salaryInfo.maxSalary}`
                : 'Não informado'}
            </span>
          </div>
          {(salaryInfo.minBonus || salaryInfo.maxBonus) && (
            <div className="flex justify-between">
              <span className="lia-text-secondary">Bônus:</span>
              <span className="font-medium text-lia-text-primary">
                R$ {salaryInfo.minBonus} - R$ {salaryInfo.maxBonus}
              </span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="lia-text-secondary">Benefícios:</span>
            <span className="font-medium text-lia-text-secondary">{enabledBenefits.length} selecionados</span>
          </div>
        </div>
      </SectionCard>

      {/* WSI Questions Summary */}
      <SectionCard id="wsi" title="Perguntas WSI" icon={Phone} count={selectedWSI.length}>
        <div className="space-y-1.5">
          {selectedWSI.map((q, i) => (
            <div key={q.id} className="flex items-start gap-2 text-xs">
              <span className="w-4 h-4 rounded-full bg-whatsapp-green/10 text-whatsapp-green text-micro flex items-center justify-center flex-shrink-0">
                {i + 1}
              </span>
              <span className="text-lia-text-primary line-clamp-1">{q.question}</span>
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Publishing Platforms */}
      <div className="rounded-md border border-lia-border-subtle overflow-hidden">
        <div className="px-3 py-2 bg-lia-bg-secondary flex items-center gap-2">
          <Rocket className="w-4 h-4 text-lia-text-secondary" />
          <span className="text-xs font-semibold text-lia-text-primary">
            Publicar em
          </span>
        </div>
        <div className="p-3 bg-lia-bg-primary border-t border-lia-border-subtle">
          <div className="grid grid-cols-2 gap-2">
            {publishingPlatforms.map(platform => (
              <button
                key={platform.id}
                onClick={() => togglePlatform(platform.id)}
                className={cn(
 "flex items-center gap-2 p-2 rounded-md transition-colors",
                  platform.enabled
                    ? "bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-btn-primary-bg"
                    : "bg-lia-bg-secondary border border-transparent hover:border-lia-border-subtle"
                )}
              >
                <div className={cn(
 "w-4 h-4 rounded-md flex items-center justify-center",
                  platform.enabled ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" : "border border-lia-border-subtle"
                )}>
                  {platform.enabled && <CheckCircle2 className="w-2.5 h-2.5" />}
                </div>
                <span className="text-xs font-medium text-lia-text-primary">
                  {platform.name}
                </span>
              </button>
            ))}
          </div>
          <p className="text-micro lia-text-secondary mt-2">
            {enabledPlatforms.length} plataforma(s) selecionada(s)
          </p>
        </div>
      </div>
    </div>
  )
}

export default ReviewPublishStage
