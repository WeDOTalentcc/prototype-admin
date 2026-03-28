import { useMemo } from 'react'
import { useWizardContext } from '../WizardContext'
import type { WizardStage } from '../types'

interface StageValidation {
  isValid: boolean
  errors: string[]
  warnings: string[]
  completionPercentage: number
}

export function useStageValidation(stage?: WizardStage): StageValidation {
  const {
    currentStage,
    detectedCriteria,
    basicInfoFields,
    technicalSkills,
    behavioralCompetencies,
    salaryInfo,
    wsiCandidates
  } = useWizardContext()
  
  const targetStage = stage || currentStage
  
  return useMemo(() => {
    const errors: string[] = []
    const warnings: string[] = []
    let completionPercentage = 0
    
    switch (targetStage) {
      case 'input-evaluation': {
        if (!detectedCriteria.cargo) {
          errors.push('Cargo não detectado')
        }
        const detected = [
          detectedCriteria.cargo,
          detectedCriteria.gestorArea,
          detectedCriteria.responsabilidades.length > 0,
          detectedCriteria.competenciasTecnicas.length >= 3,
          detectedCriteria.competenciasComportamentais.length >= 3,
          detectedCriteria.salario,
          detectedCriteria.isAffirmative !== null
        ].filter(Boolean).length
        completionPercentage = (detected / 7) * 100
        break
      }
      
      case 'job-description': {
        if (!basicInfoFields.cargo) errors.push('Cargo é obrigatório')
        if (!basicInfoFields.area) warnings.push('Área não definida')
        if (!basicInfoFields.localidade) warnings.push('Localidade não definida')
        if (!basicInfoFields.modeloTrabalho) warnings.push('Modelo de trabalho não definido')
        
        const fields = [
          basicInfoFields.cargo,
          basicInfoFields.area,
          basicInfoFields.gestor,
          basicInfoFields.localidade,
          basicInfoFields.modeloTrabalho,
          basicInfoFields.tipoContrato
        ].filter(f => f && f.length > 0).length
        completionPercentage = (fields / 6) * 100
        break
      }
      
      case 'competencies': {
        if (technicalSkills.length < 3) {
          errors.push(`Mínimo 3 competências técnicas (atual: ${technicalSkills.length})`)
        }
        const enabledBehavioral = behavioralCompetencies.filter(c => c.enabled).length
        if (enabledBehavioral < 3) {
          errors.push(`Mínimo 3 competências comportamentais (atual: ${enabledBehavioral})`)
        }
        const minRequired = 6 // 3 tech + 3 behavioral
        const current = technicalSkills.length + enabledBehavioral
        completionPercentage = Math.min(100, (current / minRequired) * 100)
        break
      }
      
      case 'salary': {
        if (!salaryInfo.minSalary || !salaryInfo.maxSalary) {
          warnings.push('Faixa salarial não definida')
        }
        const enabledBenefits = salaryInfo.benefits.filter(b => b.enabled).length
        if (enabledBenefits === 0) {
          warnings.push('Nenhum benefício selecionado')
        }
        const fields = [
          salaryInfo.minSalary,
          salaryInfo.maxSalary,
          enabledBenefits > 0
        ].filter(Boolean).length
        completionPercentage = (fields / 3) * 100
        break
      }
      
      case 'wsi-questions': {
        const selectedCount = wsiCandidates.filter(q => q.selected).length
        if (selectedCount < 3) {
          errors.push(`Selecione pelo menos 3 perguntas (atual: ${selectedCount})`)
        }
        if (selectedCount < 5) {
          warnings.push(`Recomendado: 5 perguntas (atual: ${selectedCount})`)
        }
        completionPercentage = (Math.min(selectedCount, 5) / 5) * 100
        break
      }
      
      case 'review-publish': {
        // Validate all previous stages
        if (!basicInfoFields.cargo) errors.push('Cargo obrigatório')
        if (technicalSkills.length < 3) errors.push('Competências técnicas incompletas')
        completionPercentage = errors.length === 0 ? 100 : 50
        break
      }
      
      case 'search-calibration': {
        completionPercentage = 100 // No validation needed
        break
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      completionPercentage
    }
  }, [
    targetStage, detectedCriteria, basicInfoFields,
    technicalSkills, behavioralCompetencies, salaryInfo, wsiCandidates
  ])
}

export function useAllStagesValidation() {
  const stages: WizardStage[] = [
    'input-evaluation', 'job-description', 'competencies',
    'salary', 'wsi-questions', 'review-publish', 'search-calibration'
  ]
  
  const { detectedCriteria, basicInfoFields, technicalSkills, behavioralCompetencies, salaryInfo, wsiCandidates } = useWizardContext()
  
  return useMemo(() => {
    const results: Record<WizardStage, { isValid: boolean; hasWarnings: boolean }> = {} as any
    
    results['input-evaluation'] = {
      isValid: detectedCriteria.cargo !== null,
      hasWarnings: detectedCriteria.competenciasTecnicas.length < 3
    }
    
    results['job-description'] = {
      isValid: basicInfoFields.cargo.length > 0,
      hasWarnings: !basicInfoFields.area || !basicInfoFields.localidade
    }
    
    results['competencies'] = {
      isValid: technicalSkills.length >= 3 && behavioralCompetencies.filter(c => c.enabled).length >= 3,
      hasWarnings: false
    }
    
    results['salary'] = {
      isValid: true,
      hasWarnings: !salaryInfo.minSalary || !salaryInfo.maxSalary
    }
    
    results['wsi-questions'] = {
      isValid: wsiCandidates.filter(q => q.selected).length >= 3,
      hasWarnings: wsiCandidates.filter(q => q.selected).length < 5
    }
    
    results['review-publish'] = {
      isValid: true,
      hasWarnings: false
    }
    
    results['search-calibration'] = {
      isValid: true,
      hasWarnings: false
    }
    
    return results
  }, [detectedCriteria, basicInfoFields, technicalSkills, behavioralCompetencies, salaryInfo, wsiCandidates])
}
