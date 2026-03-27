"use client"

import { useState, useEffect } from "react"
import { liaApi, CandidateList } from "@/services/lia-api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/hooks/use-toast"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription
} from "@/components/ui/dialog"
import { List, Plus, Check, Loader2, Users, X } from "lucide-react"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

const LIST_COLORS = [
  { value: 'var(--gray-400)', name: 'Cinza' },
  { value: 'var(--gray-600)', name: 'Cyan (LIA)' },
  { value: 'var(--status-success)', name: 'Verde' },
  { value: 'var(--status-warning)', name: 'Amarelo' },
  { value: 'var(--status-error)', name: 'Vermelho' },
  { value: 'var(--wedo-purple)', name: 'Roxo' },
]

interface AddToListModalProps {
  isOpen: boolean
  onClose: () => void
  candidateIds: string[]
  candidateNames?: string[]
  onSuccess?: () => void
}

export function AddToListModal({ 
  isOpen, 
  onClose, 
  candidateIds, 
  candidateNames, 
  onSuccess 
}: AddToListModalProps) {
  const { toast } = useToast()
  const [lists, setLists] = useState<CandidateList[]>([])
  const [selectedListId, setSelectedListId] = useState<string | null>(null)
  const [isCreatingNew, setIsCreatingNew] = useState(false)
  const [newListName, setNewListName] = useState('')
  const [newListColor, setNewListColor] = useState('var(--gray-400)')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadLists()
      setSelectedListId(null)
      setIsCreatingNew(false)
      setNewListName('')
      setNewListColor('var(--gray-400)')
    }
  }, [isOpen])

  const loadLists = async () => {
    setIsLoading(true)
    try {
      const response = await liaApi.getCandidateLists({ limit: 100 })
      setLists(response.items)
      if (response.items.length === 0) {
        setIsCreatingNew(true)
      }
    } catch (error) {
      toast({ title: "Erro ao carregar listas", variant: "destructive" })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (isSubmitting) return
    
    if (!isCreatingNew && !selectedListId) {
      toast({ title: "Selecione ou crie uma lista", variant: "destructive" })
      return
    }
    
    if (isCreatingNew && !newListName.trim()) {
      toast({ title: "Digite um nome para a lista", variant: "destructive" })
      return
    }
    
    setIsSubmitting(true)
    try {
      let listId = selectedListId
      
      if (isCreatingNew && newListName.trim()) {
        const newList = await liaApi.createCandidateList({
          name: newListName.trim(),
          color: newListColor
        })
        listId = newList.id
      }
      
      if (!listId) {
        toast({ title: "Selecione ou crie uma lista", variant: "destructive" })
        setIsSubmitting(false)
        return
      }
      
      const result = await liaApi.addCandidatesToList(listId, candidateIds)
      
      toast({
        title: "Candidatos adicionados",
        description: `${result.added} adicionado(s)${result.already_exists > 0 ? `, ${result.already_exists} já estava(m) na lista` : ''}`
      })
      
      onSuccess?.()
      onClose()
    } catch (error) {
      toast({ title: "Erro ao adicionar candidatos", variant: "destructive" })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
    }
  }

  const candidateCount = candidateIds.length
  const displayNames = candidateNames?.slice(0, 3) || []
  const remainingCount = candidateCount > 3 ? candidateCount - 3 : 0

  const canSubmit = isCreatingNew ? newListName.trim().length > 0 : selectedListId !== null

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className={`max-w-md ${cardStyles.default}`}>
        <DialogHeader>
          <DialogTitle className={`${textStyles.title} flex items-center gap-2`}>
            <List className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            Adicionar à Lista
          </DialogTitle>
          <DialogDescription className={textStyles.bodySmall} asChild>
            <div>
              <span className="flex items-center gap-2 mt-1">
                <Users className="w-4 h-4 text-gray-500" />
                <span>
                  {candidateCount} candidato{candidateCount !== 1 ? 's' : ''} selecionado{candidateCount !== 1 ? 's' : ''}
                </span>
              </span>
              {displayNames.length > 0 && (
                <span className="block mt-2 text-gray-800 dark:text-gray-200">
                  {displayNames.join(', ')}
                  {remainingCount > 0 && ` e mais ${remainingCount}`}
                </span>
              )}
            </div>
          </DialogDescription>
        </DialogHeader>

        <div className="py-4 space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
            </div>
          ) : (
            <>
              {lists.length > 0 && !isCreatingNew && (
                <div className="space-y-2">
                  <Label className={textStyles.label}>
                    Selecione uma lista
                  </Label>
                  <RadioGroup
                    value={selectedListId || ''}
                    onValueChange={(value) => setSelectedListId(value)}
                    className="space-y-2"
                  >
                    {lists.map((list) => (
                      <div
                        key={list.id}
                        className={cn(
                          "flex items-center space-x-3 p-3 rounded-md border border-gray-100 cursor-pointer transition-all hover:border-gray-300",
                          selectedListId === list.id && "border-gray-800 bg-gray-50"
                        )}
                        onClick={() => setSelectedListId(list.id)}
                      >
                        <RadioGroupItem value={list.id} id={list.id} />
                        <div
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: list.color || 'var(--gray-400)' }}
                        />
                        <div className="flex-1 min-w-0">
                          <Label
                            htmlFor={list.id}
                            className={`${textStyles.subtitle} cursor-pointer block truncate`}
                          >
                            {list.name}
                          </Label>
                          <span className={textStyles.bodySmall}>
                            {list.candidate_count} candidato{list.candidate_count !== 1 ? 's' : ''}
                          </span>
                        </div>
                        {selectedListId === list.id && (
                          <Check className="w-4 h-4 flex-shrink-0 text-gray-600 dark:text-gray-400" />
                        )}
                      </div>
                    ))}
                  </RadioGroup>
                </div>
              )}

              {!isCreatingNew && lists.length > 0 && (
                <div className="pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full border-dashed border-gray-300 text-gray-800 dark:text-gray-200 hover:border-gray-400 hover:text-gray-800"
                    onClick={() => {
                      setIsCreatingNew(true)
                      setSelectedListId(null)
                    }}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Criar nova lista
                  </Button>
                </div>
              )}

              {isCreatingNew && (
                <div className={`space-y-4 p-4 ${cardStyles.flat}`}>
                  <div className="flex items-center justify-between">
                    <Label className={textStyles.label}>
                      Nova lista
                    </Label>
                    {lists.length > 0 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-xs text-gray-800 dark:text-gray-200 hover:text-gray-800"
                        onClick={() => {
                          setIsCreatingNew(false)
                          setNewListName('')
                          setNewListColor('var(--gray-400)')
                        }}
                      >
                        <X className="w-3 h-3 mr-1" />
                        Cancelar
                      </Button>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="new-list-name" className={textStyles.description}>
                      Nome da lista
                    </Label>
                    <Input
                      id="new-list-name"
                      value={newListName}
                      onChange={(e) => setNewListName(e.target.value)}
                      placeholder="Ex: Candidatos Finalistas"
                      className="border-gray-100 rounded-md"
                      autoFocus
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className={textStyles.description}>
                      Cor da lista
                    </Label>
                    <div className="flex gap-2">
                      {LIST_COLORS.map((color) => (
                        <button
                          key={color.value}
                          type="button"
                          className={cn(
                            "w-8 h-8 rounded-md border-2 transition-all flex items-center justify-center",
                            newListColor === color.value
                              ? "border-gray-900 scale-110"
                              : "border-transparent hover:scale-105"
                          )}
                          style={{ backgroundColor: color.value }}
                          onClick={() => setNewListColor(color.value)}
                          title={color.name}
                        >
                          {newListColor === color.value && (
                            <Check className="w-4 h-4 text-white drop-shadow" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 -mx-6 -mb-6 rounded-b-xl">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
            className="h-9 px-4 text-xs font-medium bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 dark:text-gray-200"
          >
            Cancelar
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || isLoading || !canSubmit}
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Adicionando...
              </>
            ) : (
              <>
                <Plus className="w-4 h-4 mr-2" />
                Adicionar à Lista
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
