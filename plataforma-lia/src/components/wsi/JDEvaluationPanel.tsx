"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import {
  FileText,
  Code, Users,
  Loader2,
  CheckCircle,
  Save,
  ListChecks,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { JDEvaluationHeader } from "./jd-evaluation/JDEvaluationHeader"
import { JDArrayEditor } from "./jd-evaluation/JDArrayEditor"
import { JDGenerationSection } from "./jd-evaluation/JDGenerationSection"
import { JDEvalCriteriaList } from "./jd-evaluation/JDEvalCriteriaList"
import { JDEvalResultsPanel } from "./jd-evaluation/JDEvalResultsPanel"
import { useJDEvaluation } from "./jd-evaluation/useJDEvaluation"
import type { JDEvaluationPanelProps } from "./jd-evaluation/useJDEvaluation"

export function JDEvaluationPanel({
  jobTitle,
  responsibilities,
  technicalSkills,
  behavioralCompetencies,
  seniority,
  department,
  description,
  hasQuestions,
  onGenerateQuestions,
  onEditJD,
  onSaveJDInline,
  onSaveEnrichedJD,
  onUpdateOfficialJD,
  onUpdateJobDescription,
  enrichedJd,
  isGenerating = false,
  className,
  companyId,
  companyName,
  companyDescription,
  companyIndustry,
  benefits = [],
  interviewStages = []
}: JDEvaluationPanelProps) {
  const hook = useJDEvaluation({
    jobTitle, responsibilities, technicalSkills, behavioralCompetencies,
    seniority, department, description, hasQuestions, enrichedJd,
    companyId, companyName, companyDescription, companyIndustry,
    benefits, interviewStages,
    onSaveJDInline, onSaveEnrichedJD, onUpdateOfficialJD, onUpdateJobDescription,
  })

  const {
    isExpanded, setIsExpanded, evaluation, isLoading, isEditing, setIsEditing,
    editDescription, setEditDescription, editResponsibilities, setEditResponsibilities,
    editTechSkills, setEditTechSkills, editBehavCompetencies, setEditBehavCompetencies,
    isSavingInline, newItem, setNewItem, editingField, setEditingField, saveError,
    aiTechSuggestions, setAiTechSuggestions, aiBehavSuggestions, setAiBehavSuggestions,
    isLoadingTechSuggestions, isLoadingBehavSuggestions,
    generatedJD, isGeneratingJD, copiedJD, isSavingDefinitive, isSavingWithJD,
    jdTypedMessage, jdDynamicMessage, jdGenerationStep,
    fetchTechSuggestions, fetchBehavSuggestions, generateJD, handleCopyJD,
    fetchEvaluation, handleSaveRascunho, handleSaveDefinitiva, handleSaveAndUpdateJD, handleCancel,
  } = hook

  if (!isExpanded) {
    return (
      <div className={cn("mx-5 mt-4", className)}>
        <div className="border border-lia-border-subtle rounded-md overflow-hidden">
          <JDEvaluationHeader
            jobTitle={jobTitle}
            hasQuestions={hasQuestions}
            isExpanded={false}
            isEditing={isEditing}
            evaluation={evaluation}
            onToggleExpand={() => setIsExpanded(true)}
            onStartEdit={() => {
              setIsExpanded(true)
              setIsEditing(true)
            }}
            onEditJD={onEditJD}
            canEdit={!!(onSaveJDInline || onEditJD)}
            responsibilities={responsibilities}
            technicalSkills={technicalSkills}
            behavioralCompetencies={behavioralCompetencies}
            description={description}
          />
          <div className="px-4 py-2.5 border-t border-lia-border-subtle bg-lia-bg-primary">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <ListChecks className="w-3 h-3 text-lia-text-disabled" />
                Responsabilidades: {responsibilities.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <Code className="w-3 h-3 text-lia-text-disabled" />
                Comp. Técnicas: {technicalSkills.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <Users className="w-3 h-3 text-lia-text-disabled" />
                Comp. Comportamentais: {behavioralCompetencies.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <FileText className="w-3 h-3 text-lia-text-disabled" />
                JD: {description ? 'Sim' : 'Não'}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("mx-5 mt-4", className)}>
      <div className="border border-lia-border-subtle rounded-md overflow-hidden">
        <JDEvaluationHeader
          jobTitle={jobTitle}
          hasQuestions={hasQuestions}
          isExpanded={true}
          isEditing={isEditing}
          evaluation={null}
          onToggleExpand={() => hasQuestions && setIsExpanded(false)}
          onStartEdit={() => setIsEditing(true)}
          onEditJD={onEditJD}
          canEdit={!!(onSaveJDInline || onEditJD)}
          responsibilities={responsibilities}
          technicalSkills={technicalSkills}
          behavioralCompetencies={behavioralCompetencies}
          description={description}
        />

        <div className="p-3" role="status" aria-live="polite" aria-label="Carregando...">
          {isLoading ? (
            <div className="flex items-center justify-center py-4" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
              <span className="ml-2 text-xs text-lia-text-secondary">Avaliando Descrição do Cargo...</span>
            </div>
          ) : evaluation ? (
            <div className="space-y-3">
              <JDEvalCriteriaList evaluation={evaluation} />

              {!isEditing && (
                <JDEvalResultsPanel
                  description={description}
                  responsibilities={responsibilities}
                  technicalSkills={technicalSkills}
                  behavioralCompetencies={behavioralCompetencies}
                  enrichedJd={enrichedJd}
                />
              )}

              {isEditing && (
                <div className="space-y-0">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-4">
                      <div>
                        <label className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide mb-2 block">Descrição / Sumário</label>
                        <div className="bg-lia-bg-primary rounded-md border border-lia-border-subtle p-3">
                          <textarea
                            value={editDescription}
                            onChange={(e) => setEditDescription(e.target.value)}
                            className="w-full h-40 text-xs text-lia-text-primary border border-lia-border-subtle rounded-md p-2.5 resize-none focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium bg-lia-bg-secondary"
                            placeholder="Forneça uma visão geral da vaga, incluindo propósito e como contribui para a organização..."
                          />
                        </div>
                      </div>

                      <JDArrayEditor
                        label="Responsabilidades"
                        items={editResponsibilities}
                        onChange={setEditResponsibilities}
                        variant="list"
                        placeholder="Adicionar responsabilidade..."
                        fieldKey="responsibilities"
                        editingField={editingField}
                        newItemValue={newItem}
                        onNewItemChange={setNewItem}
                        onStartEditing={setEditingField}
                        onStopEditing={() => setEditingField(null)}
                      />

                      <JDArrayEditor
                        label="Competências Técnicas"
                        items={editTechSkills}
                        onChange={setEditTechSkills}
                        variant="tags"
                        placeholder="Adicionar competência técnica..."
                        fieldKey="techSkills"
                        editingField={editingField}
                        newItemValue={newItem}
                        onNewItemChange={setNewItem}
                        onStartEditing={setEditingField}
                        onStopEditing={() => setEditingField(null)}
                        aiSuggestions={aiTechSuggestions.map(s => ({ label: s.skill, key: s.skill }))}
                        isLoadingAI={isLoadingTechSuggestions}
                        onFetchAI={fetchTechSuggestions}
                        onAcceptSuggestion={(key) => {
                          if (!editTechSkills.includes(key)) {
                            setEditTechSkills(prev => [...prev, key])
                          }
                          setAiTechSuggestions(prev => prev.filter(x => x.skill !== key))
                        }}
                      />

                      <JDArrayEditor
                        label="Competências Comportamentais"
                        items={editBehavCompetencies}
                        onChange={setEditBehavCompetencies}
                        variant="tags"
                        placeholder="Adicionar competência comportamental..."
                        fieldKey="behavCompetencies"
                        editingField={editingField}
                        newItemValue={newItem}
                        onNewItemChange={setNewItem}
                        onStartEditing={setEditingField}
                        onStopEditing={() => setEditingField(null)}
                        aiSuggestions={aiBehavSuggestions.map(c => ({ label: c.name, key: c.key }))}
                        isLoadingAI={isLoadingBehavSuggestions}
                        onFetchAI={fetchBehavSuggestions}
                        onAcceptSuggestion={(key) => {
                          const found = aiBehavSuggestions.find(c => c.key === key)
                          if (found && !editBehavCompetencies.includes(found.name)) {
                            setEditBehavCompetencies(prev => [...prev, found.name])
                          }
                          setAiBehavSuggestions(prev => prev.filter(x => x.key !== key))
                        }}
                      />
                    </div>

                    <JDGenerationSection
                      generatedJD={generatedJD}
                      isGeneratingJD={isGeneratingJD}
                      jdGenerationStep={jdGenerationStep}
                      jdTypedMessage={jdTypedMessage}
                      jdDynamicMessage={jdDynamicMessage}
                      copiedJD={copiedJD}
                      isSavingWithJD={isSavingWithJD}
                      onGenerate={generateJD}
                      onCopy={handleCopyJD}
                      onSaveAndUpdateJD={handleSaveAndUpdateJD}
                      showSaveAndUpdate={!!(generatedJD && onUpdateJobDescription)}
                    />
                  </div>

                  <div className="flex items-center justify-between pt-4 mt-4 border-t border-lia-border-subtle">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 text-micro px-3 border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
                      onClick={handleCancel}
                    >
                      Cancelar
                    </Button>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-micro px-3 border-lia-border-subtle text-lia-text-secondary"
                        onClick={handleSaveRascunho}
                        disabled={isSavingInline}
                      >
                        {isSavingInline ? <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none mr-1" /> : <Save className="h-3 w-3 mr-1" />}
                        Salvar Rascunho
                      </Button>
                      <Button
                        size="sm"
                        className="h-7 text-micro px-4 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                        onClick={handleSaveDefinitiva}
                        disabled={isSavingDefinitive}
                      >
                        {isSavingDefinitive ? <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none mr-1" /> : <CheckCircle className="h-3 w-3 mr-1" />}
                        Salvar Versão Definitiva
                      </Button>
                    </div>
                  </div>

                  {saveError && (
                    <p className="text-micro text-status-error mt-2">Erro ao salvar. Tente novamente.</p>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-6">
              <p className="text-xs text-lia-text-secondary">Não foi possível avaliar o JD.</p>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs mt-2"
                onClick={() => fetchEvaluation()}
              >
                Tentar novamente
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default JDEvaluationPanel
