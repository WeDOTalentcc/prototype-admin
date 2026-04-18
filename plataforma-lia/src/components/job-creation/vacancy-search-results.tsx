"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { cn } from"@/lib/utils"
import { 
  Loader2,
  CheckCircle2,
  Clock,
  User,
  Calendar,
  DollarSign,
  MapPin,
  Briefcase,
  Building2
} from"lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"

export interface VacancySummary {
  id: string
  title: string
  department: string
  manager: string
  hired_candidate?: string
  date_closed: string
  salary_range: { min: number; max: number }
  work_model: string
  status: 'hired' | 'cancelled'
}

export interface VacancySearchResultsProps {
  vacancies: VacancySummary[]
  onSelect: (vacancy: VacancySummary) => void
  isLoading?: boolean
}

const NUMBER_EMOJIS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

const STATUS_CONFIG: Record<'hired' | 'cancelled', {
  icon: React.ElementType
  label: string
  className: string
  bgClassName: string
  borderClassName: string
}> = {
  hired: {
    icon: CheckCircle2,
    label: '✅ Contratado',
    className: 'text-status-success',
    bgClassName: 'bg-status-success/10 dark:bg-status-success/30',
    borderClassName: 'border-status-success/30 dark:border-status-success/30'
  },
  cancelled: {
    icon: Clock,
    label: '⏳ Cancelada',
    className: 'text-status-warning',
    bgClassName: 'bg-status-warning/10 dark:bg-status-warning/30',
    borderClassName: 'border-status-warning/30 dark:border-status-warning/30'
  }
}

const WORK_MODEL_CONFIG: Record<string, { label: string; className: string }> = {
  'remote': { label: 'Remoto', className: '-dark border-wedo-cyan/30 dark:border-wedo-cyan/30' },
  'hybrid': { label: 'Híbrido', className: ' border-wedo-purple/30 dark:text-wedo-purple dark:border-wedo-purple/30' },
  'onsite': { label: 'Presencial', className: 'bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle' },
  'presencial': { label: 'Presencial', className: 'bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle' },
  'remoto': { label: 'Remoto', className: '-dark border-wedo-cyan/30 dark:border-wedo-cyan/30' },
  'híbrido': { label: 'Híbrido', className: ' border-wedo-purple/30 dark:text-wedo-purple dark:border-wedo-purple/30' },
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

function VacancyCard({ 
  vacancy, 
  index, 
  onClick 
}: { 
  vacancy: VacancySummary
  index: number
  onClick: () => void 
}) {
  const statusConfig = STATUS_CONFIG[vacancy.status]
  const workModelConfig = WORK_MODEL_CONFIG[vacancy.work_model.toLowerCase()] || WORK_MODEL_CONFIG['onsite']

  return (
    <div 
      className="p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle hover:border-lia-btn-primary-bg hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none cursor-pointer group"
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <span className="text-lg flex-shrink-0">{NUMBER_EMOJIS[index] || `${index + 1}.`}</span>
        
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-lia-text-primary dark:text-white truncate group-hover:text-lia-text-primary dark:group-hover:text-lia-text-inverse transition-colors motion-reduce:transition-none">
              {vacancy.title}
            </h4>
            <Chip 
              variant="neutral" 
              className={cn("text-micro h-5 px-1.5 border flex-shrink-0", statusConfig.bgClassName, statusConfig.borderClassName, statusConfig.className)}
            >
              {statusConfig.label}
            </Chip>
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-xs text-lia-text-tertiary">
            <div className="flex items-center gap-1.5">
              <Building2 className="h-3 w-3 text-lia-text-secondary" />
              <span className="truncate">{vacancy.department}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <User className="h-3 w-3 text-lia-text-secondary" />
              <span className="truncate">{vacancy.manager}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Calendar className="h-3 w-3 text-lia-text-secondary" />
              <span>{formatDate(vacancy.date_closed)}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <DollarSign className="h-3 w-3 text-lia-text-secondary" />
              <span>{formatCurrency(vacancy.salary_range.min)} - {formatCurrency(vacancy.salary_range.max)}</span>
            </div>
          </div>

          <div className="flex items-center justify-between gap-2">
            <Chip 
              variant="neutral" 
              className={cn("text-micro h-4 px-1.5 border", workModelConfig.className)}
            >
              {workModelConfig.label}
            </Chip>
            {vacancy.hired_candidate && vacancy.status === 'hired' && (
              <span className="text-micro text-status-success flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                {vacancy.hired_candidate}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function VacancySearchResults({
  vacancies,
  onSelect,
  isLoading = false
}: VacancySearchResultsProps) {
  if (isLoading) {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-lia-border-default">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-xl rounded-tl-sm bg-lia-bg-primary border border-lia-border-subtle p-4" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            <span className="text-sm text-lia-text-tertiary" aria-live="polite" aria-atomic="true">Buscando vagas anteriores...</span>
          </div>
        </div>
      </div>
    )
  }

  if (vacancies.length === 0) {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-lia-border-default">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-xl rounded-tl-sm bg-lia-bg-primary border border-lia-border-subtle p-4">
          <p className="text-sm text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
            Não encontrei vagas anteriores com esses critérios. Podemos criar uma vaga do zero! Me diga o cargo e vou te ajudar.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3 max-w-[90%]">
      <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-lia-border-default">
        <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
        <AvatarFallback className="bg-gradient-to-br from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark text-white text-xs font-medium">
          LIA
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-3">
        <div className="rounded-xl rounded-tl-sm bg-lia-bg-primary border border-lia-border-subtle p-4 space-y-4">
          <p className="text-xs text-lia-text-tertiary">
            Encontrei <span className="font-semibold text-lia-text-primary">{vacancies.length}</span> vaga{vacancies.length > 1 ? 's' : ''} que pode{vacancies.length > 1 ? 'm' : ''} servir como base:
          </p>

          <div className="space-y-2 max-h-content-lg overflow-y-auto pr-1">
            {vacancies.map((vacancy, index) => (
              <VacancyCard 
                key={vacancy.id} 
                vacancy={vacancy} 
                index={index}
                onClick={() => onSelect(vacancy)}
              />
            ))}
          </div>

          <div className="pt-3 border-t border-lia-border-subtle">
            <p className="text-xs text-lia-text-tertiary italic" aria-live="polite" aria-atomic="true">
              Digite o número (ex:"1" ou"2") ou parte do título para selecionar uma vaga. 
              Se preferir criar do zero, digite"criar nova".
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VacancySearchResults
