"use client"

import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Star } from "lucide-react"

export function NPSTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const t = useTranslations("settings.nps")
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Star className="w-4 h-4" />
            {t("title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("scaleLabel")}
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
              >
                <option>{t("scaleStandard")}</option>
                <option>{t("scaleSimplified")}</option>
                <option>{t("scaleCustom")}</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-3 block">
                {t("frequencyLabel")}
              </label>
              <select
                onChange={() => onSettingsChange(true)}
                className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
              >
                <option>{t("frequencyAfterEach")}</option>
                <option>{t("frequencyWeekly")}</option>
                <option>{t("frequencyMonthly")}</option>
                <option>{t("frequencyQuarterly")}</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("mainQuestionLabel")}
            </label>
            <textarea
              rows={3}
              defaultValue={t("defaultQuestion")}
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
