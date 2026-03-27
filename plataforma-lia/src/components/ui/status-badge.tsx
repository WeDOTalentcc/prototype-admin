'use client'

import * as React from 'react'
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  MessageCircle, 
  Calendar,
  Trophy,
  User,
  Linkedin,
  Globe,
  Mail,
  Phone,
  MessageSquare,
  Video,
  Building,
  Users,
  Target,
  Briefcase,
  Search,
  FileText,
  Star,
  AlertCircle,
  BrainCircuit,
  CalendarCheck
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { SUB_STATUSES, type SubStatus } from '@/lib/recruitment-stages'

/**
 * Badge Design Specification
 * 
 * Font: 9px
 * Icon: 8px (w-2 h-2)
 * Padding: 6px horizontal, 2px vertical (px-1.5 py-0.5)
 * Border Radius: 9999px (rounded-full)
 */

// Cores por etapa para badges Accent — escala cinza monocromática (Fase 2 — 2026-03-27)
// Antes: 17 pastéis coloridos únicos. Depois: gray scale hierárquico.
// Tom = progresso no funil (mais claro = início, mais escuro = final).
// Consistente com RECRUITMENT_STAGES.color em recruitment-stages.ts.
export const STAGE_PASTEL_COLORS: Record<string, string> = {
  sourcing: 'var(--gray-200)',
  screening: 'var(--gray-200)',
  long_list: 'var(--gray-300)',          // gray-300 equiv (entre gray-200 e gray-400)
  short_list: 'var(--gray-300)',
  interview_hr: 'var(--gray-400)',
  technical_test: 'var(--gray-400)',
  english_test: 'var(--gray-400)',
  interview_technical: 'var(--gray-500)', // gray-500 equiv
  interview_manager: 'var(--gray-500)',
  interview_manager2: 'var(--gray-500)',
  interview_final: 'var(--gray-600)',
  references: 'var(--gray-600)',
  offer: 'var(--gray-800)',
  hired: 'var(--status-success)',  // único verde semântico
  rejected: 'var(--gray-200)',     // faded
  offer_declined: 'var(--gray-200)',
  standby: 'var(--gray-300)',
}

// Dark mode — inversão da escala (claro vira escuro, escuro vira claro)
export const STAGE_PASTEL_COLORS_DARK: Record<string, string> = {
  sourcing: 'var(--gray-600)',
  screening: 'var(--gray-600)',
  long_list: 'var(--gray-600)',
  short_list: 'var(--gray-600)',
  interview_hr: 'var(--gray-500)',
  technical_test: 'var(--gray-500)',
  english_test: 'var(--gray-500)',
  interview_technical: 'var(--gray-400)',
  interview_manager: 'var(--gray-400)',
  interview_manager2: 'var(--gray-400)',
  interview_final: 'var(--gray-300)',
  references: 'var(--gray-300)',
  offer: 'var(--gray-200)',
  hired: 'var(--status-success)',
  rejected: 'var(--gray-600)',
  offer_declined: 'var(--gray-600)',
  standby: 'var(--gray-600)',
}

// Tipos de badge
export type BadgeVariant = 
  | 'standard'    // Padrão - neutro
  | 'dark'        // Escuro - completed/approved
  | 'accent'      // Accent - ação pendente (pastel + pulse)
  | 'outlined'    // Com borda - status intermediário
  | 'channel'     // Canal de comunicação
  | 'scheduled'   // Entrevista agendada
  | 'hired'       // Contratado/proposta aceita
  | 'rejected'    // Reprovado/desistência

// Props do componente
export interface StatusBadgeProps {
  /** ID do estágio atual */
  stageId: string
  /** Nome do sub-status (ex: 'screening_in_progress') */
  subStatus?: string
  /** Texto customizado (sobrescreve displayName do sub-status) */
  label?: string
  /** Variante forçada (sobrescreve lógica automática) */
  variant?: BadgeVariant
  /** Ícone customizado */
  icon?: React.ElementType
  /** Se deve mostrar animação pulse */
  pulse?: boolean
  /** Callback de clique */
  onClick?: () => void
  /** Classes adicionais */
  className?: string
  /** Título/tooltip */
  title?: string
}

