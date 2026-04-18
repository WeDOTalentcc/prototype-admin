"use client"

import { useState, useEffect } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { X, Save, Target, Plus, Loader2, Brain } from"lucide-react"
import type { SearchSpec } from"@/lib/api/candidate-search"
import {
  extractTagsFromSearchSpec,
  suggestArchetypeName,
  extractIndustryFromSpec,
  extractSeniorityFromSpec,
  type ExtractedTag,
} from"@/lib/utils/extract-tags-from-search"
import { textStyles, cardStyles, inputStyles, badgeStyles } from"@/lib/design-tokens"
import { toast } from"sonner"

interface SaveArchetypeModalProps {
  open: boolean
  onClose: () => void
  searchSpec: SearchSpec | null
  query: string
  onSuccess?: (archetype: Record<string, unknown>) => void
}

const EMOJI_OPTIONS = ["🎯","🚀","💎","⚡","🧠","📊","🎨","🔧","🔍","📱"]

const INDUSTRY_OPTIONS = [
  { value:"", label:"Selecione um setor" },
  { value:"technology", label:"Tecnologia" },
  { value:"finance", label:"Financeiro" },
  { value:"healthcare", label:"Saúde" },
  { value:"education", label:"Educação" },
  { value:"retail", label:"Varejo" },
  { value:"manufacturing", label:"Indústria" },
  { value:"consulting", label:"Consultoria" },
  { value:"marketing", label:"Marketing" },
  { value:"logistics", label:"Logística" },
  { value:"real_estate", label:"Imobiliário" },
  { value:"other", label:"Outro" },
]

const SENIORITY_OPTIONS = [
  { value:"", label:"Selecione a senioridade" },
  { value:"junior", label:"Júnior" },
  { value:"pleno", label:"Pleno" },
  { value:"senior", label:"Sênior" },
  { value:"lead", label:"Lead / Tech Lead" },
  { value:"manager", label:"Gerente" },
  { value:"director", label:"Diretor" },
]

export function SaveArchetypeModal({
  open,
  onClose,
  searchSpec,
  query,
  onSuccess,
}: SaveArchetypeModalProps) {
const [isSaving, setIsSaving] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [selectedEmoji, setSelectedEmoji] = useState("🎯")
  const [tags, setTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState("")
  const [industry, setIndustry] = useState("")
  const [seniority, setSeniority] = useState("")

  useEffect(() => {
    if (open && searchSpec) {
      setName(suggestArchetypeName(searchSpec))
      setDescription(query ||"")
      setSelectedEmoji("🎯")
      
      const extractedTags = extractTagsFromSearchSpec(searchSpec)
      setTags(extractedTags.map((t) => t.value))
      
      setIndustry(extractIndustryFromSpec(searchSpec))
      setSeniority(extractSeniorityFromSpec(searchSpec))
    }
  }, [open, searchSpec, query])

  if (!open) return null

  const handleAddTag = () => {
    const trimmedTag = newTag.trim()
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags([...tags, trimmedTag])
      setNewTag("")
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((tag) => tag !== tagToRemove))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key ==="Enter") {
      e.preventDefault()
      handleAddTag()
    }
  }

  const handleSave = async () => {
    if (!name.trim()) {
      toast.error("Nome obrigatório", { description:"Por favor, insira um nome para o arquétipo." })
      return
    }

    setIsSaving(true)

    try {
      const payload = {
        name: name.trim(),
        description: description.trim(),
        emoji: selectedEmoji,
        tags,
        industry: industry || undefined,
        seniority: seniority || undefined,
        search_spec: searchSpec,
        original_query: query,
      }

      const response = await fetch("/api/backend-proxy/search/archetypes/from-search", {
        method:"POST",
        headers: {"Content-Type":"application/json" },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error ||"Erro ao salvar arquétipo")
      }

      const data = await response.json()

      toast.success("Arquétipo salvo!", { description: `O arquétipo"${name}" foi criado com sucesso.` })

      onSuccess?.(data)
      onClose()
    } catch (error) {
      toast.error("Erro ao salvar", { description: error instanceof Error ? error.message :"Não foi possível salvar o arquétipo." })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-xl max-h-[90vh] bg-lia-bg-primary overflow-y-auto rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardHeader className="flex flex-row items-center justify-between pb-4 dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl flex items-center justify-center">
              <Target className="w-5 h-5 text-lia-text-secondary" />
            </div>
            <div>
              <CardTitle className={textStyles.titleLarge}>Salvar como Arquétipo</CardTitle>
              <p className={textStyles.description}>
                Salve esta busca para reutilizar no futuro
              </p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="w-4 h-4" />
          </Button>
        </CardHeader>

        <CardContent className="space-y-5 pt-5">
          <div>
            <label className={`${textStyles.label} mb-2 block`}>Nome do Arquétipo *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Desenvolvedor Backend Sênior"
              className={`w-full ${inputStyles.default}`}
            />
          </div>

          <div>
            <label className={`${textStyles.label} mb-2 block`}>Descrição</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descreva o perfil ideal para este arquétipo..."
              rows={3}
              className={`w-full ${inputStyles.default} resize-none`}
            />
          </div>

          <div>
            <label className={`${textStyles.label} mb-2 block`}>Emoji</label>
            <div className="flex flex-wrap gap-2">
              {EMOJI_OPTIONS.map((emoji) => (
                <button
                  key={emoji}
                  type="button"
                  onClick={() => setSelectedEmoji(emoji)}
                  className={`w-10 h-10 rounded-md border-2 text-xl flex items-center justify-center transition-colors motion-reduce:transition-none ${
                    selectedEmoji === emoji
                      ?"border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
                      :"border-lia-border-subtle hover:border-lia-border-default"
                  }`}
                >
                  {emoji}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className={`${textStyles.label} mb-2 block`}>Tags</label>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {tags.map((tag, index) => (
                  <Chip variant="neutral" muted key={`tag-${index}`} className={badgeStyles.primary}>
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 hover:text-status-error"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Chip>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Adicionar tag..."
                className={`flex-1 ${inputStyles.default}`}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddTag}
                disabled={!newTag.trim()}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={`${textStyles.label} mb-2 block`}>Setor / Indústria</label>
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className={`w-full ${inputStyles.default}`}
              >
                {INDUSTRY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className={`${textStyles.label} mb-2 block`}>Senioridade</label>
              <select
                value={seniority}
                onChange={(e) => setSeniority(e.target.value)}
                className={`w-full ${inputStyles.default}`}
              >
                {SENIORITY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary dark:border-lia-border-subtle">
            <Button variant="outline" onClick={onClose} disabled={isSaving} className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse">
              Cancelar
            </Button>
            <Button
              onClick={handleSave}
              disabled={!name.trim() || isSaving}
              className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                  Salvando...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Salvar Arquétipo
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
