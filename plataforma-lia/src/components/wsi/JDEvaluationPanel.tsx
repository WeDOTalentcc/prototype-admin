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
  Wand2,
  Info,
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
    isExpanded, setIsExpanded, evaluation, evaluationError, isLoading, isEditing, setIsEditing,
    editDescription, setEditDescription, editResponsibilities, setEditResponsibilities,
    editTechSkills, setEditTechSkills, editBehavCompetencies, setEditBehavCompetencies,
    isSavingInline, newItem, setNewItem, editingField, setEditingField, saveError,
    aiTechSuggestions, setAiTechSuggestions, aiBehavSuggestions, setAiBehavSuggestions,
    isLoadingTechSuggestions, isLoadingBehavSuggestions, aiRespSuggestions, setAiRespSuggestions, isLoadingRespSuggestions,
    generatedJD, isGeneratingJD, copiedJD, isSavingDefinitive, isSavingWithJD,
    jdTypedMessage, jdDynamicMessage, jdGenerationStep, jdGenerationError,
    fetchTechSuggestions, fetchBehavSuggestions, fetchResponsibilitiesSuggestions, generateJD, handleCopyJD,
    fetchEvaluation, handleSaveRascunho, handleSaveDefinitiva, handleSaveAndUpdateJD, handleCancel,
    isExtracting, extractError, extractFromText,
  } = hook

  if (!isExpanded) {
    return (
      <div className={cn("mx-5 mt-4", className)}>
        <div className="border border-lia-border-subtle rounded-xl overflow-hidden">
          <JDEvaluationHeader
            jobTitle={jobTitle}
            isExpanded={false}
            isEditing={isEditing}
            evaluation={evaluation}
            onToggleExpand={() => setIsExpanded(true)}
            onStartEdit={() => {
              setIsExpanded(true)
              setIsEditing(true)
            }}
            canEdit={!!(onSaveJDInline || onEditJD)}
          />
          <div className="px-4 py-2.5 border-t border-lia-border-subtle bg-lia-bg-primary">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <ListChecks className="w-3 h-3 text-lia-text-muted" />
                Responsabilidades: {responsibilities.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <Code className="w-3 h-3 text-lia-text-muted" />
                Comp. Técnicas: {technicalSkills.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <Users className="w-3 h-3 text-lia-text-muted" />
                Comp. Comportamentais: {behavioralCompetencies.length}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-lia-border-subtle bg-lia-bg-secondary text-micro text-lia-text-secondary">
                <FileText className="w-3 h-3 text-lia-text-muted" />
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
      <div className="border border-lia-border-subtle rounded-xl overflow-hidden">
        <JDEvaluationHeader
          jobTitle={jobTitle}
          isExpanded={true}
          isEditing={isEditing}
          evaluation={evaluation}
          onToggleExpand={() => setIsExpanded(false)}
          onStartEdit={() => setIsEditing(true)}
          canEdit={!!(onSaveJDInline || onEditJD)}
        />

        <div className="p-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-4" role="status" aria-live="polite" aria-label="Carregando avaliação...">
              <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
              <span className="ml-2 text-xs text-lia-text-secondary">Avaliando Descrição do Cargo...</span>
            </div>
          ) : (
            <div className="space-y-3">
              {evaluation && <JDEvalCriteriaList evaluation={evaluation} />}

              {!evaluation && !isEditing && (
                <div className="text-center py-4">
                  {/* Bug A (Task #1165): mostra mensagem real do hook em vez de genérica */}
                  <p
                    className="text-xs text-lia-text-secondary"
                    role={evaluationError ? "alert" : undefined}
                  >
                    {evaluationError || "Não foi possível avaliar o JD."}
                  </p>
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
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide">Descrição / Sumário</label>
                          {/* T-1167 (Bug #3) — extrai responsabilidades/skills/comp.comp. do texto colado */}
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-6 text-micro px-2 border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover"
                            onClick={extractFromText}
                            disabled={isExtracting || !editDescription || editDescription.trim().length < 50}
                            title="Detecta responsabilidades, competências técnicas e comportamentais no texto colado e preenche as listas abaixo (sem duplicar o que você já adicionou)."
                          >
                            {isExtracting ? (
                              <Loader2 className="h-3 w-3 mr-1 animate-spin motion-reduce:animate-none" />
                            ) : (
                              <Wand2 className="h-3 w-3 mr-1 text-wedo-cyan" />
                            )}
                            Extrair do texto
                          </Button>
                        </div>
                        <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-3">
                          <textarea
                            value={editDescription}
                            onChange={(e) => setEditDescription(e.target.value)}
                            className="w-full h-40 text-xs text-lia-text-primary border border-lia-border-subtle rounded-xl p-2.5 resize-none focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 focus:border-lia-border-medium bg-lia-bg-secondary"
                            placeholder="Cole aqui um JD completo (mín. 50 caracteres) e use 'Extrair do texto' para preencher responsabilidades e competências automaticamente."
                          />
                        </div>
                        {extractError && (
                          <p role="alert" className="text-micro text-status-error mt-1">{extractError}</p>
                        )}
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
                        aiSuggestions={aiRespSuggestions.map(r => ({ label: r, key: r }))}
                        isLoadingAI={isLoadingRespSuggestions}
                        onFetchAI={fetchResponsibilitiesSuggestions}
                        onAcceptSuggestion={(key) => {
                          if (!editResponsibilities.includes(key)) {
                            setEditResponsibilities(prev => [...prev, key])
                          }
                          setAiRespSuggestions(prev => prev.filter(r => r !== key))
                        }}
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
                      jdGenerationError={jdGenerationError}
                      copiedJD={copiedJD}
                      isSavingWithJD={isSavingWithJD}
                      onGenerate={generateJD}
                      onCopy={handleCopyJD}
                      onSaveAndUpdateJD={handleSaveAndUpdateJD}
                      showSaveAndUpdate={!!(generatedJD && onUpdateJobDescription)}
                    />
                  </div>

                  {/* T-1167 (Bug #2 / Opção B) — aviso visual explícito da diferença entre Rascunho e Definitiva */}
                  <div className="flex items-start gap-2 mt-4 px-3 py-2 rounded-md bg-lia-bg-secondary border border-lia-border-subtle">
                    <Info className="h-3.5 w-3.5 text-lia-text-muted shrink-0 mt-0.5" />
                    <p className="text-micro text-lia-text-secondary leading-relaxed">
                      <span className="font-semibold">Rascunho</span> guarda uma cópia privada (apenas neste painel) e <span className="font-semibold">não atualiza</span> os campos canônicos da vaga. Para publicar Responsabilidades / Competências oficialmente, use <span className="font-semibold">Salvar Versão Definitiva</span>.
                    </p>
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
                      {/* T-1167 (Bug #2 / Opção B) — Rascunho não publica nos campos canônicos da vaga.
                          Renomeado + tooltip + banner para deixar explícito ao recrutador. */}
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-micro px-3 border-lia-border-subtle text-lia-text-secondary"
                        onClick={handleSaveRascunho}
                        disabled={isSavingInline}
                        title="Salva como rascunho privado (campo enriched_jd). NÃO atualiza Responsabilidades / Competências da vaga oficial — para isso use 'Salvar Versão Definitiva'."
                      >
                        {isSavingInline ? <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none mr-1" /> : <Save className="h-3 w-3 mr-1" />}
                        Salvar Rascunho (não publica)
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
          )}
        </div>
      </div>
    </div>
  )
}

export default JDEvaluationPanel