/**
 * Deriva automaticamente o tipo de badge baseado nos metadados do sub-status.
 * 
 * Mapeamento:
 * - isWaiting → accent (com pulse animation)
 * - isApproval → dark (concluído/aprovado)
 * - isRejection → rejected (reprovado/desistência)
 * - scheduled/confirmed → scheduled (entrevista confirmada)
 * - in_progress/analyzing → outlined (em andamento)
 * 
 * NOTA: Override especial para stageId='hired' + isApproval retorna 'hired' 
 * ao invés de 'dark' para destacar visualmente contratações com ícone verde.
 */
function getBadgeVariant(subStatus: SubStatus | undefined, stageId: string): BadgeVariant {
  if (!subStatus) return 'standard'
  
  // Override: Hired stage com approved = usar variante 'hired' com ícone verde
  // Isso destaca visualmente candidatos contratados vs apenas aprovados
  if (stageId === 'hired' && subStatus.isApproval) {
    return 'hired'
  }
  
  // Rejection
  if (subStatus.isRejection) {
    return 'rejected'
  }
  
  // Waiting = accent com pulse
  if (subStatus.isWaiting) {
    return 'accent'
  }
  
  // Approval = escuro
  if (subStatus.isApproval) {
    return 'dark'
  }
  
  // Agendado (interview scheduled)
  if (subStatus.name.includes('scheduled') || subStatus.name.includes('confirmed')) {
    return 'scheduled'
  }
  
  // Em andamento/progresso = outlined
  if (subStatus.name.includes('in_progress') || subStatus.name.includes('analyzing') || 
      subStatus.name.includes('evaluating') || subStatus.name.includes('negotiating')) {
    return 'outlined'
  }
  
  // Default
  return 'standard'
}

// Função para obter ícone baseado no contexto
function getDefaultIcon(subStatus: SubStatus | undefined, variant: BadgeVariant): React.ElementType {
  if (!subStatus) return FileText
  
  // Por variante
  if (variant === 'accent') return Clock
  if (variant === 'hired') return Trophy
  if (variant === 'rejected') return XCircle
  if (variant === 'scheduled') return CalendarCheck
  
  // Por nome do sub-status
  if (subStatus.name.includes('completed') || subStatus.name.includes('approved')) return CheckCircle
  if (subStatus.name.includes('in_progress') || subStatus.name.includes('andamento')) return MessageCircle
  if (subStatus.name.includes('interview') || subStatus.name.includes('entrevista')) return Users
  if (subStatus.name.includes('screening') || subStatus.name.includes('triagem')) return BrainCircuit
  if (subStatus.name.includes('test') || subStatus.name.includes('teste')) return FileText
  if (subStatus.name.includes('offer') || subStatus.name.includes('proposta')) return Star
  if (subStatus.name.includes('document') || subStatus.name.includes('doc')) return FileText
  
  return FileText
}

