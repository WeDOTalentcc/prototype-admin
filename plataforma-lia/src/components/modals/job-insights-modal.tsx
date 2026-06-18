"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Download, Mail, BarChart3 } from "lucide-react"

import type { JobInsightsModalProps } from "./job-insights/job-insights.types"
import { useJobInsights } from "./job-insights/useJobInsights"
import { InsightsOverviewSection } from "./job-insights/sections/InsightsOverviewSection"
import { InsightsPipelineSection } from "./job-insights/sections/InsightsPipelineSection"

export type {
  WSIScore,
  InsightCategory,
  ConversionRate,
  StageBottleneck,
  DemographicDistribution,
  CandidateDemographics,
  JobBehavioralCompetency,
  JobLiaMetrics,
  JobInsightData,
} from "./job-insights/job-insights.types"

export function JobInsightsModal({
  isOpen,
  onClose,
  onSendEmail,
  jobs,
  aggregatedDemographics,
  conversionRates,
  bottlenecks,
  insights,
}: JobInsightsModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('job-insights', isOpen)

  const {
    aggregateMetrics,
    funnelData,
    demographicData,
    salaryData,
    qualityMetrics,
    wsiMetrics,
    liaFunnelMetrics,
    calculatedConversionRates,
    categorizedInsights,
    liaTextualAnalysis,
    trendData,
    getDaysRemaining,
    getScoreColor,
    handleExportReport,
    handleSendEmail,
  } = useJobInsights({
    jobs,
    aggregatedDemographics,
    conversionRates,
    bottlenecks,
    insights,
    onSendEmail,
  })

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        data-testid="job-insights-modal"
        className="max-w-4xl max-h-[85vh] bg-lia-bg-primary border border-lia-border-subtle flex flex-col"
        aria-describedby="insights-modal-description"
      >
        {/* ── Header ──────────────────────────────────────────────────── */}
        <DialogHeader className="pb-3 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                Relatório de Insights
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5" aria-live="polite" aria-atomic="true">
                {jobs.length} vaga{jobs.length !== 1 ? "s" : ""} selecionada{jobs.length !== 1 ? "s" : ""}{" "}
                • Gerado em {new Date().toLocaleDateString("pt-BR")}
              </p>
            </div>
          </div>
          <span id="insights-modal-description" className="sr-only">
            Relatório de insights com métricas, funil, e análises das vagas selecionadas
          </span>
        </DialogHeader>

        {/* ── Scrollable body ──────────────────────────────────────────── */}
        <div id="insights-report-content" className="flex-1 overflow-y-auto py-4 space-y-4">
          <InsightsOverviewSection
            jobs={jobs}
            aggregateMetrics={aggregateMetrics}
            funnelData={funnelData}
            salaryData={salaryData}
            qualityMetrics={qualityMetrics}
            wsiMetrics={wsiMetrics}
            liaTextualAnalysis={liaTextualAnalysis}
            trendData={trendData}
            calculatedConversionRates={calculatedConversionRates}
            categorizedInsights={categorizedInsights}
            bottlenecks={bottlenecks}
            getScoreColor={getScoreColor}
            getDaysRemaining={getDaysRemaining}
          />

          <InsightsPipelineSection
            jobs={jobs}
            liaFunnelMetrics={liaFunnelMetrics}
            demographicData={demographicData}
          />
        </div>

        {/* ── Footer ──────────────────────────────────────────────────── */}
        <DialogFooter className="pt-3 border-t border-lia-border-subtle flex-shrink-0">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportReport}
                className="h-8 px-3 text-xs gap-1.5 border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover dark:hover:bg-lia-bg-secondary"
              >
                <Download className="w-3.5 h-3.5" />
                Exportar PDF
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSendEmail}
                disabled={!onSendEmail}
                className="h-8 px-3 text-xs gap-1.5 border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover dark:hover:bg-lia-bg-secondary disabled:opacity-50"
              >
                <Mail className="w-3.5 h-3.5" />
                Enviar por Email
              </Button>
            </div>
            <Button
              onClick={onClose}
              className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-bg-tertiary dark:hover:bg-lia-bg-secondary text-white"
            >
              Fechar
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
