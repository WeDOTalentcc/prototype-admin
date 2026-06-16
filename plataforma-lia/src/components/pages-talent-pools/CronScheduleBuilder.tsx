"use client"

/**
 * CronScheduleBuilder — Sprint 7C Part 3.
 *
 * Visual cron picker canonical. Presets diário/semanal/mensal + custom expression.
 * Output: cron expression string consumida pelo backend (schedule_config.cron_expression).
 *
 * Validação client-side via cron-parser (canonical JS cron parser).
 */
import React, { useState, useEffect, useMemo } from "react"
import { useTranslations } from "next-intl"
import { CronExpressionParser } from "cron-parser"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { textStyles } from "@/lib/design-tokens"

export type CronPreset = "daily" | "weekly" | "monthly" | "custom"

export interface CronScheduleBuilderProps {
  /** Initial cron expression (controlled). */
  value: string
  /** Callback canonical: `(cron_expression, label)`. */
  onChange: (cronExpression: string, label: string) => void
}

const WEEKDAYS = ["0", "1", "2", "3", "4", "5", "6"] as const

function buildCron(preset: CronPreset, hour: number, minute: number, dayOfWeek: string, dayOfMonth: number): string {
  switch (preset) {
    case "daily":
      return `${minute} ${hour} * * *`
    case "weekly":
      return `${minute} ${hour} * * ${dayOfWeek}`
    case "monthly":
      return `${minute} ${hour} ${dayOfMonth} * *`
    default:
      return ""
  }
}

function detectPreset(expr: string): CronPreset {
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) return "custom"
  const [minute, hour, dom, mon, dow] = parts
  if (!/^\d+$/.test(minute) || !/^\d+$/.test(hour)) return "custom"
  if (mon !== "*") return "custom"
  if (dom === "*" && dow === "*") return "daily"
  if (dom === "*" && /^\d$/.test(dow)) return "weekly"
  if (/^\d+$/.test(dom) && dow === "*") return "monthly"
  return "custom"
}

export function CronScheduleBuilder({ value, onChange }: CronScheduleBuilderProps) {
  const t = useTranslations("talentPool.schedule.cronBuilder")

  const initial = useMemo(() => detectPreset(value || "0 9 * * *"), [value])
  const [preset, setPreset] = useState<CronPreset>(initial)
  const [hour, setHour] = useState<number>(9)
  const [minute, setMinute] = useState<number>(0)
  const [dayOfWeek, setDayOfWeek] = useState<string>("1")
  const [dayOfMonth, setDayOfMonth] = useState<number>(1)
  const [customExpr, setCustomExpr] = useState<string>(value || "0 9 * * *")

  // Validation of custom expression
  const customValid = useMemo(() => {
    if (preset !== "custom") return true
    try {
      CronExpressionParser.parse(customExpr)
      return true
    } catch {
      return false
    }
  }, [preset, customExpr])

  useEffect(() => {
    const expr =
      preset === "custom"
        ? customExpr
        : buildCron(preset, hour, minute, dayOfWeek, dayOfMonth)
    if (preset === "custom" && !customValid) return
    const label =
      preset === "custom"
        ? `${t("presets.custom")}: ${expr}`
        : preset === "daily"
          ? `${t("presets.daily")} ${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`
          : preset === "weekly"
            ? `${t("presets.weekly")} ${t(`weekdays.${dayOfWeek}` as never)} ${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`
            : `${t("presets.monthly")} ${t("dayLabel")} ${dayOfMonth} ${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`
    onChange(expr, label)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preset, hour, minute, dayOfWeek, dayOfMonth, customExpr, customValid])

  return (
    <div className="space-y-3" data-testid="cron-schedule-builder">
      <p className={textStyles.h4}>{t("title")}</p>

      <div className="space-y-2">
        <Label htmlFor="cron-preset">{t("presetLabel")}</Label>
        <Select
          value={preset}
          onValueChange={(v) => setPreset(v as CronPreset)}
        >
          <SelectTrigger id="cron-preset" data-testid="cron-preset-select">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="daily" data-testid="cron-preset-daily">
              {t("presets.daily")}
            </SelectItem>
            <SelectItem value="weekly" data-testid="cron-preset-weekly">
              {t("presets.weekly")}
            </SelectItem>
            <SelectItem value="monthly" data-testid="cron-preset-monthly">
              {t("presets.monthly")}
            </SelectItem>
            <SelectItem value="custom" data-testid="cron-preset-custom">
              {t("presets.custom")}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {preset !== "custom" && (
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="cron-hour">{t("hourLabel")}</Label>
            <Input
              id="cron-hour"
              type="number"
              min={0}
              max={23}
              value={hour}
              onChange={(e) => setHour(Math.max(0, Math.min(23, Number(e.target.value) || 0)))}
              data-testid="cron-hour-input"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="cron-minute">{t("minuteLabel")}</Label>
            <Input
              id="cron-minute"
              type="number"
              min={0}
              max={59}
              value={minute}
              onChange={(e) => setMinute(Math.max(0, Math.min(59, Number(e.target.value) || 0)))}
              data-testid="cron-minute-input"
            />
          </div>
        </div>
      )}

      {preset === "weekly" && (
        <div className="space-y-2">
          <Label htmlFor="cron-dow">{t("dayOfWeekLabel")}</Label>
          <Select value={dayOfWeek} onValueChange={setDayOfWeek}>
            <SelectTrigger id="cron-dow" data-testid="cron-dow-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {WEEKDAYS.map((d) => (
                <SelectItem key={d} value={d}>
                  {t(`weekdays.${d}` as never)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {preset === "monthly" && (
        <div className="space-y-2">
          <Label htmlFor="cron-dom">{t("dayOfMonthLabel")}</Label>
          <Input
            id="cron-dom"
            type="number"
            min={1}
            max={28}
            value={dayOfMonth}
            onChange={(e) => setDayOfMonth(Math.max(1, Math.min(28, Number(e.target.value) || 1)))}
            data-testid="cron-dom-input"
          />
        </div>
      )}

      {preset === "custom" && (
        <div className="space-y-2">
          <Label htmlFor="cron-custom">{t("expressionLabel")}</Label>
          <Input
            id="cron-custom"
            type="text"
            value={customExpr}
            onChange={(e) => setCustomExpr(e.target.value)}
            data-testid="cron-custom-input"
            placeholder="0 9 * * *"
            className="font-mono"
          />
          {!customValid && (
            <p
              className={textStyles.bodySmall + " text-red-500"}
              data-testid="cron-custom-invalid"
              role="alert"
            >
              {t("invalid")}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
