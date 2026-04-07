import { KPIAlertSystem } from "@/components/alerts/kpi-alert-system"
import type { RecruiterData } from "../indicators.types"

interface AlertsTabProps {
  recruiters: RecruiterData[]
  onAlertAction: (alertId: string, action: string) => void
}

export function AlertsTab({ recruiters, onAlertAction }: AlertsTabProps) {
  return (
    <div className="space-y-6" data-testid="alerts-tab">
      <KPIAlertSystem
        recruiterData={recruiters as unknown as Record<string, unknown>[]}
        onAlertAction={onAlertAction}
      />
    </div>
  )
}
