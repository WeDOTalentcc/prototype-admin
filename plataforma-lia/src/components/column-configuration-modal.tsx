"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Search,
  GripVertical,
  X,
  Eye,
  EyeOff,
  Settings
} from "lucide-react"

// Lista completa de campos baseada na tabela fornecida
const AVAILABLE_COLUMNS = [
  { id: 'uid', label: 'ID do candidato', type: 'string', defaultVisible: false },
  { id: 'name', label: 'Nome completo', type: 'string', defaultVisible: true },
  { id: 'email', label: 'E-mail', type: 'string', defaultVisible: false },
  { id: 'secondary_email', label: 'E-mail secundário', type: 'string', defaultVisible: false },
  { id: 'mobile_phone', label: 'Telefone celular', type: 'string', defaultVisible: false },
  { id: 'phone', label: 'Telefone fixo', type: 'string', defaultVisible: false },
  { id: 'secondary_phone', label: 'Telefone adicional', type: 'string', defaultVisible: false },
  { id: 'linkedin', label: 'LinkedIn', type: 'string', defaultVisible: true },
  { id: 'github', label: 'GitHub', type: 'string', defaultVisible: false },
  { id: 'portfolio', label: 'Portfólio', type: 'string', defaultVisible: false },
  { id: 'current_company', label: 'Empresa atual', type: 'string', defaultVisible: true },
  { id: 'role_name', label: 'Cargo atual', type: 'string', defaultVisible: true },
  { id: 'position_level', label: 'Nível de posição', type: 'string', defaultVisible: false },
  { id: 'score_lia', label: 'Score IA', type: 'number', defaultVisible: true },
  { id: 'date_birth', label: 'Data de nascimento', type: 'date', defaultVisible: false },
  { id: 'gender', label: 'Gênero', type: 'integer', defaultVisible: false },
  { id: 'nationality', label: 'Nacionalidade', type: 'string', defaultVisible: false },
  { id: 'marital_status', label: 'Estado civil', type: 'integer', defaultVisible: false },
  { id: 'cpf', label: 'CPF', type: 'string', defaultVisible: false },
  { id: 'city', label: 'Cidade', type: 'string', defaultVisible: true },
  { id: 'state', label: 'Estado', type: 'string', defaultVisible: false },
  { id: 'country', label: 'País', type: 'string', defaultVisible: false },
  { id: 'clt_expectation', label: 'Expectativa salarial CLT', type: 'float', defaultVisible: false },
  { id: 'pj_expectation', label: 'Expectativa salarial PJ', type: 'float', defaultVisible: false },
  { id: 'freelance_expectation', label: 'Expectativa salarial Freelance', type: 'float', defaultVisible: false },
  { id: 'current_salary', label: 'Salário atual', type: 'float', defaultVisible: false },
  { id: 'desired_salary', label: 'Salário desejado', type: 'float', defaultVisible: false },
  { id: 'remote_work', label: 'Disponibilidade para trabalho remoto', type: 'boolean', defaultVisible: false },
  { id: 'mobility', label: 'Disponibilidade para mobilidade', type: 'boolean', defaultVisible: false },
  { id: 'source', label: 'Fonte de cadastro', type: 'string', defaultVisible: false },
  { id: 'completed_register', label: 'Cadastro completo', type: 'boolean', defaultVisible: false },
]

interface ColumnConfig {
  id: string
  label: string
  visible: boolean
  order: number
}

interface SavedView {
  id: string
  name: string
  columns: ColumnConfig[]
  createdAt: string
}

interface ColumnConfigurationModalProps {
  isOpen: boolean
  onClose: () => void
  currentColumns: ColumnConfig[]
  onSave: (columns: ColumnConfig[]) => void
  savedViews: SavedView[]
  onSaveView: (view: Omit<SavedView, 'id' | 'createdAt'>) => void
  onLoadView: (view: SavedView) => void
  onDeleteView: (viewId: string) => void
}

