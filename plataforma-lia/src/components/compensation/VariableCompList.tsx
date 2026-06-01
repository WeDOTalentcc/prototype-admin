"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { ChevronDown, ChevronRight, Plus, Coins } from "lucide-react"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { VariableCompItemCard } from "./VariableCompItemCard"
import { COMP_KIND_GROUPS, type VariableCompRecord } from "./variable-comp-types"

interface VariableCompListProps {
  components: VariableCompRecord[]
  isEditing: boolean
  onToggle: (c: VariableCompRecord) => void
  onEdit: (c: VariableCompRecord) => void
  onCreateInKind: (kind: string) => void
  onDelete: (id: string) => void
  mode?: "catalog" | "vacancy"
  linkedIds?: Set<string>
}

export function VariableCompList({
  components,
  isEditing,
  onToggle,
  onEdit,
  onCreateInKind,
  onDelete,
  mode = "catalog",
  linkedIds,
}: VariableCompListProps) {
  const isVacancy = mode === "vacancy"
  const [expanded, setExpanded] = React.useState<string[]>(COMP_KIND_GROUPS.map((g) => g.id))
  const toggleGroup = (id: string) =>
    setExpanded((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))

  // so mostra grupos com itens (catalogo pode ter muitos tipos vazios)
  const groups = COMP_KIND_GROUPS.filter(
    (g) => components.some((c) => c.kind === g.id) || (isEditing && !isVacancy),
  )

  return (
    <div className="space-y-3">
      {groups.map((group) => {
        const items = components.filter((c) => c.kind === group.id)
        const isOpen = expanded.includes(group.id)
        const Icon = group.icon
        const linkedCount = items.filter((c) => c.id && linkedIds?.has(c.id)).length

        return (
          <Card key={group.id} className={`${cardStyles.default} dark:border-lia-border-subtle/50 dark:bg-lia-bg-secondary/80 rounded-md overflow-hidden`}>
            <div
              className={`flex items-center justify-between p-3 cursor-pointer transition-colors ${group.bgColor}`}
              onClick={() => toggleGroup(group.id)}
              role="button"
              tabIndex={0}
              aria-expanded={isOpen}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleGroup(group.id) } }}
            >
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary">
                  <Icon className={`w-4 h-4 ${group.color}`} />
                </div>
                <div>
                  <h3 className={textStyles.title}>{group.label}</h3>
                  <p className={textStyles.caption}>{items.length} {items.length === 1 ? "verba" : "verbas"}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {isVacancy ? (
                  <Chip variant="neutral" className="text-micro">{linkedCount} vinculadas</Chip>
                ) : (
                  <Chip variant="neutral" className="text-micro">{items.filter((c) => c.is_active !== false).length} ativas</Chip>
                )}
                {isOpen ? <ChevronDown className="w-4 h-4 text-lia-text-secondary" /> : <ChevronRight className="w-4 h-4 text-lia-text-secondary" />}
              </div>
            </div>

            {isOpen && (
              <CardContent className="p-0">
                {items.length === 0 ? (
                  <div className="p-3 text-center">
                    <Coins className="w-4 h-4 mx-auto text-lia-text-disabled mb-2" />
                    <p className={textStyles.bodySmall}>Nenhuma verba deste tipo</p>
                    {!isVacancy && (
                      <Button variant="ghost" size="sm" className="mt-2 text-xs" onClick={() => onCreateInKind(group.id)} disabled={!isEditing}>
                        <Plus className="w-3.5 h-3.5 mr-1" />Adicionar
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                    {items.map((c) => (
                      <VariableCompItemCard
                        key={c.id || c.name}
                        component={c}
                        isEditing={isEditing}
                        onToggle={onToggle}
                        onEdit={onEdit}
                        onDelete={onDelete}
                        mode={mode}
                        isLinked={isVacancy && c.id ? !!linkedIds?.has(c.id) : false}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            )}
          </Card>
        )
      })}
    </div>
  )
}
