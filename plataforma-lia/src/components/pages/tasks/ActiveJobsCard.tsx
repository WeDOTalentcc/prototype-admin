"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { Search, SlidersHorizontal, ArrowUpDown, X } from"lucide-react"
import { JobListItem } from"./JobListItem"
import type { JobWithAlert } from"../use-tasks-core"

interface ActiveJobsCardProps {
  filteredAndSortedJobs: JobWithAlert[]
  jobSearchTerm: string
  setJobSearchTerm: (term: string) => void
  showJobFilters: boolean
  setShowJobFilters: (show: boolean) => void
  activeJobFiltersCount: number
  jobSortBy: string
  setJobSortBy: (sort: 'daysOpen' | 'candidates' | 'urgency') => void
  selectedDepartments: string[]
  setSelectedDepartments: (deps: string[]) => void
  selectedUrgencies: string[]
  setSelectedUrgencies: (urgs: string[]) => void
  selectedPublications: string[]
  setSelectedPublications: (pubs: string[]) => void
  uniqueDepartments: string[]
  clearJobFilters: () => void
  handleLIAAction: (action: string, job: JobWithAlert) => void
  onNavigate?: (page: string) => void
}

export function ActiveJobsCard({
  filteredAndSortedJobs,
  jobSearchTerm,
  setJobSearchTerm,
  showJobFilters,
  setShowJobFilters,
  activeJobFiltersCount,
  jobSortBy,
  setJobSortBy,
  selectedDepartments,
  setSelectedDepartments,
  selectedUrgencies,
  setSelectedUrgencies,
  selectedPublications,
  setSelectedPublications,
  uniqueDepartments,
  clearJobFilters,
  handleLIAAction,
  onNavigate,
}: ActiveJobsCardProps) {
  return (
    <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-open-sans font-semibold text-lia-text-primary">Minhas Vagas Ativas</CardTitle>
          <div className="flex items-center gap-2">
            <Chip density="relaxed" variant="neutral" className="font-sans">
              {filteredAndSortedJobs.length} vaga{filteredAndSortedJobs.length !== 1 ? 's' : ''}
            </Chip>
          </div>
        </div>

        <div className="mt-3 space-y-2">
          <div className="flex items-center gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-tertiary" />
              <Input
                placeholder="Buscar vagas por título, ID, gestor ou departamento..."
                value={jobSearchTerm}
                onChange={(e) => setJobSearchTerm(e.target.value)}
                className="pl-8 h-8 text-xs"
              />
              {jobSearchTerm && (
                <button
                  onClick={() => setJobSearchTerm("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                  aria-label="Limpar busca"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            <Button
              variant={showJobFilters || activeJobFiltersCount > 0 ?"primary" :"outline"}
              size="sm"
              onClick={() => setShowJobFilters(!showJobFilters)}
              className="gap-1.5 h-8 px-3 text-xs"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              Filtros
              {activeJobFiltersCount > 0 && (
                <Chip density="relaxed" variant="neutral" muted className="ml-1 bg-lia-bg-primary text-lia-text-primary dark:bg-lia-bg-secondary h-4 px-1">
                  {activeJobFiltersCount}
                </Chip>
              )}
            </Button>

            <SortDropdown jobSortBy={jobSortBy} setJobSortBy={setJobSortBy} />
          </div>

          {showJobFilters && (
            <JobFiltersPanel
              selectedDepartments={selectedDepartments}
              setSelectedDepartments={setSelectedDepartments}
              selectedUrgencies={selectedUrgencies}
              setSelectedUrgencies={setSelectedUrgencies}
              selectedPublications={selectedPublications}
              setSelectedPublications={setSelectedPublications}
              uniqueDepartments={uniqueDepartments}
              activeJobFiltersCount={activeJobFiltersCount}
              clearJobFilters={clearJobFilters}
            />
          )}

          {activeJobFiltersCount > 0 && (
            <ActiveFilterTags
              selectedDepartments={selectedDepartments}
              setSelectedDepartments={setSelectedDepartments}
              selectedUrgencies={selectedUrgencies}
              setSelectedUrgencies={setSelectedUrgencies}
              selectedPublications={selectedPublications}
              setSelectedPublications={setSelectedPublications}
            />
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {filteredAndSortedJobs.length === 0 ? (
          <div className="text-center py-8">
            <Search className="w-16 h-16 mx-auto text-lia-text-disabled mb-4" />
            <p className="text-base font-medium text-lia-text-primary mb-1">Nenhuma vaga encontrada</p>
            <p className="text-sm text-lia-text-secondary">
              Tente ajustar os filtros ou buscar por outros termos
            </p>
            {activeJobFiltersCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearJobFilters}
                className="mt-3 text-xs"
              >
                Limpar filtros
              </Button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredAndSortedJobs.map((job) => (
              <JobListItem
                key={job.id}
                job={job}
                onLIAAction={handleLIAAction}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

type SortOption = 'daysOpen' | 'candidates' | 'urgency'

function SortDropdown({ jobSortBy, setJobSortBy }: { jobSortBy: string; setJobSortBy: (s: SortOption) => void }) {
  const options: { value: SortOption; label: string }[] = [
    { value: 'urgency', label: 'Por Urgência' },
    { value: 'daysOpen', label: 'Por Dias em Aberto' },
    { value: 'candidates', label: 'Por Nº Candidatos' },
  ]

  return (
    <div className="relative group">
      <Button variant="outline" size="sm" className="gap-1.5 h-8 px-3 text-xs">
        <ArrowUpDown className="w-3.5 h-3.5" />
        Ordenar
      </Button>
      <div className="absolute right-0 top-full mt-1 w-40 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity motion-reduce:transition-none duration-200 z-10">
        <div className="py-1">
          {options.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setJobSortBy(value)}
              className={`w-full px-3 py-1.5 text-left text-xs hover:bg-lia-interactive-hover transition-colors ${
                jobSortBy === value ? 'bg-lia-interactive-active text-lia-text-primary dark:bg-lia-bg-elevated font-semibold' : ''
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function CheckboxFilter({
  items,
  selected,
  setSelected,
}: {
  items: { id: string; label: string }[]
  selected: string[]
  setSelected: (items: string[]) => void
}) {
  return (
    <div className="space-y-1">
      {items.map(item => (
        <label key={item.id} className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={selected.includes(item.id)}
            onChange={(e) => {
              if (e.target.checked) {
                setSelected([...selected, item.id])
              } else {
                setSelected(selected.filter(s => s !== item.id))
              }
            }}
            className="w-4 h-4 rounded-sm border-lia-border-default accent-lia-btn-primary-bg focus:ring-2 focus:ring-lia-btn-primary-bg/20"
          />
          <span className="text-xs text-lia-text-primary">{item.label}</span>
        </label>
      ))}
    </div>
  )
}

function JobFiltersPanel({
  selectedDepartments, setSelectedDepartments,
  selectedUrgencies, setSelectedUrgencies,
  selectedPublications, setSelectedPublications,
  uniqueDepartments, activeJobFiltersCount, clearJobFilters,
}: {
  selectedDepartments: string[]; setSelectedDepartments: (d: string[]) => void
  selectedUrgencies: string[]; setSelectedUrgencies: (u: string[]) => void
  selectedPublications: string[]; setSelectedPublications: (p: string[]) => void
  uniqueDepartments: string[]; activeJobFiltersCount: number; clearJobFilters: () => void
}) {
  return (
    <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-lg p-3 space-y-3 border border-lia-border-subtle dark:border-lia-border-subtle">
      <div className="flex items-center justify-between">
        <span className="text-xs font-open-sans font-semibold text-lia-text-primary">Filtros Avançados</span>
        {activeJobFiltersCount > 0 && (
          <button
            onClick={clearJobFilters}
            className="text-xs text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-inverse flex items-center gap-1"
          >
            <X className="w-3 h-3" />
            Limpar filtros
          </button>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs font-open-sans font-medium text-lia-text-primary mb-1.5 block">Departamento</label>
          <CheckboxFilter
            items={uniqueDepartments.map(d => ({ id: d, label: d }))}
            selected={selectedDepartments}
            setSelected={setSelectedDepartments}
          />
        </div>
        <div>
          <label className="text-xs font-open-sans font-medium text-lia-text-primary mb-1.5 block">Urgência</label>
          <CheckboxFilter
            items={[
              { id: 'critical', label: 'Crítico' },
              { id: 'urgent', label: 'Urgente' },
              { id: 'normal', label: 'Normal' },
            ]}
            selected={selectedUrgencies}
            setSelected={setSelectedUrgencies}
          />
        </div>
        <div>
          <label className="text-xs font-open-sans font-medium text-lia-text-primary mb-1.5 block">Publicado em</label>
          <CheckboxFilter
            items={[
              { id: 'linkedin', label: 'LinkedIn' },
              { id: 'site', label: 'Site' },
              { id: 'indeed', label: 'Indeed' },
            ]}
            selected={selectedPublications}
            setSelected={setSelectedPublications}
          />
        </div>
      </div>
    </div>
  )
}

function ActiveFilterTags({
  selectedDepartments, setSelectedDepartments,
  selectedUrgencies, setSelectedUrgencies,
  selectedPublications, setSelectedPublications,
}: {
  selectedDepartments: string[]; setSelectedDepartments: (d: string[]) => void
  selectedUrgencies: string[]; setSelectedUrgencies: (u: string[]) => void
  selectedPublications: string[]; setSelectedPublications: (p: string[]) => void
}) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs text-lia-text-primary">Filtros ativos:</span>
      {selectedDepartments.map(dept => (
        <Chip density="relaxed" key={dept} variant="neutral" muted className="flex items-center gap-1 pr-1">
          {dept}
          <button onClick={() => setSelectedDepartments(selectedDepartments.filter(d => d !== dept))} className="hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full p-0.5" aria-label="Remover filtro">
            <X className="w-2.5 h-2.5" />
          </button>
        </Chip>
      ))}
      {selectedUrgencies.map(urgency => (
        <Chip density="relaxed" key={urgency} variant="neutral" muted className="flex items-center gap-1 pr-1">
          {urgency === 'critical' ? 'Crítico' : urgency === 'urgent' ? 'Urgente' : 'Normal'}
          <button onClick={() => setSelectedUrgencies(selectedUrgencies.filter(u => u !== urgency))} className="hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full p-0.5" aria-label="Remover filtro">
            <X className="w-2.5 h-2.5" />
          </button>
        </Chip>
      ))}
      {selectedPublications.map(pub => (
        <Chip density="relaxed" key={pub} variant="neutral" muted className="flex items-center gap-1 pr-1">
          {pub === 'linkedin' ? 'LinkedIn' : pub === 'site' ? 'Site' : 'Indeed'}
          <button onClick={() => setSelectedPublications(selectedPublications.filter(p => p !== pub))} className="hover:bg-lia-border-default dark:hover:bg-lia-border-medium rounded-full p-0.5" aria-label="Remover filtro">
            <X className="w-2.5 h-2.5" />
          </button>
        </Chip>
      ))}
    </div>
  )
}
