"use client"

import { textStyles } from '@/lib/design-tokens'
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Code, Linkedin, Building, Users, Globe,
  Briefcase, UserPlus
} from"lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from"@/components/ui/tooltip"

interface ProfileExperienceCardsProps {
  candidate: Record<string, unknown>
}

function ProfileIndicatorBadges({ candidate }: { candidate: Record<string, unknown> }) {
  const isOpenToWork = candidate.is_opentowork ?? candidate.is_open_to_work ?? candidate.isOpenToWork
  const isTopUniversity = candidate.is_top_universities ?? candidate.top_universities ?? candidate.isTopUniversities
  const isDecisionMaker = candidate.is_decision_maker ?? candidate.isDecisionMaker
  const isBlacklisted = candidate.is_blacklisted ?? candidate.blacklist_status ?? candidate.isBlacklisted
  const blacklistReason = candidate.blacklist_reason ?? candidate.motivo_lista_negra ?? candidate.blacklistReason

  const hasAnyIndicator = isOpenToWork === true || isTopUniversity === true || isDecisionMaker === true || isBlacklisted === true

  if (!hasAnyIndicator) return null

  return (
    <div className="flex flex-wrap gap-1.5 mb-2">
      {isOpenToWork === true && (
        <Chip variant="success" className="text-micro px-1.5 py-0 h-4 flex items-center dark:bg-status-success/20 flex items-center gap-1">
          <Globe className="w-3 h-3 text-status-success" />
          Open to Work
        </Chip>
      )}
      {isTopUniversity === true && (
        <Chip variant="neutral" className="text-micro px-1.5 py-0 h-4 flex items-center border-wedo-purple/30 flex items-center gap-1">
          🎓 Top University
        </Chip>
      )}
      {isDecisionMaker === true && (
        <Chip variant="neutral" className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle flex items-center gap-1">
          👔 Decision Maker
        </Chip>
      )}
      {isBlacklisted === true && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Chip variant="danger" className="text-micro px-1.5 py-0 h-4 flex items-center gap-1 cursor-help">
              ⚠️ LCNU
            </Chip>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="text-xs max-w-xs">
            <p className="font-medium mb-1">Lista de Candidatos Não Utilizáveis</p>
            {!!blacklistReason && <p>{String(blacklistReason)}</p>}
          </TooltipContent>
        </Tooltip>
      )}
    </div>
  )
}

