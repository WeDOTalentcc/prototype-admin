import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  Filter, ChevronDown, ChevronUp, Eye, AlertTriangle,
} from"lucide-react"

interface RecruiterFiltersProps {
  departments: string[]
  selectedPeriod: string
  setSelectedPeriod: (v: string) => void
  selectedDepartments: string[]
  setSelectedDepartments: (v: string[]) => void
  selectedRecruiters: string[]
  setSelectedRecruiters: (v: string[]) => void
  showAdvancedFilters: boolean
  setShowAdvancedFilters: (v: boolean) => void
  sortBy: string
  setSortBy: (v: string) => void
  sortOrder:"asc" |"desc"
  setSortOrder: (v:"asc" |"desc") => void
}

export function RecruiterFilters({
  departments,
  selectedPeriod,
  setSelectedPeriod,
  selectedDepartments,
  setSelectedDepartments,
  selectedRecruiters,
  setSelectedRecruiters,
  showAdvancedFilters,
  setShowAdvancedFilters,
  sortBy,
  setSortBy,
  sortOrder,
  setSortOrder,
}: RecruiterFiltersProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-lia-text-secondary" />
            Filtros Avançados
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="gap-2"
          >
            {showAdvancedFilters ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
            {showAdvancedFilters ?"Ocultar" :"Expandir"}
          </Button>
        </div>
      </CardHeader>
      {showAdvancedFilters && (
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block text-lia-text-primary">
                Período
              </label>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="w-full p-2 rounded-xl text-sm bg-lia-bg-secondary focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 text-lia-text-primary"
              >
                <option value="current_month">Este Mês</option>
                <option value="last_month">Mês Passado</option>
                <option value="quarter">Este Trimestre</option>
                <option value="year">Este Ano</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block text-lia-text-primary">
                Departamentos
              </label>
              <div className="space-y-2">
                {departments.map((dept) => (
                  <label key={dept} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedDepartments.includes(dept)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedDepartments([...selectedDepartments, dept])
                        } else {
                          setSelectedDepartments(selectedDepartments.filter((d) => d !== dept))
                        }
                      }}
                      className="rounded-md"
                    />
                    {dept}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block text-lia-text-primary">
                Ordenar por
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full p-2 rounded-xl text-sm mb-2 bg-lia-bg-secondary focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 text-lia-text-primary"
              >
                <option value="totalScore">Score Total</option>
                <option value="npsScore">NPS</option>
                <option value="conversionRate">Taxa Conversão</option>
                <option value="avgTimeToFill">Tempo de Preenchimento</option>
                <option value="totalHires">Total Contratações</option>
              </select>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as"asc" |"desc")}
                className="w-full p-2 rounded-xl text-sm bg-lia-bg-secondary focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 text-lia-text-primary"
              >
                <option value="desc">Maior para Menor</option>
                <option value="asc">Menor para Maior</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block text-lia-text-primary">
                Ações Rápidas
              </label>
              <div className="space-y-2">
                <Button variant="outline" size="sm" className="w-full gap-2">
                  <Eye className="w-3 h-3" />
                  Ver Top Performers
                </Button>
                <Button variant="outline" size="sm" className="w-full gap-2">
                  <AlertTriangle className="w-3 h-3" />
                  Alertas de Performance
                </Button>
              </div>
            </div>
          </div>

          {(selectedDepartments.length > 0 || selectedRecruiters.length > 0) && (
            <div className="flex flex-wrap gap-2 pt-4 border-t">
              {selectedDepartments.map((dept) => (
                <Chip key={dept} variant="neutral" className="gap-1">
                  {dept}
                  <button
                    onClick={() =>
                      setSelectedDepartments(selectedDepartments.filter((d) => d !== dept))
                    }
                    className="ml-1 hover:text-status-error"
                  >
                    ×
                  </button>
                </Chip>
              ))}
              {selectedRecruiters.map((name) => (
                <Chip key={name} variant="neutral" className="gap-1">
                  {name}
                  <button
                    onClick={() =>
                      setSelectedRecruiters(selectedRecruiters.filter((n) => n !== name))
                    }
                    className="ml-1 hover:text-status-error"
                  >
                    ×
                  </button>
                </Chip>
              ))}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
