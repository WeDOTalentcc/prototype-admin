'use client'

import { useState } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Settings,
  Edit3,
  EyeOff,
  Trash2,
  ArrowLeft,
  ArrowRight,
  Clock,
  ExternalLink,
  Eye,
} from 'lucide-react'
import type { DynamicStage } from '../types'

type StageCategory = 'system' | 'default' | 'custom'

interface ColumnContextMenuProps {
  stage: DynamicStage
  stageCategory: StageCategory
  onRename: (stageId: string, newName: string) => void
  onToggleActive: (stageId: string, isActive: boolean) => void
  onRemove: (stageId: string) => void
  onMoveLeft: (stageId: string) => void
  onMoveRight: (stageId: string) => void
  onUpdateSLA: (stageId: string, slaHours: number) => void
  onOpenSettings: () => void
  canMoveLeft: boolean
  canMoveRight: boolean
}

const CATEGORY_PERMISSIONS: Record<StageCategory, {
  canRename: boolean
  canDeactivate: boolean
  canRemove: boolean
  canReorder: boolean
  canEditSLA: boolean
}> = {
  system: { canRename: false, canDeactivate: false, canRemove: false, canReorder: false, canEditSLA: false },
  default: { canRename: true, canDeactivate: true, canRemove: false, canReorder: true, canEditSLA: true },
  custom: { canRename: true, canDeactivate: true, canRemove: true, canReorder: true, canEditSLA: true },
}

export function ColumnContextMenu({
  stage,
  stageCategory,
  onRename,
  onToggleActive,
  onRemove,
  onMoveLeft,
  onMoveRight,
  onUpdateSLA,
  onOpenSettings,
  canMoveLeft,
  canMoveRight,
}: ColumnContextMenuProps) {
  const [renameOpen, setRenameOpen] = useState(false)
  const [slaOpen, setSlaOpen] = useState(false)
  const [confirmRemoveOpen, setConfirmRemoveOpen] = useState(false)
  const [newName, setNewName] = useState(stage.displayName)
  const [slaHours, setSlaHours] = useState(0)

  const permissions = CATEGORY_PERMISSIONS[stageCategory]
  const isActive = stage.isActive !== false

  const handleRename = () => {
    if (newName.trim() && newName !== stage.displayName) {
      onRename(stage.id, newName.trim())
    }
    setRenameOpen(false)
  }

  const handleSLAUpdate = () => {
    onUpdateSLA(stage.id, slaHours)
    setSlaOpen(false)
  }

  const handleRemove = () => {
    onRemove(stage.id)
    setConfirmRemoveOpen(false)
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="p-0.5 rounded-xl hover:bg-lia-interactive-active dark:hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none opacity-0 group-hover:opacity-100">
            <Settings className="w-3.5 h-3.5 text-lia-text-tertiary" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-48">
          {permissions.canRename && (
            <DropdownMenuItem onClick={() => { setNewName(stage.displayName); setRenameOpen(true) }}>
              <Edit3 className="w-3.5 h-3.5 mr-2" />
              <span className="text-xs">Renomear</span>
            </DropdownMenuItem>
          )}
          {permissions.canDeactivate && (
            <DropdownMenuItem onClick={() => onToggleActive(stage.id, !isActive)}>
              {isActive ? <EyeOff className="w-3.5 h-3.5 mr-2" /> : <Eye className="w-3.5 h-3.5 mr-2" />}
              <span className="text-xs">
                {isActive ? 'Desativar' : 'Ativar'}
              </span>
            </DropdownMenuItem>
          )}
          {permissions.canEditSLA && (
            <DropdownMenuItem onClick={() => setSlaOpen(true)}>
              <Clock className="w-3.5 h-3.5 mr-2" />
              <span className="text-xs">Configurar SLA</span>
            </DropdownMenuItem>
          )}
          {permissions.canReorder && (canMoveLeft || canMoveRight) && (
            <>
              <DropdownMenuSeparator />
              {canMoveLeft && (
                <DropdownMenuItem onClick={() => onMoveLeft(stage.id)}>
                  <ArrowLeft className="w-3.5 h-3.5 mr-2" />
                  <span className="text-xs">Mover para esquerda</span>
                </DropdownMenuItem>
              )}
              {canMoveRight && (
                <DropdownMenuItem onClick={() => onMoveRight(stage.id)}>
                  <ArrowRight className="w-3.5 h-3.5 mr-2" />
                  <span className="text-xs">Mover para direita</span>
                </DropdownMenuItem>
              )}
            </>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={onOpenSettings}>
            <ExternalLink className="w-3.5 h-3.5 mr-2" />
            <span className="text-xs">Ver configuracao completa</span>
          </DropdownMenuItem>
          {permissions.canRemove && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => setConfirmRemoveOpen(true)}
                className="text-status-error dark:text-status-error focus:text-status-error"
              >
                <Trash2 className="w-3.5 h-3.5 mr-2" />
                <span className="text-xs">Remover coluna</span>
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent className="sm:max-w-panel-lg bg-lia-bg-primary rounded-xl dark:bg-lia-bg-secondary">
          <DialogHeader>
            <DialogTitle className="text-sm font-semibold">
              Renomear Etapa
            </DialogTitle>
          </DialogHeader>
          <div className="py-3">
            <Label className="text-xs text-lia-text-secondary">
              Nome da etapa
            </Label>
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="mt-1.5 text-base-ui"
             
              onKeyDown={(e) => e.key === 'Enter' && handleRename()}
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenameOpen(false)} className="text-xs h-8">
              Cancelar
            </Button>
            <Button onClick={handleRename} className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text text-xs h-8 dark:hover:bg-lia-interactive-active">
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={slaOpen} onOpenChange={setSlaOpen}>
        <DialogContent className="sm:max-w-panel-lg bg-lia-bg-primary rounded-xl dark:bg-lia-bg-secondary">
          <DialogHeader>
            <DialogTitle className="text-sm font-semibold">
              Configurar SLA
            </DialogTitle>
          </DialogHeader>
          <div className="py-3">
            <Label className="text-xs text-lia-text-secondary">
              Prazo em horas
            </Label>
            <Input
              type="number"
              value={slaHours}
              onChange={(e) => setSlaHours(parseInt(e.target.value) || 0)}
              className="mt-1.5 text-base-ui"
             
              min={0}
              autoFocus
            />
            <p className="mt-1 text-xs text-lia-text-tertiary">
              Tempo maximo de permanencia nesta etapa
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSlaOpen(false)} className="text-xs h-8">
              Cancelar
            </Button>
            <Button onClick={handleSLAUpdate} className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text text-xs h-8 dark:hover:bg-lia-interactive-active">
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={confirmRemoveOpen} onOpenChange={setConfirmRemoveOpen}>
        <DialogContent className="sm:max-w-panel-lg bg-lia-bg-primary rounded-xl dark:bg-lia-bg-secondary">
          <DialogHeader>
            <DialogTitle className="text-sm font-semibold">
              Remover Coluna
            </DialogTitle>
          </DialogHeader>
          <div className="py-3">
            <p className="text-base-ui text-lia-text-primary">
              Tem certeza que deseja remover a coluna <strong>{stage.displayName}</strong>?
            </p>
            <p className="mt-2 text-xs text-lia-text-secondary">
              Candidatos nesta etapa serao movidos para a etapa anterior.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmRemoveOpen(false)} className="text-xs h-8">
              Cancelar
            </Button>
            <Button onClick={handleRemove} className="bg-status-error hover:bg-status-error text-white text-xs h-8">
              Remover
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
