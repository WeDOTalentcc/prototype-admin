'use client'

import React, { useState, useMemo } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import {
  Code,
  Laptop,
  Database,
  Wrench,
  Package,
  Search,
  Plus,
  Star,
  Check,
  X,
} from 'lucide-react'

export interface Skill {
  id: string
  name: string
  category: 'language' | 'framework' | 'database' | 'tool' | 'infrastructure' | 'general'
  weight?: number
  description?: string
}

export interface AddSkillModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  category: 'language' | 'framework' | 'database' | 'tool' | 'infrastructure' | 'general'
  companyCatalog: Skill[]
  marketSuggestions: Skill[]
  selectedSkills: Skill[]
  onAddSkill: (skill: Skill) => void
}

const CATEGORY_ICONS: Record<Skill['category'], React.ElementType> = {
  language: Code,
  framework: Laptop,
  database: Database,
  tool: Wrench,
  infrastructure: Package,
  general: Wrench,
}

const CATEGORY_LABELS: Record<Skill['category'], string> = {
  language: 'Linguagem',
  framework: 'Framework',
  database: 'Banco de Dados',
  tool: 'Ferramenta',
  infrastructure: 'Infraestrutura',
  general: 'Geral',
}

const CATEGORY_COLORS: Record<Skill['category'], { bg: string; text: string; border: string }> = {
  language: { bg: 'bg-wedo-cyan/10', text: 'text-wedo-cyan-dark', border: 'border-wedo-cyan/30' },
  framework: { bg: 'bg-wedo-purple/15', text: 'text-wedo-purple', border: 'border-wedo-purple/30' },
  database: { bg: 'bg-wedo-green/15', text: 'text-wedo-green', border: 'border-wedo-green/30' },
  tool: { bg: 'bg-status-warning/10', text: 'text-status-warning', border: 'border-status-warning/30' },
  infrastructure: { bg: 'bg-status-error/10', text: 'text-status-error', border: 'border-status-error/30' },
  general: { bg: 'bg-lia-bg-secondary', text: 'text-lia-text-secondary', border: 'border-lia-border-subtle' },
}

interface SkillCardProps {
  skill: Skill
  isSelected: boolean
  onAdd: (skill: Skill) => void
}