// Estilos por variante — tokens CSS vars (Fase 2 — 2026-03-27)
// Antes: 90 hex hardcoded. Depois: CSS vars de design-tokens.css.
// Valores são CSS strings pois são injetados em custom properties via style={}.
const variantStyles: Record<BadgeVariant, {
  bg: string
  text: string
  icon: string
  border?: string
  fontWeight: string
  darkBg?: string
  darkText?: string
  darkIcon?: string
  darkBorder?: string
}> = {
  standard: {
    bg: 'var(--gray-50)',
    text: 'var(--gray-600)',
    icon: 'var(--gray-400)',
    fontWeight: '500',
    darkBg: 'var(--gray-600)',
    darkText: 'var(--gray-200)',
    darkIcon: 'var(--gray-400)',
  },
  dark: {
    bg: 'var(--gray-950)',
    text: '#FFFFFF',
    icon: '#FFFFFF',
    fontWeight: '700',
    darkBg: 'var(--gray-50)',
    darkText: 'var(--gray-950)',
    darkIcon: 'var(--gray-950)',
  },
  accent: {
    bg: '', // preenchido dinamicamente com STAGE_PASTEL_COLORS[stageId]
    text: 'var(--gray-950)',
    icon: 'var(--gray-800)',
    fontWeight: '600',
    darkBg: 'var(--gray-600)',
    darkText: 'var(--gray-200)',
    darkIcon: 'var(--gray-200)',
  },
  outlined: {
    bg: 'var(--gray-50)',
    text: 'var(--gray-600)',
    icon: 'var(--gray-600)',
    border: 'var(--gray-200)',
    fontWeight: '400',
    darkBg: 'var(--gray-800)',
    darkText: 'var(--gray-200)',
    darkIcon: 'var(--gray-200)',
    darkBorder: 'var(--gray-600)',
  },
  channel: {
    bg: 'var(--gray-50)',
    text: 'var(--gray-800)',
    icon: 'var(--gray-800)',
    border: 'var(--gray-200)',
    fontWeight: '400',
    darkBg: 'var(--gray-600)',
    darkText: 'var(--gray-200)',
    darkIcon: 'var(--gray-200)',
    darkBorder: 'var(--gray-400)',
  },
  scheduled: {
    bg: 'var(--gray-800)',
    text: '#FFFFFF',
    icon: 'var(--wedo-cyan)',   // ícone de calendário: único uso cyan não-LIA justificado
    border: 'var(--gray-600)', // (scheduled = ação pendente de alta relevância)
    fontWeight: '600',
    darkBg: 'var(--gray-200)',
    darkText: 'var(--gray-950)',
    darkIcon: 'var(--wedo-cyan-dark)',
  },
  hired: {
    bg: 'var(--gray-950)',
    text: '#FFFFFF',
    icon: 'var(--status-success)',   // Trophy verde = único indicador de contratação
    fontWeight: '700',
    darkBg: 'var(--gray-50)',
    darkText: 'var(--gray-950)',
    darkIcon: 'var(--status-success)',
  },
  rejected: {
    bg: 'var(--gray-50)',
    text: 'var(--gray-600)',
    icon: 'var(--gray-400)',
    border: 'var(--gray-200)',
    fontWeight: '500',
    darkBg: 'var(--gray-600)',
    darkText: 'var(--gray-200)',
    darkIcon: 'var(--gray-400)',
    darkBorder: 'var(--gray-400)',
  },
}

export function StatusBadge({
  stageId,
  subStatus,
  label,
  variant: forcedVariant,
  icon: CustomIcon,
  pulse: forcedPulse,
  onClick,
  className,
  title,
}: StatusBadgeProps) {
  // Buscar sub-status nos dados
  const subStatusData = subStatus 
    ? SUB_STATUSES[stageId]?.find(s => s.name === subStatus)
    : undefined
  
  // Determinar variante
  const variant = forcedVariant || getBadgeVariant(subStatusData, stageId)
  
  // Determinar se deve pulsar
  const shouldPulse = forcedPulse ?? (variant === 'accent' && subStatusData?.isWaiting)
  
  // Obter estilos
  const styles = variantStyles[variant]
  
  // Para accent, usar cor pastel da etapa (light e dark)
  const bgColor = variant === 'accent' 
    ? STAGE_PASTEL_COLORS[stageId] || 'var(--gray-200)'
    : styles.bg
  const bgColorDark = variant === 'accent'
    ? STAGE_PASTEL_COLORS_DARK[stageId] || 'var(--gray-600)'
    : styles.darkBg || styles.bg
  
  // Obter ícone
  const Icon = CustomIcon || getDefaultIcon(subStatusData, variant)
  
  // Texto a exibir
  const displayText = label || subStatusData?.displayName || subStatus || ''
  
  // Tooltip
  const tooltipText = title || (
    subStatusData?.isWaiting && subStatusData?.waitingFor
      ? `Aguardando: ${
          subStatusData.waitingFor === 'candidate' ? 'Candidato' :
          subStatusData.waitingFor === 'interviewer' ? 'Entrevistador' :
          subStatusData.waitingFor === 'manager' ? 'Gestor' :
          subStatusData.waitingFor === 'hr' ? 'RH' :
          subStatusData.waitingFor === 'system' ? 'Sistema' :
          subStatusData.waitingFor
        }`
      : undefined
  )

  // CSS custom properties for dark mode support
  const cssVars = {
    '--badge-bg': bgColor,
    '--badge-bg-dark': bgColorDark,
    '--badge-text': styles.text,
    '--badge-text-dark': styles.darkText || styles.text,
    '--badge-icon': styles.icon,
    '--badge-icon-dark': styles.darkIcon || styles.icon,
    '--badge-border': styles.border || 'transparent',
    '--badge-border-dark': styles.darkBorder || styles.border || 'transparent',
  } as React.CSSProperties

  return (
    <div
      className={cn(
        'inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full',
        'bg-[var(--badge-bg)] dark:bg-[var(--badge-bg-dark)]',
        'border border-[var(--badge-border)] dark:border-[var(--badge-border-dark)]',
        shouldPulse && 'motion-safe:animate-pulse',
        onClick && 'cursor-pointer hover:opacity-80',
        className
      )}
      style={{
        ...cssVars,
        fontFamily: "'Open Sans', sans-serif",
      }}
      onClick={onClick}
      title={tooltipText}
    >
      <Icon 
        className="w-2 h-2 flex-shrink-0 text-[var(--badge-icon)] dark:text-[var(--badge-icon-dark)]" 
      />
      <span 
        className="text-micro text-[var(--badge-text)] dark:text-[var(--badge-text-dark)]"
        style={{ 
          fontWeight: styles.fontWeight,
        }}
      >
        {displayText}
      </span>
    </div>
  )
}

