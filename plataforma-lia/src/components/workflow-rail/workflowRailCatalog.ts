/**
 * workflowRailCatalog — declarative map of funnel stages and predictive next steps.
 *
 * This is the single source of truth for the WorkflowRail bar.
 * Each `FunnelStage` defines a node in the main funnel progression.
 * Each `NextStep` defines a clickable action the recruiter can take from a given stage,
 * including which stage the rail should transition to after the action is performed.
 *
 * To extend: add stages or next-step entries here; the bar picks them up automatically.
 */

export type FunnelStageKey =
  | "initial"
  | "create_job"
  | "sourcing"
  | "screening"
  | "interview"
  | "offer"
  | "hired"
  | "analytics"

export interface FunnelStage {
  key: FunnelStageKey
  labelKey: string
  icon: string
  /** Ordered position in the linear funnel display (1-based). "initial" is excluded from the bar. */
  order: number
}

export type NextStepActionType = "navigate" | "handler"

export interface NextStep {
  id: string
  icon: string
  titleKey: string
  descKey: string
  actionType: NextStepActionType
  /** Path for navigate actions (locale-relative, e.g. /jobs). */
  path?: string
  /** Handler id for handler actions — matched in the component. */
  handlerId?: string
  /**
   * The funnel stage the rail should display after this step is taken.
   * Allows branch-aware transitions — not always the next sequential stage.
   * If omitted, the bar stays on the current stage.
   */
  resultingStage?: FunnelStageKey
}

export const FUNNEL_STAGES: FunnelStage[] = [
  { key: "create_job", labelKey: "workflowRail.funnel.createJob", icon: "📋", order: 1 },
  { key: "sourcing",   labelKey: "workflowRail.funnel.sourcing",  icon: "🔍", order: 2 },
  { key: "screening",  labelKey: "workflowRail.funnel.screening", icon: "📝", order: 3 },
  { key: "interview",  labelKey: "workflowRail.funnel.interview", icon: "🤝", order: 4 },
  { key: "offer",      labelKey: "workflowRail.funnel.offer",     icon: "📄", order: 5 },
  { key: "hired",      labelKey: "workflowRail.funnel.hired",     icon: "✅", order: 6 },
  { key: "analytics",  labelKey: "workflowRail.funnel.analytics", icon: "📊", order: 7 },
]

