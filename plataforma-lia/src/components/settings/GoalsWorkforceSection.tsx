"use client"

import { CURRENCY_PLACEHOLDER } from "@/lib/pricing"
import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Calendar, Plus, Edit, Trash2, Save, X,
  ChevronDown, ChevronUp, Download, RefreshCw, Loader2
} from "lucide-react"
import { SmartImportZone } from "./SmartImportZone"
import { LiaFieldToggle, defaultLiaFieldExamples } from "./LiaFieldToggle"
import { textStyles, cardStyles, badgeStyles, buttonStyles, actionButtonStyles } from '@/lib/design-tokens'
import type { MonthlyPlanning, Position, DepartmentData } from "./goalsPlanningConstants"

interface GoalsWorkforceSectionProps {
  departments: DepartmentData[]
  selectedYear: number
  setSelectedYear: (year: number) => void
  isEditingWorkforce: boolean
  setIsEditingWorkforce: (editing: boolean) => void
  saving: boolean
  departmentsLoaded: boolean
  liaToggles: Record<string, boolean>
  liaInstructions: Record<string, string>
  handleLiaToggleChange: (fieldKey: string, isActive: boolean) => Promise<void>
  handleLiaInstructionSave: (fieldKey: string, instruction: string) => Promise<void>
  toggleDepartmentExpand: (deptId: string) => void
  addDepartment: () => Promise<void>
  addPositionToDepartment: (deptId: string) => void
  updatePositionSalary: (deptId: string, posId: string, field: 'salary_min' | 'salary_max', value: number | undefined) => void
  updatePositionName: (deptId: string, posId: string, name: string) => void
  updatePositionMonth: (deptId: string, posId: string, month: keyof MonthlyPlanning, value: number) => void
  deletePosition: (deptId: string, posId: string) => void
  updateDepartmentName: (deptId: string, name: string) => Promise<void>
  saveWorkforceData: () => Promise<void>
  fetchWorkforceData: () => Promise<void>
}

const monthKeys: (keyof MonthlyPlanning)[] = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
const monthLabels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

const getPositionTotal = (pos: Position) => {
  return monthKeys.reduce((sum, key) => sum + pos.monthlyPlanned[key], 0)
}

