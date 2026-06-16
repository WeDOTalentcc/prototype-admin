"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { CheckCircle, AlertCircle, Eye, X } from "lucide-react"
import type { PreviewData } from "./smart-import-types"

interface SmartImportPreviewProps {
  fileName?: string
  previewData: PreviewData | null
  onCancel: () => void
  onConfirm: () => void
}

export function SmartImportPreview({
  fileName,
  previewData,
  onCancel,
  onConfirm,
}: SmartImportPreviewProps) {
  const t = useTranslations("settings.smartImport")
  return (
    <Card className={`${cardStyles.default} dark:border-lia-border-subtle rounded-md overflow-hidden`}>
      <div className="px-2 py-1.5 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-lia-bg-primary dark:bg-lia-bg-secondary">
              <Eye className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <h3 className={textStyles.title}>{t("previewTitle")}</h3>
              <p className={textStyles.caption} aria-live="polite" aria-atomic="true">
                {t("previewSubtitle", { count: previewData?.totalRows || 0, fileName: fileName || "" })}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onCancel}
            className="rounded-md text-lia-text-primary hover:text-lia-text-primary"
          >
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      <CardContent className="p-4">
        {previewData && (
          <>
            <div className="flex flex-wrap gap-2 mb-3">
              {previewData.matchedFields.length > 0 && (
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5 text-status-success" />
                  <span className={textStyles.labelSmall}>{t("matchedFields")}</span>
                  {previewData.matchedFields.map((field) => (
                    <Chip
                      variant="neutral"
                      muted
                      key={field}
                      className="text-micro  dark:bg-status-success/30 dark:text-status-success rounded-full"
                    >
                      {field}
                    </Chip>
                  ))}
                </div>
              )}
              {previewData.unmatchedFields.length > 0 && (
                <div className="flex items-center gap-1.5 mt-1">
                  <AlertCircle className="w-3.5 h-3.5 text-status-warning" />
                  <span className={textStyles.labelSmall} aria-live="polite" aria-atomic="true">
                    {t("unmatchedFields")}
                  </span>
                  {previewData.unmatchedFields.map((field) => (
                    <Chip
                      variant="neutral"
                      muted
                      key={field}
                      className="text-micro  dark:bg-status-warning/30 dark:text-status-warning rounded-full"
                    >
                      {field}
                    </Chip>
                  ))}
                </div>
              )}
            </div>

            {previewData.rows.length > 0 && (
              <div className="border border-lia-border-subtle dark:border-lia-border-strong rounded-xl overflow-hidden mb-3">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50">
                        {previewData.headers.map((header, idx) => (
                          <th
                            key={idx}
                            className="px-2 py-1.5 text-left text-micro font-medium text-lia-text-secondary dark:border-lia-border-subtle"
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.rows.map((row, rowIdx) => (
                        <tr
                          key={rowIdx}
                          className="hover:bg-lia-bg-secondary/50 dark:hover:bg-lia-btn-primary-hover/30"
                        >
                          {previewData.headers.map((header, colIdx) => (
                            <td
                              key={colIdx}
                              className="px-2 py-1.5 text-xs text-lia-text-primary dark:border-lia-border-strong truncate max-w-sidebar-content"
                            >
                              {row[header] || '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {previewData.totalRows > 5 && (
                  <div className="px-2 py-1.5 text-center text-micro text-lia-text-secondary bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/30">
                    {t("moreRecords", { count: previewData.totalRows - 5 })}
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onCancel}
                className="gap-1.5 rounded-md text-xs"
              >
                <X className="w-3.5 h-3.5" />
                {t("cancel")}
              </Button>
              <Button
                size="sm"
                onClick={onConfirm}
                className="gap-1.5 rounded-md text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                {t("confirmImport")}
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
