"use client"

import React, { useState } from "react"
import { Shield, ChevronDown, Check, X } from "lucide-react"

interface AffirmativeData {
  is_affirmative?: boolean
  affirmative_criteria_primary?: string
  affirmative_criteria_secondary?: string
  affirmative_description?: string
  affirmative_document_required?: boolean
  affirmative_document_types?: string[]
}

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

const CRITERIA_LABELS: Record<string, string> = {
  gender: "Gênero (Mulheres)",
  race_ethnicity: "Raça/Etnia (Pessoas Negras)",
  disability: "Pessoa com Deficiência (PcD)",
  lgbtqia: "LGBTQIA+",
  age: "50+ anos",
  indigenous: "Povos Indígenas",
  refugee: "Refugiados / Imigrantes",
  other: "Ação Afirmativa (outro)",
}

const CRITERIA_KEYS = Object.keys(CRITERIA_LABELS)

const DOC_LABELS: Record<string, string> = {
  laudo_pcd: "Laudo PcD",
  autodeclaracao_racial: "Autodeclaração racial",
  autodeclaracao: "Autodeclaração",
  documento_identidade: "Documento de identidade",
  certificado_reabilitacao: "Cert. de reabilitação",
}

export function AffirmativePanel({ data, onUpdate }: Props) {
  const d = data as unknown as AffirmativeData
  const [localData, setLocalData] = useState<AffirmativeData>({
    is_affirmative: d.is_affirmative ?? false,
    affirmative_criteria_primary: d.affirmative_criteria_primary ?? "",
    affirmative_criteria_secondary: d.affirmative_criteria_secondary ?? "",
    affirmative_description: d.affirmative_description ?? "",
    affirmative_document_required: d.affirmative_document_required ?? true,
    affirmative_document_types: d.affirmative_document_types ?? [],
  })
  const [saved, setSaved] = useState(false)

  const handleToggleActive = () => {
    const next = !localData.is_affirmative
    const updated = { ...localData, is_affirmative: next }
    setLocalData(updated)
    if (!next) {
      onUpdate?.({
        is_affirmative: false,
        affirmative_criteria_primary: null,
        affirmative_criteria_secondary: null,
        affirmative_description: null,
        affirmative_document_required: true,
        affirmative_document_types: [],
      })
    }
  }

  const handleSave = () => {
    onUpdate?.({
      is_affirmative: localData.is_affirmative,
      affirmative_criteria_primary: localData.affirmative_criteria_primary || null,
      affirmative_criteria_secondary: localData.affirmative_criteria_secondary || null,
      affirmative_description: localData.affirmative_description || null,
      affirmative_document_required: localData.affirmative_document_required,
      affirmative_document_types: localData.affirmative_document_types,
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleDocTypeToggle = (docType: string) => {
    const current = localData.affirmative_document_types ?? []
    const updated = current.includes(docType)
      ? current.filter((d) => d !== docType)
      : [...current, docType]
    setLocalData({ ...localData, affirmative_document_types: updated })
  }

  return (
    <div className="px-4 py-3 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-medium text-lia-text-secondary">
            Ação Afirmativa
          </span>
        </div>
        {/* Toggle ativo/inativo */}
        <button
          type="button"
          onClick={handleToggleActive}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
            localData.is_affirmative ? "bg-purple-500" : "bg-lia-border-subtle"
          }`}
          aria-label={localData.is_affirmative ? "Desativar vaga afirmativa" : "Ativar vaga afirmativa"}
        >
          <span
            className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
              localData.is_affirmative ? "translate-x-4" : "translate-x-0.5"
            }`}
          />
        </button>
      </div>

      {/* Detectado automaticamente */}
      {d.is_affirmative && (
        <div className="flex items-start gap-2 rounded-md bg-purple-500/10 border border-purple-500/20 p-2">
          <Shield className="w-3.5 h-3.5 text-purple-400 mt-0.5 shrink-0" />
          <p className="text-xs text-lia-text-secondary leading-relaxed">
            Detectado automaticamente via análise da descrição.
            Confirme os critérios abaixo ou ajuste se necessário.
          </p>
        </div>
      )}

      {localData.is_affirmative && (
        <div className="space-y-3">
          {/* Critério principal */}
          <div>
            <label className="block text-xs text-lia-text-secondary mb-1">
              Critério principal
            </label>
            <div className="relative">
              <select
                value={localData.affirmative_criteria_primary ?? ""}
                onChange={(e) =>
                  setLocalData({ ...localData, affirmative_criteria_primary: e.target.value })
                }
                className="w-full appearance-none bg-lia-bg-subtle border border-lia-border-subtle rounded-md px-3 py-1.5 text-xs text-lia-text-primary pr-8 focus:outline-none focus:ring-1 focus:ring-purple-400"
              >
                <option value="">Selecione o critério</option>
                {CRITERIA_KEYS.map((key) => (
                  <option key={key} value={key}>
                    {CRITERIA_LABELS[key]}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-secondary pointer-events-none" />
            </div>
          </div>

          {/* Critério secundário */}
          <div>
            <label className="block text-xs text-lia-text-secondary mb-1">
              Critério secundário{" "}
              <span className="text-lia-text-tertiary">(opcional — ex: mulheres negras)</span>
            </label>
            <div className="relative">
              <select
                value={localData.affirmative_criteria_secondary ?? ""}
                onChange={(e) =>
                  setLocalData({
                    ...localData,
                    affirmative_criteria_secondary: e.target.value || undefined,
                  })
                }
                className="w-full appearance-none bg-lia-bg-subtle border border-lia-border-subtle rounded-md px-3 py-1.5 text-xs text-lia-text-primary pr-8 focus:outline-none focus:ring-1 focus:ring-purple-400"
              >
                <option value="">Nenhum</option>
                {CRITERIA_KEYS.filter(
                  (k) => k !== localData.affirmative_criteria_primary
                ).map((key) => (
                  <option key={key} value={key}>
                    {CRITERIA_LABELS[key]}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-secondary pointer-events-none" />
            </div>
          </div>

          {/* Descrição livre */}
          <div>
            <label className="block text-xs text-lia-text-secondary mb-1">
              Descrição da ação afirmativa
              <span className="text-lia-text-tertiary"> (opcional)</span>
            </label>
            <input
              type="text"
              value={localData.affirmative_description ?? ""}
              onChange={(e) =>
                setLocalData({ ...localData, affirmative_description: e.target.value })
              }
              placeholder="Ex: Mulheres negras acima de 30 anos"
              className="w-full bg-lia-bg-subtle border border-lia-border-subtle rounded-md px-3 py-1.5 text-xs text-lia-text-primary placeholder:text-lia-text-tertiary focus:outline-none focus:ring-1 focus:ring-purple-400"
            />
          </div>

          {/* Documentação */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs text-lia-text-secondary">
                Exige documentação comprobatória
              </label>
              <button
                type="button"
                onClick={() =>
                  setLocalData({
                    ...localData,
                    affirmative_document_required: !localData.affirmative_document_required,
                    affirmative_document_types: !localData.affirmative_document_required
                      ? localData.affirmative_document_types
                      : [],
                  })
                }
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  localData.affirmative_document_required
                    ? "bg-purple-500"
                    : "bg-lia-border-subtle"
                }`}
                aria-label="Toggle documentação"
              >
                <span
                  className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                    localData.affirmative_document_required
                      ? "translate-x-4"
                      : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>

            {localData.affirmative_document_required && (
              <div className="space-y-1 mt-2">
                <p className="text-xs text-lia-text-tertiary mb-1.5">
                  Tipos de documentos aceitos:
                </p>
                {Object.entries(DOC_LABELS).map(([key, label]) => {
                  const selected = (localData.affirmative_document_types ?? []).includes(key)
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => handleDocTypeToggle(key)}
                      className={`flex items-center gap-2 w-full text-left px-2.5 py-1.5 rounded-md text-xs transition-colors ${
                        selected
                          ? "bg-purple-500/15 border border-purple-500/30 text-lia-text-primary"
                          : "bg-lia-bg-subtle border border-lia-border-subtle text-lia-text-secondary hover:bg-lia-bg-hover"
                      }`}
                    >
                      <span
                        className={`w-3.5 h-3.5 rounded-sm flex items-center justify-center shrink-0 ${
                          selected ? "bg-purple-500" : "border border-lia-border-subtle"
                        }`}
                      >
                        {selected && <Check className="w-2.5 h-2.5 text-white" />}
                      </span>
                      {label}
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Botão confirmar */}
          <button
            type="button"
            onClick={handleSave}
            disabled={!localData.affirmative_criteria_primary}
            className={`w-full flex items-center justify-center gap-1.5 py-2 rounded-md text-xs font-medium transition-colors ${
              saved
                ? "bg-green-500/20 text-green-400 border border-green-500/30"
                : localData.affirmative_criteria_primary
                ? "bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30"
                : "bg-lia-bg-subtle text-lia-text-tertiary border border-lia-border-subtle cursor-not-allowed"
            }`}
          >
            {saved ? (
              <>
                <Check className="w-3.5 h-3.5" /> Confirmado
              </>
            ) : (
              "Confirmar ação afirmativa"
            )}
          </button>
        </div>
      )}

      {!localData.is_affirmative && (
        <p className="text-xs text-lia-text-tertiary text-center py-2">
          Vaga não configurada como afirmativa.
          <br />
          Ative o toggle acima para configurar.
        </p>
      )}
    </div>
  )
}
