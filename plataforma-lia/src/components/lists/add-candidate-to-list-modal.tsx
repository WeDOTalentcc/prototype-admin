"use client"

import { toast } from "sonner"
import { useState, useEffect, useCallback, useRef } from "react"
import { liaApi, CandidateProfile } from "@/services/lia-api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
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
      
      toast.success("Candidatos adicionados", { description: `${candidateIds.length} candidato(s) adicionado(s) à lista "${listName}".` })
      
      onCandidatesAdded(candidateIds)
      onOpenChange(false)
    } catch (error) {
      toast.error("Erro ao adicionar", { description: "Não foi possível adicionar os candidatos. Tente novamente." })
    } finally {
      setAdding(false)
    }
  }

  const handleLinkedInImport = async () => {
    if (!linkedinUrl.trim()) return

    const urlPattern = /^https?:\/\/(www\.)?linkedin\.com\/(in|pub)\/[a-zA-Z0-9_-]+\/?/
    if (!urlPattern.test(linkedinUrl.trim())) {
      toast.error("URL inválida", { description: "Por favor, insira uma URL válida do LinkedIn." })
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
        toast.success("Candidato importado", { description: `${localIds.length} candidato(s) do LinkedIn adicionado(s) à lista "${listName}".` })
        onCandidatesAdded(localIds)
        onOpenChange(false)
      } else if (data.imported_count > 0 || data.updated_count > 0) {
        toast.success("Candidato importado", { description: "Candidato salvo na base, mas sem ID para adicionar à lista." })
      } else {
        toast.error("Nenhum candidato", { description: "Não foi possível importar candidatos do LinkedIn." })
      }
    } catch (error) {
      toast.error("Erro na importação", { description: "Não foi possível importar o candidato do LinkedIn." })
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
      toast.error("Formato inválido", { description: "Por favor, envie um arquivo PDF, DOC ou DOCX." })
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
        toast.success("CV importado", { description: `Candidato do CV adicionado à lista "${listName}".` })
        onCandidatesAdded(localIds)
        onOpenChange(false)
      } else if (data.success || data.parsed) {
        toast.info("CV processado", { description: "CV importado com sucesso. Busque o candidato para adicionar à lista." })
      } else {
        toast.info("CV processado", { description: "CV importado, mas precisa ser adicionado manualmente." })
      }
    } catch (error) {
      toast.error("Erro no upload", { description: "Não foi possível processar o CV." })
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
      <DialogContent className="sm:max-w-lg bg-white dark:bg-lia-bg-primary border-0 rounded-md">
        <DialogHeader className="border-b border-lia-border-subtle dark:border-lia-border-subtle pb-4">
          <DialogTitle className="font-['Open_Sans',sans-serif] text-lg text-lia-text-primary">
            Adicionar Candidatos à Lista "{listName}"
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-2">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-lia-text-primary">
              <Search className="w-4 h-4 text-lia-text-secondary" />
              Buscar na Base
            </div>
            
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 lia-text-secondary" />
              <Input
                placeholder="Buscar por nome, email ou ID..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-10 bg-gray-50 dark:bg-lia-bg-secondary border-0 focus:ring-1 focus:ring-gray-300"
              />
              {searching && (
                <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin motion-reduce:animate-none lia-text-secondary" />
              )}
            </div>

            {searchResults.length > 0 && (
              <div className="max-h-48 overflow-y-auto space-y-1 bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-2">
                {searchResults.map((candidate) => {
                  const candidateId = candidate.id || ""
                  const isSelected = selectedCandidates.has(candidateId)
                  
                  return (
                    <button
                      key={candidateId}
                      type="button"
                      onClick={() => candidateId && toggleCandidate(candidateId)}
                      className={`w-full flex items-center gap-3 p-2 rounded-md transition-colors motion-reduce:transition-none text-left ${
 isSelected 
                          ? 'bg-gray-50' 
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className={`flex-shrink-0 w-5 h-5 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none ${
 isSelected 
                          ? 'bg-gray-800' 
                          : 'bg-gray-200'
                      }`}>
                        {isSelected && <Check className="w-3 h-3 text-white" />}
                      </div>
                      
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={undefined} />
                        <AvatarFallback className="bg-gray-200 text-xs text-lia-text-secondary">
                          {getInitials(candidate.name)}
                        </AvatarFallback>
                      </Avatar>
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-lia-text-primary truncate">
                          {candidate.name || "Nome não disponível"}
                        </p>
                        <p className="text-xs text-lia-text-tertiary truncate">
                          {candidate.contact?.email || candidate.current_title || candidate.headline || ""}
                        </p>
                      </div>

                      {candidate.match_score && (
                        <span className="flex-shrink-0 text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary">
                          {Math.round(candidate.match_score)}%
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            )}

            {searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
              <p className="text-sm text-lia-text-tertiary text-center py-3" aria-live="polite" aria-atomic="true">
                Nenhum candidato encontrado para "{searchQuery}"
              </p>
            )}

            {selectedCandidates.size > 0 && (
              <div className="flex items-center justify-between pt-2">
                <span className="text-sm text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                  {selectedCandidates.size} candidato(s) selecionado(s)
                </span>
                <Button
                  onClick={handleAddCandidates}
                  disabled={adding}
                  size="sm"
                  className="bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200 gap-1.5"
                >
                  {adding ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
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
              <span className="w-full border-t border-lia-border-subtle dark:border-lia-border-subtle" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white dark:bg-lia-bg-primary px-2 lia-text-secondary">ou</span>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-lia-text-primary">
              <Upload className="w-4 h-4 text-lia-text-secondary" />
              Importar Novo Candidato
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <div className="relative">
                  <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 lia-text-secondary" />
                  <Input
                    placeholder="Colar URL LinkedIn"
                    value={linkedinUrl}
                    onChange={(e) => setLinkedinUrl(e.target.value)}
                    className="pl-10 pr-10 text-xs bg-gray-50 dark:bg-lia-bg-secondary border-0"
                    disabled={importingLinkedin}
                  />
                  {linkedinUrl && (
                    <button
                      onClick={handleLinkedInImport}
                      disabled={importingLinkedin}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors motion-reduce:transition-none"
                    >
                      {importingLinkedin ? (
                        <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none lia-text-secondary" />
                      ) : (
                        <ArrowRight className="w-4 h-4 lia-text-secondary" />
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
                  className="w-full h-10 text-xs border-0 bg-gray-50 dark:bg-lia-bg-secondary hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingCV}
                >
                  {uploadingCV ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
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
              <span className="w-full border-t border-lia-border-subtle dark:border-lia-border-subtle" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white dark:bg-lia-bg-primary px-2 lia-text-secondary">ou</span>
            </div>
          </div>

          <button
            onClick={handleGoToSearch}
            className="w-full flex items-center justify-between p-4 rounded-md bg-gray-50 dark:bg-lia-bg-secondary hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors motion-reduce:transition-none group"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-100 dark:bg-lia-bg-elevated">
                <Search className="w-5 h-5 text-lia-text-secondary" />
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-lia-text-primary">
                  Ir para Busca Avançada
                </p>
                <p className="text-xs text-lia-text-tertiary">
                  Usar filtros e busca inteligente
                </p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 lia-text-secondary group-hover:text-lia-text-primary dark:group-hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none" />
          </button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
