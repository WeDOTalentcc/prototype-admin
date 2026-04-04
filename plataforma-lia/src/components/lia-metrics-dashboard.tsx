"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, Activity, ArrowRight, Timer } from "lucide-react"
import { LiaMetricsChart } from "./lia-metrics-chart"
import { textStyles } from "@/lib/design-tokens"
import { useLiaMetrics, generateTimeSeriesData, type DashboardCandidate } from "./useLiaMetrics"
import { LiaMetricsKPIs } from "./LiaMetricsKPIs"
import { LiaMetricsDetails } from "./LiaMetricsDetails"

interface LiaMetricsDashboardProps {
  candidates: DashboardCandidate[]
}

export function LiaMetricsDashboard({ candidates }: LiaMetricsDashboardProps) {
  const metrics = useLiaMetrics(candidates)

  return (
    <div className="space-y-4">
      <LiaMetricsKPIs
        contacted={metrics.contacted}
        totalCandidates={metrics.totalCandidates}
        contactRate={metrics.contactRate}
        triageCompleted={metrics.triageCompleted}
        triageConversionRate={metrics.triageConversionRate}
        triageApproved={metrics.triageApproved}
        triageApprovalRate={metrics.triageApprovalRate}
        interviewScheduled={metrics.interviewScheduled}
        interviewConversionRate={metrics.interviewConversionRate}
        avgTimeContact={metrics.avgTimeContact}
        avgLiaScore={metrics.avgLiaScore}
        avgSkillsMatch={metrics.avgSkillsMatch}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <Activity className="w-4 h-4 text-wedo-purple" />
              Funil de Conversão LIA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {metrics.funnelStages.map((stage, index) => (
                <div key={stage.stage} className="relative">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-md ${stage.bgColor} flex items-center justify-center`}>
                      {stage.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`${textStyles.label}`}>
                          {stage.stage}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-lia-text-secondary">
                            {stage.count}/{stage.total}
                          </span>
                          <Badge className="text-xs px-1.5 py-0.5" variant="outline">
                            {stage.rate.toFixed(0)}%
                          </Badge>
                        </div>
                      </div>
                      <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${
                            stage.rate >= 70 ? 'bg-wedo-green' :
                            stage.rate >= 50 ? 'bg-wedo-orange' :
                            'bg-status-error'
                          }`}
                          style={{width: `${stage.rate}%`}}
                        />
                      </div>
                    </div>
                    {stage.avgTime > 0 && (
                      <div className={`flex items-center gap-1 ${textStyles.bodySmall}`}>
                        <Timer className="w-3 h-3" />
                        {stage.avgTime}h
                      </div>
                    )}
                  </div>
                  {index < metrics.funnelStages.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-lia-text-secondary ml-4 my-1" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <TrendingUp className="w-4 h-4 text-status-success" />
              Distribuição de Scores LIA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <LiaMetricsChart
                data={metrics.scoreDistribution}
                title="Distribuição de Scores"
                color="var(--status-success)"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <LiaMetricsDetails
        contactRate={metrics.contactRate}
        triageConversionRate={metrics.triageConversionRate}
        triageApprovalRate={metrics.triageApprovalRate}
        interviewConversionRate={metrics.interviewConversionRate}
        avgLiaScore={metrics.avgLiaScore}
        avgSkillsMatch={metrics.avgSkillsMatch}
        avgTimeContact={metrics.avgTimeContact}
        avgTimeTriage={metrics.avgTimeTriage}
        avgTimeInterview={metrics.avgTimeInterview}
        avgTimeTotal={metrics.avgTimeTotal}
        pendingApproval={metrics.pendingApproval}
        sourceMetrics={metrics.sourceMetrics}
        candidateStatusBreakdown={metrics.candidateStatusBreakdown}
      />
    </div>
  )
}
