"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { X, Search, Check, Globe } from "lucide-react"

type TableColumn = {
  id: string
  label: string
  visible: boolean
  order: number
  width?: number
  minWidth?: number
  category?: string
  sortable?: boolean
  isGlobalSearch?: boolean
}

interface ColumnConfigSidebarProps {
  showColumnConfig: boolean
  tableColumns: TableColumn[]
  setTableColumns: React.Dispatch<React.SetStateAction<TableColumn[]>>
  columnSearchTerm: string
  setColumnSearchTerm: (value: string) => void
  setShowColumnConfig: (value: boolean) => void
}

export function ColumnConfigSidebar({
  showColumnConfig,
  tableColumns,
  setTableColumns,
  columnSearchTerm,
  setColumnSearchTerm,
  setShowColumnConfig,
}: ColumnConfigSidebarProps) {
  const t = useTranslations('candidates.columns')

  if (!showColumnConfig) return null

  const categoryLabels: Record<string, string> = {
    basico: t('basico'),
    contato: t('contato'),
    pessoal: t('pessoal'),
    profissional: t('profissional'),
    competencias: t('competencias'),
    localizacao: t('localizacao'),
    endereco: t('endereco'),
    preferencias: t('preferencias'),
    salario: t('salario'),
    documentos: t('documentos'),
    origem: t('origem'),
    busca_global: t('busca_global'),
    ia: t('ia'),
    status: t('status'),
    comunicacao: t('comunicacao'),
    cadastro: t('cadastro'),
    adicional: t('adicional'),
    datas: t('datas'),
  }

  const categoryOrder = [
    "basico", "contato", "pessoal", "profissional", "competencias",
    "localizacao", "endereco", "preferencias", "salario", "documentos",
    "origem", "busca_global", "ia", "status", "comunicacao", "cadastro",
    "adicional", "datas",
  ]

  const filteredColumns = tableColumns.filter(
    (col) =>
      col.id !== "acoes" &&
      col.id !== "feedback" &&
      (col.label.toLowerCase().includes(columnSearchTerm.toLowerCase()) ||
        col.id.toLowerCase().includes(columnSearchTerm.toLowerCase()))
  )

  const groupedColumns = filteredColumns.reduce((acc, col) => {
    const category = col.category || "adicional"
    if (!acc[category]) acc[category] = []
    acc[category].push(col)
    return acc
  }, {} as Record<string, typeof tableColumns>)

  return (
    <div data-testid="column-config-sidebar" className="flex-shrink-0 w-80 transition-colors motion-reduce:transition-none duration-300">
      <div className="bg-lia-bg-primary rounded-xl h-[calc(100vh-6rem)] overflow-hidden">
        <div className="p-4 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-lia-text-primary">
              {t('configureColumns')}
            </h3>
            <p className="text-xs mt-0.5 text-lia-text-primary">
              {t('columnsActive', {
                visible: tableColumns.filter((c) => c.visible && c.id !== "acoes").length,
                total: tableColumns.filter((c) => c.id !== "acoes").length
              })}
            </p>
          </div>
          <button
            onClick={() => setShowColumnConfig(false)}
            className="h-8 w-8 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none text-lia-text-primary hover:text-lia-text-primary hover:bg-lia-bg-tertiary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-3 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-primary" />
            <input
              type="text"
              placeholder={t('searchColumn')}
              value={columnSearchTerm}
              onChange={(e) => setColumnSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-md bg-lia-bg-secondary placeholder-lia-text-tertiary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 text-lia-text-primary"
            />
          </div>
          <div className="flex gap-2">
            <button
              className="flex-1 text-xs h-8 rounded-xl bg-lia-bg-secondary hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none text-lia-text-secondary"
              onClick={() => {
                setTableColumns((prev) =>
                  prev.map((col, idx) => ({
                    ...col,
                    visible: col.id === "acoes" || idx < 7,
                    order: col.id === "acoes" ? 0.5 : idx,
                  }))
                )
              }}
            >
              {t('restoreDefault')}
            </button>
            <button
              className="text-xs h-8 px-4 rounded-xl bg-lia-bg-secondary hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none text-lia-text-secondary"
              onClick={() => {
                setTableColumns((prev) => prev.map((col) => ({ ...col, visible: true })))
              }}
            >
              {t('showAll')}
            </button>
          </div>
        </div>

        <div className="overflow-y-auto h-[calc(100%-160px)] p-3">
          {categoryOrder.map((category) => {
            const columns = groupedColumns[category]
            if (!columns || columns.length === 0) return null

            const visibleCount = columns.filter((c) => c.visible).length

            return (
              <div key={category} className="mb-5">
                <div className="flex items-center justify-between mb-2 px-1">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary">
                    {categoryLabels[category] || category}
                  </h4>
                  <span
                    className="text-micro px-2 py-0.5 rounded-full bg-lia-bg-tertiary text-lia-text-secondary"
                  >
                    {visibleCount}/{columns.length}
                  </span>
                </div>
                <div className="space-y-1">
                  {columns.map((col) => (
                    <div
                      key={col.id}
                      onClick={() => {
                        setTableColumns((prev) =>
                          prev.map((c) =>
                            c.id === col.id ? { ...c, visible: !c.visible } : c
                          )
                        )
                      }}
                      className={`flex items-center gap-3 p-2.5 rounded-md cursor-pointer transition-colors motion-reduce:transition-none hover:bg-lia-bg-tertiary bg-lia-bg-secondary ${col.visible ? "border border-lia-border-default" : "border border-lia-border-subtle"}`}
                    >
                      <div
                        className={`w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors motion-reduce:transition-none ${col.visible ? "bg-lia-text-secondary border-0" : "bg-transparent border-2 border-lia-border-default"}`}
                      >
                        {col.visible && (
                          <Check className="w-3 h-3 text-white" strokeWidth={3} />
                        )}
                      </div>
                      <span
                        className={`text-xs flex-1 flex items-center gap-1.5 ${col.visible ? "text-lia-text-primary font-medium" : "text-lia-text-secondary font-normal"}`}
                      >
                        {col.isGlobalSearch && (
                          <Globe className="w-3 h-3 text-lia-text-secondary" />
                        )}
                        {col.label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
