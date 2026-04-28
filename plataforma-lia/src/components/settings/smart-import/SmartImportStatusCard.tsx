"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ThinkingDots } from "@/components/ui/thinking-dots"
import {
  Brain,
  Loader2,
  CheckCircle,
  AlertCircle,
  Upload,
  X,
} from "lucide-react"

type StatusVariant = 'uploading' | 'analyzing' | 'importing' | 'success' | 'error'

interface SmartImportStatusCardProps {
  variant: StatusVariant
  fileName?: string
  totalRows?: number
  message?: string | null
  onReset?: () => void
}

export function SmartImportStatusCard({
  variant,
  fileName,
  totalRows,
  message,
  onReset,
}: SmartImportStatusCardProps) {
  const t = useTranslations("settings.smartImport")
  if (variant === 'uploading') {
    return (
      <Card className="border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/30">
        <CardContent className="p-4">
          <div
            className="flex flex-col items-center justify-center text-center gap-2"
            role="status"
            aria-live="polite"
            aria-label={t("loading")}
          >
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-lia-bg-primary dark:bg-lia-bg-secondary">
              <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
            <h3 className={textStyles.title}>{t("uploadingFile")}</h3>
            <p className={textStyles.bodySmall}>{fileName}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (variant === 'analyzing') {
    return (
      <Card className="rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 border border-lia-border-default dark:border-lia-border-default">
        <CardContent className="p-4">
          <div className="flex flex-col items-center justify-center text-center gap-2">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-lia-bg-primary dark:bg-lia-bg-secondary animate-pulse motion-reduce:animate-none">
              <Brain className="w-4 h-4 text-wedo-cyan" />
            </div>
            <h3 className={textStyles.title}>{t("analyzing")}</h3>
            <p className={textStyles.bodySmall}>{t("analyzingDesc")}</p>
            <div className="flex items-center gap-2 mt-2">
              <ThinkingDots dotClassName="bg-lia-btn-primary-bg" size="md" />
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (variant === 'importing') {
    return (
      <Card className="border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary/50">
        <CardContent className="p-4">
          <div
            className="flex flex-col items-center justify-center text-center gap-2"
            role="status"
            aria-live="polite"
            aria-label={t("loading")}
          >
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-lia-bg-primary dark:bg-lia-bg-secondary">
              <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
            <h3 className={textStyles.title}>{t("importing")}</h3>
            <p className={textStyles.bodySmall}>
              {t("importingDesc", { count: totalRows || 0 })}
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (variant === 'success') {
    return (
      <Card
        className={`${cardStyles.default} border border-status-success/30 dark:border-status-success/30 rounded-md bg-status-success/10/50 dark:bg-status-success/10`}
      >
        <CardContent className="p-4">
          <div className="flex flex-col items-center justify-center text-center gap-2">
            <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-success/15 dark:bg-status-success/30">
              <CheckCircle className="w-4 h-4 text-status-success dark:text-status-success" />
            </div>
            <h3 className={textStyles.title}>{t("success")}</h3>
            <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success`}>
              {message}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
              className="gap-1.5 rounded-md text-xs border-status-success/30 text-status-success hover:bg-status-success/15 dark:border-status-success/30 dark:text-status-success dark:hover:bg-status-success/30"
            >
              <Upload className="w-3.5 h-3.5" />
              {t("newImport")}
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card
      className={`${cardStyles.default} border border-status-error/30 dark:border-status-error/30 rounded-md bg-status-error/10/50 dark:bg-status-error/10`}
    >
      <CardContent className="p-4">
        <div className="flex flex-col items-center justify-center text-center gap-2">
          <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-error/15 dark:bg-status-error/30">
            <AlertCircle className="w-4 h-4 text-status-error dark:text-status-error" />
          </div>
          <h3 className={textStyles.title}>{t("errorTitle")}</h3>
          <p className={`${textStyles.bodySmall} text-status-error dark:text-status-error max-w-md`}>
            {message}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={onReset}
            className="gap-1.5 rounded-md text-xs border-status-error/30 text-status-error hover:bg-status-error/15 dark:border-status-error/30 dark:text-status-error dark:hover:bg-status-error/30"
          >
            <X className="w-3.5 h-3.5" />
            {t("tryAgain")}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
