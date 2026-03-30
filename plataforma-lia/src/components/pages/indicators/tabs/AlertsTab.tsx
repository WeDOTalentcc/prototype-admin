import { KPIAlertSystem } from "@/components/alerts/kpi-alert-system"
import type { RecruiterData } from "../indicators.types"

interface AlertsTabProps {
  recruiters: RecruiterData[]
  onAlertAction: (alertId: string, action: string) => void
}

export function AlertsTab({ recruiters, onAlertAction }: AlertsTabProps) {
  return (
    <div className="space-y-6">
      <KPIAlertSystem
        recruiterData={recruiters}
        onAlertAction={onAlertAction}
      />
    </div>
  )
}
