"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import {
  Gift,
  Upload,
  Plus,
  Pencil,
  Trash2,
  ChevronDown,
  ChevronRight,
  Brain,
  GripVertical,
  Loader2,
  Library,
} from "lucide-react"

import {
  BENEFIT_CATEGORIES,
  SENIORITY_LEVELS,
  WAITING_PERIODS,
} from "../setup-empresa.constants"
import type { Benefit, BenefitsContentProps } from "../setup-empresa.types"

export function BenefitsContent({
  isLoading,
  benefits,
  expandedCategories,
  setShowImportModal,
  setShowTemplateModal,
  setEditingBenefit,
  setShowBenefitModal,
  toggleCategory,
  handleToggleBenefitStatus,
  handleDeleteBenefit,
  defaultBenefit,
}: BenefitsContentProps) {
  const getBenefitsByCategory = (categoryId: string) =>
    benefits.filter((b) => b.category === categoryId)

  const formatBenefitValue = (benefit: Benefit) => {
    if (benefit.value_type === "monetary" && benefit.value) {
      const prefix = benefit.is_discount ? "Desconto: " : ""
      return `${prefix}R$ ${benefit.value.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
      })}`
    }
    if (benefit.value_type === "percentage" && benefit.percentage_value) {
      return `${benefit.percentage_value}%`
    }
    if (benefit.value_type === "informative") {
      return benefit.value_details || "Informativo"
    }
    return "-"
  }

  return (
    <div aria-live="polite" aria-busy={isLoading} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary">
            Benefícios da Empresa
          </h2>
          <p className="text-sm mt-1 lia-text-500 dark:text-lia-text-tertiary">
            Configure os benefícios oferecidos aos colaboradores
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setShowImportModal(true)} className="gap-2">
            <Upload className="w-4 h-4" />
            Importar com LIA
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowTemplateModal(true)}
            className="gap-2 border-lia-border-default"
          >
            <Library className="w-4 h-4" />
            Adicionar da Lista
          </Button>
          <Button
            onClick={() => {
              setEditingBenefit({ ...defaultBenefit })
              setShowBenefitModal(true)
            }}
            className="gap-2 bg-gray-800"
          >
            <Plus className="w-4 h-4" />
            Adicionar Benefício
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none lia-text-400" />
        </div>
      ) : benefits.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Gift className="w-12 h-12 lia-text-300 mb-4" />
            <h3 className="text-lg font-medium mb-2 lia-text-800 dark:text-lia-text-primary">
              Nenhum benefício cadastrado
            </h3>
            <p className="text-sm text-center mb-4 lia-text-500 dark:text-lia-text-tertiary">
              Comece importando uma planilha ou adicionando benefícios manualmente
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setShowImportModal(true)}
                className="gap-2"
              >
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Importar com LIA
              </Button>
              <Button
                onClick={() => {
                  setEditingBenefit({ ...defaultBenefit })
                  setShowBenefitModal(true)
                }}
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                Adicionar Manual
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {BENEFIT_CATEGORIES.map((category) => {
            const categoryBenefits = getBenefitsByCategory(category.id)
            if (categoryBenefits.length === 0) return null
            const isExpanded = expandedCategories.includes(category.id)
            const CategoryIcon = category.icon
            return (
              <Card key={category.id}>
                <div
                  className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  onClick={() => toggleCategory(category.id)}
                >
                  <div className="flex items-center gap-3">
                    <CategoryIcon className={`w-5 h-5 ${category.color}`} />
                    <span className="font-medium lia-text-800 dark:text-lia-text-primary">
                      {category.name}
                    </span>
                    <Badge variant="secondary" className="text-xs">
                      {categoryBenefits.length}
                    </Badge>
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 lia-text-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 lia-text-400" />
                  )}
                </div>

                {isExpanded && (
                  <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    {categoryBenefits.map((benefit) => (
                      <div
                        key={benefit.id}
                        className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 border-b last:border-b-0 border-lia-border-subtle dark:border-lia-border-subtle"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          <GripVertical className="w-4 h-4 lia-text-300 cursor-grab" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm lia-text-800 dark:text-lia-text-primary">
                                {benefit.name}
                              </span>
                              {benefit.is_highlighted && (
                                <Badge className="text-xs bg-status-warning/15 text-status-warning dark:bg-status-warning dark:text-status-warning">
                                  Destaque
                                </Badge>
                              )}
                              {!benefit.is_active && (
                                <Badge variant="secondary" className="text-xs">
                                  Inativo
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-4 mt-1">
                              <span className="text-xs lia-text-400 dark:lia-text-500">
                                {formatBenefitValue(benefit)}
                              </span>
                              <span className="text-xs lia-text-400 dark:lia-text-500">
                                {benefit.seniority_levels?.includes("all")
                                  ? "Todos os níveis"
                                  : benefit.seniority_levels
                                      ?.map(
                                        (l) =>
                                          SENIORITY_LEVELS.find((s) => s.id === l)?.name
                                      )
                                      .join(", ") || "Todos os níveis"}
                              </span>
                              {benefit.waiting_period_days > 0 && (
                                <span className="text-xs lia-text-400 dark:lia-text-500">
                                  Carência:{" "}
                                  {WAITING_PERIODS.find(
                                    (w) => w.id === benefit.waiting_period_days
                                  )?.name || `${benefit.waiting_period_days} dias`}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={benefit.is_active}
                            onCheckedChange={() => handleToggleBenefitStatus(benefit)}
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingBenefit(benefit)
                              setShowBenefitModal(true)
                            }}
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              benefit.id && handleDeleteBenefit(benefit.id)
                            }
                            className="text-status-error hover:text-status-error"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