function ProfileLinkedInCard({ candidate }: { candidate: Record<string, unknown> }) {
  const headline = candidate.headline ?? candidate.linkedinHeadline
  const estimatedAge = candidate.estimated_age ?? candidate.estimatedAge ?? candidate.age
  const followersCount = candidate.linkedin_followers_count ?? candidate.followers_count ?? candidate.linkedinFollowersCount
  const connectionsCount = candidate.linkedin_connections_count ?? candidate.connections_count ?? candidate.linkedinConnectionsCount

  const hasLinkedInData = headline || estimatedAge || followersCount || connectionsCount

  if (!hasLinkedInData) return null

  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <Linkedin className="w-3.5 h-3.5 text-lia-text-secondary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Perfil LinkedIn
          </CardTitle>
          <Globe className="w-3 h-3 text-lia-text-secondary" />
        </div>
      </CardHeader>
      <CardContent className="p-2.5 space-y-2">
        {!!headline && (
          <p className="text-xs text-lia-text-primary leading-relaxed">
            {String(headline)}
          </p>
        )}
        
        <div className="flex items-center gap-3 flex-wrap">
          {!!estimatedAge && (
            <div className="flex items-center gap-1">
              <span className={textStyles.caption}>Idade estimada:</span>
              <span className={`${textStyles.bodySmall} font-medium`}>{String(estimatedAge)} anos</span>
            </div>
          )}
          {followersCount !== undefined && followersCount !== null && (
            <div className="flex items-center gap-1">
              <Users className="w-3 h-3 text-lia-text-muted" />
              <span className={`${textStyles.bodySmall} font-medium`}>{(followersCount as number).toLocaleString('pt-BR')}</span>
              <span className={textStyles.caption}>seguidores</span>
            </div>
          )}
          {connectionsCount !== undefined && connectionsCount !== null && (
            <div className="flex items-center gap-1">
              <UserPlus className="w-3 h-3 text-lia-text-muted" />
              <span className={`${textStyles.bodySmall} font-medium`}>{(connectionsCount as number) >= 500 ? '500+' : String(connectionsCount)}</span>
              <span className={textStyles.caption}>conexões</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function formatDate(dateStr: string) {
  if (!dateStr || dateStr === 'Atual') return dateStr
  try {
    return new Date(dateStr).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })
  } catch {
    return dateStr
  }
}

function ProfileWorkExperienceCard({ candidate }: { candidate: Record<string, unknown> }) {
  const hasWorkHistory = (((candidate.workHistory as Record<string, unknown>[])?.length > 0) || ((candidate.work_history as Record<string, unknown>[])?.length > 0) || ((candidate.experiences as Record<string, unknown>[])?.length > 0) || ((candidate.additional_data as Record<string, unknown>)?.work_history as Record<string, unknown>[])?.length > 0 || ((candidate.additional_data as Record<string, unknown>)?.experiences as Record<string, unknown>[])?.length > 0)

  const workEntries = (candidate.workHistory || candidate.work_history || candidate.experiences || (candidate.additional_data as Record<string, unknown>)?.work_history || (candidate.additional_data as Record<string, unknown>)?.experiences || []) as Record<string, unknown>[]

  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <Briefcase className="w-3.5 h-3.5 text-lia-text-primary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Experiência Profissional
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-2.5 space-y-2.5">
        {hasWorkHistory ? (
          <div className="space-y-2.5">
            {workEntries.map((exp: Record<string, unknown>, index: number) => {
              const title = (exp.title || exp.position || exp.role || '') as string
              const company = (exp.company || exp.company_name || exp.organization || '') as string
              const location = (exp.location || exp.city || '') as string
              const startDate = (exp.start_date || exp.startDate || '') as string
              const endDate = (exp.end_date || exp.endDate || (exp.current ? 'Atual' : '')) as string
              const description = exp.description || exp.responsibilities || ''
              const descriptionList = Array.isArray(description) ? description as string[] : (description ? [description as string] : [])
              
              const industries = exp.industries || exp.industry || exp.segment || exp.segmento || []
              const industriesList = Array.isArray(industries) ? industries as string[] : (industries ? [industries as string] : [])
              const technologies = exp.technologies || exp.tech_stack || exp.skills || []
              const technologiesList = Array.isArray(technologies) ? technologies as string[] : []
              const companySize = (exp.company_size || exp.company_size_range || exp.porte || null) as string | null
              const isStartup = exp.is_startup || exp.startup
              
              let durationYears = (exp.duration_years as number | null) || null
              if (!durationYears && startDate) {
                try {
                  const start = new Date(startDate)
                  const end = endDate && endDate !== 'Atual' ? new Date(endDate) : new Date()
                  const diffMs = end.getTime() - start.getTime()
                  durationYears = Math.round((diffMs / (1000 * 60 * 60 * 24 * 365)) * 10) / 10
                } catch { /* ignore */ }
              }
              
              return (
                <div key={`${index}-${company}`} className={`border-l-2 ${index === 0 ? 'border-lia-border-medium' : 'border-lia-border-default'} pl-3`}>
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div>
                      <h5 className="text-xs font-medium text-lia-text-primary">{title || 'Cargo não informado'}</h5>
                      <p className="text-xs text-lia-text-secondary">
                        {company || 'Empresa não informada'}
                        {location && ` • ${location}`}
                        {durationYears && durationYears > 0 && <span className="lia-text-secondary ml-1">({durationYears.toFixed(1)} anos)</span>}
                      </p>
                    </div>
                    {(startDate || endDate) && (
                      <span className="text-micro text-lia-text-tertiary whitespace-nowrap">
                        {formatDate(startDate)}{startDate && endDate ? ' - ' : ''}{formatDate(endDate)}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {industriesList.slice(0, 2).map((ind: string) => (
<span key={ind} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
                        <Building className="w-2.5 h-2.5 mr-0.5" />
                        {ind}
                      </span>
                    ))}
                    {!!isStartup && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium  border border-status-success/30">
                        🚀 Startup
                      </span>
                    )}
                    {!!companySize && (
                      <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-micro bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle">
                        <Users className="w-2.5 h-2.5" />
                        {companySize}
                      </span>
                    )}
                  </div>

                  {technologiesList.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      <span className="text-micro text-lia-text-secondary flex items-center gap-0.5">
                        <Code className="w-2.5 h-2.5" />
                        Stack:
                      </span>
                      {technologiesList.slice(0, 6).map((tech: string) => (
                        <span key={tech} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-primary">
                          {tech}
                        </span>
                      ))}
                      {technologiesList.length > 6 && (
                        <span className="text-micro text-lia-text-muted">+{technologiesList.length - 6}</span>
                      )}
                    </div>
                  )}
                  
                  {descriptionList.length > 0 && (
                    <p className="text-xs text-lia-text-secondary mt-1">{descriptionList[0]}</p>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <p className={`${textStyles.description} italic`}>Não informado</p>
        )}
      </CardContent>
    </Card>
  )
}

export function ProfileExperienceCards({ candidate }: ProfileExperienceCardsProps) {
  return (
    <>
      <ProfileIndicatorBadges candidate={candidate} />
      <ProfileLinkedInCard candidate={candidate} />
      <ProfileWorkExperienceCard candidate={candidate} />
    </>
  )
}