export function GoalsWorkforceSection({
  departments,
  selectedYear,
  setSelectedYear,
  isEditingWorkforce,
  setIsEditingWorkforce,
  saving,
  departmentsLoaded,
  liaToggles,
  liaInstructions,
  handleLiaToggleChange,
  handleLiaInstructionSave,
  toggleDepartmentExpand,
  addDepartment,
  addPositionToDepartment,
  updatePositionSalary,
  updatePositionName,
  updatePositionMonth,
  deletePosition,
  updateDepartmentName,
  saveWorkforceData,
  fetchWorkforceData,
}: GoalsWorkforceSectionProps) {
  const totalPlanned = departments.reduce((acc, d) => acc + d.positions.reduce((pAcc, p) => pAcc + getPositionTotal(p), 0), 0)

  return (
    <div className="space-y-4">
      <SmartImportZone
        title="Importar Plano de Headcount"
        description="Importe o plano anual de contratações por departamento e mês. A LIA analisa e sugere ajustes baseados em dados históricos."
        importEndpoint="/api/backend-proxy/workforce/entries/import"
        templateDownloadEndpoint="/api/backend-proxy/workforce/entries/import/template"
        expectedFields={["department", "month", "year", "planned", "actual"]}
        onImportSuccess={fetchWorkforceData}
        disabled={!isEditingWorkforce}
      />

      <Card className={cardStyles.default}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h3} flex items-center gap-2 flex-wrap`}>
                <Calendar className="w-3.5 h-3.5 text-lia-text-secondary" />
                Planejamento de Headcount {selectedYear}
                {departmentsLoaded && (
                  <Badge variant="outline" className={`${badgeStyles.success} text-micro font-normal`}>
                    <RefreshCw className="w-2.5 h-2.5 mr-1" />
                    Sincronizado
                  </Badge>
                )}
                <div className="flex items-center gap-2 ml-2">
                  <LiaFieldToggle
                    fieldKey="headcount_planning"
                    isActive={liaToggles.headcount_planning ?? false}
                    currentInstruction={liaInstructions.headcount_planning || ''}
                    examples={defaultLiaFieldExamples.headcount_planning}
                    onToggleChange={handleLiaToggleChange}
                    onInstructionSave={handleLiaInstructionSave}
                    compact
                  />
                  <span className={textStyles.caption}>Consumido pela LIA</span>
                </div>
              </CardTitle>
              <p className={`${textStyles.description} mt-1`}>
                Departamentos integrados com Empresa e Equipe. Novos departamentos são criados automaticamente.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                disabled={!isEditingWorkforce}
                className={`${textStyles.caption} border border-lia-border-subtle rounded-md px-2 py-1.5 bg-lia-bg-primary dark:bg-lia-bg-elevated disabled:bg-lia-bg-secondary dark:disabled:bg-lia-btn-primary-hover disabled:text-lia-text-secondary dark:border-lia-border-default`}
              >
                <option value={2024}>2024</option>
                <option value={2025}>2025</option>
              </select>
              <button className={actionButtonStyles.smOutline}>
                <Download className={actionButtonStyles.icon} />
                Exportar
              </button>
              {!isEditingWorkforce ? (
                <button
                  onClick={() => setIsEditingWorkforce(true)}
                  className={actionButtonStyles.smOutline}
                >
                  <Edit className={actionButtonStyles.icon} />
                  Editar
                </button>
              ) : (
                <>
                  <button
                    onClick={() => setIsEditingWorkforce(false)}
                    className={actionButtonStyles.smSecondary}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={async () => {
                      await saveWorkforceData()
                      setIsEditingWorkforce(false)
                    }}
                    disabled={saving}
                    className={actionButtonStyles.smPrimary}
                  >
                    {saving ? <Loader2 className={actionButtonStyles.icon + " animate-spin motion-reduce:animate-none"} /> : <Save className={actionButtonStyles.icon} />}
                    Salvar Alterações
                  </button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 mb-4">
            <Card className={`${cardStyles.flat} rounded-md flex-1`}>
              <CardContent className="p-2.5">
                <p className={textStyles.caption}>Total Planejado {selectedYear}</p>
                <p className={textStyles.metricLarge} aria-live="polite" aria-atomic="true">{totalPlanned} vagas</p>
              </CardContent>
            </Card>
            <p className={`${textStyles.description} max-w-xs`}>
              O acompanhamento do realizado será exibido nos dashboards de performance.
            </p>
          </div>

          <div className="space-y-3">
            {departments.map((dept) => (
              <div key={dept.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl overflow-hidden">
                <div 
                  className="flex items-center justify-between p-3 cursor-pointer hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/50"
                  onClick={() => toggleDepartmentExpand(dept.id)}
                >
                  <div className="flex items-center gap-2 flex-1">
                    {dept.expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
                    <input
                      type="text"
                      value={dept.name}
                      onChange={(e) => updateDepartmentName(dept.id, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      disabled={!isEditingWorkforce}
                      className={`${textStyles.subtitle} font-semibold border-0 bg-transparent outline-0 disabled:opacity-70 text-lia-text-primary`}
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={textStyles.description}>
                      {dept.positions.length} posição{dept.positions.length !== 1 ? 's' : ''}
                    </span>
                    <span className={`${textStyles.subtitle} font-semibold text-lia-text-primary`} aria-live="polite" aria-atomic="true">
                      {dept.positions.reduce((acc, p) => acc + getPositionTotal(p), 0)} vagas
                    </span>
                  </div>
                </div>

                {dept.expanded && (
                  <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/50">
                    <div className="overflow-x-auto">
                      <table className={`w-full ${textStyles.caption}`}>
                        <thead>
                          <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
                            <th className={`text-left p-2 min-w-[140px] sticky left-0 bg-lia-bg-secondary dark:bg-lia-bg-secondary ${textStyles.captionBold}`}>Posição</th>
                            <th className={`text-center p-2 min-w-[90px] ${textStyles.captionBold} text-lia-text-primary`}>Salário Mín.</th>
                            <th className={`text-center p-2 min-w-[90px] ${textStyles.captionBold} text-lia-text-primary`}>Salário Máx.</th>
                            {monthLabels.map((month, idx) => (
                              <th key={idx} className={`text-center p-2 min-w-10 ${textStyles.captionBold} text-lia-text-primary`}>{month}</th>
                            ))}
                            <th className={`text-center p-2 min-w-[50px] font-semibold text-lia-text-primary`}>Total</th>
                            <th className="w-8 p-2"></th>
                          </tr>
                        </thead>
                        <tbody>
                          {dept.positions.map((pos) => (
                            <tr key={pos.id} className=" dark:border-lia-border-subtle hover:bg-lia-bg-primary dark:hover:bg-lia-bg-inverse/50">
                              <td className="p-2 sticky left-0 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                                <input
                                  type="text"
                                  value={pos.name}
                                  onChange={(e) => updatePositionName(dept.id, pos.id, e.target.value)}
                                  placeholder="Nome da posição"
                                  disabled={!isEditingWorkforce}
                                  className={`w-full px-2 py-1 ${textStyles.caption} border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-lia-bg-primary dark:bg-lia-bg-elevated disabled:bg-lia-bg-secondary dark:disabled:bg-lia-btn-primary-hover disabled:text-lia-text-secondary dark:disabled:text-lia-text-secondary`}
                                />
                              </td>
                              <td className="p-1 text-center">
                                <input
                                  type="number"
                                  min={0}
                                  value={pos.salary_min ?? ''}
                                  onChange={(e) => updatePositionSalary(dept.id, pos.id, 'salary_min', e.target.value ? parseInt(e.target.value) : undefined)}
                                  placeholder={CURRENCY_PLACEHOLDER}
                                  disabled={!isEditingWorkforce}
                                  className={`w-20 px-1 py-1 ${textStyles.caption} border border-lia-border-subtle dark:border-lia-border-default rounded-md text-center bg-lia-bg-primary dark:bg-lia-bg-elevated disabled:bg-lia-bg-secondary dark:disabled:bg-lia-btn-primary-hover disabled:text-lia-text-secondary`}
                                />
                              </td>
                              <td className="p-1 text-center">
                                <input
                                  type="number"
                                  min={0}
                                  value={pos.salary_max ?? ''}
                                  onChange={(e) => updatePositionSalary(dept.id, pos.id, 'salary_max', e.target.value ? parseInt(e.target.value) : undefined)}
                                  placeholder={CURRENCY_PLACEHOLDER}
                                  disabled={!isEditingWorkforce}
                                  className={`w-20 px-1 py-1 ${textStyles.caption} border border-lia-border-subtle dark:border-lia-border-default rounded-md text-center bg-lia-bg-primary dark:bg-lia-bg-elevated disabled:bg-lia-bg-secondary dark:disabled:bg-lia-btn-primary-hover disabled:text-lia-text-secondary`}
                                />
                              </td>
                              {monthKeys.map((monthKey, idx) => (
                                <td key={idx} className="p-1 text-center">
                                  <input
                                    type="number"
                                    min={0}
                                    value={pos.monthlyPlanned[monthKey] || 0}
                                    onChange={(e) => updatePositionMonth(dept.id, pos.id, monthKey, parseInt(e.target.value) || 0)}
                                    disabled={!isEditingWorkforce}
                                    className={`w-10 px-1 py-1 ${textStyles.caption} border border-lia-border-subtle dark:border-lia-border-default rounded-md text-center bg-lia-bg-primary dark:bg-lia-bg-elevated disabled:bg-lia-bg-secondary dark:disabled:bg-lia-btn-primary-hover disabled:text-lia-text-secondary`}
                                  />
                                </td>
                              ))}
                              <td className="p-2 text-center font-semibold text-lia-text-primary">
                                {getPositionTotal(pos)}
                              </td>
                              <td className="p-1">
                                {isEditingWorkforce && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => deletePosition(dept.id, pos.id)}
                                    className="p-1 h-6 w-6"
                                  >
                                    <Trash2 className="w-3 h-3 text-status-error" />
                                  </Button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {isEditingWorkforce && (
                      <div className="p-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => addPositionToDepartment(dept.id)}
                          className={`w-full gap-1.5 py-1.5 text-micro rounded-md ${buttonStyles.outline}`}
                        >
                          <Plus className="w-3 h-3" />
                          Adicionar Posição
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {isEditingWorkforce && (
            <Button
              onClick={addDepartment}
              className={`w-full mt-4 gap-1.5 py-1.5 text-xs rounded-md ${buttonStyles.primary}`}
            >
              <Plus className="w-3.5 h-3.5" />
              Adicionar Departamento
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
