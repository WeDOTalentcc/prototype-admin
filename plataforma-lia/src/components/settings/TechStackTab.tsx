"use client";

import React from"react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card";
import { Chip } from "@/components/ui/chip";
import {
  Code,
  ChevronDown,
  ChevronUp,
  Brain,
} from"lucide-react";
import { LiaFieldToggle, defaultLiaFieldExamples } from './LiaFieldToggle';
import {
  type CompanyData,
  type TechStackByCategory,
  TECH_STACK_CATEGORIES,
} from '@/hooks/settings/department-types';
import { cardStyles } from"@/lib/design-tokens";

export interface TechStackTabProps {
  companyData: CompanyData;
  isEditingCompanyData: boolean;
  techStackByCategory: TechStackByCategory;
  expandedCategories: Record<string, boolean>;
  setExpandedCategories: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  setCompanyData: React.Dispatch<React.SetStateAction<CompanyData>>;
  addTechToCategory: (category: string, tech: string) => void;
  removeTechFromCategory: (category: string, tech: string) => void;
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void;
  updateLiaInstruction: (fieldKey: string, instruction: string) => void;
}

export function TechStackTab({
  companyData,
  isEditingCompanyData,
  techStackByCategory,
  expandedCategories,
  setExpandedCategories,
  setCompanyData,
  addTechToCategory,
  removeTechFromCategory,
  updateLiaToggle,
  updateLiaInstruction,
}: TechStackTabProps) {
  const t = useTranslations("settings.techStackTab");
  return (
    <Card className={cardStyles.default}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-semibold text-lia-text-primary">
            <Code className="w-4 h-4" />
            {t("title")}
          </CardTitle>
          <LiaFieldToggle
            fieldKey="tech_stack"
            isActive={companyData.lia_field_toggles?.tech_stack ?? true}
            currentInstruction={companyData.lia_instructions?.tech_stack || ''}
            examples={defaultLiaFieldExamples.tech_stack}
            onToggleChange={updateLiaToggle}
            onInstructionSave={updateLiaInstruction}
            compact
          />
        </div>
      </CardHeader>
      <CardContent className="p-4 space-y-3">
        {TECH_STACK_CATEGORIES.map((category) => {
          const CategoryIcon = category.icon;
          const isExpanded = expandedCategories[category.key] ?? false;
          const categoryTechs = techStackByCategory[category.key] || [];

          return (
            <div
              key={category.key}
              className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl overflow-hidden"
            >
              <button
                type="button"
                onClick={() =>
                  setExpandedCategories((prev) => ({
                    ...prev,
                    [category.key]: !isExpanded,
                  }))
                }
                className={`w-full flex items-center justify-between px-3 py-2.5 ${category.color} hover:opacity-90 transition-opacity motion-reduce:transition-none`}
              >
                <div className="flex items-center gap-2">
                  <CategoryIcon className="w-4 h-4" />
                  <span className="text-xs font-medium">
                    {category.label}
                  </span>
                  {categoryTechs.length > 0 && (
                    <Chip variant="neutral" muted className="bg-lia-bg-primary/50 dark:bg-black/20 text-micro px-1.5 py-0.5">
                      {categoryTechs.length}
                    </Chip>
                  )}
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>

              {isExpanded && (
                <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary space-y-3">
                  {categoryTechs.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {categoryTechs.map((tech, idx) => (
                        <Chip variant="neutral" muted
                          key={idx}
                          className={`${category.color} text-xs px-2.5 py-1 rounded-full`}
                        >
                          {tech}
                          {isEditingCompanyData && (
                            <button
                              onClick={() =>
                                removeTechFromCategory(category.key, tech)
                              }
                              className="ml-1.5 hover:text-status-error"
                            >
                              ×
                            </button>
                          )}
                        </Chip>
                      ))}
                    </div>
                  )}

                  <div className="flex flex-wrap gap-1.5">
                    {category.suggestions
                      .filter((s) => !categoryTechs.includes(s))
                      .slice(0, 8)
                      .map((suggestion) => (
                        <button
                          key={suggestion}
                          type="button"
                          disabled={!isEditingCompanyData}
                          onClick={() => {
                            if (!isEditingCompanyData) return;
                            addTechToCategory(category.key, suggestion);
                          }}
                          className={`text-micro px-2 py-1 border border-dashed border-lia-border-default dark:border-lia-border-default rounded-full text-lia-text-secondary hover:border-lia-border-medium hover:text-lia-text-primary dark:hover:border-lia-border-medium transition-colors motion-reduce:transition-none ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                        >
                          + {suggestion}
                        </button>
                      ))}
                  </div>

                  <input
                    type="text"
                    placeholder={t("addCustom", { category: category.label.toLowerCase() })}
                    disabled={!isEditingCompanyData}
                    className={`w-full px-3 py-2 text-xs border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                    onKeyDown={(e) => {
                      if (e.key ==="Enter" && e.currentTarget.value.trim()) {
                        e.preventDefault();
                        addTechToCategory(category.key, e.currentTarget.value.trim());
                        e.currentTarget.value ="";
                      }
                    }}
                  />
                </div>
              )}
            </div>
          );
        })}

        {techStackByCategory["outros"] && techStackByCategory["outros"].length > 0 && (
          <div className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl overflow-hidden">
            <button
              type="button"
              onClick={() =>
                setExpandedCategories((prev) => ({
                  ...prev,
                  outros: !prev.outros,
                }))
              }
              className="w-full flex items-center justify-between px-3 py-2.5 bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary hover:opacity-90 transition-opacity motion-reduce:transition-none"
            >
              <div className="flex items-center gap-2">
                <Code className="w-4 h-4" />
                <span className="text-xs font-medium">{t("others")}</span>
                <Chip variant="neutral" muted className="bg-lia-bg-primary/50 dark:bg-black/20 text-micro px-1.5 py-0.5">
                  {techStackByCategory["outros"].length}
                </Chip>
              </div>
              {expandedCategories.outros ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>

            {expandedCategories.outros && (
              <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary space-y-3">
                <div className="flex flex-wrap gap-1.5">
                  {techStackByCategory["outros"].map((tech, idx) => (
                    <Chip variant="neutral" muted
                      key={idx}
                      className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary text-xs px-2.5 py-1 rounded-full"
                    >
                      {tech}
                      {isEditingCompanyData && (
                        <button
                          onClick={() => removeTechFromCategory("outros", tech)}
                          className="ml-1.5 hover:text-status-error"
                        >
                          ×
                        </button>
                      )}
                    </Chip>
                  ))}
                </div>

                <input
                  type="text"
                  placeholder={t("addTechnology")}
                  disabled={!isEditingCompanyData}
                  className={`w-full px-3 py-2 text-xs border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                  onKeyDown={(e) => {
                    if (e.key ==="Enter" && e.currentTarget.value.trim()) {
                      e.preventDefault();
                      addTechToCategory("outros", e.currentTarget.value.trim());
                      e.currentTarget.value ="";
                    }
                  }}
                />
              </div>
            )}
          </div>
        )}

        <div className="border-t border-lia-border-subtle dark:border-lia-border-strong pt-4">
          <label className="flex items-center gap-3 text-xs font-medium text-lia-text-secondary mb-2">
            <span className="flex items-center gap-1">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
              {t("engineeringCulture")}
            </span>
            <LiaFieldToggle
              fieldKey="engineering_culture"
              isActive={companyData.lia_field_toggles?.engineering_culture ?? true}
              currentInstruction={companyData.lia_instructions?.engineering_culture || ''}
              examples={defaultLiaFieldExamples.engineering_culture}
              onToggleChange={updateLiaToggle}
              onInstructionSave={updateLiaInstruction}
              compact
            />
          </label>
          <textarea
            value={companyData.engineering_culture ||""}
            disabled={!isEditingCompanyData}
            onChange={(e) =>
              setCompanyData((prev) => ({
                ...prev,
                engineering_culture: e.target.value,
              }))
            }
            className={`w-full px-3 py-2 text-xs border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium dark:focus:ring-lia-border-strong dark:focus:border-lia-border-medium transition-colors motion-reduce:transition-none ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-lia-bg-secondary dark:bg-lia-bg-primary' : ''}`}
            rows={3}
            placeholder={t("engineeringPlaceholder")}
          />
        </div>
      </CardContent>
    </Card>
  );
}
