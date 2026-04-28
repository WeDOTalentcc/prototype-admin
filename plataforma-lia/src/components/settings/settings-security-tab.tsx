"use client"

import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Shield, Phone, Download } from "lucide-react"

export interface SettingsSecurityTabProps {
  onSettingsChange: (changed: boolean) => void
}

export function SettingsSecurityTab({ onSettingsChange }: SettingsSecurityTabProps) {
  const t = useTranslations("settings.security")
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Shield className="w-4 h-4" />
            {t("title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Button variant="outline" className="w-full justify-start">
              <Shield className="w-4 h-4 mr-2" />
              {t("changePassword")}
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Phone className="w-4 h-4 mr-2" />
              {t("configure2FA")}
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Download className="w-4 h-4 mr-2" />
              {t("downloadData")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("privacy")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label htmlFor="privacy-share-usage-data" className="cursor-pointer">
                <div className="text-sm font-medium">{t("shareUsageData")}</div>
                <div className="text-xs text-lia-text-primary">{t("shareUsageDataDesc")}</div>
              </label>
              <input
                id="privacy-share-usage-data"
                type="checkbox"
                defaultChecked
                onChange={() => onSettingsChange(true)}
              />
            </div>
            <div className="flex items-center justify-between">
              <label htmlFor="privacy-behavior-analysis" className="cursor-pointer">
                <div className="text-sm font-medium">{t("behaviorAnalysis")}</div>
                <div className="text-xs text-lia-text-primary">{t("behaviorAnalysisDesc")}</div>
              </label>
              <input
                id="privacy-behavior-analysis"
                type="checkbox"
                defaultChecked
                onChange={() => onSettingsChange(true)}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
