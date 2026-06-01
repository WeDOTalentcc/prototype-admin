"use client"

/**
 * VariableCompCatalogSection — catalogo item-centric de verbas variaveis em
 * Configuracoes (Dados da Empresa, junto das Politicas de Remuneracao). Lista
 * agrupada por tipo + criar/editar/excluir. Fonte canonica das verbas variaveis
 * (a aba "Verbas Variaveis" do CompensationPolicy fica depreciada). Strings PT.
 */
import React, { useMemo, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Coins, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { VariableCompList } from "@/components/compensation/VariableCompList"
import { VariableCompFormModal } from "@/components/compensation/VariableCompFormModal"
import { defaultComponent, type VariableCompRecord } from "@/components/compensation/variable-comp-types"

const BASE = "/api/backend-proxy/company/compensation-components"

export function VariableCompCatalogSection() {
  const queryClient = useQueryClient()
  const { data: items = [], isLoading } = useQuery<VariableCompRecord[]>({
    queryKey: ["company-comp-components"],
    queryFn: async () => {
      const res = await fetch(`${BASE}/`, { signal: AbortSignal.timeout(12000) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return Array.isArray(json) ? json : json?.data || []
    },
    staleTime: 30_000,
    retry: 1,
  })

  const [editing, setEditing] = useState<VariableCompRecord | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["company-comp-components"] })

  async function handleSave(c: VariableCompRecord) {
    setIsSaving(true)
    try {
      const url = c.id ? `${BASE}/${c.id}` : `${BASE}/`
      const method = c.id ? "PUT" : "POST"
      const res = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(c) })
      if (res.ok) {
        await invalidate()
        setModalOpen(false)
        setEditing(null)
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function handleDelete(id: string) {
    const res = await fetch(`${BASE}/${id}`, { method: "DELETE" })
    if (res.ok) await invalidate()
  }

  function openCreate(kind?: string) {
    setEditing({ ...defaultComponent, kind: kind || "bonus" })
    setModalOpen(true)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-lia-text-primary flex items-center gap-1.5">
            <Coins className="w-4 h-4 text-lia-text-secondary" />
            Verbas Variáveis
          </h3>
          <p className="text-xs text-lia-text-tertiary">Bônus, PLR, comissão, stock options — por nível, área, contrato e CNPJ. Reutilizadas nas vagas.</p>
        </div>
        <Button size="sm" onClick={() => openCreate()} className="gap-1.5 text-xs">
          <Plus className="w-3.5 h-3.5" />Adicionar verba
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 p-4 text-sm text-lia-text-secondary"><Loader2 className="w-4 h-4 animate-spin" />Carregando…</div>
      ) : items.length === 0 ? (
        <div className="rounded-md border border-dashed border-lia-border-default p-6 text-center">
          <Coins className="w-5 h-5 mx-auto text-lia-text-disabled mb-2" />
          <p className="text-sm text-lia-text-secondary">Nenhuma verba variável cadastrada.</p>
          <Button size="sm" variant="outline" onClick={() => openCreate()} className="mt-3 gap-1.5 text-xs"><Plus className="w-3.5 h-3.5" />Adicionar verba</Button>
        </div>
      ) : (
        <VariableCompList
          components={items}
          isEditing={true}
          mode="catalog"
          onToggle={(c) => { /* catalogo: toggle ativa/desativa via PUT */ if (c.id) { fetch(`${BASE}/${c.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_active: !(c.is_active !== false) }) }).then((r) => { if (r.ok) invalidate() }) } }}
          onEdit={(c) => { setEditing(c); setModalOpen(true) }}
          onCreateInKind={openCreate}
          onDelete={handleDelete}
        />
      )}

      <VariableCompFormModal
        open={modalOpen}
        onOpenChange={(o) => { if (!o) { setModalOpen(false); setEditing(null) } }}
        editing={editing}
        setEditing={setEditing}
        isSaving={isSaving}
        onSave={handleSave}
      />
    </div>
  )
}

export default VariableCompCatalogSection
