"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { X, MapPin, Brain, Code, CheckCircle, Bookmark, Calendar } from "lucide-react"
import { badgeStyles, textStyles } from "@/lib/design-tokens"
import { TriStateButtons } from "./filters/TriStateButtons"
import type { TableFilters } from "./types"

export interface FilterSectionsAdvancedProps {
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  newSoftSkillFilter: string
  setNewSoftSkillFilter: (v: string) => void
  newCertificationFilter: string
  setNewCertificationFilter: (v: string) => void
  onClearAll: () => void
}

export function FilterSectionsAdvanced({
  tableFilters,
  setTableFilters,
  newSoftSkillFilter,
  setNewSoftSkillFilter,
  newCertificationFilter,
  setNewCertificationFilter,
  onClearAll,
}: FilterSectionsAdvancedProps) {
  return (
    <>
      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Brain className="w-3 h-3 text-wedo-cyan" />
          Soft Skills
        </h4>
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              value={newSoftSkillFilter}
              onChange={(e) => setNewSoftSkillFilter(e.target.value)}
              placeholder="Ex: comunicação, liderança..."
              className="h-8 text-xs"
              onKeyDown={(e) => {
                if (e.key === "Enter" && newSoftSkillFilter.trim()) {
                  if (!tableFilters.softSkills.includes(newSoftSkillFilter.trim())) {
                    setTableFilters((prev) => ({
                      ...prev,
                      softSkills: [...prev.softSkills, newSoftSkillFilter.trim()],
                    }))
                  }
                  setNewSoftSkillFilter("")
                }
              }}
            />
          </div>
          {tableFilters.softSkills.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {tableFilters.softSkills.map((skill) => (
                <Badge key={skill} variant="secondary" className={`${badgeStyles.default} px-2 py-0.5 flex items-center gap-1`}>
                  {skill}
                  <button
                    onClick={() =>
                      setTableFilters((prev) => ({
                        ...prev,
                        softSkills: prev.softSkills.filter((s) => s !== skill),
                      }))
                    }
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Code className="w-3 h-3" />
          Certificações
        </h4>
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              value={newCertificationFilter}
              onChange={(e) => setNewCertificationFilter(e.target.value)}
              placeholder="Ex: AWS, PMP, Scrum..."
              className="h-8 text-xs"
              onKeyDown={(e) => {
                if (e.key === "Enter" && newCertificationFilter.trim()) {
                  if (!tableFilters.certifications.includes(newCertificationFilter.trim())) {
                    setTableFilters((prev) => ({
                      ...prev,
                      certifications: [...prev.certifications, newCertificationFilter.trim()],
                    }))
                  }
                  setNewCertificationFilter("")
                }
              }}
            />
          </div>
          {tableFilters.certifications.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {tableFilters.certifications.map((cert) => (
                <Badge key={cert} variant="secondary" className={`${badgeStyles.default} px-2 py-0.5 flex items-center gap-1`}>
                  {cert}
                  <button
                    onClick={() =>
                      setTableFilters((prev) => ({
                        ...prev,
                        certifications: prev.certifications.filter((c) => c !== cert),
                      }))
                    }
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <MapPin className="w-3 h-3" />
          Disponibilidade
        </h4>
        <div className="space-y-3">
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>Aberto a mudar</label>
            <TriStateButtons
              value={tableFilters.willingToRelocate}
              onChange={(v) => setTableFilters((prev) => ({ ...prev, willingToRelocate: v }))}
            />
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>Mobilidade</label>
            <TriStateButtons
              value={tableFilters.mobility}
              onChange={(v) => setTableFilters((prev) => ({ ...prev, mobility: v }))}
            />
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>Disponibilidade</label>
            <div className="grid grid-cols-2 gap-1.5">
              {[
                { value: "immediate", label: "Imediato" },
                { value: "15_days", label: "15 dias" },
                { value: "30_days", label: "30 dias" },
                { value: "60_days", label: "60 dias" },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() =>
                    setTableFilters((prev) => ({
                      ...prev,
                      availabilityWindow:
                        prev.availabilityWindow === opt.value
                          ? undefined
                          : (opt.value as TableFilters["availabilityWindow"]),
                    }))
                  }
                  className="px-2 py-1.5 text-micro rounded-md transition-colors motion-reduce:transition-none"
                  style={{backgroundColor:
                      tableFilters.availabilityWindow === opt.value ? "var(--lia-btn-primary-bg)" : "var(--lia-bg-secondary)",
                    color: tableFilters.availabilityWindow === opt.value ? "white" : "var(--lia-text-secondary)",
                    border:
                      tableFilters.availabilityWindow === opt.value
                        ? "none"
                        : "1px solid var(--lia-border-subtle)"}}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Bookmark className="w-3 h-3" />
          Shortlisted
        </h4>
        <div className="space-y-3">
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>Data Inclusão</label>
            <div className="grid grid-cols-2 gap-2">
              <Input
                type="date"
                value={tableFilters.shortlistedDateFrom ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    shortlistedDateFrom: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
              />
              <Input
                type="date"
                value={tableFilters.shortlistedDateTo ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    shortlistedDateTo: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
              />
            </div>
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>Vaga Origem</label>
            <Input
              type="text"
              value={tableFilters.shortlistedVacancyOrigin ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  shortlistedVacancyOrigin: e.target.value || undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="Nome ou ID da vaga de origem"
            />
          </div>
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <CheckCircle className="w-3 h-3" />
          Placement
        </h4>
        <div className="space-y-3">
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>Data Colocação</label>
            <div className="grid grid-cols-2 gap-2">
              <Input
                type="date"
                value={tableFilters.placementDateFrom ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    placementDateFrom: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
              />
              <Input
                type="date"
                value={tableFilters.placementDateTo ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    placementDateTo: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
              />
            </div>
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>Vaga Destino</label>
            <Input
              type="text"
              value={tableFilters.placementVacancyDestination ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  placementVacancyDestination: e.target.value || undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="Nome ou ID da vaga"
            />
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>Empresa Cliente</label>
            <Input
              type="text"
              value={tableFilters.placementClientCompany ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  placementClientCompany: e.target.value || undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="Nome da empresa"
            />
          </div>
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Bookmark className="w-3 h-3" />
          Vaga Específica
        </h4>
        <Input
          type="text"
          value={tableFilters.specificVacancyId ?? ""}
          onChange={(e) =>
            setTableFilters((prev) => ({
              ...prev,
              specificVacancyId: e.target.value || undefined,
            }))
          }
          className="h-8 text-xs"
          placeholder="Buscar vaga por ID ou nome..."
        />
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Calendar className="w-3 h-3" />
          Data de Cadastro
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <Input
            type="date"
            value={tableFilters.registrationDateFrom ?? ""}
            onChange={(e) =>
              setTableFilters((prev) => ({
                ...prev,
                registrationDateFrom: e.target.value || undefined,
              }))
            }
            className="h-8 text-xs"
            placeholder="De"
          />
          <Input
            type="date"
            value={tableFilters.registrationDateTo ?? ""}
            onChange={(e) =>
              setTableFilters((prev) => ({
                ...prev,
                registrationDateTo: e.target.value || undefined,
              }))
            }
            className="h-8 text-xs"
            placeholder="Até"
          />
        </div>
      </div>

      <div className="pt-4 border-t border-lia-border-subtle space-y-2">
        <button
          className="w-full h-9 text-xs rounded-md transition-colors motion-reduce:transition-none border border-lia-border-subtle"
          onClick={onClearAll}
        >
          Limpar Todos os Filtros
        </button>
      </div>
    </>
  )
}
