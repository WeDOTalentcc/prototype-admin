"use client"

import { useState, useEffect, type ReactNode } from"react"
import { X, Search, Plus, Trash2 } from"lucide-react"
import { cn } from"@/lib/utils"
import { Input } from"@/components/ui/input"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Label } from"@/components/ui/label"
import { useUIPreferencesStore } from"@/stores/ui-preferences-store"

export interface SearchPreset<T> {
  id: string
  name: string
  description: string
  items: T[]
  isOrganization?: boolean
}

export interface SearchPresetsModalConfig<T> {
  title: string
  itemLabel: string
  generalPresets: SearchPreset<T>[]
  localStorageKey?: string
  parseStoredPresets?: (raw: unknown[]) => SearchPreset<T>[]
  getPreviewText?: (items: T[]) => string
  renderItemBadges?: (items: T[]) => ReactNode
  saveFormPosition?:"inline" |"footer"
  generalTabSubtitle?: string
}

interface SearchPresetsModalProps<T> {
  isOpen: boolean
  onClose: () => void
  onSelectPreset: (items: T[]) => void
  organizationPresets?: SearchPreset<T>[]
  onSavePreset?: (preset: { name: string; description: string }) => void
  config: SearchPresetsModalConfig<T>
}

export function SearchPresetsModal<T>({
  isOpen,
  onClose,
  onSelectPreset,
  organizationPresets = [],
  onSavePreset,
  config,
}: SearchPresetsModalProps<T>) {
  const {
    title,
    itemLabel,
    generalPresets,
    localStorageKey,
    parseStoredPresets,
    getPreviewText,
    renderItemBadges,
    saveFormPosition ="inline",
    generalTabSubtitle,
  } = config

  const hasCustomTab = !!localStorageKey

  type TabType ="organization" |"general" |"custom"
  const [searchQuery, setSearchQuery] = useState("")
  const [activeTab, setActiveTab] = useState<TabType>("general")
  const [showSaveForm, setShowSaveForm] = useState(false)
  const [newPresetName, setNewPresetName] = useState("")
  const [newPresetDescription, setNewPresetDescription] = useState("")
  const [customPresets, setCustomPresets] = useState<SearchPreset<T>[]>([])

  const { getCustomPresets, setCustomPresets: setCustomPresetsInStore } = useUIPreferencesStore()

  useEffect(() => {
    if (isOpen && localStorageKey && parseStoredPresets) {
      try {
        const stored = getCustomPresets(localStorageKey)
        if (stored.length > 0) {
          setCustomPresets(parseStoredPresets(stored))
        }
      } catch {
      }
    }
  }, [isOpen, localStorageKey, parseStoredPresets, getCustomPresets])

  const handleDeleteCustomPreset = (presetId: string) => {
    if (!localStorageKey) return
    try {
      const stored = getCustomPresets(localStorageKey)
      const filtered = stored.filter((p: unknown) => (p as { id: string }).id !== presetId)
      setCustomPresetsInStore(localStorageKey, filtered)
      setCustomPresets(prev => prev.filter(p => p.id !== presetId))
    } catch {
    }
  }

  if (!isOpen) return null

  const lowerQuery = searchQuery.toLowerCase()
  const filterPresets = (presets: SearchPreset<T>[]) =>
    presets.filter(
      p =>
        p.name.toLowerCase().includes(lowerQuery) ||
        p.description.toLowerCase().includes(lowerQuery)
    )

  const filteredGeneralPresets = filterPresets(generalPresets)
  const filteredOrgPresets = filterPresets(organizationPresets)
  const filteredCustomPresets = filterPresets(customPresets)

  const handleSavePreset = () => {
    if (onSavePreset && newPresetName.trim()) {
      onSavePreset({
        name: newPresetName.trim(),
        description: newPresetDescription.trim(),
      })
      setNewPresetName("")
      setNewPresetDescription("")
      setShowSaveForm(false)
    }
  }

  const handleSelectAndClose = (items: T[]) => {
    onSelectPreset(items)
    onClose()
  }

  const tabClasses = (isActive: boolean) =>
    cn("flex-1 px-4 py-2.5 text-sm font-medium transition-colors",
      isActive
        ?"text-lia-text-primary rounded-lg bg-lia-bg-tertiary dark:border-lia-border-subtle"
        :"text-lia-text-secondary hover:text-lia-text-primary"
    )

  const cardClasses ="w-full text-left p-3 rounded-md border border-lia-border-subtle hover:border-lia-border-medium hover:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:border-lia-border-medium dark:hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none"

  const renderStandardCard = (preset: SearchPreset<T>) => (
    <>
      <div className="flex items-start justify-between">
        <div>
          <div className="font-medium text-sm text-lia-text-primary">
            {preset.name}
          </div>
          <div className="text-xs text-lia-text-secondary mt-0.5">
            {preset.description}
          </div>
        </div>
        <Chip variant="neutral" muted className="text-micro bg-lia-bg-tertiary text-lia-text-secondary">
          {preset.items.length} {itemLabel}
        </Chip>
      </div>
      {renderItemBadges?.(preset.items)}
    </>
  )

  const renderGeneralCard = (preset: SearchPreset<T>) => {
    if (getPreviewText) {
      return (
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium text-sm text-lia-text-primary">
                {preset.name}
              </span>
              <span className="text-xs text-lia-text-tertiary">
                ({getPreviewText(preset.items)})
              </span>
            </div>
            <div className="text-xs text-lia-text-secondary mt-0.5 line-clamp-1">
              {preset.description}
            </div>
          </div>
        </div>
      )
    }
    return renderStandardCard(preset)
  }

  const savePlaceholder = `My ${title.replace(" Presets","")} Preset`

  const renderInlineSaveForm = () => (
    <div className="mt-4 p-4 border border-lia-border-subtle rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
      <h3 className="text-sm font-medium text-lia-text-primary mb-3">Save as Preset</h3>
      <div className="space-y-3">
        <div>
          <Label className="text-xs">Preset Name</Label>
          <Input
            value={newPresetName}
            onChange={e => setNewPresetName(e.target.value)}
            placeholder={savePlaceholder}
            className="mt-1"
          />
        </div>
        <div>
          <Label className="text-xs">Description</Label>
          <Input
            value={newPresetDescription}
            onChange={e => setNewPresetDescription(e.target.value)}
            placeholder="Descrição desta predefinição..."
            className="mt-1"
          />
        </div>
        <div className="flex gap-2 justify-end">
          <Button variant="outline" size="sm" onClick={() => setShowSaveForm(false)}>
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={handleSavePreset}
            disabled={!newPresetName.trim()}
            className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            Save Preset
          </Button>
        </div>
      </div>
    </div>
  )

  const renderFooterSaveForm = () => (
    <div className="px-4 py-3 border-t border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary dark:border-lia-border-subtle">
      <Label className="text-xs font-medium text-lia-text-primary">
        Create New Preset
      </Label>
      <div className="flex gap-2 mt-2">
        <Input
          value={newPresetName}
          onChange={e => setNewPresetName(e.target.value)}
          placeholder="Nome da predefinição"
          className="text-sm"
        />
        <Input
          value={newPresetDescription}
          onChange={e => setNewPresetDescription(e.target.value)}
          placeholder="Description"
          className="text-sm"
        />
        <Button
          size="sm"
          onClick={handleSavePreset}
          disabled={!newPresetName.trim()}
          className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
        >
          Save
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setShowSaveForm(false)
            setNewPresetName("")
            setNewPresetDescription("")
          }}
        >
          Cancel
        </Button>
      </div>
    </div>
  )

  return (
    <div className="fixed inset-0 bg-lia-overlay backdrop-blur-[1px] z-overlay flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <div className="flex items-center justify-between px-4 py-3 dark:border-lia-border-subtle">
          <h2 className="text-base font-semibold text-lia-text-primary">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-lia-bg-tertiary rounded-xl transition-colors motion-reduce:transition-none"
          >
            <X className="w-5 h-5 text-lia-text-secondary" />
          </button>
        </div>

        <div className="px-4 py-3 dark:border-lia-border-subtle">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
            <Input
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Buscar predefinições..."
              className="pl-9 text-sm"
            />
          </div>
        </div>

        <div className="flex dark:border-lia-border-subtle">
          {hasCustomTab && customPresets.length > 0 && (
            <button
              onClick={() => setActiveTab("custom")}
              className={tabClasses(activeTab ==="custom")}
            >
              Meus Presets ({customPresets.length})
            </button>
          )}
          <button
            onClick={() => setActiveTab("organization")}
            className={tabClasses(activeTab ==="organization")}
          >
            Organization Presets
          </button>
          <button
            onClick={() => setActiveTab("general")}
            className={tabClasses(activeTab ==="general")}
          >
            General Presets ({generalPresets.length})
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {activeTab ==="custom" ? (
            <div className="space-y-4">
              <p className="text-xs text-lia-text-secondary">Presets que você salvou</p>

              {filteredCustomPresets.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-lia-text-secondary">
                    Nenhum preset salvo encontrado
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredCustomPresets.map(preset => (
                    <div
                      key={preset.id}
                      className={cn(cardClasses,"group cursor-default")}
                    >
                      <div className="flex items-start justify-between">
                        <button
                          onClick={() => handleSelectAndClose(preset.items)}
                          className="flex-1 text-left"
                        >
                          <div className="font-medium text-sm text-lia-text-primary">
                            {preset.name}
                          </div>
                          <div className="text-xs text-lia-text-secondary mt-0.5">
                            {preset.description}
                          </div>
                        </button>
                        <div className="flex items-center gap-2">
                          <Chip variant="neutral" muted className="text-micro bg-lia-bg-tertiary text-lia-text-secondary">
                            {preset.items.length} {itemLabel}
                          </Chip>
                          <button
                            onClick={e => {
                              e.stopPropagation()
                              handleDeleteCustomPreset(preset.id)
                            }}
                            className="p-1 opacity-0 group-hover:opacity-100 hover:bg-status-error/10 rounded-md transition-colors motion-reduce:transition-none"
                            title="Excluir preset"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-status-error" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : activeTab ==="organization" ? (
            <div className="space-y-4">
              <p className="text-xs text-lia-text-secondary">
                Presets created by you and your team members
              </p>

              {filteredOrgPresets.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-lia-text-secondary">
                    {searchQuery
                      ?"No organization presets match your search"
                      :"No presets found, please create a new preset"}
                  </p>
                  {onSavePreset && !searchQuery && (
                    <Button
                      onClick={() => setShowSaveForm(true)}
                      className="mt-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Create New Preset
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredOrgPresets.map(preset => (
                    <button
                      key={preset.id}
                      onClick={() => handleSelectAndClose(preset.items)}
                      className={cardClasses}
                    >
                      {renderStandardCard(preset)}
                    </button>
                  ))}
                </div>
              )}

              {showSaveForm && saveFormPosition ==="inline" && renderInlineSaveForm()}
            </div>
          ) : (
            <div className="space-y-4">
              {generalTabSubtitle && (
                <p className="text-xs text-lia-text-secondary">{generalTabSubtitle}</p>
              )}

              <div className="space-y-2">
                {filteredGeneralPresets.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => handleSelectAndClose(preset.items)}
                    className={cardClasses}
                  >
                    {renderGeneralCard(preset)}
                  </button>
                ))}
              </div>

              {filteredGeneralPresets.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-sm text-lia-text-secondary">No presets match your search</p>
                </div>
              )}
            </div>
          )}
        </div>

        {showSaveForm && onSavePreset && saveFormPosition ==="footer" && renderFooterSaveForm()}
      </div>
    </div>
  )
}
