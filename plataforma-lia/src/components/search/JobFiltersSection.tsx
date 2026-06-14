"use client"

import { useState } from"react"
import { X, ChevronRight, Save } from"lucide-react"
import { cn } from"@/lib/utils"
import { badgeStyles } from '@/lib/design-tokens'
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Chip } from "@/components/ui/chip"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import type { SearchFilters } from './hooks/useAdvancedFiltersCore'
import { globalJobPresets } from './advancedFiltersTypes'
import { JobTitlesSection } from './job-filters/JobTitlesSection'
import { PastTitlesSection } from './job-filters/PastTitlesSection'
import { TenureSection } from './job-filters/TenureSection'
import { JobLevelsAndRolesSection } from './job-filters/JobLevelsAndRolesSection'

export const JobFiltersSection = ({
  filters,
  updateFilter,
  addToArray,
  removeFromArray
}: {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
  addToArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
  removeFromArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
}) => {
  const [showPresetsModal, setShowPresetsModal] = useState(false)
  const [showSavePresetModal, setShowSavePresetModal] = useState(false)
  const [savePresetName, setSavePresetName] = useState("")
  const [savePresetDescription, setSavePresetDescription] = useState("")
  const [customPresets, setCustomPresets] = useState<Array<{id: string, name: string, description: string, titles: string[]}>>([])
  const [selectedPreset, setSelectedPreset] = useState<typeof globalJobPresets[0] | null>(null)
  const [presetTarget, setPresetTarget] = useState<"titles" |"pastTitles">("titles")

  const handleClearAllJobFilters = () => {
    updateFilter("job","titles", [] as string[])
    updateFilter("job","pastTitles", [] as string[])
    updateFilter("job","levels", [] as string[])
    updateFilter("job","roles", [] as string[])
    updateFilter("job","titleScope","current_only")
    updateFilter("job","timeInRoleMin","no_limit")
    updateFilter("job","timeInRoleMax","no_limit")
    updateFilter("job","minAverageTenure","no_limit")
  }

  const handleApplyPreset = (preset: typeof globalJobPresets[0], target:"titles" |"pastTitles" ="titles") => {
    const currentArray = target ==="titles" ? filters.job?.titles : filters.job?.pastTitles
    preset.titles.forEach(title => {
      if (!currentArray?.includes(title)) {
        addToArray("job", target, title)
      }
    })
    setShowPresetsModal(false)
    setSelectedPreset(null)
    setPresetTarget("titles")
  }

  const handleSavePreset = () => {
    const currentTitles = presetTarget ==="titles"
      ? (filters.job?.titles || [])
      : (filters.job?.pastTitles || [])
    if (currentTitles.length === 0 || !savePresetName.trim()) return

    const newPreset = {
      id: `custom_${Date.now()}`,
      name: savePresetName.trim(),
      description: savePresetDescription.trim() || `Preset com ${currentTitles.length} cargos`,
      titles: [...currentTitles]
    }

    setCustomPresets(prev => [...prev, newPreset])
    setSavePresetName("")
    setSavePresetDescription("")
    setShowSavePresetModal(false)
    setPresetTarget("titles")
  }

  const handleOpenPresetsModal = (target:"titles" |"pastTitles") => {
    setPresetTarget(target)
    setShowPresetsModal(true)
  }

  const handleOpenSavePresetModal = (target:"titles" |"pastTitles") => {
    setSavePresetName(`Novo Preset (${new Date().toLocaleDateString('pt-BR')})`)
    setPresetTarget(target)
    setShowSavePresetModal(true)
  }

  return (
    <div className="space-y-6">
      {/* Job Titles Section */}
      <JobTitlesSection
        filters={filters}
        updateFilter={updateFilter}
        addToArray={addToArray}
        removeFromArray={removeFromArray}
        onOpenPresetsModal={handleOpenPresetsModal}
        onOpenSavePresetModal={handleOpenSavePresetModal}
      />

      {/* Time in Role & Average Tenure */}
      <TenureSection
        filters={filters}
        updateFilter={updateFilter}
      />

      {/* Past Job Titles */}
      <PastTitlesSection
        filters={filters}
        updateFilter={updateFilter}
        addToArray={addToArray}
        removeFromArray={removeFromArray}
        onOpenPresetsModal={handleOpenPresetsModal}
        onOpenSavePresetModal={handleOpenSavePresetModal}
      />

      {/* Job Title Levels & Roles */}
      <JobLevelsAndRolesSection
        filters={filters}
        addToArray={addToArray}
        removeFromArray={removeFromArray}
      />

      {/* Presets Modal */}
      {showPresetsModal && (
        <div className="fixed inset-0 z-overlay flex items-center justify-center">
          <div className="absolute inset-0 bg-lia-overlay backdrop-blur-[1px]" onClick={() => { setShowPresetsModal(false); setSelectedPreset(null) }} />
          <div className="relative bg-lia-bg-primary rounded-xl w-full max-w-lg max-h-[70vh] overflow-hidden dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
            <div className="flex items-center justify-between p-4 dark:border-lia-border-subtle">
              <div className="flex items-center gap-2">
                {selectedPreset && (
                  <button
                    onClick={() => setSelectedPreset(null)}
                    className="text-lia-text-secondary hover:text-lia-text-primary"
                  >
                    <ChevronRight className="w-4 h-4 rotate-180" />
                  </button>
                )}
                <h3 className="font-medium text-lia-text-primary">
                  {selectedPreset ? `${selectedPreset.name} (${selectedPreset.titles.length})` :"Presets de Cargos"}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                {selectedPreset && (
                  <>
                    <Select
                      value={presetTarget}
                      onValueChange={(value) => setPresetTarget(value as"titles" |"pastTitles")}
                    >
                      <SelectTrigger className="h-8 w-[140px] text-xs border-lia-border-subtle">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-lia-bg-secondary">
                        <SelectItem value="titles" className="text-xs">Cargos Atuais</SelectItem>
                        <SelectItem value="pastTitles" className="text-xs">Cargos Anteriores</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      size="sm"
                      onClick={() => handleApplyPreset(selectedPreset, presetTarget)}
                      className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                    >
                      Aplicar Preset
                    </Button>
                  </>
                )}
                <button onClick={() => { setShowPresetsModal(false); setSelectedPreset(null); setPresetTarget("titles") }} className="text-lia-text-tertiary hover:text-lia-text-secondary">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-4 overflow-y-auto max-h-[calc(70vh-60px)]">
              {!selectedPreset ? (
                <div className="space-y-4">
                  {/* Custom Presets */}
                  {customPresets.length > 0 && (
                    <div>
                      <h4 className="text-xs font-medium text-lia-text-primary mb-2">Meus Presets</h4>
                      <p className="text-xs text-lia-text-secondary mb-3">Presets criados por você</p>
                      <div className="space-y-2">
                        {customPresets.map(preset => (
                          <button
                            key={preset.id}
                            onClick={() => setSelectedPreset(preset)}
                            className="w-full text-left p-3 rounded-xl border border-wedo-purple/30 hover:border-wedo-purple/30 hover:bg-wedo-purple/10/50 transition-colors motion-reduce:transition-none"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="font-medium text-xs text-lia-text-primary flex items-center gap-1.5">
                                  <Save className="w-3.5 h-3.5 text-wedo-purple" />
                                  {preset.name}
                                </div>
                                <div className="text-xs text-lia-text-secondary mt-0.5">{preset.description}</div>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-wedo-purple-text">+{preset.titles.length} cargos</span>
                                <ChevronRight className="w-4 h-4 text-lia-text-tertiary" />
                              </div>
                            </div>
                            <div className="flex flex-wrap gap-1 mt-2">
                              {preset.titles.slice(0, 3).map(title => (
                                <span key={title} className="text-micro px-1.5 py-0.5 bg-wedo-purple/15 rounded-full text-wedo-purple-text">
                                  {title}
                                </span>
                              ))}
                              {preset.titles.length > 3 && (
                                <span className="text-micro text-wedo-purple-text">...</span>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Global Presets */}
                  <div>
                    <h4 className="text-xs font-medium text-lia-text-primary mb-2">Presets Globais</h4>
                    <p className="text-xs text-lia-text-secondary mb-3">Conjuntos pré-definidos de cargos por área</p>
                    <div className="space-y-2">
                      {globalJobPresets.map(preset => (
                        <button
                          key={preset.id}
                          onClick={() => setSelectedPreset(preset)}
                          className="w-full text-left p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-subtle hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-medium text-xs text-lia-text-primary">{preset.name}</div>
                              <div className="text-xs text-lia-text-secondary mt-0.5">{preset.description}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-lia-text-tertiary">+{preset.titles.length} cargos</span>
                              <ChevronRight className="w-4 h-4 text-lia-text-tertiary" />
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {preset.titles.slice(0, 3).map(title => (
                              <span key={title} className="text-micro px-1.5 py-0.5 bg-lia-bg-tertiary rounded-full text-lia-text-secondary">
                                {title}
                              </span>
                            ))}
                            {preset.titles.length > 3 && (
                              <span className="text-micro text-lia-text-tertiary">...</span>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {selectedPreset.titles.map(title => (
                    <span key={title} className="px-3 py-1.5 bg-lia-bg-tertiary rounded-xl text-xs text-lia-text-primary">
                      {title}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Save Preset Modal */}
      {showSavePresetModal && (
        <div className="fixed inset-0 z-overlay flex items-center justify-center">
          <div className="absolute inset-0 bg-lia-overlay backdrop-blur-[1px]" onClick={() => setShowSavePresetModal(false)} />
          <div className="relative bg-lia-bg-primary rounded-xl w-full max-w-md p-4 dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
            <h3 className="font-medium text-lia-text-primary mb-4">Salvar como Preset</h3>

            <div className="space-y-4">
              <div>
                <Label className="text-xs font-medium text-lia-text-secondary mb-1 block">Nome do Preset</Label>
                <Input
                  value={savePresetName}
                  onChange={(e) => setSavePresetName(e.target.value)}
                  placeholder="Ex: Product Managers"
                  className="border border-lia-border-subtle"
                />
              </div>

              <div>
                <Label className="text-xs font-medium text-lia-text-secondary mb-1 block">Descrição</Label>
                <Input
                  value={savePresetDescription}
                  onChange={(e) => setSavePresetDescription(e.target.value)}
                  placeholder="Descrição opcional"
                  className="border border-lia-border-subtle"
                />
              </div>

              <div className="p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="text-xs text-lia-text-secondary mb-2">
                  {(presetTarget ==="titles" ? filters.job?.titles?.length : filters.job?.pastTitles?.length) || 0} cargos {presetTarget ==="pastTitles" ?"anteriores" :""}serão salvos:
                </div>
                <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                  {(presetTarget ==="titles" ? filters.job?.titles : filters.job?.pastTitles)?.slice(0, 10).map(title => (
                    <span key={title} className="text-micro px-1.5 py-0.5 bg-lia-interactive-active rounded-full text-lia-text-primary">
                      {title}
                    </span>
                  ))}
                  {((presetTarget ==="titles" ? filters.job?.titles?.length : filters.job?.pastTitles?.length) || 0) > 10 && (
                    <span className="text-micro text-lia-text-tertiary">+{((presetTarget ==="titles" ? filters.job?.titles?.length : filters.job?.pastTitles?.length) || 0) - 10} mais</span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => { setShowSavePresetModal(false); setPresetTarget("titles") }}
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleSavePreset}
                disabled={!savePresetName.trim() || ((presetTarget ==="titles" ? filters.job?.titles?.length : filters.job?.pastTitles?.length) || 0) === 0}
                className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
              >
                <Save className="w-3.5 h-3.5 mr-1.5" />
                Salvar Preset
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const TagInput = ({
  value = [],
  onAdd,
  onRemove,
  placeholder
}: {
  value: string[]
  onAdd: (val: string) => void
  onRemove: (val: string) => void
  placeholder: string
}) => {
  const [inputValue, setInputValue] = useState("")

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key ==="Enter" && inputValue.trim()) {
      e.preventDefault()
      onAdd(inputValue)
      setInputValue("")
    }
  }

  return (
    <div className="space-y-2">
      <Input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="border border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium"
      />
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {value.map((item) => (
            <Chip
              key={item}
              variant="neutral" muted
              className={`${badgeStyles.default} pl-2 pr-1 py-1 flex items-center gap-1`}
            >
              {item}
              <button
                onClick={() => onRemove(item)}
                className="ml-1 hover:bg-lia-border-default rounded-md p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </Chip>
          ))}
        </div>
      )}
    </div>
  )
}
