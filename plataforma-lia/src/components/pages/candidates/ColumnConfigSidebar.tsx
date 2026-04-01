"use client"

import React from "react"
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
  if (!showColumnConfig) return null

  const categoryLabels: Record<string, string> = {
    basico: "Identificação Básica",
    contato: "Contato",
    pessoal: "Informações Pessoais",
    profissional: "Perfil Profissional",
    competencias: "Competências",
    localizacao: "Localização",
    endereco: "Endereço Completo",
    preferencias: "Preferências de Trabalho",
    salario: "Salário e Expectativas",
    documentos: "Currículo e Documentos",
    origem: "Origem e Integração",
    busca_global: "Busca Global",
    ia: "Insights LIA / IA",
    status: "Status e Workflow",
    comunicacao: "Comunicação",
    cadastro: "Status de Cadastro",
    adicional: "Informações Adicionais",
    datas: "Datas e Timestamps",
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
    <div className="flex-shrink-0 w-80 transition-colors motion-reduce:transition-none duration-300">
      <div className="bg-lia-bg-primary rounded-md h-[calc(100vh-6rem)] overflow-hidden">
        {/* Header */}
        <div className="p-4 flex items-center justify-between border-b border-lia-border-subtle">
          <div>
            <h3 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">
              Configurar Colunas
            </h3>
            <p className="text-xs mt-0.5 text-lia-text-primary">
              {tableColumns.filter((c) => c.visible && c.id !== "acoes").length} de{" "}
              {tableColumns.filter((c) => c.id !== "acoes").length} colunas ativas
            </p>
          </div>
          <button
            onClick={() => setShowColumnConfig(false)}
            className="h-8 w-8 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none text-lia-text-primary hover:text-lia-text-primary hover:bg-gray-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Search and Actions */}
        <div className="p-3 space-y-3 border-b border-lia-border-subtle">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-primary" />
            <input
              type="text"
              placeholder="Buscar coluna..."
              value={columnSearchTerm}
              onChange={(e) => setColumnSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-md bg-gray-50 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 text-lia-text-primary dark:text-lia-text-primary"
            />
          </div>
          <div className="flex gap-2">
            <button
              className="flex-1 text-xs h-8 rounded-md bg-gray-50 hover:bg-gray-100 transition-colors motion-reduce:transition-none text-lia-text-secondary"
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
              Restaurar Padrão
            </button>
            <button
              className="text-xs h-8 px-4 rounded-md bg-gray-50 hover:bg-gray-100 transition-colors motion-reduce:transition-none text-lia-text-secondary"
              onClick={() => {
                setTableColumns((prev) => prev.map((col) => ({ ...col, visible: true })))
              }}
            >
              Todas
            </button>
          </div>
        </div>

        {/* Column List */}
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
                    className="text-xs px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor:
                        visibleCount > 0 ? "var(--gray-100)" : "var(--gray-100)",
                      color:
                        visibleCount > 0 ? "var(--gray-600)" : "var(--gray-400)",
                    }}
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
                      className="flex items-center gap-3 p-2.5 rounded-md cursor-pointer transition-colors motion-reduce:transition-none hover:bg-gray-100"
                      style={{
                        backgroundColor: col.visible
                          ? "var(--gray-50)"
                          : "var(--gray-50)",
                        border: col.visible
                          ? "1px solid var(--gray-300)"
                          : "1px solid var(--gray-200)",
                      }}
                    >
                      <div
                        className="w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors motion-reduce:transition-none"
                        style={{
                          backgroundColor: col.visible
                            ? "var(--gray-600)"
                            : "transparent",
                          border: col.visible
                            ? "none"
                            : "2px solid var(--gray-300)",
                        }}
                      >
                        {col.visible && (
                          <Check className="w-3 h-3 text-white" strokeWidth={3} />
                        )}
                      </div>
                      <span
                        className="text-xs flex-1 flex items-center gap-1.5"
                        style={{
                          color: col.visible
                            ? "var(--gray-800)"
                            : "var(--gray-500)",
                          fontWeight: col.visible ? 500 : 400,
                        }}
                      >
                        {col.isGlobalSearch && (
                          <Globe className="w-3 h-3 text-lia-text-secondary dark:text-lia-text-tertiary" />
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