// Componente para badge de canal de comunicação
export interface ChannelBadgeProps {
  channel: 'whatsapp' | 'email' | 'phone' | 'linkedin' | 'teams' | 'presencial' | string
  className?: string
}

const channelIcons: Record<string, React.ElementType> = {
  whatsapp: MessageSquare,
  email: Mail,
  phone: Phone,
  linkedin: Linkedin,
  teams: Video,
  presencial: Building,
}

const channelLabels: Record<string, string> = {
  whatsapp: 'WhatsApp',
  email: 'Email',
  phone: 'Telefone',
  linkedin: 'LinkedIn',
  teams: 'Teams',
  presencial: 'Presencial',
}

export function ChannelBadge({ channel, className }: ChannelBadgeProps) {
  const Icon = channelIcons[channel.toLowerCase()] || MessageSquare
  const label = channelLabels[channel.toLowerCase()] || channel
  
  return (
    <StatusBadge
      stageId=""
      variant="channel"
      icon={Icon}
      label={label}
      className={className}
    />
  )
}

// Componente para badge de origem do candidato
export interface SourceBadgeProps {
  source: 'linkedin' | 'indeed' | 'google_jobs' | 'website' | 'referral' | 'headhunting' | 'internal' | 'lia_database' | 'recruiter' | string
  isApplication?: boolean
  className?: string
}

const sourceIcons: Record<string, React.ElementType> = {
  linkedin: Linkedin,
  indeed: Briefcase,
  google_jobs: Search,
  website: Globe,
  referral: Users,
  headhunting: Target,
  internal: Building,
  lia_database: BrainCircuit,
  recruiter: User,
}

const sourceLabels: Record<string, string> = {
  linkedin: 'LinkedIn',
  indeed: 'Indeed',
  google_jobs: 'Google Jobs',
  website: 'Site',
  referral: 'Indicação',
  headhunting: 'Hunting',
  internal: 'Interno',
  lia_database: 'Banco LIA',
  recruiter: 'Manual',
}

export function SourceBadge({ source, isApplication, className }: SourceBadgeProps) {
  const Icon = sourceIcons[source.toLowerCase()] || User
  const label = isApplication 
    ? `Inscrito ${sourceLabels[source.toLowerCase()] || source}`
    : sourceLabels[source.toLowerCase()] || source
  
  return (
    <div
      className={cn(
        'inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full',
        'bg-gray-50 dark:bg-gray-700',
        'border border-gray-200 dark:border-gray-600',
        className
      )}
      style={{ fontFamily: "'Open Sans', sans-serif" }}
      title={isApplication ? `Inscrito via ${sourceLabels[source.toLowerCase()] || source}` : `Origem: ${sourceLabels[source.toLowerCase()] || source}`}
    >
      <Icon className="w-2 h-2 flex-shrink-0 text-gray-500 dark:text-gray-400" />
      <span className="text-micro text-gray-600 dark:text-gray-300 font-medium">
        {label}
      </span>
    </div>
  )
}

