"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Bell, Settings, Eye, EyeOff, RefreshCw,
  X, CheckCircle
} from "lucide-react"
import { AlertSettingsModal } from "./alert-settings-modal"
import { useKpiAlerts } from "./useKpiAlerts"
import { KpiAlertCard } from "./KpiAlertCard"

interface KPIAlertSystemProps {
  recruiterData: Record<string, unknown>[]
  onAlertAction: (alertId: string, action: string) => void
}

export function KPIAlertSystem({ recruiterData, onAlertAction }: KPIAlertSystemProps) {
  const {
    alertRules,
    filteredAlerts,
    alertStats,
    filterType,
    setFilterType,
    filterCategory,
    setFilterCategory,
    sortBy,
    setSortBy,
    showArchived,
    setShowArchived,
    selectedAlert,
    setSelectedAlert,
    isRefreshing,
    showSettingsModal,
    setShowSettingsModal,
    handleMarkAsRead,
    handleArchiveAlert,
    handleSendNotification,
    handleRefreshAlerts,
    handleUpdateRules,
  } = useKpiAlerts(recruiterData, onAlertAction)

  return (
    <div data-testid="kpi-alert-system" className="space-y-6">
      <Card className="border-l-4 border-l-lia-border-medium dark:border-l-lia-border-medium">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 font-sans">
                <Bell className="w-5 h-5 text-lia-text-secondary" />
                Sistema de Alertas KPI
              </CardTitle>
              <p className="text-sm text-lia-text-secondary mt-1">
                Monitoramento automático da performance dos recrutadores
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshAlerts}
                disabled={isRefreshing}
                className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin motion-reduce:animate-none' : ''}`} />
                Atualizar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettingsModal(true)}
                className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
              >
                <Settings className="w-4 h-4" />
                Configurar
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-semibold text-lia-text-primary">{alertStats.total}</div>
              <div className="text-sm text-lia-text-secondary">Total de Alertas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-semibold text-status-error">{alertStats.critical}</div>
              <div className="text-sm text-lia-text-secondary">Críticos</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-semibold text-status-warning">{alertStats.warning}</div>
              <div className="text-sm text-lia-text-secondary">Avisos</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-semibold text-lia-text-primary">{alertStats.byCategory.performance}</div>
              <div className="text-sm text-lia-text-secondary">Performance</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-semibold text-wedo-orange-text">{alertStats.byCategory.deadline}</div>
              <div className="text-sm text-lia-text-secondary">Prazos</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filtros e Controles</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">Tipo</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full p-2 border border-lia-border-default rounded-xl text-sm"
              >
                <option value="all">Todos</option>
                <option value="critical">Crítico</option>
                <option value="warning">Aviso</option>
                <option value="info">Informação</option>
                <option value="success">Sucesso</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">Categoria</label>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="w-full p-2 border border-lia-border-default rounded-xl text-sm"
              >
                <option value="all">Todas</option>
                <option value="performance">Performance</option>
                <option value="deadline">Prazos</option>
                <option value="target">Metas</option>
                <option value="budget">Orçamento</option>
                <option value="quality">Qualidade</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">Ordenar por</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                className="w-full p-2 border border-lia-border-default rounded-xl text-sm"
              >
                <option value="date">Data</option>
                <option value="priority">Prioridade</option>
                <option value="severity">Severidade</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-lia-text-primary mb-2 block">Ações</label>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowArchived(!showArchived)}
                  className="gap-2 flex-1 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                >
                  {showArchived ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  {showArchived ? 'Ocultar' : 'Mostrar'} Arquivados
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Alertas Ativos ({filteredAlerts.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts.length === 0 ? (
              <div className="text-center py-8 text-lia-text-secondary">
                <Bell className="w-12 h-12 mx-auto mb-4 text-lia-text-secondary" />
                <p aria-live="polite" aria-atomic="true">Nenhum alerta encontrado</p>
                <p className="text-sm">Todos os KPIs estão dentro dos parâmetros esperados</p>
              </div>
            ) : (
              filteredAlerts.map((alert) => (
                <KpiAlertCard
                  key={alert.id}
                  alert={alert}
                  onMarkAsRead={handleMarkAsRead}
                  onArchive={handleArchiveAlert}
                  onSendNotification={handleSendNotification}
                  onShowDetails={setSelectedAlert}
                />
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-lia-bg-primary rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Detalhes do Alerta</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedAlert(null)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Todas as Ações Sugeridas:</h4>
                  <ul className="space-y-2">
                    {selectedAlert.suggestedActions.map((action, index) => (
                      <li key={`sel-action-${index}`} className="text-sm text-lia-text-secondary flex items-start gap-2 p-2 bg-lia-bg-secondary rounded-xl">
                        <span className="text-lia-text-secondary mt-1">•</span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex gap-2 pt-4 border-t">
                  <Button
                    onClick={() => {
                      handleMarkAsRead(selectedAlert.id)
                      setSelectedAlert(null)
                    }}
                    className="gap-2 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Implementar Ações
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setSelectedAlert(null)}
                  >
                    Fechar
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <AlertSettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        alertRules={alertRules}
        onUpdateRules={handleUpdateRules}
      />
    </div>
  )
}
