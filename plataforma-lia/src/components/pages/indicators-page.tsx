"use client"

import { Button } from "@/components/ui/button"
import { ExpandableAIPrompt } from "@/components/expandable-ai-prompt"
import { AdvancedReportExporter } from "@/components/reports/advanced-report-exporter"
import { Download, RefreshCw } from "lucide-react"
import { useIndicatorsPage } from "./indicators/useIndicatorsPage"
import { TABS } from "./indicators/indicators.constants"
import { StrategicTab } from "./indicators/tabs/StrategicTab"
import { RecruitersTab } from "./indicators/tabs/RecruitersTab"
import { AlertsTab } from "./indicators/tabs/AlertsTab"
import { WorkModelsTab } from "./indicators/tabs/WorkModelsTab"
import { PredictionsTab } from "./indicators/tabs/PredictionsTab"
import { AgentControlTab } from "./indicators/tabs/AgentControlTab"

export function IndicatorsPage() {
  const {
    activeTab,
    setActiveTab,
    selectedPeriod,
    setSelectedPeriod,
    selectedDepartments,
    setSelectedDepartments,
    selectedRecruiters,
    setSelectedRecruiters,
    showAdvancedFilters,
    setShowAdvancedFilters,
    viewMode,
    setViewMode,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    selectedCandidates,
    showExportModal,
    setShowExportModal,
    recruiters,
    departments,
    filteredRecruiters,
    teamMetrics,
    getStatusColor,
    handleCommandAction,
    handleAlertAction,
  } = useIndicatorsPage()

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
            Indicadores e Analytics
          </h1>
          <p className="text-lia-text-secondary dark:text-lia-text-tertiary">
            Dashboard executivo com insights estratégicos e performance de recrutadores
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => setShowExportModal(true)}
          >
            <Download className="w-4 h-4" />
            Exportar Relatório
          </Button>
          <Button variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Atualizar Dados
          </Button>
        </div>
      </div>

      {/* LIA Prompt */}
      <ExpandableAIPrompt
        selectedCandidates={selectedCandidates}
        onCommand={handleCommandAction}
        filteredCount={filteredRecruiters.length}
        totalCount={recruiters.length}
      />

      {/* Tabs */}
      <div className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
        <div className="flex space-x-8">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-1 py-4 text-sm font-medium border-b-2 transition-colors motion-reduce:transition-none ${
                activeTab === tab.id
                  ? "border-gray-900 dark:border-lia-border-medium text-lia-text-secondary dark:text-lia-text-tertiary"
                  : "border-transparent text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-disabled"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "strategic" && <StrategicTab />}

      {activeTab === "recruiters" && (
        <RecruitersTab
          recruiters={recruiters}
          filteredRecruiters={filteredRecruiters}
          departments={departments}
          teamMetrics={teamMetrics}
          selectedPeriod={selectedPeriod}
          setSelectedPeriod={setSelectedPeriod}
          selectedDepartments={selectedDepartments}
          setSelectedDepartments={setSelectedDepartments}
          selectedRecruiters={selectedRecruiters}
          setSelectedRecruiters={setSelectedRecruiters}
          showAdvancedFilters={showAdvancedFilters}
          setShowAdvancedFilters={setShowAdvancedFilters}
          viewMode={viewMode}
          setViewMode={setViewMode}
          sortBy={sortBy}
          setSortBy={setSortBy}
          sortOrder={sortOrder}
          setSortOrder={setSortOrder}
          getStatusColor={getStatusColor}
          setActiveTab={setActiveTab}
        />
      )}

      {activeTab === "alerts" && (
        <AlertsTab recruiters={recruiters} onAlertAction={handleAlertAction} />
      )}

      {activeTab === "work_models" && <WorkModelsTab />}

      {activeTab === "predictions" && <PredictionsTab recruiters={recruiters} />}

      {activeTab === "agent_control" && <AgentControlTab />}

      {/* Modal de Exportação Avançada */}
      <AdvancedReportExporter
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        data={{
          recruiters: filteredRecruiters,
          teamMetrics,
          selectedPeriod,
          selectedDepartments,
          alertStats: {},
        }}
        userRole="hr"
      />
    </div>
  )
}
