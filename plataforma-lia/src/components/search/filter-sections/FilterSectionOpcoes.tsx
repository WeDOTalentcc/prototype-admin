"use client"
import React from"react"
import { Zap, Mail, Phone, TrendingUp, AlertCircle } from"lucide-react"
import { Chip } from "@/components/ui/chip"
import { Label } from"@/components/ui/label"
import { Switch } from"@/components/ui/switch"
import { type SearchFilters, type SearchSource } from"../advancedFiltersTypes"
import { type CreditEstimate } from"@/lib/api/candidate-search"

interface FilterSectionOpcoesProps {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
  searchSource: SearchSource
  creditEstimate: CreditEstimate
}

export const FilterSectionOpcoes = React.memo(function FilterSectionOpcoes({
  filters,
  updateFilter,
  searchSource,
  creditEstimate,
}: FilterSectionOpcoesProps) {
  return (
    <div className="space-y-6">
      {(searchSource ==="global" || searchSource ==="hybrid") && (
        <div className="p-4 rounded-xl border bg-lia-bg-secondary border-lia-border-subtle">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Zap className="w-3.5 h-3.5 text-lia-text-secondary" />
              <span className="font-medium text-xs">Custo Estimado</span>
            </div>
            <Chip density="relaxed" variant="neutral" className="px-1.5 py-0.5 border-lia-border-medium text-lia-text-primary">
              Tempo Real
            </Chip>
          </div>

          <div className="flex items-end justify-between">
            <div>
              <div className="text-sm font-semibold text-lia-text-primary">
                {creditEstimate.cost_per_candidate} cred + ${creditEstimate.apify_cost_per_candidate ?? 0.01}
              </div>
              <div className="text-xs text-lia-text-secondary">por candidato (créditos + Apify)</div>
            </div>
            <div className="text-right">
              <div className="font-semibold text-lia-text-primary">{creditEstimate.total_estimated} cred + ${(creditEstimate.apify_total ?? creditEstimate.limit * 0.01).toFixed(2)}</div>
              <div className="text-xs text-lia-text-secondary">total ({creditEstimate.limit} candidatos)</div>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-wedo-cyan/20 space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-lia-text-secondary">
                Base (Busca Rápida)
              </span>
              <span className="font-medium">{creditEstimate.base_cost}</span>
            </div>
            {creditEstimate.insights_cost > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-lia-text-secondary">Insights + Scoring</span>
                <span className="font-medium">+{creditEstimate.insights_cost}</span>
              </div>
            )}
            {creditEstimate.freshness_cost > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-lia-text-secondary">Dados Atualizados</span>
                <span className="font-medium">+{creditEstimate.freshness_cost}</span>
              </div>
            )}
            <div className="flex justify-between text-xs text-lia-text-muted">
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3" />
                Enriquecimento Apify
              </span>
              <span className="font-medium">${creditEstimate.apify_cost_per_candidate ?? 0.01}/candidato</span>
            </div>
            <div className="flex justify-between text-xs pt-1.5 border-t border-wedo-cyan/15">
              <span className="flex items-center gap-1 font-medium text-lia-text-primary">
                <TrendingUp className="w-3 h-3" />
                Total por Candidato
              </span>
              <span className="font-bold text-lia-text-primary">{creditEstimate.cost_per_candidate} cred + ${creditEstimate.apify_cost_per_candidate ?? 0.01}</span>
            </div>
          </div>

          {creditEstimate.warnings.length > 0 && (
            <div className="mt-3 p-2 bg-status-warning/10 rounded-xl border border-status-warning/30">
              {creditEstimate.warnings.map((warning, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-status-warning">
                  <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>{warning}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="space-y-3">
        <Label className="text-xs font-medium block">Informações de Contato</Label>

        <div className="flex items-center justify-between p-2.5 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-2">
            <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />
            <div>
              <div className="text-xs font-medium">Apenas com Email</div>
              <div className="text-xs text-lia-text-secondary">Filtrar candidatos com email</div>
            </div>
          </div>
          <Switch
            checked={filters.ppiOptions?.requireEmails || false}
            onCheckedChange={(checked: boolean) => updateFilter("ppiOptions","requireEmails", checked)}
          />
        </div>

        <div className="flex items-center justify-between p-2.5 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-2">
            <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />
            <div>
              <div className="text-xs font-medium">Mostrar Emails</div>
              <div className="text-xs text-lia-text-secondary">Exibir emails nos resultados</div>
            </div>
          </div>
          <Switch
            checked={filters.ppiOptions?.showEmails || false}
            onCheckedChange={(checked: boolean) => updateFilter("ppiOptions","showEmails", checked)}
          />
        </div>

        <div className="flex items-center justify-between p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <Phone className="w-4 h-4 text-lia-text-secondary" />
            <div>
              <div className="text-xs font-medium">Apenas com Telefone</div>
              <div className="text-xs text-lia-text-secondary">Filtrar candidatos com telefone</div>
            </div>
          </div>
          <Switch
            checked={filters.ppiOptions?.requirePhoneNumbers || false}
            onCheckedChange={(checked: boolean) => updateFilter("ppiOptions","requirePhoneNumbers", checked)}
          />
        </div>

        <div className="flex items-center justify-between p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <Phone className="w-4 h-4 text-lia-text-secondary" />
            <div>
              <div className="text-xs font-medium">Mostrar Telefones</div>
              <div className="text-xs text-lia-text-secondary">Exibir telefones nos resultados</div>
            </div>
          </div>
          <Switch
            checked={filters.ppiOptions?.showPhoneNumbers || false}
            onCheckedChange={(checked: boolean) => updateFilter("ppiOptions","showPhoneNumbers", checked)}
          />
        </div>

        <div className="flex items-center justify-between p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <Mail className="w-4 h-4 text-lia-text-secondary" />
            <Phone className="w-4 h-4 -ml-2 text-lia-text-secondary" />
            <div>
              <div className="text-xs font-medium">Email OU Telefone</div>
              <div className="text-xs text-lia-text-secondary">Pelo menos um contato</div>
            </div>
          </div>
          <Switch
            checked={filters.ppiOptions?.requirePhonesOrEmails || false}
            onCheckedChange={(checked: boolean) => updateFilter("ppiOptions","requirePhonesOrEmails", checked)}
          />
        </div>
      </div>
    </div>
  )
})
FilterSectionOpcoes.displayName ="FilterSectionOpcoes"