function SkillCard({ skill, isSelected, onAdd }: SkillCardProps) {
  const CategoryIcon = CATEGORY_ICONS[skill.category]
  const colors = CATEGORY_COLORS[skill.category]

  return (
    <div
      className={cn(
 'p-3 rounded-md transition-colors',
        isSelected
          ? 'bg-lia-bg-secondary border-2 border-lia-btn-primary-bg opacity-60 cursor-not-allowed'
          : 'bg-lia-bg-primary border border-lia-border-subtle hover:border-lia-btn-primary-bg cursor-pointer'
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1">
          <h4 className="text-xs font-semibold text-lia-text-primary mb-1">
            {skill.name}
          </h4>
          <div className="flex items-center gap-1.5 flex-wrap">
            <Badge
              variant="outline"
              className={cn(
 'text-micro border',
                colors.border,
                colors.bg,
                colors.text
              )}
            >
              <CategoryIcon className="w-2.5 h-2.5 mr-0.5" />
              {CATEGORY_LABELS[skill.category]}
            </Badge>
            {skill.weight && (
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((w) => (
                  <Star
                    key={w}
                    className={cn(
 'w-2.5 h-2.5',
                      w <= skill.weight!
                        ? 'fill-lia-text-primary text-lia-text-secondary'
                        : 'lia-text-muted'
                    )}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {isSelected ? (
          <div className="flex-shrink-0 w-5 h-5 rounded-full bg-lia-btn-primary-bg flex items-center justify-center">
            <Check className="w-3 h-3 text-white" />
          </div>
        ) : (
          <button
            onClick={() => onAdd(skill)}
            disabled={isSelected}
            className="flex-shrink-0 w-5 h-5 rounded-full border-2 border-lia-btn-primary-bg text-lia-text-secondary hover:bg-lia-bg-tertiary transition-[width,height] flex items-center justify-center disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-lia-border-default"
            aria-label={`Adicionar ${skill.name}`}
          >
            <Plus className="w-3 h-3" />
          </button>
        )}
      </div>
      {skill.description && (
        <p className="text-micro lia-text-secondary line-clamp-2">
          {skill.description}
        </p>
      )}
    </div>
  )
}

interface TabContentProps {
  skills: Skill[]
  selectedSkills: Skill[]
  onAddSkill: (skill: Skill) => void
  tabLabel: string
}

function SkillsTabContent({ skills, selectedSkills, onAddSkill, tabLabel }: TabContentProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredSkills = useMemo(() => {
    if (!searchQuery.trim()) return skills
    const query = searchQuery.toLowerCase()
    return skills.filter(
      (skill) =>
        skill.name.toLowerCase().includes(query) ||
        skill.description?.toLowerCase().includes(query)
    )
  }, [skills, searchQuery])

  const selectedIds = new Set(selectedSkills.map((s) => s.id))

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-2.5 w-4 h-4 lia-text-secondary" />
        <Input
          placeholder={`Buscar ${tabLabel.toLowerCase()}...`}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 bg-lia-bg-primary border-lia-border-subtle text-lia-text-primary placeholder:lia-text-secondary rounded-md focus:border-lia-border-medium"
        />
      </div>

      {filteredSkills.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-xs lia-text-secondary">
            {searchQuery ? 'Nenhum resultado encontrado' : 'Nenhuma skill disponível'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-content-lg overflow-y-auto pr-2">
          {filteredSkills.map((skill) => (
            <SkillCard
              key={skill.id}
              skill={skill}
              isSelected={selectedIds.has(skill.id)}
              onAdd={onAddSkill}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface CustomSkillFormProps {
  onAddCustomSkill: (skill: Skill) => void
  selectedSkills: Skill[]
}

function CustomSkillForm({ onAddCustomSkill, selectedSkills }: CustomSkillFormProps) {
  const [name, setName] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<Skill['category']>('general')
  const [weight, setWeight] = useState(3)
  const [error, setError] = useState('')
  const [saveToCatalog, setSaveToCatalog] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')

    if (!name.trim()) {
      setError('Nome da skill é obrigatório')
      return
    }

    // Check for duplicates
    if (selectedSkills.some((s) => s.name.toLowerCase() === name.toLowerCase())) {
      setError('Esta skill já foi adicionada')
      return
    }

    const customSkill: Skill = {
      id: `custom-${Date.now()}`,
      name: name.trim(),
      category: selectedCategory,
      weight,
    }

    // Save to company catalog if toggle is on
    if (saveToCatalog) {
      setIsSaving(true)
      try {
        const response = await fetch('/api/backend-proxy/company/skills-catalog', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            company_id: 'default',
            skill_name: name.trim(),
            category: selectedCategory,
            default_weight: weight,
            default_level: 'Intermediário',
          }),
        })

        if (!response.ok) {
          throw new Error('Falha ao salvar no catálogo')
        }

        setSuccessMessage('Skill salva no catálogo da empresa!')
      } catch (err) {
        setError('Erro ao salvar no catálogo. Clique novamente para tentar ou desative a opção para adicionar apenas à vaga.')
        setIsSaving(false)
        return // Don't add skill or reset form - let user retry
      } finally {
        setIsSaving(false)
      }
    }

    onAddCustomSkill(customSkill)
    setName('')
    setSelectedCategory('general')
    setWeight(3)
    setSaveToCatalog(false)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="skill-name" className="text-xs font-medium text-lia-text-primary">
          Nome da Skill
        </Label>
        <Input
          id="skill-name"
          placeholder="ex: Python, React, Docker..."
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="bg-lia-bg-primary border-lia-border-subtle rounded-md focus:border-lia-border-medium"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="skill-category" className="text-xs font-medium text-lia-text-primary">
          Categoria
        </Label>
        <Select value={selectedCategory} onValueChange={(v) => setSelectedCategory(v as Skill['category'])}>
          <SelectTrigger className="bg-lia-bg-secondary border-lia-border-subtle rounded-md">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.entries(CATEGORY_LABELS) as [Skill['category'], string][]).map(
              ([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              )
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="skill-weight" className="text-xs font-medium text-lia-text-primary">
          Peso/Importância
        </Label>
        <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary rounded-md">
          {[1, 2, 3, 4, 5].map((w) => (
            <button
              key={w}
              type="button"
              onClick={() => setWeight(w)}
              className="transition-colors motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-lia-border-default rounded-full"
              aria-label={`Peso ${w} de 5`}
            >
              <Star
                className={cn(
 'w-5 h-5 transition-colors',
                  w <= weight
                    ? 'fill-lia-text-primary text-lia-text-secondary'
                    : 'lia-text-muted'
                )}
              />
            </button>
          ))}
          <span className="ml-auto text-xs font-semibold text-lia-text-primary">
            {weight}/5
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
        <div className="space-y-0.5">
          <Label htmlFor="save-to-catalog" className="text-xs font-medium text-lia-text-primary cursor-pointer">
            Salvar no Catálogo da Empresa
          </Label>
          <p className="text-micro lia-text-secondary">
            Skill ficará disponível para futuras vagas
          </p>
        </div>
        <Switch
          id="save-to-catalog"
          checked={saveToCatalog}
          onCheckedChange={setSaveToCatalog}
        />
      </div>

      {successMessage && (
        <div className="p-2.5 bg-wedo-green/15 border border-wedo-green/30 rounded-md">
          <p className="text-xs text-wedo-green">{successMessage}</p>
        </div>
      )}

      {error && (
        <div className="p-2.5 bg-status-error/10 border border-status-error/30 rounded-md">
          <p className="text-xs text-status-error">{error}</p>
        </div>
      )}

      <Button
        type="submit"
        disabled={isSaving}
        className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text font-medium text-xs rounded-md disabled:opacity-50"
      >
        <Plus className="w-3.5 h-3.5 mr-1.5" />
        {isSaving ? 'Salvando...' : 'Adicionar Skill Customizado'}
      </Button>
    </form>
  )
}

export function AddSkillModal({
  open,
  onOpenChange,
  category,
  companyCatalog,
  marketSuggestions,
  selectedSkills,
  onAddSkill,
}: AddSkillModalProps) {
  const [activeTab, setActiveTab] = useState('catalog')

  // Filter skills by category
  const catalogByCategory = companyCatalog.filter((s) => s.category === category)
  const suggestionsWithoutSelected = marketSuggestions.filter(
    (s) =>
      s.category === category && !selectedSkills.some((sel) => sel.id === s.id)
  )

  const handleAddCustomSkill = (skill: Skill) => {
    onAddSkill(skill)
    // Reset to first tab after adding
    setActiveTab('catalog')
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-lia-bg-primary border border-lia-border-subtle rounded-md" role="dialog" aria-modal="true" aria-labelledby="add-skill-modal-title">
        <DialogHeader>
          <DialogTitle id="add-skill-modal-title" className="text-sm font-semibold text-lia-text-primary">
            Adicionar Skill: {CATEGORY_LABELS[category]}
          </DialogTitle>
          <p className="text-xs text-lia-text-tertiary mt-1">
            Selecione uma skill do catálogo, sugestões de mercado ou crie uma customizada
          </p>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-lia-bg-secondary p-1 rounded-md mb-4">
            <TabsTrigger
              value="catalog"
              className="text-xs font-medium rounded-md data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-secondary text-lia-text-tertiary"
            >
              Catálogo da Empresa
            </TabsTrigger>
            <TabsTrigger
              value="market"
              className="text-xs font-medium rounded-md data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-secondary text-lia-text-tertiary"
            >
              Sugestões de Mercado
            </TabsTrigger>
            <TabsTrigger
              value="custom"
              className="text-xs font-medium rounded-md data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-secondary text-lia-text-tertiary"
            >
              Skill Customizado
            </TabsTrigger>
          </TabsList>

          <TabsContent value="catalog" className="space-y-3">
            {catalogByCategory.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-xs lia-text-secondary">
                  Nenhuma skill de {CATEGORY_LABELS[category].toLowerCase()} no catálogo da empresa
                </p>
              </div>
            ) : (
              <SkillsTabContent
                skills={catalogByCategory}
                selectedSkills={selectedSkills}
                onAddSkill={onAddSkill}
                tabLabel={CATEGORY_LABELS[category]}
              />
            )}
          </TabsContent>

          <TabsContent value="market" className="space-y-3">
            {suggestionsWithoutSelected.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-xs lia-text-secondary">
                  Nenhuma sugestão de mercado disponível para {CATEGORY_LABELS[category].toLowerCase()}
                </p>
              </div>
            ) : (
              <SkillsTabContent
                skills={suggestionsWithoutSelected}
                selectedSkills={selectedSkills}
                onAddSkill={onAddSkill}
                tabLabel={`sugestões para ${CATEGORY_LABELS[category].toLowerCase()}`}
              />
            )}
          </TabsContent>

          <TabsContent value="custom" className="space-y-3">
            <CustomSkillForm onAddCustomSkill={handleAddCustomSkill} selectedSkills={selectedSkills} />
          </TabsContent>
        </Tabs>

        <DialogFooter className="pt-4 border-t border-lia-border-subtle">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="border-lia-border-subtle lia-text-secondary hover:bg-lia-interactive-hover rounded-md focus-visible:ring-2 focus-visible:ring-lia-border-default"
            aria-label="Fechar"
          >
            <X className="w-3.5 h-3.5 mr-1.5" />
            Fechar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
