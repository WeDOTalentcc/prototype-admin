"use client"

import { Search, Loader2, FileText, Lightbulb, Briefcase, Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface ArchetypeCreateViewProps {
  archetypeCreateMode: "job" | "description"
  onArchetypeCreateModeChange: (mode: "job" | "description") => void
  jobSearchQuery: string
  onJobSearchQueryChange: (v: string) => void
  isSearchingJobs: boolean
  jobSearchResults: Array<{
    id: string
    title: string
    department: string | null
    seniority_level: string | null
    status: string
    created_at: string
    description: string | null
    technical_requirements: string[] | null
  }>
  onOpenArchetypeFromJob: (job: { id: string; title: string; department: string | null; seniority_level: string | null; status: string; created_at: string; description: string | null; technical_requirements: string[] | null }) => void
  archetypeDescription: string
  onArchetypeDescriptionChange: (v: string) => void
  isCreatingArchetype: boolean
  onCreateArchetypeFromDescription: (description: string) => void
  onSearchJobsForArchetype: (query: string) => void
}

export function ArchetypeCreateView({
  archetypeCreateMode,
  onArchetypeCreateModeChange,
  jobSearchQuery,
  onJobSearchQueryChange,
  isSearchingJobs,
  jobSearchResults,
  onOpenArchetypeFromJob,
  archetypeDescription,
  onArchetypeDescriptionChange,
  isCreatingArchetype,
  onCreateArchetypeFromDescription,
  onSearchJobsForArchetype,
}: ArchetypeCreateViewProps) {
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <button
          onClick={() => onArchetypeCreateModeChange("job")}
          className={cn(
            "flex-1 px-3 py-2 rounded-md text-xs font-medium transition-colors border border-lia-border-subtle",
            archetypeCreateMode === "job"
              ? "bg-lia-bg-tertiary ring-1 ring-lia-border-medium text-lia-text-primary"
              : "bg-lia-bg-primary hover:bg-lia-bg-secondary text-lia-text-secondary"
          )}
        >
          <Briefcase className="w-3.5 h-3.5 inline mr-1.5" />
          A partir de Vaga
        </button>
        <button
          onClick={() => onArchetypeCreateModeChange("description")}
          className={cn(
            "flex-1 px-3 py-2 rounded-md text-xs font-medium transition-colors border border-lia-border-subtle",
            archetypeCreateMode === "description"
              ? "bg-lia-bg-tertiary ring-1 ring-lia-border-medium text-lia-text-primary"
              : "bg-lia-bg-primary hover:bg-lia-bg-secondary text-lia-text-secondary"
          )}
        >
          <FileText className="w-3.5 h-3.5 inline mr-1.5" />
          A partir de Descrição
        </button>
      </div>

      {archetypeCreateMode === "job" && (
        <div className="space-y-2">
          <p className="text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
            Busque por nome ou ID da vaga para criar um arquétipo:
          </p>

          <div className="relative">
            <Search
              className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-lia-text-tertiary"
            />
            <input
              type="text"
              value={jobSearchQuery}
              onChange={(e) => {
                onJobSearchQueryChange(e.target.value)
                onSearchJobsForArchetype(e.target.value)
              }}
              placeholder="Buscar vaga por nome ou ID..."
              className="w-full pl-8 pr-3 py-2 rounded-xl text-xs focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 border border-lia-border-subtle"
            />
            {isSearchingJobs && (
              <Loader2 className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-lia-text-primary" />
            )}
          </div>

          {jobSearchQuery.trim() && (
            <div className="max-h-chart-sm overflow-y-auto space-y-1.5 rounded-xl border border-lia-border-subtle" role="status" aria-live="polite" aria-label="Carregando...">
              {isSearchingJobs ? (
                <div className="flex items-center justify-center py-4" role="status" aria-live="polite" aria-label="Carregando...">
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-primary" />
                  <span className="ml-2 text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                    Buscando vagas...
                  </span>
                </div>
              ) : jobSearchResults.length === 0 ? (
                <div className="text-center py-4 px-3">
                  <Briefcase className="w-5 h-5 mx-auto mb-1.5" />
                  <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                    Nenhuma vaga encontrada para "{jobSearchQuery}"
                  </p>
                </div>
              ) : (
                jobSearchResults.map((job) => (
                  <button
                    key={job.id}
                    onClick={() => onOpenArchetypeFromJob(job)}
                    className="w-full p-2.5 text-left transition-colors motion-reduce:transition-none hover:bg-lia-bg-secondary border-b border-lia-border-subtle last:border-b-0"
                  >
                    <div className="flex items-start gap-2">
                      <Briefcase className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-xs truncate text-lia-text-primary">
                            {job.title}
                          </p>
                          <span
                            className="px-1.5 py-0.5 rounded-full text-micro font-medium"
                            style={{backgroundColor:
                                job.status === "Publicada"
                                  ? "var(--status-success-bg-15)"
                                  : job.status === "Encerrada"
                                  ? "var(--lia-bg-tertiary)"
                                  : "var(--status-warning-bg-15)",
                              color:
                                job.status === "Publicada"
                                  ? "var(--status-success)"
                                  : job.status === "Encerrada"
                                  ? "var(--lia-text-tertiary)"
                                  : "var(--status-warning)"}}
                          >
                            {job.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-micro text-lia-text-tertiary">
                            ID: {job.id.slice(0, 8)}...
                          </span>
                          {job.department && (
                            <>
                              <span className="text-micro text-lia-text-muted">•</span>
                              <span className="text-micro text-lia-text-tertiary">{job.department}</span>
                            </>
                          )}
                          {job.seniority_level && (
                            <>
                              <span className="text-micro text-lia-text-muted">•</span>
                              <span className="text-micro text-lia-text-tertiary">{job.seniority_level}</span>
                            </>
                          )}
                        </div>
                        <p className="text-micro mt-0.5 text-lia-text-tertiary">
                          Criada em {new Date(job.created_at).toLocaleDateString("pt-BR")}
                        </p>
                        {job.description && (
                          <p className="text-micro mt-1 line-clamp-2 text-lia-text-tertiary">
                            {job.description.slice(0, 120)}
                            {job.description.length > 120 ? "..." : ""}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          )}

          {!jobSearchQuery.trim() && (
            <div className="text-center py-4 px-3 rounded-xl border border-dashed border-lia-border-subtle">
              <Search className="w-5 h-5 mx-auto mb-1.5" />
              <p className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                Digite o nome ou ID da vaga para buscar
              </p>
            </div>
          )}

          <div className="p-2.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
              <p className="text-xs text-lia-text-primary">
                <strong>Dica:</strong> Selecione uma vaga para preencher automaticamente os dados do
                arquétipo. Você poderá editar antes de salvar.
              </p>
            </div>
          </div>
        </div>
      )}

      {archetypeCreateMode === "description" && (
        <div className="space-y-2">
          <p className="text-xs text-lia-text-secondary">
            Descreva o perfil ideal que deseja buscar:
          </p>
          <textarea
            value={archetypeDescription}
            onChange={(e) => onArchetypeDescriptionChange(e.target.value)}
            placeholder="Ex: Desenvolvedor Python sênior com experiência em machine learning e cloud AWS, preferencialmente com background em fintechs..."
            rows={3}
            className="w-full rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 resize-none border border-lia-border-default bg-lia-bg-secondary text-lia-text-primary"
          />
          <Button
            onClick={() => onCreateArchetypeFromDescription(archetypeDescription)}
            disabled={archetypeDescription.length < 20 || isCreatingArchetype}
            size="sm"
            className={cn("w-full", archetypeDescription.length >= 20 ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" : "bg-lia-bg-tertiary text-lia-text-secondary")}
          >
            {isCreatingArchetype ? (
              <>
                <Loader2 className="w-4 h-4 mr-1 animate-spin motion-reduce:animate-none" />
                Criando...
              </>
            ) : (
              <>
                <Brain className="w-4 h-4 mr-1 text-wedo-cyan" />
                Criar Arquétipo com LIA
              </>
            )}
          </Button>

          <div className="p-2.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
              <p className="text-xs text-lia-text-primary">
                <strong>Dica:</strong> Descreva o perfil ideal e a LIA vai extrair automaticamente cargo,
                senioridade e skills para criar o arquétipo.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
