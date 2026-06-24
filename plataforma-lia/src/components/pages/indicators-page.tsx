"use client"

import { Button } from "@/components/ui/button"
import { AdvancedReportExporter } from "@/components/reports/advanced-report-exporter"
import { Download, RefreshCw } from "lucide-react"
import { useIndicatorsPage } from "./indicators/useIndicatorsPage"
import { TABS } from "./indicators/indicators.constants"
import dynamic from "next/dynamic"
import { AlertsTab } from "./indicators/tabs/AlertsTab"
import { AgentControlTab } from "./indicators/tabs/AgentControlTab"

// Tabs com chart.js/react-chartjs-2 - lazy loaded para reduzir bundle inicial (~300kb)
const StrategicTab = dynamic(
  () => import("./indicators/tabs/StrategicTab").then((m) => ({ default: m.StrategicTab })),
  { ssr: false, loading: () => <div className="h-64 flex items-center justify-center text-lia-text-secondary">Carregando graficos...</div> }
)
const RecruitersTab = dynamic(
  () => import("./indicators/tabs/RecruitersTab").then((m) => ({ default: m.RecruitersTab })),
  { ssr: false, loading: () => <div className="h-64 flex items-center justify-center text-lia-text-secondary">Carregando graficos...</div> }
)
const PredictionsTab = dynamic(
  () => import("./indicators/tabs/PredictionsTab").then((m) => ({ default: m.PredictionsTab })),
  { ssr: false, loading: () => <div className="h-64 flex items-center justify-center text-lia-text-secondary">Carregando...</div> }
)

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
    showExportModal,
    setShowExportModal,
    recruiters,
    departments,
    filteredRecruiters,
    teamMetrics,
    getStatusColor,
    handleAlertAction,
  } = useIndicatorsPage()

  return (
    <div className="p-6 space-y-6 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-lia-text-primary">
            Indicadores e Analytics
          </h1>
          <p className="text-lia-text-secondary">
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

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-lia-bg-secondary rounded-lg w-fit">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
                activeTab === tab.id
                  ? "bg-lia-bg-primary text-lia-text-primary shadow-sm"
                  : "text-lia-text-secondary hover:text-lia-text-primary"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
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