// Componente para badge de warning (dias parado)
export interface WarningBadgeProps {
  days?: number
  message?: string
  className?: string
}

export function WarningBadge({ days, message, className }: WarningBadgeProps) {
  const displayText = message || (days ? `${days} dias parado` : 'Atenção')
  
  return (
    <div
      className={cn(
        'inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full',
        'bg-gray-100 dark:bg-gray-600',
        'border border-gray-300 dark:border-gray-500',
        className
      )}
      style={{ fontFamily: "'Open Sans', sans-serif" }}
    >
      <AlertCircle className="w-2 h-2 flex-shrink-0 text-gray-500 dark:text-gray-300" />
      <span className="text-micro text-gray-600 dark:text-gray-200 font-semibold">
        {displayText}
      </span>
    </div>
  )
}

// Componente para badge de data/hora de entrevista
export interface DateTimeBadgeProps {
  date: Date | string
  showTime?: boolean
  className?: string
}

export function DateTimeBadge({ date, showTime = true, className }: DateTimeBadgeProps) {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  
  const formatDate = (d: Date) => {
    const day = d.getDate().toString().padStart(2, '0')
    const month = (d.getMonth() + 1).toString().padStart(2, '0')
    return `${day}/${month}`
  }
  
  const formatTime = (d: Date) => {
    const hours = d.getHours().toString().padStart(2, '0')
    const minutes = d.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  }
  
  const displayText = showTime 
    ? `${formatDate(dateObj)} às ${formatTime(dateObj)}`
    : formatDate(dateObj)
  
  return (
    <StatusBadge
      stageId=""
      variant="standard"
      icon={Calendar}
      label={displayText}
      className={className}
    />
  )
}

export type CandidateOrigin = 'web' | 'whatsapp' | 'sourcing' | 'ats'

export interface OriginBadgeProps {
  origin: CandidateOrigin | string
  className?: string
}

const originConfig: Record<string, { label: string; bg: string; border: string; text: string; icon: React.ElementType }> = {
  web: { label: 'Web', bg: 'bg-blue-50 dark:bg-blue-900/30', border: 'border-blue-200 dark:border-blue-700', text: 'text-blue-700 dark:text-blue-300', icon: Globe },
  whatsapp: { label: 'WhatsApp', bg: 'bg-green-50 dark:bg-green-900/30', border: 'border-green-200 dark:border-green-700', text: 'text-green-700 dark:text-green-300', icon: MessageCircle },
  sourcing: { label: 'Busca', bg: 'bg-gray-50 dark:bg-gray-700', border: 'border-gray-200 dark:border-gray-600', text: 'text-gray-700 dark:text-gray-300', icon: Search },
  ats: { label: 'ATS', bg: 'bg-purple-50 dark:bg-purple-900/30', border: 'border-purple-200 dark:border-purple-700', text: 'text-purple-700 dark:text-purple-300', icon: Briefcase },
}

export function OriginBadge({ origin, className }: OriginBadgeProps) {
  const config = originConfig[origin.toLowerCase()] || originConfig.sourcing
  const Icon = config.icon

  return (
    <div
      className={cn(
        'inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full',
        config.bg,
        `border ${config.border}`,
        className
      )}
      style={{ fontFamily: "'Open Sans', sans-serif" }}
      title={`Origem: ${config.label}`}
    >
      <Icon className={cn('w-2 h-2 flex-shrink-0', config.text)} />
      <span className={cn('text-micro font-medium', config.text)}>
        {config.label}
      </span>
    </div>
  )
}

export interface AwaitingBadgeProps {
  className?: string
}

export function AwaitingBadge({ className }: AwaitingBadgeProps) {
  return (
    <div
      className={cn(
        'inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full',
        'bg-amber-50 dark:bg-amber-900/30',
        'border border-amber-200 dark:border-amber-700',
        className
      )}
      style={{ fontFamily: "'Open Sans', sans-serif" }}
      title="Aguardando na fila de saturação"
    >
      <Clock className="w-2 h-2 flex-shrink-0 text-amber-600 dark:text-amber-400" />
      <span className="text-micro font-medium text-amber-700 dark:text-amber-300">
        Aguardando
      </span>
    </div>
  )
}

export default StatusBadge
