"use client"

import { useState, useEffect } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  X,
  Save,
  BookOpen,
  Users,
  Briefcase,
  BarChart3,
  Zap,
  FileText,
  Mail,
  Brain,
  Plus,
  Tag,
  MessageCircle,
  CheckCircle
} from"lucide-react"

interface SaveCommandModalProps {
  isOpen: boolean
  onClose: () => void
  originalCommand: string
  commandResult?: string
  onSave: (commandData: SavedCommandData) => void
  existingData?: {
    title: string
    description: string
    category: string
    examples: string[]
    tags: string[]
  }
}

export interface SavedCommandData {
  title: string
  command: string
  description: string
  category: string
  examples: string[]
  tags: string[]
  context?: string
  result?: string
}

const categories = [
  { id:"candidates", name:"Candidatos", icon: Users, color:"text-lia-text-secondary" },
  { id:"jobs", name:"Vagas", icon: Briefcase, color:"text-status-success" },
  { id:"analytics", name:"Indicadores", icon: BarChart3, color:"text-lia-text-secondary" },
  { id:"automation", name:"Automações", icon: Zap, color:"text-wedo-orange-text" },
  { id:"reports", name:"Relatórios", icon: FileText, color:"text-lia-text-secondary" },
  { id:"communication", name:"Comunicação", icon: Mail, color:"text-wedo-magenta-text" },
  { id:"custom", name:"Personalizado", icon: Brain, color:"text-lia-text-secondary" }
]

