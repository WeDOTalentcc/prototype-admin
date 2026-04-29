"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  FileSpreadsheet,
  FileText,
  Upload,
  Brain,
  Download,
} from "lucide-react"

interface SmartImportDropAreaProps {
  title: string
  description: string
  expectedFields: string[]
  templateDownloadEndpoint?: string
  disabled: boolean
  isDragging: boolean
  fileInputRef: React.RefObject<HTMLInputElement | null>
  onDragOver: (e: React.DragEvent) => void
  onDragLeave: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent) => void
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  onDownloadTemplate: () => void
}

export function SmartImportDropArea({
  title,
  description,
  expectedFields,
  templateDownloadEndpoint,
  disabled,
  isDragging,
  fileInputRef,
  onDragOver,
  onDragLeave,
  onDrop,
  onFileSelect,
  onDownloadTemplate,
}: SmartImportDropAreaProps) {
  const t = useTranslations("settings.smartImport")
  return (
    <Card
      className={`${cardStyles.interactive} border-2 border-dashed rounded-xl transition-colors motion-reduce:transition-none duration-200 ${
        disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
      } ${
        isDragging && !disabled
          ? 'border-lia-border-medium bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 scale-[1.01]'
          : 'border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium hover:bg-lia-bg-secondary/50 dark:hover:bg-lia-btn-primary-hover/30'
      }`}
      onDragOver={disabled ? undefined : onDragOver}
      onDragLeave={disabled ? undefined : onDragLeave}
      onDrop={disabled ? undefined : onDrop}
      onClick={() => !disabled && fileInputRef.current?.click()}
    >
      <CardContent className="p-4">
        <div className="flex flex-col items-center justify-center text-center gap-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center transition-transform motion-reduce:transition-none duration-200 bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <h3 className={textStyles.title}>{title}</h3>
          <p className={`${textStyles.bodySmall} max-w-md`}>{description}</p>
          <div className="flex items-center gap-2">
            <Chip variant="neutral" className="text-micro rounded-full">
              <FileSpreadsheet className="w-3.5 h-3.5 mr-1" />
              {t("excelFormat")}
            </Chip>
            <Chip variant="neutral" className="text-micro rounded-full">
              <FileText className="w-3.5 h-3.5 mr-1" />
              {t("csvFormat")}
            </Chip>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 rounded-md text-xs"
              onClick={(e) => {
                e.stopPropagation()
                if (!disabled) fileInputRef.current?.click()
              }}
              disabled={disabled}
            >
              <Upload className="w-3.5 h-3.5" />
              {t("selectFile")}
            </Button>
            {templateDownloadEndpoint && (
              <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 rounded-md text-xs text-lia-text-primary hover:text-lia-text-primary"
                onClick={(e) => {
                  e.stopPropagation()
                  if (!disabled) onDownloadTemplate()
                }}
                disabled={disabled}
              >
                <Download className="w-3.5 h-3.5" />
                {t("downloadTemplate")}
              </Button>
            )}
          </div>
          {expectedFields.length > 0 && (
            <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle w-full">
              <p className={`${textStyles.labelSmall} mb-2`}>{t("expectedFields")}</p>
              <div className="flex flex-wrap justify-center gap-1.5">
                {expectedFields.map((field) => (
                  <Chip
                    key={field}
                    variant="neutral"
                    muted
                    className="text-micro bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary rounded-xl"
                  >
                    {field}
                  </Chip>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".xlsx,.xls,.csv"
        onChange={onFileSelect}
      />
    </Card>
  )
}
