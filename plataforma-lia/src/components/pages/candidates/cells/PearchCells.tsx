import React from "react"
import { Copy } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { textStyles, badgeStyles } from "@/lib/design-tokens"
import type { Candidate } from "@/components/pages/candidates/types"

export function renderPearchInsightCell(
  columnId: string,
  candidate: Candidate
): React.ReactNode {
  switch (columnId) {
    case "is_open_to_work": {
      const isOpenToWork = candidate.is_opentowork || candidate.is_open_to_work
      return isOpenToWork ? (
        <Badge className="text-xs bg-status-success/15 text-status-success">Open to Work</Badge>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    }
    case "is_decision_maker":
      return candidate.is_decision_maker ? (
        <Badge className="text-xs bg-wedo-purple/15 text-wedo-purple">Decision Maker</Badge>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "is_top_universities":
      return candidate.is_top_universities ? (
        <Badge className="text-xs bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary">
          Top University
        </Badge>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "is_hiring":
      return candidate.is_hiring ? (
        <Badge className="text-xs bg-wedo-orange/15 text-wedo-orange">Contratando</Badge>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "headline":
      return <span className="text-xs text-lia-text-primary truncate">{candidate.headline || ""}</span>
    case "expertise":
      return (
        <span className="text-xs text-lia-text-primary truncate">
          {candidate.expertise?.slice(0, 3).join(", ") || ""}
          {candidate.expertise && candidate.expertise.length > 3 ? ` (+${candidate.expertise.length - 3})` : ""}
        </span>
      )
    case "linkedin_followers_count":
      return candidate.linkedin_followers_count ? (
        <span className="text-xs text-lia-text-primary">
          {candidate.linkedin_followers_count.toLocaleString("pt-BR")}
        </span>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "linkedin_connections_count":
      return candidate.linkedin_connections_count ? (
        <span className="text-xs text-lia-text-primary">
          {candidate.linkedin_connections_count.toLocaleString("pt-BR")}
        </span>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "outreach_message":
      return candidate.outreach_message ? (
        <div className="flex items-center gap-1">
          <span className="text-xs text-lia-text-primary truncate max-w-sidebar-content">
            {candidate.outreach_message.slice(0, 50)}...
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              navigator.clipboard.writeText(candidate.outreach_message!)
            }}
            className="p-0.5 hover:bg-gray-100 rounded-md"
            title="Copiar mensagem"
          >
            <Copy className="w-3 h-3 text-lia-text-tertiary" />
          </button>
        </div>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "pearch_insights":
      return candidate.pearch_insights?.overall_summary ? (
        <span className="text-xs text-lia-text-primary truncate">
          {candidate.pearch_insights.overall_summary.slice(0, 50)}...
        </span>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "best_personal_email":
      return candidate.best_personal_email ? (
        <a
          href={`mailto:${candidate.best_personal_email}`}
          className="text-xs text-lia-text-secondary dark:text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse hover:underline truncate"
        >
          {candidate.best_personal_email}
        </a>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "best_business_email":
      return candidate.best_business_email ? (
        <a
          href={`mailto:${candidate.best_business_email}`}
          className="text-xs text-lia-text-secondary dark:text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse hover:underline truncate"
        >
          {candidate.best_business_email}
        </a>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "phone_types": {
      if (!candidate.phone_types || Object.keys(candidate.phone_types).length === 0) {
        return <span className="text-xs text-lia-text-tertiary">—</span>
      }
      const activeTypes = Object.entries(candidate.phone_types)
        .filter(([_, active]) => active)
        .map(([type]) => type)
      return (
        <span className="text-xs text-lia-text-primary">{activeTypes.join(", ") || "—"}</span>
      )
    }
    case "estimated_age":
      return candidate.estimated_age ? (
        <span className="text-xs text-lia-text-primary">{candidate.estimated_age} anos</span>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "match_reasoning":
      return candidate.pearch_insights?.match_reasoning ? (
        <span
          className="text-xs text-lia-text-primary truncate"
          title={candidate.pearch_insights.match_reasoning}
        >
          {candidate.pearch_insights.match_reasoning.slice(0, 60)}...
        </span>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "overall_summary":
      return candidate.pearch_insights?.overall_summary ? (
        <span
          className="text-xs text-lia-text-primary truncate"
          title={candidate.pearch_insights.overall_summary}
        >
          {candidate.pearch_insights.overall_summary.slice(0, 60)}...
        </span>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "query_insights": {
      const queryInsights = candidate.pearch_insights?.query_insights
      if (!queryInsights || queryInsights.length === 0) {
        return <span className="text-xs text-lia-text-tertiary">—</span>
      }
      return (
        <div className="flex flex-col gap-0.5">
          {queryInsights.slice(0, 2).map((insight, idx) => (
            <div key={idx} className="flex items-center gap-1">
              <Badge
                className={`text-micro px-1 py-0 ${
                  insight.match_level === "Exceeds"
                    ? "bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success"
                    : insight.match_level === "Meets"
                      ? "bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary"
                      : insight.match_level === "Partial"
                        ? "bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning"
                        : "bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-secondary"
                }`}
              >
                {insight.match_level}
              </Badge>
              <span
                className={`${textStyles.caption} truncate max-w-[150px]`}
                title={insight.subquery}
              >
                {insight.subquery?.slice(0, 25)}...
              </span>
            </div>
          ))}
          {queryInsights.length > 2 && (
            <span className={textStyles.caption}>+{queryInsights.length - 2} mais</span>
          )}
        </div>
      )
    }
    case "middle_name":
      return candidate.middle_name ? (
        <span className="text-xs text-lia-text-primary truncate">{candidate.middle_name}</span>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "personal_emails": {
      const arr = candidate.personal_emails
      if (!arr || arr.length === 0) return <span className="text-xs text-lia-text-tertiary">—</span>
      return (
        <span className="text-xs text-lia-text-primary truncate" title={arr.join(", ")}>
          {arr.length === 1 ? arr[0] : `${arr[0]} (+${arr.length - 1})`}
        </span>
      )
    }
    case "business_emails": {
      const arr = candidate.business_emails
      if (!arr || arr.length === 0) return <span className="text-xs text-lia-text-tertiary">—</span>
      return (
        <span className="text-xs text-lia-text-primary truncate" title={arr.join(", ")}>
          {arr.length === 1 ? arr[0] : `${arr[0]} (+${arr.length - 1})`}
        </span>
      )
    }
    case "company_followers_count":
      return candidate.company_followers_count != null ? (
        <span className="text-xs text-lia-text-primary">
          {candidate.company_followers_count.toLocaleString("pt-BR")}
        </span>
      ) : (
        <span className="text-xs text-lia-text-tertiary">—</span>
      )
    case "company_keywords": {
      const arr = candidate.company_keywords
      if (!arr || arr.length === 0) return <span className="text-xs text-lia-text-tertiary">—</span>
      return (
        <div className="flex flex-wrap gap-1">
          {arr.slice(0, 3).map((keyword, idx) => (
            <Badge key={idx} variant="outline" className={`${badgeStyles.default} px-1 py-0`}>
              {keyword}
            </Badge>
          ))}
          {arr.length > 3 && (
            <span className={textStyles.caption}>+{arr.length - 3}</span>
          )}
        </div>
      )
    }
    default:
      return null
  }
}
