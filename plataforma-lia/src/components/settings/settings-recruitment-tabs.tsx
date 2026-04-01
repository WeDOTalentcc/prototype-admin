// Re-exports — split into src/components/settings/recruitment/
export { CommunicationTab, RecruitmentJourneyTab, AssessmentTab, AutomationsTab, NPSTab } from "./recruitment"

export interface SettingsRecruitmentTabProps {
  onSettingsChange: (changed: boolean) => void
}
