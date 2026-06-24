"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { AlertTriangle, FileText, Briefcase, Award, GraduationCap, X, CheckCircle2, XCircle } from "lucide-react"
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"

export interface DataRequirement {
  field: string
  label: string
  hasData: boolean
  required: boolean
  description?: string
}

interface InsufficientDataModalProps {
  isOpen: boolean
  onClose: () => void
  onProceedAnyway?: () => void
  requirements: DataRequirement[]
  candidateName?: string
}

export function InsufficientDataModal({
  isOpen,
  onClose,
  onProceedAnyway,
  requirements,
  candidateName
}: InsufficientDataModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('insufficient-data', isOpen)

  const requiredMissing = requirements.filter(r => r.required && !r.hasData)
  const optionalMissing = requirements.filter(r => !r.required && !r.hasData)
  const hasEnoughData = requiredMissing.length === 0
  
  const getIcon = (field: string) => {
    switch (field) {
      case 'resume':
      case 'summary':
        return <FileText className="w-4 h-4" />
      case 'experiences':
      case 'workHistory':
        return <Briefcase className="w-4 h-4" />
      case 'skills':
        return <Award className="w-4 h-4" />
      case 'education':
        return <GraduationCap className="w-4 h-4" />
      default:
        return <FileText className="w-4 h-4" />
    }
  }
  
  return (
    <AlertDialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
      <AlertDialogContent className="max-w-md rounded-md" data-testid="insufficient-data-modal">
        <AlertDialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className={`p-2.5 rounded-md ${hasEnoughData ? 'bg-status-warning/15 text-status-warning' : 'bg-status-error/15 text-status-error'}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            <AlertDialogTitle className="text-lg font-semibold">
              {hasEnoughData ? 'Dados limitados' : 'Dados insuficientes'}
            </AlertDialogTitle>
          </div>
          <AlertDialogDescription asChild>
            <div className="space-y-4">
              <p className="text-lia-text-primary">
                {hasEnoughData ? (
                  <>
                    Para gerar um parecer mais preciso para <strong className="text-lia-text-primary">{candidateName || 'este candidato'}</strong>, 
                    seria ideal ter mais informações disponíveis.
                  </>
                ) : (
                  <>
                    Não é possível gerar um parecer de qualidade para <strong className="text-lia-text-primary">{candidateName || 'este candidato'}</strong> 
                    {' '}sem as informações essenciais abaixo.
                  </>
                )}
              </p>
              
              {requiredMissing.length > 0 && (
                <div className="p-3 rounded-xl bg-status-error/10 border border-status-error/30">
                  <h4 className="text-xs font-semibold text-status-error mb-2 flex items-center gap-1.5">
                    <XCircle className="w-4 h-4" />
                    Informações obrigatórias faltando
                  </h4>
                  <ul className="space-y-1.5">
                    {requiredMissing.map((req) => (
                      <li key={req.field} className="flex items-start gap-2">
                        <span className="text-status-error mt-0.5">{getIcon(req.field)}</span>
                        <div>
                          <span className="text-xs font-medium text-status-error">{req.label}</span>
                          {req.description && (
                            <p className="text-xs text-status-error">{req.description}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {optionalMissing.length > 0 && (
                <div className="p-3 rounded-xl bg-status-warning/10 border border-status-warning/30">
                  <h4 className="text-xs font-semibold text-status-warning mb-2 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    Informações recomendadas para melhor análise
                  </h4>
                  <ul className="space-y-1.5">
                    {optionalMissing.map((req) => (
                      <li key={req.field} className="flex items-start gap-2">
                        <span className="text-status-warning mt-0.5">{getIcon(req.field)}</span>
                        <div>
                          <span className="text-xs font-medium text-status-warning">{req.label}</span>
                          {req.description && (
                            <p className="text-xs text-status-warning">{req.description}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {requirements.filter(r => r.hasData).length > 0 && (
                <div className="p-3 rounded-xl bg-status-success/10 border border-status-success/30">
                  <h4 className="text-xs font-semibold text-status-success mb-2 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Informações disponíveis
                  </h4>
                  <ul className="space-y-1">
                    {requirements.filter(r => r.hasData).map((req) => (
                      <li key={req.field} className="flex items-center gap-2 text-xs text-status-success">
                        <span className="text-status-success">{getIcon(req.field)}</span>
                        {req.label}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <p className="text-xs text-lia-text-secondary">
                {hasEnoughData 
                  ? 'Você pode prosseguir, mas o parecer terá qualidade limitada.'
                  : 'Complete o perfil do candidato com as informações obrigatórias para gerar um parecer.'}
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="gap-2 sm:gap-2 flex-col sm:flex-row border-t border-lia-border-subtle bg-lia-bg-secondary p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button 
            variant="outline" 
            onClick={onClose}
            className="gap-2 bg-lia-bg-primary border border-lia-border-default hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg"
          >
            <X className="w-4 h-4" />
            {hasEnoughData ? 'Cancelar' : 'Entendi'}
          </Button>
          {hasEnoughData && onProceedAnyway && (
            <Button
              onClick={onProceedAnyway}
              className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              <AlertTriangle className="w-4 h-4" />
              Gerar mesmo assim
            </Button>
          )}
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export function validateCandidateDataForOpinion(candidate: Record<string, unknown>): {
  isValid: boolean
  canProceedWithWarning: boolean
  requirements: DataRequirement[]
} {
  const hasExperiences = (
    (Array.isArray(candidate.experiences) && candidate.experiences.length > 0) ||
    (Array.isArray(candidate.work_history) && candidate.work_history.length > 0) ||
    (Array.isArray(candidate.work_history) && candidate.work_history.length > 0)
  )
  
  const hasSkills = (
    (Array.isArray(candidate.skills) && candidate.skills.length > 0) ||
    (Array.isArray(candidate.expertise) && candidate.expertise.length > 0)
  )
  
  const hasSummary = !!(
    candidate.summary || 
    candidate.resume_text || 
    candidate.resumeText ||
    candidate.cv_text ||
    candidate.cvText ||
    candidate.headline
  )
  
  const hasEducation = (
    Array.isArray(candidate.education) && candidate.education.length > 0
  )
  
  const hasCurrentPosition = !!(
    candidate.current_title || 
    candidate.current_title || 
    candidate.position
  )
  
  const requirements: DataRequirement[] = [
    {
      field: 'experiences',
      label: 'Experiência profissional',
      hasData: hasExperiences,
      required: true,
      description: 'Pelo menos 1 experiência com cargo e empresa'
    },
    {
      field: 'summary',
      label: 'Resumo ou CV',
      hasData: hasSummary,
      required: true,
      description: 'Resumo profissional, headline ou texto do CV'
    },
    {
      field: 'skills',
      label: 'Habilidades técnicas',
      hasData: hasSkills,
      required: false,
      description: 'Lista de skills ou competências'
    },
    {
      field: 'education',
      label: 'Formação acadêmica',
      hasData: hasEducation,
      required: false,
      description: 'Informações sobre educação'
    },
    {
      field: 'currentPosition',
      label: 'Cargo atual',
      hasData: hasCurrentPosition,
      required: false,
      description: 'Título do cargo atual'
    }
  ]
  
  const requiredMissing = requirements.filter(r => r.required && !r.hasData)
  const optionalFilled = requirements.filter(r => !r.required && r.hasData).length
  
  const isValid = requiredMissing.length === 0
  const canProceedWithWarning = requiredMissing.length === 0 && optionalFilled < 2
  
  return {
    isValid,
    canProceedWithWarning,
    requirements
  }
}
