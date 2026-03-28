"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Shield,
  Plus,
  ToggleLeft,
  ToggleRight,
  Pencil,
  RefreshCw,
  Loader2,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react"
import { toast } from "sonner"

interface Guardrail {
  id: string
  level: "primary" | "secondary"
  domain: string | null
  node: string | null
  tool: string | null
  rule: string
  blocking_message: string
  is_active: boolean
  company_id: string | null
  updated_by: string
}

const DOMAINS = [
  { value: "", label: "Todos os domínios" },
  { value: "pipeline", label: "Pipeline" },
  { value: "sourcing", label: "Sourcing" },
  { value: "cv_screening", label: "Triagem de CVs" },
  { value: "wsi_interviewer", label: "Entrevistador WSI" },
  { value: "communication", label: "Comunicação" },
  { value: "job_management", label: "Gestão de Vagas" },
  { value: "hiring_policy", label: "Política de Contratação" },
]

const LEVEL_LABEL: Record<string, string> = {
  primary: "Primário",
  secondary: "Secundário",
}

const DOMAIN_LABEL: Record<string, string> = Object.fromEntries(
  DOMAINS.filter(d => d.value).map(d => [d.value, d.label])
)

export default function GuardrailsPage() {
  const [guardrails, setGuardrails] = useState<Guardrail[]>([])
  const [loading, setLoading] = useState(true)
  const [filterDomain, setFilterDomain] = useState("")
  const [filterLevel, setFilterLevel] = useState("")
  const [filterActive, setFilterActive] = useState("")
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingGuardrail, setEditingGuardrail] = useState<Guardrail | null>(null)
  const [saving, setSaving] = useState(false)

  const [form, setForm] = useState({
    level: "primary",
    domain: "",
    tool: "",
    rule: "",
    blocking_message: "",
  })

  const fetchGuardrails = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterDomain) params.set("domain", filterDomain)
      if (filterLevel) params.set("level", filterLevel)
      if (filterActive !== "") params.set("is_active", filterActive)

      const res = await fetch(`/api/backend-proxy/guardrails?${params.toString()}`)
      if (!res.ok) throw new Error("Falha ao carregar guardrails")
      setGuardrails(await res.json())
    } catch {
      toast.error("Erro ao carregar guardrails")
    } finally {
      setLoading(false)
    }
  }, [filterDomain, filterLevel, filterActive])

  useEffect(() => { fetchGuardrails() }, [fetchGuardrails])

  const handleToggle = async (guardrail: Guardrail) => {
    try {
      const res = await fetch(`/api/backend-proxy/guardrails/${guardrail.id}/toggle`, {
        method: "PATCH",
      })
      if (!res.ok) throw new Error()
      const updated: Guardrail = await res.json()
      setGuardrails(prev => prev.map(g => g.id === updated.id ? updated : g))
      toast.success(`Guardrail ${updated.is_active ? "ativado" : "desativado"}`)
    } catch {
      toast.error("Erro ao alternar status do guardrail")
    }
  }

  const openCreateDialog = () => {
    setEditingGuardrail(null)
    setForm({ level: "primary", domain: "", tool: "", rule: "", blocking_message: "" })
    setDialogOpen(true)
  }

  const openEditDialog = (g: Guardrail) => {
    setEditingGuardrail(g)
    setForm({
      level: g.level,
      domain: g.domain ?? "",
      tool: g.tool ?? "",
      rule: g.rule,
      blocking_message: g.blocking_message,
    })
    setDialogOpen(true)
  }

  const handleSave = async () => {
    if (!form.rule.trim() || !form.blocking_message.trim()) {
      toast.error("Regra e mensagem de bloqueio são obrigatórias")
      return
    }

    setSaving(true)
    try {
      const payload = {
        level: form.level,
        domain: form.domain || null,
        tool: form.tool || null,
        rule: form.rule,
        blocking_message: form.blocking_message,
        updated_by: "admin",
      }

      let res: Response
      if (editingGuardrail) {
        res = await fetch(`/api/backend-proxy/guardrails/${editingGuardrail.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
      } else {
        res = await fetch("/api/backend-proxy/guardrails", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
      }

      if (!res.ok) throw new Error()
      toast.success(editingGuardrail ? "Guardrail atualizado" : "Guardrail criado")
      setDialogOpen(false)
      fetchGuardrails()
    } catch {
      toast.error("Erro ao salvar guardrail")
    } finally {
      setSaving(false)
    }
  }

  const activeCount = guardrails.filter(g => g.is_active).length
  const primaryCount = guardrails.filter(g => g.level === "primary").length

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="h-6 w-6 text-gray-700" />
          <div>
            <h1 className="text-lg font-semibold text-gray-900">Guardrails de Agentes</h1>
            <p className="text-xs text-gray-500">
              Regras de comportamento editáveis em produção sem deploy
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchGuardrails} disabled={loading}>
            {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
          </Button>
          <Button size="sm" onClick={openCreateDialog} className="bg-gray-900 hover:bg-gray-800 text-white">
            <Plus className="h-3 w-3 mr-1" />
            Novo Guardrail
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="border border-gray-200">
          <CardContent className="p-4">
            <div className="text-2xl font-semibold text-gray-900">{guardrails.length}</div>
            <div className="text-xs text-gray-500 mt-0.5">Total de guardrails</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-200">
          <CardContent className="p-4">
            <div className="text-2xl font-semibold text-status-success">{activeCount}</div>
            <div className="text-xs text-gray-500 mt-0.5">Ativos</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-200">
          <CardContent className="p-4">
            <div className="text-2xl font-semibold text-gray-700">{primaryCount}</div>
            <div className="text-xs text-gray-500 mt-0.5">Primários (todos os agentes)</div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-3">
        <Select value={filterDomain} onValueChange={setFilterDomain}>
          <SelectTrigger className="w-48 h-8 text-xs">
            <SelectValue placeholder="Filtrar por domínio" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos os domínios</SelectItem>
            {DOMAINS.filter(d => d.value).map(d => (
              <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filterLevel} onValueChange={setFilterLevel}>
          <SelectTrigger className="w-36 h-8 text-xs">
            <SelectValue placeholder="Nível" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos</SelectItem>
            <SelectItem value="primary">Primário</SelectItem>
            <SelectItem value="secondary">Secundário</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filterActive} onValueChange={setFilterActive}>
          <SelectTrigger className="w-32 h-8 text-xs">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos</SelectItem>
            <SelectItem value="true">Ativos</SelectItem>
            <SelectItem value="false">Inativos</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Lista */}
      <div className="space-y-2">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        ) : guardrails.length === 0 ? (
          <div className="text-center py-12 text-gray-400 text-sm">
            Nenhum guardrail encontrado
          </div>
        ) : (
          guardrails.map(g => (
            <Card key={g.id} className={`border ${g.is_active ? "border-gray-200" : "border-gray-100 opacity-60"}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <Badge variant="outline" className="text-xs px-1.5 py-0">
                        {LEVEL_LABEL[g.level]}
                      </Badge>
                      {g.domain && (
                        <Badge variant="secondary" className="text-xs px-1.5 py-0">
                          {DOMAIN_LABEL[g.domain] ?? g.domain}
                        </Badge>
                      )}
                      {g.tool && (
                        <span className="text-xs font-mono text-gray-500 bg-gray-50 px-1.5 py-0.5 rounded-md">
                          tool: {g.tool}
                        </span>
                      )}
                      {g.is_active ? (
                        <span className="flex items-center gap-0.5 text-xs text-status-success">
                          <CheckCircle2 className="h-3 w-3" /> Ativo
                        </span>
                      ) : (
                        <span className="flex items-center gap-0.5 text-xs text-gray-400">
                          <AlertTriangle className="h-3 w-3" /> Inativo
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-700 leading-relaxed">{g.rule}</p>
                    <p className="text-xs text-gray-400 mt-1 italic">
                      Mensagem: &ldquo;{g.blocking_message}&rdquo;
                    </p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => openEditDialog(g)}
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => handleToggle(g)}
                    >
                      {g.is_active
                        ? <ToggleRight className="h-4 w-4 text-status-success" />
                        : <ToggleLeft className="h-4 w-4 text-gray-400" />
                      }
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Dialog criar/editar */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-sm font-semibold">
              {editingGuardrail ? "Editar Guardrail" : "Novo Guardrail"}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Nível</Label>
                <Select value={form.level} onValueChange={v => setForm(f => ({ ...f, level: v }))}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="primary">Primário (todos agentes)</SelectItem>
                    <SelectItem value="secondary">Secundário (domínio)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Domínio</Label>
                <Select value={form.domain} onValueChange={v => setForm(f => ({ ...f, domain: v }))}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue placeholder="Todos (opcional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Todos os domínios</SelectItem>
                    {DOMAINS.filter(d => d.value).map(d => (
                      <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-1">
              <Label className="text-xs">Tool bloqueada (opcional)</Label>
              <Input
                className="h-8 text-xs"
                placeholder="ex: reject_candidate, send_bulk_email"
                value={form.tool}
                onChange={e => setForm(f => ({ ...f, tool: e.target.value }))}
              />
            </div>

            <div className="space-y-1">
              <Label className="text-xs">Regra <span className="text-status-error">*</span></Label>
              <Textarea
                className="text-xs resize-none"
                rows={3}
                placeholder="Descreva a regra em linguagem natural..."
                value={form.rule}
                onChange={e => setForm(f => ({ ...f, rule: e.target.value }))}
              />
            </div>

            <div className="space-y-1">
              <Label className="text-xs">Mensagem de bloqueio <span className="text-status-error">*</span></Label>
              <Textarea
                className="text-xs resize-none"
                rows={2}
                placeholder="Mensagem exibida ao usuário quando bloqueado..."
                value={form.blocking_message}
                onChange={e => setForm(f => ({ ...f, blocking_message: e.target.value }))}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setDialogOpen(false)}>
              Cancelar
            </Button>
            <Button
              size="sm"
              className="bg-gray-900 hover:bg-gray-800 text-white"
              onClick={handleSave}
              disabled={saving}
            >
              {saving && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
              {editingGuardrail ? "Salvar" : "Criar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