export const NEXT_STEPS_MAP: Record<FunnelStageKey, NextStep[]> = {
  initial: [
    {
      id: "create_job",
      icon: "📋",
      titleKey: "workflowRail.nextSteps.initial.createJob.title",
      descKey:  "workflowRail.nextSteps.initial.createJob.desc",
      actionType: "handler",
      handlerId: "createJob",
      resultingStage: "create_job",
    },
    {
      id: "search_candidates",
      icon: "🔍",
      titleKey: "workflowRail.nextSteps.initial.searchCandidates.title",
      descKey:  "workflowRail.nextSteps.initial.searchCandidates.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "sourcing",
    },
    {
      id: "open_funnel",
      icon: "📊",
      titleKey: "workflowRail.nextSteps.initial.openFunnel.title",
      descKey:  "workflowRail.nextSteps.initial.openFunnel.desc",
      actionType: "navigate",
      path: "/visao-do-funil",
      resultingStage: "sourcing",
    },
  ],

  create_job: [
    {
      id: "publish_job",
      icon: "📢",
      titleKey: "workflowRail.nextSteps.createJob.publishJob.title",
      descKey:  "workflowRail.nextSteps.createJob.publishJob.desc",
      actionType: "navigate",
      path: "/jobs",
      resultingStage: "sourcing",
    },
    {
      id: "start_sourcing",
      icon: "🎯",
      titleKey: "workflowRail.nextSteps.createJob.startSourcing.title",
      descKey:  "workflowRail.nextSteps.createJob.startSourcing.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "sourcing",
    },
    {
      id: "generate_jd",
      icon: "✨",
      titleKey: "workflowRail.nextSteps.createJob.generateJD.title",
      descKey:  "workflowRail.nextSteps.createJob.generateJD.desc",
      actionType: "navigate",
      path: "/jobs?action=create",
      resultingStage: "create_job",
    },
    {
      id: "divulge_channels",
      icon: "📣",
      titleKey: "workflowRail.nextSteps.createJob.divulgeChannels.title",
      descKey:  "workflowRail.nextSteps.createJob.divulgeChannels.desc",
      actionType: "navigate",
      path: "/jobs",
      resultingStage: "sourcing",
    },
  ],

  sourcing: [
    {
      id: "add_to_list",
      icon: "➕",
      titleKey: "workflowRail.nextSteps.sourcing.addToList.title",
      descKey:  "workflowRail.nextSteps.sourcing.addToList.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "sourcing",
    },
    {
      id: "search_candidates",
      icon: "🔍",
      titleKey: "workflowRail.nextSteps.sourcing.searchCandidates.title",
      descKey:  "workflowRail.nextSteps.sourcing.searchCandidates.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "sourcing",
    },
    {
      id: "send_wsi",
      icon: "📋",
      titleKey: "workflowRail.nextSteps.sourcing.sendWSI.title",
      descKey:  "workflowRail.nextSteps.sourcing.sendWSI.desc",
      actionType: "navigate",
      path: "/wsi",
      resultingStage: "screening",
    },
    {
      id: "link_to_job",
      icon: "🔗",
      titleKey: "workflowRail.nextSteps.sourcing.linkToJob.title",
      descKey:  "workflowRail.nextSteps.sourcing.linkToJob.desc",
      actionType: "navigate",
      path: "/jobs",
      resultingStage: "sourcing",
    },
  ],

  screening: [
    {
      id: "send_wsi",
      icon: "📋",
      titleKey: "workflowRail.nextSteps.screening.sendWSI.title",
      descKey:  "workflowRail.nextSteps.screening.sendWSI.desc",
      actionType: "navigate",
      path: "/wsi",
      resultingStage: "screening",
    },
    {
      id: "schedule_interview",
      icon: "📅",
      titleKey: "workflowRail.nextSteps.screening.scheduleInterview.title",
      descKey:  "workflowRail.nextSteps.screening.scheduleInterview.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "interview",
    },
    {
      id: "move_rejected",
      icon: "❌",
      titleKey: "workflowRail.nextSteps.screening.moveRejected.title",
      descKey:  "workflowRail.nextSteps.screening.moveRejected.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "screening",
    },
    {
      id: "lia_opinion",
      icon: "✨",
      titleKey: "workflowRail.nextSteps.screening.liaOpinion.title",
      descKey:  "workflowRail.nextSteps.screening.liaOpinion.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "screening",
    },
  ],

  interview: [
    {
      id: "move_to_offer",
      icon: "📄",
      titleKey: "workflowRail.nextSteps.interview.moveToOffer.title",
      descKey:  "workflowRail.nextSteps.interview.moveToOffer.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "offer",
    },
    {
      id: "request_feedback",
      icon: "💬",
      titleKey: "workflowRail.nextSteps.interview.requestFeedback.title",
      descKey:  "workflowRail.nextSteps.interview.requestFeedback.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "interview",
    },
    {
      id: "move_rejected",
      icon: "❌",
      titleKey: "workflowRail.nextSteps.interview.moveRejected.title",
      descKey:  "workflowRail.nextSteps.interview.moveRejected.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "sourcing",
    },
  ],

  offer: [
    {
      id: "approve_offer",
      icon: "✅",
      titleKey: "workflowRail.nextSteps.offer.approveOffer.title",
      descKey:  "workflowRail.nextSteps.offer.approveOffer.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "hired",
    },
    {
      id: "negotiate",
      icon: "🤝",
      titleKey: "workflowRail.nextSteps.offer.negotiate.title",
      descKey:  "workflowRail.nextSteps.offer.negotiate.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "offer",
    },
    {
      id: "move_rejected",
      icon: "❌",
      titleKey: "workflowRail.nextSteps.offer.moveRejected.title",
      descKey:  "workflowRail.nextSteps.offer.moveRejected.desc",
      actionType: "navigate",
      path: "/visao-do-funil?view=candidatos",
      resultingStage: "sourcing",
    },
  ],

  hired: [
    {
      id: "start_onboarding",
      icon: "🎉",
      titleKey: "workflowRail.nextSteps.hired.startOnboarding.title",
      descKey:  "workflowRail.nextSteps.hired.startOnboarding.desc",
      actionType: "navigate",
      path: "/visao-do-funil",
      resultingStage: "analytics",
    },
    {
      id: "view_analytics",
      icon: "📊",
      titleKey: "workflowRail.nextSteps.hired.viewAnalytics.title",
      descKey:  "workflowRail.nextSteps.hired.viewAnalytics.desc",
      actionType: "navigate",
      path: "/visao-do-funil",
      resultingStage: "analytics",
    },
    {
      id: "create_new_job",
      icon: "📋",
      titleKey: "workflowRail.nextSteps.hired.createNewJob.title",
      descKey:  "workflowRail.nextSteps.hired.createNewJob.desc",
      actionType: "handler",
      handlerId: "createJob",
      resultingStage: "create_job",
    },
  ],

  analytics: [
    {
      id: "view_report",
      icon: "📈",
      titleKey: "workflowRail.nextSteps.analytics.viewReport.title",
      descKey:  "workflowRail.nextSteps.analytics.viewReport.desc",
      actionType: "navigate",
      path: "/visao-do-funil",
      resultingStage: "analytics",
    },
    {
      id: "create_new_job",
      icon: "📋",
      titleKey: "workflowRail.nextSteps.analytics.createNewJob.title",
      descKey:  "workflowRail.nextSteps.analytics.createNewJob.desc",
      actionType: "handler",
      handlerId: "createJob",
      resultingStage: "create_job",
    },
  ],
}

/** Maps a backend campaign stage name to a FunnelStageKey for the rail. */
export function mapCampaignStageToFunnelKey(stageName: string | undefined): FunnelStageKey {
  if (!stageName) return "initial"
  const s = stageName.toLowerCase()
  if (s.includes("sourcing") || s.includes("funil") || s.includes("captação") || s.includes("captacao")) return "sourcing"
  if (s.includes("screening") || s.includes("triagem") || s.includes("long_list") || s.includes("short_list")) return "screening"
  if (s.includes("interview") || s.includes("entrevista") || s.includes("technical_test") || s.includes("english_test")) return "interview"
  if (s.includes("offer") || s.includes("proposta") || s.includes("references")) return "offer"
  if (s.includes("hired") || s.includes("contratado") || s.includes("onboarding")) return "hired"
  if (s.includes("analytics") || s.includes("análises") || s.includes("analises")) return "analytics"
  if (s.includes("rejected") || s.includes("reprovado")) return "sourcing"
  return "sourcing"
}
