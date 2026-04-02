"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SaveCommandModal, SavedCommandData } from "@/components/save-command-modal"
import {
  Edit, Trash2, Star, Copy, MessageCircle, Calendar,
  User, Filter, Search, Plus, MoreHorizontal,
  BookOpen, Clock, Check, X, AlertCircle
} from "lucide-react"

interface UserCommand extends SavedCommandData {
  id: string
  createdAt: string
  lastUsed?: string
  usageCount: number
  rating: number
  author: string
}

interface UserCommandsSectionProps {
  searchTerm: string
  selectedCategory: string
}

export function UserCommandsSection({ searchTerm, selectedCategory }: UserCommandsSectionProps) {
  const [userCommands, setUserCommands] = useState<UserCommand[]>([])
  const [editingCommand, setEditingCommand] = useState<UserCommand | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [commandToDelete, setCommandToDelete] = useState<UserCommand | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  // Carregar comandos do localStorage
  useEffect(() => {
    const savedCommands = localStorage.getItem('lia-user-commands')
    if (savedCommands) {
      try {
        const commands = JSON.parse(savedCommands)
        setUserCommands(commands)
      } catch (error) {
      }
    } else {
      // Mock data inicial
      const mockCommands: UserCommand[] = [
        {
          id: '1',
          title: 'Análise Completa de Candidatos Tech',
          command: 'Analise todos os candidatos de tecnologia com foco em React e Node.js',
          description: 'Comando personalizado para análise detalhada de candidatos da área de tecnologia com foco em stack React/Node.js',
          category: 'candidates',
          examples: [
            'Analise todos os candidatos de tecnologia com foco em React e Node.js',
            'Mostre candidatos tech com experiência fullstack',
            'Liste desenvolvedores com stack moderna'
          ],
          tags: ['tecnologia', 'react', 'nodejs', 'fullstack'],
          createdAt: '2025-03-15T10:30:00Z',
          lastUsed: '2025-03-20T14:22:00Z',
          usageCount: 12,
          rating: 4.5,
          author: 'Ana Silva'
        },
        {
          id: '2',
          title: 'Relatório de Performance Semanal',
          command: 'Gere relatório completo da semana com métricas principais',
          description: 'Relatório automático com todas as métricas importantes da semana para apresentação gerencial',
          category: 'reports',
          examples: [
            'Gere relatório completo da semana com métricas principais',
            'Relatório semanal para gerência',
            'Métricas da semana consolidadas'
          ],
          tags: ['relatório', 'semanal', 'métricas', 'gerência'],
          createdAt: '2025-03-10T09:15:00Z',
          lastUsed: '2025-03-19T16:45:00Z',
          usageCount: 8,
          rating: 5,
          author: 'Ana Silva'
        },
        {
          id: '3',
          title: 'Busca Inteligente por Skills',
          command: 'Encontre candidatos com skills específicas e disponibilidade imediata',
          description: 'Busca avançada que combina skills técnicas com disponibilidade para início imediato',
          category: 'candidates',
          examples: [
            'Encontre candidatos com skills específicas e disponibilidade imediata',
            'Busque profissionais disponíveis com Python',
            'Candidatos com React disponíveis para começar'
          ],
          tags: ['busca', 'skills', 'disponibilidade'],
          createdAt: '2025-03-12T11:20:00Z',
          usageCount: 5,
          rating: 3.5,
          author: 'Ana Silva'
        }
      ]
      setUserCommands(mockCommands)
      localStorage.setItem('lia-user-commands', JSON.stringify(mockCommands))
    }
  }, [])

  // Salvar comandos no localStorage
  const saveCommands = (commands: UserCommand[]) => {
    localStorage.setItem('lia-user-commands', JSON.stringify(commands))
    setUserCommands(commands)
  }

  // Filtrar comandos baseado na busca e categoria
  const filteredCommands = userCommands.filter(cmd => {
    const matchesCategory = selectedCategory === "all" || cmd.category === selectedCategory
    const matchesSearch = searchTerm === "" ||
      cmd.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cmd.command.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cmd.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cmd.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))

    return matchesCategory && matchesSearch
  })

  // Adicionar novo comando
  const addCommand = (commandData: SavedCommandData) => {
    const newCommand: UserCommand = {
      ...commandData,
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
      usageCount: 1,
      rating: 0,
      author: 'Ana Silva' // Current user
    }

    const updatedCommands = [newCommand, ...userCommands]
    saveCommands(updatedCommands)
  }

  // Editar comando
  const handleEditCommand = (command: UserCommand) => {
    setEditingCommand(command)
    setShowEditModal(true)
  }

  const saveEditedCommand = (commandData: SavedCommandData) => {
    if (!editingCommand) return

    const updatedCommand: UserCommand = {
      ...editingCommand,
      ...commandData,
    }

    const updatedCommands = userCommands.map(cmd =>
      cmd.id === editingCommand.id ? updatedCommand : cmd
    )

    saveCommands(updatedCommands)
    setEditingCommand(null)
    setShowEditModal(false)
  }

  // Excluir comando
  const handleDeleteCommand = (command: UserCommand) => {
    setCommandToDelete(command)
    setShowDeleteConfirm(true)
  }

  const confirmDelete = () => {
    if (!commandToDelete) return

    const updatedCommands = userCommands.filter(cmd => cmd.id !== commandToDelete.id)
    saveCommands(updatedCommands)
    setCommandToDelete(null)
    setShowDeleteConfirm(false)
  }

  // Avaliar comando
  const rateCommand = (commandId: string, rating: number) => {
    const updatedCommands = userCommands.map(cmd =>
      cmd.id === commandId ? { ...cmd, rating } : cmd
    )
    saveCommands(updatedCommands)
  }

  // Incrementar uso do comando
  const incrementUsage = (commandId: string) => {
    const updatedCommands = userCommands.map(cmd =>
      cmd.id === commandId
        ? { ...cmd, usageCount: cmd.usageCount + 1, lastUsed: new Date().toISOString() }
        : cmd
    )
    saveCommands(updatedCommands)
  }

  // Copiar comando
  const copyCommand = (command: UserCommand) => {
    navigator.clipboard.writeText(command.command)
    incrementUsage(command.id)
  }

  // Renderizar estrelas de avaliação
  const renderStars = (command: UserCommand) => {
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => rateCommand(command.id, star)}
            className="hover:scale-110 transition-transform motion-reduce:transition-none"
          >
            <Star
              className={`w-3 h-3 ${
 star <= command.rating
                  ? 'text-status-warning fill-yellow-500'
                  : 'lia-text-muted'
              }`}
            />
          </button>
        ))}
        <span className="text-xs text-lia-text-primary ml-1">
          ({command.rating > 0 ? command.rating.toFixed(1) : 'Sem avaliação'})
        </span>
      </div>
    )
  }

  // Formatar data
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const formatLastUsed = (dateString?: string) => {
    if (!dateString) return 'Nunca usado'

    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Hoje'
    if (diffDays === 1) return 'Ontem'
    if (diffDays < 7) return `${diffDays} dias atrás`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} semanas atrás`
    return formatDate(dateString)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-lia-text-primary">
            Meus Comandos Personalizados
          </h2>
          <p className="text-sm text-lia-text-secondary">
            {filteredCommands.length} {filteredCommands.length === 1 ? 'comando' : 'comandos'}
            {searchTerm && ` encontrado${filteredCommands.length !== 1 ? 's' : ''} para "${searchTerm}"`}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            <User className="w-3 h-3 mr-1" />
            Ana Silva
          </Badge>
        </div>
      </div>

      {/* Lista de Comandos */}
      {filteredCommands.length === 0 ? (
        <Card className="bg-white dark:bg-lia-bg-secondary p-8 text-center">
          <div className="text-lia-text-primary">
            <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">
              {searchTerm ? 'Nenhum comando encontrado' : 'Nenhum comando personalizado ainda'}
            </h3>
            <p className="text-sm">
              {searchTerm
                ? 'Tente ajustar os termos de busca ou filtros'
                : 'Use a busca com IA para criar seus primeiros comandos personalizados'
              }
            </p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredCommands.map((command) => (
            <Card key={command.id} className="hover:transition-shadow bg-white dark:bg-lia-bg-secondary">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-base font-semibold text-lia-text-primary mb-2">
                      {command.title}
                    </CardTitle>
                    <div className="flex flex-wrap gap-1 mb-2">
                      {command.tags.map((tag, tagIndex) => (
                        <Badge key={tagIndex} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    {renderStars(command)}
                  </div>

                  <div className="flex items-center gap-1 ml-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyCommand(command)}
                      className="h-8 w-8 p-0"
                      title="Copiar comando"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditCommand(command)}
                      className="h-8 w-8 p-0"
                      title="Editar comando"
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteCommand(command)}
                      className="h-8 w-8 p-0 text-status-error hover:text-status-error"
                      title="Excluir comando"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Comando */}
                <div className="bg-gray-50 dark:bg-lia-bg-elevated rounded-md p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageCircle className="w-4 h-4 text-wedo-purple" />
                    <span className="text-xs font-medium text-lia-text-primary">Comando:</span>
                  </div>
                  <code className="text-sm text-wedo-purple dark:text-wedo-purple font-mono">
                    {command.command}
                  </code>
                </div>

                {/* Descrição */}
                <p className="text-xs text-lia-text-secondary leading-relaxed">
                  {command.description}
                </p>

                {/* Estatísticas */}
                <div className="flex items-center justify-between text-xs text-lia-text-primary bg-gray-50 dark:bg-lia-bg-elevated rounded-md p-2">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>Criado: {formatDate(command.createdAt)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>Usado: {formatLastUsed(command.lastUsed)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <span>{command.usageCount}x usado</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modal de Edição */}
      {showEditModal && editingCommand && (
        <SaveCommandModal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false)
            setEditingCommand(null)
          }}
          originalCommand={editingCommand.command}
          commandResult={editingCommand.result}
          onSave={saveEditedCommand}
          // Passar dados existentes para edição
          existingData={{
            title: editingCommand.title,
            description: editingCommand.description,
            category: editingCommand.category,
            examples: editingCommand.examples,
            tags: editingCommand.tags
          }}
        />
      )}

      {/* Modal de Confirmação de Exclusão */}
      {showDeleteConfirm && commandToDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md bg-white dark:bg-lia-bg-secondary">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-lia-text-primary flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-status-error" />
                Confirmar Exclusão
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-lia-text-secondary">
                Tem certeza que deseja excluir o comando <strong>"{commandToDelete.title}"</strong>?
              </p>
              <p className="text-xs text-lia-text-primary">
                Esta ação não pode ser desfeita. O comando foi usado {commandToDelete.usageCount} vezes.
              </p>

              <div className="flex justify-end gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowDeleteConfirm(false)
                    setCommandToDelete(null)
                  }}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={confirmDelete}
                  className="bg-status-error hover:bg-status-error text-white"
                >
                  Excluir Comando
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

// Hook para adicionar comando externamente
export const useUserCommands = () => {
  const addUserCommand = (commandData: SavedCommandData) => {
    const savedCommands = localStorage.getItem('lia-user-commands')
    const commands = savedCommands ? JSON.parse(savedCommands) : []

    const newCommand: UserCommand = {
      ...commandData,
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
      usageCount: 1,
      rating: 0,
      author: 'Ana Silva'
    }

    const updatedCommands = [newCommand, ...commands]
    localStorage.setItem('lia-user-commands', JSON.stringify(updatedCommands))
  }

  return { addUserCommand }
}