export function ColumnConfigurationModal({
  isOpen,
  onClose,
  currentColumns,
  onSave,
  savedViews,
  onSaveView,
  onLoadView,
  onDeleteView
}: ColumnConfigurationModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('column-configuration', isOpen)

  const [columns, setColumns] = useState<ColumnConfig[]>(currentColumns)
  const [searchTerm, setSearchTerm] = useState("")
  const [draggedItem, setDraggedItem] = useState<ColumnConfig | null>(null)
  const [newViewName, setNewViewName] = useState("")
  const [showSaveView, setShowSaveView] = useState(false)

  useEffect(() => {
    setColumns(currentColumns)
  }, [currentColumns, isOpen])

  const filteredColumns = columns.filter(col =>
    col.label.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleToggleColumn = (columnId: string) => {
    setColumns(prev => prev.map(col =>
      col.id === columnId ? { ...col, visible: !col.visible } : col
    ))
  }

  const handleDragStart = (e: React.DragEvent, column: ColumnConfig) => {
    setDraggedItem(column)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e: React.DragEvent, targetColumn: ColumnConfig) => {
    e.preventDefault()

    if (!draggedItem || draggedItem.id === targetColumn.id) return

    const newColumns = [...columns]
    const draggedIndex = newColumns.findIndex(col => col.id === draggedItem.id)
    const targetIndex = newColumns.findIndex(col => col.id === targetColumn.id)

    // Remove o item da posição original
    const [removed] = newColumns.splice(draggedIndex, 1)
    // Insere na nova posição
    newColumns.splice(targetIndex, 0, removed)

    // Atualiza as ordens
    const updatedColumns = newColumns.map((col, index) => ({
      ...col,
      order: index
    }))

    setColumns(updatedColumns)
    setDraggedItem(null)
  }

  const handleSave = () => {
    onSave(columns)
    onClose()
  }

  const handleReset = () => {
    // Reset para configuração padrão
    const defaultColumns = AVAILABLE_COLUMNS.map((col, index) => ({
      id: col.id,
      label: col.label,
      visible: col.defaultVisible,
      order: index
    }))
    setColumns(defaultColumns)
  }

  const handleSaveNewView = () => {
    if (newViewName.trim()) {
      onSaveView({
        name: newViewName.trim(),
        columns: columns
      })
      setNewViewName("")
      setShowSaveView(false)
    }
  }

  const visibleCount = columns.filter(col => col.visible).length

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="right" className="w-96 p-0">
        <div className="flex flex-col h-full">
          {/* Header */}
          <SheetHeader className="p-4 dark:border-lia-border-subtle">
            <SheetTitle className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Columns
            </SheetTitle>
            <div className="text-sm text-lia-text-secondary">
              {visibleCount} de {columns.length} colunas visíveis
            </div>
          </SheetHeader>

          {/* Search */}
          <div className="p-4 dark:border-lia-border-subtle">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-lia-text-muted" />
              <Input
                placeholder="Search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 h-9"
              />
            </div>
          </div>

          {/* Saved Views */}
          {savedViews.length > 0 && (
            <div className="p-4 dark:border-lia-border-subtle">
              <h4 className="text-sm font-medium text-lia-text-primary mb-2">Visualizações Salvas</h4>
              <div className="space-y-1">
                {savedViews.map(view => (
                  <div key={view.id} className="flex items-center justify-between p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <button
                      onClick={() => onLoadView(view)}
                      className="flex-1 text-left text-sm text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                    >
                      {view.name}
                    </button>
                    <button
                      onClick={() => onDeleteView(view.id)}
                      className="text-lia-text-disabled hover:text-status-error p-1"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Save New View */}
          <div className="p-4 dark:border-lia-border-subtle">
            {!showSaveView ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSaveView(true)}
                className="w-full"
              >
                Salvar Visualização Atual
              </Button>
            ) : (
              <div className="space-y-2">
                <Input
                  placeholder="Nome da visualização"
                  value={newViewName}
                  onChange={(e) => setNewViewName(e.target.value)}
                  className="h-8"
                />
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleSaveNewView} className="flex-1">
                    Salvar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setShowSaveView(false)
                      setNewViewName("")
                    }}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Columns List */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-1">
              {filteredColumns.map((column) => (
                <div
                  key={column.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, column)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, column)}
                  className={`flex items-center gap-3 p-2 rounded-md border-2 transition-colors motion-reduce:transition-none cursor-move ${
 column.visible
                      ? 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated border-lia-border-default dark:border-lia-border-default'
                      : 'bg-lia-bg-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle'
                  } hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse`}
                >
                  <GripVertical className="w-4 h-4 text-lia-text-muted" />

                  <button
                    onClick={() => handleToggleColumn(column.id)}
                    className="flex items-center gap-2 flex-1 text-left"
                  >
                    <div className={`w-4 h-4 rounded-md border flex items-center justify-center ${
 column.visible
                        ? 'bg-lia-btn-primary-bg border-lia-btn-primary-bg'
                        : 'border-lia-border-default dark:border-lia-border-default'
                    }`}>
                      {column.visible && (
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>

                    <span className={`text-sm ${
 column.visible ? 'text-lia-text-primary font-medium' : 'text-lia-text-secondary'
                    }`}>
                      {column.label}
                    </span>
                  </button>

                  {column.visible ? (
                    <Eye className="w-4 h-4 text-lia-text-primary" />
                  ) : (
                    <EyeOff className="w-4 h-4 text-lia-text-muted" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Footer Actions */}
          <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary">
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleReset}
                className="flex-1"
              >
                RESET
              </Button>
              <Button
                variant="outline"
                onClick={onClose}
                className="flex-1"
              >
                CANCEL
              </Button>
              <Button
                onClick={handleSave}
                className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
              >
                SAVE
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
