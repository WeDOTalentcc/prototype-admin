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
    <div className="flex-shrink-0 w-80 transition-all duration-300">
      <Card className="h-[calc(100vh-12rem)] flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700 rounded-md">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Columns className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <h3 className={textStyles.title}>Configurar Colunas</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 p-0 hover:bg-gray-100"
            >
              <X className="w-4 h-4 text-gray-600" />
            </Button>
          </div>

          <div className="space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600" />
              <input
                type="text"
                placeholder="Buscar coluna..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-xs rounded-md bg-gray-50 dark:bg-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 text-gray-950 dark:text-gray-50"
              />
            </div>
            <div className="flex gap-2">
              <button
                className="flex-1 text-xs h-8 rounded-md bg-gray-50 hover:bg-gray-100 transition-all text-gray-600"
                onClick={onResetColumns}
              >
                Restaurar Padrão
              </button>
              <button
                className="text-xs h-8 px-4 rounded-md bg-gray-50 hover:bg-gray-100 transition-all text-gray-600"
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
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-600">
                    {CATEGORY_LABELS[category] || category}
                  </h4>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${visibleCount > 0 ? 'bg-gray-900/10 text-gray-800' : 'bg-gray-200 text-gray-400'}`}
                  >
                    {visibleCount}/{columns.length}
                  </span>
                </div>
                <div className="space-y-1">
                  {columns.map((col) => (
                    <div
                      key={col.id}
                      onClick={() => toggleColumn(col.id)}
                      className={`flex items-center gap-3 p-2.5 rounded-md cursor-pointer transition-all border ${col.visible ? 'bg-gray-900/5 border-gray-900/20' : 'bg-gray-50 border-gray-200'}`}
                    >
                      <div
                        className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0 transition-all"
                        style={{
                          backgroundColor: col.visible ? 'var(--gray-800)' : 'transparent',
                          border: col.visible ? 'none' : '2px solid var(--gray-300)',
                        }}
                      >
                        {col.visible && (
                          <CheckCircle className="w-3 h-3 text-white" strokeWidth={3} />
                        )}
                      </div>
                      <span
                        className={`text-xs flex-1 ${col.visible ? 'font-medium' : 'font-normal'}`}
                        style={{
                          color: col.visible ? 'var(--gray-800)' : 'var(--gray-500)',
                        }}
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
