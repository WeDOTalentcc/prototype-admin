"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { Copy } from"lucide-react"
import { textStyles, badgeStyles } from"@/lib/design-tokens"
import type { KanbanCandidate, QueryInsight } from"./KanbanTableCellRenderer.types"
import { useTranslations } from "next-intl"

export function renderPearchCell(
  candidate: KanbanCandidate,
  columnId: string,
  t: (key: string, params?: Record<string, unknown>) => string
): React.ReactNode | undefined {
  switch (columnId) {
    case 'is_open_to_work': {
      const isOpenToWork = candidate.is_opentowork || candidate.is_open_to_work
      return isOpenToWork ? (
        <Chip density="relaxed" variant="neutral" muted >Open to Work</Chip>
      ) : <span className="text-xs text-lia-text-muted">—</span>
    }

    case 'is_decision_maker':
      return candidate.is_decision_maker ? (
        <Chip density="relaxed" variant="neutral" muted >Decision Maker</Chip>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'is_top_universities':
      return candidate.is_top_universities ? (
        <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary">Top University</Chip>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'is_hiring':
      return candidate.is_hiring ? (
        <Chip density="relaxed" variant="neutral" muted >{t('pearchHiring')}</Chip>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'headline':
      return <span className="text-xs text-lia-text-primary truncate">{(candidate.headline as string | undefined) || ''}</span>

    case 'expertise': {
      const expertiseArray = candidate.expertise
      return <span className="text-xs text-lia-text-primary truncate">{Array.isArray(expertiseArray) ? expertiseArray.join(', ') : (expertiseArray || '')}</span>
    }

    case 'linkedin_followers_count':
      return candidate.linkedin_followers_count ? (
        <span className="text-xs text-lia-text-primary">{(candidate.linkedin_followers_count as number).toLocaleString('pt-BR')}</span>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'linkedin_connections_count':
      return candidate.linkedin_connections_count ? (
        <span className="text-xs text-lia-text-primary">{(candidate.linkedin_connections_count as number).toLocaleString('pt-BR')}</span>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'outreach_message':
      return candidate.outreach_message ? (
        <div className="flex items-center gap-1">
          <span className="text-xs text-lia-text-primary truncate max-w-sidebar-content">{(candidate.outreach_message as string).slice(0, 50)}...</span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              navigator.clipboard.writeText(candidate.outreach_message as string)
            }}
            className="p-0.5 hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-xl"
            title={t('copyMessage')}
          >
            <Copy className="w-3 h-3 text-lia-text-tertiary" />
          </button>
        </div>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'best_personal_email':
      return candidate.best_personal_email ? (
        <a href={`mailto:${candidate.best_personal_email as string}`} className="text-xs text-lia-text-secondary hover:text-lia-text-primary hover:underline truncate dark:hover:text-lia-text-inverse">
          {candidate.best_personal_email as string}
        </a>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'phone_types': {
      if (!candidate.phone_types || Object.keys(candidate.phone_types).length === 0) {
        return <span className="text-xs text-lia-text-muted">—</span>
      }
      const activePhoneTypes = Object.entries(candidate.phone_types)
        .filter(([_, active]) => active)
        .map(([type]) => type)
      return <span className="text-xs text-lia-text-primary">{activePhoneTypes.join(', ') || '—'}</span>
    }

    case 'estimated_age':
      return candidate.estimated_age ? (
        <span className="text-xs text-lia-text-primary">{t('yearsOld', { age: candidate.estimated_age as number })}</span>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'match_reasoning':
      return (candidate.pearch_insights as unknown as Record<string, string | undefined>)?.match_reasoning ? (
        <span className="text-xs text-lia-text-primary truncate" title={(candidate.pearch_insights as unknown as Record<string, string>).match_reasoning}>
          {(candidate.pearch_insights as unknown as Record<string, string>).match_reasoning.slice(0, 60)}...
        </span>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'overall_summary':
      return candidate.pearch_insights?.overall_summary ? (
        <span className="text-xs text-lia-text-primary truncate" title={candidate.pearch_insights.overall_summary}>
          {candidate.pearch_insights.overall_summary.slice(0, 60)}...
        </span>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'query_insights': {
      const queryInsightsData = candidate.pearch_insights?.query_insights
      if (!queryInsightsData || queryInsightsData.length === 0) {
        return <span className="text-xs text-lia-text-muted">—</span>
      }
      return (
        <div className="flex flex-col gap-0.5">
          {queryInsightsData.slice(0, 2).map((insight: QueryInsight, idx: number) => (
            <div key={idx} className="flex items-center gap-1">
              <Chip variant="neutral" muted className={`${textStyles.caption} !text-micro px-1 py-0 ${
                insight.match_level === 'Exceeds' ? badgeStyles.success :
                insight.match_level === 'Meets' ? badgeStyles.info :
                insight.match_level === 'Partial' ? badgeStyles.warning :
                badgeStyles.default
              }`}>
                {insight.match_level}
              </Chip>
              <span className={`${textStyles.caption} dark:!text-lia-text-disabled truncate max-w-[150px]`} title={insight.subquery}>
                {insight.subquery?.slice(0, 25)}...
              </span>
            </div>
          ))}
          {queryInsightsData.length > 2 && (
            <span className={textStyles.caption}>{t('moreCount', { count: queryInsightsData.length - 2 })}</span>
          )}
        </div>
      )
    }

    case 'pearch_insights':
      return candidate.pearch_insights?.overall_summary ? (
        <span className="text-xs text-lia-text-primary truncate">{candidate.pearch_insights.overall_summary.slice(0, 50)}...</span>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'middle_name':
      return candidate.middle_name ? (
        <span className="text-xs text-lia-text-primary truncate">{candidate.middle_name as string}</span>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'best_business_email':
      return candidate.best_business_email ? (
        <a href={`mailto:${candidate.best_business_email as string}`} className="text-xs text-lia-text-secondary hover:text-lia-text-primary hover:underline truncate dark:hover:text-lia-text-inverse">
          {candidate.best_business_email as string}
        </a>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'personal_emails': {
      const personalEmails = candidate.personal_emails as string[] | undefined
      if (!personalEmails || personalEmails.length === 0) {
        return <span className="text-xs text-lia-text-muted">—</span>
      }
      return (
        <span className="text-xs text-lia-text-primary truncate" title={personalEmails.join(', ')}>
          {personalEmails.length === 1 ? personalEmails[0] : `${personalEmails[0]} (+${personalEmails.length - 1})`}
        </span>
      )
    }

    case 'business_emails': {
      const businessEmails = candidate.business_emails as string[] | undefined
      if (!businessEmails || businessEmails.length === 0) {
        return <span className="text-xs text-lia-text-muted">—</span>
      }
      return (
        <span className="text-xs text-lia-text-primary truncate" title={businessEmails.join(', ')}>
          {businessEmails.length === 1 ? businessEmails[0] : `${businessEmails[0]} (+${businessEmails.length - 1})`}
        </span>
      )
    }

    case 'company_followers_count':
      return candidate.company_followers_count != null ? (
        <span className="text-xs text-lia-text-primary">{(candidate.company_followers_count as number).toLocaleString('pt-BR')}</span>
      ) : <span className="text-xs text-lia-text-muted">—</span>

    case 'company_keywords': {
      const companyKeywords = candidate.company_keywords as string[] | undefined
      if (!companyKeywords || companyKeywords.length === 0) {
        return <span className="text-xs text-lia-text-muted">—</span>
      }
      return (
        <div className="flex flex-wrap gap-1">
          {companyKeywords.slice(0, 3).map((keyword: string, idx: number) => (
            <Chip key={idx} variant="neutral" className="text-micro px-1 py-0 bg-lia-bg-secondary text-lia-text-secondary dark:bg-lia-bg-elevated">
              {keyword}
            </Chip>
          ))}
          {companyKeywords.length > 3 && (
            <span className={textStyles.caption}>+{companyKeywords.length - 3}</span>
          )}
        </div>
      )
    }

    default:
      return undefined
  }
}
