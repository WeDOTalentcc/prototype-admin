"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { liaApi, CandidateProfile } from "@/services/lia-api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useToast } from "@/hooks/use-toast"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Search, Upload, Link2, ArrowRight, Check, Loader2, UserPlus, X
} from "lucide-react"

interface AddCandidateToListModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  listId: string
  listName: string
  onCandidatesAdded: (candidateIds: string[]) => void
  onGoToSearch: () => void
}

export function AddCandidateToListModal({
  open,
  onOpenChange,
  listId,
  listName,
  onCandidatesAdded,
  onGoToSearch,
}: AddCandidateToListModalProps) {
  const { toast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<CandidateProfile[]>([])
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set())
  const [searching, setSearching] = useState(false)
  const [adding, setAdding] = useState(false)
  
  const [linkedinUrl, setLinkedinUrl] = useState("")
  const [importingLinkedin, setImportingLinkedin] = useState(false)
  const [uploadingCV, setUploadingCV] = useState(false)

  useEffect(() => {
    if (!open) {
      setSearchQuery("")
      setSearchResults([])
      setSelectedCandidates(new Set())
      setLinkedinUrl("")
    }
  }, [open])

  const debounceRef = useRef<NodeJS.Timeout | null>(null)

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 2) {
      setSearchResults([])
      return
    }

    setSearching(true)
    try {
      const response = await liaApi.searchCandidates({
        query: query.trim(),
        search_type: 'fast',
        limit: 10,
      })
      setSearchResults(response.candidates || [])
    } catch (error) {
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }, [])

  const onSearchChange = (value: string) => {
    setSearchQuery(value)
    
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }
    
    debounceRef.current = setTimeout(() => {
      handleSearch(value)
    }, 300)
  }

  const toggleCandidate = (candidateId: string) => {
    setSelectedCandidates(prev => {
      const next = new Set(prev)
      if (next.has(candidateId)) {
        next.delete(candidateId)
      } else {
        next.add(candidateId)
      }
      return next
    })
  }

  const handleAddCandidates = async () => {
    if (selectedCandidates.size === 0) return

    setAdding(true)
    try {
      const candidateIds = Array.from(selectedCandidates)
      await liaApi.addCandidatesToList(listId, candidateIds)
      
      toast({
        title: "Candidatos adicionados",
        description: `${candidateIds.length} candidato(s) adicionado(s) à lista "${listName}".`,
      })
      
      onCandidatesAdded(candidateIds)
      onOpenChange(false)
    } catch (error) {
      toast({
        title: "Erro ao adicionar",
        description: "Não foi possível adicionar os candidatos. Tente novamente.",
        variant: "destructive",
      })
    } finally {
      setAdding(false)
    }
  }

  const handleLinkedInImport = async () => {
    if (!linkedinUrl.trim()) return

    const urlPattern = /^https?:\/\/(www\.)?linkedin\.com\/(in|pub)\/[a-zA-Z0-9_-]+\/?/
    if (!urlPattern.test(linkedinUrl.trim())) {
      toast({
        title: "URL inválida",
        description: "Por favor, insira uma URL válida do LinkedIn.",
        variant: "destructive",
      })
      return
    }

    setImportingLinkedin(true)
    try {
      const response = await fetch('/api/backend-proxy/search/candidates/import/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ linkedin_url: linkedinUrl.trim() }),
      })
      
      if (!response.ok) throw new Error('Import failed')
      
      const data = await response.json()
      
      // Backend returns: { imported_count, updated_count, mapping: [{pearch_id, local_id}] }
      const localIds: string[] = []
      
      // Extract local IDs from mapping
      if (data.mapping && Array.isArray(data.mapping)) {
        for (const m of data.mapping) {
          if (m.local_id) {
            localIds.push(m.local_id)
          }
        }
      }
      
      // Fallback to candidate_id if provided directly
      if (localIds.length === 0 && data.candidate_id) {
        localIds.push(data.candidate_id)
      }
      
      if (localIds.length > 0) {
        await liaApi.addCandidatesToList(listId, localIds)
        toast({
          title: "Candidato importado",
          description: `${localIds.length} candidato(s) do LinkedIn adicionado(s) à lista "${listName}".`,
        })
        onCandidatesAdded(localIds)
        onOpenChange(false)
      } else if (data.imported_count > 0 || data.updated_count > 0) {
        toast({
          title: "Candidato importado",
          description: "Candidato salvo na base, mas sem ID para adicionar à lista.",
        })
      } else {
        toast({
          title: "Nenhum candidato",
          description: "Não foi possível importar candidatos do LinkedIn.",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Erro na importação",
        description: "Não foi possível importar o candidato do LinkedIn.",
        variant: "destructive",
      })
    } finally {
      setImportingLinkedin(false)
      setLinkedinUrl("")
    }
  }

  const handleCVUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const validTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    if (!validTypes.includes(file.type)) {
      toast({
        title: "Formato inválido",
        description: "Por favor, envie um arquivo PDF, DOC ou DOCX.",
        variant: "destructive",
      })
      return
    }

    setUploadingCV(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/backend-proxy/cv/upload/', {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) throw new Error('Upload failed')
      
      const data = await response.json()
      
      // CV upload can return candidate_id directly or mapping array
      const localIds: string[] = []
      
      // Check for direct candidate_id
      if (data.candidate_id) {
        localIds.push(data.candidate_id)
      }
      
      // Also check mapping array format
      if (data.mapping && Array.isArray(data.mapping)) {
        for (const m of data.mapping) {
          if (m.local_id) {
            localIds.push(m.local_id)
          }
        }
      }
      
      if (localIds.length > 0) {
        await liaApi.addCandidatesToList(listId, localIds)
        toast({
          title: "CV importado",
          description: `Candidato do CV adicionado à lista "${listName}".`,
        })
        onCandidatesAdded(localIds)
        onOpenChange(false)
      } else if (data.success || data.parsed) {
        toast({
          title: "CV processado",
          description: "CV importado com sucesso. Busque o candidato para adicionar à lista.",
        })
      } else {
        toast({
          title: "CV processado",
          description: "CV importado, mas precisa ser adicionado manualmente.",
        })
      }
    } catch (error) {
      toast({
        title: "Erro no upload",
        description: "Não foi possível processar o CV.",
        variant: "destructive",
      })
    } finally {
      setUploadingCV(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  const handleGoToSearch = () => {
    onOpenChange(false)
    onGoToSearch()
  }

  const getInitials = (name: string | null) => {
    if (!name) return "?"
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg bg-white dark:bg-gray-900 border-0 rounded-md">
        <DialogHeader className="border-b border-gray-200 dark:border-gray-700 pb-4">
          <DialogTitle className="font-['Open_Sans',sans-serif] text-lg text-gray-950 dark:text-gray-50">
            Adicionar Candidatos à Lista "{listName}"
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-2">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-800 dark:text-gray-200">
              <Search className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              Buscar na Base
            </div>
            
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Buscar por nome, email ou ID..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-10 bg-gray-50 dark:bg-gray-800 border-0 focus:ring-1 focus:ring-gray-300"
              />
              {searching && (
                <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
              )}
            </div>

            {searchResults.length > 0 && (
              <div className="max-h-48 overflow-y-auto space-y-1 bg-gray-50 dark:bg-gray-800 rounded-md p-2">
                {searchResults.map((candidate) => {
                  const candidateId = candidate.id || ""
                  const isSelected = selectedCandidates.has(candidateId)
                  
                  return (
                    <button
                      key={candidateId}
                      type="button"
                      onClick={() => candidateId && toggleCandidate(candidateId)}
                      className={`w-full flex items-center gap-3 p-2 rounded-md transition-colors text-left ${
                        isSelected 
                          ? 'bg-gray-50' 
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className={`flex-shrink-0 w-5 h-5 rounded-md flex items-center justify-center transition-colors ${
                        isSelected 
                          ? 'bg-gray-800' 
                          : 'bg-gray-200 dark:bg-gray-600'
                      }`}>
                        {isSelected && <Check className="w-3 h-3 text-white" />}
                      </div>
                      
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={undefined} />
                        <AvatarFallback className="bg-gray-200 dark:bg-gray-600 text-xs text-gray-600 dark:text-gray-300">
                          {getInitials(candidate.name)}
                        </AvatarFallback>
                      </Avatar>
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-950 dark:text-gray-50 truncate">
                          {candidate.name || "Nome não disponível"}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {candidate.contact?.email || candidate.current_title || candidate.headline || ""}
                        </p>
                      </div>

                      {candidate.match_score && (
                        <span className="flex-shrink-0 text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                          {Math.round(candidate.match_score)}%
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            )}

            {searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-3">
                Nenhum candidato encontrado para "{searchQuery}"
              </p>
            )}

            {selectedCandidates.size > 0 && (
              <div className="flex items-center justify-between pt-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedCandidates.size} candidato(s) selecionado(s)
                </span>
                <Button
                  onClick={handleAddCandidates}
                  disabled={adding}
                  size="sm"
                  className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 gap-1.5"
                >
                  {adding ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Adicionando...
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-3.5 h-3.5" />
                      Adicionar
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-200 dark:border-gray-700" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white dark:bg-gray-900 px-2 text-gray-500">ou</span>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-800 dark:text-gray-200">
              <Upload className="w-4 h-4 text-gray-700" />
              Importar Novo Candidato
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <div className="relative">
                  <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Colar URL LinkedIn"
                    value={linkedinUrl}
                    onChange={(e) => setLinkedinUrl(e.target.value)}
                    className="pl-10 pr-10 text-xs bg-gray-50 dark:bg-gray-800 border-0"
                    disabled={importingLinkedin}
                  />
                  {linkedinUrl && (
                    <button
                      onClick={handleLinkedInImport}
                      disabled={importingLinkedin}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                    >
                      {importingLinkedin ? (
                        <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                      ) : (
                        <ArrowRight className="w-4 h-4 text-gray-500" />
                      )}
                    </button>
                  )}
                </div>
              </div>

              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleCVUpload}
                  className="hidden"
                  id="cv-upload"
                />
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full h-10 text-xs border-0 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingCV}
                >
                  {uploadingCV ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload CV
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-200 dark:border-gray-700" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white dark:bg-gray-900 px-2 text-gray-500">ou</span>
            </div>
          </div>

          <button
            onClick={handleGoToSearch}
            className="w-full flex items-center justify-between p-4 rounded-md bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-100 dark:bg-gray-700">
                <Search className="w-5 h-5 text-gray-700" />
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Ir para Busca Avançada
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Usar filtros e busca inteligente
                </p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors" />
          </button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
