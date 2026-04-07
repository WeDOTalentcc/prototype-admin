"use client"

import { useState } from "react"
import { Columns, X, Search } from "lucide-react"
import { CheckCircle } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { textStyles } from "@/lib/design-tokens"
import type { TableColumn } from "@/components/tables"

interface KanbanColumnConfigPanelProps {
  open: boolean
  onClose: () => void
  tableColumns: TableColumn[]
  onTableColumnsChange: (columns: TableColumn[]) => void
  onResetColumns: () => void
}

const CATEGORY_LABELS: Record<string, string> = {
  basico: 'Identificação Básica',
  contato: 'Contato',
  pessoal: 'Informações Pessoais',
  profissional: 'Perfil Profissional',
  competencias: 'Competências',
  localizacao: 'Localização',
  endereco: 'Endereço Completo',
  preferencias: 'Preferências de Trabalho',
  salario: 'Salário e Expectativas',
  documentos: 'Currículo e Documentos',
  origem: 'Origem e Integração',
  busca_global: 'Busca Global',
  ia: 'Insights LIA / IA',
  status: 'Status e Workflow',
  comunicacao: 'Comunicação',
  cadastro: 'Status de Cadastro',
  adicional: 'Informações Adicionais',
  datas: 'Datas e Timestamps',
}

const CATEGORY_ORDER = ['basico', 'contato', 'pessoal', 'profissional', 'competencias', 'localizacao', 'endereco', 'preferencias', 'salario', 'documentos', 'origem', 'busca_global', 'ia', 'status', 'comunicacao', 'cadastro', 'adicional', 'datas']

export function KanbanColumnConfigPanel({
  open,
  onClose,
  tableColumns,
  onTableColumnsChange,
  onResetColumns,
}: KanbanColumnConfigPanelProps) {
  const [searchTerm, setSearchTerm] = useState('')

  if (!open) return null

  const filteredColumns = tableColumns.filter(col =>
    col.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
    col.id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const groupedColumns = filteredColumns.reduce((acc, col) => {
    const category = col.category || 'adicional'
    if (!acc[category]) acc[category] = []
    acc[category].push(col)
    return acc
  }, {} as Record<string, TableColumn[]>)

  const toggleColumn = (colId: string) => {
    onTableColumnsChange(tableColumns.map(c =>
      c.id === colId ? { ...c, visible: !c.visible } : c
    ))
  }

  const showAll = () => {
    onTableColumnsChange(tableColumns.map(col => ({ ...col, visible: true })))
  }

  return (
    <div className="flex-shrink-0 w-80 transition-colors motion-reduce:transition-none duration-300">
      <Card className="h-[calc(100vh-12rem)] flex flex-col overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Columns className="w-4 h-4 text-lia-text-secondary" />
              <h3 className={textStyles.title}>Configurar Colunas</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary"
            >
              <X className="w-4 h-4 text-lia-text-secondary" />
            </Button>
          </div>

          <div className="space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-secondary" />
              <input
                type="text"
                placeholder="Buscar coluna..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-xs rounded-md bg-lia-bg-secondary dark:bg-lia-bg-secondary placeholder-lia-text-tertiary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 text-lia-text-primary"
              />
            </div>
            <div className="flex gap-2">
              <button
                className="flex-1 text-xs h-8 rounded-md bg-lia-bg-secondary hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none text-lia-text-secondary"
                onClick={onResetColumns}
              >
                Restaurar Padrão
              </button>
              <button
                className="text-xs h-8 px-4 rounded-md bg-lia-bg-secondary hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none text-lia-text-secondary"
                onClick={showAll}
              >
                Todas
              </button>
            </div>
          </div>
        </div>

        {/* Column List */}
        <div className="overflow-y-auto flex-1 p-3">
          {CATEGORY_ORDER.map(category => {
            const columns = groupedColumns[category]
            if (!columns || columns.length === 0) return null

            const visibleCount = columns.filter(c => c.visible).length

            return (
              <div key={category} className="mb-5">
                <div className="flex items-center justify-between mb-2 px-1">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-secondary">
                    {CATEGORY_LABELS[category] || category}
                  </h4>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${visibleCount > 0 ? 'bg-lia-btn-primary-bg/10 text-lia-text-primary' : 'bg-lia-interactive-active text-lia-text-disabled'}`}
                  >
                    {visibleCount}/{columns.length}
                  </span>
                </div>
                <div className="space-y-1">
                  {columns.map((col) => (
                    <div
                      key={col.id}
                      onClick={() => toggleColumn(col.id)}
                      className={`flex items-center gap-3 p-2.5 rounded-md cursor-pointer transition-colors motion-reduce:transition-none border ${col.visible ? 'bg-lia-btn-primary-bg/5 border-lia-btn-primary-bg/20' : 'bg-lia-bg-secondary border-lia-border-subtle'}`}
                    >
                      <div
                        className={`w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors motion-reduce:transition-none ${col.visible ? 'bg-lia-text-primary border-none' : 'border-2 border-lia-border-default bg-transparent'}`}
                      >
                        {col.visible && (
                          <CheckCircle className="w-3 h-3 text-white" strokeWidth={3} />
                        )}
                      </div>
                      <span
                        className={`text-xs flex-1 ${col.visible ? 'font-medium text-lia-text-primary' : 'font-normal text-lia-text-secondary'}`}
                      >
                        {col.label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}