export function SaveCommandModal({ isOpen, onClose, originalCommand, commandResult, onSave, existingData }: SaveCommandModalProps) {
  const [title, setTitle] = useState(existingData?.title ||"")
  const [description, setDescription] = useState(existingData?.description ||"")
  const [selectedCategory, setSelectedCategory] = useState(existingData?.category ||"custom")
  const [examples, setExamples] = useState(existingData?.examples || [originalCommand])
  const [newExample, setNewExample] = useState("")
  const [tags, setTags] = useState<string[]>(existingData?.tags || [])
  const [newTag, setNewTag] = useState("")
  const [isSaving, setIsSaving] = useState(false)

  // Atualizar dados quando existingData mudar (modo edição)
  useEffect(() => {
    if (existingData) {
      setTitle(existingData.title)
      setDescription(existingData.description)
      setSelectedCategory(existingData.category)
      setExamples(existingData.examples)
      setTags(existingData.tags)
    } else {
      // Reset para dados do comando original quando não estiver editando
      setTitle("")
      setDescription("")
      setSelectedCategory("custom")
      setExamples([originalCommand])
      setTags([])
    }
  }, [existingData, originalCommand])

  if (!isOpen) return null

  const handleAddExample = () => {
    if (newExample.trim() && !examples.includes(newExample.trim())) {
      setExamples([...examples, newExample.trim()])
      setNewExample("")
    }
  }

  const handleRemoveExample = (index: number) => {
    setExamples(examples.filter((_, i) => i !== index))
  }

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim().toLowerCase())) {
      setTags([...tags, newTag.trim().toLowerCase()])
      setNewTag("")
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  const handleSave = async () => {
    if (!title.trim() || !description.trim()) return

    setIsSaving(true)

    const commandData: SavedCommandData = {
      title: title.trim(),
      command: originalCommand,
      description: description.trim(),
      category: selectedCategory,
      examples: examples.filter(ex => ex.trim()),
      tags: tags,
      context: `Comando criado pelo usuário`,
      result: commandResult
    }

    // Simular salvamento
    await new Promise(resolve => setTimeout(resolve, 1000))

    onSave(commandData)
    setIsSaving(false)

    // Reset form
    setTitle("")
    setDescription("")
    setSelectedCategory("custom")
    setExamples([originalCommand])
    setTags([])

    onClose()
  }

  // Sugerir título baseado no comando
  const suggestTitle = () => {
    if (originalCommand.toLowerCase().includes("candidato")) {
      return"Análise de Candidatos"
    } else if (originalCommand.toLowerCase().includes("vaga")) {
      return"Gestão de Vagas"
    } else if (originalCommand.toLowerCase().includes("relatório")) {
      return"Relatório Personalizado"
    } else if (originalCommand.toLowerCase().includes("email")) {
      return"Comunicação por Email"
    }
    return"Comando Personalizado"
  }

  const suggestCategory = () => {
    if (originalCommand.toLowerCase().includes("candidato")) return"candidates"
    if (originalCommand.toLowerCase().includes("vaga")) return"jobs"
    if (originalCommand.toLowerCase().includes("relatório") || originalCommand.toLowerCase().includes("métrica")) return"analytics"
    if (originalCommand.toLowerCase().includes("email") || originalCommand.toLowerCase().includes("comunicar")) return"communication"
    return"custom"
  }

  return (
    <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-3xl max-h-[90vh] bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between pb-4 dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-wedo-purple/15 dark:bg-wedo-purple/20 rounded-md flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-wedo-purple dark:text-wedo-purple" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-lia-text-primary">
                Salvar Novo Comando
              </CardTitle>
              <p className="text-sm text-lia-text-tertiary">
                Adicione este comando à biblioteca da LIA para futuros usos
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="w-4 h-4" />
          </Button>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Comando Original */}
 <div className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl p-4 border border-lia-border-default">
            <div className="flex items-center gap-2 mb-2">
              <MessageCircle className="w-4 h-4 text-lia-text-secondary" />
 <span className="text-sm font-medium text-lia-text-secondary">Comando Original:</span>
            </div>
 <div className="text-sm text-lia-text-secondary font-mono bg-lia-bg-primary rounded-xl p-2">"{originalCommand}"
            </div>
          </div>

          {/* Auto-sugestões */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setTitle(suggestTitle())}
              className="gap-2 bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
            >
              <Brain className="w-3 h-3 text-wedo-cyan" />
              Sugerir Título
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedCategory(suggestCategory())}
              className="gap-2 bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
            >
              <Tag className="w-3 h-3" />
              Sugerir Categoria
            </Button>
          </div>

          {/* Título */}
          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-2">
              Título do Comando *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Análise Avançada de Candidatos"
              className="w-full px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          {/* Categoria */}
          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-2">
              Categoria *
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`p-3 rounded-md border transition-colors motion-reduce:transition-none ${
 selectedCategory === category.id
                      ? 'border-wedo-purple/30 bg-wedo-purple/10 dark:bg-wedo-purple/20'
                      : 'border-lia-border-subtle dark:border-lia-border-default hover:border-wedo-purple/30'
                  }`}
                >
                  <category.icon className={`w-5 h-5 mb-1 mx-auto ${category.color}`} />
                  <div className="text-xs font-medium text-lia-text-primary">
                    {category.name}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Descrição */}
          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-2">
              Descrição *
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descreva o que este comando faz e quando deve ser usado..."
              rows={3}
              className="w-full px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            />
          </div>

          {/* Exemplos */}
          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-2">
              Exemplos de Uso
            </label>
            <div className="space-y-2">
              {examples.map((example, index) => (
                <div key={`example-${index}`} className="flex items-center gap-2">
                  <div className="flex-1 text-sm text-lia-text-primary bg-lia-bg-secondary dark:bg-lia-bg-elevated rounded-xl px-3 py-2">"{example}"
                  </div>
                  {examples.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveExample(index)}
                      className="h-8 w-8 p-0 text-status-error hover:text-status-error"
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              ))}

              <div className="flex gap-2">
                <input
                  type="text"
                  value={newExample}
                  onChange={(e) => setNewExample(e.target.value)}
                  placeholder="Adicionar outro exemplo..."
                  className="flex-1 px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleAddExample()}
                />
                <Button variant="outline" size="sm" onClick={handleAddExample} disabled={!newExample.trim()} className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-lia-text-primary mb-2">
              Tags (palavras-chave)
            </label>
            <div className="space-y-2">
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag, index) => (
                    <Chip density="relaxed" key={tag} variant="neutral" muted >
                      {tag}
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 text-lia-text-secondary hover:text-lia-text-primary"
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
                  placeholder="Adicionar tag..."
                  className="flex-1 px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                />
                <Button variant="outline" size="sm" onClick={handleAddTag} disabled={!newTag.trim()} className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Resultado do Comando (se disponível) */}
          {commandResult && (
            <div className="bg-status-success/10 dark:bg-status-success/10 rounded-xl p-4 border border-status-success/30 dark:border-status-success/30">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-4 h-4 text-status-success" />
                <span className="text-sm font-medium text-status-success dark:text-status-success">Resultado:</span>
              </div>
              <div className="text-sm text-status-success dark:text-status-success">
                {commandResult}
              </div>
            </div>
          )}

          {/* Botões */}
          <div className="flex justify-end gap-3 pt-4 border-t border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary dark:border-lia-border-subtle -mx-6 px-6 pb-0 mt-6">
            <Button variant="outline" onClick={onClose} className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse">
              Cancelar
            </Button>
            <Button
              onClick={handleSave}
              disabled={!title.trim() || !description.trim() || isSaving}
              className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin motion-reduce:animate-none" />
                  Salvando...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Salvar na Biblioteca
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
